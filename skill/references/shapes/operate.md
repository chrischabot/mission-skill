# Shape: operate

Read this at intake when the goal changes the state of a live system and no code change is the point
(deploy an existing release, rotate a secret, import data, run a backfill, move DNS, restore a backup,
clean up resources, start a stopped service), and again at the start of every phase. It decides the
phase order, how a step is planned with its undo before it runs, who executes and who observes, what
counts as evidence of an effect, when the run must stop, and what Done means. One rule governs the
whole shape: drive the system now through its own tools (MCP verbs, CLI, API), and never report that
something will happen when a schedule next fires.

## When it applies

The deliverable is a changed live system. When a defect is the reason for the change, the shape is
`fix/incident`. When consumers move from one system to another over time, it is `move/migration`. A
script needed to perform a step is a small `build` package with its own test, because a script that
changes a live system is code. Between two sizes take the larger; an under-sized operation is the one
that skips the undo.

## Phases

| Phase | Entry | Work and agent | Artifact | Exit check (checker) |
|---|---|---|---|---|
| intake | the goal | classify; record `live means` and which system each step touches (orchestrator) | GOAL.md | committed before other work (orchestrator) |
| archaeology | GOAL.md committed | load the system's own verbs (ToolSearch for its MCP tools, its CLI, its API); read the runbook, current state through read verbs, recent changes, and every other actor on the system (schedules, other services) (orchestrator loads tools; drive:researcher reads logs and config) | `how-it-works.md` at M and above; STATE.md Verified facts | the exact target identity (account, environment, service or database name) confirmed through a read verb; a read verb named for every effect to observe (orchestrator) |
| plan | archaeology exit | one line per state change: the action through a verb, the exact undo, the read that will show the effect, and the restore point for anything destructive; one STATUS row per intended effect (orchestrator at S; drive:architect at M and above) | GOAL.md plan lines in the form under "Plan lines"; STATUS.md | every step has an undo, or has none and is implied by the goal; nothing destructive lacks a restore point (drive:verifier at S and M, in plan-review mode; drive:auditor at L and above) |
| execute | plan pass, per step | confirm the evidence supports this action; append the undo to DECISIONS.md; run the step through the system's own tools; for bulk data, idempotent batches sized from platform limits and resumable by cursor (orchestrator) | DECISIONS.md; `.drive/proofs/<key>/r<n>/commands.log` | the command completed with output saved; this is not the effect (orchestrator) |
| observe | each executed step | read the effect through the system's read verbs, independently of the command that caused it; trigger dependent jobs now and read their result; on a mismatch run the undo or hold (drive:verifier) | `ops:` or `live:` evidence on the STATUS row | the effect is visible through an independent read (drive:verifier) |
| retro, report | every step observed, or the run stopped | lessons; final audit by drive:auditor at L and above, otherwise a fresh drive:verifier running the same checklist; REPORT.md listing every step, its undo, and its observation (orchestrator) | LESSONS.md, `.drive/reviews/<date>-final-audit.json`, REPORT.md | `drive.py lint --final` passes (orchestrator) |

## Plan lines

Write one `execute` line and one `observe` line per step, in the grammar every GOAL.md plan line
uses. The step's words sit between the phase name and `artifact:`, and `artifact:`, `exit:`, and
`checker:` are always present, because `drive.py lint` rejects a line without them:

```
- [ ] execute · rotate the api key · artifact: .drive/proofs/api-key-rotated/r1/commands.log · exit: command completed with output saved · checker: orchestrator
- [ ] observe · rotate the api key · artifact: .drive/proofs/api-key-rotated/r1/ops.md · exit: new key serves and old key is refused, read through the provider's key listing · checker: drive:verifier
```

## Step rules

- Write the undo before the step, however small. A step whose undo you cannot write is allowed only
  when the goal implies it; otherwise it is a stop condition, reported with everything else finished.
- Before a destructive step (deletion, overwrite, schema change, rotation, restore over live data),
  record a restore point and prove on a copy that it restores.
- Change a live system through its verbs, never by writing to its database behind it: the verbs
  enforce its invariants and leave its audit trail.
- Confirm the target identity in every state-changing command matches the one archaeology confirmed;
  a wrong environment or service name is the cheapest catastrophe to prevent.
- Rotate by adding first: set the new secret, prove it serves, then revoke the old one. Name secrets
  the owner must set; never type a value into a file, a command log, or STATE.md.
- A data import or backfill runs in batches whose size comes from the platform's limits, is safe to
  re-run, resumes from a recorded cursor, and ends with counts and a checksum compared on both sides.
- When a step depends on a scheduled job, trigger that job now through its own tools. A schedule is
  used only for a soak with no triggering signal, as `references/shapes/move.md` describes, and the
  scheduled check decides and acts.
- Watch long operations with `Monitor` on a command that exits when the condition holds.

## Size

| Size | What runs |
|---|---|
| XS | one reversible command with an obvious read-back (restart a stopped worker): inline, no `.drive/`; the final message names the command, its undo, and the observed effect |
| S | a few steps on one system: GOAL, STATE, STATUS, DECISIONS.md (`drive.py init --size S` creates the first three; copy `templates/DECISIONS.md` before the first undo is written); plan lines in GOAL.md reviewed by `drive:verifier`; observation by `drive:verifier` |
| M | several steps or a destructive one: `how-it-works.md`, verified restore points, the plan reviewed by `drive:verifier` before execution |
| L | several systems: change order across systems in the plan, auditor plan review and final audit |
| XL | a multi-day operation: stages with a soak each, as in `references/shapes/move.md`, and a re-classification review by `drive:auditor` at each phase gate |

## Trait gates that commonly attach

| Trait | Effect |
|---|---|
| `deploy-infra` | config diff before apply; the previous version id recorded as the undo; smoke check after |
| `data` | restore point proven on a copy; batch discipline; counts and checksums |
| `auth` | add-then-revoke rotation; secrets named, never written; security review when an access policy changes |
| `async-scheduled` | trigger now; disable a schedule at its source (the row or trigger, not only the handler) |
| `external-systems` | sandbox and live distinguished per call; quotas and cost recorded before bulk steps |

## Verification centre, Done, parallelism

The centre of gravity is the observed effect, read independently of the command, with every undo
written before its step. Observation gets 2 rounds per step: after one undo and a retry on a new
diagnosis, the same failure again stops the run. Done means every step's effect is observed and
recorded with `ops:` or `live:` evidence; DECISIONS.md holds every undo, each timestamped before its
step; nothing is reported as pending a schedule; and when the goal includes staying healthy, the rows
are Operational: a smoke check or alert exists and was fired once during the run
(`references/observability.md`).

State changes run strictly in sequence with an observation after each. Read-only evidence gathering
(log sweeps, config reads across systems) may run in parallel.

**Re-classify** when a defect turns out to be the reason (`fix/incident`); when a code change beyond a
small script is needed (a `feature` or `build` sub-goal); and when the operation is really consumers
moving between systems over time (`move/migration`). A destructive step the goal does not imply is not
a re-classification; it is a stop condition.

## Excuses and rebuttals

| Excuse | Rebuttal |
|---|---|
| "The command returned 0, so it worked." | Deploys, rotations, and cutovers succeed at the prompt and fail in effect; read the effect through the system's verbs. |
| "The job will pick it up on its next run." | Trigger it now and observe; a schedule is a hypothesis about the future, not evidence. |
| "Writing to the database directly is quicker." | It bypasses the system's invariants and audit trail; use its verbs. |
| "It is a small change; no undo needed." | The undo is written first so that a wrong step costs one command. |
| "Revoke the old key first to be safe." | Revoking before the new key serves causes the outage; add, prove, then revoke. |
| "The backup exists." | Until it has restored on a copy, it is not a restore point. |

## Red flags

- A DECISIONS.md undo entry written after its step ran.
- Evidence that is only an exit code or a "success" message.
- "Will run at", "should propagate", or "on the next cycle" in STATUS, STATE.md, or the report.
- A write to a system's database when the system exposes a verb for it.
- A destructive command with no recorded, proven restore point.
- A target name in a command that differs from the identity confirmed at archaeology.
- A secret value in STATE.md, a proof log, or a saved command line.
