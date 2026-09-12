# MSqlStudio

An online SQL learning platform where users solve SQL assignments against real PostgreSQL databases. Submissions execute in isolated sandboxes, and results are compared against reference solutions for automated grading.

### **_I M P O R T A N T_** note for developers:

There is no `maverickreal/m_sql`. The orchestrator is this repo (`m_sql_studio`). Checkout **`dev`** on all four.

1. Clone sibling repos:
   - https://github.com/maverickreal/m_sql_studio
   - https://github.com/maverickreal/m_sql_studio_api_gateway
   - https://github.com/maverickreal/m_sql_studio_sandbox
   - https://github.com/maverickreal/m_sql_studio_client
2. `cp .env.example .env` in `m_sql_studio` and fill it in (never commit `.env`).
3. From `m_sql_studio` (does **not** stop unrelated Docker on the machine):
   ```sh
   export COMPOSE_PROJECT_NAME=msql-studio
   export COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml
   ./scripts/setup.sh
   ```
   The `setup.sh` script handles build, boot, health checks, and catalog gate (>= 200 unique problems).
4. Client UI: http://127.0.0.1:3000 — API (via nginx-edge, 2 gateway replicas): http://127.0.0.1:8000 — health: `curl -s http://127.0.0.1:8000/health`
5. Grade a sample assignment (cookie from sign-in or sign-up). Leaderboard solution: `SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 3;`
   ```sh
   curl -sS -c /tmp/msql.cj -b /tmp/msql.cj \
     -H 'Content-Type: application/json' -H 'Origin: http://127.0.0.1:3000' \
     -d '{"email":"<you@example.com>","password":"<password>","name":"Dev"}' \
     http://127.0.0.1:8000/api/auth/sign-up/email
   curl -sS http://127.0.0.1:8000/api/v1/assignments
   curl -sS -c /tmp/msql.cj -b /tmp/msql.cj \
     -H 'Content-Type: application/json' -H 'Origin: http://127.0.0.1:3000' \
     -d '{"assignmentId":"<id>","userSql":"SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 3;","mode":"read"}' \
     http://127.0.0.1:8000/api/v1/assignments/client-sql-code-run/execute
   curl -sS -c /tmp/msql.cj -b /tmp/msql.cj \
     http://127.0.0.1:8000/api/v1/assignments/client-sql-code-run/status/<taskId>
   ```
   A matching query returns `"passed": true`; a wrong ORDER BY returns `"passed": false`. The client assignment page shows Passed / Failed after Run Query.

## Architecture

```
Client (Browser)
      │
      ▼
 API Gateway  ──BullMQ──▶  Sandbox Executor
      │                          │
      ▼                          ▼
   MongoDB                  PostgreSQL
      ▲                          ▲
      └──────── Redis ───────────┘
```

| Service              | Image / Build Context              | Port  | Purpose                                                      |
| -------------------- | ---------------------------------- | ----- | ------------------------------------------------------------ |
| **redis**            | `redis:7-alpine`                   | 6379  | Caching, rate limiting, BullMQ job queue                     |
| **mongo**            | `mongo:8`                          | 27017 | Assignment metadata storage                                  |
| **postgres**         | `postgres:16-alpine`               | 5432  | SQL execution sandbox (isolated schemas per assignment)      |
| **api-gateway**      | `../m_sql_studio_api_gateway` | 8000  | REST API for clients and admin operations                    |
| **sandbox-executor** | `../m_sql_studio_sandbox`     | --    | BullMQ worker that executes user SQL in sandboxed PostgreSQL |

### Related Repositories

| Repository                                                        | Description                                          |
| ----------------------------------------------------------------- | ---------------------------------------------------- |
| [m_sql_studio_api_gateway](../m_sql_studio_api_gateway) | Express.js 5 REST API (TypeScript, Node.js 22)       |
| [m_sql_studio_sandbox](../m_sql_studio_sandbox)         | BullMQ SQL execution worker (TypeScript, Node.js 22) |
| [m_sql_studio_client](../m_sql_studio_client)           | Web UI (Vite) on port 3000                           |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Node.js 22+](https://nodejs.org/) (for dependency installation and seeding)

## Getting Started

### 1. Clone All Repositories

All four repositories must be sibling directories:

```
project/
├── m_sql_studio/               # This repo (orchestrator)
├── m_sql_studio_api_gateway/
├── m_sql_studio_sandbox/
└── m_sql_studio_client/
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Fill in every value in `.env`. See the [Environment Variables](#environment-variables) section.

### 3. Automated Dev Setup

```bash
export COMPOSE_PROJECT_NAME=msql-studio
export COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml
./scripts/setup.sh
```

This script will:

1. Build and start all services via `docker compose up -d --build`
2. Wait for all services to be healthy (5 min timeout)
3. Verify health endpoints (`/health`, catalog, client)
4. Run bootstrap guard and admin initialization via `bun misc/seed.ts`
4. Trigger forced problems-sync (canonical assignments from `m_sql_studio_problems` repo)
5. Poll live unique-title count to >= 200 (catalog gate)

## Environment Variables

| Variable                     | Description                                              |
| ---------------------------- | -------------------------------------------------------- |
| `REDIS_PASSWORD`             | Redis server password                                    |
| `MONGO_USER`                 | MongoDB root username                                    |
| `MONGO_PASSWORD`             | MongoDB root password                                    |
| `API_GATEWAY_MONGO_USER`     | MongoDB user for the API Gateway                         |
| `API_GATEWAY_MONGO_PASSWORD` | MongoDB password for the API Gateway                     |
| `API_GATEWAY_MONGO_DB`       | MongoDB database name for the API Gateway                |
| `API_GATEWAY_MONGO_ROLE`     | MongoDB custom role for the API Gateway                  |
| `POSTGRES_USER`              | PostgreSQL superuser username                            |
| `POSTGRES_PASSWORD`          | PostgreSQL superuser password                            |
| `POSTGRES_DB`                | PostgreSQL database name                                 |
| `SANDBOX_PG_USER`            | Restricted PostgreSQL user for sandbox execution         |
| `SANDBOX_PG_PASSWORD`        | Password for the sandbox PostgreSQL user                 |
| `BULLMQ_SQL_QUEUE_NAME`      | BullMQ queue name shared between API Gateway and Sandbox |
| `ENV_MODE`                   | Environment mode (`DEV`, `STAGING`, `PROD`)              |
| `LOG_LEVEL`                  | Pino log level (`info`, `debug`, etc.)                   |
| `LOG_DIR`                    | Log output directory                                     |
| `CLIENT_URL`                 | Frontend client origin for CORS                          |
| `API_GATEWAY_URL`            | API Gateway base URL (used by seed script and sandbox)   |
| `INTERNAL_API_KEY`           | Shared secret for internal service-to-service auth       |

## Project Structure

```
m_sql_studio/
├── docker-compose.yml          # Orchestrates all 5 services
├── docker-compose.dev.yml      # DEV overlay (DB ports, mem limits, problems bind-mount)
├── .env.example                # Environment variable template
├── scripts/
│   └── setup.sh                # Idempotent fresh boot + catalog gate (canonical)
└── misc/
    ├── seed.ts                 # Bootstrap guard + admin init (bun-native, no hardcoded assignments)
    └── init-db/
        ├── mongodb/
        │   └── setup.sh        # Configures MongoDB replica set and users
        └── postgresql/
            └── setup.sh        # Creates restricted sandbox PostgreSQL role
```

## Database Initialization

On first startup, Docker entrypoint scripts automatically configure the databases:

- **PostgreSQL** (`misc/init-db/postgresql/setup.sh`): Creates a restricted `SANDBOX_PG_USER` role with `LOGIN`, `CONNECT`, and `TEMPORARY` privileges only. All other privileges on the `public` schema and database are revoked.
- **MongoDB** (`misc/init-db/mongodb/setup.sh`): Initiates the replica set, creates the root admin user, and creates the API Gateway user with configured roles.

## Canonical Problem Seed Source

The problems repository (`m_sql_studio_problems/problems/*.yaml` + `datasets/`) is the single canonical source of assignments, synchronized into the database via `problems-sync` (triggered by `scripts/setup.sh`). `misc/seed.ts` performs only admin user bootstrap and readiness checks, without maintaining any hardcoded assignment list.

## Running Tests

```bash
E2E_TEST=true MONGO_HOST=<host> REDIS_HOST=<host> npm run test -- assignment_execution.e2e.test.ts
```

See the test file in the API Gateway repository for configurable values.

NOTE: For unit and integration tests, just run `npm run test` in eiter the API gateway or sandbox repo.

## TODOs:
* Add comments.
* Auth is live (better-auth email/password + admin plugin, Google + GitHub OAuth). Remaining: polish, RBAC review.
* Shipped: nginx-edge load balancing (2 gateway replicas), periodic schema cleanup (BullMQ), last-SQL persistence + restore, SSE job-status stream with polling fallback.
* Integrate AI (API or local) for certain features.
* Meditate on how to eliminate/minimise redundancy of relations due to schemas.
* Remaining scale work: db replication/sharding, distributed worker, etc.

## GitHub problem bank webhook (PB1)

Content lives in the public `maverickreal/m_sql_studio_problems` repo and is materialized into Mongo (`problems`, `sync_state`) via `POST /api/webhooks/github` on the gateway: the route verifies `X-Hub-Signature-256` (HMAC-SHA256 of the raw body with `GITHUB_WEBHOOK_SECRET`, `dev-webhook-secret` in DEV) and ignores non-`push` events, then enqueues BullMQ job `client_sql_studio_problems_sync` with `X-GitHub-Delivery` Redis dedup (24h TTL). The route sits under `/api/` so nginx-edge proxies it with no extra location block; `POST /internal/problems-sync` (internal API key) enqueues the same job manually with optional `{forced:true}` full resync, and DEV fixtures can be read from `GITHUB_PROBLEMS_LOCAL_DIR`.

## User profiles (PF)

Authenticated users get a profile page at `/profile` (SPA routes `/profile` for own edit, `/profile/:id` for public read-only). Gateway exposes `GET /api/v1/profile/me`, `PATCH /api/v1/profile/me`, `GET /api/v1/profile/:id`. Profile data lives in Mongo `user_profiles` collection linked to `better-auth` users via `userId`; profile auto-created on signup.

## Leaderboard

`GET /api/v1/leaderboard` ranks users by total assignment passes (real sandbox `passed: boolean`, not synthetic scores). The leaderboard page lives at `/leaderboard` (SPA, 15s poll, "Load more" pagination, 15s public HTTP cache). Passes are recorded idempotently on the gateway side during job-status polling, so duplicate client polls never inflate counts.
