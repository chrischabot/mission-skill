# Shape: move

Read this at intake when the goal moves, migrates, consolidates, upgrades, refactors, or simplifies
something whose behaviour must survive, and again at the start of every phase. It decides the phase
order for a move and its three variants, who does each phase, what `.drive/MIGRATION.md` holds, how
consumers are found, how parity is defined, how cutover advances and rolls back, how long a soak
lasts and who acts on it, how the old path dies, and what Done means. The risk in this shape is that
the old thing stops working for a consumer nobody wrote down, so the steps below exist to make the
hidden consumer, the kinder harness, and the irreversible cutover structurally hard to skip.

## When it applies

| Variant | Applies when | Differs |
|---|---|---|
| `move/migration` | behaviour crosses a boundary: repository, service, platform, datastore | the full runbook, with shadow, staged cutover, soak, and decommission |
| `move/refactor` | in place, one codebase, behaviour and public interfaces unchanged | no cutover or soak; characterization is the full suite output |
| `move/upgrade` | a toolchain, runtime, or dependency version changes | characterization is build plus suite plus runtime smoke; flips per module |

The run lives in the repository that will hold the deliverable, the destination; a repository named
after "from" in the goal is never the home. The old path still needs writes (identity logging, the
disable step, decommission), so list every repository the move touches as an absolute path under
GOAL.md's `probe.repos`, which the launch settings and the write guard both honour.

No new behaviour enters a move: anything the owner wants changed becomes a `feature` sub-goal after
cutover. Between two sizes take the larger. Isolation here is a runtime property (shadow-named
resources, a flag, routing weights), never a branch or worktree.

## Phases

| Phase | Entry | Work and agent | Artifact | Exit check (checker) |
|---|---|---|---|---|
| intake | the goal | classify; record the no-new-behaviour rule and `live means` (orchestrator) | GOAL.md | committed before other work (orchestrator) |
| archaeology | GOAL.md committed | source and destination read; commands run once; drift table; blast radius; for upgrades the migration guide and changelog between installed and target versions (drive:researcher lanes, reconciled with `model: "opus"`) | `how-it-works.md`; RESEARCH.md rows for upgrades | green baseline recorded; dangerous drift fixed in its own commit (orchestrator) |
| inventory | archaeology exit | charter, invariants, consumers from the old path's logs, secrets by name (drive:researcher gathers; drive:architect writes the charter) | MIGRATION.md Current state, Target state, Invariants, Consumer inventory | the verifier reads the old logs itself and finds no identity missing from the table; Unknowns empty before the first weight step (drive:verifier) |
| characterize | inventory exit | goldens from current code; redacted traffic recording (a small deployed package with its undo); Known-wrong list (drive:severe-tester writes the characterization tests; drive:implementer the recorder) | tests and goldens in the project's test tree; recordings in `.drive/local/recordings/`; MIGRATION.md Characterization | characterization passes against the old path; goldens carry commit and date (drive:verifier) |
| design | characterize exit | stage plan: seam, flag, parity fields, shadow sampling, write strategy, expand and contract, error budget, undo per stage, pre-mortem (drive:architect) | MIGRATION.md Parity, Expand and contract, Stages; DESIGN.md for the new implementation at M and above | no unlisted consumer, kinder shim, or step without an undo found (drive:architect fresh context at S to M; drive:auditor at L to XL) |
| build | design pass | seam package first and alone; new implementation behind the flag defaulting to old; call-site moves by path partition (drive:implementer; `model: "opus"` for packages marked hard) | code, tests, CONSTRAINTS.md | gates, `drive.py guard`, whole suite on both flag states (drive:verifier per package) |
| verify | build exit | parity lens: goldens and replay on both paths over production-shaped data with real limits in the harness; operability lens: undo commands match the current state, down paths run on a copy (two drive:verifier handoffs; drive:grader classifies mismatches) | `.drive/proofs/<key>/r<n>/verdict.json` | both lenses pass; rung at most Local Proof (drive:verifier) |
| cutover | verify pass | shadow run, rollback drill, weight stages; the orchestrator decides each advance from the verdict | MIGRATION.md Undo ledger, Rollback drill; `live:` proofs | stage within budget; drill evidence recorded (drive:verifier) |
| soak | each non-zero stage | force what can be forced, then the soak check decides and acts | MIGRATION.md Soak record; `ops:` evidence | each stage held a full cycle within budget, the last at 100% (drive:verifier reads the window) |
| decommission | final soak closed | disable, observe, delete code; delete a data store only while the run is open, otherwise name its deletion as an owner step in REPORT.md (orchestrator; drive:implementer for code removal) | commits; DECISIONS.md; STATE.md; MIGRATION.md Decommission | zero hits for a cycle; every consumer migrated with evidence; zero references (drive:verifier) |
| docs | decommission exit | runbook, CLAUDE.md, `how-it-works.md` (drive:writer) | docs | commands in docs run (orchestrator) |
| retro, report | docs exit, or the run stopped | lessons; REPORT.md; final audit always (drive:auditor) | `.drive/reviews/<date>-final-audit.json`, REPORT.md | `drive.py lint --final` passes (orchestrator) |

## MIGRATION.md

At M and above, copy `templates/MIGRATION.md` to `.drive/MIGRATION.md` at inventory; at S the charter
lives in STATUS rows and GOAL.md. Its sections, in order: Current state, Target state, Point of no
return, Invariants, Consumer inventory with Unknowns, Characterization with Known-wrong behaviour,
Parity with named normalizers, Requirements, Expand and contract, Stages, Backups, Undo ledger,
Rollback drill, Soak record, Decommission, then where the test environment is kinder, what each rung
means, Assumptions, Risks, and Changes. The architect writes the charter sections. The undo ledger,
drill, soak record, and decommission are appended during the run, each undo row before its action,
and never rewritten.

## Inventory and characterization

Build the consumer inventory from the old path's own access logs over at least one full cycle of
the traffic's periodicity (a week for anything daily or weekly), matching every identity to a row.
Then search every repository you can reach and every client configuration for the URL, binding,
table, or function name; list schedules on every machine and platform involved; read runbooks and
dashboards. A consumer can be a schedule row in a table rather than code. Record secrets by name
only; values are set by the owner or copied by a script, never typed into files.

When the old path does not log caller identity, or keeps logs for less than a cycle, deploy identity
logging first as a small package with its undo, and continue characterization, design, and build while
the cycle accumulates; only the first weight step waits for it.

Capture current behaviour before the first change, labelled observed and never correct. Goldens for
deterministic units come from running the current code over fixtures, each with the commit and
date. Recorded traffic covers the integration surface for a full cycle, with the redaction list
written before recording starts; it is never committed. Behaviour discovered to be wrong goes under
Known-wrong with a decision, because otherwise a golden set quietly turns bugs into specification.

## Design rules

1. **Seam first.** Define the interface consumers will use, implement it as an adapter over the old
   path, move every consumer to it, and ship that alone with the suite green. Only then build the
   new implementation behind the same interface, with a flag that selects the old path when unset
   and a removal date written the day it is created.
2. **Parity on decisions, not payloads.** Compare what the two paths decide (identity, tenant,
   route, cache key, limit verdict, cost line, headers, stored row); treat nondeterministic output
   as pass-through. Every normalizer is named in the report. A second normalizer for the same class
   of mismatch is the second-time signal: stop and investigate.
3. **Serve the control, shadow the candidate.** Return only the old path's result while the flag is
   off and publish the comparison. Never shadow writes to shared stores; dual-write with an
   idempotency key and compare at read time. When the candidate has real upstream cost, shadow the
   decision logic on everything and the full path on a small sample.
4. **Expand and contract.** Never rename or drop a field, column, or endpoint in the same deploy as
   the code that depends on the change. Add the new shape beside the old and deploy; write both and
   deploy; backfill in resumable batches sized from platform limits and driven by a verb, checking
   counts and a checksum; switch reads while still writing both; stop writing the old shape; remove
   it in its own later deploy once search and logs show nothing reads it. Every step deploys and
   reverts alone, and every schema step has a down path that has actually been run on a copy.
5. **Back up before anything destructive** (schema change, data rewrite, rotation, route or schedule
   removal): export, record the restore point, write the undo row, then act. Exports live in
   `.drive/local/backups/` or the owner's backup bucket, never in git.
6. **Error budget per stage**, unless the charter sets another: new-path error rate at most control
   plus 0.1 percentage points; p95 latency at most 1.2 times control; parity mismatch at most 0.1
   percent and zero on identity, tenant, and cost fields; at most a dozen metrics, compared with the
   control in the same window, never with last week.

## Cutover, soak, decommission

Advance through weights (0, 10, 50, 100) or consumer by consumer, least critical first, writing
each stage's undo row before acting. At the first non-zero weight, run the rollback exactly as the
ledger writes it, confirm from logs that every request is back on the old path and the error rate
returned to control, roll forward, and record the elapsed time. A rollback that needed improvisation
means the plan is not ready. The bound is 4 verification rounds per cutover and 3 for every other
gated phase of a move (inventory, characterize, design, build, verify, soak, decommission). When the charter shows
every consumer is owned and enumerable from configuration (five or fewer), move consumer by consumer
with the drill before the first, and soak only the final stage for one cycle; record that choice in
DECISIONS.md, because a week at 10 percent of near-zero traffic proves little.

A soak is the one legitimate scheduled condition, because nothing makes time pass under real
traffic. First force everything that can be forced now: synthetic traffic, corpus replay, scheduled
handlers triggered through their own tools, the drill, the first weight. Soak each stage for one
full periodicity cycle. While the session lives, watch with `Monitor` or a self-paced `/loop`; a
schedule is used only when the session must end, and it runs a check that decides and acts: advance,
hold, or roll back to the previous weight and write an investigation. An exhausted budget means roll
back, never advance more slowly. While any soak is open the claim is at most Live Proof, STATE.md
says `blocked` with a `soak:` Blocked on line naming the window end and where the check runs, and
nothing is Done.

Decommission is disable, observe, delete. Disable the old route or binding, the schedule itself (the
row or trigger, not only its handler), and old tokens, and make the old path answer with a named,
logged refusal. Observe zero hits for a full cycle. Delete the code promptly in its own commit with
zero-reference evidence. Delete data stores only after the rollback window, with an export retained
and its restore proven on a copy.

When the window closes while the run is still open, the run deletes the store itself, with drive's
guard and reviewers in place: first a DECISIONS.md entry with the deletion command and its restore,
then a check that nothing read the store during the window, then the deletion through the platform's
tools, with the evidence under `.drive/proofs/`. When the window outlasts the run, drive never
schedules the deletion, because a scheduled prompt that deletes data after `drive.py end` runs with no
guard and no reviewer. Instead, put it in REPORT.md's "Needed from you" as one owner step giving the
read check to run first, the exact deletion command, and the exact restore command from the verified
export, and add a dated STATE.md line outside Done. The deletion is not a soak, so the move's rows
reach Done without waiting for it.

## Variants

**`move/refactor`.** Characterize by capturing the full test output and a snapshot of public
interfaces before changing anything; verify by diffing the output after, allowing only timing noise.
No existing test is modified. When the goal is simplification, have a `drive:implementer` under a package brief run `/simplify <paths>`, re-gate, and
revert if the baseline changed. Superseded code is deleted with zero-reference evidence; cleanups
outside the goal are discoveries. Live proof runs only if the code is deployed.

**`move/upgrade`.** Characterize with the build, the suite, and a runtime or simulator smoke on the
old version, with screenshots when `ui` applies. Change one dependency at a time, green before and
after; read the lockfile diff and never hand-edit it. Flip module by module where the toolchain
allows and change nothing beyond what the new version demands. The last flip is the cutover; soak
only when the upgraded runtime serves live traffic; `drive:ui-reviewer` compares old and new smoke
screenshots.

## The ladder for a move

| Rung | Evidence |
|---|---|
| Local Proof | goldens and replay pass on both paths over production-shaped data with real limits enforced; down paths run |
| Live Proof | shadow parity met the budget for a full cycle; rollback drill ran in production; one stage soaked |
| Operational | 100% held through its soak; old path disabled and at zero hits for a cycle; every consumer migrated with evidence |
| Done | Operational plus old code deleted, flag removed, docs updated, final audit go; store deletion check scheduled |

## Size and traits

| Size | What changes |
|---|---|
| XS | only a rename inside one file with its tests; otherwise size up |
| S | refactor or upgrade of one module: GOAL, STATE, STATUS; characterization recorded in STATUS rows; one verifier with both lenses |
| M | MIGRATION.md, CONSTRAINTS.md, recorded goldens, flag, drill; two lenses may share one verifier round |
| L | two repositories or surfaces: ownership map and change order in the charter, recorded traffic, shadow run, separate lens verifiers, auditor design review |
| XL | per-phase bounds, Workflow fan-out for read-only sweeps, a re-classification review by `drive:auditor` at every gate |

`multi-repo` pins the cross-repository contract first and orders changes provider before consumer.
`data` adds backups, expand and contract, tested down paths, and real limits in the harness. `auth`
means secrets by name, rotation only at decommission, and a security review. `async-scheduled` makes
schedules consumers, triggered now and disabled at the source. `api` and `public-api` freeze the old
contract and log caller identity until sunset. `large-surface` fans call-site moves into waves with a
verifier per package. `deploy-infra` follows the domain file's deploy ladder.

## Verification centre, Done, parallelism

The centre of gravity is the equivalence corpus, built before any code moves, plus the rollback
drill. Done means the move is at Done on the ladder above, every Consumers row reads migrated with
evidence, the Parity table closes with a final report, MIGRATION.md's stages all carry drill or soak
evidence, and the final audit compares STATUS with the intake commit. Mechanical call-site moves run
in parallel by path partition in the shared checkout; cutover, soak, and decommission are strictly
serial. Do not use worktrees.

**Re-classify** when new behaviour is requested (a `feature` sub-goal after cutover); when a third
repository or surface appears (size up); when a schema change appears (add `data`); when a consumer
surfaces after cutover began (hold the weight, add the row, re-run the inventory gate); and when a
refactor turns out to change observable behaviour (migration or feature).

## Excuses and rebuttals

| Excuse | Rebuttal |
|---|---|
| "Search found every caller." | Logs over a full cycle find what search cannot: other repositories, client configs, schedule rows, runbooks. |
| "While we are moving it, we can fix this." | Nothing pins what "the same" means for new behaviour; record it as Known-wrong and ship it as a feature after cutover. |
| "Rollback is one command; no need to drill it." | An unexecuted rollback is theoretical; the drill measures its real duration and exposes improvisation. |
| "An hour at 100% looked clean." | Load varies by time of day and jobs run daily; the claim stays at Live Proof until a full cycle passes. |
| "Delete the old store now; we have git." | Git holds code, not data; stores go after the rollback window with an export retained. |
| "The test double behaves like production." | Name where it is kinder, enforce the real limits in it, and run against a production-shaped copy. |

## Red flags

- The inventory came from search alone, or Unknowns is not empty at the first weight step.
- Characterization tests were written after the new code, or fail against the old path.
- Both sides of a parity comparison read the same store, or the control is stubbed.
- An unnamed normalizer, or a second normalizer for the same mismatch class.
- The candidate's result reached a caller with the flag off, or writes were shadowed to a shared store.
- An undo row written after its action, or a stage advanced without drill evidence.
- A soak reported as passed before its window closed, or a scheduled check that reports instead of acting.
- An old handler removed while its schedule, token, or route still exists.
- A column renamed or dropped in the same deploy as the code that needs the change.
