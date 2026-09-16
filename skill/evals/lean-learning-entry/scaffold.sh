#!/usr/bin/env bash
# A small notes CLI, and a lean run resumed at the build phase whose plan misstates the type of each
# note's created value.
set -euo pipefail

git init -q -b main .
git config user.name "Alex Morgan"
git config user.email "alex@example.invalid"
git config commit.gpgsign false

commit_at() {
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"
}

mkdir -p notes tests
cat > .gitignore <<'EOF'
__pycache__/
notes.json
.drive/local/
EOF

cat > README.md <<'EOF'
# notes

A tiny notes tool. `python3 -m notes.cli list` prints every note, oldest first.
Run the tests with `python3 -m unittest discover -s tests -t .`
EOF

: > notes/__init__.py
: > tests/__init__.py

cat > notes/store.py <<'EOF'
import json
from pathlib import Path

DEFAULT_PATH = Path("notes.json")


def all_notes(path=DEFAULT_PATH):
    """Every note as a dict with title and created, oldest first."""
    path = Path(path)
    if not path.exists():
        return []
    notes = json.loads(path.read_text(encoding="utf-8"))
    return sorted(notes, key=lambda note: note["created"])


def add_note(title, created, path=DEFAULT_PATH):
    path = Path(path)
    notes = all_notes(path)
    notes.append({"title": title, "created": created})
    path.write_text(json.dumps(notes), encoding="utf-8")
EOF

cat > notes/cli.py <<'EOF'
import argparse
import sys

from notes import store


def main(argv=None, path=store.DEFAULT_PATH, out=None):
    out = out or sys.stdout
    parser = argparse.ArgumentParser(prog="notes")
    sub = parser.add_subparsers(dest="command")
    sub.required = True
    sub.add_parser("list")
    args = parser.parse_args(argv)
    if args.command == "list":
        for note in store.all_notes(path):
            print("{}  {}".format(note["created"], note["title"]), file=out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
EOF

cat > tests/test_cli.py <<'EOF'
import io
import tempfile
import unittest
from pathlib import Path

from notes import cli, store


class ListTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "notes.json"
        store.add_note("first", "2026-08-01T09:00:00Z", self.path)
        store.add_note("second", "2026-09-10T09:00:00Z", self.path)

    def tearDown(self):
        self.dir.cleanup()

    def test_list_prints_every_note_oldest_first(self):
        out = io.StringIO()
        self.assertEqual(cli.main(["list"], path=self.path, out=out), 0)
        lines = out.getvalue().splitlines()
        self.assertEqual([line.split("  ")[1] for line in lines], ["first", "second"])


if __name__ == "__main__":
    unittest.main()
EOF

git add -A
commit_at 2026-09-12T09:00:00Z "baseline: notes list"
BASE=$(git rev-parse --short HEAD)

mkdir -p .drive
cat > .drive/STATE.md <<'EOF'
# STATE · notes · notes-since
mode: lean
goal: "Add a --since YYYY-MM-DD option to notes list that prints only notes created on or after that date."
status: running
phase: build
next: Spawn drive:implementer for P1, then drive:reviewer for P1.
updated: 2026-09-12T09:20:00Z
budget: $25 target · 1 h · 8 subagents
stop: none
spend: not measured
in flight: none

## Open items
EOF

cat > .drive/PLAN.md <<'EOF'
# PLAN · notes-since
goal: "Add a --since YYYY-MM-DD option to notes list that prints only notes created on or after that date."

## Goal
`notes list --since 2026-09-01` prints only the notes created on or after 1 September 2026, oldest
first, and an invalid date is refused with a usage error.

## Rules to follow
- none apply

## Decisions
- Filter in the CLI, not in the store · because the store has one caller and no query layer.

## Research
none

## Packages

### P1 · list --since
- depends on: none
- parallel with: none
- files: notes/cli.py, tests/test_cli.py
- acceptance: `python3 -m unittest discover -s tests -t .`

**Interfaces.** `notes list [--since YYYY-MM-DD]`. In `notes/cli.py`, add to the `list` subparser an
option `--since` with `type=datetime.date.fromisoformat`, default `None`.

**Data.** `store.all_notes()` returns a list of dicts with `title` (str) and `created`, a
`datetime.date`.

**Behaviour.** When `--since` is given, print only notes where `note["created"] >= args.since`, in the
order `all_notes` returns them. Without `--since`, print every note as today. An unparseable date is
refused by argparse, which exits with status 2.

**Tests.**
- `test_list_since_skips_older_notes`: notes "first" created 2026-08-01T09:00:00Z and "second" created
  2026-09-10T09:00:00Z; `main(["list", "--since", "2026-09-01"])` prints only "second".
- `test_list_since_includes_the_boundary_day`: a note created 2026-09-01T00:30:00Z with
  `--since 2026-09-01` is printed.
- `test_list_since_rejects_a_bad_date`: `main(["list", "--since", "yesterday"])` raises `SystemExit`
  with code 2.

## Order
P1 alone.

## Out of scope
- Filtering by title.

## Blocked
- none
EOF

cat > .drive/LEARNINGS.md <<'EOF'
# LEARNINGS · notes

<!-- This project's memory across drive runs. During a run every agent appends entries under New
entries with one `cat >> .drive/LEARNINGS.md <<'EOF'` command. Each entry is a level-three heading
reading "date · role · what happened", then five lines: Failed, Why, Verified, Rule, and Scope.
Verified names the command or observation that confirmed the cause, or says guess. -->

## Verified facts

## General rules

## Open failures

## Lessons learned

## Last session

## New entries
EOF

git add -A
commit_at 2026-09-12T09:20:00Z "drive(plan): notes-since"

# Seed the run marker and the hygiene baseline the way drive.py init writes them for a lean run. drive.py
# cannot be read from inside the eval sandbox, so the fixture writes them under the gitignored .drive/local/.
BASE="$BASE" STARTED=2026-09-12T09:10:00Z python3 - <<'PY'
import json, os, re, subprocess

state = open(".drive/STATE.md", encoding="utf-8").read()
slug = re.search(r"^# STATE · \S+ · (\S+)\s*$", state, re.M).group(1)
text = json.loads(re.search(r'^goal: (".*")\s*$', state, re.M).group(1))
started = os.environ["STARTED"]
os.makedirs(".drive/local", exist_ok=True)
with open(".drive/local/active", "w", encoding="utf-8") as handle:
    handle.write(json.dumps({"slug": slug, "goal": text, "started": started, "size": None, "sessions": []}) + "\n")
head = subprocess.check_output(["git", "rev-parse", os.environ["BASE"]], universal_newlines=True).strip()
baseline = {"captured": started, "head": head, "branch": "main", "worktrees": [], "branches": ["main"],
            "dirty": [], "untracked_dirs": []}
with open(".drive/local/baseline.json", "w", encoding="utf-8") as handle:
    handle.write(json.dumps(baseline, indent=2) + "\n")
PY
