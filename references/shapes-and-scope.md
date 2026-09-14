# Shapes, scope and conditional obligations

## When to load

At Phase 0 Intake (always), at every phase gate (re-classification check), and whenever a worker returns
`trait_discovered`. This file decides *which* phases, gates, documents, reviewers and agents a mission needs. The
methods live in the other references; this file says when they switch on.

## Core rules

- **SHP-1 MUST** classify on three separate axes: **shape** (what kind of work; closed vocabulary §1), **class**
  (S/M/L/XL from four scores, conventions §5), and **traits** (surfaces and risks that add obligations, §4). Never one
  "project type" label.
- **SHP-2 MUST** write `.mission/PROFILE.yaml` (`templates/PROFILE.yaml`) before any other artefact except the intake
  notes. For class S the profile is 5 lines inside the task card.
- **SHP-3 MUST** pick exactly one **primary shape**: the one whose done criterion is the mission's done criterion.
  At most 2 secondary shapes; more means splitting into milestones or separate missions.
- **SHP-4 MUST** establish the primary shape's **gate zero** (§1) before any code change.
- **SHP-5 MUST** mark every trait `present` / `absent` / `unknown` with evidence (file:line, prompt quote, probe output).
  No evidence → `unknown` → probe. `unknown` counts as present for verification and absent for design ceremony.
- **SHP-6 MUST** expand present traits into obligation IDs (§4), record them in PROFILE.yaml, and make every obligation
  appear in PLAN.md as a task or a gate check. Obligations are never skipped silently; a waiver is a D-entry.
- **SHP-7 MUST** keep behaviour-preserving work (MIG, REF, UPG, DAT parity) and behaviour-changing work (FEA, GRN) in
  separate milestones and PRs, preserving first.
- **SHP-8 SHOULD** not invent shapes mid-mission. Use the nearest shape plus a D-entry; propose a new shape at retro.

## 1. Shape catalog

| ID | Shape | Typical prompt | Repo signal | Gate zero (before code changes) | Primary deliverable | Usual class |
|---|---|---|---|---|---|---|
| GRN | Greenfield product | "build an app that…", "from scratch" | empty or near-empty repo, no deploy config | CHARTER-SIGNED (+ CONTRACT-FROZEN if multi-surface) | deployed walking skeleton → milestones | L–XL (never S) |
| FEA | Feature in existing product | "add X to our…", "new dashboard/page/endpoint" | existing app, tests, CI | CONVENTIONS-MAPPED | merged feature (behind a flag where the product has flags) with journeys | S–L |
| BUG | Bug hunt / fix (incident mode when live) | "fix", "broken", "crash", "flaky", "why does" | failing test, issue, logs | REPRODUCED (deterministic or statistical) | fix + frozen regression test + sibling sweep | S–L |
| MIG | Service migration / extraction / consolidation | "move X into Y", "extract", "consolidate", "replatform" | two codebases or services named | FEASIBILITY + PARITY-BASELINE (validated judge) | new home serving traffic, old path retired | L–XL |
| REF | Refactor / modernization / language port | "clean up", "restructure", "port to" | large legacy module, no behaviour ask | PARITY-BASELINE | same behaviour, new structure | M–XL |
| UPG | Dependency / framework / runtime upgrade | "upgrade", "bump", "migrate to vN", CVE notice | lockfile, deprecation warnings | PARITY-BASELINE (suite green on old version) | new version, suite green, deprecations cleared | S–L |
| DAT | Schema change / data migration / backfill | "add column", "backfill", "move data" | migrations dir, ORM schema | RESTORE-POINT + DATA-PROFILED | applied migration, row-level invariants verified | S–L |
| PRF | Performance / cost optimization | "slow", "p95", "memory", "bundle", "cost" | benchmarks, profiles | BASELINE-MEASURED (repeatable harness) | metric past target, no regression | S–L |
| INF | Infra / deploy / CI / observability | "set up CI", "deploy", "Terraform", "alerts" | workflows, IaC, wrangler/Docker | DRY-RUN-GREEN | pipeline or infra change with rollback | S–M |
| SEC | Security audit / hardening | "audit", "harden", "threat model" | auth code, secrets, public endpoints | THREAT-MODEL | dispositioned findings + fixes + controls | M–L |
| WEB | Research + marketing website / content / docs | "website", "landing page", "blog", "docs site" | none or static-site generator | CLAIMS-SOURCED (research register + message hierarchy) | deployed site with sourced claims and docs IA | M–L (docs-only: S–M) |
| RSR | Research / spike / prototype | "investigate whether", "compare", "market position" | often none | QUESTION-FRAMED (decision question, criteria, timebox) | decision memo / ADR (+ throwaway prototype) | S–M |
| OPS | Recurring ops / triage automation | "every morning…", "whenever CI fails…" | CI logs, alerting | RUNBOOK-DRY-RUN (one supervised run) | Routine or script + runbook + eval cases | S–M |

Merges: AI/LLM features are a trait (they sit inside GRN/FEA). Incident is BUG with `live_incident` (mitigate first).
Docs-only is WEB without the site build. Prototype code is RSR and MUST NOT merge without re-entering as FEA/GRN.
MIG crosses a deploy or repository boundary and has traffic to cut over; REF does not.

## 2. Classification procedure (Phase 0 and every gate)

1. **Probe (no model).** `scripts/probe-signals.sh [repo]` writes `.mission/tmp/signals.json`: languages and file counts,
   manifests, platform markers, deploy config, test harness, CI files, migration dirs, sensitive-path hits, git depth.
2. **Prompt signals.** Verbs, named systems, platforms, audiences, deadlines, "from scratch" vs "our existing",
   explicit non-goals.
3. **Classify.** The orchestrator fills PROFILE.yaml with per-field `confidence: high|medium|low` and evidence, using the
   catalog, the signal table below and §4.
4. **Forcing rules** (table, bold rows) override judgement. They only add traits or raise class, never remove.
5. **Blind second opinion at L/XL.** `mission-reviewer` gets the prompt + signals.json + this file (not your profile) and
   returns its own profile. Disagreement on a forking field → adjudicate; ask the human only if it still forks.
6. **Resolve low confidence.** For each low-confidence field that forks the plan, spend ≤10 minutes probing (dispatch
   `mission-scout` for grep-and-read). Still unresolved → ask (≤3 multiple-choice questions with defaults, ≤2 rounds)
   or, in autonomous mode, assume and log `ASSUMED (unconfirmed)`.
   A field **forks the plan** if changing it alters the primary shape, moves class by ≥2 steps, flips an irreversible
   trait (`deploy_to_production`, `data_migration`, `touches_payments`, `cross_repo_migration`), or changes the platform
   set. Non-forking unknowns become `A-NN` assumptions and are never asked.
7. **Re-classify** at every gate and at once when: a worker returns `trait_discovered`; an estimate is exceeded by >2×;
   the defect lives in a different layer or shape (UI bug that is really data corruption → add DAT); gate zero cannot
   be established (no judge → insert a "build the judge" milestone); the user changes scope; a classifier refusal
   occurs (add `classifier_sensitive_domain`). Write the profile diff to DECISIONS.md.

| Signal (source) | Implies |
|---|---|
| <~20 source files, no deploy config, prompt says build/create | GRN |
| prompt names an existing product area + app code present | FEA |
| stack trace, failing test ID, crash/flaky/regression | BUG |
| two systems named with move/extract/consolidate verbs | MIG + `cross_repo_migration` |
| **`*.xcodeproj`, `Package.swift` with iOS platform, or iOS/iPhone/SwiftUI in prompt** | **`has_ios`** |
| **Android Gradle app plugin, or "Android" in prompt** | **`has_android`** |
| **`wrangler.toml`/`wrangler.jsonc`, Dockerfile + deploy workflow, `vercel.json`, IaC dirs** | **`deploy_to_production: unknown` → probe environments** |
| **`migrations/`, `schema.prisma`, `drizzle.config.*`, SQL files in touched paths** | **`has_database`** |
| backfill/transform of existing rows, "move data" | `data_migration` |
| **auth libraries, session/cookie/JWT code in touched paths** | **`touches_auth`** |
| **Stripe/RevenueCat/StoreKit/payment SDK imports in touched paths** | **`touches_payments`** |
| upload handlers, user profile schema, photos, email/phone fields | `touches_pii` (probe) |
| Anthropic/OpenAI/Workers AI SDKs, prompt files, AI/LLM/agent in prompt | `has_ai_llm_features` |
| JSX/TSX/Vue/Svelte/HTML templates; page/dashboard/UI | `has_web_frontend` |
| website/blog/landing/docs, marketing copy | WEB + `public_facing_content` |
| market/competitors/state of the art, unfamiliar platform or API | `needs_external_research` |
| numeric latency/memory/cost target; "slow" | PRF or `performance_sensitive` |
| **exploit, pentest, malware, CVE PoC, bio/chem protocols, model distillation** | **`classifier_sensitive_domain`** |
| estimated >1 session, or class ≥ L | `long_running` |
| "overnight", "autonomous", headless/Routine run | `unattended` |
| consumer UI, brand, "beautiful/polished", App Store launch | `design_quality_matters` |

## 3. Class → toggles

Scores and the class formula: conventions §5.

| Toggle | S | M | L | XL |
|---|---|---|---|---|
| Typical | typo, one-line bug, small endpoint | dashboard, bounded bug hunt, one-major upgrade | multi-component feature, migration, website with research | multi-platform product, platform consolidation |
| Mission files | task card only (no `.mission/` unless multi-session) | PROFILE, CHARTER-lite, SPEC-mini, registry, acceptance, TEST-PLAN, STATUS, STATE, INBOX, BUDGET | full set + designs + ADRs + CONTRACTS + HANDOFF per session | L per milestone + milestone ledger, STOP list, `state/` split |
| Phases | Intake → Build (test first) → Verify → Review (1 pass) → Retro (3 bullets) | all; design merges into spec when small | all; ≥3 milestones | each milestone an L mission + consolidated cross-milestone review |
| Spec review rounds cap | 0 | 1 | 2 | 2 (+1 only for new-section blockers) |
| Implementation review cap | 1 | 2 | 3 | 4 per milestone |
| Writers per wave / concurrent agents | 2 / 3 | 4 / 5 | 8 / 8 | 12 / 15 |
| Research depth | ≤3 inline lookups | ≤3 researchers × ≤15 calls | ≤5 angle lanes + fact-check | waves of ≤5, per-milestone refresh |
| Hooks | none | SessionStart | + Stop freshness, PreCompact, protect-frozen | + SubagentStop |
| Human checkpoints | irreversible actions only | + notify at Spec | + spec sign-off, irreversible design, release | + per-milestone summary |
| Budget soft / hard (API $) | 8 / 20 | 50 / 120 | 300 / 700 | 1,500 / 3,500 |
| Loop iteration cap | 3 | 5 | 8 | 8 per task, 20 hard max |
| Orchestrator | Opus 4.8 high (session) | Fable 5.1 medium (Lean: Opus 4.8 high) | Fable 5.1 medium, high at intake/spec/adjudication | same as L |
| Session plan | one session | 1–3 sessions, HANDOFF at end | per-phase sessions | milestone worktrees; Routine or `claude -p` continuation |

## 4. Trait → obligations

Floor = smallest class where the obligation applies (`S+` = always). Obligation IDs are stable; cite them in PLAN.md
tasks and acceptance checks. Method details live in the named reference.

### 4a. Surfaces

| Trait | Obligations | Floor → scaling | Gates | Method |
|---|---|---|---|---|
| `existing_codebase` | **EC-1** read-only conventions digest `.mission/CONTEXT.md` (commands, patterns, reusable components, test harness, existing ID schemes) before design. **EC-2** reuse existing patterns and design system unless a D-entry says otherwise. **EC-3** affected-module regression suites mapped from touched paths. **EC-4** baseline pre-existing failures; they never block. | EC-1 S+ (S: 10 lines) → L reader lane; EC-3 M+ | CONVENTIONS-MAPPED | swarms, testing |
| `no_test_harness` on touched paths | **NT-1** characterization tests of current behaviour before edits, frozen. **NT-2** 1 oracle + ≤2 edge cases per touched behaviour; no mass generation. | S+ | PARITY-BASELINE (lite) | testing |
| `has_web_frontend` | **WF-1** screen specs + tokens before UI code (existing: extracted tokens + reference screenshots). **WF-2** G1 deterministic layout/a11y. **WF-3** G2 vision verifier on a viewport matrix. **WF-4** G3 walkthroughs of changed journeys. **WF-5** Playwright journeys asserting outcomes on seeded data. | WF-2/3 S+ (S: 1 viewport) → L 3 viewports × light/dark; WF-4/5 M+ | VISUAL, A11Y, JOURNEYS | frontend-verification, testing |
| `has_ios` | **IO-1** state matrix: light/dark, largest accessibility Dynamic Type, smallest + largest device. **IO-2** simulator screenshot matrix with status-bar override. **IO-3** XCUITest golden flows (launch-argument seeding, erased simulator). **IO-4** HIG lens. **IO-5** `performAccessibilityAudit` with justified suppressions. **IO-6** App Store readiness (privacy details, privacy manifest, in-app account deletion if accounts exist). **IO-7** per-lane simulator in swarms. **IO-8** device-only behaviour UNVERIFIED until run on hardware. | IO-1/2 S+ (S: 1 device × light) → L full; IO-3/4 M+; IO-6 at Release | VISUAL-IOS, XCUITEST, STORE-READY | frontend-verification, testing |
| `has_android` | **AN-1** light/dark, 200% font scale, small + large screens. **AN-2** screenshot tests. **AN-3** instrumented golden flows. **AN-4** Material lens. **AN-5** Play data-safety at Release. *(analogy with iOS; verify tooling at intake)* | as iOS | as iOS | frontend-verification |
| `multi_platform` (≥2 of web/iOS/Android/backend built together) | **MP-1** M0 contract: schema file as single source of truth, generated clients or shared types, contract tests on both sides. **MP-2** walking skeleton (auth → one core flow → backend round-trip, deployed to dev) before feature fan-out. **MP-3** platform lanes only after CONTRACT-FROZEN; contract change → `BLOCKED(contract-change)`. **MP-4** same journey IDs across clients. | S+ contract file; MP-2 M+ | CONTRACT-FROZEN, SKELETON-LIVE | spec-and-design, swarms |
| `has_backend_api` | **BA-1** request/response schema + ≥1 unwanted-behaviour requirement per endpoint. **BA-2** offline credential-free test run; Workers tests in the Workers runtime. **BA-3** idempotency + retry semantics per mutating endpoint. **BA-4** platform limits table with sources. **BA-5** walking skeleton exercises the real entrypoint and bindings, not only `/health`. | BA-1/2/5 S+; BA-3 M+; BA-4 L+ | CONTRACT, INTEGRATION | spec-and-design, testing |
| `published_api` | **PA-1** breaking-change diff against previous schema. **PA-2** expand/contract with deprecation window. **PA-3** changelog + versioning D-entry. | S+ | COMPAT review | spec-and-design |
| `has_database` | **DB-1** versioned migrations applied to a local/ephemeral DB in tests. **DB-2** up-migration on a production-shaped fixture; restore procedure documented. **DB-3** single owner per entity. **DB-4** restore point (e.g. D1 Time Travel) recorded before remote apply. | DB-1/4 S+; DB-2 M+ | RESTORE-POINT | spec-and-design, testing |
| `data_migration` | **DM-1** data profile first. **DM-2** invariants as executable queries before/after. **DM-3** expand/contract; live: dual-write → backfill → shadow-read compare → switch reads → contract. **DM-4** dry run on a snapshot with timing. **DM-5** human approval before prod apply. **DM-6** restore rehearsal. | DM-1/2/5 S+; DM-3/4 M+; DM-6 L+ | DATA-PROFILED, SHADOW-PARITY, H-APPROVE | testing, orchestration |
| `concurrency_or_distributed_state` | **CD-1** state machines with illegal transitions. **CD-2** model-based property tests + targeted mutation. **CD-3** makers start at `mission-builder`. **CD-4** failure injection (crash points, duplicate delivery). | CD-3 S+; others M+ | PROPERTY, MUTATION | testing, debugging |
| `third_party_integrations` | **TP-1** providers behind a port with deterministic fake + oracle-bite per adapter. **TP-2** sanitised contract goldens from real responses. **TP-3** spend-bounded live canary, `PENDING-LIVE` until run. | TP-1 S+; TP-2 M+; TP-3 L+ or Release | CONTRACT, CANARY | testing |

### 4b. Risk, content and process traits

| Trait | Obligations | Floor → scaling | Gates | Method |
|---|---|---|---|---|
| `touches_auth` | **AU-1** named ASVS subset as acceptance items. **AU-2** negative authz tests (other user/tenant denied) for every new resource. **AU-3** security lens `mission-critic` in the panel. **AU-4** middleware ordering invariants as tests. **AU-5** iOS + account creation → in-app account deletion requirement. | AU-2/3/5 S+; AU-1 M+ | SECURITY, AUTHZ-NEG | review, testing |
| `touches_payments` | **PY-1** idempotency keys, webhook replay/duplicate tests. **PY-2** integer minor units or decimal type, property-tested. **PY-3** sandbox only in CI; live payment actions H-APPROVE. **PY-4** security lens + state-machine mutation. **PY-5** no visual experimentation on payment UI; platform-standard sheets. | S+ | PROPERTY, MUTATION, H-APPROVE | testing, review |
| `touches_pii` | **PI-1** data inventory (fields, purpose, retention, deletion path, readers). **PI-2** log/telemetry redaction test. **PI-3** no real PII in fixtures, research logs or prompts. **PI-4** retention/deletion requirements in spec; media storage-access review. **PI-5** check retention terms of any cloud/Routine path the data flows through. | PI-2/3 S+; PI-1/4 M+; PI-5 when cloud runs | PRIVACY, REDACTION | spec-and-design, memory |
| `has_ai_llm_features` | **AI-1** eval suite before prompt tuning: ≥20 tasks (L+: ≥50), outcome graders first, model graders calibrated (≥3 good + 3 bad). **AI-2** N≥3 trials, pass@k and pass^k. **AI-3** separate capability and regression suites. **AI-4** cost/latency per task tracked. **AI-5** prompt-injection and unsafe-output cases when user input reaches a model. **AI-6** model IDs pinned; provider fallback tested with a fake. | AI-1 S+ (S: ≥5 golden cases, 1 trial); AI-2/3 M+; AI-5 S+ | EVALS-DEFINED, EVAL-THRESHOLD | testing |
| `public_facing_content` | **PC-1** every factual/comparative claim bound to an S-id + access date; unsourced → cut or rephrased as opinion. **PC-2** fact-check pass (`mission-critic` for public claims). **PC-3** voice/messaging guide frozen before content lanes. **PC-4** build, link check, Lighthouse budget, meta/OG, sitemap. **PC-5** team bios, customer names, pricing, security claims → human sign-off; `[NEEDS-EVIDENCE]` blocks launch. | PC-1/2/4/5 S+; PC-3 M+ | CLAIMS-SOURCED, H-APPROVE publish | research, review |
| `needs_external_research` | **ER-1** question cards before searching. **ER-2** graded evidence + recheck-by dates in RESEARCH.md. **ER-3** L+: angle lanes + skeptic; sampled re-verification. **ER-4** design-driving vendor facts cited next to the decision. | ER-1/2 S+; ER-3 L+ | Research gate | research |
| `performance_sensitive` | **PF-1** numeric budget + measurement method in spec. **PF-2** committed benchmark harness before changes, ≥10 runs, variance reported. **PF-3** regression check at Verify/CI. **PF-4** iOS: on-device numbers (simulator for trend only). | PF-1 S+; PF-2/3 M+ (S: 5 runs before/after) | BASELINE-MEASURED, PERF-BUDGET | testing, debugging |
| `cross_repo_migration` | **XR-1** feasibility report ("don't migrate" allowed). **XR-2** parity inventory of old behaviour (endpoints, side effects, config, quotas, caching, logging, error shapes) captured before the move. **XR-3** portable parity judge validated on old-vs-old and against a deliberately broken build. **XR-4** strangler milestones: characterize → shadow → dual-run compare → switch by flag/percentage → retire. **XR-5** runbook with Evidence + Rollback per step and a rollback window. **XR-6** secrets/keys move → security lens. **XR-7** consumer inventory with a switch plan each. **XR-8** no behaviour change until parity. | XR-2/3/5/8 S+; XR-1/4/7 M+ | FEASIBILITY, PARITY-BASELINE, SHADOW-PARITY, CUTOVER (H-APPROVE), CONTRACTED | testing, spec-and-design |
| `deploy_to_production` | **DP-1** preview/staging deploy smoke-tested before prod. **DP-2** written rollback command, tested once (Workers: gradual deployment + rollback). **DP-3** canary checklist naming shared state that could mask differences. **DP-4** prod deploy is H-APPROVE enforced in settings/hooks. **DP-5** post-deploy verification; `PENDING-LIVE` until evidence. **DP-6** monitoring/alert on the new path. | DP-1/2/4/5 S+; DP-3/6 M+ | H-APPROVE, LIVE-VERIFIED | orchestration |
| `infra_or_ci_changes` | **IC-1** plan/dry-run output captured and reviewed. **IC-2** workflow and secret changes need human approval; frozen-path protection on `.github/workflows`, `.claude/`, hooks. **IC-3** no parallel writers. **IC-4** branch pipeline before main. | S+ | DRY-RUN-GREEN, H-APPROVE | swarms, testing |
| `classifier_sensitive_domain` | **CS-1** sensitive lanes default to Opus 4.8 agents. **CS-2** fallback events logged; unresolved refusal → BLOCKED-SAFETY; never rephrase. **CS-3** orchestrator receives summaries, not payloads. **CS-4** human informed when offensive-security work is in scope. | S+ | — | models-and-cost |
| `long_running` | **LR-1** HANDOFF at session end or ~60% context. **LR-2** session-start ritual. **LR-3** milestone branches/worktrees. **LR-4** continuation: Routine → `claude -p` script → manual resume. **LR-5** budget review at every phase boundary. | S+ once triggered | session gates | orchestration, memory |
| `unattended` | **UN-1** no irreversible actions; queue BLOCKED-HUMAN and continue elsewhere. **UN-2** end in draft PRs, never merges. **UN-3** `--max-budget-usd` or equivalent hard cap. **UN-4** pre-allowlisted permissions only; Stop-hook enforcement on. | S+ | — | orchestration |
| `design_quality_matters` | **DQ-1** 2–3 reference apps/sites (asked or proposed); tokens before first screen. **DQ-2** craft rubric thresholds by class. **DQ-3** pairwise position-swapped tournament for visual direction, hero, naming. **DQ-4** batched blinded human review per milestone. **DQ-5** AI-default tells checklist. | DQ-2 S+; DQ-1/3/5 M+; DQ-4 L+ | RUBRIC, HUMAN-BATCH | frontend-verification |
| `localized` | **LO-1** longest-language/pseudo-locale screenshot pass. **LO-2** RTL if supported. **LO-3** hard-coded strings lint. | LO-3 S+; LO-1/2 M+ | VISUAL-L10N | frontend-verification |
| `live_incident` | **LI-1** mitigate first (rollback, flag off); mitigation ≠ resolution. **LI-2** timeline log. **LI-3** full BUG pipeline on the unmitigated build in non-prod. **LI-4** postmortem with a generic control. | S+ | MITIGATED → REPRODUCED | debugging |

## 5. Composition rules

- **CMP-1 Canonical order.** All shapes merge into phases 0–9. Shape gates are *inserted* (e.g. REPRODUCED between
  Research and Spec), never reordered.
- **CMP-2 Secondary-shape order.** RSR first (its decision can change everything) → baseline-capturing shapes (MIG,
  REF, UPG, DAT, PRF) establish gate zero before behaviour-changing shapes touch shared code → SEC threat model enters
  at Design → INF pipeline arrives with the GRN walking skeleton → OPS last.
- **CMP-3 Deduplicate.** Same obligation ID merges; parameters take the maximum (trial counts, reviewer tier, sample
  sizes, caps). Review lenses merge into one panel.
- **CMP-4 Precedence on conflict** (log each in DECISIONS.md): safety and irreversibility controls > correctness
  oracles (parity, repro, evals) > user-facing quality > cost and speed.
- **CMP-5 Known conflicts.** Frequent deploys vs data migration → expand/contract, contract only after reads switched
  and verified. Design tournaments vs payments → tournaments on non-payment surfaces only. Unattended vs production
  deploy → never deploy unattended; queue BLOCKED-HUMAN. Sensitive domain vs Fable orchestrator → sensitive lanes on
  Opus 4.8, orchestrator sees summaries. Migration + feature request → feature becomes a post-parity FEA milestone.
- **CMP-6 Budget.** Obligations are costed at Plan against the phase allocation (plan/spec/arch 15%, research 10%,
  build 45%, verify/review 20%, reserve 10%). If they exceed the reserve, re-plan or raise class; never drop them.

## 6. Per-shape pipelines

Inserted gates in CAPS. Model deviations are relative to `models-and-cost.md`.

| Shape | Pipeline | Swarm usage | Model deviations | Done criteria |
|---|---|---|---|---|
| GRN | 0 → 1 research (platform limits, reference apps) → 2 CHARTER-SIGNED → 3 design → M0 CONTRACT-FROZEN → 4 → 5 M1 SKELETON-LIVE → milestone loops (5–7) → 8 → 9 | only after M0: backend lane, per-platform client lanes, contract-test lane; design proposals tournament → one writer | charter/spec synthesis `mission-strategist`; design `mission-builder`; architecture review `mission-critic` | all P1 journeys green on each platform against deployed dev/staging; trait release gates; human batch review passed |
| FEA | 0 → CONVENTIONS-MAPPED → 2 mini spec (+ metric definitions) → 3 short design → 4 → 5 spine lane then widget lanes → 6 → 7 → 8 behind flag → 9 | reader lane; spine merges first; ≤4 widget lanes | defaults | criteria tests + 1–3 journeys green; affected suites green; flag-off check; UI gates |
| BUG | 0 failure record → check the plug → REPRODUCED → isolate (bisect, differential) → hypothesis ledger → CONFIRMED (two-way, separate confirmer) → fix → PROVEN → sibling sweep → 7 → 9 conversion | experiment lanes only if REPRODUCED + ≥3 independent open hypotheses; one writer | investigator `mission-builder`; reset `mission-strategist` after 2 stalled rounds | repro red→green in clean worktree; flaky: n ≥ ln(α)/ln(1−p) clean runs; sweep dispositioned; suite green; control added |
| MIG | 0 → FEASIBILITY → parity inventory → PARITY-BASELINE → 2 spec (keep/drop/change) → 3 design (seams, data/secret move) → 4 strangler milestones → 5 build in new home → SHADOW-PARITY → CUTOVER per consumer (H-APPROVE) → soak → CONTRACTED → 9 | reader lanes for inventory; per-endpoint lanes after the shared shim lands serially; one writer per shared interface | judge author `mission-builder`; plan `mission-strategist` at L/XL; secrets lens `mission-critic` | judge passes on new path; old suite re-run on old path with zero inherited failures; consumers switched; old path retired or kept by D-entry |
| REF | 0 → PARITY-BASELINE → rulebook + pilot → per-unit implement + review → parity burn-down → 7 → 9 | homogeneous per-unit fan-out via workflow when ≥10 units | reviewers on a different model than makers | architecture lint green; judge reports no behaviour diff |
| UPG | 0 → changelog research → PARITY-BASELINE → one major at a time → codemods → deprecations → 6 → 8 → 9 | none for coupled bumps; lockfile-bisection lanes for regressions | `mission-worker-high` default; `mission-builder` for toolchain breakage | suite green on new version; zero new deprecations in touched code; rollback = revert PR |
| DAT | 0 → DATA-PROFILED → invariants as queries → 3 expand/contract design → RESTORE-POINT → snapshot dry run → H-APPROVE → expand → backfill → SHADOW-PARITY → switch reads → CONTRACTED → 9 | none (shared schema) | migration author `mission-builder` | invariants identical before/after or diff explained by spec; restore rehearsed at L+ |
| PRF | 0 → BASELINE-MEASURED → profile → hypothesis per hotspot → change → measure ≥10 runs → regression check → 7 → 9 | experiment lanes in own worktrees with own runtime; best one merges | analysis `mission-reviewer`; lanes `mission-worker-high` | metric past target with variance; no functional regression; perf check committed |
| INF | 0 → DRY-RUN-GREEN → branch pipeline → H-APPROVE → apply → LIVE-VERIFIED → 9 | none | `mission-builder` for secrets/permissions | pipeline green on branch and main; rollback tested; secret scan clean |
| SEC | 0 → THREAT-MODEL → audit lanes by lens → findings → refutation → dispositions → fixes (BUG-lite each) → 6 → 9 controls | parallel read-only audit lanes; one writer per fix | all audit lanes Opus 4.8 (`mission-critic`); never Fable for exploit reasoning | every CONFIRMED blocker/major FIXED with failing-without-fix test or accepted-risk D-entry; controls for recurring classes |
| WEB | 0 → research (RSR) → CLAIMS-SOURCED → positioning + message hierarchy + sitemap + page inventory → 3 visual direction tournament → tokens → 5 spine shell → page/content lanes (frozen voice guide) → docs IA → 6 build/links/Lighthouse/visual/fact-check → H-APPROVE publish → 9 | research angle lanes + skeptic; content lanes after voice guide freezes | synthesizer `mission-builder` (`mission-strategist` at XL); fact-check `mission-critic` | deployed preview then prod; zero unsourced claims; link check clean; budgets met; docs tree test ≤3 clicks; human publish sign-off |
| RSR | 0 → QUESTION-FRAMED → research/prototype → synthesis → skeptic review → decision memo / ADR → 9 | angle lanes; best-of-N prototypes | synthesizer `mission-builder` | question answered with cited evidence and confidence; prototype not merged |
| OPS | 0 → runbook + classification rules → eval cases from past incidents → RUNBOOK-DRY-RUN → schedule (Routine / cron `claude -p`) → 9 weekly eval refresh | per-item fan-out only for batch triage | classifier `mission-checker` with 5% double-classify audit | dry run matches human triage on ≥90% of eval cases (proposed threshold); UN-1..4 in force |

### Shape × class

| Shape | S | M | L | XL |
|---|---|---|---|---|
| GRN | not allowed (re-classify as RSR prototype or FEA scaffold) | internal single-platform tool: charter-lite, skeleton, 1–2 milestones | single-platform product with backend: full spec, contract-lite M0, ≥3 milestones | multi-platform: M0 contract + testkit, skeleton, L-mission milestones, human batches |
| FEA | small UI/API tweak: task card, 1 test, 1 screenshot | dashboard/page: mini spec, spine + widgets, journeys | cross-component feature: designs, lens panel, flag rollout | treat as GRN within the product |
| BUG | known location: inline record, failing test first, one grep sweep | ledger file, 2h repro budget, differentials | multi-layer: experiment lanes, live recurrence check, postmortem | incident scale: mitigate first, O-id per cause, drill |
| MIG | config/endpoint move inside one repo: parity test + flag | one service, few consumers: judge + shadow | gateway/service extraction: full strangler + runbook | platform consolidation: per-service L missions behind a shared judge |
| WEB | docs page edit: build + link check | landing page with sourced claims | site with research, blog, docs | multi-product localized site |

## 7. Worked examples (illustrations)

**1. "A fashion/outfit iOS app with a Cloudflare backend and native Swift frontend."** GRN; traits `multi_platform`,
`has_ios`, `has_backend_api`, `has_database`, `touches_auth`, `touches_pii` (wardrobe photos), `has_ai_llm_features`
(unknown → question), `design_quality_matters`, `deploy_to_production`, `third_party_integrations`, `long_running`.
Scores B3 D3 U2 C3 → XL. Questions: AI-generated or rule-based outfits (default: model-based with evals); accounts +
cloud photo storage or on-device (default: accounts + R2 → AU-5, PI-1/4); 2–3 reference apps (default: proposed and
ASSUMED). Runs: research lanes (Workers/D1/R2 limits, image pipeline, SwiftUI patterns, competitor apps) → strategist
charter + spec (domains AUTH, WARDROBE, OUTFIT, FEED) → spec sign-off → builder designs (D1 vs Durable Objects ADR,
R2 signed URLs, IA, tokens) → visual direction tournament → **M0** OpenAPI + generated Swift client + TS types +
contract tests + provider fakes → **M1 SKELETON-LIVE** (Sign in with Apple → upload one garment → stored → list
renders, XCUITest against the dev Worker) → M2 wardrobe, M3 outfit generation (≥50 eval tasks, outcome grader "every
outfit uses only garments the user owns", calibrated style-coherence grader, 3 trials) → release (TestFlight, IO-6,
gradual Worker deploy, restore point). After M0: backend + iOS + contract-test lanes, per-lane simulators. Done: P1
journeys green on the simulator matrix against staging, eval threshold met, store readiness, LIVE-VERIFIED canary.

**2. "Find this deep annoying bug and fix it."** BUG; `existing_codebase` + whatever triage finds. B1 D1 U3 C0 → M
+1 → L, but ceremony stays BUG-shaped (the spec is the repro). One question only if no symptom evidence exists
("where and how often?"; default: search logs, issues, CI history first). Runs: failure record → check the plug →
REPRODUCED with baseline rate p → bisect/differential → ledger ≥3 hypotheses across layers → experiment lanes if the
precondition holds → CONFIRMED by `mission-reviewer` two-way intervention → fix → PROVEN (n ≥ ln(0.05)/ln(1−p) clean
runs, doubled if state can't reset) → sweep → review ≤3 rounds → regression test + control + inbox lesson. Re-classify
if the root cause is data corruption (add DAT) or the fix changes a public contract (add `published_api`).

**3. "Add this new dashboard to the existing product."** FEA; `existing_codebase`, `has_web_frontend`,
`has_backend_api` (aggregate endpoint), `has_database` (read path), `touches_auth` (tenant visibility; forcing if RBAC
exists), `performance_sensitive` if volumes are large (probe row counts). B1 D1 U1 C1 → M. Runs: reader lane →
CONTEXT.md → mini spec with metric definitions (source, formula, timezone, refresh, empty/partial) + authz rule → short
design reusing chart/table components, index check → spine lane (route, layout, flag, data hook) → ≤4 widget lanes →
Verify: criteria tests, journeys on seeded data asserting displayed aggregates equal SQL expectations, AU-2 negative
test, G1–G3 → panel (correctness + UX) → flag rollout with a screenshot summary.

**4. "Move our AI gateway from an external project into a core platform service."** MIG (+ DAT if usage logs, keys or
quotas move); `cross_repo_migration`, `has_backend_api`, `has_ai_llm_features`, `touches_auth` (API keys),
`third_party_integrations`, `deploy_to_production`, `existing_codebase`, `long_running`. B2 D2 U2 C2 → L (XL if
external customers call it directly). Questions: who calls it today; does the old project stay alive; behaviour
changes wanted (default: none until parity, then a post-parity FEA milestone). Runs: FEASIBILITY (`mission-builder`) →
parity inventory (reader lanes; a script diffs the route dump against the inventory) → PARITY-BASELINE (recorded request
corpus replayed against the old gateway with fake providers, normalising differential runner, oracle-bite on a broken
build) → spec + design (seams, key custody with security lens, consumer switch plan, runbook with Evidence + Rollback)
→ per-endpoint lanes after the shared shim → SHADOW-PARITY → CUTOVER per consumer (H-APPROVE) → soak → CONTRACTED.
Merged obligations: XR-1..8, AU-1..3 (one panel member with XR-6), TP-1..3, AI-6, DP-1..6.

**5. "Research our market position, create a website describing project, goals, team, with blog and docs."** WEB
primary, RSR secondary (runs first); `public_facing_content`, `needs_external_research`, `has_web_frontend`,
`design_quality_matters`, `deploy_to_production`, `touches_pii` (team bios/photos: consent), `existing_codebase` (docs
source). B1 D2 U2 C1 → L. Questions: audience priority; hosting/domain and publish policy (default: preview deploy,
publish H-APPROVE); source of team details (default: team page waits in BLOCKED-HUMAN; no placeholder people). Runs:
QUESTION-FRAMED → 3–6 angle lanes (competitors, category vocabulary, audience pain evidence, pricing norms,
differentiators checked against the repo) + skeptic → positioning memo + claim register → CLAIMS-SOURCED → sitemap +
page inventory (home, goals, team, blog index/post, docs landing + tree from existing docs) → tournament of 3 rendered
directions → tokens → spine shell → page/content lanes (every factual sentence carries an S-id) → Verify: build, links,
Lighthouse, axe, G2 matrix, AI-tells, fact-check → H-APPROVE publish.

## Model routing

| Role | Agent | Guard |
|---|---|---|
| Repository probe | `scripts/probe-signals.sh` (no model) | deterministic; forcing rules |
| Classification | orchestrator (prompt and signals are small and already in context) | forcing rules; blind second opinion at L/XL; retro audit |
| Blind second classifier (L/XL) | `mission-reviewer` without your profile | disagreement on forking fields → adjudicate or ask |
| Trait probes (`unknown` → present/absent) | `mission-scout` | must return file:line; no evidence stays `unknown` |
| Pipeline planning | orchestrator; `mission-strategist` at L/XL | plan critique by `mission-critic`; gate-zero-before-code lint |
| Retro classification audit | `mission-reviewer` (every L/XL mission, 1 in 5 M missions) | same missed trait twice → add a forcing rule to this file at retro |

## Anti-patterns

- One label instead of shape + class + traits; risk traits inflating class (an S payment bug is still S, with PY gates).
- Marking a trait absent without evidence; skipping obligations without a D-entry.
- Mixing parity work and feature work in one PR.
- Greenfield fan-out before the contract freezes; green offline suites over mocks declared "done" without a live
  walking skeleton (the user's own XL project finished every milestone offline with nothing real wired).
- Asking the human about non-forking unknowns; asking more than 3 questions per round.
- Ceremony by habit: charters and review panels on S work.

## Unverified harness details

- Android tooling (screenshot and instrumented test libraries) was written by analogy; verify at intake.
- `scripts/probe-signals.sh` markers are heuristics; treat misses as `unknown`, not `absent`.
- Budget caps and thresholds (OPS ≥90%, eval task counts) are proposed defaults; calibrate from BUDGET.md ledgers and
  retro audits after three missions.

## Evidence

- Research lane 11: `research/mission-skill/11-project-shapes-conditionals.md` (§4–6).
- Anthropic code migration kit: https://github.com/anthropics/code-migration-kit-with-claude-code
- Strangler fig / parallel change: https://martinfowler.com/bliki/StranglerFigApplication.html
- Claude Code best practices (scale process to scope): https://code.claude.com/docs/en/best-practices
- Anthropic evals guidance: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Cloudflare Workers Vitest integration: https://developers.cloudflare.com/workers/testing/vitest-integration/
- arcwell walking-skeleton gap: `arcwell/docs/operations/gap-closure-plan.md:3-22`
- arcwell cutover runbook: `arcwell/docs/operations/cutover-runbook.md`
