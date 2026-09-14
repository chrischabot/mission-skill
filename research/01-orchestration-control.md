# R01 — Orchestration & control loop (coordination, phases, goal loops, long-running execution)

Lane: coordination, control and the orchestration loop (post steps 01–05, 09, 14 and the compound stack).

## 1. Executive summary & strong opinions

The control loop is the part of the skill that turns "build me X" into days of work that actually finishes. Most of
the post's orchestration primitives are real in September 2026: `/goal`, Managed Agents Outcomes, Routines, dynamic
workflows, Fable 5.1, and classifier fallback to Opus 4.8. But several of them work differently from what the post
implies, and two of those differences directly affect the user's constraints. First, the `/goal` evaluator defaults to
Haiku. Second, the `opus`/`sonnet` aliases now resolve to Opus 5 / Sonnet 5, not Opus 4.8 / Sonnet 4.6. The skill should
treat the platform primitives as accelerators and keep its own file-based control plane, which works in any harness,
as the source of truth.

Verdicts (each is actionable):

1. **Files are the control plane; platform loops are optional engines.** Keep the mission's truth in
   `mission/PLAN.md`, `mission/STATUS.md` and a machine-checkable `mission/acceptance.json`, never only in a session
   transcript, a `/goal` string, or a CMA event stream. Every primitive the post names can be missing, rate-limited or
   changed. Files survive compaction, resume, harness switches and human hand-offs. Evidence: Anthropic's own
   long-running harness bridges context windows with `claude-progress.txt` + a JSON feature list + git history
   (https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).
2. **The maker never grades itself: acceptance is decided by a fresh-context verifier reading artifacts and evidence.**
   This holds in every form: CMA Outcomes' grader, `/goal`'s evaluator, or a plain verifier sub-agent. It is the
   structural move all the verified sources agree on (https://platform.claude.com/docs/en/managed-agents/define-outcomes,
   https://www.anthropic.com/engineering/harness-design-long-running-apps).
3. **`/goal` is a stop-condition shortcut, not a verifier.** Its evaluator only reads the transcript and "doesn't run
   commands or read files independently" (https://code.claude.com/docs/en/goal), and it defaults to Haiku. Use `/goal`
   only with conditions that point at evidence (a test exit code the maker printed, a board with zero open rows), pair
   it with a real verifier sub-agent, and repoint the small fast model at Sonnet 4.6 or don't depend on it.
4. **Pin model IDs, never aliases.** On the Anthropic API `opus` → Opus 5 and `sonnet` → Sonnet 5
   (https://code.claude.com/docs/en/model-config). The user mandated Opus 4.8 and Sonnet 4.6, so agent frontmatter and
   Agent-tool calls must use full model names (or `ANTHROPIC_DEFAULT_*_MODEL` pins), and the intake phase must verify
   they resolve.
5. **Every mission runs through ten phases, but the skill scales the ceremony by size (S/M/L/XL) and never lets a gate
   be skipped silently.** A one-line bug fix still has intake → verify → retro; it just collapses spec/design/plan into
   a single paragraph. Each phase has an explicit exit gate with a named evidence artifact.
6. **Human checkpoints are few, early and at irreversibility.** Stop for a human only at (a) spec/acceptance sign-off
   for L/XL missions, (b) anything irreversible or externally visible (prod deploy, data migration, push to protected
   branches, spending), and (c) a stop rule firing. Everything else runs autonomously, and assumptions go into an
   assumptions log instead of becoming questions.
7. **Every loop has three independent stop bounds: success, budget, and futility.** Success is verifier PASS on every
   acceptance check. The budget is max iterations / tokens / wall-clock. Futility is no progress for N iterations, the same
   failure twice, or a verifier "impossible". Without futility detection, loops burn money at a plateau. CMA's own
   max_iterations defaults low (3 per secondary source https://avinashsangle.com/blog/claude-managed-agents-outcomes).
8. **The orchestrator runs on Fable 5.1 at medium effort for M+ missions; workers default to Sonnet 4.6; the verifier
   is always at least one step "harder to fool" than the maker.** Fable 5.1 at Low/Medium matches or beats Fable 5 at
   much lower cost (https://www.anthropic.com/claude-fable-and-mythos-5-1). The orchestrator should spend its tokens on
   planning, integration and judgment, never on typing code.
9. **Sub-agent briefs are contracts.** Each brief states the objective, context pointers, owned files, the acceptance checks
   it must pass, forbidden actions, budget and an exact return format. Vague briefs cause duplicated work and gaps
   (https://www.anthropic.com/engineering/multi-agent-research-system). Ship the template verbatim.
10. **Size tasks to "one verifiable change in one fresh context".** One feature, one acceptance check, ≤ ~15 files touched,
    finishable well inside a sub-agent's context. Agents that try to one-shot run out of context mid-feature and leave
    undocumented half-work (https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).
11. **Prefer context resets with handoff files over relying on compaction for multi-hour runs.** Compaction keeps
    continuity but not a clean slate. Resets plus a structured handoff fix coherence loss and premature wrap-up
    (https://www.anthropic.com/engineering/harness-design-long-running-apps). Guardrails stated only in conversation can
    be lost in compaction (https://code.claude.com/docs/en/auto-mode-config), so they belong in settings and files.
12. **Treat classifier refusals as a routed outcome, not an error, and make the switch visible.** In Claude Code a
    flagged Fable request silently re-runs on Opus 4.8 and stays there for the session
    (https://github.com/anthropics/claude-code/issues/74311). The skill must log every fallback in STATUS.md, restore
    the orchestrator model deliberately, and send security-heavy tasks straight to Opus 4.8 up front.
13. **Autonomous runs need guardrails in settings, not in prose.** Use `permissions.deny` for destructive commands,
    `permissions.ask` or a PreToolUse hook for push/PR/deploy, `claude/`-prefixed branches or worktrees for all writes,
    and no connector writes that the mission doesn't need. Routines run with no approval prompts at all
    (https://code.claude.com/docs/en/routines).
14. **Days-long does not mean one session.** Model long missions as many bounded sessions (interactive, `claude -p`, or
    Routines) that each read STATUS.md, advance one milestone slice, verify, write back and exit. This is what makes resume
    trivial and cost observable.
15. **Review cadence must be budgeted.** The user's own project needed a process amendment after eighteen adversarial
    rounds "prevented progress" (arcwell/docs/operations/review-process-amendment.md:3-5,25-31). Cap review rounds per
    milestone and move remaining findings into the dispositions log.

## 2. Claim check

Legend: **V** = verified against a primary source; **V2** = verified only via secondary sources; **P** =
plausible but unverified; **H** = likely hype or wrong in a way that matters.

| # | Post claim (steps 01–05, 09, 14 + stack) | Verdict | Evidence | What the skill should do |
|---|---|---|---|---|
| 01a | Fable is "Mythos-class", one rung above Opus; Mythos without the extra safeguards is restricted | **V** (for 5.1) | "Claude Fable 5.1 and Claude Mythos 5.1 are the same model, but with different levels of safeguards… Mythos 5.1 is available only through our trusted access programs" (https://www.anthropic.com/claude-fable-and-mythos-5-1) | Treat Fable 5.1 as the top tier available; never plan for Mythos. |
| 01b | Fable 5 launched June 9 2026 | **V2** | Secondary only (https://avinashsangle.com/blog/claude-code-fable-5-model-routing). Fable 5.1 released Sep 1 2026 (https://codewalkers.com/news/ai-models/claude-fable-5-1-mythos-5-1/) | Irrelevant to behaviour; target Fable 5.1 (`claude-fable-5-1`). |
| 01c | Days-long autonomous sessions | **P** (hours well evidenced) | Launch quotes: "ran for hours unattended, with strong verification loops", 3-day prototype (https://www.anthropic.com/claude-fable-and-mythos-5-1); model-config says Fable is "suited to tasks larger than a single sitting" (https://code.claude.com/docs/en/model-config) | Design for days as a *sequence of bounded sessions* with file handoffs, not one immortal session. |
| 01d | $10/$50 per MTok, 90% cache discount | **V2**, and outdated | $10/$50 unchanged for 5.1; cache reads made cheaper, ~25% lower typical cost, up to ~45% on agentic work (https://www.anthropic.com/claude-fable-and-mythos-5-1, https://codewalkers.com/news/ai-models/claude-fable-5-1-mythos-5-1/) | Keep prompts cache-friendly: a stable system prompt/skill preamble, files appended at the end. Never hardcode prices in the skill. |
| 02 | "Design loops that let the model self-correct… (e.g., /goal or Outcomes) and manage its own context" | **V2** (quote) / **V** (spirit) | The quote is attributed but no primary text was located (https://growthexe.substack.com/p/designing-loops-with-claude-fable). Docs say for Fable: "Describe the outcome, not the steps… set a goal", "Skip the verification reminders" (https://code.claude.com/docs/en/model-config) | Orchestrator prompts state outcomes plus acceptance checks, not step lists; steps belong in worker briefs for cheaper models. |
| 03 | Four-layer compound stack | **P** (framing, not a fact) | No Anthropic source uses this taxonomy. The pieces exist (memory, dreaming, outcomes, multiagent: https://claude.com/blog/new-in-claude-managed-agents) | Use it as a mental model only. The skill's structure should be phases + control files + retro, not "layers". |
| 04a | Opus 4.8 is the fallback for classifier blocks | **V** | Claude Code re-runs flagged Fable requests on "a fixed default Opus model (currently Opus 4.8)", sticky for the session (https://github.com/anthropics/claude-code/issues/74311). Launch page: "cybersecurity tasks were completed by Claude Opus 4.8" (https://www.anthropic.com/claude-fable-and-mythos-5-1) | Log it and restore the model. Route cyber-flavoured tasks to Opus 4.8 up front. |
| 04b | Fable ≈5× Opus 4.8 per token | **H/P** (conflicting) | One secondary source says 2× (https://avinashsangle.com/blog/claude-code-fable-5-model-routing) | Route by task difficulty and verifier outcomes, not by an assumed ratio. Measure with `--output-format json` `total_cost_usd` (https://code.claude.com/docs/en/headless). |
| 04c | Haiku for graders | **V** that the default is Haiku; **overridden** by user | `/goal` evaluator "defaults to Haiku on the Claude API" (https://code.claude.com/docs/en/goal) | Graders = Sonnet 4.6 (low/medium) or Opus 4.8. Repoint the small fast model or don't rely on `/goal` as the grader. |
| 05a | `/goal`: plain-text goal, model grader, in-terminal loop | **V**, with a big caveat | Evaluator returns met / not yet met / impossible after each turn; it "doesn't run commands or read files independently"; condition ≤4,000 chars; add "or stop after 20 turns" to bound; works under `claude -p` (https://code.claude.com/docs/en/goal) | Use it for stop conditions over *printed evidence*. Never let it be the only acceptance gate. |
| 05b | Outcomes: file-based rubric, sub-agent grader, hard max_iterations | **V** (rubric, grader) / **V2** (max_iterations) | Rubric required, grader in separate context (https://platform.claude.com/docs/en/managed-agents/define-outcomes); max_iterations default 3, max 20 (https://avinashsangle.com/blog/claude-managed-agents-outcomes); up to +10 pts task success (https://claude.com/blog/new-in-claude-managed-agents) | Emulate with verifier sub-agent + `rubric.md` + iteration cap in STATUS.md when not on CMA. |
| 05c | Outcomes best for "ML training, GPUs, multi-day" | **P** | Not confirmed in fetched pages | Don't encode GPU claims. The skill targets Claude Code first. |
| 05d | "The agent that wrote the code is not the agent that grades it" | **V** | Grader "uses a separate context window to avoid being influenced by the main agent's implementation choices" (https://platform.claude.com/docs/en/managed-agents/define-outcomes); verifier sub-agent quote attributed to Anthropic's Lance Martin (https://x.com/RLanceMartin/status/2064397389189071163) | MUST rule (see §4). |
| 09a | Routines: saved config running on Anthropic cloud with schedule/API/GitHub triggers; research preview | **V** | https://code.claude.com/docs/en/routines | Offer a Routine recipe for recurring missions (nightly eval, CI triage). |
| 09b | Routines launched April 14 2026 | **P** | Date not on the docs page | Irrelevant. |
| 09c | Example: `/schedule … use Fable 5 in CMA … /goal don't stop until…` | **H** (conflates products) | Routines are Claude Code cloud sessions with a per-routine model selector, not CMA. They run with "no permission-mode picker and no approval prompts" (https://code.claude.com/docs/en/routines) | A Routine prompt must be self-contained, carry its own stop rule and budget, and write STATUS.md. Don't mix CMA vocabulary into it. |
| 14a | Fable classifiers decline cyber, bio, chem, distillation | **V** with corrections | API categories are `cyber`, `bio`, `frontier_llm`, `reasoning_extraction`, `general_harms`. There is no "chem" category (https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback). Fable 5.1 blocks 60% fewer cyber false positives and may *discover* vulnerabilities but not develop exploits (https://www.anthropic.com/claude-fable-and-mythos-5-1) | Security review of your own code is usually fine on 5.1. Exploit/pentest logic → Opus 4.8 or a human. |
| 14b | Fallback is automatic | **V** in Claude Code; **not** by default on the raw API | API refusals are `stop_reason: "refusal"`; auto-retry requires `fallbacks: "default"` (beta) or client code (https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback) | Harness-specific handling; detect and log in both. |
| 14c | Silent classifier failure looks like a real error | **P**, but the real risk is different | In Claude Code the danger is a *silent, sticky model downgrade* whose effort level carries over (issues #74311, #73833 via https://github.com/anthropics/claude-code/issues/74311) | STATUS.md "Model/fallback events" section. The orchestrator checks the active model at each phase boundary. |
| 14d | "Audit the system card (319 pages)" | **P** | Not verified | Omit from the skill. |
| M1 | "Days-long needs cloud infra: CMA or Routines" | **H** (overstated) | `/loop` stops when the machine is off (secondary summary https://cldnavi.com/en/blog/claude-code-loops-guide-2026/), but resumable bounded sessions work locally (https://code.claude.com/docs/en/goal "Resume with an active goal") | Local runs are fine if state is in files. Use Routines when you need laptop-off *triggers*. |
| M2 | Without objective stop condition + independent grader, loops stop at "handled enough" | **V** in substance | "A later agent instance would look around, see that progress had been made, and declare the job done" (https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | The acceptance file starts all-failing; only the verifier flips entries. |

## 3. Deep findings

### 3.1 Start simple, escalate structure only when it pays

Anthropic's baseline guidance is still "find the simplest solution possible, and only increase complexity when
needed". Their pattern catalogue has five shapes: prompt chaining with programmatic *gates* between steps, routing,
parallelization (sectioning/voting), orchestrator-workers, and evaluator-optimizer
(https://www.anthropic.com/engineering/building-effective-agents). The mission loop in this skill is a composition of
three of them. A **gated chain** drives the phases, **orchestrator-workers** covers the build, and an
**evaluator-optimizer** loop runs at each gate. Evaluator-optimizer fits when "we have clear evaluation criteria, and
when iterative refinement provides measurable value". That is exactly why §4 makes acceptance checks a precondition
for looping.

Multi-agent structure is expensive. In Anthropic's Research system a multi-agent setup beat single-agent Opus by 90.2%,
but "agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more", and
"most coding tasks involve fewer truly parallelizable tasks than research"
(https://www.anthropic.com/engineering/multi-agent-research-system). Their early failure modes are the ones this skill
must prevent by rule: "spawning 50 subagents for simple queries", endless searching, and agents distracting each other.
The fix was embedded scaling rules (1 agent / 3–10 tool calls for simple lookups; 2–4 sub-agents for comparisons; more
only for complex work) and detailed delegation, where each sub-agent needs "an objective, an output format, guidance on
the tools and sources to use, and clear task boundaries". The skill should copy both: an explicit S/M/L/XL fan-out table
and a mandatory brief template.

### 3.2 Goal-driven loops: what the primitives really do

**`/goal` (Claude Code).** One goal per session. After each turn, the configured small fast model (default Haiku on the
Claude API) reads the condition plus the conversation and returns *not yet met* (the reason becomes guidance for the next
turn), *met*, or *impossible*. `/goal` is literally "a wrapper around a session-scoped prompt-based Stop hook". Crucially,
the evaluator "doesn't run commands or read files independently", so a condition must be something "Claude's own output
can demonstrate". A good condition has one measurable end state, a stated check, and constraints that must not change,
and it can include a turn/time bound ("or stop after 20 turns"). `/goal` works in `claude -p`, and an active goal is
restored on resume with its counters reset (https://code.claude.com/docs/en/goal). Implications:

- The evaluator can be *fooled by the maker's narration*. If the maker claims tests pass without printing output, a
  transcript-only judge may accept it. `/goal` is therefore a **stop-condition engine**, not an acceptance gate.
- Budget clauses are judged by a model reading the transcript, not enforced by a counter. Hard caps must live in files
  and scripts too.
- With the user's no-Haiku constraint, the evaluator model must be repointed via model configuration (the exact
  variable is inferred, not verified; see §9), or the skill must prefer its own verifier sub-agent.

**Outcomes (Claude Managed Agents).** A `user.define_outcome` event carries a description plus a required markdown
rubric. The harness "automatically provisions a *grader*" in "a separate context window to avoid being influenced by the
main agent's implementation choices". The grader returns per-criterion explanations that feed the next iteration
(https://platform.claude.com/docs/en/managed-agents/define-outcomes). Secondary sources add that the grader shares
the writer's model and tools, re-checks the full artifact each iteration, and that `max_iterations` defaults to 3 (max 20)
(https://avinashsangle.com/blog/claude-managed-agents-outcomes). Anthropic reports "up to 10 points" of task-success
improvement, largest on the hardest problems (https://claude.com/blog/new-in-claude-managed-agents). The rubric
guidance transfers directly to Claude Code: criteria must be explicit and gradeable ("The CSV contains a price column
with numeric values", not "The data looks good"). One practical trick is to bootstrap a rubric by having Claude
analyse a known-good artifact.

**Loop taxonomy.** Anthropic's loops guide (via secondary summary https://cldnavi.com/en/blog/claude-code-loops-guide-2026/;
the primary https://claude.com/blog/getting-started-with-loops exceeded fetch limits) describes four loops.
*Turn-based* is the normal agent loop, improved by encoding verification in a skill. *Goal-based* uses `/goal`.
*Time-based* uses `/loop` locally or `/schedule` in the cloud. *Proactive* combines schedule + goal + worktrees +
adversarial reviewer. Its token advice matches this lane's opinions: define clear success and stop conditions, pilot a
small slice before launching hundreds of agents, use scripts for deterministic work, and watch `/usage`, `/goal` status
and `/workflows`.

**Stop hooks** are the durable, harness-native form: `/goal` and a Stop hook "both fire after every turn", but a Stop
hook "lives in your settings file" and "can run a script for deterministic checks or a prompt for model-evaluated ones"
(https://code.claude.com/docs/en/goal). For this skill, a script-based Stop hook that runs `mission/check.sh` is the
strongest cheap gate, because it actually executes the checks instead of reading narration.

### 3.3 Long-running execution: the failure modes are known

Anthropic's long-running harness work names four failure modes. All of them map to control-loop rules
(https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents,
https://www.anthropic.com/engineering/harness-design-long-running-apps):

1. **One-shotting.** The agent "tried to do too much at once", ran out of context mid-feature, and the next session had to
   guess. Fix: one feature per session or sub-agent, commit plus progress note at the end.
2. **Premature completion.** "A later agent instance would look around, see that progress had been made, and declare the
   job done." Fix: an initializer writes a comprehensive feature list (200+ entries for a claude.ai clone), all marked
   `"passes": false`. Agents may only flip the flag, and "It is unacceptable to remove or edit tests". The list is JSON
   because "the model is less likely to inappropriately change or overwrite JSON files compared to Markdown".
3. **Marking complete without end-to-end testing.** Fix: browser automation, "do all testing as a human user would", and
   run a smoke test *before* starting new work so a broken state gets repaired first.
4. **Coherence loss and "context anxiety".** Context resets (fresh agent + structured handoff) differ from compaction:
   "compaction preserves continuity, it doesn't give the agent a clean slate". Resets add orchestration overhead but
   were essential for weaker models. Context engineering explains why: "context rot", a finite "attention budget", and
   the target of "the smallest possible set of high-signal tokens"
   (https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).

There is also a standard session-start ritual: `pwd` → read progress file + `git log` → read feature list → pick the
highest-priority failing item → run `init.sh` and a basic e2e check → only then implement. The evaluator side matters as
much. "Tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical
of its own work". The design evaluator ran 5–15 iterations, used Playwright to navigate the live page, and after each
evaluation the generator decided to refine or pivot. Scores plateaued, and a middle iteration was sometimes best
(https://www.anthropic.com/engineering/harness-design-long-running-apps). So: keep the best-scoring artifact, not the
last one, and stop on plateau.

### 3.4 Execution surfaces in Claude Code (and how to degrade)

Claude Code offers four ways to parallelize (https://code.claude.com/docs/en/agents):

- **Subagents** run in their own context window with a custom prompt, tool restrictions and independent permissions, and
  return a summary (https://code.claude.com/docs/en/sub-agents). Descriptions cost context (startup warning above 15,000
  tokens combined), so custom agents need short descriptions. The built-in Explore/Plan agents are read-only and skip
  CLAUDE.md.
- **Agent teams** give multiple sessions a shared task list and messaging. They are experimental, disabled by default,
  and "don't isolate teammates in worktrees", so work must be partitioned by file.
- **Dynamic workflows** are a JavaScript script Claude writes, and "the script" decides what runs next. Intermediate
  results live in script variables, so "Claude's context holds only the final answer". A workflow can "have independent
  agents adversarially review each other's findings", scales to "dozens to hundreds of agents per run", and is resumable
  (https://code.claude.com/docs/en/workflows). `/deep-research` is bundled. Workflows are triggered by asking for a
  workflow, by the `ultracode` keyword, or by `/effort ultracode`.
- **Agent view** (`claude agents`) is for background sessions you hand off.
- Supporting pieces: worktrees; `/batch` splits one change into 5–30 worktree-isolated sub-agents that each open a PR.

Opinion: the *default* engine for this skill is plain subagents driven by file state, because it works everywhere,
including other harnesses where only "spawn a worker with a prompt" exists. Escalate to a dynamic workflow when a phase
needs more than about 8 parallel workers or cross-checking votes (audits, 500-file migrations, research). Agent teams
are not a dependency while experimental.

**Headless** (`claude -p`) returns an exit code, and `--output-format json` reports `total_cost_usd` with a per-model
breakdown (client-side estimate). `--bare` skips hooks, skills, subagents, plugins, MCP, auto memory and CLAUDE.md, and
is "recommended for scripted and SDK calls, and will become the default for `-p`". A skill-driven headless run must
therefore either avoid `--bare` or pass `--add-dir`/`--agents`/`--settings` explicitly. Without `--bare`, `-p` "runs
the hooks in a project's `.claude/settings.json`… even in a folder you've never trusted". Background subagents keep the
process open until they finish, up to a 10-minute idle ceiling (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`). SIGTERM exits
143 and leaves the turn unfinished for resume (https://code.claude.com/docs/en/headless).

**Routines** are saved prompt + repos + environment + connectors, run in Anthropic's cloud on schedule, API or GitHub
triggers. They are in research preview, create `claude/`-prefixed branches, and run "autonomously as full Claude Code
cloud sessions: there is no permission-mode picker and no approval prompts". Included connectors can write without
asking, actions appear under the user's identity, and "the prompt must be self-contained and explicit about what to do
and what success looks like" (https://code.claude.com/docs/en/routines). GitHub Actions is a further CI surface
(https://code.claude.com/docs/en/github-actions).

### 3.5 The safety boundary and guardrails

Fable 5.1, Fable 5 and Opus 5 carry classifiers. On the API a refusal is HTTP 200 with `stop_reason: "refusal"`, a
category (`cyber`, `bio`, `frontier_llm`, `reasoning_extraction`, `general_harms`), and unstable explanation text. It can
arrive mid-stream, in which case partial output must be discarded. A server-side `fallbacks: "default"` beta retries on a
recommended model (https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback). In Claude Code the
fallback is automatic but **sticky**: the session stays on Opus 4.8 until `/model`. `fallbackModel` covers only
availability errors, and `switchModelsOnFlag: false` gives an interactive prompt that is unusable unattended
(https://github.com/anthropics/claude-code/issues/74311). Fable 5.1 cut cyber false positives by 60% and allows
vulnerability discovery but not exploit development (https://www.anthropic.com/claude-fable-and-mythos-5-1).

Guardrails for autonomy come from auto mode's classifier, which "blocks anything irreversible, destructive, or aimed
outside your environment". But it *allows pushes to any branch including the default branch, and PR creation* by
default. Deny/ask rules run before the classifier, and boundaries stated only in conversation "can be lost if context
compaction removes the message" (https://code.claude.com/docs/en/auto-mode-config). So human checkpoints need
`permissions.ask`, or a PreToolUse hook for variants like `git -C dir push`. Hard bans belong in `permissions.deny`.

### 3.6 Evidence from the user's own practice (arcwell, read-only)

- Gate discipline: "An item is checked only after the gate command has been run green on a clean workspace"
  (arcwell/docs/operations/milestone-ledger.md:3-4). Requirements whose clauses had no oracle were *moved* to later
  milestones rather than weakened (milestone-ledger.md:47). Live gates stay PENDING with "no live gate may be marked
  PASSED without cited evidence" (milestone-ledger.md:279). The skill's gate table encodes the same honesty statuses.
- Review fatigue: after eighteen adversarial rounds, review was consolidated into one cross-milestone review, "the
  amendment changes review timing, not the quality bar" (arcwell/docs/operations/review-process-amendment.md:3-18,25-31).
  This supports capped review rounds plus a milestone-end consolidated review.
- Handoffs: the 2026-08-21 handoff is self-contained. It has orientation (repo, commit, deployed resources), what works
  (verified against sent bytes), what a remote agent *cannot* do, priority-ordered fixes with exact file:line references,
  and one verification-bar command (arcwell/docs/handoff/2026-08-21-morning-remediation-handoff.md:3-41). That is the
  right shape for `HANDOFF.md`.

## 4. Opinionated spec for the skill

Normative keywords: MUST / SHOULD / MAY. "Orchestrator" means the top-level session running the skill. "Verifier" means
any fresh-context agent that judges artifacts it did not produce.

### 4.1 Orchestrator role and the mission loop

- **O1 MUST** keep the mission control plane in files under `mission/` (paths configurable): `BRIEF.md` (expanded
  intent), `PLAN.md` (milestones + task DAG), `STATUS.md` (task board + gate state + budget), `acceptance.json`
  (all checks, start all failing), `ASSUMPTIONS.md`, `DECISIONS.md`, `HANDOFF.md`. Project memory (`STATE.md`,
  learnings) belongs to the memory lane. The orchestrator reads it at start and appends to it at retro, but MUST NOT use
  STATE.md as the task board.
- **O2 MUST** run the loop *read → decide → dispatch → integrate → verify → write → (continue | stop)* and write STATUS.md
  before every dispatch wave and after every integration. If the session died now, STATUS.md must be enough to resume.
- **O3 MUST NOT** implement large changes itself on M+ missions. The orchestrator plans, briefs, integrates small
  glue, adjudicates and writes the control files. Direct edits are allowed for ≤ ~30-line glue/integration fixes.
- **O4 MUST** classify the mission at intake by *shape* (§6) and *size* (S/M/L/XL). The size sets which phases collapse,
  the fan-out ceiling, the review rounds and the budget. It MUST be recorded in STATUS.md and MAY be re-classified at
  any gate with a DECISIONS.md entry.
- **O5 MUST** expand a high-level prompt into `BRIEF.md` before planning: goal restated as outcomes, users/actors, in
  scope / out of scope, constraints (tech, cost, deadlines, models), definition of done as acceptance checks, risks, and
  numbered open questions *each with a default assumption*.
- **O6 MUST** log every non-trivial assumption in ASSUMPTIONS.md (id, assumption, why, confidence, how to invalidate,
  owner phase) instead of stopping to ask. The exception is questions whose wrong answer is irreversible or expensive
  (§4.3).
- **O7 MUST** log decisions in DECISIONS.md (ADR-lite: id, date, decision, options considered, rationale, reversibility,
  evidence link). Every model downgrade, scope cut, gate waiver and review-round cap is a decision.
- **O8 SHOULD** describe outcomes, not step lists, when the orchestrator runs on Fable ("Describe the outcome, not the
  steps", https://code.claude.com/docs/en/model-config). Worker briefs for Sonnet 4.6 SHOULD contain explicit steps.

### 4.2 Phase gate table (paste-ready)

Every phase ends at a gate. A gate is PASSED only when its evidence exists *and* a verifier (not the author) confirmed
it. The allowed gate states are `PENDING`, `PASSED`, `PASSED-WITH-WAIVER (DEC-id)`, `BLOCKED (reason)` and
`PENDING-LIVE (mechanism delivered, live evidence not yet run)`. The last one mirrors the user's ledger practice
(arcwell/docs/operations/milestone-ledger.md:279).

| Phase | Purpose | Exit gate (all MUST hold) | Evidence artifact | Gate verifier | Human checkpoint? | S | M | L/XL |
|---|---|---|---|---|---|---|---|---|
| 0 Intake | Understand ask, classify shape/size, set budget | BRIEF.md has outcomes, scope, DoD draft, assumptions with defaults; size+shape recorded; model pins verified | `BRIEF.md`, `STATUS.md` header | Orchestrator self-check against checklist (cheap) | No (L/XL: optional ask if a *blocking* ambiguity exists) | 5-line brief | full | full |
| 1 Research | Remove unknowns that change design | Every open question is answered with a source, converted to an assumption, or escalated; research log written | `research/` notes with URLs/paths | Sonnet 4.6 medium spot-checks citations | No | skip unless unknown API | targeted | fan-out |
| 2 Spec | Define *what* and *done* | Each requirement has ≥1 acceptance check that is executable or rubric-gradeable; no check duplicates another; out-of-scope list present | `SPEC.md`, `acceptance.json` (all `passes:false`) | Opus 4.8 medium adversarial spec review ("find untestable or missing criteria") | **Yes for L/XL** (sign-off on acceptance.json); M: notify only | merged into brief | yes | yes |
| 3 Design | Define *how* | Architecture, interfaces/contracts, data model, test strategy, risk list; every acceptance check mapped to a component | `DESIGN.md` (+ ADRs) | Opus 4.8 high design review | L/XL only if irreversible choices (datastore, public API) | skip | short | full |
| 4 Plan | Milestones → tasks DAG | Every task has owner role, model, inputs, owned files, acceptance check ids, size ≤ one fresh context; DAG acyclic; critical path marked; budget allocated per milestone | `PLAN.md`, STATUS.md board rows | Sonnet 4.6 medium structural lint + orchestrator | No | 1–3 tasks | yes | yes |
| 5 Build | Implement tasks in waves | Each task's checks green *on integrated branch*; no unowned file edits; commits per task | diffs, test output logs | Per-task verifier (see §5) | No | yes | yes | yes |
| 6 Verify | Prove mission-level DoD | `acceptance.json` 100% `passes:true` by verifier runs; full test suite green on clean checkout; e2e/UX checks where applicable | `verify/REPORT.md` with command outputs | Fresh Opus 4.8 or Sonnet 4.6 high verifier; never the builder | No | yes | yes | yes |
| 7 Review | Adversarial quality/security review | All findings dispositioned (fixed / accepted-risk DEC / deferred with task); review rounds ≤ cap | `review/FINDINGS.md` + dispositions | Opus 4.8 high (security-heavy: Opus 4.8 by default) | L/XL: human reads summary | 1 pass | 1–2 rounds | ≤3 rounds + final consolidated |
| 8 Release | Ship safely | Release checklist green; rollback path documented; irreversible steps approved | `RELEASE.md`, PR link | Sonnet 4.6 medium checklist verifier | **Yes** for prod deploy, data migration, publishing, spending | PR only | PR | PR + staged rollout |
| 9 Retro | Compound | Failures classified and turned into lessons/skill edits (memory lane); STATUS.md closed; cost & iteration stats recorded | `RETRO.md`, STATE.md append | Sonnet 4.6 low | No | 3 bullets | yes | yes |

Rules for the table:

- **G1 MUST** never advance with a gate in `PENDING` or `BLOCKED`. A waiver needs a DECISIONS.md entry naming the
  risk.
- **G2 MUST** loop back to the earliest invalidated phase when later evidence invalidates an earlier artifact (for
  example, build finds a design flaw → Design). Do not patch around it in Build.
- **G3 SHOULD** batch human checkpoints into a single message listing decisions, defaults taken, and what continues
  meanwhile. Work on unblocked tasks continues while waiting.

### 4.3 Autonomy vs human checkpoints

- **H1 MUST** stop and ask a human (or, if unattended, park the task as `BLOCKED-HUMAN` and continue other work) only
  when an action is **irreversible or externally visible**: production deploy, destructive data migration, force-push or
  push to protected/default branches, publishing (store, blog, DNS), spending money or quota beyond the budget, sending
  messages to real people, changing CI/workflow files or secrets, or touching paths the project marks sensitive.
- **H2 MUST** encode H1 boundaries as settings, not prose: `permissions.deny` for never-actions, `permissions.ask` for
  checkpoints, and a PreToolUse hook when command variants escape pattern rules
  (https://code.claude.com/docs/en/auto-mode-config). Boundaries stated only in conversation can be lost in compaction.
- **H3 SHOULD** ask at intake only if a *blocking* ambiguity changes the shape of the whole mission (for example, "native
  Swift or React Native?" when the user didn't say). Otherwise take the default and log it.
- **H4 MUST** surface to the human, at the next checkpoint or in the final report: stop-rule firings, classifier blocks
  that forced a fallback, waived gates, budget overruns, and assumptions whose confidence is `low`.

### 4.4 Goal loops and stop-condition rules (paste-ready)

A **loop** is any repeated *make → verify → feedback* cycle: a task iteration, a gate review, a design tournament, a
bug-hunt hypothesis cycle. Every loop MUST declare, before its first iteration, the fields in the loop template (§7.3).

**Stop-condition rules** (evaluated after each verifier verdict, in this order):

1. **S1 Success.** STOP-SUCCESS when every declared acceptance check for the loop has verdict PASS from a verifier that
   did not produce the artifact, *with evidence attached* (command output, screenshot path, file:line). Narrated claims
   without evidence count as FAIL.
2. **S2 Impossible.** STOP-IMPOSSIBLE when the verifier returns `IMPOSSIBLE` with a reason (missing capability, a
   contradiction in the spec, an external dependency down). Escalate to the orchestrator, who either amends the spec
   (DECISIONS.md) or marks the task BLOCKED.
3. **S3 Hard budget.** STOP-BUDGET when any cap is hit: `max_iterations` (default S=3, M=5, L=8; never >20), token/cost cap,
   wall-clock cap. Caps MUST be counted in STATUS.md by the orchestrator or a script, not judged from narration.
4. **S4 Futility.** STOP-STALLED when (a) the count of passing checks has not increased for `stall_window` iterations
   (default 2), or (b) the *same* failure signature (same check id + same error class) recurs 2 times after a fix
   attempt, or (c) the artifact oscillates (a check flips PASS→FAIL→PASS). Keep the best-scoring iteration, not the last.
5. **S5 Guardrail.** STOP-GUARDRAIL immediately on an attempted forbidden action, a tampered acceptance check (a test
   deleted or weakened, assertions loosened, a check marked skipped), or a classifier refusal the fallback could not
   resolve.
6. **S6 Escalation ladder.** On STALLED: iteration 1 → retry the same model with the verifier's diff-style feedback.
   Stall 1 → change approach (new hypothesis / smaller slice) and log it. Stall 2 → escalate the model one tier (Sonnet
   4.6 → Opus 4.8; Opus 4.8 → Fable 5.1 only for reasoning-heavy work). Stall 3 → mark BLOCKED with a failure note for the
   memory lane and continue other DAG branches.
7. **S7 Never** "fix" a loop by editing the acceptance check. Changing a check requires a DECISIONS.md entry *and* a
   different agent than the one failing it.

**Platform mapping.** Where `/goal` is available, the orchestrator MAY set a session goal that points at file evidence,
e.g. `/goal mission/STATUS.md shows every M2 task PASSED by verifier with evidence links, and ./mission/check.sh M2 has
printed exit 0 in this session, or stop after 25 turns`. It MUST NOT treat a `/goal` "met" as a gate pass without the
verifier record. On CMA, a gate MAY be run as an Outcome: the rubric file = the loop's rubric, max_iterations = the S3
cap. Elsewhere, emulate with a verifier sub-agent plus the STATUS.md counters. A script Stop hook running
`mission/check.sh` is the preferred deterministic engine where hooks exist.

### 4.5 Work breakdown and delegation

- **W1 MUST** decompose milestones into tasks that each (a) produce one verifiable change, (b) cite ≥1 acceptance check
  id, (c) list owned files/directories (no two concurrent tasks own the same path unless isolated by worktree), (d) fit
  in one fresh context. Heuristic: ≤ ~15 files touched and ≤ ~1 day of human work.
- **W2 MUST** record dependencies as an explicit DAG in PLAN.md (`needs: [T-ids]`). Dispatch waves = sets of ready
  tasks with disjoint owned paths.
- **W3 MUST** fan out by size: S ≤ 2 concurrent workers; M ≤ 4; L ≤ 8; XL ≤ 12 per wave, or a dynamic workflow when
  more are needed. Research fan-out follows the multi-agent research scaling rule (simple lookup = 1 agent).
- **W4 MUST** use the sub-agent brief template (§7.2) verbatim for every delegated task and require the structured
  return format. A return without evidence is treated as FAIL.
- **W5 MUST** integrate serially: merge one task at a time (or one wave onto an integration branch), run the affected
  checks after each merge, and roll back the task rather than patching blindly when integration breaks.
- **W6 SHOULD** use worktree isolation (`isolation: worktree` or `git worktree`) for parallel writers and let verifiers
  read the integrated branch.

### 4.6 Long-running execution, context and resume

- **L1 MUST** start every session (including resumed, headless and Routine runs) with the ritual: read HANDOFF.md →
  STATUS.md → PLAN.md (ready tasks) → STATE.md "Last session"; `git log --oneline -20`; run the smoke check. If the
  smoke check is red, fix that before new work.
- **L2 MUST** end every session (or when context use passes ~60%) by writing HANDOFF.md (§7.5): what changed, gate
  states, in-flight tasks, next 3 actions, open risks, exact commands to verify.
- **L3 SHOULD** prefer a context *reset* over repeated compaction for L/XL missions. Delegate heavy reading to
  sub-agents that return ≤ ~1–2 pages. The orchestrator never ingests raw logs; it reads summaries plus file pointers.
- **L4 MUST** keep hard caps outside the model: STATUS.md budget counters, `--output-format json` cost capture in
  headless runs (https://code.claude.com/docs/en/headless), and a turn/time clause in any `/goal`.
- **L5 MAY** schedule recurring or laptop-off continuation with Routines (self-contained prompt, `claude/` branches,
  scoped connectors) or `claude -p` in CI. Headless runs MUST NOT use `--bare` unless skills/agents are passed
  explicitly.

### 4.7 Safety boundary

- **B1 MUST** pin models by full ID in agent definitions and Agent-tool calls (Fable 5.1 = `claude-fable-5-1`, per
  https://www.anthropic.com/claude/fable; Opus 4.8 / Sonnet 4.6 IDs per the provider's model list). Intake MUST check the
  resolved model, because `opus`/`sonnet` aliases resolve to Opus 5 / Sonnet 5 on the Anthropic API
  (https://code.claude.com/docs/en/model-config).
- **B2 MUST** route tasks predicted to trip classifiers (exploit development, pentest logic, malware analysis, some bio,
  training-competitor-model work) to Opus 4.8 from the start, or to a human. Defensive review of the project's own code
  MAY stay on the planned model.
- **B3 MUST** record every fallback in STATUS.md → "Model/fallback events" (time, task, category if known, from→to
  model, effort). After a fallback the orchestrator MUST re-select its intended model at the next phase boundary,
  because the switch is sticky (https://github.com/anthropics/claude-code/issues/74311).
- **B4 MUST** treat an unresolved refusal as `BLOCKED-SAFETY` (a visible state), never as a retryable generic error. It
  MUST NOT try to rephrase around the classifier.

## 5. Model & effort assignment

Principles. (1) Pay for judgment where errors compound (plan, integration, adjudication) and for skepticism where
errors hide (verification, review). (2) Default cheap for volume. (3) Every downgrade has a named guard that would catch
the quality loss. (4) The verifier is never weaker than necessary to catch the maker's *likely* failure: a Sonnet 4.6
maker gets a verifier that runs commands (cheap and deterministic) plus, for M+ gates, an Opus 4.8 reviewer. Fable 5.1
at Low/Medium effort "achieves results similar to or better than Fable 5's at a much lower cost", and Fable 5.1
defaults to High in Claude Code (https://www.anthropic.com/claude-fable-and-mythos-5-1). So the skill MUST set effort
explicitly instead of inheriting High everywhere.

| Role | Size S | Size M | Size L/XL | Why / cost reasoning | Guard that protects the downgrade |
|---|---|---|---|---|---|
| Orchestrator (plan, dispatch, integrate, adjudicate) | Sonnet 4.6 high (or the session model) | Fable 5.1 medium | Fable 5.1 medium; high only for Spec/Design gates and stall adjudication | The orchestrator's tokens are mostly reading summaries and writing control files; Fable's value is long-horizon coherence and delegation. S missions don't need it. | Plan lint (DAG, check coverage) by a Sonnet 4.6 verifier; if an S mission gets reclassified to M at any gate, switch the orchestrator to Fable. |
| Intake / BRIEF expansion | orchestrator | orchestrator | orchestrator (Fable 5.1 high, one-off) | Framing errors are the most expensive, and this is a one-off cost. | Spec gate adversarial review (Opus 4.8). |
| Researcher (web/docs/codebase) | Sonnet 4.6 medium | Sonnet 4.6 medium | Sonnet 4.6 medium fan-out; Opus 4.8 medium for synthesis of conflicting sources | High volume, cheap reading. | Citation spot-check: a verifier re-opens 20% of cited URLs/paths (min 2); any mismatch → the whole report is re-verified. |
| Spec reviewer (adversarial) | skip / orchestrator | Opus 4.8 medium | Opus 4.8 high | Finding missing/untestable criteria needs strong reasoning, but on bounded input. | Human sign-off on acceptance.json for L/XL. |
| Architect / Design author | orchestrator | Opus 4.8 high | Opus 4.8 high (Fable 5.1 high only for cross-system architecture with many unknowns) | Hard but bounded; Opus 4.8 is the post's stated niche, and it's cheaper than Fable. | Design review by a *different* Opus 4.8 instance with the brief "find the three most likely ways this design fails the acceptance checks". |
| Planner (milestones → task DAG) | orchestrator | orchestrator | orchestrator | Plan quality = orchestrator responsibility. | Structural lint (Sonnet 4.6 low): every task has check ids, owned paths, needs; no cycles; no uncovered checks. |
| Builder: routine (scaffold, CRUD, docs, lint, simple refactor, test scaffolding) | Sonnet 4.6 medium | Sonnet 4.6 medium | Sonnet 4.6 medium | Bulk of fan-out; the cheapest competent coder. | Per-task verifier runs the checks. S4/S6 escalation to Opus 4.8 after stall 2. |
| Builder: hard (concurrency, migrations, perf, gnarly debugging) | Opus 4.8 medium | Opus 4.8 high | Opus 4.8 high | Failure loops on Sonnet cost more than one Opus pass. | Same verifier; the orchestrator records the rationale in the plan. |
| Per-task verifier (runs checks, inspects diff vs brief) | Sonnet 4.6 low | Sonnet 4.6 medium | Sonnet 4.6 medium | Mostly executing commands and comparing to a rubric; the replacement for Haiku graders. | Gate verifier re-runs a random 20% of task verifications; any disagreement → the per-task verifier for that milestone is escalated to Opus 4.8 medium. |
| Gate / mission verifier (Verify phase) | Sonnet 4.6 high | Opus 4.8 medium | Opus 4.8 high | Last line before review; must be skeptical and thorough. | Evidence required per check; the orchestrator refuses PASS without artifacts. |
| Adversarial reviewer (quality) | Sonnet 4.6 high (1 pass) | Opus 4.8 high | Opus 4.8 high, ≤3 rounds + consolidated final | Reviews are where subtle defects surface; the user's history shows value *and* fatigue. | Round cap + disposition log; a finding repeated across rounds signals a process gap for retro. |
| Security reviewer | Opus 4.8 medium | Opus 4.8 high | Opus 4.8 high | Avoids Fable classifier stalls on security content (Opus 4.8 completed Fable's cyber-blocked tasks per https://www.anthropic.com/claude-fable-and-mythos-5-1). | Human review for auth/payments/crypto paths. |
| UI/visual verifier | Sonnet 4.6 medium | Sonnet 4.6 high | Opus 4.8 medium for design-quality judgment; Sonnet 4.6 high for layout checks | Vision checks are frequent; taste judgments are fewer and harder. | Rubric with concrete criteria + screenshot evidence; human for brand-critical surfaces (see the frontend lane). |
| `/goal` evaluator (if used) | Sonnet 4.6 (repoint small fast model) | same | same | The user forbids Haiku; the condition only reads the transcript anyway. | Never the sole gate (S1). |
| Handoff / STATUS writer | orchestrator | orchestrator | orchestrator | Must reflect the orchestrator's understanding. | L1 smoke check at the next session catches stale handoffs. |
| Retro / lesson distiller | Sonnet 4.6 low | Sonnet 4.6 medium | Opus 4.8 medium | Generalizing lessons benefits from reasoning at L/XL; the memory lane owns the format. | Lessons must cite the failure evidence; the next retro checks whether the lesson was consulted. |
| Classifier fallback target | Opus 4.8 (same effort +1 step) | same | same | Verified fallback target; raising effort compensates for the tier drop (the community rationale in https://github.com/anthropics/claude-code/issues/74311). | B3 logging; the orchestrator re-selects Fable at the next boundary. |

Cost notes:

- Measure, don't guess: headless runs capture `total_cost_usd` per invocation (https://code.claude.com/docs/en/headless);
  `/usage`, `/goal` status and `/workflows` show spend in-session (secondary:
  https://cldnavi.com/en/blog/claude-code-loops-guide-2026/). STATUS.md keeps a per-milestone budget line.
- Multi-agent is ~15× chat tokens (https://www.anthropic.com/engineering/multi-agent-research-system). Fan-out ceilings
  (W3) and the "simple lookup = 1 agent" rule are the main cost controls. The second is cache friendliness: stable
  brief preambles and a shared `mission/CONTEXT.md` that briefs *point to* instead of pasting.
- **Downgrade experiment rule.** When the orchestrator wants to move a role one tier down (e.g. gate verifier Opus 4.8 →
  Sonnet 4.6), it MUST run both on the next 3 gates and compare verdicts. Downgrade only if they agree on 3/3 and the
  cheaper one found every FAIL the stronger one found. Record it in DECISIONS.md.

## 6. Project-shape conditionals

### 6.1 Size classification (decided at Intake, revisable at any gate)

| Size | Signals | Phases | Fan-out ceiling | Review rounds | Human checkpoints | Default iteration cap |
|---|---|---|---|---|---|---|
| **S** | ≤1 day human work; ≤~10 files; one component; no schema/API change | Intake → (Research if unknown) → Plan-in-brief → Build → Verify → Review (1 pass) → Retro | 2 | 1 | Only H1 actions | 3 |
| **M** | 1–5 days; one or two components; limited contract changes | All phases; Design short; Spec + acceptance.json | 4 | ≤2 | H1 + notify at Spec | 5 |
| **L** | 1–4 weeks; multiple components or platforms; new data model | All phases, milestones ≥3, handoff per session | 8 | ≤3 + consolidated final | Spec sign-off, irreversible design, release | 8 |
| **XL** | Multi-month / greenfield product; multiple platforms; external launch | All phases per milestone (each milestone is an L-mission with its own gates); Routines/headless continuation | 12 (or a dynamic workflow) | per milestone ≤2 + one cross-milestone review before release | Spec sign-off, per-milestone summary, release | 8 per task, 20 hard max |

**IF** the classification is uncertain between two sizes **THEN** choose the larger for *verification* (gates, checks)
and the smaller for *ceremony* (document length, fan-out), and log it as an assumption.

### 6.2 Shape rules

**Greenfield multi-platform app** (e.g. Swift iOS + Cloudflare backend):
- IF there are ≥2 platforms THEN Design MUST define the contract first (API schema / shared types) as its own milestone M0,
  with contract tests, and build platforms in parallel only after M0 PASSED.
- IF the task includes a UI THEN acceptance.json MUST contain user-journey checks (executable e2e plus rubric-graded
  visual checks) from Spec. The UI verifier is a separate role (frontend lane owns the method).
- IF there's a mobile app THEN plan a "walking skeleton" milestone (login → one core flow → backend round-trip, deployed
  to a dev environment) before feature fan-out.
- IF the app has infra THEN Release MUST include environment bootstrap scripts (`init.sh`-style) that the smoke check
  runs every session.

**Deep bug hunt** ("find this annoying bug and fix it"):
- Phases collapse to Intake → Reproduce → Investigate (hypothesis loop) → Fix → Verify → Review → Retro. Spec = the
  reproduction as a failing test.
- The gate "Reproduced" MUST pass before any fix attempt: a deterministic repro or a statistical repro (e.g. fails ≥1 in N
  runs with N recorded).
- The investigation loop uses S4 futility with `stall_window` = 3 hypotheses. Each hypothesis is a sub-agent brief with
  "evidence that would confirm/refute". Hypotheses MAY run in parallel on worktrees.
- IF the bug involves concurrency, memory or a vendor library THEN the investigator is Opus 4.8 high (or Fable 5.1 high
  after stall 2). The launch evidence of Fable 5.1 root-causing a one-in-a-million crash
  (https://www.anthropic.com/claude-fable-and-mythos-5-1) justifies escalating there, not starting there.
- DoD MUST include "repro test fails before fix, passes after, and the full suite is green", plus a regression note for
  retro.

**Feature in an existing product** (e.g. new dashboard):
- Research MUST include a codebase map sub-agent (Explore-style, read-only) producing conventions, reusable components
  and the test harness location. Design MUST reuse existing patterns unless a DECISIONS.md entry says otherwise.
- IF it touches shared components or data models THEN the regression suite for affected modules becomes part of the
  acceptance checks (not the whole world: only suites mapped to touched paths).
- IF the product has feature flags THEN release behind a flag and add a flag-off check.
- Human checkpoint: none beyond H1 for M. Screenshot summary at Review for UI features.

**Service migration / extraction** (e.g. AI gateway → core platform service):
- Spec MUST produce a **behavioural parity inventory**: every endpoint/contract/side effect of the old service as an
  acceptance check (golden/contract tests captured *before* the move). This is the "feature list all failing" pattern
  applied to parity.
- Plan MUST be strangler-style milestones: (1) characterize the old behaviour, (2) new service passes parity in shadow,
  (3) dual-run/compare, (4) cut over behind a switch, (5) retire. Each cutover step is an H1 checkpoint.
- IF data moves THEN a rollback rehearsal is a gate, and destructive steps are `permissions.ask`.
- Stop rule addition: STOP-GUARDRAIL if the parity check count ever decreases.

**Research + marketing website with blog/docs:**
- Research is a first-class milestone with fan-out (market, competitors, positioning) and a synthesis gate. Claims
  that will be published MUST carry sources, checked by a citation verifier (the Outcomes cookbook pattern of a grader
  fetching every URL: https://platform.claude.com/cookbook/managed-agents-cma-verify-with-outcome-grader).
- Content acceptance = rubric-graded (voice, accuracy, structure) + executable (links 200, build passes, Lighthouse/a11y
  thresholds, docs nav complete).
- Human checkpoints: positioning/messaging sign-off (L), and publish (H1). Taste-heavy choices (hero concept, naming) MAY
  use a tournament of 3 variants judged by a rubric verifier, then a human picks.

**Other shapes that matter:**
- **Dependency / framework upgrade:** acceptance = the existing suite green + a deprecation-warning count of 0. Fan-out by
  module with `/batch`-style worktrees (https://code.claude.com/docs/en/agents). S4 same-failure rule is critical.
- **Incident / production triage:** time-boxed. Intake → mitigate (H1-gated) → root cause → fix → post-mortem. The
  orchestrator MUST NOT deploy without a human unless a runbook explicitly allows it.
- **Recurring operations** (nightly eval, CI triage, docs drift): a Routine or scheduled `claude -p`. Each run is an S
  mission with its own STATUS entry and a digest. The stop condition is in the prompt, and the connectors are scoped
  (https://code.claude.com/docs/en/routines).
- **Security-sensitive work** (authz, crypto, payments): add a security review gate with Opus 4.8 high, route
  exploit-style testing to Opus 4.8 or a human (B2), and require a human checkpoint before merge.

## 7. Artifacts & templates

All templates are meant to ship verbatim under `templates/`. Placeholders are in `<angle brackets>`. The phase gate
table (§4.2), stop-condition rules (§4.4) and size table (§6.1) are also paste-ready.

### 7.1 `mission/STATUS.md` (task board and loop state; the orchestrator is the only writer)

```markdown
# STATUS · <mission name>
Updated: <UTC timestamp> · Session: <n> · Orchestrator model: <id @ effort> · Harness: <claude-code|cma|other>
Shape: <greenfield|bug-hunt|feature|migration|website|upgrade|incident|recurring> · Size: <S|M|L|XL>
Current phase: <0..9 name> · Stop state: <RUNNING|STOP-SUCCESS|STOP-IMPOSSIBLE|STOP-BUDGET|STOP-STALLED|STOP-GUARDRAIL|BLOCKED-HUMAN|BLOCKED-SAFETY>

## Gates
| Phase | State | Evidence | Verifier | Date |
|---|---|---|---|---|
| 0 Intake | PASSED | BRIEF.md | orchestrator checklist | <date> |
| 2 Spec | PENDING | acceptance.json (0/<n> passing) | — | — |

## Board
| Task | Milestone | Title | Owner role · model@effort | Needs | Owned paths | Checks | State | Iter | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| T-012 | M2 | Add /outfits POST endpoint | builder · sonnet-4.6@medium | T-010 | apps/api/src/outfits/** | AC-021, AC-022 | VERIFYING | 2/5 | logs/T-012-iter2.txt |

States: TODO → READY → IN-PROGRESS → VERIFYING → PASSED | FAILED(iter) | STALLED | BLOCKED(<reason>) | CANCELLED(DEC-id)

## Budget
| Scope | Cap | Used | Source of truth |
|---|---|---|---|
| Mission | <$ or tokens> | <n> | headless total_cost_usd / usage view |
| M2 | <cap> | <n> | |

## Model / fallback events
| Time | Task | Event | From → To | Category | Action taken |
|---|---|---|---|---|---|

## Human queue (batched)
- [ ] <decision needed> · default taken: <x> · blocks: <T-ids> · since <date>

## Stop-rule log
- <date> T-019 STOP-STALLED (same failure signature AC-031 TypeError ×2) → escalated to opus-4.8@high (DEC-014)
```

### 7.2 Sub-agent task brief template (paste into every Agent/Task call)

```markdown
# Task brief · <T-id> · <one-line title>

## Role & model
You are the <builder|researcher|verifier|reviewer|investigator> for task <T-id> of mission <name>.
Model: <full model id> · effort: <low|medium|high>. You work in a fresh context; everything you need is below or linked.

## Objective (outcome, not steps)
<What must be true when you are done, in 1–3 sentences.>

## Why it matters
<1–2 sentences linking to the milestone goal, so you can make sensible local trade-offs.>

## Context to read first (read these, not the whole repo)
- mission/CONTEXT.md (conventions, commands)
- <path or URL> — <why>
- Relevant decisions: <DEC-ids>. Relevant assumptions: <A-ids>.

## Ownership & boundaries
- You MAY edit: <globs>. You MUST NOT edit anything else. If another path needs changes, stop and report it.
- Work in: <worktree path / branch claude/<T-id>-slug>.
- Forbidden: deleting or weakening tests/checks; editing acceptance.json; touching CI/workflows/secrets; pushing to
  default branch; network writes; <project-specific>.

## Acceptance checks you must satisfy
| Check id | Type | How to prove |
|---|---|---|
| AC-021 | executable | `<command>` exits 0; paste the last 30 lines of output |
| AC-022 | rubric | <criterion text>; attach <screenshot/file:line> |

## Steps (for Sonnet-class workers; omit for Fable/Opus outcome briefs)
1. <step>
2. Run the checks above; fix until green or until you hit the budget.

## Budget & stop rules
Max <n> fix iterations · stop after <m> tool calls without progress · if the same error repeats twice, stop and report
STALLED with your best hypothesis. If a request is refused for safety reasons, stop and report BLOCKED-SAFETY. Do not
rephrase around it.

## Return format (exactly this, ≤ 400 words plus evidence paths)
STATUS: DONE | STALLED | BLOCKED(<reason>) | BLOCKED-SAFETY
SUMMARY: <what changed, 3–6 bullets>
FILES CHANGED: <paths>
CHECKS: <check id> = PASS|FAIL · evidence: <path to saved output / screenshot / file:line>
ASSUMPTIONS MADE: <A-new: text> (or none)
OUT-OF-SCOPE FINDINGS: <issues noticed but not fixed, with file:line>
NEXT: <what the orchestrator should do next, if anything>
```

Brief-writing rules for the orchestrator: (1) never paste large files into the brief; point to them. (2) Every brief
names check ids that already exist in acceptance.json. (3) Verifier briefs get the *artifact, the checks and the
rubric only*: no maker summary, no maker reasoning. (4) Two briefs dispatched in the same wave MUST NOT share owned
paths.

### 7.3 Loop spec + rubric template (`mission/loops/<loop-id>.md`)

```markdown
# Loop · <loop-id> · <what is being iterated>
Kind: <task-build | gate-review | design-tournament | hypothesis-hunt | content-draft>
Maker: <role · model@effort> · Verifier: <role · model@effort> (fresh context; never the maker)
Artifact under test: <paths / URL / screenshot set>
Engine: <plain sub-agents | /goal (condition below) | CMA Outcome | Stop hook check.sh | dynamic workflow>

## Success (S1): all must PASS with evidence
| Criterion id | Criterion (explicit, gradeable) | Method | Evidence required | Weight |
|---|---|---|---|---|
| AC-021 | `pnpm test apps/api/outfits` exits 0 | executable | saved output path | must |
| R-03 | Empty state shows a primary action and no placeholder text | rubric + screenshot | screenshot path + note | must |
| R-07 | Visual hierarchy: exactly one H1; CTA above the fold at 390×844 | rubric + screenshot | screenshot | should (score 0–3, ≥2) |

## Ignore (verifier must not fail on these)
- <style nits covered by the formatter> · <copy wording, owned by content loop>

## Caps (S3)
max_iterations: <S=3|M=5|L=8, ≤20> · token/cost cap: <n> · wall-clock cap: <n> · stall_window: 2

## Futility signals (S4)
- passing-criteria count not increased for stall_window iterations
- same failure signature twice after a fix attempt
- oscillation of any criterion

## Escalation (S6)
iter-fail → same maker + verifier feedback · stall 1 → change approach · stall 2 → maker tier +1 · stall 3 → BLOCKED

## Iteration log (orchestrator appends)
| Iter | Passing | Failing ids | Verdict | Best-so-far? | Cost |
|---|---|---|---|---|---|
```

**Verifier prompt skeleton** (paired with the loop spec):

```markdown
You are an independent verifier. You did not write this artifact and you have not seen its author's reasoning.
Be skeptical: your job is to find where it fails the criteria, not to be encouraging.
Inputs: loop spec <path> (criteria + ignore list), artifact <paths>, environment commands in mission/CONTEXT.md.
For each criterion: run or inspect it yourself. Do not trust claims in commit messages, comments or summaries.
Verdict per criterion: PASS | FAIL | CANNOT-VERIFY (say why, e.g. tool unavailable). CANNOT-VERIFY is not PASS.
Return exactly:
VERDICT: MET | NOT-MET | IMPOSSIBLE(<reason the criteria can never be satisfied as written>)
CRITERIA: <id> = PASS|FAIL|CANNOT-VERIFY · evidence: <path/output excerpt> · gap: <concrete, diff-style description of what must change>
TAMPERING: <any sign checks/tests were weakened, skipped or deleted> (or none)
TOP FIX: <the single most valuable change for the next iteration>
```

The rubric rules come from the Outcomes guidance: explicit, independently scored criteria; bootstrap from a known-good
artifact (https://platform.claude.com/docs/en/managed-agents/define-outcomes). The "cannot-verify is not pass" rule
mirrors `/deep-research` listing unverifiable claims as unverified rather than refuted
(https://code.claude.com/docs/en/workflows).

### 7.4 `mission/acceptance.json`, PLAN task entry, ASSUMPTIONS and DECISIONS

```json
{
  "mission": "<name>",
  "checks": [
    {
      "id": "AC-021",
      "requirement": "REQ-007",
      "description": "Creating an outfit returns 201 and persists it",
      "type": "executable",
      "command": "pnpm vitest run apps/api/src/outfits/create.test.ts",
      "milestone": "M2",
      "passes": false,
      "verified_by": null,
      "evidence": null
    },
    {
      "id": "R-03",
      "requirement": "REQ-012",
      "description": "Empty wardrobe state shows a primary 'Add item' action and no placeholder text",
      "type": "rubric",
      "method": "screenshot at 390x844 reviewed by UI verifier",
      "milestone": "M3",
      "passes": false,
      "verified_by": null,
      "evidence": null
    }
  ]
}
```

Rules: only a verifier flips `passes` and fills `verified_by` + `evidence`. Adding checks is allowed at any time.
Removing or editing a check needs a DECISIONS entry (S7). JSON is chosen deliberately because models overwrite it less
readily than Markdown (https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

PLAN.md task entry:

```markdown
### T-012 · Add /outfits POST endpoint
milestone: M2 · needs: [T-010] · role: builder · model: <sonnet-4.6 full id>@medium · size: S
owned: apps/api/src/outfits/** · checks: [AC-021, AC-022] · risk: low · parallel-safe: yes (worktree)
notes: reuse validation middleware from apps/api/src/common/validate.ts
```

ASSUMPTIONS.md row: `| A-004 | Users sign in with Apple only for v1 | brief silent; iOS-first | medium | invalidated if
Android is named in scope | Spec | open |`

DECISIONS.md entry:

```markdown
## DEC-014 · 2026-09-12 · Escalate T-019 maker to Opus 4.8 high
Context: STOP-STALLED, AC-031 same TypeError twice (logs/T-019-iter3.txt)
Options: (a) retry Sonnet with narrower slice (b) escalate to Opus 4.8 (c) mark BLOCKED
Decision: (b) · Rationale: concurrency bug; two identical failures · Reversible: yes · Cost impact: ~+1 Opus task
```

### 7.5 `mission/HANDOFF.md` (written at session end or at ~60% context; overwritten each time, history in git)

```markdown
# HANDOFF · <mission> · session <n> → <n+1> · <UTC timestamp>
Orientation: repo <path> · branch <name> @ <commit> · integration branch <name> · environments <dev URLs>
Read next, in order: STATUS.md (gates + board) → PLAN.md ready tasks → STATE.md "Last session"

## What changed this session
- <T-ids PASSED with evidence paths> · <gates advanced>

## In flight (do not restart blindly)
- T-019 STALLED iter 3/8, hypothesis: <x>, worktree <path>, last output <path>

## Verified facts this session (with how)
- <fact> · verified by <command/output path>

## Not available to the next agent
- <credentials, devices, human-only steps, rate-limited services>

## Next 3 actions
1. <action> · expected evidence: <x>
2. …

## Risks / open questions
- <risk> · default assumption A-<id>

## Verification bar (run before claiming anything)
<single command line, e.g. pnpm verify && pnpm test && cargo test --workspace>
```

This shape follows the user's own handoff style: orientation, what works (verified), what's unavailable, priority-ordered
fixes, and one verification bar (arcwell/docs/handoff/2026-08-21-morning-remediation-handoff.md:9-41).

### 7.6 Guardrail settings for autonomous runs (project or `--settings`; adjust per project)

```json
{
  "permissions": {
    "deny": [
      "Bash(git push --force *)",
      "Bash(git push -f *)",
      "Bash(rm -rf /*)",
      "Bash(terraform apply *)",
      "Edit(.github/workflows/**)"
    ],
    "ask": [
      "Bash(git push *)",
      "Bash(gh pr merge *)",
      "Bash(wrangler deploy *)",
      "Bash(npx wrangler deploy *)"
    ]
  }
}
```

The ask/deny semantics and the "ask rules don't catch `git -C <dir> push`" caveat are verified
(https://code.claude.com/docs/en/auto-mode-config). The specific deny entries are this lane's recommendations. The
exact rule-pattern grammar for `Edit(...)` paths should be checked against the permissions docs by the synthesizer
(inference, not verified here). For an unattended run, the orchestrator converts `ask` items into `BLOCKED-HUMAN` tasks
rather than waiting on a prompt.

### 7.7 Deterministic gate script and Stop hook

`mission/check.sh <milestone>` runs every executable check for the milestone listed in acceptance.json, writes outputs
to `mission/logs/`, and exits non-zero on any failure. It MUST NOT flip `passes`; the verifier does that after reading the
logs. A script-based Stop hook can run it after each turn ("can run a script for deterministic checks",
https://code.claude.com/docs/en/goal). The hook JSON shape and the exit-code semantics for blocking a stop are in the
hooks docs, which this lane did not re-fetch. The synthesizer should copy the current schema from
https://code.claude.com/docs/en/hooks rather than from memory.

### 7.8 Headless / Routine continuation prompt skeleton

```text
You are continuing mission <name> using the <skill-name> skill. This prompt is self-contained.
1. Follow the session-start ritual (L1): read mission/HANDOFF.md, mission/STATUS.md, mission/PLAN.md, STATE.md "Last session"; run mission/check.sh smoke.
2. Work only on READY tasks of the current milestone, at most <k> tasks this run, using the brief template.
3. Obey stop rules S1–S7 and caps: this run's budget <$ or turns>; stop after <n> turns.
4. Never perform H1 actions; queue them in STATUS.md "Human queue".
5. Before exiting: update STATUS.md, write HANDOFF.md, commit to branch claude/<mission>-run-<date>, and print a 10-line digest
   (tasks passed, gates, stop state, cost, blockers).
Success for this run = digest printed AND STATUS.md + HANDOFF.md committed.
```

Invocation example (headless, measured, no `--bare` so the skill and agents load; verified flags
https://code.claude.com/docs/en/headless):
`claude -p "$(cat mission/continue-prompt.txt)" --model <fable-5.1 id> --output-format json > mission/logs/run-<ts>.json`.
With `/goal` available, the last line of the prompt MAY instead be
`/goal STATUS.md and HANDOFF.md were committed this run and the digest was printed, or stop after 40 turns`
(https://code.claude.com/docs/en/goal).

### 7.9 Orchestrator main loop (the SKILL.md core, ≤ 25 lines)

```text
INTAKE: classify shape+size → BRIEF.md → verify model pins → STATUS.md header → guardrail settings present?
FOR phase in applicable phases(size, shape):
  read STATUS/PLAN · pick ready work · write STATUS (dispatch wave)
  dispatch briefs (≤ fan-out ceiling, disjoint owned paths, pinned models)
  integrate returns serially · run check.sh · dispatch verifier(s) with artifact+checks only
  apply stop rules S1–S7 per loop · log fallbacks/decisions/assumptions
  gate: evidence + verifier → PASSED | loop back (G2) | waiver (DEC) | BLOCKED-HUMAN (batch human queue)
  context > ~60% or session end → HANDOFF.md, reset
RETRO: failures → lessons (memory lane) · cost + iteration stats → STATUS closed · final report with H4 items
```

## 8. Anti-patterns & failure modes

**Control-loop anti-patterns**

1. **Transcript as state.** Progress lives only in chat or in a `/goal` string. After compaction, a crash or a resume,
   the agent guesses. Fix: O1/O2; STATUS.md written before and after every wave.
2. **Self-grading.** The builder reports "all tests pass" and the orchestrator believes it. Agents "reliably skew
   positive when grading their own work" (https://www.anthropic.com/engineering/harness-design-long-running-apps).
   Fix: S1 evidence rule; verifier briefs exclude maker reasoning.
3. **`/goal` as the verifier.** The evaluator reads narration, not reality (https://code.claude.com/docs/en/goal), and
   defaults to Haiku, against the user's constraint. Fix: conditions reference printed command output; a real verifier
   gates.
4. **Premature "done".** A later session sees lots of code and declares victory
   (https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents). Fix: the all-failing
   acceptance.json starts at Spec; only verifiers flip entries.
5. **Check tampering.** Tests deleted, assertions loosened, checks marked skipped to go green. Fix: S5 guardrail, S7,
   and a verifier TAMPERING field. Diffs touching test files get extra scrutiny.
6. **Unbounded loops.** No iteration/cost cap, or caps judged by the model from narration. Fix: S3 counters in files;
   turn clause in `/goal`; CMA max_iterations.
7. **Plateau grinding.** Iterating long after gains stopped; shipping the *last* rather than the *best* iteration
   (the harness post observed plateaus and preferred middle iterations). Fix: S4 + best-so-far tracking.
8. **Gate theatre.** Ten phases with long documents for a one-line fix. Fix: size table §6.1; S missions collapse
   phases but keep verify + retro.
9. **Asking instead of assuming.** Stopping for questions the orchestrator could default. Fix: O6 assumptions log; H1
   limits human stops to irreversible actions.
10. **Silent guardrails.** Boundaries stated in chat ("don't push") that compaction drops
    (https://code.claude.com/docs/en/auto-mode-config). Fix: H2 settings.

**Delegation anti-patterns**

11. **Vague briefs** ("research the semiconductor shortage") → duplicated work and gaps
    (https://www.anthropic.com/engineering/multi-agent-research-system). Fix: §7.2 template, check ids, owned paths.
12. **Swarm by default.** 50 sub-agents for a simple query; fan-out on coding work that isn't parallelizable. Fix: W3
    ceilings; "simple lookup = 1 agent"; pilot a slice before a big workflow run.
13. **Overlapping ownership.** Parallel writers on the same files, especially in agent teams, which don't isolate
    worktrees (https://code.claude.com/docs/en/agents). Fix: W1(c), W6.
14. **Big-bang integration.** Merging a whole wave then debugging the pile. Fix: W5 serial integration with rollback.
15. **Orchestrator doing the work.** The Fable orchestrator writes the code, burning top-tier tokens and polluting its
    context. Fix: O3.
16. **Raw logs into the orchestrator.** Pasting 5,000 lines of test output into the main context causes context rot
    (https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents). Fix: logs to files; sub-agents
    return ≤400-word summaries plus paths.

**Cost and token traps**

17. **Alias drift.** `model: opus` silently runs Opus 5 and `sonnet` runs Sonnet 5 (https://code.claude.com/docs/en/model-config).
    That breaks the user's model policy and changes cost. Fix: B1 pins + intake check.
18. **Inherited High effort.** Fable 5.1 defaults to High in Claude Code
    (https://www.anthropic.com/claude-fable-and-mythos-5-1). Fix: explicit effort per role (§5).
19. **Sticky fallback.** After one classifier flag the whole session keeps running on Opus 4.8 with the old effort level,
    unnoticed (https://github.com/anthropics/claude-code/issues/74311). Fix: B3.
20. **Outcome iteration multiplier.** Every CMA revision multiplies writer + grader tokens (secondary
    https://avinashsangle.com/blog/claude-managed-agents-outcomes). Fix: fix the rubric before raising max_iterations.
21. **`--bare` surprise.** A headless continuation run with `--bare` loads no skills, agents or hooks, so the mission
    runs without its process (https://code.claude.com/docs/en/headless). Fix: L5.
22. **Review fatigue loop.** Endless adversarial rounds that block progress; the user lived this (eighteen rounds,
    arcwell/docs/operations/review-process-amendment.md:3-5). Fix: round caps + a consolidated milestone review;
    findings get dispositions, not infinite reruns.
23. **Test ballooning as "verification".** Adding hundreds of shallow tests to satisfy a gate. Fix: acceptance checks map
    to requirements (one requirement → the minimum checks that would catch its failure); the verification lane owns the
    method.

**Safety-boundary failure modes**

24. Rephrasing to evade a classifier. Forbidden (B4). Surface it as BLOCKED-SAFETY.
25. Routines with every connector attached and no scoped environment. They run with no approval prompts and act under
    the user's identity (https://code.claude.com/docs/en/routines). Fix: minimal connectors, `claude/` branches, digest
    output.
26. Parsing the refusal `explanation` text for routing. It is "not stable"
    (https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback). Route on `category` / stop_reason
    only.

## 9. Open questions / risks for the synthesizer

1. **Repointing the `/goal` evaluator away from Haiku.** The docs say it uses the configured "small fast model"
   (https://code.claude.com/docs/en/goal) but this lane did not verify the exact setting or env var name on the model
   configuration page (the fetch truncated). Risk: the skill quietly uses Haiku. Recommendation: verify the setting. If
   it can't be pinned, document `/goal` as optional and rely on verifier sub-agents + a script Stop hook.
2. **Exact model IDs for Opus 4.8 and Sonnet 4.6.** Fable 5.1 is `claude-fable-5-1` (https://www.anthropic.com/claude/fable).
   The Opus 4.8 / Sonnet 4.6 full IDs were not confirmed in fetched pages. Also note that Sonnet 4.6 may be unavailable
   as the `sonnet` alias on the Anthropic API. Intake must verify availability, and the skill needs a documented
   degradation (e.g. if Sonnet 4.6 is unavailable, use Opus 4.8 low for workers and record a DECISION). Using Sonnet 5
   would violate the user's list.
3. **Should the user's model list be revisited?** Opus 5 exists and is the `opus` alias; Fable 5.1 at low effort
   competes on cost (https://www.anthropic.com/claude-fable-and-mythos-5-1). The user's constraint stands, but the
   synthesizer may want a single clearly marked override point (one table in `references/models.md`).
4. **Classifier fallback control.** There is no API-side setting to choose the fallback model/effort in Claude Code
   (feature request https://github.com/anthropics/claude-code/issues/74311). The skill can only detect and log it. How
   it detects a fallback from inside a session (model line, transcript entry `model_refusal_fallback`) was not verified.
5. **Outcomes max_iterations default/max** are from a secondary source only. Verify before quoting numbers in the skill.
6. **Hooks schema** (Stop hook JSON, blocking semantics) and **permission rule grammar** for path patterns were not
   re-fetched in this lane. Copy from current docs.
7. **Dynamic workflow availability and API** (post's `agent()/parallel()/pipeline()`) were not confirmed. The skill should
   *ask for a workflow* in natural language rather than emit a script against an assumed API
   (https://code.claude.com/docs/en/workflows).
8. **Size thresholds, fan-out ceilings, iteration caps and the 20% re-verification sampling** are this lane's judgment,
   not measured. Retro stats (§7.1 budget + stop-rule log) should tune them over time. That makes this a candidate for
   the self-improvement lane.
9. **Human checkpoint vs full autonomy.** The user wants "drive the full process end to end". Spec sign-off for L/XL is a
   deliberate interruption. The synthesizer could offer an `--autonomous` mode where sign-off becomes "notify and
   proceed after N hours", while H1 irreversible actions always stay gated.
10. **Boundary with sibling lanes.** STATE.md/lessons format (memory lane), test design and "no ballooning"
    (verification lane), UI/vision verification (frontend lane), adversarial review protocol (review lane). This report
    assumes those lanes define the content. The control loop only schedules them and enforces gates. Conflicts in file
    names (`STATUS.md` board columns, gate states) need one canonical definition.

## Sources

All URLs below were fetched or seen in search results during this lane. Entries marked SECONDARY or (search snippet) are
not primary confirmations.

- https://www.anthropic.com/claude/fable (search snippet) — "use claude-fable-5-1 via the Claude API".
- Brief: research/mission-skill/00-brief.md §3 steps 01–05, 09, 14; §5 format; §6 rules.

- https://code.claude.com/docs/en/goal — /goal verified: session-scoped completion condition; after each turn a "small fast model" (defaults to Haiku on Claude API) returns not-yet-met / met / impossible with reason; wrapper around a session-scoped prompt-based Stop hook; evaluator judges only transcript, does NOT run commands or read files; condition ≤4,000 chars; bound runs via clause "or stop after 20 turns"; one goal per session; restored on --continue/--resume (turn count reset); works with `claude -p "/goal ..."`; use auto mode for unattended; `/goal clear`.
- https://code.claude.com/docs/llms.txt — docs index lists routines, agents (subagents, agent view, agent teams, dynamic workflows), headless, github-actions, desktop scheduled tasks.
- Search result snippets (secondary, unverified): mer.vin says /goal shipped v2.1.139 (May 2026); explainx.ai says Anthropic "Getting started with loops" guide July 7 2026.

- https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback — VERIFIED: Claude Fable 5.1, Fable 5 and Opus 5 include safety classifiers; refusal = HTTP 200 with `stop_reason: "refusal"`, `stop_details.category` in {cyber, bio, frontier_llm, reasoning_extraction, general_harms}; explanation text not stable (display, don't parse); refusal can arrive mid-stream → discard partial output; pre-output refusals not billed but count against rate limits; server-side fallback beta `fallbacks: "default"` header `server-side-fallback-2026-07-01`; `recommended_model` hint; for categories with no recommended fallback the refusal stands. Post's "cyber, bio, chem, distillation" only partially matches (no "chem" category; frontier_llm ≈ distillation). Note: page names Opus 5 as also classifier-gated.

- https://platform.claude.com/docs/en/managed-agents/define-outcomes (fetched via mirror github.com/thevibeworks/claude-code-docs raw) — VERIFIED: `user.define_outcome` event; harness auto-provisions a grader in a separate context window; rubric (markdown, per-criterion) REQUIRED; grader returns explanation of which criteria passed/failed, fed back to agent; tip: explicit gradeable criteria ("CSV contains a price column with numeric values" not "data looks good"); bootstrap rubric from a known-good artifact; beta header `managed-agents-2026-04-01`.
- https://claude.com/blog/new-in-claude-managed-agents (May 19 2026) — VERIFIED: outcomes, multiagent orchestration, webhooks public beta; dreaming research preview; outcomes improved task success up to 10 points over standard prompting loop, largest on hardest problems; +8.4% docx, +10.1% pptx; multiagent orchestration = lead agent delegates to specialists with own model/prompt/tools on shared filesystem; Spiral example runs a cheap lead + Opus sub-agents + outcomes gate.
- https://avinashsangle.com/blog/claude-managed-agents-outcomes (SECONDARY) — max_iterations default 3, max 20; verdict `needs_revision` loops; grader has same model + tools as writer, fresh context; re-checks full artifact every iteration; span.outcome_evaluation_start/end events; cost trap is iteration count.
- https://platform.claude.com/cookbook/managed-agents-cma-verify-with-outcome-grader — (search snippet) writer drafts cited brief, stateless grader fetches every URL and checks quotes.

- https://code.claude.com/docs/en/routines — VERIFIED (research preview): routine = saved prompt + repos + connectors (+ environment) run on Anthropic-managed cloud (or self-hosted env); triggers Scheduled / API (HTTP POST + bearer token) / GitHub events; create at claude.ai/code/routines or CLI `/schedule`; Pro/Max/Team/Enterprise; runs autonomously with NO permission-mode picker and NO approval prompts; can use skills committed to the cloned repo; branches `claude/`-prefixed; connectors included by default can write without asking → scope them; actions appear as your identity; count against daily run allowance; prompt "must be self-contained and explicit about what to do and what success looks like"; model selector per routine. Post's "April 14, 2026" launch date not verified on this page.
- https://code.claude.com/docs/en/agents — VERIFIED: four parallel approaches: subagents (own context, return summary), agent view (`claude agents`, research preview), agent teams (shared task list + messaging, experimental, disabled by default), dynamic workflows (a script runs many subagents and cross-checks results; `/workflows`). Worktrees isolate; `/batch` splits a large change into 5–30 worktree-isolated subagents each opening a PR; forked subagent inherits full context (`/subtask`); multiplies token usage. Agent teams do NOT isolate in worktrees → partition files.

- https://code.claude.com/docs/en/workflows — VERIFIED: dynamic workflow = JavaScript script Claude writes that orchestrates many subagents; runtime executes in background; "who decides what runs next: the script"; intermediate results in script variables so Claude's context holds only final answer; dozens-hundreds of agents per run; resumable in same session; can have independent agents adversarially review each other's findings; `/workflows` progress view (pause/stop/restart agent/save as command); bundled `/deep-research` (fan-out, cross-check, vote, filters unsurvived claims, lists unverifiable claims as unverified not refuted); trigger by asking for a workflow or keyword `ultracode`, or `/effort ultracode`; on Pro enable in `/config`. Post's "agent(), parallel(), pipeline()" primitive names and "May 28 2026" date NOT confirmed on the fetched portion.
- https://code.claude.com/docs/en/sub-agents — VERIFIED: subagent own context window, custom system prompt, tool access, independent permissions; returns summary; descriptions cost context (warning >15,000 tokens combined); Explore/Plan read-only and skip CLAUDE.md; Explore inherits main model capped at Opus on Claude API (v2.1.198+); `CLAUDE_CODE_SUBAGENT_MODEL` env var; deny `Agent` tool via permissions.deny; forked subagent inherits context. Docs suggest routing to Haiku for cost — user override: Sonnet 4.6 low effort.

- https://www.anthropic.com/engineering/multi-agent-research-system (Jun 13 2025) — VERIFIED: orchestrator-worker; Opus 4 lead + Sonnet 4 subagents beat single-agent Opus 4 by 90.2% on internal research eval; token usage explains 80% of BrowseComp variance; agents ~4× chat tokens, multi-agent ~15×; most coding tasks less parallelizable than research; lead saves plan to Memory because context >200k gets truncated; early failures: 50 subagents for simple queries, endless search, agents distracting each other; each subagent needs objective, output format, tool/source guidance, clear task boundaries; vague briefs → duplicate work; embedded effort-scaling rules (1 agent 3–10 calls simple; 2–4 subagents 10–15 calls comparison; more for complex).
- https://www.anthropic.com/engineering/harness-design-long-running-apps (Mar 24 2026, Prithvi Rajasekaran) — VERIFIED: GAN-inspired generator + evaluator; three-agent planner/generator/evaluator for multi-hour autonomous full-stack builds; two failure modes: coherence loss as context fills + "context anxiety" (premature wrap-up); context RESET (fresh agent + structured handoff) vs compaction (continuity but no clean slate); Sonnet 4.5 needed resets; self-evaluation skews positive; "tuning a standalone evaluator to be skeptical is far more tractable than making a generator critical of its own work"; evaluator used Playwright MCP to navigate live page; 5–15 iterations, runs up to 4 hours; generator decides refine-vs-pivot after each evaluation; scores plateau, middle iteration sometimes preferred; earlier harness: initializer decomposes spec into task list, coder implements one feature at a time with handoff artifacts; mentions "Ralph Wiggum" loop method.

- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents (Nov 26 2025) — VERIFIED: sessions begin with no memory ("engineers working in shifts"); compaction isn't sufficient; failure 1: one-shotting → runs out of context mid-feature, next session guesses; failure 2: later agent sees progress and declares job done; initializer agent writes init.sh, claude-progress.txt, initial git commit, and a comprehensive feature list (200+ features for claude.ai clone) all marked `"passes": false`; coding agents may only flip `passes`; "It is unacceptable to remove or edit tests"; JSON less likely to be inappropriately rewritten than Markdown; one feature at a time; commit with descriptive messages + progress summary; leave "clean state" mergeable; mark-complete-without-e2e failure → prompt browser automation, test as human user; session start ritual: pwd, read progress + git log, read feature list, pick highest-priority failing feature, run init.sh + basic e2e smoke BEFORE new work.
- https://claude.com/blog/getting-started-with-loops — (search snippet; fetch failed, page >500KB) "Loop engineering": four loop types turn-based, goal-based, time-based, proactive; /goal, /loop, /schedule.

- https://cldnavi.com/en/blog/claude-code-loops-guide-2026/ (SECONDARY summary of claude.com/blog/getting-started-with-loops, which exceeded fetch size) — four loop types: turn-based (encode verification in a SKILL.md: start dev server, interact, before/after screenshots, zero console errors; "never return partial verification"), goal-based `/goal ... Stop after 5 attempts`, time-based `/loop 5m` (local, stops when PC off) vs `/schedule` (cloud routine), proactive (`/schedule` + `/goal` + parallel worktrees + adversarial reviewer); token principles: right primitive/model, clear success+stop conditions, pilot a small slice before launching hundreds of agents, scripts for deterministic work, monitor with `/usage`, `/goal` status, `/workflows`.
- https://x.com/RLanceMartin/status/2064397389189071163 (search snippet, Anthropic's Lance Martin) — quote VERIFIED as attributable: "We've found that a verifier sub-agent tends to outperform self-critique with Fable 5, because grading is done in an independent context window. Outcomes in CMA handles this by spawning a grader sub-agent for you."
- https://movez.substack.com/p/build-self-improving-agent-system — the post itself republished (same text).

- https://code.claude.com/docs/en/headless — VERIFIED: `claude -p` non-interactive; exit 0/non-zero; `--allowedTools`; `--output-format json` includes `total_cost_usd` + per-model breakdown (client-side estimate); `--output-format stream-json --verbose`; `--bare` skips hooks/skills/subagents/plugins/MCP/auto memory/CLAUDE.md (recommended for CI; will become default for -p) → a skill-driven run must NOT use --bare or must pass `--add-dir` / `--agents` / `--settings`; without --bare, -p runs project hooks and MCP servers with no trust dialog; background subagent/workflow keeps -p open, idle wait ceiling 10 min (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`); SIGTERM exit 143 leaves turn unfinished, resume continues it; SIGINT ends turn.
- https://www.anthropic.com/claude-fable-and-mythos-5-1 (search snippet) + https://codewalkers.com/news/ai-models/claude-fable-5-1-mythos-5-1/ + https://letsdatascience.com/news/anthropic-releases-claude-fable-51-and-mythos-51-0e33494c (secondary) — Fable 5.1 released Sep 1 2026; $10/$50 unchanged; cheaper cache reads; 1M context, 128k max output; "when set to Low or Medium effort, Fable 5.1 achieves results similar to or better than Fable 5's at a much lower cost"; Mythos 5.1 restricted to trusted-access programs; secondary report of Fable 5 "June export-control suspension"; fewer false refusals (MacRumors headline).
- https://growthexe.substack.com/p/designing-loops-with-claude-fable (secondary) — attributes the "Rather than directly prompting and steering Fable 5, it's often better to design loops..." quote to an Anthropic speaker; primary source not located.

- https://www.anthropic.com/claude-fable-and-mythos-5-1 (Sep 2026) — VERIFIED: Fable 5.1 and Mythos 5.1 are the same model with different safeguards; Fable 5.1 ~25% cheaper than Fable 5 for typical workloads via cheaper cache reads, up to ~45% for highly agentic work; cyber safeguards block 60% fewer false positives; Fable 5.1 may be used to DISCOVER vulnerabilities but not develop exploits; "Fable 5.1 defaults to High effort in Claude Code"; Low/Medium effort ≈ or > Fable 5 at much lower cost; in benchmark interventions "cybersecurity tasks were completed by Claude Opus 4.8, and biology tasks were completed by Claude Opus 5" (so Opus 4.8 as cyber fallback is real); MongoDB quote: ran for hours unattended with strong verification loops, woke up to next phase finished with visual walkthrough + evidence.

- https://code.claude.com/docs/en/model-config — VERIFIED, HIGH IMPACT: aliases on Anthropic API resolve `opus` → Opus 5 and `sonnet` → Sonnet 5 (Claude Platform on AWS: sonnet → Sonnet 4.6; Bedrock/Vertex sonnet → 4.5); `fable` → Fable 5.1 (v2.1.257+); `opus` was Opus 4.8 only between v2.1.154 and v2.1.219; pin with full model names or `ANTHROPIC_DEFAULT_OPUS_MODEL` / `ANTHROPIC_DEFAULT_SONNET_MODEL` / `ANTHROPIC_DEFAULT_FABLE_MODEL` → the skill MUST pin Opus 4.8 / Sonnet 4.6 by full ID, never by alias; Fable not the default on any plan; Fable classifier flags (most often cyber/bio) trigger "automatic model fallback" in Claude Code; Fable guidance: describe the outcome not the steps, set a /goal, hand it ambiguous problems, skip verification reminders, size up larger tasks; `opusplan` alias exists.

- https://github.com/anthropics/claude-code/issues/74311 (Jul 5 2026, user feature request; describes current behaviour) — On the Anthropic API, when Fable's classifier flags a request Claude Code re-runs it on a fixed default Opus (currently Opus 4.8) and the switch is STICKY for the session until manual `/model`; `--fallback-model`/`fallbackModel` fires only on availability errors (overload), never on classifier flags; `"switchModelsOnFlag": false` gives a pause-and-choose prompt (unsuitable for unattended runs); related issues #73833 (fallback preserves effort level instead of mapping to capability-equivalent tier), #67009 (auto-restore primary model after `model_refusal_fallback`), #68107 (auto-mode classifier fallback undocumented).
- https://platform.claude.com/cookbook/fable-5-fallback-billing-guide (search snippet) — detect classifier blocks on Fable 5 and fall back to Opus 4.8 via server-side or SDK client-side fallback.
- https://avinashsangle.com/blog/claude-code-fable-5-model-routing (SECONDARY snippet) — claims Fable 5 at 2× Opus 4.8 per-token price (contradicts post's "~5×"), "sessions silently reroute to Opus 4.8".
- https://code.claude.com/docs/en/env-vars (snippet) — `ANTHROPIC_DEFAULT_FABLE_MODEL` is also the ID recognized as Fable for automatic fallback on third-party providers.

- https://code.claude.com/docs/en/auto-mode-config — VERIFIED: auto mode routes tool calls through a classifier blocking irreversible/destructive/external actions; deny and explicit ask rules evaluated BEFORE the classifier; default trusts only working dir + repo remotes; auto mode allows pushes to any branch incl. default branch and PR creation by default (v2.1.211+) → human checkpoint needs `permissions.ask` ["Bash(git push *)", "Bash(gh pr create *)"]; ask rules don't match `git -C dir push` variants → use a PreToolUse hook for full-text inspection; `permissions.deny` in managed settings cannot be overridden; boundaries stated only in conversation can be LOST after compaction → put them in rules; classifier reads CLAUDE.md; does NOT read `autoMode` from project `.claude/settings.json` (anti-injection).

- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (Sep 29 2025) — VERIFIED: "context rot" (recall falls as tokens grow); context is finite "attention budget"; aim for "smallest possible set of high-signal tokens"; prompts at the "right altitude" (between brittle if-else hardcoding and vague guidance); curate diverse canonical examples rather than laundry lists of edge cases; agents = "LLMs autonomously using tools in a loop".
- arcwell/docs/operations/review-process-amendment.md:3-21 — after eighteen M1 adversarial rounds the owner deferred review to one cross-milestone review; M2–M7 close on green named non-live exit gates + traceability + mutation testing; "No milestone may claim a live provider/unattended acceptance result that was not actually run"; rationale lines 25-31: repeated remediation loop "prevented progress" (review fatigue evidence).
- arcwell/docs/operations/milestone-ledger.md:3-4 — "An item is checked only after the gate command has been run green on a clean workspace"; line 21-27 exit gates with timestamps; line 47 requirements demoted to later milestones BECAUSE a clause had no oracle; line 279 live acceptance PENDING, "no live gate may be marked PASSED without cited evidence"; statuses like "PROVISIONALLY CLOSED; FINAL REVIEW PENDING", "HUMAN GATE PENDING".
- arcwell/docs/handoff/2026-08-21-morning-remediation-handoff.md:3-7,9-22,35-41 — self-contained handoff after an 8-agent deep audit: orientation (repo, commit, deployed resources), what works (verified against sent bytes), what is NOT available to a remote agent, priority-ordered remediation with exact file:line fixes, and a single verification bar command line.
- https://www.anthropic.com/engineering/building-effective-agents (Dec 19 2024) — VERIFIED: "find the simplest solution possible, only increasing complexity when needed"; workflows (predefined code paths) vs agents (LLM directs own process); patterns: prompt chaining with programmatic "gate" checks between steps; routing; parallelization (sectioning, voting); orchestrator-workers (subtasks not predefined); evaluator-optimizer (good fit when clear evaluation criteria exist and feedback demonstrably improves output); frameworks obscure prompts — understand the underlying code.
- https://code.claude.com/docs/en/github-actions (listed in llms.txt index) — Claude Code GitHub Actions: respond to @claude mentions, automate tasks, issues → PRs.
