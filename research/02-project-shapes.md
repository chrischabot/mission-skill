# 02 · Project shapes, scope sizing, and the conditional logic of `/drive`

Researcher component: the taxonomy of project shapes, the scope-sizing scheme, the intake decision procedure, the conditional ("if the task includes X then also do Y") matrix, worked classifications, and how to encode all of it inside the SKILL.md budget.

Date: 2026-09-14. Facts marked **verified** were checked today against code.claude.com; everything labelled opinion is mine and argued.

---

## 1. Executive opinion

The skill's most consequential design decision is to treat classification as three separate questions rather than one label. What kind of work it is (the **shape**) fixes the order of phases. What the work touches (the **traits**) attaches gates. How big it is (the **size**) sets depth and parallelism. Collapsing them into one "project type" is how frameworks end up too heavy for a bug fix and too light for a launch.

Seven shapes suffice: **build, feature, fix, move, publish, report, operate**. Refactor, upgrade, incident and performance work are variants of `move` and `fix`; data pipelines, CLIs and libraries are traits, because they change gates, not phases. Around eighteen traits carry the conditional rules, each with a named gate, artifact and exit check. Five sizes (XS to XL) are set by structural triggers only (components, unknowns, surfaces, repositories, duration); risk stays out of the size formula and enters through trait gates, so a two-line auth change stays XS in ceremony yet still gets its security review.

Intake runs silently in the orchestrator's context: parse the prompt, probe the tree for thirty seconds, assign shape, traits and size, write the classification and its assumptions into the state file, derive the plan, start. It asks the user only when a wrong guess would destroy work or waste over an hour that cannot be redirected, and then once, while continuing independent phases.

Re-classification is a standing rule checked at every phase gate and on named events; upgrades add gates to the remaining plan and never discard evidence.

Encoding: tables and the intake procedure in the first ~150 lines of SKILL.md so they survive compaction; per-shape plans and gate checklists in reference files re-read each phase; the plan itself in the state file, the only authority after compaction.

---

## 2. What the post says, and a critique

The source post has no notion of project shape or scope at all. Its fourteen steps are a single stack applied uniformly: STATE.md with five sections, verifier subagents, vision self-checks, dynamic workflows, routines. It is written as though every run were a days-long greenfield effort, which is precisely the failure the owner named: ceremony he "should" apply but does not because typing it out for a bug fix is absurd. A skill that encoded the post literally would impose the twelve-phase process on a config-value change.

Where the post is right, and worth keeping in this component:

- "Route by task complexity, not by default" is correct in spirit. It is unusable without objective triggers, which is what the sizing scheme here supplies. The post's tiers ("planning across days" vs "lint passes") are examples, not a decision procedure.
- The five-stage memory progression (fail, investigate, verify, distill, consult) is a good description of what the `fix` shape's hypothesis ledger and the lessons step must do. It says nothing about which shapes need it in full; a `report` run has no failures to progress through.
- "The agent that wrote the code is not the agent that grades it" is a structural rule this component adopts for every size from S upward, and it is why the size table specifies an independent reviewer at S rather than self-review.

Where it is exaggerated or wrong for this component:

- Its "classify-and-act" workflow pattern is about routing *subtasks* to models, not about classifying the *work*. Nothing in the post decides which phases apply. The post's implicit answer is "all of them".
- "No STATE.md means every session restarts from zero" is true for multi-day work and false for an XS fix, where the commit message is the state and a STATE.md is clutter. The owner's "no stray artifacts" rule cuts against reflexive state files.
- The Haiku-grader recommendation is rejected by the owner outright, and independently of trust the intake classification is the single highest-leverage judgment in the run: a wrong shape costs hours. It belongs to the orchestrator model, not a cheap grader. Sonnet at low effort is appropriate for mechanical sub-checks (claim-to-source matching, diff-touches-auth-file detection), which the matrix names explicitly.
- The post's model matrix names "Opus 4.8" and "Sonnet 4.6". **Verified today**: on the Anthropic API the `opus` alias resolves to Opus 5 and `sonnet` to Sonnet 5; Opus 4.8 is now the cybersecurity classifier fallback target, not the alias. The skill should use aliases and never pin version numbers in its text.

---

## 3. Verified facts (checked 2026-09-14)

Skills, from https://code.claude.com/docs/en/skills:

- "Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files." Supporting files are loaded on demand with the Read tool, not at invocation; the doc's pattern is to reference them from SKILL.md "so Claude knows what each file contains and when to load it."
- "Claude Code does not re-read the skill file on later turns, so write guidance that should apply throughout a task as standing instructions rather than one-time steps." This is why re-classification triggers must be phrased as standing rules.
- On compaction: the most recent invocation of each skill is re-attached "keeping the first 5,000 tokens of each"; re-attached skills "share a combined budget of 25,000 tokens", filled from the most recently invoked skill, so "older skills can be dropped entirely after compaction if you have invoked many in one session." `/drive` is by construction the *earliest* invoked skill in its run and will invoke several helpers (`severe-testing`, `frontend-design`, `deep-research`, `writing`), so it is the skill most at risk of being dropped. The mitigations in §4.9 follow from this.
- Frontmatter `effort` (`low|medium|high|xhigh|max`, "available levels depend on the model") and `model` override the session while the skill is active. `paths` limits auto-activation by glob. `context: fork` runs the skill body as a subagent's prompt "in a forked subagent context" that "doesn't see your conversation history".

Subagents, from https://code.claude.com/docs/en/sub-agents:

- Model resolution: per-invocation `model` parameter, then frontmatter (`inherit` selects the main model), then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main conversation's model. (The brief's ordering put the env var first; the live doc puts it third.)
- **Effort cannot be overridden per invocation**; only the definition's `effort` field sets it. Consequence: if the skill wants the same role at two efforts (a sonnet scout at high for M, an opus scout for L), it needs two agent definitions or must accept the session effort.
- `isolation: worktree` gives "an isolated copy of the repository branched by default from your default branch rather than the parent session's HEAD" and is "automatically cleaned up if the subagent makes no changes". A worktree with changes persists, so for the owner merging and deleting must be an explicit step of the same phase.
- "By default, a subagent can spawn subagents of its own, up to three layers below the main conversation." Omit `Agent` from a reviewer's tools to keep it read-only.
- `memory: user|project|local` gives a subagent a persistent directory whose `MEMORY.md` (first 200 lines or 25 KB) is injected into its system prompt.

Workflows, from https://code.claude.com/docs/en/workflows:

- `agent()` accepts a `schema` and then "returns JSON matching the shape instead of prose", retried up to five times; useful for structured scouting, not needed for intake.
- "No mid-run user input"; "Up to 16 concurrent agents"; default size guideline `medium` means "fewer than 15 agents". The `ultracode` keyword is an opt-in only in a prompt the human typed; it "doesn't start a workflow" from `-p`, scheduled prompts, or relayed payloads. Asking "in your own words" (for example "use a workflow") "also works". Whether a skill's instruction counts as that request is a brief claim I could not verify from the page.

Goal, from https://code.claude.com/docs/en/goal:

- The evaluator "doesn't run commands or read files independently, so write the condition as something Claude's own output can demonstrate." Up to 4,000 characters. "To bound how long a goal runs, include a turn or time clause in the condition, such as `or stop after 20 turns`." Background subagents defer evaluation; check-ins begin after 30 minutes. Works with `claude -p`.

Model configuration, from https://code.claude.com/docs/en/model-config:

- Effort levels: Fable 5.1 and Fable 5, Opus 5, Sonnet 5, Opus 4.8, Opus 4.7 all support `low, medium, high, xhigh, max`. Opus 4.6 and Sonnet 4.6 lack `xhigh`. Default effort is `high` on every model that supports it (Opus 4.7 defaults to `xhigh`). Unsupported levels fall back to the highest supported level at or below.
- On the Anthropic API `opus` → Opus 5 and `sonnet` → Sonnet 5. `fable` → Fable 5.1 unless `ANTHROPIC_DEFAULT_FABLE_MODEL` is set. "Neither Fable model is the account-type default on any plan or provider."
- Classifier fallback: for Fable 5.1, "biology-flagged requests re-run on Opus 5, and cybersecurity-flagged requests re-run on Opus 4.8." Then: "After a fallback, the session continues on the fallback model." That last sentence matters for this component: a security review run *inline* by the orchestrator can flip the whole session off Fable for the rest of the run. Security work should run in a subagent with an explicit `model: opus`.

Not verified: any doc page specific to "project classification"; none exists. Everything in §4 is design.

---

## 4. Detailed spec

### 4.1 The three axes

The orchestrator answers three questions at intake and records each separately:

| Axis | Question | Decides | Values |
|---|---|---|---|
| Shape | What kind of work is this? | The ordered list of phases and which are skipped | build, feature, fix, move, publish, report, operate (+ variant) |
| Traits | What does the work touch? | Which gates attach to which phases, and which reviews are mandatory | ~18 named traits, each `confirmed` or `suspected` |
| Size | How much is there, and how uncertain? | Depth of each phase, number of parallel agents, state-file weight, verification tier | XS, S, M, L, XL |

The axes are orthogonal by design. Size never adds phases from another shape (a large bug hunt does not acquire a specification phase); traits never change the phase order (an auth trait on a fix adds a security review to the verify phase, it does not turn the fix into a build); shape never sets the depth (a `build` can be S when it is a single-file script).

### 4.2 Shapes

The table is what goes into SKILL.md. The detail beneath it goes into `references/shapes/<shape>.md`.

| Shape | Prompt signals | Phases (in order) | Skips | Verification centre of gravity |
|---|---|---|---|---|
| **build** | "build/create/new", multiple surfaces named, no code for the deliverable in cwd, prose paragraphs rather than a ticket | research → spec → architecture → design system → test strategy → scaffold + walking skeleton → slices (parallel) → integrate → severe review → live proof → docs → lessons | archaeology (beyond owner conventions), characterization, reproduce | contract tests between surfaces; refuting test per claim; vision on screens; live deploy smoke; harness-fidelity audit |
| **feature** | "add/extend/new X in existing Y", cwd has code, names existing screens or modules | archaeology → mini-spec → design delta → slices → verify → severe review (scaled) → live proof if deployable → docs | research (unless unknown tech), full architecture, design-system creation | baseline suite recorded green *before* the change; refuting tests for new claims; neighbour regression; vision if ui |
| **fix** | "bug/broken/fails/wrong/flaky/sometimes", a stack trace, "find and fix" | narrow archaeology → reproduce → hypothesis ledger → localize → fix at cause → prove → blast radius → scaled review → lesson | spec, architecture, design, research (unless third-party behaviour) | reproducer observed failing then passing; no unrelated test edits; cause not symptom |
| **move** | "migrate/move X into Y/consolidate/upgrade to/refactor/simplify/replace", "from … to …", behaviour preserved | archaeology of source and destination → inventory (+ ownership map) → characterization tests → cutover plan with undo → strangler steps → compare → flip → remove source → live proof → docs | spec of new behaviour (forbidden; new behaviour is a separate `feature` sub-goal), design | characterization green on both sides; output comparison on real inputs; rollback rehearsal for data |
| **publish** | "website/landing/docs site/blog", "describe our project/team/goals", "market position" plus a site | source-lane research → content plan → design direction → information architecture → build → drafting → design QA → Lighthouse + a11y → link/spell check → deploy → live proof | contract tests, security review (unless forms/auth), backend architecture | every on-page claim traces to the ledger; screenshots vs design direction; Lighthouse thresholds; links resolve; mobile renders |
| **report** | "research/report/analysis/compare", deliverable is prose only | question decomposition → source-lane research → cross-check → synthesis → editorial review → deliver | everything code-related | every claim cited; contradictions surfaced; adversarial reader tries to refute the top claims; freshness dated |
| **operate** | "deploy/rotate/import/cut over/get X running again/clean up", a named live system, no code change is the point | read runbook + state → plan with undo per step → execute through the system's own tools now → verify live → record | spec, tests (unless a script is written, which then gets tests), design | observed effect, not command exit; every step has an undo recorded before it runs |

**Variants** (recorded alongside the shape; they change one or two steps, never the skeleton):

- `fix/incident`: a live system is failing now. Insert **mitigate** before **reproduce**, with the undo recorded first; remove the mitigation only after the real fix is live-proven. Everything else is `fix`.
- `fix/perf`: the symptom is a number. **Reproduce** becomes a baseline measurement on a named metric and path; **hypothesis ledger** is profile-driven; **prove** is a re-measurement against the baseline; the benchmark is kept as a regression guard.
- `move/migration`: cross-boundary (repo, service, platform); the full cutover plan applies, including dual-run and comparison.
- `move/refactor`: in place, single codebase; cutover collapses into a commit; the mechanical part may be delegated to the `simplify` skill inside a subagent; characterization is still mandatory.
- `move/upgrade`: toolchain or dependency; **characterization** is the existing build plus suite plus a simulator or runtime smoke; **research** reads the migration guide and changelog for hidden behaviour changes; strangler is per-module where the toolchain allows it.

**Shapes I considered and rejected as shapes:**

- *Data pipeline*, *CLI tool*, *library/SDK*: each is a `build` or `feature` with a trait (`data`, `cli`, `public-api`). They change which gates run (idempotency and replay for data; golden outputs for CLI; API review and semver for libraries), not the order of phases. Making them shapes would triple the shape table for no change in sequence.
- *Refactor/simplification* as its own shape: it is `move/refactor`. The one real difference from migration is the absence of a cutover, which the variant handles.
- *Ops/incident* as its own shape: split. Incident is `fix/incident` because the goal is still a root cause. Planned operations with no defect (deploy, rotate, import, cut over) are `operate`, which earns shape status because its skeleton has no implementation phase at all and its whole verification is live observation; it is also the shape where the owner's "never wait on a scheduler" rule bites hardest, so it deserves its own reference file with that rule at the top.

**Per-shape model, effort and parallelism** (opinion, informed by the verified effort table):

| Shape | Orchestrator | Hard-but-bounded (opus) | Volume (sonnet) | Graders (sonnet, low) | Typical parallelism |
|---|---|---|---|---|---|
| build | fable, xhigh: spec and architecture judgement, integration, root-cause calls | architecture review, the hardest slices, every verifier | scaffold, well-specified slices, docs, tests from a written strategy | claim-to-test coverage check; screenshot-vs-token matching | high: research fan-out (3–5), then backend and frontend slices in parallel against a fixed contract, verifiers in parallel; worktrees merged within the slice |
| feature | fable, high | the core of the feature, the diff reviewer | remaining slices, tests, docs delta | baseline-vs-after suite diff | moderate: front and back halves in parallel once the contract is fixed; verifier parallel to maker |
| fix | fable, high: judges cause vs symptom, second-time rule | the hunt itself (deep debugging is the canonical hard-but-bounded task) | regression test authoring once cause is known; running suites | none needed | low: hypotheses are sequential; read-only scouts may test independent hypotheses in parallel; never parallel writers on a fix |
| move | fable, xhigh for the cutover plan | inventory of tangled code, the tricky moves, comparison analysis | mechanical moves in bulk (workflow fan-out when >~20 files) | "did behaviour change?" diff classification | high for mechanical steps (per-module worktrees); strictly serial for cutover steps |
| publish | fable, high: content strategy, voice, what to claim | design direction, the key pages | page volume, link checks, a11y fixes | claim-to-source matching | high: research fan-out; page drafting in parallel after the content plan; design QA per page |
| report | fable, high: synthesis and what to believe | cross-check lane, contradiction adjudication | readers per source lane | claim extraction, citation format | high: this is the `/deep-research` workflow shape |
| operate | fable, high: live-system judgement | the risky steps | log reading, evidence collection | none | none: serial with checkpoints |

### 4.3 Traits

A trait is anything the work touches that attaches a gate. Each has *signals* (prompt words and probe findings), a *gate* (what must additionally happen, at which phase), an *artifact* (what the gate leaves behind), and an *exit check* (how the orchestrator knows the gate ran, with ground-truth precedence: code and tests beat proof artifacts beat status files beat prose). Traits are recorded as `confirmed` (seen in the prompt or the tree) or `suspected` (inferred); a suspected trait attaches its gate until archaeology refutes it, because the cost of an unneeded review is minutes and the cost of a missed one is the D1 incident.

| Trait | Signals (prompt / probe) | Gate added | At phase | Artifact | Exit check |
|---|---|---|---|---|---|
| `ui` | screen, page, view, dashboard, app; SwiftUI/UIKit, React/Vue/Svelte, HTML templates, TUI libs, HTML email templates | vision verification of rendered output; design review against tokens; accessibility tree check; responsive and dark mode | verify, and design delta/system | screenshots under `.drive/evidence/`, verifier's structured diff | a verifier *other than the maker* read the screenshot and wrote a pass/gap |
| `api` | endpoint, route, RPC, webhook, contract; `wrangler.toml`, server frameworks, OpenAPI files | contract tests (request/response shapes, error shapes); live-proof gate (the deployed thing answers) | test strategy, verify, live proof | contract test files; live smoke transcript | a request against the deployed URL appears in the transcript with its response |
| `auth` (covers secrets, payments, PII) | login, session, token, key, secret, billing, card, PII fields; auth libs, `.env*`, KMS, payment SDKs | security review by a read-only subagent with explicit `model: opus`; `severe-testing` skill preloaded in that subagent; secrets never in repo, logs or screenshots; least privilege | verify | security review report with findings ≥50 confidence; severe test files | review report exists and every finding has a disposition |
| `data` (schema, migrations, stores) | table, schema, migration, D1, R2, KV, Postgres, backfill; `migrations/` dir, ORM config | backup plus rollback plan before any destructive step; migration rehearsal on a copy; **harness-fidelity audit** ("where is the shim kinder than production?"); idempotency of writes | architecture/test strategy, before implement, verify | `ROLLBACK.md` per migration; fidelity audit note listing each shim and its known divergences | rollback rehearsed at least once in the transcript; fidelity note names the production limits checked (bind counts, size limits, timeouts) |
| `existing-code` | cwd is a repo with source; prompt names modules/screens | archaeology pass before changing anything: CLAUDE.md, README/docs, tests and how to run them, `git log -30`, recent PRs, conventions, the failing or touched path | first phase | archaeology brief in STATE.md | brief exists and names the test command and the conventions |
| `multi-repo` | two or more repos named or discovered; monorepo packages with separate owners | ownership map (who owns what, which repo is source of truth); change order across repos; cross-repo contract pinned | inventory/architecture | ownership map in STATE.md | every touched repo appears in the map with its role and the order of changes |
| `external-systems` | Cloudflare, Apple, Stripe, a third-party API, OAuth provider, App Store | sandbox-vs-live distinction recorded; credential handling plan (owner-set secrets are named, never fabricated); quotas and cost noted; egress verified from where the code actually runs | architecture, live proof | external-systems note | a live call from the deployed runtime, not the laptop, appears in evidence |
| `async-scheduled` | cron, queue, workflow, scheduled, webhook, retry, backoff; Workflows/Queues/DO alarms/launchd | drive-now rule: trigger through the system's own tools during the run, never "it will run at the next tick"; idempotency; replay/backfill path; trigger observability | implement, live proof | a triggered run's evidence | the transcript shows the trigger fired and the effect observed, this session |
| `concurrency` | race, parallel, actor, Durable Object, lock, Swift strict concurrency | severe concurrency tests (ordering, interleaving, invariants under load) | test strategy, verify | property/stress tests | tests exist that would fail for a plausible race |
| `native-platform` | iOS/macOS/Xcode/Swift, Android | simulator build-launch-screenshot-inspect loop; build matrix noted; device-only features flagged as untestable here; signing/entitlements | scaffold, verify, live proof | simulator screenshots + accessibility inspections | `build` and `launch` succeeded in-session and a screenshot was read |
| `prose-content` | blog, docs, copy, README, announcement, report prose | `writing` skill inside the drafting subagent; voice rules; every factual claim traced to a ledger entry | drafting, editorial | claim→source table | a sonnet-low grader confirms each claim has a source or is marked opinion |
| `public-api` (library/SDK) | package, SDK, library, "consumers", semver, publish to registry | API design review; semver decision; docs and examples that run as tests; deprecation path | architecture, verify | API review note; example tests | examples execute in CI/test run |
| `cli` | command, flag, `argv`, "tool you run" | golden-output tests; `--help` review; exit codes; argument edge cases (empty, unicode, huge) | test strategy, verify | golden files | goldens exist and a wrong output would fail them |
| `perf` | faster, slow, latency, memory, startup, "make it snappy" | baseline measurement before any change; profile-driven hypotheses; re-measure after; benchmark kept | reproduce, prove | benchmark script and before/after numbers in STATE.md | both numbers in the transcript from the same script |
| `research-needed` | unknown tech, "figure out", new platform, market/competitor questions; probe finds no prior art in the tree | research ledger with URLs and dates before design decisions depend on them; distinguish verified fact, source claim, assumption | research | `RESEARCH.md` ledger | every architecture decision cites a ledger row or is marked assumption |
| `deploy-infra` | deploy, release, environment, DNS, config, IaC | deploy plan with undo; config diff before apply; live smoke after | live proof | deploy log with undo | smoke result observed post-deploy |
| `ai-llm` | prompt, model, agent, embedding, "uses Claude/GPT" | eval set with expected behaviours; non-determinism handling; cost budget; prompt versioning; graders on sonnet at low effort, never the maker | test strategy, verify | eval results | eval ran and numbers recorded |
| `large-surface` | the same operation on >~20 files/modules (probe count) | fan-out via dynamic workflow (L/XL) or parallel subagents in worktrees, each with a verifier; merge inside the phase | implement | per-item results | no worktree remains after the phase |
| `generated-code` | `*.pb.go`, `*.generated.*`, `node_modules`, vendored trees | never hand-edit; change the generator or source and regenerate | implement | regeneration command in STATE.md | diff of generated files matches a fresh regeneration |

Threshold discipline, because trait inflation is the way ceremony creeps back in: `auth` attaches only when the *diff* touches identity, money or personal-data code or config, or the feature's own claims involve them; reading a user's display name on a dashboard is not `auth`. `data` attaches on schema or migration changes and on new write paths, not on a read-only query against an existing table (though the harness-fidelity question still applies if the test double is not the real store). `concurrency` attaches when shared mutable state or interleaved I/O exists, not because the language has threads.

### 4.4 Sizes

Size is computed from **structural** triggers only. The rule is the maximum: the largest size any single trigger demands is the size. Risk does not enter the formula; it enters through trait gates, which apply at every size. This keeps a two-line auth change XS in ceremony (no spec, no state file) while still forcing the security review, and it stops a low-risk but sprawling rename from being called "small" because nothing dangerous is touched.

| Trigger | XS | S | M | L | XL |
|---|---|---|---|---|---|
| Components touched | one function or file | one module or component | several modules in one service or app | two surfaces (e.g. backend + client) or two repos | three or more surfaces or repos, or a whole platform |
| Unknowns (questions the prompt plus a 30-second probe cannot answer) | none: cause or change is known | at most one, resolvable by reading code | two or three, resolvable by archaeology or a spike | a design unknown: how it should be built is open | the problem itself is open, or several design unknowns |
| UI surface | none | delta to one existing screen | new screens in an existing app | a new client | a new product across clients |
| Expected duration (honest) | under 15 minutes | under 2 hours | half a day to a day | one to three days | more |
| New files | none or one | a few | a directory | a package or app | a repo or several |

Ceremony by size (what each size adds to the shape's phases; a smaller size never adds phases, it thins them):

| Size | State | Planning artifacts | Verification tier | Agents | Live proof |
|---|---|---|---|---|---|
| **XS** | none beyond the commit message | none; the claim is stated in the commit body | one refuting test if a behavioural claim exists; the project's own checks; self-review of the diff | none: the orchestrator does it inline | only if the trait `deploy-infra` or `operate` is present |
| **S** | a short `.drive/STATE.md` block (classification, claim, evidence), or none for `report` | claim plus acceptance in STATE.md | refuting test; independent read-only reviewer (opus) on the diff; vision if `ui` | maker (may be inline) + reviewer | if deployable and cheap; otherwise Local Proof and say so |
| **M** | full STATE.md with status ladder per component | mini-spec (claims, out of scope, acceptance); test plan | refuting tests per claim; verifier subagent per slice; severe review (scaled to the diff) | 2–4 slice makers, verifiers, one reviewer | required when a deploy target exists |
| **L** | full STATE.md plus `RESEARCH.md` where unknowns exist; `LESSONS.md` | spec; architecture; design delta or system; test strategy with harness-fidelity plan | adversarial verification per component; severe review; live proof | parallel slices in worktrees merged within the slice; verifiers; research fan-out | required; the status ladder cannot pass Local Proof without it |
| **XL** | everything in L plus a "last session" resume block updated at every gate | research ledger with online sources; design system; cutover or rollout plan | everything in L plus phase gates with re-classification review; `/goal` bounded per phase | workflow fan-out for bulk; design tournament for taste decisions | required per surface |

Borderline rule: when two adjacent sizes are both defensible, choose the smaller and rely on re-classification, *unless* the shape is `move` or `operate`, where an under-called size tends to skip the cutover plan or the undo record, which are the steps that prevent damage; there, take the larger. Never round up merely because the prompt sounds important ("deep", "annoying", "critical" describe the owner's mood, not the structure).

### 4.5 The intake decision procedure

Intake is run by the orchestrator itself, inline, before any subagent is spawned, and it must finish in a handful of tool calls. It is silent: the user sees the classification in the state file and in the first status line, not as a question.

**Step 0. Resume check.** If `.drive/STATE.md` exists in the working directory and its classification block is present, this is a resume. Read it, read the shape file it names, and continue from the "last session" block. Re-classify only if the new prompt changes the deliverable. Never re-run intake on a resume; that is how plans drift.

**Step 1. Parse the prompt** into six slots and write them down before looking at the tree, so the tree does not bias the reading of the request:

- *Deliverable*: the noun the user will hold at the end (an app, a passing test, a moved service, a site, a report, a running system).
- *Verb*: build, add, fix, move, research, make-faster, upgrade, deploy.
- *Named systems and surfaces*: iOS, Cloudflare, "the dashboard", "our AI gateway", a repo name.
- *Constraints*: stack choices, "no new dependencies", "keep the public API", "only".
- *Quality words*: "deep", "annoying", "from scratch", "quick". These inform expectations, never size.
- *Exclusions*: "only", "just", "don't touch".

**Step 2. Probe the environment**, about thirty seconds, no subagent. Concretely:

```bash
git rev-parse --show-toplevel 2>/dev/null && git log --oneline -20 && git status --short | head
ls -a; ls docs 2>/dev/null; test -f CLAUDE.md && head -60 CLAUDE.md
# stack signals
ls package.json Package.swift *.xcodeproj wrangler.toml wrangler.jsonc Cargo.toml pyproject.toml go.mod 2>/dev/null
ls -d migrations db/migrate prisma drizzle 2>/dev/null
grep -rIl --exclude-dir=node_modules --exclude-dir=.git -E 'jwt|oauth|session|stripe|passport|apiKey|SECRET' . 2>/dev/null | head -20
# does the prompt's noun exist here?
grep -rIl --exclude-dir=node_modules --exclude-dir=.git -i '<noun from the prompt>' . 2>/dev/null | head
```

If the working directory is empty or unrelated but the prompt names a project, look for it under `~/Projects/<name>*` before assuming greenfield. Record what was found as the *probe* section of the classification block. For `existing-code` at M or above, the probe is followed by a proper archaeology pass run by the scout subagent (§6); the probe only has to be good enough to classify.

**Step 3. Assign the shape by precedence.** The order matters because prompts mix verbs; the first rule that fires wins:

1. A named defect, failure, wrong output or flaky behaviour → `fix`. If a live system is failing now → `fix/incident`. If the "defect" is a measured quality (slow, large, laggy) → `fix/perf`. Test for a false fix: if the expected behaviour never existed (check history), it is a `feature` phrased as a complaint ("fix the dashboard so it also shows X").
2. "From X to Y", migrate, consolidate, upgrade, refactor, simplify, replace, with behaviour expected to survive → `move`, with the variant from the verb.
3. The deliverable is prose and nothing is built → `report`.
4. The deliverable is a site, docs or content that must be designed and deployed → `publish`.
5. The deliverable is a change of state in a live system with no code change as the point → `operate`.
6. Existing code hosts the deliverable → `feature`.
7. Otherwise → `build`.

A prompt that carries two shapes ("fix the sync bug and then add the export dashboard") is split into ordered sub-goals, each classified on its own, sharing one state file, run in dependency order (fixes before features that sit on the fixed path; moves before features that depend on the new home). Each sub-goal gets its own commits. This is the only place intake produces more than one classification.

**Step 4. Assign traits** from prompt words and probe signals using the table in §4.3. `existing-code` is confirmed by the probe, not the prompt. Stack detection does most of the work: `Package.swift` or an `.xcodeproj` confirms `native-platform` and almost always `ui`; `wrangler.toml` confirms `api`, `external-systems` and `deploy-infra`, and `suspected: async-scheduled, data` (Workers projects usually have a cron or a D1 binding; the archaeology pass confirms or refutes). Mark each trait `confirmed` or `suspected`.

**Step 5. Assign the size** with the table in §4.4 and the maximum rule. Write down which trigger set the size; that is the fact re-classification later checks against.

**Step 6. Derive the plan.** Take the shape's phase list, delete the shape's skips, insert each trait's gate at its phase, and thin or deepen per size. Write the result into STATE.md as a checklist where every line names its artifact and its exit check. From this point the plan in STATE.md, not the skill text, is authoritative.

**Step 7. Write the classification block** (schema below), including assumptions with the evidence that would overturn each, and the questions you chose *not* to ask with the default you took instead.

**Step 8. Decide whether one question is unavoidable.** It is unavoidable only when both of these hold: two readings of the prompt lead to materially different deliverables *and* proceeding on the wrong one would destroy something or waste more than an hour of work that cannot be redirected. Ambiguity that costs less than that is resolved by assuming the more conservative reading and recording it. If a question is unavoidable, ask it once in conversation, state the default you will take, keep working on every phase that does not depend on the answer, and record the pending question in STATE.md so a resume sees it. Do not stop the run; do not ask a second question.

**Classification block schema** (lives in `.drive/STATE.md`; YAML inside a fenced block so both humans and tools can read it):

```yaml
classification:
  shape: feature                  # build | feature | fix | move | publish | report | operate
  variant: null                   # fix: incident | perf ; move: migration | refactor | upgrade
  size: M                         # XS S M L XL
  size_set_by: "several modules in one service; 2 unknowns"
  traits:
    confirmed: [existing-code, ui, api]
    suspected: [data]             # gate attached until refuted in archaeology
  probe:
    repo: /Users/chabotc/Projects/acme
    stacks: [typescript, react, cloudflare-workers]
    test_command: "npm test"
    recent_history: "20 commits, last 3 touch src/metrics/*"
    claude_md: present
  assumptions:
    - text: "The dashboard reads the existing metrics table; no new ingestion."
      overturned_by: "no such table, or the spec needs new sources"
    - text: "Visual style follows the existing component library."
      overturned_by: "archaeology finds no component library"
  not_asked:
    - question: "Which roles may see the dashboard?"
      default: "same as the existing admin pages"
  classified_at: 2026-09-14T09:12Z
  reclassifications: []
```

### 4.6 Re-classification

Discovery changes the picture in every non-trivial run, and a plan that cannot change with it produces either the wrong ceremony or, worse, work that is labelled complete against the wrong bar. Re-classification is therefore a standing instruction, checked in two ways.

**At every phase gate**, before starting the next phase, the orchestrator re-reads the classification block and answers three questions in the state file: does the shape still describe the work; has any trait become confirmed, refuted or newly discovered; has any structural trigger moved past the size's ceiling. Only a "no" to all three lets the next phase start unchanged.

**On events**, immediately, wherever they happen:

| Event | Change | Why |
|---|---|---|
| A fix requires changing an interface or touching more than one module | `fix` → `move/refactor` (or a `feature` sub-goal if behaviour changes); size up one; add characterization on the callers | The reproducer becomes the first characterization test; without the change, a "fix" silently becomes an unreviewed refactor |
| A feature turns out to need a schema or store change | add `data` (confirmed); insert rollback plan and fidelity audit before implementation continues | Additive-looking changes are where test doubles diverge from production |
| Archaeology finds a cron, queue, webhook, alarm or workflow on the touched path | add `async-scheduled`, `external-systems` as applicable | The drive-now rule and idempotency checks must be in the plan before the code is written |
| Any file matching the auth/secret/payment signals appears in the diff | add `auth` (confirmed) even at XS; schedule the opus security review | Cheapest gate to run, most expensive to skip |
| The same workaround is applied a second time | stop; mark the current diagnosis wrong in the ledger; return to the hypothesis phase | "Second time is the bug": the first diagnosis was of a symptom |
| Component count or repo count exceeds the size's ceiling | size up one; add the ceremony the new size requires to the *remaining* phases | Sizing is a forecast; the count is the fact |
| Research overturns a recorded assumption | update the assumption; re-derive the plan from the affected phase forward | The assumptions list exists to be checked, not decorated |
| The user's follow-up prompt changes the deliverable | re-run steps 1–7 as a new sub-goal | A changed deliverable is a new classification, not an edit |
| Reproduction shows a one-line, well-understood cause | `fix` size down to XS or S; keep the reproducer as the regression test | Downgrades are allowed and expected; ceremony that stopped paying should stop |

Every change appends to `reclassifications` and never edits history:

```yaml
  reclassifications:
    - at: 2026-09-14T11:40Z
      gate: reproduce
      from: "fix / S"
      to: "move/refactor / M"
      because: "the retry loop's design double-fires under backoff; a cause-level fix changes three callers"
      added: [characterization tests on callers, blast-radius review]
      kept: [reproducer (now the first characterization test)]
```

Two rules protect against the failure modes of re-classification itself. Evidence already gathered is never discarded when the shape changes; a reproducer stays a test, a research ledger stays a ledger. And a re-classification never restarts completed phases; it re-derives the plan from the current phase forward.

### 4.7 The conditional matrix

Each rule is "if the task includes X, then also do Y", with the argument. Rules are grouped by what triggers them. The gate details (procedure, artifact, exit check) are in §4.3; this section is the *why*, so the coordinator can decide which arguments to keep in SKILL.md and which to move to `references/gates.md`.

**Triggered by traits**

1. **Has a UI (anything a human looks at, including TUIs, HTML emails and generated reports) → vision verification by a non-maker, plus a design review against the project's tokens, plus an accessibility-tree check.** Text assertions cannot see a clipped label, a wrong colour token or a layout that breaks at 375 px. The owner's morning-brief incident (text-only email shipped because no one looked at the rendered output) is exactly a `ui` trait that was never attached because "email" did not sound like UI. Hence the broad definition.
2. **Has a backend or API → contract tests and a live-proof gate.** A backend's claims are about shapes over the wire and behaviour under real bindings. Unit tests against handlers do not exercise the runtime (bindings, limits, cold starts). The status ladder cannot pass Local Proof without a request against the deployed endpoint recorded in the transcript.
3. **Touches auth, secrets, payments or PII → a security review by a read-only subagent with explicit `model: opus` and the `severe-testing` skill preloaded, plus severe tests on the boundary.** Two arguments. Structural: the maker cannot review its own boundary. Verified operational: Fable's cybersecurity classifier can fire on exactly this content and, once it does, "the session continues on the fallback model"; running the review in a subagent keeps the orchestrator on Fable. Threshold: the diff touches identity, money or personal-data code or config, or the feature's own claims involve them.
4. **Touches data, schemas or migrations → backup and rollback plan before any destructive step, a rehearsal on a copy, and a harness-fidelity audit that names every test double and where it is kinder than production.** The D1 hundred-bind-variable incident is the archetype: 24 green runs against a sql.js shim that allowed unlimited parameters. The audit is a written list of production limits checked (bind counts, row and blob sizes, timeouts, transaction semantics), not a sentiment.
5. **Existing codebase → archaeology before changing anything: CLAUDE.md, README and docs, the test suite and how to run it, `git log -30`, recent PRs, the conventions in the touched area, and the failing or touched path itself.** Changing code you have not read produces plausible diffs that fight the codebase's conventions and re-implement what exists. For a `fix`, archaeology is narrow (the failing path and its recent history); for `feature` and `move`, it is broad. Record the baseline: run the suite before touching anything and write the result down, so "tests pass" after the change means something.
6. **Multi-repo → an ownership map and an explicit change order.** Two repos means two sources of truth and a contract between them. Without a map, the run changes the consumer before the producer, or edits a vendored copy. The map lists each repo, its role, who owns it, and the order of changes; the cross-repo contract is pinned (a version, a schema file, a hash) before either side moves.
7. **External systems (Cloudflare, Apple, Stripe, OAuth providers, third-party APIs) → record sandbox vs live per system, name the credentials the owner must set (never fabricate or guess them), note quotas and cost, and verify egress from where the code actually runs.** The owner's egress blackout (30 sources unreachable from the deployed runtime while everything worked locally) is why "verified from the laptop" does not count for this trait.
8. **Scheduled or asynchronous systems (cron, queues, workflows, alarms, webhooks) → drive them through their own tools during the run, require idempotency, provide a replay or backfill path, and make the trigger observable.** "It will run at the next tick" is not done; the owner's rule is explicit, and the reason is that a schedule is a hypothesis about the future, while a triggered run is evidence. Never report scheduled work as complete.
9. **Concurrency or distributed state → severe concurrency tests on ordering, interleaving and invariants under load.** Ordinary tests exercise one interleaving. If the failure mode is "sometimes", the test that matters is the one that runs the operations many times in varied orders.
10. **Native platform (iOS, macOS) → the simulator loop (build, launch, screenshot, inspect the accessibility tree, tap) is the verification harness; flag device-only features (camera, push, HealthKit, StoreKit real purchases) as *not verifiable here* rather than claiming them verified.** Honesty about the harness is part of the ladder: a feature that can only be proven on a device stays at Local Proof with the reason written down.
11. **Prose content → the `writing` skill inside the drafting subagent, the owner's voice rules, and a claim-to-source table checked by a sonnet grader at low effort.** Marketing pages and docs are where fabricated facts land quietly. Every factual sentence either cites a research-ledger row or is labelled opinion.
12. **Public API or library → API design review, a semver decision, and docs whose examples run as tests.** Consumers you cannot see will depend on the shape you ship; an example that does not compile is a broken promise.
13. **CLI → golden-output tests, a `--help` review, exit-code assertions, and argument edge cases.** A CLI's UI is its output; goldens are the vision check.
14. **Performance work → measure before, profile, change, measure after with the same script, and keep the benchmark.** Without a baseline every optimisation "feels faster". The metric and the path are named in the classification's assumptions when the prompt does not name them.
15. **Unknown technology or open questions → a research ledger with URLs and dates before any design decision depends on the answer; each row marked verified fact, source claim or assumption.** Architecture built on remembered documentation is where stale knowledge (the brief warns about it explicitly) becomes a wrong binding limit or a removed API.
16. **Deploy or infrastructure → a deploy plan with an undo per step, a config diff before apply, and a live smoke after.** Deploys are the operations most often reported as done on command exit rather than observed effect.
17. **LLM or agent features → an eval set with expected behaviours, explicit handling of non-determinism, a cost budget, prompt versioning, and graders on sonnet at low effort that are never the maker.** Prompts regress silently; only an eval notices.
18. **Large surface (the same operation on more than ~20 files) → fan out (dynamic workflow at L/XL, parallel worktree subagents otherwise), one verifier per item, and merge plus worktree deletion inside the same phase.** Serial editing of 200 files exhausts context and patience; unmerged worktrees violate the owner's one-checkout rule.
19. **Generated or vendored code → never hand-edit; fix the generator or source and regenerate; record the command.** Hand edits are erased by the next generation and the bug returns.

**Triggered by shape**

20. **Greenfield → research, spec, architecture (backend and frontend separately, with the contract between them written first), a design system when `ui` is present, and a test strategy before code; then a walking skeleton (one end-to-end path deployed) before breadth.** The skeleton is the earliest live proof and the cheapest place to discover that the shim is kinder than production.
21. **Bug → reproduce first, keep a hypothesis ledger (hypothesis, prediction, test, result), fix at the cause, prove with the reproducer, check the blast radius, and apply the second-time rule.** A fix without a reproducer is a guess with a commit message; a ledger is what turns a hunt into evidence and what the lessons step distils from.
22. **Migration or consolidation → characterization tests at the boundary, an inventory of what moves and what depends on it, a strangler plan (shadow, dual-run, compare, flip, remove) with an undo per step, and a hard rule that no new behaviour enters the move.** New behaviour hidden in a migration is untestable because nothing pins what "the same" meant.
23. **Research plus website → source-lane research with a ledger, a content plan before design, design direction before build, then design QA with vision, Lighthouse and accessibility, and link and spell checks before deploy.** The site is a claims machine; the ledger is what makes it honest and the design QA is what makes it not look generated.
24. **Pure research → decomposition, fan-out by source lane, a cross-check lane that hunts contradictions, an adversarial reader who tries to refute the top claims, and dated freshness.** Without the adversarial reader, synthesis converges on the first confident source.
25. **Operate → read the runbook and state first, write the undo before each step, execute through the system's own tools now, observe the effect, record what changed.** No code means no tests; observation is the only proof, and the undo is the only safety.

**Triggered by size**

26. **XS → no state file, no subagents, no spec; a refuting test if a claim exists, the project's checks, and a commit whose body states the claim and the evidence.** The commit is the record. Anything more is the ceremony the owner is trying to stop paying for.
27. **S and above → an independent reviewer who is not the maker.** The verified engineering finding ("a verifier sub-agent tends to outperform self-critique") is the reason; the cost is one read-only subagent call.
28. **M and above → STATE.md with the status ladder per component, a mini-spec with named claims, and severe review scaled to the diff.** This is the size at which the orchestrator's context stops being a reliable memory of the plan.
29. **L and above → adversarial verification per component, live proof as a ladder requirement, research where unknowns exist, lessons distilled at the end.** Multi-surface work is where "each half works" and "the product works" diverge.
30. **XL → phase gates with re-classification review, a resume block updated at every gate, `/goal` bounded per phase ("… or stop after N turns"), and workflow fan-out for bulk.** Multi-day work is where compaction, drift and forgotten plans do their damage.

### 4.8 Worked classifications

Each entry gives the classification block's essentials and the derived plan in prose, with the assumptions the skill would record instead of asking, and the re-classification watch.

**1. Fashion and outfit-creating iOS app, Cloudflare backend, native Swift front end (a few paragraphs of input).**
Shape `build`, size **XL** (three surfaces: iOS client, Workers backend, storage; the problem itself is open; multi-day). Traits confirmed: `ui`, `native-platform`, `api`, `external-systems` (Cloudflare, Apple), `data` (D1/R2 for wardrobe items and images), `auth` (accounts), `deploy-infra`, `research-needed` (domain: outfit composition, image handling; platform: current Workers limits, Swift concurrency). Suspected: `ai-llm` (outfit creation almost certainly calls a model; confirmed at spec), `async-scheduled` (image processing pipelines), `prose-content` (App Store copy, minor).
Plan: research fan-out (3–5 sonnet readers with a fable synthesis: comparable apps, Cloudflare Images/R2/D1 limits, SwiftUI patterns, the owner's Garderobe work as prior art since it is in his own systems) → spec with named behavioural claims and out-of-scope → architecture in two documents plus a contract (OpenAPI or typed schema) written before either side → design system via `frontend-design` and `design` canvas → test strategy naming per-claim refuting tests and the fidelity audit (D1 bind limits, R2 object sizes, Workers CPU time) → scaffold both repos or a monorepo → walking skeleton: one photo uploaded from the simulator to a deployed Worker and back → slices in parallel (opus for the outfit engine and auth; sonnet for CRUD, screens from the design system, tests from the strategy) each with a verifier → integrate → security review (opus subagent) → live proof on both surfaces (simulator screenshots read by a verifier; deployed endpoints called from the Worker runtime) → docs → lessons.
Assumptions recorded: single-user accounts first; images stored in R2 with D1 metadata; no payments in v1 (overturned by a paragraph mentioning subscriptions). Not asked: "which iOS minimum version?" (default: current minus one). Re-classification watch: payments appear → `auth` widens and a Stripe `external-systems` row is added; the outfit engine needs a model → `ai-llm` confirmed and an eval set inserted before slices.
Parallelism: high; models as in the `build` row of §4.2.

**2. "Find this deep annoying bug and fix it" in an existing codebase.**
Shape `fix`, size **M** at intake (the cause is unknown, so unknowns are two or three; one service; a day at most). "Deep" and "annoying" set nothing. Traits: `existing-code` confirmed; others from the failing path once known (a flaky async job would add `async-scheduled` and `concurrency`).
Plan: narrow archaeology by the scout (the failing path, its tests, `git log` on those files, recent related PRs) → reproduce (a failing test or script; if intermittent, record the rate and the loop that shows it) → hypothesis ledger, opus hunting, each hypothesis with a prediction and the experiment that would refute it; read-only scouts may run independent hypotheses in parallel → localize → fix at the cause → prove (the reproducer passes; the transcript shows it failing before) → blast radius (callers, similar patterns elsewhere) → scaled review (opus reviewer on the diff) → lesson if the cause generalises.
Assumptions: none about the cause; the ledger replaces them. Not asked: "how do you reproduce it?" (the run finds out; if reproduction fails after a bounded effort, that fact is the finding and the ledger says what was tried). Re-classification watch: the cause is a design flaw → `move/refactor` at M or L with characterization on callers; the cause is a one-liner → size down to S, keep the reproducer; a workaround is tried twice → stop and re-open the ledger.
Parallelism: low. Models: opus hunts; fable judges cause vs symptom; sonnet writes the regression test and runs the suite.

**3. "Add this new dashboard to the existing product."**
Shape `feature`, size **M** (several modules: a route, a data query, screens; two unknowns: charting approach and who may see it; a day). Traits confirmed: `existing-code`, `ui`, `api`. Suspected: `data` (a read against existing tables: refuted as a gate if no schema change and the test store is the real engine; kept if the test double is not), `auth` (if the dashboard is role-gated the diff touches authorization code; confirmed or refuted by archaeology).
Plan: archaeology (component library, existing admin pages, how similar pages fetch data, test command, baseline suite green) → mini-spec (claims: which numbers, from where, refreshed how; acceptance; out of scope) → design delta reusing the component library via `frontend-design` only for what is new → slices: query and endpoint (opus if the query is hard, else sonnet), screen (sonnet from the design delta), tests (sonnet from the claims) with a verifier per slice → vision verification of the rendered dashboard at desktop and 375 px, `dataviz` skill for the charts → severe review scaled to the diff → live proof if a staging deploy exists → docs delta.
Assumptions recorded: reads existing metrics, no ingestion; visibility same as existing admin pages. Re-classification watch: a new aggregation table is needed → `data` confirmed, rollback plan and fidelity audit inserted; a new role is needed → `auth` confirmed, security review scheduled.
Parallelism: moderate (endpoint and screen in parallel once the response shape is fixed).

**4. "Move our AI gateway from an external project into a core service of our platform."**
Shape `move/migration`, size **L** (two repos, two surfaces; design unknown: where in the platform it lives and how consumers switch; one to three days). Traits confirmed: `existing-code`, `multi-repo`, `api`, `auth` (provider keys and caller credentials), `external-systems` (model providers), `deploy-infra`. Suspected: `async-scheduled` (retries, usage aggregation), `data` (usage logs, key storage), `concurrency` (rate limiting).
Plan: archaeology of both repos → inventory (endpoints, callers, configuration, secrets, provider adapters, what depends on the gateway and what it depends on) → ownership map and change order (platform first as the new home, callers second, external project last to retire) → characterization tests at the gateway boundary (recorded request/response pairs against the *current* gateway; golden where deterministic) → cutover plan: the platform service shadows the external one, dual-run with comparison on real traffic or replayed logs, flip callers by configuration with an undo, retire the external project → strangler steps implemented in worktrees per adapter (sonnet for mechanical adapter moves, opus for rate limiting and key handling), verifier per step → comparison report → flip → live proof from the platform runtime → remove → docs.
Hard rule recorded: no new behaviour enters the move; the owner's wish list for the gateway becomes a `feature` sub-goal after cutover. Assumptions: consumers switch by configuration not code; provider keys move via the owner setting secrets (named, not fabricated). Not asked: "which service is the home?" (default: the platform's existing outbound-integration service if one exists, else a new module beside it; recorded). Re-classification watch: a third repo appears → XL; usage data needs a schema → `data` confirmed with rollback plan.
Parallelism: high for adapters, serial for cutover.

**5. "Research our market position, create a website describing our project, goals, team, with blog and documentation sections."**
Shape `publish`, size **L** (two surfaces: research deliverable and a multi-section site; a design unknown; external deploy; one to three days). Traits confirmed: `research-needed`, `prose-content`, `ui`, `deploy-infra`. Suspected: `external-systems` (hosting, analytics), `api` only if forms exist (refuted otherwise). No `auth` unless a newsletter form stores addresses (then `auth`/PII applies).
Plan: source-lane research (market, competitors, the project's own facts from its code and docs, the team's public bios) into a ledger with URLs → content plan (audience, pages, message hierarchy, voice rules from the owner's writing skill) → design direction via `frontend-design` with tokens and type → information architecture (home, project, goals, team, blog index and posts, docs section with navigation) → build with a static-site approach unless the probe finds an existing framework → drafting in parallel per page under the `writing` skill, each claim traced to the ledger → design QA: screenshots at three widths and dark mode read by a verifier; `web-design-guidelines` review → Lighthouse and accessibility with thresholds recorded → link and spell check → deploy with undo → live proof at the URL.
Assumptions: static hosting; no CMS; blog as markdown. Re-classification watch: a contact or signup form is requested → `api` and PII `auth` gates attach.
Parallelism: high for research and drafting; QA per page.

**6. Edge case: "make the app faster."**
Shape `fix/perf`, size **M** at intake (the metric and the path are unknown; one app). Traits: `existing-code`, `perf`, plus the app's own traits (`ui`, `native-platform` for an iOS app).
Plan: archaeology (what "the app" is; any existing benchmarks or perf complaints in issues or history) → define the metric and path *without asking*: measure the obvious user-facing paths (launch to first screen, the main list, the hottest endpoint) with a repeatable script, pick the worst by ratio to a reasonable budget, record the choice as an assumption → baseline recorded → profile → hypothesis ledger (each with a predicted gain) → change the top hypothesis → re-measure with the same script → keep the benchmark as a test with a budget → review.
Assumption recorded: "faster" means the measured worst path; overturned by the owner naming a different one. Re-classification watch: the profile shows an architectural cause (synchronous I/O on the main thread across the codebase, an N+1 pattern in the data layer) → `move/refactor` at L with characterization; a single hot spot → size down to S.

**7. Edge case: "upgrade to Swift 6."**
Shape `move/upgrade`, size **M to L** (one repo, but strict concurrency can touch every file, so the probe's file count decides: over ~20 affected modules pushes L and confirms `large-surface`). Traits confirmed: `existing-code`, `native-platform`, `ui` (regression only), `concurrency` (Swift 6's strict concurrency is exactly a concurrency change and can alter runtime behaviour, not only compile results), `research-needed` (the migration guide and the toolchain's known behaviour changes).
Plan: research (migration guide, changelog entries flagged as behaviour changes) → characterization: the existing suite green and a simulator smoke on the main flows *before* touching anything → inventory of modules and their concurrency warnings under the new mode → strangler per module: flip `swiftLanguageMode` module by module, fix diagnostics, rerun characterization, commit; fan out per module in worktrees when `large-surface` holds → compare: same smoke, same screenshots read by a verifier → severe concurrency tests where the migration introduced actors or `Sendable` changes → docs.
Hard rule: no refactors beyond what the compiler demands; opportunistic cleanups become a `move/refactor` sub-goal afterwards.

**8. Edge case: "write a market research report only."**
Shape `report`, size **S** for a narrow question or **M** for a market map (one deliverable; unknowns are the research itself; hours). Traits: `research-needed`, `prose-content`. No code traits; no state file at S beyond the ledger.
Plan: decompose the question → source lanes (`deep-research` workflow or tavily fan-out) with a ledger → cross-check lane hunting contradictions → adversarial reader (opus) tries to refute the top five claims → synthesis (fable) → editorial pass under the `writing` skill → deliver as a file (and an artifact if it has an audience). Verification is entirely source-based: cited, dated, contradictions surfaced, unverified claims listed rather than dropped.

### 4.9 Encoding inside the budget

The constraints are verified: SKILL.md should stay under 500 lines; the body is never re-read after invocation; after compaction only the first 5,000 tokens come back, and `/drive` is the skill most likely to be dropped entirely because it is invoked first and invokes others. That leads to four rules.

**Put the decision tables first.** The shape table (7 rows), the size table (5 rows), the trait-to-gate list (one line each, ~19 lines) and the intake procedure (~25 lines) fit in roughly 90 to 110 lines, which is comfortably inside the first 5,000 tokens. Everything the orchestrator needs to *classify* survives compaction; everything it needs to *execute* is read from disk anyway.

**Move the arguments and checklists to reference files, loaded by shape.** Only the matched shape's file is read at intake, and only the matched traits' sections of the gates file. Proposed layout:

```
skill/
  SKILL.md                         # intake + tables in the first ~110 lines; standing rules; pointers
  references/
    intake.md                      # full §4.5 procedure, classification schema, re-classification table
    sizing.md                      # §4.4 with borderline examples
    gates.md                       # one section per trait: procedure, artifact, exit check, argument
    shapes/
      build.md  feature.md  fix.md  move.md  publish.md  report.md  operate.md
                                   # phase plan, per-size thinning/deepening, exit criteria per phase, variants
  templates/
    STATE.md                       # with the classification block and the plan checklist
    RESEARCH.md  LESSONS.md  ROLLBACK.md
```

Each shape file is 60 to 120 lines and is re-read at every phase start; that costs one to two thousand tokens per phase and buys immunity to compaction. The gates file is read by section (the orchestrator greps for the trait heading and reads that range) so a run with three traits does not load nineteen.

**Make the state file, not the skill, the authority for the plan.** Step 6 of intake writes the derived plan into STATE.md as a checklist with artifact paths and exit checks. After compaction the orchestrator reads STATE.md and the shape file; it never needs the skill body again. This also honours the doc's instruction to write standing rules rather than one-time steps: the re-classification triggers are phrased as standing instructions in SKILL.md and repeated at the top of each shape file.

**Load helper skills inside subagents, not in the orchestrator's context.** `severe-testing`, `frontend-design`, `writing`, `deep-research` and the rest consume the shared 25,000-token re-attachment budget and push `/drive` out of it. Preload them with the `skills` field on the subagent that needs them (the security reviewer preloads `severe-testing`, the designer preloads `frontend-design`, the drafter preloads `writing`). The orchestrator's context then holds one skill: `/drive`.

On format: a table for the shapes and sizes, a decision list for the intake precedence, one-liners for the traits. A YAML block for the classification schema, because the orchestrator writes YAML into STATE.md and a schema shown in the same syntax it must produce removes a translation step. No prose arguments in SKILL.md at all; they live in `references/gates.md` and this report.

Sketch of the SKILL.md block for this component (lines are indicative; the coordinator will merge with the other components):

```markdown
## Intake (run silently, before any subagent)
1. Read .drive/STATE.md if present; if it has a classification, resume; do not re-classify.
2. Parse the prompt: deliverable, verb, named systems, constraints, quality words, exclusions.
3. Probe the tree (≤30s): repo, stacks, CLAUDE.md, tests, git log -20, does the prompt's noun exist here.
4. Shape by precedence: defect→fix (live→incident; measured→perf) · from-X-to-Y→move · prose only→report ·
   site/docs→publish · live-system change→operate · existing code hosts it→feature · else→build.
   Two shapes in one prompt → ordered sub-goals, one state file, separate commits.
5. Traits from prompt and probe (table below); mark confirmed or suspected; suspected still gates.
6. Size = the largest any structural trigger demands (table below). Risk never sets size; traits do.
7. Read references/shapes/<shape>.md and the matched sections of references/gates.md; derive the plan;
   write it and the classification block into .drive/STATE.md (templates/STATE.md). The file is now the plan.
8. Ask the user only if two readings give different deliverables AND the wrong one destroys work or costs
   >1h unredirectable. One question, once, with your default stated; keep working on independent phases.

## Re-classify (standing rule)
At every phase gate re-read the classification. Change it immediately when: a fix needs an interface change
(→ move/refactor); a schema appears (+data); a cron/queue/webhook appears (+async); an auth/secret/payment
file enters the diff (+auth, even at XS); a workaround is applied a second time (stop; diagnosis was wrong);
component or repo count passes the size ceiling (size up); research overturns an assumption. Append to
`reclassifications`; keep all evidence; re-derive only the remaining phases. Downgrades are expected.
```

---

## 5. Conditionals by project shape

This is the compact per-shape view of §4, in the form the coordinator can drop into `references/shapes/<shape>.md` headers. "Always" means regardless of size; "M+" means from size M upward.

**build.** Always: research ledger for every unknown; spec with named claims; architecture per surface plus the contract between surfaces written before either side; test strategy including the fidelity audit for every test double; walking skeleton deployed before breadth. `ui` → design system before screens, vision verification per screen. `native-platform` → simulator loop as the harness. `data` → rollback plan and fidelity audit even in v1. `auth` → opus security review before live proof. Skips: archaeology of code that does not exist (but read the owner's conventions and sibling repos), characterization, reproduce. Size: a `build` can be S (a one-file script); it is XL when three surfaces are involved.

**feature.** Always: archaeology with a recorded green baseline; mini-spec with claims; refuting tests; an independent reviewer at S+. `ui` → design delta against the existing library, vision at two widths. `api` → contract tests and live proof when a deploy target exists. Skips: research unless a technology is new to the codebase; architecture beyond the delta; design-system creation. The trap to encode: a "fix" whose expected behaviour never existed is a `feature`.

**fix.** Always: reproduce first, hypothesis ledger, fix at the cause, prove with the reproducer, blast radius, second-time rule. `incident` variant: mitigate first with the undo recorded, remove the mitigation after live proof of the real fix. `perf` variant: baseline and re-measure with one script, keep the benchmark. Skips: spec, architecture, design, research (unless the bug is in third-party behaviour, then a ledger row). Size: starts M when the cause is unknown; downgrades to S or XS when reproduction shows a known one-liner. Never parallel writers.

**move.** Always: inventory; characterization at the boundary before any move; cutover plan with an undo per step; comparison of outputs on real inputs; no new behaviour (spawn a `feature` sub-goal instead). `migration` variant: strangler with dual-run. `refactor` variant: cutover is a commit; `simplify` skill inside a subagent for the mechanical part. `upgrade` variant: characterization is build plus suite plus smoke; research the migration guide; per-module flips where possible. `multi-repo` → ownership map and change order. `large-surface` → fan-out with a verifier per item, worktrees merged and deleted inside the phase. Border rule: when in doubt about size, round *up* for `move`.

**publish.** Always: source-lane research with a ledger; content plan before design; design direction before build; every on-page claim traced; design QA with vision at three widths plus dark mode; Lighthouse and accessibility with thresholds; link and spell check; live proof at the URL. `api`/`auth` attach only when forms collect data. Skips: contract tests otherwise; backend architecture; severe security review unless forms.

**report.** Always: decomposition; fan-out by source lane; a cross-check lane; an adversarial reader on the top claims; dated freshness; unverified claims listed, not dropped. Skips: every code gate; no state file at S (the ledger is the state). Deliverable is a file; an artifact when it has an audience.

**operate.** Always: read runbook and state; undo written before each step; execute through the system's own tools now; observe the effect; record. Never report a scheduled run as done. Skips: spec, tests unless a script is written, design. Size rounds up.

---

## 6. Model and effort assignment for this component's roles

This component owns three roles: the intake classifier, the archaeology scout, and the classification refuter. It also names the sonnet-low graders that some gates use, since the owner wants those instead of Haiku.

**Intake classifier: the orchestrator itself, inline, on `fable`.** Not a subagent, for three reasons. The classification is the highest-leverage judgment of the run and a wrong shape costs hours, so it should be made by the model that will live with the consequences. It needs the full prompt and the probe output, which are already in the orchestrator's context; delegating would copy them out and the verdict back for no gain. And it must be silent and fast: eight steps and half a dozen tool calls. Effort: whatever the skill's frontmatter sets for the orchestrator; I recommend `effort: high` for the skill as a whole and reserve `xhigh` for the `build` and `move` shapes' planning phases, which the orchestration component can switch with `/effort` or by running those phases in a `fable` planning subagent defined at `xhigh`. (Verified: per-invocation effort cannot be set on the Agent tool, so a distinct effort needs a distinct agent definition.)

**Archaeology scout: a predefined subagent, `drive-scout`, read-only, returning a structured brief.** Archaeology produces exactly the verbose output the subagent docs say to keep out of the main context (file listings, test output, git history). Sonnet at `high` is right for M; for L and XL, where the codebase is tangled and the brief drives architecture, use an opus variant. Because effort is per definition, ship two files with the same body: `drive-scout` (sonnet, high) and `drive-scout-deep` (opus, high). Both omit `Agent`, `Edit` and `Write` so they stay read-only and cannot nest. Bash stays, because `git log`, `ls` and running the test suite once for the baseline are the point; the system prompt forbids any mutating command.

Draft `~/.claude/agents/drive-scout.md`:

```markdown
---
name: drive-scout
description: Read-only archaeology of an existing codebase for the /drive skill. Returns a structured brief: how to build and test, conventions, recent history on the touched path, traits detected, baseline test result. Never edits.
tools: Read, Grep, Glob, Bash
disallowedTools: Edit, Write, NotebookEdit, Agent
model: sonnet
effort: high
maxTurns: 40
---

You are the archaeology scout for an autonomous engineering run. You read; you never change anything. Run no command that writes, installs, deploys, or touches git state beyond reading (`git log`, `git show`, `git diff`, `git status` are fine; `git checkout`, `git stash`, `git commit` are not).

You will be given: the working directory, the classification block from `.drive/STATE.md` (shape, traits, size, and the path or feature under investigation), and the questions the orchestrator needs answered.

Produce a brief in exactly this structure, in plain language, with file paths:

1. Build and test: the commands that build, lint, typecheck and test, taken from CLAUDE.md, package manifests or CI config; which ones you ran and their result (run the test suite once for the baseline unless it is known to take more than ten minutes, then say so). Name every test double or shim you can see (in-memory stores, sql.js, mocked HTTP) and, for each, where it is kinder than the production system it stands in for.
2. Conventions: directory layout, naming, error handling, how similar features or fixes were done recently (cite two examples by path and commit).
3. The touched path: the files involved, their callers and callees, the tests that cover them, and the last ten commits that changed them with one line on why each mattered.
4. Traits observed, each with the evidence: ui, api, auth (identity, secrets, payments, personal data), data (schemas, migrations, stores), async or scheduled systems (cron, queues, workflows, alarms, webhooks), external systems, concurrency, native platform, generated code, large surface (count files the change would touch).
5. Risks and unknowns: anything the orchestrator's assumptions got wrong, anything that suggests the size or shape should change, anything that looks like a live system.

Do not speculate beyond what you read; mark inferences as inferences. Keep the brief under 150 lines. Do not summarise files you did not open.
```

`drive-scout-deep.md` is identical except `model: opus` and a description that says "for L and XL runs and tangled codebases".

**Classification refuter: an opus subagent, read-only, used at L and XL or whenever the intake records low confidence.** It receives the prompt, the probe, the scout's brief and the classification block, and is told to argue for a *different* shape, size or missing trait, or to concede. It does not need a definition of its own; the orchestrator can spawn the verification component's read-only reviewer with a prompt. It exists because the one place self-critique is weakest is the classification the orchestrator just wrote; the cost is a single call and it fires only at the sizes where a wrong call costs a day.

**Sonnet-low graders named by this component's gates:** claim-to-source matching for `prose-content`; "does this diff touch a file matching the auth signal list" as a backstop to `grep` for the `auth` re-classification trigger; "did behaviour change between these two outputs" for `move` comparisons; screenshot-versus-tokens matching for `ui`. Each is a definition with `model: sonnet`, `effort: low`, `tools: Read, Grep, Glob`, no Bash, no Agent, and an instruction to answer in a fixed short format. They grade; they never fix.

Isolation: none of the roles in this component write, so none needs `isolation: worktree`.

---

## 7. Failure modes and anti-patterns

Each is paired with how the skill prevents it, and the mirage-completion variant is called out where it exists.

**Wrong shape, feature-as-fix.** "Fix the dashboard so it also shows weekly totals" is a feature; treating it as a fix skips the mini-spec and the design delta and produces an unreviewed addition. Prevention: the precedence rule's history check ("did the expected behaviour ever exist?").

**Wrong shape, fix-as-feature.** A defect treated as a feature adds code around the symptom with no reproducer; the tests that get written pass against the new code and prove nothing. This is a mirage: green tests, bug intact. Prevention: a named defect always fires `fix` first; the reproduce gate cannot be skipped at any size.

**Wrong shape, migration-as-feature.** New behaviour rides along, nothing pins what "the same" meant, and the comparison step cannot exist. Prevention: `move` forbids new behaviour by rule; the wish list becomes a `feature` sub-goal after cutover.

**Missed `ui` trait on non-obvious surfaces.** Emails, PDF reports, TUIs and generated HTML are looked at by humans and break visually. The owner's text-only email shipped for exactly this reason. Prevention: the trait's definition is "anything a human looks at", and HTML templates in the probe confirm it.

**Missed `existing-code` when the cwd is empty.** The prompt names a project; the run builds a second one. Prevention: step 2 searches `~/Projects/<name>*` before concluding greenfield, and records the located repo in the probe.

**Size under-called, live proof skipped.** The archetype is the D1 bind-variable incident: local shim, 24 green runs, failed live. Prevention is deliberate: the harness-fidelity audit and the live-proof gate are *trait* gates (`data`, `api`, `deploy-infra`), so they attach at every size; the status ladder's Local Proof label is the honest ceiling when live proof is impossible, and the skill says so rather than inflating.

**Size over-called, ceremony on a bug.** Prevention is structural: size thins or deepens the shape's own phases and never imports phases from another shape, so no size of `fix` acquires a specification.

**Trait inflation.** Everything gets `auth` and `data`, reviews pile up, and the owner learns to ignore them. Prevention: the thresholds in §4.3; `suspected` traits are refuted (and their gates removed) by the scout's brief, not left attached forever.

**The checklist mirage.** The derived plan in STATE.md is a list; lists get ticked. Prevention: every line names an artifact path and an exit check, and the ladder cannot advance a component without the artifact existing and the check having run *in this session's transcript*; ground-truth precedence (code and tests beat artifacts beat status beat prose) is the rule the reviewer applies when the file and the tree disagree.

**The question mirage.** Asking the user and reporting the question as progress, or stopping the run to wait. Prevention: the unavoidable-question test is strict; the default is stated; independent phases continue; the pending question lives in STATE.md for the resume.

**Re-classification never fires.** The trigger table exists but nothing reads it. Prevention: the gate check is a numbered line item at every phase boundary in every shape file, and the event triggers are phrased as standing rules near the top of SKILL.md where they survive compaction.

**Compaction amnesia.** The orchestrator loses the plan mid-run, re-plans from a partial memory, and diverges from the recorded classification. Prevention: STATE.md is the authority; shape files are re-read at every phase start; helper skills load inside subagents so `/drive` is not evicted from the re-attachment budget.

**Entangled sub-goals.** A fix and a feature in one prompt land in one diff; the fix cannot be reviewed on its own and the reproducer's meaning is lost. Prevention: sub-goals with separate classification and separate commits, in dependency order.

**Inline security review flips the session model.** Verified today: after a classifier fallback the session continues on the fallback model. An orchestrator that reviews an auth boundary inline can finish the run on Opus 4.8 without noticing. Prevention: `auth` work runs in a subagent with explicit `model: opus`.

**Scheduled work reported as done.** "The cron will pick it up" ends a phase. Prevention: the `async-scheduled` trait's exit check requires a triggered run's effect in the transcript; the `operate` shape's reference file opens with the rule.

---

## 8. Open questions and trade-offs

**Where the state file lives and whether it is committed.** I propose `.drive/STATE.md` in the repository, committed at M and above (the owner's Arcwell culture treats status files as part of the repo's truth) and absent at XS and S for `fix` and `feature` (the commit body carries the claim and evidence). The trade-off is repo clutter against resumability. This belongs to the state-tracking component; my only firm position is that XS must produce no file.

**`operate` as a shape.** The case for it is the missing implementation phase and the primacy of live observation. The case against is that it is rare compared with the other six and could be a `fix/incident` sibling. I keep it, because the owner's day contains many of these and it is the shape where the scheduler rule matters most; if the coordinator cuts it, its rules should fold into `fix/incident` and `deploy-infra`.

**Multi-shape prompts.** Sub-goals in dependency order is my recommendation. The alternative, one L project with mixed phases, produces entangled diffs. Open: whether each sub-goal gets its own `/goal` condition or one condition names both.

**`/goal` per run or per phase.** The evaluator judges from the transcript only, so the orchestrator must surface the state file's exit criteria in its own output at phase ends. I lean toward one goal per phase at L and XL (bounded, "or stop after N turns" with N by size: roughly 15 for S, 40 for M, 100 per phase for L and XL) and one per run below that. This is the orchestration component's call.

**Whether a skill can start a dynamic workflow.** The docs verify that "use a workflow" in the user's own words works and that the `ultracode` keyword does not fire from `-p` or relayed prompts; whether a skill's instruction counts as the user's request I could not verify. Recommendation: treat workflows as an optimisation for `large-surface` at L and XL and design every fan-out so parallel worktree subagents can do the same job if the workflow does not start.

**Alias drift.** The owner named Opus 4.8 and Sonnet 4.8; the live docs resolve `opus` to Opus 5 and `sonnet` to Sonnet 5 on the Anthropic API. The skill should use aliases only and never state version numbers in its body; a note in the README can record what the aliases resolved to on the day it was written.

**The `/goal` evaluator runs on Haiku.** The owner distrusts Haiku, and `ANTHROPIC_DEFAULT_HAIKU_MODEL` also moves compaction summaries to whatever it names. Recommendation: leave it, and write goal conditions so a small model can judge them from surfaced text ("STATE.md shows every component at Done and the last verification command's output appears above"). The owner can set the env var to a Sonnet model if he prefers; the skill should not do it for him.

**Size rounding.** I chose "round down and re-classify" except for `move` and `operate`. The alternative, always round up, wastes tokens on the many small tasks and is the ceremony the owner is trying to stop paying for. The re-classification triggers are the safety net; if in practice under-calls recur for a shape, that shape's file should switch to rounding up.

---

## 9. Skill text candidates

Ready to lift. Plain language, imperative voice.

**1. (SKILL.md, intake header)**
Classify before you plan. Answer three separate questions and record each: what kind of work this is (the shape, which fixes the order of phases), what it touches (the traits, which attach gates), and how big it is (the size, which sets depth and parallelism). Do not collapse them into one label; a large bug is still a bug and gets no specification, and a two-line change to an auth file is still two lines but still gets the security review.

**2. (SKILL.md, shape precedence)**
Pick the shape by the first rule that fires. A named defect, failure or wrong output is a fix (a live system failing now is an incident; a measured quality like slowness is perf). "From X to Y", migrate, consolidate, upgrade, refactor or simplify with behaviour preserved is a move. A prose-only deliverable is a report. A site, docs or designed content is a publish. A change to a live system with no code as the point is an operate. Existing code that will host the deliverable makes it a feature. Anything else is a build. Before calling something a fix, check whether the expected behaviour ever existed; if it never did, it is a feature phrased as a complaint.

**3. (SKILL.md, sizing)**
Size is the largest any structural trigger demands: components touched, unknowns left after a thirty-second probe, surfaces, repositories, honest duration. Risk never sets size; data, auth and live systems attach their gates through traits at every size. "Deep", "annoying" and "critical" describe mood, not structure; they set nothing. When two sizes are defensible, take the smaller and let re-classification correct you, except for moves and operations, where an under-call skips the undo and the cutover plan; there take the larger.

**4. (SKILL.md, the probe)**
Spend thirty seconds on the tree before you decide anything: is it a repository, what stacks are present, is there a CLAUDE.md, how are tests run, what do the last twenty commits touch, and does the noun in the prompt exist here. If the directory is empty but the prompt names a project, look for it under `~/Projects` before assuming greenfield. Write what you found into the classification block; the probe is the evidence your assumptions rest on.

**5. (SKILL.md, traits)**
A trait is anything the work touches that changes what must be proven. Mark each one confirmed (seen in the prompt or the tree) or suspected (inferred from the stack). A suspected trait keeps its gate until the archaeology brief refutes it: an unneeded review costs minutes, a missed one costs the D1 incident. Attach `auth` only when the diff touches identity, money or personal data; attach `data` on schema or write-path changes, not on a read against an existing table; attach `ui` to anything a human will look at, including emails, reports and terminal interfaces.

**6. (SKILL.md, no questions)**
Assume and record rather than ask. Ask the user only when two readings of the prompt lead to different deliverables and proceeding on the wrong one would destroy something or waste more than an hour that cannot be redirected. Then ask once, in conversation, state the default you will take, keep working on every phase that does not depend on the answer, and write the pending question into the state file so a resume sees it. Never ask a second question, and never report a question as progress.

**7. (SKILL.md, the plan is the file)**
Derive the plan from the shape's phases minus its skips, plus each trait's gate at its phase, thinned or deepened by size, and write it into `.drive/STATE.md` as a checklist where every line names its artifact and its exit check. From then on the file is the plan, not your memory of this text. Re-read the classification block and `references/shapes/<shape>.md` at the start of every phase; after compaction they are the only record.

**8. (SKILL.md, standing re-classification rule)**
Re-classify the moment the picture changes, wherever you are. A fix that needs an interface change is a refactor; a feature that needs a schema gains `data` and a rollback plan before another line is written; a cron, queue or webhook on the path gains `async` and the drive-now rule; an auth, secret or payment file entering the diff gains `auth` even at XS; a workaround applied a second time means the diagnosis was wrong, so stop and reopen the hypothesis ledger; a component or repo count past the size's ceiling moves the size up. Append the change to `reclassifications`, keep every piece of evidence already gathered, and re-derive only the phases that remain. Downgrades are expected and welcome.

**9. (references/shapes/fix.md, opening)**
Reproduce before you theorise. Write a test or script that fails for the reported reason and record it failing; if the failure is intermittent, record the rate and the loop that exposes it. Keep a hypothesis ledger: each entry names the hypothesis, the prediction it makes, the experiment that would refute it, and the result. Fix at the cause, then prove with the same reproducer and keep it as the regression test. Check who else calls the changed code. If you find yourself applying the same workaround twice, the first diagnosis was of a symptom; go back to the ledger.

**10. (references/shapes/move.md, opening)**
No new behaviour enters a move. Pin what exists first with characterization tests at the boundary and recorded outputs on real inputs, then move in strangler steps: shadow, dual-run, compare, flip, remove, each with its undo written before it runs. Anything the owner wants changed becomes a feature after the cutover, with its own classification and its own commits.

**11. (references/shapes/operate.md, opening)**
Nothing here is done because a command exited zero. Read the runbook and the state, write the undo for each step before you run it, drive the system through its own tools now rather than waiting for its schedule, and record the observed effect. A schedule is a hypothesis about the future; a triggered run is evidence. If a step has to be repeated by hand a second time, it becomes a script or a fix.

**12. (references/gates.md, data)**
Before any destructive step: a backup you have verified you can restore from, a rollback rehearsed on a copy, and a fidelity audit that lists every test double on the path and where it is kinder than production (bind counts, sizes, timeouts, transaction semantics). Green tests against a shim that permits what production forbids certify broken code.

**13. (references/gates.md, auth)**
Run the security review in a read-only subagent with `model: opus` and the `severe-testing` skill preloaded, never inline. A classifier fallback during inline review moves the whole session off Fable for the rest of the run. Secrets are named for the owner to set; they are never fabricated, committed, logged or screenshotted.

**14. (references/gates.md, ui)**
Someone other than the maker reads the rendered result. Screenshot at desktop and 375 px and in dark mode, read the accessibility tree, compare against the design tokens and the previous screenshot, and write a pass or a structured list of gaps. This applies to every surface a human looks at: screens, terminal output, HTML email, generated reports.

**15. (SKILL.md, sub-goals)**
When one prompt carries two shapes, split it into ordered sub-goals sharing one state file: fixes before the features that sit on the fixed path, moves before the features that depend on the new home. Classify each on its own and give each its own commits, so a fix can be reviewed without the feature tangled through it.

**16. (SKILL.md, helper skills)**
Load helper skills inside the subagent that needs them, never in your own context: the security reviewer preloads `severe-testing`, the designer preloads `frontend-design`, the drafter preloads `writing`. Your context holds one skill, this one, so it survives compaction.

**17. (SKILL.md, honesty about proof)**
A component's status is the weakest of its evidence. Local proof against a test double is Local Proof, however many runs are green. A feature that can only be exercised on a physical device stays at Local Proof with the reason written down. Never label something Live Proof because the deploy command returned.

**18. (SKILL.md, XS)**
At XS there is no state file, no subagent and no specification. Read the surrounding code and its tests, make the change, add one test that would fail if your claim were false, run the project's checks, and commit with the claim and the evidence in the body. The commit is the record. Any more is the ceremony this skill exists to stop.
