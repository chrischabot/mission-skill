# Specification & design

Turns a one-line direction into a contract: charter, assumptions, requirements with IDs and oracles, a script-validated
registry, design docs that record trade-offs, and a capped adversarial review. Names follow
`references/conventions.md`; if this file disagrees with it, conventions wins.

## When to load

- Phase 0 Intake: after classification, to run exploration, assumptions, questions and the charter or task card.
- Phase 2 Spec and Phase 3 Design: to write SPEC.md, requirements.yaml, design docs, ADRs, and to run the review gate.
- Any later phase when reality contradicts the spec (incident, refuted assumption, design change, contract change).
- Not needed for S missions beyond the "Intake" and "S" rows below (task card only).

Templates (copied into `.mission/` by `scripts/init-mission.sh`):

| Artefact | Template | Target path |
|---|---|---|
| Task card (S) | `templates/TASK-CARD.md` | PR description, or `.mission/TASK-CARD.md` if multi-session |
| Charter (M+) | `templates/CHARTER.md` | `.mission/CHARTER.md` |
| Assumptions | `templates/ASSUMPTIONS.md` | `.mission/ASSUMPTIONS.md` |
| Spec | `templates/SPEC.md` | `.mission/SPEC.md` |
| Bugfix spec (M bugs) | `templates/BUGFIX-SPEC.md` | `.mission/SPEC.md` |
| Registry | `templates/requirements.yaml` | `.mission/requirements.yaml` |
| Backend design | `templates/design/BACKEND.md` | `.mission/design/BACKEND.md` |
| Frontend design | `templates/design/FRONTEND.md` | `.mission/design/FRONTEND.md` |
| Screen spec | `templates/design/SCREEN.md` | `.mission/design/screens/SCR-NNN.md` |
| ADR | `templates/design/ADR.md` | `.mission/design/adr/ADR-NNN.md` |
| Migration plan | `templates/design/MIGRATION.md` | `.mission/design/MIGRATION.md` |
| Website brief | `templates/design/WEBSITE-BRIEF.md` | `.mission/design/WEBSITE-BRIEF.md` |
| Review rubric + reviewer prompt | `templates/spec-review-rubric.md` | brief for the reviewer; output `reviews/spec-findings.md` |
| Registry validator | `scripts/validate-registry.py` | `.mission/bin/validate-registry.py` (copied by init); run from the repo root |

## Core rules

MUST / SHOULD / MAY per conventions §9. Rule IDs keep the source report's `SPEC-R` prefix.

### Classification and depth

- **SPEC-R01** MUST classify the mission (shape + class from the four scores + traits; conventions §5 and
  `references/shapes-and-scope.md`) before writing any spec artefact. Do not re-derive the formula here. Risk traits add
  requirements and review lenses, never document depth.
- **SPEC-R02** Scores, class and justification live in `.mission/PROFILE.yaml` + the STATUS header (for S: the profile
  block of the task card). The charter header repeats class and shape only. Revise upward at any gate; downward only
  with a D-entry.
- **SPEC-R03** Artefact depth MUST follow the class table in "Scale by class". Producing more than the class requires is
  a rubric R11 finding, not diligence.
- **SPEC-R03a** IF any phase discovers higher scores or a new trait THEN re-classify (shapes-and-scope §2 step 7) and
  produce the missing artefacts for that slice before continuing it.

### Intake

- **SPEC-R04** MUST explore before drafting. Brownfield: read-only repo sweep (conventions, existing spec/ID scheme,
  tests and citation style, tokens/components, owners, build commands) → scout digests with `path:line` pointers in
  `.mission/lanes/<lane-id>/digest.md`, merged by the orchestrator into `.mission/CONTEXT.md` (obligation EC-1). Novel
  platform/domain: web research only for unknowns that change the design (references/research.md), findings with URLs.
- **SPEC-R05** MUST fill every gap with a labelled assumption in ASSUMPTIONS.md: `A-NN`, statement, reversal cost
  L/M/H, confirmation state, how it will be verified, what it affects. Never state an assumption as fact.
- **SPEC-R06** MUST ask the human only about unknowns with HIGH reversal cost: platform, data ownership/retention,
  money/spend ceilings, irreversible external effects (publishing, payments, deletion, messaging), taste anchors,
  "what must not change" (the same set as the plan-forking fields of shapes-and-scope §2 step 6). At most 3 questions
  per round, at most 2 rounds. Each question is multiple-choice with a ★ recommended default and a one-line consequence
  per option. Low/medium-cost gaps are never asked.
- **SPEC-R07** Headless run, or no answer: apply the ★ defaults, mark them `ASSUMED (unconfirmed)`, list them under
  "Headless defaults applied", continue. MUST NOT block on them unless a STOP condition applies.
- **SPEC-R08** Intake MUST end in files (charter or task card, assumptions), not in conversation state. Implementation
  never starts from the raw prompt on M+ work.

### Charter

- **SPEC-R09** The charter MUST contain: outcome (no technology), goals, non-goals that are plausible goals
  deliberately excluded, users/stakeholders (L/XL), constraints incl. "must not change", success metrics as `OUT-NNN`
  with threshold + measurement method + automated/live, assumption index, questions asked (L/XL), risks (L/XL), STOP
  conditions, definition of done split product / engineering / operational, artefact plan with review-round cap.
- **SPEC-R10** STOP conditions MUST include the generic four (dual ownership of a record or side effect; a test that can
  pass without observing its outcome; deleting/overwriting unclassified user data or spending/publishing beyond
  approval; a decision contradicting a non-goal or constraint) plus shape-specific stops.
- **SPEC-R11** Outcomes that cannot be simulated honestly (real users, real mornings, production traffic) MUST be
  registered `live-only` and stay `PENDING-LIVE` until the live check actually runs. Never fake them with a simulation.
- **SPEC-R12** Charter length: M ≤1 page (◆ sections only), L/XL ≤4 pages. On L/XL, human sign-off of the charter +
  spec is a checkpoint; in autonomous mode notify instead of waiting and log a D-entry.

### Spec

- **SPEC-R13** Every normative statement MUST have a stable ID (conventions §3): `<DOMAIN>-<NNN>` on L/XL (domain 2–6
  capitals or digits starting with a letter, e.g. `API-012`, `A11Y-002`), `REQ-NNN` on M, `OUT-NNN` for outcomes,
  `BUG-<n>-C1/E1/U1` for bugfix clauses. IDs are never renumbered or reused; removed ones stay in the registry with
  `status: withdrawn`. Test-architecture requirements use a `TEST` domain. Split any independently testable behaviour
  found in prose into its own ID before coding.
- **SPEC-R14** Normative strength uses BCP 14 capitals only. Behavioural requirements SHOULD use EARS: ubiquitous
  ("The <system> SHALL …"), state ("While …"), event ("When …"), optional ("Where …"), unwanted ("If …, then …"),
  complex (combinations). One system name, zero-or-one trigger, one or more responses.
- **SPEC-R15** Every external boundary (network, provider, storage, user input, permission) MUST have ≥1
  unwanted-behaviour requirement (`If <condition>, then the <system> SHALL …`) with a named failure fixture, listed in
  SPEC §6.
- **SPEC-R16** Every requirement MUST name its oracle kind (`unit | property | contract | integration | scenario | e2e |
  visual | a11y | live | human | review`) and a falsifiable criterion. Unmeasurable adjectives (fast, intuitive, robust,
  clean, simple, modern, seamless, scalable, large, many) MUST NOT appear without a threshold or rubric reference.
- **SPEC-R17** User journeys MUST be prioritised P1..Pn, each independently testable and demonstrable. P1 journeys MUST
  carry Given/When/Then scenarios that become scenario or e2e tests. Given/When/Then is not used for every requirement.
- **SPEC-R18** Unknowns surviving intake MUST appear inline as `[NEEDS CLARIFICATION: question · owner · default ·
  blocks]`. A spec MUST NOT pass review with such a marker on a P1 requirement or journey.
- **SPEC-R19** A test MAY cover several IDs. An ID naming a specific contract MUST NOT rely solely on one broad e2e test.
- **SPEC-R20** Spec-anchored, not spec-as-source: a behaviour change MUST update SPEC.md, requirements.yaml and the
  change log in the same change set; a refuted assumption MUST update the charter/spec and ASSUMPTIONS.md; an incident
  SHOULD add or amend a requirement plus a recurrence fixture. Never regenerate code from the spec.
- **SPEC-R21** Grader conditions derived from the spec MUST state the command whose output proves them, the frozen
  surfaces that must not change, and a turn/time bound. `/goal` is never a gate; gates come from verifiers and `check.sh`.

### Registry

- **SPEC-R22** The registry MUST be validated by script, never by a model: `python3 .mission/bin/validate-registry.py
  --registry .mission/requirements.yaml --tests <test dirs> [--spec .mission/SPEC.md]`. Exit 1 blocks the spec gate
  and every later gate. The script fails on: duplicate or malformed IDs; missing text/owner/status; missing
  `oracle_kind`; status `implemented`/`verified` without `oracles`; oracle paths that don't exist; implemented oracles
  that don't cite `@req:<ID>`; tests citing unknown, malformed or withdrawn IDs; `--spec` mismatches.
- **SPEC-R23** Citation is bidirectional: the registry points at the test (`path::name`), and the test cites the ID
  (`@req:<ID>` in its name or annotation). Add an oracle reference only once the file exists.
- **SPEC-R24** Status promotion: makers MAY set `implemented`; only a verifier sets `verified` after the gate. Demoting an
  entry back to `planned` with a note naming the gap is the gate working, not a regression.
- **SPEC-R25** M: hand-written registry. L/XL SHOULD keep the same file but MAY split authored text (SPEC.md) from
  curation (status, oracles) if the repo already does; a generated registry MUST still pass the validator. Brownfield
  repos with an existing registry scheme: extend it, don't create a parallel one.
- **SPEC-R26** Keep the registry inside the documented YAML subset (validator `--help`) so it validates without PyYAML.

### Design

- **SPEC-R27** A design doc MUST include context & scope, goals/non-goals (link the charter), the design, ≥2 genuine
  alternatives with trade-offs, cross-cutting concerns (security, privacy, observability, cost) and failure modes. No
  genuine alternatives → no design doc; write the task list in PLAN.md. Beyond ~20 pages → split into sub-designs.
- **SPEC-R28** Choices expensive to reverse (datastore, auth model, API style, client platform, sync model, public URL
  structure, token set, cutover order) MUST get an ADR (Nygard: context, decision, alternatives, consequences, reversal
  cost, revisit trigger) plus a D-entry. Superseding an ADR creates a new ADR.
- **SPEC-R29** Backend designs MUST: list the platform limits that bound the design with source URLs and access dates;
  give each entity, schedule and external side effect exactly one owning component; describe every multi-step
  lifecycle as a state machine with rejected transitions; define idempotency and retry semantics (policy, backoff, max
  attempts, fallback) for every external call; link the contract file instead of pasting schemas.
- **SPEC-R30** Frontend designs MUST include an IA tree with screen IDs, P1 flows with failure branches, a screen
  inventory, a single token source (roles, not raw values), components, copy rules, accessibility requirements with
  IDs and performance budgets. Each new or changed screen MUST get `design/screens/SCR-NNN.md` with regions + layout
  assertions, a state matrix (populated, empty, loading, error, partial/offline, permission-denied where relevant,
  largest text size, dark mode where supported) and verification hooks. Accessibility minimums follow the platform: HIG
  on Apple platforms (Dynamic Type to the largest accessibility size, text enlargeable ≥200%), WCAG 2.2 AA on the web.
- **SPEC-R31** Screen specs are written as checkable assertions (region order, alignment relations, token references,
  minimum target sizes, truncation/overlap rules), never as adjectives. They feed `references/frontend-verification.md`.
- **SPEC-R32** Tokens live in the target repo, never in the global skill. `design/tokens.md` names the token source
  (repo DTCG file or existing theme) and holds the role table only if the repo has none.

### Review and hand-off

- **SPEC-R33** Before implementation of M+ work, a fresh-context reviewer (`mission-critic`) MUST review charter +
  assumptions + spec + registry (+ designs) against `templates/spec-review-rubric.md` (R1–R12). The reviewer gets files
  and the rubric only, never the author's transcript.
- **SPEC-R34** Findings MUST cite section/ID, quote, and a concrete failure scenario; without a scenario they are
  `question` and cannot block. Candidate blocker/major findings are refuted by `mission-verifier` before they block.
  Dispositions: FIXED / REFUTED / RESIDUAL / DEFERRED / CONTESTED.
- **SPEC-R35** Round caps: S = 0, M = 1, L/XL = 2; stop on severity, not finding count; round 2 re-reviews only changed
  sections and dependents. The gate passes when no CONFIRMED blocker is open and every CONFIRMED major is FIXED,
  RESIDUAL or DEFERRED. At the cap with an open blocker: CONTESTED → orchestrator adjudication at high effort with a
  D-entry, or the human queue on L/XL. No extra round without a D-entry; XL MAY run a third round only for a blocker in
  a section newly written in round 2 (shapes-and-scope §3).
- **SPEC-R36** After the gate, implementation MUST start in a fresh context loaded from files (CONTEXT.md, charter,
  spec, registry, designs, CONTRACTS.md). The intake conversation is never carried into build briefs.

## Procedure

### Phase 0 — Intake

1. Classify (SPEC-R01) and pick the shape. Record in PROFILE.yaml + STATUS header. S → write the task card
   (`templates/TASK-CARD.md`), make its acceptance line name the command, and go to Build. Stop reading here.
2. Explore (SPEC-R04). Brief `mission-scout` sweeps per area with the discovery brief below; spot-check 3 random
   pointers from each digest. Any miss → rerun that area with `mission-verifier` (read-only, high effort).
3. Draft ASSUMPTIONS.md: one row per gap. Rate reversal cost with the rubric in the template.
4. Select questions: take HIGH-cost rows only, rank by (reversal cost × likelihood the default is wrong), keep ≤3.
   Write each as multiple choice with ★ default and one-line consequences. Interactive → ask once, wait; answers go
   into the rows and the charter §8. Headless → apply defaults (SPEC-R07). A second round is allowed only if round 1
   answers created new HIGH-cost unknowns.
5. Write CHARTER.md (◆ sections for M). Add shape-specific STOP conditions from "Shape conditionals".
6. Write the artefact plan (charter §12) from "Scale by class" + shape conditionals. Record the review cap.

Discovery brief (paste into the scout brief):

```text
Role: discovery sweeper (read-only). Area: <path or subsystem>.
Produce a conventions digest with path:line pointers for: existing spec/requirement IDs and registry files; test
framework, naming and citation style; design tokens/components; routing/IA; data stores and owners; external
integrations; build/test/deploy commands; anything contradicting assumptions A-*. Facts only, each with a pointer.
Label inferences. ≤400 lines. No recommendations. Write to .mission/lanes/<lane-id>/digest.md.
```

### Phase 2 — Spec

7. Brief the spec author (see "Model routing") with charter, assumptions, digests and `templates/SPEC.md` (or
   `BUGFIX-SPEC.md`). Output: SPEC.md + requirements.yaml with every ID `status: planned` and `oracle_kind` set; the
   template's example entries (API-001..003) are replaced, not kept.
8. Run `python3 .mission/bin/validate-registry.py --registry .mission/requirements.yaml --spec .mission/SPEC.md`
   via `mission-checker`; save output to `.mission/logs/validate-registry-spec.txt`. Exit 1 → author fixes, rerun.
9. Self-check before review (orchestrator, cheap): every boundary in SPEC §6 has an unwanted-behaviour ID; no banned
   adjective without threshold (`grep -nEi 'fast|intuitive|robust|clean|seamless|scalable' .mission/SPEC.md`); no
   `[NEEDS CLARIFICATION` on P1. The spec feeds acceptance.json (AC-NNN citing IDs) and TEST-PLAN.md
   (references/testing.md).

### Phase 3 — Design

10. Brief designers per the artefact plan from `.mission/design/templates/` (copied by init at L/XL; M copies from the
    skill): BACKEND.md, FRONTEND.md + screens, MIGRATION.md or WEBSITE-BRIEF.md, ADRs.
    Contract decisions that cross lanes go to CONTRACTS.md before any parallel writing (references/swarms.md).
11. Designs that change a requirement MUST edit SPEC.md + registry in the same change (SPEC-R20); rerun the validator.

### Review gates (spec review ends Phase 2; design review ends Phase 3)

Same rubric, same caps, counted per gate. Spec review focuses R1–R7, R11 over charter + assumptions + spec + registry;
design review focuses R8–R12 over designs + any spec edits. M with designs ≤2 pages MAY run one combined review after
Phase 3. Output: `reviews/spec-findings.md` / `reviews/design-findings.md` and matching `-disposition.md` files.

12. Pick lenses (rubric template maps lenses → items): M = 1 lens (ambiguity & testability, or the lens matching the
    riskiest trait); L = 2–3 lenses in parallel; XL = 3 lenses incl. one on a different model (see "Model routing").
    Security & privacy lens is mandatory when PII, auth, money, secrets or provider accounts are in scope.
13. Brief each reviewer with `templates/spec-review-rubric.md` filled in (files + rubric + validator log only).
14. Refute candidate blocker/major findings (`mission-verifier`, not the raising reviewer). Write dispositions to
    `reviews/<spec|design>-disposition.md`. Fix CONFIRMED blockers/majors; minors/nits MAY be batched or deferred.
15. Round 2 (L/XL only): re-review changed sections and dependents. Apply the gate rule (SPEC-R35). Record the gate
    state in STATUS.md with evidence (findings + disposition paths, validator exit code).
16. L/XL: queue human sign-off (charter + spec summary, open ASSUMED rows); in autonomous mode notify and log a D-entry.
17. Hand off: write/refresh CONTEXT.md pointers; start build briefs in fresh contexts from files (SPEC-R36).

### Any phase — change control

18. Incident, refuted assumption, contract change → amend SPEC.md + registry + change log in the same change set;
    withdraw IDs rather than delete; rerun the validator with `--tests`; re-classify if scores or traits changed.

## Scale by class (S/M/L/XL)

| Class | Intake | Charter / card | Spec & IDs | Registry | Designs | Review cap | Human |
|---|---|---|---|---|---|---|---|
| S | orchestrator inline; no scouts unless the file is unknown | TASK-CARD (≤2 lines per field) | none; acceptance line names the command | none (repo registry: add `@req` citation if one exists) | none | 0 | none |
| M | 1 scout sweep if brownfield; ≤3 questions, ≤2 rounds | charter ◆ sections, ≤1 page | mini spec ≤2 pages, `REQ-NNN`, P1 G/W/T | hand-written, validated | only what the change touches; ADR only for irreversible choices | 1 | only STOP/irreversible |
| L | fan-out scouts per area; research for design-changing unknowns | full charter ≤4 pages | domain IDs, all SPEC sections | validated with `--spec` and `--tests` at every gate | BACKEND and/or FRONTEND + screens, ADRs | 2 | charter+spec sign-off (autonomous: notify + D-entry) |
| XL | as L + milestone M0 contract/walking skeleton | as L + milestone exit gates | as L; per-milestone delta sections | as L; MAY generate from curation; validator in CI | as L + MIGRATION/WEBSITE-BRIEF where relevant, sub-designs beyond ~20 pages | 2 + consolidated cross-milestone review after integration (references/review.md); third round only per SPEC-R35 | as L |

Sizing guards: IF unsure between two classes THEN use the smaller for document ceremony and the larger for verification
strength (conventions §5). IF a bug hunt is long THEN investigation depth still does not raise spec depth.

## Shape conditionals

Shape definitions and trait → obligation mapping: `references/shapes-and-scope.md`. Below: what each shape adds to the
spec and design artefacts.

### GRN — greenfield multi-platform app (e.g. SwiftUI iOS + Cloudflare backend)

- IF greenfield product THEN never S (conventions §5); multi-platform is typically XL. Order: charter → spec → BACKEND →
  FRONTEND + screens → ADRs → review → plan.
- IF >1 client platform, or any client + backend THEN SPEC MUST define the API contract as its own domain (`API-NNN`)
  with one schema file (OpenAPI or a typed contracts package) that both sides test against; it goes to CONTRACTS.md and
  milestone M0 (walking skeleton) proves it end to end (obligations MP-1/MP-2). Every endpoint gets a request/response
  schema reference and ≥1 unwanted-behaviour requirement (BA-1).
- IF the backend is Cloudflare THEN BACKEND §5 MUST carry the limits table (D1 10 GB per database, not raisable;
  single-threaded per database; 1,000 queries per Worker invocation on Paid; 100 bound parameters per query; store fit
  KV / R2 / Durable Objects / D1 / Queues) with source URLs, plus a per-entity store ownership table (§6). Blobs in R2
  with metadata in D1; Durable Objects only for coordination or strict ordering. Re-verify limits before relying.
- IF the client is SwiftUI THEN FRONTEND §1 MUST cite HIG conventions (navigation pattern, Dynamic Type ≥200% /
  largest accessibility size, Accessibility Inspector audit) and every screen's state matrix MUST include light, dark
  and largest-text rows.
- IF users upload personal images (e.g. outfit photos) THEN the charter MUST name retention and deletion requirements
  (constraint + `PRIV-NNN` IDs), BACKEND §10 MUST include a privacy section (PII inventory, deletion path and deadline,
  access control on objects), and the security & privacy review lens is mandatory.
- IF the product has a taste component THEN one of the ≤3 intake questions MUST ask for 2–3 reference apps as taste
  anchors (headless default: 2–3 platform-exemplary apps named in ASSUMPTIONS.md), and tokens MUST be defined before the
  first screen is built.

### BUG — bug fix

- IF S bug THEN the bug variant of TASK-CARD.md (repro, Current / Expected / Unchanged, test first). IF M bug THEN
  BUGFIX-SPEC.md as SPEC.md with `BUG-<n>-C/E/U` IDs in the registry.
- IF no reliable repro THEN the first deliverable is a repro or a statistical repro with a frequency
  (references/debugging.md); spec review is skipped until the repro exists.
- ALWAYS add at least one Unchanged clause per adjacent behaviour a narrow fix could break; the fix MUST NOT weaken
  those oracles.
- IF the fix changes a public contract THEN add trait `published_api` (PA-1..3) and write a delta SPEC section + ADR.
- ALWAYS register the regression oracle (registry entry or test header `@req:BUG-<n>-E1`).

### FEA — feature in an existing product (e.g. a new dashboard)

- IF brownfield THEN discovery MUST precede the charter: existing spec/ID scheme, tokens/components, routing/IA, data
  sources, test conventions and citation style, owners → conventions digest with `path:line` pointers.
- IF the repo already has a spec/registry/ID scheme THEN extend it (same prefixes, same registry file, its citation
  style mapped to `@req:<ID>` in CONTEXT.md). Create the `.mission/` scheme only when absent. Never run two registries.
- IF the feature adds or changes screens THEN write screen specs only for new or changed screens; reuse existing
  tokens and components; a new token needs a D-entry (ADR-lite).
- IF the feature shows metrics (dashboard) THEN each metric MUST have a `METRIC-NNN` definition requirement: source,
  formula, unit, time zone, aggregation window, refresh cadence, empty and partial-data semantics, and an oracle fixture
  with known expected values. Metric-definition ambiguity is this shape's most common defect class (inference).

### MIG — service migration / extraction

- IF migration THEN usual class L–XL (shapes-and-scope §6); write `design/MIGRATION.md` at M+: current-state map,
  behaviour inventory, target, seams, import / do-not-import, parity criteria, cutover, rollback.
- IF the old system has undocumented behaviour THEN discovery MUST produce a behaviour inventory with each item
  classified keep / drop / change (kept → `PAR-NNN`, changed → `MIG-NNN`). Never specify "same as before".
- IF traffic is live THEN parity MUST be shown by shadow or replay comparison with thresholds before cutover, and
  cutover MUST disable the legacy owner of each side effect before enabling the new owner. Import runs twice ⇒ identical
  canonical result.
- ALWAYS add STOP: "old and new both own an external side effect without a suppression fence". Promote, canary and
  retire steps are human checkpoints (irreversible / externally visible).
- IF secrets, keys or provider accounts move THEN the security lens is mandatory in spec and design review.

### WEB — research + marketing website with blog/docs

- IF market research is in scope THEN SPEC starts with research questions (`Q-NN`, references/research.md) and every
  claim reaching the site MUST be a `CLAIM-NNN` requirement (kind `content-claim`) bound to `S-NNN` sources with URL +
  access date.
- IF a website is in scope THEN write `design/WEBSITE-BRIEF.md`: audiences/JTBD, positioning, messaging hierarchy
  (message → proof → source), sitemap ≤3 levels, page inventory, blog and docs rules, SEO/metadata, analytics events;
  page templates get `SCR-NNN` screen specs; accessibility WCAG 2.2 AA; public URL structure gets an ADR.
- IF the site has docs THEN run a synthetic tree test (labelled synthetic): for the top 5 tasks the expected path is
  ≤3 clicks and labels are unambiguous.
- IF the site makes comparative claims THEN the charter STOP list MUST include "unsourced comparative claim".
- ALWAYS: publishing and DNS changes are human checkpoints.

### Other shapes (RSR spike, PRF performance, docs-only WEB)

- IF spike / prototype THEN charter-lite: the question it answers, the timebox, the decision it feeds. No registry, no
  review. Output: an ADR citing the prototype as evidence.
- IF performance / cost optimisation THEN success metrics MUST be numeric (baseline, target, percentile, load profile)
  and the measurement harness MUST be named and run for a baseline before any change.
- IF docs-only / content-only (WEB without the site build) THEN usually S–M; review uses R1, R3, R6 and the
  source-binding check only.

## Model routing

Roster and model IDs: conventions §6–§7. The orchestrator runs intake and the spec/design gates at high effort. Spend
top-tier tokens on synthesis and judgement (what not to build, which 3 questions, consistency across IDs); spend cheap
tokens on reading and checking. Every downgrade has a mechanical guard where one exists.

| Role | S | M | L / XL | Guard on the cheaper choice |
|---|---|---|---|---|
| Classifier (SPEC-R01) | orchestrator inline | orchestrator inline | orchestrator inline + blind second opinion `mission-reviewer` (shapes-and-scope §2) | Forcing rules in shapes-and-scope §2 only add traits or raise class; disagreement on a forking field → adjudicate or ask |
| Discovery sweeper | — | `mission-scout` | `mission-scout`, fan-out per area (≤16 read-only lanes) | Orchestrator spot-checks 3 random pointers per digest; any miss → rerun area with `mission-verifier` |
| Web research for platform limits / conventions | — | `mission-worker` | `mission-worker`; contested trade-offs → `mission-builder` | Unsourced facts are rejected by the synthesizer; limits carry URL + access date |
| Charter author + question selector | orchestrator (task card) | orchestrator | `mission-strategist` | Rubric R1–R4 at the review gate |
| Spec synthesizer (IDs, EARS, oracles) | — | `mission-builder` | `mission-strategist` on XL; `mission-builder` on L | `validate-registry.py` exit 0 + review gate |
| Backend / frontend / migration designer, ADRs | — | `mission-builder` | `mission-builder` (architecture on XL MAY go to `mission-strategist`) | Review lenses "failure modes & limits", "UX verifiability" |
| Template filling, EARS rewrite of existing prose, registry drafting | — | `mission-worker` | `mission-worker` | Validator + reviewer samples 10% of rewritten requirements against the source prose |
| Registry validator | — | script via `mission-checker` | script via `mission-checker` | Deterministic; never a model verdict |
| Adversarial spec/design reviewer | — | `mission-critic`, 1 lens | `mission-critic`, 2–3 lenses in parallel | Findings need quote + failure scenario; refuter before blocking |
| Cross-model lens (XL) | — | — | `mission-strategist-review` when the spec author was `mission-builder`; `mission-critic` when it was `mission-strategist` | Author and reviewer MUST differ in context; SHOULD differ in model on XL |
| Security & privacy lens | — | `mission-critic` | `mission-critic` | Route directly to Opus 4.8; Fable cyber classifiers may refuse benign threat modelling — never skip the lens silently |
| Refuter of candidate blocker/major findings | — | `mission-verifier` | `mission-verifier` | Not the reviewer that raised the finding |
| Finding triage & disposition | — | orchestrator | orchestrator (high effort) | Disposition log is re-read in round 2 |

Cost rules:

1. M never spends Fable on spec authoring beyond the orchestrator's own charter drafting; `mission-builder` writes the
   spec and the review round is the guard (judgement, not measured).
2. L/XL: `mission-strategist` writes only the charter and spec synthesis. Everything that reads a lot (discovery,
   research) runs on Sonnet 4.6 roster agents with pointer-checked outputs.
3. Reviewers get artefacts + rubric + validator log, never transcripts (cheaper and more independent).
4. When author and reviewer share model·effort (L: `mission-builder` design reviewed by `mission-critic`, both Opus
   4.8 high), the reviewer MUST differ in lens prompt and evidence set.
5. A one-requirement change edits the delta; never regenerate the whole spec.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Interview fatigue (20–60 questions) | Recreates the typing burden the skill removes | Assumption-first intake; ≤3 questions per round, ≤2 rounds (SPEC-R06) |
| Silent assumption | Platform, datastore or retention chosen invisibly; unreviewable | ASSUMPTIONS.md rows; rubric R3 |
| Sledgehammer spec | Stories and dozens of criteria for a small bug | Classify first; S = task card (SPEC-R03) |
| Prose requirement with no oracle ("should feel fast") | Cannot be graded; loops end at "handled enough" | Oracle kind + threshold (SPEC-R16); rubric R2/R5 |
| EARS theatre | Perfect SHALL sentences, no named test | Oracle kind on every ID; validator requires oracles once implemented |
| Model-maintained registry | Silent drift, tokens spent every edit | Script validator (SPEC-R22); models only add references |
| One e2e test as oracle for everything | Registry looks complete while contracts go unverified | SPEC-R19; contract-level oracles |
| Design doc as implementation manual | No trade-offs; should have been code or a task list | ≥2 alternatives or no doc (SPEC-R27) |
| Pasting full schemas into designs | Stale copies, bloated context | Link the contract file; sketch trade-off parts only |
| Platform surprise mid-build (e.g. D1 10 GB ceiling) | Re-architecture after code exists | Limits table with sources (SPEC-R29) |
| Unverifiable screen spec ("modern card layout") | Visual verifier grades by vibes | Regions + assertions + state matrix (SPEC-R30/R31) |
| Tokens in the global skill | Diverge from the code | Token source in the repo (SPEC-R32) |
| Uncapped spec review | Fixes create findings; progress stops | Caps S=0 M=1 L/XL=2, stop on severity (SPEC-R35) |
| Human gate at every phase | Days-long autonomous runs stall | Human only for high-cost questions, L/XL sign-off, irreversible actions |
| Spec rot | Next agent trusts a stale spec | Same-change-set updates + change log (SPEC-R20) |
| Spec-as-source regeneration | Destroys hard-won fixes; unproven | Spec-anchored only |
| Carrying intake context into build | Interview bias + bloated context | Fresh context from files (SPEC-R36) |
| Faking live acceptance | "Real users in 3 minutes" marked passed from a simulation | `live-only` stays PENDING-LIVE (SPEC-R11) |
| Migration by "same as before" | Replicates unwanted legacy behaviour, misses hidden behaviour | Behaviour inventory keep/drop/change |
| Parallel registry in a brownfield repo | Two sources of truth for IDs | Extend the existing scheme |
| Optimistic status promotion | `implemented`/`verified` claims without proof | Only verifiers set `verified`; demote with a note (SPEC-R24) |

## Unverified harness details

| Detail | What is unverified | Safe fallback |
|---|---|---|
| Question tool in headless runs | Whether an ask-the-user tool exists or blocks in `claude -p` / Routines | Treat every run without a live human as headless: apply ★ defaults, mark ASSUMED (unconfirmed), queue in STATUS.md |
| Pausing for human approval | Whether the harness can pause mid-mission for an irreversible step | Fail closed: STOP condition → BLOCKED-HUMAN; never proceed on a default for irreversible actions |
| `/goal` evaluator model | Setting name and whether it can avoid Haiku | Never use `/goal` as a gate; verifiers + `check.sh` + `validate-registry.py` |
| Kiro bugfix-spec field names | Current / Expected / Unchanged came from search snippets | Structure is adopted on its merits; names are this skill's own |
| Apple 44×44 pt target minimum | Practitioner-sourced; the HIG page carrying it was not fetched | Use it as the default threshold; lane E / verification MAY replace it with a HIG-cited value |
| Viewport sizes in SCREEN.md | Illustrative (393×852, 375×667 pt) | Take device list from charter constraints or the simulator list in CONTEXT.md |
| Cloudflare limits beyond D1 | Workers CPU, body size, R2 object size, Queue batch size were not fetched | BACKEND §5 rows say "look up"; the designer fetches and cites before relying |
| PyYAML presence in target environments | Unknown | Validator falls back to its built-in subset parser; keep the registry in the subset (SPEC-R26) |
| Question-budget thresholds (3 per round, 2 rounds) and class thresholds | Judgement grounded in the user's stated pain, not measured | Keep; revise via LESSONS-INBOX after retros |

## Evidence

- https://code.claude.com/docs/en/best-practices.md — explore → plan → implement; skip the plan for one-sentence diffs.
- https://velvetshark.com/stop-prompting-claude-code-let-it-interview-you — interview technique; fresh-session hand-off.
- https://raw.githubusercontent.com/github/spec-kit/main/templates/spec-template.md — prioritised independent stories, NEEDS CLARIFICATION, assumptions.
- https://alistairmavin.com/ears/ — EARS patterns and ruleset.
- https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html — spec-first / spec-anchored / spec-as-source.
- https://www.industrialempathy.com/posts/design-docs-at-google/ — design-doc anatomy; alternatives; when not to write one.
- https://raw.githubusercontent.com/joelparkerhenderson/architecture-decision-record/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md — Nygard ADR.
- https://developers.cloudflare.com/d1/platform/limits/index.md — D1 size, concurrency, per-invocation limits (store map: BACKEND template §5).
- https://developer.apple.com/tutorials/data/design/human-interface-guidelines/accessibility.json — HIG accessibility (Dynamic Type ≥200%).
- https://martinfowler.com/bliki/StranglerFigApplication.html — incremental migration, seams, unwanted legacy behaviour.
- `arcwell/docs/product/arcwell-spec.md` lines 27-29 (ID + CI rule), 1911-1960 (import/cutover), 2063-2076 (STOP list); source report `research/mission-skill/03-spec-design.md`.
