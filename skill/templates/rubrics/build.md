# Rubric · build · <goal slug>
frozen: <ISO UTC> · commit <short sha> · copied from templates/rubrics/build.md by drive:architect
applies to: <milestone names or claim keys>
derived from: <path or URL of a known-good comparable artifact | none>

<!-- Fill every placeholder, delete trait rows whose trait is not on the run, and commit before the
first maker starts. Never edit during a verification loop; between units append to Amendments with a
DECISIONS.md entry. Each criterion reads: observation (what an agent can see), oracle (what decides
it), refutation (the observation that makes it false), threshold (blocking, should_fix, or note, with
the number where one applies). A criterion that cannot apply to the deliverable is reported as
`rubric_gap:`, never failed and never skipped silently. Rules: references/verification.md. -->

## Standing floor
<!-- Always in scope. Never a rubric gap. -->

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| No weakened tests | no skip, focus, or ignore marker without a quarantine ticket; no assertion removed or widened without a spec change | `drive.py guard` exit 0 before each integration commit; marker grep and test-file diff over the range | a marker without a ticket; an expected value changed while SPEC.md is untouched | blocking |
| Harness no kinder than production | every double and local runtime in scope has kindness-ledger rows with existing mitigation evidence | TESTPLAN.md ledger and limits probe results | a double with no row; a passing test that the real limit would fail | blocking |
| No data loss | every destructive step had a verified backup and a written undo before it ran | undo records and DECISIONS.md timestamps against the command log | a destructive command logged before its undo or backup | blocking |
| Security holds | no secret in tracked files; no authorization check removed or bypassed | secret scan over the range; security review file when the trait applies | a matched secret; a protected route reachable without its check | blocking |

## Process

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Claims before code | every claim's TESTPLAN.md row was committed before its implementation | `git log` order of TESTPLAN.md against the implementing commit | an implementation committed before its row | should_fix |
| Limits probed | the limits probe ran on the current toolchain for every platform in play | probe results versions against lockfile and `--version` output | a platform with documented limits and no probe, or stale versions | blocking |
| Verifier ran the gates | each verdict's `ran` holds the project test command at exit 0 in that round | verdict.json | the command absent, or taken from another agent's output | blocking |
| Constraints measured | `.drive/CONSTRAINTS.md` rows carry commands and measured values the codebase met when measured | the file and its first commit | a threshold the codebase failed at measurement | should_fix |
| Lessons honoured | every rule quoted under "Lessons that apply" in the briefs holds in the diff | the lessons list against the diff | a change doing what a quoted rule forbids | blocking |
| Values have sources | every number in verdicts, STATUS.md, and REPORT.md names its source | reading | a number with no source, or a local value presented as live | blocking |

## User outcome

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| <Primary job in words> | a user completes <job> end to end on <surface> | drive:verifier or drive:ui-reviewer drives the running build and reads state through the accessibility tree or the API | an inert control, a dead end, or a shown value that differs from the stored one | blocking |

## Shape criteria

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Rungs match evidence | every STATUS row's rung is supported by its evidence tokens | STATUS.md against proof directories and latest verdicts | a rung above what its latest verdict supports | blocking |
| Contracts hold on both sides | each provider and consumer passes the contract tests over the shared schema or fixture files | contract tests run by the verifier on both sides | a fixture one side accepts and the other rejects | blocking |
| Dependencies point one way | modules depend only in capability-map build order | `<import graph command>` | a cycle, or a dependency against the build order | should_fix |
| Failure behaviour observable | each claim's failure behaviour (offline, denied, over quota, partial failure) happens as SPEC.md states | tests that inject each failure | a crash, a 5xx, or silent success under the injected failure | blocking |
| <Hot path> within budget | <metric> at most <budget with unit> in <environment> | `<measurement command>`, value labelled with its source | measured over budget, or not measured | should_fix; blocking above <hard limit> |
| Calls per request bounded | <hot path> issues at most <n> queries and <n> outbound calls | counting-wrapper test | a count over budget | should_fix |
| Live rows proven live | every row with live `y` has a response from the deployed environment that agrees with local | `live.md` and `proof.json` environment | local-only evidence behind Live Proof, or a live mismatch | blocking |
| Setup docs run | README install, test, and run commands succeed from a clean copy | the verifier runs them in a fresh `mktemp -d` directory and removes it | a documented command that fails | should_fix |
| Clean end state | no worktree, branch, or uncommitted path the run created remains after the final commit | `git worktree list`, `git branch --list`, and `git status --porcelain` compared with `.drive/local/baseline.json` from `drive.py init` | an entry absent from the baseline | blocking |

## Trait additions

| trait | criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|---|
| `auth` | Abuse cases refuted | every abuse case in the threat model has a passing severe test | TESTPLAN.md severe table, verifier run | an abuse case without a test, or one that succeeds | blocking |
| `api` | Deployed contract | each route's deployed response matches the contract schema | schema validation of live responses | a live response the schema rejects | blocking |
| `data` | Down path exercised | each migration's down path ran and a restore from backup was tested on a copy | command log | a down path or restore never executed | blocking |
| `async-scheduled` | Triggered now and idempotent | each handler was triggered through its own verb, and a second run is a no-op | live or harness run with state read before and after | a second run changes state, or evidence waits on a schedule | blocking |
| `concurrency` | Interleavings refuted | named orderings of <operations> produce the claimed state | severe tests forcing each ordering | a lost write or duplicate under a forced ordering | blocking |
| `ui` | Design contract met | ui-reviewer reports zero blocking and zero major findings, with the observation counts references/ui-verification.md section 7 sets | `findings.json` | a blocking or major finding, or a review below those counts | blocking |
| `native-platform` | Runs on the simulator | build, launch, capture, and tree read succeed on <device and runtime> | ui-reviewer or `xcodebuild test` evidence | a launch failure; device-only features above Local Proof without a reason | blocking |
| `ai-llm` | Eval set measured | pass rate on <eval set> at least <n> percent, cost per call at most <amount>, prompt version recorded | eval run output with source label | below threshold, or not measured | blocking |
| `cli` | Golden outputs | each command's output and exit code match goldens, including `--help` and hostile arguments | golden tests | a mismatch | blocking |
| `public-api` | Examples run | every documented example compiles and runs as a test; semver decision recorded | example tests; DECISIONS.md | a failing example, or a breaking change without a major version | blocking |
| `prose-content` | Statements traced | every factual sentence traces to a RESEARCH.md entry or a repository file | grader claim-trace table | an unsupported sentence | blocking |

## Amendments
<!-- Append only, between units. -->
- <ISO UTC> · <criterion added, removed, or reworded> · because <rubric gap or ruling> · DECISIONS.md <date>-<slug> · applies from <unit>
