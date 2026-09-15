# REPORT · <goal slug>

<!-- Derived from STATUS, STATE, DECISIONS, LESSONS, the investigations, and the proofs, never from
memory of the run. Written for a reader who saw none of the work: outcome first, then anything
needed from the owner. Every statement cites a row, a file, or a proof; nothing the lint would reject
is stated; no plan or intention is described as a result; claims are named by their words, never by
key alone. drive.py lint --final checks the Ladder counts against STATUS.md. -->

## Outcome
<One paragraph: what was asked, what is true now at which commit, and its honest rung>

## Needed from you
<!-- Write "none", or a list with one line per step only the owner can take (a login, a secret, a
team identifier, a production promote, evidence for a removed claim), in the order to take them.
Each line names the step, then "meanwhile:" and the default the run applied, then "finish with:"
and the exact command or action that completes it. -->
<none, or the single decision, or one line per owner step as the comment says>

## What to look at first
<The one or two things most worth the owner's attention, with their paths.>

## Ladder
| rung | rows |
|------|------|
| Missing | <missing count> |
| Scaffold | <scaffold count> |
| Partial | <partial count> |
| Local Proof | <local proof count> |
| Live Proof | <live proof count> |
| Operational | <operational count> |
| Done | <done count> |
| Dropped | <dropped count> |

## What shipped
- <claim words> · <rung> · <evidence path>

## Proven live and proven locally
- Live: <claim words> · <live proof path>
- Local only: <claim words> · <why live proof was not reached>
- Where a harness was kinder than production: <every shim_differences and harness_kindness answer, one line each>

## Not done
- <claim words> · <rung reached> · <the exact step that would finish it>

## Decisions taken on your behalf
- <decision in plain words> · undo: <exact command or steps> · <DECISIONS.md entry date>

## Open failures
<!-- Every open failure in STATE.md, every blocking gap left open at a bound, and every flake. A
frozen or suite test that failed in any recorded run (a verifier's saved output, a gate run, the
lint's suite run) and passed on a rerun is a flake, listed as "flake: <test path>::<name> failed <n>
of <m> recorded runs, passed on rerun · <what would close it>", and never omitted because the last
run was green. -->
- <symptom> · <the command or observation that would close it>

## Lessons
- <rule heading> → <destination> (<commit sha>), or none: <the reason>

## Verify from a clean checkout
```bash
<exact commands, each on its own line>
```

## Paused run
<none, or the .drive/runs/ directory and how to restore it>

## Spend
<!-- Written after the final audit and the security review have returned, never before, because a
figure taken earlier leaves out the most expensive verdicts. Every cost figure comes from a recorded
total named with its source (a headless result's total_cost_usd, earlier legs' totals in
.drive/local/run.md, /usage, or the harness budget line), or the line says "not measured"; an
estimate is never written as spend. A headless leg's own total arrives only when its session ends,
so give the latest recorded figure with its time and say the leg's result holds the final one. -->
<turns, subagents, wall clock, and cost from a recorded total with its source or "not measured", against GOAL.md's envelope>
