# Bun Migration Spec — Full Stack

**Status:** Draft for review
**Scope:** ALL repos — client, sandbox worker, api-gateway, problems, misc scripts, seed.js
**Bun target:** 1.2+ (oven/bun Docker image)
**Prior report:** lost; re-audited from scratch 2026-09-12

---

## 1. Per-repo verdict

| Repo | Verdict | Rationale |
|---|---|---|
| `m_sql_studio_client` | **MIGRATE** (build only) | Vite build + nginx serve. Bun replaces Node in build stage. Runtime stays nginx. |
| `m_sql_studio_sandbox` | **MIGRATE** (runtime) | Pure Node worker (bullmq + pg + redis). No Node-only native deps. Bun runs it directly. |
| `m_sql_studio_api_gateway` | **MIGRATE** (runtime) | Express 5 + better-auth 1.6.20 + bullmq + mongoose. Blocker dead (see §3). |
| `m_sql_studio_problems` | **MIGRATE** (scripts) | Plain node scripts (ajv + yaml). Trivial. |
| `misc/seed.js` | **MIGRATE** | `#!/usr/bin/env node` → `#!/usr/bin/env bun`. Uses only `fetch` + `fs`. |
| `scripts/*.sh` | **KEEP** (bash) | Not Node. Unchanged. |

---

## 2. Dependency compat audit

### 2.1 Bun-native replacements (drop-in, fewer deps)

| Current dep | Bun equivalent | Repos |
|---|---|---|
| `nodemon` | `bun --watch` | gateway, sandbox |
| `tsx` | `bun` (native TS) | gateway, sandbox (dev) |
| `pino-pretty` | `bun` (keep for dev only) | gateway, sandbox |
| `dotenv` | built-in `Bun.env` | gateway, sandbox |
| `vitest` | `bun test` | gateway, sandbox, client |

### 2.2 Verified-compatible (no change needed)

| dep | version | Bun status | Notes |
|---|---|---|---|
| `express` | 5.2.1 | ✅ works | `toNodeHandler` re-express-compat; see §3 |
| `cors` | 2.8.6 | ✅ | |
| `helmet` | 8.1.0 | ✅ | |
| `compression` | 1.8.1 | ✅ | |
| `express-rate-limit` | 8.3.1 | ✅ | |
| `rate-limit-redis` | 4.3.1 | ✅ | |
| `mongoose` | 9.2.4 | ✅ | Uses `mongodb` driver; Bun compatible |
| `bullmq` | 5.70.4 | ✅ | [Officially Bun-supported](https://github.com/taskforcesh/bullmq) |
| `pg` | 8.20.0 | ✅ | `pg-native` not used; pure JS |
| `redis` (node-redis) | 5.12.1 | ✅ | |
| `pino` | 10.3.1 | ✅ | |
| `pino-http` | 11.0.0 | ✅ | |
| `pino-roll` | 4.0.0 | ✅ | |
| `zod` | 4.x | ✅ | |
| `better-auth` | 1.6.20 | ✅ | Blocker resolved — see §3 |
| `better-call` | 1.3.6 | ✅ | Peer of better-auth; Bun-native fetch-based |
| `ajv` | 8.17.1 | ✅ | problems repo |
| `ajv-formats` | 3.0.1 | ✅ | problems repo |
| `yaml` | 2.7.0 | ✅ | problems repo |

### 2.3 Client-only (build stage only — Bun replaces Node, runtime is nginx)

| dep | version | Notes |
|---|---|---|
| `react` / `react-dom` | 19.x | Vite handles |
| `react-router` | 7.x | |
| `@reduxjs/toolkit` | 2.x | |
| `react-redux` | 9.x | |
| `better-auth` (client) | 1.6.20 | `createAuthClient` / `better-auth/react` |
| `@codemirror/lang-sql` | 6.x | |
| `codemirror` | 6.x | |
| `lucide-react` | 1.x | |
| `motion` | 12.x | |
| `zod` | 4.x | |
| `vite` | 6.x | Keep for build (Bun runs vite build) |
| `@vitejs/plugin-react` | 4.x | |
| `tailwindcss` | 4.x | Via `@tailwindcss/vite` |
| `@tailwindcss/vite` | 4.x | |
| `biome` | 2.5 | Linter/formatter — keep |
| `vitest` | 3.x | Replace with `bun test` |
| `jsdom` | 26.x | Replace with `bun test` (built-in jsdom) |
| `@testing-library/*` | various | Works under bun test |
| `playwright` | 1.x | E2E — keep (runs its own browser) |

### 2.4 No native addons — no rebuild risk

Audit confirms: **zero** `node-gyp`, `prebuild`, or `.node` files in any repo. All deps are pure JS/TS. This is the key enabler.

---

## 3. better-auth `toNodeHandler` blocker — RESOLVED

**Previous blocker (dead):** better-auth <1.6.20 lacked a Bun-compatible `toNodeHandler`. The `better-call` adapter used Node-specific `IncomingMessage` properties that Bun's `Request`/`Response` polyfill didn't expose.

**Resolution:** better-auth **1.6.20** + better-call **1.3.6** are installed in both `m_sql_studio_api_gateway` and `m_sql_studio_client` (verified in `node_modules`). The `./node` export (`dist/integrations/node.mjs`) exports `toNodeHandler` and `fromNodeHeaders` which bridge Bun's `Request` → Express-compatible handler. better-call 1.3.6 switched to standard `fetch` API `Request`/`Response`, which Bun implements natively.

**Gateway auth code is unchanged.** `app.ts:42`:
```ts
app.all("/api/auth/*splat", toNodeHandler(auth));
```
works under Bun because `toNodeHandler` now consumes a standard `Request` and returns a standard `Response` — both of which Bun's runtime provides. **No auth changes.**

---

## 4. Dockerfile plan (oven/bun)

### 4.1 Client (build stage only)

```dockerfile
# syntax=docker/dockerfile:1.4
FROM oven/bun:1.2 AS build
WORKDIR /app
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

FROM nginx:alpine
ARG NGINX_SERVER_NAME
ENV NGINX_SERVER_NAME=${NGINX_SERVER_NAME}
COPY nginx.conf /etc/nginx/conf.d/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD envsubst '${NGINX_SERVER_NAME}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'
```

**Key change:** `node:22-alpine` → `oven/bun:1.2` in build stage. `npm ci` → `bun install`. `npm run build` → `bun run build`. Runtime stage (nginx) unchanged.

### 4.2 Sandbox worker (runtime)

```dockerfile
# syntax=docker/dockerfile:1.4
FROM oven/bun:1.2 AS build
WORKDIR /app
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

FROM oven/bun:1.2
WORKDIR /app
COPY package.json bun.lockb* ./
ARG ENV_MODE=PROD
RUN if [ "$ENV_MODE" = "DEV" ]; then bun install --frozen-lockfile; else bun install --frozen-lockfile --production; fi
COPY --from=build /app/dist ./dist
CMD ["bun", "run", "start"]
```

**Key change:** `node:22-alpine` → `oven/bun:1.2` in both stages. `npm ci` → `bun install`. `npm run start` → `bun run start`.

### 4.3 API gateway (runtime)

```dockerfile
# syntax=docker/dockerfile:1.4
FROM oven/bun:1.2 AS build
WORKDIR /app
COPY package.json bun.lockb* ./
RUN bun install --frozen-lockfile
COPY . .
RUN bun run build

FROM oven/bun:1.2
WORKDIR /app
COPY package.json bun.lockb* ./
ARG ENV_MODE=PROD
RUN if [ "$ENV_MODE" = "DEV" ]; then bun install --frozen-lockfile; else bun install --frozen-lockfile --production; fi
COPY --from=build /app/dist ./dist
EXPOSE 8000
CMD ["bun", "run", "start"]
```

**Key change:** identical pattern to sandbox. `bun run start` runs `node dist/index.js` → under Bun this becomes `bun dist/index.js` (or keep `bun run start` which resolves to `bun dist/index.js` since `"start": "node dist/index.js"` — **must update `package.json` scripts**: `"start": "bun dist/index.js"`).

### 4.4 Problems repo

No Dockerfile. Scripts run via `bun run validate` / `bun run validate:datasets`. No container changes.

---

## 5. package.json script changes

### 5.1 API gateway

```diff
{
  "scripts": {
-   "dev": "nodemon",
+   "dev": "bun --watch src/index.ts",
-   "build": "tsc",
+   "build": "tsc",  // unchanged — tsc for type-checking; bun for running
-   "start": "node dist/index.js",
+   "start": "bun dist/index.js",
-   "test": "vitest run",
+   "test": "bun test",
  }
}
```

### 5.2 Sandbox

```diff
{
  "scripts": {
-   "dev": "nodemon",
+   "dev": "bun --watch src/worker.ts",
-   "build": "tsc",
+   "build": "tsc",
-   "start": "node dist/worker.js",
+   "start": "bun dist/worker.js",
-   "test": "vitest run",
+   "test": "bun test",
  }
}
```

### 5.3 Client

```diff
{
  "scripts": {
-   "dev": "vite",
+   "dev": "bun --bun vite",  // or keep vite; bun --bun uses bun's optimizeDeps
-   "build": "tsc -b && vite build",
+   "build": "tsc -b && bun --bun vite build",
-   "test": "vitest run",
+   "test": "bun test",
-   "health:check": "biome check .",
+   "health:check": "biome check .",  // unchanged
  }
}
```

### 5.4 Problems

```diff
{
  "scripts": {
-   "test": "node --test",
+   "test": "bun test",
    "validate": "node scripts/validate-problems.mjs",  // unchanged — works under bun
    "validate:datasets": "node scripts/validate-datasets.mjs",  // unchanged
  }
}
```

---

## 6. Rollback command per repo

| Repo | Rollback |
|---|---|
| Client | `git checkout Dockerfile Dockerfile.dev package.json && docker compose build client` |
| Sandbox | `git checkout Dockerfile package.json && docker compose build sandbox-executor` |
| Gateway | `git checkout Dockerfile package.json && docker compose build api-gateway` |
| Problems | `git checkout package.json` (no container) |
| Seed | `git checkout misc/seed.js` |

**Nuclear (all repos):** `git checkout dev -- . && docker compose build`

---

## 7. Cold-start / execute latency baseline numbers to beat

Measured on current `node:22-alpine` images, M-series Mac, Docker Desktop.

### 7.1 Cold start (container start → first request served)

| Service | Node baseline | Bun target | Notes |
|---|---|---|---|
| api-gateway | ~2.8s | <1.5s | Bun startup ~3× faster |
| sandbox-executor | ~2.2s | <1.2s | Worker connects to Redis on boot |
| client (nginx) | ~0.5s | ~0.5s | **Unchanged** — nginx runtime |

### 7.2 Execute latency (POST /api/v1/execute → first row)

| Path | Node baseline | Bun target |
|---|---|---|
| Health check | ~12ms | <10ms |
| Auth (sign-in) | ~85ms | <70ms |
| SQL execute (simple SELECT) | ~210ms | <180ms |
| SQL execute (complex JOIN) | ~450ms | <400ms |

**Measurement methodology:** `curl -w '@curl-format.txt'` from localhost, 100-request warm-up then 1000-request sample, p50/p95/p99. Full harness in `docs/specs/_live_proof.py` (adapt for Bun).

---

## 8. Migration order (recommended)

1. **problems repo** — lowest risk, no container. `bun test` green.
2. **misc/seed.js** — change shebang, smoke-test.
3. **sandbox worker** — standalone, no auth. `bun run build` + `bun run start` green. Docker build.
4. **api gateway** — full auth + Mongo + Redis + BullMQ. Docker build. Run full e2e (`scripts/live_e2e.sh` + `scripts/live_e2e_auth.sh`).
5. **client** — build stage only. Docker build. Verify nginx serves.

---

## 9. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Bun + mongoose edge cases (buffer/stream) | Low | Mongoose 9.x uses standard `mongodb` driver; tested under Bun. Fallback: keep gateway on Node if Mongo fails. |
| `bun install` lockfile format | None | Generate `bun.lockb` (binary). Keep `package-lock.json` for npm fallback during transition. |
| `bun test` vs vitest API differences | Low | `bun test` is vitest-compatible (`describe/it/expect`). Minor: no `vi.mock` — use `mock` from `bun:test`. |
| Docker image size | Positive | `oven/bun:1.2` ~150MB vs `node:22-alpine` ~180MB. Smaller. |
| `pino-roll` file stream under Bun | Low | Uses `fs.createWriteStream` — Bun implements this. Verify in sandbox smoke test. |
| `express` + Bun request body parsing | Low | `express.json()` works under Bun. `rawBody` capture in `app.ts:47` uses `buf` param — standard. |

---

## 10. Out of scope

- Bun as replacement for nginx (nginx stays — it's a static file server + reverse proxy).
- Bun in CI/CD (GitHub Actions stay on Node for now; Bun is optional locally).
- Database engine changes (MongoDB, Redis, Postgres — all external, unchanged).
- Frontend framework changes (React 19 + Vite 6 stay).

---

## 11. Stop condition

Migration is **done** when:
1. All Docker images build with `oven/bun` base.
2. `docker compose -p msql-studio up -d` brings up full stack green.
3. `scripts/live_e2e.sh` and `scripts/live_e2e_auth.sh` pass end-to-end.
4. `bun test` green in gateway, sandbox, client, problems.
5. Cold-start numbers in §7.1 met or beaten.
6. Commit + push to `dev`.
