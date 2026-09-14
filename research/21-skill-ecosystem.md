# How `/drive` composes with the installed skills, agents, and MCP tools

Researcher report, component 21. Verified on 2026-09-14 against the live docs at
`https://code.claude.com/docs/en/skills`, `/sub-agents`, `/code-review`, `/commands`, `/hooks`, and
`/desktop`, against Claude Code 2.1.263 on the owner's machine, and with two live probes described in
section 3.4. This report builds on `01-harness-primitives.md` (packaging, the `drive:<role>` agent
roster, workflows, the Stop gate) and on `07-verification-architecture.md` (the verification layers).
It does not repeat them.

## 1. Executive opinion

`/drive` should be a conductor, not a second orchestra. Most of the expensive, well-tested procedure it
needs already exists on this machine: `severe-testing` for refutation, `deep-research` and the Tavily
tools for sourced research, `frontend-design` and `dataviz` for visual direction, `/code-review`,
`/simplify` and `/security-review` for hardening, `/run` for driving an app, `google-dev-docs-style` and
`writing` for prose, and the Playwright, Chrome DevTools and iOS Simulator tools for seeing what was built.
The skill's own contribution is the part none of them do: choosing which to use for this goal and shape,
feeding them the right scope, reading their output as evidence rather than as a verdict, and refusing to
count a clean report produced against an empty diff.

Three mechanics decide how composition works. Stable role knowledge should be preloaded into the
predefined agent through `skills:`, because I verified that preload injects the full text of user,
plugin, and bundled skills into a subagent without any tool call. Conditional project knowledge
(`claude-api` for a gateway migration, `rust-refinement` for a Rust crate) should be named in the
delegation message, because I verified that the Skill tool works inside a subagent. And the bundled
workflow skills that spawn their own agents or edit the tree (`/code-review`, `/simplify`,
`/security-review`, `/run`, `workflow-authoring`) should be invoked by the orchestrator from the main
conversation, never from a worker.

The skill must also degrade honestly. On this very machine two skill symlinks dangle, `/verify` and
`/refactor` cannot be invoked by the model, routines are unavailable, and the iOS Simulator and Browser
pane tools vanish in a headless `claude -p` run. A capability preflight at intake, written to
`.drive/capabilities.json`, lets the run pick fallbacks and lower the status ceiling instead of silently
skipping a verification layer.

## 2. What the post says, and a critique

The post has almost nothing to say about composing existing capabilities. It treats skills in two ways:
as procedural memory that the loop should write lessons back into (step 12, and the closing mistake
"Skills that never get written to"), and implicitly as the place a verifier finds design tokens (step 13).
Both are right as far as they go, and both miss the harder problem a general skill faces.

It is right that procedure belongs in skills rather than in chat, and that a skill is sharpened by adding
known failure modes. The owner's `severe-testing` skill is exactly that artifact: a scored evidence scale
and a false-positive filter that took iterations to get right. A drive run that paraphrases "write
adversarial tests" into a worker prompt throws that accumulated work away.

It is wrong, or at least careless, in assuming the loop can write lessons into any skill it uses. Most of
the skills drive composes are not drive's to edit: bundled skills live inside the Claude Code binary,
`frontend-design` and the Tavily skills are vendored copies under `~/.agents/skills`, `writing` belongs to
the Arcwell repository, and `anthropic-skills:*` are synced from a claude.ai account. A lesson about how a
composed skill misbehaves ("`/security-review` reports clean when the branch is already pushed") belongs in
drive's own notes, where the next run consults it before invoking that skill.

It exaggerates vision checking as "read a screenshot and compare to design tokens in the project Skill".
The tools installed here do considerably more (accessibility trees, Lighthouse, console and network logs,
taps and swipes), and a verifier that only looks at pixels misses the functional failures that matter.
Report 09 covers the vision method; this report covers which tool a verifier gets and how it is kept
read-only.

It ignores that the capability surface differs by host. The post writes as if every loop has the same
tools. In practice the Desktop app injects the iOS Simulator and Browser pane tools, the terminal CLI does
not, cloud routines have neither local MCP servers nor `~/.claude/skills`, and a skill copied to another
machine finds a different set. A skill that assumes its tools exist produces mirage completion the first
time it runs somewhere else.

## 3. Verified facts

### 3.1 Documentation

Each item quotes or paraphrases the linked page; quotations are short.

- Preload semantics (`https://code.claude.com/docs/en/sub-agents`, "Preload skills into subagents"): "The
  full content of each listed skill is injected into the subagent's context at startup." The field
  "controls which skills are preloaded, not which skills the subagent can access"; without it the subagent
  "can still discover and invoke project, user, and plugin skills through the Skill tool". To prevent
  invocation, omit `Skill` from `tools` or add it to `disallowedTools`.
- Skills with `disable-model-invocation: true` cannot be preloaded, "This includes the bundled `/verify`
  skill" (same page).
- Background subagents keep "every MCP tool" and a fixed built-in set that includes `Skill` and
  `ToolSearch` (same page). Every subagent loses `Workflow`, `ScheduleWakeup`, and `AskUserQuestion`
  (covered in report 01).
- `tools` and `disallowedTools` accept `mcp__<server>` and `mcp__<server>__*`; in `disallowedTools`,
  `mcp__*` removes every MCP tool. An entry with a specifier such as `Bash(git push *)` "still removes the
  whole tool" (same page).
- Plugin subagents ignore `hooks`, `mcpServers`, and `permissionMode` (same page). A plugin agent therefore
  cannot declare an inline Playwright server; it can only reach servers configured in the session.
- If no entry in `tools` resolves, the subagent "usually fails to launch" (same page, linking the
  zero-tools error).
- Hooks from settings and plugins "also run inside subagents"; tool events carry `agent_id` and
  `agent_type` (`https://code.claude.com/docs/en/hooks`, common input fields). This is what makes a
  plugin-level read-only guard possible (section 4.4).
- Built-in commands reachable through the Skill tool include "`/init` and `/security-review`" and exclude
  others such as `/compact` (`https://code.claude.com/docs/en/skills`).
- `context: fork` skills run in the background "with the narrower tool set that applies to background
  subagents" unless `background: false` (same page).
- Synced skills: when a local command shares the short name, "`/<name>` runs the other command, and the
  synced skill runs only as `/anthropic-skills:<name>`" (same page). On this machine `simplify` resolves to
  the bundled skill; the synced multi-agent pipeline is `anthropic-skills:simplify`.
- Bundled run and verify skills (same page): `/run` launches and drives the app; `/verify` confirms a change
  by building and running it "without falling back to tests or type checks"; `/run-skill-generator`
  commits a recipe to `.claude/skills/run-<name>/`. `/verify` "runs only when you invoke it" and, per
  `https://code.claude.com/docs/en/commands`, Claude stopped being able to run it on its own in v2.1.215.
- `/code-review` (`https://code.claude.com/docs/en/code-review`, "Review a diff locally"): reviews "your
  branch's commits ahead of its upstream plus any uncommitted changes" unless given a target (path, PR,
  branch, or ref range such as `main...my-feature`). It "runs as a background subagent"; in `-p` it runs in
  the foreground. At `low` and `medium` it reports only its most confident findings; `high` through `max`
  "may include findings the review is less sure about". With no level typed, it "reuses the last level from
  `low` through `max` you typed, even in an earlier session". A background `--fix` edits "outside your
  session's checkpoints". It does not read `REVIEW.md`. Claude can start it on its own (v2.1.246+).
- `/security-review` (`https://code.claude.com/docs/en/commands`): "Reviews the diff between your branch
  and origin's default branch" and "Needs an `origin` remote". No target argument is documented.
- `/simplify` (same page): "Four review agents run in parallel", covering reuse, simplification,
  efficiency, and abstraction level; it "doesn't look for correctness bugs" and applies fixes.
- `/batch` (same page): presents a plan, and "Once approved" spawns one background subagent per unit in a
  worktree; "Each subagent implements its unit, runs tests, and opens a pull request."
- Desktop-only surfaces (`https://code.claude.com/docs/en/desktop`): the Browser pane ("uses a clean browser
  profile, separate from your personal browser"), the iOS Simulator pane, and computer use (Pro or Max,
  Desktop app running). The preview server configuration is stored in `.claude/launch.json` at the project
  root.
- Routines cannot see personal skills: a skill "only in `~/.claude/skills/` on your machine" is reported as
  not found when a routine invokes it (`https://code.claude.com/docs/en/skills`).

### 3.2 Bundled skill behavior read from the 2.1.263 binary

These are read from string tables in `~/.local/share/claude/versions/2.1.263`; they are implementation
facts for this version, not documented contracts.

- `simplify` has two prompt variants selected by whether the Agent tool is available: a four-agent fan-out,
  and a "single-pass inline cleanup" that tells the reader to say "this was a single-pass fan-out" or
  "single-pass review ... not the full multi-agent fan-out" in its summary.
- `code-review` sizes its finder fleet to the diff: "Spawn about N finder subagents (min 2, max 8)" with N
  about one per 150 changed lines. Its context switch returns `inline` in some hosts and `fork` otherwise.
  After reporting it says to invoke `/verify` if that has not run and the diff has a runtime surface; since
  `/verify` is user-only, a model-driven run cannot follow that instruction.
- `security-review` instructs its sub-task: "Do not use the bash tool or write to any files", flags only
  findings with over 80 percent confidence, and hard-excludes denial of service, rate limiting, memory
  safety in memory-safe languages, test-only files, and log spoofing, among others.
- `schedule` returns "API accounts are not supported" without a claude.ai login; the owner uses Console
  login, so routines are unavailable (consistent with report 01).
- `run` first looks for a project run skill, falls back to per-type patterns (CLI, server, TUI, Electron,
  browser via Playwright, library), and recommends `/run-skill-generator` when it had to improvise.

### 3.3 Inventory on this machine (inspected)

User skills under `~/.claude/skills/` (symlinks followed): `agent-browser`, `arcwell-operator` (dangling),
`audit` (to `~/Projects/audit-skill/skill`), `chrome-cdp`, `deep-research` (to `~/Projects/deep-research/skill`),
`frontend-design` (to `~/.agents/skills`), `google-dev-docs-style` (to `~/Projects/google-dev-docs-skill/skill`),
`imagegen`, `improve`, `react-component-performance`, `refactor` (adapter to `~/Projects/refactor/skill`,
`disable-model-invocation: true`), `rust-refinement`, `severe-testing` (to `~/Projects/severe-testing`), eight
`tavily-*` skills (to `~/.agents/skills`), `vercel-react-best-practices`, `web-design-guidelines`, and
`writing` (dangling: its target `~/Projects/arcwell/plugins/arcwell-codex/skills/writing` no longer exists).

Plugins enabled: `arcwell@arcwell-local` (skills include `arcwell:writing`, `arcwell:deep-research`) and
`ferrite@ferrite-labs`. The official marketplace is cloned under `~/.claude/plugins/marketplaces/` but none of
its plugins is enabled, so `skill-creator`, `claude-security`, and the plugin copy of `frontend-design` are
not loaded from there. `skill-creator` and a multi-agent `simplify` are present as claude.ai-synced
`anthropic-skills:*`. `~/.agents/skills/` holds more skills that are not linked into Claude Code
(`impeccable`, `design-taste-frontend`, `redesign-existing-projects`, `cve-pattern-agent`, `changelog`,
`brandkit`, `gpt-taste`, `full-output-enforcement`); the Skill tool cannot load them.

No `~/.claude/agents/` and no `~/.claude/agent-memory/` exist. None of the owner's skills ship Claude agents;
several ship `agents/openai.yaml` for Codex.

MCP servers configured in `~/.claude.json`: `chrome-devtools` (a launcher that starts Chrome with a dedicated
profile at `~/.cache/chrome-devtools-mcp/attach-profile`), `playwright` (`npx -y @playwright/mcp@latest`,
unpinned), `tavily-remote-mcp` (HTTP), `blender`, `unreal` (failed to connect today), `arcwell-hub`,
`arcwell-companion`, `x`, `ferrite` (failed today), `fabric-tutti-dev` (needs auth), `local-agent-bridge`.
Host-injected in the Desktop app, not configured on disk: `Claude_Code_iOS_Simulator`, `Claude_Browser`,
`claude-in-chrome`, `computer-use`.

CLIs: `gh` (logged in as `chrischabot`), `xcrun simctl` (iPhone 17 Pro and iPad Pro 11-inch booted),
`xcodebuild` 27.0, `wrangler`, `npx`, `tvly` 0.1.6, `imagegen` (`OPENAI_API_KEY` is not in the shell
environment; whether the CLI reads it from elsewhere is unverified), `agent-browser`.

### 3.4 Live probes (run today, nothing left behind)

**Probe A, Skill tool inside a subagent.** A foreground `general-purpose` subagent on `sonnet` reported:
`Skill`, `Agent`, and `ToolSearch` present; `Workflow`, `AskUserQuestion`, `ScheduleWakeup` absent. Its
skill listing held about 65 entries including every skill named in the brief except `refactor`. It invoked
`severe-testing` and `web-design-guidelines` successfully (content returned inline, first headings "# Severe
Testing" and "# Web Interface Guidelines"). It invoked bundled `simplify` successfully; the invocation
returned the instructions inline, which would then have told the subagent to spawn four more agents. Through
`ToolSearch` it found `mcp__playwright__browser_snapshot` and related tools.

**Probe B, `skills:` preload and headless tool surface.** From a scratch directory under `/private/tmp`
(deleted afterwards): `claude -p --model sonnet --agents '{"probe-preload": {..., "skills":
["web-design-guidelines","simplify","arcwell:writing","refactor"], "tools":["Read"], ...}}'`. The subagent,
answering from context with no tool calls, confirmed the Web Interface Guidelines text and the
`arcwell:writing` text were present; bundled `simplify` was preloaded in its no-Agent-tool variant (its first
line reads "Agent tool unavailable → single-pass inline cleanup → apply the fixes"); `refactor` was absent,
as the docs predict for a user-only skill. The headless main session listed MCP prefixes `arcwell-companion`,
`arcwell-hub`, `blender`, `chrome-devtools`, `claude_ai_Gmail`, `local-agent-bridge`, `playwright`,
`plugin_ferrite_ferrite`, `tavily-remote-mcp`, `x`, and **no** `Claude_Code_iOS_Simulator`, `Claude_Browser`,
or `claude-in-chrome` tools.

What the probes settle: all three invocation routes work in a subagent (Skill tool, preload, and naming the
skill so the worker calls the Skill tool); preload works for user, plugin, and bundled skills but not for
user-only ones; a bundled skill's behavior can change with the tools of the agent that loads it; and a
headless run loses the Desktop-hosted verification tools.

What the probes did not settle: whether a preloaded skill that refers to `references/*.md` by relative path
receives its base directory (the Skill tool invocation does; preload was not tested for this), and whether
`agent()` calls inside a Workflow get the Skill tool.

## 4. Detailed spec

### 4.1 The inventory, classified

The table gives, for each capability, what it does, its inputs and outputs, whether it edits anything, the
model or effort it assumes, and where drive uses it. "Read-only" means it does not edit the target project;
several write reports or publish artifacts, which is noted. Where a skill names no model, the column says so;
drive assigns one from report 06.

| Capability | What it does | Inputs → outputs | Edits the project? | Model/effort assumed | Drive phase | Shapes |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| `severe-testing` (user, owner's repo) | Refute behavioral claims with adversarial, malicious, and failure-mode tests; score findings 0–100 and filter false positives | claims, code, test surface → tests, commands run, scored findings, untested risk | Yes, writes tests (runs destructive cases only in fixtures) | None stated | Test design; hardening; bug-fix proof | All code shapes |
| `deep-research` (user; duplicate `arcwell:deep-research`) | Evidence-led report with three source lanes and claim labels (verified fact, source claim, inference, conflict) | question, audience, time window → cited report | No | Host-agnostic; suggests parallel workers by source family | Research | Research, website, greenfield, migration |
| `tavily-search`, `-extract`, `-map`, `-crawl`, `-research`, `-dynamic-search` (user) and `tavily-remote-mcp` | Web search, URL extraction, site map, crawl to markdown, cited research (30–120 s), on-disk triage of large payloads | query or URLs → JSON or markdown files | No (crawl can write markdown to a chosen dir) | None; `research` has `--model pro` | Research; citation checking | Research, website, greenfield, migration |
| `tavily-cli`, `tavily-best-practices` | Setup and auth for `tvly`; SDK reference for building Tavily into an app | — | No | — | Preflight; implementation only if the product uses Tavily | Rare |
| `frontend-design` (user, vendored) | Two-pass visual direction: token plan (4–6 named hexes, type roles, ASCII layout, one signature), critique against templated defaults, then build | brief, subject → design plan, then UI code | Guidance; the building step edits | None | Architecture (design contract); UI build | Greenfield UI, website, new UI surfaces |
| `web-design-guidelines` (user, Vercel) | Fetches the latest Web Interface Guidelines from GitHub and reviews named files | file paths → terse `file:line` findings | No | None; needs WebFetch | UI verification (web) | Website, web features |
| `dataviz` (bundled) | Chart form heuristic, palette formula with a runnable validator, mark and interaction rules | data, medium → chart code and checks | Guidance | None | Architecture and build for charts | Dashboards, reports with charts |
| `design` (bundled) | Draft `.dc.html` artboards and publish a design canvas Artifact the owner can tweak | brief → published Artifact URL | No, but publishes a (private) Artifact | None | Optional design exploration | Greenfield UI, website |
| `artifact-design` (bundled, session-provided) | Design calibration before writing an Artifact page | — | No | — | Only when the deliverable is an Artifact | Research reports published as pages |
| `imagegen` (user; CLI) | Generate or edit images with gpt-image models | prompt, size, quality → image files | Writes image files | OpenAI models; costs per image | Build (imagery) | Website, greenfield marketing |
| `/code-review` (bundled) | Correctness bugs plus reuse and efficiency cleanups on a diff; finder fleet sized to the diff | effort level, target (path, PR, ref range), `--fix` → findings | Only with `--fix` (outside checkpoints when backgrounded) | Uses session model; effort from typed level or the level last typed | Hardening, first-pass correctness | Existing codebases: feature, bug, migration, refactor |
| `/simplify` (bundled) | Behavior-preserving cleanup in four lenses; applies fixes; no bug hunting | optional target → edits plus summary | Yes | Session model | Hardening, after a pass | Feature, greenfield milestone, refactor |
| `anthropic-skills:simplify` (synced) | Deep multi-agent simplification pipeline with plans, worktree execution, tech-lead review | scope → plans, worktree diffs, verdicts | Yes, via worktrees | high/xhigh subagents | Refactor shape only | Refactor, post-greenfield consolidation |
| `/security-review` (built-in, Skill-invocable) | High-confidence exploitable vulnerabilities in the branch diff against `origin`'s default branch | none → markdown findings with severity and exploit scenario | No (its sub-task is told not to use Bash or write) | Session model | Hardening, conditional on surface | Any change touching auth, input, data, network |
| `audit` (user, owner's repo) | Whole-codebase simplification audit of data structures, state, control flow, ownership; coverage contract, read-only workers, audit of the audit | repository → one report with inventory, findings, skips, priorities | No; must not run tests | None; uses read-only workers | Discovery | Refactor, migration discovery, pre-feature recon on large systems |
| `improve` (user, shadcn) | Senior-advisor survey producing self-contained implementation plans for other agents | repository, focus → findings table, `plans/*.md` | Writes `plans/` in the repo root; `execute` variant uses a worktree | Expensive model plans, cheaper executes | Not used inside a run (see 4.5) | "What should we build next" requests |
| `refactor` (user, owner's repo) | Behavior-preserving refactor pipeline with lenses, snapshot, worktree execution | explicit invocation only | Yes | high/xhigh lenses, medium executor | Not invocable by drive | — |
| `/run` (bundled) | Launch and drive the project's app to see a change working | request → observed behavior, screenshots | Launches processes; may recommend a recipe | Session model | UI and runtime verification | Anything with a runtime |
| `/verify`, `/run-skill-generator` (bundled) | Build-and-observe confirmation; record a launch recipe as a committed project skill | — | `/run-skill-generator` commits `.claude/skills/run-<name>/` | — | `/verify`: not invocable by drive. Generator: optional, greenfield | Greenfield, products with non-standard launch |
| `google-dev-docs-style` (user, owner's repo) | Binding Google developer docs style; references and a review checklist | draft docs → conforming docs | Edits docs | None | Docs | Website docs section, library, CLI, SDK |
| `writing` (dangling user link; `arcwell:writing` plugin works) | Audience-facing prose under the owner's name; fidelity to sources; Fable used only as story researcher | sources, brief → prose | Edits prose | Requires Fable for story mapping on substantial narratives | Copy, blog, README narrative | Website marketing and blog, research reports |
| `claude-api` (bundled) | Current model IDs, pricing, SDK usage, caching, tool use, migrations | project language → reference | No | — | Architecture and build when the product calls Claude | Migration of an AI gateway, any LLM feature |
| `vercel-react-best-practices`, `react-component-performance` (user) | React and Next.js performance rules; render-thrash diagnosis | code → recommendations | Guidance | — | Build and review | React or Next.js projects |
| `rust-refinement` (user, owner's repo) | Survey, mechanize, review, refactor, verify for Rust | crate → change sets | Yes | — | Build and hardening | Rust projects |
| `workflow-authoring` (bundled) | Script API and patterns for the Workflow tool | — | No | — | Orchestration, before writing a workflow script | Any shape using fan-out |
| `loop` (bundled), `schedule` (bundled) | Timer-driven or self-paced re-runs; cloud routines | — | — | — | `loop`: only for a condition with no signal. `schedule`: unavailable here | Ops waiting on external propagation |
| `skill-creator` (synced; plugin not enabled) | Draft skills, run with-skill and baseline evals, human review viewer | skill, prompts → eval results | Writes eval workspace | — | Drive's own self-improvement (report 11) | Close-out |
| `agent-browser` (user; CLI) | Browser automation via refs | commands → snapshots, screenshots | No | — | Fallback web verification | Web, when MCP is absent |
| `chrome-cdp` (user) | Drives the owner's real Chrome session; "only on explicit user approval" | — | — | — | Never used by drive | — |
| `/batch` (bundled) | Plan, then on approval one worktree subagent per unit, each opening a PR | — | Yes, via PRs | — | Never used by drive | — |

Two groupings follow from the table and drive the rest of the design. The first is by **how the capability
behaves when loaded**: pure knowledge (frontend-design, dataviz, google-dev-docs-style, claude-api, the React
and Rust playbooks, severe-testing's method), procedures that run in the loader's context (deep-research,
web-design-guidelines, audit, severe-testing's workflow), and orchestration skills that spawn agents, fork,
or edit on their own (`/code-review`, `/simplify`, `anthropic-skills:simplify`, `/run`, `improve`,
`/batch`). The second is by **who may invoke it**: model-invocable, user-only (`/verify`, `refactor`,
`/goal` per report 01), and unavailable on this login (`schedule`).

### 4.2 Invocation routes and which to use

There are four ways a capability reaches the agent that needs it. All four were checked (section 3.4).

1. **The orchestrator invokes it with the Skill tool** in the main conversation. The content lands in the
   orchestrator's context, and any agents the skill spawns are spawned from the main thread, so they count
   against nesting depth from the top, stay under the session's hooks, and report back to the orchestrator.
   Use this for the orchestration skills: `/code-review`, `/simplify`, `/security-review`, `/run`,
   `workflow-authoring`, and `claude-api` when the orchestrator itself is choosing models.
2. **Preload with `skills:` in a predefined agent's frontmatter.** The full text is in the agent's context
   from its first turn, with no tool call and no chance that the agent decides not to load it. Use this for
   knowledge and method that the role always needs. It costs the whole skill's size on every spawn of that
   agent, so reserve it for skills under about 15 KB that the role uses every time.
3. **Name the skill in the delegation message** and tell the worker to invoke it with the Skill tool before
   starting. Use this for conditional knowledge that depends on the project (the implementer on a Rust crate
   gets "invoke `rust-refinement`"; on an Anthropic-API gateway, "invoke `claude-api`"). A per-call `skills`
   parameter does not exist on the Agent tool, so this is the only per-call route.
4. **Point the worker at a file path** instead of a skill. Use this when the skill is a thin wrapper around
   a document that the worker can read directly and more cheaply, and when the skill depends on reference
   files that a preload may not locate: `audit/references/audit-your-codebase.md`,
   `google-dev-docs-style/references/review-checklist.md`, the Web Interface Guidelines file fetched once
   into `.drive/ui/web-interface-guidelines.md`.

Rules that follow from the evidence:

Never preload an orchestration skill into a worker. Probe B showed that bundled `simplify` preloaded into an
agent without the Agent tool becomes a single-pass inline cleanup that edits files; preloaded into an agent
with the Agent tool it would fan out four agents from depth two. Either way it is not what the orchestrator
thinks it asked for.

Never give a read-only role the Skill tool. A verifier with `Skill` can load `/simplify` or
`severe-testing` and start writing. Give read-only roles an explicit `tools` allowlist without `Skill`, and
preload what they need.

Never rely on a user-only skill. `/verify`, `refactor`, and `/goal` cannot be invoked by the model. Where
their method is useful, replicate the intent through a model-invocable route (`/run` plus a verifier for
`/verify`), and do not preload them (the preload silently does nothing, as probe B showed for `refactor`).

In a Workflow, pass `agentType: 'drive:<role>'` so the predefined agent's preloads come along, rather than
naming skills in `agent()` prompts; whether workflow agents get the Skill tool is unverified.

### 4.3 Preload assignments for the roster

Report 01 defines the roster; report 07 adds a severe tester and an auditor. The recommended `skills:` field
for each, with measured sizes:

| Agent | `skills:` preload | Named in delegation when relevant | Rationale |
| :-- | :-- | :-- | :-- |
| `drive:researcher` | `deep-research` (4.3 KB) | `tavily-dynamic-search` for large payloads; `tavily-research` for a one-call cited synthesis | The claim-label discipline is the whole value; it is small |
| `drive:architect` | none | `frontend-design` for greenfield UI direction; `dataviz` for chart-heavy specs; `claude-api` when the product calls Claude | Architecture is broad; conditional knowledge only |
| `drive:test-designer` | `severe-testing` (12.3 KB) | — | Refutation-first design is this role's job |
| `drive:severe-tester` | `severe-testing` | — | Report 07 layer 4; the scored scale must be verbatim |
| `drive:implementer` | none | `rust-refinement`, `vercel-react-best-practices`, `react-component-performance`, `claude-api`, `frontend-design` when building new UI | Implementers vary by stack; preloading all of these would cost about 50 KB per spawn |
| `drive:verifier` | none | none; give it `severe-testing`'s false-positive filter by path if needed | A correctness verifier should reason from artifacts, and must not be able to load editing skills |
| `drive:ui-verifier` | `frontend-design` (8.3 KB) for greenfield projects only, otherwise none | Path to `.drive/ui/web-interface-guidelines.md` and `DESIGN.md` | The guidelines skill is a 1.2 KB stub that fetches at run time; fetch once, pass the file |
| `drive:grader` | none | rubric path | Graders must be cheap |
| `drive:investigator` | none | `severe-testing` when proving a root cause | Invokes it only for the verify rung |
| `drive:writer` (if added) | `arcwell:writing` (14.3 KB) | `google-dev-docs-style` for docs pages | Report 18 separates marketing prose from docs |
| `drive:auditor` | none | — | Reads status and proofs; no skills needed |

Because one plugin agent file carries one `skills:` list, a ui-verifier that sometimes wants
`frontend-design` and sometimes does not has two honest options: preload it always (8 KB per spawn) or name it
in the delegation. Recommendation: name it in the delegation and allow the Skill tool for the ui-verifier
only, with the read-only hook in 4.4 as the guard, because the ui-verifier's cost is dominated by screenshots,
not by skill text.

### 4.4 MCP tools per role, and keeping verifiers read-only

**Which tools each role needs.**

Web UI verification uses Playwright MCP first. It is headless-capable, runs an isolated browser, returns an
accessibility snapshot as well as screenshots, and scripts multi-step flows. Chrome DevTools MCP is second,
for what Playwright lacks: `lighthouse_audit`, `performance_start_trace` and `performance_analyze_insight`,
heap snapshots, detailed console and network inspection. The Desktop Browser pane (`Claude_Browser`, with
`preview_start` and `.claude/launch.json`) is acceptable only in a Desktop session and only for localhost;
it disappears headless and writes a launch file into the repo. `claude-in-chrome` and the `chrome-cdp` skill
drive the owner's real, logged-in browser; drive never uses them for verification. The chrome-devtools
launcher here uses a dedicated profile, and the owner's memory records that the debugging Chrome is signed
into a different Google account, so drive must not read or create any Google state through it.

iOS UI verification uses `mcp__Claude_Code_iOS_Simulator__build` and `control` (`launch`, `screenshot`,
`inspect` for the accessibility tree, `tap`, `swipe`) when running under the Desktop app. Outside Desktop the
fallback is `xcodebuild` with an XCUITest target (queries the accessibility hierarchy and taps), `xcrun simctl
launch booted <bundle-id>`, and `xcrun simctl io booted screenshot <file>`, which the verifier then reads. The
fallback loses the free-form accessibility inspection, so the capability file must record it and the
ui-verifier must say which surface it used.

Research uses `tavily-remote-mcp` or the `tvly` CLI for search and extraction and built-in WebSearch for
breadth. Citations should be checked against raw page text from `tavily_extract`, `tvly extract`, or `curl`,
not against WebFetch, whose tool description says it "answers `prompt` against it using a small fast model";
a summary is not a quotation. `tvly research`, `map`, and `crawl` need authentication; the Tavily skills say
an unattended run should report the cap rather than start a login.

Bug hunts and ops use `gh` for CI evidence (`gh run list`, `gh run view --log-failed`), issue history, and
blame context. Drive does not post comments, open PRs, or run `/code-review --comment`; the owner commits to
`main` and publishing on his behalf needs his explicit permission.

Native macOS apps with no CLI are the only place `computer-use` belongs, and it needs the Desktop app and a Pro
or Max plan; drive treats it as absent unless the preflight finds it.

Domain servers (`arcwell-hub`, `x`, `blender`, `ferrite`) are project-specific. Drive reaches for them only
when the goal names that system, and then through the system's own tools, never by poking its storage.

**How `tools:` and `disallowedTools:` keep verifiers read-only.**

Plugin agents honor `tools` and `disallowedTools` but ignore frontmatter `hooks`, `mcpServers`, and
`permissionMode`. The allowlist is therefore the primary control, and it has one hole: Bash. A verifier must
run tests, and `disallowedTools` cannot remove only some Bash commands (a specifier removes the whole tool).
Close the hole with a plugin-level hook, which does run inside subagents and carries `agent_type`.

Draft frontmatter for the web and iOS ui-verifier, extending report 01's draft:

```yaml
---
name: ui-verifier
description: Drives the rendered app and judges it against the spec and design contract using screenshots and the accessibility tree. Never edits. Use for any change a user can see.
model: opus
effort: high
tools: Read, Grep, Glob, Bash, ToolSearch, Skill, mcp__playwright__*, mcp__chrome-devtools__*, mcp__Claude_Code_iOS_Simulator__*, mcp__Claude_Browser__*
disallowedTools: Write, Edit, NotebookEdit, mcp__playwright__browser_run_code_unsafe, mcp__playwright__browser_file_upload, mcp__chrome-devtools__upload_file, mcp__chrome-devtools__execute_3p_developer_tool
maxTurns: 60
color: pink
---
```

Read, Grep, Glob, and Bash guarantee the agent launches on a machine where none of the MCP patterns resolve
(the docs say a list that resolves to nothing fails to launch). The ui-verifier keeps `Skill` only so the
orchestrator can name `frontend-design` per project; the correctness verifier, grader, and auditor get no
`Skill`:

```yaml
tools: Read, Grep, Glob, Bash
```

The plugin's `hooks/hooks.json` adds two guards scoped to read-only roles:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [ { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/readonly-guard.sh", "args": [], "timeout": 5 } ] }
    ],
    "SubagentStart": [
      { "matcher": "^drive:(verifier|grader|ui-verifier|auditor)$",
        "hooks": [ { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/tree-snapshot.sh", "args": ["start"], "timeout": 10 } ] }
    ],
    "SubagentStop": [
      { "matcher": "^drive:(verifier|grader|ui-verifier|auditor)$",
        "hooks": [ { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/tree-snapshot.sh", "args": ["stop"], "timeout": 10 } ] }
    ]
  }
}
```

`readonly-guard.sh` reads the hook input, exits 0 unless `agent_type` is one of the read-only roles, and for
those denies (exit 2 with a reason) commands that change tracked state: `git commit|push|reset|checkout|
restore|stash|rebase|merge|apply|am|clean`, `rm`, `mv`, `sed -i`, redirection into tracked paths, package
installs, and `wrangler deploy|d1 execute --remote`. It cannot be complete, which is why the second guard
exists. `tree-snapshot.sh start` records `git rev-parse HEAD` and a hash of `git status --porcelain
--untracked-files=no` into `.drive/.ro/<agent_id>`; `stop` compares, and on a difference prints the changed
paths and returns `decision: block` with the instruction "You are read-only; revert your changes to tracked
files and report what you changed." Build output in ignored directories does not trip it. The agent's
verdict is discarded if the guard fired, and the orchestrator records a failure note.

Whether the plugin-scoped `agent_type` value is `drive:verifier` or `verifier` should be checked on the first
run (report 01, open question 6 has the same uncertainty for memory directories); write the matcher to accept
both.

### 4.5 Overlaps, a hardening order, and gaps drive must fill

**How the five review-shaped capabilities differ.** They look alike and are not substitutes.

`/code-review` looks for correctness bugs in a diff, plus cleanups, with a finder fleet and some verification
of candidates. Its unit is the diff, its bar depends on effort, and its output is findings, not proof.
`/simplify` looks for none of that; it improves the structure of changed code and edits. `severe-testing` is
not a review at all: it writes and runs tests that try to refute named claims, and its output is executable
evidence with a confidence score. `/security-review` is a narrow, high-precision read of the branch diff for
exploitable vulnerabilities; it is deliberately blind to denial of service, resource exhaustion, and
theoretical races, which are exactly the categories `severe-testing` covers. `audit` is whole-codebase and
read-only, and it looks for structural simplification opportunities in data and state, not in a diff; it is
discovery, not hardening. `improve` overlaps `audit` and adds plan writing for other agents.

**Recommended order in the hardening phase.** This is report 07's layer order with the skills placed in it
and the scope traps closed:

1. Deterministic gates by Bash (build, typecheck, lint, tests). No skill.
2. `/code-review high <run-baseline-sha>...HEAD` for existing codebases, invoked by the orchestrator, in
   parallel with the `drive:verifier`. Always pass the level and the range explicitly (section 7).
   Findings above the model's confidence cut become `should_fix` inputs to the verifier, never verdicts.
3. `drive:severe-tester` with `severe-testing` preloaded, on every unit with behavioral claims. Its tests
   are evidence the verifier re-runs.
4. `/security-review` when the surface touches identity, input, data, files, network, or secrets, run
   before the commits are pushed; otherwise the severe tester's security lenses with the explicit range.
5. `drive:ui-verifier` for anything rendered, with `/run` from the orchestrator to launch the app when no
   project run skill exists.
6. `/simplify <paths touched by this run>` after a pass, then gates again, then a grader check that the test
   baseline is unchanged; revert on any change in the baseline.
7. Docs: `google-dev-docs-style` checklist for docs pages; `writing` for narrative prose.
8. Final audit by `drive:auditor` for greenfield, migration, and large features.

Security review sits after severe testing rather than before because its exclusions make a clean result weak
evidence, and the severe tester has already produced the demonstrations the security reading can check.
Simplification sits last because it edits and would invalidate every earlier verdict if run first.

**Gaps drive must fill itself.** Nothing installed does these, and each is a place mirage completion hides:

- *Claim naming and the claims ledger.* `severe-testing` assumes claims exist; nothing produces them from a
  goal. The architect and test designer do (reports 03 and 08).
- *Scope control for diff-based reviewers.* Every diff reviewer defaults to "ahead of upstream" or "against
  origin's default branch". For an owner who commits straight to `main`, that scope is either the right set
  of unpushed commits or empty. Drive records `baseline_sha` at intake and passes explicit ranges.
- *Evidence adjudication.* Review skills output findings; none says whether a claim is proven. The verdict
  schema and the status ladder are drive's (report 07).
- *Harness-kindness auditing.* No skill asks where a test shim is kinder than production. The test designer
  and verifier prompts carry that question.
- *Live proof.* `/run` shows local behavior; nothing installed deploys and observes the real environment.
  Domain components (reports 17 and 18) own this.
- *Cross-run memory of skill quirks.* Section 2: a notes file inside drive, `references/skill-notes.md`.
- *Taste verification for native iOS.* `frontend-design` and `web-design-guidelines` are web-shaped; report
  09 supplies the HIG-based contract.
- *Capability detection and fallback.* Section 4.6.

**Where drive deliberately does not use an installed skill.** `improve` writes `plans/` into the repo root and
asks the owner to choose which plans to write; `/batch` waits for plan approval and opens pull requests;
`refactor` and `/verify` are user-only; `chrome-cdp` touches the owner's real browser; the `skill-creator`
review viewer is a human queue (report 11). Drive borrows their method where useful (the `improve` audit
playbook's finding format, the `refactor` lenses) by reading their reference files, not by invoking them.

### 4.6 Graceful degradation

**Preflight at intake.** Before planning, the orchestrator runs `${CLAUDE_PLUGIN_ROOT}/scripts/capabilities.sh`
and a short ToolSearch pass, and writes `.drive/capabilities.json`. The script checks what Bash can check;
the ToolSearch pass checks MCP tools, which only the session can see.

```bash
#!/usr/bin/env bash
# capabilities.sh: detect skills and CLIs drive composes with; never fails the run.
set -uo pipefail
out() { printf '  "%s": %s,\n' "$1" "$2"; }
skill() {  # present only if the directory resolves and holds SKILL.md
  local p="$HOME/.claude/skills/$1"
  if [ -f "$p/SKILL.md" ]; then echo true
  elif [ -L "$p" ]; then echo '"dangling"'
  else echo false; fi
}
echo "{"
for s in severe-testing deep-research frontend-design web-design-guidelines google-dev-docs-style \
         audit imagegen rust-refinement vercel-react-best-practices tavily-search tavily-research writing; do
  out "skill:$s" "$(skill "$s")"
done
out "plugin:arcwell:writing" "$([ -f "$HOME/.claude/plugins/cache/arcwell-local/arcwell/2.0.0/skills/writing/SKILL.md" ] && echo true || echo false)"
out "cli:gh"        "$(gh auth status >/dev/null 2>&1 && echo true || echo false)"
out "cli:tvly"      "$(command -v tvly >/dev/null && echo true || echo false)"
out "cli:imagegen"  "$(command -v imagegen >/dev/null && echo true || echo false)"
out "cli:simctl"    "$(xcrun simctl list devices booted 2>/dev/null | grep -q Booted && echo true || echo false)"
out "cli:xcodebuild" "$(command -v xcodebuild >/dev/null && echo true || echo false)"
out "cli:wrangler"  "$(command -v wrangler >/dev/null && echo true || echo false)"
out "cli:agent-browser" "$(command -v agent-browser >/dev/null && echo true || echo false)"
out "git:origin"    "$(git remote get-url origin >/dev/null 2>&1 && echo true || echo false)"
out "git:baseline_sha" "\"$(git rev-parse HEAD 2>/dev/null || echo none)\""
printf '  "checked_at": "%s"\n}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

The orchestrator then runs ToolSearch for `+playwright snapshot`, `+chrome-devtools lighthouse`,
`+Claude_Code_iOS_Simulator`, `+tavily search`, and `+Claude_Browser`, and merges `mcp:<server>: true|false` into
the file. The orchestrator's own skill listing (the system reminder) is authoritative for whether a skill is
invocable; the script only catches dangling links and CLIs. Skill names are checked by name, with the plugin
or synced variant accepted where one exists (`writing` or `arcwell:writing`; `skill-creator` or
`anthropic-skills:skill-creator`).

**The fallback table.** When a capability is missing, the run continues with the fallback, records the
substitution in `STATE.md`, and applies the ceiling.

| Missing | Fallback | Effect on status ceiling |
| :-- | :-- | :-- |
| `severe-testing` | Test designer uses `references/refutation.md` inside drive, a condensed copy of the claim, refutation, oracle, and 0–100 scoring rules | None, if the condensed copy is kept current |
| `deep-research` | Researcher follows drive's `references/research.md` (three lanes, claim labels) | None |
| Tavily (skill, CLI, and MCP all absent) | WebSearch for discovery, `curl` for raw text of cited pages | None; slower |
| `frontend-design` | Drive's `references/design-contract.md` (token plan, anti-default critique) | None for function; taste review notes the gap |
| `web-design-guidelines` or network | Fetch the guidelines file once when available and cache it in the drive repo | None |
| Playwright and Chrome DevTools MCP | `agent-browser` CLI, else `npx playwright test` with screenshots read by the verifier | None if a scripted browser runs; otherwise UI claims cap at Partial |
| iOS Simulator MCP (any non-Desktop run) | `xcodebuild test` with XCUITest plus `simctl io screenshot` | Accessibility inspection limited; state it in the verdict |
| No simulator or Xcode | UI claims cannot exceed Scaffold or Partial; the run says so plainly | Partial at most |
| `/security-review` or no `origin` | Severe tester's security lenses with the explicit range | None |
| `/code-review` | Verifier alone | None; one less independent pass |
| `/simplify` | Skip simplification; record it | None; simplification is not a completion requirement |
| `writing` | Drive's voice rules plus the owner's CLAUDE.md voice section | None for docs; narrative prose flagged for a later pass |
| `imagegen` or its API key | No generated imagery; use real screenshots and typographic design | None |
| `gh` unauthenticated | CI evidence from local reproduction only | None |
| `claude-api` | Researcher reads `platform.claude.com` docs directly | None |
| Workflow tool disabled | Sequential Agent calls for panels | None; slower |

Two rules govern degradation. A missing verification capability lowers the ceiling of the claims it would
have verified; it never lets a layer pass by default. And a missing capability is reported once, in the
final summary and in `STATE.md`; the run does not stop to ask for it to be installed.

The condensed fallbacks (`references/refutation.md`, `research.md`, `design-contract.md`) should be short, a
page each, and should say at the top that they are the fallback for the named skill. They are the one place
drive duplicates installed work, and they exist so that the skill still works when copied to a machine
without the owner's repositories.

### 4.7 Capability map, ready for `references/capabilities.md`

"Orch" means the orchestrator invokes the skill in the main conversation; "pre" means preloaded into the
named agent; "named" means named in the delegation message; "path" means passed as a file path. Shapes: G
greenfield app, B bug hunt, F feature on an existing product, M migration or consolidation, W research plus
website, R pure research report, S refactor or simplification, O ops or incident, L library, SDK, or CLI, D
data pipeline.

| Phase | Shapes | Skills (route) | MCP and CLI tools | Agents |
| :-- | :-- | :-- | :-- | :-- |
| Intake and preflight | all | none | `capabilities.sh`; ToolSearch probes; `git rev-parse HEAD` | orchestrator |
| Reconnaissance | F, M, S, B, O, L | `audit` (orch, whole-codebase; S and M only); `audit-your-codebase.md` (path) for bounded subsystem readers | `gh` for CI and issue history (B, O) | built-in `Explore`; `drive:researcher` |
| External research | G, W, R, M, F when unfamiliar tech | `deep-research` (pre, researcher); `tavily-dynamic-search` or `tavily-research` (named) | `tavily-remote-mcp` or `tvly`; WebSearch; `curl` for citation text | `drive:researcher` ×N via Workflow; `drive:grader` for citation checks |
| Two-fact lookup | any | none | WebFetch or `tvly extract` on the primary page | orchestrator or one researcher |
| Specification and claims | G, F, M, W, L, D | `claude-api` (named, when the product calls Claude) | — | `drive:architect` |
| Visual direction and design contract | G (UI), W, F (new UI surface) | `frontend-design` (named, architect or designer); `dataviz` (named, charts); `design` (orch, optional canvas, never a gate) | — | `drive:architect` (opus) |
| Test design | G, F, M, L, D, B | `severe-testing` (pre) | — | `drive:test-designer` |
| Implementation | G, F, M, W, L, D, B, S | stack playbooks (named): `rust-refinement`, `vercel-react-best-practices`, `react-component-performance`, `claude-api`, `frontend-design` for new UI | `xcodebuild`, `wrangler`, project toolchain | `drive:implementer` |
| Imagery and copy | W, G (marketing) | `imagegen` (named); `arcwell:writing` (pre, writer) | `imagegen` CLI | `drive:implementer` or `drive:writer` |
| Docs | W, L, G, M | `google-dev-docs-style` (named or pre, writer) | — | `drive:writer`; `drive:grader` for doc-claim checks |
| Correctness hardening | F, M, B, S, L, G per milestone | `/code-review high <range>` (orch) | — | `drive:verifier` in parallel |
| Adversarial testing | all code shapes | `severe-testing` (pre) | — | `drive:severe-tester` |
| Security review | any touching auth, input, data, network, secrets | `/security-review` (orch, before push) | `git` | `drive:severe-tester` security lenses |
| Runtime and UI verification | G, F, W, B (visual or runtime), O | `/run` (orch, to launch); `frontend-design` (named, taste lens) | Playwright MCP; Chrome DevTools MCP (Lighthouse, traces); iOS Simulator MCP or `xcodebuild`/`simctl`; Browser pane (Desktop only) | `drive:ui-verifier` |
| Simplification | F, G milestones, S | `/simplify <paths>` (orch); `anthropic-skills:simplify` (orch, S only, worktree landed and removed in the same step) | — | `drive:grader` for baseline check |
| Live proof | G, W, M, O, D | domain components (reports 17, 18) | `wrangler`, deploy tools, `gh run` | `drive:verifier` |
| Failure investigation | all | `severe-testing` (named, verify rung) | `gh`, logs | `drive:investigator` |
| Final audit | G, M, large F | none | — | `drive:auditor` |
| Orchestration mechanics | any using fan-out | `workflow-authoring` (orch, before the first script) | Workflow tool | orchestrator |
| Waiting on an external signal | O, M cutover, deploy propagation | `loop` (orch, only with no signal) | `Monitor` preferred | orchestrator |
| Lessons and self-improvement | all | `skill-creator` principles (path), not its viewer | — | `drive:investigator`; orchestrator |

### 4.8 Delegation message templates

For a worker that should load a conditional skill:

```text
Before you start, invoke the Skill tool with `rust-refinement`. Use its operating contract and its rule
that mechanical and behavioral changes land in separate commits. Do not run its full survey; your scope is
the package below.

Package: <id and one-line goal>
Files in scope: <list>. Out of scope: <list>.
Claims this package must satisfy: <claim ids from .drive/claims.md>
Checks to run: <exact commands>
Report: files changed, commit SHA, check commands with exit codes, anything you could not verify.
```

For the orchestrator's own hardening pass (not a subagent prompt; the orchestrator's instructions to itself):

```text
baseline=$(jq -r '."git:baseline_sha"' .drive/capabilities.json)
/code-review high ${baseline}...HEAD          # never omit the level or the range
# before trusting a clean /security-review:
git rev-parse --verify origin/HEAD && test -n "$(git diff --stat origin/HEAD...HEAD)"
/security-review                               # only if the check above passed
/simplify <space-separated paths touched since baseline>
```

## 5. Conditionals by project shape

**Greenfield iOS app with a Cloudflare backend.** For a project of that shape the skill would instruct: run
`deep-research` through researchers on platform choices and competitors; have the architect invoke
`frontend-design` for the visual direction, adapted to the Human Interface Guidelines (report 09); use
`claude-api` only if the product calls Claude; preload `severe-testing` in the test designer and severe
tester; name no web design skills for the iOS surface, and apply `web-design-guidelines` only to any web
surface (a marketing page or admin console). Verification uses the iOS Simulator MCP under Desktop and the
`xcodebuild`/`simctl` fallback headless, with the capability file deciding which. `/run-skill-generator` is
worth running once, because the launch involves both a Worker dev server and a simulator build and every
later agent benefits from a recorded recipe; the recipe is committed as part of the change. `/code-review` is
of limited use before there is a meaningful diff; use it per milestone with the milestone's range.
`/security-review` runs on the backend milestone before its first push. `imagegen` is for marketing imagery
only, never for app screenshots.

**Deep bug hunt.** Almost no design or research skills. `gh` for CI history. The investigator leads, and it
invokes `severe-testing` for the reproduce-then-refute rung (report 20). After the fix, `/code-review medium
<range>` is enough; medium favors confident findings on a small diff. `/simplify` is skipped for tiny diffs.
`/run` is used when the bug is observable at runtime. Security review only if the root cause is in a trust
boundary.

**Feature on an existing product (a dashboard).** Reconnaissance with `Explore` and, for a large system, the
audit reference by path for bounded subsystem reads, not the whole `audit` skill. `dataviz` is mandatory for
charts, named to the architect and implementer. `frontend-design` is used in "match the existing system"
mode, not "distinctive" mode; say so in the delegation, because the skill's default stance pushes toward a
distinctive identity. `web-design-guidelines` for the web UI. Full hardening order.

**Migration or consolidation (AI gateway into a core service).** `audit` from the orchestrator on the source
project, or its reference by path for per-subsystem readers, to inventory every behavior before moving it.
`claude-api` named to the architect and implementer, because an AI gateway's model IDs, caching headers, and
pricing are exactly what drifts. `severe-testing` for parity claims between old and new paths. `/simplify` is
deferred until cutover is proven (report 07). `/code-review` in batches with explicit ranges.

**Research plus website.** `deep-research` through researchers; `tavily-crawl` when competitor docs must be
read in bulk; `frontend-design` mandatory including its writing section; `design` as an optional canvas for
the owner to look at, never as a gate; `imagegen` for illustrations; `arcwell:writing` for marketing and blog;
`google-dev-docs-style` for the documentation section; `dataviz` for any market charts;
`web-design-guidelines` plus Playwright and Chrome DevTools Lighthouse for verification. `/security-review`
only if the site has forms or a backend.

**Pure research report.** `deep-research`, Tavily, graders checking citations against raw extractions, and
`arcwell:writing` when the report goes out under the owner's name. `artifact-design` only if the deliverable
is published as an Artifact. No code skills.

**Refactor or simplification.** `audit` for discovery when the scope is a whole codebase;
`anthropic-skills:simplify` or bundled `/simplify` for the change itself, with the synced pipeline's worktrees
landed and removed in the same step; `severe-testing` characterization tests before risky changes. The owner's
`refactor` pipeline is user-only; if he invokes it himself, drive is not involved.

**Ops or incident.** `gh` and the affected system's own MCP or CLI; `loop` or `Monitor` only for propagation
with no signal; `severe-testing` for the regression; no design, research, or simplification skills.

**Library, SDK, or CLI.** `google-dev-docs-style` for reference docs and README procedures; `severe-testing`
for public API claims (property tests and malformed input); stack playbooks; `/code-review` and
`/security-review` for anything that parses untrusted input.

**Data pipeline.** `severe-testing` for idempotency, reordering, and partial-write claims; `dataviz` for any
output charts; no UI skills.

## 6. Model and effort assignment

Report 06 owns routing; this section only records what composition changes.

A skill invoked with the Skill tool runs on the model of the agent that invoked it. `/code-review`,
`/simplify`, and `/security-review` invoked from the orchestrator therefore run on Fable 5.1 unless their own
forks pick a different model, and Fable's cybersecurity classifiers are most likely to trip on
`/security-review` (report 15). Two consequences follow. Invoke `/security-review` only through a model
override: have the orchestrator spawn a short-lived `drive:severe-tester` (Opus) with the instruction "invoke
the Skill tool with `security-review` and return its findings verbatim", which is the one case where a
subagent should invoke a built-in review, because the model matters more than nesting. And run `/code-review`
and `/simplify` from the orchestrator, accepting Fable cost for the coordinator turn, because their finder
fleets are subagents that carry their own effort routing.

The bundled `writing` skill says Fable is required for story mapping on substantial narratives and suggests
`claude --bare -p --model fable` in a TTY when the host cannot select Fable. Inside drive the orchestrator is
already Fable; it should spawn the story-mapping step as an Agent call with `model: "fable"` rather than a
nested CLI, and give the drafting to an Opus writer.

Preloaded skill text is paid on every spawn of that agent. At current prices (report 01), 12 KB of
`severe-testing` is roughly 3,000 input tokens, about $0.015 on Opus per spawn before caching and far less
with cache reads. That is negligible for the test designer and severe tester, which spawn a handful of times.
It would not be negligible if every grader in a 30-vote panel preloaded it, which is why graders preload
nothing.

Agent frontmatter changes relative to report 01, in summary: researcher adds `skills: [deep-research]`;
test designer and severe tester add `skills: [severe-testing]`; verifier, grader, and auditor keep `tools:
Read, Grep, Glob, Bash` with no `Skill`; ui-verifier uses the draft in 4.4; an optional writer agent on `opus`
at `high` with `skills: [arcwell:writing]`, named in the roster only if report 18's split of prose roles is
adopted. The plugin's `hooks.json` gains the read-only guards.

## 7. Failure modes and anti-patterns

**Re-implementing severe testing inline.** The orchestrator writes "now write some adversarial tests for
edge cases" into a worker prompt. The worker writes boundary tests with shape assertions, which the skill's
own ladder calls weak or moderate, and reports findings without the 0–100 score or the false-positive filter.
The result reads as thorough and certifies little. Prevention: severe testing is only ever done by an agent
with `severe-testing` preloaded, and the verdict schema requires the score for every finding.

**Deep research for a two-fact lookup.** The run needs the D1 bind-variable limit and the current Swift
toolchain version. Invoking `deep-research` produces a report with three evidence lanes and burns a
researcher fan-out on two numbers. Prevention: the rule "one primary page answers it" routes to WebFetch or
`tvly extract` on that page, with the raw quotation stored in the research ledger. Use deep research when
freshness, coverage, or contradiction matter, as its own description says.

**Design skills on a bug fix.** Loading `frontend-design` for a layout regression tempts the agent to
"improve" the design, since the skill's stance is to take an aesthetic risk. Prevention: the shape table
lists no design skills for bug hunts; if the bug is visual, the ui-verifier compares against the previous
screenshot and the existing tokens, not against a new direction.

**Loading every skill into every agent.** A `skills:` list with eight entries costs 50 to 80 KB per spawn,
dilutes the role prompt, and can inject contradictory instructions (`arcwell:writing` and
`google-dev-docs-style` disagree on purpose about voice). Worse, it can inject orchestration skills that change
the agent's behavior, as probe B showed with `simplify`. Prevention: the preload table in 4.3 is the whole
list.

**Trusting a clean review of an empty diff.** `/security-review` compares against `origin`'s default branch;
`/code-review` without a target reviews commits ahead of upstream. On `main` after a push, both can report
nothing because they reviewed nothing. That is mirage completion by scope. Prevention: explicit ranges from
the recorded baseline, and a non-empty-diff check before a clean result counts.

**Nondeterministic review depth.** `/code-review` without a level reuses the level the owner last typed,
even in an earlier session. Two runs of the same skill on the same diff can review at `low` and at `max`.
Prevention: always pass the level.

**Background `--fix` outside checkpoints.** A backgrounded `/code-review --fix` edits the tree outside
`/rewind`. Prevention: drive never passes `--fix`; findings go to the implementer, whose change is gated and
verified like any other.

**Invoking skills that cannot run here.** Relying on `/verify`, `refactor`, `/goal`, or `/schedule`
produces a loop step that silently does nothing. Prevention: the capability file and the rule in 4.2.

**Dangling skills.** `~/.claude/skills/writing` points at a path that no longer exists; the Skill tool reports
it missing and a careless orchestrator proceeds without prose review. Prevention: preflight accepts
`arcwell:writing` as the substitute and records which variant ran.

**A read-only verifier that writes.** A verifier with Bash "fixes" a test to confirm its theory, then passes
the claim. Prevention: the allowlist without Edit, Write, or Skill; the Bash guard; the tree snapshot that voids
the verdict.

**Using the owner's real browser.** `claude-in-chrome` and `chrome-cdp` act in the owner's logged-in
sessions. A verifier that uses them can touch real accounts, and the debugging Chrome is signed into the wrong
Google account. Prevention: those tools are excluded from every drive agent's `tools`.

**Human queues imported from skills.** `improve` waits for the owner to pick plans; `/batch` waits for plan
approval and opens PRs; `skill-creator` opens a review viewer. Prevention: drive borrows their method by path
and never invokes their interactive flows.

**Worktrees left by a composed skill.** `anthropic-skills:simplify` and `improve execute` create worktrees.
Prevention: the orchestrator lands and removes them in the same step it reads the result, exactly as report 01
requires for its own implementers, and checks `git worktree list` before leaving the phase.

**Artifacts in the owner's repos.** `improve` writes `plans/`, the Browser pane writes `.claude/launch.json`,
`/run-skill-generator` commits `.claude/skills/run-<name>/`, `/verify` (when the owner runs it) writes
`.claude/skills/verify/SKILL.md`. Prevention: only the run recipe is allowed, as a deliberate committed part of
the change, and the final status check lists untracked files.

**Unpinned tools changing under a run.** Playwright MCP runs `@playwright/mcp@latest`, so a multi-day run can
start one version and end on another. Prevention: record `npx @playwright/mcp@latest --version` in the proof
artifact of each UI verdict; treat a version change between verdicts as a reason to re-run the earlier one if
it fails.

**WebFetch summaries treated as quotations.** WebFetch answers through a small model. A citation checked
against its output is checked against a paraphrase. Prevention: raw extraction for citations.

## 8. Open questions and trade-offs

1. **Do preloaded skills get their base directory?** The Skill tool supplies it; preload was not tested for
   skills that link `references/*.md` relatively (`audit`, `google-dev-docs-style`, `improve`).
   Recommendation: pass absolute reference paths in the delegation whenever a preloaded skill has reference
   files, and test once with `google-dev-docs-style` preloaded into a probe agent via `--agents`.
2. **Can Workflow `agent()` calls use the Skill tool?** Unverified. Recommendation: use `agentType` with
   preloads in workflows and do not depend on Skill there.
3. **Does `/code-review` invoked from inside a subagent fork again?** Its context selector returns fork or
   inline depending on the host; nesting from depth two would spend depth three. Recommendation: orchestrator
   only, except the security-review model-override case in section 6, which is a built-in without a fork.
4. **`/security-review` scope control.** No target argument is documented. Recommendation: run it before
   pushing; when already pushed, rely on the severe tester's security lenses with the explicit range. Worth a
   one-line test of whether passing a range as arguments changes the diff it reads.
5. **Should lessons about composed skills be written into those skills?** `severe-testing`, `audit`, and
   `google-dev-docs-style` are the owner's own repos, so drive could commit improvements there. That crosses
   repositories mid-run and changes behavior for every other use. Recommendation: write them to
   `references/skill-notes.md` in drive during runs; at close, when a note has recurred twice, open a commit in
   the owner's skill repo as a separate, clearly described step, never mid-run.
6. **Bundled `simplify` or the synced multi-agent pipeline for the refactor shape?** The synced one is far more
   thorough and uses worktrees; the bundled one is quick and in-place. Recommendation: bundled in hardening,
   synced for the refactor shape, and verify on the first refactor run that the synced skill can run
   non-interactively (it presents a table and asks which findings to plan, with a non-interactive default).
7. **`imagegen` key.** `OPENAI_API_KEY` is not in the shell; the CLI may read a config file. Recommendation:
   the preflight runs `imagegen models >/dev/null` and records the result instead of guessing.
8. **`agent_type` value for plugin agents in hook input.** Write matchers that accept both `drive:verifier` and
   `verifier` until the first run shows which.
9. **The ~/.agents skills not linked into Claude Code.** `impeccable`, `redesign-existing-projects`, and
   `cve-pattern-agent` look relevant to UI taste and security. They are not loadable today, and linking them
   changes the owner's environment. Recommendation: leave them unlinked; report 09 already mines their tell
   lists by path.
10. **Fixing the dangling `writing` link.** This is an owner decision about his environment, not something a
    run should change. Recommendation: drive's install script reports dangling skill links once and does not
    touch them.

## 9. Skill text candidates

**Conduct, don't duplicate.** Before writing any procedure into a delegation message, check the capability
map. If an installed skill does the job, route to it. Write your own procedure only where the map lists a gap
or the capability file says the skill is missing.

**Three routes into a worker.** Knowledge a role always needs is preloaded in that agent's definition.
Knowledge this project needs is named in the delegation: "Before you start, invoke the Skill tool with
`<skill>`." A skill that is really a document is passed as an absolute file path. Never add skills to a worker
beyond these.

**Orchestration skills stay with you.** Invoke `/code-review`, `/simplify`, `/run`, and `workflow-authoring`
yourself, in the main conversation. They spawn agents or edit files, and from inside a worker they spend
nesting depth or change behavior. The one exception is `/security-review`: have a `drive:severe-tester`
invoke it, so it runs on Opus.

**Read-only roles get no Skill tool.** The verifier, grader, and auditor run with Read, Grep, Glob, and Bash
only. If one of them changes a tracked file, its verdict is void; record a failure note and spawn a fresh one.

**Preflight before planning.** Run `${CLAUDE_PLUGIN_ROOT}/scripts/capabilities.sh > .drive/capabilities.json`,
then probe with ToolSearch for Playwright, Chrome DevTools, the iOS Simulator, Tavily, and the Browser pane,
and merge the results. Plan only with capabilities the file shows as present. For each missing one, apply the
fallback and the status ceiling from `references/capabilities.md`, and write the substitution into STATE.md.

**Missing tools lower the ceiling, never the bar.** When a verification capability is absent, the claims it
would have checked cannot rise above the ceiling the fallback table gives. Do not pass a layer because its tool
was unavailable. Report missing capabilities once, in STATE.md and the final summary, and keep going.

**Always give reviewers a scope and a level.** Record `baseline_sha` at intake. Run `/code-review high
<baseline_sha>...HEAD`, never bare `/code-review`, because without a level it reuses whatever the owner typed
last and without a range it may review nothing. Never pass `--fix` or `--comment`.

**A clean review of nothing is not a pass.** Before counting a clean `/security-review`, confirm `origin`
exists and `git diff --stat origin/HEAD...HEAD` is not empty. If the work is already pushed, use the severe
tester's security lenses on the recorded range instead.

**Hardening order.** Gates, then the verifier with `/code-review` beside it, then the severe tester, then
security review when the surface warrants it, then UI verification, then `/simplify` on the touched paths
followed by gates and a baseline check, then docs, then the final audit. Simplification comes last because it
edits; revert it if the test baseline changes.

**Severe testing has one owner.** Never ask a worker for "adversarial tests" in your own words. Spawn
`drive:severe-tester`, which carries the `severe-testing` skill, and require its 0–100 score on every finding.
A finding without a score is a note, not evidence.

**Research sized to the question.** If one primary page answers it, fetch that page with `tvly extract` or
`curl`, store the exact quotation in the research ledger, and move on. Use `deep-research` through researchers
when freshness, coverage, or conflicting sources matter. Check citations against raw page text, never against a
WebFetch summary.

**Design skills only where there is design.** Use `frontend-design` for new visual surfaces, in "distinctive"
mode for greenfield and marketing work and "match the existing system" mode for features on an existing
product; say which in the delegation. Use `dataviz` for any chart. Use neither on a bug fix; a visual
regression is judged against the previous screenshot and the existing tokens.

**Which browser.** Verify web UI with Playwright first and Chrome DevTools for Lighthouse, traces, console, and
network. Use the Browser pane only in a Desktop session and only for localhost. Never use `claude-in-chrome` or
`chrome-cdp`; they act in the owner's real browser. Never read or create Google account state in the
debugging Chrome.

**Which simulator surface.** Under the Desktop app, drive iOS screens with the iOS Simulator tools (`build`,
`launch`, `screenshot`, `inspect`, `tap`). Headless, use `xcodebuild test` with XCUITest and `xcrun simctl io
booted screenshot`, and say in the verdict that the accessibility tree was not inspected directly.

**Skills you must not rely on.** `/verify`, `refactor`, and `/goal` run only when the owner types them, and
`/schedule` does not work with this login. Do not plan steps that need them. Do not invoke `improve`'s plan
selection, `/batch`, or the `skill-creator` review viewer; each waits for a person. Borrow their method by
reading their reference files.

**Composed skills leave nothing behind.** If a skill you invoked created a worktree, land it and remove it in
the same step you read its result. If it wrote into the project (`plans/`, `.claude/launch.json`), remove the
file before the phase ends unless it is a run recipe you deliberately commit with the change.

**Notes about skills live in drive.** When a composed skill misbehaves or needs a specific argument to behave,
add one line to `${CLAUDE_PLUGIN_ROOT}/references/skill-notes.md` with the date and the fix. Read that file
before invoking any skill it mentions. Do not edit another skill's files during a run.

**Prose skills by audience.** Marketing, blog, and anything under the owner's name go through
`arcwell:writing` (or `writing` if that link resolves). Documentation pages go through
`google-dev-docs-style`, finishing with its review checklist. Do not apply both to the same page.
