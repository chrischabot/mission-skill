# State files

Read this file when you create, write, repair, or read any file under `.drive/`: at intake, at
every phase gate, when the Stop gate blocks you, at resume, when a run for a different goal is
already present, and when you write the report. It decides which files a run creates, the grammar
of each, who may write them, what may go in them, how to read them at start, how to hand a phase
to a fresh context, what the lint enforces, and which statuses end a run. `drive.py <subcommand>` means
`python3 <skill dir>/scripts/drive.py <subcommand>`, with the absolute skill directory SKILL.md
names. The script and the templates
it copies live at `scripts/drive.py` and `templates/`; where a template and this file disagree on a
field name, the template wins and this file is the defect.

**Contents.** 1 What survives · 2 The `.drive/` layout · 3 One writer · 4 Content rules ·
5 GOAL.md · 6 STATE.md · 7 STATUS.md · 8 DECISIONS.md and project LESSONS.md · 9 What the lint
enforces · 10 Write before stopping · 11 Read at start, resume, and in-flight work · 12 The
phase-handoff summary · 13 Size control · 14 Precedence, registries, and paused runs ·
15 The report · 16 Excuses and rebuttals · 17 Red flags

## 1. What survives

Nothing you know survives compaction, the end of a session, or a subagent boundary unless it is in
code, tests, git, or `.drive/`. Treat every turn as if your context could reset at its end.

| Boundary | What comes back | What is lost |
|---|---|---|
| Auto-compaction | the first ~5,000 tokens of SKILL.md, unless later skills filled the shared 25,000-token budget first; SKILL.md up to the end of section 6 is about 17,500 characters, and how much of that fits in 5,000 tokens depends on how this Markdown tokenizes, so do not count on that copy reaching the end of section 6; the output of the SessionStart hook `drive.py hook-reinject` after a compaction or resume (the start view, then SKILL.md's section 1, standing rules, section 6, and section 7 to the end), printed only in a session the run's marker records (in any session while it records none); CLAUDE.md; up to five recently modified files, each only if under ~5,000 tokens | everything else you read or reasoned, including every reference file |
| Session end or `--resume` | files and git; a resumed session also restores its conversation and the unexpired tasks it created with `CronCreate` | background subagents, monitors, self-paced `/loop` tasks, background shells |
| Subagent spawn | its own prompt, the brief, CLAUDE.md, git status, its preloads | your conversation and auto memory |
| Subagent return | a status line, paths, at most 1,500 characters | everything it did not write to a file |

Rewrite STATE.md before every fan-out and before any step you expect to be long. Compaction can
land mid-step, and a small, recently written STATE.md is one of the files that returns whole.

## 2. The `.drive/` layout

All run state lives in `.drive/` at the root of the repository the session started in, committed on
the current branch with the code. SKILL.md section 2 step 0 moves a run whose goal belongs to another
repository before anything is written. `.drive/local/` is gitignored and holds `active` (the marker
the hooks test), `baseline.json` (written by `drive.py init` for a new run, and at a resume when it is missing: HEAD, the current branch, the real path
of every linked worktree, every local branch, every uncommitted path outside `.drive/` apart from
`.gitignore`, and each untracked directory, every file under which counts as the owner's), `session.json` (the session id and permission mode the hooks last saw),
`stop-gate.json`, `ro/` (read-only review snapshots and `.void` markers), `gate.log`,
`lost-marker-warned.json` (the sessions the Stop hook has already warned that the marker is missing),
`workers/<name>/report.md`, `logs/`, `ui/`, `ios/` (device ids and raw result bundles), `research/`
(lane reports and saved page text), `recordings/`, `backups/`, `archive/` (a paused run's local
files), `scratch.list`, `run.md` (including the headless leg spend), and `ops-<key>-fault.md`. No secret
goes anywhere in `.drive/` outside `.drive/local/`, and a test credential kept there, such as a smoke
token in `.drive/local/smoke.env`, is rotated when the run ends. An XS run
creates no `.drive/`; its commit body records the claim and evidence. An S run creates GOAL.md,
STATE.md, STATUS.md with one to three rows, and the shape's own ledger (HUNT.md for a fix,
RESEARCH.md for a report). M and above creates everything the shape and traits call for:

| File or directory | Holds | Created for |
|---|---|---|
| `GOAL.md`, `STATE.md`, `STATUS.md` | the plan; working memory and resume pointer; the ladder | every run above XS |
| `DECISIONS.md` | decisions taken on the owner's behalf, each with its undo | M and above, or any size once a decision or narrowing occurs |
| `LESSONS.md` | project lessons from verified failures | M and above, or once a lesson routes here |
| `CONSTRAINTS.md` | the quality floor | M and above, written at archaeology or after wave 0 for a greenfield build; any size once a quarantine exception is recorded |
| `capabilities.json` | the capability preflight | S and above, written after `drive.py init` |
| `SPEC.md` | requirements as claim headings | `build`, `feature` (change spec; under 300 words at S), `move/refactor`, `move/upgrade` |
| `capability-map.md` | capabilities and their build order, which becomes the wave order | `build`, and a `feature` that bundles capabilities |
| `DESIGN.md`, `TESTPLAN.md` | design, contracts, decision index; claim to test mapping and kindness ledger | `build`, a large `feature`, `move`; TESTPLAN.md also at S once a test double is on a claim's path |
| `RESEARCH.md`, `research/probes/` | research ledger; committed probes | any run with a research phase |
| `content-plan/` | positioning, site map, and page briefs | `publish` |
| `HUNT.md` | brief, repro, pre-fix commit, hypothesis ledger, post-mortem | `fix` |
| `MIGRATION.md` | charter, invariants, consumers, parity, stages, undo ledger | `move/migration` |
| `how-it-works.md` | archaeology note with the drift table | `existing-code` at M and above; at S the findings go to Verified facts |
| `REPORT.md` | the final report | every run above XS, at the end |
| `handoffs/<unit>.md` | verifier handoffs from `templates/handoff.md`; `<unit>` is a STATUS key or a package id | every verification round |
| `rubrics/<shape>.md`, `rubrics/ui.md` | the frozen rubric; the UI rubric, built from `references/ui-verification.md` section 11 | every verification round; `ui` |
| `packages/index.md`, `packages/<id>/brief.md`, `report.json` | the wave table; parallel work packages | runs that decompose |
| `proofs/<key>/proof.json`, `r<n>/` | manifest; per round `verdict.json`, `commands.log`, output, `shots/`, `live.md`, `findings.json`; a package verdict uses the package id as its key | every claim that reaches Local Proof |
| `reviews/` | review verdicts (`<date>-<slug>.md` or `.json`), the final audit `<date>-final-audit.json`, citation checks `<date>-citations-<slug>.json`, disputes `<date>-dispute-<key>.md`, and the retro `<date>-retro.md` | every review, dispute, and retro |
| `investigations/<date>-<slug>.md`, `.patch` | failure records; a test or fix an investigator saved as a patch | every failure event |
| `runs/<date>-<slug>/` | a paused run for a different goal, with its RESTORE.md | section 14 |

The UI design contract lives with the product in `design/`, including `design/images/`, never in
`.drive/`. Nothing the owner reads uses opaque numbers. A claim's key is the slug of its words
(`deleting-the-account-removes-every-photo`); failures, decisions, investigations, and lessons are
keyed by date plus slug, and prose refers to things by their words.

**The provenance ledger** lives outside `.drive/`, where neither a subagent nor a main-thread tool
call may write. Its file is `<base>/<repository key>/ledger.jsonl`, where the repository key is the
sha256 of the repository root's real path. Writers use `${CLAUDE_PLUGIN_DATA}/ledger` when that
variable is set (hooks get it; a Bash call may not), else the first existing
`~/.claude/plugins/data/drive*/ledger`, else `~/.claude/drive/ledger`; readers merge every one of
them. Only drive's hooks and `drive.py` append to it: a record of every `drive:` subagent start; for
each reviewing agent that stops (verifier, grader, UI reviewer, auditor, security reviewer), the
sha256 of each JSON file under `.drive/proofs/` and `.drive/reviews/` that changed during its review
and that its own transcript (the SubagentStop input's `agent_transcript_path`) shows a successful
tool call writing, with its agent id and type and that transcript's path, sha256, and size, and a
record of its voided review window when there is one; every commit a main-thread Bash call made;
every path the main thread or a non-reviewing agent wrote with Edit, Write, NotebookEdit, or
MultiEdit, and, while a reviewer runs, every path outside `.drive/` that a Bash or PowerShell call of
theirs changed; each full-suite and registry run `drive.py lint` made, with its exit code, against the
latest code commit (recorded only while nothing outside `.drive/` is uncommitted); every `freeze add`,
park, unpark, and amendment; each `drive.py preflight` result; a stall the Stop gate set, and a turn
Claude Code ended at its Stop hook block cap; and the run's end.

An evidence entry counts only when its transcript is still a Claude Code transcript under
`~/.claude/projects` (or `$CLAUDE_CONFIG_DIR/projects`), belongs to the recorded agent type, still
begins with the bytes it held when the entry was recorded, and contains the write; the lint re-checks
each of these, so a hand-appended entry, or a hook command run without such a transcript, never
counts. A write is a Write or Edit call whose `file_path` resolves to the file, or a Bash or
PowerShell command that names the file by its repository-relative path
(`.drive/proofs/<key>/r<n>/verdict.json`), that path with `./` in front, or its absolute path. A
command that runs `cd .drive/proofs/<key>/r<n>` and then writes `verdict.json` names none of these,
so the file has no provenance: reviewers write evidence from the repository root with the full path
in the command.

**Transcripts expire.** Claude Code deletes session transcripts, and the subagent transcripts stored
with them, after `cleanupPeriodDays`, 30 days by default. From then on every verdict, final audit, live
proof, citation check, and refutation that a deleted transcript backed stops counting, the lint says
the transcript no longer exists, and the rows it supported fall to the rung their other evidence
holds. The setting in the run's own `--settings` covers only that session, and the run never edits
settings files. For a run that may last longer than the period, name raising `cleanupPeriodDays` in
the owner's user settings (`~/.claude/settings.json`) under "Needed from you" at intake, and before
`lint --final` spawn a fresh reviewer for every piece of evidence the lint reports with a missing
transcript.

**What the guard and the ledger can and cannot do.** Drive's hooks run as the same user, in the same
shell, as the session they watch, so no command filter can prevent deliberate tampering. The guard
refuses the plain forms of the mistakes a run is likely to make, such as writing under
`~/.claude/drive/`, `~/.claude/plugins/data/`, or `${CLAUDE_PLUGIN_DATA}`, writing a Claude Code
transcript, running a `drive.py hook-*` command by hand, writing a verdict, or, while a run is active, deleting, moving, or overwriting `.drive/local/active` or `baseline.json` (with `rm`, `mv`, `cp` or `tee` onto them, a `>` redirect, `find ... -delete`, `rsync --delete` into a folder holding them, inline code that calls a delete such as `os.remove`, `shutil.rmtree`, `Path(...).unlink`, or `fs.rmSync` on them or on `.drive/local`, or the Write, Edit, MultiEdit, and NotebookEdit tools, for every role and the main thread; reading them stays allowed) or running `git clean` with `x` or `X` in any flag cluster inside the project other than as a dry run, so that an honest mistake or a shortcut fails loudly. A command
written to hide what it touches can still get past it. The ledger makes that evident afterwards:
evidence without a matching reviewer transcript does not count, and the final audit reports it.
Neither the guard nor the ledger makes forgery impossible.

**Public repositories.** At intake, run `drive.py visibility` (add `--root <dir>` for another
directory). It prints `PUBLIC` or `PRIVATE` on its first line and the reason on its second, and
always exits 0, so read the first line. It prints `PRIVATE` only when the repository has no `origin`
remote or its origin is a local path, `gh repo view` reports it private or internal, or an
unauthenticated request says so (GitHub's page returns 404, or another host refuses an anonymous
`git ls-remote`). Anything it cannot establish, including a missing or signed-out `gh`, counts as
`PUBLIC`, and `drive.py capabilities` records the same answer as `git:visibility`. When it
prints `PUBLIC`, commit only GOAL.md, STATE.md, STATUS.md, DECISIONS.md, and REPORT.md, because
proofs, screenshots, reviews, investigations, and research notes expose internal detail. Add these
lines to `.gitignore` in the intake commit and record the choice in DECISIONS.md:

```
.drive/*
!.drive/GOAL.md
!.drive/STATE.md
!.drive/STATUS.md
!.drive/DECISIONS.md
!.drive/REPORT.md
```

The ignored files stay on disk, so evidence tokens still resolve for the lint and the final audit,
and REPORT.md says that the evidence lives only in this checkout.

## 3. One writer

Every file has exactly one writer at a time, so there is never a concurrent edit to reconcile.

| Files | Writer |
|---|---|
| GOAL.md, STATE.md, STATUS.md, DECISIONS.md, LESSONS.md, CONSTRAINTS.md, REPORT.md | the orchestrator only |
| SPEC.md, DESIGN.md, TESTPLAN.md | `drive:architect` during its phase; the orchestrator afterwards |
| RESEARCH.md | the one researcher the brief assigns; parallel lanes write their own report files and the reconciling agent merges |
| HUNT.md | the role `references/shapes/fix.md` names for each section, one at a time: the orchestrator for Brief, Mitigation, and Post-mortem; `drive:researcher` lanes for Since, Prior, Harness, and the plug lines; `drive:investigator` for Reproduction and the Hypothesis ledger; `drive:implementer` for Fix |
| `investigations/` | `drive:investigator` for the record it was given |
| `packages/<id>/report.json`, `local/workers/<name>/report.md` | the maker of that package |
| `proofs/<key>/r<n>/` | the agent working that round, through Bash: the verifier writes its command output and its own `verdict.json`, the severe tester and ui-reviewer their files; `proof.json` names `verifier` or `ui-reviewer` as `produced_by`, never the orchestrator. The orchestrator reads a verdict and never writes or edits one: the guard refuses the main thread, and any subagent outside drive's roster, every JSON file under `.drive/proofs/` and `.drive/reviews/`, any `verdict.json` or `proof.json` under `.drive/`, anything under `.drive/local/ro/`, and the ledger, and refuses them deleting or moving anything under `.drive/proofs/`, `.drive/reviews/`, or `.drive/local/ro/`; the lint accepts only files whose hash the ledger recorded from a reviewer of the right type whose transcript shows the write |
| `reviews/` | the agent whose brief names the file: the auditor, the security reviewer (no file at XS), the grader, a fresh verifier running a final-audit checklist or close check, or a ui-reviewer running a close check; the final audit and citation checks are bound to the ledger like verdicts; the orchestrator writes only Markdown there: dispute files, dispositions, re-grade comparisons, panel results, and the retro |

The lint counts each kind of evidence only from these agent types: a verdict from `drive:verifier`
or `drive:ui-reviewer`; a final audit from `drive:auditor` or `drive:verifier`; a live proof from
`drive:verifier` or `drive:ui-reviewer`; a citation check from `drive:grader`; and a refutation of a
verdict's blocking gap from a `drive:verifier` other than the agent that wrote the verdict.

A review is voided, never blocked. When `drive:verifier`, `drive:grader`, `drive:ui-reviewer`,
`drive:auditor`, or `drive:security-reviewer` stops, the SubagentStop hook
compares HEAD and every tracked path with uncommitted changes outside `.drive/` with what it recorded
when the agent started, and voids the review in exactly two cases. The first is a tracked file
outside `.drive/` modified or deleted in that window when no hook recorded that path as an edit since
the window opened. The hooks record every Edit, Write, NotebookEdit, and MultiEdit call by the main
thread or a non-reviewing agent, and, while a reviewer runs, the paths a Bash or PowerShell call by
either changed before that call returned. So your `.drive/` edits, your and the makers' recorded tool
calls, and a tracked file dirty at the start that you commit unchanged do not void a review; a change
no such call recorded does: a background command, dev server, or watcher still writing after its
call returned, another session or process, or the reviewer's own writes to tracked files. The second
is HEAD rewritten, so that the old HEAD is no longer an ancestor, or moved by commits the main thread
did not make, apart from commits that touch only `.drive/`. Untracked files that appear, change, or go
away in the window never void it, and neither does staging one (`git add` of a file that was untracked
at the start), while removing a tracked file from the index (`git rm --cached`) counts as a deletion.
The hook logs untracked files in `gate.log` as
`SNAPSHOT NOTE <role> <agent>: untracked path(s) ...`, and `lint --stop` and `--final` report any the
run leaves uncommitted. On a void the hook logs `SNAPSHOT VOID` with the changed paths in `gate.log`
and writes `.drive/local/ro/<agent>.void` and a ledger entry, the reviewer is never told to revert
anything, and the lint refuses, naming the changed paths, every evidence file that agent wrote and
every evidence file modified inside that window. Re-run the review on a still tree. When the start snapshot did not finish (the hook
timed out), the review is logged as not judged for tree changes; files past 5,000, larger than 8 MB,
or reached after the snapshot's time budget are compared by size and modification time instead of
content.

Workers report and the orchestrator writes. A worker that believes a state file is wrong says so
in its report. A subagent diff touching a file it does not own is drift: save it, revert it, and
record it. Long-running workers write their report file as they go, so an interrupted worker still
leaves something to reconcile.

## 4. Content rules

- **Nothing git already says.** Never record which files changed, what a function does, or what
  happened in what order. State files hold what a fresh context cannot derive: the next action,
  checked facts, rules in force, open failures, and decisions.
- **Facts name their check.** Every Verified fact ends with how and when it was checked. A fact you
  cannot check is a hypothesis: write it under Open failures with a repro, or not at all.
- **Claims, not tasks.** Every STATUS row is a behavioural sentence a test could refute, named
  before the code exists. "An expired token is rejected with 401" is a claim; "Implement token
  expiry" is a task and does not belong in the table.
- **Evidence per rung.** A row's status is the weakest rung its evidence supports (section 7). Only
  a verifier's verdict, or the ui-reviewer's for `[ui]` evidence, moves a row to Local Proof or
  above. Local-only work is never Live Proof.
- **Rows never disappear.** A claim that proves wrong or out of scope becomes Dropped with `why:`.
  Demoting a row after a failed review is the gate working; deleting one is never allowed.
- **Targets are fixed at intake.** GOAL.md is committed before any other work, and each row's
  `live` value is fixed when the row is created. Lowering a target (`live` y to n, a row Dropped, a
  phase removed) needs a DECISIONS.md entry in the same commit. The final audit compares the intake
  commit of GOAL.md with the final STATUS and lists every narrowing.

## 5. GOAL.md

```markdown
# GOAL · <goal slug>
goal: "<verbatim prompt>"
live means: <what live is for this project, decided at intake>
budget: <turns, subagents, wall clock, usd envelope>

## Restate
outcome: / user: / why now: / success: / constraints: / out of scope:   (one line each)

## Classification
(yaml: shape, variant, size, size_set_by, traits confirmed and suspected, probe with repo, stacks,
baseline_sha, the exact build, focused-test, and full-suite commands, claude_md; assumptions with
overturned_by; not_asked with the default taken; classified_at; reclassifications)

## Plan
- [ ] <phase> · artifact: <path> · exit: <checkable condition> · checker: <orchestrator | any roster agent name>

## Re-plans
- <ISO date> · <what changed> · <phases re-derived>
```

Each restate line is quoted from the goal or marked `assumption:`. Phase names come from this list
and no other: `intake`, `archaeology`, `research`, `spec`, `design`, `test-plan`, `decompose`,
`build`, `verify`, `integrate`, `live-proof`, `harden`, `docs`, `retro`, `report`; and, by shape,
`reproduce`, `diagnose`, `fix`; `inventory`, `characterize`, `cutover`, `soak`, `decommission`;
`content-plan`, `draft`, `design-qa`, `deploy`; `plan`, `execute`, `observe`. A `fix/incident`
mitigates in an `execute` phase before `archaeology`; `mitigate` is not a phase. A checker is
`orchestrator` or any roster agent's name, with or without the `drive:` prefix. An `operate` step
names itself in words between the phase and `artifact:`
(`- [ ] execute · rotate the api key · artifact: … · exit: … · checker: orchestrator`), as
`references/shapes/operate.md` shows. Sub-goals get `## Classification · <slug>` and
`## Plan · <slug>` sections in the one GOAL.md, and each of their STATUS rows carries a `sub:<slug>`
token (section 7). In the probe, `none` means the project has no such command, and
`test_command: none` means it has no suite. After intake GOAL.md changes only by ticking plan lines,
appending to `reclassifications`, appending Re-plans, and replacing a probe command, which needs a
DECISIONS.md entry naming the new one; the goal line and the restate block never change.

## 6. STATE.md

```markdown
# STATE · <project> · <goal slug>
status: running
phase: <phase>
next: <one imperative sentence>
updated: <ISO UTC>
commit: <short sha>
session: <session id>
model: <model · effort actually running>

## Resume here
Why: <one sentence>
Blocked on: none | <the single thing, who can unblock it, the default being taken meanwhile>
In flight: none | <agent> → <unit> (report at .drive/local/workers/<name>/report.md)

## Verified facts
- <fact>. Verified: <command or source and date>.

## Rules in force
- <project rule>. Because: <reason>. From: <investigation or decision slug>.

## Open failures
- <date> <slug>: <symptom>. Repro: <path or command> | Observed: <n of m runs>. Next: <step>.

## Discoveries
- <date> · <file or area> · <problem noticed and not touched, or a premise that changed> · <reason>

## Workaround ledger
| obstacle | workaround | by | when | count |

## Boundary events
- <ISO> · <step> · <classifier category or tool refusal> · <action taken> · <result>
```

`status` is one of `running`, `verifying`, `blocked`, `stalled`, `done`, `stopped`, `aborted`.
`running` and `verifying` keep the Stop gate closed, and no other status opens it by being declared:
`done` and `stopped` need `lint --final` to pass; `blocked` needs the Blocked on line to begin with
one of `budget:`, `impossible:`, `destructive:`, `credentials:`, `payment:`, `legal:`, `account:`,
`two-diagnoses:`, or `soak:` followed by the condition in words (the stop conditions in SKILL.md
section 9), and REPORT.md to say "Stopped because", where `budget:` counts only once maker spawns
reached the subagent figure on GOAL.md's budget line or a DECISIONS.md entry added since intake has a `Decision:` line that begins with `Stop` or `Narrow` and names the budget (an entry counts as added when its heading and body were not at intake, so a reused heading still counts), and `credentials:` must name
the secret as an uppercase identifier containing an underscore or ending in `TOKEN`, `KEY`, `SECRET`, `PASSWORD`, `PAT`, `CREDENTIALS`, or `CERT` (`credentials: CLOUDFLARE_API_TOKEN`), or as a name of two or more letters in backquotes or double quotes, so `credentials: none`, `TBD`, `TODO`, `N/A`, and `UNKNOWN` are refused; or the Blocked on line to begin
`launch preflight:` and quote the `claude` relaunch command in backticks or quotes, which counts only
when the latest `drive.py preflight` the ledger records for this session failed; `aborted` needs
REPORT.md and a DECISIONS.md entry whose `Decision:` line begins with `Abort` or `Aborted`, in any case, followed by `;`, `:`, a comma, a period, or the end of the line (as in
`Decision: Abort; the owner cancelled the run`; `Abort not needed` and a line that only mentions aborting do not count); `stalled`
counts only when the Stop gate set it. A status that was `blocked` at HEAD becomes `running` or
`verifying` only with a new DECISIONS.md entry naming the evidence that the condition cleared, and
one that was `stalled` at HEAD never does: further work is a new run. `done` means every row is Done or Dropped. `stopped` means the
run ended short of Done for a stop condition, every piece of work that did not depend on the blocker
is finished, and REPORT.md opens with "Stopped because"; `references/definition-of-done.md` section 4
lists what `lint --final` asks of it. `drive.py end` closes `done`, `stopped`, and `aborted`, and
closes `blocked` and `stalled` as stopped once the gate's conditions for them hold and the
`lint --stop` hygiene checks pass, so STATE.md and REPORT.md are committed first. "In flight" names each `drive:` agent with its unit and report path, and each
background shell, monitor, or workflow by its task id or its whole command, because the Stop gate
matches only those; a description or a name does not count. `session:` holds
the session id (from `.drive/local/session.json`, or what `claude --bg` printed) and may add the
name after it, because resuming a background session by name starts a copy. Add `registry: <command>` to the header when section 14 applies. STATE.md is rewritten, not appended: a closed failure leaves, and its investigation record
keeps the story. Record a missing capability once, as a Verified fact whose check is the preflight.
Workers' `noticed_not_touched` and `concerns` go under Discoveries.

## 7. STATUS.md

```markdown
# STATUS · <project>
ladder: Missing → Scaffold → Partial → Local Proof → Live Proof → Operational → Done   (Dropped needs why:)

| key | claim | live | status | evidence | updated |
|-----|-------|------|--------|----------|---------|
| expired-token-is-rejected | An expired token is rejected with 401 and creates no session | y | Local Proof | test:api/tests/auth.test.ts::expired token is rejected; severe:api/tests/severe_auth.test.ts::forged expiry is rejected; verdict:.drive/proofs/expired-token-is-rejected/r2/verdict.json; commit:4f2a9c1 | 2026-09-14 |
```

Evidence tokens, separated by `; `: `test:<path>::<name>`, `severe:<path>::<name>`,
`verdict:<path>`, `proof:<dir>`, `shot:<path>`, `live:<dir>`, `ops:<url or path>`, `review:<path>`,
`commit:<sha>`, `doc:<path>`, `why:<text>`, `planned:<path>::<name>` (only before the build
phase), and `sub:<slug>`, which names the sub-goal a row belongs to when GOAL.md has sub-goals, so
that `drive.py lint --gate <phase> --sub <slug>` checks only that sub-goal's rows. `[ui]` at the
start of a claim marks a UI row.

| Rung | Evidence required |
|---|---|
| Missing | nothing |
| Scaffold | `commit:` |
| Partial | `commit:` and at least one `test:` |
| Local Proof | the Partial set, `severe:`, and a `verdict:` that passes the checks in section 9 and supports at least Local Proof; `shot:` naming a screenshot too for `[ui]` rows |
| Live Proof | the Local Proof set with a verdict supporting Live Proof, plus `live:` whose `proof.json` passes the checks in section 9 |
| Operational | the Live Proof set with a verdict supporting Operational, plus `ops:` |
| Done | the Local Proof set plus `review:` naming the final audit, and `doc:` when user-facing behaviour changed (a warning when missing); with live `y`, also `live:` and a verdict supporting Live Proof; never a row carrying `why:device-only:` |
| Dropped | `why:` |

Write a proof's evidence file before quoting it in a row. Every `proof.json` answers in
`shim_differences` where the harness is kinder than production; an empty answer needs a note
saying why no double is involved.

## 8. DECISIONS.md and project LESSONS.md

```markdown
# DECISIONS · <project>

## <date> · <the decision in plain words>
- Context: <what forced a choice; claim keys involved>
- Decision: <what was chosen>
- Rejected: <each alternative and why it lost>
- Undo: <exact command or steps> · reversal cost: <low | medium | high, and what it costs>
- Evidence: <tokens, or none>
- Narrows: none | <live y→n on <key> | <key> Dropped | phase <phase> removed>
```

DECISIONS.md is append-only; a reversal is a new entry naming the one it reverses. An auditor
ruling on a dispute, the default applied for the single question, and a paused run (with the
restore as its Undo) are each recorded as entries. Project LESSONS.md uses `templates/lesson.md`;
its entries may name this project's files, because they never leave it. Its cap and routing are in
`references/lessons.md`.

## 9. What the lint enforces

`drive.py lint` runs with `--gate <phase>` at every gate, `--stop` from the Stop hook, and
`--final` before the run ends `done` or `stopped`; `--json` gives machine output. It prints one plain line per
finding and exits 1 on any failure. Fix what it reports; never edit a file to hide a finding.

| Scope | Checks |
|---|---|
| GOAL.md | header fields; classification parses with vocabulary values; every plan line names a canonical phase, an artifact, an exit, and a checker that is `orchestrator` or a roster agent name; a `drive(intake): <slug>` commit exists, and GOAL.md was committed before any other file of the run |
| STATE.md | header fields; `status` in the vocabulary; canonical `phase`; non-empty `next`; `updated` parses and is not older than the latest commit touching anything outside `.drive/`; `commit` exists and is an ancestor of HEAD; `Verified:` on every fact; `Because:` and `From:` on every rule; date, slug, and `Repro:` or `Observed:` on every open failure; 150 lines and 12,000 bytes at most; a status that was `blocked` at HEAD and is `running` or `verifying` now needs a DECISIONS.md entry added since HEAD, and one that was `stalled` at HEAD may not become either |
| STATUS.md | table parses; slug keys; `live` y or n; status a ladder word or Dropped; `updated` not in the future; tokens match the grammar; each rung has its evidence; `test:` and `severe:` files exist and contain the name, except a citation check's `test:` file under `.drive/reviews/`, which is JSON and must parse; a Done row's `review:` points at the final audit; `commit:` shas and paths exist; `verdict:` files say pass, match a ledger entry backed by the transcript of a reviewer of the right type, and were not written in a voided review window; a `verdict:` counts only when it records pass, covers the key as `unit` or a claim id, lists at least one command at exit 0 including the full-suite command unless there is no suite to show (the probe's full-suite command is `none`, or every shape in scope is `report` or `operate`, where a row's `sub:` token narrows the scope to that sub-goal's classification and its own probe command when it records one), has every claim `holds` at confidence 75 or more with a refutation attempt, has no unrefuted blocking gap and no unresolved `blocking` or `should_fix` harness kindness, supports at least Local Proof, is the latest round, and matches a ledger hash from a reviewer of the right type outside any voided window (a `fail` whose every blocking gap another verifier refuted counts as a pass); the best counting verdict's `rung_supported`, taking a claim's own value for the key over the verdict's and reading Done as Operational, reaches Live Proof or Operational for rows at those rungs, Live Proof for a Done row with live `y`, and Local Proof otherwise; a `live:` `proof.json` has `environment` `live` or `device` (a `live` target that is not a local address), the row's key, verdict pass, a `shim_differences` list (an empty one needs `shim_differences_note`), `commands` with exit codes, `artifacts` whose files exist beside it and match their recorded sha256, a commit that exists, `verifier` or `ui-reviewer` as `produced_by`, and a matching ledger hash; `shot:` names an image; `sub:` names a `## Classification · <slug>` section in GOAL.md; `planned:` only before the build gate; every key that appeared in STATUS.md at any commit since the intake commit is still present; a `live` flip from y to n, a new Dropped row, or a phase removed from GOAL.md's plan, compared with HEAD and at `--final` also with the intake commit, needs DECISIONS.md text added since that commit naming the key or the phase (write it on the entry's `Narrows:` line); warnings for claims opening with a work verb and for one test as the only evidence of more than five rows |
| Frozen tests | at every lint, when `.drive/frozen.txt` or `.drive/frozen.sha256` exists, every problem `drive.py freeze check` reports without `--base` (`references/testing.md` section 9) |
| Constraints floor | at `--gate integrate`, `--gate harden`, and `--final`, `drive.py guard` against GOAL.md's `baseline_sha` (else HEAD); every violation, and a guard that could not run, is a failure |
| Registry | when STATE.md names `registry:`, that command runs and must exit 0 at every `--gate` and at `--final` |
| `--gate <phase>` adds | that phase's exit criteria: for example `capabilities.json` at intake for M and above, `how-it-works.md` with a drift table at archaeology, a `test:`, `severe:`, or `planned:` token on every row at test-plan, disjoint ownership at decompose, every active row at Partial after build, fix, draft, or execute and at Local Proof after verify, harden, design-qa, and integrate, and live rows at Live Proof after live-proof, deploy, and cutover (a `why:device-only:` row at Local Proof); integrate also runs the `--stop` hygiene checks; `--sub <slug>` checks only the rows carrying `sub:<slug>` and takes the size from that sub-goal's classification |
| GOAL.md budget | at every gate, the maker subagent starts (`drive:implementer`, `drive:writer`, `drive:designer`, `drive:architect`, `drive:researcher`) the ledger recorded since `init`, counted against the number before `subagents` on the budget line; reviewer starts are reported and never counted: a warning past the count, a failure past twice it until a DECISIONS.md entry that mentions the budget, an overrun, or the envelope carries a `Narrows:` line other than `none` naming what was cut |
| DECISIONS.md | no entry present at HEAD removed or altered; Decision and Undo on every entry |
| `.drive/` outside `local/` | no secret-shaped string (`sk-`, `ghp_`, `AKIA`, `-----BEGIN`, a long bearer token) |
| `--stop` adds | no uncommitted or untracked path outside `.drive/local/` that `.drive/local/baseline.json` neither lists nor holds under one of its untracked directories (with no baseline, every such path fails, `.drive/` state files included); `.gitignore` ignores `.drive/local/`; no linked worktree and no local branch the baseline does not list, a `worktree-*` branch that a background worktree created included (with no baseline, any `drive/*`, `pkg/*`, or `worktree-*` branch fails); no `.drive/local/workers/*/report.md` newer than `updated` |
| `--final` adds | `status` is `done` or `stopped`; with `done`, every row Done or Dropped; with `stopped`, every row below Done carries its reason (a `why:` token, an Open failure or the Blocked on line naming its key, or a DECISIONS.md `Narrows:` line naming it) and REPORT.md's Outcome opens with "Stopped because"; either way REPORT.md exists and its rung counts equal STATUS's, any Done row needs a go in `.drive/reviews/<date>-final-audit.json` no older than the last code commit and matching a ledger hash from `drive:auditor` or `drive:verifier`, a `stopped` run with any row above Missing needs that same transcript-backed go, a no-go never satisfying it (a run with no rows, or every row at Missing or Dropped, needs none), no investigation is open, `.drive/reviews/<date>-retro.md` exists, every plan line is ticked or marked `[-]` unless the run is `stopped`, and the full-suite command from GOAL.md's probe runs once within `--suite-timeout` seconds (default 1800), exits 0, and is recorded in the ledger against the latest code commit; `report` and `operate` runs, and a probe whose `test_command` is `none`, have no suite and skip that run; a command changed since the intake commit, a `none` replaced by a real command included, needs a DECISIONS.md entry naming the new one; and when a line of DECISIONS.md, STATE.md, or MIGRATION.md records a scheduled deletion, REPORT.md's "Needed from you" names the deletion as the owner's step, because `drive.py end` leaves every hook inert and a scheduled deletion would run unguarded (otherwise keep the run open with `Blocked on: soak: <window>` until the deletion check has run) |

When evidence is unreachable, move the row down to the rung its reachable evidence supports.
The Stop hook runs `--final` without running any command, and reads the ledger's record of the last
full-suite run instead, so run `drive.py lint --final` yourself before setting `done` or `stopped`.
`drive.py end` closes a run, removing `.drive/local/active` and recording the end in the ledger, only
for these statuses: `done` or `stopped` when `lint --final` passes (it runs the suite, within
`--suite-timeout` seconds, default 1800); `aborted` when `lint --stop` passes, REPORT.md exists, and a
DECISIONS.md entry's `Decision:` line begins with `Abort` or `Aborted` (section 6); `blocked` when the Stop gate's
blocked conditions hold and the `lint --stop` hygiene checks pass; and `stalled` when the gate set that
status against the current STATE.md bytes, REPORT.md says "Stopped because", and the `lint --stop`
hygiene checks pass. It records `blocked` and `stalled` as stopped and
refuses every other status. Because `--final` and `--stop` both run the hygiene checks, commit
STATE.md, REPORT.md, and every other `.drive/` file before `lint --final` and `drive.py end`; an
uncommitted state file fails them. `drive.py lint` exits 1 on any failure, and 2 for an unknown phase or
`--sub` without `--gate`. The lint does not
read prose: whether a `doc:` file describes the behaviour, what a screenshot shows, or whether
`live.md` captured a real response is the final audit's to check.

## 10. Write before stopping

At every phase gate, in order: update the STATUS rows the phase touched, with evidence; rewrite
STATE.md (`phase`, `next`, `updated`, `commit`, facts verified, failures opened or closed); append
DECISIONS.md entries; run `drive.py lint --gate <phase>` and fix what it reports; commit naming the
phase and the claim keys.

Before ending any turn, `next` names the real next action, `updated` and `commit` are current,
every in-flight agent is listed with its report path, and the tree is committed. If you stop for
the one question, write it on the Blocked on line first. When the Stop hook blocks, do the recorded
`next` with tool calls, then update STATE.md; the gate's decision table and the rules against
escaping it are in `references/long-running.md`. Routine writes need no deliberation: update the
files, run the lint, commit, continue.

## 11. Read at start, resume, and in-flight work

At a fresh start and at every resume, read in this order, keeping the state files within about
6,000 tokens:

At a resume, first run `drive.py init --goal -` with GOAL.md's goal on stdin: it re-creates a missing
`.drive/local/active`, records this session so the Stop gate and the re-injection hook act in it, and
archives nothing.

1. `drive.py start`: STATE header and Resume here, rung counts, open rows, open failures, ledger
   rows at count two or more, lint findings. SKILL.md prints it at invocation; after compaction the
   SessionStart hook, `drive.py hook-reinject`, prints it again with SKILL.md's contract, standing
   rules, section 6, and section 7 to the end.
2. STATE.md in full, then GOAL.md in full.
3. `references/lessons/general.md` in full; the Learned constraints of each selected domain and of
   `references/capabilities.md`; `.drive/LESSONS.md` in full.
4. `git status --porcelain`, `git log --oneline -15`, `git worktree list`.
5. On demand only: other STATUS rows, the current phase's SPEC and DESIGN sections, RESEARCH
   entries a row cites, DECISIONS entries by slug. Open a `proof.json` only to refute or report.
   Never read logs or screenshots at start.

After compaction or resume the files win over any summary: if the summary says something is done
and STATUS does not, STATUS is right until you re-check the code. The full resume protocol,
including the smoke run before new work, is `references/long-running.md` section 8. Reconcile each
In flight line before anything else:

| What you find | What you do |
|---|---|
| a report newer than `updated` | merge it; rows move only on a verdict; carry `noticed_not_touched` and `concerns` into Discoveries; clear the line |
| no report, but owned paths changed or commits exist | the work died with the process: audit the paths, re-dispatch from the brief, which tells the maker to report work already present |
| a `partial` report | continue it once: resume the same agent with `SendMessage` while its id is still valid in this session (it keeps the cache), or re-dispatch from the brief after a resume or compaction; either counts as one workaround ledger row; a second partial means re-scope; a third attempt on the same brief is forbidden |
| a verifier with no verdict file | spawn a fresh verifier from the handoff; never infer a pass |
| a monitor, background poll, or self-paced loop | re-create it; a `CronCreate` task that `--resume` restored needs nothing |

Then set every affected row to the rung its evidence on disk supports. A point in the run is
resumable when HEAD, STATE.md, and STATUS.md agree.

## 12. The phase-handoff summary

A handoff is safe only at a finished unit of work. Before a phase boundary, a fresh session, or the
end of a headless leg, make the files carry these six things, and use the same six headings for any
summary you write in the conversation:

| Item | Where it lives |
|---|---|
| Difficulties met and how each was handled | investigation records; a DECISIONS entry when a choice resulted |
| Options raised, tried, or set aside, and why | `Rejected:` lines in DECISIONS.md; the attempt ledger in HUNT.md or RESEARCH.md |
| Everything decided or ruled out, exactly | DECISIONS.md, Verified facts, Rules in force |
| Where things stand | the STATE header, Resume here, STATUS rows, the commit |
| What is open | Open failures, Blocked on, open STATUS rows, Discoveries |
| Hard-to-reconstruct details: commands, shas, ids, versions, URLs | Verified facts with their checks, GOAL.md's probe, `proof.json` |

Record verification commands with their results and the commit they ran against. The next session
reads the files and the real `git status` first, re-runs any check whose baseline no longer matches
the code, and never assumes an approval or a passing result it cannot see in a file. A process
that exited is not evidence that anything passed.

## 13. Size control

- **STATE.md**, 150 lines and 12,000 bytes, whichever comes first: move closed failures out, delete facts the code now makes obvious, route
  general rules to lessons. Needing more means you are writing what git records.
- **STATUS.md** only grows. The start view shows open rows; grep a key for the rest.
- **DECISIONS.md, RESEARCH.md, HUNT.md** are ledgers: never trimmed. Sources stay; a superseded
  finding names its replacement; refuted hypotheses stay so nobody re-tests them.
- **LESSONS.md**, 40 entries; **how-it-works.md**, 150 lines.
- **proofs/**: screenshots downscaled to about 200 KB; larger logs go to `.drive/local/logs/` with
  their hash in `proof.json`.

Consolidate lightly at every phase gate (a minute of reading) and thoroughly at the retro, never
during build turns, when your context is full of code and generalizations are least reliable.

## 14. Precedence, registries, and paused runs

**Precedence.** When records disagree, trust working-tree code and tests, then proof artifacts,
then STATUS.md, then prose (STATE.md, SPEC.md, DESIGN.md, REPORT.md). Correct the lower record in
the same turn. A disagreement that shows a process failure, such as a Local Proof row whose named
test does not exist, is a failure event. Verifiers check STATUS against the code, never the reverse.

**Existing registry.** If the repository already has a requirements registry or status ladder with
its own gate, do not create a second. Write `registry: <command>` in STATE.md's header, reduce
STATUS.md to its header, `registry: <command>`, and one sentence saying where the claims live, and
the lint runs that command at every gate and at `lint --final`. The Stop hook runs no command,
because a hook cancelled at its timeout decides nothing and the stop would go through; it relies on
the result `lint --final` recorded. Claims are still named before
code and get refutation tests, recorded in the registry's format. Build no translation table
between vocabularies. The report quotes the registry's summary and says per claim, in plain words,
whether its proof is local or live.

**Paused runs.** If `.drive/` holds a run for a different goal, `drive.py init --size <size> --goal -`
moves the tracked state to `.drive/runs/<date>-<slug>/` with a RESTORE.md, parks its local files under
`.drive/local/archive/<date>-<slug>/`, and appends a DECISIONS.md entry whose Undo is the exact
restore. It commits nothing: the intake commit, `drive(intake): <slug>`, carries the move, the new
GOAL.md, and that entry together, so GOAL.md stays the new run's first commit. Never overwrite a paused
run and never ask. Name it in the final report. The same goal, however reworded, means resume:
compare the deliverable, not the wording, and record the judgement in DECISIONS.md. `init` recognises
the same goal only by goal text identical to the goal GOAL.md recorded at init (ignoring case and
spacing); the 50-character slug decides only for an older GOAL.md that records no goal text, so a
different goal that shares its opening archives the old run. For the same goal `init`
only re-creates a missing marker, records the session, and writes a missing baseline, with no `--size` needed; for a reworded goal pass it the goal quoted in
GOAL.md, never the new wording, or it archives the run.

## 15. The report

Write `.drive/REPORT.md` from `templates/REPORT.md`, derived from STATUS, STATE, DECISIONS,
LESSONS, the investigations, and the proofs, never from memory of the run. Sections: what is needed
from the owner, a short list in which each item names the default already applied and the command
that finishes it (a login, a secret to set, a team identifier, a push, a production promote), or
none; what to look at first (written last); what shipped, with rung and evidence; what is proven live versus only
locally, with the union of every `shim_differences` answer; what is not done and the exact step
that would finish each; decisions with their undo, including every narrowing since intake; open
failures with the command that would close each; lessons with commits, or "none" and why; commands
to verify from a clean checkout; any paused run; spend. A stopped run's report opens with
"Stopped because <reason>". Every statement cites a row, a file, or a proof. State nothing the lint would reject and describe no plan as a result. Mid-run, tell the
user one line per milestone: the phase that passed, the claims that moved, the evidence path.

## 16. Excuses and rebuttals

| Excuse | Why it fails |
|---|---|
| "I'll update STATE.md at the end of the phase." | Compaction or a process death can land first; the file is all that survives. |
| "The summary says the tests pass, so the row can move." | A summary is not evidence; only a verdict moves a row to Local Proof or above. |
| "This claim is out of scope; delete the row." | Mark it Dropped with `why:` and a DECISIONS entry in the same commit. |
| "Live proof is not feasible; set live to n." | The target was fixed at intake; lowering it is a decision the report lists. |
| "Letting the worker update STATUS is faster." | Two writers overwrite each other's edits, so workers report and you write. |
| "I'll note what I did this session for context." | `git log` says it. STATE.md holds the next action, checked facts, and open failures. |
| "This fact is obviously true." | Unverified guesses stated as facts are how long runs fail. Name the check. |
| "I remember where we were." | Your recollection did not survive compaction or resume; reconcile against files, git, and reports. |
| "The run fell short, so there is no honest status to end on." | `stopped`, with every row's reason recorded, is that status. A bare `blocked` no longer opens the Stop gate, and a run that never reaches `drive.py end` keeps its marker, so its hooks stay live in this repository. |
| "I'll write the verdict from what the verifier said." | No reviewer's transcript shows the write of a file you wrote, so the lint refuses it; spawn the reviewer again. |
| "The repo's registry is awkward; STATUS.md is easier." | Two registries for one truth drift apart. |

## 17. Red flags

- STATE.md `updated` is older than the last commit that touched code.
- A status word outside the ladder: implemented, drafted, wired, handled, in progress.
- STATUS.md has fewer keys than at HEAD or at the intake commit.
- A Verified fact lacks `Verified:`, or STATE.md passes 150 lines or narrates what happened.
- In flight names an agent with no report file and no recorded re-dispatch.
- A Live Proof row's manifest says `local` or `simulator`.
- `next` is a question for the owner, or "wait for" something a tool could trigger now.
- A subagent's diff touches STATE.md, STATUS.md, or DECISIONS.md.
- A `live` value changed or a row became Dropped without a DECISIONS.md change.
- REPORT.md's counts disagree with STATUS.md, or it mentions work with no row or file.
- STATE.md says `done` with a row below Done, or `stopped` with a row below Done that carries no reason.
- A plan line whose checker is neither `orchestrator` nor a roster agent name, or whose phase is not
  in the list in section 5.
- Proofs, reviews, or investigations committed in a public repository.
- A verdict, final audit, or live proof the lint reports as not matching the provenance ledger.
- A worktree, branch, or uncommitted path created during the run still present at a stop.
