# <From> to <To> · migration charter
Version: <YYYY-MM-DD> · shape: move/migration · size: <M|L|XL> · baseline: <baseline_sha> · latest review: <.drive/reviews/<file> | none yet> · changes: <count>

<!-- Written by drive:architect from archaeology and the consumer inventory. Rules: references/spec.md
and the move shape file. 1,000 to 2,500 words. A migration specifies no new behaviour; wanted new
behaviour is a feature sub-goal after cutover. Nothing here is a numbered identifier: invariants,
consumers, stages, and normalizers are named in words. The undo ledger, drill, soak, and decommission
sections are appended during the run and never rewritten. Delete guidance comments before the spec gate. -->

## Current state
<!-- Read from the systems, never from memory: what exists, where it runs, who calls it, what it
stores, measured traffic and data volumes with the command that measured each. -->

## Target state
<!-- The same paragraph rewritten for the end: what exists, what is deleted, and what callers see that
differs, if anything. -->

## Point of no return
<!-- The one step after which rollback means recovery rather than undo, and what recovery costs. -->
Step: <stage or action> · Recovery after it: <path and cost>

## Invariants
<!-- Things that must hold before, during, and after. Include the ones that break silently: ordering,
time zones, rounding, idempotency, authorisation semantics, platform limits, error shapes. Each heading
is a claim and a STATUS key. -->

### <Invariant as a claim in three to eight words>
Check: <characterization golden, parity event field, or live query, with its command>

What would prove this wrong

**<Regression scenario title>**
Given <state>. When <the same input reaches the new path>. Then <the outcome identical to the old path>.

## Consumer inventory
<!-- Sources in order of reliability: the old path's own access logs over at least one full traffic
cycle; a search of every reachable repository and client configuration; schedules on every machine
and platform; runbooks and dashboards. A consumer can be a row in a table. When the old path does not
log caller identity, or keeps logs for less than a cycle, deploy identity logging first as a small
package with its undo and keep building while the cycle accumulates; only the first traffic step waits. -->
Observed window: <start> to <end> from <log source>

| consumer | kind | where | contract it depends on | found by | traffic | migrated | parity evidence |
|---|---|---|---|---|---|---|---|
| <name> | <code, binding, http, schedule, queue, cli, repository, runbook, or webhook> | <path, config key, or host> | <request and response shape> | <log identity, search command> | <per day> | no | none |

### Unknowns
<!-- Must be empty before the first traffic step. Each entry is traffic or a reference not matched to a
listed consumer. -->
- <identity, user agent, or reference not yet matched> · seen <count> in window · next check: <what>

## Characterization
Goldens:      `<path>` · produced by `<command>` at <baseline_sha> · labelled observed, never correct
Recorded traffic: `<store or prefix>` · window <start> to <end> · kept out of git
Redaction, written before recording starts: <headers, cookies, tokens, identifiers hashed, body size cap>

### Known-wrong behaviour
| behaviour observed today | preserved or fixed | decision |
|---|---|---|
| <what the old path does that is wrong> | <preserved, or fixed as a contract change> | <DECISIONS.md entry> |

## Parity
<!-- Parity is defined on deterministic decisions, never on non-deterministic payloads such as model
text. Every normalizer is named. A second normalizer for the same class of mismatch stops the work for
an investigation. -->

| decision compared | comparison | tolerance |
|---|---|---|
| <decision: identity, tenant, route, cache key, limit verdict, cost line, log row> | <identical, or equal after a named normalizer> | <zero divergence, or at most a stated percentage> |

Normalizers:
- <name>: <what it ignores, such as ordering, whitespace, float precision, timestamps>, because <reason>.

Shadowing: the old path serves; the new path runs on <share of traffic, stubbed or real upstream> and publishes events to <store>. Writes to shared stores are never shadowed; they are dual-written with an idempotency key and compared at read time.

## Requirements
<!-- Parity and operability claims only, in the claim format. Heading slugs are STATUS keys. -->

### <Claim in three to eight words>

**<Scenario title>**
Given <state>. When <trigger>. Then <observable outcome>.

**<Scenario title>**
Given <state>. When <trigger>. Then <observable outcome>.

What would prove this wrong

**<Refuting scenario title>**
Given <state>. When <trigger>. Then <the outcome a divergent implementation would not produce>.

## Expand and contract
<!-- Each step deploys and reverts on its own. Never pair a schema step with a cutover release. -->
1. Expand: <new shape added beside the old, deployed alone>.
2. Dual write: <both shapes written, with the idempotency key>.
3. Backfill: <throttled batches resumable by cursor, sized from limits, run by a command>; verified by row counts, a checksum over sorted keys, and sampled field comparison.
4. Switch reads: <reads move while writes still go to both, and how that is verified>.
5. Stop writing the old shape: <when>.
6. Contract: <old shape removed in a later deploy once search and logs show no reader>.

## Stages
<!-- Defaults unless GOAL.md set targets: new-path error rate at most control plus 0.1 percentage points;
p95 latency at most 1.2 times control; parity mismatch at most 0.1% overall and zero on identity, tenant,
and cost; at most a dozen metrics, compared with control in the same window. An exhausted budget rolls
back to the previous stage automatically. When every consumer is owned and enumerable from configuration
(five or fewer), stages go consumer by consumer with the drill before the first, and only the final stage
soaks for a full cycle; record that choice in DECISIONS.md. -->

| stage | scope or weight | entry condition | error budget | soak length | check and who runs it | on breach | undo |
|---|---|---|---|---|---|---|---|
| <name> | <consumer or percentage> | <evidence required> | <budget> | <one full traffic cycle, or shorter with reason> | <command or admin endpoint> | roll back to <stage> | <undo ledger row> |

## Backups
<!-- Before any destructive step: schema change, data rewrite or deletion, secret rotation, route or
schedule removal. -->
| taken at (UTC) | what | command | copy kept at | restore command | restore tested |
|---|---|---|---|---|---|

## Undo ledger
<!-- Append-only. Write the row before executing the action. -->
| when (UTC) | action | undo | evidence |
|---|---|---|---|
| <YYYY-MM-DDTHH:MMZ> | <action> | `<exact reverse command>` | <deploy id, bookmark, export path, first log line> |

## Rollback drill
<!-- At the first non-zero stage, run the undo exactly as written. Repeat once for the data layer when a
schema change is involved. A drill that needed improvisation means the cutover does not advance. -->
| date (UTC) | stage | undo run as written | time to restore | traffic back on old path shown by | error rate back to control | improvisation needed | rolled forward |
|---|---|---|---|---|---|---|---|

## Soak record
<!-- Force everything that can be forced before waiting: synthetic traffic, corpus replay, handlers
triggered directly, the drill. The scheduled check decides and acts (advance, hold, roll back); it never
produces an item for a person to review. While a soak is open the migration is at most Live Proof. -->
| stage | window start | window end | forced beforehand | check mechanism | decision | evidence |
|---|---|---|---|---|---|---|

## Decommission
1. Disable: <old routes, schedule triggers as well as handlers, and tokens>; the old path answers with a logged, named refusal · done <date> · commit <sha>
2. Observe: zero hits on the disabled path from <start> to <end> · evidence <query and output path>; every consumer row migrated with evidence
3. Delete code: commit <sha>
4. Delete data stores: safe to delete after <YYYY-MM-DD> with export kept at <location>; command `<command>`; restore `<command>`; DECISIONS.md <entry>; dated STATE.md line outside Done; scheduled check `<task name>` confirms the export restores and nothing read the store, then deletes it and commits the evidence, or holds and writes an investigation

## Where the test environment is kinder than production
- <System or limit>: <local stand-in> permits <what production forbids>. Closed by: <limit enforced in the double, dry run on a production export, or live check>.

## What each rung means here
- Local Proof: goldens and replay pass on both paths against production-shaped data with production limits enforced; migration and backfill run against an export locally; down path exercised.
- Live Proof: shadow parity met the budget for a full cycle; the rollback drill ran in production; at least one stage soaked.
- Operational: full traffic held through its soak; old path disabled and at zero hits for a cycle; every consumer migrated with evidence; docs updated.
- Done: old code deleted, flag removed, store deletion check scheduled for the end of the window with exports kept, and code, tests, proofs, STATUS, and docs agree.

## Assumptions

### We assume <the decision, as a plain claim>
Because: <the facts or preferences that drove it>.
Instead we could have: <the strongest alternative>.
To overturn: say "<sentence>". Before <milestone> this costs <cost>; after it costs <cost>, because <reason>.
Status: assumed <YYYY-MM-DD>

## Risks
- <Risk>. Trigger: <what would confirm it>. Response: <what the run does>.

## Changes
- <YYYY-MM-DD> · <heading words affected> · <what changed and why> · invalidates: <keys demoted, tests to re-run> · decision: <DECISIONS.md entry | none>
