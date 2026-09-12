# Problem Bank Catalog C3 Sync & Verification Evidence

## Summary
- **Live Unique Titles**: 203 (178 problem YAMLs synced + 25 initial seed assignments). All 203 have `pgSchemaReady: true`.
- **Schema Families**: 6 families (`commerce`, `content`, `education`, `finance`, `hr`, `ops-logistics`), satisfying `>=4`.
- **Write-Mode Ratio**: 12 write-mode assignments out of 203 = **5.91%** (satisfying `<=20%`).
- **Validation**: `node scripts/validate-problems.mjs` validated all 178 problem YAML files with zero errors.
- **Gold Diffs**: `scripts/generate-sandbox-gold-diff.mjs` executed 178/178 problems against PostgreSQL with 0 failures.
- **API Grading Verification**: Graded 3 new-domain read problems through `http://localhost:8000/api/v1/assignments/client-sql-code-run/execute` and `/status/:taskId`, all returning `passed: true`, `success: true`, and matching their `.gold` output.
- **Git Repositories**:
  - `m_sql_studio_problems` on branch `main` committed & pushed to `origin/main`.
  - `m_sql_studio` on branch `dev` committed & pushed to `origin/dev`.

---

## 1. Live Catalog Count & Distribution

Querying `GET http://localhost:8000/api/v1/assignments?limit=200`:
```json
{
  "total": 203,
  "count": 100,
  "page": 1,
  "totalPages": 3
}
```

Mongo DB Verification (`m_sql_studio` database):
```javascript
Total live assignments: 203
Unique live titles: 203
Write mode count: 12 (5.91%)
Read mode count: 191 (94.09%)
Schema families: 6 ['commerce', 'content', 'education', 'finance', 'hr', 'ops-logistics']
Assignments with pgSchemaReady=true: 203
Assignments with pgSchemaReady=false: 0
```

---

## 2. Validation & Gold-Diff Results

### `validate-problems.mjs`
```
node scripts/validate-problems.mjs
✅ Successfully validated 178 problem file(s).
```

### `npm test`
```
npm test
1..25
# tests 25
# suites 0
# pass 25
# fail 0
```

### `generate-sandbox-gold-diff.mjs`
```
========================================
Gold generation complete
Total: 178  Passed: 178  Failed: 0  Skipped: 0
Output: m_sql_studio_problems/gold/
```

---

## 3. End-to-End Grade Verification via API (`:8000`)

### Test Case 1: [content] Draft articles
- **Assignment ID**: `6aa4f36e2109bb531ca003a2`
- **SQL**: `SELECT title FROM articles WHERE status = 'draft' ORDER BY title`
- **Task ID**: `347`
- **Status**: `completed`
- **Result**: `passed: true`, `success: true`, `rowCount: 2`
- **Output Rows**:
  - `Data Modeling Basics`
  - `PostgreSQL vs MySQL`
- **Gold Match**: Verified matching `gold/content__draft-articles.gold`.

### Test Case 2: [commerce] Electronics products
- **Assignment ID**: `6aa4f36e2109bb531ca000f5`
- **SQL**: `SELECT name FROM products WHERE category = 'Electronics' ORDER BY name`
- **Task ID**: `348`
- **Status**: `completed`
- **Result**: `passed: true`, `success: true`, `rowCount: 3`
- **Output Rows**:
  - `Laptop Pro`
  - `Monitor 27"`
  - `Wireless Mouse`
- **Gold Match**: Verified matching `gold/commerce__electronics-products.gold`.

### Test Case 3: [education] CS Majors
- **Assignment ID**: `6aa4f36e2109bb531ca005e6`
- **SQL**: `SELECT name FROM students WHERE major = 'CS' ORDER BY name`
- **Task ID**: `349`
- **Status**: `completed`
- **Result**: `passed: true`, `success: true`, `rowCount: 3`
- **Output Rows**:
  - `Mina Patel`
  - `Nora Klein`
  - `Omar Haddad`
- **Gold Match**: Verified matching `gold/education__cs-majors.gold`.
