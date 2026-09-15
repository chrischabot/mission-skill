# STATE · <project> · <goal slug>
mode: lean
goal: "<verbatim prompt>"
status: running
phase: plan
next: Set the budget line, then spawn drive:planner to write .drive/PLAN.md.
updated: <ISO UTC>
budget: <usd hard stop> · <wall clock> · <subagents> subagents
spend: not measured
in flight: none

<!-- A lean run's resume file, rewritten after every wave and before every stop, in about 40 lines.
The status is running, blocked, done, stopped, or aborted, and the phase is plan, build, review, or
finish. The updated time comes from `date -u +%Y-%m-%dT%H:%M:%SZ`, never an estimate. The budget
line is a hard stop set from the lean envelopes in references/models.md, and spend is a recorded
figure with its source (total_cost_usd, /usage, or the harness budget line) or "not measured". The
in flight line names each background command the run waits on, by task id or whole command. The Stop
gate holds a running run to its next step and lets a turn end on any other status. Under Open items,
write one line each for a package waiting on rework, an open finding, a blocked item, or a refusal. -->

## Open items
