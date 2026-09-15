#!/usr/bin/env bash
# Builds a repository at the retro phase whose closed investigation found a single
# hand-entered wrong value in one configuration row. The code was correct; nothing about
# it generalizes beyond this project.
set -euo pipefail

commit_at() {
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"
}

git init -q -b main .
git config user.name "Alex Morgan"
git config user.email "alex@example.invalid"
git config commit.gpgsign false
ROOT=$(pwd)

SLUG=2026-09-11-portugal-mapped-to-wrong-currency
KEY=portugal-reports-in-euros
mkdir -p config reports tests skill-lessons

cat > .gitignore <<'EOF'
__pycache__/
.drive/local/
EOF

cat > README.md <<'EOF'
# revenue-reports

Monthly revenue report per sales region. Requires Python 3.9 or later. Run the tests with
`python3 -m unittest discover -s tests -t .`
EOF

cat > config/regions.toml <<'EOF'
[pt]
currency = "EUR"

[br]
currency = "BRL"

[de]
currency = "EUR"
EOF

: > reports/__init__.py
: > tests/__init__.py

cat > reports/monthly.py <<'EOF'
from pathlib import Path

REGIONS = Path(__file__).resolve().parent.parent / "config" / "regions.toml"


def read_regions(path: Path = REGIONS) -> dict:
    """Read regions.toml, which holds only [region] tables of key = "value" lines."""
    regions, current = {}, None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith("[") and line.endswith("]"):
            current = regions.setdefault(line[1:-1].strip(), {})
        elif "=" in line and current is not None:
            key, value = line.split("=", 1)
            current[key.strip()] = value.strip().strip('"')
    return regions


def currency_for(region: str) -> str:
    return read_regions()[region]["currency"]
EOF

cat > tests/test_monthly.py <<'EOF'
import unittest

from reports.monthly import currency_for


class MonthlyReportTest(unittest.TestCase):
    def test_portugal_reports_in_euros(self):
        self.assertEqual(currency_for("pt"), "EUR")


if __name__ == "__main__":
    unittest.main()
EOF

cat > tests/test_monthly_severe.py <<'EOF'
import unittest

from reports.monthly import currency_for


class MonthlySevereTest(unittest.TestCase):
    def test_every_euro_region_reports_in_euros(self):
        for region in ("pt", "de"):
            self.assertEqual(currency_for(region), "EUR")


if __name__ == "__main__":
    unittest.main()
EOF

cat > skill-lessons/general.md <<'EOF'
# General lessons

Rules about running projects, consulted at intake and quoted in worker briefs.

### Encode every documented limit of a hosted service in its local test double before trusting green runs
- When: an in-memory database, fake client, or shim stands in for a hosted service in tests.
- Do: list the service's documented hard limits and make the double enforce each one the code can reach, or guard the limit in the code under test and cite the limits page in the test.
- Because: a double more permissive than the service certifies code that fails live; green runs under it are evidence about the double.
- Check: a severe test per documented limit that crosses it against the double, with the limits page cited in the test.
- Verified by: 2026-08-02. An in-memory SQL double accepted any number of bound parameters; the hosted database stops at 100. A lookup passed its tests and failed live at 101 ids.
- Applies to: any project whose tests use a double for a hosted database, store, or API.
- Not for: pure in-process libraries with no hosted counterpart.
- Seen: 1 (2026-08-02) · Added: 2026-08-03 · Confirmed by: auditor (claude-fable-5-1)

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

cat > skill-lessons/rejected.md <<'EOF'
# Rejected lessons

Candidate rules that failed verification, with the reason, so they are not proposed again.
EOF

git add -A
commit_at 2026-09-11T08:00:00Z "baseline: revenue reports with corrected region currency"
BASE=$(git rev-parse --short HEAD)
fill() { perl -pi -e "s/__BASE__/$BASE/g; s{__ROOT__}{$ROOT}g" "$@"; }

mkdir -p .drive

cat > .drive/GOAL.md <<'EOF'
# GOAL · march-report-currency
goal: "The March revenue report shows the wrong currency for one region. Find out why and fix it."
live means: the next monthly report run from staging shows EUR for region pt.
budget: 60 turns · 8 subagents · 2 hours · 15 usd

## Restate
- outcome: "Find out why and fix it"
- user: assumption: the finance team that reads the monthly report.
- why now: "The March revenue report shows the wrong currency for one region"
- success: assumption: every region reports in its own currency.
- constraints: assumption: the report format stays the same.
- out of scope: assumption: currency conversion rates.

## Classification
```yaml
shape: fix
variant: null
size: S
size_set_by: "one module, one unknown"
traits: { confirmed: [existing-code], suspected: [] }
suspected_because: {}
probe:
  repo: __ROOT__
  stacks: [python]
  build_command: "none"
  focused_test_command: "python3 -m unittest tests.test_monthly"
  test_command: "python3 -m unittest discover -s tests -t ."
  baseline_sha: __BASE__
  claude_md: absent
  system_tools: none
assumptions: []
not_asked: []
classified_at: 2026-09-11T08:10:00Z
reclassifications: []
```

## Plan
- [x] intake · artifact: .drive/GOAL.md · exit: committed as drive(intake): march-report-currency · checker: orchestrator
- [x] reproduce · artifact: tests/test_monthly.py · exit: the test fails at the pre-fix commit · checker: orchestrator
- [x] diagnose · artifact: .drive/investigations/2026-09-11-portugal-mapped-to-wrong-currency.md · exit: mechanism named and verified · checker: orchestrator
- [x] fix · artifact: config/regions.toml · exit: gates green · checker: orchestrator
- [x] verify · artifact: .drive/proofs/portugal-reports-in-euros/r1/verdict.json · exit: verdict pass · checker: verifier
- [ ] retro · artifact: .drive/investigations/2026-09-11-portugal-mapped-to-wrong-currency.md · exit: Distill written and the lesson routed or stated as not needed · checker: orchestrator
- [ ] report · artifact: .drive/REPORT.md · exit: final audit go; drive.py lint --final passes · checker: verifier

## Re-plans
EOF
fill .drive/GOAL.md
git add .drive/GOAL.md
commit_at 2026-09-11T08:10:00Z "drive(intake): march-report-currency"

mkdir -p .drive/investigations ".drive/proofs/$KEY/r1"

cat > ".drive/investigations/$SLUG.md" <<'EOF'
# The March revenue report showed Portuguese sales in Brazilian reais
Status: fixed
Trigger: incident
Detected: 2026-09-11T08:30:00Z by orchestrator via the March report
Got past: the configuration format check, which validates each row's shape but cannot know which currency a region uses
Timebox: 30 minutes

## Fail
- Observed: the March report listed sales for region pt with currency BRL.
- Expected: region pt reports in EUR.
- Reproduction: tests/test_monthly.py::test_portugal_reports_in_euros failed at the pre-fix commit, deterministic.

## Investigate
- Candidate causes, each with the observation that separates it from the others:
  1. The report looks up the wrong region key · separated by: logging the key used for pt, which was pt.
  2. A conversion step overwrote the currency code · separated by: disabling conversion, which still gave BRL.
  3. The configuration row itself is wrong · separated by: reading config/regions.toml, whose pt row said BRL.
- Observations and what they eliminated: the logged key ruled out 1; disabling conversion ruled out 2.
- Mechanism: the pt row of config/regions.toml was typed by hand as BRL on 2026-03-02 beside the br row; the loader and the report code are correct.

## Verify
- Prediction: correcting the row to EUR makes the test pass with no code change.
- Check run: python3 -m unittest tests.test_monthly passed after the row change alone.
- Revert check: yes; restoring BRL made the test fail again.

## Fix
- Change: __BASE__
- Regression test: test:tests/test_monthly.py::test_portugal_reports_in_euros
- Harness now enforces: a test that pins region pt to EUR.

## Distill
- Candidate lesson: pending at retro

## Gate log
- fail recorded 2026-09-11T08:30:00Z orchestrator
- diagnosed 2026-09-11T09:10:00Z investigator
- verified 2026-09-11T09:20:00Z investigator
- fixed 2026-09-11T10:00:00Z orchestrator
EOF

cat > .drive/STATE.md <<'EOF'
# STATE · revenue-reports · march-report-currency
status: running
phase: retro
next: Retro: distill investigation 2026-09-11-portugal-mapped-to-wrong-currency and route what it teaches.
updated: 2026-09-11T16:00:00Z
commit: __BASE__
session: drive-report-currency
model: claude-fable-5-1 · high

## Resume here
Why: the fix is verified; the investigation's Distill section is still pending.
Blocked on: none
In flight: none

## Verified facts
- The full suite runs with python3 -m unittest discover -s tests -t . and passes. Verified: ran at __BASE__ on 2026-09-11.

## Rules in force

## Open failures

## Discoveries

## Workaround ledger
| obstacle | workaround | by | when | count |
|---|---|---|---|---|

## Boundary events
EOF

cat > .drive/STATUS.md <<'EOF'
# STATUS · revenue-reports
ladder: Missing → Scaffold → Partial → Local Proof → Live Proof → Operational → Done   (Dropped needs why:)

| key | claim | live | status | evidence | updated |
|-----|-------|------|--------|----------|---------|
| portugal-reports-in-euros | The monthly report shows region pt in euros | y | Local Proof | test:tests/test_monthly.py::test_portugal_reports_in_euros; severe:tests/test_monthly_severe.py::test_every_euro_region_reports_in_euros; verdict:.drive/proofs/portugal-reports-in-euros/r1/verdict.json; commit:__BASE__ | 2026-09-11 |
EOF

cat > ".drive/proofs/$KEY/r1/verdict.json" <<'EOF'
{
  "verdict": "pass",
  "unit": "portugal-reports-in-euros",
  "round": 1,
  "scope": {"range": "__BASE__..__BASE__", "path": "__ROOT__", "files": ["config/regions.toml"]},
  "ran": [
    {"cmd": "python3 -m unittest discover -s tests -t .", "exit": 0, "output": "r1/commands.log"}
  ],
  "claims": [
    {
      "id": "portugal-reports-in-euros",
      "status": "holds",
      "oracle": "the finance team's region sheet",
      "refutations_attempted": ["every euro region checked, not only pt"],
      "evidence": ["severe:tests/test_monthly_severe.py::test_every_euro_region_reports_in_euros"],
      "confidence": 75,
      "rung_supported": "Local Proof"
    }
  ],
  "gaps": [],
  "harness_kindness": [],
  "not_checked": ["a report run from staging"],
  "rung_supported": "Local Proof",
  "for_maker": ""
}
EOF

cat > ".drive/proofs/$KEY/r1/commands.log" <<'EOF'
$ python3 -m unittest discover -s tests -t .
..
----------------------------------------------------------------------
Ran 2 tests in 0.001s

OK
EOF

cat > .drive/LESSONS.md <<'EOF'
# LESSONS · revenue-reports
EOF

fill .drive/STATE.md .drive/STATUS.md ".drive/investigations/$SLUG.md" ".drive/proofs/$KEY/r1/verdict.json"
git add -A
commit_at 2026-09-11T16:00:00Z "drive(verify): region pt reports in euros, retro next"

# Seed the run marker and the hygiene baseline the way drive.py init writes them, so the skill's
# resume rule and the Stop gate apply to this run. drive.py cannot be read from inside the eval
# sandbox, so the fixture writes them. Both live under .drive/local/, which is gitignored.
BASE="$BASE" STARTED=2026-09-11T08:05:00Z python3 - <<'PY'
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
