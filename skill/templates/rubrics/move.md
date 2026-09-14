# Rubric · move · <goal slug>
frozen: <ISO UTC> · commit <short sha> · copied from templates/rubrics/move.md by drive:architect
variant: <move/migration | move/refactor | move/upgrade> · applies to: <invariant and claim keys>
baseline: <baseline_sha> · charter: .drive/MIGRATION.md | .drive/SPEC.md (change spec)

<!-- Fill every placeholder, delete variant and trait rows that do not apply, and commit before the
first code moves. Never edit during a verification loop. Each criterion reads: observation, oracle,
refutation, threshold. A criterion that cannot apply is reported as `rubric_gap:`. At cutover run two
verifiers with distinct lenses, parity and operability, and require both to pass. Rules:
references/verification.md; goldens and replay: references/testing.md section 12. -->

## Standing floor
<!-- Always in scope. Never a rubric gap. -->

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| No weakened tests | no skip, focus, or ignore marker added; no assertion removed or widened; goldens never regenerated to match new output | `drive.py guard` exit 0; marker grep and diff of tests and goldens over the range | a golden rewritten without a Known-wrong behaviour row | blocking |
| Harness no kinder than production | every stand-in for the old or new system has kindness-ledger rows; replay ran with production limits enforced | TESTPLAN.md ledger and limits probe | a replay that passes only because a stand-in skips a limit | blocking |
| No data loss | every destructive step (schema change, rewrite, deletion, rotation, route removal) had a tested backup and a written undo first | MIGRATION.md backups and undo ledger against the command log | a destructive action logged before its backup or undo row | blocking |
| Security holds | authorization, tenant, and rate-limit semantics of the old path are preserved; no secret in tracked files | parity on identity and tenant decisions; secret scan | a divergence on an identity or tenant decision; a matched secret | blocking |

## Process

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Goldens before change | characterization goldens were committed before the first commit that changed old code | `git log` order of the goldens path against the old code paths | goldens committed later, or absent | blocking |
| Baseline recorded | the pre-existing suite's names and pass counts at `<baseline_sha>` are saved | baseline log path | no baseline | blocking |
| Forced before waiting | synthetic traffic, corpus replay, direct handler triggers, and the drill ran before any soak window opened | soak record "forced beforehand" column | a soak opened with forcible checks not yet run | blocking |
| Verifier ran the gates | each verdict's `ran` holds the test command and the replay command at exit 0 | verdict.json | either absent | blocking |

## User outcome

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Consumers see no difference | every consumer in the inventory gets the contract it depended on through the new path | per-consumer parity evidence in MIGRATION.md | a consumer error or contract change not listed as intended | blocking |

## Shape criteria

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Replay parity | the recorded corpus replays with an empty diff, or each difference is explained by a named normalizer or a Known-wrong behaviour row | replay test output | an unexplained difference | blocking |
| Live decision parity | mismatch on deterministic decisions at most <0.1> percent overall and zero on identity, tenant, and cost | parity report with its query and window | over tolerance | blocking |
| Inventory complete | every consumer row is migrated with evidence and Unknowns is empty before the first traffic step | MIGRATION.md inventory against the old path's access logs over <window> | traffic from an identity no row lists | blocking |
| Expand and contract order | each expand, dual-write, backfill, read switch, and contract step deployed alone, never a schema step with a cutover release | deploy log and commits | two steps in one deploy | blocking |
| Backfill verified | backfilled data matches by row counts, a checksum over sorted keys, and sampled field comparison | verification query output | any mismatch | blocking |
| Rollback drilled | the undo ran exactly as written at the first non-zero stage, restored within <n> minutes, with no improvisation | rollback drill table | failure, overrun, or improvisation | blocking |
| Stage budgets held | each stage kept new-path error rate at most control plus <0.1> points and p95 at most <1.2> times control | stage metrics with source labels | a breach without automatic rollback | blocking |
| Nothing references the old path | disabled path at zero hits for a full cycle; search across repositories, configuration, schedules, and runbooks finds nothing | log query and `<search command>` output | any hit | blocking before decommission |
| No open soak at Done | every soak window is closed with a decision | soak record | an open window | blocking |

## Variant additions

| variant | criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|---|
| `move/refactor` | Behaviour identical | full test output before and after lists the same test names and results; no test file edited | baseline log against the verifier's run; test-file diff | a new failure, a missing test, or an edited test | blocking |
| `move/refactor` | Complexity removed, not relocated | the concepts a reader must hold to follow <area> are fewer after the change | reviewer count of branches, modes, and layers before and after | an unchanged count with code merely moved | should_fix |
| `move/upgrade` | One dependency per change | each upgraded dependency lands in its own commit with its changelog's breaking changes listed | `git log` and the commit bodies | two upgrades in one commit, or no breaking-change list | should_fix |
| `move/upgrade` | Lockfile reviewed, runtime smoke passes | lockfile diff shows only intended packages; the app starts and serves <smoke flow> | lockfile diff; smoke output | an unintended package change, or a failed smoke | blocking |

## Trait additions

| trait | criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|---|
| `async-scheduled` | Schedules moved, not duplicated | each schedule exists on exactly one path after cutover and was triggered once through its own verb | schedule listing on both platforms; trigger output | a schedule on both paths, or none | blocking |
| `data` | Down path executed | each schema step's down path ran on a copy | command log | an unexecuted down path | blocking |
| `multi-repo` | Change order held | repositories changed in the order in DESIGN.md, contract first | commit timestamps across repositories | a consumer changed before its contract | blocking |

## Amendments
- <ISO UTC> · <criterion added, removed, or reworded> · because <rubric gap or ruling> · DECISIONS.md <date>-<slug> · applies from <unit>
