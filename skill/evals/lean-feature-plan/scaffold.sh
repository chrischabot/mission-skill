#!/usr/bin/env bash
# Builds a tiny standard-library web app with an admin accounts page, a SQLite
# schema holding accounts and sessions, and passing tests.
set -euo pipefail

git init -q -b main .
git config user.name "Alex Morgan"
git config user.email "alex@example.invalid"
git config commit.gpgsign false

mkdir -p app/templates tests

cat > .gitignore <<'EOF'
__pycache__/
*.db
.drive/local/
EOF

cat > README.md <<'EOF'
# accounts-admin

Internal admin site for the accounts service.

- `python3 -m app.server` serves the admin pages on http://127.0.0.1:8000
- Run the tests with `python3 -m unittest discover -s tests -t .`
EOF

: > app/__init__.py
: > tests/__init__.py

cat > app/db.py <<'EOF'
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    started_at TEXT NOT NULL
);
"""


def connect(path: str = "app.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
EOF

cat > app/queries.py <<'EOF'
def list_accounts(conn, limit=50):
    rows = conn.execute(
        "SELECT id, email, created_at FROM accounts ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    return [dict(row) for row in rows]
EOF

cat > app/views.py <<'EOF'
from pathlib import Path
from string import Template

TEMPLATES = Path(__file__).parent / "templates"


def render(name: str, **values) -> str:
    body = Template((TEMPLATES / name).read_text(encoding="utf-8")).substitute(values)
    layout = Template((TEMPLATES / "admin_layout.html").read_text(encoding="utf-8"))
    return layout.substitute(body=body)
EOF

cat > app/server.py <<'EOF'
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer

from app import db, queries, views


def accounts_page(conn) -> str:
    rows = "".join(
        f"<tr><td>{escape(account['email'])}</td><td>{escape(account['created_at'])}</td></tr>"
        for account in queries.list_accounts(conn)
    )
    return views.render("admin_accounts.html", rows=rows)


ROUTES = {"/admin/accounts": accounts_page}


def handle(path: str, conn) -> tuple[int, str]:
    page = ROUTES.get(path)
    if page is None:
        return 404, "not found"
    return 200, page(conn)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, body = handle(self.path, db.connect())
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
EOF

cat > app/templates/admin_layout.html <<'EOF'
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Admin</title></head>
<body>
  <nav><a href="/admin/accounts">Accounts</a></nav>
  <main>$body</main>
</body>
</html>
EOF

cat > app/templates/admin_accounts.html <<'EOF'
<h1>Accounts</h1>
<table>
  <thead><tr><th>Email</th><th>Created</th></tr></thead>
  <tbody>$rows</tbody>
</table>
EOF

cat > tests/test_server.py <<'EOF'
import unittest

from app import db
from app.server import handle


class AdminPagesTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        self.conn.execute(
            "INSERT INTO accounts (email, created_at) VALUES ('a@example.com', '2026-09-01T10:00:00Z')"
        )

    def test_accounts_page_lists_accounts(self):
        status, body = handle("/admin/accounts", self.conn)
        self.assertEqual(status, 200)
        self.assertIn("a@example.com", body)

    def test_unknown_path_is_not_found(self):
        self.assertEqual(handle("/nope", self.conn)[0], 404)


if __name__ == "__main__":
    unittest.main()
EOF

git add -A
git commit -q -m "baseline: admin accounts page"
