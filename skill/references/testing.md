# Testing

Read this file at the `test-plan` phase, whenever a test double enters the project, before writing
the reproduction for a fix or the characterization corpus for a move, when a test flakes, and
before anyone changes a test, a threshold, or a constraint. It decides what a test is for, the layer
each claim is refuted at, how many tests a run may add, how test doubles are kept honest, the
quality floor in `.drive/CONSTRAINTS.md`, which tests are frozen before implementation and how a
frozen test is disputed, how flakes are measured and a flake fix is proven, how bugs, schedules, and
migrations are tested, and what the verifier does to the suite. Platform commands live in the domain
files; this file holds the rules those commands serve. `drive.py` means the state tool as SKILL.md
defines it.

## Contents

1. Tests exist to refute claims
2. Choosing the layer
3. What not to test
4. Budgets
5. Real runtimes and test doubles
6. The kindness ledger
7. The limits probe and named limits
8. The constraints floor
9. Changing a test, and frozen refutation tests
10. Flakes and statistical proof
11. Bugs: reproduce first
12. Schedules, migrations, and screens
13. Coverage and mutation
14. What the verifier does to the suite
15. Platform pointers
16. Excuses and rebuttals
17. Red flags

## 1. Tests exist to refute claims

A test is evidence only if it would fail when its claim is false. Every claim is a sentence about
something a user, a caller, or another system can observe: "Deleting the account removes every
photo" is a claim, and "the delete handler calls the storage client" is an implementation detail.
If a requirement cannot be phrased as an observation a test could make, send it back to the spec
phase before planning a test for it. Build each test around the observation in the claim's "What
would prove this wrong" line, not around the code that implements it.

`drive:architect` writes `.drive/TESTPLAN.md` from `templates/TESTPLAN.md` after the spec and before
decomposition: one row per claim key with its layer, its refutation test as
`planned:<path>::<name>`, who writes it, and status Missing. At M and above the claim's refutation
test is written by `drive:severe-tester` before the implementing package starts and is then frozen
(section 9); at S the implementer writes it. You copy status and evidence into TESTPLAN.md from
validated verdicts when you update STATUS.md; when the two disagree, STATUS.md and the code win.

## 2. Choosing the layer

Give every claim one refutation test at the cheapest layer whose real runtime can refute it.
Cheapest means the fastest run with the least setup; able to refute means the runtime enforces every
constraint the claim depends on. Choosing a lower layer than the claim needs is the commonest way a
suite goes green while the product is broken.

| The claim depends on | Layer | A refuting observation looks like |
|---|---|---|
| pure logic: computation, parsing, formatting, ordering | unit test in the project's own runner | a wrong total at a boundary input |
| storage, a platform binding, a query, a queue, an alarm, a workflow step | the platform's real local runtime | the 101st bound parameter rejected; a replayed step losing a value |
| a contract between two components the run owns | contract test over shared schema or fixture files, run on both sides | a fixture the server accepts that the client cannot decode |
| wiring across processes, or a screen showing what a server returned | one end-to-end flow | the screen shows a value the API never sent |
| behaviour only the deployed system has: limits with no local runtime, egress, production config | a live check against the deployed environment | live rejects what local accepted |
| how a screen looks | `drive:ui-reviewer` captures against the design contract | see `references/ui-verification.md` |

A second test on the same claim needs one of three reasons, written in a comment on the test and in
the TESTPLAN.md row: an independent oracle for code that carries money, auth, or data loss; a boundary
the first test cannot reach (N and N+1 of a documented limit); or a bug that actually happened, kept
as a regression test named for its symptom. `drive:severe-tester` adds refutation tests per trust
boundary on top of these, recorded as `severe:` tokens. Any other extra test is deleted at review,
and the deletion is recorded in STATE.md.

## 3. What not to test

Do not write tests for constructors, getters and setters, facts the type checker already enforces,
framework behaviour (that the router routes, that a view renders a string it was given), third-party
libraries, private helpers reached through reflection, or log wording. Do not snapshot whole pages or
JSON blobs without a named reason. The one accepted golden is an output whose entire content is the
claim: a rendered email, a CLI's `--help`, a generated SQL statement. Store it inline where the diff
stays readable.

Mark a test for deletion or rewrite when any answer is yes: would it pass against a stub that returns
constants; does it only assert that a mock was called; does it repeat another test's oracle on the
same claim; does its name paraphrase the code rather than a claim; does it still pass with the
production line it targets deleted.

## 4. Budgets

The budget is counted in claims, never in lines or coverage.

| Shape | Tests the run may add |
|---|---|
| `fix` | the failing reproduction, kept as the regression test (written by `drive:severe-tester` and frozen at M and above, by the implementer at S), plus at most one maker-written boundary test if the fix changed a limit; a third maker-written test means the hunt became a feature, so re-classify. Counted separately: `drive:severe-tester`'s adjacent-input tests, at least one at every size above XS, and the class fix's test that generates the violating shape |
| `feature` | one refutation test per claim (frozen at M and above); one severe test per trust boundary crossed (auth, tenant, external input, money); one end-to-end run per user-visible flow; an N and N+1 pair per platform limit the feature can hit; implementer unit tests for its own internals, which never stand alone as a claim's evidence at M and above |
| `build`, per module | the same as `feature`, plus the limits probe once per platform |
| `move/migration` | the characterization corpus, the replay diff, the cutover smoke, the rollback drill; feature tests only for behaviour meant to change, each named in MIGRATION.md |
| `move/refactor`, `move/upgrade` | none; the existing suite passes unchanged, with characterization tests first where the touched area has none |
| `publish` | route smoke (status and console errors), link check, accessibility and performance runs per template, traceability of every factual sentence to RESEARCH.md; no unit tests for content |
| `report` | no code tests; citation and completeness grading in `references/verification.md` |
| `operate` | none unless the run writes a script, which is then tested like a feature; observation of the live effect is the proof |

Two smells mark bloat without reading the tests: a test file more than three times the size of the
code it covers, when that code is not a parser or a state machine, is asserting on implementation;
a module with more tests than claims and no bug references has extras to delete.

## 5. Real runtimes and test doubles

A harness kinder than production certifies broken code, and the number of green runs against it is
not evidence. A SQL shim with no bind-parameter limit once passed two dozen runs for a query that
production rejected at the 101st parameter, and the platform's own local runtime would have rejected
it too. So the first rule is to stop writing shims where a real runtime exists: platform code runs in
the platform's local runtime, native code in the simulator, browser code in a real browser, and SQL
against the production engine. Hand-rolled binding fakes, in-memory stand-ins for a store that has a
local runtime, and one SQL dialect standing in for another are refused.

Where a double is unavoidable, use this order and stop at the first that works: the real
implementation; a fake (a small working implementation that enforces the same limits); a stub
(canned responses); and a call-checking mock only where the real dependency is slow,
nondeterministic, or has effects you cannot contain. Assert on outcomes (returned values, stored rows,
responses, visible state), never on which internal methods ran. A double for a hosted service with no
local runtime returns that provider's real failure shapes (429 with `Retry-After`, 5xx, malformed
bodies, timeouts), and a remote or live check covers what the double cannot.

## 6. The kindness ledger

Every double, and every local runtime, gets rows in TESTPLAN.md's kindness ledger before any test
runs against it. At S, where the run has no full test plan, create `.drive/TESTPLAN.md` holding only
the kindness ledger the first time a double or local runtime sits on a claim's path; the ledger has
one home at every size. A row names the production constraint, the harness behaviour as observed by
the limits probe (never as read in documentation), the mitigation, and its evidence token. The
mitigation is exactly one of: a guard in production code with its own `test:` or `severe:` test; a
live check that crosses the limit (`live:`); or an accepted risk with its reason and the `verdict:` of
the verifier that accepted it. An empty ledger for a platform with documented limits is a blocking
gap.

Ask these questions of every double and of the local runtime itself:

| Dimension | Where is it kinder than production |
|---|---|
| Counts and sizes | parameters per query, statement length, row and payload size, batch size, list length, headers, files, pages |
| Time | request and query timeouts, CPU time per invocation, sleeps the harness skips, clock skew, the runtime's timezone |
| Rate and quota | requests per second, subrequests or queries per invocation, daily quotas, concurrent connections |
| Auth and identity | skipped token validation, expired tokens accepted, scopes and tenant boundaries ignored, every caller treated as the owner |
| Consistency and ordering | eventual consistency, redelivery, out-of-order delivery, missing consumer concurrency, retries the harness never performs |
| Failure shapes | only success returned; no real error codes, partial writes, or cancellations |
| Data realism | one item against a thousand; ASCII against Unicode normalization variants; empty strings against nulls |
| Environment | cold starts, missing secrets, an older compatibility date, flags enabled locally and off in deployed config |

## 7. The limits probe and named limits

For each platform in play, write a limits probe in the project's test directory that exercises each
documented limit at N and N+1 against the local harness and prints which are enforced. Run it in the
first hour of the build phase, before any code that could hit a limit, and again whenever the
toolchain version changes. Record the results and the toolchain versions in the ledger rows and under
"Verified facts" in STATE.md with the date. Where local accepts what live rejects, the guard's severe
test is the only local protection, and a live check that crosses the limit is required before the
claim reaches Live Proof.

Encode every limit the code can hit as a named constant in production code (`MAX_BOUND_PARAMS = 100`)
next to a guard that chunks, validates, or rejects with a clear error, and test the guard at N and
N+1. Test the guard, not the platform. A comment beside a query is not a guard.

## 8. The constraints floor

For size M and above, write `.drive/CONSTRAINTS.md` from `templates/CONSTRAINTS.md` at archaeology for
existing code, or after wave 0 for a greenfield build, since nothing exists to measure before it; in
every case before the first integration commit. The floor holds without any row: no added
suppression comments or skips, no assertion removed or weakened in a test file that still exists, no
test-only branch in production code, no stubs, placeholder throws, or empty catches, no secrets, and
this file is never loosened to let a change pass.

Each enforced row carries the exact command, the measured value, the direction (must not fall, or
must not grow), a tolerance, the reason, and the commit and date of the measurement. With no owner
target, measure today and record that value. With an owner target the codebase already meets, record
the target. With one it fails today, record today's measurement as the enforced value, name the
target in the reason, and set the direction toward it. Never set a threshold the codebase fails
today: a permanently red check teaches every agent to ignore red. Ask of each row whether code that
does not work could pass it, and keep at least one row whose verdict comes from outside the project's
own tests: a vulnerability database, an accessibility engine, or the real runtime's limits probe.

Run the guard after the gates are green and before every integration commit. Without `--base` it
compares with GOAL.md's `baseline_sha` when that names a commit, and with HEAD only when it does not,
so work already committed in this run is still compared; `--base <sha>` chooses another base and
`--root <dir>` another checkout. `drive.py lint` also runs it against the baseline at the integrate
and harden gates and at `--final`.

```bash
drive.py guard
```

It reads the range from the base plus staged, unstaged, and untracked files, and blocks on the
shapes in the table below, a loosened value in CONSTRAINTS.md, and an exception with no recorded
decision. It never treats an edited date as a lowered threshold, and a word such as `skip` in
documentation is not a test marker. Exit 0 means commit; exit 1 means fix the code, never the check;
exit 2 means it could not run, which is a failure: repair its environment and commit nothing until it
exits 0.

| Shape the guard and the verifier refuse | Examples |
|---|---|
| Added skip or focus | `.skip(`, `.only(`, `xit(`, `xdescribe(`, `test.fixme`, `it.todo` replacing a test, `@Disabled`, `XCTSkip`, `#[ignore]`, `@pytest.mark.skip`, `pytest.skip(`, `from unittest import skip`, a bare `@skip(`, `self.skipTest(`, `t.Skip(` |
| Weakened assertion | an exact matcher replaced by a looser one (`toEqual` to `toBeDefined`, `toContain`, or `toBeTruthy`; `assertEqual` to `assertTrue`, `assertIsNotNone`, or `assertTrue(True)`; `XCTAssertEqual` to `XCTAssertNotNil`; `assert x == y` to `assert x`); fewer expected items; a larger tolerance or a lower precision argument; an assertion wrapped in try and catch or a retry; an early `return` at the top of a test |
| Suite narrowed | a deleted test file, a test file renamed or moved out of the runner's discovery pattern, `collect_ignore` or `--deselect` added, `-k "not ..."` in `addopts`, a narrowed `include` or `testMatch`, `passWithNoTests`, retries raised above 2, `fail_under` or a coverage floor lowered, a snapshot threshold such as `maxDiffPixels` raised, a gating suite whose test count fell against the baseline |
| Test-only production branch | `NODE_ENV === 'test'`, `process.env.VITEST`, `process.env.JEST_WORKER_ID`, `"pytest" in sys.modules`, `XCTestConfigurationFilePath`, or a production literal copied from a fixture value |

SKILL.md section 1 holds the rule for a red check: fix the code, never the check. If a constraint is
wrong, change its row in a commit of its own, `constraints: <rule> <old> to <new>`, with the measurement
output and the reason, never in the commit that was failing. Tightening passes silently; loosening
needs a DECISIONS.md entry in the same commit, and the final audit lists it.

## 9. Changing a test, and frozen refutation tests

**Changing a test.** Never widen an assertion without a spec change. Widening includes raising a
tolerance, replacing an expected value with the observed one, broadening a matcher, wrapping an
assertion in try and catch, retrying around an assertion, and loosening a snapshot threshold. A
commit that changes an expected value also changes the claim in SPEC.md (or a Known-wrong behaviour
row in MIGRATION.md) and names it in the message; a change that narrows what the claim promises is a
lowered target and needs a DECISIONS.md entry in the same commit.

Delete a test only when section 3 marked it useless, with the deletion recorded in STATE.md, or when
its claim is Dropped with a `why:`. For `feature` and every `move` variant, the pre-existing suite
passes unchanged: the same test names, no edited assertions, pass counts equal to the baseline recorded
at archaeology plus the new tests. A simplification that needs a test edit has changed behaviour.

**Why tests are frozen.** A maker that can edit the test that judges it will, under pressure, bend the
test instead of the code, and a test written by the maker after the code tends to encode what the code
does rather than what the claim promises. So at M and above the refutation test for each claim is
written before implementation by an agent that has not seen any implementation, proven red, and then
frozen: nobody who builds may change it. Three independent layers hold the freeze, because each alone
can be evaded: the guard hook refuses writes, the manifest records each frozen file's sha256, and the
verifier checks the manifest against the base commit and the provenance ledger, and every
`drive.py lint` runs the same check without a base.

**What is frozen.** At M and above: each claim's refutation test written by `drive:severe-tester`
before its package starts; the fix reproducer written by `drive:severe-tester` once it is seen failing
on the pre-fix commit; the shared fixtures and helpers those tests import, which the severe tester
lists; migration goldens and the characterization corpus once they are recorded; and
`design/baselines/` when the `ui` trait applies. Test-runner configuration is not frozen, because
packages legitimately add paths to it; the guard's suite-narrowed shapes in section 8 protect it.
Implementer unit tests for internals are not frozen.

**Writing and freezing, in order.**

1. `drive:architect` marks each TESTPLAN.md row at M and above with its test path and `frozen: y`, and
   keeps those paths out of every package's owned paths.
2. After the wave that lands the contract a claim depends on, and before the package that implements
   the claim starts, spawn a fresh `drive:severe-tester` in its before-implementation mode with the
   claim keys, the SPEC.md sections, DESIGN.md section 4 and the `contracts/` paths, the TESTPLAN.md
   rows, and the test paths it owns. It never receives package briefs, implementer reports, or code
   outside the contract.
3. The severe tester runs each new test on the current code and shows it red for the right reason:
   the failure is the claim's assertion, or the contract skeleton's not-implemented error raised at
   the call under test. A compile error, import error, missing fixture, collection failure, or
   timeout is the wrong reason, and so is a pass. For a language where tests cannot compile without
   the implementation, the wave 0 contract package supplies signatures that compile and fail at run
   time. The output goes to `.drive/proofs/<key>/red/red.txt`, the command and exit code to
   `.drive/proofs/<key>/red/commands.log`. A test that passes before implementation means the claim
   already holds or the test is wrong; it is reported, never frozen.
4. You run `drive.py freeze add <path> [<path> ...]`. It appends the paths to `.drive/frozen.txt`,
   writes `<sha256>  <path>` lines to `.drive/frozen.sha256`, and records each hash in the provenance
   ledger. A path is a file or directory inside the project and outside `.drive/`, and a directory
   freezes every file under it; `freeze add` refuses a path that does not exist and an already frozen
   file whose hash changed. From that moment the guard refuses the writes, deletes, moves, and in-place
   edits of those paths that it recognises, from every agent and from you, and `drive.py freeze check`
   catches through the recorded hash any change that got past it; while any test is frozen the guard also refuses
   `git stash`, `git reset --hard`, `--merge`, or `--keep`, `git clean` other than a dry run, and
   `git apply` or `git am` reading a patch from standard input or named through a variable. For a
   patch file given to `git apply`, `git am`, or `patch`, the guard reads the `---` and `+++` lines and
   also the `diff --git a/... b/...`, `rename from` and `rename to`, and `copy from` and `copy to`
   lines, so a pure rename or mode change of a frozen test is refused. A patch file the guard
   cannot read, because it is missing or 1 MB or larger, is refused while any test is frozen.
5. The frozen tests stay uncommitted until the package that turns them green lands, so main is never
   red: commit each claim's frozen tests with its package, together with `.drive/frozen.txt` and
   `.drive/frozen.sha256`. When a package fails and other packages in the wave land, run
   `drive.py freeze park <key>` to move that claim's frozen tests out of the suite into
   `.drive/local/frozen-parked/<key>/` with their hashes kept, and `drive.py freeze unpark <key>` before
   the package is retried. A key's files are the frozen files its STATUS row cites in `test:`,
   `severe:`, or `planned:` tokens and those its TESTPLAN.md row names; both commands refuse a file
   whose hash changed and a destination that already exists.
6. The TESTPLAN.md row and later the STATUS row cite the frozen test as its `test:` token.

For a fix at M and above the same order applies to the reproducer: the severe tester writes it from
HUNT.md's brief and the code, shows it failing on the pre-fix commit for the brief's reason, you freeze
it, and it lands in the fix commit.

**A maker who believes a frozen test is wrong** stops, changes nothing in the test, its fixtures, or
the code to match it, and reports `blocked` with a test dispute: the test as `<path>::<name>`, the
claim key, which of these it is (contradicts the claim, impossible together with another named test or
claim, needs an environment absent here, asserts internals the claim leaves open, or passes or fails
for a reason unrelated to the claim), the quoted assertion with its line, the quoted claim or test it
conflicts with, and the command and output that show it. You write
`.drive/reviews/<date>-dispute-<key>.md` from that report and spawn `drive:auditor` once. The ruling
is final for the run:

| Ruling | Means | What happens |
|---|---|---|
| `defect` | the test stands and the code is wrong | the maker's package resumes with the ruling as its evidence |
| `not_a_defect` | the test asserts something the claim does not promise | write the DECISIONS.md entry; run `drive.py freeze amend --open <path or key> --dispute .drive/reviews/<date>-dispute-<key>.md`; a fresh `drive:severe-tester` amends only that test and shows it red again on the pre-change code; `drive.py freeze amend --close <path or key>` rehashes it |
| `rubric_ambiguous` | the claim itself is unclear | clarify the claim in SPEC.md with a DECISIONS.md entry, then treat the test as `not_a_defect` when it fails the clarified claim and as `defect` when it matches it |

Nothing else rewrites the manifest: `freeze add` refuses to rehash a listed file whose hash changed,
and there is no force option. `amend --open` needs the dispute record, taken from `--dispute` or, when
you name a key, the newest `.drive/reviews/*-dispute-<key>.md`, holding `not_a_defect` or
`rubric_ambiguous`, and a DECISIONS.md entry that names the key or path and the amendment; while it is
open only `drive:severe-tester` may change those files. `amend --close` needs an open amendment and
the amended file present. The subcommands, spelled as the parser takes them:

| Command | Does | Exit codes |
|---|---|---|
| `drive.py freeze add <path> [<path> ...]` | lists and hashes new frozen paths | 0 frozen; 1 a frozen file changed; 2 no path, or a path missing or inside `.drive/` |
| `drive.py freeze check [--base <sha>]` | prints every departure from the manifest; with `--base`, also from the list and manifest at that commit | 0 clean or nothing frozen; 1 problems; 2 `--base` is not a commit |
| `drive.py freeze park <key>` | moves a claim's frozen files to `.drive/local/frozen-parked/<key>/` | 0 moved; 1 refused; 2 not exactly one key |
| `drive.py freeze unpark <key>` | moves them back | as for park |
| `drive.py freeze amend --open <path or key> [--dispute <file>]` | opens an amendment | 0 opened; 1 refused; 2 not exactly one target, or not exactly one of `--open` and `--close` |
| `drive.py freeze amend --close <path or key>` | rehashes the amended files and closes the amendment | as for `--open` |

Every subcommand takes `--root <dir>` and exits 2 when that directory has no `.drive/`.

## 10. Flakes and statistical proof

A flake fails and then passes with no code change. Never declare a flake fixed, or a test healthy,
from a handful of green runs; the number of clean runs needed depends on how often it failed.

**Measure the rate first.** Run the test in a loop on the unchanged code, with retries off and state
reset between runs (fresh database or fixtures, erased simulator, cleared caches, a new process), until
it has failed at least five times. The rate p is failures divided by runs. With fewer than five
failures the rate is a guess: keep running, or amplify first (a fixed seed, added load, raised
parallelism, injected delay at the suspected interleaving, a race detector, shuffled order) and record
the amplifier with the rate. Record the rate in STATE.md's Open failures entry or HUNT.md's
Reproduction table.

**Prove a fix with n consecutive clean runs**, where n = ln(α) / ln(1 − p), rounded up. α is the
chance of wrongly calling the fix good: 0.05 by default, 0.01 for money, auth, data integrity, or a
concurrency primitive. Double n when state cannot be fully reset between runs. If the rate was
measured under an amplifier, the proof runs under the same amplifier.

| Measured p | n at α 0.05 | n at α 0.01 | α 0.05, no reset | α 0.01, no reset |
|---|---|---|---|---|
| 1 in 10 | 29 | 44 | 58 | 88 |
| 1 in 50 | 149 | 228 | 298 | 456 |
| 1 in 200 | 598 | 919 | 1196 | 1838 |

Compute n and run the proof with a script, never with a model turn per run, and stop at the first
failure:

```bash
n=$(python3 -c 'import math,sys; p=float(sys.argv[1]); a=float(sys.argv[2]); print(math.ceil(math.log(a)/math.log(1-p)-1e-9))' <p> <alpha>)
i=0; while [ "$i" -lt "$n" ]; do <reset command>; <test command> </dev/null >/tmp/drive-flake-<key>.log 2>&1 || { echo "FAIL at run $((i+1)) of $n"; exit 1; }; i=$((i+1)); done; echo "PASS $n/$n"
```

Save the `PASS n/n` or `FAIL at run k` line with the p, α, and reset used under the round's proof
directory. When n passes about 300 slow runs, amplify to raise p rather than cutting n. The verifier
recomputes n from the recorded p and α and cites the line.

**Before a fix exists.** If the cause is shared state, test ordering, a missing await, or a race with
a cheap fix, fix it now and prove it as above. Otherwise quarantine it, in this order:

1. Add an Open failure to STATE.md: `<date> <slug>: <symptom>. Repro: <command> | Observed: <failures>
   of <runs> runs. Next: <step>`. The date and slug are the ticket.
2. Skip the test with the runner's own marker and a reason naming the ticket, for example
   `test.skip("quarantined: 2026-09-14-export-total-flake", ...)`.
3. In the same commit, record the skip as an exception row in CONSTRAINTS.md naming the test and the
   ticket (create the file with that one row when the run has none), with a DECISIONS.md entry whose
   Undo removes the skip. `drive.py guard` accepts a skip only as a recorded exception, so this
   quarantine is the one skip a run may add.
4. Add a row to TESTPLAN.md's quarantine table with the non-blocking lane command, and keep that lane
   running so observations accumulate.

Never delete a flaky test and never add blanket retries to a blocking lane. A frozen test is never
quarantined, and neither is a test that guards money, auth, or data loss: it keeps blocking and the
flake becomes an investigation. A claim whose only refutation test is quarantined stays at Partial.
The second time the same test needs the same workaround, the workaround ledger row reaches count 2:
stop and open an investigation.

## 11. Bugs: reproduce first

No production file changes until a command fails on the current code for the reported reason. Record
the command and the pre-fix commit in HUNT.md, then turn the command into a test in the project's own
framework, named for the symptom, with a `CLAIM` line. Make an intermittent bug reliable first, and
measure its rate as section 10 describes; a fix for a failure you cannot produce on demand cannot be
verified. Where a framework test is impossible (a physical device, a third party's production system),
the reproduction is a scripted probe whose output goes into HUNT.md, and the claim stays at Local
Proof until a live check exists.

A bug is complex when it has more than one plausible cause, is intermittent, crosses a module or
process boundary, arrives only as a symptom, or has already survived one fix. For a complex bug, and
for every fix at M and above, a fresh `drive:severe-tester` that has not seen any proposed fix writes
the reproducing test, which is then frozen (section 9). Its brief carries the report verbatim,
HUNT.md's brief section, the pre-fix commit, and the code; never a hypothesis naming a fix, a diff, or
an investigator's conclusion. When documentation states an invariant, add one test on an input where
the obvious narrow fix still breaks it.

The regression test must fail on the pre-fix commit. The handoff names the pre-fix sha, never a tree
path. The verifier, or the severe tester when it writes the reproducer, exports the pre-fix tree itself
with `git archive`, which leaves no worktree behind and never touches the shared checkout's git state,
and removes the copy in the same step:

```bash
mkdir -p /tmp/drive-prefix-<key> && git archive <pre-fix sha> | tar -x -C /tmp/drive-prefix-<key>
cp <regression test path> /tmp/drive-prefix-<key>/<regression test path>   # install dependencies inside the copy if needed
# run the test in the copy (expect red) and on HEAD (expect green); save both outputs under .drive/proofs/<key>/r<n>/
rm -rf /tmp/drive-prefix-<key>
```

Bisect, when a known-good commit exists, with the detached form in `references/parallel.md` section 11.
The hunt's full procedure, including the check-the-plug list, the bug classes, two-way confirmation,
the sibling sweep, and the masked-workaround check, is in `references/shapes/fix.md`.

## 12. Schedules, migrations, and screens

**Never wait on a schedule to prove anything.** Fire the scheduled handler through its local trigger
or the system's own verb, trigger the workflow now, fire the alarm from the test harness. A status
never depends on a future event. Only a soak with no triggering signal may wait
(`references/long-running.md`), and nothing is Done while one is open.

**Migration goldens and replay.** Nothing moves until the old behaviour is pinned:

1. Build the characterization corpus from real inputs (recorded traffic with credentials stripped,
   stored requests, production-shaped fixtures), run it through the old system, and store normalised
   outputs as golden files headed with `observed_at`, `commit`, and `input`. Normalise only what the
   contract does not promise (timestamps, generated ids, unordered collections), and name each
   normalizer in MIGRATION.md's Parity section. Commit the goldens before the first commit that
   changes old code, and at M and above freeze them in the same commit (section 9).
2. Goldens record what the old system does, bugs included. Fixing one during the move is a row marked
   fixed in MIGRATION.md's Known-wrong behaviour table, with a DECISIONS.md entry and its own claim.
3. Replay the corpus against the new code in the integration lane. The diff is empty, or every
   difference is explained by a named normalizer or a Known-wrong behaviour row.
4. Compare old and new live on deterministic decisions (authorization verdicts, routing, cost lines),
   not on nondeterministic payloads.
5. Execute the rollback before cutover, then re-run the corpus on the rolled-back system. A rollback
   that has never run is not evidence that rollback works.

TESTPLAN.md gains a parity section with one row per corpus class.

**Vision is not a data oracle.** A screenshot proves layout and rendered state. Pair every number,
name, or list on screen with an accessibility-tree read, an API response, or a remote data read that
shows the same value. Refute a displayed total with a value computed independently from the same
fixture, never with a value read back from the UI.

## 13. Coverage and mutation

Coverage never gates and never moves a status. Use it to find an untested branch in a module that
carries a claim; never print a percentage in TESTPLAN.md or the report. A mutation-testing tool is
optional: run it only incrementally, on changed files in pure-logic modules that carry money, auth, or
data-loss claims, in the integration lane, where its score informs and never blocks. The verifier's
manual mutation in section 14 is always required, and it is the only mutation that also covers a
diff that touched tests without touching source.

## 14. What the verifier does to the suite

`drive:verifier` edits nothing in the repository, and the tests it runs were written by someone else.
For each round it:

1. Runs every lane in TESTPLAN.md's "How to run" with the commands from the handoff, saving output
   under `.drive/proofs/<key>/r<n>/` and a line per command in `commands.log`.
2. Runs `drive.py freeze check --base <range base>` when the run has `.drive/frozen.txt`. Every line it
   prints (a CHANGED, MISSING, ADDED, UNHASHED, or UNRECORDED file, a path REMOVED from the list or
   the manifest, or a hash REHASHED since the base without a closed amendment) is a blocking gap
   whatever the verdict on the claims.
3. Runs `drive.py guard --base <range base>` and reports every shape in section 8's table that has no
   recorded exception.
4. Confirms each claim's named test exists, asserts an observable outcome rather than a mock call,
   sits at an honest layer by section 2, and would fail against a constant-returning stub. At M and
   above the claim's evidence must include its frozen test; an implementer's own test alone does not
   carry the claim.
5. Mutates by hand for the five riskiest claims, or all claims when there are five or fewer, in a copy
   that does not duplicate dependency directories:

   ```bash
   mkdir -p /tmp/drive-<repo>-mutant-<key>-r<n> && git archive HEAD | tar -x -C /tmp/drive-<repo>-mutant-<key>-r<n>
   ln -s <checkout>/node_modules /tmp/drive-<repo>-mutant-<key>-r<n>/node_modules   # each dependency directory GOAL.md's probe names
   # break the line the claim depends on (flip the operator, remove the guard, return a constant), run the named test in the copy, expect red
   rm -rf /tmp/drive-<repo>-mutant-<key>-r<n>
   ```

   Never run an install inside a copy that links a dependency directory. A test that stays green is a
   blocking gap. A copy that cannot build goes under `not_checked` with the reason.
6. Diffs test files over the range for widened assertions, replaced expected values, and new
   try-and-catch or retry wrappers; each without a matching spec change is blocking.
7. Checks every kindness-ledger row has mitigation evidence that exists, and states in
   `harness_kindness` where each double in scope is kinder than production.
8. For a fix, runs the regression test in its own `git archive` copy of the pre-fix commit (red) and
   on HEAD (green), as section 11 shows. For an intermittent fix, recomputes n from the recorded rate
   and α and checks the saved `PASS n/n` line (section 10).
9. For `feature` and `move`, compares test names and pass counts with the archaeology baseline.
10. Checks that evidence files exist and postdate the commits they claim to cover, then sets
    `rung_supported` to the highest rung it proved.

## 15. Platform pointers

| Platform | Read | For |
|---|---|---|
| Cloudflare Workers, D1, Durable Objects, Queues, Workflows | `references/domains/cloudflare.md` sections 9 and 10 | lanes, the Vitest plugin setup and version pin, seeded ledger rows, the kinder-shim probe |
| iOS | `references/domains/ios.md` section 7 | Swift Testing and XCUITest lanes, stub ledger rows, snapshots, the accessibility audit, a minimal hard suite |
| Web | `references/domains/web.md` | Playwright lanes, visual regression, axe, Lighthouse budgets |
| Any rendered UI | `references/ui-verification.md` | the capture matrix, objective checks, the reviewer protocol |

## 16. Excuses and rebuttals

| The argument for skipping the step | Why it fails |
|---|---|
| "A mock is fine; the real runtime takes too long to set up." | The runtime is what enforces the limits. Its setup is a one-time cost, while a kinder double lets limit violations reach production. |
| "It passed twenty times in a row." | Twenty clean runs prove little against a one-in-fifty failure; compute n from the measured rate. And green runs against a kinder harness are not evidence at all. |
| "This test is flaky; skip it for now." | Quarantine needs a ticket, a repro command, a CONSTRAINTS.md exception row, and a running lane. Money, auth, data-loss, and frozen tests block. |
| "The expected value was wrong, so I set it to what the code returns." | That is widening. Change the claim first, or fix the code. |
| "The frozen test is obviously wrong; I will fix it and mention it." | A maker never edits the test that judges it. File the dispute; the auditor rules. |
| "Freezing slows the build; let the implementer write the claim tests." | A test written after the code encodes the code. At M and above the claim's test comes first, from the claim alone. |
| "This threshold is unrealistic for this codebase." | Record today's measurement as the floor, in its own commit. Never loosen inside the failing commit. |
| "The bug is obvious; a reproduction is ceremony." | A fix whose test never failed proves nothing. A simple reproduction takes minutes. |
| "I know the fix, so I will write the regression test too." | A test shaped by the fix passes the fix. A fresh severe tester writes it for complex bugs and at M and above. |
| "The scheduled run will exercise it tonight." | Trigger it now. A status cannot wait on a future event. |
| "The screenshot shows the right number." | Pair it with a tree read or an API response. |
| "Coverage is ninety percent." | Coverage says lines ran, not that any test can fail. |
| "More tests are safer." | Tests without claims dilute the signal and cost every future run. |

## 17. Red flags

- A test without a claim key, or a claim whose evidence has no test at an honest layer.
- A test double added in the diff with no new kindness-ledger row.
- A skip marker without a ticket and a CONSTRAINTS.md exception row, or a test deleted in the commit
  that turned a check green.
- An expected value changed in a commit that does not touch SPEC.md or MIGRATION.md.
- A CONSTRAINTS.md value moved in the easier direction, or `drive.py guard` exit 2 treated as clean.
- `drive.py guard` run before GOAL.md records `baseline_sha`, which compares only with HEAD and
  misses every loosening already committed.
- A frozen file whose hash differs from the manifest, a path removed from `.drive/frozen.txt` without
  an amend record, or a frozen test edited by anyone but a severe tester after a ruling.
- A frozen test with no `red/red.txt`, or one whose recorded red was an import or compile error.
- A claim at M and above whose only test was written by its implementer.
- A claim whose only assertion is that a mock was called.
- A fix with no recorded failing run of its reproduction on the pre-fix commit, or a pre-fix check run
  in a worktree instead of a `git archive` copy.
- A flake called fixed with no measured rate, or with fewer clean runs than n.
- A fix whose makers added more than two tests.
- A status that depends on a scheduled run.
- A screenshot as the only evidence for a data claim.
- A coverage percentage in TESTPLAN.md or the report.
- A platform with documented limits and no limits probe, or a toolchain upgraded since the last probe.
