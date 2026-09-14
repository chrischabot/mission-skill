# 10 · State, status, and memory files

Researcher report for the `/drive` skill, written 2026-09-14. Component: the files that carry a run across compaction, session ends, and subagent boundaries (STATE.md, STATUS.md, LESSONS.md and their conditional companions), the rules for reading and writing them, and the lint that keeps them honest. This covers the post's steps 10 and 11 and the owner's "how to track things in STATUS.md".

Throughout, claims are marked **[verified]** (checked against a live page today, URL given in section 3), **[source claim]** (asserted by the post or another secondary source, not independently confirmed), or **[opinion]** (mine, argued).

---

## 1. Executive opinion

Everything the skill knows that is not in code, tests, or git evaporates at the next compaction, the next session, or the next subagent boundary. The files are the only memory that survives, so they decide whether a run resumes or restarts, and whether the final report is true. That makes this the component most exposed to the owner's two dislikes: tracking overhead, and mirage completion.

The answer to both is the same: fewer files, each with one job, each machine-checked. Three files carry almost every project. STATE.md is the resume pointer plus the small set of facts the code cannot tell you. STATUS.md is the ladder: one row per refutable behavioral claim, with typed evidence pointers a script resolves. LESSONS.md holds rules distilled from verified failures, each citing the failure that taught it. Everything else (hypothesis ledger, research ledger, decisions, spec, designs, proof bundles) appears only when the project shape earns it, in the same `.drive/` directory, committed with the code.

The rules matter more than the templates. Workers report and the orchestrator writes, so there is never a concurrent edit. Nothing is written down that git or the code already records. A fact without a "verified by" clause is a guess and is not allowed in the facts section. A lesson that names a file is a fix, not a rule, and stays out. A small script (`drive-lint`) enforces the shape: every row has a status, every status carries the evidence its rung demands, no Live Proof without a live artifact, STATE.md never older than the last code commit. A Stop hook runs that script so a session cannot end with stale state, and the `/goal` condition asks for the same script's clean output, so the fresh-model judge and the deterministic gate agree on what "done" means.

The research supports the restraint. The benchmark paper the post leans on found that dedicated memory systems introduced "spurious generalizations and stale beliefs" and lost to plain in-context learning. Memory pays only when it is small, verified, and consulted. Fable 5's edge in Anthropic's own small experiment was finishing the verify and distill stages, not writing more notes.

---

## 2. What the post says, and a critique

The post's steps 10 and 11 make four moves: it presents a five-stage memory progression as coming "from Anthropic's Continual Learning Bench 1.0"; it quotes per-model verification-coverage numbers; it shows a STATE.md with five sections mapped to the stages; and it states two operational rules, write before walking away and read at session start. Step 12 adds that lessons should be written into the skill, not only into project memory.

**The attribution is wrong.** Continual Learning Bench is a third-party benchmark by Parth Asawa and colleagues at UC Berkeley, Snorkel AI, and UW-Madison (arXiv 2606.05661, submitted 4 June 2026) **[verified]**. It covers six domains and defines a "gain" metric that isolates learning from base capability. It does not define a five-stage progression. What Anthropic did was smaller: R. Lance Martin, who works at Anthropic, ran Fable 5, Opus 4.7, and Sonnet 4.6 on the benchmark's database-querying task (30 sequential questions, each a separate agent session, memory provided through a mounted filesystem shared across sessions in Claude Managed Agents) and described the progression and the numbers in an article on X **[verified]**. He calls these "small scale experiments" and says so twice. The numbers the post repeats (Sonnet exits around stage 1; Opus around stage 3 with 7–33% verification coverage, median about 17%; Fable up to 73%, meaning 22 of 30 questions) are his, from one task family, one run set. They are suggestive, not measured properties of the models.

**The STATE.md example is the post author's, not Anthropic's.** Martin's article shows no state file and states no operational rules **[verified]**. The gloss is reasonable in spirit: the memory tool's built-in system prompt says "ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE" and "ASSUME INTERRUPTION: Your context window might be reset at any moment" **[verified]**, and Anthropic's long-running-harness post has agents read a progress file at the start of each session and update it at the end **[verified]**. But the post should not be cited as Anthropic guidance on file layout, and the example itself has flaws. "General rules" and "Lessons learned" are both stage 4 with no distinction between them. The file mixes the resume pointer, cross-session knowledge, and the open-failure ledger in one place, so it cannot stay small. There is no status for requirements at all, no evidence model, and no size rule. In the owner's anti-mirage culture this is exactly the file where hollow completion would hide: "3 fixes drafted" is not a status anyone can check.

**The post misses the paper's own headline.** Full-context in-context learning with Sonnet 4.6 topped the gain metric (25.4% normalized gain); Claude Code driving Sonnet 4.6 with automatic compaction came third (23.9%); the dedicated memory system ACE came tenth (8.6%) at the highest cost of any system **[verified]**. The authors attribute the losses to agents that "overfit to immediate observations or fail to reuse knowledge across instances" and to memory systems that "introduce spurious generalizations and stale beliefs" **[verified]**. This is the strongest external argument for the owner's instincts: memory must be minimal and verified, and the harness must never let a note outrank the code. The progression is valuable precisely because stages 3 and 4 are filters, not because stage 1 accumulates.

**Where the post is right.** Memory lives in files. The end of a session must write and the start must read. Project memory and cross-project procedural memory are different things and live in different places. The verifier must be a different context from the maker. Anthropic's Fable 5 prompting page corroborates the skill-writing point: Fable "does a good job of updating skills on the fly based on what it learns from the task at hand", with the counterweight that "skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality" **[verified]**. So lessons must be pruned into the skill, not only appended.

**What the post leaves undefined is the whole job.** Which files, why each exists, how big, who writes, what counts as evidence, how the ladder maps to evidence, how to resume after compaction, what a machine can check. The rest of this report supplies that.

---

## 3. Verified facts with URLs

Anthropic sources on memory and long runs:

- Lance Martin (Anthropic), "Designing loops with Fable 5" on X: the five-stage progression ("fail ... investigate ... verify ... distill ... consult"), the per-model numbers, the setup (CL-Bench 1.0 database task, 30 questions, each question a separate session, memory via CMA mounted filesystem), the loop quote ("Rather than directly prompting and steering Fable 5, it's often better to design loops that let the model to self-correct in response to environment feedback (e.g., /goal or Outcomes) and manage its own context (e.g., via memory)"), the "small scale experiments" caveat; no state-file example, no operational rules. https://x.com/RLanceMartin/article/2064397389189071163 (read via a mirror because X blocks fetches).
- Continual Learning Bench paper: authors and affiliations, six domains, gain metric, ICL-beats-memory finding, "spurious generalizations and stale beliefs", Claude Code third at 23.9% gain. https://arxiv.org/abs/2606.05661 and https://arxiv.org/html/2606.05661
- "Effective context engineering for AI agents" (29 Sep 2025): structured note-taking ("the agent regularly writes notes persisted to memory outside of the context window"), NOTES.md example, compaction, subagents return "a condensed, distilled summary ... often 1,000-2,000 tokens", "Note-taking excels for iterative development with clear milestones." https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- "Effective harnesses for long-running agents" (26 Nov 2025): initializer and coding agents; `claude-progress.txt`; a feature list in JSON with `passes: false` per feature; JSON chosen because "the model is less likely to inappropriately change or overwrite JSON files compared to Markdown files"; "It is unacceptable to remove or edit tests"; one feature at a time; leave the environment in a clean state; failure modes: one-shotting, declaring done prematurely, context loss "even with compaction", marking features complete "without proper testing". https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Memory tool docs: the injected system prompt (view memory before anything else; record progress; assume interruption), the multisession pattern (initializer session, subsequent sessions read memory files, end-of-session update), and "Mark a feature complete only after end-to-end verification confirms it works, not when the code is written." https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
- "Prompting Claude Fable 5": "Construct a memory system" ("Store one lesson per file with a one-line summary at the top. Record corrections and confirmed approaches alike, including why they mattered. Don't save what the repo or chat history already records; update an existing note rather than creating a duplicate; delete notes that turn out to be wrong."); "Ground progress claims during long runs" ("audit each claim against a tool result from this session"); verifier subagents outperform self-critique; the "rare cases of early stopping" text-only-intent failure and the autonomous-operation reminder; the final-summary-as-re-grounding guidance; the warning not to ask the model to echo its reasoning (triggers a refusal category). https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- Claude Managed Agents memory (23 Apr 2026): memories are files on a mounted filesystem with an audit log; vendor case-study numbers (Rakuten "97% fewer first-pass errors") are marketing claims, not benchmarks. https://claude.com/blog/claude-managed-agents-memory

Claude Code harness facts that constrain the design:

- Memory: auto memory lives at `~/.claude/projects/<project>/memory/`, `MEMORY.md` index loaded "first 200 lines or 25KB, whichever comes first"; topic files load on demand; four note types (`user`, `feedback`, `project`, `reference`); Claude "skips anything it can derive from the codebase"; CLAUDE.md "target under 200 lines"; project-root CLAUDE.md is re-read after `/compact`; a `modified` frontmatter timestamp is stamped on memory files (v2.1.214+); the main conversation's auto memory is not loaded into subagents; block-level HTML comments in CLAUDE.md are stripped before injection. https://code.claude.com/docs/en/memory
- What survives compaction: project-root CLAUDE.md and unscoped rules, auto memory, and the plan-mode plan are re-injected from disk; up to five most recently modified files are re-read (a file over 5,000 tokens comes back as a path reference); invoked skill bodies re-injected "capped at 5,000 tokens per skill and 25,000 tokens total; oldest dropped first", truncation keeps the start of the file; SessionStart hooks matching `compact` run and their output is added. The skill listing is not reloaded. https://code.claude.com/docs/en/context-window
- Hooks: Stop input JSON carries `session_id`, `transcript_path`, `cwd`, `permission_mode`, `stop_hook_active`, `last_assistant_message`; exit 2 blocks the stop; the JSON block form is `{"hookSpecificOutput":{"hookEventName":"Stop","decision":"block","reason":"..."}}`; stderr on exit 0 goes only to the debug log; SessionStart matchers are `startup|resume|clear|compact|fork`; `PreCompact`/`PostCompact` exist; `SubagentStop` exists; hooks declared in skill frontmatter are registered when the skill is invoked and persist for the rest of the session (`once: true` removes after first success); prompt hooks return `{"ok":..., "reason":...}` and, for Stop, `"impossible": true` allows the stop; agent hooks are experimental (60 s, up to 50 tool turns); default timeouts 600 s command, 30 s prompt. https://code.claude.com/docs/en/hooks
- Stop hook block cap: "Claude Code overrides a Stop hook after it blocks eight times in a row without progress", raise with `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`; re-inject context after compaction with a `SessionStart` hook, matcher `compact`, whose stdout is added to context. https://code.claude.com/docs/en/hooks-guide
- `/goal`: "a wrapper around a session-scoped prompt-based Stop hook"; evaluated by the small fast model (Haiku by default; `ANTHROPIC_DEFAULT_HAIKU_MODEL` overrides everywhere the small model is used); "It doesn't run commands or read files independently, so write the condition as something Claude's own output can demonstrate"; verdicts met, not yet met, impossible; 4,000 characters; bound with "or stop after 20 turns"; restored on every resume route with turn count reset; works with `-p`; background work defers evaluation with check-ins after 30 minutes; a stall (no tool use for several turns) stops the loop with the goal still set. https://code.claude.com/docs/en/goal
- Subagent memory: `memory: user|project|local` maps to `~/.claude/agent-memory/<name>/`, `.claude/agent-memory/<name>/`, `.claude/agent-memory-local/<name>/`; the first 200 lines or 25KB of that MEMORY.md go into the subagent's system prompt; requires auto memory enabled; `isolation: worktree` is cleaned up automatically if the subagent makes no changes; a subagent that hits `maxTurns` returns output marked partial (v2.1.246+). https://code.claude.com/docs/en/sub-agents
- Sessions: transcripts at `~/.claude/projects/<project>/<session-id>.jsonl`, format "internal to Claude Code and changes between versions"; resume restores conversation, model, agent, active goal, and unexpired scheduled tasks, but not background Bash or monitor tasks; `-p` sessions are left out of the picker but resumable by ID; on Pro/Max, resuming after more than about an hour idle with over 100k tokens offers "Resume from summary" (runs `/compact`). https://code.claude.com/docs/en/sessions
- Best practices: "Give Claude a way to verify its work"; a Stop hook "runs your check as a script and blocks the turn from ending until it passes. Claude Code overrides the hook and ends the turn after 8 consecutive blocks"; "Have Claude show evidence rather than asserting success"; adversarial review in a fresh subagent; "Customize compaction behavior in CLAUDE.md with instructions like 'When compacting, always preserve the full list of modified files and any test commands'"; "If you can't verify it, don't ship it." https://code.claude.com/docs/en/best-practices

Owner conventions read from his repositories (read-only; these are facts about his existing practice, not external sources):

- Arcwell v2 tracks requirements in a generated `REQUIREMENTS.yaml` merged from the spec and a curation file; `pnpm verify:requirements` fails if a registered test reference does not resolve to an exact `path::test_name`, if the test does not cite the requirement it claims to prove ("a proof must claim what it proves"), if one test is the sole oracle for more than five critical requirements, if the committed registry differs from regeneration, or if the spec's recorded digest changed without review. Status vocabulary there is `planned | implemented | live-only`, and live references point into a live acceptance register with `path::check_id`.
- His handoff documents record each expectation as exactly one of **Observed**, **Inferred**, or **Unverified**, with the exact command that would close an Unverified item; landed work is a table of items with PR links and one-line descriptions; the milestone ledger checks an item "only after the gate command has been run green on a clean workspace".

---

## 4. Detailed spec

### 4.1 Where the files live

All working state goes in one directory at the project root: `.drive/`. It is committed with the code, because the owner commits straight to main and a run must be resumable from any checkout; state that lives only in `~/.claude` is machine-local and vanishes on a clone. A single gitignored subdirectory, `.drive/local/`, holds things that must not travel: worker scratch, large logs, the active-run marker. Secrets go nowhere in `.drive/`, ever; the lint greps for the usual token shapes and fails.

Why a dotted directory rather than `docs/drive/`: the state files are the skill's working area, not product documentation, and the owner is the only human reader; he reads the final report, not the tree. When the project shape makes documents the product (the research-and-website shape, or a repo with an established `docs/` convention), the deliverable documents (SPEC, DESIGN-*) move to where the repo keeps documents and `.drive/` keeps only the working state plus pointers. When a repo already has its own requirement registry and gate (Arcwell's `REQUIREMENTS.yaml` and `verify:requirements` is the live example), STATUS.md does not duplicate it; it becomes a short pointer file and the lint runs the repo's own gate. Two registries for one truth is the anti-pattern this whole component exists to prevent.

```
.drive/
  STATE.md            resume pointer, verified facts, rules in force, open failures   (always)
  STATUS.md           the ladder: one row per behavioral claim, with evidence          (always; may be 1–3 rows)
  LESSONS.md          rules distilled from verified failures                            (always; may be empty)
  HYPOTHESES.md       hypothesis ledger with repro pointer                              (bug hunt, incident)
  RESEARCH.md         questions, findings with confidence, sources                       (any shape with a research stage)
  DECISIONS.md        dated decisions with alternatives and undo                         (greenfield, migration, feature)
  SPEC.md             the specification (owned by the spec stage)                       (greenfield, feature, migration)
  DESIGN-backend.md   (owned by the architecture stage)
  DESIGN-frontend.md  (owned by the architecture stage)
  TESTPLAN.md         (owned by the test-design stage; small shapes fold it into STATUS rows)
  REPORT.md           the final report, generated from the files above                  (always, at the end)
  proofs/<ID>/        proof.json plus small artifacts (screenshots ≤200 KB, log tails)  (per Local/Live Proof row)
  reviews/            adversarial review dispositions, one file per review              (per verify stage)
  local/              gitignored: workers/<name>/report.md, big logs, active marker
```

### 4.2 The minimal set, and why each file exists

The owner dislikes tracking overhead, so every file has to justify itself against the question "what breaks if this is folded into another file?"

**STATE.md** exists because a fresh context needs one place to read first, and that place must be small. It answers: what is the next action, why, what is blocked, what is in flight, which facts have been checked so nobody re-derives them, which project rules are in force, and which failures are open. It is rewritten at every stop. Budget: 150 lines, 8 KB (about 2,000 tokens). Folding STATUS into it would blow the budget within a day on a greenfield app; folding LESSONS into it would mix project-scoped state with knowledge meant to leave the project.

**STATUS.md** exists because "done" must be a checkable property of rows, not a feeling. It has a different write cadence from STATE (phase gates, not every stop), a different reader (the verifier and the report generator, not the resumer), and a different size profile (it grows with requirements and never shrinks). Anthropic's harness post kept the feature list separate from the progress file for the same reasons, and found that a strict, machine-shaped file was less likely to be corrupted by the model **[verified]**. This report keeps STATUS.md as Markdown so it renders in the report and on GitHub, but with a fixed table grammar the lint parses, and a rule the lint enforces: rows are never deleted, only moved to Dropped with a reason.

**LESSONS.md** exists because a rule that leaves the project needs to be findable and to carry its provenance. Its entries are the output of stage 4 (distill); the promotion step to the skill's own lessons file reads from here. It is append-mostly with a consolidation pass. Putting rules in STATE.md's "rules in force" section is allowed only for project-specific rules; anything general must live here so it can be promoted.

**HYPOTHESES.md** exists for bug hunts and incidents because a hypothesis ledger has its own grammar (prediction, test, result, refuted or confirmed) and a bug hunt with a dozen hypotheses would swamp STATE.md's open-failures section. It replaces most of the STATUS ladder for that shape.

**RESEARCH.md** exists whenever the run includes a research stage, because findings must carry confidence and sources or they become the "stale beliefs" the CL-Bench authors warned about. The owner asked for a research ledger with online search for the greenfield shape explicitly.

**DECISIONS.md** exists (one file, not an ADR directory) for shapes where a later agent will find the code doing something odd and needs to know it was chosen, what was rejected, and how to undo it. This is the owner's audit-plus-undo culture in file form: decisions are made autonomously and recorded, never queued. One file with dated entries is enough until it exceeds the budget; an ADR directory is ceremony that does not pay for itself on a personal project.

**SPEC.md, DESIGN-*.md, TESTPLAN.md** are deliverables of other stages and other reports specify them. Here they matter only in two ways: STATUS.md row IDs originate in SPEC.md's requirement list (or in STATUS.md itself for small shapes), and they sit at the bottom of the truth precedence, below STATUS, so a disagreement between prose and a STATUS row is resolved by the row and the code, never by the prose.

**Proof bundles** exist because "test passed" in a chat message is not evidence a later session can check. Each bundle is a directory named after the row it proves, with a `proof.json` manifest (command, exit code, environment, commit, artifact hashes, verdict, and the mandatory answer to "where is this harness kinder than production?") plus small artifacts. Commit the manifests and screenshots; gitignore logs above a size cap and record their hash so a missing log is detectable but not fatal.

### 4.3 Templates

Section semantics are tied to the five stages (Fail, Investigate, Verify, Distill, Consult) and to the ladder (Missing, Scaffold, Partial, Local Proof, Live Proof, Operational, Done). The templates below are exact; the lint parses the headers and the tables.

#### STATE.md

```markdown
# STATE · <project> · <goal in one line>
updated: 2026-09-14T09:12:04Z
commit: 4f2a9c1
phase: implement            # intake | research | spec | design | tests | implement | verify | distill | report
session: drive-outfitter-ios  # name given with /rename; resume with: claude --resume drive-outfitter-ios
live means here: <what "live" is for this project, decided at intake, e.g. "deployed Worker on workers.dev + app on iPhone 17 simulator against it">

## Resume here                                   (stage 5: consult before re-deriving)
Next action: <one imperative sentence; the first thing a fresh context should do>
Why: <one sentence>
Blocked on: none | <the single thing, and who can unblock it>
In flight: none | worker-2 → R-07,R-08 (writes .drive/local/workers/worker-2/report.md) | verifier → review of R-01..R-06
Gates passed: intake ✓ research ✓ spec ✓ design ✓ tests ✓ | implement (current) | verify | distill | report

## Verified facts                                (stage 3: each line names how it was checked)
- D1 rejects statements with more than 100 bound parameters. Verified: live query against arcwell-v2 returned SQLITE_RANGE on 101 binds, 2026-09-13.
- The simulator's accessibility tree omits elements under 4 pt. Verified: `inspect` on iPhone 17 Pro, 2026-09-13.

## Rules in force                                (stage 4, project-scoped; general rules go to LESSONS.md)
- Chunk every D1 batch at 90 parameters. Because of the 100-bind limit above. From: F-03.
- UI verification screenshots are taken at 3x scale on iPhone 17 Pro only. Because the design tokens were specified at that size. From: D-04.

## Open failures                                 (stage 1 → 2: documented, under investigation)
- F-07 (2026-09-13) Outfit save returns 200 but the row is missing on the second device. Observed: two simulators, 3 of 10 runs. Hypothesis: write lands after the read replica is queried. Repro: `.drive/local/repro/f07.sh`. Next: log the sequence numbers on both paths.
```

Rules the lint enforces on STATE.md: the `updated` and `commit` header fields exist and parse; `Next action:` is non-empty; every bullet under Verified facts contains `Verified:`; every Open failure has an ID `F-nn`, a date, and either `Repro:` or `Observed:`; the file is under budget. A fact that cannot name how it was verified is moved to Open failures as a hypothesis or deleted; it does not stay as a fact.

What does not go in STATE.md: anything git or the code already says (which files changed, what a function does), the full list of requirements (that is STATUS.md), general lessons (LESSONS.md), or narrative of what happened (the report and git log carry that).

#### STATUS.md

```markdown
# STATUS · <project>
ladder: Missing → Scaffold → Partial → Local Proof → Live Proof → Operational → Done   (Dropped is a terminal side-state, needs why:)
rules: rows are never deleted; a status moves only with the evidence its rung requires; Live Proof requires live:; Done requires review: and live: when needs-live is y.
evidence grammar: test:<path>::<name> | severe:<path>::<name> | proof:.drive/proofs/<ID>/ | shot:<path.png> | live:.drive/proofs/<ID>/ | ops:<url or path> | review:.drive/reviews/<file> | commit:<sha> | pr:#<n> | doc:<path> | why:<text>

| ID   | Claim (behavioral, refutable)                                              | Needs live | Status      | Evidence                                                                                                   | Updated    |
|------|----------------------------------------------------------------------------|------------|-------------|------------------------------------------------------------------------------------------------------------|------------|
| R-01 | An expired token is rejected with 401 and no session row is created        | y          | Live Proof  | test:api/tests/auth.test.ts::expired_token_rejected; severe:api/tests/severe_auth.test.ts::forged_exp_claim_rejected; live:.drive/proofs/R-01/; commit:4f2a9c1 | 2026-09-14 |
| R-02 | Saving an outfit with 40 items succeeds and re-reads identically           | y          | Local Proof | test:api/tests/outfits.test.ts::save_40_items_roundtrip; severe:api/tests/severe_outfits.test.ts::save_101_items_is_chunked_not_truncated; commit:4f2a9c1 | 2026-09-14 |
| R-03 | The wardrobe grid renders 200 items at 60 fps on iPhone 17 Pro             | n          | Partial     | test:ios/Tests/GridPerfTests.swift::grid_200_items_under_16ms; commit:31be0d2                               | 2026-09-13 |
| R-04 | Users can share an outfit by link                                          | y          | Dropped     | why: out of scope after D-03 (no public sharing in v1)                                                      | 2026-09-12 |
```

The claim column is the behavioral claim named before coding, in the owner's culture. The lint warns when a claim starts with "Implement", "Add", "Create", "Set up", "Wire", or "Refactor", because those describe work, not behavior; a claim must be something a test can try to refute.

The `Needs live` column is set at spec time and answers whether local proof can ever be enough for this row. Backend behavior against a real datastore, anything that crosses a network boundary, and anything the owner will touch on a device gets `y`. Pure functions, layout under a fixed viewport, and CLI parsing usually get `n`. The lint requires a `live:` pointer for Done when the column says `y`, and refuses Live Proof on any row whose live bundle was produced in a local harness.

For a greenfield project with more than about 150 rows, split by area (`STATUS-backend.md`, `STATUS-ios.md`) and keep `STATUS.md` as an index with one line per area and its counts. Do not split earlier; a single table is easier to lint and to read.

#### Ladder semantics and the evidence each rung requires

| Rung | Meaning | Evidence the lint demands |
|------|---------|---------------------------|
| Missing | No code path exists for the claim. | none |
| Scaffold | A code path exists; nothing about the behavior is shown. | `commit:` |
| Partial | Some of the behavior is shown by a passing test; the claim is not fully covered or a known gap remains. | ≥1 `test:` |
| Local Proof | The claim's test passes and at least one adversarial test tried to refute it, in a local harness. UI rows also need a `shot:`. | ≥1 `test:` and ≥1 `severe:` (and `shot:` when the row is tagged ui) |
| Live Proof | The same claim shown against the real environment named in STATE.md's "live means here". | Local Proof set plus `live:` whose `proof.json` has `environment` of `live` or `device`, `verdict: pass`, and a non-empty `shim_differences` answer |
| Operational | Live, and observed over time or under monitoring: a health probe, a run window, a runbook exists. Only for shapes with a running service. | Live Proof set plus `ops:` |
| Done | Everything agrees: code, tests, the adversarial review disposition, live proof where required, docs, and this row. | Local Proof set plus `review:`; plus `live:` when Needs live is y; `doc:` when the row changed user-facing behavior |
| Dropped | Deliberately not pursued; the reason is recorded. | `why:` |

Local-only work is never labelled Live Proof. The lint cannot know whether a harness is kinder than production, but it can force the question to be answered: every proof bundle's `shim_differences` field must be present, and `[]` is accepted only with a `shim_differences_note` explaining why there is no shim at all.

#### proof.json

```json
{
  "requirement": "R-01",
  "claim": "An expired token is rejected with 401 and no session row is created",
  "environment": "live",
  "target": "https://outfitter-api.chabotc.workers.dev",
  "commit": "4f2a9c1",
  "produced_by": "verifier",
  "started": "2026-09-14T08:40:12Z",
  "commands": [
    {"cmd": "curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer <expired>' $TARGET/session", "exit": 0, "stdout_tail": "401"},
    {"cmd": "wrangler d1 execute outfitter --remote --command \"select count(*) from sessions where token_hash='...'\"", "exit": 0, "stdout_tail": "0"}
  ],
  "artifacts": [
    {"path": "response-headers.txt", "sha256": "…", "kind": "response"},
    {"path": "d1-count.txt", "sha256": "…", "kind": "log"}
  ],
  "shim_differences": [
    "Local tests use miniflare's D1 emulation, which does not enforce the 100-bind limit; the live target does. This proof ran against the live target, so no shim applies to this row."
  ],
  "verdict": "pass",
  "notes": ""
}
```

`environment` is one of `local`, `simulator`, `device`, `live`. A `simulator` proof is Local Proof for UI rows and Live Proof only if the simulator talked to the live backend, which the `target` field must show. Screenshots go next to the manifest, downscaled to fit 200 KB; the report links them.

#### LESSONS.md

```markdown
# LESSONS · <project>
One entry per rule. A rule says when, what, and why, and names the verified failure that taught it. Specific fixes belong in git history, not here.
Scope is `general` (to be promoted to the skill's lessons file) or `project`.

## L-01 · When a local harness stands in for a production store, encode the production limit in the harness
- Scope: general
- Shapes: all
- Rule: Before trusting green tests against a shim or emulator, list each limit the real service enforces (bind counts, payload sizes, rate limits, timeouts) and make the shim enforce it or add a live test for it.
- Because: a harness kinder than production certifies broken code; 24 green runs preceded a live failure at 101 binds.
- Taught by: F-03 (STATE, resolved 2026-09-13), verified by api/tests/severe_outfits.test.ts::save_101_items_is_chunked_not_truncated and the live proof for R-02.
- Promoted: 2026-09-14 → ~/Projects/drive/skill/references/lessons.md (L-general-017)
```

The lint requires `Rule:`, `Because:`, and `Taught by:` on every entry, and warns when a Rule line contains a path, a line number, or a commit hash, because that is the shape of a fix pretending to be a rule. Promotion is allowed only for entries whose `Taught by:` names a verified failure or a proof; a guess is never promoted.

#### HYPOTHESES.md (bug hunt and incident shapes)

```markdown
# HYPOTHESES · <bug in one line>
Observed: <exact symptom, with log lines and paths>
Expected: <what should happen>
Repro: `.drive/local/repro/f07.sh` reproduces 3 of 10 runs; first seen at commit 9d1e0aa (2026-09-10); does not reproduce at 7c44b12
Ground truth so far: <facts established, each with how; these also go to STATE.md Verified facts>

| H  | Hypothesis                                    | Prediction if true                                  | Test performed                              | Result        | Status    |
|----|-----------------------------------------------|-----------------------------------------------------|---------------------------------------------|---------------|-----------|
| H1 | Webhook handler races the write               | Delaying the webhook 500 ms makes it 10/10          | Injected delay, 20 runs                      | 3/20, unchanged | Refuted |
| H2 | Read hits a replica before the primary commits| Sequence number in read < sequence in write         | Logged both, 10 runs                         | 3/10 lower    | Confirmed |
```

Status is `Open`, `Testing`, `Refuted`, `Confirmed`, or `Suspect`. Confirmed requires two things: the prediction was observed, and removing the cause removed the symptom (a fix behind a flag, or a targeted change, run against the repro). The owner's rule "second time is the bug" is encoded: if a workaround is applied a second time for the same symptom, the earlier Confirmed row is set to Suspect and the ledger reopens. The fix itself still gets a STATUS row with a refuting regression test, and a live proof if the bug was live.

#### RESEARCH.md

```markdown
# RESEARCH · <question or scope>
## Questions
- Q1 <question> → F1, F3
- Q2 <question> → open
## Findings
- F1 <claim>. Confidence: verified (S2, fetched 2026-09-14) | source claim (S4) | inference from F2+F3. Affects: R-05, D-02.
## Sources
- S1 <title> · <URL> · fetched <date> · kind: docs | paper | vendor blog | forum · note: <what it is good for and what it is not>
## Contradictions and open threads
- S3 says X, S5 says Y; resolved by testing (F6) | unresolved, choosing X because <reason> (D-02)
```

Every finding names its confidence and its sources; every finding that changed a requirement or a decision names it. A finding with no source is not a finding; it is a hypothesis and goes to STATE.md's open failures or is dropped.

#### DECISIONS.md

```markdown
# DECISIONS · <project>
## D-02 (2026-09-13) · Chunk D1 writes at 90 bound parameters instead of switching to batch statements
- Context: R-02 failed live at 101 binds (F-03).
- Decision: chunk in the repository layer; keep a single-statement API for callers.
- Rejected: D1 batch API (adds a transaction boundary we do not need); raising the limit (not possible).
- Consequences: writes over 90 items are two round trips; ordering is preserved by the chunker.
- Undo: revert commit 7e1c3aa; the callers are unchanged.
- Evidence: severe:api/tests/severe_outfits.test.ts::save_101_items_is_chunked_not_truncated; live:.drive/proofs/R-02/
```

Decisions are made autonomously and recorded with an undo line; this is the audit-plus-undo the owner asked for in place of approval queues. The only decision that ever reaches him is one where the alternatives differ in something only he can weigh, and then the file records that it was surfaced, once, and what was chosen or what the default will be if he does not answer.

### 4.4 Operational rules

#### Read at start

Order and budget matter because the SKILL.md body is re-injected after compaction with only its first 5,000 tokens **[verified]**, so the read-at-start procedure must sit near the top of SKILL.md and the state files themselves must be small enough to load whole.

1. Run `drive-lint --start`. It prints: STATE.md's header and "Resume here" section verbatim; the count of rows per rung; the open (not Done, not Dropped) rows; the open failures; any staleness or lint errors. This is at most about 60 lines.
2. Read STATE.md in full (≤8 KB).
3. Read LESSONS.md in full if it is under 4 KB, otherwise only its entry headings.
4. Read the skill's own lessons file, `${CLAUDE_SKILL_DIR}/references/lessons.md`, filtered by the project's shape (entries are tagged `Shapes:`).
5. Read STATUS.md rows for the current phase only: the `--start` output already listed open rows; open the file when a row's evidence must be inspected.
6. Load on demand, never at start: SPEC.md and DESIGN-*.md sections for the current phase, RESEARCH.md findings referenced by the rows in hand, DECISIONS.md entries by ID, proof bundles never (read `proof.json` only when refuting or reporting).

Total startup load from state files should stay under about 6,000 tokens. Auto memory is loaded by the harness on its own and is not part of this procedure; the skill does not write project state into auto memory (see 4.7).

#### Write before walking away

At every phase gate (intake → research → spec → design → tests → implement → verify → distill → report):

- update the STATUS rows the phase touched, with evidence;
- update STATE.md: `updated`, `commit`, `phase`, "Resume here", "Gates passed", and any facts verified or failures opened or closed in the phase;
- append LESSONS entries for any failure that reached stage 4 in the phase;
- run `drive-lint --gate <phase>` and fix what it reports;
- commit to main with a message naming the phase and the rows.

At every stop, meaning the end of any turn where the model would return control, whether the run is finished or not:

- STATE.md "Resume here" describes the actual next action; `updated` is not older than the last commit that touched anything outside `.drive/`;
- `drive-lint --stop` passes: STATUS grammar clean, evidence pointers resolve, STATE fresh and under budget, working tree clean except `.drive/local/`, exactly one git worktree, no worker directories left in `.drive/local/workers/` without a merged report;
- if the stop is to ask the owner the one allowed question, "Blocked on:" names it, so that a blocked stop is itself recorded state.

Enforcement: a Stop hook declared in the skill's frontmatter runs `drive-lint --stop --hook`. On failure it emits the block JSON with a reason listing the exact fixes; the model fixes and tries to stop again. The hook does not short-circuit on `stop_hook_active`, because the checks are deterministic and cheap and the point is to re-check after the fix; the harness's cap of eight consecutive blocks is the safety net **[verified]**, and a hook that blocks eight times means the state is unrecoverable by the model, at which point stopping with a loud warning is the right outcome. The hook exits 0 immediately when `.drive/local/active` is absent, so it is inert in sessions where `/drive` is not running (skill hooks persist for the rest of the session once invoked **[verified]**).

The `/goal` set at intake asks for the same script's output, because the evaluator can only judge what appears in the transcript **[verified]**: "`drive-lint --final` exits 0 and its full output is shown in the conversation; `.drive/REPORT.md` exists and its counts match that output; or stop after N turns." The deterministic hook prevents stopping with stale state; the goal keeps the run going until the ladder is complete. They are complementary, not redundant.

#### Parallel workers: workers report, the orchestrator writes

No subagent ever edits STATE.md, STATUS.md, LESSONS.md, DECISIONS.md, or RESEARCH.md. There is no lock and there is no merge; there is one writer. Each worker's final message is a structured report in a fixed shape:

```
## Worker report · worker-2 · R-07, R-08
Claims touched: R-07 → Local Proof (test:…; severe:…), R-08 → Partial (test:…), commit: 8a1f2c0
Facts verified: <fact>. Verified: <how>.
Failures: F-09 <symptom>. Repro: <path>. Hypothesis: <…>
Candidate lessons: <rule>, taught by F-09 (not yet verified)
Left behind: nothing | <exact paths of scratch that should be deleted>
```

Long-running workers that may be interrupted write the same shape to `.drive/local/workers/<name>/report.md` as they go (their own file, so no contention) and the orchestrator merges from the file if the final message is partial (a subagent that hits `maxTurns` returns output marked partial **[verified]**). The verifier writes only its disposition file under `.drive/reviews/`; the orchestrator moves rows and cites the disposition. A worker that finds the state files wrong says so in its report; it does not fix them.

Subagent `memory:` is left off for all drive agents. It would create a second, machine-local memory store next to LESSONS.md and the skill's lessons file, which is the duplicated-truth anti-pattern applied to the skill itself. Section 8 records this as a trade-off.

#### Resume protocol

After compaction within a session: a `SessionStart` hook with matcher `compact`, also declared in the skill frontmatter, runs `drive-lint --start` and its stdout is added to context **[verified]**. The model then follows the read-at-start order. It trusts the files over the compaction summary: the harness post observed that compaction "doesn't always pass perfectly clear instructions to the next agent" **[verified]**, and a summary can carry a claim of completion that no row supports.

After a new session or `claude --resume <name>`: the skill named the session at intake (`/rename drive-<project>-<slug>`) and recorded the name in STATE.md, so the report can tell the owner exactly how to resume. The active goal is restored on every resume route with its turn count reset **[verified]**; background tasks are not, so "In flight" in STATE.md is the only record of workers that were running, and the first action after a resume is to reconcile it: check `.drive/local/workers/*/report.md`, check `git log` for their commits, and either re-dispatch or mark the rows back to their evidenced rung.

On the Pro/Max "resume from summary" dialog (offered after about an hour idle over 100k tokens **[verified]**): either choice is fine because the files are the truth; the skill's non-interactive path never sees the dialog.

#### Single source of truth

Precedence when two records disagree: working-tree code and tests, then proof bundles, then STATUS.md, then prose (STATE.md, SPEC.md, DESIGN-*.md, REPORT.md). The higher wins and the lower is corrected in the same turn. If the disagreement reveals a process failure (a row claimed Local Proof but the named test does not exist), that is a stage-1 failure and goes to STATE.md's open failures. The verifier checks STATUS against code, never code against STATUS. The report is generated from the files and may not state anything the lint would reject.

### 4.5 Size control

- STATE.md: warn at 120 lines, fail at 200 lines or 12 KB. Keep it under 150 by moving resolved failures out (they become LESSONS entries or nothing; git history keeps the story), deleting verified facts the code now makes obvious, and promoting general rules out of "Rules in force".
- STATUS.md: rows are never deleted, so it only grows. Reading is controlled by the `--start` view (open rows only). Split by area above about 150 rows, with STATUS.md as an index. Done rows stay; the report needs them.
- LESSONS.md: at most about 40 entries. The distill stage runs a consolidation pass: merge duplicates, generalize a cluster of near-duplicates into one rule, delete rules shown wrong, promote general ones and mark them promoted. This is the Fable prompting page's own guidance ("update an existing note rather than creating a duplicate; delete notes that turn out to be wrong") **[verified]**.
- HYPOTHESES.md: refuted rows stay (they prevent re-testing); when a hunt closes, the ledger's Confirmed row and the fix's STATUS row are the record and the rest may be trimmed to one line each.
- RESEARCH.md: sources are never deleted; findings superseded are marked superseded with the ID of the finding that replaced them.
- Consolidation cadence: at every phase gate (cheap: a minute of reading) and at the distill stage (thorough). Never during implementation turns; consolidation while context is full of code produces the "spurious generalizations" the paper warned about.

### 4.6 The lint: `drive-lint`

One script, Python 3 standard library only (macOS ships it), living at `~/Projects/drive/skill/scripts/drive-lint.py` and reached through the symlink `~/.claude/skills/drive/scripts/drive-lint.py`. It reads `.drive/` in the current repo and exits 0 or 1, printing one plain line per finding in the form `STATUS R-02: Live Proof without live: pointer`. With `--json` it prints a findings array; with `--hook` it reads the Stop hook's stdin JSON and prints the block decision on failure.

Modes:

- `--start`: prints the read-at-start view (STATE header and Resume here, rung counts, open rows, open failures, staleness) and exits 0 even with findings, listing them at the end.
- `--gate <phase>`: the phase's exit criteria, for example `--gate verify` requires every non-Dropped row at Local Proof or higher and every `Needs live: y` row at Live Proof or higher; `--gate spec` requires that every row has a refutable claim and a Needs-live value; `--gate tests` requires at least one `test:` planned per row (allowed to be a not-yet-existing path marked `planned:` at that gate only).
- `--stop`: write-before-walking-away: STATE fresh, STATUS clean, tree clean except `.drive/local/`, one worktree, no orphan worker reports.
- `--final`: everything `--stop` checks, plus every row Done or Dropped, `.drive/REPORT.md` exists, and the report's rung counts equal STATUS's.
- `--fix-dates`: the only writing mode; stamps `Updated` on rows whose status changed since HEAD and `updated:` in STATE.md. Everything else is read-only.

Checks, grouped:

STATUS.md
1. Header lines present; table parses; every row has an ID matching `^[A-Z]{1,4}-\d{2,3}$`, a non-empty claim, a Needs-live value of `y` or `n`, a status in the ladder or `Dropped`, and an `Updated` date not in the future.
2. Evidence tokens match the grammar; unknown token types fail.
3. Rung requirements from the table in 4.3: Partial needs `test:`; Local Proof needs `test:` and `severe:` (and `shot:` if the claim is tagged `[ui]`); Live Proof needs `live:`; Operational needs `ops:`; Done needs `review:` and, when Needs-live is `y`, `live:`; Dropped needs `why:`.
4. Every `test:` and `severe:` resolves: the file exists and the test name appears in it as a string (a cheap version of the owner's inventory check; language-aware parsing is not worth the dependency).
5. Every `commit:` exists (`git cat-file -e <sha>^{commit}`); every `proof:`, `live:`, `shot:`, `review:`, `doc:` path exists; every `proof.json` parses and has `requirement` equal to the row ID, `verdict`, `environment`, `commit`, `commands` non-empty, and `shim_differences` present (empty only with `shim_differences_note`).
6. `live:` bundles have `environment` of `live` or `device`; a `simulator` or `local` bundle under `live:` fails with the message "local-only work is never Live Proof".
7. Row retention: parse `git show HEAD:.drive/STATUS.md`; every ID present at HEAD must be present now. A row may change status downward (a demotion after review is the gate working) but not vanish.
8. Rows whose status differs from HEAD must have today's `Updated`.
9. Claim wording warnings: leading verbs that describe work ("Implement", "Add", "Create", "Set up", "Wire", "Refactor", "Build") produce a warning, not a failure, so a human can override with a deliberate wording.
10. Oracle concentration: if one `test:` reference is the sole evidence for more than five rows, warn (the owner's existing check, relaxed to a warning for small projects).

STATE.md
11. `updated:` parses as ISO 8601; `commit:` exists.
12. Staleness: let T be the author time of the most recent commit that touched any path outside `.drive/`; fail in `--stop` and `--final` if `updated` < T. Also fail if `commit:` is not an ancestor of HEAD or HEAD has moved by more than one commit since it without `updated` moving.
13. Budget: warn at 120 lines, fail at 200 lines or 12 KB.
14. `Next action:` non-empty; `Blocked on:` present.
15. Every Verified-facts bullet contains `Verified:`; every Open-failure bullet has an `F-nn` ID, a date, and `Repro:` or `Observed:`.
16. Secret shapes (`sk-`, `AKIA`, `ghp_`, `-----BEGIN`, `Bearer ` followed by a long token) anywhere in `.drive/` outside `local/` fail hard.

LESSONS.md
17. Every entry has `Rule:`, `Because:`, `Taught by:`, `Scope:`; warn if `Rule:` contains a path, a line number, or a 7-plus hex run.
18. `Promoted:` entries must point at an existing anchor in the skill's lessons file (checked when that file is reachable).

Repository hygiene (in `--stop` and `--final`)
19. `git status --porcelain` empty ignoring `.drive/local/`.
20. `git worktree list` has one entry.
21. No `.drive/local/workers/*/report.md` newer than STATE.md's `updated` (an unmerged worker report).

The Stop hook wiring, in SKILL.md frontmatter:

```yaml
hooks:
  Stop:
    - hooks:
        - type: command
          command: "python3 ~/.claude/skills/drive/scripts/drive-lint.py --stop --hook"
          timeout: 60
  SessionStart:
    - matcher: compact
      hooks:
        - type: command
          command: "python3 ~/.claude/skills/drive/scripts/drive-lint.py --start"
          timeout: 30
```

The absolute path through the symlink avoids depending on `${CLAUDE_SKILL_DIR}` substitution inside frontmatter hooks, which I could not verify (section 8). The `--hook` mode exits 0 at once when `.drive/local/active` does not exist, so an unrelated session that happened to invoke `/drive` earlier is not gated after the run ends; the report stage deletes the marker.

A script in the skill, not in the repo: one copy, versioned with the skill, and the report tells the owner the command to run. The repo carries the data, not the checker. When a repo has its own gate (Arcwell), the skill's lint runs that gate in `--stop` and `--final` instead of parsing STATUS.md, configured by a single line in STATE.md's header: `registry: pnpm verify:requirements`.

### 4.7 Cross-project memory

What leaves the project: LESSONS entries with `Scope: general`, and process lessons about the skill itself (a phase that was skipped, a template that misled, a check the lint should have had). Both go to the skill's own lessons file, `~/Projects/drive/skill/references/lessons.md`, committed in the skill's repo, in the same entry format plus `From: <project> <date>` and `Shapes:`. When a process lesson is a rule about the procedure, the distill stage edits SKILL.md itself in the same commit, and prunes as much as it adds; the Fable prompting page's warning about over-prescriptive skills applies **[verified]**.

What stays: every project fact, every requirement row, every decision, every hypothesis, every proof. The owner's working preferences (no queues, plain language, no worktrees left behind) already live in `~/.claude/CLAUDE.md` and his auto memory; the skill reads them there and does not copy them.

Auto memory: the harness will keep saving `feedback` and `user` notes on its own, which is fine and useful. The skill does not write project state or lessons into auto memory: it is machine-local, not committed, capped at 200 lines of index, and would be a second truth. The one exception is a `reference` note pointing at `.drive/` so a session that starts without `/drive` knows the state exists.

How the skill reads its own lessons: the lessons file mirrors MEMORY.md's shape because the harness's own limits taught the lesson: an index of one line per entry at the top (under 200 lines), full entries below. At intake the skill reads the index and the entries whose `Shapes:` include the current shape or `all`. Lessons are promoted only after stage 3 (verified); a guess never crosses the project boundary. At the close of every run the distill stage consolidates the skill's lessons file the same way as LESSONS.md.

### 4.8 The final report

`.drive/REPORT.md` is derived from the files, not from the model's memory of the run. The orchestrator writes it at the report stage after `drive-lint --final` passes on everything except the report's own existence; `drive-lint --final` then checks the report's counts against STATUS.md. Shape:

1. **Outcome** in one paragraph: what was asked, what is true now, at which commit, and how to resume (session name, `claude --resume <name>`, the state directory). Written as a re-grounding for a reader who saw none of the work, in the Fable prompting page's sense **[verified]**.
2. **Ladder summary**: counts per rung, then the STATUS table rendered verbatim (or per-area tables), each evidence pointer a link.
3. **Proven live versus proven locally**: the rows at Live Proof and above; the rows with Needs-live `y` that did not reach it and why; the union of `shim_differences` from all proof bundles, so the owner sees in one place every way the local harness is kinder than production.
4. **Open failures and dropped rows**, each with its reason and the exact command or observation that would close it, in the owner's Observed / Inferred / Unverified idiom.
5. **Decisions made on his behalf**, from DECISIONS.md, each with its undo line.
6. **The one question**, if any, as a single choice with the default that applies if he does not answer.
7. **Lessons distilled**, with which were promoted and where.
8. **Cost and time** if the harness exposed them.

Rules: every claim in the report cites a row, a file, or a proof; nothing is stated as done that the lint would reject; plain language, full sentences, no rule IDs without their meaning (a row is referred to as "the expired-token rejection (R-01)", not "R-01"); no narration of the process ("first I..."), which is what git log is for.

---

## 5. Conditionals by project shape

The principle: every file must earn its place per shape, and "live" must be defined per project at intake and written into STATE.md's header, because the ladder's upper rungs mean nothing until the skill knows what the real environment is.

**Greenfield app (Cloudflare backend, Swift iOS front end).** The full set: STATE, STATUS (split by area if it passes about 150 rows; `Needs live: y` for every row that touches the Worker, D1, or the device), LESSONS, DECISIONS, RESEARCH, SPEC, DESIGN-backend, DESIGN-frontend, TESTPLAN, proof bundles with screenshots, review dispositions. "Live means here": the deployed Worker on its workers.dev host plus the app on the named simulator talking to that host; device proof if a device is available. UI rows are tagged `[ui]` and need a `shot:` at Local Proof; the vision verifier's disposition is the `review:` for those rows. This is the only shape where a STATUS split is expected.

**Deep bug hunt in an existing codebase.** STATE (the repro pointer lives in "Resume here"), HYPOTHESES, LESSONS, and a STATUS of two or three rows: "the bug reproduces on demand" (Local Proof with the repro script as evidence), "the root cause is confirmed" (evidence: the Confirmed hypothesis row), and "the fix holds and a regression test tries to refute it" (Local Proof, Live Proof if the bug was live). No SPEC, DESIGN, or DECISIONS unless the fix changes an interface, in which case one DECISIONS entry. RESEARCH only if the hunt needed external documentation, and then a light one. The lint runs with `--shape bughunt`, which relaxes the STATUS row minimum and requires HYPOTHESES.md to have a Confirmed row before the fix row may pass Partial.

**Feature on an existing product.** STATE, STATUS rows for the feature only, LESSONS, DECISIONS for integration choices, a short SPEC; DESIGN only if a new surface is introduced; TESTPLAN folded into STATUS rows. If the repo already has a requirement registry or status ladder, STATUS.md is a pointer file and the lint runs the repo's gate. "Live means here" is inherited from the product's existing deployment.

**Migration or consolidation.** STATE, STATUS with parity rows (one row per behavior of the old system that must survive: "requests with header X are routed to provider Y as before", evidence old-versus-new comparison proofs), DECISIONS (heavy: every divergence from the old behavior is a decision with an undo), LESSONS, and cutover rows in STATUS (shadow traffic, cutover, decommission) that are `Needs live: y` without exception. RESEARCH if the target platform is unfamiliar. The report's "proven live versus locally" section is the cutover decision record.

**Research plus website.** RESEARCH.md is the primary artifact; STATUS rows are the site's behavioral claims (each section exists and renders, blog and docs sections build, design quality verified by screenshot review); DESIGN-frontend; the deliverable content goes to the site's content directory, not `.drive/`; REPORT.md carries the research findings with sources. "Live means here" is the deployed site.

**Pure research report.** RESEARCH and REPORT, a minimal STATE (resume pointer and open questions), one STATUS row ("the report answers Q1..Qn with cited sources", evidence `doc:` and `review:` from an adversarial read). No LESSONS unless the research process itself taught one.

**Refactor or simplification.** STATUS rows are behavior-preservation claims (the existing suite is unchanged and green; measured performance is within tolerance; public interfaces unchanged), evidence the before-and-after test runs as proofs. Small; no SPEC.

**Ops or incident.** HYPOTHESES (the incident timeline goes in its header), STATE, LESSONS (the post-mortem's rules), STATUS rows for recovery and for prevention, both `Needs live: y`. The owner's "never wait on a scheduler" rule applies to recovery rows: evidence must show the recovery was driven, not scheduled.

**Data pipeline.** STATUS rows include data-quality invariants ("no duplicate keys after the merge step", "row counts reconcile within N"), evidence proofs against real data samples with counts in `proof.json`. "Live" means the real source and sink.

**CLI tool or library.** Mostly Local Proof; "live" means installed from a clean environment (fresh virtualenv, `npx` from the published tarball, a clean clone) and exercised, recorded as a `live:` bundle with `environment: live` and the clean-install commands.

---

## 6. Model and effort assignment

State-file maintenance is orchestrator work. Deciding what is true, what a row's rung should be, and what the next action is are judgment calls that sit with the orchestrator on Fable 5, and the files must have one writer. No subagent is needed for writing them, and none should exist: a "state keeper" agent would be a second writer.

Two roles in this component do benefit from a fresh context and can be delegated:

**The distiller** (stage 4). Generalizing correctly is the hardest step; Martin's observation was that Opus 4.7 tended to stop at verify while Fable 5 completed distill **[source claim, small experiment]**. A fresh context also helps: a distiller that did not live through the session's narrative is less anchored to the specific fix. Run it on Fable at high effort for greenfield and migration shapes, Opus at xhigh for smaller shapes. It reads only files and git and returns candidate LESSONS entries with promotion recommendations; the orchestrator writes. Draft, for `~/.claude/agents/drive-distiller.md`:

```markdown
---
name: drive-distiller
description: Reads a finished drive phase's state files, review dispositions, and git history and returns general rules distilled from verified failures. Use at the distill stage; never during implementation.
model: fable
effort: high
tools: Read, Grep, Glob, Bash
disallowedTools: Edit, Write, NotebookEdit
maxTurns: 40
---
You turn verified failures into rules. You do not write files; you return text the orchestrator will write.

Read `.drive/STATE.md`, `.drive/LESSONS.md`, `.drive/HYPOTHESES.md` if present, every file under `.drive/reviews/`, and `git log --stat` since the commit named in STATE.md's header. Then, for every failure that reached verification (it has a test, a proof, or a Confirmed hypothesis), decide whether it teaches a rule that applies beyond this case.

A rule says when, what, and why in one or two sentences and names the failure that taught it. A rule never contains a file path, a line number, or a commit hash; if you cannot state it without those, it is a fix, and fixes stay in git history. Say which existing LESSONS entries a new rule duplicates or supersedes, and which entries the evidence now shows to be wrong. Mark each rule `Scope: general` only if it would have helped in a different repository; otherwise `project`.

Do not propose a rule from a failure that was never verified. Do not restate what the code or the tests already record. Return at most eight entries; fewer, better-argued rules are worth more than a list.
```

**The status grader** (a cheap pre-check the verifier can call). Before the adversarial verifier spends effort, a Sonnet agent at low effort reads STATUS.md and each row's named tests and answers, per row, one classification: "the claim is behavioral and the named test could refute it", "the claim describes work, not behavior", or "the named test cannot fail for the claim as stated" (it asserts something else, or nothing). This is a classifier task, and the owner wants Sonnet at low effort for classifiers rather than Haiku. It writes nothing; its output feeds the verifier's disposition. It can be an inline `Agent` call with `model: sonnet` rather than a predefined agent.

The lint itself has no model; it is a script. The report is written by the orchestrator (Fable), because the owner reads it and its quality is the last thing he sees; a Sonnet draft would need a Fable rewrite anyway.

Effort for the orchestrator's own state writes: routine STATE updates at every stop do not need deliberation and should not trigger it; the Fable prompting page notes that at high effort Fable "can gather context and deliberate beyond what the task needs" on routine work **[verified]**. The skill text should say so plainly: update the files, run the lint, commit; do not re-read the whole ladder to write a resume pointer.

---

## 7. Failure modes and anti-patterns

How this component manufactures mirage completion, and what stops it:

- **Intent recorded as done.** "Fix drafted", "implemented", "wired up" in a status column. The ladder has no such rungs; the lint rejects any status outside the vocabulary and demands evidence per rung. The claim-wording warning catches rows that describe work.
- **A test that cannot fail.** A row cites a test that asserts nothing about the claim, or asserts something weaker. The lint checks existence, not strength; the status grader and the adversarial verifier check strength; the Local Proof rung requires a second, refuting test. The owner's own rule (a proof must claim what it proves) is the model, and his citation check (`@req:` in the test body) is worth adopting when the repo's test style allows a comment tag.
- **Live Proof against a kinder harness.** The D1 incident. The lint refuses Live Proof from a `local` or `simulator` bundle and forces every bundle to answer where its harness is kinder than production. The report aggregates those answers so the owner sees them.
- **Duplicated truth.** STATUS.md next to a repo's own registry; a fact repeated in STATE.md and SPEC.md; lessons in LESSONS.md and in auto memory and in a subagent's memory directory. Rule: one writer, one place per kind of fact, precedence when they disagree, and the skill defers to an existing registry.
- **Stale resume pointer.** The most common way a run restarts instead of resuming. The Stop hook makes it impossible to end a turn with `updated` older than the last code commit; the `--start` view prints the pointer so a fresh context sees it before anything else.
- **Compaction summary as truth.** The summary says "all tests pass"; STATUS says three rows are Partial. The read-at-start order puts files before the summary, and the SessionStart compact hook re-injects the lint view.
- **Lessons that are fixes.** "Change line 42 of foo.ts to chunk at 90." The lint warns on paths and hashes in Rule lines; the distiller is told the difference; promotion requires a verified `Taught by:`.
- **Lessons never consulted.** Stage 5 is the one the post's own numbers say models skip. The read-at-start procedure reads LESSONS.md and the skill's lessons index every time, and the `Shapes:` tag keeps the read small enough to happen.
- **Memory that grows beliefs.** The CL-Bench finding. Facts need `Verified:`, rules need `Taught by:`, findings need sources and confidence, and consolidation deletes what turned out wrong. Nothing enters the files at stage 1 except as an explicitly labelled open failure or hypothesis.
- **Concurrent edits.** Two workers append to STATUS.md and one clobbers the other. Workers do not write shared files; they report; the orchestrator writes.
- **Deleted rows.** A requirement quietly disappears when it gets hard. The retention check compares against HEAD; a row may be Dropped with a reason, never removed. The harness post's finding that models corrupt Markdown more readily than JSON is the reason this check exists at all.
- **The goal evaluator fooled by a claimed lint pass.** The model writes "lint passes" without running it. The goal condition asks for the full output in the transcript, and the Stop hook runs the script regardless of what the transcript says.
- **The hook that never lets go.** A lint check that cannot be satisfied (a proof path on another machine) blocks eight times and the harness overrides with a warning. Acceptable as a last resort; better, the `--stop` mode marks unreachable evidence as a finding with an exact fix ("mark R-05 back to Partial or restore the bundle") so the model can always reach a passing state honestly.
- **State bloat.** STATE.md becomes a diary; nobody reads it. Budgets, the "nothing git already says" rule, and the consolidation pass. The harness's own 200-line index limit for MEMORY.md is the precedent.
- **Secrets in committed state.** A live proof's command line contains a token. The lint fails hard on secret shapes anywhere outside `.drive/local/`, and the proof.json convention writes `<redacted>` placeholders.
- **Asking instead of recording.** The model ends a turn with "Shall I continue?" The Fable prompting page documents this early-stopping failure **[verified]**. The Stop hook passes only if STATE.md records either a next action or a real "Blocked on", so a rhetorical question without state is blocked with the reason "record the next action or the blocker, then continue".

---

## 8. Open questions and trade-offs

1. **STATUS.md as a Markdown table versus a `status.yaml` source of truth.** YAML is easier to parse and extend (lists of evidence, notes per row) and Anthropic found JSON harder for the model to corrupt. Markdown renders in the report and on GitHub and is what the owner calls it. Recommendation: Markdown table with the strict grammar and the row-retention check, because one file beats two and the retention check substitutes for JSON's robustness. Revisit if the lint's parser proves brittle in practice; switching later is a one-time conversion.
2. **Commit proof bundles or not.** Committing screenshots and manifests makes evidence travel with the repo and lets the lint resolve pointers on a fresh clone; it also grows the repo and risks "stray artifacts committed", which the owner dislikes. Recommendation: commit manifests and small screenshots (≤200 KB), gitignore logs above a cap, record hashes for everything. Alternative: keep bundles entirely in `.drive/local/` and let the lint downgrade unresolvable Live Proof to a warning on a fresh clone. I prefer the first; evidence that cannot be found is not evidence.
3. **`${CLAUDE_SKILL_DIR}` inside frontmatter `hooks:` commands.** The brief confirms the variable substitutes in the skill body; I could not verify it substitutes inside hook command strings. The absolute symlink path sidesteps this. Test once during skill build; if substitution works, prefer it.
4. **Subagent `memory:` for the verifier.** A verifier that remembers recurring failure patterns across projects is attractive, and the harness supports it. It is also a second cross-project memory next to the skill's lessons file, machine-local and uncommitted. Recommendation: off. If the owner later wants it, make the skill's lessons file the verifier's memory directory by symlink rather than a separate store.
5. **Whether Done should require `doc:`.** Requiring it makes docs part of completion, matching the owner's culture; it also adds a pointer for every row on shapes with no docs (bug hunt). Recommendation: require it only for rows tagged `[user-facing]`, set at spec time.
6. **Skill hooks persisting for the session after the run ends.** Verified behavior. The active-marker check makes the hook inert, but the hook still executes on every stop in that session. Cost is a few milliseconds of Python; acceptable. The cleaner alternative is registering hooks in the project's `.claude/settings.local.json` for the run and removing them at report time; that leaves a file to clean up, which is the kind of stray state the owner dislikes.
7. **The `/goal` model.** The evaluator defaults to Haiku, which the owner does not trust in a general skill. `ANTHROPIC_DEFAULT_HAIKU_MODEL` can point it at Sonnet, but the variable also redirects every background small-model task **[verified]**. Recommendation: leave the default and rely on the deterministic Stop hook as the gate that matters; the goal's job is to keep the run going, and its condition is a script's exit code, which Haiku can read.
8. **Repos with an existing registry.** The Arcwell case: the repo's own gate is stricter than the skill's lint. The skill should defer, but the mapping from the repo's status vocabulary (`planned | implemented | live-only`) to the ladder is not one to one. Recommendation: STATE.md declares `registry:` and the lint calls that command; the report shows the repo's summary line rather than a ladder count. Do not attempt a translation table; it would be a second truth.
9. **How much of this the bug-hunt shape really needs.** Three STATUS rows plus a hypothesis ledger is small, but it is still four files for a task the owner might describe in one sentence. The alternative is HYPOTHESES.md alone with the fix row inside it. Recommendation: keep the three rows; the anti-mirage rule (a fix with a refuting test, live if the bug was live) is the whole point of the skill, and three rows is not ceremony.

---

## 9. Skill text candidates

Plain language, imperative voice, ready to lift into SKILL.md or `references/state-files.md`.

1. **What survives.** Nothing you know survives compaction, the end of the session, or a subagent boundary unless it is in code, tests, git, or the files under `.drive/`. Treat every turn as if the context could reset at its end, because it can.

2. **Read at start.** Before anything else, run `python3 ~/.claude/skills/drive/scripts/drive-lint.py --start` and read what it prints. Then read `.drive/STATE.md` in full, `.drive/LESSONS.md`, and the entries in this skill's `references/lessons.md` tagged with the current project shape. Open STATUS rows, the spec, and the designs only when the current phase needs them. Do not read proof bundles at start.

3. **One writer.** Only you, the orchestrator, edit STATE.md, STATUS.md, LESSONS.md, DECISIONS.md, and RESEARCH.md. Workers and verifiers report in the fixed report shape; you write. If a worker believes a state file is wrong, it says so in its report and does not fix it.

4. **Nothing git already says.** Do not write into the state files anything the code, the tests, or the git log already records. STATE.md holds the next action, the facts you had to check, the project rules in force, and the open failures. That is all.

5. **A fact names its check.** Every line under Verified facts ends with how it was verified and when. A fact you cannot check is a hypothesis; write it under Open failures with a repro, or do not write it.

6. **Claims, not tasks.** Every STATUS row is a behavioral claim a test could refute, named before the code is written. "An expired token is rejected with 401" is a claim. "Implement token expiry" is a task and does not belong in the table.

7. **Evidence per rung.** Partial needs a passing test. Local Proof needs that test and a second one that tried to refute the claim. Live Proof needs a proof bundle produced against the real environment named in STATE.md's "live means here" line. Done needs the adversarial review's disposition and, when the row needs live, the live bundle. Move a row only when its evidence exists; the lint will refuse otherwise.

8. **Where is the harness kinder?** Every proof bundle answers, in its `shim_differences` field, where the test harness is more permissive than production. A local bundle is never Live Proof, whatever it proves. A green run against an emulator that enforces fewer limits than the real service certifies nothing about the real service.

9. **Rows never disappear.** A requirement that turns out to be wrong or out of scope becomes Dropped with a reason in the same row. Never delete a row. The lint compares against the last commit and fails if one is missing.

10. **Write before you stop.** Before ending any turn, update STATE.md's "Resume here" so a fresh context knows the next action, set `updated` and `commit`, run the lint's `--stop` mode, and commit. If you are stopping to ask the owner the one question a run may ask, record it under "Blocked on" first. A Stop hook runs the same lint and will not let the turn end with stale state.

11. **Define live at intake.** Write one line in STATE.md's header saying what "live" means for this project: the deployed host, the device or simulator and what it talks to, the clean environment a CLI must install into. Mark each STATUS row with whether local proof can ever be enough for it. Do this before any code exists; the upper rungs mean nothing without it.

12. **Lessons are rules.** A lesson says when, what, and why, and names the verified failure that taught it. If you cannot state it without a file path, a line number, or a commit hash, it is a fix, not a lesson, and it stays in git. Promote a lesson out of the project only if it would have helped in a different repository and only after its failure was verified. Update an existing entry rather than adding a near-duplicate; delete entries the evidence has shown to be wrong.

13. **Files over summaries.** After compaction or a resume, trust the state files over the conversation summary. If the summary says something is done and STATUS does not, STATUS is right until you have re-checked against the code. When code, proofs, STATUS, and prose disagree, the earlier in that list wins and you correct the later one in the same turn.

14. **Reconcile in-flight work after a resume.** Background workers do not survive a resume. Read "In flight" in STATE.md, check each worker's report file under `.drive/local/workers/` and its commits in `git log`, then either re-dispatch the work or move its rows back to the rung their evidence supports.

15. **Defer to an existing registry.** If the repository already has a requirement registry or status ladder with its own gate, do not create a second one. Write `registry: <command>` in STATE.md's header, keep STATUS.md as a pointer, and let the lint run the repository's gate.

16. **Keep STATE.md small.** Under 150 lines. At every phase gate, move resolved failures out, delete facts the code now makes obvious, and promote general rules to LESSONS.md. If the file needs to grow past that to hold what you know, you are writing things git already records.

17. **The report comes from the files.** Write `.drive/REPORT.md` from STATE.md, STATUS.md, LESSONS.md, and DECISIONS.md, not from memory of the run. Open with the outcome and how to resume, then the ladder with its evidence, then what is proven live versus only locally and every way the local harness was kinder than production, then open failures with the exact command that would close each, then decisions taken with their undo, then the one question if there is one. State nothing the lint would reject.

18. **Routine writes are routine.** Updating the resume pointer, stamping a date, running the lint, and committing do not need deliberation. Do them and continue. Save the thinking for the distill stage, where a fresh-context distiller reads the verified failures and proposes rules, and you decide what to keep.
