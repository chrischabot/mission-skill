# BUDGET · <mission name>

<!-- Template: skills/mission/templates/BUDGET.md → .mission/BUDGET.md (M+). The cost ledger: caps, spawn log,
     escalations, downgrade guards, phase reviews. Rules: references/models-and-cost.md (CB, ES, GD, CF).
     Owner: orchestrator. Spawn rows are batch-written by mission-checker from headless JSON or usage deltas.
     Fallback/refusal events live in STATUS.md → Model / fallback events (point there, do not copy).
     Dollar figures are local list-price estimates; reconcile real spend in the Console. -->

Class: <S|M|L|XL> · Profile: <standard | lean (D-NNN) | degraded: <no-fable|no-opus> (D-NNN)> · Billing: <api-usd | plan-usage%>
Soft cap: <n> USD · Hard cap: <n> USD · `--max-budget-usd` in headless runs: <remaining hard cap | not available (checked `claude --help` <YYYY-MM-DD>)>
Orchestrator: <claude-fable-5-1 @ medium | claude-opus-4-8 @ high | claude-opus-4-8 @ xhigh (degraded)>
Prices: references/conventions.md §6 (verified <YYYY-MM-DD>) · US-only inference: <yes → ×1.1 | no>
Preflight: <.mission/logs/preflight.txt> · probes: <S ok · O ok · F ok | not run (S mission)>

## Caps and phase allocation

<!-- Defaults from the scope caps table: S 8/20 · M 50/120 · L 300/700 · XL 1,500/3,500 USD (starting defaults).
     No research phase → add its 10% to verification. >150% of an allocation → written re-plan (D-entry) first. -->

| Phase | Allocation | Planned (USD) | Spent (USD) | % of allocation | State |
|---|---|---|---|---|---|
| Plan / spec / architecture | 15% | <n> | <n> | <n>% | <open | closed> |
| Research | 10% | <n> | <n> | <n>% | <open | closed | n/a → verification> |
| Build | 45% | <n> | <n> | <n>% | <open | closed> |
| Verify / review / audit | 20% | <n> | <n> | <n>% | <open | closed> |
| Reserve | 10% | <n> | <n> | <n>% | <untouched | used by D-NNN> |
| **Total** | 100% | <soft cap> | <n> | <n>% of soft · <n>% of hard | <RUNNING | PAUSED-SOFT-CAP | STOP-BUDGET> |

Fan-out bounds (CB7): writers per wave <2|4|8|12> · max concurrent agents <3|5|8|15> · max spawns per phase <10|40|120|150>.
Wider waves need a value case row below.

| Date | Wave / phase | Width planned | Bound | Value case (one line) | D-entry |
|---|---|---|---|---|---|
| <YYYY-MM-DD> | <wave id> | <n> | <n> | <why breadth pays here> | <D-NNN> |

## Spawn log (one row per agent run)

<!-- Model = the RESOLVED model from headless JSON or usage by-model, not the planned one. Outcome: accepted ·
     failed-gate · refused · fallback · void (canary miss / format failure). Evidence = gate log or report path. -->

| # | Time (UTC) | Task | Role | Agent file | Model (resolved) | Effort | Rung | In / cache-read / cache-write / out (k tok) | USD est | Outcome | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | <HH:MM> | <T-NNN> | <implementer> | <mission-worker> | <claude-sonnet-4-6> | <medium> | <1> | <3 / 410 / 60 / 12> | <0.54> | <failed-gate> | <.mission/logs/T-NNN-a1.txt> |

## Escalations (ES1–ES5)

<!-- One row per rung change. Fable rung (mission-strategist) needs a written reason; max 2 Fable attempts per task. -->

| Time (UTC) | Task | From → To | Attempts at old rung | Red gate + evidence | Brief | Result |
|---|---|---|---|---|---|---|
| <HH:MM> | <T-NNN> | <mission-worker → mission-worker-high> | <2> | <AC-NNN · .mission/logs/T-NNN-a2.txt> | <.mission/lanes/T-NNN/escalation-2.md> | <accepted | failed-gate | next rung> |

Role moves (ES6 de-escalation, ES7 promotion):

| Date | Phase | Role | From → To | Trigger (5 clean first passes + clean audit | 2 disagreements | canary miss | first-pass <60%) | D-entry | Lesson |
|---|---|---|---|---|---|---|---|
| <YYYY-MM-DD> | <phase> | <role> | <agent → agent> | <trigger with evidence> | <D-NNN> | <L-NNN | none> |

## Downgrade guards

Seeded-defect canaries (GD3) — the canary ID and expected verdict never appear in the brief:

| Date | Phase | Checker agent | Batch | Canary id | Planted defect | Expected | Got | Action |
|---|---|---|---|---|---|---|---|---|
| <YYYY-MM-DD> | <phase> | <mission-checker> | <batch id, n items> | <CAN-NN> | <log with exit 1 | missing citation | `.skip` in diff | schema violation> | FAIL | <FAIL | PASS> | <none | batch void → re-run on mission-verifier> |

Sampled blind audits (GD4) — ≥10% of accepted Sonnet-tier outputs per phase, min 1, max 5, by `mission-critic`:

| Date | Phase | Spawn # | Role / agent | First verdict | Audit verdict | Agree | Most important defect (if REJECT) | Action |
|---|---|---|---|---|---|---|---|---|
| <YYYY-MM-DD> | <phase> | <#> | <implementer / mission-worker> | <ACCEPT> | <ACCEPT | REJECT> | <yes | no> | <defect with evidence> | <none | artifact reopened; ES7 count n/2> |

Per-role stats (GD6), updated at each phase boundary:

| Phase | Role | Accepted | First-pass gate rate | Rework count | Audited | Agreements | Canary misses | USD per accepted task | Action |
|---|---|---|---|---|---|---|---|---|---|
| <phase> | <role> | <n> | <n>% | <n> | <n> | <n>/<n> | <n> | <n> | <none | promote (ES7) | de-escalate (ES6)> |

## Phase-boundary reviews

Checklist (copy per boundary):

- [ ] Spawn rows complete for the phase, with resolved models.
- [ ] Spend vs allocation; >150% → written re-plan before the next spawn (CB3).
- [ ] Soft cap reached → pause, STATUS written, narrowed plan proposed (CB4). Hard cap → STOP-BUDGET + HANDOFF.
- [ ] Cost per accepted task by role; any role >2× its peers → check loops, oversized briefs, cache misses.
- [ ] Canaries planted and results recorded (GD3); sampled audit done (GD4); disagreements → GD5/ES7.
- [ ] Fallback events in STATUS reviewed; orchestrator model re-asserted (CF3).
- [ ] Marginal-value test: a gate turned green or a finding verified this phase? Two "no" in a row → stop (CB5).
- [ ] Fan-out stayed inside bounds or has a value case (CB7).

Log:

- <YYYY-MM-DD> phase <name>: spent <n> of <n> USD planned (<n>%); cost per accepted task: <role n, role n>; audits
  <n>/<n> agree; canary misses <n>; fallbacks <n> (STATUS); orchestrator model <verified | restored (event time)>;
  marginal value: <gates newly green / findings verified>; decision: <continue | re-plan D-NNN | pause at soft cap |
  STOP-BUDGET>.

## Retro cost summary

- Total: <n> USD (<n>% of hard cap) · by tier: F <n> · O <n> · S <n> · by phase: <…>
- Cost per accepted task by role: <role n, …> · escalations: <n> (<n> reached Fable) · refusals/fallbacks: <n>
- Audit agreement: <n>/<n> · canary misses: <n> · role moves: <list or none>
- Routing lessons for LESSONS-INBOX.md: <L-NNN one line | none>
