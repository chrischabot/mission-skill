# Models and cost

Model IDs, prices and the agent roster are canonical in `references/conventions.md` §6–§8; this file says how to use
them. Notation: **F** `claude-fable-5-1` · **O** `claude-opus-4-8` · **S** `claude-sonnet-4-6`; effort after `·`.
No Haiku anywhere: Sonnet 4.6 at low effort (`mission-checker`, `mission-scout`, `Explore`) takes those roles.

## When to load

| Moment | What you need from this file |
|---|---|
| Phase 0 Intake | PF preflight, profile choice, `BUDGET.md` caps (CB1, scope caps table) |
| Phase 4 Plan | Agent per task (Model routing matrix), ES4 risky-area check, fan-out bounds (CB7), budget per milestone |
| A task fails its gate twice at one rung | ES ladder, `templates/escalation-brief.md` |
| Accepting output from a Sonnet-tier agent | GD guards: grader choice, seeded canary, sampled blind audit (`templates/audit-prompt.md`) |
| A refusal, classifier flag or unexpected answering model | CF rules |
| Every phase boundary, soft cap, hard cap | CB3–CB5 review, CF3 model re-assertion, ES6/ES7 role moves |
| Before editing models or agent files | "How to change models" |

## Core rules

### Routing (MR)

- **MR1 MUST** reference models only by full ID. Aliases (`opus`, `sonnet`, `fable`, `best`, `default`, `opusplan`)
  are forbidden in agent files, scripts, `--model` flags and Agent-tool overrides: on the Anthropic API `opus` and
  `sonnet` resolve to Opus 5 / Sonnet 5. `scripts/preflight.sh` fails on any alias or non-roster ID.
- **MR2 MUST** spawn every sub-agent through a roster file (conventions §7) chosen from the matrix in Model routing. An
  ad-hoc general-purpose spawn MUST pass an explicit full-ID `model`.
- **MR3 MUST NOT** run on Fable (`mission-strategist`, `mission-strategist-review`): doc updates, lint/format fixes,
  simple refactors, test scaffolding, search fetch-and-summarise, classification, ledger/state bookkeeping, mechanical
  merge conflicts, code implementation.
- **MR4 MUST** default makers to `mission-worker` (S · medium). Higher tiers need a matrix row, an ES4 area or an ES
  rung as the reason.
- **MR5 SHOULD** use Fable only for: the orchestrator on M/L/XL; charter/spec synthesis, architecture and swarm planning
  on L/XL; hypothesis-space reset after a `mission-builder` investigation stalled (immediately when the bug is
  non-reproducible, cross-system or survived prior human attempts); the XL consolidated review lens and XL milestone
  design review; XL retro distillation.
- **MR6 MUST** run the orchestrator as the session model: F · medium on M/L/XL (high for intake, spec/design gates and
  adjudication); O · high on S. Lean profile: O · high on every class.
- **MR7 MUST** install the project `Explore` agent (S · low) so built-in exploration never inherits the orchestrator's
  top-tier model (built-in Explore inherits the main model, capped at Opus).
- **MR8 MUST NOT** switch the orchestrator's model mid-mission (`/model`); each model has its own prompt cache and a
  switch re-reads the whole history uncached. Escalate by spawning a different agent file or passing `model` on the
  Agent call. Change orchestrator effort only at phase or gate boundaries.
- **MR9 MUST NOT** set `max` effort anywhere. `xhigh` is used only by the Degraded-profile Opus orchestrator. Sonnet 4.6
  has no `xhigh`.
- **MR10 MAY**, where dynamic workflows are available, route per call with `agent()` options (model + `opts.effort`);
  the same matrix, IDs and efforts apply.

Effort is frontmatter-only; the Agent tool overrides `model` per call but not effort. A one-off tier-up is therefore
"`<agent>` with Agent-tool `model` override" and keeps that file's effort; a different effort needs a different file.

### Escalation and de-escalation (ES)

- **ES1 MUST** climb the maker ladder one rung at a time and log each rung in `BUDGET.md → Escalations`:
  `mission-worker` → `mission-worker-high` → `mission-builder` → `mission-strategist` → human (`BLOCKED-HUMAN`).
- **ES2 MUST** escalate after **2 failed attempts at the same rung** on the same task. "Failed" = a named gate (test,
  typecheck, rubric criterion, CONFIRMED blocker/major) is still red. Never a third attempt at one rung.
- **ES3 MUST** start each rung in a fresh context holding only: the unchanged brief, the red gate output (path or last 30
  lines), a ≤300-word failure summary, and the current diff pointer (`templates/escalation-brief.md`). Never pass the
  failing agent's transcript.
- **ES4 MUST** start at `mission-builder` (maker and test author) when the task touches auth, payments, data
  migrations, concurrency, security boundaries, public API contracts, or infra/CI configuration. The ladder then
  continues from `mission-builder`.
- **ES5 SHOULD** use the Fable rung only with a written ledger reason ("mission-builder failed: <gate>", or
  "non-reproducible / cross-system"). Max 2 Fable attempts per task, then human. `mission-strategist` writes docs only:
  it returns a root-cause statement, a revised plan or design; the implementation is re-issued to `mission-builder`
  with that document.
- **ES6 SHOULD** de-escalate a role one rung for the rest of the phase after its last 5 consecutive outputs passed gates
  first time **and** the phase audit (GD4) found no disagreement. Never below the role's floor, never in ES4 areas.
- **ES7 MUST** promote a role one rung for the rest of the mission after 2 audit disagreements in one phase, a second
  canary miss (GD3), or a first-pass gate rate below 60% over ≥5 tasks (GD6). Write a D-entry and a
  `LESSONS-INBOX.md` candidate ("role X on tier Y missed Z").
- **ES8 MUST** count as a failed attempt: context exhaustion, looping, a return without the required format, edits
  outside owned paths, or any write to a frozen path.

### Guarding downgrades (GD)

- **GD1 MUST** gate maker output with deterministic oracles first: tests, typecheck, lint, build, schema validation,
  `.mission/check.sh`, `scripts/validate-registry.py`, `scripts/test-diff-grep.sh`, geometry/a11y probes, screenshot
  diffs. A model grader never re-derives what a command can prove; it judges only what code cannot.
- **GD2 MUST** judge a Sonnet maker's output with a grader on a **different model**: minimum `mission-reviewer`
  (O · medium); `mission-critic` for adversarial lenses. `mission-verifier` (S · high) MAY be the per-task verifier of
  Sonnet makers only because its verdicts rest on re-run commands and the test-diff audit; any criterion it cannot
  decide from command output is `UNVERIFIED` and goes to `mission-reviewer`. Opus/Fable makers SHOULD be graded by an
  agent differing in model or effort; the roster pairing `mission-builder` → `mission-critic` (same O · high) is
  allowed with a fresh context, an adversarial lens, GD1 oracles first and GD4 audits.
- **GD3 MAY** use `mission-checker` (S · low) only for checklist verdicts over deterministic evidence ("exit 0 and 0
  failures", "every item cites file:line", "JSON matches schema", "no `.skip` in the diff"). **Seeded-defect canary
  (MUST):** in the first checklist batch of each phase, and at least 1 per 20 items after that, plant one known-bad
  item (log with non-zero exit, missing citation, a `.only`/`XCTSkip` in a diff, a schema violation) whose expected
  verdict is FAIL. The canary ID lives in `BUDGET.md → Downgrade guards`, never in the brief. Canaries apply to
  `mission-checker` and to `mission-verifier` checklist runs (test-diff audits, citation checks). A PASS on a canary
  voids that batch: re-run it on the next tier (`mission-verifier`, then `mission-reviewer`) and log the miss; a second
  miss in the mission triggers ES7.
- **GD4 MUST** run a **sampled blind audit** every phase: re-grade ≥10% (minimum 1, maximum 5) of accepted outputs from
  Sonnet-tier agents (`mission-worker`, `mission-worker-high`, `mission-verifier`, `mission-checker`, `mission-scout`)
  with `mission-critic` using `templates/audit-prompt.md`, blind to the first verdict. Pick samples by random draw
  from the spawn log, weighted toward ES4 areas and "no findings" verdicts. Record agreement in `BUDGET.md`.
- **GD5 MUST** treat an audit disagreement as a process defect: fix the artifact (its gate reopens), apply ES7 when the
  threshold is met, and audit that role's next 2 accepted outputs.
- **GD6 SHOULD** track per role: first-pass gate rate, rework count, audit agreement, canary misses, cost per accepted
  task. First-pass gate rate below 60% over ≥5 tasks → ES7.
- **GD7 SHOULD** cascade classification: `mission-checker` classifies with a `confidence: high|low` tag; low confidence
  or a risky label (ES4 list, classifier-sensitive domain) re-classifies on `mission-reviewer`. OPS missions
  double-classify 5% as an audit.
- **GD8 MUST** keep the adversarial reviewer of any change headed to merge on a different model than the maker, or,
  when the maker is `mission-builder`, on a different lens with GD1 oracles and refutation first. Risky merges (auth,
  payments, PII) keep the human checkpoint; XL adds the `mission-strategist-review` consolidated lens.

### Classifier fallback (CF)

- **CF1 MUST** pre-route exploit development, pentest logic, malware analysis, CVE proof-of-concept and offensive
  tooling to Opus 4.8 agents (`mission-builder` to write, `mission-critic` to review); never on Fable. Vulnerability
  discovery in the project's own code stays on the normal matrix. Tell the human when offensive work is in scope and
  get sign-off before anything runs against live systems.
- **CF2 MUST** record every refusal, classifier flag or unexpected answering model in `STATUS.md → Model / fallback
  events` (time, task, role, requested model @ effort, answering model, category if known, action) and mark the
  spawn-log row `refused` or `fallback`.
- **CF3 MUST** re-assert the orchestrator's intended model at each phase boundary: read the active model (status line,
  `/model`, or the per-model breakdown of headless `--output-format json`); if it drifted after a fallback (the switch
  is sticky for the session), restore it with `/model claude-fable-5-1` and log the restore. Interactive sessions that
  cannot self-restore queue a one-line human action.
- **CF4 MUST** re-issue a refused worker task explicitly to an Opus 4.8 agent with the same brief (`mission-builder`
  for makers, `mission-critic` for read-only roles). A second refusal on Opus → task `BLOCKED-SAFETY`, human queue
  entry with the category.
- **CF5 MUST NOT** rewrite, obfuscate, split or rephrase a brief to get past a classifier. Agents that hit a refusal
  return `BLOCKED-SAFETY`.
- **CF6 SHOULD** tag biology/life-sciences missions: automatic reroutes there may be answered by Opus 5, outside the
  user's model set. Log the event and ask the human before continuing those tasks (`BLOCKED-HUMAN`).

### Budget and ledger (CB)

- **CB1 MUST** create `.mission/BUDGET.md` from `templates/BUDGET.md` at intake with class, profile, billing regime
  (API dollars or plan-usage %), soft/hard caps from the scope caps table, and the phase allocation. S missions without
  `.mission/` keep three budget lines in the task card.
- **CB2 MUST** append one spawn-log row per agent run: task, role, agent file, **resolved** model, effort, rung,
  tokens (input / cache read / cache write / output) or estimate, outcome (`accepted` · `failed-gate` · `refused` ·
  `fallback` · `void`), evidence pointer. Rows come from headless JSON (`total_cost_usd`, per-model breakdown) or
  `/usage` deltas, written by `mission-checker` in batches; the orchestrator reads summaries, not rows.
- **CB3 MUST** review the ledger at every phase boundary (checklist in `templates/BUDGET.md`): spend vs allocation, cost
  per accepted task by role, audit agreement, canary misses, fallbacks, fan-out. Spend >150% of a phase allocation →
  written re-plan (D-entry) before the next spawn. A role costing >2× its peers per accepted task → look for loops,
  oversized briefs or cache misses.
- **CB4 MUST** pause at the soft cap: write STATUS, propose a narrowed plan, continue only after a recorded decision
  (autonomous mode: continue on the narrowed plan inside the remaining reserve with a D-entry; raising the cap is a
  human decision). Stop at the hard cap (`STOP-BUDGET`, HANDOFF written, work preserved). A budget ceiling is a WAIT,
  not a verdict. Headless runs pass `--max-budget-usd <remaining hard cap>` when the flag exists.
- **CB5 MUST** apply the marginal-value stop: end any loop, review round series or investigation after 2 consecutive
  iterations with no newly green gate and no newly verified finding (`STOP-STALLED`), whatever budget remains.
- **CB6 SHOULD** treat `/usage` and headless dollar figures as local list-price estimates; reconcile real spend in the
  Console. US-only inference bills 1.1×. Subscription users: record plan-usage % instead of dollars.
- **CB7 MUST** keep fan-out inside the scope caps table; any wider wave needs a one-line value case in the ledger and a
  D-entry. Multi-agent runs use roughly 15× the tokens of a chat, and every extra agent pays its own cold cache write.
- **CB8 SHOULD** run sequentially when subtasks share files or consume each other's outputs; parallelise only research
  angles, independent reviewers and file-disjoint implementation.

**Scope caps table** (starting defaults; calibrate from ledgers after 3 missions):

| Class | Orchestrator (Standard) | Writers per wave / max concurrent agents | Max spawns per phase | Soft / hard cap (API USD) | Fable allowed for |
|---|---|---|---|---|---|
| S | O · high | 2 / 3 | 10 | 8 / 20 | nothing by default; ES5 rung only, with ledger reason |
| M | F · medium | 4 / 5 | 40 | 50 / 120 | orchestrator; ES5 rung; hypothesis reset |
| L | F · medium (high at gates) | 8 / 8 | 120 | 300 / 700 | + charter/spec synthesis, architecture, swarm planning |
| XL | F · medium (high at gates) | 12 / 15 | 150 per session; split sessions per phase | 1,500 / 3,500 | + consolidated review lens, XL milestone design review, XL retro distillation |

Read-only lanes inside a dynamic workflow: ≤16. Sanity anchor: enterprise Claude Code averages about 13 USD per
developer per active day; an S mission costing more than a developer-day is over-orchestrated.

**Phase allocation of the cap:** plan/spec/architecture 15% · research 10% · build 45% · verify/review/audit 20% ·
reserve 10%. No research phase → its 10% goes to verification. UI-heavy or multi-platform missions: verification ≥20%
before reserve. Obligations from `shapes-and-scope.md` are costed against these at Plan; if they exceed the reserve,
re-plan or raise the class — never drop them.

### Context and caching (CX)

- **CX1 MUST** write briefs cache-first: role preamble (the agent file) → stable mission context pointer
  (`.mission/CONTEXT.md`, SPEC/STATE paths) → task-specific section → required return format. Timestamps, run IDs and
  the variable task text go last. Workers of one role share one agent file and the same leading brief text.
- **CX2 MUST** pass paths and short excerpts, never whole files or raw logs; workers read what they need.
- **CX3 MUST NOT** connect/disconnect MCP servers, toggle plugins, change permission sets or edit installed agent files
  during a phase; each invalidates caches. Load skill references lazily (they append, the prefix stays intact).
- **CX4 SHOULD** cap sub-agent returns at ≤400 words plus pointers; larger artifacts go to `.mission/lanes/<id>/`.
- **CX5 SHOULD** compact or hand off the orchestrator only at phase boundaries after STATE/STATUS are written; prefer a
  context reset with `HANDOFF.md` at ~60% context over repeated compaction.

### Preflight and degradation (PF)

- **PF1 MUST** at intake run `.mission/bin/preflight.sh` (or `scripts/preflight.sh --repo <path>` before init) and save
  its output to `.mission/logs/preflight.txt`. It checks: `CLAUDE_CODE_SUBAGENT_MODEL` unset; `claude --version` ≥
  v2.1.257 (Fable 5.1) and ≥ v2.1.154 (Opus 4.8); every roster file present with a full-ID `model`. On M+ also spawn one
  tiny probe per model ID (`mission-scout` for S, `mission-reviewer` for O, `mission-strategist-review` for F; prompt
  "Reply OK") and confirm the answering model in `/usage` by-model or headless JSON. A worker silently running on the
  orchestrator's model costs ≈3× plan.
- **PF2 MUST** switch to the Degraded profile when a model is unavailable or the version floor fails (see Profiles).
  Record the profile in the STATUS header and a D-entry.
- **PF3 MUST**, in harnesses without per-agent model selection, run roles as separate sessions (`claude -p --model
  <full id>`), keeping maker and grader in different sessions.
- **PF4 SHOULD** warn subscription users that Fable-heavy missions consume plan limits quickly and offer Lean; flag
  that Fable use requires 30-day data retention by default for missions with sensitive data.

## Procedure

1. **Preflight (Phase 0).** Run preflight (PF1). Hard failure → fix (unset the env var, reinstall agents with
   `scripts/init-mission.sh --force-agents`, upgrade Claude Code) or pick Degraded (PF2). Probe spawns on M+.
2. **Profile.** Standard unless: user asks for minimum cost or is on a subscription → Lean; a model unavailable →
   Degraded. Write `Orchestrator: <id @ effort> · Profile: <…>` in the STATUS header. If the session is not on the
   intended orchestrator model, ask the user to switch once (`/model claude-fable-5-1`, effort medium) or continue on
   Lean with a D-entry.
3. **Budget.** Create `BUDGET.md` (CB1) with caps and allocation from the scope caps table.
4. **Plan (Phase 4).** For each task pick the agent from the matrix; apply ES4; set the rung-1 agent in the PLAN task
   and the STATUS board (`agent · model · effort`). Check wave sizes against the caps table (CB7) and cost each
   milestone against its allocation.
5. **Spawn.** Fill the brief cache-first (CX1). Use the roster file; use an Agent-tool `model` override only for a
   logged one-off tier-up. Batch-log spawn rows (CB2).
6. **Accept or fail.** Deterministic gate first (GD1) → grader chosen by GD2/GD3 → verdict. A red gate counts toward
   ES2; after 2 fails at one rung, fill `templates/escalation-brief.md` and spawn the next rung in a fresh context (ES3).
7. **Guards.** Seed canaries into checklist batches (GD3). At phase end draw the GD4 sample and run `mission-critic`
   with `templates/audit-prompt.md`; compare verdicts; record; apply GD5/ES7.
8. **Refusals.** Apply CF1–CF6 the moment a refusal, flag or unexpected answering model appears.
9. **Phase boundary.** Run the `BUDGET.md` phase-boundary checklist: CB3 spend review, CF3 model re-assertion, CB5
   marginal-value test, ES6/ES7 role moves, CB7 fan-out check. Soft cap → CB4 pause; hard cap → `STOP-BUDGET`.
10. **Retro (Phase 9).** Report cost by role and per accepted task, audit agreement, canary misses, promotions and
    de-escalations. Routing lessons ("role X needs tier Y for Z") go to `LESSONS-INBOX.md`.

## Scale by class (S/M/L/XL)

| Aspect | S | M | L | XL |
|---|---|---|---|---|
| Orchestrator | O · high | F · medium | F · medium; high at intake, spec/design gates, adjudication | same as L; per-phase sessions |
| `mission-strategist` | ES5 rung only | ES5 rung, hypothesis reset | + charter/spec synthesis, architecture, swarm planning | + XL retro distillation |
| `mission-strategist-review` | — | — | — (use `mission-critic`) | consolidated review lens, milestone design review, flagship-screen tie-break |
| Ledger | 3 lines in task card / STATUS Budget | `BUDGET.md` spawn log + phase reviews | + per-milestone allocation | per-milestone ledger section; session split per phase |
| Preflight | script only | script + 3 probe spawns | same as M | same, rerun at each new session |
| GD3 canary | first checklist batch | per phase | per phase + 1 per 20 items | same as L |
| GD4 audit | 1 sample at Verify | ≥10% per phase (1–5) | ≥10% per phase (1–5) | ≥10% per milestone phase (1–5) |
| CF3 re-assertion | at Verify | every phase boundary | every phase boundary | every phase boundary and session start |

## Shape conditionals

- **IF** greenfield multi-platform app (e.g. iOS + Cloudflare backend) **THEN** class ≥ L; charter/spec synthesis and
  architecture on `mission-strategist`; screen/backend design docs on `mission-builder`; one implementer brief variant
  per platform so briefs and caches stay platform-stable; contract tests and platform builds (`xcodebuild`,
  `wrangler`) are the first gates so model graders judge only UX and design; per-screen vision `mission-reviewer`,
  flagship tie-breaks `mission-strategist-review` (XL); verification ≥20% of budget.
- **IF** deep bug hunt **THEN** orchestrator stays the class default (S: O · high); repro and flake work on
  `mission-worker-high`; investigator `mission-builder`; no deterministic repro after 2 attempts, or non-reproducible /
  cross-system → `mission-strategist` hypothesis reset with the failure notes (ES5); parallel experiment lanes ≤3
  (`mission-worker`), one hypothesis each, only after REPRODUCED; CB5 stops stale hypotheses; root-cause confirmer
  `mission-reviewer`.
- **IF** feature in an existing product (e.g. a dashboard) **THEN** class M; heavy `Explore`/`mission-scout` sweeps
  before planning; implementers `mission-worker`; code review `mission-reviewer`; vision on seeded-data screenshots
  `mission-reviewer`; Fable beyond the orchestrator only if the feature crosses ≥3 subsystems.
- **IF** service migration/extraction (e.g. an AI gateway into a core service) **THEN** class L; plan and boundary on
  `mission-strategist`; ES4 applies to almost every change (contracts, data, infra, credentials) → makers
  `mission-builder`, reviews `mission-critic`; parity/dual-run diff tests are the grader; keep fan-out low (files
  overlap), prefer sequential slices (CB8).
- **IF** market research plus website with blog/docs **THEN** search angles `mission-worker` (4–8 lanes, every claim
  URL + quote + date), single-fact lookups `mission-scout`; synthesis/positioning `mission-builder` (`mission-strategist`
  at XL); fact-check `mission-verifier`, public/load-bearing claims `mission-critic`; copy `mission-worker-high` with
  `mission-reviewer` brand/claim review; site build `mission-worker`; vision `mission-reviewer`.
- **IF** offensive security, exploit development or pentest logic **THEN** CF1 pre-routing to Opus 4.8 agents, human
  sign-off before live-system actions, orchestrator receives summaries not payloads.
- **IF** biology/life-sciences content **THEN** CF6: log reroutes, ask the human.
- **IF** chore (lint sweep, dependency bump, doc refresh) **THEN** class S, no Fable anywhere: one `mission-worker` with
  deterministic gates and a `mission-checker` checklist grader (+ canary).
- **IF** OPS/triage with a classifier **THEN** `mission-checker` classifies, low-confidence or risky labels cascade to
  `mission-reviewer` (GD7), 5% double-classify audit.
- **IF** subscription plan or minimum-cost request **THEN** Lean profile; ledger records plan-usage % (CB6).
- **IF** unattended overnight/multi-day **THEN** hard cap via `--max-budget-usd` where available, CF3 at every phase
  boundary, ledger written before each wait, soft cap in autonomous mode follows CB4's narrowed-plan rule.
- **IF** Fable 5.1 unavailable or Claude Code < v2.1.257 **THEN** Degraded profile (PF2).
- **IF** no per-agent model selection **THEN** PF3 separate sessions per role.

## Model routing

Every role the skill uses. "Tier-up" = next agent when the row's trigger fires (ES ladder for makers). "Floor" = lowest
agent ES6 may move to. Orchestrator-inline work runs on the session model and never grades itself.

| # | Role | Default agent (model · effort) | Tier-up when | Floor | Guard on the cheaper choice |
|---|---|---|---|---|---|
| 1 | Orchestrator S | session O · high | 2 failed phases → `mission-strategist` for the plan | O · high | gates verified by non-authors; CB3 |
| 2 | Orchestrator M/L/XL | session F · medium (high: intake, spec/design gates, adjudication) | — | Lean: O · high | CB3 review; CF3 model re-assertion |
| 3 | Intake / charter | orchestrator inline; L/XL charter synthesis `mission-strategist` (F · high) | — | inline | `mission-checker` intake checklist; L/XL blind class second opinion `mission-reviewer` |
| 4 | Planner / decomposer | S/M inline; L/XL `mission-strategist` | plan fails lint twice | inline | `mission-checker` structural lint + `check-ownership.sh`; L/XL plan critique `mission-critic` |
| 5 | Spec writer | M inline; L/XL `mission-strategist` | — | inline | `validate-registry.py`; `mission-critic` spec review (caps M1, L/XL2) |
| 6 | Architect / designers | L/XL architecture `mission-strategist`; bounded designs, screen/backend/migration docs `mission-builder` (O · high) | — | `mission-builder` | `mission-critic` design lens; XL + `mission-strategist-review` |
| 7 | Research lead / synthesiser | M inline; L `mission-builder`; XL market/strategy `mission-strategist` | — | inline | claim table with URL per claim; fact-check sample |
| 8 | Search / reading workers | `mission-worker` (S · medium); single fact `mission-scout` (S · low) | ≥2 contradictory sources → `mission-worker-high` | `mission-scout` | URL + verbatim quote + date per claim; `mission-verifier` re-checks quotes |
| 9 | Fact-checker | `mission-verifier` (S · high) | public or load-bearing claims → `mission-critic` | `mission-verifier` | quote must appear at the URL; GD4 |
| 10 | Implementer | `mission-worker`; multi-file/unfamiliar `mission-worker-high` (S · high); ES4 `mission-builder` | ES2 → ES1 ladder | `mission-worker` | GD1 oracles; per-task `mission-verifier`; `mission-reviewer` review; GD4 |
| 11 | Test strategist (TEST-PLAN) | S/M inline; L/XL `mission-builder` | — | inline | `mission-critic` spec review covers TEST-PLAN; every criterion has an oracle |
| 12 | Test author | `mission-worker-high`; concurrency/security/money/parity `mission-builder` | ES2 | `mission-worker-high` | tests proven red on the pre-change tree by `mission-verifier`; frozen manifest |
| 13 | Debugger rung 1: repro, flake, bisect | `mission-worker-high` | no repro after 2 attempts | `mission-worker-high` | REPRODUCED gate with command + output line |
| 14 | Debugger rung 2: investigator | `mission-builder` | 2 falsified hypotheses / cross-system | `mission-builder` | hypothesis ledger; discriminating checks |
| 15 | Debugger rung 3: hypothesis-space reset | `mission-strategist` (max 2, ledger reason) | → human | — | reset doc re-issued to `mission-builder`; red→green proof |
| 16 | Root-cause confirmer | `mission-reviewer` (O · medium) | disagreement → `mission-critic` | `mission-reviewer` | two-way CONFIRMED; confirmer ≠ investigator |
| 17 | Code reviewer (routine) | `mission-reviewer` | ES4 area → `mission-critic` | `mission-reviewer` | findings cite file:line; GD4 sample of "no findings" |
| 18 | Adversarial / spec / design / security reviewer | `mission-critic` (O · high); XL consolidated lens `mission-strategist-review` (F · medium) | CONTESTED → orchestrator adjudication (F · high) | `mission-critic` | refutation before blocking; GD8; exploit reasoning never on Fable (CF1) |
| 19 | Refuter | `mission-verifier` (never the raising reviewer) | UNVERIFIED on a blocker → `mission-critic` | `mission-verifier` | only CONFIRMED blocks; GD3 canary on citation checks |
| 20 | Per-task verifier, test-diff audit S/M | `mission-verifier` | judgement criterion → `mission-reviewer`; L/XL test-diff audit `mission-critic` | `mission-verifier` | re-runs commands in a clean worktree; `test-diff-grep.sh` first; GD3/GD4 |
| 21 | Merged-result / gate verifier, tournament judge | `mission-critic` | XL release → + `mission-strategist-review` lens | `mission-critic` | clean-checkout runs; evidence per criterion |
| 22 | UI vision verifier | G1 probes run by `mission-checker`; G2 per-screen vision `mission-reviewer` | flagship-screen tie-break (XL) → `mission-strategist-review` | `mission-reviewer` | geometry/a11y probe first; screenshot path + pixel box per verdict; GD4 by `mission-critic` |
| 23 | Grader / checklist / gate runner | `mission-checker` (S · low) | judgement needed → `mission-reviewer`; loop-grader audit `mission-reviewer` | `mission-checker` | GD3 evidence-only scope + seeded canary; GD4 |
| 24 | Classifier / router | `mission-checker` | low confidence or risky label → `mission-reviewer` | `mission-checker` | GD7 cascade; OPS 5% double-classify |
| 25 | Ledger / STATUS bookkeeping input | `mission-checker` (orchestrator writes STATUS) | — | `mission-checker` | schema/lint of ledger; totals match headless JSON |
| 26 | Doc writer | `mission-worker`; changelog bump `mission-worker` with a short brief | never Fable (MR3) | `mission-worker` | link check, code samples run; GD4 |
| 27 | Integrator | `mission-integrator` (O · medium) | semantic conflict in ES4 area → `mission-builder` | `mission-integrator` | task checks + smoke suite on merged tree; revert on red |
| 28 | Release readiness | `mission-reviewer` | irreversible step → human | `mission-reviewer` | checklist with evidence |
| 29 | Lesson distiller | phase lessons inline; retro `mission-builder`; XL cross-mission `mission-strategist` | — | inline | each lesson cites failure evidence |
| 30 | Promotion verifier | `mission-verifier` (fresh context) | disagreement / SKILL.md-body target → `mission-critic` | `mission-verifier` | criteria a–h cited; 2 REJECTs close |
| 31 | Curator | `mission-worker` proposes ID-level edits; `mission-verifier` information-loss check | XL ≥3 contradictions → `mission-reviewer` | `mission-worker` | `memory-lint.sh`; every removed ID accounted |
| 32 | Explore / lookups | `Explore` (S · low); pointer maps, log extraction `mission-scout` | thorough cross-repo map → `mission-worker` | `Explore` | output is pointers; consumer verifies |

Why checklist graders are Sonnet low but judges are not: a same-model, lower-effort judge shares the maker's blind spots
and explores less; spend `mission-reviewer` tokens on judgement over Sonnet work, `mission-checker` tokens only on
evidence that a command already produced.

### Profiles

| Profile | When | Changes (guards never change) |
|---|---|---|
| **Standard** | default | the matrix above |
| **Lean** | user asks for minimum cost, or subscription limits | orchestrator O · high on every class; rows using `mission-strategist` move to `mission-builder` and rows using `mission-strategist-review` to `mission-critic`, unless the human approves Fable for a named task (D-entry) |
| **Degraded: no Fable** | Fable 5.1 unavailable or Claude Code < v2.1.257 | orchestrator `claude-opus-4-8` · xhigh (select at session start); `mission-strategist` rows → Agent-tool `model: claude-opus-4-8` override (effort stays high: xhigh cannot be set per call); `mission-strategist-review` rows → `mission-critic` |
| **Degraded: no Opus 4.8** | Opus 4.8 unavailable or Claude Code < v2.1.154 | O-tier write rows (`mission-builder`, `mission-integrator`) → `mission-worker-high`; O-tier read-only rows (`mission-reviewer`, `mission-critic`) → `mission-verifier` (both S · high); GD2/GD8 model difference is lost, so GD4 audits and design gates add `mission-strategist-review`, and every ES4-area change gets human review before merge |
| **Degraded: no Sonnet 4.6** | Sonnet 4.6 unavailable | stop and ask the human; never silently promote all workers to Opus |

Record the profile in the STATUS header and `BUDGET.md`, with a D-entry for Lean and Degraded.

### How to change models

1. Edit `references/conventions.md` §6 (IDs, prices, efforts) and §7 (roster model · effort) — the only canonical place.
2. Update `model:` / `effort:` in `skills/mission/agents/*.md`; reinstall with `scripts/init-mission.sh --force-agents`.
3. Update the `EXPECTED` roster table and `ALLOWED_MODELS` in `scripts/preflight.sh`; re-verify prices on the pricing
   page before quoting figures; run preflight.
4. Newer models exist (Opus 5, Sonnet 5; the `opus`/`sonnet` aliases resolve to them on the Anthropic API, and Sonnet 5
   lists cheaper than Sonnet 4.6). The user chose Opus 4.8 and Sonnet 4.6: do not switch without the user's
   instruction, and never switch by using an alias.

## Anti-patterns

| Anti-pattern | Why it hurts | Fix |
|---|---|---|
| Alias in an agent file or `--model` | `opus`/`sonnet` silently run Opus 5 / Sonnet 5 (Sonnet 4.5 on Bedrock/Google) | MR1; preflight fails |
| Omitted `model`, org allowlist exclusion, or `CLAUDE_CODE_SUBAGENT_MODEL` set | workers silently inherit the orchestrator's model; "cheap" fan-out costs ≈3× | PF1 script + probes; ledger logs resolved model |
| Built-in Explore on the top tier | dozens of explorations at Opus price | MR7 project `Explore` |
| `/model` switch mid-session to escalate | whole history re-read uncached (≈3.75 USD per switch on a 300k-token Fable context) | MR8; spawn instead |
| Timestamps or task text at the top of briefs; toggling MCP/plugins mid-phase | cache prefix invalidated for every worker | CX1, CX3 |
| Pasting whole files or logs into briefs | inflates each worker's cold cache write | CX2 |
| Fan-out by default | ~15× chat tokens; merge tax on coupled files | CB7, CB8, caps table |
| Fable for chores | ≈4× Sonnet for the same text | MR3 |
| `max` effort as a quality knob | effort is a behavioural signal, not a budget; overthinking | MR9; better context |
| Retry storms at one rung | cost without new information | ES2 |
| Same-model lower-effort judge on judgement criteria | rubber-stamps shared blind spots | GD2, GD3 |
| Model grader re-reading logs a command already scored | pays for a verdict that costs nothing | GD1 |
| Cheap graders with no audit or canary | quality drift goes unnoticed | GD3 canary, GD4, GD6 |
| Plan-high / execute-low with gaps | Sonnet low does not catch inherited ambiguity | makers default medium; plan critique first |
| Escalation that inherits the transcript | stronger model repeats the failing reasoning | ES3 fresh context |
| Silent sticky fallback | ledger says Fable, session runs Opus at the old effort | CF2, CF3 |
| Rephrasing around a refusal | policy violation; brittle | CF5 → `BLOCKED-SAFETY` |
| Ledger theatre by the Fable orchestrator | top-tier tokens on bookkeeping | CB2 via `mission-checker` / headless JSON |
| Budget as verdict | work lost at the soft cap, or cap blown silently | CB4 pause at soft, stop at hard |
| Trusting `/usage` dollars as the bill | local list-price estimate | CB6 reconcile in Console |
| New agent file per (role × model × effort) | cache and maintenance sprawl | roster only; Agent-tool `model` override for one-offs |

## Unverified harness details

| Detail | Status | Safe fallback |
|---|---|---|
| `effort:` frontmatter honoured by sub-agents | verified via issue #72596 quoting the docs; `/effort` and `--effort` rest on community sources | ship per-effort agent files (works either way); do not rely on session `/effort` switches |
| `CLAUDE_CODE_SUBAGENT_MODEL` precedence over frontmatter | sources conflict | keep it unset (preflight warns) |
| Org `availableModels` exclusion silently inherits the parent model | single secondary source | probe spawns per model ID; resolved model in ledger |
| Fan-out ceilings (200 sub-agents per session, 20 concurrent, depth 3) | single secondary source | caps table stays ≤15 concurrent; split sessions |
| Sub-agents build their own caches; prefix reuse across sibling sub-agents | own cache secondary; cross-agent reuse inferred | still write briefs cache-first; do not count on the saving |
| `/usage` by-model includes sub-agent tokens | not confirmed (the cache line excludes sub-agents) | headless JSON `total_cost_usd` per-model breakdown, or per-agent estimates |
| Detecting a classifier fallback from inside an interactive session | not verified | CF3 phase-boundary model check; human-visible step if needed |
| Changing effort keeps the cache | docs: only for Fable 5.1 on API key/subscription | change orchestrator effort only at boundaries; treat elsewhere as a cache miss |
| Fable 5.1 on the newer tokenizer (~30% more tokens than Sonnet 4.6) | inferred from "4.7 and later" | routing unchanged; ledger measures real tokens |
| `--max-budget-usd` available in the installed version | depends on version | check `claude --help`; else the orchestrator enforces caps from the ledger |
| Sonnet-low vs Opus-high grader agreement rate | no primary data | GD4 measures it per mission |
| Budget caps and thresholds (caps table, 10%, 60%, 2 disagreements) | opinionated starting defaults | calibrate after 3 mission ledgers; change via D-entry |

## Evidence

1. Pricing, cache multipliers, tokenizer note: https://platform.claude.com/docs/en/about-claude/pricing
2. Aliases, pinning, version floors, automatic fallback: https://code.claude.com/docs/en/model-config
3. Sub-agents, Explore inheritance, `CLAUDE_CODE_SUBAGENT_MODEL`: https://code.claude.com/docs/en/sub-agents
4. Cost estimates, `--max-budget-usd`, enterprise averages: https://code.claude.com/docs/en/costs
5. Cache layers and invalidators: https://code.claude.com/docs/en/prompt-caching
6. Effort levels per model: https://platform.claude.com/docs/en/build-with-claude/effort
7. Effort is frontmatter-only: https://github.com/anthropics/claude-code/issues/72596
8. Fable 5.1 safeguards, discovery vs exploit, reroutes: https://www.anthropic.com/claude-fable-and-mythos-5-1
9. Fable availability, rerouted billing, retention: https://www.anthropic.com/claude/fable
10. Multi-agent token multipliers and scaling rules: https://www.anthropic.com/engineering/multi-agent-research-system
11. Code vs model graders, trials: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
12. "A budget ceiling is a WAIT, not a verdict": arcwell/docs/handoff/2026-08-21-remediation-status.md:168
