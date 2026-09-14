# Bugfix spec · BUG-<n> · <title>

<!-- Template: skills/mission/templates/BUGFIX-SPEC.md → .mission/SPEC.md for M bug missions (S bugs use the bug variant
     of TASK-CARD.md). <n> is the issue number or the investigation number (investigations/O-NNN.md → BUG-<NNN>).
     Clause IDs BUG-<n>-C1 / E1 / U1 go into requirements.yaml (kind: bugfix). Investigation depth is not spec depth:
     keep this to one page even when the hunt is long. -->

Class: <S|M> · Investigation: investigations/O-<NNN>.md · Status: repro-pending | reproduced | fixed | verified

## Repro

- Environment: <OS, runtime, app version, config flags, data set>
- Steps: 1. <…> 2. <…> 3. <…>
- Observed: <exact output, error text, screenshot path>
- Expected: <what should happen>
- Frequency: <always | k failures in n runs (flaky; see references/debugging.md for n)>
- Evidence: <logs/<file> line, screenshot path with pixel box>
- Repro artefact: <test path::name or script path> — fails before the fix: <command → exit code + line>

<!-- No reliable repro yet? The first deliverable is the repro (or a statistical repro with a frequency). Skip spec
     review until it exists. -->

## Current behaviour (defect)

- **BUG-<n>-C1.** When <condition>, the <system> <incorrect behaviour>.

## Expected behaviour

- **BUG-<n>-E1.** When <condition>, the <system> SHALL <correct behaviour>. · Oracle: `<test path::name>` (fails before
  the fix, passes after) · Kind: <unit | integration | e2e>

## Unchanged behaviour (regression fence)

- **BUG-<n>-U1.** When <adjacent condition>, the <system> SHALL CONTINUE TO <existing behaviour>. · Oracle: `<existing
  test path::name>`
- **BUG-<n>-U2.** <…>

<!-- Pick adjacent conditions a narrow fix could break: other input classes, other roles, the empty case, the retry
     path. The fix MUST NOT delete, skip or weaken any Unchanged oracle. -->

## Root cause (verified, not guessed)

<file:line · mechanism · evidence (command + output line) · hypothesis ledger: investigations/O-<NNN>.md>

## Contract impact

<none | changes public contract → reclassify to L; write a delta SPEC section + ADR-NNN>

## Proof of fix

- `<command>` exits 0 with <line>; red-before-green evidence: <commit or log path>
- Flaky defects: n ≥ ln(α)/ln(1−p) consecutive clean runs with state reset (α 0.05; 0.01 for money/auth/data/concurrency;
  doubled when state cannot be fully reset): <n, tally, log path>

## Generalisation (hand-off to LESSONS-INBOX.md)

<class of bug · rule to consult next time · or "none">
