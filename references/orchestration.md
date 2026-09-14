# Orchestration and control loop

Phases 0–9 and their gates, stop rules, loops, work breakdown, briefs, long-running execution, human checkpoints,
guardrails and the safety boundary. Names, states and IDs: `references/conventions.md` (it wins on any conflict).

## When to load

| Moment | Read |
|---|---|
| Phase 0 Intake (gate checklist) | Procedure P1, Core rules O, H, B |
| Entering any phase / closing a gate | Procedure P2 gate table, rules GT |
| Phase 4 Plan | W1–W6, P3, `templates/PLAN.md` |
| Phase 5 Build: dispatching, integrating | W4–W10, P4, `templates/brief.md` |
| Declaring or judging any loop | S1–S7, LP1–LP3, P5, `templates/loop.md` |
| Session end, ~60% context, resume, headless or Routine run | L1–L7, P6, `templates/HANDOFF.md`, `templates/continue-prompt.md` |
| Anything irreversible or externally visible; autonomous mode | H1–H5, P7, `templates/settings.guardrails.json` |
| Phase 8 Release | P8 |
| Classifier refusal, model drift, security-offensive work | B1–B4 (full fallback protocol: `models-and-cost.md` CF1–CF6) |

## Core rules

### Control plane and orchestrator (O)

- **O1 MUST** keep mission truth in `.mission/` files (conventions §2): `STATUS.md` = work, `STATE.md` = knowledge,
  `acceptance.json` = done, `PLAN.md` = milestones + DAG. Never only in chat, a `/goal` string or a transcript. Never
  use STATE.md as the task board.
- **O2 MUST** run the loop *read → decide → dispatch → integrate → verify → write → continue | stop*. Write STATUS.md
  before every dispatch wave and after every integration. If the session died now, the files must be enough to resume.
- **O3 MUST NOT** implement changes itself on M+ missions. The orchestrator plans, briefs, integrates ≤ ~30 lines of
  glue, adjudicates and writes control files.
- **O4 MUST** record class, shape and traits at intake (`PROFILE.yaml`, STATUS header). Reclassify upward at any gate;
  downward only with a D-entry.
- **O5 MUST** expand the direction into `CHARTER.md` (M+) or `TASK-CARD.md` (S) before planning (content rules:
  `spec-and-design.md`).
- **O6 MUST** log every non-trivial gap as an `A-NN` assumption (reversal cost, how to verify) instead of asking, unless
  H3 applies.
- **O7 MUST** write a D-entry for every model downgrade, profile change, scope cut, gate waiver, review-round cap,
  reclassification and check change.
- **O8 SHOULD** brief Fable 5.1 and Opus 4.8 agents with outcomes, not step lists; Sonnet 4.6 briefs SHOULD carry
  explicit steps.
- **O9 MUST NOT** ingest raw logs or whole files. Read summaries plus paths; delegate heavy reading to `mission-scout`.

### Gates (GT)

- **GT1 MUST** gate every phase. A gate is `PASSED` only with cited evidence and a verdict from a roster agent that did
  not author the artifact (gate verifier column in P2). The orchestrator transcribes the verdict and cites the report.
- **GT2 MUST NOT** advance past a gate in `PENDING` or `BLOCKED(<reason>)`. A waiver is `PASSED-WITH-WAIVER(D-id)` whose
  D-entry names the risk and the owner. `PENDING-LIVE` MAY advance only when the mechanism is delivered, the live run is
  impossible before release, and a STATUS Risks line tracks it.
- **GT3 MUST** loop back to the earliest invalidated phase when later evidence breaks an earlier artifact (a build
  finds a design flaw → Design). Do not patch around it in Build.
- **GT4 MUST** keep `acceptance.json` checks at `passes:false` until a verifier verdict is transcribed. Scripts
  (`check.sh`, Stop hooks) produce evidence; they never flip `passes`.
- **GT5 SHOULD** report at each gate in ≤10 lines: gate state, evidence pointers, defaults taken, what runs next, spend.

### Loops (LP)

- **LP1 MUST** declare every *make → verify → feedback* cycle (task iteration, gate review, design tournament,
  hypothesis hunt, content draft, parity run) in `.mission/loops/<loop-id>.md` from `templates/loop.md` before
  iteration 1: criteria, ignore list, caps, futility signals, maker and verifier agents, engine.
- **LP2 MUST** count iterations, cost and wall-clock in the loop file and STATUS Board (`Iter n/cap`), never from
  narration. Criteria and caps are frozen after iteration 1 (S7).
- **LP3 MUST** track the best iteration (most required criteria PASS, then fewest regressions) and ship or escalate
  from it, not from the last one.

### Stop rules (S1–S7, evaluated after each verifier verdict, in this order)

| Rule | Fires when | Loop stop state | Action |
|---|---|---|---|
| **S1 Success** | Every required criterion PASS from a verifier that did not produce the artifact, evidence attached | `STOP-SUCCESS` | Transcribe; task `PASSED`; next DAG node |
| **S2 Impossible** | Verifier's `impossible` field shows the criteria cannot be met as written (contradiction, missing capability, dependency down) with evidence | `STOP-IMPOSSIBLE` | Orchestrator amends spec via D-entry (different agent, S7) or marks `BLOCKED(<reason>)` |
| **S3 Budget** | Iteration cap hit (S 3 · M 5 · L 8 · XL 8 per task · never >20), cost cap or wall-clock cap | `STOP-BUDGET` | Keep best iteration, STATUS stop-rule log, re-plan or escalate (S6); a budget ceiling is a wait, not a verdict |
| **S4 Futility** | (a) passing count not increased for `stall_window` iterations (default 2; hypothesis hunts 3), (b) same failure signature (criterion id + error class) twice after a fix, (c) oscillation PASS→FAIL→PASS | `STOP-STALLED` | Keep best iteration; S6 |
| **S5 Guardrail** | Forbidden action attempted, tampered check (test deleted/skipped/loosened, acceptance.json or loop file edited by the maker, `check.sh` exit 4), parity/check count decreased, unresolved safety refusal | `STOP-GUARDRAIL` | Stop immediately; revert the lane; D-entry; refusal → task `BLOCKED-SAFETY` |
| **S6 Escalate** | 2 failed attempts at one rung, or S3/S4 fired | — | Attempt 1 FAIL → same agent + verifier `gap`/`top_fix` feedback. Attempt 2 FAIL or STALLED → next rung in a fresh context with `templates/escalation-brief.md`: `mission-worker` → `mission-worker-high` → `mission-builder` → `mission-strategist` (max 2) → `BLOCKED-HUMAN`. Log in BUDGET Escalations; continue other DAG branches |
| **S7 Never edit the check** | Anyone proposes changing a criterion, test or cap to get green | — | Refuse. A change needs a D-entry *and* an agent other than the failing maker; disputes are `TEST-DISPUTE` (`testing.md`) |

A narrated claim without evidence counts as FAIL. `UNVERIFIED` never satisfies S1.

### Work breakdown and delegation (W)

- **W1 MUST** make each task one verifiable change in one fresh context: cites ≥1 existing `AC-NNN`, lists owned
  paths, touches ≤ ~15 files and ≤ ~1 human-day of work. Larger → split, at contract boundaries only.
- **W2 MUST** record dependencies as a DAG in `PLAN.md` (`needs: [T-NNN]`). A wave = READY tasks with disjoint owned
  paths. The critical path gets the strongest suitable agent and is monitored first.
- **W3 MUST** cap writers per wave S ≤2 · M ≤4 · L ≤8 · XL ≤12; read-only lanes ≤16 inside a workflow. Any wave >2
  agents runs the swarm go/no-go first (`swarms.md`). Simple lookup = 1 agent.
- **W4 MUST** brief every maker with `templates/brief.md` and require its return format. A return without evidence
  paths counts as FAIL (and as a failed attempt for S6).
- **W5 MUST** integrate serially: `mission-integrator` merges one task at a time onto `claude/<mission>/integration`
  in DAG order, reruns that task's checks plus the smoke check, and on failure reverts the merge and returns the task
  with the failure log. No big-bang merges, no blind patching.
- **W6 MUST** isolate parallel writers in worktrees spawned from the primary checkout (branch
  `claude/<mission>/<T-NNN>-<slug>`). Verifiers read the integrated branch or a clean worktree.
- **W7 MUST** point to files in briefs (`CONTEXT.md`, spec sections, R-/L-ids); never paste large files or logs.
- **W8 MUST** name only AC ids that already exist in `acceptance.json`. Missing criteria → fix the spec first (GT3).
- **W9 MUST** give verifier briefs the artifact, the criteria and the evidence bundle only (`templates/gate-verifier.md`,
  `review.md` V2): no maker summary, reasoning, self-assessment or brief.
- **W10 MUST NOT** dispatch two briefs in one wave that share an owned path; lanes that need a frozen contract changed
  return `BLOCKED(contract-change)`.

### Human checkpoints, autonomy and guardrails (H)

- **H1 MUST** stop for a human only for: (a) irreversible or externally visible actions: production deploy,
  destructive or shared-data migration, force-push or push to default/protected branches, merges, publishing (store,
  blog, DNS, packages), spending money or quota beyond BUDGET caps, messaging real people, CI/workflow/secret changes,
  sensitive paths the project marks; (b) spec sign-off on L/XL; (c) stop-rule escalations that reach `BLOCKED-HUMAN`.
  Everything else: assume, log, continue.
- **H2 MUST** enforce H1 in settings, not prose: `permissions.deny` for never-actions, `permissions.ask` for
  checkpoints, a PreToolUse hook for command variants patterns miss (`templates/settings.guardrails.json`, P7).
  Boundaries stated only in conversation can be lost at compaction.
- **H3 SHOULD** ask at intake only about high-reversal-cost unknowns that change the mission's shape (platform,
  data retention, spend ceiling, irreversible external actions, taste anchors): ≤3 multiple-choice questions with
  recommended defaults, one batched message, ≤2 rounds. Work on unblocked tasks continues while waiting.
- **H4 MUST** surface at the next checkpoint or in the final report: stop-rule firings, classifier fallbacks, waived
  gates, budget overruns, `low`-confidence or `ASSUMED (unconfirmed)` assumptions, `PENDING-LIVE` items.
- **H5 MUST** in autonomous mode (`.mission/config autonomous=1`; direction says autonomous, unattended or overnight;
  every headless or Routine run): ask nothing; apply defaults marked `ASSUMED (unconfirmed)`; L/XL spec sign-off
  becomes notify-and-proceed with a D-entry (Approved by: autonomous default); every H1(a) action becomes a
  `BLOCKED-HUMAN` task in STATUS Human queue and other work continues; work ends in draft PRs on `claude/` branches,
  never merges; `enforce_stop=1`.

### Long-running execution, context and resume (L)

- **L1 MUST** start every session (interactive, resumed, headless, Routine) with the ritual: `HANDOFF.md` → STATUS
  header, Gates, Board → STATE Resume, Rules index, Open failures → PLAN READY tasks → `git log --oneline -20` → smoke
  check. Red smoke check → repairing it is the first task (`memory-and-lessons.md` MEM-30).
- **L2 MUST** at session end, before a reset, or when context use passes ~60%: rewrite STATE Resume, write
  `HANDOFF.md` (`templates/HANDOFF.md`), commit `.mission/`.
- **L3 SHOULD** prefer context resets with a handoff over repeated compaction on L/XL: compaction keeps continuity but
  not a clean slate. Compact or reset only at phase boundaries after STATE/STATUS are written.
- **L4 MUST** model days-long missions as many bounded sessions that each read the files, advance one milestone slice,
  verify, write back and exit.
- **L5 MUST** keep hard caps outside the model: loop counters in files, BUDGET ledger, `--output-format json`
  `total_cost_usd` per headless run, `--max-budget-usd <remaining hard cap>` where the flag exists, and a turn clause in
  any `/goal`.
- **L6 MUST NOT** start a skill-driven headless run with `--bare` (it skips skills, agents, hooks and CLAUDE.md) unless
  skill, agents and settings are passed explicitly with a D-entry. Use `templates/continue-prompt.md`.
- **L7 MUST** make Routine prompts self-contained: own stop rule, run budget, allowed scope, H1 queueing, digest,
  commit target. Vendor the skill into the repo; scope connectors to what the mission needs; output on `claude/`
  branches.

### Safety boundary (B)

- **B1 MUST** pin models by full ID (`claude-fable-5-1`, `claude-opus-4-8`, `claude-sonnet-4-6`) through roster agents
  and Agent-tool `model` overrides. Intake verifies the resolved models (preflight); aliases drift to newer models.
- **B2 MUST** pre-route predictable classifier work (exploit development, pentest logic, malware analysis, CVE PoC,
  offensive tooling, bio protocols, model-distillation work) to Opus 4.8 agents (`mission-builder` makers,
  `mission-critic` read-only) or to a human. Defensive review of the project's own code MAY stay on the planned agent.
- **B3 MUST** log every refusal, fallback or unexpected answering model in STATUS → Model / fallback events (time,
  task, category if known, from → to model @ effort, action) and re-select the intended orchestrator model at the next
  phase boundary: the Claude Code switch is sticky for the session.
- **B4 MUST** mark an unresolved refusal `BLOCKED-SAFETY` (visible state, human queue) and MUST NOT rephrase, split or
  obfuscate a brief to get past a classifier. Route on stop reason / category, never on the refusal's explanation
  text.

### Platform mapping (PM)

- **PM1 MUST NOT** treat `/goal` as a gate: its evaluator reads only the transcript, runs no commands, reads no files,
  and defaults to Haiku. A session MAY set a goal that points at printed evidence plus a turn bound, paired with a real
  verifier.
- **PM2 MAY** run a gate as a Claude Managed Agents Outcome: rubric = the loop file's criteria, `max_iterations` = the
  S3 cap. The Outcome grader's verdict still needs transcription with evidence (GT1).
- **PM3 SHOULD** use a script Stop hook running `.mission/check.sh <milestone>` as the deterministic engine in
  unattended runs (P6); it executes checks instead of reading narration.
- **PM4 MUST** degrade to plain sub-agents + file counters when no platform engine exists; briefs, loop files and
  artifacts stay identical across engines.

### Downgrade experiment (DX)

- **DX1 MUST**, before moving a role one tier down (e.g. gate verifier `mission-critic` → `mission-verifier`), run both
  on the next 3 gates blind to each other and compare verdicts. Downgrade only if they agree 3/3 and the cheaper agent
  found every FAIL the stronger one found. Record the comparison and decision in a D-entry and BUDGET audits.

## Procedure

### P1 Intake gate checklist (phase 0; verifier `mission-checker`, orchestrator never self-certifies)

| # | Item | Evidence |
|---|---|---|
| 1 | Shape (+ ≤2 secondary), class scores, traits with evidence, obligations recorded | `.mission/PROFILE.yaml` (S: 5 lines in `TASK-CARD.md`) |
| 2 | STATUS header complete: class, shape, profile, orchestrator model @ effort, mode | `.mission/STATUS.md` lines 1–5 |
| 3 | Charter (M+) or task card (S) with outcomes, non-goals, STOP list, DoD | `CHARTER.md` / `TASK-CARD.md` |
| 4 | Every gap is an `A-NN` with reversal cost and how to verify | `ASSUMPTIONS.md` |
| 5 | Model pins verified, `CLAUDE_CODE_SUBAGENT_MODEL` unset, roster agents installed | `.mission/logs/preflight.txt` (preflight exit 0) |
| 6 | Budget caps set by class and profile | `BUDGET.md` |
| 7 | Guardrails merged into `.claude/settings.json`; hooks merged | diff of settings or `claude` `/permissions` output saved to `logs/` |
| 8 | Human questions: ≤3, batched, defaults stated (autonomous: none asked, defaults logged) | STATUS Human queue / ASSUMPTIONS |
| 9 | Classifier-sensitive work identified and pre-routed (B2) | PROFILE trait `classifier_sensitive_domain` + PLAN notes |
| 10 | `.mission/` committed; smoke check command recorded | `CONTEXT.md` Commands row, commit sha |

### P2 Phase gate table

| Phase | Evidence artifact (exit gate) | Gate verifier | Human checkpoint | S | M | L | XL |
|---|---|---|---|---|---|---|---|
| 0 Intake | P1 checklist items with evidence | `mission-checker` | Only H3 questions | task card, 5-line profile | full | full + blind second-opinion classification (`mission-reviewer`) | as L |
| 1 Research | `RESEARCH.md`, `research/Q-NN.md`: every design-changing question answered, assumed or escalated | `mission-verifier` fact-check sample; public or load-bearing claims `mission-critic` | No | skip unless an API is unknown (≤3 inline lookups) | targeted | angle lanes + fact-check | per-milestone refresh |
| 2 Spec | `SPEC.md`, `requirements.yaml`, `acceptance.json` (all `passes:false`), `TEST-PLAN.md`, `reviews/spec-disposition.md` | `mission-critic` (`templates/spec-review-rubric.md`) | L/XL sign-off (autonomous: notify + D-entry); M notify | merged into task card | yes, review cap 1 | cap 2 | cap 2 |
| 3 Design | `design/*`, `design/adr/ADR-NNN.md`, `CONTRACTS.md`, `reviews/design-disposition.md` | `mission-critic` design lens (XL + `mission-strategist-review`) | L/XL irreversible choices (datastore, public API) | skip | short, may merge into Spec | full | full per milestone |
| 4 Plan | `PLAN.md` DAG + plan lint table, STATUS Board rows, swarm decision, budget per milestone | `mission-checker` structural lint | No | 1–3 tasks in task card | yes | ≥3 milestones | milestones sized as own class |
| 5 Build | Per task `.mission/lanes/<T-NNN>/verify-<n>.yaml`, `logs/<AC-id>-<ts>.log`, commits on integration branch | per-task `mission-verifier` (risky areas `mission-reviewer` / `mission-critic`) | No (H1 actions queue) | test first, ≤2 writers | ≤4 writers | ≤8 | ≤12 |
| 6 Verify | `verification/VERIFICATION-<M>.md`: `acceptance.json` 100% PASS on a clean checkout of the integrated branch, live checks PASS or `PENDING-LIVE` | `mission-critic` merged-result verifier | No | yes | yes | yes | per milestone |
| 7 Review | `reviews/<surface>-findings.md` + `-disposition.md`, all findings dispositioned | lenses per `review.md` triggers; refuters `mission-verifier` | L/XL human reads summary | 1 pass | ≤2 rounds | ≤3 | ≤4 per milestone + consolidated cross-milestone review |
| 8 Release | `reviews/release-findings.md` (P8 checklist), PR link, rollback command | `mission-reviewer` release lens | **Yes** for every H1(a) action | PR only | PR | PR + staged rollout | + per-milestone summary |
| 9 Retro | STATE deltas, `LESSONS-INBOX.md`, BUDGET stats, final report, STATUS closed | `mission-verifier` (promotion check) | No | 3 bullets | yes | yes | + distillation `mission-strategist` |

Loop back per GT3. Shape gates (REPRODUCED, PARITY-BASELINE, CONTRACT-FROZEN …) are inserted between phases, never
reordered (`shapes-and-scope.md` CMP-1).

### P3 Plan (phase 4)

1. Draft `PLAN.md` from `templates/PLAN.md`: milestones with exit checks and budget share; M0 contract + walking
   skeleton first where the profile requires it.
2. Decompose milestones into tasks per W1; assign roster agent and verifier (Model routing); risky areas start at
   `mission-builder`; add test-author tasks before the implementation tasks they gate.
3. Compute waves (W2, W3); run `check-ownership.sh` per wave where installed; swarm go/no-go for waves >2 agents.
4. Create STATUS Board rows (`TODO`/`READY`, `Iter 0/<cap>`). Dispatch `mission-checker` with the plan lint table.
5. Gate: every lint row PASS with evidence. FAIL → fix the plan, not the lint.

### P4 Build wave (phase 5; repeat per wave)

1. Write STATUS (tasks `IN-PROGRESS`, wave id) before dispatch.
2. Test author first where tests are missing: proves red on the pre-change tree, commits, paths join
   `.mission/frozen-paths.txt` and the manifest.
3. Dispatch makers with filled `templates/brief.md` (parallel Agent calls in one turn for ≤5 lanes; see `swarms.md`
   for surfaces). One loop file per task (P5).
4. On each return: return format complete? evidence paths exist? Else FAIL attempt (W4). Run `.mission/check.sh
   <milestone>` (or dispatch `mission-checker` to run it) and save the summary path.
5. Dispatch the verifier with `templates/gate-verifier.md` (W9). Save the reply to
   `.mission/lanes/<T-NNN>/verify-<n>.yaml`; apply S1–S7.
6. On S1: `mission-integrator` merges serially (W5); rerun that task's checks + smoke; failure → revert, task back to
   `FAILED(iter n)` with the log.
7. Write STATUS (Board, Iter, Evidence, stop-rule log), BUDGET rows; merge workers' `memory_delta` into STATE by ID.

### P5 Loops

1. Copy `templates/loop.md` to `.mission/loops/<loop-id>.md` (`<T-NNN>` for task loops, `<M>-<gate>` for gate
   loops). Fill criteria verbatim from `acceptance.json`, caps by class, engine. Commit before iteration 1.
2. After each verdict append one iteration-log row, update Board `Iter`, mark best-so-far, then apply S1–S7 in order.
3. On any stop state write the stop reason and best iteration into the loop file and STATUS Stop-rule log.
4. Iteration feedback to the maker = the verifier's `gap` lines and `top_fix` only, not the full report.

### P6 Sessions, handoff, headless and Routines

1. **Start**: L1 ritual. SessionStart hook injects STATUS/STATE parts where installed (`memory-and-lessons.md`).
2. **Check the model** at start and every phase boundary (B3); drift → log, re-select, note effort.
3. **Context ~60% or session end**: L2. Write in this order: STATE Resume → `HANDOFF.md` → STATUS `Updated` → commit.
   Then reset (new session reading HANDOFF) rather than compacting again.
4. **Continuation** (LR-4 order): Routine → `claude -p` script → manual resume. Fill `templates/continue-prompt.md`,
   set `.mission/config` `autonomous=1`, `enforce_stop=1`.
5. **Headless launch**: `claude -p` with the prompt, `--model claude-fable-5-1`, `--output-format json` redirected to
   `.mission/logs/run-<ts>.json`, `--max-budget-usd <remaining hard cap>`; no `--bare` (L6). Record `total_cost_usd` and
   per-model breakdown in BUDGET. Exit 143 (SIGTERM) leaves the turn unfinished: resume, do not restart.
6. **Routine**: self-contained prompt (L7), vendored skill, minimal connectors, model selected per routine, output on
   `claude/` branches, digest printed.
7. **Stop hook engine** (PM3, unattended only): add a Stop hook command next to `stop-check.sh` in
   `.claude/settings.json`, e.g. `"$CLAUDE_PROJECT_DIR"/.mission/check.sh M1 > "$CLAUDE_PROJECT_DIR"/.mission/tmp/stop-checks.txt 2>&1 || { echo "M1 acceptance checks failing: see .mission/tmp/stop-checks.txt" >&2; exit 2; }`.
   Scope it to the current milestone, never `all` during Build, and change it only at milestone boundaries with a
   D-entry. JSON-escape the quotes when pasting it as the hook's `command` string. Test-first red phases block by
   design; keep it off in interactive sessions.

### P7 Guardrails setup (intake, before any autonomous work)

1. Merge `templates/settings.guardrails.json` into the project `.claude/settings.json` (append to existing arrays;
   never replace user rules). Managed-settings `deny` rules cannot be overridden; prefer them when the owner controls
   managed settings.
2. Adjust per project: add deploy, migration, publish and payment CLIs the repo uses to `ask`; add sensitive paths
   to `deny` (Read/Edit) or `ask`.
3. Add a PreToolUse hook for variants patterns miss (`git -C <dir> push`, `env … git push`, shell wrappers): the hook
   inspects the full command text and blocks pushes to non-`claude/` refs, deploy commands and workflow edits.
4. Unattended runs that must push a `claude/` branch or open a draft PR: narrow the broad `git push *` / `gh pr create *`
   ask entries to a hook that allows only `claude/` refs and `--draft`, and log the change as a D-entry.
5. `ask` items in autonomous mode become `BLOCKED-HUMAN` tasks (H5); never wait on a prompt nobody will answer.
6. Verify: a `mission-checker` attempts one denied and one ask-listed command that would be harmless even if allowed
   (e.g. `git push --force no-such-remote HEAD:refs/heads/claude/guard-test`) and saves the refusal output to `logs/`.

### P8 Release checklist (phase 8; written to `reviews/release-findings.md` by `mission-reviewer`)

| # | Item | Evidence |
|---|---|---|
| 1 | Milestone Verify gate PASSED; every required AC PASS or `PENDING-LIVE` with mechanism | `verification/VERIFICATION-<M>.md` |
| 2 | Review dispositions complete; no CONFIRMED blocker/major open | `reviews/*-disposition.md` |
| 3 | Frozen manifest check clean; no test weakened in the release diff | `frozen-manifest.sh` output, test-diff audit |
| 4 | Preview/staging deploy smoke-tested (DP-1) | log path + URL |
| 5 | Rollback command written and exercised once (DP-2); data: restore point recorded (DB-4) | runbook path + log |
| 6 | Each irreversible step listed in Human queue and approved by the human, with date | STATUS Human queue line |
| 7 | Changelog / versioning D-entry for published contracts (PA-3) | D-entry |
| 8 | Canaries and live checks run, or `PENDING-LIVE` with owner and trigger | acceptance.json entries |
| 9 | Monitoring/alerting on the new path (DP-6, M+) | dashboard or alert rule path |
| 10 | Work on `claude/` branch in a PR (draft in autonomous mode); no secrets in the diff | PR link, secret scan output |

### P9 Retro (phase 9)

1. Failures → regression tests, controls and `LESSONS-INBOX.md` candidates (`memory-and-lessons.md`, `debugging.md`).
2. Stats into BUDGET and STATUS: cost by role, first-pass gate rate, iterations per task, stop-rule firings, fallbacks.
3. Final report per SKILL.md Reporting, including every H4 item. Close STATUS (`Stop state`, Done log), write HANDOFF.

## Scale by class (S/M/L/XL)

| Toggle | S | M | L | XL |
|---|---|---|---|---|
| Phases | Intake → Build (test first) → Verify → Review (1 pass) → Retro (3 bullets) | all; Design may merge into Spec | all; ≥3 milestones | each milestone runs its own class's toggles + consolidated cross-milestone review |
| Control files | task card in PR; `.mission/` only if multi-session | PLAN, acceptance.json, STATUS, STATE, loop file per task | full set, loop file per task | full set per milestone |
| Loop declaration | task card `Bound` line | `loops/<id>.md` | `loops/<id>.md` | `loops/<id>.md` |
| Iteration cap (S3) | 3 | 5 | 8 | 8 per task, 20 hard |
| Writers per wave (W3) | 2 | 4 | 8 | 12 (read-only lanes ≤16 in a workflow) |
| Implementation review rounds | 1 | 2 | 3 | 4 per milestone |
| Human checkpoints | H1(a) only | + notify at Spec | + spec sign-off, irreversible design, release | + per-milestone summary |
| Handoff | none unless multi-session | at session end | per session, reset at ~60% | per session + milestone worktrees |
| Continuation | one session | 1–3 sessions | per-phase sessions; `claude -p` | Routine or scheduled `claude -p` |
| Orchestrator | Opus 4.8 high | Fable 5.1 medium | Fable 5.1 medium (high: intake, spec/design gates, adjudication) | as L |

IF unsure between two classes THEN take the larger for verification (gates, caps, verifier tier) and the smaller for
ceremony (document length, fan-out), and log an `A-NN`.

## Shape conditionals

- IF **≥2 surfaces talk to each other** THEN M0 = frozen contract + contract tests on both sides, then walking skeleton
  (real entrypoint → one core flow → backend round-trip on dev), and platform lanes only after M0 PASSED (MP-1..3).
- IF **UI exists** THEN acceptance.json carries journey checks (executable) and rubric checks (screenshots) from Spec;
  the visual verifier is a separate loop (`frontend-verification.md`).
- IF **bug hunt** THEN phases collapse to Intake → REPRODUCED gate → hypothesis loop → fix → Verify → Review →
  Retro; no fix attempt before REPRODUCED passes; hypothesis loops use `stall_window` 3; hypotheses MAY run in
  parallel worktrees (`debugging.md`).
- IF **migration / extraction** THEN the parity inventory becomes acceptance checks captured before the move;
  strangler milestones (characterize → shadow → dual-run compare → switch → retire); each cutover step is an H1
  checkpoint; a decreasing parity check count fires S5.
- IF **feature in an existing product** THEN Research includes a `mission-scout` codebase map into `CONTEXT.md`; the
  affected-module regression suites join the milestone's checks; flags → add a flag-off check.
- IF **research + website** THEN research is its own milestone with a synthesis gate; published claims need sources
  checked by a fact-checker; positioning sign-off (L) and publish (H1) are checkpoints.
- IF **dependency upgrade** THEN acceptance = existing suite green + deprecation-warning count 0; fan out by module in
  worktrees; S4(b) same-failure rule applies strictly.
- IF **live incident** THEN time-box; mitigation is H1-gated unless a runbook explicitly allows it; the orchestrator
  never deploys without a human.
- IF **recurring operations** THEN each run is an S mission: Routine or scheduled `claude -p`, own STATUS entry and
  digest, stop condition in the prompt, scoped connectors.
- IF **security-sensitive** (auth, crypto, payments) THEN security lens `mission-critic`, exploit-style testing on
  Opus 4.8 agents or a human (B2), human checkpoint before merge.
- IF **classifier-sensitive domain** THEN B2 pre-routing, CS-3: the orchestrator receives summaries, not payloads.
- IF **long-running or unattended** THEN L1–L7, H5, P6 Stop hook engine, `--max-budget-usd`, draft PRs only.
- IF **no sub-agents or no per-agent model selection** THEN run briefs as separate `claude -p --model <full id>`
  sessions; maker and verifier never share a session (PM4).

## Model routing

| Role | Agent (conventions §7) | Guard that protects the choice |
|---|---|---|
| Orchestrator: plan, dispatch, integrate glue, adjudicate | session model: Fable 5.1 medium (M/L/XL), Opus 4.8 high (S) | Plan lint by `mission-checker`; S reclassified to M → switch orchestrator with a D-entry |
| Intake gate, plan lint, gate runner (`check.sh`) | `mission-checker` | Deterministic evidence only; low confidence → `mission-verifier` |
| Makers (routine) | `mission-worker` → ladder (S6) | Per-task verifier re-runs checks; S4/S6 |
| Makers (risky areas, CD-3, hard builds) | `mission-builder` | Verifier tier ≥ maker; reviewer on a different model before merge |
| Test author | `mission-worker-high` (risky: `mission-builder`) | Red-before-green proof in the verifier's run |
| Per-task verifier | `mission-verifier` | Sampled blind audit (`models-and-cost.md` GD4); disagreement → promote |
| Gate / merged-result verifier, spec and design review | `mission-critic` | Evidence per criterion; DX1 before any downgrade |
| Integrator | `mission-integrator` | Never a lane's maker; checks rerun after each merge |
| Release readiness | `mission-reviewer` | P8 checklist evidence; human approval for H1(a) |
| L/XL charter, architecture, swarm planning, last maker rung | `mission-strategist` | Written reason, max 2 attempts, then human |
| Codebase/log lookups | `Explore`, `mission-scout` | Verbatim quotes with file:line |
| Classifier fallback target | `mission-builder` (makers), `mission-critic` (read-only) | B3 logging; second refusal → `BLOCKED-SAFETY` |
| `/goal` evaluator | not relied on (PM1) | Real verifier gates; turn bound in any goal |

Downgrading any role one tier needs DX1. The Agent tool can override `model` per call, not effort: escalate by
choosing a different agent file.

## Anti-patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| Transcript as state | After compaction or resume the agent guesses where it was | O1, O2, L1, L2 |
| Self-grading | "All tests pass" accepted from the maker | GT1, S1, W9 |
| `/goal` as verifier | Goal "met" while checks are red; Haiku judging narration | PM1; `check.sh` + verifier |
| Premature "done" | Later session sees lots of code and declares victory | acceptance.json all `passes:false` until verdicts (GT4) |
| Check tampering | Tests deleted, assertions loosened, checks skipped, acceptance.json edited | S5, S7, frozen paths, `check.sh` exit 4 |
| Unbounded loops | No cap, or caps judged from narration | LP2, S3, L5 |
| Plateau grinding | Iterating after gains stop; shipping the last, not the best | S4, LP3 |
| Gate theatre | Ten long documents for a one-line fix | Scale by class; S collapses phases but keeps Verify and Retro |
| Asking instead of assuming | Mission stalls on questions a default would settle | O6, H3, H5 |
| Guardrails in prose | "Don't push" lost at compaction | H2, P7 |
| Vague briefs | Duplicated work, gaps, unowned edits | W4, W7, W8, `templates/brief.md` |
| Swarm by default | Many agents on non-parallel work or simple lookups | W3, swarm go/no-go |
| Overlapping ownership | Two writers on the same files | W6, W10 |
| Big-bang integration | Whole wave merged, then debugging the pile | W5 |
| Orchestrator doing the work | Top-tier tokens spent typing code; context polluted | O3 |
| Raw logs into the orchestrator | Context rot; lost attention | O9; logs to files, ≤400-word returns |
| Sticky fallback unnoticed | Ledger says Fable, session runs Opus at the old effort | B3, P6 step 2 |
| Rephrasing around a refusal | Policy violation; brittle routing | B4 → `BLOCKED-SAFETY` |
| `--bare` headless continuation | Run loads no skill, agents or hooks | L6 |
| Everything-connector Routine | Writes under the owner's identity with no approval prompt | L7, H5 |
| Review fatigue | Endless adversarial rounds block progress | round caps by class, dispositions (`review.md`) |
| Stop hook on `all` during Build | Every turn blocked by future-milestone checks | P6 step 7 scope |

## Unverified harness details

| Detail | Status | Safe fallback |
|---|---|---|
| Permission rule grammar (`Bash(cmd *)` vs legacy `Bash(cmd:*)`, mid-pattern `*`, `Edit(./path/**)` path anchoring) | not re-fetched for this skill | Verify rules at intake with P7 step 6; keep a PreToolUse hook for pushes and deploys |
| `permissions.ask` in headless `claude -p` and Routines (prompt, deny, or skip) | not verified | Treat every ask item as `BLOCKED-HUMAN` in autonomous mode (H5); never depend on the prompt appearing |
| Precedence when an `allow` entry overlaps an `ask` entry | not verified here | Do not rely on allow-overrides; use a hook to permit `claude/` pushes (P7 step 4) |
| Stop hook blocking semantics (exit 2 + stderr vs JSON `decision: block`) and `stop_hook_active` loop limit | secondary sources (`memory-and-lessons.md` Unverified table) | P6 step 7 uses exit 2; if a harness ignores it, run `.mission/check.sh <milestone>` as the continuation prompt's final step |
| `--max-budget-usd` flag present in the installed version | version-dependent | `claude --help`; else enforce caps between runs from BUDGET.md |
| Repointing the `/goal` evaluator away from Haiku | setting name not verified | Do not use `/goal` for anything that matters (PM1) |
| Detecting a classifier fallback from inside an interactive session | not verified | Model check at every phase boundary (B3); headless per-model cost breakdown |
| Outcomes `max_iterations` default 3 / max 20 | secondary source only | Set the S3 cap explicitly; never rely on the default |
| Routine push rights beyond `claude/` branches | docs say branches are `claude/`-prefixed; push policy not tested | Merges stay a human action; digest names the branch |
| Dynamic workflow API names | not confirmed | Ask for a workflow in natural language (`swarms.md`); briefs identical across surfaces |

## Evidence

1. `/goal` evaluator reads transcript only, defaults to Haiku, turn bounds: https://code.claude.com/docs/en/goal
2. Headless `-p`, `--output-format json` `total_cost_usd`, `--bare` skips skills/hooks, exit 143: https://code.claude.com/docs/en/headless
3. Routines: self-contained prompt, no approval prompts, `claude/` branches, connector scope: https://code.claude.com/docs/en/routines
4. Deny/ask before the auto-mode classifier; `git -C` variants; boundaries lost at compaction: https://code.claude.com/docs/en/auto-mode-config
5. Aliases resolve to newer models; pin full IDs; Fable guidance: https://code.claude.com/docs/en/model-config
6. Sticky classifier fallback to Opus 4.8 in Claude Code: https://github.com/anthropics/claude-code/issues/74311
7. Refusal stop reason and categories; explanation text not stable: https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback
8. Outcomes grader in a separate context, rubric required: https://platform.claude.com/docs/en/managed-agents/define-outcomes
9. All-failing JSON feature list, one feature per session, session-start ritual: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
10. Context resets vs compaction, skeptical standalone evaluator, plateaus: https://www.anthropic.com/engineering/harness-design-long-running-apps
11. Brief contents, fan-out scaling, 15× token multiplier: https://www.anthropic.com/engineering/multi-agent-research-system
12. Gate honesty and review fatigue in the owner's practice: arcwell/docs/operations/milestone-ledger.md:3-4,279;
    arcwell/docs/operations/review-process-amendment.md:3-5,25-31
