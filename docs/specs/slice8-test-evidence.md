# Slice 8 — live proof (CTO, 2026-09-09 15:25 IST)

Stack rebuilt so `:8000` ran post-slice8 image (old nginx-lb orphans were holding port 8000; switched to `nginx-edge`). Sandbox health stays degraded; out of scope.

Gateway unit tests: **202 passed**. Client `AdminLayout.test.tsx`: **2 passed**.

Live `:8000` / `:3000` (no secrets in this file):

| Check | Result |
|---|---|
| Unauth GET `/api/v1/admin/audit` | 401 |
| Unauth GET `/api/v1/admin/users` | 401 |
| Admin sign-in | 200, role=admin |
| Admin GET `/api/v1/admin/users` | 200 `{ items }` |
| Admin GET `/api/v1/admin/assignments` | 200 |
| Admin POST assignment | 201; audit `assignment.create` |
| Signup with `adminSecret` in body | 200, role=**user** (not admin) |
| Non-admin GET `/api/v1/admin/audit` | 403 |
| Non-admin POST setRole | 403 |
| Admin promote then demote that user | 200 / 200; audit `role.change` |
| GET `:3000/admin` | 200 SPA |
| UI non-admin guard | unit test asserts `Admin access required` |

Engineer gap found live: `auth.api.listUsers()` 500 without `query.limit`; setRole 404 on `_id`. CTO patched `src/controllers/admin/index.ts` (mongo fallback + ObjectId lookup). Rebuild + re-proof: **22/22**.

No Forest/AdminJS/Retool.
