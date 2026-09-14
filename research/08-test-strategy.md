# 08 · Test strategy: hard tests that measure real success without ballooning

Researcher report for the `/drive` skill. Date 2026-09-14. Sources are marked as **verified** (checked today, URL given), **probe** (measured on this machine today), **source claim** (the post or a secondary source, unverified), or **opinion** (mine, argued).

## 1. Executive opinion

The skill should treat testing as the mechanism that decides whether work is done, not as a phase that produces files. Everything else in this report follows from three commitments.

First, a test exists to refute a claim. The specification phase must end with a numbered list of behavioral claims in plain words, and the test-design phase must produce exactly one refutation test per claim at the cheapest layer that can genuinely refute it. A second test on the same claim needs a stated reason (an independent oracle for critical code, a boundary the first test cannot reach, or a bug that actually happened). This single rule is what stops ballooning: the budget is the claim count, and a reviewer can detect bloat by counting tests that have no claim.

Second, the harness must be at least as strict as production. The owner's D1 incident was not bad luck; it was a shim that let 24 green runs certify a query that could never run live. I probed the real local D1 today: it rejects the 101st bound variable, so the runtime that would have caught the bug was already in the toolchain. The skill must default to real runtimes (workerd through the Cloudflare Vitest plugin, the iOS simulator, a real browser under Playwright) and, wherever a shim is unavoidable, write down where it is kinder than the real thing and add a guard or a live check for each entry.

Third, the agent that wrote the code must not be the agent that decides the tests are sufficient. A verifier with fresh context reads the claim list, runs the tests, breaks a line of production code and expects red, and assigns the status. Its output is the only thing that moves a claim up the ladder from Local Proof to Live Proof.

The deliverable that ties this together is `TESTPLAN.md`: one row per claim, naming the test, its layer, its status and the evidence path. The verifier audits that table; the state file records what it downgraded. Without the table, "tests pass" is a sentence; with it, it is a checkable fact.

## 2. What the post says, and a critique

The post says almost nothing specific about testing, which is itself the problem. Its testing content amounts to five sentences: Fable "writes its own tests to check its work"; a "verifier sub-agent tends to outperform self-critique"; vision compares a screenshot against the goal; the example skill carries the anti-pattern "never disable a failing test to make CI green"; and an eval suite should "run weekly". It also proposes Haiku for graders.

Where it is right: the verifier separation is the correct structural move, and it is the one part of the testing story that matters most for agents. A model grading its own tests sees the reasoning that produced them and will rate a stub as evidence. The "never disable a failing test" rule is right and should be broadened (Section 4.10).

Where it is exaggerated: "writes its own tests" is presented as a capability when it is, unsupervised, the source of the mirage. A maker that writes both code and tests will write tests that pass; that is what optimising toward green means. The post never says who decides whether those tests could fail. It also treats vision as a self-verification primitive, but a screenshot is a weak oracle for the claims that matter in a dashboard or an outfit recommender (is the number right, is the outfit the one the rules say it should be). Vision catches layout and state rendering; it does not catch off-by-one in a total.

Where it is wrong for this owner: Haiku graders are ruled out by the brief (Sonnet at low effort instead). "Run weekly" is a scheduler-wait; his rule is to drive systems through their own tools now. And the post has no notion of harness fidelity or of a test budget, the two things he explicitly asked for. The "known failure modes" section it proposes for skills is good, and this report feeds it: the D1 incident becomes a general rule about shims, not a note about SQLite.

## 3. Verified facts

Cloudflare Workers testing, as of today:

- The Vitest integration package was renamed on 2026-08-19 from `@cloudflare/vitest-pool-workers` to `@cloudflare/vitest-plugin` ("Version 1"); a codemod exists: `npx @cloudflare/codemods vitest:pool-workers-to-vitest-plugin`. https://developers.cloudflare.com/changelog/post/2026-08-19-vitest-plugin/
- Install line in the docs: `npm i -D vitest@^4.1.0 @cloudflare/vitest-plugin`. Config uses `cloudflareTest({ wrangler: { configPath } })` as a Vite plugin; tests import `env`/`exports` from `cloudflare:workers` and helpers from `cloudflare:test`; types come from `@cloudflare/vitest-plugin/types`. https://developers.cloudflare.com/workers/testing/vitest-integration/write-your-first-test/
- npm registry today: `@cloudflare/vitest-plugin` latest 1.1.8 with peer `vitest ^4.1.0`; `vitest` latest is **5.0.0**, so the plugin does not yet accept Vitest 5 and the pin `vitest@^4.1.0` is mandatory. (registry.npmjs.org, fetched 2026-09-14.)
- `cloudflare:test` helpers: `createExecutionContext`, `waitOnExecutionContext`, `createScheduledController`, `createMessageBatch`, `getQueueResult`, `runInDurableObject`, `runDurableObjectAlarm`, `evictDurableObject`, `listDurableObjectIds`, `abortAllDurableObjects`, `reset`, `applyD1Migrations`, and for Workflows `introspectWorkflowInstance`/`introspectWorkflow` with modifiers `disableSleeps`, `disableRetryDelays`, `mockStepResult`, `mockStepError`, `forceStepTimeout`, `mockEvent`, `forceEventTimeout`. https://developers.cloudflare.com/workers/testing/vitest-integration/test-apis/
- Known limitations: no native V8 coverage (use Istanbul); fake timers do not affect KV/R2/cache simulators; storage isolation is per test file, not per test, and requires awaiting all storage operations and consuming response bodies; WebSockets with Durable Objects need `--max-workers=1 --no-isolate`; global setup runs in Node, not workerd. https://developers.cloudflare.com/workers/testing/vitest-integration/known-issues/
- Configuration options include `wrangler.configPath`, `wrangler.environment`, `main`, and a `miniflare` block (`bindings`, `d1Databases`, `kvNamespaces`, `r2Buckets`, `queueProducers/Consumers`, `durableObjects`, `workflows`, `serviceBindings`, `compatibilityFlags`, `workers`); `readD1Migrations` is exported from the plugin package. https://developers.cloudflare.com/workers/testing/vitest-integration/configuration/
- Official example fixtures (D1 with migrations, Durable Objects, Queues, Workflows, request mocking with `@msw/cloudflare`, multiple workers, AI/Vectorize mocks) live under https://github.com/cloudflare/workers-sdk/tree/main/fixtures/vitest-plugin-examples/ ; I read the D1, Workflows, Queues and request-mocking test files directly from that tree.
- A second, newer integration path exists: `createTestHarness()` from `wrangler`, which runs production Worker builds from any Node test runner, supports multiple Workers, `server.fetch`, `worker.scheduled`, `worker.getEnv()`, `worker.applyD1Migrations("DB")`, `worker.getDurableObjectStorage`, `server.getLogs()`, `server.reset()`, and Workflow introspection. https://developers.cloudflare.com/workers/testing/test-harness/get-started/ , https://developers.cloudflare.com/workers/testing/test-harness/prepare-test-state/ , https://developers.cloudflare.com/workers/testing/test-harness/interact-with-workers/
- Local development defaults to local simulation; `remote: true` per binding connects a locally running Worker to deployed resources. Recommended remote: Workers AI, Browser Rendering, Vectorize, mTLS, Images. Cannot be remote: Durable Objects, Workflows, vars, secrets, static assets, Analytics Engine, Rate Limiting, Hyperdrive. `wrangler dev --remote` is legacy. https://developers.cloudflare.com/workers/development-testing/
- D1 limits: 100 bound parameters per query; 100,000 bytes per SQL statement; 30 s per query; 1,000 queries per invocation (Paid); 2,000,000 bytes per row/string/blob; 100 columns per table; 32 arguments per SQL function; 50 bytes per LIKE/GLOB pattern; 10 GB per database. https://developers.cloudflare.com/d1/platform/limits/
- D1 local vs remote: `wrangler d1 migrations apply DB --local` and `--remote`; `wrangler d1 execute DB --local|--remote --command|--file --json --yes`; `wrangler d1 export`; `wrangler d1 time-travel info|restore DB --timestamp|--bookmark` (restore is destructive, in place, and returns a bookmark to undo; 30-day window on Paid). https://developers.cloudflare.com/d1/wrangler-commands/ , https://developers.cloudflare.com/d1/reference/time-travel/
- Versions and previews: `wrangler versions upload [--preview-alias name --tag t --message m]` creates a version with a preview URL `<prefix-or-alias>-<worker>.<subdomain>.workers.dev`; `wrangler versions deploy <id>@10% <id>@90% -y` splits traffic non-interactively; `wrangler rollback [VERSION_ID] --message ""` skips prompts; `wrangler deploy --dry-run --outdir`. Preview URLs are **not generated for Workers that implement a Durable Object**, and preview traffic has no `wrangler tail`/logs. https://developers.cloudflare.com/workers/wrangler/commands/workers/ , https://developers.cloudflare.com/workers/configuration/previews/ , https://developers.cloudflare.com/workers/configuration/versions-and-deployments/gradual-deployments/
- `wrangler tail [WORKER] --status ok|error|canceled --method --search --format json|pretty --sampling-rate --header --ip self --version-id`; max 10 concurrent tail clients; high-traffic Workers sample. https://developers.cloudflare.com/workers/observability/logs/real-time-logs/
- Cron triggers are tested locally by hitting `http://localhost:8787/cdn-cgi/local/scheduled?cron=*+*+*+*+*&time=<ms>` while `wrangler dev` runs. https://developers.cloudflare.com/workers/configuration/cron-triggers/
- Workflows: local dev needs Wrangler 3.89+; `wrangler workflows trigger|list|instances describe --local` (4.79+); a Local Explorer UI at `/cdn-cgi/local/explorer` (4.82.1+); Workflows cannot be remote bindings. https://developers.cloudflare.com/workflows/build/local-development/
- Queues locally: producer and consumer run together; consumer concurrency is not supported locally; no remote mode. https://developers.cloudflare.com/queues/configuration/local-development/

**Probe, this machine, 2026-09-14** (plugin 1.1.4, wrangler 4.129.0, miniflare 5.20260903.0-alpha, vitest 4.1.11, run in a throwaway scratchpad project): against the local D1 simulator, a prepared statement with 101 bound parameters throws `D1_ERROR: too many SQL variables ... SQLITE_ERROR`; 100 succeeds; 101 in an `IN (...)` list throws; a 101 KB statement throws `SQLITE_TOOBIG`; a 101-column `CREATE TABLE` throws `D1_EXEC_ERROR`. The local simulator did **not** enforce the 50-byte LIKE pattern limit (a 62-byte pattern ran) nor the 2 MB row limit (a 2.1 MB insert succeeded). So the real local runtime would have caught the owner's bug, and it still has two documented kindnesses that a ledger must record.

Frontend web:

- Playwright `toHaveScreenshot` options and defaults: `threshold` 0.2 (YIQ colour distance per pixel, 0 strict to 1 lax), `maxDiffPixels`/`maxDiffPixelRatio` unset by default, `animations: "disabled"`, `caret: "hide"`, `scale: "css"`, `mask`, `maskColor`, `stylePath`, `fullPage`; snapshots are named `{test}-{browser}-{platform}.png` and the docs warn rendering varies by OS/hardware, so baselines must be generated where they are compared. https://playwright.dev/docs/api/class-pageassertions , https://playwright.dev/docs/test-snapshots
- Playwright CLI: `--repeat-each N`, `--retries N`, `--fail-on-flaky-tests`, `--last-failed`, `--only-changed`, `--update-snapshots all|changed|missing|none`, `--trace retain-on-failure`, `--forbid-only`, `--shard`. Tests are labelled passed / flaky (failed then passed on retry) / failed. https://playwright.dev/docs/test-cli , https://playwright.dev/docs/test-retries
- Accessibility: `@axe-core/playwright` (4.13.0 today) with `new AxeBuilder({ page }).withTags([...]).include().exclude().disableRules().analyze()`; the fixture pattern is documented. https://playwright.dev/docs/accessibility-testing . Deque's study: automated axe rules find about 57% of issues by volume (source claim from the vendor). https://www.deque.com/blog/automated-testing-study-identifies-57-percent-of-digital-accessibility-issues/
- Lighthouse CI (`@lhci/cli` 0.15.1): `lighthouserc.js` with `ci.collect` (`url`, `staticDistDir`, `startServerCommand`, `numberOfRuns`), `ci.assert` (`preset`, `assertions`, `budgetsFile`), `ci.upload`. https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md
- Vitest 5.0.0 Browser Mode is stable; providers `playwright` (recommended), `webdriverio`, `preview`; `vitest-browser-react` 2.3.0 supports Vitest 4 and 5 and React 18/19; locators via `page` from `vitest/browser`. https://vitest.dev/guide/browser/
- StrykerJS: `@stryker-mutator/vitest-runner` 10.0.0 supports only the threads pool, not Browser Mode, forces per-test coverage, and says nothing about custom pools. https://stryker-mutator.io/docs/stryker-js/vitest-runner/

Native iOS:

- This Mac has Xcode 27.0 (build 27A5209h, the RC line) with Swift 6.4, and iOS 26.4 simulator runtimes installed (no iOS 27 runtime yet); `wrangler` 4.127.1 is on PATH; Node 26.8.1. (Local `xcodebuild -version`, `swift --version`, `xcrun simctl list runtimes`.) The task prompt's "Xcode 17 / Swift 6-era" framing is stale: Apple moved to year numbering with Xcode 26 in 2025, and Xcode 27 RC ships Swift 6.4 and requires macOS Tahoe 26.6. https://developer.apple.com/documentation/xcode-release-notes/xcode-27-release-notes
- Xcode 27 testing changes (release notes, verbatim items): UI-test crash severity is configurable in the test plan (off / warning / failure / fatal); a launch-test file template opts into `runsForEachTargetApplicationUIConfiguration` (every orientation, localization and appearance); a Swift Testing and XCTest Interoperability setting controls cross-framework assertions; `XCUIVoiceOverService` is a new API for driving and verifying VoiceOver from UI tests; parameterized Swift Testing suites are much faster; Test Repetition Mode now repeats individual Swift Testing cases; parameterized test links include an argument hash. Same URL.
- Swift Testing: `@Test`, `@Suite`, `#expect`, `#require`, traits (`.tags`, `.disabled`, `.enabled(if:)`, `.timeLimit`, `.serialized`, `.bug`), parameterized tests, parallel by default, exit tests, attachments; UI testing is not supported, keep XCUITest for that. https://developer.apple.com/documentation/testing
- `xcodebuild -help` on this machine lists `-only-testing:ID`, `-skip-testing:ID`, `-testPlan`, `-resultBundlePath`, `-enableCodeCoverage`, `-parallel-testing-enabled`, `-test-iterations N`, `-retry-tests-on-failure`, `-run-tests-until-failure`, `-test-repetition-relaunch-enabled`, `-test-timeouts-enabled`, `-default-test-execution-time-allowance`, `-collect-test-diagnostics on-failure|never`.
- `xcrun xcresulttool get test-results summary|tests|test-details|activities|insights|metrics --path X.xcresult` is the current (non-legacy) interface; the pre-Xcode-16 `get object` needs `--legacy`. (Local `xcrun xcresulttool help get test-results`; https://developer.apple.com/forums/thread/763050 )
- Swift Testing test identifiers in `-only-testing` were reported to need doubled parentheses (`Target/Suite/test()()`) because xcodebuild strips one pair; verify on Xcode 27 before relying on it. Source claim: https://trinhngocthuyen.com/posts/tech/swift-testing-and-xcodebuild/
- `xcrun simctl` subcommands present locally include `boot`, `install`, `launch`, `terminate`, `io` (screenshot/recordVideo), `status_bar`, `ui`, `privacy`, `push`, `openurl`, `location`, `keychain`, `get_app_container`, `erase`, `reboot` (new in Xcode 27), `spawn`. (Local `xcrun simctl help`.)
- `XCUIApplication.performAccessibilityAudit(for:_:)` (iOS 17+) audits contrast, dynamicType, elementDetection, hitRegion, sufficientElementDescription, textClipped, trait; the closure receives an `XCUIAccessibilityAuditIssue` and returns whether to ignore it. https://developer.apple.com/videos/play/wwdc2023/10035/ , https://www.polpiella.dev/xcode-15-automated-accessibility-audits/
- swift-snapshot-testing 1.19.4 (2026-07-28): `assertSnapshot(of:as:)`, strategies `.image`, `.recursiveDescription`, `.json`, `.dump`; SwiftUI `.image(drawHierarchyInKeyWindow:precision:perceptualPrecision:layout:traits:)` where `precision` is the share of pixels that must match and `perceptualPrecision` is how closely a pixel must match (98–99% "mimics the human eye"); record modes `.all/.failed/.missing/.never` via `withSnapshotTesting(record:)` or `@Suite(.snapshots(record:))`; the README insists snapshots be compared on the same simulator that recorded them. https://github.com/pointfreeco/swift-snapshot-testing
- Muter (Swift mutation testing): last GitHub release is tag 16 dated 2023-09-16. https://github.com/muter-mutation-testing/muter/releases

Harness (Claude Code):

- Hooks include `Stop`, `SubagentStop`, `PreToolUse`, `PostToolUse`, `SessionStart`; a `Stop` hook can block completion by exiting 2 or returning `continueDecision: "block"` with a `blockReason`, and the docs' own example runs the test suite in that hook. https://code.claude.com/docs/en/hooks
- Available in this environment (tool schemas loaded this session): an iOS Simulator MCP with `build`/`build_status` (headless `xcodebuild`) and `control` actions `attach`, `launch`, `screenshot`, `inspect` (accessibility tree as JSON with frames), `tap`, `swipe`, `touch_path`, `text`, `button`, `open_url`; a Chrome DevTools MCP with `lighthouse_audit`, `take_screenshot`, `take_snapshot`, `performance_start_trace`; a Playwright MCP with `browser_snapshot`, `browser_take_screenshot`, `browser_network_requests`.

## 4. Detailed spec

### 4.1 Philosophy the skill must enforce

**Claims before tests.** The spec phase ends with `SPEC.md` containing a numbered list of acceptance criteria written as behavioral claims in plain language: "When the wardrobe has more than 100 items, the brief still builds", "Deleting an outfit removes it from every list within one refresh", "The dashboard total equals the sum of the rows shown". A claim names an observable outcome, not an implementation. If a criterion cannot be phrased as something a test could observe, it is not a criterion yet and the spec is sent back.

**One refutation test per claim, at the cheapest honest layer.** The test designer maps each claim to the lowest layer whose harness can actually refute it. Pure logic (outfit scoring, date bucketing) is refuted at unit level. A claim about storage or a binding (a query, a queue message, an alarm) is refuted inside workerd through the Vitest plugin, never through a hand-written fake of the binding. A claim about wiring (the app shows what the server returned) is refuted end to end, once. Choosing a lower layer than the claim needs is the most common way a suite goes green while the product is broken.

**A second test needs a reason.** Allowed reasons, each written into the test's comment: an independent oracle for critical code (a total recomputed from fixtures, not read from the UI); a boundary the first test cannot reach (the 100th and 101st item); a bug that actually happened (the regression test keeps the incident number). Anything else is deleted at review.

**What is never tested directly.** Constructors, getters and setters, type-level facts the compiler already checks, framework behavior (that the router routes, that SwiftUI renders a `Text`), third-party libraries, private helpers reached through reflection, log wording, and "snapshot everything" captures of whole pages or JSON blobs without a named reason. The one accepted snapshot is a golden output where the entire artifact is the claim (a rendered email, a CLI's `--help`, a generated SQL statement), and it is stored inline where possible so a reviewer can read the diff.

**Budget heuristics per scope.** The budget is counted in claims, never in lines or coverage points:

| Scope | Budget |
|---|---|
| Bug fix | 1 failing reproduction that becomes the regression test; at most 1 neighbouring boundary test if the fix changed a limit. |
| Feature | 1 test per claim, plus 1 severe test per trust boundary the feature crosses (auth, tenant, external input, money), plus 1 end-to-end run per user-visible flow. |
| Greenfield module | claims + the number of external limits it touches (each documented platform limit the module can hit gets a boundary test at N and N+1). |
| Migration | characterization corpus + parity diff + cutover check + rollback drill (Section 4.7); feature tests only for behavior that is meant to change. |

Two smell thresholds the reviewer applies mechanically: if the test file is more than three times the size of the code it covers and the code is not a parser or state machine, the tests are asserting on implementation; if a module has more tests than claims and no bug references, the extra tests are bloat.

**How a reviewer detects a useless test.** Ask, in order: Would this test still pass against a stub that returns constants? Does it assert that a mock was called rather than that the outcome happened? Does it duplicate another test's oracle on the same claim? Is its name a paraphrase of the code rather than of a claim? If the production line it targets is deleted, does it still pass? (The verifier does this last check by hand on the most important claims; Section 4.9.) Any yes marks the test for deletion, and the deletion is recorded in the state file so the decision is auditable.

**Flake policy.** A flake is a test that fails and then passes with no code change. The skill never deletes one silently and never adds blanket retries to the main lane. On first observation: reproduce deliberately (`npx playwright test --repeat-each 20 <file>`, `npx vitest run --retry 0 <file>` in a loop, `xcodebuild test ... -test-iterations 20 -run-tests-until-failure`), fix it in the same run if the cause is shared state, ordering or a real race with a cheap fix, otherwise quarantine it: mark it skipped with a reason that carries a ticket id, add an entry under "Open failures" in `STATE.md` with the reproduction command and the current hypothesis, and move it to a non-blocking lane that still runs so the data keeps accumulating. On second observation of the same test with the same workaround, stop: the first diagnosis was wrong, and the root cause hunt becomes the task (Section 4.8). Flaky tests that guard money, auth or data loss cannot be quarantined; they block.

**Mutation testing, worth it or not.** Opinion: as a gate, no; as a tool the verifier uses by hand, always; as an automated pass, only on pure-logic modules that carry money, auth or data-loss claims, and only in incremental mode. StrykerJS runs Vitest only in the threads pool and does not know about custom pools, so it cannot exercise tests that run inside workerd; this is a second argument (beyond speed) for keeping scoring, pricing and validation logic in pure modules with Node-runnable tests, and for keeping binding code thin. On iOS, Muter's last release is from 2023 and Swift 6.4 toolchains are unlikely to be a comfortable fit; do not spend a run discovering that. The manual form is what matters: for each of the top five claims, the verifier flips the operator or deletes the line the claim depends on, runs the named test, and expects red. A test that stays green under that flip is not a test.

### 4.2 Harness fidelity

The owner's incident, restated as a rule: a harness that is more permissive than production certifies broken code, and the number of green runs is not evidence. The probe in Section 3 sharpens this: the real local D1 rejects the 101st variable, so the shim was not just kinder than production, it was kinder than the free local runtime. The first rule of fidelity is therefore not "write stricter shims" but "stop writing shims where a real runtime exists".

**Rules the skill enforces.**

1. Prefer the platform's own runtime. Workers code runs under workerd via `@cloudflare/vitest-plugin` or `createTestHarness()`; iOS code runs in the simulator; browser code runs in a browser (Playwright, or Vitest Browser Mode with the playwright provider). `jsdom` is allowed only for hooks and pure view logic that never measures layout. `sql.js`, hand-rolled `D1Database` fakes, in-memory KV maps and similar are banned when the real local binding exists.
2. Where no local runtime exists (Workers AI, Vectorize, Browser Rendering, third-party HTTP APIs), the test double must be at least as strict as production in every dimension you can name: limits, timeouts, auth, quotas, error shapes, eventual consistency. The Cloudflare recommendation for those bindings is `remote: true`, which the Vitest plugin supports; use it in the integration lane against a test account, and use `@msw/cloudflare` in the fast lane with handlers that return the provider's real error payloads for the failure cases.
3. Every shim ships with a kindness ledger. Before any test runs against a double, the test designer fills in a table in `TESTPLAN.md` (template below) listing each production constraint the double does not enforce, and for each one either a guard in production code with its own unit test, or a live check that crosses the limit, or an explicit "accepted risk" line signed by the verifier.
4. Probe the harness, do not trust the docs about it. For each platform in play, the skill generates a `limits.probe.test.ts` (or Swift equivalent) that exercises the documented limits against the local harness and prints which are enforced. Today's probe took under a minute and produced two ledger entries that no documentation states. The probe is rerun when the toolchain version changes (record the versions in the ledger row).
5. Encode limits as named constants in production code and test the guard, not the platform. `D1_MAX_BOUND_PARAMS = 100` with a `chunkBinds()` helper and a test at 100 and 101 is a permanent fix; a comment in a query is not.

**"Where is this shim kinder than the real thing" checklist.** Run it against every double, and against the local runtime itself:

- Counts and sizes: parameters per query, statement length, row size, columns per table, payload size, batch size, list lengths, header count and length, file size, page size.
- Time: request timeout, query duration, CPU time per invocation, alarm granularity, sleep durations that the local runtime skips, clock skew between services, timezone of the runtime (UTC in production).
- Rate and quota: requests per second, subrequests per invocation, queries per invocation, daily quota, billing tier limits, concurrent connections, tail sampling.
- Auth and identity: does the double skip token validation, accept expired tokens, ignore scopes, ignore tenant boundaries, treat every caller as the owner.
- Consistency and ordering: eventual consistency of KV and R2 listings, single-threaded Durable Objects, queue redelivery and out-of-order delivery, local Queues lacking consumer concurrency, retries the local runtime does not perform.
- Failure shapes: does the double ever return the real error codes and payloads (429 with `Retry-After`, 5xx, partial writes, cancelled queries at restore time), or only success.
- Data realism: one item versus a thousand; ASCII versus Unicode normalisation variants; empty strings versus nulls; a wardrobe of 3 versus 300.
- Environment: cold start behavior, missing secrets, a compatibility date older than production, Node compatibility flags on locally but off in `wrangler.jsonc`.

### 4.3 Backend testing on Cloudflare Workers

**Lanes.** Three lanes, each with its own command, each recorded in `TESTPLAN.md`:

- Fast lane (every edit, under two minutes): unit and binding-level tests inside workerd via the Vitest plugin, with `@msw/cloudflare` for outbound HTTP.
- Integration lane (before a status change to Local Proof): `createTestHarness()` against the production build, multiple Workers when the design has them, plus the limits probe.
- Live lane (required for Live Proof): a preview version or a staging environment on Cloudflare, smoke requests, `wrangler tail`, remote D1 reads, a cost sanity count.

**Setup skeleton.**

```bash
npm i -D vitest@^4.1.0 @cloudflare/vitest-plugin @msw/cloudflare msw
```

`vitest.config.ts`:

```ts
import path from "node:path";
import { cloudflareTest, readD1Migrations } from "@cloudflare/vitest-plugin";
import { defineConfig } from "vitest/config";

export default defineConfig(async () => {
  const migrations = await readD1Migrations(path.join(import.meta.dirname, "migrations"));
  return {
    plugins: [
      cloudflareTest({
        main: "./src/index.ts",
        wrangler: { configPath: "./wrangler.jsonc" },
        miniflare: {
          bindings: { TEST_MIGRATIONS: migrations },
          // remote bindings for things with no local simulator, integration lane only:
          // set `remote: true` on the AI binding in wrangler.jsonc for that lane
        },
      }),
    ],
    test: { setupFiles: ["./test/apply-migrations.ts"], include: ["test/**/*.test.ts"] },
  };
});
```

`test/apply-migrations.ts`:

```ts
import { applyD1Migrations } from "cloudflare:test";
import { env } from "cloudflare:workers";
await applyD1Migrations(env.DB, env.TEST_MIGRATIONS);
```

`test/tsconfig.json` adds `"types": ["@cloudflare/vitest-plugin/types"]`.

**Per-binding approach.**

- D1: tests run real SQL against the workerd D1 with migrations applied in setup. Every query module gets a boundary pair at the documented limit (100 binds, 100 KB) and the production code carries `chunkBinds()`. Remote parity: `wrangler d1 execute DB --remote --json --command "SELECT COUNT(*) FROM items"` in the live lane, and `wrangler d1 migrations list DB --remote` to prove the schema matches.
- KV and R2: real local simulators; remember fake timers do not expire keys, so TTL claims are tested by asserting the `expirationTtl` argument at the write site plus one live check.
- Durable Objects: `runInDurableObject(stub, (instance, state) => ...)` for internal state, `runDurableObjectAlarm(stub)` to fire alarms deterministically, `listDurableObjectIds(ns)` for existence claims. Because DOs cannot be remote and get no preview URLs, their live proof runs in a staging environment (`wrangler deploy --env staging`).
- Queues: `exports.default.queue("queue", messages)` (needs the `service_binding_extra_handlers` compatibility flag per the official fixture) or `createMessageBatch` + `getQueueResult`, asserting `explicitAcks`, `retryMessages`, and the resulting storage state. Consumer concurrency does not exist locally, so any claim about parallel consumers is live-lane only.
- Workflows: `introspectWorkflow(env.WF)` with `modifyAll(m => { m.disableSleeps(); m.mockStepResult({ name }, value) })`, then `waitForStatus("complete")` and `getOutput()`; use `await using` so instances are disposed. Test the retry path with `mockStepError({ name }, err, times)` and the timeout path with `forceStepTimeout`. Remember the owner's earlier lesson that Workflow steps must return values rather than mutate closures; write one test that would fail if a step mutated a closure (assert on `getOutput()`, never on module state).
- Scheduled handlers: `createScheduledController({ cron, scheduledTime })` in the fast lane; `curl "http://localhost:8787/cdn-cgi/local/scheduled?cron=0+5+*+*+*&time=<ms>"` against `wrangler dev` in the integration lane. Never wait for the real cron.
- Outbound HTTP: `@msw/cloudflare` handlers that return the provider's real error payloads; one test per provider failure mode the code claims to handle (429, 5xx, malformed JSON, timeout).

**Contract tests from types or OpenAPI.** If the API is described with a schema (Zod, OpenAPI), generate one request/response validation test per route from that schema in the fast lane, and one test that feeds the iOS client's fixture files through the same validator so the app and the server cannot drift silently. Keep these generated, keep them small, and do not hand-edit them.

**Integration lane with the production build.**

```ts
import { createTestHarness } from "wrangler";
const server = createTestHarness({ workers: [{ configPath: "./wrangler.jsonc", env: "test" }] });
beforeAll(() => server.listen()); afterEach(() => server.reset()); afterAll(() => server.close());
const api = server.getWorker("api");
beforeEach(async () => { await api.applyD1Migrations("DB"); /* seed via (await api.getEnv()).DB */ });
```

**Live lane commands** (all non-interactive, all recorded into `.drive/evidence/<run>/backend/`):

```bash
# preview version (no Durable Objects) with a stable alias
npx wrangler versions upload --preview-alias drive-$RUN --tag drive-$RUN --message "drive $RUN" | tee evidence/upload.txt
# or, for DO-bearing Workers, a staging environment
npx wrangler deploy --env staging | tee evidence/deploy-staging.txt
# smoke requests against the printed URL; save status, headers and body
curl -sS -D evidence/headers.txt -o evidence/body.json -w '%{http_code} %{time_total}\n' "$PREVIEW_URL/health"
# remote data check
npx wrangler d1 execute DB --remote --json --command "SELECT COUNT(*) AS n FROM outfits" > evidence/d1-count.json
# logs, only for deployed (not preview) traffic
timeout 60 npx wrangler tail my-worker --env staging --format json --status error > evidence/tail-errors.jsonl
```

**Load and cost sanity.** Not a load test; a budget check. One test asserts the number of D1 queries and subrequests a hot path issues against fixtures (count calls in a thin wrapper around `env.DB.prepare` and `fetch`, and fail above the budget the design set). In the live lane, run the hot path fifty times with `--repeat-each`-style loops from a small script and read `wrangler d1 insights DB --json` and the tail sample for error rate. A change that doubles queries per request is a bug even when every assertion passes.

### 4.4 Frontend web testing

**Unit and component tests.** Vitest Browser Mode with the playwright provider for components (`@vitest/browser-playwright`, `vitest-browser-react` for React; check the plugin pin: Browser Mode supports Vitest 4 and 5, the Cloudflare plugin needs Vitest 4, so keep the frontend and backend Vitest configs as separate projects with their own pins). `jsdom` plus Testing Library is acceptable for hooks and formatting logic with no layout. Test behavior through roles and labels (`getByRole`, `getByLabelText`), never through class names or component internals.

**End to end.** Playwright with two configurations: `fixtures` (routes intercepted with `page.route()` serving JSON fixture files, fully deterministic, runs in the fast lane) and `live` (against the preview URL, a handful of flows, live lane). Pin `timezoneId` and `locale` in `use` so date and number rendering are deterministic. Use `--trace retain-on-failure` and store traces in evidence.

**Visual regression.** `toHaveScreenshot` with `maxDiffPixelRatio: 0.01`, `animations: "disabled"` (default), `mask` on timestamps, avatars and charts with live data, `stylePath` to hide cursors and scrollbars. Baselines are per browser and platform; since the owner runs on one Mac without CI, keep chromium-darwin baselines and record the macOS and Playwright versions in the ledger. Snapshot only the three to five screens whose layout is a claim; do not snapshot every route.

**Accessibility.** An axe fixture with `withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])`, `violations` must equal `[]`, exclusions named and justified in `TESTPLAN.md`. Run it on every route the feature adds, in the default and any dark theme. Keyboard-only traversal of the main flow is one explicit Playwright test (Tab through, assert focus order, Enter activates). axe finds roughly half of real issues, so the vision-verification step still reads the page for contrast and reading order.

**Performance budgets.** Lighthouse CI:

```js
// lighthouserc.cjs
module.exports = { ci: {
  collect: { url: [process.env.LH_URL], numberOfRuns: 3 },
  assert: { assertions: {
    "categories:performance": ["error", { minScore: 0.9 }],
    "categories:accessibility": ["error", { minScore: 0.95 }],
    "categories:best-practices": ["warn", { minScore: 0.9 }],
    "categories:seo": ["warn", { minScore: 0.9 }],
    "total-byte-weight": ["error", { maxNumericValue: 1_500_000 }],
  }},
  upload: { target: "filesystem", outputDir: ".drive/evidence/lighthouse" },
}};
```

Run `npx lhci autorun` against the preview; the Chrome DevTools MCP's `lighthouse_audit` is the interactive equivalent for a single page.

**What a dashboard feature specifically needs.** Data correctness is the claim, so the oracle must be independent of the UI: the test loads the same fixture the page will render, computes totals, percentages and bucket counts itself, and asserts the rendered values match to the displayed precision. Then the four states (loading, empty, error, partial data) each get one test using route interception to return `[]`, a 500, and a truncated payload. Responsiveness is three viewport widths (375, 768, 1280) with one screenshot each of the primary view and an assertion that no element overflows the body (`document.documentElement.scrollWidth <= innerWidth`). Time handling is one test at a DST boundary in the pinned timezone. Nothing else, unless a claim says otherwise.

### 4.5 Native iOS testing

**Frameworks.** Swift Testing for unit and integration tests of models, view models, formatting and networking; XCTest only where Swift Testing cannot go, which today is UI tests (XCUITest), performance tests and the accessibility audit. Turn on the Xcode 27 interoperability setting so a cross-framework assertion surfaces as a warning rather than vanishing. Structure: an `App` target, an `AppTests` target (Swift Testing, parallel, fast), and an `AppUITests` target (XCTest, serial, slow).

**Commands** (destination names must match an installed runtime; today that means iOS 26.4 on this Mac until `xcodebuild -downloadPlatform iOS` installs 27):

```bash
xcodebuild -list -project App.xcodeproj
xcrun simctl list devices available --json | jq -r '.devices[][] | select(.isAvailable) | "\(.name) \(.udid)"'
xcodebuild test -project App.xcodeproj -scheme App \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.4' \
  -testPlan Fast -parallel-testing-enabled YES -enableCodeCoverage NO \
  -resultBundlePath .drive/evidence/$RUN/ios/fast.xcresult 2>&1 | tail -40
xcrun xcresulttool get test-results summary --path .drive/evidence/$RUN/ios/fast.xcresult > .drive/evidence/$RUN/ios/fast-summary.json
xcrun xcresulttool get test-results tests   --path .drive/evidence/$RUN/ios/fast.xcresult | jq '.testNodes[] | select(.result=="Failed")'
# selective: Swift Testing ids may need doubled parentheses on some Xcode versions; verify once and record
xcodebuild test ... -only-testing:'AppTests/OutfitScoringTests/prefersUnwornItems()()'
# UI lane, serial, with diagnostics on failure
xcodebuild test -project App.xcodeproj -scheme App -testPlan UI \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.4' \
  -parallel-testing-enabled NO -collect-test-diagnostics on-failure \
  -resultBundlePath .drive/evidence/$RUN/ios/ui.xcresult
# flake proof
xcodebuild test ... -only-testing:AppUITests/CheckoutFlow -test-iterations 20 -run-tests-until-failure
```

The iOS Simulator MCP in this environment wraps the build (`build` → `build_status` returns the `.app` path) and the launch; prefer it for the vision step because `inspect` returns the accessibility tree with frames, which is a far better oracle than a screenshot for "the label shows the server's value".

**Testing SwiftUI state.** Test the `@Observable` model, not the view: construct it with a stubbed client, drive its intents (`load()`, `select(item)`), and `#expect` on published state. Views get at most one snapshot per design-critical screen and one launch test (Xcode 27's `runsForEachTargetApplicationUIConfiguration` template) that exercises every appearance and orientation without a hand-written matrix. Do not test that a `Text` shows a string you just passed in.

**Snapshots.** swift-snapshot-testing with an explicit device and tolerance so tiny antialiasing differences do not churn:

```swift
@Suite(.snapshots(record: .missing))
struct OutfitCardSnapshots {
  @Test func cardLayout() {
    assertSnapshot(of: OutfitCard(outfit: .fixture), as: .image(layout: .device(config: .iPhone13Pro), precision: 0.99, perceptualPrecision: 0.98))
  }
}
```

Record on the same simulator model and OS the comparison will run on; write both into the ledger. If the OS runtime changes, re-record deliberately with `record: .all` in one commit whose message names the runtime.

**Network stubbing.** Inject a `URLSession` built from `URLSessionConfiguration.ephemeral` with `protocolClasses = [StubURLProtocol.self]`, and give the stub a small queue of `(URLRequest) -> (HTTPURLResponse, Data)` handlers loaded from fixture files that are the same JSON the backend contract tests validate (Section 4.3). Offline is a stub that throws `URLError(.notConnectedToInternet)`; the claim "the last synced wardrobe is shown offline" is tested by loading once online, switching the stub, relaunching the model, and asserting the items and an offline indicator. Cache claims assert on what the model exposes, never on `URLCache` internals.

**Accessibility.** One XCUITest per screen:

```swift
func testWardrobeScreenAudit() throws {
  let app = XCUIApplication(); app.launchArguments += ["-UITEST", "1"]; app.launch()
  app.tabBars.buttons["Wardrobe"].tap()
  try app.performAccessibilityAudit(for: [.contrast, .dynamicType, .hitRegion, .sufficientElementDescription, .textClipped]) { issue in
    // ignore only with a ticket id in the comment; the verifier greps for this pattern
    return false
  }
}
```

Xcode 27's `XCUIVoiceOverService` lets one test walk the main flow under VoiceOver and assert the spoken labels; use it for the two flows the design calls primary.

**Simulator automation for deterministic screenshots and states.**

```bash
xcrun simctl boot "$UDID"; xcrun simctl status_bar "$UDID" override --time 9:41 --batteryState charged --batteryLevel 100 --wifiBars 3
xcrun simctl ui "$UDID" appearance dark
xcrun simctl privacy "$UDID" grant photos com.example.app
xcrun simctl install "$UDID" "$APP_PATH"
xcrun simctl launch --console-pty "$UDID" com.example.app -API_BASE_URL "$STAGING_URL" -UITEST 1
xcrun simctl io "$UDID" screenshot .drive/evidence/$RUN/ios/wardrobe-dark.png
xcrun simctl push "$UDID" com.example.app payload.apns
xcrun simctl location "$UDID" set 51.5074,-0.1278
```

Arguments passed as `-Key value` land in `UserDefaults`, which is how the app learns its base URL and test mode without a separate build.

**TestFlight, later.** Not part of proof for this skill's ladder until the app has real users; when it arrives, `xcodebuild archive` + `-exportArchive` and an App Store Connect API key. Do not let a TestFlight upload be recorded as Live Proof of anything but "the archive builds and uploads".

### 4.6 End to end across backend and app

Live proof means the app on a simulator talked to code running on Cloudflare and the observed value can be traced to a row that exists remotely. The recipe:

1. Deploy: `wrangler versions upload --preview-alias drive-$RUN` for Workers without Durable Objects; otherwise `wrangler deploy --env staging`. Record the URL and version id in the evidence folder.
2. Seed: `wrangler d1 execute DB --remote --file test/seed/e2e-$RUN.sql --yes` creating a test account whose identifiers embed the run id so the data is recognisable and deletable. Test accounts are real accounts in a staging tenant with an obviously synthetic email domain; never a personal account. Add a teardown script and run it at the end of the run, whatever the outcome.
3. Build and launch: MCP `build` → `launch`, or `xcrun simctl launch ... -API_BASE_URL "$URL" -TEST_ACCOUNT "$ID"`.
4. Drive and observe: `inspect` the accessibility tree and assert the value on screen equals the seeded value; take a screenshot for the vision verifier; hit the same endpoint with `curl` and save the body; read the row back with `wrangler d1 execute --remote --json`.
5. Write down what "live proof" means for each layer, because it differs: backend, a response from the deployed URL plus a remote data read that agrees; app, an accessibility-tree read of the value on a simulator pointed at that URL plus a screenshot; web, a Playwright run with trace against the preview URL. All three saved under `.drive/evidence/<run>/` and referenced from `TESTPLAN.md`.

Preview URLs carry no logs; anything that needs `wrangler tail` for proof goes through the staging environment instead.

### 4.7 Migration and consolidation testing

Order matters here more than anywhere: nothing is touched until the old behavior is pinned.

1. Characterization: pick a corpus of real inputs (sampled from `wrangler tail --format json` on the old service for an hour, or from stored requests), run them against the old system, store normalised outputs as golden files (strip timestamps, ids, ordering where the contract does not promise order). Each golden file is one characterization test. These tests describe what the old system does, including its bugs; fixing a bug during a migration is a separate, named decision.
2. Golden traffic replay: a script replays the corpus against the new implementation in the integration lane (`createTestHarness`) and diffs normalised outputs. The diff must be empty, or each difference must map to a listed intended change.
3. Parity in the live lane: deploy the new version alongside the old one and use gradual deployment with a small percentage (`wrangler versions deploy <old>@90% <new>@10% -y`), then compare error rates and latency from `wrangler tail --status error` on both versions (`--version-id` filter) over a fixed window of real traffic driven by the replay script, not by waiting for users.
4. Cutover verification: promote to 100% (`wrangler versions deploy <new>@100% -y`), rerun the smoke set, read the key remote counts. Before cutover, take a D1 bookmark (`wrangler d1 time-travel info DB --json`) and record it in `STATE.md`.
5. Rollback drill: actually run `wrangler rollback <old-version-id> --message "drill $RUN"` in staging and prove the smoke set passes on the old version, then roll forward. A rollback that has never been executed is a hope. For data, `wrangler d1 time-travel restore` is destructive and cancels in-flight queries; drill it only on the staging database, and record the returned undo bookmark.

### 4.8 Bug-hunt testing

Reproduce first, as a failing test, before reading the fix into existence. The severe-testing skill's confidence scale applies: a reproduction that fails on the broken code with realistic input scores 75; on the real runtime with captured evidence, 100; anything below 50 is a hypothesis, not a finding. If the bug is intermittent, make it reliable first (`--repeat-each 50`, `-run-tests-until-failure`, add logging, pin the seed); a fix for a bug you cannot make fail on demand cannot be verified. For regressions with a known good commit, `git bisect start <bad> <good>` then `git bisect run ./scripts/repro.sh` where the script exits non-zero on the bug; the found commit goes into the state file as a verified fact. When the fix lands, the reproduction stays as the regression test, named after the symptom and carrying the incident reference; then the verifier reverts the fix locally and confirms the test goes red, because a regression test that never failed proves nothing. Add nothing else: a bug hunt that grows the suite by more than two tests has drifted into a feature.

### 4.9 The test plan artifact

`TESTPLAN.md` lives at the repo root next to `SPEC.md` and `STATE.md`, is written by the test designer before implementation with every status at Missing, is updated by implementers as tests land, and is audited by the verifier, who is the only role allowed to write Local Proof or Live Proof.

```markdown
# TESTPLAN · <project> · <date>

## How to run
fast:        npm run test:fast            (workerd unit + binding tests, <2 min)
integration: npm run test:integration     (createTestHarness, limits probe)
live:        ./scripts/live.sh $RUN       (preview/staging deploy, smoke, remote reads)
ios-fast:    ./scripts/ios-fast.sh        (Swift Testing, parallel)
ios-ui:      ./scripts/ios-ui.sh          (XCUITest, serial, audits)

## Claims → tests
| ID | Claim (plain words, from SPEC) | Layer | Test (file::name) | Status | Evidence | Verified by |
|----|-------------------------------|-------|-------------------|--------|----------|-------------|
| C1 | A wardrobe of 101 items still produces a brief | workerd | test/brief.test.ts::builds at 100 and 101 items | Local Proof | .drive/evidence/r7/backend/fast.txt | verifier r7 |
| C2 | Deleting an outfit removes it from every list on next refresh | e2e | ui/Wardrobe.test.ts::delete propagates | Missing | | |

## Severe tests (trust boundaries)
| ID | Boundary | Attack | Test | Status |

## Harness kindness ledger
| Constraint (production) | Harness behavior | Mitigation | Evidence |
|---|---|---|---|
| D1 ≤100 bound params | enforced by local D1 (probe r7) | chunkBinds() + boundary test C1 | test/limits.probe.test.ts |
| D1 LIKE pattern ≤50 bytes | NOT enforced locally (probe r7) | guard in search.ts + unit test | test/search.test.ts::rejects long patterns |
| D1 row ≤2 MB | NOT enforced locally (probe r7) | accepted risk: max image ref is 200 B | signed: verifier r7 |
| Workers AI latency/429 | msw handler returns recorded 429 | retry test; remote binding in integration lane | |

## Quarantine
| Test | First seen | Hypothesis | Repro command | Ticket in STATE |

## Deliberately not tested
| Area | Reason |
```

Status words follow the owner's ladder and are downgraded, never upgraded, by anyone but the verifier. "Local Proof" means the named test passed in the real local runtime and failed under the verifier's manual mutation; "Live Proof" means the evidence path holds artifacts from the deployed URL or a simulator pointed at it.

**How the verifier uses it.** Fresh context, no access to the maker's transcript. It receives `SPEC.md`, `TESTPLAN.md`, the diff and the run commands. It runs every lane and records output paths. For each claim it checks that the named test exists, that its assertions could refute the claim (not a mock-call assertion), and that its layer is honest. For the top five claims by risk it performs a manual mutation and expects red. It checks that every ledger row has a mitigation or a signature, that every quarantined test has a state-file entry, that evidence files exist and postdate the diff. It then writes the status column and a short report; any row it could not verify is set to the highest status it could prove, which is usually one rung lower than the maker claimed. Ground truth precedence applies: code and tests over evidence, evidence over `TESTPLAN.md`, `TESTPLAN.md` over prose.

### 4.10 Anti-patterns and how the skill blocks each

- Green by mocking: the binding or dependency is replaced with a double that returns success, and the test asserts the double was called. Blocked by the real-runtime rule and by the reviewer question "would a constant-returning stub pass this test".
- Asserting on implementation: tests that read private state, count function calls, or snapshot internal structures. Blocked by the roles-and-labels rule for UI and the "observable outcome" wording rule for claims.
- Testing the scaffold: a test that the server starts, that a route returns 200 with no body check, that a view renders without crashing. These are allowed only as a single smoke test in the live lane and never count toward a claim.
- Coverage worship: coverage is a diagnostic for finding untested branches in a module that carries a claim, never a target and never a status input. The skill does not print coverage percentages in `TESTPLAN.md`.
- Relaxing assertions to pass: widening a tolerance, changing an expected value to the observed one, wrapping in try/catch. Blocked procedurally: any commit that changes an expected value must cite the claim change in `SPEC.md`, and the verifier diffs test files for weakened assertions.
- Disabling tests: `skip`, `.disabled`, `xit`, commented-out blocks, or deleting a test file. Allowed only through the quarantine table with a state-file ticket; the verifier greps for skip markers and fails any without a ticket.
- Waiting on a schedule for proof: "the cron will show whether it works tonight". Blocked by the local scheduled endpoint and by `wrangler workflows trigger --local`; a status can never depend on a future event.
- Vision as the only oracle for data: a screenshot "looks right" while the total is wrong. Blocked by requiring an accessibility-tree or API read alongside any screenshot used as evidence.

## 5. Conditionals by project shape

**Greenfield iOS app with Cloudflare backend.** Everything in Section 4 applies. Test design produces `TESTPLAN.md` with three lanes per layer before implementation begins, and the limits probe runs in the first hour so the ledger exists before any query is written. Snapshot tests are limited to the three to five screens the design phase marks as signature screens; every screen gets an accessibility audit; the launch test covers appearance and orientation. The end-to-end recipe (Section 4.6) is mandatory for Live Proof and runs against a staging environment because a fashion app with per-user state will almost certainly use Durable Objects or Workflows, which have no preview URLs. Contract tests are generated from the shared schema so the Swift client and the Worker cannot drift.

**Deep bug hunt in an existing codebase.** Skip test design ceremony. The only new tests are the failing reproduction and at most one boundary neighbour; `TESTPLAN.md` gets a two-row appendix rather than a rewrite. Use the project's existing runner and conventions, whatever they are; introducing a framework during a bug hunt is out of scope. Bisect when a good commit exists. Characterization tests around the touched function are added only if it has none and the fix changes its shape. The verifier's job shrinks to two checks: the reproduction goes red with the fix reverted, and the suite the project already had still passes.

**New dashboard on an existing product.** Detect and adopt the existing test stack (read `package.json`, look for `playwright.config.*`, `vitest.config.*`, `jest.config.*`). Data correctness against fixtures with an independently computed oracle is the primary claim set; the four states, three widths, one axe run, one keyboard traversal and one e2e flow complete it. A contract test against the API route the dashboard consumes is added if none exists. Visual snapshots only for the dashboard's primary view. No new frameworks, no touching unrelated suites.

**Migration or consolidation (AI gateway into the platform).** Section 4.7 in full, and it comes first: no code moves until the characterization corpus exists and passes against the old system. `TESTPLAN.md` gains a parity section whose rows are corpus classes rather than claims. Feature tests exist only for behavior the migration is meant to change, each cited in `SPEC.md`. The rollback drill is a required Live Proof row, not optional.

**Research plus website with blog and docs.** No unit tests for content. Playwright smoke across every generated route (status 200, no console errors), an internal link checker, an RSS and sitemap validity check, axe on the templates (home, post, docs page), Lighthouse budgets on the same three, visual snapshots of the same three at two widths. One content test the others do not have: every factual claim in the copy is traced to an entry in the research ledger, checked by a Sonnet low-effort classifier that reads the page text and the ledger and flags unsupported sentences.

**Other shapes.** CLI tool: golden output tests per command including `--help`, exit codes, and one test per documented error message; nothing else. Library or SDK: public-API contract tests and a compiled example per documented entry point; semver breaks caught by a type-level test that imports the public surface. Data pipeline: schema validation at every boundary, an idempotency test (run twice, same result), a replay test from a fixture batch, and a poison-record test. Refactor or simplification: the goal is that no test changes; characterization first if the area lacks tests, then the diff must leave the suite untouched and green. Ops or incident: reproduce the incident condition in staging, run the runbook as a script, keep the script as the drill. Pure research: no code tests; the verifier checks that each claim in the report has a source with a URL and that quoted facts match the source.

## 6. Model and effort assignment

| Role | Model / effort | Tools | Notes |
|---|---|---|---|
| Test designer (claims → tests, budget, ledger) | opus, high | Read, Grep, Glob, Bash (read-only commands), WebFetch | Runs after spec, before implementation. Writes `TESTPLAN.md` with all statuses Missing. Should be a predefined subagent (below). |
| Test implementer (writes the tests the designer named) | sonnet, medium | Read, Edit, Write, Bash | Volume work. Works from the designer's rows; may not add rows without a reason string. |
| Verifier (fresh context, adversarial) | opus, high | Read, Grep, Bash, the simulator and browser MCPs | Never sees maker transcripts. Only role that writes Local/Live Proof. Predefined subagent (below). Read-only on source; may write only `TESTPLAN.md` status columns and its report. |
| Harness-fidelity auditor (kindness ledger, limits probe) | opus, high | Read, Bash, WebFetch | Can be the designer wearing a second hat on small scopes; separate on greenfield. |
| Flake triage | sonnet, medium | Read, Bash | Reproduce, classify, quarantine with ticket. Escalates second occurrences to opus. |
| Test-bloat classifier / claim-trace grader | sonnet, low | Read | Labels each test refutes-claim / duplicate / scaffold / implementation-coupled; labels each copy sentence supported / unsupported. Never Haiku. |
| Arbiter when maker and verifier disagree | fable (main session) | all | The only place Fable spends tokens on testing; it reads both reports and the code and rules once. |

Isolation: none of these roles needs a worktree. The verifier must be read-only on source to keep its independence; give it `disallowedTools: Edit, Write` except for a scripted append to `TESTPLAN.md` via Bash. If a maker used a worktree, it is merged and deleted before the verifier starts; the verifier always reads the canonical checkout.

Draft `~/.claude/agents/drive-test-designer.md`:

```markdown
---
name: drive-test-designer
description: Turns SPEC.md acceptance criteria into TESTPLAN.md, one refutation test per claim at the cheapest honest layer, with a harness kindness ledger. Use after the spec is final and before implementation.
model: opus
effort: high
tools: Read, Grep, Glob, Bash, WebFetch
disallowedTools: Edit
memory: project
---
You design tests; you do not write production code. Read SPEC.md and the repository. For every acceptance criterion produce one row in TESTPLAN.md: the claim in plain words, the lowest layer whose real runtime can refute it, the test file and name, status Missing. Add a second test for a claim only with a written reason: independent oracle for critical code, a boundary the first cannot reach, or a bug that happened. Never propose tests for constructors, getters, framework behavior, private helpers, or whole-page snapshots. For every platform in play, list its documented limits, write a limits probe test that exercises each against the local harness, and fill the kindness ledger with what the harness does not enforce and how production code guards it. Name the commands for each lane. Keep the plan proportional: a bug fix gets two rows; a feature gets its claims plus one severe test per trust boundary plus one end-to-end flow. Write TESTPLAN.md using Bash heredocs and stop.
```

Draft `~/.claude/agents/drive-verifier.md`:

```markdown
---
name: drive-verifier
description: Independent verification of a change against SPEC.md and TESTPLAN.md. Fresh context; never sees the maker's reasoning. The only role that may set Local Proof or Live Proof.
model: opus
effort: high
tools: Read, Grep, Glob, Bash, mcp__Claude_Code_iOS_Simulator__control, mcp__playwright__browser_snapshot, mcp__playwright__browser_take_screenshot, mcp__chrome-devtools__lighthouse_audit
disallowedTools: Edit, Write
memory: project
---
You are auditing, not helping. Inputs: SPEC.md, TESTPLAN.md, the diff, the run commands. Run every lane and save outputs under .drive/evidence/<run>/. For each claim row: confirm the named test exists, that its assertions observe the outcome rather than a mock being called, and that its layer can refute the claim. For the five riskiest claims, break the production line the claim depends on, run the named test, expect red, restore. Grep for skip, disabled, xit, fixme, only; every hit needs a quarantine row with a ticket. Check each kindness-ledger row has a guard test or a signed accepted risk. Confirm evidence files exist and postdate the diff. Then set the Status column: Local Proof only for tests that passed in the real local runtime and failed under mutation; Live Proof only where evidence came from a deployed URL or a simulator pointed at one. Never raise a status you did not prove; lower any you could not. Report in plain sentences: what you ran, what failed, what you downgraded and why, and what remains untested. Do not fix anything.
```

## 7. Failure modes and anti-patterns

The mirage this component can produce is a `TESTPLAN.md` that reads as complete. Three routes lead there and each has a block.

The maker fills in the status column itself. Block: the column is owned by the verifier; the skill's completion check (a `Stop` hook or the final orchestration step) rejects a run where any Local/Live Proof row lacks a "Verified by" value and a matching evidence path.

The tests are real but the harness is kind. Block: the limits probe and ledger are required rows, and the verifier fails the run if the ledger is empty for a platform with documented limits. The D1 incident is the standing example in the skill's known-failure-modes section.

The verifier is not independent. It received the maker's transcript by being spawned with the conversation, or it was the same agent with a different prompt. Block: the verifier is a predefined subagent invoked with only file paths; the skill text forbids passing summaries of the maker's reasoning into its prompt.

Other failure modes: the fast lane grows past two minutes and agents stop running it (cap it, move slow tests to integration); e2e tests run against production data (test accounts with run ids, staging environment, teardown script that runs on failure too); visual baselines rot when macOS updates (record the environment in the ledger, re-record deliberately in one commit); a preview URL is used for a Durable Object Worker and silently is not created (the skill checks for `durable_objects` in `wrangler.jsonc` and picks the staging path); Vitest 5 is installed by habit and the Cloudflare plugin refuses to load (pin `vitest@^4.1.0` in the backend project and keep frontend Vitest separate); Swift Testing filters silently run zero tests because of the parentheses quirk (the skill asserts the summary JSON reports at least one test executed and fails otherwise); a `Stop` hook running the whole e2e lane makes the loop take twenty minutes per turn (the hook runs the fast lane only).

## 8. Open questions and trade-offs

1. Vitest 5 versus the Cloudflare plugin's `^4.1.0` peer range. Recommendation: pin 4.1.x in the Worker project, run the frontend on whichever Vitest the component tooling wants, keep them as separate Vitest projects with separate configs; revisit when the plugin's peer range moves.
2. Vitest plugin versus `createTestHarness()` for integration. Recommendation: plugin for everything that wants binding-level assertions and isolated storage; harness for production builds, multiple Workers and Vite-built frontends served by a Worker. Do not use both for the same claim.
3. Whether to wire a `Stop` hook that runs the fast lane during `/drive` runs. Recommendation: yes, via the skill's `hooks` frontmatter if it applies while the skill is active (verify that semantics on the docs before shipping), running only `npm run test:fast` and the iOS fast lane if a project has one, and blocking completion on red. It is the cheapest guard against "declared done with red tests". Trade-off: adds up to two minutes per turn.
4. Visual regression without CI on a single Mac. Baselines are chromium-darwin and simulator-specific; both drift with OS updates. Recommendation: accept, record the environment in the ledger, re-record in one commit when the environment changes, and treat a screenshot diff as a prompt for the vision verifier rather than as a hard failure unless the diff ratio exceeds 5%.
5. Mutation testing budget. Recommendation: manual mutation by the verifier always; Stryker incremental only on pure-logic packages that carry money, auth or data-loss claims, run in the integration lane, threshold `break: 60` initially so it informs without blocking. No Muter on iOS until it has a release that targets a Swift 6.x toolchain.
6. iOS 27 runtime is not installed; Xcode 27 RC is. Recommendation: run on iOS 26.4 today and record it; the skill should check `xcrun simctl list runtimes` and download the runtime matching the app's deployment target when the design phase fixes it.
7. How much to trust `inspect` (accessibility tree) as a data oracle. It is a stronger oracle than a screenshot but it reads what the app labels, which the app could label wrongly. Recommendation: pair it with an API or remote data read for the same value; that pairing is what "live proof" means for the app layer.
8. The Swift Testing `-only-testing` parentheses quirk on Xcode 27 is unverified. Recommendation: the skill's iOS bootstrap runs one filtered test and asserts the summary counts one executed test; whichever form works is recorded in the state file as a verified fact.

## 9. Skill text candidates

**Claims come first.** Before any test is written, restate each acceptance criterion as a claim about something observable: what a user or a caller would see, not how the code does it. If a criterion cannot be phrased that way, it is not ready; send it back to the spec.

**One test per claim, at the cheapest layer that can actually refute it.** Pure logic is refuted in a unit test. Anything that touches storage or a binding is refuted inside the real local runtime, never against a hand-written fake. Wiring between systems is refuted end to end, once. A second test on the same claim needs a written reason: an independent oracle for critical code, a boundary the first test cannot reach, or a bug that actually happened.

**Do not test these.** Constructors, getters, type-level facts the compiler checks, framework behavior, third-party libraries, private helpers, log wording, and whole-page snapshots without a named reason. Tests like these make the suite longer and the signal weaker.

**Budget by claims, not by lines.** A bug fix gets the failing reproduction and at most one boundary neighbour. A feature gets its claims, one severe test per trust boundary it crosses, and one end-to-end flow. If a module has more tests than claims and none cites a bug, delete the extras and note the deletion in STATE.md.

**A harness kinder than production certifies broken code.** Prefer the platform's own runtime: workerd through the Cloudflare Vitest plugin, the iOS simulator, a real browser under Playwright. Where a double is unavoidable, list every production constraint it does not enforce (sizes, counts, timeouts, auth, quotas, consistency, error shapes) in the kindness ledger in TESTPLAN.md, and give each entry a guard in production code with its own test, a live check that crosses the limit, or a signed accepted risk.

**Probe the harness instead of trusting it.** For each platform, write a limits probe that exercises the documented limits against the local runtime and prints which are enforced. Record the toolchain versions next to the results and rerun the probe when they change. Known result on 2026-09-14: local D1 enforces 100 bound parameters, 100 KB statements and 100 columns; it does not enforce the 50-byte LIKE pattern limit or the 2 MB row limit.

**Encode limits as named constants and test the guard.** `D1_MAX_BOUND_PARAMS = 100` with a chunking helper and tests at 100 and 101 is a permanent fix. A comment in a query is not.

**The verifier owns the status column.** Spawn the verifier with only file paths: SPEC.md, TESTPLAN.md, the diff, the run commands. Never pass it the maker's reasoning. It runs every lane, breaks a production line for the riskiest claims and expects red, greps for skipped tests without tickets, checks evidence exists and is fresh, and sets each row to the highest status it could prove. Nobody else may write Local Proof or Live Proof.

**Live proof means a deployed URL was involved.** Backend: a response from the preview or staging URL plus a remote data read that agrees. App: an accessibility-tree read of the value on a simulator pointed at that URL, plus a screenshot. Web: a Playwright run with trace against that URL. Save all of it under .drive/evidence/<run>/ and reference the paths from TESTPLAN.md. Preview URLs are not created for Workers with Durable Objects and carry no logs; use a staging environment for those.

**Flakes are quarantined with a ticket, never deleted.** Reproduce deliberately with repeat flags, fix it now if the cause is shared state or ordering, otherwise skip it with a reason that names a ticket, add the ticket to Open failures in STATE.md with the reproduction command, and keep it running in a non-blocking lane. The second time the same test flakes with the same workaround, the workaround was wrong; the root cause becomes the task. Tests guarding money, auth or data loss cannot be quarantined.

**Never widen an assertion to make a test pass.** Any change to an expected value must cite a change to the claim in SPEC.md. The verifier diffs test files for widened tolerances, replaced expectations and new try/catch blocks and treats each as a finding.

**Reproduce the bug as a failing test before you fix it.** If it is intermittent, make it reliable first with repeat flags and a pinned seed. Bisect with `git bisect run` when a good commit exists. Keep the reproduction as the regression test, named after the symptom, and have the verifier revert the fix once to see it go red.

**Never wait for a schedule to prove anything.** Fire the scheduled handler through the local endpoint, trigger Workflows with `wrangler workflows trigger --local`, fire alarms with `runDurableObjectAlarm`. A status may never depend on a future event.

**Migration: pin the old behavior before touching it.** Sample real traffic, store normalised golden outputs, replay against the new code and require an empty diff except for listed intended changes. Take a D1 bookmark before cutover and write it to STATE.md. Run the rollback for real in staging; a rollback that has never been executed is a hope.

**Vision is not a data oracle.** A screenshot proves layout and state rendering. For any number, name or list on screen, pair the screenshot with an accessibility-tree read or an API response that shows the same value.

**Pin the Cloudflare test stack.** `npm i -D vitest@^4.1.0 @cloudflare/vitest-plugin`; the plugin does not accept Vitest 5 today. Keep frontend and backend Vitest configs as separate projects so the frontend can move independently.

**Coverage is a flashlight, not a score.** Use it to find an untested branch in a module that carries a claim. Never print a percentage in TESTPLAN.md and never let it move a status.
