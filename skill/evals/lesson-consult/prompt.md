---
name: lesson-consult
description: A resumed run about to brief an implementer for a package that writes through a test double for a hosted object store. The brief must carry the heading "Lessons that apply to this task" and quote the matching rule verbatim, and should leave out rules that do not apply.
tags: [lessons, briefs]
expected_outcome: the implementer's brief contains "Lessons that apply to this task" and the double-limits rule heading, and does not quote the simulator rule.
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  Evaluation harness note, not from the user: the skill's own lessons store cannot be reached from
  this sandbox. For this run, skill-lessons/general.md in the workspace stands in for
  references/lessons/general.md. End the run once the implementer for package csv-export has
  returned. Do not integrate or verify its work.
---

/drive --resume
