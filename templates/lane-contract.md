# Lane contract (swarm extension to the task brief)

<!-- Template: skills/mission/templates/lane-contract.md. Rules: references/swarms.md SW11–SW24, P3, P5.
     Use: fill templates/brief.md, then append the "Swarm lane contract" block below it (after "Ownership and
     boundaries" content, before "Return format"), and REPLACE the brief's text return block with the JSON return below.
     Save the result to .mission/lanes/<T-NNN>/brief.md and commit it on the integration branch before dispatch.
     Verifier lanes do not get this block: they use templates/gate-verifier.md.
     Keep <placeholders> in angle brackets until filled; delete lines marked (optional) that do not apply. -->

---

## Swarm lane contract

### Identity
- Lane id: `<T-NNN>` (idempotency key: reuse on every retry) · Wave: `W<k>` · Attempt: `<1 | 2 (narrowed)>`
- Pattern / role: <fan-out maker | mechanical maker | reader | per-item verifier | experiment lane H-<NNN> | candidate <k> of <N>>
- Agent: `<mission-worker | mission-worker-high | mission-builder | mission-scout>` · model `<claude-sonnet-4-6 | claude-opus-4-8>`
- Mission: `<mission>` · integration tip at dispatch: `<sha>`

### Ownership
- Branch: `claude/<mission>/<T-NNN>-<slug>` (created from the integration tip above; never another branch)
- Worktree: `<isolation: worktree | .claude/worktrees/<T-NNN>>` (spawned from the primary checkout)
- owns (you MAY create or edit only these; new directories listed literally):
  - `<apps/api/src/outfits/**>`
  - `<tests/unit/outfits/**>`
  - `.mission/lanes/<T-NNN>/**` (always yours)
- reads (frozen, never edit): `.mission/CONTRACTS.md#<section>` (contract v<n>), `.mission/CONTEXT.md`,
  `.mission/SPEC.md#<section>`, `<other paths>`
- needs (already integrated before you start): <T-NNN: one-line scope | none>
- Siblings in this wave (awareness only; never edit their paths, never coordinate with them):
  <T-NNN: one-line scope>, <T-NNN: one-line scope>
- Anything outside `owns` must change → stop, return `BLOCKED` with `blocked_reason: "ownership"` and the path.
- A frozen contract must change → stop, return `BLOCKED` with `blocked_reason: "contract-change"` and the proposal.

### Runtime isolation
- `PORT=<base + 10 × lane index>` · `DB_NAME=<name>_<T-NNN>` (or schema `<name>_<T-NNN>`)
- Simulator device: `<UDID | none>` · derived data: `<path | none>` (optional)
- `TMPDIR=.mission/tmp/<T-NNN>/` · caches: `<shared read-only store | per-lane dir>`
- Never bind default ports, never use the shared dev database, never touch another lane's simulator.
- Environment missing (dependency, `.env`, service) → return `BLOCKED` with `blocked_reason: "env"`; do not "fix" code
  to work around the environment.

### Checkpoints and resume
- First action: if `.mission/lanes/<T-NNN>/progress.md` exists, read it and continue from its last `next`. Do not redo
  completed steps.
- After every major step append one line: `<UTC time> · <step> · <result> · next: <next step>`.
- Commit on your branch at least every 3 steps with message `<T-NNN>: <summary>`. Commit before returning, whatever
  the status.
- Save check output to `.mission/lanes/<T-NNN>/evidence/<AC-NNN>.log` (last 50 lines is enough).
- Write large files section by section; never compose a large artifact in one tool call.

### Stall contract
- Time box: `<minutes>` · tool-call cap: `<n>` · fix iterations: `<n>`.
- Same error signature twice after a fix attempt → stop, return `STALLED` (`stalled_reason: "same-error"`).
- No newly passing check within `<m>` tool calls → stop, return `STALLED` (`stalled_reason: "no-progress"`).
- Context above ~60% → checkpoint, return `STALLED` (`stalled_reason: "context"`) with `proposed_split`.
- The orchestrator retries once with a narrower brief on the same branch, then escalates one rung, then marks the task
  `STALLED` for the human queue. You never retry yourself beyond the caps above.
- Safety refusal → return `BLOCKED-SAFETY`. Do not rephrase, split or obfuscate the task.
- You never spawn agents, push, merge, open PRs, or edit `.mission/STATUS.md`, `STATE.md`, `acceptance.json`.

### Output
- Code on your branch + `.mission/lanes/<T-NNN>/{progress.md,evidence/,return.json}` committed.
- Final message = the same JSON as `return.json`, nothing else, ≤400 words.

---

## Return schema (JSON Schema 2020-12; also usable as a workflow `schema`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LaneReturn",
  "type": "object",
  "required": ["lane_id", "status", "summary", "branch", "commit", "files_changed", "outside_ownership", "checks", "artifacts", "model_used", "memory_delta", "next"],
  "additionalProperties": false,
  "properties": {
    "lane_id": { "type": "string", "pattern": "^T-[0-9]{3,}(-[a-z0-9-]+)?$" },
    "status": { "enum": ["DONE", "STALLED", "TEST-DISPUTE", "BLOCKED", "BLOCKED-SAFETY"] },
    "blocked_reason": { "enum": ["ownership", "contract-change", "conflict", "env", "missing-context", "other", null] },
    "stalled_reason": { "enum": ["same-error", "no-progress", "context", "time-box", "budget", null] },
    "verdict": { "enum": ["PASS", "FAIL", "UNVERIFIED", null], "description": "per-item verifier lanes inside a workflow only" },
    "summary": { "type": "array", "items": { "type": "string" }, "maxItems": 6 },
    "branch": { "type": "string" },
    "commit": { "type": ["string", "null"] },
    "files_changed": { "type": "array", "items": { "type": "string" } },
    "outside_ownership": { "type": "array", "items": { "type": "string" }, "description": "must be empty when status is DONE" },
    "checks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "result", "evidence"],
        "properties": {
          "id": { "type": "string", "pattern": "^AC-[0-9]{3}$" },
          "result": { "enum": ["PASS", "FAIL", "UNVERIFIED"] },
          "evidence": { "type": "string", "description": "log path, file:line or URL; self-check only, the verifier decides" }
        }
      }
    },
    "findings": {
      "type": "array", "maxItems": 8,
      "items": {
        "type": "object", "required": ["claim", "pointer", "confidence"],
        "properties": {
          "claim": { "type": "string" },
          "pointer": { "type": "string" },
          "confidence": { "enum": ["VERIFIED", "SECONDARY", "INFERENCE"] }
        }
      }
    },
    "assumptions": { "type": "array", "items": { "type": "string" } },
    "out_of_scope_findings": { "type": "array", "items": { "type": "string" } },
    "proposed_split": { "type": "array", "items": { "type": "string" } },
    "contract_change": { "type": ["string", "null"], "description": "section, current, proposed, why, lanes affected" },
    "artifacts": { "type": "array", "items": { "type": "string" } },
    "model_used": { "type": "string", "enum": ["claude-sonnet-4-6", "claude-opus-4-8", "claude-fable-5-1"] },
    "memory_delta": { "type": "string", "description": "the <memory_delta> block (templates/memory-delta.md) or a path to .mission/lanes/<T-NNN>/memory-delta.md" },
    "next": { "type": "string" }
  }
}
```

## Orchestrator acceptance (deterministic, before any model reads the return)

| # | Check | Fail → |
|---|---|---|
| 1 | Final message parses as JSON and validates against the schema | `STALLED` (invalid return) |
| 2 | `status: DONE` ⇒ every `checks[].result` is `PASS` with non-empty `evidence`, and `outside_ownership` is empty | `STALLED` |
| 3 | `commit` exists on `branch` (`git cat-file -e <commit>` and `git branch --contains <commit>` lists the lane branch) | `STALLED` |
| 4 | `git diff --name-only <integration tip>...<branch>` ⊆ owns globs ∪ `.mission/lanes/<T-NNN>/**` | `BLOCKED(ownership)`; revert nothing, return the lane |
| 5 | Every evidence path exists on the branch | `STALLED` |
| 6 | `BLOCKED` has `blocked_reason`; `STALLED` has `stalled_reason`; `contract-change` has `contract_change` | `STALLED` |

Only then dispatch the per-lane verifier (`templates/gate-verifier.md`) with the branch, AC ids and rubric; never pass
this return or its summary to the verifier.

## Example return (filled)

```json
{
  "lane_id": "T-014",
  "status": "DONE",
  "blocked_reason": null,
  "stalled_reason": null,
  "verdict": null,
  "summary": ["Added POST /v1/outfits handler per CONTRACTS §1", "Validation errors map to VALIDATION (§2)", "Unit tests for create and duplicate name"],
  "branch": "claude/fashion-app/T-014-api-outfits",
  "commit": "a1b2c3d",
  "files_changed": ["apps/api/src/outfits/create.ts", "tests/unit/outfits/create.test.ts", ".mission/lanes/T-014/progress.md"],
  "outside_ownership": [],
  "checks": [
    { "id": "AC-021", "result": "PASS", "evidence": ".mission/lanes/T-014/evidence/AC-021.log" },
    { "id": "AC-022", "result": "PASS", "evidence": ".mission/lanes/T-014/evidence/AC-022.log" }
  ],
  "findings": [],
  "assumptions": ["A-new: outfit names unique per user, not globally (reversal cost: low)"],
  "out_of_scope_findings": ["apps/api/src/auth/refresh.ts:88 swallows refresh errors"],
  "proposed_split": [],
  "contract_change": null,
  "artifacts": [".mission/lanes/T-014/progress.md", ".mission/lanes/T-014/evidence/"],
  "model_used": "claude-sonnet-4-6",
  "memory_delta": ".mission/lanes/T-014/memory-delta.md",
  "next": "verify T-014, then integrate before T-016 (imports outfits client)"
}
```
