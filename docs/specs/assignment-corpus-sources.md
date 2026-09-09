# Assignment Corpus Sources

> Evidence catalog of importable SQL problem sets that fit the MSqlStudio
> assignment schema (`m_sql_studio_problems/schemas/problem-v1.json`).
>
> Schema fields: `title`, `description`, `difficulty`, `mode` (read|write),
> `sampleInput`, `sampleOutput`, `solutionSql`, `validationSql`, `initSql`,
> `orderMatters`.
>
> Rules: license-clean only. No login scrape. No LeetCode/Hackerrank dumps.
> HITL before any third-party text lands on GitHub. Catalog != dump — inclusion
> here is a flag that a source *exists* and has a license we can read, not a
> grant to republish its text.

## Source catalog

### 1. NUKnightLab/sql-mysteries

- **URL**: https://github.com/NUKnightLab/sql-mysteries
- **License**: MIT (code), CC BY-SA 4.0 (text/content)
- **Approx count**: 1 mystery (multi-step, ~15-20 clues)
- **Has init SQL?**: Yes — `sql-murder-mystery.db` is a self-contained SQLite DB with schema + data.
- **Has expected result/solution?**: Yes — `prompt_beginner.pdf`, `prompt_experienced.pdf`, `walkthrough.html`, and a `solution` table in the DB.
- **ToS / ban risk**: Low. MIT code + CC BY-SA content. Explicitly open.
- **$0?**: Yes.
- **Field map**:
  - `title` → from prompt PDFs
  - `description` → from prompt PDFs
  - `difficulty` → easy (beginner) / medium (experienced)
  - `mode` → read
  - `sampleInput` → DB schema (table DDL)
  - `sampleOutput` → expected query results from walkthrough
  - `solutionSql` → walkthrough SQL
  - `validationSql` → `INSERT INTO solution VALUES (...)` + `SELECT value FROM solution`
  - `initSql` → reconstruct from `sql-murder-mystery.db` (SQLite → PG DDL conversion needed)
  - `orderMatters` → false
- **Notes**: Single mystery, but each clue maps to a standalone query. Good seed
  for "read" mode. SQLite → PostgreSQL DDL conversion required.

### 2. XD-DENG/SQL-exercise

- **URL**: https://github.com/XD-DENG/SQL-exercise
- **License**: CC BY-SA 3.0
- **Approx count**: 10 exercises (SQL_exercise_01 through SQL_exercise_10), each with multiple questions
- **Has init SQL?**: Yes — `*_build_schema.sql` per exercise.
- **Has expected result/solution?**: Yes — `*_questions_and_solutions.sql` per exercise.
- **ToS / ban risk**: Low. CC BY-SA 3.0, explicitly open.
- **$0?**: Yes.
- **Field map**:
  - `title` → exercise folder names
  - `description` → from questions SQL files
  - `difficulty` → easy → medium (progressive)
  - `mode` → read (mostly SELECT queries)
  - `sampleInput` → schema figures + build_schema.sql
  - `sampleOutput` → from solutions SQL
  - `solutionSql` → `*_questions_and_solutions.sql`
  - `validationSql` → derive from expected result sets in solutions
  - `initSql` → `*_build_schema.sql`
  - `orderMatters` → false (most)
- **Notes**: Derived from Wikibook "SQL Exercises". CC BY-SA means any
  republished text must carry the same license — HITL required before GitHub push.

### 3. zichongkao/selectstarsql

- **URL**: https://github.com/zichongkao/selectstarsql
- **License**: CC BY-SA 4.0 (prose), CC0 (code and datasets)
- **Approx count**: 5 chapters with multiple interactive exercises each
- **Has init SQL?**: Yes — datasets in `/data` directory.
- **Has expected result/solution?**: Yes — interactive exercises with expected outputs.
- **ToS / ban risk**: Low. CC0 datasets + CC BY-SA prose. Explicitly open.
- **$0?**: Yes.
- **Field map**:
  - `title` → chapter/section titles
  - `description` → chapter prose
  - `difficulty` → easy → medium
  - `mode` → read
  - `sampleInput` → datasets in `/data`
  - `sampleOutput` → from interactive exercise definitions
  - `solutionSql` → embedded in exercise logic
  - `validationSql` → derive from expected outputs
  - `initSql` → reconstruct from datasets
  - `orderMatters` → false
- **Notes**: Datasets are CC0 (public domain) — safest for republishing data.
  Prose is CC BY-SA 4.0 — attribution + share-alike required.

### 4. jadebono/hundred_sql_exercises

- **URL**: https://github.com/jadebono/hundred_sql_exercises
- **License**: MIT
- **Approx count**: 100 exercises
- **Has init SQL?**: No — assumes HR schema (Oracle/MySQL standard). No init files provided.
- **Has expected result/solution?**: Yes — solutions embedded in exercise markdown.
- **ToS / ban risk**: Low. MIT license, explicitly open.
- **$0?**: Yes.
- **Field map**:
  - `title` → exercise titles in markdown
  - `description` → exercise descriptions
  - `difficulty` → easy → medium (progressive)
  - `mode` → read + write (includes INSERT/UPDATE/DELETE exercises)
  - `sampleInput` → HR schema (must be reconstructed)
  - `sampleOutput` → from solutions
  - `solutionSql` → in markdown
  - `validationSql` → derive from expected results
  - `initSql` → must build HR schema from scratch
  - `orderMatters` → false (most)
- **Notes**: MIT is the most permissive — can republish with attribution.
  Largest count (100 exercises). Covers both read and write modes. HR schema
  must be authored separately (not provided in repo).

### 5. eirkostop/SQL-Northwind-exercises

- **URL**: https://github.com/eirkostop/SQL-Northwind-exercises
- **License**: MIT
- **Approx count**: 3 sets (~30+ exercises total)
- **Has init SQL?**: No — assumes Northwind database (separate download).
- **Has expected result/solution?**: Yes — `.sql` answer files for each set.
- **ToS / ban risk**: Low. MIT license, explicitly open.
- **$0?**: Yes.
- **Field map**:
  - `title` → exercise names
  - `description` → exercise questions (PDF)
  - `difficulty` → easy → medium → hard
  - `mode` → read + write (includes INSERT/UPDATE/DELETE)
  - `sampleInput` → Northwind schema
  - `sampleOutput` → from answer SQL files
  - `solutionSql` → `*.sql` answer files
  - `validationSql` → derive from expected row counts in questions
  - `initSql` → Northwind DDL (must source separately)
  - `orderMatters` → false (most)
- **Notes**: MIT. Northwind is a widely-available sample DB (Microsoft origin,
  public domain). Covers read + write modes. Good difficulty range.

### 6. learner-next/sql-challenge

- **URL**: https://github.com/learner-next/sql-challenge
- **License**: MIT
- **Approx count**: ~30+ exercises (CRUD categories)
- **Has init SQL?**: Yes — exercises include table creation + data.
- **Has expected result/solution?**: Yes — built into interactive web UI.
- **ToS / ban risk**: Low. MIT license, explicitly open.
- **$0?**: Yes.
- **Field map**:
  - `title` → exercise names
  - `description` → exercise prompts
  - `difficulty` → easy → medium
  - `mode` → read + write (full CRUD)
  - `sampleInput` → from exercise definitions
  - `sampleOutput` → from interactive grader
  - `solutionSql` → embedded in app logic
  - `validationSql` → from grader logic
  - `initSql` → from exercise definitions
  - `orderMatters` → varies
- **Notes**: MIT. Full CRUD coverage (create, read, update, delete). Interactive
  web app with built-in grader — good reference for validation patterns.

### 7. codedex-io/sql-101

- **URL**: https://github.com/codedex-io/sql-101
- **License**: MIT
- **Approx count**: 21 exercises
- **Has init SQL?**: Yes — each `.sql` file includes schema + data.
- **Has expected result/solution?**: Yes — solutions in `.sql` files.
- **ToS / ban risk**: Low. MIT license, explicitly open.
- **$0?**: Yes.
- **Field map**:
  - `title` → file names (e.g., `streaming_wars.sql`, `rotten_tomatoes.sql`)
  - `description` → from exercise context
  - `difficulty` → easy
  - `mode` → read + write
  - `sampleInput` → from SQL files
  - `sampleOutput` → from solutions
  - `solutionSql` → in `.sql` files
  - `validationSql` → derive from expected outputs
  - `initSql` → in `.sql` files
  - `orderMatters` → false (most)
- **Notes**: MIT. Beginner-friendly. Real-world themed datasets (streaming wars,
  rotten tomatoes, billboard hot 100, video games).

### 8. s-shemmee/SQL-101

- **URL**: https://github.com/s-shemmee/SQL-101
- **License**: MIT
- **Approx count**: ~30+ exercises across 14 chapters
- **Has init SQL?**: Yes — examples embedded in lessons.
- **Has expected result/solution?**: Yes — exercises with solutions.
- **ToS / ban risk**: Low. MIT license, explicitly open.
- **$0?**: Yes.
- **Field map**:
  - `title` → chapter/section titles
  - `description` → lesson prose
  - `difficulty` → easy → medium
  - `mode` → read + write
  - `sampleInput` → from lesson examples
  - `sampleOutput` → from exercise solutions
  - `solutionSql` → in exercises
  - `validationSql` → derive from expected results
  - `initSql` → from lesson examples
  - `orderMatters` → false (most)
- **Notes**: MIT. Comprehensive beginner-to-intermediate coverage. Good for
  seeding foundational exercises.

### 9. shinbatsu/sql-ex

- **URL**: https://github.com/shinbatsu/sql-ex
- **License**: MIT
- **Approx count**: 150+ exercises
- **Has init SQL?**: No — assumes SQL-EX platform schemas.
- **Has expected result/solution?**: Yes — each `.sql` file is a solution.
- **ToS / ban risk**: Low. MIT license, explicitly open.
- **$0?**: Yes.
- **Field map**:
  - `title` → file names
  - `description` → from SQL-EX platform (not in repo)
  - `difficulty` → easy → medium → hard
  - `mode` → read
  - `sampleInput` → must reconstruct from SQL-EX platform schemas
  - `sampleOutput` → derive from solution SQL
  - `solutionSql` → in `.sql` files
  - `validationSql` → derive from solutions
  - `initSql` → must source from SQL-EX platform
  - `orderMatters` → false (most)
- **Notes**: MIT. Largest count (150+). Solutions only — problem descriptions
  live on the SQL-EX platform (separate ToS). Use solutions as reference, but
  problem text must be re-authored or licensed separately.

### 10. LeetCode (SQL 50 / SQL Study Plans)

- **URL**: https://leetcode.com/studyplan/top-sql-50/
- **License**: Proprietary — LeetCode ToS applies. Content is NOT open source.
- **Approx count**: 50+ SQL problems (SQL 50 plan), 100+ total SQL problems
- **Has init SQL?**: Yes — each problem provides schema + sample data.
- **Has expected result/solution?**: Yes — expected output shown; community solutions exist.
- **ToS / ban risk**: **HIGH**. LeetCode ToS prohibits scraping, redistribution,
  and derivative works. Automated scraping = ban risk. Manual copy = gray area.
- **$0?**: Partial — free tier has limits; full access requires subscription.
- **Field map**:
  - `title` → problem titles
  - `description` → problem statements
  - `difficulty` → easy / medium / hard
  - `mode` → read
  - `sampleInput` → from problem schema
  - `sampleOutput` → from problem examples
  - `solutionSql` → community solutions (license unclear)
  - `validationSql` → LeetCode's internal grader (not accessible)
  - `initSql` → from problem schema
  - `orderMatters` → varies
- **Notes**: **Catalog flag only — NOT a dump source.** LeetCode content is
  proprietary. Do NOT scrape, bulk-copy, or republish. Useful as a reference
  for problem patterns (e.g., "write a query that finds Nth highest salary"),
  but problem text must be re-authored from scratch. HITL + legal review
  required before any LeetCode-derived content lands in the repo.

### 11. HackerRank (SQL Domain)

- **URL**: https://www.hackerrank.com/domains/sql
- **License**: Proprietary — HackerRank ToS applies. Content is NOT open source.
- **Approx count**: 100+ SQL problems across sub-domains
- **Has init SQL?**: Yes — each problem provides schema.
- **Has expected result/solution?**: Yes — expected output shown.
- **ToS / ban risk**: **HIGH**. HackerRank ToS prohibits scraping,
  redistribution, and commercial use without permission.
- **$0?**: Partial — free tier has limits.
- **Field map**:
  - `title` → problem titles
  - `description` → problem statements
  - `difficulty` → easy / medium / hard
  - `mode` → read + write
  - `sampleInput` → from problem schema
  - `sampleOutput` → from problem examples
  - `solutionSql` → community solutions (license unclear)
  - `validationSql` → HackerRank's internal grader (not accessible)
  - `initSql` → from problem schema
  - `orderMatters` → varies
- **Notes**: **Catalog flag only — NOT a dump source.** Same treatment as
  LeetCode. Useful as a pattern reference only. Do NOT scrape or republish.
  HITL + legal review required.

### 12. PGExercises (pgexercises.com)

- **URL**: https://pgexercises.com/
- **License**: **Unclear / not explicitly open.** No LICENSE file found.
  Site states "PostgreSQL Exercises was made by Alisdair Owens" but does not
  specify a content license.
- **Approx count**: ~80 exercises across 7 categories
- **Has init SQL?**: Yes — single dataset (club schema) with provided schema.
- **Has expected result/solution?**: Yes — answers shown on site.
- **ToS / ban risk**: **Medium.** No explicit open license found. Content is
  publicly viewable but redistribution rights are unclear.
- **$0?**: Yes.
- **Field map**:
  - `title` → exercise titles
  - `description` → exercise questions
  - `difficulty` → easy → medium → hard
  - `mode` → read + write (includes UPDATE/DELETE exercises)
  - `sampleInput` → club schema
  - `sampleOutput` → from answers on site
  - `solutionSql` → from answers on site
  - `validationSql` → derive from expected results
  - `initSql` → club schema (must reconstruct)
  - `orderMatters` → false (most)
- **Notes**: **HITL required before use.** No explicit open license. Contact
  author (Alisdair Owens) for clarification, or treat as pattern reference only.
  PostgreSQL-specific (good fit for MSqlStudio's PG backend).

---

## Recommendations: 2 sources to seed locally

After reviewing the catalog, these two sources are the best candidates for
**local seeding without republishing** (i.e., you can load the problems into
your private MSqlStudio instance for personal/team use — just don't push the
third-party text to a public GitHub repo without HITL):

### Recommendation 1: jadebono/hundred_sql_exercises (MIT, 100 exercises)

- **Why**: MIT license is the most permissive. 100 exercises = highest volume.
  Covers both read and write modes. Progressive difficulty.
- **Caveat**: No init SQL provided — you must author the HR schema yourself.
  Solutions are embedded in markdown (easy to parse).
- **Seeding approach**: Author a standard HR schema (employees, departments,
  jobs, etc.), then map each exercise's question + solution onto the
  problem-v1 schema. All 100 can be loaded locally.

### Recommendation 2: eirkostop/SQL-Northwind-exercises (MIT, ~30+ exercises)

- **Why**: MIT license. Northwind is a well-known, public-domain sample
  database (Microsoft origin). Covers read + write modes. Three difficulty
  tiers. Solutions are clean SQL files.
- **Caveat**: No init SQL provided — you must source/create the Northwind
  DDL separately (widely available online).
- **Seeding approach**: Create the Northwind schema once, then map each
  exercise set onto the problem-v1 schema. All three sets can be loaded locally.

### Why not the others?

- **sql-mysteries / selectstarsql / SQL-exercise**: CC BY-SA — share-alike
  clause means any republished text must carry the same license. Fine for
  private use, but requires HITL before any public GitHub push.
- **LeetCode / HackerRank**: Proprietary — do NOT seed locally from these.
  Pattern reference only.
- **PGExercises**: No explicit license — HITL required before any use.
- **codedex-io / s-shemmee / learner-next / shinbatsu**: MIT, good backups
  but lower volume or require more reconstruction work.

---

## Field map summary

| Source                  | License     | Count | Init SQL | Solution | Read/Write | ToS Risk | $0 |
|-------------------------|-------------|-------|----------|----------|------------|----------|----|
| sql-mysteries           | MIT+CCBYSA  | 1     | Yes      | Yes      | read       | Low      | Y  |
| SQL-exercise            | CC BY-SA 3.0| ~10   | Yes      | Yes      | read       | Low      | Y  |
| selectstarsql           | CC0+CCBYSA  | ~20   | Yes      | Yes      | read       | Low      | Y  |
| hundred_sql_exercises   | MIT         | 100   | No       | Yes      | read+write | Low      | Y  |
| SQL-Northwind-exercises | MIT         | ~30   | No       | Yes      | read+write | Low      | Y  |
| sql-challenge           | MIT         | ~30   | Yes      | Yes      | read+write | Low      | Y  |
| codedex-io/sql-101      | MIT         | 21    | Yes      | Yes      | read+write | Low      | Y  |
| s-shemmee/SQL-101       | MIT         | ~30   | Yes      | Yes      | read+write | Low      | Y  |
| shinbatsu/sql-ex        | MIT         | 150+  | No       | Yes      | read       | Low      | Y  |
| LeetCode                | Proprietary | 50+   | Yes      | Yes      | read       | **HIGH** | P  |
| HackerRank              | Proprietary | 100+  | Yes      | Yes      | read+write | **HIGH** | P  |
| PGExercises             | Unclear     | ~80   | Yes      | Yes      | read+write | Medium   | Y  |

---

## Next steps (HITL before import)

1. Confirm license interpretation with founder before any third-party text
   lands on GitHub.
2. For MIT sources: author missing init SQL (HR schema, Northwind schema).
3. For CC BY-SA sources: decide if share-alike clause is acceptable for the
   project's licensing model.
4. For LeetCode/HackerRank: do NOT import — use as pattern reference only.
5. For PGExercises: contact author for license clarification before use.
