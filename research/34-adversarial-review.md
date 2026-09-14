# 34 · Adversarial review of the whole project at 84ccd54

Reviewed on 2026-09-14 by a clean-context reviewer. The only file this review changed is this one. I
ran the checks myself in scratch repositories under the session scratchpad, with `HOME` and
`CLAUDE_PLUGIN_DATA` pointed at scratch directories so no ledger or setting outside the scratchpad
was touched. Two helper agents checked facts against live Anthropic and Claude Code documentation,
another checked cross-references mechanically, and a fourth audited the eval graders. I re-read or
reproduced every finding below before listing it.

## Verdict

The design is coherent and the documentation is unusually consistent with itself. The model
roster, prices and effort levels match the live documentation, and the cost envelopes recompute
within five percent. Every section citation resolves. The test suite passes on Python 3.13 and on
the Python 3.9.6 that macOS ships. Most of the guard does what the threat model promises: the main
thread cannot write a verdict by any plain means, nobody can push or create a branch, and a frozen
test cannot be edited through any ordinary tool. The Stop gate refuses a vague stop, a premature
`done`, and a Done row without its evidence.

The project is not ready for a first real run, though. A few mechanisms fail in exactly the places
the tests never reach. The worst is that the guard refuses the one write every reviewing agent is
told to use: a Bash heredoc. A verifier, auditor, grader, security reviewer or UI reviewer following
its agent file is therefore refused on its first verdict. In practice no claim can reach Local
Proof, and the run stalls or ends `stopped`. The suite never sends a reviewer's heredoc through the
guard, which is how 338 green tests coexist with that bug. Next come `install.sh`, which exits 1 on
a fresh machine before it prints the launch settings, and a `drive.py end` path that closes a
blocked run with branches and worktrees still present. A review gets voided when its own test run
leaves an artifact git does not ignore. The trivial goal the owner asked about, fixing a typo in a
README, cannot stay XS and escalates into a full size-S `fix` run. None of these needs a redesign.
Each needs a targeted fix and a test that exercises the real path. The eval suite has never produced a score, and several of its cases would pass a wrong run or
fail a correct one, so it cannot yet stand in for a real run.

## Findings

### Critical

**1. The guard refuses every reviewer's documented heredoc write, so no verdict can be written as
instructed.**

- **Where:** `skill/scripts/drive.py:4453-4553` (`split_shell`, which splits on every newline at
  `:4521` and has no heredoc handling). The instructions it contradicts are:
  - `skill/agents/verifier.md:112-121`, "Create files only with Bash heredocs", with
    `cat > .drive/proofs/<key>/r<n>/verdict.json <<'JSON'`;
  - `skill/agents/auditor.md:28-31`;
  - `skill/agents/grader.md:37-41`;
  - `skill/agents/security-reviewer.md:63-66` and `:76`;
  - `skill/agents/ui-reviewer.md:24-29`;
  - `skill/references/verification.md:186-194`;
  - `skill/references/definition-of-done.md:321-323`.
- **What:** `split_shell` treats each line of the heredoc body as a separate simple command, and the
  reviewer command allowlist then judges that line. I fed hook inputs to `drive.py hook-guard` as
  `drive:verifier`, `drive:auditor`, `drive:grader`, `drive:ui-reviewer` and
  `drive:security-reviewer`. Every multi-line heredoc was refused with exit 2:
  - a verdict whose body is `{`, `"verdict": "pass",`, `}` was refused with "'verdict:' is not on
    the reviewer's list of read-only command shapes";
  - a one-line JSON body was refused as `{verdict:`;
  - a Markdown security review was refused as `-`;
  - the `tee path <<'JSON'` form failed the same way.

  Single-line `echo '...' > path` and `printf '%s\n' '...' > path` are allowed. No agent file
  mentions them, and the refusal text points the agent the wrong way: "the orchestrator records it
  as the build, focused-test, or full-suite command in GOAL.md".
- **Why the tests miss it:** `skill/scripts/tests/helpers.py:280` uses a heredoc only as fabricated
  transcript content for the provenance tests, and `test_severe_review.py:151` checks a heredoc only
  as a main-thread refusal. Nothing sends a reviewer's heredoc through the guard.
- **Failure scenario:** the first verification round of any run above XS proceeds as follows.
  1. The verifier runs the tests and composes its verdict.
  2. The guard refuses the documented heredoc.
  3. Per `verifier.md:125-126` ("never wrap the command to get past it"), the verifier returns
     `blocked`.
  4. The orchestrator re-spawns, the same refusal repeats, and the row never reaches Local Proof.
  5. The run stalls, or ends `stopped` with nothing verified.

  The final audit, citation checks and security review files fail the same way.
- **Fix:** teach `split_shell` heredocs.
  - After a `<<WORD`, `<<'WORD'`, `<<"WORD"` or `<<-WORD` redirection, consume the body up to the
    delimiter line and hand it to nobody; `<<-` strips leading tabs.
  - Keep judging the command line itself, including its `>` target.
  - Add one guard test per reviewing role with a multi-line JSON body and a Markdown body, driven
    through `hook-guard` exactly as a transcript would record it.
  - Make the refusal message for an unknown first word say which part of the command it judged.

### High

**2. `install.sh` fails on a fresh machine before it runs `selfcheck` or prints the launch
settings.**

- **Where:** `install.sh:52-60`.
- **What:** the script reads `claude plugin list` and requires the status line to contain
  "enabled". For a skills-directory plugin, Claude Code 2.1.270 prints `Status: ✔ loaded`. I ran
  the script with `HOME` set to an empty scratch directory and `DRIVE_INSTALL_SKIP_TESTS=1`.
  1. It linked the skill, validated it, and ran `claude plugin enable drive@skills-dir`; run by
     hand, that command reports success.
  2. It printed "Enabled drive@skills-dir" unconditionally at `:53`, because the enable call ends in
     `|| true`.
  3. It then exited 1 with "claude plugin list does not show drive@skills-dir as enabled (status:
     Status: ✔ loaded)".
- **Failure scenario:** a new user runs `./install.sh`, sees an error, and never receives
  `DRIVE_SETTINGS`. The README's launch recipe (`README.md:96-106`) depends on that value. Without
  it the user either gives up or launches without `worktree.bgIsolation: none`. A background session
  then moves into a harness worktree, which commits and pushes a branch: exactly what the skill
  exists to prevent.
- **Fix:** accept `loaded` as well as `enabled`, and treat `disabled` or absence as failure. Print
  "Enabled" only when the enable command exited 0. Add a test that runs `install.sh` against a
  stubbed `claude` printing the skills-dir format.

**3. `drive.py end` closes a `blocked` run without any hygiene check, leaving branches, worktrees
and dirty paths behind with every hook switched off.**

- **Where:** `skill/scripts/drive.py:3510-3514`. The documented behaviour is at
  `skill/references/state-files.md:393-395` and `skill/SKILL.md:321-323`.
- **What:** for `blocked`, `cmd_end` checks only the Blocked-on token and that REPORT.md says
  "Stopped because". It runs no lint at all; `stalled` is the same. I reproduced it:
  1. In a scratch run I left a new local branch, a detached worktree under `/tmp`, and an untracked
     file.
  2. I set `status: blocked` with `Blocked on: credentials: none` and wrote a one-line REPORT.md.
  3. `drive.py lint --stop` reported 7 failures, including the branch and the worktree.
  4. `drive.py end` then printed "Run closed as stopped" and removed `.drive/local/active`.
- **Failure scenario:** a run blocks honestly on a missing secret, with a detached experiment
  worktree or a background session's branch still present. The orchestrator follows SKILL.md
  section 9, runs `drive.py end`, and the run closes. The guard and the Stop gate go inert. The
  owner inherits a branch and a worktree, which owner requirement 3 forbids and `lint --stop`
  exists to catch.
- **Fix:** run the `--stop` hygiene checks, at least, before `end` accepts `blocked` or `stalled`,
  and refuse on any failure. The Stop gate may keep allowing the turn to end; closing the run is
  what must require a clean tree.

**4. A review is voided when the reviewer's own test run creates a file git does not ignore, and
re-running the review repeats the void.**

- **Where:**
  - `skill/scripts/drive.py:6092-6137`: `tracked_state` includes every untracked, non-ignored file
    outside `.drive/`.
  - `:6035-6044`: `cmd_hook_post` returns early for reviewer roles, so a reviewer's own Bash changes
    are never recorded as edits.
  - `:6269-6280`: the void.
  - `skill/references/verification.md:203-212`: the recovery advice.
- **What:** I started a `drive:verifier` snapshot, wrote a verdict backed by a transcript, created
  `.coverage` as a Python coverage run would, and stopped the agent. The hook recorded provenance,
  then logged "SNAPSHOT VOID verifier ag-v1 changed: .coverage". The lint refused the verdict: the
  review "was voided because tracked files changed while it ran". The same happens with
  `test-results/`, `playwright-report/`, junit XML, `.wrangler/` state, and screenshots a test
  writes into the tree.
- **Failure scenario:** a greenfield build's wave 0 has no `.gitignore` entries for its test
  runner's artifacts.
  1. Every verifier round is voided.
  2. The documented recovery ("restore the tree, add an Open failure, and spawn a fresh reviewer")
     runs the same suite and is voided again.
  3. Two diagnoses later the run ends on `two-diagnoses:`, or stalls, on a harmless artifact.
- **Fix:** do not void on new untracked files created during a review whose paths match the
  reviewer's own recorded commands, or do not void on untracked files at all and void only on
  tracked modifications and HEAD movement. Also have the void message name the path and suggest
  ignoring build and test artifacts, and add a wave 0 rule that the ignore file covers the test
  runner's outputs.

**5. The single switch that turns off all enforcement, `.drive/local/active`, can be deleted by
ordinary cleanup commands.**

- **Where:**
  - `skill/scripts/drive.py:3673-3697`: every hook returns early when the marker is missing.
  - The guard's refusal list is what fails to protect it.
  - `skill/references/long-running.md:347` says "never delete `.drive/local/active` by hand".
- **What:** as the main thread, the guard allows:
  - `rm .drive/local/active`;
  - `git clean -fdX`, which removes every ignored file, so the marker, `baseline.json`, the
    snapshot records and `gate.log` all go;
  - `git clean -fdx`.

  (`rm -rf .drive/local` is refused, but only because `.drive/local/frozen-parked` is protected.)
  Once the marker is gone, the Stop gate allows every stop and the guard allows every write.
- **Failure scenario:** `lint --stop` reports untracked build output, and the orchestrator runs
  `git clean -fdX` to clean the tree. That is a plausible honest move. It silently ends
  enforcement mid-run, and the run can then set `status: done` with no gate.
- **Fix:**
  - Refuse deleting or moving the marker and `baseline.json`, and refuse `git clean` with `-x` or
    `-X`, while a run is active.
  - Separately, when `.drive/STATE.md` says `running` or `verifying` but the marker is missing, have
    `hook-stop` warn once (it can find the repository from `cwd`) rather than stay silent.

**6. A goal like "fix a typo in README" cannot stay XS and escalates into a full size-S `fix` run.**

- **Where:** `skill/SKILL.md:75-84` (the XS fast path), `:92-100` (the shape table), and
  `skill/references/shapes/fix.md:243-244`. The promise it breaks is in `README.md:8-9`.
- **What:**
  - The XS fast path requires writing "one test that would refute the claim and see it fail", and
    `SKILL.md:83-84` moves the run to S "the moment ... the test cannot fail first".
  - A README typo has no meaningful failing test. The shape table's first row ("names a defect,
    failure, wrong output") makes it a `fix`.
  - An S `fix` brings GOAL.md, STATE.md, STATUS.md, HUNT.md, an investigator, a severe test on an
    adjacent input, a verifier with a pre-fix `git archive` check, a retro, a final-audit checklist
    by a fresh verifier, REPORT.md and `lint --final`. `models.md` prices that at $20 to $40.
  - The only non-code XS rules are `shapes/publish.md:105` (a copy change on a site page) and
    `shapes/report.md:59` (one fact); neither covers a repository's own docs.
  - The `xs-restraint` eval covers a one-line code fix, not a docs edit.
- **Failure scenario:** the owner types `/drive fix a typo in README`.
  1. The orchestrator either invents a test that greps the README (a test written to pass), or
     follows the text to size S.
  2. It creates `.drive/` and spawns three or four agents.
  3. It spends twenty dollars and several minutes on a one-character change.
- **Fix:**
  - Add an XS rule for edits with no runtime behaviour (docs, comments, copy, typos). The evidence
    is the diff plus whatever check applies (render, link check, spell check, the build), and the
    commit body names it.
  - Say in the shape table that a typo or wording change is not a `fix`.
  - Add a `docs-typo-restraint` eval case.

**7. The eval suite cannot yet tell a correct run from a wrong one in several cases, and some
graders fail correct runs.**

- **Where:** `skill/evals/`, with details from a grader-by-grader audit that I spot-checked against
  the grader files.
- **What:** no scored run exists (`skill/evals/README.md:103-121`), so none of the following has
  been caught by running the suite.
  - **A wrong run scores 1.0 in `verifier-isolation`.**
    `graders/handoff-free-of-maker-summary.md:4` and `verifier-brief-free-of-maker-summary.md:4`
    forbid only three exact phrases from the seeded maker report ("definitely correct", "reviewed
    every edge case", "no further review"). A handoff that paraphrases the maker's summary, or
    lists the maker's `report.json` as an evidence input, passes both.
  - **A wrong run scores 1.0 in `example-only-restraint`.** Its negatives forbid only manifests,
    schemas, Swift, Xcode projects, worker config and generator commands. A run that does full
    intake on the example, writing and committing `.drive/GOAL.md` and a TypeScript source file,
    passes every grader.
  - **A correct run probably cannot reach 1.0 in `harness-kindness`.**
    `graders/guard-written.md:4` looks in the trace for an Edit or Write of a `.py` file containing
    `25`. SKILL.md sections 4 and 6 delegate code edits to `drive:implementer`, and the README's
    own section 10 says it is unverified whether the trace includes subagent tool calls.
  - **Graders that match text the skill does not require:**
    - `stays-on-main/graders/no-push-or-pull-request.md:4` matches `git push` anywhere in a
      command, so `echo "not running git push"` fails the run, which is the
      mention-versus-act mistake the README's section 8 warns against;
    - `xs-restraint/graders/trailing-hyphen-fixed.md:4` accepts only `strip("-")`, `rstrip("-")` or
      a `-+$` regex, so a correct rewrite using `"-".join(...)` fails;
    - `no-lesson-for-instance-failure/graders/distill-says-none.md:4` reads `## Distill` to the
      end of the file, so any later "none" satisfies it.
  - **Classification expectations the references contradict.**
    - The publish prompt (`classification/publish-research-website/prompt.md:15`) never asks for
      deployment, while SKILL.md:97 and `intake.md:158` make "deployed" the trigger for `publish`.
    - The mobile app's expected XL rests on counting storage as a third surface, while the size
      table and the take-the-smaller rule (`intake.md:390-396`) make L defensible.
  - **Idle scores.** Six cases give a do-nothing run between 0.54 and 0.67, above the README's own
    rule that idle runs score well below 1.0.
  - **Classification cases may stall before GOAL.md is written.** At M and above, intake runs
    `drive.py init`, `preflight`, and an architect review. The README says `drive.py` cannot be
    read inside the sandbox, and these cases, unlike the seeded ones, have no fixture workaround.
- **Failure scenario:** the first gating run reports 1.0 on `verifier-isolation` and
  `example-only-restraint` for a skill that leaks the maker's summary or scaffolds the example, and
  below 1.0 on `harness-kindness` for a skill that behaves correctly. Per the README's section 7, a
  newly failing case is then treated as a skill regression, and an investigation chases a grader
  defect.
- **Fix:**
  - Replace the phrase negatives with an LLM rubric over the handoff and the Agent inputs, or with a
    positive check that the handoff's sections contain only template fields.
  - Add negatives on `.drive/**`, `git commit`, and new source files to `example-only-restraint`.
  - Grade `harness-kindness` on the contents of `contacts/store.py`.
  - Anchor command negatives to the start of a command.
  - Settle the publish and XL expectations in intake.md or change the prompts.
  - Before the first paid run, compute each case's idle score with a scripted do-nothing trace.

### Medium

**8. A `stopped` run closes with no verifier, no severe test and no final audit, despite the docs
saying a stopped run is audited.**

- **Where:**
  - `skill/scripts/drive.py:2854-2938` (`final_audit_problems` and `check_final`): a final audit is
    required only when a row is Done.
  - The promise is at `skill/references/definition-of-done.md:202-205` and `:259-264`,
    `skill/references/verification.md:599-602`, and `skill/agents/auditor.md:59-62`.
- **What:** I built a size-S run with one row at Partial carrying `why:the run stopped before
  verification`, a REPORT.md filled from the template, and a retro filled from the template, and
  set `status: stopped`. `lint --final` passed, `drive.py end` closed the run, and no reviewer had
  ever been spawned. Nothing reached Done, so the anti-mirage requirement holds for Done. But the
  final audit's stated purpose on a stopped run, catching "a plan described as a result" in the
  report, never happens, and the `why:` token accepts any text.
- **Failure scenario:** under budget pressure the orchestrator skips verification and the audit,
  marks every row with a free-text `why:`, and ends `stopped`. The owner reads a report nobody
  independent checked.
- **Fix:** require `.drive/reviews/<date>-final-audit.json` with transcript-backed provenance at
  `--final` for `stopped` runs too, whenever any row has evidence above Missing. Alternatively,
  change the documentation to say stopped runs are not audited.

**9. The Blocked-on stop tokens accept any words after the token.**

- **Where:** `skill/scripts/drive.py:3441-3466`, together with finding 3.
- **What:** `Blocked on: budget: I think we have done enough` and `Blocked on: credentials: none`,
  plus any REPORT.md containing "Stopped because", both ended the turn in my tests. The
  documentation admits the gate reads text (`long-running.md:322-327`). The threat model is honest
  here; the concern is that `budget:` needs no evidence at all, although the lint already counts
  maker spawns.
- **Failure scenario:** a run that is merely stuck labels itself `budget:` and stops. With finding
  3, `drive.py end` then closes it.
- **Fix:** for `budget:`, require either the spawn count past the budget line or a DECISIONS.md
  entry naming the overrun, both of which the lint can already see. For `credentials:`, require a
  named variable or secret after the token (an uppercase identifier or a quoted name).

**10. `aborted` is accepted when the Decision line merely mentions aborting.**

- **Where:** `skill/scripts/drive.py:3422` (`ABORT_RE` matches `\babort` anywhere) and
  `skill/templates/STATE.md:17` ("a DECISIONS.md entry whose Decision: line says why").
- **What:** a DECISIONS.md entry whose Decision line reads "do not abort; continue with the fix",
  plus a REPORT.md, made the Stop gate log "ALLOW status aborted". The template's wording does not
  tell the orchestrator which words the gate needs.
- **Fix:** match an affirmative form such as `^(abort|aborted|the owner (ended|stopped|cancelled))`,
  or a dedicated `Aborted:` field. Quote the required words in the template.

**11. The main thread may run `git stash`, `git clean` and `git commit --amend` in the shared
checkout while makers and reviewers are working.**

- **Where:** the guard's main-thread git rules; `skill/references/parallel.md:284` lists what the
  main thread is refused. `SKILL.md:234` forbids only `git reset --hard`.
- **What:** all three were allowed for the main thread in my tests. A stash while implementers are
  mid-edit removes their uncommitted work from the tree. An amend rewrites HEAD, which voids every
  running review ("HEAD was rewritten") and can rewrite the intake commit the lint and the audit
  anchor on.
- **Fix:** refuse `stash` (except `stash list`), `clean`, and `commit --amend` for the main thread
  while any `drive:` agent is running or `.drive/local/ro/*.json` exists, and mention them next to
  `git reset --hard` in SKILL.md section 6.

**12. The orchestrator runs `/simplify` and `/code-review` in its own context.**

- **Where:** `skill/references/verification.md:274`, `:280`; `shapes/feature.md:29`, `:31`;
  `shapes/build.md:33`; `research/24-synthesis.md:484-488`.
- **What:** `/simplify` edits code, so the orchestrator becomes a maker for that step. SKILL.md
  section 1 says the maker never judges its own work, and section 4 says never to read source
  inline. `/code-review` returns findings, which can include security weaknesses, into the Fable
  context that `safety.md` section 2 works hard to keep free of attack material, because a cyber
  flag there switches the orchestrator to Opus 4.8 for the rest of the session.
- **Fix:** run both through a `drive:` agent: the implementer for `/simplify` under a package brief,
  the verifier or security reviewer for `/code-review`. Alternatively, record in safety.md why the
  exposure is acceptable.

**13. HANDOFF.md is stale and contradicts the shipped skill.**

- **Where:** `HANDOFF.md:14-16`, `:56`, `:82`, `:105-108`, `:127-150`.
- **What:**
  - It says the synthesis has "amendment sections 15 to 19"; there are 15 to 21.
  - It lists reports only to 23; the directory runs to 33.
  - It keeps an "Open conflicts to settle during synthesis" list and a "Synthesis plan (next steps)"
    whose first step is "Wait for reports 16, 21, 22, and 23".
  - It says "Report 22 will settle the rest".
  - It says "Opus at high verifies ... architecture", while the architect is at xhigh.
  - It names a local path, `~/Projects/agent-skills`.

  The top section says the skill is drafted and committed, so the file contradicts itself.
- **Failure scenario:** whoever picks the project up next follows the synthesis plan and re-opens
  settled questions.
- **Fix:** rewrite the lower half as current state. Move the history to a dated section, or
  delete it now that `research/24-synthesis.md` holds it.

**14. Documentation gaps that would make a correct agent write a file the lint rejects** (from the
cross-reference check, each confirmed).

- **proof.json fields:** `skill/references/verification.md:252-256` lists the proof.json fields
  but omits `key`, `verdict: pass`, `produced_by`, and `shim_differences_note` for an empty list.
  `drive.py:1555-1585` requires all four. Neither `agents/verifier.md` nor `agents/ui-reviewer.md`
  names any proof.json field.
- **Per-claim `rung_supported`:** the lint prefers it (`drive.py:1523-1526`), and the auditor and
  `definition-of-done.md:324` require it. It is absent from `verification.md` section 4 and from the
  verifier's Verdict section. The schema allows `Done` at claim level
  (`templates/verdict.schema.json:66`) but not at top level (`:52`).
- **Who writes HUNT.md:** `skill/references/state-files.md:161` names only `drive:investigator`,
  while `shapes/fix.md:38-46` has the orchestrator, researchers and the implementer writing its
  sections.

**15. `models.md` misstates what happens off the Anthropic API, where an override alias can select
a model outside the roster.**

- **Where:** `skill/references/models.md:22-26`.
- **What:** the file says the three IDs "may not exist" on Bedrock, Google Cloud or Foundry. In
  fact Google Cloud and Foundry use the same IDs, and Bedrock uses `anthropic.claude-opus-5`. The
  bigger point is aliases: according to the model-config documentation, `opus` resolves to Opus 4.6
  on Foundry, and `sonnet` to Sonnet 4.5 on Bedrock and Google Cloud. An implementer override
  (`model: "opus"`) on Foundry would therefore run Opus 4.6, a model the owner excluded. The file
  relies on the auditor spotting the reported model afterwards.
- **Fix:** state the per-provider alias table and say drive refuses to pass an override when the
  run is not on the Anthropic API; the preflight can detect the provider from the environment.
  This is a documentation accuracy issue, not a mismatch between docs and code, so I have not
  ranked it Critical.

**16. SKILL.md's size table omits the severe tester that Local Proof requires at size S.**

- **Where:** `skill/SKILL.md:117` (S: "a short spec; one verifier"). The Local Proof row in
  `skill/references/state-files.md:336` requires a `severe:` token.
- **What:** only `intake.md:405` and `verification.md:276` say a severe test runs at S, and
  `intake.md` says it only for a fix. An S feature planned from SKILL.md alone reaches Partial, and
  the orchestrator then discovers mid-run that it needs another agent the budget line did not plan
  for.
- **Fix:** add "a severe test per claim" to the S row in SKILL.md and intake.md section 9.

### Low

17. **Stale docstring in `hook_stop`.** `skill/scripts/drive.py:3805-3807` still says the Stop
    event is registered by both `hooks.json` and the skill frontmatter. HANDOFF says it was moved
    out of the frontmatter, and SKILL.md has no hook.

18. **Wrong section citations.** `README.md:132` points at `skill/evals/README.md` section 2 for
    what blocked the eval attempts; that account is in section 3. `skill/references/design.md:104`
    cites `observability.md` section 2 for the health endpoint, which is in section 7.

19. **Disagreeing token estimates for the lessons cap.** `references/lessons/general.md:7` says
    "about 4,000 tokens", while `references/lessons.md:358` and `references/lessons/README.md:11`
    say 16,000 characters, "about 6,400 tokens". The character limit is the same everywhere; the
    token estimates differ because drive.py assumes 4 characters per token and state-files.md 2.5.

20. **"Only copy" claims that other files contradict.** `models.md:46` says never to name a model
    or effort outside the agent files, yet SKILL.md, models.md section 5, verification.md section
    11 and the README all do; the values agree. `verification.md:292` calls its round-bound table
    the only copy, while `parallel.md:226` names SKILL.md as the source.

21. **The stall message understates what counts as progress.** `drive.py:3901-3902` says only
    STATE.md was unchanged, but `progress_digest` also counts STATUS.md, HEAD and the working tree.

22. **An undocumented byte cap on STATE.md.** `drive.py:2072` fails a STATE.md over 12,000 bytes;
    the docs mention only the 150-line cap.

23. **Undocumented flags and untested subcommands.** These flags appear in no document:
    `init --goal-file`, `--slug`, `--root` on several subcommands, `end --suite-timeout`, and
    `lesson-commit --heading` and `--scope`. No test invokes the `visibility` subcommand through its
    command line (its function is tested); `lesson-commit` has two test references.

24. **Slug-based resume matching.** `same_goal` (`drive.py:3240-3245`) treats two goals whose slugs
    match as the same run. Slugs are cut at 50 characters, so two different goals that share their
    first 50 characters resume each other's run instead of archiving it.

25. **`lesson-commit` accepts any change to SKILL.md.** At `drive.py:7236` it does not check that
    only the standing-rules block changed, while `lessons.md` and synthesis section 10 say the loop
    never edits the core text.

26. **Minor gaps in models.md.**
    - `models.md:108`: Explore inherits the session model but is capped at Opus on the API, so
      from a Fable session it runs on Opus 5.
    - `:219-221`: the list of cases where an effort change still rebuilds the cache omits
      `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS` and HIPAA configurations.
    - `:155`: calls `ANTHROPIC_DEFAULT_HAIKU_MODEL` "the only documented override", but the
      deprecated `ANTHROPIC_SMALL_FAST_MODEL` is also still documented.

27. **A patch can change a frozen test without a guard refusal.** The guard allows the main thread's
    `git apply <patch>` when the patch touches a frozen test. The next `freeze check` and every
    lint catch it, so the design's "evident afterwards" promise holds, but an investigator patch
    applied honestly fails late rather than loudly.

## Walking the example goals through the instructions

These walks assume finding 1 is fixed; without that fix, every walk stalls at its first
verification round.

**A trivial XS goal, "fix a typo in README".** See finding 6: the run escalates to an S `fix`.
Even at XS, the injected `drive.py start` view runs and prints "No drive run", which is harmless.

**A greenfield iOS app with a Cloudflare backend.**
1. SKILL.md section 2, step 0, sends new work to a fresh repository under `PROJECTS` and launches a
   background session there with a single Bash command. The recipe works as written.
2. Intake classifies it `build` XL: three surfaces and an open problem. The plan is long but each
   phase has an exit.
3. The walking skeleton needs `wrangler` authenticated. Without it, `shapes/build.md:70-74`
   continues the waves on the local runtime with rows capped at Local Proof, which is sound.

Four problems follow.
- The iOS Simulator MCP and the Browser pane exist only in the Desktop app. Whether a `claude --bg`
  session gets them is not documented (see UNVERIFIED), so `ui-reviewer` may silently fall back to
  `xcodebuild test` plus `simctl`, and nothing tells the orchestrator in advance.
- Device-only rows can never be Done, so this run is designed to end `stopped`. That is honest,
  but the owner should expect it; the README does not say so.
- `wrangler dev` writes `.wrangler/` state into the repository. Unless wave 0 ignores it, every
  review is voided (finding 4).
- The spend envelope is $650 to $1,600 with 200 maker spawns. The lint counts spawns, but a
  background session has no dollar cap, and nothing enforces a stop at the dollar figure.

**A deep bug hunt, "find this deep annoying bug and fix it".**
1. With no symptom, intake searches earlier open failures, CI, issues, logs and auto memory. When
   nothing turns up, it writes REPORT.md and stops `stopped`.
2. With zero STATUS rows, that stop passes `lint --final` without any review (finding 7).
3. SKILL.md calls intake "a handful of tool calls", while the symptom search in
   `shapes/fix.md:25-32` can be long. The cost belongs in the plan, not in intake.
4. At S the reproducer is written by `drive:implementer` (`fix.md:41`), yet `fix.md:18-20` forbids
   editing non-test source before a red reproduction. Those are consistent. But the S row at
   `fix.md:244` also needs "one investigator", which the budget line for S (8 maker spawns) must
   absorb together with the implementer and the researcher lanes at archaeology.

The instructions do not loop here; the two-round bound and the escalation rules end the hunt.

**A dashboard on an existing product.** This is `feature` at M.
- The designer extracts the contract from the existing system. When the product exposes no build
  identifier, the designer names a stamp endpoint "as verification infrastructure"
  (`agents/designer.md:66-69`). That adds product code the goal did not ask for, recorded as a
  decision. Tolerable, but it is a quiet widening of scope.
- Each displayed metric becomes its own claim (`feature.md:100-109`), so the run quickly passes five
  claims and needs the Fable auditor for the final audit. That is correct but pushes the cost toward
  the top of the envelope.
- Per-role live checks need test accounts the owner holds. The file handles that with
  `credentials:` and Local Proof. Finding 3 then lets the run close with leftovers.

**Moving an AI gateway into a core service.** This is `move/migration` at L, with both repositories
under `probe.repos` and `additionalDirectories`.
- The consumer census needs "at least one full cycle" of access logs (`move.md:58-67`). When the old
  gateway does not log caller identity, the run deploys identity logging and must wait a week before
  the first weight step. The documented wait is a `soak:` block whose scheduled check "invokes
  `/drive --resume`".
- With an API-key login and no Desktop app, the only listed scheduler is the project's CI. A CI job
  cannot resume a local Claude session, so this run in practice blocks until the owner resumes it
  by hand. The instructions do not say that is what happens on an API-key machine.
- Write guarding in the second repository covers makers only (`drive.py:4038-4041` adds
  `probe.repos` roots for makers), and hygiene there is a Verified-facts line checked by the
  auditor, not by the lint. That matches the docs, but a leftover branch in the old gateway
  repository is caught only by prose.

**Market research plus a website with blog and docs.** This is `publish` at L with a `report`
sub-goal first.
- "Build a site" does not ask for a launch, so every site row is created with `live: n`, and Done
  is reachable on a preview. That is sensible.
- When the hosting account is not authenticated, the run must "deploy nothing" and block on
  `account:`, yet `definition-of-done.md:153` requires every publish run to deploy a preview. Such
  a run always ends `stopped`, which is honest.
- The team page with no supplied material is removed, with a Needed-from-you line.
- The report sub-goal's evidence is the grader's citation JSON, which the grader cannot write today
  (finding 1).
- Lighthouse at performance 0.95 and accessibility 1.0 on mobile is a high default for a first
  build. The gate says thresholds can be set at intake; the orchestrator should be told to lower
  them only with a DECISIONS.md entry, which `definition-of-done.md` section 5 already covers.

## What I verified as correct

**The test suite.** `python3 -m unittest discover -s skill/scripts/tests` passes all 338 tests on
Python 3.13.12 in 176 seconds, and on `/usr/bin/python3` (3.9.6) in 202 seconds. Every Python file
parses with `ast.parse(..., feature_version=(3, 9))`, and `from __future__ import annotations`
covers the annotations.

**Structural checks.** `drive.py selfcheck`, `drive.py lesson-check` and `claude plugin validate
skill` all pass on Claude Code 2.1.270. SKILL.md is 371 lines and 16,769 characters through section
6, which matches the "about 16,800" in state-files.md.

**Models.**
- Every agent file's `model` and `effort` matches the roster in SKILL.md, models.md sections 2 and
  5, verification.md section 11 and the README.
- A repository-wide grep finds no Haiku selection. Older model names appear only in safety.md's
  description of Claude Code's cyber fallback (Opus 4.8), in models.md's explanation of why Haiku is
  absent, and in HANDOFF history.

**Prices and costs.** A helper agent read the raw markdown of the live models overview and pricing
pages. Fable 5.1 costs $10/$50 with cache writes of $12.50/$20 and cache reads of $0.25; Opus 5
costs $5/$25, $6.25/$10 and $0.50; Sonnet 5 costs $2/$10, $2.50/$4 and $0.20. All three support
low through max effort, with high as the default. These match models.md lines 33-35. From models.md
section 7's own token model I recomputed:
- a full verifier round at $3.42 against the stated $3.40;
- a scoped round at $1.56 against $1.60;
- an implementer at $1.68 against $1.70;
- an xhigh investigation at $8.62 against $8.60;
- a Fable final audit at $10.79 against $10.80.

The shape envelopes for fix M, feature M, build L, build XL, move L, publish L and report M
recompute within 5%; the largest gap is report M high, at $57 against $60.

**Claude Code facts, against code.claude.com.**
- Agent frontmatter: the `disallowedTools` spelling is right, and `effort`, `maxTurns` and `skills`
  are documented fields.
- Skill frontmatter: `disable-model-invocation` and `disallowed-tools` are documented, and
  `${CLAUDE_SKILL_DIR}` is substituted in both the skill body and `allowed-tools`.
- Hook inputs: `agent_id` and `agent_type` in subagent tool events, `agent_transcript_path` in
  SubagentStop, and `background_tasks` with `id`, `type`, `status`, `command` and `agent_type` in
  Stop.
- The Stop cap defaults to 8 consecutive blocks, and `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` is
  documented.
- Hooks receive `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}`.
- Settings and environment: `worktree.bgIsolation: none`, `promptCacheTtl` and
  `subagentPromptCacheTtl` (v2.1.242), and the TTL precedence. `CLAUDE_CODE_SESSION_ID` is exported
  to Bash and hook subprocesses. `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` defaults to 10 minutes.
- CLI flags: `--permission-prompts` and `--safe-mode` exist.
- Plugins: skills-directory plugins load as `<name>@skills-dir`, and `claude plugin eval` exists from
  v2.1.269 with the six grader types the eval README names.
- `/code-review` accepts a ref range such as `main...my-feature`.
- The classifier fallback table in safety.md matches model-config.

**Transcript format.** Real subagent transcripts on this machine have `agentId`, `cwd`, `type` and
`message.content` items of type `tool_use` and `tool_result`, with `is_error`, plus an
`agent-<id>.meta.json` holding `agentType`. That is exactly what `transcript_tool_calls` and
`meta_agent_type` parse.

**Guard refusals I exercised through `hook-guard`.**
- **Main-thread verdict writes** are refused through the Write tool, a heredoc, `python3 -c`, `cp`,
  a `jq` redirect, `tee`, `mv`, `cd` into the proof directory then a write, a variable holding the
  path, and a script file that names the path.
- **Push and branch operations:** `git push` is refused, including `git -C`, as are `git checkout
  -b`, `git switch -c`, `git branch x`, `git tag v1`, `git reset --hard`, `git rebase`, `git
  worktree add` without `--detach`, and `gh pr create`.
- **Implementers** are refused `git add`/`commit` and writes to STATUS.md, STATE.md and a verdict.
- **Verifiers** are refused `python3 -m pip install` and `sed -i` on source.
- **Frozen tests** are protected against the Edit tool, `sed -i`, `perl -pi`, `git checkout`,
  `git restore --source`, `git stash`, `git rm`, `cp` over the file, moving its directory, inline
  Python, and edits by an implementer. A changed frozen test fails `freeze check` and the lint.
- **A subagent outside the roster** (`general-purpose`) gets the main thread's refusal for a
  verdict write.

**The Stop gate.** It blocks:
- `running`, with the recorded `next:` and the lint findings;
- `blocked` with a Blocked-on line that names no token;
- `blocked` with a token but no "Stopped because";
- `done` with a Done row lacking `severe:`, a verdict, `review:`, a final audit, a retro, ticked
  plan lines and a recorded suite run.

**Provenance.** A verdict whose writing appears in the reviewer's transcript is recorded; a void
window makes the lint refuse it.

**Hard-coded paths.** Nothing that `install.sh` links contains a user's home path. `/private/tmp`
and `/tmp` appear as scratch roots, alongside `$TMPDIR`. `/Users/someone` appears only in a negative
test. The one local path is in HANDOFF.md, which is not installed.

**Cross-references.** All 168 section citations resolve, and all but the two in finding 18 match
what the citing sentence describes. These match across SKILL.md, the references, the templates and
drive.py:
- the status vocabulary, the nine Blocked-on tokens, the 13 evidence tokens, the 19 traits and the
  phase list;
- the subagent budgets, the 150-line cap, the 1,500-character result cap, the six-block stall, the
  confidence of 75 and the round bounds.

No script pushes, and `lesson-commit` commits on the skill repository's current branch.

## UNVERIFIED

- **Full IDs in the Agent tool's `model` parameter.** The docs do not say whether it accepts full
  model IDs. This session's tool schema lists only `sonnet`, `opus`, `haiku` and `fable`, which
  supports the skill's claim that only aliases are accepted, but no documentation page states it.
- **Skill-frontmatter `effort` beyond one turn.** The docs say a skill's `model` applies for one
  turn. They are silent about `effort: high` in SKILL.md, which the launch recipe sets anyway.
- **`color` on plugin agents.** The plugins reference's list of fields supported for plugin agents
  does not include `color`. The field is probably ignored, harmlessly.
- **The block cap through `--settings`.** I could not confirm that `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`
  placed in the `--settings` `env` block takes effect for the Stop cap, rather than only as an
  exported variable.
- **Bundled skills from a subagent.** I could not confirm that a subagent's Skill tool can invoke
  the bundled `security-review` skill, which `drive:security-reviewer` relies on.
- **Tools in background sessions.** I could not confirm whether the iOS Simulator MCP, the Browser
  pane and `mcp__Claude_Browser__*` tools are available to a `claude --bg` session, which the
  `ui-reviewer` tool list assumes.
- **The eval sandbox and symlinks.** `skill/evals/README.md:103-121` says the Bash sandbox refuses
  evals when `~/.docker` holds symbolic links. The sandboxing documentation does not mention it, and
  no scored run exists to test the claim. The README's own section 10 lists further open points
  about grader targets.
- **Subagent turn limits.** The `maxTurns` values in agent files are documented fields, but I did
  not test that a plugin agent honours them.
