#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const envPath = path.resolve(__dirname, "../.env");
if (fs.existsSync(envPath)) {
  const envFile = fs.readFileSync(envPath, "utf8");
  envFile.split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith("#")) {
      const parts = trimmed.split("=");
      const key = parts[0].trim();
      const value = parts
        .slice(1)
        .join("=")
        .trim()
        .replace(/^['"]|['"]$/g, "");
      if (key && !process.env[key]) {
        process.env[key] = value;
      }
    }
  });
}

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || "http://127.0.0.1:8000";
const CLIENT_URL = process.env.CLIENT_URL || "http://127.0.0.1";
const ADMIN_EMAIL = process.env.DEFAULT_ADMIN_EMAIL || "admin@m-sql-studio.dev";
const ADMIN_PASSWORD = process.env.DEFAULT_ADMIN_PASSWORD || "admin123";

let sessionCookie = null;

const ASSIGNMENTS = [
  {
    title: "E-commerce: Order Totals",
    description:
      "Calculate the total amount spent by each customer. Join customers, orders, and order_items tables and group by customer name.",
    difficulty: "medium",
    mode: "read",
    sampleInput: [
      "SELECT c.name, SUM(oi.price * oi.quantity) as total_spent FROM customers c JOIN orders o ON c.id = o.customer_id JOIN order_items oi ON o.id = oi.order_id GROUP BY c.name;",
    ],
    sampleOutput: "name | total_spent\n---|---\nAlice | 150.00\nBob | 75.50",
    initSql: `
      CREATE TABLE customers (id SERIAL PRIMARY KEY, name TEXT);
      CREATE TABLE orders (id SERIAL PRIMARY KEY, customer_id INT REFERENCES customers(id), order_date DATE);
      CREATE TABLE order_items (id SERIAL PRIMARY KEY, order_id INT REFERENCES orders(id), product_name TEXT, price DECIMAL(10,2), quantity INT);
      INSERT INTO customers (name) VALUES ('Alice'), ('Bob');
      INSERT INTO orders (customer_id, order_date) VALUES (1, '2024-01-01'), (2, '2024-01-02');
      INSERT INTO order_items (order_id, product_name, price, quantity) VALUES (1, 'Widget A', 50.00, 2), (1, 'Widget B', 25.00, 2), (2, 'Widget C', 75.50, 1);
    `,
    solutionSql:
      "SELECT c.name, SUM(oi.price * oi.quantity) as total_spent FROM customers c JOIN orders o ON c.id = o.customer_id JOIN order_items oi ON o.id = oi.order_id GROUP BY c.name;",
    orderMatters: false,
  },
  {
    title: "School Management: Student Enrollment",
    description:
      "Find all students enrolled in 'Computer Science 101'. Use JOINs across students, enrollments, and courses.",
    difficulty: "medium",
    mode: "read",
    sampleInput: [
      "SELECT s.name FROM students s JOIN enrollments e ON s.id = e.student_id JOIN courses c ON e.course_id = c.id WHERE c.title = 'Computer Science 101';",
    ],
    sampleOutput: "name\n---\nAlice\nCharlie",
    initSql: `
      CREATE TABLE students (id SERIAL PRIMARY KEY, name TEXT);
      CREATE TABLE courses (id SERIAL PRIMARY KEY, title TEXT);
      CREATE TABLE enrollments (student_id INT REFERENCES students(id), course_id INT REFERENCES courses(id));
      INSERT INTO students (name) VALUES ('Alice'), ('Bob'), ('Charlie');
      INSERT INTO courses (title) VALUES ('Computer Science 101'), ('Database Systems');
      INSERT INTO enrollments (student_id, course_id) VALUES (1, 1), (2, 2), (3, 1);
    `,
    solutionSql:
      "SELECT s.name FROM students s JOIN enrollments e ON s.id = e.student_id JOIN courses c ON e.course_id = c.id WHERE c.title = 'Computer Science 101';",
    orderMatters: false,
  },
  {
    title: "Library System: Outdated Books Cleanup",
    description: "Remove all books published before 1950 from the books table.",
    difficulty: "hard",
    mode: "write",
    sampleInput: ["DELETE FROM books WHERE publish_year < 1950;"],
    sampleOutput: "Successfully deleted 2 rows.",
    initSql: `
      CREATE TABLE books (id SERIAL PRIMARY KEY, title TEXT, author TEXT, publish_year INT);
      INSERT INTO books (title, author, publish_year) VALUES ('The Great Gatsby', 'F. Scott Fitzgerald', 1925), ('1984', 'George Orwell', 1949), ('The Catcher in the Rye', 'J.D. Salinger', 1951);
    `,
    solutionSql: "DELETE FROM books WHERE publish_year < 1950;",
    validationSql: "SELECT COUNT(*) FROM books;",
    orderMatters: true,
  },
  {
    title: "HR: Employee Salary Update",
    description:
      "Give a 10% raise to all employees in the 'Engineering' department.",
    difficulty: "hard",
    mode: "write",
    sampleInput: [
      "UPDATE employees SET salary = salary * 1.1 WHERE department = 'Engineering';",
    ],
    sampleOutput: "Salaries updated for Engineering department.",
    initSql: `
      CREATE TABLE employees (id SERIAL PRIMARY KEY, name TEXT, department TEXT, salary DECIMAL(10,2));
      INSERT INTO employees (name, department, salary) VALUES ('Alice', 'Engineering', 100000.00), ('Bob', 'Marketing', 80000.00), ('Charlie', 'Engineering', 90000.00);
    `,
    solutionSql:
      "UPDATE employees SET salary = salary * 1.1 WHERE department = 'Engineering';",
    validationSql:
      "SELECT salary FROM employees WHERE department = 'Engineering' ORDER BY name;",
    orderMatters: true,
  },
  {
    title: "Leaderboard: Top Scores",
    description: "Get the top 3 users by score in descending order.",
    difficulty: "easy",
    mode: "read",
    sampleInput: [
      "SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 3;",
    ],
    sampleOutput:
      "username | score\n---|---\nCharlie | 95\nBob | 80\nAlice | 75",
    initSql: `
      CREATE TABLE leaderboard (id SERIAL PRIMARY KEY, username TEXT, score INT);
      INSERT INTO leaderboard (username, score) VALUES ('Alice', 75), ('Bob', 80), ('Charlie', 95), ('Dave', 60);
    `,
    solutionSql:
      "SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 3;",
    orderMatters: true,
  },
];

const waitForGateway = async (url, retries, interval) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url);
      const body = await response.json().catch(() => null);
      const mongoOk = body?.checks?.mongodb === "ok";

      // Seeding only needs the API and MongoDB; sandbox_db may still be warming up.
      if (response.ok || mongoOk) {
        console.log("API Gateway is up and ready for seeding!");
        return true;
      } else {
        console.log(
          `API Gateway returned status ${response.status}\n${url}. Attempt number ${i + 1} of ${retries}.`,
        );
      }
    } catch (err) {
      console.log(
        `Error: ${err.message}\nAttempt number ${i + 1} of ${retries}.`,
      );
    }
    await new Promise((resolve) => setTimeout(resolve, interval));
  }

  return false;
};

const seed = async () => {
  console.log("Seeding Database with sample assignments.");

  const isUp = await waitForGateway(`${API_GATEWAY_URL}/health`, 10, 2000);

  if (!isUp) {
    console.error("API Gateway is unreachable or unhealthy; Skipping seed!");
    process.exit(1);
  }

  console.log("Authenticating as admin user...");
  const signInRes = await fetch(`${API_GATEWAY_URL}/api/auth/sign-in/email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Origin: CLIENT_URL,
    },
    body: JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASSWORD }),
    redirect: "manual",
  });

  if (!signInRes.ok) {
    const errorText = await signInRes.text();
    console.error(
      `Admin authentication failed! Status ${signInRes.status}: ${errorText}`,
    );
    process.exit(1);
  }

  const setCookieHeader = signInRes.headers.get("set-cookie");
  if (setCookieHeader) {
    sessionCookie = setCookieHeader;
  }
  console.log("Admin authentication complete.");

  for (const assignment of ASSIGNMENTS) {
    console.log(`Seeding assignment: ${assignment.title}.`);

    try {
      const response = await fetch(
        `${API_GATEWAY_URL}/api/v1/admin/assignments`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Origin: CLIENT_URL,
            ...(sessionCookie ? { Cookie: sessionCookie } : {}),
          },
          body: JSON.stringify(assignment),
        },
      );

      if (response.ok) {
        const result = await response.json();
        console.log(`Seeded Assignment ${result.assignmentId}.`);
      } else {
        const error = await response.text();

        throw new Error(`Status ${response.status}: ${error}`);
      }
    } catch (err) {
      console.error(`Failed in seeding Assignment ${assignment.title}!`, err);
    }
  }

  console.log("Seeding complete.");
};

seed().catch((err) => {
  console.error("Unhandled error in seed script!", err);
  process.exit(1);
});
