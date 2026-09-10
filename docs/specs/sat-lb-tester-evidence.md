# SAT-LB tester evidence (2026-09-10)

CTO mechanical proof after Hermes tester stall (empty log, pid dead, then judge `block --kind transient`).

## Live stack

- `GET http://127.0.0.1:8000/health` → 200, redis/mongodb/queue/sandbox ok
- Catalog `GET /api/v1/assignments?limit=1` → 200 (`E2E seed`)
- Client `GET http://127.0.0.1:3000/leaderboard` → 200 (SPA)
- Client asset `LeaderboardPage-C0JwkiTS.js` → 200
- API replicas same image SHA `79e30affe50b6e7f79fcf2c71776124953e6e4592dd726244817ddf92d0108b0`

## Ranking

Inserted two `userpasses` rows (3 vs 1) then:

`GET http://127.0.0.1:8000/api/v1/leaderboard` → 200

```json
{"total":2,"passes":[3,1],"sorted_desc":true}
```

Handles: `6aa225b2e71fd4a5a33ab9f2` (3), `6aa225b2e71fd4a5a33ab9f3` (1). Not the SQL puzzle table.

## Build gap closed

Engineer push did not `tsc` in Docker. Fixed:

- `UserProfile.findOne({ userId })` (typed query; PF model keys by `userId`)
- unused `res` in `optionalAuthMware` (`noUnusedParameters`)

`npx tsc --noEmit` 0; `vitest` leaderboard+user_pass 9/9. Image rebuild + recreate `api-gateway`, `api-gateway-b`, `client`.
