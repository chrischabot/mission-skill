# STATE · <project> · <goal slug>
mode: lean
goal: "<verbatim prompt>"
status: running
phase: plan
next: Set the budget target and the stop line, then spawn drive:planner to write .drive/PLAN.md.
updated: <ISO UTC>
budget: $<usd target> target · <wall clock> · <subagents> subagents
stop: none
spend: not measured
pushed: none
in flight: none

<!-- A lean run's resume file, rewritten after every wave and before every stop, in about 40 lines, so
that a fresh process can resume from the repository alone. The status is running, blocked, done,
stopped, or aborted, and the phase is plan, build, review, or finish. From the build on, next names
the next package by its id in PLAN.md, and pushed names the short sha of the last commit the run
pushed, or "none" when the branch has no upstream. The updated time comes from
`date -u +%Y-%m-%dT%H:%M:%SZ`, never an estimate. The budget line records a target set from the lean
envelopes in references/models.md; it is a checkpoint, not a stop. When the recorded spend reaches
the target, and again at each further multiple, the run commits and pushes everything reviewed,
updates this file and LEARNINGS.md, writes or refreshes REPORT.md with what is done and what remains,
and continues. The stop line is the owner's, and the only thing that ends a run before the plan is
complete: a dollar figure, a wall clock, or a date, copied from the goal when the owner states one
there, otherwise "none". Spend is a recorded figure with its source (total_cost_usd, /usage, or the
harness budget line) or "not measured". The in flight line names each background command the run
waits on, by task id or whole command. The Stop gate holds a running run to its next step and lets a
turn end on any other status. Under Open items, write one line each for a package waiting on rework,
an open finding, a blocked item, or a refusal. -->

## Open items
