#!/usr/bin/env python3
"""Live :8000 proof. Does not print secrets. Writes JSON results to stdout."""
from __future__ import annotations

import http.cookiejar
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path("/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio")
ENV = ROOT / ".env"
BASE = "http://127.0.0.1:8000"


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


class Session:
    def __init__(self, origin: str):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj)
        )
        self.origin = origin

    def req(self, method: str, path: str, body=None, headers=None):
        h = {
            "Origin": self.origin,
            "Content-Type": "application/json",
        }
        if headers:
            h.update(headers)
        data = None if body is None else json.dumps(body).encode()
        r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
        try:
            with self.opener.open(r, timeout=20) as resp:
                raw = resp.read().decode()
                return resp.status, raw, json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            raw = e.read().decode()
            try:
                parsed = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                parsed = {"_text": raw[:300]}
            return e.code, raw, parsed


def main() -> int:
    env = load_env(ENV)
    origin = env.get("CLIENT_URL", "http://localhost:3000")
    admin_email = env["DEFAULT_ADMIN_EMAIL"]
    admin_password = env["DEFAULT_ADMIN_PASSWORD"]
    admin_secret = env.get("ADMIN_SECRET_CODE", "definitely-not-the-secret")
    results = []

    def rec(name, ok, detail):
        results.append({"name": name, "ok": bool(ok), "detail": detail})
        print(("PASS" if ok else "FAIL"), name, detail)

    unauth = Session(origin)
    st, _, body = unauth.req("GET", "/api/v1/admin/audit")
    rec("unauth GET /admin/audit", st == 401, f"status={st}")
    st, _, _ = unauth.req("GET", "/api/v1/admin/users")
    rec("unauth GET /admin/users", st == 401, f"status={st}")

    admin = Session(origin)
    st, _, body = admin.req(
        "POST",
        "/api/auth/sign-in/email",
        {"email": admin_email, "password": admin_password},
    )
    role = (body or {}).get("user", {}).get("role") if isinstance(body, dict) else None
    rec("admin sign-in", st in (200, 201) and role == "admin", f"status={st} role={role}")

    st, _, users = admin.req("GET", "/api/v1/admin/users")
    rec("admin GET /users", st == 200 and isinstance(users, dict) and "items" in users, f"status={st} keys={list(users)[:6] if isinstance(users, dict) else type(users)}")

    st, _, assigns = admin.req("GET", "/api/v1/admin/assignments")
    rec("admin GET /assignments", st == 200 and isinstance(assigns, dict), f"status={st}")

    stamp = str(int(time.time()))
    payload = {
        "title": f"slice8-proof-{stamp}",
        "description": "cto live proof assignment",
        "difficulty": "easy",
        "mode": "read",
        "sampleInput": ["id"],
        "sampleOutput": "1",
        "initSql": "CREATE TABLE t (id int); INSERT INTO t VALUES (1);",
        "orderMatters": False,
    }
    st, _, created = admin.req("POST", "/api/v1/admin/assignments", payload)
    created_id = None
    if isinstance(created, dict):
        created_id = created.get("_id") or created.get("id") or (created.get("assignment") or {}).get("_id")
    rec("admin POST assignment", st in (200, 201), f"status={st} id={created_id}")

    user_email = f"slice8user{stamp}@example.test"
    user = Session(origin)
    st, raw_signup, signed = user.req(
        "POST",
        "/api/auth/sign-up/email",
        {
            "email": user_email,
            "password": "Userpass-12345",
            "name": "Slice8 User",
            "adminSecret": admin_secret,
        },
    )
    uobj = signed.get("user") if isinstance(signed, dict) else None
    if not isinstance(uobj, dict):
        uobj = {}
    urole = uobj.get("role")
    uid = uobj.get("id") or uobj.get("_id")
    rec("signup keys", True, f"status={st} top={list(signed)[:8] if isinstance(signed, dict) else type(signed)}")
    st_s, _, sess = user.req("GET", "/api/auth/get-session")
    if isinstance(sess, dict) and isinstance(sess.get("user"), dict):
        uid = uid or sess["user"].get("id") or sess["user"].get("_id")
        urole = urole or sess["user"].get("role")
        rec("user session", True, f"status={st_s} role={urole} id_set={bool(uid)}")
    else:
        rec("user session", False, f"status={st_s}")
    rec(
        "signup+adminSecret does not grant admin",
        st in (200, 201) and urole != "admin",
        f"status={st} role={urole}",
    )

    st, _, _ = user.req("GET", "/api/v1/admin/audit")
    rec("non-admin GET /audit", st == 403, f"status={st}")
    st, _, _ = user.req("POST", f"/api/v1/admin/users/{uid or 'x'}/role", {"role": "admin"})
    rec("non-admin setRole", st in (401, 403), f"status={st}")

    if uid:
        st, _, _ = admin.req("POST", f"/api/v1/admin/users/{uid}/role", {"role": "admin"})
        rec("admin promote user", st in (200, 201), f"status={st}")
        st, _, _ = admin.req("POST", f"/api/v1/admin/users/{uid}/role", {"role": "user"})
        rec("admin demote user", st in (200, 201), f"status={st}")
    else:
        rec("admin promote user", False, "no user id from signup")
        rec("admin demote user", False, "no user id from signup")

    st, _, audit = admin.req("GET", "/api/v1/admin/audit?limit=20")
    actions = []
    items = []
    if isinstance(audit, dict):
        items = audit.get("items") or audit.get("rows") or []
        actions = [i.get("action") for i in items if isinstance(i, dict)]
    rec(
        "audit has assignment.create",
        st == 200 and "assignment.create" in actions,
        f"status={st} actions={actions[:8]}",
    )
    rec(
        "audit has role.change",
        st == 200 and "role.change" in actions,
        f"status={st} n={len(items)}",
    )

    st, raw, catalog = unauth.req("GET", "/api/v1/assignments?page=1&limit=2")
    keys = list(catalog) if isinstance(catalog, dict) else []
    rec(
        "catalog envelope total/totalPages",
        st == 200
        and isinstance(catalog, dict)
        and "total" in catalog
        and "totalPages" in catalog,
        f"status={st} keys={keys}",
    )
    st, _, bad = unauth.req("GET", "/api/v1/assignments?page=0")
    rec("catalog page=0 is 400", st == 400, f"status={st}")
    st, _, filt = unauth.req("GET", "/api/v1/assignments?filter[difficulty]=easy&limit=5")
    rec("catalog filter difficulty", st == 200, f"status={st}")
    st, _, q = unauth.req("GET", "/api/v1/assignments?q=slice8-proof&limit=5")
    rec("catalog search q", st == 200, f"status={st}")
    st, _, srt = unauth.req("GET", "/api/v1/assignments?sort=title&order=asc&limit=5")
    rec("catalog sort title asc", st == 200, f"status={st}")
    st, _, badf = unauth.req("GET", "/api/v1/assignments?filter[nope]=x")
    rec("unknown filter 400", st == 400, f"status={st}")

    ui = urllib.request.urlopen("http://127.0.0.1:3000/admin", timeout=10)
    html = ui.read().decode("utf-8", "replace")
    rec("GET :3000/admin serves SPA", ui.status == 200 and "<div" in html.lower() or "root" in html.lower(), f"status={ui.status} len={len(html)}")

    failed = [r for r in results if not r["ok"]]
    out = ROOT / "docs/specs/_live_proof_results.json"
    out.write_text(json.dumps({"failed": len(failed), "results": results}, indent=2))
    print("SUMMARY", f"pass={len(results)-len(failed)} fail={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
