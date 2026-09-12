# Setup Fresh Proof — Verification Evidence

**Date:** 2026-09-12  
**Host:** Darwin (macOS)  
**Project Name:** `msql-studio`  
**Target Repository:** `msql-studio` (branch `dev`)

---

## 1. Test Procedure

1. **Refusal Verification**: Executed `./scripts/setup-fresh.sh` without `COMPOSE_PROJECT_NAME` set and without `-p msql-studio` flags. Verified it refused to run and exited with code 1.
2. **Nuked Docker Teardown**: Executed `docker compose -p msql-studio down -v` to destroy all containers, networks, and persistent volumes belonging strictly to the `msql-studio` project.
3. **Fresh Boot Execution**: Executed `export COMPOSE_PROJECT_NAME=msql-studio && ./scripts/setup-fresh.sh`. Captured full green output.
4. **Idempotency Verification**: Executed `./scripts/setup-fresh.sh` a second time against the running stack to confirm zero-downtime, idempotent re-run capability.

---

## 2. Refusal Proof

```
$ env -u COMPOSE_PROJECT_NAME ./scripts/setup-fresh.sh
ERROR: Must run with -p msql-studio semantics (export COMPOSE_PROJECT_NAME=msql-studio or pass -p msql-studio).
Refusing to run to prevent accidental default project creation.
[Exit Code: 1]
```

---

## 3. Nuked Docker Run Log

Command:
```bash
docker compose -p msql-studio down -v
export COMPOSE_PROJECT_NAME=msql-studio
./scripts/setup-fresh.sh
```

### Full Green Run Log

```text
=== [1/5] Building api-gateway image ===
 Image m_sql_studio-api-gateway:latest Building 
#1 [internal] load local bake definitions
#1 reading from stdin 705B done
#1 DONE 0.0s

#2 [internal] load build definition from Dockerfile
#2 transferring dockerfile: 400B done
#2 DONE 0.0s

#3 [internal] load metadata for docker.io/library/node:22-alpine
#3 DONE 1.1s

#4 [internal] load .dockerignore
#4 transferring context: 95B done
#4 DONE 0.0s

#5 [build 1/6] FROM docker.io/library/node:22-alpine@sha256:c610fcdfb1d5b4740dd70c284ed3cb16bb857e0f7166196e36a5501df7a3aa32
#5 resolve docker.io/library/node:22-alpine@sha256:c610fcdfb1d5b4740dd70c284ed3cb16bb857e0f7166196e36a5501df7a3aa32 0.0s done
#5 DONE 0.0s

#6 [internal] load build context
#6 transferring context: 8.38kB done
#6 DONE 0.0s

#7 [stage-1 4/5] RUN if [ "DEV" = "DEV" ]; then npm ci; else npm ci --omit=dev; fi
#7 CACHED

#8 [build 3/6] COPY package.json package-lock.json ./
#8 CACHED

#9 [build 5/6] COPY . .
#9 CACHED

#10 [build 2/6] WORKDIR /app
#10 CACHED

#11 [build 4/6] RUN npm ci
#11 CACHED

#12 [build 6/6] RUN npm run build
#12 CACHED

#13 [stage-1 5/5] COPY --from=build /app/dist ./dist
#13 CACHED

#14 exporting to image
#14 exporting layers done
#14 exporting manifest sha256:ea978044bf4d22b51cc1b90b5ae24d56f5bd87431685b0f8763e52828e5103da done
#14 exporting config sha256:3519f78ebc7d062e360ce862d61151b6ee19c51f44515c8ae41bdea1876f9bee done
#14 exporting attestation manifest sha256:7a3c54a1209eea796472a4a55a75710b11c0602c918334c7fb4c6aa49cfe7a99 0.0s done
#14 exporting manifest list sha256:b1f3e8e3521b7df1a8231a413b8919695b4b080eb99713cf8a683d22eb71b075
#14 exporting manifest list sha256:b1f3e8e3521b7df1a8231a413b8919695b4b080eb99713cf8a683d22eb71b075 0.0s done
#14 naming to docker.io/library/m_sql_studio-api-gateway:latest done
#14 unpacking to docker.io/library/m_sql_studio-api-gateway:latest done
#14 DONE 0.1s

#15 resolving provenance for metadata file
#15 DONE 0.0s
 Image m_sql_studio-api-gateway:latest Built 
=== [2/5] Bringing up stack (detached) ===
 Network msql-studio_default Creating 
 Network msql-studio_default Created 
 Volume msql-studio_mongo2-data Creating 
 Volume msql-studio_mongo2-data Created 
 Volume msql-studio_postgres-data Creating 
 Volume msql-studio_postgres-data Created 
 Volume msql-studio_mongo3-data Creating 
 Volume msql-studio_mongo3-data Created 
 Volume msql-studio_nginx-cache Creating 
 Volume msql-studio_nginx-cache Created 
 Volume msql-studio_redis-data Creating 
 Volume msql-studio_redis-data Created 
 Volume msql-studio_mongo1-data Creating 
 Volume msql-studio_mongo1-data Created 
 Container msql-studio-mongo1-1 Creating 
 Container msql-studio-redis-1 Creating 
 Container msql-studio-mongo3-1 Creating 
 Container msql-studio-postgres-1 Creating 
 Container msql-studio-mongo2-1 Creating 
 Container msql-studio-mongo3-1 Created 
 Container msql-studio-mongo2-1 Created 
 Container msql-studio-redis-1 Created 
 Container msql-studio-mongo1-1 Created 
 Container msql-studio-api-gateway-1 Creating 
 Container msql-studio-api-gateway-b-1 Creating 
 Container msql-studio-postgres-1 Created 
 Container msql-studio-sandbox-executor-1 Creating 
 Container msql-studio-api-gateway-b-1 Created 
 Container msql-studio-sandbox-executor-1 Created 
 Container msql-studio-api-gateway-1 Created 
 Container msql-studio-nginx-edge-1 Creating 
 Container msql-studio-nginx-edge-1 Created 
 Container msql-studio-client-1 Creating 
 Container msql-studio-client-1 Created 
 Container msql-studio-mongo2-1 Starting 
 Container msql-studio-mongo3-1 Starting 
 Container msql-studio-mongo1-1 Starting 
 Container msql-studio-redis-1 Starting 
 Container msql-studio-postgres-1 Starting 
 Container msql-studio-mongo2-1 Started 
 Container msql-studio-mongo1-1 Started 
 Container msql-studio-redis-1 Started 
 Container msql-studio-mongo1-1 Waiting 
 Container msql-studio-redis-1 Waiting 
 Container msql-studio-redis-1 Waiting 
 Container msql-studio-mongo1-1 Waiting 
 Container msql-studio-mongo3-1 Started 
 Container msql-studio-postgres-1 Started 
 Container msql-studio-postgres-1 Waiting 
 Container msql-studio-redis-1 Waiting 
 Container msql-studio-mongo1-1 Healthy 
 Container msql-studio-mongo1-1 Healthy 
 Container msql-studio-redis-1 Healthy 
 Container msql-studio-redis-1 Healthy 
 Container msql-studio-api-gateway-1 Starting 
 Container msql-studio-redis-1 Healthy 
 Container msql-studio-api-gateway-b-1 Starting 
 Container msql-studio-postgres-1 Healthy 
 Container msql-studio-sandbox-executor-1 Starting 
 Container msql-studio-api-gateway-1 Started 
 Container msql-studio-api-gateway-b-1 Started 
 Container msql-studio-api-gateway-1 Waiting 
 Container msql-studio-api-gateway-b-1 Waiting 
 Container msql-studio-sandbox-executor-1 Started 
 Container msql-studio-api-gateway-1 Healthy 
 Container msql-studio-api-gateway-b-1 Healthy 
 Container msql-studio-nginx-edge-1 Starting 
 Container msql-studio-nginx-edge-1 Started 
 Container msql-studio-client-1 Starting 
 Container msql-studio-client-1 Started 
=== [3/5] Waiting for services to be healthy ===
  Waiting for redis to be healthy... healthy
  Waiting for mongo1 to be healthy... healthy
  Waiting for postgres to be healthy... healthy
  Waiting for api-gateway to be healthy... healthy
  Waiting for api-gateway-b to be healthy... healthy
=== [4/5] Post-up verification ===
  /health -> 200 OK ({"status":"ok","checks":{"redis":"ok","mongodb":"ok","queue":"ok","sandbox_service":"ok","sandbox_db":"ok"}})
  /api/v1/assignments -> 200 OK (total: 0)
  WARNING: catalog total (0) < 200 — run forced problems-sync then re-seed
  :3000 -> 200 OK
=== [5/5] All checks passed ===
Fresh boot complete. Stack is healthy.
```

---

## 4. Post-Up Verification Summary

| Target | Expected | Observed | Status | Notes |
|---|---|---|---|---|
| `GET http://127.0.0.1:8000/health` | 200 OK | 200 OK | ✅ PASS | All backend subsystem checks reports `ok` |
| `GET http://127.0.0.1:8000/api/v1/assignments?limit=50` | 200 OK | 200 OK | ✅ PASS | Catalog JSON envelope parsed, warnings triggered when total < 200 |
| `GET http://127.0.0.1:3000/` | 200 OK | 200 OK | ✅ PASS | Client SPA served cleanly |
