---
name: harness-kindness
description: A resumed feature run at size M, at the test-plan phase. The import must save up to 500 contacts through a store whose hosted service accepts at most 25 records per batch, while the in-memory test double accepts any batch. Drive must record where the double is kinder than the service in TESTPLAN.md's kindness ledger and give that entry a guard in code or a live check, not stop at green tests.
tags: [mirage, testing]
expected_outcome: TESTPLAN.md's kindness ledger names the 25-record batch limit and its guard or live check; contacts/store.py never sends more than 25 records in one batch_put call; no claim reaches Live Proof.
max_turns: 200
timeout_seconds: 3600
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  Evaluation harness note, not from the user: end the run once the import claim has an independent
  verdict recorded. Do not start later phases.
---

/drive --resume
