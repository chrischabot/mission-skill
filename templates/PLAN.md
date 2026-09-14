# PLAN · <mission name>

<!-- Template: skills/mission/templates/PLAN.md → .mission/PLAN.md (M+; S missions keep 1–3 tasks in the task card).
     Owner: orchestrator (L/XL: drafted by mission-strategist, adopted by the orchestrator). Rules: references/orchestration.md
     W1–W10. Progress does NOT live here: task state, iterations and evidence live in STATUS.md → Board.
     A task = one verifiable change in one fresh context: cites ≥1 AC id, lists owned paths, ≤ ~15 files, ≤ ~1 human-day.
     Two tasks in the same wave never own the same path (check with .mission/bin/check-ownership.sh where installed).
     Changing a milestone's scope after Plan PASSED needs a D-entry. Delete this comment when filled. -->

Class: <S|M|L|XL> · Shape: <primary> · Plan version: <n> (D-<NNN> for every re-plan) · Updated: <YYYY-MM-DDTHH:MMZ>
Integration branch: `claude/<mission>/integration` · Default branch: `<main>` (never pushed to by agents)

## Milestones

| Milestone | Outcome (observable) | Exit gate checks | Budget allocation | Human checkpoint | Depends on |
|---|---|---|---|---|---|
| M0 | <contract frozen + walking skeleton: real entrypoint → one core flow → backend round-trip on dev> | <AC-001, AC-002> | <$ or % of mission cap> | <none | spec sign-off (L/XL)> | — |
| M1 | <first user-visible slice> | <AC-003 … AC-010> | <…> | <none> | M0 |
| M2 | <…> | <…> | <…> | <release approval> | M1 |

Rules: M0 exists for multi-surface work (MP-1, MP-2). Every AC id in acceptance.json belongs to exactly one milestone.
Every milestone ends at Verify (VERIFICATION-<M>.md) before the next milestone's Build starts, unless a D-entry allows
overlap.

## Task DAG

<!-- One block per task. `needs` lists T-ids that must be PASSED first. `agent` is a roster name (conventions §7).
     `risk` = low | high (auth, payments, data migration, concurrency, security boundary, public contract, infra/CI → start
     at mission-builder). `parallel-safe: yes` only with worktree isolation and disjoint owned paths. -->

### T-001 · <one-line title>
- milestone: M0 · needs: [] · agent: <mission-worker> · verifier: <mission-verifier> · risk: <low>
- owned: `<apps/api/src/<area>/**>` · reads: `<packages/contracts/**>` · frozen (read-only): `<tests/acceptance/**>`
- checks: [<AC-001>] · test author task: <T-000 | none (tests exist and are frozen)>
- fits one fresh context: <yes — est. <n> files, <n> tool calls>
- parallel-safe: <yes (worktree claude/<mission>/T-001-<slug>) | no (touches shared schema)>
- notes: <reuse pointers, R-/L- ids to consult>

### T-002 · <one-line title>
- milestone: M0 · needs: [T-001] · agent: <mission-builder> · verifier: <mission-critic> · risk: <high: migration>
- owned: `<migrations/**>` · reads: `<design/MIGRATION.md>` · frozen (read-only): `<tests/regression/**>`
- checks: [<AC-002>] · test author task: <T-000>
- fits one fresh context: <yes — est. <n> files>
- parallel-safe: <no>
- notes: <…>

## Waves

<!-- A wave = ready tasks with disjoint owned paths, at most S≤2 · M≤4 · L≤8 · XL≤12 writers. Read-only lanes MAY reach
     16 inside a workflow. Run the swarm go/no-go (references/swarms.md) before any wave with >2 agents. -->

| Wave | Tasks | Owned paths disjoint? (evidence) | Surface | Integration order |
|---|---|---|---|---|
| W1 | T-000 (test author) | n/a (single writer) | Agent call | — |
| W2 | T-001, T-003 | <yes: `check-ownership.sh W2` → exit 0> | <parallel Agent calls | workflow | claude -p> | <T-001 → T-003> |

Critical path: <T-001 → T-002 → T-005> (strongest agents, monitored first).

## Plan lint (mission-checker fills; the Plan gate stays PENDING until every row is PASS with evidence)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Every task cites ≥1 AC id that exists in acceptance.json | <PASS|FAIL> | <command or file:line> |
| 2 | Every executable/rubric AC id is cited by ≥1 task | | |
| 3 | Every task lists owned paths, needs, agent, verifier | | |
| 4 | DAG is acyclic; every `needs` id exists | | |
| 5 | Owned paths are disjoint within each wave | | |
| 6 | Wave sizes within the class ceiling | | |
| 7 | Risky tasks start at `mission-builder`; blocker-capable tasks have verifier tier ≥ maker | | |
| 8 | No task exceeds ~15 files or one fresh context | | |
| 9 | Test-author tasks precede the implementation tasks they gate | | |
| 10 | Budget allocated per milestone and sums to ≤ the mission cap in BUDGET.md | | |
| 11 | M0 contract / walking skeleton first where the profile requires it | | |
| 12 | Release tasks carry human checkpoints for irreversible actions | | |
