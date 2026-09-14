# <surface> — review disposition

<!-- Template: skills/mission/templates/disposition.md (references/review.md F3–F6, C1–C7, Procedure B8–B10).
     File: .mission/reviews/<surface>-disposition.md, written by the orchestrator. One "## Round <N>" section per round,
     newest last. Every finding in the round gets exactly one disposition row. Keep rows one line; prose only for
     CONTESTED and RESIDUAL items. S missions: the Dispositions table + Convergence check go in the PR description or
     TASK-CARD.md. Replace the example rows. -->

## Round <N> of <cap> · class <S|M|L|XL>

- Findings: `.mission/reviews/<surface>-findings.md#round-<N>` · Refutations: `.mission/reviews/<surface>-refutations.md`
- Reviewers: <lens → agent, e.g. CORRECTNESS → mission-reviewer; SECURITY → mission-critic> · Commit reviewed: <sha>
- Scope: <initial | remediation diff <base>..<head> + callers of <symbols> + constructions of <FND-ids>> · Full-surface
  reason (if any): <e.g. fix exceeded 30% of surface LOC>
- Review types selected (R1) → trigger evidence: <CORRECTNESS → 180 LOC touching settle(); SECURITY → webhook signature
  check changed> · Not selected: <PERFORMANCE: no perf requirement, no hot-path change>
- Verdict as written by reviewers: <clean | not closed — k blockers, m majors (before refutation)>

Dispositions: **FIXED** (commit + test that fails without the fix, verified against the original construction) ·
**REFUTED** (evidence that the construction does not hold) · **RESIDUAL** (accepted limitation, rationale, owner,
D-entry) · **DEFERRED** (target milestone + owner + why the proof cannot exist now; deferring a surface that already
exists is goalpost-moving) · **CONTESTED** (premise disputed, evidence, escalated to <adjudicator | human>).

| ID | Sev | Class | Refutation | Finding (one line) | Disposition | Evidence / pointer |
|---|---|---|---|---|---|---|
| <FND-checkout-03> | blocker | zero-row-write-as-success | CONFIRMED | settle() treats a zero-row UPDATE as success | FIXED | commit <a1b2c3>; `tests/webhooks/settle.test.ts::replay_is_idempotent` fails on parent (`.mission/logs/T-041/fix-proof.txt`); construction re-run: `.mission/logs/T-041/construction-03.txt` |
| <FND-checkout-04> | major | missing-idempotency-key | REFUTED | refund() can double-refund on client retry | REFUTED | unique index at `migrations/0007.sql:14`; second insert raises constraint error (`.mission/logs/T-041/refute-04.txt`) |
| <FND-checkout-05> | minor | unbounded-retry | none | webhook retry has no max attempts | DEFERRED | M3, owner <T-058>; the queue adapter enforcing attempt budgets lands in M3; proving test named: `queue_budget_exhausts` |
| <FND-checkout-06> | major | key-encoding-mismatch | CONFIRMED | canary obligation key contradicts migration 0001 | CONTESTED | maker cites `SPEC.md#15.1` (components named, serialization unspecified) and `obligations/identity.ts:12`; escalated to <mission-critic>; see CONTESTED notes |
| <FND-checkout-07> | minor | log-noise | none | pre-existing: verbose logging in legacy handler | DEFERRED | pre-existing (R6); backlog owner <name or T-id> |

### Sub-findings (F4)

A parent is FIXED only when every sub-finding below has its own disposition.

| Parent | Sub-finding | Disposition | Evidence / pointer |
|---|---|---|---|
| <FND-checkout-03> | <FND-checkout-08 (own ID, `parent: FND-checkout-03`): replay after partial failure> | <FIXED> | <test name + log path> |

### CONTESTED notes

- <FND-id>: reviewer position <one sentence + evidence path>; refuter/maker position <one sentence + evidence path>;
  adjudicator <agent>, verdict <CONFIRMED | REFUTED>, evidence <path>. A new construction from the adjudicator goes back
  to refutation.

### Outside-contract observations (F6)

| Source (reviewer / verifier) | Observation | Triage decision |
|---|---|---|
| <mission-reviewer> | <file:line — what> | <new task T-NNN | backlog (owner) | dropped: reason> |

### Residuals

Each accepted limitation is stated plainly as what is NOT claimed, with owner and D-entry. The gate becomes
`PASSED-WITH-WAIVER(D-id)`.

- <FND-id> · <limitation, e.g. "audit packet contents are not parsed against the pair; the CI writer is trusted"> ·
  owner <name | role> · <D-NNN> · review by <date | milestone>

### Verification after remediation

Fresh runs after the last fix commit <sha>, by a verifier that did not make the fixes.

- `<gate command>` → exit <code>; <salient output line> (`.mission/logs/<T-NNN>/<file>`)
- F5 construction checks: <FND-ids> → <verifier report path, e.g. .mission/lanes/T-041/verify-3.yaml>

### Convergence check (C1–C5)

- C1 — CONFIRMED blockers/majors this round: <n>; still open after fixes: <n>
- C2 — Round <N> of cap <cap> (class <S|M|L|XL>; security-sensitive: <yes|no>) · review spend vs build spend:
  <x tokens / y tokens> (`BUDGET.md`)
- C3 — Next scope if re-reviewed: <remediation diff <base>..<head> + callers <symbols> + constructions <FND-ids>>
- C4 — Class CONFIRMED in this round and the previous one: <class | none> → design review surface opened:
  <design-<mechanism> | no>
- C5 — Instrument share of CONFIRMED findings (round ≥ 3): <x% | n/a> → instrument audit task: <T-NNN | no>
- Decision: <CLOSED (gate PASSED) | CLOSED WITH RESIDUALS (PASSED-WITH-WAIVER(D-NNN)) | SCOPED RE-REVIEW (round N+1) |
  DESIGN REVIEW (C4) | INSTRUMENT AUDIT (C5) | ESCALATED (to <adjudicator | human: BLOCKED-HUMAN>)>
- Recorded in: STATUS.md gate row <gate name> · missed-defect escapes this round: <none | lens + class → C7 tier-up>
