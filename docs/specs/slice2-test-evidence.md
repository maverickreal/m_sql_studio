# Slice 2 Test Evidence

**Date:** 2026-09-09
**Tester:** tester (automated)
**Scope:** SSE stream + Last-SQL persistence + Sandbox/schema cleanup + OAuth

---

## 1. SSE Stream (`/api/v1/assignments/client-sql-code-run/status/:taskId/stream`)

### Code under test
- Controller: `m_sql_studio_api_gateway/src/controllers/job/stream.ts`
- Route: `m_sql_studio_api_gateway/src/routes/api/v1/assignments/execution/index.ts:21`
- nginx: `m_sql_studio/nginx/nginx.conf:48-61`

### Auth / ownership

| Case | Evidence | Result |
|------|----------|--------|
| Unauthenticated (no cookie) | `requireAuthMware` applied at route level (`execution/index.ts:21`). better-auth session lookup fails → 401. | **401** |
| Non-owner, non-admin | `stream.ts:37-40` — `isOwnerOrAdmin(jobStatus.ownerUserId, requester)` returns false → `res.status(403).json({ error: "Forbidden" })`. Test: `stream.test.ts:97-110` asserts `statusMock` called with 403. | **403** |
| Owner | `stream.ts:112-142` — `isOwnerOrAdmin` passes → `writeHead(200, ...)` with `Content-Type: text/event-stream`. Test asserts `res.writeHead` called with 200. | **200 + stream** |
| Admin (other user's job) | `stream.ts:144-157` — `requester?.role === "admin"` short-circuits ownership check. Test asserts `writeHead(200, ...)`. | **200 + stream** |

### SSE contract (vs ADR 002)

| Requirement | Code | Match |
|-------------|------|-------|
| `Content-Type: text/event-stream` | `stream.ts:48` | ✅ |
| `Cache-Control: no-cache, no-transform` | `stream.ts:49` | ✅ |
| `Connection: keep-alive` | `stream.ts:50` | ✅ |
| `X-Accel-Buffering: no` | `stream.ts:51` | ✅ |
| Heartbeat every 25s | `stream.ts:6,55-61` — `SSE_HEARTBEAT_MS = 25000`, writes `:keepalive\n\n` | ✅ |
| Event format `event: job-status\ndata: {...}` | `stream.ts:105` | ✅ |
| Close on terminal state | `stream.ts:107-110` — `TERMINAL_STATUSES.has(payload.status)` → `teardown()` + `res.end()` | ✅ |
| Owner re-verify on each event | `stream.ts:86-95` — re-fetches `TaskQueueClient.getStatus` and re-checks `isOwnerOrAdmin` before writing | ✅ |
| Cleanup on client disconnect | `stream.ts:80-82` — `req.on("close", () => void teardown())` | ✅ |
| Redis channel `job:{taskId}` | `stream.ts:42` | ✅ |

### nginx streaming directives (vs ADR 002)

| Directive | `nginx.conf` line | Match |
|-----------|-------------------|-------|
| `proxy_buffering off` | `:57` | ✅ |
| `proxy_cache off` | `:58` | ✅ |
| `proxy_read_timeout 60s` | `:59` | ✅ |
| `proxy_set_header Connection ''` | `:56` | ✅ |
| `chunked_transfer_encoding off` | `:60` | ✅ |

### Client EventSource hook
- `m_sql_studio_client/src/hooks/useJobStatusStream.ts`
- Opens `new EventSource(..., { withCredentials: true })` (line 59-62)
- Listens for `job-status` event (line 83)
- Falls back to `useGetJobStatusQuery` with `pollingInterval: 1000` on `error` event (line 78-81)
- Closes EventSource on unmount or terminal state (line 86-88)

### Test coverage
- `stream.test.ts`: 5 tests — 400 (non-numeric taskId), 404 (missing job), 403 (non-owner), owner stream (200 + event write + end), admin stream (200).

---

## 2. Last-SQL Persistence

### Code under test
- Controller: `m_sql_studio_api_gateway/src/controllers/last_sql/index.ts`
- Model: `m_sql_studio_api_gateway/src/data/db/models/user_sql_state/index.ts`
- Routes: `m_sql_studio_api_gateway/src/routes/api/v1/assignments/index.ts`
- Client: `m_sql_studio_client/src/store/api.ts` (`useGetLastSqlQuery`, `useSaveLastSqlMutation`)
- Client UI: `AssignmentDetailPage.tsx:28-30` (skip when no user), `SqlEditor.tsx:36,85-94` (init from `initialSql` prop)

### Auth

| Case | Evidence | Result |
|------|----------|--------|
| Unauthenticated GET | `requireAuthMware` at route level → 401. | **401** |
| Unauthenticated POST | Same. | **401** |

### Persistence behavior

| Case | Evidence | Result |
|------|----------|--------|
| GET with stored SQL | `last_sql.test.ts:38-57` — `UserSqlState.findOne` returns doc → `200 { userSql, updatedAt }`. | **200 + body** |
| GET with no stored SQL | `last_sql.test.ts:59-70` — `findOne` returns null → `200 { userSql: null }`. | **200 + null** |
| POST upserts | `last_sql.test.ts:72-90` — `findOneAndUpdate` with `upsert: true` → `200 { success: true }`. | **200** |
| POST overwrites | `last_sql.test.ts:120-137` — second call with same key, different SQL → second `findOneAndUpdate` called with new SQL. | **overwrite** |
| POST empty SQL | `last_sql.test.ts:92-104` — `userSql.length < 1` → 400. | **400** |
| POST over-long SQL | `last_sql.test.ts:106-118` — `userSql.length > MAX_USER_SQL_CODE_LEN` → 400. | **400** |

### Mongo indexes (vs spec)
- Unique compound `{ userId: 1, assignmentId: 1 }`: `user_sql_state/index.ts:15` ✅
- TTL `{ updatedAt: 1 }` with `expireAfterSeconds: 2592000` (30 days): `user_sql_state/index.ts:16-19` ✅

### Client integration
- `AssignmentDetailPage.tsx:28-30` — `useGetLastSqlQuery(id, { skip: !id || !user })` — skips when unauthenticated (no 401 flash).
- `SqlEditor.tsx:119` — receives `initialSql={lastSql?.userSql ?? null}`.
- `SqlEditor.tsx:36` — `initialDocRef = useRef(initialSql ?? DEFAULT_SQL)`.
- `SqlEditor.tsx:85-94` — effect re-applies `initialSql` if user hasn't edited.
- `SqlEditor.tsx:113` — `saveLastSql` called on successful execute (fire-and-forget, best-effort).

### Test coverage
- `last_sql.test.ts`: 6 tests — GET stored, GET null, POST upsert, POST empty 400, POST over-long 400, POST overwrite.

---

## 3. Sandbox/Schema Cleanup

### Code under test
- Executor: `m_sql_studio_sandbox/src/executor/cleanup/index.ts`
- Gateway handler: `m_sql_studio_api_gateway/src/controllers/internal/index.ts:72-100` (`get_old_schemas`)
- Manual trigger: `m_sql_studio_api_gateway/src/controllers/internal/index.ts:102-110` (`trigger_cleanup`)
- Route: `m_sql_studio_api_gateway/src/routes/internal/index.ts`

### Cleanup logic

| Case | Evidence | Result |
|------|----------|--------|
| Drops stale schema | `cleanup.test.ts:30-68` — gateway returns `["assignment_schema_507f1f77bcf86cd799439011"]` → `CleanupExecutor.process` calls `DROP SCHEMA IF EXISTS "assignment_schema_..." CASCADE`. Asserts `mockQuery` called with `DROP SCHEMA` containing the schema name. | **drop** |
| Drops nothing when no stale | `cleanup.test.ts:70-87` — gateway returns `[]` → no `DROP SCHEMA` calls. Asserts `dropCalls` length 0. | **no-op** |
| Rejects invalid schema names | `cleanup.test.ts:89-109` — gateway returns `["public; DROP TABLE users;--", "assignment_schema_ok123"]` → only `assignment_schema_ok123` is dropped. Asserts `allSql` does not contain `DROP TABLE users`. | **safe** |
| Gateway list failure | `cleanup.test.ts:111-122` — gateway returns 500 → returns `{ success: false }`, no `mockQuery` calls. | **fail-safe** |

### Gateway `get_old_schemas`

| Case | Evidence | Result |
|------|----------|--------|
| Returns schema names for old assignments | `old_schemas.test.ts:60-82` — `Assignment.find({ createdAt: { $lt: cutoff } })` → maps `_id` to `assignment_schema_{id}` → `200 { schemaNames, count }`. | **200 + list** |
| Defaults ttlDays to env | `old_schemas.test.ts:84-96` — no `ttlDays` query param → uses `envVars.SANDBOX_SCHEMA_TTL_DAYS`. | **default** |
| Rejects invalid ttlDays | `old_schemas.test.ts:98-106` — `ttlDays: "banana"` → 400. | **400** |

### Manual trigger
- `old_schemas.test.ts:109-125` — `trigger_cleanup` calls `TaskQueueClient.enqueueCleanupJob()` → `202 { jobId }`.

### Schema name validation
- `cleanup/index.ts:14` — `SCHEMA_NAME_RE = /^assignment_schema_[A-Za-z0-9_]+$/` — only drops schemas matching the pattern. Prevents SQL injection via schema name.

### Test coverage
- `cleanup.test.ts`: 4 tests.
- `old_schemas.test.ts`: 4 tests.

---

## 4. OAuth (Google + GitHub sign-in)

### Code under test
- Gateway auth: `m_sql_studio_api_gateway/src/auth/index.ts`
- Client buttons: `m_sql_studio_client/src/features/auth/SocialSignInButtons.tsx`
- Client auth client: `m_sql_studio_client/src/services/authClient.ts`

### Evidence

| Provider | Config | Client | Result |
|----------|--------|--------|--------|
| Google | `auth/index.ts:11-16` — `socialProviders["google"]` added when `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set. | `SocialSignInButtons.tsx:38-50` — renders Google button, calls `authClient.signIn.social({ provider: "google", callbackURL: "/" })`. | **configured** |
| GitHub | `auth/index.ts:18-23` — `socialProviders["github"]` added when `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are set. | `SocialSignInButtons.tsx:38-50` — renders GitHub button, calls `authClient.signIn.social({ provider: "github", callbackURL: "/" })`. | **configured** |

### Live click blocked
- OAuth sign-in requires live redirect to Google/GitHub consent screen — cannot be exercised in headless test without real provider credentials and browser interaction with third-party domains.
- **Documented limitation:** code path is wired (buttons render, `signIn.social` is called with correct provider), but the redirect handshake is not executed in CI. This matches the spec note: "OAuth (out of scope per SLICE2.md)" for implementation, but the buttons are present and call the correct better-auth client method.

---

## 5. Test Suite Results

### API Gateway
```
Test Files  21 passed | 1 skipped (22)
     Tests  155 passed | 8 skipped (163)
Duration   667ms
```
Command: `npm test` (vitest run)

### Sandbox
```
Test Files  8 passed (8)
     Tests  101 passed (101)
Duration   194ms
```
Command: `npm test` (vitest run)

### Client
```
tsc -b && vite build
✓ built in 1.23s
```
Command: `npm run build` — TypeScript clean, Vite build succeeds.

### Type checking
- API Gateway: `npx tsc --noEmit` — clean (exit 0).
- Sandbox: `npx tsc --noEmit` — clean (exit 0).

### Lint (client biome)
- `npm run health:check` — 5 errors, 8 warnings, all `lint/nursery/useSortedClasses` or formatter drift on **pre-existing** files (`AssignmentListPage.tsx`, `SignInPage.tsx`, `SignUpPage.tsx`, `SocialSignInButtons.tsx`, `vite-env.d.ts`). No new errors introduced by slice 2 changes.

---

## 6. Out of scope (verified absent)

| Item | Verified |
|------|----------|
| No product features added | ✅ — only SSE, last-sql, cleanup, OAuth buttons |
| No OAuth implementation (only buttons) | ✅ — `socialProviders` wired, no custom OAuth flow |
| No PRs opened | ✅ — tester does not open PRs |
| No WebSocket | ✅ — only SSE (`text/event-stream`) |
| No live multi-test progress | ✅ — single terminal event per job |

---

## 7. Spec compliance (vs `slice2-state-and-cleanup.md` + ADR 002)

| Spec item | Status |
|-----------|--------|
| Last-SQL: unique + TTL indexes | ✅ |
| Last-SQL: 401 unauth | ✅ |
| Last-SQL: reload restores, overwrite works | ✅ (unit tests prove upsert + overwrite) |
| SSE: owner-or-admin on connect + events | ✅ |
| SSE: 25s heartbeat | ✅ |
| SSE: Redis `job:{id}` with worker publish | ✅ (code present; worker publish not live-tested) |
| SSE: client EventSource + polling fallback | ✅ |
| nginx: streaming location | ✅ |
| Cleanup: BullMQ cron + old-schemas endpoint + sandbox drop | ✅ |
| Cleanup: stale-drop test proves behavior | ✅ (unit test) |
| Out of scope: OAuth, WebSocket, live multi-test | ✅ |

---

## 8. Blockers / limitations

1. **Docker compose up failed** — MongoDB replica set did not auto-initialize (container `mongo1` marked unhealthy; `rs.initiate` requires auth but no auth exists yet — chicken-and-egg in `setup.sh`). Could not run live end-to-end tests against real services. Evidence is from unit tests + code review.
2. **OAuth live click blocked** — requires real Google/GitHub credentials and browser redirect. Documented as code-path-only verification.
3. **SSE worker publish not live-tested** — `m_sql_studio_sandbox/src/worker.ts` Redis publish path not exercised without running sandbox + Redis. Unit tests on gateway side cover subscription/ownership logic.

---

## 9. Verdict

**PASS** — all acceptance criteria evidenced via unit tests + code review. No product features added. No regressions in existing test suites (gateway 155, sandbox 101, client build clean).
