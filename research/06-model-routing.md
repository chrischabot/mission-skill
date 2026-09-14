# 06 · Model routing and effort levels

Component: the routing policy the `/drive` skill applies to every role. Models in play: Fable 5.1, Opus, Sonnet; Haiku excluded. Researched 2026-09-14 against live docs, the installed Claude Code (2.1.266), the owner's `~/.claude/settings.json`, and the bundled `claude-api` skill. Where I state a fact I checked it; where I state an opinion I say so.

---

## 1. Executive opinion

The lineup the owner named is one release behind what ships. In Claude Code today the `opus` alias resolves to Opus 5 and `sonnet` to Sonnet 5; there is no Sonnet 4.8 (Sonnet went 4.6 to 5), and Opus 4.8 is a legacy model at the same price as Opus 5 whose only remaining role is as the cybersecurity fallback target. The skill should write aliases (`fable`, `opus`, `sonnet`), never version numbers, and let Claude Code's alias resolution carry the policy forward. The one pinned ID in the whole policy is `claude-opus-4-8`, and only as a contingency.

The routing principle is to route by the shape of the work rather than by prestige. Output-heavy volume (implementation, tests, docs, breadth research) goes to Sonnet 5. Bounded judgment (architecture, review, verification, security) goes to Opus 5 at high or xhigh. Fable 5.1 holds the orchestrator context and takes three one-shot roles where a wrong verdict is the most expensive mistake to discover later: spec and architecture review on greenfield and migration shapes, lesson distillation, and the final audit. Fable's premium on a read-heavy one-shot role is under a dollar. Its premium as orchestrator is bounded by a cache-read rate of $0.25 per million tokens, which is cheaper than Opus's $0.50, provided the main-conversation cache lifetime is raised to one hour. The owner bills by API key, so his default is five minutes, and an orchestrator that waits ten minutes on a subagent currently pays to re-read its whole context at $10 per million.

Grading is two-tier. Sonnet 5 at low effort grades checklists and binary assertions against evidence (tier 1). Opus 5 at high grades quality: architecture, specs, UI, root-cause claims (tier 2). Fable audits the finished run once. Low-effort Sonnet is a good checklist grader and a poor quality grader, and the docs explain why: it follows instructions literally and scopes its work to exactly what was asked.

Effort must be explicit per role. The Agent tool has no effort parameter (verified in 2.1.266), so effort lives in predefined agent files under `~/.claude/agents/`; the Workflow tool's `agent()` does accept per-call effort. The owner's own settings default Fable 5.1 to medium effort, so "inherit" is not a safe default for the orchestrator.

Finally, the classifier rule: cyber-flavored analysis must never touch the orchestrator's context, because in Claude Code a flagged request moves the whole session to Opus 4.8 and it stays there.

---

## 2. What the post says, and a critique

**"Fable 5 costs ~5× what Opus 4.8 does per token."** Wrong by a factor of 2.5. Fable 5.1 is $10 in / $50 out; Opus 5 and Opus 4.8 are $5 / $25. Fable is 2× Opus and 5× Sonnet 5 ($2 / $10). More interesting, and unmentioned, is that Fable 5.1 cache reads are $0.25 per million against Opus's $0.50, so a long-lived Fable context that mostly re-reads itself is cheaper per cached token than Opus.

**The cost-capability matrix (Fable 5 / Opus 4.8 / Sonnet 4.6 / Haiku 4.5).** Two of the four rows are stale. Sonnet 5 shipped June 30 at $2 / $10, cheaper than Sonnet 4.6 was ($3 / $15), with the full effort ladder including `xhigh`. Opus 5 shipped July 24 and the docs call it "a step-change improvement over Claude Opus 4.8" at the same price. The post's structure (orchestrator, bounded hard work, volume, graders) is right; the model names should be read as tiers.

**"Haiku 4.5 for grader sub-agents and cheap classifiers."** The post's reasons (independent context, low cost) are true of any subagent and do not favor Haiku specifically. The owner's distrust is well founded on the facts: Haiku 4.5 has a 200K window, does not support the effort parameter at all, uses the old manual `budget_tokens` thinking, has a February 2025 knowledge cutoff (before every model in this policy existed), uses the previous tokenizer, and its retirement commitment runs out on October 15, 2026, one month from now. Sonnet 5 at low effort costs twice Haiku's rate and is a model you can actually tell to think less. Anthropic's own harness moved the built-in Explore agent off Haiku in v2.1.198 (it now inherits the session model, capped at Opus), which tells you where the Claude Code team landed on Haiku for sub-tasks.

**"A verifier sub-agent tends to outperform self-critique with Fable 5."** Verified. The sentence is Lance Martin's (Anthropic), from his X article "Designing loops with Fable 5" dated 2026-06-09, with the mechanism stated as "because grading is done in an independent context window." Prithvi Rajasekaran's engineering post on harness design gives the empirical texture: "Tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work." The post omits the half of that finding that matters for building one: "Out of the box, Claude is a poor QA agent. In early runs, I watched it identify legitimate issues, then talk itself into deciding they weren't a big deal and approve the work anyway." Separation is necessary, not sufficient. The evaluator needed several calibration rounds, few-shot examples with score breakdowns, and live tools (Playwright) to inspect the artifact. Note also that Rajasekaran ran the same model for generator and evaluator (Opus 4.5, later 4.6); the post's implication that a cheaper model makes a fine grader is the post's, not Anthropic's.

**"Classifiers decline in cybersecurity vulnerability research, biology, chemistry, and model distillation; Anthropic falls back to Opus 4.8 automatically."** Half right. The API's named refusal categories are `cyber`, `bio`, `frontier_llm` (this is the "distillation" one), `reasoning_extraction`, and `general_harms`; chemistry is not a named category. The Fable 5.1 prompting guide states plainly that "finding vulnerabilities in source code is permitted," while the migration guide notes Fable's bug-finding gains "exclude security-focused analysis, where the cyber classifiers apply." On fallback, Claude Code does switch automatically (cyber to Opus 4.8, biology to Opus 5), but the post leaves out the operationally decisive sentence from the docs: "After a fallback, the session continues on the fallback model." In the raw API, fallback is opt-in (`fallbacks: "default"`, beta), not automatic.

**"Route by complexity, not by default."** Right, but the measured data Anthropic has since published adds a constraint the post lacks. An orchestrator with cheaper workers "buys something only when there is bulk to hand off: many independent pieces, ideally too many for one context window. When the work is one dependent chain, or fits in a single context, the orchestrator pays for a plan, a handoff, and a merge that a single model gets for free." In every such case they measured, "the coordinator's model alone at lower effort came out ahead." The deep-bug-hunt shape is one dependent chain. The skill must not impose the fleet on it.

**"/goal ... a small fast model (defaults to Haiku) judges met/not-met."** Verified, and it means the owner's no-Haiku rule is violated by default in every `/goal` loop unless he sets `CLAUDE_CODE_GOAL_GRADER_MODEL` (v2.1.208+) or `ANTHROPIC_DEFAULT_HAIKU_MODEL`. The grader has no tools and sees only the transcript.

---

## 3. Verified facts

### 3.1 The models

| | Fable 5.1 | Opus 5 | Opus 4.8 | Sonnet 5 | Haiku 4.5 |
|---|---|---|---|---|---|
| API ID | `claude-fable-5-1` | `claude-opus-5` | `claude-opus-4-8` | `claude-sonnet-5` | `claude-haiku-4-5-20251001` (alias `claude-haiku-4-5`) |
| Claude Code alias | `fable` | `opus` | none (full ID) | `sonnet` | `haiku` |
| Input / output per MTok | $10 / $50 | $5 / $25 | $5 / $25 | $2 / $10 | $1 / $5 |
| Cache read per MTok | $0.25 | $0.50 | $0.50 | $0.20 | $0.10 |
| 5m / 1h cache write | $12.50 / $20 | $6.25 / $10 | $6.25 / $10 | $2.50 / $4 | $1.25 / $2 |
| Context / max output | 1M / 128K | 1M / 128K | 1M / 128K | 1M / 128K | 200K / 64K |
| Effort levels | low, medium, high, xhigh, max | same | same | same | not supported |
| Thinking | adaptive, always on | adaptive, on by default | adaptive, off when omitted | adaptive, on by default | manual `budget_tokens` |
| Reliable knowledge cutoff | Jun 2026 | May 2026 | Jan 2026 | Jan 2026 | Feb 2025 |
| Status | Latest, released 2026-09-01 | Latest, released 2026-07-24 | Legacy, released 2026-05-28 | Latest, released 2026-06-30 | retirement not before 2026-10-15 |

Sources: [Models overview](https://platform.claude.com/docs/en/about-claude/models/overview), [Pricing](https://platform.claude.com/docs/en/about-claude/pricing), [Fable 5.1](https://platform.claude.com/docs/en/models/fable-5-1/overview), [Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview), [Opus 4.8](https://platform.claude.com/docs/en/models/opus-4-8/overview), [Sonnet 5](https://platform.claude.com/docs/en/models/sonnet-5/overview). `https://platform.claude.com/docs/en/models/sonnet-4-8/overview` returns 404 and no such model appears in the current or legacy lists. Sonnet 5's $2 / $10 "introductory" price is now permanent (pricing page note). Models from 4.7 onward share a tokenizer that produces about 30% more tokens than Sonnet 4.6's, so token counts are comparable across Fable 5.1, Opus 5, Opus 4.8, and Sonnet 5 ([pricing note](https://platform.claude.com/docs/en/about-claude/pricing)). Batch API is 50% off everywhere.

### 3.2 Effort

- Effort defaults to `high` on all four; `high` is "exactly the same behavior as omitting the effort parameter." It "affects all tokens in the response," including tool calls; lower effort means "fewer and terser tool calls." ([Effort](https://platform.claude.com/docs/en/build-with-claude/effort))
- Fable 5.1: "Start with `high`... step down to `medium` or `low` for routine or latency-sensitive work once your evals show quality holds." At `medium`, "results roughly match Claude Fable 5 at lower cost." At `low` it "calls search and retrieval tools less often." At `xhigh` and `max` it "can think for longer before writing a long deliverable" and may draft the deliverable twice. ([Prompting Fable 5.1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1))
- Opus 5: "Start with `high`... step up to `xhigh` for demanding coding and agentic work... use `low` and `medium` liberally as your primary control for token cost." Opus 4.8: "Start with `xhigh` for coding and agentic use cases." ([Effort](https://platform.claude.com/docs/en/build-with-claude/effort))
- Sonnet 5: "respects effort levels strictly, especially at the low end. At `low` and `medium`, the model scopes its work to what was asked rather than going above and beyond... on moderately complex tasks running at `low` effort there is some risk of under-thinking." It "interprets prompts literally and explicitly, particularly at lower effort levels." `medium` on Sonnet 5 is "comparable in intelligence to Claude Sonnet 4.6 at high." ([Prompting Sonnet 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5))
- Measured effort curves (bundled `claude-api` skill, `shared/cost-optimization.md` §2.6, citing Anthropic runs): research and knowledge work is nearly flat (`low` gave up 1 to 3 points for a third to half off cost; `medium` matched default accuracy at 70 to 85% of cost); long-horizon coding on Opus 5 gave up about 2 points at `medium` for half the cost and about 8 at `low` for a quarter. Running everything at `low` and re-running failures at default hit about 93% pass for about $0.70 per task versus 91.7% for $1.39 at default throughout.
- Changing top-level effort mid-conversation invalidates the prompt cache on most models; on Fable 5.1 with an API key or subscription (Claude Code v2.1.260+), changing effort keeps the cache. Switching models always resets it. ([Claude Code prompt caching](https://code.claude.com/docs/en/prompt-caching))

### 3.3 Claude Code mechanics (v2.1.266 installed, checked with `claude --version`)

- Aliases: `default`, `best` (Fable 5.1 where available), `fable` (Fable 5.1), `opus` (Opus 5), `sonnet` (Sonnet 5), `haiku` (Haiku 4.5), `opusplan`. Fable 5.1, Fable 5, Sonnet 5 and Opus 4.7+ have native 1M windows; the `[1m]` suffix is unnecessary on them. ([Model config](https://code.claude.com/docs/en/model-config))
- Subagent model resolution, in order: per-invocation `model` on the Agent tool call; the agent's frontmatter `model` (`inherit` means the main model); `CLAUDE_CODE_SUBAGENT_MODEL`; the main conversation's model. "Before v2.1.251, `CLAUDE_CODE_SUBAGENT_MODEL` came first." The brief's stated order is the pre-2.1.251 one and is now wrong. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (v2.1.257+) overrides everything. ([Sub-agents](https://code.claude.com/docs/en/sub-agents))
- Frontmatter `effort`: "Overrides the session effort level. Default: inherits from session. Options: `low`, `medium`, `high`, `xhigh`, `max`." `experimental.cacheTtl` sets the agent's cache TTL. "A subagent's context window is sized by its own model, not the parent's." Built-in Explore: since v2.1.198 "inherits from the main conversation, capped at Opus." A user agent named `Explore` overrides it. Agent descriptions over 15,000 tokens combined trigger a startup warning. (same page)
- Agent tool schema in this session: `subagent_type`, `prompt`, `model` (`sonnet|opus|haiku|fable`), `run_in_background`, `isolation`, `description`. There is no `effort` parameter. (Observed from the tool definition in this 2.1.266 session.)
- Workflow `agent(prompt, opts)` accepts `model`, `effort` (`'low'|'medium'|'high'|'xhigh'|'max'`), `agentType` (a custom subagent from the same registry as the Agent tool), `isolation: 'worktree'`, `schema`; a `budget` global gives a hard output-token ceiling for the turn. Workflow agents pick their model "in the same order it uses for subagents." (Bundled `workflow-authoring` reference; [Workflows](https://code.claude.com/docs/en/workflows))
- Skill frontmatter `model`: "The override applies for the rest of the current turn and isn't saved to settings." A skill whose `model` differs from the session's "is also a model switch: the next request reads the entire conversation history with no cache hits." Skill `effort` "overrides the session effort level"; `${CLAUDE_EFFORT}` expands to the active level. With `context: fork`, `model` sets the forked subagent's model. ([Skills](https://code.claude.com/docs/en/skills), [prompt caching](https://code.claude.com/docs/en/prompt-caching))
- Session effort precedence: `CLAUDE_CODE_EFFORT_LEVEL` / `--effort` / `/effort`; then a per-model "default effort hold" (Fable 5, Opus 4.8, Opus 4.7 only); then `modelSettings[<model>].effortLevel` or `effortLevel`; then the model default. An unsupported level falls to "the highest supported level at or below the one you set." ([Model config](https://code.claude.com/docs/en/model-config))
- Owner's `~/.claude/settings.json` (read locally): `model: "claude-fable-5-1[1m]"`, `effortLevel: "high"`, `modelSettings["claude-fable-5-1"].effortLevel: "medium"`, `env.ANTHROPIC_SMALL_FAST_MODEL: "claude-sonnet-4-5-20250929[1m]"` (deprecated variable; docs say use `ANTHROPIC_DEFAULT_HAIKU_MODEL`), `forceLoginMethod: "console"` (API-key billing), `permissions.defaultMode: "auto"`. So today a Fable 5.1 session starts at medium effort, and the "small fast model" for background work and `/goal` grading is Sonnet 4.5.
- `/goal`: the evaluator is "your configured small fast model, which defaults to Haiku"; it "does not call tools, so it can only judge what Claude has already surfaced in the conversation"; condition up to 4,000 characters; background subagents defer evaluation, with check-ins after 30 minutes. Override: `CLAUDE_CODE_GOAL_GRADER_MODEL` (v2.1.208+, [env vars](https://code.claude.com/docs/en/env-vars)) or `ANTHROPIC_DEFAULT_HAIKU_MODEL`, which also re-aliases `haiku` and moves background summarization. ([Goal](https://code.claude.com/docs/en/goal))
- Prompt cache TTL: "Main conversation: one hour on a Claude subscription within plan usage; five minutes on usage credits, API key, or cloud provider. Everything else (subagents, workflows, compaction): five minutes." Controls: `promptCacheTtl` / `CLAUDE_CODE_PROMPT_CACHE_TTL` for the main conversation; `subagentPromptCacheTtl` / `CLAUDE_CODE_SUBAGENT_PROMPT_CACHE_TTL` or the agent's `experimental.cacheTtl` for the rest (v2.1.242+). Cache is scoped per working directory, "That includes worktrees of the same repository." Accumulating many images eventually forces Claude Code to drop a batch of the oldest, which invalidates the cache from that point. ([Prompt caching](https://code.claude.com/docs/en/prompt-caching))
- Classifier fallback in Claude Code: "Fable models and Opus 5 run with safety classifiers, which most often flag cybersecurity and biology content." Fable: biology to Opus 5, cybersecurity to Opus 4.8. Opus 5: cybersecurity to Opus 4.8, biology ends in refusal. "After a fallback, the session continues on the fallback model. To return to your original model, run `/model`." "Fallback can trigger on the first request of a session... A repository that contains security or biology material can trip the classifier on that context alone." `switchModelsOnFlag: false` prompts instead; "In non-interactive mode and SDK integrations that can't show the prompt, a flagged request ends the turn with a refusal instead." ([Model config](https://code.claude.com/docs/en/model-config))
- API-side refusal: HTTP 200 with `stop_reason: "refusal"` and `stop_details.category` in `cyber`, `bio`, `frontier_llm`, `reasoning_extraction`, `general_harms`, or `null`. "Benign cybersecurity work can also trigger this category." Server-side `fallbacks: "default"` (beta `server-side-fallback-2026-07-01`) retries on Anthropic's recommended model per category; permitted named fallbacks for Fable 5.1 are Opus 4.8 and Opus 5. ([Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback))
- Fable 5.1 false-positive guidance: fewer than Fable 5 "and finding vulnerabilities in source code is permitted." Three triggers: compile-check phrasing ("ask 'Are there any bugs in this program?'"), lesser-known languages, and "Base64 in tool output." ([Prompting Fable 5.1](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1))
- Vision cost: images are 28×28-pixel patches; 4.7+ models use a high-resolution tier (2576 px long edge, 4,784 tokens max). An iPhone screenshot at 1179×2556 costs about 43×92 = 3,956 tokens: roughly $0.008 on Sonnet, $0.02 on Opus, $0.04 on Fable. Above 20 images in one request a stricter 2000 px limit applies. ([Vision](https://platform.claude.com/docs/en/build-with-claude/vision))
- Multi-model measurements ([Optimizing for cost and intelligence](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence)): on a 21.6M-token corpus benchmark, Fable 5.1 coordinating 25 Sonnet 5 workers cost 47 to 55% less than Fable 5.1 solo ($468 to $552), scored 10 to 12 points lower, and finished in 2.3 hours instead of 15 to 20. On one search benchmark "lowering effort beat an architecture change." Recommended order: "Sweep effort on your current model first... If the sweep shows a gap, price the stronger model alone at low effort. That is the number an advisor pairing has to beat."
- Advisor tool (experimental, API only): Sonnet 5 main accepts Fable, Opus 4.7+, or Sonnet 5 advisors; Fable 5.1 main accepts only Fable 5.1. Toggling it keeps the cache; "Subagents inherit the configured advisor." ([Advisor](https://code.claude.com/docs/en/advisor))
- Anthropic harness-design post ([Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps)): planner + generator + evaluator; evaluator used Playwright to click through the live app; full-stack runs cost $124.70 over 3h50m on Opus 4.6 and about $200 over 6h on the earlier harness, versus $9 in 20 minutes for a solo baseline.
- Evals post ([Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)): "choosing deterministic graders where possible, LLM graders where necessary"; "grade each dimension with an isolated LLM-as-judge rather than using one to grade all dimensions"; "give the LLM a way out, like providing an instruction to return 'Unknown'"; "grade what the agent produced, not the path it took."

---

## 4. Detailed spec

### 4.1 The routing table

Aliases are load-bearing: `fable` = Fable 5.1, `opus` = Opus 5, `sonnet` = Sonnet 5 as of 2.1.266. Effort lives in the agent file. "Override" means the orchestrator passes `model:` on the Agent tool call under a listed conditional; nothing else in the skill names a model.

| Role | Model | Effort | Isolation / tools | Why here | Under-provisioned | Over-provisioned |
|---|---|---|---|---|---|---|
| Orchestrator (the `/drive` turn itself) | fable | high (xhigh for greenfield, migration) | main session; delegates all reading and writing | The only context that lives the whole run; long-horizon persistence and delegation are what Fable is priced for; cache reads at $0.25 make a long context cheap | Opus orchestrator decomposes worse and distills worse; the docs' memory-progression claim (Fable completes fail→investigate→verify→distill, Opus stops at verify) is a source claim but matches my experience | xhigh on a feature: "can gather context and deliberate beyond what the task needs" (migration guide); max: drafts deliverables twice |
| Repo survey / intake facts | sonnet | low | read-only + Bash for `ls`, `git log`, test runner detection | Mechanical, literal, structured output; the orchestrator makes the shape decision itself from the survey | Missed test runner or CI facts cascade; mitigated because the orchestrator re-checks anything the plan depends on | Nothing to gain |
| Researcher, breadth | sonnet | medium | WebSearch/WebFetch/tavily, Read; many in parallel | Flat effort curves on research; each returns URL + verbatim quote; independence matters more than brains | Fabricated citations; mitigate with a tier-1 check that each URL resolves and contains the quote | Opus for breadth wastes 2.5× on the dominant input cost |
| Researcher, synthesis | opus | high | Read the ledger only | Contradiction resolution is judgment | Sonnet merges without noticing contradictions | Fable only when the report is the deliverable (pure research shape) |
| Spec writer | opus | xhigh | fresh context; reads goal, survey, research | Hard but bounded; every downstream role anchors on it | Sonnet writes literal specs that omit the unstated requirement | Override to fable on greenfield and migration: the document with the largest blast radius, and Rajasekaran's planner role |
| Spec reviewer | opus | high | fresh, no maker exposure | Tier-2 grader: completeness, testability of every claim, ambiguity | Sonnet low approves plausible prose | Fable optional on greenfield |
| Architect (backend, frontend, each its own agent) | opus | xhigh | fresh; reads spec + survey | Docs: xhigh is the coding/agentic starting point on Opus; inference of unstated constraints | Sonnet architecture is the classic anti-pattern (§4.6) | Fable architecting a dashboard |
| Architecture reviewer | opus | xhigh | fresh; asks the shim question | Tier-2 grader; must reason about production vs harness kindness (the D1 bind-variable class) | A lenient reviewer certifies a design whose tests will lie | Override to fable on greenfield and migration; absolute premium under $1 |
| Implementer, standard slice | sonnet | high | `isolation: worktree`; Write/Edit/Bash | Volume; one behavioral claim per slice; Sonnet 5 high is the "hardest coding" recommendation's neighbor | Sonnet low/medium narrows scope literally; verifier fails loop | Opus on boilerplate doubles the largest output sink |
| Implementer, hard slice | opus | xhigh | worktree | Concurrency, cross-cutting seams, unfamiliar framework, the actual bug fix | Sonnet fails verification twice and burns rounds | Fable writing code: output at $50/MTok |
| Test author | sonnet | high (opus high for property/concurrency tests) | worktree or same as implementer's, reads spec + claim, not the implementation | Volume; independence is structural (test-first from the claim), not a model property | Tests that mirror the implementation; shim kinder than production | Opus for ordinary unit tests |
| Independent verifier | opus | high | fresh; read-only + Bash to run tests; sees claim, diff, spec; never maker reasoning | Leniency is the documented failure; a stronger, skeptical model is "more tractable" | Sonnet talks itself into "not a big deal" | Fable per slice is the largest possible cost sink; reserve for tie-breaks |
| Adversarial / severe tester | opus | xhigh | worktree or read-only; `severe-testing` skill | Exploratory, tool-heavy; xhigh is recommended for "repeated tool calling"; classifier exposure argues against Fable | Sonnet finds surface bugs only | Fable here gets flagged and moved |
| Security reviewer | opus | xhigh | read-only; `security-review` skill; sanitized report | "Security-focused analysis" is where Fable's cyber classifiers apply; Opus 5 falls back to Opus 4.8 automatically | Sonnet misses severity | Fable: flagged, session moved |
| UI / vision reviewer | opus | high | simulator/Playwright MCP, `inspect` a11y tree, screenshots; crop/zoom | Docs list Opus 5 for "vision-heavy workflows"; evaluator must navigate live, not read one screenshot | Sonnet grades a screenshot's vibe | Fable once, as the design-taste gate on greenfield (tournament pattern) |
| Simplifier | opus | high | via the `simplify` skill; test baseline | Behavior preservation is judgment | Sonnet deletes the thing that mattered | Fable adds nothing |
| Docs writer | sonnet | medium | `writing`/`google-dev-docs-style`; reads code | Volume; a tier-1 checker runs every documented command | Docs describe intent, not behavior; caught by checker | Opus prose is not better docs |
| Grader, tier 1 (checklist) | sonnet | low | read-only + Bash for the named check commands; `maxTurns` small | Binary assertions against evidence; literal and cheap | Used for quality judgments: false "met" | Opus for checklists wastes money on the input-dominated cost |
| Grader, tier 2 (judgment) | opus | high | fresh; rubric + few-shot calibration | Architecture, spec, UI, root-cause, simplification value | Sonnet: leniency, no unstated-requirement inference | Fable: reserve for the final audit |
| `/goal` evaluator | sonnet (via env) | n/a | none; transcript only | Replaces the Haiku default | Haiku (the default) | n/a |
| Lesson distiller | fable | high | fresh; reads STATE, failure log, verifier verdicts; writes to the skill's lessons file | The compounding layer; generalizing without over-generalizing is the hardest judgment; runs once, input-heavy | Opus writes workarounds not rules; "second time is the bug" | max: overthinks a small log |
| Final auditor | fable | xhigh | fresh; never the orchestrator; read-only + Bash | Last line against mirage completion; the most expensive verdict to get wrong; input-heavy, once | Orchestrator self-grades: the self-critique problem by another name | n/a |

Three notes on the table.

First, the absolute-dollar view changes what "over-provisioned" means. A one-shot review that reads 150k tokens and writes 5k costs about $1.75 on Fable and $0.88 on Opus. The premium is under a dollar. Where a wrong verdict costs an afternoon of rework (architecture on a greenfield system, the final audit), Fable is the cheap option. Where the role is output-heavy or repeated per slice (implementers, verifiers), the same 2× premium compounds across dozens of invocations and is not worth it. Route judgment up and volume down; count invocations, not prestige.

Second, the escalation rule replaces guesswork about difficulty. Every slice starts on the standard implementer. If the verifier fails it twice, the orchestrator re-runs the slice on `drive-implementer-hard` (Opus xhigh) with the verifier's findings, once. If that fails, the slice is recorded as an open failure in STATE and the run continues; it never loops. This is the docs' measured "run at low, re-run failures at default" pattern applied to model tier, and it bounds the cost of misjudging difficulty at intake.

Third, the built-in `Explore` and `Plan` agents inherit the session model (Explore capped at Opus). In a Fable session the orchestrator's casual "explore the codebase" runs on Opus. The skill should never call the built-ins for volume work; it calls `drive-survey`. Optionally the owner can drop a `~/.claude/agents/Explore.md` with `model: sonnet`, `effort: low` to override the built-in globally; that is his call because it affects every session.

### 4.2 The two-tier grader policy

Is low-effort Sonnet a good grader? For checklists, yes, and for two documented reasons: Sonnet 5 "respects effort levels strictly" and "interprets prompts literally and explicitly, particularly at lower effort levels." A grader you want to answer exactly the questions asked, cite exactly the evidence given, and say "unknown" otherwise is well served by literalism. For quality judgments, no, for the same reasons: at low effort it "scopes its work to what was asked rather than going above and beyond," and quality grading is precisely the act of noticing what was not asked. Anthropic's own review-harness note adds the trap to avoid in any grader prompt: told to "be conservative" or "only report high-severity issues," Sonnet 5 "may follow that instruction more faithfully than earlier models did" and under-report. Grader prompts must ask for full coverage plus a confidence per item, and filter downstream.

**Tier 0: deterministic, no model.** Tests exit code, build exit code, lint, `git status --porcelain` empty, file exists, URL returns 200 and contains the quoted string, screenshot file exists and is non-empty, no worktrees listed by `git worktree list`. The skill runs these as scripts and writes their output to the run's evidence directory before any model grades anything. Most gates end here. Evidence must land in the transcript as text (a `cat` of the summary file), because the `/goal` evaluator can read only the transcript.

**Tier 1: checklist grader (`drive-grader`, Sonnet low).** Input: a behavioral claim, a list of binary assertions, and pointers to evidence files. Output schema:

```json
{
  "verdict": "met | not_met | unknown",
  "assertions": [
    {"text": "...", "result": "true | false | unknown", "evidence": "path:line or command output excerpt", "confidence": 0.0}
  ],
  "reason": "one paragraph, plain language",
  "model_reported": "the model name stated in your system prompt"
}
```

Rules in its system prompt: every `true` must cite evidence it read or produced by running a named check command; prose claims by other agents are not evidence; any `unknown` makes the verdict `not_met`; never grade quality, only presence and truth of the assertion. It gets Read, Grep, Glob, and Bash restricted to the named check commands, and `maxTurns: 12`.

Use tier 1 for: slice completion checklists, research-ledger citation checks, docs-command checks, STATUS-file consistency (does every "Live Proof" row point at a proof artifact), the `/goal` condition (via `CLAUDE_CODE_GOAL_GRADER_MODEL=claude-sonnet-5`), and the "no stray branches or worktrees" gate.

**Tier 2: judgment grader (`drive-judge`, Opus high).** Input: the artifact, the rubric file for its kind (`references/rubrics/<kind>.md`), and two or three calibration examples with score breakdowns, as Rajasekaran found necessary. One isolated judge per dimension when dimensions are independent (the evals post's recommendation), so a UI review runs design quality, craft, and functionality as three short judges rather than one long one. Output: per-dimension score, a must-fix list ordered by severity, each item with a confidence, and the model line. It is prompted to refute ("Default to not passing if uncertain"), in the workflow reference's adversarial-verify shape.

Use tier 2 for: spec review, architecture review, UI quality from live navigation plus screenshots, "is this fix a root cause or a workaround," simplification value, security severity triage, research-synthesis quality.

**Tier 3: audit (`drive-auditor`, Fable xhigh), once per run**, plus tie-breaks when a maker and a tier-2 judge disagree twice on the same artifact. It applies the ground-truth order (working-tree code and tests, then proof artifacts, then STATUS, then docs) and writes the status-ladder entry itself.

Where grading needs Opus rather than Sonnet, concretely: judging architecture (the shim question requires reasoning about what production would do differently); judging UI from screenshots (spatial and aesthetic judgment plus reading an accessibility tree against a spec); judging whether a bug diagnosis is causal or coincidental; judging specs for the requirement nobody wrote down. Where it needs Fable: the final completion verdict, because it is the only grader whose error the owner will not catch until the next session.

### 4.3 Where routing is expressed, and where the policy should live

The mechanics, ranked by how they behave:

1. **Predefined agent frontmatter** (`~/.claude/agents/*.md`): `model` and `effort` both supported; hot-reloaded within seconds for existing directories. This is the only place effort can be set for an Agent-tool subagent.
2. **Agent tool `model` param**: overrides frontmatter per call; accepts `sonnet|opus|haiku|fable`; no effort.
3. **Workflow `agent()`**: `model`, `effort`, `agentType` per call. When the skill uses a workflow, pass `agentType: 'drive-verifier'` and inherit the file's model and effort; set `effort` inline only for throwaway mechanical stages.
4. **Skill frontmatter** (`SKILL.md`): `model: fable`, `effort: high`. Applies to the orchestrator turn. If the session is not already on Fable this is one model switch and one full cache rebuild at the start of the run, which is acceptable once. `${CLAUDE_EFFORT}` should be written into STATE at intake so the audit can see what the orchestrator actually ran at.
5. **`CLAUDE_CODE_SUBAGENT_MODEL`**: since 2.1.251 it sits below frontmatter, so it is only a default for agents that name no model. Do not set it; do not set `_FORCE` (it flattens the policy for every subagent, teammate, and workflow agent).
6. **Settings env**: `CLAUDE_CODE_GOAL_GRADER_MODEL` for `/goal`; `promptCacheTtl` for the orchestrator's cache.

Recommended layout so the owner changes the policy in one place:

```
~/Projects/drive/
  skill/SKILL.md                      # frontmatter: model: fable, effort: high
  skill/references/routing.md         # the table above + the conditional overrides (the only model names in prose)
  skill/references/rubrics/*.md       # tier-2 rubrics with calibration examples
  agents/drive-*.md                   # one file per role: model, effort, tools, isolation, system prompt
~/.claude/skills/drive -> ~/Projects/drive/skill
~/.claude/agents/drive -> ~/Projects/drive/agents   # directory symlink; agents are scanned recursively
```

The agent files are the policy. To move the verifier to Fable, edit one line in `drive-verifier.md`. To lower implementer effort, one line in `drive-implementer.md`. `routing.md` carries the same table for the orchestrator to read at intake and the short list of conditional overrides it may apply (`model: fable` for spec writer and architecture reviewer on greenfield and migration; `model: fable` for one design-taste judge on greenfield). The orchestrator must not invent overrides beyond that list.

Two things I could not verify and the coordinator should test on install: whether the agents scanner follows a directory symlink (skills are documented to allow symlinks; agents are documented as scanned recursively, without mention of symlinks), and whether a new directory under `~/.claude/agents/` created mid-session needs a restart (the brief says it does for the first file). If the symlink fails, an `install.sh` that copies the files is the fallback.

Settings changes to recommend to the owner (`~/.claude/settings.json`), each with the reason:

```json
{
  "promptCacheTtl": "1h",
  "env": {
    "CLAUDE_CODE_GOAL_GRADER_MODEL": "claude-sonnet-5",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-sonnet-5"
  }
}
```

`promptCacheTtl: "1h"` because API-key billing gives the main conversation a five-minute cache by default; an orchestrator that waits on a fifteen-minute subagent re-reads its entire context at $10/MTok every time. The one-hour write rate is $20 instead of $12.50 per million on new content, which is far cheaper than repeated cold re-reads. `CLAUDE_CODE_GOAL_GRADER_MODEL` replaces the Haiku default for `/goal`. `ANTHROPIC_DEFAULT_HAIKU_MODEL` replaces the deprecated `ANTHROPIC_SMALL_FAST_MODEL` (currently pointing at Sonnet 4.5) for background summarization; remove the deprecated key. The `modelSettings["claude-fable-5-1"].effortLevel: "medium"` entry can stay; the skill's frontmatter overrides it for `/drive` turns.

### 4.4 Cost model

Assumptions: prices from §3.1; orchestrator on Fable with a warm one-hour cache; subagents on five-minute caches; verifier rounds capped at two; screenshots at about 4,000 tokens each. Figures are order-of-magnitude, not quotes.

**Deep bug hunt (existing codebase, one dependent chain).** Orchestrator: about 40 requests, context to 150k; cache reads 40 × 120k × $0.25 ≈ $1.20, new content 200k × $20 ≈ $4, output 30k × $50 = $1.50; about $7. Survey (Sonnet low) $0.25. Two or three investigators (Opus xhigh, hypothesis each, one assigned to refute the leader): about $1.50 each, $4.50. Fix (Opus xhigh) $2. Test author (Sonnet high) $0.50. Verifier (Opus high), two rounds, $3. Severe tester (Opus xhigh) $3. Distiller (Fable high) $1.25. Auditor (Fable xhigh) $2. **Total about $25; range $15 to $40.** The Fable share is about 40%, almost all of it orchestrator overhead on a shape where the docs say a single model would win. That is the price of "one invocation drives everything," and the bug shape should keep the orchestrator's turn count low by delegating the whole hunt to one investigator loop rather than narrating hypotheses itself.

**Feature on an existing product (a dashboard).** Orchestrator: about 120 requests, context to 300k with one compaction; cache reads 30M × $0.25 ≈ $7.50, new content 600k × $20 ≈ $12, output 80k × $50 ≈ $4; about $24. Research (3 Sonnet medium + Opus synthesis) $2.50. Spec + review (Opus) $4. Architect + review (Opus xhigh) $4.50. Implementers: 4 to 6 Sonnet high slices ≈ $8, 1 to 2 Opus xhigh slices ≈ $5. Test authors (Sonnet) $3. Verifiers: 6 slices × 1.5 rounds × $1.50 ≈ $13. Severe tester $5. Security review $3. UI reviewer with 30 screenshots ($0.60 in image tokens) ≈ $3. Simplifier $4. Docs $1. Distiller $1.50. Auditor $3. **Total about $85; range $60 to $150.** With a five-minute orchestrator cache and ten cold re-reads of 300k, add about $30.

**Greenfield app (Cloudflare backend, native Swift iOS).** Orchestrator over a multi-day run with several compactions: $60 to $120. Research (8 Sonnet + Opus synthesis) $8. Spec on Fable (override) $4 and Fable review $2. Two architects (Opus xhigh) $8 and Fable reviews $5. Test strategy (Opus) $3. Implementation, 25 to 40 slices: 70% Sonnet high at $1.50 to $2 ≈ $50; 30% Opus xhigh at $4 ≈ $45; escalations $15. Test authors (Sonnet) $25. Verifiers: 40 slices × 1.5 rounds × $1.50 ≈ $90. Severe testing, several passes, $20. Security review $8. UI reviewer, 150 screenshots (about $3 of image tokens) plus navigation ≈ $20; Fable design-taste gate once, $5. Simplifier $10. Docs $5. Distiller $3. Auditor $6. **Total about $400 to $600; a bad run with many escalations can reach $1,000.** For calibration: Anthropic's three-agent harness built a full-stack app for $124.70 in under four hours on Opus 4.6, and its corpus benchmark had Fable 5.1 solo at $468 to $552.

Where the money goes, in order: verifier rounds (they scale with slices × rounds and run on Opus), the orchestrator's own context (Fable cache writes and output), and implementer output plus retries. The three biggest sinks and how the skill bounds them:

1. **Verifier rounds.** Cap at two per slice, then one model escalation, then record and move on. Run tier 0 first so a slice with failing tests never reaches a model-graded verifier. Batch trivially small slices into one verification. Never give the verifier the maker's transcript (it would both bias the verdict and double the input).
2. **Orchestrator context.** One-hour cache TTL. The orchestrator never reads source files, test output, or screenshots inline; every subagent returns a structured result of at most about 300 words plus paths. Compact at phase boundaries with an explicit "preserve" list (STATE path, open failures, the routing decisions made). Hold model and effort constant for the whole run; Fable 5.1 keeps its cache across effort changes on an API key, but nothing survives a model switch, and the classifier fallback is a model switch.
3. **Implementer output and retries.** One behavioral claim per slice, sized so a Sonnet high implementer finishes in one sitting. Sonnet first, Opus on the second failure. Every implementer's system prompt carries Anthropic's "don't add extras" instruction (report pre-existing bugs as follow-ups, commit tests only where the task asks, don't turn scratch checks into permanent files), which the docs say cuts unrequested additions "substantially with no measurable change in task success." Worktree per parallel implementer, merged and deleted in the same orchestrator step.

Cache-friendly prompts: agent system prompts are static files; volatile task detail goes in the user message. In a workflow fan-out, agents with the same model, effort, agent type, tools, and working directory share a cached prefix, and Claude Code holds the siblings up to five seconds so they read it. Two implementers in two worktrees do not share a cache (different working directories), which is another reason to keep the worktree count equal to the genuinely parallel count and no higher.

Hard stops: `claude -p "/drive ..." --max-budget-usd 150` for headless runs; the Workflow `budget` global for any workflow phase; STATE.md records per-phase estimated spend so the auditor can flag a run that blew its envelope.

### 4.5 The safety-classifier fallback

**Which roles will trip it in ordinary software work.** In descending likelihood: the security reviewer (exploitability reasoning, auth bypass, injection payloads); the severe tester when the scope includes auth, crypto, network, or fuzzing with malformed input; any researcher reading CVE write-ups or exploit repositories; an implementer writing or reviewing cryptographic code (usually fine when it uses a library, riskier when it discusses breaking one); and, per the docs, the orchestrator's very first request if the repository's CLAUDE.md, directory names, or git status contain security material. Base64 blobs in tool output are a named false-positive trigger, so any role that dumps binary or encoded data into its context is exposed regardless of topic.

**How to tell a block from a normal error.** In Claude Code: the transcript shows a fallback notice and the session's model changes; there is no HTTP error, and the turn continues on the new model. In `-p` mode with `switchModelsOnFlag: false`, or when the category has no fallback (biology on Opus 5, `general_harms`, `frontier_llm`), the turn ends with a refusal message instead. From the orchestrator's seat, a flagged subagent looks like a result that is abruptly short, contains refusal language, cites no tool evidence, and completed far faster than the task warranted. At the API layer (if any part of the pipeline calls the API directly, as Arcwell does): HTTP 200, `stop_reason: "refusal"`, `stop_details.category`, and a `fallback` content block or `usage.iterations` entry when a fallback ran; a network or 5xx error looks nothing like this.

**The routing rule.**

1. Roles with expected exposure (security reviewer, severe tester, any investigator whose brief mentions exploits, auth, or crypto) run on `opus`. Opus 5's cyber flags fall back to Opus 4.8 automatically; that is a switch inside the subagent's own conversation, and its cost is one cache rebuild of a small context. If a run shows repeated fallback notices for one role, pin that agent file to `claude-opus-4-8` to skip the switch.
2. The orchestrator never analyzes exploitability inline and never has payloads, PoC code, encoded blobs, or CVE text pasted into its context. Exposed roles return sanitized reports: describe the class of weakness and the fix, never reproduce the attack string. This protects the Fable orchestrator from the fallback that would demote it to Opus 4.8 for the rest of the run and rebuild its largest cache from zero.
3. When a subagent's result matches the block signature, the orchestrator re-runs it once on `claude-opus-4-8` with the same prompt and records `fallback: cyber` (or the category) against that role in STATE. A second refusal is recorded as an open item; the loop never retries a third time.
4. `switchModelsOnFlag` stays `true`. Setting it `false` turns every flag into either a prompt (an approval queue, which the owner has ruled out) or, in non-interactive mode, a dead turn.
5. Every agent's result header includes the model name stated in its own system prompt (this session's system prompt carries "You are powered by the model named Fable 5.1"; subagents get an equivalent line). The auditor compares the reported model against the routing table and flags any role that ran below its tier. A `PreModelSwitch` hook that appends `{from, to, reason, time}` to `.drive/model-switches.jsonl` gives the same signal for the main session, if that hook fires on classifier fallback; the docs confirm the hook exists for `/model` switches, and whether it fires on fallback is unverified.
6. At intake, the survey greps the repository for security tooling and vulnerability write-ups. If present, STATE notes the risk that the orchestrator was demoted on its first request, and the auditor checks the model line before trusting Fable-tier verdicts.

Phrasing hygiene from the docs, to put in every reviewer's system prompt: ask "Are there any bugs in this program?" rather than "Does this compile?"; give context for lesser-known languages; strip base64 from tool output before it enters the model's context.

### 4.6 Anti-patterns

**Fable doing volume work.** Fable writing code, fetching documentation, or running test suites inline spends $50 per million output tokens and $10 per million on every file it reads, on work Sonnet does for a fifth of the price at flat quality curves. Symptom: the orchestrator's own token count dominates `/usage`. Rule: the orchestrator's tools in the `/drive` turn are Agent, Read (for STATE and results only), Write (for STATE), and Bash for the tier-0 scripts; everything else is delegated.

**Sonnet doing architecture.** Sonnet 5 at any effort follows the brief literally and does not "infer requests you didn't make." Architecture is the act of inferring the requirement nobody wrote, and the docs' measured coding curves show Sonnet-class models give up the most on exactly the open-ended work. Symptom: an architecture that satisfies the spec sentence by sentence and fails the first integration test.

**Graders that share context with makers.** Includes the obvious (verifier reads the maker's transcript), the subtle (the orchestrator grades its own plan; the spec reviewer is the spec writer resumed with `SendMessage`), and the structural (a verifier launched as a fork, which inherits the parent's conversation). Every grader is a fresh, non-fork subagent that receives artifacts and rubrics, never reasoning.

**Effort left at default everywhere.** "Default" here means three different things: the API default (`high`), the owner's saved Fable 5.1 level (`medium`), and whatever the session inherited. The skill sets effort explicitly for the orchestrator (frontmatter) and every agent file, and writes `${CLAUDE_EFFORT}` into STATE so the auditor can see it.

**`CLAUDE_CODE_SUBAGENT_MODEL_FORCE`.** Collapses the whole policy to one model for subagents, teammates, and workflow agents; useful for a one-off experiment, fatal as a standing setting.

**Switching the orchestrator model mid-run.** `/model`, `opusplan`, a skill with a different `model`, or a classifier fallback: each throws away the largest cache in the system. The orchestrator stays on Fable from the first request to the last.

**Haiku grading `/goal` by default.** Unless the env var is set, every goal loop is graded by the model the owner excluded. The skill's install step must set it, and the orchestrator should refuse to start a `/goal` loop if `CLAUDE_CODE_GOAL_GRADER_MODEL` is unset (check with `env`).

**Screenshots in the orchestrator.** Each is about 4,000 tokens at $10 per million on Fable, and accumulating images eventually forces Claude Code to drop a batch and rebuild the cache. Screenshots go to the UI reviewer and stay there; the orchestrator gets a verdict and paths.

---

## 5. Conditionals by project shape

**Greenfield app (Cloudflare backend, Swift iOS).** All roles active. Overrides: spec writer and both architecture reviewers on `fable`; one Fable design-taste judge at the end, run as a tournament over two or three design directions (the workflow reference's judge-panel pattern), because Sonnet 5 "may settle into a consistent default visual style." Two architects in parallel (backend, iOS), each Opus xhigh in fresh context, then a third Opus xhigh pass reconciling the API contract between them. UI reviewer active with the simulator MCP (`inspect` for the accessibility tree, screenshots for layout), one judge per dimension. Security review mandatory (auth, storage, network). Orchestrator effort xhigh. Budget envelope $400 to $600; hard stop $1,000.

**Deep bug hunt.** Skip spec writer, architects, docs writer, UI reviewer unless the bug is visual. The orchestrator delegates the whole hunt to one `drive-investigator` (Opus xhigh, `maxTurns` generous) with a second investigator briefed to refute the leading hypothesis before any fix is written. Fix on Opus xhigh; test author writes the refuting test first from the claim; verifier and severe tester on the fix; distiller mandatory (the whole point of the shape is the general lesson). Orchestrator effort high, few turns. If the bug is security-flavored, investigators run on `opus` with sanitized reports. Budget $15 to $40.

**Feature on an existing product.** The default table. Spec writer on Opus xhigh (no override). UI reviewer active only if the feature has UI (the dashboard does: Playwright or Chrome DevTools MCP, not the simulator). Security review active if the feature touches auth, permissions, payments, or user data; otherwise the severe tester covers it. Simplifier runs once after all slices pass. Budget $60 to $150.

**Migration / consolidation (AI gateway into the core platform).** Overrides: spec writer and architecture reviewer on `fable` (highest blast radius; the seam design is the whole task). Implementation splits into many mechanical Sonnet medium slices (call-site moves, config rewrites) in worktrees, following the workflow reference's migrate pattern (discover sites, transform each in isolation, verify each), plus one or two Opus xhigh slices for the seam itself. Verifier per slice at tier 1 (tests pass, no behavior change) and one tier-2 review of the seam. Severe tester on the integrated result with the explicit shim question: where is the test double kinder than the real gateway? Distiller mandatory. Budget $100 to $300.

**Research + website.** Researchers as a Sonnet medium fan-out, or the bundled `/deep-research` workflow when the owner has opted into workflows. Synthesis on Opus high; on `fable` if the market-position report is itself a deliverable. Website: `frontend-design` skill, Sonnet high implementers, Opus UI reviewer with Playwright, one Fable design-taste judge. Docs and blog copy on Sonnet medium with the `writing` skill and a tier-1 checker that every documented link resolves. Severe tester light (forms, 404s, mobile widths); security review light (static site) unless there is a contact form or auth. Budget $40 to $120.

**Other shapes.** Pure research report: Sonnet breadth, Fable xhigh synthesis when the report is the deliverable, tier-1 citation check mandatory. Refactor/simplification: Opus high via `simplify`, deterministic test baseline before and after, tier-2 judge on behavior preservation, no Sonnet in the loop. Ops/incident: Opus xhigh investigator, no Sonnet, classifier caution if the incident is a security event, distiller mandatory. Data pipeline: Sonnet implementers, Opus for schema and invariants, verifier must run against production-shaped data (the bind-variable lesson: a shim that accepts anything certifies nothing). CLI tool: Sonnet throughout with an Opus verifier. Library/SDK: Opus xhigh for the public API design and its review, Sonnet for implementation, docs writer plus tier-1 command checker mandatory.

---

## 6. Model and effort assignment for this component's roles, with draft frontmatter

All agents below are predefined in `~/Projects/drive/agents/` (symlinked into `~/.claude/agents/`). None use `memory:` (durable lessons live in the skill's own files, which the owner controls and versions). None are forks. Descriptions are kept short because they all load into every session's context.

**`drive-grader.md` (tier 1)**

```yaml
---
name: drive-grader
description: Grades a checklist of binary assertions against evidence. Use for slice completion, citation checks, docs-command checks, status consistency.
model: sonnet
effort: low
tools: Read, Grep, Glob, Bash
maxTurns: 12
color: green
---
You grade assertions, not quality. You receive a behavioral claim, a list of binary assertions, and paths to evidence. For each assertion answer true, false, or unknown, and cite the evidence you read or the exact command you ran and its output. Prose written by another agent is not evidence. If any assertion is unknown, the verdict is not_met. Run only the check commands named in your brief. Do not fix anything. Return JSON matching the schema in your brief, and include the model name stated in your system prompt in the model_reported field.
```

**`drive-judge.md` (tier 2)**

```yaml
---
name: drive-judge
description: Judges one quality dimension of an artifact against a rubric with calibration examples. Use for spec, architecture, UI, root-cause, and simplification reviews.
model: opus
effort: high
tools: Read, Grep, Glob, Bash, WebFetch
maxTurns: 30
color: purple
---
You are a skeptical reviewer with no stake in the work. You receive an artifact, one rubric dimension, and two or three scored examples that calibrate the scale. You did not see how the artifact was made and you must not ask. Inspect the artifact directly: read the code, run the checks, open the page or screen if a tool is provided. Report every issue you find, including ones you are uncertain about, each with a severity and a confidence; a downstream step filters, you do not. Default to not passing when uncertain. Ask of every test double or harness: where is it kinder than production? Return the dimension score, the ordered must-fix list, one paragraph of reasoning in plain language, and the model name stated in your system prompt.
```

**`drive-verifier.md`**

```yaml
---
name: drive-verifier
description: Independently verifies one implemented slice against its behavioral claim by running the tests and reading the diff. Never sees the maker's reasoning.
model: opus
effort: high
tools: Read, Grep, Glob, Bash
maxTurns: 40
color: red
---
You verify a claim, not a summary. You receive the claim, the spec excerpt, the diff, and the test command. Your first action is to run the tests and quote the output. Then read the diff and the tests and try to refute the claim: find an input, state, or ordering the tests do not cover and check it. Where the tests use a stub, fake, or in-memory substitute, state what the real system would do differently and whether the tests would still pass against it. Do not edit code. Return pass or fail, the evidence for each, the gaps you found ordered by severity, and the model name stated in your system prompt. If you cannot run the tests, return fail with the reason; never infer a pass.
```

**`drive-implementer.md`** (standard) and **`drive-implementer-hard.md`** (identical prompt, `model: opus`, `effort: xhigh`)

```yaml
---
name: drive-implementer
description: Implements one slice with one behavioral claim in an isolated worktree, test-first, with no extras.
model: sonnet
effort: high
isolation: worktree
tools: Read, Grep, Glob, Bash, Edit, Write
maxTurns: 80
color: blue
---
You implement exactly one slice. The brief names the behavioral claim, the spec excerpt, the files in scope, and the test command. Write or update the test that would refute the claim before the implementation, run it red, implement, run it green, run the full suite. If, while working, you find a pre-existing bug, a performance concern, or behavior the task doesn't mention, don't fix or extend it unless the requested behavior cannot work without it; report it as a follow-up. Commit tests only where the task asks or the repository already keeps tests for this kind of change, sized like the neighboring tests; don't turn scratch checks into permanent files. Commit in the worktree with a plain message. Return the claim, the commit hash, the test command and its final output, follow-ups, and the model name stated in your system prompt. You are operating autonomously; nobody will answer a question mid-task, so decide and state the assumption.
```

**`drive-security-reviewer.md`**

```yaml
---
name: drive-security-reviewer
description: Reviews a change or system for security weaknesses and returns a sanitized report. Runs on Opus so classifier fallback stays inside this agent.
model: opus
effort: xhigh
tools: Read, Grep, Glob, Bash
skills: security-review
maxTurns: 40
color: orange
---
Review the code in scope for security weaknesses: authentication and authorization boundaries, input handling at system edges, secrets, storage, network exposure, dependency risk. Ask "are there bugs in this code" rather than whether it compiles. Describe each weakness as a class, its location, its severity, and the fix. Never include attack strings, proof-of-concept exploit code, or encoded payloads in your report; describe, don't reproduce. Strip base64 and binary from any tool output before reasoning about it. Return the ordered findings and the model name stated in your system prompt. If your own request is declined, return a report saying so and stop.
```

**`drive-ui-reviewer.md`**

```yaml
---
name: drive-ui-reviewer
description: Verifies a screen or page against the spec and design tokens by driving it live (simulator or browser), reading the accessibility tree, and inspecting screenshots.
model: opus
effort: high
tools: Read, Grep, Glob, Bash
maxTurns: 40
color: pink
---
You verify UI against a spec, not against taste alone. Drive the screen or page yourself with the provided tool (iOS Simulator MCP or Playwright/Chrome DevTools MCP): read the accessibility tree first, then take screenshots of each state the spec names (empty, loading, error, populated, and the smallest and largest viewport). Crop or zoom when a detail is small. Compare against the spec text, the design tokens file, and the previous screenshots referenced in STATE. Report each mismatch with the state, the element, what the spec says, what you observed, and a severity. Keep every screenshot in the run's evidence directory and return paths, not images. Include the model name stated in your system prompt.
```

**`drive-distiller.md`**

```yaml
---
name: drive-distiller
description: Distills a run's failures and verifications into general lessons and writes them into the skill's lessons file. Runs once at the end of a run.
model: fable
effort: high
tools: Read, Grep, Glob, Edit, Write
maxTurns: 30
color: yellow
---
Read STATE.md, the failure log, and the verifier and judge verdicts for this run. For each failure, write the chain: what failed, why (as verified, not guessed), the general rule that would have prevented it, and where in the skill that rule belongs. A rule must apply beyond this repository; a fix that only works here is a note for the project's STATE, not a lesson. Store one lesson per entry with a one-line summary, record confirmed approaches as well as corrections, don't save what the repo or the run already records, update an existing lesson rather than duplicating it, and delete lessons the evidence now contradicts. Return the list of lessons written and the model name stated in your system prompt.
```

**`drive-auditor.md`**

```yaml
---
name: drive-auditor
description: Final independent audit of a completed run against the status ladder. Never the orchestrator. Decides whether the run is done.
model: fable
effort: xhigh
tools: Read, Grep, Glob, Bash
maxTurns: 60
color: cyan
---
You decide whether this run is complete, and you assume it is not. Ground truth in this order: working-tree code and tests, then proof artifacts, then STATUS files, then prose. For every row in STATUS claiming Local Proof or above, find the artifact and re-run the check; for every Live Proof, find evidence from the real system, not a local harness. Ask of every shim where it is kinder than production. Confirm no branches or worktrees remain (`git worktree list`, `git branch`). Compare the model each agent reported against the routing table and flag any role that ran below its tier. Write the audited status-ladder entry and a plain-language verdict. Do not fix anything.
```

Remaining roles, compactly: `drive-survey` (sonnet, low, read-only, `maxTurns: 20`); `drive-researcher` (sonnet, medium, WebSearch/WebFetch/Read, returns URL + verbatim quote + one-line relevance); `drive-synthesizer` (opus, high, Read only); `drive-spec-writer` (opus, xhigh; orchestrator overrides to `fable` on greenfield and migration); `drive-architect` (opus, xhigh, read-only plus Write for the design doc); `drive-test-author` (sonnet, high, worktree, reads claim and spec only); `drive-severe-tester` (opus, xhigh, `skills: severe-testing`, worktree, sanitized report); `drive-investigator` (opus, xhigh, read-only plus Bash, hypothesis-driven, `maxTurns: 120`); `drive-docs-writer` (sonnet, medium, `skills: writing, google-dev-docs-style`). The `simplify` skill is invoked by the orchestrator rather than wrapped in an agent.

---

## 7. Failure modes and anti-patterns, including mirage completion

**A grader on the wrong tier passes garbage.** A Sonnet-low grader asked "is this architecture sound" answers from the prose and says yes. Prevention: the grader's brief is a list of binary assertions, and the skill's rubric files name which tier each artifact kind requires; the orchestrator may not downgrade a tier-2 artifact to tier 1.

**The verifier reads the summary instead of running the tests.** The single most common mirage. Prevention: the verifier's first action is mandated (run tests, quote output); a result without quoted command output fails tier-1 validation automatically.

**The orchestrator declares done.** Self-critique by another name. Prevention: only `drive-auditor` writes the status-ladder entry; the orchestrator's final message reports the auditor's verdict, never its own.

**Silent demotion after a classifier flag.** The auditor "on Fable" was actually Opus 4.8 after a first-request flag; or an implementer's subagent moved mid-slice. Prevention: model line in every result header; the auditor checks it; optional `PreModelSwitch` hook log.

**Effort inherited as medium.** The owner's saved Fable 5.1 level is medium; an orchestrator that inherits it plans shallowly on a greenfield run. Prevention: skill frontmatter `effort`, and `${CLAUDE_EFFORT}` recorded in STATE at intake.

**Cold-cache tax.** Not a mirage but a run killer at $10/MTok per cold re-read. Prevention: `promptCacheTtl: 1h`; orchestrator context lean.

**Verifier loops without a cap.** A slice that Sonnet cannot finish is retried until the budget dies. Prevention: two rounds, one escalation, then an open failure in STATE.

**Literal narrowing at low effort.** A Sonnet implementer at low or medium implements the sentence, not the requirement. Prevention: implementers at high; slices name a behavioral claim and the verifier checks the claim, not the code.

**Tests kinder than production.** The bind-variable incident. Prevention: the architecture reviewer, verifier, severe tester, and auditor each carry the shim question verbatim; Live Proof requires evidence from the real system, which no local grader can grant.

**Screenshots and payloads in the orchestrator.** Cache churn and classifier exposure respectively. Prevention: reviewers return paths and sanitized descriptions; the orchestrator's tool list excludes the browser and simulator MCPs during a `/drive` turn.

---

## 8. Open questions and trade-offs

1. **Does a classifier fallback inside a subagent move only that subagent, or the parent session too?** The docs say "the session continues on the fallback model" and, for the separate availability-fallback chain, that a subagent's failover leaves "your session's model unchanged." I could not confirm the same isolation for classifier fallback. Recommendation: design for the worst case (rules 1 to 6 in §4.5), log switches with a `PreModelSwitch` hook, and test once with a deliberately cyber-flavored subagent prompt in a throwaway session.
2. **No effort parameter on the Agent tool.** Until one ships, one agent file per (role, effort) pair. The Workflow tool has per-call effort today, which argues for using workflows for the fan-out phases even outside ultracode; that trades the model-driven flexibility of the Agent tool for deterministic control flow and per-call effort. Recommendation: Agent tool for the sequential spine, workflows for implementation and verification fan-outs when the owner has opted in.
3. **`opus` alias versus pinned `claude-opus-4-8` for security roles.** Opus 5 is stronger and has a later cutoff; a cyber flag costs one small cache rebuild and continues on 4.8. Recommendation: start with the alias, pin only if `/usage` or the model lines show repeated switches for the role.
4. **Fable at low effort as a tier-1 grader instead of Sonnet at low.** The Fable 5.1 guide claims low effort is "often competitive with Claude Opus and Claude Sonnet models on cost per task while scoring higher." Grading is input-dominated, and Fable's input is 5× Sonnet's, so the claim probably does not hold for graders. Recommendation: keep Sonnet; run a 20-case eval of false "met" verdicts once, and revisit.
5. **Fable versus Opus for architecture review on the feature shape.** Absolute premium under a dollar per review. Recommendation: default Opus; if the auditor overturns architecture reviews on two runs in a row, promote the role.
6. **One-hour cache TTL on Fable.** Writes at $20 versus $12.50 per million on new content. Worth it whenever the orchestrator idles more than five minutes between requests, which is every wait on a real subagent. Recommendation: set it; confirm with the `Prompt cache (main)` line in `/usage` after a run.
7. **Overriding the built-in Explore to Sonnet low.** Affects every session, not just `/drive`. Owner's call.
8. **Sonnet implementers at high versus xhigh.** The docs recommend xhigh for "the hardest coding" on Sonnet 5, and the measured re-run-failures pattern favors starting lower. Recommendation: high, with the two-failure escalation to Opus xhigh; measure the escalation rate over the first ten runs.
9. **Subagent cache TTL.** Long-running implementers and verifiers that wait on test suites longer than five minutes lose their cache. `experimental.cacheTtl: 1h` on those two agent files is cheap insurance; confirm the 2× write rate is worth it from `/usage` attribution.

---

## 9. Skill text candidates

Each passage is ready to lift into `SKILL.md` or `references/routing.md`. Imperative voice, plain language.

**Routing principle.** Route by the shape of the work. Volume that produces many output tokens (implementation, tests, docs, breadth research) runs on Sonnet. Bounded judgment (architecture, review, verification, security) runs on Opus at high or xhigh. Fable holds the orchestrator context and takes three one-shot roles: spec and architecture review on greenfield and migration runs, lesson distillation, and the final audit. Write aliases (`fable`, `opus`, `sonnet`), never version numbers; the one pinned ID is `claude-opus-4-8`, used only as a cyber fallback.

**Where routing lives.** Model and effort for every role live in the agent files under `agents/`. Do not name a model anywhere else except the override table in `references/routing.md`. To change the policy, edit one agent file; it reloads within seconds.

**Overrides the orchestrator may apply.** On greenfield and migration runs, pass `model: fable` when launching the spec writer and the architecture reviewer. On greenfield and website runs, launch one Fable design judge at the end. Apply no other model overrides.

**Effort is explicit.** Every agent file sets `effort`. The `/drive` turn runs at the effort in the skill's frontmatter, not the session's saved level. At intake, write `${CLAUDE_EFFORT}` into STATE.md so the audit can see what the orchestrator actually ran at.

**The orchestrator delegates everything.** During a `/drive` turn, read only STATE.md and subagent results, write only STATE.md, and run only the tier-0 check scripts. Never read source files, test output, screenshots, or web pages inline. Every subagent returns a structured result of at most 300 words plus file paths.

**Escalation replaces difficulty guessing.** Start every slice on the standard implementer. If the verifier fails it twice, re-run the slice once on the hard implementer with the verifier's findings. If that fails, record an open failure in STATE and continue. Never retry a slice a fourth time.

**Graders are strangers.** Launch every grader, verifier, reviewer, and judge as a fresh subagent that receives artifacts and a rubric, never a transcript or a summary of reasoning. Do not resume a maker as its own reviewer. Do not use forks for grading.

**Two tiers of grading.** Use the checklist grader (Sonnet, low) for binary assertions with evidence: tests passed, files exist, citations resolve, status rows point at proof. Use the judgment grader (Opus, high) for quality: architecture, specs, UI, root cause, simplification value. Use the auditor (Fable, xhigh) once, at the end, and for tie-breaks. Before any model grades, run the deterministic checks and put their output in the transcript.

**Grader prompts ask for coverage.** Tell graders to report every issue, including uncertain and low-severity ones, each with a confidence, and to say unknown when the evidence is missing. Never tell a grader to be conservative or to report only important issues; filter in a later step.

**Verifiers run before they read.** A verifier's first action is to run the tests and quote the output. A verification result without quoted command output is invalid. A verifier that cannot run the tests returns fail with the reason.

**The shim question.** Every architecture reviewer, verifier, severe tester, and auditor asks of each stub, fake, mock, or in-memory substitute: where is it kinder than production, and would the tests still pass against the real thing? A harness kinder than production certifies broken code.

**Classifier exposure stays in Opus subagents.** Run the security reviewer and severe tester on Opus. Never analyze exploitability, paste attack strings, or carry encoded blobs in the orchestrator's context. Exposed roles describe weaknesses; they never reproduce attacks. If a subagent's result is abruptly short, cites no evidence, and reads like a decline, re-run it once on `claude-opus-4-8`, record the category in STATE, and do not retry again.

**Every result names its model.** Every subagent ends its result with the model name stated in its system prompt. The auditor compares each against the routing table and flags any role that ran below its tier.

**Cache discipline.** Hold the orchestrator's model and effort constant for the whole run. Compact only at phase boundaries, with a preserve list: STATE path, open failures, routing decisions. Keep screenshots and large tool output in subagents. Set `promptCacheTtl` to `1h` when billing by API key.

**Cost envelopes.** Estimate before starting and record in STATE: bug hunt $15 to $40, feature $60 to $150, migration $100 to $300, greenfield $400 to $600. Start headless runs with `--max-budget-usd`. Cap verifier rounds at two per slice. When a phase exceeds twice its estimate, stop, record why, and continue only if the remaining envelope covers the rest.

**Install checks.** Before the first run, confirm `CLAUDE_CODE_GOAL_GRADER_MODEL` is set (otherwise `/goal` grades on Haiku), confirm the `agents/` symlink is scanned (launch a session and list agents), and confirm `switchModelsOnFlag` is not `false`.
