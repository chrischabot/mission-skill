# Comparison: the mission skill and the drive skill

Written 2026-09-14 against drive at commit 94f49ab and the mission skill as found in the scratchpad copy
(`skills/mission/` plus `research/mission-skill/`). Neither skill was edited. Scratch work lived under
`/private/tmp` and was deleted. Paths below are relative to each skill's root unless they start with
`research/`; mission's research lives in `research/mission-skill/` beside its skill, and drive's in
`/Users/chabotc/Projects/drive/research/`.

Drive's working tree changed while this comparison ran. Between 11:01 and 11:07 another session left
uncommitted edits in `scripts/drive.py`, its test helpers, `hooks/hooks.json`, three templates and the
install scripts. They add a provenance ledger for evidence files, tighter conditions for the Stop gate, a
narrower subagent matcher, a PostToolUse hook and a hygiene baseline, which address clean review findings 3
to 6. The scores below describe commit 94f49ab and give no credit for that unfinished work.

## Summary

Both skills are serious attempts at the same thing, and they reach it from different directions.
Mission is a gated phase machine distilled from a close reading of the owner's arcwell history: its best
parts are the adversarial review economy (refute findings before they block, cap rounds, audit the cheap
graders), the anti-cheating layers around frozen acceptance tests, and a deep bug-hunt protocol. Drive is a
claims-and-evidence machine packaged as a plugin with a tested state tool: its best parts are the status
ladder enforced by code, the kindness ledger for test doubles, the UI contract with a build stamp and
reviewer-captured evidence, and a lesson loop that commits to the skill without a queue.

The decisive difference is fit with the owner's standing rules. Mission builds branches, draft pull
requests, a human queue, human sign-off gates, and batched human design reviews into its core flow, and it
writes in rule identifiers and capitalised MUST/SHOULD throughout. Drive commits to main, asks at most one
question, and writes in plain language. Drive also has more machinery that actually runs. Its weaknesses
are real and verified by the independent clean review (`research/29-clean-review.md`): the gates can be
satisfied by hand-written verdicts, the background launch recipe collides with the harness's worktree
isolation, and several hooks misfire. Those are fixable defects in a sound design. Mission's conflicts with
the owner are structural.

| # | Dimension | mission | drive |
|---|---|---|---|
| 1 | Entry and orchestration spine | 3 | 4 |
| 2 | Classification and conditionals | 4 | 4 |
| 3 | Specification and design | 4 | 5 |
| 4 | Research protocol and ledger | 4 | 5 |
| 5 | Test strategy and harness fidelity | 5 | 5 |
| 6 | Frontend, layout, design quality, UX with vision | 4 | 5 |
| 7 | Adversarial verification | 5 | 4 |
| 8 | Parallelism and swarms | 3 | 4 |
| 9 | State, status, anti-mirage enforcement | 3 | 4 |
| 10 | Failure investigation and compounding lessons | 4 | 5 |
| 11 | Model routing, effort, cost, classifier fallback | 4 | 4 |
| 12 | Enforcement machinery | 3 | 4 |
| 13 | Owner-rule compliance | 2 | 4 |
| 14 | Correctness of harness facts | 3 | 4 |
| 15 | Evals | 2 | 3 |
| 16 | Research depth and source verification | 3 | 5 |
| 17 | Size, readability, maintainability | 3 | 3 |
| | **Total (of 85)** | **59** | **72** |

Recommendation: keep drive as the base, fix the clean review's blocking findings, and port a specific set
of mission's mechanisms into it (listed in "What drive should take from mission"). Do not merge the two
skills wholesale and do not keep both.

## How the comparison was done

I read both SKILL.md files, both READMEs, every agent file on both sides, mission's
`references/conventions.md`, and on each side the references for shapes and intake, orchestration or
definition of done, models, testing, UI verification, review or verification, debugging or lessons,
swarms or parallel work, research, spec and design, and state files, in full or in large sections. I
sampled templates (STATE, STATUS, GOAL, TASK-CARD, brief, gate-verifier, continue-prompt, human-review,
lesson, investigation), mission's `stop-check.sh` and `session-start.sh`, drive's hooks and plugin
manifest, and the synthesis notes on both research sides. Four read-only helper agents audited drive.py
and its tests, ran mission's scripts in a scratch repository, audited both eval suites, and sampled both
research corpora against the live docs; I re-checked the findings from them that decide a score. I read
drive's clean review, which finished while this comparison was running.

Commands run, with results:

| Command | Result |
|---|---|
| `cd /Users/chabotc/Projects/drive && python3 -m unittest discover -s skill/scripts/tests` | 180 tests, OK, 59 s |
| `claude plugin validate /Users/chabotc/Projects/drive/skill` | Validation passed (Claude Code 2.1.263) |
| `bash -n` on all 13 mission shell scripts | all pass |
| `python3 -m py_compile scripts/validate-registry.py`; `node --check scripts/geometry-probe.js` | both pass |
| `python3 -m json.tool` on mission's acceptance.json, settings.hooks.json, settings.guardrails.json, evals.json | all parse |
| `bash scripts/protect-frozen.sh --self-test` (mission) | `self-test: PASS (36 checks)` |
| `bash scripts/flake-runs.sh --p 0.02 --dry-run` (mission) | `149`, as its README predicts |
| `python3 scripts/validate-registry.py --registry templates/requirements.yaml --no-pyyaml` (mission) | `result: PASS (0 failures, 0 warnings)` |
| `bash scripts/init-mission.sh --class M --repo <scratch> --dry-run` (mission) | 30 files planned, agents into `.claude/agents/`, prints settings to merge |
| `claude plugin eval --help` | exists; the docs require v2.1.269 for plugin evals, installed is 2.1.263 |

One asymmetry in the inputs matters for fairness. Mission's brief (`research/mission-skill/00-brief.md`
lines 40-43) told it to use Opus 4.8 and Sonnet 4.6 by version. Drive's brief (`research/00-brief.md`,
the model correction at line 13) told it that the owner's intent is the three tiers and that the aliases
now resolve to Opus 5 and Sonnet 5. Each skill is faithful to its brief. I judge the routing on its
consequences, not on which version it names.

## Harness facts that decide comparison points

Checked against the pages under https://code.claude.com/docs/en/ on 2026-09-14.

| Fact | Documentation | Bearing |
|---|---|---|
| `opus` and `sonnet` resolve to Opus 5 and Sonnet 5 on the Anthropic API | model-config, "Model aliases" table | Both skills state this correctly (mission `references/conventions.md:139-140`; drive `references/models.md:20-22`). |
| Fable 5.1 and Opus 5 run safety classifiers; Fable cyber flags fall back to Opus 4.8, bio to Opus 5; Opus 5 cyber to Opus 4.8; the session stays on the fallback model | model-config, "Automatic model fallback" | Drive's table matches (`references/safety.md:18-21`). Mission's sticky-fallback rule matches (`references/orchestration.md:150-152`). Pinning security lanes to Opus 4.8, as mission does, avoids the Opus 5 classifier altogether. |
| Subagent `isolation: worktree` branches from the repository's default branch unless `worktree.baseRef` is `"head"` | worktrees, lines 117 and 144-147; sub-agents frontmatter table | Mission tells parallel writers to use Agent-tool worktree isolation on branches cut from its integration branch (`references/swarms.md:110-116`); a harness worktree will not start from that branch, so lanes built after the contract milestone do not see it. Drive states the fact correctly (`references/verification.md:103-106`) and never gives an editing agent worktree isolation (`SKILL.md:279`). |
| The Agent tool's per-call `model` accepts aliases only (schema enum `sonnet`, `opus`, `haiku`, `fable` in this session) | sub-agents "Choose a model"; the Agent tool schema | Mission's degraded profile and its downgrade guard pass full model IDs through the Agent tool (`references/models-and-cost.md:324`; `references/frontend-verification.md:357-358`), which the tool cannot accept. Drive says so and routes the one pinned retry through `claude -p` (`SKILL.md:250-254`). |
| Effort cannot be passed per Agent call; it is set in agent or skill frontmatter | sub-agents frontmatter; model-config "Adjust effort level" | Both correct (mission `references/models-and-cost.md:49-50`; drive `references/models.md:39-40`). |
| Sonnet 4.6 supports low, medium, high, max; no xhigh | model-config effort table | Mission correct (`references/models-and-cost.md:44-45`). Drive's Opus agents at xhigh are valid on Opus 5. |
| A user or project agent named `Explore` overrides the built-in and keeps its own model | sub-agents, Explore tab, line 45 | Mission uses this (`agents/Explore.md`, `references/models-and-cost.md:39-40`). Drive only tells the orchestrator not to use Explore (`references/models.md:94-95`). |
| `/goal`'s evaluator reads only the transcript and runs on the small fast model, Haiku by default; `ANTHROPIC_DEFAULT_HAIKU_MODEL` moves it | goal, lines 120 and 165-170 | Both treat `/goal` as a nudge, never a gate. Mission lists the override setting as unverified (`references/orchestration.md:402`); it is documented. |
| Every background session (`claude --bg`, `/bg`) moves into a worktree before editing and commits and pushes its branch when a remote exists, unless `worktree.bgIsolation` is `"none"` | agent-view, lines 490-519 | Breaks drive's launch recipe (`references/long-running.md:85-90`) and its single-checkout design; clean review finding 1. Mission does not use `--bg`. |
| An injected `` !`command` `` in a skill that is not already allowed aborts the whole invocation | skills, lines 659-674 | Drive's start view at `SKILL.md:283` has no `allowed-tools` grant; clean review finding 2. Mission injects nothing. |
| Plugin subagents ignore `hooks`, `mcpServers`, `permissionMode` | sub-agents line 234; plugins-reference line 68 | Drive's agents avoid those fields. Mission's agents are copied into the project, so the restriction does not apply. |
| `SubagentStart` matchers for plugin agents use the scoped name, anchored | hooks, line 2326 | Drive's `hooks/hooks.json:30` and `:42` use `^(drive:)?(verifier|...)$`, which is correct. |
| Explicit ask rules force a prompt even in auto mode | permission-modes, lines 274 and 611 | Mission's guardrails put pushes, deploys, pull requests and workflow edits under `permissions.ask` (`templates/settings.guardrails.json:24-56`), so an unattended run meets prompts nobody answers; mission converts them into human-queue items. |
| After compaction only the first 5,000 tokens of each invoked skill are re-attached, within a shared 25,000-token budget | skills, line 517 | Mission's SKILL.md is 260 lines and mostly fits; drive's is 27 KB, and its re-injection hook restores only from section 7 onward (clean review finding 18). |
| Plugin evals need Claude Code v2.1.269 and use `case.yaml` plus `graders/`; skill-creator's `evals/evals.json` is a separate format | plugin-evals, lines 15 and 25 | Drive's suite is in the plugin-eval format but cannot run on the installed CLI. Mission's `evals/evals.json` is in the skill-creator format. |

## Dimensions

### 1. Entry and orchestration spine

**mission: 3.** The spine is compact and easy to follow: an invocation table with resume, status, retro,
autonomous and lean modes (`SKILL.md:20-29`), fifteen non-negotiables (`SKILL.md:31-76`), one phase table
with a gate verifier per phase (`SKILL.md:112-122`), and a collapse rule by class (`SKILL.md:124-126`).
Run state lives in `.mission/` in the target repository with one canonical names file
(`references/conventions.md:19-56`), and a SessionStart hook prints the resume pointer, rules index and
board after startup, resume or compaction (`templates/settings.hooks.json:3-13`,
`scripts/session-start.sh`). Three things hold it back. The hooks and guardrails are not installed:
`init-mission.sh` prints snippets and the orchestrator must merge them into the project's
`.claude/settings.json` (`SKILL.md:91-94`; the dry run above confirms), which is a protected path. The Stop
hook is inert unless `enforce_stop=1` (`scripts/stop-check.sh:52-55`), and the reference keeps it off in
interactive work (`references/memory-and-lessons.md:196-198`). And the entry asks the user questions a
default could settle: whether to resume or archive an existing mission (`SKILL.md:24`), and to switch model
by hand (`SKILL.md:87-90`). There is no rule for a goal that belongs in another repository.

**drive: 4.** The spine is longer but answers more of the hard questions. It settles where the run lives
before anything else, including a goal for another repository and new work needing a new repository
(`SKILL.md:63-78`), then resume (`SKILL.md:79-84`), a silent intake that ends in a committed GOAL.md whose
intake commit later detects narrowing (`SKILL.md:137-152`), a five-step phase loop (`SKILL.md:168-183`),
and a stop and report section (`SKILL.md:333-359`). Packaging as a skills-directory plugin installs the
re-injection, guard and snapshot hooks automatically (`hooks/hooks.json:4-51`), and the Stop gate travels in
the skill's own frontmatter (`SKILL.md:8-13`). It loses a point for defects at the joints with the harness,
each verified by the clean review: the start view injected at `SKILL.md:283` aborts the invocation in
Manual mode because it has no `allowed-tools` grant (finding 2); the background launch recipe lands the
run in a harness worktree that commits and pushes a branch (finding 1); `/drive --resume` depends on a
goal match it cannot make (finding 24); and the re-injection hook does not restore sections 1 to 6 after
compaction (finding 18).

### 2. Classification and conditionals by shape and size

**mission: 4.** Classification runs on three axes: thirteen shapes with a "gate zero" each
(`references/shapes-and-scope.md:29-43`), a class computed from four scores
(`references/conventions.md:111-129`), and about thirty traits that expand into numbered obligations
(`references/shapes-and-scope.md:120-156`). Forcing rules raise class or add traits from repository
signals, a blind second classifier runs at L and XL (`references/shapes-and-scope.md:49-69`), composition
rules order secondary shapes (`:158-174`), and worked examples cover all five of the owner's goals
(`:206-258`). The conditionals are thorough, including metric definitions for dashboards
(`references/spec-and-design.md`, the FEA section) and parity protocols for moves. The smallest class is
S, and even S keeps a verifier, one review pass and a three-bullet retro (`SKILL.md:124`), preceded by the
probe script and preflight (`SKILL.md:83-90`); a one-line fix therefore spawns at least two subagents. The
obligation codes (`EC-1`, `AU-2`, `XR-5`) are the vocabulary the owner has asked skills not to lean on.

**drive: 4.** Seven shapes with variants for incidents, performance, migration, refactor and upgrade
(`SKILL.md:101-116`), nineteen traits each with signals, gate, phase, artifact and exit check
(`references/intake.md:188-338`), explicit thresholds so traits do not inflate gates (`:340-357`), size set
by the largest structural trigger (`:359-385`), an event table for re-classification (`:543-555`), and
worked classifications for the five goals plus three edge cases (`:579-670`). It has a true XS level: no
`.drive/`, no subagents beyond trait gates, one refutation test seen red then green, and the claim and
evidence in the commit body (`SKILL.md:131`; `references/definition-of-done.md:84-96`). That is the least
ceremony either skill gives a one-line fix. The XS path does not survive a literal reading, though: the
test file counts as the second file that forces S, `references/shapes/fix.md` demands a verifier at every
size, and XS is told to read the heavy references (clean review finding 7). Two shapes in one goal have no
working mechanism in drive.py (finding 11), and the deep-bug example can classify as an incident
(finding 23).

### 3. Specification and design

**mission: 4.** A charter with outcomes, non-goals and stop conditions, a spec with stable identifiers and
an oracle kind per requirement, and a machine-readable registry checked by a script rather than a model
(`references/spec-and-design.md:109-123`; the validator ran clean above). Designs must present two genuine
alternatives or become a task list, irreversible choices get an ADR, backend designs list platform limits
with sources and a single owner per entity and side effect, and frontend designs carry screen specs
written as checkable assertions (`:125-147`). The shape sections are specific, with a Cloudflare limits
table, privacy requirements for uploaded photos, and metric-definition requirements for a dashboard
(`:243-326`). Review uses a rubric, refutes candidate blockers before they block, and caps rounds
(`:148-161`). It loses a point for asking a person to sign off the charter and spec on L and XL
(`references/spec-and-design.md:223`; `references/orchestration.md:104-108`) and for its
EARS and BCP 14 style with requirement codes in the prose.

**drive: 5.** Requirements are headings phrased as claims that could be false, each with scenarios, a
"What would prove this wrong" scenario that a plausible wrong implementation fails, and failure behaviour
(`references/spec.md:88-109`); keys are slugs of the words, so tests, proofs and STATUS share one name
(`:111-130`). The author runs a cheat test, and a fresh reviewer repeats it with a check for owner
conformance, which flags approval queues, schedulers and codes in prose (`:200-252`). Design sizes itself
to the run (`references/design.md:44-71`), gives every write path a failure-semantics row and every
operation an idempotency row (`:119-146`), turns the contract into a package with fixtures and contract
tests in the real runtime owned by one wave-0 maker (`:148-192`), and ends with a scored eleven-dimension
review and a pre-mortem that must name design elements and detection (`:234-310`). Nothing in the spec or
design procedure waits on a person. Its registry support is weaker than mission's validator; it runs a
project's existing registry command rather than shipping one.

### 4. Research protocol and ledger

**mission: 4.** Research opens only on named triggers and a question card naming the decision it
unblocks, with budgets and stop rules (`references/research.md:46-61`). Sources are tiered and claims
graded from a local run down to inference, with triangulation and a mandatory disconfirming query
(`:65-96`). Sub-agent summaries are leads, WebFetch output is recognised as a summary rather than the page,
and a separate fact-checker confirms load-bearing and public claims (`:93-107`). It adds two things drive
lacks: a tech evaluation with frozen criteria and two independent scorers who do not see each other's
scores (`:144-158`), and a public-claims standard in which missing evidence becomes a visible
`[NEEDS-EVIDENCE]` marker that blocks launch by grep (`:170-175`). The weakness is the fact-check itself,
which leans on WebFetch with a request for verbatim sentences (`:93-96`), and the offline fallback that
sends publishable claims to the human queue (`:199-204`).

**drive: 5.** Every question names the decision and the file section it lands in, or it is not researched
(`references/research.md:32-43`). Budgets are tiered with dollar and credit envelopes and an explicit
"assumed pending refutation" exit (`:63-78`). Load-bearing questions run primary, independent and
disconfirming lanes (`:80-91`). The tools table forbids pasting a WebFetch answer or search snippet as a
quotation and requires raw text from `curl` or `tvly extract` saved with a hash (`:93-110`). External
behaviour counts as verified only with docs read in full plus a probe against the real system at the
boundary, and the entry names where a local emulator is kinder (`:126-139`). Freshness uses re-verify
dates and origin validators (`:157-182`), an Opus researcher reconciles lanes, and a grader that never saw
the lane reports re-fetches raw text and searches for each recorded quotation (`:192-252`). Codebase
archaeology produces a short how-it-works note with a drift table (`:254-259`).

### 5. Test strategy and harness fidelity

**mission: 5.** Every gating test cites a requirement and the verifier computes coverage from the code, not
the plan (`references/testing.md:45-60`). The budget is one specific oracle and at most two edge cases per
criterion, with bans on tautological tests and on mocking one's own code (`:64-83`). Acceptance tests are
written before implementation by a separate author, proven red for the right reason, committed alone and
frozen (`:87-102`), and the freeze is held by three independent layers: deny rules, a PreToolUse hook that
parses Bash as well as edits (its self-test passes 36 checks), and a sha256 manifest checked by the
verifier (`:106-148`). In a scratch run the hook let `python3 -c`, `node -e`, `git apply`, `git stash` and
`git reset --hard` through, and left the Stop hook, the lint script and `acceptance.json` editable, so the
manifest check against the base commit is the layer that actually holds. The design earns the score; the
hook needs the same hardening as drive's guard. Held-out scenarios catch special-casing (`:162-167`).
Backend runs are offline with a network guard and Workers tests run in the Workers runtime (`:171-196`).
Flake fixes need n ≥ ln(α)/ln(1−p) clean runs with state reset, computed by a script (`:220-227`). The gate
table by shape and class and the bug and migration protocols are paste-ready (`:285-414`). Harness kindness
is covered by rules rather than a named ledger (`:175-179`).

**drive: 5.** Tests exist to refute claims, at the cheapest layer whose real runtime can refute them, with
a second test on a claim allowed for only three stated reasons (`references/testing.md:46-67`). Budgets are
counted per shape in claims (`:83-100`). The kindness ledger is the best treatment of harness fidelity in
either skill: every double and every local runtime gets rows across eight dimensions, each with a guard, a
live check or an accepted risk (`:120-140`), backed by a limits probe at N and N+1 and named limits in
production code (`:142-154`). That is the owner's bound-parameter incident turned into procedure. The
constraints floor holds without rows and `drive.py guard` refuses loosened checks, skips and removed
assertions (`:156-189`). Fixes are reproduced first and proven red in a `git archive` copy of the pre-fix
commit (`:229-258`), migrations are pinned by goldens and replay (`:260-284`), and the verifier mutates the
five riskiest claims by hand (`:299-324`). Its anti-cheating layer is weaker than mission's: tests are not
frozen, and the guard is a regex pass that the clean review evaded with interpreters and aliases
(finding 9). Flakes get a repeat run and a quarantine rather than a statistical proof (`:205-227`).

### 6. Frontend, layout, design quality, UX verification with vision

**mission: 4.** Three ordered gates: deterministic layout and accessibility checks, a separate vision
verifier on a fixed screenshot matrix, and walkthroughs through the accessibility tree
(`references/frontend-verification.md:60-81`). Two mechanisms are distinctive: an image canary, where the
verifier transcribes a known string and states image sizes before judging, so a blind vision pass cannot
pass (`:75-77`), and an invalid-output rule that rejects "looks good" without element-level observations
(`:72-74`). Taste decisions use pairwise tournaments with position swap (`:121-123`). There is a
browser-side geometry probe script, web and iOS matrix templates, and a capability probe with a fallback
order (`:151-156`). Two things cost it: every L or XL milestone and every consumer greenfield requires a
batched, blinded human review that no agent may pass (`:140-147`; `templates/human-review.md:11-12`), which
is the owner's approval queue in its purest form, and nothing proves the screenshot came from the build
under test.

**drive: 5.** The designer writes a design contract before any UI code, names the generic default it
rejected, and computes contrast ratios for token pairs (`references/ui-verification.md:58-88`;
`agents/designer.md:30-50`). A debug-only state harness opens every declared state, and a build stamp lets
the reviewer prove the capture is HEAD (`references/ui-verification.md:90-117`). The reviewer captures its
own evidence and never grades a maker's screenshot (`:152-157`), runs objective checks with thresholds
before vision (`:202-224`), records a minimum number of anchored observations per screen, checks a
maintained list of templated-default tells (`:226-258`), walks the primary job against a tap budget and
breaks the flow on purpose (`:260-280`), and is calibrated with weights, floors and scored examples
(`:334-373`). Local and live proof are defined for UI (`:375-386`), surfaces cover email and terminal
output (`:388-399`), and the iOS domain pack covers the simulator loop and device-only claims. No person is
asked to approve a design.

### 7. Adversarial verification

**mission: 5.** Verifier briefs may contain only artifact locations, criteria, the evidence bundle and
cited spec text (`references/review.md:41-44`). Review types run only when a trigger holds, one lens per
reviewer and one bounded surface each (`:62-81`). Every candidate blocker or major finding goes to a
separate refuter before it reaches the maker, and only confirmed findings block (`:82-85`). Convergence is
the most carefully argued part of either skill: close a surface when a round has no confirmed blocker or
major, cap rounds by class, scope re-review to the fix, stop patching when a defect class recurs, and audit
the instruments when late findings are about the tests (`:114-135`), all grounded in the measured defect
counts of eighteen arcwell review rounds (`:137-152`). Cheap graders are watched with seeded canaries and
blind re-grades by a stronger agent (`references/models-and-cost.md:87-98`; `references/review.md:297-301`).
The weaker points are the per-task verifier on Sonnet 4.6 for Sonnet makers, and the escalation of an open
blocker at the cap to a human.

**drive: 4.** The handoff is built from files, with an explicit list of what a verifier must never receive
(`references/verification.md:50-81`). Verdict validity is stricter than mission's: a pass needs the test
command in `ran` at exit 0, a refutation attempt per claim at confidence 75 or above, and resolved kindness
entries, and a malformed pass is rejected (`:108-142`). Reviewers are told to report everything with
severity and confidence and filtering happens afterwards (`:236-250`); two rounds of dismissed findings are
treated as validating rather than verifying (`:223-226`). The final audit hunts mirages by breaking a
production line in a copy and expecting red (`references/definition-of-done.md:273-287`). Two verified
defects keep it below mission. The snapshot hook tells every background reviewer to revert the
orchestrator's STATE.md edits and never voids a verdict (clean review finding 5), and nothing binds a
verdict file to the agent that should have written it (finding 3). Its review panel settles splits with a
fresh verifier (`references/parallel.md:312-390`) but has no refutation step for findings before they
reach the maker.

### 8. Parallelism and swarms

**mission: 3.** The swarm reference is rich: a stance of parallel readers and a single writer per shared
surface, a pattern table with preconditions and failure modes (`references/swarms.md:46-73`), a go/no-go
checklist and a frozen contracts file before parallel writing (`:77-91`), per-lane runtime isolation for
ports, databases and simulators (`:119-122`), serial integration by a separate integrator with a
merged-result verifier (`:123-132`), a stall rule (`:150-154`), and an ownership overlap script. Its core
mechanism does not work as written: writers get Agent-tool worktree isolation on branches cut from the
integration branch (`:110-116`), but the harness branches those worktrees from the default branch, so they
miss the contract milestone. And the design lives on branches by intent: an integration branch, lane
branches, and work that ends in draft pull requests (`references/conventions.md:176-183`;
`references/orchestration.md:117-121`).

**drive: 4.** Makers edit one shared checkout on the current branch with disjoint ownership, never run git,
request wiring and dependencies instead of touching shared files, and the orchestrator integrates alone,
runs full gates plus a real-runtime check, commits per package by explicit path, and runs an orphan audit
before any verifier (`references/parallel.md:18-25`, `:27-77`, `:149-182`). Workflows are used only for
read-only fan-out, with a reason given (`:89-111`). Worktrees exist only for experiment arms, bisects and
hypothesis probes under `/private/tmp` and are removed in the same step (`:238-293`). It loses a point for
the experiment arms still creating `drive/<slug>` branches and merging them with `worktree-land`
(`:260-272`; clean review finding 12), for the hygiene check that orders the removal of worktrees and
untracked files the run did not create (finding 6), and for giving no guidance on runtime isolation when
parallel makers run focused tests against shared local services.

### 9. State and status tracking; anti-mirage enforcement

**mission: 3.** STATUS says what is done and STATE what is true, with one home per kind of fact and a single
writer (`references/memory-and-lessons.md:33-72`). Facts need evidence, a level and a verified date,
hypotheses need a falsifying check, rules need instances, and `memory-lint.sh` checks those fields
(`:76-99`, `:120-131`). A curator pass with an information-loss verifier prevents lossy rewrites
(`:271-311`). `acceptance.json` starts every check at false and only a verifier's transcribed verdict flips
it, and live gates stay `PENDING-LIVE` (`references/conventions.md:91-100`). What it lacks is the owner's
status ladder: there is no per-claim Missing to Done scale, only gate and task states. Enforcement is
mostly prose. The lint checks memory fields, not that a PASS has a verifier report, and the Stop freshness
check is opt-in (`scripts/stop-check.sh:52-55`).

**drive: 4.** STATUS rows are behavioural claims on the owner's ladder, Missing through Done, rows are never
deleted, and a claim sits at the weakest of its evidence (`references/definition-of-done.md:33-74`). Each
rung requires specific evidence tokens (`references/state-files.md:212-241`), and `drive.py lint`
enforces them, tested by 180 unit tests. Targets are fixed at intake and every narrowing needs a decision
in the same commit, found by diffing against the intake commit (`references/definition-of-done.md:214-243`).
STATE carries a workaround ledger and boundary events (`templates/STATE.md:23-40`), and the report is
derived from files (`SKILL.md:345-353`). The provenance gap stops it at 4: a hand-written verdict and final
audit let `lint --final`, the Stop gate and `drive.py end` close a run in which nothing ran, and the Stop
gate opens on a self-declared `blocked` or `stalled` status (clean review findings 3 and 4).

### 10. Failure investigation and compounding lessons

**mission: 4.** The debugging reference is the deeper of the two for a hunt: a failure record before code,
a "check the plug" list for stale builds and wrong targets (`references/debugging.md:51-60`), a table of
hard-bug classes with amplification, isolation and the symptom-patch trap for each (`:68-79`), mechanical
isolation before theorising (`:100-111`), a hypothesis ledger with predictions written before experiments
and a two-way confirmation by a separate confirmer (`:115-135`), statistical proof for flakes (`:157-173`),
a sibling sweep and a check for masked earlier workarounds (`:181-188`), and a taxonomy of process
failures with a mechanical control for each (`:216-239`). Lessons wait in an inbox until retro and are
promoted only when eight criteria hold, including an eval case that passes with the skill and fails without
it (`references/memory-and-lessons.md:143-180`). That eval criterion is excellent, but nothing in the repo
can run it, the seven seeded lessons are marked advisory (`references/lessons.md:8-9`), and "second time is
the bug" appears only as an escalation trigger, not as a ledger.

**drive: 5.** Failure events are defined, and "second time is the bug" is a workaround ledger: every retry,
sleep, wider mock or re-dispatch gets a row, and count two stops work and opens an investigation
(`references/lessons.md:42-54`; `SKILL.md:294-297`). The investigation record has a gate per stage and a
four-part test for a root-cause fix (`references/lessons.md:56-79`, `:107-115`). Distillation insists on
predictive, checkable, scoped rules and prefers checks to prose (`:117-166`). Routing sends project facts,
platform constraints, tool quirks, general rules and owner preferences to different homes (`:168-184`).
The loop's write scope is narrow (`:186-206`), a grader dedupes and an auditor accepts with an injection
guard (`:208-248`), and each lesson lands as one commit with project and run trailers that consolidation
counts, with `git revert` as the undo and no queue (`:250-328`). Every brief must quote the applicable rules
(`:330-337`). The six seeded lessons are the owner's real incidents (`references/lessons/general.md:15-73`).
It is less thorough than mission on hard-bug classes and statistical flake proof.

### 11. Model routing, effort, cost, and classifier fallback

**mission: 4.** Twelve roster agents, one per model, effort and permission profile, pinned by full ID, with
a preflight script that fails on aliases (`references/conventions.md:146-165`;
`references/models-and-cost.md:23-45`). An escalation ladder with fresh context per rung (`:54-75`), guards
on every downgrade including seeded canaries, sampled blind audits and a three-gate agreement test before
moving a role down (`:78-108`; `references/orchestration.md:171-173`), budgets with caps and phase
allocations (`references/models-and-cost.md:131-172`), and Lean and Degraded profiles (`:318-328`). The
classifier rules pre-route offensive work to Opus 4.8, which avoids the Opus 5 classifier entirely, log
every fallback and re-select the model at phase boundaries (`:110-129`). Against that: it pins older
models, and Sonnet 4.6 lists at 3 and 15 dollars per million tokens against Sonnet 5's 2 and 10 in drive's
table (`references/conventions.md:133-137`; drive `references/models.md:28-32`); two routes pass full IDs
through the Agent tool, which it cannot accept; and the per-spawn ledger rows are bookkeeping a long run
will pay for.

**drive: 4.** Routes by the shape of the work, writes aliases only, and pins one ID for the classifier retry
(`references/models.md:12-26`). The roster gives a reason for each role's model and effort (`:37-58`), per-call
overrides are limited to a short table (`:75-95`), and grading runs in tiers from scripts to Sonnet at low
effort for binary checklists, Opus for judgment and Fable for the final verdict (`:97-117`). The safety
reference keeps attack material inside Opus subagents, never asks for reasoning text because of the
reasoning-extraction refusal, and tells a classifier decline from real errors (`references/safety.md:33-60`,
`:72-87`). The facts check out against the docs. It shares mission's score because the budget is never
enforced by anything (clean review finding 26), the writer runs on Opus against the owner's volume-on-Sonnet
intent without a recorded reason, and the Opus 4.8 retry runs as a nested `claude -p` session outside the
parent's guards (finding 28).

### 12. Enforcement machinery

**mission: 3.** Thirteen shell scripts, a Python registry validator and a browser geometry probe cover
initialisation, preflight, repository signals, gate runs, memory lint, session start, the Stop check, the
frozen-path hook and manifest, test-diff grep, flake runs, ownership overlap and headless waves. The README
says none had been executed when written (`README.md:77-78`). Run for real in a scratch repository with
the stock macOS bash 3.2 and BSD tools, all of them worked, and both hooks follow the documented Stop and
PreToolUse contracts, which is more portability than drive has. What they enforce is thin. Only
`protect-frozen.sh` (exit 2) and `stop-check.sh` (a JSON block, and only with `enforce_stop=1`) stop
anything, and both are easy to get around: the Stop check blocks a freshly initialised mission because
templates were copied after STATUS.md, clears on a bare `touch` of the two files, ignores uncommitted
edits, and can be replaced by `exit 0` without the frozen-path hook objecting; `memory-lint.sh` passes
`Evidence: TODO` and the unfilled templates; `check.sh` enforces no timeout on stock macOS;
`test-diff-grep.sh` misses a weakened assertion. `init-mission.sh` does not copy `run-wave.sh` or
`geometry-probe.js` into `.mission/bin/`, although the references tell the orchestrator to run them from
there (`scripts/init-mission.sh:162-164`; `references/swarms.md:37`). The only automated test is the
frozen-path self-test, and installation is manual: agents copied into the project, hooks and permissions
merged by hand.

**drive: 4.** One state tool, `scripts/drive.py`, provides init, start view, lint by gate, final lint, the
Stop hook, the PreToolUse guard, read-only snapshots, the floor guard, worktree landing, and lesson check
and commit, with 180 passing tests; hooks ship in the plugin (`hooks/hooks.json`) and `claude plugin
validate` passes. The clean review found the machinery sound and the joints weak: the guard lets read-only
agents write through interpreters and lets makers delete anything (finding 9), the snapshot misfires on the
orchestrator's own edits (finding 5), hygiene treats the owner's worktrees and untracked files as run
debris (finding 6), the Stop hook's 60-second timeout fails open when a registry run takes longer
(finding 15), and paths are hard-coded to `~/.claude/skills/drive`, `~/Projects` and `/private/tmp`
(finding 16). It is tested; mission's is not.

### 13. Owner-rule compliance

**mission: 2.** It is strong on anti-mirage (UNVERIFIED is never PASS, live gates stay pending) and never
waits on `/goal`. It breaks three of the owner's rules by design. Approval queues: autonomous mode turns
every irreversible action into a `BLOCKED-HUMAN` item in a human queue (`SKILL.md:28`;
`references/orchestration.md:117-121`; `templates/continue-prompt.md:28-31`), L and XL specs need human
sign-off, and design quality needs a batched human review that no agent may pass
(`references/frontend-verification.md:140-147`). Branches: work lands on `claude/<mission>/...` branches
and ends in draft pull requests (`references/conventions.md:176-180`; `SKILL.md:189-190`). Plain language:
by one grep run over both skills' markdown, mission carries about 1,150 rule and obligation identifiers,
597 capitalised MUST, SHOULD or MAY tokens and 332 em dashes; drive has none of the three. It also asks up
to three questions over two rounds (`SKILL.md:60-61`) where the owner wants one. There is no status ladder,
and "second time is the bug" survives only as an escalation trigger.

**drive: 4.** The contract states the owner's rules in his words: commit on the current branch, never
create or push branches, never leave a worktree, never build a queue, never wait on a schedule, never widen
a test to get green (`SKILL.md:39-52`). There is one question, asked only when no undo exists
(`references/intake.md:507-531`), the ladder and refutation tests are the owner's own, the workaround ledger
is his "second time" rule, and the markdown has no rule identifiers and no em dashes by grep. It loses a
point for paths that break those rules in practice: the background launch lands work on a pushed harness
branch (clean review finding 1), experiment arms create `drive/*` branches and two recipes push
(finding 12), the hygiene check tells the run to remove or commit the owner's own work (finding 6), and
`install.sh --apply-settings` changes every session on the machine (finding 17).

### 14. Correctness of harness facts

**mission: 3.** Most of what it states is right: alias resolution, sticky classifier fallback,
frontmatter-only effort, the Explore override, Sonnet 4.6's effort levels, `/goal`'s transcript-only
evaluator, the eight-block Stop cap, and the SessionStart compact matcher. It flags many details as
unverified in tables at the end of each reference, several of which are in fact documented (the Stop
decision JSON and `stop_hook_active`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`, `CLAUDE_PROJECT_DIR`), which is
honest but noisy (`references/memory-and-lessons.md:452-466`; `references/testing.md:470-486`). Two load-bearing
statements are wrong: Agent-tool worktree isolation does not branch from its integration branch
(`references/swarms.md:110-116` against worktrees lines 117 and 144-147), and the Agent tool does not take
full model IDs (`references/models-and-cost.md:324`). Its guardrail design also misses that ask rules
prompt even in auto mode.

**drive: 4.** The clean review checked agent frontmatter, hook events and matchers, effort levels,
environment variables, aliases and fallback targets and found them correct (`research/29-clean-review.md`
line 7 and the Notes), and my own checks agree: plugin agents avoid the ignored fields, the SubagentStart
matcher uses the scoped name, isolation branches from the default branch (`references/verification.md:103-106`),
the Agent tool takes aliases only, and `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`, `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`
and `CLAUDE_CODE_RETRY_WATCHDOG` behave as described. It missed four harness behaviours that matter: the
injected-command abort, background worktree isolation, the documented Workflow opt-ins (invoking `/drive`
is not one; finding 29), and that `--resume <name> --bg` starts a copy (finding 22).

### 15. Evals

**mission: 2.** Eight prompts with assertions in the skill-creator format, one per owner goal plus a typo
fix, an overnight upgrade and a review-round question (`evals/evals.json`). Nothing in the repository runs
them and no run is recorded. Every case has `"files": []`, yet five of the eight need an existing
repository or prior state to mean anything. Every assertion is prose for a judge to interpret, several key
on the skill's own vocabulary rather than behaviour, and a plain session would pass the review-round and
typo cases. Four assertions encode behaviour the owner forbids: human approval of cutovers
(`evals/evals.json:52`), human approval before publishing (`:65`), and ending in a draft pull request on a
`claude/` branch (`:82`, `:86`). The pinned model IDs are asserted directly (`:16`).

**drive: 3.** Seventeen cases in the plugin-eval format, whose fields match the documentation, each with a
scaffold, a prompt and several graders; about ninety graders, of which six are model-judged and the rest
regex, tool-use or file checks. They cover classification of all five owner goals and behaviours that
matter to him: XS restraint, mirage refusal, lowering the bar, second time is the bug, verifier isolation,
harness kindness, lesson dedupe and consult, injection, and restraint when the iOS example is only an
example. All seventeen scaffolds run and the seeded fixtures lint clean. It cannot run on the installed
CLI, which lacks the `--trust-plugin` flag the README passes and predates the v2.1.269 requirement, and the
run ledger is empty (`evals/ledger.md`). Several graders pass on a run that does nothing (mirage-refusal,
lowering-the-bar, example-only-restraint) or fail a correct run, the classification cases stop at intake,
and no case tests the no-queue, no-branch or plain-language rules (clean review finding 27).

### 16. Research depth and source verification

**mission: 3.** Twelve focused reports of 700 to 1,150 lines each, a skill architecture note and synthesis
notes (`research/mission-skill/`). The standout is the arcwell practice report, which grounds the review
caps, pending-live gates and walking skeleton in the owner's own disposition files
(`research/mission-skill/12-arcwell-practice-evidence.md`; used at `references/review.md:137-152` and
`references/lessons.md:66-80`). The reports cite 319 distinct URLs and grade every claim on one fixed scale
(`research/mission-skill/01-orchestration-control.md:77`), and every reference ends with an evidence list
and an "unverified" table. There was no verification pass: the synthesis notes record verdicts without
re-checking them, several lanes were read in part (`research/mission-skill/99-synthesis-notes.md` records
"read §4-6" and similar), the worktree base-branch question was flagged as unverified in research
(`research/mission-skill/09-swarms-workflows-parallelism.md:665`) and then built on anyway, and several
documented facts were filed as unverified.

**drive: 5.** Twenty-eight reports of roughly 35 to 140 KB each covering harness primitives, shapes,
intake, architecture, research, routing, verification, tests, UI, state, lessons, parallel work,
orchestration, long runs, the safety boundary, three domains, migration, bug hunts, the skill ecosystem and
an extraction from agent-skills (`research/01` to `23`), with 469 distinct URLs, then a source verification
that checks about fifty claims with verdicts (`research/22-source-verification.md`), a synthesis (`24`),
three integration reviews on conflicts, coverage and style (`26` to `28`), and an independent clean review
(`29`). The verification pass caught its own research's one wrong harness claim, that classifier fallback
is not automatic in headless runs (`research/15-safety-boundary.md:7` overruled at
`research/22-source-verification.md:11`), before the skill was written, and the skill follows the
correction (`references/safety.md:13-24`). The integration reviews visibly changed the skill; for example
the ruling that `maxTurns` cannot be raised per call (`research/26-review-conflicts.md:468`) is in
`references/parallel.md:45`. A sampled check of ten harness claims from each corpus against the docs found
drive's correct apart from the one it had already corrected. Its corpus does not have mission's report on
the owner's practice, though its seeded lessons and brief carry the same incidents.

### 17. Size, readability, maintainability

**mission: 3.** About 116,000 words of markdown in the skill; SKILL.md is 260 lines. One canonical names
file that wins over every reference is a good maintenance choice (`references/conventions.md:1-4`). The
cost is readability: dense tables, rule codes that references cite across files, capitalised normative
words, and 332 em dashes, all things the owner reads as noise. The scripts are small and separate but
untested.

**drive: 3.** About 153,000 words of markdown; SKILL.md is 383 lines and 27 KB, larger than what survives
compaction. The prose is plain and each reference opens with when to read it and what it decides, which
makes it readable one file at a time. Maintenance is harder: one 4,142-line Python file, a dozen
contradictions between files that the clean review lists (finding 13), and owner-specific history embedded
in shipped files (clean review Notes).

## The three biggest strengths of each

**mission**

1. A review economy that stops on evidence rather than exhaustion: refute candidate blockers before they
   block, cap rounds by class, scope re-review to the fix, turn a recurring defect class into a design
   review, and audit cheap graders with seeded canaries and blind re-grades (`references/review.md:82-135`;
   `references/models-and-cost.md:87-98`).
2. Layered protection for acceptance tests: a separate test author before implementation, red proven for
   the right reason, then deny rules, a tested PreToolUse hook and a hash manifest, plus held-out scenarios
   (`references/testing.md:87-167`; `scripts/protect-frozen.sh`).
3. A bug-hunt protocol that behaves like an experienced engineer: check the plug, class-specific tactics,
   isolation before theories, two-way confirmation by someone else, statistical proof for flakes, sibling
   sweep, masked workarounds, and a process-failure taxonomy (`references/debugging.md:51-239`).

**drive**

1. The owner's status ladder with evidence tokens per rung enforced by a tested lint, fixed targets, and
   narrowing detected against the intake commit (`references/definition-of-done.md:33-243`;
   `references/state-files.md:212-241`).
2. Harness fidelity and UI truth: the kindness ledger and limits probe for test doubles, and a design
   contract, build stamp and reviewer-captured evidence for anything a person looks at
   (`references/testing.md:120-154`; `references/ui-verification.md:58-157`).
3. Fit with how the owner works: plain language, one question, commit to main, no queues, and a lesson loop
   that commits verified rules to the skill with a revert as the undo (`SKILL.md:24-54`;
   `references/lessons.md:168-328`).

## The three biggest weaknesses of each

**mission**

1. It conflicts with the owner's rules at its core: branches and draft pull requests, a human queue, human
   sign-off and batched human design review (dimension 13).
2. Its parallel build rests on a wrong harness fact: Agent-tool worktrees do not branch from its integration
   branch, and the Agent tool cannot take the full model IDs its degraded routes pass (dimension 14).
3. Enforcement is mostly prose and manual setup: no status ladder, an opt-in Stop check, hooks and
   permissions merged by hand, untested scripts, and evals nothing can run (dimensions 9, 12, 15).

**drive**

1. The gates can be passed without the work: verdicts and audits carry no provenance, and the Stop gate
   opens on a self-declared status (clean review findings 3 and 4).
2. The joints with the harness break real runs: the injected start view aborts in Manual mode, background
   launches land in a pushed worktree branch, the snapshot hook misfires, and hygiene checks target the
   owner's own state (findings 1, 2, 5, 6).
3. Size and drift: a 27 KB spine that does not survive compaction, contradictions across files, an XS path
   that cannot be followed literally, and an eval suite that cannot run on the installed CLI
   (findings 7, 13, 18, 27).

## What drive should take from mission

Each row names the mission source, the drive destination, and exactly what to take. The first three are
the ones that matter most.

| Priority | Take | From mission | Into drive | What exactly |
|---|---|---|---|---|
| 1 | Frozen acceptance tests | `references/testing.md:87-148`; `scripts/protect-frozen.sh` (with `--self-test`); `scripts/frozen-manifest.sh`; `scripts/test-diff-grep.sh`; `templates/TEST-DISPUTE.md` | `references/testing.md` sections 8 and 9; a `frozen` role in `drive.py hook-guard`; `drive.py guard` | At M and above, have `drive:severe-tester` write the refutation tests from the claims before the implementer starts and prove them red; record their paths in a frozen list with a sha256 manifest; block maker writes to those paths in `hook-guard` (reuse protect-frozen.sh's Bash parsing and its self-test cases as unit tests); have the verifier check the manifest against the base commit; replace test edits by makers with a dispute that goes to the auditor. Do not port the hook's gaps: also block interpreters with inline code, `git apply`, `patch`, `git stash` and `git reset` on frozen paths, protect the enforcement scripts and the manifest's own `--force` rewrite, and add a weakened-assertion check that mission's grep lacks. This also narrows clean review finding 9. |
| 2 | Refutation before blocking, and convergence rules | `references/review.md:82-85` and `:114-135`; `templates/refuter.md`; `templates/disposition.md`; the eighteen-round evidence at `references/review.md:137-152` | `references/verification.md` sections 6 and 7; `references/parallel.md` section 13 | Send every blocking gap from a reviewer (UI, security, design, panel) to a fresh verifier that tries to disprove it before the maker sees it; close a surface when a round has no confirmed blocking gap; scope later rounds to the fix and its callers; when the same defect class is confirmed in two rounds, stop patching and open a design investigation; when late findings are mostly about the tests, run one instrument audit instead of another round. Keep the evidence box as the reason. |
| 3 | Hard-bug depth | `references/debugging.md:51-79` (check the plug, bug classes), `:115-135` (ledger, two-way confirmation), `:157-173` and `scripts/flake-runs.sh` (statistical proof), `:181-188` (sibling sweep, masked workarounds), `:216-239` (process failures) | `references/shapes/fix.md`; `agents/investigator.md`; `references/testing.md` section 10; `references/lessons.md` section 1 | Add the check-the-plug list to the investigator's first step; add the bug-class table as a lookup; require a separate agent to confirm a mechanism by removing and re-introducing the cause; replace "repeat 20 times" with n ≥ ln(α)/ln(1−p) clean runs and ship flake-runs.sh; add the sibling sweep and the masked-workaround check to the fix phase; add the process-failure classes as failure events with a mechanical control each. |
| 4 | Watching the cheap graders | `references/models-and-cost.md:87-98` (seeded canaries, sampled blind audit); `templates/audit-prompt.md`; `references/orchestration.md:171-173` (downgrade experiment) | `references/models.md` section 5; `references/verification.md` section 11 | Plant one known-bad item in each `drive:grader` batch (the canary never named in the brief) and void the batch on a miss; re-grade a sample of grader passes with a verifier blind to the first answer; record agreement as evidence in the retro. |
| 5 | Lessons proven by evals | `references/memory-and-lessons.md:155-175` (criteria d and h, retire on baseline pass) | `references/lessons.md` sections 6, 9 and 10 | Make the auditor's acceptance require an eval case that fails without the rule where one is possible, and retire a lesson whose case passes on the no-plugin baseline arm that `claude plugin eval` already reports. |
| 6 | Vision verification guards | `references/frontend-verification.md:72-77` (invalid output, image canary), `:121-123` and `templates/design-rubric.md` (position-swapped pairwise tournament), `scripts/geometry-probe.js` | `references/ui-verification.md` sections 6, 7 and 11; `agents/ui-reviewer.md` | Before judging, the reviewer transcribes a known string from each image and states its pixel size, or the round is blocked; use pairwise, position-swapped comparisons for direction choices instead of absolute scores; adopt the geometry probe as the web objective check for overflow, clipping, overlap and target size. Leave out the human batch. |
| 7 | Security lanes off the Opus 5 classifier | `agents/mission-builder.md` and `agents/mission-critic.md` pinned to `claude-opus-4-8`; `references/models-and-cost.md:112-125` | `agents/`; `references/safety.md` section 6 | Ship Opus 4.8 twins of the investigator and security reviewer as agent files and spawn them through the Agent tool for the retry, replacing the nested `claude -p` session (clean review finding 28). |
| 8 | Public claims and technology choices | `references/research.md:144-158` (two blind scorers), `:170-175` and `templates/positioning.md` (`[NEEDS-EVIDENCE]` marker) | `references/research.md` section 15; `references/shapes/publish.md`; `references/design.md` section 8 | For an irreversible technology choice, freeze criteria and weights, then have two agents score without seeing each other. On sites, write a visible marker wherever evidence is missing and make a grep for it a blocking objective check. |
| 9 | Dashboard metric definitions | `references/spec-and-design.md`, FEA section (source, formula, unit, time zone, window, refresh, empty and partial data, oracle fixture) | `references/spec.md` section 11; `references/shapes/feature.md` | Add a trait row: every displayed metric is a claim with those fields and a fixture with known values. |
| 10 | Cheap exploration and runtime isolation | `agents/Explore.md`; `references/models-and-cost.md:39-40`; `references/swarms.md:119-122` | `install.sh`; `references/parallel.md` section 5 | Install a user-level `Explore` agent pinned to Sonnet so any accidental built-in exploration stays cheap; give makers that run local services a port offset, database name and simulator per package. |

Mission's memory curator pass with an information-loss verifier (`references/memory-and-lessons.md:271-311`)
is also worth reading when drive's STATE.md size control is revisited, and its registry validator is a
reasonable default for projects without one.

## What drive has that mission lacks

- The owner's ladder with code-enforced evidence per rung, rows that are never deleted, and narrowing
  detected against the intake commit (`references/definition-of-done.md`; `drive.py lint`).
- A kindness ledger and limits probe for every test double and local runtime (`references/testing.md:120-154`).
- An XS level with no run directory and the evidence in the commit body (`SKILL.md:131`).
- A design contract with a rejected-default paragraph, a state harness and a build stamp, and a UI reviewer
  that captures its own evidence (`references/ui-verification.md:58-157`).
- A workaround ledger for "second time is the bug" (`references/lessons.md:42-54`).
- A lesson loop that routes, dedupes, verifies and commits to the skill without a queue, with rejected and
  retired records (`references/lessons.md:168-328`).
- Plugin packaging with hooks that install themselves, and a state tool with 180 tests.
- Where-the-run-lives rules, including launching in another repository or creating a new one
  (`SKILL.md:63-78`).
- A shared-checkout parallel model with no branches (`references/parallel.md`).
- A final audit that hunts mirages by mutation in a copy (`references/definition-of-done.md:245-316`).
- Capability preflight that lowers the ceiling of claims it cannot verify (`references/capabilities.md`).
- Domain packs for iOS, Cloudflare and the web, and references for security, observability and the
  Operational rung.
- Guidance tuned to current models: report every finding and filter afterwards, never ask for reasoning
  text (`references/verification.md:236-250`; `references/safety.md:56-60`).
- Plain language throughout.

## Recommendation

Use drive as the base. The argument rests on three points.

First, the owner's rules are not preferences a later pass can bolt on. Mission's branches, pull requests,
human queue, sign-off gates and human design batch are woven through its phase table, its guardrail
settings, its autonomous mode, its swarm model and its evals. Removing them means redesigning integration,
release and UI acceptance, and rewriting its prose out of rule codes. Drive already embodies those rules,
and where it breaks them the breaks are specific and listed.

Second, drive's defects are at the joints and have concrete fixes, most of them in the clean review:
provenance for verdicts recorded outside the orchestrator's reach, `worktree.bgIsolation: "none"` and a
permission mode in the launch settings, an `allowed-tools` grant for the start view, a baseline of the
owner's worktrees and dirty paths at init, and an XS fast path at the top of the intake section. Mission's
defects include a wrong assumption about how the harness creates worktrees, which its parallel build
depends on.

Third, mission's best ideas are portable because they are mechanisms, not architecture. Frozen tests with a
tested hook, refutation before blocking, convergence caps, grader canaries, and the bug-hunt protocol each
fit into an existing drive reference and agent without changing drive's shape.

Merging the two wholesale would double the size of an already large skill and import mission's vocabulary.
Keeping both would split lessons and evals across two loops, and the owner would have to choose between
them for every goal. Port the ten items above, in priority order, after the clean review's blocking
findings are fixed.
