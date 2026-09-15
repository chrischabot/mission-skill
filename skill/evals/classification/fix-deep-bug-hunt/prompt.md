---
name: classification-fix-deep-bug-hunt
description: A vague "deep, annoying bug" in existing code whose cause is unknown. Intake must classify it as shape fix with no incident or perf variant, size M (S is accepted because this fixture is one small module), with existing-code confirmed. Quality words set nothing. The run ends after intake.
tags: [classification]
expected_outcome: .drive/GOAL.md committed with shape fix, no incident or perf variant, size M or S, existing-code among the traits; ledger code untouched.
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  The skill's scripts directory is not readable from this environment, so drive.py init,
  preflight, and capabilities cannot run here; where intake calls for one of them, say in one line
  that it did not run and continue with intake. Once .drive/GOAL.md is written and committed, end
  the run with one line naming that file. Do not start the phase that follows intake.
---

/drive Find this deep, annoying bug and fix it: the weekly totals report is occasionally one entry off, usually in weeks where someone logged time late on a Sunday night.
