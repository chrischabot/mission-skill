# Spec & design review rubric · <mission name> · Round <n> of <cap>

<!-- Template: skills/mission/templates/spec-review-rubric.md. Used by the spec/design gate (references/spec-and-design.md,
     "Spec/design review"). The reviewer writes .mission/reviews/spec-findings.md (or design-findings.md) using
     templates/findings.md; the orchestrator writes reviews/spec-disposition.md using templates/disposition.md.
     Round caps: S = 0 (no review; the verifier checks the task card's acceptance line), M = 1, L/XL = 2. -->

## Rubric

Each item is binary per artefact: `PASS` · `FAIL` · `N-A` (with reason). Every FAIL becomes a finding with evidence.
Severity vocabulary is conventions §4: blocker · major · minor · nit; flags `pre-existing`, `question`.

| # | Criterion | FAIL looks like | Default severity |
|---|---|---|---|
| R1 | Goals and non-goals are outcome-shaped; non-goals are plausible goals deliberately excluded | "System shouldn't crash" as a non-goal; no non-goals | major |
| R2 | Every success metric has a threshold and a measurement method | "fast", "delightful" with no number or rubric | blocker for P1 outcomes, else major |
| R3 | Assumptions are in ASSUMPTIONS.md with reversal cost; high-cost ones were asked or marked ASSUMED (unconfirmed) | Silent defaults; an assumption stated as fact | major |
| R4 | STOP conditions exist and cover data loss, spend, external publication and dual ownership | No STOP list | blocker on L/XL, else major |
| R5 | Every normative requirement has a stable ID, an oracle kind and a falsifiable criterion; P1 journeys have Given/When/Then | Untestable requirement; behaviour in prose without an ID | blocker for P1, else major |
| R6 | No ambiguity: undefined terms, vague quantifiers, pronouns without referent, "etc.", contradictions, unmeasurable adjectives, open `[NEEDS CLARIFICATION]` on P1 | "support large files"; two sections disagree | major; blocker if it changes P1 behaviour |
| R7 | Failure coverage: every external boundary (network, provider, storage, user input, permission) has ≥1 unwanted-behaviour requirement with a fixture | Happy path only | blocker on L/XL, else major |
| R8 | Ownership & consistency: one owner per record and side effect; designs don't contradict the spec; registry matches spec (`validate-registry.py --spec` exits 0) | Two components write one table; API field differs between spec and design | blocker |
| R9 | Frontend verifiability: every P1 screen has regions with layout assertions, a full state matrix and platform a11y minimums (HIG / WCAG 2.2 AA) | "Clean layout"; missing empty/error states | blocker for P1 screens, else major |
| R10 | Backend soundness: platform limits cited with sources; store per entity justified; state machines with illegal transitions; idempotency and retries for every external call; security, privacy, cost addressed | D1 used for blobs; no retention for PII; retries without idempotency | blocker for PII/money/data, else major |
| R11 | Right-sized: depth matches class; ≥2 genuine alternatives in each design doc; ADRs for irreversible choices; no gold-plating beyond goals | 40 criteria for a one-screen change; design with no alternatives; feature contradicting a non-goal | major |
| R12 | Migration only: behaviour inventory keep/drop/change, parity criteria with thresholds, legacy owner disabled before new owner enabled, rollback triggers | "Same as before"; no rollback; dual ownership window | blocker |

Lens → rubric items: ambiguity & testability (R2, R5, R6) · failure modes & limits (R7, R10) · ownership & consistency
(R8, R12) · UX verifiability (R9) · security & privacy (R4, R10, R12 security) · right-sizing (R1, R3, R11).
Docs-only missions: R1, R3, R6 and the source-binding check only.

## Gate rule

- The gate is `PASSED` when no CONFIRMED blocker is open and every CONFIRMED major is FIXED, RESIDUAL (rationale, owner)
  or DEFERRED (milestone, owner, why this is not goalpost-moving). Minors and nits never block.
- A finding without a concrete failure scenario is a `question` and cannot block.
- Candidate blocker/major findings go to a refuter (`mission-verifier`, not the reviewer that raised them) before they block.
- Round 2 re-reviews only changed sections and their dependents.
- At the cap with a blocker still open: disposition CONTESTED → tier-up adjudication by the orchestrator at high effort
  with a D-entry, or the human queue on L/XL. No extra round without a D-entry; XL MAY run a third round only for a
  blocker in a section newly written in round 2.

## Reviewer prompt skeleton

```markdown
You are an adversarial specification reviewer. You did not write these documents and you have no access to the
author's reasoning or transcript. Assume the spec is broken until the documents prove otherwise.

Inputs (read all, from files): .mission/CHARTER.md, .mission/ASSUMPTIONS.md, .mission/SPEC.md,
.mission/requirements.yaml, <design docs>, this rubric, validator output <logs/validate-registry-<round>.txt>,
and, if round > 1, .mission/reviews/spec-disposition.md (re-review ONLY changed sections and their dependents).
Lens for this run: <ambiguity & testability | failure modes & limits | ownership & consistency | UX verifiability |
security & privacy | right-sizing>. Class: <M|L|XL>. Round <n> of <cap>.

Procedure:
1. For each rubric item in your lens, decide PASS / FAIL / N-A and cite the section and requirement ID.
2. For each FAIL write a finding: {id FND-spec-NN, rubric item, location (file § / ID), verbatim quote, failure
   scenario (what an implementer would build wrongly, or which test could pass while the outcome fails), severity
   (blocker | major | minor | nit), proposed minimal fix}.
3. Do not invent product scope. Concerns outside the rubric go under "Outside-contract observations" (non-blocking).
4. At most 12 findings, most severe first. Merge duplicates. No finding without a quote and a failure scenario.

Output (to .mission/reviews/spec-findings.md, no preamble):
1. Rubric verdict table: | Item | Verdict | Evidence (§ / ID) |
2. Findings list
3. Outside-contract observations
```
