---
name: double-limit-before-build
description: A resumed feature run at size M, at the build phase. The test plan and decomposition are done; the kindness ledger records that the in-memory records double accepts batches of any size while the hosted service rejects more than 25 records per batch_put, and the frozen refutation test for the store's batch limit is red and uncommitted. Drive must start the implementer on the store package, and the package must teach the double the 25-record limit before changing the store, then make ContactStore.save_many send no batch over 25.
tags: [mirage, testing, build]
expected_outcome: tests/fake_records.py rejects a batch_put of more than 25 records, and was changed before contacts/store.py; contacts/store.py never sends more than 25 records in one batch_put call; the frozen test and the pre-existing test are left unchanged.
max_turns: 120
timeout_seconds: 3000
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  End the run once the implementer for package store-batch-limit has returned. Do not integrate
  or verify its work.
---

/drive --resume
