# Escalation brief · <T-NNN> · rung <n>

<!-- Template: skills/mission/templates/escalation-brief.md. Used by ES3 when a task failed its gate twice at one
     rung. Fresh context: never attach or quote the failing agent's transcript. Stable text first, variable last.
     Ladder: mission-worker → mission-worker-high → mission-builder → mission-strategist (docs only, max 2, written
     reason) → human. ES4 areas start at mission-builder. Log the rung change in BUDGET.md → Escalations. -->

## Role

Agent: <mission-worker-high | mission-builder | mission-strategist> · Model: <claude-sonnet-4-6 | claude-opus-4-8 | claude-fable-5-1> · Effort: <high>
Rung: <n> of the ladder · Previous rung: <agent> (<2> failed attempts)
Why this rung: <"2 failed attempts at <agent>: <gate>" | "ES4 area: <auth|payments|migration|concurrency|security boundary|public contract|infra/CI>" | Fable only: "mission-builder failed: <gate>" or "non-reproducible / cross-system">

## Stable context (read, do not paste)

- Shared conventions and commands: `.mission/CONTEXT.md`
- Requirements and criteria: `.mission/SPEC.md` <REQ ids> · `.mission/acceptance.json` <AC ids>
- Rules that apply: <R-NNN, R-NNN from STATE.md → Rules index>
- Frozen paths (read, never write): `.mission/frozen-paths.txt`
- Contracts (if any): `.mission/CONTRACTS.md`

## Task brief (unchanged from the original)

<path to the original brief, e.g. .mission/lanes/T-NNN/brief.md — do not edit the objective or the acceptance criteria>

Owned paths: <globs> · Forbidden: never modify, skip, delete or special-case tests; never edit `.mission/acceptance.json`,
`.mission/STATE.md` or `.mission/STATUS.md`; never rephrase around a safety refusal (return BLOCKED-SAFETY).

## Gate that is still red

Command: `<exact command>` · Exit code: <n> · Criterion: <AC-NNN>
Output: <path to full log, e.g. .mission/logs/T-NNN-a2.txt> · Salient lines:

```text
<last ≤30 lines or the failing assertion>
```

## Prior attempts (≤300 words, written by the orchestrator from the returns, not the transcripts)

- Attempt 1 (<agent>): tried <approach>; changed <files>; failed because <gate result>.
- Attempt 2 (<agent>): tried <approach>; changed <files>; failed because <gate result>.
- Do NOT repeat: <approaches already falsified>
- Open hypotheses: <H-NNN one line each | none>

## Current diff

<path to patch, e.g. .mission/lanes/T-NNN/attempt-2.patch | "none (reverted to <commit>)">
Start from: <the reverted tree | the attempt-2 diff> (orchestrator decides; say which).

## What to do first

1. Read the red gate output and the prior-attempt summary.
2. State the root cause you believe caused the prior failures, with evidence (file:line or command output), before
   editing anything. If you cannot, investigate until you can or return BLOCKED with what is missing.
3. <mission-strategist only: produce a root-cause statement, revised plan or design at <path>; do not write code.>
4. If a test appears wrong, contradictory, or impossible, STOP and file a TEST-DISPUTE. Do NOT modify, skip, delete, or
   special-case tests, and do NOT carve out the code to match a test.

## Budget for this attempt

≤ <n> tool calls or <n> USD · wall-clock ≤ <n> min · stop and report when exceeded (the attempt counts as failed, ES8).

## Return format (≤400 words plus pointers)

STATUS (<DONE | FAILED | BLOCKED(<reason>) | BLOCKED-SAFETY | TEST-DISPUTE>) · ROOT CAUSE (with evidence) · SUMMARY ·
FILES CHANGED · CHECKS (id = PASS | FAIL · command · exit code · evidence path) · ASSUMPTIONS · OUT-OF-SCOPE FINDINGS ·
memory_delta (`templates/memory-delta.md`) · NEXT
