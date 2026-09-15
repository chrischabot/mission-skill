---
name: lesson-dedupe
description: At retro, a closed investigation teaches a rule the lessons store already holds under different wording (a test double kinder than the hosted service). Drive must add the new evidence to the existing entry and raise its Seen count, not append a second entry.
tags: [lessons, dedupe]
expected_outcome: skill-lessons/general.md still has three entries; the double-limits entry reads Seen 2 and cites the queue evidence.
max_turns: 60
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  The skill's own lessons store cannot be reached from this environment. For this run,
  skill-lessons/general.md and skill-lessons/rejected.md in the workspace stand in for
  references/lessons/general.md and references/lessons/rejected.md; read and write lessons there
  and commit them in this repository. End the run once the retro step named in .drive/STATE.md is
  committed.
---

/drive --resume
