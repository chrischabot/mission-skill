# 27 · Review: coverage of the owner's request and five simulated runs

Reviewer: independent, fresh context, read-only except for this file. Date 2026-09-14.

Read in full: `research/00-brief.md` (section 1 and the corrections), `research/24-synthesis.md`
(including amendments 15 to 19), `HANDOFF.md`, `README.md`, and under `skill/`: SKILL.md, all twelve
agent files, every reference (intake, the seven shapes, definition of done, spec, design, research,
testing, verification, UI verification, parallel, state files, lessons and the lessons store, long
running, models, safety, capabilities, and the Part B and relevant sections of the web domain;
section headings of the iOS and Cloudflare packs), and the templates that exist. Absent files were
not counted as findings: the plugin manifest, `hooks/hooks.json`, the core templates (GOAL, STATE,
STATUS, DECISIONS, REPORT, handoff, investigation, lesson, package brief and report, verdict schema),
and the hook subcommands of `drive.py`, which do not exist yet in the script. Where a finding depends
on how one of those will be written, it says so.

Facts checked rather than assumed:

- Hook placement, from https://code.claude.com/docs/en/hooks: handlers "run in the current directory
  with Claude Code's environment"; the input field `cwd` is the "Current working directory when the
  hook is invoked" and "follows Claude" after a `cd`; `${CLAUDE_PROJECT_DIR}` is "the project root
  where the session started" and stays put.
- `claude --help` on the installed 2.1.263 lists `--bg`, `--agent`, `--effort`,
  `--permission-prompts`, and `--settings`, so the launch recipes and the Opus 4.8 retry command are
  well formed.
- `drive.py`'s `find_root` resolves the run from `os.getcwd()` (nearest `.drive/`, else the git top
  level) for `start`, `init`, `end`, and `capabilities`.
- `drive.py lint --final` fails any STATUS row that is not Done or Dropped (line 2106), and
  `drive.py end` refuses unless `lint --final` passes or STATE says `aborted`.
- SKILL.md is 27,111 characters. At four characters per token, section 7 ("Failures and lessons")
  begins near token 5,100, section 9 ("Stopping and the report") near 5,900, and the standing-rules
  block near 6,300. Tables and backticked paths tokenise more densely than prose, so the real
  positions are later still. After auto-compaction only about the first 5,000 tokens come back.
- The two external reference paths named in `capabilities.md`
  (`~/.claude/skills/audit/references/audit-your-codebase.md` and
  `~/.claude/skills/google-dev-docs-style/references/review-checklist.md`) exist on this machine.
- No file in the skill mentions the fashion example by theme; the worked classifications are generic.

The skill as a whole is serious work and covers nearly everything the owner asked for. The findings
below concentrate on the places where a real run would stall, guess, or finish in a state the skill
has no word for. Three of them (where a run lives, how a run that falls short of Done ends, and what
survives compaction) affect every example, so they come first in the gap list.

## 1. Coverage of the owner's request

Verdicts: **Covered** means a reader following the named section would do what the owner asked.
**Partial** means covered with a gap that changes the outcome in some runs (the gap number points at
section 3). **Not covered** means no file says what to do.

| Request item | Where covered | Verdict |
|---|---|---|
| One invocation with a high-level goal drives the whole process to completion | SKILL.md §1 (contract), §2 (start or resume), §4 (phase loop), §9 (stop and report); Stop gate in frontmatter and `long-running.md` §5 | Partial: the run can start in the wrong repository (gap 1) and has no terminal state for an honest finish short of Done (gap 2) |
| Stages | SKILL.md §3 shape table; `references/shapes/*.md` phase tables with entry, work, artifact, exit, checker | Covered |
| Agent roles | SKILL.md §6 roster; `agents/*.md` with pinned model, effort, tools, boundaries, report shape | Covered |
| Steps in control (gates, who checks, loop bounds) | SKILL.md §4, §5; `verification.md` §5 and §6; `state-files.md` §10 | Covered; one checker assignment contradicts the grading tiers (gap 7) |
| Design (backend and frontend architecture) | `design.md` (sizing, DESIGN.md order, contract package, failure semantics, idempotency, frontend structure, review, pre-mortem); `agents/architect.md`, `agents/designer.md` | Covered |
| Implementation | `parallel.md` (packages, waves, maker rules, integration); `agents/implementer.md` | Covered |
| Research | `research.md`; `agents/researcher.md`; `shapes/report.md` research rules | Covered |
| Failure investigation | `lessons.md` §3 and §4; `agents/investigator.md`; `shapes/fix.md` diagnose | Covered |
| Recording state in STATE.md | `state-files.md` §6, §10, §11; SKILL.md §2 and §4 step 4 | Covered, subject to gap 3 after compaction |
| Compounding failures into general lessons | `lessons.md` §5 to §12; `references/lessons/general.md` seeded with six owner rules; SKILL.md §7 | Partial: the loop skips stopped runs, has conflicting triggers, and may be unable to commit (gap 5) |
| Tackling work with swarms | SKILL.md §6 parallel work; `parallel.md` §3, §4, §9, §13 (waves up to eight makers, Workflow for read-only fan-outs) | Covered |
| Clear, hard tests that measure real success without ballooning | `testing.md` §1 (tests refute claims), §2 (cheapest real layer), §3 (what not to test), §4 (budgets per shape), §14 (manual mutation) | Covered |
| How to test backend and frontend | `testing.md` §2 and §15; `domains/cloudflare.md` §9 and §10; `domains/ios.md` §7; `domains/web.md` Parts A and B | Covered |
| Verifying frontend layout, design quality, and UX | `ui-verification.md` (contract, state harness, capture matrix, objective checks, vision with calibration, walkthrough); `agents/ui-reviewer.md` | Covered; the iOS matrix is heavier than it needs to be (gap 12) and existing products get unrequested stamp code (gap 9) |
| Heavy adversarial review of everything | `verification.md` §5 layers; `agents/severe-tester.md`, `security-reviewer.md`, `verifier.md`, `auditor.md`; spec and design review in `spec.md` §12 and `design.md` §9; adversarial reader for reports | Partial: the classification itself, which every later step inherits, is never checked by anyone but its author (gap 11) |
| Which model does what (Fable orchestrates, Opus for hard bounded work, Sonnet for volume and at low effort as graders instead of Haiku) | `models.md` §2, §4, §5, §6; SKILL.md §6; agent frontmatter | Covered |
| Tracking in STATUS.md | `state-files.md` §7 and §9; `definition-of-done.md` §2 | Covered |
| Research tracking, including online search | `research.md` §5 (Tavily, WebSearch, raw-text quotation), §6 classes, §9 freshness; RESEARCH.md template | Covered |
| Conditionals for project shapes and scopes | SKILL.md §3 tables; `intake.md` §5 to §9 and §13; per-shape size tables; trait sections | Covered |
| Plain language without rule IDs | SKILL.md §9 report; `spec.md` §5 (no numbered codes); `state-files.md` §2 (keys are slugs of words) | Covered; the REPORT template, not yet written, must translate trait slugs and "kindness ledger" into words |
| No approval queues | SKILL.md §1 and §3 step 7; `intake.md` §12; `general.md` entry five; `lessons.md` §9 | Covered, with one leak: a deferred store deletion waits for a future run (gap 15) |
| No branches or worktrees left behind; commit to main | SKILL.md §1; `parallel.md` §11; `lint --stop` checks | Covered; wording conflicts with the owner's "current branch" rule (gap 19) |
| Never wait on a scheduler | SKILL.md §8; `long-running.md` §7 and §11; `general.md` entry two; `async-scheduled` trait | Covered |
| Anti-mirage completion with a status ladder and refutation tests | SKILL.md §5; `definition-of-done.md`; `testing.md` §1; lint evidence table | Covered, but see gap 2 on how the ladder and the lint interact at the end |
| Second time is the bug | SKILL.md §7; `lessons.md` §2; `general.md` entry three | Covered above XS; at XS there is no ledger (gap 6) |
| Start when invoked in an unrelated directory | `intake.md` §3 mentions looking under `~/Projects` when the directory is "empty or unrelated" | Not covered: nothing moves the run to the right repository or creates one (gap 1) |
| What happens at XS | SKILL.md §3 size table; `intake.md` §9; `definition-of-done.md` §2 commit-body form | Partial (gap 6) |
| How the run ends and what the owner sees | SKILL.md §9; `state-files.md` §15; `definition-of-done.md` §4 and §6 | Partial (gaps 2 and 18) |
| Whether the lessons loop actually fires | `lessons.md` §11 consult, §12 retro | Partial (gaps 3 and 5) |

## 2. The five examples, simulated

Each walkthrough follows the files in the order the skill tells the orchestrator to read them, and
records what it would do. The labels mean: **stuck** (no file says what to do next), **guess** (two
reasonable readings, no rule to choose), **contradiction** (two files give different instructions),
**skip** (something the owner asked for does not happen), **ceremony** (work that does not pay for
itself at this size).

### 2.1 Greenfield native iOS app with a Cloudflare backend, from a few paragraphs

Illustration only; nothing was built.

1. Invocation injects `drive.py start`. Suppose the owner types the command in whatever session is
   open, for example in `~/Projects/arcwell`. The start view prints "No drive run in
   /Users/chabotc/Projects/arcwell."
2. SKILL.md §2 step 2 sends it to intake, reading `general.md` in full first.
3. Intake §3 step 1 parses six slots; step 2 probes. The probe finds a repository (arcwell) with its
   own stacks. SKILL.md only says to look under `~/Projects` when the directory is *empty*;
   `intake.md` §3 adds "or unrelated" but gives no test for unrelated and no action once the search
   finds nothing. **Stuck, then guess.** The likeliest reading is "no repository hosts this, so it is
   a build here", and `drive.py init` would create `.drive/` inside arcwell and commit
   `drive(intake): …` to arcwell's main. The iOS project and Workers would then be scaffolded inside
   another product's repository. This is gap 1.
4. Suppose instead the owner started in an empty `~/Projects/<new>`. `init` refuses a non-git
   directory ("is not a git repository"), and no file says to run `git init`. **Stuck** (gap 1 again).
5. Shape `build`, size XL, traits as in `intake.md` §14. `capabilities` runs; in a background or
   headless session the Simulator MCP is absent and the iOS pack's `xcodebuild` and `simctl` fallback
   applies. This part reads well.
6. Plan: capability map, research lanes, spec by the architect with auditor review, design and
   design contract, test plan, decompose, wave 0 with a walking skeleton deployed live.
7. Test plan exit: `build.md` names `drive:grader` as the checker for "one refutation test per claim
   at the cheapest real layer". `models.md` §5 says a tier-two judgment must never go to the grader.
   **Contradiction** (gap 7).
8. Wave 0 live skeleton: deploying needs an authenticated `wrangler` and an Apple team for signing
   beyond the simulator. If Cloudflare is not logged in, the skill says to name the secret under
   "Blocked on", but `build.md` does not say whether waves 1 and later proceed against the local
   runtime or the run stops. **Guess** (gap 17). Proceeding is clearly right, since `workerd` is the
   real runtime locally, but the skill should say so and cap the rows.
9. UI verification per primary screen: three device roles, two schemes, two text sizes, and every
   declared state (six in the vocabulary), with at least five observations per cell. That is up to
   72 cells and 360 observations per primary screen, per round, for three rounds. **Ceremony**
   (gap 12): most cells differ from their neighbours only in ways the objective checks already
   measure.
10. Harden, docs, retro, final audit by the auditor.
11. End: any claim that needs a physical device (push delivery, camera) is "never Done" by
    `definition-of-done.md` §2. `lint --final` then fails, so `status: done` is impossible, and
    `drive.py end` refuses unless `aborted`, which is reserved for the owner stopping the run or an
    auditor ruling it impossible. **Stuck at the very end** (gap 2). The honest outcome of a
    successful native app run has no status.
12. Compaction: a multi-day XL run compacts several times. After each, sections 7 to 9 of SKILL.md,
    the standing rules, and the reference index are gone from context; the re-injected start view
    carries none of them. The orchestrator no longer has the list of which reference to read when,
    or the stop and report procedure, unless it re-reads SKILL.md on its own (gap 3).

What the owner asked for that this run does deliver: the overarching spec, backend and frontend
design, end-to-end test strategy with a kindness ledger, UI quality verification, adversarial
review, model routing, STATUS and STATE tracking, research ledger with online search, and failure
investigation. The cost envelope in `models.md` ($400 to $600) is stated in GOAL.md rather than
queued for approval, which matches his rules.

### 2.2 "Find this deep annoying bug and fix it"

1. Start and intake as before; the run is in the right repository if the owner invoked it there.
2. Parse: "deep" and "annoying" set nothing, correctly. If the prompt carries a symptom, `fix.md`
   runs cleanly. If it does not (the example prompt names no symptom at all), the false-fix test in
   `intake.md` §5 cannot run, the HUNT brief's eight fields are all "unknown", and the single-question
   test forbids asking because every step is reversible. **Stuck** (gap 10): nothing tells the
   orchestrator where to look for the bug the owner means (failing CI runs, open issues, open failures
   recorded by earlier runs, error logs, the project's memory notes).
3. Shape `fix`, size M by unknowns. Files: GOAL, STATE, STATUS, HUNT, CONSTRAINTS, a narrowed
   `how-it-works.md`.
4. Archaeology by researcher lanes; reproduce with an investigator repro script and a severe tester's
   framework test written without seeing any fix. Good.
5. Diagnose with a hypothesis ledger and bisect in a detached worktree under `/private/tmp`, removed in
   the same step. Good, and consistent with the owner's worktree rule.
6. Verify: `fix.md` says to create a detached **worktree** at the pre-fix sha and copy the test in;
   `testing.md` §11 says the same; `agents/verifier.md` step 6, `agents/severe-tester.md` step 5,
   `definition-of-done.md` §3, and synthesis §19 items 16 and 17 say a **`git archive` copy, never a
   worktree**. **Contradiction** (gap 8), already noticed in the synthesis and still unfixed. Also,
   `fix.md` runs `/code-review high` while `verification.md` §5 says `medium` for `fix`. **Contradiction.**
7. Loop bound 2 rounds; a returning gap opens an investigation. Good.
8. If reproduction fails within budget, `fix.md` says to stop and report with no row above Partial.
   The run then cannot pass `lint --final` or `drive.py end` (gap 2 again).
9. Retro: SKILL.md §7 requires the retro "before Done". A stalled hunt, which is the case most likely
   to teach something, never reaches Done, and §9's stop procedure does not mention the retro.
   **Skip** (gap 5).
10. Failure events: SKILL.md §7 and `lessons.md` §1 count "a verifier rejection" as a failure event,
    which opens an investigation record. `verification.md` §6 sends a first rejection back to the
    maker and opens an investigation only when the same gap returns. **Contradiction** (gap 5); in a
    fix with two rounds this decides whether the run writes one extra investigation or none.

Ceremony at M looks proportionate for a bug that has resisted earlier attempts. At S the skill
already drops the severe tester's reproducer and CONSTRAINTS.md, which is right.

### 2.3 Add a new dashboard to an existing product

1. Start in the product repository; intake reads `intake.md`, `feature.md`, and `web.md` Part B.
2. Traits: `web.md` §1 lists `data` as a trait of every dashboard; `intake.md` §14 marks it suspected
   and refuted when no schema changes. **Contradiction**, minor (gap 21); the intake reading is better.
3. Archaeology with a full-suite baseline; change spec; design delta.
4. Design contract: the designer extracts the existing design system into `design/DESIGN.md` and
   `design/tokens.json` in the product repository. When the product already has a token source, this
   is a second copy of the same values that will drift. **Ceremony**, minor; the designer already
   cites file and line, so a pointer file would do.
5. Wave 0 for `ui`: `ui-verification.md` §3 makes a build stamp (`<meta name="build-hash">` and a
   `/__build` endpoint that ships to production) and a debug-only state harness wave 0 requirements
   with their own STATUS row. On an existing product that is new production behaviour the goal did not
   ask for, and `definition-of-done.md` §6 A blocks "unrequested behaviour shipped". **Contradiction**
   (gap 9): the final audit would reject what UI verification required.
6. Build, verify with `/code-review high`, conformance grader, severe tests including the access-test
   table, security review if a role is new, UI review against the exemplar screen, `/simplify`, docs.
   Proportionate for M.
7. Live proof: `web.md` §20 requires "a real account for each role" on staging. The skill's never tier
   forbids creating accounts and entering credentials, and no file says where role accounts come from
   (the product's seed command in a non-production environment, or variables the owner has set).
   **Stuck** at live proof (gap 9).
8. Done in `web.md` §20 requires `doc:` pointing at a published metric definitions page. For an
   internal admin dashboard the goal did not ask for one. **Ceremony**, minor; it should be a
   discovery unless the product already publishes metric definitions.
9. Final audit by the auditor when there are five or more claims, which a dashboard usually has.

### 2.4 Move an AI gateway from an external project into a core platform service

1. Start: the orchestrator must be launched in the platform repository, but nothing says which of
   the two repositories holds `.drive/`. The `multi-repo` trait section says the final git audit runs
   in every repository, and `move.md` has commits in both. The Stop gate, guards, and snapshot hooks
   look only at the session's current directory (verified hook behaviour) and subagents' shells start
   at the launch directory. **Guess** (gap 1): the run should live in the destination repository,
   and every command against the other repository must use `git -C` with an absolute path.
2. Shape `move/migration`, size L, taking the larger size as the rule says.
3. Inventory: consumers "from the old path's own access logs over at least one full cycle". If the
   external gateway does not log caller identity or keeps logs for less than a cycle, "Unknowns empty
   before the first weight step" cannot be met, and no file says to add identity logging first and
   keep building while it accumulates. **Stuck** (gap 16).
4. Characterize: a recorder deployed into the live gateway with its undo, redaction list before
   recording, recordings never committed. Well handled for a system whose traffic contains prompts.
5. Design: seam first, flag, parity on decisions, shadow the full path on a sample because upstream
   calls cost money. `cloudflare.md` §15 on service bindings applies. Good.
6. Cutover and soak: weights 0, 10, 50, 100, each soaked "one full periodicity cycle" (a week for
   daily or weekly traffic). With the inventory cycle, the run spans about four weeks of blocked
   status and scheduled checks. For a personal platform with a handful of owned callers this is
   **ceremony** that the owner's systems cannot repay, because a week of near-zero traffic at 10
   percent proves little (gap 16).
7. Decommission: store deletion after the rollback window becomes "a dated STATE.md line … which the
   next drive run in this repository performs at start". That is a queue waiting on a future
   invocation that may never come. **Contradiction** with the no-queues rule (gap 15).
8. End: while any soak is open nothing is Done; when the last soak closes, the scheduled check invokes
   `/drive --resume`. That works, provided the scheduled task lives in the Desktop app and the machine
   is awake, which `long-running.md` §11 states honestly.

### 2.5 Research market position; build a site about the project, goals, and team with blog and docs

1. Start: "our project" resolves to the current repository if the owner is in it. Whether the site
   lives in that repository (a `site/` directory) or in a new repository is not decided anywhere.
   **Guess**; a new repository runs into gap 1.
2. Shape `publish`, size L. `intake.md` §14 sets the size from "a research deliverable and a
   multi-section site", treating the research as something the owner receives. `publish.md` treats
   it as a gate before content planning, delivered only if it "must stand alone". **Contradiction**
   (gap 14); the owner's sentence ("research our market position, create a website") asks for both.
3. Research lanes including competitor, audience, and disconfirming lanes; grader re-opens citations.
   Good.
4. Content plan location: `publish.md` puts positioning, site map, and page briefs in SPEC.md;
   `spec.md` §2 names `templates/change-spec.md`; `intake.md` (prose-content) and synthesis §19 item 3
   put them in `.drive/content-plan/`. **Contradiction** (gap 13), three answers.
5. Team page: people only from supplied material or the repository. The goal supplies none, so the
   page is left out, which narrows a requested section; that needs a DECISIONS.md entry and a line in
   the report. The files support this reading, though no file says it for this case.
6. Build, draft, design QA with the full matrix and Lighthouse thresholds, claims lint wired into the
   site build. Proportionate at L.
7. Deploy: `publish.md` deploys to a preview and promotes to production only when the goal asks for
   the site to be live. Its live-proof phase and its Done paragraph accept the preview as live
   evidence. `definition-of-done.md` §2 and §3, `web.md` §12, and synthesis §19 item 4 say a preview is
   Local Proof. **Contradiction** (gap 4). Following the stricter files, rows created with `live: y`
   stop at Local Proof, the run cannot reach Done, and it cannot end (gap 2).
8. "Never publish on the owner's behalf" (SKILL.md §8, `intake.md` §12) sits uneasily next to a
   production deploy of a site that speaks for him and names his team. The skill needs one sentence
   saying which side wins (gap 4 recommends the preview default, fixed at intake).

## 3. Gaps, in priority order, with proposed fixes

Priority 0 stops or corrupts a run in ordinary use. Priority 1 produces a wrong or unfinishable
result in one of the example shapes. Priority 2 costs quality or money. Priority 3 is consistency.

### Gap 1 (P0). The run can start in the wrong repository, and nothing creates a new one

Evidence: SKILL.md §3 step 2 handles only an empty directory; `intake.md` §3 names "unrelated" with no
test and no action; `drive.py init` refuses a non-git directory and otherwise initialises wherever it
is run; no file mentions `git init`. Hooks run in the current directory and read `cwd`, which follows
`cd`, while subagent shells start at the launch directory, so a run whose root differs from the
session's directory has inert or misdirected gates and briefs whose relative commands run in the wrong
place.

Fix, SKILL.md §2, insert before step 1:

> 0. **Where the run lives.** A run lives in the repository this session was started in, because the
>    Stop gate, the guards, and every subagent's shell start there. Settle that first.
>    - With no goal and no `--resume`, say in one line that `/drive` needs a goal, and stop.
>    - With `--resume` and no `.drive/` here, run `ls -d ~/Projects/*/.drive/local/active 2>/dev/null`,
>      name the runs it finds in one line, and stop.
>    - When the goal names or clearly means an existing repository other than this one (search with
>      `references/intake.md` section 3), launch the run there and end the turn with one line naming
>      the session: `cd <repo> && claude --bg --name drive-<slug> --model fable --effort high --settings '<DRIVE_SETTINGS>' "/drive <goal verbatim>"`,
>      with the settings JSON from `references/long-running.md` section 2.
>    - When the goal is new work (`build`, or `publish` of a new site) and this directory holds a
>      different project or is not a repository, create `~/Projects/<slug>` (refuse if it exists and is
>      not empty), run `git init -b main` and
>      `git commit --allow-empty -m "drive(launch): repository for <slug>; undo: rm -rf ~/Projects/<slug>"`,
>      then launch there as above.
>    - Otherwise this repository is the run's home. Continue.

Fix, `intake.md` §3, replace the paragraph beginning "If the directory is empty or unrelated" with:

> The directory is unrelated when the probe's noun search finds nothing the goal names and the
> repository's README and CLAUDE.md describe a different product. Then search
> `ls -d ~/Projects/*<name>* 2>/dev/null` and `grep -il '<name>' ~/Projects/*/README.md`. A hit is the
> run's repository; no hit is the evidence for greenfield. Either way SKILL.md section 2 step 0 moves the
> run; intake never continues in an unrelated repository.

Fix, `parallel.md` §6 and `spec.md` §4: every brief states the repository root as an absolute path and
writes every command as `cd <absolute root> && <command>`.

Note for whoever writes the hook subcommands: resolve the run from the `cwd` field of the hook's JSON
input, not from `os.getcwd()`.

Counterpoint: launching a background session from an interactive one leaves the owner with two
sessions. The interactive one ends in the same turn with one line, and the background launch is his
documented default anyway, so the cost is one line of output.

### Gap 2 (P0). A run that honestly falls short of Done has no terminal state and cannot end

Evidence: `lint --final` requires every row Done or Dropped; `drive.py end` accepts only a passing final
lint or `aborted`; STATE's statuses are `running`, `verifying`, `blocked`, `stalled`, `done`,
`aborted`. Device-only claims are never Done, a preview is never Live Proof, a failed reproduction
caps at Partial, and a spent budget stops the run. Each of those is an expected outcome in the
examples, and SKILL.md §9's "(or the honest stop status)" names nothing that the script accepts.

Fix, `state-files.md` §6, add to the status list:

> `stopped`: the run ended short of Done for one of SKILL.md section 9's stop conditions, every piece
> of work that did not depend on the blocker is finished, and REPORT.md opens with "Stopped because".
> Like `done`, it lets the session end and lets `drive.py end` close the run.

Fix, `state-files.md` §9, `--final` row, replace with:

> every row Done or Dropped; or, with `status: stopped`, every row below Done carries its reason as an
> Open failure, the Blocked on line, a `why:device-only:` token, or a DECISIONS.md narrowing; REPORT.md
> exists and its rung counts equal STATUS's; every investigation closed; the retro committed

Fix, SKILL.md §9, replace "set `status: done` (or the honest stop status), run `drive.py end`" with:

> set `status: done` when every row is Done or Dropped, otherwise `status: stopped`; run
> `drive.py end`, which accepts either once `lint --final` passes

Also add `stopped` to the gate table in `long-running.md` §5 (allows) and change `drive.py end` to
treat `stopped` like `done`.

### Gap 3 (P0). Compaction drops lessons, stopping, standing rules, and the reference index

Evidence: SKILL.md §7 starts past the 5,000-token re-attach line, and §8, §9, the standing-rules block,
and the reference index follow it. The re-injected start view prints state, not procedure. Synthesis §2
required the whole spine above the line; the 450-line cap was met, but the token cap was not. The
standing-rules block is where the lesson loop promotes its strongest rules, so the most-proven lessons
are exactly the ones lost.

Fix, SKILL.md structure:

1. Move `## Standing rules` (with its markers) and `## Reference index` to directly after §1.
2. Replace the trait table in §3 step 4 with two sentences: "Mark each trait `confirmed` or `suspected`
   using `references/intake.md` section 7, whose headings are the trait names. Every trait's gate
   applies at every size; `auth` brings `drive:security-reviewer` and `drive:severe-tester` even at XS."
   That saves roughly 900 tokens.
3. Tighten §5's hardening-order paragraph to a pointer to `verification.md` §5.

Fix, for the `hook-reinject` subcommand (to be written): after the start view, print SKILL.md's text
from `## 7. Failures and lessons` to the end of `## 9. Stopping and the report`, sliced by heading, so
that part returns after every compaction whatever its token position.

### Gap 4 (P1). Publish treats a preview as live in one file and as local in four

Evidence: `publish.md` live-proof row and Done paragraph accept the preview; `definition-of-done.md`
§2 and §3, `web.md` §12, `ui-verification.md` §12, and synthesis §19 item 4 say a preview is Local
Proof. SKILL.md §8 and `intake.md` §12 forbid publishing on the owner's behalf.

Recommendation: keep the preview default, because a public site under his name and his team's names is
a publishing act, and fix the target at intake so the run can finish Done.

Fix, `publish.md` "Deployment boundary", replace the paragraph with:

> Deploy to a preview on the owner's own hosting in every publish run. Promote to production only when
> the goal asks for the site to be live or launched; a production deploy is the owner's publishing act
> otherwise. When production is not in scope, create every row at intake with `live: n` and the reason
> "production promotion not requested; the promote command is in the report", and put the one promote
> command in REPORT.md. When the hosting account is not authenticated, deploy nothing, name the login
> under Blocked on, and keep rows at Local Proof.

Fix, `publish.md` phases table, live-proof row: runs only when production is in scope; its exit check
reads "gates green on the production URL; stamp matches; `shim_differences` recorded". In the Done
paragraph, delete "(the preview, or production when the goal asked for it, with a matching build
stamp)" and write "at the production URL when production is in scope; otherwise the preview gates
passed and the promote command is in the report".

Alternative the owner may prefer: treat "create a website" as asking for it to be live. If so, change
one sentence ("when the goal asks for a site to be created, launched, or live"); everything else above
still applies.

### Gap 5 (P1). The lessons loop skips stopped runs, has two triggers, and may be unable to commit

Evidence: SKILL.md §7 says "Retro before Done", and §9 does not require a retro when stopping, although
`lessons.md` §12 says every run that completed or stopped. SKILL.md §7 and `lessons.md` §1 item 2 make
every verifier rejection a failure event, while `verification.md` §6 opens an investigation only when a
gap returns. `drive.py lesson-commit` writes to `~/Projects/drive`, which is outside the run's
repository; in a headless or background session with no prompts, a write outside the working directory
is denied unless the settings allow it, and no fallback is written. The standing-rules admission rule
("Seen 3 or more across at least two projects") cannot be checked, because lesson evidence may not name
projects and nothing else records which project each sighting came from. "Every fifth run whose lessons
commit" has no counting source.

Fix, SKILL.md §7, Retro bullet, replace with:

> **Retro** on every run above XS before its report, whether it ends `done` or `stopped`; a stopped run
> is the likeliest to hold a lesson. Every investigation is closed or explained, every ledger row at
> count two is investigated, and lessons are committed or "none" is stated with the reason.

Fix, SKILL.md §7 failure-event sentence and `lessons.md` §1 item 2, replace "a verifier rejection" with:

> a verifier rejection of work whose own gates were green, which becomes a retro candidate; it opens an
> investigation record only when the same gap returns after a fix, or when no gate the maker ran could
> have caught it

Fix, `long-running.md` §2: extend `DRIVE_SETTINGS` with
`"permissions":{"additionalDirectories":["/Users/<owner>/Projects/drive"]}` (absolute path; JSON in
single quotes does not expand `$HOME`), and add a pre-flight row: "Skill repository writable:
`test -w ~/Projects/drive/skill/references/lessons && git -C ~/Projects/drive rev-parse HEAD`. When it
fails, record it and add the directory to the launch settings at the next resume."

Fix, `lessons.md` §10 commit message shape, add two body lines, `Project: <repository directory name>`
and `Run: <goal slug>`. Commit bodies are not skill files, so the no-project-names rule on entries still
holds. Consolidation counts distinct `Project:` values for standing-rule admission and distinct `Run:`
values since the last `consolidate:` commit for the every-fifth-run trigger.

### Gap 6 (P1). XS has the maker certify itself, no ledger, and no closing message

Evidence: SKILL.md §1 says the maker never decides it is done, but XS spawns no verifier; with no
`.drive/`, a second workaround is undetectable; SKILL.md §3 step 2 says "unless the size is XS, run
capabilities" before step 5 has set the size; §9 describes REPORT.md only.

Fix, SKILL.md §3 size table, XS ceremony cell, replace with:

> no `.drive/`; no subagents except trait gates; one refutation test seen failing before the change and
> passing after, which stands in for an independent verifier; the commit body records claim and
> evidence. Size up to S the moment a workaround is needed, the test cannot be made to fail first, or a
> second file changes. End with one message: the commit, the claim, and the failing and passing test
> lines.

Fix, SKILL.md §3 step 2: delete "Unless the size is XS, run `drive.py capabilities` and the ToolSearch
probes in `references/capabilities.md`" there, and add to step 6 "Run `drive.py capabilities` and the
ToolSearch probes in `references/capabilities.md` after `init`."

### Gap 7 (P1). Test-plan exits are checked by the grader, which the grading tiers forbid

Evidence: `build.md` and `feature.md` test-plan rows name `drive:grader` for "one refutation test per
claim at the cheapest real layer"; `models.md` §5 says never to give a tier-two judgment to the grader,
and choosing the honest layer is exactly the judgment `testing.md` §2 calls the commonest failure.

Fix, `build.md` and `feature.md` test-plan exit check, replace "(drive:grader)" with:

> (drive:grader first confirms every claim has a row and every double a ledger row; then drive:architect
> in fresh context at S to M, or drive:auditor at L to XL, judges the layer and the kindness answers)

### Gap 8 (P1). Pre-fix check: worktree in two files, archive copy in four; review level disagrees

Fix, `fix.md` Verify paragraph, replace "Create a detached worktree at the pre-fix sha under
`/private/tmp`, copy the regression test into it, and pass its path." with:

> Export the pre-fix tree with
> `mkdir -p /private/tmp/drive-prefix-<key> && git archive <pre-fix sha> | tar -x -C /private/tmp/drive-prefix-<key>`,
> copy the regression test into it, install dependencies there, and pass its path.

and "Remove the worktree in the step that saves the verdict" with "Remove the copy in the step that
saves the verdict". Make the same replacement for the code block in `testing.md` §11.

Fix, `fix.md` verify row: replace `/code-review high <baseline_sha>...HEAD` with
`/code-review <level from references/verification.md section 5> <baseline_sha>...HEAD`, and in
`verification.md` §5 step 2 replace "level `medium` for `fix` and size S, `high` for M, L, XL" with
"level `medium` for any run at S and for a `fix` below M, `high` otherwise".

### Gap 9 (P1). Existing products get unrequested production code, and role accounts have no source

Evidence: `ui-verification.md` §3 requires a production build stamp and a state harness in wave 0;
`definition-of-done.md` §6 A blocks unrequested behaviour. `web.md` §20 requires a real account per
role for Live Proof, while `intake.md` §12 forbids creating accounts and entering credentials.

Fix, `ui-verification.md` §3, add after the table:

> **Existing products.** Read a build identifier the product already exposes (a version endpoint, a
> deploy id in a response header, a hashed asset name) and record how in `screens.yaml`. Add the stamp
> only when none exists, with a DECISIONS.md entry naming it verification infrastructure and its undo,
> and list it in the report. Keep the state harness behind the development build. The final audit
> treats both, when recorded this way, as requested.

Fix, `web.md` §20 Live Proof cell, replace "verified with a real account for each role" with:

> verified as each role, using test accounts the environment already has, reached through variables the
> owner has set (checked with `test -n "${NAME+x}"`, never printed), or fixture users the product's own
> seed command creates in a non-production environment; with neither, the per-role checks stay at
> Local Proof and the variable names go under Blocked on

### Gap 10 (P1). A fix goal with no symptom has no way to find the bug

Fix, `fix.md` "When it applies", add:

> When the goal names no observable symptom ("find this bug"), find the candidate before classifying:
> Open failures in any earlier `.drive/` or `.drive/runs/`, failing CI runs
> (`gh run list --status failure --limit 20`), open issues labelled as bugs, errors in the system's own
> logs read through its tools, and the project's auto memory notes. Take the failure with the most
> evidence as an assumption in the restate block, list the others under Discoveries, and when nothing
> is found, stop with a report naming what was searched.

### Gap 11 (P2). The classification is never checked by anyone but its author

Evidence: intake is checked by the orchestrator alone (SKILL.md §4 step 3). A wrong shape or size
changes every later phase, and "re-classification review" at XL names no agent.

Fix, SKILL.md §3 step 6, add before the commit sentence:

> At M and above, spawn a fresh `drive:architect` in review mode with the goal verbatim, the probe
> output, and the draft GOAL.md, asking whether shape, variant, size trigger, and traits follow from
> `references/intake.md`. Apply blocking findings before the intake commit.

Fix, SKILL.md §3 size table XL row and `intake.md` §9: "phase gates with a re-classification review by
`drive:auditor`".

### Gap 12 (P2). The iOS capture matrix and observation minimum multiply without new information

Fix, `ui-verification.md` §5 tier table, replace the first primary iOS row with:

> | primary, iOS | `phone` for every state; `small` and `large` or `tablet` for `default` and the state with the most content | light and dark on `phone`; light elsewhere | `large` for every state; `accessibility-extra-extra-extra-large` for `default` and the state with the most content | as listed |

Fix, `ui-verification.md` §7 Observations, replace "For every cell it reads, the reviewer records at
least five observations" with "For every screen and state, the reviewer records at least five
observations spread across its cells, and at least one for each cell that differs from its siblings in
scheme, size, or text". Change the matching sentence in `agents/ui-reviewer.md` step 4.

Counterpoint: dark mode per state is where asset bugs hide, which is why `phone` keeps both schemes for
every state.

### Gap 13 (P2). Three locations for the publish content plan

Fix: follow synthesis §19 item 3. In `publish.md` "The content plan", replace "SPEC.md holds three
sections" with "`.drive/content-plan/` holds `positioning.md`, `site-map.md`, and `pages/<slug>.md`";
in its phases table, the content-plan artifact becomes `.drive/content-plan/`; in `spec.md` §2, the
`publish` site row's template and path become "none; `.drive/content-plan/` per
`references/shapes/publish.md`".

### Gap 14 (P2). Publish runs treat requested research as a gate, not a deliverable

Fix, `publish.md` "When it applies", replace the second sentence with:

> When the goal asks for research as well as the site ("research our market position and build …"),
> the research is a deliverable: run it as a `report` sub-goal first, delivered to the path the goal
> names or `docs/<slug>.md`, and cite its slugs in the content plan.

### Gap 15 (P2). Deferred store deletion waits on a future run

Fix, `move.md` "Cutover, soak, decommission", replace "which the next drive run in this repository
performs at start" with:

> and schedule a check for the end of the rollback window under the soak rule in
> `references/long-running.md` section 11: it confirms the export restores and nothing read the store,
> then deletes it through the platform's tools, or holds and writes an investigation

### Gap 16 (P2). Moves assume identity logs and weekly cycles that small systems lack

Fix, `move.md` "Inventory and characterization", add after the first paragraph:

> When the old path does not log caller identity, or keeps logs for less than a cycle, deploy identity
> logging first as a small package with its undo, and continue characterization, design, and build while
> the cycle accumulates; only the first weight step waits for it.

Fix, `move.md` cutover paragraph, add:

> When the charter shows every consumer is owned and enumerable from configuration (five or fewer), move
> consumer by consumer with the drill before the first, and soak only the final stage for one cycle.
> Record that choice in DECISIONS.md.

### Gap 17 (P2). A blocked walking skeleton leaves the waves undefined

Fix, `build.md` "Wave 0 and the walking skeleton", add:

> When deploying the skeleton needs a login or secret the run lacks, name it under Blocked on, record
> that every row crossing that boundary is capped at Local Proof until the skeleton runs live, and
> continue the waves against the platform's real local runtime. The first action after the owner sets
> it is the skeleton's live check, then a re-run of the kindness ledger's live checks.

### Gap 18 (P2). The owner's final view is under-specified

Evidence: SKILL.md §9 says "tell the user in a few sentences where the report is and what to look at
first". Commits stay local (`long-running.md` §10), and a background session's last message is seen
only through `claude agents` or `claude logs`.

Fix, SKILL.md §9, replace that sentence with:

> End with one short paragraph: the status and why; the rung counts; the one thing to look at first; the
> path of REPORT.md; how many commits are on the branch since `baseline_sha` and whether they are
> pushed; and the command that resumes, promotes, or finishes the run when one exists.

### Gap 19 (P3). "Commit to main" versus the owner's "current branch"

Fix, SKILL.md §1, replace "Commit to main in small steps." with "Commit on the current branch, which is
main in the owner's repositories, in small steps; never create, switch, or push branches." Record the
branch in GOAL.md's probe.

### Gap 20 (P3). Public repositories receive proofs, screenshots, and internal notes

Fix, `state-files.md` §2, add:

> When `gh repo view --json visibility -q .visibility` says `PUBLIC`, commit only GOAL, STATE, STATUS,
> DECISIONS, and REPORT; add `.drive/proofs/`, `.drive/reviews/`, `.drive/investigations/`, and
> `.drive/research/` to `.gitignore`, and record the choice in DECISIONS.md.

### Gap 21 (P3). Dashboard traits disagree

Fix, `web.md` §1 dashboard row: "`feature`, traits `existing-code` and `ui` confirmed; `data` and `auth`
suspected until archaeology".

## 4. Direct answers to the four extra questions

**Invoked in an unrelated directory.** The skill does not tell the orchestrator what to do. It would
most likely initialise the run in whatever repository the session was started in and commit GOAL.md to
that repository's main. For a new project in an empty directory, `drive.py init` refuses, and nothing
says to create the repository. Gap 1 is the fix.

**At XS.** The run classifies, reads `general.md`, writes one failing test, fixes, sees it pass, runs
the project's checks, and commits with claim and evidence in the body. The Stop gate is inert because no
`.drive/local/active` exists, which is right. What is missing is an explicit statement that the red then
green test stands in for independent verification, a rule to size up when a workaround appears, and a
defined closing message (gap 6). An `auth` trait correctly still brings the Opus security reviewer.

**How the run ends and what the owner sees.** A run where everything reaches Done ends cleanly: retro,
REPORT.md from the files, final audit, `lint --final`, `status: done`, `drive.py end`, commit, and a few
sentences. Every other ending (device-only claims, a preview-only site, an unreproducible bug, a spent
budget) cannot pass the final lint or close the run (gap 2), and the closing message does not say
whether commits are pushed or what to run next (gap 18).

**Whether the lessons loop fires.** Consult fires mechanically, since a brief without the lessons
heading is malformed and verifiers check compliance. Distillation fires on completed runs of size M and
above in an interactive session that can write `~/Projects/drive`. It is unlikely to fire on stopped
runs (no retro), after compaction (section 7 is gone from context), at XS and often at S (no ledger or
LESSONS.md), or in a background or headless session denied writes outside the repository. Its standing
rules can never be promoted, because the two-project condition has no data (gaps 3 and 5).
