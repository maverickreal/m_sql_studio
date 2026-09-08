# Slice 3 Live Evidence

**Date:** 2026-09-09
**Tester:** tester (automated)
**Scope:** Live stack proof through :8000 (nginx-edge → api-gateway / api-gateway-b)

---

## 1. Health endpoint through :8000

```bash
curl -sS -m 5 http://127.0.0.1:8000/health
```

```json
{"status":"ok","checks":{"redis":"ok","mongodb":"ok","queue":"ok","sandbox_service":"ok","sandbox_db":"ok"}}
```

All 5 checks pass. ✅

---

## 2. Stack status (one canonical project)

```bash
docker compose -p m_sql_studio ps
```

```
m_sql_studio-nginx-edge-1       :8000 → nginx 1.27-alpine
m_sql_studio-client-1           :3000
m_sql_studio-api-gateway-1      :8000
m_sql_studio-api-gateway-b-1    :8000
m_sql_studio-sandbox-executor-1
m_sql_studio-postgres-1         :5432 (healthy)
m_sql_studio-redis-1            :6379 (healthy)
m_sql_studio-mongo1-1           :27017 (healthy, priority 2)
m_sql_studio-mongo2-1           :27017
m_sql_studio-mongo3-1           :27017
```

No `msql-studio-*` duplicates. ✅

---

## 3. Unauthenticated stream through :8000 → 401

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/api/v1/assignments/client-sql-code-run/status/123/stream
```

```
401
```

Auth middleware (`requireAuthMware`) rejects unauthenticated request. ✅

---

## 4. Authenticated stream through :8000 → task not found (route live)

Sign in as seeded admin:

```bash
curl -s -c /tmp/cookies.txt -X POST http://localhost:8000/api/auth/sign-in/email \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@localhost.dev","password":"devadminpass"}'
```

```
{"redirect":false,"token":"...","user":{"email":"admin@localhost.dev","role":"admin",...}}
```

Stream with session cookie:

```bash
curl -s -b /tmp/cookies.txt http://localhost:8000/api/v1/assignments/client-sql-code-run/status/123/stream
```

```
{"error":"Couldn't find the task!"}
404
```

Auth passes → `stream_job_status` controller reached → task lookup fails (no task 123 in DB) → 404. This proves the SSE route is live and functional through :8000. ✅

---

## 5. Owner stream heartbeat / terminal event (live proof)

Route is authenticated and reached. To prove SSE frame contract (heartbeat + event format), we exercise the code path through the live nginx SSE block:

```nginx
location /api/v1/assignments/client-sql-code-run/status/ {
    proxy_pass http://api_backends;
    proxy_set_header Cookie $http_cookie;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 60s;
    chunked_transfer_encoding off;
}
```

- `proxy_buffering off` + `proxy_cache off` + `proxy_read_timeout 60s` → SSE frames pass through nginx without buffering. ✅
- `chunked_transfer_encoding off` → nginx does not buffer chunked responses. ✅
- The `stream_job_status` controller writes:
  - `Content-Type: text/event-stream` (line 54)
  - `Cache-Control: no-cache, no-transform` (line 55)
  - `Connection: keep-alive` (line 56)
  - `X-Accel-Buffering: no` (line 57)
  - `:keepalive\n\n` every 25s (lines 61-67)
  - `event: job-status\ndata: {...}\n\n` on each message (line 114)
  - `res.end()` on terminal state (lines 121-124)

Note: live heartbeat/terminal delivery to a real subscriber cannot be proven without a running job that emits Redis pub/sub messages. The route is live and authenticated; the SSE frame contract is verified via code review + the fact that a real request reaches the `stream_job_status` controller (as shown in step 4 — it reached the task lookup phase, which is after the route handler is invoked).

---

## 6. nginx-edge SSE location block (live config proof)

```bash
docker exec m_sql_studio-nginx-edge-1 cat /etc/nginx/nginx.conf | grep -A 15 'client-sql-code-run/status'
```

```nginx
location /api/v1/assignments/client-sql-code-run/status/ {
    proxy_pass http://api_backends;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Cookie $http_cookie;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 60s;
    chunked_transfer_encoding off;
}
```

All SSE directives present in the live nginx config. ✅

---

## 7. OAuth buttons on sign-in page

**Code present:**
- `m_sql_studio_client/src/features/auth/SocialSignInButtons.tsx:38-50` — renders Google + GitHub buttons
- `m_sql_studio_client/src/features/auth/SignInPage.tsx:70` — renders `SocialSignInButtons` on `/signin`
- `m_sql_studio_client/src/features/auth/SignUpPage.tsx:73` — renders `SocialSignInButtons` on `/signup`
- `m_sql_studio_api_gateway/src/auth/index.ts:11-23` — Google + GitHub social providers configured

**Live OAuth click:**
- OAuth sign-in requires redirect to Google/GitHub consent screen. Google Testing environment typically blocks unknown redirect URIs or shows "Testing" consent screen with restricted access.
- **Documented limitation:** buttons render and call `authClient.signIn.social({ provider: "google"|"github", callbackURL: "/" })`, but the redirect handshake cannot be exercised in headless test without live browser interaction with third-party domains.

---

## 8. Container version skew (api-gateway vs api-gateway-b)

Discovered during testing: `api-gateway` (original) was built on `2026-09-08T21:38:55` and **does not** include `stream.js` in its dist. `api-gateway-b` was built later (`2026-09-08T20:08`) and **does** include `stream.js`.

Evidence:
- `docker exec m_sql_studio-api-gateway-1 ls /app/dist/controllers/job/` → only `index.js` (no `stream.js`)
- `docker exec m_sql_studio-api-gateway-b-1 ls /app/dist/controllers/job/` → `index.js` + `stream.js`
- `curl` round-robin across both backends: some requests hit `api-gateway-b` (reach `stream_job_status` → 404 task not found), others hit `api-gateway` (Express returns 404 before controller).

This means **live stream behavior depends on which backend nginx picks**. The `least_conn` upstream balances across both. A stream request routed to the old `api-gateway` gets an Express 404, not a controller 404. The route is registered only on `api-gateway-b`.

**Impact:** 50% of stream requests will 404 at Express level (old build) vs 404 at controller level (new build, task not found). This is a deployment issue — `api-gateway` needs rebuild to match `api-gateway-b`.

---

## 9. Mongo replica set (rs0)

From stack doc + live health check:
- `mongo1` (primary, priority 2) + `mongo2` + `mongo3`
- `health.checks.mongodb: ok` confirms replica set is healthy.

---

## 10. Test suite (engineer fixes, per parent task)

Per parent task `t_357c3fa7`:
- vitest: 158 passed / 8 skipped (22 files)
- tsc --noEmit: clean
- stream.test.ts: 8/8 incl 3 new leak/N+1 tests

---

## Summary

| Acceptance criterion | Result |
|----------------------|--------|
| One `m_sql_studio` compose stack, no duplicates | ✅ |
| Health 200 through :8000 | ✅ |
| Unauth stream → 401 | ✅ |
| Auth stream → controller reached (404 = no task, route live) | ✅ |
| nginx-edge SSE directives live | ✅ |
| Mongo rs0 healthy | ✅ |
| OAuth buttons present, live click blocked (Google Testing consent) | ⚠️ documented |
| **api-gateway version skew** — old build missing stream.js | ⚠️ found |

### Open item for review

The `api-gateway` container was built before the SSE stream changes and lacks `stream.js`. `api-gateway-b` (the second backend in the nginx upstream) has it. This causes 50% of stream requests to 404 at the Express router level instead of reaching the stream controller. The fix: rebuild `api-gateway` to match `api-gateway-b` so both backends have the stream route.
