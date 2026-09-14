# 14 · Long-running execution: hours-to-days runs, loops, resumption, and local versus cloud

Researcher report for the `/drive` skill. Covers the post's steps 5 and 9 and its "laptop closed" claim. Everything marked **verified** was checked on 2026-09-14 against the live docs at the URL given; everything marked **post** is the source post's claim; everything marked **opinion** is mine and argued. The owner's own machine was inspected read-only (Claude Code version, `~/.claude/settings.json`, `pmset -g`, skill symlinks); no secret values are reproduced here.

## 1. Executive opinion

A run that lasts hours or days is not kept alive by the model's stamina. It is kept alive by three things the skill must own outright: a completion condition that a separate judge can check against evidence rather than against prose, a stop gate that refuses to let the session end while `STATE.md` is stale or `STATUS.md` carries an unproven "Done", and a git history in which every phase boundary is a small commit to main. Chat history is not one of the three; compaction drops it, and the skill's own text is re-attached after compaction only up to 5,000 tokens.

The mechanism that generalises is the Stop hook, not `/goal`. `/goal` is a session-scoped prompt Stop hook whose evaluator reads the transcript only, cannot run a command, and is set by a person typing a command that Claude has no documented way to issue for itself. It is still worth having on headless launches for its check-ins and status view, but the skill cannot depend on it. The skill should declare its own Stop hook in `SKILL.md` frontmatter: a script that checks state freshness, evidence paths, and a clean tree deterministically, then asks Sonnet 5 at low effort to judge the phase goal from `GOAL.md`, `STATUS.md`, and the evidence index. That gate is registered when `/drive` is invoked, lasts for the session, and works identically in interactive, background, and `-p` sessions.

On where the run lives: keep it local, in a background session under Claude Code's supervisor, on a machine that is kept awake. The owner authenticates with a Console API key, and the docs are explicit that Routines, `--cloud`, `--teleport`, and Remote Control require a claude.ai login. Even with a subscription, the greenfield shape needs the iOS Simulator and Chrome MCPs, which exist only on the Mac. "Laptop closed" is therefore honest only in one sense: a background session survives sleep by pausing, and resumes on wake. Nothing runs while the lid is shut. The cloud option should be a detected conditional with a one-line message, not a v1 dependency.

Schedules exist for one thing: a soak period with no signal to wait on. Everything else is driven now, through the system's own tools, with `Monitor` or a pushed event standing in for polling.

## 2. What the post says, and a critique

**Step 5, "/goal vs Outcomes".** The post says both are "the same idea": an independent grader, not-met starts the next iteration, exit on pass, and that the agent that wrote the code is not the agent that grades it. Partly right. `/goal` is indeed a separate small model judging after each turn (verified, goal docs), and Managed Agents Outcomes provisions a grader in a separate context window against a required markdown rubric with `max_iterations` defaulting to 3 and capped at 20 (verified, platform docs). The exaggeration is "independent grader". The `/goal` evaluator does not run commands or read files; it judges only what Claude has surfaced in the conversation. A grader that reads the maker's own claims is independent in identity, not in evidence. The post also implies Outcomes is the days-long option and `/goal` the quick in-session one. In practice `/goal` runs non-interactively, restores on resume, defers while background work runs, and checks in every 30 minutes with back-off (verified), so it is perfectly usable for a long run; its limit is what it can see, not how long it lasts.

**Step 9, "Routines for days-long orchestration".** The post lists schedule, API and GitHub triggers correctly (verified). What it omits: Routines are a research preview, require a claude.ai subscription login, refuse API-key accounts, start each run from a fresh clone on the default branch, run with no permission prompts and every connected connector by default, have a minimum schedule interval of one hour and a daily per-account run cap, and a green status "does not mean the task in your prompt succeeded" (all verified, routines docs). Each trigger starts a new session; there is no session reuse across events. So a routine is a fine way to start a self-contained job in the cloud on a signal. It is not an orchestrator of a multi-day run, and it cannot load a personal skill from `~/.claude/skills` because only what is committed in the repository's `.claude/` reaches a cloud session (verified, cloud environments docs). "Days-long orchestration" is a stretch; "unattended job starter" is accurate.

**"Running long sessions on a laptop" as a mistake.** Half right. A local interactive session dies with the terminal and does nothing while the machine sleeps. But Claude Code now runs background sessions under a supervisor process that survives closing the terminal, reconnects after sleep, restarts crashed processes, and stops only on shutdown (verified, agent view docs). The realistic failure is not the laptop; it is sleep, and the fix is trivial on the owner's machine, which already holds sleep assertions from Amphetamine and the Claude desktop app (verified locally via `pmset -g`). The post's advice would push a run that needs the iOS Simulator into a cloud VM that has no simulator.

**"Fable 5 was built to run for days."** Anthropic's own wording is more careful: Fable models "sustain long autonomous sessions" and are "suited to tasks larger than a single sitting" (verified, model-config docs), and the platform guide says single requests on hard tasks "can run many minutes". The published harness experiments that actually ran for hours used Opus 4.5 and 4.6 and cost $124 to $200 for four to six hours (verified, engineering blog). Days-long is plausible; it is a property of the harness plus model, and the harness work is what this report is about.

**"Skipping /goal or Outcomes: loops stop at handled enough."** Right diagnosis, incomplete remedy. The engineering blog describes exactly this failure: a later agent instance "would look around, see that progress had been made, and declare the job done" (verified). A goal helps only if its condition is phrased so that the judge can see evidence, and only if something deterministic also refuses to end a session whose state files disagree with its claims. Section 4 gives both.

**Quotes attributed to Anthropic.** "A verifier sub-agent tends to outperform self-critique" is a paraphrase of the Fable 5 prompting guide's "Separate, fresh-context verifier subagents tend to outperform self-critique" (verified). I could not locate the sentence about designing loops with "/goal or Outcomes" and managing context "via memory" in the current docs or the engineering index; treat it as a source claim, consistent in spirit with the model-config guidance to "describe the outcome, not the steps" and "set a goal".

## 3. Verified facts

### `/goal` (https://code.claude.com/docs/en/goal)

- One goal per session; condition up to 4,000 characters; setting it starts a turn immediately with the condition as the directive; a new goal replaces the old one.
- After each turn the configured small fast model (Haiku by default) returns one of three verdicts from the conversation only: not yet met (the reason becomes the next turn's guidance), met (goal cleared, achieved entry recorded), impossible (goal cleared, failed entry recorded). It "doesn't run commands or read files independently".
- Bound it with a clause such as "or stop after 20 turns"; Claude reports progress against the clause and the evaluator judges it from the conversation.
- If Claude answers the evaluator with no tool use for several turns, the loop stops with a warning, the goal stays set, and evaluation resumes after the next prompt. In a `-p` run this ends the process.
- A goal does not change the permission mode; unattended goal turns need auto mode or pre-approved tools.
- Resume restores a still-active goal on every route (`--continue`, `--resume` by ID, name or transcript path, and the picker as of v2.1.239) and resets the turn count, timer, and spend baseline.
- Non-interactive: `claude -p "/goal <condition>"` runs the loop to completion; add `--output-format stream-json --verbose` or nothing prints until the end.
- Errors that clear the goal: an authentication failure when Claude Code manages its own credentials (not in the desktop app or a cloud session), an exhausted credit balance, a context overflow auto-compaction could not clear, and an unavailable model. Other errors keep the goal; on v2.1.269 or later an interactive session retries transient failures three times then pauses, and pauses at once on a rate or usage limit. `CLAUDE_CODE_GOAL_CHECKIN_MINUTES=0` turns both retries and check-ins off.
- Background subagents or shell commands defer evaluation to the next turn that ends with nothing running. After 30 minutes of waiting a check-in is due, then after 1 hour, then every 2 hours (four times the first interval at most). In `-p` mode check-ins are delivered only at turn ends; interactive sessions also start idle check-ins, at most three per goal between prompts.
- Evaluator model: `ANTHROPIC_DEFAULT_HAIKU_MODEL` changes it, and also changes the `haiku` alias and every background feature that uses the small fast model. Evaluation tokens are "typically negligible".
- Requires workspace trust (same rule as settings hooks), `disableAllHooks` not true, and no `allowManagedHooksOnly`.

### Stop hooks and hook mechanics (https://code.claude.com/docs/en/hooks, https://code.claude.com/docs/en/hooks-guide)

- `/goal` "is a built-in shortcut for a session-scoped prompt-based Stop hook".
- Stop input carries `stop_hook_active`, `last_assistant_message`, `background_tasks` (id, type, status, description, command, agent_type, name) and `session_crons` (id, schedule, recurring, prompt). The two arrays "let hooks distinguish 'session is done' from 'session is paused waiting for background work'".
- Stop output: `{"decision":"block","reason":"..."}` or exit code 2 with stderr; or `hookSpecificOutput.additionalContext` for guidance shown as feedback rather than an error. Claude Code overrides a Stop hook after 8 consecutive blocks; `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` raises the cap and `0` disables it.
- Prompt hooks (`type: "prompt"`): fields `prompt` (with `$ARGUMENTS`), `model` (defaults to a fast model), `timeout` (30 s default), `continueOnBlock`; response `{ok, reason, impossible}`; on Stop, `ok:false` feeds the reason back unless `impossible:true`, which lets the stop happen.
- Agent hooks (`type: "agent"`) spawn a subagent with tools for up to 50 turns, default timeout 60 s, no `impossible` field; documented as experimental with the advice to "prefer command hooks" for production.
- Hooks in skill frontmatter register when the skill is invoked and "keep running for the rest of the session, on turns after the skill's own turn as well"; `once: true` removes a hook after its first successful run and is honoured only in skill frontmatter. Session-registered hooks show as "Session Hooks: registered in memory for the current session" in `/hooks`.
- Path placeholders documented for hook commands: `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`. Shell form is the default; exec form (`args`) is recommended when a placeholder is used. `${CLAUDE_SKILL_DIR}` is documented for skill markdown and `allowed-tools`, not for frontmatter hooks.
- Common fields: `timeout` defaults 600 s for command hooks, `if` (one permission-rule pattern), `statusMessage`, `async` (cannot block; killed at `-p` teardown), `asyncRewake`.
- `SessionStart` matchers: `startup`, `resume`, `clear`, `compact`, `fork`; command and `mcp_tool` types only; plain stdout is added to Claude's context; on `resume` the input carries `seconds_since_last_response`, `context_tokens`, `prompt_cache_likely_expired`, `estimated_cache_write_usd` (v2.1.251+). A `reloadSkills` output field re-scans skill directories.
- `PreCompact` can block (exit 2 or `decision: block`); `PostCompact` fires after. `SessionEnd` has a 1.5 s default budget, no decision control, reasons `clear|resume|logout|prompt_input_exit|other`. `StopFailure` fires instead of Stop on API errors (`rate_limit`, `overloaded`, `authentication_failed`, `billing_error`, `max_output_tokens`, ...) and is logging-only. `PostModelSwitch` supports command hooks.
- Subagent frontmatter `Stop` hooks become `SubagentStop`; settings-file `SubagentStart`/`SubagentStop` hooks match on agent name.
- Trust: hooks in settings files and a project skill's frontmatter hooks are used in a `-p` run even in an untrusted folder; a project subagent's frontmatter hooks are not, and "a `-p` session doesn't count as accepting" trust. User-level (`~/.claude`) hooks and agents need no trust step (https://code.claude.com/docs/en/permissions#what-runs-before-you-trust-a-folder, https://code.claude.com/docs/en/sub-agents#hooks-in-subagent-frontmatter).

### `/loop`, cron tools, `ScheduleWakeup`, `Monitor` (https://code.claude.com/docs/en/scheduled-tasks, https://code.claude.com/docs/en/tools-reference#monitor-tool)

- `/loop <interval> <prompt>` creates a fixed cron task; `/loop <prompt>` self-paces via `ScheduleWakeup`, choosing 1 minute to 1 hour per iteration, stopping with `stop: true`, and getting one fallback wakeup about 20 minutes after an iteration that neither reschedules nor stops. Bare `/loop` runs a maintenance prompt or `.claude/loop.md` / `~/.claude/loop.md`.
- Tasks fire only while the session is running and idle; no catch-up for missed fires; recurring tasks expire after 7 days; up to 50 per session; recurring fires are jittered up to 30 minutes (or half the interval), one-shots at `:00`/`:30` up to 90 s early.
- Resume restores unexpired `CronCreate` tasks; a self-paced `/loop` is not restored; background Bash and Monitor tasks are never restored. Backgrounding a session carries `/loop` tasks with it.
- `Monitor` runs a script in the background and streams each output line to Claude, or connects to a WebSocket; the docs call it "often more token-efficient and responsive than re-running a prompt on an interval". Not available when `DISABLE_TELEMETRY` or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` is set.
- Channels push external events (CI, webhooks, chat) into a running session; research preview; "require Anthropic authentication through claude.ai or a Console API key" (https://code.claude.com/docs/en/channels).
- Comparison table (also on the desktop scheduled-tasks page): cloud routines need no machine and no open session, minimum interval 1 hour, fresh clone, no permission prompts; desktop scheduled tasks need the app open and the machine awake, minimum 1 minute, local files, per-task permission mode; `/loop` needs an open session and inherits everything.

### Routines (https://code.claude.com/docs/en/routines) and desktop scheduled tasks (https://code.claude.com/docs/en/desktop-scheduled-tasks)

- Routines: research preview; Pro, Max, Team, Enterprise; `/schedule` in the CLI creates scheduled routines and can add GitHub triggers (v2.1.225+); API triggers are added on the web only. With a Console API key, `/schedule` prints that it is "available with Claude for Enterprise"; if `ANTHROPIC_API_KEY` is set in the shell or `apiKeyHelper` in settings, it takes precedence over a claude.ai login.
- Each run clones the selected repositories from the default branch and pushes to `claude/`-prefixed branches, which are always accepted; a push to any other branch is rejected if the branch is protected, someone else has an open PR from it, or it carries commits authored by someone else. The prompt "must be self-contained and explicit about what to do and what success looks like". The run can "use skills committed to the cloned repository". Local `claude mcp add` servers are unavailable unless declared in a committed `.mcp.json` or added as a connector. Fire payload text arrives wrapped as untrusted data and the prompt must opt in to acting on it.
- Environments: Trusted network allowlist by default (package registries, GitHub, cloud SDKs), Custom or Full available; setup script should finish within about five minutes; the filesystem snapshot is cached about seven days.
- Usage: draws down subscription usage; daily cap on runs started per account; one-off runs do not count against the cap.
- Desktop scheduled tasks: local, minimum interval 1 minute, per-task permission mode and model, optional worktree isolation, "only fire while the app is open and your computer is awake", "Keep computer awake" setting exists and "Closing the laptop lid still puts it to sleep", one catch-up run for missed fires, prompt stored at `~/.claude/scheduled-tasks/<task-name>/SKILL.md`, and a task can reschedule itself with the `update_scheduled_task` MCP tool. These tools (`mcp__scheduled-tasks__*`) are present in the owner's sessions.

### Cloud sessions (https://code.claude.com/docs/en/claude-code-on-the-web, https://code.claude.com/docs/en/cloud-environments, https://code.claude.com/docs/en/feature-availability)

- Carries over to a cloud session: the repository's `.claude/skills/`, `.claude/agents/`, `.claude/commands/`, plugins declared in `.claude/settings.json`, committed `.mcp.json`. Does not: `~/.claude/CLAUDE.md`, `~/.claude/skills|agents|commands`, user-scoped plugins, user-level hooks, servers added with `claude mcp add` at local or user scope.
- `claude --cloud "<task>"` starts a cloud session for the current repository; `claude -p "<message>" --cloud <session-id>` queues a follow-up and exits; `claude --teleport <id>` pulls a cloud session and its branch into a checkout of the same repository. All require a claude.ai account. "Sessions stop after a period of inactivity and the session's VM is reclaimed."
- Features "not reachable with an Anthropic Console API key": Claude Code on the web, Routines (`/schedule`), Remote Control, plus the mobile app and Slack. The documented alternatives for Console accounts are `/loop` for scheduling and GitHub Actions for cloud runs (which accept an `ANTHROPIC_API_KEY` secret and a cron `schedule` trigger, https://code.claude.com/docs/en/github-actions#run-on-a-schedule).
- Cloud sessions compact earlier via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`; subagents from `.claude/agents/` work; rate limits are shared with the account and there is no separate compute charge; retention follows the account type, 30 days for standard accounts (https://code.claude.com/docs/en/data-usage).

### Sessions, resume, headless, background sessions (https://code.claude.com/docs/en/sessions, https://code.claude.com/docs/en/headless, https://code.claude.com/docs/en/agent-view, https://code.claude.com/docs/en/cli-reference)

- Transcripts live at `~/.claude/projects/<project>/<session-id>.jsonl`, deleted after `cleanupPeriodDays` (default 30). Sessions created with `-p` are left out of the picker and `--continue` but resume with `claude --resume <session-id>`, which searches every project on the machine. A resumed session restores history, model, agent, permission mode (terminal routes without `-p`), the active goal, and unexpired cron tasks; not background Bash or Monitor tasks, and not `--mcp-config`, `--settings`, `--plugin-dir`, `--fallback-model`, or `--add-dir`. A tool still running when the process died "doesn't finish or run again".
- `claude -p --resume <id>` continues a session; SIGTERM leaves the in-progress turn unfinished (exit 143), runs `SessionEnd`, and the turn continues on resume. Background Bash tasks are killed about 5 s after the final result; background subagents and workflows keep `-p` open until they finish, with a 10-minute idle ceiling (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`). `--max-turns` and `--max-budget-usd` are print-mode only; `--output-format json` returns `total_cost_usd`. `--bare` skips hooks, skills, agents, CLAUDE.md and auto memory and needs `ANTHROPIC_API_KEY` in the environment.
- `claude --bg "<prompt>"` (positional prompt, not `-p`) starts a background session under the supervisor and prints a short ID; `--name`, `--agent`, and `--resume <full-id> --bg "<prompt>"` combine with it; `claude agents`, `claude agents --json --all` (state `working|blocked|done|failed|stopped`, `waitingFor`), `claude attach|logs|stop|respawn|rm <id>`, `claude daemon status`. Sessions are "preserved across sleep but stop if the machine shuts down"; a finished, unattached session's process is stopped after about an hour and resumes on the next reply (pin with Ctrl+T to keep it running); background shells, subagents, workflows and `/loop` tasks carry over when a session is backgrounded, running monitors do not. `/background` (`/bg`) moves a running interactive session to the background. `--dangerously-skip-permissions` persists for `--bg` sessions.
- Usage limits: an interactive claude.ai-subscription session waits for a usage-limit reset and continues on its own, re-arming at most twice; after a sleep longer than about 30 minutes it needs Enter; exiting ends the wait; API keys have no reset to wait for because usage is metered per request (https://code.claude.com/docs/en/interactive-mode#wait-for-a-usage-limit-to-reset). `CLAUDE_CODE_RETRY_WATCHDOG=1` retries 429/529 capacity errors indefinitely for unattended sessions and still fails at once on a spend-limit 429 (https://code.claude.com/docs/en/env-vars).

### Context, compaction, skills, subagents, workflows

- Auto-compaction on 1M-window models (Fable 5.1, Fable 5, Sonnet 5, Opus 4.7+) runs at about 967K tokens by default; cloud sessions earlier; window settable from 100K to 1M with `/autocompact`, `--autocompact`, or `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (https://code.claude.com/docs/en/model-config#default-auto-compact-thresholds). Compaction "clears older tool outputs first, then summarizes"; "detailed instructions from early in the conversation may be lost"; a "Compact Instructions" section in CLAUDE.md steers the summary; repeated refills produce a thrashing error and stop auto-compaction (https://code.claude.com/docs/en/how-claude-code-works#when-context-fills-up, https://code.claude.com/docs/en/troubleshooting#auto-compaction-stops-with-a-thrashing-error).
- What survives compaction: system prompt; project-root CLAUDE.md, auto memory and the plan-mode plan re-injected from disk; path-scoped rules and nested CLAUDE.md reloaded as matching files are read; up to five most recently modified files re-read (over 5,000 tokens become a path reference); invoked skill bodies re-injected "capped at 5,000 tokens per skill and 25,000 tokens total; oldest dropped first", truncation keeps the start of the file; context hooks added earlier is summarised; `SessionStart` hooks matching `compact` run and their output is added (https://code.claude.com/docs/en/context-window#what-survives-compaction).
- Skill content enters the conversation once and is not re-read on later turns; re-invoking an unchanged skill adds only a note; `disallowed-tools` can remove `AskUserQuestion` for autonomous skills; `description` plus `when_to_use` is truncated at 1,536 characters in the listing; `model` and `effort` in skill frontmatter apply while the skill is active and the model override "applies for the rest of the current turn" (https://code.claude.com/docs/en/skills#frontmatter-reference, #skill-content-lifecycle). Built-in commands reachable through the Skill tool are named as `/init` and `/security-review`; "Other built-in commands such as `/compact` are not". No `Goal` tool appears in the tools reference.
- Subagents: background by default in interactive sessions; in `-p` runs Claude backgrounds by default and foregrounds when it needs the result; background subagents keep MCP tools and `Read, Grep, Glob, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage, Artifact`; `maxTurns` returns partial output that can be resumed with `SendMessage`; concurrency cap 20 (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`); `memory: user|project|local` gives a subagent its own `MEMORY.md` (first 200 lines or 25 KB loaded); subagents auto-compact like the main conversation; their edits are outside `/rewind` checkpoints (https://code.claude.com/docs/en/sub-agents, https://code.claude.com/docs/en/checkpointing#subagent-edits-not-restored).
- Dynamic workflows run in the background, save their script under the session directory, are resumable within the same session (replay reruns from the first changed agent), allow 16 concurrent agents and 1,000 per run, forbid mid-run user input, and warn above 25 agents or 1.5M projected tokens; default size guideline `medium` (fewer than 15 agents) (https://code.claude.com/docs/en/workflows).
- Checkpoints: one per prompt that starts a turn, 100 most recent kept, snapshots swept after `cleanupPeriodDays`, Bash-made changes not tracked, "not a replacement for version control" (https://code.claude.com/docs/en/checkpointing).

### Models, pricing, Fable behaviour

- Aliases on the Anthropic API: `fable` resolves to Fable 5.1 (v2.1.257+), `opus` to Opus 5, `sonnet` to Sonnet 5 (https://code.claude.com/docs/en/model-config#model-aliases). Neither the models overview nor the pricing page lists a "Sonnet 4.8"; the brief's "Sonnet 4.8" should be read as "the current `sonnet` alias", which is Sonnet 5 (https://platform.claude.com/docs/en/models/overview, https://platform.claude.com/docs/en/about-claude/pricing).
- Pricing per million tokens (input / output; cache read): Fable 5.1 $10 / $50 / $0.25 (0.025x, unique to Fable 5.1 and Mythos 5.1); Fable 5 $10 / $50 / $1; Opus 5 and Opus 4.8 $5 / $25 / $0.50; Sonnet 5 $2 / $10 / $0.20; Sonnet 4.6 $3 / $15; Haiku 4.5 $1 / $5. Batch API halves these.
- Fable safety classifiers: biology-flagged requests re-run on Opus 5, cybersecurity-flagged on Opus 4.8, and "after a fallback, the session continues on the fallback model" until `/model` is run; the first request of a session can trip it on repository context alone (https://code.claude.com/docs/en/model-config#automatic-model-fallback). Fable usage-credit consent prompts are held five minutes (`dialogExpiry`) in background sessions and never shown in `-p`; this applies to subscription billing, not API keys.
- Fable 5.1 default effort is `high`; the guide says `medium` roughly matches Fable 5 at lower cost and `low` "is often competitive with Claude Opus and Claude Sonnet models on cost per task while scoring higher". Recommended prompt blocks for autonomy ("You are operating autonomously. The user is not watching in real time..."), for compaction summaries, for restraint ("Keep changes and tests to what the task asks for"), and for letting the lead keep working while subagents run (https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1). Fable 5 guide: "Before reporting progress, audit each claim against a tool result from this session"; "Separate, fresh-context verifier subagents tend to outperform self-critique"; skills written for prior models "are often too prescriptive"; telling the model to echo its reasoning can trigger `reasoning_extraction` refusals (https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5).
- Managed Agents Outcomes: rubric required, grader in a separate context, `max_iterations` default 3 and maximum 20, results `needs_revision | max_iterations_reached | failed | interrupted`, one outcome at a time, chainable (https://platform.claude.com/docs/en/managed-agents/define-outcomes). Available through the API (so to an API-key account) but it is a different harness, not Claude Code.

### Anthropic's published harness experience

- "Effective harnesses for long-running agents" (https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents): an initializer session writes `init.sh`, a progress file, a feature list JSON with every feature marked failing, and an initial commit; each later session reads the progress file and `git log`, runs a basic smoke test, works on one feature at a time, tests end to end through browser automation, commits, and updates progress. Named failure modes: trying to one-shot the app and running out of context mid-feature; a later instance declaring the job done because progress exists; marking features complete without testing.
- "Harness design for long-running application development" (Rajasekaran, 2026-03-24, https://www.anthropic.com/engineering/harness-design-long-running-apps): planner, generator, evaluator; sprint contracts negotiated through files; the evaluator used Playwright and was "out of the box... a poor QA agent" until tuned by reading its logs; context resets beat compaction on Sonnet 4.5 because of "context anxiety", while Opus 4.5 allowed one continuous session with compaction; the sprint construct was removed on Opus 4.6; the planner stayed because without it the generator under-scoped; the evaluator "is worth the cost when the task sits beyond what the current model does reliably solo". Costs: $200 for 6 hours (Opus 4.5 harness), $124.70 for 3 h 50 min (Opus 4.6 harness), of which the builder was two hours and $71.

### The owner's environment (read-only inspection, 2026-09-14)

- Claude Code 2.1.263. Below 2.1.269 (goal auto-retry and pause notices) and 2.1.267 (frontmatter effort under the Fable default-effort hold); at or above every other version gate cited here.
- `~/.claude/settings.json`: `forceLoginMethod: console` with a Console API key in the `env` block; `ANTHROPIC_SMALL_FAST_MODEL` set to a Sonnet 4.5 1M model ID (the variable is documented as deprecated in favour of `ANTHROPIC_DEFAULT_HAIKU_MODEL` and still read); `model: claude-fable-5-1[1m]`; `effortLevel: high` with `claude-fable-5-1` at `medium`; `permissions.defaultMode: auto`; `hooks: {}`; `skipDangerousModePermissionPrompt: true`; `outputStyle: Concise`; `teammateMode: tmux`. `~/.claude/agents/` is empty. Skills are symlinks to `~/Projects/<name>/skill`, confirming the convention in the brief.
- `pmset -g` reports system sleep "prevented by sharingd, Claude, Amphetamine, powerd". `caffeinate -s` prevents system sleep on AC power only (`man caffeinate`). Closing the lid still sleeps a MacBook unless it is in clamshell mode with an external display.

## 4. Detailed spec

### 4.1 Where the run lives

The skill decides this at intake and records it in `STATE.md`. The decision has three inputs: whether the shape needs local-only tools (iOS Simulator MCP, Chrome DevTools or Playwright MCPs, local databases, the owner's `~/.claude` skills and MCP servers), whether the account can use cloud features (a claude.ai login; detect by the absence of `ANTHROPIC_API_KEY` and `apiKeyHelper` and a `forceLoginMethod` other than `console`), and whether the run must survive a machine shutdown rather than a sleep.

| Situation | Host | Launch |
|---|---|---|
| Default: any shape, owner at or near the machine at times | Local background session under the supervisor | `claude --bg --name drive-<slug> "/drive <goal>"` from the repository root; watch with `claude agents`, `claude logs <id>`; attach with `claude attach <id>` |
| Owner typed `/drive` in an interactive session | Same session, then backgrounded | Skill instructs Claude to finish intake, write `STATE.md`, then tell the owner once: "run `/bg` to detach; the run continues under the supervisor" (this is the only thing he types, and it is optional) |
| Scripted or CI-driven run, no terminal | Headless | `claude -p "/drive <goal>" --output-format stream-json --verbose --permission-mode auto --permission-prompts none --max-turns 400 --max-budget-usd <n> 2>&1 \| tee .drive/runs/<id>/stream.jsonl` |
| Soak check between migration stages | Desktop scheduled task (local) or a GitHub Actions cron with `ANTHROPIC_API_KEY` | Created by the skill through the `scheduled-tasks` MCP tools or by committing `.github/workflows/drive-soak.yml`; never as the primary run |
| Run must continue with the machine shut down, and the account has a claude.ai login, and no local-only tool is needed | Cloud session or a one-off routine | Section 4.9 |

Two facts settle the default. Background sessions survive terminal closure, auto-updates and sleep, and stop only on shutdown; and the greenfield shape's verification tools are local. The launch recipe should also export, for the run only: `CLAUDE_CODE_RETRY_WATCHDOG=1`, `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=20` (the gate converges in one or two turns, the higher cap is a safety margin), `BASH_DEFAULT_TIMEOUT_MS=600000` (long test suites and deploys otherwise get moved to the background at two minutes), and `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5` (replaces the deprecated variable and moves the `/goal` evaluator, session titles and summaries onto the current Sonnet at $2/$10, cheaper than the Sonnet 4.5 currently pinned).

Keep-awake: the skill's pre-flight checks `pmset -g | grep -i 'sleep prevented'`; if nothing holds an assertion it starts `caffeinate -is -w <pid of the claude process>` and records the fact in `STATE.md`. It states plainly in `STATE.md` that a closed lid pauses the run.

### 4.2 File layout

All durable state is in the repository, never in chat and never only in `~/.claude`:

```
STATE.md                      heartbeat + resume card (rewritten at every phase boundary and before any stop)
STATUS.md                     status ladder per deliverable, one row each, evidence path per row
.drive/ACTIVE                 the current run id (presence marks a run in progress; deleted at completion)
.drive/runs/<run-id>/
  GOAL.md                     current phase goal in evaluator-checkable form (section 4.3)
  PLAN.md                     phases, order, budgets
  DIGEST.md                   what the owner would want to read, appended per phase
  gate.log                    every Stop-gate decision with reason and timestamp
  evidence/<phase>/<n>-<slug>.md   command, cwd, timestamp, exit code, output tail, screenshot paths
  stream.jsonl                headless runs only
```

`.drive/runs/*/evidence` and `stream.jsonl` are git-ignored by default; `STATE.md`, `STATUS.md`, `.drive/ACTIVE`, `GOAL.md`, `PLAN.md` and `DIGEST.md` are committed. The reason for the split: the owner's precedence rule ranks proof artifacts above STATUS files, so proof must be durable, but he also refuses stray artifacts in commits. Keep a small, curated proof set committed under `docs/proof/<date>-<phase>/` (the final smoke output, the final screenshot set, the live URL response) and leave bulk logs local. `STATUS.md` rows point at whichever exists.

`STATE.md` template (the gate checks freshness by file mtime; the `updated_at` line is for humans and the judge):

```markdown
# STATE · <project> · run <run-id>
updated_at: 2026-09-14T13:42:10+01:00
host: local background session <short-id> (supervisor) · model fable-5-1 · effort high
phase: 3/6 implementation wave B · goal: .drive/runs/<id>/GOAL.md
last_commit: 8d47a1c "wave B: outfit composer endpoint + tests"

## Done (with proof)
- Backend auth + KV schema · Local Proof · evidence/2-backend/07-tests.md
## In progress
- iOS OutfitCanvas view: renders, snapshot test failing on dark mode (evidence/3-ios/03-snapshot.md)
## Next (in order)
1. fix dark-mode snapshot; 2. wire /compose to canvas; 3. wave B gate
## Blocked / decisions taken alone
- Chose Cloudflare Queues over Durable Objects for retries; reasoning in docs/adr/004.md
## How to resume
claude --resume <full-session-id> --bg "/drive --resume"   (or /drive --resume in any session in this repo)
## Stopped early
(empty unless the run ended on a bound or an impossible verdict; give the reason)
```

`STATUS.md` uses the owner's ladder verbatim, one table, and the gate parses it:

```markdown
| Deliverable | Claim | Status | Evidence | Updated |
|---|---|---|---|---|
| POST /compose | returns a scored outfit for any 3-item wardrobe in <800 ms | Local Proof | .drive/runs/r1/evidence/2-backend/09-compose-latency.md | 2026-09-14 |
| Wardrobe sync | offline edits reconcile without loss | Partial | | 2026-09-14 |
```

Allowed statuses: `Missing`, `Scaffold`, `Partial`, `Local Proof`, `Live Proof`, `Operational`, `Done`. Any row at `Local Proof` or above must cite an evidence path that exists; any row at `Live Proof` or above must cite evidence whose file contains a live URL or a response captured from the deployed system.

### 4.3 Writing the goal condition

The evaluator, whether `/goal`'s or the skill's own judge, sees text. The condition therefore names the command that proves each clause and requires its output to appear. Template, one per phase, written to `GOAL.md` by the skill at the start of the phase:

```
Phase <n> "<name>" is complete when every clause below is shown true in this session:
1. `<test command>` exits 0; the last 20 lines of its output are in the transcript and in evidence/<phase>/.
2. STATUS.md rows for <deliverables in this phase> read "Local Proof" or better and each cites an
   evidence file that exists (show `ls` of the cited paths).
3. `git status --porcelain` prints nothing; `git log -1 --format=%s` shows this phase's commit.
4. STATE.md was rewritten after that commit (show `stat -f %m STATE.md` and `git log -1 --format=%ct`).
Constraints: no test is deleted, skipped or weakened; no file outside <scope paths> changes;
nothing is marked Live Proof without a response from the deployed URL in the transcript.
Bound: stop anyway after <N> turns or <H> hours; if you stop on the bound, write why under
"Stopped early" in STATE.md and leave the phase goal in place.
```

Rules for the clauses, each of which follows from a verified property: one measurable end state per clause (the goal doc's own guidance); a stated check the model can run and paste; constraints that protect the ladder; a turn-or-time bound because neither `/goal` nor a Stop hook has a native limit other than the block cap; and the words "shown true", because the evaluator cannot read files. Phrase every clause as evidence in the transcript, never as "the feature works".

For a run launched headless, the skill's launch recipe may also set `/goal` as the whole-run condition: `claude -p "/goal Run /drive on: <goal>. The run is complete when .drive/ACTIVE no longer exists, STATUS.md has no row below Local Proof for deliverables in PLAN.md, and STATE.md 'Next' is empty; or stop after 600 turns."` This gives the run the 30-minute check-ins and the status view for free, on top of the skill's gate. I checked and could not find a way for Claude to set `/goal` on its own, so the skill must never rely on it being present.

### 4.4 The Stop gate

Declared in `SKILL.md` frontmatter so it applies to drive runs only and to nothing else the owner does:

```yaml
---
name: drive
description: Turn a high-level goal into a complete, autonomous, evidence-gated run ...
argument-hint: <high-level goal> | --resume
disallowed-tools: AskUserQuestion
hooks:
  Stop:
    - hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/hooks/stop-gate.sh"
          timeout: 300
          statusMessage: "drive: checking state, evidence and goal before ending"
  SessionStart:
    - matcher: compact
      hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/hooks/reinject.sh"
  PostModelSwitch:
    - hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/hooks/log-model-switch.sh"
  StopFailure:
    - hooks:
        - type: command
          command: "$HOME/.claude/skills/drive/hooks/log-failure.sh"
          async: true
---
```

Why frontmatter and not settings: settings hooks fire in every session in scope, which would make the owner's ordinary sessions refuse to end; frontmatter hooks register on `/drive` and last for the session, which is exactly the scope of a run. Why `$HOME/...` rather than `${CLAUDE_SKILL_DIR}`: the docs list only `${CLAUDE_PROJECT_DIR}` and the plugin placeholders for hook commands, and the skill directory is a stable symlink under `~/.claude/skills`. Why `AskUserQuestion` is removed: the run is autonomous; a question ends a turn and, in a background session, parks it as "blocked" until someone answers, which for this owner is never.

`stop-gate.sh` (macOS `stat -f %m`; `jq` required):

```bash
#!/usr/bin/env bash
# drive stop gate: refuse to end a turn while run state is stale, claims are unproven,
# or the phase goal is not met. Allow when nothing is running a drive run here.
set -u
INPUT=$(cat)
CWD=$(jq -r '.cwd' <<<"$INPUT"); cd "$CWD" 2>/dev/null || exit 0
[ -f .drive/ACTIVE ] || exit 0
RUN=$(cat .drive/ACTIVE); RUNDIR=".drive/runs/$RUN"; LOG="$RUNDIR/gate.log"; mkdir -p "$RUNDIR"
log(){ printf '%s %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }
block(){ log "BLOCK $1"; jq -nc --arg r "$1" '{decision:"block",reason:$r}'; exit 0; }

# Background work still running: let the turn end; its result will start the next turn.
if [ "$(jq '.background_tasks // [] | length' <<<"$INPUT")" != "0" ]; then log "ALLOW background work running"; exit 0; fi

reasons=""
# 1. STATE.md must be newer than the newest change (HEAD commit or any dirty file).
newest=$( { git log -1 --format=%ct 2>/dev/null
            git status --porcelain 2>/dev/null | awk '{print $NF}' | while read -r f; do [ -e "$f" ] && stat -f %m "$f"; done
          } | sort -n | tail -1 )
state=$(stat -f %m STATE.md 2>/dev/null || echo 0)
[ "$state" -ge "${newest:-0}" ] || reasons+="STATE.md is older than the latest change. Rewrite it: done-with-proof, in-progress, next steps in order, how to resume. "

# 2. No status at Local Proof or above without an existing evidence file; Live Proof needs a live URL in it.
while IFS='|' read -r _ item claim status evidence _; do
  s=$(echo "$status" | xargs); e=$(echo "$evidence" | xargs); i=$(echo "$item" | xargs)
  case "$s" in
    "Local Proof"|"Live Proof"|"Operational"|"Done")
      { [ -n "$e" ] && [ -e "$e" ]; } || reasons+="STATUS.md: '$i' is '$s' but cites no existing evidence file. Lower the status or produce the evidence. "
      case "$s" in "Live Proof"|"Operational"|"Done")
        [ -n "$e" ] && [ -e "$e" ] && grep -qiE 'https?://' "$e" || reasons+="STATUS.md: '$i' is '$s' but its evidence has no live URL or deployed response; local-only work is never Live Proof. ";;
      esac;;
  esac
done < <(grep -E '^\|' STATUS.md 2>/dev/null | tail -n +3)

# 3. A run that declares itself finished must leave a clean tree on main.
if [ -f "$RUNDIR/DONE" ]; then
  [ -z "$(git status --porcelain)" ] || reasons+="Run is marked DONE but the tree is dirty; commit to main or revert. "
  [ "$(git rev-parse --abbrev-ref HEAD)" = "main" ] || reasons+="Run is marked DONE but HEAD is not main; merge and delete the branch or worktree now. "
  [ -z "$(git worktree list | tail -n +2)" ] || reasons+="Run is marked DONE but worktrees remain; merge and remove them. "
fi
[ -n "$reasons" ] && block "$reasons"

# 4. Phase goal judged by a fresh Sonnet 5 from files, not from the transcript.
if [ -f "$RUNDIR/GOAL.md" ] && [ ! -f "$RUNDIR/DONE" ]; then
  LAST=$(jq -r '.last_assistant_message // ""' <<<"$INPUT" | tail -c 6000)
  EVID=$(ls -1 "$RUNDIR"/evidence/*/* 2>/dev/null | tail -60)
  verdict=$(claude -p --bare --no-session-persistence --model claude-sonnet-5 --effort low \
    --output-format json \
    --json-schema '{"type":"object","properties":{"met":{"type":"boolean"},"impossible":{"type":"boolean"},"reason":{"type":"string"}},"required":["met","reason"]}' \
    "$(cat "$HOME/.claude/skills/drive/hooks/judge-prompt.md")

=== GOAL.md ===
$(cat "$RUNDIR/GOAL.md")
=== STATUS.md ===
$(cat STATUS.md)
=== STATE.md ===
$(cat STATE.md)
=== evidence files present ===
$EVID
=== agent's last message (claims, not evidence) ===
$LAST" 2>>"$LOG" | jq -c '.structured_output // empty')
  met=$(jq -r '.met // false' <<<"$verdict"); imp=$(jq -r '.impossible // false' <<<"$verdict"); why=$(jq -r '.reason // "judge returned nothing"' <<<"$verdict")
  log "JUDGE met=$met impossible=$imp $why"
  if [ "$imp" = "true" ]; then printf '## Stopped early\n%s\n' "$why" >> STATE.md; log "ALLOW impossible"; exit 0; fi
  [ "$met" = "true" ] || block "Phase goal not met: $why"
fi
log "ALLOW"; exit 0
```

`judge-prompt.md` is short and severe: you are grading whether a phase goal is met; every clause needs a cited evidence file whose contents show the command and its output; a claim in the agent's message with no file is not evidence; a STATUS row above `Local Proof` without a live response is a failure; if a clause can never be satisfied as written, say so with `impossible: true`; return only the JSON. Two design choices need saying. The gate does not exit early on `stop_hook_active`, unlike the docs' example, because its checks are idempotent and converge (once the state file is fresh, check 1 passes), and the block cap remains as the backstop. And the deterministic checks run before the model call, so the Sonnet judgment costs are paid only when the cheap checks pass.

`reinject.sh` prints `STATE.md`, the first 40 lines of `STATUS.md`, `GOAL.md`, `git log --oneline -8`, and one line: "This is a /drive run; the skill's rules apply; state lives in these files, not in memory." Plain stdout from a `SessionStart` hook enters Claude's context, and the `compact` matcher fires after every compaction, so the spine of the run is restored each time the summary might have lost it. `log-model-switch.sh` appends the new model to `STATE.md` under `host:` so a classifier fallback to Opus 4.8 is recorded rather than silent. `log-failure.sh` appends the `error` field and timestamp to `gate.log`.

Interaction with `/goal`: both are Stop hooks and both fire after every turn. `/goal` can be present or absent; when both block, Claude receives both reasons. Keep them non-overlapping: the gate enforces invariants (state, evidence, clean tree, phase goal from files); a `/goal`, if set, states the whole-run end condition and the bound. Neither should describe how to do the work.

### 4.5 Resume protocol

Run at every start, including the very first (when it finds no `.drive/ACTIVE` it creates the run):

1. `cat .drive/ACTIVE` and `STATE.md`; if `STATE.md` is missing, look for `.drive/runs/*/PLAN.md` and rebuild `STATE.md` from `git log` and `STATUS.md` before anything else.
2. `git status --porcelain`, `git log --oneline -10`, `git worktree list`, `git branch --list 'drive/*'`. A dirty tree or a leftover worktree from a previous process is the first task: inspect, then commit or revert, then remove the worktree. Uncommitted work in a worktree is exactly what the owner never wants left behind.
3. Re-derive the goal: read `GOAL.md` and `PLAN.md`; confirm the phase in `STATE.md` matches what the repository shows (tests present, files present). Where they disagree, trust the tree over `STATE.md` and rewrite `STATE.md`.
4. Re-run the phase's cheapest proof command (the smoke test, `wrangler dev` health check, simulator boot) before resuming work, as the engineering blog's harness does; undocumented breakage shows up here, not later.
5. Check `gate.log` for the last verdicts and `STATE.md` "Stopped early"; if the previous process ended on a bound, decide whether the bound was right or the plan needs a smaller phase.
6. Record `host:` (background session ID, model, effort) and `updated_at`, then continue.

Launch forms for resume, in order of preference: `claude --resume <full-session-id> --bg "/drive --resume"` (continues the same conversation with the goal and cron tasks restored; the skill hooks re-register because `/drive` is invoked again); `/drive --resume` typed in any session opened in the repository (fresh context, state from files); `claude -p "/drive --resume" ...` for scripted restarts. Resuming a session inactive for more than about an hour repays the whole context into the prompt cache; the `resume` SessionStart input reports `estimated_cache_write_usd`, and for a 500K-token transcript on Fable 5.1 that is several dollars, so a fresh session that reads the files is often cheaper than resuming the old one. The skill should prefer the fresh session once the previous one has compacted twice or exceeded roughly 400K tokens.

### 4.6 Waiting well

Order of preference when the run has to wait for something:

1. Do not wait; drive it. Deploy with `wrangler deploy` and verify with `curl`; run the migration and query the row counts; trigger the CI job with `gh workflow run` and read `gh run watch`. The owner's rule is absolute here: a thing that has an API is done through the API, now.
2. `Monitor`: a background script that tails the log, polls `gh run view --json status` or the health endpoint, and prints one line on change. Claude keeps working and reacts to the line. Cheaper than any loop, and the docs recommend it over `/loop` for dynamic waits. Caveat: monitors are not restored on resume and stop when a session is backgrounded, so the skill must re-create them from `STATE.md` "In progress" on resume.
3. A pushed event through a channel or a webhook receiver, when one exists in the environment. Not built in v1.
4. Self-paced `/loop <prompt>` for a wait longer than a monitor's five-minute default life makes sense for, such as a CI pipeline that takes 40 minutes: `/loop check whether run <id> finished; if green, continue phase 4 from STATE.md; if red, read the failing job log and fix`. It ends itself with `ScheduleWakeup stop: true`. It is not restored on resume; `STATE.md` must say it was running.
5. A scheduled check only for a soak period: a condition with no triggering signal, such as "no 5xx for 24 hours after cutover". Locally a Desktop scheduled task with a fixed prompt; in CI a GitHub Actions cron. The check itself follows the same rules: it reads `STATE.md`, runs the proof commands, appends evidence, and, on failure, rolls back through the system's own tools rather than filing a note for a human.

The gate cooperates with all five: with background work running it allows the turn to end, and the finished work starts the next turn. What the skill must never do is announce "the cron will pick it up" as a completion. A scheduled soak check is a step in `PLAN.md` with its own `STATUS.md` row (`Soak 24h` at `Partial` until the check has written evidence), and the run is not `Done` until that row is.

### 4.7 Context across a long run

- The skill's first 5,000 tokens are the spine: the run loop (resume protocol, phase loop, gate contract, commit rule, stop rule) and nothing else. Everything below that line is a pointer to `references/<topic>.md` read on demand. After compaction only that spine is re-attached; the rest of the skill is gone until re-read.
- The project `CLAUDE.md` gets a short "Compact instructions" section, committed, telling the summariser to keep the list of modified files, the proof commands, the current phase and the next three steps. The Fable 5.1 guide's compaction-summary instruction is the model for its wording.
- Heavy reading goes to subagents: log analysis, dependency surveys, reading a 3,000-line file, research fan-outs. The main context receives summaries with file paths. A single oversized tool output can make auto-compaction thrash; the fix is to read in ranges and to keep test output to its tail.
- Before each phase boundary the main agent rewrites `STATE.md` and `DIGEST.md`; those files, not the conversation, are what the next phase reads. This is the engineering blog's progress file, made mandatory by the gate.
- Prefer a fresh session per day-sized phase over one enormous conversation. The Rajasekaran post shows compaction was enough on Opus 4.5 and later, but the cache-repay cost of resuming a huge idle session and the 5,000-token skill cap both argue for resets at natural boundaries. A reset is only safe because the state is in files, which is the point of the gate.

### 4.8 Checkpointing

- Commit to main at every phase boundary and at every green test run inside a phase; small commits, messages that state the behavioural claim ("compose endpoint returns scored outfit; latency test <800ms"). Claude Code's `/rewind` checkpoints do not cover Bash-made changes or subagent edits and are swept after 30 days; git is the only checkpoint that survives a process death, a worktree, and a resume.
- Subagents that need isolation get `isolation: worktree`; merging into main and removing the worktree happens in the same step that consumed their result, and the gate's DONE check refuses to end a run with a worktree or a `drive/*` branch still present.
- Every proof command writes an evidence file before its result is quoted in `STATUS.md`: header (command, cwd, UTC timestamp, git SHA, exit code), then the output tail, then screenshot paths. The gate checks the path exists; the judge reads the header.
- Any point is resumable when three things agree: HEAD, `STATE.md`, and `STATUS.md`. The resume protocol's step 3 is the consistency check.

### 4.9 Handing a run to the cloud (conditional)

Only when all three hold: the account has a claude.ai login (detected as in 4.1), the remaining phases need no local-only tool, and the run must outlive a shutdown or the owner has asked for it. Then:

1. Commit a copy of the skill into the repository: `.claude/skills/drive/` (or add the skill as a project plugin), plus any `.claude/agents/*.md` it needs and a `.mcp.json` for servers the run uses. Personal skills, user hooks and `claude mcp add` servers do not reach a cloud session.
2. Confirm the cloud environment's network allowlist covers what the run calls (Cloudflare API, package registries) or switch it to Custom with those domains.
3. Start with `claude --cloud "/drive --resume"` for a run to continue now, or `/schedule` a one-off routine ("in 6 hours, run /drive --resume in <repo>") for a run that should start later. Steer with `claude -p "<note>" --cloud <session-id>`; pull the result back with `claude --teleport <session-id>`.
4. Tell the prompt to commit to `main` and push; personal repositories pass the push check when `main` is unprotected and carries only the owner's commits. Then `git pull` locally before any local phase resumes.

With the owner's current Console-key authentication none of this is available; the skill detects that and writes one line to `STATE.md` and `DIGEST.md`: "Cloud hand-off unavailable with API-key login; run stays local under the supervisor." Managed Agents Outcomes is reachable with an API key but is a different harness that does not run this skill; not recommended.

### 4.10 A two-day greenfield run (fashion and outfit iOS app, Cloudflare backend)

Assumes a local background session on an awake Mac, Fable 5.1 orchestrating at `high`, Opus 5 for architecture and hard subtasks, Sonnet 5 for volume, and the gate above. Times are targets, not promises; each phase has its own `GOAL.md` with a bound.

| When | Phase | Goal (abridged; full form per 4.3) | Delegated in background | Owner sees |
|---|---|---|---|---|
| Day 1, 0h–3h | Intake, shape, research, spec | `docs/spec.md`, `docs/research-ledger.md` and three ADRs committed; the ledger cites at least 12 live sources with fetch timestamps; STATUS rows exist for every deliverable at `Missing`; bound 40 turns | `deep-research` workflow on market and comparable apps; Explore agents over CF and Swift references | `DIGEST.md` entry: scope, out-of-scope, decisions taken alone |
| Day 1, 3h–6h | Architecture, test design, skeletons | Backend and iOS design docs committed; an end-to-end test plan naming the refuting test per claim; `wrangler dev` health endpoint returns 200 in the transcript; Xcode project builds in the simulator with a screenshot in evidence; bound 60 turns | Opus 5 architect (two independent designs, then a comparison); Sonnet 5 scaffolding in worktrees, merged and removed the same step | Phase gate passes; commit history shows two commits |
| Day 1, 6h–14h | Implementation wave A (backend) | All backend STATUS rows at `Local Proof`; test suite exits 0; `wrangler deploy` to a dev environment and a live response captured (that row alone becomes `Live Proof`); bound 120 turns or 8 h | 3–5 Sonnet 5 implementers in worktrees per module; an Opus 5 adversarial reviewer per module with no exposure to the maker's transcript; `Monitor` on deploy logs | Evening `DIGEST.md`; STATE.md heartbeat every phase and at each gate block |
| Day 1 night–Day 2, 4h | Implementation wave B (iOS) | iOS rows at `Local Proof`: unit tests green, simulator boots, each screen has a screenshot in evidence, accessibility tree inspected for the three primary flows; bound 120 turns or 8 h | Sonnet 5 implementers; a vision verifier reading screenshots against the design doc; the simulator MCP driven by the main agent, never by a background subagent that cannot see the pane | Morning `DIGEST.md` |
| Day 2, 4h–8h | Live proof and adversarial review | Backend live on the dev URL with the smoke suite green against it; iOS e2e flow against the live backend recorded; `severe-testing` findings triaged with each fix carrying a refuting test; bound 80 turns | `severe-testing` skill in a subagent; `security-review` | Findings and fixes in `DIGEST.md` |
| Day 2, 8h–11h | UX verification loop, docs, lessons | Vision verifier passes all screens against design tokens or the remaining gaps are listed with reasons; README and setup docs verified by a fresh subagent that follows them from a clean clone; `docs/lessons.md` written and the skill's `references/lessons.md` updated; bound 60 turns | Fresh-context verifier following the README; Sonnet 5 doc writer | Final `DIGEST.md`; `STATE.md` "Next" empty; `.drive/ACTIVE` removed; run `Done` only if every row is at `Live Proof` or above where a live system exists, otherwise `Local Proof` with the reason stated |

Cost: Anthropic's published harness runs cost $124–$200 for four to six hours on Opus-class models. Fable 5.1 output is twice Opus per token and its cache reads are a quarter of Opus's, and this plan uses Sonnet for most volume, so a two-day run is plausibly in the several-hundred to low-thousands of dollars range on the API (opinion, estimate). For a headless launch set `--max-budget-usd`; for a background session there is no hard cap, so `PLAN.md` carries a per-phase turn bound and the gate's `GOAL.md` bound enforces it.

What the owner does: nothing, unless the run parks. He can `claude agents` to see the row state, `claude logs <id>` for recent output, or read `STATE.md` and `DIGEST.md` from any machine that has the repository. A run that needs a decision writes the single question at the top of `STATE.md` under "Blocked", makes every other progress it can, and only then ends its turn; it does not ask through `AskUserQuestion`.

### 4.11 Pre-flight checklist (the skill runs it, then records it in STATE.md)

`claude --version` at or above 2.1.257 (Fable 5.1) and a note if below 2.1.269 (no automatic goal retry); `jq` present; `git` clean or reconciled; a sleep assertion present or `caffeinate` started; `ANTHROPIC_DEFAULT_HAIKU_MODEL` set for the run; `CLAUDE_CODE_RETRY_WATCHDOG=1`; `.drive/` in `.gitignore` except the committed files; the project `CLAUDE.md` has a "Compact instructions" section; permission mode is `auto` and the skill's `allowed-tools` cover the proof commands; the cloud-availability check has run and its result is recorded.

## 5. Conditionals by project shape

**Greenfield app (iOS + Cloudflare).** Everything in 4.10. Must stay local: the simulator and Chrome MCPs are local, so the cloud path is disabled regardless of auth. Per-phase goals; two implementation waves; deploy-and-verify loop for the backend; a nightly-sized reset between waves (fresh session, state from files).

**Deep bug hunt.** One session, no phases, no `DIGEST.md`. The first goal is reproduction: "a script or test reproduces the failure deterministically in N of N runs, output in the transcript, and the reproducer is committed as a failing test". Only after that does the goal become "the reproducer passes 20 of 20 runs and no other test changed". Use `Monitor` for flaky reproduction loops (run the reproducer in a loop and stream failures) rather than repeated turns. Bound tightly (40 turns each). The gate's evidence rule matters most here: "fixed" without a committed refuting test is `Partial`. Keep it interactive or `--bg`; never scheduled.

**Feature on an existing product.** One or two phases with goals; worktree isolation for parallel implementers, merged and removed in the same step; the product's own test suite and its dev environment as the proof commands; `Live Proof` only after a deployed response. If the product has CI, the run drives it (`gh workflow run`, `gh run watch`) and does not wait for a scheduled poll.

**Migration or consolidation.** Staged cutover, each stage a phase with a goal that includes a rollback rehearsal in evidence. Soak is the one legitimate scheduled check: after cutover the run creates a Desktop scheduled task (API-key compatible, local) or a GitHub Actions cron that, every hour for the soak window, runs the health and error-rate checks, appends evidence, updates the `Soak` row, and rolls back through the platform's own tools on failure. The primary run ends the stage with `STATUS.md` `Soak` at `Partial` and `STATE.md` naming the scheduled check; `Operational` is claimed only by the check's final evidence. The gate blocks a "Done" until then.

**Research plus website.** Research via the `deep-research` workflow (resumable within the session; replay reruns changed agents). Website through a deploy-and-verify loop: deploy, then Lighthouse and Playwright screenshots against the live URL, then fix, with the vision verifier reading the screenshots. Shorter run, cloud-eligible in principle if the browser tooling exists there, but the Playwright and Chrome MCPs here are local, so it stays local by default too.

**Pure research report.** Single session, workflow fan-out, no Stop gate beyond `STATE.md` freshness; the goal is "report committed with every claim cited and cross-checked or listed as unverified".

**Refactor or simplification.** Behaviour-preserving loop: the goal is "tests identical and green before and after; diff reviewed by a fresh subagent". Short; the `simplify` pipeline already owns the mechanics.

**Ops or incident.** Loop until resolved with `Monitor` on logs and metrics; never a schedule; `Operational` requires the metric back in range for the stated window, observed live.

**Data pipeline.** As migration: staged, with a soak on a real run window.

**CLI tool or library.** Fast test-driven goals; one phase; publish-and-verify (install from the registry into a clean directory and run the smoke test) is the live proof.

## 6. Model and effort assignment

| Role | Model | Effort | Tools and notes |
|---|---|---|---|
| Orchestrator (the `/drive` session) | `fable` (Fable 5.1) | `high` for multi-day runs; the owner's saved `medium` for Fable 5.1 is fine for bounded runs. Set at launch (`--model fable --effort high`) rather than in skill frontmatter: the frontmatter `model` override lasts "for the rest of the current turn", and a goal loop is many turns | Full tools minus `AskUserQuestion` |
| Phase-goal judge (in the gate) | `claude-sonnet-5` | `low` | Nested `claude -p --bare --no-session-persistence --output-format json --json-schema`; reads files handed to it; no tools |
| `/goal` evaluator and background summariser | `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5` for the run | n/a | Replaces the deprecated `ANTHROPIC_SMALL_FAST_MODEL` Sonnet 4.5 pin; cheaper and current |
| Run auditor (phase-end state and evidence consistency) | `sonnet` | `low` | Read-only; predefined agent below |
| Soak checker (scheduled) | `sonnet` | `medium` | Desktop scheduled task prompt or Actions step; needs Bash and the platform CLI; writes evidence and may roll back |
| Implementers | `sonnet` | `medium` | Background, `isolation: worktree`, merged same step |
| Architecture, adversarial review, hard debugging | `opus` (Opus 5) | `high` | Owned by other components; listed for the model map |

Draft predefined agent, `~/.claude/agents/drive-run-auditor.md` (shipped separately from the skill, per the brief's packaging note):

```markdown
---
name: drive-run-auditor
description: Audits a /drive run's STATE.md, STATUS.md and evidence files for consistency with the working tree and git history. Read-only. Use at phase boundaries and before declaring a run done.
model: sonnet
effort: low
tools: Read, Grep, Glob, Bash
disallowedTools: Edit, Write, NotebookEdit, Agent
maxTurns: 30
---
You audit an autonomous run's bookkeeping. You change nothing.

Ground truth, in this order: the working tree and its tests; evidence files under .drive/runs/<id>/evidence and docs/proof; STATUS.md; STATE.md; prose in docs. When two disagree, the higher-ranked source wins and you report the disagreement.

Check every STATUS.md row: the status is one of Missing, Scaffold, Partial, Local Proof, Live Proof, Operational, Done; a row at Local Proof or above cites an evidence file that exists and whose header shows the command, timestamp, git SHA and exit code 0; a row at Live Proof or above cites a response from a deployed URL; a row's claim has at least one test that would fail if the claim were false (name it). Re-run the cheapest cited command for up to three rows you consider most at risk and compare the output.

Check STATE.md: updated_at is later than the last commit; "How to resume" names a working command; "Next" is ordered and concrete.

Check git: clean tree, HEAD on main, no worktrees, no drive/* branches, and that any shim, mock or fake used by tests is listed with where it is kinder than the real system.

Report as a table of findings with severity (blocks-done, lower-status, note), each with the file and line. End with one line: the highest status the evidence supports for the run as a whole.
```

## 7. Failure modes and anti-patterns

**The goal is judged from claims.** `/goal`'s evaluator sees the transcript, so "all tests pass" said confidently satisfies it. Mitigations: conditions phrased as commands whose output must appear; the gate's deterministic checks; the judge reading evidence files rather than the last message; the Fable 5 "audit each claim against a tool result" instruction in the skill's spine. Mirage risk that remains: the agent writes an evidence file that contains a claim instead of output. The evidence header format and the auditor's re-run of cited commands are the answer.

**Unbounded loops.** A goal with no turn clause, a fixed `/loop` with no end, a self-paced loop that keeps rescheduling. Mitigations: every `GOAL.md` has a turn-and-time bound; `/loop` tasks are recorded in `STATE.md` and cancelled at phase end; the 7-day cron expiry and the block cap are backstops, not the design.

**Waiting on cron for work the user implied.** "The nightly routine will deploy it" is not done. Mitigation: the skill's rule that a scheduled check is a `STATUS.md` row at `Partial` and the run is not `Done` until that row has evidence; schedules only for soak.

**Ending a session without writing state.** Mitigation: the gate blocks it. Residual: a process killed by SIGTERM or a crash runs no Stop hook; `SessionEnd` gets 1.5 s by default, enough to `touch` a marker, not to write a considered state file. Hence the rule that `STATE.md` is rewritten at every phase boundary and every green run, not only at the end, so a hard kill loses at most one step.

**Relying on chat history as memory.** Compaction drops it; the skill body is truncated to its first 5,000 tokens; a fresh session has none of it. Mitigation: the file layout, the compact-source `SessionStart` hook, the CLAUDE.md compact instructions, and a spine short enough to survive.

**Laptop closed.** A background session pauses in sleep and resumes on wake; a Desktop scheduled task skips its fire and catches up once; `/loop` fires nothing. Mitigation: pre-flight keep-awake check; `STATE.md` states the fact; cloud only when available and appropriate.

**Auth and billing kills.** With a Console key there is no usage-limit wait, only spend limits and rate limits; a spend-limit 429 fails immediately even with the watchdog, and `/goal` clears on an exhausted balance. Mitigation: `StopFailure` logging, `RETRY_WATCHDOG` for capacity errors, and the resume protocol, which makes a restart after a top-up a `claude --resume ... --bg "/drive --resume"` away.

**Silent model switch.** A classifier fallback moves the session to Opus 4.8 for the rest of the run. Mitigation: the `PostModelSwitch` hook writes it into `STATE.md`; the resume protocol checks `host:` and switches back with the launch flag where appropriate.

**Background subagent limitations.** A background subagent cannot use the interactive panes (simulator, browser preview) that live in the main session's desktop pane, and monitors it starts die with it. Mitigation: vision verification runs in the main agent or a foreground subagent; monitors are owned by the main agent.

**Stale STATUS after a subagent merge.** A worktree subagent finishes, the merge lands, and nobody updates the row. Mitigation: the step that consumes a subagent's result also writes the row and the evidence path, in that order; the gate catches a `Local Proof` row without a file.

**Resuming a huge idle session.** Cache repay of hundreds of thousands of tokens at Fable prices. Mitigation: prefer a fresh session after two compactions or 400K tokens; the files make that safe.

**Over-prescription.** Anthropic's Fable guidance says step-by-step scaffolding written for older models reduces Fable output quality. The gate, the file layout and the goal form are invariants, not procedures; the skill should state goals and constraints and let the model plan the path.

## 8. Open questions and trade-offs

1. **Can Claude set `/goal` itself?** Not documented; no `Goal` tool exists; `/goal` is not among the built-ins named as reachable through the Skill tool. Recommendation: assume no, own the loop with the gate, and use `/goal` only in the `-p` launch recipe. Verify at build with a one-line test.
2. **Does the hook subprocess inherit the settings `env` block (the API key) for the nested `claude -p --bare` judge?** Likely, since Claude Code applies `env` to its own process and hooks are children, but unverified. Fallback: the judge calls the API with the SDK via a small script, or the gate exports the key from the shell profile. Verify at build.
3. **`${CLAUDE_SKILL_DIR}` in frontmatter hooks** is not documented; `$HOME/.claude/skills/drive/...` in shell form is the safe path. Verify at build whether the placeholder expands there.
4. **Skill-frontmatter hooks after `--resume` into a new process.** They are registered in memory for the session; a new process presumably starts without them until `/drive --resume` is invoked, which is why the resume recipe always invokes the skill. Verify.
5. **Whether custom prompt Stop hooks see the conversation** the way `/goal`'s evaluator does. The gate sidesteps this by feeding files to a nested `-p` call; if prompt hooks do see the transcript, a `type: prompt` hook with `model: claude-sonnet-5` becomes a cheaper second judge.
6. **Cost visibility inside a background session.** No hook receives spend; `--max-budget-usd` is print-mode only. The turn bounds in `GOAL.md` are the substitute. A `StopFailure` on `billing_error` is the only hard signal.
7. **Committing evidence.** Trade-off between the owner's precedence for proof artifacts and his dislike of stray files. Recommendation above: small curated proof committed under `docs/proof/`, bulk under git-ignored `.drive/`. The coordinator should align this with the state-tracking report.
8. **Cloud at all.** Requires the owner to switch to a claude.ai login, which also changes billing and enables usage-limit waits. That is one decision for him, once, and the skill should surface it only when a run would benefit (a shape with no local-only tools and a multi-day horizon). My recommendation is to ship v1 local-only with detection.
9. **`Sonnet 4.8`.** The brief names it; the live model list has Sonnet 5 as the current Sonnet at $2/$10. Use the `sonnet` alias in agents and `claude-sonnet-5` where a full ID is needed, and note the discrepancy to the owner once.
10. **Version.** The owner's 2.1.263 lacks goal auto-retry (2.1.269). `claude update` before the first long run.

## 9. Skill text candidates

**Spine, first lines of SKILL.md**

> You are running autonomously; the owner is not watching and cannot answer mid-run. Truth lives in files: STATE.md, STATUS.md, GOAL.md, evidence under .drive/runs/<id>/, and git. Chat history is not memory. Begin every run, including a resumed one, with the resume protocol in this file. End a turn only when the Stop gate lets you: state fresh, every claim backed by an evidence file that exists, tree clean on main, phase goal met.

**Resume protocol**

> At start: read .drive/ACTIVE and STATE.md. Run `git status --porcelain`, `git log --oneline -10`, `git worktree list`. A dirty tree or a leftover worktree is your first task: inspect, commit or revert, remove. Re-read GOAL.md and PLAN.md and check them against the tree; where STATE.md and the tree disagree, the tree wins and you rewrite STATE.md. Re-run the phase's cheapest proof command before doing anything new. Record the host, model and time in STATE.md, then continue from "Next".

**Writing a phase goal**

> Write GOAL.md so a reader with no tools could check it from the transcript: one measurable end state per clause, the exact command that proves it, and the requirement that its output appears. Add the constraints that protect the ladder: no test deleted or weakened, no file outside scope, nothing Live Proof without a deployed response. End with a bound: "or stop after N turns or H hours; if you stop on the bound, say why under Stopped early in STATE.md."

**Evidence before status**

> A status moves up only after an evidence file exists: header with command, cwd, UTC time, git SHA, exit code; then the output tail; then screenshot paths. Write the file, then the STATUS.md row that cites it, in that order. Local-only work is never Live Proof. A shim that is kinder than the real system (unlimited parameters, no auth, no latency) certifies nothing; name where it is kinder in the evidence.

**Progress claims**

> Before reporting progress, audit each claim against a tool result from this session. Only report work you can point to evidence for; if something is not yet verified, say so. If tests fail, say so with the output; if a step was skipped, say that.

**Commits as checkpoints**

> Commit to main at every phase boundary and every green run, small, with a message that states the behavioural claim. When a subagent worked in a worktree, merge and remove the worktree in the same step you consume its result, then write its STATUS row. Never end a run with a worktree, a drive/* branch or a dirty tree.

**Waiting**

> Do not wait for what you can drive: deploy and verify, run and query, trigger CI and watch it. When you must wait, start a Monitor that prints one line on change and keep working. For a wait longer than a monitor's life, a self-paced /loop with a stop condition, recorded in STATE.md. A schedule is only for a soak period with no signal to wait on, and a scheduled check is a STATUS row at Partial until it has written evidence; the run is not Done before that. Never report "it will happen when the cron runs" as done.

**Context**

> Send heavy reading to subagents and receive summaries with paths. Read large files in ranges. At each phase boundary rewrite STATE.md and DIGEST.md; they, not this conversation, are what the next phase reads. After a compaction, re-read STATE.md, STATUS.md and GOAL.md before acting.

**Where the run lives**

> Prefer a local background session under the supervisor: it survives closing the terminal and sleeps with the machine. Check for a sleep assertion (`pmset -g`) and start `caffeinate -is` if none exists; write in STATE.md that a closed lid pauses the run. Hand a run to the cloud only if the account has a claude.ai login, the remaining phases need no local-only tool, and the run must outlive a shutdown; then commit the skill into the repository's .claude/skills first, because personal skills do not load there. With API-key login, record that cloud hand-off is unavailable and continue locally.

**Stopping**

> Stop for one of three reasons only: the run is Done by the ladder and the gate agrees; a bound was reached and STATE.md says why; a decision only the owner can take, written as one question at the top of STATE.md after you have finished everything that does not depend on it. Never stop to ask "shall I". Never mark Done because a scaffold, a README or a command exists.

**Bug hunts**

> First goal: reproduce deterministically, and commit the reproducer as a failing test. Only then fix. Second goal: the reproducer passes 20 of 20 and no other test changed. Use a Monitor to loop a flaky reproducer instead of spending turns.

**Migrations**

> Cut over in stages. Each stage rehearses its rollback in evidence before it runs. After cutover, create the soak check (Desktop scheduled task locally, or an Actions cron) that runs the health checks hourly, appends evidence, updates the Soak row, and rolls back through the platform's own tools on failure. Operational is claimed by the soak's final evidence, not by you.

**Launch recipes (references/long-running.md)**

> Background: `claude --bg --name drive-<slug> "/drive <goal>"`. Headless: `claude -p "/drive <goal>" --output-format stream-json --verbose --permission-mode auto --permission-prompts none --max-turns 400 --max-budget-usd <n>`. Resume: `claude --resume <full-id> --bg "/drive --resume"`. For every form export `CLAUDE_CODE_RETRY_WATCHDOG=1 CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=20 BASH_DEFAULT_TIMEOUT_MS=600000 ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5`.

**Compact instructions for the project CLAUDE.md**

> When compacting, keep exactly: the current phase and GOAL.md path, the ordered next three steps, the list of files modified in this phase, every proof command and its last result, and any decision taken without the owner. Drop tool output bodies; keep their evidence file paths.
