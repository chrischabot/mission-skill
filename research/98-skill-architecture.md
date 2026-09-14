# Skill architecture for `mission` (for reference-writer lanes)

The deliverable is a Claude Code skill at `skills/mission/` in this workspace. The user copies it to
`~/.claude/skills/mission/` (or vendors it into a repo's `.claude/skills/` for cloud runs) and invokes it with a
high-level direction, e.g. `/mission build a fashion outfit iOS app with a Cloudflare backend` or
`/mission find and fix the checkout flake`.

Canonical names: `skills/mission/references/conventions.md` (READ IT FIRST; it wins over every report).

## Layout and ownership

```text
skills/mission/
  SKILL.md                         # orchestrator (lean): invocation, phase loop, invariants, decision map → references
  references/
    conventions.md                 # orchestrator: roles, .mission layout, IDs, states, models, agent roster
    shapes-and-scope.md            # orchestrator: classification, traits→obligations, per-shape pipelines, worked examples
    orchestration.md               # lane A (source: 01)
    models-and-cost.md             # lane B (source: 02)
    spec-and-design.md             # lane C (source: 03)
    testing.md                     # lane D (source: 04)
    frontend-verification.md       # lane E (source: 05)
    review.md                      # lane F (source: 06)
    memory-and-lessons.md          # lane G (source: 07)
    debugging.md                   # lane H (source: 08)
    swarms.md                      # lane I (source: 09)
    research.md                    # lane J (source: 10)
    lessons.md                     # lane G: promoted cross-project lessons (seeded, ≤40 entries)
  templates/                       # copied into the target repo's .mission/ by scripts/init-mission.sh
    (per-lane files listed below)
  agents/                          # lane B: the 12 agent files from conventions.md §7
  scripts/                         # per-lane scripts listed below + init-mission.sh (orchestrator)
  evals/evals.json                 # orchestrator
```

| Lane | Reference | Templates it owns (`skills/mission/templates/`) | Scripts it owns (`skills/mission/scripts/`) |
|---|---|---|---|
| A orchestration | `references/orchestration.md` | `PLAN.md`, `acceptance.json`, `HANDOFF.md`, `brief.md` (sub-agent task brief), `loop.md` (loop spec + verifier skeleton), `continue-prompt.md` (headless/Routine continuation), `settings.guardrails.json` | `check.sh` (runs executable checks of a milestone from acceptance.json, writes logs, never flips passes; uses `jq` if present else `python3`) |
| B models & cost | `references/models-and-cost.md` | `BUDGET.md`, `escalation-brief.md`, `audit-prompt.md` | `preflight.sh` (checks CLAUDE_CODE_SUBAGENT_MODEL unset, claude version if available, prints model table) ; plus all of `skills/mission/agents/*.md` |
| C spec & design | `references/spec-and-design.md` | `CHARTER.md`, `TASK-CARD.md`, `SPEC.md`, `BUGFIX-SPEC.md`, `requirements.yaml`, `design/BACKEND.md`, `design/FRONTEND.md`, `design/SCREEN.md`, `design/ADR.md`, `design/MIGRATION.md`, `design/WEBSITE-BRIEF.md`, `spec-review-rubric.md`, `ASSUMPTIONS.md` | `validate-registry.py` (duplicate IDs, unknown test citations, implemented requirements without oracle; stdlib only, parses the templates' YAML subset or uses PyYAML if installed) |
| D testing | `references/testing.md` | `TEST-PLAN.md`, `VERIFICATION.md`, `TEST-DISPUTE.md`, `test-diff-audit.md` | `protect-frozen.sh` (PreToolUse hook blocking writes to frozen paths), `frozen-manifest.sh` (write/check sha256 manifest), `test-diff-grep.sh` (grep pre-pass for .only/.skip/XCTSkip/etc. in a diff) |
| E frontend verification | `references/frontend-verification.md` | `verification/matrix.web.yaml`, `verification/matrix.ios.yaml`, `visual-verifier.md`, `design-rubric.md`, `walkthrough.md`, `human-review.md` | `geometry-probe.js` |
| F review | `references/review.md` | `reviewer.md` (skeleton + lens blocks), `refuter.md`, `gate-verifier.md`, `findings.md`, `disposition.md`, `grader-rubric.md` | — |
| G memory & lessons | `references/memory-and-lessons.md`, `references/lessons.md` | `STATUS.md` (merge of lane 01 §7.1 and lane 07 §7.3: phase/class/shape header, goal + done-means, gates table, board, budget summary, model/fallback events, human queue, stop-rule log, done log), `STATE.md`, `DECISIONS.md`, `LESSONS-INBOX.md`, `memory-delta.md`, `settings.hooks.json` | `session-start.sh`, `stop-check.sh`, `memory-lint.sh` |
| H debugging | `references/debugging.md` | `investigation.md` (failure record + hypothesis ledger + proof + conversion) | `flake-runs.sh` (compute n from p and alpha, then run a command n times with a tally) |
| I swarms | `references/swarms.md` | `CONTRACTS.md`, `lane-contract.md` (brief extension + JSON return schema), `swarm-decision.md` (go/no-go) | `check-ownership.sh` (fails if owned globs of lanes in a wave overlap), `run-wave.sh` (headless `claude -p` lane runner) |
| J research | `references/research.md` | `RESEARCH.md`, `researcher.md`, `fact-checker.md`, `option-matrix.md`, `positioning.md` | — |

Orchestrator owns: `SKILL.md`, `references/conventions.md`, `references/shapes-and-scope.md`, `templates/CONTEXT.md`,
`scripts/init-mission.sh`, `evals/evals.json`, `README.md`.

## SKILL.md phase loop (what references plug into)

Phases: **0 Intake** (classify shape + class + traits, preflight models, charter/task card, assumptions, ≤3 human
questions) → **1 Research** (only unknowns that change design) → **2 Spec** (requirements, acceptance.json, TEST-PLAN,
spec review) → **3 Design** (backend/frontend/migration designs, ADRs, CONTRACTS, design review) → **4 Plan** (milestones,
task DAG, swarm decision, budget allocation) → **5 Build** (waves: test author → makers → per-task verifier → serial
integration) → **6 Verify** (mission-level VERIFICATION with red-before-green, visual/UX gates, merged verifier) →
**7 Review** (trigger-selected lenses, refutation, dispositions, convergence caps) → **8 Release** (checklist, human
checkpoint for irreversible actions, canaries PENDING-LIVE) → **9 Retro** (failure conversion, lessons inbox,
promotion, cost stats). S missions collapse to Intake → Build(test-first) → Verify → Review(1 pass) → Retro(3 bullets).
Every phase ends at a gate verified by an agent that did not author it. Memory protocol (read at start, write before
exit) wraps every session.

## Writing rules for every reference

1. Audience: the orchestrator model at runtime, loading the file on demand. Write normative, dense, imperative
   instructions. Tables over prose. No marketing, no history lessons.
2. Target 250–550 lines per reference. Put long paste-ready artifacts in the template files you own and point to them
   by path (`templates/<file>`). Each template must be complete and immediately usable (placeholders in `<angle
   brackets>`), not a stub.
3. Use conventions.md names exactly: `.mission/` paths, ID formats, state names, severity/disposition vocabulary,
   agent roster names (`mission-worker`, `mission-critic`, ...), model IDs. Do not invent new agent names; say
   "`mission-reviewer` with Agent-tool `model` override" if a report wanted a variant.
4. Required sections, in this order: `When to load`, `Core rules` (numbered rule IDs with the lane prefix already used
   in the source report, MUST/SHOULD/MAY), `Procedure` (step-by-step for the orchestrator), `Scale by class (S/M/L/XL)`,
   `Shape conditionals` (IF … THEN …), `Model routing` (roster names + guard for each downgrade), `Anti-patterns`,
   `Unverified harness details` (anything the source report could not verify, with the safe fallback), `Evidence`
   (≤12 key URLs or arcwell paths).
5. Resolve conflicts with conventions.md and these decisions:
   - Mission dir is `.mission/` (not `mission/`).
   - Orchestrator = Fable 5.1 medium effort (high for intake, spec/design gates, adjudication) on M/L/XL; Opus 4.8 high on S.
   - Flaky-fix proof: n ≥ ln(α)/ln(1−p) consecutive clean runs with state reset (α 0.05; 0.01 for money/auth/data/
     concurrency), doubled when state cannot be fully reset. Not "10×N".
   - Implementation review round caps S=1, M=2, L=3, XL=4 (lane 06); spec review caps S=0, M=1, L/XL=2 (lane 03).
   - Fan-out writers per wave S≤2, M≤4, L≤8, XL≤12; read-only lanes ≤16 inside a workflow.
   - `/goal` is never a gate (its evaluator reads only the transcript and defaults to Haiku). Gates come from verifier
     sub-agents and `check.sh`/Stop-hook scripts.
   - Unproven criteria use the verdict `UNVERIFIED` (not "UNPROVEN").
   - Human checkpoints only for irreversible or externally visible actions, spec sign-off on L/XL (skippable in
     autonomous mode with a logged D-entry), and stop-rule escalations. Everything else: assume, log, continue.
6. Scripts: POSIX bash (or python3 stdlib), `set -euo pipefail`, `--help` output, no network, no destructive git
   operations, idempotent. Run `bash -n <script>` and a small smoke test if the sandbox works; if the sandbox is down,
   say so in your return.
7. Write incrementally: never more than ~1,200 words per tool call. Create the file with the first sections, then
   append with edits. Never put the character sequences dollar-backtick, dollar-quote or dollar-ampersand inside an
   edit's replacement text (the edit tool treats them as replace patterns and corrupts the file); in shell snippets
   prefer `"${var}"` forms and avoid those sequences entirely.
8. Do not copy report prose wholesale. Distil: keep every normative rule and threshold that survived, drop narrative,
   and fix inconsistencies with conventions.md.
