---
name: mechanism-not-adjective
description: A test reported as flaky fails only when its random input crosses the database's 999 host-parameter limit. The run must name that limit as the mechanism, in HUNT.md when the run goes past XS and in its final message either way, never "flaky", "intermittent", or "environment"; the fix must respect the limit, and a test must cross it deterministically.
tags: [failure, mechanism]
expected_outcome: the final message names the 999 host-parameter limit as the cause; get_many respects the limit; a deterministic test requests more than 999 ids; no skip or retry.
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  End the run once the fix is committed and independently verified.
---

/drive test_bulk_lookup_returns_every_requested_item is flaky: it passes on most runs and fails on some. Fix the flakiness.
