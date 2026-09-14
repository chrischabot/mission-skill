# Definition of done

Read this file before you move any STATUS row above Local Proof, before you describe status to the
user, before the final audit, and before you write REPORT.md. It decides what each rung of the ladder
means, the two bars every unit clears, what done means for each shape, how to describe work that is
not done and end a run that stops short of Done, when a target may be lowered and how, and the
checklist the final audit applies. The final reviewer, `drive:auditor` or a fresh `drive:verifier`,
uses section 6 as its rubric; the evidence tokens each rung requires are in
`references/state-files.md` section 7.

Contents
1. Two bars
2. The ladder
3. Done for each shape
4. Saying what is not done, and stopped runs
5. Targets and narrowing
6. The final audit
7. Excuses and rebuttals
8. Red flags

## 1. Two bars

Acceptance criteria belong to one claim and ask whether you built this thing. The definition of done
is the same for every claim and asks whether it is finished to standard. A unit is done only when
both hold. Never let acceptance criteria stand in for the standing bar, and never lower the bar
because a run is long, a bound was reached, or the remaining gap looks small.

The standing bar is joined to the ladder rather than kept as a second system: each rung above
Partial adds part of it (section 2). Ground truth is read in one order: working-tree code and tests,
then proof files, then STATUS.md, then prose. When a higher layer disagrees with a lower one, the
lower one is wrong, and the disagreement is a finding.

## 2. The ladder

Use these words and no others for status: Missing, Scaffold, Partial, Local Proof, Live Proof,
Operational, Done, and the side state Dropped.

| Rung | Means | What the standing bar adds |
|---|---|---|
| Missing | no code path or content exists for the claim | nothing |
| Scaffold | files, types, routes, stubs, or a README exist; nothing shows the behaviour | nothing |
| Partial | a passing test shows some of the behaviour; the claim is not fully covered, a path is stubbed, or the only verdict rests on reading code | nothing |
| Local Proof | the claim's tests and a refutation test pass in a local harness, run by a verifier whose verdict is pass, with the harness's kindness answered | acceptance criteria met; behaviour exercised at runtime by a test that fails without the change; the pre-existing suite still green; edge and error paths handled; no dead code, debug output, stub, or unrelated change; the CONSTRAINTS.md floor holds |
| Live Proof | the claim holds in the environment GOAL.md's `live means` names, checked by an agent that did not make the change, with output captured | works with the running system; migrations, flags, and configuration accounted for |
| Operational | live, and something will notice when it breaks | written on-call questions, structured events with a correlation id, a test-fired alert with delivery captured, and one induced failure located from telemetry alone (`references/observability.md`) |
| Done | code, tests, verdicts, live proof where `live` is y, docs, and STATUS all agree | documentation describes the current state; STATUS agrees with the proofs; the final audit says go |
| Dropped | deliberately not pursued | a `why:` and a DECISIONS.md entry in the same commit |

The evidence tokens each rung requires, which the lint enforces, are in `references/state-files.md`
section 7, the one copy of that table. This table says what the evidence means.

Rules that apply to every row:

- A claim's status is the weakest of its evidence, and every token points at a file that exists.
- Only a verifier's verdict, or the ui-reviewer's for `[ui]` evidence, moves a row to Local Proof or
  above. A maker's report, your reading of a diff, or a green run you watched moves nothing, and a
  verdict counts only when the provenance ledger shows the reviewer wrote it; one you wrote, copied,
  or edited fails the lint.
- Done's `review:` token points at `.drive/reviews/<date>-final-audit.json`. A security review, a
  design review, or any other review file cited as `review:` on a row does not satisfy Done.
- A verdict that rests only on reading code supports Partial at most. A row never sits above the
  `rung_supported` of its latest verdict, and a blocking gap moves it down to that rung.
- Local-only work is never Live Proof. A deploy command that exited zero, a local emulator, and a
  simulator talking to a mock are Local Proof. A simulator proof is Live Proof only when
  `proof.json`'s `target` shows it exercised the deployed backend. A site is Live Proof only when
  production serves the tested build; a preview deployment is Local Proof.
- A claim that only a physical device can prove carries `why:device-only:<reason>`. It reaches Local
  Proof without a physical device, Live Proof only with an `environment: device` bundle, and is never
  Done in a run without the owner's device. A claim blocked on the owner's developer team or account
  stays at Partial.
- `shim_differences` is always present; `[]` is accepted only with a note saying no double exists.
- A missing verification capability lowers the ceiling of the claims it would have verified. A
  skipped layer is written as skipped with its reason, never as green.
- Rows are never deleted, and you never reword a claim to fit what was built (section 5). When a
  claim's requirement text changes for any reason, its row drops to Partial until a new verdict
  round.

**Rows that are not code.** Report, publish content, and operate rows use the same tokens with these
meanings, so the lint can check them.

| Row kind | `test:` | `severe:` | `live:` |
|---|---|---|---|
| report or site claim | the grader's citation check, written by `drive:grader` as JSON and cited as `test:.drive/reviews/<date>-citations-<slug>.json::every citation resolves` (the lint accepts a JSON file under reviews for `test:` when it parses) | the adversarial reader's refutation record, `severe:.drive/proofs/<key>/r<n>/refutations.md::central claims attacked` | sites only: the deployed page captured by the ui-reviewer |
| operate step | the independent read-back command, `test:.drive/proofs/<key>/r<n>/observe.txt::<what was read>` | the check that the step's undo works, or that the unwanted effect is absent | the same read-back against the live system, `environment: live` |

**XS runs** have no STATUS.md. The commit body is the record, in this form:

```
<imperative subject>

Claim: <one sentence that could be false>
Evidence: <test path>::<test name> failed before the change (<one output line>) and passes after;
<build, lint, and test commands> ok
Security review: <verdict line and dispositions>        (only when auth applies)
```

At XS the security reviewer writes no file; its findings come back in its final message, and the
commit body records the verdict line and each finding's disposition. An XS run becomes S the moment a
second non-test source file changes, a workaround is needed, or the test cannot be made to fail
first; the refutation test's own file never counts as the second file.

## 3. Done for each shape

Targets are fixed at intake. Operational is the target only where the shape puts continued health in
scope, and for a service where it is in scope, a STATUS row for its operability must reach
Operational before the run can be Done.

| Shape | Default target for a `live` y row | Characteristic mirage |
|---|---|---|
| build | Live Proof; Operational when the goal says it must run in production | a scaffold or a simulator against a mock called done |
| feature | Live Proof when the product deploys, else Local Proof | new tests green while the old suite was loosened |
| fix | Live Proof when the bug was seen live, else Local Proof; `fix/incident` Operational | a fix with no reproducer seen failing |
| move | `move/migration` Operational; refactor and upgrade Local Proof, or Live Proof when deployed | the old path still on, or new behaviour smuggled in |
| publish | Live Proof when production is in scope; otherwise rows are created with `live` n at intake and stop at Local Proof with the promote command in the report | a well-laid-out page full of invented content |
| report | `live` is n; Done after the adversarial read | unverifiable claims quietly omitted |
| operate | Live Proof per step; Operational when the goal includes staying healthy | a command's exit code taken as the effect |

**build.** Every claim row is at its target with a verdict file. Every surface with a real
environment is at Live Proof or better; for an app with a backend, the app in the simulator
exercised the deployed backend end to end, and every screen in the claim list was visited,
screenshotted, and inspected through the accessibility tree. At L and XL the walking skeleton was
proven live at the end of wave 0. The final audit says go and the git audit is clean.

**feature.** Every new claim row is at its target. The baseline recorded at archaeology is green
again, with no pre-existing test deleted, skipped, or loosened; the auditor checks the diff for it.
Live Proof exists when the product deploys, and the docs mention the feature where a user would
look.

**fix.** A verifier ran the reproducer against the pre-fix commit and saw it fail, then against the
fix and saw it pass; the pre-fix run happens in a `git archive` copy at
`${TMPDIR:-/tmp}/drive-prefix-<key>` that the verifier makes and removes before its verdict returns. At
every size above XS, `drive:severe-tester` added at least one test on an adjacent input, which is the
row's `severe:` token. HUNT.md names the mechanism in one paragraph, the blast radius (callers and the
same pattern elsewhere) was checked, and the fix is committed. When the bug was seen in a live
system, that system, read through its own tools, no longer shows it. A fix without a failing-then-
passing test is Partial. When reproduction fails within budget, no row rises above Partial and the
run ends `stopped` with what was tried and what would make it reproducible. For `fix/incident`, the real fix is
live-proven, the mitigation is removed, and an alert or smoke check that would catch a recurrence
exists and was fired once during the run. For `fix/perf`, both numbers come from the same committed
script at named commits with run-to-run variance stated, every kept change beat that variance, and
the benchmark runs as a test with a budget.

**move.** For `move/migration`, every consumer in the census is served by the new path with parity
evidence; the old path is disabled, not merely unreferenced, in a commit; real traffic has flowed
through the new path with a log or metric to show it; and the rollback was exercised once. While the
soak is open its row stays at Live Proof and nothing is Done; the run sets `status: blocked` with a
`soak:` Blocked on line, and the scheduled check decides, acts, and resumes the run (`references/long-running.md`). No
package changed observable behaviour beyond the parity contract. For `move/refactor`, test output
before and after is identical apart from timing, public interfaces are unchanged, and no existing
test was modified. For `move/upgrade`, the build, the suite, and the runtime smoke are green on the
new toolchain as they were on the old, and `drive:ui-reviewer` compared the smoke screenshots.

**publish.** Every publish run deploys a preview. Production is in scope when the goal asks for a
launch or a production target already exists; then the site is deployed at its real URL and
production serves the tested build, meaning the deployed build's identifier matches the commit the
verdicts ran against. When production is out of scope, the rows were created at intake with `live` n
and that reason, the preview gates pass, and REPORT.md carries the one promote command. A preview
deployment is never Live Proof. Lighthouse performance and accessibility meet the thresholds GOAL.md
recorded at intake, measured against the deployed URL (production, or the preview when production is
out of scope), since a localhost pass says nothing about the CDN, redirects, fonts, or the production
build. `drive:ui-reviewer` judged the deployed pages at 360, 768, 1280, and 1600 px wide and in dark
mode, every navigation path was walked, links resolve,
and the blog and docs sections each render a real entry. Every factual sentence traces to a ledger
row or is labelled opinion, and no placeholder remains: no lorem ipsum, no TBD, no invented team
biography, no sample post.

**report.** `live` is n for every row, recorded at intake. A row is Local Proof when every claim is
labelled verified fact, source claim, or opinion, every citation resolves by the grader's check,
and contradictions are listed. It is Done when an adversarial reader on Opus attacked the central
claims and each attack has a disposition, the final reviewer spot-checked three claims against their
sources, and every claim that could not be verified is listed as unverified rather than dropped.

**operate.** Every step's undo was committed before the step ran. Every step's effect was read back
through the system's own read verbs by an agent other than the one that ran it; a command's exit
code is never the evidence. When the goal includes staying healthy, a smoke check or alarm exists and
fired once during the run. Nothing scheduled is reported as done.

## 4. Saying what is not done, and stopped runs

Name the rung, never the feeling. In STATE.md, STATUS.md, REPORT.md, commit messages, and messages to
the user, do not write "complete", "done", "finished", "shipped", "working", "fixed", or "live" about
anything below its target rung. Say the rung, what it rests on, why it is not higher, and the exact
step that would raise it:

- `Local Proof: the export claim passes its refutation tests locally; not deployed because the
  staging secret EXPORT_BUCKET_KEY is not set; after it is set, run npm run deploy:staging.`
- `Partial: the happy path runs; the retry path is stubbed at src/sync/retry.ts:48 and its test is
  skipped; the stub remains because the provider's retry header is undocumented.`
- `Scaffold: types and routes exist; no behaviour is implemented; nothing to verify.`
- `Local Proof, device-only: push registration passes in the simulator; delivery needs a physical
  device, so the row carries why:device-only:push delivery and cannot be Done in this run; the step
  that would finish it is a device run of PushTests.`
- `Live Proof, soak open: the new path has carried traffic since 10:40 UTC; the check
  migration-soak decides at 2026-09-15T10:40Z and rolls back through the undo in DECISIONS.md on
  failure.`

"Unverifiable" is never a rung. A row that cannot be checked stays at the rung it reached, with the
missing input named. Mid-run milestone lines take one form:
`<phase> passed; <claim> Partial → Local Proof; evidence .drive/proofs/<key>/r2/verdict.json`.

**A run that ends short of Done.** Device-only claims, a preview-only site, a bug that would not
reproduce, a spent budget, and a missing credential are ordinary endings, and each has an honest
status. When a stop condition in SKILL.md section 9 holds and every piece of work that does not
depend on it is finished, the retro is committed, and the final audit has run where one is required,
set `status: stopped`.
`drive.py lint --final` passes a stopped run when:

- every row below Done carries its reason where a reader finds it: a `why:` token (such as
  `why:device-only:<reason>`), an Open failure or the Blocked on line naming the row's key, or a
  DECISIONS.md entry whose `Narrows:` line names it;
- REPORT.md opens with `Stopped because <reason>`, reports every row at the rung it holds, and its
  rung counts equal STATUS.md's;
- no investigation is open;
- `.drive/reviews/<date>-retro.md` exists;
- when any row is above Missing, the latest `.drive/reviews/<date>-final-audit.json` is schema-valid,
  says `verdict: pass`, is no older than the latest code commit, and has a ledger entry backed by the
  transcript of the `drive:auditor` or `drive:verifier` that wrote it, exactly as for a done run; a run
  with no rows, or with every row at Missing or Dropped, needs no audit. A no-go audit does not
  satisfy this: address its findings, usually by narrowing rows with `why:` tokens or DECISIONS.md
  entries and fixing the report, and get a fresh passing audit;
- STATE.md, REPORT.md, and the rest of `.drive/` are committed, and nothing else the run created is
  left uncommitted, because `lint --final` runs the `lint --stop` hygiene checks.

`drive.py end` then closes the run, and the Stop gate treats `stopped` like `done`. A run left
`blocked` closes the same way, as stopped, once its Blocked on line begins with a stop-condition
token (`budget:`, `impossible:`, `destructive:`, `credentials:`, `payment:`, `legal:`, `account:`,
`two-diagnoses:`, or `soak:`) followed by the condition, and REPORT.md says "Stopped because";
`budget:` counts only once the maker spawns reached the subagent figure on GOAL.md's budget line or a DECISIONS.md entry
added since intake has a `Decision:` line that begins with `Stop` or `Narrow` and names the budget, and `credentials:`
must name the secret as an uppercase identifier containing an underscore or ending in `TOKEN`, `KEY`, `SECRET`,
`PASSWORD`, `PAT`, `CREDENTIALS`, or `CERT` (`credentials: CLOUDFLARE_API_TOKEN`), or as a name of two or more letters
in backquotes or double quotes. A
run the Stop gate marked `stalled` closes as stopped once REPORT.md says so
(`references/state-files.md` section 6). `drive.py end` closes a blocked or stalled run only after the
`lint --stop` hygiene checks pass, so STATE.md and REPORT.md must be committed, and any branch,
worktree, or untracked or dirty path the run created removed or committed, before `end`; the Stop gate
alone still lets a blocked or stalled turn end on a dirty tree. A status line alone never ends a run.
`stopped` is not `aborted`, which is kept for a run the owner ended or a goal ruled impossible as
written, and counts only when a DECISIONS.md entry's `Decision:` line begins with `Abort` or `Aborted` followed by
punctuation or the end of the line, as in `Decision: Abort; <why>`.

## 5. Targets and narrowing

- **Targets are fixed at intake.** GOAL.md is committed as `drive(intake): <slug>` before
  any other work. Every STATUS row's `live` value is fixed when the row is created, and a target
  below the shape's default is written beside its claim at that moment with the reason (no deploy
  target, a device-only feature, a missing capability, a prose deliverable).
- **Lowering a target** means any of: `live` y becoming n; a row moving to Dropped; a phase removed
  from the plan; a CONSTRAINTS.md value loosened; a claim reworded into an easier one. Each needs a
  DECISIONS.md entry in the same commit that says what was asked, what remains, why, the evidence,
  and the step that would restore it, and whose `Narrows:` line names the row's key or the phase. An
  unrelated DECISIONS.md change excuses nothing: the lint looks for the row's key or the phase name in
  the DECISIONS.md text added since HEAD, and at `--final` since the intake commit, and it reads a
  stopped run's reasons only from `Narrows:` lines.
- **Never reword a claim to fit what was built.** Add the narrower claim as a new row and move the
  original to Dropped with its decision, so both stay visible.
- **Never narrow because rounds ran out.** At a loop bound, the row takes the rung its last verdict
  supports and keeps its target; the gap is reported as not done.
- **Budget pressure narrows in a fixed order**, each step a logged decision that appears in the
  report: drop optional claims, narrow live proof to the critical path, accept Local Proof for named
  claims with a reason, stop.
- **GOAL.md changes only by appending** to `reclassifications` and `## Re-plans`. Its goal line,
  restate block, and intake plan are never edited.

Find every narrowing with commands, never from memory:

```bash
intake=$(git log --grep '^drive(intake): <slug>$' --format=%h -1)
git show "$intake":.drive/GOAL.md                         # the intake baseline
git diff "$intake" -- .drive/GOAL.md .drive/CONSTRAINTS.md # what changed in plan and floor
git log -p --format='commit %h' -- .drive/STATUS.md | grep -E '^[-+]\| '   # every row that ever existed, and every change to it
git log --format='%h' -- .drive/DECISIONS.md               # commits that carry a decision
```

## 6. The final audit

**Who and when.** `drive:auditor` runs it for `build`, `move`, every `fix/incident`, a `feature` with
five or more claims, and every run at L or above whatever its shape. For every other
run at S or above, a fresh `drive:verifier` applies this same checklist in its final-audit mode. The
grader never runs it. It runs after the retro is committed and REPORT.md is drafted, and before any
row becomes Done or STATE.md says `done` or `stopped`. A stopped run with any row above Missing is
audited too, because its report is where a plan is most easily described as a result, and
`lint --final` refuses it without a passing audit; a stopped run with no rows, or every row at Missing
or Dropped, has nothing to audit. On a stopped run, go means the report honestly states what was and
was not achieved, with every row at the rung its evidence supports and its reason recorded.

**The handoff** is built from files with `templates/handoff.md`: the goal slug, the intake commit,
`baseline_sha`, the recon commands from GOAL.md's probe, the range `<baseline_sha>..HEAD`, and the
paths of GOAL.md, STATE.md, STATUS.md, DECISIONS.md, the REPORT.md draft, `.drive/proofs/`, and
`.drive/reviews/`. Nothing you believe about how the run went goes in it.

**Sampling.** Check every row when there are ten or fewer. Otherwise check ten rows plus every row
at Live Proof or Operational and every row whose target was lowered.

**A. Intake comparison**

| Check | How | Blocking when |
|---|---|---|
| The deliverable is the one asked for | intake GOAL.md goal line and restate block against the report's "What shipped" and the code | a different or easier deliverable stands in for the asked one |
| No row disappeared | every key from the STATUS history is present now | any key is missing |
| Every narrowing has its decision | for each lowering in section 5, the same commit touches DECISIONS.md | any narrowing without one |
| Every intake phase ran or was removed by decision | intake plan lines against gate commits | a phase silently absent |
| Nothing unrequested was added | changed paths against plan and package ownership; features in code the goal and restate do not name | unrequested behaviour shipped rather than listed as a follow-up |
| Re-classifications kept their evidence | each entry's evidence path exists | evidence discarded |

**B. Work that only appears finished**

| Check | How | Blocking when |
|---|---|---|
| Proof still holds | re-run the cheapest proof command of each sampled row at HEAD | it fails; the row drops to what still holds |
| Verdicts are valid | each `verdict:` file has `ran` with the full-suite command at exit 0 when the run has a suite, a refutation per claim, confidence 75 or more, no blocking gap | a pass is malformed |
| No scaffold behind a rung | search code behind each sampled row for TODO, FIXME, `not implemented`, `NotImplementedError`, `unimplemented!`, `fatalError(`, placeholder returns, lorem ipsum | a stub sits on the claim's path |
| Tests can fail | copy the tree with `mkdir -p "${TMPDIR:-/tmp}/drive-audit-<slug>" && git archive HEAD \| tar -x -C "${TMPDIR:-/tmp}/drive-audit-<slug>"`, break one production line behind a sampled claim, run its test, expect red, delete the copy | the test stays green |
| Tests were not weakened | `git diff <baseline_sha>..HEAD` for added skips (`.skip`, `xit`, `@Disabled`, `XCTSkip`, `#[ignore]`, `pytest.mark.skip`), removed assertions in test files that still exist, deleted test files, loosened CONSTRAINTS.md values; `drive.py guard` output | any appears without a decision |
| Live means live | each Live Proof `proof.json` has `environment` live or device, a target that is not localhost, 127.0.0.1, or an emulator, and a captured response in `live.md` | any is missing |
| Harness kindness answered | every TESTPLAN.md kindness row has a guard, a live check, or an accepted risk; verdict `harness_kindness` entries are resolved | an open kindness on a Local Proof or higher row |
| UI evidence is independent | `[ui]` rows' `shot:` paths sit under the ui-reviewer's proof round | the maker supplied the screenshots |
| Blockers are real | a "credential absent" claim checked with `test -n "${NAME+x}"` (never printing the value); a "tool missing" claim checked against `.drive/capabilities.json` | the blocker is not real |
| Effects were observed | operate, deploy, and async rows show an independent read-back from this session | only an exit code or a schedule stands behind the row |
| Serving model recorded | Boundary events in STATE.md; verdicts written after a model switch are attributed to that model in the report | a switch is unreported |

**C. Plans described as results**

| Check | How | Blocking when |
|---|---|---|
| Every result has evidence | each line under "What shipped" and each ladder row names a path that exists | any line has none |
| No intentions in the results | search "What shipped" for will, would, should, is designed to, can, once deployed, planned, next | future or conditional tense describes shipped work |
| Rungs match | the report's rung per row equals STATUS.md; the words in section 4 appear only at or above target | a mismatch or a feeling word |
| Everything carried forward | every stop, narrowing, discovery, assumption, capability substitution, paused run, boundary event, and `noticed_not_touched` item from STATE.md, DECISIONS.md, and worker reports appears in the report | any is missing |
| Local versus live is honest | the report's local-versus-live section lists every harness kindness from TESTPLAN.md and the verdicts | one is missing |

**D. Hygiene and retro**

| Check | How | Blocking when |
|---|---|---|
| Nothing the run created is left | in the home repository, `drive.py lint --final` reports no worktree, branch, or uncommitted path absent from `.drive/local/baseline.json`; in every other repository of the run, `git worktree list`, `git branch --list`, and `git status --porcelain` compared with the state recorded under Verified facts at intake. The owner's pre-existing entries are never findings and are never removed | anything the run created remains |
| No secrets in run files | a `grep -rnE` or `rg` pattern search over `.drive/` and REPORT.md that reports locations only; `gitleaks detect --redact --no-banner` only when GOAL.md or CONSTRAINTS.md records it as a command, because the guard allows gitleaks unrecorded only to the security reviewer (`references/verification.md` section 3) | a secret appears |
| Retro is real | `.drive/reviews/<date>-retro.md` exists whether the run ends done or stopped; every investigation closed or explained; every workaround ledger row at count two has an investigation; lessons committed or "none" with a reason | any is missing |
| Evidence has provenance | `drive.py lint --final` reports no verdict, live proof, or citation check without a ledger entry backed by its reviewer's transcript, and none written in a voided review window; a transcript Claude Code deleted after `cleanupPeriodDays` counts as missing, so that review is re-run | any is reported |
| Files agree | `drive.py lint --final` exits 0, which includes one run of the full suite when the run has one | it does not |

**The verdict** uses the verdict schema. The agent that ran the audit writes it to
`.drive/reviews/<date>-final-audit.json`, and you never write, copy, or edit it: drive's hooks record
its hash when that agent stops and its transcript shows a command naming that full path, and `lint --final` refuses an audit file the ledger does not match. `pass` is go, any blocking gap is
no-go, and `claims[]` carries `rung_supported` for each sampled row. On go, move each row that meets its
target to Done with `review:` pointing at that file, finish the report, set `status: done` when every
row is Done or Dropped and `status: stopped` otherwise, commit, run `lint --final`, then `drive.py end`.
On no-go, blocking gaps become work within the remaining budget; the audit runs at most twice
more, each time with a fresh agent, then rows take the rung the last audit supports, the run ends
`stopped`, and the report says so. That stopped run still needs a passing audit before `lint --final`
accepts it: once the rows sit at the rungs their evidence supports, each with its reason, and the
report says so honestly, a fresh audit can say go. The audit is final for the run: a finding you believe wrong goes
into the report with the evidence on both sides, and the row stays where the audit put it.

## 7. Excuses and rebuttals

| The argument for calling it done | Why it fails |
|---|---|
| "The tests pass." | Passing tests are Partial until a verifier ran them, a refutation test exists, and the harness's kindness is answered. |
| "It deployed without errors." | A deploy's exit code is not an observed effect; Live Proof needs a captured response from the live system. |
| "It works in the simulator." | Against a mock backend that is Local Proof for the app and nothing for the system. |
| "The verifier ran out of rounds, and the remaining gap is minor." | The rung is what the last verdict supports; rounds ending is not evidence. |
| "Only a small part is not live; the rest is done." | Status is per row. The live rows stay at their rung, and the report says so. |
| "That claim was too ambitious, so I scoped it down." | Scoping down without a decision in the same commit is silent narrowing, and the audit blocks it. |
| "The cron will pick it up tonight." | Scheduled work is not done; trigger it now through the system's own tools or keep the row below target. |
| "I can't verify that without credentials, so I marked it done." | A blocker caps the rung; it never raises one. Name the credential and the step. |
| "I skipped the flaky test; it's unrelated." | A skipped test is a weakened bar; it needs an investigation or a decision, and the audit greps for skips. |
| "The README describes it, so users can use it." | Documentation of behaviour that no verdict proves supports Scaffold at most. |
| "I already watched the maker's tests go green." | You are not independent of the work you orchestrated; only a verifier's verdict moves a row. |
| "It's a report; checking citations is overkill." | Unchecked citations are how invented facts reach the owner; the grader's check is the report's test. |
| "The final audit is expensive, and everything is green." | The audit is the only independent check on your summary of the run, and a mirage passes every gate you already ran. |
| "The run could not finish, so there is nothing to audit or retro." | A stopped run still ends through the audit, the retro, and `lint --final`; it is the likeliest run to hold a lesson. |

## 8. Red flags

Stop and re-check the evidence when you see any of these:

- A status sentence with "done", "working", or "complete" and no evidence path beside it.
- A row above Partial whose only verdict rests on reading code, or whose `verdict:` has an empty
  `ran`.
- Live Proof where `proof.json` names localhost, an emulator, or a mock, or where `shim_differences`
  is absent.
- A STATUS key that existed last week and is gone, or a claim reworded since intake.
- `live` flipped from y to n, or a phase missing from the plan, in a commit that does not touch
  DECISIONS.md.
- Added skip markers, removed assertions, or a loosened CONSTRAINTS.md value in the run's diff.
- A report sentence in future or conditional tense under "What shipped".
- Screenshots in a `[ui]` row that the maker produced.
- A soak or scheduled check still open while STATE.md says `status: done`.
- A fix whose reproducer was never seen failing on the pre-fix commit.
- A `why:device-only:` row at Done, or a preview deployment cited as Live Proof.
- An operate step whose only evidence is the command's output.
- "Unverifiable" or "blocked" with no check that the blocker is real.
- The final audit skipped, run by the grader, or its verdict summarized by you instead of saved
  unedited at `.drive/reviews/<date>-final-audit.json`.
- A Done row whose `review:` points at a security review or any file but the final audit.
- `status: stopped` with a row below Done that carries no reason, or a report that does not open with
  "Stopped because".
- A worktree, branch, or uncommitted path the run created still present at the end.
- A verdict or final audit whose hash the provenance ledger does not hold.
