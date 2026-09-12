#!/usr/bin/env bash
# scripts/setup-fresh.sh — idempotent fresh boot and verification for msql-studio
# Usage:
#   export COMPOSE_PROJECT_NAME=msql-studio
#   export COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml
#   ./scripts/setup-fresh.sh
#
# Must refuse to run without -p msql-studio semantics (export COMPOSE_PROJECT_NAME).

set -euo pipefail

# Parse optional -p / --project-name argument
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project-name)
      if [[ $# -ge 2 ]]; then
        PROJECT_NAME="$2"
        shift 2
      else
        shift
      fi
      ;;
    *)
      shift
      ;;
  esac
done

# Hard requirement 1: enforce project name msql-studio
if [[ "$PROJECT_NAME" != "msql-studio" ]]; then
  echo "ERROR: Must run with -p msql-studio semantics (export COMPOSE_PROJECT_NAME=msql-studio or pass -p msql-studio)." >&2
  echo "Refusing to run to prevent accidental default project creation." >&2
  exit 1
fi

export COMPOSE_PROJECT_NAME="msql-studio"

cd "$(dirname "$0")/.."

# Hard requirement 2: DEV overlay carries DB ports, mem limits, and problems-repo mount
export COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml:docker-compose.dev.yml}"
if [[ "$COMPOSE_FILE" != *"docker-compose.dev.yml"* ]]; then
  export COMPOSE_FILE="docker-compose.yml:docker-compose.dev.yml"
fi

# Ensure ../m_sql_studio_problems resolves to ./m_sql_studio_problems for dev overlay bind-mount
if [[ ! -d "../m_sql_studio_problems/problems" ]]; then
  if [[ -d "./m_sql_studio_problems/problems" ]]; then
    echo "Ensuring ../m_sql_studio_problems symlink points to ./m_sql_studio_problems..."
    rm -rf "../m_sql_studio_problems" 2>/dev/null || true
    ln -s "$(pwd)/m_sql_studio_problems" "../m_sql_studio_problems"
  fi
fi

# Ensure mongo keyfile exists with strict 400 permissions
KEYFILE="misc/init-db/mongodb/mongo-keyfile"
if [[ ! -f "$KEYFILE" ]]; then
  mkdir -p misc/init-db/mongodb
  openssl rand -base64 741 > "$KEYFILE"
  chmod 400 "$KEYFILE"
else
  chmod 400 "$KEYFILE" 2>/dev/null || true
fi

echo "=== [1/6] Building all images (gateway, client, sandbox) ==="
docker compose -p msql-studio build api-gateway client sandbox-executor

echo "=== [2/6] Bringing up stack with DEV overlay (detached) ==="
docker compose -p msql-studio up -d

echo "=== [3/6] Waiting for services to be healthy (timeout: 5m) ==="
SERVICES=("redis" "mongo1" "postgres" "api-gateway" "api-gateway-b")
MAX_WAIT=300  # 5 minutes
START=$(date +%s)

for svc in "${SERVICES[@]}"; do
  echo -n "  Waiting for ${svc} to be healthy... "
  while true; do
    CID=$(docker compose -p msql-studio ps -q "$svc" 2>/dev/null || true)
    if [[ -z "$CID" ]]; then
      echo "MISSING (container not found)"
      echo "Loud failure: service ${svc} container not found" >&2
      docker compose -p msql-studio logs --tail=100 "$svc" 2>/dev/null || true
      exit 1
    fi

    STATE=$(docker inspect --format='{{.State.Status}}' "$CID" 2>/dev/null || echo "unknown")
    if [[ "$STATE" == "exited" || "$STATE" == "dead" ]]; then
      echo "EXITED (state: $STATE)"
      echo "Loud failure: service ${svc} container exited unexpectedly" >&2
      docker compose -p msql-studio logs --tail=100 "$svc"
      exit 1
    fi

    HEALTH=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$CID" 2>/dev/null || echo "unknown")
    if [[ "$HEALTH" == "healthy" ]]; then
      echo "healthy"
      break
    fi
    if [[ "$HEALTH" == "unhealthy" ]]; then
      echo "UNHEALTHY"
      echo "Loud failure: service ${svc} failed health check" >&2
      docker compose -p msql-studio logs --tail=100 "$svc"
      exit 1
    fi

    NOW=$(date +%s)
    if (( NOW - START > MAX_WAIT )); then
      echo "TIMEOUT after ${MAX_WAIT}s"
      echo "Loud failure: timed out waiting for service ${svc} (health: $HEALTH, state: $STATE)" >&2
      docker compose -p msql-studio logs --tail=100 "$svc"
      exit 1
    fi
    sleep 3
  done
done

echo "=== [4/6] Post-up verification (/health, catalog, :3000) ==="

# 1. /health 200
HEALTH_RESP=$(curl -sS -w "\n%{http_code}" http://127.0.0.1:8000/health || echo "000")
HEALTH_CODE=$(echo "$HEALTH_RESP" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESP" | sed '$d')
if [[ "$HEALTH_CODE" != "200" ]]; then
  echo "FAIL: /health returned HTTP $HEALTH_CODE" >&2
  echo "$HEALTH_BODY" >&2
  docker compose -p msql-studio logs --tail=100 api-gateway
  exit 1
fi
echo "  /health -> 200 OK ($HEALTH_BODY)"

# 2. catalog 200
CATALOG_RESP=$(curl -sS -w "\n%{http_code}" "http://127.0.0.1:8000/api/v1/assignments?limit=50" || echo "000")
CATALOG_CODE=$(echo "$CATALOG_RESP" | tail -n1)
CATALOG_BODY=$(echo "$CATALOG_RESP" | sed '$d')
if [[ "$CATALOG_CODE" != "200" ]]; then
  echo "FAIL: catalog endpoint returned HTTP $CATALOG_CODE" >&2
  echo "$CATALOG_BODY" >&2
  docker compose -p msql-studio logs --tail=100 api-gateway
  exit 1
fi
echo "  /api/v1/assignments -> 200 OK"

# 3. :3000 200
CLIENT_RESP=$(curl -sS -w "\n%{http_code}" -o /dev/null http://127.0.0.1:3000/ || echo "000")
CLIENT_CODE=$(echo "$CLIENT_RESP" | tail -n1)
if [[ "$CLIENT_CODE" != "200" ]]; then
  echo "FAIL: client :3000 returned HTTP $CLIENT_CODE" >&2
  docker compose -p msql-studio logs --tail=50 client
  exit 1
fi
echo "  :3000 -> 200 OK"

echo "=== [5/6] Catalog gate (sync & live unique-title verification) ==="

if [[ ! -f .env ]]; then
  echo "FAIL: .env file missing in repository root" >&2
  exit 1
fi

INTERNAL_API_KEY=$(grep -E '^INTERNAL_API_KEY=' .env | head -n1 | cut -d '=' -f2- | tr -d '\r"')
if [[ -z "$INTERNAL_API_KEY" ]]; then
  echo "FAIL: INTERNAL_API_KEY not found in .env" >&2
  exit 1
fi

MONGO_USER=$(grep -E '^MONGO_USER=' .env | head -n1 | cut -d '=' -f2- | tr -d '\r"')
MONGO_PASSWORD=$(grep -E '^MONGO_PASSWORD=' .env | head -n1 | cut -d '=' -f2- | tr -d '\r"')

get_unique_title_count() {
  local count=""
  if [[ -n "$MONGO_USER" && -n "$MONGO_PASSWORD" ]]; then
    count=$(docker compose -p msql-studio exec -T mongo1 mongosh \
      -u "$MONGO_USER" -p "$MONGO_PASSWORD" \
      --authenticationDatabase admin --quiet \
      --eval 'db.getSiblingDB("m_sql_studio").assignments.distinct("title", { pgSchemaReady: true, deletedAt: null }).length' 2>/dev/null | tr -d ' \r\n' || echo "")
  fi
  if ! [[ "$count" =~ ^[0-9]+$ ]]; then
    count=$(curl -sS "http://127.0.0.1:8000/api/v1/assignments?limit=1" 2>/dev/null | jq -r '.total // 0' 2>/dev/null || echo "0")
  fi
  echo "$count"
}

CURRENT_UNIQUE=$(get_unique_title_count)
echo "  Current live unique titles: $CURRENT_UNIQUE"

# Seed initial 25 base assignments if catalog is empty or missing base seed
if (( CURRENT_UNIQUE < 25 )); then
  echo "  Catalog unique count ($CURRENT_UNIQUE) < 25 — running seed.js..."
  node misc/seed.js
  CURRENT_UNIQUE=$(get_unique_title_count)
  echo "  Base assignments seeded. Current unique titles: $CURRENT_UNIQUE"
fi

echo "  Triggering forced problems-sync via POST /internal/problems-sync..."
SYNC_RESP=$(curl -sS -w "\n%{http_code}" -X POST \
  http://127.0.0.1:8000/internal/problems-sync \
  -H "Content-Type: application/json" \
  -H "x-internal-api-key: ${INTERNAL_API_KEY}" \
  -d '{"forced":true}' || echo "000")

SYNC_CODE=$(echo "$SYNC_RESP" | tail -n1)
SYNC_BODY=$(echo "$SYNC_RESP" | sed '$d')

if [[ "$SYNC_CODE" != "202" && "$SYNC_CODE" != "200" ]]; then
  echo "FAIL: POST /internal/problems-sync returned HTTP $SYNC_CODE: $SYNC_BODY" >&2
  echo "=== api-gateway logs ===" >&2
  docker compose -p msql-studio logs --tail=100 api-gateway
  exit 1
fi
echo "  Problems-sync triggered (HTTP $SYNC_CODE: $SYNC_BODY)."

echo "  Polling live unique-title count to >= 200 (timeout 15m; sync tests-before-write)..."
SYNC_TIMEOUT=900  # 15 minutes
POLL_START=$(date +%s)

while true; do
  LIVE_COUNT=$(get_unique_title_count)
  NOW=$(date +%s)
  ELAPSED=$(( NOW - POLL_START ))

  echo "  [+${ELAPSED}s] Live unique titles: $LIVE_COUNT / 200"

  if [[ "$LIVE_COUNT" =~ ^[0-9]+$ ]] && (( LIVE_COUNT >= 200 )); then
    echo "  Catalog gate PASSED: live unique titles = $LIVE_COUNT (>= 200)."
    break
  fi

  if (( ELAPSED > SYNC_TIMEOUT )); then
    echo "FAIL: Timed out waiting for live unique titles >= 200 (current: $LIVE_COUNT) after ${SYNC_TIMEOUT}s" >&2
    echo "=== Sync worker log tail (api-gateway) ===" >&2
    docker compose -p msql-studio logs --tail=100 api-gateway
    echo "=== Sync worker log tail (api-gateway-b) ===" >&2
    docker compose -p msql-studio logs --tail=100 api-gateway-b
    exit 1
  fi

  sleep 5
done

FINAL_TOTAL=$(curl -sS "http://127.0.0.1:8000/api/v1/assignments?limit=1" 2>/dev/null | jq -r '.total // "unknown"' 2>/dev/null || echo "unknown")
echo "=== [6/6] All checks and catalog gate passed ==="
echo "Fresh boot complete. Stack is healthy and catalog contains $LIVE_COUNT unique problems (total: $FINAL_TOTAL)."
