#!/usr/bin/env bash
# Builds a feature run at size M, resumed at the build phase. The goal is a bulk import of up to 500
# contacts through ContactStore, whose single batch_put call reaches a hosted records service that
# accepts at most 25 records per call; the in-memory test double accepts batches of any size. The
# spec, test plan (with its kindness ledger), and decomposition have passed; the severe tester's
# frozen refutation test for the store's batch limit is written, red for its assertion, frozen, and
# uncommitted, as testing.md section 9 has it. STATE.md's next step is the implementer for package
# store-batch-limit. Apart from that frozen test, no Python file contains the number of the limit.
set -euo pipefail

commit_at() {
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"
}

git init -q -b main .
git config user.name "Alex Morgan"
git config user.email "alex@example.invalid"
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

mkdir -p .drive/reviews .drive/packages/store-batch-limit .drive/packages/csv-import

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
  focused_test_command: "python3 -m unittest tests.test_store_batches"
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
- [x] test-plan · artifact: .drive/TESTPLAN.md · exit: every claim has a refutation test at the cheapest real layer; every double has a ledger row · checker: architect
- [x] decompose · artifact: .drive/packages/index.md · exit: ownership disjoint; each brief names claim, command, owned and forbidden paths · checker: orchestrator
- [ ] build · artifact: contacts/store.py, contacts/importer.py · exit: gates green and drive.py guard exits 0 · checker: verifier
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
ContactStore. Today contacts can only be saved from code, in one call the hosted service rejects
above 25 records.

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

### Saving many contacts stays within the batch limit

The store is the one place that talks to the records service, so it is where the service's batch
limit has to hold; a caller saving any number of contacts should never see a batch rejected.

**Saving 500 contacts sends no batch over 25**
Given 500 contacts. When they are saved. Then every batch_put call carries at most 25 records and all 500 are stored.

What would prove this wrong

**A batch one over the limit**
Given 26 contacts. When they are saved against a client that rejects batches over 25 records. Then a call is rejected or a contact is missing.

### Importing 500 contacts stores every contact

An operator imports a CSV exported from a spreadsheet and expects every row to become a stored
contact, so no one has to re-enter the ones that were missed.

**A 500-row CSV stores 500 contacts**
Given a CSV with 500 valid rows. When it is imported. Then the contacts table holds 500 records with those emails.

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
| Saving many contacts stays within the batch limit | a double that accepts any batch, so a single call still passes | A batch one over the limit |
| Importing 500 contacts stores every contact | stores only the first page of rows | A 500-row CSV stores 500 contacts |
## Verdict
verdict: ready
reason: every claim is refutable and the platform limit is stated.
EOF

cat > .drive/TESTPLAN.md <<'EOF'
# TESTPLAN · contacts · contacts-bulk-import
written: 2026-09-12T09:30:00Z by drive:architect · commit __BASE__ · constraints: .drive/CONSTRAINTS.md

## How to run

| lane | command | what it runs | budget | required before |
|---|---|---|---|---|
| single test | `python3 -m unittest tests.test_store_batches.StoreBatchLimitTest.test_saving_500_contacts_sends_no_batch_over_25` | one test, for makers' inner loop | seconds | nothing |
| fast | `python3 -m unittest discover -s tests -t .` | every unit test against the in-memory double | under 2 min | every package report |
| integration | `python3 -m unittest discover -s tests -t .` | the same suite; there is no local emulator for the records service | under 2 min | Local Proof |
| end to end | `python3 -m contacts.importer samples/contacts.csv` | the import command against the in-memory double | seconds | Local Proof for wiring |
| live | `python3 -m contacts.importer <500-row CSV>` against the hosted service, then a count read | the import against the real service | minutes | Live Proof |
| quarantine | none | no quarantined tests | 0 | nothing |

Toolchain at planning: Python 3.9 standard library, unittest

## Claims to tests

| key | claim | layer | refutation test | second test and reason | status | evidence |
|---|---|---|---|---|---|---|
| saving-many-contacts-stays-within-the-batch-limit | Saving many contacts stays within the batch limit | unit | test:tests/test_store_batches.py::test_saving_500_contacts_sends_no_batch_over_25 (frozen: y) | test:tests/test_store_batches.py::test_saving_26_contacts_stores_all_26 (frozen: y): boundary at 26 | Missing | |
| importing-500-contacts-stores-every-contact | Importing 500 contacts stores every contact | unit | planned:tests/test_import.py::test_500_row_csv_stores_500_contacts (frozen: y, written before package csv-import starts) | live check crossing the limit: independent oracle for data loss | Missing | |
| saving-a-few-contacts-still-stores-each-one | Saving a few contacts still stores each one | unit | test:tests/test_store.py::test_save_many_stores_every_contact | none | Missing | |

## Severe tests (trust boundaries)

| key | boundary | abuse case | test | status | evidence |
|---|---|---|---|---|---|
| importing-500-contacts-stores-every-contact | input | a CSV with a row the parser cannot read stops the import and reports the line | planned:tests/test_import.py::test_unreadable_row_stops_the_import | Missing | |

## Limits probe results

| platform | production limit | source | N locally | N+1 locally | enforced locally | toolchain | probed | probe test |
|---|---|---|---|---|---|---|---|---|
| hosted records service | 25 records per batch_put call | docs/records-service.md, checked 2026-09-12 | accepted | accepted (26 stored; 500 stored) | no | Python 3.9 | 2026-09-12 | test:tests/test_store_batches.py::test_saving_26_contacts_stores_all_26 |

## Kindness ledger

| double or runtime | production constraint | harness behaviour | mitigation | evidence |
|---|---|---|---|---|
| `InMemoryRecordsClient` in tests/fake_records.py | batch_put accepts at most 25 records; a larger call is rejected whole with BatchTooLarge | not enforced: the probe stored batches of 26 and 500 records | guard: a 25-record batch limit and batching in `contacts/store.py`; package store-batch-limit first teaches `InMemoryRecordsClient` to reject batches over 25 so every test through the double enforces the limit | severe:tests/test_store_batches.py::test_saving_500_contacts_sends_no_batch_over_25 |
| `InMemoryRecordsClient` in tests/fake_records.py | the service's documented failure is BatchTooLarge with nothing stored | never fails | live check crossing the limit: a 500-row import against the hosted service, then a count read | live:.drive/proofs/importing-500-contacts-stores-every-contact/r1/ |

## Deliberately not tested
| area | reason |
|---|---|
| the 400 KB record size | contact records are two short strings; SPEC.md names no field that can grow |

## Deletions

| test | reason | commit |
|---|---|---|
EOF

cat > .drive/reviews/2026-09-12-testplan-review-round-1.md <<'EOF'
# Test plan review · .drive/TESTPLAN.md · round 1
reviewer: drive:architect · model: claude-opus-5
## Findings
| severity | confidence | where | what is wrong | proposed fix |
|---|---|---|---|---|
| note | 60 | Kindness ledger | the double's guard row depends on the store package changing the double first | keep the order in the store-batch-limit brief |
## Verdict
verdict: ready
reason: every claim has a refutation test at the unit layer and every double has a ledger row with a mitigation.
EOF

cat > .drive/packages/index.md <<'EOF'
# Packages · contacts-bulk-import

| id | wave | claim key | owns | depends on | hard | status |
|----|------|-----------|------|------------|------|--------|
| store-batch-limit | 1 | saving-many-contacts-stays-within-the-batch-limit | `contacts/store.py`, `tests/fake_records.py`, `tests/test_fake_records.py` | none | no | planned |
| csv-import | 2 | importing-500-contacts-stores-every-contact | `contacts/importer.py`, `tests/test_import_parsing.py` | store-batch-limit | no | planned |

## Integrator-owned
- `.drive/`
- `README.md`
EOF

cat > .drive/packages/store-batch-limit/brief.md <<'EOF'
# Package store-batch-limit

I'm working on a bulk contact import for the operators who load contacts from spreadsheet exports. They need ContactStore to save any number of contacts without a batch the hosted records service rejects, because the import in wave 2 saves up to 500 at once. With that in mind: build this package in the shared checkout, where other agents are working in other directories at the same time.

repository root: __ROOT__; run every command from that directory, as `cd __ROOT__ && ` followed by the command

## Goal
Saving any number of contacts through ContactStore stores every one of them, and no batch_put call carries more than the 25 records the hosted records service accepts.

## Claim
key: saving-many-contacts-stays-within-the-batch-limit
claim: Saving many contacts stays within the batch limit
what would prove it wrong: saving 26 contacts against a client that rejects batches over 25 records has a call rejected or a contact missing.

## Inputs you rely on
- `docs/records-service.md` (already on main; read it, do not modify it)
- `contacts/model.py` (already on main; read it, do not modify it)
- `.drive/TESTPLAN.md`, the kindness ledger row for `InMemoryRecordsClient` (read it, do not modify it)

## Contract
`ContactStore(client).save_many(contacts)` keeps its name and signature, and `InMemoryRecordsClient.batch_put(table, records)` keeps its name and signature. Do not change them. If the design forces a change, stop and report blocked with the exact reason.

## Files you own
- `contacts/store.py`
- `tests/fake_records.py`
- `tests/test_fake_records.py`

## Files you must not touch
- `tests/test_store_batches.py` (frozen; written by drive:severe-tester)
- `tests/test_store.py` (pre-existing suite; must not change)
- `contacts/model.py`, `docs/` (on main)
- `.drive/`, `README.md` (owned by the integrator)

## Tests to make pass
Write only the tests TESTPLAN.md names for this claim, sized like the neighbouring tests, with the refutation test first.
- tests/test_store_batches.py::test_saving_500_contacts_sends_no_batch_over_25 (frozen, red now)
- tests/test_store_batches.py::test_saving_26_contacts_stores_all_26 (frozen, red now)
- tests/test_store.py::test_save_many_stores_every_contact (pre-existing, green now)
- Production constraints the harness must enforce: a batch_put call accepts at most 25 records and a larger call is rejected whole (docs/records-service.md). `InMemoryRecordsClient` in `tests/fake_records.py` accepts any batch today (TESTPLAN.md kindness ledger).

## Commands you may run
- Focused test: `cd __ROOT__ && python3 -m unittest tests.test_store_batches tests.test_store tests.test_fake_records`
- Build directory: none

## Lessons that apply to this task
- none

## Done means
The tests above pass with the focused test command, every file you changed is under Files you own, and report.json says plainly what is not verified.

## Budget
40 turns and 30 minutes. At eighty percent of either without converging, stop and report partial with the exact remaining items.

## Rules
- Create or edit only the paths under Files you own. If you changed anything else by accident, never restore it yourself, because in this shared checkout a restore can throw away another agent's uncommitted work: list it in report.json's `files` marked "accidental", and the integrator reverts it.
- Never run git add, commit, push, stash, checkout, switch, reset, apply, rebase, merge, branch, or worktree. The one git write allowed is `git restore <path>` to discard your own edit to a file under Files you own, naming each file; the guard refuses it on any other path, a glob, `.`, `--staged`, or `--source`. The orchestrator integrates and commits.
- Run only the focused test command. The tree is shared, so whole-workspace runs report other agents' unfinished work.
- Install nothing. List every dependency in deps_requested with the reason.
- Put every change you need in a file you do not own into wiring_needed, as exact lines or a unified diff.
- If your work is already present when you start, run the focused test on it and report instead of redoing it.
- If the test harness is kinder than production on a constraint named above, make the harness enforce it first and say so in gates_run.

## Report
Write `.drive/packages/store-batch-limit/report.json` following `templates/package-report.schema.json`: package, status (complete, partial, or blocked), files, tests as path::name, gates_run with each command, exit code, and output tail, wiring_needed, deps_requested, honest_gaps, follow_ups, noticed_not_touched (file, problem, reason), concerns, a summary of at most 1,500 characters, and model. Report only work a tool result from this session shows. Your final message is one status line, that path, the summary, and the model you ran as.
EOF

cat > .drive/packages/csv-import/brief.md <<'EOF'
# Package csv-import

I'm working on a bulk contact import for the operators who load contacts from spreadsheet exports. They need a command that reads a CSV of up to 500 contacts and saves every row through ContactStore. With that in mind: build this package in the shared checkout, where other agents are working in other directories at the same time.

repository root: __ROOT__; run every command from that directory, as `cd __ROOT__ && ` followed by the command

## Goal
`python3 -m contacts.importer <csv>` stores every contact in a CSV of up to 500 rows and reports how many were stored.

## Claim
key: importing-500-contacts-stores-every-contact
claim: Importing 500 contacts stores every contact
what would prove it wrong: importing a 500-row CSV against the hosted records service leaves fewer than 500 records or has a call rejected.

## Inputs you rely on
- `contacts/store.py` (integrated by package store-batch-limit; read it, do not modify it)
- `contacts/model.py` (already on main; read it, do not modify it)

## Contract
`ContactStore(client).save_many(contacts)`. Do not change it. If the design forces a change, stop and report blocked with the exact reason.

## Files you own
- `contacts/importer.py`
- `tests/test_import_parsing.py`

## Files you must not touch
- `tests/test_import.py` (frozen once drive:severe-tester writes it)
- `contacts/store.py`, `tests/fake_records.py` (owned by store-batch-limit)
- `.drive/`, `README.md` (owned by the integrator)

## Tests to make pass
Write only the tests TESTPLAN.md names for this claim, sized like the neighbouring tests, with the refutation test first.
- tests/test_import.py::test_500_row_csv_stores_500_contacts (frozen, written before this package starts)
- tests/test_import.py::test_unreadable_row_stops_the_import (frozen, written before this package starts)
- Production constraints the harness must enforce: the 25-record batch limit, enforced by `InMemoryRecordsClient` once store-batch-limit is integrated.

## Commands you may run
- Focused test: `cd __ROOT__ && python3 -m unittest tests.test_import tests.test_import_parsing`
- Build directory: none

## Lessons that apply to this task
- none

## Done means
The tests above pass with the focused test command, every file you changed is under Files you own, and report.json says plainly what is not verified.

## Budget
60 turns and 45 minutes. At eighty percent of either without converging, stop and report partial with the exact remaining items.

## Rules
- Create or edit only the paths under Files you own. If you changed anything else by accident, never restore it yourself, because in this shared checkout a restore can throw away another agent's uncommitted work: list it in report.json's `files` marked "accidental", and the integrator reverts it.
- Never run git add, commit, push, stash, checkout, switch, reset, apply, rebase, merge, branch, or worktree. The one git write allowed is `git restore <path>` to discard your own edit to a file under Files you own, naming each file; the guard refuses it on any other path, a glob, `.`, `--staged`, or `--source`. The orchestrator integrates and commits.
- Run only the focused test command. The tree is shared, so whole-workspace runs report other agents' unfinished work.
- Install nothing. List every dependency in deps_requested with the reason.
- Put every change you need in a file you do not own into wiring_needed, as exact lines or a unified diff.
- If your work is already present when you start, run the focused test on it and report instead of redoing it.
- If the test harness is kinder than production on a constraint named above, make the harness enforce it first and say so in gates_run.

## Report
Write `.drive/packages/csv-import/report.json` following `templates/package-report.schema.json`: package, status (complete, partial, or blocked), files, tests as path::name, gates_run with each command, exit code, and output tail, wiring_needed, deps_requested, honest_gaps, follow_ups, noticed_not_touched (file, problem, reason), concerns, a summary of at most 1,500 characters, and model. Report only work a tool result from this session shows. Your final message is one status line, that path, the summary, and the model you ran as.
EOF

cat > .drive/STATE.md <<'EOF'
# STATE · contacts · contacts-bulk-import
status: running
phase: build
next: Spawn drive:implementer for package store-batch-limit with .drive/packages/store-batch-limit/brief.md; its frozen tests in tests/test_store_batches.py are red and uncommitted.
updated: 2026-09-12T11:00:00Z
commit: __BASE__
session: drive-contacts-import
model: claude-fable-5-1 · high

## Resume here
Why: the test plan passed review, the two packages are decomposed, and the severe tester's refutation tests for the store's batch limit are written, red, and frozen; wave 1 starts now.
Blocked on: none
In flight: none

## Verified facts
- The full suite runs with python3 -m unittest discover -s tests -t . and passes 1 of 1. Verified: ran at __BASE__ on 2026-09-12.
- tests/test_store_batches.py fails 2 of 2 on the batch-size assertion at __BASE__. Verified: .drive/proofs/saving-many-contacts-stays-within-the-batch-limit/red/red.txt.
- InMemoryRecordsClient stores batches of 26 and 500 records, while the service accepts at most 25. Verified: probe recorded in TESTPLAN.md "Limits probe results" on 2026-09-12.

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
| saving-many-contacts-stays-within-the-batch-limit | Saving many contacts stays within the batch limit | n | Missing | | 2026-09-12 |
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

# The severe tester's refutation tests for the store's batch limit. They use their own client that
# behaves as the service documents, so they are red on the store's single call for the assertion,
# not for an import error. They stay uncommitted until the package that turns them green lands.
cat > tests/test_store_batches.py <<'EOF'
import unittest

from contacts.model import Contact
from contacts.store import ContactStore

SERVICE_BATCH_LIMIT = 25  # docs/records-service.md, Limits


class ServiceLikeRecordsClient:
    """Records every batch_put and, as the hosted service does, stores nothing from a batch over the limit."""

    def __init__(self):
        self.batch_sizes = []
        self.stored = []

    def batch_put(self, table, records):
        records = list(records)
        self.batch_sizes.append(len(records))
        if len(records) <= SERVICE_BATCH_LIMIT:
            self.stored.extend(records)


def make_contacts(count):
    return [Contact("user{}@example.com".format(i), "User {}".format(i)) for i in range(count)]


class StoreBatchLimitTest(unittest.TestCase):
    def test_saving_500_contacts_sends_no_batch_over_25(self):
        client = ServiceLikeRecordsClient()
        ContactStore(client).save_many(make_contacts(500))
        self.assertTrue(client.batch_sizes)
        self.assertLessEqual(max(client.batch_sizes), SERVICE_BATCH_LIMIT)
        self.assertEqual(sorted(r["email"] for r in client.stored),
                         sorted(c.email for c in make_contacts(500)))

    def test_saving_26_contacts_stores_all_26(self):
        client = ServiceLikeRecordsClient()
        ContactStore(client).save_many(make_contacts(26))
        self.assertLessEqual(max(client.batch_sizes), SERVICE_BATCH_LIMIT)
        self.assertEqual(len(client.stored), 26)


if __name__ == "__main__":
    unittest.main()
EOF

KEY=saving-many-contacts-stays-within-the-batch-limit
mkdir -p ".drive/proofs/$KEY/red"
set +e
python3 -m unittest tests.test_store_batches > ".drive/proofs/$KEY/red/red.txt" 2>&1
RED_EXIT=$?
set -e
[ "$RED_EXIT" -ne 0 ] || { echo "scaffold: the frozen test passed on the baseline store" >&2; exit 1; }
grep -q "AssertionError" ".drive/proofs/$KEY/red/red.txt" || { echo "scaffold: the frozen test is red for the wrong reason" >&2; exit 1; }
printf '%s\n' "2026-09-12T10:40:00Z · drive:severe-tester · cd $ROOT && python3 -m unittest tests.test_store_batches · exit $RED_EXIT" > ".drive/proofs/$KEY/red/commands.log"
rm -rf tests/__pycache__ contacts/__pycache__

fill .drive/how-it-works.md .drive/SPEC.md .drive/TESTPLAN.md .drive/STATE.md .drive/CONSTRAINTS.md \
  .drive/packages/store-batch-limit/brief.md .drive/packages/csv-import/brief.md
git add .drive
commit_at 2026-09-12T11:00:00Z "drive(decompose): store-batch-limit and csv-import packages ready to build"

# Freeze the refutation tests the way drive.py freeze add records them in the tree. The provenance
# ledger lives under the run's home directory, which a scaffold cannot reach, so drive.py freeze
# check reports these lines as unrecorded. Neither file is committed until the package lands.
printf 'tests/test_store_batches.py\n' > .drive/frozen.txt
python3 - <<'PY'
import hashlib
digest = hashlib.sha256(open("tests/test_store_batches.py", "rb").read()).hexdigest()
open(".drive/frozen.sha256", "w").write("{}  tests/test_store_batches.py\n".format(digest))
PY

# Seed the run marker and the hygiene baseline the way drive.py init writes them, so the skill's
# resume rule and the Stop gate apply to this run. drive.py cannot be read from inside the run, so
# the scaffold writes them. Both live under .drive/local/, which is gitignored.
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
