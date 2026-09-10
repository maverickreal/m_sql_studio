# MSqlStudio — Slice 8 (locked 2026-09-09)

**Workdir:** `/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/` (`dev` on all four)
**Owner:** `@swe`
**Why:** Founder approved: own admin UI, better-auth provisioning, audit logs. Not Forest/AdminJS/Retool. Not SIEM.

## Out of scope

- Forest, AdminJS, Retool, Refine
- Impersonation, ban UI, full RBAC rewrite
- SIEM / third-party audit SaaS
- WebSocket, OAuth live-click, PRs unless founder says
- Stack change
- `ADMIN_SECRET_CODE` as a product feature (remove from signup path)

## Done (finite)

1. **Admin UI (own, Vite)** — existing client only. `/admin` shell:
   - Assignments: keep create; add list (title, difficulty, mode, created)
   - Users: list email/name/role; promote/demote `user` ↔ `admin`
   - Audit: table of recent events
   Non-admin hitting `/admin/*` → same “Admin access required” as create. Stop when an admin can do all three in the UI through `:3000` / API `:8000`.

2. **Provisioning via better-auth admin plugin** — `setRole` / list users through better-auth (already `admin({ defaultRole: "user", adminRoles: ["admin"] })`). `DEFAULT_ADMIN_*` seed on boot stays. Remove the `adminSecret` signup hook. Stop when an existing admin can promote a user without the secret code, and a non-admin cannot.

3. **Audit logs** — Mongo append-only collection (e.g. `audit_log`): `{ actorId, action, targetType, targetId, at }`. Write on: assignment create, role change. `GET /api/v1/admin/audit` admin-only. Stop when those two actions produce rows and non-admin GET is 403.

## Pipeline

architect (impl spec) → engineer (code) → tester → reviewer
