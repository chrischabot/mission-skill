# Verification & adversarial review

Maker/checker separation, trigger-selected adversarial review, refutation, dispositions, convergence caps and loop
graders. Names follow `references/conventions.md`; if this file disagrees with it, conventions wins. Rule prefixes:
**V** verification · **R** review · **F** findings · **C** convergence · **G** graders · **S** classifier routing (not
the loop stop rules S1–S7 in SKILL.md).

## When to load

| Moment | What you need from this file |
|---|---|
| Phase 2 Spec / Phase 3 Design gate | R1 spec and design rows, R4 refutation, F templates. Spec-review caps stay lane C's (`spec-and-design.md`) |
| Phase 5 Build, every task gate | V1–V8, `templates/gate-verifier.md`; loop graders G1–G4 |
| Phase 6 Verify | V2 brief rules for the merged-result verifier (report format: `testing.md`) |
| Phase 7 Review | The whole Procedure |
| Phase 8 Release | Release-readiness lens, C6 integration-point panel |
| Any time | Reviewer refusal (S2), CONTESTED finding or missed-defect escape (C7), same defect class twice (C4) |

| Artefact | Template | Target path |
|---|---|---|
| Gate verifier prompt | `templates/gate-verifier.md` | brief; reply saved by the orchestrator to `.mission/lanes/<T-NNN>/verify-<n>.yaml` (milestone gates: `testing.md` report) |
| Reviewer prompt, lens blocks, personas | `templates/reviewer.md` | brief; reply appended by the orchestrator to `.mission/reviews/<surface>-findings.md` |
| Refuter prompt | `templates/refuter.md` | brief; reply appended by the orchestrator to `.mission/reviews/<surface>-refutations.md` |
| Finding schema | `templates/findings.md` | `.mission/reviews/<surface>-findings.md` |
| Disposition log | `templates/disposition.md` | `.mission/reviews/<surface>-disposition.md` |
| Grader rubric | `templates/grader-rubric.md` | rubric section of `.mission/loops/<loop-id>.md` (`templates/loop.md`) |

A **surface** is a stable id for one reviewable unit (`spec`, `design`, `auth`, `checkout-api`, `release`). One findings
file and one disposition file per surface; rounds append as `## Round <N>`. Finding IDs `FND-<surface>-NN` continue
across rounds and are never reused. Evidence files live under `.mission/logs/<T-NNN>/`.

## Core rules

MUST / SHOULD / MAY per conventions §9.

### Verification — maker/checker (V)

- **V1 MUST.** A gate state (`acceptance.json` `passes`, a STATUS gate `PASSED`, a task `PASSED`) changes only on a
  verifier verdict with cited evidence. The maker and the orchestrator MUST NOT change it on their own judgment; the
  orchestrator MAY transcribe a verdict mechanically, citing the report path.
- **V2 MUST.** The verifier brief contains only: (a) artifact locations (paths, commit or worktree, URL); (b) the
  acceptance criteria or rubric; (c) the evidence bundle — gate command outputs, the relevant **test files**,
  screenshots, fetched sources; (d) the spec excerpts the criteria cite. It MUST NOT contain the maker's transcript,
  reasoning, self-assessment or "what I changed and why" prose. `git diff --stat` output is allowed.
- **V3 MUST.** Verifiers are read-only on the artifact: read-only roster agents only, a clean worktree where possible,
  and `git status --porcelain` empty at the end. A dirty workspace voids the report.
- **V4 MUST.** Programs judge first: tests, typecheck, lint, build, schema and link checks run before any model verifier
  (models-and-cost.md GD1); red → skip the model call. The verifier re-runs or directly observes evidence and never
  accepts "tests pass". When a re-run exceeds the brief's time budget, it checks that the log exists, is newer than the
  reviewed commit, and came from the declared command.
- **V5 MUST.** Verdict per criterion: `PASS` (evidence cited) · `FAIL` (evidence cited) · `UNVERIFIED` (reason). A
  required criterion that is UNVERIFIED, skipped, quarantined or flaky keeps the gate `PENDING`. UNVERIFIED is never PASS.
- **V6 MUST** for blocker-capable gates (release, security, auth, money, data integrity, migrations): verifier tier ≥
  maker tier. **SHOULD** elsewhere: verifier differs from the maker in model or effort (models-and-cost.md GD2, GD8).
- **V7 SHOULD.** Contract before build: numbered, testable criteria (`AC-NNN`, or loop criteria in
  `.mission/loops/<loop-id>.md`) are agreed before the maker starts. Criteria raised after the build are
  outside-contract (F6).
- **V8 MUST.** Maker self-review is encouraged as a pre-flight, recorded as `self-check`, and never satisfies V1.

### Adversarial review (R)

- **R1 MUST.** Select review types from the trigger table; a type runs only when its trigger holds. "Every lens on
  everything" is forbidden. Record the selection (type → trigger evidence) in the disposition header.

| Review type | Trigger | Unit | Mandatory evidence bundle | Lens |
|---|---|---|---|---|
| Spec | Before build on M+, or any MUST without a test yet | spec + charter/brief | requirement list, acceptance criteria | `SPEC` (+ `templates/spec-review-rubric.md`) |
| Design / architecture | New component, cross-service boundary, persistence or concurrency model, migration plan, API contract between platforms | design doc + interfaces | spec excerpts, constraints, ADRs, CONTRACTS.md | `DESIGN` |
| Code correctness | Non-trivial change (≥ ~50 LOC, or touches state, IO, money, auth) | ≤ ~400 changed LOC | diff, tests, gate outputs | `CORRECTNESS` |
| Test quality | New/changed tests guarding a MUST; mutation survivors; suspicious green | tests + code under test | mutation/coverage output, requirement IDs | `TEST-QUALITY` |
| Security | Auth, permissions, secrets, untrusted input parsing, crypto, payments, CI config, dependency adds | changed surface + trust boundary | SAST / dependency-audit output, threat notes | `SECURITY` (Opus 4.8) |
| Performance | Stated perf requirement or hot-path change | code + benchmark | benchmark outputs, methodology | `PERFORMANCE` |
| UX / visual | UI change | screens / flows | screenshots, geometry/a11y probe output | `references/frontend-verification.md`; lens adds walkthrough findings only |
| Research fact-check | Deliverable with factual claims | claim list | fetched sources, URLs, access dates | `references/research.md` (`templates/fact-checker.md`) |
| Release readiness | Before deploy, publish, cutover, merge to a protected branch | gate register + residuals | all gate outputs, residual D-entries, rollback plan | `RELEASE` |

- **R2 MUST.** One lens per reviewer and a bounded unit: ≤ ~400 changed LOC or one coherent surface (one module, one
  API contract, one screen flow, one document). Split larger changes across reviewers.
- **R3 MUST.** The brief says: find defects that make the artifact fail its purpose; a clean report is a valid outcome;
  invented or speculative findings are failure; at most 5 nits; at most 15 findings ranked by severity, "truncated" if
  more exist.
- **R4 MUST.** Every candidate `blocker`/`major` passes a refutation pass before it reaches the maker: a separate agent
  (never the raising reviewer) tries to disprove it against the actual code and tests (`templates/refuter.md`). Only
  `CONFIRMED` findings block. `REFUTED` → disposition REFUTED with the refutation evidence. `UNVERIFIED` → question for
  the orchestrator; it cannot block.
- **R5 SHOULD.** Lens panels (2–4 parallel reviewers with distinct lenses) for L/XL surfaces and integration points; one
  reviewer for S/M or single-lens changes. Dedupe and rank panel output before refutation.
- **R6 MUST.** Defects outside the change are flagged `pre-existing`, never block the current change, and are
  dispositioned DEFERRED with an owner (backlog or target milestone).
- **R7 MUST.** Security review and exploit construction run on Opus 4.8 (`mission-critic`) from the start (S1).

### Findings and dispositions (F)

- **F1 MUST.** Findings use `templates/findings.md`: id, type, severity, `pre_existing`, lens, class tag, location
  (`file:line` or doc#section/URL), claim, construction, evidence, expected vs observed, impact, fix class, refutation
  block, related IDs. A finding without a reproduction (command + observed output) or a construction citing `file:line`
  for every step is filed as `type: question` and cannot block.
- **F2 MUST.** Severity per conventions §4: `blocker` · `major` · `minor` · `nit`; flags `pre-existing`, `question`.
  False gate evidence counts as "artifact fails its purpose" (blocker); a missing required negative case is an overstated
  completion claim (major). Nits never trigger a round.
- **F3 MUST.** Every finding gets exactly one disposition in `.mission/reviews/<surface>-disposition.md`: `FIXED`
  (commit + test that fails without the fix) · `REFUTED` (evidence) · `RESIDUAL` (rationale, owner, D-entry) ·
  `DEFERRED` (milestone, owner, why the proof cannot exist now — deferring work on a surface that already exists is
  goalpost-moving and not allowed) · `CONTESTED` (evidence, escalated to the tier-up adjudicator or the human).
  Silently narrowing a finding is itself a defect.
- **F4 MUST.** A parent finding is FIXED only when every sub-finding is FIXED or has its own disposition.
- **F5 MUST.** A FIXED disposition is verified against the **finding** (the original construction or reproduction now
  shows correct behaviour), not against the fix's own new test; the new test MUST fail on the parent commit.
- **F6 SHOULD.** Verifiers and reviewers list concerns outside the contract or lens under `outside_contract`; the
  orchestrator triages each (new task · backlog · dropped with reason). They never silently widen the gate.

### Convergence and stopping (C)

- **C1 MUST.** A surface's review closes when a round produces **no CONFIRMED blocker or major**. Minors and nits never
  trigger another round. "Zero findings" is not a stop condition.
- **C2 MUST.** Implementation review round cap per surface: **S=1 · M=2 · L=3 · XL=4** (initial round + scoped
  re-reviews); security-sensitive surfaces get at least 3. At the cap the options are: open CONFIRMED blocker →
  escalate (C7 adjudicator, then human `BLOCKED-HUMAN`); only majors or lower open → RESIDUAL with owner and a D-entry,
  gate `PASSED-WITH-WAIVER(D-id)`; or a design change (C4). Round N+1 of the same process is never an option. SHOULD:
  if review spend on a surface exceeds 2× its build spend (`BUDGET.md`), justify any further round in a D-entry.
- **C3 MUST.** Re-review scope = remediation diff + direct callers/consumers + the original findings' constructions.
  A full-surface re-review needs a stated reason in the disposition (e.g. the fix exceeds 30% of the surface's LOC).
  Remediation lands in small commits, one test per fix.
- **C4 MUST.** The same defect `class` CONFIRMED in two consecutive rounds → stop patching; open a design review of that
  mechanism as its own surface (`design-<mechanism>`, own cap). The original surface stays open until it lands.
- **C5 SHOULD.** From round 3, if more than half of CONFIRMED findings concern the instruments (tests that pass for the
  wrong reason, mutation targets, registry/traceability claims), switch to one bounded instrument-audit task (mutation
  causality, oracle strength; `testing.md`), then one re-review — not another full round.
- **C6 SHOULD.** Multi-milestone missions run automated gates at every milestone and heavy adversarial panels at
  integration points (walking skeleton complete, pre-release, pre-cutover). L/XL add one consolidated cross-surface
  review before release or cutover, then one focused re-review of remediated surfaces (cap 2 for that pair). Timing
  changes; the quality bar does not.
- **C7 MUST.** Tier up a reviewer only for a CONTESTED finding or a missed-defect escape (a defect found later in code
  the lens reviewed). An escape raises that lens one tier for the rest of the mission and adds the class to the lens
  checklist via `LESSONS-INBOX.md`. Never tier up just because another round runs.

> **What 18 rounds taught (arcwell Milestone 1)**
> - New-defect counts per round R2–R17: 14, 11, 7, 13, 15, 15, 13, 13, 7, 8, 15, 15, 18, 13, 19, 17 — no downward
>   trend. Stop on severity (C1), not on count.
> - Fixes became the defect source: 14 new defects from the first rework; 5 of 19 in R16 came from R15's fixes, "now the
>   pattern rather than the exception". Small fixes, scoped re-review (C3).
> - The delimiter/identity class recurred in R2, R4 and R17. Recurrence means the design is wrong (C4).
> - Late rounds were mostly about instruments (non-causal mutation targets, overstated registrations). Audit them
>   separately (C5).
> - R18's verdict was still "reject closure"; M1 closed "per the owner's direction". Caps make stopping a rule, not a
>   governance crisis (C2).
> - The amendment moved heavy review to one cross-milestone review with automated gates per milestone; it found 23
>   findings, and the focused re-review found 7 blockers, "several introduced by round one itself" (C6, C3).
> - What worked and is kept: no parent FIXED while a sub-finding is open, goalpost-moving deferrals rejected, CONTESTED
>   with cited evidence (F3, F4); quality compounded to 148/148 critical mutations killed and 283 integration tests.
> - Pointers: `research/mission-skill/06-verification-adversarial-review.md` §3.4 (lines 161–222) and the arcwell files
>   listed under Evidence.

### Graders (G)

- **G1 MUST.** Loop graders use binary criteria, each with a required-evidence field (`templates/grader-rubric.md`).
  Scored 0–4 scales only for taste dimensions, with anchors and examples; thresholds per `frontend-verification.md`.
- **G2 MUST.** Graders start every criterion at FAIL. A PASS without a cited artifact is treated as UNVERIFIED.
- **G3 SHOULD.** Calibrate before loop use on 3 known-good and 3 known-bad samples (or seeded defects: deleted guard,
  stale log, doctored exit code). 6/6 correct, else tighten wording or anchors and re-run. Record the result in the rubric.
- **G4 MUST.** The loop verdict is derived mechanically from per-criterion results (PASS only if every required and
  process criterion PASS). The grader MUST NOT soften or downgrade a failure in its own summary without a stated
  refutation. Keep-best: at the iteration cap the orchestrator keeps the best iteration, not the latest.

### Classifier routing (S)

- **S1 MUST.** Security review, threat modelling with exploit construction, and fuzz/pentest logic are assigned to
  Opus 4.8 from the start (`mission-critic` to review, `mission-builder` to write); never Fable (models-and-cost.md CF1).
- **S2 MUST.** If a reviewer, refuter or verifier refuses (`stop_reason: "refusal"` or the harness equivalent): discard
  its partial output, log the event in `STATUS.md → Model / fallback events` (CF2), and re-run on Opus 4.8 with the same
  brief (CF4). Never rephrase to evade the classifier (CF5). A second refusal on Opus → `BLOCKED-SAFETY`.
- **S3 MUST.** A refusal is never PASS or FAIL. The affected criteria or findings stay UNVERIFIED until the re-run
  completes.

## Procedure

### A. Gate verification (every task, loop iteration and phase gate)

1. **Contract (V7).** Confirm the criteria exist before the maker starts: `AC-NNN` in `acceptance.json`, loop criteria
   in `.mission/loops/<loop-id>.md` (paste `templates/grader-rubric.md`). For a model-graded loop on M+ or any taste
   loop, run calibration (G3) once and record it.
2. **Programs first (V4).** Run the declared commands (`.mission/check.sh <milestone>`, tests, typecheck, lint, build);
   outputs go to `.mission/logs/<T-NNN>/`. Red → back to the maker; no model verifier call.
3. **Bundle (V2).** Artifact paths + commit or worktree, criteria, log paths, the relevant test files, cited spec
   excerpts, `git diff --stat`. Drop every sentence of the maker's return except file paths and commands.
4. **Spawn** the verifier chosen in Model routing with `templates/gate-verifier.md`. For `mission-checker` batches,
   seed the canary (Model routing) from `BUDGET.md → Downgrade guards`; never mention it in any brief.
5. **Read the report.** Reject and re-spawn if `workspace_clean_after` is false, a PASS lacks cited evidence (G2), or
   the verdict does not follow mechanically from the criteria. Gate verdict: every required criterion PASS → PASS; any
   FAIL → FAIL; otherwise UNVERIFIED.
6. **Transcribe (V1).** PASS → `passes:true` / task `PASSED` citing the report path. FAIL → task `FAILED(iter n)`, the
   maker gets the failing criteria and evidence only. UNVERIFIED → gate stays `PENDING`; fix the check environment or
   route the criterion to the next tier (`mission-verifier` → `mission-reviewer`).
7. **Triage** `outside_contract` items (F6) into new tasks, backlog, or dropped-with-reason.

### B. Review round (per surface)

1. **Select** review types from the R1 trigger table. Write the selection with the trigger evidence into the disposition
   header. Skip every type whose trigger is absent.
2. **Chunk** (R2): ≤ ~400 changed LOC or one coherent surface per reviewer, one lens each. L/XL surfaces and integration
   points get a 2–4 lens panel (R5).
3. **Brief** each reviewer with `templates/reviewer.md`: skeleton + exactly one lens block (+ one red-team persona line
   on L/XL panels) + the trigger table's mandatory evidence (tests always included). Round > 1: scope per C3 and
   attach the previous round's disposition.
4. **Collect** findings into `## Round <N>` of `.mission/reviews/<surface>-findings.md`. With >1 reviewer, dedupe and
   rank (`mission-checker`). Re-file any evidence-free finding as `type: question` (F1).
5. **Refute** every candidate blocker/major in parallel with `templates/refuter.md` (R4). Append results to
   `<surface>-refutations.md` and copy verdict + evidence into each finding's `refutation` block. Apply a
   `severity_check` change only with its stated reason.
6. **Fix** CONFIRMED blockers/majors: small commits, each with a test that fails on the parent commit (F3). Minors are
   fixed inside the same task when cheap, else DEFERRED or RESIDUAL; they never cause a round.
7. **Verify remediation (F5).** Re-run the gates; spawn a gate verifier whose criteria are "the construction of
   FND-<surface>-NN now shows the expected behaviour" for every FIXED finding.
8. **Disposition** with `templates/disposition.md`: one row per finding, sub-findings (F4), residual D-entries,
   outside-contract triage, CONTESTED items sent to the adjudicator (step C).
9. **Converge** — evaluate in order, record the result in the disposition's convergence check:
   a. No CONFIRMED blocker/major this round, or all of them FIXED and F5-verified at the cap → **CLOSE**; gate `PASSED`,
      or `PASSED-WITH-WAIVER(D-id)` when residuals exist.
   b. Same defect class CONFIRMED in this round and the previous one → **DESIGN REVIEW** surface (C4); this surface
      stays open.
   c. Round ≥ 3 and >50% of CONFIRMED findings concern instruments → **INSTRUMENT AUDIT** task, then one re-review (C5).
   d. Round = cap (C2) → no more rounds: open CONFIRMED blocker → **ESCALATE** (step C, then `BLOCKED-HUMAN`); open
      majors or lower → **RESIDUALS ACCEPTED** with owner + D-entry.
   e. Otherwise → **SCOPED RE-REVIEW** round N+1: remediation diff + direct callers + original constructions (C3).
10. **Record** the gate row in STATUS.md, review spend in `BUDGET.md`, and any missed-defect escape (C7).

### C. CONTESTED adjudication and escapes

1. Give the adjudicator the finding, the refutation note, and the maker's counter-evidence as files (never a
   transcript). It must cite evidence; its verdict is final for this round.
2. A new construction raised by the adjudicator goes back to refutation (B5) before it can block.
3. Missed-defect escape: raise that lens one tier for the rest of the mission, log a D-entry, add a
   `LESSONS-INBOX.md` candidate naming the class.

### D. Mission level (C6)

- Deterministic gates at every task and milestone. Adversarial panels at integration points: walking skeleton complete,
  pre-release, pre-cutover, and milestone ends on L/XL.
- L/XL: one consolidated cross-surface review before release or cutover, then one focused re-review of remediated
  surfaces (cap 2 for that pair). Release readiness runs last, over the gate register and residuals.

## Scale by class (S/M/L/XL)

| Class | Verification | Adversarial review | Round cap (C2) | Panel (R5) | Refutation (R4) | Where findings live |
|---|---|---|---|---|---|---|
| S | Gate verifier on the task card's criteria (`mission-checker` for checklist evidence, else `mission-verifier`) | 1 reviewer, 1 lens chosen by trigger (usually CORRECTNESS on `mission-reviewer`) | 1 | no | candidate blockers/majors (usually 0–2) | PR description or `TASK-CARD.md` table (no `.mission/reviews/`) |
| M | Per-task verifier + loop grader | 1–2 lenses on the changed surface | 2 | optional | all candidate blockers/majors; 1-in-3 blocker refutations re-checked (Model routing) | `.mission/reviews/` |
| L | Per task + milestone verifier | Spec + design review before build; lens panel at milestone integration points | 3 | yes, 2–4 | as M | `.mission/reviews/` |
| XL | Per task + milestone + consolidated cross-milestone verifier | Automated gates per milestone; panels at skeleton, pre-release, pre-cutover; one consolidated review with a `mission-strategist-review` lens | 4 per surface | yes, 2–4 | as L | `.mission/reviews/`, one surface per milestone integration point |

At XL each milestone runs its own class's toggles (conventions §5). Risk traits (money, PII, auth, irreversibility) add
the security lens and V6 tier rules; the only cap change is the security-sensitive floor of 3 (Shape conditionals).

## Shape conditionals

- **IF** GRN multi-platform (API contract between platforms) **THEN** run a DESIGN-lens contract review on
  `CONTRACTS.md` before either side builds; contract-conformance tests are the verifier's evidence for both sides.
- **IF** GRN and the walking skeleton is live **THEN** run the first lens panel on the end-to-end path; do not review
  isolated layers in depth before it exists (C6).
- **IF** user data, auth or payments exist **THEN** the SECURITY lens (`mission-critic`) is mandatory at pre-release and
  auth/payment items join the human queue.
- **IF** there is UI **THEN** visual/UX verification per `frontend-verification.md`; the "first-time user in a hurry"
  persona runs at pre-release.
- **IF** BUG **THEN** the verifier's first criterion is "a failing reproduction exists and fails for the stated reason",
  re-run before and after the fix. A root-cause claim gets a refutation review of the causal story ("find an
  observation this explanation does not account for"; `debugging.md`). Code review is scoped to the fix diff + call
  sites, cap 2, no panel unless the fix touches concurrency or data integrity. Same bug class in two places → C4.
- **IF** FEA in an existing product **THEN** the evidence bundle includes `CONTEXT.md`, the repo's CLAUDE.md and
  neighbouring tests; reviewers check consistency with conventions, not their own taste. Lenses: CORRECTNESS +
  TEST-QUALITY (+ UX if UI). Behind a flag → release readiness checks the flag default and rollback path.
- **IF** MIG or REF **THEN** the primary verifier is a parity verifier (evidence: parity inventory, diffed outputs of
  old and new paths); model judgment is secondary. Mandatory lenses: data integrity/state and failure modes/rollback
  (`mission-critic`), SECURITY at trust-boundary changes. Consolidated review before cutover; focused re-review cap 2.
- **IF** an irreversible cutover, deploy or data migration step exists **THEN** release readiness runs on
  `mission-critic` with a human checkpoint; live gates stay `PENDING-LIVE`, never reported as passed.
- **IF** DAT **THEN** the data-integrity lens needs an executed migration on a copy as evidence, and rollback rehearsed.
- **IF** UPG **THEN** the verifier relies on the full suite plus a changelog breaking-change checklist; adversarial
  review covers only code changed to adapt.
- **IF** PRF **THEN** the verifier re-runs benchmarks with fixed seeds and hardware notes; the PERFORMANCE lens checks
  methodology (warm-up, variance, representative inputs).
- **IF** SEC or a security-sensitive change (auth, crypto, permissions, secrets, CI) **THEN** SECURITY lens on every
  change, round cap at least 3 on that surface, S2 refusal handling.
- **IF** WEB or any public factual claims **THEN** every claim is fact-checked against a fetched source
  (`research.md`); UNVERIFIED claims are removed or softened before publish. No code lens panel beyond build, links and
  accessibility gates unless custom backend code exists. Team, customer or market claims → human checkpoint.
- **IF** RSR **THEN** fact-check lens + "strongest counter-argument" persona; no code lenses.
- **IF** OPS **THEN** the verifier grades the dry run against eval cases; review covers the runbook and classifier rules.

## Model routing

Roster and IDs: conventions §6–§7; downgrade mechanics GD1–GD8 in `models-and-cost.md`. No Haiku anywhere: checklist
roles use `mission-checker`. A one-off tier-up is "`<agent>` with Agent-tool `model` override" and keeps that file's
effort; a different effort needs a different agent file.

| Role | Default agent | Escalate to | Guard that protects the default |
|---|---|---|---|
| Checklist gate verifier (command ran, exit 0, output matches, file exists, cited line satisfies the text) | `mission-checker` | `mission-verifier` when a criterion needs code read against the spec | **Seeded-defect canary** in ~1 in 10 verification units (never below GD3's floor): a planted known-bad item (stale log, doctored exit code, missing citation, `.only` in a diff) whose expected verdict is FAIL. A PASS on it voids the batch → re-run on `mission-verifier`, log the miss; a second miss → role promoted for the mission (ES7) |
| Per-task verifier (criteria read against code) | `mission-verifier` | `mission-reviewer` for judgment criteria; blocker-capable gates: tier ≥ maker (V6), `mission-critic` when the maker is `mission-builder` | V4 re-runs; GD4 blind audit sample |
| Merged-result / milestone gate verifier | `mission-critic` | + `mission-strategist-review` lens on XL release | clean-checkout runs, evidence per criterion |
| Loop grader | `mission-verifier` when every criterion is deterministic evidence; `mission-reviewer` when any criterion needs judgement over a Sonnet maker's work (models-and-cost GD2) | `mission-critic` for taste or complex correctness | **Every 5th PASS re-graded blind by `mission-reviewer`**; any disagreement → `mission-reviewer` grades the rest of that loop; the loop's final PASS is always re-checked by the gate verifier |
| Refuter | `mission-verifier` (never the raising reviewer) | `mission-reviewer` for concurrency, data integrity, auth; UNVERIFIED on a blocker → `mission-critic` | 1 in 3 blocker refutations re-refuted by `mission-reviewer`; one false refutation found → all blocker refutations on `mission-reviewer` |
| CORRECTNESS lens (state, concurrency, data) | `mission-reviewer` | `mission-critic` at integration points; XL consolidated review → `mission-strategist-review` (one lens) | missed-defect escape → that lens one tier up (C7) |
| TEST-QUALITY lens | `mission-verifier` | `mission-reviewer` when mutation survivors are disputed | mutation run output is the external oracle |
| SPEC lens | `mission-critic` | `mission-strategist-review` for XL greenfield master specs | reviewer differs from the spec author's tier or effort; blockers refuted against the brief |
| DESIGN / architecture lens | `mission-critic` | `mission-strategist-review` at XL or for irreversible-cutover migrations | L/XL human sign-off checkpoint |
| SECURITY lens | `mission-critic` | never Fable; human queue for auth, crypto, payments | SAST / dependency-audit output is mandatory evidence; S1–S3 |
| PERFORMANCE lens | `mission-verifier` (benchmark output) | `mission-reviewer` for algorithmic or design review | benchmarks re-run by the verifier (V4) |
| UX / visual | `mission-reviewer` per `frontend-verification.md` | `mission-critic` | that file's image canaries |
| Research fact-check | `mission-verifier` | `mission-critic` for public or load-bearing claims | quote must appear at the URL; 1 in 5 CONFIRMED claims re-checked by `mission-reviewer`, any wrong → re-check all |
| RELEASE readiness | `mission-reviewer` | `mission-critic` for irreversible deploys or cutovers | evidence per checklist item; human checkpoint before deploy |
| Dedupe / rank / format findings | `mission-checker` | — | orchestrator spot-reads one unit per panel |
| CONTESTED adjudicator (tier-up only, C7) | reviewer was `mission-verifier` or `mission-reviewer` → `mission-critic` | reviewer was `mission-critic` and not security → orchestrator adjudication at high effort; security → fresh `mission-critic`; then human | adjudicator cites evidence; a new construction goes back to refutation |
| Disposition triage | orchestrator (session model) | — | file-backed disposition log, reviewed at retro |

Cost rules: never put a whole-repo review on `mission-critic` — chunk (R2) and review the changed surface; refutation on
`mission-verifier` is the cheapest false-positive filter before a maker iteration; programs run before any model call
(V4); panels run at integration points, not at every task (C6).

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| The maker's summary ("all tests pass") accepted as evidence | V4: re-run or timestamp-check the declared log |
| Transcript leakage "for context" into a verifier brief | V2 whitelist; strip the maker's return to paths and commands |
| Lenient drift: grader finds a real issue, then talks itself into passing it | G4 mechanical verdict; G3 calibration |
| UNVERIFIED, rate limits, tool errors or refusals read as green | V5, S3: three-valued verdicts, gate stays PENDING |
| Instruments that cannot fail (stale mutation targets, tests passing for the wrong reason) | Seeded canaries; C5 instrument audit |
| Reviewer without the test files files false findings | R1 mandatory evidence column; tests always in the bundle |
| `/goal` or a model's "done" treated as a gate | V1: only verifier reports and `check.sh` flip gates |
| Unbounded rounds, "one more round to be safe" | C1 severity stop, C2 caps, escalate or accept residuals |
| Whole-surface re-review after every fix | C3 scoped re-review |
| Big-batch remediation that injects new defects | Small commits, one failing-without-fix test per fix, C3 |
| Patching the same mechanism round after round | C4 design review |
| Nitpick spiral: padded reports, style "fixes", another round | R3 nit cap 5; nits never trigger rounds; one lens per reviewer |
| Invented findings to look useful | R3 clean report valid; R4 refutation; F1 evidence or `question` |
| Every lens on every change (security panel on a doc typo) | R1 trigger table |
| Goalpost-moving deferral of a surface that already exists | F3: DEFERRED must say why the proof cannot exist now |
| Quiet narrowing: parent FIXED while sub-findings remain open | F4 |
| Inherited debt holding a small change hostage | R6 `pre-existing` flag |
| Rephrasing a brief around a classifier refusal | S2 re-run on Opus 4.8 with the same brief; log the event |
| Taste loops without keep-best | G4 keep-best iteration |
| Disposition docs hundreds of lines long per round | `templates/disposition.md` table; prose only for CONTESTED and RESIDUAL |

## Unverified harness details

| Detail | Status | Safe fallback |
|---|---|---|
| Read-only enforcement for agents with Bash | Bash can write; allow-lists do not prevent it | Clean worktree per verifier; `git status --porcelain` at the end (a detector, not a preventer); hooks from `settings.guardrails.json` / `protect-frozen.sh` where installed |
| How a refusal surfaces inside a Claude Code sub-agent | API docs describe `stop_reason: "refusal"`; sub-agent behaviour may differ (sticky, silent fallback) | Treat an empty or truncated return, refusal text, or an answering model different from the requested one as a refusal → S2; CF2/CF3 in `models-and-cost.md` |
| Round caps, the 2× review-spend guard, the >50% instrument threshold, the ~400 LOC chunk | Judgment derived from arcwell's pattern and human review studies, not measured for LLM reviewers | Log review spend, rounds and escapes per surface in `BUDGET.md`; tune at retro via `LESSONS-INBOX.md` |
| Evaluator leniency ("talks itself into" passing) and sprint contracts | From a secondary summary of Rajasekaran's post; primary fetch truncated | Rules stand on independent-context and calibration evidence (G3, G4) |
| Bias reduction of Claude-only panels | PoLL's gains needed disjoint model families | Lens, persona and effort diversity; refutation; programs first |
| Canary leakage | Makers or verifiers could learn canary shapes | Vary canary types; canary IDs live only in `BUDGET.md → Downgrade guards` and are never named in any brief |
| Dynamic workflows' adversarial verification | Availability varies by harness | Plain Agent-tool sub-agents with the same templates |
| Consolidated-review timing on XL greenfield | Arcwell's consolidated review came after all implementation; balance unvalidated | Contract/design review before build, automated gates per milestone, panels at integration points (C6) |

## Evidence

1. `research/mission-skill/06-verification-adversarial-review.md` — source report (§3.4 round table, §4 rules, §7 templates).
2. `arcwell/docs/operations/m1-eighteenth-review-disposition.md` L3–6, L47–57 — "reject closure", closed per owner direction, 148/148.
3. `arcwell/docs/operations/m1-rereview-disposition.md` L3–7, L36–38, L94–103 — 14 rework defects; sub-finding rule; check fix against the finding.
4. `arcwell/docs/operations/m1-sixteenth-review-disposition.md` L3–10; `m1-sixth-review-disposition.md` L9–11 — fixes as defect source; goalpost-moving.
5. `arcwell/docs/operations/review-process-amendment.md` L3–31 — consolidated review, gates each milestone, same quality bar.
6. `arcwell/docs/operations/m2-m7-review-disposition.md` L3–9, L39, L55–58, L93–114 — 23 findings, CONTESTED, missing test files, 7 blockers.
7. https://www.anthropic.com/engineering/harness-design-long-running-apps — separation helps; tuning a skeptical evaluator is tractable.
8. https://arxiv.org/abs/2406.01297 — self-correction works with reliable external feedback.
9. https://code.claude.com/docs/en/code-review — lens agents, verification step, Pre-existing severity.
10. https://code.claude.com/docs/en/workflows — adversarial verification; unverified is not refuted.
11. https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback — `cyber` refusals on benign security work.
12. https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/ — 200–400 LOC review units, checklists.
