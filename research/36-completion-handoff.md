# 36 · Completion handoff: what is left and how to finish it

**Status: completed on 2026-09-14.** Every step below was carried out: the docs were reconciled, the
two known code spots fixed, a focused re-review run (`research/37-fix-review.md`) and its findings
fixed, all checks passed (393 tests on Python 3.13 and 3.9), and the result was committed and pushed
to `chrischabot/mission-skill`. The rest of this file is kept as the record of the plan.

Written on 2026-09-14 for the agent that finishes this work. Read this file first, then `HANDOFF.md`
(project overview), `research/34-adversarial-review.md` (the last full review) and
`research/35-code-fixes-for-docs.md` (the behaviour changes made in response). The repository is
`/Users/chabotc/Projects/drive`, branch `main`, with no git remote.

## Where the work stands

The skill `drive` is complete and was committed up to `cfd30b3`, which added the adversarial review.
That review found 1 critical, 6 high, 9 medium and 11 low findings. Three agents then fixed them in
the working tree, and none of those fixes are committed yet (about 97 changed or new paths):

- **Code** (`skill/scripts/drive.py`, `install.sh`, `skill/templates/STATE.md`, the tests,
  including the new `skill/scripts/tests/test_adversarial_review.py`). The agent that made them
  reported 370 tests passing on `python3` (3.13) and on `/usr/bin/python3` (3.9.6), and `selfcheck`
  and `lesson-check` passing. Every new test was checked to fail against the old code.
- **Docs** (`skill/SKILL.md`, `skill/references/**`, `skill/agents/**`, `README.md`). These were
  edited before research/35 existed, then a reconciliation agent made them match research/35 and
  drive.py. It reported that `selfcheck`, `test_model_ids`, `test_templates` and
  `claude plugin validate skill` pass, and it also corrected one error 35 missed: `lint --final`
  runs the hygiene checks too, so a done or stopped run commits its final state before the lint
  and `drive.py end`, not after. Nobody independent has checked the docs against the code yet.
- **Evals** (`skill/evals/**`). There are now 19 cases, including the new `docs-typo-restraint`.
  Graders were rewritten per finding 7 and the README has an idle-score table. Nothing can be scored
  on this machine (see below).
- **HANDOFF.md** was rewritten as a current-state overview. It says all review findings were fixed;
  that is true only once step 2 below passes.

An earlier "flaky test" was investigated and is not a flake: the failing run happened mid-edit, and
the committed tree passed eight consecutive full runs, three of them concurrent.

## What to do, in order

1. **Check the docs against the code.** For each section of research/35 (quoted heredoc delimiters,
   `install.sh` accepting "enabled or loaded", `drive.py end` requiring a clean, committed tree for
   blocked or stalled runs, exactly what voids a review, marker and `git clean -x/-X` protection,
   stopped runs needing a passing final audit when any row is above Missing, the `budget:`,
   `credentials:` and `Abort` forms, main-thread `git stash`/`clean`/`commit --amend` refusals,
   provider detection, resume by recorded goal text, `lesson-commit` block check, frozen-test
   patches, `/code-review` through `drive:security-reviewer`), grep SKILL.md, the references, the
   agent files and README for the old behaviour and fix any disagreement. drive.py is the source
   of truth; if the code looks wrong rather than the doc, fix the code and add a test. Two such
   spots are already known and should be fixed in code:
   - `drive.py end` still prints "Commit the final state" after closing, although the hygiene
     checks already required a clean, committed tree; change the message.
   - The guard's frozen-test check for `git apply`, `git am` and `patch` lets a patch file that is
     missing or 1 MB or larger through unread. `references/testing.md` now says `freeze check`
     catches such a change afterwards. Either refuse unreadable patches while tests are frozen
     (and restore the doc's stronger wording) or leave the behaviour and keep the doc as it is;
     refusing is the more honest-mistake-proof choice.
2. **Run every check and make them all pass.** Run them after all edits have stopped, because
   doc-reading tests fail on half-finished edits:
   ```bash
   cd /Users/chabotc/Projects/drive && python3 -m unittest discover -s skill/scripts/tests
   ```
   ```bash
   cd /Users/chabotc/Projects/drive && /usr/bin/python3 -m unittest discover -s skill/scripts/tests
   ```
   ```bash
   cd /Users/chabotc/Projects/drive && python3 skill/scripts/drive.py selfcheck && python3 skill/scripts/drive.py lesson-check && claude plugin validate skill
   ```
   Also check that every JSON file under `skill/evals` parses with `python3 -m json.tool`.
3. **Commit on `main`** in a few plain commits (for example code and tests; docs; evals; research
   and HANDOFF). No branches, no worktrees, no attribution lines in commit messages.
4. **Optionally, run a short clean-context re-review** of only the changed areas, especially the
   heredoc handling in the guard and the new `end`, void and stopped-audit rules, walking one blocked
   run and one stopped run in a scratch repository under `$TMPDIR`. Fix and commit anything real.
5. **Push to `https://github.com/chrischabot/mission-skill`** (private). The owner asked for it to be
   overwritten with drive:
   - clone it into a scratch directory (`gh repo clone chrischabot/mission-skill`);
   - remove every tracked file (`git rm -rq .`), then copy in drive's committed tree, for example
     `git -C /Users/chabotc/Projects/drive archive HEAD | tar -x -C <clone>`, keeping drive's
     layout (`skill/`, `research/`, root files);
   - commit once on `main` with a message saying it replaces the mission skill with drive, and
     push normally. Never force-push;
   - update the repository description with `gh repo edit` to describe drive, and state in the
     README or the description that the eval suite has no scored run yet.
6. **Update HANDOFF.md** if anything above changed its claims (test count, case count, what is
   unproven), commit, and push the same change to mission-skill.
7. **Report to the owner** in exactly two short paragraphs of plain prose: what changed since the
   review and what is still unproven. The owner has twice rejected long summaries as a "wall of text".

## Constraints the owner set

- **Models.** Drive uses exactly `claude-fable-5-1` (Fable 5.1), `claude-opus-5` (Opus 5) and
  `claude-sonnet-5` (Sonnet 5), with Sonnet at low effort for graders and never Haiku. Any
  mismatch between docs and code about models, prices or effort is a critical bug.
  `skill/scripts/tests/test_model_ids.py` enforces this and must pass. The prices in
  `references/models.md` were verified against live docs in research/33 and 34.
- **Examples are only examples.** The iOS app with a Cloudflare backend (and the other four
  example goals) are illustrations of what drive might be asked to do. Never write code for them.
- **Repository discipline.** Plain commits on the current branch. Remove any worktree or branch you
  create immediately.
- **No approval queues.** Do not leave work waiting for the owner when you can finish it yourself.
- **Anti-mirage.** Do not call something done without having run the check that proves it; report
  failures with their output.
- **Writing.** Plain, full sentences; no rule IDs or codenames, no hype, no fragments.

## Known limits to state honestly

- **No scored eval run exists.** `claude plugin eval` refuses Bash-granting cases on this machine
  because `~/.docker` contains symbolic links from Docker Desktop and OrbStack. A scoped
  `DOCKER_CONFIG` workaround did not help. The owner must choose between running on another machine
  and moving those links; do not move them without asking.
- **No real `/drive` run exists.** The cost envelopes are modelled.
- **Unverified harness facts** are listed at the end of research/34: tool availability in background
  sessions, `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` via `--settings`, and bundled skills from subagents.
