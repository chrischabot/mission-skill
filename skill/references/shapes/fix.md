# Shape: fix

Read this at intake when the goal names a defect, a failure, wrong output, flakiness, a live
incident, or a measured quality that is too slow or too large, and again at the start of every
phase. It decides phase order and variants, who does each phase, what `.drive/HUNT.md` holds, what to
check before any hypothesis, how a hard bug is classified, amplified, isolated, and confirmed, what a
fix may contain and what it must also sweep, how it is verified, and what Done means. It is also the
sub-loop when a verification failure elsewhere is not explained by the change under test.

## When it applies

| Variant | Applies when | Changes |
|---|---|---|
| `fix` | behaviour differs from what existed or was specified | nothing; the runbook below |
| `fix/incident` | a live system is failing now | an `execute` phase before archaeology mitigates, with its undo recorded first; target rung Operational |
| `fix/perf` | the symptom is a number (latency, memory, size, query count) | reproduce is a baseline measurement; attempts follow keep or revert |

If the expected behaviour never existed, the goal is a `feature`; re-classify first. Three invariants
hold at S and above: no edit to non-test source before a reproduction that runs and fails; no
completion without a verifier that saw the failure at the pre-fix commit itself; no completion without
a one-sentence cause explaining symptom, frequency, environment, and since-when, with the harness
taught the constraint that let the bug through. At XS the first holds and the other two shrink to a
test seen red then green and a cause line in the commit body (Size and traits, below).

When the goal names no observable symptom ("find this bug and fix it"), find the candidate before
filling the brief. Search, in order: Open failures in `.drive/STATE.md` and `.drive/runs/*/STATE.md`;
failing CI runs (`gh run list --status failure --limit 20`); open bug issues (`gh issue list --label bug`);
errors in the system's own logs, read through its tools; and the project's auto memory notes. Take
the failure with the most evidence as an assumption in GOAL.md's restate block, record how it was
found on HUNT.md's Source line, and add each other candidate to STATE.md's Open failures with its
evidence. When the search finds nothing, write REPORT.md naming every place searched and stop with
`status: stopped`.

## Phases

| Phase | Entry | Work and agent | Artifact | Exit check (checker) |
|---|---|---|---|---|
| intake | the goal | classify; fill the brief fields the goal and probe answer; record the pre-fix sha (orchestrator) | GOAL.md, HUNT.md Brief | every brief field in `templates/HUNT.md` filled or marked unknown (orchestrator) |
| execute | `fix/incident` only; failure confirmed through the system's read verbs | reversible mitigation through the system's own tools, undo appended to DECISIONS.md first (orchestrator) | DECISIONS.md, HUNT.md Mitigation | effect observed through read verbs, not the command's exit (drive:verifier) |
| archaeology | brief written | rule out causes outside the code (the plug checks below), then the lookups below (drive:researcher lanes) | HUNT.md Since, Prior, Harness, plug lines; `how-it-works.md` narrowed to the failing path at M and above | every plug check recorded, baseline suite result, running build identity, one kindness line per test double (orchestrator) |
| reproduce | archaeology exit | repro script and measured rate (drive:investigator); framework test from brief and code alone (drive:severe-tester at M and above, frozen once red; drive:implementer at S) | HUNT.md Reproduction; `.drive/proofs/<key>/r1/repro.sh`; the test | the repro command exits non-zero now for the brief's reason, output saved (orchestrator runs it) |
| diagnose | reproduce exit | bug class, hypothesis ledger, isolation, experiments in throwaway worktrees (drive:investigator); two-way confirmation (a fresh drive:verifier) | HUNT.md Hypothesis ledger; `confirm-<hypothesis>.json`; `.drive/local/logs/` | one row confirmed by the separate confirmer and explaining all four brief fields (drive:verifier) |
| fix | a confirmed row | smallest change that removes the cause, the sibling sweep, the masked-workaround check, and the class fix (drive:implementer) | diff; HUNT.md Fix; STATUS row | gates green; `git diff \| grep -c HUNT-` is 0; `drive.py guard --base <baseline_sha>` and `drive.py freeze check` exit 0 (orchestrator) |
| verify | fix gate green | the verifier procedure; `/code-review <level> <baseline_sha>...HEAD` in parallel, level from `references/verification.md` section 5 (drive:verifier; drive:security-reviewer in its code-review mode) | `.drive/proofs/<key>/r<n>/verdict.json` | pass verdict; for an intermittent bug the n-run proof; for a live bug the live reproduction passes (drive:verifier) |
| harden | verify pass | severe tests on adjacent inputs (drive:severe-tester: one at S, one per adjacent input the verifier named at M and above); security review when `auth` (drive:security-reviewer); no `/simplify` on a fix | `severe:` tests; `.drive/reviews/` | every finding refuted or dispositioned; severe tests green (drive:verifier) |
| retro | harden exit, or the hunt stopped | post-mortem, facts to STATE.md, lessons (orchestrator; drive:auditor verifies a candidate lesson) | HUNT.md Post-mortem, LESSONS.md | investigations closed; lesson committed or "none" with a reason (orchestrator) |
| report | retro exit | final audit by drive:auditor for every `fix/incident` and any fix at L or above, otherwise a fresh drive:verifier running the same checklist; then REPORT.md from the files | `.drive/reviews/<date>-final-audit.json`; `.drive/REPORT.md` | `drive.py lint --final` passes with `status: done` or `status: stopped` (orchestrator) |

## HUNT.md

Copy `templates/HUNT.md` to `.drive/HUNT.md` at intake. Its sections are appended in this order and
never rewritten: Brief (symptom, evidence, frequency, environment, running build, since, impact,
trigger, prior, harness, repro command, and the source of a symptom the goal did not name), Mitigation
(`fix/incident` only, written in the execute phase), Claims, Reproduction (with the plug lines and the
measured rate), Hypothesis ledger, Attempt ledger (`fix/perf` only), Fix, Verification,
Re-classification, and Post-mortem (written at retro). Prior lists the STATE.md, LESSONS.md, and
`references/lessons/general.md` entries consulted. The file is the handoff if the hunt stalls and the
only input a second opinion or a confirmer receives.

## Archaeology: rule out causes outside the code first

A large share of hard bugs are not in the code at all: the wrong build is running, a test is not
executing, or an exit code is swallowed. Check these six things, the plug checks, before writing any
hypothesis, and record each
under Reproduction as `plug: <item> · <command> · exit <code> · <salient line>`:

1. The code under test is the commit or deployment you believe: read the running build's identity with
   its own command (build stamp, version endpoint, deploy id, installed app's Info.plist).
2. The build is fresh: no stale artifact, cache, simulator install, or old worker bundle.
3. Environment variables, secrets, and bindings are present, checked for presence and never printed.
4. The failing test actually runs: not skipped, no focus marker elsewhere, the filter matches, and the
   executed test count is what you expect.
5. The directory, branch, and target environment are the intended ones.
6. No exit code is masked by a pipe (`set -o pipefail`, or read `${PIPESTATUS[0]}`).

A failed plug check is the finding. Fix it and re-run the reproduction; if the failure disappears, the
hunt closes there, and the post-mortem names the plug that was loose and the check that now guards it.

Then look fields up; never ask. Read STATE.md, LESSONS.md, CLAUDE.md, and the selected domains' Learned
constraints: a match is a high-prior hypothesis, never a conclusion, and a recorded earlier fix for
this symptom or area makes that fix's cause suspect. Load the system's own observability tools now
(its MCP verbs via ToolSearch, its log tail, `gh run view`). Run `git log --since=<last good> -- <area>`,
`git log -S'<symbol>'`, and `gh issue list --search`. Run the area's tests on HEAD; for every fake,
shim, in-memory store, or mocked clock, write where it is kinder than the real thing.

## Reproduce

Do not edit non-test source until the Repro line names a command that exits non-zero now, for the
brief's reason, and prints a one-line signature of that reason. Turn it into a framework test named for
the claim it refutes, written at M and above by `drive:severe-tester`, which has seen no proposed fix,
and frozen once it is red (`references/testing.md` section 9). When no framework test is possible, a
scripted probe with saved output is the reproduction and the row caps at Local Proof until a live check
exists.

- **Deterministic.** Test at the lowest layer that shows it; keep a wide test too when the symptom
  is visible only end to end. Assert on what leaves the system, not on an inner layer.
- **Intermittent.** Amplify first, cheapest first, from the class table below, then measure the rate
  until at least five failures are observed, with state reset between runs; fewer failures make the
  rate a guess. Record runs, failures, and the amplifier in the Reproduction table. Below about one
  failure in ten, diagnose by differential logging across many runs.
- **Production only.** Diff environments before code: configuration (variables, secrets present,
  flags, bindings, exact deploy target), data shape (sizes, nulls, unicode, cardinality past a
  limit), runtime (real engine against local substitute), artifact staleness, and the harness. Teach
  the local harness the constraint, or reproduce live and read-only with a captured input.
- **Visual.** Capture a screenshot and the accessibility tree; assert on the tree.
- **Budget.** Three strategies without a failing command: switch to live capture; if that fails,
  stop and report what was tried and what would make it reproducible. Without a reproducer, no row
  rises above Partial.

```bash
runs=0; fails=0; while [ "$fails" -lt 5 ] && [ "$runs" -lt <cap> ]; do runs=$((runs+1)); <reset command>
  if ! <repro command> </dev/null >.drive/local/logs/run.log 2>&1; then fails=$((fails+1)); cp .drive/local/logs/run.log ".drive/local/logs/fail-$fails.log"; fi
done; echo "runs=$runs fails=$fails"
```

## Diagnose

**Classify first.** Match the signals against this table and load that row's tactics; with two
plausible classes, record both and treat the second as a family of hypotheses.

| Class | Signals | Amplify and isolate | Symptom patch to refuse |
|---|---|---|---|
| Race or timing | fails some of the time; order-dependent; worse under load or in CI | loop runs; shuffle order; raise parallelism; throttle CPU; inject delay at the suspected interleaving; the runtime's race detector; serialize one resource at a time | sleeps, longer timeouts, blanket retries |
| Vanishes when observed | goes away with a debugger, logging, or an unoptimized build | ring-buffer logging dumped only on failure; identical build flags; differential on build configuration | calling it fixed because instrumentation shifted timing |
| Resource leak | monotonic growth; out of memory after hours; throughput decays | a soak script that compresses time; heap snapshots at three points, diffed by retained type; bisect with a soak threshold | periodic restarts, a bigger instance |
| Environment or configuration drift | one environment fails; works locally | capture both environments' fingerprints (versions, flags, bindings, secrets present, compatibility date) and apply half the differences at a time | hand-editing production configuration |
| Dependency upgrade | broke after a lockfile change | read the changelog first; old and new pinned side by side; bisect versions or lockfile commits | pinning forever with no Open failure |
| Data-dependent | only some records, tenants, or inputs | capture the failing input with personal data removed; shrink it until removing any one element makes the failure vanish; a property test around the minimal case | special-casing the one bad record |
| Distributed or async | duplicates, lost or reordered effects | replay recorded sequences; force redelivery; kill between accept and record; correlation ids end to end | deduplicating in the display only |
| Performance regression | a metric crossed a threshold after a change | benchmark with warm-up, ten or more runs, and spread reported; `git bisect run` with a threshold script; profiler diff | a cache that hides the hot path |
| Simulator, emulator, or local runtime against device or deployed runtime | fails only on device or only deployed | the platform's list of differences; device logs; the same build configuration on both; a canary on the deployed runtime | declaring it fixed from the simulator or local runtime |

**Isolate before theorising.** Run the mechanical isolators that apply and record which ran: bisect
from a known-good commit (re-verify the first bad commit by running the repro on it and on its parent);
shrink a large failing input to a minimal one; diff a working environment against the failing one.
Instrument each component boundary once, recording what enters and what leaves, then re-run the
unchanged repro: it must still fail at about the measured rate, or the instrumentation is itself a
variable and must be replaced by logging dumped only on failure.

**Keep the ledger.** Start with three to five candidates across layers (data, logic, timing,
configuration, platform, stale artifact). Write each prediction and what you expect if it is false
before running its experiment, run the cheapest experiment that separates the likeliest, and change one
variable at a time; a bundled change is no experiment. Refuted rows stay with their evidence and are
listed as "do not re-test" in every later brief. Several partial rows may be joint contributors rather
than rivals: test the combination. Probe or read a platform instead of guessing about it. Experiments
that change code run in a detached worktree under `/tmp`, with `HUNT-<slug>` instrumentation.

**Confirm two ways, by someone else.** A row is confirmed only when a fresh `drive:verifier` in
confirmation mode, given HUNT.md, the repro, the candidate patch, and the evidence files and nothing
from the investigator's session, shows all three in its own `git archive` copy: with the cause present
the failure occurs at about the measured rate; with the cause removed alone it passes, for an
intermittent failure with n clean runs by `references/testing.md` section 10; and with the cause
re-introduced the failure returns. It first tries one experiment that would separate a cheaper
explanation, and writes `.drive/proofs/<key>/r<n>/confirm-<hypothesis>.json` with `confirmed`,
`refuted` (the step and evidence), or `unsettled` (what is missing). The row must also explain why the
bug started when it did and why it happens here and not elsewhere. At S with a deterministic repro, the
verifier's pre-fix red and HEAD green on the minimal change is the two-way check.

Bisect when there is a last-good reference and a deterministic or amplified repro; the investigator
creates, uses, and removes the worktree in one step (exit 125 skips an unbuildable commit):

```bash
git worktree add --detach /tmp/drive-<repo>-bisect-<slug> <bad-sha>
( cd /tmp/drive-<repo>-bisect-<slug> && git bisect start <bad-sha> <good-sha> \
  && git bisect run sh -c '<build command> || exit 125; <absolute path>/repro.sh'; \
  git bisect log > <absolute root>/.drive/local/logs/bisect-<slug>.log; git bisect reset )
git worktree remove --force /tmp/drive-<repo>-bisect-<slug> && git worktree prune && git worktree list
```

The first bad commit is a hypothesis, not the cause. **Escalate** by attempts: after three refuted
rows with no open candidate, or three failed fix attempts on one failure, stop and have a fresh
`drive:investigator` give a second opinion from the brief, ledger, and repro only (its own ranked
differential and the most discriminating experiment); if that fails, run parallel arms when two or more
substantial independent hypotheses remain, else re-classify. Exploit strings stay in the investigator;
on a cyber-classifier decline, cap the claim, log it, and surface it once (`references/safety.md` section 6).

## Fix rules, the sweep, and the class fix

Remove the confirmed cause with the smallest change that does so; every diff line must be explained
by the confirmed row. A retry, sleep, widened timeout, swallowed error, null check, default, disabled
feature, skipped test, special-cased input, or loosened assertion is a symptom patch unless a ledger row
proves the cause is external and this is its correct handling. When the proper fix is large, ship the
smallest correct fix, record its limit as a verified fact, and re-classify the rest. Do no surrounding
cleanup; a refactor becomes a follow-up in REPORT.md.

**Sibling sweep.** Express the mechanism, not the line, as a search (`rg`, `ast-grep`, a lint query)
and list every hit in HUNT.md's Fix section with a disposition: fixed (commit and test), unaffected
(the evidence), or left (an Open failure with the reason). At M and above the verifier re-checks at
least three unaffected hits without seeing your reasons; a disagreement sends the whole sweep back.
Also list the ways the mechanism could be reached around the fix (another entry point, another caller,
a retry path) and test each.

**Masked-workaround check.** List earlier workarounds for this symptom: comments, commit messages,
retries, flags, and timeouts near the mechanism, and rows in STATE.md's workaround ledger. At L remove
each one the fix makes obsolete and re-run the broader suite; at S and M remove it the same way or keep
it with a reason in HUNT.md. Never remove a workaround "because the root cause is fixed" without that
re-run, and never keep one silently.

**Class fix.** Teach the test double the production constraint; enforce it in the code under test; add
a test that generates the violating shape. Repair existing bad data as a separate step with a backup
and an undo. Test and fix land in one commit so main is never red; at M and above that commit carries
the frozen reproducer with `.drive/frozen.txt` and `.drive/frozen.sha256`. The maker writes at most one
boundary test; the reproducer, the class-fix shape test, and the severe tester's tests are counted
separately.

## Verify

Build the handoff from HUNT.md with `templates/handoff.md`: brief, ledger, diff range, test name,
repro command, and the pre-fix sha, never a tree path and never the transcript. The verifier exports
the pre-fix tree itself with
`mkdir -p /tmp/drive-prefix-<key> && git archive <pre-fix sha> | tar -x -C /tmp/drive-prefix-<key>`,
copies the regression test in, installs dependencies there with the probe's command when the test
needs them, and removes the copy before it returns. Saving each output in the round directory, it:
(1) runs the test and repro in the copy and confirms the failure the brief describes; (2) runs the
test, the full gates, and `drive.py freeze check` on HEAD; (3) for an intermittent bug, runs the n-run
proof from the recorded rate; (4) states whether the cause explains symptom, frequency, environment,
and since-when; (5) tries at least two adjacent inputs the fix was not written for; (6) checks the
sibling sweep, the masked-workaround check, and the harness constraint; (7) lists symptom-patch
shapes, weakened assertions, and changes the cause does not explain. A failing verdict becomes the next
ledger row, answered by an experiment. Bound and convergence: `references/verification.md` section 6.
For a bug seen live, deploy through the system's own tools, confirm the deployed identity is your
build, reproduce the original condition live, and record the request id; if it cannot be forced now,
the rung is Local Proof and Open failures names the pending check.

## Variants

**`fix/incident`.** Mitigate first in the execute phase with the undo recorded; read topology and
recent deploys before docs; watch with `Monitor`, never a schedule. Mitigation may close the incident,
never the hunt. Remove the mitigation only after the real fix is live-proven. Operational needs an
alert or smoke check for a recurrence, fired once (`references/observability.md`). Every incident gets
the final audit from `drive:auditor`.

**`fix/perf`.** Write the budget (p95 latency, memory, query count) as a CONSTRAINTS.md row, baseline
with a script on a named path, profile, and give each ledger row a predicted gain. A change stays a
hypothesis until re-measured exactly as the baseline, one change at a time, against run-to-run
variance. Keep it only if it clears the threshold with every test green; revert it when within noise,
worse, or bought with an edited test. Log every attempt; prefer counts to timings; keep the benchmark.

## Size and traits

| Size | What runs |
|---|---|
| XS | cause known, one non-test source file: inline, no `.drive/`; the plug checks that apply; failing test seen red then green; project gates; commit body holds claim, repro, cause, evidence; trait gates still run, and a severe tester or security reviewer at XS writes nothing under `.drive/` |
| S | GOAL, STATE, STATUS (one row), HUNT.md; one investigator; full verifier procedure, whose pre-fix red and HEAD green is the two-way check for a deterministic bug; one severe test on an adjacent input by `drive:severe-tester`; the final-audit checklist by a fresh `drive:verifier` (by `drive:auditor` for `fix/incident`) |
| M | adds narrowed `how-it-works.md`, CONSTRAINTS.md, the severe tester's frozen reproducer, two-way confirmation by a separate verifier, the verifier's blind check of the sibling sweep, a severe test for each adjacent input the verifier named |
| L | adds a research lane for third-party behaviour, hypothesis arms, removal of obsolete workarounds with a broader re-run, and the final audit by `drive:auditor`; XL is an open problem, so re-classify |

Traits: `auth` adds security review and severe tests even at XS, attack material only inside Opus
subagents; `concurrency` adds interleaving loops, α 0.01 for the n-run proof, and severe ordering tests;
`async-scheduled` means triggering the job now to reproduce and to prove, plus a replay and idempotency
test; `external-systems` and `data` mean read-only probes, captured fixtures, and a backup before
repairing rows; `ui` and `native-platform` mean screenshot plus tree reproduction, with
`drive:ui-reviewer` judging before and after.

## Verification centre, Done, parallelism

The centre of gravity is the reproducer, seen by the verifier failing at the pre-fix commit and
passing after. Done: the STATUS row carries `test:`, `severe:`, `verdict:`, `review:` pointing at
`.drive/reviews/<date>-final-audit.json`, and `live:` when the bug was live; the post-mortem is
complete; the regression test stays; no `HUNT-` marker remains; `git worktree list` shows no worktree
the run created; `fix/incident` is Operational with the mitigation removed; `fix/perf` has both numbers
from one script and a kept benchmark. A symptom that stopped without a confirmed cause is Partial. At
retro, facts go to STATE.md with how they were verified and general rules through
`references/lessons.md`. A stalled hunt writes its best hypothesis, rate, and repro path into Open
failures, still runs the retro, and ends with `status: stopped` and a report that opens "Stopped
because".

Never run parallel writers. Read-only lanes (log sweep, environment diff, sibling search) may run
together. Hypothesis arms run only when two to four open hypotheses each need a substantial,
independent experiment: one detached worktree per arm (`references/parallel.md` section 11), one
investigator per arm with one hypothesis, its prediction, the brief, the refuted rows, and the repro;
every arm's worktree is removed whether or not it confirmed, an arm's `confirmed` is only a candidate
until the separate confirmer runs, and only the fix phase applies code on main.

**Re-classify** when the cause is a design flaw many callers rely on (ship the small correct fix, then
`move/refactor` or a `feature` sub-goal fed by the ledger); when the expectation was wrong or undefined
(write the corrected claim and what must stay unchanged before any fix, or report with evidence and
stop); when the fix needs an interface change or a second module (size up, characterize callers); when
the cause is a known one-liner (size down); and before a workaround's second use.

## Excuses and rebuttals

| Excuse | Rebuttal |
|---|---|
| "The cause is obvious; reproducing wastes time." | A cause that cannot be made to fail on demand is a guess, and the reproducer is the regression test you need anyway. |
| "The build is surely current; skip the plug checks." | A stale build or a test that never ran explains a large share of hard bugs, and the checks take a minute. |
| "It is flaky; a retry is correct." | A retry is a symptom patch unless a ledger row proves the cause is external. |
| "It passed twenty times after the fix." | Against a one-in-fifty failure, twenty runs prove little. Run n from the measured rate. |
| "I reverted my fix and the failure came back, so it is confirmed." | The agent that proposed a cause is the worst judge of it. A separate confirmer runs the two-way check. |
| "The verifier can rerun my test on HEAD." | A regression test that never failed on the broken code is not evidence. |
| "Teaching the fake the limit is scope creep." | The kinder double is why the bug shipped; without the class fix it returns under another name. |
| "The same mistake is surely not elsewhere." | Search for the mechanism, list every hit, and let the verifier check your unaffected calls. |
| "The old retry can stay; it does no harm." | A workaround left in place hides whether the fix worked and masks the next occurrence. Remove it with a re-run, or record why it stays. |
| "This matches the lesson from last time." | A signal that matches a known failure may have a different cause; run the experiment. |

## Red flags

- Non-test source changed before the Repro command was seen failing; a ledger row whose prediction is missing or came after the result.
- No plug lines under Reproduction, or a hypothesis written before them.
- An intermittent bug with fewer than five observed failures behind its rate, or a fix proven with fewer clean runs than n.
- A row marked confirmed with no `confirm-<hypothesis>.json` from a separate agent, or a refuted row re-tested without new evidence.
- The diff adds a retry, sleep, timeout, catch-all, null check, default, skip, or loosened assertion.
- A fix with no sibling sweep, or a workaround near the mechanism left without a reason.
- A frozen reproducer changed after it was frozen.
- A `HUNT-` marker in the main checkout, a worktree the run created still in `git worktree list`, or a second workaround row for one obstacle.
- "Probably", "should be", or "flaky" in the root cause; a live check run against a build other than the one serving the symptom.
- A handoff that names a pre-fix tree path instead of the pre-fix sha.
