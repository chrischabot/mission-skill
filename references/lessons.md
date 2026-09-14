# Lessons (promoted) · mission skill

<!-- Owner: promotion pipeline only (references/memory-and-lessons.md P8). Never edited mid-mission.
     Budget: ≤40 entries, ≤300 lines (lint: scripts/memory-lint.sh references/lessons.md). Grouped by phase.
     Entry fields: Rule · Applies when / Not when · Why · Evidence · Eval · Promoted · Seen · Last cited · Supersedes ·
     Confidence (low = 1 instance, medium = 2, high = ≥3 or reproduced by a verifier).
     Retire an entry whose eval passes on baseline without the skill, or uncited for 6 months → lessons-archive.md.
     SEED NOTE: L-001..L-007 were promoted by the skill author at creation (2026-09-14) from research evidence, not
     through the P8 pipeline. They carry `Eval: advisory` until an eval case exists in evals/evals.json. -->

How to use: at intake skim Contents and name matching L-ids in briefs (MEM-24). At retro check new candidates against
these entries for duplicates and contradictions (criterion f).

## Contents

- Review: L-001 · Verification and status: L-002, L-004, L-007 · Spec: L-003 · Execution and delegation: L-005 · Models: L-006

## Review

### L-001 · Cap adversarial review rounds; consolidate heavy review at integration points
- Rule: Cap adversarial rounds per surface by class (S1 · M2 · L3 · XL4), stop when a scoped round has no CONFIRMED
  blocker/major, scope re-review to the remediation diff plus its callers, and run the heavy cross-surface review once
  the integrated vertical exists. Never commission round N+1 by default.
- Applies when: iterating review → remediation → re-review on a stateful or multi-component surface.
  Not when: a single small diff with a deterministic oracle (one review pass is the cap anyway).
- Why: "zero findings" is not a reachable stop condition for an adversarial reviewer on a non-trivial system; late
  rounds mostly find defects introduced by the previous round's fixes, while later surfaces stay unbuilt.
- Evidence: 18 Milestone-1 rounds with new-defect counts 14, 11, 7, 13, 15, 15, 13, 13, 7, 8, 15, 15, 18, 13, 19, 17 and
  no downward trend (`research/mission-skill/06-verification-adversarial-review.md` §3.4 lines 161–189); closure came
  by owner direction, and the amendment moved review to one cross-milestone pass "after the full vertical product
  exists" (`arcwell/docs/operations/review-process-amendment.md` lines 3–5, 15–18, 25–31); the focused re-review still
  returned "seven blockers, several introduced by round one itself" (`arcwell/docs/operations/m2-m7-review-disposition.md` line 111).
- Eval: advisory · Promoted: 2026-09-14 · Seen: 1 project, 2 review phases (M1 rounds, M2–M7 re-review) · Last cited: —
- Supersedes: — · Confidence: medium

## Verification and status

### L-002 · Never report a live gate that did not run; keep it PENDING-LIVE
- Rule: A gate that needs a deployed environment, real provider, device, human or elapsed time stays `PENDING-LIVE`
  (mechanism delivered, evidence not yet run) until cited live evidence exists. Offline gates never stand in for it,
  and downstream irreversible steps (cutover, retirement, publish) stay blocked on it.
- Applies when: acceptance includes production, unattended, provider, device or human-evaluation criteria.
  Not when: the criterion is fully checkable offline and says so in acceptance.json.
- Why: green offline suites over fakes are easy to round up to "done"; the honest state keeps the remaining risk
  visible and blocks the steps that depend on it.
- Evidence: "No milestone may claim a live provider/unattended acceptance result that was not actually run"
  (`arcwell/docs/operations/review-process-amendment.md` lines 19–21); live acceptance "PENDING, deployment-bound …
  no live gate may be marked PASSED without cited evidence", cutover step 9 blocked until then
  (`arcwell/docs/operations/milestone-ledger.md` line 279).
- Eval: advisory · Promoted: 2026-09-14 · Seen: 1 project, 7 milestones · Last cited: —
- Supersedes: — · Confidence: medium

### L-004 · `/goal` is a nudge, never a gate
- Rule: Gates change state only on a verifier sub-agent's cited evidence or a deterministic script (`check.sh`, Stop
  hook). A `/goal` condition MAY drive a loop, and MUST name the command whose printed output proves it.
- Applies when: using `/goal`, Outcomes-style graders or any evaluator that sees only the conversation.
  Not when: never; there is no case where a transcript-only verdict flips a gate.
- Why: the `/goal` evaluator judges only what the transcript surfaced, does not run commands or read files, and
  defaults to Haiku on the Claude API (which this skill forbids).
- Evidence: https://code.claude.com/docs/en/goal, as read independently by three research lanes
  (`research/mission-skill/01-orchestration-control.md` lines 90, 967; `research/mission-skill/03-spec-design.md`
  line 79; `research/mission-skill/04-testing-strategy.md` lines 78, 260). Level: doc-source.
- Eval: advisory · Promoted: 2026-09-14 · Seen: doc-source, 3 independent reads · Last cited: —
- Supersedes: — · Confidence: high

### L-007 · Green offline gates are not a working product; wire a live walking skeleton first
- Rule: For anything that runs somewhere, the first build milestone MUST deploy the real entrypoint with real bindings
  and at least one real adapter to a dev environment and exercise one journey end to end. Requirements carry the
  production call path they are reachable from; reviewers get that path in their evidence bundle.
- Applies when: a mission builds or changes a deployed service, app or integration.
  Not when: pure libraries, offline tooling or research deliverables with no runtime.
- Why: suites over fakes and ports can all pass while production wiring is a no-op; review depth does not catch what
  no reviewer was shown.
- Evidence: every milestone of the user's XL project closed with automated gates green while the deployed hub served
  only `/health` with zero real provider adapters (`arcwell/docs/operations/gap-closure-plan.md` lines 3–22); the first
  live morning failed on wiring no review round had examined
  (`arcwell/docs/handoff/2026-08-21-morning-remediation-handoff.md` lines 72–88, 169–178;
  `research/mission-skill/12-arcwell-practice-evidence.md`). Level: production.
- Eval: evals/evals.json#1 (walking-skeleton assertion) · Promoted: 2026-09-14 · Seen: 1 project, 1 costly incident · Last cited: —
- Supersedes: — · Confidence: medium

## Spec

### L-003 · A requirement with no oracle is demoted, not weakened
- Rule: When a requirement's clause cannot yet be proven by a test that cites it, demote it (status `planned` or a
  later milestone) with a D-entry naming the gap and the bar for re-registration. Do not reword the requirement or
  loosen the test to make the gate green.
- Applies when: review or verification finds an `implemented` claim with no causal oracle, or the surface that could
  prove a clause does not exist yet.
  Not when: the defect is constructible now on the current surface; deferring it then is goalpost-moving and it is
  fixed instead.
- Why: a red gate that names its gap is honest progress; a weakened requirement silently lowers the bar and the
  defect ships.
- Evidence: "roughly forty requirements were moved back to `planned` … That is the gate working"
  (`arcwell/docs/operations/m1-adversarial-disposition.md` lines 12–15; `arcwell/requirements-curation.yaml` lines
  10–15); clauses moved to the milestone "that can prove those clauses", and a demotion judged goalpost-moving was
  restored (`arcwell/docs/operations/milestone-ledger.md` lines 47, 62).
- Eval: advisory · Promoted: 2026-09-14 · Seen: 1 project, ≥3 review rounds · Last cited: —
- Supersedes: — · Confidence: medium

## Execution and delegation

### L-005 · Sub-agents write long artifacts incrementally
- Rule: Any agent producing a document or file longer than ~1,200 words creates it with the first section, then
  appends one section per tool call, and checkpoints to its lane directory. Briefs say so explicitly.
- Applies when: a sub-agent writes reports, references, specs or other large single files.
  Not when: short files that fit in one small tool call.
- Why: a long single-shot generation can stall or fail and lose everything written; incremental writes keep partial
  work on disk and resumable.
- Evidence: "A previous lane stalled and lost everything by composing the whole report in one giant tool call"
  (`research/mission-skill/00-brief.md` lines 321–327), which made incremental writing a mandatory rule for every lane
  (`research/mission-skill/98-skill-architecture.md` lines 95–98).
- Eval: advisory · Promoted: 2026-09-14 · Seen: 1 observed incident · Last cited: —
- Supersedes: — · Confidence: low

## Models

### L-006 · Pin models by full ID; aliases drift
- Rule: Agent files, Agent-tool `model` overrides and headless `--model` flags use full model IDs
  (`claude-fable-5-1`, `claude-opus-4-8`, `claude-sonnet-4-6`). Intake checks the resolved model and records any
  fallback in STATUS.
- Applies when: any routing that depends on a specific model tier.
  Not when: never for this skill; if a full ID is unavailable, switch to the Degraded profile with a D-entry.
- Why: aliases resolve to whatever the provider maps today; on the Anthropic API `opus` and `sonnet` resolve to
  Opus 5 / Sonnet 5, silently breaking cost and capability routing.
- Evidence: https://code.claude.com/docs/en/model-config as recorded in
  `research/mission-skill/01-orchestration-control.md` lines 409–410, 898, 1000 and `skills/mission/references/conventions.md`
  lines 125–126. Level: doc-source.
- Eval: advisory · Promoted: 2026-09-14 · Seen: doc-source, 2 research lanes · Last cited: —
- Supersedes: — · Confidence: medium
