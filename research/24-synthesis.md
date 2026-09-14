# 24 · Synthesis: the decisions the skill is built on

This file is the coordinator's reconciliation of reports 01 to 23. Where reports disagree, this
file decides, and every drafting agent follows it over the individual reports. It fixes names,
file grammar, the agent roster, and the rules that must be identical everywhere they appear.
It is written for the agents that draft the skill, so it is terse and exact rather than argued;
the arguments live in the reports it cites.

Binding corrections from the owner apply throughout: the fashion-app prompt is only an example
of a project shape and nothing is built for it; model aliases are `fable`, `opus`, `sonnet`
(Fable 5.1, Opus 5, Sonnet 5 today); Haiku is never used.

## 1. Packaging

- Repository `~/Projects/drive/`. Plugin root is `~/Projects/drive/skill/`, symlinked to
  `~/.claude/skills/drive`, which loads as the skills-directory plugin `drive@skills-dir` (report
  01). Invocation is `/drive <goal>` or `/drive --resume`. Agents are addressed as `drive:<name>`.
- Plugin root contents:

```
skill/
  .claude-plugin/plugin.json
  SKILL.md                      the spine; first ~150 lines survive compaction
  agents/<name>.md              the roster in section 6
  hooks/hooks.json              plugin-wide hooks (inert unless a run is active)
  scripts/drive.py              one stdlib-only Python 3 tool with subcommands (section 9)
  scripts/tests/                tests for drive.py, including severe tests
  references/                   read on demand; never all loaded
  references/shapes/<shape>.md  one per shape
  references/domains/<d>.md     ios, cloudflare, web (hand-written part + "Learned constraints")
  references/lessons/           general.md, retired.md, README.md (the compounding store)
  templates/                    every file the run writes into a project
  evals/                        claude plugin eval cases (section 12)
```

- Repo root also holds `README.md`, `LICENSE` (MIT), `install.sh`, `uninstall.sh`, `research/`,
  `HANDOFF.md`.
- Verified harness facts that shape packaging: plugin agents ignore `hooks`, `mcpServers`, and
  `permissionMode` frontmatter; plugin `hooks.json` hooks fire inside subagents and their input
  carries `agent_type` (for plugin agents, `drive:<name>`); the Agent tool has no effort parameter,
  so effort lives in agent frontmatter; a skill's `model` frontmatter lasts only one turn, so
  SKILL.md sets no model; `disable-model-invocation: true` skills cannot be preloaded (fine for
  `/drive`); subagents can invoke unlisted skills through the Skill tool, and `skills:` preloads
  full skill text.

## 2. SKILL.md frontmatter and spine

```yaml
---
name: drive
description: Turn one high-level goal into finished, verified work and drive it to completion autonomously. Classifies the work, researches, specifies, designs, tests, builds in parallel, verifies adversarially, records state in files, and compounds lessons. Only the user starts it.
argument-hint: "<high-level goal> | --resume"
disable-model-invocation: true
disallowed-tools: AskUserQuestion
effort: high
hooks:
  Stop:
    - hooks:
        - type: command
          command: "python3 \"$HOME/.claude/skills/drive/scripts/drive.py\" hook-stop"
          timeout: 60
---
```

Spine order in SKILL.md, all of it above the compaction line (about 5,000 tokens):
1. Who you are and the autonomy contract (report 13, section 4.5 wording).
2. Read-at-start and resume (`drive.py start`, then STATE.md, GOAL.md, lessons).
3. Intake: parse, probe, shape precedence, traits, size, plan, the single-question rule.
4. The shape table, trait-to-gate one-liners, size table.
5. The phase loop and gates, maker never grades its own work, the ladder and evidence rule.
6. Parallel execution rules in brief, model routing table in brief.
7. Failure events, the workaround ledger, second time is the bug.
8. Stop conditions and the report.
9. The standing-rules block delimited by `<!-- drive:standing-rules:start -->` and
   `<!-- drive:standing-rules:end -->` (the only region the lesson loop may edit; 15 lines max).
10. Reference index: which file to read when.

SKILL.md stays under 450 lines. No arguments or examples in SKILL.md; those live in references.

## 3. Classification (from report 02, adopted as written)

- Three axes recorded separately. **Shape** fixes phase order: `build`, `feature`, `fix`, `move`,
  `publish`, `report`, `operate`. Variants: `fix/incident`, `fix/perf`, `move/migration`,
  `move/refactor`, `move/upgrade`. **Traits** attach gates, each `confirmed` or `suspected`
  (suspected still gates): `ui`, `api`, `auth`, `data`, `existing-code`, `multi-repo`,
  `external-systems`, `async-scheduled`, `concurrency`, `native-platform`, `prose-content`,
  `public-api`, `cli`, `perf`, `research-needed`, `deploy-infra`, `ai-llm`, `large-surface`,
  `generated-code`. **Size** `XS`, `S`, `M`, `L`, `XL` is the maximum any structural trigger
  demands; risk never sets size. Borderline: take the smaller, except `move` and `operate`, take
  the larger.
- Shape precedence, first rule wins: named defect → `fix` (live now → incident; measured quality
  → perf; behaviour never existed → `feature`); from X to Y, migrate, consolidate, upgrade,
  refactor, simplify → `move`; prose only → `report`; site, docs, designed content → `publish`;
  change of state in a live system with no code as the point → `operate`; existing code hosts
  the deliverable → `feature`; otherwise `build`. Two shapes in one prompt become ordered
  sub-goals sharing one state directory, fixes and moves before the features that sit on them.
- Intake is silent and inline: resume check, parse six slots, thirty-second probe, shape, traits,
  size, derive plan, write GOAL.md, decide whether the one question is unavoidable.
- Re-classification is a standing rule at every phase gate and on the events in report 02 table
  4.6. Append to `reclassifications`; keep all evidence; re-derive only remaining phases.
- **XS runs** create no `.drive/`, spawn no subagent except where a trait gate demands one
  (`auth` still gets the Opus security review), and the commit body records claim and evidence.

## 4. The project state directory (the one layout; supersedes the per-report variants)

All run state lives in `.drive/` at the target repository root and is committed to main with
the code, except `.drive/local/`, which is gitignored. When the project has an existing
requirements registry with its own gate, STATUS.md becomes a pointer and records
`registry: <command>` in STATE.md's header.

```
.drive/
  GOAL.md               goal verbatim, classification block, plan checklist, budget, re-plans
  STATE.md              volatile working memory and resume pointer (≤150 lines)
  STATUS.md             the ladder: one row per behavioural claim, typed evidence
  DECISIONS.md          decisions taken on the owner's behalf, each with undo (append-only)
  LESSONS.md            project lessons distilled from verified failures
  SPEC.md               build, feature (change spec), move (charter lives in MIGRATION.md)
  DESIGN.md             backend and system design, contracts, decision index (build, large feature)
  TESTPLAN.md           claim → layer → test → status → evidence, plus the kindness ledger
  RESEARCH.md           research ledger (any run with a research phase)
  HUNT.md               fix: brief, repro command, pre-fix commit, hypothesis ledger, post-mortem
  MIGRATION.md          move/migration: charter, invariants, consumer inventory, parity, stages, undo ledger
  how-it-works.md       existing-code archaeology note with the drift table (≤150 lines)
  REPORT.md             the final report, derived from the files
  handoffs/<unit>.md    verifier handoffs built from files by template
  rubrics/<shape>.md    frozen per run
  packages/<id>/brief.md, report.json      parallel work packages
  proofs/<key>/proof.json                  manifest for a claim's proof
  proofs/<key>/r<n>/verdict.json, commands.log, *.txt, shots/, live.md, findings.json
  reviews/<date>-<slug>.md                 spec, design, security review verdicts
  investigations/<date>-<slug>.md          failure records (five stages)
  local/                                   gitignored: active, gate.log, workers/, logs/, ui/
```

UI design contract lives with the product, not in `.drive/`: `design/DESIGN.md`,
`design/tokens.json`, `design/screens.yaml`, `design/baselines/`. For an existing product the
contract is extracted from the existing design system into the same place.

Which files a run creates, by size: XS none. S: GOAL.md, STATE.md, STATUS.md (one to three
rows), plus the shape's own ledger (HUNT.md for a fix, RESEARCH.md for a report). M and above:
everything the shape and traits call for.

### 4.1 Keys, not numbers

Nothing the owner reads uses opaque identifiers. Requirements are short claims used as headings
in SPEC.md ("Deleting the account removes every photo"). The machine key is the slug of those
words (`deleting-the-account-removes-every-photo`), used in STATUS.md, proof paths, test suite
names, and handoffs. Failures, decisions, investigations, and lessons are keyed by date plus
slug. Reports refer to things by their words.

### 4.2 GOAL.md grammar

```markdown
# GOAL · <goal slug>
goal: <verbatim prompt, quoted>
live means: <what live is for this project, decided at intake>
budget: <turns, subagents, wall clock, usd envelope>

## Classification
```yaml
shape: feature
variant: null
size: M
size_set_by: "<the trigger>"
traits: { confirmed: [existing-code, ui, api], suspected: [data] }
probe: { repo: <path>, stacks: [...], test_command: "<cmd>", claude_md: present }
assumptions:
  - text: "<assumption>"
    overturned_by: "<evidence>"
not_asked:
  - question: "<question>"
    default: "<default taken>"
classified_at: <ISO UTC>
reclassifications: []
```

## Plan
- [ ] <phase> · artifact: <path> · exit: <checkable condition> · checker: <orchestrator|verifier|grader|auditor>

## Re-plans
- <ISO date> · <what changed> · <phases re-derived>
```

### 4.3 STATE.md grammar

```markdown
# STATE · <project> · <goal slug>
status: running
phase: <phase>
next: <one imperative sentence>
updated: <ISO UTC>
commit: <short sha>
session: <session name>
model: <model · effort actually running>

## Resume here
Why: <one sentence>
Blocked on: none | <the single thing, who can unblock, the default being taken meanwhile>
In flight: none | <agent> → <unit> (report at .drive/local/workers/<name>/report.md)

## Verified facts
- <fact>. Verified: <command or source and date>.

## Rules in force
- <project rule>. Because: <reason>. From: <investigation or decision slug>.

## Open failures
- <date> <slug>: <symptom>. Repro: <path or command> | Observed: <n of m runs>. Next: <step>.

## Workaround ledger
| obstacle | workaround | by | when | count |

## Boundary events
- <ISO> · <step> · <classifier category or tool refusal> · <action taken> · <result>
```

`status` is one of `running`, `verifying`, `blocked`, `stalled`, `done`, `aborted`. Only
`running` and `verifying` keep the Stop gate closed.

### 4.4 STATUS.md grammar (report 10, adapted to keys)

```markdown
# STATUS · <project>
ladder: Missing → Scaffold → Partial → Local Proof → Live Proof → Operational → Done   (Dropped needs why:)

| key | claim | live | status | evidence | updated |
|-----|-------|------|--------|----------|---------|
| expired-token-is-rejected | An expired token is rejected with 401 and creates no session | y | Local Proof | test:api/tests/auth.test.ts::expired token is rejected; severe:api/tests/severe_auth.test.ts::forged expiry is rejected; verdict:.drive/proofs/expired-token-is-rejected/r2/verdict.json; commit:4f2a9c1 | 2026-09-14 |
```

Evidence tokens: `test:<path>::<name>`, `severe:<path>::<name>`, `verdict:<path>`,
`proof:<dir>`, `shot:<path>`, `live:<dir>`, `ops:<url or path>`, `review:<path>`,
`commit:<sha>`, `doc:<path>`, `why:<text>`, `planned:<path>::<name>` (only before build).
`[ui]` at the start of a claim marks a UI row.

Evidence each rung requires:

| Rung | Required |
|---|---|
| Missing | nothing |
| Scaffold | `commit:` |
| Partial | ≥1 `test:` |
| Local Proof | `test:`, `severe:`, `verdict:` whose verdict is pass; `shot:` too for `[ui]` rows |
| Live Proof | Local Proof set plus `live:` whose `proof.json` has `environment` `live` or `device` and a present `shim_differences` |
| Operational | Live Proof set plus `ops:` |
| Done | Local Proof set plus `review:` (final audit), plus `live:` when live is `y`, plus `doc:` when user-facing behaviour changed |
| Dropped | `why:` |

Rows are never deleted. Only a verifier's verdict moves a row to Local Proof or above.
Local-only work is never Live Proof.

### 4.5 Verdict schema

Adopt report 07 section 4.4 exactly (`verdict`, `unit`, `round`, `scope`, `ran`, `claims` with
`status`, `oracle`, `refutations_attempted`, `evidence`, `confidence`; `gaps` with severity
`blocking | should_fix | note`; `harness_kindness`; `not_checked`; `rung_supported`;
`for_maker`) and its validity rules. `unit` is a STATUS key or a package id. Ship it as
`templates/verdict.schema.json`. UI findings use report 09's `findings.json` shape and are
referenced from the verdict.

### 4.6 The fixed transcript block

After every gate run and verification round the orchestrator prints report 07's block:

```
DRIVE · VERIFY · <unit> · round <n>/<K>
GATES   build ok · typecheck ok · lint ok · tests 212/212 ok
VERDICT pass|fail · claims N · holds N · refuted N · blocking N · should_fix N · notes N
GAPS    <severity> <claim key> <where> <what> (one line each, blocking first)
RUNG    <unit> → <rung> (was <rung>)
FILE    .drive/proofs/<key>/r<n>/verdict.json
```

## 5. Phases and gates

Canonical phase names (used in STATE.md `phase:`, GOAL.md plan lines, and `drive.py lint --gate`):
`intake`, `archaeology`, `research`, `spec`, `design`, `test-plan`, `decompose`, `build`,
`verify`, `integrate`, `live-proof`, `harden`, `docs`, `retro`, `report`; shape-specific:
`reproduce`, `diagnose`, `fix` (fix); `inventory`, `characterize`, `cutover`, `soak`,
`decommission` (move); `content-plan`, `draft`, `design-qa`, `deploy` (publish); `plan`,
`execute`, `observe` (operate). Each shape file lists its order and per-size thinning (report 02
table 4.2 and report 13 collapse rules; where they differ, report 02's per-shape phase lists win
and report 13's gate table supplies entry and exit conditions).

Gate checkers: the orchestrator checks intake, archaeology, research completeness, decompose, and
docs; an independent agent checks spec, design, build, verify, integrate, live-proof, harden, and
the final audit. The orchestrator never certifies its own work.

Loop bounds (report 07): fix 2 rounds; feature, publish, report 3; build 3 per milestone plus 2
final; move cutover 4. Gate-fix cycles before a verifier round: 3. A blocking gap that returns
after a fix requires an investigation record before any further code change. Disputes go once to
`drive:auditor` as arbiter and the ruling is logged in DECISIONS.md.

Hardening order (report 07 section 4.5): deterministic gates; correctness verifier; conformance
grader; severe tester; security review when `auth` or the surface list applies; UI review when
`ui`; simplify (then re-gate; revert if the test baseline changed); docs review; final audit.

## 6. Agent roster (the smallest set whose model, effort, tools, or preloads genuinely differ)

| Agent | Job | model | effort | Tools and restrictions | Preload |
|---|---|---|---|---|---|
| `researcher` | web research lanes, codebase archaeology, log and config sweeps; writes only under `.drive/` | sonnet | high | Read, Grep, Glob, Bash, WebFetch, WebSearch, ToolSearch, Write | none |
| `architect` | SPEC.md, DESIGN.md, TESTPLAN.md, decomposition; also a fresh-context spec or design reviewer at S to M | opus | xhigh | Read, Grep, Glob, Bash, Write, Edit (guard: `.drive/` and docs only) | none |
| `designer` | design direction and the design contract for `ui` work | opus | high | Read, Grep, Glob, Bash, Write, Edit, ToolSearch (guard: `design/` and `.drive/`) | frontend-design |
| `implementer` | one work package: code and its claim tests, in the shared checkout; never touches git | sonnet | high | all except Agent (guard: no git mutations; owned paths reported and audited) | none |
| `writer` | prose deliverables: site copy, blog, docs, README | sonnet | high | Read, Grep, Glob, Bash, Write, Edit | writing |
| `verifier` | fresh-context correctness verification against a handoff; runs everything, edits nothing | opus | high | Read, Grep, Glob, Bash; disallowed Edit, Write, NotebookEdit, Agent (guard: read-only Bash) | none |
| `severe-tester` | refutation tests for claims; writes only tests, fixtures, proofs | opus | high | Read, Grep, Glob, Bash, Write, Edit (guard: test paths and `.drive/proofs/` only) | severe-testing |
| `security-reviewer` | read-only security review; describes weaknesses, never reproduces attacks | opus | high | Read, Grep, Glob, Bash; disallowed Edit, Write (guard: read-only Bash) | severe-testing |
| `ui-reviewer` | captures its own UI evidence and judges it against the design contract | opus | high | Read, Grep, Glob, Bash, ToolSearch; disallowed Edit (Write only to `.drive/proofs/` via guard) | none |
| `grader` | checklist grading, citation checks, conformance, dedupe classification, parity mismatch triage | sonnet | low | Read, Grep, Glob, WebFetch | none |
| `investigator` | failure investigation to a mechanism, bug diagnosis, hypothesis arms, second opinion | opus | xhigh | Read, Grep, Glob, Bash, Write (guard: `.drive/` and throwaway worktrees under `/private/tmp`) | none |
| `auditor` | final audit before Done, arbiter of disputes, lesson verifier, spec and design reviewer at L to XL build and move | fable | xhigh | Read, Grep, Glob, Bash; disallowed Edit, Write | none |

Rules:
- The orchestrator is the main conversation on `fable` at `high`. The launch recipe sets model
  and effort; intake records what is actually running and says so in one line if it is not Fable.
  The orchestrator also distills lessons (report 11) and decides cutovers.
- Per-call `model` overrides allowed: `implementer` to `opus` after two verifier failures or for a
  package the architect marks hard; `researcher` to `opus` for reconciliation; `investigator` to
  `claude-opus-4-8` once when a cyber-classifier decline is detected (report 15). No other
  overrides.
- Security review and severe testing are Opus-pinned by default, never run inline in the
  orchestrator, and attack material never enters the orchestrator's context (report 15).
- `memory:` is not used on any agent; lessons live in version-controlled files (reports 10, 11
  override report 01's verifier memory).
- Every agent ends its final message with the model it ran as, and returns a fixed-size result:
  a status line, file paths, and at most 1,500 characters; full output goes to a file.
- Guards are enforced by one plugin PreToolUse hook (`drive.py hook-guard`) that reads
  `agent_type` and applies the rule for that agent. It is inert unless `.drive/local/active`
  exists. Prompts repeat the rule; the integrator audits changed paths after each package.

## 7. Parallel execution (report 12 over report 01)

- Default substrate: one shared checkout, disjoint file ownership, workers never run git, the
  orchestrator integrates and commits per package. At most eight makers per wave.
- Worktrees only for experiment arms whose losers are discarded, bisects, and hypothesis arms in a
  bug hunt; created under `/private/tmp` from HEAD by the orchestrator or investigator; merged
  (winners only) and removed in the same step. `git worktree list` shows one entry at the end of
  every wave; `drive.py lint --stop` enforces it.
- Never use `isolation: worktree` on a subagent that edits: Claude Code does not merge it back and
  the sweep keeps worktrees with unpushed commits.
- Workflows read and judge (review panels, research sweeps, hypothesis tournaments, screenshot
  judging); Agent calls edit. Invoking `/drive` is the user's opt-in to the Workflow tool for
  those read-only fan-outs. Keep a workflow under the session's size guideline.
- Package brief and report shapes: report 12 section 4 templates, keyed by package id.

## 8. Completion, loops, and long runs

- Primary loop: the SKILL.md Stop hook `drive.py hook-stop`. It exits 0 at once unless
  `.drive/local/active` exists. Allows the stop when `background_tasks` is non-empty. Otherwise
  runs the `--stop` lint; if STATE.md status is `running` or `verifying` it blocks with the
  recorded `next:`; if status is `done` it additionally requires `lint --final` to pass; stall
  detection marks `stalled` after six consecutive blocks with an unchanged STATE.md. Every
  decision is appended to `.drive/local/gate.log`. No model call inside the hook.
- Plugin `hooks.json`: `SessionStart` matcher `compact|resume` runs `drive.py hook-reinject`
  (prints the start view); `PreToolUse` matcher `Bash|Edit|Write|NotebookEdit` runs
  `drive.py hook-guard`.
- `/goal` is optional belt and braces, recommended in the headless recipe with
  `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5` scoped to the process. The skill never depends
  on `/goal` and never names `CLAUDE_CODE_GOAL_GRADER_MODEL` (it does not exist in the docs).
- Waiting: drive it now through the system's own tools; otherwise `Monitor`; otherwise a
  self-paced `/loop` recorded in STATE.md; a schedule only for a soak with no signal, and the soak
  check decides and acts (advance, hold, roll back). Nothing is Done while a soak is open.
- Runs are local. Launch recipes (report 14): background `claude --bg --name drive-<slug>
  --model fable --effort high "/drive <goal>"`; headless `claude -p ... --permission-mode auto
  --permission-prompts none --output-format stream-json --verbose --max-turns <n>
  --max-budget-usd <n>`; environment for either: `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP=30`,
  `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0` (headless), `BASH_DEFAULT_TIMEOUT_MS=600000`,
  `CLAUDE_CODE_RETRY_WATCHDOG=1`. Keep-awake with `caffeinate` recorded in STATE.md. Cloud
  hand-off is a detected conditional; with an API-key login it is unavailable and the run says so
  in one line.

## 9. `scripts/drive.py`

One Python 3 standard-library script, no dependencies, fast (under a second on a typical
`.drive/`). Subcommands:

| Subcommand | Does |
|---|---|
| `init --goal "<text>" [--slug s]` | creates `.drive/` from templates for the size in GOAL.md, adds `.drive/local/` to `.gitignore`, writes `.drive/local/active` |
| `start` | read-at-start view: STATE header and Resume here, rung counts, open rows, open failures, workaround rows at count ≥2, lint findings (exit 0 always) |
| `lint [--gate <phase> \| --stop \| --final] [--json]` | report 10 section 4.6 checks adapted to keys and to section 4 of this file; exit 1 on failure |
| `hook-stop` | Stop hook (section 8) |
| `hook-reinject` | SessionStart hook: prints `start` output when a run is active, nothing otherwise |
| `hook-guard` | PreToolUse hook: per-agent guard rules from section 6; exit 2 with a plain reason on a violation |
| `end` | removes `.drive/local/active` after `lint --final` passes |
| `worktree-land <branch> <sha>` | fast-forward or merge, remove the worktree, delete the branch, prune; refuses if the branch moved |
| `lesson-check` | structural checks on `references/lessons/` and domain "Learned constraints" (report 11 section 4.5) |
| `lesson-commit <file>...` | one lesson, one commit in the skill repo, fixed message shape |

`scripts/tests/` holds unittest-based tests over fixture `.drive/` trees, including severe tests
that try to fool the lint (Live Proof with a simulator bundle, deleted rows, a verdict with no
commands, stale STATE, a secret in STATE, a leftover worktree).

## 10. Failure to lesson (report 11, adopted)

- Failure events: something got past a gate, or a workaround is about to be used a second time
  (full trigger list in report 11 section 4.1). Ordinary red-to-green inside a package is not one.
- Workaround ledger in STATE.md; count 2 stops the work and opens an investigation.
- Investigation record template: Fail, Investigate (three candidates and a named mechanism),
  Verify (prediction and revert check), Fix, Distill (explicit "none" allowed), Gate log.
- Distill runs in the orchestrator. Dedupe by `drive:grader`. Verification of a candidate rule
  by `drive:auditor` with report 11's seven questions.
- Routing: project fact → STATE.md or project LESSONS.md; platform constraint →
  `references/domains/<d>.md` "Learned constraints"; procedural rule →
  `references/lessons/general.md`; owner preference → auto memory note, one line in the report;
  skill defect → general rule plus an eval case, core edit proposed in the report.
- One commit per lesson in `~/Projects/drive` with `lesson(<scope>): <rule heading>`; undo is
  `git revert`. Caps: general.md 60 entries or about 4,000 tokens; each Learned constraints 40;
  standing-rules block 15 lines. A cap blocks appends until consolidation runs, immediately.
- Consult is mechanical: intake reads general.md and the selected domains' Learned constraints;
  every worker brief carries "Lessons that apply to this task" with at most ten rules verbatim;
  the verifier checks compliance against the same list.
- `references/lessons/general.md` ships seeded with the owner's already-verified rules: harness
  kinder than production; never wait on a scheduler, drive the system's own tools; second time is
  the bug; no branches or worktrees survive their step; no approval queues; drive a system through
  its API, not its database. Each seeded entry uses the lesson template with its real evidence.

## 11. Research, spec, design, tests, UI (pointers; adopt the reports)

- Research: report 05 (ledger with decision served, claim classes, checked dates and re-verify
  rules, lanes, budgets per question, docs plus probe, grader re-opens load-bearing citations).
- Spec: report 03 (requirements as claim headings, "What would prove this wrong" scenario,
  assumptions with reversal cost, one batched question only for irreversible choices with no
  defensible default, lint and trace, templates per shape). With `AskUserQuestion` disallowed, the
  one question is written as plain text at the end of a turn that delivered all independent
  progress, with its default applied immediately for reversible choices; the run blocks only for
  irreversible, destructive, credential, payment, or legal steps.
- Design: report 04 (contract package as the seam, design review with pre-mortem, sizing,
  decision records inside DESIGN.md's decision index rather than a docs/decisions directory unless
  the repo already has one).
- Tests: report 08 (one refutation test per claim at the cheapest layer that can refute it,
  real runtimes over shims, kindness ledger in TESTPLAN.md, limits probe, flake quarantine rules,
  never widen an assertion without a spec change).
- UI: report 09 (contract before pixels, state harness and build stamp, reviewer captures its own
  evidence, capture matrix, objective checks before vision, five observations per variant and the
  worst element, templated-default tells, three rounds, Local versus Live Proof for UI).

## 12. Evals

`evals/` follows `claude plugin eval` layout with the cases in report 11 section 4.6 plus: XS
restraint (a one-line fix must not create `.drive/`), classification (the five example prompts
classify as report 02 section 4.8 says), verifier isolation (the handoff contains no maker
summary), mirage refusal (Local Proof never reported as Live Proof), and example-only restraint
(a prompt that describes a project as an example must not scaffold it). Judge model `sonnet`.

## 13. Conflicts resolved

| Topic | Reports | Decision |
|---|---|---|
| Worktrees for implementers | 01 (per concurrent implementer) vs 12, 19 (shared tree) | shared tree with ownership; worktrees only for discarded arms, bisect, hypotheses |
| File layout | 01, 07, 10, 11, 13, 14 each differ | section 4 of this file |
| Requirement identifiers | 10 (R-01) vs 03, 11 (words) | slugs of claim words; no numbers |
| Verifier memory | 01 (memory: user) vs 10, 11 (none) | none |
| Stop-hook model judge | 14 (nested claude -p Sonnet judge) vs 01, 10 (deterministic) | deterministic hook; model judgment belongs to the auditor at Done |
| Goal grader variable | 06 vs 01, 14 | `ANTHROPIC_DEFAULT_HAIKU_MODEL` only |
| Spec author model | 03 (Fable author) vs 06 (Fable reviewer) | `architect` (opus xhigh) authors; `auditor` (fable) reviews at L to XL build and move |
| Asking the user | 03 (AskUserQuestion batch) vs 01, 14 (disallow) | disallow the tool; one plain-text question with a default, section 11 |
| Decisions file | 04 (docs/decisions ADRs) vs 10 (one DECISIONS.md) | DECISIONS.md, unless the repo already keeps ADRs |
| Size names | 13 (small to greenfield) vs 02 (XS to XL) | XS to XL |
| Proof layout | 07 (proofs/<unit>/rN) vs 10 (proofs/<ID>/proof.json) | both: manifest at `proofs/<key>/proof.json`, rounds under `r<n>/` |

## 15. Amendments from report 21 (skill ecosystem)

These override sections 5, 6, 8, and 9 where they differ.

1. **Preloads and tools per agent.**

| Agent | `skills:` preload | Tools change |
|---|---|---|
| `researcher` | `deep-research` | add Skill (so a brief can name `tavily-dynamic-search` or `tavily-research`) |
| `architect` | none | add Skill; briefs name `frontend-design`, `dataviz`, or `claude-api` when relevant |
| `designer` | `frontend-design` | briefs say "match the existing design system" for features on existing products |
| `implementer` | none | add Skill; briefs name stack playbooks (`rust-refinement`, `vercel-react-best-practices`, `react-component-performance`, `claude-api`) when relevant |
| `writer` | none | model `opus`, effort `high`; add Skill; the brief names the prose skill resolved at preflight (`writing` or `arcwell:writing`) and `google-dev-docs-style` for docs; story mapping for substantial narratives is an Agent call with `model: "fable"` made by the orchestrator |
| `verifier`, `grader`, `auditor` | none | `tools: Read, Grep, Glob, Bash` only; no Skill, no WebFetch; citation checks use `curl` or `tvly extract` raw text |
| `severe-tester` | `severe-testing` | add Skill |
| `security-reviewer` | `severe-testing` | add Skill; it invokes the Skill tool with `security-review` itself (so the review runs on Opus, never on Fable in the orchestrator), after checking the diff range is non-empty |
| `ui-reviewer` | none | report 21 section 4.4 frontmatter: Read, Grep, Glob, Bash, ToolSearch, Skill, `mcp__playwright__*`, `mcp__chrome-devtools__*`, `mcp__Claude_Code_iOS_Simulator__*`, `mcp__Claude_Browser__*`; disallowed Write, Edit, NotebookEdit, `mcp__playwright__browser_run_code_unsafe`, `mcp__playwright__browser_file_upload`, `mcp__chrome-devtools__upload_file`, `mcp__chrome-devtools__execute_3p_developer_tool`; briefs name `frontend-design` as a taste lens when useful |
| `investigator` | none | add Skill; briefs name `severe-testing` for the verify rung |

2. **Orchestrator-invoked skills.** The orchestrator itself runs `/code-review <level> <baseline_sha>...HEAD`
   (always with level and range) in parallel with the verifier on existing codebases, `/simplify
   <paths touched since baseline>` after a pass, `/run` when it needs the app launched and no
   project run recipe exists, and `workflow-authoring` before its first Workflow script. It never
   runs `/security-review` in its own context. Intake records `baseline_sha` in GOAL.md's probe.
3. **Capability preflight.** `drive.py capabilities` writes `.drive/capabilities.json` (skills by
   directory with dangling-symlink detection, plugin variants such as `arcwell:writing`, CLIs:
   `gh` auth, `tvly`, `imagegen`, `xcodebuild`, `simctl` booted device, `wrangler`,
   `agent-browser`, git origin, `baseline_sha`). The orchestrator merges ToolSearch probes for
   Playwright, Chrome DevTools, the iOS Simulator MCP, Tavily, and the Browser pane. The fallback
   table in report 21 section 4.6 goes into `references/capabilities.md`. A missing verification
   capability lowers the ceiling of the claims it would have verified; it never lets a layer pass.
   Missing capabilities are reported once, in STATE.md and the final report.
4. **Headless reality.** The iOS Simulator MCP and the Browser pane exist only in the Desktop app.
   Headless runs verify iOS with `xcodebuild test` plus XCUITest and `xcrun simctl io <udid>
   screenshot`, and web with Playwright MCP or `npx playwright`. The verdict names the surface used.
5. **Second read-only guard.** Add `drive.py hook-snapshot start|stop`, registered in
   `hooks/hooks.json` on `SubagentStart` and `SubagentStop` with matcher
   `^(drive:)?(verifier|grader|ui-reviewer|auditor|security-reviewer)$`: record HEAD and a hash of
   tracked-file status at start; on stop, if either changed, block with an instruction to revert
   and report, and write a line to `.drive/local/gate.log`. The orchestrator discards that
   agent's verdict and opens a failure note. All guards accept `agent_type` with or without the
   `drive:` prefix.
6. **Never.** Drive never posts PR comments, opens pull requests, or publishes on the owner's
   behalf; never uses `claude-in-chrome` or `chrome-cdp` (the owner's real browser) for
   verification; never invokes `improve`, `/batch`, or the `skill-creator` review viewer; reads
   their reference files for method when useful.
7. **Skill quirks** found during runs are platform constraints for the lesson router: they go to a
   "Learned constraints" section at the end of `references/capabilities.md`, capped at 40.

## 16. Amendments from report 22 (source verification)

These override earlier sections and reports 15 and 06 where they differ.

1. **Classifier fallback is automatic and sticky in Claude Code, headless included.**
   `switchModelsOnFlag` defaults to true (settings reference; model-config). A flagged request
   switches the session to Opus 4.8 (cyber) or Opus 5 (bio) and stays there. Leave the default;
   setting it false makes a `-p` run end the flagged request as an error. The danger is a silent
   downgrade of the orchestrator, so: keep attack material inside Opus-pinned subagents; record
   the serving model at every phase gate; treat any `model_refusal_fallback` event or model change
   as a Boundary event and a finding. The one explicit retry on `claude-opus-4-8` applies only when
   a subagent returns a refusal result. Report 15's "no fallback for frontier_llm" is unconfirmed;
   do not state it.
2. **Never nag makers.** Do not tell makers to double-check, self-verify, or spawn their own
   reviewers (Opus 5 guidance: such instructions cause over-verification; Claude Code on Fable:
   skip verification reminders). Verification is a structural step the orchestrator schedules at
   defined checkpoints with fresh agents against claims and rubric.
3. **Never ask for reasoning text.** No prompt, template, or brief asks an agent to show, echo,
   transcribe, or explain its reasoning or chain of thought; that can trigger the
   `reasoning_extraction` refusal on Fable. Ask for conclusions with evidence.
4. **Recall wording for reviewers.** Graders, verifiers, and reviewers report every finding with
   confidence and severity; filtering happens afterwards in a separate step. Never tell a reviewer
   to be conservative or to report only important issues.
5. **Official blocks to use nearly verbatim** (Prompting Fable 5.1): the autonomous-operation
   block (already in SKILL.md section 1), grounded progress claims ("Before reporting progress,
   audit each claim against a tool result from this session..."), scope as deliverable, keep
   changes and tests to the task (makers write the tests the test plan asks for, sized like
   neighbouring tests, and nothing more), check evidence before state-changing commands, final
   message as re-grounding, and the six-item compaction or phase-handoff summary (difficulties and
   how handled; options raised, tried or set aside and why; everything decided or ruled out,
   exactly; where things stand; what is open; hard-to-reconstruct details exactly).
6. **Brief opening.** Every subagent brief opens with the reason: "I'm working on <larger task>
   for <who>. They need <what the output enables>. With that in mind: <request>." Sonnet and Opus
   workers get precise instructions; Sonnet follows literally and does not generalize.
7. **Lessons become checks.** Wherever possible a distilled lesson becomes a test, lint rule,
   hook, or gate, not only prose (Fable system card: "correction fails" is a recurring shortfall).
8. **Subagent model resolution** since v2.1.251: per-invocation `model`, then agent frontmatter,
   then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main model. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`
   overrides all; the install notes must warn that it would break the roster.
9. **Evaluator calibration.** UI and design judges use few-shot examples with score breakdowns,
   weighted criteria with hard floors, and a penalty list of generic patterns. Divergences between
   a judge and later evidence are failure events that tune the judge prompt through the lesson loop.
10. **Rubrics.** Process criteria (a baseline exists, the corpus ran) are legitimate and cheap to
    grade. A verdict distinguishes "rubric does not fit the deliverable" (`rubric_gap`) from "work
    not done". A known-good artifact, when one exists, is the best source for a rubric.
11. **Session start runs a smoke test** before any new work (Anthropic's long-running harness).
    STATUS stays Markdown with lint-enforced row retention; the JSON-is-safer observation is
    answered by the lint and the rule that only the orchestrator edits STATUS.
12. **Cost facts.** Fable costs about twice Opus per token, not five times. Haiku 4.5 may retire
    from 2026-10-15, one more reason it is absent.
13. **Workflow scripts.** `Date.now()` and `Math.random()` throw (pass timestamps in `args`);
    `agent()` returns null when blocked (filter and count); a relaunch reruns everything after the
    first failure in a fan-out.

## 17. Amendments from report 13 sections 5 to 9

1. **Targets are fixed at intake and committed.** GOAL.md is committed to main before any other
   work, and every STATUS row's `live` value is fixed when the row is created. Lowering a target
   (a `live` y becoming n, a claim moving to Dropped, a phase removed from the plan) requires a
   DECISIONS.md entry in the same commit. `drive.py lint` fails when a `live` value flips from y to
   n, or a row becomes Dropped, without a DECISIONS.md change in the working tree or the commits
   since.
2. **The auditor compares against intake.** The final audit reads the intake commit of GOAL.md and
   the final STATUS, lists every narrowing, checks each has a decision, and blocks a report that
   describes plans or intentions as results.
3. **No gatekeeper agent.** Report 13's `drive-gatekeeper` is covered by `drive:verifier` (per-unit
   gates) and `drive:auditor` (phase and final audits); no new roster entry.
4. **Hooks.** `${CLAUDE_SKILL_DIR}` is not expanded in hook commands, and a skill-frontmatter
   SessionStart `resume` hook can never fire; re-injection stays in the plugin `hooks.json`, and
   SKILL.md hook commands use the `$HOME/.claude/skills/drive` path.
5. **Orchestrator effort stays `high`** (report 13 section 6.3 over reports 06 and 12).

## 18. Amendments from report 23 (addyosmani/agent-skills extraction)

Take the content, reject the human-in-the-loop control model. Every "ask first", "the human
reviews", or "stop and wait" in lifted material becomes decide-and-log with a reversal cost, a
verifier verdict, or the single question. Report 23 section 5 lists 21 conflicts; drive's rules win
on all of them. Additions that override earlier sections:

1. **The constraints floor.** For M and above, `.drive/CONSTRAINTS.md` records the quality floor:
   one row per rule with the exact command, the measured value, the direction (must not fall, must
   not grow), a tolerance, and the reason. With no owner target, measure today and record it;
   never set a threshold the codebase fails today. Changing a row is its own commit with evidence.
   `drive.py guard` runs before every integration commit over staged, unstaged, and untracked
   files: it blocks added suppression comments and skips, removed assertions in test files that
   still exist, added stubs or empty catches, a loosened CONSTRAINTS.md value, and an unrecorded
   exception; it does not flag date edits as lowered thresholds; exit 0 clean, 1 violation, 2
   could not run (treated as failure). Tightening passes silently; loosening is loud.
2. **Standing rule against lowering the bar** (report 23 passage 7) goes into SKILL.md.
3. **Excuses and red flags.** Shape and topic references carry a short "Excuses and rebuttals"
   table (the argument an agent uses to skip a step, and why it fails) and a "Red flags" list of
   observable signs, where the step is one agents skip: integration, verification, lessons,
   completion, test design, research.
4. **Operational rung standard** (passage 20): written on-call questions, structured events with a
   correlation id, a test-fired alert, and one induced failure located from telemetry alone.
   Lives in `references/observability.md`.
5. **Security references** (passages 16, 17): `references/security.md` holds the threat model
   (trust boundaries including model output and values written by other processes; STRIDE; abuse
   cases as the severe tester's first tests), the derived-path deletion check (also applied to
   drive's own cleanup), idempotency (passage 18), install-script and dependency gates, and
   retention and deletion. `references/safety.md` keeps the classifier and model-independent
   boundaries.
6. **Measurement honesty** for every verifier and reviewer (passage 9): never report an unmeasured
   value; label every value with its source.
7. **Verifier reconcile order and doubt theater** (passage 10) go into `references/verification.md`.
   Give the verifier what must be true, never the maker's assertion that it holds.
8. **Keep or revert** for perf and experiments (passage 15) with an attempt ledger kept in HUNT.md
   (fix/perf) or RESEARCH.md; neutral results are reverted.
9. **Expand and contract** (passage 19) goes into `references/shapes/move.md` and the Cloudflare
   file's migration discipline.
10. **GOAL.md opens with the restate block**: outcome, user, why now, success, constraints, out of
    scope; each line quoted from the goal or marked as an assumption.
11. **Capability map** (passage 12) precedes the spec for build and large feature shapes; module
    build order becomes wave order.
12. **Decision tiers** (passage 11): always; allowed once the undo is written in STATE.md or
    DECISIONS.md; never. Only a step with no possible undo can become the single question.
13. **Paused runs** (passage 14): if `.drive/` holds unfinished work for a different goal,
    `drive.py init` archives it to `.drive/runs/<date>-<slug>/`, records how to restore it, and the
    final report names it. Same goal means resume.
14. **Recon commands** (passage 1): the exact build, focused-test, and full-suite commands are
    written into GOAL.md's probe and quoted in every brief. Never assume a default.
15. **Worker report** adds `noticed_not_touched` (file, problem, one-line reason) and
    `concerns`; the integrator carries them into STATE.md discoveries and the final report.
16. **Bugs** (passage 2): for a complex bug, a subagent that has not seen the fix writes the
    reproducing test from the report and the code alone.
17. **Test doubles** (passage 3): real, then fake, then stub, then a call-checking mock only where
    unavoidable; assert on outcomes.
18. **Dead code** is deleted only with zero-reference evidence (dynamic lookups, configuration,
    other repositories found at recon) in its own commit; otherwise it is a discovery.
19. **Never `git reset --hard`** in a shared checkout; restore only a package's owned paths, or
    `git reset --keep` on the integrator's own merge.
20. **External CLIs of other vendors** run only if configured, read-only, prompt on stdin; otherwise
    skipped with one line.
21. **Evals** (passage 22): fixtures copied into a fresh git repository with a committed baseline;
    headless runs with edit permissions; grade tool calls and file changes from the stream-json
    trace, fenced as untrusted; reject grading whose counts disagree; three repeats and one run
    without drive; pressure cases (arguments to skip verification) and mirage cases (a double
    kinder than production).
22. **Skill-repo self-checks**: `drive.py selfcheck` verifies every reference path named in
    SKILL.md, agents, and references exists, every template path named anywhere exists, and SKILL.md
    stays under its line cap.
23. **Rejected lessons** are recorded in `references/lessons/rejected.md` with the reason, so a
    false lesson is not proposed twice. Removing or weakening a lesson needs consolidation
    evidence; adding a verified one is an ordinary commit.
24. **Attribution**: `THIRD_PARTY_NOTICES.md` at the repository root carries the MIT notice for
    addyosmani/agent-skills (commit be4e44a). Files that lift substantial passages nearly verbatim
    carry a one-line header naming the source file; adapted material needs only the notices entry.

## 19. Decisions recorded from drafting agents

1. `drive:verifier` may write through Bash under `.drive/proofs/` and `/private/tmp`; it owns claims
   audits and docs smoke tests (no separate roster entry).
2. `drive:architect` may write `.drive/`, `docs/`, `design/`, and a web project's claims ledger at
   `src/content/claims/`.
3. Publish runs keep positioning, site map, and page briefs in `.drive/content-plan/`.
4. A site reaches Live Proof only when production serves the tested build; preview-only results are
   Local Proof. For services where Operational is in scope, a STATUS row for operability must reach
   Operational before Done.
5. `drive.py capabilities` uses flat keys and preserves `git:baseline_sha` across re-runs; any
   `<plugin>:writing` variant is accepted; `/code-review` runs at `medium` for fix and S, `high`
   otherwise, never `ultra`; drive never invokes `anthropic-skills:simplify` or the `design` canvas.
6. The wave table lives in `.drive/packages/index.md` (template `packages-index.md`) with an
   `## Integrator-owned` section; briefs carry `## Files you own`. Worktrees are `drive/<slug>` at
   `/private/tmp/drive-<repo>-<slug>`; the orchestrator commits an arm's work; a failed landing is
   undone with `git revert`.
7. The Agent tool's `model` accepts aliases only, so the Opus 4.8 retry runs as
   `claude -p --agent drive:<role> --model claude-opus-4-8`.
8. Launch recipes pass environment, the Workflow allow rule, and prompt cache TTL through
   `--settings`, because exported variables are not documented to reach `--bg` sessions. `/goal`
   runs as a separate resumed leg, never in the same prompt as `/drive`. `caffeinate` never runs as
   a harness background task (it would make the Stop gate allow every stop). A soak with nothing
   else to do sets `status: blocked`.
9. iOS: device UDIDs and raw result bundles live in gitignored `.drive/local/ios/`; enumerations,
   summaries, manifests, and screenshots go in the proof round directory. Project scripts under
   `scripts/ios/` may be run by verifiers and ui-reviewers. Device-only claims may reach Local Proof
   with `why:device-only:<reason>` and never Done; team-blocked claims stay at Partial. A missing
   simulator runtime is downloaded with the undo recorded, not asked about.
10. Spec: a size-S feature or build writes a short SPEC.md under 300 words; the report brief is a
    `## Brief` section at the top of RESEARCH.md (template `report-brief.md`); spec structure is
    checked by `drive.py lint --gate spec` plus the reviewer's rubric; spec-time assumptions stay in
    SPEC.md and later decisions go to DECISIONS.md, both listed in the report; spec review uses the
    verdict severities; test names use the claim's words, slugs only where a framework needs an
    identifier; rows whose requirement text changed drop to Partial until a new verdict round.
11. Intake and done: the intake commit message is `drive(intake): <slug>`; the final audit verdict is
    `.drive/reviews/<date>-final-audit.json`; when the auditor is not required, a fresh verifier runs
    the final-audit checklist; sub-goals get `## Classification · <slug>` and `## Plan · <slug>`
    sections in one GOAL.md; the probe records build, focused-test, and full-suite commands and
    system tools; for report and operate rows `test:` means the citation check or read-back and
    `severe:` means the adversarial reading or undo check; the auditor breaks tests in a
    `git archive` copy under `/private/tmp`, never a worktree.
12. Design and research: `.drive/capability-map.md`; probes committed under `.drive/research/probes/`,
    lane reports and saved page text under gitignored `.drive/local/research/`; the full decision
    record lives in DESIGN.md's decision index with a one-line pointer and undo in DECISIONS.md; the
    contract package is `contracts/` at the repository root; design reviews, citation grading, and
    design consistency checks write JSON under `.drive/reviews/` with verdicts pass,
    pass-with-changes, or block and the three severities; archaeology stays on the sonnet researcher.
13. UI: `drive:ui-reviewer` writes through Bash only under `.drive/proofs/<key>/r<n>/` and
    `.drive/local/ui/`; full-size screenshots are gitignored with hashes recorded, review copies and
    crops are committed; findings open after round three go to STATE.md and minor ones to the report;
    web widths are 360, 768, 1280, 1600.
14. Security and observability: `drive:security-reviewer` and `drive:auditor` write through Bash only
    under `.drive/reviews/`; at XS the reviewer returns findings in its final message; scratch
    ownership evidence is `.drive/local/scratch.list`; the threat model lives in DESIGN.md (or SPEC,
    HUNT, MIGRATION below M); on-call questions live in DESIGN.md `## Operations`; operability
    evidence is `.drive/proofs/<key>/r<n>/ops.md`; an injected fault is recorded in
    `.drive/local/ops-<key>-fault.md` and hidden from the verifier who must diagnose it from
    telemetry alone; the log field naming what started a run is `trigger`.
15. Testing and verification: when the auditor is not required, a fresh `drive:verifier` (never the
    grader) runs the final-audit checklist; disputes are recorded in
    `.drive/reviews/<date>-dispute-<key>.md`; a rubric gap is a `not_checked` entry starting
    `rubric_gap:`; operate rounds are bounded at 2 per observed step; the pre-fix check runs in a
    detached worktree the orchestrator creates under `/private/tmp` at the pre-fix commit and removes
    in the same step; mutation checks run in an rsync copy under `/private/tmp/drive-*`;
    `.drive/CONSTRAINTS.md` also records the project's own constraints file when one exists.
16. Agents: the verifier writes its own `verdict.json` under `.drive/proofs/<key>/r<n>/` through Bash
    and the orchestrator validates it before any STATUS change; the final audit output is
    `.drive/reviews/<date>-final-audit.json`; pre-fix code is exported with `git archive` into
    `/private/tmp/drive-*` (no worktree) for both verifier and severe tester; UI findings map
    blocking and major to blocking gaps and minor to should_fix; the researcher may use Tavily MCP
    tools when present and the `tvly` CLI otherwise.
17. Shapes: `fix/incident` mitigation is an `execute` phase before `archaeology`, and every incident
    gets the auditor; below L, fix and publish save a fresh verifier or ui-reviewer check to
    `.drive/reviews/` as their `review:`; blast radius and dialect notes are sections of SPEC.md (or
    change-spec); move recordings go in `.drive/local/recordings/`, backups in `.drive/local/backups/`,
    goldens in the project's test tree; old-store deletion after the rollback window is a dated
    STATE.md line outside Done; a publish run deploys to a preview always and to production when the
    goal asks for a launch or a production target already exists, otherwise its rows stop at Local
    Proof with the promote command in the report; fixes skip `/simplify`; plan-line checkers may name
    any roster agent. Conflict resolved: pre-fix code is always a `git archive` copy under
    `/private/tmp/drive-*`, never a worktree (item 16 wins over shapes/fix.md and verification.md,
    which the integration review corrects).

## 20. Rulings from the integration reviews (reports 26, 27, 28)

These override every earlier section and item where they differ.

1. **Where a run lives.** A run lives in the repository its session started in. When the goal targets
   another existing repository, or is new work in an unrelated directory (new repository under
   `~/Projects/<slug>`), SKILL.md section 2 step 0 launches a background session there and stops.
   Hooks resolve the run from the hook input's `cwd`. Every brief states the repository root as an
   absolute path and writes commands as `cd <root> && <command>`.
2. **Honest stops.** STATE status gains `stopped`: the run ended short of Done for a stop condition,
   all independent work is finished, and REPORT.md opens with "Stopped because". `lint --final`
   passes with `done` when every row is Done or Dropped, and with `stopped` when every row below Done
   carries its reason (an Open failure, the Blocked on line, a `why:` token such as
   `why:device-only:`, or a DECISIONS.md narrowing), REPORT.md's counts match STATUS, no
   investigation is open, and a retro exists. `drive.py end` accepts `done` or `stopped` after
   `lint --final`, or `aborted`. The Stop gate treats `stopped` like `done`.
3. **Compaction.** SKILL.md keeps the contract, standing rules, start, intake, phase loop, proof,
   and delegation first; the injected start view sits after section 6; `hook-reinject` prints the
   start view, then SKILL.md's section 1, the standing rules, section 6, and `## 7. ` to the end
   (failures, waiting, stopping, reference index). (Amended after the tooling hardening: compaction
   re-attaches only the first 5,000 tokens of an invoked skill and may drop an older skill entirely,
   so the contract and the delegation rules are printed again rather than trusted to survive.)
4. **Auditor coverage.** `drive:auditor` runs the final audit for build, move, every `fix/incident`,
   a feature with five or more claims, and any run at L or above (amended after the fix pass: every shape at L and above).
   Otherwise a fresh `drive:verifier` runs the same checklist. The grader never does.
5. **Review files.** The verifier and ui-reviewer may write, through Bash, the one output file under
   `.drive/reviews/` their brief names when they run a final-audit checklist, a close check, or a final
   review, in addition to their proof paths. `verifier.md` gains an "Other modes" section: final-audit
   checklist, claims audit, docs smoke test, telemetry-only diagnosis (no source reading), operate
   observation, and plan review, each naming which standard steps it skips.
6. **Final audit file** is `.drive/reviews/<date>-final-audit.json`. The intake commit is found with
   `git log --grep '^drive(intake): <slug>$' --format=%h -1`, never by the first addition of GOAL.md.
7. **Incident mitigation** is an `execute` phase before `archaeology`; `mitigate` is not a phase name.
8. **Citation evidence** for report and site rows: the grader writes
   `.drive/reviews/<date>-citations-<slug>.json`, and the row's token is
   `test:.drive/reviews/<date>-citations-<slug>.json::every citation resolves`; the lint accepts a JSON
   file under reviews for `test:`.
9. **Contracts.** `drive:architect` specifies the contract in DESIGN.md section 4; the `contracts/`
   package is a wave 0 `drive:implementer` package; a contract change is its own package, committed by
   the orchestrator as `contract: <change in words>`.
10. **Fix rows at S** get one severe test on an adjacent input by `drive:severe-tester`, so Local Proof
    is reachable at every size above XS.
11. **Plan-line checkers** are `orchestrator` or any roster agent name.
12. **XS security review** writes no file; findings return in the final message and the commit body
    records the counts.
13. **Dispute rulings** use `defect`, `not_a_defect`, `rubric_ambiguous`; UI findings map `defect` to
    upheld and `not_a_defect` to overruled; the orchestrator writes DECISIONS.md from the ruling.
14. **Pre-fix code** is a `git archive` copy made by the verifier or severe tester under
    `/private/tmp/drive-prefix-<key>`; the handoff names the pre-fix sha, never a tree path.
15. **Classification review.** At M and above a fresh `drive:architect` reviews the classification
    before the intake commit; at XL phase gates the re-classification review is `drive:auditor`.
16. **Retro** runs on every run above XS, whether it ends `done` or `stopped`. A verifier rejection of
    work whose own gates were green is a retro candidate; it opens an investigation only when the same
    gap returns after a fix or no gate the maker ran could have caught it.
17. **Lesson commits** carry `Project: <repository directory name>` and `Run: <goal slug>` in the body;
    consolidation counts those. Launch settings add the skill repository to `additionalDirectories` so
    background and headless runs can commit lessons; pre-flight checks it is writable.
18. **Agent file paths.** Agent files name skill files as `~/.claude/skills/drive/<path>`, never bare
    `references/` or `templates/`, because subagents run from the project directory.
19. **Public repositories.** When `gh repo view --json visibility -q .visibility` is `PUBLIC`, commit
    only GOAL, STATE, STATUS, DECISIONS, and REPORT; ignore proofs, reviews, investigations, and
    research, and record the choice in DECISIONS.md.
20. **A fix goal with no symptom** searches earlier `.drive/` open failures, failing CI runs, open bug
    issues, the system's own logs, and auto memory notes; takes the best-evidenced failure as an
    assumption; stops with a report of what was searched when nothing is found.

## 21. Rulings after the final clean review (report 32)

1. **Threat model.** Drive's hooks and the orchestrator run as the same user with the same shell, so
   no command filter can prevent deliberate tampering; three reviews in a row found new shell tricks
   around the guard. The guard's job is to make honest mistakes and lazy shortcuts fail loudly, and
   provenance's job is to make tampering evident. Stop adding command-pattern special cases for
   adversarial constructions (string concatenation, variable indirection, copied scripts).
   Documentation states this plainly and never claims the guard refuses every write.
2. **Transcript-backed provenance.** A ledger entry counts only when the SubagentStop input's
   `agent_transcript_path` exists, belongs to the recorded agent type, and contains a tool call that
   wrote the evidence file; the entry stores that transcript path and its sha256, and the lint
   re-checks both. Hand-written entries or hook invocations without such a transcript never count.
3. **No pushes, no branches, anywhere.** `git push`, `gh pr`, `gh release`, and `gh repo` write verbs
   are refused for every role and the main thread unless GOAL.md records a deploy that needs them.
   Branch creation, `branch -f`, `update-ref refs/heads/*`, `symbolic-ref`, `checkout -b`, `switch -c`,
   and tag creation are refused in every worktree whose common git directory is the run repository's.
   Hygiene fails on any local branch not listed in `baseline.json`.
4. **Resume re-creates the marker** when `.drive/STATE.md` exists; relaunch instructions set
   `status: blocked` with a "launch preflight" Blocked on line before ending the turn.
5. **`none` means no suite**, and shapes without a suite skip the full-suite requirement.
6. **Sub-goal rows** carry a `sub:<slug>` evidence token; gates with `--sub` check only those rows.

## 14. Pending inputs

Reports 16 (iOS), 21 (skill ecosystem), 22 (source verification), 23 (agent-skills extraction)
and the completion of 13 (sections 5 to 9) land after this file. When they do, the coordinator
amends this file first, then the drafting agents apply the amendments.
