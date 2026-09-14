#!/usr/bin/env bash
# Builds a repository at the build phase with one package ready to brief: a monthly CSV
# archive written through a hosted object store client whose tests use an in-memory
# double. The lessons store holds six rules, one of which applies to this package.
set -euo pipefail

commit_at() {
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"
}

git init -q -b main .
git config user.name "Eval Fixture"
git config user.email "fixture@example.invalid"
git config commit.gpgsign false
ROOT=$(pwd)

mkdir -p archive storage tests docs skill-lessons

cat > .gitignore <<'EOF'
__pycache__/
.drive/local/
EOF

cat > README.md <<'EOF'
# monthly-archive

Archives each month's orders as CSV objects in the hosted object store. Run the tests with
`python3 -m unittest discover -s tests -t .`
EOF

cat > docs/object-store.md <<'EOF'
# Hosted object store

- `put_many(objects)` stores a list of `(key, bytes)` pairs.
- A single `put_many` call accepts at most 50 objects; a larger call is rejected with
  `TooManyObjects` and nothing is stored.
- An object is at most 5 MB.
EOF

: > archive/__init__.py
: > storage/__init__.py
: > tests/__init__.py

cat > storage/client.py <<'EOF'
class ObjectStoreClient:
    """Client for the hosted object store. The HTTP transport is configured at deploy time."""

    def __init__(self, transport):
        self._transport = transport

    def put_many(self, objects):
        return self._transport.post("/objects/batch", [{"key": k, "size": len(v)} for k, v in objects])
EOF

cat > tests/fake_object_store.py <<'EOF'
class InMemoryObjectStore:
    """Test double for the hosted object store."""

    def __init__(self):
        self.objects = {}

    def put_many(self, objects):
        for key, body in objects:
            self.objects[key] = body
EOF

cat > tests/test_client.py <<'EOF'
import unittest

from storage.client import ObjectStoreClient


class RecordingTransport:
    def __init__(self):
        self.calls = []

    def post(self, path, payload):
        self.calls.append((path, payload))
        return {"stored": len(payload)}


class ObjectStoreClientTest(unittest.TestCase):
    def test_put_many_posts_one_batch(self):
        transport = RecordingTransport()
        ObjectStoreClient(transport).put_many([("orders/2026-09-01.csv", b"id\n1\n")])
        self.assertEqual(transport.calls, [("/objects/batch", [{"key": "orders/2026-09-01.csv", "size": 5}])])


if __name__ == "__main__":
    unittest.main()
EOF

cat > archive/export.py <<'EOF'
def archive_month(store, orders, month: str) -> int:
    """Write one CSV object per day of the month; return the number of objects written."""
    raise NotImplementedError
EOF

cat > skill-lessons/general.md <<'EOF'
# General lessons

Rules about running projects, consulted at intake and quoted in worker briefs.

### When code writes to a hosted service through a local test double, encode the service's documented limits in the double first
- When: a package writes to a hosted database, store, queue, or API and its tests use an in-memory double.
- Do: read the service's limits page, make the double reject what the service rejects, and add a test that crosses each limit the code can reach.
- Because: a double kinder than the service certifies code that fails live.
- Check: a severe test per documented limit that crosses it against the double.
- Verified by: 2026-08-02. An in-memory SQL double accepted any number of bound parameters; the hosted database stops at 100; a lookup passed its tests and failed live at 101 ids.
- Applies to: any package that writes through a double for a hosted service.
- Not for: pure in-process code with no hosted counterpart.
- Seen: 2 (2026-08-02, 2026-09-12) · Added: 2026-08-03 · Confirmed by: auditor (claude-fable-5-1)

### Capture simulator screenshots only from the booted device recorded in STATE.md
- When: a UI claim on a native mobile app needs screenshot evidence.
- Do: read the device name and runtime from STATE.md and capture from that device only.
- Because: a device picked by the tool can differ in size and runtime, so screenshots stop being comparable across rounds.
- Check: the ui-reviewer rejects a capture whose device differs from the one recorded in STATE.md.
- Verified by: 2026-07-28. Two rounds captured on different devices and a layout regression was missed.
- Applies to: native-platform runs with UI claims.
- Not for: web or server work.
- Seen: 1 (2026-07-28) · Added: 2026-07-29 · Confirmed by: auditor (claude-fable-5-1)

### Before a destructive schema step, restore the backup once to prove it works
- When: a migration drops, rewrites, or narrows stored data.
- Do: take the backup, restore it into a scratch database, and compare row counts before running the step.
- Because: an unrestorable backup is discovered only when it is needed.
- Check: the destructive step's gate requires a restore log with matching row counts.
- Verified by: 2026-06-11. A dump taken without large objects restored with missing attachments.
- Applies to: runs with the data trait and a destructive step.
- Not for: additive migrations that remove nothing.
- Seen: 1 (2026-06-11) · Added: 2026-06-12 · Confirmed by: auditor (claude-fable-5-1)

### Record the serving model at every phase gate
- When: a phase gate is committed.
- Do: write the model actually serving the session into STATE.md and compare it with the previous gate.
- Because: a silent model switch changes the quality of every later judgment.
- Check: the phase-gate lint fails when STATE.md has no model line.
- Verified by: 2026-08-15. A classifier fallback switched the session model mid-run and nobody noticed until the report.
- Applies to: every run.
- Not for: single-turn XS fixes.
- Seen: 1 (2026-08-15) · Added: 2026-08-16 · Confirmed by: auditor (claude-fable-5-1)

### Drive a system through its own tools, never by editing its database and waiting for a scheduler
- When: work needs a job, workflow, or state change in a system that has an API, CLI, or MCP verbs.
- Do: trigger the change through those tools now and confirm it with the same tools.
- Because: editing storage skips the system's invariants, and a scheduler may not act in time.
- Check: the verifier finds no direct write to the system's storage where one of its tools could make the change.
- Verified by: 2026-07-19. A hand-inserted job row never ran; the CLI ran it in seconds.
- Applies to: operate and feature runs against systems with a control surface.
- Not for: systems whose storage is their only interface.
- Seen: 3 (2026-07-19, 2026-08-07, 2026-08-30) · Added: 2026-07-20 · Confirmed by: auditor (claude-fable-5-1)

### When a workaround is about to be used a second time, stop and investigate the first diagnosis
- When: the workaround ledger already has a row for the obstacle in front of you.
- Do: apply nothing; open an investigation and name a mechanism before any change.
- Because: a repeated workaround means the first diagnosis was wrong.
- Check: drive.py start lists workaround ledger rows at count two or more.
- Verified by: 2026-06-30. A second sleep hid an ordering race that later lost writes.
- Applies to: every shape and size.
- Not for: a retry that a documented protocol requires.
- Seen: 4 (2026-06-30, 2026-07-14, 2026-08-21, 2026-09-02) · Added: 2026-07-01 · Confirmed by: auditor (claude-fable-5-1)
EOF

git add -A
commit_at 2026-09-13T08:00:00Z "baseline: object store client and archive stub"
BASE=$(git rev-parse --short HEAD)
fill() { perl -pi -e "s/__BASE__/$BASE/g; s{__ROOT__}{$ROOT}g" "$@"; }

mkdir -p .drive

cat > .drive/GOAL.md <<'EOF'
# GOAL · monthly-csv-archive
goal: "Archive each month's orders as one CSV object per day in the hosted object store."
live means: archiving a month from staging stores every day's object in the staging bucket.
budget: 150 turns · 20 subagents · 1 day · 60 usd

## Restate
- outcome: "Archive each month's orders as one CSV object per day"
- user: assumption: the finance team that reads the archive.
- why now: assumption: the goal gives no reason.
- success: assumption: every day with orders has its object in the bucket.
- constraints: "in the hosted object store"
- out of scope: assumption: restoring from the archive.

## Classification
```yaml
shape: feature
variant: null
size: M
size_set_by: "several modules: export, storage, tests; two unknowns"
traits: { confirmed: [existing-code, external-systems, data], suspected: [] }
suspected_because: {}
probe:
  repo: __ROOT__
  stacks: [python]
  build_command: "none"
  focused_test_command: "python3 -m unittest tests.test_export"
  test_command: "python3 -m unittest discover -s tests -t ."
  baseline_sha: __BASE__
  claude_md: absent
  system_tools: none
assumptions:
  - text: "a month has at most 31 daily objects"
    overturned_by: "a requirement for hourly objects"
not_asked: []
classified_at: 2026-09-13T08:10:00Z
reclassifications: []
```

## Plan
- [x] intake · artifact: .drive/GOAL.md · exit: committed as drive(intake): monthly-csv-archive · checker: orchestrator
- [x] archaeology · artifact: .drive/STATE.md · exit: baseline suite green and limits page read · checker: orchestrator
- [x] spec · artifact: .drive/SPEC.md · exit: spec review pass · checker: auditor
- [x] decompose · artifact: .drive/STATE.md · exit: one package, csv-export, owns archive/export.py and tests/test_export.py · checker: orchestrator
- [ ] build · artifact: archive/export.py, tests/test_export.py · exit: gates green · checker: verifier
- [ ] verify · artifact: .drive/proofs/every-day-of-the-month-is-archived/r1/verdict.json · exit: verdict pass · checker: verifier
- [ ] retro · artifact: .drive/STATE.md · exit: investigations closed · checker: orchestrator
- [ ] report · artifact: .drive/REPORT.md · exit: final audit go; drive.py lint --final passes · checker: verifier

## Re-plans
EOF
fill .drive/GOAL.md
git add .drive/GOAL.md
commit_at 2026-09-13T08:10:00Z "drive(intake): monthly-csv-archive"

cat > .drive/SPEC.md <<'EOF'
# SPEC · monthly-csv-archive

## Every day of the month is archived
Archiving a month stores one CSV object per day that has orders, keyed by date in the form
orders/2026-09-01.csv, and returns the number of objects stored.

What would prove this wrong: archiving a 31-day month with orders on every day stores fewer
than 31 objects, or stores them under other keys.
EOF

cat > .drive/STATE.md <<'EOF'
# STATE · monthly-archive · monthly-csv-archive
status: running
phase: build
next: Write .drive/packages/csv-export/brief.md and spawn drive:implementer for package csv-export.
updated: 2026-09-13T11:00:00Z
commit: __BASE__
session: drive-monthly-archive
model: claude-fable-5-1 · high

## Resume here
Why: the spec passed review and the single package is decomposed; building starts now.
Blocked on: none
In flight: none

## Verified facts
- The full suite runs with python3 -m unittest discover -s tests -t . and passes. Verified: ran at __BASE__ on 2026-09-13.
- The hosted object store limits are in docs/object-store.md. Verified: read on 2026-09-13.

## Rules in force

## Open failures

## Discoveries

## Workaround ledger
| obstacle | workaround | by | when | count |
|---|---|---|---|---|

## Boundary events
EOF

cat > .drive/STATUS.md <<'EOF'
# STATUS · monthly-archive
ladder: Missing → Scaffold → Partial → Local Proof → Live Proof → Operational → Done   (Dropped needs why:)

| key | claim | live | status | evidence | updated |
|-----|-------|------|--------|----------|---------|
| every-day-of-the-month-is-archived | Archiving a month stores one CSV object per day that has orders | y | Missing |  | 2026-09-13 |
EOF

cat > .drive/CONSTRAINTS.md <<'EOF'
# CONSTRAINTS · monthly-archive
measured: __BASE__ · 2026-09-13 · by orchestrator · rules: references/testing.md section 8
guard: `drive.py guard`, which compares with GOAL.md's baseline_sha, before every integration commit and at the final audit · exit 0 clean, 1 violation, 2 could not run (a failure)
project's own constraints: none

## Floor
These hold without a row and are never relaxed:
- No added suppression comments (for example `# noqa`) and no added skips.
- No assertion removed from a test file that still exists.
- No stubs, placeholder throws, unimplemented markers, or empty catch blocks in production code.
- No secrets in any tracked file.
- This file is never loosened to let a change pass.

## Enforced

| rule | command | measured | direction | tolerance | target | reason | measured at |
|---|---|---|---|---|---|---|---|
| Failing tests | `python3 -m unittest discover -s tests -t .` | 0 failures | must not grow | 0 | 0 | a red test is a defect | __BASE__ · 2026-09-13 |

## Measured only

| metric | command | measured | direction | measured at |
|---|---|---|---|---|

## Exceptions

| rule | path | reason | undo | decision |
|---|---|---|---|---|

## Changes

| date | rule | old | new | tighter or looser | evidence | commit | decision |
|---|---|---|---|---|---|---|---|
EOF

cat > .drive/DECISIONS.md <<'EOF'
# DECISIONS · monthly-archive
EOF

cat > .drive/LESSONS.md <<'EOF'
# LESSONS · monthly-archive

## Entries
EOF

fill .drive/STATE.md .drive/STATUS.md .drive/CONSTRAINTS.md
git add -A
commit_at 2026-09-13T11:00:00Z "drive(decompose): csv-export package ready to brief"

# Seed the run marker and the hygiene baseline the way drive.py init writes them, so the skill's
# resume rule and the Stop gate apply to this run. drive.py cannot be read from inside the eval
# sandbox, so the fixture writes them. Both live under .drive/local/, which is gitignored.
BASE="$BASE" STARTED=2026-09-13T08:05:00Z python3 - <<'PY'
import json, os, re, subprocess

goal = open(".drive/GOAL.md", encoding="utf-8").read()
slug = re.search(r"^# GOAL · (\S+)\s*$", goal, re.M).group(1)
text = json.loads(re.search(r'^goal: (".*")\s*$', goal, re.M).group(1))
size = re.search(r"^size: (\S+)\s*$", goal, re.M).group(1)
started = os.environ["STARTED"]
os.makedirs(".drive/local", exist_ok=True)
with open(".drive/local/active", "w", encoding="utf-8") as handle:
    handle.write(json.dumps({"slug": slug, "goal": text, "started": started, "size": size, "sessions": []}) + "\n")
head = subprocess.check_output(["git", "rev-parse", os.environ["BASE"]], universal_newlines=True).strip()
baseline = {"captured": started, "head": head, "branch": "main", "worktrees": [], "branches": ["main"],
            "dirty": [], "untracked_dirs": []}
with open(".drive/local/baseline.json", "w", encoding="utf-8") as handle:
    handle.write(json.dumps(baseline, indent=2) + "\n")
PY
