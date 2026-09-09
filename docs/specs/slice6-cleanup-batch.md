# Spec — Slice 6: batched sandbox schema cleanup

**Status:** locked for engineer (CTO wrote after architect looped with no artifact)
**Date:** 2026-09-09
**Follows:** reviewer HIGH on sequential `DROP SCHEMA` in slice 2 cleanup
**Workdir:** `m_sql_studio_sandbox` on `dev`
**Out of scope:** docker/compose, OAuth, nginx, new queues, extra BullMQ workers, gateway list API changes

## Problem

`CleanupExecutor.process` drops stale schemas **one after another**:

```52:66:m_sql_studio_sandbox/src/executor/cleanup/index.ts
    for (const schemaName of schemaNames) {
      if (!SCHEMA_NAME_RE.test(schemaName)) {
        logger.error({ schemaName }, "Refusing to drop unexpected schema!");
        continue;
      }

      try {
        // validated against SCHEMA_NAME_RE above — safe to interpolate.
        await pool.query(`DROP SCHEMA IF EXISTS "${schemaName}" CASCADE`);
        dropped.push(schemaName);
        logger.info({ schemaName }, "Dropped stale assignment schema.");
      } catch (err) {
        logger.error({ err, schemaName }, "Failed to drop stale schema!");
      }
    }
```

A large orphan list (failed seeds, TTL backlog) holds the cleanup job for `N * DROP` wall time on the **same** BullMQ worker that also runs SQL exec (`CONCURRENT_WORKERS_COUNT = 3` in `src/utils/constants/index.ts`). That is the sequential HIGH.

Admin pool is `PG_POOL_MAX = 5` (`src/db/index.ts` `adminClientInst`). Unbounded `Promise.all` of drops would stall the pool and SQL exec.

## Change (one file + tests)

Keep one cleanup job. Inside `CleanupExecutor.process`, drop with a **semaphore of 3** (leave 2 admin-pool slots for concurrent SQL/admin work).

1. Filter `schemaNames` with existing `SCHEMA_NAME_RE` first (unchanged refuse + log).
2. Run validated drops with at most **3** in flight.
   - No new dependency if a 12-line local limiter is enough (`active` counter + waiter queue). `p-limit` only if already in package.json (it is not required).
   - Still `DROP SCHEMA IF EXISTS "<name>" CASCADE` after the regex gate.
   - Per-schema try/catch: one failure does not abort the batch. Push successes onto `dropped`.
3. Existing remaining-schema count query stays **after** the batch.
4. Env optional: `SANDBOX_CLEANUP_CONCURRENCY` default `3`, clamp `1..PG_POOL_MAX-1` (never 5). If env plumbing is more than a few lines, hardcode `3` and document it.

Do **not**:

- Split one schema per BullMQ job
- Raise `PG_POOL_MAX` or `CONCURRENT_WORKERS_COUNT`
- Touch gateway `/internal/cleanup/old-schemas`
- Drop names that fail `SCHEMA_NAME_RE`

## Tests to add

File: `m_sql_studio_sandbox/src/executor/cleanup/__tests__/cleanup.test.ts`

Keep existing cases. Add:

1. **Concurrency cap** — gateway returns 8 valid names. `mockQuery` for `DROP SCHEMA` delays (~20ms) and records `inFlight` / `maxInFlight`. After `process()`, `maxInFlight <= 3` and `droppedCount === 8`.
2. **Partial failure** — 3 names; middle `DROP` rejects. Result `success: true`, `droppedCount === 2`, the other two names still dropped.
3. **Cap with rejects mixed in** — list includes one `public; DROP TABLE users;--` plus 4 valid names. Still `maxInFlight <= 3`, no SQL containing `DROP TABLE users`, `droppedCount === 4`.

Do not require a live Postgres for these unit tests.

## Stop

- Sequential `for await drop` is gone.
- Tests above pass (`vitest` in sandbox).
- Commit + push `origin/dev` on `m_sql_studio_sandbox` (and the spec file on `m_sql_studio` if still dirty). Never `.env`.
