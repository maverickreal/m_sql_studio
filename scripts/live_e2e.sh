#!/usr/bin/env bash
# Live e2e through nginx-edge. No cookies. Exit nonzero on first miss.
set -euo pipefail
BASE="${LIVE_E2E_BASE:-http://127.0.0.1:8000}"
OID="650000000000000000000001"

fail() { echo "FAIL: $*" >&2; exit 1; }

code() {
  local method="$1" path="$2"
  shift 2
  curl -sS -o /tmp/live_e2e_body -w "%{http_code}" -X "$method" "${BASE}${path}" "$@"
}

h="$(code GET /health)"
[[ "$h" == "200" ]] || fail "health http $h"
python3 - <<'PY' || fail "health json"
import json
d=json.load(open("/tmp/live_e2e_body"))
assert d.get("status")=="ok", d
PY
echo "ok health"

a="$(code GET /api/v1/assignments)"
[[ "$a" == "200" ]] || fail "assignments http $a"
python3 - <<'PY' || fail "assignments envelope"
import json
d=json.load(open("/tmp/live_e2e_body"))
for k in ("assignments","page","limit","total","totalPages"):
    assert k in d, (k, d.keys())
assert isinstance(d["assignments"], list)
PY
echo "ok assignments envelope"

u="$(code GET /api/v1/admin/users)"
[[ "$u" == "401" ]] || fail "admin users want 401 got $u"
echo "ok admin 401"

e="$(code POST /api/v1/assignments/client-sql-code-run/execute -H 'content-type: application/json' -d '{}')"
[[ "$e" == "401" ]] || fail "execute want 401 got $e"
echo "ok execute 401"

l="$(code GET /api/v1/assignments/${OID}/last-sql)"
[[ "$l" == "401" ]] || fail "last-sql want 401 got $l"
echo "ok last-sql 401"

i="$(code GET /internal/cleanup/old-schemas)"
[[ "$i" == "401" ]] || fail "internal want 401 got $i"
echo "ok internal 401"

w="$(code POST /api/webhooks/github -H 'content-type: application/json' -d '{}')"
[[ "$w" == "401" ]] || fail "webhook want 401 got $w"
echo "ok webhook 401"

echo "PASS live_e2e ${BASE}"
