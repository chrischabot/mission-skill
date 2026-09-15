# Shape: build

Read this at intake when nothing that exists hosts the deliverable, and again at the start of every
phase. It decides the phase order for new work, when a capability map precedes the spec, what wave 0
contains and why a walking skeleton goes live before breadth, what each phase leaves behind and who
checks it, how each size thins the plan, and what Done means. A build carries the largest number of
phases because every decision is still open, and its characteristic failure is that each half works
while the product does not, so contracts, the skeleton, and integration are separate gates.

## When it applies

The goal names something new with no code for it in the working directory. Before assuming a
greenfield, look for a sibling repository the goal names; if one hosts the deliverable, the shape is
`feature`, and SKILL.md section 2 step 0 moves the run there. There are no variants: a data pipeline, a command-line tool, and a library
are builds with the `data`, `cli`, or `public-api` trait. Read the owner's conventions and any sibling
repositories at intake, and check that the resource names the design will need (services, databases,
buckets, domains) are not already taken.

## Phases

| Phase | Entry | Work and agent | Artifact | Exit check (checker) |
|---|---|---|---|---|
| intake | the goal | classify; restate block; conventions and name collisions checked (orchestrator) | GOAL.md | committed before other work (orchestrator) |
| research | GOAL.md committed | unknowns inventory; one question per decision; lanes and probes on scratch resources (drive:researcher; reconciliation with `model: "opus"`; drive:grader re-opens cited sources) | RESEARCH.md | every blocking question answered or held as an assumption with a refuting test; conflicts filed with a next check (orchestrator; drive:grader for citations) |
| spec | research exit | capability map when warranted, then claims per module as headings, each with what would prove it wrong; out of scope; assumptions with reversal cost (drive:architect) | SPEC.md | claims refutable, constraints cite RESEARCH.md slugs (drive:architect in fresh context at S to M, one full round plus at most one scoped re-check, folded into the combined design and test-plan review at S; drive:auditor at L to XL, up to three full rounds) |
| design | spec pass | architecture per surface; the contract between surfaces written before either side; data model; decision index; the parity list of production limits the tests must honour; pre-mortem; the design contract when `ui` (drive:architect; drive:designer) | DESIGN.md; `design/DESIGN.md`, `design/tokens.json`, `design/screens.yaml` | review passes and the parity list is complete, which blocks (same reviewer as spec; at S and M the review waits for the test plan and covers both) |
| test-plan | design written | claim to layer to test; kindness ledger; limits probe; `planned:` evidence in STATUS (drive:architect) | TESTPLAN.md; STATUS.md rows | one refutation test per claim at the cheapest real layer; every double has a guard, a live check, or an accepted risk (drive:grader first confirms every claim has a row and every double a ledger row; then the combined design and test-plan review by drive:architect in fresh context at S to M, or drive:auditor's own test-plan review at L to XL, judges the layer and the kindness answers) |
| decompose | test-plan pass | packages with disjoint ownership; wave order from the capability map's build order; wave 0 defined (drive:architect) | `.drive/packages/<id>/brief.md`; GOAL.md plan | no two packages in a wave share a path; each brief names claim, command, owned and forbidden paths (orchestrator) |
| build | decompose exit | wave 0 alone, then waves of at most eight implementers; integration and commit per package; CONSTRAINTS.md measured after wave 0 and before wave 1's first integration commit (drive:implementer; orchestrator) | code, tests, commits | gates green, `drive.py guard` exits 0, ownership audit clean (drive:verifier: one at S, one per wave at M, per package at L to XL and for any package carrying an auth, money, or data-loss claim) |
| verify | a wave integrated | at M one handoff per wave that also covers the seams, split only when its claims exceed the handoff budget; at L to XL a handoff per package plus a wave verifier on the seams (`references/verification.md` section 2); conformance against SPEC.md (drive:verifier; drive:grader) | `.drive/proofs/<key>/r<n>/verdict.json` | pass; rows at Local Proof (drive:verifier) |
| integrate | all waves verified | the whole system end to end locally, as a user would use it, plus one check against the real system (orchestrator) | `.drive/proofs/<key>/` | end-to-end smoke passes (drive:verifier) |
| live-proof | integrate pass | deploy each surface through its tools; requests against deployed endpoints; the client against the deployed backend; external calls from the deployed runtime; UI captured on the real surface (orchestrator; drive:ui-reviewer) | `proof.json` with `environment: live` or `device` | every row whose live is y has `live:` evidence with `shim_differences` (drive:verifier) |
| harden | live-proof pass | the full hardening order: severe tests, security review when `auth`, UI review, `/simplify` run by a `drive:implementer` under a package brief then re-gate, docs review | severe tests; `.drive/reviews/` | blocking findings fixed with regression tests (drive:verifier) |
| docs | harden exit | README, runbook, and a `how-it-works.md` for the next session (drive:writer) | docs; `doc:` tokens | documented commands run from a clean checkout (orchestrator) |
| retro, report | docs exit, or the run stopped | lessons; REPORT.md; final audit, always (drive:auditor) | `.drive/reviews/<date>-final-audit.json`, REPORT.md | `drive.py lint --final` passes (orchestrator) |

Every classification, spec, design, and test-plan review round writes
`.drive/reviews/<date>-<phase>-review-r<n>.md`; the bounds by size and what a scoped re-check reads
are in `references/verification.md` section 6. At S and M the reviews exist to find blocking gaps
early, not to polish: the linkkeeper run's later rounds did find real gaps, but three full rounds per
artifact cost about three hours before any code at M.

## Research

Research answers a named decision. Before searching, write the question and the decision that
changes with the answer; when no decision changes, decide and record it instead. Every entry states a
class (verified fact, source claim, inference, conflict). A claim about how an external system behaves
is a verified fact only when the primary documentation was read in full and a probe ran against the
real system on a scratch resource, at the boundary (the limit and one past it). A search snippet is a
lead, not evidence. Record the disconfirming search even when it finds nothing, and never smooth a
contradiction into "results vary". Budget per question: three to ten tool calls for one fact, two to
four lanes for a comparison. When a budget runs out, record the conservative assumption and the test
that will refute it. `references/research.md` holds the ledger template and the lane brief.

## Capability map

When one goal bundles capabilities that have their own users or data, could ship and be verified
separately, or could be dropped without rewriting the others, write `.drive/capability-map.md` from
`templates/capability-map.md` before SPEC.md. It gives one row per module with a plain-word name, its
responsibility, and the modules it depends on, then the build order. Dependencies point one way; two
modules that need each other are one module; the contract between two modules is specified in the
provider's section of SPEC.md. Each module gets its own `## Requirements · <module>` section, and the
build order becomes the wave order.

## Wave 0 and the walking skeleton

Wave 0 runs first and alone: the contract package, a skeleton with one path through every surface,
the test harness with every production limit from DESIGN.md's parity list enforced in its doubles,
the schema, the design tokens, and the ignore file. The ignore file covers every output the test
runner and the local runtime write (coverage data, `test-results/`, `playwright-report/`, junit XML,
screenshots a test saves, `.wrangler/` state, simulator result bundles), so a test run leaves no
untracked path for `lint --stop` to fail on and never rewrites a tracked file under a running review. At L and above, when live is in scope, wave 0 ends with the
skeleton deployed and exercised against real infrastructure: one request from the client through the
deployed backend and back, captured as `live:` evidence. Below L there is usually one surface, and
integrate's check against the real system is the first live contact. The skeleton is the cheapest
place to learn that the local harness is kinder than production; learning it after three waves were
verified against that harness reopens every one of them.

When deploying the skeleton needs a login or secret the run lacks, name it on a `credentials:` or `account:` Blocked on line in
STATE.md, record in DECISIONS.md that every row crossing that boundary is capped at Local Proof until
the skeleton runs live, and continue the waves against the platform's real local runtime. The first
action after the owner sets it is the skeleton's live check, then a re-run of the kindness ledger's
live checks.

After wave 0 lands, and before wave 1's first integration commit, measure the constraints floor into
CONSTRAINTS.md (test count, lint warnings, bundle or binary size, build time) with its direction and
tolerance; nothing exists to measure before wave 0.

A greenfield GOAL.md records `none` for the build, focused-test, and full-suite commands at intake,
because none exist yet. Wave 0's plan line creates them. When wave 0 lands, replace each `none` in
GOAL.md's probe with the real command, in the same commit as a DECISIONS.md entry naming each new
command: the lint compares the probe with the intake commit, and a changed command without that entry
fails `lint --final`. Until then verdicts need no full-suite run, which is also why wave 0 must not be
skipped.

## Size

| Size | What runs |
|---|---|
| XS | a script in one source file, plus its test, with a known shape: inline, no `.drive/`, one refutation test, commit body with claim and evidence |
| S | a small tool: GOAL, STATE, STATUS; research as one or two RESEARCH.md rows; design as a paragraph in GOAL.md; spec, design, and test plan reviewed together in one round plus at most one scoped re-check; decompose, integrate, and docs fold into build; one verifier |
| M | the full table with a short DESIGN.md; a spec review, then one combined design and test-plan review, each one full round plus at most one scoped re-check; a verifier per wave, with packages carrying auth, money, or data-loss claims verified alone; a severe test per claim, scaled to the diff; CONSTRAINTS.md |
| L | two surfaces: research lanes in parallel, contract first, live proof required, auditor review of spec, design, and test plan of up to three full rounds each, a verifier per package, lessons |
| XL | three or more surfaces: phase gates with a re-classification review by `drive:auditor`, an auditor mid-run audit after the walking skeleton, Workflow fan-out for research and review panels, per-phase budgets |

## Trait gates that commonly attach

| Trait | Effect |
|---|---|
| `ui` | design contract before UI code (drive:designer); capture matrix and `drive:ui-reviewer` per screen |
| `native-platform` | the simulator build, launch, screenshot, and accessibility-tree loop; device-only features stay at Local Proof with the reason |
| `api` | contract tests; Live Proof needs a request against the deployed endpoint |
| `data` | the parity list names every storage limit; backup and rehearsed rollback before destructive steps, even in a first version |
| `auth` | threat model from `references/security.md`; security review and severe tests on Opus before live proof |
| `external-systems` | sandbox and live recorded per system; owner-set secrets named, never invented; egress proven from the deployed runtime |
| `async-scheduled`, `ai-llm`, `deploy-infra` | trigger jobs now with idempotency and replay tests; an eval set and cost budget before build; a deploy plan with an undo per step and a smoke after |

## Verification centre, Done, parallelism

The centre of gravity is contract tests between surfaces, one refutation test per claim, the walking
skeleton proven live, vision on every screen, and an audit of every test double's kindness. The
bound is 3 verifier rounds per milestone, a milestone being one module of the capability map's build
order (or one wave without a map), plus 2 for the final integration and live proof pass. Done means
every claim row is at its target rung with a verdict; every surface with a real environment is at
Live Proof or better; Operational is claimed only when the goal says the thing must run in production
and `references/observability.md`'s standard is met; the final audit compared STATUS with the intake
commit of GOAL.md; docs exist; and no worktree, branch, or uncommitted path that the run created
remains, judged against the baseline `drive.py init` recorded, so the owner's own worktrees and
untracked files are left alone.

Parallelism is high: three to five research lanes run together, wave 0 runs serially, and later
waves run up to eight implementers in the shared checkout with verifiers spawned as each wave integrates at M and as
packages integrate at L and above. Review
panels and screenshot judging use the Workflow tool, which only reads. Parallel design arms in
worktrees are for a decision that reading cannot settle (`references/parallel.md` section 12).

**Re-classify** when existing code turns out to host the deliverable (feature); when payments or
personal data appear (confirm `auth`, add the provider as an external system); when the product calls
a model (confirm `ai-llm` and insert the eval set before build); when the surface count passes the
size ceiling (size up); when research overturns an assumption (re-derive from the affected phase);
and when a designed site or docs deliverable appears (a `publish` sub-goal).

## Excuses and rebuttals

| Excuse | Rebuttal |
|---|---|
| "Research is slower than building." | A design built on a remembered limit fails live after every wave has been verified against it. |
| "The spec is obvious from the goal." | Unnamed claims cannot be refuted, so the verifier ends up grading against the maker's idea of done. |
| "We can align the contract once both sides exist." | Two sides built to different shapes cost a rewrite; wave 0 fixes the contract first. |
| "Deploying the skeleton now is premature." | It is the cheapest moment to find that the harness is kinder than production. |
| "Every package is green, so the product works." | Halves that work and a product that works diverge at the seams; integrate and live proof are separate gates. |
| "The client against a mock backend proves the app." | That is Local Proof for the client and nothing for the system. |

## Red flags

- A SPEC.md constraint about a platform limit or external behaviour that cites no RESEARCH.md slug.
- A wave started before the contract it depends on exists.
- Two packages in one wave owning the same path, or a maker running git.
- A test double with no kindness-ledger entry.
- A STATUS row at Local Proof without `test:`, `severe:`, and `verdict:` tokens.
- "Live Proof" on a row whose `proof.json` names a local environment.
- Placeholder data, sample content, or invented configuration values in the deliverable.
- A branch or worktree left after a wave.
