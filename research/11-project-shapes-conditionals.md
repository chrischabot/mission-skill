# R11 — Project shapes, scope sizing, and the conditional rule system

Lane: project-shape taxonomy, classification, S/M/L/XL sizing, trait → obligation rules, per-shape pipelines.

## 1. Executive summary & strong opinions

This lane defines how one skill recognises *what kind of work* it has been handed and adapts its whole process to it.
The design is three independent axes plus a composition step:

- **Shape** (what kind of work): picks the phase pipeline and its special gates.
- **Size** (S/M/L/XL, how much work): sets the amount of process: document depth, review rounds, swarm width,
  budget, human checkpoints.
- **Traits** (which surfaces and risks are present): each trait adds obligations through `IF trait THEN obligations`
  rules, whatever the size.
- **Composition**: one primary shape plus secondary shapes plus traits, merged by fixed ordering and precedence
  rules into a single `mission/PROFILE.yaml` that every later phase reads.

Strong opinions, each actionable:

1. **Classify on three axes, never one.** One "project type" label mixes up how much work there is with how dangerous
   it is. A one-line fix in payment code is *small* but *risky*. It needs payment obligations (idempotency tests,
   security lens, human approval before deploy), not an XL spec. The skill MUST record shape, size and traits
   separately.
2. **Risk traits add gates, not ceremony.** This disagrees with R03's rule "XL if B3" (money/irreversible → XL,
   `03-spec-design.md:341`). Money, PII, auth and irreversibility switch on *trait obligations* at every size. Size is
   driven by breadth, uncertainty and duration. Otherwise small risky fixes carry XL paperwork and review fatigue.
3. **Thirteen shapes, not five.** The five user examples are GREENFIELD, BUGHUNT, FEATURE, MIGRATION and WEBSITE. The
   skill also needs REFACTOR, UPGRADE, DATA, PERF, INFRA, SECURITY, RESEARCH/SPIKE and OPS, because each has a *different
   first gate*. AI/LLM work, incidents and docs-only work are traits or variants, not shapes.
4. **Every shape has a "gate zero" that must pass before any code changes.** BUGHUNT: REPRODUCED. MIGRATION /
   REFACTOR / UPGRADE: PARITY-BASELINE (a validated judge exists). PERF: BASELINE-MEASURED. GREENFIELD multi-platform:
   CONTRACT-FROZEN. FEATURE: CONVENTIONS-MAPPED. WEBSITE: CLAIMS-SOURCED. Anthropic's migration kit says it
   plainly: "No judge, no exit condition" (https://github.com/anthropics/code-migration-kit-with-claude-code).
5. **Behaviour-preserving and behaviour-changing work never share a change set.** When a migration and a feature are
   combined ("move the gateway and add caching"), the move reaches parity first and the feature follows as a separate
   milestone. This is Fowler's expand/migrate/contract applied to missions
   (https://martinfowler.com/bliki/ParallelChange.html).
6. **Classification runs as a script plus a cheap model.** A repository probe (manifests, directories, SDK imports,
   deploy configs) writes `signals.json`. Sonnet 4.6 at medium effort maps signals and prompt to a profile, and
   hard-coded forcing rules override it (for example, a `migrations/` path being touched forces `has_database`).
   Fable 5.1 does not spend tokens on classification; the orchestrator only confirms it.
7. **Ask the human only when the answer forks the pipeline.** Ask when two plausible profiles differ in primary shape,
   by two or more size steps, or on an irreversible trait, *and* ten minutes of reading cannot settle it. Ask at most
   3 multiple-choice questions, each with a recommended default. Headless runs record the default as ASSUMED.
8. **Unknown traits are probed, not assumed.** `touches_pii: unknown` triggers a detection task (grep schemas and
   upload paths) before Spec. A trait left unknown at the Spec gate is treated as *present* for verification
   obligations and *absent* for design ceremony.
9. **Re-classify at every phase gate.** New signals appear mid-mission: the "UI bug" turns out to be a data corruption.
   A newly discovered trait adds its obligations at once. Size can go up freely but goes down only with a recorded
   reason (R03 SPEC-R02, `03-spec-design.md:342-344`).
10. **Obligations are data, not prose.** The trait→obligation table ships as `references/traits.yaml`. Each obligation
    has an ID, a gate, a size floor, and an owning reference file. The planner concatenates the obligations that apply
    into `acceptance.json` and PLAN.md, so nothing depends on the orchestrator remembering a paragraph.
11. **Deduplicate by strongest parameter.** When several traits require the same kind of obligation (review lens,
    model tier, trial count), keep one instance at the maximum parameter. Never stack three separate security reviews
    because auth, payments and PII all fired.
12. **Multi-platform greenfield is a sequence of L-missions behind a contract milestone.** M0 = contracts + testkit +
    walking skeleton, as arcwell did (`arcwell/docs/operations/milestone-ledger.md:10`). Platform lanes fan out only
    after CONTRACT-FROZEN passes.
13. **Migrations are strangler milestones with a rollback column on every step.** Every cutover step records evidence
    and a rollback. It is reversible until a named final step with a retention window, as in arcwell's cutover runbook
    (`arcwell/docs/operations/cutover-runbook.md:4,8,20`). Shadow comparison comes before any traffic shift
    (https://github.com/github/scientist).
14. **S missions are the default and must stay cheap.** "If you could describe the diff in one sentence, skip the
    plan" (https://code.claude.com/docs/en/best-practices). The S pipeline is: task card, failing check, fix, gate run by
    a verifier, one review pass. No PROFILE ceremony beyond five lines.
15. **The website shape is research-first and claims-bound.** Every public factual or comparative sentence traces to a
    RESEARCH.md source ID, or it is cut. Taste decisions (name, hero, visual direction) go through a tournament, not a
    single maker's opinion.

## 2. Claim check

The post barely mentions project shapes. Its claims that matter for this lane are about which kinds of work Fable
suits, the cost of using the top tier on small work, long-running work, and classifier-sensitive domains.

| # | Post claim (brief §3) | Verdict | Evidence | What the skill does |
|---|---|---|---|---|
| C1 | Fable's headline use case is "large migrations, complex implementations, multi-day autonomous coding sessions" (step 01) | **Plausible, partly verified.** Anthropic's migration kit exists and describes a Bun Zig→Rust port of more than 1M lines. Search summaries (not the primary blog page, which could not be fetched) say Fable 5 and Opus 4.8 were used | https://github.com/anthropics/code-migration-kit-with-claude-code ; https://claude.com/blog/ai-code-migration (page larger than the 500KB fetch limit) | MIGRATION and REFACTOR at L/XL use Fable 5.1 for orchestration and rulebook/plan synthesis only. Translation and fixing lanes stay on Sonnet/Opus, following the kit's implementer + two reviewers + fixer structure |
| C2 | "Fable 5 on tasks Sonnet 4.6 would handle (doc updates, simple refactors, lint fixes)" is a mistake (Mistakes list) | **Verified in spirit** (a cost argument, not a benchmark). Pricing verified by R02: Fable $10/$50, Sonnet $3/$15 per MTok (`99-synthesis-notes.md:69`) | R02 lane | Size S and shape DOCS/UPGRADE-patch default to Sonnet 4.6 as the session model. Fable only when the user is already running it as the session model, never spawned for S |
| C3 | "Running long sessions on a laptop (days-long needs cloud infra: CMA or Routines)" | **Plausible-unverified as a requirement.** Routines and headless `claude -p` exist (R01/R09, `99-synthesis-notes.md:14,97`), but nothing says laptops cannot do days-long work | R01, R09 | Trait `long_running` requires resumable file state (HANDOFF/STATE), per-phase sessions, and a degradation path: Routines, then `claude -p` script, then manual resume. It never *requires* cloud |
| C4 | Opus 4.8 is the fallback for classifier blocks in "cyber, bio, chem, distillation" (steps 04, 14) | **Partly verified, list differs.** R01 verified categories cyber, bio, frontier_llm, reasoning_extraction, general_harms, and "no chem" (`99-synthesis-notes.md:13`) | R01 lane | Trait `classifier_sensitive_domain` routes exploit/pentest/offensive work to Opus 4.8 *upfront*, logs fallback events, and uses a BLOCKED-SAFETY state. The SECURITY shape defaults its audit lanes to Opus |
| C5 | "No vision-verify on visual tasks (UI, dashboards, design fidelity)" is a mistake | **Verified as recommended practice.** Claude Code best practices: "Verify UI changes visually… take a screenshot of the result and compare it to the original" | https://code.claude.com/docs/en/best-practices | Traits `has_web_frontend`, `has_ios`, `has_android`, `design_quality_matters` add the R05 G1–G3 stack with size-scaled matrices |
| C6 | Routines on API/GitHub triggers: "CI fails → investigate; Sentry alert → triage" (step 09) | **Plausible-unverified in this lane** (R01 verified Routines exist) | R01 | Shape OPS encodes recurring triage as a Routine *when available*, degrading to a scheduled `claude -p`. Unattended runs end in a draft PR, never a merge (R08, `99-synthesis-notes.md:113`) |
| C7 | "Days-long runs with checkpoints. Each major phase can be a separate worktree. A failed phase doesn't poison the rest." (step 08) | **Plausible.** Worktree isolation is documented. "Failed phase doesn't poison" is design advice, not a guarantee | https://code.claude.com/docs/en/common-workflows (worktrees section) | XL milestones get a branch/worktree per milestone, and milestone gates merge only on PASS |
| C8 | Dynamic Workflows "classify-and-act (route the task to the right model based on a classifier)" (step 07) | **Pattern verified** as Anthropic's "routing" workflow; the Dynamic-Workflows primitive names are unverified (R01, `99-synthesis-notes.md:11`) | https://www.anthropic.com/engineering/building-effective-agents | The classification step here is a routing workflow: script signals, then a Sonnet classifier, then pipeline selection. It works without Dynamic Workflows |
| C9 | "Outcomes… Best for ML training, long-running migrations, multi-day research" | **Plausible-unverified for the migration fit** (R01 verified Outcomes exists) | R01 | MIGRATION's parity judge is harness-independent: a script with an exit code. Outcomes or `/goal` may wrap it, but never replace it |

Two things the post misses that this lane adds: (a) *no shape taxonomy at all*. The post treats every task as "long
autonomous coding", but the evidence says the right first gate differs by shape (repro, judge, baseline, contract).
(b) *No scaling-down*. Anthropic's own best practices say planning "adds overhead" and should be skipped when the
diff fits in one sentence (https://code.claude.com/docs/en/best-practices). A skill that always runs 14 steps will be
abandoned for small work, which is exactly the user's complaint in reverse.

## 3. Deep findings

### 3.1 Behaviour-preserving change: the evidence says incremental, judged, reversible

- **Big-bang replacement usually fails.** Fowler: simple-replacement plans "go down in flames most of the time",
  because existing behaviour is hard to specify and much of it isn't wanted anyway. The remedy is to find *seams*,
  replace small components, and accept transitional architecture as a cost worth paying
  (https://martinfowler.com/bliki/StranglerFigApplication.html). For the skill, MIGRATION's plan unit is a *seam*,
  not a file.
- **Expand / migrate / contract** keeps the system releasable at every phase and applies to DB refactors, canary and
  blue-green deploys, and remote API evolution. Its failure mode is never contracting: "you might end up in a worse
  state than you started" (https://martinfowler.com/bliki/ParallelChange.html). For the skill, every MIGRATION, DATA
  and UPGRADE plan MUST end with an explicit CONTRACT milestone (removing the old path) that has its own gate, or with a
  DECISIONS.md entry that keeps both paths on purpose.
- **Shadow comparison before switching.** GitHub Scientist runs the old code as *control* and the new code as
  *candidate*, compares their results in production, and always returns the control's result
  (https://github.com/github/scientist). Stripe's online migration pattern is dual-write → backfill from a snapshot →
  switch reads, with shadow comparison → retire the old writes (https://stripe.com/blog/online-migrations, via
  summaries). For the skill, `cross_repo_migration` and `data_migration` add a SHADOW-PARITY gate before any traffic or
  read switch.
- **Canary well.** A canary needs a subset deployment, an evaluation process, and integration into the release flow.
  Shared state (for example a shared cache) makes canary metrics meaningless
  (https://sre.google/workbook/canarying-releases/, snippets). Cloudflare Workers supports percentage traffic splits
  across immutable versions, with rollbacks
  (https://developers.cloudflare.com/workers/versions-and-deployments/gradual-deployments/). For the skill, a
  `deploy_to_production` trait on a Workers target uses gradual deployment plus a written rollback command. The canary
  check list MUST name any shared state that could hide a difference.
- **arcwell already does this**: the cutover runbook has Evidence and Rollback columns, SHADOW enablement, "reversible
  until step 10", and a bounded 30-day rollback snapshot (`arcwell/docs/operations/cutover-runbook.md:4,8,14,20`). The
  skill should ship this table format verbatim (§7).

### 3.2 Anthropic's migration kit is the strongest primary source for MIGRATION / REFACTOR at scale

From https://github.com/anthropics/code-migration-kit-with-claude-code:
- **Feasibility first**: a read-only report in which "Don't migrate" is a valid outcome. For the skill, MIGRATION and
  REFACTOR at L/XL start with a FEASIBILITY gate.
- **"Make sure you have a judge before Step 1… No judge, no exit condition."** The judge is either the existing suite
  (if it tests the public surface) or a portable parity harness, "validated… against the original *and* against
  deliberately broken code". This is the PARITY-BASELINE gate zero, including its oracle-bite check.
- **"If two agents could answer differently, it goes in the rulebook."** For swarmed behaviour-preserving work, the
  shape needs a RULEBOOK.md before fan-out, and stress-tests it with a bake-off plus a pilot.
- **Deterministic ordering**: the dependency map "is a deterministic script, not agent judgment". Expensive operations
  are banned "by configuration, not request" (`.claude/settings.json` denies). "Every referee has a price, and the
  price decides its position in the loop." For the skill, each pipeline table below says where each referee sits: cheap
  typecheck inside the unit loop, expensive E2E at the milestone.
- **Done-gate**: the parity referee passes AND the original suite has been re-run on the original code with zero
  inherited failures. This separates bugs the migration introduced from bugs that were already there.

### 3.3 Upgrades: small and continuous beats heroic

GitHub upgrades Rails weekly through a scheduled automated PR and credits this with avoiding large migrations
(https://github.blog/engineering/architecture-optimization/building-github-with-ruby-and-rails/, snippet). The
dual-boot technique runs the test suite against the current and the next framework version at the same time
(https://github.com/fastruby/upgrading-rails-the-dual-boot-way). For the skill, UPGRADE sizes by *version distance*:
one major version is M, more than one major version is L with stepwise waypoints, never a single jump. Where the
ecosystem allows it (a lockfile or conditional dependency), dual-running is the parity judge. Finish with an OPS
suggestion: automate the recurring upgrade.

### 3.4 Scaling process to scope is an explicit Anthropic recommendation

Claude Code best practices give four phases (Explore, Plan, Implement, Commit), but warn that "Plan mode is useful, but
also adds overhead", and say planning pays off when you are "uncertain about the approach, when the change modifies
multiple files, or when you're unfamiliar with the code" (https://code.claude.com/docs/en/best-practices). The same page
orders gate strength: an in-prompt check, a `/goal` condition (re-checked by a separate evaluator every turn), a Stop
hook (overridden after 8 consecutive blocks), and a verification subagent or workflow. For the skill, size S uses
in-prompt checks plus one verifier pass. M and above use the Stop hook running `mission/check.sh`. L and above add
verifier subagents at every phase gate.

### 3.5 AI/LLM features need evals, not only tests

Anthropic's eval guidance: outcomes are "the final state in the environment", not what the agent says. Code-based
graders are fast and objective but brittle. Model-based graders need "calibration with human graders". Capability
suites and regression suites are separate. Multiple trials are needed because outputs vary. Evals written early resolve
spec ambiguity ("Two engineers reading the same initial spec could come away with different interpretations")
(https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents). For the skill, `has_ai_llm_features`
requires an eval suite (tasks, trials, graders) as part of Spec, before the prompt is written.

### 3.6 Platform facts that drive trait obligations

- **Cloudflare**: `@cloudflare/vitest-plugin` runs tests inside the Workers runtime locally (Miniflare) with isolated
  per-test-file storage and multi-Worker support
  (https://developers.cloudflare.com/workers/testing/vitest-integration/). D1 uses versioned SQL migration files
  (https://developers.cloudflare.com/d1/reference/migrations/) and Time Travel restore to any minute in the last 30
  days (https://developers.cloudflare.com/d1/reference/time-travel/). For the skill, `has_database` on D1 requires a
  migration test against a local D1 and a recorded Time Travel bookmark (restore point) before any remote apply. AI
  Gateway covers analytics, caching, rate limiting and model fallback (https://developers.cloudflare.com/ai-gateway/),
  so example 4's parity inventory must include those behaviours if the old gateway had them.
- **Apple**: Apple says to "continue to use XCTest for user interface tests and Performance Tests"
  (https://developer.apple.com/documentation/xctest). XCUIAutomation drives the app's UI
  (https://developer.apple.com/documentation/XCUIAutomation). Apps that support account creation "must also include an
  option in the app to initiate account deletion"
  (https://developer.apple.com/support/offering-account-deletion-in-your-app). For the skill, `has_ios` together with
  `touches_auth` makes in-app account deletion a P1 requirement at Spec, not a late App Review surprise.
- **Security**: OWASP ASVS gives graded verification requirements, including session management
  (https://owasp.github.io/www-project-application-security-verification-standard/,
  https://asvs.dev/v5.0.0/V7-Session-Management/). For the skill, `touches_auth` imports a small, named ASVS checklist
  subset as acceptance items, instead of asking a reviewer to "check security".

### 3.7 arcwell as an XL multi-component specimen

arcwell (read-only) has a Workers hub (D1/R2/Workflows), an optional execution worker, a Rust macOS companion, shared
Rust types, TS contracts, devtools, a deterministic testkit, and frozen fixtures (`arcwell/README.md:9-17`). Its
Milestone 0 was "Contracts, testkit, and repository spine", with a TS↔Rust conformance corpus as "the executable schema
authority" (`arcwell/docs/operations/milestone-ledger.md:10,16`). Tests are split by kind (unit, property, integration,
scenario, security, performance, contracts, mutation), and live canaries are separate, spend-bounded commands
(`arcwell/package.json:20-37`, `arcwell/README.md:40`). For the skill, it confirms two rules for multi-platform XL work:
the contract milestone comes first, and test kinds are separate so each size or trait can switch on only the kinds it
needs. It also shows the cost of uncapped review (18 rounds; R06 in `99-synthesis-notes.md:59`), which is why the size
table caps rounds.

### 3.8 Reconciling sibling lanes (for the synthesizer)

- **Size signals.** R01 sizes by duration, files and components (`01-orchestration-control.md:466-471`). R03 sizes by
  ambiguity × blast radius, with money/irreversible → XL (`03-spec-design.md:338-341`). This lane: size = breadth,
  uncertainty, duration and coordination. Blast-radius *risk* moves into traits (§6.1). R03's B3 "multi-platform"
  stays a size driver; "money/irreversible" does not.
- **Fan-out numbers.** R01/R09 give *writers per wave* S2/M4/L8/XL12 (`99-synthesis-notes.md:98`). R02 gives
  *concurrent agents* S3/M5/L8/XL15 (`99-synthesis-notes.md:77`). They measure different things and both can stand:
  writers ≤ ceiling_writers, total concurrent ≤ ceiling_total.
- **Review caps.** R06 caps implementation review at S1/M2/L3/XL4. R03 caps spec review at S0/M1/L2/XL2(+1). The
  sizing table below uses both, labelled separately.

## 4. Opinionated spec for the skill

Key words MUST / SHOULD / MAY are used in the RFC 2119 sense. Rule IDs are `SHP-*` (shapes), `CLS-*`
(classification), `SZ-*` (size), `CMP-*` (composition).

### 4.1 The mission profile

- **SHP-R01 MUST.** Before any artefact other than BRIEF.md, the orchestrator writes `mission/PROFILE.yaml` (template
  §7.1) with: `primary_shape`, `secondary_shapes[]`, `size`, `size_justification`, `traits{name: present|absent|unknown,
  evidence}`, `gate_zero`, `obligations[]` (IDs expanded from `references/traits.yaml`), `open_classification_questions[]`.
  For size S the profile is 5 lines inside the task card.
- **SHP-R02 MUST.** Exactly one primary shape. The primary shape is the one whose *done criterion* is the mission's
  done criterion. Secondary shapes contribute phases and gates but not the definition of done.
- **SHP-R03 MUST.** Trait obligations apply at every size unless the obligation row says `floor: M` or higher.
- **SHP-R04 SHOULD.** Shapes are closed-vocabulary (§4.2). If nothing fits, use the nearest shape plus a DECISIONS.md
  entry. Do not invent a shape mid-mission; propose one at retro (the promotion rules of R07 apply).

### 4.2 Shape catalog (paste-ready)

| ID | Shape | Typical prompt | Repo signal | Gate zero (before code changes) | Primary deliverable | Usual size | Variants / merged-in |
|---|---|---|---|---|---|---|---|
| GRN | Greenfield product | "build an app that…", "from scratch" | empty or near-empty repo; no deploy config | CHARTER-SIGNED (+ CONTRACT-FROZEN if multi-platform) | deployed walking skeleton → milestones | L–XL | multi-platform; single-platform; internal tool |
| FEA | Feature in existing product | "add X to our…", "new dashboard/page/endpoint" | existing app, tests, CI | CONVENTIONS-MAPPED (codebase map + reuse list) | merged feature behind flag with journeys | S–L | UI feature; API feature; integration |
| BUG | Bug hunt / fix | "fix", "broken", "crash", "flaky", "why does" | failing test, issue link, logs | REPRODUCED (deterministic or statistical) | fix + frozen regression test + sibling sweep | S–L | **incident mode** (`live_incident`: mitigate first); flaky test |
| MIG | Service migration / extraction / consolidation | "move X into Y", "extract", "consolidate", "replatform" | two codebases or services named | PARITY-BASELINE (validated judge) + FEASIBILITY | new home serving traffic, old path retired | L–XL | extraction; consolidation; vendor swap |
| REF | Refactor / modernization / language port | "clean up", "restructure", "port to", "modernize" | large legacy module, no behavior ask | PARITY-BASELINE | same behavior, new structure | M–XL | language port (kit six steps); architecture lint adoption |
| UPG | Dependency / framework / runtime upgrade | "upgrade", "bump", "migrate to vN", CVE notice | lockfile, deprecation warnings | PARITY-BASELINE (suite green on old version) | new version, suite green, deprecations cleared | S–L | toolchain; OS SDK (iOS target); security patch |
| DAT | Schema change / data migration / backfill | "add column", "backfill", "move data", "normalize" | migrations dir, ORM schema | RESTORE-POINT + DATA-PROFILED | applied migration, verified row-level invariants | S–L | expand/contract schema; bulk transform; store swap |
| PRF | Performance optimization | "slow", "p95", "memory", "bundle size", "cost" | benchmarks, profiles, perf budgets | BASELINE-MEASURED (numeric, repeatable harness) | metric moved past target, no regression | S–L | latency; memory; cost/tokens; startup |
| INF | Infra / deploy / CI / observability | "set up CI", "deploy", "Terraform", "alerts" | workflows, IaC, wrangler/Docker config | DRY-RUN-GREEN (plan/preview output captured) | pipeline or infra change with rollback | S–M | CI; deploy pipeline; monitoring |
| SEC | Security audit / hardening | "audit", "pentest", "harden", "threat model" | auth code, secrets, public endpoints | THREAT-MODEL (assets, entry points, attacker) | findings with dispositions + fixes + controls | M–L | audit-only; remediation; compliance prep |
| WEB | Research + marketing website / content | "website", "landing page", "blog", "docs site" | none or static site generator | CLAIMS-SOURCED (research log + message hierarchy) | deployed site, sourced claims, docs IA | M–L | marketing site; docs site; **docs-only** (S–M, no site build) |
| RSR | Research / spike / prototype | "investigate whether", "compare", "prototype", "market position" | often none | QUESTION-FRAMED (decision question + timebox + decision criteria) | decision memo/ADR (+ throwaway prototype) | S–M | technical spike; market research; throwaway prototype |
| OPS | Recurring ops / triage | "every morning…", "whenever CI fails…", "triage issues" | CI logs, alerting | RUNBOOK-DRY-RUN (one supervised run) | Routine/script + runbook + eval cases | S–M | CI triage; dependency bot; digest |

Merges and splits, with reasons: **AI/LLM features** are a trait, because they always sit inside GRN or FEA. The eval
obligations attach to whatever builds the feature. **Incident** is BUG in a mode that reorders phases (mitigate before
root-cause) but keeps the same done criterion. **Docs-only** is WEB without the site build. **Prototype** is RSR,
because its deliverable is a decision, and prototype code MUST NOT be merged without re-entering as FEA or GRN.
**REF vs MIG**: MIG crosses a deploy or repository boundary and has traffic to cut over; REF does not.

### 4.3 Classification procedure

- **CLS-R01 MUST, step 1: probe.** Run a deterministic repository probe (script in §7.3) that writes
  `mission/signals.json`: file and language counts, manifests, directory markers, SDK imports, deploy targets, test
  harness presence, CI files, commit history depth, and matches from a sensitive-path grep. No model is involved.
- **CLS-R02 MUST, step 2: extract prompt signals.** Verbs, named systems, platforms, audiences, deadlines, "from
  scratch" vs "our existing", explicit non-goals.
- **CLS-R03 MUST, step 3: classify.** A classifier agent (Sonnet 4.6 medium) receives the prompt, `signals.json` and
  the shape/trait catalogs, and returns the profile with per-field `confidence: high|medium|low` and cited evidence.
- **CLS-R04 MUST, step 4: apply forcing rules** that override the model (table below). Forcing rules only *add*
  traits or *raise* size. They never remove.
- **CLS-R05 MUST, step 5: resolve low confidence.** For each low-confidence field that *forks the plan* (CLS-R06), spend
  ≤10 minutes on targeted reading or probing. If it is still unresolved, ask (CLS-R07) or assume (headless).
- **CLS-R06 (fork test).** A field forks the plan if changing it alters the primary shape, moves size by ≥2 steps,
  switches an irreversible trait (`deploy_to_production`, `data_migration`, `touches_payments`,
  `cross_repo_migration`), or changes the platform set.
- **CLS-R07 MUST.** Ask at most 3 multiple-choice questions per round, each with a recommended default and the cost of
  being wrong, and at most 2 rounds (aligned with R03, `99-synthesis-notes.md:85`). Non-forking unknowns become
  `A-nn` assumptions and are never asked.
- **CLS-R08 MUST.** Re-run classification at every phase gate, and immediately whenever a worker reports a
  `trait_discovered` in its return block. The diff between the old and new profile goes to DECISIONS.md.

**Signal → shape/trait table (forcing rules in bold):**

| Signal (source) | Implies | Confidence |
|---|---|---|
| repo has <~20 source files and no deploy config, and the prompt says "build/create" (probe + prompt) | GRN | high |
| prompt names an existing product area + repo has app code | FEA | high |
| stack trace, failing test ID, "crash/flaky/regression" (prompt) | BUG | high |
| two systems named with move/extract/consolidate verbs | MIG + `cross_repo_migration` | high |
| **`*.xcodeproj`, `Package.swift` with iOS platform, or "iOS/iPhone/SwiftUI" in prompt** | **`has_ios`** | forcing |
| **`build.gradle(.kts)` with `com.android.application`, or "Android" in prompt** | **`has_android`** | forcing |
| **`wrangler.toml/jsonc`, Dockerfile + deploy workflow, `vercel.json`, IaC dirs** | **`deploy_to_production`: unknown → probe environments** | forcing (unknown) |
| **`migrations/`, `schema.prisma`, `drizzle.config.*`, `*.sql` in diff path** | **`has_database`** | forcing |
| backfill/transform of existing rows, "move data" (prompt) | `data_migration` | high |
| **imports of auth libraries or session/cookie/JWT code in the touched paths** | **`touches_auth`** | forcing |
| **Stripe/RevenueCat/StoreKit/payment SDK imports in touched paths** | **`touches_payments`** | forcing |
| upload handlers, user profile schema, photos, email/phone fields | `touches_pii` | medium → probe |
| Anthropic/OpenAI/Workers AI SDK, prompt files, "AI/LLM/agent" in prompt | `has_ai_llm_features` | high |
| JSX/TSX/Vue/Svelte/HTML templates; "page/dashboard/UI" | `has_web_frontend` | high |
| "website/blog/landing/docs", marketing copy | WEB + `public_facing_content` | high |
| "market/competitors/state of the art", unfamiliar platform/API | `needs_external_research` | medium |
| numeric latency/memory/cost target; "slow" | PRF or `performance_sensitive` | high |
| "exploit", "pentest", "malware", "CVE PoC", bio/chem protocols | `classifier_sensitive_domain` | forcing |
| estimated >1 session of work, or size ≥ L | `long_running` | derived |
| consumer-facing UI, brand, "beautiful/polished", App Store launch | `design_quality_matters` | medium |

### 4.4 Scope sizing S/M/L/XL

- **SZ-R01 MUST.** Score four dimensions 0–3 and record them:
  - **Breadth (B)**: 0 = one file or one behaviour. 1 = one component, or one vertical slice inside one app. 2 = several
    services, a new data model, a public contract, or two repositories. 3 = two or more client platforms built together,
    or three or more services/repos.
  - **Uncertainty (U)**: 0 = approach known. 1 = details unknown, approach known. 2 = open design questions, or an
    unfamiliar codebase or platform. 3 = the problem can't be framed yet (no repro, no judge, research needed to state
    the goal).
  - **Duration (D)**, human-equivalent: 0 = under half a day. 1 = up to ~3 days. 2 = 1–4 weeks. 3 = more than a month.
  - **Coordination (C)**: 0 = one writer. 1 = parallel lanes on disjoint files. 2 = frozen contracts between lanes, or
    internal consumers. 3 = external users or parties, app-store release, or a multi-team cutover.
- **SZ-R02 MUST.** `base = max(B, D)` mapped 0→S, 1→M, 2→L, 3→XL. Add **one** step if U = 3 or C = 3 (capped at XL).
  Risk traits never change size (opinion 2). When the size is uncertain, choose the larger for *verification* and the
  smaller for *ceremony* (R01, `01-orchestration-control.md:473-474`).
- **SZ-R03 MUST.** At XL, each milestone is sized on its own (usually L or M) and runs that size's toggles.
  XL-only toggles apply to the cross-milestone layer.

**Size → toggles (paste-ready; cells cite the owning lane):**

| Toggle | S | M | L | XL |
|---|---|---|---|---|
| Typical | typo, one-line bug, small endpoint | dashboard, bounded bug hunt, one-major upgrade | multi-component feature, migration, website with research | multi-platform product, platform consolidation |
| Spec depth (R03) | task card | charter-lite + mini spec + registry | charter + spec (domain IDs) + designs + ADRs | L + milestone gates + generated registry + STOP list |
| Design | none | short (≤2 pages) | full, ≥2 alternatives | per milestone + architecture review before M1 |
| Spec review rounds (R03) | 0 | 1 | 2 | 2 (+1 only for new-section blockers) |
| Impl review cap (R06) | 1 pass | 2 | 3 + consolidated | 4 per milestone + cross-milestone before release |
| Writers per wave / total concurrent (R09 / R02) | 2 / 3 | 4 / 5 | 8 / 8 | 12 / 15 |
| Research depth (R10) | inline lookups ≤3 | ≤10 queries, one researcher | 15–30 queries, 2–4 angle lanes + skeptic | standing RESEARCH.md, per-milestone refresh, recheck-by dates |
| Memory files (R07) | none (PR description + 1 inbox line) | STATE + STATUS + INBOX | full set + Stop & PreCompact hooks | `state/*.md` split, SubagentStop hook, weekly retro |
| Gate mechanism (§3.4) | in-prompt check + 1 verifier pass | Stop hook → `mission/check.sh` + verifier at Verify | verifier subagent every phase gate | L + milestone release verifier |
| Human checkpoints (R01) | irreversible actions only | + notify at Spec | spec sign-off, irreversible design, release | + per-milestone summary |
| Budget soft/hard (R02) | $8 / $20 | $50 / $120 | $300 / $700 | $1,500 / $3,500 |
| Iteration cap per loop (R01) | 3 | 5 | 8 | 8 per task, 20 hard max |
| Session plan | one session | 1–3 sessions, HANDOFF at end | per-phase sessions, HANDOFF every session | milestone worktrees; Routine or `claude -p` continuation |
| Orchestrator model (R02) | session model (Sonnet 4.6 by default) | Fable 5.1 medium, or Opus 4.8 high (Lean profile) | Fable 5.1 medium, high at intake/spec/adjudication | Fable 5.1 high |

### 4.5 Composition rules (when shapes and traits combine)

- **CMP-R01 MUST, canonical phase order.** Merge all phases into R01's order: 0 Intake, 1 Research, 2 Spec, 3 Design,
  4 Plan, 5 Build, 6 Verify, 7 Review, 8 Release, 9 Retro. Shape-specific gates are *inserted* (for example REPRODUCED
  between Research and Spec), never reordered.
- **CMP-R02 MUST, secondary-shape ordering.** (1) RSR first; its decision can change every other field. (2) Shapes
  that capture a baseline (MIG, REF, UPG, DAT, PRF) establish their gate zero before any shape that changes behaviour
  (FEA, GRN) touches shared code. (3) SEC's threat model enters at Design, not after Build. (4) INF's deploy pipeline
  enters with the walking skeleton for GRN. (5) OPS comes last; it automates something that already exists.
- **CMP-R03 MUST, split preserving from changing.** Behaviour-preserving and behaviour-changing edits go in different
  milestones and PRs, with the preserving one first. A parity failure in a mixed PR cannot be attributed to either.
- **CMP-R04 MUST, deduplicate.** Obligations with the same ID merge. Parameters take the maximum (trial counts, review
  tier, sample sizes, iteration caps). Review *lenses* merge into one panel rather than separate reviews.
- **CMP-R05 MUST, precedence on conflict.** (1) safety and irreversibility controls (human approval, restore point,
  rollback) > (2) correctness oracles (parity, repro, evals) > (3) user-facing quality (visual, UX, content) > (4) cost
  and speed. Every conflict resolved this way goes to DECISIONS.md.
- **CMP-R06 SHOULD, known conflicts and resolutions.**
  - `deploy_to_production` (small frequent deploys) vs `data_migration` (stable windows): use expand/contract, deploying
    between phases, and apply the contract only after the read path has switched and been verified.
  - `design_quality_matters` (tournaments, iteration) vs `touches_payments` (frozen, platform-standard flows): run
    tournaments on non-payment surfaces only. Payment UI follows the platform-standard sheet.
  - `long_running` + unattended vs `deploy_to_production`: an unattended run never deploys to production. It queues
    BLOCKED-HUMAN and keeps working on other tasks.
  - `classifier_sensitive_domain` vs "Fable orchestrates": route the sensitive lanes to Opus 4.8 upfront, and keep the
    orchestrator out of the payload (it gets summaries only).
  - `cross_repo_migration` + a feature request: the feature becomes a post-parity FEA milestone (CMP-R03).
- **CMP-R07 MUST, budget.** Shape phase allocations follow R02's split (plan/spec/arch 15%, research 10%,
  implementation 45%, verify/review 20%, reserve 10%). Trait obligations are costed at Plan. If their estimate exceeds
  the reserve, re-plan or raise size, and never skip them silently.

### 4.6 Re-classification triggers

Re-run CLS at once when: a worker returns `trait_discovered`; an estimate is exceeded by more than 2×; a repro shows
the defect lives in a different layer or shape (a UI bug that is really a data corruption → add DAT); gate zero can't
be established (no judge → insert a "build the judge" milestone; kit Quick start item 5,
https://github.com/anthropics/code-migration-kit-with-claude-code); the user changes scope; or a classifier refusal
occurs (add `classifier_sensitive_domain`).

## 5. Model & effort assignment

Classification is cheap and high-leverage. A wrong profile misroutes the whole mission, but the input is small
(prompt + `signals.json`, a few thousand tokens). So a mid-tier model plus deterministic forcing rules, with a blind
second opinion only where the stakes are large.

| Role | S | M | L | XL | Cost reasoning | Guard that protects the downgrade |
|---|---|---|---|---|---|---|
| Repository probe | script | script | script | script | Zero tokens; deterministic | Probe self-test: fixture repos with known markers (§7.3) |
| Shape/trait/size classifier | Sonnet 4.6 low | Sonnet 4.6 medium | Sonnet 4.6 medium | Sonnet 4.6 high | Small input; the catalog tables do the heavy lifting | Forcing rules (CLS-R04) override; blind second classifier at L/XL; escaped-trait metric |
| Blind second classifier | — | — | Opus 4.8 medium (no access to the first profile) | Opus 4.8 medium | About $0.10–$0.50 per run at this input size (inference from R02 prices); cheap insurance for L/XL | Disagreement on any forking field → orchestrator adjudicates, and asks the human if it still forks |
| Trait detection probes (`unknown` → present/absent) | inline | Sonnet 4.6 low | Sonnet 4.6 medium | Sonnet 4.6 medium | Grep-and-read work; volume fan-out | Must return file:line evidence. No evidence means `unknown`, never `absent` |
| Obligation expander | script | script | script | script | `traits.yaml` → acceptance stubs; no judgement | Schema validation; every present trait has ≥1 obligation in PLAN |
| Pipeline planner (phases, milestones, gate placement) | orchestrator inline | Opus 4.8 high | Fable 5.1 high | Fable 5.1 high | Plan errors are the costliest rework (R02 planner row, `99-synthesis-notes.md:78`) | Plan critique by a different model (Opus 4.8 high when the planner is Fable); gate-zero-before-code lint |
| Clarifying-question composer | orchestrator inline | orchestrator inline | orchestrator inline | orchestrator inline | Needs the whole profile in context; ≤3 questions | CLS-R06 fork test must name the fork each question resolves |
| Re-classification on trigger | Sonnet 4.6 medium | Sonnet 4.6 medium | Sonnet 4.6 medium | Opus 4.8 medium | Triggers are rare | Profile diff logged; size decreases need a recorded reason |
| Retro classification audit | — | 1 in 5 missions: Opus 4.8 medium | every mission: Opus 4.8 medium | every milestone: Opus 4.8 medium | Compares the predicted profile with what the mission actually needed | Miss of the same trait twice → new forcing rule (R08 "recurs twice → mechanical control", `99-synthesis-notes.md:111`) |

Rules:
- **MDL-R01 MUST NOT** use Fable 5.1 for classification or trait probing. Its value is in planning and adjudication,
  not pattern matching over manifests.
- **MDL-R02 MUST** treat a classifier output that lacks cited evidence for a present trait as `unknown`, which triggers a
  probe.
- **MDL-R03 SHOULD** downgrade the L classifier to Sonnet 4.6 low only after R01's downgrade experiment (3/3
  agreement, `01-orchestration-control.md:458-460`). The blind second classifier stays.
- **MDL-R04 MUST** give a mission with `classifier_sensitive_domain` lanes whose default is Opus 4.8. The classifier
  itself runs on Sonnet over *descriptions*, never over exploit payloads.
- Shape-specific worker/verifier routing is owned by R02/R04/R05/R06/R08/R09. §6 names only the deviations each shape
  forces.

## 6. Project-shape conditionals

This section is the lane's main deliverable: the full trait→obligation rule table (§6.1), the per-shape pipelines
(§6.2–6.4), how each shape scales by size (§6.5), and five worked examples (§6.6). Obligation IDs are stable. The
floor is the smallest size at which an obligation applies (`S+` = always). Obligations above their floor scale up as
noted.

### 6.1 Trait → obligation rule table, part A: surfaces

| Trait | IF present THEN (obligations) | Floor → scaling | Gate(s) it feeds | Method owner |
|---|---|---|---|---|
| `existing_codebase` | **EC-1** read-only codebase map → `CONVENTIONS.md` (commands, patterns, reusable components, test harness location) before design. **EC-2** reuse existing patterns unless DECISIONS.md says otherwise. **EC-3** run affected-module regression suites mapped from touched paths, not the whole world. **EC-4** pre-existing failures are recorded at baseline and never block (R06). | EC-1 S+ (S: 10-line digest) → L: map by a reader lane. EC-3 M+ | CONVENTIONS-MAPPED | R09 reader, R04 |
| `no_test_harness` (existing code, weak or no tests on touched paths) | **NT-1** characterization tests of the current behaviour on touched paths before edits, frozen. **NT-2** do not mass-generate tests: 1 oracle + ≤2 edge cases per touched behaviour (R04 B-rules). | S+ (S: one characterization test) | PARITY-BASELINE (lite) | R04 |
| `has_web_frontend` | **WF-1** screen spec + tokens (existing product: extracted tokens + reference screenshots) before UI code. **WF-2** G1 deterministic checks (axe WCAG, geometry probe, console errors). **WF-3** G2 vision verifier on a fixed viewport matrix. **WF-4** G3 UX walkthrough of changed journeys. **WF-5** Playwright journeys asserting outcomes on seeded data. | WF-2 S+; WF-3 S+ (1 viewport) → L: 3 viewports × light/dark; WF-4 M+; WF-5 M+ (L 3–7 journeys, XL ≤12) | Verify: VISUAL, A11Y, JOURNEYS | R05, R04 |
| `has_ios` | **IO-1** SwiftUI state matrix: Light/Dark, largest Dynamic Type accessibility size, smallest and largest supported device. **IO-2** snapshot/screenshot matrix via simulator with status-bar override. **IO-3** XCUITest golden flows (launchArguments seeding, erased simulator). **IO-4** HIG conformance review lens. **IO-5** `performAccessibilityAudit` (iOS 17+) with justified suppressions. **IO-6** App Store readiness checklist: privacy details, privacy manifest, account deletion if accounts exist. **IO-7** per-lane simulator in swarms. | IO-1/IO-2 S+ (S: 1 device × light) → L: full matrix; IO-3 M+; IO-4 M+; IO-6 at Release when shipping | Verify: VISUAL-IOS, XCUITEST; Release: STORE-READY | R05, R04, R09 |
| `has_android` | **AN-1** state matrix (light/dark, font scale 200%, small and large screen). **AN-2** screenshot tests. **AN-3** instrumented golden flows (Espresso/Compose UI test). **AN-4** Material guidelines lens. **AN-5** Play data-safety readiness at Release. | Same floors as `has_ios` | as iOS | R05, R04 (Android specifics unverified in this lane) |
| `multi_platform` (derived: ≥2 of web/iOS/Android/backend built together) | **MP-1** contract milestone M0: API schema file as single source of truth, generated clients or shared types, contract tests on *both* sides. **MP-2** walking skeleton (auth → one core flow → backend round-trip, deployed to dev) before feature fan-out. **MP-3** platform lanes fan out only after CONTRACT-FROZEN. Contract changes return BLOCKED(contract-change). **MP-4** cross-platform journey parity table (same journey IDs on each client). | S+ contract file (S: shared fixture); MP-2 M+ | CONTRACT-FROZEN, SKELETON-LIVE | R01, R03, R09 |
| `has_backend_api` | **BA-1** every endpoint has request/response schema + ≥1 unwanted-behaviour requirement (invalid input, authz failure). **BA-2** offline, credential-free test run (network guard). Workers: `@cloudflare/vitest-plugin` in-runtime tests. **BA-3** idempotency and retry semantics stated for every mutating endpoint. **BA-4** platform limits table with sources in design (for example D1 limits). | BA-1/BA-2 S+; BA-3 M+; BA-4 L+ | Verify: CONTRACT, INTEGRATION | R03, R04 |
| `published_api` (consumers you don't control) | **PA-1** compatibility check against the previous schema (breaking-change diff). **PA-2** expand/contract for breaking changes, with a deprecation window. **PA-3** changelog + versioning decision in DECISIONS.md. | S+ | Review: COMPAT | R03 |
| `has_database` | **DB-1** migration files versioned and applied to a local/ephemeral DB in tests. **DB-2** up-migration tested on a production-shaped fixture. Down-migration or restore procedure documented. **DB-3** a single owner per table/entity (R03). **DB-4** D1: record a Time Travel restore point before remote apply. | DB-1 S+; DB-2 M+; DB-4 S+ for remote apply | Release: RESTORE-POINT | R03, R04 |
| `data_migration` (transforming or moving existing production data) | **DM-1** data profile first (row counts, null/dup/edge distributions) → DATA-PROFILED. **DM-2** invariants written as executable queries (counts, sums, referential integrity) run before and after. **DM-3** expand/contract. For live systems: dual-write → backfill → shadow read comparison → switch reads → contract. **DM-4** dry run on a snapshot copy with timing. **DM-5** human approval before production apply. **DM-6** rollback or restore rehearsal. | DM-1/2/5 S+; DM-3/4 M+; DM-6 L+ | DATA-PROFILED, SHADOW-PARITY, H-APPROVE | this lane (Stripe pattern), R01 |
| `concurrency_or_distributed_state` | **CD-1** state machines with illegal transitions listed. **CD-2** model-based property tests + targeted mutation on transition code. **CD-3** worker/fixer tier starts at Opus 4.8 high (R02 ES4). **CD-4** failure injection (crash points, duplicate delivery). | CD-1 M+; CD-2/4 M+; CD-3 S+ | Verify: PROPERTY, MUTATION | R04, R02, R08 |
| `third_party_integrations` | **TP-1** all providers behind a port with a deterministic fake + oracle-bite per adapter. **TP-2** contract goldens from recorded real responses (sanitised). **TP-3** live canary as a separate, spend-bounded command, PENDING until evidence exists. | TP-1 S+; TP-2 M+; TP-3 L+ or at Release | Verify: CONTRACT; Release: CANARY | R04, arcwell `README.md:40` |

### 6.1 (cont.) Part B: risk, content and process traits

| Trait | IF present THEN (obligations) | Floor → scaling | Gate(s) it feeds | Method owner |
|---|---|---|---|---|
| `touches_auth` | **AU-1** named ASVS subset as acceptance items (session, credential storage, authz per resource). **AU-2** negative tests: cross-tenant/other-user access denied for every new resource. **AU-3** security lens on Opus 4.8 high in the review panel. **AU-4** middleware/ordering invariants captured as tests. **AU-5** `has_ios` + account creation → in-app account deletion requirement. | AU-1 M+ (S: AU-2 + AU-3 only); AU-2/3 S+; AU-5 S+ | Review: SECURITY; Verify: AUTHZ-NEG | R06, R04, Apple 5.1.1(v) |
| `touches_payments` | **PY-1** idempotency keys and webhook replay/duplicate tests. **PY-2** money as integer minor units or decimal type, asserted by property tests. **PY-3** sandbox-only in CI. Live payment actions are H-APPROVE. **PY-4** security lens + state-machine mutation testing. **PY-5** no tournament/visual experimentation on payment UI (CMP-R06). | S+ | Verify: PROPERTY, MUTATION; Release: H-APPROVE | R04, R06 |
| `touches_pii` | **PI-1** data inventory: fields, purpose, retention, deletion path, who can read. **PI-2** logs and telemetry redaction test. **PI-3** no real PII in fixtures, research logs or model prompts (synthetic data). **PI-4** retention/deletion requirement in spec. Photos and media get a storage-access review. **PI-5** check the retention terms of any cloud/Routine path the data would flow through (post Mistakes list). | PI-2/3 S+; PI-1/4 M+; PI-5 when `long_running` uses cloud runs | Spec: PRIVACY; Verify: REDACTION | R03, R07 |
| `has_ai_llm_features` | **AI-1** eval suite before the prompt: ≥20 tasks (L: ≥50) with outcome-based graders first, model graders calibrated on ≥3 good + 3 bad examples. **AI-2** N≥3 trials per task, report pass@k and pass^k. **AI-3** separate capability and regression suites. **AI-4** cost/latency per task budget tracked. **AI-5** prompt-injection and unsafe-output cases for user-controlled input. **AI-6** model IDs pinned; provider fallback tested with a fake. | AI-1 S+ (S: ≥5 golden cases, 1 trial); AI-2/3 M+; AI-5 S+ if user input reaches the model | Spec: EVALS-DEFINED; Verify: EVAL-THRESHOLD | R04, Anthropic evals post |
| `public_facing_content` | **PC-1** every factual or comparative claim bound to a RESEARCH.md source ID + access date. Unsourced → cut or rephrased as opinion. **PC-2** fact-check verifier pass (Opus 4.8 medium for public claims, R06). **PC-3** voice and messaging guide frozen before content lanes. **PC-4** link check, build, Lighthouse/CWV budget, meta/OG, sitemap. **PC-5** legal-sensitive statements (team bios, customer names, pricing, security claims) → human sign-off. | PC-1/2 S+; PC-3 M+; PC-4 S+ for sites; PC-5 S+ | CLAIMS-SOURCED; Release: H-APPROVE (publish) | R10, R06, R05 |
| `needs_external_research` | **ER-1** research questions written before searching. **ER-2** RESEARCH.md entries with reliability grade and recheck-by date. **ER-3** L+: angle lanes + skeptic. Claims sampled and re-verified. **ER-4** vendor/platform facts that drive design are cited in DESIGN.md next to the decision. | ER-1/2 S+; ER-3 L+ | Research gate | R10, R07 |
| `performance_sensitive` | **PF-1** numeric budget with a measurement method in spec. **PF-2** repeatable benchmark harness committed before changes, ≥10 runs, variance reported. **PF-3** regression check in CI or at Verify. **PF-4** iOS: on-device measurement for final numbers (simulator for trend only). | PF-1 S+; PF-2 M+ (S: before/after of 5 runs); PF-3 M+ | BASELINE-MEASURED; Verify: PERF-BUDGET | R04, R08 |
| `cross_repo_migration` | **XR-1** feasibility report (a "don't migrate" outcome is allowed). **XR-2** behaviour parity inventory of the old service (endpoints, side effects, config, quotas, caching, logging, error shapes) as acceptance checks captured *before* the move. **XR-3** portable parity judge validated against the old service and against a deliberately broken build. **XR-4** strangler milestones: characterize → shadow → dual-run compare → switch behind a flag/percentage → contract (retire). **XR-5** runbook table with Evidence + Rollback per step and a rollback window. **XR-6** secrets/keys movement gets a security lens. **XR-7** consumer inventory with a switch plan per consumer. **XR-8** no behaviour change until parity (CMP-R03). | XR-2/3/5/8 S+; XR-1/4/7 M+ | FEASIBILITY, PARITY-BASELINE, SHADOW-PARITY, CUTOVER (H-APPROVE), CONTRACTED | this lane, migration kit, arcwell runbook |
| `deploy_to_production` | **DP-1** preview/staging deploy exercised by smoke checks before prod. **DP-2** written rollback command, tested once. Workers: gradual deployment percentage + rollback. **DP-3** canary check list naming shared state that could mask differences. **DP-4** prod deploy is H-APPROVE (permissions ask/deny + hook, not prose). **DP-5** post-deploy verification with PENDING-LIVE until evidence. **DP-6** monitoring/alert for the new path. | DP-1/2/4/5 S+; DP-3/6 M+ | Release: H-APPROVE, LIVE-VERIFIED | R01, SRE canarying, CF docs |
| `infra_or_ci_changes` | **IC-1** plan/dry-run output captured and reviewed. **IC-2** workflow and secret changes need human approval. Frozen-path protection on `.github/workflows`, `.claude/`, hooks. **IC-3** no swarm (R09). **IC-4** test in a branch pipeline before main. | S+ | DRY-RUN-GREEN; H-APPROVE | R09, R04 |
| `classifier_sensitive_domain` | **CS-1** sensitive lanes default to Opus 4.8. **CS-2** fallback events logged in STATUS. Refusal → BLOCKED-SAFETY. Never rephrase around a refusal. **CS-3** orchestrator receives summaries, not payloads. **CS-4** a human is informed when offensive-security work is in scope. | S+ | — | R02, R01 |
| `long_running` (>1 session) | **LR-1** HANDOFF at every session end or ~60% context. **LR-2** session-start ritual (HANDOFF → STATUS → PLAN → STATE → smoke). **LR-3** milestone branches/worktrees. **LR-4** continuation via Routine → `claude -p` script → manual resume, degrading gracefully. **LR-5** budget ledger reviewed at every phase boundary. | S+ once triggered | Session gates | R01, R07, R02 |
| `unattended` (headless/overnight) | **UN-1** no irreversible actions: queue BLOCKED-HUMAN and continue elsewhere. **UN-2** end in a draft PR, never a merge. **UN-3** `--max-budget-usd` or equivalent cap. **UN-4** pre-allowlisted permissions only. | S+ | — | R01, R08, R02 |
| `design_quality_matters` | **DQ-1** 2–3 reference apps/sites requested or proposed. Tokens before the first screen. **DQ-2** craft rubric thresholds (R05: L/XL mean ≥3.3). **DQ-3** tournament for hero/visual direction/naming (pairwise, position-swapped). **DQ-4** batched blinded human review per milestone. **DQ-5** AI-default tells checklist. | DQ-1/5 M+; DQ-2 S+ at S/M thresholds; DQ-3 M+; DQ-4 L+ | Verify: RUBRIC; Review: HUMAN-BATCH | R05 |
| `localized` | **LO-1** pseudo-locale / longest-language screenshot pass. **LO-2** RTL if supported. **LO-3** no hard-coded strings lint. | LO-3 S+; LO-1/2 M+ | Verify: VISUAL-L10N | R05 |
| `live_incident` (BUG mode) | **LI-1** mitigate first (rollback, flag off), with mitigation ≠ resolution recorded. **LI-2** timeline log. **LI-3** then the full BUG pipeline on the unmitigated build in non-prod. **LI-4** postmortem with a generic control (R08 LSN). | S+ | MITIGATED, then REPRODUCED | R08 |

### 6.2 Per-shape pipeline master table (all 13 shapes)

Phase numbers follow R01 (0 Intake … 9 Retro). Inserted gates are shown in CAPS. Model deviations are relative to
R02's role matrix.

| Shape | Pipeline | Key deliverables | Swarm usage | Model deviations | Done criteria |
|---|---|---|---|---|---|
| GRN | 0 → 1 research (platform limits, reference apps) → 2 CHARTER-SIGNED → 3 design → CONTRACT-FROZEN (M0) → 4 → 5 walking skeleton → SKELETON-LIVE → milestone loops (5–7) → 8 → 9 | charter, spec, backend + frontend design, contract schema, testkit, skeleton, milestone ledger | Fan-out only after M0: backend lane, per-platform client lanes, contract-test lane; design tournament → one writer | charter/spec synthesis Fable 5.1 high; architecture review Opus 4.8 high | all P1 journeys green on each platform against deployed dev/staging; release gates for present traits; human batch review passed |
| FEA | 0 → 1 CONVENTIONS-MAPPED → 2 mini spec (+ metric definitions) → 3 short design → 4 → 5 spine lane then widget lanes → 6 → 7 → 8 behind flag → 9 | CONVENTIONS.md, mini spec, screen specs for new/changed screens, flag, journeys | reader lane for map; spine lane merges first, then ≤4 widget lanes | none beyond defaults | criteria tests + 1–3 journeys green; affected regression suites green; flag-off check green; visual gates for UI |
| BUG | 0 failure record → "check the plug" → REPRODUCED → hypothesis loop (isolate, bisect, differential) → CONFIRMED (two-way intervention) → fix → PROOF (red→green, N clean runs) → sibling sweep → 7 → 9 | failure record, frozen repro test, hypothesis ledger, fix, sweep list, lesson/control | 3–5 hypothesis lanes only if REPRODUCED + ≥3 independent open hypotheses; one writer | investigator Opus 4.8 high for concurrency/memory/vendor; Fable 5.1 high as a hypothesis-space reset after 2 stalled rounds (R08) | repro fails before and passes after in a clean worktree; intermittent: n ≥ ln(α)/ln(1−p) clean runs; sweep dispositioned; suite green |
| MIG | 0 → 1 FEASIBILITY → parity inventory → PARITY-BASELINE (judge validated) → 2 spec (inventory keep/drop/change) → 3 design (target seams, data/secrets move) → 4 strangler milestones → 5 build in new home → SHADOW-PARITY → CUTOVER per consumer (H-APPROVE) → soak → CONTRACTED (old retired) → 9 | feasibility report, parity inventory, judge, runbook (evidence + rollback), consumer switch plan, retirement record | per-module/per-endpoint migration lanes partitioned by the judge; one migration writer per shared interface; readers for inventory | plan/rulebook Fable 5.1 high (L/XL); security lens Opus 4.8 high on secrets; judge author Opus 4.8 high | judge passes on the new path; original suite re-run on the old path with zero inherited failures; all consumers switched; old path retired or kept by a DECISIONS entry; rollback window recorded |
| REF | 0 → 1 PARITY-BASELINE → RULEBOOK (if swarmed) → bake-off + pilot → 5 per-unit implementer + 2 reviewers + fixer → survey build/typecheck → run → parity burn-down → 7 → 9 | judge, rulebook, dependency map (script), manifest queue | homogeneous per-unit fan-out via workflow when ≥10 units; rule amendments queued to the orchestrator | lanes Sonnet 4.6 medium; reviewers on a different model than makers | kit done-gate (§3.2); architecture lint green; no behaviour diff reported by the judge |
| UPG | 0 → 1 changelog/breaking-change research → PARITY-BASELINE (suite green on old version) → 4 waypoint plan (one major at a time) → 5 dual-run where possible → deprecations → 6 → 8 → 9 (suggest OPS automation) | waypoint plan, codemods, deprecation list, lockfile | none for coupled bumps; lockfile bisection lanes when hunting a regression | Sonnet 4.6 high default; Opus 4.8 high for runtime/toolchain breakage | suite green on the new version; zero new deprecation warnings in touched code; lockfile committed; rollback = revert PR |
| DAT | 0 → 1 DATA-PROFILED → invariants as queries → 3 expand/contract design → RESTORE-POINT → dry run on snapshot → H-APPROVE → apply expand → backfill → SHADOW-PARITY (reads) → switch reads → CONTRACTED → 9 | profile, invariant queries, migration files, dry-run timings, restore point id | none (shared schema = no parallel writers, R09) | migration author Opus 4.8 high (R02 ES4) | invariants identical before and after (or diff explained by spec); restore rehearsal documented at L+; contract applied |
| PRF | 0 → 1 BASELINE-MEASURED → profile → hypothesis per hotspot → 5 change → measure (≥10 runs) → regression check → 7 → 9 | harness, baseline report, profiles, before/after table | parallel *experiment* lanes, each in its own worktree with its own runtime; best one merges | analysis Opus 4.8 medium; lanes Sonnet 4.6 high | metric past target with variance reported; no functional regression; perf check committed |
| INF | 0 → 1 → DRY-RUN-GREEN → 5 branch pipeline → H-APPROVE → apply → LIVE-VERIFIED → 9 | plan output, pipeline config, runbook, rollback | none (IC-3) | Opus 4.8 high for secrets/permissions; Sonnet 4.6 medium otherwise | pipeline green on branch and main; rollback tested; secrets not exposed (scan) |
| SEC | 0 → THREAT-MODEL → 1 audit fan-out by lens → findings → refutation pass → 7 dispositions → 5 fixes (each a BUG-lite with repro) → 6 → 9 controls | threat model, finding YAML, dispositions, fixes, controls (lint/hook/test) | parallel read-only audit lanes by lens/surface; one writer per fix | all audit lanes Opus 4.8 high (CS-1); never Fable for exploit reasoning | every blocker/major CONFIRMED finding FIXED with a failing-without-fix test, or accepted-risk DEC; controls added for recurring classes |
| WEB | 0 → 1 research (market, audience, competitors) → CLAIMS-SOURCED → message hierarchy + sitemap + page inventory → 3 visual direction tournament → tokens → 4 → 5 spine shell → page/content lanes (frozen voice guide) → docs IA → 6 build/links/Lighthouse/visual → fact-check → H-APPROVE publish → 9 | RESEARCH.md, positioning memo, messaging guide, sitemap, page specs, site, blog scaffold + launch posts, docs tree | research angle lanes + skeptic; content lanes after the voice guide freezes; naming/hero tournament | research synthesizer Opus 4.8 high (Fable 5.1 high at XL for market strategy); copy Sonnet 4.6 high; fact-check Opus 4.8 medium; UI verifier Opus 4.8 high | site deployed to preview then prod; zero unsourced claims; link check clean; Lighthouse budgets met; docs synthetic tree test ≤3 clicks; human publish sign-off |
| RSR | 0 → QUESTION-FRAMED (decision question, criteria, timebox) → 1 research/prototype → synthesis → skeptic review → decision memo/ADR → 9 | question card, RESEARCH.md, prototype (throwaway branch), decision memo | angle lanes; best-of-N prototypes for taste or feasibility | synthesizer Opus 4.8 high; Fable 5.1 high only for XL strategy synthesis | the decision question is answered with cited evidence and a confidence level; prototype code not merged |
| OPS | 0 → 1 → runbook + classification rules → eval cases from past incidents → RUNBOOK-DRY-RUN (supervised) → schedule (Routine / cron `claude -p`) → 9 weekly eval refresh | runbook skill, eval JSONL, schedule config, digest format | none per run; per-item fan-out only for batch triage | triage classifier Sonnet 4.6 low with a 5% double-classify audit; investigation Sonnet 4.6 high → Opus 4.8 high | dry run matches a human triage on ≥90% of eval cases (inference: threshold proposed by this lane); unattended rules UN-1..4 in force |

### 6.3 Detailed pipelines for the five user shapes (part 1: GRN, BUG, FEA)

**GRN: greenfield multi-platform product** (sized XL; milestones sized L/M)

| Phase / gate | Deliverable | Gate check (who verifies) | Swarm | Models |
|---|---|---|---|---|
| 0 Intake | BRIEF, PROFILE, ≤3 forking questions (platforms, reference apps, data retention) | profile schema valid; forking fields answered or ASSUMED | — | orchestrator Fable 5.1 high; classifier Sonnet 4.6 medium + blind Opus 4.8 medium |
| 1 Research | platform limits table (Workers/D1/R2, iOS target), competitor/reference app notes, API/vendor facts | every design-driving fact has a source + recheck-by date | 2–4 angle lanes + skeptic | lanes Sonnet 4.6 medium; synthesizer Opus 4.8 high |
| 2 CHARTER-SIGNED | charter, spec with domain IDs, acceptance.json, P1 journeys, privacy section | spec review (2 rounds cap); human sign-off at L/XL | — | Fable 5.1 high author; Opus 4.8 high reviewer |
| 3 Design | backend design + ADRs, frontend IA + screen specs + tokens, test strategy, threat model lite | design review Opus 4.8 high; ≥2 alternatives per irreversible choice | proposal tournament for visual direction → one writer | Opus 4.8 high designers |
| M0 CONTRACT-FROZEN | OpenAPI/JSON Schema file, generated Swift client + TS types, contract tests both sides, testkit fakes | contract tests green on both sides; fixtures validated against the schema | contract lane + stub-generation lane | Opus 4.8 medium author; Sonnet 4.6 high tests |
| M1 SKELETON-LIVE | sign-in → one core flow → backend round-trip, deployed to dev; CI; `init.sh` smoke | XCUITest skeleton journey vs dev deploy; smoke script exit 0 | backend lane + iOS lane (disjoint globs, own simulator) | Sonnet 4.6 medium makers; Opus 4.8 medium verifier |
| M2..Mn feature milestones (each an L-mission) | vertical slices per journey | per milestone: criteria tests, visual G1–G3, review ≤3 rounds + consolidated | ≤8 writers per wave after contract freeze | makers Sonnet 4.6 medium → Opus 4.8 high on escalation |
| 8 Release | TestFlight build, prod Worker via gradual deployment, restore point, store readiness | H-APPROVE; LIVE-VERIFIED canary; IO-6 checklist | — | release readiness Opus 4.8 medium; final sign-off Fable 5.1 reading VERIFICATION.md |
| 9 Retro | lessons, skill-promotion candidates, classification audit | lesson cites evidence; audit filed | — | distiller Opus 4.8 high (Fable 5.1 at XL cross-milestone) |

**BUG: deep bug hunt** (usually M; L when U = 3 or it spans layers)

| Phase / gate | Deliverable | Gate check | Swarm | Models |
|---|---|---|---|---|
| 0 Failure record | symptom verbatim, expected/observed, env fingerprint, first seen, blast radius | record complete before any code is touched | — | triage Sonnet 4.6 medium |
| Check the plug | build current, right binary/deploy, env/bindings, test actually runs | checklist evidence | — | Sonnet 4.6 low runner |
| REPRODUCED | repro script/test, one-line failure signature, baseline failure rate | exits non-zero; ≥5 failures or deterministic; frozen path | — | repro builder Sonnet 4.6 high (Opus 4.8 medium for races) |
| Isolate | bisect result, ddmin input, differential runs (local vs preview, simulator vs device) | ≤200 log lines to the orchestrator | differential env lanes (read-only) | Sonnet 4.6 medium |
| Hypothesis loop | ledger: statement, mechanism, prediction, discriminating experiment, raw result | ≥3 hypotheses across layers; FALSIFIED kept; stall after 2 rounds → escalate | 3–5 experiment lanes (each in its own worktree) if the swarm precondition holds | investigator Opus 4.8 high; reset Fable 5.1 high (max 2) |
| CONFIRMED | two-way intervention (break → fails, restore → passes) | separate confirmer agrees | — | confirmer Opus 4.8 medium |
| Fix + PROOF | fix at the confirmed mechanism; red→green in a clean worktree; n clean runs | verifier run; test-diff audit; no catch-ignore/retry/timeout-bump fix | — | fixer Sonnet 4.6 high / Opus 4.8 high cross-component |
| Sweep + review | sibling pattern sweep with dispositions; review 1–2 rounds | every hit dispositioned | sweep readers | Sonnet 4.6 medium + Opus 4.8 blind sample of ≥3 |
| 9 Lesson | regression test + control (lint/hook/type) + generic audit task | lesson cites the ledger | — | distiller Opus 4.8 high |

**FEA: feature in an existing product, e.g. a new dashboard** (usually M)

| Phase / gate | Deliverable | Gate check | Swarm | Models |
|---|---|---|---|---|
| 0 Intake | task card or charter-lite; profile (FEA + `has_web_frontend` + `has_database` read path) | profile valid | — | orchestrator Fable 5.1 medium (Lean: Opus 4.8 high) |
| CONVENTIONS-MAPPED | CONVENTIONS.md: routing, state, data-fetch layer, chart/table components, tokens, test harness, flag system | spot-check of 3 pointers by the orchestrator | 1 reader lane | Sonnet 4.6 medium |
| 2 Mini spec | metric definitions (source table, formula, timezone, refresh cadence, empty/partial states), P1 journeys, authz rule | spec review 1 round | — | Opus 4.8 medium |
| 3 Short design | screen spec + state matrix, query plan with index check, reuse list | review within the spec round | — | Opus 4.8 medium |
| 5 Build | spine (route, layout, data hooks, flag) → widget lanes | per-lane criteria tests; lint/typecheck in the loop | spine first, then ≤4 widget lanes | Sonnet 4.6 medium |
| 6 Verify | criteria tests, 1–3 journeys on seeded data asserting aggregates, G1–G3 visual, affected regression suites, flag-off check | VERIFICATION.md PASS by an independent verifier | — | gate runner Sonnet 4.6 low; vision verifier Opus 4.8 medium |
| 7 Review | panel: correctness + UX; security lens if new data exposure | ≤2 rounds; no CONFIRMED blocker/major | 2 lenses in parallel | Opus 4.8 medium/high |
| 8 Release | flag rollout plan; screenshot summary for the human | H1 only if deploying to prod | — | — |

### 6.4 Detailed pipelines (part 2: MIG, WEB)

**MIG: service migration/extraction, e.g. an AI gateway moving into a core platform service** (usually L)

| Phase / gate | Deliverable | Gate check | Swarm | Models |
|---|---|---|---|---|
| 0 Intake | profile (MIG + `cross_repo_migration`, `has_backend_api`, `has_ai_llm_features`, `touches_auth` for keys, `deploy_to_production`, `third_party_integrations`) | profile valid; forking questions (retire the old project? consumers? downtime tolerance?) | — | Fable 5.1 medium orchestrator |
| FEASIBILITY | read-only report: case for moving, structure-preserving vs redesign, verification cost, verdict | human reads the verdict at L/XL | — | Opus 4.8 high |
| Parity inventory | table of every route, provider, model mapping, retry/fallback, caching, rate limit, logging/analytics field, error shape, config/secret, quota; keep/drop/change per row | inventory reviewer finds no unlisted route in a grep/route dump (script) | 2–4 reader lanes partitioned by module | Sonnet 4.6 medium readers; Opus 4.8 medium review |
| PARITY-BASELINE | judge = recorded request corpus + differential runner (old vs new, normalised responses) using fake providers | judge passes on old vs old; fails on a deliberately broken build (oracle bite) | — | judge author Opus 4.8 high |
| 2–3 Spec + design | target module seams inside the platform, data/secret move plan, consumer switch plan, runbook skeleton | spec 2 rounds; design review + security lens for key custody | — | Opus 4.8 high; security Opus 4.8 high |
| 5 Build (structure-preserving) | new service passing the judge endpoint by endpoint | judge per endpoint in the unit loop (cheap referee inside the loop) | per-endpoint lanes after shared interface/shim lands serially | Sonnet 4.6 medium makers; Sonnet 4.6 high per-item verifier |
| SHADOW-PARITY | new service receives mirrored traffic; the old service still answers; diff report | diff rate ≤ agreed threshold, with every class of difference explained | — | Opus 4.8 medium analyst |
| CUTOVER per consumer | switch via flag/percentage (Workers gradual deployment), runbook row with evidence + rollback | H-APPROVE per step; LIVE-VERIFIED metrics; rollback tested once | — | release readiness Opus 4.8 medium |
| CONTRACTED | old gateway retired or read-only; final export archived; rollback window end date | DECISIONS entry; no traffic on the old path for the window | — | — |
| Post-parity FEA | behaviour changes requested during the move (CMP-R03) | as FEA | as FEA | as FEA |

**WEB: research + marketing website with blog and docs** (usually L)

| Phase / gate | Deliverable | Gate check | Swarm | Models |
|---|---|---|---|---|
| 0 Intake | profile (RSR secondary → WEB primary; `public_facing_content`, `needs_external_research`, `has_web_frontend`, `design_quality_matters`, `deploy_to_production`) | forking questions: audience, tone reference sites, domain/hosting, team details source | — | Fable 5.1 medium |
| 1 Research (RSR) | RESEARCH.md: competitors, category language, audience pains, the project's differentiators (with evidence), positioning options | QUESTION-FRAMED first; skeptic pass; every claim graded | 3–6 angle lanes + synthesizer + skeptic | lanes Sonnet 4.6 medium; synthesizer Opus 4.8 high |
| CLAIMS-SOURCED | positioning memo + message hierarchy; claim register (claim → S-id) | fact-check verifier samples all comparative claims | — | Opus 4.8 medium fact-check |
| 2 Site spec | sitemap, page inventory (home, about/goals, team, blog index/post, docs landing/page), SEO/meta requirements, docs IA tree | spec review 1–2 rounds; synthetic tree test ≤3 clicks for top docs tasks | — | Opus 4.8 medium |
| 3 Visual direction | 3 directions as rendered hero + one inner page; tournament; tokens | pairwise, position-swapped judge; human picks when the tournament ties | best-of-3 proposals → one writer | makers Sonnet 4.6 high; judge Opus 4.8 high |
| 5 Build | spine shell (layout, nav, tokens, MDX/content pipeline, blog and docs collections) → page lanes → content lanes against the frozen voice guide | build green; lint; per-page G1 checks | spine first; ≤4 page/content lanes | Sonnet 4.6 medium/high |
| 6 Verify | link check, Lighthouse/CWV budgets, axe, G2 vision on a page×viewport matrix, AI-tells checklist, content fact-check | VERIFICATION.md PASS; zero unsourced claims | — | gate runner Sonnet 4.6 low; vision Opus 4.8 medium/high |
| 8 Release | preview deploy → H-APPROVE publish (PC-5 legal-sensitive items signed off) → prod | LIVE-VERIFIED (status 200, sitemap, OG render) | — | — |

### 6.5 How each shape scales by size

| Shape | S | M | L | XL |
|---|---|---|---|---|
| GRN | not allowed (re-classify as RSR prototype or FEA scaffold) | internal single-platform tool: charter-lite, skeleton, 1–2 milestones | single-platform product with backend: full spec, M0 contract lite, 3+ milestones | multi-platform: M0 contract + testkit, skeleton, per-milestone L-missions, human batch reviews |
| FEA | small UI/API tweak: task card, 1 test, 1 viewport screenshot | dashboard/page: mini spec, spine + widgets, journeys | cross-component feature: designs, lens panel, flag rollout | treat as GRN-within-product: milestones |
| BUG | known-location fix: inline record, failing test first, one grep sweep | ledger file, repro budget 2h, differentials | multi-layer: experiment lanes, live recurrence check, postmortem | incident-scale: mitigate first, one O-id per cause, drill |
| MIG | config/endpoint move inside one repo: parity test + flag | one service, few consumers: judge + shadow | gateway/service extraction: full strangler + runbook | platform consolidation: per-service L-missions behind a shared judge |
| REF | rename/extract: suite green before and after | module restructure: characterization tests + arch lint | subsystem port: rulebook, pilot, fan-out | language port: kit six steps |
| UPG | patch/minor: suite on the new lockfile | one major: breaking-change research, codemods | multiple majors: waypoints, dual-run | runtime/platform generation shift: per-waypoint milestones |
| DAT | additive column: DB-1, restore point | backfill: profile, invariants, dry run | live table move: dual-write, shadow reads | store swap: per-entity L-missions |
| PRF | one hotspot: 5-run before/after | harness + ≥10 runs + CI check | experiment lanes | architecture-level: RSR spike first |
| INF | one workflow edit | pipeline + environments | IaC module + monitoring | platform bootstrap: sequence of INF + DAT |
| SEC | one finding fix | lens audit of one surface | multi-surface audit + controls | program: threat model per component, recurring OPS |
| WEB | docs-only page edit: build + link check | landing page with sourced claims | site with research, blog, docs | multi-product site with localization |
| RSR | ≤3 lookups inline | single researcher, memo | angle lanes + skeptic + prototype | strategy research with human review |
| OPS | one-off script | Routine + runbook + ≥10 eval cases | multi-trigger triage with weekly eval refresh | fleet-wide automation: treat as GRN for the tool |

### 6.6 Five worked examples (illustrations, not implementations)

**Example 1: "A fashion/outfit-creating iOS app with a Cloudflare backend and a native Swift iOS frontend."**
- *Signals*: empty repo; "iOS", "Swift", "Cloudflare" in the prompt; "outfit-creating" suggests AI generation and user
  photos (inferred, so `unknown` → question).
- *Profile*: primary GRN. Traits: `multi_platform`, `has_ios`, `has_backend_api`, `has_database`, `touches_auth`,
  `touches_pii` (wardrobe photos), `has_ai_llm_features` (if the outfit generation is model-based), `design_quality_matters`,
  `deploy_to_production`, `long_running`, `third_party_integrations`. Scores B3 D3 U2 C3 → XL.
- *Forking questions (≤3)*: (1) Are outfits generated by an AI model or by rules? Default: model-based, with an eval
  suite. (2) Accounts and cloud photo storage, or on-device only? Default: accounts + R2, which switches on AU-5 in-app
  account deletion and PI-1/4 retention. (3) 2–3 reference apps for taste? Default: the orchestrator proposes three and
  records them as ASSUMED.
- *What the engine runs*: Research lanes (Workers/D1/R2 limits, image pipeline options, SwiftUI patterns, competitor
  apps) → Fable 5.1 charter + spec with domains AUTH, WARDROBE, OUTFIT, FEED → human spec sign-off → Opus 4.8 design
  (backend ADRs: D1 vs Durable Objects for per-user state, R2 signed URLs; frontend IA, tokens) → visual direction
  tournament → **M0 CONTRACT-FROZEN** (OpenAPI + generated Swift client + TS types + contract tests both sides +
  testkit fakes for the AI provider) → **M1 SKELETON-LIVE** (Sign in with Apple → upload one garment photo → backend
  stores it → list renders; XCUITest against the dev Worker) → M2 wardrobe, M3 outfit generation (AI-1..6: ≥50 eval
  tasks, outcome graders such as "every outfit uses only garments owned by the user", calibrated model grader for style
  coherence, 3 trials), M4 social/feed if in scope → Release (TestFlight, IO-6 checklist, gradual Worker deploy,
  restore point).
- *Swarm*: after M0, backend lane + iOS lane + contract-test lane per milestone (≤8 writers); per-lane simulators.
- *Human checkpoints*: spec sign-off, irreversible design (datastore), per-milestone batch design review (DQ-4),
  TestFlight/prod release.
- *Done*: P1 journeys green on the simulator matrix against staging; eval threshold met; store readiness complete;
  LIVE-VERIFIED canary.

**Example 2: "Find this deep annoying bug and fix it."**
- *Signals*: existing repo; the prompt lacks a repro, so U3; the touched layer is unknown until triage.
- *Profile*: primary BUG. Traits: `existing_codebase`, plus whatever triage finds (for example
  `concurrency_or_distributed_state` if it is a race). Scores B1 D1 U3 C0 → base M, +1 for U3 → **L**. Ceremony is
  still BUG-shaped: no charter, and the "spec" is the repro.
- *Forking question*: only if no symptom evidence exists at all: "Where do you see it, and how often?", with the default
  "I will search logs/issues and CI history first". Everything else is probed.
- *What the engine runs*: failure record → check the plug → REPRODUCED (Sonnet 4.6 high repro builder; the statistical
  repro records a baseline rate p) → git bisect / differential runs → hypothesis ledger with ≥3 hypotheses across layers
  → if ≥3 independent hypotheses stay open after 2 rounds, 3 experiment lanes in worktrees → CONFIRMED by an Opus 4.8
  confirmer using two-way intervention → fix → PROOF: n ≥ ln(0.05)/ln(1−p) clean runs, doubled when state can't be reset
  → sibling sweep → review (≤3 rounds) → lesson + mechanical control (for example a lint rule banning the unsafe
  pattern).
- *Triggers*: if the root cause is data corruption, add DAT and re-classify (§4.6). If the fix changes a public
  contract, add `published_api` obligations.
- *Done*: repro red→green in a clean worktree, n clean runs, suite green, sweep dispositioned, control added.

**Example 3: "Add this new dashboard to the existing product."**
- *Signals*: app code, React/TSX, charts library, API layer, ORM; the prompt says "dashboard".
- *Profile*: primary FEA. Traits: `existing_codebase`, `has_web_frontend`, `has_backend_api` (new aggregate endpoint),
  `has_database` (read-only queries, so DB-1 is only needed if indexes are added), `performance_sensitive` if the data
  volume is large (probe: row counts), `touches_auth` (who may see which tenant's metrics; forcing if the repo has
  RBAC). Scores B1 D1 U1 C1 → **M**.
- *Forking question*: "Which metrics, and for whom?" only if the prompt names neither. Default: propose metric
  definitions in the mini spec and notify at Spec.
- *What the engine runs*: reader lane → CONVENTIONS.md → mini spec with metric definitions (formula, source, timezone,
  refresh, empty/partial states) + authz rule → short design (reuse existing chart/table components, index check) →
  spine lane (route, layout, flag, data hook) → ≤4 widget lanes → Verify: criteria tests; journeys on seeded data
  asserting the displayed aggregates equal SQL-computed expectations; AU-2 negative test (another tenant's data not
  visible); G1 axe/geometry, G2 vision on 3 viewports × light/dark, G3 walkthrough → review panel (correctness + UX)
  → flag rollout.
- *Done*: journeys + criteria tests green, affected regression suites green, flag-off check green, visual rubric at
  the M threshold, screenshot summary delivered.

**Example 4: "Move our AI gateway from an external project into a core service of our platform."**
- *Signals*: two codebases named; the external gateway has provider SDKs, routes, key storage, a caching/rate-limit
  config; the platform repo has Workers/services.
- *Profile*: primary MIG. Secondary: DAT if usage logs, keys or quotas must move. Traits: `cross_repo_migration`,
  `has_backend_api`, `has_ai_llm_features` (provider/model routing is the gateway's behaviour), `touches_auth` (API keys,
  tenant auth), `third_party_integrations`, `deploy_to_production`, `existing_codebase`, `long_running`. Scores B2 D2
  U2 C2 → **L**. It would be XL if external customers call the gateway directly (C3 → +1).
- *Forking questions*: (1) Who calls the gateway today (internal services only, or external customers)? This forks C2
  vs C3. (2) Does the old project stay alive for other users after the move? This forks CONTRACTED vs a DECISIONS
  "keep both". (3) Any behaviour changes wanted during the move? Default: none until parity (CMP-R03), then a
  post-parity FEA milestone.
- *What the engine runs*: FEASIBILITY report (Opus 4.8 high) → parity inventory (reader lanes: routes, provider
  adapters, retries/fallback, caching and rate limits, analytics/logging fields, error shapes, secrets, quotas; a script
  diffs the route dump against the inventory) → **PARITY-BASELINE**: a recorded request corpus replayed against the old
  gateway with fake providers, a normalising differential runner, oracle bite on a deliberately broken build → spec +
  design (target seams in the platform, key custody with a security lens, consumer switch plan, runbook with Evidence
  and Rollback columns modelled on `arcwell/docs/operations/cutover-runbook.md:8`) → per-endpoint build lanes after the
  shared shim lands → **SHADOW-PARITY** with mirrored traffic and a diff report → **CUTOVER** per consumer via
  flag/percentage (Workers gradual deployment where applicable), each step H-APPROVE → soak → **CONTRACTED** with a
  rollback window.
- *Obligations that fired and merged*: XR-1..8, AU-1/2/3 (the security lens merged with XR-6 into one panel member,
  CMP-R04), TP-1/2/3, AI-6 (model IDs pinned, fallback tested), DP-1..6.
- *Done*: the judge passes on the new path; the original suite re-run on the old gateway has zero inherited failures
  (kit done-gate); all consumers switched; old path retired; rollback window recorded.

**Example 5: "Research our market position, create a website, design it to describe our project, goals, team, and have
blog and documentation sections."**
- *Signals*: a project exists (repo/README); no site generator or an empty `site/`; prompt verbs are "research" and
  "create/design".
- *Profile*: primary WEB, secondary RSR (runs first, CMP-R02). Traits: `public_facing_content`,
  `needs_external_research`, `has_web_frontend`, `design_quality_matters`, `deploy_to_production`, `touches_pii` (team
  bios and photos: consent), `existing_codebase` (docs source). Scores B1 D2 U2 C1 → **L**.
- *Forking questions*: (1) Audience priority (developers / buyers / investors)? This forks the messaging hierarchy.
  (2) Hosting/domain and whether publishing is allowed without review. Default: preview deploy, publish needs
  H-APPROVE. (3) Source for team details and consent. Default: team section placeholder copy is *not* allowed, so the
  team page waits in BLOCKED-HUMAN while the rest proceeds.
- *What the engine runs*: QUESTION-FRAMED ("Where do we win, against whom, for which audience?") → 3–6 research angle
  lanes (competitors, category vocabulary, audience pain evidence, pricing/positioning norms, our differentiators
  checked against the repo) + skeptic → positioning memo + claim register → **CLAIMS-SOURCED** → sitemap and page
  inventory (home, about/goals, team, blog index and post template, docs landing plus a tree generated from the existing
  docs/README) → visual direction tournament (3 rendered directions) → tokens → spine shell → page and content lanes
  (launch blog posts drafted against the frozen voice guide; every factual sentence carries an S-id) → Verify: build,
  link check, Lighthouse/CWV budgets, axe, G2 vision matrix, AI-tells checklist, fact-check → H-APPROVE publish.
- *Done*: preview and prod live; zero unsourced claims in the claim register; budgets met; docs tree test ≤3 clicks for
  the top 5 tasks; human sign-off on legally sensitive content.

## 7. Artifacts & templates

### 7.1 `mission/PROFILE.yaml`

```yaml
# mission/PROFILE.yaml — written at Intake, re-written on every re-classification (diff → DECISIONS.md)
profile_version: 3
classified_at: 2026-08-30T10:12Z
classifier: {model: claude-sonnet-4-6, effort: medium, second_opinion: claude-opus-4-8/medium, agreed: true}
primary_shape: MIG            # GRN|FEA|BUG|MIG|REF|UPG|DAT|PRF|INF|SEC|WEB|RSR|OPS
secondary_shapes: [DAT]
size: L
size_scores: {breadth: 2, uncertainty: 2, duration: 2, coordination: 2}
size_justification: "Two repos, internal consumers only (C2); ~2-3 weeks human-equivalent."
gate_zero: [FEASIBILITY, PARITY-BASELINE]
traits:
  cross_repo_migration: {state: present, evidence: "prompt: 'move our AI gateway from ...'", confidence: high}
  touches_auth:         {state: present, evidence: "gateway/src/keys.ts:14 (API key lookup)", confidence: high}
  touches_pii:          {state: unknown, evidence: "request logs may contain prompts; probe task T-0003", confidence: low}
  deploy_to_production: {state: present, evidence: "platform/wrangler.jsonc routes", confidence: high}
  has_web_frontend:     {state: absent, evidence: "no UI in either repo (probe)", confidence: high}
obligations: [XR-1, XR-2, XR-3, XR-4, XR-5, XR-6, XR-7, XR-8, AU-1, AU-2, AU-3, TP-1, TP-2, TP-3, AI-6, DP-1, DP-2, DP-3, DP-4, DP-5, DP-6, DM-1, DM-2, DM-5]
merged_obligations: {"security-lens": [AU-3, XR-6]}
open_classification_questions:
  - id: Q-01
    forks: "coordination C2 vs C3 (size L vs XL)"
    question: "Who calls the gateway today?"
    options: ["internal services only (recommended default)", "external customers too", "both, with SLAs"]
    default_if_unanswered: "internal services only — ASSUMED"
assumptions: [A-01, A-02]
```

For size S, replace the file with five lines at the top of the task card:
`Shape: BUG · Size: S (B0 U1 D0 C0) · Traits: existing_codebase, touches_auth · Gate zero: REPRODUCED · Obligations: EC-1, AU-2, AU-3`.

### 7.2 `references/traits.yaml` row schema

```yaml
- trait: has_ios
  detect:
    forcing: ["glob:**/*.xcodeproj", "glob:**/Package.swift&&grep:'.iOS('", "prompt:/\\b(iOS|iPhone|SwiftUI)\\b/i"]
    probe_if_unknown: "list targets via xcodebuild -list; grep SwiftUI imports"
  obligations:
    - id: IO-1
      text: "SwiftUI state matrix: Light/Dark, largest accessibility Dynamic Type, smallest+largest device"
      floor: S
      scale: {S: "1 device x light", M: "2 devices x light/dark", L: "full matrix", XL: "full matrix + localization"}
      gate: VERIFY.VISUAL-IOS
      owner_ref: references/frontend-verification.md#ios-matrix
      merge_key: visual-matrix-ios      # CMP-R04: same key merges, parameters take max
    - id: IO-6
      text: "App Store readiness: privacy details, privacy manifest, in-app account deletion if accounts exist"
      floor: S
      when: "release includes App Store/TestFlight submission"
      gate: RELEASE.STORE-READY
      owner_ref: references/release.md#app-store
      merge_key: store-readiness
```

The obligation expander (a script) reads PROFILE.yaml plus traits.yaml and emits `acceptance.json` stubs
(`passes: false`) and PLAN.md task stubs for every obligation whose floor ≤ size, deduplicated by `merge_key`. It fails
if a present trait expands to zero obligations.

### 7.3 Repository probe (`scripts/probe-signals.sh`, outline to ship; validate on fixture repos)

```bash
#!/usr/bin/env bash
# Emits mission/signals.json. Deterministic; no network; read-only.
set -euo pipefail
root="${1:-.}"
count() { find "$root" -path '*/node_modules' -prune -o -path '*/.git' -prune -o -name "$1" -print 2>/dev/null | wc -l | tr -d ' '; }
has()   { [ "$(count "$1")" -gt 0 ] && echo true || echo false; }
grepq() { grep -rIl --exclude-dir=node_modules --exclude-dir=.git -E "$1" "$root" 2>/dev/null | head -n 5 | paste -sd, - || true; }
src_files=$(find "$root" -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.swift' -o -name '*.kt' -o -name '*.rs' -o -name '*.py' -o -name '*.go' \) -not -path '*/node_modules/*' | wc -l | tr -d ' ')
mkdir -p "$root/mission"
cat > "$root/mission/signals.json" <<JSON
{
  "source_files": $src_files,
  "markers": {
    "xcodeproj": $(has '*.xcodeproj'), "package_swift": $(has 'Package.swift'),
    "android_gradle": $(has 'build.gradle*'), "wrangler": $(has 'wrangler.*'),
    "dockerfile": $(has 'Dockerfile'), "gh_workflows": $( [ -d "$root/.github/workflows" ] && echo true || echo false ),
    "migrations_dir": $( [ -n "$(find "$root" -type d -name migrations -not -path '*/node_modules/*' | head -n1)" ] && echo true || echo false ),
    "prisma": $(has 'schema.prisma'), "drizzle": $(has 'drizzle.config.*')
  },
  "sdk_hits": {
    "auth": "$(grepq 'jsonwebtoken|next-auth|lucia|passport|SignInWithApple|ASAuthorization')",
    "payments": "$(grepq 'stripe|RevenueCat|StoreKit')",
    "llm": "$(grepq '@anthropic-ai/sdk|openai|workers-ai|env\\.AI\\b')",
    "pii_fields": "$(grepq '\\b(email|phone|dateOfBirth|address)\\b')"
  },
  "tests_present": $( [ -n "$(grepq 'describe\\(|XCTestCase|@Test|#\\[test\\]')" ] && echo true || echo false )
}
JSON
```

The script was not executed in this lane (sandbox unavailable; §9). The skill MUST ship it with a self-test over
three fixture repos (empty, web+Workers, iOS+SwiftUI) that asserts the expected markers.

### 7.4 Classifier sub-agent brief (Sonnet 4.6 medium)

```text
ROLE: Mission classifier. You classify; you do not plan or implement.
INPUTS (read only these): mission/BRIEF.md (user direction verbatim), mission/signals.json,
  references/shapes.md (catalog §4.2), references/traits.yaml (trait names + detect rules), references/sizing.md.
TASK:
1. Choose ONE primary_shape and 0-2 secondary_shapes from the closed list. The primary shape's done criterion must be
   the mission's done criterion.
2. For EVERY trait in traits.yaml output state present|absent|unknown with evidence (file:line, signals.json key, or a
   verbatim prompt quote). No evidence → unknown. Never absent without evidence.
3. Score breadth, uncertainty, duration, coordination 0-3 using sizing.md anchors; compute size with SZ-R02.
4. List fields with confidence low that FORK the plan (primary shape, size ±2, irreversible trait, platform set).
   For each, propose ONE multiple-choice question with a recommended default and the cost of guessing wrong.
OUTPUT: PROFILE.yaml content only (schema §7.1). ≤400 words outside the YAML.
DO NOT: read source files beyond the paths cited in signals.json; invent traits not in traits.yaml; ask about
non-forking details.
```

The blind second classifier (L/XL, Opus 4.8 medium) gets the identical brief and does not see the first output. A
script diffs the two profiles field by field. Disagreement on a forking field goes to the orchestrator.

### 7.5 Clarifying-question block (asked at most twice per mission)

```markdown
## Before I start: 3 decisions that change the plan
Reply with letters (e.g. "1b 2a 3a") or "defaults". Unanswered items use the default and are marked ASSUMED.

1. **Who calls the gateway today?** (changes size L → XL and adds a customer cutover plan)
   a) internal services only ← recommended default  b) external customers too  c) both, with SLAs
2. **After the move, is the external project retired?** (changes the final milestone)
   a) retire after a 30-day rollback window ← default  b) keep both running (I'll record why)
3. **Any behaviour changes wanted during the move?** (they will be scheduled after parity, never mixed in)
   a) none ← default  b) yes: list them and I'll add a post-parity milestone
```

### 7.6 Cutover runbook table (MIG, DAT, INF; modelled on `arcwell/docs/operations/cutover-runbook.md:8`)

```markdown
# Cutover runbook — <mission id>
Reversible until step <N>. Rollback window closes: <date>. Owner approval required on rows marked H.

| # | Step | Evidence required (command + expected output) | Rollback (command) | H? | Status |
|---|---|---|---|---|---|
| 1 | Parity judge green old-vs-new on recorded corpus | `pnpm judge:diff --corpus fixtures/corpus` → 0 unexplained diffs | none needed | | PENDING |
| 2 | Deploy new service to staging; shadow 100% mirrored | diff report `reports/shadow-<date>.md` ≤ threshold, classes explained | disable mirror flag | | PENDING |
| 3 | Consumer A → new service at 10% | error rate/latency within budget for 24h | `wrangler versions deploy` previous version 100% | H | PENDING |
| 4 | Consumer A → 100% | as step 3 for 72h | route back to old gateway flag | H | PENDING |
| N | Retire old path; archive final export + rollback snapshot | export hash, snapshot id, window end date in DECISIONS | restore snapshot and re-point within window | H | PENDING |

## Standing rules during cutover
- No behaviour changes merged until row N passes (CMP-R03).
- Any unexplained diff class → stop, investigate (BUG pipeline), do not raise the threshold.
```

The `wrangler versions deploy` command is illustrative. The skill MUST resolve the exact rollback command from the
current Cloudflare docs at Plan (ER-4) and test it once (DP-2).

### 7.7 Gate-zero lint (PLAN.md check, script)

```text
FAIL if any task with kind in {build, fix, migrate, refactor, upgrade, apply} has no dependency path to the profile's
gate_zero tasks, or if gate_zero gate status is not PASSED when such a task starts.
FAIL if PROFILE.traits has state=present and obligations expand to zero PLAN tasks.
FAIL if the profile (primary or secondary) includes MIG, REF, UPG, DAT or PRF and a behaviour-changing task shares a
PR with a behaviour-preserving task (CMP-R03).
WARN if size ≤ M and PLAN.md has > 25 tasks (ceremony creep).
```

### 7.8 Worker return extension and DECISIONS entry

```yaml
# appended to every worker return block (R01 §7.2 format)
trait_discovered:
  - trait: data_migration
    evidence: "api/src/usage.ts:88 rewrites historical rows on read"
    suggested_obligations: [DM-1, DM-2]
```

```markdown
| DEC-017 | 2026-08-31 | Re-classification | PROFILE v2 → v3: +trait data_migration (worker T-0021 evidence api/src/usage.ts:88); +secondary DAT; size unchanged L (B2 U2 D2 C2). Obligations added: DM-1, DM-2, DM-5. Plan: new gate DATA-PROFILED before T-0030. | orchestrator |
```

## 8. Anti-patterns & failure modes

| Anti-pattern | Symptom | Why it hurts | Control |
|---|---|---|---|
| **One label for everything** ("project type: app") | Payment one-liner gets an XL spec, or an XL product gets a task card | Size and risk are conflated, so the ceremony is wrong in both directions | Three axes (SHP-R01); risk traits never change size (SZ-R02) |
| **Shape by vibes** | The classifier says GRN for a repo with 40k LOC | No probe; the model over-reads the prompt | Probe first (CLS-R01); forcing rules; blind second classifier L/XL |
| **Asking everything up front** | 12 questions before any work; the user abandons the skill | Violates the user's core goal (less typing) | Fork test (CLS-R06), ≤3 questions, defaults, ASSUMED in headless runs |
| **Never asking** | Builds on-device when the user wanted cloud photos; rework | Irreversible fields were guessed | Forking irreversible traits MUST be asked or explicitly ASSUMED with reversal cost |
| **`absent` without evidence** | PII discovered at Review | Obligations never expanded | No evidence → `unknown` → probe (MDL-R02) |
| **Frozen profile** | A "UI bug" fixed with a CSS change while the data stays corrupted | The mission drifted from its profile | Re-classification triggers (§4.6), `trait_discovered` return field |
| **Ceremony creep at S** | PROFILE.yaml, STATE.md, 3 reviewers for a typo | Token burn; the skill gets bypassed | S = 5-line profile, in-prompt check + 1 verifier; lint WARN > 25 tasks at ≤ M |
| **Obligation stacking** | Separate security reviews for auth, payments and PII; three screenshot matrices | Paying for duplicates; review fatigue (arcwell 18 rounds) | `merge_key` dedupe, max parameter (CMP-R04) |
| **Mixed preserve + change PRs** | "Moved the gateway and added caching"; parity diffs can't be attributed | The oracle loses its meaning | CMP-R03 + gate-zero lint |
| **No judge, start translating** | Migration "done" but nobody can say it matches | No exit condition | PARITY-BASELINE gate zero with oracle bite (kit) |
| **Never contracting** | Old gateway still running a year later | Worse than before (Fowler) | CONTRACTED gate or a DECISIONS entry to keep both |
| **Canary with shared state** | Canary looks green because it shares a cache with prod | Evaluation invalid (SRE workbook) | DP-3 shared-state list |
| **Unsourced public claims** | Website says "fastest" or "only" with no source | Legal and reputational risk | PC-1 claim register; cut or rephrase |
| **Evals after the prompt** | Prompt tuned to five hand-picked examples | Overfitting, no regression signal | AI-1 evals at Spec; separate capability and regression suites |
| **GRN at S** | "Quick app" scaffold merged as a product | Skipped contract, skeleton and privacy decisions | GRN minimum M; prototypes are RSR and are not merged |
| **Fable for classification** | High token spend on pattern matching | Wasted top-tier cost | MDL-R01 |
| **Swarming coupled work** | Parallel lanes editing the shared schema or migration | Merge conflicts, broken invariants | DAT/INF: no parallel writers; MP-3 contract freeze before fan-out |
| **Unattended irreversible actions** | Overnight run deploys to prod or applies a migration | No human for rollback decisions | UN-1..4; H-APPROVE via permissions/hooks |

**Cost traps specific to this component:** running the blind second classifier at S/M (≈ its cost × every mission;
scale it to L/XL only). Re-classifying on every worker return instead of only on `trait_discovered`. Expanding
obligations for `unknown` traits as if present at *design* depth (unknown means present for verification only, opinion
8). Loading all 13 shape pipelines into SKILL.md: ship `references/shapes/<ID>.md` and load only the primary and
secondary shapes' files.

## 9. Open questions / risks for the synthesizer

1. **Size rule conflict with R03.** This lane says money/irreversibility are traits, not size drivers. R03 SPEC-R01 says
   B3 → XL (`03-spec-design.md:341`). Decide one. Recommendation: adopt SZ-R02 for size, and keep R03's B3 list as the
   *irreversible-trait* list that triggers H-APPROVE and the security lens.
2. **Shape count vs SKILL.md leanness.** 13 shapes × pipeline references is a lot of files. Option: ship full references
   for the five user shapes plus MIG-family REF/UPG/DAT (which share a parity core), and one combined
   `references/shapes/other.md` for PRF/INF/SEC/RSR/OPS until usage data justifies splitting.
3. **Mission directory name.** R01 uses `mission/`, R07 `.mission/` (`99-synthesis-notes.md:34`). All paths here use
   `mission/` and should follow the synthesizer's decision.
4. **Duration anchors are human-equivalent guesses.** Agents compress wall-clock time unevenly (research compresses
   well; App Store review and soak windows do not). The D dimension may need an "external waits" flag so an L mission
   with a 72h soak isn't mis-sized.
5. **Unverified numbers proposed by this lane** (inference, not sourced): OPS ≥90% agreement threshold; blind-classifier
   cost estimate ($0.10–$0.50); AI-1 task counts (≥20 / ≥50, partly aligned with R04's ≥20); GRN minimum size M;
   the 25-task ceremony WARN. Calibrate them at the first retros.
6. **Android obligations** (AN-1..5) were written by analogy with iOS. No Android source was fetched in this lane.
7. **Blog-page evidence gap.** The Anthropic migration blog page (https://claude.com/blog/ai-code-migration) was larger
   than the fetch limit. Facts come from the companion kit README. The claim that Fable 5 and Opus 4.8 were used on the
   Bun port comes from secondary summaries only.
8. **Probe script untested.** The sandbox was unavailable during this lane (command launcher failed). §7.3 must be
   validated on fixture repos before shipping.
9. **Classifier input privacy.** `signals.json` grep hits could include PII-bearing file paths or snippets. The probe
   emits *paths only*, never matched content. Keep it that way.
10. **Human-question tolerance.** The user wants less typing. Even ≤3 questions may feel heavy for S/M. Consider a
    `--defaults` invocation flag that converts all forking questions to ASSUMED with a summary at the first checkpoint.
11. **Combined shapes beyond two secondaries.** The profile allows 0–2 secondary shapes. A mission needing more
    (for example GRN + DAT + INF + SEC) is a signal to split into milestones with their own profiles at XL. Confirm this
    rule is acceptable.

## Sources

Primary and practitioner sources consulted during this lane via the web tools (snippet-only sources are marked):
- https://code.claude.com/docs/en/best-practices (fetched)
- https://code.claude.com/docs/en/common-workflows (fetched)
- https://github.com/anthropics/code-migration-kit-with-claude-code (README fetched)
- https://claude.com/blog/ai-code-migration (not fetched: larger than 500KB; referenced by the kit and common-workflows)
- https://martinfowler.com/bliki/StranglerFigApplication.html (fetched)
- https://martinfowler.com/bliki/ParallelChange.html (fetched)
- https://github.com/github/scientist (snippet)
- https://stripe.com/blog/online-migrations (snippet/secondary; fetch returned navigation only)
- https://arpitbhayani.me/videos/how-stripe-achieves-zero-downtime-consistent-data-migrations-at-scale/ (secondary, snippet)
- https://sre.google/workbook/canarying-releases/ (snippet; fetch timed out)
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents (fetched)
- https://www.anthropic.com/engineering/building-effective-agents (snippet)
- https://developers.cloudflare.com/workers/testing/vitest-integration/ (fetched)
- https://developers.cloudflare.com/workers/versions-and-deployments/gradual-deployments/ (snippet)
- https://developers.cloudflare.com/d1/reference/migrations/ (snippet)
- https://developers.cloudflare.com/d1/reference/time-travel/ (snippet)
- https://developers.cloudflare.com/ai-gateway/ (snippet)
- https://developer.apple.com/documentation/xctest (snippet)
- https://developer.apple.com/documentation/XCUIAutomation (snippet)
- https://developer.apple.com/support/offering-account-deletion-in-your-app (snippet)
- https://developer.apple.com/app-store/app-privacy-details/ (snippet)
- https://www.simplified.guide/xcuitest/test-plan-create (secondary, snippet)
- https://github.blog/engineering/architecture-optimization/building-github-with-ruby-and-rails/ (snippet)
- https://github.com/fastruby/upgrading-rails-the-dual-boot-way (snippet)
- https://owasp.github.io/www-project-application-security-verification-standard/ (snippet)
- https://asvs.dev/v5.0.0/V7-Session-Management/ (snippet)

Workspace evidence (read-only): `arcwell/README.md:9-17,40`; `arcwell/docs/operations/milestone-ledger.md:10,16-17`;
`arcwell/docs/operations/cutover-runbook.md:4,8,14,20`; `arcwell/package.json:20-37`. Sibling lanes:
`research/mission-skill/01-orchestration-control.md:455-514`, `research/mission-skill/03-spec-design.md:330-352`,
`research/mission-skill/99-synthesis-notes.md` (R02, R04–R09 summaries).
