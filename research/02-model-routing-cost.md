# R02 — Model routing, effort levels and cost control

Lane report for the mission skill. Component: post steps 04 (cost-capability matrix), 14 (classifier fallback) and the
"Fable on tasks Sonnet would handle" mistake.

## 1. Executive summary & strong opinions

The post's routing matrix (step 04) has the right *shape* — top tier orchestrates, mid tier takes hard bounded work,
cheap tier does volume, an independent grader checks — but its *numbers* are stale or wrong, and it says nothing about
effort levels, which in 2026 are as important a cost dial as the model choice. Three facts change the design:

- **Fable 5.1 costs 2× Opus 4.8 per fresh token, not ~5×**, and its cache reads ($0.25/MTok) are *half* the price of
  Opus 4.8's ($0.50) (https://platform.claude.com/docs/en/about-claude/pricing). For a long-lived orchestrator whose
  turns are mostly cache reads, Fable 5.1 costs roughly the same per turn as Opus 4.8. Fable is expensive when it
  *writes* a lot or *re-reads cold context*, not when it sits on a warm cache and delegates.
- **The `opus` and `sonnet` aliases no longer mean Opus 4.8 and Sonnet 4.6.** On the Anthropic API they resolve to Opus 5
  and Sonnet 5 (https://code.claude.com/docs/en/model-config). The user's constraint is therefore only honoured by
  **full model IDs**: `claude-fable-5-1`, `claude-opus-4-8`, `claude-sonnet-4-6`.
- **Effort cannot be set per Agent/Task invocation in Claude Code.** Effort is a frontmatter-only field on the agent
  definition; the per-invocation knobs are `model` and `isolation` (https://github.com/anthropics/claude-code/issues/72596,
  closed as not planned). The skill must ship **one agent file per (role, effort) pair it actually uses**.

Strong opinions (each is actionable):

1. **Pin models by full ID everywhere** — agent frontmatter, `--model`, workflow scripts. Never use `opus`/`sonnet`
   aliases in the skill. Log the resolved model of every spawn in the budget ledger.
2. **Default worker = `claude-sonnet-4-6` at `medium`.** Low is for mechanical, oracle-checked work (classify, lint-fix,
   grep-and-summarise, format a rubric verdict). High is for Sonnet work where the only check is another model.
3. **Opus 4.8 is the escalation and adversary tier, not a default tier.** Use it for: the second attempt after a Sonnet
   worker fails its gate twice; adversarial and security review of Sonnet-made changes; architecture review; and the
   explicit cyber fallback when Fable's classifier flags a request.
4. **Fable 5.1 is used for three things only**: the mission orchestrator (long-lived, cache-warm, delegating), the
   one-shot planner/spec author on L/XL missions, and root-cause investigation of a bug that has already defeated an
   Opus 4.8 attempt. Everything else on Fable is waste by default.
5. **The grader must differ from the maker in model or effort, and must differ in model when the maker is the cheap
   tier.** A Sonnet 4.6 maker is graded by Opus 4.8 or by deterministic checks; Sonnet low grading Sonnet low is not a
   check. "Different context window" is necessary but not sufficient.
6. **Code-based oracles beat model graders on cost and trust; model graders only judge what code cannot.** A failing test
   is a $0 verdict. Spend model-grader tokens on spec fit, design quality and review — never on "did the tests pass".
7. **Guard every downgrade with a sampled audit**: re-run ≥10% of accepted cheap-tier outputs (minimum 1 per phase)
   through an Opus 4.8 high auditor. Two audit disagreements in a phase → promote that role one tier for the rest of the
   mission and log a lesson.
8. **Escalation ladder is fixed and logged**: Sonnet 4.6 (medium) → Sonnet 4.6 (high, fresh context, failure notes) →
   Opus 4.8 (high) → Fable 5.1 (high) or human. No step is skipped silently, no step is repeated a third time.
9. **Classifier fallback is an event, not an error.** On a Fable refusal/fallback, record it, re-issue security-flavoured
   work to `claude-opus-4-8` explicitly, and re-assert the orchestrator's model at the next phase boundary; in Claude
   Code the switch is sticky for the session (issue #74311, verified by sibling lane 01).
10. **Escalate by spawning, never by `/model`-switching the orchestrator.** Each model and (on most models) each effort
    level has its own prompt cache; switching mid-session re-reads the whole history uncached
    (https://code.claude.com/docs/en/prompt-caching). A subagent builds its own cache and leaves the parent's intact.
11. **Structure every brief cache-first**: stable skill text and project context first, the variable task last; keep
    agent definitions and tool sets stable across a phase; do not toggle MCP servers or plugins mid-mission.
12. **Every mission has a budget ledger with a soft cap and a hard cap**, set from scope (S/M/L/XL), enforced with
    `--max-budget-usd` in headless runs where available (https://code.claude.com/docs/en/costs), and reviewed at each
    phase boundary. A hit soft cap is a *pause and re-plan*, not a failure (mirrors arcwell's "A budget ceiling is a
    WAIT, not a verdict", arcwell/docs/handoff/2026-08-21-remediation-status.md:168).
13. **Fan-out needs a value case.** Multi-agent systems use ~15× the tokens of chat
    (https://www.anthropic.com/engineering/multi-agent-research-system). Fan out for breadth (research, independent
    files, independent reviewers); run sequentially when pieces share state.
14. **Stop when marginal value drops**: two consecutive iterations with no new gate passing and no new verified finding
    ends a loop, regardless of remaining budget.
15. **Never set `max` effort in the skill by default.** Use `xhigh` only for Fable 5.1/Opus 4.8 on long asynchronous runs
    (Anthropic recommends "extra"/xhigh "for difficult tasks and long-running asynchronous workflows",
    https://www.anthropic.com/news/claude-opus-4-8); Sonnet 4.6 has no `xhigh` level at all
    (https://platform.claude.com/docs/en/build-with-claude/effort).

## 2. Claim check

Legend: **V** verified (source), **P** plausible but unverified, **H** likely hype / wrong.

| # | Post claim (my area) | Verdict | Evidence | What the skill does |
|---|---|---|---|---|
| 01a | Fable priced $10 in / $50 out | **V** | Pricing table lists Fable 5 and Fable 5.1 at $10/$50 (https://platform.claude.com/docs/en/about-claude/pricing); launch post same (https://www.anthropic.com/news/claude-fable-5-mythos-5) | Use in the ledger's price table. |
| 01b | "existing 90% input token discount for prompt caching" | **V for Fable 5, outdated for 5.1** | Fable 5 cache hit $1 (0.1×); Fable 5.1 cache hit $0.25, footnote "0.025x the base input price" (pricing page); 5.1 "25% less than Fable 5 for typical workloads ... up to approximately 45%" for agentic work (https://www.anthropic.com/claude-fable-and-mythos-5-1) | Price table uses 5.1 figures; cache discipline matters even more for Fable 5.1. |
| 01c | "This is not a subscription model" | **H (for 5.1)** | "Claude Fable 5.1 is available to Pro, Max, Team, and Enterprise users" (https://www.anthropic.com/claude/fable) | Ledger must handle two regimes: API dollars vs plan-limit consumption. |
| 04a | "Fable 5 costs ~5× what Opus 4.8 does per token" | **H** | $10/$50 vs $5/$25 = 2× on fresh input and output; cache reads $0.25 vs $0.50 = 0.5× (pricing page) | Route on capability and write volume, not a mythical 5× multiplier. |
| 04b | Fable for the heavy-lift orchestrator | **V (consistent with docs)** | Models overview: Fable 5.1 "for demanding reasoning and long-horizon agentic work, or when your evals on Claude Opus 5 at higher effort still fall short" (https://platform.claude.com/docs/en/about-claude/models/overview); Claude Code: "suited to tasks larger than a single sitting" (https://code.claude.com/docs/en/model-config) | Orchestrator on `claude-fable-5-1` for M+ missions, with an Opus 4.8 fallback profile. |
| 04c | Opus 4.8 for architecture decisions, complex debugging, deep code reviews | **P, partially contradicted** | Claude Code docs name "root-cause investigations, outage debugging, and architecture decisions" as where *Fable* pays off (model-config). Opus 4.8 is "around four times less likely than its predecessor to allow flaws in code it has written to pass unremarked" (https://www.anthropic.com/news/claude-opus-4-8) | Opus 4.8 for bounded reviews and second attempts; Fable only after Opus fails on a deep bug. |
| 04d | Sonnet 4.6 for high-volume worker tasks | **V (pattern)** | Anthropic's research system used Opus lead + Sonnet subagents and beat single-agent Opus by 90.2% (https://www.anthropic.com/engineering/multi-agent-research-system); effort doc lists `low` for "Simpler tasks ... such as subagents" (https://platform.claude.com/docs/en/build-with-claude/effort); Sonnet 4.6 "approaches Opus-level intelligence" (https://www.anthropic.com/news/claude-sonnet-4-6) | Default worker tier. |
| 04e | Haiku 4.5 for graders and cheap classifiers | **V as practice, overridden by user** | Claude Code docs still say "Control costs by routing tasks to faster, cheaper models like Haiku" (https://code.claude.com/docs/en/sub-agents) | Replace with `claude-sonnet-4-6` at `low`; see §5 for why a *grader* is not always low. |
| 04f | Opus 4.8 is the fallback for classifier blocks | **V with nuance** | Fable 5 launch: flagged queries "receive a response from ... Claude Opus 4.8"; Fable 5.1 benchmarks: "cybersecurity tasks were completed by Claude Opus 4.8, and biology tasks were completed by Claude Opus 5" (https://www.anthropic.com/claude-fable-and-mythos-5-1); "You won't be charged Fable prices for rerouted requests" (https://www.anthropic.com/claude/fable) | Explicit Opus 4.8 re-issue for cyber; biology work may land on Opus 5 automatically — log the actual model. |
| 14a | Classifiers cover "cyber, bio, chem, distillation" | **Partly V** | API categories are cyber, bio, frontier_llm, reasoning_extraction, general_harms (sibling lane 01, research/mission-skill/01-orchestration-control.md:971, citing https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback); 5.1 cyber false positives down 60% and vulnerability *discovery* allowed, exploit development not (https://www.anthropic.com/claude-fable-and-mythos-5-1) | Pre-route exploit/pentest logic to Opus 4.8; keep ordinary security review on the normal matrix. |
| 14b | Fallback happens "automatically" | **V in Claude Code; sticky** | Claude Code: flagged requests "trigger automatic model fallback" (model-config); session stays on the fallback model until `/model` (issue #74311 per lane 01:1002) | Detect and re-assert at phase boundaries. |
| M5 | "Fable 5 on tasks Sonnet 4.6 would handle" is a mistake | **V (by arithmetic)** | Per fresh token Fable 5.1 is 3.3× Sonnet 4.6 input/output list price; plus Claude 4.7+ tokenizer "approximately 30% more tokens for the same text" while Sonnet 4.6 uses the previous tokenizer (pricing page) → ≈4.3× for the same text (inference from list prices) | Hard rule: doc updates, lint fixes, simple refactors, test scaffolding never run on Fable. |
| M10 | Retention "30-day / 2-year terms" | **Half V** | "Using Fable requires 30-day data retention for safety monitoring by default" (https://www.anthropic.com/claude/fable). 2-year figure not found. | Flag retention for sensitive missions; don't cite 2 years. |
| 07 | Dynamic workflows shipped May 28 2026; classify-and-act routing | **V date / P pattern** | Opus 4.8 launch post announces dynamic workflows research preview the same day (https://www.anthropic.com/news/claude-opus-4-8); workflow `agent()` supports per-call `opts.effort` (issue #72596) | When workflows are available, route per call with model + effort; otherwise use the agent-file matrix. |

## 3. Deep findings

### 3.1 The lineup the skill is actually running in

The current Anthropic lineup is Fable 5.1, Opus 5, Sonnet 5 and Haiku 4.5; the models overview even says "start with
Claude Opus 5 for most workloads" (https://platform.claude.com/docs/en/about-claude/models/overview). The user's chosen
models are still **Active** — `claude-opus-4-8` retires "not sooner than May 28, 2027", `claude-sonnet-4-6` "not sooner
than February 17, 2027", `claude-fable-5-1` "not sooner than September 1, 2027"
(https://platform.claude.com/docs/en/about-claude/model-deprecations). So the constraint is workable for at least the
next six months, but the skill must (a) pin by full ID, and (b) keep model IDs in **one** table (a references file)
so a later swap to Opus 5 / Sonnet 5 is a one-line change. I am honouring the user's constraint; §9 flags that Sonnet 5
at $2/$10 is *cheaper* than Sonnet 4.6 at $3/$15 (pricing page), which the synthesizer should surface to the user.

### 3.2 Prices and the real shape of agent cost

List prices per million tokens (https://platform.claude.com/docs/en/about-claude/pricing):

| Model | Input | 5m cache write | 1h cache write | Cache read | Output |
|---|---|---|---|---|---|
| `claude-fable-5-1` | $10.00 | $12.50 | $20.00 | $0.25 | $50.00 |
| `claude-opus-4-8` | $5.00 | $6.25 | $10.00 | $0.50 | $25.00 |
| `claude-sonnet-4-6` | $3.00 | $3.75 | $6.00 | $0.30 | $15.00 |

Two modifiers matter. First, "Claude 4.7 and later models ... use a newer tokenizer ... approximately 30% more tokens for
the same text ... Claude Sonnet 4.6 and earlier models use the previous tokenizer" (pricing page). Opus 4.8 is on the
new tokenizer; I infer Fable 5.1 is too ("later models"). So for identical text, Opus 4.8 is ≈2.2× Sonnet 4.6 and Fable
5.1 ≈4.3× on fresh tokens. Second, US-only inference is 1.1× (https://www.anthropic.com/claude/fable), and Claude Code
applies the 1.1× in its session estimate since v2.1.239 (https://code.claude.com/docs/en/costs).

Agent cost is **dominated by cache reads and output**, not fresh input. Claude Code's own `/usage` example shows a
Sonnet 4.6 session at "1.2k input, 5.3k output, 940.0k cache read, 50.0k cache write ($0.55)"
(https://code.claude.com/docs/en/costs). That shape changes the routing arithmetic. Worked examples (my calculations
from list prices; not measured):

- **Orchestrator turn**, 200k tokens of warm context, 2k new input, 1.5k output.
  Fable 5.1: 200k×$0.25 + 2k×$10 + 1.5k×$50 ≈ $0.05 + $0.02 + $0.075 = **$0.145**.
  Opus 4.8: 200k×$0.50 + 2k×$5 + 1.5k×$25 ≈ $0.10 + $0.01 + $0.0375 = **$0.148**.
  Sonnet 4.6 (≈154k tokens for the same text): ≈ $0.046 + $0.005 + $0.017 = **≈$0.07**.
  → On a warm cache, Fable 5.1 orchestrating costs about what Opus 4.8 does. The first cold write of that 200k context,
  however, costs $2.50 on Fable vs $1.25 on Opus — **cache misses are where Fable gets expensive**.
- **Implementation worker**, 30 turns, average 40k context (Sonnet-tokenizer count), ~60k tokens of new content written
  to cache, 15k output. Sonnet 4.6 ≈ $0.36 + $0.23 + $0.23 = **≈$0.81**. Opus 4.8 (×1.3 tokens) ≈ $0.78 + $0.49 +
  $0.49 = **≈$1.76**. Fable 5.1 ≈ $0.39 + $0.98 + $0.98 = **≈$2.34**.
  → For workers that read many files and write code, Sonnet 4.6 is ≈2.2× cheaper than Opus 4.8 and ≈2.9× cheaper than
  Fable 5.1. That is the saving the matrix should chase.

Customer claims point the same way but are not independent evidence: Cognition moved Opus 5 code-review traffic to Fable
5.1 because "with the new cache read pricing a Fable-class model is finally economical", and Every reported Fable 5.1
"used half as many tokens" as Opus 5 (https://www.anthropic.com/claude/fable). Anthropic also states Fable 5.1 at
Low/Medium effort "achieves results similar to or better than Fable 5's at a much lower cost"
(https://www.anthropic.com/claude-fable-and-mythos-5-1). **Label: vendor/customer-reported.** The skill must measure its
own cost per accepted task rather than trust these.

Batch API requests are 50% off (models overview), but Claude Code sessions do not use the Batch API; only offline
audits run through a separate API script could benefit. The skill should not depend on it.

### 3.3 What effort actually changes

The API effort parameter (`output_config.effort`) is supported on `claude-fable-5-1`, `claude-opus-4-8` and
`claude-sonnet-4-6` (https://platform.claude.com/docs/en/build-with-claude/effort). Verified behaviour:

- Default is `high`: "Setting effort to high produces exactly the same behavior as omitting the effort parameter".
- It "affects all tokens in the response, including: Text responses ... Tool calls and function arguments ... Thinking"
  and "Lower effort also means fewer and terser tool calls".
- Levels: `low` ("Simpler tasks that need the best speed and lowest costs, such as subagents"), `medium` ("Agentic tasks
  that require a balance of speed, cost, and performance"), `high` ("Complex reasoning, difficult coding problems, agentic
  tasks"), `xhigh` ("Long-running agentic and coding tasks (over 30 minutes) with token budgets in the millions" — Fable
  5.1 and Opus 4.8, **not** Sonnet 4.6), `max` (all three).
- "Effort is a behavioral signal, not a strict token budget." It is not a cap; the ledger must still measure.

Fable 5.1 thinking is "Adaptive (always on)" (models overview), and Fable 5.1 "defaults to High effort in Claude Code,
and to Medium in Claude Cowork and on Claude.ai" (https://www.anthropic.com/claude-fable-and-mythos-5-1). For Opus 4.8
Anthropic says high is "the best overall balance" and recommends "extra" (`xhigh` in Claude Code) "for difficult tasks and
long-running asynchronous workflows" (https://www.anthropic.com/news/claude-opus-4-8).

Practitioner evidence (secondary, https://github.com/tmozii1/Claude-Code-Everything/blob/main/docs/reference/effort-levels.md):
low skips thinking on simple problems and reads minimally; medium "thinks when warranted"; high reads related files
unprompted. The plan-high / execute-low pattern "fails when the plan has gaps — Sonnet at low effort won't catch
ambiguity it inherits". The same source claims the `ultrathink` keyword does not change API effort. I treat both as
plausible, not verified. Consequence for roles: **effort buys exploration and self-checking**. Roles whose value is
noticing what was not asked (reviewers, debuggers, planners) benefit from high; roles whose output is pinned by an
oracle or a precise brief (formatters, classifiers, test runners, doc updaters) do not.

### 3.4 How model and effort are expressed in Claude Code

- **Session model**: `/model <alias|id>` or `claude --model <alias|id>`; the `model` setting accepts an alias or "a full
  model name" (https://code.claude.com/docs/en/model-config). Aliases: `default`, `best`, `fable`, `sonnet`, `opus`,
  `haiku`, `sonnet[1m]`, `opus[1m]`, `opusplan`. On the Anthropic API `opus` → Opus 5 and `sonnet` → Sonnet 5; on Claude
  Platform on AWS `sonnet` → Sonnet 4.6; on Bedrock/Google `sonnet` → Sonnet 4.5. "To pin to a specific version, use the
  full model name ... or set ... `ANTHROPIC_DEFAULT_OPUS_MODEL`" (same page). Opus 4.8 requires Claude Code v2.1.154+,
  Fable 5.1 v2.1.257+. "Neither Fable model is the account-type default on any plan or provider. Select one explicitly."
  The picker lists Fable only once the server reports availability, but a typed `/model fable` checks directly.
- **Subagent model**: frontmatter `model:` in `.claude/agents/<name>.md` accepts an alias, a full model ID, or `inherit`;
  omitted means inherit (secondary, https://backgrind.com/blog/claude-code-subagent-models/; consistent with the official
  statement that the `model` setting accepts full names). The Agent/Task tool can pass `model` per invocation.
- **Subagent effort**: frontmatter `effort: low|medium|high|xhigh|max` (since ~v2.1.196); **no per-invocation effort**.
  The feature request was "Closed as not planned"; the only workaround is "duplicating agent definitions per effort
  level" (https://github.com/anthropics/claude-code/issues/72596). The dynamic-workflow `agent()` API does accept
  `opts.effort` (same issue).
- **Session effort**: `/effort <level>` and `claude --effort <level>` are reported by community sources
  (https://joaothallis.com/posts/how-to-set-claude-code-effort-level-to-max/); I could not fetch the exact official
  section because the model-config page was truncated by the fetch tool — **label: plausible, verify in the harness**.
- **Global override hazard**: `CLAUDE_CODE_SUBAGENT_MODEL` sets the model for subagents; the official page says it applies
  when "nothing assigns a model another way" unless you "force it onto every subagent"
  (https://code.claude.com/docs/en/sub-agents). A secondary source claims it wins over frontmatter (backgrind). Either
  way the skill's preflight must check it is unset.
- **Silent allowlist trap** (secondary, backgrind): a model excluded by the org's `availableModels` allowlist is
  "skipped with no error and the subagent runs on the inherited model". A Sonnet worker silently becomes a Fable worker
  if the orchestrator runs on Fable. Preflight must spawn one probe agent per model ID and confirm the model reported.
- **Built-in Explore** now "inherits from the main conversation, capped at Opus on the Claude API"
  (https://code.claude.com/docs/en/sub-agents). With a Fable orchestrator, built-in exploration therefore runs on an Opus
  model (inference: most likely Opus 5, since `opus` resolves to Opus 5 on the API), not Sonnet 4.6. A project subagent
  named `Explore` "overrides the built-in and keeps its own `model` field" (same
  page) — the skill should ship one pinned to `claude-sonnet-4-6`.
- **Budget and cost surfaces**: `/usage` session cost is "computed locally from token counts at list price" and is an
  estimate; the status line cost field "compares it with `--max-budget-usd`"; the "Prompt cache (main)" line reports
  hit share and misses but "covers the main conversation only, not subagents" (https://code.claude.com/docs/en/costs).
  Headless `--output-format json` includes `total_cost_usd` with a per-model breakdown (sibling lane 01,
  research/mission-skill/01-orchestration-control.md:994).
- **Fan-out ceilings** (secondary, backgrind): 200 subagents per session, 20 concurrent, nesting depth three.

### 3.5 Classifier fallback mechanics

Fable 5 launched with safeguards so that "queries on some topics will instead receive a response from our
next-most-capable model, Claude Opus 4.8", tuned "conservatively" and triggering "in less than 5% of sessions"
(https://www.anthropic.com/news/claude-fable-5-mythos-5). Fable 5.1's cyber safeguards "block 60% fewer false positives",
and the model "can now be used to discover software vulnerabilities—though not to develop exploits for them"
(https://www.anthropic.com/claude-fable-and-mythos-5-1). In benchmark interventions "cybersecurity tasks were completed
by Claude Opus 4.8, and biology tasks were completed by Claude Opus 5" (same page). "You won't be charged Fable prices for
rerouted requests" (https://www.anthropic.com/claude/fable). In Claude Code, flagged requests "trigger automatic model
fallback" (https://code.claude.com/docs/en/model-config). Sibling lane 01 verified that the fallback is **sticky for the
session**, that `fallbackModel`/`--fallback-model` fires only on availability errors, and that a related issue reports the
effort level carrying over unchanged (research/mission-skill/01-orchestration-control.md:1002). On the raw API a refusal
is `stop_reason: "refusal"` with a category, and server-side fallback is an opt-in beta (lane 01:971).

Design consequences: (1) the orchestrator's model can change under it without an error; (2) a subagent spawned with an
explicit `model: claude-sonnet-4-6` is unaffected by Fable's classifier because it never calls Fable; (3) exploit or
pentest work should be *pre-routed* to Opus 4.8 so the loop never depends on a sticky fallback.

### 3.6 Prompt caching in a multi-agent mission

The API caches exact prefixes in the order `tools`, `system`, `messages`; default TTL 5 minutes, "refreshed for no
additional cost each time the cached content is used", with a paid 1-hour option; the TTL is measured "from the start of
the request", so a long streaming response eats into it (https://platform.claude.com/docs/en/build-with-claude/prompt-caching).
Claude Code orders requests as system prompt + tool definitions → project context (CLAUDE.md, memory, rules) →
conversation, and "a change anywhere in the prefix recomputes everything after it" (https://code.claude.com/docs/en/prompt-caching).
Verified invalidators: switching models, changing effort (except Fable 5.1 on API key/subscription), fast mode, MCP
connect/disconnect, plugin toggles, denying a tool, compaction, many images, upgrading Claude Code (same page). "Skill
loading ... append[s] ... as conversation messages, so the cached prefix stays intact" (same page). Named subagents build
their own cache (backgrind, secondary).

Implications: keep the orchestrator on one model/effort for its whole life; load skill references lazily (they append
rather than invalidate); give all workers of one role the *same* agent file and the same leading brief text so their
prefixes match when spawned within the TTL (inference: prefix matching across separate subagent sessions is plausible
but not documented); put the task-specific part of a brief at the end.

### 3.7 Fan-out economics

Anthropic's research system: "agents typically use about 4× more tokens than chat interactions, and multi-agent systems
use about 15× more tokens than chats. For economic viability, multi-agent systems require tasks where the value of the
task is high enough to pay for the increased performance" (https://www.anthropic.com/engineering/multi-agent-research-system).
**Verified.** The same post: token usage "by itself explains 80% of the variance" on BrowseComp; "upgrading to Claude
Sonnet 4 is a larger performance gain than doubling the token budget on Claude Sonnet 3.7" (model choice is an
efficiency multiplier); "most coding tasks involve fewer truly parallelizable tasks than research"; early failures
included "spawning 50 subagents for simple queries"; the fix was embedded scaling rules — "Simple fact-finding requires
just 1 agent with 3-10 tool calls, direct comparisons might need 2-4 subagents with 10-15 calls each". A vendor-reported,
unreproduced figure says Claude Code fan-outs consumed "2.6x to 5.9x as many input tokens as the same work done
sequentially" (quoted by backgrind, secondary). Enterprise Claude Code averages "around $13 per developer per active day
... below $30 per active day for 90% of users" (https://code.claude.com/docs/en/costs) — a useful sanity anchor: an S
mission costing more than a developer-day is probably over-orchestrated.

The ~15× is a *chat baseline* multiplier from mid-2025 research workloads. The skill should not use it as a forecast;
it should use it as a warning that fan-out is a multiplier on *every* per-agent cost, including each agent's cold
cache write, and require a written reason for any fan-out wider than the scope table allows (§6).

### 3.8 Guarding downgrades: what the evidence supports

- Anthropic's evals guidance: code-based graders are "Fast, Cheap, Objective, Reproducible"; model-based graders are
  "Non-deterministic, More expensive than code, Requires calibration with human graders for accuracy"; human spot-check
  sampling is the gold standard; "Because model outputs vary between runs, we run multiple trials"; grade the *outcome*
  (environment state), not the agent's claim (https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).
- Separate grader context: Anthropic's Lance Martin, "a verifier sub-agent tends to outperform self-critique with Fable 5,
  because grading is done in an independent context window" (verified attribution by lane 01, line 991); the harness
  post found "tuning a standalone evaluator to be skeptical is far more tractable than making a generator critical of its
  own work" (lane 01:985).
- Model gap matters for the *reviewer*: Opus 4.8 is "around four times less likely than its predecessor to allow flaws in
  code it has written to pass unremarked" (https://www.anthropic.com/news/claude-opus-4-8); Cognition said Sonnet 4.6
  "meaningfully closed the gap with Opus on bug detection, letting us run more reviewers in parallel"
  (https://www.anthropic.com/news/claude-sonnet-4-6). Reading: parallel Sonnet reviewers are a legitimate breadth tool,
  but the *final* review of risky changes should sit a tier above the maker.
- Sonnet 4.6 was rated "significantly less prone to overengineering" with "fewer false claims of success" than Opus 4.5
  (Sonnet 4.6 launch post) — evidence that it is a sound default worker, not evidence it can grade itself.

No primary source quantifies how often a Sonnet-low grader disagrees with an Opus-high grader on the same artifact. The
sampled-audit rule in §4 exists to *measure* that on each mission instead of assuming it.

## 4. Opinionated spec for the skill

Rule IDs are stable so other lanes and the synthesizer can reference them.

### 4.1 Routing (MR)

- **MR1 MUST** reference models only by full ID: `claude-fable-5-1`, `claude-opus-4-8`, `claude-sonnet-4-6`. The IDs live
  in one table (`references/model-routing.md`); agent files copy them. Aliases (`opus`, `sonnet`, `best`, `fable`) are
  forbidden in skill-authored agent files and scripts.
- **MR2 MUST** assign every spawned agent a role from the matrix in §5 and use that role's agent file. Ad-hoc
  general-purpose spawns MUST pass an explicit `model`.
- **MR3 MUST NOT** run these on Fable 5.1: doc updates, lint/format fixes, simple refactors, test scaffolding, web search
  fetch-and-summarise, classification, ledger/state bookkeeping, merge conflict resolution of mechanical conflicts.
- **MR4 MUST** default workers to `claude-sonnet-4-6`. Effort `medium` unless the role table says otherwise.
- **MR5 SHOULD** use Fable 5.1 for: orchestrator on M/L/XL missions; mission planner / overarching spec on L/XL; deep
  root-cause investigation after one failed Opus 4.8 attempt, or immediately when the bug is non-reproducible,
  cross-system, or has survived prior human attempts.
- **MR6 SHOULD** run the orchestrator of an S mission on `claude-opus-4-8` (high), or on Sonnet 4.6 high for trivially
  bounded tasks (single-file fix with an existing failing test).
- **MR7 MUST** ship a project-level `Explore` agent pinned to `claude-sonnet-4-6` so built-in exploration does not
  inherit the orchestrator's top-tier model.
- **MR8 MUST NOT** switch the orchestrator's own model or effort mid-phase (`/model`, `/effort`). Escalation happens by
  spawning a different agent file or passing `model` on the Agent call.
- **MR9 MAY**, when dynamic workflows are available, route per call with `agent()` options (model + `opts.effort`);
  the same matrix applies.

### 4.2 Escalation and de-escalation (ES)

- **ES1 MUST** follow the ladder, one rung at a time, logging each rung in the ledger:
  `sonnet-4-6/medium` → `sonnet-4-6/high` (fresh context + failure notes) → `opus-4-8/high` → `fable-5-1/high` → human.
- **ES2 MUST** escalate after **2 failed attempts at the same rung** on the same task, where "failed" means a named gate
  (test, typecheck, rubric criterion, reviewer blocking finding) is still red. Never a third attempt at the same rung.
- **ES3 MUST** give the escalated agent a *fresh context* containing: the task brief, the gate output, a ≤300-word failure
  summary from the prior attempts, and the diff (if any). It MUST NOT inherit the failing agent's transcript.
- **ES4 MUST** skip directly to `opus-4-8/high` when the task touches: auth, payments, data migrations, concurrency,
  security boundaries, public API contracts, or infra/CI configuration.
- **ES5 SHOULD** escalate to Fable 5.1 only with a written reason in the ledger ("Opus attempt failed: <gate>"; or
  "non-reproducible / cross-system"). Fable attempts are capped at 2 per task; then human.
- **ES6 SHOULD** de-escalate a role one rung for the rest of the phase when its last 5 consecutive outputs passed gates
  first-time **and** the sampled audit found no disagreement. De-escalation MUST NOT cross below the role's floor (§5).
- **ES7 MUST** promote a role one rung for the rest of the mission after 2 audit disagreements in one phase, and write a
  lesson ("role X at tier Y missed Z").
- **ES8 MUST** treat a sub-agent that exhausts context, loops, or returns without its required output format as a failed
  attempt (it counts toward ES2).

### 4.3 Guarding downgrades (GD)

- **GD1 MUST** use deterministic oracles (tests, typecheck, lint, build, schema validation, screenshot diffs) as the first
  gate for any maker output. A model grader never re-derives what a command can prove.
- **GD2 MUST** grade maker output with an agent that differs in **model** from a Sonnet maker, or in **model or effort**
  from an Opus/Fable maker. Minimum grader for a `sonnet-4-6` maker whose output has no deterministic oracle:
  `opus-4-8/medium`.
- **GD3 MAY** use `sonnet-4-6/low` graders only for *checklist verdicts over deterministic evidence*: "the command output
  shows exit 0 and 0 failures", "every rubric item has a cited file:line", "the JSON matches the schema".
- **GD4 MUST** run a sampled audit per phase: re-grade ≥10% (minimum 1, maximum 5) of accepted cheap-tier outputs with
  `opus-4-8/high`, blind to the first grader's verdict. Record agreement in the ledger.
- **GD5 MUST** treat an audit disagreement as a defect in the process, not just the artifact: fix the artifact, then
  apply ES7.
- **GD6 SHOULD** track per role: first-pass gate rate, rework count, audit agreement, and cost per accepted task. A drop of
  first-pass gate rate below 60% over ≥5 tasks triggers promotion of that role (ES7).
- **GD7 SHOULD** run cascades for classification: `sonnet-4-6/low` classifies with a confidence tag; `low` confidence or a
  high-risk label (ES4 list) re-classifies on `opus-4-8/medium`.
- **GD8 MUST** keep the adversarial reviewer on a *different model than the maker* for any change headed to merge.

### 4.4 Classifier fallback (CF)

- **CF1 MUST** pre-route to `claude-opus-4-8` any task whose brief involves exploit development, pentest logic,
  malware analysis, or offensive security tooling. Vulnerability *discovery* in the project's own code stays on the
  normal matrix (Fable 5.1 allows discovery, not exploit development — https://www.anthropic.com/claude-fable-and-mythos-5-1).
- **CF2 MUST** record every detected fallback or refusal as a ledger event: time, task ID, role, requested model, answering
  model, effort, category if known, and what the orchestrator did next.
- **CF3 MUST** re-assert the orchestrator's intended model at each phase boundary (check the session's active model; if
  it drifted after a fallback, restore it and log the restore). In headless runs, compare the per-model breakdown in
  `--output-format json` against the planned model set.
- **CF4 MUST** re-issue a refused worker task *explicitly* to `claude-opus-4-8/high` with the same brief. A second refusal
  on Opus stops the task and surfaces it to the human with the category.
- **CF5 MUST NOT** rewrite or obfuscate a brief to get past a classifier.
- **CF6 SHOULD** tag biology-domain missions: automatic reroutes there may be answered by Opus 5 (Fable 5.1 benchmark
  note), which is outside the user's model set — log it and ask the human whether to continue.

### 4.5 Cost control and the budget ledger (CB)

- **CB1 MUST** create `BUDGET.md` (or a `## Budget` section in STATUS.md when the mission is S) at mission start with a
  soft cap and hard cap derived from scope (§6 table), and the price table from §3.2.
- **CB2 MUST** append one ledger row per spawned agent: role, agent file, model, effort, attempt/rung, tokens (input,
  cache read, cache write, output) or dollar estimate, outcome (accepted / failed gate / refused), gate evidence pointer.
- **CB3 MUST** review the ledger at every phase boundary: spend vs plan, cost per accepted task by role, audit agreement,
  fallbacks. A phase that exceeds its phase allocation by >50% requires a written re-plan before the next spawn.
- **CB4 MUST** pause at the soft cap (write STATUS, propose a narrowed plan, continue only with a recorded decision) and
  stop at the hard cap. In headless runs set `--max-budget-usd` to the hard cap when the flag is available
  (https://code.claude.com/docs/en/costs).
- **CB5 MUST** apply the marginal-value stop: end any loop after 2 consecutive iterations with no newly green gate and no
  newly verified finding, independent of budget remaining.
- **CB6 SHOULD** treat dollar figures from `/usage` and headless JSON as estimates ("computed locally from token counts at
  list price", https://code.claude.com/docs/en/costs); for subscription users record plan-usage percentage instead of
  dollars.
- **CB7 MUST** bound fan-out by the scope table; wider fan-out requires a one-line value case in the ledger.
- **CB8 SHOULD** prefer sequential execution when subtasks share files or depend on each other's outputs; parallelise
  research, independent reviewers, and file-disjoint implementation only.

### 4.6 Context and caching discipline (CX)

- **CX1 MUST** write briefs in the order: fixed role preamble (from the agent file) → stable mission context pointer
  (paths to SPEC/STATE, not pasted content) → task-specific section → required output format. Variable content last.
- **CX2 MUST** pass paths and excerpts, not whole files, to workers; workers read what they need.
- **CX3 MUST NOT** connect/disconnect MCP servers, toggle plugins, or change tool permission sets during a phase
  (each invalidates the cache — https://code.claude.com/docs/en/prompt-caching).
- **CX4 SHOULD** cap sub-agent return payloads (e.g. ≤500 words plus pointers) so the orchestrator's context grows slowly.
- **CX5 SHOULD** compact or hand off the orchestrator only at phase boundaries, after writing STATE/STATUS.

### 4.7 Preflight and graceful degradation (PF)

- **PF1 MUST** at mission start: check `CLAUDE_CODE_SUBAGENT_MODEL` is unset (or equals `inherit`); confirm the Claude Code
  version supports the chosen models (Fable 5.1 needs v2.1.257+, Opus 4.8 v2.1.154+, https://code.claude.com/docs/en/model-config);
  spawn one tiny probe per model ID and confirm in `/usage` or headless JSON that the expected model answered.
- **PF2 MUST** degrade when a model is unavailable: Fable 5.1 unavailable → orchestrator/planner on `opus-4-8/xhigh`;
  Opus 4.8 unavailable → escalation rung becomes `sonnet-4-6/high` + mandatory human review of risky changes; Sonnet
  4.6 unavailable → stop and ask (do not silently promote all workers to Opus). Log the degraded profile in STATUS.md.
- **PF3 MUST** in harnesses without per-agent model selection, run the matrix as *sequential phases* in separate sessions
  (`claude -p --model <id>`), keeping the maker/grader separation by session.
- **PF4 SHOULD** warn the user when running on a subscription plan that Fable-heavy missions consume plan limits
  quickly; offer the Opus-orchestrator profile.

## 5. Model & effort assignment

Notation: `F` = `claude-fable-5-1`, `O` = `claude-opus-4-8`, `S` = `claude-sonnet-4-6`; effort after the slash. "Floor" is
the lowest tier ES6 may de-escalate to. "Guard" is the check that makes the chosen (cheaper) tier safe. Agent file names
follow `<role>-<model>-<effort>.md` so one role can have several effort variants (effort is frontmatter-only).

| # | Role | Default | Floor | Escalate to | Cost reasoning | Guard on the downgrade |
|---|---|---|---|---|---|---|
| 1 | Orchestrator (M/L/XL) | F/high (XL unattended multi-day: F/xhigh chosen at session start) | O/high | human | Long-lived, cache-warm; per turn ≈ O/high cost (§3.2); value is judgement across days | Phase-boundary ledger review (CB3); deterministic gates; human checkpoints |
| 1b | Orchestrator (S) | O/high | S/high | F/high on 2 failed phases | S missions rarely amortise Fable cold writes | Same gates; ES ladder |
| 2 | Planner / decomposer | L/XL: F/high · M: O/high · S: orchestrator inline | O/medium | F/high | One-shot, low volume, highest leverage | Plan critique by a different model (O/high if planner F; F/high only on XL) |
| 3 | Spec writer | Overarching: O/high · feature spec: S/high | S/high | O/high | Specs are read many times; errors multiply | Every requirement has a named oracle; O/medium spec review when writer is S |
| 4 | Architect | L/XL system design: F/high · bounded decisions: O/high | O/high | F/high | Architecture errors are the costliest rework | Adversarial architecture review on the other model; ADR with rejected alternatives |
| 5 | Research lead / synthesiser | O/high | S/high | F/high (market/strategy on XL) | Synthesis is judgement; volume is low | Claim table with URL per claim; sampled claim re-verification |
| 6 | Web-search worker | S/medium (single fact: S/low) | S/low | S/high | High volume, fetch-and-summarise; results checkable | Every claim carries URL + quote; S/low claim-checker confirms quote appears on page |
| 7 | Implementer | S/medium (multi-file or unfamiliar code: S/high) | S/medium | ES ladder → O/high → F/high | Bulk of tokens; ≈2.2× cheaper than O (§3.2) | Tests/typecheck/lint green; O reviewer (GD2); sampled audit (GD4) |
| 8 | Test writer | Test plan: O/medium · test code: S/medium | S/medium | O/high | Weak tests silently pass bad code, so the *plan* gets the better model | New test must fail before the fix / against a mutant; O review of the plan |
| 9 | Debugger | Reproducible, localised: S/high · hard: O/high · deep root cause: F/high | S/high | F/high → human | Most bugs are cheap; the rare deep ones justify Fable ("root-cause investigations" — model-config) | Failing repro test before fix, green after; root-cause statement checked against evidence |
| 10 | Code reviewer (routine) | O/medium | S/high (only when maker is O or F) | O/high | Reviewer a tier above the maker catches more (§3.8) | Findings cite file:line; sampled audit of "no findings" verdicts |
| 11 | Adversarial reviewer | O/high; final L/XL milestone review: F/high once | O/high | F/high | Low volume, high catch value | Different model from maker (GD8); findings must be reproducible or cite evidence |
| 12 | Security reviewer | O/high | O/high | human | Pre-routed to Opus to avoid sticky Fable fallback (CF1); discovery on own code allowed on F 5.1 but O avoids refusal churn | SAST/dependency scanners as oracle; exploit-style work never on F |
| 13 | UI / vision verifier | Design-quality verdict: O/high · checklist over screenshot/DOM: S/medium · flagship-screen fidelity tie-break (L/XL): F/high | S/medium | F/high | Images are input-heavy; F only where visual judgement is the product | Pixel/DOM assertions first; judgement verdicts sampled by O/high |
| 14 | Grader / judge | Checklist over deterministic evidence: S/low · rubric judgement of S-made work: O/medium · audit: O/high | S/low (checklists only) | O/high | Graders run often; spend only where judgement is needed | GD3 limits S/low to evidence checklists; GD4 audit |
| 15 | Classifier / router | S/low | S/low | O/medium (cascade) | Tiny prompts, very high volume | Confidence tag; low confidence or risky label → O/medium (GD7) |
| 16 | Doc writer | S/medium (changelog/README bump: S/low) | S/low | S/high | Never Fable (MR3) | Link check, code-sample compile/run; sampled audit |
| 17 | Merge integrator | S/high | S/medium | O/high for semantic conflicts in ES4 areas | Mostly mechanical | Full test suite on merged tree; conflict list in ledger |
| 18 | Lesson distiller | Phase lessons: orchestrator inline (warm cache) · cross-mission skill edits: O/high | S/high | F/high (XL retrospective) | Orchestrator already holds evidence in cache; a fresh distiller pays a cold read | Each lesson cites the failure evidence; S/medium checker confirms citations exist |
| 19 | Explore (project override) | S/low (thorough mode: S/medium) | S/low | O/medium | Stops built-in Explore inheriting an Opus-tier model (MR7) | Output is pointers; consumer verifies |
| 20 | Ledger / STATUS bookkeeper | S/low | S/low | — | Pure bookkeeping | Schema check of the ledger file |

Why graders are not uniformly "Sonnet low": the user's instinct (Haiku → Sonnet low) is right for **classifiers and
evidence checklists**, where the grader reads command output and ticks boxes. It is wrong for **judgement** over
Sonnet-made artifacts: a same-model, lower-effort judge shares the maker's blind spots and explores less (effort "means
fewer and terser tool calls", https://platform.claude.com/docs/en/build-with-claude/effort). The cost of an O/medium
judge on a 20k-token artifact is roughly 26k×$5 + 1.5k×$25 ≈ $0.17 per verdict (calculation, new tokenizer); a missed
defect that reaches merge costs a full rework cycle.

Which roles benefit from high effort: planner, architect, debugger, adversarial and security reviewers, research lead,
test *planning*, and the second rung of any escalation. Which do not: classifiers, bookkeepers, evidence checklists,
search workers on single facts, doc bumps. `max` is not assigned anywhere by default (opinion 15); `xhigh` only for the
XL unattended orchestrator and for Opus as the degraded orchestrator (PF2).

Profiles the skill should offer (chosen at mission start, recorded in BUDGET.md):

- **Standard**: table above.
- **Lean** (user asks for cheapest, or subscription limits): orchestrator O/high for all scopes; planner/architect O/high;
  deep debugging F/high only with human approval; everything else unchanged. Guards unchanged.
- **Degraded** (PF2): Fable unavailable → rows 1, 2, 4 on O/xhigh; Opus unavailable → risky reviews need human sign-off.

## 6. Project-shape conditionals

### 6.1 Scope table (starting defaults; calibrate from ledgers after 3 missions)

Budget figures are my opinionated API-dollar defaults anchored on Claude Code's enterprise average of "around $13 per
developer per active day" (https://code.claude.com/docs/en/costs); they are not Anthropic figures.

| Scope | Typical shape | Orchestrator | Max concurrent agents | Max agents per phase | Soft / hard cap (API $) | Fable allowed for |
|---|---|---|---|---|---|---|
| S | one bug, one small feature, chore | O/high (or S/high single session for chores) | 3 | 10 | $8 / $20 | deep root cause only, with ledger reason |
| M | feature in existing product, bounded bug hunt | F/high if cross-cutting, else O/high | 5 | 40 | $50 / $120 | orchestrator, deep debugging |
| L | service extraction, website + research, single-platform app | F/high | 8 | 120 | $300 / $700 | orchestrator, planner, architect, final review |
| XL | multi-platform greenfield app | F/high (xhigh if unattended multi-day) | 15 (below the 20-concurrent ceiling reported by backgrind) | 150 per session; split sessions per phase | $1,500 / $3,500 | as L, plus flagship-screen vision tie-breaks and XL retrospective |

Phase allocation of the cap (default): planning/spec/architecture 15%, research 10%, implementation 45%,
verification/review/audit 20%, reserve 10%. Missions without research move that 10% to verification.

### 6.2 IF/THEN rules

- **IF** the task is a greenfield multi-platform app (e.g. Swift iOS + Cloudflare backend) **THEN** scope ≥ L; F/high
  orchestrator, planner and architect; separate implementer agent files per platform (`implementer-ios-sonnet-4-6-medium`,
  `implementer-worker-sonnet-4-6-medium`) so briefs and caches stay platform-stable; make backend↔app contract tests and
  `xcodebuild`/`wrangler` builds the first gates so model graders only judge UX and design; UI verifier O/high on each
  screen, F/high only for flagship-screen tie-breaks; allocate ≥20% of budget to verification.
- **IF** the task is a deep bug hunt **THEN** orchestrator O/high; debugger ladder starts at S/high for reproduction;
  **IF** no deterministic repro after 2 attempts, or the bug is non-reproducible/cross-system **THEN** spawn F/high
  investigator with the failure notes (ES5); parallel hypothesis testers ≤3 (S/medium), one hypothesis each; stop
  hypotheses on the marginal-value rule (CB5); the fix is accepted only with a repro test that fails before and passes
  after.
- **IF** the task adds a feature to an existing product (e.g. a dashboard) **THEN** scope M; use the pinned `Explore`
  (S/low) heavily before planning; implementer S/medium; reviewer O/medium; UI verifier O/high on dashboard screenshots
  with seeded data; F only if the feature crosses ≥3 subsystems.
- **IF** the task is a service migration/extraction (e.g. AI gateway into a core service) **THEN** scope L; architect
  F/high for the boundary and cut-over plan; ES4 applies to almost every change (API contracts, data, infra) so reviews
  default O/high; implementers S/high; parity/dual-run diff tests are the grader; security reviewer O/high because
  gateways hold credentials; keep fan-out low (files overlap) — prefer sequential slices.
- **IF** the task is market research plus a website with blog/docs **THEN** research lead O/high; search workers S/medium
  fan-out 4–8 by subtopic, each claim with URL + quote; S/low claim-checker; positioning synthesis O/high (F/high only
  at XL); copy S/high with O/medium brand/claim review; site build S/medium; UI verifier O/high; doc writer S/medium.
- **IF** the task includes offensive security, exploit development or pentest logic **THEN** pre-route all such work to
  O/high (CF1) and require human sign-off before running anything against live systems.
- **IF** the task touches biology/life-sciences content **THEN** expect reroutes to a model outside the user's set
  (Opus 5); log them and ask the human (CF6).
- **IF** the task is a chore (lint sweep, dependency bump, doc refresh) **THEN** no orchestrator and no Fable; one S/medium
  session with deterministic gates and an S/low checklist grader.
- **IF** the user is on a subscription plan or asks for minimum cost **THEN** Lean profile (§5); record plan-usage % in the
  ledger instead of dollars (CB6).
- **IF** the mission is unattended overnight/multi-day **THEN** set the hard cap via `--max-budget-usd` where available,
  run CF3 checks at every phase boundary, and write the ledger before each wait.
- **IF** Fable 5.1 is unavailable or the Claude Code version is older than v2.1.257 **THEN** Degraded profile (PF2).
- **IF** a named platform feature is unavailable (dynamic workflows, per-agent model selection) **THEN** keep the matrix
  but express it as separate sessions per role (PF3).

## 7. Artifacts & templates

### 7.1 `references/model-routing.md` — the single source of model IDs

```markdown
# Model routing table (edit here only)
| Tier | Model ID | Input $/MTok | Cache write 5m | Cache read | Output $/MTok | Efforts used |
|---|---|---|---|---|---|---|
| F | claude-fable-5-1 | 10.00 | 12.50 | 0.25 | 50.00 | high, xhigh |
| O | claude-opus-4-8 | 5.00 | 6.25 | 0.50 | 25.00 | medium, high, xhigh |
| S | claude-sonnet-4-6 | 3.00 | 3.75 | 0.30 | 15.00 | low, medium, high |
Prices verified <date> at https://platform.claude.com/docs/en/about-claude/pricing. O and F use the newer tokenizer
(~30% more tokens for the same text than S). Never use aliases (`opus`, `sonnet`, `fable`, `best`).
Escalation ladder: S/medium → S/high → O/high → F/high → human.
```

### 7.2 Subagent frontmatter examples (`.claude/agents/`)

Fields used: `name`, `description`, `tools`, `model` (full ID), `effort` (frontmatter-only; see
https://github.com/anthropics/claude-code/issues/72596). Keep descriptions short — combined custom descriptions over
15,000 tokens trigger a startup warning (https://code.claude.com/docs/en/sub-agents).

```markdown
---
name: implementer-sonnet-4-6-medium
description: Implements one scoped task from a brief; returns diff summary and gate results.
tools: Read, Grep, Glob, Edit, Write, Bash
model: claude-sonnet-4-6
effort: medium
---
You implement exactly the task in the brief. Run the named gate commands before returning.
Return: files changed, gate commands with exit codes, open risks (≤200 words). Never weaken or delete tests.
```

```markdown
---
name: implementer-sonnet-4-6-high
description: Second-rung implementer; receives failure notes from prior attempts.
tools: Read, Grep, Glob, Edit, Write, Bash
model: claude-sonnet-4-6
effort: high
---
Read the failure summary first. State the root cause you believe caused the prior failures before editing.
```

```markdown
---
name: code-reviewer-opus-4-8-medium
description: Reviews a diff made by a Sonnet implementer against the brief and gates. Read-only.
tools: Read, Grep, Glob, Bash
model: claude-opus-4-8
effort: medium
---
You did not write this code. Judge the artifact and the brief only. Every finding cites file:line and severity
(blocking / should-fix / nit). If you find nothing blocking, list the three riskiest lines you checked.
```

```markdown
---
name: adversarial-reviewer-opus-4-8-high
description: Tries to break a change or plan; used before merge and on risky areas.
tools: Read, Grep, Glob, Bash
model: claude-opus-4-8
effort: high
---
Assume the change is wrong. Find a concrete input, sequence or environment that breaks it, and show the evidence.
```

```markdown
---
name: grader-checklist-sonnet-4-6-low
description: Ticks a checklist over supplied command output and file pointers. No judgement calls.
tools: Read, Grep, Glob
model: claude-sonnet-4-6
effort: low
---
For each checklist item answer PASS/FAIL with the exact evidence line. If evidence is missing, FAIL. Do not infer.
```

```markdown
---
name: router-sonnet-4-6-low
description: Classifies a task into a role and risk label; returns JSON only.
tools: Read
model: claude-sonnet-4-6
effort: low
---
Return {"role": <role from table>, "risk": "normal|risky", "confidence": "high|low", "reason": "<≤20 words>"}.
risky = auth, payments, data migration, concurrency, security boundary, public API, infra/CI.
```

```markdown
---
name: debugger-fable-5-1-high
description: Deep root-cause investigator after an Opus attempt failed or the bug is non-reproducible.
tools: Read, Grep, Glob, Bash, Edit, Write
model: claude-fable-5-1
effort: high
---
Describe the outcome you will prove: the root cause, a failing reproduction, and the fix that turns it green.
```

```markdown
---
name: security-reviewer-opus-4-8-high
description: Reviews changes for security defects in this project's own code. Never develops exploits.
tools: Read, Grep, Glob, Bash
model: claude-opus-4-8
effort: high
---
Run the project's scanners first and cite their output. Report defects with file:line, impact, and fix direction.
```

```markdown
---
name: Explore
description: Read-only codebase search returning file:line pointers and short excerpts.
tools: Read, Grep, Glob
model: claude-sonnet-4-6
effort: low
---
Return pointers, not essays. Maximum 300 words.
```

Per-invocation escalation (Agent/Task tool): pass `model: "claude-opus-4-8"` when re-running a role one tier up for a
single task; effort stays whatever the agent file says, so use a dedicated agent file when effort must change.

### 7.3 Per-mission budget ledger — `BUDGET.md`

```markdown
# Budget ledger · <mission name>
Scope: <S|M|L|XL> · Profile: <standard|lean|degraded> · Billing: <api-dollars|plan-usage%>
Soft cap: $<n> · Hard cap: $<n> · `--max-budget-usd`: <value|not available>
Price table: references/model-routing.md (verified <date>)

## Phase plan
| Phase | Allocation | Spent | % of allocation | Status |
|---|---|---|---|---|
| plan/spec/architecture | 15% = $<n> | $<n> | <n>% | open / closed |
| research | 10% | | | |
| implementation | 45% | | | |
| verification/review/audit | 20% | | | |
| reserve | 10% | | | |

## Spawn log (one row per agent run)
| # | Time | Task | Role | Agent file | Model (resolved) | Effort | Rung | In / cache-read / cache-write / out (k tok) | $ est | Outcome | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10:02 | T-004 | implementer | implementer-sonnet-4-6-medium | claude-sonnet-4-6 | medium | 1 | 3 / 410 / 60 / 12 | 0.54 | failed gate | test output: logs/T-004-a1.txt |

## Escalations
| Task | From → To | Reason (gate + evidence) | Result |
|---|---|---|---|

## Model / fallback events
| Time | Task | Requested model | Answering model | Effort | Category | Action taken |
|---|---|---|---|---|---|---|

## Downgrade guards
| Phase | Role | Accepted outputs | Audited | Agreements | Disagreements | First-pass gate rate | Action |
|---|---|---|---|---|---|---|---|

## Phase-boundary reviews
- <date> phase <name>: spent $<n> vs $<n> plan; cost per accepted task by role: <...>; fallbacks: <n>;
  marginal-value check: <new gates green / new verified findings>; decision: <continue | re-plan | pause at soft cap>.
```

### 7.4 Escalation handoff brief (fresh context, ES3)

```markdown
Role: <role> · Model: <full id> · Effort: <level> · Rung <n> of ladder
Task brief (unchanged): <path or text>
Gate that is still red: <command> → <last 30 lines or path>
Prior attempts (≤300 words): what was tried, what changed, why it failed, what you should NOT repeat.
Current diff: <path to patch or "none (reverted)">
Output required: root cause statement · change summary · gate commands with exit codes · residual risk.
Budget for this attempt: ≤ $<n> or <n> tool calls; stop and report if exceeded.
```

### 7.5 Sampled audit prompt (GD4)

```markdown
You are auditing an output that was already accepted. You do not see the first grader's verdict.
Artifact: <path/diff> · Brief: <path> · Rubric: <path> · Deterministic evidence: <paths>
For each rubric criterion: PASS / FAIL with evidence (file:line or command output line).
Then: overall ACCEPT / REJECT, and the single most important defect if REJECT.
```

The orchestrator compares audit verdict vs original verdict and records agreement in `BUDGET.md → Downgrade guards`.

### 7.6 Phase-boundary cost review checklist

- [ ] Ledger rows complete for every spawn in the phase (model *resolved*, not planned).
- [ ] Spend vs allocation; >150% of allocation → written re-plan before next spawn (CB3).
- [ ] Soft cap reached? → pause, write STATUS, propose narrowed scope (CB4).
- [ ] Cost per accepted task by role; any role >2× its peers → check for loops, oversized briefs, cache misses.
- [ ] Sampled audit done; disagreements → promote role (ES7) and write lesson.
- [ ] Fallback events reviewed; orchestrator model re-asserted (CF3).
- [ ] Marginal-value test: did this phase turn a gate green or verify a finding? Two phases with "no" → stop (CB5).
- [ ] Fan-out within the scope table (CB7).

### 7.7 Preflight checklist (PF1)

- [ ] `claude --version` ≥ 2.1.257 (Fable 5.1) / ≥ 2.1.154 (Opus 4.8).
- [ ] `CLAUDE_CODE_SUBAGENT_MODEL` unset or `inherit`.
- [ ] Agent files present for each (role, effort) used; all `model:` values are full IDs.
- [ ] Probe spawn per model ID; `/usage` "Usage by model" or headless JSON shows the three expected IDs.
- [ ] Project `Explore` override present (MR7).
- [ ] BUDGET.md created with caps, profile and billing regime.

## 8. Anti-patterns & failure modes

Cost and token traps:

1. **Alias drift.** `model: opus` in an agent file silently runs Opus 5, `sonnet` runs Sonnet 5 on the Anthropic API and
   Sonnet 4.5 on Bedrock/Google (https://code.claude.com/docs/en/model-config). The user's model constraint is violated
   without any error. Fix: MR1.
2. **Silent inheritance.** A worker whose `model` is excluded by an org allowlist, or omitted, inherits the orchestrator's
   Fable model (backgrind, secondary). The "cheap" fan-out costs ≈2.9× what was planned. Fix: PF1 probes; ledger records
   the *resolved* model.
3. **Built-in Explore on the top tier.** Explore "inherits from the main conversation, capped at Opus"
   (https://code.claude.com/docs/en/sub-agents). Dozens of explorations on an Opus-tier model. Fix: MR7.
4. **Mid-session `/model` switches (and `/effort` switches on most models).** Each re-reads the whole history uncached;
   Fable 5.1 on an API key or subscription keeps its cache across effort changes
   (https://code.claude.com/docs/en/prompt-caching). On a 300k-token Fable orchestrator a cold rewrite is ≈$3.75 per switch
   (300k × $12.50/MTok, calculation). Fix: MR8.
5. **Cache-hostile briefs.** Timestamps, run IDs or task text at the *top* of briefs and agent prompts; toggling MCP
   servers/plugins mid-phase. Fix: CX1, CX3.
6. **Pasting whole files into briefs** instead of paths, inflating every worker's cold write. Fix: CX2.
7. **Fan-out by default.** "spawning 50 subagents for simple queries" was an early Anthropic failure
   (https://www.anthropic.com/engineering/multi-agent-research-system). Coding tasks sharing files do not parallelise well
   and pay a merge-integration tax. Fix: CB7, CB8, scope table.
8. **Fable for chores.** Doc updates, lint fixes and simple refactors on Fable cost ≈4.3× Sonnet for the same text
   (§3.2). Fix: MR3.
9. **`max` effort as a quality knob.** Effort is "a behavioral signal, not a strict token budget"
   (https://platform.claude.com/docs/en/build-with-claude/effort); practitioners report overthinking at `max` (secondary).
   Better context beats more effort. Fix: opinion 15.
10. **Retry storms.** Re-running the same failing worker at the same rung five times. Fix: ES2 (two attempts per rung).
11. **Budget as verdict.** Killing a mission at the soft cap and losing the work, or blowing through it silently. Fix: CB4
    — pause and re-plan at soft, stop at hard (the arcwell lesson: "A budget ceiling is a WAIT, not a verdict",
    arcwell/docs/handoff/2026-08-21-remediation-status.md:168).
12. **Trusting `/usage` dollars as the bill.** It is a local list-price estimate (https://code.claude.com/docs/en/costs).
    Use it for relative control; reconcile against the Console for real spend.

Quality traps from downgrades:

13. **Same-model, lower-effort judge.** Sonnet low grading Sonnet medium output on judgement criteria rubber-stamps shared
    blind spots. Fix: GD2/GD3.
14. **Model graders re-deriving command results.** Paying a judge to read logs a command already turned into exit codes.
    Fix: GD1.
15. **No audit, no drift detection.** The cheap tier's quality drops (harder module, unfamiliar stack) and nobody notices
    because every grader is cheap too. Fix: GD4, GD6.
16. **Plan-high / execute-low with gaps.** A Sonnet low executor "won't catch ambiguity it inherits" (secondary). Fix:
    implementers default medium; plan review before execution.
17. **Escalation that inherits the transcript.** The escalated model reads the failing agent's reasoning and repeats it.
    Fix: ES3 fresh context with a short failure summary.

Fallback traps:

18. **Silent sticky fallback.** After a classifier flag, the orchestrator keeps running on Opus 4.8 at the old effort and
    the ledger still says Fable (lane 01:1002). Fix: CF2, CF3.
19. **Brief laundering.** Rephrasing security work to slip past classifiers. Fix: CF5 — route explicitly.

Process bloat:

20. **Ledger theatre.** A 12-column spawn log maintained by the Fable orchestrator by hand. Fix: bookkeeping on an S/low
    agent (role 20) or from headless JSON; the orchestrator reads summaries.
21. **Agent-file explosion.** One file for every (role × model × effort) combination. Fix: ship only the variants in §7.2
    plus those the matrix actually uses; per-invocation `model` covers one-off escalations.
22. **Review loops without a stop rule.** arcwell's eighteen review rounds "prevented progress on the remaining normative
    plan" (arcwell/docs/operations/review-process-amendment.md:25-28). Fix: CB5 marginal-value stop applies to reviews.

## 9. Open questions / risks for the synthesizer

1. **The user's model set is not the current lineup.** Opus 5 ($5/$25) and Sonnet 5 ($2/$10) are current; Sonnet 5 is
   *cheaper* than Sonnet 4.6 and has a later knowledge cutoff (https://platform.claude.com/docs/en/about-claude/pricing,
   https://platform.claude.com/docs/en/about-claude/models/overview). I honoured the constraint. The synthesizer should
   keep IDs in one table and mention the option to the user, without changing the default.
2. **Tokenizer multiplier on Fable 5.1 is inferred.** The pricing note names "Claude 4.7 and later models"; I assume Fable
   5.x is included. If not, Fable's effective per-text cost vs Sonnet is ≈3.3× instead of ≈4.3×. The routing decisions do
   not change.
3. **Official Claude Code effort controls were not fully fetched.** `effort:` frontmatter is verified through issue
   #72596's quote of the docs; `/effort` and `--effort` rest on community sources. The skill should probe at runtime and
   fall back to per-effort agent files, which work either way.
4. **Model precedence for subagents conflicts between sources.** The official sub-agents page implies
   `CLAUDE_CODE_SUBAGENT_MODEL` applies only when nothing else assigns a model unless forced; backgrind (secondary) puts it
   first. PF1's "must be unset" rule avoids needing the answer.
5. **Allowlist silent-inheritance, fan-out ceilings (200/20/depth 3), and "named subagents build their own cache"** come
   from a single secondary source (backgrind). Plausible and consistent with official docs, but unverified.
6. **Does `/usage` "Usage by model" include subagent tokens?** The prompt-cache line explicitly excludes subagents
   (https://code.claude.com/docs/en/costs); the per-model breakdown was not confirmed either way. If it excludes them, the
   ledger must rely on headless JSON or per-agent estimates.
7. **Detecting a classifier fallback from inside a running session** (what the orchestrator can observe) is not verified
   by me or lane 01 (lane 01:941). CF3 relies on phase-boundary checks of the resolved model, which may need a human-visible
   step in interactive sessions.
8. **Budget numbers in §6.1 are opinions**, anchored on an enterprise per-developer average. They need calibration from
   the first few mission ledgers; the synthesizer should label them "starting defaults".
9. **No primary data on Sonnet-low vs Opus-high grader agreement.** GD4's 10% sample and ES7's "2 disagreements" threshold
   are judgement calls meant to generate that data per mission.
10. **Subscription vs API billing.** Fable 5.1 is available on Pro/Max/Team/Enterprise plans
    (https://www.anthropic.com/claude/fable); dollar caps are meaningless there. The ledger supports plan-usage %, but
    the skill cannot read plan limits programmatically in all harnesses.
11. **Biology reroutes to Opus 5** are outside the user's model set; the skill can only log and ask (CF6).
12. **Customer and vendor claims** (Every's "half as many tokens", Cognition's code-review migration, the 2.6×–5.9× fan-out
    figure) are not independent evidence; none are used as normative thresholds.
13. **Harness portability.** In harnesses without per-agent model selection, PF3's session-per-role pattern keeps
    maker/grader separation but loses parallelism; the synthesizer should keep that path simple.

## Sources

Primary (fetched during this lane unless marked):

- https://platform.claude.com/docs/en/about-claude/pricing — per-model prices, cache multipliers (Fable 5.1 0.025×),
  tokenizer note, US-only/regional notes.
- https://platform.claude.com/docs/en/about-claude/models/overview — current lineup, API IDs, default effort, latency,
  context, Batch 50%.
- https://platform.claude.com/docs/en/about-claude/model-deprecations — Active status and retirement floors for
  `claude-fable-5-1`, `claude-opus-4-8`, `claude-sonnet-4-6`.
- https://platform.claude.com/docs/en/build-with-claude/effort — effort levels, per-model availability, behaviour.
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching — prefix order, TTL, refresh, 1h option.
- https://code.claude.com/docs/en/model-config — aliases and their resolution, pinning, Fable guidance, version floors,
  automatic fallback mention.
- https://code.claude.com/docs/en/sub-agents — subagent contexts, Explore inheritance cap, `CLAUDE_CODE_SUBAGENT_MODEL`,
  description-token warning, Haiku cost advice.
- https://code.claude.com/docs/en/costs — enterprise averages, `/usage` estimate semantics, `--max-budget-usd`, prompt
  cache statistics (main conversation only).
- https://code.claude.com/docs/en/prompt-caching — cache layers, invalidators, per-model and per-effort caches.
- https://www.anthropic.com/news/claude-fable-5-mythos-5 — Fable 5 launch, Opus 4.8 fallback, <5% sessions, pricing.
- https://www.anthropic.com/claude/fable — Fable 5.1 availability (incl. subscription plans), cache-read price, rerouted
  requests not billed at Fable prices, 30-day retention, customer quotes.
- https://www.anthropic.com/claude-fable-and-mythos-5-1 — Fable 5.1 effort/cost claims, 60% fewer cyber false positives,
  discovery vs exploit rule, cyber → Opus 4.8 / bio → Opus 5 in benchmarks.
- https://www.anthropic.com/news/claude-opus-4-8 — Opus 4.8 price, flaw-flagging improvement, xhigh recommendation,
  dynamic workflows launch date.
- https://www.anthropic.com/news/claude-sonnet-4-6 — Sonnet 4.6 price, positioning, reviewer/bug-detection quotes.
- https://www.anthropic.com/engineering/multi-agent-research-system — ~4×/~15× token multipliers, 80% variance, scaling
  rules, early fan-out failures.
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents — grader types, calibration, trials, outcomes.
- https://github.com/anthropics/claude-code/issues/72596 — effort frontmatter-only; per-invocation `model`/`isolation`;
  workflow `agent()` `opts.effort`; closed as not planned.

Verified by sibling lane 01 (research/mission-skill/01-orchestration-control.md), cited, not re-fetched by me:

- https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback (lane 01:971) — refusal stop_reason,
  categories, server-side fallback beta.
- https://github.com/anthropics/claude-code/issues/74311 (lane 01:1002) — sticky fallback, `fallbackModel` scope,
  related effort carry-over issue.
- Lance Martin verifier quote and harness-design post (lane 01:985, 991).

Secondary (practitioner; used only where labelled):

- https://backgrind.com/blog/claude-code-subagent-models/ — frontmatter `model` values, precedence claim, allowlist
  silent inheritance, fan-out ceilings, subagent cache isolation.
- https://github.com/tmozii1/Claude-Code-Everything/blob/main/docs/reference/effort-levels.md — effort behaviour,
  plan-high/execute-low caveat, `ultrathink` claim.
- https://joaothallis.com/posts/how-to-set-claude-code-effort-level-to-max/ (search snippet) — `/effort`, `--effort`.
- https://www.finout.io/blog/claude-fable-5-mythos-5-pricing-benchmarks (search snippet) — "2x the cost of Claude Opus 4.8".

Workspace evidence (read-only):

- arcwell/docs/handoff/2026-08-21-remediation-status.md:168 — "A budget ceiling is a WAIT, not a verdict".
- arcwell/docs/operations/cutover-runbook.md:28 — soft/hard cost budgets during cutover.
- arcwell/docs/architecture/ownership.md:23 — model gateway owns budgets and reservations.
- arcwell/docs/operations/review-process-amendment.md:25-31 — repeated review loop prevented progress.
- research/mission-skill/00-brief.md §3 steps 01, 04, 07, 14 and "Mistakes" list — the post claims checked in §2.
