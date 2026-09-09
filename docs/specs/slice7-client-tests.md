# Slice 7 — client tests + docs truth

**Repo:** `m_sql_studio_client` (tests/docs) + `m_sql_studio` (README TODOs)
**Branch:** `dev`

## Implement

### 1. Vitest in the client

- Add `vitest` + `jsdom` (and `@testing-library/react` if hooks need it). Vite 6 compatible.
- Script: `"test": "vitest run"`.
- Do not add Playwright/Cypress this slice.

### 2. `useJobStatusStream` tests (`src/hooks/useJobStatusStream.test.ts`)

Mock `EventSource` on `window`.

Must pass:

1. **completed** — fake EventSource fires `job-status` with `{status:"completed", result:{...}}` → store gets `executionCompleted`; source closed.
2. **failed** — same for `{status:"failed"}` → `executionFailed`.
3. **onerror fallback** — EventSource `onerror` → hook enables RTK `useGetJobStatusQuery` polling (`skip` becomes false / pollingInterval 1000). Assert the fallback path is taken (spy or store).

Keep `withCredentials: true` on EventSource (already in hook). Do not change stream URL.

### 3. Last-SQL restore

Existing: `AssignmentDetailPage` passes `initialSql={lastSql?.userSql ?? null}` into `SqlEditor`.

Test that when last-sql query returns `{ userSql: "SELECT 1" }`, the editor initial doc is that string (not the default `SELECT * FROM users LIMIT 5;`). Prefer a small unit test of the mapping / SqlEditor `initialSql` prop over a full CodeMirror mount if CodeMirror is painful — if so, extract a 5-line `initialDoc(initialSql)` helper and test that. Do not rewrite the editor.

### 4. Docs

- `m_sql_studio/README.md` TODOs: shipped items (nginx/LB, periodic cleanup, last-SQL, OAuth) must not still read as open work. Leave AI as remaining (HITL).
- `m_sql_studio_client/AGENTS.md`: SQL execution is EventSource on `/status/:taskId/stream` with 1s polling **fallback**, not primary polling.

## Stop

`npm test` green in client. `npm run health:check` no new errors. Commit + push `origin/dev`. Never `.env`.

## Out of scope

Docker, nginx, OAuth recode, AI, new product, Playwright.
