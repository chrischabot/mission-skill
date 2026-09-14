# Research brief — the `drive` skill

> **Correction from the owner (binding, overrides anything below).** The fashion and outfit
> iOS app with a Cloudflare backend is ONLY an illustrative description of the kind of project
> the skill might be asked to tackle. It is not a project to build. Do not write any code,
> scaffolding, Xcode projects, Workers, schemas, or probe apps themed on it, in any directory.
> Where this brief asks for a "worked example", describe briefly what the skill would instruct
> an agent to produce for a project of that shape, in prose; do not produce the artifacts.
> Read-only tooling checks (`xcodebuild -version`, `xcrun simctl list`, `wrangler --version`,
> reading docs) are fine. Anything beyond that needs a generic name, must live under
> `/private/tmp`, and must be deleted before you finish.
>
> **Model correction (verified by earlier researchers).** In Claude Code the aliases `fable`,
> `opus`, and `sonnet` currently resolve to Fable 5.1, Opus 5, and Sonnet 5; there is no
> Sonnet 4.8. The owner's intent is the three tiers, so the skill uses the aliases.

You are one researcher in a fleet. Every researcher reads this brief, then goes deep on ONE
component, and writes ONE report to the path given in your task prompt. The coordinator will
read all reports together with the source post and turn them into a Claude Code skill.

Date: 2026-09-14. Your knowledge may be stale on tooling; verify with the live web (Claude Code
docs at https://code.claude.com/docs/en/..., index at https://code.claude.com/docs/en/llms.txt;
Anthropic engineering blog; framework docs). Distinguish **verified fact (with URL)** from
**source claim** from **your opinion**. Opinions are wanted, strongly held, and argued.

## 1. What the coordinator is building

A personal Claude Code skill, `/drive`, invoked as `/drive <high-level goal>`. It turns a
high-level direction into a complete, autonomous execution engine: intake and shape
classification, research, specification, architecture design (backend and frontend), test
design, parallel implementation with subagents, independent adversarial verification,
vision-based UI verification, state tracking in files, failure investigation distilled into
general lessons, and compounding those lessons back into the skill. It must scale from
"build an app from scratch" down to "find and fix this one deep bug" without imposing
ceremony that does not pay for itself.

The owner (Chris) said: "I sometimes work this way and more often feel I should, but am too
lazy to type out all of these stages, agent roles, steps ... its costing me efficiency and
makes for poorer results." The skill exists so he never has to type it again.

### Worked project shapes the skill must handle well

1. **Greenfield app**: a fashion and outfit-creating iOS app. Cloudflare backend, native Swift
   iOS front end. Input is a few paragraphs. Skill must produce the overarching spec, backend
   design, frontend design, end-to-end test strategy, front-end design/UX quality verification,
   correctness testing, heavy adversarial review, model routing, STATUS/STATE tracking,
   learnings, failure analysis → generic lessons, and a research ledger (incl. online search).
2. **Deep bug hunt**: "find this deep annoying bug and fix it" in an existing codebase.
3. **Feature on existing product**: "add this new dashboard to the existing product".
4. **Migration / consolidation**: "move our AI gateway from an external project into a core
   service of our platform".
5. **Research + website**: "research our market position, create a website, design it to
   describe our project, goals, team, with blog and documentation sections".

Also consider: pure research report; refactor/simplification; ops/incident; data pipeline;
CLI tool; library/SDK. Say which shapes matter and which conditionals ("if the task includes
X then also do Y") the skill needs.

### Hard requirements from the owner

- Models: **Fable 5.1** (alias `fable`) for orchestration and the hardest judgment;
  **Opus 4.8** (alias `opus`) for hard-but-bounded work; **Sonnet 4.8** (alias `sonnet`) for
  volume work and, at **low effort, as graders/classifiers instead of Haiku**. He does not
  trust Haiku in a general skill. Ignore any "4.6"/"4.7" version numbers in the post.
- The skill must be "smart about instructing the agent to do different things for different
  project types and scopes." Conditionals are first-class.
- End goal: one invocation with a high-level goal drives the full process to completion.

### Owner's working preferences (binding; from his memory files)

- **Plain language.** Never lean on rule IDs, codenames, or jargon labels; say what a thing
  means. Write like a careful senior colleague; full sentences; no hype; no staccato; no
  em-dash confetti; no flattery.
- **No approval queues.** Anything gated on him reviewing an inbox never completes. Automate
  fully with audit trail + undo. If a human decision is truly unavoidable, surface ONE choice
  directly in conversation, once. Assume autonomous operation: he is not watching.
- **No branches or worktrees left behind.** He commits straight to main in his own repos. If a
  subagent needs worktree isolation mid-task, merging and deleting it is part of the same
  step, never an epilogue. One canonical checkout. No stray artifacts committed.
- **Never wait on a scheduler.** Drive systems through their own tools/APIs; make things happen
  now; schedules only for conditions with no triggering signal. Never report "it will happen
  when the cron runs" as done.
- **Anti-mirage completion culture** (from his Arcwell repo): never mark work complete because
  a scaffold/README/command exists. Completion = code + tests + severe (adversarial) review +
  live proof where relevant + docs + status files all agreeing. Every feature names its
  behavioral claim before coding and gets at least one test that tries to REFUTE the claim.
  Status ladder: Missing → Scaffold → Partial → Local Proof → Live Proof → Operational → Done;
  local-only work is never labelled Live Proof. Ground-truth precedence when judging claims:
  working-tree code + tests > proof artifacts > STATUS files > docs prose. A test harness
  kinder than production certifies broken code (his D1 100-bind-variable incident: a sql.js
  shim allowed unlimited params, 24 green runs, failed live). Ask of any shim: where is it
  kinder than the real thing?
- **Second time is the bug.** Repeating a workaround means the first diagnosis was wrong.

## 2. Verified harness facts (checked 2026-09-14 against code.claude.com docs)

**Subagent definitions** live in `~/.claude/agents/*.md` (user) or `.claude/agents/*.md`
(project), scanned recursively, hot-reloaded within seconds (exception: the first file in a
directory that did not exist at session start needs a restart). Frontmatter fields: `name`,
`description`, `tools`, `disallowedTools`, `model` (`sonnet|opus|haiku|fable|inherit|<full id>`),
`permissionMode`, `maxTurns`, `skills` (preload), `mcpServers`, `hooks`, `memory`
(`user|project|local`), `background`, `effort` (`low|medium|high|xhigh|max`; levels depend on
model), `isolation: worktree`, `color`, `initialPrompt`, `experimental.cacheTtl`. Resolution
order for model: `CLAUDE_CODE_SUBAGENT_MODEL` env > per-invocation `model` param > frontmatter
> main session model.

**Skills** live in `~/.claude/skills/<dir>/SKILL.md` (command name = directory name; symlinks
allowed). Frontmatter: `name`, `description`, `when_to_use`, `argument-hint`, `arguments`,
`disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`,
`effort`, `context: fork`, `agent`, `background`, `hooks`, `paths`, `shell`, `metadata`,
`license`, `compatibility`. `$ARGUMENTS`, `$0..$N`, `${CLAUDE_SKILL_DIR}`,
`${CLAUDE_PROJECT_DIR}`, `${CLAUDE_EFFORT}` substitute. Keep SKILL.md under ~500 lines; after
auto-compaction only the first ~5,000 tokens of each skill are re-attached (shared 25k budget),
so the durable state must live in files, not in the prompt. Skills cannot bundle agents unless
packaged as a plugin (`.claude-plugin/plugin.json`); otherwise agents ship separately into
`~/.claude/agents/`. The owner's convention: each skill is its own git repo under
`~/Projects/<name>/` with `skill/SKILL.md`, symlinked to `~/.claude/skills/<name>`.

**Agent tool** (in-session): `subagent_type`, `model` (`sonnet|opus|haiku|fable`), `prompt`,
`run_in_background`, `isolation: "worktree"` (auto-cleaned if unchanged). Custom agent types
from `.claude/agents` carry their own model/effort/tools. `SendMessage` continues a spawned
agent with context intact.

**Workflow tool** (dynamic workflows): Claude writes a JS script using `agent()`, `parallel()`,
`pipeline()`, `phase()`; runs in background; only when the user opted in ("workflow",
"ultracode", or a skill instructs it). Default size guideline: ≤15 agents. Patterns documented:
fan-out-and-synthesize, adversarial verification, loop-until-done, pipeline,
classify-and-act, tournament.

**/goal**: session-scoped completion condition, up to 4,000 chars; after each turn a small
fast model (defaults to Haiku; override with `ANTHROPIC_DEFAULT_HAIKU_MODEL`) judges
met/not-met/impossible from the transcript only (no tools). Works non-interactively
(`claude -p "/goal ..."`), restores on resume, defers evaluation while background work runs
(check-ins after 30 min). Bound it with "or stop after N turns". It is a prompt-based Stop
hook underneath.

**/loop**: re-run a prompt on an interval or self-paced (`ScheduleWakeup`). **Routines /
scheduled cloud agents**: `/schedule` skill creates cron-triggered cloud runs.

**Vision**: Claude reads screenshots/images via the Read tool. Available here: an iOS Simulator
MCP (`build`, `launch`, `screenshot`, `inspect` accessibility tree, `tap`, `swipe`), Chrome
DevTools MCP and Playwright MCP (screenshots, snapshots, Lighthouse), an in-app browser.

**Installed skills the new skill can call** (via the Skill tool): `severe-testing`,
`deep-research`, `frontend-design`, `web-design-guidelines`, `dataviz`, `design` (canvas
mockups), `simplify`, `code-review`, `security-review`, `audit`, `improve`, `imagegen`,
`skill-creator`, `run`, `schedule`, `loop`, `workflow-authoring`, `claude-api`, tavily
search/extract/crawl/research, `google-dev-docs-style`, `writing`.

## 3. Output contract for your report

Write Markdown to the exact path in your task prompt. Structure:

1. **Executive opinion** (≤300 words): what the skill must do for this component and why.
2. **What the post says, and a critique**: where it is right, exaggerated, or wrong.
3. **Verified facts** with URLs (docs, tools, framework behavior, pricing where relevant).
4. **Detailed spec**: exactly what the skill should instruct, step by step. Include concrete
   templates, rubrics, schemas, file layouts, checklists, command lines. Be prescriptive.
5. **Conditionals by project shape**: for each of the five worked shapes (and any others that
   matter), what this component does differently, or skips.
6. **Model and effort assignment** for this component's roles (fable/opus/sonnet; effort
   level; tools; isolation; whether it should be a predefined subagent in `~/.claude/agents/`
   and its draft frontmatter + system prompt).
7. **Failure modes and anti-patterns**, including how the component can produce mirage
   completion and how the skill prevents that.
8. **Open questions and trade-offs** you could not settle, with your recommendation.
9. **Skill text candidates**: 5–20 tight passages, ready to lift into SKILL.md or a
   `references/<topic>.md` file. Plain language. Imperative voice.

Length: whatever the material needs; 4,000–10,000 words is typical. Depth beats breadth.
Do not pad. Do not edit any file except your own report. Do not touch `~/Projects/arcwell`.
Do not create branches, worktrees, or scratch files outside `/private/tmp`. When you finish,
reply with a ≤150-word summary of your top recommendations; the report on disk is the
deliverable.

## 4. The source post (verbatim)

From https://x.com/0xCodez/status/2065089060104720776:

Build self-improving agent system with Fable 5 in 14 steps : loops, dynamic workflows, routines
Most people are using Claude Fable 5 like Sonnet 4.6 with a bigger context window. They prompt it. It works for 5 minutes. They close the tab.
9 out of 10 users have never run an agent system that compounds - where every run leaves the next run smarter, every state file accumulates, every skill sharpens.
Fable 5 was built to run for days. You're using it for minutes. This is the 14-step roadmap to build the self-improving system Fable 5 was designed for.

Claude Fable 5 launched June 9, 2026 - the first publicly available Mythos-class model, the tier Anthropic put one rung above Opus.
This is the 14-step roadmap to build the self-improving system Fable 5 was designed for - sourced from Anthropic engineering posts, the team's public experiments, and verified against the launch documentation as of June 2026.
Three tiers: what Fable 5 actually unlocks, the three primitives that make it compound (loops, dynamic workflows, routines), and the self-improvement layer that turns it into a system.
14 steps. 3 tiers. Stop prompting. Start building a system that compounds.

PART 1 · What Fable 5 actually unlocks

01. Fable 5 is a Mythos-class model. Days-long autonomy is the headline.
Claude Fable 5 launched June 9, 2026 as the first publicly available Mythos-class model - the tier Anthropic introduced one rung above Opus. Mythos Preview shipped in April through Project Glasswing to a handful of critical-infrastructure partners; Fable 5 is the version Anthropic considered safe for general release, with built-in safety classifiers that decline requests in high-risk areas. Mythos 5 (without those classifiers) remains Glasswing-only.
What Fable 5 actually does that previous Claude models couldn't sustain, from Anthropic's launch documentation:
* Days-long autonomous sessions. Run inside an agent harness like Claude Code or Claude Managed Agents (CMA), Fable 5 can work for days - planning across stages, delegating to sub-agents, and checking its own work.
* Self-verification built in. Writes its own tests to check its work. Uses vision to check outputs against goals. Distills lessons into general rules. Tests its own assumptions.
* Most ambitious code work. Large migrations, complex implementations, multi-day autonomous coding sessions. The headline use case Anthropic puts forward is "hand off large projects and review completed deliverables."
* Multi-stage knowledge work. Deep research and analysis to deliverables ready for review - with minimal oversight.
The pricing matches the tier: $10 per million input tokens, $50 per million output tokens, with the existing 90% input token discount for prompt caching. Available on Claude API, AWS, Amazon Bedrock, Vertex AI, Microsoft Foundry, and the consumption-based Enterprise plan. This is not a subscription model. Heavy use earns its own bill.

02. Self-improving is not self-learning.
The phrase "self-improving agent system" gets thrown around carelessly. The version that's real and the version that's hype are very different things, and the gap is worth understanding before you build anything.
* Self-learning - the agent updates its own weights based on what it learns. Fable 5 does not do this. No publicly available model does this in production. Recursive self-improvement (RSI) is the long-term direction Anthropic itself warned about in May 2026, not the capability shipping today.
* Self-improving - the system around the agent compounds. Each session writes lessons to memory. Skills sharpen as edge cases get added. State files accumulate verified facts. Eval loops refine prompts and rubrics. The model stays the same; the environment it runs in gets sharper.
Self-improvement, in this sense, is a property of the system you build. Fable 5 has the raw capability - long context, sub-agent delegation, vision self-check, days-long stamina - that turns the environment-feedback loop into something that actually compounds run over run.
Anthropic's engineering team puts it directly: "Rather than directly prompting and steering Fable 5, it's often better to design loops that let the model self-correct in response to environment feedback (e.g., /goal or Outcomes) and manage its own context (e.g., via memory)."

03. The compound stack: four layers, one feedback loop.
* Layer 1 · Primitives. Fable 5 itself, sub-agents, worktrees, the tools the agent reaches for. Raw capability with no system around it yet.
* Layer 2 · Orchestration. /goal and Outcomes for self-correcting loops. Dynamic Workflows for complex multi-step orchestration. Routines for laptop-off cloud runs.
* Layer 3 · Memory. State files, Skills, Knowledge Bases, lessons written down. Memory is what makes tomorrow's session resume instead of restart.
* Layer 4 · Self-improvement. Vision self-checks, eval loops, rule distillation. The agent grades its own output, refines the Skill that produced it, writes the lesson back to memory. The loop closes.
The reason this architecture compounds: every output from layer 1 flows up through layer 4, where it gets graded, distilled, and written back to layer 3. Tomorrow's run at layer 1 inherits the sharpened memory and refined Skills from yesterday. The model is stateless; the system around it isn't.

04. When to use Fable 5 vs Opus 4.8 vs Sonnet 4.6. The cost-capability matrix.
Fable 5 costs ~5× what Opus 4.8 does per token. Not every step in a self-improving system needs the top tier. Route by task complexity, not by default:
* Fable 5 for the heavy-lift orchestrator role: planning across days, delegating to sub-agents, checking work with vision, distilling rules from accumulated evidence.
* Opus 4.8 for hard-but-bounded subtasks the orchestrator delegates: architecture decisions, complex debugging, deep code reviews. Also the explicit fallback for any request Fable 5's classifiers block (cyber, bio, chem, distillation).
* Sonnet 4.6 for high-volume worker tasks: lint passes, simple refactors, test scaffolding, doc updates. The bulk of fan-out work runs here.
* Haiku 4.5 for grader sub-agents and cheap classifiers. Independent context window, low cost - ideal for the verifier role Anthropic explicitly recommends.
The cost pattern: orchestrator on Fable 5, workers on Sonnet 4.6, graders on Haiku 4.5, fallback to Opus 4.8 on classifier blocks.

PART 2 · The three Primitives

05. /goal vs Outcomes. Two implementations of the same idea.
Both share the same shape: an independent grader checks the work, a not-met verdict starts the next iteration, the loop exits when the grader passes.
* Use /goal in Claude Code when the work happens at your machine and you want a quick, in-session loop with a measurable end state. Plain text goal, model grader, in-terminal feedback.
* Use Outcomes in CMA when the work needs to run for hours or days on Anthropic-hosted infrastructure. File-based rubric with gradable criteria, sub-agent grader, hard max_iterations bound.
Both share the structural move that makes them work: the agent that wrote the code is not the agent that grades it.

06. Verifier sub-agent beats self-critique.
Anthropic engineer Prithvi Rajasekaran wrote a piece on the engineering blog showing models have a hard time self-critiquing their own outputs. The Claude Code team confirmed this empirically with Fable 5: "We've found that a verifier sub-agent tends to outperform self-critique with Fable 5."
The mechanism is structural. A model evaluating its own output sees its own reasoning trail and prefers conclusions consistent with what it already wrote. A separate model evaluating the same output sees only the artifact and the rubric. The verifier has no skin in the maker's game.
Parameter Golf chart: Fable 5 made larger structural changes (TRAIN_SEQ_LEN=2048, overlapped sliding-window eval, int6 QAT) and pushed through a quantization regression to its biggest win. Opus 4.7's experiments mostly adjusted scalars. Takeaway: Fable 5 with an independent verifier explores larger hypothesis spaces and recovers from negative intermediate results. Without the verifier, the same model has nothing forcing it past the first "good enough."

07. Dynamic Workflows compose self-correction patterns.
Dynamic Workflows shipped in Claude Code on May 28, 2026. Claude writes its own JavaScript harness on the fly - agent(), parallel(), pipeline() primitives plus standard JS. Three patterns earn their place in self-improving systems:
* Fan-out-and-synthesize. Split into N independent pieces, run in parallel, synthesize. Best when each step benefits from its own clean context window.
* Adversarial verification. For each maker agent, spawn an independent verifier with no exposure to the maker's reasoning.
* Loop until done. Loop spawning agents until a stop condition is met. Pair with /goal to set a hard completion requirement.
Also: classify-and-act (route to the right model) and tournament (pairwise comparison for taste-based ranking; useful for design or naming).

08. Worktrees for parallel safety.
Two agents writing the same file is the same problem as two engineers committing to the same lines. A git worktree fixes it. Maker writes in worktree A; verifier reads in worktree B (or read-only). Parallel structural experiments each run in their own worktree; the best one merges. Days-long runs with checkpoints: each major phase a separate worktree; a failed phase doesn't poison the rest. In Claude Code: git worktree directly, --worktree flag, and isolation: worktree on subagents (fresh checkout that cleans itself up).

09. Routines for days-long orchestration.
Routines (April 14, 2026, research preview): saved Claude Code configurations that run on Anthropic-managed cloud infrastructure on a trigger. Schedule triggers (morning briefing: re-run yesterday's eval suite, distill new failure modes into Skills, post digest). API triggers (CI fails → investigate; Sentry alert → triage). GitHub event triggers (on PR open evaluate against latest Skills; on merge write new patterns back to the Skill).

PART 3 · The Self-Improvement Layer

10. The 5-stage memory progression (from Anthropic's Continual Learning Bench 1.0):
1. Fail - document the failure with enough detail to be useful later.
2. Investigate - figure out why the failure happened.
3. Verify - turn the diagnosis into a checked fact, not a guess.
4. Distill - turn the verification into a general rule that applies beyond the specific case.
5. Consult - on the next task, read the rule instead of re-deriving the fact.
Measured: Sonnet 4.6 exits at step 1 (failure notes and guesses, rarely consults). Opus 4.7 exits at step 3 (verification coverage 7–33%, median ~17%). Fable 5 tends to complete the progression (verification coverage up to 73%, distills general rules).

11. The state file. Where memory actually lives.
Five sections matching the five stages:
```
# Project memory · trading-platform
## Verified facts            # stage 3 — stop guessing about these
- prc is in dollars, not cents. Verified via SELECT MIN(prc), MAX(prc) FROM trades.
## General rules             # stage 4 — consult before re-deriving
- When querying time-bucketed metrics, always include timezone.
- Auth middleware order matters: rate_limit -> jwt -> rbac.
## Open failures (investigate next session)   # stage 1 → 2
- 2026-06-09: tests/e2e/checkout flakes ~1 in 50 runs. Hypothesis: webhook race. Repro in debug/checkout-flake.md.
## Lessons learned           # stage 4 distillations
- PowerShell hits TLS 1.2 issue on Windows CI runners. Always shell out to bash.
## Last session              # stage 5 — resume, don't restart
2026-06-10 03:30 UTC · 7 failures classified, 3 fixes drafted, 4 escalated. Next: verify the auth middleware fix.
```
Two operational rules: **Write before walking away** (every session ends by updating STATE.md) and **Read at session start** (every session begins by reading STATE.md and the relevant Skills).

12. Skills that compound. Write the lesson into the Skill, not just the chat.
STATE.md is project memory; Skills are procedural memory that applies across projects. After any non-trivial failure, write the lesson into the Skill itself. A two-week-old Skill has new sections: known failure modes, rules from post-mortems, anti-patterns observed. Example ci-triage skill with Classification rules, Known failure modes (added by the loop), Anti-patterns (never disable a failing test to make CI green; never modify workflows without approval; never touch payments without security review), State (update STATE.md after each run), Eval suite (run weekly; newly failing case → add to known failure modes after verifier confirms).

13. Self-verification via vision.
Maker sub-agent writes UI code, renders a screenshot. Verifier sub-agent reads the screenshot with vision, compares against the goal description, design tokens in the project Skill, and the previous screenshot from STATE.md. Match → complete. Mismatch → describe the gap, hand back to maker with a structured diff.

14. The Mythos safety boundary.
Fable 5 ships with classifiers that decline in cybersecurity vulnerability research, biology, chemistry, and model distillation; Anthropic falls back to Opus 4.8 automatically. Architect for the fallback: route those tasks to Opus explicitly or surface to a human. A loop that silently fails on a classifier block looks identical to a loop that fails on a real error until you debug it. Treat the boundary as a known fallback, not a failure mode.

§ The mistakes that keep Fable 5 at 10% of its potential
* Using Fable 5 like Sonnet with more context (5-minute prompt-and-close).
* Self-critique instead of an independent verifier.
* No STATE.md — every session restarts from zero.
* Skills that never get written to.
* Fable 5 on tasks Sonnet would handle. Route by complexity.
* Running long sessions on a laptop.
* Ignoring the safety boundary.
* No vision-verify on visual tasks.
* Skipping /goal or Outcomes — loops stop at "handled enough" instead of done.
* No retention policy review.

Conclusion: Self-improvement is a property of the system, not the model. Build the system.
