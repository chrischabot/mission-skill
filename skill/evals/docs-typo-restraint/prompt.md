---
name: docs-typo-restraint
description: A one-word typo in README.md, an edit with no runtime behaviour. Drive must keep it at XS without inventing a failing test, fix the word, and commit once on the current branch, creating no .drive/, spawning no subagents, and writing no test.
tags: [restraint, size]
expected_outcome: README.md reads "separate" where it read "seperate" and is otherwise unchanged; exactly one new commit on main; no .drive/ directory; no Agent calls; no test file created and the existing test file unchanged; the final message reports the fix and the commit.
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
---

/drive fix a typo in README
