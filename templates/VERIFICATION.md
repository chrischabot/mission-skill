# Verification · <M<n> | T-NNN> · candidate <sha> · base <sha> · verifier <mission-critic | mission-verifier> · <YYYY-MM-DDTHH:MMZ>

<!-- Template: skills/mission/templates/VERIFICATION.md → .mission/verification/VERIFICATION-<M>.md.
     Rules: references/testing.md W-3, V-1, V-2, G-4..G-8, H-1. The verifier returns this document as its whole reply;
     the orchestrator saves it verbatim. Graders and reviewers accept only this file plus the raw logs it links.
     Every PASS cites a gate row or log line; an uncited PASS is UNVERIFIED. Report every run, not only the green one.
     Delete this comment before returning. -->

## 1. Environment

- Worktree: <path> · clean checkout at <sha> · `git status --porcelain` before: <empty>
- Toolchain: node <v> · package manager <v> · wrangler/miniflare <v> · Workers Vitest integration <@cloudflare/vitest-plugin
  | @cloudflare/vitest-pool-workers> <v> · Playwright <v> · Xcode <v> · simulator <name, runtime, udid, erased: yes>
- Network guard: <on (tests/setup/no-network.ts)> · credentials present in the test environment: <none>
- Inputs read: `.mission/TEST-PLAN.md` · `.mission/acceptance.json` · <spec excerpts> · maker transcript: NOT READ

## 2. Frozen paths

| Check | Command | Exit | Result |
|---|---|---|---|
| Base manifest copy | `git show <base>:.mission/frozen-manifest.sha256 > .mission/tmp/base-manifest` | <0> | <n entries> |
| Manifest check | `.mission/bin/frozen-manifest.sh check --manifest .mission/tmp/base-manifest` | <0 | 1> | <OK | CHANGED/MISSING/ADDED lines> |

## 3. Gate runs (executed by this verifier)

| Gate | Command | Exit | Passed | Failed | Skipped | Flaky | Duration | Log |
|---|---|---|---|---|---|---|---|---|
| <lint+typecheck> | `<pnpm lint && pnpm typecheck>` | <0> | – | – | – | – | <41s> | `.mission/logs/<M>/lint.txt` |
| <integration> | `<pnpm vitest run --project integration --reporter=json --outputFile=...>` | <0> | <212> | <0> | <0> | – | <96s> | `.mission/logs/<M>/integration.json` |
| <e2e web> | `<npx playwright test --reporter=json>` | <0> | <9> | <0> | <0> | <0> | <3m10s> | `.mission/logs/<M>/pw.json` |
| <e2e iOS> | `<timeout 1800 xcodebuild test ...>` | <0 | 65 | 124 timeout> | <n> | <n> | <n> | – | <n> | `.mission/logs/<M>/ui.xcresult` |

Skipped or flaky tests on gating suites (each needs a quarantine row, else the gate fails):
<test — O-NNN / quarantine row — criteria now UNVERIFIED | none>

Gates not run here: <gate — reason (no simulator | no browser | no network) — criteria UNVERIFIED | none>

## 4. Red-before-green

New or changed oracles must fail on base with the expected symptom and pass on the candidate.

| ID | Test (path::name) | On base <sha> | On candidate | Failing message on base (expected symptom?) |
|---|---|---|---|---|
| <API-001> | `<tests/acceptance/outfits.test.ts::@req:API-001 save persists order>` | <FAIL> | <PASS> | <"expected 201, received 404" · yes> |

Nondeterministic fixes: p measured <k/N on the unfixed code> · α <0.05 | 0.01> · state reset <yes | no → n doubled> ·
n required <n> · consecutive clean runs <n> · command `<scripts/flake-runs.sh ...>` · log <path>

## 5. Test-quality proof

- Oracle-bite (S/M, every fix): <semantic break applied in scratch worktree, e.g. "removed tenant filter at
  src/repo/outfits.ts:42"> → <test> <FAILED as expected with "<message>" | PASSED (weak oracle → FAIL)> · worktree discarded
- Adapter oracle-bites (K-3): <adapter — proof removed — test failed: yes/no>
- Targeted mutation (L/XL critical files): `<command>` · killed <k>/<n> · survivors: <id — weak-oracle | equivalent
  (reason, mission-reviewer)> · harness errors (not kills): <n>
- Held-out scenarios (H-1): <n run · n pass · failures: message handed to maker, test withheld | not enabled>

## 6. Test-diff audit (`templates/test-diff-audit.md`)

- Pre-pass: `.mission/bin/test-diff-grep.sh --base <base>` → exit <0 | 1> · flags: <FLAG lines | none> · dispositions
  cited: <quarantine row / D-entry per flag | none>
- Checklist answers: <Q1..Q10 with file:line or "none">
- Bloat audit: <tests without @req, duplicates, higher-level duplicates | none>
- Audit verdict: CLEAN | BLOCKING(<list>) | ADVISORY(<list>)

## 7. Coverage from code

`grep -rn "@req:" <test dirs>` → <n citations, n distinct IDs> · required IDs with no passing oracle: <list | none> ·
tests citing unknown IDs: <list | none> · broad tests that are sole oracle for >3 unrelated required criteria: <list | none>

## 8. Criteria matrix

| ID | Required | Oracle(s) | Result | Evidence |
|---|---|---|---|---|
| <API-001> | yes | `<…::@req:API-001 …>` | PASS | §3 row integration (212 passed, log line <n>); §4 row 1 |
| <PAY-004> | yes | `<…::@req:PAY-004 …>` (quarantined) | UNVERIFIED | quarantine row O-007, expires M2 Verify |
| <LIVE-002> | yes | `<pnpm canary:imagegen>` | UNVERIFIED | canary not run here → gate PENDING-LIVE |

## 9. Verdict

Mechanical: every required criterion PASS and audit not BLOCKING and manifest OK and no expired quarantine → PASS ·
any required FAIL or BLOCKING audit or manifest mismatch → FAIL · otherwise UNVERIFIED.

**Verdict: <PASS | FAIL | UNVERIFIED>** — <one line>.
FAIL IDs: <list | none> · UNVERIFIED IDs: <list with reason | none> · PENDING-LIVE: <list | none>
Workspace clean after (`git status --porcelain` empty): <true | false>
Commands run: <exact list, in order>
