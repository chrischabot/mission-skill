---
name: classification-feature-dashboard
description: A new dashboard in an existing product's admin area. Intake must classify it as shape feature, size M (a route, a query, and a screen with two unknowns), with existing-code and ui confirmed and api confirmed or suspected. The run ends after intake.
tags: [classification]
expected_outcome: .drive/GOAL.md committed with shape feature, size M, traits including existing-code and ui, with api confirmed or suspected; no new files under app/.
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  Evaluation harness note, not from the user: the skill's scripts directory cannot be read from
  this sandbox, so drive.py init, preflight, and capabilities cannot run here; where intake calls
  for one of them, say in one line that it did not run and continue with intake. This run is
  scored on intake only. Once .drive/GOAL.md is written and committed, end the run with one line
  naming that file. Do not start the phase that follows intake.
---

/drive Add a usage dashboard to the existing admin area that shows daily active accounts and new signups for the last 30 days.
