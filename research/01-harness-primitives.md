# Harness primitives and packaging for `/drive`

Researcher report, component: Claude Code harness primitives and how to package the skill.
Verified against code.claude.com docs and the local Claude Code 2.1.263 install on 2026-09-14.
Raw docs were fetched as markdown from `https://code.claude.com/docs/en/<slug>.md` (the index the
brief cites, `/docs/en/llms.txt`, returns 404; the working index is `https://code.claude.com/docs/llms.txt`).

## 1. Executive opinion

The skill should be packaged as a **skills-directory plugin**: the existing `~/Projects/drive/skill/`
directory gets a `.claude-plugin/plugin.json`, keeps `SKILL.md` at its root, and gains `agents/`,
`hooks/`, and `scripts/`. One symlink, `~/.claude/skills/drive -> ~/Projects/drive/skill`, makes Claude
Code load it as `drive@skills-dir` with no install step, and the agents, hooks, and skill travel in the
same git repo. This is the only packaging option in which agents ship with the skill; loose files in
`~/.claude/agents/` would be a second thing to install, and project-level `.claude/agents/` written at
run time would leave artifacts in the owner's repos.

The orchestrator must run in the **main conversation**, never as a `context: fork` skill or a subagent.
The docs are explicit that every subagent loses the `Workflow`, `ScheduleWakeup`, and `AskUserQuestion`
tools, and `/goal` is a main-session Stop hook. A forked `/drive` would be an orchestrator that cannot
orchestrate.

The "keep going until verified done" loop should be the skill's own **Stop hook**, registered from
`SKILL.md` frontmatter and driven by a script that reads `.drive/STATE.md`. That is what `/goal` is
underneath, but under the skill's control, deterministic, and able to distinguish "done" from "waiting
on background subagents". `/goal` remains useful as a belt-and-braces condition the owner can type, and
its evaluator can be moved off Haiku with `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5`. Routines are
unavailable on this machine (Console API-key login), and `/loop` is a timer, not a completion loop.

Predefine eight subagents (researcher, architect, test-designer, implementer, verifier, ui-verifier,
grader, investigator). Only the verifier gets `memory: user`; cross-project *lessons* belong in the skill
repo, not in agent memory. Use the Workflow tool for read-only fan-outs (review panels, research sweeps,
hypothesis tournaments) and plain Agent calls for anything that edits the checkout; the owner's own
memory files record a workflow fan-out that wedged on build locks and another that drifted 72 files off
scope. Worktrees are for concurrent implementers only, and merge-plus-remove is part of the same step.

One correction to the brief: on the Anthropic API the `opus` and `sonnet` aliases now resolve to Opus 5
and Sonnet 5. "Sonnet 4.8" does not appear in the docs or the bundled model table.

## 2. What the post says, and a critique

The post is right about the architecture at the level of slogans and wrong or loose at the level of
mechanism, which is the level a skill has to live at.

It is right that the verifier should be a separate context from the maker. The docs support this
structurally: a non-fork subagent starts with a fresh context that contains only its system prompt, the
delegation message, CLAUDE.md, and git status; it does not see the parent's reasoning. It is right that
`/goal`, dynamic workflows, and routines are the three loop primitives, and that state should live in
files because context does not survive. It is right that `isolation: worktree` exists and cleans up
unchanged worktrees.

It is wrong to present Haiku as the grader for this owner, and the docs give a clean alternative: prompt
hooks accept a `model` field, and `ANTHROPIC_DEFAULT_HAIKU_MODEL` retargets the `/goal` evaluator (the
docs warn it also retargets every other background use of the small model, which is acceptable here).

It exaggerates worktrees. The post says "the best one merges" and "a failed phase doesn't poison the
rest" as if merging were free. The docs say a subagent worktree branches from the repository's default
branch, not from `HEAD`, and that a worktree with changes stays on disk until a periodic sweep. For an
owner who commits straight to `main` and forbids leftover worktrees, the merge and the removal are the
hard part, and the post skips them.

It presents dynamic workflows as the general orchestration substrate. The docs and the bundled
`workflow-authoring` reference say workflows are for structure the script can hold (fan-out, adversarial
verify, loop-until-dry) and warn that `isolation: 'worktree'` per agent is expensive; the owner's own
notes record two failed attempts to use workflows for scoped implementation. The right reading is
narrower: workflows for read-only breadth, Agent calls for edits.

It says "Fable 5 was built to run for days" but the mechanics that make a day-long run survive are
absent from the post: skills are re-attached after compaction only to their first 5,000 tokens, the
`/goal` evaluator only sees the transcript, Stop hooks have an eight-block cap, and `claude -p` gives up
on idle background work after ten minutes unless told otherwise. Those limits shape the design more than
the model's stamina does.

Its five-stage memory ladder (fail, investigate, verify, distill, consult) is a good rubric and maps
directly onto what the investigator agent should produce. Its STATE.md template is fine as a starting
shape but needs a machine-readable header so a hook can read it.

## 3. Verified facts

Each item is a fact from the linked page unless marked otherwise. Version numbers are from the docs'
own "requires vX" notes.

### Subagents (`https://code.claude.com/docs/en/sub-agents.md`)

- Locations and precedence: managed settings, then `--agents` JSON, then `.claude/agents/`, then
  `~/.claude/agents/`, then a plugin's `agents/`. All scanned recursively; identity comes only from the
  `name` field. Plugin agents are scoped: `agents/review/security.md` in plugin `my-plugin` registers as
  `my-plugin:review:security`.
- Hot reload: `~/.claude/agents/` and `.claude/agents/` are watched and changes apply within seconds,
  except the first file in an `agents` directory that did not exist at session start (restart needed).
  `~/.claude/agents/` does not exist on this machine today. Plugin `agents/` and `hooks/` changes need
  `/reload-plugins` or a restart; a plugin skill's `SKILL.md` edits apply immediately.
- Frontmatter fields: `name`, `description` (both required), `tools`, `disallowedTools`, `model`
  (`sonnet|opus|haiku|fable|<full id>|inherit`), `permissionMode`, `maxTurns`, `skills`, `mcpServers`,
  `hooks`, `memory` (`user|project|local`), `background`, `effort` (`low|medium|high|xhigh|max`),
  `isolation: worktree`, `color`, `initialPrompt`, `experimental.cacheTtl`.
- Plugin agents support `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`,
  `skills`, `memory`, `background`, `isolation`. They ignore `hooks`, `mcpServers`, `permissionMode`
  (`plugins-reference.md`). A plugin agent with unparseable frontmatter still loads under its filename.
- Model resolution (v2.1.251 and later): per-invocation `model` parameter, then frontmatter `model`,
  then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main conversation's model. The per-call value persists
  when the subagent is resumed. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` overrides everything.
- Subagents inherit the main conversation's extended-thinking setting; there is no per-agent thinking
  field. Frontmatter `effort` overrides the session level but not `CLAUDE_CODE_EFFORT_LEVEL`.
- Tool filters: every subagent loses `Agent` (only at the depth limit), `AskUserQuestion`,
  `EndConversation`, `EnterPlanMode`, `ExitPlanMode` (unless `permissionMode: plan`), `ScheduleWakeup`,
  `TaskOutput`, `WaitForMcpServers`, and `Workflow`. A background subagent additionally keeps only
  `Read, Grep, Glob, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill,
  ToolSearch, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage, Artifact` plus all MCP tools.
- In interactive sessions fork mode is on by default (v2.1.232+), which means Claude's spawned subagents
  run in the background and the `run_in_background` parameter is removed. In `-p` mode fork mode is off
  and Claude chooses foreground when it needs the result.
- `skills:` injects the full content of each listed skill at startup, not the description. Skills with
  `disable-model-invocation: true` cannot be preloaded.
- `memory: user` writes to `~/.claude/agent-memory/<name-of-agent>/`; `project` to
  `.claude/agent-memory/<name>/`; `local` to `.claude/agent-memory-local/<name>/`. The first 200 lines or
  25 KB of that directory's `MEMORY.md` is injected into the subagent's system prompt, Read/Write/Edit are
  auto-enabled, and the whole feature is off when `autoMemoryEnabled` is false. The main conversation's
  auto memory is never loaded into a non-fork subagent.
- `maxTurns` returns output marked partial (v2.1.246+) with a hint that `SendMessage` can continue it.
- Default nesting depth is three layers; `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` changes it. Default
  concurrency is 20 running subagents; `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` changes it; ultracode
  sessions are exempt.
- Frontmatter `hooks` on an agent run only while that agent runs; a `Stop` entry is converted to
  `SubagentStop`. Project-level agent hooks need workspace trust; user-level ones do not.
- `permissionMode` in frontmatter is ignored when the main conversation is in `bypassPermissions`,
  `acceptEdits`, or auto mode. The owner's `settings.json` sets `permissions.defaultMode: auto`.
- Named subagents: when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, an Agent call with a `name` launches a
  teammate instead of a subagent unless the call is a fork or passes `isolation` (`agent-teams.md`).
  That variable is not set on this machine.
- Subagent output is scanned before Claude reads it; instruction-shaped text gets a marker line.
- The combined agent descriptions carry a 15,000-token warning threshold.

### Agent tool (this session's schema, plus docs)

- Parameters: `subagent_type`, `prompt`, `description`, `model` (`sonnet|opus|haiku|fable`),
  `run_in_background`, `isolation` (`worktree|remote`). A custom agent is addressed by its `name`, or by
  `<plugin>:<name>` for plugin agents. `subagent_type: "fork"` inherits the whole conversation.

### Skills (`https://code.claude.com/docs/en/skills.md`)

- Frontmatter: `name`, `description`, `when_to_use`, `argument-hint`, `arguments`,
  `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`, `model`, `effort`,
  `context`, `agent`, `background`, `hooks`, `paths`, `shell`, `metadata`, `license`, `compatibility`.
- Command name: for a personal skill directory the command is the directory name; for a plugin skill it
  is `/<plugin>:<name>`, and the bare `/<name>` also works unless another command already uses it.
- `$ARGUMENTS` is the full argument string; `$0`, `$1` and `$ARGUMENTS[N]` are positional with
  shell-style quoting; `arguments: [a, b]` declares `$a`, `$b`. If no placeholder consumes them, Claude
  Code appends `ARGUMENTS: <text>`.
- Substitutions: `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_SKILL_DIR}`,
  `${CLAUDE_PROJECT_DIR}`, and in plugin skills `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}`.
  They are substituted in the body and in `allowed-tools` Bash rules.
- Dynamic injection: `` !`command` `` at line start or after whitespace runs before the content is sent.
  A failing command (non-zero exit, except exit 1 from search/comparison commands) **aborts the whole
  invocation**; append `|| true`. Injected commands never prompt; an ask or deny rule aborts. Output is
  inserted once and not rescanned. Runs in the session shell's cwd under the Bash tool's 2-minute timeout.
- Skill content enters the conversation once and stays. Re-invoking with identical rendered content adds
  a short "already loaded" note; different arguments or different injected output append the full content
  again. **After auto-compaction, each invoked skill is re-attached keeping only its first 5,000 tokens,
  within a shared 25,000-token budget filled from the most recently invoked skill.**
- `allowed-tools` grants permission for the invoking turn only and clears on the next user message;
  `disallowed-tools` removes tools from the pool for the same span. The docs name `AskUserQuestion` as the
  example for autonomous skills.
- `disable-model-invocation: true` removes the description from context, blocks preloading, and blocks
  scheduled-task invocation. Keep `SKILL.md` under 500 lines. Skill listing descriptions are truncated
  at 1,536 characters and the listing budget is 1% of the context window.
- `context: fork` runs the skill body as the task prompt inside a subagent of type `agent` (default
  `general-purpose`), in the background by default (`background: false` waits), with the narrower
  background tool set, and its edits fall outside `/rewind` checkpoints. It is not a conversation fork.
- `hooks` in skill frontmatter register on invocation and stay for the rest of the session; `once: true`
  removes a hook after its first successful run (`hooks.md`, "Hooks in skills and agents").
- `paths:` limits automatic activation to work on matching files.

### Hooks (`https://code.claude.com/docs/en/hooks.md`, `hooks-guide.md`)

- Handler types: `command`, `http`, `mcp_tool`, `prompt`, `agent`. Stop and SubagentStop accept all
  five. SessionStart accepts only `command` and `mcp_tool`.
- Stop input includes `stop_hook_active`, `last_assistant_message`, `background_tasks` (with `type`
  values such as `subagent`, `workflow`, `shell`) and `session_crons`. Output `{"decision":"block",
  "reason":...}` keeps Claude working with the reason as its next instruction; exit code 2 with stderr
  does the same; `hookSpecificOutput.additionalContext` continues without an error label. Claude Code
  overrides the hook after eight consecutive blocks; `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` raises the cap.
- Prompt hooks default to Haiku and accept `model`; the response is `{ok, reason, impossible}`. Agent
  hooks are experimental, default 60 s and up to 50 tool turns.
- `SubagentStop` fires per agent type (matcher on `name`, or `^plugin:name$` for plugin agents) and
  receives `agent_transcript_path` and `last_assistant_message`; `decision: block` keeps the subagent
  running. `SubagentStart` can inject `additionalContext` into the subagent.
- `TaskCompleted` fires when `TaskUpdate` marks a task complete; exit 2 refuses the completion and
  returns stderr to the model.
- `SessionStart` with matcher `compact` fires after every compaction; stdout is added to context.
- Command hooks: use exec form (`command` plus `args: []`) whenever the path uses
  `${CLAUDE_PLUGIN_ROOT}` or `${CLAUDE_PROJECT_DIR}`. `${CLAUDE_PROJECT_DIR}` does not follow worktrees;
  the hook input's `cwd` does.

### `/goal` (`https://code.claude.com/docs/en/goal.md`)

- Session-scoped prompt-based Stop hook. Condition up to 4,000 characters. Evaluator is the "small fast
  model", Haiku by default, retargeted by `ANTHROPIC_DEFAULT_HAIKU_MODEL` (a full model name). It sees
  only the transcript and calls no tools. Verdicts: not yet met, met, impossible.
- Works with `claude -p "/goal ..."`; use `--output-format stream-json --verbose` to see progress.
  Restored on every resume route (v2.1.239+). Cleared by auth failure, exhausted credits, unrecoverable
  context overflow, or unavailable model; other errors retry or pause.
- Background work defers evaluation. Check-ins at 30 min, then 1 h, then every 2 h; at most three idle
  check-ins per goal between prompts (v2.1.246+); in `-p` check-ins arrive only at turn end.
  `CLAUDE_CODE_GOAL_CHECKIN_MINUTES=0` turns them off. Several turns without tool use stop the loop.
- Unavailable when `disableAllHooks` is true or under `allowManagedHooksOnly`.
- The docs do not list `/goal` among built-in commands reachable through the Skill tool (only `/init`
  and `/security-review` are named); whether the model can set a goal itself is unverified.

### `/loop`, `ScheduleWakeup`, cron (`https://code.claude.com/docs/en/scheduled-tasks.md`)

- `/loop` is a bundled skill; fixed interval maps to `CronCreate`, no interval means Claude self-paces
  between 1 minute and 1 hour with `ScheduleWakeup`, and `ScheduleWakeup({stop: true})` ends it. Tasks
  fire only when the session is idle, expire after 7 days, and a self-paced loop is not restored on
  resume. `ScheduleWakeup` is removed from every subagent.
- Cloud routines: minimum interval 1 hour, fresh clone, no local files, require claude.ai subscription
  login. `routines.md`: `/schedule` is hidden when authenticated with a Console API key or when
  `ANTHROPIC_API_KEY` is set. The owner's `settings.json` has `forceLoginMethod: console` and an
  `ANTHROPIC_API_KEY` in its `env` block, so **routines are unavailable on this machine**.

### Dynamic workflows (`https://code.claude.com/docs/en/workflows.md`; bundled `/workflow-authoring`)

- Opt-in: the `ultracode` keyword typed by a human, a plain request for a workflow, `/effort ultracode`,
  or a skill that instructs it. The keyword does not trigger from `-p` prompts, scheduled prompts, or
  relayed content. In `-p` and the SDK the launch goes through permission rules (`Workflow` or
  `Workflow(<name>)` allow rule, auto mode, bypass, or a PreToolUse hook). The owner's settings have
  `skipWorkflowUsageWarning: true`.
- Script API: `export const meta = {name, description, phases?, whenToUse?}` as a pure literal first;
  `agent(prompt, {label, phase, schema, model, effort, isolation:'worktree', agentType})`,
  `pipeline(items, ...stages)` (no barrier between stages), `parallel(thunks)` (barrier, nulls for
  failures), `phase()`, `log()`, `args`, `budget.{total,spent(),remaining()}`, `workflow(nameOrRef,
  args)` one level deep. Plain JavaScript, no TypeScript, no `Date.now()`/`Math.random()`/`new Date()`,
  no filesystem. `agentType` resolves custom agents from the same registry as the Agent tool.
- Limits: `min(16, CPUs-2)` concurrent agents, 1,000 agents per run, 4,096 items per call. Size
  guideline default `medium` (aim under 15 agents); `Large workflow` warning past 25 agents or 1.5M
  projected tokens. Intermediate results stay in script variables; only the return value reaches context.
- Resume: relaunch with `{scriptPath, resumeFromRunId}`; the longest unchanged prefix of `agent()` calls
  returns cached results; a failed agent and everything after it rerun. `journal.jsonl` in the transcript
  directory holds each agent's return value.
- Structured output: `schema` forces a `StructuredOutput` tool call with validation and up to five
  retries (`MAX_STRUCTURED_OUTPUT_RETRIES`).
- No mid-run user input; agent permission prompts can pause a run. In auto mode the classifier can block
  an `agent()` call, which resolves to `null`.
- Same-prefix fan-out agents are staggered up to 5 s so they read the first agent's prompt cache.
- Workflow agents can reach session MCP tools via `ToolSearch`.

### Memory (`https://code.claude.com/docs/en/memory.md`, `claude-directory.md`)

- CLAUDE.md files load from cwd upward, concatenated root-first; `.claude/rules/*.md` load at launch or
  on matching `paths`; `~/.claude/rules/` applies everywhere. Subagents receive the whole CLAUDE.md
  hierarchy (Explore and Plan excepted).
- Auto memory lives at `~/.claude/projects/<project>/memory/`, keyed by git repository, machine-local,
  first 200 lines or 25 KB of `MEMORY.md` loaded per session, topic files read on demand. Claude decides
  what to save; it skips what CLAUDE.md already says or what the code shows.
- Agent memory (`memory:`) is a separate directory per agent; `claude-directory.md` calls `memory:
  project` shareable with a team and `memory: user` cross-project.

### Models and effort (`https://code.claude.com/docs/en/model-config.md`; bundled `/claude-api`, cached 2026-06-24)

- Aliases on the Anthropic API: `fable` → Fable 5.1 (v2.1.257+), `opus` → Opus 5, `sonnet` → Sonnet 5,
  `haiku` → Haiku 4.5, `best` → same as `fable` where available. Opus 4.8 exists as
  `claude-opus-4-8` and is the cybersecurity-flag fallback target; biology flags fall to Opus 5.
- Prices per million tokens (input/output): Fable 5.1 $10/$50 (cache reads $0.25); Opus 5 and Opus 4.8
  $5/$25; Sonnet 5 $2/$10; Sonnet 4.6 $3/$15; Haiku 4.5 $1/$5. **No Sonnet 4.8 appears in either the
  docs or the model table.**
- Effort levels `low|medium|high|xhigh|max` on Fable 5/5.1, Opus 5, Sonnet 5, Opus 4.8/4.7; default
  `high`; `max` "prone to overthinking". Skill and subagent frontmatter `effort` overrides the session
  level. `ultracode` sends `xhigh` and turns on automatic workflow orchestration.
- Fable 5.1 API notes from the bundled skill: thinking always on; forced `tool_choice` (`any`/`tool`)
  returns 400; classifier refusals return `stop_reason: refusal`; Claude Code re-runs flagged requests on
  Opus automatically.
- Env: `ANTHROPIC_DEFAULT_{FABLE,OPUS,SONNET,HAIKU}_MODEL` pin aliases; `ANTHROPIC_SMALL_FAST_MODEL` is
  deprecated in favor of `ANTHROPIC_DEFAULT_HAIKU_MODEL`. The owner's `settings.json` still sets
  `ANTHROPIC_SMALL_FAST_MODEL=claude-sonnet-4-5-20250929[1m]`, and a string search of the 2.1.263 binary
  shows that variable is read before `ANTHROPIC_DEFAULT_HAIKU_MODEL`, so today his `/goal` evaluator and
  prompt hooks run on Sonnet 4.5.
- Owner's model settings: session model `claude-fable-5-1[1m]`, global `effortLevel: high`, per-model
  `claude-fable-5-1: medium`, `alwaysThinkingEnabled: true`.

### Plugins and packaging (`https://code.claude.com/docs/en/plugins.md`, `plugins-reference.md`)

- Any folder under a skills directory containing `.claude-plugin/plugin.json` loads as
  `<name>@skills-dir` on the next session, discovered in place, no marketplace, no install. Personal
  scope (`~/.claude/skills/`) has none of the project-scope trust restrictions. `claude plugin init
  <name> --with agents hooks` scaffolds one; `claude plugin disable <name>@skills-dir` turns it off.
- A plugin with `SKILL.md` at its root and no `skills/` directory loads it as a single skill named by the
  frontmatter `name`. Component directories (`agents/`, `hooks/`, `workflows/`, `scripts/`, `bin/`) sit
  at the plugin root, never inside `.claude-plugin/`. A `CLAUDE.md` at plugin root is not loaded.
- Component paths must stay inside the plugin; symlinks leading outside are refused. Plugin `hooks.json`
  and skill bodies get `${CLAUDE_PLUGIN_ROOT}`. Plugins may also ship `workflows/*.js`, invoked as
  `/<plugin>:<meta.name>`.
- Empirically verified here: a scratch plugin laid out as `skill/{.claude-plugin/plugin.json, SKILL.md,
  agents/*.md, hooks/hooks.json, scripts/}` passes `claude plugin validate --strict --json` with zero
  warnings on 2.1.263. Not yet verified: that discovery works when `~/.claude/skills/drive` is a symlink
  (the owner's existing skills are all symlinks into `~/Projects/*` and load as plain skills).

### Headless (`https://code.claude.com/docs/en/headless.md`)

- `claude -p "/drive <goal>"` expands user-invoked skills. `--permission-mode auto` plus
  `--permission-prompts none` (v2.1.259+) denies anything that would prompt and removes
  `AskUserQuestion`. A `-p` run stays open for background subagents and workflows, but gives up after 10
  minutes of idle waiting unless `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` is raised or set to 0. `--bare`
  skips skills discovery except `/skill-name` resolution and skips agents entirely; do not use it.
- `--agent <name>` runs the main thread as a named agent whose system prompt replaces Claude Code's;
  `initialPrompt` in that agent's frontmatter is auto-submitted first and is prepended to the user prompt.

### Owner's machine (inspected)

- Claude Code 2.1.263, arm64. `~/.claude/skills/` holds symlinks into `~/Projects/*/skill` (deep-research,
  audit, rust-refinement, google-dev-docs-style) and into `~/Projects/severe-testing` (SKILL.md at repo
  root). None ship Claude agents; each has an `agents/openai.yaml` for Codex only. Two plugins are
  installed from local directory marketplaces (`arcwell@arcwell-local`, `ferrite@ferrite-labs`); the
  arcwell plugin uses `hooks/hooks.json` with a `SessionStart` command hook.
- `~/Projects/drive/skill/` already contains empty `agents/`, `references/`, `templates/` directories.
- No `~/.claude/agents/`, `~/.claude/workflows/`, or `~/.claude/rules/` exists.
- Memory notes from the owner's `codex-swift` project record: a workflow that fanned out parallel
  build/test agents into one checkout wedged on the SwiftPM `.build` lock; a hardened sequential workflow
  then drifted from 5 requested items to 72 files and five unrequested features (5.25M tokens). Read-only
  adversarial review panels "repeatedly caught real defects the implement agents' own green tests masked".

## 4. Detailed spec

### 4.1 Repository layout and packaging

Make `~/Projects/drive/skill/` the plugin root. The repo:

```
~/Projects/drive/
├── README.md
├── LICENSE
├── install.sh                 # creates the symlink, validates, prints checks
├── uninstall.sh
├── research/                  # these reports; not loaded by Claude Code
└── skill/                     # PLUGIN ROOT, symlinked to ~/.claude/skills/drive
    ├── .claude-plugin/
    │   └── plugin.json
    ├── SKILL.md               # the /drive skill (loads as /drive:drive and bare /drive)
    ├── agents/
    │   ├── researcher.md      # drive:researcher
    │   ├── architect.md       # drive:architect
    │   ├── test-designer.md   # drive:test-designer
    │   ├── implementer.md     # drive:implementer
    │   ├── verifier.md        # drive:verifier
    │   ├── ui-verifier.md     # drive:ui-verifier
    │   ├── grader.md          # drive:grader
    │   └── investigator.md    # drive:investigator
    ├── hooks/
    │   └── hooks.json         # plugin-wide: SessionStart(compact) re-inject
    ├── scripts/
    │   ├── stop-gate.sh       # Stop hook: refuses to end the turn while STATE.md says running
    │   ├── reinject-state.sh  # prints .drive/STATE.md after compaction
    │   ├── task-gate.sh       # TaskCompleted hook: no verdict file, no completion
    │   └── worktree-land.sh   # merge a subagent worktree into main and remove it
    ├── workflows/
    │   ├── review-panel.js    # /drive:review-panel  adversarial verification fan-out
    │   └── research-sweep.js  # /drive:research-sweep
    ├── references/
    │   ├── phases.md          # the long procedural narrative, read on demand
    │   ├── shapes.md          # conditionals per project shape
    │   ├── verification.md    # status ladder, refutation rubric
    │   ├── models.md          # routing table
    │   └── lessons.md         # cross-project lessons, appended by the investigator step
    └── templates/
        ├── STATE.md
        ├── SPEC.md
        ├── verdict.json
        └── lesson.md
```

`plugin.json` (validated shape):

```json
{
  "name": "drive",
  "version": "0.1.0",
  "description": "Turn a high-level goal into a complete, verified, autonomous execution run.",
  "author": { "name": "Chris Chabot", "url": "https://github.com/chrischabot" },
  "license": "MIT",
  "keywords": ["orchestration", "autonomous", "verification"]
}
```

Why this and not the alternatives:

(a) Symlinking `agents/*.md` into `~/.claude/agents/` gives hot reload and lets agents carry `hooks`,
`mcpServers`, and `permissionMode`. It costs a second install step per agent, puts eight bare-named
agents into every session's agent listing with no namespace, and gives no single switch to turn them off.
The `permissionMode` field is moot for this owner (auto mode makes the harness ignore it), and agent-level
hooks are not needed because `disallowedTools` covers the read-only verifier.

(b) The skills-directory plugin needs one symlink, namespaces everything as `drive:*`, ships hooks and
workflows in the same tree, and is disabled with one command. The costs: agent and hook edits need
`/reload-plugins`, and plugin agents cannot declare frontmatter hooks. Both are acceptable.

(c) Writing `.claude/agents/` into the target project at run time needs a restart when the directory is
new, pollutes the owner's repos (or needs `.gitignore` edits), and forks the agent definitions per
project. Reject.

Recommendation: (b), with (a) as the documented fallback if symlinked discovery fails the first live test
(see open question 1). The `--plugin-dir ~/Projects/drive/skill` flag is the certain fallback for a
single session.

### 4.2 Install and uninstall

`install.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$REPO/skill"
DST="$HOME/.claude/skills/drive"

command -v claude >/dev/null || { echo "claude not on PATH"; exit 1; }
claude plugin validate "$SRC" --strict >/dev/null && echo "manifest valid"
chmod +x "$SRC"/scripts/*.sh

mkdir -p "$HOME/.claude/skills"
if [ -e "$DST" ] && [ ! -L "$DST" ]; then
  echo "$DST exists and is not a symlink; refusing to replace it"; exit 1
fi
ln -sfn "$SRC" "$DST"
echo "linked $DST -> $SRC"

# Settings the skill depends on. Applied only with --apply-settings; otherwise printed.
NEEDED='{
  "env": {
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-sonnet-5",
    "CLAUDE_CODE_STOP_HOOK_BLOCK_CAP": "200",
    "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0"
  }
}'
if [ "${1:-}" = "--apply-settings" ]; then
  S="$HOME/.claude/settings.json"; cp "$S" "$S.bak.$(date +%Y%m%dT%H%M%S)"
  jq -s '.[0] * .[1] | del(.env.ANTHROPIC_SMALL_FAST_MODEL)' "$S" <(echo "$NEEDED") > "$S.tmp" && mv "$S.tmp" "$S"
  echo "settings merged (backup kept)"
else
  echo "settings to merge into ~/.claude/settings.json (rerun with --apply-settings):"; echo "$NEEDED"
fi

cat <<'EOF'
verify:
  claude plugin list            # expect: drive@skills-dir  enabled
  claude -p '/drive --selftest' # expect: STATE.md template rendered, agents listed by /context
in a running session: /reload-plugins
EOF
```

`uninstall.sh` removes the symlink, runs `claude plugin disable drive@skills-dir || true`, and prints the
agent-memory directory path so the owner can decide whether to keep it. It does not touch settings (the
backup from install covers reversal).

Notes on the settings block: `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5` moves the `/goal`
evaluator, prompt hooks, and background summarization onto Sonnet 5 (the owner's stated preference over
Haiku) and the merge deletes the deprecated `ANTHROPIC_SMALL_FAST_MODEL`, which currently pins those to
Sonnet 4.5. `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=200` keeps the Stop gate from being overridden after eight
blocks on a long run. `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` matters only for `claude -p` runs and
stops a ten-minute idle limit from killing background subagents. Changing settings is a one-time install
decision the owner makes once; it is not an approval queue.

### 4.3 SKILL.md skeleton and the compaction budget

Frontmatter:

```yaml
---
name: drive
description: Turn a high-level goal into a complete, verified, autonomous execution run. Only the user starts it.
argument-hint: "<high-level goal, one or more sentences>"
disable-model-invocation: true
disallowed-tools: AskUserQuestion
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/*) Bash(cat .drive/*) Bash(git *) Workflow
hooks:
  Stop:
    - hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/scripts/stop-gate.sh"
          args: []
          timeout: 20
  TaskCompleted:
    - hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/scripts/task-gate.sh"
          args: []
          timeout: 20
---
```

The body opens with the two dynamic injections, then the standing rules, and nothing else above the
5,000-token line:

```markdown
Goal: $ARGUMENTS

Existing run state (empty on a fresh start):
!`cat .drive/STATE.md 2>/dev/null || echo "(no .drive/STATE.md; this is a new run)"`

Cross-project lessons (consult before planning):
!`cat "${CLAUDE_PLUGIN_ROOT}/references/lessons.md" 2>/dev/null | head -120 || true`

## Standing rules (kept above the compaction line on purpose)
... invariants: STATE.md is truth; every claim gets a refuting test; verifier is separate;
    status ladder; no worktree survives its step; no questions to the user; plugin root path ...
## Phase index
Read `${CLAUDE_PLUGIN_ROOT}/references/phases.md` when entering a phase; `shapes.md` at intake;
`verification.md` before any status promotion; `models.md` when choosing a subagent's model.
```

Reasoning: after auto-compaction only the first ~5k tokens of `SKILL.md` survive, and the phase narrative
is the part that a running orchestrator can re-read from disk. The invariants, the file layout, and the
instruction to re-read `STATE.md` are the part that must survive, so they go first. `references/*.md`
are read with the Read tool as needed; they are never all loaded. The `!`cat STATE.md`` injection makes a
resumed `/drive` start with state in the prompt instead of hoping the model reads the file. Both
injections end in `|| true` because a failed injected command aborts the whole invocation.

`disallowed-tools: AskUserQuestion` enforces the no-approval-queue rule at the harness level for the
invoking turn; the SKILL.md text repeats the rule for later turns, and `claude -p ... --permission-prompts
none` removes the tool for headless runs. `disable-model-invocation: true` means Claude can never start
`/drive` on its own, which is correct for something that spends this much.

### 4.4 Where the orchestrator runs

In the main conversation. Do not set `context: fork`. The evidence:

1. Every subagent loses `Workflow`, `ScheduleWakeup`, `AskUserQuestion`, `TaskOutput`, and (at the depth
   limit) `Agent`. A forked orchestrator could not run a workflow or schedule a wake-up.
2. `/goal` and Stop hooks act on the main agent's turns. A forked skill's Stop hook is converted to
   `SubagentStop`, which governs only that subagent.
3. A background fork runs with the narrower tool set, and its edits fall outside `/rewind` checkpoints.
4. Nesting depth is three by default. Orchestrator (main) → implementer → its own helper is already two
   layers; a forked orchestrator would burn one.

The one place a forked variant is useful is headless: `claude -p --agent drive:orchestrator "<goal>"`
with an `initialPrompt: "/drive:drive"` agent, mirroring the shipped `claude-security` plugin. That keeps
the orchestrator as the main thread (so it keeps Workflow) while replacing the default system prompt with
the drive persona. Treat it as optional and test the `$ARGUMENTS` hand-off first (open question 5).

### 4.5 Subagent roster

| Agent (`drive:<name>`) | Purpose | Model | Effort | Tools | Isolation | Memory |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| `researcher` | Evidence gathering with citations into `.drive/research/`; web and repo | `sonnet` | `high` | Read, Grep, Glob, Bash, WebFetch, WebSearch, ToolSearch, Write | none | none |
| `architect` | Spec and design documents from the goal plus research; names behavioral claims | `opus` | `xhigh` | Read, Grep, Glob, Bash, Write | none | none |
| `test-designer` | Refutation-first test plan and skeletons written before implementation | `opus` | `high` | Read, Grep, Glob, Bash, Write, Edit | none | none |
| `implementer` | One scoped work package, code plus tests, commits on its branch, reports SHA | `sonnet` (override to `opus` per call for hard packages) | `high` | all inherited minus Agent | `worktree` (see 4.7) | none |
| `verifier` | Independent adversarial verification of a claim against artifacts; never edits | `opus` | `xhigh` | Read, Grep, Glob, Bash | none | `user` |
| `ui-verifier` | Vision check of screenshots against spec and design references | `opus` | `high` | Read, Bash, Glob, Grep, ToolSearch (simulator, Playwright, Chrome MCP) | none | none |
| `grader` | Cheap structured verdicts and classifications for panels and rubrics | `sonnet` | `low` | Read, Grep, Glob | none | none |
| `investigator` | Failure to root cause to verified fact to general lesson | `opus` | `xhigh` | Read, Grep, Glob, Bash, Write | none | none |

Fable is reserved for the orchestrator (the main session) and for per-call escalation when the verifier
and the implementer disagree twice on the same claim; that is the "hardest judgment" the brief describes.
The `haiku` alias appears nowhere.

Draft frontmatter and system prompts follow. Bodies are deliberately short; the delegation message
carries the task, and CLAUDE.md is injected automatically.

`agents/researcher.md`

```markdown
---
name: researcher
description: Gathers evidence for a drive run from the web and the repository and writes a cited ledger entry. Use for any question whose answer should be sourced, not guessed.
model: sonnet
effort: high
tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, ToolSearch, Write
maxTurns: 60
color: cyan
---
You research one question and write one ledger file. Read the question and the target path in your
task. Prefer primary sources; read what you cite; mark each finding as verified (with URL or file:line),
claimed by a source, or your inference. Where sources disagree, say so and say which you trust and why.
Write the ledger to the path you were given, in the template you were given, and return the path plus a
five-line summary. Do not modify any file outside `.drive/research/`.
```

`agents/architect.md`

```markdown
---
name: architect
description: Writes the specification and design documents for a drive run and names each feature's behavioral claim. Use after research and before test design.
model: opus
effort: xhigh
tools: Read, Grep, Glob, Bash, Write
maxTurns: 60
color: purple
---
You turn a goal and a research ledger into documents another agent can build from without talking to
you. Every feature gets one behavioral claim written as a sentence that could be false, and one note on
how it would be refuted. Prefer the smallest design that meets the goal; list what you deliberately left
out. Name every external dependency and every place a test harness could be kinder than production.
Write only under `.drive/` unless your task names another path. Return the file list and the open
decisions, if any, each with your recommendation.
```

`agents/test-designer.md`

```markdown
---
name: test-designer
description: Designs refutation-first tests from a specification before implementation exists. Use once the spec names behavioral claims.
model: opus
effort: high
tools: Read, Grep, Glob, Bash, Write, Edit
maxTurns: 60
color: yellow
---
For each behavioral claim in the spec you were given, write at least one test that would fail for a
plausible wrong implementation, and say which wrong implementation it catches. Use the project's real
test surface; where you must stub, write down where the stub is kinder than the real thing. Tests may
fail or not compile yet; that is expected. Do not write production code. Return the list of test files,
the claim each covers, and any claim you could not find a way to refute.
```

`agents/implementer.md`

```markdown
---
name: implementer
description: Implements exactly one scoped work package with tests in an isolated worktree, commits on its branch, and reports the commit. Use for bounded, well-specified changes.
model: sonnet
effort: high
disallowedTools: Agent
isolation: worktree
maxTurns: 120
color: green
---
Implement the package you were given and nothing adjacent. If you notice work outside the package, list
it in your report; do not do it. Make the named tests pass without weakening them; if a test is wrong,
say so and stop rather than editing it to green. Run the project's real checks. Commit on your worktree
branch with a message naming the package. Report: branch name, `git rev-parse HEAD`, files changed, test
command and its exit code, and anything you could not verify locally.
```

`agents/verifier.md`

```markdown
---
name: verifier
description: Independently verifies a completion claim against code, tests, and proof artifacts, and tries to refute it. Never edits. Use before any status promotion.
model: opus
effort: xhigh
tools: Read, Grep, Glob, Bash
maxTurns: 40
memory: user
color: red
---
You are handed a claim, the paths that supposedly prove it, and nothing about how the work was done. Your
job is to refute the claim. Read the code and run the tests yourself; do not trust a report of a green
run. Ask of every harness: where is it kinder than production? Check that the tests would fail if the
claim were false. Decide from working-tree code and tests first, proof artifacts second, status files
third, prose last. Return a verdict in the JSON shape you were given: pass, fail, or unverifiable, with
the strongest evidence for and against, and the exact command that would settle any doubt. Before you
start, read your memory for patterns of false completion you have seen; after you finish, add any new
pattern in one line.
```

`agents/ui-verifier.md`

```markdown
---
name: ui-verifier
description: Checks rendered UI against the specification and design references using screenshots and the accessibility tree. Use for any change a user would see.
model: opus
effort: high
tools: Read, Bash, Glob, Grep, ToolSearch
disallowedTools: Write, Edit
maxTurns: 40
color: pink
---
Capture the screens named in your task with the tool you were told to use (iOS Simulator MCP, Playwright,
or Chrome), read the screenshots, and compare them against the spec, the design references, and the
previous screenshots in `.drive/ui/`. Judge layout, hierarchy, spacing, typography, states (empty,
loading, error), and whether the screen does what the spec says, not whether it looks plausible. Report
each mismatch as: screen, what you expected, what you saw, severity. A screen you could not render is a
failure to report, not a pass.
```

`agents/grader.md`

```markdown
---
name: grader
description: Returns a cheap structured verdict on one question with a fixed rubric. Use inside panels and workflows, never for judgment that changes the plan.
model: sonnet
effort: low
tools: Read, Grep, Glob
maxTurns: 15
color: blue
---
Answer only the question you were asked, in the exact schema you were given. Read the referenced files;
do not speculate beyond them. If the evidence does not settle the question, say `unverifiable`, never
`pass`.
```

`agents/investigator.md`

```markdown
---
name: investigator
description: Investigates a failure to its root cause, verifies the diagnosis, and distills a general lesson. Use after any refuted claim, live failure, or repeated workaround.
model: opus
effort: xhigh
tools: Read, Grep, Glob, Bash, Write
maxTurns: 80
color: orange
---
Work the ladder in order and write each rung down: the failure as observed; the investigation and the
hypotheses you discarded; the verification that turns your diagnosis into a checked fact (a command, a
test, a log line); the general rule that would have prevented it, stated so it applies beyond this case.
A second occurrence of a workaround means the first diagnosis was wrong; say so. Write the lesson file to
the path you were given in the lesson template and return its path plus the one-line rule.
```

### 4.6 Invoking the roster

From the main conversation the orchestrator uses the Agent tool with `subagent_type: "drive:<name>"`.
Per-call `model` overrides the frontmatter (for example `model: "opus"` on an implementer package the
architect marked hard, or `model: "fable"` on a verifier for a third-round dispute). In an interactive
session every spawn runs in the background; the orchestrator must wait for the completion notification
before reporting anything about it, and it must treat a result marked partial (from `maxTurns`) as
unfinished and continue it with `SendMessage`. Do not pass a `name` on Agent calls; if agent teams are
ever enabled that turns the call into a teammate.

The verifier is spawned with only the claim, the artifact paths, and the verdict schema. It never
receives the implementer's report, transcript, or reasoning. The orchestrator writes the verdict to
`.drive/verdicts/<claim-id>.json` and only then may update `STATE.md`.

### 4.7 Worktrees: when, and how they end

Use `isolation: worktree` only when two or more implementers run concurrently on disjoint areas. A
single implementer works in the main checkout in the foreground of the phase (one lane, no lock
contention, nothing to merge). The owner's evidence and the docs both point here.

When worktrees are used, the orchestrator commits the main checkout first (a subagent worktree branches
from the default branch, so uncommitted work in `main` is invisible to it), then lands each implementer's
result in the same step that reads its report:

```bash
# scripts/worktree-land.sh <branch> <expected-sha>
set -euo pipefail
BR="$1"; SHA="$2"
test "$(git rev-parse "$BR")" = "$SHA" || { echo "branch moved since report"; exit 2; }
git merge --no-ff --no-edit "$BR"           # or --ff-only when the package is linear
WT="$(git worktree list --porcelain | awk -v b="refs/heads/$BR" '$1=="worktree"{w=$2} $1=="branch"&&$2==b{print w}')"
[ -n "$WT" ] && git worktree remove --force "$WT"
git branch -d "$BR"
git worktree prune
```

Run the project's checks on `main` after each landing, and record the landing in `STATE.md`. A worktree
that cannot be merged cleanly is a failed package: revert the merge, hand the conflict to the implementer
with `SendMessage`, and do not move on. Never leave the phase with `git worktree list` showing more than
the main checkout.

### 4.8 The completion loop

Primary mechanism: the Stop hook registered by `SKILL.md`. `scripts/stop-gate.sh`:

```bash
#!/usr/bin/env bash
# Refuse to end the turn while .drive/STATE.md says the run is still going.
set -euo pipefail
INPUT="$(cat)"
CWD="$(jq -r '.cwd' <<<"$INPUT")"
STATE="$CWD/.drive/STATE.md"
[ -f "$STATE" ] || exit 0                                     # no run here

status="$(sed -n 's/^status: *//p' "$STATE" | head -1)"
case "$status" in done|aborted|blocked-on-human|"") exit 0 ;; esac

# Background subagents or workflows still running: let the turn end; their results start the next one.
if [ "$(jq '.background_tasks | length' <<<"$INPUT")" -gt 0 ]; then exit 0; fi

# Stall detection: STATE.md unchanged across N consecutive blocks means the loop is not progressing.
GATE="$CWD/.drive/.gate"; touch "$GATE"
cur="$(shasum "$STATE" | cut -c1-16)"; prev="$(sed -n '1p' "$GATE")"; n="$(sed -n '2p' "$GATE")"; n="${n:-0}"
if [ "$cur" = "$prev" ]; then n=$((n+1)); else n=0; fi
printf '%s\n%s\n' "$cur" "$n" > "$GATE"
if [ "$n" -ge 6 ]; then
  sed -i.bak 's/^status: .*/status: stalled/' "$STATE"
  echo "STATE.md has not changed across six turns; marking the run stalled and ending." >&2
  exit 0
fi

next="$(sed -n 's/^next: *//p' "$STATE" | head -1)"
jq -n --arg r "The drive run is not finished. STATE.md status is '$status'. Next step recorded: ${next:-none}. Continue; update .drive/STATE.md before you stop again." \
  '{decision:"block", reason:$r}'
```

`STATE.md` therefore carries a machine-readable header: `status:` (one of `running`, `verifying`,
`stalled`, `blocked-on-human`, `done`, `aborted`), `next:` (one line), `phase:`, `updated:`. The
template in `templates/STATE.md` puts this header first, then the post's five sections (verified facts,
general rules, open failures, lessons, last session), then the status ladder per feature.

Why this beats the alternatives for "keep going until verified done":

- `/goal` judges from the transcript with a model and cannot read `STATE.md` or the verdict files; the
  gate reads them. `/goal` is still worth typing for a specific measurable end state (the docs' guidance
  on conditions applies), and with `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5` it runs on Sonnet.
  Whether the model can set `/goal` itself is unverified, so the skill must not depend on it.
- `/loop` and `ScheduleWakeup` are timers. They belong to the "no triggering signal" case only: a deploy
  that needs minutes to propagate, a CI run with no channel back. Even then, prefer `Monitor` on a
  command that exits when the condition holds; the docs say it is cheaper than polling.
- Routines are unavailable with the owner's login method, and would run in a fresh clone without his
  MCP servers in any case.
- A prompt-type Stop hook (`type: prompt`, `model: claude-sonnet-5`) is the right second layer when the
  gate is satisfied but the orchestrator's last message claims completion: ask Sonnet whether every
  feature in `STATE.md` reached the status the claim implies. It costs one small call per turn.

`scripts/task-gate.sh` (TaskCompleted): refuse to mark a task complete unless
`.drive/verdicts/<task_id>.json` exists with `"verdict": "pass"`; exit 2 with the reason. This makes the
harness, not the model, hold the line that nothing is done until a separate verifier said so.

`hooks/hooks.json` (plugin-wide, active in every session where the plugin is enabled):

```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "compact|resume",
        "hooks": [ { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/reinject-state.sh", "args": [], "timeout": 10 } ] }
    ]
  }
}
```

`reinject-state.sh` prints `.drive/STATE.md` (head 200 lines) if it exists in the hook's `cwd`, else
nothing. It is cheap, silent in projects without a run, and puts the state back after compaction or a
resume even if the skill body was dropped from the 25k re-attach budget.

### 4.9 Workflow versus Agent fan-out

Rule: **a workflow may read, judge, and write into `.drive/`; only an Agent-spawned implementer edits the
project.** In detail:

Use the Workflow tool (from the main conversation; the skill's instruction counts as the opt-in) when the
work is a fan-out over a known list with no edits to the checkout and the result is a structured
verdict: adversarial verification panels (three graders per claim, each told to refute, majority
survives), research sweeps with cross-checking, hypothesis tournaments for a bug hunt, screenshot judging
across many screens, audits over many files. Default size `medium`; use `agentType: 'drive:grader'` for
votes and `agentType: 'drive:verifier'` for the deciding read; pass paths through `args`; return only the
verdict table. Prefer `pipeline()`; use `parallel()` only where a stage needs all prior results.

Use plain Agent calls when the work edits files, when the orchestrator must steer mid-way, when the
result decides the plan (spec, design), or when there are fewer than about four independent items.
Implementation is never fanned out inside a workflow; the two recorded failures (lock contention, scope
drift) were exactly that.

Template, `workflows/review-panel.js`:

```javascript
export const meta = {
  name: 'review-panel',
  description: 'Adversarially verify each completion claim with independent refuters',
  phases: [{ title: 'Refute', detail: 'three graders per claim' }, { title: 'Decide', detail: 'verifier on split votes' }],
}
const VOTE = { type: 'object', required: ['refuted', 'evidence'], properties: { refuted: { type: 'boolean' }, evidence: { type: 'string' } } }
const VERDICT = { type: 'object', required: ['verdict', 'for', 'against', 'settle'], properties: {
  verdict: { enum: ['pass', 'fail', 'unverifiable'] }, for: { type: 'string' }, against: { type: 'string' }, settle: { type: 'string' } } }
// args: [{ id, claim, paths: [...] }, ...]
const results = await pipeline(args,
  async (c) => {
    phase('Refute')
    const votes = (await parallel([0, 1, 2].map(i => () =>
      agent(`Try to refute this claim. Default to refuted=true if uncertain.\nClaim: ${c.claim}\nEvidence paths: ${c.paths.join(', ')}\nLens ${i}: ${['correctness', 'harness kinder than production', 'does the test fail on a wrong implementation'][i]}`,
        { agentType: 'drive:grader', schema: VOTE, phase: 'Refute', label: `${c.id}#${i}` })))).filter(Boolean)
    return { c, votes }
  },
  async ({ c, votes }) => {
    const refuted = votes.filter(v => v.refuted).length
    if (refuted === 0) return { id: c.id, verdict: 'pass', votes }
    if (refuted === votes.length) return { id: c.id, verdict: 'fail', votes }
    const v = await agent(`Claim: ${c.claim}\nPaths: ${c.paths.join(', ')}\nGraders split ${refuted}/${votes.length}. Decide.`,
      { agentType: 'drive:verifier', schema: VERDICT, phase: 'Decide', label: c.id })
    return { id: c.id, ...(v || { verdict: 'unverifiable' }), votes }
  })
log(`${results.filter(Boolean).filter(r => r.verdict === 'pass').length}/${args.length} claims pass`)
return results.filter(Boolean)
```

The orchestrator writes each result to `.drive/verdicts/<id>.json`. Note the two `.filter(Boolean)`
calls: an `agent()` blocked by the auto-mode classifier or killed by an API error resolves to `null`, and
silently dropping it would read as "covered". Log the count of dropped items.

### 4.10 Memory placement

Three stores, three jobs:

- **Project state** goes in the target repo at `.drive/STATE.md` plus `.drive/{research,verdicts,ui,
  lessons}/`. It is what the gate reads, what compaction re-injects, and what a resumed session finds.
  Whether `.drive/` is committed is per project; the default is to commit it (it is the audit trail the
  owner's culture demands) with `.drive/.gate` and `*.bak` ignored.
- **Cross-project lessons** go in the skill repo at `skill/references/lessons.md`, appended by the
  orchestrator from the investigator's lesson files at the close of every run, one line per rule with a
  date and the project. The `/drive` body injects the first 120 lines at invocation, which is the
  post's "consult" stage made mechanical. This is preferred over agent memory because it is versioned,
  reviewable, and portable to Codex, and because it is exactly the "write the lesson into the Skill"
  move the post recommends.
- **Agent memory** (`memory: user`) is enabled only on the verifier, whose accumulated patterns of false
  completion are a genuine cross-project asset and are consulted by the one agent that needs them. Do not
  give the implementer or researcher memory; it makes their behavior drift between runs for no gain.
- **Auto memory and CLAUDE.md** are left alone. Auto memory is machine-local and Claude-curated; CLAUDE.md
  is the owner's voice. The skill reads both implicitly and writes neither.

### 4.11 Model, effort, and environment defaults

Aliases, not IDs, in frontmatter: `fable`, `opus`, `sonnet`. They track Anthropic's recommended version
and the harness substitutes correctly under an allowlist. If the owner insists on Opus 4.8 rather than
Opus 5, pin `ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-4-8` in settings rather than editing eight agent
files. There is no Sonnet 4.8 to pin.

Effort follows the role table. Do not use `max` anywhere by default; the docs call it prone to
overthinking, and `xhigh` on Opus already exceeds prior generations. `${CLAUDE_EFFORT}` in `SKILL.md`
lets the orchestrator scale panel sizes to the session effort.

Consider `subagentPromptCacheTtl: "1h"` in settings: an API-key user on hour-long runs pays higher cache
writes but avoids re-warming eight agents' prefixes after each five-minute gap. Measure on one run before
adopting.

## 5. Conditionals by project shape

For this component the question is which primitives each shape uses.

**Greenfield app (iOS plus Cloudflare).** Full roster. Research sweep as a workflow; architect produces
`SPEC.md`, `BACKEND.md`, `FRONTEND.md`; test-designer before each implementation phase; two implementer
lanes (backend, iOS) in worktrees, landed and removed per phase; verifier on every claim through the
review-panel workflow; ui-verifier drives the iOS Simulator MCP (`build`, `launch`, `screenshot`,
`inspect`) and keeps a screenshot history in `.drive/ui/`. Live Proof requires a deployed Cloudflare
worker and a device build, not a mock. Preload `frontend-design` into the ui-verifier only if its size is
acceptable (full content is injected; check with `/context`).

**Deep bug hunt.** Investigator leads, not architect. A hypothesis tournament workflow: N investigators
on `opus` each propose a root cause and a disproving experiment, graders refute, the verifier picks. One
implementer in the main checkout, no worktree. The verifier must reproduce the bug before the fix and
fail to reproduce it after; the regression test is the behavioral claim. Lessons step is mandatory.
Skip spec and UI unless the bug is visual.

**Feature on an existing product.** Built-in `Explore` for reconnaissance (it skips CLAUDE.md and is
cheap); architect writes a short design note, not a spec; test-designer; one or two implementers,
worktrees only if two; verifier; ui-verifier if a user can see the change. Status ladder stops at Local
Proof unless a staging environment exists.

**Migration or consolidation.** Discovery as a workflow (one reader per site, structured list); the
plan by the architect; implementation in sequential batches by one implementer in the main checkout with
the verifier after each batch. Do not fan out per-file transforms into worktree agents despite the docs'
example; the merge cost and the owner's evidence argue against it. Live Proof means both the old and the
new path observed on real traffic or a real replay.

**Research plus website.** Research sweep workflow or the bundled `/deep-research`; architect for
information architecture; implementer; ui-verifier through Playwright or Chrome MCP, plus the
`web-design-guidelines` skill invoked by the verifier; `writing` skill for prose. Live Proof is a deployed
site with Lighthouse output in `.drive/ui/`.

**Pure research report.** Researcher and grader only, through a workflow; no implementer, no worktree; the
verifier checks citations. Done means every claim cites a read source.

**Refactor or simplification.** `simplify` or `audit` skill from the main conversation; one implementer;
verifier proves behavior unchanged by the existing test surface plus a refuting test for any claimed
equivalence.

**Ops or incident.** Investigator first; implementer for the fix; verifier with Live Proof mandatory
(the fix observed in the live system through its own tools); lessons mandatory; never "it will happen when
the cron runs".

**Data pipeline, CLI, library.** Standard roster; test-designer weighs most for libraries (public API
claims), ui-verifier is skipped, Live Proof for a pipeline means a real run on real data.

## 6. Model and effort assignment

The roster table in 4.5 is the assignment. The reasoning per tier:

- **Fable 5.1, orchestrator only.** It holds the plan across hours, writes the delegation messages,
  reads verdicts, and decides. Effort `medium` per the owner's saved setting is fine for delegation turns;
  the skill should say `ultrathink` in the intake and dispute-resolution passages, which the docs
  recognize as a per-turn deeper-reasoning request without changing session effort.
- **Opus, hard-but-bounded.** Architect and investigator at `xhigh` because a wrong spec or a wrong root
  cause costs the whole run; verifier at `xhigh` because it is the last line against mirage completion;
  test-designer and ui-verifier at `high`.
- **Sonnet, volume.** Implementer at `high` (escalate individual packages to `opus` per call);
  researcher at `high`; grader at `low` for classification and votes, replacing the post's Haiku.
- **Haiku, nowhere.** The one place the harness would use it (the `/goal` evaluator, prompt hooks,
  compaction summaries) is redirected by `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5`.

All eight are predefined agents shipped in the plugin; the draft frontmatter and system prompts are in
4.5. The orchestrator is not an agent file unless the headless `--agent` variant is adopted.

## 7. Failure modes and anti-patterns

**Mirage completion through harness mechanics.**
- A subagent that hits `maxTurns` returns output marked partial; an orchestrator that summarizes it as
  done has lied by accident. Rule: partial means continue with `SendMessage`, never record.
- Background subagents report by notification; before v2.1.211 Claude sometimes reported unfinished
  results, and the failure mode remains a prompt failure: never describe a subagent's result until its
  completion notification has arrived.
- `agent()` in a workflow resolving to `null` (classifier block, API death) and being filtered away
  silently. Rule: log dropped counts; a dropped verifier vote is `unverifiable`, not `pass`.
- The verifier reading the implementer's report. Contamination is a prompt-construction error: the
  orchestrator passes claim and paths only.
- Green tests in a kinder harness (the D1 bind-variable incident). The verifier prompt asks the question
  explicitly and the test-designer writes down every stub.
- `STATE.md` written from prose rather than from verdict files. The `TaskCompleted` gate and the rule
  "verdict file first, then STATE.md" make the order mechanical.

**Loop failures.**
- The Stop hook's eight-block cap ending a long run early; mitigated by `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`
  and the gate's own stall counter.
- The gate blocking forever on a run that is genuinely blocked; the `blocked-on-human` and `stalled`
  statuses release it, and the stall counter forces the second after six unchanged turns.
- Skill hooks persisting for the whole session: after `/drive` finishes, the gate still runs on every
  turn. It exits immediately when `STATE.md` is `done` or absent, so the cost is one `cat` per turn.
- `/goal` evaluator judging from a transcript that says "done" while files say otherwise; the gate reads
  files, so the two disagree in the right direction.

**Context failures.**
- Skill content past 5,000 tokens dropped after compaction; hence the layout in 4.3 and the
  `SessionStart(compact)` re-injection.
- `skills:` preload of a large skill into an agent (the `frontend-design` skill could be thousands of
  tokens on every ui-verifier spawn); measure before preloading, or have the agent invoke the skill
  itself.
- Eight agent descriptions in every session's listing; keep each under 200 characters.

**Packaging failures.**
- Editing an agent file and expecting hot reload: plugin agents need `/reload-plugins`. The install
  script prints this; the SKILL.md can say it once.
- A component path that is a symlink out of the plugin (for example linking `references/lessons.md` to
  another repo) is refused.
- A `!`command`` that exits non-zero aborts the whole `/drive` invocation with no skill content
  delivered; every injection ends in `|| true`.

**Worktree failures.**
- Worktree branched from `main` while the orchestrator's fresh commits sit uncommitted in the checkout:
  commit first.
- A changed worktree left on disk "for the sweep": forbidden; landing and removal are one step.
- Two implementers in one checkout running the same build tool: forbidden; one lane or worktrees.

**Model failures.**
- Fable classifier refusals in security-adjacent work re-run on Opus 4.8 automatically in interactive
  sessions but end the turn with a refusal in `-p` runs; the skill should route known cybersecurity work
  (security-review, penetration-style testing) to `opus` agents explicitly.
- `schema` on a Fable agent inside a workflow: Fable 5.1 rejects forced `tool_choice`; whether Claude
  Code's `StructuredOutput` forcing survives that is unverified (open question 7). Keep schema-bearing
  workflow agents on `sonnet` and `opus`.

## 8. Open questions and trade-offs

1. **Symlinked skills-dir plugin discovery.** Verified that the layout validates; not verified that
   `~/.claude/skills/drive -> ~/Projects/drive/skill` is discovered as `drive@skills-dir`. Test: create
   the symlink, run `claude plugin list`. If it fails, fall back to `~/.claude/skills/drive` as a real
   directory that is itself a git checkout, or to symlinking `agents/*.md` into `~/.claude/agents/` (which
   needs one restart the first time because the directory does not exist).
2. **Can the model set `/goal`?** The docs list only `/init` and `/security-review` as built-ins reachable
   through the Skill tool. Test once: have Claude try `Skill(goal ...)`. Until then the Stop gate is the
   loop and `/goal` is something the owner types.
3. **Stop hook cap semantics.** The reference says "8 consecutive blocks"; the guide says "eight times in
   a row without progress". Setting `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=200` is cheap insurance either way.
4. **`context: fork` with `agent: drive:<name>`.** Docs say built-in or `.claude/agents/` types; plugin
   scoped names probably resolve (same registry as the Agent tool) but are untested. Not needed for the
   main design.
5. **Headless `--agent drive:orchestrator` with `initialPrompt: "/drive:drive"`.** The docs say the
   initial prompt is prepended to the user prompt and skills are processed; whether the user prompt
   arrives as `$ARGUMENTS` is untested. Recommendation: ship `/drive` first; add the `--agent` variant
   after one `claude -p` experiment.
6. **Agent memory directory for a plugin agent.** Docs give `~/.claude/agent-memory/<name-of-agent>/`;
   whether the plugin-scoped name (with colon) or the bare name is used is unstated. Check the directory
   after the first verifier run so the uninstall script names it correctly.
7. **Workflow `schema` on Fable agents** given Fable 5.1's rejection of forced `tool_choice`. Test with
   one `agent(..., {model: 'fable', schema})` call before relying on it.
8. **`SessionStart` hooks registered from skill frontmatter.** Skill hooks persist for the session, and
   `SessionStart(compact)` fires on compaction, so it should work; the plugin-wide `hooks.json` covers
   it regardless, which is why the design puts the re-inject there.
9. **Sonnet 4.8.** The brief names it; neither the docs nor the bundled model table (cached 2026-06-24)
   list it. Recommendation: use the `sonnet` alias (Sonnet 5, $2/$10, cheaper than Sonnet 4.6) and let
   the coordinator confirm with the owner whether "4.8" was a slip.
10. **Cost of the gate loop on Fable.** Every blocked turn is a Fable turn with the whole context. The
    stall counter and the rule that the orchestrator delegates rather than works keep turns short;
    still, measure the first greenfield run's token total and set a `budget` line in `STATE.md` that
    the orchestrator reports against.
11. **`subagentPromptCacheTtl: 1h`.** Better hit rates on long runs against higher write cost; measure.

## 9. Skill text candidates

Passages ready to lift; imperative voice; plain language.

**Where you run.** You are the orchestrator and you run in the main conversation. Do not delegate the
orchestration to a subagent or a forked skill: subagents cannot run workflows, cannot schedule
wake-ups, and are not governed by this session's Stop hook.

**State is the file.** `.drive/STATE.md` is the truth about this run. Read it before every phase and
after every compaction. Update it before every pause. Its first lines are `status:`, `phase:`, `next:`,
`updated:`; the Stop hook reads them, so keep them exact. Status is one of `running`, `verifying`,
`stalled`, `blocked-on-human`, `done`, `aborted`.

**Spawning.** Call the Agent tool with `subagent_type: "drive:<role>"`. Pass `model: "opus"` on an
implementer package the architect marked hard; pass `model: "fable"` only to a verifier settling a
second dispute. Never pass a `name`. Wait for the completion notification before you describe any
result; a result marked partial is unfinished, so continue it with `SendMessage`.

**The verifier sees nothing but the artifact.** Give the verifier the claim, the paths, and the verdict
schema. Do not give it the implementer's report, its transcript, or your opinion. Write its verdict to
`.drive/verdicts/<id>.json` before you touch `STATE.md`.

**Workflows read; agents edit.** Use the Workflow tool for fan-outs that read and judge: review panels,
research sweeps, hypothesis tournaments, screenshot judging. Never put implementation inside a workflow.
Anything that edits the project is a single `drive:implementer` call.

**One lane unless two.** A single implementer works in the main checkout. Use `isolation: worktree`
only when two implementers run at once on disjoint areas. Commit the main checkout before spawning
them. When each reports, land it and remove it in the same step:
`${CLAUDE_PLUGIN_ROOT}/scripts/worktree-land.sh <branch> <sha>`. Leave the phase with `git worktree
list` showing only the main checkout.

**Status ladder.** Missing, Scaffold, Partial, Local Proof, Live Proof, Operational, Done. Promote only
on a verdict file. Local-only work is never Live Proof. Where a harness is kinder than production, write
down where, and count the claim as Local Proof at most.

**Compaction.** Everything in this file below the "Phase index" heading may be gone after compaction.
When that happens, `STATE.md` is re-injected for you; read `references/phases.md` for the phase you are
in and continue.

**No questions.** You have no `AskUserQuestion` tool and you would not use it if you did. When a
decision is truly unavoidable, write it under `decisions:` in `STATE.md` with your recommendation, set
`status: blocked-on-human`, and end the turn. Expect to be resumed, not answered.

**Refuse to finish early.** The Stop hook will block you while `STATE.md` says `running` or
`verifying`. Do not argue with it and do not edit the status to escape it. Finish the work or record why
you cannot.

**Lessons.** When a claim is refuted, a live check fails, or you repeat a workaround, spawn
`drive:investigator` with the failure and the path `.drive/lessons/<slug>.md`. At the close of the run,
append each lesson's one-line rule to `${CLAUDE_PLUGIN_ROOT}/references/lessons.md` with the date and
project, and commit the skill repo. The next run reads that file before it plans.

**Models.** Fable is you. Opus is the architect, the verifier, the investigator, and the tests'
designer. Sonnet does the volume and the grading. Haiku is not used. If a Fable request is refused for a
safety category, the harness moves it to Opus; do not retry on Fable.

**Timers are a last resort.** Do not schedule a wake-up to wait for something that has a signal. Drive
the system through its own tools, use `Monitor` on a command that exits when the condition holds, and use
`/loop` only for a condition with no signal at all.

**Headless.** The same skill runs as `claude -p "/drive <goal>" --permission-mode auto
--permission-prompts none --output-format stream-json --verbose`. Background subagents keep the process
open; `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` stops the ten-minute idle limit from killing them.

**After you edit an agent or hook in the plugin.** Run `/reload-plugins`. Editing `SKILL.md` needs
nothing.
