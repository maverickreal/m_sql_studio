#!/bin/bash
# MongoDB replica set + user initialization for Docker Compose.
#
# Design: Start ALL members (mongo1, mongo2, mongo3) with --keyFile so internal
# replica set auth is consistent. The "localhost exception" lets us connect from
# localhost and create the first user when no users exist yet.
#
# This script runs inside mongo1's container entrypoint. It:
#   1. Waits for the local mongod to accept connections (localhost exception).
#   2. Waits for mongo2 and mongo3 to be reachable (needed for RS quorum).
#   3. Initiates the replica set.
#   4. Creates the admin user and the app user (api-gateway).
#
# Idempotent: safe to re-run on a persistent volume that already has users.
# First run: no users → localhost exception. Re-run: users exist → admin auth.

set -euo pipefail

# ── Authentication state ──────────────────────────────────────────────────────
# After the admin user is created, the localhost exception disappears and we
# must use admin auth for everything. We track this with AUTH_FLAG.

AUTH_FLAG=()

# Try admin auth. If it works, users already exist.
if mongosh --quiet -u "$MONGO_USER" -p "$MONGO_PASSWORD" \
    --authenticationDatabase admin --eval "db.runCommand('ping').ok" &>/dev/null; then
  echo "[setup.sh] Admin user detected — using authenticated connection."
  AUTH_FLAG=(-u "$MONGO_USER" -p "$MONGO_PASSWORD" --authenticationDatabase admin)
fi

# ── Helper: run JS via mongosh with current auth ─────────────────────────────

run_js() {
  local js="$1"
  mongosh --quiet "${AUTH_FLAG[@]}" --eval "$js"
}

# ── Switch to admin auth after creating users ─────────────────────────────────

enable_admin_auth() {
  AUTH_FLAG=(-u "$MONGO_USER" -p "$MONGO_PASSWORD" --authenticationDatabase admin)
  echo "[setup.sh] Switched to admin auth."
}

# ── Wait for local mongod ────────────────────────────────────────────────────

echo "[setup.sh] Waiting for local mongod to accept connections..."
while ! mongosh --quiet --eval "db.runCommand('ping').ok" &>/dev/null; do
  sleep 2
done
echo "[setup.sh] mongod is up."

# ── Wait for RS members ───────────────────────────────────────────────────────

for host in mongo2:27017 mongo3:27017; do
  echo "[setup.sh] Waiting for $host to be reachable..."
  until mongosh --host "$host" --quiet --eval "db.runCommand('ping').ok" &>/dev/null; do
    sleep 3
  done
  echo "[setup.sh] $host is reachable."
done

# ── Replica set ──────────────────────────────────────────────────────────────

RS_STATUS=$(run_js "try { rs.status().ok } catch (e) { 0 }" 2>/dev/null || echo "0")
if [ "$RS_STATUS" = "1" ]; then
  echo "[setup.sh] Replica set already initialized."
else
  echo "[setup.sh] Initiating replica set..."
  mongosh --quiet "${AUTH_FLAG[@]}" <<'EOF'
rs.initiate({
  _id: "rs0",
  version: 1,
  members: [
    { _id: 0, host: "mongo1:27017", priority: 2 },
    { _id: 1, host: "mongo2:27017", priority: 1 },
    { _id: 2, host: "mongo3:27017", priority: 1 }
  ]
});
EOF
  echo "[setup.sh] Waiting for primary election..."
  until mongosh --quiet --eval "db.hello().isWritablePrimary" 2>/dev/null | grep -q "true"; do
    sleep 1
  done
  echo "[setup.sh] Primary elected."
fi

# ── Admin user ───────────────────────────────────────────────────────────────

ADMIN_EXISTS=$(run_js "db.getSiblingDB('admin').getUsers().users.length" 2>/dev/null || echo "0")
if [ "$ADMIN_EXISTS" -gt 0 ] 2>/dev/null; then
  echo "[setup.sh] Admin users already exist."
else
  echo "[setup.sh] Creating admin user..."
  # First user must be created via localhost exception (no auth yet).
  if [ ${#AUTH_FLAG[@]} -ne 0 ]; then
    echo "[setup.sh] ERROR: admin user missing but auth required — cannot create."
    exit 1
  fi
  mongosh --quiet <<EOF
use admin;
db.createUser({
  user: "$MONGO_USER",
  pwd: "$MONGO_PASSWORD",
  roles: [ { role: "root", db: "admin" } ]
});
EOF
  echo "[setup.sh] Admin user created: $MONGO_USER"
  # Now the localhost exception is gone — switch to admin auth.
  enable_admin_auth
fi

# ── App user ─────────────────────────────────────────────────────────────────

# After admin user exists we must use admin auth. If AUTH_FLAG is still empty
# something went wrong (should have been set above or detected at startup).
if [ ${#AUTH_FLAG[@]} -eq 0 ]; then
  echo "[setup.sh] ERROR: admin auth not available — cannot create app user."
  exit 1
fi

APP_DB_EXISTS=$(run_js "db.getSiblingDB('$API_GATEWAY_MONGO_DB').getUsers().users.length" 2>/dev/null || echo "0")
if [ "$APP_DB_EXISTS" -gt 0 ] 2>/dev/null; then
  echo "[setup.sh] App user already exists in $API_GATEWAY_MONGO_DB."
else
  echo "[setup.sh] Creating app user for api-gateway..."
  mongosh --quiet "${AUTH_FLAG[@]}" <<EOF
use $API_GATEWAY_MONGO_DB;
db.createUser({
  user: "$API_GATEWAY_MONGO_USER",
  pwd: "$API_GATEWAY_MONGO_PASSWORD",
  roles: [ { role: "$API_GATEWAY_MONGO_ROLE", db: "$API_GATEWAY_MONGO_DB" } ]
});
EOF
  echo "[setup.sh] App user created: $API_GATEWAY_MONGO_USER in db $API_GATEWAY_MONGO_DB"
fi

echo "[setup.sh] MongoDB replica set initialization complete."
