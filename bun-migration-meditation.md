# Bun Migration Meditation

**Date:** 2026-09-10
**Researcher:** @researcher
**Scope:** Evaluate migrating MSqlStudio (client, API gateway, sandbox worker, problems validator) from Node.js 22 to Bun.

---

## 1. Current Architecture (from codebase inspection)

| Package | Runtime | Key Dependencies | Module System |
|---|---|---|---|
| `m_sql_studio_client` | Vite dev server | React 19, RTK Query, Zod, Tailwind 4 | ESM |
| `m_sql_studio_api_gateway` | Node 22 (nodemon/tsc) | Express 5, Mongoose 9, BullMQ 5, better-auth 1.6, Redis 5, pino, helmet, cors, express-rate-limit, rate-limit-redis, SSE | CJS |
| `m_sql_studio_sandbox` | Node 22 (nodemon/tsc) | BullMQ 5, pg (node-postgres), Redis 5, pino, Zod | CJS |
| `m_sql_studio_problems` | Node test runner | ajv, ajv-formats, yaml | ESM |

Docker images: `node:22-alpine` throughout (multi-stage: build + nginx for client, build + run for gateway/sandbox).

---

## 2. Dependency-by-Dependency Bun Compatibility Assessment

### 2.1 GREEN (Works or near-zero risk)

| Dependency | Bun Status | Evidence |
|---|---|---|
| **Express 5** | Works | node:http passes 97% of Node's own tests (Bun 1.4.1). Express 5 middleware ecosystem works without changes. |
| **helmet** | Works | Standard Express middleware, no Node.js internals beyond req/res. |
| **cors** | Works | Same. |
| **compression** | Works | Pure JS, uses node:stream which passes 97% of tests. |
| **express-rate-limit** | Works | Standard Express middleware. |
| **rate-limit-redis** | Works | Uses Redis client which Bun supports; adapter interface available. |
| **pino / pino-http** | Works | Multiple production blogs confirm Bun + pino-http works. |
| **Zod** | Works | Pure JS, no runtime dependencies. |
| **vitest** | Works (with caveat) | Vitest runs on Bun via its own Node.js compatibility layer. Existing suites should pass. Some advanced mocking features may differ. |
| **Vite 6** | Works | Vite runs on Bun; `bun --bun run dev` works out of the box. |
| **Biome 2.5** | Works | Pure Rust/JS CLI. |
| **React 19 / RTK Query** | Works | Frontend code; Vite handles bundling. |
| **SSE (raw res.write)** | Works | Bun supports text/event-stream and streaming responses. Native SSE guide exists. |
| **Node test runner** | Works | `node --test` equivalent via `bun test`. |

### 2.2 YELLOW (Works but with known edge cases)

| Dependency | Risk | Evidence |
|---|---|---|
| **Mongoose 9.x** | Connection stability on Bun with Atlas Serverless | Known issue: connections drop after ~20 min on Bun (GitHub oven-sh/bun#8609). The app uses `sharedMongoClient` (MongoClient directly), which reduces but doesn't eliminate Mongoose-dependent code paths. Mongoose officially lists Deno as "alpha" support; Bun relies on node compatibility. The `mongodb` Node.js driver underneath has native C++ components that could behave differently on Bun. |
| **BullMQ 5.x** | Officially Bun-compatible since 2026, but multi-instance deployments had issues as of Jan 2025 | BullMQ docs now list Bun support with pluggable Redis client adapters. A Jan 2025 issue (smela-back#59) warned against BullMQ + Bun for multi-instance setups. The 2026 pluggable adapter architecture should have resolved this, but the app uses `new Worker()` with ioredis-style connection options that need testing. The sandbox worker pattern (BullMQ Worker + Redis pub) is the main risk. |
| **node-redis v5** | Compatibility OK, but Bun has a native alternative | Bun ships its own Redis client (`import { redis } from "bun"`). The app uses `createClient` from the `redis` npm package. This works on Bun via compat layer, but migrating to Bun's native client would be cleaner long-term. |
| **pg (node-postgres)** | Connection pooling issues under load | Real-world report: "queries would intermittently hang under load" on Bun, switched to Drizzle ORM as fix. The sandbox worker uses `Pool` from `pg`. For the sandbox's pattern (short-lived, per-assignment schemas), this may not manifest as a problem, but sustained-load scenarios need load testing. |

### 2.3 RED (Significant risk — likely breakage)

| Dependency | Risk | Evidence |
|---|---|---|
| **better-auth** (server) | `toNodeHandler(auth)` is Node.js-specific; known Bun issues | Multiple GitHub issues: better-auth#6781 (fails to build with Bun runtime in Next.js 16, Dec 2025), better-auth#7987 (Docker fails due to better-sqlite3 native binding, Feb 2026), oven-sh/bun#23778 (bunx --bun @better-auth/cli generate crashes, Oct 2025), better-auth#6530 (Bun + Hono + Prisma getSession returns null, Dec 2025). The app uses `toNodeHandler(auth)` from `better-auth/node` which is explicitly a Node.js adapter. The `mongodbAdapter` from better-auth is pure JS but the overall Node.js handler path is fragile on Bun. This is the single biggest blocker. |

---

## 3. Runtime Feature Gaps (from source grep)

| Feature | Usage | Bun Status |
|---|---|---|
| `process.env` | Everywhere | Works |
| `process.exit()` | Error handlers, signal handlers | Works |
| `process.on("SIGTERM/SIGINT")` | Graceful shutdown | Works |
| `process.on("unhandledRejection")` | Safety net | Works |
| `Buffer` | `req.rawBody` capture for webhook verification | Works |
| `crypto.timingSafeEqual` | Internal API key middleware | Works |
| `node:fs/promises` (readFile) | Dataset SQL loading (test path) | Works (97% tests pass) |
| `node:http` server | `app.listen()` under the hood | Works |
| `__dirname` | Not used in source | N/A |
| `require()` | Not used (CJS but uses import/export) | N/A |

No blocking Node.js globals detected in the source code.

---

## 4. What a Migration Looks Like (Component by Component)

### 4.1 Client (Vite + React)
- **Effort:** Minimal
- **Changes:** Replace `node:22-alpine` Docker build with `oven/bun:1.4-alpine`. Replace `npm ci` with `bun install`. Replace `npm run build` with `bun run build`. Vite already works with Bun.
- **Risk:** Low. Vite + Bun is a common, well-tested combination.
- **Recommendation:** Do this first as a low-risk win.

### 4.2 API Gateway (Express + Mongoose + better-auth + BullMQ + Redis)
- **Effort:** Medium-High
- **Changes:** Replace Docker base image. Replace `tsc` build with `bun build` or run TypeScript directly with `bun`. Replace `nodemon` with `bun --watch`. Replace `node dist/index.js` with `bun dist/index.js` or run TS directly.
- **Risk:** Medium-high. The `better-auth/node` `toNodeHandler` is the primary blocker. This likely needs either:
  - (a) better-auth releasing a Bun-native handler (no public timeline),
  - (b) Replacing better-auth with a Bun-compatible auth library (e.g., a more portable session/JWT approach),
  - (c) Running the API gateway on Node.js 22 while moving only the client and worker to Bun.
- **Secondary risk:** Mongoose connection stability needs load testing on Bun.
- **Recommendation:** Don't migrate the gateway until better-auth's Bun story is confirmed. Keep it on Node 22 for now.

### 4.3 Sandbox Worker (BullMQ + pg + Redis)
- **Effort:** Medium
- **Changes:** Replace Docker base image. Replace `nodemon` with `bun --watch`. Replace `node dist/worker.js` with `bun dist/worker.js`.
- **Risk:** Medium. BullMQ officially supports Bun (pluggable Redis adapter). The `redis` npm package's `createClient` works on Bun. `pg` works but needs load testing for connection pool stability. The pattern (long-running Worker + Redis pub) is compatible.
- **Recommendation:** Proceed with migration but run a soak test (sustained load for >24h) before promoting to production. Have Node.js 22 as a fallback image tag.

### 4.4 Problems Validator (Node test runner)
- **Effort:** Minimal
- **Changes:** Replace `node --test` with `bun test` or keep `node --test` (it works on Node). No Docker image.
- **Risk:** None.
- **Recommendation:** Low priority. Either runtime works.

---

## 5. Phased Migration Recommendation

### Phase 1: Bun as Package Manager + Dev Runtime (Low Risk, Immediate Win)
- Use `bun install` instead of `npm ci` across all packages.
- Use `bun --bun run dev` for Vite dev server (faster cold starts, faster HMR).
- Use `bun run build` for client (Vite build, faster).
- **Risk:** Near zero. Bun's npm compat is mature.
- **Value:** 3-8x faster installs, faster dev server startup.

### Phase 2: Client Production Docker on Bun (Low Risk)
- Switch client Dockerfile to `oven/bun:1.4-alpine` build stage + `nginx:alpine` serve.
- **Risk:** Low.
- **Value:** Smaller image, faster CI builds.

### Phase 3: Sandbox Worker on Bun (Medium Risk, Needs Soak Test)
- Switch sandbox Dockerfile to Bun base.
- Run BullMQ Worker + pg + Redis on Bun.
- Soak test for 24-48h under production-like load before cutting over.
- **Risk:** Medium (connection stability edge cases).
- **Value:** Faster worker startup, lower memory footprint.

### Phase 4: API Gateway on Bun (Conditional — Blocked on better-auth)
- **Do not start until:**
  1. better-auth has a documented, working Bun handler (check GitHub issues for resolution).
  2. Mongoose connection stability is verified on Bun with the app's actual MongoDB deployment.
- **Fallback:** Keep gateway on Node.js 22 indefinitely while other components run on Bun. They communicate via HTTP + Redis, so mixed-runtime is fine.

### Phase 5: API Gateway Test Suite (Parallel)
- Evaluate switching from `vitest` to `bun:test`. Bun's test runner is faster but has weaker module mocking. For the gateway's current test suite (integration-style, Supertest), `bun:test` should work but needs a trial run.
- **Risk:** Low-medium. Vitest works on Bun, so this is optional optimization.

---

## 6. Docker Image Impact

| Component | Current Image | Proposed Image | Estimated Size Change |
|---|---|---|---|
| Client build | `node:22-alpine` (~190MB) | `oven/bun:1.4-alpine` (~120MB) | -37% |
| Gateway run | `node:22-alpine` (~190MB) | `oven/bun:1.4-alpine` (~120MB) | -37% (if migrated) |
| Sandbox run | `node:22-alpine` (~190MB) | `oven/bun:1.4-alpine` (~120MB) | -37% |

Bun's compiled binary is smaller than Node.js. Additionally, Bun's `--compile` flag (Bun 1.4 supports `--bytecode`) can produce a self-contained executable, potentially allowing `scratch`-based distroless images.

---

## 7. Known Unknowns (Things Only Real Testing Can Answer)

1. **Does `toNodeHandler(auth)` actually fail on Bun?** The GitHub issues suggest it does, but no one has tested the exact version (better-auth 1.6.11) with Bun 1.4.x.
2. **Does Mongoose 9 connection pooling survive long-term on Bun?** The 20-minute drop issue was reported with Mongoose 8 + Atlas Serverless. The app uses Mongoose 9 + a dedicated MongoDB (not necessarily Atlas Serverless), so behavior may differ.
3. **Does BullMQ Worker concurrency on Bun behave correctly?** The app uses `CONCURRENT_WORKERS_COUNT = 3` with `maxRetriesPerRequest: null`. This should work but needs verification.
4. **Does `express.json({ verify: ... })` rawBody capture work on Bun?** Bun's Express compat handles `req`/`res` objects, but the `verify` callback with `Buffer` may have edge cases.
5. **Does SSE with `res.flushHeaders?.()` and `heartbeat.unref?.()` work on Bun?** Bun supports both methods, but the optional chaining suggests defensive coding; Bun should implement them.

---

## 8. Bottom Line

| Question | Answer |
|---|---|
| Should we use Bun as package manager? | **Yes, immediately.** Low risk, high reward. |
| Should we run the client on Bun? | **Yes.** Vite + Bun is well-proven. |
| Should we run the sandbox worker on Bun? | **Yes, after a soak test.** |
| Should we run the API gateway on Bun? | **Not yet.** Blocked on better-auth. Keep on Node 22. |
| Should we switch from Vitest to bun:test? | **Optional.** Vitest works on Bun. bun:test is faster but has weaker mocking. |
| Is full migration (all-Bun) possible today? | **No.** better-auth is a hard blocker. |
| Estimated effort for Phase 1-3 | **2-3 days** (Dockerfile updates, bunfig.toml configs, soak test). |
| Expected performance gain | **3-5x faster cold starts, 3-8x faster installs, ~30% lower memory.** |

**The honest summary:** Bun is ready for the parts of this app that don't touch better-auth. The client and worker can move now. The gateway must wait. A mixed-runtime deployment (Bun client + Bun worker + Node gateway) is architecturally clean since they're separated by HTTP and Redis.

---

## 9. Sources

- Bun Node.js Compatibility: https://bun.com/docs/runtime/nodejs-compat
- Bun 1.4.1 release: https://bun.com/blog/bun-v1.4.1
- Bun vs Node.js 2026: https://strapi.io/blog/bun-vs-nodejs-performance-comparison-guide
- Bun compatibility 2026: https://dev.to/alexcloudstar/bun-compatibility-in-2026-what-actually-works-what-does-not-and-when-to-switch-23eb
- Bun + Express guide: https://mintlify.wiki/oven-sh/bun/guides/express
- Bun + better-auth issues: https://github.com/better-auth/better-auth/issues/6781, #7987, #2155, #23778, #6530
- BullMQ Bun support: https://bullmq.io/articles/guides/pluggable-redis-clients/
- BullMQ production warning (Jan 2025): https://github.com/SlavaMelanko/smela-back/issues/59
- Bun + Mongoose Atlas Serverless issue: https://gitmemories.com/oven-sh/bun/issues/8609
- Bun + pg (node-postgres): https://github.com/brianc/node-postgres/issues/3391
- Bun real-world migration report: https://dev.to/alanwest/we-moved-our-api-from-node-to-bun-heres-what-broke-and-what-got-3x-faster-3hg6
- Bun Redis: https://bun.com/docs/runtime/redis
- Bun SSE: https://bun.com/docs/guides/http/sse
- Bun 1.4 vs Node.js 26: https://dev.to/jamilxt/bun-141-vs-nodejs-26-should-you-actually-move-your-server-2ce8
- Bun test vs vitest: https://www.pkgpulse.com/guides/bun-test-vs-vitest-vs-jest-test-runner-benchmark-2026
