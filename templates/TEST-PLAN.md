# Test plan · <mission name> · class <M | L | XL> · shape <GRN | FEA | BUG | MIG | REF | UPG | DAT | PRF | INF | SEC | WEB>

<!-- Template: skills/mission/templates/TEST-PLAN.md → .mission/TEST-PLAN.md (M+; S missions use the task card's
     "Test first" line instead). Rules: references/testing.md T-1..T-6, B-1..B-8, G-1, E-1, E-5, K-3/K-4/K-8.
     Written by the test strategist before implementation; reviewed inside the Phase 2 spec gate (mission-critic).
     This file plans oracles. Coverage is computed by the verifier from @req: citations in code, never from this
     table. Point to other files; do not copy requirement text that lives in SPEC.md. Delete this comment. -->

## Goal (one sentence; an outcome, not an activity)

<e.g. "A signed-in user can generate, save and reopen an outfit from their wardrobe on iOS, persisted in D1.">

Done means: every required criterion below PASS in the verifier's run on the final integrated commit, no blocking
test-diff audit finding, clean frozen-manifest check, no expired quarantine (testing.md V-2).

## Frozen paths (implementer may read and run, never write)

Mirror of `.mission/frozen-paths.txt`. Freeze with `.mission/bin/frozen-manifest.sh add '<glob>'` after the tests are
proven red; the verifier checks the base commit's manifest copy.

- tests/acceptance/**
- tests/regression/**
- tests/golden/**
- <shared test setup / fixtures the oracles import, e.g. tests/setup/**, packages/testkit/fakes/**>
- <test configs: playwright.config.*, vitest.config.*, jest.config.*, stryker.config.*, *.xctestplan>
- <CI workflows: .github/workflows/**>
- .claude/hooks/**, .claude/settings.json
- <visual-tolerance configs listed by frontend-verification.md>

Deny rules (layer a; same path form as `templates/settings.guardrails.json`). Deny binds the whole session, test
author included: put every frozen glob into the settings file of separately launched implementer lanes; merge into
`.claude/settings.json` at setup only the paths nobody in the session writes later (CI, hooks, settings, pre-recorded
goldens). One Edit + one Write rule per glob:

```json
[
  "Edit(./tests/acceptance/**)", "Write(./tests/acceptance/**)",
  "Edit(./tests/regression/**)", "Write(./tests/regression/**)",
  "Edit(./tests/golden/**)", "Write(./tests/golden/**)",
  "Edit(./<test config, e.g. playwright.config.ts>)", "Write(./<test config>)",
  "Edit(./.mission/frozen-paths.txt)", "Write(./.mission/frozen-paths.txt)",
  "Edit(./.mission/frozen-manifest.sha256)", "Write(./.mission/frozen-manifest.sha256)"
]
```

Guardrail self-test (Procedure step 3): `protect-frozen.sh --self-test` → <PASS · date> · live probe from a
sub-agent → <refused Edit + refused Bash append | NOT BLOCKED → D-<NNN>> · recorded as <F-NNN>.

## Gates for this class and shape

From the gate table in `references/testing.md` (Scale by class). One row per gate the verifier runs. Required gates
block DONE; "unavailable" gates keep their criteria UNVERIFIED with the reason (never a mock substitute).

| Gate | Command (exact, JSON reporter where available) | Required | Runs where | Timeout |
|---|---|---|---|---|
| Build + typecheck + lint | `<pnpm lint && pnpm typecheck && pnpm build>` | yes | verifier worktree | <5m> |
| Unit + property | `<pnpm vitest run --project unit --project property --reporter=json --outputFile=.mission/logs/<M>/unit.json>` | yes | verifier worktree | <10m> |
| Integration (real local runtime) | `<pnpm vitest run --project integration --reporter=json --outputFile=.mission/logs/<M>/integration.json>` | yes | verifier worktree | <15m> |
| Security | `<pnpm vitest run --project security --reporter=json ...>` | <yes at L/XL> | verifier worktree | <10m> |
| API E2E | `<pnpm test:api-e2e>` against `<wrangler dev --local | staging URL>` | <yes | no> | verifier worktree | <10m> |
| Web E2E journeys | `<npx playwright test --reporter=json>` | <yes | no> | verifier worktree | <20m> |
| iOS E2E journeys | `<timeout 1800 xcodebuild test -scheme <App>UITests -destination 'platform=iOS Simulator,id=<udid>' -resultBundlePath .mission/logs/<M>/ui.xcresult>` after `xcrun simctl erase <udid>` | <yes | no> | <macOS runner> | 30m |
| Traceability lint | `<python3 .mission/bin/validate-registry.py --registry .mission/requirements.yaml --tests <dirs> --spec .mission/SPEC.md>` | <yes at L/XL> | verifier worktree | 2m |
| Frozen manifest | `.mission/bin/frozen-manifest.sh check --manifest .mission/tmp/base-manifest` | yes | verifier worktree | 1m |
| Diff pre-pass | `.mission/bin/test-diff-grep.sh --base <base>` | yes | verifier worktree | 1m |
| Targeted mutation | `<npx stryker run --incremental --mutate <critical files>>` · `<cargo mutants --in-diff <diff>>` | <yes L/XL critical | no> | verifier worktree | <30m> |
| AI eval suite | `<pnpm eval:<behaviour> --trials 3>` · threshold <pass rate ≥ n%> | <yes if AI behaviour> | verifier worktree | <n> |
| Canary | `<pnpm canary:<name>>` · spend ceiling <$n> · cleanup read-back `<command>` | before release | test account, human checkpoint if spend | <n> |
| Link check + Lighthouse (WEB) | `<lychee ./dist>` · `<lhci autorun>` (≥3 runs, assertions in lighthouserc) | <yes for WEB> | verifier worktree | <10m> |

Unavailable here: <gate — reason — criteria that stay UNVERIFIED — what would settle it | none>

## Criteria → oracles (traceability matrix)

Budget per criterion: 1 specific oracle + ≤2 edge/negative cases (B-1). Lowest observing level (B-6). Oracle names
carry `@req:<ID>` (T-2). Status ∈ PLANNED · RED-PROVEN · PASS · FAIL · UNVERIFIED(<reason>) · QUARANTINED(<O-NNN>).

| ID | Criterion (observable) | Priority | Level | Oracle kind | Oracle (path::name) | Extra cases (≤2, why) | Red-before-green (commit · failing message) | Status |
|---|---|---|---|---|---|---|---|---|
| <API-001> | <POST /outfits persists items in order and returns 201 with id> | P1 | integration | integration | `tests/acceptance/outfits.test.ts::@req:API-001 save persists order` | <empty wardrobe → 422> | <abc1234 · "expected 201, received 404"> | PLANNED |
| <API-002> | <outfit list is tenant-scoped> | P1 | integration | integration | `tests/acceptance/security/tenancy.test.ts::@req:API-002 cross-tenant read denied` | — | <…> | PLANNED |
| <IOS-003> | <generate → save → relaunch shows the saved outfit> | P1 | e2e | e2e | `ios/AppUITests/OutfitJourneyTests.swift::testIOS003_generateSaveReopen` | — | <…> | PLANNED |

Sole-oracle check (T-4): no broad E2E/scenario test is the only oracle for more than 3 unrelated P1 criteria.
<list any test that is sole oracle for ≥2 criteria, with the IDs>

## Budget exceptions (anything over 1 oracle + 2 cases)

- <API-00x: +1 property test, input space wardrobe sizes 0..500 — kills survivor M-3 | none>

## Golden journeys (E-1: M 1–3 through the new surface · L 3–7 per surface · XL ≤12)

| Journey | Surface | Steps (user-visible) | Seed | Outcome asserted | Criteria observed | Test |
|---|---|---|---|---|---|---|
| <J-1 save outfit> | <iOS> | <sign in → generate → save → relaunch> | <`-uiTestSeed wardrobe_basic`> | <saved outfit visible after relaunch, D1 row exists> | <IOS-003, API-001> | `<path::name>` |

## Property / model-based tests (B-4: model from the spec, never from the code)

| Machine / domain | Spec source (transition table) | Generator size / runs | Test |
|---|---|---|---|
| <subscription lifecycle> | <SPEC.md#billing-states> | <10,000 sequences, fixed seed> | `<path::name>` |

## Fakes, fixtures and canaries

| Provider / boundary | Deterministic fake (behind port) | Oracle-bite test (proof removed → fails) | Golden fixture (normalised, versioned) | Canary (ceiling · cleanup read-back) |
|---|---|---|---|---|
| <image model API> | `<packages/testkit/fakes/imagegen.ts>` seed <n> | `<path::bite missing image id fails>` | `tests/golden/imagegen/v1/*.json` | `<pnpm canary:imagegen>` · <$2> · <lists and deletes test objects> |

Network guard (K-1): `<tests/setup/no-network.ts>` loaded by every test project · credentials in ordinary runs: none.

## AI/LLM evals (if the mission has AI behaviour)

| Behaviour | Tasks (≥20) | Trials per task (≥3) | Code grader | Rubric grader (mission-verifier) + calibration set | Pass threshold |
|---|---|---|---|---|---|
| <outfit suggestion respects dress code> | <evals/dress-code/*.json, n> | 3 | <structured output schema + rule checks> | <rubric path · ≥20 labelled cases · agreement ≥90%> | <≥ 85% of trials> |

## Critical modules (mutation at L/XL, oracle-bite at S/M)

| Module / files | Why critical | Tool + command | Survivors policy |
|---|---|---|---|
| <src/domain/billing/**> | <money> | `<npx stryker run --mutate src/domain/billing/**/*.ts>` (vitest.related:false for fetch-driven suites) | block until killed or marked equivalent with a reason by mission-reviewer |

## Held-out scenarios (verifier-owned, H-1)

Enabled: <no | yes (L/XL, or after a cheating signal on <date>)> · count: <1–3 per epic> · stored: <outside the maker's
worktree>. Contents are never listed here.

## Flake / quarantine register (E-5)

A quarantined test does not gate; its criteria are UNVERIFIED. Expiry ≤ 2 phase gates ahead; an expired row is a
failing gate. Retries never above 2. Fix proof: n ≥ ln(α)/ln(1−p) consecutive clean runs with state reset.

| Test | Open failure | First seen | Measured p (failures/runs) | α | n required | Owner | Expires at gate | Criteria now UNVERIFIED |
|---|---|---|---|---|---|---|---|---|
| <tests/e2e/checkout.spec.ts::@req:PAY-004 pays> | <O-007> | <YYYY-MM-DD> | <3/150> | <0.01> | <228> | <T-031> | <M2 Verify> | <PAY-004> |

## Test disputes

See `.mission/reviews/test-disputes.md`. Open: <none | TEST-DISPUTE <n> (<test>) → D-<NNN> pending>
