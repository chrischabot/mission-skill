# Memory and lessons: STATE, STATUS, failure conversion, compounding into the skill

Mission memory compounds only when three things hold: writes are **gated by evidence**, reads are **forced by the
harness**, and the store is **pruned** so loading it stays cheap. This file ships those as templates, hooks, a lint
script and a curator pass. Names (paths, IDs, states, roster agents) come from `references/conventions.md`, which wins.

Honesty notes the orchestrator must not overstate: the fail → investigate → verify → distill → consult progression is
Lance Martin's framing for one SQL task, used here as a *lesson lifecycle schema*, not a benchmark finding. The
benchmark it ran on (CL-Bench) is Berkeley Sky lab's, not Anthropic's, and its authors found that "naive ICL
outperforms systems dedicated to memory management". So: plain files loaded into context, no vector DB or memory
service by default.

## When to load

| Situation | Load this file? |
|---|---|
| Intake of an M/L/XL mission (scaffold `.mission/`, install hooks) | Yes: §Core rules 1–2, §Procedure P0 |
| Resuming a session without a SessionStart hook | Yes: P1 |
| Merging worker `memory_delta` blocks into STATE/STATUS | P5 |
| `scripts/memory-lint.sh` fails, a budget is exceeded, a milestone closes | P6 curator pass |
| A failure is resolved and needs conversion (after `references/debugging.md` proof of fix) | P7 |
| Phase 9 Retro, or `/mission retro` | P7–P8 (promotion) |
| S mission | Only §Scale by class, S row |

Skim `references/lessons.md` contents line at intake and consult matching lessons before planning.

## Core rules

Rule IDs: `MEM-` (project memory), `CMP-` (compounding into the skill). MUST/SHOULD/MAY per conventions §9.

### 1. One home per kind of fact

| Kind of fact | Home | Loaded when | Writer |
|---|---|---|---|
| Build/test commands, durable conventions for every session | `CLAUDE.md` (import `@AGENTS.md` if present) | Every session (harness) | Human; mission only *proposes* at retro |
| Phase, gates, board, budget summary, fallback events, human queue, stop log, done log | `.mission/STATUS.md` | SessionStart hook prints header + board top rows | Orchestrator only |
| Resume pointer, rules index, verified facts, hypotheses, rules, open failures | `.mission/STATE.md` | SessionStart hook prints Resume + Rules index | Orchestrator only |
| What "done" means | `.mission/acceptance.json` | On demand | Spec phase; only verifiers flip `passes` |
| Decisions incl. waivers, downgrades, scope cuts | `.mission/DECISIONS.md` (append-only, index at top) | On demand; index line in STATE | Orchestrator after a decision gate |
| External sources and findings | `.mission/RESEARCH.md`, `research/Q-NN.md` | On demand | Research workers via orchestrator |
| Long failure investigations | `.mission/investigations/O-NNN.md` | On demand, linked from STATE | Investigator (`templates/investigation.md`) |
| Candidate cross-project lessons | `.mission/LESSONS-INBOX.md` | Retro only | Orchestrator appends (from worker `lesson_candidates`) |
| Promoted cross-project lessons | skill `references/lessons.md` + skill `evals/evals.json` | When the skill loads the reference | Promotion pipeline only (P8) |
| Session hand-off narrative | `.mission/HANDOFF.md` (overwritten) | Session start, first read | Orchestrator |
| Superseded, expired, rolled-off entries | `.mission/archive/state-YYYY-MM.md`, `archive/status-YYYY-MM.md` | Never automatically | Curator pass |
| Scratch, stamps, large logs | `.mission/tmp/` (gitignored) | Never | Anyone |

- **MEM-01 MUST** keep each fact in exactly one home. STATUS says what is done; STATE says what is true. "T-007
  PASSED" belongs in STATUS; "the webhook race is real, verified by `scripts/repro.sh`" belongs in STATE. A fact in two
  files is a bug: point, don't copy.
- **MEM-02 MUST** give every STATE/DECISIONS/INBOX entry a stable ID (`F-`, `H-`, `R-`, `O-`, `D-`, `L-`; conventions
  §3), a date, and for facts and rules a confidence (`low` = 1 instance, `medium` = 2, `high` = ≥3 or
  verifier-reproduced). IDs are never renumbered or reused.
- **MEM-03 MUST NOT** store secrets, tokens or customer data in any memory file. Record the *name and location* of a
  secret, never its value. `memory-lint.sh` scans for common key patterns.
- **MEM-04 MUST NOT** copy CLAUDE.md/AGENTS.md content into STATE (paid twice per session, contradictions appear). The
  mission MAY propose a CLAUDE.md addition at retro only for a project-wide rule violated ≥2 times.
- **MEM-05 SHOULD NOT** rely on Claude Code auto memory or subagent `memory:` stores for mission facts: they live
  outside the repo by default and are not reviewable. Leave auto memory on; route durable facts to STATE.

### 2. Writes: ID-addressed deltas, one writer

- **MEM-10 MUST** let only the orchestrator write `STATE.md` and `STATUS.md`. Makers, verifiers and reviewers return a
  `memory_delta` block (`templates/memory-delta.md`) at the end of their return; the orchestrator merges it (P5).
- **MEM-11 MUST** apply edits as ID-addressed deltas: add, modify-by-ID, supersede-by-ID. **MUST NOT** ask any model to
  "rewrite / condense / clean up STATE.md" in one pass: whole-file regeneration causes brevity bias and context
  collapse. Consolidation is the curator pass (P6) with an information-loss verifier.
- **MEM-12 MUST** supersede instead of silently editing a verified fact: the new entry carries `Supersedes: F-NNN`,
  the old one moves to `archive/` with `Superseded-by`.
- **MEM-13 MUST** reject a worker delta whose `facts_add` item has no evidence; demote it to `hypotheses_add`.
- **MEM-14 MUST** re-run `scripts/memory-lint.sh` after every merge and fix violations before the next dispatch.
- **MEM-15 SHOULD** commit `.mission/` at every session end (`mission: s<N> memory update`) so git holds the audit trail.

### 3. Five-stage gates, enforced by template fields

The stage is carried by *which section an entry sits in* and *which fields it has*. `memory-lint.sh` fails closed on
missing fields, so Sonnet-class workers produce stage-3 evidence without being trusted to remember the protocol.

| Stage | Section in STATE | Required fields (lint-checked where marked ✔) | Rejected example |
|---|---|---|---|
| 1 Fail | `## Open failures` (`O-NNN`) | date, symptom, `Repro:` ✔, observed vs expected, blast radius | "tests flaky" |
| 2 Investigate | `## Hypotheses` (`H-NNN`) | claim, `for O-NNN`, `Check:` ✔ (a command whose output would falsify it) | a hypothesis under Verified facts |
| 3 Verify | `## Verified facts` (`F-NNN`) | `verified YYYY-MM-DD` ✔, `recheck-by`, `Evidence:` ✔ (command + salient output line, or artifact path + SHA), `Level:` ✔ (`local-run`·`ci`·`staging`·`production`·`doc-source`), `Scope:` | "Confirmed 2026-06-09" with no command |
| 4 Distill | `## General rules` (`R-NNN`) | imperative statement, `Applies when:` ✔, `Instances:` ✔ (≥1 F-id), `Counter-cases:` (or "none known"), conf by instance count | a rule from one observation with no scope |
| 5 Consult | `## Rules index` + every brief | relevant R-ids and L-ids named in each worker brief; workers return `rules_cited` | "remember to check prior notes" |

- **MEM-20 MUST** open an O-entry (symptom, repro, observed/expected) *before* trying fixes on any failure worth more
  than one retry. Deep investigations move to `investigations/O-NNN.md` (`references/debugging.md`); STATE keeps a
  two-line entry with the link.
- **MEM-21 MUST** keep falsified hypotheses (`H-NNN · FALSIFIED <date>` + evidence) until the parent failure closes, so
  no later session retries them.
- **MEM-22 MUST NOT** place any claim under `## Verified facts` without Evidence + Level + verified date. No evidence →
  Hypotheses. The per-task verifier SHOULD re-run the evidence command of any fact that gates a decision or a rule.
- **MEM-23 MUST** give a rule with one instance `conf: low`; raise to `medium` at 2 instances, `high` at ≥3 or once a
  verifier reproduced it.
- **MEM-24 MUST** name relevant rule and lesson IDs in every worker brief ("Consult R-004, L-003 before editing auth
  middleware"). A rule uncited across 5 sessions is a retirement candidate (P6 step 6).
- **MEM-25 MUST** record a conflict between new evidence and a verified fact as `O-NNN · CONTRADICTION · F-x says …;
  <new observation>` with `Resolve by:` naming both evidence commands, and resolve it by re-running both. The loser is
  superseded, never picked arbitrarily or edited in place.

### 4. Session protocol

- **MEM-30 MUST (start)** read, in order: `HANDOFF.md` → `STATUS.md` header, gates, board → `STATE.md` Resume, Rules
  index, Open failures → `git log --oneline -20` → run the smoke check (red → fix first). In Claude Code the
  SessionStart hook injects the STATE/STATUS parts; everywhere else this is step 1 of the orchestrator prompt.
- **MEM-31 MUST (during)** write STATUS before every dispatch wave and after every integration; merge deltas by ID.
- **MEM-32 MUST (before compaction, reset, hand-off, or at ~60% context)** rewrite `## Resume` so a fresh agent with
  no chat history can act: next concrete action as a runnable command with the expected result, branch/worktree +
  HEAD, the command that re-verifies the last change, what blocks progress, files to read first. Then write
  `HANDOFF.md` (`templates/HANDOFF.md`). Prefer a reset over repeated compaction on L/XL.
- **MEM-33 MUST (end)** write the session delta: STATUS board moves with evidence, gate results, budget summary;
  STATE facts/hypotheses/rules/failures deltas; inbox appends; one `## Last session` line; run `memory-lint.sh`;
  commit `.mission/`. The Stop hook checks freshness when enforcement is on.
- **MEM-34 SHOULD** keep the resume pointer runnable: "Next: `pnpm test apps/api/auth --run`; expect 3 failures in
  rate-limit order" beats "continue auth work".

### 5. Hygiene budgets, expiry, contradictions

| Artifact | Budget | Over budget → |
|---|---|---|
| `STATE.md` | ≤150 lines (≈12 KB) | curator pass P6 |
| `STATUS.md` | ≤100 lines; Done log keeps 10 lines | roll to `archive/status-YYYY-MM.md` |
| `STATE.md ## Last session` | 5 lines, newest first | roll to `archive/state-YYYY-MM.md` |
| `LESSONS-INBOX.md` | ≤30 open entries (`candidate`/`verifying`) | triage at P6 step 9 before appending more |
| `DECISIONS.md` | unbounded body; index at top ≤25 lines | older index lines → `archive/` pointer |
| skill `references/lessons.md` | ≤40 entries and ≤300 lines, with Contents | merge or retire before promoting (CMP criterion g) |
| SessionStart hook output | ≤ ~3k tokens (default 12,000 chars) | `session-start.sh` truncates; everything else linked by path |
| Any single STATE entry body | ≤4 lines | detail → `investigations/<id>.md` |

- **MEM-40 MUST** enforce the budgets with `scripts/memory-lint.sh` (exit 1 on violation) and run the curator pass when
  a budget is exceeded, at each milestone close, and at mission end.
- **MEM-41 MUST** give every fact about volatile things a `recheck-by` date: 90 days by default, 30 days for toolchain
  facts (Xcode, simulators, wrangler, SDK versions), 14 days for production/infra state, decommission date for facts
  about a system being migrated away. An expired fact is treated as a hypothesis until re-verified; the hook prints
  `EXPIRED F-NNN`.
- **MEM-42 MUST** run the curator pass when ≥3 CONTRADICTION entries are open.
- **MEM-43 SHOULD** keep static text first and dynamic text last in what gets loaded (cache-friendly; an inference,
  not measured). The thresholds above are judgment calls modelled on Claude Code's own 200-line / 25 KB auto-memory
  load cap; projects MAY override them in `.mission/config` (`state_max_lines=`, `status_max_lines=`,
  `inbox_max_open=`, `session_budget_chars=`).

### 6. Compounding into the skill

- **CMP-01 MUST** separate project memory (STATE) from procedural cross-project memory (the skill). Test: "would this
  help on a different repository?" No → it stays an R-entry in STATE.
- **CMP-02 MUST** append lesson candidates to `.mission/LESSONS-INBOX.md` during work (`templates/LESSONS-INBOX.md`).
  **MUST NOT** edit the skill (SKILL.md, references, agents, scripts, `references/lessons.md`) mid-mission. Promotions
  are batched at retro (mission end, milestone retro on L, weekly on XL).
- **CMP-03 MUST** draft a candidate only from an *investigated* failure with verified root cause (conversion output D5
  in `references/debugging.md`) or a costly process failure. **MUST NOT** promote from "a test newly passes": there is
  no causal link to the skill.
- **CMP-04 MUST** prefer controls to prose: a candidate that could be a lint, hook, type or schema constraint says why
  it is not one. The subject of a lesson is a missing mechanism, never "be more careful".
- **CMP-05 MUST** promote only when *all* criteria hold, each cited by the promotion verifier:

| # | Criterion | Check |
|---|---|---|
| a | Root cause verified | `Evidence:` has a command/test that fails before and passes after, or links a stage-3 F-id |
| b | Recurrence or cost | seen in ≥2 independent missions/projects, OR 1 incident costing ≥1 day or a production defect |
| c | General and scoped | no project names in the rule; `Applies when` and `Does not apply when` present |
| d | Testable | an eval case exists in skill `evals/evals.json`; with-skill run satisfies its assertions and baseline does not, or the verifier records why the lesson is `advisory` |
| e | Independent approval | `mission-verifier` in a fresh context approves; it sees lesson + evidence + current lessons.md only, never the distiller's reasoning |
| f | Non-duplicative | no existing lesson says the same; a contradiction names what it supersedes |
| g | Budget | lessons.md stays ≤40 entries / ≤300 lines after merge; otherwise merge or retire first |
| h | Right target | SKILL.md body or a procedural reference edited **only when the skill steered a run wrong** (a wrong command, a missing step, a rule that caused the failure); everything else goes to `references/lessons.md` |

- **CMP-06 MUST** follow the `/verify` rule for procedural skill files: Anthropic's bundled `/verify` skill used to fold
  in everything a run learned, which caused frequent merge conflicts; it now edits its recipe "only when it steered a
  run wrong". Copy that trigger.
- **CMP-07 MUST** ship every non-advisory promoted lesson with an eval case in skill-creator format
  (`{skill_name, evals:[{id, prompt, expected_output, files, assertions}]}`), run with-skill and baseline in the same
  turn. A lesson that cannot be expressed as a test stays `advisory`.
- **CMP-08 MUST** retire a lesson whose eval passes on baseline without the skill (dead weight) or uncited for 6
  months; retirements go to skill `references/lessons-archive.md` with the reason.
- **CMP-09 MUST** vendor the skill for cloud runs: personal skills under `~/.claude/skills/` load in "all your projects
  on this machine, but not Cowork or cloud sessions". For Routines/CMA, commit the skill to the repo's
  `.claude/skills/mission/` (or a plugin) and sync `references/lessons.md` + `evals/evals.json` through a PR.
- **CMP-10 SHOULD** mark a candidate rejected twice by the promotion verifier `rejected(<criterion>)`; a stale candidate
  (older than 60 days, count 1, cost <1 day) becomes `rejected(stale)`.

### 7. Graceful degradation by storage backend

| Environment | Store | Read forcing | Write checking |
|---|---|---|---|
| Claude Code with hooks | `.mission/` files | SessionStart `startup\|resume\|compact` → `session-start.sh` | Stop → `stop-check.sh` (opt-in `enforce_stop=1`), lint at session end |
| Claude Code without hooks (or hooks disallowed) | `.mission/` files | orchestrator prompt starts "Read `.mission/HANDOFF.md`, STATUS header + board, STATE Resume + Rules index" | session-end checklist is the last prompt step; final verifier checks `Last session` freshness |
| Claude Managed Agents | memory store: split STATE into small files (`state/resume.md`, `state/rules.md`, `state/facts.md`, `state/failures.md`), each <100 kB | session `instructions` (≤4,096 chars) say "read state/resume.md and state/rules.md first" | orchestrator mounted `read_write`; workers `read_only`, they still return `memory_delta` |
| API memory tool (`memory_20250818`) | `/memories/mission/` with the same file names | Claude checks its memory directory before starting; still put "read STATE Resume first" in the system prompt | the harness runs `memory-lint.sh` over the exported files at the end |
| Routines / headless `claude -p` | vendored skill + `.mission/` in the repo | `templates/continue-prompt.md` step 1 | `enforce_stop=1`; digest (STATUS header + new Open failures) written before exit |

- **MEM-50 MUST** use SessionStart with the `compact` matcher to re-inject after compaction, not PostCompact (its
  output does not reach the conversation).
- **MEM-51 MUST** keep the Stop check quick, specific and loop-safe: respect `stop_hook_active`, block with a reason
  that is the next instruction, and record `tmp/memory-debt` instead of blocking twice. Claude Code force-ends a turn
  after 8 consecutive Stop blocks.
- **MEM-52 SHOULD** keep Stop enforcement off in interactive missions (Stop fires at every turn end) and on for
  unattended/headless runs.

## Procedure

### P0 Scaffold (Intake, M/L/XL)

1. `scripts/init-mission.sh --class <M|L|XL>` copies `STATUS.md`, `STATE.md`, `DECISIONS.md`, `LESSONS-INBOX.md`
   into `.mission/` and writes `.mission/config`. `templates/memory-delta.md` stays in the skill; every brief pastes its
   skeleton. Add `.mission/tmp/` to `.gitignore`.
2. Init also copies `session-start.sh`, `stop-check.sh`, `memory-lint.sh` and the frozen-path guard `protect-frozen.sh`
   (`references/testing.md`) into `.mission/bin/`, so hooks work in cloud runs where the personal skill is absent.
   Confirm they exist and are executable.
3. Merge `templates/settings.hooks.json` into `.claude/settings.json` (committed). Never overwrite existing hooks:
   append entries to the matching event arrays.
4. Check `.mission/config` (`key=value`, one per line): `class=<M|L|XL>`, `enforce_stop=<0|1>` (1 for unattended),
   optional budget overrides (MEM-43).
5. Fill STATUS header and Goal (direction verbatim, done-means mapped to `AC-NNN`). STATE starts with Resume only.
6. Gate check: `.mission/bin/memory-lint.sh` exits 0; `echo '{}' | .mission/bin/session-start.sh` prints the Resume.

### P1 Session start

1. Read `HANDOFF.md`, then what the hook injected (or read by hand: STATUS header + Gates + Board, STATE Resume + Rules
   index + Open failures).
2. If `tmp/memory-debt` was printed: reconstruct the missing delta from `git log` and `.mission/lanes/*/progress.md` first.
3. If Resume `Updated` is older than the latest non-`.mission/` commit, run "Re-verify last change" before planning.
4. For each `EXPIRED F-NNN` you depend on: treat as hypothesis, schedule a re-verify task.
5. Open files listed under "Read first". Do not read `archive/` unless an ID you need lives there.
6. List the R-ids and L-ids relevant to today's tasks; they go into each brief (MEM-24).

### P2 During work

| Event | Write |
|---|---|
| New failure worth >1 retry | O-entry (symptom, `Repro:`, observed/expected, blast radius) before any fix |
| Diagnosis idea | H-entry with `Check:`; falsified → `FALSIFIED <date>` + evidence, keep |
| Claim confirmed by command/artifact | F-entry with Evidence, Level, verified, recheck-by, Scope; `Supersedes: H-NNN` if it came from one |
| Same mechanism verified again | add F-id to the rule's `Instances:`, raise conf |
| Evidence conflicts with a fact | O-entry `CONTRADICTION` (MEM-25) |
| Decision, waiver, downgrade, scope cut | `DECISIONS.md` D-entry + one index line in STATE `## Decisions index` |
| Task state change, gate result, fallback, human question, stop rule fired | STATUS only |
| Reusable across repositories | `LESSONS-INBOX.md` candidate; never the skill |

### P3 Before compaction, reset, hand-off, ~60% context

Rewrite `## Resume` (all six lines of the template), write `HANDOFF.md`, commit `.mission/`. The compact matcher
re-injects Resume after compaction; if Resume is vague, the reset becomes a restart.

### P4 Session end checklist

1. STATUS: board states + evidence, Progress from the latest gate results only (never task counts), Gates table,
   Budget summary line, Done log line, header `Updated:` timestamp and session number.
2. STATE: apply pending deltas by ID; Resume; one `## Last session` line
   (`- <YYYY-MM-DDTHH:MMZ> · s<N> · <what moved> · +F-… ~H-… +R-… +O-…`), keep 5.
3. Inbox: append candidates collected from `lesson_candidates`.
4. `.mission/bin/memory-lint.sh` → fix until exit 0.
5. Budget exceeded or milestone closed → P6.
6. `git add .mission && git commit -m "mission: s<N> memory update"`.

### P5 Merge a worker `memory_delta`

1. Parse the block (`templates/memory-delta.md`). Missing block from a maker/verifier/investigator → ask the worker for
   it once; still missing → record nothing from that return.
2. `facts_add` item without `evidence` + `level` → convert to `hypotheses_add` (MEM-13). With evidence → new F-id,
   `verified` = the evidence run date, `recheck-by` per MEM-41. The per-task verifier's re-run counts as `conf: high`.
3. `hypotheses_add` → H-id (needs `check`); `hypotheses_falsified` → mark `FALSIFIED` + evidence. `failures_add` →
   O-id (needs `repro`). `supersede` → new entry + archive old with `Superseded-by`. `contradictions`, or a conflict
   with an existing F-entry that the worker did not flag → CONTRADICTION O-entry.
4. `rules_cited` → bump nothing in STATE; note cited IDs in the `## Last session` line (feeds P6 step 6).
5. `tasks` → STATUS board only; a state flip to PASSED needs the verifier's verdict, never the maker's delta.
6. `lesson_candidates` → inbox entries written by the orchestrator (fill Origin, Evidence, Applies when).
7. Allocate IDs in the orchestrator only (next free number per prefix); workers use temporary `new-1`, `new-2`.
8. Run `memory-lint.sh`.

### P6 Curator pass (paste-ready)

Triggers: lint budget violation; milestone closed; mission end; `## Last session` > 5 lines; ≥3 open CONTRADICTION
entries; weekly on XL. Runner: `mission-worker` proposes ID-level edits; `mission-verifier` checks information loss.

```text
ROLE: Memory curator for .mission/. You propose ID-level edits; you never rewrite a file wholesale.
INPUT: .mission/STATE.md, .mission/STATUS.md, .mission/LESSONS-INBOX.md, today's date <YYYY-MM-DD>.
DO, in order:
 1 Snapshot: copy STATE.md and STATUS.md to .mission/tmp/*.pre-curate.md; list entry IDs (grep -oE '^- [FHRO]-[0-9]+').
 2 Expire: each F-entry past recheck-by → re-run its Evidence command if cheap (<30 s) and in scope, else move it
   to Hypotheses as an H-entry whose Check: is the old evidence command.
 3 Contradictions: for each CONTRADICTION O-entry re-run both evidence commands; winner stays, loser gets
   Superseded-by <id> and moves to archive/state-YYYY-MM.md.
 4 Close failures: O-entries with a verified fix → one archive line "O-NNN closed <date> by F-NNN (<regression test>)";
   their FALSIFIED hypotheses move into investigations/O-NNN.md.
 5 Merge rules: R-entries with overlapping Applies when and compatible statements → one rule, union of Instances,
   narrowest correct scope, "Merged: R-a, R-b".
 6 Retire rules uncited for 5 sessions and not needed by an open task → archive "Retired (uncited)". Never retire
   conf: high rules guarding data integrity or security.
 7 Roll logs: keep 5 Last session lines, 10 STATUS Done log lines; the rest to archive/.
 8 Offload: any entry body >4 lines → detail into investigations/<id>.md, leave a 2-line entry with the link.
 9 Inbox triage: candidates >60 days with count 1 and cost <1 day → rejected(stale); duplicates → merged-into(L-NNN).
RETURN: a table ID | action (keep/expire/supersede/close/merge/retire/roll/offload) | destination | reason,
plus the exact line edits. Do not apply anything.
```

The orchestrator applies the edits, then spawns the information-loss verifier (fresh context):

```text
ROLE: Information-loss verifier. Prove a memory consolidation lost nothing load-bearing.
INPUT: .mission/tmp/STATE.pre-curate.md, .mission/STATE.md, git diff of .mission/archive/ and .mission/investigations/.
DO: For every entry ID present before and absent after, find where it went (archived / superseded-by / merged-into /
moved-to-investigation) and quote the destination line. For every merged rule, confirm the union of Instances is
preserved and scope is not broadened. For every expired fact, confirm it became a hypothesis or was re-verified with
new evidence and a new verified date. Flag any fact whose wording changed without a supersede.
RETURN: PASS, or FAIL with a table of unaccounted IDs, broadened scopes and silent edits.
```

FAIL → restore the lost entries by ID, re-run the verifier. PASS → `memory-lint.sh` → commit
`mission: curate STATE (-<n> lines, archived <ids>)`.

### P7 Failure → project rule → lesson candidate

Runs when `references/debugging.md` marks a failure PROVEN (conversion parts C–D of `templates/investigation.md`).

1. STATE: the root-cause claim becomes an F-entry whose Evidence is the regression test red on the parent SHA and green
   on the fix SHA. Close the O-entry (archive line) and keep a pointer to `investigations/O-NNN.md`.
2. Distill (D4): group with earlier F-entries by *mechanism*, not by file. ≥1 instance → R-entry with Applies when,
   Instances, Counter-cases, conf by count. Update `## Rules index`.
3. Controls first (D2): if a lint/hook/type/schema constraint can prevent the class, create the task; the lesson
   candidate, if any, must say why prose is still needed.
4. Generic follow-up (D3): audit task over an enumerable scope with a completion check.
5. Candidate (D5) ONLY IF mechanism confirmed ∧ class general ∧ (count ≥2 ∨ cost ≥1 day ∨ user-visible/production).
   Otherwise write "no lesson: <reason>" in the investigation. Phrase bug-hunt lessons as detection techniques ("when
   <symptom shape>, check <mechanism> first"), blamelessly.

### P8 Retro promotion (batched)

1. List inbox entries with status `candidate` meeting b (recurrence/cost). Others stay.
2. **Distiller** (`mission-builder`; `mission-strategist` for XL cross-mission retros over ≥10 investigations):

```text
ROLE: Distiller. Turn verified project facts and closed failures into general rules and lesson drafts.
INPUT: STATE Verified facts + closed O-entries since <date>; LESSONS-INBOX candidates; skill references/lessons.md Contents.
DO: 1 Group facts by underlying mechanism. 2 Draft per group: imperative rule, Applies when, Does not apply when,
Instances (F-ids / origins), confidence by instance count. 3 Decide scope: project-only → STATE R-entry; cross-project →
lesson draft with an eval case (prompt + ≤3 binary assertions, skill-creator format). 4 Check duplicates and
contradictions against lessons.md; propose supersede or merge explicitly. 5 Name the target (criterion h).
RETURN: ID-addressed deltas only. AVOID: project names in lessons; rules from one observation without scope; restating
tool docs; "be careful" rules.
```

3. Mark the entry `verifying`. **Promotion verifier** (`mission-verifier`, fresh context, sees only entry + linked
   evidence + eval case + current lessons.md):

```text
ROLE: Independent promotion verifier. Find reasons NOT to promote.
YOU SEE: one inbox entry, its evidence (commands + outputs), the eval case, current references/lessons.md.
YOU DO NOT SEE the distiller's reasoning; do not ask for it.
CHECK and quote the text satisfying or failing each: a root cause verified · b recurrence ≥2 or cost ≥1 day/production
defect · c general + scoped · d run the eval with-skill and baseline, report assertion results (or state why advisory)
· e you · f duplicates/contradictions · g lessons.md ≤40 entries/300 lines after merge · h SKILL.md body only if the
skill steered a run wrong.
VERDICT: PROMOTE | REVISE(<specific edits>) | REJECT(<criterion>), plus the final lesson text if PROMOTE.
```

4. Disagreement between distiller and verifier, or a SKILL.md-body target → tier-up to `mission-critic`. Two REJECTs →
   `rejected(<criterion>)`.
5. PROMOTE → one PR/commit against the skill (repo-vendored copy for cloud users): add the entry to
   `references/lessons.md` in its phase group, update Contents, append the eval to `evals/evals.json` (next free id),
   set inbox status `promoted` with the lessons.md anchor. Human spot-checks the first eval run after a promotion.
6. Retro report to the user: candidates, promoted/rejected with reasons, eval results, cost of the retro.

## Scale by class (S/M/L/XL)

| Class | Memory footprint | Hooks | Promotion |
|---|---|---|---|
| **S** | No `.mission/`. Resume and facts go in the PR description / task card (`templates/TASK-CARD.md` Generalisation line). At most one candidate line appended to `~/.claude/mission-lessons-inbox.md` | None; the end-of-task checklist is inline | None mid-task; reviewed at the next retro of any mission |
| **M** | `.mission/STATUS.md`, `STATE.md`, `DECISIONS.md`, `LESSONS-INBOX.md` (short entries) | SessionStart; Stop wired but inert (`enforce_stop=0`); PreToolUse frozen-path guard (`protect-frozen.sh`) | At mission end, only if criterion b holds |
| **L** | Full layout: DECISIONS, RESEARCH, investigations/, archive/ | All three hooks of `templates/settings.hooks.json`; `enforce_stop=1` when unattended | Retro per milestone; distiller `mission-builder` |
| **XL** | Full layout; STATE split into `state/*.md` topic files behind a ≤150-line STATE index; monthly archive rollover | All of L; SubagentStop `memory_delta` check only after verifying the hook input schema | Weekly retro; `mission-strategist` cross-mission synthesis; eval per promoted lesson; curator `mission-reviewer` tier-up when ≥3 entries contradict |

A mission reclassified upward at a gate scaffolds the missing files at that gate; a downward reclassification keeps
existing files (D-entry).

## Shape conditionals

- IF **≥2 platforms or surfaces** (e.g. iOS app + Cloudflare backend) THEN `## Verified facts` gets per-surface
  subsections (`### backend`, `### ios`, `### contracts`), Rules index lines carry a surface tag, and toolchain facts
  (Xcode, simulator runtime, wrangler, SDK versions) get `recheck-by` 30 days.
- IF **an API contract is frozen** THEN it lives in `CONTRACTS.md` / the schema file + a D-entry; STATE holds one fact
  "Contract source of truth: `<path>` @ <sha>". Never copy the schema into memory.
- IF **UI with design tokens** THEN tokens and screen specs stay in `design/`; STATE stores only their paths and the
  last accepted screenshot run path (`verification/screens/<run-id>/`), which the vision verifier diffs against.
- IF **bug hunt** THEN `## Open failures` is the spine: every hypothesis has an H-id with `Check:`, FALSIFIED ones stay
  until close, the root-cause fact's Evidence is the regression test, and the promotion check always runs at close
  (big-bug missions are the highest-yield lesson source).
- IF **existing product with CLAUDE.md/AGENTS.md** THEN read them first and do not copy them into STATE; STATE records
  only mission-specific discoveries with grep/command evidence. A plan that conflicts with an existing convention →
  D-entry before implementing.
- IF **migration/extraction** THEN STATE gets `### invariants` under Verified facts: each behaviour that must survive,
  with the command proving it on *both* old and new paths. Cutover steps are STATUS Gates whose Evidence level MUST
  reach `staging` or `production`; offline gates alone keep them `PENDING-LIVE`. Facts about the old system get
  `recheck-by` = planned decommission date, then archive. Rollback trigger + its verification → D-entry.
- IF **research or public content** THEN `RESEARCH.md` is primary (source URL, access date, reliability); STATE holds
  only decided positioning facts citing `S-NNN`/`Q-NN`; market facts expire at 90 days. Promote content-process lessons
  sparingly: they are taste-dependent and hard to eval.
- IF **unattended/cloud run** (Routines, CMA, headless) THEN `enforce_stop=1`, the digest (STATUS header + new Open
  failures) is written before exit, and the skill is vendored (CMP-09).
- IF **multi-repo** THEN one `.mission/` lives in the coordinating repo; the others get a one-line pointer in their PR
  descriptions. No duplicate STATE files.
- IF **credentials, exploits or PII** THEN memory records names and locations only; `memory-lint.sh` secret scan must
  pass before every commit of `.mission/`.

## Model routing

Memory mechanics (loading, freshness, schema validity, budgets) are scripts and cost no tokens. Models are spent on
investigate, distill and independently verify.

| Role | Agent (conventions §7) | Escalate to | Guard that makes the cheaper choice safe |
|---|---|---|---|
| Loader, freshness check, schema/budget lint | no model: `session-start.sh`, `stop-check.sh`, `memory-lint.sh` | — | exit codes; lint fails closed |
| STATE/STATUS merge | orchestrator (session model) | — | deltas ID-addressed and small; lint after merge; git diff |
| Worker `memory_delta` producer | the worker's own agent (typically `mission-worker`) | — | template forces fields; orchestrator demotes evidence-less facts (MEM-13) |
| Failure investigator (stages 2–3) | `mission-worker-high` for env/config/known-flake failures | `mission-builder` after 2 falsified hypotheses, cross-subsystem cause, concurrency or data integrity | evidence command must reproduce the failure and show the fix; verifier re-runs it |
| Evidence re-runner for facts that gate decisions | `mission-checker` | `mission-verifier` when output needs interpretation (perf numbers, flake statistics) | pass requires a quoted output line; L/XL: `mission-verifier` spot-checks 1 in 5 |
| Distiller (fact → rule, candidate → lesson draft) | `mission-builder` | `mission-strategist` for XL cross-mission retros (≥10 investigations or several projects) | promotion verifier + eval with-skill vs baseline |
| Promotion verifier | `mission-verifier`, fresh context, never sees distiller reasoning | `mission-critic` on disagreement or a SKILL.md-body target | verdict cites criteria a–h; 2 REJECTs close the candidate |
| Curator | `mission-worker` proposes ID-level edits | `mission-reviewer` (Opus 4.8 medium) on XL with ≥3 contradicting entries | information-loss verifier `mission-verifier` accounts for every removed ID; lint confirms budget |
| Eval runner / grader | runner `mission-worker` (with-skill and baseline); grader `mission-checker` on binary assertions | `mission-verifier` grader for subjective assertions | assertions pre-written and binary; human spot-check of first run after a promotion |
| CLAUDE.md proposal review | `mission-reviewer` | human | proposal links ≥2 violations; CLAUDE.md stays <200 lines |

Keep Fable 5.1 off the per-failure path; templates carry the discipline Martin's data attributes to stronger models.
No Haiku anywhere.

## Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| Guess in a fact's clothing ("Confirmed 2026-06-09", no command) | memory starts lying with authority | lint rejects F-entries without Evidence/Level/verified |
| Rule from one observation, no scope | CL-Bench's "overfit to immediate observations", made permanent | `Applies when` + `Instances` + `conf: low` |
| "General rules" and "Lessons learned" both in STATE | two homes drift | rules in STATE; cross-project lessons in inbox → skill |
| Status in STATE, facts in STATUS | bloats the loaded index; facts on a board are never consulted | MEM-01 table |
| Silent in-place edit of a verified fact | erases the contradiction signal | supersede by ID; CONTRADICTION entry |
| "Condense STATE.md" in one pass | brevity bias, context collapse | ID deltas + information-loss verifier |
| Workers writing STATE/STATUS in parallel | races, clobbered sections, inconsistent IDs | `memory_delta`; orchestrator is the only writer; CMA workers `read_only` |
| Relying on CLAUDE.md or instructions for read-at-start | "a request, not a guarantee"; Sonnet rarely consults prior notes | SessionStart hook |
| PostCompact for re-injection | output does not reach the conversation | SessionStart `compact` matcher |
| Stop hook that nags or loops (ignores `stop_hook_active`, exits 1, blocks interactive turns) | exit 1 does not block; 8-block override; user fatigue | opt-in `enforce_stop=1`, loop guard, memory-debt file, specific reason |
| Vague resume pointer ("continue auth work") | a reset becomes a restart | runnable next action + re-verify command |
| Writing every lesson into the skill after each failure | merge conflicts, bloat, contradictory guidance (Anthropic reversed `/verify`) | inbox + batched promotion + criterion h |
| Self-graded promotion | self-critique loses to independent-context verification | fresh-context `mission-verifier` |
| Promoting from newly passing tests | no causal link | promote only investigated failures |
| Loading the whole archive "just in case" | every session pays; context rot | hook output ≤ ~3k tokens, rest by path |
| `.mission/` for a typo fix | ceremony and recurring load cost | S row: PR description |
| Eval suite bloat (case per trivial lesson, run at high effort) | cost without signal | cases only for promoted lessons; `mission-checker` grader; retire baseline-passing cases |
| Vector DB / memory service by default | naive ICL beat dedicated memory systems in CL-Bench | plain files; retrieval only if a measured load budget is unfixable by curation |
| Personal skill assumed in cloud runs | personal skills do not load in cloud sessions | vendor the skill (CMP-09) |
| Secrets in memory | memory files are committed and loaded every session | names only; lint secret scan |

## Unverified harness details

| Detail | Status | Safe fallback |
|---|---|---|
| SessionStart stdin field `source` (`startup`/`resume`/`compact`) | community-sourced, not seen in the full hooks reference | `session-start.sh` defaults to `startup` and prints the same content for every source |
| `CLAUDE_PROJECT_DIR` env var in hook commands | official hooks guide shape + community examples | scripts fall back to `git rev-parse --show-toplevel`, then the current directory |
| Stop block JSON `{"decision":"block","reason":…}` on exit 0; exit 1 does not block; exit 2 blocks | Academy course + third-party guide | `stop-check.sh` emits the JSON form and exits 0; if a harness ignores it, the next SessionStart prints `tmp/memory-debt` |
| `stop_hook_active` field in Stop input | third-party guide | guard matches the literal `"stop_hook_active": true`; absent field → one block only, then 8-block override ends the turn (verified official) |
| SubagentStop input schema (transcript access) | not verified | do not ship a SubagentStop delta check; P5 step 1 asks the worker instead |
| SessionEnd can block or inject | not verified | Stop hook + memory-debt file |
| Hook `timeout` field and per-hook default | not verified | scripts do no network and finish in well under a second on normal STATE sizes |
| CMA memory-store mount path (`/mnt/memory/<slug>/`) | third-party | read the mount note Claude adds to the system prompt; never hard-code the path |
| Auto memory settings (`autoMemoryDirectory`) and subagent `memory:` frontmatter | third-party | do not use in v1 (MEM-05) |
| `stat` flags differ on macOS vs Linux | known portability issue | `stop-check.sh` tries GNU `stat -c %Y`, then BSD `stat -f %m`, then exits 0 (no block) |
| Thresholds (150/100 lines, ~3k tokens, 30 inbox, 40 lessons, 5-session retirement, 90/30/14-day expiry) | judgment calls, not measured | overridable in `.mission/config` (MEM-43) |

## Evidence

1. Lance Martin, "Designing loops with Fable 5" (2026-06-09), 5-stage framing, Sonnet "rarely consults prior notes",
   "task-specific memory instructions are needed": https://github.com/lchesupercool/ob-clippings/blob/main/2026-06/2026-06-10-designing-loops-with-fable-5.md
2. CL-Bench (Berkeley Sky lab), "naive ICL outperforms systems dedicated to memory management": https://arxiv.org/abs/2606.05661
3. ACE, "brevity bias" and "context collapse", incremental deltas: https://arxiv.org/html/2510.04618v1
4. Claude Code skills docs: `/verify` edits "only when it steered a run wrong"; personal skills not in cloud sessions: https://code.claude.com/docs/en/skills
5. Claude Code memory docs: 200 lines / 25 KB auto-memory load; "Claude may pick one arbitrarily": https://code.claude.com/docs/en/memory
6. Hooks reference (events): https://code.claude.com/docs/en/hooks · Academy hooks course (SessionStart `compact`, exit codes): https://academy.claude.com/courses/claude-code-in-action/hooks
7. Best practices: Stop hook overridden after 8 consecutive blocks: https://code.claude.com/docs/en/best-practices
8. Managed Agents memory stores (100 kB per memory, many small files, `read_only`): https://platform.claude.com/docs/en/managed-agents/memory
9. skill-creator `evals/evals.json` format, with-skill vs baseline: https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/plugins/skill-creator/skills/skill-creator/SKILL.md
10. Context engineering (structured note-taking, attention budget): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
11. `arcwell/docs/handoff/2026-08-21-remediation-status.md` lines 3–10, 59–60, 168, 216–221 (one authoritative doc per
    fact kind, gate command per item, distilled rules, evidence-level honesty)
12. Source report `research/mission-skill/07-memory-compounding.md` §4, §6, §7; STATUS merge from
    `research/mission-skill/01-orchestration-control.md` §7.1; conversion rules `research/mission-skill/08-failure-investigation-lessons.md` §4.7
