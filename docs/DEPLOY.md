# Deploy MSqlStudio (single VPS, Docker Compose)

Local proof: OrbStack + this compose. Production: same compose on a VM, Caddy (or nginx) for TLS in front of `:3000` (client) and optionally `:8000` (API). No Kubernetes.

## Layout

```
m_sql_studio/                 # compose + nginx-edge
  docker-compose.yml          # product stack (DB ports unpublished)
  docker-compose.dev.yml      # local only: DB host ports + problems bind-mount
  .env                        # secrets — never commit
../m_sql_studio_api_gateway
../m_sql_studio_client
../m_sql_studio_sandbox
../m_sql_studio_problems      # content repo (optional bind-mount in dev)
```

## First boot (OrbStack or a VPS)

```bash
cd m_sql_studio
cp .env.example .env          # then fill real secrets
# BETTER_AUTH_URL and CLIENT_URL must be the public origin in production
# (https://your.domain). Local: http://127.0.0.1:8000 and http://127.0.0.1:3000

export COMPOSE_FILE=docker-compose.yml
# local laptop only:
export COMPOSE_FILE=docker-compose.yml:docker-compose.dev.yml
export COMPOSE_PROJECT_NAME=msql-studio

# The One True Compose Project Name is `msql-studio`.
# Always use `-p msql-studio` with docker compose commands to avoid
# accidental creation of a duplicate `m_sql_studio` project.
docker compose -p msql-studio build api-gateway
docker compose -p msql-studio up -d
```

Wait until `api-gateway` and `api-gateway-b` are healthy, then:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/health
curl -sS -D- http://127.0.0.1:8000/api/v1/assignments | head
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/
```

Both gateway replicas must share one image SHA (`docker inspect msql-studio-api-gateway-1 msql-studio-api-gateway-b-1 --format '{{.Image}}'`).

## Project Name & Teardown Policy

- **One True Project Name**: `msql-studio` (container names `msql-studio-*`, network `msql-studio_default`).
- **Duplicate Stack Prevention**: Running compose inside `m_sql_studio/` without specifying `-p msql-studio` causes Docker Compose to default the project name to `m_sql_studio`, generating duplicate containers and volumes (`m_sql_studio_*`).
- **Tear Down Duplicate Stacks**:
  ```bash
  docker compose -p m_sql_studio down
  ```
  Remove stale duplicate containers/networks. Keep volumes unless proven redundant AND empty.

## Hints (AI Hint Stack)

- `docker-compose.yml` (line 35) defaults `HINT_ENABLED=false` so live failed queries return no hints by default.
- To enable live hints:
  1. Set `HINT_ENABLED=true` in `.env` (documented in `.env.example`).
  2. For local LFM2.5 model serving:
     Start server on host:
     ```bash
     mlx-serve LFM2.5-8B-A1B-MLX-6bit --detach
     ```
     Configure `.env`:
     ```env
     HINT_ENABLED=true
     HINT_API_URL=http://host.docker.internal:3208/v1
     HINT_MODEL=LFM2.5-8B-A1B-MLX-6bit
     HINT_ALLOW_REMOTE=false
     ```
  3. Restart **ONLY** the two api-gateway replicas without touching database or edge services:
     ```bash
     docker compose -p msql-studio up -d --no-deps api-gateway api-gateway-b
     ```
  4. Verify both replicas are running healthy with the identical Image SHA:
     ```bash
     docker inspect msql-studio-api-gateway-1 msql-studio-api-gateway-b-1 --format '{{.Name}}: {{.State.Health.Status}} {{.Image}}'
     ```
  5. Remote vendor APIs: `HINT_ALLOW_REMOTE=true` plus remote URL/key (`HINT_REMOTE_API_URL`, `HINT_REMOTE_API_KEY`). Extra PII off-box requires founder approval.

## TLS (production)

Put Caddy on the host (or a sibling container) with the public DNS name:

```
your.domain {
  reverse_proxy 127.0.0.1:3000
}
```

Set in `.env`:

- `CLIENT_URL=https://your.domain`
- `BETTER_AUTH_URL=https://your.domain` if auth is same-origin via the client `/api` proxy, **or** `https://api.your.domain` if you expose `:8000` separately
- `NGINX_SERVER_NAME=your.domain`
- Rebuild the **client** image after changing `CLIENT_URL` / auth URLs (Vite + better-auth trusted origins are not hot-reloaded)

OAuth: Google/GitHub callback URLs must match `BETTER_AUTH_URL`.

## Do not

- Publish Mongo/Redis/Postgres to the internet (base compose does not map those ports)
- Commit `.env` or any secret files
- Point production `CLIENT_URL` at `127.0.0.1`
- Run `docker compose` with a Hub pull of `m_sql_studio-api-gateway` (`pull_policy: never`; build locally or from your registry)
- Launch compose without `-p msql-studio`

## MongoDB password charset rule

`API_GATEWAY_MONGO_PASSWORD` may contain any printable ASCII. The gateway URL-encodes the password at MONGO_URI construction time (see `src/data/db/client/index.ts:encodeMongoPassword`). Do **not** escape/quote the value in `.env`; write the raw string. If you change the password, rebuild the gateway image so the new encoded URI is baked in.
