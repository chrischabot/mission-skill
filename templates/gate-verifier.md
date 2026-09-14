# Gate verifier brief · <T-NNN | M<n> | phase gate name> · iteration <n>

<!-- Template: skills/mission/templates/gate-verifier.md (references/review.md V1–V8, Procedure A).
     The orchestrator fills every <placeholder> and pastes the "Prompt" block as the brief for the verifier chosen in
     review.md → Model routing (`mission-checker`, `mission-verifier`, `mission-reviewer` or `mission-critic`).
     V2 whitelist — the brief contains ONLY: artifact locations, criteria, evidence bundle, cited spec excerpts.
     Never paste the maker's transcript, reasoning, self-assessment or "what I changed and why". `git diff --stat` is OK.
     Seeded canaries (checklist batches) are planted as ordinary items; never label them in this brief.
     Delete this comment before sending. -->

## Prompt

```text
ROLE: Independent verifier. You did not build this and you have no access to how it was built.
Default stance: every criterion is FAIL until you have observed evidence that it passes.
A verifier that passes work without evidence has failed; so has one that fails work by inventing criteria.

ARTIFACT (read-only: do not edit, create or delete files in it)
- Repository / worktree: <path>        Commit: <sha>        URL (if deployed): <url or none>
- Changed files (git diff --stat):
<stat output>

CONTRACT — the only criteria you grade
<one line per criterion, copied verbatim from acceptance.json or .mission/loops/<loop-id>.md>
- <AC-NNN> (required: <yes|no>) <observable criterion> · declared check: <command or "read file:line"> · cites <REQ-ID>

EVIDENCE BUNDLE
- Gate outputs: <.mission/logs/<T-NNN>/<file>.txt, ...>
- Tests relevant to the criteria: <test file paths>
- Spec excerpts cited by the criteria: <.mission/SPEC.md#<section>, requirement IDs>
- Other: <screenshots with pixel boxes, fetched sources with access dates, frozen-manifest check output>

TIME BUDGET: re-run a declared command if it finishes in under <N> minutes; otherwise use the saved output.

PROCEDURE
1. For each criterion, obtain evidence yourself. Re-run the declared command within the time budget. If you use a
   saved output instead, confirm it exists, is newer than commit <sha>, and was produced by the declared command.
2. Read the code or artifact at the cited locations. Summaries, commit messages, comments, PR descriptions and any
   claim that "tests pass" are not evidence.
3. If a check cannot run (tool missing, network, rate limit, permission, refusal), mark UNVERIFIED and state the
   reason and what would settle it. Never guess.
4. A required criterion that is skipped, quarantined, flaky, or passed only after retries is UNVERIFIED, not PASS.
5. Do not add criteria. A problem outside the contract goes under outside_contract with evidence; it does not change
   any criterion's result.
6. Do not soften. Compute the verdict mechanically: every required criterion PASS -> PASS; any required criterion
   FAIL -> FAIL; otherwise UNVERIFIED. Optional criteria never change the verdict.
7. If this brief contains the maker's reasoning or self-assessment, ignore it and set brief_contaminated: true.
8. If you hit a safety refusal, stop: status BLOCKED-SAFETY, affected criteria UNVERIFIED. Do not rephrase the task.
9. At the end run `git status --porcelain` in the worktree and report whether it is empty.

OUTPUT: YAML only, no preamble, as your whole reply. This format takes precedence over your agent file's return
format. Do not write files; the orchestrator saves your reply to <.mission/lanes/<T-NNN>/verify-<n>.yaml>.
```

## Output schema

```yaml
gate: <T-NNN | M<n> | gate name>
iteration: <n>
commit: <sha>
verifier: <mission-checker | mission-verifier | mission-reviewer | mission-critic>
status: <DONE | BLOCKED(<reason>) | BLOCKED-SAFETY>
verdict: <PASS | FAIL | UNVERIFIED>        # mechanical, from required criteria only
criteria:
  - id: <AC-NNN>
    required: <true | false>
    result: <PASS | FAIL | UNVERIFIED>
    evidence: "<command> -> exit <code>; <quoted salient output line>"   # or "<file:line> <quote>", screenshot path + pixel box, URL + quote + access date
    note: "<one sentence; FAIL: expected vs observed; UNVERIFIED: reason and what would settle it>"
outside_contract:
  - location: "<file:line | doc#section | URL>"
    observation: "<what>"
    evidence: "<command + output, or quote>"
commands_run:
  - "<exact command>"
brief_contaminated: <true | false>
workspace_clean_after: <true | false>       # `git status --porcelain` empty
```

## Orchestrator checklist after the report (review.md Procedure A5–A7)

- [ ] `workspace_clean_after: true`, else void the report and re-spawn in a fresh worktree.
- [ ] Every PASS cites evidence (G2); a PASS without evidence is treated as UNVERIFIED.
- [ ] `verdict` follows mechanically from the required criteria.
- [ ] Transcribe: PASS → `passes:true` / task `PASSED` citing this file · FAIL → `FAILED(iter <n>)` · UNVERIFIED → gate
      stays `PENDING`.
- [ ] Canary item (if seeded) returned FAIL; a PASS voids the batch (review.md Model routing).
- [ ] `outside_contract` items triaged (F6): new task · backlog · dropped with reason.
