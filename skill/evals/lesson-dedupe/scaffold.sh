#!/usr/bin/env bash
# Builds a repository at the retro phase. The closed investigation found a queue test
# double that accepted messages over the hosted queue's 256 KB limit. The lessons store
# already holds the general rule, worded around a SQL double, with Seen: 1.
set -euo pipefail

commit_at() {
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"
}

git init -q -b main .
git config user.name "Eval Fixture"
git config user.email "fixture@example.invalid"
git config commit.gpgsign false
ROOT=$(pwd)

SLUG=2026-09-12-queue-double-accepted-oversized-messages
KEY=large-orders-are-published
mkdir -p orders tests docs skill-lessons

cat > .gitignore <<'EOF'
__pycache__/
.drive/local/
EOF

cat > README.md <<'EOF'
# orders

Publishes order events to the hosted message queue. Run the tests with
`python3 -m unittest discover -s tests -t .`
EOF

cat > docs/queue-limits.md <<'EOF'
# Hosted queue limits

- A message body is at most 256 KB. Larger messages are rejected with `MessageTooLarge`.
EOF

: > orders/__init__.py
: > tests/__init__.py

cat > orders/publisher.py <<'EOF'
import json

MAX_MESSAGE_BYTES = 256 * 1024


def publish_order(queue, order: dict) -> int:
    """Publish an order as one or more messages, each under the queue's size limit."""
    header = {key: value for key, value in order.items() if key != "items"}
    batch, sent = [], 0
    for item in order["items"]:
        candidate = batch + [item]
        if batch and len(json.dumps({**header, "items": candidate}).encode()) > MAX_MESSAGE_BYTES:
            queue.send(json.dumps({**header, "items": batch}).encode())
            sent += 1
            candidate = [item]
        batch = candidate
    queue.send(json.dumps({**header, "items": batch}).encode())
    return sent + 1
EOF

cat > tests/fake_queue.py <<'EOF'
MAX_MESSAGE_BYTES = 256 * 1024


class MessageTooLarge(Exception):
    pass


class FakeQueue:
    """Test double for the hosted queue; enforces the documented message size limit."""

    def __init__(self):
        self.messages = []

    def send(self, body: bytes) -> None:
        if len(body) > MAX_MESSAGE_BYTES:
            raise MessageTooLarge(len(body))
        self.messages.append(body)
EOF

cat > tests/test_publisher.py <<'EOF'
import unittest

from orders.publisher import publish_order
from tests.fake_queue import FakeQueue


class PublisherTest(unittest.TestCase):
    def test_large_order_is_published(self):
        items = [{"sku": f"sku-{i}", "note": "x" * 300} for i in range(900)]
        queue = FakeQueue()
        sent = publish_order(queue, {"id": 5521, "items": items})
        self.assertGreater(sent, 1)
        self.assertEqual(len(queue.messages), sent)


if __name__ == "__main__":
    unittest.main()
EOF

cat > tests/test_publisher_severe.py <<'EOF'
import json
import unittest

from orders.publisher import publish_order
from tests.fake_queue import MAX_MESSAGE_BYTES, FakeQueue


class PublisherSevereTest(unittest.TestCase):
    def test_every_message_fits_the_queue_limit(self):
        items = [{"sku": f"sku-{i}", "note": "y" * 2000} for i in range(400)]
        queue = FakeQueue()
        publish_order(queue, {"id": 9, "items": items})
        self.assertTrue(all(len(message) <= MAX_MESSAGE_BYTES for message in queue.messages))
        restored = [item for message in queue.messages for item in json.loads(message)["items"]]
        self.assertEqual(restored, items)


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
- Verified by: 2026-08-02. An in-memory SQL double accepted any number of bound parameters; the hosted database stops at 100. A lookup passed its tests and failed live at 101 ids. Capping the double made the old test fail; chunking made it pass.
- Applies to: any project whose tests use a double for a hosted database, store, or API.
- Not for: pure in-process libraries with no hosted counterpart.
- Seen: 1 (2026-08-02) · Added: 2026-08-03 · Confirmed by: auditor (claude-fable-5-1)

### Drive a system through its own tools, never by editing its database and waiting for a scheduler
- When: work needs a job, workflow, or state change in a system that has an API, CLI, or MCP verbs.
- Do: load the system's tools at intake and trigger the change through them now; confirm the result with the same tools.
- Because: editing storage directly skips the system's invariants, and a scheduler may not pick the change up in the window that matters.
- Check: the verifier finds no direct write to the system's storage where one of its tools could make the change.
- Verified by: 2026-07-19. A job row inserted by hand never ran because the runner reads its own lease table; triggering through the CLI ran it in seconds.
- Applies to: operate and feature runs against systems with their own control surface.
- Not for: systems whose storage is their only interface.
- Seen: 3 (2026-07-19, 2026-08-07, 2026-08-30) · Added: 2026-07-20 · Confirmed by: auditor (claude-fable-5-1)

### When a workaround is about to be used a second time, stop and investigate the first diagnosis
- When: the workaround ledger already has a row for the obstacle in front of you.
- Do: apply nothing; open an investigation record and name a mechanism before any change.
- Because: a repeated workaround means the first diagnosis was wrong, and each repeat hides the cause further.
- Check: drive.py start lists workaround ledger rows at count two or more.
- Verified by: 2026-06-30. A second sleep added to a sync test hid an ordering race that later lost writes live; the investigation found the race between two named writers.
- Applies to: every shape and size.
- Not for: a retry that a documented protocol requires, such as an HTTP 429 with Retry-After.
- Seen: 4 (2026-06-30, 2026-07-14, 2026-08-21, 2026-09-02) · Added: 2026-07-01 · Confirmed by: auditor (claude-fable-5-1)
EOF

cat > skill-lessons/rejected.md <<'EOF'
# Rejected lessons

Candidate rules that failed verification, with the reason, so they are not proposed again.
EOF

git add -A
commit_at 2026-09-12T08:00:00Z "baseline: order publisher that splits large orders"
BASE=$(git rev-parse --short HEAD)
fill() { perl -pi -e "s/__BASE__/$BASE/g; s{__ROOT__}{$ROOT}g" "$@"; }

mkdir -p .drive

cat > .drive/GOAL.md <<'EOF'
# GOAL · publish-large-orders
goal: "Large orders are rejected by the queue in staging although every test passes. Find out why and fix it."
live means: an order with 900 line items published from staging is accepted by the hosted queue.
budget: 80 turns · 10 subagents · 3 hours · 25 usd

## Restate
- outcome: "Find out why and fix it"
- user: assumption: services that publish orders to the queue.
- why now: "Large orders are rejected by the queue in staging"
- success: assumption: a 900-item order is accepted in staging.
- constraints: assumption: the queue's documented limits stay as they are.
- out of scope: assumption: changes to the queue service.

## Classification
```yaml
shape: fix
variant: null
size: S
size_set_by: "one module, one unknown"
traits: { confirmed: [existing-code, external-systems], suspected: [] }
suspected_because: {}
probe:
  repo: __ROOT__
  stacks: [python]
  build_command: "none"
  focused_test_command: "python3 -m unittest tests.test_publisher"
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
- [x] intake · artifact: .drive/GOAL.md · exit: committed as drive(intake): publish-large-orders · checker: orchestrator
- [x] reproduce · artifact: tests/test_publisher.py · exit: the test fails against the old publisher · checker: orchestrator
- [x] diagnose · artifact: .drive/investigations/2026-09-12-queue-double-accepted-oversized-messages.md · exit: mechanism named and verified · checker: orchestrator
- [x] fix · artifact: orders/publisher.py, tests/fake_queue.py · exit: gates green · checker: orchestrator
- [x] verify · artifact: .drive/proofs/large-orders-are-published/r2/verdict.json · exit: verdict pass · checker: verifier
- [ ] retro · artifact: .drive/investigations/2026-09-12-queue-double-accepted-oversized-messages.md · exit: Distill written and the lesson routed or stated as not needed · checker: orchestrator
- [ ] report · artifact: .drive/REPORT.md · exit: final audit go; drive.py lint --final passes · checker: verifier

## Re-plans
EOF
fill .drive/GOAL.md
git add .drive/GOAL.md
commit_at 2026-09-12T08:10:00Z "drive(intake): publish-large-orders"

mkdir -p .drive/investigations ".drive/proofs/$KEY/r2"

cat > ".drive/investigations/$SLUG.md" <<'EOF'
# An order with 900 line items was rejected by the queue in staging after passing every test
Status: fixed
Trigger: green-check-failed
Detected: 2026-09-12T09:00:00Z by orchestrator via a staging publish of order 5521
Got past: build gates and verifier round 1
Timebox: 45 minutes

## Fail
- Observed: publishing order 5521 to the hosted queue in staging returned MessageTooLarge; the tests for the same order passed.
- Expected: the order is published.
- Reproduction: tests/test_publisher.py::test_large_order_is_published, deterministic once the double enforces the limit.

## Investigate
- Candidate causes, each with the observation that separates it from the others:
  1. Serialization differs between test and staging · separated by: payload byte length in both, identical at 301 KB.
  2. Staging has a lower limit than documented · separated by: docs/queue-limits.md and the provider's limits page, both 256 KB.
  3. The test double accepted messages of any size · separated by: reading tests/fake_queue.py, which had no size check.
- Observations and what they eliminated: equal payload sizes ruled out 1; the documented limit matched staging, ruling out 2.
- Mechanism: the queue double appended any payload while the hosted queue rejects messages over 256 KB, and a 900-item order serialized to 301 KB.

## Verify
- Prediction: with the 256 KB check in the double, test_large_order_is_published fails against the old publisher.
- Check run: python3 -m unittest tests.test_publisher failed with MessageTooLarge against the old publisher.
- Revert check: yes; removing the check made the old publisher pass again.

## Fix
- Change: __BASE__
- Regression test: test:tests/test_publisher.py::test_large_order_is_published
- Harness now enforces: tests/fake_queue.py rejects messages over 256 KB.

## Distill
- Candidate lesson: pending at retro

## Gate log
- fail recorded 2026-09-12T09:00:00Z orchestrator
- diagnosed 2026-09-12T09:40:00Z investigator
- verified 2026-09-12T10:00:00Z investigator
- fixed 2026-09-12T11:30:00Z orchestrator
EOF

cat > .drive/STATE.md <<'EOF'
# STATE · orders · publish-large-orders
status: running
phase: retro
next: Retro: distill the lesson from investigation 2026-09-12-queue-double-accepted-oversized-messages and route it.
updated: 2026-09-12T17:30:00Z
commit: __BASE__
session: drive-large-orders
model: claude-fable-5-1 · high

## Resume here
Why: the fix is verified; the investigation's Distill section is still pending.
Blocked on: none
In flight: none

## Verified facts
- The full suite runs with python3 -m unittest discover -s tests -t . and passes. Verified: ran at __BASE__ on 2026-09-12.

## Rules in force

## Open failures

## Discoveries

## Workaround ledger
| obstacle | workaround | by | when | count |
|---|---|---|---|---|

## Boundary events
EOF

cat > .drive/STATUS.md <<'EOF'
# STATUS · orders
ladder: Missing → Scaffold → Partial → Local Proof → Live Proof → Operational → Done   (Dropped needs why:)

| key | claim | live | status | evidence | updated |
|-----|-------|------|--------|----------|---------|
| large-orders-are-published | An order with 900 line items is published as messages the queue accepts | y | Local Proof | test:tests/test_publisher.py::test_large_order_is_published; severe:tests/test_publisher_severe.py::test_every_message_fits_the_queue_limit; verdict:.drive/proofs/large-orders-are-published/r2/verdict.json; commit:__BASE__ | 2026-09-12 |
EOF

cat > ".drive/proofs/$KEY/r2/verdict.json" <<'EOF'
{
  "verdict": "pass",
  "unit": "large-orders-are-published",
  "round": 2,
  "scope": {"range": "__BASE__..__BASE__", "path": "__ROOT__", "files": ["orders/publisher.py", "tests/fake_queue.py"]},
  "ran": [
    {"cmd": "python3 -m unittest discover -s tests -t .", "exit": 0, "output": "r2/commands.log"}
  ],
  "claims": [
    {
      "id": "large-orders-are-published",
      "status": "holds",
      "oracle": "the documented 256 KB message limit enforced by the double",
      "refutations_attempted": ["400 items of 2 KB each, every message checked against the limit and reassembled"],
      "evidence": ["severe:tests/test_publisher_severe.py::test_every_message_fits_the_queue_limit"],
      "confidence": 75,
      "rung_supported": "Local Proof"
    }
  ],
  "gaps": [],
  "harness_kindness": [
    {"shim": "tests/fake_queue.py", "kinder_than_production_how": "no network, no throughput limits", "severity": "note"}
  ],
  "not_checked": ["a publish against the staging queue"],
  "rung_supported": "Local Proof",
  "for_maker": ""
}
EOF

cat > ".drive/proofs/$KEY/r2/commands.log" <<'EOF'
$ python3 -m unittest discover -s tests -t .
..
----------------------------------------------------------------------
Ran 2 tests in 0.200s

OK
EOF

cat > .drive/LESSONS.md <<'EOF'
# LESSONS · orders
EOF

fill .drive/STATE.md .drive/STATUS.md ".drive/investigations/$SLUG.md" ".drive/proofs/$KEY/r2/verdict.json"
git add -A
commit_at 2026-09-12T17:30:00Z "drive(verify): large orders published under the queue limit, retro next"

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
