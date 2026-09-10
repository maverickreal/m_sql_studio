# Slice LB — Product Leaderboard

**Parent:** `SATURATION.md` Slice LB
**Workdir:** `/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/`
**Branches:** `dev` on `m_sql_studio_api_gateway` and `m_sql_studio_client`
**Stack unchanged.** No new services, no new infra, no spend.

## Scope

Build a **product leaderboard** that ranks users by real assignment passes — not a SQL puzzle, not a synthetic score. The ranking signal is `passed: boolean` from the existing sandbox executor's job result.

**What users see:** A public `/leaderboard` page showing a ranked list of users sorted by total distinct-assignment passes, descending. Each row shows a handle and a pass count.

**What the leaderboard is NOT:**
- A SQL challenge or meta-puzzle
- A per-assignment leaderboard
- Real-time SSE feed (polling is fine)
- A moderation or admin tool

### Rankings Source of Truth

The ranking signal already exists: every `UserSqlCodeRun` job produces `passed: boolean` in its result (see `m_sql_studio_sandbox/src/executor/user/index.ts`). The gateway already knows the `userId` on each job. The leaderboard simply **materializes** these pass events into a queryable, aggregated view.

---

## Data Layer (Gateway)

### New Model — `user_passes`

Mongo collection: `user_passes`

```ts
{
  userId: string,        // auth user id (from job payload)
  assignmentId: string,  // assignment that was passed
  taskId: string,        // BullMQ job id — idempotency key
  passedAt: Date,
}
```

**Indexes:**
- `{ taskId: 1 }` unique — prevents double-counting if the interception logic fires more than once for the same job.
- `{ userId: 1, assignmentId: 1 }` — supports "has this user already passed this assignment" checks.
- `{ userId: 1 }` — supports per-user aggregation.

**Rule:** A `taskId` is written at most once. A user can pass an assignment many times (different jobs), but the unique index on `{ userId, assignmentId }` can be added later if dedup is needed. For now, count **all** passes per user — repeat passes of the same assignment still count toward the total. (This keeps the model simple and avoids race conditions on idempotency.)

> **Design note:** We count total passes, not distinct assignments. This is intentional — it rewards persistence and re-engagement. If product later wants distinct-assignment ranking, the aggregation pipeline can switch from `$count` to `$addToSet` + `$size`. The data model supports both.

### Files

| File | Purpose |
|------|---------|
| `src/data/db/models/user_pass/index.ts` | Mongoose model + zod schema |
| `src/services/pass_recorder/index.ts` | Service: record a pass when a job completes |
| `src/controllers/leaderboard/index.ts` | Controller: aggregate and return rankings |
| `src/routes/api/v1/leaderboard/index.ts` | Router: `GET /api/v1/leaderboard` |

---

## Pass Recording Mechanism

When a SQL execution job completes with `passed: true`, the gateway records a pass for the user. The interception point is the existing `getJobStatus` flow — the gateway already calls `TaskQueueClient.getStatus(taskId)` and already has access to `ownerUserId`.

### Recording Flow

1. Client polls `GET /api/v1/assignments/client-sql-code-run/status/:taskId` (existing endpoint).
2. Gateway's `getJobStatus` handler calls `TaskQueueClient.getStatus(taskId)`.
3. If the returned status is `"completed"` AND `result?.passed === true`, the handler calls `PassRecorder.recordPass({ userId, assignmentId, taskId })`.
4. `PassRecorder` does an upsert-or-ignore into `user_passes` using the unique `taskId` index. Duplicate key errors are caught and ignored (idempotent).
5. The job status response is returned to the client unchanged.

**Why this point:**
- No new infrastructure — reuses existing status polling.
- No client trust required — the server decides when a pass happened based on the real job result.
- Idempotent by construction — the unique taskId index prevents double counts even if the client polls the same completed job many times.

### Service: `PassRecorder`

```ts
class PassRecorder {
  static async recordPass(data: {
    userId: string;
    assignmentId: string;
    taskId: string;
  }): Promise<void> {
    try {
      await UserPass.create({
        userId: data.userId,
        assignmentId: data.assignmentId,
        taskId: data.taskId,
        passedAt: new Date(),
      });
    } catch (err) {
      // Duplicate taskId → already recorded. Ignore.
      if (err.code === 11000) return;
      throw err;
    }
  }
}
```

**Integration in `controllers/job/index.ts`:**
After `getStatus` returns, before sending the response:

```ts
if (
  jobStatus.status === "completed" &&
  jobStatus.result?.passed === true
) {
  await PassRecorder.recordPass({
    userId: ownerUserId,
    assignmentId: jobStatus.result.assignmentId,  // if exposed
    taskId,
  });
}
```

> **Note:** The current `JobStatusResponse` in `services/job_queue/index.ts` returns `result` as `unknown`. The `result` shape from the sandbox is `{ success, passed, ... }`. The handler will need to type-narrow `result` and extract `assignmentId` if it's available in the job data. If `assignmentId` is not in the result, the handler can read it from `task.data` (the original `SqlJobPayload`) — the BullMQ `getJob` call already loads `task.data`.

### Alternative Considered (Rejected)

| Option | Why rejected |
|--------|-------------|
| Client calls `POST /leaderboard/pass` when it sees `passed: true` | Forgeable — client could spam passes. |
| Sandbox worker writes directly to Mongo | Breaks isolation — sandbox has no Mongo access by design. |
| Gateway polls all completed jobs in a background loop | Overkill — the status endpoint already has the data. |

---

## Leaderboard API

### `GET /api/v1/leaderboard`

**Auth:** None (public read).

**Query params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | number | 50 | Max rows to return (capped at 100) |
| `offset` | number | 0 | Pagination offset |

**Response:**

```ts
{
  entries: Array<{
    userId: string;
    displayName: string | null;  // from UserProfile if Slice PF landed, else null
    passes: number;
    lastPassAt: string;          // ISO
  }>;
  total: number;                 // total number of ranked users
  generatedAt: string;           // ISO, server time
}
```

**Aggregation pipeline:**

1. `$group` by `userId` → `{ passes: { $sum: 1 }, lastPassAt: { $max: "$passedAt" } }`
2. `$sort` by `passes` descending, then `lastPassAt` ascending (tiebreak: earlier achiever ranks higher)
3. `$skip` + `$limit`
4. (Optional) `$lookup` to `user_profiles` for `displayName` if the collection exists. If Slice PF hasn't landed yet, skip the lookup — return `displayName: null` and the client shows a truncated `userId` instead.

**Tiebreak rule:** Same pass count → the user who reached that count **first** ranks higher (earlier `lastPassAt`). This rewards early adopters and avoids arbitrary tiebreaks.

**Caching:** `Cache-Control: public, max-age=15` (same as assignments catalog). The leaderboard is eventually consistent — a pass shows up within 15 seconds at worst.

---

## Client (SPA) — `m_sql_studio_client`

### New Files

| File | Purpose |
|------|---------|
| `src/features/leaderboard/LeaderboardPage.tsx` | Main leaderboard page |
| `src/features/leaderboard/index.ts` | Exports |

### RTK Query Extension

Add to `src/store/api.ts`:

```ts
getLeaderboard: builder.query<
  { entries: LeaderboardEntry[]; total: number; generatedAt: string },
  { limit?: number; offset?: number }
>({
  query: ({ limit = 50, offset = 0 }) =>
    `/api/v1/leaderboard?limit=${limit}&offset=${offset}`,
  providesTags: ["Leaderboard"],
  // Poll every 15s to stay fresh without SSE
  keepUnusedDataFor: 15,
}),
```

### Type

```ts
export interface LeaderboardEntry {
  userId: string;
  displayName: string | null;
  passes: number;
  lastPassAt: string;
}
```

### Route

Add to `src/app/router.tsx`:

```ts
{
  path: "/leaderboard",
  lazy: () => import("@/features/leaderboard/LeaderboardPage"),
}
```

### Leaderboard Page UI

```
┌─────────────────────────────────────────────────────────────┐
│  Leaderboard                                               │
│  Ranked by real assignment passes                          │
│                                                             │
│  #    Handle                         Passes    Last Active  │
│  1    alice                          12        2h ago      │
│  2    bob                            8         1d ago      │
│  3    u_3f8a2c...                    5         3d ago      │
│  ...                                                        │
│                                                             │
│  [Load more]                                               │
└─────────────────────────────────────────────────────────────┘
```

- **Rank:** Position in the sorted list (1-indexed, respects offset).
- **Handle:** `displayName` from UserProfile if available. Otherwise, truncate `userId` to `u_${slice(0, 6)}...`.
- **Passes:** Total pass count.
- **Last Active:** Human-readable relative time from `lastPassAt`.
- **Pagination:** "Load more" button increments offset (infinite scroll or button).
- **Styling:** Reuse existing `Table` / `Badge` components. Tailwind utility classes.
- **Empty state:** "No passes yet. Be the first to solve an assignment!"
- **Error state:** Show error message, retry button.

### Navbar

No navbar change — `/leaderboard` is accessible via direct URL. (Adding it to the nav is a future enhancement, out of scope.)

---

## Verification Commands

```bash
# Gateway
cd m_sql_studio_api_gateway && npm test
# → user_pass model tests: create, unique taskId, aggregation

# Client
cd m_sql_studio_client && npm run build
# → typecheck passes
cd m_sql_studio_client && npm test
# → LeaderboardPage renders, table shows rows, load-more works

# Live verification (requires dev stack running)
# 1. Sign up as user A, pass 2 assignments
# 2. Sign up as user B, pass 1 assignment
# 3. Open /leaderboard → A ranks above B (2 > 1)
# 4. Pass another assignment as B → B moves to 2, tiebreak by lastPassAt
# 5. Duplicate job status calls do not inflate counts (check user_passes count)
```

### Manual Test Matrix

| Scenario | Expected |
|----------|----------|
| User passes 1 assignment | Appears on leaderboard with passes=1 |
| User passes 3 assignments | passes=3 |
| Two users, different pass counts | Higher count ranks first |
| Two users, same pass count | Earlier achiever ranks first |
| Same job polled 10 times | user_passes has 1 document (idempotent) |
| No assignments solved yet | Empty state shown |
| UserProfile exists for a user | displayName shown |
| UserProfile missing | Truncated userId shown |
| Pagination (limit=1, offset=0) | Returns top 1, total reflects all |

---

## Tests to Add (Gateway)

File: `src/__tests__/user_pass.test.ts`

1. **Model:** `UserPass.create()` with valid data — document saved.
2. **Unique taskId:** Second insert with same `taskId` throws duplicate key (code 11000).
3. **PassRecorder.recordPass()** — inserts on first call, no-op on second call with same taskId.
4. **Aggregation pipeline** — given 3 users with different pass counts, returns sorted by passes desc, with correct totals.

File: `src/__tests__/leaderboard.test.ts`

1. `GET /api/v1/leaderboard` — empty DB returns `{ entries: [], total: 0 }`.
2. `GET /api/v1/leaderboard` — after inserting passes, returns sorted entries.
3. `GET /api/v1/leaderboard?limit=1&offset=0` — returns top 1, total=all.
4. `GET /api/v1/leaderboard` — tiebreak by lastPassAt when passes are equal.

---

## Tests to Add (Client)

File: `src/features/leaderboard/LeaderboardPage.test.tsx`

1. **Empty state** — renders "No passes yet" message.
2. **Populated** — renders rows with rank, handle, passes, last active.
3. **Pagination** — "Load more" button calls API with incremented offset.
4. **Handle fallback** — when displayName is null, shows truncated userId.

---

## Dependencies

- Existing `TaskQueueClient` (BullMQ) — job status and pass detection.
- Existing `SqlJobPayload` — carries `userId` and `assignmentId` into the job.
- Existing `UserSqlExecJobResult` — carries `passed: boolean` from sandbox.
- Optional: `UserProfile` model (from Slice PF) — only if landed. If not, skip the lookup.

---

## Out of Scope

- Real-time SSE for leaderboard updates (15s polling is enough).
- Per-assignment leaderboards.
- Score-based ranking beyond pass count.
- Admin moderation / banning from leaderboard.
- Historical leaderboard snapshots over time.
- Profile avatars on leaderboard rows.
- Adding `/leaderboard` to the navbar (future enhancement).

---

## Finite Done List

### Gateway (`m_sql_studio_api_gateway`, branch `dev`)

| # | Task | Acceptance |
|---|------|------------|
| 1 | Create `UserPass` model + unique taskId index | Model compiles; unique index on `taskId` |
| 2 | Create `PassRecorder` service | `recordPass()` inserts once, idempotent on retry |
| 3 | Intercept `getJobStatus` to call `PassRecorder` when `passed: true` | Pass recorded on completed job with `passed: true` |
| 4 | Create `leaderboard` controller with aggregation pipeline | Returns sorted entries, correct totals |
| 5 | Create `routes/api/v1/leaderboard/index.ts` | `GET /api/v1/leaderboard` mounted |
| 6 | Wire router in `src/routes/api/v1/index.ts` | `router.use("/leaderboard", leaderboardRouter)` |
| 7 | Write `src/__tests__/user_pass.test.ts` | All 4 test groups pass |
| 8 | Write `src/__tests__/leaderboard.test.ts` | All 4 test groups pass |
| 9 | `npm test` green | No regressions |

### Client (`m_sql_studio_client`, branch `dev`)

| # | Task | Acceptance |
|---|------|------------|
| 1 | Add `LeaderboardEntry` type + RTK Query endpoint | Hook exported |
| 2 | Create `LeaderboardPage.tsx` | Table renders, pagination works |
| 3 | Add route `/leaderboard` in `src/app/router.tsx` | Page accessible at `/leaderboard` |
| 4 | Write `LeaderboardPage.test.tsx` | Component tests pass |
| 5 | `npm run build` + `npm test` green | No type errors, tests pass |

### Cross-cutting

- Commit + push `origin/dev` on both repos.
- Never commit `.env`.
- Documentation: one paragraph in `m_sql_studio/README.md` confirming `GET /api/v1/leaderboard`.

---

## Stop Condition

Two users with different pass counts sort correctly on `/leaderboard` in the running dev stack. No product code written beyond the spec's done list.
