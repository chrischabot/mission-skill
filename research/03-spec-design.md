# R03 — Specification & design: from a high-level prompt to an executable spec

Lane report for the mission skill. Component: intake → mission charter → overarching spec with requirement registry →
backend/frontend design → delta designs for other shapes → adversarial spec review → right-sizing.

---

## 1. Executive summary & strong opinions

The post says almost nothing about specification. It assumes a "goal" already exists and that a grader can check it
(post steps 05, 13; brief §3). In practice a mission succeeds or fails on whether a one-line direction becomes a
*contract*: a small set of stable, testable requirements with named oracles, explicit non-goals, recorded assumptions
and stop conditions. The best external practice agrees on the shape. Claude Code's own guidance is explore → plan →
implement, with a check Claude can run (https://code.claude.com/docs/en/best-practices.md). Spec Kit uses
prioritised, independently testable stories plus `[NEEDS CLARIFICATION]` markers
(https://raw.githubusercontent.com/github/spec-kit/main/templates/spec-template.md). Kiro gates requirements → design →
tasks and writes criteria in EARS (https://dev.codemyspec.com/blog/kiro-specs-explained). The user's own arcwell project
already runs a registry with CI traceability (`arcwell/docs/product/arcwell-spec.md:27-29`, `arcwell/REQUIREMENTS.yaml:1-20`).
The skill should keep that rigour and fix its two costs: heavy up-front typing and uncapped review loops.

Verdicts (actionable):

1. **Never start building from the raw prompt on M+ work. Produce a one-page Mission Charter first.** It has goals,
   non-goals, users, constraints, success metrics, assumptions, stop conditions and a scope class. If you could describe
   the diff in one sentence, skip the charter and write a 5-line task card instead
   (https://code.claude.com/docs/en/best-practices.md).
2. **Ask at most 3 questions per intake round (≤2 rounds, so ≤6 total). Every other gap becomes a recorded,
   reversible assumption.** The viral "interview me" technique asks 20–60 questions
   (https://velvetshark.com/stop-prompting-claude-code-let-it-interview-you). That contradicts this user's stated pain:
   typing everything out is too much work (brief §1). Ask only about things that are *expensive to reverse*:
   platform, data ownership, money, irreversible external side effects, taste anchors.
3. **Explore before you specify. For brownfield work, discovery is mandatory and comes first.** Map the conventions,
   the existing tests and the owners, then write a *delta* spec. Spec tools are weakest here
   (https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html).
4. **Every normative requirement gets a stable ID and at least one named oracle before any code.** An ID with no
   oracle is a wish. Copy arcwell's rule: CI rejects an ID with no registered verification and a test that cites an
   unknown ID (`arcwell-spec.md:1276`).
5. **Use EARS for behavioural criteria and BCP 14 capitals for normative strength. Don't bolt Gherkin onto
   everything.** EARS forces trigger + system + response (https://alistairmavin.com/ears/). BCP 14 key words mean
   something only in capitals (https://www.rfc-editor.org/rfc/rfc8174.txt). Given/When/Then belongs to the few P1
   journeys that become scenario tests.
6. **Keep a registry, but split authored from generated.** Requirement text lives in the spec. Status and test refs
   live in a curation file. The registry is generated and checked. This is exactly arcwell's split
   (`arcwell/REQUIREMENTS.yaml:1-5`, `arcwell/requirements-curation.yaml:1-8`). For S/M missions a single hand-written
   YAML is enough.
7. **Right-size ruthlessly.** S: task card only. M: charter + mini spec (≤2 pages). L: charter + spec + backend
   and/or frontend design + ADRs. XL: all of these plus milestone gates and a migration plan where relevant. Kiro
   turning a small bug into 4 stories and 16 criteria is the canonical failure ("sledgehammer to crack a nut",
   https://www.thoughtworks.com/insights/decoder/s/spec-driven-development).
8. **Design docs record trade-offs and alternatives, not implementation manuals.** A doc with no alternatives
   considered shouldn't exist (https://www.industrialempathy.com/posts/design-docs-at-google/). Irreversible choices
   become Nygard ADRs (Context / Decision / Consequences).
9. **Backend designs must state the limits of the platform they sit on and the failure mode at each boundary.** On
   Cloudflare, D1's hard 10 GB per-database ceiling and its single-threaded execution are design inputs, not
   surprises (https://developers.cloudflare.com/d1/platform/limits/index.md).
10. **Frontend designs are screen specs with a state matrix, and they should be written to be verified by machine.**
    Each screen lists regions, tokens, the empty/loading/error/partial/offline states, accessibility minimums (Dynamic
    Type ≥200%, targets ≥44 pt on iOS) and a layout assertion list the visual-verification lane can check.
11. **The spec review is adversarial, fresh-context and capped.** Use a rubric (ambiguity, untestable criteria,
    missing failure modes, contradictions, missing non-goals, unowned responsibilities). Default 1 round for M,
    2 for L/XL, and stop on severity, not on finding count. Arcwell's eighteen rounds show the uncapped cost
    (`arcwell/docs/operations/review-process-amendment.md:3-5`).
12. **Specs are spec-anchored, not spec-as-source.** Update the spec when reality contradicts it: an incident, a
    refuted assumption, a design change. Don't regenerate code from specs (Böckeler's three levels,
    https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html).
13. **Every charter carries STOP conditions.** These are situations where the agent escalates instead of
    improvising. Arcwell's §26 list is the model (`arcwell-spec.md:2063-2076`).
14. **Fable 5.1 writes the charter and synthesizes the spec on L/XL. Opus 4.8 does design and adversarial review.
    Sonnet 4.6 does discovery sweeps, registry lint and template filling.** A mechanical registry validator (a script)
    guards every downgrade.

## 2. Claim check

The post makes few claims about specification. The ones that bear on this component:

| # | Post claim (brief §3) | Verdict | Evidence | What the skill should do |
|---|---|---|---|---|
| C1 | `/goal` is a plain-text goal with a model grader; the loop exits when the grader passes (step 05) | **Verified** | https://code.claude.com/docs/en/goal.md: a small fast model checks the condition after each turn and returns met / not yet met / impossible | Write acceptance criteria that can be pasted into a goal condition. Each has one measurable end state, a stated check and a constraints clause. |
| C2 | The grader is independent and objective | **Partly true, with a caveat** | The same page says the evaluator "doesn't run commands or read files independently"; it judges what the conversation surfaced. It "defaults to Haiku on the Claude API" | Criteria must name the command whose output proves them. The skill must configure the small fast model (e.g. Sonnet 4.6) to honour the no-Haiku rule, or use a Stop-hook script or verifier sub-agent instead. |
| C3 | `/goal` fits implementation work with a measurable end state | **Verified** | goal.md lists "Implementing a design doc until all acceptance criteria hold" | The spec's acceptance-criteria block is the natural goal condition for an implementation slice. |
| C4 | "Outcomes" in CMA uses a file-based rubric with gradable criteria and `max_iterations` (step 05) | **Plausible, not verified by this lane** | Not fetched; see sibling lanes 01/06 | Make the spec-review rubric and the acceptance rubric file-based and binary, so they work under either harness. |
| C5 | Fable "tests its own assumptions" and runs with "minimal oversight" on large projects (step 01) | **Plausible marketing, unverified here** | Launch-post details live in lane 02's notes (`02-model-routing-cost.md:18-24`) | Don't rely on it. Assumptions are written into the charter with a verification plan and a "reversal cost". A verifier checks them, not the author. |
| C6 | "Rather than directly prompting and steering … design loops that let the model self-correct in response to environment feedback" (step 02, attributed to Anthropic) | **Consistent with verified docs; exact quote unverified** | best-practices: "Give Claude a check it can run … the loop closes on its own" (https://code.claude.com/docs/en/best-practices.md) | The spec's job is to *create the environment feedback*: oracles, fixtures, layout assertions. Prose exhortation does not do that. |
| C7 | The vision verifier compares a screenshot against "design tokens in the project Skill" (step 13) | **Plausible, but tokens are misplaced** | A stable vendor-neutral token format exists (DTCG 2025.10, https://www.designtokens.org/tr/2025.10/format/) | Put tokens in the *project repo* (e.g. `design/tokens.json`, DTCG format), referenced by the frontend design. A global Skill is the wrong home for project tokens. |
| C8 | Dynamic workflows "strictly follow" an orchestration plan (step 07) | **Term verified; strictness unverified** | best-practices mentions "a dynamic workflow that checks its own findings" | Treat the spec's task list and gates as the plan of record, whatever orchestration primitive is available. |
| C9 | Implicit claim: a good goal is enough to start | **Contradicted by practice** | Claude Code recommends explore → plan → implement; SDD tools all put a requirements phase first (https://raw.githubusercontent.com/github/spec-kit/main/spec-driven.md, https://dev.codemyspec.com/blog/kiro-specs-explained) | Add an intake + spec stage before any loop on M+ work. |

## 3. Deep findings

### 3.1 Intake: from a short direction to a charter

**Claude Code's own workflow separates exploration from execution.** It runs Explore → Plan → Implement → Commit, and
plan mode reads files without changing them. The same page names the exit: "If you could describe the diff in one
sentence, skip the plan" (https://code.claude.com/docs/en/best-practices.md). It also calls the context window "the most
important resource to manage". So intake should *produce files* (charter, spec) that a fresh implementation context can
load. It should not rely on a long conversation.

**The interview technique works, but it costs the user's attention.** Thariq's prompt, "interview me in detail using
the AskUserQuestionTool … until it's complete", yields 20–60 questions and a spec. Implementation then runs in a *fresh
session* "so Claude doesn't carry over any biases from the interview". The author suggests adding anti-goals and
skipping the interview when nothing is ambiguous
(https://velvetshark.com/stop-prompting-claude-code-let-it-interview-you). Two parts carry over directly: the
fresh-session hand-off, and anti-goals. The question count does not. This user wants the skill to *remove* typing
(brief §1).

The synthesis this lane recommends (an inference from the sources above) is **assumption-first intake**. The agent
explores (the repo, the web if needed) and drafts the charter with every gap filled by a labelled assumption. Each
assumption gets a *reversal cost* (low/med/high). Only the top ≤3 high-reversal-cost unknowns go to the human, as
multiple-choice questions with a recommended default. If the human doesn't answer (headless run), the defaults stand
and are marked `ASSUMED`.

Spec Kit's template supports this with an explicit Assumptions section ("reasonable defaults chosen when the feature
description did not specify certain details") and inline `[NEEDS CLARIFICATION: …]` markers
(https://raw.githubusercontent.com/github/spec-kit/main/templates/spec-template.md).

**Goals and non-goals, Google style.** Non-goals "aren't negated goals like 'The system shouldn't crash', but rather
things that could reasonably be goals, but are explicitly chosen not to be goals"
(https://www.industrialempathy.com/posts/design-docs-at-google/). Arcwell's §1.3 is a strong example. It lists "not a
generic multi-tenant SaaS" and "does not fill quiet reports with weak stories to hit a duration target"
(`arcwell-spec.md:80-89`). These are exactly the scope cuts a model would otherwise "helpfully" add back.

**Success metrics must be technology-agnostic and measurable.** Spec Kit's `SC-001` ("Users can complete account
creation in under 2 minutes") shows the form. Arcwell's outcome IDs (OUT-001..010, `arcwell-spec.md:52-63`) are
product-level outcomes, and each still maps to a scenario test (`arcwell/REQUIREMENTS.yaml:14-17`). Some outcomes can't
be simulated honestly; arcwell's is "fourteen consecutive real mornings". Those are registered as `live` checks and kept
PENDING, never faked (`arcwell/REQUIREMENTS.yaml:16-20`).

**Stop conditions are the forgotten half of a charter.** Arcwell's §26 closes with "Stop and escalate rather than
improvise if …". The list includes two components owning one side effect, a test that can pass without observing the
outcome, and a migration that would overwrite unclassified user data (`arcwell-spec.md:2063-2076`). For an autonomous,
days-long mission this is the most important safety section, and no SDD tool template includes it. That is this lane's
observation from reading the Spec Kit template and the Kiro summaries.

### 3.2 The overarching spec: structure, language, IDs

**Normative strength.** BCP 14 key words carry special meaning "when, and only when, they appear in all capitals", and
"normative text does not require the use of these key words" (https://www.rfc-editor.org/rfc/rfc8174.txt). Arcwell
adopts MUST/MUST NOT/SHOULD/MAY and adds a crucial operational rule: "If implementation reveals an independently testable
behavior in prose, split it into its own ID before coding. Every test name or case record MUST cite at least one
requirement ID, and CI MUST reject an ID that has no registered verification" (`arcwell-spec.md:27-29`).

**Behavioural syntax.** EARS gives a small, learnable grammar: "While <optional pre-condition>, when <optional trigger>,
the <system name> shall <system response>". There are five patterns: ubiquitous, state-driven (While), event-driven
(When), optional feature (Where) and unwanted behaviour (If … then). The ruleset allows zero or more preconditions, zero
or one trigger, one system name and one or more responses (https://alistairmavin.com/ears/).

Kiro puts EARS into agent specs ("WHEN a user submits a form with invalid data THE SYSTEM SHALL display validation
errors next to the relevant fields"). A fair critic adds that EARS "standardizes how a requirement is phrased. It does
not make the acceptance criteria executable" (https://dev.codemyspec.com/blog/kiro-specs-explained). So EARS is
necessary for clarity. Named oracles are necessary for executability.

**The unwanted-behaviour pattern is the highest-value EARS form for agents.** "If <trigger>, then …" forces the author
to write down failure responses. Models skip those unless forced (an inference, consistent with arcwell's
failure-disposition and test-matrix sections, `arcwell-spec.md:1342`, `:1686`).

**IDs.** Arcwell uses domain-prefixed IDs (`ARCH-001`, `EVID-003`, `REL-005`, `SEC-004`, plus `ARCH-T01` for test
requirements; `arcwell-spec.md:97-144`, `requirements-curation.yaml:52-56`). Spec Kit uses flat `FR-001` / `SC-001`.
Domain prefixes scale better to XL: they group ownership and let a reviewer spot a thin domain. Flat IDs are fine for M.
IDs are **never renumbered**. Deleted IDs are tombstoned with `status: withdrawn` (this lane's recommendation, so that
test citations never silently re-point).

**Independently testable slices.** Spec Kit requires each user story to be "INDEPENDENTLY TESTABLE … if you implement
just ONE of them, you should still have a viable MVP", prioritised P1..Pn. That lines up with arcwell's "Build vertical
slices, not a broad mock surface" (`arcwell-spec.md:34`), and it gives the orchestrator natural fan-out units.

### 3.3 Machine-readable registry and traceability

Arcwell's registry is the most mature pattern found in this lane's research. It has three layers.

- **Authored text** lives in the spec and supplementary requirements.
- **Curation** (`requirements-curation.yaml`) holds `status` (planned | implemented | live-only), `automated`
  references in `path::test_name` form, and `notes`. "Every `automated` reference must resolve to an exact enabled test
  … AND that test must cite the requirement … Severity and milestone are NOT curatable" (`requirements-curation.yaml:1-8`).
- **Generated registry** (`REQUIREMENTS.yaml`): "GENERATED FILE … Edit the sources, not this file — `pnpm
  verify:requirements` rejects a stale registry" (`REQUIREMENTS.yaml:1-5`).

Its schema per entry is `id, text, kind, owner, severity, milestone, status, automated[], live[], notes`
(`REQUIREMENTS.yaml:6-20`). The spec's own example adds `failure_fixtures` (`arcwell-spec.md:1260-1274`).

Two details deserve copying.

1. **Bidirectional citation.** A test must cite the ID, and the registry must point at the test. Either side alone can
   rot silently.
2. **Demotion as a first-class move.** After adversarial review found defects behind `implemented` claims, entries
   were demoted to `planned` with a note naming the gap: "that is the gate working, not a regression"
   (`requirements-curation.yaml:10-15`).

TEST-003 forbids one vague end-to-end test as the sole oracle for unrelated contracts (`arcwell-spec.md:1278`). That is
the anti-balloon counterpart: map many IDs to *precise* oracles, not many tests to one ID.

The traceability cost is real. The registry is 5,835 lines and the curation file 3,429 (view_files receipts). The
skill should generate and validate the registry *by script*, never by model. A model should only fill in `automated`
references once tests exist.

### 3.4 Spec-driven development tools: what to adopt, what to refuse

- **Spec Kit** runs Constitution → Specify → Plan → Tasks, with checklists as per-step definitions of done. Böckeler
  notes these are "interpreted by AI, so there is no 100% guarantee that they will be respected"
  (https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html). Its philosophy doc wants "consistency
  validation continuously … for ambiguity, contradictions, and gaps", and says "production metrics and incidents …
  update specifications" (https://raw.githubusercontent.com/github/spec-kit/main/spec-driven.md).
  **Adopt:** the story template, `[NEEDS CLARIFICATION]`, Assumptions, a constitution-like standing file.
  **Refuse:** the "power inversion" claim that code is regenerated from the spec. That is spec-as-source, which is
  unproven.
- **Kiro** produces requirements.md (EARS), design.md and tasks.md, each linked to requirements and grouped into
  parallel "waves". It has a human gate per phase, steering files (product.md / tech.md / structure.md), and a separate
  **bugfix spec** with Current / Expected / Unchanged behaviour (https://kiro.dev/docs/specs/bugfix-specs/, from a
  search snippet). **Adopt:** tasks linked to requirement IDs, waves, the three-part bugfix contract (the Unchanged
  block is the regression fence). **Refuse:** a human approval gate at *every* phase. That defeats "hand off and
  review deliverables". Keep human gates to the charter questions and to irreversible actions.
- **Böckeler's levels**: spec-first, spec-anchored, spec-as-source. All tools are spec-first, few are anchored, and
  maintenance strategy is "often left vague". The critique to remember is scale mismatch. A small bug became "multiple
  user stories and dozens of acceptance criteria"
  (https://www.thoughtworks.com/insights/decoder/s/spec-driven-development). **Adopt:** spec-anchored with an explicit
  maintenance rule (the spec changes in the same commit as the behaviour change) and scope-based depth.

### 3.5 Backend design

**Google's design-doc anatomy** is the right skeleton: context & scope, goals & non-goals, the design (overview then
detail), a system-context diagram, APIs and data storage sketched "focus[ing] on the parts that are relevant to the
design and its trade-offs", alternatives considered ("one of the most important" sections), and cross-cutting concerns
(security, privacy, observability). It is 10–20 pages for large projects and a 1–3 page "mini design doc" for
incremental work. The telling line: a doc that is really an "implementation manual" with no trade-offs means "it would
probably have been a better idea to write the actual program right away"
(https://www.industrialempathy.com/posts/design-docs-at-google/). Prototyping counts as design: "I tried it out and it
works."

**ADRs** (Nygard) are the minimal durable record: Title, Status (proposed / accepted / rejected / deprecated /
superseded), Context, Decision, Consequences
(https://raw.githubusercontent.com/joelparkerhenderson/architecture-decision-record/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md).
Arcwell's §25 "Preserve / Do not preserve" decision ledger (`arcwell-spec.md:2004-2026`) is a compact variant worth
shipping for migrations.

**Platform limits are requirements.** On Cloudflare, D1's maximum database size is 10 GB (Paid) and "cannot be further
increased". Each database is "inherently single-threaded" (1 ms queries ≈ 1,000 qps). Paid plans allow 1,000 queries
per Worker invocation and 100 bound parameters per query. Large UPDATE/DELETE work must be batched, and D1 "is designed
for horizontal scale out across multiple, smaller (10 GB) databases"
(https://developers.cloudflare.com/d1/platform/limits/index.md).

The storage map: KV for eventually consistent configuration and sessions, R2 for large objects with no egress fees,
Durable Objects for "global uniqueness" and strongly consistent transactional storage and coordination, D1 for
relational read-heavy data, Queues for background jobs
(https://developers.cloudflare.com/workers/platform/storage-options/index.md). A backend design for the fashion-app
example therefore has to say *per entity* which store owns it and why. It also needs a capacity note: images in R2 with
metadata in D1, and per-user coordination in a DO only if real-time or strict ordering is required.

Arcwell's "one owner for every responsibility" (ARCH-001, `arcwell-spec.md:97`) and its canonical state machines (§6)
are, in this lane's judgement (inference), the backend patterns that most reduce agent-induced bugs. Every durable record and side effect gets exactly one
owner, and every lifecycle is an explicit state machine with illegal transitions rejected (`arcwell-spec.md:402`, `:2046`).

### 3.6 Frontend design

**Accessibility and platform conventions are inputs, not polish.** Apple's HIG defines an accessible interface as
intuitive, perceivable and adaptable. It tells designers to audit with Accessibility Inspector, to "give people the
option to enlarge text by at least 200 percent" (via Dynamic Type), and it lists platform default and minimum type sizes
(iOS/iPadOS default 17 pt) (https://developer.apple.com/tutorials/data/design/human-interface-guidelines/accessibility.json).
On the web, WCAG 2.2 SC 2.5.8 (Target Size, Minimum, Level AA) requires targets to meet a minimum size or spacing
(https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html). Practitioner summaries give 24×24 CSS px for
WCAG, 44 pt for Apple and 48 dp for Android (https://buildwithaccess.com/blog/touch-target-size-mobile-accessibility-wcag,
secondary; the exact Apple 44 pt figure was not fetched from the HIG in this lane).

**Tokens.** The Design Tokens Community Group format reached its first stable version (2025.10) on 2025-10-28
(https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/). The
frontend design should name one token file as the single source for colour, type, spacing, radius and motion. Both
SwiftUI and web code consume it, and the visual verifier checks against it (post step 13).

**IA and flows.** NN/g separates card sorting (users group content, which *generates* an IA) from tree testing
(evaluates a proposed hierarchy's findability) (https://www.nngroup.com/articles/card-sorting-tree-testing-differences/).
An agent can't run real users. It *can* run a synthetic tree test: "for task T, which path would a first-time user
take?" This is a cheap review lens, labelled as synthetic (inference).

**Written so layout can be verified later.** This is the key finding for the user's layout-verification goal (brief
§1). A screen spec written as prose ("a clean card grid") can't be graded. A screen spec written as *assertions* can:

- region order;
- alignment relations ("primary CTA is the bottom-most interactive element, full-width within safe-area margins");
- token references;
- a minimum target size;
- a state matrix (empty / loading / error / partial / offline / permission-denied);
- Dynamic Type at the largest accessibility size with no truncation of primary labels.

These map one-to-one onto the screenshot/vision and DOM checks that the frontend-verification lane (R05) specifies.
That mapping is this lane's recommendation. R05's grader template (`05-frontend-visual-ux-verification.md:321-361`,
headings Inputs / Procedure / Rules / Output; only the headings were scanned) is where such inputs would be consumed.

### 3.7 Delta designs for other shapes

- **Bug fix.** Kiro's bugfix spec separates Current behaviour (the defect), Expected behaviour (SHALL) and Unchanged
  behaviour (SHALL CONTINUE TO) (https://kiro.dev/docs/specs/bugfix-specs/). Add a *repro spec*: environment, exact
  steps, observed vs expected, frequency, and a failing test *before* the fix. The Unchanged block is where you stop
  a fix from quietly narrowing behaviour.
- **Feature in an existing product.** Discovery first: conventions, existing components and tokens, routing, test
  style, owners. Then a delta spec that cites existing IDs and adds new ones in the same scheme. Böckeler found SDD
  tools "even more work to introduce … into an existing codebase"
  (https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html). So the skill should *adopt the repo's*
  spec/ID conventions if they exist and create them only when absent.
- **Migration / extraction.** Fowler: wholesale replacement plans "go down in flames most of the time"; "replacements
  seem easy to specify, but often it's hard to figure out the details of existing behavior", and much of it "isn't
  really wanted". Four activities: outcomes, seams, deliver parts, organizational change. Transitional architecture is
  worth its cost (https://martinfowler.com/bliki/StranglerFigApplication.html). Arcwell's §23 supplies a concrete
  playbook (`arcwell-spec.md:1911-1960`):
  - explicit import / do-not-import lists;
  - run the import twice and require byte-identical results;
  - compare by semantic identity;
  - quarantine without blocking;
  - a 10-step side-by-side cutover that disables legacy owners *before* enabling new ones;
  - a bounded rollback snapshot;
  - "At no point may both old and new systems own the same external side effect without a deliberate
    shadow/suppression fence."
- **Research + website.** The spec becomes a content strategy and messaging brief: audiences, jobs-to-be-done, key
  messages with proof points, a sitemap, page inventory and templates (blog, docs), SEO/metadata, and research claims
  each bound to a source. Arcwell's EVID-001 ("a material factual claim MUST bind to one or more source-card revisions",
  `arcwell-spec.md:106`) is the right rule for market-position claims on a public site.

### 3.8 Adversarial spec review and right-sizing

Google's lifecycle puts review ("may be in multiple rounds") before implementation
(https://www.industrialempathy.com/posts/design-docs-at-google/). Spec Kit wants continuous checks for "ambiguity,
contradictions, and gaps" (https://raw.githubusercontent.com/github/spec-kit/main/spec-driven.md). Arcwell shows the
downside of no cap. There are 18 M1 disposition files (glob over `arcwell/docs/operations/m1-*-disposition.md`), and
the amendment says repeating the loop "prevented progress on the remaining normative plan"
(`review-process-amendment.md:26-28`). Lane 06 sets implementation-review caps S=1/M=2/L=3/XL=4 and "stop on severity,
not on count" (`06-verification-adversarial-review.md:40-44`).

Specs are cheaper to fix than code. A spec review should be *shallower and earlier*: one round for M, two for L/XL.
A third round is allowed only if round 2 found a blocker in a *newly written* section.

**Right-sizing rule.** Google's "write a design doc only when the solution is ambiguous" plus Claude Code's "one-sentence
diff → skip the plan" give a two-axis classifier: *ambiguity* (problem or solution) × *blast radius* (files, services,
users, money, irreversibility). Scope class = max of the two. That is the rule Section 4 encodes.

## 4. Opinionated spec for the skill

Normative rules, ready to paste. The key words are interpreted per BCP 14 (RFC 2119/8174) and only in capitals.

### 4.1 Scope classification (runs first, always)

- **SPEC-R01.** The orchestrator MUST classify each mission before writing any spec artefact. It rates *ambiguity*
  (A0 none, A1 bounded, A2 open) and *blast radius* (B0 one file/one behaviour, B1 one component, B2 multiple
  components/services or a public surface, B3 multiple platforms, data migration, money or irreversible side effects).
  Evaluate in order: XL if B3 or (A2∧B2); else L if max(A,B) = 2; else M if max(A,B) = 1; else S.
- **SPEC-R02.** The class and its one-line justification MUST be written at the top of the charter (or the task card
  for S). The class MAY be revised upward at any stage. It MUST NOT be revised downward after implementation starts
  without a recorded reason.
- **SPEC-R03.** Artefact depth MUST follow the class:

| Class | Required artefacts | Spec review rounds (cap) |
|---|---|---|
| S | Task card (goal, repro/acceptance, oracle, constraints) | 0 (the verifier checks the acceptance line) |
| M | Charter-lite (≤1 page) + mini spec (≤2 pages, flat IDs) + registry YAML (hand-written) | 1 |
| L | Charter + spec (domain IDs) + backend and/or frontend design + ADRs for irreversible choices + registry | 2 |
| XL | L + milestone gates + generated registry with CI validator + migration plan (if applicable) + STOP list | 2 (+1 only for new-section blockers) |

### 4.2 Intake

- **SPEC-R04.** Before drafting, the orchestrator MUST explore. For brownfield work it reads the repo (conventions,
  existing specs/IDs, tests, owners) in read-only mode. For novel domains or platforms it researches the web. Findings
  go to `research/` with URLs.
- **SPEC-R05.** The orchestrator MUST fill every gap with a labelled assumption (`A-nn`, statement, reversal cost
  low/med/high, how it will be verified).
- **SPEC-R06.** The orchestrator MUST ask the human only about unknowns whose reversal cost is high. That means at most
  3 questions per round and at most 2 rounds. Each question is multiple-choice with a recommended default and a
  one-line consequence per option. Good question topics: target platforms, data ownership/retention, spend ceilings,
  irreversible external actions (publishing, payments, deleting data), taste anchors (reference apps or sites), and
  "what must not change".
- **SPEC-R07.** In a non-interactive run, or when the human doesn't answer, the defaults MUST be applied and marked
  `ASSUMED (unconfirmed)`. The mission MUST NOT block on them unless a STOP condition applies.
- **SPEC-R08.** The charter MUST contain goals, non-goals (things that could reasonably be goals), users/stakeholders,
  constraints, success metrics (measurable, technology-agnostic, each with a measurement method), assumptions, risks,
  STOP conditions, scope class, and a definition of done split into *product*, *engineering* and *operational*
  acceptance.

### 4.3 The spec

- **SPEC-R09.** Every normative statement MUST have a stable ID. The format is `<DOMAIN>-<NNN>` (domain: 2–6 uppercase
  letters; NNN zero-padded). Test-requirement IDs use `<DOMAIN>-T<NN>`, and outcome IDs use `OUT-<NNN>`. IDs MUST NOT be
  renumbered or reused. A removed requirement is kept with `status: withdrawn`.
- **SPEC-R10.** Behavioural requirements SHOULD be written in EARS. Every external boundary (network, provider, storage,
  user input, permission) MUST have at least one *unwanted behaviour* requirement (`IF … THEN the <system> SHALL …`).
- **SPEC-R11.** Each requirement MUST name its oracle kind (unit | property | contract | integration | scenario | e2e |
  visual | a11y | live | human) and a *falsifiable* acceptance criterion. It MUST NOT use unmeasurable adjectives
  ("fast", "intuitive", "robust", "clean") without a threshold or rubric reference.
- **SPEC-R12.** User journeys MUST be prioritised (P1..Pn) and each MUST be independently testable and demonstrable.
  P1 journeys MUST also carry Given/When/Then scenarios that become scenario or e2e tests.
- **SPEC-R13.** Unknowns that survive intake MUST appear inline as `[NEEDS CLARIFICATION: …]` with an owner. A spec MUST
  NOT pass review with any such marker attached to a P1 requirement.
- **SPEC-R14.** A test MAY cover several IDs. An ID MUST NOT rely solely on one broad e2e test when it names a specific
  contract (after arcwell TEST-003).
- **SPEC-R15.** The registry MUST be validated by a script, not a model. The script fails on duplicate IDs, IDs with
  no oracle once status ≥ `implemented`, oracle references that don't resolve, and tests citing unknown IDs.
- **SPEC-R16.** The spec is *spec-anchored*. A behaviour change MUST update the spec and registry in the same change
  set. A refuted assumption MUST update the charter. An incident or post-mortem SHOULD add or amend a requirement plus
  a recurrence fixture.

### 4.4 Design documents

- **SPEC-R17.** A design doc MUST include context & scope, goals/non-goals (linking to the charter), the design, at
  least two alternatives considered with trade-offs, cross-cutting concerns (security, privacy, observability, cost) and
  failure modes. A doc with no genuine alternatives MUST be reduced to a task list.
- **SPEC-R18.** Decisions that are expensive to reverse (datastore, auth model, API style, platform, sync model, public
  URL structure) MUST get an ADR (Nygard format). Superseding an ADR MUST create a new ADR.
- **SPEC-R19.** Backend designs MUST list the platform limits that bound the design, with source URLs. They MUST give
  each entity and each side effect exactly one owning component. They MUST describe every multi-step lifecycle as a
  state machine with its illegal transitions, and they MUST define idempotency and retry semantics for every external
  call.
- **SPEC-R20.** Frontend designs MUST include an IA/screen inventory, the P1 flows, a token file reference, and, per
  screen, a screen spec with a state matrix and layout assertions that a verifier can check from a screenshot or view
  hierarchy. Accessibility minimums MUST follow the platform (HIG for Apple platforms, WCAG 2.2 AA for web).
- **SPEC-R21.** Design docs SHOULD stay under ~20 pages equivalent. Beyond that, the problem MUST be split into
  sub-designs.

### 4.5 Review and gates

- **SPEC-R22.** Before implementation of M+ work, a fresh-context reviewer MUST review the charter + spec (+ designs)
  against the spec-review rubric (§7.7). The reviewer MUST NOT be given the author's transcript.
- **SPEC-R23.** Findings MUST cite section/ID and a concrete failure scenario. They MUST be dispositioned FIXED /
  REFUTED / RESIDUAL / DEFERRED / CONTESTED (same vocabulary as lane 06). Rounds are capped per §4.1. The gate passes when there are no open blockers.
- **SPEC-R24.** After the gate, the orchestrator MUST hand implementation a *fresh* context loaded from files (charter,
  spec, designs, registry). It MUST NOT carry the intake conversation.
- **SPEC-R25.** Acceptance criteria used as `/goal` conditions (or any grader condition) MUST state the command whose
  output demonstrates them and any constraint that must not change, and MUST include a turn/time bound.

## 5. Model & effort assignment

Prices (per MTok input/output): Fable 5.1 $10/$50, Opus 4.8 $5/$25, Sonnet 4.6 $3/$15. These come from lane 02's
verified notes (`02-model-routing-cost.md:8-11`). Effort levels `low`/`medium`/`high` apply to all three; `xhigh` is
not available on Sonnet 4.6 (`02-model-routing-cost.md:43-49`). No Haiku anywhere, including the `/goal` evaluator,
which defaults to Haiku and must be reconfigured (https://code.claude.com/docs/en/goal.md).

The economics of this component are favourable. Spec work is *token-light and leverage-heavy*. A charter is ~1–2k
output tokens and a full L spec ~10–20k (inference from typical document sizes). A wrong spec wastes whole
implementation swarms. So spend top-tier tokens on *synthesis and judgement*, and cheap tokens on *reading and
checking*.

| Role | S | M | L / XL | Why | Guard on downgrade |
|---|---|---|---|---|---|
| Scope classifier (SPEC-R01) | orchestrator inline | Sonnet 4.6 low | Sonnet 4.6 medium | Cheap structured judgement over a short prompt | If Sonnet rates S/M but the prompt names a migration, a new platform, payments or public publishing, a keyword rule forces reclassification by the orchestrator |
| Discovery sweeper (brownfield map, conventions, existing IDs) | — | Sonnet 4.6 medium | Sonnet 4.6 medium, fan-out per area | Bulk reading; output is facts with file:line pointers | The orchestrator spot-checks 3 random pointers; any miss → rerun at high |
| Web researcher (platform limits, conventions) | — | Sonnet 4.6 medium | Sonnet 4.6 high; Opus 4.8 high for contested trade-offs | Facts must carry URLs | Unsourced facts are rejected by the synthesizer |
| Charter author + question selector | orchestrator (task card) | Opus 4.8 medium | **Fable 5.1 high** | Deciding what *not* to build and which 3 questions matter is the highest-leverage judgement in the mission | Rubric items R1–R4 in §7.7 |
| Spec synthesizer (IDs, EARS, oracles) | — | Opus 4.8 medium | Fable 5.1 high for XL; Opus 4.8 high for L | Consistency across many requirements | Registry validator script (mechanical) + review |
| Backend designer (architecture, data model, ADRs) | — | Opus 4.8 medium | Opus 4.8 high | Hard but bounded; the post itself routes architecture to Opus (brief §3 step 04) | Adversarial review lens "failure modes & limits" |
| Frontend designer (IA, screen specs, tokens) | — | Opus 4.8 medium | Opus 4.8 high | Taste + structure; layout assertions need precision | R05 verifier can only check what is asserted; rubric R9 |
| Template filler / registry drafting / EARS rewriting of existing prose | — | Sonnet 4.6 low | Sonnet 4.6 medium | Mechanical transformation | Validator script + reviewer samples 10% of rewritten requirements against source prose |
| Registry validator | script | script | script | Determinism beats models | n/a |
| Adversarial spec reviewer | — | Opus 4.8 medium (1 lens) | Opus 4.8 high (2–3 lenses in parallel) | Must differ from the author in context and ideally model/effort (lane 06 verdict 5) | Reviewer findings need a failure scenario; the orchestrator refutes weak ones |
| Security/privacy lens | — | Opus 4.8 medium | Opus 4.8 high | Fable 5.1 cyber classifiers may refuse benign threat modelling (`06-verification-adversarial-review.md:56-58`) | Route directly to Opus; never silently skip |
| Finding triage & disposition | orchestrator | Opus 4.8 medium | Fable 5.1 medium | Needs the whole-spec view | Disposition log is reviewed in the next round |

Cost-reasoning rules:

1. On M work, never use Fable for spec authoring. Opus 4.8 at medium is enough (this lane's judgement, not measured)
   and costs half as much per token. The review round is the guard.
2. On L/XL, Fable 5.1 writes only the charter and the spec synthesis (a few tens of thousands of output tokens).
   Everything that reads a lot (discovery, research) runs on Sonnet with pointer-checked outputs.
3. Reviewers get the artefacts plus the rubric, never transcripts. That cuts reviewer input tokens and improves
   independence.
4. Every downgrade has a *mechanical* guard where one exists (validator, pointer spot-check, keyword reclassifier) and
   a *model* guard only where it doesn't (review lens).
5. When author and reviewer would be the same model and effort (L: Opus 4.8 high on both sides), the reviewer MUST
   differ in lens prompt and evidence set. On XL, one lens SHOULD run on Fable 5.1 medium when the spec was authored
   by Opus, or on Opus 4.8 high when it was authored by Fable.

## 6. Project-shape conditionals

### 6.1 Scope scaling (applies to every shape)

- IF class = S THEN write a task card only (§7.1 last block). The acceptance line names the command/test. No
  registry, no review; the implementation verifier checks the acceptance line.
- IF class = M THEN charter-lite + mini spec with flat IDs (`FR-001`, `SC-001`) + hand-written `requirements.yaml` +
  one review round with the core rubric (R1–R8).
- IF class = L THEN full charter + spec with domain IDs + the design docs the task needs + ADRs + 2 review rounds with
  a lens panel.
- IF class = XL THEN L + milestones with exit gates + generated registry + CI validator + STOP list + a consolidated
  cross-milestone review after integration (after arcwell's amendment, `review-process-amendment.md:15-18`).
- IF any stage discovers higher ambiguity or blast radius THEN reclassify upward and produce the missing artefacts
  before continuing that slice.

### 6.2 Greenfield multi-platform app (e.g. SwiftUI iOS + Cloudflare backend)

- IF greenfield THEN class ≥ L. Produce charter → spec → backend design → frontend design → ADRs → review → slice plan.
- IF there is more than one client platform or a backend THEN the spec MUST define the API contract as its own domain
  (`API-nnn`) with a schema file (OpenAPI or typed contracts package) that both sides test against.
- IF the backend is Cloudflare THEN the backend design MUST include a limits table (D1 10 GB/DB and single-threaded;
  queries per invocation; R2 for blobs; DO only for coordination or strict ordering) and a per-entity store ownership
  table (https://developers.cloudflare.com/d1/platform/limits/index.md).
- IF the client is SwiftUI THEN the frontend design MUST cite HIG conventions (navigation pattern, Dynamic Type ≥200%
  support, Accessibility Inspector audit) and specify Light/Dark and the largest accessibility text size in every
  screen's state matrix.
- IF users upload personal images (e.g. outfit photos) THEN the charter MUST name retention and deletion requirements
  and the backend design MUST include a privacy section (after Google's dedicated privacy review practice,
  https://www.industrialempathy.com/posts/design-docs-at-google/).
- IF the product has a taste component THEN intake MUST ask for 2–3 reference apps as a taste anchor (one of the ≤3
  questions), and tokens MUST be defined before the first screen is built.

### 6.3 Deep bug hunt

- IF the task is a bug fix THEN produce a bugfix spec (§7.2 variant): Current / Expected / Unchanged behaviour + a
  repro spec. Class is usually S/M even when the hunt is long; *investigation* depth is not *spec* depth.
- IF there is no reliable repro THEN the first deliverable is a repro (or a statistical repro with a frequency, e.g.
  "fails ≥1 in 50 runs"), and spec review is skipped until the repro exists.
- IF the fix changes a public contract THEN reclassify to L and write a delta spec + ADR.
- ALWAYS add the regression oracle to the registry (or test file header) citing the bug ID.

### 6.4 Feature in an existing product (e.g. a new dashboard)

- IF brownfield THEN discovery MUST come before charter: existing spec/ID scheme, tokens/components, routing/IA, data
  sources, test conventions, owners. Output a *conventions digest* with file:line pointers.
- IF the repo already has a spec/registry scheme THEN extend it (same ID prefixes, same registry file) and don't create
  a parallel one.
- IF the feature adds screens THEN write screen specs only for the new or changed screens, and reuse existing tokens.
  A new token requires an ADR-lite note.
- IF the dashboard shows metrics THEN each metric MUST have a definition requirement (source, formula, time zone,
  refresh, empty/partial semantics). Metric-definition ambiguity is this shape's most common defect class (inference;
  compare the post's STATE.md example about time zones, brief §3 step 11).

### 6.5 Service migration / extraction (e.g. AI gateway into a platform core service)

- IF migration THEN class ≥ L. Produce the migration plan skeleton (§7.6): current-state map, target, *parity
  criteria*, import/do-not-import, cutover steps, rollback, and a single-owner rule for side effects during coexistence.
- IF the old system has undocumented behaviour THEN discovery MUST produce a behaviour inventory, classifying each
  behaviour as keep / drop / change. Don't specify "same as before"; much legacy behaviour "isn't really wanted"
  (https://martinfowler.com/bliki/StranglerFigApplication.html).
- IF traffic is live THEN parity MUST be demonstrated by shadow/replay comparison before cutover, and cutover MUST
  disable the legacy owner before enabling the new one (`arcwell-spec.md:1949-1960`).
- IF secrets, keys or provider accounts move THEN the security lens is mandatory in spec review.

### 6.6 Research + marketing website with blog/docs

- IF the task includes market research THEN the spec starts with a research question list, and every claim that
  reaches the site MUST bind to a source URL + access date (after arcwell EVID-001, `arcwell-spec.md:106`).
- IF the task includes a website THEN produce a content strategy + sitemap + page inventory + page-template screen
  specs (home, about/team, blog index/post, docs index/page) + messaging hierarchy. Tokens and accessibility follow
  WCAG 2.2 AA.
- IF the site has docs THEN define the docs IA with a synthetic tree test: for 5 top tasks, the expected path must be
  ≤3 clicks and the labels unambiguous (https://www.nngroup.com/articles/card-sorting-tree-testing-differences/).
- IF the site makes competitive claims THEN the charter's STOP list MUST include "unsourced comparative claim".

### 6.7 Other shapes that matter

- IF the task is a *spike/prototype* THEN write a charter-lite with the question the prototype answers and a timebox.
  No registry. The output is an ADR ("I tried it out and it works" is valid design evidence,
  https://www.industrialempathy.com/posts/design-docs-at-google/).
- IF the task is *performance/cost optimisation* THEN success metrics MUST be numeric with a measurement harness named
  before any change.
- IF the task is *docs-only / content-only* THEN class ≤ M and the review rubric uses R1, R3, R6 and the source-binding
  check only.

## 7. Artifacts & templates

Suggested file layout (the synthesizer may rename): `mission/CHARTER.md`, `mission/SPEC.md`, `mission/requirements.yaml`,
`mission/design/backend.md`, `mission/design/frontend.md`, `mission/design/screens/<screen-id>.md`, `mission/adr/NNNN-*.md`,
`mission/MIGRATION.md`, `mission/reviews/spec-review-rN.md`. STATE.md/STATUS.md belong to lane 07.

### 7.1 Mission charter (M: sections marked ◆ only; L/XL: all)

```markdown
# Mission Charter · <mission name>
Class: <S|M|L|XL> — ambiguity A<0-2>, blast radius B<0-3>: <one-line justification>
Direction (verbatim from human): "<original prompt>"
Status: draft | reviewed | approved-by-default | approved-by-human   · Last updated: <date>

## ◆ 1. Outcome
One paragraph: who gets what, and why it matters. No technology.

## ◆ 2. Goals
- G1 <outcome-shaped goal>
- G2 …

## ◆ 3. Non-goals (things that could reasonably be goals, deliberately excluded)
- NG1 <e.g. "multi-tenant accounts in v1">
- NG2 …

## 4. Users & stakeholders
| User/stakeholder | Primary job-to-be-done | Platform/context |

## ◆ 5. Constraints
Platforms, stack mandates, budget ceilings (money + model spend), deadlines, compliance, "must not change" surfaces.

## ◆ 6. Success metrics
| ID | Metric (technology-agnostic) | Threshold | Measurement method / oracle | Automated or live |
| OUT-001 | … | … | … | … |

## ◆ 7. Assumptions (every gap filled; verify or overturn)
| ID | Assumption | Reversal cost (L/M/H) | Confirmed? (human / verified / ASSUMED) | How verified |
| A-01 | … | H | ASSUMED (unconfirmed) | … |

## 8. Questions asked (≤3 per round, ≤2 rounds)
| Q | Options (default marked ★) | Consequence per option | Answer |

## 9. Risks
| Risk | Likelihood | Impact | Mitigation / early signal |

## ◆ 10. STOP conditions (escalate, don't improvise)
- Two components would own the same side effect or record.
- A test could pass without observing the outcome it claims.
- A step would delete/overwrite unclassified user data, spend beyond <ceiling>, or publish externally without approval.
- A required decision contradicts a non-goal or constraint.
- <shape-specific stops>

## ◆ 11. Definition of done
- Product: <user-observable outcomes>
- Engineering: every normative ID registered and verified; validator green; review findings dispositioned.
- Operational: <deploy / live checks / acceptance window>; pending live checks stay PENDING, never simulated.

## 12. Artefact plan
Which of SPEC / backend / frontend / ADRs / MIGRATION this mission needs, and the spec-review round cap.
```

Task card for class S (replaces the charter):

```markdown
# Task · <name>   Class: S
Goal: <one sentence, outcome not activity>
Acceptance: <observable result> — proven by `<command>` (<expected output>)
Must not change: <files/behaviours/tests>
Repro (bugs): <steps> → observed <x>, expected <y>
Bound: stop after <n> turns or <t> minutes; escalate if <stop condition>
```

### 7.2 Spec skeleton with requirement-ID format

**ID grammar:** `^(OUT|[A-Z]{2,6})-(T?\d{2,3}|\d+-[CEU]\d+)` (the whole ID must match). `OUT-001` is an outcome (from the charter). `API-012` is a normative
requirement in domain API. `API-T03` is a test-architecture requirement. `BUG-417-E1` is a bugfix clause (Current /
Expected / Unchanged). M missions MAY use `FR-nnn` / `SC-nnn` only.
IDs are never renumbered or reused; withdrawn IDs stay in the registry.

```markdown
# Specification · <mission name>
Charter: CHARTER.md (class <L>) · Registry: requirements.yaml · Status: draft|reviewed|approved · Version: <n>

## 0. How to read this document
The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are interpreted as described in BCP 14 (RFC 2119, RFC 8174)
when, and only when, they appear in all capitals. Bold IDs are stable test anchors. Every test MUST cite ≥1 ID. Any
independently testable behaviour found in prose MUST be split into its own ID before coding.

## 1. Outcomes (copied from charter; do not diverge)
- **OUT-001 — <name>.** <one sentence>. Oracle: <scenario|live>.

## 2. Glossary (every domain term used normatively)
| Term | Definition | Not to be confused with |

## 3. User journeys (prioritised, each independently testable)
### J1 — <title> (P1)
Why P1: … · Independent test: "Can be fully tested by <action> and delivers <value>"
Scenarios:
1. Given <state>, When <action>, Then <observable outcome>  → covers UX-001, API-003
### J2 — <title> (P2) …

## 4. Requirements by domain
### 4.1 <DOMAIN> — <name>   (owner: <component>)
- **<DOM>-001.** When <trigger>, the <system> SHALL <response>. · Oracle: <kind> · Severity: <critical|high|med|low>
- **<DOM>-002.** While <state>, the <system> SHALL <response>. · Oracle: …
- **<DOM>-003.** If <unwanted condition>, then the <system> SHALL <response>. · Oracle: …
- **<DOM>-004.** Where <feature included>, the <system> SHALL <response>. · Oracle: …
[NEEDS CLARIFICATION: <question> · owner: <human|orchestrator> · default if unanswered: <x>]

## 5. Non-functional requirements (each with a threshold)
Performance (p95 under stated load), cost ceilings, storage bounds, availability, privacy/retention, accessibility level.

## 6. Failure modes & degradation
| Boundary | Failure | Required behaviour (ID) | Injected by (fixture) |

## 7. Data & state (summary; details in design)
Entities, owners, lifecycle state machines (legal transitions only; illegal transitions rejected — ID).

## 8. Out of scope for this spec (links to charter non-goals)

## 9. Acceptance
- Automated: every ID with status ≥ implemented has a resolving oracle; validator green.
- Live checks: <ID → check name>, status PENDING until actually run.
- Goal condition for implementation slices (≤4,000 chars): "<IDs …> hold, proven by `<command>` exiting 0 with
  <evidence>; no file under <frozen paths> modified; stop after <n> turns."

## 10. Change log (spec-anchored: behaviour changes update this file in the same change set)
| Version | Date | Change | IDs touched | Reason (incident / refuted assumption / decision ADR-nnnn) |
```

**Bugfix variant (replaces §3–4 for bug missions):**

```markdown
# Bugfix spec · BUG-<id> <title>   Class: <S|M>
## Repro
Environment: <versions, config, data> · Steps: 1… 2… · Frequency: <always | n in m runs> · Evidence: <log/screenshot path>
## Current behaviour (defect)
- **BUG-<id>-C1.** When <condition>, the <system> <incorrect behaviour>.
## Expected behaviour
- **BUG-<id>-E1.** When <condition>, the <system> SHALL <correct behaviour>. · Oracle: <test path::name> (fails before fix)
## Unchanged behaviour (regression fence)
- **BUG-<id>-U1.** When <adjacent condition>, the <system> SHALL CONTINUE TO <existing behaviour>. · Oracle: <existing test>
## Root cause (filled after investigation; verified, not guessed)
## Generalisation (hand-off to lessons lane): <class of bug, rule to consult next time>
```

### 7.3 Requirement registry YAML schema

For M, `requirements.yaml` is hand-written. For L/XL, arcwell's split is copied: authored text in SPEC.md, curation in
`requirements-curation.yaml` (status, oracles, notes), and `requirements.yaml` generated by script. Either way, the
file conforms to this schema (JSON-Schema-in-YAML, validated by script):

```yaml
# requirements.schema.yaml — validate with any JSON Schema validator
$schema: "https://json-schema.org/draft/2020-12/schema"
type: array
items:
  type: object
  required: [id, text, kind, owner, severity, status]
  additionalProperties: false
  properties:
    id:        { type: string, pattern: "^(OUT|[A-Z]{2,6})-(T?\\d{2,3}|\\d+-[CEU]\\d+)$" }
    text:      { type: string, minLength: 10 }          # copied verbatim from SPEC.md
    kind:      { enum: [outcome, requirement, nfr, test-architecture, bugfix, parity, content-claim] }
    ears:      { enum: [ubiquitous, event, state, optional, unwanted, complex, none] }
    owner:     { type: string }                          # one owning component or role
    severity:  { enum: [critical, high, medium, low] }
    priority:  { enum: [P1, P2, P3] }
    milestone: { type: [integer, string] }
    status:    { enum: [planned, implemented, live-only, withdrawn] }
    oracle_kind:
      type: array
      items: { enum: [unit, property, contract, integration, scenario, e2e, visual, a11y, live, human] }
    automated:                                           # path::test_name, must resolve AND the test must cite id
      type: array
      items: { type: string, pattern: "^[^:]+::[A-Za-z0-9_.\\- ]+$" }
    live:                                                # doc::CHECK-ID for checks that cannot be simulated honestly
      type: array
      items: { type: string }
    failure_fixtures: { type: array, items: { type: string } }
    sources:   { type: array, items: { type: string } }  # URLs for content-claim / platform-limit requirements
    supersedes: { type: string }
    notes:     { type: string }
```

Example entries:

```yaml
- id: API-007
  text: If an upload exceeds 10 MB, then the Hub SHALL reject it with 413 and no R2 object SHALL be written.
  kind: requirement
  ears: unwanted
  owner: hub-api
  severity: high
  priority: P1
  milestone: 1
  status: implemented
  oracle_kind: [integration]
  automated:
    - tests/integration/uploads.test.ts::api_007_oversize_upload_rejected_without_object_write
  failure_fixtures: [upload_11mb_jpeg]
- id: OUT-002
  text: A new user creates and saves a first outfit in under 3 minutes without help.
  kind: outcome
  owner: product
  severity: high
  status: live-only
  oracle_kind: [e2e, human]
  live:
    - acceptance/live-acceptance.md::OUT-LIVE-02
  notes: Synthetic walkthrough automated; real-user timing PENDING until run.
```

Validator rules (script, CI-blocking; after `arcwell-spec.md:1276-1278`, `requirements-curation.yaml:1-8`):

1. Schema valid; IDs unique; IDs match the grammar.
2. Every ID in SPEC.md exists in the registry, and every non-withdrawn registry ID exists in SPEC.md with identical
   text (for generated registries: the registry is not stale).
3. `status: implemented` ⇒ `automated` non-empty; every reference resolves to an enabled test; that test's name or
   docstring cites the ID.
4. Every test citing an ID cites an existing, non-withdrawn ID.
5. `severity: critical` involving an external provider ⇒ `live` non-empty.
6. No `[NEEDS CLARIFICATION` marker on a P1 requirement once SPEC status ≥ reviewed.
7. Report (non-blocking): IDs whose only oracle is a single e2e test shared by more than 5 IDs (TEST-003 smell).

### 7.4 Backend design skeleton (+ ADR)

```markdown
# Backend design · <system>
Links: CHARTER.md · SPEC.md (domains <API, DATA, SEC, …>) · ADRs: adr/ · Status: draft|reviewed|approved

## 1. Context & scope (objective facts only; not requirements)
## 2. Goals / non-goals (link charter G*/NG*; add design-level non-goals)
## 3. System context diagram
Mermaid/ASCII: clients, this system, third parties, trust boundaries.

## 4. Architecture overview
Components, each with ONE responsibility and owner. | Component | Owns (records, schedules, side effects) | Does NOT own |

## 5. Platform & limits (with source URLs)
| Limit | Value | Source | Design consequence |
| D1 max DB size | 10 GB, not raisable | developers.cloudflare.com/d1/platform/limits | per-user sharding or archive to R2 beyond <n> |
| D1 concurrency | single-threaded per DB | same | keep queries <5 ms; batch writes ≤1,000 rows |

## 6. Data model
| Entity | Store (D1/R2/DO/KV/…) | Owner | Key & indexes | Retention | PII? |
Lifecycle state machines: states, legal transitions, rejected transitions (IDs), terminal states.

## 7. API contracts
Contract file: <openapi.yaml | packages/contracts>. Per endpoint: method/path, auth scope, request/response schema
reference, idempotency key, error model (codes), rate limit, pagination, versioning rule. Sketch only what matters
to trade-offs; the contract file is the source of truth.

## 8. Key flows (sequence diagrams for P1 journeys)

## 9. Failure modes
| Boundary | Failure (timeout, 5xx, partial write, duplicate delivery, quota) | Detection | Response (retry policy / fallback / incident) | Req ID | Fixture |

## 10. Security & privacy
Threat model (assets, actors, entry points), authn/authz at the final dispatch boundary, secrets handling, input as
untrusted data, PII inventory, retention and deletion, audit logging.

## 11. Observability & operations
Logs/metrics/traces, health checks, alerts with thresholds, runbook stubs, deploy/rollback.

## 12. Cost model
| Driver | Unit price source | Expected volume | Monthly estimate | Hard/soft ceiling and behaviour at ceiling |

## 13. Alternatives considered (≥2, with trade-offs and why rejected)
## 14. Open questions / [NEEDS CLARIFICATION]
## 15. Test strategy hooks (hand-off to testing lane): which IDs need fakes, contract tests, live canaries
```

```markdown
# ADR-<NNNN>: <decision title>
Status: proposed | accepted | rejected | deprecated | superseded by ADR-<NNNN>   · Date: <date> · Deciders: <agent/model, human?>
## Context — forces, constraints, requirement IDs affected, evidence links
## Decision — what we will do (active voice)
## Alternatives — options considered, each with the decisive trade-off
## Consequences — what becomes easier/harder; new requirements or limits; reversal cost and trigger to revisit
```

### 7.5 Frontend design skeleton with screen-spec format

```markdown
# Frontend design · <app/site> · Platform: <SwiftUI iOS | web | …>
Links: CHARTER.md · SPEC.md (domain UX, A11Y) · tokens: design/tokens.json (DTCG) · Status: …

## 1. Platform conventions
Apple HIG (navigation stack/tab bar, sheets, Dynamic Type, SF Symbols, Light/Dark) or web (WCAG 2.2 AA, responsive
breakpoints, keyboard navigation). Deviations need a reason.

## 2. Information architecture
Tree of destinations (screen IDs), max depth, primary navigation. Synthetic tree test: for top 5 tasks, expected path.

## 3. User flows (P1 journeys)
| Flow ID | Journey (SPEC J*) | Steps (screen → action → screen) | Success end state | Failure branches |

## 4. Screen inventory
| Screen ID | Name | Purpose | Entry points | Requirement IDs | Spec file |

## 5. Design tokens
Colour roles (with contrast pairs), type scale mapped to platform text styles, spacing scale, radii, elevation, motion.
Components use roles, never raw values.

## 6. Components
| Component | Variants | States | Tokens used | Accessibility label/trait rules |

## 7. Content & copy rules (voice, empty-state tone, error message pattern: what happened + what to do)
## 8. Accessibility requirements (IDs): text scaling ≥200% / largest AX size, contrast, targets, VoiceOver/screen-reader
order, reduced motion, colour-independent meaning
## 9. Performance budgets (first render, interaction latency, image sizes)
## 10. Alternatives considered (layout/navigation options and why rejected)
```

**Screen spec format** (one file per screen, `design/screens/<SCR-ID>.md`; written to be graded from a screenshot plus
the view hierarchy/DOM):

```markdown
# SCR-<nn> · <Screen name>
Purpose: <one sentence> · Requirement IDs: UX-0nn, A11Y-0nn · Flows: F1 step 3
Reference: <taste anchor / wireframe path> · Viewports: iPhone 15 (393×852 pt), iPhone SE (375×667 pt) | web 360/768/1280

## Regions (top → bottom; layout assertions are binding)
| Region | Contents | Layout assertions |
| R1 Nav bar | title "<text>", trailing action "Add" | title uses token type.title; trailing action hit area ≥44×44 pt |
| R2 Content | grid of OutfitCard | 2 columns on ≥375 pt; gutters = space.m; cards equal width ±1 pt |
| R3 CTA | primary button "Create outfit" | bottom-most interactive element; full width within safe-area insets minus space.l |

## State matrix (each state gets a screenshot in verification)
| State | Trigger | What renders | Assertions |
| populated | ≥1 item | R2 grid | no text truncation at default size |
| empty | 0 items | illustration + "No outfits yet" + CTA | CTA visible without scrolling on iPhone SE |
| loading | first fetch >300 ms | skeleton cards (≤6) | no layout shift >1 card height when content arrives |
| error | fetch fails | inline message + "Retry" | message states cause + action; Retry is focusable first |
| partial/offline | cached data, no network | banner "Offline — showing saved outfits" | banner does not cover R3 |
| AX largest text | Dynamic Type AX5 / 200% zoom | single-column | primary labels not truncated; no overlap |
| dark mode | system dark | same layout | contrast pairs from tokens meet threshold |

## Interactions
| Element | Gesture/input | Result | Feedback (haptic/animation ≤ motion.fast) |

## Accessibility
VoiceOver order: R1 title → R1 action → R2 cards (label "<name>, <n> items") → R3 · Traits · Reduced-motion variant.

## Verification hooks (for the visual/UX lane)
Screenshot names: SCR-nn-<state>-<viewport>.png · Machine checks: target sizes, truncation, overlap, token usage ·
Vision rubric items: hierarchy clear, one primary action, matches reference within stated tolerance.
```

### 7.6 Migration / extraction plan skeleton

```markdown
# Migration plan · <from: system/project> → <to: platform service>
Links: CHARTER.md (class ≥ L) · SPEC.md (domain MIG, PAR) · ADRs · Status: …

## 1. Outcomes & non-goals (what gets better; what we deliberately do not replicate)
## 2. Current-state map (discovery output, with file:line / endpoint / dashboard pointers)
| Capability | Where implemented | Callers | Data owned | Side effects | Undocumented behaviour? |
## 3. Behaviour inventory → disposition
| Behaviour | Evidence | Keep / Drop / Change | Req ID (PAR-nnn for kept, MIG-nnn for changed) | Owner |
## 4. Target state
Component ownership after cutover, API contracts (links), data model mapping old → new.
## 5. Seams & transitional architecture
Where traffic/data is intercepted (proxy, feature flag, dual-read), the temporary code involved, and its removal ID.
## 6. Data import
Import list · Do-not-import list (transient queues, locks, caches, derived indexes) · ID mapping table · validation
and quarantine rules · idempotency: run twice ⇒ identical canonical result, zero extra provider work.
## 7. Parity criteria (binary, each with an oracle)
| PAR ID | Criterion (e.g. same response schema, status codes, token accounting within ±0.5%, p95 ≤ old) | Method (replay / shadow / contract test) | Sample & duration | Pass threshold |
## 8. Cutover steps (each with go/no-go check and owner)
1. Freeze config; export legacy durable truth.
2. Import; run invariants and restore check.
3. Shadow: new system runs with side effects suppressed; compare outputs.
4. Canary: <n%> or one tenant/route; monitor <signals> for <duration>.
5. Promote: new system becomes the sole owner. Disable legacy owner BEFORE enabling the new owner's side effects.
6. Observe acceptance window <duration>.
7. Retire legacy; keep bounded rollback snapshot until <date>.
Invariant: at no step do old and new both own the same external side effect without an explicit suppression fence.
## 9. Rollback plan
Trigger conditions (metric thresholds) · steps · data reconciliation for writes made during the new-owner period ·
maximum rollback time · who decides.
## 10. Risks, security (secrets/keys/accounts moving), comms, and STOP conditions
```

**Research + website variant** (replaces the design docs for shape 5; the screen-spec format still applies to page
templates):

```markdown
# Content & site brief · <site>
## Research questions (each → finding with source URL + access date, confidence)
## Audiences & jobs-to-be-done | ## Positioning statement | ## Messaging hierarchy (message → proof point → source)
## Sitemap (tree, ≤3 levels) + synthetic tree test for top 5 tasks
## Page inventory | Page | Template (SCR id) | Goal | Primary CTA | Content owner | Claims (IDs with sources) |
## Blog: cadence, categories, post template, author/byline rules · ## Docs: IA, versioning, search, contribution flow
## SEO/metadata rules, analytics events (IDs), accessibility level (WCAG 2.2 AA)
## STOP: unsourced comparative claim; personal data of team members without consent
```

### 7.7 Spec-review rubric + reviewer prompt skeleton

Each item is binary (PASS / FAIL / N-A) with evidence. Severity decides whether a FAIL blocks the gate.

| # | Criterion | FAIL looks like | Default severity |
|---|---|---|---|
| R1 | Goals and non-goals are outcome-shaped. Non-goals are plausible goals that were deliberately excluded | "System shouldn't crash" as a non-goal; no non-goals | major |
| R2 | Every success metric has a threshold and a measurement method | "fast", "delightful" with no number or rubric | blocker for P1 outcomes |
| R3 | Assumptions are labelled, with reversal cost; high-cost ones were asked or flagged | Silent defaults; an assumption stated as fact | major |
| R4 | STOP conditions exist and cover data loss, spend, external publication and dual ownership | No STOP list on L/XL | blocker (L/XL) |
| R5 | Every normative requirement has a stable ID, an oracle kind and a falsifiable criterion | Untestable requirement; prose behaviour without an ID | blocker for P1 |
| R6 | No ambiguity: undefined terms, vague quantifiers, pronouns without referent, "etc.", contradictory statements | "support large files"; two sections disagree | major (blocker if it changes P1 behaviour) |
| R7 | Failure coverage: every external boundary has ≥1 unwanted-behaviour requirement with a fixture | Happy path only | blocker (L/XL) |
| R8 | Ownership and consistency: one owner per record and side effect; designs don't contradict the spec; the registry matches the spec | Two components write the same table; API field differs between spec and design | blocker |
| R9 | Frontend verifiability: every P1 screen has regions with layout assertions, a full state matrix and a11y minimums | "Clean layout"; missing empty/error states | major (blocker for P1 screens) |
| R10 | Backend soundness: platform limits cited; data store per entity justified; idempotency and retries defined; security/privacy/cost addressed | D1 used for blobs; no retention for PII | blocker for PII/money |
| R11 | Right-sized: depth matches class; no requirement exists only to exist; no gold-plating beyond goals | 40 criteria for a one-screen change; features contradicting non-goals | major |
| R12 | Migration only: behaviour inventory, parity criteria with thresholds, cutover ordering, rollback triggers | "Same as before"; no rollback | blocker |

Gate rule: PASS when there are no open blockers and every major is FIXED, RESIDUAL (with rationale) or DEFERRED (with
milestone). Round caps come from §4.1. Findings without a failure scenario are *questions* and cannot block (matches
lane 06 verdict 3).

```markdown
You are an adversarial specification reviewer. You did not write these documents and you have no access to the
author's reasoning. Assume the spec is broken until the documents prove otherwise.

Inputs (read all): CHARTER.md, SPEC.md, requirements.yaml, <design docs>, rubric (below), prior disposition log if
round > 1 (re-review ONLY changed sections and their dependents).
Lens for this run: <ambiguity & testability | failure modes & limits | ownership & consistency | UX verifiability |
security & privacy | right-sizing>.

Procedure:
1. For each rubric item in your lens, decide PASS / FAIL / N-A and cite section + requirement ID.
2. For each FAIL, write a finding: {id, rubric item, location, quote, failure scenario (what an implementer would
   build wrongly, or which test could pass while the outcome fails), severity, proposed minimal fix}.
3. Don't invent new product scope. Put concerns outside the rubric under "outside-contract observations".
4. Cap: at most 12 findings, most severe first. Merge duplicates.
Output: a markdown table of rubric verdicts, then the findings list, then outside-contract observations. No
preamble.
```

### 7.8 Intake prompt skeleton (charter author) and discovery prompt skeleton

```markdown
Role: mission intake. Turn a short direction into CHARTER.md. Do not design or implement.
Direction (verbatim): "<prompt>"
Available evidence: <repo path | none>, research notes in research/, human availability: <interactive | headless>.

Steps:
1. Classify ambiguity (A0–A2) and blast radius (B0–B3); derive the class (SPEC-R01). Justify in one line.
2. If brownfield: read the discovery digest (don't re-read the repo yourself unless a pointer is missing).
3. Draft every charter section. Fill each gap with an assumption {id, statement, reversal cost, verification}.
4. Choose ≤3 questions, ONLY about high-reversal-cost assumptions. Each is multiple-choice with ★default and a
   one-line consequence per option. If headless, apply the defaults and mark them ASSUMED (unconfirmed).
5. Write STOP conditions: the generic four + shape-specific ones.
6. Write the artefact plan (which docs, review-round cap).
Rules: non-goals must be plausible goals; metrics must be measurable with a named method; no technology choices in
Outcome/Goals; the total charter ≤ 2 pages for M, ≤ 4 for L/XL.
Output: CHARTER.md content, then the question block (or "No questions: all assumptions low/med reversal cost").
```

```markdown
Role: discovery sweeper (read-only). Area: <path or subsystem>.
Produce a conventions digest with pointers (path:line) for: existing spec/requirement IDs and registry files; test
framework, naming and citation style; design tokens/components; routing/IA; data stores and owners; external
integrations; build/deploy commands; anything that contradicts the charter's assumptions A-*.
Rules: facts only, each with a pointer. Label inferences. ≤ 400 lines. No recommendations.
```

## 8. Anti-patterns & failure modes

1. **Interview fatigue.** 20–60 questions before anything happens
   (https://velvetshark.com/stop-prompting-claude-code-let-it-interview-you). For this user it recreates the very
   typing burden the skill exists to remove. Fix: assumption-first intake, ≤3 questions per round.
2. **The opposite: silent assumption.** Picking a platform, a datastore or a retention policy without recording it.
   Fix: SPEC-R05 plus rubric R3. Every default is visible and reversible.
3. **Sledgehammer specs.** Stories and dozens of criteria for a small bug
   (https://www.thoughtworks.com/insights/decoder/s/spec-driven-development). Fix: classify first; S gets a task card.
4. **Prose requirements with no oracle.** "The app should feel fast and intuitive." It can't be graded, so the loop
   ends at "handled enough" (post, "Mistakes" list). Fix: SPEC-R11, rubric R2/R5.
5. **EARS theatre.** Perfect "WHEN … SHALL" sentences with no named test. EARS standardises phrasing and does not make
   criteria executable (https://dev.codemyspec.com/blog/kiro-specs-explained). Fix: an oracle kind on every ID and
   validator rule 3.
6. **Model-maintained registries.** Letting an LLM keep thousands of registry lines in sync invites silent drift and
   costs tokens every edit. Fix: generated registry plus a script validator (SPEC-R15). Models only fill references.
7. **One e2e test as the oracle for everything.** Many IDs point to one broad scenario, so the registry looks complete
   while contracts go unverified (arcwell TEST-003, `arcwell-spec.md:1278`). Fix: validator rule 7.
8. **Design docs as implementation manuals.** Pages of "we will create file X" with no alternatives
   (https://www.industrialempathy.com/posts/design-docs-at-google/). Fix: SPEC-R17. With no alternatives, write a
   task list instead.
9. **Pasting full schemas and API definitions into design docs.** They go stale and bloat context. Fix: link the
   contract file and sketch only the trade-off-relevant parts (same source).
10. **Platform surprises.** Discovering D1's 10 GB ceiling or the per-invocation query limit mid-build
    (https://developers.cloudflare.com/d1/platform/limits/index.md). Fix: the limits table in the backend design.
11. **Unverifiable screen specs.** "Modern card layout." The visual verifier then grades taste by vibes. Fix: region
    assertions + state matrix (§7.5).
12. **Tokens in the wrong place.** Project tokens embedded in a global Skill (post step 13) diverge from the code.
    Fix: a DTCG token file in the repo.
13. **Uncapped spec review.** Round after round of finding-and-fixing, with fixes introducing new findings (arcwell M1,
    eighteen rounds, `review-process-amendment.md:3-5`). Fix: caps, stop on severity, re-review only changed sections.
14. **Human gate at every phase.** Kiro-style approvals per phase stall days-long autonomous runs
    (https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html). Fix: human gates at the charter questions
    and irreversible actions only; everything else is gated by reviewers and scripts.
15. **Spec rot.** Code changes, the spec doesn't; the next agent trusts the stale spec. Fix: SPEC-R16 (same change
    set) plus a change log in the spec.
16. **Spec-as-source ambition.** Regenerating code from specs on every change. It's unproven and it destroys
    hard-won fixes. Fix: spec-anchored only.
17. **Carrying intake context into implementation.** The implementer inherits the interview's biases and a bloated
    context. Fix: SPEC-R24, a fresh context loaded from files
    (https://velvetshark.com/stop-prompting-claude-code-let-it-interview-you; https://code.claude.com/docs/en/best-practices.md).
18. **Faking live acceptance.** Marking "14 real mornings" or "real users complete in 3 minutes" as passed from a
    simulation. Fix: `live-only` status stays PENDING until actually run (`arcwell/REQUIREMENTS.yaml:16-20`).
19. **Cost traps.** Fable 5.1 rereading the whole repo during intake (use Sonnet discovery digests); reviewers given
    full transcripts (give artefacts only); regenerating the entire spec for a one-requirement change (edit the delta);
    `/goal` evaluator silently defaulting to Haiku, which violates the constraint (configure it,
    https://code.claude.com/docs/en/goal.md).
20. **Migration by "same as before".** Specifying parity with undocumented legacy behaviour wholesale
    (https://martinfowler.com/bliki/StranglerFigApplication.html). Fix: behaviour inventory with keep/drop/change.

## 9. Open questions / risks for the synthesizer

1. **The question budget is a judgement call.** "≤3 per round, ≤2 rounds" is this lane's opinion, grounded in the
   user's stated pain (brief §1), not in a measured study. The synthesizer may want a user-facing flag
   (`--interview deep`) that switches to the Thariq-style long interview for greenfield XL work, where the user may
   *want* to shape taste.
2. **The `/goal` evaluator model.** goal.md says the evaluator uses the configured "small fast model", which "defaults
   to Haiku on the Claude API" (https://code.claude.com/docs/en/goal.md). This lane didn't verify the exact setting
   name or whether it can be pointed at Sonnet 4.6. If it can't, the skill should gate completion with a Stop-hook
   script or a Sonnet verifier sub-agent instead of `/goal`. Lanes 01/02 may have the setting.
3. **Registry weight for M missions.** A hand-written YAML plus a validator script means the skill must ship (or
   generate) a validator in the target repo's language. Ship a small language-agnostic script (e.g. Python or Node)
   under `templates/`. Decide which runtime the skill may assume.
4. **Test citation convention.** The validator needs a detectable way for tests to cite IDs: the test name prefix
   (`api_007_…`, as arcwell does, `REQUIREMENTS.yaml:15`), a comment tag, or a docstring. Pick one default and allow
   repo-local override. This overlaps with lane 04 (testing).
5. **Scope classifier reliability.** SPEC-R01's thresholds are untested. Misclassifying XL as M is the expensive
   error. The keyword upgrade guard (§5) mitigates it, but the synthesizer should consider always running the
   classifier at medium effort and letting the orchestrator override upward.
6. **Kiro bugfix-spec details come from a search snippet** (https://kiro.dev/docs/specs/bugfix-specs/). The kiro.dev
   docs render client-side and returned no text when fetched. The Current/Expected/Unchanged structure is corroborated
   by a second snippet (verdent.ai), but exact field names may differ.
7. **Apple target-size figure.** 44 pt is widely cited, but this lane fetched only the HIG accessibility JSON (text
   sizes, Dynamic Type ≥200%), not the page carrying the 44 pt figure. Treat it as practitioner-sourced until lane 05
   confirms. Viewport sizes in the screen-spec template (393×852, 375×667 pt) are illustrative and unverified here.
8. **Spec-anchored maintenance is cultural, not just procedural.** Arcwell needed demotions after review
   (`requirements-curation.yaml:10-15`). Agents *will* mark requirements implemented optimistically. The synthesizer
   should make status promotion a verifier-owned action (lane 06), never a maker action.
9. **Human gates vs autonomy.** SPEC-R07 lets headless runs proceed on defaults. For irreversible external actions
   (publishing a website, payments, deleting data) the STOP list must still block. The synthesizer should confirm the
   harness can pause for approval, or else fail closed.
10. **Overlap with siblings.** Screen-spec verification hooks (lane 05), review round caps and disposition vocabulary
    (lane 06), test-oracle traceability (lane 04) and STATE/STATUS files (lane 07) all touch these templates. The
    synthesizer should keep one canonical vocabulary: FIXED/REFUTED/RESIDUAL/DEFERRED/CONTESTED is adopted here to
    match lane 06.
11. **Kiro product status.** The practitioner source says AWS is winding down Amazon Q Developer in favour of Kiro
    (https://dev.codemyspec.com/blog/kiro-specs-explained). This is secondary and unverified. It doesn't affect the
    skill, which borrows patterns, not the tool.

## Sources

Web (fetched unless marked "snippet"):

- https://code.claude.com/docs/en/best-practices.md — explore → plan → implement → commit; verification checks; skip the plan for one-sentence diffs.
- https://code.claude.com/docs/en/goal.md — `/goal` evaluator semantics, condition-writing guidance, Haiku default.
- https://velvetshark.com/stop-prompting-claude-code-let-it-interview-you — interview technique, fresh-session hand-off.
- https://raw.githubusercontent.com/github/spec-kit/main/spec-driven.md — SDD philosophy, continuous consistency validation.
- https://raw.githubusercontent.com/github/spec-kit/main/templates/spec-template.md — prioritised independent stories, FR/SC IDs, NEEDS CLARIFICATION, Assumptions.
- https://alistairmavin.com/ears/ — EARS patterns and ruleset.
- https://dev.codemyspec.com/blog/kiro-specs-explained — Kiro spec workflow, EARS limits, steering files (practitioner).
- https://kiro.dev/docs/specs/bugfix-specs/ — bugfix spec Current/Expected/Unchanged (snippet).
- https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html — spec-first / spec-anchored / spec-as-source; tool critique.
- https://www.thoughtworks.com/insights/decoder/s/spec-driven-development — "sledgehammer to crack a nut" (snippet).
- https://www.industrialempathy.com/posts/design-docs-at-google/ — design-doc anatomy, when not to write one.
- https://raw.githubusercontent.com/joelparkerhenderson/architecture-decision-record/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md — Nygard ADR template.
- https://www.rfc-editor.org/rfc/rfc8174.txt — BCP 14 capitalisation rule.
- https://developers.cloudflare.com/d1/platform/limits/index.md — D1 limits, single-threaded DBs, scale-out guidance.
- https://developers.cloudflare.com/workers/platform/storage-options/index.md — Cloudflare storage product map.
- https://developers.cloudflare.com/reference-architecture/ — Cloudflare reference architectures index (snippet).
- https://developer.apple.com/tutorials/data/design/human-interface-guidelines/accessibility.json — HIG accessibility (Dynamic Type ≥200%, 17 pt default).
- https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html — WCAG 2.2 SC 2.5.8 (snippet).
- https://buildwithaccess.com/blog/touch-target-size-mobile-accessibility-wcag — 24 px / 44 pt / 48 dp summary (snippet, secondary).
- https://www.designtokens.org/tr/2025.10/format/ — DTCG format module 2025.10 (snippet).
- https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/ — DTCG stable announcement (snippet).
- https://martinfowler.com/bliki/StranglerFigApplication.html — incremental modernisation, seams, transitional architecture.
- https://www.nngroup.com/articles/card-sorting-tree-testing-differences/ — card sorting vs tree testing (snippet).
- https://www.verdent.ai/guides/agents/kiro-spec-driven-development — corroborates bugfix.md current/expected/unchanged (snippet).

Workspace evidence (read-only):

- `arcwell/docs/product/arcwell-spec.md` — lines 13-38 (how to use; completion criteria), 27-29 (requirement language),
  52-63 (outcome IDs), 80-89 (non-goals), 93-144 (principle IDs), 1252-1338 (verification architecture, registry,
  TEST-001..008), 1911-1960 (import and cutover), 2004-2026 (decision ledger), 2030-2076 (definition of done, STOP
  conditions).
- `arcwell/REQUIREMENTS.yaml` — lines 1-20 (generated-file header, entry schema, live checks PENDING).
- `arcwell/requirements-curation.yaml` — lines 1-15 (curation rules, status vocabulary, demotions), 52-56 (T-IDs).
- `arcwell/docs/operations/review-process-amendment.md` — lines 3-31 (eighteen rounds, consolidated review).
- `arcwell/docs/operations/m1-*-disposition.md` — 18 files (glob).
- Sibling lanes: `research/mission-skill/02-model-routing-cost.md` lines 8-11, 18-24, 43-49;
  `research/mission-skill/06-verification-adversarial-review.md` lines 9-64; `05-frontend-visual-ux-verification.md`
  lines 321-361 (heading scan only).

