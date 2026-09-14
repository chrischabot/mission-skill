# 19 — Changing existing systems: migrations, consolidations, and feature additions to a live codebase

Researcher component: existing-codebase discipline. Worked shapes: "move our AI gateway from an external project into a core service of our platform" and "add this new dashboard to the existing product" (web-specific parts of the dashboard belong to another report). Date: 2026-09-14.

Throughout, **verified** means I fetched the page today and the URL is given; **source claim** means the post or another document asserts it and I did not verify; **owner record** means it comes from Chris's own memory notes of work he did on Arcwell (first-hand, but I did not re-run anything); **opinion** is mine and argued.

---

## 1. Executive opinion

Every other component of `/drive` carries the risk that the new thing does not work. This component carries a different risk: that the old thing stops working, quietly, for a consumer nobody wrote down. That asymmetry should shape everything the skill does here. A greenfield app can be verified by looking at it; a migration can only be verified by proving a negative (no consumer was missed, no behavior changed that anyone depended on, no environment difference was hidden by a friendly test harness). The skill therefore has to make three failure modes structurally hard to skip rather than merely discouraged: the hidden consumer, the harness that is kinder than production, and the cutover that cannot be undone.

Three disciplines follow. First, archaeology before change: a short, evidence-tagged note on how the codebase actually works, a table of where the docs and the code disagree, and a blast-radius map for the specific change. Second, the migration playbook: extract an interface, capture current behavior as characterization goldens and recorded traffic, run old and new in parallel with parity checks on deterministic decisions, cut over in weighted stages behind a switch that has already been flipped back once in a drill, soak under an error budget, and only then contract. Third, for feature additions, convention fit: copy the shape of the nearest existing code, extend helpers rather than fork them, land tests in the existing suite, and update CLAUDE.md as part of the change.

Two owner rules need reconciling rather than obeying blindly. Isolation for a migration is a runtime property (shadow-named resources, flags, routing weights), not a git property, so worktrees are the wrong tool here and the skill should not use them. And a soak is the one legitimate scheduled condition in this component, because no verb makes time pass under real traffic; the reconciliation is that the scheduled check must decide and act (advance, hold, or roll back) rather than report, and nothing is called Done while a soak is open.

Models: Sonnet reads, Opus designs and verifies, Fable holds the cutover decision, Sonnet at low effort grades parity mismatches. Argued in section 6.

---

## 2. What the post says, and a critique

The post is about self-improving agent systems in general; only a few lines touch this component, so the critique is short and specific.

**Where it is right.** The structural claim that a verifier sub-agent beats self-critique is the single most important idea for migrations, where the maker has every incentive to believe its parity report. Anthropic's own harness post says the same in plainer words: "agents reliably skew positive when grading their own work" and "tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work" (verified, URL in section 3). The post's insistence on state files ("write before walking away", "read at session start") is exactly what a multi-day migration needs, because the phases outlive any one context window. The five-stage memory progression (fail, investigate, verify, distill, consult) maps cleanly onto the owner's "second time is the bug" rule: a workaround applied twice means the investigate step was skipped.

**Where it is exaggerated.** The post presents "large migrations" and "hand off large projects and review completed deliverables" as Fable's headline use case (source claim, from the post's reading of launch material). Migrations are the worst fit for the "days-long autonomous session" framing, because their critical path is wall-clock time under real traffic, not agent time. A migration that finishes in one heroic session has either skipped the soak or lied about it. The post's Routines section is the closest it comes to acknowledging this, and there it frames routines as producing digests for a human, which for this owner is an approval queue by another name.

**Where it is wrong for this component.** Haiku as the grader is rejected by the owner outright, and I agree for migrations in particular: the grader's job includes noticing that a shim is more permissive than production, which is a reasoning task, not a classification. Sonnet at low effort is the right floor for mechanical mismatch classification; the verdict itself needs Opus. The post's worktree advice ("maker writes in worktree A; verifier reads in worktree B") conflicts with the owner's rule and is beside the point here: a verifier for a live-system change needs read access to production logs and the ability to hit the live endpoint, not a second checkout. Most importantly, the post says nothing about production safety at all: no backups, no rollback drill, no consumer inventory, no parity thresholds, no decommissioning. Those are the whole job in this component, and the skill has to supply them.

**One thing the post gets right by accident.** Its example memory entry ("prc is in dollars, not cents. Verified via SELECT MIN(prc), MAX(prc)") is a characterization fact captured from production data. That is the discipline this report generalizes: current behavior, observed and recorded with the command that observed it, before anything is changed.

---

## 3. Verified facts

### Claude Code harness (all verified 2026-09-14 against code.claude.com)

- **Subagents**: `model` accepts `sonnet`, `opus`, `haiku`, `fable`, a full model ID, or `inherit`; `effort` accepts `low|medium|high|xhigh|max` and "Overrides the session effort level"; `memory` scopes are `user`, `project`, `local` and when enabled "the subagent's system prompt also includes the first 200 lines or 25KB of MEMORY.md". `isolation: worktree` gives "an isolated copy of the repository branched by default from your default branch rather than the parent session's HEAD"; "the worktree is automatically cleaned up if the subagent makes no changes". Background subagents keep every MCP tool and a fixed list of built-ins. https://code.claude.com/docs/en/sub-agents
- **Worktree cleanup semantics**: "Each subagent gets a temporary worktree that Claude Code removes automatically when the subagent finishes without changes; a worktree with changes stays on disk until the periodic sweep below can remove it without losing work." The sweep leaves worktrees that "still hold work: changed or untracked files, or unpushed commits." This is precisely the leftover state the owner refuses to track. https://code.claude.com/docs/en/worktrees
- **CLAUDE.md**: "Treat CLAUDE.md as the place you write down what you'd otherwise re-explain. Add to it when: Claude makes the same mistake a second time; a code review catches something Claude should have known about this codebase; you type the same correction ... that you typed last session." Target "under 200 lines per CLAUDE.md file". CLAUDE.md is "context, not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook instead." Subdirectory CLAUDE.md files "load on demand when Claude reads files in those directories." `/init` "analyzes your codebase and creates a file with build commands, test instructions, and project conventions it discovers." https://code.claude.com/docs/en/memory
- **Large codebases**: per-directory CLAUDE.md, `claudeMdExcludes`, `Read` deny rules for generated/vendored code, code intelligence plugins ("jump to definitions, find references ... instead of scanning the tree"), `worktree.sparsePaths`, per-directory skills, and a note that a `Stop` hook can propose CLAUDE.md updates while "the gap it exposed is fresh". https://code.claude.com/docs/en/large-codebases
- **Hooks**: a `PreToolUse` hook blocks a tool call by exiting 2 with a reason on stderr, or by returning `{"permissionDecision": "deny"}`; "For PreToolUse permission decisions, the most restrictive answer applies, in the order deny, defer, ask, allow." Worked examples block edits to protected files and `rm -rf`. https://code.claude.com/docs/en/hooks-guide
- **/goal**: "a wrapper around a session-scoped prompt-based Stop hook"; the evaluator "does not call tools, so it can only judge what Claude has already surfaced in the conversation"; the condition can be up to 4,000 characters; "To bound how long a goal runs, include a turn or time clause in the condition, such as `or stop after 20 turns`"; the first listed example use is "Migrating a module to a new API until every call site compiles and tests pass". Background work defers evaluation; check-ins begin after 30 minutes. https://code.claude.com/docs/en/goal
- **/loop and scheduling**: "Use them to poll a deployment, babysit a PR, check back on a long-running build"; self-paced mode picks "a delay between one minute and one hour based on what it observed"; "Recurring tasks automatically expire 7 days after creation"; tasks "only fire while Claude Code is running and idle". Cloud Routines have a 1-hour minimum interval, run on a "fresh clone", and have "No" access to local files. https://code.claude.com/docs/en/scheduled-tasks
- **Dynamic workflows**: described for "codebase audits, large migrations, and cross-checked research"; example prompt "migrate every component under src/components/ from JavaScript to TypeScript, working on each file in its own isolated copy"; "Up to 16 concurrent agents"; `Date.now()` and `Math.random()` throw inside the script so a relaunched run is deterministic. https://code.claude.com/docs/en/workflows

### Migration patterns (verified)

- **Strangler fig** (Fowler): gradually replace by routing behavior from old to new until the old can be retired; "the reduced risk and earlier value from the gradual approach outweigh its costs"; requires finding "seams". https://martinfowler.com/bliki/StranglerFigApplication.html
- **Parallel change / expand-contract** (Fowler): "In the expand phase you augment the interface to support both the old and the new versions"; "During the migrate phase you update all clients ... in the case of external clients, this will be the longest phase"; "Once all usages have been migrated ... you perform the contract phase to remove the old version." Applies to interfaces, schemas, deployments, and remote APIs. https://martinfowler.com/bliki/ParallelChange.html
- **Feature toggles** (Fowler/Hodgson): release toggles "should generally not stick around much longer than a week or two"; "It's most important to test the toggle configuration which you expect to become live in production" plus the fallback with toggles off; convention "enable existing or legacy behavior when a Feature Flag is Off and new or future behavior when it's On"; toggles are "inventory which comes with a carrying cost". https://martinfowler.com/articles/feature-toggles.html
- **Scientist** (GitHub): control (`use`) and candidate (`try`); "experiment.run will always return whatever the use block returns"; randomizes order, measures durations, swallows and records candidate exceptions, publishes results; "Scientist is only safe for wrapping methods that aren't changing data" and for writes "modify both the existing and new systems simultaneously anywhere writes happen, and verify the results at read time". https://github.com/github/scientist
- **Online migrations** (Stripe): four phases: dual writing, changing read paths (compared with Scientist), changing write paths, removing old data; "Refactoring all code paths where we mutate subscriptions operations ... is arguably the most challenging part of the migration." https://stripe.com/blog/online-migrations
- **Characterization tests** (Feathers): "The purpose of characterization testing is to document your system's actual behavior, not check for the behavior you wish your system had." Procedure: write a test with a dummy expectation, run it, paste the actual value in, rename the test to what you learned. https://michaelfeathers.silvrback.com/characterization-testing ; definition and origin in *Working Effectively with Legacy Code*: https://en.wikipedia.org/wiki/Characterization_test
- **Canarying** (Google SRE Workbook): canary vs control population; "time is one of the biggest sources of change in observed metrics" so before/after comparison is the wrong design; "no more than a dozen" metrics; duration must cover time-of-day load variation. https://sre.google/workbook/canarying-releases/
- **Error budgets** (Google SRE Book): "as long as there is error budget remaining, new releases can be pushed"; when exhausted "releases are temporarily halted"; a softer form is "slowing down releases or rolling them back when the SLO-violation error budget is close to being used up." https://sre.google/sre-book/embracing-risk/
- **Generator/evaluator split** (Anthropic engineering): quotes in section 2. https://www.anthropic.com/engineering/harness-design-long-running-apps . The earlier harness post adds: a features list in JSON because "the model is less likely to inappropriately change or overwrite JSON files", and the finding of "Claude's tendency to mark a feature as complete without proper testing". https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

### Cloudflare platform facts relevant to the gateway case (verified)

- **Gradual deployments**: `wrangler versions upload` then `wrangler versions deploy` to split traffic by percentage between two versions; re-run to change the split; "each request is independently routed to a version based on the configured percentages" unless version affinity is enabled; "only one version of each Durable Object can run at a time"; last 100 versions usable. https://developers.cloudflare.com/workers/configuration/versions-and-deployments/gradual-deployments/
- **Rollbacks**: `wrangler rollback` to any of the last 100 versions; "Resources connected to your Worker will not be changed during a rollback"; "Errors could occur if using code for a prior version if the structure of data has changed"; rolling back a split deployment sends 100% to the chosen version. https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/
- **Version metadata binding**: exposes `id`, `tag`, `timestamp` so events "can be added to events emitted from the Worker to send to downstream observability systems". https://developers.cloudflare.com/workers/runtime-apis/bindings/version-metadata/
- **Service bindings**: RPC (recommended, `WorkerEntrypoint`) or `fetch`; "both Workers run on the same thread of the same Cloudflare server" with "zero overhead or added latency"; target "must be on your Cloudflare account"; "Cloudflare Access does not propagate ctx.access from Worker A to Worker B"; 32 invocations per request chain. https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/
- **Secrets**: `wrangler secret put/delete` create and deploy a new version immediately; `wrangler versions secret put` for gradual deployments; `wrangler secret bulk` from JSON or `.env` (100 per request); `.dev.vars` locally; "secret values are not visible within Wrangler or Cloudflare dashboard after you define them". https://developers.cloudflare.com/workers/configuration/secrets/
- **Rate limiting binding**: `simple.limit` and `simple.period` (10 or 60 seconds); limits are "local to the Cloudflare location that your Worker runs in" and the system is "permissive, eventually consistent, and intentionally designed to not be used as an accurate accounting system". https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/
- **D1 limits**: 100 bound parameters per query; 100 KB per statement (applies to each statement in a batch); 30 s per query; 1,000 queries per invocation on paid; database is "single-threaded, and processes queries one at a time"; 10 Time Travel restores per 10 minutes. https://developers.cloudflare.com/d1/platform/limits/
- **D1 Time Travel**: restore "to any minute within the last 30 days" (paid; 7 days free); `wrangler d1 time-travel info <db>` returns a bookmark; `restore` "overwrites the database in place", cancels in-flight queries, and returns a bookmark that lets you undo the restore. https://developers.cloudflare.com/d1/reference/time-travel/
- **D1 migrations**: `wrangler d1 migrations create|list|apply`; state in the `d1_migrations` table; no down-migration facility is documented. https://developers.cloudflare.com/d1/reference/migrations/ . `migrations apply`, `migrations list`, and `execute` default to the **remote** database when neither `--local` nor `--remote` is given. https://developers.cloudflare.com/workers/wrangler/commands/d1/
- **D1 export/import**: `wrangler d1 export <db> --remote --output=<file>` with `--table`, `--no-data`, `--no-schema`; import via `wrangler d1 execute <db> --remote --file=<file>`; "A running export will block other database requests"; virtual tables (FTS5) are not exported; int64 precision caveat. https://developers.cloudflare.com/d1/best-practices/import-export-data/
- **AI Gateway binding**: `env.AI.run(model, input, { gateway: { id, skipCache, cacheTtl, cacheKey, collectLog, metadata } })`; `env.AI.aiGatewayLogId`; `env.AI.gateway(id).getUrl(provider)`, `.getLog()`, `.patchLog()`; BYOK via the binding only for keys under the `default` alias. https://developers.cloudflare.com/ai-gateway/usage/worker-binding-methods/ . The universal endpoint (`gateway.ai.cloudflare.com/v1/{account}/{gateway}` with an ordered provider array and `cf-aig-step` response header) is marked **deprecated** in favor of the OpenAI-compatible endpoint and Dynamic Routing. https://developers.cloudflare.com/ai-gateway/usage/universal/
- **Unified billing change (2026-08-07)**: Workers AI and AI Gateway "share common interfaces"; prepaid gateway credits can cover Workers AI and supported third-party providers; different rate limits under credits (50 rpm/account/model for listed frontier models). This changes the cost baseline of any gateway comparison started before August. https://developers.cloudflare.com/changelog/post/2026-08-07-workers-ai-unified-billing/

### Owner records that bear on this component (first-hand notes, not re-verified by me)

- The v2 cutover was done with shadow names (`arcwell-hub-v2`, D1 `arcwell-v2`), v1 left untouched as rollback, delivery cut over as a discrete later step, and v1 retirement left as the irreversible owner call. The stand-down of v1 delivery was inferred from v1 endpoints returning 404 rather than proven by disabling its schedule ("Chris should confirm no other v1 job fires").
- Secrets copied from an archived `.env` had to be dequoted before `wrangler secret put` or the upstream returned 401.
- D1 rejected `GLOB '[...]'` character classes that a local SQLite accepted; a `sql.js` shim allowed unlimited bound parameters where D1 stops at 100, and 24 green validations preceded a live failure.
- Two systems each believed they owned the morning email; the broken one owned the one the owner reads. The zombie was a schedule row on the old system, not code.
- Workflows-engine replay memoizes step return values, so anything computed inside a step must be returned from it; a closure side effect was silently undone on replay.

### From memory, not re-verified (treat as leads)

HTTP `Sunset` (RFC 8594) and `Deprecation` (RFC 9745) response headers for API sunsetting; D1 `db.batch()` executing statements atomically; `wrangler deploy --dry-run --outdir=<dir>` for a bundle-size check without deploying.

---

## 4. Detailed spec

### 4.1 Archaeology before change

Archaeology runs before any edit in an existing codebase, scaled by blast radius (section 5 says how much for each shape). Its output is two short files and a decision.

**Step 1: read what the repo says about itself.** In this order, because each layer can contradict the previous one: `CLAUDE.md`, `.claude/CLAUDE.md`, `.claude/rules/*.md`, `AGENTS.md`, `README.md`, `docs/` index, `CONTRIBUTING`, and any spec or requirements registry (Arcwell has `REQUIREMENTS.yaml` and `docs/product/arcwell-spec.md`). Record every operational claim (a command, a path, a port, a name, a rule) in a claims list; it is checked in step 5.

**Step 2: read the machinery, which cannot lie.** Build and CI config (`package.json` scripts, `Cargo.toml`, `pnpm-workspace.yaml`, `.github/workflows/*`, `Makefile`), deploy config (`wrangler.toml`/`wrangler.jsonc` bindings, crons, vars, routes, environments; Dockerfiles; launchd plists under `~/Library/LaunchAgents` for anything local), test runner config and the test tree, lint and format config, and the migrations directory. From these, write the verified command set: how to build, test one file, test everything, typecheck, lint, run locally, deploy, tail logs. Run each once. A command that is documented but does not run is drift; a command that runs but is undocumented is a CLAUDE.md gap.

**Step 3: read history.** Recent history tells you where the code is alive and who has been touching what:

```bash
git log --oneline -n 60
git shortlog -sn --since=90.days
git log --since=90.days --name-only --format= | sort | uniq -c | sort -rn | head -30   # churn hotspots
git log -S'<symbol or string>' --oneline                                              # when did this appear or vanish
git log --merges --since=60.days --format='%h %s'                                     # what shipped as units
```

Read the last five commit messages touching the area you will change, and any PR descriptions (`gh pr list --state merged --search "<area>"`). Look for reverts and "fix fix" chains; those mark fragile seams. If there is an issue tracker, pull open issues mentioning the area (`gh issue list --search`).

**Step 4: map runtime topology and data contracts.** For a Cloudflare project this is mostly the wrangler config plus a live read: `wrangler deployments list`, `wrangler secret list` (names only; values are not readable, per docs), `wrangler d1 migrations list <db> --remote`, `wrangler d1 execute <db> --remote --command "SELECT name FROM sqlite_master WHERE type='table'"`, cron triggers, queue consumers, service bindings in and out, custom domains. For anything else: process list, systemd/launchd, DNS, load balancer config. Write it as a one-paragraph topology in words (which process receives which trigger and touches which store) plus a list of contracts: table schemas, JSON response shapes, event payloads, MCP tool schemas, CLI flags, environment variables read. Contracts are the things consumers depend on; they are what the blast radius is measured against.

**Step 5: detect drift.** For every claim from step 1, produce a row: claim, source file, reality, evidence (the command or file that shows it). Categories: stale command, stale path, stale architecture statement, stale rule (the code no longer does what the rule says), missing documentation for something the code plainly requires. Drift that is dangerous (a documented "safe" command that is destructive, a documented default that is wrong) is fixed immediately as its own commit; other drift is fixed in the change's own commits, never left for later.

**Step 6: blast radius of the planned change.** For each symbol, route, table, or contract the change will touch: direct callers (grep, and the language-server plugin where installed; the docs recommend code intelligence plugins for exactly this), transitive callers up to an entry point (HTTP route, cron handler, queue consumer, MCP tool, CLI command, UI view), data contracts affected, feature flags or config keys gating the path, tests that cover it, and consumers outside the repo (other repos in `~/Projects`, client configs such as `~/.claude.json` and `~/.codex/config.toml`, dashboards, runbooks, scheduled jobs, webhooks registered with third parties). Score the radius small, medium, or large by the count of entry points and external consumers, and let the score choose the discipline: small means feature discipline (4.4) only; medium adds characterization tests and a flag; large means the full playbook (4.2) even if the request was phrased as a feature.

**Step 7: write the note.** `.drive/how-it-works.md`, at most 150 lines, dated, with every statement tagged `[ran: <cmd>]`, `[read: <path:line>]`, or `[inferred]`, and a final section "Could not verify". Template:

```markdown
# How <repo> works — observed 2026-09-14 at <commit>

## Purpose and entry points
<one paragraph; list of entry points with file:line>

## Runtime topology
<one paragraph in words; bindings, stores, schedules, external services>

## Verified commands
build: …  test-one: …  test-all: …  typecheck: …  lint: …  run-local: …  deploy: …  logs: …

## Data stores and contracts
<table/schema names; response shapes; event payloads; where each is defined>

## Conventions
style/format: …  error handling: …  test layout and naming: …  DI/config pattern: …  commit style: …

## Ownership and history
<hot files last 90 days; recent reverts; areas with no tests>

## Drift (docs vs code)
| claim | source | reality | evidence |

## Could not verify
- …
```

`.drive/blast-radius.md` holds the step 6 map for the current change and is rewritten per change; `how-it-works.md` is updated in place and carries forward between sessions. Both are committed (small, text, useful to the verifier and to the next session). Recorded traffic and goldens are not committed (4.2.3).

### 4.2 Migration playbook

The playbook is expand → migrate → contract (Fowler) with Stripe's dual-write sequencing for data and Scientist-style parity for reads, wrapped in the owner's status ladder. It is written as phases with entry criteria, work, refutation tests, exit evidence, and an undo entry. The plan lives at `.drive/migration/plan.md`.

#### 4.2.1 Current state → target state → invariants

Write three short sections before any code. Current state is the topology from archaeology, restricted to the subject. Target state is the same paragraph rewritten for the end. Invariants are the things that must hold at every moment in between, phrased as tests that could fail:

```markdown
## Invariants (each has a refutation test or a live check)
- I1  Every request an existing consumer sends today receives a response of the same contract shape. Check: characterization goldens G-* pass on both paths.
- I2  No consumer is unlisted. Check: old-path logs contain zero requests from unknown identities over window W.
- I3  Old and new paths agree on every deterministic decision (auth verdict, route, rate-limit verdict, cost line). Check: parity report mismatch-rate ≤ 0.1%, zero on auth/cost fields.
- I4  Error rate on the new path ≤ control + 0.1 pp; p95 latency ≤ control × 1.2. Check: parity report per stage.
- I5  Rollback to the previous state completes in < 5 minutes by one recorded command. Check: rollback drill evidence in undo.md.
- I6  Every schema change stays backward compatible with the previous code version until the contract phase. Check: previous version runs against the migrated schema in the local harness.
```

Thresholds are the plan's error budget (4.2.7).

#### 4.2.2 Consumer inventory

`.drive/migration/consumers.yaml`. The inventory has an `unknowns` section that must be empty before cutover starts, and each consumer has a migration status the verifier checks independently.

```yaml
subject: "AI gateway: external project `ai-gw` → hub core service"
window_observed: "2026-09-07..2026-09-13 from old-path logs"
consumers:
  - id: hub-compose
    kind: internal-code        # internal-code | service-binding | http-client | cron | queue | mcp-client | cli | other-repo | runbook | dashboard | third-party-webhook
    where: apps/hub/src/products/compose.ts:112
    contract: "POST /v1/chat {model,messages} -> {text,usage}"
    found_by: "grep AI_GATEWAY_URL; logs identity svc-hub"
    traffic: "~300 req/day"
    migrated: false
    parity_evidence: null
  - id: claude-mcp-client
    kind: mcp-client
    where: "~/.claude.json mcpServers.arcwell-hub.url"
    contract: "MCP streamable HTTP /mcp"
    migrated: false
unknowns:
  - "12 req/day with UA python-requests, identity token t_7f… — not matched to any listed consumer"
```

How to find consumers, in order of decreasing reliability: the old path's own access logs over at least one full weekly cycle (identities, user agents, paths); grep for the URL, binding name, table name, or function across every repo under `~/Projects` and every client config; scheduled jobs on every machine involved (`crontab -l`, `ls ~/Library/LaunchAgents`, wrangler crons, GitHub Actions in other repos); documentation and runbooks that tell a human to call it; dashboards and alerts that query its tables. The zombie lesson from the owner's records applies: a consumer can be a schedule row in a database, not code.

#### 4.2.3 Characterization tests and recorded traffic

Two corpora, both captured before the first change and both tagged "observed", never "correct":

**Goldens** for pure or near-pure units: a script runs the current implementation over a fixture set and writes `.drive/migration/parity/goldens/<case>.json` with a header `{observed_at, commit, input}`. The test asserts `normalize(new(input)) == normalize(golden)`. Feathers' procedure (dummy expectation, run, paste the actual value, rename) is the manual form; automate it. Behaviors discovered to be wrong are listed in `plan.md` under "Known-wrong behavior preserved or fixed", with a decision per item; a fix is a contract change and gets its own consumer notice. Without that list, a golden set silently turns bugs into specification.

**Recorded traffic** for the integration surface: on the old path, record request and response pairs (headers minus `Authorization` and cookies; tenant identifiers hashed; body size capped) to a `parity_recordings` table or R2 prefix for at least one full cycle of the traffic's periodicity (a week for a daily pipeline). The redaction list is written before recording starts. The corpus is gitignored and, where it matters, copied to the backup bucket.

Both corpora are the "current behavior" the migration must preserve; they are also what the harness runs against production-shaped data (4.5).

#### 4.2.4 Strangler and parallel run with parity

Extract the seam first: define the interface consumers will use (a typed client in the contracts package), implement it as an adapter over the old path, and migrate every consumer to the interface while nothing else changes. This step is pure expand; it ships on its own with the suite green. Only then build the new implementation behind the same interface.

Parity comparison follows Scientist: serve the control, run the candidate, compare, publish. Define parity on **deterministic decisions**, not on nondeterministic payloads. For an AI gateway, the model's text is pass-through and cannot be compared; the gateway's decisions can: identity resolved, tenant, provider and model chosen, cache key, cache hit or miss, rate-limit verdict, headers forwarded, cost computed, log row written. The comparison has three outcomes per field: identical; semantically equal after a named normalizer (ordering, whitespace, float precision, timestamps); real divergence. Every normalizer is named and listed in the report; adding a second normalizer for the same class of mismatch is the "second time" signal and stops the work for a diagnosis.

Never shadow writes to shared stores. For write paths, dual-write with an idempotency key and compare at read time (Scientist's own guidance, and Stripe's phase 1).

#### 4.2.5 Shadow traffic

In a Worker, shadowing is `ctx.waitUntil(candidate(request.clone()))` after the control response is chosen, with the result published to a `parity_events` table (or Analytics Engine) rather than returned. Sample rather than mirror everything when the candidate has real upstream cost: a gateway that calls paid models twice per request doubles spend, so shadow the decision logic on 100% with a stubbed upstream and shadow end-to-end on a small sample (1 to 10%) with the real upstream. Tag both paths with `metadata: {drive_path: "old"|"new", drive_run: <id>}` on the AI Gateway binding so cost and latency can be attributed per path from the gateway logs. Version metadata (`env.CF_VERSION_METADATA.id`) goes on every emitted event so the parity dashboard can split by Worker version.

#### 4.2.6 Staged cutover

Two mechanisms, chosen by where the two paths live:

- Both paths inside one Worker (the usual strangler case): the switch is a config row or KV key read per request, with weights `0 → 10 → 50 → 100` and a per-identity override for forcing a consumer onto the new path. Flags default to the old path when unset (Fowler's convention). The flag has a removal date written in `plan.md` the day it is created.
- Two Worker versions: `wrangler versions upload` then `wrangler versions deploy` with percentages, re-run to advance. Remember the Durable Object constraint (one version per DO) and that request-level splitting is independent per request unless version affinity is on, which matters for stateful flows.

Each stage is an entry in `undo.md` with the exact reverse command. Advance only after the soak check for the stage passes (4.2.7).

#### 4.2.7 Soak periods, and the scheduler rule

A soak is a claim about time under real traffic, and no verb makes time pass. It is the one legitimate scheduled condition in this component, and the owner's rule is honored in three ways rather than ignored.

First, everything that can be forced now is forced now, before any waiting: synthetic traffic against the new path, replay of the recorded corpus, the cron handler triggered directly (`wrangler dev --test-scheduled` locally, or the system's own admin verb live), the rollback drill, and the first weight step. Second, the scheduled check is a decision, not a report: it reads the parity and error metrics for the stage window, compares them with the error budget in the plan, and either advances the weight, holds, or rolls back and writes an incident note. It never produces an item for Chris to review. Third, the status ladder is honest: the migration is at most Live Proof while any soak is open; Operational requires the last soak closed.

Error budget per stage: new-path error rate ≤ control + 0.1 pp; p95 latency ≤ control × 1.2; parity mismatch ≤ 0.1% overall and zero on auth, tenant, and cost fields; at most a dozen metrics (SRE canary guidance), compared against the control population in the same window, never against last week. Budget exhausted means automatic rollback to the previous weight, not a slower advance.

Mechanism: while the session is alive, `/loop` self-paced with the check as the prompt (documented for polling deployments; seven-day expiry bounds a forgotten loop), or the Monitor tool on a script that streams the metric. When the laptop may be closed, a Routine (one-hour minimum, fresh clone, no local files), which means the check must be an admin endpoint on the platform that performs the comparison and applies the decision, and the routine merely calls it. Soak lengths: one full periodicity cycle of the traffic per stage (a daily pipeline needs at least one real day at each weight; a request-driven API needs 24 hours to cover time-of-day load), shortened only when the traffic volume makes the sample representative sooner.

#### 4.2.8 Rollback drill before cutover

At the first non-zero weight, execute the rollback exactly as written in `undo.md`, confirm from logs that 100% of requests carry the old version id or old path tag within the expected minutes and that error rate returns to control, then roll forward again. Record the elapsed time. A rollback that needed any improvisation means the plan is not ready and the cutover does not advance. The drill is repeated once for the data layer if a schema change is involved: apply the down script locally against an export of production, then run the previous code version's suite against it.

#### 4.2.9 Decommissioning the old path

Decommission is disable, observe, then delete, and each step is separate:

1. Disable: remove the old route or binding, disable the old schedule (the row or cron trigger, not just the handler), revoke or rotate old tokens, and set the old path to return a named refusal that is logged, so any survivor announces itself.
2. Observe: zero hits on the disabled path for a full periodicity cycle; the parity table stops receiving old-path events; the consumers inventory shows every row `migrated: true` with evidence.
3. Delete code: yes, promptly; git history is the backup.
4. Delete data stores: after the rollback window (30 days matches D1 Time Travel on paid), and after an export has been written to the backup bucket. Write "safe to delete after <date>: <command>" in `STATE.md`; the next `/drive` session in the repo reads it at start and performs the deletion as housekeeping. That is compounding through state, not a queue.

Contract-phase schema changes (dropping the old column or table) happen only in step 4.

#### 4.2.10 Data migration: batching and backfills

Backfills are idempotent, cursor-resumable jobs keyed by primary key range, driven by a verb (an admin endpoint that processes N batches per call and reports the cursor) or a Workflow, never by a cron that may or may not run. Batch sizes are derived from platform limits, not guessed: on D1, rows per multi-row `INSERT` = floor(100 / columns) to stay under the 100-bound-parameter limit; statements under 100 KB; each invocation under 1,000 queries and each query under 30 s. The harness enforces the same limits (4.5). Verification is per table: row counts, a checksum over sorted primary keys, and a sampled field-by-field comparison; results go in the parity report. The sequence is Stripe's: dual-write, backfill, compare reads, switch reads, switch writes, remove.

#### 4.2.11 Observability during cutover

Before the first weight step exists: a parity report generator that reads the parity events and produces `.drive/migration/parity/report-<date>.md` in a fixed shape; the version metadata and path tag on every event; error rate, p50/p95, and cost per path per hour; the old path's request count (its trend to zero is the decommission signal); and a named refusal counter on both paths. The report shape:

```markdown
# Parity report 2026-09-14
window: 2026-09-13T06:00Z .. 2026-09-14T06:00Z    stage: weight 10%
compared: 4,812   identical: 4,790   normalized-equal: 19 (ordering:12 precision:7)   divergent: 3 (ids: …)
error rate old/new: 0.21% / 0.19%    p50/p95 old/new ms: 410/1,890 vs 380/1,720    cost per 1k old/new: …
old-path requests total: 43,300   unknown identities: 0
budget: PASS on all invariants (I1..I6)    decision: advance to 50%
```

### 4.3 Consolidating an external service into a platform core: the AI gateway case

The gateway case has every hard property at once: it is on the request path of everything else, it holds secrets, it does accounting, it has external clients, and its "output" is nondeterministic. The phased template below is the playbook specialized; each phase has an exit that the verifier checks independently.

**Phase 0: archaeology and inventory.** Exit evidence: `how-it-works.md` for both repos; `consumers.yaml` with an empty `unknowns` list after one weekly cycle of old-gateway logs; the gateway contract written down as types (request shape, response shape, error shape, headers honored, rate-limit semantics, cost computation); the secrets inventory by **name** (`wrangler secret list` on the old project plus its `.dev.vars` keys), because values cannot be read back; a cost and latency baseline captured in the same week the comparison will run, since the August unified-billing change means older bills are not comparable.

**Phase 1: interface extraction.** In the platform repo, add `GatewayClient` to the contracts package and an adapter that calls the external gateway over HTTP with the existing token. Migrate every internal consumer to `GatewayClient`. Capture goldens for the deterministic decision functions (auth resolution, model routing, cost lines) by porting or calling the old code over fixtures, and start recording traffic on the old gateway with redaction. Exit: all internal consumers compile against the interface; goldens and a week of recordings exist; the suite is green; nothing else changed.

**Phase 2: build the core service dark.** Implement `GatewayClient` natively inside the platform, behind the flag `gateway.path` defaulting to `old`. Decisions in this phase:

- *Transport for internal callers*: a service binding (RPC via `WorkerEntrypoint`) if the gateway is its own Worker, or a direct module call if it is folded into the hub. Both remove the network hop and the bearer token from the wire; the binding is the identity. Note that Access context does not propagate across bindings, so the callee must authorize on its own terms (a caller-id argument, not a header it trusts).
- *Transport for external clients*: the HTTP surface stays, frozen at `/v1/*` with the old response shape, validating the old client tokens (migrated as secrets) and logging token id per request so the sunset can be proven.
- *Config and secrets*: provider keys move to the platform's secret store with `wrangler secret bulk` from a JSON file generated by a script that dequotes values (owner record: quoted values caused 401s). Per-tenant keys go to KV or Secrets Store keyed by tenant. A health endpoint reports which secret **names** are set as booleans, never values.
- *Auth and rate-limit parity*: write down what the old gateway enforced (global per-tenant limits via a Durable Object? per-colo counters? none?). The Workers rate-limit binding is per-colo and permissive; if the old system enforced global limits, matching it needs a DO or an explicit acceptance of the semantic change in `plan.md`. Do not let parity be assumed by naming.
- *Upstream*: the AI Gateway binding (`env.AI.run` with `gateway: {id, metadata, skipCache, cacheKey}`) or `getUrl(provider)` for SDK clients. The universal endpoint is deprecated; do not port code that depends on its provider-array fallback without moving to Dynamic Routing.
- *Multi-tenant hygiene*: every cache key, rate-limit key, and log row namespaced by tenant; before dual-write, check for key collisions between the two systems' namespaces.
- *Data*: gateway logs and cost ledger dual-written to old and new tables with an idempotency key (Stripe phase 1). Exit: Local Proof: goldens pass; recorded traffic replays with a stubbed upstream and produces identical decisions; production-shaped data in the harness; D1 constraints enforced in the shim.

**Phase 3: shadow run.** Flag stays `old`; shadow the new path on 100% of requests with the stubbed upstream and on a 5% sample with the real upstream, publishing parity events. Fix divergences at the root. Exit: one full weekly cycle with the budget met; cost per request on the new path measured, not estimated; latency on the new path lower than old (a service binding should be faster; if it is not, find the extra round trip).

**Phase 4: staged cutover for internal consumers.** Flag `new` at 10% (or per-consumer for the least critical consumer first), rollback drill, soak, 50%, soak, 100%, soak. Dual-read compares the two ledgers at each stage. Exit: 100% held for a full cycle; ledgers agree; old-path internal traffic zero.

**Phase 5: external client switch-over.** Per client: point it at the platform's `/v1/*`, verify from logs, mark `migrated: true` in the inventory. Return `Deprecation` and `Sunset` headers on the old host (header names from memory; verify the RFCs before citing them in the skill). Exit: old host zero hits for a cycle.

**Phase 6: decommission.** Disable old routes and schedules, rotate provider keys the old project held, switch writes to the new ledger only, export old tables to the backup bucket, delete the old project's code, and schedule-by-state the resource deletion after 30 days. Update CLAUDE.md (new commands, the gateway's location and conventions), the architecture doc, and `STATE.md`. Exit: Done.

The phases are sized for the gateway; a smaller consolidation collapses phases 2 and 3 but never skips the inventory, the rollback drill, or the disable-observe-delete sequence.

### 4.4 Feature addition discipline

Features on an existing product fail by being written in a different dialect than the code around them. The discipline is imitation before invention.

1. **Convention fingerprint.** Before writing code, find the three nearest existing examples of the thing being added (an existing route for a new route, an existing view for a new view, an existing report for a new report) and record their shape in `blast-radius.md`: file placement, naming, error handling (Arcwell uses named refusals that fail closed; other codebases throw typed errors; some return result objects), validation, logging, test file location and naming, and how configuration reaches them. The new code copies the shape exactly. Where the design system exists (tokens, components), use it; the web-specific rules are in the other report.
2. **Extend, do not fork.** If a helper does 80% of what is needed, add a parameter or a sibling function next to it, keeping its existing tests green, rather than copying it into a new file. A fork is a second place to fix every future bug.
3. **Reviewable changes.** Land the feature as a sequence of commits each of which leaves the suite green: preparatory refactor (if any) first and alone; then the data or contract change; then the behavior; then the docs. No drive-by refactors inside the feature commit. Aim for commits a reader can hold in one sitting.
4. **Tests in the existing suite.** Same runner, same directory convention, same fixtures. Every behavioral claim gets a refutation test (the owner's rule), named for the claim it tries to break, and the whole existing suite runs plus the new tests, not the new tests alone. If the feature touches a shared contract, add a characterization golden for the old behavior first so the run proves nothing else moved.
5. **Performance regression check.** Measure the hot path before and after with the same input: a timed request against the local server, CPU milliseconds from `wrangler tail` or Workers logs on a preview deploy, and bundle size from a dry-run build (command from memory; verify). A feature that adds a KV read or a D1 query per request on a hot path says so in the commit message with the number.
6. **Docs and CLAUDE.md as part of the change.** If the feature adds a command, a convention, or a pitfall a future session would have to rediscover, it goes in CLAUDE.md (the docs' own test: "what you'd otherwise re-explain"). Architecture and user docs updated in the same commit series. The status file entry cites the test names and the proof artifact, per the owner's ground-truth precedence.

### 4.5 Safety

**Backups before anything destructive.** A destructive step is any schema change, any data deletion or rewrite, any secret rotation, any route or schedule removal. Before it: `wrangler d1 export <db> --remote --output=.drive/backups/<db>-<date>.sql` (note it blocks other requests, so run it at a quiet moment and keep it short with `--table` where possible), copy the export to the backup bucket, record `wrangler d1 time-travel info <db>` bookmark, and touch the marker `.drive/migration/backup-<date>.ok`. For KV and R2, copy the affected keys or prefixes. For secrets, record the **names** and confirm the source of truth for values before rotating.

**Undo ledger.** `.drive/migration/undo.md` is append-only and every risky action writes a row before it is executed:

```markdown
| when (UTC) | action | undo | evidence |
| 2026-09-14T09:12 | weight new=10% via config row gateway.path | `POST /internal/config gateway.path=old` (or `wrangler versions deploy <old-id>@100%`) | deploy id …, first new-path log id … |
| 2026-09-14T09:40 | applied migration 0007_gateway_ledger | bookmark 0000…; `wrangler d1 time-travel restore <db> --bookmark=…`; down script migrations/0007_gateway_ledger.down.sql tested locally at commit … | export .drive/backups/…-2026-09-14.sql → r2://backups/… |
```

`STATE.md` carries a short "Undo paths" section pointing at the ledger and listing anything currently reversible only within a window.

**No schema change without a rollback script.** D1 has no down migrations, so every `NNNN_name.sql` gets a hand-written `NNNN_name.down.sql`, and the test is mechanical: apply up then down against a local copy and diff `sqlite_master` against the pre-migration schema. Schema changes stay expand-only (add nullable column, add table, add index) until the contract phase, so the previous code version still runs against the new schema, which is what makes `wrangler rollback` safe (the docs warn rollback does not touch data).

**Harness kinder than production.** Before trusting any local proof, ask of every shim where it is more permissive than the real thing, and close the gap in the harness itself. Concretely for D1: enforce 100 bound parameters, 100 KB statements, and the SQLite dialect D1 actually accepts in the test shim, so the class of bug fails locally. Then dry-run against production-shaped data: export production (`--remote`), import into the local database, apply the migration and the backfill, and run the suite and the goldens against it. Row counts and distributions from production are the fixture; hand-written fixtures are the trap.

**Deterministic guards.** CLAUDE.md is advisory; a hook is not. Install a `PreToolUse` hook on `Bash` for the duration of the migration:

```bash
#!/bin/bash
# .claude/hooks/guard-destructive-wrangler.sh
INPUT=$(cat); CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
if printf '%s' "$CMD" | grep -Eq 'wrangler +d1 +(execute|migrations +apply)' && ! printf '%s' "$CMD" | grep -q -- '--local'; then
  if printf '%s' "$CMD" | grep -Eiq 'drop |delete |alter |truncate|migrations +apply'; then
    marker=".drive/migration/backup-$(date -u +%F).ok"
    [ -f "$marker" ] || { echo "Blocked: remote destructive D1 command without today's backup marker ($marker). Run the backup step first." >&2; exit 2; }
  fi
fi
if printf '%s' "$CMD" | grep -Eq 'wrangler +(delete|d1 +delete|r2 +bucket +delete|kv +namespace +delete)'; then
  echo "Blocked: resource deletion belongs to the decommission step after the rollback window (see .drive/migration/plan.md)." >&2; exit 2
fi
exit 0
```

Registered under `hooks.PreToolUse` with `"matcher": "Bash"` in `.claude/settings.local.json` for the repo. Remember that D1 commands default to remote when no flag is given, which is why the guard treats "no `--local`" as remote.

### 4.6 Verification: what the ladder means for a migration

- **Scaffold**: interface and flag exist; new path returns something. Not evidence of anything.
- **Partial**: goldens pass for some decision functions; parity harness exists.
- **Local Proof**: all goldens and the recorded-traffic replay pass on both paths; the harness enforces production constraints; the migration and backfill have run against an export of production data locally; the down script has been exercised. This is the maximum status any local-only work can hold.
- **Live Proof**: shadow traffic parity met the budget for a full cycle with the real upstream on a sample; the rollback drill was executed in production and recorded; at least one weight stage is live and its soak has passed; the parity dashboard is producing reports from production events.
- **Operational**: 100% weight held through its soak; the old path disabled and observed at zero hits for a cycle; every consumer marked migrated with evidence; docs and CLAUDE.md updated; `STATE.md` records the pending resource deletion date.
- **Done**: old code deleted, old resources deleted after the window with exports retained, flag removed, `plan.md` closed with the final parity report linked, and code, tests, proof artifacts, `STATE.md`, and docs all agreeing.

The verifier (section 6) judges the rung from the evidence, not from the maker's claim, and applies the owner's precedence: working-tree code and tests, then proof artifacts, then status files, then prose.

---

## 5. Conditionals by project shape

**Greenfield app (fashion iOS app, Cloudflare backend).** Archaeology reduces to a collision check: existing Workers, D1, R2, KV, and domain names in the account, so shadow names later remain available; existing repos and client configs that might be confused by a new MCP server name. No migration playbook. One habit is worth planting on day one because it makes every future migration cheap: version the public API path (`/v1/`), tag emitted events with version metadata, and write `how-it-works.md` at the end of the build so the next session inherits it.

**Deep bug hunt.** Archaeology is the primary tool but scoped to the failing path: entry point to sink, with the drift table limited to claims about that path. The characterization test becomes the reproduction test and is written before the fix. Blast radius is computed for the fix, not the bug, because fixes in shared helpers are how bug hunts break other consumers. "Second time is the bug" governs the loop: a second workaround on the same symptom halts the hunt and reopens diagnosis. No flags, no soak, unless the fix changes a contract, in which case it becomes a medium-radius change and gets a golden and a flag.

**Feature on an existing product (dashboard).** Full archaeology at light depth (steps 1, 2, 4, 6, 7; step 3 only for the touched area), then the feature discipline of 4.4 in full. If the dashboard needs a new table or a change to a shared query, the schema part follows expand-only rules with a down script and a backup marker, and the dashboard reads behind a flag until its own data is verified. Performance check is mandatory because dashboards are where N+1 queries are born. The web-specific verification is in the other report; the existing-codebase part is that the dashboard is written in the product's dialect and its tests live in the product's suite.

**Migration / consolidation (AI gateway).** Everything in 4.1 through 4.6, with the phased template in 4.3. This is the shape the component exists for.

**Research + website.** If a site already exists, replacing it is a migration in disguise: the URL inventory is the consumer inventory (inbound links, sitemap, RSS subscribers, OAuth callback URLs, documentation links from other repos), the parity check is "every old URL resolves to the right new page or a 301", the flag is DNS or a routing rule, and the rollback is the previous deployment. Capture the old sitemap and a crawl as the recorded corpus before touching anything. If no site exists, this component is not involved.

**Other shapes.** *Refactor / simplification*: characterization goldens are the entire safety net; treat it as a migration with one consumer (the suite) and no soak. *Ops / incident*: archaeology under pressure inverts the order (topology and recent history first, docs last), and every action goes in the undo ledger before it runs. *Data pipeline*: dual-run on the same input window and compare outputs field by field; backfills as in 4.2.10; the soak is one full schedule cycle. *CLI tool*: flags and exit codes are the contract, scripts are the consumers, deprecation warnings are the expand phase. *Library / SDK*: consumers are downstream packages; expand-contract runs across semver majors, and the "old path" is the previous major kept on a maintenance branch, which is the one case where a branch is the right artifact.

---

## 6. Model and effort assignment

The argument, then the definitions.

**Archaeology on Sonnet, with an Opus synthesizer.** Reading build config, tests, and history is volume work with structured output, and Sonnet at medium effort does it well and cheaply when each reader gets one area and a schema. The two parts that are not volume work are drift detection (deciding that a doc claim and the code disagree requires holding both) and the consumer hunt (a missed consumer is the most expensive error in the whole component). So: Sonnet readers fan out per area and return structured findings; one Opus pass at high effort writes `how-it-works.md`, adjudicates drift, and owns the `unknowns` list in the inventory. Running the hunt on Sonnet alone would save little and risk the one thing that cannot be recovered after cutover.

**Migration design on Opus, cutover decision on Fable.** The plan (states, invariants, phases, budget) is hard but bounded; Opus at high effort writes it, and a second Opus context with a red-team prompt tries to break it before any code (find the unlisted consumer, the shim gap, the irreversible step without an undo). Fable is already the orchestrator and holds the most context; it reviews the invariants once and takes the go/no-go at each weight step from the verifier's report. Paying Fable rates to draft documents is waste; paying them to decide whether production moves is not.

**Verifier on Opus, high effort, independent context, no maker transcript.** The verifier must reason about environment differences, read production logs itself, and try to refute the parity report. That is not a classification task and Sonnet at low effort would rubber-stamp it. The verifier is read-only in the repo but must be able to run tests, hit the live endpoint, and query logs.

**Parity mismatch grading on Sonnet, low effort.** Classifying thousands of field diffs into identical, normalized-equal, or divergent with a named normalizer is exactly the grader role the owner wants filled by Sonnet-low instead of Haiku. Output is JSON against a schema; no verdicts.

**Implementation workers on Sonnet for mechanical call-site migration, Opus for the seam.** Migrating fifty call sites to `GatewayClient` is mechanical once the adapter exists; partition by directory and run Sonnet workers sequentially per partition in the single checkout, committing after each with the suite green. The adapter, the native implementation, and any backfill script are Opus work.

**No worktrees.** Partition by path ownership instead. If the dynamic-workflow "isolated copy" pattern is ever used for a very large mechanical migration, the merge and removal of each copy is inside the same workflow step, and the suite runs on the merged tree before the step reports success.

### Predefined subagents (ship into `~/.claude/agents/`)

```markdown
---
name: drive-archaeologist
description: Learns how an existing codebase actually works before any change. Reads docs, build/CI, tests, history, runtime config; detects doc-vs-code drift; writes .drive/how-it-works.md and .drive/blast-radius.md. Writes nothing else.
model: sonnet
effort: medium
tools: Read, Grep, Glob, Bash, Write, WebFetch
disallowedTools: Edit, NotebookEdit
---
You are reading a codebase you did not write in order to describe how it actually works today. You are not fixing anything.

Procedure: read CLAUDE.md, .claude/rules, AGENTS.md, README and docs and list every operational claim; read build, CI, deploy, and test configuration and run each documented command once to see whether it exists and works; read the last 90 days of history for churn hotspots, reverts, and recent authorship in the area named in your task; map runtime topology from deploy config and live read-only commands; list data contracts (tables, response shapes, event payloads, tool schemas). Then compute the blast radius of the planned change named in your task: direct and transitive callers up to entry points, contracts touched, flags gating the path, tests covering it, and consumers outside this repo (other repos, client configs, schedules, runbooks).

Tag every statement [ran: <command>], [read: <path:line>], or [inferred]. Keep how-it-works.md under 150 lines and end it with a "Could not verify" list. Write only the two files named above. Do not edit any other file; do not create branches or worktrees; run only read-only commands (no deploys, no remote writes, no `wrangler d1 execute` without `--local`).
```

```markdown
---
name: drive-migration-verifier
description: Independent adversarial verifier for changes to live systems. Never sees the maker's reasoning. Tries to refute parity, completeness, rollback, and status claims using code, tests, logs, and live endpoints. Read-only; returns a structured verdict.
model: opus
effort: high
tools: Read, Grep, Glob, Bash, WebFetch
disallowedTools: Edit, Write, NotebookEdit
---
You are verifying a change to a system that is serving real traffic. You receive the plan (.drive/migration/plan.md), the consumer inventory, the latest parity report, the undo ledger, and the claimed status rung. You do not receive the maker's transcript and you should not ask for it.

Try to refute, in this order: (1) an unlisted consumer exists — grep every repo you can reach and every client config, and read the old path's logs yourself for identities not in the inventory; (2) the harness is kinder than production — find every shim and ask where it is more permissive than the real service, and check that production constraints are enforced in the code under test; (3) the parity report compares the wrong things — confirm both sides read from different stores and that every normalizer is named and justified; (4) the rollback is theoretical — find the drill evidence, and confirm the undo command in the ledger matches the current state; (5) the old path is not really dead — read its request count yourself; (6) docs, CLAUDE.md, and STATE.md disagree with the code.

Judge the status rung from evidence using this precedence: working-tree code and tests, then proof artifacts, then status files, then prose. Return exactly: verdict (rung supported / rung not supported), the highest rung the evidence supports, the list of refutations with file:line or log evidence, and the single most important thing to fix. Never run a command that writes to production.
```

```markdown
---
name: drive-parity-grader
description: Classifies old-vs-new output pairs for a migration parity report. Returns JSON only: identical, normalized-equal (with the named normalizer), or divergent (with the differing field paths). No verdicts, no prose.
model: sonnet
effort: low
tools: Read
---
For each pair you are given, compare the two JSON documents. Return {"id": ..., "class": "identical" | "normalized_equal" | "divergent", "normalizer": <one of the normalizers listed in your task, or null>, "fields": [<json paths that differ>]}. Use only the normalizers listed in your task; if a difference needs a normalizer that is not listed, classify it divergent. Return a JSON array and nothing else.
```

All three run without worktree isolation and in the foreground for the verifier (its verdict gates the next step), background for readers and graders.

---

## 7. Failure modes and anti-patterns

Each entry names how it produces mirage completion and what in the skill prevents it.

- **Rewriting instead of migrating.** A rewrite feels like progress and produces a great deal of new code; the mirage is that the new system "works" while the old one still serves the traffic that matters. The owner's own v2 was a rewrite, and it succeeded because the cutover was then run as a migration: shadow names, old system untouched, delivery switched as a separate step, old path retained as rollback. The skill treats any rewrite's cutover as a full playbook run regardless of how the work was phrased.
- **Big-bang cutover.** One deploy flips everything; the first parity data arrives from angry consumers. Prevented by requiring weight stages with a soak each and a rollback drill at the first stage; the verifier refuses Live Proof without drill evidence.
- **Deleting the old path before parity.** Once deleted, there is nothing to compare against and nothing to roll back to. Prevented by the disable-observe-delete sequence, the hook that blocks `wrangler delete`, and the rule that contract-phase schema changes happen only after the rollback window.
- **Hidden consumers.** The zombie schedule row, the MCP client config on the laptop, the other repo's cron, the runbook that tells a human to curl the old URL. Prevented by building the inventory from the old path's logs over a full cycle rather than from grep alone, by the `unknowns` list that must be empty before cutover, and by the verifier reading the logs itself.
- **Tests that only cover the new path.** The new path is green; the old path (still serving 90%) was broken by the shared helper change. Prevented by running the whole existing suite plus goldens on both flag states, per Fowler's toggle-testing guidance.
- **Parity that compares the new path with itself.** Both sides of the experiment read the new store, or the control is stubbed. Prevented by the verifier's explicit check that the two sides read different stores, and by publishing the control's source in the report.
- **Goldens promoted to specification.** A characterization golden encodes a bug; the migration preserves it faithfully; a consumer who depended on the bug being fixed elsewhere is now stuck. Prevented by the "Known-wrong behavior" list in the plan with a decision per item.
- **Harness kinder than production.** The sql.js shim with unlimited parameters; a local SQLite that accepts a GLOB D1 rejects; a stub upstream that never rate-limits. Prevented by enforcing production constraints in the shim, by dry-running against a production export, and by the verifier's standing question about every shim.
- **Soak reported as done, or skipped.** "It will run tomorrow morning" reported as success, or 100% flipped after ten minutes of green. Prevented by the status rule (at most Live Proof with a soak open) and by making the soak check a decision with an error budget rather than a wait.
- **Approval queue in disguise.** A parity dashboard someone has to look at; a "confirm deletion" item; a digest. Prevented by having the soak check act, by scheduling-through-state for deletions, and by surfacing at most one irreversible choice once in conversation if truly needed.
- **Worktree litter.** A subagent worktree with changes stays on disk until a sweep; the owner will not track it. Prevented by not using worktree isolation in this component and by partitioning by path.
- **Secrets migrated by hand.** Quoted values, missing names, a key rotated on the old project before the new one has it. Prevented by a name inventory, a generated bulk file with dequoting, a health endpoint reporting names as booleans, and rotation only in decommission.
- **Docs left stale.** The next session rediscovers the pitfall. Prevented by treating CLAUDE.md and `how-it-works.md` updates as part of the change's commit series and by the verifier's check (6) above.
- **Replay-memoized side effects.** In durable-execution engines (Cloudflare Workflows, the owner's record) a step's closure side effect is undone on replay; a migration step that "fixed" data inside a closure did not. Prevented by the rule that anything a step computes is returned from the step, and by verifying the effect from the store, not from the step's log line.

---

## 8. Open questions and trade-offs

1. **Where the state files live and what is committed.** I recommend committing `STATE.md`, `.drive/how-it-works.md`, `.drive/blast-radius.md`, `.drive/migration/plan.md`, `consumers.yaml`, `undo.md`, and parity reports (small text, needed by the verifier and future sessions), and gitignoring goldens and recorded traffic. The owner dislikes stray artifacts, so the coordinator should settle one layout across all components; the risk is a `.drive/` directory that grows into another 11 GB proofs folder. Recommendation: text only in git, bulk in R2 or the platform's backup bucket, and a size check in the verifier.
2. **Flag storage on Cloudflare.** A config row in D1 costs a query per request on a hot path; a KV key is eventually consistent (a rollback may take up to a minute to reach every colo); an environment variable requires a deploy to flip. Recommendation: KV with a short cache for request-path flags, with the rollback drill measuring the actual propagation time and recording it as the rollback's real duration.
3. **Shadowing cost for paid upstreams.** Full end-to-end shadowing of an AI gateway doubles model spend. Recommendation as in 4.2.5: 100% on decision logic with a stubbed upstream, a small real sample end-to-end, and an explicit budget line in the plan.
4. **Per-colo rate limiting.** If the old gateway enforced global limits and the new one uses the per-colo binding, that is a semantic change no parity test on a single machine will show. Recommendation: name it in the plan as a decision, and if global semantics matter, implement them with a Durable Object rather than accept the binding's approximation.
5. **Soak mechanism when the laptop is closed.** Routines run on a fresh clone with no local files or credentials, so the soak check must be an authenticated admin endpoint on the platform. That is extra work per project. Recommendation: make the check endpoint part of the phase 2 deliverable in the gateway template and reuse the pattern.
6. **The irreversible owner decision.** Deleting the old D1 or the old project cannot be undone after 30 days. Recommendation: schedule-by-state (write the date and command into `STATE.md`; the next session executes it) rather than asking; if the coordinator prefers a human choice, surface it exactly once in conversation and proceed with "retained, disabled" as the default when unanswered.
7. **How much archaeology for a small change.** A one-line fix should not pay for a 150-line note. Recommendation: the blast-radius score chooses; for small radius, steps 1, 2, and 6 only, and the note is a paragraph appended to an existing `how-it-works.md` rather than a rewrite.
8. **Unverified specifics.** The `Sunset`/`Deprecation` header RFC numbers, `wrangler deploy --dry-run --outdir`, and D1 batch atomicity should be verified before they appear in skill text as facts.

---

## 9. Skill text candidates

For `references/existing-codebase.md`:

**A. Archaeology first.** Before you change a codebase you did not just write, learn how it actually works and write it down. Read what the repo says about itself, then read the machinery that cannot lie: build, CI, deploy, and test configuration. Run every documented command once. Read the last ninety days of history for the files you will touch. Map what runs where and which stores it touches. Write `.drive/how-it-works.md` in under 150 lines, tag every statement with the command you ran or the file you read, and end with what you could not verify.

**B. Drift is a finding, not a footnote.** Where the docs and the code disagree, write a row: claim, source, reality, evidence. Fix dangerous drift immediately as its own commit. Fix the rest inside the change you are making. Never leave drift for later; later does not come.

**C. Blast radius chooses the discipline.** For every symbol, route, table, or contract you will touch, list direct callers, transitive callers up to an entry point, contracts affected, flags gating the path, tests covering it, and consumers outside the repo. Score it small, medium, or large. Small gets feature discipline. Medium adds characterization goldens and a flag. Large runs the migration playbook even if the request was phrased as a feature.

**D. Write in the codebase's dialect.** Find the three nearest existing examples of what you are adding and copy their shape: placement, naming, error handling, validation, logging, test location. Extend an existing helper rather than forking it. Land the change as commits that each leave the suite green: refactor first and alone, then contract, then behavior, then docs.

**E. Tests go in the existing suite.** Same runner, same layout, same fixtures. Name each test for the claim it tries to break. Run the whole existing suite plus the new tests; never the new tests alone. If you touched a shared contract, add a golden of the old behavior first so the run proves nothing else moved.

**F. Measure the hot path.** Before and after, same input: request time locally, CPU milliseconds from the platform's logs, bundle size from a dry-run build. A change that adds a store read per request on a hot path says so in the commit message, with the number.

**G. CLAUDE.md is part of the change.** If you learned something a future session would otherwise rediscover (a command, a convention, a pitfall), write it into CLAUDE.md in the same commit series. Keep the file under 200 lines; move procedures into skills or path-scoped rules.

For `references/migration.md`:

**H. Isolation is a runtime property here.** Isolate with shadow-named resources, flags, and routing weights, not with branches or worktrees. Partition parallel workers by path ownership in the single checkout. If an isolated copy is ever unavoidable, merging and removing it is inside the same step that created it.

**I. Extract the seam before you build anything new.** Define the interface consumers will use, implement it as an adapter over the old path, migrate every consumer to the interface, ship that with the suite green and nothing else changed. Only then build the new implementation behind the same interface, defaulting to the old path when the flag is unset.

**J. Capture current behavior before the first change.** Goldens for deterministic units, produced by running the current code over fixtures and recording the output with the date and commit. Recorded, redacted traffic for the integration surface over at least one full cycle of the traffic's periodicity. Both are labeled observed, never correct. Behaviors you discover to be wrong go in the plan under "Known-wrong behavior" with a decision each.

**K. Build the consumer inventory from logs, not from grep alone.** Read the old path's own access logs over a full cycle and match every identity to a listed consumer. Then grep every repo you can reach and every client config, list every schedule on every machine, and read the runbooks. The `unknowns` list must be empty before the first weight step. A consumer can be a row in a table.

**L. Define parity on decisions, not on payloads.** Compare the deterministic things the two paths decide: identity, tenant, route, cache key, rate-limit verdict, cost line, headers, log row. Treat nondeterministic output as pass-through. Every normalizer is named in the report. If you need a second normalizer for the same class of mismatch, stop and diagnose; the second time is the bug.

**M. Serve the control, shadow the candidate, publish the diff.** Never return the candidate's result while the flag is off. Never shadow writes to shared stores; dual-write with an idempotency key and compare at read time. When the candidate has real upstream cost, shadow the decision logic on everything and the full path on a small sample.

**N. Drill the rollback at the first non-zero weight.** Run the undo command exactly as written in the ledger, confirm from logs that every request is back on the old version or path, confirm the error rate returned to control, roll forward, record the elapsed time. If the rollback needed improvisation, the plan is not ready and the cutover does not advance.

**O. A soak is the one scheduled condition.** No verb makes time pass under real traffic. First force everything that can be forced now: synthetic traffic, corpus replay, the cron handler triggered directly, the drill, the first weight step. Then schedule the check, and make it a decision with an error budget: advance, hold, or roll back and write the incident note. It never produces an item for a human to review. While a soak is open the work is at most Live Proof.

**P. Error budget per stage.** New-path error rate at most control plus 0.1 percentage points; p95 latency at most 1.2 times control; parity mismatch at most 0.1 percent and zero on identity, tenant, and cost. At most a dozen metrics, compared against the control in the same window, never against last week. Budget exhausted means roll back to the previous weight, not advance more slowly.

**Q. Back up before anything destructive, and write the undo first.** Export the database, copy it to the backup bucket, record the Time Travel bookmark, touch the backup marker. Append the undo row to `.drive/migration/undo.md` before executing the action, with the exact reverse command and the evidence you will check. A hook blocks remote destructive commands without today's marker and blocks resource deletion outside the decommission step.

**R. Schema changes are expand-only until contract, and every migration has a tested down script.** Add columns nullable, add tables, add indexes; never drop or rename until the old code version is gone and the rollback window has passed. Write the down script by hand, apply up then down against a local copy of production, and diff the schema against the baseline.

**S. Ask of every shim where it is kinder than production.** Enforce the real limits in the test harness (bound parameters, statement size, dialect, rate limits). Dry-run the migration and the backfill against an export of production data, and run the suite and the goldens against that, not against hand-written fixtures.

**T. Decommission is disable, observe, delete.** Disable the old route, schedule, and tokens and make the old path answer with a logged, named refusal. Observe zero hits for a full cycle. Delete code promptly; git is the backup. Delete data stores after the rollback window with an export retained, by writing the date and command into STATE.md so the next session performs it.

**U. The ladder for a migration.** Local Proof: goldens and replay pass on both paths on production-shaped data with production constraints enforced. Live Proof: shadow parity met the budget for a full cycle, the rollback drill ran in production, at least one weight stage soaked. Operational: 100% held through its soak, old path disabled and at zero hits, every consumer migrated with evidence, docs updated. Done: old code and resources gone after the window, flag removed, and code, tests, artifacts, STATE.md, and docs agree. The verifier judges the rung from evidence with this precedence: code and tests, then artifacts, then status files, then prose.
