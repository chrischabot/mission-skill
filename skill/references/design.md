# Design

Read this file before the `design` phase of a build, feature, publish, or move run; before writing a
capability map; before changing anything under `contracts/`; and before spawning a design review. It
decides how much design the run needs, what `.drive/DESIGN.md` contains and in what order, how the
contract package becomes the seam parallel makers build against, where decisions are recorded, how an
independent reviewer judges the design, and when the design gate opens. Design documents are the plan,
never the proof: code and tests outrank proof artifacts, which outrank STATUS and STATE, then prose.

## Contents

1. What design is for, and who does it
2. Size the design to the scope
3. The capability map
4. DESIGN.md section order
5. Failure semantics and idempotency
6. The contract package
7. Frontend structure
8. Decision records and the decision index
9. Independent design review
10. The pre-mortem
11. Existing products and migrations
12. Reconciling design with code
13. The design gate
14. Excuses and rebuttals
15. Red flags

## 1. What design is for, and who does it

Design exists so that makers editing one checkout at the same time make the same assumptions about
every shape, error, and ordering they share, and so that later verifiers have concrete statements to
check. An artifact earns its place only when a later agent acts differently because of it, so the
checkable parts (contract package, fixtures, claims, the design contract's per-screen statements)
matter most and prose is kept for reasons. Design is finished when two makers working in parallel
could not reach different assumptions about the same thing, not when every question is answered. A
decision implementation does not need yet becomes a proposed decision record with a "decide by"
trigger (a milestone or a measurement), and the phase moves on. `drive:architect` writes the
capability map, DESIGN.md (including the contract's specification in section 4), and the decision
index, and never edits `contracts/`; the contract package itself is a wave 0 `drive:implementer`
package built from that specification. `drive:designer` writes the design contract under `design/`
for `ui`; `drive:grader` runs the mechanical checks. A fresh `drive:architect` reviews at S and M, and
`drive:auditor` reviews every shape at L and XL. You read verdicts; you never write one.

## 2. Size the design to the scope

| Run | Design output | Review |
|---|---|---|
| XS, any shape | none | none; trait gates still apply |
| `fix`, any size | no DESIGN.md; the diagnosis lives in HUNT.md; an interface or data-shape change gets a decision record and a contract-change step | the verifier reviews the fix; a defect fixed before gets a small design review of its component |
| `feature` at S | no DESIGN.md; the change spec carries a "Design delta": existing endpoints and queries used, the contract delta with fixtures, screens with their states | `drive:grader` consistency check, unless a trigger below applies |
| M, any shape with a design phase | DESIGN.md with changed sections written and the rest marked not applicable with a reason | fresh `drive:architect`; pre-mortem with three causes |
| `build` at L and XL | capability map, then full DESIGN.md | `drive:auditor`; full pre-mortem |
| `feature` or `publish` at L and XL | full DESIGN.md; a capability map when section 3's triggers hold | `drive:auditor`; full pre-mortem |
| `publish` at M and above | mostly frontend: information architecture, content model (page frontmatter schemas, navigation), a performance budget as claims, the hosting decision; backend sections only for forms | fresh `drive:architect` |
| `move/migration`, any size | DESIGN.md for the target; MIGRATION.md for parity and cutover (section 11) | fresh `drive:architect` at S and M, `drive:auditor` at L and XL; full pre-mortem, always |
| `move/refactor`, `move/upgrade` | no new design; read the decision index first; a superseding record for every decision reversed | fresh `drive:architect` at S and M, `drive:auditor` at L and XL |
| `operate`, `report` | none | none |

These apply whatever the size says:

- A new table, collection, or write path requires DESIGN.md sections 3, 6, and 7, and the review runs.
- A new external dependency, or a preview feature on the critical path, requires a decision record
  and an answered RESEARCH.md question before the design relies on it.
- `ui` requires the design contract before any UI code; `auth`, deletion of user data, money, or a
  data migration requires the review.
- More than one maker means the contract package is committed in wave 0 before any maker starts;
  `multi-repo` means the cross-repository contract is pinned with its version before either side changes.

Keep DESIGN.md readable in one sitting, about 2,500 words, and restate nothing SPEC.md or the contract
holds. If DESIGN.md still runs long, split the capability map.

## 3. The capability map

Write `.drive/capability-map.md` from `templates/capability-map.md` before SPEC.md for a build at M and
above, or a feature at L or XL, when the goal bundles capabilities: they have their own users or data,
they could ship and be verified separately, or one could be cut without rewriting the others. When
none holds, write "one capability; no map" on the plan line in GOAL.md.

Name each module in plain words ("billing", "notifications"), give it one responsibility, and list
what it owns: data, secrets, external connections. Dependencies point one way; two modules that need
each other are one module. The contract between two modules lives in the provider's SPEC.md section,
and each module gets its own section of claim headings. The build order becomes the wave order in
`.drive/packages/index.md`, with shared schema and contracts in wave 0, and module names become package
id prefixes. Before the spec, `drive:grader` writes JSON to
`.drive/reviews/<date>-capability-map-<slug>.json` after checking for cycles, a module that cannot be verified without
another's implementation (contract fixtures aside), a contract placed in the consumer, and a resource
owned twice. The architect fixes what it reports.

## 4. DESIGN.md section order

Write `.drive/DESIGN.md` from `templates/DESIGN.md` in this order. When a section does not apply, write
"Not applicable because <reason>"; a missing heading or empty section is a finding, because a checker
cannot tell absence from oversight.

| # | Section | Must contain |
|---|---|---|
| 1 | Context | at most three paragraphs: what the system does, who calls it, what exists; link SPEC.md |
| 2 | Components | per component: one responsibility, what it owns, what it must never do |
| 3 | Data model | keys, types, indexes with the query each serves; rows at launch, one year, and a lucky scale; row size; retention; personal data; soft delete; identifier scheme; every platform limit that bites, with headroom and its RESEARCH.md slug |
| 4 | Contract | the contract's specification, which the wave 0 package builds (section 6): first two or three call sites written as a caller would write them, with the types then reconciled to that usage; location; exact emit, check, and generate commands; per operation the method and path (or command, event), auth, idempotency, request and response fields, error cases, and the fixture cases to write by name; error shape, pagination, timestamps, versioning. Once `contracts/` exists, point at its schemas instead of copying them |
| 5 | Auth model | identities and how each authenticates; token lifetimes and rotation; one rule per resource, "a caller may X a Y when Z"; where secrets live; what revocation does |
| 6 | Failure semantics | section 5's first table |
| 7 | Idempotency | section 5's second table |
| 8 | Operations | event shape with correlation id, hashed user reference, component, outcome, and `trigger`; the on-call table of two to four questions asked when it breaks, with the signal, query, and alert for each; the health endpoint (`references/observability.md` section 7) |
| 9 | Cost envelope | assumptions; unit prices with URLs and checked dates; monthly totals at the three scales; the dominant line; the kill switch that caps it; rough is fine, absent blocks |
| 10 | Environments | names, resources each owns (never shared stores), how a client selects one, where test data lives |
| 11 | Deployment | command or trigger per environment, what runs before promotion, how a version reaches production |
| 12 | Rollback | the command, what it does not restore (schema, bindings, secrets on many platforms), and the rule that forces: expand and contract (`references/shapes/move.md`) |
| 13 | Scaling cliffs | hard limits in the order they will be hit, headroom, and whether the system notices first |
| 14 | Security boundaries | trust boundaries including model output and values written by other processes; validation at each; encryption; the personal-data map and the end-to-end deletion path; a `### Threat model` subsection with the STRIDE table and abuse cases (`references/security.md` section 2) |
| 15 | Frontend structure | section 7, for `ui` |
| 16 | Claims | sentences "when X, the system Y" that exist because of a design choice |
| 17 | Research to verify | each unverified assumption, its cheapest check, its RESEARCH.md slug |
| 18 | Decision index | section 8 |

When design is committed, each section 16 claim becomes a STATUS.md row (key the slug of its words,
`live` fixed at creation, evidence `planned:<path>::<name>`) and a TESTPLAN.md entry.

## 5. Failure semantics and idempotency

Reviewers read failure semantics first and designers most often skip it. Give every write path a row:

| Write path | Client sees on success | On timeout | On partial failure | Retry safe, and why | Compensation | Left behind if compensation fails | Claim key |
|---|---|---|---|---|---|---|---|

A path with no row is not designed. Every call to an external system has three outcomes, success,
failure, and unknown; record the intent durably before calling out so an unknown can be reconciled
rather than guessed. A multi-step write names its transaction mechanism and that mechanism's limits
with a research slug. A scheduled or queued path names how to trigger it now through the system's own
tools and how to replay it. An unknown outcome with no reconciliation path is a blocking finding.

| Operation | By nature or key required | Key derived from | Claimed where | Key lifetime | Replay returns | Same key, different payload | Duplicate mid-flight |
|---|---|---|---|---|---|---|---|

Derive the key from the intent, never the attempt. Claim it with a unique constraint in one operation,
because a read followed by an insert is a race. A replay returns the original response, not a new
success; a reused key with a different payload is refused loudly with a conflict. Decide on purpose
what a duplicate arriving mid-flight receives (a conflict, a bounded wait, or a pending status with a
status URL), and never let it through because the first seems stuck. Keep keys longer than the longest
path that can redeliver a request, including a replayed dead-letter queue, and assume every queue
delivers at least once.

Every contract also follows three boundary rules: one error shape across all operations (the domain
file's, when it names one); validation at every boundary, including third-party responses and model
output; and change by adding, never mutating. A new optional field or operation is additive; removing
a field or changing its meaning is a new version shipped by expand and contract.

## 6. The contract package

The contract is data no implementation owns. Put it at `contracts/`, or where the repository or domain
file already keeps it (`references/domains/cloudflare.md` names `contracts/openapi.json`).

```
contracts/
  <schema source>                    schemas with ids, descriptions, examples
  <operation table>                  per operation: method and path (or command, event), auth, idempotency, request, responses, summary
  fixtures/<operation>/<case>.json   { "request": {...}, "response": { "status": 201, "body": {...} } }
  <emitted document>                 for HTTP, OpenAPI; generated, committed, checked with <emit> && git diff --exit-code
  generated/                         clients and validators generated from the emitted document, committed
```

When the provider's language can emit the document from its schemas, the schemas are the source;
otherwise the hand-written document is, and validators are generated from it. Other seams follow the
same rules: a CLI's contract is its command grammar, help text, and exit codes, tested by golden
outputs; a library's is its public API surface and semver policy, tested by running the documented
examples; events and queues have message schemas with sample messages; a data pipeline has source and
target schemas with sample records and replay semantics. Quote the exact emit, fixture-check, and
generate commands from DESIGN.md section 4 in every brief.

**Contract tests in the real runtime.** A mock that accepts anything proves the client and nothing else. On the provider side, send every
fixture request to the service in its production runtime, or the local runtime the domain file names
as faithful, and assert status, that the body parses with the response schema, and stored state for
stateful cases; then run a schema-driven fuzzer against the running service (for OpenAPI,
`uvx schemathesis run <base-url>/openapi.json --checks all`). On the consumer side, decode every
fixture through the generated client with a fake transport, run two or three flows against a mock
server serving the fixtures, and run one smoke against staging at live proof. Every mock server and
fake transport gets a row in TESTPLAN.md's kindness ledger.

**Ownership and contract changes.** `drive:architect` specifies the contract in DESIGN.md section 4
and never edits `contracts/`. The package is built by a wave 0 `drive:implementer` package
(`references/parallel.md`) that owns `contracts/`: it writes the schemas, the operation table, a
fixture for every named case, the emitted document, and the generated clients. That package's
verifier checks that the emit-and-diff command and the fixture check exit 0 and that every operation
in section 4 appears in the operation table. No other maker edits `contracts/`; a maker that finds a
gap reports `blocked` with the request in words ("add a fixture for an expired session"). A contract
change is its own package: `drive:architect` specifies it in DESIGN.md section 4; a
`drive:implementer` updates schemas and fixtures, emits and runs the fixture check, regenerates every
consumer, and runs provider and consumer contract suites until both are green; you commit it as
`contract: <change in words>`. Add a decision record when an existing consumer's behaviour changes,
use expand and contract when it would break, and re-brief every maker whose package consumes the
changed operations.

## 7. Frontend structure

For `ui`, DESIGN.md section 15 fixes structure, not pixels:

- **Information architecture**: the objects users think in and how they nest, named as the UI names them.
- **Screen inventory**: screen, route or entry point, purpose, contract operations read and written,
  and states; every screen reachable by route or deep link so a reviewer can capture it directly.
- **Navigation**: the graph, deep links, back behaviour, modal versus push.
- **State model**: per piece of state, its truth (server, local, derived), where it lives, how it
  syncs, its conflict rule, and its offline behaviour.
- **States and scope**: what loading, empty, error, offline, and permission-denied each contain; the
  sizes, orientations, color schemes, and text sizes in scope.

Visual direction, tokens, per-screen statements a screenshot or accessibility tree can confirm, and
baselines form the design contract (`design/DESIGN.md`, `design/tokens.json`, `design/screens.yaml`,
`design/baselines/`), written by `drive:designer` before UI code as `references/ui-verification.md`
describes. That file lives with the product; `.drive/DESIGN.md` is the run's system design. Screen
names must match between section 15 and `design/screens.yaml`.

## 8. Decision records and the decision index

A choice that is expensive to reverse (a datastore, auth provider, hosting platform, sync model, public
API style, build versus adopt, or a new core dependency) is settled by the option matrix in
`references/research.md` section 15 before its record is written: frozen criteria and weights, then
two scorers who never see each other's scores, with `drive:auditor` adjudicating any disagreement.
The record's evidence line cites that matrix, and a record for such a choice without one is a
blocking design finding.

Write a record when the design chose between viable options with lasting consequences, puts a preview
feature on the critical path, overrides a domain file's default, accepts a pre-mortem risk, changes a
contract for an existing consumer, drops a behaviour in a migration, or a review finding says
`needs_decision_record`. Skip choices with no real alternative or that a reader could re-derive quickly.

Records live in DESIGN.md section 18 under headings that state the decision in words; the heading's
slug is the key. When the repository already keeps records (`docs/decisions/`, `docs/adr/`, `adr/`,
`doc/architecture/decisions/`), write there in its format and numbering and keep one index line per
record with its path. Either way DECISIONS.md gets one entry per design decision in the standard
grammar of `references/state-files.md` section 8, with `Decision:` as a one-line pointer to the
DESIGN.md record or the repository's record path and `Undo:` filled with its reversal cost, so the
lint accepts it and the report, which is built from DECISIONS.md, lists it. An entry carries status (`proposed`,
`accepted`, `superseded by <slug>`) and date, the globs it applies to, context, options, the decision,
consequences, reversal cost, evidence slugs with their meaning, "reopen if" copied from those entries'
"would change the answer", and "decide by" when proposed. Never edit an accepted record; supersede it.

Records stay alive by being quoted: every implementer brief quotes the entries whose globs overlap its
owned paths, the verifier checks conformance, and `/simplify` and every refactor read the index first.
Do not add imports to the project's CLAUDE.md or rules files unless the project already does so.

## 9. Independent design review

Before a reviewer spends judgment, `drive:grader` writes JSON to
`.drive/reviews/<date>-design-consistency-<slug>.json` listing operations named elsewhere in DESIGN.md
and absent from section 4, and the reverse; when `contracts/` already exists, operations absent from
its operation table and fixtures failing validation; section 15 screens missing from
`design/screens.yaml` or missing a state, claims with no planned test, cited decision or research slugs
that are absent, unverified, or stale, and sections missing or marked not applicable without a reason.
The architect fixes every item before the review.

Build the reviewer's handoff from files with `templates/handoff.md`: the repository root as an
absolute path, SPEC.md, the capability map, DESIGN.md, `contracts/` when it exists, the design contract, RESEARCH.md, `how-it-works.md` when present, shape and
size. Never pass the architect's summary or your own opinion. Tell the reviewer to report every finding
with severity and confidence; you filter afterwards. Each dimension scores 0 (absent or wrong), 1
(present with gaps), or 2 (sound) and cites the section or `file:line` judged; no pointer means 0.

| Dimension | Question |
|---|---|
| Simplicity | Could a component, table, or dependency go without losing a SPEC.md claim? |
| Boring technology | Is every non-default or preview choice justified by a decision record? |
| Single source of truth | Does every important fact have one owner, with copies regenerated, not edited? |
| Failure handling | Does every write path have a row with timeouts, retry safety, and compensation? |
| Security boundaries | Are boundaries drawn, inputs validated at each, authorization per resource, personal data mapped to deletion? |
| Scaling cliffs | Are limits listed with headroom, and will the system notice before the first? |
| Vendor lock-in | Is the cost of leaving each vendor stated and deliberate? |
| Testability | Does every claim have a refuting test in a production-faithful harness, and do the seams exist? |
| Cost | Is the envelope present, with assumptions, a dominant line, and a kill switch? |
| Operability | Can someone find what broke from the events and the stated questions alone? |
| Data lifecycle | Are retention, deletion, backup, restore, and export stated? |
| Interface depth | Does each module hide more than its interface costs to learn, and does each representation decision live in one module? |

Interface depth scores down for four red flags, which are John Ousterhout's from *A Philosophy of
Software Design*: a shallow module, whose callers coordinate several calls for one operation or whose
options expose its internal stages; information leakage, where one representation, policy, or wire
format appears in more than one module; temporal decomposition, where modules follow execution order
(load, validate, save) rather than the knowledge they own; and a pass-through method that forwards its
arguments unchanged. A deep module is not a deep call chain, which spreads understanding across layers.
At L and above, a design decision that crosses a module or service boundary records in section 18 at
least one structurally different alternative, not a variant of the chosen shape, and why it lost; the
reviewer checks it under Simplicity.

A 0 on failure handling, security boundaries, or testability blocks, as does an absent cost envelope
when the system pays per use. A 0 on interface depth is `should_fix`, never blocking.

**Verdict file.** Every round, a scoped re-check included, writes
`.drive/reviews/<date>-design-review-r<n>.md` from `templates/review.md`, opening with `verdict: not
ready` when the scored verdict below is `block` and `verdict: ready` otherwise, then `round: <n>/<bound>`.
A combined round writes `.drive/reviews/<date>-test-plan-review-r<n>.md` beside it with the test plan's
own verdict and findings. `drive:auditor` also writes the scored document below to
`.drive/reviews/<date>-design-<slug>.json`. `drive:architect`, reviewing at S and M, puts the same
document inside a `json` fence in the review file's Notes, because the guard lets only a reviewing
agent (verifier, grader, UI reviewer, auditor, or security reviewer) write a JSON file under
`.drive/reviews/`. The scored document, or the review file holding it, is the design gate's `review:`
evidence.

```json
{ "verdict": "pass | pass-with-changes | block", "reviewer": "drive:auditor (fable)",
  "inputs": [".drive/DESIGN.md@<sha>", "contracts/@<sha> when it exists"],
  "scores": { "simplicity": 2, "boring": 1, "single_source": 2, "failure": 1, "security": 2, "scaling": 2,
              "lockin": 2, "testability": 2, "cost": 1, "operability": 1, "data": 2, "depth": 2 },
  "findings": [{ "severity": "blocking | should_fix | note", "confidence": "25 | 50 | 75 | 100",
                 "dimension": "failure", "where": ".drive/DESIGN.md#6-failure-semantics", "claim": "<what is wrong>",
                 "evidence": "<what shows it>", "fix": "<change>", "needs_decision_record": false }],
  "premortem": [{ "cause": "", "design_element": "", "detection": "", "already_detected": false,
                  "mitigation": "", "cost": "", "recommendation": "mitigate | accept | decision record", "rank": 1 }],
  "unverified_assumptions": [], "rubric_gap": [] }
```

`block` when any blocking zero or blocking finding exists; `pass-with-changes` when only should_fix
findings remain; otherwise `pass`. `rubric_gap` names where the rubric did not fit the deliverable,
which is different from work not done.

**Rounds and disputes.** The architect revises against blocking findings, and a fresh reviewer runs
each later round with the previous gaps in its handoff. At S and M the design is reviewed together with
the test plan in one full round plus at most one scoped re-check of that round's blocking findings; at
L and XL `drive:auditor` runs up to three full rounds. `references/verification.md` section 6 holds the
bounds and what a re-check reads. A disputed blocking finding goes once to a fresh
`drive:auditor` with `.drive/reviews/<date>-dispute-<key>.md`; it rules `defect`, `not_a_defect`, or
`rubric_ambiguous`, and you write the DECISIONS.md entry from the ruling. A block still open at the
bound, after the re-check at S and M or after round three at L and XL, becomes a proposed decision
record holding both positions; the build proceeds on the reviewer's position and the open gap goes into
STATE.md and the report. A review with no findings on a design at M or above is
itself a finding: run one fresh reviewer told to name the three weakest points with evidence. For XL
builds and migrations, competing designs are judged as `references/parallel.md` section 12 describes.

## 10. The pre-mortem

The reviewer runs it after scoring, so invented failures do not color the scores. A reviewer asked
whether a design is good tends to praise it; one asked why it failed has to name mechanisms.

1. Write one paragraph dated six months ahead stating that the project failed, was rolled back, or
   sits unused, whichever is most plausible for this shape.
2. List three causes at M, and at least six at L, XL, and for any migration, drawn from data loss,
   cost, a platform limit, auth or security, user abandonment, a vendor or dependency change, an
   operational blind spot, and drift between two sides of a contract.
3. For each, name the design element that permits it, how it would be detected and whether the design
   already detects it, the mitigation and its cost, and a recommendation: mitigate, accept, or record.
4. Discard any cause that names no design element or no detection mechanism.
5. Rank by probability times damage and resolve the top three before the gate: a mitigation in
   DESIGN.md with a claim and a planned test, or a record titled "Accepted risk: <words>".

## 11. Existing products and migrations

**A feature on an existing product: extract, do not reinvent.** Read `.drive/how-it-works.md` and the existing decision records first. The change design names, with
paths, the components, endpoints, queries, and UI components it extends; every new query with its index
and read cost; and the contract delta with fixtures. The design contract is extracted from the existing
design system and matched. Never add a second architecture, design system, error shape, HTTP client, or
state store. A decision record is needed only for a new library or pattern, and a near-duplicate of an
existing helper in the blast radius is a design finding.

**A migration: parity and cutover.** A migration's design is a parity-and-cutover plan. MIGRATION.md holds the charter, invariants, consumer
inventory, parity, stages, and undo ledger; DESIGN.md holds the target placement and contract. Together
they cover a behaviour inventory from tests, logs over a full traffic cycle, and live traffic; the
legacy contract frozen with golden fixtures; the target contract; a shadow or dual run with a
comparison harness; the cutover switch and the switch back; data migration and reconciliation; expand
and contract for every schema change; a decommission checklist; and a decision record for every
behaviour deliberately dropped. The design reviewer (`drive:auditor` at L and XL) always runs the full
pre-mortem, because migration
failures hide in headers, timeouts, and defaults the old system normalized without saying so.

## 12. Reconciling design with code

DESIGN.md's header carries `reconciled at: <sha>`. After the last build wave (at `integrate` for a
build) and before `docs` for every shape, `drive:grader` compares DESIGN.md sections 2 to 7, 15, and 18
with `contracts/`, the schema or migrations, and the code, listing each difference with paths. Where the
code is right, the architect corrects the document; where the code breaks an accepted decision or a
claim, the difference is a gap for the verifier, never a document edit. Then update `reconciled at`.
The contract drift check runs before every integration commit, and a failure stops the commit.

Three signs during the build mean the design is wrong rather than a package: the same workaround shape
recurring across packages, types that need casts or optional fields that are always set in practice,
and callers that must know an abstraction's internal rules to use it. Record each against its decision
in section 18 and treat it as `references/verification.md` section 6 treats the same defect class
confirmed twice.

## 13. The design gate

The reviewer checks the design gate, never you. It opens when all of these hold:

1. Every DESIGN.md section is written or marked not applicable with a reason.
2. Section 4 names every operation with its request, responses, error cases, and fixture cases, and
   the consistency check lists nothing open. When `contracts/` already exists (an existing product),
   the emit-and-diff command and the fixture check also exit 0 at the committed sha; for new
   contracts those two checks are the wave 0 contract package's exit.
3. The latest verdict is `pass` or `pass-with-changes`; every blocking finding is resolved in DESIGN.md
   or a decision record; the pre-mortem is non-empty and its top three are resolved.
4. The decision index holds every non-default choice and accepted risk, each with a DECISIONS.md line.
5. Every section 16 claim has a STATUS row with `planned:` evidence and a TESTPLAN.md entry, and every
   section 17 item has a RESEARCH.md question with a status.
6. For `ui`, the design contract exists and passes the checks in `references/ui-verification.md`.
7. `drive.py lint --gate design` passes, and DESIGN.md and the review are committed.

## 14. Excuses and rebuttals

| Excuse | Why it fails |
|---|---|
| "The makers can agree on shapes as they go." | They cannot see each other; each invents a shape and integration becomes a negotiation. |
| "Failure semantics can wait until the code exists." | Retry safety and compensation decide the schema and contract; found later, they force a rewrite. |
| "A mock server is enough to test the contract." | It accepts whatever the schema allows and proves only the client. |
| "This small contract edit is obviously fine." | An unregenerated consumer fails a day later; the drift check exists because obvious edits break. |
| "The cost envelope is premature." | Rough numbers change designs; absence hides the line that dominates. |
| "It is an existing product, so no design is needed." | Without extraction the feature brings a second pattern, and every later reader inherits both. |

## 15. Red flags

- A DESIGN.md heading with nothing under it, or a section dropped instead of marked not applicable.
- A write path in the operation table with no failure-semantics row.
- A diff touching `contracts/` outside a contract package, an architect editing `contracts/`, or
  generated consumer code older than the emitted document.
- Contract tests that only run against a mock server or an in-process stub.
- A verdict file written, edited, or summarized by the orchestrator or the architect.
- A review with no findings on a design at M or above, or pre-mortem causes that name no design element.
- A decision record edited after acceptance, or a refactor that reverses one without superseding it.
- A limit or price in DESIGN.md with no RESEARCH.md slug, or a stale one.
- `reconciled at` older than the last build wave when the docs phase starts.
