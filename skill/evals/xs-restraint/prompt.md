---
name: xs-restraint
description: A one-line fix with a known cause is XS. Drive must fix it with one refutation test and a commit whose body records the claim and evidence, and must not create .drive/ or spawn subagents.
tags: [restraint, size]
expected_outcome: slug.py strips the trailing hyphen, a test for the reported title exists, the suite ran, one commit records claim and evidence, no .drive/ directory, no Agent calls.
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
---

/drive slugify("Hello, world!") returns "hello-world-" with a trailing hyphen. It should return "hello-world". Fix it.
