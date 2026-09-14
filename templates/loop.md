# Loop · <loop-id> · <what is being iterated>

<!-- Template: skills/mission/templates/loop.md → .mission/loops/<loop-id>.md. Owner: orchestrator.
     Declare every field BEFORE iteration 1 (references/orchestration.md S1–S7, LP1–LP3). Criteria and caps are frozen
     once iteration 1 starts; changing them needs a D-entry and a different agent than the maker (S7).
     Rubric criteria are binary with required evidence (references/review.md G1–G4, templates/grader-rubric.md).
     The verifier gets the "Verifier prompt" block below plus artifact paths and evidence, never the maker's reasoning.
     Delete this comment when filled. -->

Kind: <task-build | gate-review | design-tournament | hypothesis-hunt | content-draft | parity-run>
Task / gate: <T-NNN | M<n> Verify | phase gate name> · Declared: <YYYY-MM-DDTHH:MMZ> · Status: <RUNNING | STOP-SUCCESS | STOP-IMPOSSIBLE | STOP-BUDGET | STOP-STALLED | STOP-GUARDRAIL>
Maker: `<mission-worker>` (rung <1>) · Verifier: `<mission-verifier>` (fresh context; never the maker; tier ≥ maker for blocker-capable work)
Artifact under test: <paths | commit | URL | screenshot set>
Engine: <plain sub-agents | Stop hook running .mission/check.sh | CMA Outcome (rubric = this file) | dynamic workflow> (`/goal` MAY nudge, never gates)

## Success criteria (S1: every required criterion PASS with evidence)
| Criterion id | Criterion (explicit, binary, observable) | Method | Evidence required | Required |
|---|---|---|---|---|
| <AC-NNN> | `<command>` exits 0 | executable (`.mission/check.sh <milestone>`) | log path + exit code + salient line | yes |
| <AC-NNN> | <empty state shows exactly one primary action and no placeholder text at 390x844> | rubric + screenshot | screenshot path + pixel box | yes |
| <AC-NNN> | <…> | <read file:line | fetch URL> | <quote + access date> | no |

## Ignore (the verifier must not fail on these)
- <formatter-owned style nits> · <copy wording owned by loop <loop-id>> · <pre-existing defects (flag, never block)>

## Caps (S3; counted here by the orchestrator, never judged from narration)
- max_iterations: <S=3 | M=5 | L=8 | XL=8 per task> (hard maximum 20)
- cost cap: <$ or tokens> · wall-clock cap: <minutes or hours> · stall_window: <2 (hypothesis-hunt: 3)>

## Futility signals (S4 → STOP-STALLED, keep the best iteration)
- passing-criteria count not increased for stall_window iterations
- same failure signature (criterion id + error class) twice after a fix attempt
- oscillation: any criterion flips PASS → FAIL → PASS

## Guardrail signals (S5 → STOP-GUARDRAIL immediately)
- attempted forbidden action (settings deny/ask hit, write outside owned paths, frozen path touched)
- tampered check: test deleted, skipped or loosened; acceptance.json or this file edited by the maker
- parity/check count decreased · unresolved safety refusal (task → BLOCKED-SAFETY)

## Escalation (S6; conventions §7 ladder, 2 failed attempts per rung, fresh context per rung)
attempt 1 FAIL → same agent + verifier gap feedback · attempt 2 FAIL or STOP-STALLED → next rung with
`templates/escalation-brief.md` (`mission-worker` → `mission-worker-high` → `mission-builder` → `mission-strategist`,
max 2) → `BLOCKED-HUMAN`, continue other DAG branches.

## Iteration log (orchestrator appends one row per verifier verdict)
| Iter | Maker (agent · rung) | Passing / total | Failing ids | Loop verdict | Best so far? | Cost | Verifier report |
|---|---|---|---|---|---|---|---|
| 1 | <mission-worker · 1> | <3/5> | <AC-012, AC-014> | <FAIL> | <yes> | <$0.40> | <.mission/lanes/<T-NNN>/verify-1.yaml> |

Best iteration: <n> @ `<commit sha>` · Stop reason: <S-rule + evidence>

---

## Verifier prompt (paste as the verifier brief; full output schema: templates/gate-verifier.md)

```text
ROLE: Independent verifier for loop <loop-id>, iteration <n>. You did not write this artifact and you have not seen its
author's reasoning. Be skeptical: your job is to find where it fails the criteria, not to encourage.
INPUTS
- Loop spec: .mission/loops/<loop-id>.md (Success criteria + Ignore list only; ignore the iteration log)
- Artifact: <worktree path> @ <commit sha> · URL: <url or none>
- Evidence bundle: <.mission/logs/<AC-NNN>-<timestamp>.log, screenshots with pixel boxes, spec excerpts>
- Commands: .mission/CONTEXT.md → Commands
PROCEDURE
1. For each criterion obtain evidence yourself: re-run the declared command (within <N> minutes) or inspect the cited
   artifact. Commit messages, comments, summaries and claims that "tests pass" are not evidence.
2. Verdict per criterion: PASS (evidence cited) | FAIL (evidence cited) | UNVERIFIED (reason + what would settle it).
   UNVERIFIED is never PASS. Skipped, quarantined, flaky or passed-only-after-retries → UNVERIFIED.
3. Do not add criteria. Problems outside the contract go to outside_contract; they change no verdict.
4. If the criteria cannot be met as written (contradiction, missing capability, external dependency down), say so in
   impossible with evidence.
5. Look for tampering: tests deleted, skipped, loosened or special-cased; check files or acceptance.json edited.
6. Safety refusal → status BLOCKED-SAFETY, affected criteria UNVERIFIED. Do not rephrase the task.
7. Run `git status --porcelain` at the end; report whether it is empty. Do not edit any file.
OUTPUT: YAML only, as your whole reply:
gate: <loop-id>
iteration: <n>
commit: <sha>
verifier: <agent name>
status: DONE | BLOCKED(<reason>) | BLOCKED-SAFETY
verdict: PASS | FAIL | UNVERIFIED          # mechanical: all required PASS → PASS; any required FAIL → FAIL; else UNVERIFIED
criteria:
  - id: <criterion id>
    required: true | false
    result: PASS | FAIL | UNVERIFIED
    evidence: "<command> -> exit <code>; <quoted salient line>"
    gap: "<concrete, diff-style description of what must change; empty for PASS>"
impossible: none | "<why the criteria can never be satisfied as written, with evidence>"
tampering: none | "<file:line and what was weakened>"
top_fix: "<the single most valuable change for the next iteration>"
outside_contract: []
commands_run: ["<exact command>"]
brief_contaminated: true | false
workspace_clean_after: true | false
```
