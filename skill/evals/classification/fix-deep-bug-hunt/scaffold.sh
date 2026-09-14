#!/usr/bin/env bash
# Builds a small time-tracking ledger whose weekly bucketing attaches the author's
# offset without converting the time, so late Sunday entries land in the wrong week.
set -euo pipefail

git init -q -b main .
git config user.name "Eval Fixture"
git config user.email "fixture@example.invalid"
git config commit.gpgsign false

mkdir -p ledger tests

cat > .gitignore <<'EOF'
__pycache__/
.drive/local/
EOF

cat > README.md <<'EOF'
# ledger

Time tracking with a weekly totals report.

- `python3 -m ledger.report export.json` prints hours per ISO week.
- Run the tests with `python3 -m unittest discover -s tests -t .`
EOF

: > ledger/__init__.py
: > tests/__init__.py

cat > ledger/weekly.py <<'EOF'
"""Weekly totals for the time-tracking ledger."""
from datetime import datetime, timedelta, timezone


def week_key(timestamp: float, utc_offset_minutes: int) -> str:
    """Return the ISO week, as YYYY-Www, that an entry belongs to for its author."""
    moment = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    local = moment.replace(tzinfo=timezone(timedelta(minutes=utc_offset_minutes)))
    year, week, _ = local.isocalendar()
    return f"{year}-W{week:02d}"


def weekly_totals(entries):
    """Sum logged minutes per ISO week in each author's own time zone."""
    totals = {}
    for entry in entries:
        key = week_key(entry["timestamp"], entry["utc_offset_minutes"])
        totals[key] = totals.get(key, 0) + entry["minutes"]
    return totals
EOF

cat > ledger/report.py <<'EOF'
"""Prints weekly totals for a ledger export."""
import json
import sys

from ledger.weekly import weekly_totals


def main(path: str) -> None:
    with open(path, encoding="utf-8") as handle:
        entries = json.load(handle)
    for week, minutes in sorted(weekly_totals(entries).items()):
        print(f"{week}\t{minutes / 60:.1f}h")


if __name__ == "__main__":
    main(sys.argv[1])
EOF

cat > tests/test_weekly.py <<'EOF'
import unittest
from datetime import datetime, timezone

from ledger.weekly import week_key, weekly_totals


def ts(*args):
    return datetime(*args, tzinfo=timezone.utc).timestamp()


class WeeklyTotalsTest(unittest.TestCase):
    def test_midweek_entries_share_a_week(self):
        entries = [
            {"timestamp": ts(2026, 3, 11, 12, 0), "utc_offset_minutes": 60, "minutes": 30},
            {"timestamp": ts(2026, 3, 12, 9, 0), "utc_offset_minutes": 60, "minutes": 45},
        ]
        self.assertEqual(weekly_totals(entries), {"2026-W11": 75})

    def test_week_key_format(self):
        self.assertEqual(week_key(ts(2026, 1, 7, 12, 0), 0), "2026-W02")


if __name__ == "__main__":
    unittest.main()
EOF

git add -A
git commit -q -m "baseline: weekly totals report"
