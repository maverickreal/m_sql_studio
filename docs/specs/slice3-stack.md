# Slice3 — One stack + Mongo replica set

## What this is

The single canonical compose stack for m_sql_studio, running as one compose
project (`m_sql_studio`) with a three-node Mongo replica set (`rs0`).

Previous duplicate `msql-studio-*` containers and their volumes have been
removed — only the `m_sql_studio` compose project should exist.

## Exact up command

```bash
cd /Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio
docker compose -p m_sql_studio up -d
```

This uses the project name `m_sql_studio` so container names, networks and
volumes are deterministic. Do **not** run `docker compose up` without `-p` —
Docker would derive the project name from the directory, which previously
created the duplicate `msql-studio-*` stack.

## Compose files used

- `docker-compose.yml` — main definition (redis, mongo1/2/3, postgres, api-gateway, api-gateway-b, nginx-edge, sandbox-executor, client).
- `docker-compose.dev.yml` — dev overrides (mongo `mem_limit: 512m`, sandbox `mem_limit: 512m cpus: 1.0`).

## Health & verification

```bash
curl -sS -m 5 http://127.0.0.1:8000/health
# → {"status":"ok","checks":{"redis":"ok","mongodb":"ok","queue":"ok",...}}

docker compose -p m_sql_studio ps
# All services up; mongo1 healthy (was unhealthy on the stale volume)
```

## Mongo replica set

Three-node set `rs0`:

- `mongo1:27017` — priority 2 (primary on init)
- `mongo2:27017`
- `mongo3:27017`

On first boot, `mongo1` runs `misc/init-db/mongodb/setup.sh` which calls
`rs.initiate` with the config above and creates the app users. Because the
stale `mongo1-data` volume had a broken RS state (auth enabled, no users),
the volume was recreated — this is the documented exception to "do not delete
data volumes" from the task spec.

## Reset / teardown

```bash
docker compose -p m_sql_studio down -v   # stops + removes all containers and volumes
docker compose -p m_sql_studio up -d     # fresh stack
```
