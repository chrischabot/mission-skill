# 35 · Code fixes after the adversarial review, and what the docs must say

Written on 2026-09-14 alongside the code fixes for `research/34-adversarial-review.md`. Finding numbers refer
to that report. This file lists every behaviour change in `skill/scripts/drive.py`, `install.sh` and
`skill/templates/` that SKILL.md, the references, the agent files and the README must reflect, with the exact
token forms and refusal conditions the code now applies.

## Heredoc writes (finding 1)

The guard now reads here-documents. After a line holding `<<WORD`, `<<'WORD'`, `<<"WORD"` or `<<-WORD`, the
lines up to the delimiter are data and are not judged as commands; `<<-` strips leading tabs before the
delimiter is matched, several heredocs on one line are read in order, and an unterminated heredoc runs to the
end of the command. The command line itself is still judged, including its `>` or `tee` target, so the main
thread's heredoc into a verdict path stays refused, and a command on the line after the delimiter is judged
as usual.

In an unquoted heredoc (`<<EOF`), bash expands `$(...)` and backticks in the body, so the guard judges those
substitutions as commands. The agent files should keep telling reviewers to quote the delimiter
(`cat > <path> <<'JSON'`); a Markdown review with backticked code spans under an unquoted delimiter is refused,
because bash would run those spans.

When a reviewer's first word is not on its allowlist, the refusal now quotes the simple command it judged, in
backquotes, and points at a quoted heredoc into the reviewer's own output path for verdict and review files.

## install.sh (finding 2)

`install.sh` accepts `loaded` (the skills-directory status) or `enabled` in `claude plugin list`; `disabled` or
no entry for `drive@skills-dir` fails with exit 1. It prints "Enabled drive@skills-dir" only when
`claude plugin enable` exited 0, and otherwise says the enable command did not succeed and checks the list.
Any README line that says to expect "enabled" should say "enabled or loaded".

## drive.py end for blocked and stalled runs (finding 3)

`drive.py end` for a `blocked` or `stalled` run now runs the hygiene checks `lint --stop` runs (uncommitted or
untracked paths not in the baseline, worktrees and branches created during the run, `.drive/local/` ignored,
worker reports newer than STATE.md) and refuses to close on any failure, printing them. In practice STATE.md
and REPORT.md must be committed before `end`. An `aborted` run already ran the full `lint --stop`. The Stop
gate is unchanged: a properly blocked or stalled turn may still end on a dirty tree.

## Reviews and untracked files (finding 4)

A review is voided in exactly two cases. The first is a tracked file (outside `.drive/`) that is modified or
deleted during the reviewer's window when no hook recorded that path as an edit since the window opened; the
hooks record an edit for every Edit, Write, MultiEdit or NotebookEdit by the main thread or a non-reviewing agent,
and for every file a shell call by the main thread or a non-reviewing agent changed while a reviewer ran. So a
recorded maker or main-thread edit still never voids a review, and an unrecorded tracked change (the reviewer's
own, or one made outside Claude Code) does. A tracked file dirty at the start that the main thread commits
unchanged also does not void. The second is HEAD moving by a rewrite (the old HEAD is no longer an ancestor) or by
commits the main thread did not make, apart from commits that touch only `.drive/`. Untracked files that appear, change or disappear during the window never void it. They are logged
in `.drive/local/gate.log` as `SNAPSHOT NOTE <role> <agent>: untracked path(s) ... do not void it: <paths>`,
and `lint --stop` and `--final` report any the run leaves uncommitted. The void message names the changed paths
in both gate.log and the lint failure. `references/verification.md`'s recovery advice for a voided review should
no longer mention test artifacts as a cause, and wave 0's advice to ignore test-runner output still applies for
hygiene.

## The run marker, the baseline, and git clean (finding 5)

While a run is active, the guard refuses for every role and the main thread any delete, move, or overwrite of
`.drive/local/active` or `.drive/local/baseline.json`: `rm`, `mv`, `cp` or `tee` onto them, a `>` redirect,
`find ... -delete` over them, and the Write, Edit, MultiEdit and NotebookEdit tools. Reading them (`cat`,
`python3 -c` with `open(...)`) stays allowed. `git clean` with `x` or `X` in any argument cluster (`-fdX`,
`-xdf`, `-f -d -X`) is refused inside the project unless it is a dry run (`-n`, `--dry-run`). `drive.py end`
removes the marker itself.

When `hook-stop` finds no marker but `.drive/STATE.md` (searched from the hook's `cwd` up to the git top level)
says `running` or `verifying`, it allows the stop and emits one warning, once per session, as a `systemMessage`
and on stderr, naming the missing marker and `/drive --resume`. The sessions already warned are recorded in
`.drive/local/lost-marker-warned.json`.

## Stopped runs are audited (finding 8)

`lint --final` for a `stopped` run now requires `.drive/reviews/<date>-final-audit.json` with transcript-backed
provenance, the same as a done run, whenever any STATUS row is above Missing (Scaffold or higher). A stopped run
with no rows, or with every row Missing (or Dropped), needs no audit. A no-go audit does not satisfy the check:
`final_audit_problems` requires `verdict: pass` in the latest `*-final-audit.json`, schema-valid, transcript-backed,
and no older than the latest code commit, for stopped runs exactly as for done runs. A stopped run whose audit
says no-go has to address the findings (usually by narrowing rows with `why:` or DECISIONS.md entries and fixing the
report) and get a fresh passing audit before `lint --final` and `drive.py end` accept it. The documents that promise a stopped run
is audited (`definition-of-done.md`, `verification.md`, `agents/auditor.md`) are now accurate; anything saying a
stopped run skips the audit is not. No template text contradicted this.

## Blocked-on tokens (finding 9)

`Blocked on: budget: <words>` ends the turn (and lets `drive.py end` close the run) only when the maker spawn
count the lint keeps (implementer, writer, designer, architect, researcher since the run started) has reached
the subagent figure on GOAL.md's `budget:` line, or when a DECISIONS.md entry added since the `drive(intake)`
commit has the word "budget" on its `Decision:` line. Otherwise the refusal says so and asks for that decision or
more work.

`Blocked on: credentials: <words>` requires a named secret after the token: an uppercase identifier of three or
more characters (`CLOUDFLARE_API_TOKEN`), or a name in backquotes (`` `stripe live key` ``) or double quotes
(`"Apple notarization password"`). `credentials: none` and `credentials: the owner's deploy token` are
refused. `skill/templates/STATE.md` now shows both forms.

## Aborted (finding 10)

`status: aborted` needs REPORT.md and a DECISIONS.md entry whose `Decision:` line begins with `Abort` or
`Aborted`, case-insensitive (`- Decision: Abort; the owner ended the run.`). A Decision line that merely
mentions aborting ("do not abort", "aborting would be premature") no longer counts. The STATE.md template quotes
the required words.

## Main-thread git while a run is active (finding 11)

In the shared checkout the main thread is now refused `git stash` (except `git stash list` and
`git stash show`), `git clean` other than `-n` or `--dry-run`, and `git commit --amend`. The refusals explain
that a stash or clean removes makers' uncommitted or untracked work, and that an amend rewrites HEAD, which
voids running reviews and can rewrite the intake commit the lint and the audit anchor on. The same commands in a
scratch copy outside the project (`git -C <scratch> ...`) stay allowed. SKILL.md section 6 and
`references/parallel.md` should list these next to `git reset --hard`.

## Provider detection (finding 15)

`drive.py preflight` adds a `provider` check: `ok provider: anthropic` when none of `CLAUDE_CODE_USE_BEDROCK`,
`CLAUDE_CODE_USE_VERTEX` or `CLAUDE_CODE_USE_FOUNDRY` is set to a true value, and otherwise
`warn provider: bedrock|vertex|foundry (<variable> is set)` with the warning that model aliases resolve to older
models there, so drive must not pass a per-call model override to the Agent tool. A warning does not fail
preflight. `drive.py capabilities` records the same value as `env:provider` in `.drive/capabilities.json`.
`references/models.md` should state that rule.

## Smaller changes

- **Stall message (low 21):** the stall system message and gate.log line now name everything that counts as
  progress: STATE.md apart from its `updated:` line, STATUS.md, HEAD, and the working tree.
- **Resume matching (low 24):** `drive.py init` treats a goal as the same run only when its text matches the
  goal GOAL.md recorded at init, ignoring case and whitespace. The 50-character slug decides only for an older
  GOAL.md with no recorded goal text, so a different goal that shares its opening now archives the old run.
- **lesson-commit (low 25):** `drive.py lesson-commit` refuses a SKILL.md whose change reaches outside the
  `<!-- drive:standing-rules:start -->` ... `<!-- drive:standing-rules:end -->` block, and a SKILL.md that is not
  committed.
- **Patches (low 27):** the guard's frozen-path check for `git apply`, `git am` and `patch` now also reads
  `diff --git a/... b/...`, `rename from/to` and `copy from/to` lines, so a pure rename or mode change of a
  frozen test is refused; patch files of 1 MB or more are not read.
- **Docstring (low 17):** `hook_stop` now says Stop is registered only in hooks.json.
- **visibility (low 23):** covered by a command-line test; no behaviour change.

## /code-review through drive:security-reviewer (docs finding 12)

No code change is needed. The guard does not judge the Skill tool itself. The shell commands the skill runs
inside `drive:security-reviewer` go through that role's read-only allowlist: git read-only subcommands, reading and
searching, the project's recorded checks. Its writes are confined to `.drive/proofs/` and `.drive/reviews/`, and
the Edit and Write tools are refused. A code-review report is therefore written as a quoted heredoc under
`.drive/reviews/`. Review evidence is recorded with provenance only for the roles the lint names (verdicts from
verifier or ui-reviewer, final audits from auditor or verifier), so a code-review Markdown file is an input for
the orchestrator, not a STATUS evidence token.

## After the fix review (research/37)

A later review (`research/37-fix-review.md`) found gaps in the fixes above. The code now applies these forms, and the
documents that describe them were updated alongside.

- **Here-strings (H1):** `<<<` is a here-string, not a heredoc, so every line after `cat <<< hi` is judged as a command.
- **Standard input (H2):** a heredoc body is data only when the command reading it is not a shell or an interpreter.
  A body or here-string fed to a shell with no script operand, or with `-s` (`sh <<'EOF'`, `bash -s <<'EOF'`,
  `bash <<< '...'`), and a body piped into a bare shell (`cat <<'EOF' | bash`), is judged as `bash -c` with that text
  would be. `bash < file` is judged as `bash file` would be, and refused when the file cannot be read (missing, named
  through a variable, or 256 KB or larger). A body an interpreter reads as its program (`python3 - <<'PY'`,
  `python3 <<'PY'`, `node -`, `ruby -`, `perl -`, or piped into one) gets the inline-code analysis `-c` and `-e` get.
  Quoted heredocs fed to `cat` or `tee`, whatever their bodies say, stay allowed.
- **Heredocs in `$(...)` (M1):** the substitution scanner skips a heredoc body, so Claude Code's commit form
  `git commit -m "$(cat <<'EOF' ... EOF\n)"` with an apostrophe or parenthesis in the message no longer hides a following
  `git push`.
- **credentials: (M2):** the named secret is an uppercase identifier containing an underscore or ending in `TOKEN`, `KEY`,
  `SECRET`, `PASSWORD`, `PAT`, `CREDENTIALS` or `CERT` (`CLOUDFLARE_API_TOKEN`, `GITHUB_PAT`), or a name of at least two
  letters in backquotes or double quotes (`"Apple notarization password"`). `NONE`, `TBD`, `TODO`, `N/A`, `NA` and
  `UNKNOWN` are refused in every form, and single quotes no longer count.
- **budget: (M3, L5):** the DECISIONS.md entry must be added since intake, compared by heading and body so a reused
  heading counts, and its `Decision:` line must begin with `Stop` or `Narrow` (any case) and name the budget, as in
  `Decision: Stop; the budget no longer covers the admin screen`.
- **HEAD rewrites (M4):** while a run is active the main thread is refused `git reset` to a commit other than `HEAD`
  (`HEAD~1`, `HEAD^`, a sha, `--soft X`, `--mixed X`) and `git update-ref HEAD ...` in the shared checkout. `git reset`,
  `git reset HEAD`, `git reset -- <paths>`, `git reset HEAD -- <paths>` and `git reset <existing path>` still unstage,
  and `git -C <scratch>` copies are unaffected. SKILL.md section 6, `parallel.md` and `intake.md` list them.
- **Abort (L1):** the `Decision:` line must begin with `Abort` or `Aborted` followed by `;`, `:`, a comma, a period or
  the end of the line, so the documented form is `Decision: Abort; <why>`. `Abort not needed` no longer counts.
- **Marker deletes (L2):** inline code (`-c`, `-e`, or a stdin body) that calls `os.remove`, `os.unlink`, `shutil.rmtree`,
  `Path(...).unlink`, `fs.rmSync`, `fs.unlinkSync`, `fs.rmdirSync`, or a similar delete, with a literal naming
  `.drive/local/active`, `.drive/local/baseline.json`, `.drive/local` or `.drive`, is refused like `rm`, and so is
  `rsync --delete*` into a destination that holds them.
- **Index transitions (L3):** in a reviewer's window, an untracked file staged from outside the hooks (`??` to `A`)
  counts as untracked and never voids, and a tracked file removed from the index (`git rm --cached`, `D `) voids like a
  deletion.
- **install.sh (L4):** the status check stops at the next plugin entry, so another plugin's `Status:` line is never read
  as drive's.
- **Stalls (L6):** `references/long-running.md` now says to commit STATE.md unchanged, with REPORT.md, before
  `drive.py end`.
- **Digit-only short shas:** GOAL.md's classification reader keeps a digit run with a leading zero as the string it
  was written as, so `baseline_sha: 0970287` names commit `0970287` instead of the integer 970287; only canonical
  integers (`3`, `12`) become numbers. The GOAL.md template and the `intake.md` example now quote `baseline_sha`.
  STATE.md's `commit:` is read as raw text and was never coerced; quoting it there would put the quotes in the value.
- **Not changed:** a subagent outside drive's roster (`general-purpose`) keeps the main thread's rules, so it may still
  commit, and `bash <<'EOF'` / `git commit` from it is judged exactly as `git commit` and `bash -c 'git commit'` are.
