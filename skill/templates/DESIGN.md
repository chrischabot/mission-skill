# DESIGN · <project> · <goal slug>
reconciled at: <short sha>
spec: .drive/SPEC.md@<short sha>
capability map: .drive/capability-map.md | one capability; no map
design contract: design/DESIGN.md | not applicable because <no ui trait>
latest review: .drive/reviews/<date>-design-<slug>.json, or <date>-design-review-r<n>.md from drive:architect · verdict: <pass | pass-with-changes | block>

<!-- Write every section in order. When a section does not apply, write
"Not applicable because <reason>." Never delete a heading. Restate nothing that SPEC.md
or contracts/ already holds. Procedure: references/design.md. -->

## 1. Context
<Up to three paragraphs: what it does, who calls it, what exists, SPEC.md link>

## 2. Components
### <component name in words>
Responsibility: <one sentence>
Owns: <data, secrets, external connections>
Never: <what it must not do>

## 3. Data model
| Table or collection | Key | Fields and types | Indexes and the query each serves | Rows at launch / one year / lucky | Row size | Retention | Personal data | Soft delete |
|---|---|---|---|---|---|---|---|---|

Identifier scheme: <scheme and why>
Platform limits that bite:
| Limit | Value (research: slug) | Design's worst case | Headroom |
|---|---|---|---|

## 4. Contract
<!-- drive:architect specifies the contract here. The `contracts/` package is a wave 0
drive:implementer package; a later contract change is its own package, committed by the orchestrator
as `contract: <change in words>`. -->
Location: contracts/ · source of truth: <schema source | hand-written document>
Emitted document: contracts/<file> · operations: <n>
Emit and drift check: `<emit command> && git diff --exit-code contracts/<file>`
Fixture check: `<command>`
Generate consumers: `<command per consumer>`
Provider contract tests: `<command>` in <runtime> · fuzzer: `<command>`
Consumer contract tests: `<command>` · mock server: `<command>`
Conventions: error shape <shape> · pagination <scheme> · timestamps <format> · versioning <scheme> · idempotency header <name> · auth header <name>

| Operation | Method and path, command, or event | Auth | Idempotency | Fixtures |
|---|---|---|---|---|

## 5. Auth model
Identities: <users, devices, services, and how each authenticates>
Tokens: <lifetimes, rotation, storage>
Rules:
- A caller may <X> a <Y> when <Z>.
Secrets: <names, where each lives, and which the owner must set>
Revocation: <what happens, and how fast>

## 6. Failure semantics
| Write path | Client sees on success | On timeout | On partial failure | Retry safe, and why | Compensation | Left behind if compensation fails | Claim key |
|---|---|---|---|---|---|---|---|

Unknown outcomes: <where intent is recorded before each call, and how an unknown is reconciled>

## 7. Idempotency
| Operation | By nature or key required | Key derived from | Claimed where | Key lifetime | Replay returns | Same key, different payload | Duplicate mid-flight |
|---|---|---|---|---|---|---|---|

## 8. Operations
<!-- Two to four on-call questions, written before any telemetry. Every event, metric, trace, and
alert answers one of them; a signal that answers none is removed. Rules: references/observability.md
section 2. -->
service: <component> · Operational row: <key> | not in scope because <reason>
| question | signal | query that answers it | alert |
|---|---|---|---|
| <what someone asks when it breaks> | <event name or metric> | <exact query or command> | <none, or page or ticket: threshold and its reason> |

Event shape: <fields added to the standard set in references/observability.md section 3>

## 9. Cost envelope
| Assumption | Value | Basis |
|---|---|---|

| Line | Unit price (research: slug, checked) | Launch / month | One year / month | Lucky / month |
|---|---|---|---|---|

Dominant line: <line>
Kill switch: <flag or quota, the metric that trips it, the threshold>

## 10. Environments
| Environment | Resources it owns | How a client selects it | Test data |
|---|---|---|---|

## 11. Deployment
| Environment | Command or trigger | Runs before promotion | Rollout |
|---|---|---|---|

## 12. Rollback
Command: `<command>`
Does not restore: <schema, bindings, secrets, data>
Compatibility rule: <expand and contract: every schema change keeps the previous version working>

## 13. Scaling cliffs
| Order | Limit | Headroom now | Noticed before it hits by |
|---|---|---|---|

## 14. Security boundaries
| Boundary | What crosses it | Who writes the value | Validation | Encryption |
|---|---|---|---|---|

Personal data map: <each personal field with its store and retention>
Deletion path: <every store, cache, backup, and log a deletion request must reach, end to end>

### Threat model
<!-- At M and above when `auth` or the security surface list applies; written by drive:architect in
words with no payloads, before any control or security test, and checked by the design reviewer. Answer
each STRIDE column with the control or `n/a (why)`. Rules: references/security.md section 2. -->
| boundary | writer | assets | S | T | R | I | D | E |
|---|---|---|---|---|---|---|---|---|
| <entry point> | <who can write the value> | <what is at risk> | <control> | <control> | <control> | <control> | <control> | <control> |

#### Abuse cases
- <key> · <boundary> · expected: <what must happen instead> · planned:<path>::<name>

## 15. Frontend structure
Information architecture: <objects users think in and how they nest>

| Screen | Route or entry | Purpose | Operations read and written | States |
|---|---|---|---|---|

Navigation: <graph, deep links, back behaviour, modal versus push>

| State | Truth (server, local, derived) | Lives in | Sync | Conflict rule | Offline |
|---|---|---|---|---|---|

States policy: <what loading, empty, error, offline, and permission-denied each contain>
Scope: <sizes, orientations, color schemes, text sizes in scope>
Visual design: design/DESIGN.md, design/tokens.json, design/screens.yaml

## 16. Claims
- <When X, the system Y.> · key: <slug> · refuting test: planned:<path>::<name> · live: <y | n>

## 17. Research to verify
| Assumption | Cheapest check | Research slug | Status |
|---|---|---|---|

## 18. Decision index
| Decision | Status | Date | Applies to | Record |
|---|---|---|---|---|
| <decision in words> | accepted | <date> | <globs> | #<slug> or <existing ADR path> |

### <decision in words>
Status: proposed | accepted | superseded by <slug> · Date: <YYYY-MM-DD>
Applies to: <globs>
Context: <two or three sentences on the forces>
Options considered:
1. <option>
2. <option>
Decision: <what we will do>
Consequences: good: <...>; bad: <...>
Reversal cost: <what undoing it takes>
Evidence: <slug> (<what it means>)
Option matrix: <.drive/research/options-slug.md, or not an expensive choice>
Reopen if: <copied from each evidence entry's would-change-the-answer line>
Decide by: <milestone or measurement, for proposed records>
DECISIONS.md: <date and slug of the entry that points here, with Undo filled>
