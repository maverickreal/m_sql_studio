# ADR 002 — SSE job-status stream

**Status:** accepted for slice 2 (replace 1s polling with EventSource + polling fallback)
**Date:** 2026-09-09
**Supersedes:** ADR 001 (polling kept for slice 1; SSE now justified — jobs still seconds, but we want the UI to update the instant a job terminates, and we want to stop burning a GET per second per open editor)

## Context

Slice 1 uses HTTP polling: client `useGetJobStatusQuery(taskId, { pollingInterval: 1000 })` until `completed` / `failed`. This works. Slice 2 replaces it with a Server-Sent Events stream that pushes the terminal state, with polling as a fallback when EventSource is unavailable (e.g. some corporate proxies, older browsers).

The pub/sub primitive is already in the stack: Redis 7. BullMQ runs on it. The sandbox worker already emits `completed` / `failed` events. We just do not publish them to a channel the gateway can subscribe to.

## Decision

Add one SSE endpoint on the gateway. The sandbox worker publishes a terminal-state message to a Redis channel named `job:{jobId}` when a job finishes. The gateway subscribes to that channel and streams events to the client. nginx gets a streaming location. The client switches to EventSource and falls back to the existing polling query if EventSource fails or the stream errors out.

## Exact contract

### Redis channel

- Name: `job:{jobId}` (e.g. for BullMQ job id `42`, publish to `job:42`)
- Publisher: sandbox worker, once per terminal state (`completed` or `failed`)
- Payload (JSON):
  ```json
  { "status": "completed", "result": { ... } }
  ```
  or
  ```json
  { "status": "failed", "result": { "error": "..." } }
  ```
  `result` shape is the existing `SqlExecutionResult` union (`SqlExecutionSuccess | SqlExecutionError`) — same as the polling endpoint returns today.
- TTL: not relied on. The message is consumed near-instantly. If no subscriber is listening, the message is lost and the client's SSE `error` event triggers the polling fallback.

### Gateway endpoint

- Route: `GET /api/v1/assignments/client-sql-code-run/status/:taskId/stream`
- Auth: `requireAuthMware` (cookie → better-auth session). Unauthenticated → 401.
- Owner check on connect: same logic as the polling endpoint — load job via `TaskQueueClient.getStatus(taskId)`, reject with 403 if `ownerUserId` is set and requester is not owner and not admin. Do this before writing any SSE headers so a 403/404 reaches the client as a normal HTTP response, not a broken stream.
- Owner check on each event: re-verify the subscriber is still owner-or-admin before writing each event. (Session revocation mid-stream is unlikely but cheap to guard.)
- Headers:
  ```
  Content-Type: text/event-stream
  Cache-Control: no-cache, no-transform
  Connection: keep-alive
  X-Accel-Buffering: no
  ```
- Event format (SSE):
  ```
  event: job-status
  data: {"status":"completed","result":{...}}

  ```
  One event per terminal state. After writing the terminal event, close the stream.
- Heartbeat: write a comment line (`:keepalive\n\n`) every 25 s to keep nginx/idle proxies from closing the connection. Stop after the terminal event.
- Implementation: use `ioredis` or the existing `redis` client (already a dep via `CacheClient`) in `subscribe` mode. Subscribe to `job:{taskId}`. On message, verify ownership, write SSE event, unsubscribe and end the response on terminal state. On client disconnect (`req.on('close')`), unsubscribe and clean up the Redis subscription. Do not leave orphaned subscriptions.

### nginx directives

Add a dedicated location in `m_sql_studio/nginx/nginx.conf`:

```nginx
location /api/v1/assignments/client-sql-code-run/status/ {
    proxy_pass http://api_backends;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Cookie $http_cookie;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 60s;
    chunked_transfer_encoding off;
}
```

Notes:
- `proxy_buffering off` — required for SSE; otherwise nginx buffers the response.
- `proxy_read_timeout 60s` — longer than the heartbeat interval (25 s) so an idle stream is not cut. Tune up if jobs routinely exceed 60 s (they do not today).
- `proxy_set_header Connection ''` — disables keep-alive to the upstream so the stream is not held open by nginx's own keep-alive pool.
- `chunked_transfer_encoding off` — SSE uses `Content-Type: text/event-stream`, not chunked.
- The location is a prefix match on `.../status/` so it covers both `/status/:taskId` (polling, unchanged) and `/status/:taskId/stream` (SSE). Polling requests still work because the same directives are compatible with normal HTTP responses.

### Client

- Replace `useGetJobStatusQuery` polling with a new hook `useJobStatusStream` that:
  1. Opens `new EventSource(`/api/v1/assignments/client-sql-code-run/status/${taskId}/stream`, { withCredentials: true })`.
  2. Listens for `event: job-status`, dispatches `executionCompleted` / `executionFailed` from the existing `executionSlice`.
  3. On `error` event (or if `EventSource` is not available in `window`), falls back to the existing `useGetJobStatusQuery` with `pollingInterval: 1000`. This is the polling fallback — the old code path stays intact and is the safety net.
  4. Closes the EventSource on unmount or when the terminal state is received.
- The existing `executionSlice` (`idle | running | polling | done | error`) is reused. Add a `streaming` phase if the UI needs to distinguish "connected to stream" from "polling" — but this is optional; `polling` phase can cover both.
- The existing `getJobStatus` RTK Query endpoint is kept for the fallback. Do not delete it.

### Sandbox worker change

In `m_sql_studio_sandbox/src/worker.ts`, after the existing `BullMQWorker.on('completed', ...)` and `BullMQWorker.on('failed', ...)` handlers, publish to Redis:

```ts
// after the existing completed/failed handlers
const redis = new Redis(envVars.REDIS_URL);
// in completed handler, after existing logic:
await redis.publish(`job:${job.id}`, JSON.stringify({ status: 'completed', result: job.returnvalue }));
// in failed handler, after existing logic:
await redis.publish(`job:${job.id}`, JSON.stringify({ status: 'failed', result: { success: false, error: job.failedReason } }));
// quit redis when worker closes (in cleanup)
```

Use a dedicated Redis connection for publishing (not the BullMQ connection — BullMQ needs its connection for job management). A lightweight `ioredis` or `redis` client publish-only connection is fine.

## Verification (via :8000)

1. Sign in, open an assignment, open browser DevTools → Network.
2. Run a query. A new request appears: `GET /api/v1/assignments/client-sql-code-run/status/:taskId/stream` (type `eventsource`). Status 200. Response tab shows the SSE frames.
3. When the job finishes, one `job-status` frame arrives with `{ "status": "completed", ... }` (or `"failed"`). The stream closes. The UI updates to Passed / Failed without any polling request.
4. While waiting, every ~25 s a `:keepalive` comment arrives (visible in the EventSource frame list).
5. Fallback test: in the browser console, `window.EventSource = undefined` before running. The client falls back to polling — `GET /status/:taskId` requests appear every 1 s.
6. Auth test: sign out in another tab, then run a query in the first tab. The stream request returns 401 (visible in DevTools). The client dispatches `executionFailed` with the auth error.
7. Owner test: user A runs a job, user B (non-admin) opens the stream URL for that taskId in a new tab → 403.
8. Reload the page mid-job: a new stream opens for the same taskId. The old one is closed by the browser. The server cleans up the orphaned subscription on `req.on('close')`.

## Out of scope

- WebSocket (slice 2 is SSE only; WebSocket is explicitly out of scope per SLICE2.md).
- Live multi-test progress (single terminal event per job).
- Replay of missed events (if the stream misses the message, polling fallback covers it).
- OAuth (out of scope per SLICE2.md).
- Redis Streams / consumer groups (plain pub/sub is enough for this scale).
