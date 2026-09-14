# TESTPLAN · <project> · <goal slug>
written: <ISO UTC> by drive:architect · commit <short sha> · constraints: .drive/CONSTRAINTS.md | none (size S)

<!-- Rules: references/testing.md. Written after the spec and before decomposition, every status
Missing. Implementers write the tests named here and nothing more. Only the orchestrator edits the
status and evidence columns, copied from validated verdicts when STATUS.md is updated; STATUS.md and the
code win on any disagreement. Status uses the ladder words only. Keys are STATUS keys (slugs of claim
words), never numbers. Delete guidance comments as sections fill; delete a section only when it cannot
apply, and say why in "Deliberately not tested". -->

## How to run
<!-- Exact commands with flags, copied from GOAL.md's probe or discovered from the repository's own
scripts and CI. Never assume a default such as `npm test`. -->

| lane | command | what it runs | budget | required before |
|---|---|---|---|---|
| single test | `<command with a filter for one named test>` | one test, for makers' inner loop | seconds | nothing |
| fast | `<command>` | unit and binding tests in the real local runtime | under 2 min | every package report |
| integration | `<command>` | production build, limits probe, contract and remote-binding tests, corpus replay | <minutes> | Local Proof |
| end to end | `<command>` | one run per user-visible flow | <minutes> | Local Proof for wiring and `[ui]` claims |
| live | `<command>` | deployed smoke, remote reads, live checks crossing limits | <minutes> | Live Proof |
| quarantine | `<command>` | quarantined tests only; never blocks | <minutes> | nothing |

Toolchain at planning: <runtime, runner, and platform CLI versions from lockfile and --version>

## Claims to tests
<!-- One row per claim key. Layer is the cheapest whose real runtime can refute the claim. A second
test needs one of three reasons: independent oracle for money, auth, or data loss; a boundary the first
cannot reach; a bug that happened. -->

| key | claim | layer | refutation test | second test and reason | status | evidence |
|---|---|---|---|---|---|---|
| <claim-slug> | <claim words from SPEC.md> | <unit, local runtime, contract, end to end, live, ui capture> | planned:<path>::<name> | none | Missing | |
| <claim-slug> | <claim words> | <layer> | planned:<path>::<name> | planned:<path>::<name>: boundary at <N+1> | Missing | |

## Severe tests (trust boundaries)
<!-- Planned by drive:architect from the threat model's abuse cases; test names from the severe
tester's report are copied in by the orchestrator. One row per boundary a claim crosses; the abuse
cases come first. Describe the case in words; no working attack material. -->

| key | boundary | abuse case | test | status | evidence |
|---|---|---|---|---|---|
| <claim-slug> | <auth, tenant, input, money, file path, model output, another process's values> | <what a hostile or broken caller does> | planned:<path>::<name> | Missing | |

## Limits probe results
<!-- Filled by running the probe against the local harness, never from documentation. Re-run and
re-record when any toolchain version changes. Copy each result to STATE.md "Verified facts". -->

| platform | production limit | source | N locally | N+1 locally | enforced locally | toolchain | probed | probe test |
|---|---|---|---|---|---|---|---|---|
| <platform> | <limit with number and unit> | <docs URL, checked date> | <accepted> | <rejected or accepted> | <yes or no> | <versions> | <YYYY-MM-DD> | test:<path>::<name> |

## Kindness ledger
<!-- One row per constraint per double or local runtime, filled before any test runs against it.
Mitigation is exactly one of: a guard in production code with its own test; a live check that crosses
the limit; an accepted risk with its reason and the verdict that accepted it. An empty ledger for a
platform with documented limits is a blocking gap. -->

| double or runtime | production constraint | harness behaviour | mitigation | evidence |
|---|---|---|---|---|
| <local runtime or double name> | <constraint with number and unit> | <enforced, not enforced, or never fails this way, from the probe> | guard: `<CONSTANT_NAME>` and <guard> in `<path>` | severe:<path>::<name> |
| <double name> | <constraint> | <behaviour> | live check crossing the limit | live:.drive/proofs/<key>/r<n>/ |
| <double name> | <constraint> | <behaviour> | accepted risk: <reason the limit cannot be reached> | verdict:.drive/proofs/<key>/r<n>/verdict.json |

## Parity (move only)
<!-- One row per corpus class. Goldens are committed before the first commit that changes old code. A
difference is explained only by a named normalizer or a Known-wrong behaviour row in MIGRATION.md. -->

| corpus class | inputs and source | goldens | replay test | diff | status | evidence |
|---|---|---|---|---|---|---|
| <class in words> | <n inputs from <source and window>> | `<path>` at <commit> | planned:<path>::<name> | <empty, or explained by <normalizer or row>> | Missing | |

## Flake quarantine
<!-- The ticket is the Open failures entry in STATE.md. The skip reason in the test names the ticket,
and the skip is an exception row in CONSTRAINTS.md with its DECISIONS.md entry, which is what lets
`drive.py guard` accept it.
A test that guards money, auth, or data loss is never listed here: it blocks. A claim whose only
refutation test is quarantined stays at Partial. -->

| test | ticket | first seen | observed | current hypothesis | repro command | guards money, auth, or data loss |
|---|---|---|---|---|---|---|
| test:<path>::<name> | <YYYY-MM-DD>-<slug> | <YYYY-MM-DD> | <n of m runs> | <mechanism under test> | `<repeat command>` | no |

## Deliberately not tested
| area | reason |
|---|---|
| <area> | <framework behaviour, compiler-checked, third-party, or a SPEC.md non-goal> |

## Deletions
<!-- Tests removed at review as useless, or because their claim was Dropped. Also recorded in STATE.md. -->

| test | reason | commit |
|---|---|---|
| <path>::<name> | <passes a constant stub, duplicates an oracle, asserts a mock call, or Dropped> | <short sha> |
