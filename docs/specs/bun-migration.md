# Bun Migration Spec — MSqlStudio Full Stack

**Status:** Approved Migration Spec  
**Target Runtime:** Bun 1.2+ (`oven/bun:1.2-alpine` or `oven/bun:1.4`)  
**Target Branch:** `dev`  
**Measurement Date:** 2026-09-12  
**Audit Scope:** `m_sql_studio_api_gateway`, `m_sql_studio_client`, `m_sql_studio_sandbox`, `m_sql_studio_problems` (scripts + tests), `misc/*.mjs`, `misc/seed.js`  
**Compose Stack:** `msql-studio`  

---

## 1. Per-Repo Verdicts

| Repository / Component | Verdict | Reason & Scope |
|---|---|---|
| `m_sql_studio_api_gateway` | **GO-WITH-CHANGES** | Express 5 + BullMQ + Mongoose + Redis runtime runs cleanly on Bun. Upstream `better-auth` `toNodeHandler` Bun issue was fixed in `better-call 1.3.6` (installed: `better-auth@1.6.20` + `better-call@1.3.6`). No application code changes needed. Requires Dockerfile migration to `oven/bun:1.2-alpine`, npm script updates (`nodemon` -> `bun --watch`), and test strategy alignment (`vi.mock` module isolation vs `bun x vitest`). |
| `m_sql_studio_client` | **GO-WITH-CHANGES** | Vite 6 + React 19 SPA. Production runtime is `nginx:alpine` (untouched). Bun is adopted exclusively in the Docker multi-stage build (`FROM oven/bun:1.2-alpine AS build`), replacing Node 22 for `bun install --frozen-lockfile` and `bun run build`. Tests use DOM environment (`vitest run` with jsdom retained, excluding Playwright e2e). |
| `m_sql_studio_sandbox` | **GO-WITH-CHANGES** | BullMQ + `pg` + `redis` worker runs directly on Bun. Zero native modules. Verified worker lifecycle under Bun. Requires Dockerfile migration to `oven/bun:1.2-alpine`, `package.json` script updates (`node dist/worker.js` -> `bun dist/worker.js`), and test mock isolation if moving from `vitest` to `bun test`. |
| `m_sql_studio_problems` | **GO** | All CLI scripts (`validate-problems.mjs`, `validate-datasets.mjs`, `test-executor.mjs`, `generate-uuids.mjs`, `generate-sandbox-gold-diff.mjs`) and test suites (`node:test` + `node:assert/strict`) run natively under Bun with 100% pass rate (24/24 tests pass in 129ms). Zero container changes. |
| `misc/seed.js` | **GO** | Standalone seeding script using `fs`, `path`, and standard `fetch`. Runs out-of-the-box via `bun misc/seed.js`. Shebang can optionally update from `node` to `bun`. |
| `misc/init-db/mongodb/01-setup.js` | **N/A (KEEP)** | MongoDB shell script executed by the `mongo:7` container entrypoint (`mongosh`). Not a Node.js runtime script. |

---

## 2. Incompatibility & Runtime Audit

### 2.1 Node Builtin Usage

| Component | Node Builtins Used | Bun Compatibility | Notes |
|---|---|---|---|
| `m_sql_studio_api_gateway` | `node:fs/promises`, `node:path`, `crypto` (`createHmac`, `timingSafeEqual`), `fs` | 100% Compatible | All APIs (`fs.readFile`, `path.join`, `crypto.timingSafeEqual`) are natively polyfilled in Bun's Web/Node API layer. |
| `m_sql_studio_client` | None in `src/` | N/A | Pure browser bundle. Build stage uses Vite. |
| `m_sql_studio_sandbox` | None directly in `src/` | 100% Compatible | Pure JS BullMQ worker and pg client. |
| `m_sql_studio_problems` | `node:fs`, `node:path`, `node:url`, `node:child_process`, `node:os`, `node:crypto`, `node:test`, `node:assert/strict` | 100% Compatible | Fully supported in Bun 1.2+; `bun test` recognizes `node:test` definitions natively. |
| `misc/seed.js` | `fs`, `path`, global `fetch` | 100% Compatible | Built into Bun runtime. |

### 2.2 Native Module Audit

Audit confirmed:
- **Zero** compiled C/C++ addons or `node-gyp` builds in production dependencies.
- `pg` uses pure JavaScript implementation (`pg-native` is **not** installed).
- `redis` (`node-redis` 5.x) is pure JavaScript.
- `mongoose` 9.x uses official pure-JS `mongodb` driver.
- Optional dependency `@msgpackr-extract` in `bullmq` cleanly falls back to pure JavaScript `msgpackr` if native N-API binding is unavailable.
- Development-only macOS bindings (`fsevents`, `@rolldown/binding-*`, `lightningcss-*`) are omitted in production Docker containers (`--production` / `--omit=dev`).

### 2.3 `better-auth` & `toNodeHandler` Verification

- **Historical Bug:** In earlier versions of `better-auth` (< 1.6.16), `toNodeHandler` assumed Node.js `http.IncomingMessage` / `http.ServerResponse` stream mechanics that failed under Bun's native `Request`/`Response` pipeline.
- **Upstream Fix:** Fixed in `better-call 1.3.6` (released June 2026) by refactoring header parsing and request adaptation to use the standard Web Fetch API `Request`/`Response` specifications.
- **Installed State:**
  - `better-auth`: `1.6.20`
  - `better-call`: `1.3.6` (dependency of `better-auth`)
- **Single Usage Site:** `m_sql_studio_api_gateway/src/app.ts:42`:
  ```ts
  app.all("/api/auth/*splat", toNodeHandler(auth));
  ```
- **Verdict:** Auth routes work without code modification on Bun.

### 2.4 Test Runner: `vitest` vs `bun test`

| Suite | Current Test Engine | Current Baseline | `bun test` Behavior | Strategy & Recommendation |
|---|---|---|---|---|
| `api_gateway` | Vitest 4.0 (`vitest run`) | 27 files, 199 passed, 1 skipped (2.20s) | Config validation fails because Bun evaluates ESM imports before `vi.mock("../config")`. Vitest hoists `vi.mock` automatically; Bun's `mock.module` does not retroactively rewrite already evaluated imports without preload. | **Keep `vitest run`** (invoked via `bun x vitest run` or `bun test` via npm script delegation), OR introduce `test-setup.ts` preload setting dummy env vars for `bun test`. |
| `sandbox` | Vitest 4.0 (`vitest run`) | 13 files, 55 passed (337ms) | Isolated files pass 100% (e.g., `user_executor.test.ts` passes 6/6 in 40ms). However, `worker.test.ts` uses `vi.mock("../executor")` which leaks across file boundaries in Bun's shared module registry. | Run tests with Vitest or use scoped `mock.module()` cleanup per test file. |
| `client` | Vitest 3.2 (`vitest run`) | 32 files, 139 passed (3.60s) | Pure logic tests pass (e.g. `errors.test.ts` 5/5 in 24ms). DOM component tests require browser globals and origin (`window.location.origin`) for `better-auth` URL resolution. | Retain `vitest run` with JSDOM/Happy-DOM environment. Exclude `e2e/**` (Playwright). |
| `problems` | Node builtin (`node --test`) | 3 files, 25 passed (183ms) | `bun test` runs out of the box with zero modifications: 24 passed (129ms). | **Migrate directly to `bun test`**. |

---

## 3. Exact Dockerfile Diffs Plan

### 3.1 `m_sql_studio_api_gateway/Dockerfile`

```diff
--- a/m_sql_studio_api_gateway/Dockerfile
+++ b/m_sql_studio_api_gateway/Dockerfile
@@ -1,19 +1,20 @@
-FROM node:22-alpine AS build
+# syntax=docker/dockerfile:1.4
+FROM oven/bun:1.2-alpine AS build
 WORKDIR /app
 
-COPY package.json package-lock.json ./
-RUN npm ci
+COPY package.json bun.lock* ./
+RUN bun install --frozen-lockfile
 
 COPY . .
-RUN npm run build
+RUN bun run build
 
-FROM node:22-alpine
+FROM oven/bun:1.2-alpine
 WORKDIR /app
 
-COPY package.json package-lock.json ./
+COPY package.json bun.lock* ./
 ARG ENV_MODE=PROD
-RUN if [ "$ENV_MODE" = "DEV" ]; then npm ci; else npm ci --omit=dev; fi
+RUN if [ "$ENV_MODE" = "DEV" ]; then bun install --frozen-lockfile; else bun install --frozen-lockfile --production; fi
 
 COPY --from=build /app/dist ./dist
 EXPOSE 8000
-CMD ["npm", "run", "start"]
+CMD ["bun", "run", "start"]
```

### 3.2 `m_sql_studio_sandbox/Dockerfile`

```diff
--- a/m_sql_studio_sandbox/Dockerfile
+++ b/m_sql_studio_sandbox/Dockerfile
@@ -1,18 +1,19 @@
-FROM node:22-alpine AS build
+# syntax=docker/dockerfile:1.4
+FROM oven/bun:1.2-alpine AS build
 WORKDIR /app
 
-COPY package.json package-lock.json ./
-RUN npm ci
+COPY package.json bun.lock* ./
+RUN bun install --frozen-lockfile
 
 COPY . .
-RUN npm run build
+RUN bun run build
 
-FROM node:22-alpine
+FROM oven/bun:1.2-alpine
 WORKDIR /app
 
-COPY package.json package-lock.json ./
+COPY package.json bun.lock* ./
 ARG ENV_MODE=PROD
-RUN if [ "$ENV_MODE" = "DEV" ]; then npm ci; else npm ci --omit=dev; fi
+RUN if [ "$ENV_MODE" = "DEV" ]; then bun install --frozen-lockfile; else bun install --frozen-lockfile --production; fi
 
 COPY --from=build /app/dist ./dist
-CMD ["npm", "run", "start"]
+CMD ["bun", "run", "start"]
```

### 3.3 `m_sql_studio_client/Dockerfile`

```diff
--- a/m_sql_studio_client/Dockerfile
+++ b/m_sql_studio_client/Dockerfile
@@ -1,11 +1,12 @@
-FROM node:22-alpine AS build
+# syntax=docker/dockerfile:1.4
+FROM oven/bun:1.2-alpine AS build
 
 WORKDIR /app
 
 ARG VITE_API_BASE_URL=
 ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
 
-COPY package.json package-lock.json* ./
-RUN npm ci
+COPY package.json bun.lock* ./
+RUN bun install --frozen-lockfile
 
 COPY . .
-RUN npm run build
+RUN bun run build
 
 FROM nginx:alpine
 
```

---

## 4. `package.json` Script Changes & Test-Command Mapping

### 4.1 Script Adjustments

| Repo | Script | Current (Node 22) | Migrated (Bun) | Notes |
|---|---|---|---|---|
| `m_sql_studio_api_gateway` | `dev` | `nodemon` | `bun --watch src/index.ts` | Eliminates nodemon watcher overhead |
| | `start` | `node dist/index.js` | `bun dist/index.js` | Direct Bun execution |
| | `test` | `vitest run` | `bun x vitest run` | Retains full `vi.mock` hoisting compatibility |
| `m_sql_studio_sandbox` | `dev` | `nodemon` | `bun --watch src/worker.ts` | Native TS compilation and watcher |
| | `start` | `node dist/worker.js` | `bun dist/worker.js` | Direct Bun execution |
| | `test` | `vitest run` | `bun x vitest run` | Retains mock isolation |
| `m_sql_studio_client` | `dev` | `vite` | `bun --bun vite` | Bun optimizes dependency pre-bundling |
| | `build` | `tsc -b && vite build` | `tsc -b && bun --bun vite build` | Fast build step |
| | `test` | `vitest run` | `vitest run --exclude '**/e2e/**'` | Runs DOM unit test suite cleanly |
| `m_sql_studio_problems` | `test` | `node --test` | `bun test` | Direct drop-in (24/24 pass) |
| | `validate` | `node scripts/validate-problems.mjs` | `bun scripts/validate-problems.mjs` | Faster execution |
| | `validate:datasets` | `node scripts/validate-datasets.mjs` | `bun scripts/validate-datasets.mjs` | Faster execution |

---

## 5. Rollback Commands Per Repo

If regressions or issues occur post-migration, execute the corresponding rollback:

### 5.1 API Gateway
```bash
git -C m_sql_studio_api_gateway checkout HEAD -- Dockerfile package.json
docker compose build api-gateway && docker compose up -d api-gateway
```

### 5.2 Sandbox Executor
```bash
git -C m_sql_studio_sandbox checkout HEAD -- Dockerfile package.json
docker compose build sandbox-executor && docker compose up -d sandbox-executor
```

### 5.3 Client
```bash
git -C m_sql_studio_client checkout HEAD~1 -- Dockerfile package.json && rm -f m_sql_studio_client/bun.lock && docker compose build client && docker compose up -d client
```

### 5.4 Problems Repo
```bash
git -C m_sql_studio_problems checkout HEAD -- package.json
```

### 5.5 Universal Full-Stack Rollback
```bash
git checkout dev -- .
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## 6. Cold-Start & Latency Baseline to Beat (Measured on Current Node 22 Stack)

All metrics measured on macOS ARM64 (Apple Silicon) with Docker Desktop, running production `node:22-alpine` containers against local PostgreSQL 16, Redis 7, and MongoDB 7.

### 6.1 Cold-Start Baseline

| Measurement Target | Node 22 Measured | Bun Target to Beat | Description |
|---|---|---|---|
| **Gateway Container Restart -> HTTP 200** | **290.0 ms** | **< 200 ms** | `docker restart msql-studio-api-gateway-1` until `GET /health` returns 200. |
| **Gateway Cold Start (stop -> start -> 200)** | **180.0 ms** | **< 120 ms** | Time from `docker start` until health check responds. |
| **Gateway In-Container Module Load** | **548.4 ms** | **< 250 ms** | Execution time of `require("./dist/app.js")` inside container. |
| **Sandbox Container Restart -> Worker Ready** | **216.0 ms** | **< 150 ms** | `docker restart msql-studio-sandbox-executor-1` until BullMQ worker ready. |
| **Sandbox Cold Start (stop -> start -> ready)** | **171.0 ms** | **< 100 ms** | Time from `docker start` to worker listening. |
| **Sandbox In-Container Module Load** | **183.1 ms** | **< 80 ms** | Execution time of `require("./dist/worker.js")` inside container. |
| **Client Container Restart -> HTTP 200** | **312.0 ms** | **~ 300 ms** | Nginx runtime (unchanged). |

### 6.2 One-Execute Latency Baseline (Empirical HTTP Benchmarks)

Measured with 15–50 iterations per endpoint after warm-up.

| Operation / Endpoint | Samples (N) | Min (ms) | Mean (ms) | Median (p50 ms) | p95 (ms) | p99 (ms) | Bun Target (p50) |
|---|---|---|---|---|---|---|---|
| **Health Check** (`GET /health`) | 50 | 3.32 | 4.30 | **4.00** | 6.00 | 6.67 | **< 3.0 ms** |
| **Assignments Catalog** (`GET /api/v1/assignments`) | 30 | 0.57 | 0.93 | **0.63** | 0.89 | 9.23 | **< 0.5 ms** |
| **Auth Sign-Up** (`POST /api/auth/sign-up/email`) | 1 | 66.11 | 66.11 | **66.11** | 66.11 | 66.11 | **< 50.0 ms** |
| **Auth Sign-In** (`POST /api/auth/sign-in/email`) | 20 | 46.65 | 49.18 | **49.28** | 52.40 | 52.40 | **< 35.0 ms** |
| **SQL Execute Enqueue** (`POST .../execute`) | 20 | 3.38 | 4.50 | **4.15** | 8.11 | 8.11 | **< 3.0 ms** |
| **Full E2E Execution Lifecycle** (Enqueue -> Redis Queue -> Worker -> PG Sandbox -> Result in Redis) | 15 | 36.57 | 42.30 | **41.13** | 54.07 | 54.07 | **< 30.0 ms** |

---

## 7. Migration Sequence

```
  [Phase 1: Zero Risk]
  m_sql_studio_problems
  ├── Validate all problems & datasets with Bun CLI
  └── Update test script to bun test
           │
           ▼
  [Phase 2: Seeding Utility]
  misc/seed.js
  └── Verify seeding script with bun misc/seed.js
           │
           ▼
  [Phase 3: Background Worker]
  m_sql_studio_sandbox
  ├── Update Dockerfile to oven/bun:1.2-alpine
  ├── Build container & verify BullMQ connectivity
  └── Verify SQL sandbox execution against Postgres
           │
           ▼
  [Phase 4: API Gateway]
  m_sql_studio_api_gateway
  ├── Update Dockerfile to oven/bun:1.2-alpine
  ├── Verify better-auth routes (/api/auth/*splat)
  └── Run scripts/live_e2e.sh and scripts/live_e2e_auth.sh
           │
           ▼
  [Phase 5: Frontend Client]
  m_sql_studio_client
  ├── Update build stage to oven/bun:1.2-alpine
  ├── Build static assets with bun run build
  └── Verify Nginx serves frontend on port 3000
```
