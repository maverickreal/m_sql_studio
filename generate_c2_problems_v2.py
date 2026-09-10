#!/usr/bin/env python3
"""Regenerate all 30 new problems with full initSql baked in (dataset SQL included)."""
import os

UUIDS = [
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6001", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6002",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6003", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6004",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6005", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6006",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6007", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6008",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6009", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6010",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6011", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6012",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6013", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6014",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6015", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6016",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6017", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6018",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6019", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6020",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6021", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6022",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6023", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6024",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6025", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6026",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6027", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6028",
    "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6029", "0192f0a1-2b3c-7d8e-9f0a-1b2c3d4e6030",
]

HR_SCHEMA = """CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dept_id INT NOT NULL,
    salary INT NOT NULL,
    hire_date DATE NOT NULL,
    manager_id INT
);

CREATE TABLE departments (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL
);

CREATE TABLE projects (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dept_id INT NOT NULL,
    budget INT NOT NULL
);

CREATE TABLE employee_projects (
    employee_id INT NOT NULL,
    project_id INT NOT NULL,
    role VARCHAR(50) NOT NULL,
    PRIMARY KEY (employee_id, project_id)
);"""

HR_SEED = """INSERT INTO departments (id, name, location) VALUES
    (1, 'Engineering', 'San Francisco'),
    (2, 'Sales', 'New York'),
    (3, 'Marketing', 'Austin'),
    (4, 'HR', 'Chicago');

INSERT INTO employees (id, name, dept_id, salary, hire_date, manager_id) VALUES
    (1, 'Alice Chen', 1, 150000, '2020-01-15', NULL),
    (2, 'Bob Smith', 1, 120000, '2021-03-22', 1),
    (3, 'Carol Davis', 1, 130000, '2021-06-10', 1),
    (4, 'David Wilson', 2, 110000, '2019-11-05', NULL),
    (5, 'Eva Martinez', 2, 95000, '2022-02-14', 4),
    (6, 'Frank Brown', 2, 105000, '2022-08-30', 4),
    (7, 'Grace Lee', 3, 100000, '2021-04-18', NULL),
    (8, 'Henry Taylor', 3, 85000, '2023-01-12', 7),
    (9, 'Iris Anderson', 4, 90000, '2020-09-03', NULL);

INSERT INTO projects (id, name, dept_id, budget) VALUES
    (1, 'Data Pipeline', 1, 500000),
    (2, 'Mobile App', 1, 300000),
    (3, 'CRM Integration', 2, 200000),
    (4, 'Brand Campaign', 3, 150000);

INSERT INTO employee_projects (employee_id, project_id, role) VALUES
    (1, 1, 'Lead'),
    (2, 1, 'Developer'),
    (3, 1, 'Developer'),
    (2, 2, 'Lead'),
    (4, 3, 'Lead'),
    (5, 3, 'Analyst'),
    (7, 4, 'Lead'),
    (8, 4, 'Designer');"""

HR_INIT = HR_SCHEMA + "\n" + HR_SEED

# Problem definitions
PROBLEMS = [
    # --- advanced-joins extensions ---
    ("advanced-joins", "employees-longest-hire-streak",
     "Longest Continuous Hire Streak",
     "Find the longest streak of consecutive years where at least one employee was hired.",
     "medium", "read", ["hr"],
     ["employees(id, hire_date)"],
     "streak_start | streak_end | years_active\n---|---|---\n2019 | 2023 | 5",
     "WITH hire_years AS (SELECT DISTINCT EXTRACT(YEAR FROM hire_date) AS yr FROM employees),\nstreaks AS (SELECT yr, yr - ROW_NUMBER() OVER (ORDER BY yr) AS grp FROM hire_years)\nSELECT MIN(yr) AS streak_start, MAX(yr) AS streak_end, COUNT(*) AS years_active\nFROM streaks GROUP BY grp ORDER BY years_active DESC LIMIT 1;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    WITH hire_years AS (SELECT DISTINCT EXTRACT(YEAR FROM hire_date) AS yr FROM employees),\n    streaks AS (SELECT yr, yr - ROW_NUMBER() OVER (ORDER BY yr) AS grp FROM hire_years)\n    SELECT MIN(yr) AS streak_start, MAX(yr) AS streak_end, COUNT(*) AS years_active\n    FROM streaks GROUP BY grp ORDER BY years_active DESC LIMIT 1\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES (2019, 2023, 5)) expected(streak_start, streak_end, years_active)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("advanced-joins", "managers-with-multiple-direct-reports-same-dept",
     "Managers with Cross-Department Reports",
     "Find managers who have direct reports in more than one department.",
     "medium", "read", ["hr"],
     ["employees(id, name, dept_id, manager_id)"],
     "manager_name | num_departments\n---|---\nAlice Chen | 2",
     "SELECT m.name AS manager_name, COUNT(DISTINCT e.dept_id) AS num_departments\nFROM employees m JOIN employees e ON m.id = e.manager_id\nGROUP BY m.name HAVING COUNT(DISTINCT e.dept_id) > 1;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT m.name AS manager_name, COUNT(DISTINCT e.dept_id) AS num_departments\n    FROM employees m JOIN employees e ON m.id = e.manager_id\n    GROUP BY m.name HAVING COUNT(DISTINCT e.dept_id) > 1\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES ('Alice Chen', 2)) expected(manager_name, num_departments)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("advanced-joins", "projects-with-dept-mismatch",
     "Projects Outside Home Department",
     "Find employees working on projects that belong to a different department than their own.",
     "hard", "read", ["hr"],
     ["employees(id, name, dept_id)", "projects(id, name, dept_id)", "employee_projects(employee_id, project_id, role)"],
     "employee_name | employee_dept | project_name | project_dept\n---|---|---|---\n(no rows)",
     "SELECT e.name AS employee_name, d.name AS employee_dept, p.name AS project_name, pd.name AS project_dept\nFROM projects p\nJOIN departments pd ON p.dept_id = pd.id\nJOIN employee_projects ep ON p.id = ep.project_id\nJOIN employees e ON ep.employee_id = e.id\nJOIN departments d ON e.dept_id = d.id\nWHERE p.dept_id != e.dept_id;",
     "SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS correct FROM (\n  SELECT e.name AS employee_name, d.name AS employee_dept, p.name AS project_name, pd.name AS project_dept\n  FROM projects p\n  JOIN departments pd ON p.dept_id = pd.id\n  JOIN employee_projects ep ON p.id = ep.project_id\n  JOIN employees e ON ep.employee_id = e.id\n  JOIN departments d ON e.dept_id = d.id\n  WHERE p.dept_id != e.dept_id\n) t;",
     True),

    # --- aggregation extensions ---
    ("aggregation", "salary-spread-by-dept",
     "Salary Spread by Department",
     "Calculate the difference between the highest and lowest salary in each department.",
     "easy", "read", ["hr"],
     ["departments(id, name)", "employees(id, dept_id, salary)"],
     "dept_name | salary_spread\n---|---\nEngineering | 30000\nSales | 15000\nMarketing | 15000\nHR | 0",
     "SELECT d.name AS dept_name, COALESCE(MAX(e.salary) - MIN(e.salary), 0) AS salary_spread\nFROM departments d LEFT JOIN employees e ON d.id = e.dept_id\nGROUP BY d.name ORDER BY salary_spread DESC;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT d.name AS dept_name, COALESCE(MAX(e.salary) - MIN(e.salary), 0) AS salary_spread\n    FROM departments d LEFT JOIN employees e ON d.id = e.dept_id\n    GROUP BY d.name ORDER BY salary_spread DESC\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES ('Engineering', 30000), ('Sales', 15000), ('Marketing', 15000), ('HR', 0)) expected(dept_name, salary_spread)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("aggregation", "median-salary-per-role",
     "Median Salary by Role",
     "Compute the median salary for each project role.",
     "hard", "read", ["hr"],
     ["employees(id, salary)", "employee_projects(employee_id, project_id, role)"],
     "role | median_salary\n---|---\nLead | 120000.00\nDeveloper | 120000.00\nDesigner | 85000.00\nAnalyst | 95000.00",
     "SELECT ep.role, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.salary) AS median_salary\nFROM employees e JOIN employee_projects ep ON e.id = ep.employee_id\nGROUP BY ep.role ORDER BY median_salary DESC;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT ep.role, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.salary) AS median_salary\n    FROM employees e JOIN employee_projects ep ON e.id = ep.employee_id\n    GROUP BY ep.role ORDER BY median_salary DESC\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES ('Lead', 120000.00), ('Developer', 120000.00), ('Designer', 85000.00), ('Analyst', 95000.00)) expected(role, median_salary)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("aggregation", "dept-budget-utilization",
     "Department Budget Utilization",
     "Show what fraction of department budget is consumed by employee salaries.",
     "medium", "read", ["hr"],
     ["departments(id, name)", "employees(dept_id, salary)", "projects(dept_id, budget)"],
     "dept_name | salary_cost | project_budget | utilization_pct\n---|---|---|---\nEngineering | 400000 | 800000 | 50.00\nSales | 310000 | 200000 | 155.00\nMarketing | 185000 | 150000 | 123.33\nHR | 90000 | 0 | NULL",
     "SELECT d.name AS dept_name,\n  SUM(e.salary) AS salary_cost,\n  SUM(p.budget) AS project_budget,\n  CASE WHEN SUM(p.budget) > 0 THEN ROUND(SUM(e.salary) * 100.0 / SUM(p.budget), 2) ELSE NULL END AS utilization_pct\nFROM departments d\nLEFT JOIN employees e ON d.id = e.dept_id\nLEFT JOIN projects p ON d.id = p.dept_id\nGROUP BY d.name ORDER BY utilization_pct DESC NULLS LAST;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT d.name AS dept_name, SUM(e.salary) AS salary_cost, SUM(p.budget) AS project_budget,\n      CASE WHEN SUM(p.budget) > 0 THEN ROUND(SUM(e.salary) * 100.0 / SUM(p.budget), 2) ELSE NULL END AS utilization_pct\n    FROM departments d LEFT JOIN employees e ON d.id = e.dept_id LEFT JOIN projects p ON d.id = p.dept_id\n    GROUP BY d.name ORDER BY utilization_pct DESC NULLS LAST\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Engineering', 400000, 800000, 50.00),\n    ('Sales', 310000, 200000, 155.00),\n    ('Marketing', 185000, 150000, 123.33),\n    ('HR', 90000, 0, NULL)\n  ) expected(dept_name, salary_cost, project_budget, utilization_pct)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    # --- self-joins ---
    ("self-joins", "pairs-under-same-manager",
     "Employee Pairs Under Same Manager",
     "List all pairs of employees who report to the same manager (excluding self-pairs).",
     "medium", "read", ["hr"],
     ["employees(id, name, manager_id)"],
     "manager_id | employee_a | employee_b\n---|---|---\n1 | Bob Smith | Carol Davis\n4 | Eva Martinez | Frank Brown",
     "SELECT e1.manager_id, e1.name AS employee_a, e2.name AS employee_b\nFROM employees e1 JOIN employees e2 ON e1.manager_id = e2.manager_id AND e1.id < e2.id\nWHERE e1.manager_id IS NOT NULL\nORDER BY e1.manager_id;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT e1.manager_id, e1.name AS employee_a, e2.name AS employee_b\n    FROM employees e1 JOIN employees e2 ON e1.manager_id = e2.manager_id AND e1.id < e2.id\n    WHERE e1.manager_id IS NOT NULL ORDER BY e1.manager_id\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    (1, 'Bob Smith', 'Carol Davis'),\n    (4, 'Eva Martinez', 'Frank Brown')\n  ) expected(manager_id, employee_a, employee_b)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("self-joins", "salary-gap-between-peers",
     "Salary Gap Between Peers",
     "Find pairs of employees in the same department with the largest salary difference.",
     "medium", "read", ["hr"],
     ["employees(id, name, dept_id, salary)"],
     "dept_id | higher_paid | lower_paid | salary_gap\n---|---|---|---\n1 | Alice Chen | Bob Smith | 30000\n1 | Alice Chen | Carol Davis | 20000\n1 | Carol Davis | Bob Smith | 10000\n2 | David Wilson | Eva Martinez | 15000\n2 | David Wilson | Frank Brown | 5000\n2 | Frank Brown | Eva Martinez | 10000\n3 | Grace Lee | Henry Taylor | 15000",
     "SELECT e1.dept_id, e1.name AS higher_paid, e2.name AS lower_paid, ABS(e1.salary - e2.salary) AS salary_gap\nFROM employees e1 JOIN employees e2 ON e1.dept_id = e2.dept_id AND e1.id < e2.id\nORDER BY salary_gap DESC;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT e1.dept_id, e1.name AS higher_paid, e2.name AS lower_paid, ABS(e1.salary - e2.salary) AS salary_gap\n    FROM employees e1 JOIN employees e2 ON e1.dept_id = e2.dept_id AND e1.id < e2.id\n    ORDER BY salary_gap DESC\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    (1, 'Alice Chen', 'Bob Smith', 30000),\n    (1, 'Alice Chen', 'Carol Davis', 20000),\n    (1, 'Carol Davis', 'Bob Smith', 10000),\n    (2, 'David Wilson', 'Eva Martinez', 15000),\n    (2, 'David Wilson', 'Frank Brown', 5000),\n    (2, 'Frank Brown', 'Eva Martinez', 10000),\n    (3, 'Grace Lee', 'Henry Taylor', 15000)\n  ) expected(dept_id, higher_paid, lower_paid, salary_gap)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("self-joins", "hire-order-by-dept",
     "Hire Order by Department",
     "Rank employees within their department by hire date (seniority).",
     "easy", "read", ["hr"],
     ["employees(id, name, dept_id, hire_date)"],
     "dept_id | name | hire_date | seniority_rank\n---|---|---|---\n1 | Alice Chen | 2020-01-15 | 1\n1 | Bob Smith | 2021-03-22 | 2\n1 | Carol Davis | 2021-06-10 | 3\n2 | David Wilson | 2019-11-05 | 1\n2 | Eva Martinez | 2022-02-14 | 2\n2 | Frank Brown | 2022-08-30 | 3\n3 | Grace Lee | 2021-04-18 | 1\n3 | Henry Taylor | 2023-01-12 | 2\n4 | Iris Anderson | 2020-09-03 | 1",
     "SELECT dept_id, name, hire_date,\n  ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY hire_date) AS seniority_rank\nFROM employees ORDER BY dept_id, seniority_rank;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT dept_id, name, hire_date,\n      ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY hire_date) AS seniority_rank\n    FROM employees ORDER BY dept_id, seniority_rank\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    (1, 'Alice Chen', '2020-01-15', 1), (1, 'Bob Smith', '2021-03-22', 2), (1, 'Carol Davis', '2021-06-10', 3),\n    (2, 'David Wilson', '2019-11-05', 1), (2, 'Eva Martinez', '2022-02-14', 2), (2, 'Frank Brown', '2022-08-30', 3),\n    (3, 'Grace Lee', '2021-04-18', 1), (3, 'Henry Taylor', '2023-01-12', 2),\n    (4, 'Iris Anderson', '2020-09-03', 1)\n  ) expected(dept_id, name, hire_date, seniority_rank)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    # --- cte-expressions ---
    ("cte-expressions", "org-depth-per-employee",
     "Org Depth Per Employee",
     "Calculate the management depth (number of levels from CEO) for each employee.",
     "hard", "read", ["hr"],
     ["employees(id, name, manager_id)"],
     "name | org_depth\n---|---\nAlice Chen | 0\nDavid Wilson | 0\nGrace Lee | 0\nIris Anderson | 0\nBob Smith | 1\nCarol Davis | 1\nEva Martinez | 1\nFrank Brown | 1\nHenry Taylor | 1",
     "WITH RECURSIVE org AS (\n  SELECT id, name, manager_id, 0 AS org_depth FROM employees WHERE manager_id IS NULL\n  UNION ALL\n  SELECT e.id, e.name, e.manager_id, o.org_depth + 1\n  FROM employees e JOIN org o ON e.manager_id = o.id\n)\nSELECT name, org_depth FROM org ORDER BY org_depth, name;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    WITH RECURSIVE org AS (\n      SELECT id, name, manager_id, 0 AS org_depth FROM employees WHERE manager_id IS NULL\n      UNION ALL\n      SELECT e.id, e.name, e.manager_id, o.org_depth + 1\n      FROM employees e JOIN org o ON e.manager_id = o.id\n    )\n    SELECT name, org_depth FROM org ORDER BY org_depth, name\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Alice Chen', 0), ('David Wilson', 0), ('Grace Lee', 0), ('Iris Anderson', 0),\n    ('Bob Smith', 1), ('Carol Davis', 1), ('Eva Martinez', 1), ('Frank Brown', 1), ('Henry Taylor', 1)\n  ) expected(name, org_depth)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("cte-expressions", "team-roster-with-levels",
     "Team Roster with Levels",
     "Show each manager's team hierarchy with indentation levels.",
     "hard", "read", ["hr"],
     ["employees(id, name, manager_id)"],
     "manager_name | team_size | max_depth\n---|---|---\nAlice Chen | 2 | 1\nDavid Wilson | 2 | 1\nGrace Lee | 1 | 1",
     "WITH RECURSIVE team AS (\n  SELECT e.id, e.name, e.manager_id, 1 AS lvl, e.id AS root\n  FROM employees e WHERE e.manager_id IS NULL\n  UNION ALL\n  SELECT e.id, e.name, e.manager_id, t.lvl + 1, t.root\n  FROM employees e JOIN team t ON e.manager_id = t.id\n)\nSELECT m.name AS manager_name, COUNT(t.id) AS team_size, MAX(t.lvl) - 1 AS max_depth\nFROM team t JOIN employees m ON t.root = m.id\nWHERE t.manager_id IS NOT NULL\nGROUP BY m.name ORDER BY team_size DESC;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    WITH RECURSIVE team AS (\n      SELECT e.id, e.name, e.manager_id, 1 AS lvl, e.id AS root\n      FROM employees e WHERE e.manager_id IS NULL\n      UNION ALL\n      SELECT e.id, e.name, e.manager_id, t.lvl + 1, t.root\n      FROM employees e JOIN team t ON e.manager_id = t.id\n    )\n    SELECT m.name AS manager_name, COUNT(t.id) AS team_size, MAX(t.lvl) - 1 AS max_depth\n    FROM team t JOIN employees m ON t.root = m.id\n    WHERE t.manager_id IS NOT NULL\n    GROUP BY m.name ORDER BY team_size DESC\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Alice Chen', 2, 1), ('David Wilson', 2, 1), ('Grace Lee', 1, 1)\n  ) expected(manager_name, team_size, max_depth)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("cte-expressions", "budget-waterfall",
     "Budget Waterfall Analysis",
     "Compute cumulative budget spent across projects ordered by project id.",
     "medium", "read", ["hr"],
     ["projects(id, name, budget)"],
     "project_name | budget | cumulative_budget\n---|---|---\nData Pipeline | 500000 | 500000\nMobile App | 300000 | 800000\nCRM Integration | 200000 | 1000000\nBrand Campaign | 150000 | 1150000",
     "WITH ordered AS (\n  SELECT name AS project_name, budget, ROW_NUMBER() OVER (ORDER BY id) AS rn\n  FROM projects\n)\nSELECT project_name, budget, SUM(budget) OVER (ORDER BY rn) AS cumulative_budget\nFROM ordered;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    WITH ordered AS (\n      SELECT name AS project_name, budget, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM projects\n    )\n    SELECT project_name, budget, SUM(budget) OVER (ORDER BY rn) AS cumulative_budget\n    FROM ordered\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Data Pipeline', 500000, 500000), ('Mobile App', 300000, 800000),\n    ('CRM Integration', 200000, 1000000), ('Brand Campaign', 150000, 1150000)\n  ) expected(project_name, budget, cumulative_budget)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    # --- string-operations ---
    ("string-operations", "name-pattern-search",
     "Pattern-Based Employee Search",
     "Find employees whose name contains a space and starts with a vowel in the last name.",
     "easy", "read", ["hr"],
     ["employees(id, name)"],
     "name\n---\nAlice Chen\nEva Martinez",
     "SELECT name FROM employees\nWHERE name LIKE '% %'\nAND (name ILIKE '% A%' OR name ILIKE '% E%' OR name ILIKE '% I%' OR name ILIKE '% O%' OR name ILIKE '% U%')\nORDER BY name;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT name FROM employees\n    WHERE name LIKE '% %'\n    AND (name ILIKE '% A%' OR name ILIKE '% E%' OR name ILIKE '% I%' OR name ILIKE '% O%' OR name ILIKE '% U%')\n    ORDER BY name\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES ('Alice Chen'), ('Eva Martinez')) expected(name)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("string-operations", "extract-name-components",
     "Name Component Extraction",
     "Split employee names into first and last name components.",
     "easy", "read", ["hr"],
     ["employees(id, name)"],
     "first_name | last_name\n---|---\nAlice | Chen\nBob | Smith\nCarol | Davis\nDavid | Wilson\nEva | Martinez\nFrank | Brown\nGrace | Lee\nHenry | Taylor\nIris | Anderson",
     "SELECT SPLIT_PART(name, ' ', 1) AS first_name, SPLIT_PART(name, ' ', 2) AS last_name\nFROM employees ORDER BY last_name, first_name;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT SPLIT_PART(name, ' ', 1) AS first_name, SPLIT_PART(name, ' ', 2) AS last_name\n    FROM employees ORDER BY last_name, first_name\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Alice', 'Chen'), ('Bob', 'Smith'), ('Carol', 'Davis'), ('David', 'Wilson'),\n    ('Eva', 'Martinez'), ('Frank', 'Brown'), ('Grace', 'Lee'), ('Henry', 'Taylor'), ('Iris', 'Anderson')\n  ) expected(first_name, last_name)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("string-operations", "name-acronym-generator",
     "Department Acronym Generator",
     "Generate an acronym from each department name by concatenating first letters of words.",
     "medium", "read", ["hr"],
     ["departments(id, name)"],
     "dept_name | acronym\n---|---\nEngineering | E\nHR | H\nMarketing | M\nSales | S",
     "SELECT name AS dept_name, UPPER(LEFT(name, 1)) AS acronym FROM departments ORDER BY name;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT name AS dept_name, UPPER(LEFT(name, 1)) AS acronym FROM departments ORDER BY name\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Engineering', 'E'), ('HR', 'H'), ('Marketing', 'M'), ('Sales', 'S')\n  ) expected(dept_name, acronym)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    # --- date-arithmetic ---
    ("date-arithmetic", "tenure-categories",
     "Employee Tenure Categories",
     "Categorize employees into tenure brackets using hire date: <1 year, 1-3 years, 3-5 years, >5 years.",
     "medium", "read", ["hr"],
     ["employees(id, name, hire_date)"],
     "name | hire_date | years_since_hire | tenure_category\n---|---|---|---\nAlice Chen | 2020-01-15 | 6 | >5 years\nDavid Wilson | 2019-11-05 | 6 | >5 years\nBob Smith | 2021-03-22 | 4 | 3-5 years\nCarol Davis | 2021-06-10 | 4 | 3-5 years\nGrace Lee | 2021-04-18 | 4 | 3-5 years\nIris Anderson | 2020-09-03 | 5 | 3-5 years\nEva Martinez | 2022-02-14 | 3 | 3-5 years\nFrank Brown | 2022-08-30 | 3 | 3-5 years\nHenry Taylor | 2023-01-12 | 3 | 3-5 years",
     "SELECT name, hire_date,\n  EXTRACT(YEAR FROM AGE('2026-01-01'::date, hire_date)) AS years_since_hire,\n  CASE\n    WHEN AGE('2026-01-01'::date, hire_date) < INTERVAL '1 year' THEN '<1 year'\n    WHEN AGE('2026-01-01'::date, hire_date) < INTERVAL '3 years' THEN '1-3 years'\n    WHEN AGE('2026-01-01'::date, hire_date) < INTERVAL '5 years' THEN '3-5 years'\n    ELSE '>5 years'\n  END AS tenure_category\nFROM employees ORDER BY years_since_hire DESC;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT name, hire_date,\n      EXTRACT(YEAR FROM AGE('2026-01-01'::date, hire_date)) AS years_since_hire,\n      CASE\n        WHEN AGE('2026-01-01'::date, hire_date) < INTERVAL '1 year' THEN '<1 year'\n        WHEN AGE('2026-01-01'::date, hire_date) < INTERVAL '3 years' THEN '1-3 years'\n        WHEN AGE('2026-01-01'::date, hire_date) < INTERVAL '5 years' THEN '3-5 years'\n        ELSE '>5 years'\n      END AS tenure_category\n    FROM employees ORDER BY years_since_hire DESC\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Alice Chen', '2020-01-15', 6, '>5 years'),\n    ('David Wilson', '2019-11-05', 6, '>5 years'),\n    ('Bob Smith', '2021-03-22', 4, '3-5 years'),\n    ('Carol Davis', '2021-06-10', 4, '3-5 years'),\n    ('Eva Martinez', '2022-02-14', 3, '3-5 years'),\n    ('Frank Brown', '2022-08-30', 3, '3-5 years'),\n    ('Grace Lee', '2021-04-18', 4, '3-5 years'),\n    ('Henry Taylor', '2023-01-12', 3, '3-5 years'),\n    ('Iris Anderson', '2020-09-03', 5, '3-5 years')\n  ) expected(name, hire_date, years_since_hire, tenure_category)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("date-arithmetic", "hire-anniversary-this-month",
     "Hire Anniversaries in January",
     "Find employees whose hire anniversary falls in January.",
     "easy", "read", ["hr"],
     ["employees(id, name, hire_date)"],
     "name | hire_date\n---|---\nAlice Chen | 2020-01-15",
     "SELECT name, hire_date\nFROM employees WHERE EXTRACT(MONTH FROM hire_date) = 1\nORDER BY hire_date;",
     "SELECT CASE WHEN COUNT(*) = 1 THEN 1 ELSE 0 END AS correct FROM (\n  SELECT name, hire_date FROM employees WHERE EXTRACT(MONTH FROM hire_date) = 1 ORDER BY hire_date\n) t;",
     True),

    ("date-arithmetic", "longest-hire-gap",
     "Longest Gap Between Hires",
     "Find the longest time gap between consecutive hires in the company.",
     "medium", "read", ["hr"],
     ["employees(id, hire_date)"],
     "previous_hire | next_hire | gap_days\n---|---|---\n2022-08-30 | 2023-01-12 | 135\n2022-02-14 | 2022-08-30 | 197\n2021-06-10 | 2022-02-14 | 249",
     "WITH ordered AS (\n  SELECT hire_date, LEAD(hire_date) OVER (ORDER BY hire_date) AS next_hire_date\n  FROM employees\n)\nSELECT hire_date AS previous_hire, next_hire_date AS next_hire,\n  (next_hire_date - hire_date) AS gap_days\nFROM ordered\nWHERE next_hire_date IS NOT NULL\nORDER BY gap_days DESC LIMIT 3;",
     "SELECT CASE WHEN COUNT(*) = 3 THEN 1 ELSE 0 END AS correct FROM (\n  WITH ordered AS (\n    SELECT hire_date, LEAD(hire_date) OVER (ORDER BY hire_date) AS next_hire_date FROM employees\n  )\n  SELECT hire_date AS previous_hire, next_hire_date AS next_hire, (next_hire_date - hire_date) AS gap_days\n  FROM ordered WHERE next_hire_date IS NOT NULL ORDER BY gap_days DESC LIMIT 3\n) t;",
     True),

    # --- pivoting ---
    ("pivoting", "role-spread-matrix",
     "Role Spread Matrix",
     "Pivot employee count by department and role.",
     "hard", "read", ["hr"],
     ["departments(id, name)", "employees(id, dept_id)", "employee_projects(employee_id, project_id, role)"],
     "dept_name | Lead | Developer | Analyst | Designer\n---|---|---|---|---\nEngineering | 1 | 2 | 0 | 0\nHR | 0 | 0 | 0 | 0\nMarketing | 1 | 0 | 0 | 1\nSales | 1 | 0 | 1 | 0",
     "SELECT d.name AS dept_name,\n  COUNT(*) FILTER (WHERE ep.role = 'Lead') AS \"Lead\",\n  COUNT(*) FILTER (WHERE ep.role = 'Developer') AS \"Developer\",\n  COUNT(*) FILTER (WHERE ep.role = 'Analyst') AS \"Analyst\",\n  COUNT(*) FILTER (WHERE ep.role = 'Designer') AS \"Designer\"\nFROM departments d\nLEFT JOIN employees e ON d.id = e.dept_id\nLEFT JOIN employee_projects ep ON e.id = ep.employee_id\nGROUP BY d.name ORDER BY d.name;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT d.name AS dept_name,\n      COUNT(*) FILTER (WHERE ep.role = 'Lead') AS \"Lead\",\n      COUNT(*) FILTER (WHERE ep.role = 'Developer') AS \"Developer\",\n      COUNT(*) FILTER (WHERE ep.role = 'Analyst') AS \"Analyst\",\n      COUNT(*) FILTER (WHERE ep.role = 'Designer') AS \"Designer\"\n    FROM departments d LEFT JOIN employees e ON d.id = e.dept_id LEFT JOIN employee_projects ep ON e.id = ep.employee_id\n    GROUP BY d.name ORDER BY d.name\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Engineering', 1, 2, 0, 0), ('HR', 0, 0, 0, 0), ('Marketing', 1, 0, 0, 1), ('Sales', 1, 0, 1, 0)\n  ) expected(dept_name, \"Lead\", \"Developer\", \"Analyst\", \"Designer\")\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("pivoting", "salary-band-distribution",
     "Salary Band Distribution",
     "Group employees into salary bands and count distribution.",
     "medium", "read", ["hr"],
     ["employees(id, salary)"],
     "salary_band | count | pct_of_total\n---|---|---\n100k-125k | 3 | 33.33\nOver-125k | 1 | 11.11\nUnder-100k | 5 | 55.56",
     "SELECT\n  CASE\n    WHEN salary < 100000 THEN 'Under-100k'\n    WHEN salary <= 125000 THEN '100k-125k'\n    ELSE 'Over-125k'\n  END AS salary_band,\n  COUNT(*) AS count,\n  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM employees), 2) AS pct_of_total\nFROM employees\nGROUP BY 1 ORDER BY 1;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT\n      CASE\n        WHEN salary < 100000 THEN 'Under-100k'\n        WHEN salary <= 125000 THEN '100k-125k'\n        ELSE 'Over-125k'\n      END AS salary_band,\n      COUNT(*) AS count,\n      ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM employees), 2) AS pct_of_total\n    FROM employees GROUP BY 1 ORDER BY 1\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('100k-125k', 3, 33.33), ('Over-125k', 1, 11.11), ('Under-100k', 5, 55.56)\n  ) expected(salary_band, count, pct_of_total)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    # --- window-analytics ---
    ("window-analytics", "salary-percentile-rank",
     "Salary Percentile Rank",
     "Compute percentile rank for each employee's salary (what fraction earn less).",
     "medium", "read", ["hr"],
     ["employees(id, name, salary)"],
     "name | salary | percentile_rank\n---|---|---\nHenry Taylor | 85000 | 0.111\nIris Anderson | 90000 | 0.222\nEva Martinez | 95000 | 0.333\nDavid Wilson | 110000 | 0.444\nFrank Brown | 105000 | 0.556\nGrace Lee | 100000 | 0.667\nBob Smith | 120000 | 0.778\nCarol Davis | 130000 | 0.889\nAlice Chen | 150000 | 1.000",
     "SELECT name, salary,\n  PERCENT_RANK() OVER (ORDER BY salary) AS percentile_rank\nFROM employees ORDER BY salary;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT name, salary, PERCENT_RANK() OVER (ORDER BY salary) AS percentile_rank\n    FROM employees ORDER BY salary\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Henry Taylor', 85000, 0.111), ('Iris Anderson', 90000, 0.222), ('Eva Martinez', 95000, 0.333),\n    ('David Wilson', 110000, 0.444), ('Frank Brown', 105000, 0.556), ('Grace Lee', 100000, 0.667),\n    ('Bob Smith', 120000, 0.778), ('Carol Davis', 130000, 0.889), ('Alice Chen', 150000, 1.0)\n  ) expected(name, salary, percentile_rank)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("window-analytics", "top-2-earners-per-dept",
     "Top 2 Earners Per Department",
     "Select the two highest-paid employees in each department.",
     "medium", "read", ["hr"],
     ["departments(id, name)", "employees(id, name, dept_id, salary)"],
     "dept_name | name | salary | dept_rank\n---|---|---|---\nEngineering | Alice Chen | 150000 | 1\nEngineering | Carol Davis | 130000 | 2\nHR | Iris Anderson | 90000 | 1\nMarketing | Grace Lee | 100000 | 1\nMarketing | Henry Taylor | 85000 | 2\nSales | David Wilson | 110000 | 1\nSales | Frank Brown | 105000 | 2",
     "SELECT dept_name, name, salary, dept_rank\nFROM (\n  SELECT d.name AS dept_name, e.name, e.salary,\n    ROW_NUMBER() OVER (PARTITION BY d.id ORDER BY e.salary DESC) AS dept_rank\n  FROM employees e JOIN departments d ON e.dept_id = d.id\n) ranked\nWHERE dept_rank <= 2 ORDER BY dept_name, dept_rank;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT dept_name, name, salary, dept_rank\n    FROM (\n      SELECT d.name AS dept_name, e.name, e.salary,\n        ROW_NUMBER() OVER (PARTITION BY d.id ORDER BY e.salary DESC) AS dept_rank\n      FROM employees e JOIN departments d ON e.dept_id = d.id\n    ) ranked WHERE dept_rank <= 2 ORDER BY dept_name, dept_rank\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Engineering', 'Alice Chen', 150000, 1), ('Engineering', 'Carol Davis', 130000, 2),\n    ('HR', 'Iris Anderson', 90000, 1),\n    ('Marketing', 'Grace Lee', 100000, 1), ('Marketing', 'Henry Taylor', 85000, 2),\n    ('Sales', 'David Wilson', 110000, 1), ('Sales', 'Frank Brown', 105000, 2)\n  ) expected(dept_name, name, salary, dept_rank)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("window-analytics", "salary-momentum-over-hires",
     "Salary Momentum Over Hires",
     "Track whether salaries are increasing or decreasing over time using a running comparison.",
     "medium", "read", ["hr"],
     ["employees(id, name, hire_date, salary)"],
     "name | hire_date | salary | prev_hire_salary | trend\n---|---|---|---|---\nAlice Chen | 2020-01-15 | 150000 | NULL | START\nBob Smith | 2021-03-22 | 120000 | 150000 | DOWN\nCarol Davis | 2021-06-10 | 130000 | 120000 | UP\nDavid Wilson | 2019-11-05 | 110000 | NULL | START\nEva Martinez | 2022-02-14 | 95000 | 110000 | DOWN\nFrank Brown | 2022-08-30 | 105000 | 95000 | UP\nGrace Lee | 2021-04-18 | 100000 | NULL | START\nHenry Taylor | 2023-01-12 | 85000 | 100000 | DOWN\nIris Anderson | 2020-09-03 | 90000 | NULL | START",
     "SELECT name, hire_date, salary,\n  LAG(salary) OVER (ORDER BY hire_date) AS prev_hire_salary,\n  CASE\n    WHEN LAG(salary) OVER (ORDER BY hire_date) IS NULL THEN 'START'\n    WHEN salary > LAG(salary) OVER (ORDER BY hire_date) THEN 'UP'\n    WHEN salary < LAG(salary) OVER (ORDER BY hire_date) THEN 'DOWN'\n    ELSE 'FLAT'\n  END AS trend\nFROM employees ORDER BY hire_date;",
     "SELECT CASE WHEN COUNT(*) = 9 THEN 1 ELSE 0 END AS correct FROM (\n  SELECT name, hire_date, salary,\n    LAG(salary) OVER (ORDER BY hire_date) AS prev_hire_salary,\n    CASE\n      WHEN LAG(salary) OVER (ORDER BY hire_date) IS NULL THEN 'START'\n      WHEN salary > LAG(salary) OVER (ORDER BY hire_date) THEN 'UP'\n      WHEN salary < LAG(salary) OVER (ORDER BY hire_date) THEN 'DOWN'\n      ELSE 'FLAT'\n    END AS trend\n  FROM employees ORDER BY hire_date\n) t;",
     True),

    # --- set-analysis ---
    ("set-analysis", "employees-in-all-projects",
     "Universal Project Participants",
     "Find employees who are assigned to every project in the company.",
     "medium", "read", ["hr"],
     ["employees(id, name)", "projects(id)", "employee_projects(employee_id, project_id)"],
     "name\n---\n(no rows)",
     "SELECT e.name FROM employees e\nJOIN employee_projects ep ON e.id = ep.employee_id\nGROUP BY e.id, e.name\nHAVING COUNT(DISTINCT ep.project_id) = (SELECT COUNT(*) FROM projects);",
     "SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END AS correct FROM (\n  SELECT e.name FROM employees e\n  JOIN employee_projects ep ON e.id = ep.employee_id\n  GROUP BY e.id, e.name\n  HAVING COUNT(DISTINCT ep.project_id) = (SELECT COUNT(*) FROM projects)\n) t;",
     True),

    ("set-analysis", "project-coverage-by-dept",
     "Project Coverage by Department",
     "Find departments that have at least one employee on every project.",
     "hard", "read", ["hr"],
     ["departments(id, name)", "employees(id, dept_id)", "employee_projects(employee_id, project_id)"],
     "dept_name\n---\nEngineering",
     "SELECT d.name AS dept_name\nFROM departments d\nJOIN employees e ON d.id = e.dept_id\nJOIN employee_projects ep ON e.id = ep.employee_id\nGROUP BY d.id, d.name\nHAVING COUNT(DISTINCT ep.project_id) = (SELECT COUNT(*) FROM projects);",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT d.name AS dept_name\n    FROM departments d JOIN employees e ON d.id = e.dept_id JOIN employee_projects ep ON e.id = ep.employee_id\n    GROUP BY d.id, d.name HAVING COUNT(DISTINCT ep.project_id) = (SELECT COUNT(*) FROM projects)\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES ('Engineering')) expected(dept_name)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("set-analysis", "mutually-exclusive-project-pairs",
     "Mutually Exclusive Project Pairs",
     "Find pairs of projects that share no common employees.",
     "hard", "read", ["hr"],
     ["projects(id, name)", "employee_projects(project_id, employee_id)"],
     "project_a | project_b\n---|---\nBrand Campaign | Data Pipeline\nBrand Campaign | Mobile App\nCRM Integration | Mobile App",
     "SELECT p1.name AS project_a, p2.name AS project_b\nFROM projects p1 CROSS JOIN projects p2\nWHERE p1.id < p2.id\nAND NOT EXISTS (\n  SELECT 1 FROM employee_projects ep1\n  JOIN employee_projects ep2 ON ep1.employee_id = ep2.employee_id\n  WHERE ep1.project_id = p1.id AND ep2.project_id = p2.id\n)\nORDER BY project_a, project_b;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT p1.name AS project_a, p2.name AS project_b\n    FROM projects p1 CROSS JOIN projects p2\n    WHERE p1.id < p2.id\n    AND NOT EXISTS (\n      SELECT 1 FROM employee_projects ep1\n      JOIN employee_projects ep2 ON ep1.employee_id = ep2.employee_id\n      WHERE ep1.project_id = p1.id AND ep2.project_id = p2.id\n    )\n    ORDER BY project_a, project_b\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Brand Campaign', 'Data Pipeline'),\n    ('Brand Campaign', 'Mobile App'),\n    ('CRM Integration', 'Mobile App')\n  ) expected(project_a, project_b)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    # --- analytics-reporting ---
    ("analytics-reporting", "quarterly-hiring-report",
     "Quarterly Hiring Report",
     "Generate a quarterly hiring summary for all years.",
     "medium", "read", ["hr"],
     ["employees(id, hire_date)"],
     "quarter | hire_count\n---|---|---\n1 | 2\n2 | 1\n3 | 1\n4 | 2",
     "SELECT EXTRACT(QUARTER FROM hire_date) AS quarter,\n  COUNT(*) AS hire_count\nFROM employees\nGROUP BY quarter ORDER BY quarter;",
     "SELECT CASE WHEN COUNT(*) = 4 THEN 1 ELSE 0 END AS correct FROM (\n  SELECT EXTRACT(QUARTER FROM hire_date) AS quarter, COUNT(*) AS hire_count\n  FROM employees GROUP BY quarter ORDER BY quarter\n) t;",
     True),

    ("analytics-reporting", "department-comparison-dashboard",
     "Department Comparison Dashboard",
     "Build a comprehensive dashboard comparing departments on key metrics.",
     "hard", "read", ["hr"],
     ["departments(id, name)", "employees(id, dept_id, salary)", "projects(dept_id, budget)"],
     "dept_name | emp_count | avg_salary | total_budget | budget_per_emp\n---|---|---|---|---\nEngineering | 3 | 133333.33 | 800000 | 266666.67\nSales | 3 | 103333.33 | 200000 | 66666.67\nMarketing | 2 | 92500.00 | 150000 | 75000.00\nHR | 1 | 90000.00 | 0 | 0.00",
     "SELECT d.name AS dept_name,\n  COUNT(e.id) AS emp_count,\n  ROUND(AVG(e.salary), 2) AS avg_salary,\n  COALESCE(SUM(p.budget), 0) AS total_budget,\n  CASE WHEN COUNT(e.id) > 0 THEN ROUND(COALESCE(SUM(p.budget), 0) * 1.0 / COUNT(e.id), 2) ELSE 0 END AS budget_per_emp\nFROM departments d\nLEFT JOIN employees e ON d.id = e.dept_id\nLEFT JOIN projects p ON d.id = p.dept_id\nGROUP BY d.name ORDER BY avg_salary DESC;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT d.name AS dept_name,\n      COUNT(e.id) AS emp_count,\n      ROUND(AVG(e.salary), 2) AS avg_salary,\n      COALESCE(SUM(p.budget), 0) AS total_budget,\n      CASE WHEN COUNT(e.id) > 0 THEN ROUND(COALESCE(SUM(p.budget), 0) * 1.0 / COUNT(e.id), 2) ELSE 0 END AS budget_per_emp\n    FROM departments d LEFT JOIN employees e ON d.id = e.dept_id LEFT JOIN projects p ON d.id = p.dept_id\n    GROUP BY d.name ORDER BY avg_salary DESC\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Engineering', 3, 133333.33, 800000, 266666.67),\n    ('Sales', 3, 103333.33, 200000, 66666.67),\n    ('Marketing', 2, 92500.00, 150000, 75000.00),\n    ('HR', 1, 90000.00, 0, 0.00)\n  ) expected(dept_name, emp_count, avg_salary, total_budget, budget_per_emp)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    # --- query-patterns ---
    ("query-patterns", "consecutive-salary-increases",
     "Consecutive Salary Increases",
     "Find the longest streak of consecutive hires where each new hire had a higher salary than the previous.",
     "hard", "read", ["hr"],
     ["employees(id, hire_date, salary)"],
     "streak_start_date | streak_end_date | streak_length\n---|---|---\n2020-09-03 | 2021-06-10 | 4\n2021-04-18 | 2023-01-12 | 2\n2022-02-14 | 2022-08-30 | 2",
     "WITH ordered AS (\n  SELECT hire_date, salary, ROW_NUMBER() OVER (ORDER BY hire_date) AS rn FROM employees\n),\nstreaks AS (\n  SELECT hire_date, salary, rn,\n    CASE WHEN salary > LAG(salary) OVER (ORDER BY rn) THEN 0 ELSE 1 END AS new_group\n  FROM ordered\n),\ngrouped AS (\n  SELECT hire_date, salary, SUM(new_group) OVER (ORDER BY rn) AS grp\n  FROM streaks\n)\nSELECT MIN(hire_date) AS streak_start_date, MAX(hire_date) AS streak_end_date, COUNT(*) AS streak_length\nFROM grouped GROUP BY grp ORDER BY streak_length DESC LIMIT 3;",
     "SELECT CASE WHEN COUNT(*) >= 1 THEN 1 ELSE 0 END AS correct FROM (\n  WITH ordered AS (SELECT hire_date, salary, ROW_NUMBER() OVER (ORDER BY hire_date) AS rn FROM employees),\n  streaks AS (SELECT hire_date, salary, rn, CASE WHEN salary > LAG(salary) OVER (ORDER BY rn) THEN 0 ELSE 1 END AS new_group FROM ordered),\n  grouped AS (SELECT hire_date, salary, SUM(new_group) OVER (ORDER BY rn) AS grp FROM streaks)\n  SELECT MIN(hire_date) AS streak_start_date, MAX(hire_date) AS streak_end_date, COUNT(*) AS streak_length\n  FROM grouped GROUP BY grp ORDER BY streak_length DESC LIMIT 3\n) t;",
     True),

    ("query-patterns", "salary-change-point-detection",
     "Salary Change Point Detection",
     "Identify hire dates where the salary trend shifted direction.",
     "hard", "read", ["hr"],
     ["employees(id, hire_date, salary)"],
     "hire_date | salary | prev_salary | next_salary | trend_shift\n---|---|---|---|---\n2020-09-03 | 90000 | NULL | 110000 | VALLEY\n2019-11-05 | 110000 | 90000 | NULL | PEAK\n2022-08-30 | 105000 | 95000 | NULL | PEAK",
     "SELECT hire_date, salary, prev_salary, next_salary,\n  CASE\n    WHEN (prev_salary IS NULL OR salary > prev_salary) AND (next_salary IS NOT NULL AND next_salary < salary) THEN 'PEAK'\n    WHEN (prev_salary IS NULL OR salary < prev_salary) AND (next_salary IS NOT NULL AND next_salary > salary) THEN 'VALLEY'\n    ELSE 'CONTINUE'\n  END AS trend_shift\nFROM (\n  SELECT hire_date, salary,\n    LAG(salary) OVER (ORDER BY hire_date) AS prev_salary,\n    LEAD(salary) OVER (ORDER BY hire_date) AS next_salary\n  FROM employees\n) sub\nWHERE (prev_salary IS NULL OR salary > prev_salary) AND (next_salary IS NOT NULL AND next_salary < salary)\n   OR (prev_salary IS NULL OR salary < prev_salary) AND (next_salary IS NOT NULL AND next_salary > salary)\nORDER BY hire_date;",
     "SELECT CASE WHEN COUNT(*) >= 1 THEN 1 ELSE 0 END AS correct FROM (\n  SELECT hire_date, salary, prev_salary, next_salary,\n    CASE\n      WHEN (prev_salary IS NULL OR salary > prev_salary) AND (next_salary IS NOT NULL AND next_salary < salary) THEN 'PEAK'\n      WHEN (prev_salary IS NULL OR salary < prev_salary) AND (next_salary IS NOT NULL AND next_salary > salary) THEN 'VALLEY'\n      ELSE 'CONTINUE'\n    END AS trend_shift\n  FROM (\n    SELECT hire_date, salary,\n      LAG(salary) OVER (ORDER BY hire_date) AS prev_salary,\n      LEAD(salary) OVER (ORDER BY hire_date) AS next_salary\n    FROM employees\n  ) sub\n  WHERE (prev_salary IS NULL OR salary > prev_salary) AND (next_salary IS NOT NULL AND next_salary < salary)\n     OR (prev_salary IS NULL OR salary < prev_salary) AND (next_salary IS NOT NULL AND next_salary > salary)\n  ORDER BY hire_date\n) t;",
     True),

    # --- remaining problems ---
    ("aggregation", "employee-age-pyramid",
     "Employee Age Pyramid",
     "Build an age pyramid (buckets) showing distribution of employees by age decade.",
     "medium", "read", ["hr"],
     ["employees(id, name, hire_date)"],
     "hire_decade | count\n---|---\n19s | 9",
     "SELECT\n  CONCAT(EXTRACT(YEAR FROM hire_date) - 2000, 's') AS hire_decade,\n  COUNT(*) AS count\nFROM employees GROUP BY 1 ORDER BY 1;",
     "SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END AS correct FROM (\n  SELECT CONCAT(EXTRACT(YEAR FROM hire_date) - 2000, 's') AS hire_decade, COUNT(*) AS count\n  FROM employees GROUP BY 1 ORDER BY 1\n) t;",
     True),

    ("window-functions", "dense-salary-rank",
     "Dense Salary Ranking",
     "Rank all employees by salary using DENSE_RANK() with ties.",
     "easy", "read", ["hr"],
     ["employees(id, name, salary)"],
     "name | salary | dense_rank\n---|---|---\nAlice Chen | 150000 | 1\nCarol Davis | 130000 | 2\nBob Smith | 120000 | 3\nDavid Wilson | 110000 | 4\nGrace Lee | 100000 | 5\nFrank Brown | 105000 | 6\nEva Martinez | 95000 | 7\nIris Anderson | 90000 | 8\nHenry Taylor | 85000 | 9",
     "SELECT name, salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank\nFROM employees ORDER BY dense_rank;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT name, salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank\n    FROM employees ORDER BY dense_rank\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Alice Chen', 150000, 1), ('Carol Davis', 130000, 2), ('Bob Smith', 120000, 3),\n    ('David Wilson', 110000, 4), ('Grace Lee', 100000, 5), ('Frank Brown', 105000, 6),\n    ('Eva Martinez', 95000, 7), ('Iris Anderson', 90000, 8), ('Henry Taylor', 85000, 9)\n  ) expected(name, salary, dense_rank)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("recursive", "management-chain-to-root",
     "Management Chain to Root",
     "For each employee, show the full chain of command up to the CEO.",
     "hard", "read", ["hr"],
     ["employees(id, name, manager_id)"],
     "employee | chain\n---|---\nBob Smith | Bob Smith -> Alice Chen\nCarol Davis | Carol Davis -> Alice Chen\nEva Martinez | Eva Martinez -> David Wilson\nFrank Brown | Frank Brown -> David Wilson\nHenry Taylor | Henry Taylor -> Grace Lee",
     "WITH RECURSIVE chain AS (\n  SELECT id, name, manager_id, name AS path, 0 AS depth\n  FROM employees WHERE manager_id IS NULL\n  UNION ALL\n  SELECT e.id, e.name, e.manager_id, e.name || ' -> ' || c.path, c.depth + 1\n  FROM employees e JOIN chain c ON e.manager_id = c.id\n)\nSELECT name AS employee, path AS chain FROM chain WHERE depth > 0 ORDER BY depth, name;",
     "SELECT CASE WHEN COUNT(*) = 6 THEN 1 ELSE 0 END AS correct FROM (\n  WITH RECURSIVE chain AS (\n    SELECT id, name, manager_id, name AS path, 0 AS depth FROM employees WHERE manager_id IS NULL\n    UNION ALL\n    SELECT e.id, e.name, e.manager_id, e.name || ' -> ' || c.path, c.depth + 1\n    FROM employees e JOIN chain c ON e.manager_id = c.id\n  )\n  SELECT name AS employee, path AS chain FROM chain WHERE depth > 0 ORDER BY depth, name\n) t;",
     True),

    ("subqueries", "above-dept-avg-with-subquery",
     "Above Department Average (Subquery)",
     "Find employees earning more than their department average using a correlated subquery.",
     "medium", "read", ["hr"],
     ["employees(id, name, dept_id, salary)"],
     "name | salary | dept_id\n---|---|---\nAlice Chen | 150000 | 1\nCarol Davis | 130000 | 1\nDavid Wilson | 110000 | 2\nGrace Lee | 100000 | 3",
     "SELECT name, salary, dept_id FROM employees e\nWHERE salary > (\n  SELECT AVG(salary) FROM employees WHERE dept_id = e.dept_id\n)\nORDER BY dept_id, salary DESC;",
     "SELECT CASE WHEN NOT EXISTS (\n  SELECT 1 FROM (\n    SELECT name, salary, dept_id FROM employees e\n    WHERE salary > (SELECT AVG(salary) FROM employees WHERE dept_id = e.dept_id)\n    ORDER BY dept_id, salary DESC\n  ) user_result\n  EXCEPT SELECT 1 FROM (VALUES\n    ('Alice Chen', 150000, 1), ('Carol Davis', 130000, 1),\n    ('David Wilson', 110000, 2), ('Grace Lee', 100000, 3)\n  ) expected(name, salary, dept_id)\n) THEN 1 ELSE 0 END AS correct;",
     True),

    ("cte-expressions", "salary-percentile-buckets",
     "Salary Percentile Buckets",
     "Divide employees into quartiles based on salary.",
     "medium", "read", ["hr"],
     ["employees(id, name, salary)"],
     "name | salary | quartile\n---|---|---\nHenry Taylor | 85000 | 1\nIris Anderson | 90000 | 1\nEva Martinez | 95000 | 2\nGrace Lee | 100000 | 2\nFrank Brown | 105000 | 3\nDavid Wilson | 110000 | 3\nBob Smith | 120000 | 4\nCarol Davis | 130000 | 4\nAlice Chen | 150000 | 4",
     "SELECT name, salary, NTILE(4) OVER (ORDER BY salary) AS quartile\nFROM employees ORDER BY salary;",
     "SELECT CASE WHEN COUNT(*) = 9 THEN 1 ELSE 0 END AS correct FROM (\n  SELECT name, salary, NTILE(4) OVER (ORDER BY salary) AS quartile\n  FROM employees ORDER BY salary\n) t;",
     True),

    ("joins", "project-teams-with-manager-info",
     "Project Teams with Manager Info",
     "List project teams including each member's manager name.",
     "medium", "read", ["hr"],
     ["employees(id, name, manager_id)", "projects(id, name)", "employee_projects(employee_id, project_id, role)"],
     "project_name | member_name | role | manager_name\n---|---|---|---\nBrand Campaign | Grace Lee | Lead | (null)\nBrand Campaign | Henry Taylor | Designer | Grace Lee\nCRM Integration | David Wilson | Lead | (null)\nCRM Integration | Eva Martinez | Analyst | David Wilson\nData Pipeline | Alice Chen | Lead | (null)\nData Pipeline | Bob Smith | Developer | Alice Chen\nData Pipeline | Carol Davis | Developer | Alice Chen\nMobile App | Bob Smith | Lead | Alice Chen",
     "SELECT p.name AS project_name, e.name AS member_name, ep.role, m.name AS manager_name\nFROM projects p\nJOIN employee_projects ep ON p.id = ep.project_id\nJOIN employees e ON ep.employee_id = e.id\nLEFT JOIN employees m ON e.manager_id = m.id\nORDER BY p.name, e.name;",
     "SELECT CASE WHEN COUNT(*) = 8 THEN 1 ELSE 0 END AS correct FROM (\n  SELECT p.name AS project_name, e.name AS member_name, ep.role, m.name AS manager_name\n  FROM projects p JOIN employee_projects ep ON p.id = ep.project_id\n  JOIN employees e ON ep.employee_id = e.id LEFT JOIN employees m ON e.manager_id = m.id\n  ORDER BY p.name, e.name\n) t;",
     True),

]


def make_problem_yaml(pid, category, slug, title, description, difficulty, mode, datasets, sampleInput, sampleOutput, initSql, solutionSql, validationSql, orderMatters):
    datasets_yaml = "\n".join(f"  - {d}" for d in datasets)
    sampleInput_yaml = "\n".join(f"  - \"{s}\"" for s in sampleInput)

    order = "true" if orderMatters else "false"

    return f'''id: "{pid}"
slug: "{slug}"
title: "{title}"
description: |
  {description}
difficulty: {difficulty}
mode: {mode}
category: {category}
datasets:
{datasets_yaml}
sampleInput:
{sampleInput_yaml}
sampleOutput: |
  {sampleOutput}
initSql: |
  {initSql}
solutionSql: |
  {solutionSql}
validationSql: |
  {validationSql}
orderMatters: {order}
origin: first-party
author: "maverickreal"
license: "CC-BY-4.0"
schema_version: 1
'''


def main():
    base = "/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio_problems/problems"

    # Create new category directories
    new_categories = ["self-joins", "cte-expressions", "string-operations", "date-arithmetic", "pivoting", "window-analytics", "set-analysis", "analytics-reporting", "query-patterns"]
    for cat in new_categories:
        os.makedirs(f"{base}/{cat}", exist_ok=True)

    for i, (category, slug, title, description, difficulty, mode, datasets, sampleInput, sampleOutput, solutionSql, validationSql, orderMatters) in enumerate(PROBLEMS):
        pid = UUIDS[i]
        content = make_problem_yaml(pid, category, slug, title, description, difficulty, mode, datasets, sampleInput, sampleOutput, HR_INIT, solutionSql, validationSql, orderMatters)
        filepath = f"{base}/{category}/{slug}.yaml"
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Created: {filepath}")

    # Count total
    total = sum(1 for _, _, _, _, _, _, _, _, _, _, _, _ in PROBLEMS)
    print(f"\nTotal new problems: {total}")


if __name__ == "__main__":
    main()
