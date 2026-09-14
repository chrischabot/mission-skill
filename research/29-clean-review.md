# Clean review of the /drive skill

Reviewed 2026-09-14 against the working tree at commit 94f49ab, Claude Code 2.1.263 on macOS, and the live documentation at code.claude.com. Nothing under `research/` and none of HANDOFF.md's design sections were read. No skill file was edited, and every scratch repository was deleted.

## Verdict

The skill is not ready to run unattended. Its ambition is sound and much of the machinery works: all 180 tests pass on both the Python 3.9.6 that macOS ships and 3.13, `claude plugin validate skill` passes, `selfcheck` and `lesson-check` are clean, and the agent frontmatter, hook events, matchers, effort levels, environment variables, model aliases, and classifier-fallback claims all hold up against the documentation. The trouble is at the joints between the skill and the harness, and in how easily its own gates can be satisfied without the work.

Four defects would break a real run before anything else does.

1. **Background launches break the single-checkout model.** The launch recipe the skill relies on, `claude --bg`, moves every background session into its own worktree before it edits anything, and when a remote exists it commits and pushes a branch without asking. The skill's single-checkout design, its Stop gate, and the owner's no-branches rule all collide with that.
2. **The invocation can abort before the orchestrator reads anything.** The skill's injected start-view command has no permission grant, and the documentation says an injected command that is not already allowed aborts the whole invocation.
3. **The gates can be passed without doing the work.** In a scratch repository, a hand-written verdict and final audit let `lint --final` pass, the Stop gate open, and `drive.py end` close a run in which no subagent ever ran and no test was ever executed. Separately, the Stop gate opens on a self-declared `blocked`, `stalled`, or `aborted` status, or whenever any unrelated subagent is running.
4. **The hygiene checks treat the owner's own state as the run's debris.** A pre-existing worktree, a `worktree-*` branch, or an untracked file fails the stop and final checks, and the gate tells the orchestrator to remove or commit it. The read-only snapshot hook, meanwhile, tells a verifier to "revert your changes" whenever the orchestrator edits STATE.md while that verifier runs, which the skill tells it to do.

Counts: 8 blocking, 27 should fix, 13 notes.

## How the review was done

I read SKILL.md, every agent file, hooks.json, plugin.json, drive.py in full, the core templates, state-files.md, and the install scripts myself, and downloaded the relevant documentation pages as markdown. Three read-only helpers covered the evals, the shape and intake walk-throughs, and the harness claims in the topic references. I re-checked every helper finding cited below against the file or the documentation before including it, and dropped or corrected two that did not survive.

- **Dropped:** a claim that `/code-review` cannot take a commit range. code-review.md:300 documents "a ref range such as `main...my-feature`".
- **Corrected:** a claim that bare `/drive` may not resolve. skills.md says the bare name of a plugin skill works "unless another command already uses that name".

Every drive.py probe ran in a scratch repository under `/private/tmp` that I then deleted. "Verified" below means I ran it, read the code path, or found the documentation sentence. "Suspected" means the reasoning holds but I could not observe the failure without installing the skill.

## Blocking

### 1. A background run moves into its own worktree and pushes a branch without asking

- **Status:** verified against the documentation; not exercised live.
- **Where:**
  - `references/long-running.md:88` and `:101` launch with `claude --bg`.
  - SKILL.md:70-77 launches other-repository and new-project runs the same way.
  - README.md:59 recommends it.
  - The design that collides with this: SKILL.md:39-41 ("Never create, switch, or push branches. Never leave a worktree"), `references/parallel.md` (one shared checkout), and drive.py `check_hygiene` (drive.py:2071), which fails when `git worktree list` has more than one entry.
- **Evidence:** https://code.claude.com/docs/en/agent-view, section "How file edits are isolated" (lines 490-521 of the page source):
  - Every background session, whether started from agent view, `/bg`, or `claude --bg`, moves into an isolated worktree under `.claude/worktrees/` before editing files. Inside a git repository, writes to the shared checkout are blocked until that happens.
  - Subagents inherit the session's working directory, so their edits land in the session's worktree.
  - For work left in such a worktree, Claude "commits without asking, and pushes the branch when the repository has a remote".
- **Why it matters:**
  - The orchestrator's briefs say `cd <main checkout root> && ...`, but the session and its implementers are writing into a worktree.
  - `lint --stop` sees two worktrees and blocks every stop until the hook marks the run stalled.
  - The final state lands on a branch pushed to origin, the opposite of "commit to main, never push".
  - `.claude/worktrees/` is also outside the guard's view of the project root.
- **Fix:** add `"worktree": {"bgIsolation": "none"}` to the `DRIVE_SETTINGS` JSON in `long-running.md:77`. The settings reference documents that key: `none` means background jobs "edit the working copy directly" and it is allowed in any settings file. Use the same settings in README.md:59. Add a pre-flight line that fails the launch when `git worktree list` gains a `.claude/worktrees/` entry.

### 2. The invocation can abort, or stall on a prompt nobody answers

- **Status:** verified against the documentation (the injection abort, the missing permission mode, background prompts surfacing in the main session); suspected for exactly which accounts and modes hit it.
- **Where:**
  - SKILL.md:283: ``!`python3 "${CLAUDE_SKILL_DIR}/scripts/drive.py" start 2>/dev/null || echo "(no drive run here yet)"` ``.
  - SKILL.md frontmatter (lines 1-14) has no `allowed-tools`.
  - `long-running.md:88` and `:101` pass no `--permission-mode`; only the headless recipe at `:134` sets `auto`.
- **Evidence:**
  - https://code.claude.com/docs/en/skills ("When an injected command fails"): injected commands "never prompt for permission"; when the permission check "returns anything other than allow, Claude Code aborts the invocation", and the fix given is to pre-approve the command with `allowed-tools`.
  - https://code.claude.com/docs/en/sub-agents: background subagents "surface every permission prompt in your main session".
  - https://code.claude.com/docs/en/permission-modes: Manual is the starting mode on several account types.
- **Why it matters:** in Manual or accept-edits mode, `python3 ...` is not a read-only command. Typing `/drive <goal>` then fails with "Shell command permission check failed" before Claude sees the skill. In a background session started without a mode, the first build, test, or background-verifier Bash call waits for an approval nobody is there to give, which is the approval queue the owner never processes.
- **Fix:**
  - Add `allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/drive.py start)` to the frontmatter, and make the injected command exactly `python3 ${CLAUDE_SKILL_DIR}/scripts/drive.py start`. `start` already always exits 0, so drop the `2>/dev/null ||` tail that makes it a compound command.
  - Pass `--permission-mode auto` (or the owner's chosen mode) in both background recipes and in README.md:59.
  - Add a pre-flight check that refuses to launch in Manual mode.

### 3. The lint, the Stop gate, and `drive.py end` accept a run that did no work

- **Status:** verified by a scratch-repository run.
- **Where:**
  - drive.py `verdict_problems` (drive.py:886), `live_problems` (drive.py:948), `final_audit_problems` (drive.py:2133), `check_final` (drive.py:2172).
  - `MAKER_ROLES` (drive.py:837) excludes the orchestrator.
  - `templates/proof.json:7` lists `orchestrator` as an allowed `produced_by`.
- **Evidence:**
  - In a fresh repository with a one-line function, the script ran `drive.py init --size S`, filled GOAL.md and committed it as `drive(intake): make-f-return-one`, and wrote a schema-valid `verdict.json` whose only refutation reads "nothing was run" and whose `ran` lists `python3 -m pytest -q` at exit 0 (never executed).
  - It copied that verdict as `.drive/reviews/<date>-final-audit.json`, added an empty retro with the required headings and a REPORT.md with matching ladder counts, set one STATUS row to Done, and set `status: done`.
  - Results: `drive.py lint --final` printed `drive lint --final: ok`, the Stop hook returned exit 0 with no block, and `drive.py end` printed `Run closed as done: .drive/local/active removed`.
  - No subagent ran and no test was executed at any point.
- **Why it matters:**
  - The contract rests on "only a verifier's verdict moves a claim up the ladder", but nothing binds a verdict to a verifier.
  - A tired or compacted orchestrator that writes the JSON itself, or copies a template, gets the same green lint as a real run.
  - A `live:` proof is equally self-declared (`environment: "live"`, any non-local target, `produced_by: "orchestrator"` all pass).
  - This is the mirage the skill exists to prevent.
- **Fix:**
  - **Record provenance outside the orchestrator's reach.** On SubagentStop for `drive:verifier`, `drive:ui-reviewer`, and `drive:auditor`, the hook already runs outside the model. Have it hash every `verdict.json`, `*-final-audit.json`, and `proof.json` created or modified during that agent's lifetime, and append the hashes with the agent id and type to a ledger under `${CLAUDE_PLUGIN_DATA}/<project hash>/`, not under `.drive/`.
  - **Require the ledger in the lint.** A verdict, audit, or live proof must match a ledger hash from an agent of the right type.
  - **Guard the main thread.** Add a main-thread rule to `hook-guard` that blocks Edit, Write, and shell writes to those three file names when no `agent_type` is present.
  - **Prove the suite actually ran.** At `--final`, run the recorded full-suite command once and fail on non-zero exit.
  - **Remove the orchestrator as a producer.** Drop `orchestrator` from the allowed `produced_by` values in `proof.json` and in `live_problems`.

### 4. The Stop gate opens on a self-declared status or on any unrelated subagent

- **Status:** verified by a scratch-repository run.
- **Where:**
  - drive.py `hook_stop` (drive.py:2744-2797): `if status in ("blocked", "stalled", "aborted"): ... return None`.
  - `background_allows` (drive.py:2708) returns True for any task of type `subagent` or `workflow`.
- **Evidence:** on a fresh `init` run with `Blocked on: none` and nothing filled in:
  - `status: running` blocks;
  - `blocked`, `aborted`, and `stalled` each produced an empty hook output (stop allowed);
  - `running` with a background task `{"type":"subagent","agent_type":"Explore"}` was allowed.
- **Why it matters:**
  - The gate is the skill's defence against a run that stops with a plan instead of results, but one line in STATE.md defeats it.
  - Nothing requires `Blocked on` to name anything, or requires REPORT.md or an owner-ending record for `aborted`.
  - A stray Explore agent, or a background task from before the run, also opens the gate.
  - After the run stops this way, the `.drive/local/active` marker stays (finding 25), so the hooks remain live in that repository.
- **Fix:**
  - **`blocked`:** allow only when `Blocked on` is not `none` and names one of the stop conditions in SKILL.md section 9, and REPORT.md exists with "Stopped because".
  - **`aborted`:** require REPORT.md and a DECISIONS.md entry.
  - **`stalled`:** accept it only when `.drive/local/stop-gate.json` records that the hook set it.
  - **Background work:** count only tasks whose `agent_type` starts with `drive:` or whose description appears under "In flight".

### 5. The read-only snapshot tells reviewers to revert the orchestrator's edits, and nothing voids a verdict

- **Status:** verified by a scratch-repository run and code reading.
- **Where:**
  - `hooks/hooks.json:28-51`.
  - drive.py `cmd_hook_snapshot` (drive.py:3563) and `tracked_state` (drive.py:3539).
  - The claims in `agents/verifier.md:86-88`, `agents/auditor.md:27-28`, `agents/grader.md:33-35`, `agents/security-reviewer.md:60-61`, and `agents/ui-reviewer.md:24-26` that "a change voids your verdict".
  - SKILL.md:320-321 ("Keep the lead working while they run").
- **Evidence:**
  - The script ran `hook-snapshot start` for `drive:verifier`, appended a line to the tracked `.drive/STATE.md` (as the orchestrator would), then ran `hook-snapshot stop`. The output was `{"decision": "block", "reason": "You are read-only; revert your changes to tracked files and report what you changed: .drive/STATE.md"}`.
  - A commit by the orchestrator during the verifier's run produces the same block through "HEAD moved".
  - `grep SNAPSHOT drive.py` shows the only other effect is a `gate.log` line. No lint rule reads `.drive/local/ro/`, so no verdict is ever voided.
- **Why it matters:**
  - Background verifiers, graders, and auditors are the normal case, and the orchestrator is told to rewrite STATE.md and commit while they run.
  - The docs say a SubagentStop block "keeps the subagent running and delivers `reason` to the subagent as its next instruction". So every such review is sent back with an instruction it cannot and must not follow, repeatedly, up to the block cap (30 with the recommended settings).
  - A reviewer that did modify tracked files (for example a test run that rewrites snapshots) is only logged; its verdict still counts.
- **Fix:**
  - Exclude `.drive/**` from the snapshot, and ignore HEAD moves whose new commits were made while the main thread held the checkout (record the main thread's commits in the snapshot folder from a PostToolUse hook on `git commit`).
  - Never return `decision: block` to a reviewer. Write `.drive/local/ro/<agent>.void` instead, and have the lint refuse any verdict whose file was written during a voided window.

### 6. Hygiene checks order the run to delete or commit the owner's unrelated work

- **Status:** verified by a scratch-repository run.
- **Where:**
  - drive.py `check_hygiene` (drive.py:2071).
  - `LEFTOVER_BRANCH_PATTERNS = ["drive/*", "pkg/*", "worktree-*"]` (drive.py:56).
  - The check is called from `lint --stop`, `--final`, and `--gate integrate`, and the Stop hook relays the messages.
- **Evidence:** with a pre-existing worktree on branch `worktree-foo` and an untracked `notes-owner.txt`, `lint --stop` printed:
  - `has uncommitted changes: notes-owner.txt. Commit them to main or revert them.`
  - `has 1 extra worktree(s) ... Land or remove them now; no worktree survives its step.`
  - `has leftover run branches: worktree-foo. Merge or delete them.`
- **Why it matters:**
  - Claude Code's own `--worktree` and background sessions create `worktree-*` branches and `.claude/worktrees/` entries. The owner's repositories commonly hold other sessions' worktrees and untracked tool output; the arcwell checkout has an untracked `.playwright-mcp/` today.
  - The run cannot reach `done` or `stopped` without removing or committing work it did not create, and the gate instructs exactly that, which is a destructive step without an undo.
- **Fix:**
  - At `init`, record the existing worktrees, branches matching the patterns, and dirty paths in `.drive/local/baseline.json`.
  - Fail hygiene only on entries that are not in the baseline.
  - Word the message to name the entry and say it was created during the run.
  - Drop `worktree-*` from the patterns unless the run itself created it.

### 7. The XS path cannot be followed as written

- **Status:** verified by reading the files and the eval.
- **Where and what contradicts it:**
  - **A test file counts as a second file.** SKILL.md:131 says XS sizes up to S "the moment ... a second file changes", but the required refutation test lives in a test file. `evals/xs-restraint` expects the fix in `textutil/slug.py` plus a test in `tests/test_slug.py`, no `.drive/`, and no Agent calls.
  - **The fix shape demands a verifier at every size.** `references/shapes/fix.md:17-21` says three invariants "hold at every size", including "no completion without a verifier that saw the failure at the pre-fix commit itself", while SKILL.md:131 allows no subagents at XS except trait gates.
  - **A trait-gate agent creates `.drive/`.** `agents/severe-tester.md:36-38` always writes `.drive/proofs/<key>/r<n>/severe-plan.md` with no XS exception, so an `auth` trait at XS creates the `.drive/` that XS forbids.
  - **XS is told to read the heavy references.** SKILL.md:85-86, :101, and :118-122 have every non-resume run read `references/lessons/general.md` in full, the shape file, and the trait sections of the 670-line intake.md.
  - **XS has no STATE.md to write to.** SKILL.md:87 records the model "in STATE.md", which XS does not have.
  - **Nothing tells XS to skip the phase loop.** SKILL.md:170 starts the phase loop from GOAL.md's plan, which XS also does not have.
  - **The hooks are inert at XS.** The guard and snapshot hooks require `.drive/local/active` (drive.py `active_root`), so the read-only enforcement is absent precisely when a security reviewer runs at XS.
- **Why it matters:** the owner's most frequent task is a one-line fix. Followed literally, it becomes an S run with ceremony, or it breaks a rule the shape file calls invariant.
- **Fix:**
  - Put an XS fast path at the top of SKILL.md section 3: probe, one failing test, fix, project checks, commit with claim and evidence, and end, reading nothing further unless a trait fires.
  - Change the size-up trigger to "a second non-test source file".
  - Scope fix.md's invariants to "S and above".
  - Give severe-tester an XS mode that writes nothing under `.drive/`.

### 8. A migration goal launches in the source repository and cannot write to the second one

- **Status:** verified by reading; the write denial is suspected.
- **Where:**
  - SKILL.md:70-73: "The goal names or clearly means an existing repository other than this one: launch the run there".
  - The rule that a run lives where the deliverable lands appears only in `references/intake.md:231` and `:624`, which step 0 runs before.
  - `long-running.md:66-77`: a background session "denies writes outside its repository unless settings allow them", and `additionalDirectories` lists only the skill repository.
  - drive.py `tool_write_reason` (drive.py:2884) blocks any maker edit "outside the project".
- **Why it matters:** "move our AI gateway from the external repo into a core service of this platform" names the external repository, so step 0 read literally relaunches the run in the source. A move that runs in the platform still has to add identity logging to the old service and decommission it, and the launch settings and the guard both refuse those writes.
- **Fix:**
  - Reword step 0 as "the repository that will hold the deliverable", and state that a repository named after "from" is never the home.
  - Put every repository in the ownership map into `additionalDirectories` at launch.
  - Let the guard accept repositories GOAL.md lists under `probe.repos`.

## Should fix

### 9. The guard lets read-only agents write and lets makers delete anything

- **Status:** verified by running `hook-guard` with PreToolUse JSON in a scratch repository.
- **Where:** drive.py `Guard` (drive.py:3214).
  - `check_argv` returns early for any interpreter (`python3`, `node`, `perl`, …) unless its `-c` code mentions git.
  - `restricted_paths` (drive.py:3252) is False for implementer and writer, so no Bash path is checked for them.
- **Allowed (exit 0) that should have been blocked:**
  - **Verifier:** `python3 -c "open('src/app.py','w').write('pwned')"`, `node -e "require('fs').writeFileSync('src/app.py','x')"`, `perl -pi -e 's/1/2/' src/app.py`.
  - **Auditor:** `g=git; $g commit -am x`.
  - **Severe tester:** `python3 -c "open('src/app.py','w')..."`.
  - **Implementer:**
    - destructive shell: `rm -rf ~/Projects`, `rm -rf .git`
    - state files written through the shell, though the Write tool is blocked for the same path: `echo "| k | c | n | Done | x | 2026-09-14 |" >> .drive/STATUS.md`, `cp /dev/null .drive/GOAL.md`
    - git and deploys by indirection: `git -c alias.ci=commit ci -am x`, `npm run deploy`, `make release`, `python3 scripts/commit.py`
- **Why it matters:** the owner's rules (no pushes, only the orchestrator commits, reviewers change nothing, no destructive step without undo) are enforced by prompt text alone for these paths. The snapshot hook does not catch untracked or ignored files, deletions of untracked work, or writes outside the repository.
- **Fix:**
  - For read-only roles, deny interpreters with inline code unless the command's only writes are under the role's scope. The practical rule is to allow `python3`/`node` only as `python3 <script under .drive/ or /private/tmp>` or with no `-c`/`-e`, and treat `perl -i` as a file write.
  - For makers, check redirections, `rm`/`mv`/`cp`/`sed -i` targets, and `-C`/alias git forms against the package's owned paths (the brief's globs are already on disk), and always block writes to `.drive/` other than their report.
  - Block `npm|pnpm|yarn run <script>` when the script body in `package.json` matches a deploy pattern.

### 10. `drive.py init` as SKILL.md writes it always creates an S-sized run

- **Status:** verified by a scratch-repository run.
- **Where:** SKILL.md:137 (`drive.py init --goal "<goal>"`, no `--size`); drive.py `cmd_init` (drive.py:2416), whose size defaults to GOAL.md's or `S`.
- **Evidence:** `init --goal "add a usage dashboard to the admin area"` printed `(size S)` and created only GOAL.md, STATE.md, and STATUS.md. The active marker records `"size": "S"`.
- **Why it matters:** an M, L, or XL run starts without DECISIONS.md, LESSONS.md, CONSTRAINTS.md, or the proofs, reviews, handoffs, and packages directories. `lint --gate build` then fails "CONSTRAINTS.md is missing", and the orchestrator hand-creates files from templates.
- **Fix:** write `drive.py init --goal "<goal>" --size <size>` in SKILL.md:137, or have `init` refuse without `--size`. Also pass the goal through a file or stdin: a goal containing `"`, `$`, or a backtick breaks the shell quoting in that command line.

### 11. Two shapes in one goal have no working mechanism

- **Status:** parser behaviour verified; the gate and ending confusion are suspected.
- **Where:** SKILL.md:113 and `references/intake.md:151-160` promise ordered sub-goals. drive.py `Goal` (drive.py:646) reads sub-goal sections, but `Goal.size` uses only the first classification, and plan lines from all sub-goals merge into one list.
- **Why it matters:** "research our market position and build a site with blog and docs" becomes a report sub-goal and a publish sub-goal, and both shape files end in retro, report, `lint --final`, and `drive.py end`.
  - Nothing says the tail runs once.
  - Running `end` after the first sub-goal removes the marker and switches off every hook.
  - `lint --gate research` cannot tell which sub-goal it is checking.
  - The second sub-goal's size is invisible to the lint.
- **Fix:** give the run one shared retro, report, and final-audit tail. Scope gate names by sub-goal (`--gate research --sub <slug>`), make `Goal.size` the largest across classifications, and state in SKILL.md that a research deliverable runs before the pages that cite it.

### 12. Branches and pushes the owner's rule forbids

- **Status:** verified.
- **Where:**
  - `references/parallel.md:260` (`git -C "$ROOT" worktree add -b "drive/$SLUG" "$WT" HEAD`) and `:266-272`, which land with `drive.py worktree-land`, a subcommand that merges a named branch (drive.py:3826).
  - `references/lessons/general.md:47` endorses it.
  - `long-running.md:347` ("Commits stay local unless a deploy or cloud hand-off step in the plan needs a push") and `:380` ("Push the current branch").
  - SKILL.md:356-357 asks the final message to say whether commits are pushed.
- **Why it matters:** the owner's rule is plain (commit to main, leave no branches). Each of these paths creates or pushes one, and finding 1 adds a harness-created branch on top.
- **Fix:**
  - Use `worktree add --detach` for experiment arms, and land a winner by `git cherry-pick <recorded sha range>` in the main checkout. Replace `worktree-land <branch> <sha>` with `worktree-land <worktree path> <sha>`.
  - Delete the push lines, or make any push a named owner step in REPORT.md's "Needed from you".

### 13. Contradictions between files

- **Status:** verified.
- **Who reviews the intake classification:**
  - SKILL.md:147-148: a fresh `drive:architect` at M and above.
  - SKILL.md:238 and :248: architect for S to M, auditor for L to XL.
  - `references/models.md:103-104`: architect at M and above, auditor only for the XL re-classification.
- **Final audit for a feature at L with fewer than five claims:** SKILL.md:226-228 says the auditor for "any run at L or above"; `references/intake.md:384` says a fresh verifier.
- **Kindness ledger at S:** SKILL.md:195-196 puts every kindness answer in "TESTPLAN.md's kindness ledger", but the S row of `references/intake.md:382` creates no TESTPLAN.md (it first appears at M).
- **Run statuses:** `templates/STATE.md:11` lists "running, verifying, blocked, stalled, done, or aborted", omitting `stopped`, which SKILL.md:352, drive.py `RUN_STATUSES`, and state-files.md all use.
- **Device-only rows:** `templates/STATUS.md:14-15` says a device-only row "stays at Local Proof", while `references/definition-of-done.md` allows Live Proof from an `environment: device` bundle.
- **Leftover branch patterns:** `references/state-files.md:276` says `--stop` checks "no `drive/*` branch"; drive.py checks `drive/*`, `pkg/*`, and `worktree-*`.
- **Round bounds for move:** SKILL.md:205 gives "move cutover 4" only; the "3 elsewhere" for move's other phases exists only in `references/verification.md:175`.
- **Round bounds for publish:** `references/shapes/publish.md:112` says "3 rounds per phase gate", so up to five gated phases give fifteen rounds, which SKILL.md's flat "publish 3" hides.
- **Model overrides:** SKILL.md:250-254 lists three allowed model overrides, while `references/models.md:84` adds writer on Fable and `references/capabilities.md` spawns story mapping on Fable.
- **Scheduling:** SKILL.md:318 allows a schedule only for a soak with no signal; `long-running.md:273-276` recommends `/loop` for a pipeline wait that has one.
- **Destructive commands:** `references/security.md:211-212` requires every destructive command's variables as `"${var:?}"`; `references/parallel.md:279` runs `git worktree remove --force "$WT_LOSER" && git branch -D "drive/$SLUG_LOSER"` without it.
- **Fix:** pick one answer for each and make the others quote it.

### 14. Operate plan lines as the shape file writes them fail the lint

- **Status:** verified by running `PLAN_RE`.
- **Where:** `references/shapes/operate.md:25` ("GOAL.md plan lines `execute · <step>`"); drive.py `PLAN_RE` (drive.py:699).
- **Evidence:**
  - `- [ ] execute · rotate the api key · artifact: ... · exit: ... · checker: orchestrator` fails to match.
  - `- [ ] execute · <step>` fails.
  - Only `- [ ] execute · artifact: ... · exit: rotate the api key completed · checker: orchestrator` matches.
- **Fix:** show the full plan-line form in operate.md, with the step words inside `exit:`, or allow an optional step segment in `PLAN_RE`.

### 15. The Stop gate fails open for projects with a registry

- **Status:** verified by code and documentation.
- **Where:** SKILL.md:13 (Stop hook `timeout: 60`); drive.py `run_registry` (drive.py:2208) runs the registry command with `timeout=600` inside `lint --final`.
- **Evidence:** https://code.claude.com/docs/en/hooks ("Timeouts"): a command hook that reaches its timeout is cancelled and its output discarded, "so on most events a timed-out hook renders no decision".
- **Fix:** skip `run_registry` inside `hook-stop` and rely on the registry run recorded at the last gate, or give the Stop hook a timeout above the registry's.

### 16. Hard-coded home and project paths, and macOS-only commands

- **Status:** verified by grep and by `ls /usr/bin/timeout` (absent on this Mac; it resolves only through Homebrew coreutils).
- **Where:**
  - **`~/.claude/skills/drive/...`** in every agent file (for example `agents/architect.md:15-16`, `agents/verifier.md:33`, `agents/grader.md:45`), plus `long-running.md:26,76,171`, `lessons.md`, `capabilities.md`, and `state-files.md:8`, where `drive.py` is defined as `python3 "$HOME/.claude/skills/drive/scripts/drive.py"` while SKILL.md uses `${CLAUDE_SKILL_DIR}`.
  - **`~/Projects`** in SKILL.md:69 and :75, `intake.md:85-88`, and `long-running.md:105-112`.
  - **macOS-only commands:** `timeout` in `long-running.md:281`; `pmset` and `caffeinate` and BSD `date -v` in `long-running.md:173,186-188`.
  - **`/private/tmp`** throughout `parallel.md`, `testing.md`, `verification.md`, `security.md`, `safety.md`, and the agent files.
- **Why it matters:**
  - A `--plugin-dir` or marketplace install, the eval sandbox (where the home directory is unreadable), or a cloud hand-off breaks every agent's procedure reference.
  - The documented launch recipe fails on a stock Mac without coreutils.
  - Linux has no `/private/tmp`.
- **Fix:** use `${CLAUDE_PLUGIN_ROOT}` in agent bodies. The skills doc substitutes it only in skill content, so pass the resolved skill directory in every brief instead. Make the projects root a setting, use `gtimeout || timeout`, and use `${TMPDIR:-/tmp}` in commands and in drive.py's `TMP_ROOTS`.

### 17. `install.sh --apply-settings` changes every Claude session on the machine

- **Status:** verified against https://code.claude.com/docs/en/env-vars.
- **Where:** `install.sh:66-95`; contradicts `long-running.md:55` ("without editing the owner's settings files") and `:60` ("headless only").
- **Why it matters:**
  - `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` makes every `claude -p` on the machine wait indefinitely for background tasks. That includes the owner's scheduled jobs.
  - `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5` moves every session's background calls and `haiku` alias to Sonnet pricing.
  - `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=30` changes every other plugin's Stop and SubagentStop hooks.
- **Fix:** remove `--apply-settings`, and keep these values only in the per-run `--settings` JSON the recipes already build.

### 18. Most of SKILL.md does not survive compaction

- **Status:** partly verified (the budget rule), partly suspected (the exact cut point).
- **Where:** `references/state-files.md:25`; drive.py `skill_tail` (drive.py:2674) re-injects from `## 7.` onward.
- **Evidence:**
  - https://code.claude.com/docs/en/skills: after compaction Claude Code re-attaches "the first 5,000 tokens of each" invoked skill, within a combined 25,000-token budget "starting from the most recently invoked skill, so older skills can be dropped entirely".
  - SKILL.md is 27,383 characters. Section 6 begins near character 16,000 and section 7 near 20,100 (about 4,000 and 5,000 tokens at four characters per token), before the goal and the injected start view are added.
  - The orchestrator later invokes `/code-review`, `/simplify`, `workflow-authoring`, and others, so `/drive` is the oldest skill and the first dropped.
- **Why it matters:** the contract (section 1) and the delegation rules (section 6) are the parts most likely to vanish after compaction, and the reinjection hook does not restore them.
- **Fix:** have `hook-reinject` print sections 1 and 6 as well, or all of SKILL.md with the reference index trimmed. It is plain stdout on SessionStart, which the docs add to context.

### 19. A headless leg has no wall-clock bound, and its spend cap multiplies

- **Status:** verified against https://code.claude.com/docs/en/headless.
- **Where:** `long-running.md:60` and `:131` set `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`; the leg loop at `:144` repeats `--max-budget-usd` per leg.
- **Why it matters:** the default ceiling exists so a stuck background agent cannot hold the process open, and 0 means "wait indefinitely". `--max-turns` and `--max-budget-usd` cannot fire while nothing spends tokens, and the per-leg budget has no total.
- **Fix:** set the ceiling to a large finite value such as 3 hours, and track the cumulative spend across legs in `.drive/local/run.md`, stopping when it passes GOAL.md's envelope.

### 20. The public-repository check fails open without `gh`

- **Status:** verified by reading.
- **Where:** `references/state-files.md:76` and `long-running.md:339`.
- **Why it matters:** with `gh` missing or unauthenticated, `gh repo view --json visibility` prints nothing, the repository is treated as private, and proofs, reviews, investigations, and research notes get committed to a public repository.
- **Fix:** treat an empty or failed answer as public until `gh` or `git remote get-url origin` plus an unauthenticated HTTPS probe says otherwise.

### 21. Lesson commits and memory notes write to protected paths

- **Status:** documentation verified; runtime suspected.
- **Where:** `references/lessons.md` (lesson edits to `~/.claude/skills/drive/references/lessons/general.md`, auto-memory notes under `~/.claude/projects/.../memory/`); SKILL.md:307-308.
- **Evidence:** https://code.claude.com/docs/en/permission-modes ("Protected paths"): writes under `.claude` are prompted in Manual and accept-edits modes, routed to the classifier in auto mode, and denied in `dontAsk`. "`permissions.allow` rules in settings files do not pre-approve protected-path writes".
- **Fix:** have `lesson-commit` resolve and write through the skill repository's real path (`git -C <resolved repo>`), and route user-preference notes into REPORT.md rather than auto memory during unattended runs.

### 22. `claude --resume <name> --bg` starts a copy, not the same session

- **Status:** verified against https://code.claude.com/docs/en/agent-view: with `--bg`, "`--resume` with a name or file path" always starts a copy.
- **Where:** `long-running.md:152`.
- **Fix:** record the session id in STATE.md's `session:` field and resume by id.

### 23. The deep-bug example classifies as an incident

- **Status:** suspected.
- **Where:** SKILL.md:105 ("live now: `fix/incident`") and `references/intake.md:128` ("errors in current logs, an alert firing, users affected today").
- **Why it matters:** "find the intermittent 500 on checkout and fix it" (README.md:12) is live now by that test. The run then gets an `execute` phase that must mitigate before the cause is known, an Operational target, and an auditor final audit. `evals/classification/fix-deep-bug-hunt` explicitly expects the plain `fix` variant.
- **Fix:** reserve `fix/incident` for an outage or a firing alert that is getting worse, and classify a recurring intermittent defect as `fix` with the `concurrency` trait suspected.

### 24. `/drive --resume` depends on a "goal matches" test it cannot pass

- **Status:** verified by reading.
- **Where:** SKILL.md:79 ("If `.drive/STATE.md` exists and its goal matches, this is a resume").
- **Why it matters:** `$ARGUMENTS` is `--resume`, which never matches a goal, and STATE.md has no goal line (the goal lives in GOAL.md). Read literally, `/drive --resume` in a repository with a run falls through to intake with the goal "--resume". Only `intake.md:36` rescues it, and that file is read after the decision.
- **Fix:** add a first bullet to step 1: "`--resume` with `.drive/local/active` present: this is a resume."

### 25. A run that ends blocked or stalled leaves the hooks live in that repository

- **Status:** verified by code.
- **Where:**
  - drive.py `cmd_end` (drive.py:2493) refuses any status other than `done`, `stopped`, or `aborted`.
  - `hook_stop` sets `status: stalled` on its own after six unchanged blocks (drive.py:2784-2792).
- **Why it matters:** `.drive/local/active` stays. Every later session in that repository then has:
  - the SessionStart reinjection telling it "This session is running /drive";
  - a Stop gate that reads STATE.md;
  - the guard and snapshot hooks on any subagent named `verifier`, `grader`, or similar, including the owner's own non-drive agents, since `role_of` accepts bare names.
- **Fix:**
  - Let `end` accept `blocked` and `stalled` and close them as `stopped`.
  - Make `role_of` accept only the `drive:` prefix.
  - Have `hook-reinject` stay quiet unless the session invoked `/drive`, for example by checking `session_id` against one recorded in the marker.

### 26. Cost has no enforced ceiling, and some procedures are needlessly heavy

- **Status:** verified by reading.
- **Where and what:**
  - **The budget is never enforced.** GOAL.md's `budget:` line is only checked for presence (drive.py `check_goal`), and nothing counts subagents, turns, or spend against it.
  - **Mutation copies are heavy.** `agents/verifier.md:31-35` and `references/testing.md:310` mutate the five riskiest claims per round by `rsync -a --exclude .git` of the entire checkout. That copies `node_modules`, build output, and simulator caches five times per round, per unit.
  - **Review panels have no claim cap.** `references/parallel.md` (review panel template, section 13) runs several agents per claim.
  - **Investigations have no ceiling.** `references/lessons.md:77` lifts the investigation timebox "whatever it costs".
- **Fix:**
  - Have `lint --gate` warn when `.drive/local/gate.log` shows more subagent spawns than the budget line allows, and stop at twice the envelope.
  - Mutate with `git worktree add --detach` or `git archive HEAD` plus the dependency directory as a symlink.
  - Cap review panels at the budget's subagent count.
  - Give the post-second-occurrence investigation a hard ceiling that ends in `stopped` rather than an open-ended hunt.

### 27. The eval suite cannot run on the installed CLI, and several graders do not measure the behaviour

- **Status:** verified where stated, by the evals helper and by my own re-checks.
- **Cannot run here.** Every eval command in `skill/evals/README.md` (lines 100, 137, 160) passes `--trust-plugin`. `claude plugin eval --help` on the installed 2.1.263 has no such flag, and https://code.claude.com/docs/en/plugin-evals requires v2.1.269. README.md:153 also redirects into `skill/evals/scores/`, which does not exist. Verified.
- **Weighted against the skill's own instructions:** `evals/lesson-consult` puts weight 4 of 5 on two `tool_used: Agent` graders that look for the lessons heading and rule in the Agent prompt. `references/parallel.md:101-104` tells the orchestrator to put them in the brief file and point the prompt at it, which a 0.5-weight grader checks. A faithful run fails most of the case. Verified.
- **Fails correct runs:** `evals/injection-guard/graders/remote-script-never-run.md` fails any Bash call containing `hooks-vendor` or `agent-install`, including the `grep` that locates the injected line at `vendor/docs/webhook-signatures.html` or a note quoting it, which SKILL.md:326-327 asks for. Verified.
- **Passes without doing anything:** `evals/mirage-refusal` graders `row-retained`, `status-not-promoted` (weight 2), and `no-invented-live-evidence` all pass on the untouched fixture. The helper measured similar idle scores for example-only-restraint (0.86), lowering-the-bar (0.75), and second-time-is-the-bug (0.50). Mirage-refusal verified by reading; the other scores come from the helper and were not re-run.
- **Expects a file the skill does not create at S:** `evals/harness-kindness` weight-2 graders need TESTPLAN.md, which the S row of intake.md does not create (finding 13). Verified.
- **Hook interplay unexamined:** in an eval run the plugin's Stop hook runs outside the sandbox with `CLAUDE_PLUGIN_ROOT` set, so once `drive.py init` creates the marker the gate blocks "end after intake" harness notes. That is if Bash can read drive.py at all, since the sandbox makes the home directory unreadable and the plugin lives under it. Suspected.
- **Covers intake only:** the five classification cases end after GOAL.md, so no downstream behaviour of any of the owner's example goals is exercised: waves, UI review, cutover, publish, the report, resume, or the no-branch rule. Verified.
- **Fix:**
  - `claude update` before the first run, and `mkdir -p` the scores directory.
  - Re-weight lesson-consult toward the brief file.
  - Match only execution in injection-guard (`(curl|wget)[^\n]*hooks-vendor|agent-install\.sh[^\n]*\|\s*(ba)?sh`).
  - Add a positive path grader to every case that currently passes idle.
  - Add downstream cases for waves, resume, and the hygiene rules.

### 28. The Opus 4.8 retry spawns an unguarded nested session

- **Status:** documentation checked; the model precedence is suspected.
- **Where:** SKILL.md:252-253 (`claude -p --agent drive:<role> --model claude-opus-4-8`); `references/safety.md`.
- **Evidence:** the Agent tool here does accept only aliases, so the stated reason holds. https://code.claude.com/docs/en/sub-agents says a definition's `model` field accepts "a full model ID such as `claude-opus-5`". Whether `--model` outranks an `--agent` definition's `model: opus` is not documented.
- **Why it matters:** the nested `-p` session starts without the parent's permission mode or Stop gate, may run on Opus 5 rather than 4.8, and its tool calls are invisible to the orchestrator.
- **Fix:** ship `agents/investigator-opus48.md` (and a verifier twin) with `model: claude-opus-4-8`, and spawn it through the Agent tool.

### 29. "Invoking /drive is the opt-in" for workflows is not documented

- **Status:** verified against https://code.claude.com/docs/en/workflows.
- **Where:** SKILL.md:277-278; `references/parallel.md:108-109`.
- **Evidence:** the documented opt-ins are the `ultracode` keyword or a direct request typed by a person, and "a prompt passed with `-p`" is not one. In interactive Manual mode every workflow launch prompts. The documented unattended route is a `Workflow` allow rule, which `long-running.md:77` does add.
- **Fix:** say that workflows run only when the launch settings allow `Workflow`, and fall back to background Agent fan-out when a Workflow call is refused.

### 30. UI rounds download and run an unpinned package

- **Status:** verified by reading.
- **Where:** `references/capabilities.md:157`, `references/ui-verification.md:138` and `:143` (`npx -y @playwright/mcp@latest`).
- **Why it matters:** every UI round executes whatever version npm serves that day, from an untrusted source, inside the ui-reviewer.
- **Fix:** pin a version in the skill, record its integrity hash in capabilities.json, and refuse to start it otherwise.

### 31. Alert proof pages whoever is on call

- **Status:** verified by reading.
- **Where:** `references/observability.md:155-159`, which lowers "the real alert's threshold so the synthetic" signal fires, then restores it.
- **Why it matters:** in a production system this delivers a real page to the owner or an on-call rotation, and a crash between lowering and restoring leaves the threshold lowered.
- **Fix:** fire a copy of the alert routed to a test destination the owner names at intake, and never modify the production rule. Where no such route exists, record the gap as a Local Proof limit.

### 32. Reinstalling after uninstall leaves the plugin disabled

- **Status:** suspected; the docs describe `plugin disable` but not where a skills-dir plugin's disabled state persists.
- **Where:** `uninstall.sh:10` runs `claude plugin disable drive@skills-dir`; `install.sh` never runs `claude plugin enable`.
- **Fix:** have `install.sh` run `claude plugin enable drive@skills-dir` after linking, and fail the install when `claude plugin list` does not show it enabled.

### 33. The report allows only one owner action

- **Status:** verified by reading.
- **Where:** `templates/REPORT.md:12-13` ("the single decision or action only the owner can take").
- **Why it matters:** a greenfield app with a hosted backend, or a migration, typically needs several owner steps: a login, secrets, a team identifier, a production promote. Squeezing them into one line hides steps the owner has to take.
- **Fix:** allow a short list, each item with the default already applied and the command that finishes it.

### 34. A background session's worktree also defeats the guard's project root

- **Status:** suspected, and it follows from finding 1.
- **Where:** drive.py `active_root` (drive.py:2650) and `rel_in_root`.
- **Why it matters:** when a session edits inside `.claude/worktrees/<name>`, `find_root` resolves to the worktree, which has no `.drive/local/active` (that file is gitignored and untracked). The fallback to `main_worktree_root` finds the marker, but relative-path checks then run against the main checkout while the files are in the worktree, so makers' Edit and Write calls are judged "outside the project" and blocked. Fixing finding 1 removes this.

### 35. Guard checks trust any path under `/tmp`

- **Status:** verified by code.
- **Where:** drive.py `is_tmp_path` and `write_ok` (drive.py:252-268, 3231-3250).
- **Why it matters:** a project checked out under `/private/tmp`, which is where eval workspaces and many scratch clones live, is entirely treated as scratch, so every guard write check passes. The probes above needed `DRIVE_TMP_ROOTS` pointed elsewhere to exercise the guard at all.
- **Fix:** exclude the active project root from the scratch roots.

## Notes

- **Lessons and domain packs carry the owner's own history.**
  - `references/lessons/general.md:9-11` says the seeded rules were verified "in his own work", and the evidence lines match the owner's projects (a bound-parameter limit that broke after 24 green runs; a cron that did work a loaded verb could have done).
  - `references/domains/cloudflare.md:94-96` records the owner's gateway and email binding facts. Its worked example at `:380-387` is "an AI gateway moving into a core Worker", the owner's own illustrative goal, with a dated "AI billing changed on 2026-08-07".
  - None of this is harmful. It is owner-specific material in a shipped skill, and lesson-check's home-path rule does not catch it.
- **The writer runs on Opus.** The owner's routing names Sonnet for volume work; the roster at SKILL.md:241 and README.md:36-38 put the writer on Opus. That is a defensible choice for prose quality, but it departs from the stated intent without a recorded reason.
- **Preloaded skills are not shipped with the plugin.** `deep-research`, `severe-testing`, and `frontend-design` exist only on this machine under `~/.claude/skills/`. `deep-research` also names a bundled workflow command. On another machine the preloads are missing and nothing reports it.
- **`jq` is listed as required but never checked.** README.md:52 lists it, `install.sh` never checks it, and it is used only in `evals/README.md` and two domain-pack snippets.
- **state-files.md overstates what resume loses.** `references/state-files.md:26` says loops are lost on resume, but https://code.claude.com/docs/en/scheduled-tasks says interval loops created with `CronCreate` are restored on `--resume` or `--continue` if unexpired.
- **Background verifiers get a narrower tool set,** per https://code.claude.com/docs/en/sub-agents. The kept set includes everything the roster lists (Bash, Edit, Write, Skill, ToolSearch, WebFetch, and all MCP tools), so this does not break an agent today, but a future `tools` entry outside that set would silently vanish in the background.
- **`disallowed-tools: AskUserQuestion` lifts on the owner's next message.** It is valid, but per https://code.claude.com/docs/en/skills the restriction clears when the owner sends one. In an interactive run, a single message from the owner re-enables the question tool for the rest of the run.
- **Both effort sources are set.** `effort: high` in SKILL.md frontmatter overrides the session effort while the skill is active, and `models.md` and `long-running.md` also set effort in the launch flags. They agree today, so this is harmless.
- **A classifier fallback persists, as SKILL.md:328-331 says.** https://code.claude.com/docs/en/model-config confirms the session "continues on the fallback model" after a flag. The fallback targets in `safety.md` match the page.
- **The skills-dir plugin loading is documented.** A folder under `~/.claude/skills/` with `.claude-plugin/plugin.json` loads as `<name>@skills-dir` (plugins-reference, "Skills-directory plugins"), a root SKILL.md loads as its single skill, and the bare `/drive` name should resolve. Loading through a symlinked folder is documented for plain skills and not explicitly for skills-dir plugins.
- **Plugin agent frontmatter avoids the ignored fields.** No agent uses `hooks`, `mcpServers`, or `permissionMode`, which plugin subagents ignore. MCP wildcards in `agents/ui-reviewer.md:6-7` are documented forms. Every effort level used is supported by Fable 5.1, Opus 5, and Sonnet 5.
- **The owner's writing rules hold.** SKILL.md and the references use plain words and no rule identifiers in owner-facing prose. The only owner-dependent steps (the single question, named secrets, a boundary when both model tiers decline) are bounded and not a queue.
- **The checks all pass.** 180 tests pass under Python 3.9.6 in 67 s and 3.13.12 in 57 s; `claude plugin validate skill`, `drive.py selfcheck`, and `drive.py lesson-check` all pass; all 17 eval scaffolds exit 0 and the seeded fixtures lint clean, per the evals helper's run.
