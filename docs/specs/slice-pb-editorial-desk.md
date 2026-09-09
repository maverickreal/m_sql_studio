# Slice PB — Editorial Desk Implementation Plan

**Locked design:** `m_sql_studio/docs/superpowers/specs/2026-09-09-problem-bank-editorial-desk-design.md` (commit 7d3dc25)
**Parent spec:** Slice PB1 (`slice-pb1-github-problem-bank.md`)
**Branch:** `dev`
**Artifact:** This file at `m_sql_studio/docs/specs/slice-pb-editorial-desk.md`
**Completion:** Commit + push `origin/dev`. Stop when file exists. No app code. No next cards.

---

## Scope

Implement the **editorial desk** cycle for community + first-party problems:
- Datasets as reusable SQL catalog (`datasets/<slug>/schema.sql + seed.sql`)
- Problem YAML gains `datasets[]`, `overlaySql`, `origin`, `author`
- Contribution tiers (1=default, 2=overlay, 3=new dataset)
- **Tests run in CI (Postgres) AND on worker before any DB write**
- Intelligence gate (human/AI approval via branch protection)
- Worker: re-run tests on merged blob → only then upsert Mongo `problems` + create `Assignment` + `AssignmentSolution` + enqueue sandbox seed
- Community badge/filter in catalog (`origin: community`)
- Drift handling via `gitSha` (rebuild from git)
- Webhook path pinned: `POST /api/webhooks/github` (existing gateway route)

**Out of scope** (per design): in-app portal, DB→git, GitHub App, polling backfill, migration of historical seeds, ML scores, auto-merge, new deployable.

---

## Finite Done List

### 1. Content Repo (`m_sql_studio_problems`) — extends PB1

| # | Task | Acceptance |
|---|------|------------|
| 1.1 | Add `datasets/` directory with `problem-v1.json` updated for new fields | `datasets/` exists; schema validates new fields |
| 1.2 | Add sample dataset `datasets/hr/` with `schema.sql` + `seed.sql` | Files present; deterministic seed |
| 1.3 | Update `.github/workflows/validate-problems.yml`: validate `datasets[]` refs exist, tier rules, deny-list, exact-clone gate | CI fails on missing dataset ref, invalid tier, deny-list hit, exact clone |
| 1.4 | Branch protection on `main`: require CI + **intelligence approval** (maintainer or approved bot) | Protection rule active; tests + approval required to merge |

### 2. Gateway Ingest (`m_sql_studio_api_gateway`, branch `dev`)

| # | Task | Acceptance |
|---|------|------------|
| 2.1 | Pin live webhook path: document `POST /api/webhooks/github` in `m_sql_studio/README.md` | One paragraph in README confirms path |
| 2.2 | Worker: fetch merged blob via GitHub API (or `GITHUB_PROBLEMS_LOCAL_DIR` in DEV) | Worker reads file content for changed YAMLs |
| 2.3 | **Runnable test executor** (shared lib, used by CI + worker):<br>• Apply `datasets/*.sql` + `overlaySql` in isolated Postgres schema<br>• Execute `solutionSql`<br>• Read mode: compare to `sampleOutput` (order per `orderMatters`)<br>• Write mode: run `validationSql` against outcome<br>• Statement timeout + row caps = sandbox limits<br>• Deterministic, no network | Unit tests green; integration test against real Postgres passes |
| 2.4 | Deny-list enforcement (CI + worker): `COPY`, `GRANT`/`REVOKE`, `ALTER SYSTEM`, `SET ROLE`/`SET SESSION AUTHORIZATION`, `CREATE EXTENSION`, `dblink`, `file_fdw`, `pg_read_file`/`pg_ls_dir`/`lo_import`/`lo_export`, `COPY TO PROGRAM`, cross-schema access | CI rejects; worker rejects |
| 2.5 | Worker transaction (conceptually atomic):<br>• Re-run tests on merged blob<br>• **Only if pass**: upsert Mongo `problems` (`id`, `gitSha`, `path`, `deletedAt: null`)<br>• Create/update `Assignment` + `AssignmentSolution`:<br>  - `initSql` = concatenated dataset schema+seed + overlay snapshot<br>  - `origin: community` (contributor PR) or `first-party` (maintainer file)<br>  - `contributor` = GitHub handle<br>• Enqueue existing admin seed job → `pgSchemaReady`<br>• Audit: `assignment.create` / `assignment.sync` | Worker test: push valid PR → DB rows created; push failing tests → **zero** DB writes, retry alert |
| 2.6 | Drift handler: on `gitSha` mismatch or force-push, full resync from HEAD (tests → write; tombstone missing ids) | Force-push test: stale `gitSha` → rebuild passes |
| 2.7 | Invalid YAML: skip file, log, continue siblings; no partial assignment | Mixed push test: one bad + one good → good upserts, bad skipped |
| 2.8 | Tests (must pass `npm test`):<br>- HMAC mismatch → 401<br>- Valid push → 202, worker upserts after tests pass<br>- Duplicate deliveryId → second skipped<br>- Invalid YAML skipped, sibling upserts<br>- Deleted file → `deletedAt` set<br>- **Tests fail → no DB write, retry**<br>- **Tests pass → DB write**<br>- Drift rebuild works | All named tests green |

### 3. Catalog API (`m_sql_studio_api_gateway`)

| # | Task | Acceptance |
|---|------|------------|
| 3.1 | `GET /api/assignments` (or existing catalog endpoint): add `origin` filter (`community` | `first-party` | `all`) and return `origin` + `contributor` on each item | Filter works; community items show badge data |
| 3.2 | Ensure ADR 004 contract (pagination, search, filter, sort) is respected | No regression on ADR 004 |

### 4. Sandbox / Seed (existing job)

| # | Task | Acceptance |
|---|------|------------|
| 4.1 | No code change — existing admin seed job enqueued by worker handles `initSql` → Postgres schema | Worker enqueues; seed job runs; `pgSchemaReady` emitted |

### 5. Client (SPA) — `m_sql_studio_client`

| # | Task | Acceptance |
|---|------|------------|
| 5.1 | Catalog UI: add **community badge** (visual) and **origin filter** (All / First-party / Community) | Badge visible; filter toggles list |
| 5.2 | Contributor handle displayed on community assignment detail | Handle shown |

---

## Cross-Cutting

- **No GitHub App** — webhook remains HMAC on `POST /api/webhooks/github`
- **GitHub = files, DB = catalog** — zero direct GitHub reads at student runtime
- **Tests before write** — enforced in CI (required check) AND worker (gate before upsert)
- **UUID v7 identity** — path is not identity; `gitSha` is drift signal
- **No `contentHash` stored** — identity = UUID, drift = `gitSha`
- **Intelligence gate** — branch protection requires approval (maintainer or bot) in addition to CI

---

## Test-First Order (enforced)

1. Test executor library (unit + Postgres integration)
2. Deny-list tests
3. Worker integration: push → test → DB write / no-write
4. Drift rebuild test
5. Catalog filter test
6. Client badge/filter test

---

## Repos & Branches

| Repo | Branch | Notes |
|------|--------|-------|
| `m_sql_studio_problems` | `main` | Content repo; branch protection added |
| `m_sql_studio_api_gateway` | `dev` | Webhook, worker, catalog API |
| `m_sql_studio_client` | `dev` | Catalog UI badge + filter |

---

## Verification Commands

```bash
# Content repo
gh api repos/maverickreal/m_sql_studio_problems --jq .visibility
# → PUBLIC
gh api repos/maverickreal/m_sql_studio_problems/branches/main/protection --jq '.required_status_checks.contexts[]'
# → includes CI workflow + "intelligence-approval"

# Gateway
cd m_sql_studio_api_gateway && npm test
# → all named tests green

# Client
cd m_sql_studio_client && npm test
# → badge/filter tests green
```

---

## Dependencies

- ADR 003 (GitHub + DB dual store) — already committed
- ADR 004 (collection API contract) — already committed
- Slice PB1 (webhook + Mongo `problems` sync) — already implemented on `dev`
- Existing sandbox seed job (`pgSchemaReady`) — unchanged

---

## Non-Goals (Explicit)

- No in-app contribution form
- No automatic DB→git sync
- No GitHub App installation
- No polling cron (PB2)
- No migration of historical `seed.js` assignments
- No ML quality scoring
- No auto-merge / trusted-maintainer rule
- No new microservice or database