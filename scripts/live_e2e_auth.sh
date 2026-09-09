#!/usr/bin/env bash
# Live logged-in e2e through nginx-edge. Email/password session (not OAuth).
# Exit nonzero on first miss. Never prints session tokens.
set -euo pipefail
BASE="${LIVE_E2E_BASE:-http://127.0.0.1:8000}"
ORIGIN="${LIVE_E2E_ORIGIN:-http://127.0.0.1:3000}"
COOKIE_JAR="$(mktemp)"
BODY="$(mktemp)"
trap 'rm -f "$COOKIE_JAR" "$BODY"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

http() {
  local method="$1" path="$2"
  shift 2
  curl -sS -o "$BODY" -w "%{http_code}" -X "$method" \
    -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
    -H "origin: ${ORIGIN}" \
    "${BASE}${path}" "$@"
}

EMAIL="e2e.learner.$(date +%s)@example.com"
PASS="E2ePass_12345"

s="$(http POST /api/auth/sign-up/email -H 'content-type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\",\"name\":\"E2E Learner\"}")"
[[ "$s" == "200" ]] || fail "signup http $s body=$(head -c 200 "$BODY")"
python3 - "$BODY" <<'PY' || fail "signup json"
import json, sys
d=json.load(open(sys.argv[1]))
assert d.get("user", {}).get("role") == "user", d
assert d.get("user", {}).get("email"), d
PY
echo "ok signup"

a="$(http GET '/api/v1/assignments?limit=1')"
[[ "$a" == "200" ]] || fail "assignments http $a"
AID="$(python3 - "$BODY" <<'PY'
import json, sys
d=json.load(open(sys.argv[1]))
items=d.get("assignments") or []
assert items, d
print(items[0]["_id"])
PY
)"
[[ -n "$AID" ]] || fail "no assignment id"

l="$(http GET "/api/v1/assignments/${AID}/last-sql")"
[[ "$l" == "200" ]] || fail "last-sql want 200 got $l body=$(head -c 200 "$BODY")"
python3 - "$BODY" <<'PY' || fail "last-sql json"
import json, sys
d=json.load(open(sys.argv[1]))
assert "userSql" in d, d
PY
echo "ok last-sql 200 cookie"

e="$(http POST /api/v1/assignments/client-sql-code-run/execute \
  -H 'content-type: application/json' \
  -d "{\"assignmentId\":\"${AID}\",\"userSql\":\"SELECT 1\"}")"
[[ "$e" == "202" || "$e" == "200" ]] || fail "execute want 202/200 got $e body=$(head -c 200 "$BODY")"
python3 - "$BODY" <<'PY' || fail "execute json"
import json, sys
d=json.load(open(sys.argv[1]))
assert d.get("taskId"), d
PY
echo "ok execute 202 cookie"

u="$(http GET /api/v1/admin/users)"
[[ "$u" == "403" ]] || fail "admin want 403 got $u body=$(head -c 200 "$BODY")"
echo "ok admin 403 learner"

# sign-in with same credentials (second session path)
COOKIE_JAR2="$(mktemp)"
trap 'rm -f "$COOKIE_JAR" "$COOKIE_JAR2" "$BODY"' EXIT
si="$(curl -sS -o "$BODY" -w "%{http_code}" -X POST \
  -c "$COOKIE_JAR2" -H "origin: ${ORIGIN}" -H 'content-type: application/json' \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASS}\"}" \
  "${BASE}/api/auth/sign-in/email")"
[[ "$si" == "200" ]] || fail "sign-in http $si body=$(head -c 200 "$BODY")"
ls2="$(curl -sS -o "$BODY" -w "%{http_code}" -b "$COOKIE_JAR2" -H "origin: ${ORIGIN}" \
  "${BASE}/api/v1/assignments/${AID}/last-sql")"
[[ "$ls2" == "200" ]] || fail "sign-in last-sql want 200 got $ls2"
echo "ok sign-in cookie"

echo "PASS live_e2e_auth ${BASE}"
