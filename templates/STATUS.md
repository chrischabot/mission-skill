# STATUS · <mission name>
Updated: <YYYY-MM-DDTHH:MMZ> · Session: s<N> · Harness: <claude-code|cma|headless|routine>
Class: <S|M|L|XL> — <one-line justification: A?/B? …> · Shape: <primary> (+ <secondary shapes>) · Traits: <ui, auth, payments, migration, public-content, ai-behaviour, …>
Phase: <0 Intake|1 Research|2 Spec|3 Design|4 Plan|5 Build|6 Verify|7 Review|8 Release|9 Retro> · Stop state: <RUNNING|STOP-SUCCESS|STOP-IMPOSSIBLE|STOP-BUDGET|STOP-STALLED|STOP-GUARDRAIL|BLOCKED-HUMAN|BLOCKED-SAFETY>
Orchestrator: <claude-fable-5-1 @ medium | claude-opus-4-8 @ high> · Profile: <standard|lean|degraded (D-NNN)> · Mode: <interactive|autonomous>

<!-- Template: skills/mission/templates/STATUS.md → .mission/STATUS.md (M+). WHAT IS DONE / NEXT.
     Owner: orchestrator only; write it before every dispatch wave and after every integration. Budget: ≤100 lines.
     No facts or rules here (STATE.md), no decision rationale (DECISIONS.md), no raw logs (logs/). Point, don't copy.
     States (conventions §4) — gates: PENDING · PASSED · PASSED-WITH-WAIVER(D-id) · BLOCKED(<reason>) · PENDING-LIVE.
     Tasks: TODO → READY → IN-PROGRESS → VERIFYING → PASSED | FAILED(iter n) | STALLED | BLOCKED(<reason>) |
     BLOCKED-HUMAN | BLOCKED-SAFETY | CANCELLED(D-id). The SessionStart hook prints the header, Gates and top Board rows. -->

## Goal
- Direction (verbatim): "<the user's high-level direction>"
- Done means (each maps to acceptance checks in acceptance.json; OUT ids from CHARTER.md):
  1. <OUT-001 observable outcome> → AC-001, AC-002
  2. <OUT-002 observable outcome> → AC-003
- Started: <YYYY-MM-DD> · Target: <YYYY-MM-DD or none> · Status: <active|paused|done|abandoned (D-NNN)>

## Progress
<!-- From verifier-recorded gate results only, never from task counts. -->
- Acceptance: <k>/<n> checks PASS · <u> UNVERIFIED · <p> PENDING-LIVE (last verifier run <YYYY-MM-DDTHH:MMZ>, verification/VERIFICATION-<M>.md)
- Milestones: M0 <gate state> · M1 <gate state> · M2 <gate state>

## Gates
| Phase / milestone | State | Evidence | Verifier (agent) | Date |
|---|---|---|---|---|
| 0 Intake | <PENDING> | <CHARTER.md, ASSUMPTIONS.md, preflight output logs/preflight.txt> | <mission-checker> | <YYYY-MM-DD> |
| 2 Spec | <PENDING> | <acceptance.json 0/<n> passing; reviews/spec-disposition.md> | <mission-critic> | <—> |
| M1 Verify | <PENDING> | <verification/VERIFICATION-M1.md> | <mission-critic> | <—> |

## Board
| Task | Milestone | Title | Owner (agent · model · effort) | Needs | Owned paths | Checks | State | Iter | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| T-001 | <M1> | <title> | <mission-worker · claude-sonnet-4-6 · medium> | <—> | <apps/api/src/<area>/**> | <AC-001, AC-002> | <READY> | <0/5> | <—> |
| T-002 | <M1> | <title> | <mission-builder · claude-opus-4-8 · high> | <T-001> | <packages/contracts/**> | <AC-003> | <TODO> | <0/5> | <—> |
<!-- Iter = iterations used / loop cap (S3 · M5 · L8). "PASSED" needs the verifier's evidence path in Evidence. -->

## Budget
<!-- Summary only; the ledger (caps, spawn log, escalations, audits) is BUDGET.md. -->
- Mission: <used> / <soft cap> soft · <hard cap> hard (<tokens or USD>) · source: <headless total_cost_usd | usage view>
- Current phase/milestone: <used> / <cap> · Largest spender: <agent · task>

## Model / fallback events
| Time (UTC) | Task | Event (fallback, refusal, escalation, alias check) | From → To (model @ effort) | Category | Action taken |
|---|---|---|---|---|---|
<!-- After a fallback, re-select the intended model at the next phase boundary. Unresolved refusal → BLOCKED-SAFETY. -->

## Human queue (batched)
<!-- One message per batch. Only irreversible / externally visible actions, L/XL spec sign-off, stop-rule escalations. -->
- [ ] <decision needed> · default taken: <x> · blocks: <T-ids> · since <YYYY-MM-DD>

## Stop-rule log
- <YYYY-MM-DD> <T-NNN|loop id> <STOP-STALLED|STOP-BUDGET|…> (<signal, e.g. same failure signature on AC-NNN twice>) → <escalated to mission-builder (D-NNN) | BLOCKED(<reason>)>

## Risks
- <YYYY-MM-DD> · <risk or open finding> · impact: <…> · owner: <role> · mitigation / where tracked: <FND-id, O-NNN, D-NNN>

## Done log (newest first, keep 10; older → archive/status-YYYY-MM.md)
- <YYYY-MM-DD> · <T-NNN> <title> PASSED · evidence: <verifier report path or `command` → output line>
