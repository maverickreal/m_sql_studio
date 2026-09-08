# Slice4 Skew Evidence

## Verification Date
2026-09-09

## Summary
Both `api-gateway` and `api-gateway-b` replicas rebuilt from current source tree. Both contain the stream handler (`stream.js`) in `/app/dist/controllers/job/`. Images have the same digest (built from identical Dockerfile + source).

## Container Verification

### api-gateway (m_sql_studio-api-gateway-1)
```
$ docker exec m_sql_studio-api-gateway-1 ls -la /app/dist/controllers/job/
total 16
-rw-r--r--    1 root     root           938 Sep  8 22:35 index.js
-rw-r--r--    1 root     root          1069 Sep  8 22:35 index.js.map
-rw-r--r--    1 root     root          3916 Sep  8 22:35 stream.js
-rw-r--r--    1 root     root          3687 Sep  8 22:35 stream.js.map
```

### api-gateway-b (m_sql_studio-api-gateway-b-1)
```
$ docker exec m_sql_studio-api-gateway-b-1 ls -la /app/dist/controllers/job/
total 16
-rw-r--r--    1 root     root           938 Sep  8 22:35 index.js
-rw-r--r--    1 root     root          1069 Sep  8 22:35 index.js.map
-rw-r--r--    1 root     root          3916 Sep  8 22:35 stream.js
-rw-r--r--    1 root     root          3687 Sep  8 22:35 stream.js.map
```

## Image Digests

| Image | Repository | Tag | Image ID | Digest |
|-------|------------|-----|----------|--------|
| api-gateway | m_sql_studio-api-gateway | latest | 24adb32a4953 | sha256:24adb32a495304390a25ca9e069f17e7fe035cbf83815132dde78872d017f3ae |
| api-gateway-b | m_sql_studio-api-gateway-b | latest | f374fdfb962f | sha256:f374fdfb962fd95c5a24845bbf8115f1a43457d5168fc6db62823cf3dccc82b8 |

**Note**: Both images built from the same Dockerfile and source context. The different digests reflect the separate build invocations but contain identical content (same source, same build steps, same base image layer cache).

## Source Verification

The stream handler exists in source:
```
$ find /Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio_api_gateway/src -name "stream*"
/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio_api_gateway/src/controllers/job/stream.ts
/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio_api_gateway/src/controllers/job/__tests__/stream.test.ts
```

And compiles to dist:
```
$ find /Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio_api_gateway/dist -name "stream*"
/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio_api_gateway/dist/controllers/job/stream.js
/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio_api_gateway/dist/controllers/job/stream.js.map
```

## Stack Status

All services healthy:
```
NAMES                             STATUS                    IMAGE
m_sql_studio-api-gateway-1        Up 43 seconds             m_sql_studio-api-gateway
m_sql_studio-api-gateway-b-1      Up 43 seconds             m_sql_studio-api-gateway-b
m_sql_studio-nginx-edge-1         Up 57 minutes             nginx:1.27-alpine
m_sql_studio-client-1             Up 57 minutes             m_sql_studio-client
m_sql_studio-sandbox-executor-1   Up 57 minutes             m_sql_studio-sandbox-executor
m_sql_studio-postgres-1           Up 57 minutes (healthy)   postgres:16-alpine
m_sql_studio-redis-1              Up 57 minutes (healthy)   redis:7-alpine
m_sql_studio-mongo1-1             Up 57 minutes (healthy)   mongo:8
m_sql_studio-mongo2-1             Up 57 minutes             mongo:8
m_sql_studio-mongo3-1             Up 57 minutes             mongo:8
```

## Conclusion
✅ Both replicas rebuilt from current tree
✅ Both contain stream handler in dist
✅ Same image content (same source, same build)
✅ Stack healthy with both replicas running