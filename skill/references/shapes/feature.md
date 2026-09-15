# Shape: feature

Read this at intake when existing code hosts the deliverable, including a "fix" whose expected
behaviour never existed, and again at the start of every phase. It decides the phase order for a
feature, how deep archaeology goes, how the blast radius chooses the discipline, how new code
matches the codebase's dialect, what each phase leaves behind and who checks it, and what Done
means. A feature on an existing product fails less often by not working than by being written in a
different dialect from its neighbours or by quietly breaking one of them, so the recorded baseline
and the whole existing suite carry as much weight here as the new claims.

## When it applies

The goal adds or extends behaviour inside code that exists: a new screen, endpoint, report, command,
or option. There are no variants. When the change turns out to relocate or replace behaviour that
consumers depend on, it is a `move`; when the defect it describes once worked, it is a `fix`. When a
technology is new to the codebase, the `research-needed` trait inserts a `research` line before spec.

## Phases

| Phase | Entry | Work and agent | Artifact | Exit check (checker) |
|---|---|---|---|---|
| intake | the goal | classify; restate block; build, focused-test, and full-suite commands in the probe (orchestrator) | GOAL.md | committed before other work (orchestrator) |
| archaeology | GOAL.md committed | read the repo's self-description and machinery, run each documented command once, map touched topology, history of the touched area, blast radius, dialect (drive:researcher); measure CONSTRAINTS.md today at M and above (orchestrator) | `how-it-works.md` with its Blast radius and Dialect sections; CONSTRAINTS.md | full suite run with counts recorded; consumers of touched code listed; radius scored (orchestrator) |
| spec | archaeology exit | change spec from `templates/change-spec.md`, with Blast radius and Dialect copied from `how-it-works.md`: claims as headings, each with what would prove it wrong; out of scope; assumptions with reversal cost; `.drive/capability-map.md` first when the feature bundles modules (drive:architect) | SPEC.md | every claim refutable and in scope (drive:architect in fresh context at S to M, one full round plus at most one scoped re-check, taking in the plan's design and test-plan lines at S; drive:auditor at L to XL, up to three full rounds) |
| design | spec pass | the delta: what is extended rather than added, contract and data changes, decisions; for `ui`, the design contract extracted from the existing design system (drive:architect; drive:designer told to match the existing system) | DESIGN.md delta and decision index; `design/` | pre-mortem finds no unstated contract change (same reviewer as spec; at M the review waits for the test plan and covers both) |
| test-plan | design written | claim to layer to test; kindness ledger; a golden of old behaviour for each shared contract touched (drive:architect) | TESTPLAN.md | every claim has a refutation test at the cheapest real layer; every double has a guard (drive:grader first confirms every claim has a row and every double a ledger row; then the combined design and test-plan review by drive:architect in fresh context at S to M, or drive:auditor's own test-plan review at L to XL, judges the layer and the kindness answers) |
| decompose | test-plan pass | packages with disjoint ownership, only when more than three (drive:architect) | `.drive/packages/<id>/brief.md` | no shared paths in a wave; each brief names claim, command, owned and forbidden paths (orchestrator) |
| build | decompose exit and a recorded baseline | packages in the shared checkout; integration per package (drive:implementer; orchestrator commits) | code, tests, one commit per package | gates green, `drive.py guard` exits 0, ownership audit clean (drive:verifier: one at S, one per wave at M, per package at L to XL and for any package carrying an auth, money, or data-loss claim) |
| verify | build exit | handoffs by the unit `references/verification.md` section 2 sets for the size; `/code-review <level> <baseline_sha>...HEAD` in parallel, run by `drive:security-reviewer` in its code-review mode, level from `references/verification.md` section 5; conformance against SPEC.md (drive:verifier; drive:security-reviewer; drive:grader) | `.drive/proofs/<key>/r<n>/verdict.json` | pass; the whole pre-existing suite green with no test deleted, skipped, or loosened (drive:verifier) |
| live-proof | verify pass and the product has a deploy target | deploy to the product's existing staging or preview through its own tools; a request per endpoint; each role exercised with test accounts the environment already has (owner-set variables, checked with `test -n "${NAME+x}"` and never printed) or fixture users the product's seed command creates outside production, otherwise the per-role checks stay at Local Proof with the variable names under Blocked on; UI captured on the deployed build (orchestrator; drive:ui-reviewer) | `.drive/proofs/<key>/proof.json` with `environment: live` | `live:` evidence with `shim_differences` for every row whose live is y (drive:verifier) |
| harden | live-proof exit | severe tests on the new surface and every boundary the diff touches; security review when `auth`; UI review when `ui`; `/simplify <paths touched since baseline>` run by a `drive:implementer` under a package brief, then re-gate | severe tests; `.drive/reviews/` | findings dispositioned; baseline unchanged after simplify (drive:verifier) |
| docs | harden exit | user docs where a user would look; CLAUDE.md for anything a future session would rediscover; `how-it-works.md` updated (drive:writer) | docs; `doc:` tokens | commands and paths in docs run (orchestrator) |
| retro, report | docs exit, or the run stopped | lessons; REPORT.md; final audit by drive:auditor when the feature has five or more claims or the run is at L or above, otherwise a fresh drive:verifier running the same checklist | `.drive/reviews/<date>-final-audit.json`, REPORT.md | `drive.py lint --final` passes (orchestrator) |

Every classification, spec, design, and test-plan review round writes
`.drive/reviews/<date>-<phase>-review-r<n>.md`; the bounds by size and what a scoped re-check reads
are in `references/verification.md` section 6.

## Archaeology and the blast radius

Read what the repository says about itself (CLAUDE.md, rules files, README, docs) and list every
operational claim. Read the machinery that cannot drift (build, CI, deploy, and test configuration)
and run each documented command once. Read history only for the touched area: the last twenty
commits on those paths, reverts, and chains of follow-up fixes, which mark fragile seams. Write
`how-it-works.md` from `templates/how-it-works.md` in at most 150 lines, tagging each statement with
the template's evidence tags and ending with its drift table and "Could not verify" list. Fix dangerous drift at once in its own commit; fix the rest inside the
feature's commits.

For every symbol, route, table, or contract the feature touches, list direct callers, transitive
callers up to an entry point, contracts affected, flags gating the path, tests covering it, and
consumers outside the repository, in `how-it-works.md`'s Blast radius table. Score the radius and let
it choose the discipline:

| Radius | Discipline |
|---|---|
| small: one entry point, no external consumer | this file as written |
| medium: several entry points or one external consumer | add a characterization golden of the old behaviour on each shared contract before changing it, and put the new path behind a flag |
| large: many entry points or several external consumers | re-classify to `move/migration` even if the goal reads like a feature |

A list of dependants does not say why none of them breaks. At the spec phase `drive:architect` fills
the change spec's `Safe because:` line with the one fact that keeps every dependant in the table
working, in one sentence, and the test or command that proves it, or `unproven`. `drive:severe-tester`
receives that line as a claim to refute.

Run the full suite before any change and record passing, failing, and skipped counts with the commit.
This baseline is the entry gate for build: without it, a green run afterwards cannot tell a working
feature from a suite that was already red or quietly loosened.

## Dialect and build discipline

Find the three nearest existing examples of what you are adding (a route for a route, a screen for a
screen) and record their shape in `how-it-works.md`'s Dialect section, which the architect copies into
the change spec: file placement, naming, error handling, validation, logging, configuration access,
test location and naming. New code copies that shape.
Where a helper does most of what is needed, add a parameter or a sibling beside it with its tests
green rather than forking it. Use the existing design system's tokens and components.

Land the feature as commits that each leave the suite green: a preparatory refactor first and alone,
then the contract or data change (expand-only, with a tested down path and a backup before any
destructive step), then the behaviour, then the docs. Tests go in the existing suite with the same
runner, directories, and fixtures, named for the claim they try to break, and every verification runs
the whole suite. Measure the hot path before and after with the same input; a change that adds a
store read per request on a hot path states the measured number in its commit message. A pre-existing
defect found nearby goes to STATE.md's Open failures with a repro path and is not fixed inline unless
it blocks the feature, in which case it becomes a `fix` sub-goal that runs first. Dead code is deleted
only with zero-reference evidence in its own commit.

## Size

| Size | What runs |
|---|---|
| XS | a small addition in one source file, plus its test, with a known shape: inline, no `.drive/`, one refutation test, commit body with claim and evidence; trait gates still run |
| S | one module: GOAL, STATE, STATUS with one to three rows; a SPEC.md under 300 words (What changes, Must not change, and the claims with their refuting scenarios); archaeology findings in STATE.md Verified facts; design and test plan are lines in GOAL.md's plan, reviewed with the spec in one round plus at most one scoped re-check; no decompose; one verifier |
| M | everything in the table: `how-it-works.md`, SPEC.md, TESTPLAN.md, CONSTRAINTS.md; a spec review, then one combined design and test-plan review, each one full round plus at most one scoped re-check; a verifier per wave, with packages carrying auth, money, or data-loss claims verified alone; a severe test per claim, scaled to the diff |
| L | two surfaces: research when technology is new, the contract change written before either side, live proof required, lessons, auditor review of spec, design, and test plan of up to three full rounds each, a verifier per package |
| XL | phase gates with a re-classification review by `drive:auditor` and Workflow fan-out for read-only sweeps; usually a sign that a `build` sub-goal is hiding inside |

## Trait gates that commonly attach

| Trait | Effect |
|---|---|
| `ui` | design contract extracted from the product before UI code; `drive:ui-reviewer` judges every state the screen can be in (loading, empty, error, populated) at desktop and phone widths against an existing screen |
| `api` | contract tests on request, response, and error shapes; Live Proof needs a request against the deployed endpoint |
| `auth` | only when the diff touches identity, money, or personal data: security review, plus access tests for unauthenticated, wrong-role, and other-tenant requests |
| `data` | expand-only schema change, tested down path, backup before destructive steps; a read against an existing table counts only when the test double is not the real engine |
| `async-scheduled` | trigger the job now through its own tools; idempotency and replay tests |
| `perf` | hot-path baseline, same script after, benchmark kept |

**Displayed metrics.** When the feature shows numbers (a dashboard, a report view, an analytics
card), every displayed metric is its own claim heading in SPEC.md and its own STATUS row, and the
spec states for each: the source (table, event, or API, with the column), the formula, the unit and
scale, the time zone that decides a day, the aggregation window, the refresh cadence, what an empty
bucket shows, what a partial current bucket shows, and the oracle fixture whose correct value is
known before the code runs (`references/spec.md` section 11). Ambiguity in these definitions is the
usual defect in this kind of feature, and a number that renders plausibly passes every visual gate.
The fixtures compute the correct value independently and cover a day boundary in a non-UTC zone, an
empty bucket, a zero denominator, an average of averages, and a partial current bucket;
`references/domains/web.md` holds the full list and the metrics registry.

## Verification centre, Done, parallelism

The centre of gravity is the recorded green baseline before the change, one refutation test per new
claim, the whole pre-existing suite after it, and vision when `ui` applies. The bound is 3 verifier
rounds. Done means every new claim row is at its target rung with evidence; the pre-existing suite
passes with no test deleted, skipped, or loosened (the guard and the final audit both check the
diff); Live Proof exists when the product is deployed; the docs mention the feature where a user
would look; CLAUDE.md carries anything a future session would otherwise rediscover; and the drift
archaeology found is fixed.

Parallelism is moderate: archaeology lanes run together, and once the contract change is fixed, packages
on either side of it (an endpoint and a screen) run in parallel in the shared checkout, at most eight
per wave. Do not use worktrees for feature work on an existing product: a fresh checkout's dependency
drift produces failures that are not real.

**Re-classify** when a new table or store change appears (add `data`, insert backup and rollback
before build continues); when a new role or permission appears (add `auth`); when a cron, queue, or
webhook sits on the touched path (add `async-scheduled`); when the blast radius scores large (move);
when a blocking pre-existing defect appears (a `fix` sub-goal first); and when the module count passes
the size ceiling (size up and add ceremony only to the remaining phases).

## Excuses and rebuttals

| Excuse | Rebuttal |
|---|---|
| "The suite was green last week." | Only a baseline recorded on this commit can tell a regression from a suite that was already red. |
| "My pattern is cleaner than theirs." | A second dialect is a second place to fix every bug; copy the nearest example and log the improvement as a discovery. |
| "Copying the helper is faster than extending it." | A fork doubles every future fix; extend it with its tests green. |
| "Only the new tests are relevant." | Features break neighbours through shared helpers; the whole suite runs on every verification. |
| "That old test was outdated, so I adjusted it." | Changing an existing assertion needs a spec change and a DECISIONS.md entry; otherwise it lowers the bar. |
| "It works locally and staging is the same." | Local is Local Proof; Live Proof needs a request against the deployed environment. |
| "Docs can follow in a later change." | Docs and CLAUDE.md belong to the same commit series, because docs deferred to a later change are rarely written. |

## Red flags

- The first build commit precedes any recorded baseline suite result.
- New files placed or named differently from their three nearest neighbours.
- A new helper whose body duplicates an existing one.
- A pre-existing test removed, skipped, or given a looser assertion.
- One commit mixing a refactor with new behaviour.
- A verification round that ran only the new tests.
- A per-request store read added on a hot path with no measured number.
- Commands or paths that archaeology proved wrong still present at Done.
