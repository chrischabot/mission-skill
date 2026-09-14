# Mission conventions (canonical)

Every other reference, template, agent file and script in this skill uses these names. If a reference seems to
disagree with this file, this file wins. Fix the reference.

## 1. Roles (who does what)

| Role | Is | Writes | Never |
|---|---|---|---|
| **Orchestrator** | The main session running this skill | `.mission/` control files, briefs, dispositions, small glue (≤ ~30 lines) | Grades its own work. Implements big changes on M+ missions. Pastes raw logs into its own context |
| **Maker** | Sub-agent that produces an artifact (code, doc, test, design, research note) | Only the paths its brief says it owns | Edits frozen paths, acceptance checks, STATE/STATUS |
| **Test author** | Maker that writes acceptance/regression tests *before* implementation | `tests/acceptance/**`, `tests/regression/**` (then frozen) | Sees the implementer's plan internals |
| **Verifier** | Fresh-context, read-only sub-agent that decides PASS/FAIL/UNVERIFIED against criteria | Its report file only | Sees the maker's transcript or self-assessment. Accepts claims without evidence |
| **Reviewer** | Fresh-context, read-only adversarial critic with one lens | Findings file only | Blocks on minors/nits. Invents findings to look useful |
| **Refuter** | Sub-agent that tries to disprove a candidate blocker/major finding | Refutation note | Is the reviewer that raised the finding |
| **Integrator** | Merges lane branches one at a time and reruns checks | Integration branch | Is any lane's maker |
| **Human** | The owner | Decisions in the human queue | Is asked about anything that can be defaulted and logged |

## 2. Mission directory (in the target repository)

```text
.mission/                      # git-tracked (except tmp/). Created by scripts/init-mission.sh
  PROFILE.yaml                 # primary/secondary shapes, class scores, traits (present|absent|unknown + evidence), gate zero, obligation IDs
  CHARTER.md                   # outcome, goals, non-goals, constraints, success metrics, STOP list, class, DoD   (M+; S uses TASK-CARD.md)
  TASK-CARD.md                 # S missions only
  SPEC.md                      # requirements with IDs (M+)
  requirements.yaml            # machine-readable registry (M+; validated by script)
  design/                      # BACKEND.md, FRONTEND.md, screens/<SCR-id>.md, tokens.md, adr/ADR-NNN.md, MIGRATION.md, WEBSITE-BRIEF.md
  PLAN.md                      # milestones + task DAG
  acceptance.json              # every acceptance check; starts all passes:false; the orchestrator flips an entry only by transcribing a verifier verdict
  STATUS.md                    # WORK: phase, gates, board, budget summary, fallback events, human queue, stop log
  STATE.md                     # KNOWLEDGE: resume pointer, rules index, verified facts, hypotheses, rules, open failures
  DECISIONS.md                 # append-only ADR-lite decisions (D-NNN), incl. every waiver, downgrade, scope cut
  ASSUMPTIONS.md               # A-NN with reversal cost and how to verify
  RESEARCH.md                  # research index: one line per question (Q-NN) + source registry (S-NNN)
  research/Q-NN.md             # per-question notes (M+), ≤1,500 words each
  BUDGET.md                    # ledger: caps, spawn log, escalations, audits
  CONTRACTS.md                 # frozen cross-lane decisions (interfaces, naming, tokens, error model) before any parallel writing
  CONTEXT.md                   # conventions + commands every brief points to (cache-friendly shared context)
  TEST-PLAN.md                 # criteria → oracles, frozen paths, gate set (M+)
  LESSONS-INBOX.md             # candidate cross-project lessons (L-NNN)
  HANDOFF.md                   # overwritten at session end or ~60% context
  loops/<loop-id>.md           # loop specs (criteria, caps, iteration log)
  reviews/<surface>-findings.md, reviews/<surface>-disposition.md
  verification/                # VERIFICATION-<milestone>.md, matrix.yaml, screens/<run-id>/, accepted/, walkthroughs/, human-review/
  investigations/O-NNN.md      # failure record + hypothesis ledger + conversion
  lanes/<lane-id>/             # lane progress.md and artifacts
  logs/                        # command outputs referenced as evidence (large logs may live in tmp/)
  archive/                     # superseded STATE entries, old handoffs
  tmp/                         # gitignored scratch
  bin/                         # copies of the skill's scripts (hooks and checks work in cloud/Routine runs without the personal skill)
  config                       # key=value: class, profile, enforce_stop (0|1), autonomous (0|1)
  frozen-paths.txt             # globs the implementer may read but not write (tests, goldens, test configs, CI, hooks)
  frozen-manifest.sha256       # sha256 manifest of frozen files, checked by verifiers/CI
  check.sh                     # runs executable acceptance checks for a milestone; never flips passes
```

Single source of truth per kind of fact:

- **STATUS.md = what is done / next.** Progress comes only from verifier-recorded gate results, never task counts.
- **STATE.md = what is true.** No fact without evidence; no rule without a verified instance and scope.
- **acceptance.json = what "done" means.** JSON on purpose: models overwrite JSON less casually than Markdown.
- A fact appearing in two files is a bug. Point, don't copy.
- Only the orchestrator writes STATUS.md and STATE.md. Workers return a `memory_delta` block (see memory reference).

S missions create `.mission/` only when the work spans sessions (task card, PROFILE, STATUS, STATE and `bin/`); otherwise
the task card lives in the PR description.

## 3. IDs

| Thing | Format | Example | Notes |
|---|---|---|---|
| Requirement | `<DOMAIN>-<NNN>` (M: `REQ-NNN`) | `API-012`, `OUTFIT-003` | Never renumbered or reused; withdrawn ones stay with `status: withdrawn` |
| Outcome | `OUT-NNN` | `OUT-001` | In CHARTER |
| Acceptance check | `AC-NNN` | `AC-021` | In acceptance.json, cites ≥1 requirement ID |
| Screen spec | `SCR-NNN` | `SCR-004` | In design/screens |
| Milestone | `M<n>` | `M0` | M0 is the contract/walking-skeleton milestone for multi-surface work |
| Task / lane | `T-NNN` | `T-012` | In PLAN.md and STATUS board |
| Assumption | `A-NN` | `A-04` | |
| Decision | `D-NNN` | `D-014` | ADRs for irreversible choices also get `ADR-NNN` |
| Verified fact | `F-NNN` | | STATE |
| Hypothesis | `H-NNN` | | STATE or investigation ledger |
| General rule | `R-NNN` | | STATE |
| Open failure | `O-NNN` | | STATE; long ones → investigations/O-NNN.md |
| Research question | `Q-NN` | `Q-03` | RESEARCH index; notes in research/Q-NN.md |
| Source | `S-NNN` | | RESEARCH source registry |
| Lesson | `L-NNN` | | LESSONS-INBOX, promoted to skill `references/lessons.md` |
| Finding | `FND-<surface>-NN` | `FND-auth-03` | reviews/ |
| Test citation | `@req:<ID>` in the test name or annotation | `it("@req:API-012 rejects expired token")` | The verifier computes coverage from code, not from the plan |

## 4. States and verdicts

- **Gate states:** `PENDING` · `PASSED` · `PASSED-WITH-WAIVER(D-id)` · `BLOCKED(<reason>)` · `PENDING-LIVE` (mechanism
  delivered, live evidence not yet run). No gate is PASSED without cited evidence and a verifier that did not author it.
- **Task states:** `TODO` → `READY` → `IN-PROGRESS` → `VERIFYING` → `PASSED` | `FAILED(iter n)` | `STALLED` |
  `BLOCKED(<reason>)` | `BLOCKED-HUMAN` | `BLOCKED-SAFETY` | `CANCELLED(D-id)`.
- **Loop stop states:** `STOP-SUCCESS` · `STOP-IMPOSSIBLE` · `STOP-BUDGET` · `STOP-STALLED` · `STOP-GUARDRAIL`.
- **Verifier verdict per criterion:** `PASS` (evidence cited) · `FAIL` (evidence cited) · `UNVERIFIED` (could not be
  checked; reason stated). A required criterion that is UNVERIFIED, skipped, quarantined or flaky keeps its gate
  PENDING. UNVERIFIED is never PASS.
- **Finding severity:** `blocker` (violates a MUST, loses/corrupts data, security exposure, artifact fails its purpose)
  · `major` (wrong behaviour on a supported path, overstated completion claim, clear spec/token violation on a key
  surface) · `minor` · `nit`. Flags: `pre-existing` (never blocks the current change), `question` (cannot block).
- **Refutation result:** `CONFIRMED` · `REFUTED` · `UNVERIFIED`. Only CONFIRMED blocker/major findings block.
- **Dispositions:** `FIXED` (commit + test that fails without the fix) · `REFUTED` (evidence) · `RESIDUAL` (rationale,
  owner, where recorded) · `DEFERRED` (milestone, owner, why this is not goalpost-moving) · `CONTESTED` (escalated to a
  tier-up adjudicator or the human).
- **Evidence levels:** `local-run` · `ci` · `staging` · `production` · `doc-source`.
- **Confidence (rules):** `low` = 1 verified instance · `medium` = 2 · `high` = ≥3 or reproduced by a verifier.

## 5. Scope classes

Score four dimensions 0–3 (details and examples: `shapes-and-scope.md`):

- **Breadth** 0 one file/behaviour · 1 one component or one vertical slice · 2 several services, a new data model, a
  public contract or two repos · 3 two or more client platforms built together, or three or more services/repos.
- **Duration** (human-equivalent) 0 < half a day · 1 ≤ ~3 days · 2 1–4 weeks · 3 > a month.
- **Uncertainty** 0 approach known · 1 details unknown · 2 open design questions or unfamiliar codebase/platform ·
  3 problem cannot be framed yet (no repro, no judge, research needed to state the goal).
- **Coordination** 0 one writer · 1 parallel lanes on disjoint files · 2 frozen contracts between lanes or internal
  consumers · 3 external users/parties, app-store release, multi-team cutover.

`base = max(Breadth, Duration)` → 0 S · 1 M · 2 L · 3 XL. Add one step if Uncertainty = 3 or Coordination = 3 (cap
XL). **Risk traits (money, PII, auth, irreversibility) add gates and stronger agents but never change size.** A
greenfield product is never S.

Record the scores, class and a one-line justification in `.mission/PROFILE.yaml` and the STATUS header. Revise upward
at any gate. Revise downward only with a D-entry. If unsure between two classes: the larger for verification strength,
the smaller for document ceremony. At XL each milestone is sized on its own and runs that class's toggles.

## 6. Models (edit here only)

| Tier | Full model ID | $/MTok in · cache read · out | Efforts used |
|---|---|---|---|
| **F** Fable 5.1 | `claude-fable-5-1` | 10.00 · 0.25 · 50.00 | medium, high |
| **O** Opus 4.8 | `claude-opus-4-8` | 5.00 · 0.50 · 25.00 | medium, high, xhigh (degraded orchestrator only) |
| **S** Sonnet 4.6 | `claude-sonnet-4-6` | 3.00 · 0.30 · 15.00 | low, medium, high (no xhigh) |

- Never use aliases (`opus`, `sonnet`, `fable`, `best`). On the Anthropic API `opus` and `sonnet` resolve to newer
  models (Opus 5 / Sonnet 5), which silently breaks this routing.
- **No Haiku anywhere.** Roles that would use Haiku (classifiers, checklist graders) use Sonnet 4.6 at low effort.
- Prices verified September 2026 from Anthropic's pricing page. Re-verify before quoting dollar figures to the user.
- Effort can only be set in agent frontmatter, not per Agent-tool call. The Agent tool can override `model` per call.
  That is why the skill ships one agent file per model·effort·permission profile.

## 7. Agent roster (installed into `.claude/agents/` by `scripts/init-mission.sh`)

| Agent file | Model · effort | Write access | Used for |
|---|---|---|---|
| `Explore` | S · low | read-only | Overrides built-in Explore so exploration never inherits a top-tier model |
| `mission-scout` | S · low | read-only | Codebase/web lookups, log extraction with verbatim quotes, pointer maps |
| `mission-checker` | S · low | read-only + Bash | Checklist verdicts over deterministic evidence, gate runner, bookkeeping, classifiers |
| `mission-worker` | S · medium | write | Routine implementation, docs, research reading, test code, capture scripts |
| `mission-worker-high` | S · high | write | Second-rung implementer, test author, repro builder, flake investigator, sweeper |
| `mission-verifier` | S · high | read-only + Bash | Per-task verifier, refuter, test-diff audit (S/M), fact-checker |
| `mission-builder` | O · high | write | Hard builds (concurrency, migrations, security-sensitive), investigator, architect/designer docs, escalation rung |
| `mission-integrator` | O · medium | write | Serial merges, conflict resolution |
| `mission-reviewer` | O · medium | read-only + Bash | Code review, per-screen vision verification, root-cause confirmer, loop-grader audits, release readiness |
| `mission-critic` | O · high | read-only + Bash | Adversarial/spec/design/security review, gate & merged-result verification, tournament judge, sampled audits |
| `mission-strategist` | F · high | write (docs) | Charter/spec synthesis and architecture on L/XL, swarm planning, hypothesis-space reset, XL retro distillation |
| `mission-strategist-review` | F · medium | read-only | One lens of an XL consolidated review; XL milestone design review |

The orchestrator itself is the session model: Fable 5.1 (medium effort; high for intake, spec/design gates and
adjudication) on M/L/XL; Opus 4.8 high on S. Escalation ladder for makers:
`mission-worker` → `mission-worker-high` (fresh context) → `mission-builder` → `mission-strategist` → human.

## 8. Profiles

- **Standard** — the tables above.
- **Lean** — user asks for minimum cost or is on a subscription plan: orchestrator Opus 4.8 high on every class;
  Fable only with human approval. Guards unchanged.
- **Degraded** — a model is unavailable. No Fable → orchestrator on Opus 4.8 xhigh (session effort); strategist roles
  run on `mission-builder` (Opus 4.8 high). No Opus 4.8 → Sonnet 4.6 high plus mandatory human review of risky changes. No Sonnet 4.6 → stop and ask; never silently promote all
  workers to Opus. Record the profile in STATUS.md and a D-entry.

## 9. Branches, worktrees and runtime isolation

- Integration branch: `claude/<mission>/integration`. Lane branches: `claude/<mission>/<lane-id>-<slug>`. Unattended
  runs: `claude/<mission>/run-<YYYYMMDD>`. Nothing lands on the default branch without a verifier PASS on the merged
  branch and, where it is externally visible, human approval.
- Parallel writers get their own worktree, spawned from the primary checkout, with disjoint `owns:` globs checked by
  `scripts/check-ownership.sh`. Per-lane runtime: ports base + 10 × lane index, database/schema `<name>_<lane-id>`,
  one simulator device per lane, temp dir `.mission/tmp/<lane-id>/`.

## 10. Normative words

MUST / MUST NOT / SHOULD / MAY as in RFC 2119/8174, only in capitals. "Evidence" means a command with its exit code and
the salient output line, a file:line, a screenshot path with a pixel box, or a URL with a quote and access date.
