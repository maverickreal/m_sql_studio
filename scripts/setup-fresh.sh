#!/usr/bin/env bash
# scripts/setup-fresh.sh — idempotent fresh boot for msql-studio
# Usage:
#   export COMPOSE_PROJECT_NAME=msql-studio && ./scripts/setup-fresh.sh
#   OR: ./scripts/setup-fresh.sh -p msql-studio
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

# Hard requirement: must run with -p msql-studio semantics
if [[ "$PROJECT_NAME" != "msql-studio" ]]; then
  echo "ERROR: Must run with -p msql-studio semantics (export COMPOSE_PROJECT_NAME=msql-studio or pass -p msql-studio)." >&2
  echo "Refusing to run to prevent accidental default project creation." >&2
  exit 1
fi

export COMPOSE_PROJECT_NAME="msql-studio"

cd "$(dirname "$0")/.."

echo "=== [1/5] Building api-gateway image ==="
docker compose -p msql-studio build api-gateway

echo "=== [2/5] Bringing up stack (detached) ==="
docker compose -p msql-studio up -d

echo "=== [3/5] Waiting for services to be healthy ==="
SERVICES=("redis" "mongo1" "postgres" "api-gateway" "api-gateway-b")
MAX_WAIT=300  # 5 minutes total
START=$(date +%s)

for svc in "${SERVICES[@]}"; do
  echo -n "  Waiting for ${svc} to be healthy... "
  while true; do
    CID=$(docker compose -p msql-studio ps -q "$svc" 2>/dev/null || true)
    if [[ -z "$CID" ]]; then
      echo "MISSING (container not found)"
      echo "Loud failure: service ${svc} container not found"
      docker compose -p msql-studio logs --tail=100 "$svc" 2>/dev/null || true
      exit 1
    fi

    STATE=$(docker inspect --format='{{.State.Status}}' "$CID" 2>/dev/null || echo "unknown")
    if [[ "$STATE" == "exited" || "$STATE" == "dead" ]]; then
      echo "EXITED (state: $STATE)"
      echo "Loud failure: service ${svc} container exited unexpectedly"
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
      echo "Loud failure: service ${svc} failed health check"
      docker compose -p msql-studio logs --tail=100 "$svc"
      exit 1
    fi

    NOW=$(date +%s)
    if (( NOW - START > MAX_WAIT )); then
      echo "TIMEOUT after ${MAX_WAIT}s"
      echo "Loud failure: timed out waiting for service ${svc} (health: $HEALTH, state: $STATE)"
      docker compose -p msql-studio logs --tail=100 "$svc"
      exit 1
    fi
    sleep 3
  done
done

echo "=== [4/5] Post-up verification ==="

# 1. /health 200
HEALTH_RESP=$(curl -sS -w "\n%{http_code}" http://127.0.0.1:8000/health || echo "000")
HEALTH_CODE=$(echo "$HEALTH_RESP" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESP" | sed '$d')
if [[ "$HEALTH_CODE" != "200" ]]; then
  echo "FAIL: /health returned HTTP $HEALTH_CODE"
  echo "$HEALTH_BODY"
  docker compose -p msql-studio logs --tail=100 api-gateway
  exit 1
fi
echo "  /health -> 200 OK ($HEALTH_BODY)"

# 2. catalog 200 + print total (warn if <200 with sync hint)
CATALOG_RESP=$(curl -sS -w "\n%{http_code}" "http://127.0.0.1:8000/api/v1/assignments?limit=50" || echo "000")
CATALOG_CODE=$(echo "$CATALOG_RESP" | tail -n1)
CATALOG_BODY=$(echo "$CATALOG_RESP" | sed '$d')
if [[ "$CATALOG_CODE" != "200" ]]; then
  echo "FAIL: catalog endpoint returned HTTP $CATALOG_CODE"
  echo "$CATALOG_BODY"
  docker compose -p msql-studio logs --tail=100 api-gateway
  exit 1
fi

TOTAL=$(echo "$CATALOG_BODY" | jq -r '.total // empty' 2>/dev/null || echo "")
if [[ -z "$TOTAL" || "$TOTAL" == "null" ]]; then
  echo "FAIL: catalog response malformed or missing total field"
  echo "$CATALOG_BODY"
  docker compose -p msql-studio logs --tail=100 api-gateway
  exit 1
fi
echo "  /api/v1/assignments -> 200 OK (total: $TOTAL)"
if (( TOTAL < 200 )); then
  echo "  WARNING: catalog total ($TOTAL) < 200 — run forced problems-sync then re-seed"
fi

# 3. :3000 200
CLIENT_RESP=$(curl -sS -w "\n%{http_code}" -o /dev/null http://127.0.0.1:3000/ || echo "000")
CLIENT_CODE=$(echo "$CLIENT_RESP" | tail -n1)
if [[ "$CLIENT_CODE" != "200" ]]; then
  echo "FAIL: client :3000 returned HTTP $CLIENT_CODE"
  docker compose -p msql-studio logs --tail=50 client
  exit 1
fi
echo "  :3000 -> 200 OK"

echo "=== [5/5] All checks passed ==="
echo "Fresh boot complete. Stack is healthy."