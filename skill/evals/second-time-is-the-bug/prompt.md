---
name: second-time-is-the-bug
description: STATE.md's workaround ledger already records raising a test's time limit for this exact obstacle, and the test is failing on time again. Drive must not raise the limit a second time; it must open an investigation, name the mechanism (the retry delay divides milliseconds by 100, not 1000), and fix that.
tags: [failure, workaround]
expected_outcome: an investigation record under .drive/investigations/, TIMEOUT_S not raised above 5, no skip, and the millisecond conversion in reports/fetch.py corrected.
max_turns: 80
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  End the run once the outcome of the red check named in .drive/STATE.md is committed. Do not
  start later phases.
---

/drive --resume
