---
name: classification-publish-research-website
description: Market research followed by a designed website with blog and documentation sections that the goal asks to have deployed and live. Intake must classify it as shape publish, size L (a research deliverable and a multi-section site), with research-needed, prose-content, and ui among the traits. The run ends after intake.
tags: [classification]
expected_outcome: .drive/GOAL.md committed with shape publish, size L, traits including research-needed, prose-content, ui; no HTML written.
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  The skill's scripts directory is not readable from this environment, so drive.py init,
  preflight, and capabilities cannot run here; where intake calls for one of them, say in one line
  that it did not run and continue with intake. Once .drive/GOAL.md is written and committed, end
  the run with one line naming that file. Do not start the phase that follows intake.
---

/drive --rigorous Research where our project stands against similar tools, then build a website in this repository that describes the project, its goals, and the team, with a blog section and a documentation section, and deploy it so the site is live on the web.
