# HUNT · <slug>
variant: <fix | fix/incident | fix/perf> · size: <S|M|L> · pre-fix commit: <sha at intake> · opened: <YYYY-MM-DD>

<!-- The working file for a fix. Sections are appended in this order and never rewritten; the file is
the handoff if the hunt stalls, the input to a second opinion, and the source of the verifier's
handoff. Rules: references/spec.md and the fix shape file. Delete guidance comments as you fill each
section. Hypotheses and attempts are named in short words, never numbered. -->

## Brief
<!-- At most fifteen lines. Look missing fields up through the system's own tools; never ask. Write
"unknown" when a field cannot be recovered. -->
Symptom:      <observed, quoted or captured> (expected: <expected>)
Evidence:     <log line, request id, stack trace path, screenshot path>
Frequency:    <always | <n> failures in <m> runs | once on <YYYY-MM-DD>>
Environment:  <production | staging | ci | local>; <runtime, device, OS, browser, version>
Running build: <deployed version id, binary build date, container tag> · checked with `<command>`
Since:        first seen <date or commit>; last good <date or commit>; changed around then: <deploys, dependencies, configuration>
Impact:       <who is affected and how badly>; workaround in use: <none | what>
Trigger:      <steps, input, or conditions | unknown>
Prior:        <STATE.md, LESSONS.md, and lessons consulted, each a hypothesis | none>
Harness:      <each test double on the path> is kinder than production in <how>
Repro cmd:    <filled by Reproduction: a command that fails now for the reason above>
Source:       <named in the goal | no-symptom search: places searched, why this one>

## Mitigation
<!-- fix/incident only, written in the execute phase before archaeology. Write the undo in
DECISIONS.md before applying. Delete for other variants. -->
Applied:      <YYYY-MM-DDTHH:MMZ> · <action through the system's own tools>
Undo:         `<exact command>`
Verified by:  <check showing the bleeding stopped, with output path>
Removed:      <after the real fix is live-proven: date and evidence | still in place>

## Claims
<!-- One to three STATUS rows. The claim is the corrected behaviour stated so it could be false. The
key is the slug of the heading. -->

### <The corrected behaviour as a claim in three to eight words>
live: <y when the bug was observed in a live system | n>

What would prove this wrong

**<Refuting scenario title>**
Given <the brief's triggering state>. When <trigger>. Then <the correct outcome the buggy code does not produce>.

## Threat model
<!-- When `auth` or the security surface list applies and the run has no DESIGN.md; delete otherwise.
Format and rules: references/security.md section 2. -->

## Operations
<!-- fix/incident with an Operational target and no DESIGN.md; delete otherwise. The on-call questions
table from references/observability.md section 2. -->

## Reproduction
<!-- Plug checks: rule out causes outside the code before any hypothesis (references/shapes/fix.md). One line each. -->
plug: running build is the commit or deployment believed · `<command>` · exit <code> · <salient line>
plug: build is fresh (no stale artifact, cache, install, or bundle) · `<command>` · exit <code> · <salient line>
plug: environment variables, secrets, bindings present (never printed) · `<command>` · exit <code> · <salient line>
plug: the failing test actually runs (not skipped, filter matches, expected count) · `<command>` · exit <code> · <salient line>
plug: directory, branch, and target environment are the intended ones · `<command>` · exit <code> · <salient line>
plug: no exit code masked by a pipe · `<command>` · exit <code> · <salient line>

<!-- No edit to non-test source until Repro cmd exits non-zero now for the brief's reason. For a
complex bug, a subagent that has not seen any proposed fix writes the failing test from this brief
and the code alone. -->
Command:      `<repro command>` · exit <code> · output: `.drive/local/logs/<file>`
Layer:        <unit | integration in the real runtime | end to end>; wide test kept: <test:<path>::<name> | not needed>
Failing test: test:<path>::<name, matching the claim words> · written by <agent>
Probe only:   <when no test is possible: probe path and output, rung capped at Local Proof>

Intermittent (delete if deterministic):
| run set | runs | failures | amplifier applied |
|---|---|---|---|
| baseline | <n> | <n> | none |
| <amplifier name> | <n> | <n> | <seed pinned, load, injected delay, deterministic scheduler, shuffled order> |

One environment only (delete otherwise):
| axis | where it fails | where it passes | evidence |
|---|---|---|---|
| configuration | | | |
| data shape | | | |
| runtime | | | |
| artifact staleness | | | |
| harness | | | |

Performance baseline (fix/perf; delete otherwise):
Metric and budget: <metric, path, target with unit>
Command:      `<benchmark or profile command>` · conditions: <machine, data size, warm-up, repetitions>
Baseline:     median <value> · spread <min to max or standard deviation> over <n> runs · commit <sha>

## Hypothesis ledger
<!-- Write the prediction before running the experiment. One variable per experiment. Confirmed means
the prediction was observed and the hypothesis explains symptom, frequency, environment, and since-when;
otherwise partial. Status: open, confirmed, partial, refuted, suspect (a confirmed cause whose fix
needed the same workaround twice). Start with three to five candidates across layers: data, logic,
timing, configuration, platform, stale artifact. -->

| hypothesis | layer | prediction (if true, doing X shows Y) | experiment | result | status |
|---|---|---|---|---|---|
| <short name> | <layer> | <prediction> | `<command or path>` | <observed, with output path> | open |

Bisect (delete if not run):
Range:        good <sha> · bad <sha> · run by drive:investigator in a detached worktree under ${TMPDIR:-/tmp}, removed
Culprit:      <sha> <subject> · log `.drive/local/logs/bisect-<slug>.log` · added to the ledger as a hypothesis

Second opinion (after three refuted rows with no open candidate; delete if not run):
Agent:        drive:investigator, fresh context, given this brief, the ledger, and the repro command only
Report:       `.drive/investigations/<YYYY-MM-DD>-<slug>.md` · most discriminating experiment: <what> · outcome: <what>

## Attempt ledger
<!-- fix/perf only; delete otherwise. Re-measure exactly as the baseline: same command, conditions, and
repetitions, one change at a time. Keep only a result that clears run-to-run spread with every test
green. Within noise, worse, or bought with a failing or edited test means revert; neutral is a revert.
Record reverted attempts too. -->

| attempt | change | median | spread | delta against baseline | clears noise | tests | decision | commit or revert |
|---|---|---|---|---|---|---|---|---|
| <short name> | <one change> | <value> | <spread> | <delta with unit> | <yes or no> | <pass or fail> | <keep or revert>: <reason> | <sha or reverted> |

## Fix
Cause:        <one sentence that explains symptom, frequency, environment, and since-when>
Instance:     <what changed, in words> · commit <sha, test and fix together>
Siblings:     `<search command>` · <n> found · <fixed in the same commit | each cleared with evidence>
Harness:      <constraint now enforced in the double, and the test feeding it the bad shape> | not applicable: <reason>
Enforced in code: <where the code under test now enforces the production constraint> | not applicable
Instrumentation: `git diff <pre-fix commit> | grep -c "HUNT-<slug>"` returned 0
Symptom-patch shapes: <none | each retry, sleep, wider timeout, default, or skip, with its row> (allowed only with the hypothesis-ledger row that proves the cause is external)

## Verification
Pre-fix failure: reproduced by the verifier in its own `git archive` copy of <pre-fix commit> under `${TMPDIR:-/tmp}/drive-prefix-<key>`, removed afterwards · evidence `.drive/proofs/<key>/r<n>/commands.log`
Verdict:      `.drive/proofs/<key>/r<n>/verdict.json` · <pass | fail> · round <n> of 2
Severe tests: severe:<path>::<name> by drive:severe-tester (at least one at every size) · adjacent inputs tried: <what>
Final audit:  `.drive/reviews/<YYYY-MM-DD>-final-audit.json` · by <drive:auditor | a fresh drive:verifier> · <go | no-go>
Live proof:   deployed identity <version id> confirmed with `<command>`; original condition replayed live, <request id or log line> | Local Proof only, pending live check: <what and why it cannot be forced now>
Rung:         <Partial | Local Proof | Live Proof>

## Re-classification
<!-- Delete if none. A design flaw ships the smallest correct fix and hands the rest to a feature or move
sub-goal with this file as input. A wrong expectation is reported with evidence and the hunt stops. -->
Outcome:      <design flaw → sub-goal <shape> | wrong expectation → stopped> · recorded in GOAL.md re-plans <YYYY-MM-DD>

## Post-mortem
<!-- At most twelve lines. -->
Symptom:        <one line>
Root cause:     <one sentence>
Why not caught: <the harness gap, missing constraint, or missing check>
Fix:            instance <sha>; class <double taught, check added, siblings handled>
Evidence:       pre-fix failure <path>; post-fix pass <path>; gates green; verdict <path>; live <request id | pending: reason>
Facts to STATE: <n, or none>
Lesson:         <general rule, routed by the lesson loop | none, because <reason>>
Rung:           <Local Proof | Live Proof | Operational>
