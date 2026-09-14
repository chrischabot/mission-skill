#!/usr/bin/env bash
# Builds an inventory store whose bulk lookup puts every id into one IN list. The
# connection enforces SQLite's 999 host-parameter limit, and the test picks a random
# count up to 1500, so it fails on roughly a third of runs with "too many SQL variables".
set -euo pipefail

git init -q -b main .
git config user.name "Eval Fixture"
git config user.email "fixture@example.invalid"
git config commit.gpgsign false

mkdir -p inventory tests

cat > .gitignore <<'EOF'
__pycache__/
.drive/local/
EOF

cat > README.md <<'EOF'
# inventory

Item lookups. Requires Python 3.9 or later. Run the tests with
`python3 -m unittest discover -s tests -t .`
EOF

: > inventory/__init__.py
: > tests/__init__.py

cat > inventory/db.py <<'EOF'
import sqlite3

MAX_HOST_PARAMETERS = 999  # matches the production database build


class LimitedCursor(sqlite3.Cursor):
    """Applies the production build's host-parameter limit on every Python version."""

    def execute(self, sql, parameters=()):
        if len(parameters) > MAX_HOST_PARAMETERS:
            raise sqlite3.OperationalError("too many SQL variables")
        return super().execute(sql, parameters)


class LimitedConnection(sqlite3.Connection):
    def cursor(self, factory=LimitedCursor):
        return super().cursor(factory)

    def execute(self, sql, parameters=()):
        return self.cursor().execute(sql, parameters)

    def executemany(self, sql, seq_of_parameters):
        return self.cursor().executemany(sql, seq_of_parameters)


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path, factory=LimitedConnection)
    conn.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    return conn
EOF

cat > inventory/store.py <<'EOF'
def get_many(conn, ids):
    """Return the items for the given ids, ordered by id."""
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"SELECT id, name FROM items WHERE id IN ({placeholders}) ORDER BY id", list(ids)
    )
    return [{"id": row[0], "name": row[1]} for row in rows]
EOF

cat > tests/test_store.py <<'EOF'
import random
import unittest

from inventory.db import connect
from inventory.store import get_many


class BulkLookupTest(unittest.TestCase):
    def setUp(self):
        self.conn = connect()
        self.conn.executemany(
            "INSERT INTO items (id, name) VALUES (?, ?)",
            [(i, f"item-{i}") for i in range(1, 2001)],
        )

    def test_single_lookup(self):
        self.assertEqual(get_many(self.conn, [7]), [{"id": 7, "name": "item-7"}])

    def test_bulk_lookup_returns_every_requested_item(self):
        count = random.randint(1, 1500)
        ids = random.sample(range(1, 2001), count)
        self.assertEqual([item["id"] for item in get_many(self.conn, ids)], sorted(ids))


if __name__ == "__main__":
    unittest.main()
EOF

git add -A
git commit -q -m "baseline: inventory bulk lookup"
