# CONTEXT · <mission name>

<!-- Shared context every sub-agent brief points to. Keep it stable (cache-friendly) and short (≤120 lines).
     Point to files; never paste large content. Owner: orchestrator. Update at phase boundaries only. -->

## Mission in one paragraph
<Outcome from CHARTER.md, restated for a worker who knows nothing else.>

## Repository orientation
- Stack: <languages, frameworks, runtimes and versions>
- Layout: <top-level directories and what lives where>
- Primary checkout: <path> · integration branch: `claude/<mission>/integration` · lane branches: `claude/<mission>/<lane-id>-<slug>`

## Commands (verified; each with how it was verified)
| Purpose | Command | Verified |
|---|---|---|
| Install | `<cmd>` | <date, exit 0> |
| Build | `<cmd>` | |
| Typecheck / lint | `<cmd>` | |
| Unit / integration tests | `<cmd>` | |
| E2E (web / iOS) | `<cmd>` | |
| Smoke check (run at every session start) | `<cmd>` | |
| Milestone gate | `.mission/check.sh <milestone>` | |

## Conventions to follow
- <naming, error handling, logging, dependency rules, existing ID scheme, design system/tokens path>
- Reuse before building: <components, helpers, adapters with paths>
- Test conventions: tests cite `@req:<ID>`; fakes live in <path>; network guard <path>

## Frozen and forbidden
- Frozen paths (read, never write): see `.mission/frozen-paths.txt`
- Never: delete/skip/weaken tests; edit `.mission/acceptance.json`, `STATE.md`, `STATUS.md`; push to the default branch;
  deploy; touch secrets or CI workflows; rephrase around a safety refusal.
- If a test looks wrong: STOP and file a TEST-DISPUTE.

## Contracts (if any)
- See `.mission/CONTRACTS.md` (frozen). A lane that needs a change returns `BLOCKED(contract-change)`.

## Runtime isolation for parallel lanes
- Ports: base <n> + 10 × lane index · Database/schema: `<name>_<lane-id>` · Simulator: one device per lane · Temp dir: `.mission/tmp/<lane-id>/`

## Rules to consult (IDs from STATE.md → Rules index)
- <R-NNN one-line rule> (applies when …)

## Return format (all makers)
STATUS · SUMMARY · FILES CHANGED · CHECKS (id = PASS|FAIL · evidence path) · ASSUMPTIONS · OUT-OF-SCOPE FINDINGS ·
memory_delta · NEXT — ≤400 words plus pointers. Large outputs go to `.mission/lanes/<lane-id>/`, written incrementally.
