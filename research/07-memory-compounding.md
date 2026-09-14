# R07 — Memory and compounding: STATE.md, STATUS.md, learnings, skills that sharpen

Lane: memory & compounding (post steps 02, 03 layers 3–4, 10, 11, 12).

## 1. Executive summary & strong opinions

The post's memory layer is directionally right: the model is stateless and the harness around it compounds. But its
evidence is thinner than it sounds. The "5-stage progression" is one Anthropic engineer's framing of *one* SQL task from
a Berkeley benchmark, and that benchmark's own paper finds that "dedicated memory systems do not fix" poor knowledge
reuse (https://arxiv.org/abs/2606.05661). Memory compounds only when three things are true: writes are **gated by
evidence**, reads are **forced by the harness** rather than hoped for, and the store is **pruned** so loading it stays
cheap. The skill should ship those three things as templates, hooks and a curator pass, not as prose telling the
model to "remember".

Verdicts (each actionable):

1. **One `.mission/` directory, git-tracked, one file per kind of fact.** `STATE.md` (knowledge: verified facts, rules,
   open failures, resume pointer), `STATUS.md` (work: board and goal progress), `DECISIONS.md` (append-only ADR-lite),
   `RESEARCH.md` (sources and findings), `LESSONS-INBOX.md` (candidates for promotion to a skill). Nothing is stored in
   two places. A fact that shows up in a second file is a bug the curator removes.
2. **No "verified fact" without the command or artifact that verified it, a date and a scope.** Lance Martin's data is
   really a verification-coverage story: Opus 4.7 flagged uncertainty but verified only 7–33%. The template field
   `Evidence:` is what forces stage 3. A fact without evidence goes under *Hypotheses*, not *Verified facts*.
3. **No "general rule" without ≥1 linked verified instance and an explicit `Applies when:` scope.** A rule with no
   instance is a guess written in rule syntax, and unscoped rules are how memory quietly starts to mislead.
4. **Stage enforcement belongs in the templates and a validator script, not in instructions.** Martin reports that
   Sonnet 4.6 "rarely consults prior notes" and that "task-specific memory instructions are needed". Most of the fan-out
   workers will be Sonnet 4.6, so the structure has to carry the discipline.
5. **Reads are harness-forced: a `SessionStart` hook (matchers `startup|resume|compact`) prints the resume pointer and
   the rules index into context.** CLAUDE.md is "a request, not a guarantee"
   (https://academy.claude.com/courses/claude-code-in-action/hooks). After compaction, re-inject with SessionStart
   `compact`, not PostCompact.
6. **Writes are harness-checked: a `Stop` hook blocks the end of a mission turn when STATUS.md or STATE.md's
   `Last session` is stale, and it respects `stop_hook_active`.** Claude Code overrides a Stop hook after 8 consecutive
   blocks (https://code.claude.com/docs/en/best-practices), so the check has to be quick and specific.
7. **Only the orchestrator writes STATE.md. Workers return findings, and the orchestrator merges them as itemized
   deltas.** Letting a model rewrite the whole file produces "context collapse, where iterative rewriting erodes details
   over time" (https://arxiv.org/html/2510.04618v1). Edits are line-level add/modify/supersede, never a whole-file
   regenerate.
8. **Hard size budgets with a curator pass when they're exceeded.** STATE.md ≤ 150 lines / ~12 KB loaded, STATUS.md
   ≤ 100 lines, the inbox ≤ 30 entries. Beyond that, archive to `.mission/archive/` and keep an index line. Claude Code
   applies the same logic to its own auto memory: only the first 200 lines / 25 KB load
   (https://code.claude.com/docs/en/memory).
9. **Supersede, don't delete, then archive.** Superseded facts move to `archive/state-YYYY-MM.md` with a pointer to what
   replaced them. Contradictions are flagged under `Open failures` as `CONTRADICTION` and must be resolved by
   re-verification, not by picking one ("Claude may pick one arbitrarily", memory docs).
10. **Skills compound through an inbox with a verifier gate, never by writing straight into the skill after every
    failure.** Anthropic's own `/verify` skill used to "fold in anything a run learned, which caused frequent merge
    conflicts". It now edits its recipe "only when it steered a run wrong" (https://code.claude.com/docs/en/skills).
    Copy that rule.
11. **Promotion criteria for a skill lesson: seen in ≥2 missions or projects (or 1 costly incident), a project-agnostic
    phrasing, a reproducible eval case, and an independent verifier pass.** Distillation runs on Opus 4.8 (Fable 5.1 only for XL cross-mission retros); verification runs on a separate Sonnet 4.6 high-effort context with no access to the distiller's
    reasoning.
12. **Every promoted lesson ships with an eval case** (`evals/evals.json` in skill-creator format, run with-skill vs
    baseline). A lesson that can't be expressed as a test case goes to `references/lessons.md` marked `advisory`, capped
    at 40 entries.
13. **CLAUDE.md is not mission memory.** It holds build commands and durable conventions for *every* session. The
    mission only proposes CLAUDE.md edits for rules that were violated twice (the docs' own trigger: "Claude makes the
    same mistake a second time").
14. **Degrade gracefully by storage backend.** In Claude Code the store is `.mission/` files plus hooks. In CMA it's a
    memory store with many small files (the docs recommend exactly that, capped at 100 kB each). With the API memory
    tool it's `/memories/`. With no hooks, the same protocol runs as the first and last steps of the orchestrator
    prompt, checked by the final verifier.
15. **Don't build memory for S-scope tasks.** A one-hour bug fix writes one lesson candidate at most and the
    STATUS/STATE sections go into the PR description. Memory scaffolding for tiny tasks is process bloat, and the
    token cost of loading it shows up in every later session.

## 2. Claim check

| # | Post claim (brief line) | Verdict | Evidence | What the skill should do |
|---|---|---|---|---|
| C1 | "Self-improving is not self-learning": weights are not updated, the environment compounds (step 02, lines 104–117) | **Verified in substance** | Context adaptation without weight updates is an established, measured paradigm: ACE gets +10.6% on agents from "evolving playbooks" (https://arxiv.org/html/2510.04618v1). The CMA, memory-tool and Claude Code memory docs all describe file-based memory, not training | Frame the skill as "sharpen the environment": files, hooks, skills, evals. Never promise learning. |
| C2 | Quote "Rather than directly prompting and steering Fable 5, it's often better to design loops … manage its own context (e.g., via memory)" attributed to "Anthropic's engineering team" (lines 115–117) | **Verified quote, loose attribution** | It appears verbatim in Lance Martin's X article "Designing loops with Fable 5", 2026-06-09 (https://x.com/RLanceMartin/article/2064380553919676416, full text mirrored at https://github.com/lchesupercool/ob-clippings/blob/main/2026-06/2026-06-10-designing-loops-with-fable-5.md). It is an Anthropic engineer's personal article, not an engineering-blog post | Cite it as guidance, not doctrine. |
| C3 | 5-stage progression "from Anthropic's Continual Learning Bench 1.0" (line 216) | **Partly wrong** | CL-Bench comes from Asawa, Zaharia, Gonzalez et al. (Berkeley Sky lab), https://arxiv.org/abs/2606.05661 and https://sky.cs.berkeley.edu/project/continual-learning-bench/. The fail→investigate→verify→distill→consult framing is Martin's, and he scopes it: "For this task, effective use of memory benefits from a progression" | Use the five stages as the *lesson lifecycle schema*. That is a design choice, not a benchmark finding. |
| C4 | Sonnet 4.6 exits at step 1 and rarely consults prior notes; Opus 4.7 at step 3 with 7–33% coverage (median ~17%); Fable 5 completes, with 73% in its strongest runs (lines 222–224) | **Verified as reported, weak evidence** | The numbers match Martin's article. It was one task, 30 questions, "strongest runs" (cherry-picked upper bound), and he calls them "a few small scale experiments". The post leaves out his key line: "To improve performance, task-specific memory instructions are needed" | Don't route memory work to Fable 5.1 on the strength of this. Ship task-specific memory instructions and templates so Sonnet/Opus workers produce stage-3 evidence. |
| C5 | A separate claim by implication: dedicated memory makes agents improve | **Contradicted by the benchmark authors** | CL-Bench abstract: "dedicated memory systems do not fix this -- in fact, naive ICL outperforms systems dedicated to memory management" | Keep memory simple and plain-text, loaded in context (ICL-style). No vector DB or memory service by default. |
| C6 | "In CMA memory is a mounted filesystem surviving between sessions" (line 227) | **Verified** | "When you attach a store to a session, it is mounted as a directory inside the session's sandbox"; each change creates an immutable version; 100 kB per memory; "many small focused files" (https://platform.claude.com/docs/en/managed-agents/memory) | CMA adapter: split `.mission/` into small files, attach with `instructions` telling the agent to read `STATE.md` first. |
| C7 | "In Claude Code locally, a markdown file or Linear board" (line 227) | **Incomplete** | Claude Code ships CLAUDE.md hierarchy + auto memory (MEMORY.md index, first 200 lines/25 KB) + subagent memory (https://code.claude.com/docs/en/memory) | Use `.mission/` for mission state. Leave auto memory on but don't rely on it for mission facts: it lives outside the repo by default (https://archcore.ai/blog/claude-code-memory/) and isn't reviewable. |
| C8 | The STATE.md example (lines 229–244) | **Useful but flawed as a template** | "General rules" and "Lessons learned" are both labelled stage 4, a duplicate kind. "Confirmed 2026-06-09" gives no evidence. No scope, no expiry, no IDs for supersession | Ship the corrected template in §7: IDs, evidence, scope, dates, confidence, supersedes. |
| C9 | "Write before walking away" / "Read at session start" (lines 245–247) | **Sound practice; the rationale is unverified** | The memory tool docs say Claude "automatically checks its memory directory before starting a task" when the tool is enabled (https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool). "Sonnet-class memory behaviour shows up even in Fable 5" without reading first has no source | Enforce with SessionStart + Stop hooks (§7). Don't rely on model habit. |
| C10 | "After any non-trivial failure, write the lesson into the Skill itself" (line 250) | **Likely harmful as stated** | Anthropic reversed exactly this in `/verify`: folding in everything "caused frequent merge conflicts", so it now edits "only when it steered a run wrong" (https://code.claude.com/docs/en/skills). ACE documents collapse from monolithic rewrites | Inbox → distill → verify → eval → promote (§4, §7). |
| C11 | "Skills live in ~/.claude/skills/ and travel with you" (line 257) | **Partly true** | Personal skills load in "All your projects on this machine, but not Cowork or cloud sessions" (https://code.claude.com/docs/en/skills) | For cloud runs (Routines/CMA), ship the skill in the repo `.claude/skills/` or as a plugin. Lessons file must sync. |
| C12 | Eval suite in the skill: newly failing case → known failure modes after a verifier confirms (line 255) | **Plausible, matches Anthropic tooling** | skill-creator uses `evals/evals.json` and runs with-skill vs baseline (https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/plugins/skill-creator/skills/skill-creator/SKILL.md) | Adopt the skill-creator eval format for lesson promotion. |
| C13 | Routine: "Any test that newly passes → distill the pattern into the skill" (line 211) | **Likely hype / wrong direction** | A newly passing test says nothing causal about the skill (the inference is mine; there is no source either way) | Promote only from *investigated* failures with a verified root cause. Newly passing cases just update the eval baseline. |
| C14 | Layer 4 "grades its own output, refines the Skill" (line 127) | **Self-grading contradicts the post's own step 06** | Martin: "a verifier sub-agent tends to outperform self-critique … because grading is done in an independent context window" | The promotion verifier must be a different context from the distiller. |

## 3. Deep findings

### 3.1 The memory surfaces that actually exist, and what each is for

- **Claude Code CLAUDE.md hierarchy.** Managed policy → `~/.claude/CLAUDE.md` → `./CLAUDE.md` or `./.claude/CLAUDE.md`
  → `./CLAUDE.local.md`. All load at launch; subdirectory files load on demand. It is "context, not enforced
  configuration". Target is under 200 lines, and "If an entry is a multi-step procedure or only matters for one part of
  the codebase, move it to a skill or a path-scoped rule" (https://code.claude.com/docs/en/memory). Right home for:
  build/test commands and conventions every session needs. Wrong home for: mission progress, hypotheses, dated facts.
- **Auto memory.** Claude writes it; it's per repository and shared across worktrees; the first 200 lines or 25 KB load
  every session (same URL). Third-party analysis says it's a `MEMORY.md` index plus topic files read on demand, stored by
  default under `~/.claude/projects/<project>/memory/`, and that truncation used to be silent
  (https://archcore.ai/blog/claude-code-memory/; version details unverified). Implication: it's a personal preference
  store, not a team-reviewable mission record. The skill should neither disable nor depend on it.
- **Subagent persistent memory.** Subagents "can also maintain their own auto memory" (memory docs). Third-party sources
  say `memory: project` writes to `.claude/agent-memory/<name>/`, which can be committed. Useful for recurring
  specialist roles (e.g., the flake investigator), but it splits knowledge across stores, so the skill should route
  durable facts back to `.mission/STATE.md` through the orchestrator.
- **Skills.** Only name + description preload; the body loads when used; keep SKILL.md under 500 lines
  (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). "Create a skill when … a section of
  CLAUDE.md has grown into a procedure rather than a fact" (https://code.claude.com/docs/en/skills). Personal skills don't
  load in cloud sessions (same URL).
- **API memory tool.** `memory_20250818`: client-side file ops under `/memories`. "Claude automatically checks its memory
  directory before starting a task", and it's built for just-in-time retrieval
  (https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool).
- **Managed Agents memory stores.** Mounted directories with immutable versions, 100 kB per memory, 10,000 memories,
  "many small focused files, not a few large ones"; attach only at session creation; `read_only` access available;
  per-session `instructions` up to 4,096 chars (https://platform.claude.com/docs/en/managed-agents/memory). The
  `read_only` option is the natural way to give workers memory without write contention.

So the post's "a markdown file" is right in spirit. Every Anthropic surface converges on **plain files in a directory,
read at start, written deliberately**. That's good for portability: one `.mission/` layout maps onto all four.

### 3.2 Context engineering: memory is for leaving the context window, not for filling it

Anthropic's context-engineering post treats context as a finite "attention budget" subject to "context rot" and asks
for "the smallest possible set of high-signal tokens". It names structured note-taking, "the agent regularly writes notes
persisted to memory outside of the context window. These notes get pulled back into the context window at later times",
as a core long-horizon technique alongside compaction and sub-agents
(https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents). The harness-design post adds the
handoff constraint: "A reset provides a clean slate, at the cost of the handoff artifact having enough state for the next
agent to pick up the work cleanly" (https://www.anthropic.com/engineering/harness-design-long-running-apps). Two design
consequences follow. (a) What gets loaded every session has to be *small and indexed*; detail lives in files opened on
demand. (b) The resume pointer is load-bearing. If it's vague, a reset turns into a restart.

### 3.3 What makes memory compound, and what doesn't

- **Verification coverage is the lever.** Martin's comparison shows the difference between models isn't *whether* they
  write notes. All three did. It's whether the notes become *checked* facts: Opus 4.7 wrote "possibly prc in cents?
  Verify." but verified only 7–33% of the time; Fable 5's best runs reached 73% and distilled rules
  (https://github.com/lchesupercool/ob-clippings/blob/main/2026-06/2026-06-10-designing-loops-with-fable-5.md). A
  template that *won't accept* an unverified fact under "Verified" forces the stage-3 step regardless of model. That's
  an inference from his data, not something he tested.
- **More memory machinery isn't better.** CL-Bench finds agents "frequently overfit to immediate observations or fail
  to reuse knowledge across instances, and dedicated memory systems do not fix this -- in fact, naive ICL outperforms
  systems dedicated to memory management" (https://arxiv.org/abs/2606.05661). That argues for small plain-text files
  loaded straight into context over retrieval services. It also names the failure the skill must guard against,
  *overfitting to immediate observations*, which is why rules need ≥1 verified instance and an explicit scope, and why
  generalization is a separate, reviewed step.
- **Rewrites destroy memory; deltas preserve it.** ACE identifies "brevity bias, which drops domain insights for
  concise summaries" and "context collapse, where iterative rewriting erodes details over time". It fixes them with a
  Reflector separated from the Curator, "incremental delta updates" and "grow-and-refine"
  (https://arxiv.org/html/2510.04618v1). For the skill: entries have IDs; updates are add / modify-by-ID /
  supersede-by-ID; consolidation is a separate curator pass with a diff that a verifier reviews. ACE's argument for
  *comprehensive* playbooks is in tension with context rot. The resolution here is a comprehensive **archive** with a
  compact **loaded index**.
- **Practitioner convergence.** Every's Compound Engineering plugin formalizes "brainstorm, plan, build, review, then
  capture what you learned — so the knowledge from each change is written down where the next change can read it"
  (https://github.com/EveryInc/compound-engineering-plugin). The capture step is a first-class workflow stage, not an
  afterthought, which matches verdict 10's inbox.

### 3.4 Enforcement: hooks turn protocol into guarantees

The hooks reference lists `SessionStart` ("When a session begins or resumes"), `SessionEnd`, `Stop`, `SubagentStop`,
`PreCompact`, `PostCompact`, `TaskCompleted`, `InstructionsLoaded` and more, and handlers can be shell commands, HTTP,
MCP tools, prompts or subagents (https://code.claude.com/docs/en/hooks). Claude Academy gives the operational details
that matter here: plain stdout from a SessionStart hook is added to context; "to re-inject context after compaction,
don't use PostCompact. Use SessionStart with the compact matcher"; only exit 2 blocks (exit 1 doesn't); Stop can be
blocked (https://academy.claude.com/courses/claude-code-in-action/hooks). Best practices adds the ceiling: "Claude Code
overrides the hook and ends the turn after 8 consecutive blocks", and it lays out a gate ladder: prompt → `/goal` → Stop
hook → verification subagent (https://code.claude.com/docs/en/best-practices). A practitioner guide stresses checking
`stop_hook_active` and writing the block `reason` as the next instruction (https://amitkoth.com/claude-code-stop-hooks/).
A community SessionStart-`compact` example re-injects a saved summary (https://www.hookstack.app/hook/session-start-reinject-after-compact).

### 3.5 Skills that sharpen without rotting

The best evidence is Anthropic's own reversal. The bundled `/verify` skill records its recipe to
`.claude/skills/verify/SKILL.md`, and "Claude edits the recorded file only when it steered a run wrong, such as a command
that failed or a missing step, so you can commit the file without per-session diffs. Before v2.1.205, the bundled skill
told Claude to fold in anything a run learned, which caused frequent merge conflicts"
(https://code.claude.com/docs/en/skills). The trigger for a skill edit is *the skill misled a run*, not *a run learned
something*. skill-creator supplies the regression mechanism: `evals/evals.json` cases, and each case run with-skill
*and* baseline in the same turn
(https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/plugins/skill-creator/skills/skill-creator/SKILL.md).
The context-engineering post warns against stuffing "a laundry list of edge cases" into prompts. A lessons file that
grows forever is exactly that.

### 3.6 Evidence from the user's own practice (arcwell)

`arcwell/docs/handoff/2026-08-21-remediation-status.md` already shows the target discipline:
- one authoritative document per fact kind, with companions deferring to it (lines 3–6);
- every landed item tied to the gate command that verified it (lines 8–10);
- rules distilled into general, reusable form: "A budget ceiling is a WAIT, not a verdict" (line 168) and "an
  in-memory harness cannot prove persistence" (lines 59–60);
- decisions recorded with the rejected alternative and the reason (lines 187–189);
- explicit evidence levels: "backed by the repository's own gates … None of it is backed by production behavior"
  (lines 216–221).

The skill should formalize these as fields (`Evidence level: offline-gate | staging | production`) rather than invent a
new style. There's no CLAUDE.md, AGENTS.md or `.claude/` directory in `arcwell/` (glob, no matches). The user's
memory is currently in docs, not harness-loaded, which is exactly the "read at start" gap the hooks close.

## 4. Opinionated spec for the skill

### 4.1 File architecture: one home per kind of fact

| Kind of fact | Home | Loaded when | Writer | Git |
|---|---|---|---|---|
| Build/test commands, durable conventions for every session | `CLAUDE.md` (import `@AGENTS.md` if it exists) | Every session (harness) | Human, or a mission *proposal* approved at retro | Tracked |
| Mission goal, success criteria, task board, progress % | `.mission/STATUS.md` | Session start (hook prints the header + board) | Orchestrator | Tracked |
| Verified facts, hypotheses, general rules, open failures, resume pointer | `.mission/STATE.md` | Session start (hook prints the Resume + Rules index) | Orchestrator only | Tracked |
| Architectural and product decisions with alternatives | `.mission/DECISIONS.md` (append-only) | On demand; index line in STATE.md | Orchestrator after a decision gate | Tracked |
| External sources, findings, dates, reliability | `.mission/RESEARCH.md` | On demand | Research workers via orchestrator | Tracked |
| Failure investigations too long for STATE | `.mission/investigations/<id>.md` | On demand, linked from STATE | Investigator worker | Tracked |
| Candidate cross-project lessons | `.mission/LESSONS-INBOX.md` | Retro only | Anyone (append) | Tracked |
| Promoted cross-project lessons | `<skill>/references/lessons.md` + `<skill>/evals/evals.json` | When the skill loads the reference | Promotion pipeline only | Skill repo |
| Superseded or expired entries | `.mission/archive/state-YYYY-MM.md` | Never automatically | Curator | Tracked |
| Scratch, transcripts, large logs | `.mission/tmp/` | Never | Anyone | **Ignored** |

- **MUST** create `.mission/` at mission start for M/L/XL scope and track it in git. It's reviewable, diffable, survives
  worktrees and branches, and gives an audit trail.
- **MUST NOT** store the same fact in two files. STATUS says *what is done*; STATE says *what is true*. "Task T7 done"
  belongs in STATUS; "the webhook race is real, verified by repro script X" belongs in STATE.
- **MUST** give every STATE/DECISIONS/INBOX entry a stable ID (`F-012`, `R-004`, `H-007`, `O-003`, `D-009`, `L-021`),
  a date, and (for facts/rules) a confidence.
- **SHOULD** put `.mission/tmp/` in `.gitignore`. **MAY** use `CLAUDE.local.md` for personal sandbox URLs.
- **MUST NOT** commit secrets, customer data or tokens into any memory file. Record the *name* of a secret, never the
  value.

### 4.2 Stage gates (fail → investigate → verify → distill → consult)

- **Stage 1 (Fail) MUST** capture: date, symptom, exact reproduction command or artifact path, observed vs expected,
  and blast radius. An entry that only says "tests flaky" is rejected by the validator.
- **Stage 2 (Investigate) MUST** add at least one hypothesis with a *discriminating check*, meaning a command whose
  result would falsify it. Hypotheses live under `## Hypotheses`, never under `## Verified facts`.
- **Stage 3 (Verify) MUST** record `Evidence:` (the exact command/query/test and the salient output line, or an
  artifact path + commit SHA), `Evidence level:` (`local-run | ci | staging | production | doc-source`), and `Verified:`
  date. No evidence, no promotion. The verifier sub-agent SHOULD re-run the evidence command for any fact that gates a
  decision or a rule.
- **Stage 4 (Distill) MUST** phrase the rule as a general, imperative statement plus `Applies when:` (scope conditions),
  `Instances:` (≥1 verified fact ID), and `Counter-cases:` (known exceptions, or "none known"). A rule with a single
  instance MUST carry `confidence: low`. It becomes `medium` at 2 instances and `high` at ≥3 or once a verifier has
  reproduced it.
- **Stage 5 (Consult) MUST** happen at the start of every task. The orchestrator includes relevant rule IDs in each
  worker brief ("Consult R-004, R-009 before editing auth middleware"), and workers cite rule IDs they applied in their
  return. A rule that nobody cites across 5 sessions is a pruning candidate.
- **MUST** mark an entry as `CONTRADICTION` in `## Open failures` when new evidence conflicts with a verified fact, and
  **MUST** resolve it by re-running both evidence commands. The loser is superseded, not silently edited.

### 4.3 Session protocol

- **MUST (start):** read `STATE.md` → `## Resume` and `## Rules index`, `STATUS.md` board, and the relevant skill
  references, before planning. In Claude Code the harness does this through the SessionStart hook; everywhere else it's
  step 1 of the orchestrator prompt.
- **MUST (before any context reset, compaction or hand-off):** update `## Resume` with the next concrete action,
  branch/worktree, the command to re-verify the last change, and the open question blocking progress.
- **MUST (end):** write the session delta: tasks moved, facts added/superseded, failures opened/closed, lessons
  appended to the inbox, and one `## Last session` line. The Stop hook checks freshness.
- **SHOULD** keep the resume pointer runnable. "Next: run `pnpm test auth` in worktree `wt-auth`; expected 3 failures
  in rate-limit order" beats "Next: continue auth work".
- **MUST NOT** let workers edit STATE.md or STATUS.md directly in fan-out. They return a structured `memory_delta`
  block (§7.8) and the orchestrator merges it. That avoids write races and whole-file rewrites.

### 4.4 Hygiene

- **MUST** enforce budgets: STATE.md ≤ 150 lines (≈12 KB), STATUS.md ≤ 100 lines, DECISIONS.md unbounded but with a ≤ 25-line
  index at the top, LESSONS-INBOX ≤ 30 open entries, `references/lessons.md` ≤ 40 entries / 300 lines with a TOC.
- **MUST** run the curator pass (§7.10) when a budget is exceeded, at each milestone, and at mission end.
- **MUST** expire facts about volatile things (external APIs, prices, versions, infra state) after a `Recheck-by:` date,
  90 days by default and 14 days for production state. Expired facts drop to `Hypotheses` until re-verified.
- **SHOULD** keep what gets loaded under ~3k tokens combined (hook output), with everything else linked by path. This
  is an inference from the context-rot guidance, not a measured threshold.
- **MUST** apply edits as ID-addressed deltas. **MUST NOT** ask a model to "rewrite/condense STATE.md" in one pass;
  consolidation produces a proposed diff that a separate verifier checks for information loss.

### 4.5 Compounding into skills

- **MUST** separate project memory (STATE) from procedural cross-project memory (skill). The test: "would this help on a
  different repository?" If not, it stays in STATE.
- **MUST** append lesson candidates to `LESSONS-INBOX.md` during work; **MUST NOT** edit the skill mid-mission.
- **MUST** promote a lesson only when all of these hold: (a) root cause verified (stage 3 evidence linked); (b) seen in ≥2
  independent missions/projects, **or** 1 incident costing ≥1 day or a production defect; (c) project-agnostic phrasing
  with `Applies when:`; (d) an eval case exists that fails without the lesson or demonstrably exercises it; (e) an
  independent verifier approves; (f) it doesn't duplicate or contradict an existing lesson (or it explicitly supersedes
  one).
- **MUST** follow the Anthropic `/verify` rule for procedural files (SKILL.md, recipes): edit only when the skill *steered
  a run wrong* (https://code.claude.com/docs/en/skills).
- **SHOULD** batch promotions at retro (mission end or weekly), not per failure.
- **MAY** propose CLAUDE.md additions at retro for project-wide rules violated ≥2 times; a human or the orchestrator at
  high effort approves.

### 4.6 Graceful degradation

- **IF** hooks are unavailable **THEN** the orchestrator prompt MUST begin with "Read `.mission/STATE.md` Resume + Rules
  index" and end with the session-end checklist, and the final verifier MUST check `Last session` freshness.
- **IF** running in CMA **THEN** mount the memory store `read_write` for the orchestrator and `read_only` for workers;
  split STATE sections into files (`state/facts.md`, `state/rules.md`, …) under 100 kB each.
- **IF** personal skills don't load (cloud/Routines) **THEN** vendor the skill into the repo's `.claude/skills/` or a
  plugin, and sync `references/lessons.md` through a PR.

## 5. Model & effort assignment

Principle: memory *mechanics* (loading, freshness, schema validity) are deterministic scripts that cost no tokens.
Models are spent on the three steps that need judgment: **investigate**, **distill**, and **independently verify a
promotion**. Pricing isn't verified in this lane; the post's figures ($10/$50 per MTok for Fable, "~5× Opus") are
treated as relative guidance only.

| Role | Default model / effort | Escalate to | Downgrade guard (the check that makes the cheaper choice safe) |
|---|---|---|---|
| Memory loader / freshness checker | **No model**: SessionStart + Stop hook scripts | n/a | The validator script's exit code; a Stop-hook block with a specific reason |
| Schema validator (IDs, evidence field present, budgets) | **No model**: `mission-memory-lint` script (§7.9) | Sonnet 4.6 low only for fuzzy checks ("is Evidence an actual command?") | Deterministic regexes; the lint fails closed |
| STATE/STATUS merge (orchestrator applies worker deltas) | Same model as the orchestrator: Fable 5.1 (L/XL), Opus 4.8 medium (M), Sonnet 4.6 high (S) | n/a | Deltas are ID-addressed and small; the lint re-runs after merge; the diff is visible in git |
| Worker `memory_delta` producer | Worker's own model, typically **Sonnet 4.6 medium** | n/a | Template forces fields. Martin found Sonnet needs "task-specific memory instructions", which the template supplies. The orchestrator rejects deltas with no evidence |
| Failure investigator (stages 2–3) | **Sonnet 4.6 high** for routine failures (env, config, known flake) | **Opus 4.8 high** when 2 Sonnet hypotheses are falsified, the root cause crosses ≥2 subsystems, or it's a concurrency/data-integrity issue | The evidence command must reproduce the failure *and* show the fix. The verifier re-runs it |
| Evidence verifier (re-runs commands, checks the claim follows from the output) | **Sonnet 4.6 low** | Sonnet 4.6 high when the output needs interpretation (perf numbers, statistical flake rates) | Pass requires a quoted output line; spot-check 1 in 5 approvals with Sonnet 4.6 high in L/XL missions |
| Distiller (stage 4: fact → general rule, inbox → lesson draft) | **Opus 4.8 high** | **Fable 5.1** for XL end-of-mission retros that synthesize ≥10 investigations or several projects (the one place Martin's evidence supports the top tier: distillation into rules) | Promotion verifier (next row) plus an eval case that must pass with-skill and show a difference from baseline |
| Promotion verifier (independent, adversarial) | **Sonnet 4.6 high**, fresh context, sees only the lesson, the linked evidence and the existing lessons.md; never the distiller's reasoning | **Opus 4.8 high** when the verifier and distiller disagree, or the change touches SKILL.md body rather than references | Verdict must cite which promotion criteria (a)–(f) pass or fail; 2 consecutive rejections return the lesson to the inbox |
| Curator / pruner | **Sonnet 4.6 medium** proposes an ID-level diff | Opus 4.8 medium for XL missions with contradictions across ≥3 entries | **Information-loss verifier**, Sonnet 4.6 high: for every removed ID, confirm it's archived or superseded by a named ID. Lint confirms budget |
| Skill eval runner + grader | Runner: **Sonnet 4.6 medium** (with-skill and baseline); grader: **Sonnet 4.6 low** against explicit assertions | Sonnet 4.6 high grader for subjective assertions | Assertions are binary and pre-written. Human spot-check of the first run after any promotion |
| CLAUDE.md proposal reviewer | **Opus 4.8 medium** | Human | A proposal must link ≥2 violations; edits stay under the 200-line target |

Cost notes:
- The recurring cost is **load**, not writes. Every session pays for the hook output. Keeping loaded memory under ~3k
  tokens and putting static skill text first (so it's cache-friendly) matters more than which model writes it. The
  cache benefit is an inference.
- Keep Fable 5.1 **off** the per-failure path. Investigations are frequent and bounded, and Opus 4.8/Sonnet 4.6 handle
  them once the templates force evidence. Fable's advantage in Martin's data is completing the whole progression on
  its own. The skill replaces "on its own" with structure, and saves Fable for cross-mission synthesis.
- No Haiku anywhere. The roles the post gives Haiku (grader, classifier) go to Sonnet 4.6 low, per the user override.

## 6. Project-shape conditionals

### 6.1 Scale by scope

| Scope | Memory footprint | Hooks | Promotion |
|---|---|---|---|
| **S** (≤ 1 session, 1–3 files) | No `.mission/`. Resume/facts go in the PR description or a `## Notes` section of the task issue. At most one inbox line appended to `~/.claude/mission-lessons-inbox.md` if a lesson is non-obvious | None installed; the end-of-task checklist is inline | None mid-task; the inbox is reviewed at the next retro |
| **M** (2–5 sessions, 1 subsystem) | `.mission/STATE.md` + `STATUS.md` + `LESSONS-INBOX.md`; DECISIONS only if a decision gate fires | SessionStart (startup/resume/compact) | At mission end, only if criteria (b) are met |
| **L** (multi-subsystem, days) | Full layout incl. DECISIONS, RESEARCH, investigations/ | SessionStart + Stop freshness + PreCompact snapshot | Retro per milestone; Opus 4.8 distiller |
| **XL** (weeks, multi-platform, swarms) | Full layout; STATE split into `state/*.md` with a ≤150-line index; archive monthly | All of the above + SubagentStop delta check | Weekly retro; Fable 5.1 cross-mission synthesis; eval suite per promoted lesson |

### 6.2 Shape rules

**Greenfield multi-platform app (e.g., Swift iOS + Cloudflare backend)**
- IF the task spans ≥2 platforms THEN STATE.md MUST have per-platform sections under `## Verified facts`
  (`### backend`, `### ios`, `### contracts`) and the Rules index MUST tag rules with platform scope.
- IF an API contract between platforms is decided THEN record it in DECISIONS.md with the contract file path, and keep
  one fact in STATE: "Contract source of truth: `packages/contracts/openapi.yaml` @ <sha>". Never duplicate the
  schema into memory.
- IF design tokens or UX decisions exist THEN they live in the project design doc/skill, and STATE only stores the path
  and the last verified screenshot artifact path (the vision verifier needs the previous screenshot, post step 13).
- Expect the most toolchain facts (Xcode versions, simulator IDs, wrangler config). Set `Recheck-by:` at 30 days.

**Deep bug hunt**
- IF the task is a bug hunt THEN `## Open failures` is the spine. Every hypothesis gets an `H-` ID with a discriminating
  check, and falsified hypotheses stay (marked `FALSIFIED` with the evidence) until the bug is closed, so the next
  session doesn't retry them.
- IF a hypothesis is falsified twice in a row THEN escalate the investigator to Opus 4.8 high (§5).
- IF the root cause is found THEN require a regression test as the fact's evidence, and draft an inbox lesson phrased
  as a detection *technique* ("when X-shaped symptom, check Y first"), not a project fact.
- Big-bug missions are the highest-yield source of skill lessons. Always run the promotion check at close.

**Feature in an existing product (e.g., a new dashboard)**
- IF the repo has CLAUDE.md/AGENTS.md THEN read it first, and don't copy its content into STATE. STATE records only
  mission-specific discoveries ("dashboard widgets register in `src/widgets/registry.ts`", evidence: grep output).
- IF existing conventions conflict with the plan THEN log a DECISION (adopt the convention or deviate, with reason)
  before implementing.
- Keep it small: M scope by default. No RESEARCH.md unless external libraries are being evaluated.

**Service migration/extraction (e.g., AI gateway into a core service)**
- IF migrating THEN STATE.md MUST have a `## Invariants` subsection under Verified facts: behaviors that must survive
  migration, each with the command that proves it on *both* old and new paths (parity evidence).
- IF cutover steps exist THEN STATUS.md tracks them as a gated checklist, and each step's `Evidence level` must reach
  `staging` or `production`. Offline gates alone are explicitly insufficient, mirroring arcwell's honesty note
  (`arcwell/docs/handoff/2026-08-21-remediation-status.md` lines 216–221).
- IF rollback is designed THEN DECISIONS.md records the rollback trigger and its verification.
- Facts about the old system get `Recheck-by:` equal to the planned decommission date, then archive.

**Research + marketing website with blog/docs**
- IF the task includes market/competitor research THEN RESEARCH.md is primary. Each finding has source URL, access date,
  reliability (`primary | secondary | vendor-claim | unverified`) and the claim it supports. STATE holds only
  *decided positioning facts* that cite RESEARCH IDs.
- IF claims will be published THEN every public claim MUST trace to a RESEARCH ID with `primary` or `secondary`
  reliability. The website verifier checks the trace.
- IF brand/voice decisions are made THEN DECISIONS.md, with examples. Expire market facts at 90 days.
- Lessons here are mostly content-process lessons. Promote sparingly; they're taste-dependent and hard to eval.

**Other shapes that matter**
- **Unattended/cloud runs (Routines, CMA):** IF no human reads the session THEN the Stop/end protocol is mandatory and
  the digest (STATUS header + new Open failures) MUST be written before exit. Personal skills don't load, so vendor the
  skill.
- **Multi-repo missions:** IF the mission touches ≥2 repos THEN one `.mission/` lives in the *coordinating* repo, and the
  others get a one-line pointer in their PR descriptions. No duplicate STATE files.
- **Security-sensitive work:** IF the task handles credentials or exploits THEN memory files record *names and
  locations* of sensitive material only, and the curator lint scans for secret patterns before commit.

## 7. Artifacts & templates

All templates are paste-ready. IDs are `F` fact, `H` hypothesis, `R` rule, `O` open failure, `D` decision, `S` source,
`L` lesson, `T` task.

### 7.1 Directory layout

```text
.mission/
  STATE.md              # what is true (≤150 lines loaded index)
  STATUS.md             # what is done / next (≤100 lines)
  DECISIONS.md          # append-only ADR-lite, index at top
  RESEARCH.md           # sources + findings with reliability
  LESSONS-INBOX.md      # candidate cross-project lessons (≤30 open)
  config                # key=value: scope=L, enforce_stop=1, owner_model=opus-4.8
  investigations/O-003-checkout-flake.md
  archive/state-2026-06.md
  tmp/                  # gitignored: stamps, precompact snapshots, logs
```

`.gitignore` addition: `.mission/tmp/`

### 7.2 STATE.md template

```markdown
# STATE · <project> · mission: <one-line goal>
<!-- Owner: orchestrator only. Workers return memory_delta blocks. Budget: ≤150 lines. -->
<!-- Edit by ID (add / modify / supersede). Never rewrite this file wholesale. -->

## Resume
<!-- Stage 5. Overwrite each session. Must be runnable by a fresh agent with no chat history. -->
- Updated: 2026-06-10T03:30Z by opus-4.8 (session 7)
- Branch/worktree: claude/fix-rate-limit-order @ wt-auth (HEAD 3f2c1ab)
- Next action: run `pnpm test apps/api/auth --run` ; expect 0 failures after R-002 reorder
- Re-verify last change: `pnpm test apps/api/auth/middleware.test.ts` (was green at 3f2c1ab)
- Blocked on: O-003 needs STRIPE_WEBHOOK_SECRET in CI (owner action)
- Read first: R-002, R-005, investigations/O-003-checkout-flake.md

## Rules index
<!-- Stage 4. One line each. Consult before re-deriving. Full entries below. -->
- R-001 time-bucketed metrics: always pass explicit timezone · conf: high
- R-002 auth middleware order rate_limit → jwt → rbac · conf: medium
- R-005 in-memory fakes cannot prove persistence; test against migrated schema · conf: high

## Verified facts
<!-- Stage 3. No entry without Evidence + Level + dates. Unverified → Hypotheses. -->
- F-012 · `trades.prc` is in dollars, not cents · conf: high · verified 2026-06-09 · recheck-by 2026-09-07
  Evidence: `SELECT MIN(prc), MAX(prc) FROM trades` → `0.01 | 48210.55`
  Level: local-run · Scope: trades table, all envs · Supersedes: H-003
- F-013 · `user_id` joins `auth_users.uid`, not `auth_users.id` · conf: high · verified 2026-06-09 · recheck-by 2026-09-07
  Evidence: `SELECT count(*) FROM trades t JOIN auth_users a ON t.user_id=a.uid` → 18231 (= total rows); `...ON a.id` → 0
  Level: local-run · Scope: prod schema v14

## Hypotheses
<!-- Stage 2. Each needs a discriminating check. FALSIFIED entries stay until the parent failure closes. -->
- H-007 · checkout flake is a webhook race (event before order row commit) · opened 2026-06-09 · for O-003
  Check: run `scripts/repro-checkout.sh --iterations 200 --delay-webhook 0ms` ; race predicts ≥2 failures, delay 50ms predicts 0
- H-006 · FALSIFIED 2026-06-09 · flake caused by test DB pool exhaustion
  Evidence: pool max=50, observed peak 11 (`pg_stat_activity` during repro)

## General rules
<!-- Stage 4. Imperative + scope + ≥1 verified instance. conf low=1 instance, medium=2, high=≥3 or verifier-reproduced. -->
- R-002 · Register auth middleware in order rate_limit → jwt → rbac · conf: medium · since 2026-06-10
  Applies when: adding/modifying Express middleware in apps/api · Instances: F-020, F-021 · Counter-cases: none known
- R-005 · Prove persistence against the migrated schema, never an in-memory harness · conf: high · since 2026-06-02
  Applies when: any durable-state change · Instances: F-004, F-009, F-017 · Counter-cases: pure reducers
  Promoted: candidate L-014 in LESSONS-INBOX

## Open failures
<!-- Stage 1→2. Symptom + repro + observed/expected. CONTRADICTION entries go here too. -->
- O-003 · 2026-06-09 · tests/e2e/checkout flakes ~1/50 runs · severity: blocks merge
  Repro: `pnpm e2e checkout --repeat 100` · Observed: 2/100 timeout at order-confirm · Expected: 0/100
  Hypotheses: H-006 (falsified), H-007 (open) · Detail: investigations/O-003-checkout-flake.md
- O-004 · CONTRADICTION · F-008 says rate limit is 100 rpm; staging returns 429 at ~60 rpm · 2026-06-10
  Resolve by: re-run `scripts/rate-probe.sh staging` and read gateway config at deployed sha

## Decisions index
- D-004 Postgres advisory locks over Redis for job leasing (DECISIONS.md#d-004)

## Last session
<!-- One line per session, newest first, keep 5; older lines move to archive. -->
- 2026-06-10 03:30Z · s7 · 7 failures classified, 3 fixes drafted (claude/fix-*), 4 escalated · +F-020,F-021 +R-002 ~H-006 falsified
```

### 7.3 STATUS.md template

```markdown
# STATUS · <mission name>
<!-- What is done and what is next. No facts or rules here (those go in STATE.md). Budget ≤100 lines. -->

## Goal
- Direction: <user's high-level direction, verbatim>
- Done means: <numbered, checkable acceptance criteria; each maps to a gate command>
  1. `pnpm e2e checkout --repeat 100` → 0 failures
  2. Dashboard renders p95 < 1.5s on staging (`scripts/lhci staging /dash`)
- Scope: L · Started: 2026-06-08 · Target: 2026-06-14 · Status: active | paused | done | abandoned

## Progress
- Acceptance: 1/5 criteria passing (last gate run 2026-06-10 03:10Z, `scripts/acceptance.sh` → 1 pass, 4 fail)
- Milestones: M1 ✅ 2026-06-09 · M2 🔄 · M3 ⏳
<!-- Progress % comes only from gate results, never from task counts. -->

## Board
| ID | Task | Owner (model/agent) | State | Evidence of done | Updated |
|---|---|---|---|---|---|
| T-07 | Reorder auth middleware | sonnet-4.6 worker wt-auth | review | `pnpm test apps/api/auth` green @3f2c1ab | 06-10 |
| T-08 | Fix checkout flake | opus-4.8 investigator | blocked (O-003) | — | 06-10 |
| T-09 | Dashboard widget registry | sonnet-4.6 worker | todo | — | 06-09 |
<!-- States: todo | doing | review | blocked(<O-id>) | done | dropped(<reason>). "done" requires Evidence. -->

## Risks & escalations
- 2026-06-10 · Needs owner: STRIPE_WEBHOOK_SECRET in CI (blocks T-08)

## Done log (newest first, keep 10; older → archive)
- 2026-06-09 · T-05 migrate 0007 applied locally · evidence `pnpm db:verify` → ok
```

### 7.4 DECISIONS.md (append-only ADR-lite)

```markdown
# DECISIONS · <project>
<!-- Append-only. To change a decision, add a new entry that Supersedes the old one; mark the old one Superseded-by. -->

## Index
- D-004 Postgres advisory locks over Redis for job leasing · accepted 2026-06-09
- D-003 ~~Redis leasing~~ superseded-by D-004

## D-004 · Postgres advisory locks for job leasing
- Date: 2026-06-09 · Status: accepted · Decider: opus-4.8 (architect), approved by orchestrator fable-5.1
- Context: two workers double-billed provider on concurrent lease (O-002, F-015)
- Options considered:
  1. Redis SETNX with TTL: extra infra; clock-skew risk
  2. Postgres advisory locks: already deployed; transactional with lease row ✅
  3. Deliberately NOT a new job state: every scan/sweep/CHECK already treats retryable identically
- Decision: option 2
- Consequences: lock IDs derived from job hash; long jobs must heartbeat
- Verification: `pnpm test jobs/lease.concurrency.test.ts` (100 parallel leases → 0 duplicates) · Level: ci
- Revisit when: >1 database, or lease p99 > 50ms
- Supersedes: D-003
```

### 7.5 RESEARCH.md entry format

```markdown
## S-011 · Cloudflare Durable Objects alarm semantics
- Accessed: 2026-06-09 · Reliability: primary (vendor docs) · Recheck-by: 2026-09-07
- URL: https://developers.cloudflare.com/durable-objects/api/alarms/
- Finding: <2–4 sentences, quote the load-bearing line>
- Supports: D-006, F-031 · Contradicts: none
```

### 7.6 Lesson entry format, promotion criteria, and skill targets

**Inbox entry** (`.mission/LESSONS-INBOX.md`, append-only; anyone may add):

```markdown
- L-014 · status: candidate | verifying | promoted | rejected(<reason>) | merged-into(L-0xx)
  Lesson: Prove persistence against the migrated schema; an in-memory harness cannot prove it.
  Applies when: a change writes durable state (DB rows, KV, files) and tests use fakes
  Does not apply when: pure functions/reducers with no I/O
  Origin: <project>/<mission> · O-002 → F-004, F-009 · cost of original failure: 1.5 days, silent prod no-op
  Evidence: `pnpm vitest run durable-acquisition.int.test.ts` fails on old code, passes on fix (sha 8e1d2c0)
  Seen in: arcwell m1 (2026-08-21); <second project> (date) · count: 2
  Proposed target: references/lessons.md § Testing · (or SKILL.md step N if the skill steered the run wrong)
  Eval case: evals/evals.json id 31 (drafted)
  Distiller: opus-4.8 high · Verifier: — · Decision date: —
```

**Promotion criteria (all MUST pass; the verifier cites each):**

| # | Criterion | Check |
|---|---|---|
| a | Root cause verified | `Evidence:` has a command/test that fails before and passes after, or a stage-3 fact ID |
| b | Recurrence or cost | `count ≥ 2` independent projects/missions, OR 1 incident with ≥1 day lost or a production defect |
| c | General & scoped | No project-specific names in `Lesson`; `Applies when` and `Does not apply when` present |
| d | Testable | An eval case exists; with-skill run satisfies its assertions and baseline doesn't (or the verifier writes why it's advisory) |
| e | Independent approval | Verifier in a fresh context approves; it sees lesson + evidence + current lessons.md only |
| f | Non-duplicative | No existing lesson says the same; if it contradicts one, it names what it supersedes |
| g | Budget | `references/lessons.md` stays ≤40 entries / ≤300 lines after merge; otherwise curator merges or retires first |
| h | Right target | Edit SKILL.md body only if the skill *steered a run wrong* (https://code.claude.com/docs/en/skills); otherwise references/lessons.md |

**Promoted entry** (`~/.claude/skills/<skill>/references/lessons.md`, or the repo-vendored skill for cloud runs):

```markdown
# Lessons (promoted) · <skill>
<!-- ≤40 entries, ≤300 lines. Grouped by phase. Each links an eval case. Retire entries unused for 6 months. -->
## Contents
- Testing (L-014, L-019) · Debugging (L-003, L-022) · Migration (L-008) · Memory hygiene (L-011)

## Testing
### L-014 · Prove persistence against the migrated schema
- Rule: When a change writes durable state, at least one test MUST drive the production store against the migrated schema.
- Applies when: durable writes + fakes in tests · Not when: pure functions
- Why: in-memory fakes pass while the real store silently no-ops
- Eval: evals/evals.json#31 · Promoted: 2026-08-30 · Seen: 2 projects · Last cited: 2026-09-12
- Supersedes: — · Confidence: high
```

**Eval case** (`<skill>/evals/evals.json`, skill-creator schema, https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/plugins/skill-creator/skills/skill-creator/SKILL.md):

```json
{
  "skill_name": "mission",
  "evals": [
    {
      "id": 31,
      "prompt": "Add a 'last_seen' column update to the session heartbeat handler and make sure it's tested.",
      "expected_output": "Plan includes an integration test against the migrated schema, not only an in-memory fake.",
      "files": ["fixtures/heartbeat-repo.tar.gz"],
      "assertions": [
        "The test plan names a test that runs against the real migrated database/schema",
        "The agent does not declare persistence verified based solely on an in-memory fake"
      ]
    }
  ]
}
```

### 7.7 Session start / end protocol (paste into SKILL.md)

```markdown
## Memory protocol

### At session start (hook-injected in Claude Code; do it manually elsewhere)
1. Read `.mission/STATE.md` → Resume, Rules index, Open failures. Read `.mission/STATUS.md` → Goal, Board.
2. If Resume.Updated is older than the latest commit on the branch, re-run "Re-verify last change" before planning.
3. Open any file listed under "Read first". Don't read archive/ unless an ID you need lives there.
4. List the rule IDs relevant to today's tasks; put them in each worker brief.
5. If any `recheck-by` date has passed for a fact you depend on, move it to Hypotheses and schedule a re-verify task.

### During work
- New failure → add O-entry (symptom, repro, observed/expected) before trying fixes.
- Diagnosis → H-entry with a discriminating check. Only move to Verified facts with Evidence + Level + date.
- Workers never edit STATE/STATUS; they return a memory_delta block. Merge by ID.
- Something reusable across projects → append to LESSONS-INBOX. Never edit the skill mid-mission.

### Before compaction, reset or hand-off
- Rewrite `## Resume` so a fresh agent with zero chat history can take the next action.

### At session end (Stop hook enforces in autonomous runs)
1. STATUS: move tasks, attach evidence to "done", update Acceptance from the latest gate run.
2. STATE: apply facts/hypotheses/rules/failures deltas; append one `## Last session` line.
3. Run `.mission/bin/memory-lint` and fix violations.
4. If budgets are exceeded or a milestone closed → run the curator pass (references/pruning.md).
5. Commit `.mission/` with message `mission: s<N> memory update`.
```

### 7.8 Worker `memory_delta` block (required at the end of every worker return)

```markdown
<memory_delta>
facts_add:        # only with evidence; otherwise put under hypotheses_add
  - claim: "Widgets register via src/widgets/registry.ts default export"
    evidence: "`rg -n 'registerWidget' src` → src/widgets/registry.ts:14"
    level: local-run
    scope: "apps/web dashboard"
hypotheses_add:
  - claim: "Slow render is N+1 fetch in useWidgetData"
    check: "`pnpm test perf/widgets --reporter=json` → count fetch calls per widget"
failures_add:
  - symptom: "..."; repro: "..."; observed: "..."; expected: "..."
supersede: []      # e.g. [{id: F-008, by: "new fact above", evidence: "..."}]
rules_cited: [R-002, R-005]
lesson_candidates: []   # one-liners; the orchestrator writes inbox entries
tasks: [{id: T-09, state: done, evidence: "`pnpm test apps/web/widgets` → 12 passed"}]
</memory_delta>
```

### 7.9 Hook configuration and scripts (Claude Code)

`.claude/settings.json` (project, committed). Event names per https://code.claude.com/docs/en/hooks; SessionStart
`compact` re-injection per https://academy.claude.com/courses/claude-code-in-action/hooks.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|compact",
        "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.mission/bin/session-start.sh" }]
      }
    ],
    "PreCompact": [
      {
        "matcher": "auto|manual",
        "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.mission/bin/pre-compact.sh" }]
      }
    ],
    "Stop": [
      {
        "hooks": [{ "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.mission/bin/stop-check.sh" }]
      }
    ]
  }
}
```

`.mission/bin/session-start.sh`. Plain stdout on exit 0 is added to context:

```bash
#!/usr/bin/env bash
set -u
root="${CLAUDE_PROJECT_DIR:-.}"; dir="$root/.mission"
[ -f "$dir/STATE.md" ] || exit 0
input="$(cat)"
src="$(printf '%s' "$input" | jq -r '.source // "startup"' 2>/dev/null || echo startup)"
mkdir -p "$dir/tmp"; touch "$dir/tmp/checkpoint.stamp"
section() { awk -v n="## $2" '$0==n{p=1;print;next} /^## /{p=0} p' "$1"; }
echo "# Mission memory (auto-injected at $src). Consult rules before re-deriving facts."
section "$dir/STATE.md" "Resume"
section "$dir/STATE.md" "Rules index"
section "$dir/STATE.md" "Open failures" | head -n 40
[ -f "$dir/STATUS.md" ] && { section "$dir/STATUS.md" "Goal"; section "$dir/STATUS.md" "Progress"; }
if [ "$src" = "compact" ] && [ -f "$dir/tmp/precompact-snapshot.md" ]; then
  echo "## Pre-compaction snapshot"; cat "$dir/tmp/precompact-snapshot.md"
fi
if [ -f "$dir/tmp/memory-debt" ]; then
  echo "## MEMORY DEBT: last session ended without updating STATE/STATUS. Reconstruct from git log first."
  cat "$dir/tmp/memory-debt"
fi
today="$(date -u +%F)"
{ grep -E '^- F-[0-9]+ .*recheck-by [0-9-]+' "$dir/STATE.md" || true; } | while IFS= read -r l; do
  d="$(printf '%s' "$l" | sed -E 's/.*recheck-by ([0-9-]+).*/\1/')"
  if [[ "$d" < "$today" ]]; then echo "EXPIRED ${l%% ·*} (recheck-by $d): treat as hypothesis until re-verified"; fi
done
exit 0
```

`.mission/bin/pre-compact.sh`. Snapshot only; its output is not re-injected, SessionStart(`compact`) prints it:

```bash
#!/usr/bin/env bash
set -u
root="${CLAUDE_PROJECT_DIR:-.}"; dir="$root/.mission"
[ -f "$dir/STATE.md" ] || exit 0
mkdir -p "$dir/tmp"
{
  echo "- Snapshot: $(date -u +%FT%TZ)"
  echo "- Branch: $(git -C "$root" rev-parse --abbrev-ref HEAD 2>/dev/null) @ $(git -C "$root" rev-parse --short HEAD 2>/dev/null)"
  echo "- Uncommitted (first 30):"; git -C "$root" status --porcelain 2>/dev/null | head -n 30 | sed 's/^/    /'
  echo "- STATE.md modified: $(date -u -r "$dir/STATE.md" +%FT%TZ 2>/dev/null)"
} > "$dir/tmp/precompact-snapshot.md"
exit 0
```

`.mission/bin/stop-check.sh`. Opt-in (`enforce_stop=1` in `.mission/config`) for autonomous runs, loop-safe:

```bash
#!/usr/bin/env bash
set -u
root="${CLAUDE_PROJECT_DIR:-.}"; dir="$root/.mission"; stamp="$dir/tmp/checkpoint.stamp"
input="$(cat)"
[ -f "$dir/STATE.md" ] && [ -f "$stamp" ] || exit 0
grep -q '^enforce_stop=1' "$dir/config" 2>/dev/null || exit 0
active="$(printf '%s' "$input" | jq -r '.stop_hook_active // false' 2>/dev/null)"
changed="$(find "$root" -type f -newer "$stamp" -not -path "$root/.git/*" -not -path "$root/.mission/*" \
  -not -path '*/node_modules/*' -print -quit 2>/dev/null)"
[ -z "$changed" ] && exit 0
if [ "$dir/STATE.md" -nt "$stamp" ] && [ "$dir/STATUS.md" -nt "$stamp" ]; then
  if ! "$dir/bin/memory-lint" 2>"$dir/tmp/lint.err"; then
    [ "$active" = "true" ] && { cp "$dir/tmp/lint.err" "$dir/tmp/memory-debt"; exit 0; }
    jq -n --arg r "Mission memory lint failed: $(head -n 5 "$dir/tmp/lint.err" | tr '\n' ' '). Fix, then stop." \
      '{decision:"block", reason:$r}'
    exit 0
  fi
  rm -f "$dir/tmp/memory-debt"; touch "$stamp"; exit 0
fi
if [ "$active" = "true" ]; then   # already blocked once; don't loop, record debt for next SessionStart
  echo "$(date -u +%FT%TZ) changed ${changed#$root/} without memory update" > "$dir/tmp/memory-debt"; exit 0
fi
jq -n --arg r "Files changed (e.g. ${changed#$root/}) but .mission/STATE.md and STATUS.md were not both updated. Update STATUS (board, evidence, Acceptance) and STATE (Resume, Last session, new facts/failures with Evidence), run .mission/bin/memory-lint, then stop." \
  '{decision:"block", reason:$r}'
exit 0
```

Optional (L/XL): a `SubagentStop` hook that rejects worker returns missing `<memory_delta>`. The input schema for
transcript access wasn't verified in this lane, so the synthesizer should check the hooks reference before shipping it.

`.mission/bin/memory-lint`. Fails closed and exits 1 on violations. POSIX awk, no interval regex:

```bash
#!/usr/bin/env bash
set -u
dir="${CLAUDE_PROJECT_DIR:-.}/.mission"; fail=0; mkdir -p "$dir/tmp"
err() { echo "memory-lint: $*" >&2; fail=1; }
n() { wc -l < "$1" | tr -d ' '; }
[ "$(n "$dir/STATE.md")" -le 150 ] || err "STATE.md > 150 lines: run curator pass"
[ ! -f "$dir/STATUS.md" ] || [ "$(n "$dir/STATUS.md")" -le 100 ] || err "STATUS.md > 100 lines"
if [ -f "$dir/LESSONS-INBOX.md" ]; then
  open="$(grep -cE '^- L-[0-9]+ · status: (candidate|verifying)' "$dir/LESSONS-INBOX.md")"
  [ "$open" -le 30 ] || err "LESSONS-INBOX has $open open entries (max 30)"
fi
awk '
  function check() {
    if (id ~ /^F-/ && (body !~ /Evidence: / || body !~ /Level: / || head !~ /verified [0-9][0-9][0-9][0-9]-/)) print id " missing Evidence/Level/verified date"
    if (id ~ /^R-/ && (body !~ /Applies when: / || body !~ /Instances: F-/)) print id " missing Applies when or a verified F- instance"
    if (id ~ /^H-/ && head !~ /FALSIFIED/ && body !~ /Check: /) print id " missing discriminating Check"
    if (id ~ /^O-/ && head !~ /CONTRADICTION/ && body !~ /Repro: /) print id " missing Repro"
    id = ""
  }
  /^## / { if (id != "") check(); section = $0; next }
  /^- [FHRO]-[0-9]+/ { if (id != "") check(); id = $2; head = $0; body = ""
                       if (section ~ /index/) id = ""; next }
  /^  / { body = body "\n" $0; next }
  { if (id != "") check() }
  END { if (id != "") check() }
' "$dir/STATE.md" > "$dir/tmp/lint.out"
if [ -s "$dir/tmp/lint.out" ]; then sed 's/^/memory-lint: /' "$dir/tmp/lint.out" >&2; fail=1; fi
if grep -nE 'sk_live_|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{20,}' "$dir"/*.md >&2; then
  err "possible secret in memory files"
fi
exit "$fail"
```

### 7.10 Pruning / consolidation procedure (curator pass)

**Triggers:** a lint budget violation; milestone closed; mission end; `Last session` has > 5 lines; ≥ 3 CONTRADICTION
entries open; weekly for XL.

**Procedure (ID-level, never a wholesale rewrite):**
1. **Snapshot.** `cp .mission/STATE.md .mission/tmp/STATE.pre-curate.md`. Record the line count and entry IDs
   (`grep -oE '^- [FHROD]-[0-9]+' STATE.md`).
2. **Expire.** For each F- entry past `recheck-by`: re-run its Evidence command if it's cheap (<30s) and in scope.
   Otherwise move it to Hypotheses as `H-` with `Check:` = the old evidence command.
3. **Resolve contradictions.** For each `CONTRADICTION` O-entry, re-run both evidence commands. The winner stays; the
   loser is marked `Superseded-by <id>` and moved to archive.
4. **Close failures.** O-entries with a verified fix → one-line archive record
   `O-003 closed 2026-06-12 by F-030 (regression test ...)`. Their FALSIFIED hypotheses move to the investigation file.
5. **Merge rules.** R-entries with overlapping `Applies when` and compatible statements → one rule. Keep the union of
   Instances and the narrowest correct scope. Record `Merged: R-007, R-011`.
6. **Retire unused rules.** Rules not cited in `rules_cited` for 5 sessions *and* not in the Rules index of any open
   task → archive with `Retired (uncited)`. Don't retire rules with `conf: high` that guard data integrity or security.
7. **Roll logs.** Keep 5 `Last session` lines and 10 STATUS `Done log` lines; move the rest to
   `archive/state-YYYY-MM.md` or `archive/status-YYYY-MM.md`.
8. **Offload detail.** Any entry body > 4 lines → move detail to `investigations/<id>.md` and leave a 2-line entry with
   a link.
9. **Inbox triage.** Candidates older than 60 days with count 1 and no cost ≥ 1 day → `rejected(stale)`. Duplicates →
   `merged-into`.
10. **Verify.** Run the information-loss verifier (prompt §7.11) against `tmp/STATE.pre-curate.md` vs the new STATE.md
    + archive diff. Every removed ID must be accounted for (archived, superseded, merged, or moved to investigations).
    Then run `memory-lint`.
11. **Commit.** `mission: curate STATE (-<n> lines, archived <ids>)`.

**Skill-side pruning (`references/lessons.md`), quarterly or when > 40 entries:** retire lessons whose eval case passes
on baseline without the skill (the model learned it; the lesson is dead weight). Merge overlapping lessons. Retire
lessons with `Last cited` > 6 months. Every retirement goes to `references/lessons-archive.md` with the reason.

### 7.11 Sub-agent prompt skeletons

**Failure investigator (Sonnet 4.6 high → Opus 4.8 high on escalation)**

```text
ROLE: Failure investigator. You diagnose; you don't ship fixes unless the brief says so.
FAILURE: <O-id, symptom, repro, observed, expected>
KNOWN: rules <R-ids with one-line text>; falsified hypotheses <H-ids + evidence>. Don't retry falsified ones.
DO:
1. Reproduce with the repro command. If it doesn't reproduce in N=<n> runs, report that as the result.
2. Propose ≤3 hypotheses. For each, a discriminating check: a command whose output would falsify it.
3. Run the checks, cheapest first. Stop when one hypothesis survives and ≥1 other is falsified.
4. Confirm the surviving cause with a before/after command (fails without fix or with the condition, passes otherwise).
RETURN: summary (≤150 words) + <memory_delta> with facts_add ONLY for claims backed by a quoted output line,
hypotheses_add for the rest, and a lesson_candidates line ONLY if the technique would help in another repository.
NEVER: mark a fact verified from reasoning alone; edit .mission/ files directly.
```

**Distiller (Opus 4.8 high; Fable 5.1 for XL retros)**

```text
ROLE: Distiller. Turn verified project facts and closed failures into general rules and lesson candidates.
INPUT: STATE.md Verified facts + closed O-entries since <date>; LESSONS-INBOX open entries; current references/lessons.md TOC.
DO:
1. Group facts by underlying mechanism, not by file or feature.
2. For each group with ≥1 verified instance, draft a rule: imperative sentence, Applies when, Does not apply when,
   Instances (F-ids), confidence by instance count (1=low, 2=medium, ≥3=high).
3. Decide scope: project-only → STATE R-entry; cross-project → inbox L-entry with a drafted eval case (prompt + ≤3
   binary assertions).
4. Check duplicates/contradictions against existing rules and lessons; propose supersede/merge explicitly.
RETURN: a list of ID-addressed deltas (add/modify/supersede). Don't rewrite whole files.
AVOID: rules generalized from one observation without scope; restating tool docs Claude already knows; project names in L-entries.
```

**Promotion verifier (Sonnet 4.6 high, fresh context; Opus 4.8 high on disagreement)**

```text
ROLE: Independent promotion verifier. Be adversarial: your job is to find reasons NOT to promote.
YOU SEE: one inbox entry, its linked evidence (commands + outputs), the eval case, current references/lessons.md.
YOU DO NOT SEE: the distiller's reasoning. Don't ask for it.
CHECK each criterion and quote the text that satisfies or fails it:
 a root cause verified · b recurrence ≥2 or cost ≥1 day/prod defect · c general + scoped (no project names)
 d eval case: run with-skill and baseline, report assertion results · e (you are e) · f duplicates/contradictions
 g lessons.md budget after merge · h target: SKILL.md body only if the skill steered a run wrong
VERDICT: PROMOTE | REVISE(<specific edits>) | REJECT(<criterion>) ; plus the final lesson text if PROMOTE.
```

**Information-loss verifier for curator diffs (Sonnet 4.6 high)**

```text
ROLE: Verify a memory consolidation lost nothing load-bearing.
INPUT: tmp/STATE.pre-curate.md, new STATE.md, archive diff, investigations diff.
DO: For every entry ID present before and absent after, find where it went (archived / superseded-by / merged-into /
moved-to-investigation). For every merged rule, confirm the union of Instances is preserved and scope isn't broadened.
For every expired fact, confirm it became a hypothesis or was re-verified with new evidence.
RETURN: PASS, or FAIL with a table of unaccounted IDs and scope changes.
```

## 8. Anti-patterns & failure modes

**Memory content**
- **Guess-in-fact's-clothing.** "user_id matches uid. Confirmed 2026-06-09." with no command. That's how memory
  starts lying with authority. Fix: the lint rejects F-entries without Evidence/Level.
- **Rules from one observation, no scope.** This is CL-Bench's "overfit to immediate observations"
  (https://arxiv.org/abs/2606.05661) written down as a permanent rule. Fix: `Instances:` + `Applies when:` +
  `conf: low` at 1 instance.
- **Duplicate kinds.** The post's example has both "General rules" and "Lessons learned" at stage 4. Two homes means
  drift. Fix: rules in STATE; cross-project lessons in the inbox → skill.
- **Status in STATE, facts in STATUS.** "T-07 done" in STATE bloats the loaded index; "rate limit is 100rpm" on a
  board card is never consulted. Fix: the table in §4.1.
- **Silent edits of verified facts.** Changing F-008's value in place erases the contradiction signal. Fix: supersede by
  ID and keep a CONTRADICTION entry until resolved.
- **Secrets in memory.** Memory files are committed and loaded into every session. Fix: names only, plus the lint's
  secret scan.

**Process**
- **"Write the lesson into the skill after every failure."** It produces merge conflicts, bloat and contradictory
  guidance. Anthropic reversed exactly this for `/verify` (https://code.claude.com/docs/en/skills). Fix: inbox +
  batched promotion + "edit only when the skill steered a run wrong".
- **Self-graded promotion.** The distiller approving its own lesson repeats the self-critique failure Martin describes.
  Fix: a fresh-context verifier.
- **Whole-file regeneration ("condense STATE.md").** Brevity bias and context collapse
  (https://arxiv.org/html/2510.04618v1). Fix: ID-addressed deltas + the information-loss verifier.
- **Workers writing shared memory in parallel.** Races, clobbered sections, inconsistent IDs. Fix: `memory_delta` blocks;
  the orchestrator is the only writer; in CMA, workers mount `read_only`.
- **Relying on instructions for read-at-start.** CLAUDE.md is "a request, not a guarantee"
  (https://academy.claude.com/courses/claude-code-in-action/hooks), and Sonnet "rarely consults prior notes" (Martin).
  Fix: the SessionStart hook injects the resume pointer and rules index.
- **Re-injecting after compaction with PostCompact.** The output doesn't reach the conversation. Fix: SessionStart
  `compact` (same Academy source).
- **Stop hook that loops or nags.** Blocking every interactive turn, ignoring `stop_hook_active`, or exiting 1 (which
  doesn't block). Claude Code force-ends after 8 consecutive blocks anyway (https://code.claude.com/docs/en/best-practices).
  Fix: opt-in `enforce_stop=1`, a loop guard, a memory-debt file, `{decision:"block"}` JSON with a specific reason.
- **Vague resume pointers.** "Continue auth work" turns a reset into a restart. Fix: a runnable next action +
  re-verify command.
- **Promoting from newly passing tests** (post step 09). There's no causal link. Fix: promote only from investigated
  failures.

**Cost / token traps**
- **Loading the whole archive "just in case".** Every session pays that cost again, and long context degrades
  performance ("LLM performance degrades as context fills", https://code.claude.com/docs/en/best-practices). Fix: hook
  prints ≤ ~3k tokens; everything else is linked by path.
- **Fable 5.1 on the per-failure path.** Frequent, bounded investigations don't need the top tier once templates force
  evidence. Fix: §5 routing.
- **Memory scaffolding on S-scope tasks.** A `.mission/` directory for a typo fix is ceremony. Fix: §6.1 S row.
- **Eval-suite bloat.** Adding an eval case per trivial lesson, then running the whole suite at high effort. Fix: only
  promoted lessons get cases; the grader runs Sonnet 4.6 low with binary assertions; retire cases that pass on baseline.
- **Separate vector DB / memory service by default.** CL-Bench found "naive ICL outperforms systems dedicated to memory
  management". Fix: plain files first; add retrieval only if a measured load budget is exceeded that the curator can't
  fix.
- **Duplicating CLAUDE.md into STATE.md** (or the reverse). It gets paid for twice in every session, and contradictions
  appear ("Claude may pick one arbitrarily", https://code.claude.com/docs/en/memory).

**Platform assumptions**
- **Assuming personal skills load in cloud runs.** They don't ("not Cowork or cloud sessions",
  https://code.claude.com/docs/en/skills). Vendor the skill for Routines/CMA.
- **Depending on auto memory for mission facts.** It's local by default, capped on load, and not code-reviewed
  (https://code.claude.com/docs/en/memory; https://archcore.ai/blog/claude-code-memory/).

## 9. Open questions / risks for the synthesizer

1. **The hook scripts in §7.9 are untested.** The sandbox was unavailable in this lane (every `bash`/`run_commands`
   call failed with "Sandbox … is not ready (state: failed)"). The JSON block format, exit-code semantics, the
   `stop_hook_active` field, SessionStart `compact` re-injection and the 8-block cap are sourced. The `source` field
   name in SessionStart input, `CLAUDE_PROJECT_DIR`, the `auto|manual` PreCompact matcher values, and `date -r <file>`
   portability on macOS are recalled or community-sourced (https://www.hookstack.app/hook/session-start-reinject-after-compact),
   not verified against the full hooks reference, which the fetch tool truncated. Run each script against a fixture
   `.mission/` and a deliberately failing case before shipping.
2. **Stop-hook ergonomics.** Stop fires at the end of every turn, not at session end. Even opt-in enforcement could nag
   in semi-interactive missions. An alternative is `SessionEnd` (verified to exist) for a final memory-debt record, but
   whether SessionEnd can block or inject wasn't verified. Recommendation: ship Stop enforcement off by default, on for
   headless/Routine runs.
3. **Thresholds are judgment calls, not measurements.** 150/100 lines, a ~3k-token loaded budget, 30 inbox entries, 40
   lessons, 5-session retirement, 90/14-day expiry. They're modelled on Claude Code's 200-line/25 KB auto-memory load
   cap and its CLAUDE.md <200-line guidance. The skill should expose them in `.mission/config`.
4. **ACE vs context rot.** ACE argues for comprehensive, growing playbooks (+10.6% on agents); Anthropic argues for
   minimal high-signal context. The §4.4 split (compact loaded index, comprehensive archive) is a reconciliation with
   no measured backing. A synthesizer eval could compare "index only" vs "full STATE" load on a real mission resume.
5. **Where do promoted lessons live when the skill is shared?** `~/.claude/skills/<skill>/references/lessons.md` is
   per-machine and doesn't load in cloud sessions. If the user runs Routines/CMA, lessons need a sync path (plugin
   repo PR). The post's "travels with you" is only locally true.
6. **Subagent persistent memory** (`memory:` frontmatter, `.claude/agent-memory/`) could serve recurring specialists.
   Its exact frontmatter and load behaviour were only verified through third-party sources. It also creates a second
   store that could violate one-home-per-fact. Recommendation: don't use it in v1.
7. **Auto memory interaction.** Auto memory may independently record mission facts (possibly stale ones) outside the
   repo. Whether to suggest `autoMemoryDirectory` or leave it alone is unresolved. The setting's name is third-party
   sourced (https://archcore.ai/blog/claude-code-memory/).
8. **The benchmark evidence is thin.** The stage-progression data is one task, 30 questions, best runs, from an X
   article. Don't encode model-capability claims ("Fable completes the progression") as routing rules. Encode the
   structure instead.
9. **Unverified post claims outside this lane that this design touches.** Fable 5/5.1 pricing, and Routines' 30-day /
   2-year retention terms (relevant to what memory files may contain in cloud runs). Sibling lanes should confirm.
10. **Human-in-the-loop for CLAUDE.md edits.** The user's arcwell repo has no CLAUDE.md/AGENTS.md at all (glob found
    none). Missions could propose one at the first retro, but the user's preference is unknown. The recommendation is
    to propose, not write.

## Sources (appendix)

Working notes gathered during research. Every URL below was fetched or surfaced through search in this lane; the
notes record what each source established.

- Brief: `research/mission-skill/00-brief.md` §3 steps 02, 03, 10, 11, 12 (lines 104–257); §5 format (298–317); §6 rules (319–334).

- Lance Martin (Anthropic), "Designing loops with Fable 5", X article 2026-06-09, canonical https://x.com/RLanceMartin/article/2064380553919676416 ; full-text clipping https://github.com/lchesupercool/ob-clippings/blob/main/2026-06/2026-06-10-designing-loops-with-fable-5.md . Facts: the 5-stage progression is HIS framing for "this task" (one SQL task from CL-Bench), run in CMA with memory (mounted filesystem shared across sessions). Sonnet 4.6 exits ~step 1 ("maybe prc instead of prc_usd?"), "To improve performance, task-specific memory instructions are needed." Opus 4.7 ~step 3, verification coverage 7–33%, median ~17%. Fable 5 strongest runs up to 73% (22 of 30), distills general rules. Quote "Rather than directly prompting and steering Fable 5 ... manage its own context (e.g., via memory)" is verified (post paraphrase accurate). Verifier sub-agent quote verified with added reason "because grading is done in an independent context window".
- CL-Bench paper: https://arxiv.org/abs/2606.05661 (Asawa, Glaze, Orlanski, ..., Zaharia, Gonzalez; submitted 4 Jun 2026). Berkeley Sky lab project https://sky.cs.berkeley.edu/project/continual-learning-bench/ ; site https://continual-learning-bench.com/ . Abstract: six domains; gain metric vs stateless baseline; "agents frequently overfit to immediate observations or fail to reuse knowledge across instances, and dedicated memory systems do not fix this -- in fact, naive ICL outperforms systems dedicated to memory management." → The benchmark is NOT Anthropic's (post says "from Anthropic's Continual Learning Bench 1.0" — misattribution).
- Claude Code memory docs https://code.claude.com/docs/en/memory : two systems (CLAUDE.md you write; auto memory Claude writes). Both "context, not enforced configuration"; to block actions use PreToolUse hook. Auto memory loaded every session "first 200 lines or 25KB"; scope per repository, shared across worktrees. CLAUDE.md scopes: managed policy, `~/.claude/CLAUDE.md`, `./CLAUDE.md` or `./.claude/CLAUDE.md`, `./CLAUDE.local.md`. Target <200 lines per CLAUDE.md; "If an entry is a multi-step procedure or only matters for one part of the codebase, move it to a skill or a path-scoped rule". Add to CLAUDE.md when "Claude makes the same mistake a second time". Contradicting rules → "Claude may pick one arbitrarily". Subagents can maintain own auto memory.

- Anthropic context engineering (Sep 29, 2025) https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents : context rot, "attention budget", "smallest possible set of high-signal tokens"; long-horizon techniques = compaction, structured note-taking, multi-agent architectures; "Structured note-taking, or agentic memory, is a technique where the agent regularly writes notes persisted to memory outside of the context window. These notes get pulled back into the context window at later times." (search snippet of same URL). Also: don't stuff "laundry list of edge cases" into prompts; curate canonical examples.
- API memory tool https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool : `{"type": "memory_20250818", "name": "memory"}`; client-side; files under `/memories`; "Claude automatically checks its memory directory before starting a task"; supports just-in-time retrieval; must restrict path traversal; available on Claude 4+ models.
- Hooks reference https://code.claude.com/docs/en/hooks : events verified incl. SessionStart ("When a session begins or resumes"), SessionEnd, UserPromptSubmit, Stop, StopFailure, SubagentStart/SubagentStop, TaskCreated/TaskCompleted, PreCompact, PostCompact, InstructionsLoaded, FileChanged, Setup. Hook handler types: shell commands, HTTP, MCP tool, LLM prompts, subagents.
- Claude Academy "Claude Code in Action · Hooks" https://academy.claude.com/courses/claude-code-in-action/hooks : CLAUDE.md instruction "a request, not a guarantee"; "to re-inject context after compaction, don't use PostCompact. Use SessionStart with the compact matcher"; exit 0 plain stdout added to context on SessionStart/UserPromptSubmit; exit 2 blocks (incl. Stop); exit 1 does NOT block; SessionStart ignores blocking.
- Amit Kothari, stop hooks (May 20, 2026) https://amitkoth.com/claude-code-stop-hooks/ : Stop block JSON `{"decision": "block", "reason": "..."}`; check `stop_hook_active` to avoid infinite loop; reason = next prompt, make it specific; test failure path deliberately. Third-party guide https://cc.bruniaux.com/guide/hooks-events-reference/ claims Stop hooks are overridden after 8 consecutive blocks; this is confirmed by the official best-practices page (below).
- HookStack "Re-inject context after compaction" https://www.hookstack.app/hook/session-start-reinject-after-compact : community SessionStart hook with `"matcher": "compact"` and `$CLAUDE_PROJECT_DIR/.claude/hooks/...` command, reading `input.session_id` and writing plain stdout into context (community source; the settings shape matches the official hooks guide https://code.claude.com/docs/en/hooks-guide).

- Managed Agents memory https://platform.claude.com/docs/en/managed-agents/memory : memory store = workspace-scoped collection of text docs; mounted as a directory in the session sandbox; "a note describing each mount is automatically added to the system prompt"; every change creates an immutable memory version (audit trail, point-in-time recovery); individual memories capped 100 kB (~25k tokens), max 10,000 memories per store, "Structure memory as many small focused files, not a few large ones."; attach only at session creation; `access` read_write | read_only; `instructions` ≤4,096 chars; beta header `agent-memory-2026-07-22` for store endpoints. Third-party: launched public beta April 23, 2026, mounts at `/mnt/memory/<slug>/` https://www.perea.ai/research/claude-managed-agents-memory-stores (unverified detail).
- Harness design for long-running apps (Prithvi Rajasekaran, Mar 24, 2026) https://www.anthropic.com/engineering/harness-design-long-running-apps : "A reset provides a clean slate, at the cost of the handoff artifact having enough state for the next agent to pick up the work cleanly." Sonnet 4.5 "context anxiety" → compaction alone insufficient, context resets essential (search snippet).
- Archcore blog (third-party, Jul/Sep 2026) https://archcore.ai/blog/claude-code-memory/ : auto memory = `~/.claude/projects/<project>/memory/` MEMORY.md index + topic files, on by default since v2.1.32 (Feb 5, 2026); only index first 200 lines/25KB loads; topic files on demand; `/memory` manages, `/context` shows loaded; `autoMemoryDirectory` setting; silent truncation history, overflow error v2.1.210; `.claude/rules/` with `paths:` globs; skill descriptions listed at start, body on invocation; subagent `memory: project` → `.claude/agent-memory/<name>/` committable; Claude Code does not read AGENTS.md directly — import `@AGENTS.md` or symlink. Version history claims = unverified against changelog.

- Claude Code best practices https://code.claude.com/docs/en/best-practices : "LLM performance degrades as context fills"; four gate strengths — in one prompt, `/goal` condition (separate evaluator re-checks after every turn), Stop hook ("Claude Code overrides the hook and ends the turn after 8 consecutive blocks" — VERIFIED official), verification subagent / dynamic workflow; "Have Claude show evidence rather than asserting success".
- Skill authoring best practices https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices : only name+description preloaded; SKILL.md loaded when relevant, additional files as needed; "Keep SKILL.md body under 500 lines"; description ≤1,024 chars, third person; "Does this paragraph justify its token cost?"; test with all models you plan to use.
- ACE paper (Zhang et al., Oct 2025) https://arxiv.org/html/2510.04618v1 : "brevity bias, which drops domain insights for concise summaries" and "context collapse, where iterative rewriting erodes details over time"; fix = Generator/Reflector/Curator roles, "incremental delta updates", "grow-and-refine"; +10.6% agents, +8.6% finance; adapts from natural execution feedback without labels. Implication: append/modify itemized entries, never let a model rewrite the whole memory file in one pass.
- arcwell evidence `arcwell/docs/handoff/2026-08-21-remediation-status.md`: companion doc defers to an "authoritative statement" (lines 3–6: single source of truth per fact kind); gate command for every landed item (lines 8–10); distilled rules phrased as general principles: "A budget ceiling is a WAIT, not a verdict" (line 168), "an in-memory harness cannot prove persistence" (lines 59–60); decision with reason "Deliberately NOT a new database state" (187–189); explicit evidence-level honesty: "backed by the repository's own gates ... None of it is backed by production behavior" (216–221). No CLAUDE.md/AGENTS.md/.claude under arcwell (glob returned no matches).

- Compound Engineering (Every; Klaassen & Chow) https://github.com/EveryInc/compound-engineering-plugin : loop "brainstorm, plan, build, review, then capture what you learned — so the knowledge from each change is written down where the next change can read it"; `/ce-compound` "Codify knowledge so it is reusable"; "A good compound note means the next agent does not have to learn the same lesson from scratch." Guide https://every.to/guides/compound-engineering (fetch returned empty shell).
- skill-creator SKILL.md (Anthropic) https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/plugins/skill-creator/skills/skill-creator/SKILL.md : `evals/evals.json` schema `{skill_name, evals:[{id, prompt, expected_output, files, assertions?}]}`; spawn with-skill AND baseline runs in same turn; results by `iteration-N/eval-K/`; SKILL.md <500 lines; references >300 lines need TOC; objectively verifiable skills benefit from evals.
- Claude Code skills docs https://code.claude.com/docs/en/skills : "Create a skill when ... a section of CLAUDE.md has grown into a procedure rather than a fact"; skill body loads only when used; Personal `~/.claude/skills/<skill-name>/SKILL.md` loads in "All your projects on this machine, but not Cowork or cloud sessions" (→ post claim "Skills live in ~/.claude/skills/ and travel with you" is only true locally). KEY: bundled `/verify` records a recipe in `.claude/skills/verify/SKILL.md`; "Claude edits the recorded file only when it steered a run wrong, such as a command that failed or a missing step, so you can commit the file without per-session diffs. Before v2.1.205, the bundled skill told Claude to fold in anything a run learned, which caused frequent merge conflicts." → Anthropic's own evidence against "write every lesson into the skill".

