# Pagination / search / filter / sort — live proof (CTO, 2026-09-09)

Against ADR 004 + inventory. Gateway `dev` includes `f91ae9c` (`parseCollectionQuery`) plus later slice8. Live `:8000` after image rebuild.

Gateway tests: **202 passed** (includes query helper + assignment collection).

| Check | Result |
|---|---|
| `GET /api/v1/assignments?page=1&limit=2` | 200 envelope `{ assignments, page, limit, total, totalPages }` |
| `page=0` | 400 |
| `filter[difficulty]=easy` | 200 |
| `q=slice8-proof` | 200 |
| `sort=title&order=asc` | 200 |
| `filter[nope]=x` | 400 |
| Already-correct endpoints | health/auth/execute unchanged (not collections) |
| `GET /internal/cleanup/old-schemas` | engineer added defensive page/limit cap (P6); not re-hit live (needs INTERNAL_API_KEY; not in this table) |

Admin list endpoints (`GET /api/v1/admin/assignments`, `/users`, `/audit`) stay simple `{ items }` this slice — ADR 004 allowed that; slice 8 spec did not require the catalog envelope there.

No product code in this proof besides the slice8 listUsers/setRole fix (separate commit).
