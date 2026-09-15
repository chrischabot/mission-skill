---
name: lean-learning-entry
description: A resumed lean run at the build phase. PLAN.md's only package says the notes store returns each note's created value as a date, but the store returns ISO text, so the planned comparison fails when it is built as written. Whichever agent meets that failure must append an entry to .drive/LEARNINGS.md recording what failed, why, how the cause was checked (or that it is a guess), and a rule, and the filter must still work.
tags: [lean, learning]
expected_outcome: .drive/LEARNINGS.md holds an entry naming the created values as text rather than dates, with Failed, Why, Verified, Rule, and Scope lines; notes list --since filters correctly; the suite ran.
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  drive.py cannot be read from inside this environment; where the skill calls for it, say in one
  line that it did not run and continue. End the run once package P1 is reviewed and committed. Do
  not start the finish.
---

/drive --resume
