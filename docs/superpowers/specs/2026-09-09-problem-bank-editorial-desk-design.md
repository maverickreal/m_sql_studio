# Problem bank editorial desk (Option A)

**Date:** 2026-09-09  
**Status:** Draft for founder review (brainstorming lock)  
**Product:** MSqlStudio  
**Repos:** `m_sql_studio_problems` (files), `m_sql_studio_api_gateway` (ingest + catalog), `m_sql_studio_sandbox` (execute)  
**Supersedes / extends:** ADR 003 (git = editorial SoT for *files*; DB = query/runtime). Slice PB1 (webhook → Mongo `problems` only). This spec adds datasets, contribution tiers, test-before-write, promote-to-assignment, community origin.

This is a design spec. It is not an implementation slice and does not authorize engineer/devops cards until a finite done list is written.

---

## 1. Intent

GitHub is the **editorial desk** for community (and later first-party) problem **files**. Mongo + Postgres remain the **database** the app queries and runs.

Students never read GitHub at runtime. GitHub is not a query engine and is not “the database.”

If a problem exists in both GitHub and our DB, it arrived on GitHub first, passed the same class of tests as a first-party problem, then was materialized. Create and later edit use that same cycle. There is no silent Mongo edit of bank content and no automatic DB→git.

Community items are in the product with an explicit **community** origin so a bad problem is not read as official MSqlStudio content.

---

## 2. Authority

| Surface | Holds | Role |
|---|---|---|
| GitHub `m_sql_studio_problems` | Dataset SQL, problem YAML, `problem-v1.json` | People propose and change **files** (issue/PR). Versioning, diff, DCO, revert. |
| Mongo `problems` | Materialized YAML + `gitSha` + `path` | Cache of accepted files. Not the student catalog by itself. |
| Mongo `assignments` + `assignmentsolutions` | Catalog + grader SQL | What the SPA lists and the sandbox seeds. |
| Postgres `assignment_schema_<id>` | Tables from concatenated `initSql` | Runtime only; recreatable. |
| Mongo users / progress / ratings / audit | PII and runtime stats | DB-only. Never git. |

**Identity:** UUID v7 `id` in YAML. Path is not identity. **Drift:** `gitSha` (git blob SHA). If DB `gitSha` ≠ blob, rebuild from git after tests pass. Git file wins. Do not patch Mongo to “fix” a file.

**Rejected:** dual-write, auto DB→git, GitHub as catalog query layer, in-app portal as source of truth, forum-as-store.

---

## 3. Repo layout

```
datasets/<slug>/
  schema.sql      # CREATE TABLE only for this dataset
  seed.sql        # deterministic INSERT
  README.md       # short, optional
problems/<category>/<id>.yaml
schemas/problem-v1.json
```

`problem-v1.json` remains the YAML **file contract**. SQL datasets are a second public catalog. A problem must reference **≥1 published dataset slug**.

### 3.1 Problem YAML (additive fields)

Existing PB1 fields stay. Add:

- `datasets`: non-empty array of dataset slugs (must exist under `datasets/`)
- `overlaySql`: optional; extra tables/rows **on top of** named datasets
- `origin`: `community` | `first-party`
- `author`: GitHub handle only (already in PB1)

Do **not** add `contentHash` as identity or merge key.  
Do **not** add LeetCode-shaped fields (`test_cases`, `hints`, `statement`).

### 3.2 Contribution tiers

| Tier | PR contains | Allowed SQL | Merge bar |
|---|---|---|---|
| 1 default | Problem YAML | Read/write against named dataset tables. No CREATE/DROP/ALTER of those tables | Tests + deny-list + intelligence approval |
| 2 overlay | YAML + `overlaySql` | Extra tables or rows. Must not DROP/ALTER published dataset tables | Same, higher intelligence scrutiny |
| 3 new dataset | `datasets/<new-slug>/` (+ usually one problem that uses it) | New schema + finite deterministic seed | Maintainer merge only + tests of **all** problems that will use it |

---

## 4. Cycle (create and edit)

```
PR
  → CI: schema contract, tier rules, SQL deny-list, exact-clone check,
        runnable tests (same class as first-party)
  → Intelligence approval (human and/or AI) — pedagogy, near-dup, belonging
  → Merge (blocked until CI green + intelligence approval)
  → Webhook
  → Worker re-runs the same runnable tests on the merged blob
  → Only then: upsert Mongo `problems` AND Assignment + AssignmentSolution
              AND enqueue sandbox schema seed
```

**Accept means runnable.** It must be as unlikely that a newly accepted community assignment fails in-system as it is for a pre-existing first-party assignment. That guarantee is **tests**, not hope.

**Any write to our databases happens only after that guarantee.** No Mongo `problems` row, no `assignments` row, no Postgres schema, if tests have not passed. There is no half-state “file accepted, catalog empty because sandbox failed.” If the worker cannot prove the blob, it writes **nothing** and retries; the file may already be on GitHub — GitHub is not our database.

Edits (including admin “fix this SQL”) are another PR through the same cycle. An in-app control, if added later, **opens a PR**; it does not write bank content to Mongo.

---

## 5. Tests (the guarantee)

Run in CI (required status check, Postgres service) and again on the worker before DB write.

Against concatenated `datasets/*.sql` + optional `overlaySql`:

1. Apply init in an isolated schema (same idea as `verify_corpus1.js`).
2. Execute `solutionSql`.
3. Read mode: result matches `sampleOutput` (order per `orderMatters`).
4. Write mode: `validationSql` required; must pass against the solution outcome.
5. Statement timeout and row caps match sandbox limits.
6. Deterministic; no network.

First-party admin-created assignments keep today’s path unless a later slice unifies them. Community bank path **must not** be weaker than that path.

### 5.1 Deny-list (CI + worker)

Reject (non-exhaustive, extend in implementation): `COPY`, `GRANT`/`REVOKE`, `ALTER SYSTEM`, `SET ROLE`/`SET SESSION AUTHORIZATION`, `CREATE EXTENSION`, dblink, file_fdw, `pg_read_file` / `pg_ls_dir` / `lo_import` / `lo_export`, `COPY TO PROGRAM`, and any attempt to touch other schemas.

### 5.2 Exact-clone check (not a stored hash)

CI may fail a PR whose **normalized** (`datasets` slugs + `solutionSql`) equals another file. This is a cheap identical-clone gate only.

**Near-duplicates are intelligence**, not hashing.

**Do not store `contentHash` as a second source of truth.** Identity = UUID v7. Drift = `gitSha`.

---

## 6. Intelligence

**Intelligence** = human and/or AI. The spec does not require a person. Branch protection requires an approval from a maintainer account **or** an approved intelligence bot, in addition to tests. Tests alone do not merge (unless a later trusted-maintainer rule is explicitly added). How the bot is wired is an implementation detail; the rule is: pedagogy/near-dup/belonging is an intelligence gate, not a SQL test.

Intelligence judges: pedagogy, near-dup, whether the problem belongs, community vs later Adopt. Intelligence does not replace SQL tests.

---

## 7. Promote (after tests)

Single successful worker transaction conceptually:

- Upsert Mongo `problems` on `id` (`gitSha`, `path`, `deletedAt: null`).
- Create or update `Assignment` + `AssignmentSolution`.
  - `initSql` = snapshot of concatenated dataset schema+seed + overlay (sandbox stays one blob).
  - `origin: community` for contributor PRs; contributor = GitHub handle.
  - `origin: first-party` for maintainer-authored files that say so.
- Enqueue existing admin seed job → `pgSchemaReady`.
- Audit: `assignment.create` or `assignment.sync`.

Catalog UI: community **badge** and **filter**. Contributor handle shown. First-party seeds are not badged community.

**Adopt (optional, later):** maintainer PR sets `origin: first-party`. Same test gate. Not automatic.

If a **dataset** file changes: CI re-tests every problem that lists that slug before merge; after merge the worker rebuilds those assignments from git (tests, then write).

---

## 8. Failure and drift

| Event | Behavior |
|---|---|
| CI red | No merge. No DB write. |
| Intelligence missing | No merge (protection rule). |
| Webhook after green merge, tests still pass | Write `problems` + assignment + seed. |
| Worker tests fail or infra error | Write **nothing**. Retry. Alert. Fix via new PR if the blob is actually bad. |
| `gitSha` mismatch | Rebuild from git: tests then write. |
| Force-push | Full resync from HEAD; same test-then-write; tombstone ids missing at HEAD. |
| Invalid YAML | Skip that file; do not fail siblings; do not write a partial assignment for the bad file. |

---

## 9. Relation to PB1

PB1 already: HMAC webhook, BullMQ sync, Mongo `problems`, `problem-v1.json`, DCO, CC-BY-4.0.

This spec **tightens** PB1:

- Do not upsert `problems` for a file that has not passed runnable tests.
- After tests, also promote to live `assignments` (PB1 explicitly did not).
- Datasets + `datasets` field + overlay rules.
- `origin` + community catalog UX.

Webhook path stays `POST /api/webhooks/github` (or the single path already documented). No new microservice.

---

## 10. Out of scope

- In-app contribution portal or forum as authoring SoT (a later form that **opens a PR** is allowed as UX, not as a second writer)
- Automatic DB→git
- Using GitHub to serve the student catalog
- GitHub App registration (existing HITL)
- Polling backfill (PB2)
- Migrating historical first-party `seed.js` rows into git
- ML quality scores, auto-merge, trusted-maintainer
- New deployable / new database

---

## 11. Success criteria

1. Student catalog GETs never touch GitHub.
2. A merged problem YAML cannot land in Mongo or Postgres unless runnable tests passed.
3. Community assignments are visually distinct (`origin: community`) and filterable.
4. Edits to bank content happen only on GitHub and re-enter through the same tests.
5. UUID v7 identity; `gitSha` drift; no stored content-hash SoT.
6. Published datasets are the only schemas a default contribution may use.

---

## 12. Implementation note

Next step after founder sign-off on **this file**: a finite implementation plan (writing-plans), then kanban cards. Not this document.
