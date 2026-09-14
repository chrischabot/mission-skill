# Migration plan · <from: system / project> → <to: platform service>

<!-- Template: skills/mission/templates/design/MIGRATION.md → .mission/design/MIGRATION.md. Class ≥ L. Never specify
     "same as before": inventory behaviour and dispose of each item. Kept behaviour → PAR-NNN ids; changed → MIG-NNN ids. -->

Links: CHARTER.md · SPEC.md (domains MIG, PAR) · ADRs · Status: draft | reviewed | approved

## 1. Outcomes & non-goals

What gets better: <…> · Deliberately not replicated: <…>

## 2. Current-state map (discovery output, every row with a pointer)

| Capability | Where implemented (file:line / endpoint / dashboard) | Callers | Data owned | External side effects | Undocumented? |
|---|---|---|---|---|---|
| <token accounting> | <gateway/src/usage.ts:40> | <3 services> | <usage rows> | <provider billing calls> | <yes> |

## 3. Behaviour inventory → disposition

| Behaviour | Evidence | Keep / Drop / Change | Req ID | Owner after cutover |
|---|---|---|---|---|
| <retries 429 twice> | <file:line, log sample> | <Keep> | <PAR-001> | <core-gateway> |
| <silently truncates prompts >32k> | <…> | <Drop> | <MIG-004 (reject with 413)> | <core-gateway> |

## 4. Target state

Component ownership after cutover · contract links · data mapping old → new:

| Old entity / field | New entity / field | Transform | Identity used for comparison |
|---|---|---|---|
| <…> | <…> | <…> | <semantic key, not row id> |

## 5. Seams & transitional architecture

| Seam (proxy, feature flag, dual-read) | Temporary code | Removal requirement ID | Removal milestone |
|---|---|---|---|
| <…> | <…> | <MIG-0NN> | <M3> |

## 6. Data import

- Import list: <…>
- Do-not-import list: <transient queues, locks, caches, derived indexes, …>
- ID mapping table: <path>
- Validation and quarantine: invalid records go to <quarantine location> without blocking the import; count reported.
- Idempotency: running the import twice yields an identical canonical result and zero extra provider work.

## 7. Parity criteria (binary, each with an oracle)

| PAR ID | Criterion | Method (replay / shadow / contract test) | Sample & duration | Pass threshold |
|---|---|---|---|---|
| <PAR-001> | <same response schema and status codes> | <replay of <n> recorded requests> | <n requests, 7 days of traffic> | <100% schema match> |
| <PAR-002> | <token accounting> | <shadow> | <…> | <within ±0.5%> |
| <PAR-003> | <latency> | <shadow> | <…> | <p95 new ≤ p95 old> |

## 8. Cutover steps (each with a go/no-go check and an owner)

| # | Step | Go / no-go check (command or dashboard + threshold) | Owner |
|---|---|---|---|
| 1 | Freeze config; export legacy durable truth | <export row counts match source> | <…> |
| 2 | Import; run invariants and restore check | <invariants pass; restore drill <n> min> | <…> |
| 3 | Shadow: new system runs with side effects suppressed; compare outputs | <PAR-* thresholds met> | <…> |
| 4 | Canary: <n%> or one tenant / route | <signals within thresholds for <duration>> | <…> |
| 5 | Promote: **disable the legacy owner of each side effect BEFORE enabling the new owner** | <legacy side-effect counter = 0> | <…> |
| 6 | Observe acceptance window <duration> | <…> | <…> |
| 7 | Retire legacy; keep bounded rollback snapshot until <date> | <…> | <…> |

Invariant: at no step do old and new both own the same external side effect without an explicit suppression fence.
Steps 4, 5 and 7 are irreversible or externally visible → human checkpoint (STATUS.md human queue).

## 9. Rollback plan

Triggers (metric thresholds): <…> · Steps: <…> · Reconciliation of writes made during the new-owner period: <…> ·
Maximum rollback time: <…> · Who decides: <human>

## 10. Risks, security, comms, STOP conditions

- Secrets, keys or provider accounts moving: <list> → security lens mandatory in spec review.
- Comms: <who is told what, when>
- STOP: both systems own a side effect; import would overwrite unclassified data; parity threshold unmet at promote.
