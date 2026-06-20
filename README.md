# MSqlStudio

An online SQL learning platform where users solve SQL assignments against real PostgreSQL databases. Submissions execute in isolated sandboxes, and results are compared against reference solutions for automated grading.

### **_I M P O R T A N T_** note for developers:

To test/run the entire backend locally, all you need do is:

1. Clone all the project repos:
   - https://github.com/maverickreal/m_sql
   - https://github.com/maverickreal/m_sql_studio_sandbox
   - https://github.com/maverickreal/m_sql_studio_api_gateway
2. Run the following shell code, from within the orchestrator repo (m_sql_studio):
   ```sh
   chmod u+x ./init.dev.bash;
   ./init.dev.bash;
   ```

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

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Node.js 22+](https://nodejs.org/) (for dependency installation and seeding)

## Getting Started

### 1. Clone All Repositories

All three repositories must be sibling directories:

```
project/
├── m_sql_studio/               # This repo
├── m_sql_studio_api_gateway/
└── m_sql_studio_sandbox/
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Fill in every value in `.env`. See the [Environment Variables](#environment-variables) section.

### 3. Automated Dev Setup

```bash
bash init.dev.bash
```

This script will:

1. Run `npm ci` in both the API Gateway and Sandbox repos
2. Stop and remove all existing Docker containers, volumes, and networks
3. Build and start all services via `docker compose up -d --build`
4. Seed sample assignments into the database when `ENV_MODE=DEV`
5. Start `docker compose watch` for live rebuilds on source changes

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
├── .env.example                # Environment variable template
├── init.dev.bash               # Automated dev environment setup
└── misc/
    ├── seed.js                 # Seeds sample SQL assignments via the API
    └── init-db/
        ├── mongodb/
        │   └── 01-setup.js     # Creates MongoDB role and user for API Gateway
        └── postgresql/
            └── 01-setup.sh     # Creates restricted sandbox PostgreSQL role
```

## Database Initialization

On first startup, Docker entrypoint scripts automatically configure the databases:

- **PostgreSQL** (`misc/init-db/postgresql/01-setup.sh`): Creates a restricted `SANDBOX_PG_USER` role with `LOGIN`, `CONNECT`, and `TEMPORARY` privileges only. All other privileges on the `public` schema and database are revoked.
- **MongoDB** (`misc/init-db/mongodb/01-setup.js`): Creates a custom role with `find`, `insert`, `update`, `remove`, and `createCollection` actions, then creates the API Gateway user with that role.

## Sample Data

When `ENV_MODE=DEV`, the init script automatically runs `misc/seed.js` to populate the platform with sample assignments across easy, medium, and hard difficulties, covering both read and write SQL modes.

## Running Tests

```bash
E2E_TEST=true MONGO_HOST=<host> REDIS_HOST=<host> npm run test -- assignment_execution.e2e.test.ts
```

See the test file in the API Gateway repository for configurable values.

NOTE: For unit and integration tests, just run `npm run test` in eiter the API gateway or sandbox repo.

## TODOs:
* Add comments.
* Add authentication and authorisation.
* Enable load balancing, Nginx,di container, db replication/sharding, distributed worker, etc.
* Integrate AI (API or local) for certain features.
* Meditate on how to eliminate/minimise redundancy of relations due to schemas.
* Periodically scheduled cleanups.
* User SQL execution state persistence.
