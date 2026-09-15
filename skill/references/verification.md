# Verification

Read this file before building any verifier handoff, before accepting or rejecting a verdict, before
a reviewer's blocking gap reaches a maker, when writing or amending a rubric, when a maker and a
verifier disagree, before trusting a grader's batch, and before the final audit. It decides who may
judge what, what a verifier receives and must never receive, how isolation is enforced, what makes a
verdict valid, which review layers run in which order, how a blocking gap is refuted before it
blocks, how fix-and-verify loops converge and stop, how findings are reconciled, what counts as
evidence, how rubrics are written, how cheap graders are watched, and who runs the final audit, whose
checklist lives in `references/definition-of-done.md` section 6.

## Contents

1. Roles
2. The handoff contract
3. Enforcement
4. Verdicts and the transcript block
5. Layers and their order
6. Loop control: refutation, convergence, disputes
7. Reconciling findings
8. Recall and measurement honesty
9. Evidence and proof layout
10. Rubric design
11. Grader placement, canaries, and blind re-grades
12. Process criteria and rubric gaps
13. The final audit
14. Excuses and rebuttals
15. Red flags

## 1. Roles

| Role | Agent | Writes | Purpose |
|---|---|---|---|
| Maker | `drive:implementer`, `drive:writer`, `drive:designer`, `drive:architect` for its own documents | code, the tests the plan assigns to makers, prose, contracts | builds the thing |
| Severe tester | `drive:severe-tester` | tests and fixtures; under `.drive/proofs/` only `severe*.md`, `commands.log`, and files under `red/` | at M and above writes each claim's refutation test before implementation (frozen, `references/testing.md` section 9); after gates pass, writes tests that try to refute each claim |
| Verifier | `drive:verifier` | command output and its own `verdict.json` under `.drive/proofs/<key>/r<n>/`; scratch under `/tmp`; in a final-audit checklist or close check, the one `.drive/reviews/` file its brief names | decides holds or refuted per claim, with evidence |
| Refuter | a fresh `drive:verifier` in refutation mode, never the agent that raised the gap or the verifier that wrote the verdict | `.drive/proofs/<key>/r<n>/refute-<gap id>.json` | tries to disprove a reviewer's blocking gap before the maker sees it (section 6) |
| Mechanism confirmer | a fresh `drive:verifier` in confirmation mode | `.drive/proofs/<key>/r<n>/confirm-<hypothesis>.json` | removes and re-introduces a proposed cause (`references/shapes/fix.md`) |
| Conformance grader | `drive:grader` | only the output file its brief names | does the artifact match the rubric; STATUS against proofs; docs against code; citations |
| Blind re-grader | a fresh `drive:verifier` | the one `.drive/reviews/` file its brief names | re-grades a sample of grader passes without seeing the first answer (section 11) |
| Security reviewer | `drive:security-reviewer` | `.drive/reviews/<date>-security-<slug>.md`; no file at XS | weaknesses at trust boundaries, described without attack material |
| UI reviewer | `drive:ui-reviewer` | captures under `.drive/proofs/<key>/r<n>/` and `.drive/local/ui/`; in a close check, the one `.drive/reviews/` file its brief names; never the final audit | rendered UI against the design contract |
| Arbiter | `drive:auditor` | nothing; you write the dispute file and the DECISIONS.md entry | rules once on a dispute, including a frozen-test dispute |
| Final auditor | `drive:auditor`, or a fresh `drive:verifier` where section 13 does not require the auditor; never the grader | `.drive/reviews/<date>-final-audit.json` | go or no-go before Done |

You, the orchestrator, schedule checks, filter findings, and record results. You never certify your
own work, and having watched the makers you never grade them.

One agent never holds two roles for the same claim. Every role is a fresh spawn: the severe tester
that wrote a claim's tests does not verify that claim, the reviewer that raised a gap does not refute
it, the auditor instance that arbitrated a dispute does not perform the final audit, and a verifier
never writes tests, so the tests it runs were not written to pass its check.

## 2. The handoff contract

Build `.drive/handoffs/<unit>.md` from `templates/handoff.md`, using files only, never any agent's
message. `<unit>` is a STATUS key or a package id. A later round may name its handoff
`.drive/handoffs/<unit>-r<n>.md`, with n the first number of its `round:` field, so earlier rounds'
handoffs stay.

| Field | Taken from |
|---|---|
| goal | the goal line in GOAL.md |
| skill directory | the absolute path of the skill directory, so the agent can read the references its file names |
| spec | the SPEC.md sections for the claim keys (HUNT.md's brief for a fix, MIGRATION.md's invariants for a move, the questions in RESEARCH.md for a report) |
| claims | each key with its claim words and its "What would prove this wrong" line: what must be true |
| rubric | `.drive/rubrics/<shape>.md` and the commit that froze it |
| scope | the commit range `<base>..<head>`, the absolute checkout path, the changed files from `git diff --name-only <range>`, and for a fix the pre-fix sha, which the verifier exports itself (`references/testing.md` section 11), never a tree path |
| validation | the exact build, typecheck, lint, test, and live commands from GOAL.md's probe |
| frozen | whether `.drive/frozen.txt` exists, and the range base for `drive.py freeze check` |
| evidence inputs | test paths, `severe:` tests, captures: inputs to re-run, never proof |
| lessons | the "Lessons that apply to this task" list from the maker's brief, for compliance |
| previous gaps | the prior round's `verdict.json` path and its dispositions file, or `none` |
| round | `n/K`, and for a later round the scope from section 6 |
| output | `templates/verdict.schema.json` and the proof directory for this round |
| budget | a tool-call budget and the call by which the verdict is written, well below the verifier's `maxTurns` (60 calls, verdict by call 50, for its 80 turns); one verdict per handoff, with no more claims than can each get a refutation inside the budget, about eight as a starting size |

The verifier never receives the maker's transcript, summary, report prose, `honest_gaps`, or
self-assessment; any assertion that a claim holds ("tests pass", "fixed the race", "I made the cache
safe"); your opinion of quality or urgency, or the run's remaining budget; or any request to be quick,
lenient, or confirmatory. The budget line is the verifier's own limit, not the run's: without it a
verifier that reaches its turn limit ends with no verdict, while with it an unfinished claim is written
as `unverifiable`. "The cache must be safe under concurrent writes" is contract and belongs in the handoff.
"I made it safe" is a conclusion and never does. A `/code-review` finding enters only as a previous gap
with its location, never with its argument.

The verifier's prompt opens with the reason line from SKILL.md section 6, then says: "Verify every
claim in the handoff against the scope. Run the validation commands yourself. Attempt to refute each
claim. If you are uncertain whether a claim holds, it does not hold. Report every gap you find with
its confidence and severity; filtering happens afterwards. Write the verdict to the path in the
handoff and return the status line, that path, the counts, and the model you ran as." Never ask for
reasoning; ask for conclusions with evidence.

## 3. Enforcement

- **Fresh agents, never forks.** Spawn a new `drive:verifier` with the Agent tool for every round,
  every refutation, and every re-grade. Never use `context: fork`, the fork agent type, `SendMessage`
  into a maker, or a resumed verifier from an earlier round.
- **Read-only tools.** The verifier, grader, and auditor have `Read, Grep, Glob, Bash`; the security
  reviewer adds `Skill`. Edit, Write, NotebookEdit, and Agent are disallowed.
- **Plugin guards.** `drive.py hook-guard` runs on every Bash, PowerShell, Monitor, Edit, Write,
  NotebookEdit, and MultiEdit call while `.drive/local/active` exists, applies the rule for the calling
  agent, and refuses EnterWorktree. Only
  an agent spawned as `drive:<name>` gets its role's rules; a bare
  `verifier` or any other subagent gets the main thread's rules. Every agent and the main thread are
  refused writes, deletes, moves, and in-place edits of frozen tests, `.drive/frozen.txt`,
  `.drive/frozen.sha256`, `.drive/local/frozen-parked/`, `drive.py`, and `hooks.json`, writes to the
  provenance ledger or a Claude Code transcript, and drive's hook commands run by hand. The main thread may not write a JSON file
  under `.drive/proofs/` or `.drive/reviews/`, any `verdict.json` or `proof.json`, or anything under
  `.drive/local/ro/`, may not delete or move anything under those directories, and may not run inline
  code or a script that names them. A tool call whose hook input cannot be read is refused while a run
  is active. A violation exits 2 with a plain reason.

  Read these refusals for what they are. The guard runs as the same user, in the same shell, as the
  session it watches, so no command filter can prevent deliberate tampering, and a command written to
  hide what it touches can get past it. The guard's job is to make honest mistakes and shortcuts fail
  loudly at the moment they happen. Tampering is caught afterwards: provenance, below, counts evidence
  only when the reviewer's own transcript shows the write, and `drive.py freeze check` catches a
  changed frozen test through its recorded hash. Never look for a way around a refusal; a refusal that
  blocks legitimate work is a finding, recorded in STATE.md with the refused command.
- **Reviewer command shapes.** `drive:verifier`, `drive:grader`, `drive:auditor`,
  `drive:security-reviewer`, and `drive:ui-reviewer` run only allowlisted command shapes. After leading `VAR=value` assignments and wrappers (`env`,
  `sudo`, `nohup`, `nice`, `timeout`, `xargs`, `npx`, `pnpm dlx`, `npm exec`, and the like) are
  stripped, each simple command's name must be on this list or be the first word of a command the
  project records: GOAL.md's build, focused-test, and full-suite commands, and CONSTRAINTS.md's
  enforced and measured-only commands. A command not on either list is refused, so the orchestrator
  records a check a reviewer needs as one of those commands. The security reviewer may also run a
  secret scan in two forms, `gitleaks detect --redact --no-git --source <path>` and
  `gitleaks detect --redact --source <path> --log-opts <range>`, with only read-only flags, a range
  written out, and `--report-path` under `.drive/reviews/` or a scratch directory; every other
  gitleaks form is refused, and where gitleaks is not installed it uses the grep fallback in
  `references/security.md` section 8.

  | Kind | Commands |
  |---|---|
  | Reading and searching | `cat`, `head`, `tail`, `grep`, `egrep`, `fgrep`, `rg`, `ag`, `ls`, `tree`, `find`, `wc`, `sort`, `uniq`, `cut`, `tr`, `diff`, `cmp`, `comm`, `file`, `stat`, `du`, `df`, `pwd`, `echo`, `printf`, `true`, `false`, `test`, `[`, `date`, `printenv`, `which`, `type`, `basename`, `dirname`, `realpath`, `readlink`, `jq`, `yq`, `sed`, `gsed`, `awk`, `gawk`, `mawk`, `xxd`, `od`, `hexdump`, `base64`, `shasum`, `sha256sum`, `sha1sum`, `md5`, `md5sum`, `cksum`, `column`, `nl`, `fold`, `paste`, `join`, `seq`, `xmllint`, `plutil`, `defaults`, `log` |
  | Shell and system | `sh`, `bash`, `zsh`, `eval`, `source`, `.`, `cd`, `pushd`, `popd`, `set`, `export`, `unset`, `read`, `wait`, `exit`, `return`, `local`, `declare`, `sleep`, `time`, `timeout`, `gtimeout`, `ps`, `pgrep`, `lsof`, `uname`, `sw_vers`, `id`, `whoami`, `hostname`, `nproc`, `sysctl` |
  | Files, with writes still confined | `tee`, `mkdir`, `touch`, `cp`, `mv`, `rm`, `rmdir`, `ln`, `tar`, `unzip`, `zip`, `gzip`, `gunzip` |
  | Git and network | `git`, `gh`, `curl`, `wget`, `dig`, `nslookup`, `ping`, `openssl` |
  | Interpreters and package managers | `python`, `python3`, `node`, `deno`, `bun`, `ruby`, `perl`, `php`, `npm`, `npx`, `pnpm`, `yarn`, `bundle`, `gem`, `pod`, `composer`, `mix` |
  | Builds, tests, and linters | `make`, `gmake`, `pytest`, `jest`, `vitest`, `mocha`, `playwright`, `go`, `cargo`, `cargo-nextest`, `rustc`, `swift`, `swiftc`, `xcodebuild`, `xcrun`, `gradle`, `gradlew`, `mvn`, `dotnet`, `rake`, `rspec`, `tsc`, `eslint`, `prettier`, `ruff`, `mypy`, `black`, `flake8`, `pylint`, `golangci-lint`, `swiftlint`, `tox`, `nox`, `coverage`, `lighthouse`, `agent-browser` |
  | Platforms, media, and research | `wrangler`, `terraform`, `kubectl`, `docker`, `helm`, `pulumi`, `aws`, `gcloud`, `vercel`, `netlify`, `firebase`, `fastlane`, `twine`, `screencapture`, `sips`, `magick`, `ffprobe`, `tvly` |

  Being on the list is not enough. A shell's `-c` string, `eval`, a sourced or path-named script, an
  `npm`, `pnpm`, `yarn`, or `bun` package script with its pre and post scripts, and a make recipe are
  checked command by command. `make` runs only the targets `test`, `tests`, `check`, `lint`, `build`,
  `verify`, `ci`, `typecheck`, `type-check`, `fmt-check`, `format-check`, `all`, or one the project
  records. `awk` runs without `-f`, output redirection, `system()`, or a piped `getline`; `sed` without
  `-f` or its `w`, `W`, and `e` commands. `python -m` runs only `unittest`, `pytest`, `json.tool`
  (which may print but not write an output file), or a module a recorded command runs. Formatters and
  linters run only in their check form, in scripts too: `prettier --write`, `eslint --fix`,
  `ruff --fix`, `ruff format` or `black` without `--check` or `--diff`, `gofmt -w`,
  `golangci-lint --fix`, `swiftlint --fix` or `autocorrect`, `cargo fmt` without `--check`,
  `cargo clippy --fix`, and `go fmt` are refused. `git` runs only read-only subcommands and the listing forms
  of `branch`, `tag`, `stash`, `worktree`, `config`, `remote`, and `reflog`, plus `git archive` into an
  allowed path, `git clone` into a scratch directory, and work inside a scratch directory; an alias is
  expanded before it is judged and `git -c alias.*` is refused. In every worktree whose common git
  directory is this repository's (or whose directory the guard cannot know), detached ones under a
  scratch directory included, neither an agent nor the main thread creates, renames, copies, or
  force-moves a branch, creates or deletes a tag, runs `update-ref` on `refs/heads/` or `refs/tags/`
  (or with `--stdin`), moves HEAD with `symbolic-ref`, or runs `checkout -b`, `switch -c`, or
  `--orphan`, because a linked worktree shares the repository's refs; a detached worktree takes
  read-only commands and commits on its detached HEAD. A separate clone has its own refs and may
  branch. `git push` is refused for every role and the main thread, from every directory, with no
  exception. The write verbs of `gh pr` (create, merge, close, comment, review, edit, ready, reopen),
  `gh release` (create, upload, delete, edit, delete-asset), and `gh repo` (create, delete, edit,
  rename, archive, unarchive, fork, sync, set-default, deploy-key) are refused to the main thread
  unless a `deploy` plan line in GOAL.md names the command, as in `- [ ] deploy · artifact: the
  GitHub release · exit: gh release create v1.2.0 published · checker: verifier`. Neither an agent nor
  the main thread runs `git worktree add` with `-b`, `-B`, or `--orphan`, or without `--detach` and a
  path in a scratch directory, even from inside a scratch directory, because a linked worktree shares
  the repository's branches; only the main thread may name that path through a variable. No drive agent deploys or publishes:
  `wrangler deploy` and its other remote writes (a `--local` D1 migration is allowed), `npm publish`,
  `gh pr create`, `gh release create`, `gh workflow run`, `gh api` with a write method, `terraform
  apply`, `kubectl apply`, `docker push`, `fastlane`, and the rest of drive.py's deploy list are
  refused, and so is a make target named `deploy`, `publish`, `release`, `ship`, or `push`. Inline code
  (`python3 -c`, `node -e`, or a script under a scratch directory or `.drive/`) runs only when it can
  just read and print: Python may import only standard modules such as `json`, `re`, `math`,
  `collections`, `datetime`, `hashlib`, `csv`, `glob`, and `os` and may not open a file for writing or
  call a function that writes, deletes, or starts a process; JavaScript may not use `require`,
  `import`, `process`, `fs`, `eval`, or `fetch`; inline Perl and Ruby are refused. The UI reviewer may
  also import PIL and numpy to crop and pixel-diff images, and write crops, diff images, and results
  only to constant paths under `.drive/proofs/` or `.drive/local/ui/`; numpy's memory maps, pickle
  loading, and text loaders and PIL's image viewer stay refused. A
  script inside the skill directory, such as `scripts/geometry-probe.js`, runs as is, and any other
  project script is refused only when its text runs a git command that changes the repository or a
  deploy. Writes (redirects, `tee`, `cp`, `mkdir`, `touch`, extraction, `curl -o`) land only under
  `.drive/proofs/` and `.drive/reviews/`, plus `.drive/local/ios/` for the verifier and
  `.drive/local/ui/` and `.drive/local/ios/` for the UI reviewer, or in a scratch directory
  (`/private/tmp`, `/tmp`, or `$TMPDIR`); deletes and moves happen only in a scratch directory.
  Reviewers write evidence with a Bash heredoc whose delimiter is quoted, such as
  `cat > .drive/proofs/<key>/r<n>/verdict.json <<'JSON'`. The guard judges the command line,
  including its `>` target, and any command on a line after the delimiter (a here-string, `<<<`, has
  no body), but not the lines of a quoted heredoc's body fed to `cat` or `tee`. A body a shell reads
  on standard input (`bash <<'EOF'`, `sh -s <<'EOF'`, `cat <<'EOF' | bash`, and `bash < file`) is
  judged as the commands it runs, and a body an interpreter reads (`python3 - <<'PY'`, `node -`)
  gets the same inline-code checks as `-c` and `-e`. Under an unquoted delimiter (`<<JSON`) bash expands `$(...)` and backticks
  in the body, so the guard judges those substitutions as commands, and a Markdown review with
  backticked code spans is refused. A refusal quotes the simple command the guard judged.
- **Provenance.** When a verifier, UI reviewer, grader, auditor, or security reviewer finishes, the
  SubagentStop hook records, in a ledger outside `.drive/` (`references/state-files.md` section 2),
  the sha256 of each JSON file under `.drive/proofs/` and `.drive/reviews/` that changed during the
  review and that the agent's own transcript (the hook input's `agent_transcript_path`) shows a
  successful tool call writing, with that transcript's path and sha256. A shell write counts only
  when its command names the file's repository-relative path (`.drive/proofs/<key>/r<n>/verdict.json`)
  or absolute path, so every reviewer writes evidence from the repository root with the full path in
  the command; `cd .drive/proofs/<key>/r<n> && cat > verdict.json` leaves the file without
  provenance. Claude Code deletes transcripts after `cleanupPeriodDays` (30 days by default), and from
  then on the evidence they backed stops counting (`references/state-files.md` section 2). An entry counts only when the transcript exists, belongs to the
  recorded agent type, still has its recorded hash, and contains that write; the lint re-checks each of
  these, so a hand-appended entry or a hook command run without such a transcript never counts. This
  makes tampering evident, not impossible. The lint counts a verdict only from `drive:verifier` or `drive:ui-reviewer`, a final audit only from
  `drive:auditor` or `drive:verifier`, a live proof only from `drive:verifier` or
  `drive:ui-reviewer`, a citation check only from `drive:grader`, and a refutation only from a
  `drive:verifier` other than the verdict's author, each unchanged since that agent stopped. A verdict
  you write, copy, or edit never counts.
- **Tree snapshot and voids.** The same hooks record HEAD and the tracked paths with uncommitted
  changes outside `.drive/` when a read-only reviewer starts, and compare them when it stops. A review
  is voided in exactly two cases. The first is a tracked file outside `.drive/` modified or deleted
  during the window when no hook recorded that path as an edit since the window opened. The hooks
  record every Edit, Write, NotebookEdit, and MultiEdit call by the main thread or a non-reviewing
  agent, and every file a Bash or PowerShell call by either changed before that call returned while a
  reviewer ran. So a recorded maker or main-thread edit never voids a review, and neither does a
  tracked file dirty at the start that the main thread commits unchanged; an unrecorded change does,
  whether it is the reviewer's own, a background command, server, or watcher writing after its call
  returned, or another process. The second is HEAD rewritten (the old HEAD is no longer an ancestor)
  or moved by commits the main thread did not make, apart from commits that touch only `.drive/`.
  Untracked files that appear, change, or disappear during the window never void it, and neither does
  staging a file that was untracked at the start, while a tracked file removed from the index
  (`git rm --cached`) counts as deleted; the hook logs untracked files in `gate.log` as `SNAPSHOT NOTE <role> <agent>: untracked path(s) ...`, and `lint --stop` and
  `--final` report any the run leaves uncommitted. On a void the hook never blocks the reviewer; it
  voids the review in the ledger, logs `SNAPSHOT VOID` with the changed paths in `gate.log`, and
  writes `.drive/local/ro/<agent>.void`, and the lint refuses any evidence written during that window,
  naming the changed paths. When `gate.log` shows `SNAPSHOT VOID`, read the paths it names first. When
  a background process wrote one, stop that process; when a command the reviewer runs rewrites a
  tracked file every time, a fresh reviewer would be voided the same way, so untrack that file
  (`git rm --cached`) and add it to the ignore file in its own commit. Then restore the tree, add an
  Open failure to STATE.md, and spawn a fresh reviewer on a still tree.
- **Verify the maker's tree in place.** Verification follows integration: path audit, wiring, gates,
  per-package commits, the orphan audit, and only then the verifier, on the shared checkout at the
  committed range with `git status --porcelain` empty. For an experiment or hypothesis arm, the scope
  is the arm's worktree path, verified before it is landed or removed.
- **Never a verifier worktree.** A subagent started with `isolation: worktree` branches from the
  default branch and never sees the maker's work. Disposable copies for mutation checks and for the
  pre-fix check are `git archive` exports under `/tmp/drive-*`, removed before the verifier returns.

## 4. Verdicts and the transcript block

The schema is `templates/verdict.schema.json`: `verdict` (`pass`, `fail`, `blocked`), `unit`,
`round`, `scope`, `ran`, `claims` (each with `status` of `holds`, `refuted`, or `unverifiable`,
`oracle`, `refutations_attempted`, `evidence`, `confidence`, and its own `rung_supported`), `gaps` (severity `blocking`,
`should_fix`, or `note`, with `where`, `repro`, and `confidence`), `harness_kindness`, `not_checked`,
`rung_supported`, and `for_maker`. The verifier saves command output with `tee` under
`.drive/proofs/<key>/r<n>/` and writes `r<n>/verdict.json` itself; you validate that file against the
rules below before any STATUS change, and `drive.py lint` checks its provenance.

Apply these rules before recording anything:

- A `pass` needs `ran` to include the project's full-suite command, run by this verifier in this
  round, at exit 0, unless the run has no suite (GOAL.md's probe records `test_command: none`, or the
  shape is `report` or `operate`); every claim `holds` at confidence 75 or above with at least one refutation attempt; no
  confirmed blocking gap after filtering and refutation; a clean `drive.py freeze check` when the run
  has frozen tests; every `harness_kindness` entry resolved or at `note`; and a `rung_supported` the
  evidence reaches.
- A `pass` that ran no commands, leaves a claim without a refutation attempt, or reports a number with
  no source is malformed. Reject it and spawn one fresh verifier with the handoff plus one sentence
  saying why the previous verdict was rejected, never what to conclude. A second malformed verdict
  becomes an Open failure, and the rung stays where other evidence puts it.
- A `fail` whose only blocking gaps each have a `refute-<gap id>.json` beside it with `result`
  `refuted`, written by a `drive:verifier` the ledger records that is not the agent that wrote the
  verdict, with a gap `id` made of letters, digits, dots, underscores, and hyphens, and which meets
  every other pass rule,
  counts as a pass for its rung. No agent edits the original verdict to say so, and no round is spent.
- `blocked` means the verifier could not execute. Repair the environment, not the maker's work, and
  re-verify without spending a round.
- `unverifiable` never counts toward a pass. The claim keeps the rung other evidence supports, and the
  missing input is named in STATE.md.
- Each claim carries its own `rung_supported` for its STATUS key. The lint takes a claim's own value
  over the verdict's top-level `rung_supported`, which it falls back to when the claim names none, and
  reads a claim's `Done` as Operational, because a verdict never grants Done; the top-level value is
  never `Done`. The final audit's `claims[]` carries one for each sampled row.
- `rung_supported` of Live Proof needs a command in `ran` against the real environment (deployed URL,
  device, or real database) with its output in `live.md`, and a `proof.json` written by the verifier
  or UI reviewer with every field the lint reads: `key` (the STATUS key it proves), `claim`,
  `environment` `live` or `device`, a `target` that is not local, the `commit`, `verdict` `pass`,
  `produced_by` `verifier` or `ui-reviewer`, `commands` as a list of `cmd` and `exit` pairs,
  `artifacts` as a list of `path` (a file beside `proof.json`) and `sha256` pairs, and a
  `shim_differences` list, which when empty needs a `shim_differences_note` saying why no double is
  involved.

Confidence uses one scale everywhere: 100 demonstrated in the real runtime with captured evidence; 75
reliably reproduced under realistic conditions against an independent oracle; 50 reproduced under
contrived conditions; 25 speculative; 0 inapplicable.

After every gate run and every verification round, print the transcript block in SKILL.md section 5,
which is its only copy. Fill it only from gate exit codes and a validated verdict file, one `GAPS` line
per confirmed gap with blocking gaps first. Before a round's verdict exists, `VERDICT` reads `pending`.

## 5. Layers and their order

Deterministic checks come first because reviewing red code wastes a round. Reviews that need green
code come next, then the expensive judgment passes, then simplification, which edits and therefore
re-gates, then the final audit. Each step starts only after the previous one is green.

| Step | Who | Runs when |
|---|---|---|
| 1. Gates: build, typecheck, lint, tests, `drive.py guard --base <baseline_sha>`, `drive.py freeze check` | you, by Bash | always; red goes back to the maker without spending a round |
| 2. Correctness | `drive:verifier` on the handoff; on existing code a `drive:security-reviewer` in its code-review mode runs `/code-review <level> <baseline_sha>...HEAD` in parallel, never you | always for code; level `medium` for every `fix` and for any run at S, `high` otherwise; never omit level or range; never `--fix`, `--comment`, `--post`, or `ultra` |
| 3. Conformance | `drive:grader` against the frozen rubric, with a canary in every batch | `feature`, `build`, `move`, `publish`, `report` |
| 4. Severe testing | `drive:severe-tester` | any unit with behavioural claims, including one test on an adjacent input for a fix at S; heavier for identity, money, data, files, network, untrusted input, concurrency |
| 5. Security review | `drive:security-reviewer`, which checks the range is non-empty and then invokes the Skill tool with `security-review` itself | the `auth` trait or any of those surfaces; never in your own context |
| 6. UI review | `drive:ui-reviewer` | the `ui` trait |
| 7. Refutation | a fresh `drive:verifier` per gap or small group of gaps (section 6) | every blocking gap from steps 2 to 6 that section 6 sends to refutation, before any maker sees it |
| 8. Simplify | a `drive:implementer` under a package brief that owns the paths touched since baseline runs `/simplify <those paths>`; you then run the gates and commit, and the grader compares test names and pass counts | after verdicts pass; skipped at XS, for every `fix`, and for `move` before cutover is proven; reverted if the test baseline changed |
| 9. Docs review | `drive:grader` checks every documented behaviour against code and tests; the owning `drive:writer` fixes what it finds | docs changed, or `build` |
| 10. Final audit | `drive:auditor`, or a fresh `drive:verifier` (section 13); never the grader | before any row becomes Done, before the run ends `done`, and before it ends `stopped` with any row above Missing |

Code-review findings are inputs for you, never a STATUS evidence token: the security reviewer that ran
`/code-review` writes them as a Markdown report under `.drive/reviews/` through a quoted heredoc, by
class and location, never with exploit material. Dismiss each finding with a reason, send it to
refutation and then to the owning maker as a fix item, or add it to the next handoff's previous gaps
when it names a claim key. Run two verifiers with distinct lenses, both of which must pass, when a
unit's diff exceeds about 800 changed lines, when a claim carries money or auth, and at a move cutover
(one for parity, one for operability and rollback).

## 6. Loop control: refutation, convergence, disputes

**Round bounds.** SKILL.md section 5 sets these bounds; this table, `references/parallel.md` section 4,
and the shape files repeat them and must agree with it.

| Shape | Verification rounds |
|---|---|
| `fix` | 2 |
| `feature`, `report` | 3 |
| `publish` | 3 per gated phase |
| `build` | 3 per milestone, plus 2 for the final integration |
| `move` | 4 at cutover, 3 for every other gated phase |
| `operate` | 2 per observed step |

Within a round, the maker gets at most three gate-fix cycles. Gates still red after the third become a
blocking gap with the failing output attached, and the round counts as failed.

**Refutation before a gap blocks.** A reviewer that is told to find problems finds some that are not
there, and a maker that fixes a false finding adds real defects. So a blocking gap reaches a maker only
after a fresh agent has tried and failed to disprove it.

- Send to refutation every blocking gap raised by `drive:security-reviewer`, by `drive:ui-reviewer`
  from vision alone, by `drive:architect` or `drive:auditor` in a spec or design review, by a review
  panel lens (`references/parallel.md` section 13), or by `/code-review`; and a verifier's own blocking
  gap whose confidence is below 75 or whose `repro` is empty.
- A gap backed by a measurement confirms itself and skips refutation: an objective UI check's result
  file, a failing command the verifier ran with its output saved at confidence 75 or above, a
  `drive.py freeze check` or `drive.py guard` finding.
- The refuter is a fresh `drive:verifier` in refutation mode, never the agent that raised the gap and
  never the verifier whose verdict holds it, because the lint counts a refutation only from a
  different verifier. Its
  brief holds the gap's fields verbatim (id, claim, severity, where, what, repro, confidence), the
  artifact at its commit, and the tests, configuration, schema, and migration files around the
  location; never the reviewer's argument beyond those fields and never the maker's reasoning. One
  refuter may take up to five gaps from the same report when they share a location.
- The refuter restates the gap as "If <precondition>, then <observable wrong outcome>", tries the
  smallest check that would show the outcome (executing before reading), looks for the guard the
  reviewer may have missed (upstream validation, a schema constraint, a unique index, a type,
  middleware, an idempotency key), and writes `.drive/proofs/<key>/r<n>/refute-<gap id>.json`:
  `result` (`confirmed`, `refuted`, `unsettled`), `proposition`, `evidence` (commands with exit codes
  and output paths, or file and line for each step or for the guard found), `guards_checked`,
  `severity_check` (`keep`, `raise`, `lower`) with a reason unless `keep`, `pre_existing` (true when
  the location is code the unit did not change), and for `unsettled` the check that would settle it.

| Result | What happens |
|---|---|
| `confirmed` | the gap blocks and goes to the maker with the refuter's evidence; a severity change applies only with its reason |
| `confirmed`, `pre_existing` | it never blocks this unit; it becomes an Open failure or a follow-up in REPORT.md |
| `refuted` | dismissed with the refutation's path in the dispositions file; the maker never sees it as work |
| `unsettled` | it cannot block; it is carried into the next round's previous gaps as `should_fix`. For a security, money, or data-loss gap, one more fresh refuter runs; if still unsettled, REPORT.md lists it as an unverified risk |

Watch the refuters as you watch the graders: re-refute one `refuted` gap in three, and at least one per
run, with another fresh verifier that does not see the first result. A disagreement sends every later
refutation in the run to two refuters, and a gap stays blocking unless both refute it.

**Dispositions.** Keep `.drive/reviews/<date>-dispositions-<unit>.md` with one row per gap per round:
round, gap id, severity, defect class (a short slug naming the mechanism, such as
`zero-row-write-treated-as-success`, never the location), refutation result and path, and exactly one
disposition: `fixed` (commit and the test that fails without it, checked against the original repro,
not only the fix's own new test), `refuted` (the refutation path), `accepted` (a DECISIONS.md entry;
never for a blocking gap, whose claim stays below Done), or `carried` (the next round). A disposition
that silently narrows a gap is itself a gap.

**Convergence.** Only confirmed blocking gaps start another round. Batch `should_fix` gaps into that
round's fix, or into one final pass when no blocking gap remains. Notes stay in the verdict file, are
listed in REPORT.md, and never re-enter the loop. The maker receives the confirmed gaps and
`for_maker`, never the verdict's prose.

- **Close on severity, not count.** A unit closes when a round has no confirmed blocking gap. Zero
  findings is not the stop condition, and a round that finds only `should_fix` gaps does not start
  another.
- **Scope later rounds to the fix.** From round two, the handoff's scope is the fix diff since the
  last verified commit, the direct callers and consumers of the changed symbols, and each earlier
  gap's repro. A full-unit re-review needs a stated reason in the handoff, such as a fix that changed
  more than about a third of the unit's lines.
- **The same gap twice is a wrong diagnosis.** When a blocking gap matches one from an earlier round by
  claim key and location, stop changing code. Open `.drive/investigations/<date>-<slug>.md` from
  `templates/investigation.md`, usually with `drive:investigator`, and change nothing until it names a
  mechanism.
- **The same class twice is a design problem.** When the same defect class is confirmed in two
  consecutive rounds, at any location in the unit, stop patching. Open an investigation of the
  mechanism that produces the class, with `drive:architect` reviewing the affected design section when
  the mechanism is a design choice. The unit stays open until the investigation's fix lands.
- **Late findings about the tests call for an instrument audit.** From round three, when more than half
  of the confirmed gaps are about the tests rather than the product (tests that pass for the wrong
  reason, mutants that survive, evidence that overstates what ran, a frozen test with a weak oracle),
  run one instrument audit instead of another round: a fresh `drive:verifier` mutates the line behind
  each claim, checks each oracle is independent of the code, and runs `drive.py freeze check`. Then run
  one scoped re-review.
- A first rejection of work whose own gates were green is a retro candidate, which the retro reads from
  the verdict file; it opens an investigation at once only when no gate the maker ran could have caught
  the gap, because then a gate is missing. After two failed rounds on one package, re-run its
  implementer once with `model: "opus"`.

These rules come from a measured failure of the opposite approach. One long review of a real milestone
ran eighteen rounds. New defects per round stayed between seven and nineteen with no downward trend,
later rounds found defects that earlier fixes had introduced, one defect class returned in three
separate rounds, and the late rounds were mostly about the tests rather than the product. Counting
findings never converged; closing on confirmed severity, scoping re-review to the fix, treating a
recurring class as a design signal, and auditing the tests once would have.

**The rubric** is committed to `.drive/rubrics/<shape>.md` before the first maker starts and is frozen
at handoff. A verifier may fail work only on rubric criteria and the standing floor, which is always in
scope: security, data loss, disabled or weakened tests, a changed frozen test, and a harness kinder
than production. Amend a rubric between units, never during a loop, with a DECISIONS.md entry.

**When the bound is reached** without a pass, set the rung to the last verdict's `rung_supported`,
record the open confirmed gaps under Open failures in STATE.md, and continue with other work or stop.
Never write Done because the rounds ran out.

**Disputes.** A maker may dispute a confirmed blocking gap in its report, with evidence. Write
`.drive/reviews/<date>-dispute-<key>.md` holding the claim, the gap, and the files, commands, and
outputs each side cites, then spawn `drive:auditor` once with that file, the artifact, and the rubric.
It rules `defect`, `not_a_defect`, or `rubric_ambiguous`; on a UI finding, `defect` marks the finding
upheld and `not_a_defect` marks it overruled. You write the DECISIONS.md entry from the ruling; it is
final for the run. For `rubric_ambiguous`, apply the stricter reading and amend the rubric for the next
unit. A dispute about a frozen test follows the same path with the rulings and the amendment steps in
`references/testing.md` section 9; the maker never edits the test while it waits.

## 7. Reconciling findings

Classify every confirmed finding in this order and stop at the first that fits:

1. The claim or contract was unclear. Clarify it in SPEC.md before the next round, with a DECISIONS.md
   entry when the clarification narrows what the claim promises. The round does not count against the
   bound.
2. The finding is valid and needs a change. Send it to the owning maker.
3. The finding is valid but costs more to fix than to accept. Record it in DECISIONS.md with the reason
   and reversal cost. A blocking gap cannot be accepted this way: its claim stays below Done, and the
   report leads with it.
4. The finding is wrong given context the verifier lacked. Add that context to the handoff files for
   the next round. A blocking gap dismissed this way goes to the auditor as a dispute.

If two consecutive rounds produce substantive findings (blocking or `should_fix` at confidence 50 or
above) and you classified none of them as needing a change, you are validating rather than verifying.
Treat that as a failure event and open an investigation. A refuter's `refuted` result is evidence, not
your classification, so it does not count toward this rule. Starting a round on an unchanged range
with an unchanged environment is stalling; never do it.

Mid-build, a non-trivial decision gets a fresh `drive:investigator` second opinion before it lands.
A decision is non-trivial when it changes branching logic, crosses a module or service boundary,
asserts what the compiler cannot check (idempotence, ordering, thread safety), depends on context a
later reader cannot see, or cannot be undone. Write the claim in two or three lines, hand over the
smallest artifact and its contract but never your conclusion, reconcile as above, and stop at trivial
findings, after three cycles, or when the artifact must be decomposed. A step with effects outside git
also needs a written undo before it runs.

## 8. Recall and measurement honesty

Tell every verifier, grader, and reviewer to report every finding with its confidence and severity.
Never tell one to be conservative, to skip nitpicks, or to report only important issues. Filtering is
a separate step you run afterwards: a gap below confidence 50 is never blocking; duplicates across
reviewers are merged by `drive:grader`; refutation decides which blocking gaps stand; the loop admits
only what section 6 allows.

Severity is set by who would notice: `blocking` when a user, an attacker, or the data would;
`should_fix` when a maintainer would; `note` when nobody would but it is worth recording.

Never report a value that was not measured. Write "not measured" with the reason, and label findings
from reading source as potential impact. Label every measured value with its source (local run, lab
run, live request, trace, field data, device) and never present one kind as another. A verdict that
contains an invented number is malformed. Hold "blocked" and "impossible" to the same bar as "works":
check that the credential is really absent or the tool really cannot load.

## 9. Evidence and proof layout

```
.drive/proofs/<key>/
  proof.json              key, claim, environment (local|simulator|preview|staging|live|device), target, commit, verdict (pass), produced_by (verifier|ui-reviewer), commands (cmd, exit), artifacts (path, sha256), latest round, shim_differences (empty needs shim_differences_note)
  red/red.txt             the frozen test's failing output before implementation, and red/commands.log
  r<n>/verdict.json       the validated verdict for round n
  r<n>/commands.log       2026-09-14T10:32:11Z · /abs/checkout · <command> · exit 0 · 41s · r2/tests.txt
  r<n>/*.txt              captured output: first 50 and last 200 lines, under 20 KB per file
  r<n>/refute-<gap>.json  a refuter's result for one gap
  r<n>/confirm-<hyp>.json a mechanism confirmer's two-way result
  r<n>/flake-proof.txt    the PASS n/n or FAIL at run k line, with p, alpha, and reset
  r<n>/shots/             <screen>/<cell>.png, .review.png, .tree.json, crops (layout in references/ui-verification.md section 5)
  r<n>/live.md            real-environment command, URL or device, timestamp, response excerpt
  r<n>/findings.json      UI findings, referenced from the verdict
```

Trim output, never the command line or the exit code. Read in ground-truth order: code and tests (run
them), then proofs, then STATUS, then docs. A disagreement between a higher and a lower layer is a gap
against the lower one: a rung the proof does not support, a doc sentence the code contradicts. A STATUS
rung without its proof is a finding, never a formatting issue. The evidence each rung requires is in
`references/state-files.md` section 7.

## 10. Rubric design

- Write each criterion as an observation, never a property: "returns 201, and a later GET returns the
  same body", not "creates the resource correctly".
- Name the oracle that decides it: a test, an independent reference, an invariant, a normalised diff, a
  permission matrix, a measured score, a capture at a stated size.
- Name the refutation: the observation that would make it false.
- Include at least one user-outcome criterion, verified by driving the artifact, and make it blocking.
- Include what must not happen: a cross-tenant read, personal data in logs, horizontal scroll, a
  disabled test.
- Put hard thresholds on criteria that matter and weights on the rest, so a security failure is never
  averaged away by good typography. Weight toward edge cases, failure paths, and production constraints.
- Derive criteria from a known-good artifact when one exists: say what makes it good, then turn that
  into observations.
- Word criteria concretely for this deliverable. Aspirational superlatives ("world-class", "polished")
  steer makers toward the same generic result and give a judge nothing to check.

Templates live in `templates/rubrics/<shape>.md`. `drive:architect` copies the shape's template to
`.drive/rubrics/<shape>.md` at the spec or test-plan phase, fills the placeholders, deletes trait rows
that do not apply, and you commit it before the first maker starts. The UI rubric,
`.drive/rubrics/ui.md`, has no template: build it from `references/ui-verification.md` section 11 and
commit it at the design gate. Abbreviated examples, one line per criterion as observation · oracle ·
refutation · threshold:

**Backend endpoint** (`POST /projects`):
- Authenticated create returns 201 and a GET returns the same body · integration test in the real local runtime · create as user A, GET as user B returns anything but 403 or 404 · blocking
- Malformed bodies return 400 with the error shape · table of empty, oversized, wrong-type, Unicode, and null inputs · any 5xx · blocking
- One idempotency key under two concurrent requests yields one row · concurrent test · two rows · blocking
- Platform limits hold in tests · limits probe and ledger · a passing test that would fail in production · blocking
- The deployed endpoint agrees with local · request against the deployed URL in `live.md` · mismatch · required for Live Proof

**Native screen** (an item editor):
- A user can edit and save an item and sees it after relaunch · UI reviewer drives the simulator and reads the accessibility tree · save inert or item absent after relaunch · blocking
- Empty, loading, error, and offline states are reachable · state harness captures · a state missing · blocking
- No clipping at the largest text size, in dark mode, or in landscape · capture matrix · a truncated label or overlap · should_fix, blocking if the primary action is hidden
- Every control has an accessibility label · tree inspection · an unlabeled control · should_fix

**Migration cutover** (a service moving into the platform):
- Recorded corpus replays identically · normalised diff of old against new · a difference no named normalizer or Known-wrong behaviour row explains · blocking
- Every public route, config key, error code, and header has a passing parity test · surface extraction plus tests · an item without a test · blocking
- Rollback completes and the corpus passes afterwards · executed drill · rollback fails or leaves state · blocking
- Nothing references the old service after removal · search across repositories and configuration · a live reference · blocking

**Research report**:
- Every factual claim cites a source that says it · grader fetches raw text for the sample `references/research.md` section 12 sets and writes `.drive/reviews/<date>-citations-<slug>.json` · a source that does not support its sentence · blocking
- Each question from the goal has an answer section · mapping · an unanswered question · blocking
- Conflicting sources are shown as conflicting · reading · a contested figure presented as settled · should_fix

**Website page**:
- Renders at 360, 768, 1280, and 1600 px without horizontal scroll · captures and the geometry probe · overflow · blocking
- Zero broken internal links · crawl · any 404 · blocking
- Accessibility and performance measured against the constraints rows · axe and Lighthouse runs · below the recorded floor · should_fix, blocking below the hard floor
- Every product statement matches the repository and RESEARCH.md · claim list against sources · a described feature that does not exist · blocking

## 11. Grader placement, canaries, and blind re-grades

| Check | Agent | Model and effort |
|---|---|---|
| Gates | you, by Bash | none |
| Rubric conformance, evidence completeness, STATUS against proofs, docs against code, citations (`curl` or `tvly extract` raw text), links, deduplication, parity mismatch triage | `drive:grader` | `sonnet`, low |
| Correctness: logic, edge cases, concurrency, boundaries; refutation; mechanism confirmation; blind re-grades | `drive:verifier` | `opus`, high |
| Refutation tests, frozen tests | `drive:severe-tester` | `opus`, high |
| Security | `drive:security-reviewer` | `opus`, high |
| Rendered UI | `drive:ui-reviewer` | `opus`, high |
| Disputes, final audit | `drive:auditor` | `fable`, xhigh |

`sonnet` at low effort suffices where the criterion has a clear oracle and the question is whether the
artifact shows a stated observation. It does not suffice where the failure would look right and be
wrong: nontrivial logic, concurrency, authorization, migration equivalence, UI taste, disputes, and the
final audit. A verifier weaker than its maker is effectively self-review, so never hand a correctness
check to the grader. Because a cheap grader can also pass what it did not really check, its passes are
watched in two ways.

**A canary in every batch.** In each `drive:grader` checklist batch, plant one known-bad item whose
correct answer is a failure: a `commands.log` line cited as exit 0 that shows a non-zero exit, a
STATUS row citing an evidence path that does not exist, a diff excerpt with an added `.only`, a doc
sentence naming a flag the code does not have. Build the item under `.drive/local/canaries/<batch>/`,
list it among the real items with nothing that marks it, and record which item it is in
`.drive/local/canaries.json`, never in the brief. Canaries go only into batches whose answers are not
STATUS evidence files; citation checks, whose JSON is evidence, are watched by the blind re-grade
instead. When the grader passes the canary, the whole batch is void: re-run it with a fresh
`drive:verifier`, and record a failure event (a judge contradicted by evidence). A second canary miss
in the run moves that kind of check to `drive:verifier` for the rest of the run. Drop the canary's
answer before recording results.

**A blind re-grade at every gate that used the grader.** Draw a random sample of the items the grader
passed, one in ten with at least one and at most five, weighted toward items passed with no finding,
and give them to a fresh `drive:verifier` with the same question and evidence but never the grader's
answer. Write the comparison to `.drive/reviews/<date>-regrade-<gate>.md`: item, grader answer,
verifier answer, agree or not. A disagreement reopens that item's gate with the verifier's answer,
counts as a failure event, and sends the next two grader batches of that kind to a full re-grade. The
retro reports the agreement counts and canary results as evidence of how far the grader can be
trusted.

**Moving a check to a cheaper agent.** Never move a check from `drive:verifier` to `drive:grader` on
belief. Run both, blind to each other, on the next three gates; move it only when they agreed on every
item and the grader found every failure the verifier found, and record the comparison in DECISIONS.md.

UI and design judges are calibrated: they receive few-shot examples with score breakdowns, weighted
criteria with hard floors, and a penalty list of generic patterns (`references/ui-verification.md`).
When a judge's verdict diverges from later evidence (a claim it passed fails live, a design it rejected
is upheld by the auditor with evidence), record a failure event; the lesson loop tunes that judge's
prompt.

## 12. Process criteria and rubric gaps

Process criteria are legitimate and cheap to grade from commits and files: a green baseline was
recorded before the first change; the characterization corpus ran on the old system before code moved;
the limits probe ran on the current toolchain; `drive.py guard --base <baseline_sha>` exited 0 before
each integration commit; frozen tests have a `red/red.txt` older than their implementing commit;
TESTPLAN.md rows were committed before their tests; the verifier ran the test command itself.
`drive:grader` checks them.

A verdict separates "the rubric does not fit the deliverable" from "the work is not done". When a
criterion cannot apply (a screen criterion on a CLI), the verifier writes
`rubric_gap: <criterion>: <why it does not fit>` under `not_checked` and does not fail the claim on it.
A criterion that fits and is not met is a gap. Decide each `rubric_gap` for the next unit with a
DECISIONS.md entry. A standing-floor criterion can never be a rubric gap.

## 13. The final audit

`drive:auditor` runs the final audit for `build`, `move`, every `fix/incident`, a `feature` with five or
more claims, and any `fix`, `publish`, `report`, or `operate` run at L or above. For every other run
above XS, a fresh `drive:verifier` runs the same checklist in its final-audit mode. The grader never
runs it, because a judge weaker than the maker passes what it cannot trace. The audit runs after the
retro is committed and REPORT.md is drafted, before any row becomes Done, and before STATE.md says
`done` or `stopped`. A `stopped` run needs it whenever any STATUS row is above Missing, and
`lint --final` refuses such a run, exactly as it refuses a done run, unless the latest
`<date>-final-audit.json` is schema-valid, backed by its reviewer's transcript, says `verdict: pass`,
and is no older than the latest code commit; a stopped run with no rows, or with every row at Missing
or Dropped, has nothing to audit and needs none. On a stopped run, go means the report honestly states
what was and was not achieved, with every row at the rung its evidence supports and its reason
recorded; it never means the goal was met.

The handoff, sampling, and checklist are in `references/definition-of-done.md` section 6, the only copy
of them; the brief names that path rather than paraphrasing it. The intake GOAL.md is read from the
commit `git log --grep '^drive(intake): <slug>$' --format=%h -1` finds, never from the first commit
that added GOAL.md, because a repository that once held a paused run has added GOAL.md more than once.

The auditor, or the verifier in its final-audit mode, writes its verdict to
`.drive/reviews/<date>-final-audit.json`. You validate it like any verdict and never edit it, and every
row that becomes Done cites it as its `review:` token. On no-go, apply the downgrades, fix what the
budget allows, and re-audit with a fresh agent, at most twice more; then the rows keep the rungs the
last audit supports and the run ends `stopped`. A no-go never closes a run, stopped or done: address
its findings (usually by narrowing rows with `why:` tokens or DECISIONS.md entries and fixing the
report) and get a fresh passing audit before `lint --final` and `drive.py end` accept it.

## 14. Excuses and rebuttals

| The argument for skipping the step | Why it fails |
|---|---|
| "The maker's report says it is fixed; paste that in so the verifier saves time." | The verifier then checks the maker's story instead of the work. Hand over what must be true, never the claim that it is. |
| "I watched the build; I can grade it myself." | Having watched the work is exactly what disqualifies you. |
| "Resume the last verifier; it already knows the code." | It also knows its previous conclusion. Spawn fresh. |
| "The verdict says pass; the commands list is empty but the tests obviously ran." | A pass without commands is malformed. Reject it. |
| "The security reviewer is Opus; its blocking finding does not need a refuter." | Any reviewer asked for problems produces some false ones, and fixing a false one adds real defects. Refute before the maker sees it. |
| "Refutation is slow; send every finding straight to the maker." | A maker patching refuted findings is how later rounds come to be about the fixes. |
| "Rounds are exhausted and only small issues remain; mark it Done." | The rung is what the last verdict supports. Reaching the bound never makes a row Done. |
| "Round five found fewer issues than round four; one more round will finish it." | Counts do not trend down. Close on confirmed severity, scope to the fix, and treat a recurring class as a design problem. |
| "The same gap came back; one more tweak will do it." | A returning gap means the diagnosis was wrong. Investigate first. |
| "This finding is out of scope; add a criterion quietly." | Rubrics are frozen during a loop. Record a rubric gap and amend for the next unit. |
| "Ask the reviewers for only the important issues to keep noise down." | Filtering belongs to you afterwards. A reviewer told to be selective drops real findings. |
| "Use the grader for the verifier's job, or for a small run's final audit; it is cheaper." | A weaker judge passes what it cannot trace. |
| "The grader has been right all run; skip the canary." | A canary costs one item. A grader that passes without checking looks exactly like a grader that is right. |
| "It must be around 200 milliseconds." | An unmeasured number is not evidence. Write "not measured". |
| "Every finding this round was a misunderstanding." | Two consecutive rounds dismissed by you as misunderstandings mean you are validating rather than verifying, which is a failure event (section 7). |

## 15. Red flags

- A handoff containing words from a maker's report, or a verifier prompt that says what was fixed.
- A verifier spawned with a fork, a resumed agent, or `isolation: worktree`.
- A verdict with an empty `ran`, a claim with no refutation attempt, or a number with no source.
- `VERDICT pass` printed without a `verdict.json` behind it, or a verdict the lint reports as lacking
  provenance.
- A `SNAPSHOT VOID` line in `gate.log` followed by that reviewer's evidence being recorded.
- A reviewer's blocking gap sent to a maker with no refutation file, or refuted by the agent that
  raised it.
- A dispositions file missing a gap, or a gap marked `fixed` without a test that fails on the parent.
- A rubric file changed during a verification loop, or no rubric committed before the first maker.
- A fourth round on a three-round shape, or Done written after the bound was reached without a pass.
- The same gap key and location, or the same defect class, in two rounds with no investigation file
  between them.
- Reviewer prompts containing "be conservative", "only important", or "no nitpicks".
- Two rounds of substantive findings with none acted on.
- A grader batch with no canary, a passed canary whose batch was recorded, or a gate that used the
  grader with no re-grade file.
- `/code-review` run without a level or range, or `/code-review`, `/simplify`, or `/security-review` run
  in your own context.
- A final report that describes intended behaviour as delivered, or narrowings without decisions.
- A final audit run by the grader, or saved anywhere but `.drive/reviews/<date>-final-audit.json`.
- A handoff that names a pre-fix tree path, or a pre-fix check run in a worktree.
- A `verdict.json` written by you rather than by the verifier that ran the round.
