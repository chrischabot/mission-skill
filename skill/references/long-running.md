# Long-running runs

Read this file at intake for any run of size M or larger, when you choose or record how the run
was launched, when `drive.py preflight` fails, when the Stop gate blocks you and you are unsure why,
before you wait on anything, at every resume, and when a soak period begins. It decides where a run
lives, how it is launched (including in another repository or a new one), what is checked before
work starts, how the run stays awake and keeps going, how it waits, how it resumes, how context and
commits carry it across hours or days, and when a schedule or the cloud is allowed.

## Contents

1. Where a run lives
2. Launch recipes
3. Pre-flight checklist
4. Keep-awake
5. The Stop gate, as you experience it
6. Optional `/goal`
7. Waiting well
8. Resume protocol
9. Context across a long run
10. Checkpointing with commits
11. The soak rule
12. Cloud hand-off
13. Worked timeline: a greenfield app with a backend and a native client

In the commands below, `SKILL_DIR` is the absolute skill directory SKILL.md names (after
`install.sh` that is `~/.claude/skills/drive`; a plugin install lives under its plugin root), and
`DRIVE` means `python3 "$SKILL_DIR/scripts/drive.py"`. `PROJECTS` is the directory new repositories
are created in: `DRIVE_PROJECTS_ROOT` when set, otherwise the directory that holds the repository the
session started in, or the starting directory itself when it is not a repository; set
`DRIVE_PROJECTS_ROOT` in the launch environment when projects live elsewhere. `/drive` is the skill's
short name; its full plugin name, `/drive:drive`, always works, and is the one to use when another
command already answers to `/drive`.

## 1. Where a run lives

Runs are local. A run is kept alive by files, a deterministic Stop gate, and commits, not by one
long conversation.

A run lives in the repository that will hold the deliverable, and its session starts there,
because the Stop gate, the guards, and every subagent's shell start in the session's directory. A
repository the goal names after "from" is a source, never the home. The hooks resolve the run from
the `cwd` field of their input: that directory's repository, then its main checkout when the
directory is a linked worktree, and `CLAUDE_PROJECT_DIR` only when `cwd` is under a scratch directory
or outside every repository; the first that holds `.drive/local/active` is the run. A `cwd` inside
another repository never falls back, so a stale marker in the session's project does not gate work
there. Only `drive.py init` records a session in the marker, for a new run and at every resume.
The Stop gate and the SessionStart re-injection act only in a session the marker records (in any
session while it records none), so another session in the same repository, such as an XS fix, is
neither held nor told it is running `/drive`. The guard and the provenance hooks act in every session
while the marker exists.

When the home is another existing repository, or the goal is new work while this directory holds a
different project or no repository, do not start the run here: launch it in the right repository
with the recipe "In another repository, or a new one" in section 2, end the turn with one line
naming the session, and stop (`references/rigorous.md` section 2, step 0).

| Situation | Host | Notes |
|---|---|---|
| Default, any shape | Local background session under the Claude Code supervisor | Survives closing the terminal, auto-updates, and sleep (it pauses and resumes on wake). Stops on shutdown. Needs `worktree.bgIsolation` set to `none` and an unattended permission mode (section 2). |
| The owner typed `/drive` in a terminal | That session, optionally moved to the background with `/bg` | `/bg` starts a fresh process that carries background subagents, workflows, and `/loop` tasks; running monitors stop. Run `$DRIVE preflight` in the first turn after the move. |
| Scripted run with no terminal | Headless `claude -p` | No iOS Simulator MCP and no Browser pane: verify native clients with `xcodebuild test` and `xcrun simctl io <udid> screenshot`, web with Playwright. |
| Must outlive a shutdown, and the account allows it | Cloud session | Section 12; unavailable with an API-key login. |

A closed laptop lid sleeps the machine, and a sleeping machine runs nothing. Say so in STATE.md.

## 2. Launch recipes

The recipes below launch a rigorous run at `--effort high`. A lean run, the default, uses the same
commands with `--effort medium` and a goal without `--rigorous`; its budget target comes from the
lean envelopes in `references/models.md`, and its `stop:` line from the owner's goal, otherwise
`none`.

The owner runs these from the repository root, and the orchestrator runs the background recipe
itself when it launches a run elsewhere. They set the model, effort, and permission mode for the
whole run and pass the run's settings on the command line, so the owner's settings files are never
edited.

Two settings are not optional for a background session, and both were checked against the Claude
Code documentation on 2026-09-14:

- **`"worktree": {"bgIsolation": "none"}`.** By default every background session, whether started
  by `claude --bg`, `/bg`, or agent view, moves into its own worktree under `.claude/worktrees/`
  before it edits anything, its subagents edit there too, and at the end Claude commits without
  asking and pushes the branch when the repository has a remote. That breaks the single shared
  checkout, the no-branch rule, and every hygiene check. The setting is allowed in any settings
  file, and with `none` background jobs edit the working copy directly.
- **`--permission-mode auto`.** A session nobody watches must not stop at a prompt, and background
  subagents surface every permission prompt in the main session. The flag overrides `defaultMode`
  from settings files. When auto mode is unavailable to the account or model, Claude Code starts the
  session in Manual instead, which `drive.py preflight` reports (section 3).

| Variable | Value | Why |
|---|---|---|
| `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` | `30` | The default of 8 consecutive Stop blocks can end a legitimate run early; the gate's own stall detection ends a stuck one at 6 unchanged blocks. |
| `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` | `10800000` (headless only) | The default abandons background subagents and workflows after 10 idle minutes. Three hours covers a long verifier or suite; never `0`, which waits without limit and lets a stuck agent hold the process open past `--max-turns` and `--max-budget-usd`, since neither fires while nothing spends. |
| `BASH_DEFAULT_TIMEOUT_MS` | `600000` | Long builds, test suites, and deploys otherwise hit the 2-minute default. |
| `CLAUDE_CODE_RETRY_WATCHDOG` | `1` | Retries 429 and 529 capacity errors indefinitely; a spend-limit 429 still fails at once. |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | `claude-sonnet-5` | Only when `/goal` is used: moves its evaluator and background summaries off Haiku for this process. |

A background session receives the dispatching shell's `PATH` and `ANTHROPIC_DEFAULT_*_MODEL`
variables but is not documented to receive other exported variables, so every launch passes the
environment through `--settings`, which the session carries when it is backgrounded or restarted.
The same JSON allows the Workflow tool and lists under `additionalDirectories` the skill repository
(where `drive.py lesson-commit` writes) and every other repository the run writes to, which is every
repository in the ownership map and GOAL.md's `probe.repos`, and sets `"promptCacheTtl": "1h"`, the
one-hour prompt cache for the main conversation that the cost envelopes assume (`models.md` section 8).

```bash
SKILL_DIR=<absolute skill directory>
SKILL_REPO=$(git -C "$SKILL_DIR" rev-parse --show-toplevel 2>/dev/null)
DRIVE_SETTINGS=$(python3 -c 'import json, sys
dirs = [d for d in sys.argv[1:] if d]
print(json.dumps({"worktree": {"bgIsolation": "none"},
                  "env": {"CLAUDE_CODE_STOP_HOOK_BLOCK_CAP": "30", "BASH_DEFAULT_TIMEOUT_MS": "600000",
                          "CLAUDE_CODE_RETRY_WATCHDOG": "1"},
                  "permissions": {"allow": ["Workflow"], "additionalDirectories": dirs},
                  "promptCacheTtl": "1h"}))' \
  "$SKILL_REPO" <each other repository the run writes to, as absolute paths>)
```

`git rev-parse --show-toplevel` resolves a symlinked skill directory to the real checkout, which is
the path lesson commits must use. When the skill directory is not inside a git checkout,
`SKILL_REPO` is empty and no run can commit lessons; record that under "Verified facts". Shell
variables do not survive between Bash tool calls, so when you launch a run yourself, build
`DRIVE_SETTINGS` and launch in the same command.

**Background (the default).**

```bash
claude --bg --name drive-<slug> --model claude-fable-5-1 --effort high --permission-mode auto \
  --settings "$DRIVE_SETTINGS" "/drive <goal>"
claude agents                 # state of every background session
claude logs <id>              # recent output; claude attach <id> to watch
```

`claude --bg` prints the new session's id. The session records it in STATE.md's `session:` field at
intake, from `.drive/local/session.json`, which drive's hooks write.

**In another repository, or a new one.** Run from the session that received the goal, as one Bash
command. Pass the goal verbatim inside single quotes, writing each `'` in it as `'\''`.

```bash
cd <absolute repository path> && \
SKILL_DIR=<absolute skill directory> && \
SKILL_REPO=$(git -C "$SKILL_DIR" rev-parse --show-toplevel 2>/dev/null) && \
DRIVE_SETTINGS=$(python3 -c '<the settings program above>' "$SKILL_REPO" <other repositories>) && \
claude --bg --name drive-<slug> --model claude-fable-5-1 --effort high --permission-mode auto \
  --settings "$DRIVE_SETTINGS" '/drive <goal verbatim>'
```

For new work (`build`, or `publish` of a new site) while this directory holds a different project or
no repository, create the repository under `PROJECTS` first, then launch there with the command
above. Refuse when the directory exists and is not empty.

```bash
dir="${DRIVE_PROJECTS_ROOT:-$(if git rev-parse --git-dir >/dev/null 2>&1; then dirname "$(git rev-parse --show-toplevel)"; else pwd; fi)}/<slug>"
if [ -e "$dir" ] && [ -n "$(ls -A "$dir")" ]; then echo "refusing: $dir exists and is not empty"; exit 1; fi
mkdir -p "$dir" && cd "$dir" && git init -b main && \
git commit --allow-empty -m "drive(launch): repository for <slug>; undo: rm -rf $dir"
```

End the turn with one line: the session name, the repository path, and `claude agents` as the way
to follow it. The new session runs intake itself; this session writes no `.drive/` anywhere.

**Interactive, then background.**

```bash
claude --name drive-<slug> --model claude-fable-5-1 --effort high --permission-mode auto --settings "$DRIVE_SETTINGS"
# type: /drive <goal>
# after intake has written STATE.md, optionally type: /bg
```

**Headless.** The `--settings` JSON carries the Workflow allow rule, the isolation setting, and the
additional directories, the same as the other recipes. Record the session id in STATE.md `session:`.

```bash
SID=$(uuidgen | tr 'A-Z' 'a-z'); mkdir -p .drive/local/logs
env CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=30 CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=10800000 \
    BASH_DEFAULT_TIMEOUT_MS=600000 CLAUDE_CODE_RETRY_WATCHDOG=1 \
  claude -p "/drive <goal>" --session-id "$SID" --model claude-fable-5-1 --effort high \
    --settings "$DRIVE_SETTINGS" --permission-mode auto --permission-prompts none \
    --output-format stream-json --verbose --max-turns <n> --max-budget-usd <usd> \
    >> .drive/local/logs/stream.jsonl 2>&1
```

For a run expected to last more than a day, run headless in legs so each leg is a fresh session
reading state from files. `--max-budget-usd` caps one leg only, and a leg that ends on it is not a
stopped run: the loop keeps going for as long as STATE.md says the run is unfinished. Before each
leg it adds up `total_cost_usd` from every result event in the log and writes the sum to
`.drive/local/run.md` as `spent $<n>`, which `drive.py` reads as the recorded spend, so the next
leg's resume does the checkpoint when the sum has passed the budget target, and the loop stops only
when the sum has reached a dollar figure on the owner's `stop:` line. The first leg is the command
above; each later leg replaces the prompt with `/drive --resume` and drops `--session-id`.

```bash
LEG_CAP=<one leg's --max-budget-usd, sized to about a day of work>
STOP=<the dollar figure on GOAL.md's stop: line, or empty when it names none>
for leg in $(seq 1 <max legs>); do
  grep -Eq '^status: (running|verifying)$' .drive/STATE.md || break
  spent=$(python3 - <<'PY'
import json
total = 0.0
try:
    for line in open('.drive/local/logs/stream.jsonl', encoding='utf-8', errors='replace'):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get('type') == 'result':
            total += float(event.get('total_cost_usd') or 0)
except OSError:
    pass
print(f'{total:.2f}')
PY
)
  echo "$(date -u +%FT%TZ) leg $leg: spent \$$spent so far" >> .drive/local/run.md
  if [ -n "$STOP" ]; then
    python3 -c "import sys; sys.exit(0 if $spent < $STOP else 1)" || { echo "the owner's stop line (\$$STOP) is reached; no further legs" >> .drive/local/run.md; break; }
  fi
  env <the same variables> claude -p "/drive --resume" <the same flags, with --max-budget-usd "$LEG_CAP" and --max-turns sized to about a day of work> \
    >> .drive/local/logs/stream.jsonl 2>&1
done
```

When the loop stops on the owner's stop line, the next resume writes the report, sets
`status: stopped`, and runs `drive.py end`. A loop that ends because `<max legs>` ran out has not
stopped the run either: start it again, and it resumes from the repository.

**Resume.** Continue the same conversation by its id, never its name:
`claude --resume <session id> --bg --model claude-fable-5-1 --effort high --permission-mode auto --settings "$DRIVE_SETTINGS" "/drive --resume"`.
With `--bg`, a name, a transcript path, `--continue`, or a bare `--resume` always starts a copy under
a new id; an id continues in place on Claude Code 2.1.257 or later, or starts a copy and prints a
`note:` line saying why. When a copy starts, write its id into STATE.md `session:`. Start a fresh
session from files with
`claude --bg --name drive-<slug>-<n> --model claude-fable-5-1 --effort high --permission-mode auto --settings "$DRIVE_SETTINGS" "/drive --resume"`.
Always re-invoke `/drive --resume`, whose resume step runs `drive.py init --goal -` and so records the new
session, which the Stop gate holds only once recorded, and always pass `--model claude-fable-5-1`, which
also returns an orchestrator that a classifier fallback moved to another model. Put the exact resume command
for this run on the "Resume here" block of STATE.md.

## 3. Pre-flight checklist

Run these at intake, after `drive.py init`, and at every resume. Record each result as one line
under "Verified facts" in STATE.md, ending with `Verified: <command>, <date>`.

Start with `$DRIVE preflight`, which exits 1 when any line says `FAIL` (`--json` prints the same
checks as JSON). Run it after `init`, because the permission mode it judges is the one drive's hooks
record in `.drive/local/session.json`, and they record nothing until the run is active.

Every relaunch below follows one order, so that the Stop gate lets this turn end and the new session
knows why the run paused: set STATE.md `status: blocked` with
``Blocked on: launch preflight: <what failed>; relaunched as `<the exact claude command>` ``, which the
Stop gate accepts only because `$DRIVE preflight` recorded that failure for this session, run
that command, end the turn with one line naming the new session, and do no more work here. With
`status: running` the gate would keep this session working in the same checkout as the new one. The
new session's resume (section 8, step 1) sets `running` again once its own preflight passes.

| Its line | FAIL or warn when | What to do |
|---|---|---|
| worktree isolation | this session runs inside `.claude/worktrees/`, or `git worktree list` gained a `.claude/worktrees/` entry since `init` recorded the baseline | Relaunch, in the order above, with `worktree.bgIsolation` set to `none`: resume by session id or start a fresh session from files (section 2). Land nothing from the harness worktree by hand; the fresh session's resume protocol reconciles it. |
| permission mode | the mode passed as `--permission-mode <mode>`, or else the mode the hooks recorded for this session, is `default` (Manual), `manual`, or `plan`, or, as a warning, `acceptEdits`; with neither, an `info` line says the mode is not detectable | In an interactive session the owner is present, so record the warning and continue. In a background or headless session, relaunch once, in the order above, with `--permission-mode auto`. If the relaunched session still reports Manual, auto mode is unavailable to this account or model: record a Boundary event, set `status: blocked` with a Blocked on line that begins `launch preflight:`, quotes the launch command, and lists the allow rules the owner would add, and end the turn with that one line. |
| `worktree.bgIsolation` | informational: the value in the settings files it can read | The per-run `--settings` JSON carries `none`; the isolation line above is the check that it took effect. |
| provider | warn when `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, or `CLAUDE_CODE_USE_FOUNDRY` is set to a true value (`warn provider: bedrock`, `vertex`, or `foundry`); otherwise `ok provider: anthropic`. A warning does not fail preflight, and `drive.py capabilities` records the same value as `env:provider` | Record it under Verified facts. Off the Anthropic API, pass no `model` override on any Agent call, because the aliases resolve to other models there (`models.md` section 1), and name the provider once in the report. |
| skill repository | the skill directory is not in a git checkout or its lessons directory is not writable | Record that lessons cannot be committed from this session; keep candidate lessons in `.drive/LESSONS.md` with the routing they need, and relaunch with the directory under `additionalDirectories` at the next resume. |

Then the checks preflight does not cover:

| Check | Command | When it fails |
|---|---|---|
| Claude Code version | `claude --version` (2.1.259 or later for `--permission-prompts`; 2.1.257 for Fable 5.1 and resume in place by id) | Say so in one line; use the background recipe instead of headless. |
| Serving model and effort | the model named in your system prompt; the effort passed at launch | Record in STATE.md `model:`. If it is not Fable, say so in one line and continue. |
| Tools | `python3 --version && git --version` | Nothing can run; record the missing tool under "Blocked on" and end the turn. |
| Tree | `git status --porcelain`, `git worktree list`, `git branch --list`, compared with `.drive/local/baseline.json` | Only entries the baseline does not list are the run's to reconcile (section 8, step 2). The owner's are never touched. |
| Run marker | `test -f .drive/local/active && git check-ignore -q .drive/local/active` | At intake, `$DRIVE init` creates it. On resume, `$DRIVE start` only reads: run `$DRIVE init --goal -` with the goal quoted in GOAL.md on stdin, which for the same goal re-creates a missing marker, records this session, and archives nothing. |
| Transcript retention | `cleanupPeriodDays` in `~/.claude/settings.json` (30 days when unset) | Evidence counts only while its reviewer's transcript exists. When the run's wall clock or a soak may outlast the period, put raising it in the user settings under "Needed from you" now (a value in the run's `--settings` covers only that session), and before `lint --final` re-run each review whose transcript the lint reports missing. |
| Other repositories | every path under GOAL.md's `probe.repos` appears in the launch settings' `additionalDirectories` | Before the first write to another repository, relaunch with them, in the relaunch order above. |
| Environment | `env \| grep -E 'CLAUDE_CODE_STOP_HOOK_BLOCK_CAP\|BASH_DEFAULT_TIMEOUT_MS\|CLAUDE_CODE_RETRY_WATCHDOG\|CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS'` | Record which are missing and what that risks; continue. A ceiling of `0` is a finding: relaunch the next leg with the finite value. |
| Keep-awake | section 4 | Start it. |
| Permissions | a Workflow allow rule exists; the test, build, and deploy commands run without a prompt | Headless denies anything that would prompt; add the rules to the launch `--settings` and relaunch. |
| Billing and cache | `[ -n "$ANTHROPIC_API_KEY" ]`, or `apiKeyHelper` or `"forceLoginMethod": "console"` in `~/.claude/settings.json` | With an API key and no one-hour cache, record the cost risk (`models.md`). |
| Capabilities | `$DRIVE capabilities`, then the ToolSearch probe and merge in `capabilities.md` section 1 | A rerun rewrites the file and keeps only `git:baseline_sha`, so every resume merges the `mcp:` and `resolved:` keys again. A missing verification capability lowers the ceiling of the claims it would verify. |
| Cloud availability | the billing check above | With an API key, record "Cloud hand-off unavailable with API-key login; the run stays local." |
| Budget | GOAL.md `budget:` line, including a subagent count, and its `stop:` line | Fill the target from the envelopes in `models.md`; the stop line holds what the owner's goal names, otherwise `none`. |
| Classifier exposure | security or biology material in the repository | Apply `safety.md` before the first review or test phase. |

## 4. Keep-awake

On macOS, if `pmset -g` shows no sleep assertion, start one detached from the harness and record it:

```bash
if command -v pmset >/dev/null && ! pmset -g | grep -qi 'sleep prevented'; then
  nohup caffeinate -is -t 43200 >/dev/null 2>&1 &
  echo "caffeinate pid $! until $(python3 -c 'import datetime as d; print((d.datetime.now(d.timezone.utc) + d.timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ"))')"
fi
```

On Linux with systemd, the equivalent is
`nohup systemd-inhibit --what=idle:sleep --why=drive sleep 43200 >/dev/null 2>&1 &`. Elsewhere,
record that nothing keeps the machine awake.

Run this as a plain Bash call, detached with `nohup`. Never start it with `run_in_background` or as
a Monitor: a harness task dies with its session, and the Stop gate never counts `caffeinate` as work
in flight, so it would neither keep the machine awake nor let a turn end. `-i` prevents idle sleep
and `-s` prevents system sleep on mains power only. Write the pid and expiry under "Verified facts",
together with the sentence "A closed lid or battery power still sleeps the machine, which pauses the
run." Re-arm at every resume and when the expiry is less than an hour away.

## 5. The Stop gate, as you experience it

The plugin's `hooks/hooks.json` registers `drive.py hook-stop` as a Stop hook for every session while
the plugin is enabled. It makes no model call, runs no build, test,
or registry command (a hook that outlives its timeout decides nothing), and every decision it takes
goes to `.drive/local/gate.log`. No status line opens it by being declared.

| Situation when you try to end a turn | Gate decision |
|---|---|
| No `.drive/local/active` (XS runs, sessions with no run) | Allows at once. When `.drive/STATE.md` (searched from the hook's `cwd` up to the git top level) still says `running` or `verifying`, it first warns, once per session, as a system message and on stderr, that the marker is missing, because every hook is off without it; the sessions it warned are recorded in `.drive/local/lost-marker-warned.json`. Restore the marker with `$DRIVE init --goal -` as section 8 step 1 describes. |
| The marker records sessions and this is not one of them | Allows at once; the run belongs to another session. |
| A running `drive:` subagent, or a background shell, monitor, or workflow whose task id or whole command appears on STATE.md's "In flight" line | Allows; the completion notification starts your next turn. A description or name on that line does not count. An unrelated subagent (Explore, another plugin's agent), a task from before the run, or a task "In flight" does not name keeps the gate closed, and a `caffeinate`, `sleep`, `yes`, `tail -f`, or `true` task never opens it. |
| STATE.md `status: running` or `verifying` | Blocks, with the recorded `next:` and any `lint --stop` findings as the reason. |
| `status: done` or `stopped` | Allows only if `lint --final` passes, reading the ledger's record of the full-suite run rather than re-running it; otherwise blocks with the findings. Run `$DRIVE lint --final` yourself first so that record exists for the latest code commit. |
| `status: blocked` | Allows only when "Blocked on" begins with one of these tokens followed by the condition in words, and REPORT.md says "Stopped because": `budget:` (the `stop:` line the owner wrote in GOAL.md reached; the budget target itself is a checkpoint and never a stop), `impossible:` (the goal is impossible as stated), `destructive:` (a destructive or irreversible step the goal does not imply, including the one question), `credentials:` (naming the secret as an uppercase identifier containing an underscore or ending in `TOKEN`, `KEY`, `SECRET`, `PASSWORD`, `PAT`, `CREDENTIALS`, or `CERT`, as in `credentials: CLOUDFLARE_API_TOKEN`, or as a name of two or more letters in backquotes or double quotes; `none`, `TBD`, `TODO`, `N/A`, `NA`, and `UNKNOWN` are refused in any form), `payment:`, `legal:` (legal acceptance), `account:` (account creation), `two-diagnoses:` (a failure that survived two distinct diagnoses), or `soak:` (section 11). The one exception is a failed launch preflight: when "Blocked on" begins `launch preflight:` and quotes the relaunch command, a `claude` command in backticks or quotes, the gate allows with no report, but only when the latest `$DRIVE preflight` the ledger records for this session failed. |
| `status: aborted` | Allows only when REPORT.md exists and a DECISIONS.md entry's `Decision:` line begins with `Abort` or `Aborted` followed by `;`, `:`, a comma, a period, or the end of the line, as in `Decision: Abort; <why>`. |
| `status: stalled` | Allows only when the gate itself set it, which the provenance ledger records against those exact STATE.md bytes. |
| `.drive/STATE.md` missing, or a status outside the vocabulary | Blocks. |
| A stop after six consecutive blocks with no progress: STATE.md apart from its `updated:` line, STATUS.md, HEAD, and the working tree all unchanged | Sets `status: stalled`, records the new STATE.md bytes in the ledger, and allows. Commit STATE.md unchanged, together with REPORT.md saying "Stopped because", before `$DRIVE end`, which needs those exact bytes and a clean tree. A stalled run is a failure the report must name. |
| The gate itself raises an error | Allows, with a message telling you to run `$DRIVE lint --stop`; the error goes to `gate.log`. |

Claude Code also ends the turn after `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` consecutive blocks (30 in
the recipes, 8 by default).

The gate reads what the files say, not whether it is true: a Blocked on line, the opening of
REPORT.md, and a DECISIONS.md entry are checked as text. It keeps an honest run from ending early by
mistake, and it cannot stop a run that writes those lines falsely; the final audit and the evidence
behind the report are what catch that. It holds only the sessions the marker records: a session
started fresh from files is held once its `/drive --resume` runs `$DRIVE init --goal -`, and until
then that session can end a turn freely.

To satisfy a block, do the `next:` step with tool calls, then update STATE.md: `next`, `updated`,
`commit`, and whatever the step changed. When the reason names lint findings, fix those first.
Set `blocked` only for a stop condition, only after every independent piece of work is done, and
only with REPORT.md written; put the stop-condition token, then the single thing, who can unblock it,
and the default being taken meanwhile on the "Blocked on" line, and the one question in plain text at the end of your turn. Set
`done` only when every row is Done or Dropped, after the final audit passes and `lint --final` is
green, then run `$DRIVE end`. Set `stopped` when the run ends short of Done for one of `references/rigorous.md`'s
section 9's stop conditions: every piece of work that does not depend on the blocker is finished,
every row below Done carries its reason (an Open failure, the Blocked on line, a `why:` token, or a
DECISIONS.md `Narrows:` line naming it), the retro exists, and REPORT.md opens with "Stopped
because"; then `lint --final` must pass and you run `$DRIVE end`. A soak with nothing else to do is
`blocked`, not `stopped`, because the run continues when the soak check resumes it. Set `aborted`
only when the owner stopped the run or the auditor ruled that the goal cannot be met as written, with
a DECISIONS.md entry whose `Decision:` line begins with `Abort;` or `Aborted;` (or the word followed by other punctuation or the line's end). `$DRIVE end` closes `done` and `stopped` after `lint --final` passes, `aborted`
after `lint --stop` passes with its report and entry, `blocked` under the conditions in the table and
`stalled` once REPORT.md says "Stopped because", each only after the `lint --stop` hygiene checks pass
(commit STATE.md, REPORT.md, and the rest of `.drive/` first, and remove or commit any branch,
worktree, or untracked or dirty path the run created; the gate itself still lets a blocked or stalled
turn end on a dirty tree), recording the last two
as stopped. Ending removes `.drive/local/active`, so drive's hooks go quiet in the repository.

Never change `status` to escape the gate. Never make cosmetic edits to STATE.md to reset stall
detection, never touch `gate.log` or the ledger, never delete `.drive/local/active` by hand (while a run is active the guard refuses deleting, moving, or overwriting it or `.drive/local/baseline.json` through any shell route or edit tool, and `git clean` with `x` or `X` in its flags other than a dry run), and
never start background work only so that a turn may end.

## 6. Optional `/goal`

`/goal` is a second, session-scoped loop. The skill never depends on it: you cannot set it
yourself, its evaluator reads only the transcript and runs no tools, and it defaults to Haiku
unless `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5` is set for the process (a background session
takes that variable from the shell it was dispatched from). Phrase every clause as output that
must appear in the transcript, and always include a bound.

```text
/goal The drive run in this repository is finished, shown by output printed in this session:
1. `python3 <skill dir>/scripts/drive.py lint --final` exits 0 and its output is shown.
2. `sed -n 1,8p .drive/STATE.md` shows "status: done", or "status: stopped" with `head -5 .drive/REPORT.md` showing "Stopped because".
3. The same lint output reports no worktree, branch, or uncommitted path created during the run.
4. For a done run, `grep -H verdict .drive/reviews/*final-audit*` shows a passing final audit.
A claim without printed command output does not count. Or stop after <N> turns; if you stop on
that bound, write why on the "Resume here" block of STATE.md.
```

In a background or interactive run the owner may type it once intake has written STATE.md. In a
headless run it cannot share a prompt with `/drive`, because the skill cannot be invoked by the
model from a goal directive. Set it in its own leg after the drive leg returns with the run still
`running` or `verifying`: `claude -p --resume "$SID" "/goal <condition>" <the headless flags>`. That
leg's turns do not re-invoke `/drive`, so the skill's Stop gate may be absent there; use it only to
finish a small remainder, and prefer a `/drive --resume` leg otherwise. Never let a goal loop
re-run a step that a safety classifier declined.

## 7. Waiting well

In order of preference:

1. **Do not wait; drive it.** Deploy and then query the deployed endpoint, run the migration and
   count the rows, trigger the CI job with `gh workflow run` and follow it with `gh run watch`. A
   system with an API or a CLI is driven through it now.
2. **Monitor.** Start a `Monitor` on a command that prints one line when the condition changes
   (a log tail, a status poll, a health check), and keep working. Monitors are not restored on
   resume and stop when a session is backgrounded, so list each under "In flight" in STATE.md with
   its command verbatim, which is also what lets the Stop gate see it (section 5).
3. **A background poll.** For a wait longer than a monitor's life, such as a 40-minute pipeline,
   run a Bash command with `run_in_background` that exits when the condition holds, bounded by a
   count rather than `timeout`, which stock macOS lacks:
   `for i in $(seq 1 180); do <check> && exit 0; sleep 20; done; exit 1`. Name it under "In flight";
   its completion notification starts your next turn, where you read the result and continue.
4. **A schedule or `/loop`.** Only for a soak with no signal (section 11).

In a headless run, background shells are killed about five seconds after the final result, and a
Monitor holds the process only until the watch times out. Wait there with a foreground command
bounded by the Bash timeout, for example `for i in $(seq 1 27); do <check> && break; sleep 20; done`,
or with a background subagent, which keeps `claude -p` open up to the wait ceiling.

Never report "it will happen when the cron runs" as done.

## 8. Resume protocol

Run this at every start, including the first leg of a headless run.

1. Run `$DRIVE init --goal -` with the goal quoted in GOAL.md on stdin. For the same goal it
   re-creates `.drive/local/active` when it is missing (a fresh clone, a cloud session,
   or an earlier `$DRIVE end`), records this session so the Stop gate holds it, and
   archives nothing; nothing else does either. Then run `$DRIVE start`, which only reads, and
   `$DRIVE preflight` (section 3). Read the STATE.md "Resume here"
   block, GOAL.md, `references/lessons/general.md`, the Learned constraints of the selected domains
   and of `references/capabilities.md`, and `.drive/LESSONS.md`.

   Then settle the status before anything rewrites STATE.md:

   | Status found | Do |
   |---|---|
   | `stalled` | Write REPORT.md opening "Stopped because" and naming the stall, commit it with STATE.md unchanged, and run `$DRIVE end`, which needs STATE.md's exact bytes and a tree that passes the `lint --stop` hygiene checks. The run is then closed as stopped and does no more work: the lint refuses a STATE.md that was `stalled` at HEAD and says `running` or `verifying`. Work that remains is a new run with a goal that names it, and `init` archives the stalled one. |
   | `blocked` | When the condition on the Blocked on line has cleared (the launch preflight now passes, the soak window ended and its check wrote evidence, the owner set the secret), append one DECISIONS.md entry naming that evidence, set `status: running`, set Blocked on to `none`, and continue. When it has not cleared, finish any work that does not depend on it, then end the turn with the status unchanged. |
   | `running`, `verifying` | Continue. |
   | `done`, `stopped`, `aborted` | The run already ended. Report that in one line with REPORT.md's path, and stop, unless the goal of this invocation asks for more, which is a new sub-goal (`references/intake.md` section 13). |
2. Run `git status --porcelain`, `git log --oneline -10`, `git worktree list`, and
   `git branch --list`, and compare them with `.drive/local/baseline.json`. An uncommitted path,
   worktree, or branch the baseline does not list is the first task: inspect it, then land or commit
   it, or save the diff under `.drive/local/logs/` and revert it, and remove the worktree. A worktree
   under `.claude/worktrees/` that this run's own background session created holds run work: commit
   what it holds, record its HEAD, and run `$DRIVE worktree-land <worktree path> <sha>` from the main
   checkout, which cherry-picks its commits and removes the worktree. Then delete its `worktree-*`
   branch with `git branch -d <branch>`, which the guard allows for a branch the baseline does not
   list; when git refuses because the commits were cherry-picked rather than merged, put
   `git branch -D <branch>` in REPORT.md's "Needed from you". Entries
   the baseline lists belong to the owner or another session and stay as they are.
3. Compare STATE.md with the tree. Where they disagree, the tree wins; rewrite STATE.md.
4. For each agent under "In flight", read its report path. A missing report means the work died
   with the old process: re-dispatch from its brief, which tells the maker to report work already
   present rather than redo it. A workflow resumes only in the session that ran it; otherwise
   re-run the script for the items without results.
5. Re-create the monitors, background polls, and self-paced loops STATE.md lists. A task created
   with `CronCreate` in a session resumed with `--resume` comes back on its own unless it expired.
6. Run the cheapest proof command of the current phase before any new work. Red is a failure
   event and comes before anything else.
7. Read the tail of `.drive/local/gate.log` and the Boundary events. If the previous process
   stalled or ended on a bound, decide whether the plan needs a smaller phase and record the
   re-plan in GOAL.md.
8. Re-arm keep-awake. Record `session` (the id), `model` (the model and effort actually serving), and
   `updated` in STATE.md, then continue from `next`.

## 9. Context across a long run

- On 1M-window models auto-compaction runs near 967K tokens. After it, Claude Code re-attaches the
  first 5,000 tokens of each invoked skill within a shared 25,000-token budget, filled from the most
  recently invoked skill, so `/drive` can be dropped entirely once later skills were invoked. SKILL.md
  up to the end of section 6 is about 17,500 characters, and how much of that fits in 5,000 tokens
  depends on how this Markdown tokenizes, so do not count on the re-attached copy reaching the end of
  section 6. The
  SessionStart hook (`drive.py hook-reinject`, on compaction and resume) prints the start view and
  then SKILL.md's standing rules and `references/rigorous.md` section 1, section 6, and section 7 to the end (in a lean run, SKILL.md from its Mode section on, without section 2); sections 2 to 5 come
  back only from that partial copy or a re-read. Re-read STATE.md, GOAL.md, and `.drive/packages/index.md` before acting;
  never trust the summary over the files.
- Send heavy reading to subagents and receive status lines and paths. Read large files in ranges.
  Keep test output to its tail. Keep screenshots in the reviewing agent.
- At every phase gate write down what a fresh session needs, in the files that own it: where things
  stand and what is in flight on the "Resume here" block; what was decided, ruled out, or
  constrained, stated exactly, in DECISIONS.md and "Verified facts"; what is still open under
  "Open failures"; difficulties and options set aside, with why, in DECISIONS.md; and details that
  would be hard to reconstruct (exact commands, shas, ids) where they belong.
- Prefer a fresh session per day-sized phase over one enormous conversation. Resuming a session
  idle for more than about an hour repays its whole context into the prompt cache, and a fresh
  session that reads the files is often cheaper. Headless legs (section 2) give you this
  mechanically. In a single background session, rely on the reinjection hook, and when the
  session has compacted twice or holds more than about 400K tokens, note in the final report that
  a fresh-session resume would have been cheaper.

## 10. Checkpointing with commits

- Commit on the current branch (main in the owner's repositories) at every phase gate, after every
  integrated package, and after every green gate run that changed code. Keep commits small; the
  message states the behavioural claim.
- `.drive/` is committed with the code, except `.drive/local/`. When `$DRIVE visibility` prints
  `PUBLIC`, commit only GOAL.md, STATE.md, STATUS.md, DECISIONS.md, and REPORT.md; proofs, reviews,
  investigations, and research stay ignored, and DECISIONS.md records that choice. The command
  treats anything it cannot establish, including a missing or signed-out `gh`, as `PUBLIC`
  (`state-files.md` section 2). After each commit, update STATE.md `commit:`.
- Before staging, run `git status --short` and look for changes you did not make. Stage explicit
  paths; never `git add -A`.
- `/rewind` checkpoints do not cover Bash changes or subagent edits. Git is the only checkpoint
  that survives a process death and a resume.
- A point in the run is resumable when HEAD, STATE.md, and STATUS.md agree.
- A rigorous run never pushes, and no run creates or moves a branch or tag from the shared checkout
  or from any worktree that shares the repository's refs, detached ones under a scratch directory
  included. The guard refuses `git push` for every agent, from every directory, and for you in a
  rigorous run; in a lean run it lets you push the branch you are on to its upstream, plain and never
  forced, which SKILL.md section 5 asks for after every reviewed package.
  It refuses you the write verbs of `gh pr`, `gh release`, and `gh repo` unless a `deploy` plan line
  in GOAL.md names that command (for example `- [ ] deploy · artifact: the GitHub release · exit:
  gh release create v1.2.0 published · checker: verifier`), and refuses them to every agent always.
  When a deploy or a cloud hand-off needs the commits on a remote, that push is an item in REPORT.md's
  "Needed from you" with the exact command, and the rows that depend on it stay at the rung they
  reached.

## 11. The soak rule

A soak is a period with no signal to wait on, such as "no 5xx responses for 24 hours after
cutover". It is the only reason to schedule anything.

| Scheduler | Use when |
|---|---|
| Desktop scheduled task (`mcp__scheduled-tasks__create_scheduled_task`, found with ToolSearch) | The tool exists. It fires while the desktop app is open and the machine awake, and catches up once after a miss. |
| In-session `/loop <interval> <prompt>` | The session will stay running: interactive, or a headless leg. An idle, unattached background session is stopped after about an hour, and its loops stop firing. |
| The project's existing CI scheduler | The repository already runs scheduled jobs there. |

The soak check decides and acts. Its prompt reads STATE.md, runs the health checks through the
system's own tools, writes evidence under `.drive/proofs/<key>/`, and then advances the stage,
holds, or rolls back through the platform's own tools using the undo recorded in DECISIONS.md.
Its final run invokes `/drive --resume` in the repository so the run continues from files. A CI
job cannot resume a local Claude session, so on a machine with an API-key login and no Desktop app,
where the project's CI is the only scheduler that outlives the session, the check still decides and
acts but the owner resumes the run by hand: the `soak:` Blocked on line and REPORT.md's "Needed from
you" name `/drive --resume` in this repository after the window ends as the step that unblocks it.

While a soak is open, its STATUS row stays below Operational and nothing is Done. If no other work
remains, write REPORT.md so far, and set `status: blocked` with "Blocked on: soak: <key> until
<ISO time>, a destructive cutover step the check decides; the check <name> rolls back on failure."
Remove the scheduled task when the soak ends.

Never leave a scheduled deletion behind the run. `drive.py end` removes the marker, every hook goes
inert, and a scheduled prompt that deletes data would run with no guard and no reviewer. When a line
of DECISIONS.md, STATE.md, or MIGRATION.md records a scheduled deletion, `lint --final` fails until
REPORT.md's "Needed from you" names the deletion as the owner's step, with the read check, the
deletion command, and the verified restore (`references/shapes/move.md`), or until the run stays
open on its `soak:` line and the check has run.

## 12. Cloud hand-off

This is a detected conditional. With an API-key login (section 3) it is unavailable: record the
one line and stop considering it. Otherwise it applies only when all three hold: the account has a
claude.ai login, the remaining phases need no local-only tool (Simulator MCP, Browser pane, local
databases, locally added MCP servers, personal skills), and the run must outlive a shutdown.

1. Personal skills and user-level agents and hooks do not reach a cloud session. Commit the skill
   into the repository as a project skill or a plugin declared in `.claude/settings.json`, and
   record that decision in DECISIONS.md with its undo (`git revert <sha>`).
2. Confirm the cloud environment's network access covers what the run calls.
3. The run pushes nothing, so the hand-off is the owner's step: put `git push` for the current
   branch and `claude --cloud "/drive --resume"` in REPORT.md's "Needed from you". After the cloud
   session, the owner pulls the result back with `claude --teleport <session-id>` and `git pull`
   before any local leg resumes.
4. Cloud sessions store the repository on Anthropic infrastructure under the account's retention.
   Read the retention rule in `safety.md` before recommending a hand-off for a sensitive repository.

## 13. Worked timeline: a greenfield app with a backend and a native client

A two-day `build` run at size XL: an HTTP API with a database, and a native mobile client. It runs
as a background session, launched with `worktree.bgIsolation` set to `none` and
`--permission-mode auto`, on an awake machine. Times are targets that each phase's bound enforces.

| When | Phase | Exit shown by | Delegated | In STATE.md and the files |
|---|---|---|---|---|
| Day 1, 0 to 2 h | intake, research | GOAL.md classified; preflight ok; RESEARCH.md answers each decision it serves | researchers in a read-only Workflow | budget, keep-awake, session id, cloud line |
| Day 1, 2 to 5 h | spec, design, test-plan | SPEC.md, DESIGN.md, TESTPLAN.md reviewed by the auditor | architect; designer for the client | review paths under `.drive/reviews/` |
| Day 1, 5 to 6 h | decompose, wave 0 | ownership disjoint; skeleton, contracts, harness, schema committed one by one | architect; implementers one at a time | `index.md` waves with each package's port, database, and simulator |
| Day 1, 6 to 14 h | build, waves 1 and 2 (backend) | every backend row at Local Proof by verifier verdict | up to 8 implementers per wave; verifiers per package and per wave | commit per package; handoff notes at the gate |
| Day 2, 0 to 6 h | build, waves 3 and 4 (client) | client rows at Local Proof with screenshots from the UI reviewer | implementers on per-feature modules; ui-reviewer | fresh-session resume point written |
| Day 2, 6 to 9 h | live-proof, harden | backend deployed and its smoke suite green against the live URL; security review and severe tests pass | severe-tester, security-reviewer, review panel Workflow | Boundary events if any |
| Day 2, 9 to 11 h | docs, retro, report | final audit passes; `lint --final` green with no worktree, branch, or dirty path created during the run | writer, auditor | `status: done`, then `drive.py end` |

The owner does nothing unless the run blocks. `claude agents` shows its state; STATE.md and
REPORT.md say what happened.
