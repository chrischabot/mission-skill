# drive

`/drive` is a Claude Code skill that takes one high-level goal and drives it to finished,
verified work without anyone watching. It classifies the work, researches what it does not know,
writes a specification whose requirements are claims a test could refute, designs, plans tests,
builds in parallel waves, verifies with independent agents that never see the maker's reasoning,
checks rendered UI with vision, records everything in files inside the target repository, and
turns failures into lessons that make the next run better. It scales down: a one-line fix gets a
refutation test and a commit, not a process.

```
/drive find the intermittent 500 on checkout and fix it
/drive add a usage dashboard to the admin area of this product
/drive move our AI gateway from the external repo into a core service of this platform
/drive research our market position and build a site with blog and docs sections
/drive build a native iOS app with a serverless backend from this brief: ...
/drive --resume
```

The skill loads as a plugin, so its full command is `/drive:drive`. The short `/drive` invokes it
too unless another command already uses that name; use `/drive:drive` when it does, and in scripts.

## How it works

The orchestrator is the main conversation, designed for Fable 5.1 at high effort. At intake it
answers three questions separately. The **shape** (build, feature, fix, move, publish, report,
operate) fixes the order of phases. The **traits** (UI, API, auth, data, existing code, async
systems, and a dozen more) attach gates such as an Opus security review or a design contract. The
**size** (XS to XL) sets how much ceremony pays for itself.

Run state lives in `.drive/` in the repository that will hold the deliverable and is committed with
the code: the goal and plan, a small working-memory file, a status ladder of behavioural claims with
typed evidence, decisions with their undo, and proof bundles. A claim moves up the ladder (Missing,
Scaffold, Partial, Local Proof, Live Proof, Operational, Done) only on a verifier's verdict, and
local-only work is never Live Proof. Drive's hooks record, in a ledger outside `.drive/`, which
reviewing agent wrote each verdict and final audit, and an entry counts only when that agent's own
transcript shows the tool call that wrote the file, so a verdict the orchestrator writes itself does
not count at the lint. The plugin's Stop hook keeps the run's own sessions working while STATE.md
says the run is unfinished, and lets a turn end only on the conditions
`skill/references/long-running.md` section 5 lists. The run commits on the current branch. The guard
refuses `git push` from any directory, and any command that creates or moves a branch or tag in a
worktree that shares the repository's refs, and `drive.py lint --stop` fails on any worktree, branch,
or uncommitted path the run created; the owner's own, recorded when the run started, are left alone.

These mechanisms have limits worth knowing before you trust an unattended result. Drive's hooks run
as the same user, in the same shell, as the session they watch, so no command filter can prevent
deliberate tampering. The guard exists so that honest mistakes and shortcuts, such as a hand-written
verdict, a push, a new branch, or an edit to a frozen test, fail loudly when they happen; it does not
refuse every possible write, and a command written to hide what it touches can get past it.
Provenance exists so that tampering is evident afterwards: evidence counts only when a reviewing
subagent's own Claude Code transcript shows the write, and frozen tests are checked against their
recorded hashes. Neither makes forgery impossible.

Provenance also depends on those transcripts surviving. Claude Code deletes them after
`cleanupPeriodDays`, 30 days by default, and from then on the verdicts, audits, and live proofs they
backed stop counting at the lint. For a run that may last longer, raise `cleanupPeriodDays` in
`~/.claude/settings.json` before you launch it, since a value passed in the run's own `--settings`
covers only that session and the run never edits settings files; otherwise the run re-runs every
review whose transcript the lint reports missing before it can finish.

The Stop hook checks what the state files say rather than whether it is true, lets a turn end when
the hook itself errors, and is overridden by Claude Code after 30 consecutive blocks in the launch
recipes. It is registered by the plugin in every session but holds only the sessions the run's marker
records, so a fresh session is held once its `/drive --resume` records it. The evidence files and the
final audit are what to read; the lint and the ledger make a shortcut visible rather than impossible.

Some endings are expected rather than failures. A claim that only a physical device can prove never
reaches Done, so a native iOS run with device-only rows ends `stopped`, honestly, with those rows at
the rung the simulator supports and the device step named for you. Nothing enforces a dollar cap in a
background session: the budget line's subagent count limits maker spawns, and the dollar envelope is
an estimate that only a headless run's `--max-budget-usd` enforces. A run that waits out a soak
resumes itself only through a scheduler that can start a Claude session; on a machine with an
API-key login and no Desktop app, where a CI job is the only scheduler, the soak check still acts, and
you resume the run by hand with `/drive --resume` once the window ends.

Twelve subagents do the work, each with its model, effort, tools, and preloaded skills pinned in
`skill/agents/`. Drive uses exactly three models, pinned by full ID: `claude-fable-5-1` (Fable 5.1)
for the orchestrator and the auditor, which runs final audits and disputes; `claude-opus-5` (Opus 5)
for the architect, designer, writer, verifier, severe tester, security reviewer, UI reviewer, and
investigator, where judgment or prose quality is worth the premium; and `claude-sonnet-5` (Sonnet 5)
for the researcher, implementer, and grader, the grader at low effort for checklists.
Haiku and older models are never selected.
A classifier refusal is logged and reported, never retried on another model.

## Install

```bash
./install.sh
```

The script links `skill/` to `~/.claude/skills/drive`, which Claude Code loads as the
skills-directory plugin `drive@skills-dir`, validates the plugin, runs the tooling tests, and prints
the per-run settings a long run passes on its command line. Enabling the plugin records its enabled
state under `enabledPlugins` in your user settings, as `claude plugin enable` does; the script edits
no other setting.
`./uninstall.sh` removes the link.

Requirements: Claude Code 2.1.260 or later (2.1.269 or later to run the evals with
`claude plugin eval`), Python 3, and git. `jq` is used only by the eval commands. Platform work uses
whatever the project needs (Xcode and the simulator, wrangler, Node, Playwright); the skill detects
what is installed and lowers the proof ceiling of claims it cannot verify rather than pretending.

## Launching a long run

```bash
claude --bg --name drive-<slug> --model claude-fable-5-1 --effort high --permission-mode auto \
  --settings "$DRIVE_SETTINGS" "/drive <goal>"
```

`install.sh` prints `DRIVE_SETTINGS`, the per-run settings JSON: the Stop hook block cap of 30, the
ten-minute Bash timeout, the retry watchdog, the Workflow allow rule, `worktree.bgIsolation` set to
`none`, the one-hour prompt cache for the main conversation, and the skill repository under
`additionalDirectories` so lesson commits can write there. The
settings travel with each run and no settings file is edited; the old `--apply-settings` option, which
changed every Claude session on the machine, was removed and `install.sh` now refuses it.

`--permission-mode auto` keeps a session nobody watches from stopping at its first permission
prompt. `worktree.bgIsolation` set to `none` keeps the background session in your checkout; without
it, Claude Code moves every background session into its own worktree, and at the end commits there
and pushes the branch when the repository has a remote. The run checks both with `drive.py preflight`
right after `drive.py init`, once drive's hooks have recorded the session's permission mode, and when
either did not take effect it stops with the relaunch command for you to run. A headless run
(`claude -p`) adds `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=10800000`, a three-hour ceiling on waiting for
background agents; `0` would wait forever.
`skill/references/long-running.md` has the full per-run settings (the environment, and the skill
repository plus any other repository the run writes to under `additionalDirectories`), the headless
recipe with its spend envelope across legs, keep-awake, resume by session id, and when a cloud
hand-off is possible.

## Repository layout

| Path | What it is |
|---|---|
| `skill/SKILL.md` | the spine the orchestrator follows |
| `skill/agents/` | the subagent roster |
| `skill/references/` | procedures read on demand: intake, shapes, spec, design, research, testing, verification, UI, parallel work, state files, lessons, long runs, models, safety, security, observability, capabilities, definition of done, and domain packs for iOS, Cloudflare, and the web |
| `skill/references/lessons/` | lessons the skill has learned; one commit per lesson, undo with `git revert` |
| `skill/templates/` | every file a run writes into a project |
| `skill/scripts/drive.py` | the state tool: init with the hygiene baseline, launch preflight, repository visibility, capabilities, start view, lint, end, the Stop, re-injection, guard, commit-record, and snapshot hooks with the provenance ledger, the floor guard, frozen tests, worktree landing, lesson checks and commits, and selfcheck |
| `skill/hooks/hooks.json` | plugin hooks: the Stop gate, state re-injection after compaction or resume, per-agent write and git guards, records of the main thread's commits and of files changed while a reviewer runs, transcript-backed provenance for evidence reviewers write, and voiding of a review when a tracked file changed under it with no recorded edit or HEAD was rewritten |
| `skill/evals/` | behavioural eval cases for `claude plugin eval`; first scored on 2026-09-15; `skill/evals/README.md` section 2 says how to run it on a machine whose `~/.docker` holds symbolic links |
| `research/` | the research reports and the synthesis the skill was built from |
| `HANDOFF.md` | current state of the work, for whoever picks it up next |

## Credits

Built from a reading of a public post on self-improving agent systems, checked claim by claim
against Anthropic's documentation (see `research/22-source-verification.md`), and from material
adapted from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) under the MIT
license (see `THIRD_PARTY_NOTICES.md`).
