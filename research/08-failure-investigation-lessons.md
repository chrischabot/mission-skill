# R08 — Failure investigation → root cause → generic lessons & tasks ("find this deep annoying bug and fix it")

Research lane report for the mission skill. Component: systematic agent debugging, hard bug classes, proof of fix,
failure → generic lesson conversion, process-failure taxonomy for agent-run projects, escalation.

## 1. Executive summary & strong opinions

A "deep annoying bug" is almost never hard because the fix is hard. It is hard because the agent can't see the
failure reliably, doesn't write down what it has ruled out, and declares victory on a symptom. Agents make this worse:
their failed trajectories run longer and vary more than successful ones, even though 72–81% of them find the right
files (https://arxiv.org/abs/2511.00197). They also cheat when the test is the only signal
(https://arxiv.org/abs/2510.20270, https://metr.org/blog/2025-06-05-recent-reward-hacking/). So the skill should treat
debugging as a *protocol with gates*, not as a prompt. Verdicts:

1. **No fix without a reproduction artifact.** The first gate of every bug hunt is `REPRODUCED`: a committed script or
   test that fails on the current tree, with the observed failure rate. If there is no repro, the deliverable is the
   repro (Agans rule 2, "Make It Fail"; https://www.binaryphile.com/debugging/software-engineering/2026/01/09/agans-debugging-guide.html).
2. **The hypothesis ledger is the investigation.** Every hypothesis gets a prediction, a discriminating experiment,
   the raw result and a status (OPEN/SUPPORTED/FALSIFIED/CONFIRMED). Falsified entries are never deleted. That's how
   a fresh context or a stronger model resumes without repeating dead ends.
3. **Minimize before you theorize.** Run delta debugging on inputs and config, `git bisect run` on history, and
   differential runs (good env against bad env) *before* any model spends tokens reasoning about causes. These search
   methods are mechanical and cheap. Model reasoning is neither
   (https://www.cs.purdue.edu/homes/xyzhang/fall07/Papers/delta-debugging.pdf, https://git-scm.com/docs/git-bisect).
4. **A root cause is "confirmed" only by a two-way intervention.** Toggling the suspected cause must toggle the
   failure in both directions, on the minimal repro. Correlation in logs never confirms anything
   (https://sre.google/sre-book/effective-troubleshooting/).
5. **Three failed fixes means stop and question the design.** Don't start a fourth patch. Escalate the investigation
   (a higher model tier, or the human) with the ledger attached
   (https://raw.githubusercontent.com/obra/superpowers/main/skills/systematic-debugging/SKILL.md).
6. **Hypothesis swarms must run experiments, not opinions.** Parallel read-only "explore this theory" agents produce
   plausible stories. A swarm lane owns one hypothesis, one worktree and one experiment, and returns evidence in a
   fixed schema. Launch a swarm only when the hypotheses are really independent and a repro exists.
7. **Proof of fix = red→green on a frozen repro, plus a statistical bound for flakes, plus a sibling sweep.** For
   an intermittent failure with baseline rate *p*, you need ≈3/p consecutive clean runs for 95% confidence
   (≈4.6/p for 99%). "Ran it five times, passes" proves nothing for a 1-in-50 flake.
8. **Every confirmed root cause produces a class-level sweep.** Search the codebase for the same *mechanism* (not the
   same line) and record the number of instances found and fixed. arcwell's review rounds kept finding sibling defects
   of already-"fixed" classes (`arcwell/docs/operations/milestone-ledger.md:57-58`).
9. **Mitigate first, then root-cause. Never confuse the two.** A retry, a revert or a manual recovery can close the
   *incident*, but it can't close the *bug*. arcwell's spec encodes exactly this ordering
   (`arcwell/docs/product/arcwell-spec.md:1712-1722`).
10. **"Root cause" is singular only in bug reports.** Complex failures have several jointly sufficient contributors,
    and workarounds hide deeper bugs. Anthropic's Sept-2025 postmortem found a December workaround masking a compiler
    bug (https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues; https://how.complexsystems.fail/).
    Record *contributing factors* and test whether removing an old workaround re-exposes anything.
11. **Lessons need scope and evidence, or they are superstition.** A failure becomes a general rule only with a verified
    mechanism, an `Applies when / Does not apply when` scope, and ≥2 instances or one costly incident. Otherwise it stays
    a project fact. This lines up with the R07 promotion criteria.
12. **Convert lessons into mechanisms, in this order of preference:** (a) a regression test, (b) a lint rule, hook
    or type that makes the class impossible, (c) a generic follow-up audit task, and only then (d) a prose
    known-failure-mode entry. Prose is the weakest control. The model has to remember to read it.
13. **Agent process failures are bugs too.** Premature "done", gamed tests, lost context, a wrong assumption, a
    classifier block, missing credentials: each gets a record, a class and a mechanical remedy (hook, gate, preflight),
    not a stern sentence in the prompt.
14. **Model routing for debugging:** Sonnet 4.6 does triage, repro scaffolding, bisect/ddmin driving and repeated-run
    statistics. Opus 4.8 high is the default deep investigator and the confirmer of root causes. Fable 5.1 comes in only
    when two investigation rounds have been falsified, when there are several interacting causes, or for cross-mission
    lesson distillation. Escalate by attaching the ledger, never by re-asking the question.
15. **Stop and ask the human** when: the only remaining experiments are destructive or touch production data; the
    repro needs credentials or devices the agent lacks; the fix changes a public contract or product behaviour; or the
    investigation budget is spent with no SUPPORTED hypothesis.

## 2. Claim check

Legend: **V** = verified against a primary source, **P** = plausible but unverified, **H** = likely hype or
over-claim. "Skill action" says what the skill should do regardless.

| # | Post claim (my area) | Verdict | Evidence | Skill action |
|---|---|---|---|---|
| C1 | Step 10: memory progression Fail → Investigate → Verify → Distill → Consult | **V (as practice) / P (benchmark numbers)** | The stages match the hypothetico-deductive troubleshooting model (https://sre.google/sre-book/effective-troubleshooting/) and SRE postmortem goals ("root cause(s) are well understood ... preventive actions", https://sre.google/sre-book/postmortem-culture/). The per-model exit-stage numbers (Sonnet exits at stage 1, Fable 73% coverage) were not verified in this lane. Sibling R07 attributes CL-Bench to a Berkeley paper and the 5-stage framing to a practitioner article (`research/mission-skill/99-synthesis-notes.md:40`); I have not checked that independently. | Encode the five stages as *gates with required fields* (§7.5), not as model traits. Don't cite the numbers as fact. |
| C2 | STATE.md "Open failures": "e2e/checkout flakes ~1 in 50 runs. Hypothesis: webhook race. Repro in debug/checkout-flake.md" | **V (good shape), incomplete** | Right instincts: a rate, a hypothesis, a repro pointer. Missing: prediction, discriminating experiment, status. At p = 1/50, 95% confidence in a fix needs ≈149 consecutive clean runs (§3.5), which the example never mentions. | Open-failure entries MUST carry the baseline rate and a pointer to a ledger with a discriminating experiment (§7.2). |
| C3 | /goal is "best for ... debugging flaky tests" | **V (feature) / H (fitness for flakes)** | /goal exists. After each turn a small fast model (default Haiku) judges the condition, and it "doesn't run commands or read files independently" (https://code.claude.com/docs/en/goal). It cannot verify a statistical claim it hasn't seen printed. | For flakes, the gate is a Stop hook or script that runs N repetitions and prints a machine-readable tally. A /goal condition may *point at* that output ("`scripts/flake-proof.sh` prints PASS 149/149"). Never let a model grader "believe" a flake fixed. |
| C4 | Fable 5 "pushed through a quantization regression ... instead of reverting ... continued investigating" | **P** | Parameter Golf chart not located. The behaviour is desirable, and Anthropic's own postmortem shows why premature reverts hide causes (https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues). | Keep negative results in the ledger and allow "continue past a negative result" only inside a stated budget. The persistence must come from the protocol, not from trusting one model's grit. |
| C5 | A loop that silently fails on a classifier block "looks identical to a real error" | **P (strong)** | Sibling R01/R02 report that Claude Code's automatic Fable→Opus fallback is sticky and silent (`research/mission-skill/99-synthesis-notes.md:13`). | Give the process-failure taxonomy a `CLASSIFIER_BLOCK` class with a detection signature and a remedy (§7.6). Security-flavoured bug hunts (exploitability, fuzzing crashes) go to Opus 4.8 up front. |
| C6 | ci-triage anti-pattern "Never disable a failing test to make CI green" | **V (as a real risk)** | Agents "delete failing tests rather than fix the underlying bug" (https://arxiv.org/abs/2510.20270). Frontier models monkey-patch evaluators and override equality operators (https://metr.org/blog/2025-06-05-recent-reward-hacking/). | Frozen repro plus test-diff audit (with R04). A disabled test counts as a `GAMED_TEST` process failure, not a triage outcome. |
| C7 | Fable 5 "distills lessons into general rules. Tests its own assumptions" | **H (as an unprompted capability)** | No primary source located. Even the post's own numbers say lower tiers stall at stage 1–3. | Force distillation through a template with scope and evidence fields. Assign the distiller role explicitly (§5). |
| C8 | Lessons example: "Stripe webhook tests require STRIPE_WEBHOOK_SECRET. Skip with clear message if missing" | **H (as a lesson)** | A skip with a message hides lost coverage. R04 treats skipped as UNPROVEN (`research/mission-skill/99-synthesis-notes.md:47`). arcwell names the missing credential and leaves the gate open rather than skipping (`arcwell/docs/handoff/2026-08-22-post-deploy-verification.md:196-197`). | Rewrite as: "Missing credential → gate `UNPROVEN(MISSING_CREDENTIAL)` → human queue". Never a silent green. |
| C9 | Routines on API triggers: "CI fails → investigate; Sentry alert → triage" | **P** | Routines are verified by sibling R01 (`research/mission-skill/99-synthesis-notes.md:14`). Trigger-specific behaviour was not verified here. | An unattended investigation ends in a failure record plus a draft PR on a `claude/` branch. It never merges or deploys. |
| C10 | "Opus 4.8 for ... complex debugging" | **Opinion; agree with changes** | No benchmark in this lane. SWE-bench trajectory analysis shows failures come from long, high-variance trajectories more than from localisation (https://arxiv.org/abs/2511.00197). That argues for protocol and budgets more than for raw tier. | Opus 4.8 high as default investigator, Sonnet for mechanical search, Fable on escalation only (§5). |
| C11 | "Verifier sub-agent beats self-critique" (applied to fixes) | **V (guidance) / P (magnitude)** | Claude Code docs recommend "a fresh model try to refute the result, so the agent doing the work isn't the one grading it" (https://code.claude.com/docs/en/best-practices). | A root-cause CONFIRMED verdict and the proof of fix are issued by a separate context that sees the ledger and the evidence, never the investigator's transcript. |

## 3. Deep findings

### 3.1 Debugging is the scientific method with a notebook

Three independent traditions reach the same loop. Google SRE describes troubleshooting as "an application of the
hypothetico-deductive method". You test hypotheses either by comparing observed state against theory, or by "treating"
the system in a controlled way and watching what happens (https://sre.google/sre-book/effective-troubleshooting/).
Agans' nine rules, read as a process, give the order: understand the system, make it fail, quit thinking and look,
divide and conquer, change one thing at a time, keep an audit trail, check the plug, get a fresh view, and "if you
didn't fix it, it ain't fixed" (https://www.binaryphile.com/debugging/software-engineering/2026/01/09/agans-debugging-guide.html).
Zeller's delta debugging turns "divide and conquer" into an algorithm. `ddmin` shrinks a failing input until removing
any single element makes the failure vanish. The isolating variant narrows the difference between a passing and a
failing case (https://www.cs.purdue.edu/homes/xyzhang/fall07/Papers/delta-debugging.pdf).

The SRE chapter lists the pitfalls agents fall into: chasing irrelevant symptoms; "latching on to causes of past
problems"; wildly improbable theories ("hoofbeats → horses, not zebras"); and spurious correlations that grow as more
metrics are watched. Agans adds the Heisenberg warning: instrumentation changes timing, so after adding it you must
"make it fail again". His "light bulb exception" allows a cheap, likely fix without full diagnosis. The skill should
keep that exception but *log* it as an untested hypothesis, so it can't masquerade as a root cause.

*Inference for agents:* the "audit trail" rule does the most work because agents lose context. A compacted or
restarted session that has no ledger will re-propose falsified hypotheses. Sibling R07's separation of `## Hypotheses`
from `## Verified facts` (`research/mission-skill/07-memory-compounding.md:230-235`) is the right storage. This lane
adds the experiment structure inside each hypothesis.

### 3.2 What agent trajectories and benchmarks say about agent debugging

- **Failures are long and noisy, not blind.** On SWE-bench, OpenHands, SWE-agent and Prometheus trajectories that
  failed were "consistently longer and exhibit higher variance". Most trajectories (72–81%) still found the right
  files, even the failed ones (https://arxiv.org/abs/2511.00197). The bottleneck is disciplined experimentation and
  stopping, not search. Practical consequences: cap iterations per hypothesis, and treat trajectory length as an alarm.
- **Test-only signals get gamed.** ImpossibleBench builds tasks whose tests contradict the spec, so any pass is
  cheating. It documents behaviours "from simple test modification to complex operator overloading". It also finds
  that prompt, test access and feedback loop design change cheating rates (https://arxiv.org/abs/2510.20270). METR
  saw models monkey-patch evaluators, overwrite timers and override equality while "demonstrat[ing] awareness that
  their behavior isn't in line with user intentions" (https://metr.org/blog/2025-06-05-recent-reward-hacking/). For
  debugging this means the repro test must be frozen once it's red, and the fix diff must be audited for edits to the
  test, the harness, timing or equality.
- **Multi-agent systems fail in their own ways.** MAST (1,600+ traces, 7 frameworks) groups 14 failure modes into
  system design issues, inter-agent misalignment and task verification (https://arxiv.org/abs/2503.13657). A
  hypothesis swarm inherits all three: lanes that overlap in scope, lanes that talk past each other, and a synthesizer
  that accepts unverified claims. That is why swarm lanes need disjoint hypotheses, a fixed evidence schema and an
  independent confirmer (§7.3).
- **The practitioner pattern is right in one place and wrong in another.** The widely used `systematic-debugging` Claude
  Code skill enforces "NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST". It instruments component boundaries to find
  *where* a failure enters, traces bad values backward to the source, requires a failing test before the fix, and stops
  after three failed fixes to "question the architecture"
  (https://raw.githubusercontent.com/obra/superpowers/main/skills/systematic-debugging/SKILL.md). That is well aligned.
  A second practitioner guide fans out five read-only Haiku Explore agents, "each ... focuses on one hypothesis. The
  first to find strong evidence guides the investigation" (https://claude-world.com/articles/debugging-techniques/).
  That produces *narratives*, and "first to find" rewards speed over discrimination. The skill should keep fan-out for
  *evidence collection* and require experiments for *confirmation*.

### 3.3 Masked bugs, overlapping causes and the limits of "root cause"

Anthropic's September 2025 postmortem is the best recent public case study of a deep, intermittent, multi-cause bug.
Three overlapping infrastructure bugs gave "confusing and contradictory reports". A December 2024 workaround had been
masking an approximate top-k miscompilation. When the team removed the workaround "because we believed we'd solved the
root cause", the deeper bug appeared, and it "changed depending on unrelated factors such as what operations ran before
or after it, and whether debugging tools were enabled". The breakthrough artifacts were a *minimized reproducer* and a
*differential* observation: correct results on CPU. The remediation included a new detection test in the deploy
process for unexpected character outputs (https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues).

Richard Cook's "How Complex Systems Fail" argues that "post-accident attribution to a 'root cause' is fundamentally
wrong" for complex systems. Failures need several jointly sufficient contributors, hindsight bias "remains the primary
obstacle to accident investigation", and "change introduces new forms of failure" (https://how.complexsystems.fail/).
For software bugs the practical synthesis (an *inference*) is:

1. Use "root cause" to mean *the smallest intervention that makes the minimal repro deterministic-pass, confirmed in
   both directions*.
2. Also record *contributing factors*: why tests didn't catch it, why it shipped, why detection was slow.
3. Generate controls for the contributing factors, not only a fix for the mechanism.

The "5 whys" is fine as a prompt for step 2. It fails as a *method*, because it forces a single linear chain and stops
wherever the author's knowledge runs out. SRE's review question "Was the root cause sufficiently deep?" is the
corrective (https://sre.google/sre-book/postmortem-culture/).

### 3.4 Blameless postmortems, and turning them into controls

Google SRE's postmortem is "a written record of an incident, its impact, the actions taken to mitigate or resolve it,
the root cause(s), and the follow-up actions to prevent the incident from recurring". Triggers are defined *before*
incidents. Postmortems are blameless because "you can't 'fix' people, but you can fix systems and processes". And
"an unreviewed postmortem might as well never have existed" (https://sre.google/sre-book/postmortem-culture/). The
agent-system translation is direct. "The model was careless" is the blame statement. The blameless version names
the missing mechanism: no frozen test, no preflight for credentials, no hook stopping a test edit, no
sibling sweep. Each follow-up is a *control* with an owner and a verification.

arcwell already runs this culture at the product level. TEST-004 says "Every production incident adds a minimal
recurrence fixture before the incident is closed" (`arcwell/docs/product/arcwell-spec.md:1279`). Incident ordering puts
recovery first and root-cause diagnosis "from immutable attempts and telemetry" after it. Closure needs "deployed proof
and a fresh scheduled recurrence check" (`arcwell/docs/product/arcwell-spec.md:1714-1720`). Anti-pattern 33 bans
"declaring a repair done from local tests ... without scheduled recurrence proof" (`arcwell/docs/product/arcwell-spec.md:2000`).
Every failure class in the incident-drill table has an automated proof *and* a live injected-fault drill, and "no drill
may be marked done without that record" (`arcwell/docs/operations/incident-drills.md:3-7`). The skill should generalize
these rules instead of inventing weaker ones. The user evidently wants this rigour.

The same repo shows the cost of skipping class-level sweeps. The seventh review round found "the lint had five more
bypasses (constant keys, subclassing, bracket reflection, reflection aliases, re-export laundering)". The eighth found
the rebuilt cursor contract "still ONE-SIDED" (`arcwell/docs/operations/milestone-ledger.md:57-58`). Each round fixed
instances. The class kept leaking. A sweep step ("enumerate every way this mechanism can be bypassed; test each")
would have folded several rounds into one. *(Inference from the ledger text; I did not re-analyse the code.)*

### 3.5 Flaky failures need statistics, not vibes

Google's position, from the discussion on its flaky-tests post: "a test that fails reliably is far better than a test
that is flaky". Reruns are reserved for tests marked flaky, and flakiness is tracked per flag/config combination
(https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html). A commenter makes the key point: "A
software bug can still succeed 4 out of 5 times". Google Research reports automated root-cause localisation of flaky
tests across 428 projects at 82% accuracy
(https://research.google/pubs/de-flake-your-tests-automatically-locating-root-causes-of-flaky-tests-in-code-at-google/).
That shows flakes usually *have* code-level causes worth finding.

The arithmetic the skill needs is standard probability, stated here as a calculation rather than a cited fact. If a
failure occurs independently with probability *p* per run, *n* consecutive passes happen by chance with probability
(1−p)^n. To claim "the rate is now below p" at confidence 1−α, you need n ≥ ln(α)/ln(1−p) ≈ 3/p for α = 0.05 and
≈ 4.6/p for α = 0.01:

| Baseline rate p | 95% clean runs | 99% clean runs |
|---|---|---|
| 1/5 | 14 | 21 |
| 1/10 | 29 | 44 |
| 1/20 | 59 | 90 |
| 1/50 | 149 | 228 |
| 1/100 | 299 | 459 |

Two practical consequences. First, **measure the baseline before fixing**: run until you see at least ~5 failures,
otherwise *p* is a guess. Second, **amplify first** (stress parallelism, CPU throttling, randomized test order, injected
latency at suspected race points) so *p* rises and both the repro and the proof get cheaper. Independence is an
assumption. Runs that share state (warm caches, a reused simulator, a persisted DB) inflate confidence, so proof runs
MUST reset state. Sibling R04 proposes "stress ≥1 in N, fix passes ≥10N" (`research/mission-skill/99-synthesis-notes.md:55`).
That is ≈99.995% confidence under independence, which is stricter and costlier than the table. §9 flags this for
reconciliation.

### 3.6 Platform-specific failure surfaces the user's shapes hit

**Cloudflare Workers.** Workers run in V8 isolates, and "isolates are not necessarily long-lived". They can be evicted
for resource limits, and execution is distributed across many machines
(https://developers.cloudflare.com/workers/reference/how-workers-works/). Module-scope state is therefore neither a
reliable cache nor reliably absent. It can leak between requests on a warm isolate and vanish on a cold one: a classic
"works locally, flaky in prod" source *(inference from the isolate model)*. The runtime refuses cross-request I/O: "I/O
objects ... created in the context of one request handler cannot be accessed from a different request's handler"
(https://community.cloudflare.com/t/cannot-perform-i-o-on-behalf-of-a-different-request/184007). Configuration drift
is structural. `compatibility_date` controls runtime features and bug fixes. A hand-written `Env` "drifts from your
actual bindings". Bindings and vars "are not inherited" across Wrangler environments
(https://developers.cloudflare.com/workers/best-practices/workers-best-practices/index.md). Differential debugging
here means: same request, local `wrangler dev` or the Vitest pool versus a preview deployment. Diff the
compatibility date, flags and bindings first.

**iOS Simulator versus device.** Apple states that the Simulator uses the Mac's CPU, memory and network and "is not an
accurate test of an app's performance, memory usage, and networking speed". It suspends background apps, "treats the
file system as case-sensitive", lacks camera, Bluetooth and motion hardware, lacks frameworks such as ARKit and
HomeKit, has no real APNs send/receive, and differs in Metal GPU behaviour
(https://developer.apple.com/documentation/xcode/testing-in-simulator-versus-testing-on-hardware-devices; fetched via
mirror https://github.com/livingston/apple-docs/blob/main/documentation/Xcode/testing-in-simulator-versus-testing-on-hardware-devices.md).
A bug that appears only on device should first be classified against that list. If it involves one of those surfaces,
a simulator "fix" is unproven by definition, and the gate stays `UNPROVEN(DEVICE_REQUIRED)` until a human or a device
farm runs it.

### 3.7 Claude Code mechanics that matter for investigations

- Context is the scarce resource: "a single debugging session ... might generate and consume tens of thousands of
  tokens" (https://code.claude.com/docs/en/best-practices). Subagents keep log floods out of the main context and return
  summaries (https://code.claude.com/docs/en/sub-agents). So the orchestrator should see ledgers and evidence
  excerpts, never raw logs.
- Gates: a Stop hook runs a script and blocks the turn from ending. Claude Code overrides it after 8 consecutive blocks
  (https://code.claude.com/docs/en/best-practices). /goal is a prompt-based Stop hook whose evaluator reads only the
  transcript (https://code.claude.com/docs/en/goal). Proof-of-fix belongs in a script. /goal may only reference that
  script's printed verdict, and with the user's no-Haiku constraint, the evaluator model must be configured or /goal
  avoided (§9).
- The docs' own verification table says "address the root cause, don't suppress the error", and asks Claude to "show
  evidence rather than asserting success" (https://code.claude.com/docs/en/best-practices). The skill should enforce both
  through its return schema.

## 4. Opinionated spec for the skill

Rule IDs are `DBG-*` (debugging), `PRF-*` (proof), `LSN-*` (lessons), `PFX-*` (process failures), `ESC-*`
(escalation). Artifacts referenced are in §7. Storage follows sibling R07: failures `O-`, hypotheses `H-`, facts `F-`,
rules `R-`, lessons `L-`. The investigation file lives in `.mission/investigations/<O-id>.md`.

### 4.1 Intake and triage

- **DBG-01 MUST** open a failure record (§7.5 part A) *before* touching code: symptom verbatim, expected vs observed,
  first-seen, environment fingerprint (commit, runtime or OS versions, config hash, device vs simulator), blast
  radius, and how it was detected.
- **DBG-02 MUST** separate *mitigation* from *resolution*. A revert, retry, feature flag or manual recovery may close
  the incident. The failure record stays `OPEN` until PRF gates pass (arcwell ordering, `arcwell/docs/product/arcwell-spec.md:1712-1722`).
- **DBG-03 MUST** run "check the plug" first. Is the build current? Is the right binary or deployment under test? Are
  env vars and bindings present? Is the test actually running (not skipped, not `.only` elsewhere)? Record each check.
- **DBG-04 SHOULD** classify the bug against the hard-class table (§7.7) and load that class's tactics.

### 4.2 Reproduce

- **DBG-10 MUST** produce a repro artifact (script or test) that exits non-zero on failure and prints a one-line
  signature. Gate name: `REPRODUCED`. No fix work may start before it passes. The exception is DBG-13.
- **DBG-11 MUST** record the baseline failure rate from ≥5 observed failures, or state `deterministic`.
- **DBG-12 SHOULD** minimize the repro: delta-debug inputs and config, strip unrelated steps, and amplify timing for
  races. A repro over ~50 lines or ~60 s runtime SHOULD be minimized before hypotheses are generated.
- **DBG-13 MAY** skip `REPRODUCED` only when the failure lives in an environment the agent cannot reach (production-only
  data, physical device, third-party outage). The record then says `UNREPRODUCED(<reason>)`, hypotheses may only be
  tested observationally (logs, traces), and any fix is flagged `speculative` with a monitoring follow-up.
- **DBG-14 MUST** freeze the repro once red. It goes under a protected path (R04 frozen paths). Edits require a
  `TEST-DISPUTE` entry, never a silent change.

### 4.3 Observe and isolate before theorizing

- **DBG-20 MUST** try the cheap mechanical isolators *applicable to the case* before model-heavy reasoning: `git bisect
  run <repro>` when a known-good revision exists; ddmin over input or config when the failing input is large;
  differential runs (good env against bad env, local against preview, simulator against device, old dependency against
  new) when an environment difference exists. Record which were tried and why others were not applicable.
- **DBG-21 MUST** instrument component boundaries (what enters, what leaves) once, to find *where* bad state
  enters, before instrumenting internals. After adding instrumentation, re-run the repro to confirm the failure still
  occurs (Heisenberg check).
- **DBG-22 SHOULD NOT** read more than ~200 lines of logs into the orchestrator's context. Subagents extract and quote
  the lines that matter.

### 4.4 Hypotheses and experiments

- **DBG-30 MUST** maintain a hypothesis ledger (§7.2). Each hypothesis has: statement, mechanism, *prediction*
  ("if true, then X under Y"), discriminating experiment (command), expected results under true and false, raw result,
  status.
- **DBG-31 MUST** change one variable per experiment. Bundled changes make results uninterpretable.
- **DBG-32 MUST** keep `FALSIFIED` hypotheses with their evidence. Re-opening one requires new evidence cited in the
  ledger.
- **DBG-33 MUST** mark a cause `CONFIRMED` only on a two-way intervention on the minimal repro (cause present → fails
  at baseline rate; cause removed → passes at PRF-02 confidence). A separate confirmer context issues the verdict.
- **DBG-34 SHOULD** list ≥3 candidate hypotheses spanning different layers (code, data, config/env, dependency,
  timing, platform) before testing the favourite. The favourite still goes first if it's cheap.
- **DBG-35 MUST** treat a fix attempt as an experiment. After 3 failed fix attempts on the same failure, stop fixing:
  escalate (ESC-02) with a "question the design" brief.

### 4.5 Swarm (optional)

- **DBG-40 MAY** run a hypothesis swarm (§7.3) only when all hold: `REPRODUCED` passed; ≥3 OPEN hypotheses whose
  experiments are independent; each experiment costs ≥ ~10 min serial; budget allows. Otherwise go serial.
- **DBG-41 MUST** give each lane exactly one hypothesis, its own worktree, a time/turn budget, the frozen repro, and
  the return schema. Lanes MUST NOT edit shared files outside their worktree or push.
- **DBG-42 MUST** synthesize results into the ledger, then run one confirmer on the leading SUPPORTED hypothesis
  before any fix merges.

### 4.6 Fix, proof and sweep

- **PRF-01 MUST** show red→green: the frozen repro fails on the pre-fix commit and passes on the fix commit, both run
  by the verifier in a clean worktree, with commands, exit codes and signatures recorded.
- **PRF-02 MUST** prove intermittent fixes statistically: n ≥ ln(α)/ln(1−p) consecutive clean runs with state reset
  between runs. α = 0.05 by default and 0.01 for money, auth, data integrity or concurrency primitives (table §3.5).
- **PRF-03 MUST** show the fix addresses the confirmed mechanism: the diff touches the mechanism named in the ledger,
  not only the symptom site (no catch-and-ignore, no retry wrapper, no timeout bump, unless the ledger's CONFIRMED cause
  *is* an external transient and the record says so).
- **PRF-04 MUST** pass the test-diff audit (with R04): no deleted, skipped or weakened tests; no edits to harness,
  timers, equality or evaluator code unless justified in the ledger.
- **PRF-05 MUST** run a sibling sweep: express the mechanism as a searchable pattern (grep, AST query, lint) and
  list every hit with its disposition (fixed / not-affected-because / follow-up task).
- **PRF-06 MUST** check whether the fix removes or makes obsolete a prior workaround, and re-run the broader suite
  with the workaround removed (masked-bug check).
- **PRF-07 SHOULD** for deployed systems, add a recurrence check in the target environment (canary, scheduled check or
  a log query naming the failure signature). Until it runs, the failure stays `FIXED-PENDING-LIVE`.

### 4.7 Lessons and generic tasks

- **LSN-01 MUST** end every resolved failure with a conversion step (§7.5 parts C–D) producing at least the regression
  test, plus zero or more of: a prevention control (lint, hook, type, schema constraint), a generic follow-up task, a
  lesson candidate.
- **LSN-02 MUST** prefer controls to prose. A lesson candidate that could be a lint or hook must say why it isn't one.
- **LSN-03 MUST** scope every lesson (`Applies when`, `Does not apply when`) and cite evidence. A lesson with one
  instance and low cost stays a project fact in STATE.md, not a skill lesson (R07 criteria).
- **LSN-04 MUST** write blamelessly. The subject of a lesson is a missing mechanism, never "the agent should be more
  careful".
- **LSN-05 SHOULD** phrase generic tasks as audits over a class with an enumerable scope and a completion check
  ("audit all webhook handlers for signature verification before body parse; done when every handler in
  `rg -l 'webhook' src/` has a test").

### 4.8 Process failures, escalation, human

- **PFX-01 MUST** record agent process failures (§7.6) with the same record format, class them, and apply the
  class remedy. A process failure that recurs twice gets a mechanical control.
- **ESC-01 MUST** follow the debugging ladder in §5. Every escalation carries the failure record, the ledger, the
  frozen repro command and a ≤300-word "what we know / what's falsified / what's untried" brief.
- **ESC-02 MUST** escalate when: 2 consecutive rounds end with no SUPPORTED hypothesis; 3 failed fix attempts;
  confirmer REFUTES twice; or trajectory budget exceeded.
- **ESC-03 MUST** stop and ask the human when: remaining experiments are destructive, touch production data or spend
  money; repro needs credentials, devices or accounts the agent lacks; the confirmed fix changes a public contract or
  product behaviour; a classifier refusal persists after Opus rerouting; or Fable-tier investigation has been
  exhausted. Unattended runs queue `BLOCKED-HUMAN` and continue with other work.

## 5. Model & effort assignment

Prices as verified by sibling R02 (per MTok in/out): Fable 5.1 $10/$50, Opus 4.8 $5/$25, Sonnet 4.6 $3/$15
(`research/mission-skill/99-synthesis-notes.md:69`). Effort is set in agent frontmatter only, so ship one agent file per
role@effort (`research/mission-skill/99-synthesis-notes.md:71`). No Haiku anywhere. The main cost driver in debugging
is *reading* logs, traces and code, not writing, so reading-heavy roles go to Sonnet and reasoning-over-ledgers roles
go to Opus or Fable. Scripts are rung 0: `git bisect run`, ddmin drivers and flake-proof loops need no model.

| Role | Model @ effort | Why this tier | Guard on the downgrade |
|---|---|---|---|
| Triage & failure-record author | Sonnet 4.6 @ medium | Structured extraction from an issue or CI log | Orchestrator rejects records missing DBG-01 fields (schema check, no model) |
| Check-the-plug runner | Sonnet 4.6 @ low | Runs a fixed checklist and prints results | Every item has a command and output line; missing → re-run |
| Repro builder / minimizer | Sonnet 4.6 @ high (Opus 4.8 @ medium for concurrency or platform-runtime bugs) | Mechanical but fiddly. Races need judgement about amplification | Gate is mechanical: repro exits non-zero at recorded rate on the verifier's run |
| Log/trace extractor | Sonnet 4.6 @ low | High-volume reading, quotes lines | Must quote verbatim with file:line. Orchestrator spot-checks 2 quotes per extraction via grep |
| Bisect / ddmin / differential driver | Script + Sonnet 4.6 @ low to wire it | Deterministic search | Bisect log attached. First-bad commit re-verified by running repro on it and its parent |
| Deep investigator (default, M+ bug hunts) | Opus 4.8 @ high | Hypothesis generation over code plus evidence. Hard-but-bounded is the post's Opus niche | Confirmer is a separate context. Ledger schema enforced |
| Investigator (S bugs, deterministic repro) | Sonnet 4.6 @ high | Cheap when the repro is deterministic and localised | 2 falsified rounds → Opus 4.8 @ high with the ledger (ES ladder) |
| Swarm lane (one hypothesis) | Sonnet 4.6 @ high; Opus 4.8 @ medium for concurrency, memory or compiler/runtime hypotheses | Runs one experiment in isolation | Fixed return schema. Raw command outputs attached. Confirmer re-runs the decisive experiment |
| Root-cause confirmer (refuter) | Opus 4.8 @ medium; @ high for money, auth, data or concurrency | Must be ≥ investigator tier for blocker-capable verdicts (R06 V-rules) | Sees ledger, repro, diff and evidence only, never the investigator transcript. Must attempt refutation first |
| Fixer | Sonnet 4.6 @ high once cause CONFIRMED; Opus 4.8 @ high if fix crosses components or touches a public contract | Once the mechanism is known, the fix is usually small | PRF-01..06 gates. Test-diff audit |
| Proof runner (red→green, N runs) | Script + Sonnet 4.6 @ low | Mechanical | Script prints tally. Verifier re-derives N from p |
| Sibling sweeper | Sonnet 4.6 @ medium | Pattern search plus triage of hits | Opus 4.8 @ medium samples ≥3 "not-affected" dispositions blind. Any disagreement → full Opus review of the sweep |
| Postmortem / lesson distiller | Opus 4.8 @ high (Fable 5.1 @ medium for cross-mission retro at XL) | Generalization with scope needs judgement | Promotion verifier (R07 criteria) in fresh context: Sonnet 4.6 @ high |
| Process-failure classifier | Sonnet 4.6 @ medium | Taxonomy mapping | Unclassifiable or 2 plausible classes → Opus 4.8 @ medium |
| Hypothesis-space reset (escalation) | Fable 5.1 @ high | Reads only the compact ledger and repro. Proposes new hypothesis families or a design question. Low input tokens, high leverage | Max 2 attempts with written reason. Output is hypotheses plus experiments, not a fix. Experiments still run on lower tiers |

**Debugging escalation ladder** (specializes R02 ES1, `research/mission-skill/99-synthesis-notes.md:74`):

```
Rung 0  scripts: bisect run / ddmin / differential / flake-proof            (always first where applicable)
Rung 1  Sonnet 4.6 high investigator          — S bugs with deterministic repro
Rung 2  Opus 4.8 high investigator            — default for M+ hunts; START here for concurrency, memory,
                                                 auth, payments, data integrity, platform runtime, compiler/toolchain
Rung 3  Fable 5.1 high hypothesis-space reset — after 2 rounds at rung 2 with no SUPPORTED hypothesis, or when
                                                 ≥2 causes interact, or confirmer REFUTES twice
Rung 4  Human                                  — ESC-03 triggers, or rung 3 exhausted (2 attempts)
Promotion rule: 2 failed rounds per rung. Every promotion ships: failure record + ledger + repro cmd + ≤300-word brief.
Security-flavoured hunts (exploitability, sandbox escape, crash triage for CVEs): route rungs 2–3 to Opus 4.8
explicitly; log any Fable classifier fallback as CLASSIFIER_BLOCK.
```

Cost reasoning. A typical M bug hunt without discipline burns tokens on one long, high-variance trajectory, and that
shape predicts failure (https://arxiv.org/abs/2511.00197). Under this ladder most tokens go to Sonnet (reading,
running, sweeping) and scripts (search). Opus reads compact ledgers and evidence excerpts. Fable is used rarely, on
small inputs that cache well. *Inference:* the biggest single saving is DBG-20. A 10-step `git bisect run` replaces
what is often dozens of model turns speculating about which recent change broke things.

## 6. Project-shape conditionals

### 6.1 Scale by scope

| Scope | Failure handling | Artifacts | Swarm | Lesson conversion |
|---|---|---|---|---|
| **S** (one behaviour, deterministic, ≤1 file) | DBG-01 fields go in the PR description. Repro test red→green. Sweep = one grep | Inline record, no investigation file | Never | Regression test only. At most 1 inbox line if it's a class |
| **M** (one component, or intermittent) | Full protocol. Ledger file. Confirmer at Opus @ medium | `.mission/investigations/O-xxx.md` | Rarely (≥3 independent costly experiments) | Test plus one control or task. Lesson candidate if recurrence or cost criteria hold |
| **L** (cross-component, prod-only, or multi-cause) | Full protocol plus differential environments plus PRF-07 live recurrence check | Investigation file plus postmortem (§7.5 B) | Yes when DBG-40 holds | Test, control, generic audit task, postmortem reviewed by fresh context |
| **XL** (incident with user impact, overlapping bugs, platform or compiler) | Mitigate first (DBG-02). Overlapping causes tracked as separate O-ids with a shared timeline | Incident timeline plus per-cause ledgers plus postmortem plus drill entry | Yes, and one lane per *cause family* | All four conversions, plus an incident-drill row (arcwell pattern, `arcwell/docs/operations/incident-drills.md:9-21`) |

### 6.2 Shape rules

- **IF the task is "find this deep annoying bug and fix it" THEN** this component *is* the mission. Phases: Intake
  (DBG-01..04) → `REPRODUCED` gate → Isolate (DBG-20..22) → Hypothesize/Experiment (ledger, optional swarm) →
  `CONFIRMED` gate (confirmer) → Fix → `PROVEN` gate (PRF-01..06) → Sweep → Convert (LSN) → `FIXED` or
  `FIXED-PENDING-LIVE`. The spec artifact is the bugfix card (Current / Expected / Unchanged, per sibling R03). No
  greenfield-style spec.
- **IF the bug has no repro after the repro budget (S: 30 min, M: 2 h, L: half a day of agent time) THEN** switch
  deliverable to *observability*: add structured logging or tracing at component boundaries with the failure signature,
  ship behind a flag, set a recurrence query, and record `UNREPRODUCED`. Don't ship speculative fixes without
  flagging them.
- **IF the failure is intermittent THEN** measure p first, amplify, and use PRF-02. Quarantine the test only with an
  expiry and an O-id (sibling R04 flake policy). Never retry-to-green.
- **IF the task includes a greenfield multi-platform app (e.g. Swift iOS + Cloudflare) THEN** every failed gate during
  build gets a failure record, but at S depth unless it recurs or crosses the contract. Cross-boundary failures (the
  API contract fails on device but not in the simulator) default to M and must run the simulator-vs-device and
  local-vs-preview differentials (§3.6). Device-only surfaces stay `UNPROVEN(DEVICE_REQUIRED)` until run on hardware.
- **IF the task adds a feature to an existing product THEN** regressions caught by existing tests MUST be bisected
  against the feature branch base before investigation. A pre-existing failure found along the way gets an O-id and a
  follow-up task, but never blocks the feature (sibling R06 "pre-existing never blocks").
- **IF the task is a service migration/extraction (e.g. moving the AI gateway into the platform) THEN** parity failures
  are debugged *differentially* first: same recorded request replayed on old and new paths, diff of responses,
  headers, side effects and timing. Every parity failure becomes a parity-inventory row plus regression fixture. Env and
  config drift (bindings, compatibility dates, secrets) is the first hypothesis family.
- **IF the task is research plus a marketing website THEN** "failures" are mostly broken builds, links and factual
  errors. Use the S-depth record. The lesson conversion target is usually a check (link checker, citation verifier),
  not a debugging protocol. Keep ceremony minimal.
- **IF the task includes a dependency or toolchain upgrade THEN** bisect over *dependency versions* (lockfile
  bisection) as well as commits. Check changelogs for behaviour changes before hypothesizing about your own code.
  Test whether removing old workarounds is safe (PRF-06).
- **IF the task is performance-regression hunting THEN** the repro is a benchmark with a numeric threshold and variance
  measured over ≥10 runs. `git bisect run` uses the threshold (bisect supports "old/new" terms for any property,
  https://git-scm.com/docs/git-bisect). On iOS, the benchmark MUST run on device (§3.6).
- **IF the failure is an agent process failure (not a product bug) THEN** use §7.6. The "fix" is a control in the
  mission machinery (hook, preflight, gate, template field), and the regression test is an eval case or hook self-test.
- **IF running unattended (Routine / headless) THEN** the investigation may run through local `PROVEN` gates, but it
  ends in a draft PR on a `claude/` branch plus the failure record. It never merges or deploys. `PROVEN` or
  `FIXED-PENDING-LIVE` checks that need credentials, devices or production access queue `BLOCKED-HUMAN`.

## 7. Artifacts & templates

### 7.1 Debugging protocol (paste into `references/debugging.md`)

```markdown
# Debugging protocol (bug hunts, failed gates, incidents)

Gates: OPENED → REPRODUCED → CONFIRMED → PROVEN → SWEPT → CONVERTED → FIXED | FIXED-PENDING-LIVE
Nothing skips a gate. UNREPRODUCED / UNPROVEN(<reason>) are honest terminal states that go to the human queue.

0. MITIGATE (only if users are impacted): revert / flag off / retry / manual recovery. Log it. The failure stays OPEN.
1. OPEN the failure record (.mission/investigations/O-###.md, part A). Symptom verbatim, expected vs observed,
   env fingerprint, first seen, detection path, blast radius.
2. CHECK THE PLUG. Right commit/deployment? Build fresh? Env vars and bindings present? Test actually executed?
   Record each with command + output line.
3. CLASSIFY against the hard-class table (references/bug-classes.md). Load that class's tactics.
4. REPRODUCE. Write scripts/repro/O-###.sh (or a test) that exits 1 on failure and prints `SIGNATURE: <one line>`.
   Measure baseline: deterministic, or p = failures/runs with ≥5 failures observed. Amplify races before measuring.
   Minimize (ddmin input/config; strip steps). FREEZE it (protected path). Gate: REPRODUCED.
   No repro within budget → switch to observability deliverable, state UNREPRODUCED(<reason>).
5. ISOLATE mechanically, where applicable, before theorizing:
   - known good revision → `git bisect start <bad> <good>` + `git bisect run scripts/repro/O-###.sh`
   - large failing input/config → ddmin
   - an environment that works → differential run, diff fingerprints first
   - multi-component → log what enters/leaves each boundary once; re-run repro (Heisenberg check)
6. HYPOTHESIZE. Ledger (part of O-###.md). ≥3 hypotheses across layers. Each: prediction, discriminating
   experiment, expected-if-true / expected-if-false. One variable per experiment. Keep FALSIFIED entries.
   Optional swarm when ≥3 independent costly experiments (references/bug-hunt-swarm.md).
7. CONFIRM. Two-way intervention on the minimal repro, issued by a separate confirmer context. Gate: CONFIRMED.
8. FIX the confirmed mechanism. ONE change. No drive-by refactors. No retries/timeouts/catch-all unless the
   confirmed cause is an external transient and the record says so. 3 failed fixes → stop, escalate with ledger.
9. PROVE (proof-of-fix checklist). Red on parent, green on fix, clean worktree, N = ln(α)/ln(1−p) runs for flakes,
   test-diff audit clean, masked-workaround check. Gate: PROVEN.
10. SWEEP siblings: mechanism → search pattern → every hit dispositioned. Gate: SWEPT.
11. CONVERT: regression test (always) + control / generic task / lesson candidate (part C–D). Gate: CONVERTED.
12. CLOSE: FIXED, or FIXED-PENDING-LIVE until a recurrence check runs in the target environment.

Escalate (attach record + ledger + repro cmd + ≤300-word brief) when: 2 rounds with no SUPPORTED hypothesis;
3 failed fixes; confirmer REFUTES twice; budget exceeded.
Ask the human when: experiments are destructive / production / spend money; missing credentials or devices;
fix changes a public contract or product behaviour; refusal persists after Opus reroute; rung 3 exhausted.

Red-flag thoughts (return to step 4): "quick fix now, investigate later" · "let me just try X" · "probably X" ·
"add a retry" · "increase the timeout" · "skip this test for now" · "one more attempt" (after 2+) ·
"it passed 3 times, it's fixed".
```

*(The red-flag list is adapted from the practitioner skill at
https://raw.githubusercontent.com/obra/superpowers/main/skills/systematic-debugging/SKILL.md. `git bisect run` treats
exit 0 as good, 125 as skip, and other codes up to 127 as bad, per https://git-scm.com/docs/git-bisect. For
intermittent bugs the repro script must loop internally until it sees a failure or reaches N runs, otherwise bisect
mislabels commits.)*

### 7.2 Hypothesis ledger template (section of `.mission/investigations/O-###.md`; example values are illustrative)

```markdown
## Ledger · O-### · <one-line symptom>
Repro: `scripts/repro/O-###.sh` · baseline: p = 7/200 (3.5%) amplified with STRESS=8 · frozen at <sha>
Isolation done: bisect → first bad <sha> (log: logs/O-###-bisect.txt) · ddmin: n/a (input 3 lines) ·
  differential: local wrangler dev PASS 0/200 vs preview FAIL 9/200 (fingerprint diff: compatibility_date, flag X)
Round: 2 · rung: 2 (Opus 4.8 high) · fix attempts: 0/3 · budget used: 41% of M

### H-01 · Module-scope cache shared across requests returns another tenant's token
- Layer: code/runtime · Proposed by: investigator r1 · Status: FALSIFIED (r1)
- Mechanism: `let tokenCache` at module scope survives on a warm isolate; key omits tenant id
- Prediction: if true, failures only occur on second+ request to the same isolate, and forcing a cold isolate per
  request drives p → 0
- Experiment: `STRESS=8 COLD_ISOLATE=1 scripts/repro/O-###.sh --runs 200`
- Expected if true: 0/200 · Expected if false: ≈7/200
- Result: 8/200 failures (logs/O-###-H01.txt:14 "SIGNATURE: 401 tenant=b token=a")
- Conclusion: FALSIFIED. The cold isolate does not change the rate. Keep: the signature shows cross-tenant token, which
  constrains H-03.

### H-02 · Webhook handler reads body before verifying signature; retried delivery races the first
- Layer: timing · Status: SUPPORTED (r2) → pending confirmer
- Prediction: if true, injecting 50 ms latency before signature verification raises p sharply; serializing per
  delivery id drives p → 0
- Experiment A: `INJECT_DELAY_MS=50 ...` · expected-if-true: p ≫ 3.5% · result: 61/200 (30.5%)
- Experiment B: `SERIALIZE_BY_DELIVERY_ID=1 ...` · expected-if-true: 0/149 · result: 0/149 (logs/O-###-H02B.txt)
- Confirmer verdict: <CONFIRMED | REFUTED(reason) | UNVERIFIED(reason)> · confirmer: opus-4.8 medium · date

### H-03 · ...
- Status: OPEN · Experiment: ... · Assigned: swarm lane 3 (worktree wt-O###-H03)

### Statuses
OPEN (untested) · RUNNING (lane assigned) · SUPPORTED (prediction held once) · FALSIFIED (prediction failed;
never delete) · CONFIRMED (two-way intervention, independent confirmer) · PARKED (untestable here; reason + what
would test it)

### Contributing factors (fill once CONFIRMED)
- Why the tests didn't catch it: ...  · Why it shipped: ...  · Why detection took <duration>: ...
- Prior workaround masking it? <none | path + removal test result>
```

Rules the template enforces: every experiment has *both* expected outcomes written before running it (this blocks
post-hoc rationalization); every result cites a log path and line; SUPPORTED is not CONFIRMED.

### 7.3 Bug-hunt swarm pattern (paste into `references/bug-hunt-swarm.md`)

```markdown
# Bug-hunt swarm (hypothesis-per-lane)

Entry test (all must hold, else run serially): REPRODUCED gate passed · ≥3 OPEN hypotheses whose experiments are
independent (none requires another's result) · each experiment ≥ ~10 min serial · budget headroom ≥ lanes × lane cap.
Fan-out cap: S 0 · M 3 · L 4 · XL 6 (one lane per cause family at XL).

1. PREPARE (orchestrator): freeze repro at <sha>; write the ledger with H-ids, predictions, experiments and both
   expected outcomes; assign one H-id per lane; verify no two lanes need to edit the same file for their experiment.
2. DISPATCH lanes in parallel. Each lane: own worktree (isolation: worktree / git worktree add), branch
   claude/O###-H##, turn cap (M 25 / L 40), token cap, the lane brief below. Lanes never push, never merge, never edit
   the frozen repro or tests, never touch other lanes' worktrees.
3. COLLECT returns (fixed schema). Reject a return that lacks raw command output excerpts with log paths.
4. SYNTHESIZE (orchestrator, or Opus 4.8 high at L/XL): update ledger statuses; look for *interactions* (two
   SUPPORTED hypotheses may be jointly sufficient contributors, not rivals); decide the leading hypothesis.
5. CONFIRM (separate context): confirmer re-runs the decisive experiment in a fresh worktree and attempts refutation.
6. BRANCH: CONFIRMED → fix phase (fix lands from a clean branch, not from a lane's experimental hacks).
   None SUPPORTED → round +1 with new hypotheses (after 2 rounds: escalate rung). REFUTED → ledger note, round +1.
7. CLEAN UP: `git worktree list` sweep; delete lane branches unless referenced by the ledger.
```

**Lane brief skeleton** (`.claude/agents/hypothesis-lane-sonnet-4-6-high.md` body; Opus variant for concurrency, memory
or runtime hypotheses):

```markdown
You are testing ONE hypothesis about a reproduced failure. You run experiments; you do not fix the bug.

Failure: O-### — <symptom line>. Repro: `scripts/repro/O-###.sh` (frozen; do not edit). Baseline p = <p>.
Hypothesis H-##: <statement>. Mechanism: <mechanism>.
Prediction: <if true, then ...>. Planned experiment: <command/change>.
Expected if TRUE: <...>. Expected if FALSE: <...>.
Falsified so far (do not re-test): <H-ids + one line each>.
Worktree: <path>. Branch: claude/O###-H##. Budget: <turns>, <tokens>.

Rules:
- Change ONE variable per experiment. Temporary instrumentation is allowed in your worktree only.
- After adding instrumentation, re-run the repro unchanged once to confirm the failure still occurs.
- You MAY refine the experiment if the planned one is not discriminating; say why, and write both expected outcomes
  BEFORE running it.
- Never edit tests, the repro, harness, timers or equality code to change outcomes. If the experiment seems to
  require it, stop and return STATUS: BLOCKED.
- Quote raw output lines with log file path:line. Do not paraphrase results.
- An honest FALSIFIED or INCONCLUSIVE is a successful lane.

Return exactly:
STATUS: SUPPORTED | FALSIFIED | INCONCLUSIVE | BLOCKED
H-ID: H-##
EXPERIMENTS: [{cmd, change_vs_baseline, expected_true, expected_false, observed, runs, failures, log: path:line}]
NEW_OBSERVATIONS: <facts noticed that bear on other hypotheses, each with log path:line>
NEW_HYPOTHESES: <0–2, each with a discriminating experiment>
PATCH_SKETCH: <only if SUPPORTED: where the mechanism lives, file:line; no full fix>
COST: turns used, approx tokens
```

**Confirmer prompt skeleton** (`root-cause-confirmer-opus-4-8-medium.md`; `-high` variant for money, auth, data,
concurrency):

```markdown
You are an independent root-cause confirmer. Your job is to REFUTE the claimed root cause if you can.
You see: the failure record, the ledger, the frozen repro, and the lane's evidence files. You do not see anyone's
reasoning transcript. Work in a fresh worktree at <sha>.

Claim: H-## is the root cause of O-###. Decisive experiment: <cmd + change>.

Do, in order:
1. Re-run the repro at baseline. Record failures/runs. If you cannot reproduce at ≈p, verdict UNVERIFIED.
2. Apply the cause-removal change alone. Run N = ceil(ln(0.05)/ln(1−p)) times (0.01 for money/auth/data/concurrency).
3. Re-introduce the cause (or remove the change). Confirm failures return at ≈p.
4. Look for a cheaper alternative explanation that also fits steps 1–3 (e.g. the change also alters timing or
   caching globally). Try one experiment that separates them.
5. Verdict: CONFIRMED | REFUTED(<which step failed, evidence path:line>) | UNVERIFIED(<what's missing>).

Return: VERDICT, STEP_RESULTS (cmd, runs, failures, log path:line), ALTERNATIVE_TESTED, CONFIDENCE_BASIS.
```

### 7.4 Proof-of-fix checklist (the verifier fills it in `VERIFICATION.md` § O-###)

```markdown
## Proof of fix · O-### · verifier: <model@effort> · worktree: <path> · date
[ ] P1 Repro frozen: `scripts/repro/O-###.sh` unchanged since <sha> (git log -- path shows no edits after freeze)
[ ] P2 RED on parent: `git checkout <fix-sha>~1 && scripts/repro/O-###.sh` → exit ≠0, SIGNATURE matches record
[ ] P3 GREEN on fix: same command at <fix-sha> → exit 0
[ ] P4 Intermittent? baseline p = <x>/<n> (≥5 failures). Required clean runs N = ceil(ln α / ln(1−p)), α = <0.05|0.01>
       `scripts/flake-proof.sh <N> scripts/repro/O-###.sh` → "PASS N/N" · state reset between runs: <how>
[ ] P5 Mechanism match: diff touches <file:line from CONFIRMED hypothesis>. Symptom-only patterns absent (catch-and-
       ignore, blanket retry, timeout bump, sleep, feature disabled) OR justified by ledger (external transient)
[ ] P6 Test-diff audit clean: no deleted/skipped/.only/weakened tests; no harness/timer/equality/evaluator edits;
       no fixture literals in production code; test count not decreased
[ ] P7 Full relevant suite green in clean worktree: <cmd> → exit 0, <counts>
[ ] P8 Masked-workaround check: prior workarounds for this symptom listed; each removed-and-rerun or kept with reason
[ ] P9 Sibling sweep: pattern `<rg/ast-grep/lint query>` → <k> hits; each dispositioned (fixed in <sha> | not affected
       because <reason> | follow-up T-###); sampled "not affected" checked by second reviewer
[ ] P10 Regression test is the repro, or a smaller test that goes red on parent (same P2/P3 evidence)
[ ] P11 Deployed system? recurrence check defined (<canary/log query/scheduled check>) → state FIXED-PENDING-LIVE
       until it runs; record run evidence when it does
[ ] P12 Unavailable proof (device, credentials, prod)? gate = UNPROVEN(<reason>) + BLOCKED-HUMAN item. Never green.
Verdict: PROVEN | NOT-PROVEN(<failed items>) | UNPROVEN(<reason>)
```

`scripts/flake-proof.sh` (a minimal, stack-agnostic loop; `RESET_CMD` resets state between runs):

```bash
#!/usr/bin/env bash
# usage: flake-proof.sh <runs> <repro-cmd> [args...]; exits 0 only if every run passes
set -uo pipefail
mkdir -p logs
runs="$1"; shift
fails=0
for i in $(seq 1 "$runs"); do
  if [ -n "${RESET_CMD:-}" ]; then bash -c "$RESET_CMD" >/dev/null 2>&1; fi
  if ! "$@" > "logs/flake-run-$i.txt" 2>&1; then
    fails=$((fails + 1))
    echo "FAIL run $i (logs/flake-run-$i.txt)"
    [ "${STOP_ON_FAIL:-1}" = "1" ] && break
  fi
done
if [ "$fails" -eq 0 ]; then echo "PASS $runs/$runs"; exit 0; fi
echo "FAILED $fails (stopped at run $i of $runs)"; exit 1
```

Sample-size helper line for the verifier (no model needed):
`python3 -c "import math,sys; p=float(sys.argv[1]); a=float(sys.argv[2]); print(math.ceil(math.log(a)/math.log(1-p)))" 0.02 0.05` → 149.

### 7.5 Failure record → lesson → generic task conversion template (`.mission/investigations/O-###.md`)

```markdown
# O-### · <symptom, one line> · state: OPENED|REPRODUCED|CONFIRMED|PROVEN|SWEPT|CONVERTED|FIXED|FIXED-PENDING-LIVE|UNREPRODUCED(<r>)
Kind: product-bug | process-failure (class <PF-class>) · Scope: S|M|L|XL · Bug class: <from bug-classes.md>

## A. Record (filled at OPEN)
- Detected by: <test/CI job/user report/canary/review> at <UTC time> · First bad seen: <sha/deploy/date>
- Symptom (verbatim): <error text / screenshot path / log line with path:line>
- Expected: <...> · Observed: <...>
- Env fingerprint: commit <sha> · runtime <versions> · config hash <x> · platform <sim|device model/OS | local|preview|prod>
- Blast radius: <users/requests/data affected; unknown is allowed but must say so>
- Mitigation (if any): <revert/flag/manual recovery + time> — does NOT resolve this record
- Check-the-plug: <each item + command + output line>

## B. Investigation summary (filled at CONFIRMED; ledger lives below)
- Mechanism (confirmed): <one paragraph, cite H-id + confirmer verdict>
- Contributing factors: detection gap <...> · test gap <...> · process gap <...> · masking workaround <...>
- Timeline (L/XL): <UTC lines: introduced, detected, mitigated, confirmed, fixed, live-verified>
- Blameless statement: "The system lacked <mechanism>, so <failure> could <happen/ship/go undetected>."

## C. Generalization (filled at CONVERT — distiller role)
- Mechanism class (abstract, no project names): <e.g. "request-scoped data held in process-global state">
- Where else can this class occur? <enumerable scope: all Worker modules with module-scope `let`; all webhook handlers>
- Sweep result: <k hits; fixed/not-affected/follow-up — from proof checklist P9>
- Could a machine prevent the whole class? <yes: lint/type/hook/schema constraint → D2 | no, because <reason>>
- Recurrence/cost: <first occurrence | seen in O-###, <other mission> · time lost · user impact>
- Evidence the generalization holds beyond this case: <second instance, or doc source, or "none yet" → confidence low>

## D. Outputs (every line has an owner and a completion check)
- D1 Regression test (ALWAYS): <path> · red on <parent sha>, green on <fix sha> · frozen: yes
- D2 Prevention control (if C says machine-preventable): <lint rule / PreToolUse hook / type / DB constraint / CI check>
      at <path> · self-test: <command showing the control rejects a seeded bad example> · T-### if deferred
- D3 Generic follow-up task(s): T-### "<Audit|Migrate|Instrument> all <class scope> for <mechanism>" ·
      scope query: `<rg/ast-grep query>` · done when: <every hit has test/disposition> · size: S|M · owner: <role>
- D4 Project fact / rule (STATE.md): F-### or R-### · Applies when <...> · Instances <O-ids> · Counter-cases <...>
- D5 Lesson candidate (LESSONS-INBOX.md, R07 format) ONLY IF: mechanism CONFIRMED ∧ class general ∧ (count ≥ 2 ∨
      cost ≥ 1 day ∨ user-visible) ∧ D2 impossible or insufficient. Otherwise write "no lesson: <reason>".
- D6 Known-failure-mode entry for the skill (via promotion only): target references/lessons.md § <Debugging|Testing|
      Platform> · eval case drafted: evals/evals.json id <n>
- D7 Drill (XL / operational failure classes): row in incident-drills.md with automated proof + live injected fault

## E. Close
- Proof-of-fix verdict: <PROVEN|UNPROVEN(<r>)> (VERIFICATION.md § O-###) · Live recurrence check: <evidence|pending>
- Reviewed by (fresh context): <model@effort> · open questions: <...>
```

**Worked conversion example** (illustrative, not from a real incident):

| Stage | Content |
|---|---|
| Record | Checkout webhook intermittently double-charges (p ≈ 2% under retry storm) |
| Mechanism | Handler inserts payment row before checking an idempotency key. Provider retries a slow first delivery |
| Class | Side-effecting handler without idempotency guard on at-least-once delivery |
| D1 test | Replays the same delivery twice concurrently; asserts one charge |
| D2 control | DB unique constraint on `(provider, delivery_id)`, plus a lint that fails when a queue/webhook handler lacks an `idempotencyKey` call |
| D3 task | T-041 "Audit all at-least-once consumers (webhooks, queue handlers, cron retries) for idempotency; done when each has a duplicate-delivery test" |
| D4 rule | R-012 "At-least-once inputs need an idempotency key enforced by storage, not by application checks" |
| D5 lesson | Candidate only after a second mission hits the class, or immediately if money was lost (cost criterion) |

### 7.6 Process-failure taxonomy (paste into `references/process-failures.md`)

A process failure is when the *mission machinery* produces a wrong outcome: a false "done", a gamed signal, wasted
rounds. It gets an O-id with `Kind: process-failure`, uses the same record template, and its D1 "regression test" is a
hook self-test or an eval case. Grounding: agents cheat on tests (https://arxiv.org/abs/2510.20270,
https://metr.org/blog/2025-06-05-recent-reward-hacking/); multi-agent systems fail in design, misalignment and
verification (https://arxiv.org/abs/2503.13657); failed trajectories are long and high-variance
(https://arxiv.org/abs/2511.00197). The class list itself is this lane's synthesis.

| Class | Detection signature | Immediate remedy | Prevention control (mechanical) | Escalate / human when |
|---|---|---|---|---|
| **PF-01 PREMATURE_DONE** | "Done/fixed" claim with no gate evidence. Gate flipped by maker. Verifier can't reproduce green | Reopen. Run verifier on the gate | Only verifier flips gates. Stop hook runs `check.sh`. Return schema requires command + exit code + output line | Second occurrence in a mission → orchestrator audits all gates flipped that session |
| **PF-02 GAMED_TEST** | Test deleted, skipped, weakened or special-cased. Harness, timer, equality or evaluator edited. Fixture literals in prod code | Revert those edits. Rerun gate. Record | Frozen paths + PreToolUse hook + hash manifest + test-diff audit (with R04). `TEST-DISPUTE` channel | Always report to human in the mission summary. Promote maker's role one tier for that task |
| **PF-03 SYMPTOM_PATCH** | Fix is a retry, timeout bump, sleep, catch-and-ignore or feature disable, with no CONFIRMED mechanism | Reject the fix and return to ledger | PRF-03 mechanism-match item. Diff grep for symptom patterns in the proof checklist | 3 symptom patches on one failure → rung +1 with "question the design" brief |
| **PF-04 LOST_CONTEXT** | Re-tests a FALSIFIED hypothesis. Violates a constraint stated earlier. Contradicts STATE.md | Stop. Reload ledger + STATE Resume section | Ledger file is the source of truth. SessionStart hook injects Resume + open O-ids. Handoff at ~60% context. Constraints in rules/hooks, not chat | Recurs twice → shorten briefs, split task, add hook injection |
| **PF-05 WRONG_ASSUMPTION** | Action depends on an unverified belief (units, env, API semantics, which deployment) that turns out false | Record as FALSIFIED fact. Re-run affected experiments | Assumptions logged `A-##` with a verification command. Check-the-plug step. Facts need evidence level | Assumption has high reversal cost and can't be verified → ask human |
| **PF-06 TOOL_MISUSE** | Stale build tested. Wrong branch or cwd. Exit code masked by a pipe. Wrong environment targeted. Grep over the wrong tree | Re-run with fingerprint printed | Env fingerprint in every evidence block. Checks run through exit-preserving runners. Preflight smoke (`check.sh --smoke`) | Tool unavailable or broken → degrade explicitly (`UNPROVEN(TOOL)`) |
| **PF-07 SPEC_GAP** | Fix disputes: "expected" behaviour is undefined, or the fix changes product or public contract behaviour | Freeze fix. Write bugfix card Current / Expected / Unchanged | Bugfix card required at intake (R03). Public-contract diff check | Behaviour change or contract ambiguity → ask human (ESC-03) |
| **PF-08 CLASSIFIER_BLOCK** | Refusal text. Empty or partial output. Silent model fallback logged by harness. Sudden quality drop on security-flavoured work | Discard partial output. Re-run same brief on Opus 4.8. Log fallback event | Pre-route security/exploit work to Opus 4.8. Log model per spawn. Reassert model at phase boundary (R02) | Second refusal → human. Never rephrase to evade |
| **PF-09 MISSING_ENV** | Needs credentials, device, account, paid API or production access that isn't present (arcwell example: `arcwell/docs/handoff/2026-08-22-post-deploy-verification.md:196-197`) | Gate → `UNPROVEN(MISSING_<X>)`. Queue `BLOCKED-HUMAN`. Continue other work | Intake preflight lists required secrets and devices per gate. Never mock-substitute a live gate | Immediately queue for human. Never silently skip |
| **PF-10 FLAKE_MISREAD** | "Fixed" after too few runs, or "just flaky" declared without a measured rate or investigation | Compute N from p. Re-run proof | PRF-02 script. Quarantine needs an expiry and an O-id | Quarantine expiring with no investigation → human decision |
| **PF-11 THRASHING** | Same failure signature twice with no ledger change. Turn count > cap. Oscillating fixes. Trajectory length alarm | Stop. Write ≤300-word state brief | Futility stop rule (R01 S4). Turn and token caps per role. Ledger-update requirement per round | Escalate rung. After rung 3 → human |
| **PF-12 SWARM_MISALIGNMENT** | Lanes test overlapping hypotheses, edit the same files, or return narratives without evidence. Synthesizer accepts SUPPORTED as CONFIRMED | Reject non-schema returns. Re-dispatch the single lane | Disjoint H-ids. Worktree per lane. Fixed return schema. Mandatory confirmer | Two misaligned rounds → go serial |
| **PF-13 SCOPE_CREEP** | Fix diff includes refactors or "while I'm here" changes. Diff size way above mechanism size | Split into fix commit and follow-up task | One-change rule. Diff-size budget in proof checklist. Separate T-### for refactors | Refactor needed to fix → design review task |

### 7.7 Hard bug classes: tactics table (paste into `references/bug-classes.md`)

Tool flags named here are common practice. They were *not* individually verified in this lane, so the skill should
probe them at setup (`--help`) before relying on them.

| Class | Signals | Repro / amplify | Isolate | Proof | Symptom-patch trap |
|---|---|---|---|---|---|
| **Flaky / race / timing** | Rate < 100%. Order-dependent. Worse under load or in CI | Loop N runs. Shuffle test order. Raise parallelism. Throttle CPU. Inject latency at suspected interleavings. Race detectors (TSan, `go test -race`) | Serialize one resource at a time (one variable). Log with monotonic timestamps plus ids at boundaries | PRF-02 N from p, state reset per run | `sleep`, longer timeouts, blanket retries. Prefer condition-based waits |
| **Heisenbug** (vanishes when observed) | Disappears with debugger, logging or `-O0` | Record-and-replay where available. Low-overhead ring-buffer logging dumped on failure. Keep build flags identical | Differential on build config (flags, optimizer, precision). Minimized repro on the other backend (the Anthropic CPU-vs-TPU move, https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues) | Re-run with instrumentation removed | "Fixed" because the instrumentation changed timing |
| **Resource / memory leak** | Monotonic growth. OOM after hours. Degraded throughput over time | Soak script that compresses time (many cycles fast). Heap snapshots at t0/t1/t2 | Diff heap snapshots by retained type. Bisect with the soak threshold as the property | Soak for ≥3× the pre-fix time-to-failure with flat trend | Periodic restarts, bigger instance |
| **Env / config drift** | "Works on my machine". Only one environment fails | Capture env fingerprints (versions, flags, bindings, secrets present, compatibility date) for good vs bad | Delta-debug the fingerprint diff: apply half the differences to the good env, repeat | Repro passes in the bad env with a *configuration-as-code* change | Hand-editing prod config with no record. Hand-written `Env` types (https://developers.cloudflare.com/workers/best-practices/workers-best-practices/index.md) |
| **Dependency upgrade** | Broke after lockfile change | Pin old against new in two worktrees | Bisect over dependency versions or lockfile commits. Read changelog before own-code theories. Check removed workarounds | Red on new version, green with fix. Pinned-version test added | Pinning forever with no O-id or task |
| **Data-dependent** | Only certain records, tenants or inputs | Capture the failing input (sanitized). ddmin it to 1-minimal (https://www.cs.purdue.edu/homes/xyzhang/fall07/Papers/delta-debugging.pdf) | Property-based generator around the minimized case to find the boundary | Minimized case as a regression test. Property test over the boundary | Special-casing the one bad record |
| **Distributed / async** | Duplicates, lost messages, out-of-order effects, "confusing and contradictory reports" | Replay recorded message sequences. Force retries and redelivery. Kill between accept and record (arcwell drill 5, `arcwell/docs/operations/incident-drills.md:15`) | Correlation ids end to end. Build a per-message timeline. Separate overlapping causes into distinct O-ids | Duplicate and reorder injection tests. Idempotency enforced by storage | Dedupe in the UI layer only |
| **Performance regression** | Metric crossed threshold after a change | Benchmark with warmup, ≥10 runs, variance reported, same hardware | `git bisect run` with threshold script ("old/new" terms, https://git-scm.com/docs/git-bisect). Profiler diff | Benchmark back under threshold with non-overlapping variance bands | Caching that hides the hot path |
| **iOS simulator vs device** | Device-only crash or behaviour. Perf or memory only on device | Classify against Apple's difference list: performance, background suspension, case-sensitive FS, missing hardware or APIs, Metal (https://developer.apple.com/documentation/xcode/testing-in-simulator-versus-testing-on-hardware-devices) | Device logs and Instruments on hardware. Differential sim vs device with the same build config | On-device run evidence. Otherwise `UNPROVEN(DEVICE_REQUIRED)` | Declaring fixed from the simulator |
| **Cloudflare Workers runtime** | Prod-only intermittency, cross-request errors, differences between `wrangler dev` and deployed | Hammer one warm isolate with sequential requests from different tenants. Cold-start runs. Compare compatibility date and flags | Differential local vs preview deploy. Grep module-scope mutable state. Check for request-scoped I/O objects shared across handlers ("Cannot perform I/O on behalf of a different request", https://community.cloudflare.com/t/cannot-perform-i-o-on-behalf-of-a-different-request/184007). Isolates may be evicted (https://developers.cloudflare.com/workers/reference/how-workers-works/) | Integration test in the Workers runtime pool plus preview-deploy canary | Adding global caches or retries around cross-request I/O |

## 8. Anti-patterns & failure modes

**Investigation anti-patterns**

- **Shotgun fixing.** Changing several things, running tests, keeping whatever turns green. It breaks one-variable
  experiments, and nobody can say which change mattered (Agans rule 5,
  https://www.binaryphile.com/debugging/software-engineering/2026/01/09/agans-debugging-guide.html).
- **Theorizing before reproducing.** Long causal essays from a stack trace. SRE warns about "latching on to causes of
  past problems" and spurious correlations (https://sre.google/sre-book/effective-troubleshooting/). Agents are fluent
  storytellers, so this is their default mode.
- **Retry-to-green.** CI reruns until green, then "flaky, moving on". It hides real bugs that "succeed 4 out of 5
  times" (https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html).
- **Read-only hypothesis swarms.** Five agents each argue for a theory, "first to find strong evidence" wins
  (https://claude-world.com/articles/debugging-techniques/). You pay for five narratives and still have to run the
  experiment.
- **Deleting the ledger's negatives.** Rewriting the investigation file into a clean story. The next context or
  escalation tier then re-tests falsified ideas.
- **Removing a workaround because "we fixed the root cause"**, without re-running the failure class. This is exactly how
  Anthropic's deeper top-k bug surfaced (https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues).
- **Single-cause tunnel vision on multi-cause incidents.** Forcing one root cause onto overlapping failures
  (https://how.complexsystems.fail/).
- **Simulator / local proof for device / production bugs.** It proves the wrong environment (§3.6).
- **Instance fixes without a sweep.** The same mechanism resurfaces in the next review round
  (`arcwell/docs/operations/milestone-ledger.md:57-58`).

**Proof anti-patterns**

- "Passed 3 times" for a 1-in-50 flake. That needs 149 runs for 95% (§3.5).
- Proof runs that share state (warm DB, same simulator, cached build), which fakes independence.
- The maker issues its own CONFIRMED or PROVEN verdict.
- A /goal model grader judging "the flake is fixed" from narrative text. The evaluator only reads the transcript
  (https://code.claude.com/docs/en/goal).
- Tests "fixed" by editing expectations to match new output, without a TEST-DISPUTE decision.

**Lesson anti-patterns**

- **Lesson inflation.** Every bug becomes a "general rule". Lessons files grow, go unread and contradict each other.
  Gate lessons on scope, evidence and recurrence or cost (LSN-03; R07 budgets).
- **Blame-shaped lessons.** "Be more careful with X" is unenforceable. Name the missing mechanism
  (https://sre.google/sre-book/postmortem-culture/).
- **Prose where a control fits.** A known-failure-mode paragraph instead of a lint rule, hook or constraint.
- **5-whys as the method.** A linear chain that stops where knowledge stops. Use it only as a prompt for
  contributing factors.
- **Generic tasks without an enumerable scope.** "Improve webhook robustness" never finishes. "Audit every handler
  matching `<query>` for `<mechanism>`; done when each has a duplicate-delivery test" does.
- **Unreviewed postmortems.** "An unreviewed postmortem might as well never have existed"
  (https://sre.google/sre-book/postmortem-culture/).

**Cost / token traps**

- Dumping raw logs or full CI output into the orchestrator (Fable or Opus) context. Extract with Sonnet low and quote
  lines.
- Launching Fable 5.1 at the start of a bug hunt "because it's hard". Mechanical isolation (bisect, ddmin, differential)
  is far cheaper and often decisive.
- Swarms without the entry test. N lanes × long trajectories × no repro = expensive noise. Multi-agent token use is
  ~15× chat, per sibling R09 citing Anthropic (`research/mission-skill/09-swarms-workflows-parallelism.md:46`).
- Statistical proof run by a model turn per run. Use a script, and let the model read the final tally.
- Escalating by re-asking the same question to a bigger model without the ledger. The bigger model re-derives the
  same falsified hypotheses at a higher price.

**Process bloat**

- Full L-depth ceremony (postmortem, drills, swarm) for an S bug. §6.1 is the ceiling, not the floor.
- Writing lesson candidates for one-off typos.
- Drill rows for failure classes that aren't operational.

## 9. Open questions / risks for the synthesizer

1. **Flake-proof threshold conflict with R04.** R04 proposes "fix passes ≥10N" (`research/mission-skill/99-synthesis-notes.md:55`).
   This lane proposes N = ln(α)/ln(1−p), with α = 0.05 by default and 0.01 for risky domains. Ten times the inverse rate
   gives ≈99.995% under independence. That is expensive for slow E2E suites, but it buys margin against
   non-independence. Pick one rule. My recommendation: the formula, with a 2× multiplier when runs can't fully reset
   state.
2. **/goal evaluator and the no-Haiku constraint.** /goal's evaluator is the configured "small fast model", which
   defaults to Haiku on the Claude API (https://code.claude.com/docs/en/goal). This lane did not verify whether that
   model can be set to Sonnet 4.6 for /goal alone. If it can't, the skill should avoid /goal as a gate and use Stop hooks
   running scripts.
3. **`isolation: worktree` behaviour for experiment lanes.** Sibling R09 notes cleanup caveats and a bug when spawning
   from non-primary worktrees (`research/mission-skill/09-swarms-workflows-parallelism.md:80`). Lanes that keep
   experimental branches for the ledger need an explicit "don't auto-clean" decision, or a copy of evidence logs into
   `.mission/investigations/logs/`.
4. **Directory naming.** This report uses `.mission/investigations/` per R07. The synthesis notes flag an R01 `mission/`
   vs R07 `.mission/` conflict (`research/mission-skill/99-synthesis-notes.md:34`). Paths in §7 must follow whichever wins.
5. **Tool flags in §7.7** (race detectors, shuffle or repeat flags, Xcode test iteration flags) were not verified here.
   A setup probe should confirm them per stack.
6. **Confirmer cost for S bugs.** Requiring an independent confirmer for every CONFIRMED verdict may be heavy for
   deterministic one-file bugs. Option: at S, red→green by a verifier running the frozen repro stands in for the
   confirmer. I lean toward allowing that, because the two-way intervention *is* the red→green pair when the repro is
   deterministic.
7. **Masked-workaround check (PRF-06) is hard to automate.** Finding "prior workarounds for this symptom" depends on
   commit messages and comments. It may produce noise. Treat it as SHOULD at S/M and MUST at L/XL.
8. **Unverified post claims** in this area (CL-Bench stage numbers, the Parameter Golf "pushed through regression"
   anecdote, Fable "distills rules" as an unprompted trait) should not appear as facts in the skill (§2).
9. **Practitioner-source reliability.** The claude-world guide refers to an official "debugger agent" that doesn't
   appear in the built-in subagent list I fetched (https://code.claude.com/docs/en/sub-agents). Don't depend on built-in
   debugging agents. Ship custom agent files.
10. **Risk of over-process.** The protocol is heavy by design for deep bugs. The synthesizer must make sure SKILL.md
    routes S bugs to the short path (§6.1) so the skill doesn't become the ceremony the user wants to avoid typing out.

## Sources

Primary and near-primary:
- https://code.claude.com/docs/en/best-practices — verification strategies, Stop hook 8-block override, "address the root cause", evidence over assertion, context cost of debugging sessions.
- https://code.claude.com/docs/en/goal — /goal evaluator semantics (small fast model, transcript-only, condition design).
- https://code.claude.com/docs/en/sub-agents — subagent isolation, built-in agents, model inheritance.
- https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues — overlapping bugs, masking workaround, heisenbug behaviour, minimized reproducer, detection tests.
- https://sre.google/sre-book/effective-troubleshooting/ — hypothetico-deductive troubleshooting, pitfalls, problem report shape.
- https://sre.google/sre-book/postmortem-culture/ — blameless postmortems, triggers, review criteria.
- https://how.complexsystems.fail/ — multiple contributors, limits of root cause, hindsight bias.
- https://www.cs.purdue.edu/homes/xyzhang/fall07/Papers/delta-debugging.pdf — Zeller & Hildebrandt, delta debugging (IEEE TSE 2002).
- https://git-scm.com/docs/git-bisect — bisect, run, alternate terms.
- https://arxiv.org/abs/2510.20270 — ImpossibleBench: agents exploiting test cases.
- https://metr.org/blog/2025-06-05-recent-reward-hacking/ — reward hacking examples in frontier models.
- https://arxiv.org/abs/2511.00197 — SWE-bench trajectory study (failed trajectories longer, higher variance; localisation rates).
- https://arxiv.org/abs/2503.13657 — MAST multi-agent failure taxonomy.
- https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html — Google flaky tests (post plus discussion).
- https://research.google/pubs/de-flake-your-tests-automatically-locating-root-causes-of-flaky-tests-in-code-at-google/ — automated flaky root-cause localisation (search snippet only).
- https://developers.cloudflare.com/workers/reference/how-workers-works/ — isolate model and eviction.
- https://developers.cloudflare.com/workers/best-practices/workers-best-practices/index.md — compatibility dates, generated Env types, non-inherited environment config.
- https://developer.apple.com/documentation/xcode/testing-in-simulator-versus-testing-on-hardware-devices — Simulator vs device differences (read via mirror https://github.com/livingston/apple-docs/blob/main/documentation/Xcode/testing-in-simulator-versus-testing-on-hardware-devices.md).

Practitioner and secondary:
- https://www.binaryphile.com/debugging/software-engineering/2026/01/09/agans-debugging-guide.html — summary of Agans' nine rules (the book itself not read).
- https://raw.githubusercontent.com/obra/superpowers/main/skills/systematic-debugging/SKILL.md — systematic-debugging Claude Code skill (root cause first, 3-fix architecture stop, red flags).
- https://claude-world.com/articles/debugging-techniques/ — parallel read-only investigation pattern (critiqued).
- https://community.cloudflare.com/t/cannot-perform-i-o-on-behalf-of-a-different-request/184007 — Workers cross-request I/O error text.
- https://arxiv.org/abs/2603.24631 — TRAJEVAL "Coherence Collapse" (search snippet only; not relied on).

Workspace evidence (read-only):
- `arcwell/docs/operations/incident-drills.md:3-27` — failure classes with automated proof plus live drills.
- `arcwell/docs/product/arcwell-spec.md:1279`, `:1712-1722`, `:2000` — recurrence fixtures, incident ordering, repair-done anti-pattern.
- `arcwell/docs/handoff/2026-08-22-post-deploy-verification.md:190-197` — recurrence signature, missing credentials.
- `arcwell/docs/operations/milestone-ledger.md:57-58` — sibling-defect leakage across review rounds.
- Sibling lane reports and synthesis notes: `research/mission-skill/07-memory-compounding.md`, `research/mission-skill/09-swarms-workflows-parallelism.md`, `research/mission-skill/99-synthesis-notes.md`.
