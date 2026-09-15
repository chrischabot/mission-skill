# LEARNINGS · <project>

<!-- This project's memory across drive runs. Memory builds in five stages: a failure is written
down, investigated, verified, distilled into a rule, and consulted before the next plan, and the
sections below follow those stages. The planner reads Verified facts, General rules, and Open
failures before every plan. During a run every agent appends entries under New entries with one
`cat >> .drive/LEARNINGS.md <<'EOF'` command, never by editing the file, so agents working in
parallel never overwrite each other. Each entry is a level-three heading reading "date · role · what
happened", then five lines: Failed, Why, Verified, Rule, and Scope. Verified names the command or
observation that confirmed the cause, or says guess, and a guess stays an open failure until someone
verifies it. Scope is project or general. At the finish, drive.py promote sorts the entries into the
sections and promotes verified general rules to drive's references/lessons/learned.md. -->

## Verified facts
<!-- Stage 3: checked facts about this project. Stop guessing about these. -->

## General rules
<!-- Stage 4: rules for work in this project. Consult them before re-deriving anything. -->

## Open failures
<!-- Stages 1 and 2: failures and guesses nobody has verified yet. Investigate these next. -->

## Lessons learned
<!-- Stage 4: rules promoted from this project into drive's own lessons. -->

## Last session
<!-- Stage 5: one line about the latest run. -->

## New entries
