# MSqlStudio

An online SQL learning platform where users solve SQL assignments against real PostgreSQL databases. Submissions execute in isolated sandboxes, and results are compared against reference solutions for automated grading.

## Quick Start

```bash
# 1. Clone all four repos as siblings
git clone https://github.com/maverickreal/m_sql_studio.git
git clone https://github.com/maverickreal/m_sql_studio_api_gateway.git
git clone https://github.com/maverickreal/m_sql_studio_sandbox.git
git clone https://github.com/maverickreal/m_sql_studio_client.git

# 2. Configure environment
cd m_sql_studio
cp .env.example .env
# Edit .env with your values

# 3. Boot everything
export COMPOSE_PROJECT_NAME=msql-studio
export COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml
./scripts/setup.sh
```

**Access:**
- Client UI: http://127.0.0.1:3000
- API (via nginx-edge, 2 gateway replicas): http://127.0.0.1:8000
- Health check: `curl -s http://127.0.0.1:8000/health`

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

| Service | Image / Build Context | Port | Purpose |
|---------|----------------------|------|---------|
| **redis** | `redis:7-alpine` | 6379 | Caching, rate limiting, BullMQ job queue |
| **mongo** | `mongo:8` | 27017 | Assignment metadata storage |
| **postgres** | `postgres:16-alpine` | 5432 | SQL execution sandbox (isolated schemas per assignment) |
| **api-gateway** | `../m_sql_studio_api_gateway` | 8000 | REST API for clients and admin operations |
| **sandbox-executor** | `../m_sql_studio_sandbox` | — | BullMQ worker that executes user SQL in sandboxed PostgreSQL |

## Related Repositories

| Repository | Description |
|------------|-------------|
| [m_sql_studio_api_gateway](../m_sql_studio_api_gateway) | Express.js 5 REST API (TypeScript, Node.js 22) |
| [m_sql_studio_sandbox](../m_sql_studio_sandbox) | BullMQ SQL execution worker (TypeScript, Node.js 22) |
| [m_sql_studio_client](../m_sql_studio_client) | Web UI (Vite + React 19) on port 3000 |
| [m_sql_studio_problems](../m_sql_studio_problems) | Canonical problem bank (YAML + datasets) |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Node.js 22+](https://nodejs.org/) (for dependency installation and seeding)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `REDIS_PASSWORD` | Redis server password |
| `MONGO_USER` | MongoDB root username |
| `MONGO_PASSWORD` | MongoDB root password |
| `API_GATEWAY_MONGO_USER` | MongoDB user for the API Gateway |
| `API_GATEWAY_MONGO_PASSWORD` | MongoDB password for the API Gateway |
| `API_GATEWAY_MONGO_DB` | MongoDB database name for the API Gateway |
| `API_GATEWAY_MONGO_ROLE` | MongoDB custom role for the API Gateway |
| `POSTGRES_USER` | PostgreSQL superuser username |
| `POSTGRES_PASSWORD` | PostgreSQL superuser password |
| `POSTGRES_DB` | PostgreSQL database name |
| `SANDBOX_PG_USER` | Restricted PostgreSQL user for sandbox execution |
| `SANDBOX_PG_PASSWORD` | Password for the sandbox PostgreSQL user |
| `BULLMQ_SQL_QUEUE_NAME` | BullMQ queue name shared between API Gateway and Sandbox |
| `ENV_MODE` | Environment mode (`DEV`, `STAGING`, `PROD`) |
| `LOG_LEVEL` | Pino log level (`info`, `debug`, etc.) |
| `LOG_DIR` | Log output directory |
| `CLIENT_URL` | Frontend client origin for CORS |
| `API_GATEWAY_URL` | API Gateway base URL (used by seed script and sandbox) |
| `INTERNAL_API_KEY` | Shared secret for internal service-to-service auth |

## Project Structure

```
m_sql_studio/
├── docker-compose.yml          # Orchestrates all 5 services
├── docker-compose.dev.yml      # DEV overlay (DB ports, mem limits, problems bind-mount)
├── .env.example                # Environment variable template
├── scripts/
│   └── setup.sh                # Idempotent fresh boot + catalog gate (canonical)
└── misc/
    ├── seed.ts                 # Bootstrap guard + admin init (bun-native)
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

**Note:** For unit and integration tests, run `npm run test` in either the API gateway or sandbox repo.

## Key Features

- **Auth**: better-auth email/password + admin plugin, Google + GitHub OAuth
- **Load Balancing**: nginx-edge with 2 gateway replicas
- **Schema Cleanup**: Periodic BullMQ job cleans orphaned assignment schemas
- **Last-SQL Persistence**: User's last query restored on assignment revisit
- **SSE Job-Status Stream**: Real-time execution updates with polling fallback
- **Leaderboard**: Ranks users by total assignment passes (real sandbox results)

## GitHub Problem Bank Webhook (PB1)

Content lives in the public `maverickreal/m_sql_studio_problems` repo and is materialized into Mongo (`problems`, `sync_state`) via `POST /api/webhooks/github` on the gateway:
- Verifies `X-Hub-Signature-256` (HMAC-SHA256 of raw body with `GITHUB_WEBHOOK_SECRET`, `dev-webhook-secret` in DEV)
- Ignores non-`push` events
- Enqueues BullMQ job `client_sql_studio_problems_sync` with `X-GitHub-Delivery` Redis dedup (24h TTL)
- Route sits under `/api/` so nginx-edge proxies it with no extra location block
- `POST /internal/problems-sync` (internal API key) enqueues the same job manually with optional `{forced:true}` full resync
- DEV fixtures can be read from `GITHUB_PROBLEMS_LOCAL_DIR`

## User Profiles (PF)

Authenticated users get a profile page at `/profile` (SPA routes `/profile` for own edit, `/profile/:id` for public read-only).
- Gateway exposes `GET /api/v1/profile/me`, `PATCH /api/v1/profile/me`, `GET /api/v1/profile/:id`
- Profile data lives in Mongo `user_profiles` collection linked to `better-auth` users via `userId`
- Profile auto-created on signup

## Leaderboard

`GET /api/v1/leaderboard` ranks users by total assignment passes (real sandbox `passed: boolean`, not synthetic scores).
- Leaderboard page at `/leaderboard` (SPA, 15s poll, "Load more" pagination, 15s public HTTP cache)
- Passes recorded idempotently on gateway side during job-status polling

## Development Notes

- All four repos must be on the `dev` branch
- The orchestrator (`m_sql_studio`) is the only repo with Docker Compose; the other three are built from their own Dockerfiles
- `scripts/setup.sh` handles build, boot, health checks, and catalog gate (≥200 unique problems)

## License

MIT
