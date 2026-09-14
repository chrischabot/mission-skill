# 26 · Review: contradictions inside the drafted skill

Reviewer: independent read of `research/24-synthesis.md` (sections 15 to 19 taken as overriding) against every file under `skill/` except `scripts/`, `evals/`, and `hooks/`. I read all of SKILL.md, the twelve agent files, every reference including shapes, domains, and the lessons store, and every template that existed when the review started. `templates/GOAL.md`, `DECISIONS.md`, `STATE.md`, `STATUS.md`, `LESSONS.md`, `investigation.md`, `lesson.md`, `postmortem.md`, and `retro.md` appeared while I was working; they belong to the in-progress set and are not reviewed here. Line numbers are as of 2026-09-14. Paths are relative to `skill/`.

## Summary

91 findings: 17 blocking, 42 should fix, 32 notes.

A blocking finding is one where an agent that follows one file breaks another file's hard rule, a guard write scope, a schema, or the lint. A should-fix finding is one where two files give different instructions but either reading still produces a usable run. A note is a wording or vocabulary drift that a careful agent would survive.

Five problems account for most of the risk. First, the pre-fix check is still a worktree in four files after synthesis 19.17 settled on a `git archive` copy. Second, the final audit output has two paths, and the grader is still offered as the small-run final checker. Third, the synthesis itself gives the verifier and the ui-reviewer write scopes that exclude `.drive/reviews/`, while other amendments tell them to save review files there. Fourth, the set of runs that get `drive:auditor` differs between the spine and the shape files. Fifth, `lint --final` demands every row at Done or Dropped, which no honest stopped run, device-only iOS claim, or preview-only publish run can meet, so `drive.py end` can never run for them.

Several fixes require amending the synthesis first, because the synthesis contradicts itself. Those entries say so.

---

## Blocking

### B1 · The pre-fix check runs in a worktree in four files and a `git archive` copy everywhere else

- Worktree side: `references/testing.md` 242-252 ("Create a detached worktree for that check ... `git worktree add --detach "$WT" <pre-fix sha>`"); `references/shapes/fix.md` 142-150 ("Create a detached worktree at the pre-fix sha under `/private/tmp`, copy the regression test into it, and pass its path"); `references/security.md` 104-107 ("run it in a worktree at that sha under `/private/tmp`"); `templates/rubrics/fix.md` 40 (oracle "verifier runs in the detached pre-fix worktree").
- Archive side: `agents/verifier.md` 36-38 and `agents/severe-tester.md` 49-52 (`git archive <pre-fix sha> | tar -x -C /private/tmp/drive-prefix-<key>`); `references/definition-of-done.md` 128 ("a copy under `/private/tmp`").
- Synthesis: 19.16 and 19.17 both decide for `git archive`; 19.17 names this conflict explicitly: "pre-fix code is always a `git archive` copy under `/private/tmp/drive-*`, never a worktree (item 16 wins over shapes/fix.md and verification.md)". 19.15's earlier worktree wording is overridden.
- Why blocking: testing.md tells the orchestrator to create the worktree and pass its path in the handoff, while the verifier creates its own archive copy. Both run, and the rubric's oracle names a tree the verifier never uses.
- Fix: in `testing.md` section 11, replace the code block and the sentence before it with: "The regression test must fail on the pre-fix commit. The verifier (or the severe tester, when it writes the reproducer) exports the pre-fix tree itself: `mkdir -p /private/tmp/drive-prefix-<key> && git archive <pre-fix sha> | tar -x -C /private/tmp/drive-prefix-<key>`, copies the regression test in, runs it there (red) and on HEAD (green), and removes the directory in the same step. The handoff names the pre-fix sha, not a tree path." In `shapes/fix.md` Verify, replace "Create a detached worktree ... pass its path" with "Pass the pre-fix sha; the verifier exports it with `git archive` as `agents/verifier.md` step 6 describes", and change "Remove the worktree in the step that saves the verdict" to "The verifier removes its copy before returning". In `security.md` section 3, replace "run it in a worktree at that sha under `/private/tmp`, log the exit code, and remove the worktree" with "run it in a `git archive` copy of that sha under `/private/tmp/drive-prefix-<key>`, log the exit code, and remove the copy". In `rubrics/fix.md` line 40, change the oracle to "verifier runs in a `git archive` copy of the pre-fix commit and on HEAD". In `verification.md` line 60, change "the pre-fix tree path" to "the pre-fix sha".

### B2 · The final audit is written to `.md` plus a proofs verdict in one file and to `.json` in three others

- Side A: `references/verification.md` 378: "Write its output to `.drive/reviews/<date>-final-audit.md` and `.drive/proofs/final-audit/r<n>/verdict.json`, and cite the review file as the `review:` token."
- Side B: `agents/auditor.md` 49 and `references/definition-of-done.md` 286: `.drive/reviews/<date>-final-audit.json`.
- Synthesis: 19.11 and 19.16 name `.drive/reviews/<date>-final-audit.json`. 19.14 limits the auditor's writes to `.drive/reviews/`, so the proofs path in verification.md would also be refused by the guard.
- Fix: in `verification.md` section 13, replace line 378 with "Save its verdict, unedited, at `.drive/reviews/<date>-final-audit.json`, and cite that file as the `review:` token."

### B3 · The grader is offered as the final checker for small runs

- Side A: `agents/grader.md` 41, table row "Final check on a small run" (reads the intake GOAL.md, lists narrowings, flags plans described as results). `references/capabilities.md` 129 lists `drive:grader` among the agents for "retro, final audit, report".
- Side B: `references/verification.md` 361-363 ("a fresh `drive:verifier` runs the same checklist ... a grader is too weak a judge for this"); `references/definition-of-done.md` 227-228.
- Synthesis: 19.15, "when the auditor is not required, a fresh `drive:verifier` (never the grader) runs the final-audit checklist"; 19.11 agrees.
- Fix: delete the "Final check on a small run" row from `grader.md`'s table. In `capabilities.md` line 129, change the Agents cell to "`drive:auditor`, or a fresh `drive:verifier` when the auditor is not required; orchestrator for the report".

### B4 · The synthesis sends verifier and ui-reviewer output to `.drive/reviews/` but gives them no write access there, and verifier.md has no final-audit mode

- Write scopes: `agents/verifier.md` 63 ("Create files only under `.drive/proofs/<key>/r<n>/` and `/private/tmp`"), matching synthesis 19.1; `agents/ui-reviewer.md` 22-23 (Bash writes only under `.drive/proofs/<key>/r<n>/` and `.drive/local/ui/`), matching synthesis 19.13.
- Review files they are told to produce: `references/definition-of-done.md` 227-228 and 286 (a fresh verifier's final-audit verdict "saved unedited at `.drive/reviews/<date>-final-audit.json`"); `references/shapes/fix.md` 173 ("close check by a fresh `drive:verifier` saved to `.drive/reviews/`"); `references/shapes/publish.md` 101-102 ("`drive:ui-reviewer`'s final review saved to `.drive/reviews/` below L"). Synthesis 19.15 and 19.17 require these.
- Missing modes: `verifier.md` describes only handoff verification. Other files assign it the final-audit checklist (DoD section 6), claims audits (`domains/web.md` 107-111), docs smoke tests (`web.md` 204-207, `publish.md` 35), telemetry-only diagnosis that "forbids reading source files" (`observability.md` 160-165), the operate observe step (`shapes/operate.md` 27), and the plan review (`operate.md` 25). verifier.md step 1 says run every validation command "before you read anything else" and step 2 makes any file outside ownership globs a blocking gap, both wrong for these jobs. A verifier running the final audit from its own file would write `verdict.json` under proofs, where DoD does not look.
- Synthesis: internally contradictory. 19.1 and 19.13 fix the write scopes; 19.15 and 19.17 require files in `.drive/reviews/`.
- Fix: amend synthesis 19.1 to "`drive:verifier` may write through Bash under `.drive/proofs/`, `/private/tmp`, and, when running the final-audit checklist or a close check, the one output file under `.drive/reviews/` its brief names", and 19.13 likewise for the ui-reviewer's final review. Then in `verifier.md` add a section "## Other modes" with one paragraph each for final-audit checklist (follow `definition-of-done.md` section 6, save to the reviews path in the brief), claims audit, docs smoke test, telemetry diagnosis (no source reading; return component, cause, and queries), and operate observation, each stating which of the eight steps it skips. Update `ui-reviewer.md` Boundaries to allow the one reviews path the brief names.

### B5 · verification.md says the orchestrator writes the verifier's verdict file

- Side A: `references/verification.md` 111-112: "The verifier saves command output with `tee` ...; you write its returned JSON to `r<n>/verdict.json`." Lines 78-79, the prescribed verifier prompt: "Return the verdict JSON that matches the schema, and nothing else."
- Side B: `agents/verifier.md` 67 ("Write `.drive/proofs/<key>/r<n>/verdict.json` with a Bash heredoc") and 75-77 (final message is a status line, path, counts, at most 1,500 characters, and the model line).
- Synthesis: 19.16, "the verifier writes its own `verdict.json` ... through Bash and the orchestrator validates it before any STATUS change". Section 6 fixes the result shape as status line, paths, at most 1,500 characters.
- Why blocking: two writers for one file, and a prompt that forbids the model line and path that every other file requires.
- Fix: in `verification.md` line 111-112, replace the second sentence with "The verifier writes `r<n>/verdict.json` itself; you validate it against the rules below before any STATUS change." Replace the quoted prompt's last sentence with "Write the verdict to the path in the handoff and return the status line, that path, the counts, and the model you ran as."

### B6 · Which runs get `drive:auditor` differs between the spine and the shape files

- Narrow side: `SKILL.md` 223-224, `references/verification.md` 361, `references/definition-of-done.md` 227, `agents/auditor.md` 3, and `references/intake.md` 363 all say the auditor runs "before any Done on build, move, or a feature with five or more claims".
- Wide side: `shapes/fix.md` 175 ("the final audit by `drive:auditor` (also for every `fix/incident`)" at L); `shapes/publish.md` 38 and 101 (final audit at L and above); `shapes/report.md` 52 and 62 (final audit at L); `shapes/operate.md` 25 and 56 (auditor plan review and final audit at L).
- Synthesis: 19.17, "every incident gets the auditor; below L, fix and publish save a fresh verifier or ui-reviewer check", which implies the auditor at L and above for fix and publish. The spine's list is therefore stale.
- Why blocking: SKILL.md survives compaction and the shape files may not; an incident run following the spine finishes without the audit 19.17 requires.
- Fix: in all five narrow-side files, replace the list with "build, move, every `fix/incident`, a feature with five or more claims, and any fix, publish, report, or operate run at L or above". In `references/long-running.md` 173-174, change "after the auditor's final audit passes" to "after the final audit passes".

### B7 · `mitigate` is used as a phase name, and the incident mitigation is placed before the wrong phase

- Side A: `references/intake.md` 150: "`mitigate` runs before `reproduce`". `SKILL.md` 94-95: "`fix/incident` mitigates with a recorded undo before reproducing", and the fix phase order at line 85 omits `execute`. `templates/HUNT.md` 24-25: "fix/incident only, before reproducing".
- Side B: `shapes/fix.md` 14 and 28: "mitigate through `execute` before archaeology".
- Synthesis: section 5 lists the canonical phases and `mitigate` is not one; 19.17 says "`fix/incident` mitigation is an `execute` phase before `archaeology`".
- Why blocking: a plan line `- [ ] mitigate · ...` fails `drive.py lint --gate` and the STATE.md canonical-phase check.
- Fix: in `intake.md` line 150, write "an `execute` phase runs before `archaeology`, with its undo recorded first". In `SKILL.md` line 94-95, write "`fix/incident` adds an `execute` phase before archaeology that mitigates with a recorded undo". In `templates/HUNT.md` line 25, write "fix/incident only, in the execute phase before archaeology".

### B8 · publish.md lets a preview deployment count as Live Proof, and web.md always promotes to production

- Side A: `shapes/publish.md` 99: Done means "live proof passed on the deployed URL (the preview, or production when the goal asked for it ...)"; 21-22 promote only "when the goal asks for the site to be live".
- Side B: `references/definition-of-done.md` 70 and 151 ("a preview deployment is Local Proof"); `domains/web.md` 301 ("Preview-only results stay at Local Proof").
- Side C: `domains/web.md` 65 makes every site run end with "promote the tested version and prove production serves it".
- Synthesis: 19.4, "A site reaches Live Proof only when production serves the tested build; preview-only results are Local Proof". 19.17: deploy to a preview always, and to production "when the goal asks for a launch or a production target already exists, otherwise its rows stop at Local Proof with the promote command in the report".
- Why blocking: publish.md produces a Live Proof row that DoD and the auditor treat as a mirage; web.md publishes to production when the goal did not ask for it.
- Fix: in `publish.md` lines 20-22, write "Promote to production when the goal asks for a launch or a production target already exists; otherwise stop at the preview, keep the rows at Local Proof, and put the promote command in the report." In line 99, write "live proof passed on the production URL with a matching build stamp, or, when production was out of scope, every row stops at Local Proof with the promote command in the report". In `web.md` step 9, prefix "When production is in scope (`shapes/publish.md`),".

### B9 · web.md allows the design canvas

- Side A: `domains/web.md` 157-160: "The design canvas skill is off by default. Open it only when the goal asks for mockups or options, or a stakeholder ... must approve a direction".
- Side B: `references/capabilities.md` 398, `agents/designer.md` 24, `references/ui-verification.md` 84 ("Drive never invokes the `design` canvas skill").
- Synthesis: 19.5, "drive never invokes `anthropic-skills:simplify` or the `design` canvas".
- Fix: delete `web.md` lines 157-160. If a goal asks for options, state instead: "When the goal asks for options, the designer writes two to four directions into `design/DESIGN.md`'s decision log, chooses one by the rubric (grounding in the subject, distance from the defaults, legibility at phone width, contrast), and records the choice in DECISIONS.md."

### B10 · The citation-check evidence for report and site rows has three different paths

- DoD: `references/definition-of-done.md` 86: `test:.drive/proofs/<key>/r<n>/citations.txt::every citation resolves`.
- Report shape: `shapes/report.md` 25: `.drive/proofs/<key>/r<n>/citations.json`.
- Research and templates: `references/research.md` 231 (grader "writes `.drive/reviews/<date>-citations-<slug>.md`"); `templates/RESEARCH.md` 11; `templates/rubrics/report.md` 29.
- Synthesis: 19.12, "citation grading ... write JSON under `.drive/reviews/`"; 19.11 says for report rows `test:` means the citation check.
- Why blocking: the lint checks that a `test:` file exists and contains the name. A grader following research.md writes a file the DoD token does not point at, so no report row can pass Local Proof.
- Fix: pick one path and one format. Recommended, following 19.12: the grader writes `.drive/reviews/<date>-citations-<slug>.json`, and the row's token is `test:.drive/reviews/<date>-citations-<slug>.json::every citation resolves`. Apply that path in `definition-of-done.md` 86, `shapes/report.md` 25 and 51, `research.md` 231, `templates/RESEARCH.md` 11, and `rubrics/report.md` 29, and make sure the lint's `test:` check accepts a JSON file under reviews.

### B11 · A fix below M has no severe test, but Local Proof requires one

- Side A: `shapes/fix.md` 186-187: Done "carries `test:`, `severe:` (M and above), `verdict:`, `review:`". Line 173 gives S no severe tester, and line 174 adds severe tests only at M.
- Side B: `references/state-files.md` 193 and `references/definition-of-done.md` 54: Local Proof requires `test:`, `severe:`, and a passing `verdict:`.
- Synthesis: 4.4 rung table, with no size exception.
- Why blocking: every S fix row fails the lint at Local Proof and can never reach Done.
- Fix: in `shapes/fix.md` line 173, add "one severe test on an adjacent input by `drive:severe-tester`"; in line 187, drop "(M and above)". Adjust the fix test budget accordingly (S19 below).

### B12 · ios.md's surface names are not in the findings schema

- Side A: `domains/ios.md` 210: verdicts and manifests name the surface "`mcp` or `simctl+xcuitest`".
- Side B: `templates/ui-findings.schema.json` 19 enum (`ios-simulator-mcp`, `xcuitest+simctl`); `references/capabilities.md` 152-153; `references/ui-verification.md` 121-123.
- Synthesis: 15.4, "The verdict names the surface used" (no spelling); the schema is the enforced form.
- Why blocking: a findings.json written with ios.md's names fails schema validation.
- Fix: in `ios.md` line 210, write "(`ios-simulator-mcp` or `xcuitest+simctl`)".

### B13 · design.md has the architect write `contracts/`, regenerate consumers, and run suites

- Side A: `references/design.md` 37 ("`drive:architect` writes the capability map, DESIGN.md, `contracts/`, and the decision index") and 176-181 (a contract change "run by `drive:architect`": update schemas and fixtures, emit, "regenerate every consumer; run provider and consumer contract suites until both are green; commit once").
- Side B: `agents/architect.md` 20-23 ("Write only under `.drive/` and the documentation paths the brief names. Never edit source, tests, or configuration"; "Never run a git command that changes anything"). `references/parallel.md` 36-42 makes contracts a wave 0 package that implementers build.
- Synthesis: section 6 architect guard "`.drive/` and docs only"; 19.2 widens it to `.drive/`, `docs/`, `design/`, and `src/content/claims/`. `contracts/` is not in either, and committing belongs to the orchestrator.
- Why blocking: the guard refuses the architect's writes, and "commit once" breaks the rule that only the orchestrator commits.
- Fix: in `design.md` line 37, say the architect writes the contract's specification in DESIGN.md section 4, and the contract package itself is a wave 0 implementer package. In lines 176-181, write "A contract change is its own package: `drive:architect` specifies it in DESIGN.md section 4, a `drive:implementer` updates schemas and fixtures, emits, regenerates consumers, and runs both contract suites; you commit it as `contract: <change in words>`." If the architect should own `contracts/`, amend synthesis 19.2 first and update `architect.md`.

### B14 · `lint --final` requires every row at Done or Dropped, so an honestly stopped run can never run `drive.py end`

- Side A: `references/state-files.md` 237: `--final` adds "every row Done or Dropped". Synthesis section 9: `end` "removes `.drive/local/active` after `lint --final` passes".
- Side B: `SKILL.md` 340 ("Run `drive.py lint --final`, set `status: done` (or the honest stop status), run `drive.py end`"). `references/definition-of-done.md` 71-73 (device-only claims are never Done) and 290-291 (on a second no-go, "rows take the rung the last audit supports"). `shapes/publish.md` and synthesis 19.17 (publish rows stop at Local Proof when production is out of scope). `SKILL.md` 324-328 (stop conditions: budget bound, impossible goal, credentials).
- Synthesis: internally contradictory between section 9 and 19.9 and 19.17.
- Why blocking: every run that ends below Done leaves `.drive/local/active` in place. The Stop hook then allows stops only because status is `blocked`, `stalled`, or `aborted`, while the reinject and guard hooks stay live in that repository for every later session.
- Fix: amend synthesis section 9 so `end` requires `lint --final` when STATE.md says `done`, and `lint --stop` plus a committed REPORT.md opening "Stopped because <reason>" when status is `blocked`, `stalled`, or `aborted`. In `state-files.md` 237, change the `--final` rule to "every row at Done or Dropped, or at the rung its target allows with the reason recorded (`why:device-only:`, a DECISIONS.md narrowing, or a publish run without a production target)". Update `SKILL.md` 340 to name both paths.

### B15 · The intake commit lookup `tail -1` finds the wrong GOAL.md after a paused run

- Side A: `agents/auditor.md` 33, `agents/grader.md` 41, `references/verification.md` 366: `git show $(git log --diff-filter=A --format=%h -- .drive/GOAL.md | tail -1):.drive/GOAL.md`.
- Side B: `references/definition-of-done.md` 218 and `references/intake.md` 390-392: `git log --grep '^drive(intake): <slug>$' --format=%h -1`.
- Synthesis: 18.13 archives a paused run to `.drive/runs/<date>-<slug>/`, after which the new run adds `.drive/GOAL.md` again; 17.2 says the auditor reads "the intake commit of GOAL.md". `git log` lists newest first, so `tail -1` returns the oldest addition, which is the first run's goal.
- Why blocking: in any repository that ever held a second run, the auditor compares against another goal and flags or misses narrowings.
- Fix: in all three Side A files, use DoD's command: `intake=$(git log --grep '^drive(intake): <slug>$' --format=%h -1); git show "$intake":.drive/GOAL.md`. (B3 already deletes the grader row.)

### B16 · The plan-line checker vocabulary differs, and the lint enforces one of them

- Side A: `references/state-files.md` 120: `checker: <orchestrator|verifier|grader|auditor>`, copying synthesis 4.2.
- Side B: `references/intake.md` 395 adds `ui-reviewer` and `security-reviewer`, and its example plan uses `checker: security-reviewer` at line 455.
- Synthesis: 19.17 amends 4.2: "plan-line checkers may name any roster agent".
- Why blocking: state-files.md section 9 says the lint checks plan lines. A lint built from state-files' grammar rejects intake.md's example and every shape file that names `drive:ui-reviewer` or `drive:architect` as checker.
- Fix: in both files, write `checker: <orchestrator | any roster agent name>`.

### B17 · At XS the security reviewer writes a file under `.drive/`

- Side A: `agents/security-reviewer.md` 66: "Write `.drive/reviews/<date>-security-<slug>.md` with a Bash heredoc". Line 35 handles XS diff reading but not output.
- Side B: `references/security.md` 38: at XS "no file, findings return in its final message and the commit body records the counts".
- Synthesis: 19.14, "at XS the reviewer returns findings in its final message"; section 3, XS runs create no `.drive/`; section 12 eval "XS restraint (a one-line fix must not create `.drive/`)".
- Why blocking: the XS restraint eval fails whenever `auth` applies at XS.
- Fix: in `security-reviewer.md` Report, add "At XS, write no file: return the range, path taken, and findings by severity in your final message, within 1,500 characters."

---

## Should fix

### S1 · iOS device roles are read from a committed path in two files

- Side A: `references/ui-verification.md` 168 and `templates/design/screens.yaml` 12: `.drive/ios/devices.json`.
- Side B: `domains/ios.md` 54 and 143: `.drive/local/ios/devices.json` (machine-local), which `env.sh` reads.
- Synthesis: 19.9, "device UDIDs and raw result bundles live in gitignored `.drive/local/ios/`".
- Fix: change both Side A paths to `.drive/local/ios/devices.json`.

### S2 · intake.md's example plan names the verifier as spec and design checker

- Side A: `references/intake.md` 449-450: spec and design lines use `checker: verifier`; the design exit even says "architect review has no blocking finding".
- Side B: `references/spec.md` 229-231 and `references/design.md` 39-40 (fresh `drive:architect` at S and M for feature); `SKILL.md` 234.
- Synthesis: section 6 roster and 13 "Spec author model".
- Fix: change both checkers in the example to `architect`.

### S3 · The publish content plan lives in SPEC.md in two files and in `.drive/content-plan/` in three

- Side A: `shapes/publish.md` 31 (artifact "SPEC.md") and 42 ("SPEC.md holds three sections. Positioning ... Site map ... Page briefs"); `references/spec.md` 48.
- Side B: `domains/web.md` 73 and `references/intake.md` 254: `.drive/content-plan/` with `positioning.md`, `sitemap.yaml`, `briefs/<page>.md`.
- Synthesis: 19.3, "Publish runs keep positioning, site map, and page briefs in `.drive/content-plan/`".
- Fix: in `publish.md` line 31 set the artifact to "`.drive/content-plan/` (positioning, site map, page briefs); the claims ledger in the site's content directory", and rewrite line 42's opening as "`.drive/content-plan/` holds three parts". In `spec.md` line 48, say the publish content plan is written to `.drive/content-plan/` and SPEC.md holds only the site's behavioural claims.

### S4 · DECISIONS.md entries have three grammars

- Side A: `references/state-files.md` 206-215 (Context, Decision, Rejected, Undo with reversal cost, Evidence, Narrows), which the new `templates/DECISIONS.md` follows.
- Side B: `references/intake.md` 478-480 (the decision as a plain claim, reason, strongest alternative, reversal cost now and after the next milestone, and a status `assumed`, `confirmed`, `overturned`).
- Side C: `references/design.md` 213-214: "DECISIONS.md gets one line per design decision with its undo and a pointer".
- Synthesis: 19.12 "a one-line pointer and undo in DECISIONS.md" for design records; state-files.md section 9 says the lint checks "Decision and Undo on every entry".
- Fix: in `intake.md` 478-480, replace the field list with a pointer to `state-files.md` section 8. In `design.md` 213-214, say the design decision's DECISIONS.md entry uses the standard grammar with `Decision:` as the one-line pointer to the DESIGN.md record and `Undo:` filled, so the lint accepts it.

### S5 · The research reconciliation threshold differs

- Side A: `shapes/report.md` 23: "a researcher with `model: "opus"` reconciles above four lanes".
- Side B: `references/research.md` 216-217: "For two or more lanes, spawn one `drive:researcher` with `model: "opus"` to reconcile".
- Synthesis: section 6, "`researcher` to `opus` for reconciliation", no threshold.
- Fix: in `report.md` line 23, write "a researcher with `model: "opus"` reconciles whenever two or more lanes ran".

### S6 · Saved source text has two locations

- Side A: `shapes/report.md` 23: `.drive/local/sources/<slug>-<date>.md`.
- Side B: `references/research.md` 207: `.drive/local/research/sources/<source>-<date>.txt`.
- Synthesis: 19.12, "lane reports and saved page text under gitignored `.drive/local/research/`".
- Fix: change `report.md` line 23 to research.md's path.

### S7 · `/code-review` level for fixes and S features

- Side A: `shapes/fix.md` 33 and `shapes/feature.md` 29: `/code-review high <baseline_sha>...HEAD` for every size.
- Side B: `references/verification.md` 157 and `references/capabilities.md` 375: "medium for `fix` and size S, high for M, L, XL and any auth or data diff".
- Synthesis: 19.5, "`/code-review` runs at `medium` for fix and S, `high` otherwise, never `ultra`". The "any auth or data diff" clause is an addition that leaves a fix with an auth diff ambiguous.
- Fix: in `fix.md` and `feature.md`, write `/code-review <level> <baseline_sha>...HEAD` with the level from `verification.md` section 5. In `verification.md` and `capabilities.md`, either drop "and any auth or data diff" or state that it overrides the fix rule, and amend 19.5 to match.

### S8 · Whether a fix runs `/simplify`

- Side A: `references/verification.md` 162 and `references/capabilities.md` 379 skip simplify only "for `fix` at S". `SKILL.md` 222 lists it for "anything at S or above" with no exception.
- Side B: `shapes/fix.md` harden (line 34) has no simplify step.
- Synthesis: 19.17, "fixes skip `/simplify`".
- Fix: in `verification.md` 162 and `capabilities.md` 379, write "skipped at XS, for every `fix`, and for `move` before cutover is proven". In `SKILL.md` 222, add "(never for a fix)".

### S9 · The implementer is allowed one git command that the spine and guard forbid

- Side A: `agents/implementer.md` 19-21 ("restore it (`git checkout -- <path>` ...); that restore is the only git command you may run that changes anything"); `references/parallel.md` 118 (rules block, same).
- Side B: `SKILL.md` 236 ("never touches git"); synthesis section 6 implementer guard "no git mutations".
- Why it matters: if `drive.py hook-guard` enforces section 6, the maker's rule is unfollowable and it reports an accident it cannot repair.
- Fix: in both Side A files, replace the restore instruction with "If you changed anything else by accident, list it in the report's `files` field with 'accidental'; never restore it yourself. The integrator reverts drift at integration (`parallel.md` section 7 step 2)." Alternatively, amend synthesis section 6 to allow `git checkout -- <owned or accidental path>` and make the spine say so.

### S10 · A partial package is resumed with SendMessage in two files and re-dispatched in another

- Side A: `references/parallel.md` 235 ("Resume the same agent once with `SendMessage`"); `references/models.md` 183.
- Side B: `references/state-files.md` 280 ("re-dispatch once, as a workaround ledger row"); `references/lessons.md` 44-46 counts a fresh worker on the same brief as a workaround.
- Synthesis: silent.
- Fix: choose SendMessage resume when the agent id is still valid in this session (it keeps the cache), and a fresh re-dispatch from the brief after a resume or compaction; both count as one workaround ledger row. Write that sentence in both files.

### S11 · The report shape has one verifier write both the refutation and the verdict for the same claim

- Side A: `shapes/report.md` 25: the verify phase's adversarial reader "(drive:verifier)" writes `refutations.md` (the row's `severe:` token) and `verdict.json`.
- Side B: `references/verification.md` 44-47: "One agent never holds two roles for the same claim ... a verifier never writes tests, so the tests it runs were not written to pass its check."
- Also: `templates/rubrics/report.md` 48 names a "critic file from drive:investigator" for completeness, while report.md gives completeness to the verifier.
- Fix: in `report.md` line 25, split the adversarial reader (a fresh `drive:verifier` instance that writes `refutations.md`) from the verdict (a second fresh `drive:verifier` that re-reads the refutations and writes `verdict.json`), and name the completeness check in one place, matching the rubric or changing the rubric's oracle to that verifier.

### S12 · Dispute rulings have two vocabularies, and the schema says the auditor writes DECISIONS.md

- Side A: `references/ui-verification.md` 309-310 (ruling "`upheld` or `overruled`"); `templates/ui-findings.schema.json` 180 and 210, and 211 ("DECISIONS.md entry written by drive:auditor").
- Side B: `references/verification.md` 206 and `agents/auditor.md` 55-56 (rules `defect`, `not_a_defect`, or `rubric_ambiguous`; "Write no file; the orchestrator logs the ruling"). `references/state-files.md` 72: DECISIONS.md writer is the orchestrator only.
- Synthesis: section 5, "the ruling is logged in DECISIONS.md" by the orchestrator (implied by 4 and 6).
- Fix: keep `upheld` and `overruled` as the findings status for UI disputes but map them explicitly in `ui-verification.md` 309-310: "the auditor rules `defect` (finding upheld) or `not_a_defect` (overruled); `rubric_ambiguous` applies the stricter reading and amends the rubric". In the schema line 211, change "written by drive:auditor" to "written by the orchestrator from the auditor's ruling".

### S13 · Review confidence uses words in two files and the numeric scale elsewhere

- Side A: `references/spec.md` 260 and `references/design.md` 263: confidence `high | medium | low`.
- Side B: `references/verification.md` 132 ("Confidence uses one scale everywhere: 100 ... 75 ... 50 ... 25 ... 0"); `agents/auditor.md` 20; `templates/ui-findings.schema.json` 178.
- Synthesis: 16.4 requires confidence; 4.5 adopts report 07's scale.
- Fix: change both review formats to `25 | 50 | 75 | 100`. (RESEARCH.md's high/medium/low is claim confidence in the ledger, a different field; leave it.)

### S14 · Design review and consistency files carry JSON in a `.md` file

- Side A: `references/design.md` 225-226 ("`drive:grader` writes JSON to `.drive/reviews/<date>-design-consistency-<slug>.md`") and 255 ("`.drive/reviews/<date>-design-<slug>.md`, JSON first and a readable rendering after"); `agents/architect.md` 64-66; `templates/DESIGN.md` 6; `templates/capability-map.md` 3.
- Synthesis: 19.12, "design reviews, citation grading, and design consistency checks write JSON under `.drive/reviews/`", and 19.11 uses `.json` for the final audit.
- Fix: use `.json` for the design review, the design consistency check, and the capability-map check, and drop "a readable rendering after". Update all five places.

### S15 · verification.md's role table says reviewers write nothing, and its guard paragraph omits their allowed paths

- Side A: `references/verification.md` 35-39 (grader, security reviewer, arbiter, and final auditor "write nothing"; verifier "command output under `.drive/proofs/` only") and 88-91 (the UI reviewer "writes only under `.drive/proofs/`").
- Side B: `agents/security-reviewer.md` 66 and `agents/auditor.md` 27-28 (write under `.drive/reviews/`); `agents/grader.md` 30-31 (the output path the brief names); `agents/ui-reviewer.md` 22-23 (also `.drive/local/ui/`); `agents/verifier.md` 63 (also `/private/tmp`).
- Synthesis: 19.1, 19.13, 19.14.
- Fix: update the Writes column and the guard paragraph to those paths (and to the B4 amendment).

### S16 · When CONSTRAINTS.md is written

- `SKILL.md` 140-141: at intake, in the Plan step.
- `references/testing.md` 158 and `templates/CONSTRAINTS.md` 6: at test-plan, or at archaeology for existing code.
- `shapes/build.md` 29 and 75: measured after wave 0.
- `shapes/feature.md` 26: at test-plan.
- Synthesis: 18.1 gives only "For M and above", measured values.
- Fix: settle on "at archaeology for existing code, after wave 0 for a greenfield build (nothing exists to measure before), before the first integration commit in every case". Apply in SKILL.md, testing.md, the template, and feature.md.

### S17 · The capability map is a separate file everywhere except build.md

- Side A: `shapes/build.md` 52-53: "write a capability map at the head of SPEC.md".
- Side B: `references/design.md` 72, `references/spec.md` 60, `agents/architect.md` 30, `templates/capability-map.md`: `.drive/capability-map.md`.
- Synthesis: 19.12, `.drive/capability-map.md`.
- Fix: in `build.md` line 52-53, write "write `.drive/capability-map.md` from `templates/capability-map.md` before SPEC.md", and replace the inline example with a pointer to the template.

### S18 · Which sizes need the walking skeleton live at the end of wave 0

- `shapes/build.md` 71-74: whenever live is in scope.
- `references/intake.md` 366: XL only.
- `references/definition-of-done.md` 119-120: L and XL.
- Synthesis: silent.
- Fix: choose one (L and above is the most defensible, because below L there is usually one surface) and write it in all three.

### S19 · The fix test budget contradicts the fix procedure and its own rubric

- Side A: `references/testing.md` 89 (the reproduction plus at most one boundary test; "a third new test means the hunt became a feature") and `templates/rubrics/fix.md` 47 ("at most two new tests").
- Side B: `shapes/fix.md` 136-137 (the class fix adds "a test that generates the violating shape"); `shapes/fix.md` 34 and 174 (severe tests in harden); `templates/rubrics/fix.md` 43 (at least two adjacent inputs proven by severe tests); `agents/investigator.md` 51 (a test for a further predicted failure); B11 (a severe test at S).
- Fix: in `testing.md` 89, count only maker-written tests: "the failing reproduction plus at most one boundary test; severe tests from `drive:severe-tester` (one per adjacent input, at least one) and the class-fix shape test are counted separately". Change `rubrics/fix.md` 47 to match.

### S20 · Feature at S has no SPEC.md in feature.md

- Side A: `shapes/feature.md` 83: "claims live in STATUS; design and test plan are lines in GOAL.md's plan".
- Side B: `references/intake.md` 363: "a SPEC.md under 300 words for a feature or build".
- Synthesis: 19.10, "a size-S feature or build writes a short SPEC.md under 300 words".
- Fix: in `feature.md` line 83, add "a SPEC.md under 300 words (claims, refuting scenarios, Must not change)".

### S21 · Blast radius and Dialect sections do not exist in the change-spec template, and archaeology writes them

- Side A: `shapes/feature.md` 23 (archaeology artifact "SPEC.md sections Blast radius and Dialect") and 63 ("record their shape in SPEC.md's Dialect section").
- Side B: `templates/change-spec.md` has "Where it lands" (lines 13-19) with patterns and consumers, and no Blast radius or Dialect heading. `references/state-files.md` 73 makes the architect the writer of SPEC.md; archaeology runs on `drive:researcher` before the spec exists.
- Synthesis: 19.17, "blast radius and dialect notes are sections of SPEC.md (or change-spec)".
- Fix: add `## Blast radius` and `## Dialect` sections to `change-spec.md`. In `feature.md` line 23, have archaeology record both in `how-it-works.md` (which already has a Blast radius table) and have the architect copy them into the change spec at the spec phase.

### S22 · DESIGN.md has no `## Operations` or `## Threat model` section

- Side A: `references/observability.md` 38 and 42 (on-call questions "in DESIGN.md under `## Operations`"); `references/security.md` 40 and 82 (`## Threat model` in DESIGN.md at M and above).
- Side B: `templates/DESIGN.md` 61 ("## 8. Observability") and 94 ("## 14. Security boundaries"); `references/design.md` 101 and 107 list the same section names.
- Synthesis: 19.14, "the threat model lives in DESIGN.md ...; on-call questions live in DESIGN.md `## Operations`".
- Fix: rename section 8 in `templates/DESIGN.md` and `design.md` to "## 8. Operations" (with the on-call table from observability.md section 2), and add "### Threat model" under section 14 with security.md section 2's table and abuse cases; point security.md and observability.md at those exact headings.

### S23 · TESTPLAN.md's severe section says the severe tester writes it

- Side A: `templates/TESTPLAN.md` 37: "Written by drive:severe-tester."
- Side B: synthesis section 6 guard for `severe-tester` ("test paths and `.drive/proofs/` only"); `references/state-files.md` 73 (TESTPLAN.md writer is the architect, then the orchestrator); `references/security.md` 76-79 (abuse cases planned from the threat model).
- Fix: change the comment to "Planned by drive:architect from the threat model's abuse cases; test names from the severe tester's report are copied in by the orchestrator."

### S24 · move.md's MIGRATION.md skeleton and size disagree with the template

- Side A: `shapes/move.md` 42-58 (headings Charter, Invariants, Consumers, Known-wrong behaviour, Stages, Parity, Undo ledger); line 29 checks "MIGRATION.md Charter"; line 158 creates MIGRATION.md at M.
- Side B: `templates/MIGRATION.md` (Current state, Target state, Point of no return, Invariants, Consumer inventory, Characterization with Known-wrong behaviour, Parity, Requirements, Expand and contract, Stages, Backups, Undo ledger, Rollback drill, Soak record, Decommission); line 2 allows size `<L|XL>` only. `references/design.md` 53 says any size.
- Synthesis: state-files.md 9-10 says the template wins on field names.
- Fix: replace move.md's inline skeleton with a heading list that matches the template and a pointer to it; change line 29's exit to "MIGRATION.md Current state, Target state, Invariants, Consumer inventory". In the template header, allow `<M|L|XL>`.

### S25 · fix.md's HUNT.md skeleton disagrees with the template

- Side A: `shapes/fix.md` 27 ("eight brief fields") and 40-61 (Symptom, Frequency, Environment with running build, Since, Impact with Trigger, Prior, Harness, Repro; then Ledger, Attempts, Verification, Post-mortem).
- Side B: `templates/HUNT.md` 9-22 (eleven brief fields, including Evidence, Running build, and Repro cmd as separate lines) and sections Mitigation, Claims, Reproduction, Hypothesis ledger, Attempt ledger, Fix, Verification, Re-classification, Post-mortem.
- Fix: replace the fix.md skeleton with the template's section list and a pointer; change "eight brief fields" to "the brief fields in `templates/HUNT.md`".

### S26 · Whether an S run with existing code writes how-it-works.md

- Side A: `references/research.md` 240: "For every run with `existing-code`, `drive:researcher` writes `.drive/how-it-works.md`".
- Side B: `references/intake.md` 206 (at M and above; at S, Verified facts in STATE.md); `shapes/fix.md` 29 (M+); `references/state-files.md` 38-40 (S creates only GOAL, STATE, STATUS, and the shape's ledger).
- Synthesis: section 4, S file list.
- Fix: in `research.md` 240, write "at M and above ... ; at S, the same findings go to STATE.md Verified facts".

### S27 · web.md's site order differs from publish.md and SKILL.md

- Side A: `domains/web.md` 50-65: research, content-plan, design, build (wave 1), draft, build (wave 2), `verify` (local gates then preview deploy), `design-qa` on the preview, then deploy, live-proof, `docs`, report.
- Side B: `shapes/publish.md` 27-38 and `SKILL.md` 88: research, content-plan, design, build, draft, design-qa (on the build output, line 35), deploy (preview), live-proof, retro, report; no verify or docs phase, and no retro in web.md.
- Synthesis: section 5 says each shape file lists its order; the domain file should defer.
- Fix: rewrite web.md section 3 to follow publish.md's phase names and order, keeping the second build wave as part of `build` after `draft` only if publish.md is changed to allow it; put the preview gates inside `deploy` and `live-proof`, and add `retro`.

### S28 · web.md says the writer has `writing` preloaded

- Side A: `domains/web.md` 36: "`drive:writer` (preloaded; ...)".
- Side B: `agents/writer.md` 18-20 (invokes the prose skill named in the brief with the Skill tool); synthesis 15.1 writer preload "none".
- Fix: change the cell to "`drive:writer`, invoked with the Skill tool as the brief names (`writing` or a `<plugin>:writing` variant)".

### S29 · design.md sends move and migration design review to different reviewers

- Side A: `references/design.md` 53-54: `move/migration` at any size reviewed by `drive:auditor`; `move/refactor` and `move/upgrade` by "the verifier".
- Side B: `shapes/move.md` 31 (fresh architect at S to M, auditor at L to XL); `references/models.md` 104; `SKILL.md` 234 and 244.
- Synthesis: section 6 and 13, auditor reviews "at L to XL build and move"; architect at S to M.
- Fix: in design.md's table, use "fresh `drive:architect` at S and M, `drive:auditor` at L and XL" for both move rows.

### S30 · capabilities.json at S, and preflight before a paused run is archived

- Side A: `SKILL.md` 78 (capabilities "Unless the size is XS", in the probe step, before size is decided at step 5 and before `init` at step 6); `references/capabilities.md` 26-31 (every size except XS; the script "creates `.drive/` if it does not exist").
- Side B: `references/state-files.md` 47 (`capabilities.json` created at M and above); `references/intake.md` 96-97 (after size is known, and after `init` when a run was archived).
- Why it matters: SKILL.md's order writes capabilities.json into another goal's `.drive/`, which init then archives.
- Fix: move the capabilities sentence in `SKILL.md` from step 2 to the start of step 6, after `init`. Either add S to state-files.md line 47 or restrict the preflight to M and above everywhere; the first matches three files.

### S31 · The paused-run archive commit

- Side A: `references/state-files.md` 336-338: `drive.py init` moves the state "in one commit", and a DECISIONS.md entry records the restore.
- Side B: `references/intake.md` 38-42: "Commit the archive in the intake commit", with the restore line written in STATE.md and no DECISIONS.md entry named.
- Synthesis: 17.1, GOAL.md committed "before any other work"; 18.13, init archives and records how to restore.
- Fix: settle on intake.md's version (archive, new GOAL.md, and the DECISIONS.md restore entry in the single `drive(intake): <slug>` commit), so GOAL.md remains the first commit; update state-files.md 336-338 to say init stages the move and the intake commit carries it.

### S32 · Development dependencies are "always" in intake.md and need a decision elsewhere

- Side A: `references/intake.md` 474: the Always tier includes "adding development dependencies".
- Side B: `SKILL.md` 153-154 ("new dependencies" need the undo in DECISIONS.md); `references/security.md` 281 ("A new dependency is allowed once DECISIONS.md records the package, exact version, purpose ...").
- Synthesis: 18.12 decision tiers, and 18.5 install-script and dependency gates.
- Fix: move development dependencies to the "Allowed once the undo is written" tier in `intake.md`.

### S33 · SKILL.md's override list omits the writer's story-mapping call

- Side A: `SKILL.md` 246-251: "do not pass `model` except for the overrides listed below" lists implementer, researcher, and the Opus 4.8 retry.
- Side B: `references/models.md` 84 (`writer` to `fable` for story mapping); `references/capabilities.md` 122 and 307; `shapes/publish.md` 34; `shapes/report.md` 24.
- Synthesis: 15.1, story mapping "is an Agent call with `model: "fable"` made by the orchestrator".
- Fix: add to SKILL.md's override sentence "`model: "fable"` on a `drive:writer` call for story mapping a substantial narrative".

### S34 · A security review file is used as the `review:` token that Done reserves for the final audit

- Side A: `references/security.md` 130 ("The findings file becomes a `review:` token on each row it covered"); `references/capabilities.md` 192.
- Side B: `references/state-files.md` 196 and `references/definition-of-done.md` 57 (Done needs "`review:` (final audit)").
- Synthesis: 4.4.
- Why it matters: a lint that only checks for a `review:` token lets a security review stand in for the final audit.
- Fix: amend 4.4 so the lint requires Done's `review:` path to match `*final-audit*` (or a shape's named close-check file), and in security.md 130 write "is cited on each row it covered as `review:.drive/reviews/<date>-security-<slug>.md`, which does not satisfy Done's final-audit requirement".

### S35 · Web page widths

- Side A: `references/verification.md` 316 and `templates/rubrics/publish.md` 42: 375, 768, and 1440 px. `references/definition-of-done.md` 153: "at three widths".
- Side B: `references/ui-verification.md` 170 and 376, `shapes/publish.md` 74, `domains/web.md` 286: 360, 768, 1280, and 1600.
- Synthesis: 19.13, "web widths are 360, 768, 1280, 1600".
- Fix: change all three Side A places to 360, 768, 1280, and 1600.

### S36 · The grader is handed correctness and judgment questions

- Side A: `references/parallel.md` 317-318 and the panel lenses at 330-334 (graders asked "Would the cited tests fail if the implementation were wrong? Name a plausible defect they would miss"); `shapes/operate.md` 27 ("drive:grader for a single simple read" at observe); `shapes/build.md` 27 and `shapes/feature.md` 26 (the grader checks that each test sits at "the cheapest real layer").
- Side B: `references/verification.md` 333-337 ("never hand a correctness check to the grader"); `agents/grader.md` 3 and 13-14 ("Never judges quality"); `references/models.md` 106-108 ("Never hand a tier-2 question to the grader"); `templates/rubrics/operate.md` 29 (each effect "read by drive:verifier").
- Fix: in the panel, run the three lenses as `drive:verifier` agents (read-only, no verdict file) or reduce the grader lenses to evidence-presence questions and leave the defect lens to the settling verifier. In `operate.md` 27, remove the grader clause. In build.md and feature.md test-plan exits, give the layer judgment to a fresh `drive:architect` reviewer and keep the grader for "every claim has a row and every double has a ledger row".

### S37 · The operate plan at S is written and checked by the orchestrator

- Side A: `shapes/operate.md` 25: plan work by "orchestrator at S" and exit checked by "orchestrator at S".
- Side B: synthesis section 5, "The orchestrator never certifies its own work", and `SKILL.md` 172-174 (only intake, archaeology, research completeness, decompose, and docs are self-checked).
- Fix: change the S checker to `drive:verifier`.

### S38 · Quarantining a flaky test adds a skip that the spine and the guard forbid

- Side A: `references/testing.md` 213-216 (skip the test with the runner's marker and a reason naming the ticket).
- Side B: `SKILL.md` 48 ("Never raise a tolerance, widen an assertion, add a skip ..."); synthesis 18.1, `drive.py guard` "blocks added suppression comments and skips".
- Fix: in `SKILL.md` 48, add "except a quarantine recorded under `references/testing.md` section 10"; in testing.md section 10, add a step recording the skip as an exception row in CONSTRAINTS.md with its DECISIONS.md entry, which the guard accepts as a recorded exception.

### S39 · ios.md asks the one question for a reversible choice

- Side A: `domains/ios.md` 383-385: "ask the one plain-text question (Team ID and bundle id) at intake".
- Side B: `references/intake.md` 482-488 test 4 ("The step it gates has no possible undo; anything with an undo is decided and logged instead"); `SKILL.md` 155; synthesis 18.12.
- Fix: replace with "build behind the protocol, set the rows to Partial with `why:blocked on team`, and name the Team ID and bundle id as owner steps in the report; do not ask".

### S40 · safety.md lands the retry's test through a worktree the investigator removes

- Side A: `references/safety.md` 110-112: the investigator "writes the test in a throwaway worktree and you land it through the worktree lane in `parallel.md`".
- Side B: `agents/investigator.md` 19-24 (detached worktrees, removed "in the same Bash command that finishes its work"; "a fix leaves as a patch file") and 29-31 (on a retry, save the test as a patch).
- Synthesis: section 7, worktrees merged or removed in the same step.
- Fix: in `safety.md`, write "it saves the test as a patch under `.drive/investigations/`, and you apply the patch in the shared checkout and commit it without reading its contents".

### S41 · The UI observation count for fix rounds

- Side A: `references/ui-verification.md` 226 ("A fix shape uses two observations per cell") and `templates/ui-findings.schema.json` 5.
- Side B: `agents/ui-reviewer.md` 49 and 72 (five observations per variant, required for a pass, with no fix exception).
- Fix: in `ui-reviewer.md`, add "(two per cell in a fix round)" at both places.

### S42 · Full-size screenshots are supposed to be gitignored but nobody writes the ignore rule, and proof screenshot names differ

- Side A: `references/ui-verification.md` 158-159: "The project's `.gitignore` carries `.drive/proofs/*/r*/shots/**/*.png` with the exceptions ...", with no agent or step assigned. Synthesis section 9: `init` adds only `.drive/local/` to `.gitignore`.
- Side B: `references/state-files.md` 236 (`lint --stop` requires a clean `git status --porcelain`, so untracked native PNGs block every stop).
- Naming: `references/verification.md` 260 (`shots/<screen>-<size>-<state>.png, two sizes per screen`) against `ui-verification.md` 151-154 and `ui-reviewer.md` 38 (`shots/<screen>/<cell>.png`, `.review.png`, `.tree.json`, crops).
- Synthesis: 19.13, full-size screenshots gitignored with hashes recorded.
- Fix: amend synthesis section 9 so `drive.py init` also adds the three shots patterns; in `verification.md` 260, use ui-verification's layout.

---

## Notes

### N1 · Device-only rows and Live Proof
`domains/ios.md` 369-372 lets a device-only row reach Live Proof with a physical-device bundle; `definition-of-done.md` 71 and `intake.md` 244 say "Local Proof at most". Synthesis 19.9 says only "may reach Local Proof ... and never Done". Fix: in DoD and intake, write "Local Proof without a physical device; Live Proof only with an `environment: device` bundle; never Done in a run without the owner's device".

### N2 · Smoke token under `.drive/local/`
`domains/cloudflare.md` 316 keeps the smoke token in `.drive/local/smoke.env`; `state-files.md` 37 says "No secret goes anywhere in `.drive/`". Fix: in state-files, write "No secret goes anywhere in `.drive/` outside `.drive/local/`, and a test credential there is rotated when the run ends".

### N3 · Stack files confirm or suspect different traits
`intake.md` 163-164 says an Xcode project confirms `ui`, and a wrangler file confirms `api`, `external-systems`, and `deploy-infra`; `ios.md` 20-21 only suspects `ui`, and `cloudflare.md` 26 only suspects `deploy-infra` and `external-systems`. Fix: align the domain files to intake.md.

### N4 · Investigator worktree naming
`agents/investigator.md` 21-22 uses `/private/tmp/drive-<slug>-<arm>`; `parallel.md` 264 and 289 and `shapes/fix.md` 114 use `/private/tmp/drive-$REPO-...`, matching synthesis 19.6. Fix: use `/private/tmp/drive-<repo>-<slug>-<arm>` in investigator.md.

### N5 · `hard: yes` against `hard: true`
`parallel.md` 46 and `agents/architect.md` 51. Fix: pick one and use it in `package-brief.md` when written.

### N6 · Turn limit with an Opus override
`parallel.md` 43-44 allows "120 turns (200 with an opus override)", but `agents/implementer.md` sets `maxTurns: 120` and the Agent tool has no per-call turn override. Fix: drop "(200 with an opus override)" or raise maxTurns.

### N7 · Handoff file key
`agents/verifier.md` 13 uses `.drive/handoffs/<key>.md`; synthesis section 4 and `verification.md` 51 use `<unit>` (a key or package id). Fix: `<unit>` in verifier.md.

### N8 · The walkthrough asks the reviewer why a control looked right
`ui-verification.md` 251-252 records "why it looked right" per step. Synthesis 16.3 bars asking an agent to explain its reasoning. The intent is a UX observation; rename the field "what on screen suggested it" so it asks for an observation, not reasoning.

### N9 · Maker self-review instructions
`agents/writer.md` 19-20 and `capabilities.md` 122 have the writer finish a docs page with the style skill's review checklist; `spec.md` 208-210 has the spec author run the cheat test on its own spec. Synthesis 16.2 bars telling makers to self-verify. These are style and authoring procedures rather than completion checks, but the checklist pass reads as self-review; consider moving it to the grader's docs check (`publish.md` already has a second writer do a revision pass).

### N10 · long-running.md names the auditor for every final audit
`long-running.md` 173-174, "after the auditor's final audit passes". Covered by B6's fix.

### N11 · Web capture tool order
`agents/ui-reviewer.md` 25-28 puts Playwright MCP first; `ui-verification.md` 118 makes the project capture script the first choice for web capture, with MCP for interaction. Fix: in ui-reviewer.md, write "capture with the project's capture script; Playwright MCP first for interaction and walkthroughs".

### N12 · Research claim classes
`intake.md` 284 says ledger rows are "verified fact, source claim, or assumption"; `agents/researcher.md` 42-44 uses "claimed by a source" and "contested"; `research.md` 117-122 and `templates/RESEARCH.md` 28 use verified fact, source claim, inference, unresolved conflict. Fix: use the template's four words in intake.md and researcher.md.

### N13 · WCAG version
`templates/design/DESIGN.md` 29 says WCAG 2.2 AA; `publish.md` 69, `ui-verification.md` 205, and `web.md` 244 test 2.1 AA tags. Fix: pick one.

### N14 · SKILL.md description differs from the synthesis frontmatter
`SKILL.md` 3 extends the description fixed in synthesis section 2. Harmless, but the synthesis presents it as exact; either amend section 2 or restore the text.

### N15 · The UI rubric has no template
`ui-verification.md` 319 has the orchestrator freeze `.drive/rubrics/ui.md` at the design gate; `verification.md` 286-288 has the architect copy `templates/rubrics/<shape>.md`, and there is no `templates/rubrics/ui.md`. Fix: add a template or say in verification.md that the UI rubric is built from ui-verification.md section 11.

### N16 · how-it-works tags
`shapes/feature.md` 41-42 uses `[ran: <command>]`, `[read: <path:line>]`, `[inferred]`; `templates/how-it-works.md` 5-10 uses `[read <path>:<line>]`, `` [ran `<command>`] ``, `[git ...]`, `[docs ...]`, `[inferred from ...]`. Fix: point feature.md at the template.

### N17 · Citation sampling
`rubrics/report.md` 43 samples "all claims when 30 or fewer, otherwise 30 percent at random plus every claim behind a recommendation"; `research.md` 233-235 grades every load-bearing citation and one in three of the rest. Fix: state one rule.

### N18 · When security review runs without `auth`
`SKILL.md` 221 says "when `auth` applies"; synthesis section 5 and `security.md` 21-25 add the surface list (untrusted input, derived paths, influenced outbound requests, model output). Fix: add "or the surface list in `references/security.md` section 1" to SKILL.md.

### N19 · Conformance grading scope
`SKILL.md` 220 runs the conformance grader for anything at S or above; `verification.md` 158 limits it to feature, build, move, publish, and report. Fix: add the shape list to SKILL.md.

### N20 · Headless recipe passes the Workflow rule by flag
`long-running.md` 88 uses `--allowedTools Workflow`; synthesis 19.8 says recipes pass the Workflow allow rule through `--settings`. The flag works for `-p`; either amend 19.8 to scope it to `--bg`, or pass `--settings "$DRIVE_SETTINGS"` in the headless recipe too.

### N21 · Read-at-start lists
`state-files.md` 263-265 reads general.md, domain and capabilities Learned constraints, and `.drive/LESSONS.md`; `SKILL.md` 62-63 and `long-running.md` 235-236 omit capabilities' Learned constraints and LESSONS.md. Fix: align SKILL.md and long-running.md to state-files.md.

### N22 · Which verdict moves a `[ui]` row
`state-files.md` 95 and `definition-of-done.md` 63 say "Only a verifier's verdict moves a row to Local Proof or above"; `ui-verification.md` 293 puts the ui-reviewer's verdict on the `[ui]` row. Fix: write "a verifier's or, for `[ui]` evidence, the ui-reviewer's verdict".

### N23 · Final audit sampling
`definition-of-done.md` 237-238 also samples every row whose target was lowered; `agents/auditor.md` 37-38 and `verification.md` 369-370 do not. Fix: add lowered-target rows to both.

### N24 · Simplify revert command
`capabilities.md` 381 reverts a failed simplify with `git restore --staged --worktree -- .`. Synthesis 18.19 allows restoring only owned paths or `git reset --keep`. The tree is clean before simplify, so the effect is the same, but name the paths simplify touched instead of `.`.

### N25 · state-files.md points at a canonical phase list SKILL.md does not have
`state-files.md` 126: "Phase names are the canonical ones in SKILL.md"; SKILL.md carries only per-shape orders, without `execute` for incidents. Fix: point at synthesis section 5's list reproduced in `intake.md`, or add the list to SKILL.md.

### N26 · Where UI review sits
`intake.md` 173 puts the UI review at `verify`, `design-qa`, and `live-proof`; `SKILL.md` 222 and `ui-verification.md` 40 put it in the hardening order. Fix: say "harden (verify for fix and move)" in intake.md.

### N27 · Architect write paths
`agents/architect.md` 20 writes "under `.drive/` and the documentation paths the brief names"; synthesis 19.2 adds `design/` and the claims ledger at `src/content/claims/` (which `web.md` 55 and 87 assign to it). Fix: list the four paths in architect.md.

### N28 · "Nobody reviews your direction"
`agents/designer.md` 26 says nobody reviews the direction before the build; `ui-verification.md` 81-84 and `publish.md` 32 have a fresh reviewer check the design gate. The designer line means no human approval. Fix: "No person approves your direction; a fresh reviewer checks the contract at the design gate."

### N29 · The severe tester filters below 50
`agents/severe-tester.md` 59-60 reports findings at 50 and above and lists 25-level items under untested risk; synthesis 16.4 says reviewers report every finding and filtering happens later. Nothing is dropped, so this is wording; say "Report every finding with its score; list 25-level items under untested risk".

### N30 · Empty range handling
`capabilities.md` 374 says a zero `rev-list` count means "skip every diff review and record 'empty range'"; `security-reviewer.md` 28 reports `blocked` on an empty range. Fix: align on one outcome.

### N31 · XS security record in the commit body
`intake.md` 190 quotes "the review's verdict line and each finding's disposition"; `security.md` 38 records "the counts"; `definition-of-done.md` 97 wants "verdict line and dispositions". Fix: use DoD's form in security.md.

### N32 · web.md gives `imagegen` to an agent without the Skill tool
`domains/web.md` 40 assigns `imagegen` to `drive:designer`, whose tools (synthesis 6 and 15) have no Skill; `capabilities.md` 121 names it to the implementer. The designer can still run the `imagegen` CLI through Bash. Fix: say "the `imagegen` CLI through Bash" in web.md, or move the job to an implementer package.
