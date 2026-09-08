# ADR 001 — Job status transport (polling vs push)

**Status:** accepted for slice 1 (keep polling; do not implement push)  
**Date:** 2026-09-08  
**Context:** Client `SqlEditor` POSTs execute, then RTK Query `useGetJobStatusQuery` with `pollingInterval: 1000` until BullMQ reports `completed` / `failed`.

## Options

| | Polling (current) | SSE | WebSocket |
|---|---|---|---|
| Fit | One short-lived job per submit | Server can push job terminal state | Bidirectional; overkill for “tell me when this job ends” |
| Infra | Already works through nginx + cookies + rate limits | Needs sticky-or-broadcast across **two** gateway replicas; nginx `proxy_buffering off`; extra open connections | Same replica/session problem; more client + auth surface |
| Auth | Cookie on each GET `/status/:taskId` | EventSource cookie/header quirks; must re-check owner on the stream | Must authenticate the upgrade |
| Cost on this stack | Extra GETs for ~1–5s jobs | Modest win; more moving parts behind new nginx LB | Highest complexity |

## Decision

Keep **HTTP polling** for this slice.

Grading jobs are seconds, not minutes. We just put two API replicas and an edge proxy in front; SSE/WebSocket would need a shared pub/sub (Redis is already there) and nginx streaming config we would not finish testing this slice.

Revisit SSE when: jobs routinely exceed ~10s, or we add live multi-test progress. Implementation sketch then: BullMQ worker publishes on Redis `job:{id}`, gateway `GET /status/:taskId/stream` (`text/event-stream`) subscribed to that channel, nginx `proxy_buffering off; proxy_read_timeout 60s`. Not built now.

## Lint notes (slice 1)

- **api-gateway `npm run lint`:** 0 errors; 3 warnings (unused `z`, `mockJob`, `beforeEach` in tests). ESLint 10 had no config; added `eslint.config.mjs`.
- **api-gateway `tsc --noEmit`:** clean.
- **api-gateway tests:** job/auth/assignment/logger 18/18; full suite 2 pre-existing fails (`env.test` invalid MONGO_URI accepted by zod; not this slice).
- **sandbox `tsc --noEmit`:** clean. No lint script.
- **client biome:** 0 a11y errors after `type="button"` on difficulty buttons. Remaining: nursery `useSortedClasses` warnings + formatter drift on existing files — not mass-reformatted.

## Live checks (2026-09-08)

- `:8000` is `nginx-edge`; two gateways; catalog GET `X-Cache-Status: MISS` then `HIT`; unauth execute/status/admin = 401.
