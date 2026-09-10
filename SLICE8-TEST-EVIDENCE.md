# Slice 8 — Tester Live Proof (2026-09-09 15:30 IST)

Re-ran `_live_proof.py` after CTO engineer patches (mongo fallback + ObjectId lookup in `setRole`). Stack rebuilt so `:8000` runs post-slice8 image via `nginx-edge`.

## Live :8000 / :3000 — 22/22 PASS

```
PASS unauth GET /admin/audit status=401
PASS unauth GET /admin/users status=401
PASS admin sign-in status=200 role=admin
PASS admin GET /users status=200 keys=['items']
PASS admin GET /assignments status=200
PASS admin POST assignment status=201 id=None
PASS signup keys status=200 top=['token', 'user']
PASS user session status=200 role=user id_set=True
PASS signup+adminSecret does not grant admin status=200 role=user
PASS non-admin GET /audit status=403
PASS non-admin setRole status=403
PASS admin promote user status=200
PASS admin demote user status=200
PASS audit has assignment.create status=200 actions=[...assignment.create...]
PASS audit has role.change status=200 n=10
PASS catalog envelope total/totalPages status=200 keys=['assignments', 'page', 'limit', 'total', 'totalPages']
PASS catalog page=0 is 400 status=400
PASS catalog filter difficulty status=200
PASS catalog search q status=200
PASS catalog sort title asc status=200
PASS unknown filter 400 status=400
PASS GET :3000/admin serves SPA status=200 len=719
SUMMARY pass=22 fail=0
```

## Acceptance criteria

1. **Non-admin blocked** — GET `/api/v1/admin/audit` → 401 (unauth) / 403 (non-admin session); setRole → 403. PASS.
2. **Admin actions** — sign-in role=admin; GET /users {items}; GET /assignments 200; POST assignment 201; promote user 200; demote user 200; audit has both `assignment.create` and `role.change`. PASS.
3. **adminSecret no longer grants admin** — signup with `adminSecret` in body → role=user. PASS.
4. **Evidence** — this file + `_live_proof_results.json` (22/22). PASS.

## Reproducible command

```bash
cd /Users/maverick/.hermes/profiles/swe/workspace/msql-studio
python3 m_sql_studio/docs/specs/_live_proof.py
```

No secrets in evidence files. No Forest/AdminJS/Retool. No product code changed by tester.
