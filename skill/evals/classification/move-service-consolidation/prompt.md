---
name: classification-move-service-consolidation
description: Consolidating a separately deployed service from its own repository into the platform. Intake must classify it as shape move with the migration variant, size L (two repositories and a design unknown), with existing-code, multi-repo, and api among the traits. The run ends after intake.
tags: [classification]
expected_outcome: .drive/GOAL.md committed with shape move, variant migration, size L, traits including existing-code, multi-repo, api; nothing created under core/.
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  The skill's scripts directory is not readable from this environment, so drive.py init,
  preflight, and capabilities cannot run here; where intake calls for one of them, say in one line
  that it did not run and continue with intake. Once .drive/GOAL.md is written and committed, end
  the run with one line naming that file. Do not start the phase that follows intake.
---

/drive --rigorous Move our notification gateway out of the separate notify-gateway project (checked out under external/notify-gateway) and into this platform as a core service, switch the platform's callers over to it, and retire the external project.
