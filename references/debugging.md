# Debugging: reproduce, isolate, prove, convert

Bug hunts, failed gates that survive one retry, flaky tests, incidents and agent process failures. Covers the failure
record, reproduction, mechanical isolation, the hypothesis ledger, root-cause confirmation, proof of fix, the sibling
sweep and conversion of every resolved failure into tests, controls, generic tasks and lesson candidates. Test mechanics
(frozen paths, test-diff audit, red-before-green format): `testing.md`. Lesson storage and promotion:
`memory-and-lessons.md` (P7, P8). Parallel lanes: `swarms.md`. Names follow `conventions.md`; if this file disagrees,
conventions wins. Rule prefixes: **DBG** investigation · **PRF** proof · **LSN** conversion · **PFX** process failures ·
**ESC** escalation.

Terms. **Failure**: an `O-NNN` record. **Repro**: a committed script or test that exits non-zero on the failure and
prints one `SIGNATURE: <line>`. **Baseline rate p**: failures/runs measured on the unfixed code. **Mechanism**: the
causal chain from a condition to the symptom. **Root cause**: the smallest intervention that turns the minimal repro
from failing at p into passing at PRF-02 confidence, confirmed in both directions. **Contributing factors**: why tests
missed it, why it shipped, why detection was slow, what masked it.

Investigation states (record header): `OPENED` → `REPRODUCED` | `UNREPRODUCED(<reason>)` → `CONFIRMED` → `PROVEN` →
`SWEPT` → `CONVERTED` → `FIXED` | `FIXED-PENDING-LIVE`. Nothing skips a state. The matching gate in STATUS.md uses the
conventions gate states (`PENDING`, `PASSED`, `PENDING-LIVE`, `BLOCKED(<reason>)`).

## When to load

| Moment | Use |
|---|---|
| Mission shape BUG, or `live_incident` trait | Whole file; `templates/investigation.md` → `.mission/investigations/O-NNN.md` |
| A task gate fails again after one retry (any shape) | DBG-01..03, DBG-10, Scale by class (usually S-depth) |
| A test failed then passed on retry (flaky, `testing.md` E-5) | DBG-11, PRF-02, `scripts/flake-runs.sh` |
| A root cause is claimed | DBG-33, confirmer brief in Procedure step 7 |
| Proof of fix before a task or failure closes | PRF-01..07, checklist P1–P12 in the template |
| Phase 9 Retro, or any PROVEN failure | LSN-01..05, template parts C–D, `memory-and-lessons.md` P7 |
| The mission machinery produced a wrong outcome (false done, gamed test, thrashing) | PFX rules + taxonomy |
| Two rounds with no SUPPORTED hypothesis, 3 failed fixes, refuted twice | ESC-01..03, Model routing ladder |

| Artefact | Template / script | Target |
|---|---|---|
| Failure record + ledger + proof + conversion | `templates/investigation.md` | `.mission/investigations/O-NNN.md` (M+; S: PR description) |
| Open-failure pointer (≤4 lines) | `templates/STATE.md` § Open failures | `.mission/STATE.md` |
| Repro | written by the repro builder | `tests/regression/O-NNN-repro.<ext>` (frozen once red) |
| Flake run count and tally | `scripts/flake-runs.sh` | `.mission/bin/flake-runs.sh`; tally in VERIFICATION §4 and part P |
| Bug spec (Current / Expected / Unchanged) | `templates/BUGFIX-SPEC.md` | `.mission/SPEC.md` (M bug missions) |
| Escalation | `templates/escalation-brief.md` + ledger path | brief for the next rung |
| Lesson candidate | `templates/LESSONS-INBOX.md` | `.mission/LESSONS-INBOX.md` |
| Evidence logs | — | `.mission/logs/O-NNN/` (large logs: `.mission/tmp/`) |

## Core rules

MUST / SHOULD / MAY per conventions §9.

### Intake (DBG-01..04)

- **DBG-01 MUST** open the failure record (template part A) *before* touching code: symptom verbatim, expected vs
  observed, first seen, detection path, environment fingerprint (commit, runtime/OS versions, config hash, simulator
  or device, local/preview/prod), blast radius (unknown is allowed, said explicitly). Add the 2-line O-entry in STATE.md.
- **DBG-02 MUST** separate mitigation from resolution. A revert, retry, flag-off or manual recovery may close the
  *incident*; the record stays open until PRF gates pass. Mitigation is logged in part A with its time.
- **DBG-03 MUST** check the plug first and record each item as `command → exit → salient line`: right commit or
  deployment under test; build fresh (no stale artefacts); env vars, secrets and bindings present; the failing test
  actually executes (not skipped, no `.only` elsewhere, correct filter); correct cwd, branch and target environment;
  exit codes not masked by pipes. A failed plug check is the finding: fix it, re-run, and close the record at S-depth
  if the failure disappears.
- **DBG-04 SHOULD** classify against the hard-bug class table and load that row's tactics. Two plausible classes →
  record both; the second becomes a hypothesis family.

### Hard-bug classes (DBG-04)

Tool flags named here are common practice, not verified per stack: probe with `--help` at setup.

| Class | Signals | Repro / amplify | Isolate | Proof | Symptom-patch trap |
|---|---|---|---|---|---|
| Flaky / race / timing | rate < 100%; order-dependent; worse under load or in CI | loop runs; shuffle order; raise parallelism; throttle CPU; inject latency at suspected interleavings; race detectors (TSan, `go test -race`) | serialize one resource at a time; monotonic timestamps + ids at boundaries | PRF-02 n from p, state reset per run | sleeps, longer timeouts, blanket retries; use condition-based waits |
| Heisenbug | vanishes with debugger, logging or `-O0` | record-and-replay where available; ring-buffer logging dumped on failure; identical build flags | differential on build config (flags, optimizer, precision, backend) | re-run with instrumentation removed | "fixed" because instrumentation shifted timing |
| Resource / memory leak | monotonic growth; OOM after hours; throughput decay | soak script compressing time; heap snapshots t0/t1/t2 | diff snapshots by retained type; bisect with soak threshold | soak ≥3× pre-fix time-to-failure, flat trend | periodic restarts, bigger instance |
| Env / config drift | one environment fails; "works locally" | capture fingerprints good vs bad (versions, flags, bindings, secrets present, compatibility date) | delta-debug the fingerprint diff: apply half the differences to the good env, repeat | repro passes in the bad env after a config-as-code change | hand-editing prod config; hand-written binding types |
| Dependency upgrade | broke after a lockfile change | old vs new pinned in two worktrees | read changelog first; bisect dependency versions or lockfile commits | red on new version, green with fix; pinned-version test | pinning forever without O-id and task |
| Data-dependent | only some records, tenants, inputs | capture the failing input (sanitized); ddmin to 1-minimal | property generator around the minimal case to find the boundary | minimal case as regression test + property test | special-casing the one bad record |
| Distributed / async | duplicates, lost or reordered effects, contradictory reports | replay recorded sequences; force redelivery; kill between accept and record | correlation ids end to end; per-message timeline; one O-id per overlapping cause | duplicate/reorder injection tests; idempotency enforced by storage | dedupe in the UI only |
| Performance regression | metric crossed a threshold after a change | benchmark with warmup, ≥10 runs, variance reported, same hardware | `git bisect run` with a threshold script (old/new terms); profiler diff | back under threshold with non-overlapping variance bands | caching that hides the hot path |
| iOS simulator vs device | device-only crash, perf or memory | classify against Apple's difference list (performance, background suspension, case-sensitive FS, missing hardware/APIs, Metal, APNs) | device logs + Instruments; same build config sim vs device | on-device run evidence, else `UNVERIFIED(DEVICE_REQUIRED)` | declaring fixed from the simulator |
| Cloudflare Workers runtime | prod-only intermittency; cross-request errors; `wrangler dev` ≠ deployed | hammer one warm isolate with requests from different tenants; cold-start runs | differential local vs preview; diff compatibility date, flags, bindings; grep module-scope mutable state and shared request I/O objects | Workers-runtime integration test + preview canary | global caches or retries around cross-request I/O |

### Reproduce (DBG-10..14)

- **DBG-10 MUST** produce a repro that exits non-zero on failure and prints `SIGNATURE: <one line>`. Gate
  `REPRODUCED` passes only on the verifier's own run. No fix work starts before it, except under DBG-13.
- **DBG-11 MUST** record the baseline: `deterministic`, or p = failures/runs with ≥5 observed failures. Fewer than 5
  failures → p is a guess: keep running or amplify. Amplify races (stress, parallelism, injected latency) *before*
  measuring, and record the amplification with p.
- **DBG-12 SHOULD** minimize: ddmin inputs and config, strip unrelated steps, go to the lowest level that still shows
  the signature. A repro over ~50 lines or ~60 s runtime SHOULD be minimized before hypotheses are generated.
- **DBG-13 MAY** record `UNREPRODUCED(<reason>)` only when the failure lives where the agent cannot reach: production-only
  data, physical device, third-party outage, missing credentials. Hypotheses are then tested observationally (logs,
  traces); any fix carries `speculative: true` in part B plus a monitoring follow-up (D3) and a recurrence query.
- **DBG-14 MUST** freeze the repro once red: commit it alone under `tests/regression/`, add it to the frozen manifest
  (`.mission/bin/frozen-manifest.sh add`). Changes go through `templates/TEST-DISPUTE.md`, never a silent edit. For
  intermittent failures used with `git bisect run`, the repro loops internally until it sees a failure or reaches n runs;
  otherwise bisect mislabels commits.

### Isolate before theorizing (DBG-20..22)

- **DBG-20 MUST** run the mechanical isolators that apply, before model-heavy reasoning, and record which ran and why
  the others did not apply:
  - known-good revision → `git bisect start <bad> <good>` then `git bisect run <repro>` (exit 0 good, 125 skip, other
    codes 1–127 bad). Re-verify the first-bad commit by running the repro on it and on its parent.
  - large failing input or config → ddmin to a 1-minimal case (removing any single element makes the failure vanish).
  - an environment that works → differential run (local vs preview, simulator vs device, old vs new dependency, CPU vs
    other backend); diff the fingerprints before diffing behaviour.
- **DBG-21 MUST** instrument component boundaries once (what enters, what leaves) to find *where* bad state enters,
  before instrumenting internals. Then re-run the unchanged repro: the failure must still occur at ≈p (Heisenberg
  check). If it vanishes, the instrumentation is a variable; switch to low-overhead logging dumped on failure.
- **DBG-22 MUST NOT** load more than ~200 log lines into the orchestrator's context. `mission-scout` extracts and quotes
  verbatim lines with `path:line`; the orchestrator spot-checks 2 quotes per extraction with grep.

### Hypothesis ledger (DBG-30..35)

- **DBG-30 MUST** keep the ledger in the investigation file (template § Ledger). Each `H-NNN`: statement, layer,
  mechanism, prediction ("if true, then X under Y"), discriminating experiment (command + the one change),
  expected-if-true and expected-if-false **written before running**, raw result with `log path:line`, status.
- Statuses: `OPEN` (untested; may carry `assigned: <lane>`) · `SUPPORTED` (prediction held once) · `FALSIFIED`
  (prediction failed; never deleted) · `CONFIRMED` (two-way intervention, separate confirmer) · `INCONCLUSIVE`
  (experiment not discriminating or not runnable here; reason + what would test it).
- **DBG-31 MUST** change one variable per experiment. Bundled changes are uninterpretable and count as no experiment.
- **DBG-32 MUST** keep FALSIFIED entries with their evidence. Re-opening one requires new evidence cited in the ledger.
  Briefs to any rung list the falsified H-ids as "do not re-test".
- **DBG-33 MUST** mark `CONFIRMED` only on a two-way intervention on the minimal repro: cause present → fails at ≈p;
  cause removed alone → passes at PRF-02 confidence; cause re-introduced → failures return. A separate confirmer
  (Model routing) issues the verdict `CONFIRMED | REFUTED(<step, evidence>) | UNVERIFIED(<missing>)`, seeing the
  record, ledger, repro and evidence files only, never the investigator's transcript, and tries one experiment that
  separates a cheaper alternative explanation first. At S with a deterministic repro, the verifier's red→green pair on
  the minimal change is the two-way intervention.
- **DBG-34 SHOULD** list ≥3 hypotheses spanning different layers (code, data, config/env, dependency, timing,
  platform) before testing the favourite; the favourite still runs first if it is cheapest. SUPPORTED is not
  CONFIRMED. Several SUPPORTED hypotheses may be jointly sufficient contributors, not rivals: test the combination.
- **DBG-35 MUST** treat each fix attempt as an experiment logged in the ledger. After 3 failed fix attempts on one
  failure, stop fixing: escalate (ESC-02) with a "question the design" brief. Cheap likely fixes without diagnosis
  (the "light bulb" exception) are allowed once, logged as an untested hypothesis, and never recorded as a root cause.

### Experiment lanes (DBG-40..42, optional)

- **DBG-40 MAY** run hypotheses in parallel only when all hold: `REPRODUCED` passed; ≥3 OPEN hypotheses whose
  experiments are independent (none needs another's result); each experiment costs ≥ ~10 min serial; budget covers
  lanes × lane cap. Lane caps: S 0 · M 3 · L 4 · XL 6 (one lane per cause family at XL), inside the wave caps of
  conventions. Otherwise run serially.
- **DBG-41 MUST** give each lane one H-id, its own worktree and branch `claude/<mission>/<lane-id>-O-NNN-H-NNN` (conventions §9), a turn cap (M 25, L 40),
  the frozen repro, the falsified list and the return schema: `STATUS: SUPPORTED | FALSIFIED | INCONCLUSIVE | BLOCKED`,
  experiments `[cmd, change, expected_true, expected_false, observed, runs, failures, log path:line]`, new observations,
  ≤2 new hypotheses, patch sketch (file:line only, SUPPORTED only). Lanes never edit tests, the repro, harness, timers or
  equality code, never push, never touch other worktrees. An honest FALSIFIED is a successful lane.
- **DBG-42 MUST** synthesize returns into the ledger (reject returns without raw output excerpts), copy lane logs into
  `.mission/logs/O-NNN/` before worktree cleanup, and run one confirmer on the leading SUPPORTED hypothesis before any
  fix. The fix lands from a clean branch, never from a lane's experimental hacks. Read-only "argue for a theory" fan-out
  is not a lane.

### Proof of fix (PRF-01..07)

The verifier fills checklist P1–P12 (template § P) in a clean worktree; the maker never issues PROVEN.

- **PRF-01 MUST** show red→green: the frozen repro fails with the recorded SIGNATURE on the fix's parent commit and
  passes on the fix commit, both run by the verifier (`mission-verifier`; `mission-critic` for money, auth, data
  integrity, concurrency) in a clean worktree, with commands, exit codes and signature lines recorded.
- **PRF-02 MUST** prove intermittent fixes statistically: **n ≥ ln(α)/ln(1−p)** consecutive clean runs with state
  reset between runs (fresh DB/fixtures, erased simulator, cleared caches, new process). α = 0.05 by default; 0.01 for
  money, auth, data integrity or concurrency primitives. **Double n when state cannot be fully reset.** p is the
  baseline from DBG-11 (amplified p only if the proof runs under the same amplification). Run it with
  `.mission/bin/flake-runs.sh --p <p> [--alpha 0.01] [--no-reset] -- <repro>`; the verifier re-derives n with
  `--dry-run` and cites the `PASS n/n` line. A model turn per run is forbidden: the script prints the tally.

| Baseline p | n at α 0.05 | n at α 0.01 | α 0.05, state not reset | α 0.01, state not reset |
|---|---|---|---|---|
| 1/10 | 29 | 44 | 58 | 88 |
| 1/50 | 149 | 228 | 298 | 456 |
| 1/200 | 598 | 919 | 1196 | 1838 |

n > ~300 slow runs → amplify first (raises p, shrinks n) or run the loop on CI with the tally artefact; never cut n.

- **PRF-03 MUST** fix at the mechanism, not the symptom: the diff touches the file:line named by the CONFIRMED
  hypothesis. Catch-and-ignore, blanket retry, timeout bump, sleep, disabled feature or special-cased input are rejected
  unless the confirmed cause *is* an external transient and part B says so. One change; refactors become a T-NNN.
- **PRF-04 MUST** pass the test-diff audit (`templates/test-diff-audit.md`, `scripts/test-diff-grep.sh`): no deleted,
  skipped, weakened or special-cased tests; no harness, timer, equality or evaluator edits unless justified in the
  ledger; test count not decreased; frozen manifest clean.
- **PRF-05 MUST** run a sibling sweep: express the mechanism (not the line) as a searchable pattern (rg, ast-grep, lint
  query), list every hit with `path:line` and a conventions disposition: `FIXED` (commit + test), `REFUTED` (not
  affected, evidence), `DEFERRED` (T-NNN, owner, milestone). `mission-reviewer` checks ≥3 REFUTED hits blind; any
  disagreement → full re-review of the sweep. Also enumerate the ways the mechanism can be bypassed and test each.
- **PRF-06 MUST** run the masked-bug check: list prior workarounds for this symptom (grep comments, commit messages,
  retries and flags near the mechanism). L/XL: remove each obsolete workaround and re-run the broader suite; S/M: SHOULD
  do the same, otherwise keep it with a reason in part E. Removing a workaround "because the root cause is fixed" without
  a re-run is forbidden.
- **PRF-07 SHOULD** (deployed systems) define a recurrence check in the target environment: canary, scheduled check or
  a log query on the SIGNATURE. Until it has run, the record is `FIXED-PENDING-LIVE` and the gate `PENDING-LIVE`.
  Proof that needs a device, credentials or production access stays `UNVERIFIED(<reason>)` with a `BLOCKED-HUMAN` item;
  never green.

### Conversion (LSN-01..05)

- **LSN-01 MUST** end every resolved failure with conversion (template parts C–D): D1 regression test (always; usually
  the frozen repro or a smaller test red on the parent), plus as warranted D2 prevention control (lint rule, PreToolUse
  hook, type, schema/DB constraint, CI check) with a self-test that rejects a seeded bad example, D3 generic audit task,
  D4 STATE F/R-entry, D5 lesson candidate in `.mission/LESSONS-INBOX.md`. Every output has an owner and a completion
  check. State `CONVERTED` requires D1 plus an explicit yes/no decision on D2–D5.
- **LSN-02 MUST** prefer controls to prose, in this order: regression test → lint/hook/type/schema control → generic
  audit task → prose lesson. A lesson candidate that could be a control says why it is not one.
- **LSN-03 MUST** scope every lesson (`Applies when`, `Does not apply when`) and cite evidence. Draft D5 only if
  mechanism CONFIRMED ∧ class general ∧ (count ≥2 ∨ cost ≥1 day ∨ user-visible or production) ∧ a control is impossible
  or insufficient; otherwise write "no lesson: <reason>" and keep it as a STATE fact or rule (`memory-and-lessons.md`
  CMP-03, P7).
- **LSN-04 MUST** write blamelessly: the subject is a missing mechanism ("the system lacked a frozen repro, so the test
  edit went unnoticed"), never "the agent should be more careful". "5 whys" is a prompt for contributing factors, not
  the method.
- **LSN-05 MUST** phrase generic tasks as audits over an enumerable class with a completion check: `T-NNN Audit all
  <class scope> for <mechanism>` · scope query `<rg/ast-grep>` · done when every hit has a test or disposition. "Improve
  robustness" is not a task.

### Process failures (PFX-01..03)

A process failure is the mission machinery producing a wrong outcome (false done, gamed signal, wasted rounds). It is
a bug in the mission, not in the product.

- **PFX-01 MUST** record it as `O-NNN` with `Kind: process-failure (class <NAME>)` in the same template, apply the
  class remedy, and log it in STATUS.md stop log. Its D1 is a hook self-test or an eval case, not a product test.
- **PFX-02 MUST** add the class's mechanical control (hook, gate, preflight, template field, return-schema field) when
  the same class recurs twice in a mission or across missions. A stern sentence in a prompt is not a control.
- **PFX-03 SHOULD** classify with `mission-checker`; unclassifiable or two plausible classes → `mission-reviewer`.

| Class | Detection signature | Remedy | Mechanical control |
|---|---|---|---|
| `PREMATURE_DONE` | done/fixed claim without gate evidence; gate flipped by a maker; verifier cannot reproduce green | reopen; run the verifier | only verifiers' verdicts flip gates; Stop hook runs `check.sh`; return schema demands command + exit + line |
| `GAMED_TEST` | test deleted, skipped, weakened, special-cased; harness/timer/equality/evaluator edited; fixture literals in prod code | revert those edits; re-run the gate; report to human in the summary; that task moves one rung up | frozen paths + `protect-frozen.sh` + manifest + test-diff audit; TEST-DISPUTE channel |
| `SYMPTOM_PATCH` | retry, timeout bump, sleep, catch-and-ignore or feature disable with no CONFIRMED mechanism | reject the fix; back to the ledger | PRF-03 item P5; diff grep for symptom patterns |
| `LOST_CONTEXT` | re-tests a FALSIFIED hypothesis; violates an earlier constraint; contradicts STATE.md | stop; reload ledger + STATE resume pointer | ledger file as source of truth; SessionStart hook injects open O-ids; handoff at ~60% context |
| `WRONG_ASSUMPTION` | action rested on an unverified belief (units, env, API semantics, which deployment) that proved false | record the falsified fact; re-run affected experiments | `A-NN` with a verification command; check-the-plug step; facts need an evidence level |
| `TOOL_MISUSE` | stale build; wrong branch/cwd/environment; exit code masked by a pipe; grep over the wrong tree | re-run with the fingerprint printed | fingerprint in every evidence block; exit-preserving runners; `check.sh` smoke preflight |
| `SPEC_GAP` | "expected" undefined, or the fix changes product or public-contract behaviour | freeze the fix; write `BUGFIX-SPEC.md` Current / Expected / Unchanged | bug spec at intake; public-contract diff check; ESC-03 |
| `CLASSIFIER_BLOCK` | refusal text; empty or partial output; silent model fallback; sudden quality drop on security work | discard partial output; re-run the same brief on an Opus 4.8 agent; log the fallback event | pre-route security/exploit work to Opus 4.8 agents; log model per spawn; never rephrase to evade |
| `MISSING_ENV` | needs credentials, device, account, paid API or production access that is absent | gate `UNVERIFIED(MISSING_<X>)`; queue `BLOCKED-HUMAN`; continue other work | intake preflight lists required secrets and devices per gate; never mock-substitute a live gate |
| `FLAKE_MISREAD` | "fixed" after too few runs; "just flaky" without a measured p | compute n; re-run the proof | `flake-runs.sh`; quarantine needs an expiry and an O-id (`testing.md` E-5) |
| `THRASHING` | same signature twice without a ledger change; turn cap exceeded; oscillating fixes; very long trajectory | stop; write a ≤300-word state brief; escalate a rung | turn/token caps per role; ledger update required per round; loop `stall_window` |
| `SWARM_MISALIGNMENT` | lanes test overlapping hypotheses, edit the same files, or return narratives; synthesizer treats SUPPORTED as CONFIRMED | reject non-schema returns; re-dispatch that lane; two misaligned rounds → serial | disjoint H-ids; worktree per lane; fixed return schema; mandatory confirmer |
| `SCOPE_CREEP` | fix diff carries refactors or drive-by changes; diff far larger than the mechanism | split into fix commit + follow-up T-NNN | one-change rule; diff-size note in P5; refactor needing design → design review task |

### Escalation (ESC-01..03)

- **ESC-01 MUST** climb the debugging ladder (Model routing) one rung at a time. Every promotion carries the failure
  record path, the ledger path, the frozen repro command and a ≤300-word brief "what we know / what is falsified /
  what is untried" in `templates/escalation-brief.md`, never the prior transcript. Log the rung change in BUDGET.md.
- **ESC-02 MUST** escalate one rung when any holds: 2 consecutive rounds end with no SUPPORTED hypothesis; 3 failed fix
  attempts (with a "question the design" brief); the confirmer REFUTES twice; the turn or token budget for the rung is
  spent; ≥2 causes interact. An exhausted *repro* budget does not escalate: it switches the deliverable (Scale by class).
- **ESC-03 MUST** stop and put the item in the human queue when: remaining experiments are destructive, touch production
  data or spend money; the repro needs credentials, devices or accounts the agent lacks; the confirmed fix changes a
  public contract or product behaviour; a classifier refusal persists after rerouting to Opus 4.8; or the
  `mission-strategist` reset has been used twice without a SUPPORTED hypothesis. Unattended runs set the task
  `BLOCKED-HUMAN` and continue with other work.

## Procedure

Roles below are defaults; Model routing lists guards. Every step appends to `.mission/investigations/O-NNN.md` (S:
the PR description) and ends with evidence, not narrative.

0. **Mitigate** (only when users are impacted, `live_incident`): revert, flag off, retry or manual recovery with a human
   checkpoint for production actions. Log it in part A. The record stays open (DBG-02). At XL open one O-id per suspected
   cause with a shared timeline.
1. **Open the record.** `mission-worker` (triage) copies `templates/investigation.md` to
   `.mission/investigations/O-NNN.md` and fills part A from the issue, CI log or user report. The orchestrator rejects a
   record missing any DBG-01 field. Add the 2-line O-entry to STATE.md Open failures.
2. **Check the plug.** `mission-checker` runs each DBG-03 item and records `command → exit → line`. A plug finding →
   fix, re-run, close at S-depth if gone (still D1 if a test was missing).
3. **Classify.** Pick the hard-bug class row(s) and the scale by class. Profile says BUG but the fix will change a
   public contract → add `published_api` and write `BUGFIX-SPEC.md` first.
4. **Reproduce.** `mission-worker-high` (repro builder; `mission-builder` for concurrency or platform-runtime bugs)
   writes `tests/regression/O-NNN-repro.<ext>` printing `SIGNATURE:`; measures p with ≥5 failures (amplified if needed;
   `flake-runs.sh` is not for measuring p, run a counting loop); minimizes (DBG-12); commits it alone and freezes it.
   `mission-verifier` re-runs it on a clean worktree → gate `REPRODUCED` with p. Repro budget spent → observability
   deliverable, `UNREPRODUCED(<reason>)` (Scale by class).
5. **Isolate.** Wire and run the applicable DBG-20 isolators as scripts (`mission-worker` wires them; no model per bisect
   step). Attach the bisect log, ddmin result or fingerprint diff. Add boundary instrumentation once, then the Heisenberg
   check. `mission-scout` extracts log lines (≤200 to the orchestrator).
6. **Hypothesize and experiment.** The investigator (rung per Model routing) writes ≥3 H-NNN across layers with both
   expected outcomes before each run; one variable per experiment; results cite `log path:line`. Orchestrator checks the
   ledger changed this round; unchanged twice → `THRASHING`. DBG-40 holds → experiment lanes (DBG-41, `swarms.md` for
   dispatch). Round budget per rung: 2 rounds without SUPPORTED → ESC-02.
7. **Confirm.** Brief `mission-reviewer` (`mission-critic` for money, auth, data integrity, concurrency) with record +
   ledger + repro + evidence files, not transcripts: "Refute the claim that H-NNN causes O-NNN. In a fresh worktree at
   `<sha>`: (1) re-run the repro at baseline, record failures/runs, UNVERIFIED if not ≈p; (2) apply the cause-removal
   change alone, run n = ceil(ln α / ln(1−p)) times; (3) re-introduce the cause, confirm failures return; (4) test one
   cheaper alternative explanation that fits 1–3 (global timing or caching side effects); (5) return VERDICT
   `CONFIRMED | REFUTED(<step, evidence>) | UNVERIFIED(<missing>)`, STEP_RESULTS (cmd, runs, failures, log path:line),
   ALTERNATIVE_TESTED, CONFIDENCE_BASIS." Transcribe into the ledger. CONFIRMED → write part B (mechanism, contributing
   factors, blameless statement). REFUTED → ledger note, round +1.
8. **Fix.** `mission-worker-high` (single-component fix) or `mission-builder` (crosses components, public contract,
   concurrency, data integrity) gets the CONFIRMED mechanism, owned paths, frozen list and "one change, no retries,
   sleeps, timeouts or catch-alls unless part B names an external transient". Each failed attempt → ledger entry;
   third failure → ESC-02 "question the design".
9. **Prove.** `mission-verifier` (tiered per PRF-01) fills P1–P12 in a clean worktree: red on parent, green on fix,
   `flake-runs.sh` tally, mechanism match, test-diff audit, suite, masked-bug check, recurrence plan. Verdict
   `PROVEN | NOT-PROVEN(<items>) | UNVERIFIED(<reason>)`; copy the red→green row into VERIFICATION §4.
10. **Sweep.** `mission-worker` (sweeper; `mission-worker-high` when hits need cross-component judgement) lists every
    hit with a disposition; `mission-reviewer` blind-samples ≥3 REFUTED hits (PRF-05). DEFERRED hits become T-NNN.
    State `SWEPT`.
11. **Convert.** `mission-builder` (distiller) fills parts C–D: D1 always; D2 control with self-test or "no control:
    <reason>"; D3 audit task in PLAN.md; D4 STATE F/R-entry via `memory_delta`; D5 inbox entry or "no lesson: <reason>";
    D6/D7 at L/XL. Orchestrator applies `memory-and-lessons.md` P7. State `CONVERTED`.
12. **Close.** `FIXED` when P1–P10 pass and no recurrence check applies; `FIXED-PENDING-LIVE` until PRF-07 evidence
    exists (gate `PENDING-LIVE`). Part E records the verdict and a fresh-context review. Archive the STATE O-entry with
    a pointer. Review of the fix diff follows `review.md` (BUG conditional).

Red-flag thoughts that send the investigation back to step 4: "quick fix now, investigate later" · "let me just try X"
· "probably X" · "add a retry" · "increase the timeout" · "skip this test for now" · "one more attempt" after two ·
"it passed 3 times, it's fixed".

## Scale by class (S/M/L/XL)

Size the *failure*, not the mission it occurs in (a failed gate inside an XL mission is usually S). Revise upward when
the repro budget runs out, a second cause appears or the mechanism crosses a contract.

| Class | Typical failure | Record and artefacts | Protocol depth | Lanes | Conversion |
|---|---|---|---|---|---|
| **S** | one behaviour, deterministic, known location, ≤1 file | inline record in the PR description (DBG-01 fields); no investigation file | plug → failing test first → fix → verifier red→green (stands in for the confirmer, DBG-33) → one-grep sweep; PRF-06 SHOULD | never | D1 only; at most one inbox line if it is a class |
| **M** | one component, or intermittent | `.mission/investigations/O-NNN.md` with ledger and P1–P12 | full protocol; differentials where an env difference exists; confirmer `mission-reviewer` | rarely (DBG-40) ≤3 | D1 + one of D2/D3; D5 only if LSN-03 holds |
| **L** | cross-component, prod-only, or multi-cause | investigation file + postmortem (parts B–E reviewed by a fresh context) | full protocol + differential environments + PRF-06 MUST + PRF-07 live recurrence check | when DBG-40 holds ≤4 | D1–D5 decided explicitly; audit task mandatory |
| **XL** | user-impacting incident, overlapping bugs, platform or toolchain | incident timeline + one O-id per cause (shared timeline) + per-cause ledgers + postmortem | mitigate first (step 0); every L rule; `mission-critic` confirmer for risky domains | ≤6, one per cause family | D1–D7 incl. an incident-drill row with automated proof + live injected fault |

Repro budgets (agent wall-clock): **S 30 min · M 2 h · L half a day**. Exhausted → deliverable becomes observability:
structured logging or tracing at component boundaries that emits the SIGNATURE, shipped behind a flag, a recurrence
query, record `UNREPRODUCED(<reason>)`, O-entry stays open. Speculative fixes ship only flagged (DBG-13). XL has no
repro budget before mitigation; after mitigation use L.

## Shape conditionals

- IF **BUG** is the mission shape ("find this deep annoying bug and fix it") THEN this file *is* the mission: Intake
  (DBG-01..04) → `REPRODUCED` → isolate → ledger (+ lanes) → `CONFIRMED` → fix → `PROVEN` → `SWEPT` → review (`review.md`
  BUG conditional) → `CONVERTED` → `FIXED | FIXED-PENDING-LIVE`. The spec is the repro plus `BUGFIX-SPEC.md` (M+) or the
  bug task card (S); no greenfield-style spec. Root cause is data corruption → add DAT; fix changes a public contract
  → add `published_api` and ask the human (ESC-03).
- IF **live_incident** THEN step 0 first; LI obligations of `shapes-and-scope.md`; investigate on the unmitigated build
  in non-prod; postmortem with a generic control before close.
- IF **intermittent** THEN measure p, amplify, prove with PRF-02. Quarantine only with an expiry and an O-id
  (`testing.md` E-5). Never retry-to-green.
- IF **GRN** (e.g. Swift iOS + Cloudflare backend) THEN every failed build gate gets a record at S-depth unless it
  recurs or crosses the contract. Cross-boundary failures (API works in the simulator, fails on device) default to M
  and run the simulator-vs-device and local-vs-preview differentials. Device-only surfaces stay
  `UNVERIFIED(DEVICE_REQUIRED)` until run on hardware.
- IF **FEA** in an existing product THEN a regression caught by existing tests is bisected against the feature branch
  base first. A pre-existing failure found along the way gets an O-id and a T-NNN but never blocks the feature.
- IF **MIG** (service extraction or consolidation) THEN debug parity failures differentially first: same recorded
  request replayed on old and new paths; diff responses, headers, side effects, timing. Env and config drift (bindings,
  compatibility dates, secrets) is the first hypothesis family. Every parity failure becomes a parity-inventory row plus
  a regression fixture.
- IF **WEB** THEN failures are mostly broken builds, links and factual errors: S-depth record; the conversion target is
  a check (link checker, citation verifier, build gate), not a ledger.
- IF **UPG** THEN bisect over dependency versions or lockfile commits as well as history; read changelogs for behaviour
  changes before own-code hypotheses; test removal of old workarounds (PRF-06).
- IF shape **PRF** (performance) or `performance_sensitive` regression THEN the repro is a benchmark with a numeric
  threshold and variance over ≥10 runs; `git bisect run` with the threshold script (old/new terms); iOS benchmarks run
  on device.
- IF **process failure** THEN use the PFX taxonomy; the fix is a control in the mission machinery (hook, preflight,
  gate, template field) and D1 is a hook self-test or an eval case in the skill's `evals/evals.json` via promotion.
- IF **unattended** (Routine or headless) THEN the investigation may run through local `PROVEN`, then ends in a draft
  PR on a `claude/` branch plus the record. Never merge or deploy. Checks needing credentials, devices or production
  queue `BLOCKED-HUMAN`.
- IF **SEC** crash triage or exploitability THEN route investigator and reset rungs to Opus 4.8 agents (never Fable for
  exploit reasoning); log any refusal or fallback as `CLASSIFIER_BLOCK`.

## Model routing

Reading logs and code is the cost driver: reading-heavy roles go to Sonnet agents, reasoning over compact ledgers to
Opus, Fable only for a hypothesis-space reset on small inputs. Scripts are rung 0 and need no model.

| Role | Agent (conventions §7) | Guard on the downgrade |
|---|---|---|
| Triage, failure-record author | `mission-worker` | orchestrator rejects a record missing DBG-01 fields (field check, no model) |
| Check-the-plug runner | `mission-checker` | every item has a command and output line; a missing line → re-run |
| Repro builder / minimizer | `mission-worker-high`; `mission-builder` for concurrency or platform-runtime bugs | gate is mechanical: repro exits non-zero at recorded p in the verifier's run |
| Log/trace extractor | `mission-scout` | verbatim quotes with `path:line`; orchestrator greps 2 quotes per extraction |
| Bisect / ddmin / differential driver | script, wired by `mission-worker` | bisect log attached; first-bad commit re-verified on it and its parent |
| Investigator, S with deterministic repro | `mission-worker-high` | 2 falsified rounds → `mission-builder` with the ledger |
| Investigator, default M+ | `mission-builder` | separate confirmer; ledger schema enforced by the orchestrator |
| Experiment lane (one hypothesis) | `mission-worker-high`; `mission-builder` for concurrency, memory or runtime/toolchain hypotheses | fixed return schema with raw output; confirmer re-runs the decisive experiment |
| Root-cause confirmer | `mission-reviewer`; `mission-critic` for money, auth, data integrity, concurrency | tier ≥ investigator; sees evidence, never transcripts; attempts refutation first |
| Fixer | `mission-worker-high` once CONFIRMED; `mission-builder` when the fix crosses components or touches a public contract | PRF-01..06; test-diff audit |
| Proof runner | `scripts/flake-runs.sh` run by `mission-verifier` (`mission-critic` for risky domains) | verifier re-derives n with `--dry-run`; cites the tally line |
| Sibling sweeper | `mission-worker` | `mission-reviewer` blind-samples ≥3 REFUTED hits; disagreement → full re-review |
| Distiller (parts C–D, postmortem) | `mission-builder`; `mission-strategist` for XL cross-mission retros | promotion check by `mission-verifier` in a fresh context (`memory-and-lessons.md` CMP-05) |
| Process-failure classifier | `mission-checker` | unclassifiable or two plausible classes → `mission-reviewer` |
| Hypothesis-space reset | `mission-strategist` | input = compact ledger + repro only; output = new hypothesis families and experiments, not a fix; max 2 with written reason; experiments still run on lower rungs |

Debugging ladder (specializes the conventions maker ladder; ESC-01 brief at every promotion):

```text
Rung 0  scripts: git bisect run · ddmin · differential runs · flake-runs.sh          always first where applicable
Rung 1  mission-worker-high  investigator   S failures with a deterministic, localized repro
Rung 2  mission-builder      investigator   default for M+; START HERE for concurrency, memory, auth, payments,
                                            data integrity, platform runtime, compiler/toolchain
Rung 3  mission-strategist   reset          after 2 rounds at rung 2 without SUPPORTED, ≥2 interacting causes, or
                                            confirmer REFUTED twice; compact ledger input; max 2 attempts
Rung 4  human                               ESC-03 triggers, or rung 3 exhausted
Promotion: 2 failed rounds per rung. Security-flavoured hunts: rung 3 = mission-strategist with Agent-tool model
override claude-opus-4-8; log any refusal/fallback as CLASSIFIER_BLOCK.
Degraded profile (no Fable): rung 3 runs on mission-builder with the reset brief.
```

## Anti-patterns

- **Theorizing before reproducing:** long causal essays from a stack trace; latching onto causes of past problems.
- **Shotgun fixing:** several changes at once, keep whatever turns green. Nobody can say which change mattered.
- **Retry-to-green:** CI reruns until green, then "flaky, moving on". Real bugs succeed 4 runs in 5.
- **Read-only theory fan-out:** agents each argue for a theory and "first to find evidence wins". You pay for
  narratives and still have to run the experiment.
- **Deleting negatives:** rewriting the ledger into a clean story; the next context re-tests falsified ideas.
- **Removing a workaround because "the root cause is fixed"** without re-running the failure class.
- **Single-cause tunnel vision:** forcing one root cause onto overlapping failures.
- **Wrong-environment proof:** simulator or local proof for a device or production bug.
- **Instance fixes without a sweep:** the same mechanism resurfaces in the next review round.
- **Weak proof:** "passed 3 times" for a 1-in-50 flake (needs 149); proof runs sharing state (warm DB, same simulator);
  the maker issuing its own CONFIRMED or PROVEN; a `/goal` evaluator "believing" a flake is fixed; expectations edited
  to match new output without a TEST-DISPUTE decision.
- **Lesson inflation and blame:** every bug becomes a rule; "be more careful with X"; prose where a lint, hook or
  constraint fits; generic tasks without an enumerable scope; unreviewed postmortems.
- **Cost traps:** raw logs in the orchestrator's context; starting a hunt on `mission-strategist` "because it is hard"
  instead of bisecting; lanes without the DBG-40 precondition; one model turn per proof run; escalating by re-asking a
  bigger model without the ledger.
- **Ceremony creep:** postmortem, drills and lanes for an S bug; lesson candidates for typos; drill rows for
  non-operational classes. Scale by class is a ceiling, not a floor.

## Unverified harness details

| Detail | Status | Safe fallback |
|---|---|---|
| Tool flags in the hard-bug class table (race detectors, test shuffle/repeat flags, Xcode test iteration, Instruments CLI) | not verified per stack | probe with `--help` at setup; record the working command in `CONTEXT.md` before relying on it |
| `/goal` evaluator model can be set to Sonnet 4.6 for `/goal` alone | not verified; default evaluator reads only the transcript and defaults to Haiku | never a gate; proof lives in `flake-runs.sh` output checked by a verifier or Stop-hook script |
| `isolation: worktree` cleanup for experiment lanes (caveats when spawning from non-primary worktrees) | reported by the swarms lane, not re-verified here | lanes copy evidence logs into `.mission/logs/O-NNN/` before return; orchestrator runs `git worktree list` and removes lane worktrees only after the ledger cites the copies |
| Stop hook overridden after 8 consecutive blocks | documented, not re-tested | proof gates are also re-run by the verifier; a Stop-hook override is logged as `PREMATURE_DONE` risk |
| Built-in "debugger" sub-agent | not in the built-in sub-agent list | use roster agents only |
| Per-model "memory progression" stage numbers and "model distills rules unprompted" claims | unverified | do not cite; distillation runs through template parts C–D with a verifier |
| Silent sticky Fable→Opus fallback | reported by sibling lanes, not verified here | log the model of every spawn; unexpected model → `CLASSIFIER_BLOCK` record |
| Independence of repeated runs (PRF-02 arithmetic) | assumption, not a fact about any suite | reset state per run; double n when reset is partial; amplify rather than trusting a large n over shared state |

## Evidence

1. https://sre.google/sre-book/effective-troubleshooting/ — hypothetico-deductive troubleshooting, pitfalls.
2. https://sre.google/sre-book/postmortem-culture/ — blameless postmortems, follow-up actions, review.
3. https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues — overlapping causes, masking workaround,
   minimized reproducer, differential backend.
4. https://how.complexsystems.fail/ — multiple contributors, limits of "root cause".
5. https://www.cs.purdue.edu/homes/xyzhang/fall07/Papers/delta-debugging.pdf — ddmin.
6. https://git-scm.com/docs/git-bisect — `bisect run` exit codes, old/new terms.
7. https://arxiv.org/abs/2510.20270 — ImpossibleBench: agents modify tests and overload operators.
8. https://arxiv.org/abs/2511.00197 — failed agent trajectories are longer and higher-variance; localisation is not
   the bottleneck.
9. https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html — flaky-test handling.
10. https://developer.apple.com/documentation/xcode/testing-in-simulator-versus-testing-on-hardware-devices — simulator
    vs device differences.
11. https://developers.cloudflare.com/workers/reference/how-workers-works/ — isolate lifetime and eviction.
12. `arcwell/docs/product/arcwell-spec.md:1712-1722` (mitigate first, closure needs deployed proof and recurrence check)
    and `arcwell/docs/operations/incident-drills.md:3-21` (automated proof + live drill per failure class). Source
    report: `research/mission-skill/08-failure-investigation-lessons.md`.
