# Swarm decision (go/no-go) + STATUS swarm section

<!-- Template: skills/mission/templates/swarm-decision.md. Rules: references/swarms.md SW1–SW6, SW26–SW28, P1–P8.
     Fill part A before dispatching any wave with more than 2 agents (writers or readers) and paste it, with part B,
     into .mission/STATUS.md under "## Swarm" (newest wave first; older waves → archive/status-YYYY-MM.md, keep 3).
     Owner: orchestrator only. Every ticked box carries evidence (command → output line, or file path).
     S missions: skip this file (1 maker + 1 verifier). M missions: part A + a 5-row board is enough. -->

## A. Go/no-go · wave <W<k>> · <YYYY-MM-DDTHH:MMZ>

Pattern: <pipeline | classify-and-act | fan-out/map-reduce | adversarial verification per item | loop-until-done |
generate-and-filter | best-of-N | tournament | none: single writer>
Surface: <parallel Agent calls | dynamic workflow | claude -p (run-wave.sh) | CI matrix | sequential>
Degradation path if unavailable: <workflow → Agent calls → sequential → claude -p → single session>
Lanes: <n> writers (cap <S2|M4|L8|XL12>) · <n> readers (cap <class reader cap; ≤16 inside a workflow>) · Class: <S|M|L|XL>
Planner: <orchestrator inline | mission-strategist> · Integrator: `mission-integrator` · Merged-result verifier: `mission-critic`

### GO requires every box ticked

- [ ] **Independence:** owned globs disjoint — `.mission/bin/check-ownership.sh .mission/lanes/W<k>.wave` → exit 0
      (`.mission/logs/ownership-W<k>.txt`)
- [ ] **Runtime:** no shared mutable runtime, or each lane has its own port range, database/schema, simulator, temp dir
      (values in each lane contract)
- [ ] **Contracts:** cross-lane decisions frozen and linked — `.mission/CONTRACTS.md` v<n>, D-<NNN> (or "no shared
      interface" with reason)
- [ ] **Checks:** every lane cites ≥1 existing executable or evidence-backed `AC-NNN`
- [ ] **Size:** each lane fits one fresh context (≤ ~15 owned files; briefs point, don't paste)
- [ ] **Worth it:** each unit ≥ ~15 min single-agent work, or ≥10 homogeneous units
- [ ] **Machine-verifiable success** per writer lane, or taste work runs as proposals → tournament → one writer
- [ ] **Budget:** estimate = <lanes> × <per-lane tokens or USD> × 1.3 = <total> ≤ wave budget <cap>; mission spent
      <p>% (< 80%)
- [ ] **Integration plan:** integration branch `claude/<mission>/integration` @ <sha>, merge order <T-NNN → T-NNN>
      (critical path first), smoke command `<cmd>`
- [ ] **Stall rule:** time box <min> and tool-call cap <n> per lane; retry once narrowed → tier up → STALLED
- [ ] **Allowlist:** commands lanes need are in `permissions.allow` (unattended workflow or headless only)
- [ ] **Spawn point:** dispatch from the primary checkout (`git rev-parse --show-toplevel` = primary path)

### NO-GO triggers (any one ticked → single writer or sequential)

- [ ] Two lanes need the same file, migration, schema, lockfile or registry
- [ ] Success is taste-only and no rubric exists
- [ ] Requirements still ambiguous (spec gate not PASSED)
- [ ] ≥2 lanes in an earlier wave hit the same root cause and the space was not re-partitioned
- [ ] Work is S-size (≤ ~3 files or ≤ one agent-hour)
- [ ] Data/schema migration or infra/CI change inside the wave
- [ ] Bug not yet `REPRODUCED` (experiment lanes only after REPRODUCED)

Decision: <GO | NO-GO> · Reason: <one line> · Est. multiplier vs single agent: <×n> · Override of a NO-GO trigger:
<none | D-<NNN>>

## B. STATUS section (paste under "## Swarm" in .mission/STATUS.md)

```markdown
## Swarm · wave W<k> · pattern <name> · surface <surface> · decision <GO | NO-GO> (<YYYY-MM-DD>)
Base: <sha> · Integration: claude/<mission>/integration @ <sha> · Contract: v<n> · Ownership check: exit 0 (logs/ownership-W<k>.txt)

| Lane | Role · agent · model | Owns | Branch | Runtime | Status | Last checkpoint (UTC) | Checks (self) | Verifier | Merged |
|---|---|---|---|---|---|---|---|---|---|
| T-014 | maker · mission-worker · claude-sonnet-4-6 | apps/api/src/outfits/** | claude/<mission>/T-014-api-outfits | PORT 4010 · DB app_T-014 | DONE | 14:02 | AC-021 PASS, AC-022 PASS | PASS (lanes/T-014/verify-1.yaml) | @a1b2c3d |
| T-015 | maker · mission-worker · claude-sonnet-4-6 | apps/ios/Features/Grid/** | claude/<mission>/T-015-ios-grid | sim <UDID> | STALLED (retry 1/1 narrowed) | 13:10 | AC-030 FAIL | — | — |

Budget: wave est <n> · spent <n> · mission <p>% · stop-dispatch threshold 80%
Wave metrics: dispatched <n> · first-try PASS <n> · integration reverts <n> · stalls <n> · same-root-cause events <n>
Merged-result verifier: <PENDING | PASS | FAIL> (<verification/VERIFICATION-<M>.md or reviews path>)
Cleanup debt: <none | .claude/worktrees/T-015 locked; branch claude/<mission>/T-012-… unmerged>
```

Status values in the board: `DONE` · `STALLED` · `TEST-DISPUTE` · `BLOCKED(<reason>)` · `BLOCKED-SAFETY` (lane return);
the STATUS Board task state (`IN-PROGRESS` → `VERIFYING` → `PASSED` …) stays the source of truth for progress.
