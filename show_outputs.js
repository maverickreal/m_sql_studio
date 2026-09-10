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
const env = { ...process.env, PGPASSWORD: "devpostgres" };
const psql = (db, sql) => execFileSync("psql", ["-h", "localhost", "-U", "postgres", "-d", db, "-v", "ON_ERROR_STOP=1", "-q", "-A", "-F", " | ", "-c", sql], { env, encoding: "utf8", timeout: 30000 });

// Only the 20 NEW items (index 5..24); for writes show validationSql result after solution
list.slice(5).forEach((a) => {
  const schema = "chk_" + a.title.replace(/[^a-z0-9]+/gi, "_").slice(0, 24);
  try {
    psql("corpus1_verify", `CREATE SCHEMA IF NOT EXISTS ${schema};`);
    psql("corpus1_verify", `SET search_path TO ${schema}; ${a.initSql}`);
    const q = a.mode === "write" ? `${a.solutionSql}; ${a.validationSql}` : a.solutionSql;
    const out = psql("corpus1_verify", `SET search_path TO ${schema}; ${q}`).trim();
    console.log(`=== ${a.title} [${a.mode}]`);
    console.log(out.split("\n").slice(0, 8).join("\n"));
  } catch (e) {
    console.log(`FAIL ${a.title}: ${String(e.message || e).slice(0, 300)}`);
  } finally {
    try { psql("corpus1_verify", `DROP SCHEMA ${schema} CASCADE;`); } catch (e) { /* ignore */ }
  }
});
