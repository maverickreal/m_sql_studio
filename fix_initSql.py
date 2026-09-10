#!/usr/bin/env python3
"""Update initSql for the 30 new problems to include full dataset SQL."""
import os
import re

base = "/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio_problems/problems"

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

HR_INIT = HR_SCHEMA + "\n\n" + HR_SEED

# Categories that were newly created for SAT-C2 (the 30 new problems)
NEW_CATEGORIES = ["self-joins", "cte-expressions", "string-operations", "date-arithmetic", "pivoting", "window-analytics", "set-analysis", "analytics-reporting", "query-patterns"]

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if this is a new problem (created at 10:14 or 10:15 today)
    # by checking if it has the old initSql format
    if not re.search(r'^initSql:\s*\|\s*\n\s*-- Dataset: hr', content, re.MULTILINE):
        return False  # Already has proper initSql or is original
    
    # Replace the initSql block
    # Pattern: initSql: |\n  -- Dataset: hr\n\n (or similar)
    new_init = "initSql: |\n  " + HR_INIT.replace('\n', '\n  ')
    
    # Find and replace the initSql block
    new_content = re.sub(
        r'^initSql:\s*\|-?\s*\n(?:  .*\n)*?(?=\n(?:solutionSql:|validationSql:))',
        new_init + '\n',
        content,
        flags=re.MULTILINE
    )
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False

fixed = 0
for root, dirs, files in os.walk(base):
    for fname in files:
        if fname.endswith('.yaml'):
            fpath = os.path.join(root, fname)
            if fix_file(fpath):
                print(f"Fixed: {fpath}")
                fixed += 1

print(f"\nTotal files fixed: {fixed}")
