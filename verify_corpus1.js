const fs = require("fs");
const vm = require("vm");
const { execFileSync } = require("child_process");

const src = fs.readFileSync("m_sql_studio/misc/seed.js", "utf8");
const start = src.indexOf("const ASSIGNMENTS = ");
const arrStart = src.indexOf("[", start);
let depth = 0, end = -1, inStr = false, strCh = "", esc = false, inTpl = false, inLine = false, inBlock = false;
for (let i = arrStart; i < src.length; i++) {
  const c = src[i], n = src[i + 1];
  if (inLine) { if (c === "\n") inLine = false; continue; }
  if (inBlock) { if (c === "*" && n === "/") { inBlock = false; i++; } continue; }
  if (inStr) {
    if (esc) esc = false;
    else if (c === "\\") esc = true;
    else if (c === strCh) inStr = false;
    continue;
  }
  if (inTpl) {
    if (esc) esc = false;
    else if (c === "\\") esc = true;
    else if (c === "`") inTpl = false;
    continue;
  }
  if (c === "/" && n === "/") { inLine = true; i++; continue; }
  if (c === "/" && n === "*") { inBlock = true; i++; continue; }
  if (c === '"' || c === "'") { inStr = true; strCh = c; continue; }
  if (c === "`") { inTpl = true; continue; }
  if (c === "[") depth++;
  if (c === "]") { depth--; if (depth === 0) { end = i + 1; break; } }
}
const list = vm.runInNewContext(src.slice(arrStart, end));

console.log("TOTAL:", list.length);
const diffs = {}, modes = {}, domains = {};
for (const a of list) {
  diffs[a.difficulty] = (diffs[a.difficulty] || 0) + 1;
  modes[a.mode] = (modes[a.mode] || 0) + 1;
  const dom = a.title.split(":")[0];
  domains[dom] = (domains[dom] || 0) + 1;
  for (const f of ["title", "description", "difficulty", "mode", "sampleInput", "sampleOutput", "initSql", "solutionSql", "orderMatters"]) {
    if (a[f] === undefined || a[f] === null || a[f] === "") { console.log("MISSING FIELD", f, "in", a.title); process.exitCode = 1; }
  }
  if (!Array.isArray(a.sampleInput) || a.sampleInput.length < 1) { console.log("BAD sampleInput", a.title); process.exitCode = 1; }
  if (!["easy", "medium", "hard"].includes(a.difficulty)) { console.log("BAD difficulty", a.title); process.exitCode = 1; }
  if (!["read", "write"].includes(a.mode)) { console.log("BAD mode", a.title); process.exitCode = 1; }
  if (a.mode === "write" && !a.validationSql) { console.log("WRITE WITHOUT validationSql", a.title); process.exitCode = 1; }
}
console.log("difficulty:", JSON.stringify(diffs));
console.log("mode:", JSON.stringify(modes));
console.log("domains (" + Object.keys(domains).length + "):", JSON.stringify(domains));

const env = { ...process.env, PGPASSWORD: "devpostgres" };
const psql = (db, sql) => execFileSync("psql", ["-h", "localhost", "-U", "postgres", "-d", db, "-v", "ON_ERROR_STOP=1", "-q", "-c", sql], { env, encoding: "utf8", timeout: 30000 });

let fail = 0;
list.forEach((a, i) => {
  const schema = "c" + i;
  try {
    psql("corpus1_verify", `CREATE SCHEMA IF NOT EXISTS ${schema};`);
    psql("corpus1_verify", `SET search_path TO ${schema}; ${a.initSql}`);
    const out = psql("corpus1_verify", `SET search_path TO ${schema}; ${a.solutionSql}`);
    if (a.validationSql) psql("corpus1_verify", `SET search_path TO ${schema}; ${a.solutionSql}; ${a.validationSql}`);
    console.log(`OK [${i}] ${a.title} :: solution ran, output bytes=${out.length}`);
  } catch (e) {
    fail++;
    console.log(`FAIL [${i}] ${a.title}\n${String(e.message || e).slice(0, 800)}`);
  } finally {
    try { psql("corpus1_verify", `SET search_path TO public; DROP SCHEMA ${schema} CASCADE;`); } catch (e) { /* ignore */ }
  }
});
console.log(fail === 0 ? "ALL SQL VERIFIED" : `FAILURES: ${fail}`);
process.exitCode = fail === 0 ? (process.exitCode || 0) : 1;
