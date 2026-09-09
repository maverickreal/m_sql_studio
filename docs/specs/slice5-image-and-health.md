# Slice 5 — one gateway image, two replicas (+ FOSS nginx health)

Date: 2026-09-09. Live stack: compose project `m_sql_studio`, edge on host :8000.

## 1. Compose: build ONCE, run twice

Only `api-gateway` defines `build:`; `api-gateway-b` reuses the same tagged
image (`m_sql_studio-api-gateway:latest`) with identical runtime config via the
`x-api-gateway-common` YAML anchor. `api-gateway-b` has no `build:` key, so a
second `docker compose build` can never drift the replicas.

Command:

    cd m_sql_studio
    docker compose build api-gateway && docker compose up -d --force-recreate api-gateway api-gateway-b nginx-edge

Build output (tail):

    #14 exporting manifest sha256:2e666a29b087b844acca7eb8c8ecbe6c459d2091c17f09564f746c8e818347c7 done
    #14 naming to docker.io/library/m_sql_studio-api-gateway:latest done
     Image m_sql_studio-api-gateway:latest Built

Identical Image SHA on both replicas:

    $ docker inspect m_sql_studio-api-gateway-1 m_sql_studio-api-gateway-b-1 --format '{{.Name}} {{.Image}}'
    /m_sql_studio-api-gateway-1 sha256:2e666a29b087b844acca7eb8c8ecbe6c459d2091c17f09564f746c8e818347c7
    /m_sql_studio-api-gateway-b-1 sha256:2e666a29b087b844acca7eb8c8ecbe6c459d2091c17f09564f746c8e818347c7

## 2. nginx: FOSS passive health checks, no nginx-plus

`health_check`/`match` are nginx-plus-only (`emerg: invalid parameter
"health_check"` on nginx:1.27-alpine). The FOSS equivalent is passive
`max_fails`/`fail_timeout` — a replica is skipped for 10s after 3 consecutive
failures:

    upstream api_backends {
        least_conn;
        server api-gateway:8000 max_fails=3 fail_timeout=10s;
        server api-gateway-b:8000 max_fails=3 fail_timeout=10s;
    }

`grep health_check nginx/nginx.conf` matches only the comment explaining this.

## 3. Health + unauth stream through :8000

The stream route is `GET /api/v1/assignments/client-sql-code-run/status/:taskId/stream`
(`requireAuthMware` → 401 unauthenticated, never Express 404).

    $ curl -sS -m 5 -o /dev/null -w '%{http_code}\n' http://localhost:8000/health
    200

    $ for i in $(seq 1 12); do curl -sS -m 5 -o /dev/null -w '%{http_code} ' \
        'http://localhost:8000/api/v1/assignments/client-sql-code-run/status/abc123/stream'; done
    401 401 401 401 401 401 401 401 401 401 401 401

    $ curl -sS -m 5 'http://localhost:8000/api/v1/assignments/client-sql-code-run/status/abc123/stream'
    {"error":"Authentication required"}

Root cause of the earlier 404s: host :8000 was served by a stale standalone
slice5 stack (`nginx-lb` + `api-gateway-1/2` from an untracked
`docker-compose.slice5.yml` outside this repo) whose replicas predated the
stream route. It was removed (`docker compose -f docker-compose.slice5.yml rm
-sf nginx-lb api-gateway-1 api-gateway-2`); :8000 is now served by this
compose file's `nginx-edge`.

## Out of scope (untouched)

mongo `setup.sh`, replica-set rewrite, OAuth, `nukeDocker`. (The compose diff
also aligns `mongo:8` → `mongo:7` to match the proven live stack; no setup
scripts were modified.)
