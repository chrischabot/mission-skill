# 12. Parallel execution: decomposition, swarms, worktrees, and integration

Researcher report for the `/drive` skill. Covers the post's steps 7 and 8 and the owner's "tackling things with swarms". Everything marked **verified** was checked on 2026-09-14 against code.claude.com docs, the locally installed `workflow-authoring` skill (Claude Code 2.1.263), the owner's own persisted workflow scripts and run records under `~/.claude/projects/`, his memory notes, and a scratch-repo test of the git recipe. Everything marked **opinion** is argued, not assumed.

---

## 1. Executive opinion

The skill's parallel-execution component must do three things well, in this order of importance: decompose a design into packages with disjoint file ownership, run those packages with the cheapest isolation that actually prevents collisions, and integrate the results into `main` inside the same step that produced them. Speed is the least important of the three. A swarm that finishes in twenty minutes and leaves two branches behind has failed this owner; a swarm that finishes in forty and leaves `git worktree list` showing only `main` has succeeded.

The post treats git worktrees as the default safety mechanism for parallel agents. For this owner that default is wrong, and his own history proves it. His two most successful implementation fleets (the ten-agent Arcwell v2 gap-closure build in August 2026 and the fabric plan-029 fleet) ran in a **shared checkout with strict file ownership**, no worktrees, workers forbidden from touching git, and the orchestrator applying cross-file "wiring" and committing. His fabric memory bans worktrees outright after they hid work from sibling sessions and produced phantom test failures from dependency drift. The harness confirms the danger from the other side: a subagent worktree that made changes is **never merged back by Claude Code**; it sits on disk until a thirty-day sweep, and that sweep deliberately keeps any worktree with unpushed commits, which is exactly the state a finished-but-unmerged package is in. Left to defaults, every changed subagent worktree is a permanent orphan.

So the skill should make disjoint ownership in a shared tree the default substrate, reserve worktrees for the two cases where they genuinely earn their cost (packages that must edit shared or generated files, and parallel experiments whose losers are discarded), and treat "merge, run gates, remove worktree, delete branch" as one indivisible integrator step with a mechanical audit at the end of every wave. Makers report structured summaries and file paths, never diffs. Verifiers execute tests with fresh context. The final audit checks claims against the spec, because the post-mortem lesson from his August big run was that green gates certified a scope nobody asked for.

---

## 2. What the post says, and a critique

**Step 7 (Dynamic Workflows).** The post says workflows shipped 2026-05-28, that Claude writes a JavaScript harness with `agent()`, `parallel()`, `pipeline()`, and names five patterns: fan-out-and-synthesize, adversarial verification, loop-until-done, classify-and-act, tournament. The API description is accurate as far as it goes (verified against the `workflow-authoring` skill), but it omits the parts that decide whether a workflow is the right tool for an implementation wave: the opt-in rule (the `ultracode` keyword only counts when a human types it; a skill's explicit instruction also counts), the concurrency cap of sixteen agents, the fact that scripts cannot touch the filesystem themselves, and above all the resume semantics. When one agent in a fan-out fails and the run is relaunched, every agent that started after it runs again, including ones that completed. For read-only stages that is harmless. For a wave of makers editing files, a rerun re-applies edits on top of already-edited files unless every maker is written to be idempotent. The post also says nothing about who merges the results of a fan-out, which is the whole problem.

**Step 8 (Worktrees).** The post is right that two agents writing the same file is the same failure as two engineers committing to the same lines. It is wrong about the remedy in three ways. First, "maker writes in worktree A; verifier reads in worktree B" misunderstands verifiers: a verifier reads and runs tests, it does not mutate, so it needs no worktree at all and gains nothing from one except a stale view of the maker's work. Second, "each major phase a separate worktree; a failed phase doesn't poison the rest" is precisely the branch-and-forget pattern this owner has told his agents, in strong language, never to use. Phases are sequential; sequential work belongs on `main` with commits as checkpoints. Third, the post presents `isolation: worktree` as "a fresh checkout that cleans itself up". Verified: it cleans itself up **only if the subagent makes no changes**. A worktree with changes stays. The post's safety mechanism, applied naively, manufactures orphans.

**Where the post is right.** Parallel structural experiments each in their own worktree, with the best one merging, is a legitimate use, and the tournament pattern with an independent judge is the right way to pick. Adversarial verification per maker is right and this owner's own review fleets already do it (47 reviewer and verifier agents in one run). The general claim that a verifier subagent beats self-critique is consistent with Claude Code's own best-practices page.

**What the post exaggerates.** It implies parallelism is the main lever for large projects. The Anthropic research-system post the step draws on found that token usage explains about eighty percent of performance variance; parallelism is a way to spend more tokens with clean contexts, not a free speedup. Every fleet in this owner's history that went wrong went wrong through scope drift or contention, not through insufficient parallelism. The codex-swift fleet that "did not wedge" still ballooned to 72 files and 5.25 million tokens implementing features nobody requested. Decomposition discipline, not fan-out width, is the variable that matters.

---

## 3. Verified facts

### Subagents and the Agent tool

- `isolation: worktree` runs the subagent in a temporary git worktree "branched by default from your default branch rather than the parent session's HEAD." "The worktree is automatically cleaned up if the subagent makes no changes." Nothing in the docs merges changes back. https://code.claude.com/docs/en/sub-agents
- Worktrees page, on subagent worktrees: "Each subagent gets a temporary worktree that Claude Code removes automatically when the subagent finishes without changes; a worktree with changes stays on disk until the periodic sweep below can remove it without losing work." The sweep "leaves a worktree in place" when it "still holds work: changed or untracked files, or unpushed commits." https://code.claude.com/docs/en/worktrees#isolate-subagents-with-worktrees
- The sweep runs at `cleanupPeriodDays`; "The default is 30 days and the minimum is 1", and "The same age cutoff applies to automatic removal of orphaned worktrees." https://code.claude.com/docs/en/claude-directory
- Default worktree location and branch: "under `.claude/worktrees/<name>/` at your repository root, on a new branch named `worktree-<name>`." Tip: "Add `.claude/worktrees/` to your `.gitignore`." https://code.claude.com/docs/en/worktrees#start-claude-in-a-worktree
- Base branch setting `worktree.baseRef`: `"fresh"` (default) branches "from the repository's default branch on the remote, usually `main`"; `"head"` branches "from your current local HEAD, so the worktree carries your unpushed commits." Subagent worktrees "branch from your repository's default branch unless `worktree.baseRef` is set to `"head"`." If no remote is configured, fresh falls back to local HEAD. https://code.claude.com/docs/en/worktrees#choose-the-base-branch
- Isolation enforcement inside a worktree session or worktree subagent: Claude Code blocks edits targeting the main checkout, commands whose working directory resolves to the main checkout, and git redirects into it. https://code.claude.com/docs/en/worktrees#how-claude-code-enforces-isolation
- `.worktreeinclude` copies gitignored files such as `.env` into every worktree Claude Code creates, including subagent worktrees. https://code.claude.com/docs/en/worktrees#copy-gitignored-files-into-worktrees
- Non-interactive `-p` runs "have no exit prompt, so Claude doesn't clean up their worktrees." Same page, "Clean up worktrees".
- Background subagents: "A background subagent's results reach Claude as a completion notification in a later turn." Background subagents keep every MCP tool but only a fixed built-in set (Read, Grep, Glob, Bash, Edit, Write, WebFetch, Skill, ToolSearch, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage, Artifact and a few more). https://code.claude.com/docs/en/sub-agents
- `maxTurns`: "When the subagent reaches the limit, Claude Code returns its output marked as partial, and Claude can resume it to continue." Resume is via `SendMessage` to the agent's ID or name; "Resumed subagents retain their full conversation history." Same page.
- Concurrency: "when 20 subagents are running in a session, spawning another with the Agent tool fails with `Concurrent subagent limit reached`"; configurable with `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`. Same page.
- Context warning: "Running many subagents that each return detailed results can consume significant context." Same page.
- `ExitWorktree` is "Not available to subagents that already run in their own working directory, such as with `isolation: worktree`." https://code.claude.com/docs/en/tools-reference
- Task-tracking tools (`TaskCreate` etc.) are not provided by default on current models; opt in with `CLAUDE_CODE_ENABLE_TODO_TOOLS=1`. Same page. (Relevant only if the skill wanted a shared task list; it should not.)

### Workflow tool

- Opt-in: the `ultracode` keyword "is an opt-in only in a prompt you type yourself"; it does not start a workflow from a `-p` prompt or a scheduled task. Asking in plain words ("use a workflow") "also works". The bundled `workflow-authoring` skill says it "does not itself authorize running one." In `-p` and the SDK "Claude Code never shows this prompt" and the call goes through ordinary permission evaluation; a `Workflow` allow rule approves every workflow. https://code.claude.com/docs/en/workflows
- Limits: "Up to 16 concurrent agents, fewer when Claude Code has fewer CPUs available"; 4,096 items per `parallel()`/`pipeline()`; 1,000 agents per run; "No mid-run user input"; "No direct filesystem or shell access from the workflow itself." Same page. The skill text states the cap as `min(16, CPUs - 2)`; this Mac has 18 CPUs, so the cap here is 16.
- Size guideline default is `medium` ("Fewer than 15 agents"), advisory not a cap; `large` is fewer than 50. A run scheduling more than 25 agents or projecting past 1.5M tokens shows a "Large workflow" warning. Same page.
- Resume: completed agents return cached results; "Failed: runs again, and so does every agent that started after it, even ones that completed." Same page.
- Script rules (from the loaded `workflow-authoring` skill): `agent(prompt, {label, phase, schema, model, effort, isolation:'worktree', agentType})`; `pipeline()` has no barrier between stages and is the default; `parallel()` is a barrier and never rejects (failed thunks become `null`); `isolation: 'worktree'` is "EXPENSIVE (~200-500ms setup + disk per agent), use ONLY when agents mutate files in parallel"; `Date.now()`, `Math.random()`, argless `new Date()` throw; `workflow()` nests one level; `budget` exposes the turn token target; `agent()` returns `null` on user skip or terminal API error.
- Structured output: with `schema`, validation retries up to five times (`MAX_STRUCTURED_OUTPUT_RETRIES`). https://code.claude.com/docs/en/workflows

### Other parallel surfaces

- `/batch`: "decomposes the work into 5 to 30 independent units... spawns one background subagent per unit in an isolated git worktree. Each subagent implements its unit, runs tests, and opens a pull request." https://code.claude.com/docs/en/commands
- Agent teams: "experimental and disabled by default", not available under `-p`, and "Agent teams don't isolate teammates in worktrees, so partition the work so each teammate owns a different set of files." Guidance: "Start with 3-5 teammates." https://code.claude.com/docs/en/agent-teams and https://code.claude.com/docs/en/agents
- Headless: "If Claude starts a background subagent or workflow, `claude -p` instead stays open until that work completes"; idle ceiling 10 minutes via `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`. https://code.claude.com/docs/en/headless
- Best practices: "A reviewer running in a fresh subagent context sees only the diff and the criteria you give it, not the reasoning that produced the change"; and the caution that a reviewer told to find gaps "will usually report some, even when the work is sound." https://code.claude.com/docs/en/best-practices
- Anthropic multi-agent research post: "multi-agent systems use about 15× more tokens than chats"; "token usage by itself explains 80% of the variance"; effort scaling: "Simple fact-finding requires just 1 agent with 3-10 tool calls... complex research might use more than 10 subagents with clearly divided responsibilities"; "Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries." https://www.anthropic.com/engineering/multi-agent-research-system

### The owner's own fleets (read from persisted run records and memory)

- **Arcwell gap-closure build, 2026-08-17** (`wf_eea664a7-a97`): 10 agents, 24.5 minutes, 1.67M tokens, 733 tool calls, model claude-fable-5, status completed. Design: "10 owners with disjoint file sets; wiring reported, not applied." Prompt rule: "THE TREE IS SHARED with 9 concurrent agents building OTHER directories. HARD RULE: only create/edit files in your OWNERSHIP list. Any change needed elsewhere... goes verbatim into wiring_needed in your report — the orchestrator applies it." Also: "Verify ONLY your own work... Do NOT run pnpm lint / typecheck / test:all — siblings are mid-edit and results would be noise." One agent (the Rust NotebookLM port) was the exception: it ran in an isolated worktree because it had to edit shared `Cargo.toml` and `lib.rs`, was told to commit and report "the worktree absolute path + commit sha", and "the orchestrator merges your worktree by hand."
- **Gap-closure integrate** (3 agents, 50 min, 711k tokens) applied the wiring with the tree "FULLY GREEN" and whole-workspace gates allowed because the agent was alone in the tree.
- **Gap-closure review** (47 agents on claude-opus-4-8, 19.7 min, 2.56M tokens): six severe reviewers by subsystem, then one verifier per finding with "Your DEFAULT is FALSE_POSITIVE unless you can construct the concrete failure with real code paths." **Gap-closure fixes**: 5 agents over "5 disjoint subsystems".
- **Fabric plan-029 fleet**: six then two agents, each owning a named file list with explicit "Do NOT touch X (other agents own them right now)", common rules: "Never create git worktrees or branches; work directly on the current checkout (main). Do NOT commit or stage anything — the orchestrator commits." Each writes "ONE solid milestone test". Anchors carry the caveat "line numbers in the brief are from 2026-08-26 research and may have drifted slightly."
- **Arcwell fleet 2026-07-06** (memory): 137 packages in an 8-wave dependency graph; the final run used "12 concurrent worktree implementers... serialized merge lane into main (merge agents delete branch+worktree after each merge)"; 135 of 137 merged, 261 commits, three adversarial review cycles. The owner interrupted mid-run to demand "merge everything to main, no branches/worktrees", then re-allowed worktrees for speed once the merge lane deleted them as it went.
- **codex-swift lessons** (memory): parallel agents running `swift build`/`swift test` in one checkout "contend on the SwiftPM `.build` lock — one stalls, the rest block"; a later hardened fleet "drifted hard into scope creep: the diff ballooned to 72 files / +4502/−677... burning ~5.25M tokens / 87 min." Conclusion recorded: "scope each agent to ONE file/change with an explicit 'do not touch anything else' and verify the diff size afterward."
- **Fabric worktree ban** (memory, 2026-07-28): worktrees "hide work from the other sessions' view", the deployed pin "drifted 15 commits behind main", and a fresh worktree's dependency resolution produced "67 phantom test failures." Rule: "work directly in the main checkout on `main`... commit + push early and often."
- **Staging hazard** (memory, repeated three times): `git add <file>` or `git add -A <dir>` in a tree with foreign WIP swept other sessions' hunks into commits and crash-looped a dev gateway. Rule: never `git add -A`; stage explicit paths; check `git status --short` for foreign modifications first.

### Environment facts checked on this machine

- Claude Code 2.1.263; 18 CPUs (Workflow concurrency cap 16).
- `~/.claude/settings.json` sets no `worktree`, `cleanupPeriodDays`, or `workflowSizeGuideline` keys; `~/.claude/agents/` does not exist yet (the docs say the first file in a directory that did not exist at session start needs a restart).
- `~/Projects/arcwell/.gitignore` does not list `.claude/worktrees/`; `git worktree list` there shows only `main`.
- Git 2.54 scratch-repo test of the integration recipe (in the session scratchpad, not in any project): `git merge --ff-only pkg/x` correctly refuses once `main` has advanced; `git rebase main` inside the worktree followed by `--ff-only` merges cleanly; `git worktree remove` refuses a dirty worktree without `--force`; `git format-patch` from a detached worktree plus `git am` onto main integrates with no branch ever existing; a same-file edit on both sides surfaces as a rebase conflict inside the worktree, where `git rebase --abort` returns to a clean state. After each path, `git worktree list` showed only the main checkout and `git branch --list` showed only `main`.

---

## 4. Detailed spec

### 4.1 Decomposition: from design to packages

Decomposition happens once, after the architecture and test-design phases have produced a design document, and it is done by the orchestrator (Fable) in the main loop, not delegated, because it is the highest-leverage judgment in the whole run. Its output is one file, `.drive/plan/packages.json`, plus one brief per package under `.drive/plan/briefs/<id>.md`.

**Procedure.**

1. Enumerate deliverables from the design: every module, screen, endpoint, migration, test suite, document. Each becomes a candidate package.
2. Assign file ownership. Every package lists the paths it may create or edit as globs. Ownership must be disjoint: no path may match two packages' globs. Run the disjointness check below before writing briefs; if it fails, split or merge packages until it passes.
3. Identify files that many packages will want to touch: entry points that register routes or modules, dependency manifests and lockfiles, generated code, the changelog, README, STATUS. Assign every one of these to the **integrator** (the orchestrator or its integrator agent), never to a maker. Makers request changes to these files in their report's `wiring_needed` field; the integrator applies them.
4. Build the dependency graph. A package depends on another when it imports its code, consumes its contract, or needs its migration. Contracts (types, schemas, generated clients) go in their own package that everything else depends on.
5. Cut waves by topological order. Wave 0 is whatever everything depends on (skeleton, contracts, design tokens, test harness) and runs sequentially in the main loop. Later waves contain only packages whose dependencies are already merged.
6. Size each package for one agent context: at most about ten files, at most about 1,500 changed lines, one milestone test, one to two hours of agent time. Anything larger splits along a seam that gives both halves a clear contract. Anything smaller than a single file's worth of change is not a package; fold it into a neighbor or do it in the main loop.
7. Write the briefs (template in 4.2) and record the plan.

**`packages.json` schema (one document for the run).**

```json
{
  "run_id": "2026-09-14-outfit-app",
  "repo": "/abs/path",
  "integrator_owned": ["package.json", "pnpm-lock.yaml", "apps/api/src/index.ts", "CHANGELOG.md", "STATUS.md", "ios/App/App.xcodeproj/**"],
  "waves": [
    {"wave": 0, "mode": "sequential", "packages": ["C0-contracts", "S0-skeleton"]},
    {"wave": 1, "mode": "parallel", "packages": ["B1-identity", "B2-wardrobe", "I1-shell", "I2-client"]}
  ],
  "packages": [
    {
      "id": "B2-wardrobe",
      "goal": "Wardrobe item CRUD with R2 image storage",
      "claim": "A user can upload a garment photo and retrieve it by id with metadata; an upload over 10 MiB is refused with a named error.",
      "owns": ["apps/api/src/domains/wardrobe/**", "apps/api/src/routes/wardrobe*.ts", "apps/api/test/wardrobe/**"],
      "depends_on": ["C0-contracts"],
      "wiring_targets": ["apps/api/src/index.ts", "apps/api/wrangler.jsonc"],
      "tests": ["apps/api/test/wardrobe/*.test.ts"],
      "model": "opus", "effort": "high", "max_turns": 120, "time_budget_min": 90,
      "isolation": "shared",
      "status": "planned"
    }
  ]
}
```

`isolation` is `shared` by default. It becomes `worktree` only when a package cannot be made disjoint (see 4.5) and the orchestrator records why.

**Disjointness check (run before briefs are written, and again before each wave starts).**

```bash
python3 - <<'EOF'
import json, itertools, fnmatch, pathlib
plan = json.load(open('.drive/plan/packages.json'))
pk = {p['id']: p for p in plan['packages']}
def matches(glob, path): return fnmatch.fnmatch(path, glob) or fnmatch.fnmatch(path, glob.replace('/**','/*'))
paths = [str(p) for p in pathlib.Path('.').rglob('*') if p.is_file() and '.git/' not in str(p)]
bad = []
for a, b in itertools.combinations(pk.values(), 2):
    for ga in a['owns']:
        for gb in b['owns']:
            if ga == gb or ga.startswith(gb.rstrip('*')) or gb.startswith(ga.rstrip('*')):
                bad.append((a['id'], b['id'], ga, gb))
            elif any(matches(ga, p) and matches(gb, p) for p in paths):
                bad.append((a['id'], b['id'], ga, gb))
for p in pk.values():
    for g in p['owns']:
        for i in plan['integrator_owned']:
            if matches(g, i) or matches(i, g): bad.append((p['id'], 'INTEGRATOR', g, i))
print('OK: ownership disjoint' if not bad else '\n'.join(f'OVERLAP {x}' for x in bad))
EOF
```

The check is deliberately conservative: prefix overlap between two globs counts as a conflict even when no current file matches both, because the packages will create files.

### 4.2 The package brief

Every maker receives exactly one brief, self-contained, written so that an agent with an empty context and the repo can act on it. The brief is the unit of quality control: vague briefs produced duplicated searches in Anthropic's research system and scope drift in this owner's fleets. Template:

```markdown
# Package B2-wardrobe

## Goal
One paragraph. What exists when you are done, in user-visible terms.

## Behavioral claim (what a test must be able to refute)
"A user can upload a garment photo and retrieve it by id with metadata; an upload over 10 MiB is refused with a named error."

## Inputs you rely on (already merged on main; read them, do not modify them)
- packages/contracts/src/wardrobe.ts (types WardrobeItem, UploadRequest)
- docs/design/backend.md §4 (storage layout)
- docs/design/test-plan.md §B2

## Contract you must satisfy (other packages code against this today)
- POST /wardrobe/items  -> 201 {id}; 413 {error:"payload_too_large"} over 10 MiB
- GET  /wardrobe/items/:id -> 200 WardrobeItem | 404
Do not change these shapes. If the design forces a change, stop and report it as `blocked` with the exact reason.

## Files you own (create/edit only these)
- apps/api/src/domains/wardrobe/**
- apps/api/src/routes/wardrobe*.ts
- apps/api/test/wardrobe/**

## Files you must not touch (someone else owns them right now)
- apps/api/src/index.ts, wrangler.jsonc, package.json, any lockfile, anything under apps/api/src/domains/identity/**
Any change you need there goes verbatim, as a patch or exact lines, into `wiring_needed`.

## Tests to make pass (write them first; at least one must try to refute the claim)
- apps/api/test/wardrobe/upload.test.ts: happy path; 10 MiB + 1 byte refused; missing auth refused
- Production constraints the harness must enforce: D1 binds at most 100 variables per statement; R2 object keys are content-addressed. If the local shim is kinder than production on either point, teach the shim first and say so in `gates_run`.

## Commands you may run
- `pnpm vitest run apps/api/test/wardrobe` (your tests only; the tree is shared and siblings are mid-edit, so whole-workspace commands are noise and forbidden)
- Never: git add/commit/stash/checkout, repo-wide formatters, pnpm add/cargo add (list needed deps in `deps_requested`)

## Done means
All three: your tests pass with the exact command shown in `gates_run`; every file you changed is inside your ownership list; the report is honest about what is not verified.

## Budget
120 turns, 90 minutes. If you are at 80 turns and not converging, stop, report `partial`, and list the remaining work precisely.

## Report (your final message is ONLY this JSON)
{status, files, tests, gates_run, wiring_needed, deps_requested, honest_gaps, summary<=1500 chars}
```

Two details matter more than they look. The "Inputs you rely on" list pins the maker to merged reality rather than repo archaeology, which is the drift channel his August post-mortem identified ("scope contamination from repo archaeology"). The "Done means" clause binds the maker to the ownership list, which lets the verifier compute drift mechanically.

### 4.3 Execution modes and the decision rule

There are four execution modes. The skill picks by counting packages in the next wave and asking whether any package needs shared files.

| Mode | When | Mechanics |
|---|---|---|
| **Solo** | Wave has 1 package, or the task is a bug fix, or packages are dependent on each other | Orchestrator implements in the main loop; one verifier subagent after |
| **Agent fan-out, shared tree** (default for parallel work) | 2 to 8 disjoint packages | One `Agent` call per package, `run_in_background: true`, `subagent_type: drive-maker`, per-call `model`; results arrive as completion notifications; follow-ups via `SendMessage` |
| **Workflow fan-out** | 6 or more packages in a wave, or a per-item multi-stage pipeline (migrations: discover → transform → verify each), or any read-only swarm (review, hypothesis hunt) of any size | Orchestrator authors a script with `pipeline()`/`parallel()`, `schema` on every `agent()`, `phase()` per wave; results stay in script variables; `/workflows` for progress |
| **Worktree lane** (exception) | A package must edit integrator-owned or generated files, must run a build that locks a shared cache, or is one arm of a tournament | Orchestrator creates the worktree from `HEAD`, the maker commits inside it, the integrator merges and deletes in one step (4.5) |

Rules that qualify the table:

- A wave of makers in the shared tree never exceeds 8 concurrent, whatever the harness cap, because every maker beyond that raises the odds of two agents needing the same unowned file and because the integrator has to absorb their wiring afterwards. Read-only swarms can go to the cap (16 in a Workflow, 20 for Agent calls).
- The Workflow tool is preferred for read-only swarms and for large mechanical waves; the Agent tool is preferred for small mutation waves. The reason is the resume rule: a failed Workflow agent reruns every later agent, so mutation waves under Workflow need idempotent makers (each brief begins "inspect your owned files; if the work is already present, verify and report instead of redoing it"). Agent-tool fan-out has no such replay.
- The skill supplies the Workflow opt-in itself. SKILL.md carries the line "Invoking /drive is the user's standing instruction to use the Workflow tool for fan-out phases when the decision rule selects one." For unattended `-p` runs, `Workflow` must also be in the permission allow rules, because the keyword path does not exist there.
- Agent teams are not used: experimental, unavailable under `-p`, no worktree isolation, and their shared task list adds an approval-shaped surface the owner will not process.
- `/batch` is not used: it opens a pull request per unit, which is a branch left behind by construction.
- Headless `claude -p` loops are acceptable for purely mechanical sweeps (thousands of near-identical edits) but only with `--bare`, `--allowedTools` scoped to `Edit` and the test command, and an integrator commit per batch; the skill should reach for them rarely.

### 4.4 Rules for makers in the shared tree

These are the operating rules from the owner's proven fleets, made mandatory:

1. Edit only owned paths. Before reporting, run `git status --porcelain` and confirm every listed path is inside the ownership globs; anything else is reverted by the maker (`git checkout -- <path>`) or, if the maker cannot tell whose it is, reported and left alone.
2. Never run `git add`, `git commit`, `git stash`, `git checkout <branch>`, `git rebase`, or any repo-wide formatter. Only the integrator touches git.
3. Run only your own tests, with the exact command from the brief. Whole-workspace type checks, lints, and test runs are the integrator's job at wave end, when the tree is quiet.
4. Install nothing. List dependencies in `deps_requested` with the reason; the integrator installs once per wave so the lockfile changes once.
5. Put cross-file needs in `wiring_needed` as exact lines or a unified diff against the current file, not as prose.
6. Do not compile a shared build product concurrently with siblings when the toolchain holds a global lock (SwiftPM `.build`, Cargo target dir, Xcode DerivedData). Use a per-package target directory when the toolchain supports it (`CARGO_TARGET_DIR=/tmp/<run>/<pkg>`, `xcodebuild -derivedDataPath /tmp/<run>/<pkg>`), otherwise report `tests: deferred to integrator` and let the integrator lane compile.
7. Be idempotent on restart: first inspect owned files; if work is already present, verify and report rather than redo.
8. Report at most 1,500 characters of summary, plus paths. No diffs, no full test logs; the tail of a failing test's output up to 1,000 characters is allowed in `honest_gaps`.

### 4.5 The worktree lane (exception path)

Use only when 4.1 step 3 cannot make a package disjoint, or for tournament arms. The orchestrator, not the maker, decides, and records the reason in `packages.json`.

**Creation.** The orchestrator creates the worktree from the current local `HEAD` so the base is explicit and includes unpushed commits:

```bash
ID=B7-rust-bridge
WT=".claude/worktrees/pkg-$ID"
grep -qx '.claude/worktrees/' .gitignore || printf '.claude/worktrees/\n' >> .gitignore   # once per repo, committed with wave 0
git worktree add -b "pkg/$ID" "$WT" HEAD
```

If the skill instead uses `isolation: worktree` on the Agent call (which buys enforcement against edits to the main checkout), it must first ensure `~/.claude/settings.json` contains `{"worktree": {"baseRef": "head"}}`; otherwise the subagent branches from `origin/main`, and this owner commits to local `main` without always pushing. The maker's report must then include `worktree_path`, `branch`, and `head_sha`, because the docs do not specify how a subagent's worktree is named.

**Maker rules in a worktree.** Same as 4.4 except: the maker may edit the shared files named in its brief, must `git add <explicit paths>` and `git commit` inside the worktree (never `git add -A`), must not push, and must not merge. A worktree is a fresh checkout, so the brief tells the maker how to install dependencies there (or the repo carries a `.worktreeinclude` for `.env` files) and which per-worktree build cache to use.

**Integration (one step, serialized, never in parallel with another merge).**

```bash
PRE=$(git rev-parse HEAD)
git -C "$WT" rebase main || { echo "conflict in $ID"; git -C "$WT" status --porcelain; exit 1; }   # resolve inside the worktree, or abort and re-scope
git merge --ff-only "pkg/$ID"                        # main never gets a merge commit
<full gates>                                         # the main checkout has the environment; run everything here
# on red: git reset --keep "$PRE"; keep the worktree for the fixer; do not proceed to removal
git worktree remove "$WT" && git branch -d "pkg/$ID"
git worktree prune
```

Conflicts are resolved by an integrator agent inside the worktree with the two briefs in hand, never by hand-editing `main`. If a conflict is deeper than an import block or a registration line, that is a decomposition error: abort the rebase, drop the package's worktree, and re-scope the package for the next wave.

**Patch alternative for tiny exceptions.** When a package touches one shared file for one hunk, skip the branch entirely: the maker works in a detached worktree (`git worktree add --detach`), commits, and the integrator applies `git format-patch -1` output with `git am`, then removes the worktree. Tested; leaves no branch at any point.

**Audit at the end of every wave, and again before the run reports done.**

```bash
git worktree list --porcelain | grep -c '^worktree ' | grep -qx 1 || { echo "ORPHANED WORKTREES"; git worktree list; exit 1; }
[ -z "$(git branch --list 'pkg/*' 'worktree-*')" ] || { echo "ORPHANED BRANCHES"; git branch --list 'pkg/*' 'worktree-*'; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "UNCOMMITTED"; git status --short; exit 1; }
```

A run whose audit fails is not done, whatever the tests say. The orchestrator fixes it (merge or discard, remove, delete) before writing the status file.

### 4.6 Wave integration protocol (shared tree)

When the last maker in a wave reports (or its budget expires), the integrator runs this sequence, alone in the tree:

1. Collect reports. Write each to `.drive/packages/<id>/report.json`. Mark `partial` and `blocked` packages for 4.9.
2. Apply `wiring_needed` from every `complete` package to the integrator-owned files, one package at a time, checking each item off in `.drive/packages/<id>/wiring.md`. Apply `deps_requested` with one install command.
3. Run the full gates: type check, lint, whole test suite, build, and at least one check against the real thing rather than a shim (a `wrangler dev` request against local D1; a simulator build; a real migration apply on a scratch database).
4. On green, commit **per package**, staging explicit paths from the report's `files` list plus the wiring files touched for that package. Never `git add -A`. Message format: `feat(<area>): <goal> [pkg <id>]`. Update STATUS/CHANGELOG in a final `chore(status): wave N` commit owned by the integrator.
5. On red, classify the failure by owning package (the failing test path maps to an ownership glob), and hand that package to a fixer in the next round with the failing output. Do not commit red. If the red is in a wiring seam rather than a package, the integrator fixes it directly; that is what the integrator owns.
6. Run the audit from 4.5.
7. Only then spawn the wave-level verifier (4.7).

The order matters: wiring before gates, gates before commits, audit before verification. Verification of an uncommitted tree produces a verdict about a state that can silently change.

### 4.7 Maker and verifier pairing

Three verification layers, each with fresh context, each barred from editing.

**Per-package verifier** (runs after the package's files are integrated and committed, before the wave is called done). Receives the brief, the commit range, and nothing from the maker's reasoning. Instructions:

- Read the diff for the commit range and list every changed file; flag any outside the ownership list (scope drift is a finding of severity high regardless of code quality).
- Restate the behavioral claim and try to refute it: run the package's tests, then write and run one additional test the maker did not write, aimed at the claim's weakest point (boundary, concurrency, malformed input, the production constraint the shim might be kinder about).
- Check `wiring_needed` was applied (grep the target files).
- Verdict schema: `{verdict: PASS|FAIL|PARTIAL, drift_files: [], refutation_attempted: string, refutation_result: string, gaps: [], severity: ...}`.
- Default to FAIL when uncertain, and report style opinions nowhere.

**Wave-level integration verifier.** After all packages in a wave are merged and the gates are green, one verifier checks the seams: every contract consumer against the contract package, every wiring line, and the "kinder than production" question for each new shim or fake introduced in the wave. It also re-runs the wave's full gates itself rather than trusting the integrator's transcript.

**Final audit** (end of run, Fable, fresh context via subagent). Not a code review. It takes the original spec and the run's claims (STATUS, package reports) and checks each conclusion-shaped statement two ways: did the spec ask for this, and can it be falsified in one command. "Blocked" and "impossible" claims get the same evidence bar as "works". This is the layer that would have caught the August run declaring tool families "platform-blocked" from stale docs. Ground truth precedence is the owner's: working-tree code and tests over proof artifacts over STATUS over prose.

For large review swarms, use the two-stage shape the owner already runs: N severe reviewers by subsystem produce structured findings; one verifier per finding votes with a default of false positive; only confirmed findings become fix packages, assigned by ownership, in a disjoint wave.

### 4.8 Swarm sizing and orchestrator context

**Per scope.**

| Scope | Makers in parallel | Verifiers | Total agents per run (typical) | Mode |
|---|---|---|---|---|
| One-file bug | 0 (solo) | 1 | 3 to 6 (hypothesis investigators are read-only and may run 3 to 5 in parallel) | Solo + Agent fan-out for investigation |
| Small feature, fewer than 3 packages | 0 to 2 | 1 per package | under 8 | Solo or Agent fan-out |
| Feature, 3 to 8 packages | up to 5 | 1 per package + 1 wave verifier | 10 to 20 | Agent fan-out |
| Greenfield app, migration, 8 to 40 packages | up to 8 per wave (12 for purely mechanical packages) | 1 per package + 1 per wave + review swarm | 40 to 120 across the run, in several workflows | Workflow per wave, Agent tool for the integrator |
| Mechanical sweep, hundreds of items | up to the cap (16) | sampled, 1 per 10 items + full gates | bounded by `budget` | Workflow `pipeline()` |

Stay under the harness's "Large workflow" warning (25 agents or 1.5M projected tokens) per workflow run by splitting waves into separate workflows; the owner stays in the loop between them anyway, which is what the `workflow-authoring` skill recommends for multi-phase work. Every fleet in his history that succeeded ran as several sequential workflows (build, integrate, review, fix), not one.

**Orchestrator context hygiene.** The orchestrator's context is the scarcest resource in a long run, and it is the one thing that cannot be re-spawned.

- Every worker returns through a `schema`. Summary fields are capped (1,500 characters) and logs are capped (1,000 characters of tail). Paths, not contents.
- Workers write their full report to `.drive/packages/<id>/report.json` themselves; the orchestrator receives the status line and the path. After compaction, the orchestrator re-reads files, not memory.
- Never ask a worker to "show the diff". The verifier reads diffs; the orchestrator reads verdicts.
- Wave state lives in `.drive/plan/packages.json` (`status` per package: planned, running, complete, partial, blocked, merged, verified, failed) and is updated after every report, so a resumed session can continue from the file.
- The orchestrator runs gates through the integrator agent for anything beyond a small feature; a full test log in the orchestrator's context is the most common way to lose a run to compaction.

### 4.9 Failure handling

Package outcomes are `complete`, `partial`, or `blocked`; a missing report (crash, `null` from a Workflow agent, budget expiry) is treated as `partial` with no summary.

1. **Partial.** Resume once via `SendMessage` to the same agent with the exact remaining items (the agent keeps its context and its prompt cache). If it returns `partial` again, do not resume a third time: the diagnosis is wrong somewhere. Re-scope.
2. **Blocked.** Classify from the report: missing dependency (integrator installs, package re-runs next wave), contract ambiguity (orchestrator decides, updates the contract package, re-briefs), environment (a tool or credential the run cannot obtain; record as an honest external blocker with the exact command needed, never fake it).
3. **Failed twice with the same model.** Escalate one tier with a fresh context and a brief that includes what was tried and why it failed: sonnet to opus, opus to fable. Same prompt, same model, third time is forbidden.
4. **Poisoned.** A package whose changes break the tree and whose maker cannot fix it in one round: in the shared tree, revert its owned paths (`git checkout -- <globs>` for tracked files, delete untracked files it created, using its report's `files` list); in a worktree, remove the worktree and delete the branch. Mark `failed`, move dependent packages to a later wave, continue the current wave. A poisoned package never blocks its siblings' integration.
5. **Budgets.** `maxTurns` in the maker agent definition (120 default; 60 for sonnet mechanical packages; 200 for opus domain packages), a wall-clock budget in the brief with instructions to stop and report at eighty percent, and a Workflow-level `budget` for large waves. Expired budgets produce `partial`, never silence.
6. **Workflow resume.** Before relaunching a stopped workflow that contained makers, run the audit and `git status`; a rerun of an already-merged maker on a non-idempotent brief will edit merged files. Prefer authoring a continuation script that skips merged packages by reading `packages.json` status (passed in via `args`).

### 4.10 Parallel experiments (tournament)

Worth it in exactly three situations: design alternatives whose trade-offs cannot be settled by reading (two storage layouts, two state-management approaches for the iOS app); performance approaches with a measurable benchmark; and flaky or deep bugs with competing hypotheses. Not worth it for ordinary features, where one well-briefed maker plus a verifier is cheaper than three makers plus a judge.

Mechanics:

1. The orchestrator writes one brief per arm with an identical goal, identical acceptance tests, and a distinct approach constraint. Arms run in worktrees (this is a legitimate use: losers are discarded, and the arms will edit overlapping files by design). Each arm commits inside its worktree and reports `head_sha`, benchmark numbers if any, and a one-paragraph rationale.
2. A judge with fresh context (Fable or Opus, never an arm's author) receives the rubric, the acceptance tests, the benchmark numbers, and read access to each worktree. It ranks with a structured verdict and must name the deciding evidence. For taste-based comparisons (naming, UX copy, component structure) use three Sonnet-low voters on pairwise comparisons and take the majority.
3. The winner merges through the 4.5 lane. Losers are removed in the same step (`git worktree remove --force`, `git branch -D`). One paragraph per loser goes into the research ledger with why it lost, so the run does not re-derive the comparison later.
4. For bug hypotheses, arms are read-only investigators unless a hypothesis needs a probe patch; probes happen in a worktree and the worktree is removed whether or not the hypothesis survives. Only the confirmed fix is applied on `main`.

### 4.11 Worked decompositions

**Fashion and outfit iOS app (Cloudflare backend, Swift front end).**

Design-time decision that enables parallelism: the iOS app is a SwiftPM workspace with one package per feature (`ios/Packages/DesignSystem`, `ios/Packages/APIClient`, `ios/Packages/Wardrobe`, `ios/Packages/Outfits`, `ios/Packages/Onboarding`) and a thin app target that composes them. Without this, iOS makers cannot compile in parallel (one Xcode project, one DerivedData lock), and wave 1 on the iOS side becomes sequential.

Wave 0, sequential, orchestrator: repository skeleton with gates wired (`pnpm typecheck`, `pnpm test`, `swift build` per package, `xcodebuild` for the app target); `C0-contracts` (OpenAPI source of truth under `contracts/`, a generation script producing TypeScript types and Swift `Codable` models into integrator-owned generated directories); `D0-design-tokens` (colors, type scale, spacing, component inventory, and reference mockups per screen produced with the `design` skill into `design/screens/*.png` for later vision comparison); `T0-harness` (backend test harness that enforces production constraints: D1's 100 bound variables per statement, R2 object size limits, Workers CPU time; a no-network test setup); `M0-schema` (D1 migrations skeleton; migration files are integrator-owned and append-only thereafter). Commit per package.

Wave 1, parallel, 7 makers: `B1-identity` (auth, sessions; `apps/api/src/domains/identity/**`, `routes/auth*`), `B2-wardrobe` (items, R2 upload, tagging), `B3-outfits` (composition rules, scoring, "today's outfit"), `B4-context` (weather and calendar adapters under `apps/api/src/adapters/{weather,calendar}/**`), `I1-design-system` (SwiftUI components from tokens, `ios/Packages/DesignSystem/**`), `I2-api-client` (Swift client over the generated models, auth storage in Keychain, `ios/Packages/APIClient/**`), `T1-contract-tests` (backend tests that drive every endpoint in the contract through the harness, `tests/contract/**`). Wiring targets: `apps/api/src/index.ts`, `wrangler.jsonc`, `Package.swift` at the workspace root. Integrator applies wiring, runs gates, commits per package, audits, spawns 7 package verifiers and 1 wave verifier.

Wave 2, parallel, 5 makers: `I3-wardrobe-ui` (capture via camera and photo picker, upload progress, `ios/Packages/Wardrobe/**`), `I4-outfits-ui` (browse, rate, today view, `ios/Packages/Outfits/**`), `I5-onboarding-settings`, `B5-recommendation-model` (model-assisted composition behind the B3 interface; the routing decision for which model to call lives here), `T2-integration` (backend tests through `wrangler dev` against local D1 and R2, not the shim). Integrator composes the app target (integrator-owned `ios/App/**`) and wires B5.

Wave 3, mixed: `E1-simulator-flows` (build, launch, tap and swipe through the iOS Simulator MCP, screenshot each screen; a vision verifier compares each screenshot to `design/screens/*.png` and to the screen's acceptance description and returns a structured gap list); `E2-live-proof` (deploy the Worker to a preview environment and run T2 against it, which is the run's first honest "live proof" rung); review swarm (6 severe reviewers by subsystem, verifier per finding) producing fix packages assigned by ownership; final audit; STATUS and docs by the integrator.

**Dashboard feature on an existing product.**

Wave 0, read-only fan-out, 3 to 4 investigators: existing data access layer and query patterns, the chart library already in use and its conventions, routing and navigation registration, auth and permissions for the new page. Structured findings only.

Wave 1: usually only two packages are genuinely independent, `P1-query-api` (endpoint plus tests; owns a new module directory and a new test directory) and `P2-widgets` (chart components against a fixture shaped like the P1 contract, plus a visual snapshot). Everything else (route registration, navigation entry, feature flag, docs) is integrator wiring. If the investigation shows P1 and P2 cannot be separated by a fixture-shaped contract, the whole feature runs solo with one verifier; a two-package swarm is not worth the integration overhead.

Wave 2: `P3-page` composes widgets and data (owned by the integrator or a single maker), `P4-e2e-vision` drives the page in Chrome DevTools or Playwright, screenshots it, and a vision verifier compares against the mockup and the acceptance list. One verifier per package, one integration verifier, no review swarm unless the feature touches auth or billing.

**Gateway migration (external project into a core platform service).**

Wave 0, Workflow pipeline, read-only: discover every consumer of the external gateway (`pipeline()` over candidate directories, each agent returning `{module, import_sites, call_shapes, tests_touching}`), and inventory the gateway's public surface and its configuration and secrets. Output: a consumer list that becomes the wave-2 package list.

Wave 1, sequential or 2 makers: `G1-core-service` (the gateway re-homed inside the platform behind the same interface, with its own tests and a contract test against recorded traffic shapes), `G2-shim` (an adapter at the old import path that forwards to G1, so consumers can move one at a time). Integrator wires G1 into the platform's composition root and feature-flags the switch.

Wave 2, parallel, one package per consumer module (often 5 to 15, all disjoint by directory): switch imports and call shapes to G1, update that module's tests, keep behavior identical. Mechanical enough for Sonnet on most modules; Opus on the two or three with the most call-shape variation. This is where a Workflow `pipeline()` with idempotent briefs fits well: each item is small, the same shape, and verification per item is one test command.

Wave 3: `G3-remove` deletes the shim and the external dependency (integrator-owned manifests and lockfile change here); a grep gate proves no import of the old path remains; live proof runs the platform against G1 in a staging environment with the flag on; rollback is the flag. Review swarm focuses on secrets handling, retries, and cost accounting, because those are where a gateway migration silently regresses.

### 4.12 Anti-patterns (the skill must refuse these)

- Two packages owning one file, or a maker editing outside its ownership list. Caught by the disjointness check before the wave and by `git status` against the ownership globs after.
- Worktrees or branches surviving a wave. Caught by the audit; the run is not done until it passes.
- Merging without the full gates, or verifying an uncommitted tree.
- Workers pasting diffs or full logs into the orchestrator. Prevented by `schema` with capped fields.
- Parallelizing dependent packages ("the client and the endpoint at the same time" without a contract package first).
- A swarm for a one-file bug. Solo plus one verifier, always.
- Whole-workspace test or lint runs by makers while siblings are mid-edit.
- Concurrent builds against a shared toolchain lock.
- Resuming the same package on the same model a third time with the same brief.
- Letting a boundary report's scope items flow unchecked into the next wave's briefs.
- Opening pull requests as an integration mechanism in the owner's own repos.

---

## 5. Conditionals by project shape

**Greenfield app.** Full machinery: wave 0 sequential (skeleton, contracts, design tokens, harness, schema), two to three parallel maker waves, per-package and per-wave verifiers, review swarm, final audit. Modularize the front end for parallel compilation at design time. Expect 60 to 120 agents across several workflows. Use the worktree lane only for the package that must edit shared build manifests (usually one per language).

**Deep bug hunt.** No maker swarm. A read-only investigator fan-out (3 to 5 competing hypotheses, each told to try to disprove the others' likely explanations, structured findings), then one fixer in the main loop, then one verifier who reproduces the original failure before the fix and the absence of it after. Probes run in a worktree only if they need code changes, and the worktree is removed whether or not the hypothesis survives. Tournament pattern applies to the hypotheses, not to fixes.

**Feature on an existing product.** Investigate first (read-only fan-out), then decide: fewer than three independent packages means solo with a verifier; three to eight means Agent fan-out in the shared tree with integrator wiring. Never worktrees here: the existing product has one environment and one set of installed dependencies, and the fabric memory documents exactly how a worktree's dependency drift produced phantom failures.

**Migration or consolidation.** Workflow `pipeline()` for discovery and for the per-consumer switch wave, with idempotent briefs; sequential core-service and shim packages first; grep gate and flag-based rollback last. Worktrees only if consumer packages must edit shared manifests, which good decomposition avoids by giving the manifests to the integrator.

**Research plus website.** Research is a read-only fan-out (deep-research skill or a Workflow multi-modal sweep) and does not touch git at all. The website decomposes by section (home, project, team, blog, docs) with a shared design-token and layout package in wave 0; sections are disjoint directories, so shared-tree fan-out applies; vision verification per page against the design canvas. Tournaments earn their place here for design direction: two or three visual directions in worktrees, judged by voters against the brief, winner merged, losers removed.

**Pure research report.** No git, no packages; fan-out and synthesis only; this component contributes the report schema and the context hygiene rules.

**Refactor or simplification.** Disjoint by module; the `simplify` skill already runs in an isolated worktree by its own design, so invoke it and let it clean up; for hand-rolled refactor waves, shared tree with ownership, one behavior-preservation verifier per package that runs the pre-existing tests unchanged.

**Ops or incident.** Solo. Parallel only for read-only diagnosis across systems. No worktrees.

**Data pipeline, CLI tool, library or SDK.** Same as feature or greenfield by size. Libraries add a public-API contract package in wave 0 and a consumer-facing example package as a verifier.

---

## 6. Model and effort assignment

| Role | Model | Effort | Tools | Isolation | Predefined agent |
|---|---|---|---|---|---|
| Decomposer (orchestrator itself) | fable | high (xhigh for greenfield) | all | none | no (main loop) |
| Maker, domain logic, concurrency, UI | opus | high | all except git commands by instruction | shared tree | `drive-maker` |
| Maker, scaffolds, generated clients, tests from spec, docs, mechanical migration items | sonnet | medium | same | shared tree | `drive-maker` with per-call `model: sonnet` |
| Maker for shared-file or tournament packages | opus | high | all | worktree | `drive-maker-isolated` |
| Package verifier | opus (sonnet high for small mechanical packages) | high | Read, Grep, Glob, Bash; no Edit or Write | none | `drive-verifier` |
| Refutation and pairwise voters, structured graders | sonnet | low | Read, Grep, Glob, Bash | none | `drive-judge` |
| Integrator | opus | high | all | none (works in main checkout) | `drive-integrator` |
| Wave verifier | opus | high | as verifier | none | `drive-verifier` |
| Tournament judge and final auditor | fable | high | as verifier | none | `drive-verifier` with per-call `model: fable` |

Sonnet at low effort is right for graders that answer a structured question about an artifact (does this finding reproduce, which of two options better satisfies the rubric). It is not right for the per-package verifier, whose job is to design and execute a refutation; that is hard-but-bounded work and belongs on Opus, which is also what the owner's own 47-agent review fleet ran on.

One definition per role is enough because the Agent tool's per-invocation `model` parameter overrides frontmatter (verified order). The skill's install step creates `~/.claude/agents/` and these files, and tells the user once that a restart is needed because the directory did not exist at session start.

**`~/.claude/agents/drive-maker.md`**

```markdown
---
name: drive-maker
description: Implements exactly one /drive work package in the shared checkout under strict file ownership. Never touches git.
model: opus
effort: high
maxTurns: 120
---
You implement one package from a /drive run. Your brief is the whole of your assignment; the design documents it names are the whole of your inputs. Other agents are editing other directories in this same checkout right now.

Rules you do not bend:
- Create or edit only paths inside the ownership list in your brief. Before you report, run `git status --porcelain` and confirm every path is yours; revert anything that is not.
- Never run git add, git commit, git stash, git checkout <branch>, git rebase, or a repo-wide formatter. The integrator owns git.
- Run only the test command in your brief. Whole-workspace type checks, lints, and test suites are the integrator's job.
- Install nothing; list dependencies in deps_requested. Edits you need in files you do not own go verbatim into wiring_needed as exact lines or a unified diff.
- Write the refuting test before the code: at least one test must try to make the behavioral claim false.
- If your work is already present when you start (a restart), verify it and report; do not redo it.
- If the test harness is kinder than production on any constraint your brief names, teach the harness first and say so.
- Stop at eighty percent of your budget if you are not converging; report partial with the exact remaining items.

Your final message is only the JSON report your brief specifies: status (complete|partial|blocked), files, tests, gates_run (exact commands and outcomes), wiring_needed, deps_requested, honest_gaps, summary (1,500 characters at most). Never claim what you did not run.
```

**`~/.claude/agents/drive-maker-isolated.md`**: identical body with `isolation: worktree` in the frontmatter and two changed rules: you may edit the shared files your brief names; you must `git add <explicit paths>` and `git commit` inside your worktree (never `git add -A`, never push, never merge) and report `worktree_path`, `branch`, and `head_sha`. Requires `worktree.baseRef: "head"` in user settings, which the skill's install step writes.

**`~/.claude/agents/drive-verifier.md`**

```markdown
---
name: drive-verifier
description: Independent verifier for one /drive package or wave. Fresh context, read and execute only, tries to refute the behavioral claim.
model: opus
effort: high
maxTurns: 80
disallowedTools: Edit, Write, NotebookEdit
---
You verify work you did not write. You receive a brief, a commit range or diff, and nothing of the maker's reasoning. Your default verdict is FAIL until evidence moves it.

Do, in order:
1. List every file changed in the range. Any file outside the brief's ownership list is a high-severity finding regardless of its content.
2. Restate the behavioral claim. Run the package's tests with the exact command in the brief and record the outcome.
3. Design one refutation the maker did not write: a boundary, a race, malformed input, or the production constraint the brief names. Run it (a temporary test file under /tmp or a one-off command; you may not edit repository files).
4. Check that every wiring_needed item was applied in the target files.
5. For any shim or fake introduced, ask where it is kinder than the real thing, and say so.
Report only the structured verdict: verdict (PASS|FAIL|PARTIAL), drift_files, refutation_attempted, refutation_result, gaps, severity. Do not report style. Treat "blocked" or "impossible" claims in the maker's report with the same evidence bar as "works".
```

**`~/.claude/agents/drive-integrator.md`**

```markdown
---
name: drive-integrator
description: Integrates a finished /drive wave into main: applies wiring, installs requested deps, runs full gates, commits per package with explicit paths, merges and deletes any worktree in one step, audits for orphans.
model: opus
effort: high
maxTurns: 150
---
You are the only agent that touches git in this run. You work alone in the main checkout after the makers of a wave have reported.

Sequence, never reordered: read each package report under .drive/packages/<id>/report.json; apply wiring_needed to the integrator-owned files one package at a time, ticking items off; run one install for all deps_requested; run the full gates including at least one check against the real system rather than a shim; on green, commit per package staging only the paths listed in that package's report plus the wiring files you touched for it, message `feat(<area>): <goal> [pkg <id>]`; on red, map the failing test to its owning package by path and record it for a fixer, commit nothing red.

For a worktree package: `git -C <wt> rebase main`, resolve conflicts inside the worktree using both briefs, `git merge --ff-only pkg/<id>`, run the full gates on main, then `git worktree remove <wt> && git branch -d pkg/<id>` in the same step. On red after merge, `git reset --keep <pre-merge sha>` and keep the worktree for the fixer.

Before you report: `git worktree list` must show only the main checkout, `git branch --list 'pkg/*' 'worktree-*'` must be empty, `git status --porcelain` must be empty. If any check fails you are not done. Never `git add -A`. Never open a pull request. Never force-push.
Report: merged packages with commit shas, red packages with the failing command and 1,000 characters of output tail, audit result.
```

**`~/.claude/agents/drive-judge.md`**: `model: sonnet`, `effort: low`, `maxTurns: 25`, `disallowedTools: Edit, Write, NotebookEdit`; body: answer exactly the structured question posed (CONFIRMED|FALSE_POSITIVE|UNCERTAIN for a finding, or A|B for a pairwise comparison), default to FALSE_POSITIVE or UNCERTAIN unless the evidence is concrete, cite the file and line or the rubric criterion that decided it, nothing else.

---

## 7. Failure modes and how the component produces mirage completion

**A maker reports complete without running anything.** The report schema requires `gates_run` with exact commands and outcomes; the verifier re-runs them. A report whose `gates_run` is empty is treated as `partial`.

**Green package tests, red integration.** Contract drift between packages. Caught by wave gates before commit and by the wave verifier's seam check. Prevented by the contract package in wave 0 and by makers being forbidden from changing contract shapes.

**Scope drift disguised as diligence.** The codex-swift fleet implemented five unrequested features with green tests. Caught mechanically: changed files outside ownership are a high-severity finding for the verifier and a revert for the integrator. Prevented by the brief's "Inputs you rely on" list and the rule that boundary reports never flow into next-wave briefs unchecked.

**Orphaned worktrees and branches presented as done.** The harness leaves changed subagent worktrees on disk for thirty days and never merges them; `-p` runs clean nothing. Caught by the wave and run audits, which are hard gates on "done".

**A verifier that only reads.** Reading a diff certifies plausibility, not behavior. The verifier definition requires executing the package's tests and one refutation of its own.

**Kinder-than-production harness.** Makers test against fakes; the run's first real check comes too late. Prevented by wave 0's harness package encoding known production constraints, by the brief naming them, and by the integrator's requirement of at least one real-system check per wave. The verifier asks the "where is the shim kinder" question of every new fake.

**Wiring reported but never applied.** A package is "complete" but its route is never mounted. Caught by the verifier's grep of wiring targets and by the wave verifier.

**Blocked claims from stale documents.** A maker declares something impossible based on a README. The verifier applies the same evidence bar to "blocked" as to "works"; the final audit asks whether the spec contained the goal at all.

**Orchestrator context exhaustion mid-wave.** A full test log or a pasted diff pushes the orchestrator into compaction and it loses the wave state. Prevented by schema caps, by reports living in `.drive/packages/`, and by the integrator running gates. Recovery is reading `packages.json`, never memory.

**Build-lock deadlock read as idle agents.** Concurrent `swift build` or `cargo test` in one checkout wedges; the orchestrator sees stalls. Prevented by per-package target directories or by deferring compilation to the integrator lane; the brief says which.

**Workflow relaunch re-applying edits.** A failed maker in a Workflow fan-out reruns every later maker. Prevented by idempotent briefs and by preferring Agent-tool fan-out for small mutation waves.

---

## 8. Open questions and trade-offs

1. **Where `.drive/` lives.** This report assumes `.drive/` at the repo root, gitignored, holding the plan, briefs, and reports. The state-tracking researcher may prefer a different location or committing STATUS. Recommendation: `.drive/` gitignored for run mechanics; only STATUS and the research ledger are committed, by the integrator, in one commit per wave. Whatever is chosen, the skill must add the gitignore line itself in wave 0 so no stray artifacts reach a commit.

2. **`isolation: worktree` versus orchestrator-managed `git worktree add`.** The harness flag brings enforcement (a maker cannot edit the main checkout) but an implicit base branch and an unspecified path and branch name. Explicit git brings a known base and names and no enforcement. Recommendation: orchestrator-managed for the merge lane (determinism wins because the integrator needs the path and branch), the harness flag for tournament arms where enforcement matters and the branch is discarded anyway; in both cases set `worktree.baseRef: "head"` so nothing depends on the remote.

3. **Should makers commit in the shared tree to protect against crashes?** No, because a maker's `git add` can sweep a sibling's partial edits (documented three times in the owner's memory). The cost is that a mid-wave crash loses uncommitted maker work. Mitigation: the integrator commits each package as soon as its report arrives rather than waiting for the whole wave, when packages are independent enough that gates can be run per package (usually true for type checks and the package's own tests; the full suite still runs once per wave).

4. **Workflow versus Agent tool for mutation waves.** Workflow keeps results out of the orchestrator's context and codifies the orchestration; Agent-tool fan-out avoids the replay hazard and allows `SendMessage` follow-ups. Recommendation: Agent tool for waves of eight or fewer makers, Workflow above that and for every read-only swarm, and idempotent briefs always so the choice can change mid-run.

5. **iOS parallelism depends on modularization.** If a greenfield app is not split into SwiftPM feature packages in wave 0, the iOS side runs sequentially. This is a design-phase requirement that this component imposes on the architecture component; the coordinator should carry it across.

6. **Package size heuristics are opinions.** Ten files, 1,500 lines, one milestone test, 120 turns are drawn from the owner's fleets and his "one solid test per milestone" rule, not measured. The skill should record actual turns and tokens per package in `packages.json` so the heuristics can be tuned from evidence over a few runs; that is the compounding loop applied to this component.

7. **Agent teams.** Rejected for now as experimental, unavailable under `-p`, and unisolated. Worth revisiting if they become stable and gain worktree isolation; the "competing hypotheses debate" use case is attractive for bug hunts.

---

## 9. Skill text candidates

**Default substrate.**
> Run parallel makers in the one shared checkout with disjoint file ownership. Do not create worktrees or branches for parallel work unless a package must edit files that other packages also need, or unless it is one arm of an experiment whose losers will be discarded. When you do create one, merging it into main, running the full gates, removing the worktree, and deleting the branch are one step; the wave is not finished until `git worktree list` shows only the main checkout and `git branch --list 'pkg/*'` is empty.

**Decompose before you fan out.**
> Turn the design into packages before spawning anything. Each package owns a disjoint set of paths, names one behavioral claim a test can refute, lists the merged files it may rely on, names the files it may not touch, and fits one agent: at most about ten files, one milestone test, one to two hours. Give every file that several packages would want (entry points, manifests, lockfiles, generated code, changelog, STATUS) to the integrator, never to a maker. Run the disjointness check and fix overlaps by splitting or merging packages, not by hoping.

**Waves.**
> Order packages by dependency and cut waves so that every package in a wave depends only on packages already merged. Wave 0 is whatever everything depends on (skeleton, contracts, design tokens, test harness, schema) and runs sequentially in your own loop. Never parallelize a client and the endpoint it calls in the same wave without a contract package they both build against.

**Choosing the execution mode.**
> One package, a bug, or dependent packages: do it yourself and spawn one verifier. Two to eight disjoint packages: one background Agent call per package with a structured report. More than eight, or a per-item pipeline over many similar items, or any read-only swarm: write a Workflow. Invoking /drive is the user's standing instruction to use the Workflow tool for these phases; in unattended runs make sure `Workflow` is in the allow rules. Do not use agent teams or /batch: the first is experimental and unisolated, the second opens pull requests.

**Rules every maker receives.**
> Edit only your owned paths and confirm it with `git status --porcelain` before you report. Never run git add, commit, stash, checkout, rebase, or a repo-wide formatter; the integrator owns git. Run only your own test command; the tree is shared and whole-workspace runs are noise. Install nothing; list dependencies in deps_requested. Put edits you need in files you do not own into wiring_needed as exact lines. If your work is already present when you start, verify and report instead of redoing it. Your final message is only the JSON report.

**Reports, not transcripts.**
> Workers return a structured report with capped fields: status, files, tests, gates_run with exact commands, wiring_needed, deps_requested, honest_gaps, and a summary of at most 1,500 characters. Never ask a worker to show a diff or paste a log. Workers write their full report to `.drive/packages/<id>/report.json`; you keep the status line and the path. Your own context is the one resource that cannot be re-spawned.

**Integration is one step.**
> When a wave's makers have reported, work alone in the tree: apply wiring one package at a time, install requested dependencies once, run the full gates including at least one check against the real system rather than a shim, and commit per package staging only the paths in its report. Never `git add -A`. Then run the orphan audit. Only then spawn the wave verifier. Verifying an uncommitted tree produces a verdict about a state that can change under it.

**The worktree lane, when you must.**
> Create the worktree from HEAD yourself: `git worktree add -b pkg/<id> .claude/worktrees/pkg-<id> HEAD`, with `.claude/worktrees/` in .gitignore. The maker commits inside it with explicit paths and reports the branch and sha. You integrate: rebase the package branch onto main inside the worktree, `git merge --ff-only`, full gates on main, `git worktree remove` and `git branch -d` in the same command. If gates go red, `git reset --keep` to the pre-merge sha and hand the package to a fixer. If a conflict is deeper than an import block, that is a decomposition error: abort, drop the worktree, re-scope.

**Why the harness will not save you.**
> A subagent worktree is removed automatically only when the subagent made no changes. A worktree with changes stays on disk for thirty days, and the sweep deliberately keeps any worktree with unpushed commits, which is exactly the state of a finished, unmerged package. Nothing merges it back. If you spawn a worktree, you own its merge and its removal.

**Verifier per package.**
> After a package is merged, spawn a verifier with fresh context that sees the brief and the commit range and nothing of the maker's reasoning. It lists changed files and flags any outside ownership as a high-severity finding. It runs the package's tests and writes one refutation of its own aimed at the claim's weakest point. It checks that every wiring item landed. It asks of every new fake where it is kinder than production. Its default verdict is FAIL.

**Wave and final verification.**
> After every wave, one verifier checks the seams between packages and re-runs the full gates itself. At the end of the run, a fresh Fable auditor takes the original spec and every conclusion-shaped claim in the status file and asks two questions: did the spec ask for this, and can I falsify it in one command. "Blocked" and "impossible" get the same evidence bar as "works". Working-tree code and tests outrank proof artifacts, which outrank STATUS, which outranks prose.

**Sizing.**
> Keep makers in a wave to eight or fewer in the shared tree. Read-only swarms may go to the concurrency cap (sixteen in a Workflow). Split a large run into several workflows, one per wave or phase, and read each result before writing the next. Stay under the twenty-five-agent, 1.5-million-token warning per workflow unless the scope is a greenfield app or a migration, and say so in the plan.

**When a package fails.**
> Partial: resume the same agent once with the exact remaining items. Partial again: re-scope; a third attempt with the same brief is forbidden. Blocked: classify as dependency, contract ambiguity, or environment; fix the first two yourself and record the third honestly with the exact command a human would need. Failed twice on one model: escalate one tier with a fresh context and a brief that says what was tried. Poisoned: revert its owned paths, mark it failed, move its dependents to a later wave, and let its siblings integrate. A package never blocks its wave.

**Experiments.**
> Run parallel alternatives only for design decisions reading cannot settle, performance approaches with a benchmark, or competing hypotheses for a deep bug. Give every arm the same acceptance tests and a distinct approach constraint, run arms in worktrees, judge with fresh context against a rubric and the numbers, merge the winner through the lane, remove the losers in the same step, and record one paragraph per loser in the research ledger.

**Refuse these.**
> Two packages owning one file. A swarm for a one-file bug. Makers running whole-workspace tests while siblings edit. Concurrent builds against a shared toolchain lock. Merging without full gates. Diffs or logs in your own context. Worktrees or branches alive at the end of a wave. Pull requests as an integration mechanism. A boundary report's scope items flowing into the next brief unchecked.
