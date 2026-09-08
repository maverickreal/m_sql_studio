# Spec — Slice 2: state persistence + sandbox/schema cleanup

**Status:** accepted for slice 2
**Date:** 2026-09-09
**Follows:** `company/SLICE2.md` items 2 (Last-SQL persistence) and 3 (Sandbox/schema cleanup)

## Part A — Last-SQL persistence

### Goal

Persist the last submitted SQL per (userId, assignmentId) so that reloading the assignment page restores the editor content. A new submit overwrites the previous value. Unauthenticated requests return 401.

### Mongo collection

- Collection name: `user_sql_states`
- Database: same as the API Gateway's existing Mongo database (`API_GATEWAY_MONGO_DB`)

### Document schema

```ts
{
  userId: string;          // better-auth user id
  assignmentId: string;    // Mongo ObjectId string of the Assignment
  userSql: string;         // last submitted SQL (raw text, up to MAX_USER_SQL_CODE_LEN)
  updatedAt: Date;         // last submit time
}
```

### Indexes

1. **Unique compound index** on `{ userId: 1, assignmentId: 1 }` — one document per user-assignment pair. This is the primary lookup key.
2. **TTL index** on `{ updatedAt: 1 }` with `expireAfterSeconds: 2592000` (30 days). Documents not updated in 30 days are auto-deleted by MongoDB. This is a soft cap — the data is small and we do not need it forever. 30 days is a reasonable default; tune via env if needed.

### API endpoints

Both endpoints require `requireAuthMware` (cookie → better-auth session). Unauthenticated → 401.

#### `GET /api/v1/assignments/:assignmentId/last-sql`

- Auth: `requireAuthMware`
- Params: `assignmentId` (validated via existing `validateObjectId` middleware)
- Logic:
  1. Look up `{ userId: req.user.id, assignmentId }` in `user_sql_states`.
  2. If found → `200 { userSql: "...", updatedAt: "..." }`.
  3. If not found → `200 { userSql: null }` (no stored SQL yet — client shows the default `SELECT * FROM users LIMIT 5;`).
- Response:
  ```json
  { "userSql": "SELECT * FROM users LIMIT 5;", "updatedAt": "2026-09-09T10:00:00Z" }
  ```
  or
  ```json
  { "userSql": null }
  ```

#### `POST /api/v1/assignments/:assignmentId/last-sql`

- Auth: `requireAuthMware`
- Params: `assignmentId` (validated via `validateObjectId`)
- Body:
  ```json
  { "userSql": "SELECT * FROM users LIMIT 5;" }
  ```
- Validation: `userSql` is a non-empty string, max `MAX_USER_SQL_CODE_LEN` (5000). Invalid → 400.
- Logic:
  1. Upsert: `{ userId: req.user.id, assignmentId }` → set `userSql` and `updatedAt: new Date()`.
  2. The unique index ensures one document per pair.
- Response: `200 { success: true }`

### Client integration

- On `AssignmentDetailPage` mount (after the assignment detail loads), call `GET /api/v1/assignments/:assignmentId/last-sql`. If `userSql` is non-null, initialize the CodeMirror editor with it. If null, keep the existing default (`SELECT * FROM users LIMIT 5;`).
- On successful `executeSql` (when the user runs a query), call `POST /api/v1/assignments/:assignmentId/last-sql` with the submitted SQL. Fire-and-forget — do not block the UI on this. If it fails, log but do not show an error to the user (the SQL already executed; persistence is best-effort).
- New RTK Query endpoints: `useGetLastSqlQuery` and `useSaveLastSqlMutation` added to the existing `api.ts`.

### Files to change

- `m_sql_studio_api_gateway/src/data/db/models/user_sql_state/index.ts` — new Mongoose model.
- `m_sql_studio_api_gateway/src/controllers/assignment/index.ts` — add `get_last_sql` and `save_last_sql` handlers (or a new `last_sql` controller file).
- `m_sql_studio_api_gateway/src/routes/api/v1/assignments/index.ts` — add the two routes.
- `m_sql_studio_client/src/store/api.ts` — add `useGetLastSqlQuery` and `useSaveLastSqlMutation`.
- `m_sql_studio_client/src/features/assignments/AssignmentDetailPage.tsx` — fetch last SQL on mount, initialize editor.
- `m_sql_studio_client/src/features/sql-editor/SqlEditor.tsx` — accept an initial SQL prop (or read from the store), call `saveLastSql` on successful execution.

### Verification

1. Sign in, open an assignment, type `SELECT 1;`, run it. Reload the page. The editor shows `SELECT 1;` (not the default).
2. Type `SELECT 2;`, run it. Reload. The editor shows `SELECT 2;` (overwrite works).
3. Open a different assignment. The editor shows the default (or that assignment's last SQL if one exists).
4. Sign out, open an assignment → editor shows default (no 401 flash; the `skip` option in the query hook skips when unauthenticated).
5. Direct API test:
   ```sh
   curl -sS -c /tmp/msql.cj -b /tmp/msql.cj http://127.0.0.1:8000/api/v1/assignments/:assignmentId/last-sql
   # → { "userSql": "SELECT 1;", "updatedAt": "..." }
   ```
6. Unauthenticated test:
   ```sh
   curl -sS http://127.0.0.1:8000/api/v1/assignments/:assignmentId/last-sql
   # → 401
   ```
7. TTL check: after creating a document, verify the TTL index exists:
   ```sh
   mongosh --eval "db.user_sql_states.getIndexes()"
   # → confirm TTL index on updatedAt with expireAfterSeconds: 2592000
   ```

---

## Part B — Sandbox/schema cleanup

### Goal

A scheduled BullMQ job that drops isolated Postgres schemas older than N days (N in env, default 7) and trims old job-result keys. The job can also be triggered manually for testing.

### Env variables

| Variable | Default | Description |
|---|---|---|
| `SANDBOX_SCHEMA_TTL_DAYS` | `7` | Schemas older than this many days are dropped. |
| `CLEANUP_JOB_CRON` | `0 3 * * *` | Cron schedule for the cleanup job (daily at 03:00). |
| `JOB_RESULT_TTL_DAYS` | `30` | BullMQ job-result keys older than this are trimmed (via existing `removeOnComplete`/`removeOnFail` TTL, but this env lets us tune it). |

### BullMQ job

- Job name: `client_sql_studio_cleanup` (add to `utils/constants/index.ts`).
- Queue: same `BULLMQ_SQL_QUEUE_NAME` as the SQL execution jobs.
- Schedule: via `bullmq`'s `QueueScheduler` (or a cron-enabled repeatable job) using `CLEANUP_JOB_CRON`.
- The job is enqueued once at gateway startup (in `index.ts`, after `TaskQueueClient.connect()`), with `repeat` options for the cron schedule.

### Cleanup logic (sandbox worker)

Add a new executor class `CleanupExecutor` in `m_sql_studio_sandbox/src/executor/cleanup/index.ts`:

1. **Drop old schemas:**
   - Query Postgres for schemas matching `assignment_schema_%` pattern:
     ```sql
     SELECT schema_name FROM information_schema.schemata
     WHERE schema_name LIKE 'assignment_schema_%'
     ```
   - For each schema, check if the corresponding Assignment still exists in Mongo (via the sandbox worker's existing `API_GATEWAY_URL` internal endpoint, or by parsing the assignment id from the schema name and querying Mongo — but the sandbox worker does not have Mongo access, so use the gateway).
   - If the Assignment does not exist (deleted) OR the schema is older than `SANDBOX_SCHEMA_TTL_DAYS` (compare against the Assignment's `createdAt` — but since deleted assignments have no record, the rule is simpler: **drop schemas whose assignment no longer exists in Mongo, and drop schemas older than N days even if the assignment exists**).
   - Actually, simpler and safer rule: **drop schemas whose assignment no longer exists in Mongo** (orphaned schemas from failed seed jobs — this is the existing `cleanup_assignment` internal endpoint's job, but it only fires on seed failure). The scheduled job is a backstop.
   - For age-based cleanup: the sandbox worker does not know the assignment's age directly. Add a new internal endpoint on the gateway: `GET /internal/cleanup/old-schemas?ttlDays=N` that returns a list of schema names to drop (the gateway queries Mongo for assignments older than N days and returns their `sandboxDbId` values). The sandbox worker then drops those schemas.
   - Drop each schema: `DROP SCHEMA IF EXISTS :schemaName CASCADE`.

2. **Trim old job-result keys:**
   - This is already handled by BullMQ's `removeOnComplete` / `removeOnFail` with `age: JOB_TTL_S` (600 s = 10 min). The `JOB_RESULT_TTL_DAYS` env is a no-op if the existing TTL is sufficient. If we want longer retention for debugging, increase `JOB_TTL_S`. For now, the scheduled job does not need to do anything extra here — just log the current job counts for observability.

### New internal endpoints (gateway)

#### `GET /internal/cleanup/old-schemas?ttlDays=N`

- Auth: `reqHeadIntApiKeyValidMware` (existing internal API key middleware).
- Query param: `ttlDays` (defaults to `SANDBOX_SCHEMA_TTL_DAYS` env if not provided).
- Logic:
  1. Calculate cutoff date: `now() - ttlDays`.
  2. Query Mongo for assignments with `createdAt < cutoffDate`, project `_id`.
  3. Map each `_id` to `getSandboxDBSchemaIdForAssignment(_id)`.
  4. Return `200 { schemaNames: ["assignment_schema_...", ...], count: N }`.

#### `POST /internal/cleanup/drop-schema`

- Auth: `reqHeadIntApiKeyValidMware`.
- Body: `{ "schemaName": "assignment_schema_..." }`.
- Logic: validate the schema name matches the expected pattern, then return `200 { success: true }` (the sandbox worker does the actual `DROP SCHEMA`; this endpoint is a no-op confirmation for now, or can be used by the sandbox worker to confirm the drop is authorized).
- Actually, simpler: the sandbox worker drops schemas directly. This endpoint is not needed. The sandbox worker calls `GET /internal/cleanup/old-schemas` to get the list, then drops them directly.

### Files to change

- `m_sql_studio_api_gateway/src/utils/constants/index.ts` — add `CLEANUP_JOB_NAME`, `SANDBOX_SCHEMA_TTL_DAYS` default, `CLEANUP_JOB_CRON` default.
- `m_sql_studio_api_gateway/src/config/env/index.ts` — add `SANDBOX_SCHEMA_TTL_DAYS`, `CLEANUP_JOB_CRON`, `JOB_RESULT_TTL_DAYS` to the zod schema.
- `m_sql_studio_api_gateway/src/controllers/internal/index.ts` — add `get_old_schemas` handler.
- `m_sql_studio_api_gateway/src/routes/internal/index.ts` — add `GET /cleanup/old-schemas`.
- `m_sql_studio_api_gateway/src/index.ts` — enqueue the repeatable cleanup job at startup.
- `m_sql_studio_sandbox/src/executor/cleanup/index.ts` — new `CleanupExecutor` class.
- `m_sql_studio_sandbox/src/worker.ts` — add a new `Worker` for the cleanup queue (or reuse the existing worker with a job name check — but a separate worker is cleaner since the cleanup job has different data shapes).
- `m_sql_studio_sandbox/src/utils/constants/index.ts` — add `CLEANUP_JOB_NAME`.

### Verification

1. **Manual trigger test:** Add a temporary `POST /internal/cleanup/trigger` endpoint (dev-only, `ENV_MODE === DEV`) that enqueues a cleanup job. Call it:
   ```sh
   curl -sS -X POST http://127.0.0.1:8000/internal/cleanup/trigger \
     -H 'x-internal-api-key: <key>' \
     -H 'Content-Type: application/json'
   ```
   Check the sandbox worker logs — it should log the schemas it drops.
2. **Stale schema test:** Manually create a schema in Postgres: `CREATE SCHEMA assignment_schema_test_old;`. Insert an assignment in Mongo with `_id` matching the schema suffix and `createdAt` set to 30 days ago. Trigger cleanup. Verify the schema is dropped.
3. **Active schema preserved:** Create a schema for an assignment with `createdAt` now. Trigger cleanup with `ttlDays=7`. Verify the schema is NOT dropped.
4. **Cron schedule test:** Set `CLEANUP_JOB_CRON` to `* * * * *` (every minute) temporarily. Wait 2 minutes. Check logs — the job should run.
5. **Unauthenticated test:** Call the cleanup endpoint without the internal API key → 401.
6. **Job counts:** After cleanup, check BullMQ job counts via the gateway's existing health check or a new log line.

## Out of scope

- OAuth (out of scope per SLICE2.md).
- Dropping schemas that are actively in use (the age check prevents this — schemas younger than N days are never dropped).
- Archiving schemas before drop (no need; they are recreatable from the assignment's `initSql`).
- Real-time cleanup (the scheduled job runs daily; on-demand cleanup is a dev-only convenience).
