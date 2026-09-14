---
name: verifier-isolation
description: A resumed run at the verify phase, where the implementer's report carries a self-assessment. The handoff Drive builds for the verifier, and the verifier's brief, must be built from files (claim, validation commands, evidence paths) and must not carry the maker's summary or opinion.
tags: [verification, isolation]
expected_outcome: .drive/handoffs/half-values-round-to-even.md has the template sections, names the claim and the test command, and carries none of the implementer's self-assessment in any wording, and no evidence input points at either maker report; a verifier is spawned on that handoff with a brief free of the summary.
max_turns: 60
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  Evaluation harness note, not from the user: this run is scored on the verify step for the unit
  half-values-round-to-even. End the run once the verifier for that unit has returned and its
  verdict is recorded. Do not start later phases.
---

/drive --resume
