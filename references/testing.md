# Testing: hard oracles, no bloat, no cheating

Functional testing for every shape: requirement → oracle traceability, test budgets, who writes and who runs tests,
frozen-path enforcement, backend and functional E2E rules, the evidence format and the per-shape gate set. Visual,
layout and UX verification: `frontend-verification.md`. Review lenses and dispositions: `review.md`. Reproduction,
hypotheses and flake investigation: `debugging.md`. Names follow `conventions.md`; if this file disagrees, conventions
wins. Rule prefixes: **T** traceability · **B** anti-bloat · **W** who writes/runs · **G** anti-cheating guardrails ·
**H** held-out checks · **K** backend · **E** functional E2E · **V** evidence.

Terms. **Oracle**: a test that would fail if the requirement it cites were broken. **Gate**: a check whose failure
blocks a phase transition or a DONE verdict. **Required criterion**: a P1 requirement or an acceptance check with
`required: true` in `acceptance.json`. **Outcome metric** (gate on it): cited requirement IDs whose frozen oracles pass
in the verifier's run, fail-to-pass for new behaviour, pass-to-pass for the existing suite, mutation kills, parity
mismatch rate, journey success on seeded data. **Activity metric** (report, never gate): test count, line coverage,
commits, review rounds, "all green" in a transcript.

## When to load

| Moment | Use |
|---|---|
| Phase 2 Spec | T-1..T-6, B-1..B-8, gate table (Scale by class), `templates/TEST-PLAN.md` |
| Phase 5 Build, each wave | W-1..W-5, G-1..G-8, the K/E rules for the task's layer, frozen-path scripts |
| Per-task verification | W-3, G-4..G-8, `scripts/test-diff-grep.sh`, `templates/test-diff-audit.md` |
| Phase 6 Verify (milestone) | V-1, V-2, H-1, `templates/VERIFICATION.md` |
| A maker says a test is wrong | W-5, `templates/TEST-DISPUTE.md` |
| Bug, migration, flaky test, AI feature, providers, unavailable gate | Shape conditionals |

| Artefact | Template / script | Target |
|---|---|---|
| Test plan | `templates/TEST-PLAN.md` | `.mission/TEST-PLAN.md` (M+; S: criteria inline in the task card) |
| Verification report | `templates/VERIFICATION.md` | `.mission/verification/VERIFICATION-<M>.md` |
| Test dispute | `templates/TEST-DISPUTE.md` | appended to `.mission/reviews/test-disputes.md`; decision → D-entry |
| Test-diff audit checklist | `templates/test-diff-audit.md` | pasted into the verifier brief; results go in the verifier report |
| Frozen-path hook | `scripts/protect-frozen.sh` | `.mission/bin/`, wired by `templates/settings.hooks.json` |
| Frozen manifest | `scripts/frozen-manifest.sh` | writes/checks `.mission/frozen-manifest.sha256` |
| Diff grep pre-pass | `scripts/test-diff-grep.sh` | run by the verifier before reading any diff |
| Flake run count | `scripts/flake-runs.sh` (lane H) | n from p and α, then n runs with a tally |

## Core rules

MUST / SHOULD / MAY per conventions §9.

### Traceability (T)

- **T-1 MUST** (M+) write `.mission/TEST-PLAN.md` before implementation. Every required criterion gets its ID, the
  observable criterion, the lowest observing level, oracle kind (registry vocabulary: unit · property · contract ·
  integration · scenario · e2e · visual · a11y · live · human · review), planned `path::name`, extra cases with a
  justification, a red-before-green evidence slot and a status.
- **T-2 MUST** every gating test carries `@req:<ID>` in its name or an annotation next to it
  (`it("@req:API-012 rejects expired token")`; Swift `func testAPI012_rejectsExpiredToken()` with `// @req:API-012`).
  The verifier computes the coverage matrix from the code (`grep -rn "@req:" <test dirs>`), never from the plan or
  the registry's `oracles` list.
- **T-3 MUST** DONE requires every required criterion to have ≥1 passing oracle in the verifier's own run. A criterion
  whose only oracles are skipped, quarantined, flaky or passed-on-retry is `UNVERIFIED`, never PASS.
- **T-4 MUST** one broad E2E or scenario test is never the sole oracle for more than 3 unrelated required criteria.
  Add specific oracles at a lower level.
- **T-5 SHOULD** (L/XL) run a traceability lint at every gate: tests citing unknown IDs, required IDs with no oracle,
  duplicate IDs. Use `scripts/validate-registry.py --tests <dirs>` or the same three checks by `mission-checker`.
- **T-6 MAY** keep the matrix in an existing project registry (e.g. `REQUIREMENTS.yaml`); TEST-PLAN then points to it.
  Untraced tests may exist and run but count for nothing toward DONE.

### Anti-bloat (B)

- **B-1 MUST** budget per criterion = **1 specific oracle + ≤2 edge/negative cases**. When the input space is large
  (parsers, money arithmetic, sizes, operation sequences) add one property test instead of more examples. Over budget
  needs a one-line justification in TEST-PLAN: the distinct failure mode covered, or the surviving mutant killed.
- **B-2 MUST NOT** write tautological tests: asserting a mock returns what it was told; re-implementing the function
  under test inside the test; snapshotting a whole payload without a reviewed reason; asserting only `not.toThrow()`,
  "was called" or status 200 without checking the outcome (persisted state, returned structure, rendered result).
- **B-3 MUST NOT** mock your own code for integration behaviour: never the module under test, your database, router,
  runtime, queue or bindings. Mock only third-party network boundaries, behind a port, with a deterministic fake (K-3).
- **B-4 MUST** derive property and model-based test models from the spec (transition table transcribed as data),
  never from the implementation. A model that mirrors the code can only agree with it.
- **B-5 SHOULD** the verifier runs the bloat audit (`templates/test-diff-audit.md` §C): tests without IDs; tests that
  assert nothing observable; ≥2 tests with the same ID and arrange differing only in literals (→ parameterise); a
  slower test duplicating a lower-level oracle.
- **B-6 SHOULD** test at the lowest level that observes the requirement: unit for pure logic; integration for a
  component on its real local runtime; API E2E for backend journeys; UI E2E only for journeys crossing ≥2 components
  a user touches.
- **B-7 SHOULD** delete redundant tests, recording `deleted: <test> — superseded by <test> (same oracle for <ID>)` in
  the task return. The verifier confirms the superseding test exists and still fails under oracle-bite.
- **B-8 MUST NOT** add tests to raise coverage. Coverage is reported, never gated. The only coverage-like gate: changed
  critical lines have ≥1 killing test (G-6 / G-7).

### Who writes and who runs tests (W)

- **W-1 MUST** (M+) acceptance and regression tests are written by a **test author** from the criteria, before
  implementation, in a context that never saw the implementer's plan internals. They are committed alone, then frozen
  (G-1). The test author owns `tests/acceptance/**` and `tests/regression/**` only until the freeze.
- **W-2 MAY** the implementer adds unit tests for its own internals. They count toward DONE only if they cite an ID and
  pass the bloat audit; at L/XL they are never the sole oracle for a required criterion.
- **W-3 MUST** the verifier re-executes every gate command itself in a clean worktree of the candidate commit and
  records command, exit code, passed/failed/skipped/flaky counts, duration and log path. A maker's transcript,
  summary or "tests pass" is never evidence. `/goal` is never the grader.
- **W-4 MUST** the test author proves each new acceptance/regression test **RED** on the pre-change tree (bugs: the
  unfixed commit) and records the command and failing assertion message. RED must show the expected symptom, not a
  setup, import or compile error. A test that passes before the change is mis-specified or the criterion already
  holds: escalate to the orchestrator, never ship it as an oracle.
- **W-5 MUST** an implementer who believes a frozen test is wrong stops and returns `STATUS: TEST-DISPUTE` with a
  filled `templates/TEST-DISPUTE.md`. The orchestrator routes it to the test author plus a reviewer who wrote neither
  the test nor the code. Only they amend the test, together with the spec/registry change and a D-entry; the manifest
  is then regenerated (`frozen-manifest.sh write --force`).

### Anti-cheating guardrails (G) — layered, each layer independent

- **G-1 MUST** declare frozen paths in `.mission/frozen-paths.txt` and mirror them in TEST-PLAN. Syntax: one glob per
  line, `#` comments, `**` any depth, `*` within one segment, a trailing `/` or `/**` means the whole directory, a
  pattern without `/` matches that basename at any depth. Minimum at M+: `tests/acceptance/**`, `tests/regression/**`,
  `tests/golden/**`, shared test setup and fixtures the oracles import, test configs (`playwright.config.*`,
  `vitest.config.*`, `jest.config.*`, `stryker.config.*`, `*.xctestplan`), CI workflow files, `.claude/hooks/**`,
  `.claude/settings.json`, and the visual-tolerance configs listed by `frontend-verification.md`. Configs are frozen
  because `retries: 10`, `passWithNoTests`, a narrowed `include` or a raised `maxDiffPixels` weaken tests without
  touching one. The hook always protects `.mission/frozen-paths.txt`, `.mission/frozen-manifest.sha256` and its own
  scripts in `.mission/bin/`, whether listed or not.
- **G-2 MUST** enforce with three layers. (a) `permissions.deny` rules `Edit(./<glob>)` / `Write(./<glob>)`
  (fragment in `templates/TEST-PLAN.md`). Deny rules bind the whole session, including a test author, so apply them
  only where nobody in that session writes the path: in the settings file of separately launched implementer lanes
  (every frozen glob), and at setup for paths frozen for the whole mission (CI workflows, `.claude/hooks/**`,
  `.claude/settings.json`, goldens recorded before Build). In-session sub-agents rely on (b) and (c) for globs frozen
  mid-mission. (b) The PreToolUse hook `scripts/protect-frozen.sh` (matcher `Edit|Write|MultiEdit|NotebookEdit|Bash`):
  blocks tool writes to frozen paths and Bash commands that
  redirect or `tee` into them, `sed -i`/`perl -i` them, `rm`/`mv`/`cp`-onto/`truncate` them or a parent directory,
  or run `git checkout|restore|rm|mv` on them (also via `bash -c`). (c) The sha256 manifest, checked by the verifier
  and CI against the copy committed at the task's base commit (`frozen-manifest.sh check --manifest <base copy>`).
  Only (c) catches edits made outside Claude Code or by a script the hook cannot parse (`python3 -c`, `xargs`, codegen).
- **G-3 MUST** every implementer brief repeats the stop line verbatim: "If a test appears wrong, contradictory, or
  impossible, STOP and file a TEST-DISPUTE. Do NOT modify, skip, delete, or special-case tests, and do NOT carve out
  the code to match a test."
- **G-4 MUST** the verifier runs the test-diff audit (`templates/test-diff-audit.md`) on every candidate, grep
  pre-pass first (`scripts/test-diff-grep.sh --base <base>`; its exit code cannot be overridden by a model). Blocking
  unless a quarantine entry or D-entry is cited: deleted or renamed tests; new `.only`, `.skip`, `xit`, `test.fixme`,
  `XCTSkip`, `#[ignore]`, `@pytest.mark.skip`; weakened assertions (`toEqual` → `toBeDefined`, exact → `toContain`,
  widened tolerance, fewer expected items); changed goldens/snapshots/fixture expectations without a requirement
  change; new `NODE_ENV === 'test'` / `isTesting` branches in production code; production literals or lookup tables
  matching fixture values; `passWithNoTests` enabled; retries raised; gating test count decreased versus base; any
  frozen-manifest mismatch.
- **G-5 MUST** CI and the verifier run with `forbidOnly` (Playwright) or the grep pre-pass for Vitest/Jest/XCTest/
  pytest/cargo. A non-zero skipped count on a gating suite fails the gate unless each skip is in the quarantine register.
- **G-6 SHOULD** (L/XL, critical modules: auth, state transitions, money, idempotency, the code a bug lived in)
  **targeted mutation testing** on changed critical files only: StrykerJS `--incremental` / `--mutate <files>` with
  `vitest.related: false` when integration tests reach code through `fetch`; `cargo mutants --in-diff <diff>` for Rust.
  Survivors block DONE until a test kills them or `mission-reviewer` marks them equivalent with a written reason.
  Infrastructure errors and stale mutation sites never count as kills.
- **G-7 SHOULD** (S/M) **oracle-bite** instead of mutation: in a scratch worktree the verifier applies one deliberate
  semantic break (revert the fix's essential hunk, flip the guard, drop the proof from the fixture), shows the gating
  test fails with the expected message, then discards the worktree.
- **G-8 MUST** a diff that touches tests without touching source gets the full test-diff audit and, at L/XL, a
  full-suite run: diff-scoped mutation runs no mutants for test-only diffs, so it cannot notice test deletion.

Freeze lifecycle (who can write what, when):

| Step | Actor | Mechanism |
|---|---|---|
| Author + prove red | test author | paths not yet listed; commit tests alone |
| Freeze | orchestrator (Bash) | `.mission/bin/frozen-manifest.sh add '<glob>' …` appends globs and rewrites the manifest; commit both. Adding globs only tightens, so the hook allows it |
| Implement | maker | hook blocks writes (+ deny rules in separately launched lanes); reads and test runs allowed |
| Check | verifier / CI | `git show <base>:.mission/frozen-manifest.sha256 > .mission/tmp/base-manifest` then `.mission/bin/frozen-manifest.sh check --manifest .mission/tmp/base-manifest` (exit 1 = changed, missing or added frozen file) |
| Amend (accepted TEST-DISPUTE only) | test author in a separate session started with `MISSION_FROZEN_BYPASS=1` in the Claude Code process environment (human terminal or `claude -p`) | edit, `frozen-manifest.sh write --force`, commit with the D-entry ID in the message |

### Held-out checks (H)

- **H-1 SHOULD** (L/XL, and any mission where a maker was caught cheating once) the verifier keeps 1–3 held-out
  acceptance scenarios per epic that the maker never sees, written after the candidate exists from the same criteria
  and stored outside the maker's worktree (`.mission/verification/held-out/` on a branch the maker does not merge, or
  the verifier's scratch dir). Visible pass + held-out fail = special-casing signal → escalate the audit to
  `mission-critic` and enable held-out checks for the rest of the run. Hand the failure message back to the maker,
  never the held-out test.

### Backend (K)

- **K-1 MUST** normal test runs are offline and credential-free. Install a network guard in the test setup file that
  every test project loads: block `fetch`, http/https, net/tls and DNS except loopback. Credentials in the environment
  of an ordinary test run are a finding.
- **K-2 MUST** Cloudflare Workers integration tests run inside the Workers runtime via the Workers Vitest integration
  (`@cloudflare/vitest-plugin`, formerly `@cloudflare/vitest-pool-workers`; detect which one the repo has installed,
  do not force a migration) with local D1, KV, R2 and Durable Object bindings and migrations applied per test file.
  Domain logic behind ports MAY run under plain Node for speed; binding semantics, request limits and DO alarms are
  proven only in the runtime layer or by a canary. Other stacks: the real local runtime (Postgres in a container,
  SQLite file, local emulator), never an in-memory imitation of your own database.
- **K-3 MUST** third-party providers (LLM APIs, payments, email, push, OAuth IdPs, image models) are faked
  deterministically behind a port (fixed seeds, recorded responses). Each adapter has one oracle-bite test: remove the
  provider's proof from the fixture (missing id, bad signature) and show the adapter test fails.
- **K-4 SHOULD** keep contract/golden fixtures for every external wire format consumed or produced: recorded,
  normalised (timestamps, ids, ordering) by reviewed normalisers, versioned under `tests/golden/`. Changing a golden
  requires a linked requirement change (G-4).
- **K-5 MUST** (when failure handling is a requirement) failure-injection tests assert recovery AND bounded side
  effects: count provider calls, rows written, messages emitted, charges attempted. "Error was caught" is not an oracle.
- **K-6 SHOULD** security tests in their own suite: cross-tenant access denied, authz per role, input validation at
  every external boundary, CSRF/OAuth `state`, webhook signature verification, secrets redacted from logs.
- **K-7 SHOULD** performance budgets assert complexity counters (queries per request, provider calls, bytes, renders)
  plus a generous time bound, measured inside the frozen harness, so a fast machine cannot hide an algorithmic
  regression and a maker cannot patch the timer.
- **K-8 MUST** live-provider checks are **canaries**: a separate command (`<pkg-manager> run canary:<name>`), test
  resources only, a documented spend ceiling and cleanup read-back before first enablement, never on ordinary PRs.
  Their criteria stay `PENDING-LIVE` until a canary run's evidence exists; release needs a human checkpoint if the
  canary spends money or touches production.

Layer suites as separate commands (`test:unit`, `test:property`, `test:integration`, `test:scenario`,
`test:security`, `test:perf`, `test:contracts`) so the verifier runs exactly the gate a criterion names and the
orchestrator scales gates by class. Scenario tests (a full seeded day or flow through the backend, offline) are the
backend analogue of a golden journey.

### Functional E2E (E)

- **E-1 MUST** E2E covers **golden journeys**, not criteria one by one: 3–7 journeys per product surface at L, ≤12 at
  XL, 1–3 through a new surface at M, none required at S. Each journey cites every criterion ID it observes (T-4 still
  applies).
- **E-2 MUST** seeded, isolated data per test (fixture tenant, per-test database, `launchArguments` seed on iOS) and
  assertions on the outcome (persisted state, the rendered aggregate equal to the seeded dataset's known totals, the
  saved item present after relaunch), not only on navigation or element existence.
- **E-3 MUST** web: Playwright config (frozen) with `forbidOnly: !!process.env.CI`, `retries: process.env.CI ? 2 : 0`,
  `trace: 'on-first-retry'`, a JSON reporter, and `webServer` booting the app against local backend fakes. Tests
  isolated; no ordering dependencies.
- **E-4 MUST** iOS: an XCUITest target driven by `xcodebuild test -scheme <UITests scheme> -destination
  'platform=iOS Simulator,id=<udid>' -resultBundlePath <path>.xcresult` under a hard timeout (GNU `timeout`, macOS
  `gtimeout`, or the harness timeout), a fresh simulator per run (`xcrun simctl erase <udid>` then boot), and the app
  launched with seed and backend launch arguments (`app.launchArguments += ["-uiTestSeed", "<fixture>", "-backendURL",
  "http://127.0.0.1:8787"]`) against a local `wrangler dev` or fake backend. Confirm flags with `xcodebuild -help` and
  `xcrun simctl help` at setup; do not hard-code more than this.
- **E-5 MUST** flake policy. A test that failed then passed on retry is **flaky**, not passed: it opens `O-NNN` in
  STATE.md (symptom, hypothesis, repro command, owner) and a row in the TEST-PLAN quarantine register with an expiry
  ≤ 2 phase gates ahead. A quarantined test is excluded from gates and its criteria are `UNVERIFIED`; an expired
  quarantine is a failing gate. Retries never exceed 2 and are never raised to get green. A fix is proven with
  **n ≥ ln(α)/ln(1−p)** consecutive clean runs with state reset between runs, where p is the failure rate measured on
  the unfixed code (≥5 observed failures, or deterministic), α = 0.05 by default and 0.01 for money, auth, data
  integrity or concurrency; double n when state cannot be fully reset. Example p = 0.02: n = 149 (α 0.05), 228
  (α 0.01). Compute and run with `scripts/flake-runs.sh` (`debugging.md`).
- **E-6 SHOULD** backend-only criteria get API E2E instead of UI E2E: real HTTP against local `wrangler dev`/Miniflare
  or a staging deployment, seeded tenant, assertions on the persisted outcome and body, not only the status code.

### Evidence (V)

- **V-1 MUST** the milestone verifier returns its report in the `templates/VERIFICATION.md` format and the orchestrator
  saves it verbatim to `.mission/verification/VERIFICATION-<M>.md`: environment fingerprint, per-gate command + exit +
  counts + log path, red-before-green table, test-quality proof (oracle-bite / mutation / held-out), test-diff audit
  result, frozen-manifest check, criteria matrix built from `@req:` citations, and a mechanical verdict
  `PASS | FAIL | UNVERIFIED`. Per-task verifiers return the YAML of `templates/gate-verifier.md` plus the audit block.
  Graders and reviewers consume these files and raw logs, never the maker's summary. Every PASS cites a gate row or
  log line; an uncited PASS is treated as UNVERIFIED.
- **V-2 MUST** DONE for the goal = every required criterion PASS in the verifier's run on the final integrated commit,
  no blocking audit finding, clean frozen-manifest check and no expired quarantine. Anything else is reported as a
  visible partial result listing FAIL, UNVERIFIED and `PENDING-LIVE` IDs plainly.

## Procedure

1. **Plan (Phase 2).** S: the task card's "Test first" line names one failing-first test or repro command; gates =
   that test + the existing suite + the grep pre-pass; stop here. M+: the test strategist fills `.mission/TEST-PLAN.md`:
   criteria matrix (T-1), the gate set from the table in *Scale by class* with exact commands, frozen globs (G-1),
   fakes and goldens (K-3/K-4), journeys (E-1), budget exceptions (B-1), eval sets for AI behaviour.
2. **Review the plan** inside the spec gate (`mission-critic`, `templates/spec-review-rubric.md`): every required
   criterion has an oracle at the lowest observing level; none relies only on a broad E2E beyond T-4; budgets and
   gate commands stated; unavailable gates already marked with their fallback. ≥2 blocking findings on a plan written
   inline or by a Sonnet agent → re-plan with `mission-builder`.
3. **Install guardrails once (M+).** Merge the PreToolUse hook (`templates/settings.hooks.json`) and deny rules
   (G-2a). Run `.mission/bin/protect-frozen.sh --self-test` (must print `self-test: PASS`). After the first freeze,
   run the live check: have a `mission-worker` try `Edit` on `<frozen dir>/.probe` and Bash
   `echo x >> <frozen dir>/.probe`; both must be refused. Record the result as an F-entry in STATE.md. Not refused →
   D-entry "layer (b) unavailable", raise the test-diff auditor to `mission-critic` for the whole mission.
4. **Author tests (Build wave, step 1).** Brief the test author with criterion IDs, cited spec excerpts, the harness
   pointers from `CONTEXT.md` and the budget; never the implementer's plan. Return: `(ID, path::name, red command,
   failing message)` per test, budget exceptions, fakes created. `mission-verifier` confirms RED on the base commit.
   Then freeze: `.mission/bin/frozen-manifest.sh add '<glob>' …`, commit tests + list + manifest together.
5. **Brief makers** with the owned paths, AC IDs, the frozen-path list, the G-3 stop line and "report the command and
   exit code; the verifier re-runs everything".
6. **Verify each task** (`mission-verifier`; L/XL test-diff audit `mission-critic`) in a clean worktree at the
   candidate: (a) manifest check against the base copy; (b) `test-diff-grep.sh --base <base>`; (c) run the gate commands
   for the task's AC IDs with JSON reporters; (d) red-before-green: the task's new oracles fail on base; (e)
   oracle-bite (S/M, or any fix) or targeted mutation (L/XL critical files); (f) `templates/test-diff-audit.md`
   questions with file:line answers; (g) coverage from `@req:` grep; (h) `git status --porcelain` empty at the end.
   Any required criterion not PASS keeps the task out of PASSED.
7. **Handle disputes.** On `STATUS: TEST-DISPUTE` set the task `BLOCKED(test-dispute)`, append the record to
   `.mission/reviews/test-disputes.md`, route to the test author + a non-author reviewer. Accepted → amend in a bypass
   session (freeze lifecycle table), D-entry, re-freeze, re-prove red. Rejected → return the evidence to the maker;
   the task resumes at the same rung.
8. **Handle flakes** per E-5: O-NNN, quarantine row with expiry, `debugging.md` for the investigation, n-run proof.
9. **Verify the milestone (Phase 6).** `mission-critic` on a clean checkout of the integrated branch runs the full gate
   set for the class and shape, held-out scenarios (H-1), and returns the VERIFICATION report. The orchestrator has
   `mission-checker` re-run one randomly chosen gate and compares its counts with the report and the JSON reporter
   artefacts; a mismatch voids the report. Transcribe verdicts into `acceptance.json` citing the report path.
10. **Release (Phase 8).** Run canaries (K-8) with a human checkpoint for spend or production touch; criteria stay
    `PENDING-LIVE` until cleanup read-back is evidenced.
11. **Retro (Phase 9).** Every escaped defect gets a regression oracle through the bug regression protocol and a
    lesson candidate; every cheating signal (audit hit, held-out fail) becomes a lesson and a control.

## Scale by class (S/M/L/XL)

| Toggle | S | M | L | XL |
|---|---|---|---|---|
| Test plan | task card line | TEST-PLAN short form | TEST-PLAN full | TEST-PLAN per milestone |
| Test author ≠ implementer | no (verifier checks red on the pre-change tree) | yes | yes | yes |
| Frozen layers | grep pre-pass + audit only | hook + deny + manifest | + manifest check in CI | + CI |
| Test-diff auditor | `mission-verifier` | `mission-verifier` | `mission-critic` | `mission-critic` |
| Quality proof | oracle-bite on the fix (optional) | oracle-bite | targeted mutation on critical files | targeted mutation + full run at milestones |
| Held-out scenarios | — | only after cheating | recommended | required |
| E2E journeys per surface | — | 1–3 through the new surface | 3–7 | ≤12 |
| Traceability lint (T-5) | — | registry validator | every gate | every gate + CI |
| Full-suite run | at Verify | at Verify | every integration + Verify | every integration + Verify |

If unsure between two classes, take the larger for these verification toggles (conventions §5).

Minimum hard gate set per shape × class. ● required · ○ recommended · — not required. "Suite" = the existing
suite, pass-to-pass. REF uses the MIG column; UPG, PRF, INF: Shape conditionals.

| Gate | S (any shape) | GRN M/L/XL | BUG M/L | FEA M/L | MIG L/XL | WEB M/L |
|---|---|---|---|---|---|---|
| Build + typecheck + lint | ● | ● | ● | ● | ● | ● site build |
| Existing suite pass-to-pass | ● | ● once it exists | ● | ● | ● old AND new | ● |
| Red-before-green | ● 1 test | ● per criterion | ● regression protocol | ● per criterion | ● per parity case | — |
| TEST-PLAN with criteria IDs | — | ● | ● short | ● | ● | ● claims + pages |
| Frozen paths + hook + manifest | — | ● | ● | ● | ● | ○ |
| Test-diff audit + grep pre-pass | ● | ● | ● | ● | ● | ○ |
| Property / model-based tests | — | ● core state machines | ○ | ○ | ○ | — |
| Integration on real local runtime | — | ● | ● at the bug's layer | ● | ● | — |
| Contract / golden fixtures | — | ● external APIs | ○ | ● if API changes | ● corpus from OLD system | — |
| Security tests | — | ● L/XL | ● if security bug | ● new endpoint | ● | ○ forms, headers |
| Failure injection, bounded side effects | — | ● L/XL | ● failure-path bug | ○ | ● | — |
| Complexity budget | — | ○ L · ● XL | ● perf bug | ○ | ● parity of complexity | ● Lighthouse perf |
| Functional E2E golden journeys | — | ● 3–7 per surface | ○ journey reproducing the bug | ● 1–3 new surface | ● existing journeys unchanged | ● nav, forms, search |
| Mutation or oracle-bite | ○ oracle-bite | ● mutation critical L/XL | ● oracle-bite on fix | ● bite · ○ mutation | ● mutation on moved logic | — |
| Held-out verifier scenarios | — | ○ L · ● XL | ○ | ○ | ● | — |
| Parity / shadow comparison | — | — | — | — | ● parity protocol | — |
| Link check + Lighthouse CI | — | ○ marketing pages | — | — | — | ● |
| Claim traceability (claim → S-NNN) | — | — | — | — | — | ● |
| AI/LLM eval suite | — | ● if AI features | ● if bug in AI output | ● if AI feature | ● if routing/gateway moves | ○ |
| Spend-bounded canary | — | ● before launch | ○ | ○ | ● before and after cutover | ○ uptime/link |

## Shape conditionals

- IF class = S THEN one failing-first test or repro command, the existing suite, the grep pre-pass and a short audit.
  No TEST-PLAN, no mutation, no held-out. The implementer may write the test; the verifier proves red by running it on
  the pre-change tree. Guardrail cost stays below task cost.
- IF shape = BUG THEN run **Protocol A** below. The repro oracle is frozen before any fix; the fix commit never touches it.
- IF shape = FEA THEN characterize the touched behaviour first (existing journeys pass-to-pass), add criterion oracles
  at the lowest observing level, and 1–3 journeys through the new surface asserting seeded outcomes (a dashboard's
  aggregate equals the seeded dataset's known totals; empty and error states render their specified content).
- IF shape = MIG or REF THEN run **Protocol B**. No behaviour change in the same PR as the move; improvements are later,
  separate criteria.
- IF shape = GRN with ≥2 platforms (e.g. Swift iOS + Cloudflare backend) THEN M0 freezes the API contract; one set of
  contract fixtures under `tests/golden/contract/` is consumed by the backend's response tests AND the iOS client's
  decoding tests (one fixture, two consumers); backend criteria on the Workers Vitest integration with local D1/R2;
  XCUITest journeys on a fresh simulator against local `wrangler dev` seeded via launch arguments; a spend-bounded
  canary before launch.
- IF shape = WEB THEN gates = site build, link check (internal + external, allowlist for flaky domains), Lighthouse CI
  assertions on key pages (`lhci autorun`, ≥3 runs), Playwright journeys for nav, index, docs search and forms, and a
  claims check: every factual or market claim on the site maps to an `S-NNN` source in `RESEARCH.md`; an unsourced
  claim is `[NEEDS-EVIDENCE]` and blocks launch. Visual quality: `frontend-verification.md`.
- IF the mission includes AI/LLM behaviour THEN an eval set per behaviour (≥20 tasks) graded on outcome state or
  structured output by code first, rubric second; N ≥ 3 trials per task; pass-rate threshold recorded
  in TEST-PLAN before the first run; rubric grader on `mission-verifier` calibrated against ≥20 human- or
  `mission-reviewer`-labelled cases (agreement ≥90% on binary checks, else recalibrate); deterministic provider fakes
  for every non-eval test. Never assert exact model prose.
- IF touches auth, tenancy, payments or state machines THEN security tests (K-6), one model-based property test from
  the spec's transition table (B-4), failure injection counting charges/side effects (K-5), targeted mutation at L+.
- IF external providers THEN deterministic fake behind a port, oracle-bite per adapter (K-3), and a canary with a spend
  ceiling and cleanup read-back before the provider criterion leaves `PENDING-LIVE` (K-8).
- IF a maker was caught cheating (audit finding, held-out fail) THEN enable H-1 for the rest of the run, route all
  further test-diff audits to `mission-critic`, restart that task one rung up the ladder, record a lesson candidate.
- IF a gate is unavailable in this harness (no simulator, no browser, no macOS runner, no network for a canary) THEN
  mark the dependent criteria `UNVERIFIED(<reason>)` with what would settle them. Never substitute a mock-level test and
  call it PASS; the gate stays PENDING.
- IF shape = PRF THEN record a baseline with a repeatable harness before changes; assert complexity counters (K-7) and
  identical outputs on a corpus; the metric target is the oracle.
- IF shape = UPG THEN full suite pass-to-pass on old and new versions, contract goldens, E2E smoke; no new tests unless
  behaviour changed.
- IF shape = INF THEN a dry-run pipeline plus a deliberately failing commit proving the pipeline still fails
  (oracle-bite on CI itself); workflow files stay frozen for makers outside the INF lane.

**Protocol A — bug regression (red-before-green).** Paste into the task brief or `.mission/investigations/O-NNN.md`.

```markdown
### Regression protocol · <O-NNN | bug id> · <one-line symptom>
1. REPRODUCE (debugging.md): symptom as an observable assertion ("GET /outfits returns tenant B rows for tenant A"),
   environment fingerprint, exact command. Gate REPRODUCED: command → exit ≠ 0 → "<symptom line>".
2. MINIMISE to the lowest level that still shows the symptom (unit < integration < API E2E < UI E2E).
   Nondeterministic: stress/property test with a fixed seed (races: scheduled/interleaving runner); measure
   p = failures / runs on the unfixed code (≥5 failures observed).
3. FREEZE THE ORACLE (test author, not the fixer): tests/regression/<id>_<slug>.<ext>, test name carries
   @req:<ID> and the symptom. Commit it alone; `.mission/bin/frozen-manifest.sh add 'tests/regression/<id>_*'`.
4. PROVE RED (verifier, clean worktree at the parent commit): the test fails WITH THE SYMPTOM, not a setup error.
   Message mismatch → invalid oracle → back to step 2.
5. FIX (implementer): G-3 stop line in the brief; no edits under tests/regression/**; root cause, not suppression
   (no catch-ignore, retry or timeout bump unless the cause is an external transient, evidenced).
6. PROVE GREEN + BITE (verifier): regression test passes; existing suite pass-to-pass; nondeterministic:
   n ≥ ln(α)/ln(1−p) consecutive clean runs with state reset (α 0.05; 0.01 money/auth/data/concurrency; 2n if state
   cannot reset) via `scripts/flake-runs.sh`; oracle-bite: revert the fix's essential hunk in a scratch worktree →
   the regression test fails again.
7. GENERALISE: sibling sweep for the same defect pattern (every hit dispositioned: own regression test or O-NNN);
   lesson candidate in LESSONS-INBOX.md; production incident → minimal recurrence fixture before closure.
DONE = step 4 and step 6 evidence in the verifier report.
```

**Protocol B — migration / extraction parity.** Paste into `.mission/design/MIGRATION.md` (parity section) or PLAN.md.

```markdown
### Parity protocol · <old system> → <new home>
0. SCOPE: the move changes location/ownership, not behaviour. Behaviour changes are later, separate criteria.
1. INVENTORY (test author, mission-builder): every endpoint/function, input class, error class, side effect (DB rows,
   events, provider calls, contractual log fields), non-functional contract (latency, rate limits, cost/request).
   → tests/golden/INVENTORY.md, one requirement ID per item (PAR domain, e.g. PAR-001), priority P1/P2.
2. CHARACTERISE OLD before any code moves: golden corpus of representative + edge + error requests (redacted
   production samples if allowed, else synthesised from the inventory). Reviewed normalisers for ids, timestamps,
   ordering, latency. Store tests/golden/<PAR-id>/*.json; freeze + manifest. Oddities are listed, not fixed.
3. JUDGE CHECK: replay the corpus against OLD → 100% match (else fix normaliser/corpus); replay against a
   deliberately broken OLD build → mismatches detected (the judge can fail).
4. BUILD NEW behind the same port; replay with deterministic provider fakes. Gate: 100% match on P1 PAR IDs;
   P2 mismatches each need a disposition + D-entry.
5. SIDE-EFFECT PARITY: compare rows/events/provider-call counts per request, not only responses (K-5).
6. SHADOW (staging/production, human checkpoint): old = control (returned), new = candidate (discarded), random
   order, explicit compare/ignore rules, mismatches published; side-effecting candidates in dry-run or isolated
   resources. Gate: 0 mismatches on P1, ≤ <budget, e.g. 0.1%> on P2 over ≥ <n requests | days>, every class triaged.
7. CUTOVER with a rollback switch; spend-bounded canary on the new path; old path runnable until the canary and
   <n> days of inverse shadow (new = control) are clean. Evidence level staging/production, else PENDING-LIVE.
8. DECOMMISSION: the golden corpus stays as the new home's contract suite; parity count never decreases.
```

## Model routing

Deterministic graders (exit codes, reporter JSON, grep pre-pass, manifest hash) do most grading for free. Tokens go
to authoring oracles and auditing test diffs. Running tests needs an honest separate context, not a top-tier model.

| Role | Agent (model · effort) | Tier-up when | Guard on the cheaper choice |
|---|---|---|---|
| Test strategist (TEST-PLAN) | S/M orchestrator inline; L/XL `mission-builder` (O · high) | ≥2 blocking plan findings → `mission-builder` | `mission-critic` spec review: every required criterion has an oracle, budgets and gate commands stated |
| Test author | `mission-worker-high` (S · high); concurrency, state machines, security, money, parity harness, model-based property tests → `mission-builder` | test cannot go red for the expected reason, or an oracle-bite survives → rewrite by `mission-builder` | W-4 red proof confirmed by `mission-verifier`; G-6/G-7 |
| Implementer's own unit tests | the implementer (`mission-worker`) | — | B-5 bloat audit; tests without `@req:` count for nothing |
| Gate runner (run, collect counts, excerpt failures) | `mission-checker` (S · low) | judgement needed → `mission-verifier` | counts must match reporter JSON / `.xcresult`; orchestrator's random re-run (Procedure 9) |
| Per-task verifier + test-diff audit S/M | `mission-verifier` (S · high) | L/XL, or diff touches frozen paths, goldens or configs → `mission-critic` | grep pre-pass exit is final; any held-out failure escalates later audits |
| Mutation survivor triage | `mission-reviewer` (O · medium) | disputed equivalence → `mission-critic` | written reason per "equivalent"; ≥1 sampled by the review lens per milestone |
| Flake investigator | `mission-worker-high` | 2 falsified hypotheses → `mission-builder` | repro with ≥5 failures on unfixed code; n-run proof (E-5) |
| AI eval grader | binary checks `mission-checker`; rubric scoring `mission-verifier` | calibration disagreement → `mission-reviewer` | ≥20 labelled calibration cases, ≥90% agreement |
| Milestone verifier / completion grader | `mission-critic` (O · high); S with only deterministic criteria: `mission-verifier` | XL release → + `mission-strategist-review` lens | every PASS cites a gate row; uncited PASS → UNVERIFIED |
| Orchestrator sign-off | session model (F · medium on M+, O · high on S) | — | reads the report only; never re-grades or runs gates itself |

Never: Fable 5.1 as a test runner; Haiku anywhere (conventions §6); a grader of the same agent file as the maker for
a blocker-capable gate without a deterministic oracle; `/goal` as the completion grader.

## Anti-patterns

Cheating and weakening (counter in brackets):

- Deleting, skipping or renaming the failing test; `.only` left in [G-1..G-5, pre-pass].
- Special-casing: fixture literals, `if (input === <fixture>)`, lookup tables keyed on test data [audit Q3, H-1].
- Operator overloading, monkey-patching the assertion library or editing setup files [freeze setup + configs].
- Weakening configs: retries up, `passWithNoTests`, narrowed `include`, raised tolerances, ignored exit codes [G-1].
- Tampering with measurement: patching timers, self-reported timings [K-7 counters inside the frozen harness].
- Regenerating goldens from the new code; a property model copied from the implementation [B-4, G-4].
- Test-only production branches (`NODE_ENV === 'test'`, `isTesting`) [pre-pass].
- Maker self-reporting success; a Stop hook or `/goal` as the only gate (Claude Code ends the turn after 8
  consecutive Stop-hook blocks) [W-3].
- Hook bypass via a script written elsewhere, `python3 -c`, or settings edits [manifest check, frozen `.claude/**`].

Bloat:

- Coverage chasing; tests that execute lines and assert nothing [B-8, B-2].
- Mock-everything integration tests that pass while the runtime fails (bindings, constraints, limits) [B-3, K-2].
- One E2E per criterion; snapshot-the-world payloads re-recorded on every change [E-1, K-4].
- Forty example tests where one property test would do; duplicates differing only in literals [B-1, B-5].
- One vague "the whole flow works" test as the oracle for everything [T-4].
- Keeping superseded tests "just in case" [B-7].

Process and cost:

- XL ceremony on S tasks (TEST-PLAN, mutation, held-out for a one-line fix) — it teaches skipping gates.
- A model reading full logs: use JSON reporters, keep failure excerpts only, put the gate runner on `mission-checker`.
- Blanket mutation runs every iteration; asking a model to imagine surviving mutants instead of running the tool.
- Unbounded retries hiding production races; canaries on every PR.
- Green offline suites over mocks with nothing real wired or deployed (SKILL.md non-negotiable 6).
- `UNVERIFIED` relabelled PASS under deadline pressure. A partial result reported honestly beats a false DONE.

## Unverified harness details

| Detail | Status | Safe fallback |
|---|---|---|
| PreToolUse `exit 2` blocks the tool call and feeds stderr back to Claude | From prior knowledge and community hooks; the research fetch of the hooks page was truncated. MUST be confirmed against the current hooks docs before relying on it | Procedure step 3 live probe. Not blocked → D-entry, manifest check + audit carry enforcement, auditor `mission-critic` |
| Hook input fields `tool_name`, `tool_input.file_path`, `tool_input.notebook_path`, `tool_input.command`, `cwd` | Unverified field names | `protect-frozen.sh` fails closed (exit 2) on unparseable input; live probe confirms extraction |
| Hooks fire for tool calls made inside sub-agents | Inference | Run the live probe from a `mission-worker` sub-agent, not the main session |
| `MISSION_FROZEN_BYPASS=1` reaches hooks through the Claude Code process environment | Inference | If amendment sessions are still blocked, the human applies the amendment in a terminal and runs `frozen-manifest.sh write --force` |
| `Edit(<glob>)` deny-rule anchoring and `**` semantics | Not re-read | Keep hook + manifest; probe one denied Edit at setup |
| Per-lane settings for separately launched implementer sessions (`claude -p --settings <file>`) | Inference; flag not verified in this lane | Check `claude --help`; without it, lanes rely on (b) + (c) |
| Bash command inspection | Heuristic by design (misses `python3 -c`, `xargs`, generated scripts) | Manifest check (c) and the audit are authoritative |
| python3 on PATH for the scripts | Environment-dependent | Hook blocks Edit/Write/Bash with a message when python3 is missing and frozen paths are configured; install python3 or unwire the hook with a D-entry |
| `@cloudflare/vitest-plugin` replacing `@cloudflare/vitest-pool-workers` | Cloudflare docs dated Aug 2026 | Detect the installed package; config is unchanged between them |
| `xcodebuild` / `simctl` flag set | Not re-verified | `xcodebuild -help`, `xcrun simctl help` at setup; hard timeout on every run |
| StrykerJS `thresholds.break` | Inferred from the shared Stryker config model | Gate on the survivor list, not the score |
| ImpossibleBench magnitudes (stop line 93% → 1% on one variant; read-only access as middle ground) | Secondary sources | Keep the stop line and read-only tests; do not quote numbers to the user |
| Thresholds: budget 1 + 2, T-4 limit 3, journeys 3–7 / ≤12, retries ≤2, ≥20 eval tasks, 90% agreement | Judgement defaults | Change per mission with a D-entry |

## Evidence

1. `research/mission-skill/04-testing-strategy.md` §4–§7 (source report for every rule here)
2. `arcwell/REQUIREMENTS.yaml:3468-3586` (TEST-001..TEST-008: traceability, oracle strength, incident fixtures,
   mutation, oracle-bite, failure injection, complexity budgets)
3. https://code.claude.com/docs/en/permissions (deny → ask → allow; rules enforced by Claude Code, not the model)
4. https://code.claude.com/docs/en/hooks (PreToolUse can block a tool call)
5. https://code.claude.com/docs/en/goal (evaluator reads the transcript only; defaults to Haiku)
6. https://arxiv.org/abs/2510.20270 (ImpossibleBench: agents delete or modify failing tests)
7. https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents (outcome grading, trials, calibration)
8. https://mutants.rs/in-diff.html (diff-scoped mutation; test-only diffs run no mutants)
9. https://fast-check.dev/docs/advanced/model-based-testing/ (model must not copy the system)
10. https://developers.cloudflare.com/workers/testing/vitest-integration/migration-guides/migrate-to-vitest-plugin/
11. https://playwright.dev/docs/test-configuration (`forbidOnly`, retries, trace, `webServer`)
12. https://raw.githubusercontent.com/github/scientist/main/README.md (control/candidate shadow comparison)
