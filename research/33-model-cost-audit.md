# 33 · Model, price, effort, and cost audit

Audited 2026-09-14 against live documentation, live `claude -p` runs on Claude Code 2.1.270, and the
token usage recorded in this machine's own Claude Code transcripts. Scope: `skill/` (agents,
references, SKILL.md, evals README), `README.md`, and `install.sh`. No file other than this report was
edited.

## 1. Verdict

The model facts in drive are right and the dollar figures are not. Every model ID, alias, list
price, cache price, context window, and effort level the skill states for Fable 5.1, Opus 5, and
Sonnet 5 matches the live documentation, and I confirmed the prices a second way: Claude Code's
reported cost for six live runs reproduces exactly from the pricing page's rates. The roster's
model and effort choices are all supported by each model's own guidance, with two rows whose
reasons are wrong (they imply that running security work on Opus 5 avoids the cyber classifier,
which Opus 5 also runs). The cost envelopes in `models.md` section 7 are too low for every cell I
modelled except `report` M, by roughly two to three times at XS to M and one and a half to two times
at L and XL. The research derivation priced an Opus verifier or investigator at about $1.50; Opus
subagents on this machine cost a median of $3.51, and the roster has since added Fable final audits
at xhigh, severe tests before implementation, UI review rounds, and `/code-review` and `/simplify`
passes. Because the headless leg loop stops a run when spend reaches the top of its envelope, a
typical `feature` M run (about $177 modelled) would be stopped against today's $150 ceiling before
it finishes. Beyond the envelopes, `install.sh` prints launch commands with the `fable` alias rather
than the pinned ID, `safety.md` still describes a retry that no longer exists, and two token claims
(that SKILL.md's sections 1 to 6 fit in 5,000 tokens, and the lessons cap of 4,000 tokens) are wrong
under the current tokenizer. Nothing in the skill tells a user or agent to select Opus 4.8, Sonnet
4.x, or Haiku, or quotes their prices.

## 2. Live model resolution

Each run was `claude -p --model <name> --max-turns 1 --output-format json "Reply with ok"` from
`/tmp` on Claude Code 2.1.270, first-party API.

| `--model` passed | Key under `modelUsage` | `canonicalModel` | Reported cost | Cache writes |
|---|---|---|---|---|
| `claude-fable-5-1` | `claude-fable-5-1` | `claude-fable-5-1` | $0.37775375 | 18,540 tokens, all one-hour |
| `fable` | `claude-fable-5-1` | `claude-fable-5-1` | $0.40261375 | 19,783, all one-hour |
| `claude-opus-5` | `claude-opus-5` | `claude-opus-5` | $0.1930855 | 17,945, all one-hour |
| `opus` | `claude-opus-5` | `claude-opus-5` | $0.1930555 | 17,942, all one-hour |
| `claude-sonnet-5` | `claude-sonnet-5` | `claude-sonnet-5` | $0.0723612 | 16,724, all one-hour |
| `sonnet` | `claude-sonnet-5` | `claude-sonnet-5` | $0.0773132 | 17,962, all one-hour |

Every run reported `contextWindow` 1,000,000 and `maxOutputTokens` 64,000, and exactly one model
under `modelUsage`, so no fallback occurred. The aliases resolve today to the three pinned models.

The billed cost reproduces from the pricing page to the last digit, which confirms the cache-read
and one-hour write prices independently of the page:

| Run | Cache read | One-hour write | Input | Output | Sum |
|---|---|---|---|---|---|
| Fable 5.1 | 26,935 × $0.25/M = $0.00673375 | 18,540 × $20/M = $0.37080 | 2 × $10/M = $0.00002 | 4 × $50/M = $0.0002 | $0.37775375 |
| Opus 5 | 27,051 × $0.50/M = $0.0135255 | 17,945 × $10/M = $0.17945 | 2 × $5/M = $0.00001 | 4 × $25/M = $0.0001 | $0.1930855 |
| Sonnet 5 | 27,106 × $0.20/M = $0.0054212 | 16,724 × $4/M = $0.066896 | 2 × $2/M = $0.000004 | 4 × $10/M = $0.00004 | $0.0723612 |

Two environment facts came out of these runs. A plain `claude -p` here writes one-hour cache entries
although `~/.claude/settings.json` sets no `promptCacheTtl`; I did not find the source (environment
or managed settings). And `~/.claude/settings.json` sets the deprecated
`ANTHROPIC_SMALL_FAST_MODEL` to `claude-sonnet-4-5-20250929[1m]`, so background work and any `/goal`
evaluator on this machine may run on Sonnet 4.5. That is the owner's global setting, not the
skill's, but drive's printed settings do not override it.

## 3. Sources

Fetched as Markdown on 2026-09-14:

- Pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Models overview: https://platform.claude.com/docs/en/about-claude/models/overview
- Model pages: https://platform.claude.com/docs/en/models/fable-5-1/overview, `/opus-5/overview`, `/sonnet-5/overview`, and the "What's new" pages for Fable 5.1, Opus 5, and Sonnet 5
- Effort: https://platform.claude.com/docs/en/build-with-claude/effort
- Prompting guides: `.../prompt-engineering/prompting-claude-fable-5-1`, `prompting-claude-opus-5`, `prompting-claude-sonnet-5`
- API prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Optimizing for cost and intelligence: https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence
- Vision, refusals and fallback, model deprecations (platform docs)
- Claude Code: `model-config`, `sub-agents`, `prompt-caching`, `settings-reference`, `skills`, `context-window`, `workflows`, `commands`, `code-review`, `goal`, `env-vars`, `costs`, `plugin-evals` (all under https://code.claude.com/docs/en/)

## 4. Claims

Status words: **correct**, **wrong**, **stale** (true once, or contradicted by a later change in the
repository), **unverifiable** (not stated in any live source I could fetch).

### 4.1 Model IDs, aliases, and launch commands

| File:line | Claim | Status | Source or note |
|---|---|---|---|
| README.md:55-61 | Three models pinned by full ID; the role split; Haiku and older models never selected | correct | All twelve agent frontmatters read; IDs match the models overview |
| README.md:25 | Orchestrator designed for Fable 5.1 at high effort | correct | Effort page, Fable 5.1: "Start with `high`, the default." |
| README.md:84; long-running.md:123, 140, 161, 173, 218, 223 | Launch passes `--model claude-fable-5-1 --effort high` | correct | model-config: "To pin to a specific version, use the full model name" |
| install.sh:115, 118 | Printed launch commands pass `--model fable` | wrong | Contradicts the owner's ruling and models.md:21-22. The alias resolves to Fable 5.1 today (section 2), but model-config says aliases "update over time" |
| models.md:20-22; SKILL.md:220 | Agent files pin exact IDs; drive uses no other models | correct | Frontmatter of all twelve agents |
| models.md:22-23; SKILL.md:220-222 | The Agent tool's `model` parameter accepts only the aliases `fable`, `opus`, `sonnet` | correct in substance | The tool schema in this session accepts `sonnet`, `opus`, `haiku`, `fable`; drive never passes `haiku` |
| models.md:23-25, 95-96 | Those aliases resolve to the same three models on the Anthropic API | correct | Section 2; model-config provider table ("Anthropic API: Opus 5, Sonnet 5"; `fable` → Fable 5.1) |
| models.md:25-26 | On Bedrock, Google Cloud, or Foundry the IDs may not exist | correct | Overview gives `anthropic.claude-*` IDs on Bedrock; model-config maps `opus` to Opus 4.6 on Foundry |
| models.md:99-104 | Subagent model order since v2.1.251; `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` breaks the roster | correct | sub-agents, "Choose a model" and "Run every subagent on one model" |
| models.md:106-107 | Built-in Explore and Plan inherit the session model | correct | sub-agents: Explore "inherits from the main conversation, capped at Opus" |
| install.sh:89 | `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` overrides every agent's model | correct | sub-agents |
| evals/README.md:136 | The eval pins `claude-fable-5-1` | correct | |
| evals/README.md:142 | It is "the same `claude-fable-5-1` the skill's launch recipes ... use" | stale | install.sh:115, 118 print `fable` |
| evals/README.md:150, 164, 299, 338 | `--judge-model sonnet` replaces the small default judge; `opus` as second opinion | correct | plugin-evals: "The judge ... is a small fast model by default. Pass `--judge-model sonnet`" |
| README.md:76 | Claude Code 2.1.259 or later | stale | Enough for the models (Fable 5.1 needs 2.1.257, Opus 5 2.1.219, Sonnet 5 2.1.197), but models.md:198 relies on effort changes keeping Fable's cache, which prompt-caching dates to v2.1.260 |

### 4.2 Prices and cache prices

| File:line | Claim | Status | Source or note |
|---|---|---|---|
| models.md:31-35 | Fable 5.1 $10 / $50 / read $0.25 / write $12.50 and $20; Opus 5 $5 / $25 / $0.50 / $6.25 and $10; Sonnet 5 $2 / $10 / $0.20 / $2.50 and $4 | correct, all fifteen values | Pricing table; reproduced from billed cost in section 2 |
| models.md:28-29 | Prices as of September 2026 | correct | Pricing note: Sonnet 5's $2 / $10 "is now the standard price" |
| models.md:37 | Fable about twice Opus and five times Sonnet per token; its cache reads half of Opus's | correct | $10/$5, $10/$2, $0.25/$0.50 |
| models.md:38 | "A long-lived Fable context that mostly re-reads itself is cheap" | wrong for budgeting | Cheap per token, but in section 5 cache reads are the orchestrator's largest line (build L: $72 of $156) |
| models.md:52 | Sonnet writes code "at a fifth of Fable's price" | correct | $10 against $50 output |
| models.md:196-197 | The one-hour write rate is higher than the five-minute rate | correct | Pricing: 2x against 1.25x base input |

### 4.3 Roster: model and effort per role

All twelve frontmatter `model` and `effort` values match models.md section 2 and SKILL.md's roster,
and every level used exists on its model (model-config effort table: Fable 5.1, Opus 5, and Sonnet 5
each support `low`, `medium`, `high`, `xhigh`, `max`).

| File:line | Claim | Status | Source or note |
|---|---|---|---|
| models.md:48 | Orchestrator on Fable 5.1 at high | correct | Effort page: Fable 5.1 "Start with `high`, the default" |
| models.md:49 | Researcher on Sonnet 5 at high because research's "quality curve is nearly flat across tiers" | unverifiable | Not in any fetched page. research/06 took it from the bundled claude-api skill, which measured effort levels on one model, not model tiers |
| models.md:50 | Architect at xhigh because "xhigh is Opus's recommended level for demanding agentic work" | stale | Opus 5: "Start with `high`, the default ... step up to `xhigh` for demanding coding and agentic work." "Start with `xhigh`" is the Opus 4.7 and 4.8 guidance |
| models.md:51 | Designer on Opus because literal Sonnet does not infer unwritten requirements | correct | Sonnet 5 prompting: it "does not infer requests you didn't make" |
| models.md:52 | Implementer on Sonnet 5 at high; high avoids the literal narrowing Sonnet shows at low | correct | Sonnet 5: "At `low` and `medium`, the model scopes its work to what was asked" |
| models.md:53 | Writer on Opus 5 at high | correct | Default effort; the prose-quality reason is judgment |
| models.md:54 | Verifier on Opus 5 because a stronger skeptical model is "markedly more tractable" | unverifiable | Not in the fetched sources. Opus 5 prompting supports the choice from another direction: high review precision and recall |
| models.md:55 | Severe tester: "Opus keeps any flag inside the subagent instead of the orchestrator" | wrong | Any subagent keeps a flag out of the orchestrator; Opus 5 runs its own cyber classifier (model-config, "Automatic model fallback") |
| models.md:56 | Security reviewer "runs on Opus from the start rather than on fallback" | wrong | model-config: "Opus 5: cybersecurity-flagged requests re-run on Opus 4.8." Fable 5.1 prompting: "finding vulnerabilities in source code is permitted" |
| models.md:57 | UI reviewer on Opus 5 at high | correct | Opus 5 prompting: strong "on UI and frontend visual replication" |
| models.md:58 | Grader on Sonnet 5 at low | correct, with a caveat | Sonnet 5: `low` is for "short, scoped tasks"; "on moderately complex tasks running at `low` effort there is some risk of under-thinking." Parity-mismatch triage and docs-against-code are the checklist kinds closest to that line; the canary and blind re-grade are the right guard |
| models.md:59 | Investigator on Opus 5 at xhigh | correct | Opus 5 guidance for demanding agentic work |
| models.md:60 | Auditor on Fable 5.1 at xhigh | correct | Effort page: "Step up to `xhigh` or `max` for the most capability-sensitive agentic and coding work." The warning about long deliverables at xhigh barely applies, since a verdict is short |
| models.md:92-93; capabilities.md:323 | Writer story mapping with `model: "fable"` | correct | Alias resolves to Fable 5.1 |
| verification.md:515-520 | Grading table written with aliases and efforts | correct | Matches frontmatter |
| security.md:96 | "Both agents are pinned to `opus`" | wrong in detail | Both pin `claude-opus-5` |
| SKILL.md:8 | Skill frontmatter sets `effort: high` | correct | skills: a skill's `effort` overrides the session level; on Fable 5.1 that keeps the cache |

### 4.4 Cache and effort mechanics

| File:line | Claim | Status | Source or note |
|---|---|---|---|
| models.md:73-76 | SKILL.md sets no model because a skill's model override lasts one turn and rebuilds the cache | correct | skills frontmatter reference; prompt-caching "Switching models" |
| models.md:187-195 | API key or cloud provider: main conversation cache is five minutes; set `promptCacheTtl` "1h" (v2.1.242+) or `CLAUDE_CODE_PROMPT_CACHE_TTL`, which wins; subscriptions already get the hour; confirm with `ephemeral_1h_input_tokens` | correct | prompt-caching TTL table and precedence list; the confirmation field appeared in section 2 |
| models.md:196-197 | Subagents stay at five minutes | correct | prompt-caching: "Everything else (subagents, workflows, compaction): five minutes" |
| models.md:198-199 | "On Fable an effort change keeps the cache; a model change always rebuilds it, and a classifier fallback is a model change" | correct but incomplete | prompt-caching: holds "On Fable 5.1 with an API key or a Claude subscription", not on Bedrock, Google Cloud's Agent Platform, or a Claude apps gateway, and only from v2.1.260 |
| models.md:200-202 | Workflow agents with the same model, effort, type, tools, schema, and directory share a cached prefix; agents in different worktrees do not | worktree part correct; the rest unverifiable | prompt-caching: cache is per directory, "That includes worktrees"; the sharing rule is not in the fetched workflows page |
| models.md:203-204 | Accumulated images force a dropped batch, which invalidates the cache | correct | prompt-caching "Accumulating many images" |
| long-running.md:455-456 | Resuming a session idle more than about an hour repays its whole context | correct | Follows from the one-hour TTL |
| install.sh:5-6 | "Every value a run relies on travels in that run's --settings JSON" | wrong for API-key billing | The envelopes assume a one-hour orchestrator cache, but `DRIVE_SETTINGS` (install.sh:93-101) has no `promptCacheTtl`; long-running.md:108-109 says to add it by hand |

### 4.5 Classifier fallback (safety.md section 1 and related)

| File:line | Claim | Status | Source or note |
|---|---|---|---|
| safety.md:19-22 | Fable 5.1 or Fable 5: cyber → Opus 4.8, bio → Opus 5. Opus 5: cyber → Opus 4.8, bio ends in a refusal | correct | model-config: "Fable 5.1 and Fable 5: biology-flagged requests re-run on Opus 5, and cybersecurity-flagged requests re-run on Opus 4.8. Opus 5: cybersecurity-flagged requests re-run on Opus 4.8. Biology-flagged requests end with a refusal" |
| safety.md:13 | "Fable and Opus 5 run safety classifiers" | correct, incomplete | Sonnet 5 "What's new": "the first Sonnet-tier model with real-time cybersecurity safeguards" (refusal, no Claude Code fallback). Drive's researchers, implementers, and graders run on Sonnet 5 |
| safety.md:14-17 | Fallback re-runs and stays on the fallback model in interactive, background, and headless runs because `switchModelsOnFlag` defaults to true | correct | settings-reference: "Default: `true`"; model-config: "the session continues on the fallback model" |
| safety.md:24-25 | Set false, a headless run ends the flagged request as an error | correct | settings-reference: "where no dialog can show, such as a `-p` run, the flagged request ends as an error" (model-config words it as a refusal) |
| safety.md:28-31 | Flag can fire on the first request from repository context; no fallback when the category has none or `availableModels` blocks the target | correct | model-config, "Check what triggered fallback" |
| safety.md:52-55 | Probe with and without `--safe-mode` and compare `modelUsage` | correct | model-config: `--safe-mode` disables CLAUDE.md, skills, MCP servers, and hooks |
| safety.md:125-128 | Category routing table | correct | model-config names fallbacks only for cyber and bio |
| safety.md:8 | The file covers "the one retry allowed" | stale | Section 6 and SKILL.md:223 say no declined unit is retried on another model |
| safety.md:132-143 | Surface "only when both decline ... a Fable decline followed by an Opus decline"; message says "on both Fable and Opus, including one fresh retry" | stale | Left from the removed Opus 4.8 retry design; contradicts section 6 |
| safety.md:169-170 | Fable 5.1 needs 30-day retention and is unavailable under zero data retention | correct | Fable 5.1 "What's new": "aren't available under zero data retention unless expressly authorized by Anthropic" |
| SKILL.md:301-302 | A flag switches the session automatically and for the rest of the session, headless included | correct | model-config |

### 4.6 Token and size claims

| File:line | Claim | Status | Source or note |
|---|---|---|---|
| models.md:146-148 | Haiku 4.5: 200K window, no effort control, February 2025 cutoff, may retire from 2026-10-15 | correct | Overview: 200K; effort "Not supported"; reliable cutoff Feb 2025; retirement "Not sooner than October 15, 2026" |
| models.md:150-153 | `/goal` and background summaries use the small fast model, Haiku unless `ANTHROPIC_DEFAULT_HAIKU_MODEL` is set; that variable is the only documented override | correct | goal: "defaults to Haiku"; "To evaluate on a different model, set `ANTHROPIC_DEFAULT_HAIKU_MODEL`"; env-vars lists no separate goal-grader variable today |
| long-running.md:440 | Auto-compaction near 967K tokens on 1M models | correct for Sonnet 5; consistent for Fable 5.1 | model-config states "about 967K" for Sonnet 5; local Fable 5.1 transcripts peak between 967K and 1,000K |
| long-running.md:440-442; drive.py:3705 | After compaction each invoked skill keeps its first 5,000 tokens within a shared 25,000 | correct | skills; context-window table |
| long-running.md:443; state-files.md:26 | SKILL.md keeps sections 1 to 6 inside those 5,000 tokens | wrong | Measured: skill Markdown here runs 2.5 characters per token (111,536 characters counted as about 44,300 tokens by a live Sonnet 5 call). Sections 1 to 6 are 16,096 characters, about 6,400 tokens, so the re-attached copy stops before section 6 ends. The re-injection hook re-prints section 6, which limits the harm |
| lessons.md:358; lessons/README.md:11; drive.py:7149-7150 | `general.md` cap of about 4,000 tokens, enforced as characters ÷ 4 | wrong | The check allows 16,000 characters, about 6,400 tokens on the current tokenizer |
| parallel.md:241-243 | Workflow cap of 16 concurrent agents, default size guideline of 15, warning at 25 agents or 1.5M tokens | correct | workflows: "Up to 16 concurrent agents"; default guideline `medium`, "Fewer than 15 agents"; "more than 25 agents, or its projected token total passes 1.5 million" |
| ui-verification.md:195-198 | Review copies at most 2000 px on the long edge, at most fifteen images a session | consistent | vision: above 20 images a stricter 2000 px limit applies |

### 4.7 Dollar figures

| File:line | Claim | Status | Source or note |
|---|---|---|---|
| models.md:163-171 | Cost envelopes per shape and size | wrong (too low) for every cell modelled except `report` M | Section 5 |
| models.md:173 | Add $2 to $5 for a security review at XS or S with `auth` | wrong (low) | The `auth` trait brings a security reviewer and a severe tester: modelled $3 to $9 at XS |
| models.md:177 | Budget line example "$60 to $150" | wrong | Follows the `feature` M envelope |
| models.md:139-141 | A canary costs one item at Sonnet prices; a blind re-grade is a small fraction of the rounds it protects | correct | Unit costs $0.20 (grader) and $1.56 (light verifier) against $3.42 per full verifier round |
| models.md:206-212 | Three biggest sinks: verifier rounds, orchestrator context, implementer output and retries | wrong in part | Recomputed: the orchestrator is the largest single sink, verifier rounds second, UI review third when `ui` applies; Sonnet implementer output is about 5% of a build L run |
| research.md:70-73 | Research budgets: S about $0.30; M $1.50 to $3; L $5 to $12; XL $15 to $40 | S, L, XL correct; M wrong (low) | One Sonnet lane models at $0.71, an Opus reconciliation at $1.78: M with 2 to 4 lanes, reconciliation, and grading is $3.40 to $5.50 |
| evals/README.md:152, 197, 226 | $300 ceiling per arm | unverifiable; arm 1 will probably hit it | Arm 1 is 18 cases × 3 runs = 54 Fable runs with drive; at $4 to $10 each that is $220 to $540. Its own no-plugin column answers "Unknown command" without a model call (evals/README.md:170-171), so it adds nothing. Arm 2 is 54 plain Fable runs of the stripped prompts, cheaper per run, so $300 is a closer fit there. The calibration step at line 226 is the right control |
| evals/README.md:218 | $20 ceiling for one case at one run | correct | Reasonable against $4 to $15 per run |

### 4.8 Excluded models

A repository-wide search of `skill/`, `README.md`, `install.sh`, and `uninstall.sh` for Opus 4.x,
Sonnet 4.x, Haiku, `claude-opus-4`, `claude-sonnet-4`, and `claude-haiku` finds no instruction to
select any of them and no price for any of them. The remaining mentions are allowed or harmless:

| File:line | Mention | Assessment |
|---|---|---|
| safety.md:21-22, 114, 125 | Opus 4.8 as Claude Code's cyber fallback target, and a sample Boundary event | The permitted factual description |
| models.md:6, 144-154 | Why Haiku is never used, and setting `ANTHROPIC_DEFAULT_HAIKU_MODEL` to `claude-sonnet-5` | Exclusion, not selection |
| long-running.md:92, 345 | Moving `/goal` off Haiku | Exclusion |
| README.md:59 | "Haiku and older models are never selected" | Exclusion |
| models.md:221 | "Opus 4.8 where Opus 5 was expected" as an example of a wrong reported model | Detection, not selection; outside safety.md, so a one-word change is listed in section 9 |
| scripts/drive.py:4016 | Comment on "The Opus 4.8 twins" | The known leftover the other agent is removing |
| scripts/tests/test_model_ids.py | Assertions that the removed retry agents are absent | A guard, not a reference |

## 5. Recomputed cost envelopes

### 5.1 Method

**Prices** are the live list prices in section 4.2. Subagents write their cache at the five-minute
rate; the orchestrator writes at the one-hour rate, as models.md assumes. Uncached input is
negligible in Claude Code (two tokens per request in section 2), so a request costs cache reads of
its prefix, cache writes of what is new, and output.

**One agent invocation** is modelled as T requests that start from a context of B tokens and grow by
G tokens per request (tool results plus the previous reply, which becomes input for the next
request), with O output tokens per request, thinking included:

- cache reads = T × B + G × T(T − 1)/2
- cache writes = B + G × (T − 1)
- output = O × T

**The orchestrator** runs N requests over S sessions (fresh sessions or compactions). Each session
starts at 55K tokens (a bare session here measured 44K to 45K in section 2, plus SKILL.md at about
10.5K) plus the references it reads inline, and grows by g per request. With n = N/S:

- average context = 55K + references + g × n/2; end context = 55K + references + g × n
- cache reads = N × average; cache writes = S × end + K × average, where K counts waits longer
  than the one-hour TTL; output = N × output per request

**Tokenizer.** A live Sonnet 5 call counted 111,536 characters of this skill's Markdown as about
44,300 tokens, 2.5 characters per token, the same ratio the models overview gives for the current
tokenizer. `intake.md` alone is about 24K tokens and `verification.md` about 21K, so the orchestrator's
reference reading is 50K to 100K tokens per session.

**Empirical anchors.** No drive run exists yet, so I checked the per-agent profiles against 322
Claude Code subagents and the Fable 5.1 main sessions recorded on this machine since mid-August
(list-price cost computed from each transcript's usage; these are general-purpose and Explore agents,
not drive's roles):

| Sample | n | p25 | Median | p75 | p90 |
|---|---|---|---|---|---|
| Opus 5 subagents | 170 | $1.98 | $3.51 | $6.78 | $10.15 |
| Sonnet 5 subagents | 29 | $0.70 | $1.54 | $4.40 | $7.48 |
| Fable 5.1 subagents | 123 | $2.74 | $4.52 | $7.28 | $10.80 |

Fable 5.1 main sessions with one-hour cache writes produced 350 to 1,500 output tokens per request
and re-read 150K to 550K tokens per request. The closest analogue to a drive run is one session in
the ferrite-labs project that ran 45 subagents: $76 for the Fable orchestrator and $152 for the
subagents, $228 in all.

**What the model counts** comes from the shape files, `verification.md` sections 5, 6, 11, and 13,
`parallel.md` sections 8, 9, and 13, `ui-verification.md` sections 1, 5, and 10, and the intake sizing
table: verification rounds per shape (fix 2; feature and report 3; publish 3 per gated phase; build 3
per milestone plus 2; move 3 per phase and 4 at cutover), a verifier per package and per wave, fresh
verifiers for refutation and blind re-grades, the architect's classification review at M and above,
the auditor's reviews at L and XL, and the final audit.

**Two assumptions I could not verify.** `/code-review` runs as a forked subagent (code-review docs)
and `/simplify` runs "Four review agents" (commands docs); neither page says which model they use.
The model assumes they inherit the session model, Fable 5.1. If they run on Opus instead, subtract
about half their line.

### 5.2 Unit cost per agent invocation

Role names: `_full` is a complete verification round or final-audit checklist; `_light` is a scoped
round two, a refutation, a mechanism confirmation, or a blind re-grade; `_s` is the small-run version;
`implementer_hard` and `researcher_reconcile` are the documented `opus` overrides.

| Role | Model, effort | T | B | G | O | Reads = T·B + G·T(T−1)/2 | Writes = B + G(T−1) | Output = O·T | $ reads | $ writes | $ output | $ total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| researcher_lane | Sonnet 5, high | 15 | 30K | 7.0K | 1.0K | 1.2M | 128K | 15K | 0.24 | 0.32 | 0.15 | **0.71** |
| researcher_reconcile | Opus 5, high | 12 | 30K | 8.0K | 2.0K | 888K | 118K | 24K | 0.44 | 0.74 | 0.60 | **1.78** |
| architect_author | Opus 5, xhigh | 30 | 30K | 7.0K | 3.0K | 3.9M | 233K | 90K | 1.97 | 1.46 | 2.25 | **5.68** |
| architect_author_s | Opus 5, xhigh | 15 | 30K | 6.0K | 2.5K | 1.1M | 114K | 38K | 0.54 | 0.71 | 0.94 | **2.19** |
| architect_review | Opus 5, xhigh | 12 | 30K | 6.0K | 2.5K | 756K | 96K | 30K | 0.38 | 0.60 | 0.75 | **1.73** |
| designer | Opus 5, high | 30 | 35K | 6.0K | 2.0K | 3.7M | 209K | 60K | 1.83 | 1.31 | 1.50 | **4.64** |
| implementer | Sonnet 5, high | 40 | 25K | 3.7K | 1.2K | 3.9M | 169K | 48K | 0.78 | 0.42 | 0.48 | **1.68** |
| implementer_hard | Opus 5, high | 40 | 25K | 3.7K | 1.5K | 3.9M | 169K | 60K | 1.94 | 1.06 | 1.50 | **4.50** |
| writer | Opus 5, high | 20 | 25K | 4.0K | 2.0K | 1.3M | 101K | 40K | 0.63 | 0.63 | 1.00 | **2.26** |
| verifier_full | Opus 5, high | 30 | 25K | 5.0K | 1.2K | 2.9M | 170K | 36K | 1.46 | 1.06 | 0.90 | **3.42** |
| verifier_light | Opus 5, high | 18 | 25K | 4.0K | 1.0K | 1.1M | 93K | 18K | 0.53 | 0.58 | 0.45 | **1.56** |
| severe_tester | Opus 5, high | 35 | 30K | 5.0K | 1.5K | 4.0M | 200K | 52K | 2.01 | 1.25 | 1.31 | **4.58** |
| severe_tester_s | Opus 5, high | 15 | 30K | 4.0K | 1.2K | 870K | 86K | 18K | 0.43 | 0.54 | 0.45 | **1.42** |
| security_reviewer | Opus 5, high | 30 | 30K | 5.5K | 1.2K | 3.3M | 190K | 36K | 1.65 | 1.18 | 0.90 | **3.73** |
| security_reviewer_s | Opus 5, high | 15 | 30K | 4.5K | 1.0K | 922K | 93K | 15K | 0.46 | 0.58 | 0.38 | **1.42** |
| ui_reviewer (one session) | Opus 5, high | 40 | 30K | 6.0K | 1.0K | 5.9M | 264K | 40K | 2.94 | 1.65 | 1.00 | **5.59** |
| grader | Sonnet 5, low | 10 | 20K | 2.5K | 0.3K | 312K | 42K | 3K | 0.06 | 0.11 | 0.03 | **0.20** |
| grader_citations | Sonnet 5, low | 25 | 20K | 5.0K | 0.3K | 2.0M | 140K | 8K | 0.40 | 0.35 | 0.07 | **0.82** |
| investigator | Opus 5, xhigh | 45 | 28K | 6.5K | 2.5K | 7.7M | 314K | 112K | 3.85 | 1.96 | 2.81 | **8.62** |
| investigator_s | Opus 5, xhigh | 25 | 28K | 6.0K | 2.5K | 2.5M | 172K | 62K | 1.25 | 1.07 | 1.56 | **3.89** |
| auditor_final | Fable 5.1, xhigh | 40 | 30K | 7.5K | 2.5K | 7.0M | 322K | 100K | 1.76 | 4.03 | 5.00 | **10.79** |
| auditor_review | Fable 5.1, xhigh | 15 | 30K | 6.0K | 2.0K | 1.1M | 114K | 30K | 0.27 | 1.43 | 1.50 | **3.20** |
| code_review | Fable 5.1 (assumed) | 25 | 45K | 5.0K | 1.0K | 2.6M | 165K | 25K | 0.66 | 2.06 | 1.25 | **3.97** |
| simplify (four agents) | Fable 5.1 (assumed) | 15 each | 40K | 4.0K | 0.8K | 1.0M each | 96K each | 12K each | 0.26 × 4 | 1.20 × 4 | 0.60 × 4 | **8.22** |

These sit where the empirical sample says they should: the full verifier round ($3.42) at the Opus
median, the light verifier ($1.56) below the Opus p25, the implementer ($1.68) at the Sonnet median,
the xhigh investigator ($8.62) near the Opus p75, and the xhigh final audit ($10.79) above the Fable
p75.

### 5.3 Image tokens in UI review

A review copy is at most 2000 px on its long edge (`ui-verification.md` section 5). A phone
screenshot of 1179 × 2556 scaled to 923 × 2000 costs ⌈923/28⌉ × ⌈2000/28⌉ = 33 × 72 = 2,376 visual
tokens under the vision page's formula; a square 2000 × 2000 capture reaches the 4,784-token cap. At
fifteen phone images a session that is about 35.6K tokens: writing them costs 35.6K × $6.25/M = $0.22,
and re-reading them for about twenty later requests 35.6K × 20 × $0.50/M = $0.36. Pixels are about
$0.60 of the $5.59 session; the turns, accessibility trees, and objective-check output are the rest.
The screenshot matrix matters through the number of sessions it forces, not the image price.

### 5.4 fix M

| Role | Count (low / typical / high) | Unit $ | Typical $ |
|---|---|---|---|
| researcher_lane (archaeology) | 1 / 2 / 3 | 0.71 | 1.41 |
| architect_review (classification) | 1 / 1 / 1 | 1.73 | 1.73 |
| investigator (reproduce, diagnose, arms) | 1 / 2 / 3 | 8.62 | 17.25 |
| severe_tester (frozen reproducer, harden) | 2 / 2 / 3 | 4.58 | 9.15 |
| implementer_hard (a bug fix is marked hard) | 1 / 1 / 2 | 4.50 | 4.50 |
| verifier_full (round one, final-audit checklist) | 2 / 2 / 3 | 3.42 | 6.85 |
| verifier_light (confirmation, sibling sweep, round two, harden exit) | 2 / 4 / 6 | 1.56 | 6.25 |
| code_review (medium) | 1 / 1 / 2 | 3.97 | 3.97 |
| grader (lesson dedupe) | 1 / 1 / 2 | 0.20 | 0.20 |
| auditor_review (lesson verification) | 0 / 1 / 1 | 3.20 | 3.20 |
| **subagents** | 12 / 17 / 26 invocations | | **54.50** |

| Orchestrator (one session, references 60K, g 1.2K, 800 output per request) | Low | Typical | High |
|---|---|---|---|
| requests N | 90 | 150 | 240 |
| end / average context | 223K / 169K | 295K / 205K | 403K / 259K |
| cache reads = N × average | 15.2M × $0.25 = $3.80 | 30.8M × $0.25 = $7.69 | 62.2M × $0.25 = $15.54 |
| cache writes = end + K × average | 223K × $20 = $4.46 | 295K × $20 = $5.90 | 662K × $20 = $13.24 |
| output | 72K × $50 = $3.60 | 120K × $50 = $6.00 | 192K × $50 = $9.60 |
| orchestrator | $11.86 | $19.59 | $38.38 |
| subagents (counts × unit) | $38.85 | $54.50 | $83.62 |
| **run** | **$51** | **$74** | **$122** |

Published $15 to $40: too low. Even the low case, one investigator and no lesson, is above the top.

### 5.5 feature M

| Role | Count (low / typical / high) | Unit $ | Typical $ |
|---|---|---|---|
| researcher_lane | 2 / 3 / 4 | 0.71 | 2.12 |
| architect_author (spec, design delta, test plan, decomposition) | 3 / 4 / 5 | 5.68 | 22.71 |
| architect_review (classification, spec, design, test plan) | 3 / 4 / 5 | 1.73 | 6.91 |
| designer (extracted contract) | 1 / 1 / 1 | 4.64 | 4.64 |
| implementer | 3 / 4 / 5 | 1.68 | 6.72 |
| implementer_hard | 1 / 1 / 2 | 4.50 | 4.50 |
| verifier_full (five packages, wave seams) | 6 / 7 / 10 | 3.42 | 23.97 |
| verifier_light (rounds two and three, refutations, re-grade) | 3 / 6 / 10 | 1.56 | 9.37 |
| severe_tester (refutation tests before build, harden) | 2 / 2 / 3 | 4.58 | 9.15 |
| ui_reviewer (live capture, harden rounds) | 2 / 3 / 4 | 5.59 | 16.77 |
| security_reviewer | 0 / 0 / 1 | 3.73 | 0.00 |
| grader (test-plan rows, conformance, docs, baseline) | 3 / 4 / 5 | 0.20 | 0.80 |
| writer | 1 / 1 / 2 | 2.26 | 2.26 |
| code_review (high) | 1 / 1 / 2 | 3.97 | 3.97 |
| simplify | 1 / 1 / 1 | 8.22 | 8.22 |
| auditor_final (five or more claims) | 1 / 1 / 1 | 10.79 | 10.79 |
| auditor_review | 0 / 0 / 1 | 3.20 | 0.00 |
| **subagents** | 33 / 43 / 62 invocations | | **132.91** |

| Orchestrator (one session, references 80K, g 1.3K, 800 output per request) | Low | Typical | High |
|---|---|---|---|
| requests N (re-writes K) | 150 (0) | 250 (1) | 400 (2) |
| end / average context | 330K / 232K | 460K / 298K | 655K / 395K |
| cache reads | 34.9M × $0.25 = $8.72 | 74.4M × $0.25 = $18.59 | 158.0M × $0.25 = $39.50 |
| cache writes | 330K × $20 = $6.60 | 758K × $20 = $15.15 | 1.4M × $20 = $28.90 |
| output | 120K × $50 = $6.00 | 200K × $50 = $10.00 | 320K × $50 = $16.00 |
| orchestrator | $21.32 | $43.74 | $84.40 |
| subagents | $109.22 | $132.91 | $187.25 |
| **run** | **$131** | **$177** | **$272** |

Published $60 to $150: too low. The intake table's own count (about thirty subagents for an
ordinary M feature, before review extras) already costs more than $60.

### 5.6 build L

| Role | Count (low / typical / high) | Unit $ | Typical $ |
|---|---|---|---|
| researcher_lane | 5 / 7 / 10 | 0.71 | 4.95 |
| researcher_reconcile | 1 / 1 / 2 | 1.78 | 1.78 |
| grader_citations | 1 / 1 / 2 | 0.82 | 0.82 |
| architect_author (capability map, spec, design per surface, contract, test plan, decomposition) | 5 / 6 / 8 | 5.68 | 34.07 |
| architect_review (classification) | 1 / 1 / 1 | 1.73 | 1.73 |
| auditor_review (spec, design, test plan, lesson) | 3 / 4 / 6 | 3.20 | 12.78 |
| designer | 1 / 1 / 2 | 4.64 | 4.64 |
| implementer | 6 / 10 / 16 | 1.68 | 16.80 |
| implementer_hard | 1 / 2 / 4 | 4.50 | 9.00 |
| verifier_full (twelve packages, seams, integrate, live proof) | 10 / 17 / 26 | 3.42 | 58.22 |
| verifier_light (later rounds, refutations, re-grades, two panel lenses per sampled claim) | 18 / 34 / 50 | 1.56 | 53.12 |
| grader (conformance, test plan, docs, dedupe, panel evidence lens) | 8 / 15 / 20 | 0.20 | 2.98 |
| severe_tester | 3 / 5 / 8 | 4.58 | 22.88 |
| security_reviewer | 1 / 2 / 3 | 3.73 | 7.46 |
| ui_reviewer (screen batches × rounds, live capture) | 6 / 10 / 16 | 5.59 | 55.90 |
| writer | 2 / 2 / 3 | 2.26 | 4.52 |
| code_review | 1 / 2 / 3 | 3.97 | 7.94 |
| simplify | 1 / 1 / 2 | 8.22 | 8.22 |
| auditor_final | 1 / 1 / 2 | 10.79 | 10.79 |
| **subagents** | 75 / 122 / 184 invocations | | **318.61** |

| Orchestrator (references 100K per session, g 1.1K, 800 output per request) | Low | Typical | High |
|---|---|---|---|
| requests N / sessions S / re-writes K | 540 / 2 / 1 | 900 / 3 / 3 | 1,440 / 4 / 6 |
| end / average context per session | 452K / 304K | 485K / 320K | 551K / 353K |
| cache reads | 163.9M × $0.25 = $40.97 | 288.0M × $0.25 = $72.00 | 508.3M × $0.25 = $127.08 |
| cache writes | 1.2M × $20 = $24.15 | 2.4M × $20 = $48.30 | 4.3M × $20 = $86.44 |
| output | 432K × $50 = $21.60 | 720K × $50 = $36.00 | 1.2M × $50 = $57.60 |
| orchestrator | $86.72 | $156.30 | $271.12 |
| subagents | $207.53 | $318.61 | $497.86 |
| **run** | **$294** | **$475** | **$769** |

Published $200 to $400: too low, and the typical run is above the top.

### 5.7 build XL

| Role | Count (low / typical / high) | Unit $ | Typical $ |
|---|---|---|---|
| researcher_lane (Workflow sweeps) | 12 / 20 / 30 | 0.71 | 14.14 |
| researcher_reconcile | 2 / 2 / 3 | 1.78 | 3.56 |
| grader_citations | 2 / 2 / 4 | 0.82 | 1.65 |
| architect_author | 8 / 10 / 14 | 5.68 | 56.79 |
| architect_review | 1 / 1 / 1 | 1.73 | 1.73 |
| auditor_review (per-surface reviews, re-classification at every gate, lessons) | 9 / 14 / 20 | 3.20 | 44.73 |
| auditor_final (mid-run audit after the skeleton, final) | 2 / 2 / 3 | 10.79 | 21.59 |
| designer | 1 / 2 / 3 | 4.64 | 9.27 |
| implementer | 16 / 24 / 36 | 1.68 | 40.33 |
| implementer_hard | 3 / 6 / 10 | 4.50 | 27.01 |
| verifier_full | 26 / 38 / 55 | 3.42 | 130.15 |
| verifier_light | 40 / 70 / 100 | 1.56 | 109.36 |
| grader | 20 / 33 / 45 | 0.20 | 6.56 |
| severe_tester | 6 / 10 / 15 | 4.58 | 45.75 |
| security_reviewer | 2 / 3 / 5 | 3.73 | 11.19 |
| ui_reviewer | 12 / 20 / 32 | 5.59 | 111.80 |
| writer | 3 / 4 / 6 | 2.26 | 9.04 |
| code_review | 2 / 4 / 6 | 3.97 | 15.88 |
| simplify | 1 / 2 / 3 | 8.22 | 16.44 |
| **subagents** | 168 / 267 / 391 invocations | | **676.96** |

| Orchestrator (references 100K per session, g 1.1K, 800 output per request) | Low | Typical | High |
|---|---|---|---|
| requests N / sessions S / re-writes K | 1,200 / 4 / 3 | 2,000 / 6 / 6 | 3,200 / 9 / 12 |
| end / average context per session | 485K / 320K | 522K / 338K | 546K / 351K |
| cache reads | 384.0M × $0.25 = $96.00 | 676.7M × $0.25 = $169.17 | 1,121.8M × $0.25 = $280.44 |
| cache writes | 2.9M × $20 = $58.00 | 5.2M × $20 = $103.20 | 9.1M × $20 = $182.43 |
| output | 960K × $50 = $48.00 | 1.6M × $50 = $80.00 | 2.6M × $50 = $128.00 |
| orchestrator | $202.00 | $352.37 | $590.88 |
| subagents | $436.67 | $676.96 | $1,008.52 |
| **run** | **$639** | **$1,029** | **$1,599** |

Published $400 to $600, up to $1,000 on a bad run: too low. The typical run lands at the published
bad-run figure. The orchestrator line is consistent with this machine's longest Fable 5.1 sessions
on a one-hour cache (2,130 requests for $459; 1,441 requests for $396).

### 5.8 move L

| Role | Count (low / typical / high) | Unit $ | Typical $ |
|---|---|---|---|
| researcher_lane (archaeology, inventory) | 3 / 4 / 6 | 0.71 | 2.83 |
| researcher_reconcile | 1 / 1 / 1 | 1.78 | 1.78 |
| architect_author (charter, stage plan, decomposition) | 2 / 3 / 4 | 5.68 | 17.04 |
| architect_review | 1 / 1 / 1 | 1.73 | 1.73 |
| auditor_review (design, lesson) | 1 / 2 / 3 | 3.20 | 6.39 |
| severe_tester (characterization, harden) | 1 / 2 / 3 | 4.58 | 9.15 |
| implementer (recorder, new implementation, call-site moves) | 5 / 8 / 12 | 1.68 | 13.44 |
| implementer_hard (seam) | 1 / 2 / 3 | 4.50 | 9.00 |
| verifier_full (inventory, characterize, packages, parity and operability lenses, cutover stages, soak reads, decommission) | 14 / 21 / 30 | 3.42 | 71.92 |
| verifier_light | 5 / 9 / 15 | 1.56 | 14.06 |
| grader (mismatch triage, conformance, docs) | 5 / 7 / 10 | 0.20 | 1.39 |
| security_reviewer | 0 / 1 / 1 | 3.73 | 3.73 |
| writer | 1 / 1 / 2 | 2.26 | 2.26 |
| code_review | 1 / 1 / 2 | 3.97 | 3.97 |
| simplify (after cutover) | 0 / 1 / 1 | 8.22 | 8.22 |
| auditor_final | 1 / 1 / 2 | 10.79 | 10.79 |
| **subagents** | 42 / 65 / 96 invocations | | **177.71** |

| Orchestrator (references 100K per session, g 1.1K, 800 output per request) | Low | Typical | High |
|---|---|---|---|
| requests N / sessions S / re-writes K (soak waits) | 420 / 2 / 3 | 700 / 3 / 6 | 1,120 / 5 / 12 |
| end / average context per session | 386K / 270K | 412K / 283K | 401K / 278K |
| cache reads | 113.6M × $0.25 = $28.40 | 198.3M × $0.25 = $49.58 | 311.6M × $0.25 = $77.90 |
| cache writes | 1.6M × $20 = $31.67 | 2.9M × $20 = $58.70 | 5.3M × $20 = $106.91 |
| output | 336K × $50 = $16.80 | 560K × $50 = $28.00 | 896K × $50 = $44.80 |
| orchestrator | $76.87 | $136.28 | $229.60 |
| subagents | $111.44 | $177.71 | $261.61 |
| **run** | **$188** | **$314** | **$491** |

Published $100 to $300: too low at both ends. Soak waits longer than an hour make cache re-writes a
larger share here than in any other shape.

### 5.9 publish L

| Role | Count (low / typical / high) | Unit $ | Typical $ |
|---|---|---|---|
| researcher_lane (report sub-goal) | 5 / 8 / 10 | 0.71 | 5.66 |
| researcher_reconcile | 1 / 1 / 2 | 1.78 | 1.78 |
| grader_citations | 1 / 2 / 3 | 0.82 | 1.65 |
| architect_author (content plan) | 1 / 1 / 2 | 5.68 | 5.68 |
| architect_review | 1 / 1 / 1 | 1.73 | 1.73 |
| auditor_review (design, lesson) | 1 / 2 / 3 | 3.20 | 6.39 |
| designer | 1 / 1 / 1 | 4.64 | 4.64 |
| implementer (layouts, docs structure, blog, gates) | 4 / 6 / 8 | 1.68 | 10.08 |
| implementer_hard (tokens and layout) | 1 / 1 / 2 | 4.50 | 4.50 |
| writer (report, page drafts, revision passes) | 8 / 12 / 18 | 2.26 | 27.13 |
| verifier_full (adversarial reader, build, design-qa, deploy gates, claims audit, docs smoke, live) | 5 / 8 / 11 | 3.42 | 27.40 |
| verifier_light | 4 / 8 / 12 | 1.56 | 12.50 |
| grader | 3 / 5 / 7 | 0.20 | 0.99 |
| ui_reviewer (design-qa, preview, production matrices, round two) | 4 / 7 / 10 | 5.59 | 39.13 |
| severe_tester (forms) | 1 / 1 / 2 | 4.58 | 4.58 |
| code_review | 1 / 1 / 1 | 3.97 | 3.97 |
| auditor_final | 1 / 1 / 2 | 10.79 | 10.79 |
| **subagents** | 43 / 66 / 95 invocations | | **168.60** |

| Orchestrator (references 90K per session, g 1.1K, 800 output per request) | Low | Typical | High |
|---|---|---|---|
| requests N / sessions S / re-writes K | 360 / 1 / 1 | 600 / 2 / 2 | 960 / 3 / 4 |
| end / average context per session | 541K / 343K | 475K / 310K | 497K / 321K |
| cache reads | 123.5M × $0.25 = $30.87 | 186.0M × $0.25 = $46.50 | 308.2M × $0.25 = $77.04 |
| cache writes | 884K × $20 = $17.68 | 1.6M × $20 = $31.40 | 2.8M × $20 = $55.50 |
| output | 288K × $50 = $14.40 | 480K × $50 = $24.00 | 768K × $50 = $38.40 |
| orchestrator | $62.95 | $101.90 | $170.94 |
| subagents | $116.36 | $168.60 | $251.98 |
| **run** | **$179** | **$270** | **$423** |

Published $100 to $200: too low.

### 5.10 report M

| Role | Count (low / typical / high) | Unit $ | Typical $ |
|---|---|---|---|
| researcher_lane | 4 / 8 / 10 | 0.71 | 5.66 |
| researcher_reconcile | 1 / 2 / 3 | 1.78 | 3.56 |
| grader_citations | 1 / 1 / 2 | 0.82 | 0.82 |
| grader (draft tracing) | 1 / 1 / 2 | 0.20 | 0.20 |
| architect_review | 1 / 1 / 1 | 1.73 | 1.73 |
| writer | 1 / 1 / 2 | 2.26 | 2.26 |
| verifier_full (adversarial reader) | 1 / 1 / 2 | 3.42 | 3.42 |
| verifier_light (verdict verifier, final-audit checklist) | 2 / 2 / 4 | 1.56 | 3.12 |
| **subagents** | 12 / 17 / 26 invocations | | **20.78** |

| Orchestrator (one session, references 50K, g 1.0K, 800 output per request) | Low | Typical | High |
|---|---|---|---|
| requests N | 60 | 100 | 160 |
| end / average context | 165K / 135K | 205K / 155K | 265K / 185K |
| cache reads | 8.1M × $0.25 = $2.02 | 15.5M × $0.25 = $3.88 | 29.6M × $0.25 = $7.40 |
| cache writes | 165K × $20 = $3.30 | 205K × $20 = $4.10 | 450K × $20 = $9.00 |
| output | 48K × $50 = $2.40 | 80K × $50 = $4.00 | 128K × $50 = $6.40 |
| orchestrator | $7.72 | $11.97 | $22.80 |
| subagents | $16.17 | $20.78 | $33.81 |
| **run** | **$24** | **$33** | **$57** |

Published $15 to $50: reasonable. The bottom is a little low and the top covers the typical run.

### 5.11 Small runs

| Run | Subagents (typical) | Orchestrator (typical) | Low | Typical | High | Published |
|---|---|---|---|---|---|---|
| fix XS | none | 30 requests, end 110K: 2.6M × $0.25 + 110K × $20 + 21K × $50 = $3.91 | $3 | $4 | $6 | under $3 |
| fix XS with `auth` gates | security_reviewer_s $1.42 + severe_tester_s $1.42 | 35 requests: $4.52 | $6 | $7 | $9 | under $3, plus $2 to $5 |
| fix S | researcher 0.71 + investigator_s 3.89 + implementer_hard 4.50 + verifier_full 3.42 + 2 × verifier_light 3.12 + severe_tester_s 1.42 = $17.07 | 70 requests, end 179K: $8.78 | $21 | $26 | $39 | $5 to $15 |
| feature S | researcher 0.71 + architect_author_s 2.19 + architect_review 1.73 + implementer 1.68 + verifier_full 3.42 + 2 × verifier_light 3.12 + severe_tester_s 1.42 + grader 0.20 + writer 2.26 + code_review 3.97 + simplify 8.22 = $28.93 | 80 requests, end 196K: $10.08 | $32 | $39 | $49 | $10 to $30 |

At XS the orchestrator's first one-hour write of a 55K to 110K context costs $1.10 to $2.20 on its
own, which is why "under $3" does not hold. A five-minute write would save about $0.80 on a run that
short.

### 5.12 Why the research derivation came out low

research/06 section 4.4 got its arithmetic right and its inputs low. It priced two or three Opus
xhigh investigators at $1.50 each and a two-round verifier at $3 in total; the empirical Opus median
is $3.51 per invocation, and a 45-request xhigh investigation models at $8.62. Its bug hunt gave the
orchestrator 40 requests, where drive's own procedure (probe, `init`, preflight, capabilities, state
writes, briefs, handoffs, gates, lint, commits) needs something over a hundred at M. And the roster
has grown since: the final audit is a Fable xhigh call in every `build`, `move`, and `fix/incident`,
severe tests are written before implementation at M and above, `/code-review` and `/simplify` run on
the session model, UI review runs per screen batch and per round, and the review panel adds three
lenses per sampled claim at L.

### 5.13 Proposed section 7 table

(m) marks a modelled cell. (e) marks an extrapolation from the published figure by the ratio the
modelled cells show at that size, about two at XS to M and one and a half to two at L and XL;
recompute those before quoting them.

| Shape | XS | S | M | L | XL |
|---|---|---|---|---|---|
| `fix` | $3 to $6 (m) | $20 to $40 (m) | $50 to $120 (m) | $90 to $200 (e) | reclassify |
| `feature` | $3 to $6 (e) | $30 to $50 (m) | $130 to $270 (m) | $300 to $550 (e) | $600 to $1,100 (e) |
| `build` | not used | $30 to $80 (e) | $130 to $270 (e) | $300 to $750 (m) | $650 to $1,600 (m), more on a bad run |
| `move` | $5 to $10 (e) | $30 to $80 (e) | $110 to $270 (e) | $190 to $490 (m) | $500 to $1,000 (e) |
| `publish` | $3 to $6 (e) | $20 to $60 (e) | $80 to $240 (e) | $180 to $420 (m) | $350 to $700 (e) |
| `report` | $3 to $6 (e) | $10 to $40 (e) | $25 to $60 (m) | $75 to $180 (e) | $180 to $380 (e) |
| `operate` | $3 to $6 (e) | $10 to $40 (e) | $30 to $100 (e) | $75 to $180 (e) | reclassify |

The first real runs should replace these. The headless recipe already records `total_cost_usd`; a
background run's cost is in `/usage`.

## 6. Effort and cache findings

**Effort levels are supported and mostly well chosen.** Every level in the roster exists on its
model. The orchestrator at high and the auditor at xhigh follow Fable 5.1's guidance ("Start with
`high`" and "Step up to `xhigh` or `max` for the most capability-sensitive agentic and coding work").
The architect and investigator at xhigh follow Opus 5's "step up to `xhigh` for demanding coding and
agentic work", but the stated reason is the older Opus 4.7 and 4.8 wording. Two costs of the choices
are worth knowing. The architect's classification and document reviews are short read-and-judge
tasks, and the effort page describes xhigh as for "Long-running agentic and coding tasks (over 30
minutes)"; because the Agent tool has no effort parameter, running reviews at high would need a
separate agent file, so this is an option rather than a correction. And Sonnet 5's guidance says to
raise effort to xhigh "for the hardest coding and agentic tasks", while drive escalates hard packages
to Opus 5 at high; Sonnet 5 at xhigh ($10 per million output) is an untested alternative to Opus 5 at
high ($25).

**The grader at low is inside Sonnet 5's guidance with a known edge.** Low is for "short, scoped
tasks", and the guide warns of "some risk of under-thinking" on moderately complex ones. Binary
assertions against evidence qualify; parity-mismatch triage and docs-against-code are the kinds
nearest the edge. The canary and blind re-grade in `verification.md` section 11 are the right
instruments, and the retro's agreement counts are the evidence to watch.

**Fable 5.1 cache reads cost $0.25 per million, 2.5% of input.** Confirmed on the pricing page and
in billed cost. One-hour writes cost 2x input ($20, $10, $4) and five-minute writes 1.25x ($12.50,
$6.25, $2.50).

**The one-hour orchestrator cache is the right default for drive, with one caveat from the cost
page.** Anthropic measured that on Fable 5.1 "Keeping the 5-minute cache warm cost 13% to 20% less
per session than the 1-hour cache whenever pauses ran for minutes." That keep-alive is a
`max_tokens: 0` request sent every four minutes, which an API harness can send and Claude Code does
not document doing. Without it, drive's choice is between five-minute and one-hour writes, and there
the arithmetic favours the hour: the one-hour premium on a `feature` M orchestrator is about
460K × ($20 − $12.50)/M = $3.45 for the whole run, while one missed five-minute cache on a 300K
context costs 300K × $12.50/M = $3.75. One wait over five minutes repays the premium. What does not
hold is that the setting travels with the run: `install.sh`'s printed `DRIVE_SETTINGS` omits
`promptCacheTtl`, so an API-key run launched from those printed commands gets five minutes unless the
owner adds it.

**Effort changes and the cache.** On Fable 5.1 an effort change keeps the cache only with an API key
or a Claude subscription, on Claude Code 2.1.260 or later, and not on Bedrock, Google Cloud's Agent
Platform, or a Claude apps gateway. On Opus 5 and Sonnet 5 an effort change in Claude Code rebuilds
the cache. None of drive's subagents change effort mid-conversation, so this matters only for the
orchestrator, which models.md already tells to hold effort constant.

**Opus 5 and Sonnet 5 prompting guidance agrees with drive's review prompts.** Both guides say that
"only report high-severity issues" makes the model under-report and that a review should report
everything with confidence and severity and filter later, which `models.md` section 5 already
requires. Opus 5's guide also says explicit "verify your work" instructions cause over-verification;
SKILL.md section 6 already forbids telling a maker to double-check.

## 7. Classifier fallback findings

`safety.md` section 1's table matches model-config: a flagged Fable 5.1 (or
Fable 5) request re-runs on Opus 4.8 for cyber and on Opus 5 for biology; a flagged Opus 5 request
re-runs on Opus 4.8 for cyber and ends in a refusal for biology, "because Opus 5 runs its own biology
classifiers with no fallback model." Category-based fallback needs Claude Code 2.1.219, below the
README's minimum. Two gaps: Sonnet 5 also has "real-time cybersecurity safeguards" that refuse with no
documented Claude Code fallback, which affects the Sonnet-pinned researcher, implementer, and grader;
and the reasons in `models.md` section 2 for the severe tester and security reviewer read as though
Opus 5 avoids the cyber classifier, when routing that work to Opus 5 only keeps a flag out of the
orchestrator.

## 8. Limits of this audit

The model's request counts, context growth, and roster counts per shape are estimates from the
procedure, not measurements of drive, because no drive run exists. The per-agent costs agree with
322 real subagents on this machine, but those were general-purpose and Explore agents. The models
behind `/code-review` and `/simplify` are not documented; the model assumes the session model. The
accessibility-tree size per UI cell is unknown and folded into the UI reviewer's growth figure. The
envelopes in section 5.13 marked (e) are extrapolations. The eval ceiling estimate depends on how far
each case runs before it ends.

## 9. Corrections

Line numbers are as of commit a371046 plus the working tree on 2026-09-14. `scripts/drive.py` is being
edited by another agent, so its line numbers may shift.

| File:line | Current text | Corrected text |
|---|---|---|
| install.sh:115 | `claude --bg --name drive-<slug> --model fable --effort high --permission-mode auto --settings "\$DRIVE_SETTINGS" "/drive <goal>"` | `claude --bg --name drive-<slug> --model claude-fable-5-1 --effort high --permission-mode auto --settings "\$DRIVE_SETTINGS" "/drive <goal>"` |
| install.sh:118 | `env CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=10800000 claude -p "/drive <goal>" --model fable --effort high \\` | `env CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=10800000 claude -p "/drive <goal>" --model claude-fable-5-1 --effort high \\` |
| install.sh:100 (insert after) | `    "worktree": {"bgIsolation": "none"},` | `    "worktree": {"bgIsolation": "none"},` followed by a new line `    "promptCacheTtl": "1h",` |
| README.md:89-90 | `` `none`, and the skill repository under `additionalDirectories` so lesson commits can write there. `` | `` `none`, the one-hour prompt cache for the main conversation, and the skill repository under `additionalDirectories` so lesson commits can write there. `` |
| README.md:76 | `Requirements: Claude Code 2.1.259 or later` | `Requirements: Claude Code 2.1.260 or later` |
| models.md:37-38 | `A long-lived Fable context that mostly re-reads itself is cheap; Fable writing code is not.` | `A Fable context that re-reads itself is cheap per token, but at 300K to 500K tokens re-read on every request, cache reads are still the orchestrator's largest cost; Fable writing code is expensive on every count.` |
| models.md:49 | `Breadth research is output-heavy, its quality curve is nearly flat across tiers, and independent lanes matter more than depth.` | `Breadth research is output-heavy, and independent lanes matter more than depth.` |
| models.md:50 | `and xhigh is Opus's recommended level for demanding agentic work.` | `and Opus 5's guidance is to step up from high to xhigh for demanding coding and agentic work.` |
| models.md:55 | `Adversarial, tool-heavy testing sits close to the cyber classifier, and Opus keeps any flag inside the subagent instead of the orchestrator.` | `Adversarial, tool-heavy testing sits close to the cyber classifier; as a subagent it keeps any flag out of the orchestrator, though Opus 5 runs a cyber classifier too (safety.md section 1).` |
| models.md:56 | `Security analysis is where Fable's classifiers fire most often, so it runs on Opus from the start rather than on fallback.` | `Security analysis is where the classifiers fire most often, so it runs in its own subagent, away from the orchestrator; Opus 5 is not exempt, and a cyber flag there is still a fallback event (safety.md section 1).` |
| models.md:159-161 | `are order-of-magnitude estimates from a cost model at September 2026 prices, assuming the roster above, a one-hour orchestrator cache, and the round limits in SKILL.md. They are not quotes; a run with many escalations can exceed them.` | `are estimates from a cost model recomputed on 2026-09-14 at September 2026 prices, assuming the roster above, a one-hour orchestrator cache, and the round limits in SKILL.md. They are not quotes; a run with more packages, rounds, or UI screens than the typical case lands above them.` |
| models.md:163-171 | The envelope table | The table in section 5.13 of this report, without the (m) and (e) marks |
| models.md:173 | `Add $2 to $5 for a security review on an XS or S run with the `auth` trait.` | `Add $3 to $10 for the security review and severe tests that the `auth` trait brings to an XS or S run.` |
| models.md:177 | `` (`budget: 40 turns · 40 subagents · 3 h · $60 to $150`) `` | `` (`budget: 40 turns · 40 subagents · 3 h · $130 to $270`) `` |
| models.md:198-199 | `On Fable an effort change keeps the cache; a model change always rebuilds it,` | `On Fable 5.1 with an API key or a Claude subscription (Claude Code 2.1.260 or later, not on Bedrock, Google Cloud, or a Claude apps gateway), an effort change keeps the cache; a model change always rebuilds it,` |
| models.md:210-212 | Rows in the order Verifier rounds, Orchestrator context, Implementer output and retries; the orchestrator row's "Why it grows" is `Fable cache writes and output across a long run.` | Rows in the order Orchestrator context, Verifier rounds, UI review. Orchestrator "Why it grows": `Fable cache reads, writes, and output across a long run; reads are the largest part.` New third row: `UI review` / `Each screen batch is a fresh Opus context that captures, reads trees and images, and judges, and each round repeats it.` / `Objective checks before vision, at most fifteen images a session, round two limited to affected screens and their neighbours.` Keep the implementer bounds as a sentence after the table |
| models.md:221 | `(for example Opus 4.8 where Opus 5 was expected, or Opus where Fable was` | `(for example a fallback model where Opus 5 was expected, or Opus where Fable was` |
| safety.md:8 | `decline from a real error, the one retry allowed, what gets logged and surfaced, and the boundaries` | `decline from a real error, why a declined unit is never retried on another model, what gets logged and surfaced, and the boundaries` |
| safety.md:13 | `Fable and Opus 5 run safety classifiers.` | `Fable and Opus 5 run the safety classifiers that trigger Claude Code's model fallback, and Sonnet 5 has real-time cybersecurity safeguards that refuse with no fallback.` |
| safety.md:132 | `## 9. Surface once, only when both decline` | `## 9. Surface once` |
| safety.md:134-136 | `Surface a boundary to the owner only when the work has declined on both tiers: a Fable decline followed by an Opus decline, any refusal result from a subagent, or a category the table routes to surfacing.` | `Surface a boundary to the owner for any refusal result from a subagent, any fallback that switched the orchestrator, or a category the table routes to surfacing.` |
| safety.md:140-141 | `was declined by the model safety classifier (<category>) on both Fable and Opus, including one fresh retry.` | `was declined by the model safety classifier (<category>) on <model>, and drive does not retry a declined unit on another model.` |
| security.md:96 | ``Both agents are pinned to `opus` and preload`` | ``Both agents are pinned to `claude-opus-5` and preload`` |
| long-running.md:442-443 | `SKILL.md keeps sections 1 to 6 inside those 5,000 tokens, and the SessionStart hook` | `SKILL.md's sections 1 to 6 run to about 6,400 tokens, so the re-attached copy stops before section 6 ends, and the SessionStart hook` |
| state-files.md:26 | `the first ~5,000 tokens of SKILL.md, which hold sections 1 to 6,` | `the first ~5,000 tokens of SKILL.md, which stop before the end of section 6,` |
| lessons.md:358 | `` `general.md`: 60 entries or about 4,000 tokens, whichever comes first. `` | `` `general.md`: 60 entries or 16,000 characters (about 6,400 tokens), whichever comes first. `` |
| lessons/README.md:11 | `60 entries or about 4,000 tokens` | `60 entries or 16,000 characters (about 6,400 tokens)` |
| research.md:71 | `$1.50 to $3` (the M row's cost column) | `$3 to $6` |
| evals/README.md:152 | `--max-cost-usd 300 --no-publish \` (arm 1) | `--max-cost-usd 600 --no-publish \` |
| evals/README.md:226 | `Treat 300 per arm as a starting ceiling until a` | `Treat 600 for arm 1 and 300 for arm 2 as starting ceilings until a` |
| SKILL.md:132 | ``(designed for `fable` at `high`;`` | ``(designed for `claude-fable-5-1` at `high`;`` |

The lessons-cap rows fix the text to match what `drive.py:7149-7150` enforces. If the intent is a
real 4,000-token cap, change the divisor there from 4 to 2.5 instead, once the other agent's edits to
that file have landed.

Two further notes for the owner, outside the skill: `~/.claude/settings.json` sets the deprecated
`ANTHROPIC_SMALL_FAST_MODEL` to Sonnet 4.5, and something in this environment already gives `claude -p`
a one-hour cache without `promptCacheTtl`.
