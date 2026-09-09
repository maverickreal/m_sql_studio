# Slice PB1 — GitHub problem bank (graft onto MSqlStudio)

**Locked:** 2026-09-09 (founder: graft + webhook allowed; CC-BY-4.0 + DCO; handle-only)
**Workdir:** `/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/`
**Branches:** `dev` (gateway, orchestrator). New public repo `m_sql_studio_problems` default branch `main`.
**ADR:** `workspace/adr-github-db-dual-problem-store.md` (003). This spec **overrides** ADR §4.4 file schema: problems are **SQL assignments**, not LeetCode two-sum.

## Founder lock

- Product = part of MSqlStudio. Not a new deployable.
- Public content repo + inbound webhook allowed. GitHub App registration is a later HITL click (not this slice).
- License = CC-BY-4.0 + DCO. Attribution = GitHub handle only, no PII.
- Cost = $0. Local HTTP. No certs. No cloud.

## Stack (unchanged)

Same gateway + sandbox + Mongo + Redis + Compose. **No new microservice.**

| Piece | Where |
|---|---|
| Content (git SoT) | new public repo `maverickreal/m_sql_studio_problems` |
| Webhook + HMAC | existing Express gateway `POST /webhooks/github` (no session auth) |
| Sync job | BullMQ name `client_sql_studio_problems_sync` on existing Redis |
| Materialization | Mongo collections `problems`, `sync_state` |
| Runtime / PII | existing `assignments`, solutions, users, progress — **untouched** |

## Schema (git file)

Path: `problems/<category>/<id>.yaml`. Identity = UUID v7 `id` in YAML, **not** path.

```yaml
id: "01234567-89ab-7cde-89ab-0123456789ab"  # UUID v7, immutable
slug: "employees-above-avg-salary"          # unique, URL-safe
title: "Employees above average salary"
description: |
  Write a query that returns employees whose salary is above the department average.
difficulty: easy          # enum: easy | medium | hard
mode: read                # enum: read | write
category: joins           # directory must match
sampleInput:
  - "employees(id, dept_id, salary)"
sampleOutput: "id\n1\n3"
initSql: |
  CREATE TABLE employees (...);
  INSERT INTO employees VALUES (...);
solutionSql: |
  SELECT ...;
validationSql: |
  SELECT ...;
orderMatters: false
author: "octocat"         # GitHub handle only
license: "CC-BY-4.0"
schema_version: 1
```

JSON Schema: `schemas/problem-v1.json`. CI must reject extra LeetCode fields (`test_cases`, `hints`, `statement`) so the graft stays SQL-native.

## Done (finite)

### A. Content repo (`m_sql_studio_problems`) — @devops

1. `gh repo create maverickreal/m_sql_studio_problems --public` from local dir under `workspace/msql-studio/m_sql_studio_problems`.
2. Files: `LICENSE` (CC-BY-4.0), `CONTRIBUTING.md` (DCO sign-off required; no CLA), `CODEOWNERS`, issue templates (`propose-problem.yml`, `report-data-error.yml`), `schemas/problem-v1.json`, `.github/workflows/validate-problems.yml` (ajv + slug/id uniqueness), one sample YAML under `problems/joins/`.
3. Branch protection **not** required this slice (founder can click later). Force-push to `main` still discouraged.
4. Push `origin/main`. Never commit secrets.

Stop when: repo exists, public, Actions workflow file present, `gh api repos/maverickreal/m_sql_studio_problems --jq .visibility` = `PUBLIC`.

### B. Gateway ingest — @engineer (`m_sql_studio_api_gateway`, branch `dev`)

1. Env: `GITHUB_WEBHOOK_SECRET` (required in prod/staging; in DEV may default to `dev-webhook-secret` for tests). `GITHUB_PROBLEMS_REPO` default `maverickreal/m_sql_studio_problems`. Never log the secret. Never commit `.env`.
2. `POST /webhooks/github`
   - Verify `X-Hub-Signature-256` = `sha256=` + HMAC-SHA256(body, secret). Mismatch → 401. Missing header → 401.
   - Ignore events other than `push` (read `X-GitHub-Event`). Return 204.
   - On `push`: enqueue BullMQ job `client_sql_studio_problems_sync` with `{ deliveryId, ref, afterSha, forced, commits[] }`. Return 202. Dedup by `X-GitHub-Delivery` (store last N in Redis, TTL 24h).
   - Rate-limit: existing global limiter is enough; do not add a public HTML page.
3. Worker (same process pattern as cleanup/seed — **gateway-side**, not sandbox):
   - Only files matching `problems/**/*.yaml`.
   - Fetch blob via GitHub API **or** (DEV) read from a local fixture dir `GITHUB_PROBLEMS_LOCAL_DIR`.
   - Validate with `problem-v1.json` + zod. Invalid file → log + skip (do not fail whole job).
   - Upsert Mongo `problems` on `id`. Store `gitSha`, `path`, `deletedAt: null`.
   - If file removed in the push: set `deletedAt`.
   - If `forced: true`: full resync of `problems/` tree (tombstone ids missing at HEAD).
   - Update `sync_state` singleton `{ repo, lastSha, lastDeliveryId, lastSyncAt }`.
4. `POST /internal/problems-sync` (existing `internalRouter`, not public) — enqueue the same job with `{ reason: "manual" }`. For local/dev without GitHub.
5. Tests (must pass `npm test`):
   - HMAC mismatch → 401
   - HMAC ok + push with one yaml → 202 and worker upserts the document
   - Same delivery id twice → second enqueue skipped
   - Invalid yaml skipped; valid sibling still upserts
   - Deleted file → `deletedAt` set
6. **Do not** write `Assignment` / `AssignmentSolution`. **Do not** add `problemId` on assignments this slice. **Do not** register a GitHub App. **Do not** change nginx except if a new public path needs to skip auth (webhook must not go through `requireAuthMware`).

Stop when: tests green, commit + push `origin/dev`. Never `.env`.

### C. Orchestrator note — @engineer or @devops if nginx needed

Webhook is on the gateway. If nginx-edge only proxies `/api/`, add `location /webhooks/github` → gateway. If `/api` already prefixes, **do not** invent a second path — then the route is `POST /api/webhooks/github` and this spec's path becomes that. Pick **one** and document it in `m_sql_studio/README.md` one paragraph. Prefer `POST /api/webhooks/github` if that avoids nginx edits.

## Out of scope

- GitHub App / installation tokens (HITL card, later)
- Polling backfill cron (slice PB2)
- Linking `assignments.problemId`, migrating existing assignments
- Admin UI for problems; reverse DB→git
- Contributor web form
- Cloud deploy, tunnels, certs
- Auto-merge, trusted-maintainer
- Knowledge graph

## Verify

```bash
# A
gh api repos/maverickreal/m_sql_studio_problems --jq .visibility

# B (gateway)
cd m_sql_studio_api_gateway && npm test
# HMAC 401 + upsert tests named in the worker/webhook test file
```

## Pipeline

devops (repo) ∥ engineer (ingest) → tester → reviewer
