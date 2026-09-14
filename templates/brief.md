# Task brief · <T-NNN> · <one-line title>

<!-- Template: skills/mission/templates/brief.md. The orchestrator fills every <placeholder> and sends everything below
     the line as the Agent-tool prompt for the roster agent named in PLAN.md (conventions §7). Rules: references/
     orchestration.md W4, W7–W10. Maker and test-author briefs only: VERIFIER briefs use templates/gate-verifier.md and
     receive artifact + criteria + evidence only (never this brief's summary or the maker's return).
     Swarm lanes append the extension in templates/lane-contract.md. Escalation rungs use templates/escalation-brief.md.
     Keep the stable parts first (cache-friendly): role and context pointers before task specifics.
     Never paste whole files or raw logs; point to paths. Delete this comment and any section marked (optional) that
     does not apply. -->

---

## Role
You are the <maker | test author | investigator | researcher> for task <T-NNN> of mission "<mission name>".
Agent: `<mission-worker | mission-worker-high | mission-builder | …>`. You work in a fresh context: everything you
need is below or linked. You do not grade your own work; an independent verifier will re-run every check.

## Objective (outcome, not steps)
<What must be true when you are done, in 1–3 sentences, observable by a verifier.>

## Why it matters
<1–2 sentences linking to milestone <M<n>> and outcome <OUT-NNN>, so you can make sensible local trade-offs.>

## Read first (read these, not the whole repository)
- `.mission/CONTEXT.md` — commands, conventions, frozen and forbidden paths, return format
- `<path or URL>` — <why it matters for this task>
- Requirements: <REQ ids with `.mission/SPEC.md#<section>`> · Contracts: <`.mission/CONTRACTS.md#<section>` | none>
- Decisions: <D-NNN> · Assumptions: <A-NN> · Rules and lessons to consult: <R-NNN, L-NNN> (say which you applied)

## Ownership and boundaries
- You MAY create or edit only: `<glob>`, `<glob>`. Anything else needs changes → stop and report it under NEXT.
- Read-only (frozen): `.mission/frozen-paths.txt` entries, `.mission/acceptance.json`, `.mission/STATE.md`,
  `.mission/STATUS.md`, `<tests/acceptance/**>`.
- Work in: `<worktree path>` on branch `claude/<mission>/<T-NNN>-<slug>` (spawned from the primary checkout). Commit
  there with message `<T-NNN>: <summary>`. Never push, merge, deploy or open PRs.
- Forbidden: deleting, skipping, loosening or special-casing tests or checks; editing CI/workflows, hooks, settings or
  secrets; network writes to real services; installing global tools; <project-specific>.
- A test or check that looks wrong: stop and return `STATUS: TEST-DISPUTE` with a filled `templates/TEST-DISPUTE.md`
  (references/testing.md W-5). Do not change the test.
- A frozen contract that needs changing: stop and return `BLOCKED(contract-change)`.

## Acceptance checks you must satisfy
| AC id | Type | How to prove it |
|---|---|---|
| <AC-NNN> | executable | `<command>` exits 0 from the repository root; save output to `.mission/lanes/<T-NNN>/<AC-NNN>.log` |
| <AC-NNN> | rubric | <criterion text copied verbatim>; attach <screenshot path + pixel box | file:line> |

## Steps (Sonnet-class makers; omit for outcome-style briefs to Opus/Fable agents)
1. Read the files above. Run the checks once and save the red output (expected red before your change).
2. <step>
3. <step>
4. Run every check above; fix until green or until the budget below is spent.
5. Write progress after each major step to `.mission/lanes/<T-NNN>/progress.md` (if it already exists, resume from
   the last checkpoint instead of restarting). Write large artifacts section by section, never in one tool call.

## Budget and stop rules
- Max <n> fix iterations · stop after <m> tool calls without a newly passing check · wall-clock <t> minutes.
- Same error signature twice after a fix attempt → stop, return `STALLED` with your best hypothesis and the log path.
- Context above ~60% → checkpoint `progress.md`, return `STALLED(context)` with what remains.
- Safety refusal → stop, return `BLOCKED-SAFETY`. Do not rephrase, split or obfuscate the task.

## Return format (exactly this, ≤400 words plus pointers)
```text
STATUS: DONE | STALLED | STALLED(context) | TEST-DISPUTE | BLOCKED(<reason>) | BLOCKED-SAFETY
SUMMARY: <3–6 bullets: what changed>
FILES CHANGED: <paths> · COMMIT: <sha on claude/<mission>/<T-NNN>-<slug>>
CHECKS: <AC-NNN> = PASS|FAIL · evidence: <log path or file:line> (self-check; the verifier decides)
ASSUMPTIONS MADE: <A-new: statement, reversal cost> | none
OUT-OF-SCOPE FINDINGS: <issue with file:line> | none
NEXT: <what the orchestrator should do next> | none
<memory_delta> … </memory_delta>   (skeleton and rules: templates/memory-delta.md)
```
A return without evidence paths counts as FAIL.
