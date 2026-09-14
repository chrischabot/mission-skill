# Cloudflare domain reference

Read this file when the Cloudflare pack activates (section 1): before design, before any Worker code is written, and
again before verification and deployment. It decides where platform limits live in the code, how tests are made as
strict as production, the order of a deployment, what Local Proof, Live Proof and Operational mean on this platform,
how an external service moves behind a service binding, and what to refuse. A static site served from a Worker also
follows `references/domains/web.md`.

## Contents

Sections: 1. Activation · 2. The one rule · 3. Verified limits · 4. Platform facts learned in production · 5. Architecture
defaults · 6. D1 access discipline · 7. Workflow discipline · 8. `waitUntil` and scheduled work · 9. Testing setup · 10. The
kinder-shim probe · 11. Configuration essentials · 12. Secrets · 13. The deploy ladder · 14. What the rungs mean on Cloudflare
· 15. Moving an external service behind a service binding · 16. Operational gates before Done · 17. Anti-patterns to refuse · Learned constraints

## 1. Activation

The pack is active when a `wrangler.jsonc`, `wrangler.json` or `wrangler.toml` exists outside `node_modules`; when the
goal, SPEC.md or DESIGN.md names Cloudflare, Workers, D1, R2, KV, Durable Objects, Queues, Workflows, Vectorize, Workers
AI or AI Gateway; or when design chose Cloudflare. A bare mention of "the edge" or "serverless" does not activate it.

On activation the orchestrator quotes the applicable Learned constraints (at most ten) under "Lessons that apply to
this task" in every brief for `drive:architect`, `drive:implementer`, `drive:severe-tester`, `drive:verifier` and
`drive:security-reviewer`; writes GOAL.md's `live means:` as the production Worker's route with production bindings
(staging only when no production exists yet, stated); adds the two STATUS rows in section 14; confirms `api`,
`external-systems` and `deploy-infra`; and suspects `async-scheduled` and `data`. In an existing codebase, archaeology reads every `wrangler.*` first and
records in `.drive/how-it-works.md` the Worker name, compatibility date, flags, bindings and `limits` per environment,
crons, and whether a Durable Object is bound, because that changes the deploy ladder.

## 2. The one rule

Cloudflare enforces hard limits that local tooling does not always enforce. Put every limit the code depends on into
the code under test as a named constant with a guard, write one severe test that tries to cross it, and run the same
operation once against a real deployed resource to learn where the local runtime is kinder. A green run against a shim
shows only that the shim accepted the code.

## 3. Verified limits

Verified 2026-09-14 against developers.cloudflare.com. When a decision rests on a row and this date is more than 90
days old, re-read the source page and record the value with its checked date in RESEARCH.md; if the value changed,
append a Learned constraint with the new value and URL, which overrides the row.

| Service | Limit | Value |
|---|---|---|
| Workers | CPU per invocation | 30 s default on Paid; `limits.cpu_ms` up to 300,000 |
| Workers | Memory per isolate | 128 MB |
| Workers | `waitUntil` after the response | 30 s wall time, shared by all calls, then cancelled |
| Workers | Cron, Queue consumer, alarm wall time | 15 min |
| Workers | Subrequests (KV, D1, R2, Queues, fetch and service bindings all count) | 50 Free; 10,000 Paid default via `limits.subrequests`; design under 1,000 because the service-bindings page still says 1,000 |
| Workers | Connections awaiting response headers; service-binding chain | 6 at once; 32 Worker invocations per request |
| Versions | Deployable history | last 100 versions |
| D1 | Bound parameters per statement | 100 |
| D1 | Statement length | 100 KB, applied to each statement in a batch |
| D1 | LIKE or GLOB pattern | 50 bytes |
| D1 | Row, string or blob; columns per table; query or whole-batch duration | 2 MB; 100; 30 s |
| D1 | Queries per invocation; database size | 1,000 (Paid); 10 GB (Paid) |
| D1 | Transactions; migrations; Time Travel | `batch()` only, auto-commit otherwise; no down migrations; 30 days (Paid), restore is destructive and returns an undo bookmark |
| Workflows | Step return value | 1 MiB; store larger data in R2 and return the key |
| Workflows | Steps per instance; step CPU; persisted state; retention | 10,000 default (Paid), raisable to 25,000; 30 s default, up to 5 min; 1 GB; 30 days (Paid) |
| KV | Consistency and writes | eventual, up to 60 s or more; 1 write/s per key; 25 MiB values; 1,000 operations per invocation |
| R2 | Single PUT; presigned expiry; writes; lifecycle | 5 GiB; 1 s to 7 days; 1 write/s per key; 1,000 rules per bucket acting within about 24 h |
| Queues | Message; batch; retention | 128 KB; 100 messages; 14 days |
| Vectorize | Dimensions; vectors; topK | 1,536; 20 million per index; 50 with metadata, 100 without |
| Analytics Engine | Per data point; per invocation | 20 blobs, 20 doubles, 1 index; 250 points |
| Workers Logs | Retention; event size | 7 days Paid; 256 KB |
| Rate limit binding | Period and semantics | 10 or 60 s; per location, eventually consistent; not an accounting system |
| Preview URLs | Availability | none for Workers with Durable Objects, Containers or Sandbox; no logs of any kind |

Sources: https://developers.cloudflare.com/workers/platform/limits/ · https://developers.cloudflare.com/workers/runtime-apis/context/
· https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/ · https://developers.cloudflare.com/d1/platform/limits/
· https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/ · https://developers.cloudflare.com/kv/platform/limits/
· https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/ · https://developers.cloudflare.com/r2/platform/limits/
· https://developers.cloudflare.com/workers/configuration/previews/ · https://developers.cloudflare.com/d1/worker-api/d1-database/
· https://developers.cloudflare.com/workers/observability/logs/workers-logs/ · https://developers.cloudflare.com/d1/reference/time-travel/
· https://developers.cloudflare.com/workflows/reference/limits/ · https://developers.cloudflare.com/queues/platform/limits/
· https://developers.cloudflare.com/vectorize/platform/limits/ · https://developers.cloudflare.com/analytics/analytics-engine/limits/

A probe on 2026-09-14 found that local D1 in workerd enforced 100 bound parameters, 100 KB statements and 100 columns,
but not the 50-byte pattern limit or the 2 MB row limit. Treat that as a hypothesis and re-run section 10 per project.

## 4. Platform facts learned in production

These were observed on live traffic rather than read in documentation.

| Fact | Rule |
|---|---|
| A `sql.js` shim for D1 accepts any number of bound parameters, so a query that binds one parameter per item passes every local run and fails live at 101 items | Guard module (section 6); tests run in workerd; `sql.js` and hand-written D1 fakes are banned |
| D1 rejects GLOB character classes such as `'[0-9]*'` in CHECK constraints that local SQLite accepts | Write CHECKs as `IN (...)` or comparisons; run any GLOB once against the remote database |
| A long LIKE term fails with "LIKE or GLOB pattern too complex" | Validate search input at 50 bytes and return 400 before D1 sees it |
| Joining a multi-KB text or blob column onto thousands of rows fails with `D1_ERROR: Memory limit exceeded before EOF` | Select large columns only in single-row reads |
| Paged reads over a large table can be refused as "too many requests" or "overloaded" | Back off and resume from a cursor; never loop tightly |
| A full D1-to-R2 backup exceeded one request's CPU (error 1102) and completed only when dispatched under `waitUntil` with per-table failures recorded | Anything that can exceed 25 s runs as a Workflow with one step per table |
| A Workflow step that assigned to an outer variable was right on the first run and silently reverted on replay, because replay returns the memoised result without re-running the callback | Section 7 |
| Outbound email from a Worker goes through the `send_email` binding to verified destination addresses, not a REST endpoint | One real send to a verified address in the live lane |
| An Authenticated AI Gateway returns 401 unless the request carries `cf-aig-authorization: Bearer <token>` (binding calls are pre-authenticated); a BYOK key worked on the provider-native path (`/<provider>/...`) while the unified path returned 402 | Prefer the binding; make one real call per provider path the code uses in the parity test |
| The gateway cache returned a stale response for a call whose answer had to be fresh | Send `cf-aig-skip-cache: true`, or `skipCache: true` on the binding, for those calls |
| Reasoning tokens count against `max_tokens`, so a low cap truncates or empties the answer; models asked for JSON often wrap it in code fences | Leave headroom; strip fences, schema-parse, assert non-empty content, retry once with the validation error appended |
| Secret values pasted with their quotes kept the quotes and upstream calls returned 401 | Section 12 |
| A deploy carrying a stale `name` nearly overwrote a different Worker | Ladder step 0; explicit `name` in every environment block |
| A stale `.wrangler` build directory made local behaviour disagree with the source | `rm -rf .wrangler` before concluding that a local result contradicts the code |
| Variables set in the dashboard are removed by the next deploy | `keep_vars: true` when anyone manages vars in the dashboard |

## 5. Architecture defaults

`drive:architect` applies this table and records any deviation, with its condition, in DESIGN.md's decision index.

| Need | Default | Deviate when |
|---|---|---|
| System of record | D1, with a tenant or user id on every table and every query | per-object real-time state is a requirement |
| Files | R2; the client PUTs to a presigned URL with `ContentType` signed and expiry ≤ 900 s; the Worker HEADs the key through the binding before recording it | payloads under 1 MB may pass through the Worker |
| Multi-step or slow work | Workflows | many independent producers fan in: Queues |
| Similarity search | Vectorize, namespace per tenant; confirm the embedding dimension with one real call before creating the index | never |
| Model calls | Workers AI or external providers through the AI Gateway binding, with `metadata` for attribution | never call providers with keys held in the Worker |
| Config and caches that tolerate 60 s staleness | KV | anything read right after it is written: D1 |
| Abuse damping | rate limit binding | quotas: a D1 counter updated in the same `batch()` as the metered write |
| Real-time, WebSockets, strict per-object serialisation | Durable Objects in a separate Worker | never in the API Worker: they remove preview URLs, and lifecycle changes block `versions upload`, gradual rollout and rollback |

Contract first: Hono with `@hono/zod-openapi` or chanfana, one per repository; OpenAPI 3.1 served at `/openapi.json`
and committed to `contracts/openapi.json`, with a test that fails when they differ. Every creating POST accepts
`Idempotency-Key` (same body replays the stored response, different body returns 409). One error envelope,
`{ "error": { "code", "message", "details", "request_id" } }`, codes a closed enum. Every response carries
`x-request-id`; one JSON log line per request carries `request_id`, `route`, `status`, `ms` and `version`
(`env.VERSION.id`). `GET /health` returns `{ ok, version: { id, tag, timestamp }, checks }` after `SELECT 1` and an R2
HEAD on a canary object when R2 is bound.

## 6. D1 access discipline

All D1 access goes through `src/db/`, the only module that may call `env.DB.prepare`:

```ts
// src/db/guard.ts
export const D1_MAX_BIND = 100, D1_MAX_SQL_BYTES = 100_000, D1_MAX_LIKE_BYTES = 50, D1_IN_CHUNK = 90;
export class PlatformLimitError extends Error {
  constructor(public limit: string, public actual: number, public max: number) { super(`${limit}: ${actual} exceeds ${max}`); }
}
const bytes = (s: string) => new TextEncoder().encode(s).byteLength;
export function guardStatement(sql: string, params: readonly unknown[]): void {
  if (params.length > D1_MAX_BIND) throw new PlatformLimitError("d1_bind_params", params.length, D1_MAX_BIND);
  if (bytes(sql) > D1_MAX_SQL_BYTES) throw new PlatformLimitError("d1_sql_bytes", bytes(sql), D1_MAX_SQL_BYTES);
}
export function guardLike(p: string): string {
  if (bytes(p) > D1_MAX_LIKE_BYTES) throw new PlatformLimitError("d1_like_bytes", bytes(p), D1_MAX_LIKE_BYTES);
  return p;
}
```

The helpers (`q`, `qAll`, `qFirst`, `batch`) call `guardStatement` before every `prepare().bind()`; the verifier checks:

- A test greps `src/` for `.prepare(` outside `src/db/` and fails on any hit.
- Chunk IN lists at 90 values; rows per multi-row INSERT are `floor(100 / columns)`.
- Never select a large JSON or blob column in a query that returns many rows.
- Use `batch()` whenever one request writes two tables; `BEGIN` never appears in source.
- Build LIKE patterns only through `guardLike`; reject over-long input at validation with 400.
- Migrations are forward-only and expand first (nullable columns, tables, indexes). A drop or rename ships one release
  after the code that stopped using it, because rollback moves code and never schema. Each `NNNN_name.sql` has a
  hand-written `NNNN_name.down.sql`, tested by applying up then down locally and diffing `sqlite_master`.
- Pass `--local` or `--remote` on every `wrangler d1 execute` and `migrations apply`; with no flag they hit remote.
- Before any remote destructive statement or migration, run `wrangler d1 time-travel info <db> --env <env>` and write
  the bookmark as the undo of the DECISIONS.md entry, or of MIGRATION.md's undo ledger during a `move`.

Severe tests `drive:severe-tester` writes, one per limit the code can reach:

| Test | Refutes |
|---|---|
| an IN-list read of 250 ids returns all 250; `guardStatement` with 101 params throws `PlatformLimitError` | chunking and the bind guard |
| a 100,001-byte statement throws before D1 is called | the length guard |
| a 51-byte search term returns 400 `validation_failed`, not a D1 error | the pattern guard |
| a list over 5,000 rows with 4 KB JSON columns succeeds, and a static check finds no list query selecting that column | the memory limit |
| a two-statement batch whose second statement violates a constraint persists nothing | atomicity |
| the same `Idempotency-Key` twice creates one row and returns the identical body; a different body returns 409 | idempotency |

## 7. Workflow discipline

Every value a step computes is returned from `step.do` and read from that return; nothing inside a step callback
assigns to a variable declared outside it, and top-level state is composed only from step returns. Step names are
literals or built only from earlier step returns, because names are cache keys. Wrap `Date.now()`, `Math.random()` and
`Promise.race` in steps. Derive instance ids from the idempotency key; `create()` throws on a duplicate id, which means
"already running". Keep returns under 1 MiB (large data goes to R2, return the key). Throw `NonRetryableError` for input
that can never succeed, keep step timeouts ≤ 30 minutes (`waitForEvent` beyond), always `await` steps, and return a
small summary from `run`.

Enforce it three ways. The project's `scripts/lint-workflows.mjs`, written by `drive:implementer` in wave 0, flags
assignments to identifiers declared outside a `step.do` callback,
and `drive:grader` classifies ambiguous hits as `violation`, `false_positive` or `needs_review`. A workerd test drives
`introspectWorkflow(env.WF)` with `modifyAll(m => { m.disableSleeps(); m.mockStepResult({ name }, value) })` and
`waitForStatus("complete")`, asserting `getOutput()` depends only on step outputs (retries via `mockStepError`, timeouts
via `forceStepTimeout`). Live runs use `wrangler workflows trigger <name> '<json>'` and `instances describe <name> <id> --step-output`.

## 8. `waitUntil` and scheduled work

`waitUntil` extends an invocation by 30 seconds of wall time after the response, shared across all calls, then cancels
unsettled promises without an error reaching your code. Race background work against a 25-second deadline in a helper
that logs `deadline_exceeded` with the request id; its severe test injects a slow task and asserts the marker. Work
that may exceed 25 seconds, needs retries, or must not be lost becomes a Workflow or a Queue message.

Scheduled handlers get 15 minutes. Never wait for a cron to prove anything: locally run `wrangler dev --test-scheduled` and
`curl "http://localhost:8787/cdn-cgi/local/scheduled?cron=<url-encoded expr>"`; in tests use `createScheduledController`;
live, call the system's own internal route or trigger the Workflow. Work reported as happening at the next tick is not done.

## 9. Testing setup

The Workers Vitest integration is `@cloudflare/vitest-plugin`, renamed from `@cloudflare/vitest-pool-workers` on
2026-08-19 with an unchanged API (Hono's testing page still shows the old name; migrate old configs with
`npx @cloudflare/codemods vitest:pool-workers-to-vitest-plugin`). Its peer range is `vitest ^4.1.0`, checked 2026-09-14,
so install `npm i -D vitest@^4.1.0 @cloudflare/vitest-plugin @msw/cloudflare msw` in the Worker project and keep any
frontend Vitest in a separate project.

```ts
// vitest.config.ts
import path from "node:path";
import { defineConfig } from "vitest/config";
import { cloudflareTest, readD1Migrations } from "@cloudflare/vitest-plugin";
export default defineConfig(async () => ({
  plugins: [cloudflareTest({
    wrangler: { configPath: "./wrangler.jsonc", environment: "test" },
    miniflare: { bindings: { TEST_MIGRATIONS: await readD1Migrations(path.join(import.meta.dirname, "migrations")) } },
  })],
  test: { include: ["test/workers/**/*.test.ts"], setupFiles: ["./test/setup/apply-migrations.ts"] },
}));
// test/setup/apply-migrations.ts
import { env } from "cloudflare:workers";
import { applyD1Migrations } from "cloudflare:test";
await applyD1Migrations(env.DB, env.TEST_MIGRATIONS);
```

Import `env` and `exports` from `cloudflare:workers` (`SELF` is gone; `exports` does not expose assets) and the helpers
(`createExecutionContext`, `waitOnExecutionContext`, `createMessageBatch`, `runDurableObjectAlarm`, `introspectWorkflow`)
from `cloudflare:test`. The test tsconfig sets `"types": ["@cloudflare/vitest-plugin/types"]` and declares
`TEST_MIGRATIONS` on `ProvidedEnv`. `defineWorkersConfig` and `poolOptions.workers` no longer exist. Storage is isolated
per test file (`--max-workers=1 --no-isolate` only when tests must share state). Fake timers do not expire KV, R2 or
cache entries, so test a TTL by asserting `expirationTtl` at the write site plus one live check. Dynamic `import()`
fails inside handlers and Durable Objects. Use Istanbul for coverage.

Workers AI, Vectorize and Browser Rendering have no local simulation. Mock them in the fast lane with doubles that
return the provider's real failure shapes (429 with `Retry-After`, 5xx, fenced or malformed JSON), and keep one
integration test with `"remote": true` on those bindings, against a non-production resource, asserting that the
embedding dimension matches the index and that the model returns parseable output for a real sample. Durable Objects,
Workflows, vars, secrets and assets cannot be remote.

| Lane | Command | Required before |
|---|---|---|
| fast | `npx vitest run` in workerd, under two minutes, plus `npx wrangler types --check` | every package report |
| integration | `createTestHarness` from `wrangler` against the built Worker, the probe in section 10, the remote-binding test | Local Proof |
| live | the ladder's smoke suite, tail capture and remote reads (sections 13 and 14) | Live Proof |

Seed the kindness ledger in TESTPLAN.md with these rows and fill the harness column from the probe:

| Constraint (production) | Harness behaviour | Mitigation | Evidence |
|---|---|---|---|
| D1 ≤ 100 bound parameters, ≤ 100 KB statement, LIKE ≤ 50 bytes, no GLOB classes | from probe | guard module, no GLOB in CHECKs, severe tests | `severe:` path |
| D1 row ≤ 2 MB; blob join memory limit | not enforced locally | projection rule and its severe test | `severe:` path |
| Workflow replay returns memoised step results | replays only when a test forces it | return-everything rule, lint, output test | `test:` path |
| `waitUntil` cancelled after 30 s | not enforced | deadline helper and its test | `severe:` path |
| Workers AI and Vectorize latency, 429s, dimensions | doubles | remote-binding test | `test:` path |
| Subrequests and queries per invocation | not enforced | a counting wrapper test on the hot path | `test:` path |

## 10. The kinder-shim probe

Run once per project, and again whenever the Wrangler version changes, against a dev or staging database only:

```bash
P=$(printf '?,%.0s' $(seq 101) | sed 's/,$//'); L=$(printf 'a%.0s' $(seq 51))
for where in --local --remote; do
  npx wrangler d1 execute <db> --env staging $where --command "SELECT $P"
  npx wrangler d1 execute <db> --env staging $where --command "SELECT 'x' LIKE '%$L%'"
done
```

Run the same pair for any SQL construct the schema relies on, such as a GLOB inside a CHECK. Record under STATE.md
"Verified facts" which limits local does not enforce, with Wrangler version and date, and name each covering guard in
the kindness ledger; where local accepts what remote rejects, that guard's severe test is the only protection.

## 11. Configuration essentials

```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "example-api-dev", "main": "src/index.ts", "compatibility_date": "2026-09-01",
  "observability": { "enabled": true, "head_sampling_rate": 1 },
  "version_metadata": { "binding": "VERSION" },
  "limits": { "cpu_ms": 30000 },
  "secrets": { "required": ["SESSION_SIGNING_KEY", "SMOKE_TOKEN"] },
  "d1_databases": [{ "binding": "DB", "database_name": "example-dev", "database_id": "<uuid>", "migrations_dir": "migrations" }],
  "env": {
    "test": { "d1_databases": [{ "binding": "DB", "database_name": "example-test", "database_id": "test", "migrations_dir": "migrations" }] },
    "staging": { "name": "example-api-staging", "d1_databases": [ /* staging ids */ ] },
    "production": { "name": "example-api", "workers_dev": false, "preview_urls": true,
      "routes": [{ "pattern": "api.example.com", "custom_domain": true }],
      "d1_databases": [ /* production ids; every binding and var redeclared */ ] }
  }
}
```

- Set `compatibility_date` within 90 days of project start. From 2026-08-04 Node.js compatibility is on without
  flags; an older date needs `compatibility_flags: ["nodejs_compat"]`. Missing modules are stubbed and fail at run time.
- Bindings, `vars` and secrets do not inherit into `env.<name>` blocks; redeclare every one in every environment.
- `preview_urls` defaults to `workers_dev`, so production sets `preview_urls: true` explicitly when `workers_dev` is
  false, or the ladder's candidate alias will not exist. Give every environment an explicit, distinct `name`.
- Use `npx wrangler check startup` when bundle size or cold start is in question. Do not leave Workers Builds on its
  default production command, which deploys on push around the ladder; set it to `npx wrangler versions upload`.

## 12. Secrets

Secrets never appear in `vars`, the repository, STATE.md or any proof file; command logs write `<redacted>`. Local
values live in `.dev.vars`, gitignored; if `.dev.vars.<env>` exists it replaces `.dev.vars` rather than adding to it.
Set live values from stdin without quotes, then list the names:

```bash
printf '%s' "$VALUE" | npx wrangler secret put SESSION_SIGNING_KEY --env production
npx wrangler secret list --env production
```

`wrangler secret put` deploys a new version at once; during a gradual rollout use `wrangler versions secret put`. For
many keys, run `wrangler secret bulk <file> --env <env>` on a JSON file a script generated with quotes stripped.
`secrets.required` makes `deploy` and `versions upload` fail on an unset secret. Scope R2 tokens to one bucket; rotate
the AI Gateway token at every cutover, since its `Run` permission spans every gateway and BYOK key in the account. The
smoke token authenticates only the smoke user, lives in `.drive/local/smoke.env`, and is rotated when the run ends.

## 13. The deploy ladder

The orchestrator runs the commands that change deployments. `drive:verifier` independently runs the smoke suite, the
tail capture and the `/health` check, and writes its round under `.drive/proofs/<key>/r<n>/`. Nothing waits on the owner.

```bash
# 0. confirm the target; stop if the Worker name differs from how-it-works.md and STATE.md
npx wrangler deployments status --env production
npx wrangler deploy --dry-run --outdir .wrangler/dry --env production
# 1. schema first, expand only, bookmark recorded (section 6)
npx wrangler d1 migrations list <db> --env production --remote && npx wrangler d1 migrations apply <db> --env production --remote
# 2. upload without deploying; OLD comes from `wrangler versions list --env production`, NEW from this output
SHA=$(git rev-parse --short HEAD)
npx wrangler versions upload --env production --message "$SHA" --tag "$SHA" --preview-alias candidate
# 3. smoke the candidate with production bindings (drive:verifier)
SMOKE_BASE_URL=https://candidate-<worker>.<subdomain>.workers.dev EXPECTED_VERSION_ID=$NEW \
  npx vitest run -c vitest.smoke.config.ts --reporter=json --outputFile=.drive/proofs/<key>/r<n>/smoke-candidate.json
# 4. canary with a bounded error capture, then full traffic; `timeout` is absent on a stock Mac, so fall back to perl
limit() { if command -v gtimeout >/dev/null; then gtimeout "$@"; elif command -v timeout >/dev/null; then timeout "$@"; else perl -e 'alarm shift; exec @ARGV or die "exec failed: $!"' "$@"; fi; }
npx wrangler versions deploy "$NEW@10%" "$OLD@90%" --env production --yes
limit 120 npx wrangler tail <worker> --env production --format json --status error --version-id "$NEW" > .drive/proofs/<key>/r<n>/tail-canary.jsonl || true
npx wrangler versions deploy "$NEW@100%" --env production --yes
# 5. prove the production route serves it, then smoke production
curl -fsS https://<domain>/health | python3 -c 'import json,sys; sys.exit(json.load(sys.stdin)["version"]["id"] != sys.argv[1])' "$NEW"
SMOKE_BASE_URL=https://<domain> EXPECTED_VERSION_ID=$NEW \
  npx vitest run -c vitest.smoke.config.ts --reporter=json --outputFile=.drive/proofs/<key>/r<n>/smoke-production.json
```

Rollback is `npx wrangler rollback "$OLD" --env production --message "rollback: <reason>"`. It moves code only; bindings,
secrets and D1 schema stay, which is why migrations are expand-only. An error in the canary tail, a failed smoke, or a
`/health` version mismatch triggers the rollback at once and opens a failure record.

A Worker that binds a Durable Object has no preview URL: smoke `wrangler deploy --env staging` in place of step 3. A
release that changes a Durable Object lifecycle (`exports` or `migrations`) goes out only through `wrangler deploy`,
cannot be split or rolled back past, so rehearse it on staging and ship it alone.

## 14. What the rungs mean on Cloudflare

| Rung | Means here |
|---|---|
| Local Proof | Claim and severe tests pass in workerd with real migrations; the probe ran and every kindness-ledger row has a mitigation; the remote-binding test and the dry-run bundle passed; a verifier verdict passes. Results from a preview URL or staging alone stay at this rung unless GOAL.md's `live means:` names staging. |
| Live Proof | A `live:` bundle whose `proof.json` has `environment: "live"`, `target` set to the production route, `commit`, the ladder's commands and a `shim_differences` answer, and whose round holds: both smoke reports green against the version id `/health` serves on the production route, `wrangler d1 migrations list --remote` showing the expected head, and a canary tail with zero error outcomes for that version. A deploy without the smoke supports Scaffold at most. |
| Operational | Live Proof plus an `ops:` file answering every gate in section 16. |

The smoke suite lives in `test/smoke/`, runs under a plain Node Vitest config (`vitest.smoke.config.ts`), reads
`SMOKE_BASE_URL`, `SMOKE_TOKEN` and `EXPECTED_VERSION_ID`, and runs these steps in order, failing fast:

1. `GET /health` returns 200 and `version.id` equals `EXPECTED_VERSION_ID`.
2. A real authenticated write: a creating request with an `Idempotency-Key` returns 201 and the created id.
3. If R2 is bound: request a presigned URL, PUT a small real file, and confirm through the API that it is recorded.
4. If Workflows are bound: start one through the API, poll to `complete` within a stated bound, assert its output.
5. A read returns exactly what steps 2 to 4 wrote.
6. The step 2 request replayed with the same key and body returns the identical response, and there is still one row.
7. Cleanup deletes the smoke user's rows and objects through the API; a read-only remote D1 count confirms zero remain.

Smoke rows are tagged, excluded from analytics, and land in production data, which is what Live Proof means. At intake
add two STATUS rows with live `y`, `the-production-worker-serves-the-verified-version` and
`the-production-worker-is-observable-and-reversible`; the second must reach Operational before the run is Done.

## 15. Moving an external service behind a service binding

The Cloudflare half of a `move/migration`, whose charter and ledgers live in MIGRATION.md; the steps fit any HTTP service.

1. **Inventory consumers** from the old service's own logs over one full traffic cycle (grouped by caller identity and
   user agent; without caller identity, deploy identity logging first and keep building meanwhile), then grep every
   reachable repository for hostnames, env var names, base URLs and binding names, and list every schedule. `unknowns` must
   be empty before the first traffic step. Record old secret names with `wrangler secret list`; values cannot be read back.
2. **Freeze the contract** as OpenAPI in `contracts/<service>.legacy.json` with goldens for its deterministic decisions.
   Take the cost and latency baseline in a comparison week that contains no provider price change.
3. **Extract the seam**: a typed client interface as an adapter over the old service, every internal consumer moved
   onto it, shipped alone with the suite green.
4. **Build behind a service binding**: a `WorkerEntrypoint` bound as
   `"services": [{ "binding": "GATEWAY", "service": "core-gateway", "entrypoint": "GatewayEntrypoint" }]`. Binding calls
   count as subrequests and a chain crosses at most 32 Workers. Access context does not propagate across a binding, so
   the callee authorises on its own terms with a caller id argument. The rate limit binding is per location; if the old
   service enforced global limits, build that or record the semantic change as a decision. For a model gateway, use the
   AI Gateway binding or `getUrl(provider)`; the universal endpoint is deprecated.
5. **Shadow**: serve the old result, run the new path under `ctx.waitUntil(candidate(request.clone()))`, and publish
   `{ parity, route, diff_keys, version }` to Analytics Engine or a `parity_events` table. Compare decisions, not model
   text: identity, tenant, provider and model, cache key, rate-limit verdict, cost line, log row. Shadow decision logic
   on 100% with a stubbed upstream and the full path on a 1 to 10% sample. Never shadow writes to shared stores;
   dual-write with an idempotency key and compare at read time.
6. **Parity gate**, computed from the logged events: zero mismatches on identity, tenant and cost; at most 0.1% overall
   after named normalisers; new-path error rate at most control plus 0.1 percentage points; p95 at most 1.2 times
   control. A second normaliser for the same class of mismatch stops the work for an investigation.
7. **Cut over** per consumer, smallest first, with a flag (a var, or a KV key read with a 60-second `cacheTtl`), then a
   gradual deployment of the core Worker, pinning bound Workers with the `Cloudflare-Workers-Version-Overrides` header
   to avoid version skew. Keep shadow logging on, inverted, for one more window.
8. **Drill the rollback** at the first non-zero weight exactly as the undo ledger says (flag, then `wrangler rollback`),
   confirm from logs that traffic returned, and roll forward. Never pair a schema step with a cutover release.
9. **Retire**: disable old routes, schedules and tokens behind a logged refusal; observe zero hits for a cycle; delete
   code; delete resources through the scheduled check `references/shapes/move.md` describes, after the rollback window
   with an export kept; rotate every token the old service held, including a model gateway's Authenticated Gateway token.

## 16. Operational gates before Done

The `ops:` file answers each gate with a command output or a link:

- `/health` on the production route shows the ladder's `NEW` with its checks, and Workers Logs (or `wrangler tail`)
  returned the structured line for a real smoke request id.
- An error budget is stated (default: exceptions and 5xx under 0.5% of requests) and checked from Workers Logs over the
  canary window and a load run such as `oha -n 300 -c 10 https://<domain>/<read route>` with a concurrent
  `wrangler tail --status error`; if exceeded, the row stays at Live Proof. `wrangler d1 insights <db> --env production`
  shows no hot query without an index.
- Alerting exists: a Budget Alert on the account and an external `/health` prober (Health Checks on a Pro or higher
  zone, otherwise a third-party monitor). The file says plainly that Cloudflare has no native Workers error-rate alert.
- Monthly cost is projected from the smoke and load numbers (D1 rows, requests, CPU ms, neurons, Vectorize dimensions,
  R2 storage) with pricing URLs; every required secret name appears in `wrangler secret list`, tokens are scoped and
  rotated where a cutover happened, and `git log --all -- '.dev.vars*'` is empty.
- Retention is stated (Workers Logs 7 days, R2 rules from `wrangler r2 bucket lifecycle list <bucket>`, D1 Time Travel
  30 days), and rollback was rehearsed once on staging (old version to 100%, smoke green, new back) with elapsed time.

## 17. Anti-patterns to refuse

| Refuse | Do instead |
|---|---|
| `sql.js`, in-memory KV maps or hand-written binding fakes where a local binding exists | workerd through `@cloudflare/vitest-plugin` |
| `@cloudflare/vitest-pool-workers` or Vitest 5 in the Worker project | the plugin with `vitest@^4.1.0` |
| `BEGIN TRANSACTION`; IN lists from unbounded arrays; LIKE patterns from raw input; GLOB classes in CHECKs; large JSON columns in list queries | `batch()`, the guard module, `IN (...)` checks, single-row projection |
| Outer-variable assignment inside Workflow steps; reused instance ids; `waitUntil` for work over 25 s or needing retries | step returns only; ids from idempotency keys; a Workflow or a Queue |
| KV for anything read right after writing; the rate limit binding as a quota | D1, and a D1 counter in the same `batch()` |
| Durable Objects in the API Worker without a real-time requirement | a separate Worker, or none |
| A missing or copied old `compatibility_date` | a current date and `wrangler types --check` |
| Mocked model or vector output with no real call anywhere | the remote-binding test |
| Quoted secret values; secrets in `vars` | `printf '%s'` into `wrangler secret put` |
| A contract migration in the same release as the code change | expand now, contract one release later |
| Waiting for a cron; Workers Builds deploying around the ladder | trigger now; `versions upload` only |
| "Deployed" because a URL printed; preview results reported as Live Proof; uploading without checking the Worker name | sections 13 and 14 |

The lesson loop appends entries below using the lesson template (`templates/lesson.md`), capped at 40 entries.

## Learned constraints
