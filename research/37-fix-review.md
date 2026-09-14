# 37 · Review of the fixes for the adversarial review

Written on 2026-09-14 by a clean-context reviewer against the uncommitted working tree over cfd30b3. The subject is the code
changes described in `research/35-code-fixes-for-docs.md`, and every claim below comes from running `drive.py` against hook
payloads in scratch git repositories under `$TMPDIR` (with `HOME` and `CLAUDE_PLUGIN_DATA` pointed at scratch directories),
built with the fixtures in `skill/scripts/tests/helpers.py`. Where a behaviour might predate the fixes, the same payload was fed
to `drive.py` as it stood at cfd30b3 (extracted with `git archive`) so that regressions can be told apart from older gaps. No
project file was edited.

Counts: no Critical, two High, four Medium, six Low.

## High

### H1. A here-string is read as a heredoc, so every later line of the command goes unjudged

`skill/scripts/drive.py:4677`. The check `command.startswith("<<", index) and not command.startswith("<<<", index)` rejects
`<<<` at its first character, but the loop then appends that one `<` and advances by one. At the next index the text is
`<< "hi"`, which passes the test, and `heredoc_operator` reads `hi` as a quoted delimiter. At the next newline `split_shell`
consumes the rest of the command as heredoc body, looking for a line that says `hi`. This is a regression introduced by the fix:
cfd30b3 refused these commands.

Reproduction (exit 0, allowed, now; exit 2 at cfd30b3 where noted):

- main thread: `read x <<< "$y"` newline `git checkout -b feature` (refused at cfd30b3)
- main thread: `cat <<< hi` newline `git push origin main` (refused at cfd30b3)
- `drive:verifier`: `grep -c x <<<"hi"` newline `git push origin main` (refused at cfd30b3)
- `general-purpose`: `wc -l <<< hi` newline `rm .drive/local/active`, which slips past the new run-marker protection

`split_shell("cat <<< \"hi\"\ngit push origin main")` returns `['cat <<< "hi"']`. The same command with `&& git push` on the
same line is still refused, so only later lines escape. The fix is to consume all three characters when `<<<` matches
(append `<<<` and advance the index by three) before the heredoc test runs. A test should cover a here-string followed by a
refused command on the next line, for the main thread and for a reviewer.

### H2. A heredoc body fed to a shell or interpreter on stdin is no longer judged

`skill/scripts/drive.py:4677` together with `check_argv` at `:5184`. Once the body lines became data, nothing judges them when
the command that reads them is `sh`, `bash`, `node -` or `python3 -`. `check_argv` treats a shell with no operand as harmless
(`if base in SHELLS` finds neither `-c` nor a script and returns None), and a `| bash` pipeline segment is just `bash`. Before the
fix the body lines were split as commands, which refused most of these by accident.

Reproduction (allowed now; the cfd30b3 column is what the old guard did):

- main thread: `sh <<'EOF'` / `git push origin main` / `EOF` (refused at cfd30b3)
- main thread: `bash -s <<'EOF'` / `git checkout -b feature` / `EOF` (refused at cfd30b3)
- main thread: `cat <<'EOF' | bash` / `git reset --hard HEAD~1` / `EOF` (refused at cfd30b3)
- `drive:verifier`: `node - <<'JS'` / `require('fs').writeFileSync('src/auth.py','x')` / `JS` (refused at cfd30b3), while the
  same write through `python3 -c` is refused
- `drive:verifier`: `python3 - <<'PY'` / `open('src/auth.py','w').write('x')` / `PY` (refused at cfd30b3, allowed now)
- `general-purpose`: `bash <<'EOF'` / `git commit -am x` / `EOF` was allowed at both commits.

`bash < run.sh`, where run.sh holds `git push origin main`, is allowed at both commits for the main thread and the verifier,
while `bash run.sh` is refused. Shell-on-stdin was therefore never covered, but the heredoc change widened the gap to the
common inline form. The fix: when a simple command's base is in `SHELLS` and it has no script operand (or has `-s`), judge
its heredoc body, here-string or `<` file with `check_command` / `check_script`, and do the same for a bare shell after a
pipe whose earlier segment carries a heredoc. When the base is an interpreter reading stdin (`python3 -`, `node -`, or one
with no script operand), run the body through the same inline-code analysis `-c` and `-e` get. That means keeping the
pending heredoc bodies in `split_shell`'s output rather than discarding them.

## Medium

### M1. A heredoc inside `$(...)` whose body holds an apostrophe or an unbalanced parenthesis hides the rest of the command

`skill/scripts/drive.py:4543` (`extract_paren`). The paren matcher tracks quotes and parentheses through the heredoc body. An
apostrophe in `don't` opens a quote that never closes, so the matcher returns the rest of the command as the substitution's
inner text. A `(` without its `)` has the same effect. The trailing `)"` then opens a double quote in the recursive parse,
which swallows the remainder. The allowed commands below are Claude Code's own default form for commit messages:

- main thread: `git commit -m "$(cat <<'EOF'` / `fix: don't` / `EOF` / `)" && git push origin main` is allowed
- main thread: the same with `fix (see #3` as the body is allowed
- main thread: the same with `git push origin main` on the line after `)"` is allowed

`split_shell` returns `["cat <<'EOF'", ')" && git push origin main', 'git commit -m "SUBST']`. This predates the fix
(cfd30b3 allowed all three), but research/35 presents heredocs inside `$(...)` as handled, and the fix did repair the
unwrapped case (`cat > notes.md <<'EOF'` / `don't` / `EOF` / `git push` is refused now and was allowed at cfd30b3). The
fix is to make `extract_paren` heredoc-aware: note `<<WORD` operators as it scans, and at each newline skip the pending
bodies exactly as `split_shell` does before resuming quote and paren tracking.

### M2. `credentials:` accepts words that name no secret

`skill/scripts/drive.py:3438` (`SECRET_NAME_RE`). Any three uppercase letters, any backquoted text and any double-quoted text
count as a named secret. Each of these let a blocked turn end through `hook-stop`: `credentials: NONE`, `credentials: TBD`,
`credentials: API access`, `credentials: the AWS account`, `credentials: " "`, `credentials: 'x'`, and
`` credentials: `?` ``. research/35 and `references/long-running.md:313` both promise `credentials: none` is refused, and it
is, but only in lower case. Correctly refused: `credentials: none needed`, `credentials: owner's key`,
`credentials: github_token`. The fix: require an identifier that contains an underscore or ends in a secret word (`TOKEN`,
`KEY`, `SECRET`, `PASSWORD`, `PAT`), and refuse a stoplist (`NONE`, `TBD`, `TODO`, `N/A`). Quoted names should need at
least two letters and not be whitespace.

### M3. `budget:` counts any Decision line that mentions the budget

`skill/scripts/drive.py:3462`. The test is `re.search(r"(?i)\bbudget", decision)`, which is the same word-mention loophole
the Abort fix closed for `aborted`. Reproduction: make_run's GOAL.md allows 8 subagents and no maker has spawned. Append
`- Decision: continue; the budget is fine.` to DECISIONS.md, then set `Blocked on: budget: done enough` with REPORT.md
saying "Stopped because". `hook-stop` returns no block. The genuine cases work: a budget decision that was already in
DECISIONS.md at the `drive(intake)` commit does not count, and eight recorded implementer spawns do count. The fix is to
require the Decision line to say what the budget no longer covers, for example to begin with `Stop` or `Narrow` and name
`budget`, or to require the entry's `Narrows:` line to name a key or phase.

### M4. The amend refusal is sidestepped by other HEAD rewrites the main thread may still run

`skill/scripts/drive.py:5619`. While a run is active the main thread is refused `git commit --amend` in every spelling tried
(`--amen`, `-a --amend`, `--no-edit --amend`, `git -c user.name=x commit --amend`). It is allowed
`git reset --soft HEAD~1`, `git reset HEAD~1` and `git update-ref HEAD HEAD~1`. I drove `git reset --soft HEAD~1 && git commit
-m redo` through `hook-guard` and `hook-post` while a verifier snapshot was open. The guard allowed it, and the review was
voided with `HEAD moved from bebc389 to 62af347 by a rewrite`. That is the harm the amend refusal's message describes, and
"undo the last commit and recommit" is what an honest agent does when it cannot amend. The fix: refuse `git reset` with a
commit target other than HEAD (the paths-only form stays allowed) and `git update-ref HEAD`, in the shared checkout while
a run is active. List them next to `--amend` in SKILL.md section 6 (line 240), `references/parallel.md:286` and
`references/intake.md:536`.

## Low

### L1. The Abort prefix still accepts a negation

`skill/scripts/drive.py:3435`. `^abort(ed)?\b` matches `Decision: Abort not needed; continue.` and `Decision: Abort-ish plan`,
and both let an `aborted` stop through `hook-stop`. `Aborting is premature.` and `Abortion` are refused as intended. The fix
is to require punctuation or end of line after the word (`^abort(ed)?\s*([;:,.]|$)`) or a following clause that is not
`not`.

### L2. Marker deletion through an interpreter or rsync is not refused

`skill/scripts/drive.py:5862` passes `run_control=False` for literals in inline scripts, so `python3 -c "import os;
os.remove('.drive/local/active')"` is allowed for the main thread and for `general-purpose`. `rsync -a --delete /dev/null/
.drive/local/` is also allowed. Everything research/35 lists is refused, along with every near-miss I tried: `rm -rf .drive`,
`rm -rf .drive/local`, `rm .drive/local/*`, `mv .drive/local ...`, `truncate`, `: >`, `>|`, `>>`, `sed -i`, `unlink`,
`rm src/../.drive/local/active`, `ln -sf`, `install`, `dd of=`, `touch`, `chmod`, `find .drive -delete`, `git clean -ffdX`,
`git clean --force -d -X`, `cd .drive && git clean -fdx`, and `git rm -rf --cached .drive/local`. The Write, Edit, MultiEdit
and NotebookEdit tools are also refused on both files, by absolute, relative and `../` paths. The gap matches research/35's
wording, which names only shell forms. The fix: treat `os.remove`, `os.unlink`, `shutil.rmtree`, `Path(...).unlink` and
`rmSync`/`unlinkSync` with a literal under `.drive/local/` as a write, and add `rsync --delete` to the delete forms.

### L3. Two index-only transitions outside the hooks contradict the stated void rules

`skill/scripts/drive.py:6414` classifies a path as untracked only when every recorded state is `??`. Staging an untracked file
from outside Claude Code (`git add src/new.py` during the window) voids the review with `src/new.py`, although research/35
says untracked files never void. `git rm --cached README.md` from outside, which removes a tracked file from the index, only
logs a `SNAPSHOT NOTE` and does not void. Both need git run outside the hooks. The same staging and commit done by the main
thread through `hook-guard`/`hook-post` correctly does not void. The fix is to classify by index state (`A ` from `??` as a
file newly staged, `D ` as a tracked deletion), or to document the two cases.

### L4. install.sh can read the next plugin's status line

`install.sh:58`. The awk program sets `found` on the drive line and prints the first `Status:` line after it, without stopping at
the next plugin's entry. A stub whose list shows `drive@skills-dir` with no Status line, followed by `other@mkt` with
`Status: ✔ enabled`, made install.sh print `drive@skills-dir is enabled (status: Status: ✔ enabled)` and exit 0. The
documented cases behave as research/35 says. `✔ loaded` exits 0 and prints "Enabled drive@skills-dir". `✘ disabled`
exits 1 with the enable hint. An enable that exits 1 before a `loaded` list prints "did not succeed; checking claude plugin
list" and continues. A list with no drive entry exits 1 with "not listed". The fix: in awk, clear `found` on any later
line that looks like an entry header (contains `@` and no `:`) before matching `Status:`.

### L5. A budget decision that reuses an older entry's heading is ignored

`decisions_since_intake` at `skill/scripts/drive.py:3441` compares entries by heading. A new entry headed "Compare tokens in
constant time", the same heading as an entry present at intake, is not counted, even though its Decision line reads "stop; the
budget no longer covers more", so the budget stop is refused. This is a false refusal, not a bypass. The fix is to compare
heading plus body, or count entries beyond the number present at intake.

### L6. One stall instruction omits the commit that `end` now requires

`skill/references/long-running.md:317` says "Leave STATE.md untouched until `$DRIVE end`, which needs those exact bytes".
Because the Stop gate itself rewrites STATE.md to `stalled`, STATE.md is uncommitted at that point, and `drive.py end` refuses
with `has uncommitted changes made during the run: .drive/STATE.md, .drive/REPORT.md`. The same file's line 422, SKILL.md
lines 328 to 333, and `references/definition-of-done.md:233` say to commit first. Line 317 should say "commit STATE.md
unchanged".

## What I verified and found sound

**Heredocs.** All five reviewing roles (verifier, auditor, grader, security-reviewer, ui-reviewer) may write their own
output path with quoted heredocs. I tried a JSON body and a Markdown body holding apostrophes, backticks, a literal `$(git
push)`, tables and `rm -rf /`, in the `cat >`, `tee`, `cat <<"EOF" >`, `mkdir -p ... &&` forms, from `cd <root> &&` and by
absolute path. An unquoted `<<JSON` body with no substitutions is also allowed. `<<-` with tab-indented body and delimiter
works. A `<<` (no dash) delimiter indented by a tab correctly does not terminate. Two heredocs on one line are read in order.
An unterminated heredoc runs to the end. `cat <<'EOF' > path` and `cat <<'EOF'>src/auth.py` are judged by their redirect
target. An escaped `\EOF` counts as quoted. A line `EOFX` does not terminate, and a CRLF delimiter does.

Correctly refused: the main thread's heredoc into a verdict path (`cat >` and `tee`), the same heredoc into `src/auth.py`
from any reviewer, and a command on the line after the delimiter for every role, including after two heredocs, after `<<-`,
and after `; git push` on the marker line. `$(...)` and backticks in an unquoted body are judged, so Markdown code spans
under `<<EOF` are refused. `$((1<<2))` and `(( x = 1<<2 ))` are not mistaken for heredocs. A `<<` inside double quotes or a
comment is ignored. A heredoc inside `$(...)` with a plain body is parsed correctly, including a following `git push`. An
unknown first word's refusal quotes the judged command in backquotes and names the quoted-heredoc form.

**drive.py end.** Every status runs the hygiene checks. A blocked run with STATE.md and REPORT.md uncommitted, or with STATE.md
edited after its commit, is refused, naming the paths. A committed blocked run closes as stopped with `payment:` or
`credentials: CLOUDFLARE_API_TOKEN ...`. A done run is refused with an untracked `notes.txt` and closes clean. A stopped run
(all Missing) and an aborted run (`Decision: Abort; ...`) are refused with an untracked file and close once it is removed. A
stalled run (seven Stop calls, message naming STATE.md apart from `updated:`, STATUS.md, HEAD and the working tree) is
refused until STATE.md and REPORT.md are committed, then closes.

**Voids.** No void for: untracked files appearing, changing and disappearing (one `SNAPSHOT NOTE`), a main-thread Edit
recorded by `hook-guard`, a main-thread Bash edit recorded by `hook-guard`/`hook-post`, a maker's Bash edit through the
hooks, the main thread committing a maker's untracked file or a start-dirty tracked file through the hooks, a foreign commit
touching only `.drive/`, or a tracked file deleted and restored identically. Voided: an unrecorded tracked change
(`src/auth.py`), a foreign commit touching `src/` (`by commits the main thread did not make`), and an outside amend with a new
message (`by a rewrite`). An amend with no change in the same second yields the same sha and rightly does not void.

**Marker and git clean.** Covered under L2. Dry runs stay allowed: `git clean -nX`, `-n -X`, `--dry-run -fdX`. Reading and
copying the baseline stays allowed. The lost-marker warning fires once per session as a `systemMessage` and on stderr. A
second stop in the same session, from a subdirectory `cwd`, is silent. A new session warns again, and a `verifying` STATE
warns too.

**Stopped-run audit.** A stopped run with a Scaffold row fails `lint --final` for a missing audit. Dropped plus Missing needs
none. A signed no-go audit fails as "not a go", and `drive.py end` refuses the run. A signed go passes. The go fails again
as "predates the latest code commit" once a later code commit lands.

**Main-thread git.** Refused: every `git stash` form other than `list` and `show` (pop, apply, save, `-p`,
`--include-untracked`, drop, clear, create, `-C src`, `cd src &&`, `env`, `command`, `GIT_TRACE=1`, and an alias to stash);
`git clean -fd`, `-i`, `-f -- src`; every amend spelling; `git rebase -i`. Allowed: `git stash list`, `git stash list --all`,
`git stash show`, `git stash show -p stash@{0}`, `git clean -n`, `-nfd`, `--dry-run`, a plain commit, and in a scratch clone
`git -C <copy> stash`, `clean -fdx`, `commit --amend`, `cd <copy> && git stash && git clean -fdX`, and
`--git-dir/--work-tree`.

**install.sh and models.** Covered under L4. `skill/scripts/tests/test_model_ids.py` passes (9 tests), and
`skill/scripts/tests/test_adversarial_review.py` passes (24 tests) as a control. Every agent pins `claude-opus-5`,
`claude-sonnet-5` or `claude-fable-5-1`. Launch lines pass only `--model claude-fable-5-1`, and per-call overrides in the
references are only `"opus"`, which the test permits. No other model is selected.

**Docs.** SKILL.md, the references, the agent files and the README agree with research/35 on:

- commit before `lint --final` and `end` (SKILL.md 328 to 333 and 350, `state-files.md:400-410`,
  `definition-of-done.md:233`, `long-running.md:422`)
- the two void causes and untracked files never voiding (`verification.md:209-228`, `state-files.md:173-189`, verifier,
  auditor and security-reviewer agent files, README line 140), with no test-artifact cause left in the recovery advice
- quoted delimiters in every reviewer example, and the unquoted-body warning (`verification.md:186-191`)
- the `credentials:`, `budget:` and `Abort` token wording, and the template's examples
- the stash, clean and amend refusals (SKILL.md 240, `parallel.md:286`, `intake.md:536`, `testing.md:264`)
- marker protection (`state-files.md:125`)
- the provider rule (`models.md:26-36`)
- "enabled or loaded" in install.sh's closing text

The only wording at odds with the code is L6. `verification.md:187-190` states that "any command on a line after the
delimiter" is judged. The code does this except in the H1 and H2 cases, and that sentence becomes true once they are fixed.
