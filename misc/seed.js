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
const CLIENT_URL = process.env.CLIENT_URL || "http://127.0.0.1:3000";
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
      "| name |",
      "| --- |",
      "| Alice |",
      "| Bob |",
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
      "| name |",
      "| --- |",
      "| Alice |",
      "| Bob |",
      "| Charlie |",
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
    sampleInput: [
      "| title | author | publish_year |",
      "| --- | --- | --- |",
      "| The Great Gatsby | F. Scott Fitzgerald | 1925 |",
      "| 1984 | George Orwell | 1949 |",
      "| The Catcher in the Rye | J.D. Salinger | 1951 |",
    ],
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
      "| name | department | salary |",
      "| --- | --- | --- |",
      "| Alice | Engineering | 100000.00 |",
      "| Bob | Marketing | 80000.00 |",
      "| Charlie | Engineering | 90000.00 |",
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
      "| username | score |",
      "| --- | --- |",
      "| Alice | 75 |",
      "| Bob | 80 |",
      "| Charlie | 95 |",
      "| Dave | 60 |",
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
  {
    title: "Pet Shelter: Dogs Ready for Adoption",
    description:
      "List the name and breed of every dog that is still waiting for a home, sorted alphabetically by name.",
    difficulty: "easy",
    mode: "read",
    sampleInput: [
      "| name | breed | adopted |",
      "| --- | --- | --- |",
      "| Bella | Labrador | false |",
      "| Max | Beagle | true |",
      "| Luna | Poodle | false |",
      "| Rocky | Bulldog | true |",
      "| Coco | Terrier | false |",
    ],
    sampleOutput: "name | breed\n---|---\nBella | Labrador\nCoco | Terrier\nLuna | Poodle",
    initSql: `
      CREATE TABLE dogs (id SERIAL PRIMARY KEY, name TEXT, breed TEXT, age_years INT, adopted BOOLEAN);
      INSERT INTO dogs (name, breed, age_years, adopted) VALUES ('Bella', 'Labrador', 3, false), ('Max', 'Beagle', 5, true), ('Luna', 'Poodle', 2, false), ('Rocky', 'Bulldog', 4, true), ('Coco', 'Terrier', 1, false);
    `,
    solutionSql:
      "SELECT name, breed FROM dogs WHERE adopted = false ORDER BY name;",
    orderMatters: true,
  },
  {
    title: "Cinema: Evening Showtimes",
    description:
      "Show the film title and start time for every screening that starts at or after 18:00, earliest first.",
    difficulty: "easy",
    mode: "read",
    sampleInput: [
      "| film_title | starts_at |",
      "| --- | --- |",
      "| Solaris Return | 14:30 |",
      "| Paper Moons | 18:15 |",
      "| Harbor Nights | 20:45 |",
      "| Dust Trails | 21:30 |",
    ],
    sampleOutput:
      "film_title | starts_at\n---|---\nPaper Moons | 18:15\nHarbor Nights | 20:45\nDust Trails | 21:30",
    initSql: `
      CREATE TABLE screenings (id SERIAL PRIMARY KEY, film_title TEXT, starts_at TEXT, hall TEXT);
      INSERT INTO screenings (film_title, starts_at, hall) VALUES ('Solaris Return', '14:30', 'A'), ('Paper Moons', '18:15', 'B'), ('Harbor Nights', '20:45', 'A'), ('Dust Trails', '21:30', 'C');
    `,
    solutionSql:
      "SELECT film_title, starts_at FROM screenings WHERE starts_at >= '18:00' ORDER BY starts_at;",
    orderMatters: true,
  },
  {
    title: "Grocery: Low Stock Produce",
    description:
      "Find every produce item with less than 10 kg in stock, showing the lightest stock first.",
    difficulty: "easy",
    mode: "read",
    sampleInput: [
      "| item | stock_kg |",
      "| --- | --- |",
      "| Apples | 42.50 |",
      "| Basil | 6.00 |",
      "| Carrots | 18.00 |",
      "| Dill | 3.25 |",
    ],
    sampleOutput: "item | stock_kg\n---|---\nDill | 3.25\nBasil | 6.00",
    initSql: `
      CREATE TABLE produce (id SERIAL PRIMARY KEY, item TEXT, stock_kg DECIMAL(8,2), unit TEXT);
      INSERT INTO produce (item, stock_kg, unit) VALUES ('Apples', 42.50, 'kg'), ('Basil', 6.00, 'kg'), ('Carrots', 18.00, 'kg'), ('Dill', 3.25, 'kg');
    `,
    solutionSql:
      "SELECT item, stock_kg FROM produce WHERE stock_kg < 10 ORDER BY stock_kg;",
    orderMatters: true,
  },
  {
    title: "Gym: Active Members Roll",
    description:
      "List the full name and plan of every member whose membership is currently active, in alphabetical order.",
    difficulty: "easy",
    mode: "read",
    sampleInput: [
      "| full_name | plan | active |",
      "| --- | --- | --- |",
      "| Ana | monthly | true |",
      "| Ben | annual | false |",
      "| Jo | annual | true |",
      "| Max | monthly | false |",
      "| Rae | monthly | true |",
    ],
    sampleOutput:
      "full_name | plan\n---|---\nAna | monthly\nJo | annual\nRae | monthly",
    initSql: `
      CREATE TABLE members (id SERIAL PRIMARY KEY, full_name TEXT, plan TEXT, active BOOLEAN);
      INSERT INTO members (full_name, plan, active) VALUES ('Ana', 'monthly', true), ('Ben', 'annual', false), ('Jo', 'annual', true), ('Max', 'monthly', false), ('Rae', 'monthly', true);
    `,
    solutionSql:
      "SELECT full_name, plan FROM members WHERE active = true ORDER BY full_name;",
    orderMatters: true,
  },
  {
    title: "Transit: Downtown Stops by Frequency",
    description:
      "Show downtown stops with their weekday headway, most frequent service first.",
    difficulty: "easy",
    mode: "read",
    sampleInput: [
      "| stop_name | zone | weekday_headway_min |",
      "| --- | --- | --- |",
      "| Central Plaza | downtown | 5 |",
      "| Old Market | downtown | 8 |",
      "| North Depot | uptown | 15 |",
      "| River Gate | downtown | 12 |",
      "| Hill View | suburb | 30 |",
    ],
    sampleOutput:
      "stop_name | weekday_headway_min\n---|---\nCentral Plaza | 5\nOld Market | 8\nRiver Gate | 12",
    initSql: `
      CREATE TABLE stops (id SERIAL PRIMARY KEY, stop_name TEXT, zone TEXT, weekday_headway_min INT);
      INSERT INTO stops (stop_name, zone, weekday_headway_min) VALUES ('Central Plaza', 'downtown', 5), ('Old Market', 'downtown', 8), ('North Depot', 'uptown', 15), ('River Gate', 'downtown', 12), ('Hill View', 'suburb', 30);
    `,
    solutionSql:
      "SELECT stop_name, weekday_headway_min FROM stops WHERE zone = 'downtown' ORDER BY weekday_headway_min;",
    orderMatters: true,
  },
  {
    title: "Music: Most Played Tracks",
    description:
      "Get the top 3 tracks by play count, most played first.",
    difficulty: "easy",
    mode: "read",
    sampleInput: [
      "| title | artist | plays |",
      "| --- | --- | --- |",
      "| Night Bus | The Comets | 910 |",
      "| Glass House | Mira | 720 |",
      "| Static Bloom | The Comets | 655 |",
      "| Paper Sun | Koda | 410 |",
      "| Low Orbit | Mira | 95 |",
    ],
    sampleOutput:
      "title | artist\n---|---\nNight Bus | The Comets\nGlass House | Mira\nStatic Bloom | The Comets",
    initSql: `
      CREATE TABLE tracks (id SERIAL PRIMARY KEY, title TEXT, artist TEXT, plays INT);
      INSERT INTO tracks (title, artist, plays) VALUES ('Night Bus', 'The Comets', 910), ('Glass House', 'Mira', 720), ('Static Bloom', 'The Comets', 655), ('Paper Sun', 'Koda', 410), ('Low Orbit', 'Mira', 95);
    `,
    solutionSql:
      "SELECT title, artist FROM tracks ORDER BY plays DESC LIMIT 3;",
    orderMatters: true,
  },
  {
    title: "Restaurant: Revenue Per Dish",
    description:
      "Compute total revenue for each dish by joining dishes with ticket lines, highest revenue first.",
    difficulty: "medium",
    mode: "read",
    sampleInput: [
      "| dish_name | price |",
      "| --- | --- |",
      "| Margherita | 12.50 |",
      "| Ramen | 14.00 |",
      "| Garden Salad | 9.00 |",
    ],
    sampleOutput:
      "dish_name | revenue\n---|---\nMargherita | 62.50\nRamen | 42.00\nGarden Salad | 36.00",
    initSql: `
      CREATE TABLE dishes (id SERIAL PRIMARY KEY, dish_name TEXT, price DECIMAL(10,2));
      CREATE TABLE ticket_lines (id SERIAL PRIMARY KEY, dish_id INT REFERENCES dishes(id), qty INT);
      INSERT INTO dishes (dish_name, price) VALUES ('Margherita', 12.50), ('Ramen', 14.00), ('Garden Salad', 9.00);
      INSERT INTO ticket_lines (dish_id, qty) VALUES (1, 2), (1, 3), (2, 1), (2, 2), (3, 4);
    `,
    solutionSql:
      "SELECT d.dish_name, SUM(d.price * t.qty) as revenue FROM dishes d JOIN ticket_lines t ON d.id = t.dish_id GROUP BY d.dish_name ORDER BY revenue DESC;",
    orderMatters: true,
  },
  {
    title: "Clinic: Upcoming Visits with Doctors",
    description:
      "List upcoming visits on or after 2024-06-10 with patient name, doctor name, and date, soonest first.",
    difficulty: "medium",
    mode: "read",
    sampleInput: [
      "| patient_name | visit_date |",
      "| --- | --- |",
      "| Kim | 2024-06-02 |",
      "| Sam | 2024-06-10 |",
      "| Ivy | 2024-06-12 |",
      "| Leo | 2024-06-15 |",
    ],
    sampleOutput:
      "patient_name | doc_name | visit_date\n---|---|---\nSam | Dr. Osei | 2024-06-10\nIvy | Dr. Patel | 2024-06-12\nLeo | Dr. Osei | 2024-06-15",
    initSql: `
      CREATE TABLE doctors (id SERIAL PRIMARY KEY, doc_name TEXT, specialty TEXT);
      CREATE TABLE visits (id SERIAL PRIMARY KEY, doctor_id INT REFERENCES doctors(id), patient_name TEXT, visit_date DATE);
      INSERT INTO doctors (doc_name, specialty) VALUES ('Dr. Osei', 'General'), ('Dr. Patel', 'Dental');
      INSERT INTO visits (doctor_id, patient_name, visit_date) VALUES (1, 'Kim', '2024-06-02'), (1, 'Sam', '2024-06-10'), (2, 'Ivy', '2024-06-12'), (1, 'Leo', '2024-06-15');
    `,
    solutionSql:
      "SELECT v.patient_name, d.doc_name, v.visit_date FROM visits v JOIN doctors d ON v.doctor_id = d.id WHERE v.visit_date >= '2024-06-10' ORDER BY v.visit_date;",
    orderMatters: true,
  },
  {
    title: "Airline: Seats Booked Per Flight",
    description:
      "Total up the booked seats for each flight number, ordered by flight number.",
    difficulty: "medium",
    mode: "read",
    sampleInput: [
      "| flight_no | origin | destination |",
      "| --- | --- | --- |",
      "| KQ 101 | Nairobi | Lagos |",
      "| KQ 205 | Nairobi | Accra |",
    ],
    sampleOutput: "flight_no | booked\n---|---\nKQ 101 | 210\nKQ 205 | 96",
    initSql: `
      CREATE TABLE flights (id SERIAL PRIMARY KEY, flight_no TEXT, origin TEXT, destination TEXT);
      CREATE TABLE bookings (id SERIAL PRIMARY KEY, flight_id INT REFERENCES flights(id), seats INT);
      INSERT INTO flights (flight_no, origin, destination) VALUES ('KQ 101', 'Nairobi', 'Lagos'), ('KQ 205', 'Nairobi', 'Accra');
      INSERT INTO bookings (flight_id, seats) VALUES (1, 120), (1, 90), (2, 60), (2, 36);
    `,
    solutionSql:
      "SELECT f.flight_no, SUM(b.seats) as booked FROM flights f JOIN bookings b ON f.id = b.flight_id GROUP BY f.flight_no ORDER BY f.flight_no;",
    orderMatters: true,
  },
  {
    title: "Bank: Low Balance Checking Accounts",
    description:
      "Find checking accounts under 500 with the holder name and balance, poorest first.",
    difficulty: "medium",
    mode: "read",
    sampleInput: [
      "| holder_name | acct_type | balance |",
      "| --- | --- | --- |",
      "| Tess | checking | 120.00 |",
      "| Raj | checking | 340.50 |",
      "| Moe | checking | 1500.00 |",
      "| Ada | savings | 80.00 |",
    ],
    sampleOutput: "holder_name | balance\n---|---\nTess | 120.00\nRaj | 340.50",
    initSql: `
      CREATE TABLE holders (id SERIAL PRIMARY KEY, holder_name TEXT);
      CREATE TABLE accounts (id SERIAL PRIMARY KEY, holder_id INT REFERENCES holders(id), acct_type TEXT, balance DECIMAL(12,2));
      INSERT INTO holders (holder_name) VALUES ('Tess'), ('Raj'), ('Moe'), ('Ada');
      INSERT INTO accounts (holder_id, acct_type, balance) VALUES (1, 'checking', 120.00), (2, 'checking', 340.50), (3, 'checking', 1500.00), (4, 'savings', 80.00);
    `,
    solutionSql:
      "SELECT h.holder_name, a.balance FROM holders h JOIN accounts a ON h.id = a.holder_id WHERE a.acct_type = 'checking' AND a.balance < 500 ORDER BY a.balance;",
    orderMatters: true,
  },
  {
    title: "Warehouse: Stock Value by Aisle",
    description:
      "Compute the total stock value (unit cost times quantity on hand) for each aisle, ordered by aisle.",
    difficulty: "medium",
    mode: "read",
    sampleInput: [
      "| part_name | aisle | unit_cost | on_hand |",
      "| --- | --- | --- | --- |",
      "| Bolts | A1 | 0.50 | 400 |",
      "| Nuts | A1 | 0.25 | 600 |",
      "| Sensor | B2 | 22.00 | 10 |",
    ],
    sampleOutput: "aisle | stock_value\n---|---\nA1 | 350.00\nB2 | 220.00",
    initSql: `
      CREATE TABLE parts (id SERIAL PRIMARY KEY, part_name TEXT, aisle TEXT, unit_cost DECIMAL(10,2), on_hand INT);
      INSERT INTO parts (part_name, aisle, unit_cost, on_hand) VALUES ('Bolts', 'A1', 0.50, 400), ('Nuts', 'A1', 0.25, 600), ('Sensor', 'B2', 22.00, 10);
    `,
    solutionSql:
      "SELECT aisle, SUM(unit_cost * on_hand) as stock_value FROM parts GROUP BY aisle ORDER BY aisle;",
    orderMatters: true,
  },
  {
    title: "Real Estate: Average Rent by Neighborhood",
    description:
      "For neighborhoods with at least 2 listings, show the average monthly rent rounded to 2 decimals, priciest first.",
    difficulty: "medium",
    mode: "read",
    sampleInput: [
      "| neighborhood | bedrooms | monthly_rent |",
      "| --- | --- | --- |",
      "| Old Town | 1 | 1200 |",
      "| Old Town | 2 | 1350 |",
      "| Riverside | 1 | 900 |",
      "| Hillcrest | 2 | 2000 |",
      "| Hillcrest | 3 | 2200 |",
    ],
    sampleOutput: "neighborhood | avg_rent\n---|---\nHillcrest | 2100.00\nOld Town | 1275.00",
    initSql: `
      CREATE TABLE listings (id SERIAL PRIMARY KEY, neighborhood TEXT, bedrooms INT, monthly_rent INT);
      INSERT INTO listings (neighborhood, bedrooms, monthly_rent) VALUES ('Old Town', 1, 1200), ('Old Town', 2, 1350), ('Riverside', 1, 900), ('Hillcrest', 2, 2000), ('Hillcrest', 3, 2200);
    `,
    solutionSql:
      "SELECT neighborhood, ROUND(AVG(monthly_rent), 2) as avg_rent FROM listings GROUP BY neighborhood HAVING COUNT(*) >= 2 ORDER BY avg_rent DESC;",
    orderMatters: true,
  },
  {
    title: "Music: Loyal Listeners",
    description:
      "Find listeners who have spun at least 3 different tracks.",
    difficulty: "hard",
    mode: "read",
    sampleInput: [
      "| listener_name | track_id |",
      "| --- | --- |",
      "| Amy | 1 |",
      "| Amy | 2 |",
      "| Amy | 3 |",
      "| Bo | 1 |",
      "| Bo | 2 |",
      "| Cy | 4 |",
    ],
    sampleOutput: "listener_name\n---\nAmy",
    initSql: `
      CREATE TABLE tracks2 (id SERIAL PRIMARY KEY, title TEXT);
      CREATE TABLE spins (id SERIAL PRIMARY KEY, listener_name TEXT, track_id INT REFERENCES tracks2(id));
      INSERT INTO tracks2 (title) VALUES ('Night Bus'), ('Glass House'), ('Static Bloom'), ('Paper Sun');
      INSERT INTO spins (listener_name, track_id) VALUES ('Amy', 1), ('Amy', 2), ('Amy', 3), ('Amy', 1), ('Bo', 1), ('Bo', 2), ('Cy', 4), ('Cy', 4);
    `,
    solutionSql:
      "SELECT listener_name FROM spins GROUP BY listener_name HAVING COUNT(DISTINCT track_id) >= 3;",
    orderMatters: false,
  },
  {
    title: "Airline: One-Stop Connections from Aster",
    description:
      "Using a self-join on routes, find cities reachable from Aster with exactly one stopover.",
    difficulty: "hard",
    mode: "read",
    sampleInput: [
      "| from_city | to_city |",
      "| --- | --- |",
      "| Aster | Bex |",
      "| Aster | Cora |",
      "| Bex | Dell |",
      "| Cora | Dell |",
      "| Cora | Elm |",
      "| Dell | Fay |",
    ],
    sampleOutput: "to_city\n---\nDell\nElm",
    initSql: `
      CREATE TABLE routes (id SERIAL PRIMARY KEY, from_city TEXT, to_city TEXT);
      INSERT INTO routes (from_city, to_city) VALUES ('Aster', 'Bex'), ('Aster', 'Cora'), ('Bex', 'Dell'), ('Cora', 'Dell'), ('Cora', 'Elm'), ('Dell', 'Fay');
    `,
    solutionSql:
      "SELECT DISTINCT r2.to_city FROM routes r1 JOIN routes r2 ON r1.to_city = r2.from_city WHERE r1.from_city = 'Aster' AND r2.to_city <> 'Aster' ORDER BY r2.to_city;",
    orderMatters: true,
  },
  {
    title: "Bank: Heavy Senders",
    description:
      "Find senders whose transfers add up to more than 10000, with their totals, biggest first.",
    difficulty: "hard",
    mode: "read",
    sampleInput: [
      "| sender_acct | amount |",
      "| --- | --- |",
      "| AC-77 | 8000.00 |",
      "| AC-77 | 6500.00 |",
      "| AC-31 | 9000.00 |",
      "| AC-31 | 2200.00 |",
      "| AC-09 | 4000.00 |",
      "| AC-09 | 1500.00 |",
    ],
    sampleOutput: "sender_acct | total_sent\n---|---\nAC-77 | 14500.00\nAC-31 | 11200.00",
    initSql: `
      CREATE TABLE transfers (id SERIAL PRIMARY KEY, sender_acct TEXT, amount DECIMAL(12,2));
      INSERT INTO transfers (sender_acct, amount) VALUES ('AC-77', 8000.00), ('AC-77', 6500.00), ('AC-31', 9000.00), ('AC-31', 2200.00), ('AC-09', 4000.00), ('AC-09', 1500.00);
    `,
    solutionSql:
      "SELECT sender_acct, SUM(amount) as total_sent FROM transfers GROUP BY sender_acct HAVING SUM(amount) > 10000 ORDER BY total_sent DESC;",
    orderMatters: true,
  },
  {
    title: "Cinema: Clear Unclaimed Past Reservations",
    description:
      "Delete reservations for dates before 2024-03-01 that were never claimed.",
    difficulty: "medium",
    mode: "write",
    sampleInput: [
      "| film_title | reserved_for | claimed |",
      "| --- | --- | --- |",
      "| Paper Moons | 2024-02-20 | false |",
      "| Harbor Nights | 2024-02-25 | false |",
      "| Dust Trails | 2024-03-10 | false |",
      "| Paper Moons | 2024-02-18 | true |",
    ],
    sampleOutput: "Successfully deleted 2 rows.",
    initSql: `
      CREATE TABLE reservations (id SERIAL PRIMARY KEY, film_title TEXT, seats INT, reserved_for DATE, claimed BOOLEAN);
      INSERT INTO reservations (film_title, seats, reserved_for, claimed) VALUES ('Paper Moons', 2, '2024-02-20', false), ('Harbor Nights', 4, '2024-02-25', false), ('Dust Trails', 2, '2024-03-10', false), ('Paper Moons', 3, '2024-02-18', true);
    `,
    solutionSql:
      "DELETE FROM reservations WHERE reserved_for < '2024-03-01' AND claimed = false;",
    validationSql: "SELECT COUNT(*) FROM reservations;",
    orderMatters: true,
  },
  {
    title: "Gym: Deactivate Lapsed Trials",
    description:
      "Set active to false for every trial membership that ended before 2024-05-01.",
    difficulty: "easy",
    mode: "write",
    sampleInput: [
      "| full_name | trial_ends | active |",
      "| --- | --- | --- |",
      "| Kim | 2024-04-20 | true |",
      "| Lou | 2024-04-28 | true |",
      "| Pam | 2024-05-10 | true |",
    ],
    sampleOutput: "Trials deactivated for lapsed members.",
    initSql: `
      CREATE TABLE trial_members (id SERIAL PRIMARY KEY, full_name TEXT, trial_ends DATE, active BOOLEAN);
      INSERT INTO trial_members (full_name, trial_ends, active) VALUES ('Kim', '2024-04-20', true), ('Lou', '2024-04-28', true), ('Pam', '2024-05-10', true);
    `,
    solutionSql:
      "UPDATE trial_members SET active = false WHERE trial_ends < '2024-05-01';",
    validationSql:
      "SELECT full_name FROM trial_members WHERE active = true ORDER BY full_name;",
    orderMatters: true,
  },
  {
    title: "Pet Shelter: Record an Adoption",
    description:
      "Mark the pet named 'Miso' as adopted.",
    difficulty: "medium",
    mode: "write",
    sampleInput: [
      "| pet_name | species | adopted |",
      "| --- | --- | --- |",
      "| Miso | cat | false |",
      "| Biscuit | dog | false |",
      "| Pip | rabbit | true |",
    ],
    sampleOutput: "Adoption recorded for Miso.",
    initSql: `
      CREATE TABLE shelter_pets (id SERIAL PRIMARY KEY, pet_name TEXT, species TEXT, adopted BOOLEAN);
      INSERT INTO shelter_pets (pet_name, species, adopted) VALUES ('Miso', 'cat', false), ('Biscuit', 'dog', false), ('Pip', 'rabbit', true);
    `,
    solutionSql: "UPDATE shelter_pets SET adopted = true WHERE pet_name = 'Miso';",
    validationSql:
      "SELECT adopted FROM shelter_pets WHERE pet_name = 'Miso';",
    orderMatters: false,
  },
  {
    title: "Warehouse: Book an Incoming Shipment",
    description:
      "Insert the newly arrived shipment of 150 units under SKU 'W-500' into stock.",
    difficulty: "easy",
    mode: "write",
    sampleInput: [
      "| sku | qty |",
      "| --- | --- |",
      "| W-100 | 40 |",
      "| W-200 | 75 |",
    ],
    sampleOutput: "Shipment booked: 1 row inserted.",
    initSql: `
      CREATE TABLE stock (id SERIAL PRIMARY KEY, sku TEXT, qty INT);
      INSERT INTO stock (sku, qty) VALUES ('W-100', 40), ('W-200', 75);
    `,
    solutionSql: "INSERT INTO stock (sku, qty) VALUES ('W-500', 150);",
    validationSql: "SELECT qty FROM stock WHERE sku = 'W-500';",
    orderMatters: false,
  },
  {
    title: "Bank: Post Monthly Interest",
    description:
      "Grow every savings balance of 1000 or more by its own rate_pct percentage. Leave smaller balances untouched.",
    difficulty: "hard",
    mode: "write",
    sampleInput: [
      "| holder_name | balance | rate_pct |",
      "| --- | --- | --- |",
      "| Ann | 5000.00 | 2.00 |",
      "| Ben | 800.00 | 2.00 |",
      "| Cara | 12000.00 | 1.50 |",
    ],
    sampleOutput:
      "holder_name | balance\n---|---\nAnn | 5100.00\nBen | 800.00\nCara | 12180.00",
    initSql: `
      CREATE TABLE savings (id SERIAL PRIMARY KEY, holder_name TEXT, balance DECIMAL(12,2), rate_pct DECIMAL(5,2));
      INSERT INTO savings (holder_name, balance, rate_pct) VALUES ('Ann', 5000.00, 2.00), ('Ben', 800.00, 2.00), ('Cara', 12000.00, 1.50);
    `,
    solutionSql:
      "UPDATE savings SET balance = balance * (1 + rate_pct / 100) WHERE balance >= 1000;",
    validationSql:
      "SELECT holder_name, balance FROM savings ORDER BY holder_name;",
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
