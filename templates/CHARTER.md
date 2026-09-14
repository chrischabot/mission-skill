# Mission Charter · <mission name>

<!-- Template: skills/mission/templates/CHARTER.md → .mission/CHARTER.md (M+; S missions use TASK-CARD.md).
     M: fill sections marked ◆ only (≤1 page). L/XL: all sections (≤4 pages). Point, don't copy: class justification
     lives in STATUS.md, assumptions in ASSUMPTIONS.md, decisions in DECISIONS.md. -->

Class: <M|L|XL> (scores and justification: PROFILE.yaml) · Primary shape: <GRN|FEA|BUG|MIG|REF|UPG|DAT|PRF|INF|SEC|WEB|RSR|OPS> · Secondary: <≤2 or none>
Direction (verbatim from the human): "<original prompt>"
Status: draft | reviewed | approved-by-default (D-<NNN>) | approved-by-human · Last updated: <YYYY-MM-DD>

## ◆ 1. Outcome

<One paragraph: who gets what, and why it matters. No technology names.>

## ◆ 2. Goals

- G1 <outcome-shaped goal, e.g. "A person can plan tomorrow's outfit from their own wardrobe in one sitting">
- G2 <…>

## ◆ 3. Non-goals (plausible goals deliberately excluded)

- NG1 <e.g. "Social sharing or public profiles in v1">
- NG2 <…>
<!-- Not "the system shouldn't crash". A non-goal is something a helpful model would otherwise add back. -->

## 4. Users & stakeholders

| User / stakeholder | Primary job-to-be-done | Platform / context |
|---|---|---|
| <primary user> | <job> | <iPhone, daily, one-handed> |
| <owner / operator> | <job> | <…> |

## ◆ 5. Constraints

- Platforms / stack mandates: <e.g. SwiftUI iOS 17+, Cloudflare Workers + D1 + R2>
- Budget ceilings: money <n per month>; model spend <n per mission> (ledger: BUDGET.md)
- Deadline / timebox: <…>
- Compliance / privacy: <retention, deletion, consent>
- Must not change: <surfaces, APIs, data, tests that stay untouched>

## ◆ 6. Success metrics (technology-agnostic, measurable)

| ID | Metric | Threshold | Measurement method / oracle | Automated or live |
|---|---|---|---|---|
| OUT-001 | <e.g. new user saves a first outfit without help> | <≤3 min, 4 of 5 synthetic walkthroughs> | <scenario test + walkthrough> | <automated> |
| OUT-002 | <…> | <…> | <…> | <live (PENDING-LIVE until run)> |

## ◆ 7. Assumptions

Index only; the ledger is `.mission/ASSUMPTIONS.md` (A-NN, reversal cost, confirmation, verification).
High-reversal-cost assumptions still open: <A-01, A-03>

## 8. Questions asked (≤3 per round, ≤2 rounds)

| Round | Question | Options (★ = recommended default) · consequence per option | Answer / ASSUMED (unconfirmed) | Assumption |
|---|---|---|---|---|
| 1 | <Which platforms ship in v1?> | ★ iOS only · smaller build, Android later / iOS + web · +1 client surface, +contract tests | <answer> | A-01 |

## 9. Risks

| Risk | Likelihood (L/M/H) | Impact (L/M/H) | Mitigation / early signal |
|---|---|---|---|
| <…> | <…> | <…> | <…> |

## ◆ 10. STOP conditions (escalate to the human queue; never improvise)

- Two components would own the same record or external side effect.
- A test could pass without observing the outcome it claims.
- A step would delete or overwrite unclassified user data.
- A step would spend beyond <ceiling>, publish externally, send messages, charge money or rotate credentials without approval.
- A required decision contradicts a non-goal or constraint.
- <shape-specific stop, e.g. "unsourced comparative claim" (website), "both systems own a side effect" (migration)>

## ◆ 11. Definition of done

- **Product:** <user-observable outcomes; OUT-IDs PASS>
- **Engineering:** every normative ID registered with an oracle; `validate-registry.py` exits 0; acceptance.json checks
  PASS by a verifier; review findings dispositioned; spec and registry match the shipped behaviour.
- **Operational:** <deploy target, live checks, acceptance window>; live checks stay PENDING-LIVE until actually run.

## 12. Artefact plan

| Artefact | Needed? | Author (roster) | Notes |
|---|---|---|---|
| SPEC.md + requirements.yaml | <yes> | <mission-builder / mission-strategist> | <flat REQ ids (M) or domain ids (L/XL)> |
| design/BACKEND.md | <yes/no> | mission-builder | |
| design/FRONTEND.md + design/screens/SCR-NNN.md | <yes/no> | mission-builder | |
| design/adr/ADR-NNN.md | <which decisions> | mission-builder | |
| design/MIGRATION.md | <yes/no> | mission-builder | |
| design/WEBSITE-BRIEF.md | <yes/no> | mission-builder | |
| Spec review rounds (cap) | <M=1, L/XL=2> | mission-critic | human sign-off on L/XL: <yes / autonomous: notified, D-NNN> |
