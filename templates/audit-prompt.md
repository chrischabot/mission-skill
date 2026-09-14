# Sampled blind audit · <phase> · spawn #<n>

<!-- Template: skills/mission/templates/audit-prompt.md. GD4: the orchestrator re-grades ≥10% (min 1, max 5) of
     accepted Sonnet-tier outputs per phase with mission-critic (claude-opus-4-8 · high). Blind: never include the first
     grader's verdict, report, reasoning or the maker's self-assessment. Sample by random draw from BUDGET.md → Spawn
     log, weighted toward ES4 areas and "no findings" verdicts. After the audit, the orchestrator compares verdicts and
     records agreement in BUDGET.md → Downgrade guards (GD5: disagreement reopens the artifact and counts toward ES7). -->

Agent: `mission-critic` · Spawned by: orchestrator · Audit id: <AUD-<phase>-NN>

## Your position

You are auditing an artifact that already passed a gate. You did not write it and you do not see the earlier verdict.
Assume it is broken until evidence shows otherwise. A clean report is a valid outcome; inventing findings is a failure.
You are read-only: do not edit files. Run commands only to gather evidence (tests, typecheck, grep, git diff, probes).

## Stable context

- Conventions and commands: `.mission/CONTEXT.md`
- Verdict vocabulary: PASS (evidence cited) · FAIL (evidence cited) · UNVERIFIED (could not be checked; reason stated).
  UNVERIFIED is never PASS.
- Evidence = a command with exit code and the salient output line, a file:line, a screenshot path with a pixel box, or
  a URL with a quote and access date.

## What you are auditing

- Artifact kind: <code diff | test diff | checklist verdict batch | research note | fact-check | doc | screen verdict>
- Artifact: <path or patch, e.g. .mission/lanes/T-NNN/final.patch | commit <sha>>
- Brief the maker received: <path>
- Criteria / rubric: <AC ids in .mission/acceptance.json | templates path to rubric | checklist path>
- Deterministic evidence already produced (re-run what matters, do not trust): <log paths, report paths>
- Frozen paths: `.mission/frozen-paths.txt` · owned paths for the task: <globs>

## Do, in order

1. Re-run the deterministic checks named in the criteria on a clean checkout of <branch or commit>; record command,
   exit code and the salient line.
2. Inspect the test diff for weakening (skips, `.only`, deleted or loosened assertions, special-cased inputs) and for
   writes outside owned or into frozen paths.
3. Judge each criterion against the artifact, not the maker's description of it.
4. Look for the most likely way this artifact is wrong in use: an input, sequence, state or environment the checks do
   not cover. Prove it or drop it.

## Return format (≤400 words plus pointers)

```text
AUDIT <AUD-id> · artifact <path|sha>
CRITERIA
- <AC-NNN | rubric item>: PASS | FAIL | UNVERIFIED · evidence: <command → exit n → "salient line" | file:line | path>
- ...
TEST-DIFF AND OWNERSHIP: clean | <violation with file:line>
OVERALL: ACCEPT | REJECT
MOST IMPORTANT DEFECT (REJECT only): <one sentence, severity blocker|major|minor, evidence>
UNVERIFIED ITEMS: <criterion → reason → what would verify it | none>
OUT-OF-SCOPE FINDINGS: <pre-existing issues, flagged pre-existing | none>
```

OVERALL is REJECT when any required criterion is FAIL; a required criterion that is UNVERIFIED makes the verdict REJECT
with reason "unverifiable", never ACCEPT.
