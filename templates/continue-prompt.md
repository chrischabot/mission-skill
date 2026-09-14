# Continuation prompt · headless `claude -p` or Routine

<!-- Template: skills/mission/templates/continue-prompt.md. Rules: references/orchestration.md L1–L7, H1, PM1–PM4.
     Fill the placeholders, save the "Prompt" block as .mission/tmp/continue-prompt.txt (headless) or paste it as the
     Routine prompt. It MUST be self-contained: a Routine or headless run has no chat history, no approval prompts and
     no human to ask. The skill must be available to the run: personal skills do not load in cloud sessions, so vendor
     it into the repository's .claude/skills/mission/ for Routines (memory-and-lessons.md CMP-09).
     Never start the run with --bare: it skips skills, agents, hooks and CLAUDE.md, so the mission would run without
     its process. Set .mission/config enforce_stop=1 and autonomous=1 for these runs. -->

## Prompt

```text
You are continuing mission "<mission name>" in <repository> using the `mission` skill (.claude/skills/mission/SKILL.md).
This prompt is self-contained. There is no human available during this run. Load references/conventions.md and
references/orchestration.md first.

1. Session start (L1): read .mission/HANDOFF.md → .mission/STATUS.md (header, Gates, Board, Human queue) →
   .mission/STATE.md (Resume, Rules index, Open failures) → .mission/PLAN.md (READY tasks) → `git log --oneline -20`.
   Run the smoke check `<smoke command>`. If it is red, repairing it is this run's first task.
2. Check the active model at start and at every phase boundary: the orchestrator is <claude-fable-5-1 @ medium>.
   Log any drift or classifier fallback in STATUS.md → Model / fallback events.
3. Scope of this run: milestone <M<n>> only; at most <k> tasks; <phase names allowed, e.g. Build and Verify>.
   Use templates/brief.md for makers and templates/gate-verifier.md for verifiers. Makers never grade themselves.
4. Obey stop rules S1–S7 and the loop caps in .mission/loops/. Hard limits for this run: <n> turns, <t> wall-clock
   minutes, budget <USD> (the launcher also passes --max-budget-usd). At 80% of the run budget, stop dispatching new
   work and go to step 7.
5. Never perform irreversible or externally visible actions: deploys, data migrations on shared data, pushes to the
   default or protected branches, merges, publishing, spending, messaging people, CI/workflow/secret changes. Queue each
   one in STATUS.md → Human queue with the default you would take, mark the task BLOCKED-HUMAN, and continue other work.
6. Autonomous mode: do not ask questions. Take the documented default, log it in ASSUMPTIONS.md as ASSUMED
   (unconfirmed) or as a D-entry, and continue. A safety refusal is BLOCKED-SAFETY; never rephrase around it.
7. Before exiting, even on a stop rule: update STATUS.md (board, gates, budget, stop-rule log), rewrite STATE.md →
   Resume, write HANDOFF.md, run .mission/bin/memory-lint.sh until exit 0, and commit to branch
   claude/<mission>/run-<YYYYMMDD>-<n>. <Allowed: push that branch and open a DRAFT pull request | Not allowed: leave the
   commit local>.
8. Print a digest of at most 10 lines: tasks PASSED (with evidence paths), gates changed, stop state, spend this run,
   new Open failures, Human queue items, next action.

Success for this run = the digest is printed AND STATUS.md, STATE.md and HANDOFF.md are committed on the run branch.
Stop after <n> turns regardless.
```

## Launch recipes

Headless (local, CI or cron). Capture cost per run; the JSON result carries `total_cost_usd` (client-side estimate):

```bash
claude -p "$(cat .mission/tmp/continue-prompt.txt)" \
  --model claude-fable-5-1 \
  --output-format json \
  --max-budget-usd <remaining hard cap for this run> \
  > ".mission/logs/run-<YYYYMMDDTHHMMZ>.json"
```

- Do not add `--bare`. If a harness forces bare mode, pass the skill, agents and settings explicitly (`--add-dir`,
  `--agents`, `--settings`) and record a D-entry.
- If `claude --help` does not list `--max-budget-usd`, drop the flag and enforce the cap from BUDGET.md between runs.
- Exit code non-zero or 143 (SIGTERM, unfinished turn): the next run resumes from HANDOFF.md; do not start fresh.
- Record the run in BUDGET.md → spawn log from the JSON result (per-model breakdown shows fallbacks).

Routine (Anthropic cloud; schedule, API or GitHub trigger):

- Prompt: the block above, pasted verbatim (no references to chat history).
- Repository with the vendored skill and `.mission/` committed; hooks from `.claude/settings.json` in the repo.
- Model: <claude-fable-5-1> selected per routine. Connectors: only those the mission needs, read-only where possible;
  every action appears under the owner's identity.
- Branches: Routine output lands on `claude/`-prefixed branches; merges stay a human action.
- Optional `/goal` as the prompt's last line MAY nudge the run, never gates it:
  `/goal .mission/STATUS.md and .mission/HANDOFF.md were committed this run and the digest was printed, or stop after <40> turns`
