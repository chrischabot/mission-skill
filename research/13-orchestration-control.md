# 13. The orchestrator's control loop: phases, gates, definition of done, autonomy, reporting

Researcher report for the `/drive` skill. Component: the spine that every other component
hangs from. Written 2026-09-14 against Claude Code 2.1.263 (the version installed on this
machine) and the live docs at code.claude.com and platform.claude.com. Where a claim is my
opinion rather than a verified fact, the text says so.

## 1. Executive opinion

The control loop has one job: make it structurally hard for the run to end in a mirage. Every
other property the owner wants (autonomy, lean context, compounding lessons, honest reports)
falls out of three mechanisms, and the skill should be built around them rather than around a
long list of phases.

First, the loop must separate the agent that does the work from the agent that judges it. The
platform docs say it plainly: separate, fresh-context verifier subagents tend to outperform
self-critique. The orchestrator therefore never certifies its own gates. It writes a claim,
hands the artifact and the claim to a gatekeeper that has not seen the reasoning, and accepts
only a verdict backed by evidence it can point to.

Second, the loop must keep its working memory in files, not in the conversation. Compaction
re-injects at most 5,000 tokens of the skill and re-reads at most five recently modified
files, and a file over 5,000 tokens comes back as a bare path. A STATE.md kept under that size
and rewritten before every fan-out is the only memory that reliably survives a long run.

Third, the loop must be bounded by conditions it can check, not by feelings of completeness.
The two documented failure patterns of long-running agents are trying to do everything at once
and declaring victory because progress exists. A feature list that starts fully failing, a
status ladder that forbids "Live Proof" for local-only work, and a stop condition phrased as
evidence in the transcript are the counters.

Phases are then a scheduling convenience, not a ceremony. The canonical sequence exists so
that the skill can collapse it: a bug hunt runs six phases, a greenfield app runs fifteen, and
the collapse rule is written into the intake step so the orchestrator never has to argue with
itself about which phases pay for themselves. Gates carry the rigor; phases carry the order.

## 2. What the post says, and a critique

The post is right about the architecture and loose about the evidence. Its central move, that
self-improvement is a property of the system around a stateless model, is correct and matches
Anthropic's own guidance. Its layering (primitives, orchestration, memory, self-improvement) is
a fair way to organize a skill. Its warning against self-critique is verified: the platform
docs' Fable 5 prompting guide recommends fresh-context verifier subagents over self-critique.
Its two operational rules for state files, write before walking away and read at session
start, are the same rules Anthropic's own long-running-harness post derived empirically.

It is exaggerated or wrong in ways that matter for this component:

The "Anthropic engineering team puts it directly" quote about designing loops instead of
prompting and steering is not in any official Anthropic page I could find. Secondary sources
attribute it to an unnamed Anthropic engineer and the earliest primary I can locate is an X
article by Lance Martin titled "Designing loops with Fable 5". Treat it as a source claim, not
a documented recommendation. The idea itself is sound and the official docs say the same thing
in other words ("Describe the outcome, not the steps... To keep it working toward that outcome,
set a goal").

The Haiku-as-grader recommendation contradicts the owner's explicit distrust, and the docs
give him a clean way around it: prompt-based hooks accept a `model` field, and the `/goal`
evaluator model can be swapped per process with `ANTHROPIC_DEFAULT_HAIKU_MODEL`. The skill
should use Sonnet at low effort for graders and say so.

The post frames `/goal` as a loop with an independent grader, which oversells it. The
evaluator is a single call by a small model with no tools that reads the transcript. It is a
turn-driver that decides whether to start another turn, not a verifier. The verifier has to be
a subagent that reads files and runs commands. Conflating the two is exactly how a run ends
"met" on a transcript that says the tests pass without the tests having run.

The "five-stage memory progression" and its verification-coverage percentages are attributed
to a "Continual Learning Bench 1.0" I could not verify. The progression itself (fail,
investigate, verify, distill, consult) is a useful shape for the retro phase and I keep it,
but the numbers should not appear in the skill.

The post's model matrix names Sonnet 4.6, Opus 4.8 and Haiku 4.5; the brief corrects that to
Fable 5.1, Opus 4.8 and Sonnet 4.8. The live docs disagree with both: on the Anthropic API the
`opus` alias resolves to Opus 5 and `sonnet` to Sonnet 5, the pricing page lists no Sonnet 4.8
at all, and Opus 4.8 is a legacy model still served at the same price as Opus 5. The skill
should use aliases and state what they resolve to today rather than pin version numbers.

Finally, the post never mentions budgets, stop conditions for impossible goals, or what to do
when a run discovers that its premise was wrong. Those are the parts of the control loop that
decide whether a days-long run is an asset or a bill.

## 3. Verified facts

Everything below was read from the cited page on 2026-09-14 unless marked otherwise.

### 3.1 `/goal` (https://code.claude.com/docs/en/goal)

- `/goal` is a wrapper around a session-scoped prompt-based Stop hook. After each turn the
  condition and the conversation go to the configured small fast model (Haiku by default) which
  returns one of three verdicts with a reason: not yet met, met, impossible.
- The evaluator does not call tools. It judges only what Claude has surfaced in the
  conversation, so the condition must be phrased as something the transcript can demonstrate.
- Conditions may be up to 4,000 characters. The docs recommend one measurable end state, a
  stated check, constraints, and a bound such as "or stop after 20 turns".
- If Claude answers the evaluator several turns in a row without using tools, Claude Code stops
  the loop with a warning and leaves the goal set.
- Background subagents or shell commands defer evaluation. After 30 minutes of waiting a
  check-in is due; later check-ins double up to four times the first interval. In a `-p` run,
  check-ins are delivered only at turn end. Idle check-ins are capped at three per goal.
  `CLAUDE_CODE_GOAL_CHECKIN_MINUTES` changes the first interval; `0` disables check-ins and
  automatic retries.
- Four errors clear the goal: authentication failure, exhausted credits, a context overflow that
  auto-compaction could not clear, and an unavailable model. Other errors retry (three times)
  or pause the goal.
- `/goal` with no argument shows the condition, elapsed time, turns evaluated, token spend and
  the evaluator's latest reason. Resume restores an active goal but resets turn count, timer
  and token baseline.
- `claude -p "/goal ..."` runs the loop to completion; add `--output-format stream-json
  --verbose` to see progress. A goal does not change permission mode; unattended goal turns
  need auto mode.
- `ANTHROPIC_DEFAULT_HAIKU_MODEL` changes the evaluator model, and every other place Claude Code
  uses the small fast model, including conversation summarization.

### 3.2 Compaction and what survives it

- After auto-compaction, the most recent invocation of each skill is re-attached, keeping the
  first 5,000 tokens of each, within a shared 25,000-token budget filled from the most recently
  invoked skill; older skills can be dropped entirely. Truncation keeps the start of the file
  (https://code.claude.com/docs/en/skills, https://code.claude.com/docs/en/context-window).
- Also re-injected from disk: project-root CLAUDE.md and unscoped rules, auto memory, the plan
  written in plan mode, and up to five files Claude read or edited (most recently modified
  first). A file over 5,000 tokens comes back as a path reference without content. SessionStart
  hooks matching the `compact` source run and their output is added
  (https://code.claude.com/docs/en/context-window#what-survives-compaction).
- Compaction clears older tool outputs first, then summarizes. A "Compact Instructions" section
  in CLAUDE.md steers what is kept. If a single output refills context immediately, Claude Code
  stops auto-compacting after a few attempts and shows a thrashing error
  (https://code.claude.com/docs/en/how-claude-code-works#when-context-fills-up).
- Models with a native 1M window (the Fable models, Sonnet 5, Opus 4.7 and later on the
  Anthropic API) compact at about 967K tokens by default. `/autocompact 500k`, `--autocompact`,
  or `CLAUDE_CODE_AUTO_COMPACT_WINDOW` lower it (https://code.claude.com/docs/en/model-config).

### 3.3 Subagents (https://code.claude.com/docs/en/sub-agents)

- Each subagent starts with a fresh context: its own system prompt, the delegation message
  Claude writes, the full CLAUDE.md hierarchy (except the built-in Explore and Plan agents), a
  git status snapshot, and any preloaded skills. It does not see the parent conversation, the
  skills already invoked, or files already read.
- `maxTurns` stops a subagent and returns its output marked partial; Claude can resume it with
  `SendMessage` using the agent id or name, with full prior context. Explore and Plan are
  one-shot and cannot be resumed.
- Background subagents get a reduced built-in tool set (Read, Grep, Glob, Bash and a few
  others; every MCP tool stays). Their results arrive as a completion notification in a later
  turn. An API error in a background subagent marks it failed and delivers its last output.
- Subagents nest up to three layers below the main conversation
  (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`); at most 20 run concurrently
  (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`); resumes bypass the concurrency check.
- `memory: user|project|local` gives a subagent a persistent directory
  (`~/.claude/agent-memory/<name>/` for user scope).
- `isolation: worktree` gives a temporary worktree removed automatically when the subagent
  finishes without changes; a worktree with changes stays on disk until a periodic sweep older
  than `cleanupPeriodDays` (https://code.claude.com/docs/en/worktrees).
- `CLAUDE_CODE_SUBAGENT_MODEL` sets the default model for subagents, teammates and workflow
  agents; a per-invocation `model` also applies on resume.
- Locally: `~/.claude/agents/` does not exist on this machine. The brief notes that the first
  file in a directory that did not exist at session start needs a restart to be picked up.

### 3.4 Dynamic workflows (https://code.claude.com/docs/en/workflows)

- A workflow is a JavaScript script Claude writes; `agent()`, `pipeline()`, `parallel()`,
  `phase()`, `log()`, the `args` global; runs in the background; `/workflows` shows phases and
  per-agent token usage. Scripts save to `.claude/workflows/` or `~/.claude/workflows/`.
- Default size setting `medium` means fewer than 15 agents. Hard limits: 4,096 items per
  `parallel()` or `pipeline()`, 1,000 agents per run.
- `agent()` resolves to `null` if stopped or on an unrecoverable API error; a `schema` makes an
  agent return JSON. `Date.now()` and `Math.random()` throw so a relaunch repeats the same
  calls. Resume after a pause returns finished agents from cache and reruns the failed one and
  everything after it.
- Opt-in is by the word `ultracode` in the prompt, by asking for a workflow, or by
  `/effort ultracode` (xhigh effort plus automatic workflow orchestration).

### 3.5 Hooks (https://code.claude.com/docs/en/hooks, https://code.claude.com/docs/en/hooks-guide)

- Prompt-based hooks (`type: prompt`) take `prompt`, optional `model` (defaults to a fast
  model), `timeout` (30 s default). On `Stop`, `ok: false` feeds the reason back as the next
  instruction; `impossible: true` lets the turn end.
- Agent-based hooks (`type: agent`, experimental) spawn a subagent with Read, Grep and Glob for
  up to 50 turns; default timeout 60 s; no `impossible` field.
- Claude Code overrides a Stop hook after eight consecutive blocks without progress. Stop hook
  input includes `last_assistant_message`, `background_tasks` and `session_crons`, so a hook can
  tell "done" from "waiting on background work".
- SessionStart matchers: `startup`, `resume`, `clear`, `compact`, `fork`. On `resume` and `fork`
  the hook also receives `seconds_since_last_response`, `context_tokens`,
  `prompt_cache_likely_expired`, `estimated_cache_write_usd` (v2.1.251+).
- PreCompact fires with matcher `manual` or `auto` and can block compaction.
- Hooks declared in skill frontmatter are registered when the skill is invoked and keep running
  for the rest of the session; `once: true` removes a hook after its first successful run and
  is honored only in skill frontmatter. Hooks in subagent frontmatter run only while that
  subagent runs, and `Stop` there becomes `SubagentStop`.
- The best-practices page: "Have Claude show evidence rather than asserting success," and the
  four ways to gate a stop: in one prompt, `/goal`, a deterministic Stop hook, or a second
  opinion from a verification subagent or workflow
  (https://code.claude.com/docs/en/best-practices#give-claude-a-way-to-verify-its-work).

### 3.6 Headless and CLI (https://code.claude.com/docs/en/headless, https://code.claude.com/docs/en/cli-reference)

- `--max-turns` (print mode only) exits with an error at the limit. `--max-budget-usd` (print
  mode only, v2.1.217+) caps API spend including subagents; at the cap, spawning fails with
  "Budget limit reached" and running background subagents are stopped.
- A `-p` run stays open while background subagents or workflows run, with a 10-minute idle
  ceiling (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`, `0` to wait without one). Background shell
  tasks are killed about five seconds after the final result.
- SIGTERM exits with code 143 and leaves the turn unfinished; resuming continues it.
- `--permission-mode auto --permission-prompts none` denies anything that would have prompted.
- `--name` sets a session name; `claude --resume <name>` or `<session-id>` resumes it from any
  directory. Sessions created with `-p` are excluded from the picker and from `--continue`, but
  `--resume <id>` still works. `--fork-session` makes a new id on resume
  (https://code.claude.com/docs/en/sessions).

### 3.7 Models, pricing, effort

- `fable` resolves to Fable 5.1 (v2.1.257+); on the Anthropic API `opus` resolves to Opus 5 and
  `sonnet` to Sonnet 5 (https://code.claude.com/docs/en/model-config). Fable is never the
  account default; select it explicitly.
- List prices per million tokens (input / output): Fable 5.1 $10 / $50; Opus 5 and Opus 4.8
  $5 / $25; Sonnet 5 $2 / $10; Haiku 4.5 $1 / $5. Cache reads cost 10% of input. Batch is half
  price. No Sonnet 4.8 is listed (https://platform.claude.com/docs/en/about-claude/pricing).
- Current roster: Fable 5.1, Opus 5, Sonnet 5 (all 1M context, 128K output, default effort
  `high`), Haiku 4.5 (200K). Opus 4.8 and Fable 5 are legacy but available
  (https://platform.claude.com/docs/en/about-claude/models/overview).
- Effort levels `low|medium|high|xhigh|max` on Fable 5/5.1, Opus 5, Sonnet 5, Opus 4.8, Opus
  4.7. Skill frontmatter `effort` overrides the session for the turn.
- Fable safety classifiers: cybersecurity-flagged requests re-run on Opus 4.8,
  biology-flagged on Opus 5, with a transcript notice (v2.1.219+).
- Claude Code's own Fable guidance: describe the outcome, not the steps; hand it ambiguous
  problems; skip verification reminders; size up larger tasks; set a goal to keep it working
  (https://code.claude.com/docs/en/model-config#work-with-fable).

### 3.8 Anthropic prompting guidance that bears on the loop

- Fable 5 prompting guide (https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5):
  "Separate, fresh-context verifier subagents tend to outperform self-critique." Also: a
  standing instruction to audit progress claims against tool results "nearly eliminated
  fabricated status reports"; give the model a memory file with one lesson per file; keep the
  lead agent working while subagents run; reassure the model about context so it does not
  suggest a new session; a send-to-user tool for verbatim mid-run messages.
- Fable 5.1 prompting guide (https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1):
  an autonomy block ("You are operating autonomously. The user is not watching...") whose
  opening sentence carries most of the effect; a "Delivering work" block ("the scope is the
  deliverable: don't quietly narrow, widen, or swap it"); a compaction-summary instruction
  listing six things to preserve; and a scope-discipline block that stops unrequested fixes and
  extra test files "with no measurable change in task success".
- Effective harnesses for long-running agents
  (https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents): two
  failure patterns (one-shotting the app; declaring the job done because progress exists);
  fixes: an initializer that writes a progress file, an init script and a feature list marked
  all failing; one feature at a time; commit plus progress note after each; start every
  session by reading progress and git log and running a smoke test; verify end to end as a
  user would, not with unit tests alone.
- Effective context engineering (https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents):
  context is an attention budget; compaction, structured note-taking, and sub-agent
  architectures are the three tools; note-taking "excels for iterative development with clear
  milestones".
- Multi-agent research system (https://www.anthropic.com/engineering/multi-agent-research-system):
  each delegation needs an objective, an output format, tool guidance and boundaries; embed
  scaling rules (one agent and 3-10 calls for a fact, 2-4 subagents for a comparison, 10+ for
  complex research); multi-agent systems use about 15 times the tokens of chat; evaluate end
  state, not path; LLM-as-judge against a rubric scales.
- Building effective agents (https://www.anthropic.com/engineering/building-effective-agents):
  prefer the simplest thing that works; orchestrator-workers and evaluator-optimizer are the
  two relevant patterns.

### 3.9 Owner's rules (from his memory files, binding)

- Completion means code, tests, severe review, live proof where relevant, docs and status files
  all agreeing. Ladder: Missing, Scaffold, Partial, Local Proof, Live Proof, Operational, Done.
  Local-only work is never Live Proof. Ground truth: code and tests, then proof artifacts,
  then status files, then prose. Ask of any shim where it is kinder than the real thing.
- No approval queues. Anything gated on him reviewing an inbox never completes. One choice,
  surfaced once, in conversation, only when unavoidable.
- Commit straight to main. No branch or worktree left at the end of a turn. A worktree used
  mid-step is merged and deleted in the same step.
- Never wait on a scheduler. Load the system's own tools early and drive it through them.
  "It will happen when the cron runs" is not done. A workaround used twice means the diagnosis
  was wrong.
- Plain language. No rule IDs or codenames in anything he reads.

## 4. Detailed spec

### 4.1 Where the loop lives

The orchestrator keeps its working memory in a small directory inside the target project. The
directory is committed to main like any other file, so the run's history rides with the code
and a fresh session can rebuild the orchestrator's context from disk.

```
.drive/
  GOAL.md          the goal as given, the shape classification, the phase plan, the budget
  STATE.md         working memory: phase, ladder, next action, open failures, decisions log
  FEATURES.json    behavioral claims with status; starts entirely "failing"
  RESEARCH.md      research ledger (owned by the research component; the loop only reads it)
  LESSONS.md       distilled lessons for this project (the compound phase writes here)
  evidence/        one file per gate verdict, named <phase>-<gate>-<n>.md, plus screenshots
  report.md        the final report, written once, at the end
```

Two size rules are mechanical, not stylistic. STATE.md stays under 5,000 tokens (roughly 3,500
words) because compaction re-reads it only if it is one of the five most recently modified
files and under that size; anything larger returns as a bare path. Everything that would push
it over goes into `evidence/` or LESSONS.md and STATE.md keeps a one-line pointer. The
orchestrator rewrites STATE.md before every fan-out and after every gate verdict, which also
keeps it among the five most recently modified files when compaction hits.

GOAL.md is written once at intake and edited only by the re-plan protocol (section 4.9), so
the original ask survives every later reinterpretation. The owner reads GOAL.md and report.md;
STATE.md is for the orchestrator.

### 4.2 The phase model

The canonical sequence covers the largest shape. Every other shape is a subset chosen at
intake by the collapse rules below; the orchestrator writes the chosen list into GOAL.md and
never adds a phase back without logging why.

| # | Phase | What it produces | Entry gate | Exit gate |
| - | ----- | ---------------- | ---------- | --------- |
| 0 | Intake | GOAL.md: shape, size, phase plan, budget, first STATE.md | a goal string | shape and size classified; phase list and budget written; the single question asked if unavoidable |
| 1 | Recon | map of the code, tools, constraints, consumers; environment proven to run | GOAL.md exists | smoke command runs green (or its absence is recorded); system tools loaded; consumers of anything to be changed listed |
| 2 | Research | RESEARCH.md with claims marked verified / source claim / opinion | recon done or shape is research-first | every decision-bearing claim has a source or is marked opinion |
| 3 | Spec | behavioral claims, acceptance criteria, non-goals, FEATURES.json all failing | research done | each feature names a refutable claim and the check that would refute it |
| 4 | Design | architecture, data model, contracts, model routing, test strategy incl. harness parity | spec gate passed | every production constraint the tests must honor is named (limits, quotas, auth, timeouts) |
| 5 | Decompose | work packets with file ownership, dependency order, waves | design gate passed | no two packets in a wave own the same file; each packet has its claim, its test, its budget |
| 6 | Build | code + tests + local proof per packet, committed to main | packet assigned | tests that try to refute the claim exist and pass; commit on main; STATE.md updated |
| 7 | Verify | gatekeeper verdict per packet | build exit for the packet | independent verdict "holds" with evidence file; failures loop to Build |
| 8 | Integrate | the whole system running end to end locally | all packets in the wave verified | end-to-end smoke as a user would do it; integration bugs fixed |
| 9 | Live proof | deployed, exercised against real infrastructure, UI seen | integrate gate passed | evidence from the live system: URL, logs, screenshot, simulator run; ladder set to Live Proof |
| 10 | Harden | severe testing, security review, simplification | live proof passed | severe findings scored 75+ fixed with regression tests; security review clean or findings logged with decision |
| 11 | Docs | README, runbook, decision records | harden passed | docs match code (gatekeeper spot-checks three claims) |
| 12 | Compound | LESSONS.md, skill updates, agent memory | docs passed | every open failure has a root cause or an honest "unknown"; lessons written as general rules |
| 13 | Report | report.md, one-line user summary | compound passed | report derived from STATE.md and evidence, not from the plan |

Two phases in the brief's list are folded in rather than dropped. "Test plan" lives inside
Design because the test strategy and the harness-parity question ("where is the shim kinder
than production?") are architecture decisions. "Retro" is the Compound phase.

Collapse rules, applied at intake and written into GOAL.md:

- Bug hunt: Intake, Reproduce, Diagnose, Fix, Verify, Compound, Report. Reproduce is Recon
  narrowed to one question (can I make it fail on demand?). Diagnose is Spec narrowed to the
  root-cause claim. Fix is Build for one packet whose test is the reproducer turned regression
  test. Verify is the gatekeeper confirming the regression test fails on the old code and
  passes on the new. No Design, Decompose, Integrate, Docs unless the fix touches a contract.
- Feature on an existing product: all phases, but Research only if the feature depends on an
  external API or a design question the codebase cannot answer; Decompose only if more than
  three packets; Live proof required if the product is deployed.
- Migration or consolidation: all phases, with Recon expanded into a consumer census (who calls
  the thing being moved, including cron jobs, other repos, and dashboards), Spec expressed as
  a parity contract, Integrate including a shadow or dual-run period where possible, and Live
  proof meaning the old path is off and the new path carries real traffic.
- Research plus website: Intake, Research, Spec (content and information architecture),
  Design, Build, Verify (Lighthouse, accessibility, vision), Live proof (deployed URL), Docs,
  Compound, Report. Decompose only for more than three sections built in parallel.
- Pure research: Intake, Research, Report, Compound. The "build" is the report; the gatekeeper
  checks claim discipline instead of tests.
- Refactor or simplification: Intake, Recon, Spec (the invariant: behavior unchanged, named
  tests as oracle), Build, Verify, Harden (severe testing of the invariant), Compound, Report.
- Ops or incident: Intake, Reproduce (observe), Diagnose, Fix, Live proof (the system is
  healthy now, shown by its own tools), Compound (the lesson and the missing alarm), Report.

Size affects budgets, not the phase list (section 4.6). The one exception: a task classified
"small" (a single file, a single behavior) may skip the gatekeeper for packets and use the
gatekeeper once, at the end.

### 4.3 Gates as checkable conditions

A gate is a claim, the evidence that would settle it, the party that checks it, and what
happens on failure. The orchestrator never checks its own exit gates for Build, Verify,
Integrate, Live proof and Harden; those go to the gatekeeper subagent (section 6), which
starts with a fresh context and sees the artifact and the claim, not the reasoning that
produced them. Intake, Recon, Spec, Design, Decompose and Docs gates are checked by the
orchestrator itself, because the cost of an independent check exceeds the cost of being wrong
there, with one exception: the Design gate's harness-parity list is reviewed by the gatekeeper
because that is where the owner's D1 bind-variable class of bug is born.

Every gate verdict is written to `evidence/<phase>-<gate>-<n>.md` in this shape:

```
Claim: <one sentence, the behavior or property being asserted>
Check: <the exact command or action run, verbatim>
Result: <exit code, key output lines, screenshot path>
Verdict: holds | refuted | unverifiable
Ladder: Missing | Scaffold | Partial | Local Proof | Live Proof | Operational | Done
Notes: <what would have to be true for "unverifiable" to become "holds">
```

The gatekeeper writes the file; the orchestrator reads only the Verdict and Ladder lines plus
Notes when the verdict is not "holds". That keeps gate results at a few hundred tokens each in
the orchestrator's context.

Failure loops are bounded. A refuted Build gate sends the packet back to a builder with the
evidence file attached, at most twice. A third refutation is not a retry; it is a Discovery
(section 4.9), because the owner's rule applies: the second time a workaround is needed, the
diagnosis was wrong. A refuted Live proof gate loops to Integrate, not to Build, because the
usual cause is an environment difference the local harness hid. A refuted Harden gate (a
severe finding scored 75 or higher) creates a new packet with the finding as its refutation
test and runs Build and Verify for it; the Harden gate is then re-run in full, not
incrementally, because fixes for severe findings tend to open neighbors.

Gate checks are commands where they can be. The skill should instruct the gatekeeper to prefer,
in order: a command with an exit code; a diff against an oracle; a screenshot compared to a
stated expectation; a reading of the code. A verdict that rests only on reading code is
labeled as such in the evidence file and caps the ladder at Partial.

### 4.4 Definition of done

The ladder is the vocabulary and the skill should print it in every status line, because the
words force the distinction the owner cares about:

| Rung | Meaning | Minimum evidence |
| ---- | ------- | ---------------- |
| Missing | nothing exists | none |
| Scaffold | files, types, stubs, a README exist; nothing runs the behavior | file list |
| Partial | some behavior runs; the claim is not fully tested or some paths are stubbed | test output with named gaps |
| Local Proof | the claim's refutation tests pass locally, against a harness whose kindness has been audited | test run, harness-parity note |
| Live Proof | the claim holds against the real environment: deployed backend, real device or simulator, real third-party API | URL, log line, screenshot, simulator run |
| Operational | live for a period with monitoring or a smoke check that would catch regression; runbook exists | monitor or scheduled smoke, runbook path |
| Done | all of the above plus docs, STATE.md, FEATURES.json and report agreeing | the gatekeeper's final verdict |

"Done" per shape, argued from the ladder rather than from feelings:

A website is done when it is deployed at its real URL, Lighthouse performance and
accessibility scores meet the thresholds written in GOAL.md at intake (I recommend 90 and 95
as defaults, adjustable at intake), every navigation path in FEATURES.json has been walked by a
browser subagent with screenshots in `evidence/`, the blog and docs sections render at least
one real entry each, and a vision check has compared the screenshots to the design intent.
Local `npm run build` green is Local Proof, not done.

An iOS app with a backend is done when the Xcode build succeeds from a clean checkout, unit and
UI tests pass, the app runs in the simulator with every screen in FEATURES.json visited and
screenshotted and inspected through the accessibility tree, the backend is deployed and the
app in the simulator has exercised it end to end against the deployed URL (not a mock), and a
severe test run against the backend has scored no unfixed finding at 75 or higher. A simulator
run against a mock backend is Local Proof for the app and nothing for the system.

A bug is done when a regression test exists that fails on the pre-fix code and passes on the
post-fix code (the gatekeeper checks both directions), the root cause is written in one
paragraph in LESSONS.md, the fix is committed to main, and if the bug was observed in a live
system the live system has been shown to no longer exhibit it through its own tools. A fix
without a failing-then-passing test is Partial.

A migration is done when the consumer census from Recon is fully covered by the new path with
parity tests, the old path is disabled (not merely unreferenced) and the disabling is
committed, real traffic has flowed through the new path with a log or metric to show it, and
the rollback is written and was exercised once. A migration whose old path is still on is Live
Proof at best.

A feature is done when its FEATURES.json entries are all "passing" with an evidence file each,
its live proof exists if the product is deployed, and the docs mention it where a user would
look.

A research report is done when every decision-bearing claim is labeled verified, source claim
or opinion with a URL where applicable, at least one disconfirming source was sought for each
central claim, and the gatekeeper has spot-checked three claims against their sources.

Non-done states must be reported as themselves. The skill should forbid the words "complete",
"done", "shipped" and "working" in STATE.md or the report for anything below Live Proof when
live proof was in scope, and require the rung name instead. The honest forms are:

- "Local Proof: passes 41 refutation tests locally; not deployed because <reason>; the
  deploy command is <command>."
- "Partial: the happy path works; the retry path is stubbed at <file:line> and its test is
  skipped; here is why."
- "Scaffold: types and routes exist; no behavior is implemented; nothing to verify."
- "Unverifiable: the claim needs <credential or system> I cannot reach; what I did instead
  is <substitute>, which proves less because <gap>."

### 4.5 Autonomy rules

The run assumes nobody is watching. The Fable 5.1 prompting guide supplies the exact sentence
that carries most of the effect and the skill should keep it as written: "You are operating
autonomously. The user is not watching in real time and cannot answer questions mid-task, so
asking 'Want me to…?' or 'Shall I…?' will block the work." The rest of the skill's autonomy
text then adds the owner's specifics:

Decide and log. Every reversible decision the goal does not settle is made by the orchestrator
and recorded in STATE.md under "Decisions" as one line: what was decided, the alternative
rejected, why, and how to undo it. Reversible covers everything git can revert, everything a
deploy can roll back, every file inside the project, and every configuration with an undo.

The single unavoidable question. A question is asked only when different readings would lead
to materially different work and both readings are plausible, or when an action is
irreversible and not implied by the goal. It is asked once, at the end of a turn that also
delivers all progress that does not depend on the answer, with a stated default the
orchestrator will take if no answer arrives. In a `-p` run there is no one to answer, so the
default is taken immediately and the question becomes a line in the report's "Assumptions".
Two questions in one run is a design smell; the skill should say so.

No approval queues. The loop never creates a list for the owner to work through: no "review
these 12 findings", no "confirm each migration", no "approve the deploy". It deploys, records,
and makes undo cheap. Where a decision genuinely needs him, it is the single question above,
not an item in a list.

Never wait on a scheduler. At Recon, the orchestrator loads the target system's own tools
(MCP verbs, CLI, API) and drives it through them. When something must happen, it calls the
verb. If no verb exists, the missing verb is a work packet, not a cron. A scheduled job is
acceptable only for conditions with no triggering signal, and a report never says "it will
happen when the schedule fires" as if that were done.

Commit to main, leave nothing behind. Each packet ends with a commit on main. A subagent that
needs a worktree merges and removes it inside the same packet; the Build exit gate includes
`git worktree list` showing only the main checkout and `git branch --list` showing no
run-created branches. Scratch files live under `/private/tmp` or `.drive/evidence/`, never in
the working tree unless committed on purpose.

Never let the turn end early. Before ending any turn, the orchestrator checks its last
paragraph. If it is a plan, a question, a list of next steps or a promise, it does that work
now. It ends a turn only when the run is complete, when it is blocked on input only the owner
can give, or when a stop condition below has fired.

Stop conditions, and how to report a stop. The run stops early, and says so in the report,
when:

- the goal is impossible as stated (the evidence shows the premise is false, or the thing to
  fix does not exist, or the platform cannot do it); the report names the evidence and the
  nearest achievable goal;
- the next action is destructive and not implied by the goal (dropping data, force-pushing,
  deleting a live resource, sending to real users); the report names the action and what
  would happen if the owner ran it;
- the next action requires credentials, payments, legal acceptance or account creation; the
  orchestrator does everything that does not depend on it, records what is blocked and the
  exact step the owner must take;
- the budget is exhausted (section 4.6); the report shows where the spend went and what the
  next N turns would buy;
- the same failure has repeated after two distinct diagnoses; the report presents both
  diagnoses and the evidence that refuted each.

A stop report is the final report with a "Stopped because" section at the top and the ladder
for every feature as it stands. It never uses "done" for anything that is not.

Boundaries the loop enforces on itself, taken from the Fable 5 guidance and the owner's
rules: no unrequested actions outside the goal (no defensive branches, no drafting messages
nobody asked for, no fixing neighboring bugs; those go in the report as follow-ups); before a
command that changes system state, check that the evidence supports that specific action, not
a pattern that resembles a known failure.

### 4.6 Budgeting and bounding

Budgets exist so that a run that has gone wrong stops costing money before the owner notices.
They are set at intake from the size class, written into GOAL.md, and tracked in STATE.md.

Size classes and default budgets (my recommendation; the owner should tune after two or three
runs and the compound phase should propose adjustments):

| Size | Examples | Orchestrator turns | Subagent budget | Wall clock | Rough spend at list price |
| ---- | -------- | ------------------ | --------------- | ---------- | ------------------------- |
| small | one-file bug, copy change, a config fix | 15 | 4 subagents, 20 turns each | 30 min | $2 to $8 |
| medium | a feature, a focused refactor, a deep bug across modules | 40 | 12 subagents, 40 turns each | 3 h | $15 to $60 |
| large | a migration, a dashboard, a research report plus website | 100 | 30 subagents, 60 turns each | 12 h | $80 to $300 |
| greenfield | an app with backend and native frontend | 250 | 80 subagents, 80 turns each | 2 to 4 days | $300 to $1,500 |

The spend column is an estimate, not a fact. It assumes the orchestrator on Fable 5.1 at
$10/$50 per million tokens with heavy cache reads, builders on Sonnet 5 at $2/$10, gatekeepers
on Opus at $5/$25, and the multi-agent multiplier Anthropic measured (about 15 times a chat).
A greenfield run at the top of that range is real money, which is the argument for budgets
rather than against the approach.

How the orchestrator tracks spend. Claude Code gives it no in-conversation token counter, and
the Fable 5 guidance warns that showing the model a remaining-token countdown makes it stop
early. So the loop counts what it can see: its own turns (STATE.md carries a `turn:` counter
the orchestrator increments at the top of every turn), the number of subagents spawned and
their `maxTurns`, and wall clock from the timestamps in STATE.md. `/goal` status and `/usage`
show token spend to the owner, not to the model. In a `-p` run, `--max-budget-usd` and
`--max-turns` are hard caps and the skill should recommend them in the launch command; both are
print-mode only, so an interactive run relies on the turn counter and a `/goal` clause.

Per-phase caps (fraction of the run's turn budget): Intake 5%, Recon 10%, Research 15%, Spec
and Design together 15%, Build and Verify together 40%, Integrate and Live proof 10%, Harden
and Docs 5%, Compound and Report 5% (the last is a floor, not a cap: the report is written even
if everything else overran). When a phase reaches its cap, the orchestrator does not stop; it
records the overrun in STATE.md and decides between downgrading ambition and stopping.

Downgrade before stop. The downgrade ladder is: drop optional features (marked "nice" in
FEATURES.json), then narrow live proof to the critical path, then accept Local Proof with a
named reason for specific features, then stop. Each downgrade is a logged decision and appears
in the report as scope the owner did not get. Silent narrowing is the anti-pattern (section
7); logged narrowing is the loop working.

Subagent bounds. Every subagent definition carries `maxTurns` (section 6). A subagent that
returns partial output is resumed once with its own result attached; a second partial return
is treated as a failed packet and goes to the discovery protocol. The concurrency ceiling of 20
means a wave should be sized at 12 or fewer builders so gatekeepers can start while builders
run.

How `/goal` fits. The skill sets a goal at the end of intake, phrased so the transcript can
demonstrate it and bounded by the turn budget:

```
/goal .drive/report.md exists, its first line is "# Drive report" and it contains a
"Ladder" table in which every feature from .drive/FEATURES.json has a rung, and the
orchestrator's last message quotes the gatekeeper's final verdict file path; or stop after
<N> turns and write the report as a stop report.
```

The evaluator is a small model with no tools; it only needs to see that the report exists and
was quoted. The real judgment happened in the gatekeeper. The 30-minute check-ins are useful:
when a wave of background builders runs long, the check-in makes the orchestrator read their
output and stop stuck ones instead of waiting. In a `-p` run the check-in arrives only at turn
end, so the orchestrator should not end a turn while a wave runs unless it has nothing else
useful to do; the Fable 5.1 guidance to keep the lead working while subagents run applies.

To honor the owner's distrust of Haiku without global side effects, the recommended launch
command scopes the evaluator model to the process:

```
ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5 \
claude -p --name drive-<slug> --permission-mode auto --permission-prompts none \
  --max-turns 250 --max-budget-usd 400 --output-format stream-json --verbose \
  "/drive <goal>"
```

### 4.7 Keeping the orchestrator lean

The orchestrator's context is the scarcest resource in the run and every rule in this section
protects it.

Summaries in, files out. The orchestrator does not read source files, test output, logs or
documentation itself except for STATE.md, GOAL.md, FEATURES.json and gate verdict files. It
delegates reading to Explore subagents (which return conclusions, not file dumps) and asks
every subagent to write its full output to a file under `.drive/evidence/` and return at most
a fixed-size summary. Delegation prompts carry the four things the research post found
necessary: the objective, the output format (including the file path to write to and the
maximum summary length), the tools to use, and the boundaries (files it owns, files it must
not touch).

Fixed-size returns. Builders return: packet id, ladder rung, commit hash, evidence file path,
and at most five lines of notes. Gatekeepers return: verdict, ladder, evidence path, and Notes
only when the verdict is not "holds". Researchers return the RESEARCH.md path and a
ten-line summary. A subagent that returns more is told, in its system prompt, that the
remainder will be discarded unread.

Bash output discipline. The orchestrator pipes any command it must run itself through `tail`,
`grep -c`, or a `> file && echo done` pattern. It never runs a test suite in its own context;
a builder or the gatekeeper runs it and reports the exit code and failing test names.

STATE.md as working memory. The file is rewritten, not appended, so it stays small. Its shape:

```
# Drive state · <project> · <goal slug>
turn: 47   phase: Build (wave 2 of 3)   budget: 47/100 turns, 6/30 subagents   started: <iso>
## Now
<one paragraph: what is happening this turn and why>
## Next
<the next three actions, in order, each one line>
## Ladder
| feature | rung | evidence |
...
## Open failures
- <id>: <one line>; hypothesis; evidence path; attempts: n
## Decisions
- <iso> <decision>; rejected <alt>; undo: <how>
## Discoveries
- <iso> <what changed about the premise>; re-plan: <yes/no, link>
## Running
- <subagent name or id>: <packet>; started <iso>; maxTurns <n>
## Last written
<iso> · <one line on what just happened>
```

Compaction protocol. The skill declares, in its frontmatter, a SessionStart hook with the
`compact` matcher that prints STATE.md and the current phase's gate definition to stdout, so
they re-enter the compacted context regardless of the five-file rule. It also puts the runbook
(section 4.10) at the top of SKILL.md, because re-attachment keeps the first 5,000 tokens and
drops the rest. Before every fan-out and before any step the orchestrator expects to be long,
it rewrites STATE.md; compaction can land mid-step and the file is what survives. The
orchestrator does not suggest a new session or summarize on its own account of context length;
the run's context is managed by these rules, not by the model's unease.

The frontmatter:

```yaml
hooks:
  SessionStart:
    - matcher: "compact"
      hooks:
        - type: command
          command: "cat .drive/STATE.md 2>/dev/null; echo; echo '--- current gate ---'; grep -A12 \"^## Gate: $(sed -n 's/^turn:.*phase: \\([A-Za-z ]*\\).*/\\1/p' .drive/STATE.md | head -1)\" ${CLAUDE_SKILL_DIR}/references/gates.md 2>/dev/null | head -20"
    - matcher: "resume"
      hooks:
        - type: command
          command: "cat .drive/STATE.md 2>/dev/null; git -C \"$CLAUDE_PROJECT_DIR\" log --oneline -15 2>/dev/null"
```

Correction (see the note before section 5): this block does not work as written.
`${CLAUDE_SKILL_DIR}` is not substituted in hook commands; the `sed` expression returns the
phase with trailing text, so the gate lookup never matches; and the `resume` matcher cannot fire,
because skill hooks are registered only when the skill is invoked, which happens after a resumed
process has already started. Keep the `compact` hook, point it at a script by absolute path
under `$HOME/.claude/skills/drive/`, and make resume an invocation of `/drive` rather than a
hook. Once registered, the hook persists for the rest of the session, which is what a multi-day
run wants; `once: true` is deliberately not set.

Resume protocol. On any start where `.drive/STATE.md` exists (a resumed session, a new session
in the same project, or a compaction that lost the thread), the orchestrator, in this order:
reads STATE.md and GOAL.md; reads `git log --oneline -20` and `git status --porcelain` to find
work that happened but was not recorded; runs the project's smoke command from GOAL.md to learn
whether the tree is healthy before touching it; reconciles "Running" against `/tasks` and the
ladder against FEATURES.json; then continues from "Next". It does not re-plan, re-research or
re-decompose on resume unless a Discovery is logged. This is the harness post's recipe
(progress file, git log, smoke test, then one feature) and it costs a few hundred tokens.

Long-lived helpers. Where a subagent will be needed repeatedly across a phase (the gatekeeper
in a build wave, a browser driver in live proof), the orchestrator names it and resumes it with
`SendMessage` instead of spawning fresh, so it keeps its cache and its accumulated context.
The concurrency counter does not check resumes, so the orchestrator tracks them in "Running".

### 4.8 Progress and final reporting

Two audiences, two cadences.

For the orchestrator itself, STATE.md is the progress log and is rewritten at every phase
transition, every gate verdict, every decision and every discovery, and in any case before a
fan-out. The "Last written" line is the heartbeat.

For the owner, a one-line note in the conversation when a milestone lands: a phase exit gate
passed, a wave verified, live proof achieved, a stop condition fired. The line names the
milestone, the ladder movement and the evidence path, in plain words: "Wave 2 verified: 6 of 6
packets hold; ladder for checkout is now Local Proof; evidence in .drive/evidence/build-*.
Next: integrate and deploy." Nothing else goes to the owner mid-run; the Fable 5.1 guidance
says the model's own summaries are adequate for routine progress and over-reporting trains him
to ignore the channel.

The final report is derived, not composed. The orchestrator builds it from STATE.md,
FEATURES.json and the evidence files, so a claim in the report that has no evidence file is a
generation error the gatekeeper's last check will catch. Its shape, in this order, plain
language throughout, no rule identifiers:

```
# Drive report · <goal slug>
Stopped because: <only present on a stop; one paragraph>

## What you should look at first
<three to five lines: the live URL or the app, the one file that matters, the one risk>

## What shipped
<per feature: one line, the rung, the evidence path>

## Ladder
| feature | rung | how it was proven | evidence |

## What is not done, and why
<each non-done feature: rung, reason, the exact command or step that would finish it>

## Assumptions I made
<each: the decision, the alternative, how to undo it>

## Open failures
<each: symptom, best hypothesis, what was tried, where the reproducer lives>

## Lessons distilled
<general rules, not incident notes; each one line plus why it matters>

## How to verify this yourself
<exact commands, in order, from a clean checkout; expected outputs>

## Spend
<turns used of budget, subagents spawned, wall clock; a note if any budget was exceeded>
```

"What you should look at first" is the section the owner will actually read; it should be
written last and hardest.

### 4.9 Handling discovery

A discovery is anything that changes the premise: the bug is a design flaw, the migration has
consumers nobody listed, the feature the goal describes already exists in another form, the
external API the spec assumed does not behave as documented, requirements changed mid-run
because the owner said so. Discoveries are expected; the protocol makes them cheap.

1. Freeze the wave. Builders already running finish their current packet and commit; no new
   packets start. The orchestrator writes the discovery to STATE.md under "Discoveries" with
   the evidence path.
2. Re-classify. Does the discovery change the shape (bug became design flaw: bug hunt becomes
   feature), the size (medium becomes large), or the goal (the thing asked for is impossible or
   already exists)? Shape or size changes are decide-and-log: GOAL.md gets a dated "Re-plan"
   section with the new phase list and budget, and the run continues. A goal change is the
   single unavoidable question, asked with a default and with all independent progress
   delivered in the same turn.
3. Revise the artifacts downstream of the discovery only. A design flaw revises Spec and
   Design and re-derives the affected packets; it does not restart Recon or Research. A hidden
   consumer adds packets to the census and the parity contract. FEATURES.json entries that the
   discovery invalidates go back to "failing" with a note; they never disappear.
4. Preserve budget. A re-plan may extend the turn budget by at most 50% once per run, logged.
   Beyond that, the downgrade ladder applies.
5. Compound immediately. Every discovery is also a lesson candidate: what in Recon or Spec
   would have surfaced it earlier? The compound phase turns that into a general rule and, where
   the rule is about the skill's own process, into a proposed change to the skill's reference
   files.

Two special cases. When the same failure has resisted two distinct diagnoses, it is
automatically a discovery: the orchestrator stops fixing and starts investigating, delegating
to an Opus subagent with the two refuted hypotheses and their evidence. And when a discovery
reveals that the honest answer to the goal is "do not build this" (the migration would remove
a capability with live users, the bug is an intended behavior), the run stops with a report
that says so and offers the nearest useful goal; building the wrong thing well is not a
completion.

### 4.10 The runbook for SKILL.md

The spine below is written to sit at the top of SKILL.md, under the frontmatter, so it is what
survives re-attachment after compaction. It is 98 lines. Everything that needs more than a
sentence lives in a reference file and the spine names the file.

```
# Drive

You turn one high-level goal into finished, proven work without anyone watching. You are
operating autonomously. The user is not watching in real time and cannot answer questions
mid-task, so asking "Want me to…?" or "Shall I…?" will block the work. For reversible actions
that follow from the goal, proceed. Stop only for destructive actions, credentials, payments,
legal acceptance, or a genuine change of goal, and then ask one question, once, at the end of
a turn that also delivers every piece of progress that does not depend on the answer.

Working memory lives in `.drive/` in the project (GOAL.md, STATE.md, FEATURES.json,
LESSONS.md, evidence/). Rewrite STATE.md before every fan-out and after every gate; keep it
under 5,000 tokens. On any start where STATE.md exists: read it and GOAL.md, read
`git log --oneline -20` and `git status --porcelain`, run the smoke command from GOAL.md,
reconcile, and continue from "Next". Do not re-plan on resume unless a discovery is logged.

## 1. Intake (once)
Classify shape: greenfield app, bug hunt, feature, migration, research+website, research
only, refactor, ops. Classify size: small, medium, large, greenfield. Write GOAL.md with the
goal verbatim, shape, size, the phase list from references/phases.md, the turn and subagent
budget from references/budgets.md, and the smoke command once Recon finds it. Write the first
STATE.md and an all-failing FEATURES.json (one refutable claim per feature; expand the goal
into the full list now so a later turn cannot declare victory on a subset). Set the goal:
`/goal .drive/report.md exists with a Ladder table covering every FEATURES.json entry and my
last message quotes the gatekeeper's final verdict path; or stop after <N> turns and write a
stop report.`

## 2. Run the phases in GOAL.md's order
For each phase: check the entry gate; do the work by delegation; have the exit gate checked;
write the verdict path into STATE.md; move on. Gates and their evidence are in
references/gates.md. Never certify your own Build, Verify, Integrate, Live proof or Harden
gates: hand the claim and the artifact to the gatekeeper subagent, which has not seen your
reasoning, and accept only a verdict with an evidence file.

Recon loads the target system's own tools first (MCP verbs, CLI, API) and drives it through
them; if no verb exists for something that must happen, that is a work packet, not a
schedule. Recon lists every consumer of anything you will change.

Build runs in waves of at most 12 packets, each packet owning distinct files, each ending in
tests that try to refute its claim, a commit on main, and a fixed-size return (packet id,
rung, commit, evidence path, five lines). Keep working while builders run. A worktree used by
a builder is merged and removed inside the packet; the gate checks `git worktree list` and
`git branch --list`.

Verify: gatekeeper per packet. Refuted twice means the diagnosis is wrong: log a discovery,
investigate, do not retry a third time.

Live proof means the real environment: deployed backend, real device or simulator, real
third-party API, evidence from the system itself (URL, log, screenshot, accessibility tree).
Local-only work is Local Proof and is written as such. Ask of every test harness where it is
kinder than production, and teach it the production constraint before trusting green runs.

Harden calls the severe-testing skill on the claims in FEATURES.json, then security review,
then simplify. Findings scored 75 or higher become packets with the finding as their
refutation test; rerun Harden in full after fixes.

Compound: every open failure gets a root cause or an honest unknown; every lesson is written
as a general rule in LESSONS.md and, if it is about this skill's process, proposed as a change
to references/. Write agent memory for the gatekeeper.

## 3. Ladder
Missing, Scaffold, Partial, Local Proof, Live Proof, Operational, Done. Use these words and no
others for status. "Done" requires code, refutation tests, an independent verdict, live proof
where in scope, docs, and STATE.md, FEATURES.json and the report agreeing. Ground truth when
claims disagree: code and tests, then evidence files, then STATE.md, then prose.

## 4. Decide and log
Every reversible decision the goal does not settle: decide, record in STATE.md (decision,
rejected alternative, why, undo). Never create a list for the user to review. Never leave a
branch, worktree, or scratch file. Never report a scheduled job as done. Before a command that
changes system state, check the evidence supports that specific action.

## 5. Budget
Count your turns in STATE.md. At a phase cap, log the overrun and choose: drop features marked
"nice", narrow live proof to the critical path, accept Local Proof with a named reason, or
stop. Log every narrowing; the report lists scope the user did not get. A re-plan may extend
the budget by half, once.

## 6. Discovery
When the premise changes (design flaw, hidden consumer, changed requirement, impossible goal):
freeze the wave, log it, re-classify, revise only downstream artifacts, mark invalidated
features failing again, continue. A goal change is the one question. "Do not build this" is a
valid outcome; report it.

## 7. Stop conditions
Impossible goal; destructive action not implied by the goal; credentials, payment, legal, or
account creation; budget exhausted; the same failure after two distinct diagnoses. Do all work
that does not depend on the blocker, then write the report with "Stopped because" on top.

## 8. Report
Derive .drive/report.md from STATE.md, FEATURES.json and evidence/ using the template in
references/report.md: what to look at first, what shipped with rungs, what is not done and the
exact step that would finish it, assumptions with undo, open failures, lessons, commands to
verify from a clean checkout, spend. Plain language; no rule identifiers; never "done" for
anything below its rung. Mid-run, tell the user one line per milestone and nothing else.

Before ending any turn, read your last paragraph. If it is a plan, a question, a list of next
steps or a promise, do that work now. End the turn only when the report is written or you are
blocked on input only the user can give.
```

Reference files the spine points to, each under 300 lines:

- `references/phases.md`: the canonical table from 4.2, the collapse rules per shape, entry
  and exit gates in full.
- `references/gates.md`: one section per gate with the claim template, the preferred evidence
  in order, who checks, the failure loop and its bound.
- `references/budgets.md`: the size table, per-phase caps, the downgrade ladder, the launch
  command with `--max-turns` and `--max-budget-usd`.
- `references/state.md`: the STATE.md, GOAL.md and FEATURES.json templates and the size rules.
- `references/report.md`: the report template with a worked example of a stop report and of
  a non-done feature written honestly.
- `references/delegation.md`: the fixed-size return contracts for builders, gatekeepers,
  researchers and browser drivers; the delegation prompt skeleton (objective, output format
  and path, tools, boundaries).
- `references/definition-of-done.md`: the per-shape "done" arguments from 4.4 and the list of
  honest non-done phrasings.
- `references/anti-patterns.md`: section 7 of this report, as a checklist the gatekeeper reads.

---

**Corrections to sections 1 to 4, made when sections 5 to 9 were added.** I checked the
earlier sections against the live docs (fetched as raw Markdown on 2026-09-14) and by running
their commands. Four points were wrong or unsupported. The first two are fixed in place and
marked there; the other two change the design, so they are argued below rather than patched
into sentences.

1. Section 4.10 said the runbook spine was 118 lines. Counted between its fences, it is 98.
   Fixed in place.
2. The compaction hook in section 4.7 cannot work as written, for three independent reasons.
   `${CLAUDE_SKILL_DIR}` is substituted only "in two places: the skill's markdown content, and
   Bash rules in the `allowed-tools` frontmatter" (https://code.claude.com/docs/en/skills), so in
   a hook command it reaches the shell as an unset variable. The `sed` expression that extracts
   the phase is greedy over letters and spaces: against the STATE.md header shown in 4.7 it
   returns `Build ` with a trailing space, or `Harden   budget` when no parenthetical follows the
   phase, so the grep for the gate heading never matches. Most important, the `resume` matcher
   cannot fire in a resumed process. Skill hooks are registered "when you or Claude invoke the
   skill" (https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents), and `SessionStart`
   with source `resume` fires at launch, before anything has been invoked. The `compact` matcher
   does work once `/drive` has been invoked in the running process. The paragraph under the
   block is corrected in place; the fix is an absolute script path, a machine-readable `phase:`
   line of its own, and resume as an invocation of `/drive`.
3. Section 4.6 and step 1 of the runbook tell the orchestrator to set `/goal` at the end of
   intake. I cannot prove that impossible, but nothing documented supports it. The goal page
   describes a condition "you type"; the commands reference lists `/goal` as a built-in command;
   and the skills page says "a few built-in commands are also available through the Skill tool,
   including `/init` and `/security-review`. Other built-in commands such as `/compact` are not."
   Reports 01 and 14 reached the same conclusion independently. The loop must therefore not
   depend on a goal the model sets for itself. Sections 6 to 8 move the in-session loop to a Stop
   hook declared in the skill's frontmatter and leave `/goal` to the launch command. The runbook
   sentence should become: "If this run was launched with a goal, keep its condition provable
   from the transcript. Do not try to set a goal yourself."
4. One point in 4.6 that another report contradicts is correct as written.
   `ANTHROPIC_DEFAULT_HAIKU_MODEL` is the only documented way to move the `/goal` evaluator off
   Haiku ("To evaluate on a different model, set `ANTHROPIC_DEFAULT_HAIKU_MODEL`",
   https://code.claude.com/docs/en/goal). Report 06 recommends `CLAUDE_CODE_GOAL_GRADER_MODEL`;
   that name appears on none of the goal, environment-variable, hooks, hooks-guide, sub-agents,
   skills or model-config pages as fetched today. The installed Claude Code is 2.1.263.

## 5. Conditionals by project shape

This section adopts the taxonomy in report 02 and retires the shape names used in 4.2. The
earlier collapse rules named eight shapes (greenfield, bug hunt, feature, migration, research
plus website, research only, refactor, ops). Report 02 argues for seven shapes with variants,
three separate classification axes, and five sizes, and the control loop needs exactly that
separation: the shape fixes the phase list, the traits attach gates to phases, and the size
decides how heavy the state is and how many gatekeepers run. The mapping is direct. Greenfield
is `build`; bug hunt is `fix`; feature is `feature`; migration is `move/migration` and refactor
is `move/refactor`; research plus website is `publish`; research only is `report`. The old
"ops or incident" splits in two: a defect in a live system is `fix/incident`, and a planned
change with no defect is `operate`. The budget classes in 4.6 map onto 02's sizes as small to XS
and S, medium to M, large to L, and greenfield to XL.

I depart from 4.2 in two places and from 02 in one, and each departure needs its argument.

First, 4.2 said size changes budgets, not the phase list. Report 02 is right that size also thins
phases, and at XS removes the working directory entirely. A two-line fix that produces a
`.drive/` directory, a GOAL.md and an evidence folder is the ceremony the owner wrote this skill
to stop paying for. Nothing in the loop's central argument requires those files at XS, because
the gate at XS is a command with an exit code (a refuting test seen failing and then passing),
and a command is not self-critique.

Second, 4.2's pure-research line put Report before Compound. Compound always comes first,
because the report lists the lessons.

Third, 02 makes STATE.md the authority for the plan once intake has written it. I keep the plan
in GOAL.md instead: the verbatim goal, the classification block, the phase list, and a target
rung for every claim row. GOAL.md is written once at intake, committed, and changed only by
dated re-plan sections. STATE.md carries progress. The reason is mechanical, not taste. Silent
scope narrowing can be detected only by comparing the final state with the original ask and
the original targets, and a file the orchestrator rewrites every turn cannot be that baseline.
Report 02's classification block moves into GOAL.md without other change.

### 5.1 What every shape shares

**Target rungs are fixed at intake.** GOAL.md records, for every claim row, the rung that counts
as done and, when that target is below Live Proof, the reason: no deploy target, a device-only
capability, a prose deliverable. Lowering a target later is a downgrade that the decisions log
and the report must both show. This also settles an ambiguity in 4.4, whose table reads as if
every Done required Operational. Operational is the target only where the shape puts continued
health in scope: `operate`, `move/migration`, `fix/incident`, and any `build` whose goal says
the thing must run in production.

**From S upward, every shape runs** Intake, at least one gate verdict from someone other than
the maker before any row rises above Partial, Compound (which may be a single lesson or an
honest "nothing general"), and a report derived from evidence. At XS the orchestrator works
inline and silently: it reads the surrounding code and its tests, makes the change, runs one
test that would fail if the claim were false (red first, then green), runs the project's own
checks, and commits with the claim and the evidence in the commit body. There is no `.drive/`,
no subagent and no Stop gate, because the gate is inert where `.drive/` does not exist.

**Size decides the machinery around the phases:**

| Size | Working state | Per-packet gatekeeper | Phase gates checked by | Final auditor | Stop gate | Re-classification |
| ---- | ------------- | --------------------- | ---------------------- | ------------- | --------- | ----------------- |
| XS | commit body only | none; the refuting test is the gate | the orchestrator, by command | none | inert | on events only |
| S | short GOAL.md and STATE.md | one gatekeeper at the end, using the auditor's checklist | orchestrator; gatekeeper for the end gate | none | deterministic checks only | on events |
| M | full `.drive/` | one per packet | orchestrator for planning gates; gatekeeper for Build, Verify, Live proof | yes | deterministic checks plus the phase judge at phase changes | at every phase gate and on events |
| L | full, plus RESEARCH.md and LESSONS.md | one per packet, one per wave | as M; the Design gate's parity list by the judgment gatekeeper | yes | as M | as M |
| XL | as L, resume block rewritten at every gate | as L, with two-lens checks on the riskiest packets | as L; Spec and Design judged on `fable` | yes, plus a mid-run audit after the walking skeleton | as M | as M, plus the classification refuter at intake |

The final auditor starts at M, not at L, and this is a deliberate disagreement with report 07,
which reserves it for greenfield, migration and features with five or more claims. The auditor
is the only check on the orchestrator's own summary of the run. Report 02 places the point where
the orchestrator's context stops being a reliable memory of the plan at M. Below M the plan fits
in one head; at M and above, a Fable 5.1 auditor at a few dollars a run is the cheapest insurance
against the orchestrator believing its own narrative.

**Traits attach gates at every size** (02, section 4.3). This component decides who checks each
one. The table below is the control loop's side of that contract; the gate procedures belong to
the component reports that own them.

| Trait | Gate the loop must see pass | Checked by |
| ----- | --------------------------- | ---------- |
| `ui` | a non-maker drove the rendered result and read the screenshots and accessibility tree | UI gatekeeper (Opus) |
| `api` | contract tests pass; a request to the deployed endpoint and its response are in evidence | packet gatekeeper; live-proof gate |
| `auth` | security review with dispositions for every finding | security reviewer subagent on Opus, never inline |
| `data` | rollback rehearsed on a copy; harness-parity list names each production limit checked | judgment gatekeeper at Design; packet gatekeeper at Build |
| `async-scheduled` | a run triggered through the system's own tools during this session, with its effect observed | live-proof gate |
| `external-systems` | a live call made from the deployed runtime, not the laptop | live-proof gate |
| `native-platform` | build, launch, screenshot and accessibility inspection happened in this session | UI gatekeeper |
| `prose-content` | every factual sentence traces to a ledger row or is labelled opinion | checklist grader (Sonnet, low) |
| `deploy-infra` | undo recorded before apply; smoke observed after | live-proof gate |
| `multi-repo` | ownership map and change order exist before Build; every touched repo in the final git audit | orchestrator at Decompose; auditor |
| `public-api`, `cli`, `data` pipelines | examples run as tests; goldens; idempotent re-run is a no-op | packet gatekeeper |

Data pipelines, command-line tools and libraries are traits, not shapes (02). They change which
gates run, not the order of phases, so they need no collapse rules of their own.

### 5.2 build

**Phases that run:** Intake; Recon, limited to the owner's conventions, sibling repositories
and prior art in his own systems; Research; Spec; Design (architecture per surface, the contract
between surfaces written before either side, a design system when `ui` is present, and the test
strategy with its harness-parity list); Decompose, whose wave 0 is sequential (skeleton,
contracts, design tokens, test harness with production limits encoded); Build and Verify in
waves; Integrate; Live proof; Harden; Docs; Compound; Report.

**What collapses:** nothing at L and XL. At S (a single-file script or a small tool), Research
becomes a ledger row or two, Design becomes a paragraph in GOAL.md, and Decompose, Integrate and
Docs fold into Build.

**The one reordering.** Live proof happens twice. The first time is at the end of wave 0: one
end-to-end path through every surface, deployed and exercised against real infrastructure (for
the iOS and Cloudflare example, a single request from the app in the simulator to the deployed
Worker and back). The second is the full Live proof phase after Integrate. The walking skeleton
is the cheapest place to find out that a local harness is kinder than production. Finding that
out after three waves of packets have been verified against the kind harness means reopening
every one of them.

**Gates.** The Spec gate and the Design gate go to the judgment gatekeeper on Opus, overridden to
Fable at XL, because these documents carry the largest blast radius (06). The harness-parity list
is a blocking part of the Design gate. Packets get a gatekeeper each; waves get an integration
check of the seams; each screen gets the UI gatekeeper; each surface gets a live-proof verdict;
Harden runs severe testing on every backend claim and a security review when `auth` is present;
and the final auditor runs before Report.

**Done** means every claim row is at its target rung with a verdict file. Every surface that has a
real environment is at Live Proof or better. For the iOS and Cloudflare example that means the
app, in the simulator, exercised the deployed backend end to end, with every screen in the claim
list visited, screenshotted and inspected. The final audit says go and the git audit is clean.

### 5.3 feature

**Phases that run:** Intake; Recon as archaeology, which must end with the existing test suite run
and its result recorded, plus a list of every consumer of the code the feature will touch; Spec as
a mini-spec (claims, acceptance, non-goals); Design as a delta against what exists; Build and
Verify; Live proof when the product has a deploy target; Harden scaled to the diff; Docs as a
delta; Compound; Report.

**What collapses:** Research runs only if the feature depends on a technology or an external API
new to the codebase. Decompose and Integrate run only above three packets. There is no design
system work beyond extending the existing component library.

**Gates.** The recorded green baseline is an entry gate for Build, not a nicety: without it,
"tests pass" afterwards cannot distinguish a working feature from a suite that was already red,
or one that went red and was quietly loosened. The Verify gate includes the whole pre-existing
suite, not only the new tests. `ui` adds vision checks at desktop and phone widths. `auth`
attaches only when the diff touches identity, money or personal data.

**Done** means every new claim row is at target with evidence, and the pre-existing suite passes
with no test deleted, skipped or loosened (the auditor greps the diff for this). Live Proof is
required when the product is deployed, and the docs mention the feature where a user would look.
Report 02's trap applies here: a "fix" whose expected behaviour never existed is a feature and
gets this phase list, including the mini-spec.

### 5.4 fix, with the incident and performance variants

**Phases that run:** Intake; Recon narrowed to the failing path, its tests and its recent history;
Reproduce; Diagnose, run as a hypothesis ledger; Fix, a single packet with no parallel writers;
Verify, which includes the blast radius (callers, and the same pattern elsewhere); Compound, which
is mandatory; Report.

**What collapses:** Spec becomes the root-cause claim. Research, Design, Decompose, Integrate and
Docs are skipped unless the cause is third-party behaviour (one ledger row) or the fix changes a
contract (then a decision record and a docs line). Harden becomes a review of the diff scaled to
its size, plus a severe test on the claim when the fix touches `auth`, `data` or `concurrency`.
Live proof runs only when the bug was observed in a live system.

**Gates.** A reproducer seen failing in this session is the entry gate for Fix. When reproduction
fails within the phase's budget, the run does not guess. It stops with a report that lists what was
tried, the conditions under which the failure was reported, and what would make it reproducible,
because a fix without a reproducer can never rise above Partial, and shipping one as if it could
is the mirage this shape is most prone to. At M and above, the Diagnose gate goes to the judgment
gatekeeper with one question, "is this the cause or a symptom?". At S the packet gatekeeper's
two-direction check covers it. The Verify gatekeeper runs the reproducer against the pre-fix commit
and the post-fix commit. The pre-fix run happens in a detached worktree under `/private/tmp`, which
the gatekeeper removes before returning. Two refuted fixes make a discovery, per 4.3.

Report 06 observes that on a single dependent chain an orchestrator buys little over a single
model. The control loop's answer is to keep the orchestrator's turns few: it delegates the whole
hunt to one investigator subagent that owns the hypothesis ledger, rather than narrating hypotheses
itself, and it steps in at the gates.

**`fix/incident`** inserts Mitigate before Reproduce, with the undo recorded before the mitigation
runs, and makes Live proof mandatory. Its target is Operational: done requires the real fix
live-proven, the mitigation removed afterwards, and an alert or smoke check that would catch a
recurrence, itself triggered once during the run.

**`fix/perf`** makes Reproduce a baseline measurement taken by a script on a named path, and Verify
a re-measurement by the same script. Done requires both numbers in evidence from the same script,
and the benchmark kept as a regression guard with a budget.

**Done** for a plain fix follows 4.4: a regression test that the gatekeeper saw fail before the fix
and pass after it, the root cause written as a paragraph, the fix committed to main, the blast
radius checked, and, if the bug was live, the live system shown through its own tools to no longer
exhibit it.

### 5.5 move: migration, refactor and upgrade

**Phases that run:** Intake, where a borderline size rounds up (02); Recon expanded into a
consumer census and, across repositories, an ownership map with the order of changes; Research
into the target platform and, for upgrades, the migration guide and changelog; Spec as a parity
contract, meaning characterization tests at the boundary that pass against the *old* path; Design
as a cutover plan with an undo per step; Decompose into strangler steps; Build and Verify per step;
Integrate with dual-run and comparison; Live proof; Harden with failure injection, a rollback
rehearsal and a blocking harness-parity review; Docs as a runbook; Compound; Report.

**Gates.** Characterization passing on the old path is the entry gate for Build. Tests written
against the new code only pin whatever the new code happens to do, which is precisely what a move
must not be allowed to define. The Verify gate is two-lens, as report 07 argues: a parity check and
a separate operability-and-rollback check, and both must pass. The rule that no new behaviour
enters a move is enforced at the gate. A packet whose diff changes observable behaviour beyond the
parity contract is refuted however good the change is, and the desired behaviour becomes a
`feature` sub-goal after cutover.

**`move/migration`, done:** every consumer in the census is served by the new path with parity
evidence. The old path is disabled, not merely unreferenced, and the disabling is committed. Real
traffic has flowed through the new path, with a log or metric to show it, and the rollback has been
exercised once. The target is Operational. A soak window is the one legitimate scheduled check in
this whole design (report 14): the run ends with the soak row honestly at Live Proof and a scheduled
check that promotes it with evidence. That does not break "never wait on a scheduler". The run does
not wait and does not report the soak as done, and a soak has no triggering signal, which is exactly
the owner's stated exception.

**`move/refactor`, done:** the cutover collapses into commits. Test output before and after is
identical apart from timing noise, public interfaces are unchanged, and no existing test was
modified. Live proof runs only if the refactored code is deployed.

**`move/upgrade`, done:** characterization is the existing build, suite and a runtime or simulator
smoke on the old toolchain. Done is the same three on the new toolchain, with the smoke screenshots
compared by the UI gatekeeper.

### 5.6 publish

**Phases that run:** Intake; Research by source lane into a ledger, which for a market-position
request is itself a deliverable and is gated like a `report` before anything is designed; Spec as a
content plan and information architecture; Design as direction and tokens; Decompose by section when
there are more than three; Build, covering both site construction and drafting under the `writing`
skill; Verify; Live proof; Compound; Report.

**What collapses:** Docs folds into Build, because the site is the documentation; the repository only
needs a note on how to build and deploy. Integrate folds into Verify. Harden is skipped unless the site
collects data, in which case `api` and `auth` gates attach.

**Gates.** Verify has four independent parts: claim-to-source matching by the checklist grader; the UI
gatekeeper at three widths and in dark mode; Lighthouse and accessibility against the thresholds GOAL.md
set at intake; and link and spelling checks. Live proof repeats the UI gatekeeper and Lighthouse against
the deployed URL. A pass on localhost says nothing about the CDN, redirects, fonts or the production build.

**Done** follows 4.4's website definition, with two shape-specific checks the auditor must run. Every
factual sentence on the site traces to a ledger row or is marked opinion, and no placeholder content
remains (lorem ipsum, "TBD", invented team biographies, sample blog posts). Fabricated team facts are
the characteristic mirage of this shape: the page renders, every gate on layout passes, and the content
is fiction.

### 5.7 report

**Phases that run:** Intake; Research (decomposition, source lanes, and a cross-check lane that hunts
contradictions); Build as synthesis and an editorial pass; Verify; Compound, only when the research
process itself taught something; Report, which for this shape is a short delivery note pointing at the
deliverable rather than a second copy of it.

**What collapses:** Spec becomes the list of questions in GOAL.md. Recon, Design, Decompose, Integrate,
Live proof, Harden and Docs are skipped. At S there is no STATE.md; the ledger is the state (02), and
there is no Stop gate.

**The ladder for prose.** Live Proof is out of scope and is recorded as such at intake. Each row is a
question. A row is Partial when drafted, and Local Proof when every claim is labelled verified, source
claim or opinion, every citation resolves (checked by the grader, not asserted), and the contradictions
are listed. It is Done when an adversarial reader on Opus has tried to refute the central claims, each
refutation has a disposition, and the gatekeeper has spot-checked three claims against their sources.

**Done** follows 4.4, with one addition from 02: claims the run could not verify are listed as
unverified, not dropped. Quietly omitting what could not be checked is narrowing by another name.

### 5.8 operate

**Phases that run:** Intake, where size rounds up; Recon, which loads the target system's own verbs
(MCP tools, CLI, API) before anything else and reads the runbook and the current state through them;
Spec as a step plan in GOAL.md with an undo recorded for every step; Live proof per step; Compound;
Report.

**What collapses:** Research, Design, Decompose, Build, Verify as a code gate, Integrate, Harden and
Docs are all skipped. If a script has to be written, it becomes a small Build packet with its own
test, because a script that changes a live system is code.

**Gates.** For each step there are two gates. Before it runs, a filled undo field in GOAL.md, checked
deterministically. After it runs, an observation gate: a gatekeeper, or the checklist grader for a
simple read, queries the system through its own read verbs and confirms the effect independently of
the command that caused it. A command's exit code is never the evidence here, because deploys, key
rotations and cutovers are exactly the operations that succeed at the command line and fail in effect.
A step that is destructive and not implied by the goal is a stop condition (4.5), not a gate.

**Done** means every step's effect has been observed live and recorded. When the goal includes staying
healthy, the target is Operational, which requires a smoke check or alarm that exists and was triggered
once during the run.

### 5.9 Mixed prompts and shape changes mid-run

A prompt that carries two shapes becomes ordered sub-goals (02): fixes before the features that sit on
the fixed path, moves before the features that depend on the new home. They share one GOAL.md with a
section per sub-goal and one STATUS file, and each has its own commits and gates. The final auditor runs
once, over all sub-goals, because interactions between them are where a mixed run hides its gaps. When
re-classification changes a shape mid-run, the re-plan protocol in 4.9 applies. Target rungs carry
forward, evidence is never discarded, and the new phase list starts from the current phase, not from
Intake.

## 6. Model and effort assignment

This component owns the orchestrator and every role that decides whether the loop may move on: the
gatekeepers, the phase judge inside the Stop gate, the final auditor, and the investigator that a
discovery summons. Makers belong to other components and appear here only where a gate's model has
to be at least as strong as the maker's. The aliases today resolve to Fable 5.1 (`fable`), Opus 5
(`opus`) and Sonnet 5 (`sonnet`) (section 3.7 and report 06). Haiku is used nowhere, including the
`/goal` evaluator.

### 6.1 The mechanics that constrain the choices

The Agent tool has no effort parameter. That is verified from the tool definition available in this
session, whose parameters are `subagent_type`, `prompt`, `model`, `run_in_background`, `isolation` and
`description`, and report 06 observed the same on 2.1.266. Effort for a subagent is therefore set only
in the agent's frontmatter ("Overrides the session effort level. Default: inherits from session",
https://code.claude.com/docs/en/sub-agents). A per-invocation `model` overrides the frontmatter model,
so a role that needs two models at the same effort needs one file plus a `model` on the call, while a
role that needs two efforts needs two files. The Workflow tool's `agent()` does accept effort per
call (06), which matters only for read-only fan-outs.

"Inherit" is not a safe default. The owner's settings set Fable 5.1 to `medium` effort (06, read from
his `settings.json`), so a gatekeeper or orchestrator that inherits runs at medium without anyone
having chosen it. Every role below names its effort explicitly.

### 6.2 Assignments

| Role | Model | Effort | Tools | Isolation | Where it is defined |
| ---- | ----- | ------ | ----- | --------- | ------------------- |
| Orchestrator | fable | high | full, minus `AskUserQuestion`; reads only its state and verdict files | main conversation, never a fork | SKILL.md frontmatter `model: fable`, `effort: high`, repeated as `--model fable --effort high` in the launch command |
| Classification refuter (L and XL, or low-confidence intake) | opus | high | Read, Grep, Glob, Bash | none | inline call to the judgment gatekeeper with a refuting brief (02) |
| Checklist grader: citations, docs commands, state consistency, git audit, claim-to-source | sonnet | low | Read, Grep, Glob, Bash for named check commands only | none | `drive-grader` (06, 07) |
| Judgment gatekeeper: Spec gate, Design gate and its harness-parity list, root cause, reports' synthesis | opus; `model: fable` on the call for XL `build` and for `move` | high | Read, Grep, Glob, Bash, WebFetch | none | `drive-judge` (06) |
| Packet gatekeeper: Build, Verify, Integrate, Live proof, and the operate observation gate | opus | high | Read, Grep, Glob, Bash; Write under `.drive/evidence/` only | none; never its own worktree | `drive-gatekeeper`, drafted below |
| UI gatekeeper | opus | high | as the packet gatekeeper, plus simulator and browser MCP tools | none; foreground when a tool is bound to the session's pane | `drive-ui-verifier` (07, 09) |
| Severe tester and security reviewer (Harden) | opus | xhigh | per 06 and 15; sanitized reports | per 06 | `drive-severe-tester`, `drive-security-reviewer` |
| Discovery investigator | opus | xhigh | Read, Grep, Glob, Bash; temporary detached worktrees under `/private/tmp`, removed before return | none | `drive-investigator` (06, 11) |
| Final auditor and tie-breaker | fable | xhigh | Read, Grep, Glob, Bash; Write for its own verdict file only | none | `drive-auditor`, drafted below |
| Phase judge inside the Stop gate | `claude-sonnet-5` in a nested non-interactive call | low | none; files are handed in | none | the gate script (14) |
| `/goal` evaluator, when the launch sets a goal | Sonnet, via `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5` scoped to the launch process | not applicable | none; transcript only | none | launch command |
| Distiller (Compound) | fable | high | read-only; returns lessons, the orchestrator writes them | none | `drive-distiller` (10) |

### 6.3 The arguments behind the table

**The orchestrator runs at high, not xhigh, on every shape.** Reports 06 and 12 put a greenfield or
migration orchestrator at xhigh, and I disagree. The decisions that deserve xhigh in those shapes are
the spec, the architecture, the cutover plan and the root cause, and every one of them is a one-shot
judgment this design delegates to an agent defined at xhigh, or to the judgment gatekeeper overridden
to Fable. What remains in the orchestrator's own turns is routing, bookkeeping and reading verdicts.
That is the kind of routine work where the Fable 5.1 guidance says higher effort "can gather context
and deliberate beyond what the task needs." Fable 5.1 keeps its prompt cache across effort changes
(06), so an owner who disagrees can raise it at launch without paying a cache rebuild. Effort is set in
two places because skill frontmatter overrides the session for the invoking turn (3.7), and a loop
kept alive by a Stop hook should not depend on whether a continuation counts as that turn. The
orchestrator writes `${CLAUDE_EFFORT}` into STATE.md at intake and on every resume, and the auditor
flags a run whose orchestrator actually ran at medium.

**Gatekeepers are at least as strong as the makers they judge.** Report 07's parity argument holds:
a verifier weaker than the maker defaults to approval, and Rajasekaran's finding that a separate
evaluator still "talked itself into" approving real issues makes weakness worse, not safer. Packets
built by Sonnet or Opus are judged by Opus. Sonnet at low effort is confined to checklists (binary
assertions against evidence), and a checklist verdict is never promoted to a judgment. The loop
enforces this through names rather than good intentions. The gate table in `references/gates.md` names
the agent for each gate, not a model, so an orchestrator economizing late in a run cannot pass a
correctness gate to the grader.

**The packet gatekeeper is not Fable.** Count invocations, as 06 does: a greenfield run has thirty to
forty packets and about one and a half verification rounds each, so a 2x premium compounds into real
money. Where Opus and the maker disagree twice on the same artifact, the tie goes to the Fable auditor,
once.

**The auditor is Fable because it audits Fable.** The final auditor reads a report and a state history
written by a Fable orchestrator. A weaker model reading a confident, well-organized narrative from a
stronger one is the rubber-stamp asymmetry again, in the direction that matters most. It runs once per
run from M upward, plus tie-breaks. It is input-heavy and output-light, so its absolute cost is a few
dollars (06, section 4.4).

**Classifier exposure stays out of the orchestrator's context.** In Claude Code, after a classifier
fallback "the session continues on the fallback model" (06, verified). Every gate that reads security
material (Harden's security review, severe tests on `auth`, an incident investigation that touches an
attack) runs in an Opus subagent that returns a sanitized verdict. The orchestrator never pastes
findings, payloads or encoded blobs into its own turns. `PostModelSwitch` exists as a hook event
(https://code.claude.com/docs/en/hooks) and should append any switch to STATE.md, and every gatekeeper
reports the model named in its own system prompt so the auditor can detect a demoted role.

**Every gatekeeper is predefined.** Two properties require a file: explicit effort, and a restricted
tool set with no Agent tool (which also keeps gatekeepers from nesting). Only the classification refuter
can be an inline call, because it reuses the judgment gatekeeper's definition. Whether the files ship in
a skills-directory plugin (01) or in `~/.claude/agents/` (06, 07) is the coordinator's packaging decision.
The frontmatter below works in either.

**No gatekeeper gets `memory:`.** Section 4.10's runbook says to write agent memory for the gatekeeper,
and report 01 gives its verifier `memory: user`. I now recommend against both. Agent memory is a second
lessons store that the owner does not version, and it injects conclusions from other projects into a
role whose value is having no priors about this artifact. Lessons about gates belong in the skill's
`references/` files, where the distiller writes them and the gatekeeper's brief can point at the relevant
section.

### 6.4 Draft: `drive-gatekeeper`

This role is report 07's `drive-verifier` under another name, and the coordinator should keep one file.
The draft exists because the control loop needs three things 07's text does not state. The gatekeeper
writes its own verdict file, so the orchestrator never transcribes one. A verdict that rests only on
reading code caps the rung at Partial. And the gate checks the loop's hygiene conditions (scope, stubs,
worktrees) on every pass. The verdict schema is 07's JSON; 13's six-line Markdown form in 4.3 names the
same fields and should be dropped in its favour (section 8.3).

The two hook scripts are named, not written; they belong to the harness component. The first refuses any
Write outside `.drive/evidence/`. The second, which subagent frontmatter converts to `SubagentStop`,
refuses to let the gatekeeper finish until the verdict file exists, parses, and contains at least one
command it ran. Hooks in subagent frontmatter are subject to workspace trust for project-level agent files
(https://code.claude.com/docs/en/hooks). Check the exempt scopes at install.

```markdown
---
name: drive-gatekeeper
description: Independent gate check for a /drive run. Reads a handoff naming a claim, a scope and the checks, runs the checks itself, tries to refute the claim, and writes one verdict file. Never sees the maker's reasoning and never edits the project.
model: opus
effort: high
tools: Read, Grep, Glob, Bash, Write
disallowedTools: Edit, NotebookEdit, Agent
maxTurns: 60
color: red
hooks:
  PreToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/scripts/evidence-only-write"
  Stop:
    - hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/scripts/verdict-complete"
---

You decide whether one gate in an autonomous run may pass. You did not do the work, you have
not seen how it was done, and nothing you are told about it counts as evidence.

Read the handoff file named in your task. It gives the claim, the scope (a commit range or a
path), the checks to run, the rung the claim is aiming for, the verdict schema, and the path for
your verdict file. Read nothing it does not point to, apart from the code in scope and its tests.

Work in this order. Run every check in the handoff yourself and keep each exit code and the last
lines of output. Then try to refute the claim: pick the input, ordering, boundary or failure most
likely to break it and run that as well, using a throwaway test under /private/tmp if you need
one. For every stub, fake, mock, in-memory store or local emulator the checks depend on, write
down where it is kinder than the production system and whether the claim would still hold against
the real one. If the target rung is Live Proof or higher, at least one check must exercise the real
environment (the deployed URL, the app in the simulator against the deployed backend, the real
third-party API) and you must capture its response. If you need an earlier commit, check it out as a
detached worktree under /private/tmp and remove it before you finish.

On every gate, also check: no test in scope was deleted, skipped or loosened; every changed file is
inside the scope; nothing behind the claim is a stub or placeholder; `git worktree list` shows only
the main checkout.

The verdict. "holds" requires the checks to have run green, your refutation to have failed, and no
blocking harness entry. "refuted" means something you ran contradicts the claim. "unverifiable"
means you could not run what the claim needs; name exactly what was missing. If the only evidence
is reading code, the rung you report is at most Partial, whatever the claim says. When you are
unsure, the claim does not hold.

Write exactly one file, at the verdict path, in the schema from the handoff, and write nothing
anywhere else. Your final message is four lines: the verdict, the rung the evidence supports, the
verdict path, and the model name stated in your system prompt. Do not praise the work, summarise
it, or suggest improvements beyond the gaps recorded in the file.
```

### 6.5 Draft: `drive-auditor`

Reports 06 and 07 each draft an auditor. This one adds the checks only the control loop can specify:
scope integrity against the intake commit, the tense of the report, and the reconciliation of stops,
downgrades and discoveries with what the report admits. The coordinator should merge the three into one
file and keep these checks.

```markdown
---
name: drive-auditor
description: Final audit of a /drive run before it may be reported done, and tie-breaker when a gatekeeper and a maker disagree twice. Checks evidence, the ladder, the repository, and whether the delivered scope matches the goal as first written. Read-only apart from its own verdict file.
model: fable
effort: xhigh
tools: Read, Grep, Glob, Bash, Write
disallowedTools: Edit, NotebookEdit, Agent
maxTurns: 100
color: cyan
hooks:
  PreToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/scripts/evidence-only-write"
---

You decide whether this run is finished, and you begin by assuming it is not. You audit the run,
not only the code: its scope, its evidence, its ladder, its repository and its report draft.

Ground truth, strongest first: the working tree and its tests; verdict and proof files; the
status file; STATE.md; prose, including the report draft. Where two disagree, the stronger wins
and the disagreement is a finding.

Scope first. Read GOAL.md as it was committed at intake (its header names the commit; use
git show) and compare its goal, its claim rows and their target rungs with the current status
file. Every row that disappeared, every target that was lowered and every claim reworded into an
easier one needs a dated decision in STATE.md and a line under "What is not done" in the report.
Narrowing that lacks either is a blocking finding, however good the remaining work is. Note work
the goal did not ask for.

Then evidence. For every row at Local Proof or above, open its verdict file. It must record
commands actually run with their exit codes, a refutation attempt and a harness note. Re-run the
cheapest check for every Live Proof row, and for at least three other rows you judge most at
risk. A Live Proof row with no response from the real environment is blocking. A row whose only
evidence is reading code cannot stand above Partial. Search the code behind Done rows for stubs,
placeholders and skipped tests.

Then the repository: a clean tree, HEAD on main, a single worktree, no branches created by the
run, no scratch files committed.

Then the report draft. Every statement under "What shipped" and every row of the ladder table
must point at evidence that exists. A statement there in the future or conditional tense is a
plan presented as a result, and is blocking. Every stop condition, downgrade, discovery and
assumption recorded in STATE.md must appear in the report.

For a tie-break, read the claim, both verdicts and the maker's dispute, re-run what you need, and
rule "defect", "not a defect" or "ambiguous". Ambiguous resolves to the stricter reading.

Write one verdict file at the path in your task: go or no-go; each finding with its severity
(blocks done, lowers a rung, note), file and line; and, for each row, the highest rung the
evidence supports. Your final message is go or no-go, the number of blocking findings, the
verdict path, and the model name stated in your system prompt. Do not fix anything.
```

## 7. Failure modes and anti-patterns

A control loop fails in one of two directions. It stops early and calls the partial result complete,
or it grinds on under ceremony that no longer pays. The first direction is the owner's mirage, and most
of this section is about it. Each entry names what the failure looks like, why this loop in particular
is prone to it, and the mechanism that prevents it. The mechanisms come in six layers, and the closing
table says which layer carries each one:

1. the SKILL.md spine text;
2. the Stop gate declared in the skill's frontmatter, which runs deterministic checks every turn and
   the Sonnet phase judge at phase changes;
3. the gatekeeper and the validity rules its verdicts must meet;
4. the lint over the status file and evidence pointers (report 10);
5. the final auditor;
6. GOAL.md, committed once at intake, as the baseline everything is compared against.

### 7.1 Routes to mirage completion

**Self-certification.** The orchestrator judges its own Build, Verify or Live proof gate because the
gatekeeper feels like overhead late in a run, or because it "already saw the tests pass" in a builder's
return. This is the self-critique the Fable 5 guidance warns against, disguised as efficiency. The spine
forbids it. The status lint refuses any row above Partial whose evidence pointer is not a verdict file
under `.drive/evidence/`. The gatekeeper's `SubagentStop` hook guarantees that such a file exists only
when a gatekeeper actually ran.

**Declaring done at Scaffold.** Routes exist, views compile, the README describes the feature, the
types are right, and the orchestrator reads that as progress close enough to done. This is the most
common mirage for a greenfield run, because scaffolds are cheap and look complete in a diff summary.
The ladder vocabulary is mandatory, and Scaffold is a legitimate rung where scaffolds stay. No row rises
above Partial without a verdict whose checks exercised the behaviour. A verdict that rests on reading code
caps at Partial. The gatekeeper checks for stubs behind the claim on every gate, and the auditor searches
the code behind every Done row for placeholders and unimplemented paths.

**The evidence-free verdict.** A gatekeeper returns "holds" after reading a diff and a builder's summary,
without running anything. Separation alone does not stop this: Rajasekaran observed separate evaluators
approving work they had just criticised (07). The verdict schema makes such a pass malformed: `ran` must
be non-empty, every claim needs a refutation attempt, and the gatekeeper's stop hook will not let it
finish without a command in the file. The orchestrator rejects a malformed verdict and spawns a fresh
gatekeeper once. The prompt's default is that uncertain means refuted.

**Leaked reasoning.** The gatekeeper is fresh, but the orchestrator's handoff says "the builder fixed the
race by adding a lock; please confirm." Independence is then gone through the one channel nobody watches.
The handoff is built from files by template (07's handoff contract): claim, scope, checks, target rung,
schema, verdict path. It never contains a paraphrase of any agent's report, and the spine says so in one
sentence.

**Transcribed evidence.** The orchestrator writes the evidence file from what a gatekeeper told it. Every
transcription is a chance to round "holds with a caveat" up to "holds." The gatekeeper writes its own
verdict file, and the orchestrator reads only three fields. This is why section 6 gives the gatekeeper a
Write tool fenced to `.drive/evidence/`, despite report 10's single-writer rule (argued in 8.4).

**The kinder harness.** Green tests against a stand-in that permits what production forbids: the owner's
sql.js shim with no bind-variable limit, which passed 24 runs and failed live. The loop is prone to this
because every gate before Live proof runs locally. The harness-parity list is a blocking part of the Design
gate, judged by Opus. Every verdict carries a `harness_kindness` field. `build` reorders a walking-skeleton
Live proof to the end of wave 0 so the first real-environment check comes before breadth, not after.

**Local labelled live.** A row reaches Live Proof because the deploy command exited zero, or because the
app ran in the simulator against a mock. The lint refuses Live Proof unless the verdict's `ran` includes a
real-environment command with a captured response. The gatekeeper's prompt states the requirement, and the
auditor re-runs the cheapest check for every Live Proof row.

**Command exit taken as effect.** An `operate` step or a deploy "succeeded" because the CLI said so. The
observation gate in 5.8 has a different agent query the system's own read verbs after the step, and the
spine says a command's exit code is never the evidence for a change to a live system.

**The goal judged on claims.** A `/goal` evaluator reads "all 41 tests pass" in the orchestrator's last
message and returns met. The evaluator has no tools (3.1). This design does not rely on `/goal` for
judgment. The Stop gate runs its deterministic checks on files, and a goal condition, when the launch sets
one, is phrased as "the auditor's verdict path is quoted and the file says go." A small model can check
that from the transcript, and a lie would be caught by the files anyway.

**Exhaustion labelled success.** After the second refuted fix, or at the turn cap, the orchestrator writes
"done, with minor issues." Loops tend to end where the budget ends, and a report written in that moment
reaches for the kindest words. At a bound, the rung stays whatever the last verdict supports. The report
opens with "Stopped because". Done is unreachable without a go from the auditor, and the auditor blocks on
any Done row below its verdict.

**Weakened tests.** The quickest way to green is to skip, loosen or delete the test that fails. Every
gatekeeper checks for this on every gate, whatever the rubric says; the auditor greps the run's diff for
skip markers and loosened assertions; and for `feature` and `move/refactor` the pre-existing suite must pass
unchanged.

**"Unverifiable" as an escape hatch.** A hard check is marked unverifiable ("needs credentials", "needs a
device") and the row silently settles at a higher rung than the evidence supports. The rung stays at what
was proven. The report lists the row with the exact missing input and the step that would supply it. The
auditor holds "blocked" and "impossible" to the same evidence bar as "works" (12): it checks whether the
credential really is absent from the environment, or the tool really cannot be loaded.

**Scheduled work reported as done.** "The cron will pick it up at 02:00." The spine forbids it. A scheduled
check is a status row at its honest rung until its own evidence arrives, and the only legitimate schedule
is a soak window with no triggering signal (5.5).

**Reports that restate plans as results.** The report is written from the plan and the orchestrator's
memory of intent: "the dashboard displays weekly totals, refreshes every five minutes and handles empty
states," when only the first was built and none were verified. The loop is prone to this because the
orchestrator wrote the plan and reads it more often than the evidence. The report is derived from the
status file, the verdict files and STATE.md, never composed from GOAL.md. The lint requires every row in
the report's ladder table to carry an evidence path that exists. The auditor treats future or conditional
tense under "What shipped" as blocking, and cross-checks every stop, downgrade and discovery in STATE.md
against the report.

**The compaction summary taken as truth.** After compaction the summary says "wave 2 verified," while the
status file shows two packets refuted. The `compact` hook re-injects STATE.md, the resume protocol reads
files before acting, and the spine's precedence rule puts code, tests and evidence above any prose,
including the summary.

**The wrong thing, built well.** A discovery that should have stopped the run (the migration removes a
capability with live users; the "bug" is intended behaviour) is swallowed, and a correct implementation of
the wrong goal passes every gate. Every gate is local to a packet, and no packet gate asks whether the goal
still makes sense. Discovery is a standing trigger in the spine, "do not build this" is a valid outcome, and
the auditor's first check is the scope comparison against the intake commit, which includes work the goal
did not ask for.

**Silent demotion.** A classifier flag moves the orchestrator, or the auditor, to Opus 4.8 mid-run, and
Fable-tier verdicts quietly become Opus-tier ones. The `PostModelSwitch` hook logs the switch into STATE.md,
every gatekeeper reports its model, and security material stays in Opus subagents (6.3).

### 7.2 Autonomy failures

**Asking permission for reversible actions.** "Shall I deploy to staging?" "Want me to run the migration on
the test database?" Each question ends the turn; with nobody watching, the run stops for hours, and in a
`-p` run it stops for good. The spine carries the Fable 5.1 autonomy sentence verbatim, and reversible
actions implied by the goal are simply taken and logged with their undo. `disallowed-tools: AskUserQuestion`
removes the tool while the skill is active; its restriction "clears when you send your next message", which
in an unattended run never happens. The Stop gate treats a final message that matches the permission-asking
pattern, with no "Blocked on" entry from the allowed categories in STATE.md, as a block whose reason is
"decide, log the decision and its undo, and continue."

**The question mirage.** Asking a question and counting it as progress, or asking a second one. The
unavoidable question has a strict test (4.5). It arrives in the same turn as every piece of progress that
does not depend on it, with the default the orchestrator will take. Two questions in one run is recorded as
a defect of intake, not a normal event.

**The approval queue in disguise.** The report ends with "twelve findings for you to triage" or "please
confirm each of these migrations." The owner will never process it, so none of it happens. Findings at or
above the severity threshold become packets and are fixed. Those below it are recorded with a decision, and
the report may contain one question at most.

**Ending the turn on a plan.** The last paragraph lists next steps, or promises to "now run the integration
tests." The spine's final instruction makes the orchestrator read its last paragraph and do that work now,
and the Stop gate blocks while STATE.md shows a Next action and no stop condition.

**Overreach in the other direction.** Acting on a destructive step the goal does not imply (dropping a
table, force-pushing, deleting a live resource, messaging real users) because "autonomous" was read as
"unconstrained". Destructive actions not implied by the goal are a stop condition. The orchestrator checks
that the evidence supports that specific action, not a pattern that resembles one (4.5).

### 7.3 Scope failures

**Silent scope narrowing.** Facing a hard claim, the run rewords it into an easier one, drops a status row,
or lowers a target from Live Proof to Local Proof, and reports success against the smaller goal. This is the
most dangerous failure in the section, because every gate then passes honestly. GOAL.md and the status rows
are committed at intake, and the intake commit is named in GOAL.md's header. Status rows are never deleted,
only moved to a dropped section with a reason, and the lint's row-retention check compares against HEAD
(10). Every downgrade needs a dated decision. The auditor diffs the intake commit against the final state,
and the report's "What is not done" is generated from that diff, not from the orchestrator's recollection.

**Silent widening and swapping.** Unrequested fixes to neighbouring code, extra features "while I was
there", or a different and easier deliverable that satisfies the goal's words. The Fable 5.1 guidance says
this scope discipline costs no measurable task success. Makers report follow-ups instead of doing them. The
gatekeeper treats changed files outside the packet's scope as a finding, and the auditor lists work the goal
did not ask for.

**Reinterpreting the goal by editing it.** GOAL.md is rewritten mid-run so that the new text matches what
was built. GOAL.md changes only by appending a dated re-plan section, and the auditor reads the intake
commit's version.

### 7.4 Ceremony failures

**Phase theater.** Every phase in the canonical table runs because it is in the table. The Research phase of
a config fix produces a ledger nobody reads, and a Docs gate checks that a file exists. Ceremony that does
not change the result costs the owner time and teaches him to skip the skill. Intake derives the phase list
from shape, traits and size (section 5), and every phase written into GOAL.md must name its artifact and the
later gate or packet that reads it. A phase whose artifact has no reader is deleted at intake. The auditor
spot-checks that the artifacts produced were cited by later handoffs.

**Trait inflation and gate fatigue.** Everything is marked `auth` and `data`, every packet gets three
reviews, and the run spends most of its budget on gates that find nothing. The trait thresholds in 02
decide, and a suspected trait whose gate archaeology refutes is removed and logged. Gate counts per size
follow the table in 5.1.

**Re-planning on resume.** A resumed session re-researches, re-decomposes and drifts from the recorded plan.
The resume protocol continues from STATE.md's Next action and forbids re-planning unless a discovery was
logged.

**Discovery thrash.** Every wave surfaces something that triggers a re-plan, and the run never converges.
Section 4.9 allows one budget extension per run. I add a stop condition: a third re-plan that changes shape
or goal ends the run with a report. A premise that keeps moving means intake misread the goal, and more
building on a moving premise is waste.

### 7.5 Loop and budget failures

**The third retry.** A refuted packet is sent back to the builder a third, fourth and fifth time with
slightly different instructions. Two refutations make a discovery (4.3), and the investigator starts from
the two refuted diagnoses.

**The Stop gate as a trap, or as a leak.** A gate that blocks on a condition the model cannot meet spends
eight consecutive turns and is then overridden by the harness (3.5), ending the run with no report. A gate
too loose lets the run end with stale state. Every block reason names the exact fix. STATE.md's status line
has `stopped` and `blocked` values that release the gate, but only when a stop report exists and "Blocked on"
names an allowed category. A stall counter marks the run stalled after several turns in which STATE.md did
not change (01). The block cap is not raised.

**A turn counter the model keeps for itself.** Section 4.6 has the orchestrator increment `turn:` in STATE.md.
A model under pressure forgets to, or rounds. The Stop gate counts turns deterministically, since every turn
end is a Stop event, and writes the count to a file under `.drive/`. The orchestrator reads the count and does
not maintain it.

**Budget exhaustion with no report.** The run hits `--max-budget-usd` or the turn bound mid-wave and exits.
The report is the phase with a floor, not a cap (4.6). At 90 percent of the turn bound the Stop gate's block
reason becomes "write the stop report now". In a `-p` run, a dollar cap below the planned envelope is chosen
so that the report fits under it.

**Waiting badly.** In a `-p` run the orchestrator ends its turn while a wave of background builders runs, and
learns of a stuck builder only at the next turn end (3.1). The orchestrator keeps working on anything
independent while builders run, reads completion notifications as they arrive, and bounds every builder with
`maxTurns`.

### 7.6 Repository hygiene failures

**Leaving branches and worktrees.** A changed subagent worktree is never merged back by the harness and
survives until a sweep that keeps anything with unpushed commits (12). The run ends with work hidden in
`.claude/worktrees/`. The shared tree with file ownership is the default (12). A worktree used in a packet
is merged and removed inside that packet. The integrator's audit (one worktree, no run-created branches,
clean status) runs at every wave end, the Stop gate repeats it before the run may end, and the auditor
repeats it before go.

**Makers committing in a shared tree.** A builder's `git add` sweeps a sibling's half-finished edits into
its commit. Report 12 documents this three times in the owner's history. Section 4.2 said each packet ends
in a commit on main made by the builder, and I concede that point to 12: builders never touch git, and the
integrator (or the orchestrator at M and below) commits per packet, staging explicit paths.

**Verifying an uncommitted tree.** The gatekeeper passes a state that changes before it is committed. The
order is always wiring, gates, commit, audit, and then verification (12).

**Scratch files committed.** Probe scripts, screenshots and logs land in the tree. Scratch lives under
`/private/tmp` or `.drive/local/` (gitignored), and the git audit's clean-status check catches the rest.

### 7.7 Context failures

**The orchestrator doing volume work.** It reads source, runs suites, looks at screenshots, and compacts
twice before wave 2. Section 4.7's rules apply: summaries in, files out, fixed-size returns, and no test run
or screenshot in the orchestrator's context.

**STATE.md over the re-read limit.** A file over 5,000 tokens comes back after compaction as a bare path
(3.2). The file is rewritten, not appended, and the lint fails a STATE.md over budget.

**The skill evicted from re-attachment.** Helper skills invoked in the orchestrator's context share the
25,000-token re-attachment budget and push `/drive` out, because it was invoked first (02). Helper skills
are preloaded in the subagents that need them and never invoked by the orchestrator.

### 7.8 Where each route to mirage is closed

| Route to a false "done" | Primary mechanism | Backstop |
| ----------------------- | ----------------- | -------- |
| Orchestrator certifies its own gate | spine rule; lint requires a verdict file | gatekeeper's stop hook; auditor |
| Scaffold called done | ladder vocabulary; reading-only verdict caps at Partial | stub search by gatekeeper and auditor |
| Verdict without commands | schema validity; gatekeeper's stop hook | orchestrator rejects and respawns once |
| Reasoning leaked into handoff | handoff template built from files | auditor reads handoffs |
| Evidence transcribed | gatekeeper writes its own file | lint checks the file's origin path |
| Kinder harness | Design gate parity list; `harness_kindness` field | walking skeleton; auditor |
| Local called live | lint requires a real-environment command | auditor re-runs Live Proof checks |
| Exit code as effect | observation gate by a different agent | auditor |
| Goal met on claims | Stop gate reads files, not the transcript | goal condition cites the auditor's verdict |
| Bound reached, success claimed | "Stopped because" report; rung from last verdict | auditor blocks Done |
| Tests weakened | gatekeeper checks every gate | auditor greps the run's diff |
| "Unverifiable" inflates a rung | rung stays at what was proven | auditor re-checks the blocker |
| Schedule reported as done | spine rule; scheduled row stays at its rung | auditor |
| Plans reported as results | report derived from evidence; lint on report paths | auditor's tense and reconciliation checks |
| Summary trusted after compaction | `compact` hook re-injects STATE.md | precedence rule |
| Wrong goal built well | discovery trigger; "do not build this" outcome | auditor's scope check |
| Scope narrowed silently | GOAL.md at the intake commit; row retention | auditor diffs intake against final |
| Branches or worktrees left | integrator audit per wave | Stop gate; auditor |

## 8. Open questions and trade-offs

Each question below is one I could not settle from documentation or evidence. Each ends with a
recommendation, and where it disagrees with another report, the argument.

### 8.1 What keeps the run going: a Stop gate or `/goal`

`/goal` offers check-ins, a status view and resume restoration. It is also typed by a person, graded
from the transcript by a model with no tools, and cannot be set by the orchestrator through any
documented path (see the corrections before section 5). A Stop hook declared in the skill's frontmatter
registers when `/drive` is invoked, reads files, runs in interactive, background and `-p` sessions
alike, and can tell "waiting on background work" from "done" through its `background_tasks` input
(3.5). **Recommendation:** the Stop gate is the loop, as reports 01, 10 and 14 also conclude. `/goal`
is optional and appears only in the headless launch command, with a condition that asks for the
auditor's verdict path to be quoted. Test once, at build time, whether a model-issued `/goal` works;
if it does, nothing in this design needs to change, because nothing depends on it.

### 8.2 Model invocation and the headless launch

Report 01 recommends `disable-model-invocation: true`, so that Claude never starts an expensive run on
its own. That setting also blocks the launch form `claude -p "/goal Run /drive on ..."`, because the
goal's directive would need the model to invoke the skill. **Recommendation:** keep invocation disabled
and launch headless runs as `claude -p "/drive <goal>"` with `--max-turns` and `--max-budget-usd`,
relying on the Stop gate. A `-p` process stays open while background subagents run (3.6), so the
check-ins `/goal` would add are not needed to survive a long wave. If the owner wants `/goal`'s status
view, he can run an interactive or background session and type both commands himself.

### 8.3 One ladder file, and one verdict format

Sections 4.1 and 4.10 use FEATURES.json, following Anthropic's harness post, which found JSON harder for
a model to corrupt. Reports 07, 10 and 14 use STATUS.md, a Markdown table with a strict grammar that a
lint parses, and report 10 adds a row-retention check against HEAD. The retention check delivers the
protection the JSON choice was meant to buy, deterministically and against the specific corruption that
matters, a deleted row. Markdown also renders in the report and matches the name the owner already uses.
**Recommendation:** STATUS.md, with report 10's grammar and lint. Wherever sections 4 to 7 of this report
say FEATURES.json, read STATUS.md. For verdicts, use report 07's JSON schema, one file per verdict under
`.drive/evidence/`; the six-line Markdown form in 4.3 names the same fields and should be dropped. The
fields map one to one: Claim to `claims[].id`, Check to `ran[].cmd`, Result to `ran[].exit` and `output`,
Verdict to `claims[].status`, Ladder to `rung_supported`, Notes to `not_checked`.

### 8.4 Who writes the evidence

Report 10's rule is one writer: workers report and the orchestrator writes every state file. Section 6 has
the gatekeeper write its own verdict file. The two rules protect different things. Single writing prevents
concurrent edits to shared, mutable files. A verdict file is written once, by one agent, at a unique path,
and is never edited, so there is nothing to conflict with. The risk on the other side is real: a verdict
that passes through the orchestrator's hands can be softened in transcription, and the orchestrator is the
party with an interest in the result. **Recommendation:** gatekeepers and the auditor write their own
verdict files, fenced to `.drive/evidence/` by a PreToolUse hook. Everything else keeps the single-writer
rule.

### 8.5 Where the plan lives

Report 02 makes STATE.md the plan's authority; section 5 keeps the plan, the classification and the target
rungs in GOAL.md, written once at intake. **Recommendation:** GOAL.md, for the reason given in 5: silent
narrowing is only detectable against a baseline the orchestrator does not rewrite. The cost is one more
file at S and above, and it is small.

### 8.6 Commits, worktrees and wave size

Section 4.2 had builders commit their own packets and allowed waves of twelve. Report 12, drawing on the
owner's own fleets, uses a shared checkout with strict file ownership, makers who never touch git, an
integrator who commits per packet, at most eight concurrent writers, and worktrees only as an exception.
The owner's history is the best evidence available on this question, and it favours 12. **Recommendation:**
adopt report 12's model. The Build exit gate becomes "committed to main by the integrator, with explicit
paths", and the runbook's wave limit becomes eight writers. Read-only swarms can still go to the harness cap.

### 8.7 How often the Stop gate asks a model

Report 14's gate calls a Sonnet judge in a nested non-interactive session on every turn end once the cheap
checks pass. On a 250-turn greenfield run that is 250 extra model calls, most of them grading a phase that
has not changed, and it duplicates the gatekeeper's job. Whether a hook's child process inherits the
settings environment, including the API key, is also unverified (14). **Recommendation:** run the
deterministic checks at every stop, and call the model judge only when STATE.md's `phase:` line differs
from the last value the gate recorded. Verify environment inheritance with one test at build time. If it
fails, the phase judgment moves to a checklist grader subagent that the orchestrator must call before
writing a new phase.

### 8.8 Budgets without spend visibility

The model cannot see its own spend, and the Fable guidance warns that showing it a countdown makes it stop
early (4.6). Dollar caps exist only in print mode. **Recommendation:** count turns in the Stop gate, not in
the model's head (7.5); express budgets to the model in turns and phases only; put dollar caps in the launch
command for headless runs; and record the actual spend from `/usage` in the report's Spend section after the
run, so the Compound phase can tune the size table from evidence. Report 06's dollar envelopes (bug hunt $15
to $40, feature $60 to $150, migration $100 to $300, greenfield $400 to $600) are narrower than 4.6's
estimates, and both are opinion. Three real runs should replace both tables.

### 8.9 Does the per-packet gatekeeper pay at M?

At M, with two to four packets, a gatekeeper per packet plus a final auditor is five or more Opus and Fable
calls on work a single careful review might cover. Report 07 found that small tasks inside the maker's
reliable range gain little from a heavy verifier. The counter-argument is that packets at M are where
integration seams first appear, and a per-wave check sees the seams but not each packet's claim.
**Recommendation:** keep one gatekeeper per packet at M, but let intake merge packets under about a hundred
changed lines into a single gate verdict with a claim for each. Measure the refutation rate over ten runs;
if gatekeepers at M refute less than one packet in ten, move M to a per-wave gatekeeper.

### 8.10 Does a Stop-hook continuation keep the skill's effort?

Skill frontmatter `effort` overrides the session for the invoking turn (3.7). Whether a continuation forced
by a Stop hook block is still that turn is not documented. **Recommendation:** set effort in the launch
command as well as in frontmatter (6.3), record `${CLAUDE_EFFORT}` on every resume, and test once by reading
the effort shown in `/tasks` or the status line after a forced continuation.

### 8.11 How many re-plans before the run should stop

Section 4.9 allows one budget extension, and section 7.4 adds a stop at the third re-plan that changes shape
or goal. The risk is stopping a legitimately exploratory run, such as a bug whose cause moves twice before it
is found. **Recommendation:** count only re-plans that change the shape or the goal, not size changes or
added packets, and exempt the Diagnose phase of `fix`, whose ledger is expected to move.

### 8.12 Operational as a target when the run cannot wait

For `move/migration`, `fix/incident` and `operate`, Operational needs time with the system healthy, and the
owner will not let a run wait on a schedule. **Recommendation:** the run ends at Live Proof with the
health-period row at its honest rung and a scheduled check (desktop scheduled task or CI cron; not a routine,
which the owner's Console login cannot use per report 14) that promotes the row with evidence or rolls back
through the platform's own tools. The report names the check and the date by which the row should read
Operational. This is the one place a schedule is correct, because a health window has no triggering signal.

### 8.13 Interactive or headless by default

Headless runs have hard caps and no one to answer questions, which suits the owner's autonomy rule. They
also lose the desktop pane tools some UI gates need, and the owner cannot redirect them without killing
them. **Recommendation:** interactive or background sessions by default, where the owner types
`/drive <goal>` and the Stop gate drives. Use headless only for shapes whose gates need no pane-bound tools
(`report`, `fix` without `ui`, `move/refactor`), or when the owner explicitly asks for an unattended run with
a dollar cap.

## 9. Skill text candidates

Each passage is plain and imperative and names its target file. They complement, rather than repeat, the
spine in 4.10.

**1. You never pass your own gates** (SKILL.md)
You plan, delegate and decide what happens next; you never decide that work is proven. Every Build, Verify,
Integrate, Live proof and Harden gate goes to a gatekeeper that has not seen how the work was done. Accept a
verdict only as a file the gatekeeper wrote itself, and read only three things from it: the verdict, the rung
it supports, and the gaps. If you catch yourself writing "tests pass" without a verdict path beside it, stop
and spawn the gatekeeper.

**2. Fix the targets before the work starts** (SKILL.md)
At intake, write every behavioural claim as a row in STATUS.md, and write the rung that will count as done for
each row into GOAL.md. When a target is below Live Proof, say why in the same line. Commit both files and
record the commit in GOAL.md's header. From then on, a lowered target, a dropped row or a claim reworded into
an easier one is a downgrade: log it with the date and the reason, and list it in the report under "What is
not done". Never edit GOAL.md except to append a dated re-plan.

**3. Choose phases by what they feed** (references/phases.md)
Derive the phase list from the shape, then remove the phases that shape skips, then thin or deepen the rest by
size. For each phase you keep, write the artifact it produces and the later gate or packet that will read it.
If no later step reads a phase's artifact, delete the phase. Running a phase because the canonical table lists
it is theatre; it costs the owner time and proves nothing.

**4. The smallest path** (references/phases.md)
When the change is one function or one file and its cause or content is already known, do it inline. Read the
surrounding code and its tests, make the change, write one test that fails if your claim is false, run it red
and then green, run the project's own checks, and commit with the claim and the evidence in the commit body.
Create no `.drive/` directory and spawn no subagent. The commit is the record.

**5. Build handoffs from files** (references/delegation.md)
Write every gatekeeper's brief from a template: the claim as it appears in STATUS.md, the scope as a commit range
or path, the exact check commands taken from GOAL.md or the project's own configuration, the target rung, the
verdict schema, and the path for the verdict file. Never paste or paraphrase what a builder reported, what it
changed, or what you think of the work. The gatekeeper's independence survives only if nothing from the maker
reaches it through you.

**6. Reject verdicts that did not check** (references/gates.md)
Before you accept a verdict, confirm it lists at least one command the gatekeeper ran with its exit code, a
refutation attempt for every claim, and a note on every stub or emulator the checks relied on. A pass missing
any of these is malformed: spawn a fresh gatekeeper once, with the handoff and one sentence saying which part
was missing, and do not say what to conclude. A verdict that rests only on reading code supports Partial at
most, whatever it says.

**7. Live means the real thing** (references/gates.md)
A row reaches Live Proof only when a verdict shows a check against the real environment and its captured
response: a request to the deployed URL, the app in the simulator talking to the deployed backend, a call to the
real third-party API from the runtime where the code will run. A deploy command that exited zero, a local
emulator, or a simulator against a mock is Local Proof. For a change to a live system, the evidence is the
system's state read back through its own tools by an agent that did not make the change.

**8. Scope is the deliverable** (SKILL.md)
Do not quietly narrow, widen or swap what the goal asks for. When a claim proves harder than planned, finish it,
or downgrade it openly: log the decision, keep the row, and carry it into the report. When you notice a
neighbouring bug or a tempting improvement, record it as a follow-up; do not do it. When the honest answer to the
goal is "do not build this", stop and say so with the evidence.

**9. Proceed on reversible work** (references/autonomy.md)
Reversible means anything git can revert, anything a deploy can roll back, any file inside the project, and any
configuration with an undo. For reversible actions that follow from the goal, act, then log one line in STATE.md:
what you decided, the alternative you rejected, why, and how to undo it. Never ask whether to deploy to a staging
environment, run tests, create a file, install a development dependency or restart a local service. If a final
message of yours contains "Shall I" or "Want me to", replace it with the decision and do the work.

**10. Leave one checkout** (SKILL.md)
Builders never run git. The integrator commits each packet to main with explicit paths. When a packet needs a
worktree, merge it and remove it, and delete its branch, inside that packet. Before every wave ends, and again
before any report, confirm that `git worktree list` shows only the main checkout, that no branch created by this
run exists, and that `git status --porcelain` is empty. A run that fails this check is not finished, whatever its
tests say.

**11. Report results, not intentions** (references/report.md)
Build the report from STATUS.md, the verdict files and STATE.md, never from GOAL.md or your memory of the plan.
Every line under "What shipped" and every row of the ladder table names its evidence path. Nothing there is
written in the future or conditional tense; anything still to happen belongs under "What is not done", with the
exact command or step that would finish it. Every stop, downgrade, discovery and assumption in STATE.md appears
in the report. Write "What you should look at first" last.

**12. Name the rung, not the feeling** (references/definition-of-done.md)
Describe status only with the ladder's words: Missing, Scaffold, Partial, Local Proof, Live Proof, Operational,
Done. Do not write "complete", "working", "shipped" or "done" for anything below its target rung. Write instead,
for example: "Local Proof: the checkout claim passes its refutation tests locally; not deployed because the
production secret is not set; the deploy command is ..." A clear account of a lower rung is worth more to the
owner than a vague claim of a higher one.

**13. When the premise moves** (SKILL.md)
Treat these as discoveries the moment they appear: a bug that turns out to be a design flaw, a consumer nobody
listed, a feature that already exists in another form, an external system that does not behave as documented, a
second refuted fix for the same failure. Let running builders finish their current packet, start no new ones, log
the discovery with its evidence, re-classify, and revise only what lies downstream. If the goal itself must
change, that is the one question you may ask. If this is the third re-plan to change shape or goal, stop and
write the report.

**14. Turns are counted for you** (references/budgets.md)
The Stop gate counts every turn and writes the count to a file under `.drive/`; read it, do not keep your own. At
a phase's share of the budget, record the overrun and choose, in this order: drop rows marked optional, narrow
live proof to the critical path, accept Local Proof for named rows with a reason, or stop. At ninety percent of
the run's turn bound, write the report, whatever else remains.

**15. Stopping honestly** (SKILL.md)
Stop when the goal is impossible as stated, when the next action is destructive and the goal does not imply it,
when credentials, payment, legal acceptance or account creation stand in the way, when the budget is spent, or
when the same failure has survived two distinct diagnoses. First finish everything that does not depend on the
blocker. Then set the status line in STATE.md to stopped or blocked, name the reason under "Blocked on", and
write the report with "Stopped because" at the top. The Stop gate lets the run end only when those exist.

**16. Resume by invoking, not by remembering** (SKILL.md)
To continue a run in a new session, invoke `/drive` again in the project; that registers the Stop gate and the
compaction hook, which do not survive a restarted process. Then read STATE.md and GOAL.md, read
`git log --oneline -20` and `git status --porcelain`, run the smoke command from GOAL.md, reconcile what you find
with the status file, and continue from "Next". Trust the files over any summary. Do not re-plan unless a
discovery is logged.

**17. Keep security material out of your context** (references/delegation.md)
Send security review, severe testing of authentication or payment code, and any investigation that involves an
attack to Opus subagents, and ask them for sanitized reports that describe the weakness and the fix without
reproducing attack strings or encoded payloads. Never paste such findings into your own turns. If STATE.md
records a model switch for you or for the auditor, say so in the report, and treat verdicts written after the
switch as coming from the model that actually wrote them.

**18. The auditor's questions** (references/anti-patterns.md)
Before a run is reported, the auditor answers these from the repository and the evidence, not from the report
draft. Does the final status file contain every row committed at intake, at a rung its evidence supports? Does
any Done row stand on a stub, a skipped test, a kinder harness or a local check labelled live? Did any scheduled
job, deploy command or question get counted as progress? Is every statement in the report's shipped section
backed by an evidence path, and in the past tense? Is there exactly one worktree, no run-created branch and a
clean tree? Any "no" blocks the report.
