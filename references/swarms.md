# Swarms: parallel lanes, workflows and parallel safety

Parallelism buys breadth and clean context, not correctness, and it multiplies tokens (multi-agent systems ≈15× chat,
single agents ≈4×). A swarm is a budget decision first and an architecture decision second: it has an entry test, a
pattern, a partition, an integrator and a merged-result verifier, or it does not run. Covers pattern selection, the
go/no-go, execution surfaces, worktree isolation and ownership, serial integration, lane briefs, returns and
checkpoints, scheduling and caps. Brief body: `templates/brief.md` (`orchestration.md` W4); swarm extension:
`templates/lane-contract.md`. Hypothesis experiment lanes: `debugging.md` DBG-40..42. Names follow `conventions.md`;
if this file disagrees, conventions wins. Rule prefixes: **SW** swarm rules · **SWM** swarm model routing.

Terms. **Lane**: one agent working one task `T-NNN` in a wave (lane id = task id, conventions §3); per-item units inside
one workflow task use `<T-NNN>-<item-slug>` as directory and worktree names. **Writer lane**: may edit files.
**Reader lane**: read-only (research, audit, review lens, hypothesis experiment without commits). **Wave**: lanes
dispatched together with disjoint owned paths. **Wave file**: `.mission/lanes/W<k>.wave`, one line per lane,
`<T-NNN> <glob> [<glob> ...]`. **Integrator**: `mission-integrator`, never a lane maker.

## When to load

| Moment | Use |
|---|---|
| Phase 3 Design, ≥2 lanes will write in parallel | SW4, `templates/CONTRACTS.md` |
| Phase 4 Plan: computing waves | SW1–SW3, SW25–SW28, `templates/swarm-decision.md`, `scripts/check-ownership.sh` |
| Before dispatching >2 agents at once (writers or readers) | Go/no-go (SW1), pattern table |
| Phase 5 Build: dispatch, babysit, integrate a wave | SW11–SW24, Procedure P3–P8 |
| Research, audit, tournament, best-of-N, naming | Pattern table, Shape conditionals |
| Headless, CI or overnight lanes | SW7, SW8, SW29, `scripts/run-wave.sh` |
| A lane stalls, ≥2 lanes fail the same way, a merge goes red | SW6, SW15, SW22 |
| Mission end | SW18 cleanup gate |

| Artefact | Template / script | Target |
|---|---|---|
| Frozen cross-lane decisions | `templates/CONTRACTS.md` | `.mission/CONTRACTS.md` |
| Go/no-go checklist + STATUS swarm section | `templates/swarm-decision.md` | `.mission/STATUS.md` → `## Swarm` |
| Lane brief extension + JSON return schema | `templates/lane-contract.md` | appended to the filled brief → `.mission/lanes/<T-NNN>/brief.md` |
| Wave file | written by the orchestrator | `.mission/lanes/W<k>.wave` |
| Ownership overlap check | `scripts/check-ownership.sh` | `.mission/bin/check-ownership.sh`; output → `.mission/logs/ownership-W<k>.txt` |
| Headless lane runner | `scripts/run-wave.sh` | `.mission/bin/run-wave.sh`; writes `.mission/lanes/<T-NNN>/result.json` |

## Core rules

### Which role is parallel (the reconciliation)

Anthropic's research system and Cognition's "don't build multi-agents" agree once roles are separated. The skill's
position:

| Stance | Rule | Why |
|---|---|---|
| **Parallel readers, single writer** (default) | Research angles, audits, review lenses, hypothesis experiments run in parallel; one writer per shared surface | Readers never collide. Actions carry implicit decisions; conflicting decisions carry bad results (Cognition: two subagents built a Mario background and a mismatched bird). Cognition's 2026 follow-up keeps writes single-threaded (secondary summary) |
| **Parallel writers only on pre-decided, partitioned surfaces with machine-verifiable success** | Writers need disjoint `owns:` globs, frozen `CONTRACTS.md`, per-lane executable checks | Carlini's 16-agent C compiler worked while there were many distinct failing tests; on the monolithic Linux build every agent hit the same bug and overwrote each other until a GCC oracle re-partitioned failures by file |
| **Taste → N proposals → one writer** | Design, architecture options, copy, naming: parallel proposals, tournament, then a single writer implements the winner | No oracle means parallel writers diverge silently; comparative judgement beats absolute scoring |
| **Budget first** | Estimate lanes × per-lane tokens × 1.3 retry factor before GO | Token usage alone explains ~80% of performance variance in Anthropic's BrowseComp analysis; over-spawning ("50 subagents for simple queries") was an early failure |

No-swarm defaults (any one → single writer or sequential): coupled edits (same files, shared schema or migration,
lockfile, cross-cutting rename); shared mutable runtime (database, dev-server port, simulator, global cache) without a
per-lane instance; tiny units (< ~15 minutes single-agent work or ≤ ~3 files); requirements still ambiguous (spec
first, never "let the swarm explore implementation"); infra/CI changes.

### Pattern selection

Pick from the work shape (SW2). Default to per-item pipelines (maker → verifier per item); use a barrier (wait for
all items) only when the next stage needs cross-item context: dedup, ranking, synthesis.

| Pattern | Preconditions | Lane shape | Cost profile | Characteristic failure | Stop / merge rule | Default agents |
|---|---|---|---|---|---|---|
| **Pipeline** | Fixed ordered stages, programmatic gate between | 1 agent per stage | ≈ sum of stages; latency ↑ | Weak gate lets garbage flow downstream | Gate FAIL → back to stage with log; max 2 bounces → escalate | per stage (Model routing) |
| **Classify-and-act** | Distinct categories; classifier accuracy measured; routes differ in price or treatment | 1 classifier (fixed enum output) → routed lanes | classifier cheap; saves money only if routes differ | Misclassification sends hard items to cheap lanes | Low confidence or unknown → higher route | `mission-checker` classifier; routed makers |
| **Fan-out / map-reduce** | Units independent; results mergeable; N ≥ 3; each unit ≥ ~15 min | N readers or N partitioned writers → barrier → 1 synthesizer | N × unit + synthesis; wall-clock ↓ | Duplicate work, gaps, inconsistent implicit decisions, synthesizer overload | Synthesizer needs every return or an explicit null listed as a gap | readers `mission-scout`/`mission-worker`; synthesizer `mission-builder` |
| **Adversarial verification per item** | Artifact + criteria + checks exist | per item: maker → fresh verifier (artifact, criteria, evidence only) | ~0.3–1× maker cost per item | Rubber-stamp verifier; verifier sees maker reasoning | FAIL with evidence → maker retry → SW22 → escalate | `mission-verifier` with a different lens; risky → `mission-critic` |
| **Loop-until-done** | Objective "remaining" measure (failing tests, open findings) | round k: lanes on remaining items → verify → recompute | unbounded unless capped | Infinite polishing; "handled enough" exits | remaining = 0 · no new findings 2 rounds · cap (S3 per class) · budget > 80% | per item |
| **Generate-and-filter** | Candidates cheap; filter reliable | K generators with different angles → dedupe → rubric filter | K × generation + filter | Filter picks the most confident, not the best | keep top-k by rubric after dedupe | generators `mission-worker`; filter `mission-reviewer` |
| **Best-of-N (code)** | Hard, high-variance change; strong test oracle; approaches genuinely differ | N = 2–3 makers, different approaches, separate worktrees | N × maker + verify | Candidates are the same approach twice; maker picks its own winner | tests first → verifier rubric → smallest diff | makers `mission-worker-high`/`mission-builder`; judge `mission-critic` |
| **Tournament** | Taste or approach choice; N ≤ 4; rubric exists | pairwise judge, both orders (A/B and B/A) | ~N log N judge calls | Position bias; vibes without rubric | most pairwise wins; order-dependent verdict → escalate | proposers `mission-builder`; judge `mission-critic` |
| **None: single writer** | Coupled change across shared files | 1 maker + parallel reader lenses | 1× + reviews | — | reviewer findings → maker, serially | per `review.md` |

### Deciding to swarm (SW1–SW6)

- **SW1 MUST** fill the go/no-go checklist (`templates/swarm-decision.md`) before dispatching more than 2 agents at
  once, and record the decision (pattern, surface, writer and reader counts, estimated token multiplier, GO/NO-GO with
  one-line reason) in STATUS → `## Swarm`. A GO that overrides a NO-GO trigger needs a D-entry.
- **SW2 MUST** select the pattern from the table above. No row fits → one agent.
- **SW3 MUST NOT** fan out writers when lanes would edit overlapping paths, share a schema, migration or lockfile,
  share mutable runtime state without per-lane instances, or when the work is S-size (≤ ~3 files or ≤ one agent-hour).
- **SW4 MUST** freeze cross-lane decisions in `.mission/CONTRACTS.md` (interfaces and schemas, naming, error model,
  auth flow, design tokens, voice guide, shared-path owners) with a D-entry before any parallel writing, and link it
  from every lane brief. A lane that needs a frozen decision changed stops and returns `BLOCKED(contract-change)`; the
  orchestrator decides, bumps the contract version with a D-entry, and re-briefs every lane that reads the section.
- **SW5 SHOULD** prefer parallel readers over parallel writers, and "N proposals → tournament → one writer" over "N
  writers" whenever success is taste-based.
- **SW6 MUST** stop adding agents when ≥2 lanes report the same root cause or the same failing check signature.
  Cancel the dependent lanes, then re-partition the failure space (known-good oracle, bisection, per-file or
  per-endpoint split) or collapse to one writer. Log it in STATUS → Stop-rule log.

### Surface and degradation (SW7–SW10)

- **SW7 MUST** pick the surface by scale: ≤5 lanes in a wave → parallel Agent-tool calls in one assistant turn;
  ≥10 homogeneous items, or per-item verification that must be structurally enforced → a dynamic workflow when the
  Workflow tool exists; reproducible, headless, CI or overnight → one `claude -p` process per lane
  (`scripts/run-wave.sh`). 6–9 heterogeneous lanes → two Agent-call turns, or a workflow.
- **SW8 MUST** degrade in this order: Workflow tool → parallel Agent calls → sequential Agent calls → `claude -p` per
  lane → one session running the same briefs sequentially. Briefs, return schema, owned paths and artifacts stay
  identical across surfaces; maker and verifier never share a context on any surface.
- **SW9 MUST NOT** depend on agent teams (experimental, not spawned in `-p` or SDK sessions, teammates not isolated in
  worktrees).
- **SW10 MUST** pre-allowlist the commands lanes need (test runner, package manager, build, `git` read and commit)
  in `.claude/settings.json` `permissions.allow` before an unattended workflow or headless wave; a non-allowlisted call
  can pause the run. Never allowlist the H1 actions (`orchestration.md` H2).

### Parallel safety (SW11–SW18)

- **SW11 MUST** give every parallel writer an isolated worktree (Agent-tool `isolation: worktree`, workflow
  `isolation: 'worktree'`, `claude -p --worktree <T-NNN>`, or `git worktree add`) and explicit `owns:` globs, and run
  `.mission/bin/check-ownership.sh .mission/lanes/W<k>.wave` before dispatch. Exit 1 → re-partition; never dispatch
  overlapping writers. New directories are listed literally (glob expansion cannot see files that do not exist yet).
  Each lane implicitly owns `.mission/lanes/<T-NNN>/**`. Readers need no worktree.
- **SW12 MUST** use deterministic names so a retry reuses them: branch `claude/<mission>/<T-NNN>-<slug>` created from
  the current integration tip (not from base), worktree `.claude/worktrees/<T-NNN>`, lane dir `.mission/lanes/<T-NNN>/`.
- **SW13 MUST** spawn isolated agents from the primary checkout only. Spawning `isolation: worktree` from inside a
  non-primary worktree can switch the parent worktree's branch (claude-code issue #47548).
- **SW14 MUST** give lanes that run services their own runtime: port = base + 10 × lane index, database or schema
  `<name>_<T-NNN>`, one simulator device id and derived-data path per lane, temp dir `.mission/tmp/<T-NNN>/`, and
  separate cache or build dirs where tools lock them. Worktrees isolate files, not runtime. Record the values in the
  lane contract and `CONTEXT.md` → Runtime isolation.
- **SW15 MUST** integrate through one integrator (`mission-integrator`): merge PASS lanes one at a time onto
  `claude/<mission>/integration` in DAG order, critical path first; after each merge rerun that lane's AC checks, the
  smoke suite, and the checks of earlier lanes whose owned paths this lane imports; red → revert that merge and return
  the lane as `FAILED(iter n)` with the failure log. Never patch forward blindly on the integration branch.
- **SW16 MUST** run a merged-result verifier on the integration branch after each wave and before anything reaches
  the default branch: full affected suite, contract tests, cross-lane behaviour no single lane could test, duplicated
  implementations across lanes. Lane PASS is necessary, not sufficient. FAIL → bisect over the wave's merge commits.
- **SW17 MUST** keep the conflict resolver separate from every maker: the integrator resolves with both lane briefs,
  both diffs and `CONTRACTS.md`, and reruns both lanes' AC checks. Cannot keep both green → `git merge --abort`, return
  the later lane `BLOCKED(conflict)` with the conflicting hunks saved to `.mission/lanes/<T-NNN>/conflict.diff`.
- **SW18 MUST** clean up after integration: copy lane logs needed as evidence into `.mission/logs/`, then per lane
  `git worktree unlock .claude/worktrees/<T-NNN>` (headless `-p` runs leave a lock), `git worktree remove
  .claude/worktrees/<T-NNN>`, `git branch -d claude/<mission>/<T-NNN>-<slug>` (merged only; never force), then
  `git worktree prune` and `git worktree list`. Anything left → STATUS → `## Swarm` → Cleanup debt. Mission-end gate:
  `git worktree list` shows only the primary checkout (plus named keep-worktrees with a D-entry).

### Briefs, returns, checkpoints (SW19–SW24)

- **SW19 MUST** brief every lane with `templates/brief.md` plus the `templates/lane-contract.md` block: lane id, owns,
  reads, needs, runtime isolation, siblings for awareness, checkpoint and resume rules, time box, stall contract,
  return schema. Verifier lanes use `templates/gate-verifier.md` instead (never the maker's brief or return).
- **SW20 MUST** require the lane's final message to be only the JSON return object (≤400 words, schema in the lane
  contract) pointing at artifacts on disk, also committed at `.mission/lanes/<T-NNN>/return.json` on the lane branch.
  Validate deterministically before any model reads it (Procedure P5); an invalid return counts as `STALLED`.
- **SW21 MUST** make lanes checkpoint incrementally: append `<UTC time> · step · result · next` to
  `.mission/lanes/<T-NNN>/progress.md` after every major step and commit at least every 3 steps. At start a lane reads
  `progress.md`; if it exists, it resumes from the last `next` instead of restarting (idempotent resume).
- **SW22 MUST** apply the stall rule: no new checkpoint within the time box, the same error signature twice, or a
  missing or invalid return → cancel the lane (`x` in `/workflows`, TaskStop or `/tasks`, SIGTERM via `timeout` for
  `-p`, exit 143, resumable). Retry **once** with a narrower brief (split scope or add the missing context), reusing
  branch and progress; then tier up one rung on the ladder in a fresh context; then mark `STALLED` and add it to the
  human queue.
- **SW23 MUST NOT** ask any lane (including report-writing research lanes) to produce a large artifact in one tool
  call; large outputs are written section by section (SKILL.md non-negotiable 14).
- **SW24 SHOULD** cap lane context by design: point, never paste; exploration through `Explore`/`mission-scout` or
  narrow greps; a lane that needs > ~60% of its context stops and returns `STALLED` (`stalled_reason: context`) with
  `proposed_split`.

### Scheduling and budget (SW25–SW30)

- **SW25 MUST** express lanes as a DAG (`needs:` in PLAN.md) and dispatch waves of READY lanes with disjoint
  ownership. The critical path (longest chain) gets the strongest suitable agent and is monitored and merged first.
- **SW26 MUST** respect caps: writers per wave S ≤2 · M ≤4 · L ≤8 · XL ≤12; read-only lanes ≤16 inside a workflow
  (outside a workflow, readers follow the class reader column below). Nothing exceeds the runtime ceilings: 16
  concurrent agents (fewer on low-core machines), 1,000 agents per workflow run.
- **SW27 MUST** split a lane whose estimate exceeds one fresh context or ~15 owned files, at contract boundaries
  only.
- **SW28 MUST** carry a token or cost estimate per wave in STATUS → `## Swarm` and a spawn row per lane in BUDGET.md.
  Headless lanes record `total_cost_usd` from `--output-format json`. When the mission budget is > 80% spent, dispatch
  no new wave: finish or cancel running lanes, then re-plan with a D-entry.
- **SW29 MAY** run lanes as a CI matrix (one `claude -p` job per lane, same wave file and briefs as `run-wave.sh`,
  each job pushing only its lane branch and uploading `.mission/lanes/<T-NNN>/`) when CI exists and lanes are
  independent; a final job or the orchestrator runs the integrator. Never `--bare` (`orchestration.md` L6).
- **SW30 MAY** reuse packaged fan-out: save a successful workflow as a command (`s` in `/workflows`) and cite it in
  the project skill; use `/batch` for mechanical writer fan-out where each change can be its own PR; use
  `/deep-research` for research fan-out when installed. Their outputs still go through per-item verification and
  the merged-result verifier.

## Procedure

### P1 Decide (Phase 4 Plan, per wave)

1. List the candidate units from PLAN.md READY tasks (or discovered items). Classify each lane writer or reader.
2. Pick the pattern (table above). No row fits, or a no-swarm default applies → single writer; skip to P6 for the
   one lane.
3. Copy the checklist from `templates/swarm-decision.md` into STATUS → `## Swarm`, tick with evidence, compute the
   estimate (lanes × per-lane estimate × 1.3) against the wave budget, state GO or NO-GO with one line.
4. Choose the surface (SW7) and state the degradation path (SW8).

### P2 Partition and freeze (Phase 3 end / Phase 4)

1. Freeze cross-lane decisions: fill `.mission/CONTRACTS.md` from `templates/CONTRACTS.md`, including the shared-path
   owner table (routes, registries, lockfiles, schema, tokens → one owner each). D-entry; the Design gate verifier
   checks it.
2. Write owned globs per lane into `PLAN.md`, then the wave file `.mission/lanes/W<k>.wave`. List new directories
   literally (`apps/api/src/outfits/**`, not `apps/api/src/*/**`).
3. Run `.mission/bin/check-ownership.sh .mission/lanes/W<k>.wave > .mission/logs/ownership-W<k>.txt`. Exit 1 →
   re-partition (move the shared file to a spine lane or to the contract) and rerun. Cite the exit 0 in PLAN.md Waves.
4. Assign runtime isolation per lane (SW14) and add allowlist entries (SW10).

### P3 Brief (per lane)

1. Fill `templates/brief.md`, append the block from `templates/lane-contract.md`, save to
   `.mission/lanes/<T-NNN>/brief.md` and commit on the integration branch so every worktree sees it.
2. Name the siblings in the wave (one line each) for awareness only; lanes never coordinate or edit sibling paths.
3. Create the integration branch once from the primary checkout (`git branch claude/<mission>/integration <base>`),
   and record `base: <sha>` in STATUS → `## Swarm`.

### P4 Dispatch (from the primary checkout only)

| Surface | How |
|---|---|
| Agent tool (≤5 lanes) | Write STATUS first. One assistant turn with one Agent call per lane: roster agent from PLAN.md, `model` override only to pin a full ID, `isolation: worktree` for writers, prompt = the lane brief file content |
| Dynamic workflow (≥10 homogeneous items) | Ask Claude Code for a workflow in plain words and hand it the shape: discover (1 reader returns item list with literal owned paths) → per-item pipeline (maker in `isolation: 'worktree'` → fresh verifier with artifact + checks only → at most one narrowed retry) → barrier only for dedup/synthesis → report PASS/failed ids. Integration is never inside the workflow. Let the runtime author the script; do not hand-maintain API names |
| Headless (`claude -p`) | Pre-create each lane worktree from the primary checkout so the branch starts at the integration tip: `git worktree add .claude/worktrees/<T-NNN> -b claude/<mission>/<T-NNN>-<slug> claude/<mission>/integration`. Then `.mission/bin/run-wave.sh --wave .mission/lanes/W<k>.wave --parallel <cap> --timeout-min <box> [--max-budget-usd <per-lane cap>]`; first run with `--dry-run` and save the printed commands to `.mission/logs/` |
| Sequential (degraded) | Same briefs, one lane at a time, same return validation |

### P5 Babysit and accept returns (deterministic first)

1. Poll with scripts, not a model: checkpoint mtime of `progress.md` in the lane worktree, exit codes and
   `result.json` from `run-wave.sh`, `git worktree list`, `/workflows` status. Apply SW22 on a stall.
2. Validate each return before reading it: parses as JSON against the lane-contract schema; `status: DONE` implies
   every check `PASS` with non-empty evidence and empty `outside_ownership`; `commit` exists on the lane branch;
   `git diff --name-only <integration-tip>...claude/<mission>/<T-NNN>-<slug>` ⊆ owned globs plus
   `.mission/lanes/<T-NNN>/**`. Any failure → treat as `STALLED`.
3. `BLOCKED(contract-change)` → decide per SW4 (keep the contract and re-brief, or amend with a D-entry and re-brief
   all readers). `STALLED` with `proposed_split` → re-plan the lane into its proposed parts (SW27). Same signature
   from ≥2 lanes → SW6.
4. Merge `memory_delta` blocks into STATE by ID; write STATUS board rows and BUDGET spawn rows.

### P6 Verify per lane

Dispatch a fresh verifier (`templates/gate-verifier.md`) with the lane branch, AC ids with commands, the rubric and
`CONTRACTS.md` only. It checks out a detached worktree (`git worktree add --detach .claude/worktrees/verify-<T-NNN>
claude/<mission>/<T-NNN>-<slug>`), reruns every check, runs `scripts/test-diff-grep.sh`, checks ownership, then
removes the worktree. Only PASS lanes enter the merge queue. FAIL → maker retry with the verifier report (S6 ladder).

### P7 Integrate serially

`mission-integrator` per SW15/SW17: switch to `claude/<mission>/integration`, `git merge --no-ff
claude/<mission>/<T-NNN>-<slug> -m "integrate <T-NNN>"`, run checks, keep or revert, record
`<T-NNN> merged @ <sha> · checks PASS` in STATUS. The integrator never pushes to the default branch.

### P8 Merged-result verification, cleanup, learning

1. After the wave: merged-result verifier (SW16) on the integration tip. FAIL → bisect merge commits, return the lane.
2. Cleanup (SW18); record Cleanup debt.
3. Record per wave in STATUS → `## Swarm`: lanes dispatched, first-try PASS count, integration reverts, stalls,
   tokens or USD. Two waves in a row with ≥2 reverts → halve the next wave's writer count and re-partition. Failure
   patterns → `LESSONS-INBOX.md`.

## Scale by class (S/M/L/XL)

| | S | M | L | XL |
|---|---|---|---|---|
| Swarm shape | No swarm: 1 maker + 1 fresh verifier | Research fan-out 2–4 → 1–2 makers → per-maker verifier → merged verifier | DAG waves; contracts frozen first; per-lane maker → verifier pipeline | Phased DAG per milestone; workflows for homogeneous sweeps; headless lanes overnight |
| Writers per wave | ≤2 (normally 1) | ≤4 | ≤8 | ≤12 |
| Readers per wave | ≤2 | ≤4 | ≤8 | ≤16 (inside a workflow) |
| Surface | Agent tool | parallel Agent calls | Agent calls or workflow | workflow + `claude -p` scripts / CI matrix |
| Go/no-go | skip (SW1 only fires above 2 agents) | checklist in STATUS | checklist + `mission-strategist` plan | checklist + `mission-strategist` plan, per milestone |
| CONTRACTS.md | none | only if ≥2 writers share an interface | required before parallel writing | required per milestone + contract-test lane |
| Ownership check | skip | script per wave | script per wave | script per wave, PLAN lint row 5 |
| Integration | direct on task branch | serial onto integration branch | `mission-integrator`; merged verifier each wave | integration branch per milestone; XL release adds `mission-strategist-review` lens |
| Verifier sampling | — | — | 1 in 10 PASS verdicts audited by `mission-critic` | as L |
| Ceremony cut | no swarm board, no wave file | swarm section ≤15 lines | full | full |

If unsure between two classes, take the larger cap for verification strength and the smaller for ceremony
(conventions §5).

## Shape conditionals

Shape codes: `shapes-and-scope.md` §6. Every IF below still passes SW1 and the class caps.

**GRN greenfield multi-platform (e.g. SwiftUI iOS + Cloudflare backend)**
- IF ≥2 surfaces talk to each other THEN M0 = frozen contract in `CONTRACTS.md` (schema file, error model, auth flow)
  before any fan-out, and ONE stub lane generates client and server stubs from the schema and merges first.
- IF the contract is frozen and the stub lane merged THEN run backend and iOS maker lanes in parallel worktrees with
  disjoint ownership (`services/api/**` vs `apps/ios/**`) plus a contract-test lane owning `tests/contract/**`;
  both sides' verifiers use the contract tests as evidence.
- IF lanes run simulators or dev servers THEN one simulator device id and derived-data path per lane, one port range
  and one database per lane (SW14); never share a simulator.
- IF design quality matters THEN 2–3 design proposals (tokens + one hero and one dense screen each) → position-swapped
  tournament (`frontend-verification.md`) → winning tokens freeze in `CONTRACTS.md` → one writer per screen group. No
  parallel UI writers on the same screens.

**BUG deep bug hunt**
- IF not yet `REPRODUCED` THEN no lanes: one repro builder (`debugging.md`).
- IF `REPRODUCED` and ≥3 independent open hypotheses THEN 3–5 experiment lanes (DBG-40..42 caps and return schema),
  each one H-id, own worktree and own runtime instance; lanes return SUPPORTED/FALSIFIED with raw output.
- IF ≥2 lanes converge on the same cause THEN cancel the rest (SW6) and run the confirmer.
- IF the cause is CONFIRMED THEN collapse to one writer for the fix plus a fresh verifier. Parallel fixes only as
  best-of-2 with genuinely different approaches, judged by the repro test.
- IF the bug is a flake or race THEN per-lane ports and databases are mandatory, or the lanes create the races they
  study.

**FEA feature in an existing product (e.g. dashboard)**
- IF conventions are unfamiliar THEN one codebase reader lane (`mission-worker`) runs first and drafts a conventions
  digest at `.mission/lanes/<T-NNN>/conventions.md`; the orchestrator adopts it into `.mission/CONTEXT.md` (owner:
  orchestrator), which every maker brief links.
- IF the feature touches shared layout, routing, state stores or registries THEN one spine lane owns those files and
  merges first; widget lanes start only after it is integrated.
- IF widgets own their component dirs and queries THEN ≤4 widget lanes with a per-widget verifier, then a merged-result
  verifier with visual checks (`frontend-verification.md`).

**MIG migration or extraction (e.g. AI gateway into a core platform service)**
- IF a shared interface changes THEN the interface change + compatibility shim land serially first, by one writer.
- IF many similar call sites or modules THEN pipeline: discover (1 reader lists modules with literal owned paths) →
  per-module migrate (isolated worktree) → per-module verify → barrier → serial integration. `/batch` MAY replace the
  migrate stage when each module can be its own PR (SW30).
- IF an old/new behaviour oracle exists (legacy path still running) THEN differential tests are the verifier oracle
  and failures are partitioned by endpoint or module before any new lanes (the known-good-oracle move).
- IF a data or schema migration is involved THEN exactly one migration writer; no parallel lanes against the same
  database (DAT shape: no swarm).

**WEB research + marketing website with blog/docs**
- IF market research is needed THEN 3–6 research angle lanes (competitors, pricing, positioning, audience, SEO) each
  returning claims with URLs → one synthesizer → a skeptic verifier checking the top claims against sources
  (`research.md`; `/deep-research` MAY run the fan-out).
- IF pages are built THEN one spine lane owns the site shell, theme and routing and merges first; content lanes per
  section (about, blog posts, docs pages) write against a frozen voice guide and IA in `CONTRACTS.md`.
- IF naming, taglines or hero concepts are needed THEN generate-and-filter (≥10 candidates from ≥3 angles) →
  tournament of the top 4 → human pick where the brand is externally visible.

**Other shapes**
- IF SEC or audit (security, a11y, dead code) THEN fan-out reader lanes per directory or lens + adversarial
  verification per finding; fixes are a later single-writer (or `/batch`) phase.
- IF a flaky-test backlog or many independent failing tests THEN parallel writers pay best: one lane per failing test
  cluster, each claiming its cluster with a committed lock file `.mission/lanes/<T-NNN>/claim.lock` on the integration
  branch before starting; a second claimer picks another cluster.
- IF docs or API reference sync THEN mechanical makers with an oracle (build, link check) and a 10% sampled verifier.
- IF REF refactor with ≥10 homogeneous units THEN workflow per-unit pipeline after a serial pilot unit.
- IF PRF performance THEN experiment lanes with own worktree and own runtime, the best measured one merges.
- IF INF infra/CI or DAT data migration THEN no swarm: single writer, human checkpoint (`orchestration.md` H1).

## Model routing

Lane cost × lane count dominates a swarm's bill, so the lane agent matters more than the orchestrator model. Full
matrix and profiles: `models-and-cost.md`.

| Role | Agent | Tier-up when | Guard on the cheaper choice |
|---|---|---|---|
| Swarm planner (go/no-go, pattern, DAG, partition, contracts) | S/M: orchestrator inline · L/XL: `mission-strategist` | M plan fails integration twice → `mission-strategist` | `check-ownership.sh` exit 0; `mission-checker` plan lint; integration revert rate per wave in STATUS |
| Maker lane (bounded owned paths, executable checks) | `mission-worker`; risky areas start at `mission-builder` | one narrowed retry fails → next rung of the ladder (`mission-worker-high` → `mission-builder`) | lane checks green on the lane branch; per-lane verifier PASS; checks rerun after merge |
| Mechanical maker (codemod, rename, lint fix, doc sync) | `mission-worker` (needs write; no lower write-capable Sonnet agent exists) | oracle red twice → `mission-worker-high` | compiler/linter/test oracle green; 10% random sample verified by `mission-verifier` |
| Reader lane (web or codebase) | single lookups `mission-scout`; angle research `mission-worker` | contradictory sources → `mission-worker-high` | URL or file:line per claim; synthesizer drops unpointed claims |
| Per-item verifier | `mission-verifier` with a lens different from the maker (tests-first, spec-first, contract-first) | security, concurrency, data migration, or maker was `mission-builder` → `mission-critic` | FAIL cites a failing command or file:line, PASS cites command output; L/XL: `mission-critic` audits 1 in 10 PASS verdicts |
| Merged-result verifier | `mission-critic` | XL release → + `mission-strategist-review` lens | full affected suite + contract tests on the integration tip; FAIL blocks landing |
| Integrator / conflict resolver | `mission-integrator` | semantic conflict in a risky area or in `CONTRACTS.md` paths → `mission-builder` (a non-maker instance) | both lanes' AC checks rerun; resolver never a maker of either lane |
| Classifier / router | `mission-checker` (fixed enum output) | low confidence or risky label → higher route / `mission-reviewer` | 5% of items double-classified by a second `mission-checker` instance; disagreements take the higher route |
| Tournament judge | `mission-critic`; low-stakes internal choices MAY use `mission-reviewer` | brand or flagship design → human pick from finalists | rubric required; both orders judged; order-dependent verdict escalates |
| Generate-and-filter filter | `mission-reviewer` | — | rubric scores logged per candidate; dedupe first |
| Synthesizer (map-reduce reduce) | `mission-builder`; XL market or strategy synthesis `mission-strategist` | — | every synthesized claim traces to a lane artifact; `mission-verifier` diffs synthesis claims against lane returns |
| Babysitter (stall detection, retry, cleanup) | script, no model (`run-wave.sh`, checkpoint mtime, `git worktree list`) | narrower brief rewrite by the orchestrator | exit codes and mtimes, never narration |

- **SWM1 MUST NOT** run lanes on `mission-strategist` or `mission-strategist-review` by default. Fable 5.1 plans the
  swarm and lends one XL release lens; it never supplies fan-out volume.
- **SWM2 MUST** give maker and verifier different models or different lenses. Same model and same lens is allowed only
  when the verifier's context is fresh and it holds the executable checks.
- **SWM3 MUST** pick model·effort by roster agent file, because the Agent tool overrides `model` per call but not
  effort (conventions §6). Inside a workflow, reference the same roster agents or pin full model IDs; never aliases.
- **SWM4 SHOULD** escalate the model, not the effort, when a role needs more than Sonnet 4.6 high (no xhigh).

## Anti-patterns

| Anti-pattern | Symptom | Guard |
|---|---|---|
| Swarm by default | More tokens on briefs and returns than on work; S tasks fanned out | SW1, SW3; S class has no swarm |
| Parallel writers on coupled code | Two lanes edit a router, schema or lockfile; duplicated helpers; divergent styles | `check-ownership.sh`, spine lane first, SW4 contracts |
| Same-bug stampede | Every lane fails on one root cause and overwrites the others' fixes | SW6 re-partition with an oracle or bisection |
| Implicit decisions left open | Each lane invents its own error format, naming or spacing | `CONTRACTS.md` before fan-out; verifier checks conformance |
| Phase worktrees as independent worlds | Dependent phases run isolated; a failed phase silently poisons later ones | phases are checkpoints on one integration line |
| Depending on agent teams | Plan breaks in `-p`, teammates collide in one checkout | SW9 |
| Lane-green ≠ merge-green | "All lanes passed" declared done | SW16 merged-result verifier |
| Maker-flavoured verifier | Verifier brief carries the maker's summary; a maker resolves its own conflicts | SW17, SW19 (`gate-verifier.md`) |
| Trusting workflow completion | "Every stage ran" read as "every stage was right" | workflow output is input to verification, never a verdict |
| Synthesizer hallucination | Connective claims no lane found | claim → lane artifact trace; `mission-verifier` diff |
| Tournament without rubric or order swap | First candidate wins | rubric + both orders |
| Giant single-shot outputs | Lane composes its whole file in one call, stalls, loses everything | SW21, SW23 |
| Non-idempotent retries | Retry makes a new branch and worktree; duplicated work, orphan branches | SW12 names, SW21 resume |
| Silent stalls | Lane waits on a permission prompt; `-p` drops partial results at the idle ceiling | SW10 allowlist, time box, mtime babysitter |
| Worktree litter | Locked `-p` worktrees and merged branches pile up | SW18 cleanup gate |
| Nested-worktree spawning | Parent worktree's branch switches under the orchestrator | SW13 |
| Shared runtime collisions | All lanes bind one port, DB or simulator | SW14 |
| Env drift in fresh worktrees | Missing `.env` or dependencies; makers "fix" code that is not broken | `.worktreeinclude`, setup step in the brief, `BLOCKED(env)`, verifier UNVERIFIED |
| Stale base | Wave k branches from base and re-implements wave k−1 | branch from the integration tip (SW12) |
| Fable fan-out | Budget gone in one wave | SWM1 |
| Max-depth verifier on mechanical work | Opus verifier per codemod item where a compiler oracle suffices | oracle + 10% sample |
| Transcript ingestion | Orchestrator reads lane transcripts instead of returns | SW20 JSON ≤400 words; artifacts on disk |
| Ceremony for small jobs | Swarm board, wave file and merge protocol for a 2-file fix | Scale by class: S skips all of it |

## Unverified harness details

| Detail | What is known | Safe fallback |
|---|---|---|
| Workflow script API (`agent`, `parallel`, `pipeline`, `phase`, `log`, `schema`, `isolation`, per-call `model`/`effort`) | Workflows are JS scripts run by the Workflow tool (docs); function and option names come from practitioner write-ups | Describe the intent and shape; let Claude Code author the script; check `/workflows` output |
| Workflow agents run in `acceptEdits` and inherit the allowlist; failed agents resolve to null | secondary sources | SW10 pre-allowlist; treat null as `STALLED` |
| Agent-tool per-call `isolation`; roster agent files do not set `isolation` | `isolation` is a documented subagent field; per-call support, cleanup rules and created branch names unverified | Brief requires commit before return on the named branch; if isolation is unavailable, create `git worktree add` from the primary checkout and pass the path, or use `run-wave.sh` |
| Several Agent calls in one turn run concurrently | inference from practice | Correct either way; only wall-clock changes |
| Subagent nesting | sources conflict | Orchestrator (or workflow script) owns all spawning; lanes never spawn agents |
| `claude -p --worktree <name>` creates `.claude/worktrees/<name>/` and never cleans up, leaving a lock | worktrees docs | SW18 unlock + remove; `run-wave.sh` prints the cleanup commands |
| `--max-budget-usd` | version-dependent (`models-and-cost.md`) | pass only when given and listed by `claude --help`; else enforce from BUDGET.md |
| `--agent <name>` for headless lanes | unverified | `run-wave.sh` does not use it: brief text + `--model <full id>` |
| `-p` with background agents keeps running only to a 10-minute idle ceiling | headless docs | lanes never start background agents in `-p`; one process per lane |
| Runtime ceilings 16 concurrent (fewer on low-core machines), 1,000 per run | cookbook | caps above stay far below |
| `/batch` (5–30 worktree agents, PR each) and `/deep-research` | `/batch` on the agents docs page; `/deep-research` not verified | use when listed in the session's slash commands; else Agent-call fan-out |
| Token multipliers ≈4× agent, ≈15× multi-agent | 2025 research workloads | measure `total_cost_usd` and `/workflows` totals per wave (P8) |
| Class caps S2/M4/L8/XL12 | judgement, not benchmark | log revert and stall rates per wave; tune via lessons |
| Cognition 2026 "writes stay single-threaded" | secondary summary only | treat as reported; the Carlini evidence carries the rule |

## Evidence

1. https://www.anthropic.com/engineering/multi-agent-research-system (≈15× tokens, 80% variance, over-spawning, briefs)
2. https://cognition.ai/blog/dont-build-multi-agents (implicit decisions, Flappy Bird example)
3. https://www.anthropic.com/engineering/building-c-compiler (16 agents, same-bug collision, GCC oracle, lock files)
4. https://www.anthropic.com/engineering/building-effective-agents (workflow patterns, simplest solution first)
5. https://code.claude.com/docs/en/workflows (dynamic workflows, `/workflows`)
6. https://platform.claude.com/cookbook/claude-agent-sdk-08-dynamic-workflows (16 concurrent, 1,000 per run)
7. https://code.claude.com/docs/en/worktrees (`--worktree`, isolation enforcement, `-p` leaves locks)
8. https://code.claude.com/docs/en/headless (`-p`, `--output-format json`, `total_cost_usd`, idle ceiling, `--bare`)
9. https://code.claude.com/docs/en/agent-teams (experimental, no worktree isolation, not in `-p`)
10. https://github.com/anthropics/claude-code/issues/47548 (nested worktree spawn switches parent branch)
11. https://gu-log.vercel.app/en/posts/en-sp-181-20260423-walden-cognition-multi-agents-working (secondary)
12. `research/mission-skill/09-swarms-workflows-parallelism.md` (lane report: claim check, rules, open questions)
