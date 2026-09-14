# Grader rubric · loop <loop-id> · <T-NNN>

<!-- Template: skills/mission/templates/grader-rubric.md (references/review.md G1–G4, V7, Procedure A1).
     Paste into the rubric section of .mission/loops/<loop-id>.md (loop spec: templates/loop.md) BEFORE iteration 1.
     The maker sees Goal + Criteria + Process criteria + Taste dimensions; the grader sees the whole file. Seeded canaries
     are never listed here. Grader: `mission-verifier`; taste or complex correctness → `mission-reviewer`; every 5th PASS
     re-graded blind by `mission-reviewer` (review.md Model routing). Delete the Taste section if the artifact carries no
     taste. Replace the example rows. -->

## Goal

<one sentence, copied from the brief or charter; cites OUT-NNN / REQ-IDs>

## Criteria (binary; each names its evidence)

Every criterion is observable and decidable from evidence. No adjectives without a measurement.

| ID | Criterion (observable) | Evidence required | Required? |
|---|---|---|---|
| <AC-021> | `<pnpm test tests/checkout>` exits 0 with 0 skipped | command output at `.mission/logs/<T-NNN>/ac021.txt`, newer than HEAD, produced by that command | yes |
| <AC-022> | Replaying the same webhook twice produces exactly one settlement row | test name + assertion line; test fails on the parent commit | yes |
| <AC-023> | API returns 409 on idempotency-key conflict | curl transcript against the local server with the status line | yes |
| <AC-024> | No new lint warnings in touched files | lint output diff vs base commit | no |

## Process criteria (prevent early exit)

| ID | Criterion | Evidence |
|---|---|---|
| PC-1 | Every required criterion was attempted in this iteration | per-criterion lines in the grader output |
| PC-2 | Every FAIL item of the previous iteration was addressed or carried with a stated reason | diff of the two verdict files |
| PC-3 | <e.g. at least 20 experiments run and logged, for exploration loops> | <`.mission/logs/<T-NNN>/experiments.csv` row count> |

## Taste dimensions (optional; delete if not taste-bearing)

Scale 0–4. Threshold per `references/frontend-verification.md` (`templates/design-rubric.md`); anchors are images or
excerpts the grader can open.

| Dimension | 0 | 2 | 4 | Anchor examples | Threshold |
|---|---|---|---|---|---|
| <hierarchy> | no clear primary action | primary action findable after scanning | primary action obvious at first glance | `<.mission/design/references/anchor-hierarchy-0.png>`, `-2.png`, `-4.png` | <≥3> |
| <copy clarity> | jargon; user cannot say what the page offers | offer clear after reading body text | offer clear from the headline alone | `<anchor excerpts path>` | <≥3> |

## Grader rules

- Start every criterion at FAIL. PASS requires the named evidence, quoted or linked. A PASS without cited evidence is
  invalid and is treated as UNVERIFIED.
- Per criterion: `PASS` · `FAIL` · `UNVERIFIED` (evidence could not be produced; reason stated).
- Loop verdict is computed, never judged: `PASS` only if every required criterion and every process criterion is PASS
  and every taste dimension meets its threshold; any required FAIL → `FAIL`; otherwise `UNVERIFIED`.
- Do not add criteria mid-loop; new concerns go under `outside_contract`.
- Do not soften: no severity or result changes in the summary without a stated refutation.
- Return at most 3 highest-leverage fixes for the maker, each tied to a criterion ID. No style commentary outside the
  criteria.
- Record per-iteration pass counts so the orchestrator can keep the best iteration, not the latest.

Grader output (YAML only):

```yaml
loop: <loop-id>
iteration: <n>
commit: <sha>
grader: <mission-verifier | mission-reviewer>
verdict: <PASS | FAIL | UNVERIFIED>
criteria:
  - id: <AC-NNN | PC-N>
    result: <PASS | FAIL | UNVERIFIED>
    evidence: "<command -> exit code; quoted line | file:line quote>"
taste:
  - dimension: <name>
    score: <0-4>
    anchor_compared: "<anchor path>"
    evidence: "<screenshot path + pixel box>"
top_fixes: ["<AC-NNN: fix>"]
pass_count: <n required criteria PASS>
outside_contract: []
```

## Calibration record (G3; run once before iteration 1)

Samples: 3 known-good and 3 known-bad (or seeded defects: deleted guard, stale log, doctored exit code, missing
citation). The grader must classify 6/6; otherwise tighten criterion wording or anchors and re-run.

| Date | Grader agent | Sample | Expected | Grader verdict | Match? |
|---|---|---|---|---|---|
| <YYYY-MM-DD> | <mission-verifier> | <good-1: path> | PASS | <PASS> | <yes> |
| <YYYY-MM-DD> | <mission-verifier> | <bad-1: seeded stale log> | FAIL | <FAIL> | <yes> |

Result: <6/6 — rubric accepted | k/6 — changes made: <what>; re-run on <date>>

## Loop bounds

- Max iterations: <S 3 · M 5 · L 8; never more than 20> (SKILL.md loop stop rules).
- Futility: no newly passing criterion for 2 iterations, the same failure signature twice, or oscillation → stop, keep
  the best iteration, escalate along the maker ladder (`STOP-STALLED`).
- Budget: <token / cost / wall-clock cap from BUDGET.md> → `STOP-BUDGET`.
- Criteria cannot be met as written → `STOP-IMPOSSIBLE`; amend via D-entry or `BLOCKED`.
- Success: loop verdict PASS → `STOP-SUCCESS`, then the gate verifier re-checks (`templates/gate-verifier.md`); the
  loop PASS alone never flips a gate.
- Blind re-grade: every 5th PASS by `mission-reviewer`; any disagreement → `mission-reviewer` grades the rest of the loop.
- Best iteration so far: <iteration n, pass_count, commit>
