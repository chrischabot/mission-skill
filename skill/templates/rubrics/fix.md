# Rubric · fix · <goal slug>
frozen: <ISO UTC> · commit <short sha> · copied from templates/rubrics/fix.md by drive:architect
variant: <fix | fix/incident | fix/perf> · applies to: <claim keys>
pre-fix commit: <sha from HUNT.md> · repro command: `<command from HUNT.md>`

<!-- Fill every placeholder, delete variant and trait rows that do not apply, and commit before the
fix is written. Never edit during a verification loop. Each criterion reads: observation, oracle,
refutation, threshold. A criterion that cannot apply is reported as `rubric_gap:`. Rules:
references/verification.md; test rules for fixes: references/testing.md section 11. -->

## Standing floor
<!-- Always in scope. Never a rubric gap. -->

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| No weakened tests | no skip, focus, or ignore marker added; no existing assertion removed or widened | `drive.py guard` exit 0; marker grep and test-file diff over the range | any such change without a quarantine ticket or spec change | blocking |
| Harness no kinder than production | the double or runtime that let the bug through now enforces the constraint, or a real-runtime test covers it | HUNT.md Harness and Fix lines with the class-fix test; the TESTPLAN.md ledger row at M and above | the harness still accepts the failing shape | blocking when a double was on the path |
| No data loss | any repair of bad data had a verified backup and a written undo before it ran | undo records against the command log | a data-changing command logged before its undo | blocking |
| Security holds | no secret in tracked files; no check weakened to make the symptom stop | secret scan; diff review | a matched secret, or a removed check | blocking |

## Process

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Reproduced before editing | the repro command failed for the brief's reason before any non-test source changed | HUNT.md reproduction line and `git log` order | a source edit committed before the recorded failure | blocking |
| Independent test author | for a complex bug, the failing test was written by an agent that had not seen a proposed fix | HUNT.md "written by" line and the brief that agent received | the test written by the fixing agent, or a brief containing a fix | should_fix |
| Predictions before experiments | each hypothesis row has its prediction written before its result | HUNT.md ledger | a result with no prior prediction | note |
| Verifier ran the gates | the verdict's `ran` holds the project test command at exit 0 and the pre-fix run | verdict.json | either run absent | blocking |

## User outcome

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| The reported symptom is gone | the brief's trigger now produces the expected outcome for <who is affected> | the repro command and the regression test on HEAD | the symptom under the brief's trigger | blocking |

## Shape criteria

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Red before, green after | the regression test fails on the pre-fix tree for the brief's reason and passes on HEAD | the verifier runs it in its own `git archive` copy of the pre-fix commit and on HEAD | green on the pre-fix tree, or red there for a different reason | blocking |
| Stable after | the regression test passes <n> repeated runs on HEAD when the bug was intermittent | repeat command output | any failure in the repeats | blocking |
| Cause explains the brief | HUNT.md's cause sentence accounts for symptom, frequency, environment, and since-when, and the diff changes that mechanism | HUNT.md against the diff | a brief field the cause leaves unexplained, or a diff line the cause does not need | blocking |
| Adjacent inputs hold | at least two inputs or conditions next to the brief's trigger give correct results | the severe tester's tests (at least one at every size) and the verifier's own adjacent attempts | an adjacent input that fails | blocking |
| No symptom patch | no retry, sleep, widened timeout, swallowed error, default value, or skip added, unless a ledger row proves the cause is external | diff scan | such a shape without that row | blocking |
| Siblings handled | the search for the same pattern ran and each hit is fixed or cleared with evidence | HUNT.md siblings line | an uncleared sibling | should_fix |
| Instrumentation removed | no temporary hunt logging remains | `git diff <pre-fix commit> \| grep -c "HUNT-<slug>"` prints 0 | a non-zero count | blocking |
| Suite intact and lean | the pre-existing suite passes; the maker added the failing reproduction plus at most one boundary test, with the class-fix shape test and the severe tester's tests counted separately | verifier run; new tests over the range grouped by author | a failing test (blocking) or a third maker-written test (should_fix) | as stated |
| Proven where observed | when the bug was seen live, the original condition replayed against the deployed fix passes with a request id or log line | `live.md` | local-only evidence while live is `y` | blocking |

## Variant additions

| variant | criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|---|
| `fix/incident` | Mitigation reversible | the mitigation's undo was written before it was applied, and the mitigation was removed after the live proof | HUNT.md mitigation block timestamps | undo written afterwards, or mitigation still in place at Done | blocking |
| `fix/perf` | Measured like the baseline | every attempt used the baseline's command, conditions, and repetitions | HUNT.md attempt ledger | a changed command or condition | blocking |
| `fix/perf` | Beats the noise | the kept change's median improvement exceeds the baseline's run-to-run spread with every test green | attempt ledger numbers with source labels | an improvement within spread, or a red or edited test | blocking |
| `fix/perf` | Neutral reverted | every attempt within noise or worse is reverted and still recorded | attempt ledger against `git log` | a neutral attempt kept, or a reverted attempt missing | should_fix |

## Trait additions

| trait | criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|---|
| `ui` | Visual fix without collateral | before and after captures at the reporting viewport and appearance show the fix, and the two neighbouring screens are unchanged | ui-reviewer captures and pixel diff | a changed neighbour not explained by the fix | blocking |
| `concurrency` | Ordering forced | the failing interleaving is forced deterministically in the regression test | the test's controlled scheduler or injected delay | a regression test that passes only by chance | blocking |
| `data` | Bad data repaired and counted | affected rows found by query, repaired, and the count re-checked | before and after query output | rows still affected | blocking |

## Amendments
- <ISO UTC> · <criterion added, removed, or reworded> · because <rubric gap or ruling> · DECISIONS.md <date>-<slug> · applies from <unit>
