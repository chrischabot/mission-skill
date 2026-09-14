# Package <package id>

I'm working on <larger task> for <who>. They need <what this package enables for the rest of the work>. With that in mind: build this package in the shared checkout, where other agents are working in other directories at the same time.

<!-- Written by drive:architect or the orchestrator to .drive/packages/<id>/brief.md, one per
package, self-contained. The package id is a slug of what it delivers. Every heading below is
required; drive.py lint checks them and the ownership list. -->

repository root: <absolute path; run every command as cd <root> && <command>>
skill directory: <absolute path of the drive skill, for references/ and templates/ named below>

## Goal
<What exists when you are done, in user-visible terms. One paragraph.>

## Claim
key: <claim key>
claim: <claim words>
what would prove it wrong: <the refuting scenario from the spec>

## Inputs you rely on
- `<path>` (already on main; read it, do not modify it)

## Contract
<The shapes other packages code against today>. Do not change them. If the design forces a change, stop and report blocked with the exact reason.

## Files you own
- `<path or glob>`

## Files you must not touch
- `<path or glob>` (owned by <package id or the integrator>)

## Tests to make pass
Write only the tests TESTPLAN.md names for this claim, sized like the neighbouring tests, with the refutation test first.
- <test path>::<test name>
- Production constraints the harness must enforce: <limit and where it is enforced, or none>

## Commands you may run
- Focused test: `<exact focused test command>`
- Build directory: `<per-package build directory, or none>`

## Lessons that apply to this task
- <rule heading, verbatim, at most ten, or none>

## Done means
The tests above pass with the focused test command, every file you changed is under Files you own, and report.json says plainly what is not verified.

## Budget
<turns> turns and <minutes> minutes. At eighty percent of either without converging, stop and report partial with the exact remaining items.

## Rules
- Create or edit only the paths under Files you own. If you changed anything else by accident, never restore it yourself, because in this shared checkout a restore can throw away another agent's uncommitted work: list it in report.json's `files` marked "accidental", and the integrator reverts it.
- Never run git add, commit, push, stash, checkout, switch, reset, apply, rebase, merge, branch, or worktree. The one git write allowed is `git restore <path>` to discard your own edit to a file under Files you own, naming each file; the guard refuses it on any other path, a glob, `.`, `--staged`, or `--source`. The orchestrator integrates and commits.
- Run only the focused test command. The tree is shared, so whole-workspace runs report other agents' unfinished work.
- Install nothing. List every dependency in deps_requested with the reason.
- Put every change you need in a file you do not own into wiring_needed, as exact lines or a unified diff.
- If your work is already present when you start, run the focused test on it and report instead of redoing it.
- If the test harness is kinder than production on a constraint named above, make the harness enforce it first and say so in gates_run.

## Report
Write `.drive/packages/<package id>/report.json` following `templates/package-report.schema.json`: package, status (complete, partial, or blocked), files, tests as path::name, gates_run with each command, exit code, and output tail, wiring_needed, deps_requested, honest_gaps, follow_ups, noticed_not_touched (file, problem, reason), concerns, a summary of at most 1,500 characters, and model. Report only work a tool result from this session shows. Your final message is one status line, that path, the summary, and the model you ran as.
