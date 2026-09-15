---
name: lean-feature-plan
description: A plain /drive with a feature goal and no mode word runs lean. The run must have drive:planner write .drive/PLAN.md with acceptance commands, must write no GOAL.md, SPEC.md, DESIGN.md, or TESTPLAN.md, and must spawn no reviewer of the plan. The run ends once the plan is committed.
tags: [lean, cost]
expected_outcome: .drive/PLAN.md committed with at least one package and its acceptance command; no GOAL.md, SPEC.md, DESIGN.md, or TESTPLAN.md under .drive/; drive:planner spawned; no architect, auditor, verifier, grader, designer, severe tester, or reviewer spawned.
max_turns: 40
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  The skill's scripts directory is not readable from this environment, so drive.py init and
  preflight cannot run here; where the skill calls for one of them, say in one line that it did not
  run and continue. Once .drive/PLAN.md is written and committed, end the run with one line naming
  that file. Do not start the build.
---

/drive Add a usage dashboard to the existing admin area that shows daily active accounts and new signups for the last 30 days.
