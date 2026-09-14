# Test-diff audit · <T-NNN | M<n>> · candidate <sha> · base <sha> · auditor <mission-verifier | mission-critic>

<!-- Template: skills/mission/templates/test-diff-audit.md (references/testing.md G-4..G-8, B-5, W-4, Protocols A/B).
     Pasted into the verifier brief. Order is fixed: §A deterministic pre-pass first (its exit code is final), then
     §B questions, §C bloat audit, §D protocol evidence when the task is a bug fix or a migration, §E verdict.
     Auditor: mission-verifier at S/M; mission-critic at L/XL or whenever the diff touches frozen paths, goldens,
     snapshots or test configs, and for the rest of the mission after any cheating signal. Delete this comment. -->

## A. Deterministic pre-pass (run in a clean worktree at the candidate)

```bash
git worktree add .mission/tmp/audit-<sha> <sha>          # or the verifier's own scratch checkout
cd .mission/tmp/audit-<sha>
git show <base>:.mission/frozen-manifest.sha256 > .mission/tmp/base-manifest
.mission/bin/frozen-manifest.sh check --manifest .mission/tmp/base-manifest   # exit 1 = frozen file changed/missing/added
.mission/bin/test-diff-grep.sh --base <base> --head <sha>                     # exit 1 = flags
git diff --stat <base> <sha>                                                    # which areas changed
git diff --name-only <base> <sha> -- <test dirs>                                # test-only diff? (G-8)
```

| Check | Exit | Findings (verbatim FLAG / CHANGED lines) | Disposition cited (quarantine row, D-entry) |
|---|---|---|---|
| Frozen manifest | <0 \| 1> | <none> | <—> |
| Grep pre-pass | <0 \| 1> | <none> | <—> |
| Test-only diff (tests changed, no source changed) | – | <yes \| no> | yes → full audit; L/XL → full-suite run recorded in the report |

Any finding without a cited disposition is BLOCKING. A model answer below never overrides §A.

## B. Review questions (answer each with file:line evidence or "none")

1. **Deleted or renamed tests.** Did any test disappear or move? For each: which test with the same `@req:` oracle
   supersedes it (B-7), and does that test still fail under oracle-bite?
2. **Weakened assertions.** Exact → partial (`toEqual` → `toContain`/`toBeDefined`), equality → existence, widened
   numeric/snapshot tolerance, fewer expected items, a removed assertion, `expect` moved inside a branch that may not run.
3. **Special-casing.** Does production code contain literals, branches or lookup tables that match fixture values
   (ids, emails, amounts, prompt strings) instead of general logic? Grep the fixture literals in source.
4. **Goldens and snapshots.** Did any golden, snapshot or recorded fixture change? Is there a linked requirement change
   (SPEC/registry diff + D-entry)? Regenerated from the new code without review = BLOCKING.
5. **Configs and setup.** Changes to test configs, setup files, reporters, `include`/`exclude`, retries, timeouts,
   `passWithNoTests`, `forbidOnly`, network guard, assertion-library helpers or custom matchers?
6. **Test-only production paths.** `NODE_ENV`/`isTesting`/launch-argument checks that change behaviour beyond the
   documented seeding/backend-URL seam?
7. **Test counts.** Gating test count per suite on candidate vs base (reporter JSON totals). Any decrease accounted for
   in Q1?
8. **Outcome vs activity.** Do new tests assert outcomes (persisted state, returned structure, rendered result, counted
   side effects) or only activity (called, did not throw, status 200, element exists)?
9. **Mock boundary.** Do new mocks replace the unit under test, the project's own database, router, runtime, queue or
   bindings, rather than a third-party network boundary behind a port?
10. **Red-before-green.** For each new acceptance/regression test: failing message on base recorded, and it is the
    expected symptom rather than a setup/import/compile error?

## C. Bloat audit (B-5; advisory unless it hides a missing oracle)

| Finding | Test(s) | Action |
|---|---|---|
| No `@req:` citation (counts for nothing toward DONE) | <path::name> | <add ID \| delete> |
| Asserts nothing observable | <…> | <rewrite \| delete> |
| ≥2 tests, same ID and arrange, literals differ | <…> | parameterise |
| Higher-level test duplicating a lower-level oracle | <…> | delete the slower one |
| Over budget (1 oracle + ≤2 cases) without a TEST-PLAN justification | <ID> | justify or merge |
| Broad test sole oracle for >3 unrelated required criteria (T-4) | <…> | add specific oracles |

## D. Protocol evidence (only when applicable)

Bug fix (Protocol A in `references/testing.md`):

- [ ] REPRODUCED gate evidence: command → exit ≠ 0 → symptom line
- [ ] Regression test committed alone before the fix, under a frozen path, citing `@req:<ID>`
- [ ] Fix commit does not touch the regression test (`git diff <fix-parent> <fix> -- tests/regression` empty)
- [ ] RED on the parent commit with the symptom message; GREEN on the fix; existing suite pass-to-pass
- [ ] Nondeterministic: p measured on unfixed code; n ≥ ln(α)/ln(1−p) consecutive clean runs (α 0.05; 0.01 for money,
      auth, data, concurrency; 2n without state reset) with the log path
- [ ] Oracle-bite: essential hunk reverted in a scratch worktree → regression test fails again
- [ ] Fix changes the confirmed mechanism, not a catch-ignore, retry or timeout bump (unless external transient, evidenced)
- [ ] Sibling sweep recorded, every hit dispositioned

Migration / extraction (Protocol B in `references/testing.md`):

- [ ] Inventory with PAR IDs exists and predates the move (commit order)
- [ ] Golden corpus recorded from the OLD system before code moved; normalisers reviewed; corpus frozen
- [ ] Judge check: corpus vs OLD 100% match; deliberately broken OLD build detected
- [ ] NEW replay: 100% on P1 PAR IDs; every P2 mismatch dispositioned with a D-entry
- [ ] Side-effect parity (rows, events, provider-call counts) compared per request
- [ ] No behaviour change in the move PR (diff contains no new criteria beyond parity)
- [ ] Shadow/cutover gates stay PENDING-LIVE until staging/production evidence exists

## E. Verdict

- Audit verdict: **CLEAN** | **BLOCKING(<Q-number or §A check: file:line>, …)** | **ADVISORY(<§C items>)**
- Escalation: <none | held-out failure or special-casing signal → next audits on mission-critic, H-1 enabled, lesson
  candidate L-NNN>
