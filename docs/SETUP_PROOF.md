# Setup Fresh Proof — Verification Evidence

**Date:** 2026-09-12  
**Host:** Darwin (macOS)  
**Project Name:** `msql-studio`  
**Target Repository:** `msql-studio` (branch `dev`)  
**Card:** `t_45f33a49`

---

## 1. Test Procedure

1. **Refusal Verification**: Executed `./scripts/setup-fresh.sh` without `COMPOSE_PROJECT_NAME=msql-studio` set and without `-p msql-studio` flags. Verified it refused to run and exited with code 1.
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
=== [1/6] Building all images (gateway, client, sandbox) ===
 Image msql-studio-client Building 
 Image msql-studio-sandbox-executor Building 
 Image m_sql_studio-api-gateway:latest Building 
#1 [internal] load local bake definitions
#1 reading from stdin 1.96kB done
#1 DONE 0.0s

#2 [api-gateway internal] load build definition from Dockerfile
#2 DONE 0.0s

#3 [sandbox-executor internal] load build definition from Dockerfile
#3 transferring dockerfile: 484B done
#3 DONE 0.0s

#2 [api-gateway internal] load build definition from Dockerfile
#2 transferring dockerfile: 497B done
#2 DONE 0.0s

#4 [client internal] load build definition from Dockerfile
#4 transferring dockerfile: 620B done
#4 DONE 0.0s

#5 [client] resolve image config for docker-image://docker.io/docker/dockerfile:1.4
#5 DONE 2.3s

#6 [client] docker-image://docker.io/docker/dockerfile:1.4@sha256:9ba7531bd80fb0a858632727cf7a112fbfd19b17e94c4e84ced81e24ef1a0dbc
#6 resolve docker.io/docker/dockerfile:1.4@sha256:9ba7531bd80fb0a858632727cf7a112fbfd19b17e94c4e84ced81e24ef1a0dbc 0.0s done
#6 CACHED

#7 [api-gateway internal] load .dockerignore
#7 transferring context: 95B done
#7 DONE 0.0s

#8 [client internal] load .dockerignore
#8 transferring context: 96B done
#8 DONE 0.0s

#9 [sandbox-executor internal] load .dockerignore
#9 transferring context: 95B done
#9 DONE 0.0s

#10 [client internal] load metadata for docker.io/oven/bun:1.4-alpine
#10 DONE 0.0s

#11 [client internal] load metadata for docker.io/library/nginx:alpine
#11 ...

#12 [sandbox-executor build 1/6] FROM docker.io/oven/bun:1.4-alpine@sha256:d888c0ae6c86d7866ff10c5aafdd9077b36aee6455b33dd270fb93c0dd5cef6f
#12 resolve docker.io/oven/bun:1.4-alpine@sha256:d888c0ae6c86d7866ff10c5aafdd9077b36aee6455b33dd270fb93c0dd5cef6f 0.0s done
#12 DONE 0.0s

#13 [sandbox-executor internal] load build context
#13 transferring context: 2.64kB done
#13 DONE 0.0s

#14 [sandbox-executor build 2/6] WORKDIR /app
#14 CACHED

#15 [sandbox-executor build 3/6] COPY package.json bun.lock* ./
#15 CACHED

#16 [sandbox-executor build 6/6] RUN bun run build
#16 CACHED

#17 [sandbox-executor stage-1 4/5] RUN if [ "DEV" = "DEV" ]; then bun install --frozen-lockfile; else bun install --frozen-lockfile --production; fi
#17 CACHED

#18 [sandbox-executor build 4/6] RUN bun install --frozen-lockfile
#18 CACHED

#19 [sandbox-executor build 5/6] COPY . .
#19 CACHED

#20 [sandbox-executor stage-1 5/5] COPY --from=build /app/dist ./dist
#20 CACHED

#21 [api-gateway internal] load build context
#21 transferring context: 17.19MB 0.1s done
#21 DONE 0.1s

#14 [api-gateway build 2/6] WORKDIR /app
#14 CACHED

#22 [api-gateway build 3/6] COPY package.json bun.lock* ./
#22 CACHED

#23 [api-gateway build 4/6] RUN bun install --frozen-lockfile
#23 CACHED

#24 [sandbox-executor] exporting to image
#24 exporting layers done
#24 exporting manifest sha256:f66b943e2ad42565e61f39301ec29fd9e93f5ac2bf2681d4991b5c035f51b161 done
#24 exporting config sha256:a7847b2060aba40e55873ef0c2df98f3c22e5a7389ac98e4e89f8d1e5796e95d done
#24 exporting attestation manifest sha256:79c12b9e627e2a592683e21a874b240ca3334ed56577aab1e06d5127308dbfa5 0.0s done
#24 exporting manifest list sha256:fef38af21aacda493a63aa4ceaeaf5c272e1148500b2aa28461c83f6c6fb4d4e 0.0s done
#24 naming to docker.io/library/msql-studio-sandbox-executor:latest done
#24 unpacking to docker.io/library/msql-studio-sandbox-executor:latest 0.0s done
#24 DONE 0.1s

#25 [api-gateway build 5/6] COPY . .
#25 DONE 0.2s

#11 [client internal] load metadata for docker.io/library/nginx:alpine
#11 ...

#26 [sandbox-executor] resolving provenance for metadata file
#26 DONE 0.0s

#27 [api-gateway build 6/6] RUN bun run build
#27 0.170 $ tsc
#27 ...

#11 [client internal] load metadata for docker.io/library/nginx:alpine
#11 DONE 1.6s

#12 [client build 1/6] FROM docker.io/oven/bun:1.4-alpine@sha256:d888c0ae6c86d7866ff10c5aafdd9077b36aee6455b33dd270fb93c0dd5cef6f
#12 resolve docker.io/oven/bun:1.4-alpine@sha256:d888c0ae6c86d7866ff10c5aafdd9077b36aee6455b33dd270fb93c0dd5cef6f 0.0s done
#12 DONE 0.0s

#28 [client internal] load build context
#28 transferring context: 78.02kB 0.0s done
#28 DONE 0.0s

#29 [client stage-1 1/3] FROM docker.io/library/nginx:alpine@sha256:72ba65eb42c10344912a84ff42408db7d34f2feb642204570ab8fc5ffd29f1d3
#29 resolve docker.io/library/nginx:alpine@sha256:72ba65eb42c10344912a84ff42408db7d34f2feb642204570ab8fc5ffd29f1d3 0.0s done
#29 DONE 0.0s

#14 [client build 2/6] WORKDIR /app
#14 CACHED

#30 [client build 3/6] COPY package.json bun.lock* ./
#30 CACHED

#31 [client build 4/6] RUN bun install --frozen-lockfile
#31 CACHED

#32 [client build 5/6] COPY . .
#32 DONE 0.1s

#27 [api-gateway build 6/6] RUN bun run build
#27 ...

#33 [client build 6/6] RUN bun run build
#33 0.142 $ tsc -b && bun --bun vite build
#33 ...

#27 [api-gateway build 6/6] RUN bun run build
#27 DONE 7.6s

#33 [client build 6/6] RUN bun run build
#33 6.731 vite v6.4.3 building for production...
#33 6.825 transforming...
#33 8.052 node_modules/zod/v4/core/regexes.js (72:0): A comment
#33 8.052 
#33 8.052 "/** Anchors a pattern source. The interpolation lives here rather than at the call site because
#33 8.052  * esbuild will not drop a `@__PURE__` call whose own argument interpolates a variable, but it
#33 8.052  * will drop `anchor(dateSource)`. Keeping it inline pinned `date` into every bundle. */"
#33 8.052 
#33 8.052 in "node_modules/zod/v4/core/regexes.js" contains an annotation that Rollup cannot interpret due to the position of the comment. The comment will be removed to avoid issues.
#33 ...

#34 [api-gateway stage-1 4/5] RUN if [ "DEV" = "DEV" ]; then bun install --frozen-lockfile; else bun install --frozen-lockfile --production; fi
#34 CACHED

#33 [client build 6/6] RUN bun run build
#33 8.059 node_modules/zod/v4/core/util.js (400:0): A comment
#33 8.059 
#33 8.059 "// Wrapped in a `@__PURE__` IIFE: esbuild never tree-shakes a top-level initializer that contains a member access on `Number`, so the bare object literal survived into every bundle."
#33 8.059 
#33 8.059 in "node_modules/zod/v4/core/util.js" contains an annotation that Rollup cannot interpret due to the position of the comment. The comment will be removed to avoid issues.
#33 ...

#35 [api-gateway stage-1 5/5] COPY --from=build /app/dist ./dist
#35 CACHED

#36 [api-gateway] exporting to image
#36 exporting layers 0.0s done
#36 exporting manifest sha256:5670f2bbd4b7f17c14dac7cffaf8945e4e00077c91a66ed47a2e106b8357687e done
#36 exporting config sha256:4083a16a7e088546deac34304db6548f18fc4f044b2e96c98fb20d494fadf7ee 0.0s done
#36 exporting attestation manifest sha256:53c3173fed747f95e180b17f30c1b0a80fa4226893b5bab77e2dda50fd42dd1d 0.0s done
#36 exporting manifest list sha256:0ba7baa5417244cfc20f960f9b9af9b5de88f625f7fe8b1e544d070d03a5b110 0.0s done
#36 naming to docker.io/library/m_sql_studio-api-gateway:latest done
#36 unpacking to docker.io/library/m_sql_studio-api-gateway:latest 0.0s done
#36 DONE 0.2s

#33 [client build 6/6] RUN bun run build
#33 ...

#37 [api-gateway] resolving provenance for metadata file
#37 DONE 0.0s

#33 [client build 6/6] RUN bun run build
#33 9.648 ✓ 2498 modules transformed.
#33 9.857 rendering chunks...
#33 10.22 computing gzip size...
#33 10.26 dist/index.html                                 1.31 kB │ gzip:   0.58 kB
#33 10.26 dist/assets/index-BGjT3Tg8.css                 37.43 kB │ gzip:   7.48 kB
#33 10.26 dist/assets/PageTransition-BXDFezt4.js          0.32 kB │ gzip:   0.25 kB │ map:     0.90 kB
#33 10.26 dist/assets/errors-lvEBuooj.js                  0.35 kB │ gzip:   0.20 kB │ map:     1.27 kB
#33 10.26 dist/assets/Badge-C7pmxd5G.js                   0.52 kB │ gzip:   0.34 kB │ map:     1.08 kB
#33 10.26 dist/assets/Input-DrgpJT3R.js                   0.82 kB │ gzip:   0.51 kB │ map:     1.93 kB
#33 10.26 dist/assets/Textarea-fuSnlOiM.js                0.83 kB │ gzip:   0.52 kB │ map:     1.98 kB
#33 10.26 dist/assets/Table-DkINJFDp.js                   0.87 kB │ gzip:   0.48 kB │ map:     2.78 kB
#33 10.26 dist/assets/AdminLayout-DGRbGRqM.js             1.50 kB │ gzip:   0.76 kB │ map:     3.56 kB
#33 10.26 dist/assets/AuditAdminPage-D3ZTS-u2.js          2.12 kB │ gzip:   0.88 kB │ map:     5.00 kB
#33 10.26 dist/assets/LeaderboardPage-B8IoDWHy.js         2.14 kB │ gzip:   0.99 kB │ map:     5.32 kB
#33 10.26 dist/assets/AssignmentsAdminPage-Bvdrl6fq.js    2.21 kB │ gzip:   0.91 kB │ map:     5.10 kB
#33 10.26 dist/assets/SignInPage-DdMi81gF.js              2.33 kB │ gzip:   1.13 kB │ map:     6.41 kB
#33 10.26 dist/assets/UsersAdminPage-BVybDHr2.js          2.50 kB │ gzip:   1.02 kB │ map:     6.94 kB
#33 10.26 dist/assets/SocialSignInButtons-BNA_oVE5.js     2.53 kB │ gzip:   1.38 kB │ map:     5.78 kB
#33 10.26 dist/assets/SignUpPage-BY4z6WTi.js              2.57 kB │ gzip:   1.21 kB │ map:     7.09 kB
#33 10.26 dist/assets/PublicProfilePage-DjNsnKyr.js       3.26 kB │ gzip:   1.11 kB │ map:     7.29 kB
#33 10.26 dist/assets/LandingPage-o7ZHeJKp.js             3.84 kB │ gzip:   1.56 kB │ map:     9.32 kB
#33 10.26 dist/assets/CreateAssignmentPage-ClRnhMGF.js    5.20 kB │ gzip:   1.90 kB │ map:    14.44 kB
#33 10.26 dist/assets/ProfilePage-D8mIdF2d.js             7.31 kB │ gzip:   2.39 kB │ map:    18.45 kB
#33 10.26 dist/assets/AssignmentListPage-Drh1Oxh9.js      8.60 kB │ gzip:   2.96 kB │ map:    24.47 kB
#33 10.26 dist/assets/schemas-DuwpXDev.js                81.95 kB │ gzip:  23.91 kB │ map:   515.91 kB
#33 10.26 dist/assets/react-CCSy81nK.js                 124.81 kB │ gzip:  41.25 kB │ map:   686.98 kB
#33 10.26 dist/assets/AssignmentDetailPage-CTptq4R8.js  335.69 kB │ gzip: 112.61 kB │ map: 1,720.27 kB
#33 10.26 dist/assets/index-BmcM16YQ.js                 450.75 kB │ gzip: 147.99 kB │ map: 2,271.96 kB
#33 10.26 ✓ built in 3.48s
#33 DONE 10.7s

#38 [client stage-1 2/3] COPY nginx.conf /etc/nginx/conf.d/default.conf.template
#38 CACHED

#39 [client stage-1 3/3] COPY --from=build /app/dist /usr/share/nginx/html
#39 CACHED

#40 [client] exporting to image
#40 exporting layers done
#40 exporting manifest sha256:b088186a72f014e0024fa6b29a4d16823fcf63652fea115a9b85c03e113728bf done
#40 exporting config sha256:189176147ab50f3e04ef876ccf422bf557e82019b64b6846c6eac0394dbe31ea done
#40 exporting attestation manifest sha256:4282bc5c8fa6d1b4bbe3879085c6c3055862674c390383c28e3cd94d825922a3 0.0s done
#40 exporting manifest list sha256:0b131744a4b5be1da01fa88e6ca68653559cdda1c7469a8d2073206a11ac01d7 0.0s done
#40 naming to docker.io/library/msql-studio-client:latest done
#40 unpacking to docker.io/library/msql-studio-client:latest 0.0s done
#40 DONE 0.1s

#41 [client] resolving provenance for metadata file
#41 DONE 0.0s
 Image m_sql_studio-api-gateway:latest Built 
 Image msql-studio-client Built 
 Image msql-studio-sandbox-executor Built 
=== [2/6] Bringing up stack with DEV overlay (detached) ===
 Network msql-studio_default Creating 
 Network msql-studio_default Created 
 Volume msql-studio_mongo2-data Creating 
 Volume msql-studio_mongo2-data Created 
 Volume msql-studio_postgres-data Creating 
 Volume msql-studio_postgres-data Created 
 Volume msql-studio_nginx-cache Creating 
 Volume msql-studio_nginx-cache Created 
 Volume msql-studio_redis-data Creating 
 Volume msql-studio_redis-data Created 
 Volume msql-studio_mongo1-data Creating 
 Volume msql-studio_mongo1-data Created 
 Volume msql-studio_mongo3-data Creating 
 Volume msql-studio_mongo3-data Created 
 Container msql-studio-redis-1 Creating 
 Container msql-studio-mongo2-1 Creating 
 Container msql-studio-mongo3-1 Creating 
 Container msql-studio-mongo1-1 Creating 
 Container msql-studio-postgres-1 Creating 
 Container msql-studio-mongo2-1 Created 
 Container msql-studio-mongo3-1 Created 
 Container msql-studio-mongo1-1 Created 
 Container msql-studio-redis-1 Created 
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
 Container msql-studio-redis-1 Starting 
 Container msql-studio-mongo3-1 Starting 
 Container msql-studio-mongo1-1 Starting 
 Container msql-studio-postgres-1 Starting 
 Container msql-studio-postgres-1 Started 
 Container msql-studio-mongo1-1 Started 
 Container msql-studio-redis-1 Started 
 Container msql-studio-redis-1 Waiting 
 Container msql-studio-mongo1-1 Waiting 
 Container msql-studio-postgres-1 Waiting 
 Container msql-studio-redis-1 Waiting 
 Container msql-studio-mongo1-1 Waiting 
 Container msql-studio-redis-1 Waiting 
 Container msql-studio-mongo3-1 Started 
 Container msql-studio-mongo2-1 Started 
 Container msql-studio-mongo1-1 Healthy 
 Container msql-studio-mongo1-1 Healthy 
 Container msql-studio-postgres-1 Healthy 
 Container msql-studio-redis-1 Healthy 
 Container msql-studio-redis-1 Healthy 
 Container msql-studio-api-gateway-b-1 Starting 
 Container msql-studio-redis-1 Healthy 
 Container msql-studio-api-gateway-1 Starting 
 Container msql-studio-sandbox-executor-1 Starting 
 Container msql-studio-api-gateway-b-1 Started 
 Container msql-studio-api-gateway-1 Started 
 Container msql-studio-api-gateway-1 Waiting 
 Container msql-studio-api-gateway-b-1 Waiting 
 Container msql-studio-sandbox-executor-1 Started 
 Container msql-studio-api-gateway-1 Healthy 
 Container msql-studio-api-gateway-b-1 Healthy 
 Container msql-studio-nginx-edge-1 Starting 
 Container msql-studio-nginx-edge-1 Started 
 Container msql-studio-client-1 Starting 
 Container msql-studio-client-1 Started 
=== [3/6] Waiting for services to be healthy (timeout: 5m) ===
  Waiting for redis to be healthy... healthy
  Waiting for mongo1 to be healthy... healthy
  Waiting for postgres to be healthy... healthy
  Waiting for api-gateway to be healthy... healthy
  Waiting for api-gateway-b to be healthy... healthy
=== [4/6] Post-up verification (/health, catalog, :3000) ===
  /health -> 200 OK ({"status":"ok","checks":{"redis":"ok","mongodb":"ok","queue":"ok","sandbox_service":"ok","sandbox_db":"ok"}})
  /api/v1/assignments -> 200 OK
  :3000 -> 200 OK
=== [5/6] Catalog gate (sync & live unique-title verification) ===
  Current live unique titles: 0
  Catalog unique count (0) < 25 — running seed.js...
Seeding Database with sample assignments.
API Gateway is up and ready for seeding!
Authenticating as admin user...
Admin authentication complete.
Seeding assignment: E-commerce: Order Totals.
Seeded Assignment 6aa573fda82aa2178ec272e9.
Seeding assignment: School Management: Student Enrollment.
Seeded Assignment 6aa573fda82aa2178ec272ec.
Seeding assignment: Library System: Outdated Books Cleanup.
Seeded Assignment 6aa573fd2b99248f6a7ad20d.
Seeding assignment: HR: Employee Salary Update.
Seeded Assignment 6aa573fd2b99248f6a7ad210.
Seeding assignment: Leaderboard: Top Scores.
Seeded Assignment 6aa573fda82aa2178ec272ef.
Seeding assignment: Pet Shelter: Dogs Ready for Adoption.
Seeded Assignment 6aa573fda82aa2178ec272f2.
Seeding assignment: Cinema: Evening Showtimes.
Seeded Assignment 6aa573fd2b99248f6a7ad213.
Seeding assignment: Grocery: Low Stock Produce.
Seeded Assignment 6aa573fd2b99248f6a7ad216.
Seeding assignment: Gym: Active Members Roll.
Seeded Assignment 6aa573fda82aa2178ec272f5.
Seeding assignment: Transit: Downtown Stops by Frequency.
Seeded Assignment 6aa573fda82aa2178ec272f8.
Seeding assignment: Music: Most Played Tracks.
Seeded Assignment 6aa573fd2b99248f6a7ad219.
Seeding assignment: Restaurant: Revenue Per Dish.
Seeded Assignment 6aa573fd2b99248f6a7ad21c.
Seeding assignment: Clinic: Upcoming Visits with Doctors.
Seeded Assignment 6aa573fda82aa2178ec272fb.
Seeding assignment: Airline: Seats Booked Per Flight.
Seeded Assignment 6aa573fda82aa2178ec272fe.
Seeding assignment: Bank: Low Balance Checking Accounts.
Seeded Assignment 6aa573fd2b99248f6a7ad21f.
Seeding assignment: Warehouse: Stock Value by Aisle.
Seeded Assignment 6aa573fd2b99248f6a7ad222.
Seeding assignment: Real Estate: Average Rent by Neighborhood.
Seeded Assignment 6aa573fda82aa2178ec27301.
Seeding assignment: Music: Loyal Listeners.
Seeded Assignment 6aa573fda82aa2178ec27304.
Seeding assignment: Airline: One-Stop Connections from Aster.
Seeded Assignment 6aa573fd2b99248f6a7ad225.
Seeding assignment: Bank: Heavy Senders.
Seeded Assignment 6aa573fd2b99248f6a7ad228.
Seeding assignment: Cinema: Clear Unclaimed Past Reservations.
Seeded Assignment 6aa573fda82aa2178ec27307.
Seeding assignment: Gym: Deactivate Lapsed Trials.
Seeded Assignment 6aa573fda82aa2178ec2730a.
Seeding assignment: Pet Shelter: Record an Adoption.
Seeded Assignment 6aa573fd2b99248f6a7ad22b.
Seeding assignment: Warehouse: Book an Incoming Shipment.
Seeded Assignment 6aa573fd2b99248f6a7ad22e.
Seeding assignment: Bank: Post Monthly Interest.
Seeded Assignment 6aa573fda82aa2178ec2730d.
Seeding complete.
  Base assignments seeded. Current unique titles: 25
  Triggering forced problems-sync via POST /internal/problems-sync...
  Problems-sync triggered (HTTP 202: {"jobId":"1"}).
  Polling live unique-title count to >= 200 (timeout 15m; sync tests-before-write)...
  [+0s] Live unique titles: 25 / 200
  [+6s] Live unique titles: 25 / 200
  [+11s] Live unique titles: 203 / 200
  Catalog gate PASSED: live unique titles = 203 (>= 200).
=== [6/6] All checks and catalog gate passed ===
Fresh boot complete. Stack is healthy and catalog contains 203 unique problems (total: 203).
```

---

## 4. Post-Up & Catalog Gate Verification Summary

| Target | Expected | Observed | Status | Notes |
|---|---|---|---|---|
| Refusal without `COMPOSE_PROJECT_NAME=msql-studio` | Exit 1 | Exit 1 | ✅ PASS | Enforces single true project name, prevents duplicate stack |
| DEV overlay (`docker-compose.dev.yml`) | Active | Active | ✅ PASS | DB host ports exposed, mem limits set, problems repo mounted |
| Service Health Checks (`redis`, `mongo1`, `postgres`, `gateway x2`) | All `healthy` | All `healthy` | ✅ PASS | Wait loop confirmed 5/5 services healthy |
| `GET http://127.0.0.1:8000/health` | 200 OK | 200 OK | ✅ PASS | All backend subsystem checks report `ok` |
| `GET http://127.0.0.1:8000/api/v1/assignments?limit=50` | 200 OK | 200 OK | ✅ PASS | Catalog JSON envelope accessible |
| `GET http://127.0.0.1:3000/` | 200 OK | 200 OK | ✅ PASS | Client SPA served cleanly |
| Base Assignment Seeding (`misc/seed.js`) | 25 seeded | 25 seeded | ✅ PASS | Paced seeding with admin authentication |
| `POST http://127.0.0.1:8000/internal/problems-sync` | 202 Accepted | 202 Accepted | ✅ PASS | Forced sync enqueued with `x-internal-api-key` |
| Catalog Gate: Live Unique Titles | >= 200 | 203 | ✅ PASS | 178 gold YAML problems synced + 25 seed assignments |
| Idempotent Re-Run (`./scripts/setup-fresh.sh`) | 0 errors | 0 errors | ✅ PASS | Catalog remains at 203, gate passes instantly |
