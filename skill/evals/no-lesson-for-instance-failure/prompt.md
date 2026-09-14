---
name: no-lesson-for-instance-failure
description: At retro, the closed investigation is a one-off data-entry mistake in one row of this project's configuration, with correct code around it. Drive must write "none" in the Distill section with a reason, record the project fact in STATE.md or LESSONS.md, and add no general rule.
tags: [lessons, restraint]
expected_outcome: skill-lessons/general.md unchanged at three entries; the investigation's Distill section says none; the fact about the region's currency lands in STATE.md or LESSONS.md.
max_turns: 60
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  Evaluation harness note, not from the user: the skill's own lessons store cannot be reached from
  this sandbox. For this run, skill-lessons/general.md and skill-lessons/rejected.md in the
  workspace stand in for references/lessons/general.md and references/lessons/rejected.md; read
  and write lessons there and commit them in this repository. End the run once the retro step
  named in .drive/STATE.md is committed.
---

/drive --resume
