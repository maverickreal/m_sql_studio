# Corpus 1 Seed Evidence (`t_64a5e784`)

**Date:** 2026-09-09  
**Workdir:** `/Users/maverick/.hermes/profiles/swe/workspace/msql-studio`

---

## 1. Assignment Seed Count

- **`m_sql_studio/misc/seed.js` Count:** 25 assignments
- **MongoDB Seeded Assignments Count:** 54 assignments total in database (seeded and synced via `seed.js`)
- **Status:** PASS (`>= 25` assignments present and verified)

---

## 2. API Gateway Health Check

- **Endpoint:** `GET http://127.0.0.1:8000/health`
- **HTTP Code:** `200`
- **Health JSON:**
```json
{
  "status": "ok",
  "checks": {
    "redis": "ok",
    "mongodb": "ok",
    "queue": "ok",
    "sandbox_service": "ok",
    "sandbox_db": "ok"
  }
}
```

---

## 3. Admin Authentication

- **Endpoint:** `POST http://127.0.0.1:8000/api/auth/sign-in/email`
- **Payload:** `DEFAULT_ADMIN_EMAIL` and `DEFAULT_ADMIN_PASSWORD` from `.env` (secrets omitted)
- **HTTP Code:** `200`
- **Session Cookie:** Received and passed in subsequent requests.

---

## 4. Live Assignment Execution & Grading Proof

### A. Read-Easy Assignment Execution

- **Title:** `Pet Shelter: Dogs Ready for Adoption`
- **Assignment ID:** `6aa13aca43684b83a25e2568`
- **Mode:** `read`
- **Difficulty:** `easy`
- **User SQL:** `SELECT name, breed FROM dogs WHERE status = 'available' ORDER BY name;`
- **Execute Request:** `POST http://127.0.0.1:8000/api/v1/assignments/client-sql-code-run/execute`
- **Execute HTTP Code:** `202`
- **Task ID:** `75`
- **Poll Request:** `GET http://127.0.0.1:8000/api/v1/assignments/client-sql-code-run/status/75`
- **Poll HTTP Code:** `200`
- **Final Job Status:** `completed`
- **Grading Result:**
```json
{
  "status": "completed",
  "result": {
    "executionTimeMs": 1,
    "rowCount": 3,
    "columns": [
      "name",
      "breed"
    ],
    "rows": [
      {
        "name": "Bella",
        "breed": "Labrador"
      },
      {
        "name": "Coco",
        "breed": "Terrier"
      },
      {
        "name": "Luna",
        "breed": "Poodle"
      }
    ],
    "truncated": false,
    "success": true,
    "passed": true
  }
}
```

### B. Write Assignment Execution

- **Title:** `Library System: Outdated Books Cleanup`
- **Assignment ID:** `6aa13acae8d543cfb328f949`
- **Mode:** `write`
- **Difficulty:** `hard`
- **User SQL:** `DELETE FROM books WHERE publish_year < 1950;`
- **Execute Request:** `POST http://127.0.0.1:8000/api/v1/assignments/client-sql-code-run/execute`
- **Execute HTTP Code:** `202`
- **Task ID:** `76`
- **Poll Request:** `GET http://127.0.0.1:8000/api/v1/assignments/client-sql-code-run/status/76`
- **Poll HTTP Code:** `200`
- **Final Job Status:** `completed`
- **Grading Result:**
```json
{
  "status": "completed",
  "result": {
    "success": true,
    "rows": [],
    "columns": [],
    "rowCount": 2,
    "truncated": false,
    "executionTimeMs": 0,
    "passed": true
  }
}
```

---

## 5. Summary Matrix

| Metric / Check | Value / Result |
|---|---|
| Seed.js Assignment Count | 25 (`>= 25`) |
| Seed Mongo Verification | 54 total assignments stored and ready in MongoDB |
| Health Check HTTP Code | `200` |
| Admin Auth Sign-in HTTP Code | `200` |
| Read-Easy Assignment ID | `6aa13aca43684b83a25e2568` |
| Read-Easy Exec / Poll HTTP | `202` / `200` |
| Read-Easy Final Status | `completed` (`passed: true`) |
| Write Assignment ID | `6aa13acae8d543cfb328f949` |
| Write Exec / Poll HTTP | `202` / `200` |
| Write Final Status | `completed` (`passed: true`) |
