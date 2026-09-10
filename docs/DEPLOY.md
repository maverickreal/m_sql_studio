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

docker compose build api-gateway
docker compose up -d
```

Wait until `api-gateway` and `api-gateway-b` are healthy, then:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/health
curl -sS -D- http://127.0.0.1:8000/api/v1/assignments | head
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/
```

Both gateway replicas must share one image SHA (`docker inspect … --format '{{.Image}}'`).

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

## Hints

Default `HINT_ENABLED=false` in compose. To enable: set `HINT_ENABLED=true` and `HINT_API_URL` to a reachable OpenAI-compatible `/v1` (host Ollama = `http://host.docker.internal:11434/v1`). Remote vendor APIs: `HINT_ALLOW_REMOTE=true` plus remote URL/key — extra PII off-box is a founder say.

## Do not

- Publish Mongo/Redis/Postgres to the internet (base compose does not map those ports)
- Commit `.env`
- Point production `CLIENT_URL` at `127.0.0.1`
- Run `docker compose` with a Hub pull of `m_sql_studio-api-gateway` (`pull_policy: never`; build locally or from your registry)
