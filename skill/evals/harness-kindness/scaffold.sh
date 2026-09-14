#!/usr/bin/env bash
# Builds a feature run at size M, resumed at the test-plan phase. The goal is a bulk import of up
# to 500 contacts through ContactStore, whose single batch_put call reaches a hosted records
# service that accepts at most 25 records per call; the in-memory test double accepts batches of
# any size, so tests of a 500-contact import would pass and fail live. The spec has passed review
# and names the platform limit; TESTPLAN.md does not exist yet. No Python file in the baseline
# contains the number of the limit.
set -euo pipefail

commit_at() {
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"
}

git init -q -b main .
git config user.name "Eval Fixture"
git config user.email "fixture@example.invalid"
git config commit.gpgsign false
ROOT=$(pwd)

mkdir -p contacts tests docs samples

cat > .gitignore <<'EOF'
__pycache__/
.drive/local/
EOF

cat > README.md <<'EOF'
# contacts

Contact storage on the hosted records service. Run the tests with
`python3 -m unittest discover -s tests -t .`
EOF

cat > docs/records-service.md <<'EOF'
# Hosted records service

## batch_put(table, records)

Stores a list of records in a table.

## Limits

- A single `batch_put` call accepts at most 25 records. A call with more records is rejected with
  `BatchTooLarge`, and none of its records are stored.
- A record is at most 400 KB.
EOF

cat > samples/contacts.csv <<'EOF'
email,name
ada@example.com,Ada
grace@example.com,Grace
linus@example.com,Linus
EOF

: > contacts/__init__.py
: > tests/__init__.py

cat > contacts/model.py <<'EOF'
from dataclasses import dataclass


@dataclass(frozen=True)
class Contact:
    email: str
    name: str

    def to_record(self) -> dict:
        return {"email": self.email, "name": self.name}
EOF

cat > contacts/store.py <<'EOF'
class ContactStore:
    """Saves contacts through the hosted records service client."""

    def __init__(self, client):
        self._client = client

    def save_many(self, contacts):
        self._client.batch_put("contacts", [contact.to_record() for contact in contacts])
EOF

cat > tests/fake_records.py <<'EOF'
class InMemoryRecordsClient:
    """Test double for the hosted records service."""

    def __init__(self):
        self.tables = {}

    def batch_put(self, table, records):
        self.tables.setdefault(table, []).extend(records)
EOF

cat > tests/test_store.py <<'EOF'
import unittest

from contacts.model import Contact
from contacts.store import ContactStore
from tests.fake_records import InMemoryRecordsClient


class ContactStoreTest(unittest.TestCase):
    def test_save_many_stores_every_contact(self):
        client = InMemoryRecordsClient()
        contacts = [Contact("a@example.com", "A"), Contact("b@example.com", "B"), Contact("c@example.com", "C")]
        ContactStore(client).save_many(contacts)
        self.assertEqual(len(client.tables["contacts"]), 3)


if __name__ == "__main__":
    unittest.main()
EOF

git add -A
commit_at 2026-09-12T08:00:00Z "baseline: contact store"
BASE=$(git rev-parse --short HEAD)
fill() { perl -pi -e "s/__BASE__/$BASE/g; s{__ROOT__}{$ROOT}g" "$@"; }

mkdir -p .drive/reviews

cat > .drive/GOAL.md <<'EOF'
# GOAL · contacts-bulk-import
goal: "Add a bulk import that reads a CSV of up to 500 contacts and saves them through ContactStore."
live means: importing a 500-row CSV against the hosted records service stores 500 records, counted by a read.
budget: 150 turns · 20 subagents · 1 day · 60 usd

## Restate
- outcome: "a bulk import that reads a CSV of up to 500 contacts and saves them through ContactStore"
- user: assumption: operators loading contacts from a spreadsheet export.
- why now: assumption: the goal gives no reason.
- success: assumption: every contact in a CSV of up to 500 rows is stored.
- constraints: "through ContactStore"
- out of scope: assumption: deduplication and updates to existing contacts.

## Classification
```yaml
shape: feature
variant: null
size: M
size_set_by: "a new import module and a change to the store's write path, with an external service behind it"
traits: { confirmed: [existing-code, external-systems], suspected: [data] }
suspected_because: { data: "the import writes records to the hosted service" }
probe:
  repo: __ROOT__
  stacks: [python]
  build_command: "none"
  focused_test_command: "python3 -m unittest tests.test_import"
  test_command: "python3 -m unittest discover -s tests -t ."
  baseline_sha: __BASE__
  claude_md: absent
  system_tools: none
assumptions: []
not_asked: []
classified_at: 2026-09-12T08:10:00Z
reclassifications: []
```

## Plan
- [x] intake · artifact: .drive/GOAL.md · exit: committed as drive(intake): contacts-bulk-import · checker: orchestrator
- [x] archaeology · artifact: .drive/how-it-works.md · exit: full suite run with counts recorded · checker: orchestrator
- [x] spec · artifact: .drive/SPEC.md · exit: every claim refutable and in scope · checker: architect
- [ ] test-plan · artifact: .drive/TESTPLAN.md · exit: every claim has a refutation test at the cheapest real layer · checker: architect
- [ ] build · artifact: contacts/importer.py · exit: gates green and drive.py guard exits 0 · checker: verifier
- [ ] verify · artifact: .drive/proofs/importing-500-contacts-stores-every-contact/r1/verdict.json · exit: verdict pass · checker: verifier
- [ ] retro · artifact: .drive/reviews/2026-09-12-retro.md · exit: investigations closed · checker: orchestrator
- [ ] report · artifact: .drive/REPORT.md · exit: final audit go; drive.py lint --final passes · checker: verifier

## Re-plans
EOF
fill .drive/GOAL.md
git add .drive/GOAL.md
commit_at 2026-09-12T08:10:00Z "drive(intake): contacts-bulk-import"

cat > .drive/how-it-works.md <<'EOF'
# How it works · contacts · bulk import
checked at: __BASE__ on 2026-09-12 · by: drive:researcher (claude-sonnet-5)
re-check: `git log __BASE__..HEAD -- contacts tests docs`

## Purpose
Contacts are stored through a client for a hosted records service; there is no import yet. [read contacts/store.py:1]

## Architecture
`ContactStore.save_many` turns contacts into records and sends them in one `batch_put` call. Tests use
`InMemoryRecordsClient` in place of the service client. [read contacts/store.py:7] [read tests/fake_records.py:1]

## Verified commands
| Job | Exact command | Result when run | Duration |
|---|---|---|---|
| build | none | no build step | 0 s |
| focused test | `python3 -m unittest tests.test_store` | ok | 0.1 s |
| full suite | `python3 -m unittest discover -s tests -t .` | 1/1, 0 failing, flaky: none | 0.1 s |
| lint | none | no linter configured | 0 s |
| typecheck | none | no type checker configured | 0 s |

Baseline: 1/1 at __BASE__; failing before any change: none.

## Dialect
| Aspect | Pattern | Nearest examples | Evidence |
|---|---|---|---|
| test location and naming | unittest classes in `tests/test_<module>.py` | `tests/test_store.py` | [read tests/test_store.py:7] |

## Data and external systems
| Store or system | Used for | Access path in code | How tests reach it (real, emulator, double) | Evidence |
|---|---|---|---|---|
| hosted records service | contact records | `ContactStore._client.batch_put` | double: `InMemoryRecordsClient` | [read tests/fake_records.py:1] [docs docs/records-service.md] |

## Drift table
| Claim | Where it is made | What actually happens | Evidence | Action |
|---|---|---|---|---|
| tests run with unittest discover | README.md:3 | they do | [ran `python3 -m unittest discover -s tests -t .`] | none |

## Blast radius
Score: small (small: one entry point and no external consumer)
| Change point | Depends on it | How found | Covered by real tests | Risk if it breaks |
|---|---|---|---|---|
| `ContactStore.save_many` | the new import | [ran `grep -rn save_many .`] | tests/test_store.py | contacts not stored |

## Could not verify
- The service's behaviour beyond its documentation: no credentials in this checkout · consequence: live rows wait for the owner's token

## Questions raised for research
- none
EOF

cat > .drive/SPEC.md <<'EOF'
# Contact bulk import · change spec
Version: 2026-09-12 · shape: feature · size: M · baseline: __BASE__ · latest review: .drive/reviews/2026-09-12-spec-review-round-1.md · changes: 0

## What changes and why
Operators can import a CSV of up to 500 contacts, and every contact in it is stored through
ContactStore. Today contacts can only be saved from code.

## Where it lands
- Files and modules: `contacts/importer.py` (new), `contacts/store.py`
- Interfaces and contracts touched: `ContactStore.save_many`, defined in `contacts/store.py`
- Data touched: the `contacts` table on the hosted records service, write

## Blast radius
Score: small, because the store has one caller and no external consumer

| change point | depends on it | how found | covered by real tests | risk if it breaks |
|---|---|---|---|---|
| `ContactStore.save_many` | the import | `grep -rn save_many .` | tests/test_store.py | contacts not stored |

## Dialect
| aspect | pattern to follow | nearest examples |
|---|---|---|
| test location and naming | unittest classes in `tests/test_<module>.py` | `tests/test_store.py` |

## Must not change

### Saving a few contacts still stores each one
Guarded by: test:tests/test_store.py::test_save_many_stores_every_contact
Measured baseline: not applicable

What would prove this wrong

**Three contacts saved leave three records**
Given an empty contacts table. When three contacts are saved. Then the table holds exactly those three records.

## Requirements

### Importing 500 contacts stores every contact

An operator imports a CSV exported from a spreadsheet and expects every row to become a stored
contact, so no one has to re-enter the ones that were missed.

**A 500-row CSV stores 500 contacts**
Given a CSV with 500 valid rows. When it is imported. Then the contacts table holds 500 records with those emails.

**A three-row CSV stores three contacts**
Given the sample CSV with three rows. When it is imported. Then the contacts table holds three records.

What would prove this wrong

**The records service sees the whole import**
Given a CSV with 500 valid rows. When it is imported against the hosted records service. Then all 500 records are stored and no call is rejected.

Failure behaviour: when the service rejects a call, the import stops, reports how many contacts were stored, and exits non-zero.

## Non-functional deltas
- An import of 500 contacts completes in under 30 seconds against the hosted service.

## Constraints
- A single batch_put call accepts at most 25 records, and a larger call is rejected whole. docs/records-service.md · checked 2026-09-12 · research: none, repository documentation

## Done means
- Proof: `python3 -m contacts.importer samples/contacts.csv` against the hosted records service, then a count read.
- Highest rung: Live Proof, because live means importing against the hosted service.
- The pre-existing suite at __BASE__ still passes with no test deleted, skipped, or loosened.

## Assumptions

### We assume a CSV has an email and a name column
Because: the sample export in samples/contacts.csv has exactly those columns.
Instead we could have: mapped arbitrary column names at import time.
To overturn: say "map columns by header". Before build this costs a few lines; after it costs a new option and its tests, because the parser is fixed.
Status: assumed 2026-09-12

## Risks
- Rows with invalid emails. Trigger: a row the parser cannot read. Response: the import reports the line and stops.

## Changes
EOF

cat > .drive/reviews/2026-09-12-spec-review-round-1.md <<'EOF'
# Spec review · .drive/SPEC.md · round 1
reviewer: drive:architect · model: claude-opus-5
## Findings
| severity | confidence | where | what is wrong | proposed fix |
|---|---|---|---|---|
| note | 50 | Non-functional deltas | the 30-second budget has no stated source | keep it as an assumption until measured |
## Cheat attempts
| requirement | implementation that passes and fails the user | caught by |
|---|---|---|
| Importing 500 contacts stores every contact | stores only the first page of rows | A 500-row CSV stores 500 contacts |
## Verdict
verdict: ready
reason: every claim is refutable and the platform limit is stated.
EOF

cat > .drive/STATE.md <<'EOF'
# STATE · contacts · contacts-bulk-import
status: running
phase: test-plan
next: Write TESTPLAN.md for the spec's claims with drive:architect, then build the import.
updated: 2026-09-12T11:00:00Z
commit: __BASE__
session: drive-contacts-import
model: claude-fable-5-1 · high

## Resume here
Why: the spec passed review; the test plan comes next.
Blocked on: none
In flight: none

## Verified facts
- The full suite runs with python3 -m unittest discover -s tests -t . and passes 1 of 1. Verified: ran at __BASE__ on 2026-09-12.

## Rules in force

## Open failures

## Discoveries

## Workaround ledger
| obstacle | workaround | by | when | count |
|---|---|---|---|---|

## Boundary events
EOF

cat > .drive/STATUS.md <<'EOF'
# STATUS · contacts
ladder: Missing → Scaffold → Partial → Local Proof → Live Proof → Operational → Done   (Dropped needs why:)

| key | claim | live | status | evidence | updated |
|-----|-------|------|--------|----------|---------|
| importing-500-contacts-stores-every-contact | Importing 500 contacts stores every contact | y | Missing | | 2026-09-12 |
| saving-a-few-contacts-still-stores-each-one | Saving a few contacts still stores each one | n | Missing | | 2026-09-12 |
EOF

cat > .drive/CONSTRAINTS.md <<'EOF'
# CONSTRAINTS · contacts
measured: __BASE__ · 2026-09-12 · by orchestrator · rules: references/testing.md section 8
guard: `drive.py guard` before every integration commit, and `drive.py guard --base __BASE__` at the final audit · exit 0 clean, 1 violation, 2 could not run (a failure)
project's own constraints: none

## Floor
These hold without a row and are never relaxed:
- No added suppression comments and no added skips.
- No assertion removed from a test file that still exists.
- No stubs, placeholder throws, unimplemented markers, or empty catch blocks in production code.
- No secrets in any tracked file.
- This file is never loosened to let a change pass.

## Enforced

| rule | command | measured | direction | tolerance | target | reason | measured at |
|---|---|---|---|---|---|---|---|
| Test suite passing | `python3 -m unittest discover -s tests -t .` | 1/1 | must not fall | 0 | all | a red test is a defect | __BASE__ · 2026-09-12 |

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
# DECISIONS · contacts
EOF

cat > .drive/LESSONS.md <<'EOF'
# LESSONS · contacts

## Entries
EOF

fill .drive/how-it-works.md .drive/SPEC.md .drive/STATE.md .drive/CONSTRAINTS.md
git add -A
commit_at 2026-09-12T11:00:00Z "spec: contacts-bulk-import passed review with 2 claims"

# Seed the run marker and the hygiene baseline the way drive.py init writes them, so the skill's
# resume rule and the Stop gate apply to this run. drive.py cannot be read from inside the eval
# sandbox, so the fixture writes them. Both live under .drive/local/, which is gitignored.
BASE="$BASE" STARTED=2026-09-12T08:05:00Z python3 - <<'PY'
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
