# Source verification of the post

*Component report for the `/drive` skill. Scope: check every factual claim in the 0xCodez post against primary sources, extract the engineering guidance those sources contain that the post dropped, and establish the model facts the skill can rely on as of 2026-09-14. Author model: Opus 5. Every URL below was fetched or read from a cached copy of the live page on 2026-09-14 unless marked otherwise.*

## 1. Executive opinion

The post is a secondhand summary written two days after launch (its X status ID decodes to 2026-06-11 15:09 UTC). Most of its substance comes from three real sources: Lance Martin's X article "Designing loops with Fable 5" (status ID decodes to 2026-06-09), Prithvi Rajasekaran's engineering post on harness design, and the Claude Code announcements for dynamic workflows and routines. Around that core it adds invented structure (the four-layer stack, the five-section STATE.md, the ci-triage skill), several factual errors, and a model lineup that was already stale by July. It is directionally sound and specifically unreliable, and the skill should cite the primary sources, never the post.

The errors that matter for `/drive` are these. Fable costs twice Opus per token, not five times. The Continual Learning Bench is a Berkeley-led academic benchmark, not an Anthropic one, and the five-stage memory progression and its numbers are one Anthropic engineer's anecdote on one SQL task. The "Anthropic engineering team" quote about designing loops is from that same personal X article. The Parameter Golf result compares two models under the same grader, so it says nothing about verifiers versus self-critique. Anthropic never recommended Haiku as a verifier, and Haiku 4.5 may retire as early as 2026-10-15.

One earlier report needs correcting. Report 15 says classifier fallback is not automatic in headless Claude Code. The settings reference says the opposite: `switchModelsOnFlag` defaults to `true`, the switch happens in `-p` runs too, and only when you set it to `false` does a `-p` run end the flagged request as an error.

The most valuable material is what the post flattened. That includes Anthropic's official Fable 5 and 5.1 prompting guidance, which has ready-made blocks for autonomous operation, grounded progress claims, scope control and memory. It includes the tension between Fable guidance (use fresh-context verifier subagents) and Opus 5 guidance (remove "use a subagent to verify" instructions because they cause over-verification). The skill has to resolve that tension on purpose. It also includes Rajasekaran's calibration method for evaluators, and the long-running harness pattern: a JSON feature list, a progress file, git history, and an end-to-end smoke test at the start of every session.

## 2. What the post says, and a critique

The post's argument has three parts. Fable 5 is a long-horizon model. Its value comes from loops (`/goal`, Outcomes, workflows, routines). And a system around the model can improve itself through memory, skills and verification. The argument is right, and it matches the one clear instruction in the primary material: Martin's line that it is "often better to design loops that let the model self-correct in response to environment feedback... and manage its own context." The system card for Fable 5 backs the memory emphasis with a measured result. Persistent file-based memory "improved its performance three times more than for Opus 4.8" on Slay the Spire ([launch post](https://www.anthropic.com/news/claude-fable-5-mythos-5)).

Where it goes wrong falls into four categories.

**Misattribution.** The post presents an individual engineer's X article as statements from "Anthropic's engineering team" and "the Claude Code team", and it credits an academic benchmark to Anthropic. The quotes themselves are accurate. The authority behind them is overstated.

**Inference presented as result.** The post turns a model-versus-model experiment into a claim about verifiers ("Without the verifier, the same model has nothing forcing it past the first 'good enough'"). No experiment ran without the verifier.

**Invented specifics.** The STATE.md template, the four layers, the ci-triage skill and the vision loop that compares against "the previous screenshot from STATE.md" are the author's designs. Some are reasonable. None is sourced. The STATE.md template also cuts against Anthropic's documented memory advice, which is to keep one lesson per file and many small focused files rather than one large one.

**Staleness and arithmetic.** "~5× Opus 4.8" is wrong at every point in time. The worker and grader tiers it names (Sonnet 4.6, Haiku 4.5) were superseded by Sonnet 5 on 2026-06-30. It also omits that Fable 5 access was suspended from 2026-06-12 to 2026-07-01 under US export controls, which matters for a skill that assumes Fable is always there.

## 3. Verified facts and primary sources

These are the sources the table in section 4 relies on. They are grouped by what they establish.

**Launch and model documentation**
- Introducing Claude Fable 5 and Mythos 5, 2026-06-09: https://www.anthropic.com/news/claude-fable-5-mythos-5. It covers the Mythos-class tier "above our Opus class", $10/$50 pricing, the classifier domains (cybersecurity, biology and chemistry, distillation), automatic handling by Opus 4.8 in the apps, the claim that ">95% of Fable sessions involve no fallback", and the 3x memory gain.
- Fable 5 and Mythos 5 System Card, 2026-06-09, **317 pages** (checked with `pdfinfo`; changelog entries dated June 11 and June 25): https://anthropic.com/claude-fable-5-mythos-5-system-card, which redirects to the www-cdn PDF. Section 1.5 describes fallback behavior on each surface.
- Fable 5.1 and Mythos 5.1 System Card, 2026-09-01, 212 pages: https://www-cdn.anthropic.com/0339e6a7c5c7b87f5c07798616dc32c215d14235/Claude%20Fable%205.1%20&%20Claude%20Mythos%205.1%20System%20Card.pdf
- Platform intro for Fable 5 and Mythos 5: https://platform.claude.com/docs/en/models/fable-5/introducing-claude-fable-5-and-claude-mythos-5
- What's new in Fable 5.1: https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1
- Prompting Fable 5: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- Prompting Fable 5.1: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1
- Prompting Opus 5: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5
- Prompting Sonnet 5: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5
- Prompting best practices (all models): https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Models overview: https://platform.claude.com/docs/en/about-claude/models/overview. Pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Fable product page (now describes 5.1): https://www.anthropic.com/claude/fable
- Redeploying Fable 5 (suspension from June 12 to July 1): https://www.anthropic.com/news/redeploying-fable-5
- Project Glasswing, 2026-04-07: https://www.anthropic.com/glasswing
- Refusals and fallback: https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback
- Support article on why Claude switched models: https://support.claude.com/en/articles/15363606-why-claude-switched-models-in-your-conversation-with-fable-5-or-fable-5-1

**Loops, verification, memory**
- Lance Martin, "Designing loops with Fable 5", X article, 2026-06-09. Original: https://x.com/RLanceMartin/status/2064397389189071163 (returns 402 to fetch tools). Full text read from the mirror at https://glean.smartcoder.ai/en/a/designing-loops-with-fable-5-self-correction-and-cross-sessi-p8jwfn
- Prithvi Rajasekaran, "Harness design for long-running application development", 2026-03-24: https://www.anthropic.com/engineering/harness-design-long-running-apps
- Justin Young, "Effective harnesses for long-running agents", 2025-11-26: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Continual Learning Bench, Asawa et al., arXiv 2606.05661, submitted 2026-06-04: https://arxiv.org/abs/2606.05661
- Managed Agents Outcomes: https://platform.claude.com/docs/en/managed-agents/define-outcomes. Memory stores: https://platform.claude.com/docs/en/managed-agents/memory
- Lydia Hallie, "Choosing a Claude model and effort level in Claude Code", 2026-07-07: https://claude.com/blog/claude-model-and-effort-level-in-claude-code

**Claude Code primitives**
- Introducing dynamic workflows, 2026-05-28: https://claude.com/blog/introducing-dynamic-workflows-in-claude-code. Docs: https://code.claude.com/docs/en/workflows
- Introducing routines, 2026-04-14: https://claude.com/blog/introducing-routines-in-claude-code. Docs: https://code.claude.com/docs/en/routines
- `/goal`: https://code.claude.com/docs/en/goal. Worktrees: https://code.claude.com/docs/en/worktrees. Subagents: https://code.claude.com/docs/en/sub-agents
- Model configuration (aliases, effort, automatic fallback): https://code.claude.com/docs/en/model-config. Settings reference (`switchModelsOnFlag`): https://code.claude.com/docs/en/settings-reference
- The six workflow patterns: Thariq Shihipar (Anthropic) on X, https://x.com/trq212/status/2061907337154367865. I could not fetch the original; I read it through The Neuron's explainer, https://www.theneuron.ai/explainer-articles/claude-code-dynamic-workflows-explained-claude-can-now-build-its-own-workflow-around-a-task/. Treat it as secondary.

## 4. Detailed spec: claim-by-claim verification table

Status key: **verified** means the source says it. **Partial** means it is true with material qualifications, or true of a different source than the post names. **Unverified** means no primary source was found. **Contradicted** means a primary source says otherwise.

### Part 1: what Fable 5 unlocks

| # | Claim in the post | Source | Status | What the source says | Implication for the skill |
|---|---|---|---|---|---|
| 1 | Fable 5 launched June 9, 2026 | [launch post](https://www.anthropic.com/news/claude-fable-5-mythos-5); system card cover | verified | "Jun 9, 2026". | None. |
| 2 | First publicly available Mythos-class model, one rung above Opus | launch post | verified | "Mythos-class models are a tier of Claude models that sit above our Opus class in capability." | None. |
| 3 | Mythos Preview shipped in April through Glasswing to "a handful of critical-infrastructure partners" | [Glasswing](https://www.anthropic.com/glasswing) | partial | Launched 2026-04-07 with 11 named partners (AWS, Apple, Broadcom, Cisco, CrowdStrike, Google, JPMorganChase, Linux Foundation, Microsoft, NVIDIA, Palo Alto Networks) plus over 40 organizations maintaining critical software. It was framed around cyber defense. | None; background only. |
| 4 | Fable 5 is the general-release version with classifiers; Mythos 5 without classifiers stays Glasswing-only | [platform intro](https://platform.claude.com/docs/en/models/fable-5/introducing-claude-fable-5-and-claude-mythos-5); Fable 5 system card §1.5 | partial | True for Fable 5's new classifiers. The system card says Mythos 5 has "relevant safeguards lifted", while the standard ASL-3 CB classifiers deploy "with all recent frontier models". Mythos 5.1 "powers Claude Security" for Enterprise customers. | Do not describe Mythos as unsafeguarded. |
| 5 | Days-long autonomous sessions in Claude Code or CMA: planning, delegating, checking its own work | [Fable page](https://www.anthropic.com/claude/fable); [Prompting Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5) | verified (capability) | "Tackle days-long, complex, and asynchronous tasks"; "completing multiday, goal-directed runs"; "significantly more dependable at dispatching and sustaining parallel subagents." | The skill can plan multi-session runs, but it needs file-based state (section 5.5). |
| 6 | "Self-verification built in": writes own tests, uses vision to check against goals, distills lessons into general rules, tests its own assumptions | Fable page; Martin | partial | Tests and vision are on the Fable page ("write its own tests to check its work", "use vision to help evaluate its own coding work, checking outputs against the original design or goal"). Distilling rules comes from Martin's SQL-memory anecdote. I found no source for "tests its own assumptions". "Reflects on and validates its own work" in the launch post is a customer quote (NTT DATA). | Capability, not a guarantee. The 5.1 system card lists "Skipped cheap verification" and "Fabrication" as recurring failures. Keep independent verification. |
| 7 | Headline use case: "hand off large projects and review completed deliverables" | Fable page (5.1 version) | partial | "Teams can hand off large projects and review completed work rather than supervising every step." The post's wording is a paraphrase in quotation marks. | None. |
| 8 | Multi-stage knowledge work with minimal oversight | Fable page | verified | "complex, multi-stage knowledge work with minimal oversight, from deep research and analysis to deliverables ready for your review." | Supports a research-shaped `/drive`. |
| 9 | $10 / $50 per million tokens | launch post; [pricing](https://platform.claude.com/docs/en/about-claude/pricing) | verified | $10 input, $50 output, for both Fable 5 and 5.1. | Section 7. |
| 10 | "Existing 90% input token discount for prompt caching" | pricing | verified for Fable 5, outdated | Fable 5 cache reads cost $1/MTok (0.1x). Fable 5.1 cache reads cost $0.25/MTok (0.025x), a 97.5% discount. | Long Fable 5.1 orchestrator sessions are cheaper than the post implies. The 5.1 guide says early compaction to save cost "may no longer be the right cost-intelligence tradeoff." |
| 11 | Available on Claude API, AWS, Bedrock, Vertex, Foundry, and consumption-based Enterprise | launch post; platform intro | partial | The launch post names the Claude API, consumption-based Enterprise, and Pro, Max, Team and seat-based Enterprise plans. The platform doc lists Bedrock, Claude Platform on AWS, Google Cloud and Foundry. I could not confirm launch-day cloud availability. | None. Aliases differ by provider (section 7). |
| 12 | "This is not a subscription model. Heavy use earns its own bill." | launch post; [model-config](https://code.claude.com/docs/en/model-config) | contradicted | Fable is available on Pro, Max, Team and Enterprise plans. "Depending on your plan and seat tier, Fable usage can bill to usage credits." In `-p` and the Agent SDK, "Claude Code never shows the consent prompt... bills it without asking." | A headless `/drive` run on Fable can spend usage credits silently. Say so in the skill's cost note. |
| 13 | Fable 5 was restricted, then released (omitted) | [Redeploying Fable 5](https://www.anthropic.com/news/redeploying-fable-5) | omitted by post | Access was suspended from 2026-06-12, when export controls were applied after a reported safeguard bypass. Controls were lifted June 30 and access restored July 1. | The orchestrator must degrade to `opus` if `fable` is unavailable. Do not hard-fail the run. |

### Part 1, continued: self-improvement framing and routing

| # | Claim in the post | Source | Status | What the source says | Implication for the skill |
|---|---|---|---|---|---|
| 14 | No publicly available model updates its own weights in production | [Hallie blog](https://claude.com/blog/claude-model-and-effort-level-in-claude-code) | verified for Claude | "by the time you're sending requests they're read-only. Nothing in your prompt, your CLAUDE.md, or your context changes them." | "Self-improving" in the skill means files, skills and agents. Say that plainly. |
| 15 | Anthropic warned about recursive self-improvement "in May 2026" | Secondary coverage of "When AI builds itself" (Favaro and Clark) | partial | Published 2026-06-04 according to CNN, Fortune and Scientific American. I did not fetch Anthropic's page. The Fable 5 system card §2.3.6 refers to "our recent article about recursive self-improvement". | Irrelevant to the skill. |
| 16 | "Anthropic's engineering team puts it directly: 'Rather than directly prompting and steering Fable 5, it's often better to design loops...'" | Martin X article | partial (misattributed) | The quote is accurate apart from a grammar fix; the original reads "let the model to self-correct". It comes from Lance Martin's personal X article, not an engineering-blog post. | Quote it as Martin's. The advice is consistent with the official Fable 5 guide. |
| 17 | Four-layer compound stack | none | unverified | The author's framing. | Do not import as structure. |
| 18 | Fable 5 costs "~5×" Opus 4.8 per token | pricing | contradicted | Opus 4.8 and Opus 5 cost $5/$25, so Fable is 2x. Opus fast mode is $10/$50, the same as Fable. | Routing arguments built on "5x" overstate the savings from Opus by 2.5x. |
| 19 | Opus 4.8 for hard-but-bounded work, and "the explicit fallback for any request Fable 5's classifiers block (cyber, bio, chem, distillation)" | model-config; support article; Fable 5 system card changelog | partial, outdated | At launch the apps routed all flagged categories to Opus 4.8. Since Claude Code v2.1.219, cyber goes to Opus 4.8 and bio (including chemistry and life sciences) goes to Opus 5. The `opus` alias is now Opus 5. | Pin security roles to `opus` deliberately. Expect cyber flags to land on Opus 4.8, not on the `opus` alias. |
| 20 | Sonnet 4.6 for high-volume worker tasks | models overview | outdated | Sonnet 5 (`claude-sonnet-5`, $2/$10, 1M context) shipped 2026-06-30 and is cheaper than Sonnet 4.6 ($3/$15). | Use the `sonnet` alias (Sonnet 5 on the Anthropic API). |
| 21 | Haiku 4.5 for graders, "the verifier role Anthropic explicitly recommends" | Prompting Fable 5; `/goal` docs; models overview | contradicted in part | Anthropic recommends fresh-context verifier subagents but never names Haiku for the role. `/goal`'s evaluator does default to Haiku, with no tools. Haiku 4.5 retirement is "not sooner than October 15, 2026." | The owner's choice of Sonnet at low effort over Haiku is supported. Haiku also carries retirement risk within weeks. |

### Part 2: the three primitives

| # | Claim in the post | Source | Status | What the source says | Implication for the skill |
|---|---|---|---|---|---|
| 22 | `/goal`: in-session loop, plain-text goal, model grader | [/goal docs](https://code.claude.com/docs/en/goal) | verified | Up to 4,000 characters. After each turn "a small fast model checks whether the condition holds". Verdicts are met, not yet met, or impossible. | Use `/goal` to keep the session running, not to decide quality. |
| 23 | Both `/goal` and Outcomes use "an independent grader"; "the agent that wrote the code is not the agent that grades it" | `/goal` docs; [Outcomes](https://platform.claude.com/docs/en/managed-agents/define-outcomes) | partial | The `/goal` evaluator "does not call tools, so it can only judge what Claude has already surfaced in the conversation." The Outcomes grader "uses a separate context window to avoid being influenced by the main agent's implementation choices"; its model is not stated. | `/goal` independence is weak: it grades the maker's narration. Conditions should reference verifier verdict files. |
| 24 | Outcomes: file-based rubric, subagent grader, hard `max_iterations` bound, hours or days on Anthropic infrastructure | Outcomes docs; Martin | partial | The rubric is a required Markdown document, passed inline or as a file. `max_iterations` defaults to 3 with a maximum of 20. Results are `satisfied`, `needs_revision`, `max_iterations_reached`, `failed` or `interrupted`. Martin ran on a self-hosted 8xH100 sandbox for up to 8 hours. | Borrow the rubric discipline and iteration cap for local loops. |
| 25 | Rajasekaran wrote on the engineering blog that models struggle to self-critique | [harness design post](https://www.anthropic.com/engineering/harness-design-long-running-apps) | verified | "agents tend to respond by confidently praising the work—even when, to a human observer, the quality is obviously mediocre." | Section 5.2 has the parts the post dropped. |
| 26 | "The Claude Code team confirmed this empirically with Fable 5: 'We've found that a verifier sub-agent tends to outperform self-critique with Fable 5.'" | Martin; Prompting Fable 5 | partial | The quote is Martin's, and he adds "because grading is done in an independent context window." It is not attributed to the Claude Code team and no data is published. The official Fable 5 guide does state: "Separate, fresh-context verifier subagents tend to outperform self-critique." | This is an official recommendation with unpublished evidence. It conflicts with Opus 5 guidance (row 27). |
| 27 | (Not in the post) Counter-guidance for Opus 5 | [Prompting Opus 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5); model-config "Work with Fable" | omitted by post | Opus 5: "If your prompt contains explicit verification instructions ('...use a subagent to verify'), remove them: instructions like these cause over-verification." Its damping prompt says "do not use subagents to verify or double-check your own work." Claude Code on Fable: "Skip the verification reminders." | Verification belongs to the orchestrator as a structural step. Makers should not be told to self-verify or to spawn their own verifiers (section 5.3). |
| 28 | Mechanism: a self-critic "prefers conclusions consistent with what it already wrote" | Martin; Rajasekaran | partial | Martin's stated reason is context independence. Rajasekaran adds that separation "doesn't immediately eliminate that leniency", but "tuning a standalone evaluator to be skeptical turns out to be far more tractable." | Separation plus calibration, not separation alone. |
| 29 | Parameter Golf: `TRAIN_SEQ_LEN=2048`, overlapped sliding-window eval, int6 QAT | Martin (chart image) | unverified | The article text does not contain these. They probably come from the chart, which I could not read. | Do not cite. |
| 30 | Fable pushed through a quantization regression to its biggest win; Opus 4.7 mostly adjusted scalars | Martin | verified | "pushing through a quantization regression to its biggest win"; Opus 4.7's experiments were "adjust a scalar, measure, keep if positive." | Useful anecdote about exploration breadth. |
| 31 | Roughly 6x improvement | Martin | verified as anecdote | "Fable 5 improved the training pipeline ~6x more than Opus 4.7." One toy challenge, nine checkable criteria, up to 8 hours, both models under the Outcomes grader. | An anecdote, not a benchmark. |
| 32 | Takeaway: with a verifier Fable explores larger spaces; "Without the verifier, the same model has nothing forcing it past the first 'good enough.'" | Martin | contradicted as inference | Both models ran with the same grader. There was no no-verifier arm. The rubric's criteria were process checks ("run a baseline, run 20 experiments"). | Never cite Parameter Golf as evidence for verifiers. It is evidence that checkable process criteria keep a run going. |

### Part 2, continued: workflows, worktrees, routines

| # | Claim in the post | Source | Status | What the source says | Implication for the skill |
|---|---|---|---|---|---|
| 33 | Dynamic workflows shipped May 28, 2026 | [blog](https://claude.com/blog/introducing-dynamic-workflows-in-claude-code) | verified | Dated May 28, 2026, alongside Opus 4.8. Example: Bun ported from Zig to Rust, about 750,000 lines, 99.8% of tests passing, eleven days. | None. |
| 34 | Claude writes its own JavaScript harness with `agent()`, `parallel()`, `pipeline()` | [workflows docs](https://code.claude.com/docs/en/workflows) | verified | Also `phase()`, `log()`, `args`, and a per-agent `schema`. `Date.now()` and `Math.random()` throw inside scripts. `agent()` resolves to `null` if blocked. The cap is 4,096 items per `parallel` or `pipeline`. The size guideline defaults to `medium` (fewer than 15 agents). | Section 5.8. |
| 35 | Patterns: fan-out-and-synthesize, adversarial verification, loop until done, classify-and-act, tournament | Shihipar on X (secondary); blog; docs | partial | Six patterns; the post drops **generate-and-filter**. Extra guidance: "assign one verifier per rule; use a skeptic persona to reduce false positives"; a classifier agent can pick Sonnet or Opus; "workflows are new, often use more tokens, and are unnecessary for many normal coding tasks." | Include generate-and-filter. Adopt one verifier per rule and the skeptic persona. |
| 36 | Pair loop-until-done with `/goal` | `/goal` docs | partial (opinion, compatible) | "If a subagent or a background shell command is still running when a turn ends, Claude Code skips the evaluation for that turn." Check-ins come after 30 minutes. | Compatible. |
| 37 | Worktrees: `--worktree` flag and `isolation: worktree` ("fresh checkout that cleans itself up") | [worktrees docs](https://code.claude.com/docs/en/worktrees) | partial | A subagent worktree is removed automatically only "when the subagent finishes without changes". With changes it stays until the periodic sweep (`cleanupPeriodDays`). It branches from the default branch unless `worktree.baseRef` is `"head"`. In `-p` runs, "Claude doesn't clean up" `--worktree` worktrees. | Supports the owner's rule: merge and delete in the same step, because the harness will not do it for a worktree with changes. |
| 38 | Routines, April 14, 2026, research preview; cloud runs; schedule, API and GitHub triggers | [blog](https://claude.com/blog/introducing-routines-in-claude-code); [docs](https://code.claude.com/docs/en/routines) | verified | Still "in research preview." Each run clones the repo from its default branch and creates `claude/`-prefixed branches. Minimum schedule interval is one hour. Runs act under the user's own GitHub and connector identities. Launch caps were 5, 15 and 25 runs per day for Pro, Max, and Team/Enterprise. The post's example routines are its own. | Routines leave `claude/` branches, which conflicts with the owner's main-only rule. Reserve them for conditions with no triggering signal. |

### Part 3: the self-improvement layer

| # | Claim in the post | Source | Status | What the source says | Implication for the skill |
|---|---|---|---|---|---|
| 39 | Five-stage memory progression "from Anthropic's Continual Learning Bench 1.0" | [arXiv 2606.05661](https://arxiv.org/abs/2606.05661); Martin | contradicted (attribution) | CL-Bench is by Parth Asawa, Christopher M. Glaze, Gabriel Orlanski, Ramya Ramakrishnan, Benji Xu, Asim Biswal, Vincent Sunn Chen, Frederic Sala, Matei Zaharia and Joseph E. Gonzalez. The abstract does not mention Anthropic or stages, and finds "naive ICL outperforms systems dedicated to memory management." The progression is Martin's framing for one database-querying task. | Use the stages as a procedure and credit Martin. The abstract's finding argues for simple file memory over elaborate memory machinery. |
| 40 | Sonnet 4.6 exits at stage 1; Opus 4.7 at stage 3 with 7–33% verification coverage (median about 17%); Fable 5 up to 73% | Martin | verified as anecdote | "in its strongest runs, verification coverage is up to 73% (22 of 30)". The post drops Martin's note that for Sonnet 4.6 "task-specific memory instructions are needed." | Non-Fable agents need explicit memory instructions. Do not quote the percentages as capability facts. |
| 41 | STATE.md with five sections matching the stages | none | unverified; conflicts with guidance | Prompting Fable 5: "Store one lesson per file with a one-line summary at the top... update an existing note rather than creating a duplicate; delete notes that turn out to be wrong." CMA memory: "Structure memory as many small focused files, not a few large ones." | Keep run state in a status file and lessons one per file (section 5.6). |
| 42 | "Write before walking away" and "read at session start" | [Effective harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents); best practices | verified in spirit | "Start the session by reading the progress notes file and git commit logs, and run a basic test on the development server... End the session by writing a git commit and progress update." | Adopt the fuller version, including the smoke test. |
| 43 | Write lessons into skills; skills sharpen over time | Prompting Fable 5 | partial | "Claude Fable 5 also does a good job of updating skills on the fly." In the same bullet: "Skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality." | Compounding needs pruning as well as adding (section 5.6). |
| 44 | Vision self-check: a maker renders, a verifier compares against goal, design tokens and the previous screenshot | Fable page; Rajasekaran; Prompting Fable 5.1 | partial | Vision checking against goals is verified. Rajasekaran's evaluator "would navigate the page on its own" with Playwright. Fable 5.1 "does its best work when it can iteratively analyze, crop, and visually verify"; a crop tool "delivers most of the uplift". The previous-screenshot step is the post's. | The UI verifier must interact, and should have crop and zoom. |
| 45 | Classifiers decline in "cybersecurity vulnerability research, biology, chemistry, and model distillation" | launch post; Fable 5 system card §1.5; refusals doc; Fable 5.1 system card | partial, outdated | At Fable 5 launch the domains were cybersecurity, biology and chemistry, distillation, and (per the system card) "accelerating frontier AI development". API categories are `cyber`, `bio`, `frontier_llm`, `reasoning_extraction`, `general_harms`, or `null`. Fable 5.1 "will allow vulnerability discovery in source code at all access levels" but blocks it in compiled binaries. | Source-code security review is allowed on 5.1. Asking the model to echo its reasoning is its own refusal category (section 5.4). |
| 46 | "Anthropic falls back to Opus 4.8 automatically" | system card §1.5; support article; model-config; [settings reference](https://code.claude.com/docs/en/settings-reference) | partial | Apps: automatic. Messages API: "no automatic fallback by default", opt in with `fallbacks`. Claude Code: automatic by default (`switchModelsOnFlag: true`) and **also in `-p` runs**. Only with `false` does "a `-p` run... end as an error". The switch persists for the session. | See section 6.1, which corrects report 15. |
| 47 | A classifier block "looks identical to a loop that fails on a real error" | refusals doc; SDK message | partial | On the API a refusal is an HTTP 200 with `stop_reason: "refusal"` and a category. In Claude Code the CLI emits a `system/model_refusal_fallback` message and continues on the fallback model. The practical danger is a silent, sticky downgrade, not an indistinguishable error. | Log fallback events. Check the model in `/tasks` or `modelUsage`. |
| 48 | "No retention policy review" as a mistake | platform intro | verified in relevance | Fable models "carry 30-day data retention and are not available under zero data retention unless expressly authorized." | One line in the skill's cloud-run note. |
| 49 | "9 out of 10 users have never run an agent system that compounds" | none | unverified | No source. | Ignore. |

## 5. Guidance the primary sources contain that the post omitted or flattened

This is the part of the report the coordinator should mine hardest. Each subsection says what the source says, with the text that matters, and what the skill should do with it.

### 5.1 How the loops were actually built (Martin, Outcomes docs, `/goal` docs)

Martin's Parameter Golf rubric was "a file with the nine checkable criteria (e.g., run a baseline, run 20 experiments, etc)", and "the Outcomes grader confirmed that all experimental criteria were met before allowing Claude to stop the work." Two points follow. The criteria were about the process (a baseline exists, enough experiments ran), not about how good the result was. And the run had a time bound of eight hours. Criteria of this kind are cheap to grade reliably and they stop a model from quitting early, which is the failure the post attributes to "good enough".

The Outcomes docs add three rules for rubrics. Write "explicit, gradeable criteria, such as 'The CSV contains a price column with numeric values' rather than 'The data looks good'", because "the grader scores each criterion independently, so vague criteria produce noisy evaluations." When no rubric exists, give Claude a known-good artifact and "ask it to analyze what makes that content good, then turn that analysis into a rubric". The docs say this "often produces better results than writing criteria from scratch." And a `failed` result means the rubric does not apply to the deliverable, for example because the description and rubric contradict each other. A local loop should distinguish "rubric is wrong" from "work is not done" in the same way. Outcomes can also be chained one after another, which maps onto milestones.

The `/goal` docs say to "write the condition as something Claude's own output can demonstrate", to bound it with "or stop after 20 turns", and note that the loop halts with a warning after "no tool use for several turns in a row".

### 5.2 How the evaluator was prompted and calibrated (Rajasekaran)

The post keeps only the headline. The method is what makes an evaluator useful:

- **Calibration.** "I calibrated the evaluator using few-shot examples with detailed score breakdowns." "The tuning loop was to read the evaluator's logs, find examples where its judgment diverged from mine, and update the QA's prompt to solve for those issues."
- **The failure to design against.** "I watched it identify legitimate issues, then talk itself into deciding they weren't a big deal and approve the work anyway. It also tended to test superficially, rather than probing edge cases."
- **Criteria with weights and hard floors.** Four design criteria (design quality, originality, craft, functionality), weighted toward design quality and originality, with explicit penalties for generic "AI slop" patterns. Each criterion had a threshold, and a sprint failed if any fell below it.
- **Sprint contracts before code.** "The generator proposed what it would build and how success would be verified, and the evaluator reviewed that proposal." Sprint 3 alone had 27 criteria.
- **Files as the communication channel.** "one agent would write a file, another agent would read it and respond either within that file or with a new file."
- **Interaction, not inspection.** The evaluator got the Playwright MCP and would "click through the running application the way a user would, testing UI features, API endpoints, and database states."
- **Cost and scope of the evaluator.** Solo run: 20 minutes, $9. Full harness: 6 hours, $200. The version-two harness on Opus 4.6 removed sprints, moved the evaluator "to a single pass at the end of the run", and cost $124.70 over 3 hours 50 minutes, of which QA round 1 was 8.8 minutes and $3.24. His closing rule: "the evaluator is not a fixed yes-or-no decision. It is worth the cost when the task sits beyond what the current model does reliably solo."

Shihipar's workflow guidance adds two practical rules: one verifier per rule, and a skeptic persona to reduce false positives. The Sonnet 5 guide adds a recall rule. If a review prompt says "only report high-severity issues", the model "may follow that instruction more faithfully... and then not report findings it judges to be below your stated bar." Anthropic's recommended wording is to report everything with confidence and severity, and filter in a separate step. The Opus 5 guide says the same about "be conservative."

### 5.3 The verification tension the skill must resolve

Three official sources pull in different directions.

1. Prompting Fable 5: "Make self-verification explicit in long-run prompts. Separate, fresh-context verifier subagents tend to outperform self-critique. For long-running tasks, instruct: `Establish a method for checking your own work at an interval of [X] as you build. Run this every [X interval], verifying your work with subagents against the specification.`"
2. Prompting Opus 5: remove "use a subagent to verify" instructions because they "cause over-verification". Its damping prompt includes "do not use subagents to verify or double-check your own work."
3. Claude Code on Fable: "Skip the verification reminders: it verifies its own work with less prompting, so reminders to test or check are usually unnecessary."

My reading is that these do not contradict each other. They separate two things: **nagging the maker** and **structural verification owned by the orchestrator**. Anthropic advises against the first on both current top models, because the models already self-check and the reminders add cost. The Fable guide recommends the second, at intervals and against the specification. So `/drive` should never tell a maker to "double-check" or to spawn its own reviewer. It should spawn fresh verifiers itself at defined checkpoints, against the claims file and rubric. Following Rajasekaran, it should scale the number of checkpoints with how far the task is beyond what the maker does reliably alone. Report 07's layered verifier design is consistent with this, provided the maker prompts are stripped of self-verification nags.

### 5.4 Anthropic's Fable 5 and 5.1 prompting advice for long autonomous runs

These blocks are official, tested by Anthropic, and in several cases come with a measured effect. The skill should use them nearly verbatim, adapted only where Claude Code already handles something.

- **Autonomous operation (5.1 version).** "You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work. For reversible actions that follow from the original request, proceed without asking. Stop only for destructive actions or genuine scope changes the user must decide... Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ('I'll…', 'let me know when…'), do that work now with tool calls..." Anthropic: "The opening sentence, which tells the model the user isn't watching, carries much of the effect. Keep it as written." This matches the owner's "no approval queues" rule closely.
- **Grounded progress claims.** "Before reporting progress, audit each claim against a tool result from this session. Only report work you can point to evidence for; if something is not yet verified, say so explicitly..." In Anthropic's testing this "nearly eliminated fabricated status reports even on tasks designed to elicit them." It is the most direct anti-mirage instruction in any source.
- **Scope as deliverable.** The "Delivering work" block: "The user's request... sets the scope, and the scope is the deliverable: don't quietly narrow, widen, or swap it... If one part turns out to be blocked, complete every other part in full and say exactly what you left out and why."
- **Keep changes and tests to the task.** "...don't fix, optimize or extend it in this change unless the requested behavior cannot work without it; report it as a follow-up... Commit tests only where the task asks for them or this repository already keeps tests for this kind of change, sized like the neighboring test files — roughly one focused test per stated behavior..." With this instruction, "unrequested additions and committed test code drop substantially with no measurable change in task success." The skill has to reconcile this with its own test-design phase. The skill's explicit test plan is "the task asks for them", so the block does not forbid it, but it does forbid a maker inflating tests beyond the plan.
- **State-changing commands.** "Before running a command that changes system state (restarts, deletes, config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause." This matters for the bug-hunt and ops shapes.
- **Do not ask the model to echo its reasoning.** "Prompts, skills, or harness instructions that tell the model to echo, transcribe, or explain its internal reasoning as response text can trigger the `reasoning_extraction` refusal category on Claude Fable 5, causing elevated fallbacks to Claude Opus 4.8." This is a concrete hazard for `/drive`: any template saying "show your reasoning", "explain your thinking step by step in the report" or "include your chain of thought" should be removed from Fable-run prompts. Asking for conclusions with evidence is fine.
- **Parallel subagents.** "Delegate independent subtasks to subagents and keep working while they run. Intervene if a subagent goes off track or is missing relevant context." "Long-lived subagents that keep their context across subtasks save time and cost through cache reads." In 5.1, letting the lead keep working "lowers average time to completion at similar quality, token usage, and cost." In Claude Code this means background agents plus `SendMessage` to continue them.
- **Memory.** "Store one lesson per file with a one-line summary at the top. Record corrections and confirmed approaches alike, including why they mattered. Don't save what the repo or chat history already records; update an existing note rather than creating a duplicate; delete notes that turn out to be wrong." To bootstrap from history: "Reflect on the previous sessions we've had together. Use subagents to identify core themes and lessons, and store them in [X]."
- **Give the reason.** "I'm working on [the larger task] for [who it's for]. They need [what the output enables]. With that in mind: [request]." Every subagent brief should open this way.
- **Overplanning.** "When you have enough information to act, act. Do not re-derive facts already established in the conversation, re-litigate a decision the user has already made, or narrate options you will not pursue..."
- **Context budget.** "You have ample context remaining. Do not stop, summarize, or suggest a new session on account of context limits." Use it only if a countdown is visible.
- **Final message as re-grounding.** "If you've been working for a while without the user watching... your final message is their first look at any of it. Write it as a re-grounding, not a continuation of your working thread: the outcome first, then the one or two things you need from them..." This fits the owner's plain-language preference.
- **Writing density (5.1).** Anthropic's recommended anti-pattern paragraph is the "mannered prose" paragraph that already appears word for word in the owner's global CLAUDE.md. The skill can rely on that file rather than duplicating it.
- **Compaction summaries (5.1).** For client-side compaction, preserve six items: difficulties and how they were handled; options raised, tried or set aside and why; everything decided, ruled out or constrained, stated exactly; where things stand; what is still open; hard-to-reconstruct details kept exactly. `/drive`'s end-of-phase handoff notes should cover the same six.
- **Batching (5.1).** "First privately list what you need next; then request every item that doesn't depend on another's result in this one response." This helps where 5.1 issues one tool call per turn.
- **Targeted edits (5.1).** "when it will not affect the end result, try to surgically edit a file rather than rewrite the entire thing."
- **Search at low effort (5.1).** At `low`, Fable 5.1 "answers from memory more often". The recommended nudge says that a name from "a fast-moving area like AI models and developer tools" should be searched "as the user wrote it... familiarity is not a reason to skip the search." Any research role run at low effort needs this.
- **Safeguard false positives (5.1).** Ask "Are there any bugs in this program?" rather than "Does this program compile without errors?"; give documentation for lesser-known languages; remove tools that return base64 into context.
- **Long deliverables at `xhigh` or `max` (5.1).** Run them at `high`. If you go higher, set room in `max_tokens` and tell the model not to draft the whole deliverable in thinking and then again in the reply.
- **Scaffolding.** "Start at the top of your difficulty range... Skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality. Review and consider removing older instructions if default performance is better."

### 5.5 The long-running harness pattern (Young; prompting best practices)

The post's "read STATE.md, write STATE.md" is a thin version of a pattern Anthropic documented in more detail and with observed failure modes.

- **The first context window is different.** An initializer session writes an `init.sh` that starts the dev server and runs the tests, a progress file, a structured feature list with every entry initially `"passes": false`, and an initial git commit.
- **JSON for status, prose for notes.** "the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files." Coding agents may edit only the `passes` field, under the instruction "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality."
- **One feature at a time.** "This incremental approach turned out to be critical."
- **Session start.** Run `pwd`, read the progress file and feature list, read `git log --oneline -20`, start the server, and run a fundamental end-to-end test before touching new work. "If the agent had instead started implementing a new feature, it would likely make the problem worse."
- **Session end.** Commit with a descriptive message and update the progress file.
- **Failure modes observed.** The agent tries to one-shot the app. A later agent "would look around, see that progress had been made, and declare the job done." Features get marked complete "without proper testing". End-to-end testing with browser automation "dramatically improved performance". A known blind spot: Claude "can't see browser-native alert modals through the Puppeteer MCP".
- **Fresh context versus compaction.** "Claude's latest models are extremely effective at discovering state from the local filesystem. In some cases, you may want to take advantage of this over compaction."

The "declares done because progress exists" failure is exactly the owner's mirage-completion problem, observed and named by Anthropic. The feature-list JSON with a restricted edit rule is a stronger mechanism than a Markdown STATUS file for the same reason Anthropic gives: models rewrite Markdown too freely.

### 5.6 Memory, in Anthropic's own terms (CMA docs; system cards)

- Memories are capped at 100 kB each: "Structure memory as many small focused files, not a few large ones."
- **Prompt injection into memory is a named risk.** "If the agent processes untrusted input... a successful prompt injection could write malicious content into the store. Later sessions then read that content as trusted memory. Use `read_only` for reference material." For `/drive`, lessons distilled from a research phase that read the open web should pass a verifier before they are promoted into the skill itself.
- Every memory write in CMA creates an immutable version, and rollback means writing an old version back. The owner's "audit trail plus undo" rule corresponds to committing lesson files to git.
- **Memory is not self-enforcing.** The Fable 5 system card's taxonomy of shortfalls, drawn from 886 real internal uses, includes "Correction fails: the relevant correction was present, e.g. in a memory file or repeated user feedback, but the behavior recurred anyway", and "Reckless action: taking a consequential or destructive action on the basis of unverified or fabricated information in its context or memory files." The largest cluster listed was "states an unverified guess as fact (41/886)". In that example the model reported a production release healthy after checking one error signal, and undercounted errors 20-fold. Lessons should therefore become checks (a test, a lint, a hook, a gate) wherever possible, not only prose. This is also the strongest empirical support for the owner's "second time is the bug" rule.
- The CL-Bench abstract's finding that "naive ICL outperforms systems dedicated to memory management" argues against building anything more elaborate than readable files.

### 5.7 Choosing model and effort (Hallie; What's new in 5.1; per-model guides)

- **The diagnostic question.** "did Claude not know enough or did it not try hard enough?" If it had full context and was still wrong, use a larger model. If it skipped a file, did not run tests, or did not double-check, raise effort.
- "Larger models are also better at handling ambiguity, whereas specific instructions directing execution are a better recipe for success on the smaller models." Sonnet and Opus workers therefore need precise briefs, and Fable can take outcomes.
- Fable "finished jobs Opus and Sonnet can't reach at any effort level", which justifies it for the orchestrator.
- Anthropic's default recommendation is the reverse of "Fable for everything": "For most workloads, start with Claude Opus 5... Use Claude Fable 5.1 for demanding reasoning and long-horizon agentic work, or when your evals on Claude Opus 5 at higher effort still fall short."
- **Fable 5.1 effort.** Default `high`. "At `medium`, results roughly match Claude Fable 5 at lower cost." "At `low`, Claude Fable 5.1 is often competitive with Claude Opus and Claude Sonnet models on cost per task while scoring higher." Effort names "don't correspond to the same amount of thinking across models."
- **Opus 5.** "`low` and `medium`... produce strong quality at a fraction of the tokens"; step up to `xhigh` for demanding coding. Code-review "accuracy holds at lower effort settings".
- **Sonnet 5.** It "respects effort levels strictly, especially at the low end... on moderately complex tasks running at `low` effort there is some risk of under-thinking." It "interprets prompts literally... does not silently generalize an instruction from one item to another." For a low-effort grader this is an advantage when the rubric is explicit and a risk when it is not. Rough mapping: "Sonnet 5 at medium is comparable in intelligence to Claude Sonnet 4.6 at high."
- Claude Code: `max` "may show diminishing returns and is prone to overthinking"; `ultracode` is `xhigh` plus workflow orchestration.

### 5.8 Workflows and subagent limits

- **When not to use a workflow.** "workflows are new, often use more tokens, and are unnecessary for many normal coding tasks" (Shihipar). The launch blog recommends "starting on a scoped task."
- **Size guideline.** `workflowSizeGuideline` defaults to `medium` (fewer than 15 agents) and is advice rather than a cap. `large` is fewer than 50.
- **Script constraints.** `Date.now()` and `Math.random()` throw, so pass timestamps in `args`. A relaunch replays completed `agent()` calls from cache but reruns everything after the first failure in a fan-out. `agent()` returns `null` when auto mode's classifier blocks it, so filter results.
- **Subagent caps in Claude Code.** `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` defaults to 20. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` defaults to 3.
- **Model resolution for subagents has changed since the brief was written.** Since v2.1.251 the order is: the per-invocation `model` parameter, then the definition's `model` frontmatter, then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main conversation's model. Setting `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` forces one model onto every subagent, teammate and workflow agent. The brief's order (environment variable first) is the pre-2.1.251 behavior.

## 6. Corrections to earlier reports and drafts

### 6.1 Report 15 (safety boundary): headless fallback is automatic by default

Report 15's executive opinion says "on the API and in headless (`-p`) Claude Code, the fallback to Opus is not automatic." Half of this is right. On the Messages API, fallback is opt-in (Fable 5 system card §1.5; support article; refusals doc). For Claude Code it misreads the documentation. The sentence it cites, "In non-interactive mode and SDK integrations that can't show the prompt, a flagged request ends the turn with a refusal instead", sits in the bulleted exceptions under **"Ask before switching"**. That section only applies after you turn off automatic switching. The settings reference is explicit about `switchModelsOnFlag`: "`true`: Claude Code switches to the fallback model and continues. `false`: in an interactive session Claude Code pauses...; where no dialog can show, such as a `-p` run, the flagged request ends as an error. Default: `true`." The Agent SDK behavior confirms this. The CLI emits `system/model_refusal_fallback`, retries the turn once on the fallback model, and the swap is "made persistent for the session". The GitHub issue #67009 event that report 15 quotes shows `"direction":"retry"`, which is a switch, not a refusal.

Consequences for the skill. With default settings, a headless `/drive` run whose orchestrator trips a classifier does not stall. It continues on Opus 4.8 (cyber) or Opus 5 (bio) for the rest of the session, which is a quieter failure: a silent downgrade of the orchestrator. Setting `switchModelsOnFlag: false` for headless runs, as the coordinator's draft `sec9-all.md` recommends for interactive runs, would turn every flag into a hard error. Report 15's practical recommendation to pin security and severe-testing roles to `opus` still stands, for the different reason of keeping attack material out of the orchestrator's context so the orchestrator is never downgraded.

Report 15's category table also states that `frontier_llm` has no fallback. The refusals doc does not publish per-category routing ("The routing is applied server-side and is not published per model"). The Fable 5 system card changelog says the frontier-LLM safeguard was updated "to reflect a safeguard that triggers fallback to an Opus model." Treat "no fallback for `frontier_llm`" as unconfirmed. For `/drive` this has limited practical weight.

### 6.2 Report 11 (failure to lesson): confirmed

The attribution findings hold. CL-Bench is by Asawa et al. (arXiv 2606.05661, 2026-06-04), and the stages and numbers are Martin's. Two small refinements. Martin's article is dated 2026-06-09 by its status ID, not 06-10. And the arXiv abstract page I fetched lists authors without affiliations, so the Berkeley, Snorkel and Wisconsin affiliations in report 11 are plausible but I did not confirm them.

### 6.3 Report 07 (verification): thin evidence confirmed, but the claim is now official

The evidence is still qualitative and unpublished. However, the verifier-over-self-critique claim is not only Martin's. Anthropic's official Fable 5 prompting page states it. Report 07 should also absorb the Opus 5 counter-guidance (section 5.3), which argues against telling makers to verify themselves, and Anthropic's report-everything-then-filter wording for review recall.

### 6.4 Brief and coordinator draft

- The brief's subagent model resolution order is outdated (section 5.8).
- The brief's model correction is confirmed: on the Anthropic API, `fable` resolves to Fable 5.1 (Claude Code v2.1.257 or later), `opus` to Opus 5, and `sonnet` to Sonnet 5. On other providers `sonnet` does not resolve to Sonnet 5 (section 7).
- `sec9-all.md` in the scratchpad refers to `CLAUDE_CODE_GOAL_GRADER_MODEL`. That variable does not appear in the environment variable reference or the `/goal` page. The only documented override is `ANTHROPIC_DEFAULT_HAIKU_MODEL`, which also changes the `haiku` alias and background tasks. I read only the matching lines of that draft, not the whole file.

## 7. Model realities as of 2026-09-14

Sources: [models overview](https://platform.claude.com/docs/en/about-claude/models/overview), [pricing](https://platform.claude.com/docs/en/about-claude/pricing), [model-config](https://code.claude.com/docs/en/model-config).

**Current models**

| | Fable 5.1 | Opus 5 | Sonnet 5 | Haiku 4.5 |
|---|---|---|---|---|
| API ID | `claude-fable-5-1` | `claude-opus-5` | `claude-sonnet-5` | `claude-haiku-4-5-20251001` (alias `claude-haiku-4-5`) |
| Released | 2026-09-01 | 2026-07-24 (secondary sources) | 2026-06-30 (secondary sources) | 2025 |
| Input / output, $ per MTok | $10 / $50 | $5 / $25 | $2 / $10 | $1 / $5 |
| Cache read | $0.25 (0.025x) | $0.50 | $0.20 | $0.10 |
| Batch | $5 / $25 | $2.50 / $12.50 | $1 / $5 | $0.50 / $2.50 |
| Context window | 1M | 1M | 1M | 200K |
| Max output (sync) | 128K | 128K | 128K | 64K |
| Thinking | adaptive, always on | adaptive | adaptive (on by default) | extended |
| Default effort (API) | `high` | `high` | `high` | not supported |
| Reliable knowledge cutoff | Jun 2026 | May 2026 | Jan 2026 | Feb 2025 |
| Retirement, not sooner than | 2027-09-01 | 2027-07-24 | 2027-06-30 | **2026-10-15** |

Sonnet 5's $2/$10 was announced as introductory pricing. The pricing page now says it "is now the standard price" and the planned September increase "will not occur."

Legacy models still available include Fable 5 (`claude-fable-5`, cache read $1), Opus 4.8 (`claude-opus-4-8`, $5/$25), Opus 4.7, Opus 4.6, Sonnet 4.6 ($3/$15) and Sonnet 4.5. Mythos 5.1 (`claude-mythos-5-1`) is for Glasswing participants only. Fable 5.1 does not accept forced tool use (`tool_choice` of `any` or `tool` returns a 400), prefill, or non-default sampling parameters. Its tokenizer, like every model since Opus 4.7, produces roughly 30% more tokens than earlier models for the same text.

**What the Claude Code aliases resolve to**

| Provider | `fable` | `opus` | `sonnet` |
|---|---|---|---|
| Anthropic API | Fable 5.1 (v2.1.257+; Fable 5 in Claude apps gateway sessions) | Opus 5 (v2.1.219+) | Sonnet 5 (v2.1.197+) |
| Claude Platform on AWS | Fable 5.1 | Opus 5 | **Sonnet 4.6** |
| Bedrock, Google Cloud Agent Platform | Fable 5.1 | Opus 5 | **Sonnet 4.5** |
| Microsoft Foundry | Fable 5.1 | **Opus 4.6** | **Sonnet 4.5** |

`best` resolves to whatever `fable` resolves to where Fable is available, and to `opus` otherwise. Fable is never the account default. Pins are set with `ANTHROPIC_DEFAULT_FABLE_MODEL`, `ANTHROPIC_DEFAULT_OPUS_MODEL` and `ANTHROPIC_DEFAULT_SONNET_MODEL`. Subagent frontmatter accepts `sonnet`, `opus`, `haiku`, `fable`, a full ID, or `inherit`. If the owner ever runs `/drive` through Bedrock or Vertex, the `sonnet` alias silently means an older model. The skill should either state that it assumes the Anthropic API, or check `modelUsage` at startup.

**Effort levels per model in Claude Code**

| Model | Levels |
|---|---|
| Fable 5.1, Fable 5 | `low`, `medium`, `high`, `xhigh`, `max` |
| Opus 5, Sonnet 5, Opus 4.8, Opus 4.7 | `low`, `medium`, `high`, `xhigh`, `max` |
| Opus 4.6, Sonnet 4.6 | `low`, `medium`, `high`, `max` |
| Haiku 4.5 | none |

An unsupported level falls back to the highest supported level below it. The default is `high` on every model except Opus 4.7 (`xhigh`). Fable 5, Opus 4.8 and Opus 4.7 have a "hold" on their default effort that persists across sessions; Fable 5.1 and Opus 5 do not. Frontmatter `effort` applies even during that hold since v2.1.267. `max` applies to the current session only unless set through `CLAUDE_CODE_EFFORT_LEVEL`. A non-interactive `/effort` is session-only, and on held models it reports `Not applied`, so pass `--effort` at launch. `ultracode` sends `xhigh` and turns on workflow orchestration. Thinking cannot be disabled on Fable. `ultrathink` in a prompt adds an in-context instruction without changing the effort sent to the API.

**Automatic classifier fallback in Claude Code**

- Fable 5.1 and 5: bio re-runs on Opus 5, cyber re-runs on Opus 4.8.
- Opus 5: cyber re-runs on Opus 4.8; bio ends in a refusal.
- The switch is sticky for the session. A flag can fire on the first request because of CLAUDE.md content or git status. `claude --safe-mode` tests whether a customization is the trigger.

## 8. Conditionals by project shape

This component does not run a phase of its own. What it contributes to each shape is which verified guidance applies and which post claims to avoid.

- **Greenfield app.** Use the long-running harness in full: an initializer phase that writes the feature list as JSON with `passes: false`, an `init.sh`, a progress file and an initial commit; one feature at a time; a smoke test at each session start. Use sprint contracts written before code, with the evaluator reviewing the maker's proposal of what it will build and how it will be verified. The UI evaluator interacts through the simulator or a browser and has crop and zoom. For design quality, use Rajasekaran's four weighted criteria with hard floors and derive the rubric from a known-good reference app where one exists. Tournaments suit choosing among design directions. Anthropic's Sonnet 5 guide also recommends proposing four distinct visual directions before building.
- **Deep bug hunt.** Fable's "bug-finding recall... is noticeably higher than Claude Opus 4.8", including search of repository history. Use the report-everything-then-filter wording, with a separate verification step that ranks by confidence and severity. Include the rule that "a signal that pattern-matches to a known failure may have a different cause" before any state-changing action. Do not prompt makers to self-verify; the reproducer test is the verification. Workflows are justified only for bug hunts across a whole service, the case the launch blog names.
- **Feature on an existing product.** The 5.1 "keep changes and tests to what the task asks for" block applies almost verbatim, with the test plan defining what "the task asks for". Read neighboring tests to size new ones. Report pre-existing bugs as follow-ups rather than fixing them.
- **Migration or consolidation.** This is dynamic workflows' flagship case (Bun's port) and Fable 5.1's stated strength ("large refactors and migrations"). Build the equivalence checks before moving code, and make "run the baseline" a process criterion the loop cannot skip, following Martin's rubric style. Long sessions favor Fable 5.1's cheap cache reads, so compact later rather than earlier.
- **Research plus website.** Low-effort research roles need the search nudge. Summaries must mark quotations, because 5.1 "is more likely... to reproduce passages of the source text without marking them as quotations" and the owner publishes under his own name. Lessons from web-reading phases are untrusted input for memory until verified. Website UI verification follows the greenfield rules.
- **Security-adjacent work in any shape.** Source-code vulnerability review is allowed on Fable 5.1. Keep exploit strings and attack payloads in Opus-pinned subagents so the orchestrator is never downgraded. Avoid compile-check phrasing and base64 tool output. Never put "explain your reasoning" instructions in Fable prompts.
- **Pure research report, refactor, ops or incident, CLI, library.** Refactors take the scope block and the anti-overengineering block. Ops and incident work takes the state-change evidence check and the grounded-progress block. Research reports take the rubric-from-known-good method.

## 9. Model and effort assignment implied by the sources

This section records what the sources say. The routing decision itself belongs to report 06.

- **Orchestrator: `fable`, `high`.** Anthropic's recommended default is `high`, with `xhigh` only where measured. Fable 5.1 has no effort hold, so frontmatter and launch flags behave predictably. If Fable is unavailable, fall back to `opus` at `xhigh`, which Anthropic recommends for demanding agentic coding on Opus 5. The June suspension is the precedent for planning this.
- **Hard bounded work: `opus`, `high` or `xhigh`.** Opus 5 delegates readily, so cap spawning in its brief using the damping prompt. Do not include verification nags.
- **Volume work: `sonnet`, `medium` or `high`.** Sonnet 5 at `medium` roughly equals Sonnet 4.6 at `high`. Briefs must be literal and state their scope explicitly.
- **Graders and classifiers: `sonnet`, `low`.** This is supported where criteria are explicit and each has an oracle. Anthropic warns of "some risk of under-thinking" on moderately complex judgments at `low`, so anything requiring code-path reasoning goes to a verifier on `opus`. Haiku carries both trust concerns and an October 2026 retirement risk.
- **Consider Fable 5.1 at `low` for a few judge roles.** Anthropic says it "is often competitive with Claude Opus and Claude Sonnet models on cost per task while scoring higher". It may suit the final auditor or arbiter where Opus at `xhigh` would otherwise run. This is unmeasured for `/drive`, and flags of any kind would downgrade that subagent.
- **`/goal` evaluator: Haiku by default.** It can only be changed globally through `ANTHROPIC_DEFAULT_HAIKU_MODEL`. Keep it as the loop-continuation mechanism and never as the verdict.

## 10. Failure modes, and claims the skill must not rely on

**Claims the skill must not rely on or repeat**

1. Any cost ratio of Fable to Opus other than 2x on list price. Real cost per task varies; Anthropic says the larger model can be cheaper on hard tasks.
2. "Anthropic falls back automatically" as a universal statement. It is automatic and sticky in Claude Code and the apps, and opt-in on the API.
3. The Parameter Golf specifics and the verifier conclusion drawn from them.
4. The 73%, 17% and 7–33% figures as model capability facts, and any attribution of CL-Bench or the five stages to Anthropic.
5. "The Claude Code team confirmed empirically." Cite the Fable 5 prompting guide instead.
6. Haiku as the recommended verifier, and Sonnet 4.6 or Opus 4.8 as the current tiers.
7. The five-section STATE.md as a recommended format.
8. "Fable 5 is not a subscription model."
9. The claim that `isolation: worktree` always cleans up after itself.
10. Classifier domains as "vulnerability research, biology, chemistry, distillation". Source-code vulnerability discovery is allowed on 5.1.

**Mirage risks this component exposes**

- **Citing a source you did not read.** The post is itself an example: quotes are correct but attributed to more authoritative bodies than wrote them. Prevention: every references/ file names author, venue and date for each quoted claim, and a verifier checks one quote per file against the URL.
- **Official guidance as proof.** "Anthropic recommends X" is not "X is measured". Where Anthropic gives a measured effect (grounded progress claims; scope and test instruction; memory 3x), say so. Where it does not (verifier over self-critique), say that too.
- **Sticky downgrade presented as success.** A run that finished on Opus 4.8 after a cyber flag reports success, and the orchestrator's quality assumptions no longer hold. Prevention: record the serving model per phase from `modelUsage` or `/tasks`, and treat a fallback event as a finding in the status file.
- **Memory that says the right thing while the behavior recurs.** The system card documents "Correction fails". Prevention: turn a lesson into a check wherever possible.
- **Workflows adopted by default.** Anthropic's own team says they are unnecessary for many coding tasks and use more tokens.

## 11. Open questions and trade-offs

1. **Does a subagent's classifier fallback make the main session sticky?** The docs describe session-level stickiness for the main conversation. I found nothing on whether a subagent's switch affects its parent. Recommendation: treat it as possible, keep flag-prone material in Opus-pinned subagents, and verify with a deliberately benign security-review probe on a scratch repository before relying on either answer.
2. **Should `/drive` set `switchModelsOnFlag: false`?** In interactive runs it gives a visible choice. In `-p` runs it turns flags into errors, which stops a run that would otherwise have continued on Opus. Recommendation: leave the default `true`, log fallback events, and have the orchestrator re-dispatch the affected unit deliberately. Do not set `false` for headless runs.
3. **How much verification structure for Fable makers?** Opus 5 guidance says over-verification wastes tokens. Rajasekaran found the evaluator's value shrank as models improved and moved it to a single end-of-run pass. Recommendation: verify at milestone boundaries and before Done, scaled by the intake classifier's estimate of difficulty, rather than after every unit on easy work. Report 07's loop bounds are compatible if the per-unit round is optional for low-risk units.
4. **Markdown STATUS versus JSON feature list.** Anthropic observed that JSON resists inappropriate edits better. The owner's status ladder is richer than `passes: true/false`. Recommendation: a JSON ledger holding each claim's rung and a proof path, with a Markdown STATUS generated from it rather than edited by hand.
5. **The six workflow patterns rest on a secondary source.** The Claude Code workflows doc confirms adversarial review and weighing several angles, but not the full list. Recommendation: keep the patterns, cite the Claude Code docs for the mechanics, and use Shihipar's X post as secondary.

## 12. Skill text candidates

These are ready to lift into SKILL.md or `references/`. The text is plain and imperative. Quoted Anthropic blocks keep their original wording, including Anthropic's own dashes.

**1. Operating autonomously** (SKILL.md, orchestrator preamble; source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1)

> You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work. For reversible actions that follow from the original request, proceed without asking. Stop only for destructive actions or genuine scope changes the user must decide. Before ending your turn, check your last paragraph. If it is a plan, a list of next steps, or a promise about work you have not done, do that work now with tool calls. End your turn only when the task is complete or you are blocked on input only the user can provide.

**2. Evidence before status** (SKILL.md, every role that writes status; same source; Anthropic reports this "nearly eliminated fabricated status reports")

> Before reporting progress or updating a status file, audit each claim against a tool result from this session. Report only work you can point to evidence for, and say explicitly what is not yet verified. If tests fail, say so and include the output. If a step was skipped, say that. When something is done and verified, state it plainly.

**3. Who verifies** (SKILL.md, verification section; sources: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5 and https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5)

> Verification is a step the orchestrator schedules, not a reminder given to the maker. Do not tell makers to double-check, re-verify, or spawn their own reviewer; current models already check their own work, and those instructions add cost without improving results. At each checkpoint in the plan, the orchestrator spawns a fresh verifier that has not seen the maker's reasoning and gives it the claims, the rubric, and the commands to run. Add checkpoints in proportion to how far the task is beyond what the maker does reliably alone.

**4. Calibrating a verifier** (`references/verification.md`; source: https://www.anthropic.com/engineering/harness-design-long-running-apps)

> A verifier left to itself finds real problems and then talks itself into approving the work. Counter this in three ways. Give it scored examples of past verdicts, including one where the work looked fine and was not. Put a hard floor on every criterion that matters, so one failure fails the round no matter how good the rest is. Make it interact with the running artifact (click, call, query) before scoring anything it could otherwise only read. When a verdict disagrees with what you later learn, record the disagreement and change the verifier's prompt, not just the verdict.

**5. Report everything, filter separately** (`references/verification.md`; source: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5)

> Report every issue you find, including ones you are uncertain about or consider low-severity. Do not filter for importance or confidence at this stage; a separate verification step will do that. For each finding, include your confidence level and an estimated severity so a downstream filter can rank them.

**6. Writing rubrics** (`references/rubrics.md`; sources: https://platform.claude.com/docs/en/managed-agents/define-outcomes and Martin's article via the mirror above)

> Write each criterion so a grader can decide it alone: "the CSV has a numeric price column", not "the data looks good". Include process criteria the run cannot skip, such as "a baseline was measured before any change" and "every stated behavior has a test that ran". When a known-good example exists, have an agent analyze what makes it good and turn that analysis into the rubric. If the rubric and the deliverable do not fit each other, stop and fix the rubric; do not count it as a failed attempt.

**7. Session start and end** (`references/state.md`; source: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

> At the start of every session or phase: confirm the working directory, read the progress notes and the claims ledger, read the last twenty commits, start the app with the project's init script, and run one end-to-end smoke test. If the smoke test fails, fix that before starting anything new. At the end: commit with a message that says what changed and why, and update the progress notes. Never conclude the project is done because a lot of work exists; conclude it only from the ledger.

**8. Ledger format** (`references/state.md`; same source plus prompting best practices)

> Keep claim status in a JSON ledger and notes in Markdown. Agents change only a claim's status and proof path in the ledger; they never delete or reword a claim. Removing or editing a claim to make progress look better is not allowed, because it hides missing or broken work. Generate the human-readable STATUS file from the ledger instead of editing it directly.

**9. Lessons** (`references/lessons.md`; sources: Prompting Fable 5, https://platform.claude.com/docs/en/managed-agents/memory, and the Fable 5 system card §2.3.3)

> Store one lesson per file, with a one-line summary at the top. Record confirmed approaches as well as corrections, and say why each mattered. Update an existing lesson rather than adding a duplicate, and delete a lesson that turns out to be wrong. A lesson written as prose can be read and still ignored, so wherever a lesson can become a test, a lint rule, a hook, or a gate, make it one and link the lesson to it. Treat lessons derived from web pages or other untrusted input as unverified until a verifier confirms them.

**10. Improving the skill itself** (`references/lessons.md`; source: Prompting Fable 5)

> When a lesson belongs in this skill, add it, and in the same change look for an older instruction it makes unnecessary. Instructions written for weaker models are often too prescriptive for current ones and make results worse. If default behavior is already correct, remove the instruction.

**11. Scope and tests for makers** (maker brief template; source: Prompting Fable 5.1)

> If you find a pre-existing bug, a performance concern, or behavior the task does not mention, do not fix or extend it in this change unless the requested behavior cannot work without it; report it as a follow-up. Where the task is ambiguous, implement the reading its wording and the surrounding code most directly support, and state the assumption. Write the tests the test plan names, sized like the neighboring tests. Do not turn scratch checks into permanent test files. Implement every behavior the task asks for, completely.

**12. Before changing system state** (SKILL.md, bug-hunt and ops conditionals; source: Prompting Fable 5.1)

> Before running a command that changes system state, such as a restart, a delete, a migration, or a configuration edit, check that the evidence supports that specific action. A symptom that matches a failure you have seen before may have a different cause.

**13. Briefing a subagent** (subagent brief template; sources: Prompting Fable 5; https://claude.com/blog/claude-model-and-effort-level-in-claude-code)

> Open every brief with why the work matters: "This is part of [larger task] for [who]. They need [what the output enables]." Brief Fable with the outcome and let it plan. Brief Opus and Sonnet with precise instructions and explicit scope, because they follow instructions literally and do not generalize from one item to the next. Do not ask any subagent to write out its reasoning in its reply; ask for conclusions, the evidence for each, and what it could not check.

**14. Delegation** (SKILL.md, orchestration; sources: Prompting Fable 5.1 and Prompting Opus 5)

> Delegate independent, sizeable work to background subagents and keep working while they run; continue a finished subagent with SendMessage instead of starting a new one when its context is still useful. Do not delegate what you can finish in a few tool calls. Use a dynamic workflow only when the work fans out across many independent pieces or needs adversarial cross-checking at scale; for ordinary coding tasks a workflow uses more tokens for no gain.

**15. Choosing model and effort when a step goes wrong** (`references/routing.md`; source: https://claude.com/blog/claude-model-and-effort-level-in-claude-code)

> When a step produces a wrong result, first check its context: the brief, the files it had, the tools it could use. If the context was complete and the agent was confidently wrong, rerun on a more capable model. If it skipped a file, did not run the tests, or stopped partway, rerun at higher effort. Record which change fixed it as a lesson about that kind of step.

**16. Classifier fallback** (`references/safety-boundary.md`; sources: https://code.claude.com/docs/en/model-config, https://code.claude.com/docs/en/settings-reference, https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)

> In Claude Code, when a Fable model's safety classifier flags a request, the session switches automatically, including in headless runs: cybersecurity flags continue on Opus 4.8 and biology flags on Opus 5, and the session stays on that model. The run does not stop, so you have to notice. After each phase, record which model served it, and treat any fallback as an event in the status file. Keep exploit strings, attack payloads, and offensive test material inside Opus-pinned subagents so the orchestrator is never switched. Leave `switchModelsOnFlag` at its default in headless runs; setting it to false turns every flag into an error that ends the request.

**17. Research at low effort** (research role brief; source: Prompting Fable 5.1)

> When a question centers on a name you do not confidently recognize, or one from a fast-moving area such as AI models and developer tools, search before answering and include the name exactly as written in at least one query. Partial familiarity is what makes an outdated answer sound authoritative. When summarizing a source, put its exact words in quotation marks and reword everything else.

**18. When Fable is unavailable** (SKILL.md, startup; source: https://www.anthropic.com/news/redeploying-fable-5)

> At startup, confirm which model the `fable` alias actually serves. If Fable is unavailable, run the orchestrator on `opus` at `xhigh`, say so once in the first status entry, and continue. Do not stop the run to wait for Fable.

**19. Final message** (SKILL.md, completion; source: Prompting Fable 5)

> Your final message is the owner's first look at the work. Lead with the outcome in one sentence. Then give the one or two things he needs to know or decide, each explained as if new. Leave behind the shorthand and labels you invented while working, and name files and commits in plain clauses.
