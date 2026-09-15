---
name: classification-build-mobile-app-serverless
description: "Greenfield native mobile app with a serverless backend and storage. Intake must classify it as shape build, size XL (a new product across two clients, the iOS app and the web app, plus a serverless backend: three surfaces, and an open problem), with ui, native-platform, api, auth, and data among its traits. The run ends after intake."
tags: [classification]
expected_outcome: .drive/GOAL.md committed with shape build, size XL, traits including ui, native-platform, api, auth, data; no Swift or backend code written.
max_turns: 60
timeout_seconds: 1800
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
append_system_prompt: >-
  The skill's scripts directory is not readable from this environment, so drive.py init,
  preflight, and capabilities cannot run here; where intake calls for one of them, say in one line
  that it did not run and continue with intake. Once .drive/GOAL.md is written and committed, end
  the run with one line naming that file. Do not start the phase that follows intake.
---

/drive --rigorous Build a mobile app in this repository that helps people keep their houseplants alive. Each person signs in, photographs a plant, and the app works out its watering and light needs, reminds them when to water, and keeps a care history with photos for every plant. The app is a native iOS app in Swift, and people can also see and update their plants from a web app in the browser. The backend is serverless on Cloudflare Workers and stores accounts, plants, care events, and photos. People only ever see their own plants.
