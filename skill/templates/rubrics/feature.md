# Rubric · feature · <goal slug>
frozen: <ISO UTC> · commit <short sha> · copied from templates/rubrics/feature.md by drive:architect
applies to: <claim keys>
baseline: <baseline_sha> · baseline test log: <path of the archaeology test run>
derived from: <path of the nearest existing feature used as the pattern | none>

<!-- Fill every placeholder, delete trait rows whose trait is not on the run, and commit before the
first maker starts. Never edit during a verification loop; between units append to Amendments with a
DECISIONS.md entry. Each criterion reads: observation, oracle, refutation, threshold (blocking,
should_fix, or note, with the number where one applies). A criterion that cannot apply is reported as
`rubric_gap:`. Rules: references/verification.md. -->

## Standing floor
<!-- Always in scope. Never a rubric gap. -->

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| No weakened tests | no skip, focus, or ignore marker without a quarantine ticket; no assertion removed or widened without a spec change | `drive.py guard` exit 0 before each integration commit; marker grep and test-file diff over the range | a marker without a ticket; an expected value changed while the change spec is untouched | blocking |
| Harness no kinder than production | every double and local runtime the feature's tests use has kindness-ledger rows with existing mitigation evidence | TESTPLAN.md ledger | a new double with no row | blocking |
| No data loss | any destructive or schema step had a verified backup and a written undo before it ran | undo records against the command log | a destructive command logged before its undo | blocking |
| Security holds | no secret in tracked files; no existing authorization check weakened | secret scan over the range; security review file when the trait applies | a matched secret; a check bypassed | blocking |

## Process

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Baseline recorded | a green run of the pre-existing suite at `<baseline_sha>` was saved before the first change | the baseline log path and its commit | no baseline, or a red baseline not recorded as such | blocking |
| Claims before code | each claim's TESTPLAN.md row was committed before its implementation | `git log` order | an implementation before its row | should_fix |
| Verifier ran the gates | each verdict's `ran` holds the project test command at exit 0 in that round | verdict.json | absent, or taken from another agent | blocking |
| Lessons honoured | every rule quoted under "Lessons that apply" holds in the diff | lessons list against the diff | a change doing what a quoted rule forbids | blocking |
| Values have sources | every number in verdicts and REPORT.md names its source | reading | an unsourced number | blocking |

## User outcome

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| <Job the feature exists for> | a user completes <job> end to end in the running product | drive:verifier or drive:ui-reviewer drives the product and reads state through the tree or the API | an inert control, a dead end, or a shown value that differs from the stored one | blocking |

## Shape criteria

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Pre-existing suite unchanged | the baseline's test names all pass; no pre-existing test file edited | baseline log against the verifier's run; `git diff <baseline_sha>..HEAD -- <existing test paths>` | a baseline test missing, failing, or edited | blocking |
| Must-not-change invariants hold | each "Must not change" heading's guard passes | the named guard tests | a guard failing, deleted, or never written | blocking |
| New claims refuted honestly | each new claim's test sits at an honest layer and turns red under the verifier's mutation | verifier mutation in a disposable copy | a test that stays green under mutation | blocking |
| Adjacent behaviour intact | screens, routes, or commands sharing <navigation, data path, module> behave as at baseline | regression tests; ui regression captures | an adjacent output changed without a change-spec entry | blocking |
| Convention fit | new code follows the patterns named in the change spec; no second implementation of an existing helper; no new framework | diff against the example paths; `<search command for near-duplicate helpers>` | a forked helper, or a dependency without a DECISIONS.md entry | should_fix |
| Scope held | changed files are in "Where it lands", tests, docs, or wiring | `git diff --name-only <range>` against the change spec | an unexplained file | should_fix |
| File size held | no changed file went from under about 1,000 lines at the range base to over at head without a reason in its package report | `git diff --stat <range>` for the changed files, then `wc -l` on each at base and head | a file that crossed about 1,000 lines with no recorded reason | should_fix |
| Live on the product's deployment | rows with live `y` have evidence from the existing deployment named in GOAL.md's "live means" | `live.md` | local-only evidence behind Live Proof | blocking |
| Docs match behaviour | user-facing changes are documented; no doc describes behaviour the code lacks | drive:grader docs check | a documented behaviour the code contradicts | blocking for a false doc; should_fix for a missing one |
| Metrics defined and recomputed | each displayed metric has a SPEC.md definition (source, formula, unit, time zone, window, refresh, empty, partial) and an oracle fixture whose expected value was computed independently; delete this row when the feature shows no metric | the definition block against the query code; the fixture test on HEAD asserting the data layer and the rendered text | a metric with a missing field, or a fixture whose expected value came from running the code under test | blocking |

## Trait additions

| trait | criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|---|
| `ui` | Matches the existing design system | ui-reviewer reports zero blocking and major findings, with the observation counts references/ui-verification.md section 7 sets; tokens and components come from the product's existing contract | `findings.json` against `design/DESIGN.md` | an off-contract value on a primary screen, or a review below those counts | blocking |
| `api` | Contract preserved and extended | existing clients' fixtures still validate; new routes validate against the schema live | contract tests; live schema validation | an existing fixture rejected | blocking |
| `auth` | Abuse cases refuted | each boundary the feature crosses has a passing severe test | TESTPLAN.md severe table | an abuse case that succeeds | blocking |
| `data` | Migration reversible | the schema step's down path ran; backfill verified by counts and a checksum | command log and verification output | an unexecuted down path, or a count mismatch | blocking |
| `async-scheduled` | Triggered now and idempotent | the new handler ran through its own verb and a second run is a no-op | state read before and after | a changed second run, or a status waiting on a schedule | blocking |
| `perf` | Budget met | <metric> at most <budget> in <environment>, same script as the baseline | measurement output with source label | over budget, or a different script | blocking |
| `existing-code` | Archaeology current | how-it-works.md drift table rows touched by the feature are updated | the note against the diff | a changed behaviour the note still describes the old way | should_fix |

## Amendments
- <ISO UTC> · <criterion added, removed, or reworded> · because <rubric gap or ruling> · DECISIONS.md <date>-<slug> · applies from <unit>
