# HANDOFF · <mission name> · session s<N> → s<N+1> · <YYYY-MM-DDTHH:MMZ>

<!-- Template: skills/mission/templates/HANDOFF.md → .mission/HANDOFF.md. Owner: orchestrator.
     Written at session end, before a context reset, or when context use passes ~60% (references/orchestration.md L2,
     memory-and-lessons.md MEM-32). Overwritten each time; history lives in git (archive/ for superseded copies).
     Write STATE.md → Resume FIRST, then this file, then commit .mission/. Point to files; never paste logs.
     A fresh agent with no chat history must be able to take the next action from this file alone. -->

## Orientation
- Repository: <path or URL> · Primary checkout: <path>
- Branch: `<claude/<mission>/integration>` @ `<commit sha>` · Default branch: `<main>` @ `<sha>`
- Worktrees in flight: <`<path>` → `claude/<mission>/<T-NNN>-<slug>` | none>
- Environments: <dev/staging URLs, simulator names, deployed resources with ids>
- Phase: <n name> · Class: <S|M|L|XL> · Orchestrator: <claude-fable-5-1 @ medium> · Profile: <standard|lean|degraded>
- Stop state: <RUNNING|STOP-SUCCESS|STOP-IMPOSSIBLE|STOP-BUDGET|STOP-STALLED|STOP-GUARDRAIL|BLOCKED-HUMAN|BLOCKED-SAFETY>

## Read next, in order
1. This file.
2. `.mission/STATUS.md` → header, Gates, Board, Human queue.
3. `.mission/STATE.md` → Resume, Rules index, Open failures.
4. `.mission/PLAN.md` → READY tasks of <milestone>.
5. `git log --oneline -20`, then run the smoke check: `<command>` (expect: <exit 0 / output line>). Red → fix first.

## What changed this session
- Tasks PASSED: <T-NNN> (evidence: `.mission/lanes/<T-NNN>/verify-<n>.yaml`) · <…>
- Gates advanced: <phase or milestone> → <PASSED | PASSED-WITH-WAIVER(D-NNN) | PENDING-LIVE> (evidence: <path>)
- Decisions: <D-NNN title> · Assumptions added: <A-NN> · Stop rules fired: <T-NNN STOP-STALLED → escalated>

## In flight (do not restart blindly)
| Task / loop | State | Iter | Agent (rung) | Where | Last output | Hypothesis / next step |
|---|---|---|---|---|---|---|
| <T-NNN> | <IN-PROGRESS | VERIFYING | STALLED> | <2/5> | <mission-worker-high> | <worktree path, lanes/<T-NNN>/progress.md> | <.mission/logs/<AC-NNN>-<ts>.log> | <…> |

## Verified facts this session (how verified)
- <fact> · `<command>` → `<salient output line>` (exit <n>) · recorded as <F-NNN>

## Not available to the next agent
- <credentials, devices, human-only steps, rate-limited or paid services, anything needing the owner's identity>

## Human queue waiting
- <decision> · default taken meanwhile: <x> · blocks: <T-ids> · since <YYYY-MM-DD>

## Next 3 actions (priority order)
1. <action as a runnable command or a brief to dispatch> · expected evidence: <exit 0 / file / screenshot>
2. <action> · expected evidence: <…>
3. <action> · expected evidence: <…>

## Risks / open questions
- <risk> · default assumption <A-NN> · owner: <role> · tracked in <O-NNN | FND-id | STATUS Risks>

## Budget
- Mission spend: <used> / <soft cap> soft · <hard cap> hard · this session: <used> · source: <headless total_cost_usd | usage view>

## Verification bar (run before claiming anything)
`<single command line, e.g. .mission/check.sh all && pnpm test && pnpm build>`
