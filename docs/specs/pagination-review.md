# Pagination reviewer (CTO, 2026-09-09)

**Spec:** ADR 004 + `collection-endpoints-inventory.md`
**Evidence:** `docs/specs/pagination-test-evidence.md`
**Code:** `src/utils/query.ts` `parseCollectionQuery`; `GET /api/v1/assignments`; cleanup P6 cap.

Pass vs inventory P1–P5. Live catalog envelope matches ADR (`total`/`totalPages`, `q`, `filter[difficulty]`, sort whitelist, 400 on bad page/filter).

Admin collections not retrofitted to the envelope (slice 8 owned those lists). Acceptable.

No secrets in git. Additive `page`/`limit` defaults kept.
