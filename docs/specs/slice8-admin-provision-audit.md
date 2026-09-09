# Slice 8 — admin UI, provision, audit

**Locked:** `workspace/company/SLICE8.md` (2026-09-09)
**Workdir:** `/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/`
**Branch:** `dev` on `m_sql_studio_api_gateway` and `m_sql_studio_client`. Orchestrator README only if a TODO is now false.
**Stack unchanged.** Own UI only (no Forest/AdminJS/Retool/Refine). No SIEM, impersonation, ban UI, WebSocket, OAuth recode, spend.

## Current code (do not rewrite)

- Gateway admin router: `src/routes/api/v1/admin/index.ts` — `requireAuthMware` + `requireAdminMware`, **only** `POST /assignments`.
- Create controller: `src/controllers/admin/index.ts`.
- better-auth already has `admin({ defaultRole: "user", adminRoles: ["admin"] })` in `src/auth/index.ts`. Signup hook still accepts `adminSecret === ADMIN_SECRET_CODE` → strip that hook.
- `DEFAULT_ADMIN_*` seed on boot **stays**.
- Client: only ` /admin/assignments/new` (`CreateAssignmentPage`). Navbar link for admins exists.
- Non-admin hitting create already shows “Admin access required” via loader — reuse that pattern.

## Routes (gateway)

All under `/api/v1/admin`, same two middlewares. Unauth → **401**. Auth but not admin → **403** (existing `requireAdminMware`).

| Method | Path | Body / query | Success |
|---|---|---|---|
| POST | `/assignments` | existing create body | **keep** |
| GET | `/assignments` | none | `{ items: [{ _id, title, difficulty, mode, createdAt }] }` newest first. No pagination this slice. |
| GET | `/users` | none | better-auth admin **list users**: `{ items: [{ id, email, name, role }] }`. Do not invent a parallel users collection. |
| POST | `/users/:id/role` | `{ "role": "admin" \| "user" }` | better-auth admin **setRole**. Actor must already be admin. Cannot demote the last remaining admin (409). After success, write audit. |
| GET | `/audit` | optional `?limit=50` (clamp 1–200, default 50) | `{ items: AuditRow[] }` newest first. |

Do not add PATCH/DELETE users. Do not add impersonation.

## Audit (Mongo)

Collection `audit_log`, append-only. **No updates, no deletes** from app code. No TTL.

```ts
{
  actorId: string,          // required
  action: "assignment.create" | "role.change",
  targetType: "assignment" | "user",
  targetId: string,         // assignment _id or user id
  at: Date,                 // default now
  meta?: { from?: string; to?: string }  // role.change only
}
```

Write:

1. After successful `POST /assignments` → `assignment.create`.
2. After successful `POST /users/:id/role` → `role.change` with `meta.from` / `meta.to`.

Failed requests write **nothing**.

## better-auth provision

- Use the admin plugin API already on the server (`auth.api.listUsers` / `auth.api.setRole` or the equivalent installed version — check `better-auth` docs for the version in package.json; do not add a new plugin).
- Remove the `adminSecret` signup path and any client field that sends it.
- `ADMIN_SECRET_CODE` may remain in env for now but must not gate signup. Do not add it as a product feature.
- Seed admin via `DEFAULT_ADMIN_*` remains the bootstrap.

## Vite pages (`m_sql_studio_client`)

Add an `/admin` shell (layout) with three nav items. Reuse existing “Admin access required” for non-admin. Routes:

| Path | Page |
|---|---|
| `/admin` | redirect to `/admin/assignments` |
| `/admin/assignments` | table: title, difficulty, mode, createdAt. Keep a link to existing `/admin/assignments/new`. |
| `/admin/users` | table: email, name, role. Button promote `user` → `admin` and demote `admin` → `user` (confirm). Calls `POST /api/v1/admin/users/:id/role`. |
| `/admin/audit` | table: at, actorId, action, targetType, targetId. Read-only. |
| `/admin/assignments/new` | **keep** CreateAssignmentPage |

Navbar: one “Admin” target `/admin` (not only “new assignment”).

RTK/fetch: follow existing `src/store/api.ts` style. Credentials same as other API calls.

## 401 / 403

| Caller | Result |
|---|---|
| No session on any `/api/v1/admin/*` | 401 |
| Logged-in non-admin on those APIs | 403 |
| Non-admin client `/admin/*` | same “Admin access required” UI as create (no data flash) |
| Last-admin demote | 409, no audit row |

## Verify (tester)

Through `:8000` (API) and `:3000` (UI):

1. Seed/default admin can open `/admin`, see assignment list, user list, audit table.
2. Admin promotes a normal user → user.role is admin; audit has `role.change`.
3. That user can now open `/admin`.
4. Admin creates an assignment (existing form) → audit has `assignment.create`.
5. Non-admin GET `/api/v1/admin/audit` → 403; UI `/admin` blocked.
6. Unauth GET → 401.
7. Signup with a random `adminSecret` does **not** grant admin.

`npm test` green in gateway (new tests for 401/403/audit writes/last-admin 409). Client: no Playwright this slice; a loader/guard unit test is enough if cheap.

Commit + push `origin/dev` on both repos. Never `.env`.

## Out of scope

Forest/AdminJS/Retool, impersonation, SIEM, pagination of audit, RBAC beyond `user`↔`admin`, OAuth, nginx, sandbox, problem-bank.
