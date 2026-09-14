# O-<NNN> · <symptom, one line> · state: <OPENED | REPRODUCED | UNREPRODUCED(<reason>) | CONFIRMED | PROVEN | SWEPT | CONVERTED | FIXED | FIXED-PENDING-LIVE>

<!-- Template: skills/mission/templates/investigation.md → .mission/investigations/O-<NNN>.md (M+). Rules:
     references/debugging.md (DBG, PRF, LSN, PFX, ESC). Fill parts in order; a part is filled only when its state is
     reached. Nothing skips a state. Append-only: never delete FALSIFIED hypotheses, failed fix attempts or refuted
     verdicts. Every result cites a log path:line under .mission/logs/O-<NNN>/. The orchestrator writes this file from
     sub-agent returns; the verifier writes part P in its own report and the orchestrator transcribes it verbatim.
     STATE.md keeps only a 2-line O-entry pointing here.

     S failures: no file. Paste this block into the PR description instead:
       O-<NNN> · <symptom verbatim> · expected <…> · observed <…> · env <commit, runtime, platform>
       Plug: <items + command → exit → line> · Repro/test: `<path::name>` red on <parent sha> → green on <fix sha> (verifier)
       Mechanism: <file:line + one line> · Sweep: `<rg query>` → <k> hits, <dispositions> · D1: <test path> · Lesson: <no lesson: reason | L-NNN>
-->

Kind: <product-bug | process-failure (class <PREMATURE_DONE | GAMED_TEST | SYMPTOM_PATCH | LOST_CONTEXT | WRONG_ASSUMPTION | TOOL_MISUSE | SPEC_GAP | CLASSIFIER_BLOCK | MISSING_ENV | FLAKE_MISREAD | THRASHING | SWARM_MISALIGNMENT | SCOPE_CREEP>)>
Scale: <S | M | L | XL> · Hard-bug class: <row(s) from references/debugging.md § Hard-bug classes>
Mission: <.mission/STATUS.md task T-NNN | gate | none> · Severity: <blocks merge | blocks milestone | degraded | cosmetic>
Current rung: <0 scripts | 1 mission-worker-high | 2 mission-builder | 3 mission-strategist | 4 human> · Round: <n> · Fix attempts: <n>/3
Repro budget: <30 min | 2 h | half a day> · used: <…> · Turn/token budget for this rung: <…> · used: <…>

## A. Record (filled at OPENED, before touching code)

- Detected by: <test | CI job <name> | user report | canary | review | agent gate> at <YYYY-MM-DD HH:MM UTC>
- First bad seen: <sha | deploy id | date | unknown>
- Symptom (verbatim): <error text | log line with path:line | screenshot path + pixel box>
- Expected: <…>
- Observed: <…>
- Environment fingerprint: commit <sha> · runtime <versions> · config hash <…> · platform <simulator <model/OS> | device <model/OS> | local | preview | prod> · flags/bindings <…>
- Blast radius: <users, requests, records affected | unknown (say how it will be measured)>
- Mitigation: <none | revert/flag-off/retry/manual recovery at <UTC>, by <who>, human checkpoint D-NNN> — does NOT resolve this record
- Linked: STATE O-entry <O-NNN> · BUGFIX-SPEC <.mission/SPEC.md BUG-<n> | none> · issue <url | none>

Check the plug (DBG-03; `mission-checker`):

| # | Check | Command | Exit | Salient line | OK? |
|---|---|---|---|---|---|
| 1 | Right commit or deployment under test | `<git rev-parse HEAD; deploy id query>` | <0> | <"…"> | <yes/no> |
| 2 | Build fresh, no stale artefacts | `<clean build command>` | | | |
| 3 | Env vars, secrets, bindings present (names only, never values) | `<env check>` | | | |
| 4 | Failing test actually executes (not skipped, no `.only`, right filter) | `<runner list-tests command>` | | | |
| 5 | Correct cwd, branch, target environment | `<pwd; git branch --show-current>` | | | |
| 6 | Exit codes not masked by pipes or wrappers | `<command with set -o pipefail>` | | | |

Plug finding: <none | item # → fixed in <sha> → failure gone? yes (close at S-depth) | no (continue)>

## B. Investigation summary (filled at CONFIRMED)

- Mechanism (confirmed): <one paragraph: condition → causal chain → symptom; file:line> · H-id: <H-NNN> · confirmer verdict: <CONFIRMED by <agent> on <date>, ledger § H-NNN>
- Root-cause intervention: <smallest change that toggles the failure both ways>
- External transient? <no | yes: <evidence>; retries/timeouts in the fix are justified by this line>
- Speculative fix (UNREPRODUCED only): <no | yes: monitoring follow-up T-NNN, recurrence query `<…>`>
- Contributing factors: detection gap <…> · test gap <…> · process gap <…> · masking workaround <none | path + removal test result>
- Timeline (L/XL, UTC): introduced <…> · detected <…> · mitigated <…> · reproduced <…> · confirmed <…> · fixed <…> · live-verified <…>
- Blameless statement: "The system lacked <mechanism>, so <failure> could <happen | ship | go undetected>."

## Ledger · O-<NNN>

Repro: `<tests/regression/O-<NNN>-repro.<ext>>` · prints `SIGNATURE: <…>` · frozen at <sha> (manifest updated: yes/no)
Baseline: <deterministic | p = <failures>/<runs> (≥5 failures) · amplification: <none | STRESS=<n>, injected latency <…>>>
REPRODUCED gate: <verifier <agent> · command → exit <n> → "SIGNATURE: …" · log <path> | UNREPRODUCED(<reason>)>
Minimization: <ddmin result | steps stripped | not needed (<why>)>

Isolation (DBG-20/21; record why a technique was not applicable):
- Bisect: <`git bisect run <repro>` → first bad <sha>; parent <sha> passes · log .mission/logs/O-<NNN>/bisect.txt | n/a: <no known-good revision>>
- ddmin: <input/config reduced from <n> to <k> elements · log <path> | n/a: <input already minimal>>
- Differential: <good env <…> PASS <k>/<n> vs bad env <…> FAIL <k>/<n> · fingerprint diff: <…> | n/a: <no working environment>>
- Boundary instrumentation: <boundaries logged> · Heisenberg check: <still fails at ≈p: <k>/<n> | vanished → switched to <…>>

Statuses: OPEN (untested; may carry `assigned: <lane>`) · SUPPORTED (prediction held once; not a root cause) ·
FALSIFIED (prediction failed; never deleted) · CONFIRMED (two-way intervention by a separate confirmer) ·
INCONCLUSIVE (not discriminating or not runnable here; reason + what would test it).

### H-<NNN> · <statement>
- Layer: <code | data | config/env | dependency | timing | platform> · Proposed by: <agent, round n> · Status: <OPEN | SUPPORTED | FALSIFIED | CONFIRMED | INCONCLUSIVE> (round <n>)
- Mechanism: <how this would produce the symptom>
- Prediction: if true, then <observable> under <condition>
- Experiment: `<command>` · one change vs baseline: <…> · runs: <n>
- Expected if TRUE: <…> · Expected if FALSE: <…>   (both written before running)
- Result: <failures>/<runs> · "<verbatim line>" (<log path:line>)
- Conclusion: <status + one line; what this constrains for other hypotheses>
- Confirmer (only for the leading SUPPORTED): <CONFIRMED | REFUTED(<step, evidence path:line>) | UNVERIFIED(<missing>)> · <agent> · <date> · alternative tested: <…>

### H-<NNN> · <statement>
- Layer: <…> · Proposed by: <…> · Status: <…>
- Mechanism: <…>
- Prediction: <…>
- Experiment: `<…>` · one change: <…> · runs: <n>
- Expected if TRUE: <…> · Expected if FALSE: <…>
- Result: <…> (<log path:line>)
- Conclusion: <…>

### H-<NNN> · <statement>
- Layer: <…> · Proposed by: <…> · Status: <…>
- Mechanism: <…>
- Prediction: <…>
- Experiment: `<…>` · one change: <…> · runs: <n>
- Expected if TRUE: <…> · Expected if FALSE: <…>
- Result: <…> (<log path:line>)
- Conclusion: <…>

<!-- ≥3 hypotheses across different layers before testing the favourite (DBG-34). Add H blocks as needed. -->

### Fix attempts (each is an experiment; 3 failures → ESC-02 "question the design")
| # | Commit | Agent | Change (mechanism addressed) | Result (command → exit → line) | Status |
|---|---|---|---|---|---|
| 1 | <sha> | <agent> | <…> | <…> | <failed / candidate> |

### Rounds and escalations
| Round | Rung / agent | Hypotheses tested | SUPPORTED? | Ledger changed? | Escalation (brief path, reason) |
|---|---|---|---|---|---|
| 1 | <2 · mission-builder> | <H-NNN, H-NNN> | <yes/no> | <yes/no> | <none / .mission/lanes/O-<NNN>/escalation-r1.md · 2 rounds without SUPPORTED> |

## P. Proof of fix (filled by the verifier at PROVEN; also referenced from VERIFICATION §4)

Verifier: <mission-verifier | mission-critic> · worktree: <clean path at <fix sha>> · date: <YYYY-MM-DD>
α: <0.05 | 0.01 (money, auth, data integrity, concurrency)> · state reset between runs: <how | partial → n doubled>

- [ ] **P1 Repro frozen:** `<repro path>` unchanged since <freeze sha> · `git log --oneline <freeze sha>..<fix sha> -- <repro path>` → <empty> · manifest check → <exit 0>
- [ ] **P2 RED on parent:** at `<fix sha>~1`: `<repro command>` → exit <≠0> → "SIGNATURE: <matches part A>" · log <path>
- [ ] **P3 GREEN on fix:** at `<fix sha>`: same command → exit 0 · log <path>
- [ ] **P4 Intermittent proof (skip only if deterministic):** baseline p = <failures>/<runs> · `.mission/bin/flake-runs.sh --p <p> --alpha <α> <--no-reset if partial> --dry-run` → n = <n> · `.mission/bin/flake-runs.sh --p <p> --alpha <α> <--no-reset> -- <repro command>` → "PASS <n>/<n>" · log <path>
- [ ] **P5 Mechanism match:** diff touches <file:line from the CONFIRMED H-NNN> · symptom-only patterns absent (catch-and-ignore, blanket retry, timeout bump, sleep, disabled feature, special-cased input) OR justified by part B external transient · diff size proportional to the mechanism (drive-by changes split to T-NNN)
- [ ] **P6 Test-diff audit clean:** `.mission/bin/test-diff-grep.sh --base <parent sha> --head <fix sha>` → exit 0 · no deleted, skipped, weakened or special-cased tests · no harness, timer, equality or evaluator edits (or ledger justification) · test count <before> → <after> (not decreased)
- [ ] **P7 Suite green in clean worktree:** `<suite command>` → exit 0 · <passed/failed/skipped counts> · log <path>
- [ ] **P8 Masked-bug check:** prior workarounds for this symptom: <list with path:line | none found by `<query>`> · each <removed and suite re-run → exit <n> | kept because <reason>>
- [ ] **P9 Sibling sweep:** pattern `<rg | ast-grep | lint query>` → <k> hits · each dispositioned in part C sweep table · bypass variants enumerated: <…> · blind sample of ≥3 REFUTED hits by `mission-reviewer`: <agree | disagree → full re-review>
- [ ] **P10 Regression test (D1):** `<path::name>` is the repro or a smaller test with its own RED on parent / GREEN on fix evidence · frozen: <yes>
- [ ] **P11 Recurrence check (deployed systems):** <canary | scheduled check | log query on SIGNATURE `<query>`> · status <not applicable | pending → record state FIXED-PENDING-LIVE, gate PENDING-LIVE | ran <date> → evidence <path>>
- [ ] **P12 Unavailable proof:** <none | UNVERIFIED(<DEVICE_REQUIRED | MISSING_<X> | PROD_ONLY>) + BLOCKED-HUMAN item in STATUS human queue> — never green

Verdict: <PROVEN | NOT-PROVEN(<failed items>) | UNVERIFIED(<reason>)>

## C. Generalization (filled at CONVERTED; distiller `mission-builder`)

- Mechanism class (abstract, no project names): <e.g. "request-scoped data held in process-global state">
- Where else can this class occur? (enumerable scope): <e.g. "every Worker module with module-scope `let`"; "every webhook or queue handler">
- Bypass variants of the mechanism: <aliases, re-exports, reflection, other entry points | none>
- Could a machine prevent the whole class? <yes: <lint | hook | type | schema constraint | CI check> → D2 | no, because <reason>>
- Recurrence / cost: <first occurrence | also seen in <O-NNN, other mission>> · time lost <…> · user impact <…>
- Evidence the generalization holds beyond this case: <second instance | doc source URL + quote | none yet → confidence low>

Sibling sweep (PRF-05; dispositions per conventions):

| # | path:line | Instance of the mechanism? | Disposition | Evidence / task |
|---|---|---|---|---|
| 1 | <src/…:42> | <yes / no> | <FIXED / REFUTED / DEFERRED> | <commit + test · or: not affected because <evidence> · or: T-NNN, owner, milestone> |

## D. Outputs (each line has an owner and a completion check)

| ID | Output | Owner | Completion check | Status |
|---|---|---|---|---|
| D1 | Regression test (ALWAYS): `<path::name>` · RED on <parent sha>, GREEN on <fix sha> · frozen | <test author agent> | P2/P3/P10 evidence in part P | <done / pending> |
| D2 | Prevention control: <lint rule / PreToolUse hook / type / DB or schema constraint / CI check> at `<path>` — or "no control: <reason>" | <agent> | self-test `<command>` rejects a seeded bad example → exit <≠0> | <done / T-NNN / n/a> |
| D3 | Generic audit task T-NNN "<Audit / Migrate / Instrument> all <class scope> for <mechanism>" in PLAN.md | <agent> | scope query `<rg or ast-grep query>` → every hit has a test or disposition · size <S / M> | <open / done / n/a> |
| D4 | STATE entry via memory_delta: <F-NNN (root-cause fact, evidence = D1 red→green) / R-NNN (Applies when <…> · Instances <O-ids> · Counter-cases <…>)> | orchestrator | entry present; `memory-lint.sh` → exit 0 | <done / pending> |
| D5 | Lesson candidate L-NNN in `.mission/LESSONS-INBOX.md` ONLY IF mechanism CONFIRMED ∧ class general ∧ (count ≥2 ∨ cost ≥1 day ∨ user-visible/production) ∧ D2 impossible or insufficient — else "no lesson: <reason>" | orchestrator from distiller draft | inbox entry has Applies when, Does not apply when, Why not a control, Evidence | <candidate / no lesson: <reason>> |
| D6 | Skill known-failure-mode (promotion only, at retro): target `references/lessons.md § <group>` · eval case `evals/evals.json` id <n> | distiller + `mission-verifier` | promotion criteria a–h (`memory-and-lessons.md` CMP-05) | <n/a / proposed / promoted> |
| D7 | Incident drill (XL, operational classes): drill row with automated proof + live injected fault | <agent> | drill run evidence <path> | <n/a / pending / done> |

Process failures: D1 = hook self-test or eval case; D2 = the class control from `references/debugging.md` § Process
failures (mandatory when the class has recurred twice).

## E. Close

- Proof verdict: <PROVEN | UNVERIFIED(<reason>)> (part P) · VERIFICATION row: <.mission/verification/VERIFICATION-<M>.md §4 | PR description>
- Final state: <FIXED | FIXED-PENDING-LIVE (recurrence check <…> due <date>)> · gate in STATUS.md: <PASSED | PENDING-LIVE>
- Workarounds kept (P8) and why: <…>
- Postmortem review (L/XL, fresh context): <agent · date · open questions | n/a>
- STATE O-entry archived with pointer: <yes, <date>>
- Open follow-ups: <T-NNN list | none>
