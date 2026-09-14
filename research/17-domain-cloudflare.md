# 17 · Domain pack: Cloudflare backends

Researcher report for the `/drive` skill. Component: what the skill must know, instruct, and gate when the backend runs on Cloudflare (Workers, D1, R2, KV, Durable Objects, Queues, Workflows, Workers AI, AI Gateway, Vectorize, static assets). Facts were checked against developers.cloudflare.com on 2026-09-14; the owner's own production lessons come from his Arcwell memory notes and are labelled as such.

---

## 1. Executive opinion

Cloudflare is a platform of hard, documented, low ceilings that the local tooling does not enforce. That single property decides what the skill has to do. D1 stops at 100 bound parameters and 100 KB per statement; a Worker gets 30 seconds of CPU by default and `waitUntil` buys 30 more seconds of wall time after the response; a Workflow step forgets anything it did not return; a preview URL has no logs at all; a rollback moves code but never the schema. None of those limits bite in `wrangler dev` or in a Node shim, and several do not bite in workerd either. The owner's 100-bind incident (24 green runs, one live failure) is the archetype, not an outlier.

So the pack's job is threefold. First, make the agent build the limits into the code under test: a single D1 access module that refuses more than 100 binds and chunks IN lists, a Workflow style that returns every computed value, a `waitUntil` budget, structured logs with a request id. Second, make the test harness as unkind as production: run tests in workerd with `@cloudflare/vitest-plugin` (the package was renamed from `vitest-pool-workers` on 2026-08-19; Hono's docs still show the old name), apply the real migrations, write at least one refutation test per limit, and probe the remote D1 once to learn where the local simulator is kinder. Third, make "Live Proof" a literal thing: a smoke suite that runs against a preview alias of the uploaded version with the real bindings, checks the served version id, does a real write, upload, Workflow run, and read, and writes a proof packet before the version takes 10% and then 100% of traffic.

For the fashion app I recommend one Worker (Hono, Zod-first OpenAPI, Swift client generated from the committed contract), D1 as system of record, R2 with presigned PUTs for photos, one Workflow for garment ingest (thumbnail, vision attributes, embedding, Vectorize upsert), Workers AI through the AI Gateway binding, KV only for config and the Apple JWKS cache, and no Durable Objects in the API Worker at all, because DO lifecycle changes block `versions upload`, preview URLs, and rollbacks.

## 2. What the post says, and a critique

The post never mentions Cloudflare, so this section is about how its general claims land on this platform.

Where it is right: the insistence that the agent which wrote the code must not be the agent that grades it applies with unusual force here, because the maker's tests are exactly what certified the broken `session_brief`. A verifier that re-derives the limits from the docs and runs its own refutation tests is the only structure that would have caught it. The post's "verified facts" section of the state file is also the right home for platform limits once they have been confirmed by a failing test, not merely by reading a page.

Where it is exaggerated: "writes its own tests to check its work" is presented as a capability, when on Cloudflare the interesting question is not whether tests exist but whether the runtime under them is production-shaped. A self-written test against `sql.js` is worse than no test, because it manufactures confidence. The post's Routines pitch ("laptop-off cloud runs") also inverts the owner's rule: on Cloudflare the agent should never wait for a cron; `wrangler dev --test-scheduled` exposes `/cdn-cgi/local/scheduled`, and live Workflows are triggered with `wrangler workflows trigger`. Anything reported as "will run at the next tick" is not done.

Where it is wrong for this owner: graders on Haiku. He has said Sonnet at low effort. The post also has nothing to say about domain conditionals, which is the whole point of a pack like this one: the skill should load `references/cloudflare.md` only when the repository has a `wrangler.jsonc|toml|json` or the goal names the platform, and then apply the gates unconditionally.

## 3. Verified facts

Each line is a fact I read on the cited page on 2026-09-14 unless marked otherwise. "Owner" marks an empirical lesson from the Arcwell memory notes; those are source claims from production, not docs.

### Workers runtime and configuration

- CPU time: Free 10 ms; Paid default 30 s, configurable to 300,000 ms via `limits.cpu_ms`. Memory 128 MB per isolate. Bundle 64 MiB uncompressed. Cron, Queue consumer, and DO alarm invocations get 15 minutes of wall time. `waitUntil` extends execution up to 30 seconds after the response is sent, shared across all `waitUntil` calls, after which unsettled promises are cancelled. https://developers.cloudflare.com/workers/platform/limits/ and https://developers.cloudflare.com/workers/runtime-apis/context/
- Subrequests: Free 50 per invocation; Paid default 10,000, raisable via `limits.subrequests`. KV, D1, R2, Cache, Queues and `fetch` all count. Six simultaneous connections may be awaiting response headers at once. The service-bindings page still says 1,000 on Paid; the limits page is the newer statement, but the skill should design under 1,000 and not lean on the difference. https://developers.cloudflare.com/workers/platform/limits/#subrequests and https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/
- Service bindings count toward the subrequest limit, not toward the connection limit; a request chain may pass through at most 32 Worker invocations; RPC via `WorkerEntrypoint` is the recommended style. Same URL.
- `compatibility_date` omitted via the API defaults to 2021-11-02; the recommendation is to set the current date on new projects and revisit it deliberately. https://developers.cloudflare.com/workers/configuration/compatibility-dates/
- Node.js compatibility is on by default for `compatibility_date` ≥ 2026-08-04; between 2024-09-23 and 2026-08-03 it needs `compatibility_flags: ["nodejs_compat"]`. Unsupported modules are stubbed by unenv and throw or no-op. https://developers.cloudflare.com/workers/runtime-apis/nodejs/
- Configuration keys: `limits.cpu_ms`, `limits.subrequests`, `observability.enabled` (defaults true), `observability.head_sampling_rate`, `workers_dev`, `preview_urls` (defaults to the value of `workers_dev`), `keep_vars` (top-level only), `secrets.required` (deploy fails if any listed secret is unset), `assets.directory|not_found_handling|run_worker_first`, the declarative `exports` block for Durable Objects (mutually exclusive with the legacy `migrations` array), `env.<name>`. Bindings, `vars`, and secrets are not inheritable across environments and must be redeclared per environment. https://developers.cloudflare.com/workers/wrangler/configuration/ and https://developers.cloudflare.com/workers/wrangler/environments/
- Environments deploy as separate Workers named `<name>-<env>` unless `name` is overridden inside the env block; deploy with `--env` or `CLOUDFLARE_ENV`; service bindings target an env by suffix (`worker-a-staging`). https://developers.cloudflare.com/workers/wrangler/environments/
- Rate limiting binding: `ratelimits` config with `namespace_id`, `simple.limit`, `simple.period` of 10 or 60 seconds only; counters are per Cloudflare location and eventually consistent; the docs say it is "intentionally designed to not be used as an accurate accounting system". Wrangler 4.36+. https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/
- Version metadata binding exposes `id`, `tag`, `timestamp`. https://developers.cloudflare.com/workers/runtime-apis/bindings/version-metadata/
- Smart Placement (`placement.mode: "smart"`) moves fetch-handler execution near a backend after observing traffic; `cf-placement` header reports `remote-XXX` or `local-XXX`; it needs consistent traffic from several locations to engage. https://developers.cloudflare.com/workers/configuration/smart-placement/
- Custom domains: `routes: [{ pattern, custom_domain: true }]`, zone must be on Cloudflare, DNS and certificate are provisioned automatically. https://developers.cloudflare.com/workers/configuration/routing/custom-domains/
- Cron: `triggers.crons`; local test route `http://localhost:8787/cdn-cgi/local/scheduled?cron=...` under `wrangler dev --test-scheduled`; crons run in UTC; changes can take up to 15 minutes to propagate. https://developers.cloudflare.com/workers/configuration/cron-triggers/

### Versions, deployments, previews, secrets

- `wrangler deploy` creates and deploys a version in one step and must be used for the first upload; `wrangler versions upload --message --tag --preview-alias` creates a version without deploying; `wrangler versions deploy <id>@10% <id>@90% --yes` splits traffic; a deployment may include only the last 100 versions; `wrangler rollback [<VERSION_ID>] --message` makes a single-version deployment. https://developers.cloudflare.com/workers/versions-and-deployments/ , https://developers.cloudflare.com/workers/configuration/versions-and-deployments/gradual-deployments/ , https://developers.cloudflare.com/workers/wrangler/commands/workers/
- Rollback does not change bindings, secrets, or D1 schema; it is blocked across a Durable Object lifecycle change or if the target version binds a deleted resource; the docs warn that code from a prior version can error if data structure changed. https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/
- Preview URLs: `<alias-or-version-prefix>-<worker>.<subdomain>.workers.dev`; not available for Workers with Durable Objects, Containers, or Sandbox; no logs of any kind (Workers Logs, tail, Logpush); public unless fronted by Cloudflare Access. https://developers.cloudflare.com/workers/configuration/previews/
- Durable Object lifecycle changes apply only via `wrangler deploy`; `versions upload` rejects configs containing them; they cannot roll out gradually; rollbacks cannot cross them. https://developers.cloudflare.com/durable-objects/reference/durable-objects-migrations/
- Secrets: `wrangler secret put <KEY> --env <env>` (new version, immediate deploy), `wrangler versions secret put` for staged, `wrangler secret bulk <file> --env` (JSON with `null` to delete needs 4.97+), `.dev.vars` and `.dev.vars.<env>` for local (if the env-specific file exists, only it loads); values are not visible after set. https://developers.cloudflare.com/workers/configuration/secrets/
- `wrangler deploy --dry-run --outdir <dir>` bundles without uploading; `wrangler types --env-interface Env --check`; `wrangler check startup` profiles startup locally. https://developers.cloudflare.com/workers/wrangler/commands/workers/
- Workers Builds: production branch defaults to `npx wrangler deploy`, other branches to `npx wrangler versions upload`; root directory setting for monorepos; Worker name must match config `name`. https://developers.cloudflare.com/workers/ci-cd/builds/configuration/

### Observability

- Workers Logs: `observability.enabled`, `head_sampling_rate`, `logs.invocation_logs`; retention 3 days Free / 7 days Paid; 200k events/day Free, 20M/month Paid then $0.60 per million; 256 KB per event; account cap 5 billion events/day after which a 1% head sample applies; JSON objects passed to `console.log` are field-indexed. https://developers.cloudflare.com/workers/observability/logs/workers-logs/
- `wrangler tail [WORKER] --format json --status error --sampling-rate --version-id --env`; at most 10 concurrent tail clients; high volume drops into sampling mode. https://developers.cloudflare.com/workers/observability/logs/real-time-logs/
- Tail Workers: `tail_consumers`, `tail(events)` handler, billed by CPU time, Paid plan. https://developers.cloudflare.com/workers/observability/logs/tail-workers/
- Analytics Engine: `analytics_engine_datasets` binding; per `writeDataPoint` 20 blobs, 20 doubles, 1 index (96 bytes); 250 data points per invocation; 3-month retention. https://developers.cloudflare.com/analytics/analytics-engine/limits/
- There is no native Workers error-rate alert in the notifications catalogue; Budget Alerts (announced 2026-04-13) email when projected monthly spend crosses a threshold; Health Checks exist on Pro (10), Business (50), Enterprise (1,000) zones, not Free. https://developers.cloudflare.com/notifications/notification-available/ , https://developers.cloudflare.com/changelog/post/2026-04-13-billable-usage-dashboard-and-budget-alerts/ , https://developers.cloudflare.com/health-checks/

### D1

- Limits: 10 GB per database (Paid), 100 bound parameters per query, 100 KB per SQL statement (applies to each statement inside a batch), 100 columns per table, 2 MB per row/string/blob, 32 arguments per SQL function, 50 bytes per LIKE/GLOB pattern, 30 s query duration (also the whole batch), 1,000 queries per Worker invocation (Paid), 6 simultaneous connections. https://developers.cloudflare.com/d1/platform/limits/
- `batch()` is the transactional primitive ("If a statement in the sequence fails ... it aborts or rolls back the entire sequence"); D1 runs in auto-commit; `exec()` is for maintenance only; `meta` carries `rows_read`, `rows_written`, `served_by_region`, `served_by_primary`, `changes`, `last_row_id`. https://developers.cloudflare.com/d1/worker-api/d1-database/
- Migrations: `wrangler d1 migrations create|list|apply <DB> --local|--remote|--preview`; tracked in `d1_migrations`; `migrations_dir` and `migrations_table` configurable; no down migrations. https://developers.cloudflare.com/d1/reference/migrations/ and https://developers.cloudflare.com/d1/wrangler-commands/
- Read replication requires the Sessions API (`withSession("first-primary" | "first-unconstrained" | bookmark)`), otherwise every query still goes to the primary; sequential consistency via bookmarks; `served_by_*` are undefined under `wrangler dev`; no extra charge. https://developers.cloudflare.com/d1/best-practices/read-replication/
- Pricing: Paid includes 25 billion rows read and 50 million rows written per month, then $0.001 per million read and $1.00 per million written; 5 GB storage included then $0.75/GB-month; index updates count as extra rows written. https://developers.cloudflare.com/d1/platform/pricing/
- Time Travel: 30 days Paid; `wrangler d1 time-travel info|restore --timestamp|--bookmark`; restore is destructive and in place but returns a bookmark of the prior state. https://developers.cloudflare.com/d1/reference/time-travel/
- Export: `wrangler d1 export <DB> --remote --output f.sql [--no-data|--no-schema|--table]`; exports block other requests; FTS5 virtual tables are not exported; `d1 execute --file` up to 5 GiB. https://developers.cloudflare.com/d1/best-practices/import-export-data/
- Owner: D1 rejects `GLOB '[...]'` character classes; a long `LIKE` term trips "LIKE too complex"; joining a multi-KB blob column onto thousands of rows throws `D1_ERROR: Memory limit exceeded before EOF`; a full D1→R2 backup exceeds one request's CPU (error 1102) and only survives under `waitUntil`; paged reads on a large table can be rate-limited ("too many requests"/"overloaded").

### R2, KV, Durable Objects, Queues

- R2 presigned URLs: generated locally with any SigV4 implementation (AWS SDK shown), need an R2 API token pair and the account endpoint; expiry 1 second to 7 days; single S3 operation on a single object; `ContentType` in the signature restricts the upload type; multipart via presigned POST not supported. https://developers.cloudflare.com/r2/api/s3/presigned-urls/
- R2 limits: 5 GiB single PUT, 10,000 parts multipart, 1,024-byte keys, 8 KB metadata, one write per second per key (429 beyond), 1,000 lifecycle rules per bucket, lifecycle actions run within roughly 24 hours; `wrangler r2 bucket lifecycle add|set|list|remove`. https://developers.cloudflare.com/r2/platform/limits/ and https://developers.cloudflare.com/r2/buckets/object-lifecycles/
- KV: eventually consistent, propagation "up to 60 seconds or more", negative lookups cached, one write per second per key, 512-byte keys, 25 MiB values, 1,000 operations per invocation, minimum `cacheTtl` 30 s; not for read-after-write or atomic operations. https://developers.cloudflare.com/kv/concepts/how-kv-works/ and https://developers.cloudflare.com/kv/platform/limits/
- Durable Objects: SQLite-backed is the only path for new namespaces (`exports: { Cls: { type: "durable-object", storage: "sqlite" } }`); 10 GB per object, 100 binds, 100 KB statements, 2 MB rows, ~1,000 req/s soft limit per object; `sql.exec` is implicitly transactional, `transactionSync` for multi-statement, no `BEGIN`; 30-day point-in-time bookmarks. https://developers.cloudflare.com/durable-objects/platform/limits/ and https://developers.cloudflare.com/durable-objects/api/sqlite-storage-api/
- Queues: 128 KB messages, 100 per batch, retention up to 14 days, 5,000 msg/s per queue, 250 concurrent push consumers, 100 retries max, 24 h max delay, 15-minute consumer wall time; consumer config `max_batch_size` (10), `max_batch_timeout` (5 s), `max_retries` (3), `dead_letter_queue`, `max_concurrency`, `retry_delay`; billed per 64 KB operation, roughly three per delivered message. https://developers.cloudflare.com/queues/platform/limits/ , https://developers.cloudflare.com/queues/configuration/configure-queues/ , https://developers.cloudflare.com/workers/platform/pricing/

### Workflows

- Limits: 10,000 steps per instance (Paid, raisable to 25,000; `step.sleep` excluded), 1 MiB per non-stream step return, 1 GB persisted state per instance, 30-day retention of completed state (Paid), sleep up to a year, 300 instances/second per account, step CPU 30 s default (configurable to 5 minutes). https://developers.cloudflare.com/workflows/reference/limits/
- Rules: make bindings idempotent; keep steps granular; "Do not rely on state outside of a step" because the engine hibernates and loses in-memory state; build top-level state exclusively from `step.do` returns; wrap `Math.random()`, `Date.now()`, `Promise.race` in steps; name steps deterministically (names are cache keys); the `event` is immutable; always `await` steps; instance ids must be unique; keep timeouts ≤ 30 minutes and use `waitForEvent` for longer waits. https://developers.cloudflare.com/workflows/build/rules-of-workflows/
- API: `step.do(name, { retries: { limit, delay, backoff }, timeout }, cb, rollbackOptions?)`; `NonRetryableError` stops retries; `create({ id, params })` throws on a duplicate id within retention while `createBatch` skips duplicates; `instance.status()` returns `queued|running|paused|errored|terminated|complete|waiting|...` plus `output`; `restart({ from })` and `terminate({ rollback })`. https://developers.cloudflare.com/workflows/build/workers-api/
- CLI: `wrangler workflows trigger <NAME> '<json>' [--id]`, `instances list --status`, `instances describe <NAME> <ID|latest> --step-output`, `instances terminate|pause|resume|restart|send-event`; `--local` targets a dev session (Wrangler 4.79+). https://developers.cloudflare.com/workers/wrangler/commands/workflows/
- Owner: replay re-returns the memoised step value without re-running the callback, so a closure variable mutated inside a step silently reverts; this bit twice (the midnight `briefKey`, the audit story-drop).
- Pricing: Paid includes 500,000 steps/month then $0.80 per additional 100,000; Workflows share the Workers request and CPU allowances. https://developers.cloudflare.com/workers/platform/pricing/

### AI: Workers AI, AI Gateway, Vectorize, Images

- Workers AI: 10,000 free neurons/day, $0.011 per 1,000 neurons on Paid; `@cf/meta/llama-3.2-11b-vision-instruct` $0.049/M input, $0.676/M output; `@cf/baai/bge-m3` $0.012/M input tokens, 60,000-token context, `text[]` or `query+contexts` modes (the page does not state the output dimension; confirm with one call before creating the Vectorize index); rate limits 300 rpm text generation, 3,000 rpm embeddings, 720 rpm image-to-text. https://developers.cloudflare.com/workers-ai/platform/pricing/ , https://developers.cloudflare.com/workers-ai/models/bge-m3/ , https://developers.cloudflare.com/workers-ai/platform/limits/
- Workers AI, Vectorize, Browser Rendering, and mTLS have no local simulation; in `wrangler dev` and the vitest plugin they must be mocked or declared `remote: true`. https://developers.cloudflare.com/workers/development-testing/
- AI Gateway: Authenticated Gateway requires `cf-aig-authorization: Bearer <token>` on provider-native endpoints or `Authorization: Bearer` on the REST path; the `AI Gateway Run` permission is account-wide, so any such token reaches every gateway and every BYOK key in the account; binding requests are pre-authenticated. https://developers.cloudflare.com/ai-gateway/configuration/authentication/
- BYOK keys live in Secrets Store under `{gateway}_{provider}_{alias}`; the binding and unified endpoints use only the `default` alias and fall through to Unified Billing when it is absent; provider-native endpoints honour `cf-aig-byok-alias`. https://developers.cloudflare.com/ai-gateway/configuration/bring-your-own-keys/
- Binding methods: `env.AI.run(model, input, { gateway: { id, skipCache, cacheTtl, cacheKey, metadata } })`, `env.AI.gateway(id).getUrl(provider)` for SDK base URLs, `getLog`/`patchLog` for feedback, `env.AI.aiGatewayLogId`. https://developers.cloudflare.com/ai-gateway/integrations/worker-binding-methods/
- Owner: on gateway `arcwell`, DeepSeek ran BYOK on the `/deepseek` provider path while `/ai/v1` returned 402 for it; `cf-aig-skip-cache: true` was needed to stop a stale cached compose from double-charging semantics; reasoning tokens count against `max_tokens`.
- Vectorize: 1,536 dimensions max, 20 million vectors per index, 10 KiB metadata per vector, topK 50 with metadata or 100 without, 1,000 vectors per Worker upsert, 10 metadata indexes; Paid includes 50M queried and 10M stored dimensions, then $0.01 per million queried and $0.05 per 100 million stored. https://developers.cloudflare.com/vectorize/platform/limits/ and https://developers.cloudflare.com/vectorize/platform/pricing/
- Images binding: `images: { binding }`; `env.IMAGES.input(stream).transform({ width, height, fit }).output({ format }).response()`; 20 MB input; billed per unique source-plus-parameters per month; `.info()` free; low-fidelity locally, full fidelity with `remote: true`. https://developers.cloudflare.com/images/transform-images/bindings/

### Testing

- The Workers Vitest integration is `@cloudflare/vitest-plugin` (renamed from `@cloudflare/vitest-pool-workers` on 2026-08-19; API unchanged; codemod `npx @cloudflare/codemods vitest:pool-workers-to-vitest-plugin`; tsconfig types `@cloudflare/vitest-plugin/types`). It requires Vitest 4.1+. Config is `defineConfig({ plugins: [cloudflareTest({ wrangler: { configPath, environment }, main, miniflare })] })`; `defineWorkersConfig` and `poolOptions.workers` are gone. https://developers.cloudflare.com/changelog/post/2026-08-19-vitest-plugin/ , https://developers.cloudflare.com/workers/testing/vitest-integration/migration-guides/migrate-to-vitest-plugin/ , https://developers.cloudflare.com/workers/testing/vitest-integration/get-started/write-your-first-test/ , https://developers.cloudflare.com/workers/testing/vitest-integration/configuration/
- `env` and `exports` now come from `cloudflare:workers`; `SELF` is replaced by `exports` (which does not expose Assets); `cloudflare:test` exports `createExecutionContext`, `waitOnExecutionContext`, `createScheduledController`, `createMessageBatch`, `getQueueResult`, `runInDurableObject`, `runDurableObjectAlarm`, `listDurableObjectIds`, `applyD1Migrations`, `introspectWorkflowInstance`, `introspectWorkflow`, `reset`. Type `env` via `declare module "cloudflare:workers" { interface ProvidedEnv { ... } }`. https://developers.cloudflare.com/workers/testing/vitest-integration/test-apis/
- Storage isolation is per test file by default; use `--max-workers=1 --no-isolate` to share state; the old `isolatedStorage`/`singleWorker` options are not in the plugin's documented option list. https://developers.cloudflare.com/workers/testing/vitest-integration/isolation-and-concurrency/
- D1 migrations in tests: `readD1Migrations(dir)` in the config, passed as a `TEST_MIGRATIONS` binding, applied with `applyD1Migrations(env.DB, env.TEST_MIGRATIONS)` in a setup file. https://developers.cloudflare.com/workers/testing/vitest-integration/configuration/
- Known issues: fake timers do not expire KV/R2/cache; dynamic `import()` fails inside handlers and DOs; WebSockets with DOs need `--no-isolate`; V8 coverage unsupported (use Istanbul); `require()`-of-ESM errors fixed with `deps.optimizer`. https://developers.cloudflare.com/workers/testing/vitest-integration/known-issues/
- Remote bindings (`"remote": true` on a binding) are GA for Wrangler 4.37+, the Vite plugin, and the Vitest plugin; the Worker still runs locally and binding calls are proxied to the deployed resource; Durable Objects, Workflows, vars, secrets, assets, version metadata, Analytics Engine and rate limits cannot be remote. https://developers.cloudflare.com/changelog/post/2025-09-16-remote-bindings-ga/ and https://developers.cloudflare.com/workers/development-testing/
- Hono's Cloudflare testing example still shows `@cloudflare/vitest-pool-workers` and `defineWorkersProject`; it is stale relative to Cloudflare's docs. https://hono.dev/examples/cloudflare-vitest

### Frameworks, contracts, auth

- Hono on Workers: `new Hono<{ Bindings: Env }>()`, `export default app` or `{ fetch: app.fetch, scheduled }`, `wrangler types --env-interface CloudflareBindings` for binding types. https://hono.dev/docs/getting-started/cloudflare-workers
- `@hono/zod-openapi`: `OpenAPIHono`, `createRoute({ method, path, request, responses })`, `app.openapi(route, handler)`, `app.doc('/doc', { openapi, info })`. https://hono.dev/examples/zod-openapi
- chanfana: class-based `OpenAPIRoute` with Zod v4 schemas, `fromHono(app)`, serves `/openapi.json` and `/docs`, OpenAPI 3.1, "considered stable and production ready", powers Cloudflare Radar's public API. https://github.com/cloudflare/chanfana
- swift-openapi-generator: SwiftPM build plugin, OpenAPI 3.0 and 3.1, `openapi-generator-config.yaml` with `generate: [types, client]`, URLSession transport for iOS 13+. https://github.com/apple/swift-openapi-generator
- jose runs on Cloudflare Workers; `createRemoteJWKSet(url)` + `jwtVerify(token, jwks, { issuer, audience })`. https://github.com/panva/jose
- Sign in with Apple server verification: fetch keys from `https://appleid.apple.com/auth/keys`, verify signature, `iss` = `https://appleid.apple.com`, `aud` = your bundle id / client id, `exp` in the future, nonce matches. https://developer.apple.com/documentation/signinwithapple/verifying-a-user
- `@simplewebauthn/server` documents Node 22+ and Deno 2.4+ only; no statement about Workers. https://simplewebauthn.dev/docs/packages/server

### Static sites

- Cloudflare's migration guide positions Workers with static assets over Pages for new full-stack projects; `assets.directory`, `not_found_handling` (`single-page-application` | `404-page` | `none`), `run_worker_first`; asset requests are free. https://developers.cloudflare.com/workers/static-assets/migration-guides/migrate-from-pages/

## 4. Detailed spec

### 4.0 Activation

The pack activates when any of these hold: a `wrangler.jsonc`, `wrangler.json`, or `wrangler.toml` exists anywhere in the repository (excluding `node_modules`); the goal or spec names Cloudflare, Workers, D1, R2, KV, Durable Objects, Queues, Workflows, Vectorize, Workers AI, or AI Gateway; or the architecture step chose Cloudflare. On activation the orchestrator loads `references/cloudflare.md` into the architect, implementer, and verifier prompts and appends the Cloudflare gates (section 4.7) to the Done criteria. The pack never activates on a bare mention of "the edge" or "serverless".

### 4.1 Repository layout the skill should produce or expect

```
apps/api/                  Worker source (Hono)
  src/index.ts             app + scheduled export
  src/env.ts               Env interface + secret inventory (comments only, no values)
  src/db/                  the ONLY module allowed to call env.DB.prepare
  src/db/guard.ts          platform-limit guards (see 4.4)
  src/workflows/           WorkflowEntrypoint classes
  src/http/errors.ts       error envelope
  migrations/              0001_init.sql ... (forward-only)
  wrangler.jsonc
  vitest.config.ts         workerd tests
  vitest.smoke.config.ts   node tests against a deployed URL
  test/setup/apply-migrations.ts
  test/workers/            unit + integration in workerd
  test/smoke/              live smoke (reads SMOKE_BASE_URL, SMOKE_TOKEN, EXPECTED_VERSION_ID)
contracts/openapi.json     committed contract, regenerated and diffed in tests
ios/                       Swift package/app; swift-openapi-generator reads ../contracts/openapi.json
.drive/proofs/<feature>/proof-packet.json
```

### 4.2 Service design for an agent-built API

Router and contract. Use Hono with `@hono/zod-openapi`. Every route is declared with `createRoute` carrying request and response schemas, so the handler cannot exist without a contract. Serve the document at `/openapi.json` and write it to `contracts/openapi.json` with a script (`node scripts/export-openapi.mjs`, which imports the app and calls `app.getOpenAPIDocument(...)`); a test fails if the committed file differs from the generated one. The Swift side consumes that file through the swift-openapi-generator build plugin, so a contract change that is not committed breaks the iOS build, which is the coupling we want. chanfana is an acceptable alternative (class-based, Cloudflare-maintained); pick one per repo and never mix. Emit `openapi: "3.1.0"`; both generators accept it.

Auth. Primary is Sign in with Apple, since this is an iOS app. The client sends the Apple identity token to `POST /auth/apple`; the Worker verifies it with jose against `https://appleid.apple.com/auth/keys` (issuer `https://appleid.apple.com`, audience `APPLE_BUNDLE_ID`, nonce echoed from the client), upserts the user by Apple `sub`, and issues its own tokens: a 15-minute access JWT signed with `SESSION_SIGNING_KEY` (HS256 is fine for one issuer; EdDSA if a second service must verify) and a 30-day opaque refresh token stored hashed in D1 with rotation on use and family revocation on reuse. Cache Apple's JWKS in KV with a `cacheTtl` of 3,600 seconds; that is one of the two legitimate uses of KV in this app. Passkeys are a later feature: no WebAuthn server library documents Workers support, so treat it as a research task with a spike test, not a default.

Rate limiting. Bind `ratelimits` with one namespace for authenticated traffic keyed by user id (say 120 per 60 s) and one for unauthenticated by client IP (20 per 60 s). Treat it as abuse damping, not quota; the docs say counters are per-location and permissive. Hard quotas (uploads per day, inference calls per day) live in a D1 `usage_counters` table updated in the same `batch()` as the write they meter.

Idempotency. Every creating `POST` accepts an `Idempotency-Key` header (UUID). Table `idempotency_keys(user_id, key, request_hash, status, body, created_at, PRIMARY KEY(user_id, key))`. On a hit with the same hash return the stored response; on a hit with a different hash return 409 `idempotency_mismatch`; purge rows older than 24 hours from the scheduled handler. Workflow instance ids are derived from the same key (`ingest:<user>:<garment>`) so a retried request cannot create a second instance; `create()` throws on duplicates, which the handler turns into "already running".

Error envelope. One shape everywhere: `{ "error": { "code": "validation_failed", "message": "...", "details": {...}, "request_id": "..." } }`. Codes are a closed union in `src/http/errors.ts` and appear in the OpenAPI document as an enum so the Swift client can switch on them. Zod failures map to 400 `validation_failed` via the OpenAPIHono `defaultHook`; unknown exceptions map to 500 `internal` with the request id and are logged with the stack. Every response carries `x-request-id`; the id is `crypto.randomUUID()` per request.

Observability. `observability.enabled: true`, `head_sampling_rate: 1` for a personal app. Log one JSON object per request from a Hono middleware: `{ request_id, route, method, status, ms, user_id, version }`, where `version` is `env.VERSION.id` from the version metadata binding. Log D1 `meta.rows_read` for queries above a threshold to catch scans. `GET /health` returns `{ ok, version: { id, tag, timestamp }, checks: { d1, r2 } }` after `SELECT 1` and a `HEAD` on a canary object; `/health` is the endpoint the smoke suite and any external prober hit. Product metrics (garments created, recommendations served, inference ms) go to Analytics Engine via `writeDataPoint`, within 20 blobs and 20 doubles.

Cost envelope. Workers Paid is the floor ($5/month) because D1 beyond 500 MB, `cpu_ms` above 30 s, 30-day Workflow retention, and 7-day logs all need it. For the fashion app at owner scale (one user, a few hundred garments, tens of recommendations a day) everything else sits inside the included allowances: D1 rows, Vectorize dimensions (a few hundred vectors times about a thousand dimensions is well under the 10M stored included), Workers AI (a few hundred vision calls a month are cents), R2 storage of a few GB. The skill writes this estimate into the spec with the pricing URLs and re-checks it after the load sanity run using real `rows_read` numbers.

### 4.3 Storage choices and the fashion app data model

Decision table the architect applies:

| Need | Choice | Why not the others |
|---|---|---|
| System of record: users, garments, outfits, wear log, sessions, idempotency | D1 | Relational, migrations, Time Travel, cheap; DO would fragment per-user data and complicate deploys |
| Photos and thumbnails | R2 via presigned PUT | Bytes never transit the Worker; lifecycle rules; zero egress |
| Multi-step ingest (thumbnail → vision → embed → index) | Workflows | Durable retries and step memoisation; Queues would need hand-rolled state |
| Similarity search for outfit candidates | Vectorize (namespace per user) | Built for this; D1 has no vector type |
| Embeddings and vision attributes | Workers AI via `env.AI.run` with `gateway` options; external models via AI Gateway BYOK | Gateway gives caching, logs, cost visibility, one token |
| Feature flags, Apple JWKS cache | KV | Read-heavy, staleness tolerated |
| Live collaboration, strict per-user counters, WebSockets | Durable Objects (only if a requirement appears) | Otherwise they cost preview URLs and gradual rollout |
| Fan-in of many external events | Queues (only if a requirement appears) | Workflows cover the pipeline case |

D1 schema (forward-only migrations; every table has `user_id`; every query filters on it):

```sql
CREATE TABLE users (id TEXT PRIMARY KEY, apple_sub TEXT UNIQUE NOT NULL, created_at INTEGER NOT NULL);
CREATE TABLE refresh_tokens (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, family TEXT NOT NULL, hash TEXT NOT NULL, expires_at INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
CREATE INDEX rt_user ON refresh_tokens(user_id, family);
CREATE TABLE garments (
  id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
  category TEXT NOT NULL, subcategory TEXT, colors_json TEXT NOT NULL, attributes_json TEXT NOT NULL,
  photo_key TEXT NOT NULL, thumb_key TEXT, status TEXT NOT NULL CHECK (status IN ('uploaded','processing','ready','failed')),
  ingest_instance_id TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
CREATE INDEX garments_user_created ON garments(user_id, created_at DESC);
CREATE INDEX garments_user_category ON garments(user_id, category);
CREATE TABLE outfits (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, name TEXT, occasion TEXT, created_at INTEGER NOT NULL);
CREATE TABLE outfit_items (outfit_id TEXT NOT NULL, garment_id TEXT NOT NULL, slot TEXT NOT NULL, PRIMARY KEY(outfit_id, garment_id));
CREATE TABLE wear_log (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, outfit_id TEXT, garment_id TEXT, worn_on TEXT NOT NULL, created_at INTEGER NOT NULL);
CREATE INDEX wear_user_day ON wear_log(user_id, worn_on);
CREATE TABLE idempotency_keys (user_id TEXT NOT NULL, key TEXT NOT NULL, request_hash TEXT NOT NULL, status INTEGER NOT NULL, body TEXT NOT NULL, created_at INTEGER NOT NULL, PRIMARY KEY(user_id, key));
CREATE TABLE usage_counters (user_id TEXT NOT NULL, day TEXT NOT NULL, metric TEXT NOT NULL, n INTEGER NOT NULL, PRIMARY KEY(user_id, day, metric));
```

Rules the implementer must follow, each with a refutation test (4.4): keep `attributes_json` small and never select it in list queries alongside many rows (owner's blob-join memory bomb); chunk every IN list at 90 parameters; never build a `LIKE` pattern from user input longer than 50 bytes and never use GLOB character classes; use `batch()` when a request must write two tables; keep `CHECK` constraints simple (`IN (...)`, not GLOB).

Photo upload flow. `POST /uploads {content_type, bytes}` → the Worker validates type (`image/jpeg|png|heic|webp`) and size (≤ 20 MB, the Images binding input cap), mints `photos/<user>/<garment>/orig` and returns a presigned PUT (aws4fetch in the Worker with `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` scoped to the bucket, `ContentType` in the signature, 900-second expiry). The Swift client PUTs straight to R2. `POST /garments {photo_key, idempotency}` → the Worker `HEAD`s the key through the R2 binding to confirm it exists and matches the declared type, inserts the garment as `uploaded`, and creates the `GarmentIngest` Workflow with id `ingest:<user>:<garment>`. Lifecycle rules: `photos/*/tmp/` delete after 1 day; abort incomplete multipart after 7 days (default); nothing else expires.

`GarmentIngest` Workflow (each step returns its value; nothing is assigned to outer variables):

1. `thumbnail`: read original from R2, `env.IMAGES.input(...).transform({ width: 512, fit: "cover" }).output({ format: "image/webp" })`, write `thumb` key, return `{ thumb_key, width, height }`.
2. `attributes`: call `env.AI.run("@cf/meta/llama-3.2-11b-vision-instruct", ..., { gateway: { id, cacheTtl: 0, metadata: { user_id, garment_id } } })` with a JSON-only prompt; parse with Zod (strip code fences first, an owner lesson); on parse failure retry with the validation error appended; after 3 failures throw `NonRetryableError`; return the attributes object.
3. `embed`: build a canonical description string from the attributes, `env.AI.run("@cf/baai/bge-m3", { text: [description] })`, return `{ vector }` (under 1 MiB; a 1,024-float vector is ~8 KB as JSON).
4. `index`: `env.GARMENT_INDEX.upsert([{ id: garment_id, values: vector, namespace: user_id, metadata: { category, colors } }])`, return `{ mutation_id }`.
5. `commit`: one D1 `batch()` updating `garments` to `ready` with `thumb_key`, `attributes_json`, `colors_json`; return `{ updated_at }`.

Failure path: any terminal error sets `garments.status = 'failed'` in a final step guarded by try/catch around the run, and the client sees it on `GET /garments/:id`. The Workflow's `run` returns a small summary object so `wrangler workflows instances describe <name> <id>` shows it.

Recommendation inference (`GET /recommendations?occasion=&weather=`). Retrieve candidates by querying Vectorize with the embedding of a generated "need" string (topK 50 with metadata, namespace user), filter by hard rules in code (category coverage, recently worn from `wear_log`), then ask a text model through the gateway to assemble 3 outfits from at most 30 candidate garments, returning ids only, validated against the candidate set so the model cannot invent a garment. Cache per `(user, occasion, weather bucket, day)` with `cacheTtl` on the gateway and a D1 `recommendations` row; a `?fresh=1` query sets `skipCache: true`. This keeps model cost proportional to distinct requests, not app opens.

Read replication and placement. Do not enable D1 read replication for a single-user app; if it is enabled later the Sessions API becomes mandatory (`withSession("first-primary")` on the request following a write, or a bookmark header echoed by the Swift client), otherwise nothing changes. Turn on `placement: { mode: "smart" }`; with several D1 round trips per request it is a cheap latency win and the `cf-placement` header shows whether it engaged.

### 4.4 Testing: as strict as production

Packages and config (verified 2026-09-14):

```bash
npm i -D vitest@^4.1.0 @cloudflare/vitest-plugin
```

```ts
// apps/api/vitest.config.ts
import path from "node:path";
import { defineConfig } from "vitest/config";
import { cloudflareTest, readD1Migrations } from "@cloudflare/vitest-plugin";

export default defineConfig({
  plugins: [
    cloudflareTest(async () => ({
      wrangler: { configPath: "./wrangler.jsonc", environment: "test" },
      miniflare: {
        bindings: { TEST_MIGRATIONS: await readD1Migrations(path.join(__dirname, "migrations")) },
      },
    })),
  ],
  test: {
    include: ["test/workers/**/*.test.ts"],
    setupFiles: ["./test/setup/apply-migrations.ts"],
  },
});
```

```ts
// apps/api/test/setup/apply-migrations.ts
import { env } from "cloudflare:workers";
import { applyD1Migrations } from "cloudflare:test";
import { beforeAll } from "vitest";
beforeAll(async () => { await applyD1Migrations(env.DB, env.TEST_MIGRATIONS); });
```

```ts
// apps/api/test/workers/garments.test.ts (shape)
import { env, exports } from "cloudflare:workers";
import { createExecutionContext, waitOnExecutionContext } from "cloudflare:test";
import { describe, it, expect } from "vitest";
import app from "../../src/index";
```

`tsconfig.test.json` gets `"types": ["@cloudflare/vitest-plugin/types"]` and the `ProvidedEnv` augmentation for `TEST_MIGRATIONS`. The `test` environment in `wrangler.jsonc` redeclares the bindings with placeholder ids (miniflare ignores them) and keeps Workers AI and Vectorize either mocked (see the recipe "Mock Workers AI and Vectorize bindings in unit tests") or declared `remote: true` pointing at staging resources for the one remote-parity test described below.

Guards in the code under test. The whole point of the owner's lesson is that the constraint must live in the code, where every test path exercises it:

```ts
// src/db/guard.ts
export const D1_MAX_BIND = 100;
export const D1_MAX_SQL_BYTES = 100_000;
export const D1_MAX_LIKE_BYTES = 50;
export const D1_IN_CHUNK = 90;

export class PlatformLimitError extends Error {
  constructor(public limit: string, public actual: number, public max: number) {
    super(`${limit}: ${actual} exceeds ${max}`);
  }
}
export function guardStatement(sql: string, params: readonly unknown[]): void {
  if (params.length > D1_MAX_BIND) throw new PlatformLimitError("d1_bind_params", params.length, D1_MAX_BIND);
  const bytes = new TextEncoder().encode(sql).byteLength;
  if (bytes > D1_MAX_SQL_BYTES) throw new PlatformLimitError("d1_sql_bytes", bytes, D1_MAX_SQL_BYTES);
}
export function guardLike(pattern: string): string {
  const bytes = new TextEncoder().encode(pattern).byteLength;
  if (bytes > D1_MAX_LIKE_BYTES) throw new PlatformLimitError("d1_like_bytes", bytes, D1_MAX_LIKE_BYTES);
  return pattern;
}
export function chunk<T>(items: readonly T[], size = D1_IN_CHUNK): T[][] { /* ... */ }
```

`src/db/index.ts` exposes `q(env, sql, params)`, `qAll`, `qFirst`, `batch(env, stmts)`, each calling `guardStatement` before `prepare().bind()`. A repo-level test greps `src/` for `\.prepare\(` outside `src/db/` and fails if any is found, so the guard cannot be bypassed by a later change.

Refutation tests (one per limit, named `severe_*` per the owner's convention):

- `severe_in_list_over_100`: insert 250 garments for one user; call `GET /garments?ids=<all 250>`; expect 200 and 250 rows (chunking works). Then call `guardStatement` directly with 101 params and expect `PlatformLimitError`.
- `severe_sql_length`: build a statement of 100,001 bytes and expect the guard to throw before D1 sees it.
- `severe_like_length`: search with a 51-byte term; expect 400 `validation_failed`, not a D1 error.
- `severe_blob_projection`: a static test asserts that no list query in `src/db/garments.ts` selects `attributes_json` (regex over the module), and a runtime test lists 5,000 garments with 4 KB attribute blobs and expects success.
- `severe_batch_atomicity`: a two-statement batch whose second statement violates a constraint; expect the first not to persist.
- `severe_workflow_returns_state`: run `GarmentIngest` under `introspectWorkflowInstance` with mocked AI; assert the final summary equals a function of step outputs only. Pair it with a lint gate (`scripts/lint-workflows.mjs`) that flags any assignment to an identifier declared outside a `step.do` callback body; ambiguous hits go to a Sonnet low-effort classifier.
- `severe_waituntil_budget`: the scheduled handler's background work is wrapped in a helper that races against a 25-second deadline and records `deadline_exceeded`; the test injects a slow task and asserts the marker is logged rather than the work being silently cut at 30 s.
- `severe_idempotency_replay`: same key twice returns the identical body and creates one garment; same key with a different body returns 409.
- `severe_auth_apple_claims`: identity tokens with wrong `aud`, wrong `iss`, expired `exp`, and mismatched nonce are each rejected with 401 and distinct codes.

Local versus remote parity probe. Do not assume miniflare enforces D1's limits; find out once per project and record the answer under verified facts:

```bash
P=$(printf '?,%.0s' $(seq 101) | sed 's/,$//')   # 101 placeholders
npx wrangler d1 execute wardrobe --env staging --local  --command "SELECT $P"   # expect: ?
npx wrangler d1 execute wardrobe --env staging --remote --command "SELECT $P"   # expect: error (100 max)
```

If local accepts what remote rejects, the guard module is load-bearing and the test that exercises the guard at 101 is the only thing standing between green and live failure; say so in the STATE file.

Contract tests. `test/workers/contract.test.ts` generates the OpenAPI document from the app and deep-compares it to `contracts/openapi.json`; a diff fails with instructions to run the export script and commit. A second test validates every example response in the document against its schema.

Integration against a deployed URL. `vitest.smoke.config.ts` is a plain Node config (`environment: "node"`, `include: ["test/smoke/**"]`) that reads `SMOKE_BASE_URL`, `SMOKE_TOKEN` (a bearer accepted only for a dedicated smoke user whose rows are tagged and purged), and `EXPECTED_VERSION_ID`. The sequence: `/health` 200 and `version.id === EXPECTED_VERSION_ID`; `POST /uploads` → presigned URL → `PUT` a 20 KB JPEG → `POST /garments` → poll `GET /garments/:id` until `ready` (timeout 180 s) → `GET /recommendations?occasion=work` returns ≥ 1 outfit whose ids all exist → `DELETE` smoke data. Run with:

```bash
SMOKE_BASE_URL=https://candidate-wardrobe-api.<subdomain>.workers.dev \
SMOKE_TOKEN=$(cat /private/tmp/drive/smoke_token) \
EXPECTED_VERSION_ID=<id from versions upload> \
npx vitest run -c vitest.smoke.config.ts --reporter=json --outputFile=.drive/proofs/<feature>/smoke.json
```

Load sanity. For a personal app the bar is "no platform errors under modest concurrency": `oha -n 300 -c 10 -H "Authorization: Bearer $SMOKE_TOKEN" $SMOKE_BASE_URL/garments` (or `hey`), then `wrangler tail --status error --format json` for 60 seconds while it runs, then `wrangler d1 insights wardrobe --env staging` to see the top queries by rows read and `EXPLAIN QUERY PLAN` via `d1 execute --remote --command` on any query without an index hit.

Command lines the skill runs, in order: `npm run typecheck`, `npx wrangler types --check`, `npx vitest run` (workerd), `npx wrangler deploy --dry-run --outdir .wrangler/dry --env production` (bundle and config validation), then the deploy ladder in 4.5 with the smoke suite between upload and traffic.

### 4.5 Environments, deployment, rollback, Live Proof

`wrangler.jsonc` skeleton (top level is the developer's own dev target; `staging` and `production` redeclare every binding):

```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "wardrobe-api",
  "main": "src/index.ts",
  "compatibility_date": "2026-09-01",
  "workers_dev": true,
  "preview_urls": true,
  "placement": { "mode": "smart" },
  "observability": { "enabled": true, "head_sampling_rate": 1 },
  "version_metadata": { "binding": "VERSION" },
  "limits": { "cpu_ms": 30000 },
  "secrets": { "required": ["SESSION_SIGNING_KEY", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "SMOKE_TOKEN"] },
  "vars": { "ENVIRONMENT": "dev", "APPLE_BUNDLE_ID": "dev.chabot.wardrobe", "AI_GATEWAY_ID": "wardrobe" },
  "d1_databases": [{ "binding": "DB", "database_name": "wardrobe-dev", "database_id": "<uuid>", "migrations_dir": "migrations" }],
  "r2_buckets": [{ "binding": "PHOTOS", "bucket_name": "wardrobe-photos-dev" }],
  "kv_namespaces": [{ "binding": "CONFIG", "id": "<id>" }],
  "vectorize": [{ "binding": "GARMENT_INDEX", "index_name": "wardrobe-garments-dev", "remote": true }],
  "ai": { "binding": "AI", "remote": true },
  "images": { "binding": "IMAGES" },
  "ratelimits": [
    { "name": "RL_USER", "namespace_id": "1001", "simple": { "limit": 120, "period": 60 } },
    { "name": "RL_ANON", "namespace_id": "1002", "simple": { "limit": 20, "period": 60 } }
  ],
  "workflows": [{ "binding": "GARMENT_INGEST", "name": "garment-ingest-dev", "class_name": "GarmentIngest" }],
  "analytics_engine_datasets": [{ "binding": "METRICS", "dataset": "wardrobe_metrics_dev" }],
  "triggers": { "crons": ["17 3 * * *"] },
  "env": {
    "test": { "vars": { "ENVIRONMENT": "test", "APPLE_BUNDLE_ID": "dev.chabot.wardrobe", "AI_GATEWAY_ID": "wardrobe" },
              "d1_databases": [{ "binding": "DB", "database_name": "wardrobe-test", "database_id": "test", "migrations_dir": "migrations" }],
              "r2_buckets": [{ "binding": "PHOTOS", "bucket_name": "wardrobe-photos-test" }],
              "kv_namespaces": [{ "binding": "CONFIG", "id": "test" }],
              "workflows": [{ "binding": "GARMENT_INGEST", "name": "garment-ingest-test", "class_name": "GarmentIngest" }] },
    "staging": { "vars": { "ENVIRONMENT": "staging", "APPLE_BUNDLE_ID": "dev.chabot.wardrobe", "AI_GATEWAY_ID": "wardrobe" },
                 "d1_databases": [{ "binding": "DB", "database_name": "wardrobe-staging", "database_id": "<uuid>", "migrations_dir": "migrations" }],
                 "r2_buckets": [{ "binding": "PHOTOS", "bucket_name": "wardrobe-photos-staging" }],
                 "kv_namespaces": [{ "binding": "CONFIG", "id": "<id>" }],
                 "vectorize": [{ "binding": "GARMENT_INDEX", "index_name": "wardrobe-garments-staging" }],
                 "ai": { "binding": "AI" }, "images": { "binding": "IMAGES" },
                 "ratelimits": [ /* same two */ ],
                 "workflows": [{ "binding": "GARMENT_INGEST", "name": "garment-ingest-staging", "class_name": "GarmentIngest" }],
                 "analytics_engine_datasets": [{ "binding": "METRICS", "dataset": "wardrobe_metrics_staging" }] },
    "production": { "workers_dev": false, "preview_urls": true,
                    "routes": [{ "pattern": "api.wardrobe.chabot.dev", "custom_domain": true }],
                    "vars": { "ENVIRONMENT": "production", "APPLE_BUNDLE_ID": "dev.chabot.wardrobe", "AI_GATEWAY_ID": "wardrobe" },
                    /* every binding redeclared with production ids */ }
  }
}
```

Two details matter. `preview_urls` defaults to `workers_dev`, so production must set `preview_urls: true` explicitly while `workers_dev: false`, or the candidate alias URL will not exist. And `remote: true` on Vectorize and AI in the dev block means `wrangler dev` hits the real dev index and Workers AI; the `test` env omits them so workerd tests mock those bindings.

Secrets. Never in `vars`, never in the repo. `.dev.vars` (gitignored) for local; `.dev.vars.staging` if needed, remembering that its presence suppresses `.dev.vars`. Set live secrets from stdin without quotes (owner lesson: quoted values from an archived `.env` produced 401s):

```bash
printf '%s' "$VALUE" | npx wrangler secret put SESSION_SIGNING_KEY --env production
npx wrangler secret list --env production
```

`secrets.required` makes `wrangler deploy` and `versions upload` fail with a clear error if any listed secret is missing, which turns "forgot a secret" from a runtime 500 into a build failure.

Migrations. Forward-only, expand/contract. A release that needs a column adds it (expand) and ships code that tolerates both shapes; the next release removes the old column (contract) only after the previous version is out of the rollback window the owner cares about. This is not ceremony: rollback moves code and never schema, so a contract migration in the same release as its code change makes `wrangler rollback` a trap.

The deploy ladder (the skill runs all of it; nothing waits on the owner):

```bash
# 0. sanity
npx wrangler deployments status --env production           # confirm the target Worker name is the one STATUS expects
npx wrangler deploy --dry-run --outdir .wrangler/dry --env production
# 1. schema first (expand only)
npx wrangler d1 migrations list  wardrobe --env production --remote
npx wrangler d1 migrations apply wardrobe --env production --remote
# 2. upload without deploying; alias for a stable smoke URL
SHA=$(git rev-parse --short HEAD)
npx wrangler versions upload --env production --message "$SHA" --tag "$SHA" --preview-alias candidate
# capture the printed Version ID as NEW; OLD from `wrangler versions list --env production`
# 3. smoke the candidate with real bindings (writes go to production D1/R2 under the smoke user)
SMOKE_BASE_URL=https://candidate-wardrobe-api.<subdomain>.workers.dev EXPECTED_VERSION_ID=$NEW ... npx vitest run -c vitest.smoke.config.ts
# 4. 10% canary, watch errors for a bounded window, then 100%
npx wrangler versions deploy "$NEW@10%" "$OLD@90%" --env production --yes
timeout 120 npx wrangler tail --env production --format json --status error --version-id "$NEW" | tee .drive/proofs/<feature>/tail-canary.jsonl
npx wrangler versions deploy "$NEW@100%" --env production --yes
# 5. prove the live domain serves it
curl -fsS https://api.wardrobe.chabot.dev/health | jq -e --arg v "$NEW" '.version.id == $v'
npx wrangler deployments status --env production
```

Rollback is one command: `npx wrangler rollback "$OLD" --env production --message "rollback: <reason>"`. Because bindings and schema stay, the ladder's expand-only rule is what makes this safe.

Live Proof, precisely. A feature reaches Live Proof only when a proof packet exists with: the version id served by the production domain (from `/health`), the smoke JSON report with every step green against that version, the migration list showing the expected head applied remotely, the bounded tail capture with zero error outcomes for the new version, and the timestamp and command lines. Preview-URL evidence alone is Local Proof plus, never Live Proof, because preview URLs have no logs and are not the production route. "Deployed" without the smoke is Scaffold with a URL.

Proof packet schema:

```json
{
  "feature": "garment-ingest",
  "claim": "A photo PUT to a presigned URL becomes a ready garment with attributes and a Vectorize entry within 180 s",
  "rung": "Live Proof",
  "worker": "wardrobe-api", "env": "production",
  "version_id": "…", "git_sha": "…",
  "migrations_head": "0007_add_thumb_key.sql",
  "smoke": { "report": "smoke.json", "passed": 9, "failed": 0, "base_url": "https://api.wardrobe.chabot.dev" },
  "tail": { "file": "tail-canary.jsonl", "window_s": 120, "errors": 0 },
  "refutation_tests": ["severe_in_list_over_100", "severe_workflow_returns_state"],
  "checked_at": "2026-09-14T10:22:31Z"
}
```

Workers Builds. Do not connect the repo to Workers Builds for this owner; its default is to deploy `main` on push, which would race the ladder and skip the smoke. If it is connected, set the production deploy command to `npx wrangler versions upload` so pushes create versions and the skill still promotes.

### 4.6 Migration and consolidation playbook (an AI gateway moving into a core Worker)

1. Inventory consumers. Grep every repository for the legacy hostname, env var names, and SDK base URLs; export AI Gateway logs for 7 days and group by `metadata` and user agent; list each consumer with owner, call shape, and whether it can tolerate a base URL change. Write the inventory into the spec; it is the cutover checklist.
2. Freeze the contract. Generate an OpenAPI document from the legacy surface (or write one from observed traffic); commit it as `contracts/ai-gateway.legacy.json`. The new implementation must satisfy it byte-for-byte on the fields consumers read.
3. Build behind a service binding. Implement the module inside the core Worker or as a sibling Worker exposed via `WorkerEntrypoint` RPC and bound with `services: [{ binding: "AI_GATEWAY", service: "core-ai-gateway", entrypoint: "GatewayEntrypoint" }]`. Remember service-binding calls count as subrequests and a chain may cross at most 32 Workers. During gradual rollout pin bound Workers with the `Cloudflare-Workers-Version-Overrides` header to avoid version skew.
4. Shadow traffic. In the core Worker, for the legacy routes, call the new path and, via a service binding to the legacy Worker, the old path; return the old result; compare normalised responses (drop timestamps, ids, latency fields) and log `{ parity: boolean, route, diff_keys }` as a JSON line and as an Analytics Engine data point. Keep shadowing at 100% for at least the traffic volume that covers every consumer in the inventory.
5. Parity gate. Zero mismatches on fields consumers read; overall mismatch rate under 0.5% on ignorable fields; p95 latency within 20% of legacy. The gate is evaluated from the logged data, not from a claim.
6. Cutover. Flip the source of truth per consumer (a `vars` flag or a KV flag read with a 60-second `cacheTtl`), starting with the smallest consumer; gradual deployment 10% → 100% for the core Worker itself; keep the shadow logging on but inverted (new is primary, old is comparison) for one more window.
7. Rollback. Flag flip first (seconds), `wrangler rollback` second (also seconds), and never a schema step in the same release.
8. Retire. Remove consumer references, delete the legacy Worker after the agreed window, rotate the Authenticated Gateway token (account-wide, so anything that had it must be updated), and confirm BYOK keys are attached to the surviving gateway with the `default` alias if the binding path is used.

### 4.7 Operational gates before Done

- `/health` returns version id, tag, timestamp and dependency checks, and the production domain serves the version the ladder deployed.
- Workers Logs enabled and a dashboard query (or `wrangler tail`) shown to return the structured request log for a real request id from the smoke run.
- Error budget stated numerically (default: under 0.5% non-2xx/4xx over 24 h) and checked once from Workers Logs after the canary; if the budget is exceeded the rung stays Live Proof, not Operational.
- Alerting: a Budget Alert set on the account; an external prober on `/health` if the zone plan allows Health Checks (Pro or above) or a free third-party monitor otherwise; a Tail Worker or Workers Logs query for `outcome = exception` reviewed in the proof packet. Say plainly in STATUS that Cloudflare has no native Workers error-rate alert.
- Cost check: projected monthly D1 rows read/written, Workers requests, CPU-ms, Workers AI neurons, Vectorize dimensions, R2 GB, computed from the smoke and load runs with pricing URLs cited.
- Secrets: every required secret present (`wrangler secret list --env production`), R2 API token scoped to the one bucket, Authenticated Gateway on and its token rotated at cutover, `.dev.vars*` gitignored and absent from history.
- Retention: Workers Logs 7 days (state it), R2 lifecycle rules listed via `wrangler r2 bucket lifecycle list`, D1 Time Travel 30 days noted as the backup story with an `export` job only if a longer horizon is required, Analytics Engine 3 months.
- Rollback rehearsed once on staging (`versions deploy` old at 100%, then new again) and recorded.

### 4.8 Common agent failure modes on Cloudflare and the fix the skill applies

| Failure | What the skill does |
|---|---|
| Omits or copies an old `compatibility_date` | Requires a date within 90 days at project start; `wrangler types --check` runs in CI; a note that ≥ 2026-08-04 gives Node compat without flags |
| Imports a Node module that unenv stubs, works in tests, throws live | The workerd test suite imports the real entrypoint; `wrangler deploy --dry-run` runs before every upload; `wrangler check startup` when bundle size or cold start is suspected |
| Assumes unlimited CPU | `limits.cpu_ms` set explicitly; long work goes to Workflows; the scheduled handler uses the 25-second `waitUntil` budget helper |
| Treats `waitUntil` as a job queue | Anything over 25 seconds or needing retries becomes a Workflow or Queue message |
| Uses `BEGIN TRANSACTION` in D1 | Lint forbids `BEGIN`; `batch()` is the only transaction |
| Builds IN lists from arrays | `chunk()` and the guard module; the 250-garment refutation test |
| Mutates closures inside Workflow steps | Lint script plus `severe_workflow_returns_state`; every step returns; top-level state is composed only from step returns |
| Reuses a Workflow instance id | Ids derived from idempotency key, `create()` duplicate error handled as "already running" |
| Local success declared as done | Status ladder enforced by the verifier; Live Proof requires the proof packet |
| Deploys to the wrong Worker name (owner's 2026-08-20 incident) | `deployments status` printed and compared to STATUS before any upload; `name` per env is explicit |
| Waits for the cron | `/cdn-cgi/local/scheduled` locally; direct trigger of the route or `wrangler workflows trigger` live |
| Puts Durable Objects in the API Worker | Architecture rule: DOs live in a separate Worker or not at all, because they remove preview URLs, block `versions upload`, and pin rollbacks |
| Expects KV read-after-write | KV limited to config and JWKS; the refutation test writes then reads through D1 |
| Treats the rate limiter as a quota | Quotas in D1 counters; the limiter only damps |
| Mocks Workers AI and Vectorize too kindly | One remote-binding parity test against the staging index asserts the embedding dimension matches the index and that the vision model returns parseable JSON for a sample image |
| Installs `@cloudflare/vitest-pool-workers` from Hono docs | Reference file names the current package and the codemod |
| Quotes secret values when piping to `wrangler secret put` | `printf '%s'` idiom in the reference |
| Rolls back across a schema change | Expand/contract rule; contract migrations ship one release later |

## 5. Conditionals by project shape

Greenfield fashion app (Cloudflare backend, Swift client). Everything above applies. The architect emits the storage decision table, schema, upload flow, Workflow, and the contract-first route plan before implementation. The implementer is split: one Sonnet worker per bounded area (auth, garments and uploads, ingest Workflow, recommendations, ops endpoints) with the guard module written first by Opus and frozen. The verifier runs the parity probe, refutation tests, and the ladder. The Swift client is regenerated from the committed contract in the same step that changes it.

Deep bug hunt in an existing Cloudflare codebase. Read `wrangler.*` first and record name, env layout, compat date, flags, bindings, and `limits`. Ask the kinder-shim question of every test double in the repo. Reproduce in workerd with the real migrations before touching code; if the bug only appears live, pull the request id from Workers Logs (`wrangler tail --status error` while reproducing) and check `meta.rows_read`, `served_by_primary`, and the version id in the log line against the deployed version. Suspect the platform limits first: bind count, statement bytes, LIKE length, subrequests, CPU, the 30-second `waitUntil` window, Workflow replay. The fix ships with a refutation test that fails on the old code and a live proof of the specific failing request now succeeding. Second occurrence of the same workaround means the diagnosis was wrong; stop and re-diagnose.

Feature on an existing product. Add bindings to every environment block, not just the top level; expand-only migration; contract test updated in the same change; the ladder as usual. If the feature adds a Workflow, its instance-id scheme and the "return everything" rule are reviewed before code.

Migration or consolidation. Section 4.6 verbatim. Add a consumer inventory file to the spec and make the parity gate the acceptance test. Skip vision verification; the artefacts are logs and diffs.

Research plus website. Use Workers with static assets (`assets.directory`, `not_found_handling: "404-page"` or SPA), no D1 unless the site has dynamic state, no Workflows, `observability.enabled` on, custom domain, and the deploy ladder collapses to `deploy --dry-run`, `versions upload`, Lighthouse and visual verification against the preview alias, then `versions deploy`. Pages is acceptable if the team already uses it, but the pack recommends Workers because it is where Cloudflare's own migration guide points and where previews, logs, and gradual deploys live.

Other shapes. Pure research report and CLI or library: the pack is inactive. Data pipeline: Workflows for orchestration, Queues for fan-in, R2 for artefacts, D1 or R2 for state; the return-from-steps rule and the 1 MiB step-return limit (stream or store in R2 and return a key) matter most. Ops or incident: the runbook is `deployments status`, `tail --status error`, Workers Logs query by request id, `rollback`, D1 `time-travel info` before any restore, and the proof that the incident is closed is a smoke run against production.

## 6. Model and effort assignment

- Cloudflare architecture (storage decision table, schema, upload and Workflow design, deploy topology): Opus, high effort, in the main session or a Plan-type subagent, with the reference file loaded. Fable reviews the decision only when the shape is greenfield or migration, because those are where a wrong storage choice is expensive to unwind.
- Guard module, error envelope, health endpoint, deploy scripts: Opus, medium effort, written once before the fan-out because everything else depends on them.
- Route handlers, migrations, tests per bounded area: Sonnet, medium effort, one worker per area, `isolation: worktree` only if two workers touch the same files, merged and deleted in the same step.
- Limit linting of diffs (IN-list spreads, string-built SQL, closure assignment in steps, `BEGIN`, direct `prepare` outside `src/db`): a script first, then Sonnet at low effort to classify the ambiguous hits into `violation | false_positive | needs_human`, never Haiku.
- Independent verification and the deploy ladder: a predefined subagent, Opus at high effort, read-only on source. Draft:

```markdown
---
name: cloudflare-verifier
description: Independent verifier for Cloudflare Workers backends. Re-derives platform limits from developers.cloudflare.com, runs refutation tests in workerd, probes the remote D1 for places the local simulator is kinder, executes the smoke suite against a preview alias and then the production domain, and writes the proof packet. Never edits source.
model: opus
effort: high
tools: Bash, Read, Grep, Glob, WebFetch
disallowedTools: Edit, Write, NotebookEdit
memory: project
---
You verify; you do not fix. You have not seen the implementer's reasoning and you must not ask for it.

Start by reading wrangler.* and the STATUS file, then state in one paragraph which Worker name, environment, and version you expect to be verifying. Refuse to continue if the deployed name does not match.

For every platform limit the code relies on, cite the docs URL and run the test that tries to break it. If the repository has a test double for D1, R2, KV, Workers AI, or Vectorize, write down where it is kinder than the real service and run one call against the remote resource to check. Treat "24 green runs" as no evidence about production.

Run the smoke suite against the preview alias with EXPECTED_VERSION_ID set; then, after traffic is shifted, against the production domain. Capture wrangler tail for the new version for a bounded window. Write .drive/proofs/<feature>/proof-packet.json via a shell redirect with the fields the reference file lists, and assign the rung honestly: preview-only evidence is not Live Proof.

Report in plain sentences: what you tried to refute, what refused to break, what broke, and the rung. One decision for the orchestrator at most.
```

- Deployment execution (the ladder): the same verifier runs it, because the person shifting traffic should be the one who just proved the candidate. If the environment forbids the verifier from deploying, the orchestrator runs the ladder and the verifier re-checks `/health` and the tail afterwards.

## 7. Failure modes and anti-patterns (how mirage completion happens here)

The harness is kinder than production. This is the headline failure and the reason the pack exists. It appears as a Node shim for D1, as a mocked Workers AI that always returns valid JSON, as a Vectorize mock with no dimension check, as fake timers that "expire" KV keys the real service would still serve, and as a local `wrangler dev` that never enforced the 100-bind cap. The skill prevents it by putting the limits into the code, by making the workerd harness the default, by the remote probe, and by refusing Live Proof without the smoke against real bindings.

The URL exists, therefore it works. `wrangler deploy` prints a URL; a `curl /` returns 200; the agent reports done. The health endpoint with a version id, the smoke suite that exercises a real write path, and the tail capture are what turn a URL into evidence. The pack also forbids counting preview-URL behaviour as production behaviour, since previews have no logs and are not on the custom domain.

Deployed to the wrong thing. The owner's frozen v1 Worker was nearly overwritten by a deploy with a stale name. `deployments status` before upload and an explicit `name` inside every env block make this a checked precondition rather than a hope.

Waiting on a schedule. "The cron will pick it up at 03:17" is the approval-queue anti-pattern in a different coat. The scheduled handler is invoked locally through `/cdn-cgi/local/scheduled`, the Workflow through `wrangler workflows trigger`, the backup through its `/internal` route; the report contains the resulting instance id or output, or the work is not done.

Replay undid my fix. A Workflow step that mutated an outer variable ran correctly once, then the engine hibernated, replayed, and returned the memoised value. The lint, the refutation test, and the rule "top-level state is only step returns" exist because this bit the owner twice.

Rollback that cannot roll back. A contract migration shipped with the code that needed it; rollback restored the old code against the new schema and produced 500s. Expand/contract plus a rehearsal on staging is the fix.

Mocked model output certifies the pipeline. A vision model that returns fenced JSON, or a different key order, or an empty array, is normal; a mock that never does is a lie. The pack demands one real call per model in the parity test and a Zod parse with fence stripping in the step.

Cost surprises. `cacheTtl: 0` everywhere, a recommendation call on every app open, `head_sampling_rate: 1` on a busy Worker, or a list query without an index reading a million rows. The cost gate with real `rows_read` numbers catches the D1 case; the gateway cache and the per-day recommendation key catch the model case.

## 8. Open questions and trade-offs

`@hono/zod-openapi` or chanfana. Both are current and Zod-based; chanfana is Cloudflare-maintained and class-based, zod-openapi is Hono-native and function-based. Recommendation: zod-openapi for a fresh Hono app because the contract sits next to the handler; chanfana if the repo already uses itty-router or prefers classes. Never both.

Does local D1 enforce the 100-bind cap. Unknown from the docs; the probe in 4.4 answers it in ten seconds per project and the answer goes under verified facts. The guard module is required either way.

Subrequest limit. Two docs pages disagree (1,000 versus 10,000 on Paid). Recommendation: design under 1,000, set `limits.subrequests` explicitly if the Worker legitimately needs more, and cite the limits page.

Durable Objects for per-user state. Tempting for a single-user app (zero-latency SQLite next to compute) but it removes preview URLs, gradual rollout, and easy rollback for the whole Worker. Recommendation: D1 now; a separate DO Worker later if a real-time feature demands it.

Passkeys. No Workers-supporting WebAuthn server library is documented. Recommendation: Sign in with Apple only for v1; passkeys as a spike with a refutation test against a real authenticator response.

Read replication. Not worth enabling for one user; if enabled, the Sessions API is mandatory. Recommendation: leave off and note the bookmark-header design so the Swift client can adopt it later.

Smoke writes into production D1. The candidate preview shares production bindings, so the smoke user's rows land in the real database. Recommendation: accept it (that is what Live Proof means), tag the rows, purge them at the end of the run, and exclude the smoke user from analytics.

Workers Builds. Convenient, but its default auto-deploy on `main` bypasses the smoke-before-traffic ladder. Recommendation: not connected; if connected, `versions upload` only.

Model for vision attributes. Workers AI's llama-3.2-11b-vision is cheap and in-platform but weaker than frontier multimodal models reachable through AI Gateway BYOK. Recommendation: start on Workers AI for cost and latency, log gateway feedback with `patchLog`, and route to a stronger model only for garments the first pass flags as low confidence.

## 9. Skill text candidates

Each passage is ready to lift into `references/cloudflare.md` (or SKILL.md where marked). Imperative voice, plain language.

**9.1 Activation (SKILL.md).** If the repository contains `wrangler.jsonc`, `wrangler.json`, or `wrangler.toml`, or the goal names Cloudflare, Workers, D1, R2, KV, Durable Objects, Queues, Workflows, Vectorize, Workers AI, or AI Gateway, read `references/cloudflare.md` before designing, implementing, or verifying, and add its gates to the Done criteria.

**9.2 The one rule.** Cloudflare enforces limits that local tooling does not. Put every limit you depend on into the code under test, write one test that tries to break it, and run one real call against the deployed resource to learn where your simulator is kinder. Twenty-four green runs against a shim are not evidence about production.

**9.3 Limits table (verified 2026-09-14).**

| Service | Limit | Value |
|---|---|---|
| Workers | CPU per invocation | 30 s default, `limits.cpu_ms` up to 300,000 (Paid) |
| Workers | `waitUntil` after response | 30 s wall time, shared, then cancelled |
| Workers | Cron / Queue / alarm wall time | 15 min |
| Workers | Subrequests | 50 Free; 10,000 Paid default (`limits.subrequests`); design under 1,000 |
| Workers | Simultaneous connections awaiting headers | 6 |
| Workers | Service-binding chain | 32 invocations |
| D1 | Bound parameters per statement | 100 |
| D1 | Statement length | 100 KB (each statement in a batch) |
| D1 | LIKE/GLOB pattern | 50 bytes; no GLOB character classes |
| D1 | Row / string / blob | 2 MB |
| D1 | Query duration; whole batch | 30 s |
| D1 | Queries per invocation | 1,000 (Paid) |
| D1 | Database size | 10 GB (Paid) |
| D1 | Transactions | `batch()` only; auto-commit otherwise |
| Workflows | Step return | 1 MiB (stream or store in R2 above that) |
| Workflows | Steps per instance | 10,000 default (Paid) |
| Workflows | Step CPU | 30 s default, up to 5 min |
| Workflows | Persisted state | 1 GB per instance |
| KV | Consistency | eventual, up to 60 s or more; 1 write/s per key; 25 MiB values |
| R2 | Single PUT | 5 GiB; presigned URL expiry ≤ 7 days; 1 write/s per key |
| R2 | Lifecycle rules | 1,000 per bucket; act within ~24 h |
| Queues | Message / batch | 128 KB / 100 messages; 14-day retention |
| Vectorize | Dimensions / vectors / topK | 1,536 / 20M per index / 50 with metadata |
| Analytics Engine | Per data point | 20 blobs, 20 doubles, 1 index; 250 points per invocation |
| Workers Logs | Retention / event size | 7 days Paid / 256 KB; 5B events per account per day then 1% sample |
| Rate limit binding | Period | 10 or 60 s; per-location, permissive; not a quota |

Sources: developers.cloudflare.com pages for `workers/platform/limits`, `d1/platform/limits`, `workflows/reference/limits`, `kv/platform/limits`, `r2/platform/limits`, `queues/platform/limits`, `vectorize/platform/limits`, `analytics/analytics-engine/limits`, `workers/observability/logs/workers-logs`, `workers/runtime-apis/bindings/rate-limit`.

**9.4 D1 access discipline.** Create `src/db/guard.ts` exporting the limits as constants and a `guardStatement(sql, params)` that throws a named `PlatformLimitError` above 100 parameters or 100 KB. Route every query through `src/db/`; add a test that greps `src/` for `.prepare(` outside that folder and fails on any hit. Chunk IN lists at 90. Never select a large JSON or blob column in a query that returns many rows. Use `batch()` for any request that writes two tables. Write forward-only migrations in expand/contract pairs; never ship a column drop or rename in the same release as the code that stops using it.

**9.5 Workflow discipline.** Every value a step computes is returned from `step.do` and read from the return; nothing inside a step assigns to a variable declared outside it. Step names are literal strings or built only from earlier step returns. Wrap `Date.now()`, `Math.random()`, and `Promise.race` in steps. Derive instance ids from the request's idempotency key and treat a duplicate-id error as "already running". Keep step returns under 1 MiB; above that write to R2 and return the key. Throw `NonRetryableError` for input that can never succeed. Never trigger a live Workflow by waiting for a cron; use `wrangler workflows trigger <name> '<json>'` and read `instances describe <name> latest --step-output`.

**9.6 Testing setup.** Install `vitest@^4.1.0` and `@cloudflare/vitest-plugin` (the package was renamed from `@cloudflare/vitest-pool-workers` on 2026-08-19; Hono's docs are stale). Configure with `defineConfig({ plugins: [cloudflareTest({ wrangler: { configPath: "./wrangler.jsonc", environment: "test" }, miniflare: { bindings: { TEST_MIGRATIONS: await readD1Migrations("migrations") } } })] })` and apply migrations in a setup file with `applyD1Migrations(env.DB, env.TEST_MIGRATIONS)`. Import `env` and `exports` from `cloudflare:workers`; import `createExecutionContext`, `waitOnExecutionContext`, `introspectWorkflowInstance` from `cloudflare:test`. Storage is isolated per test file; pass `--max-workers=1 --no-isolate` only when tests must share state. Workers AI and Vectorize have no local simulation: mock them in unit tests and keep one parity test with `remote: true` against staging resources that asserts the embedding dimension and a parseable model response.

**9.7 The kinder-shim probe.** Before trusting any local D1 result, run the same 101-placeholder `SELECT` with `wrangler d1 execute <db> --local` and `--remote`. Record which limits local does not enforce under verified facts, and name the guard that covers each one.

**9.8 Config skeleton essentials.** Set `compatibility_date` to a recent date (≥ 2026-08-04 enables Node compatibility without flags). Set `observability.enabled: true`, bind `version_metadata`, set `limits.cpu_ms` explicitly, list `secrets.required`, enable `preview_urls: true` in production even with `workers_dev: false`, and redeclare every binding and `vars` inside each `env.<name>` block because they do not inherit. Keep Durable Objects out of the API Worker: they remove preview URLs, block `versions upload`, and pin rollbacks.

**9.9 Secrets.** Never in `vars`, never in the repository. Local values go in `.dev.vars` (gitignored); if `.dev.vars.<env>` exists it replaces `.dev.vars`. Set live values from stdin without quotes: `printf '%s' "$VALUE" | npx wrangler secret put NAME --env production`. Confirm with `wrangler secret list --env production`. Rotate the AI Gateway token at every cutover; its `Run` permission spans every gateway and BYOK key in the account.

**9.10 Deploy ladder.** `wrangler deployments status --env production` and compare the Worker name to STATUS; `wrangler deploy --dry-run --outdir .wrangler/dry --env production`; `wrangler d1 migrations apply <db> --env production --remote` (expand only); `wrangler versions upload --env production --message "$SHA" --tag "$SHA" --preview-alias candidate`; run the smoke suite against `https://candidate-<worker>.<subdomain>.workers.dev` with `EXPECTED_VERSION_ID`; `wrangler versions deploy "$NEW@10%" "$OLD@90%" --env production --yes`; `timeout 120 wrangler tail --env production --format json --status error --version-id "$NEW"`; `wrangler versions deploy "$NEW@100%" --env production --yes`; `curl /health` on the custom domain and check `version.id`. Rollback is `wrangler rollback "$OLD" --env production --message "<reason>"`; it moves code, never schema or secrets.

**9.11 Live Proof definition.** Live Proof means a proof packet with: the version id served by the production domain, a green smoke report that performed a real authenticated write, upload, Workflow run, and read against that version, the remote migration head, and a bounded tail capture with zero error outcomes for that version. Preview-URL results are Local Proof (previews have no logs and are not the production route). A deploy without the smoke is Scaffold with a URL.

**9.12 Smoke suite contents.** `/health` 200 with the expected version id; `POST /uploads` → presigned PUT of a small image → `POST /garments` with an idempotency key → poll `GET /garments/:id` to `ready` within 180 s → `GET /recommendations` returns outfits whose garment ids all exist → replay the same idempotency key and expect the identical body → purge the smoke user's rows. Use a dedicated smoke user authenticated by `SMOKE_TOKEN`; its rows are tagged and excluded from analytics.

**9.13 Never wait for the cron.** Locally run `wrangler dev --test-scheduled` and `curl "http://localhost:8787/cdn-cgi/local/scheduled?cron=<expr>"`. Live, call the internal route or `wrangler workflows trigger`. A report that says work will happen at the next tick is a report of work not done.

**9.14 Consolidation playbook (AI gateway into core).** Inventory consumers from code and gateway logs; freeze the legacy contract as OpenAPI; implement behind a service binding (`services` with `entrypoint`, RPC via `WorkerEntrypoint`); shadow at 100% and log `{ parity, route, diff_keys }`; gate on zero mismatches in consumer-read fields; cut over per consumer with a flag, then gradual deployment; roll back by flag first, `wrangler rollback` second; retire the legacy Worker after the window and rotate the gateway token. Service-binding calls count as subrequests; a chain crosses at most 32 Workers; pin versions across bound Workers with `Cloudflare-Workers-Version-Overrides` during rollouts.

**9.15 Operational gates before Done.** Health endpoint with version and dependency checks on the production domain; Workers Logs enabled and a real request id retrieved; error budget stated and checked after canary; Budget Alert set and an external `/health` prober configured (Cloudflare has no native Workers error-rate alert); cost projected from real `rows_read` and neuron counts with pricing URLs; secrets complete, scoped, rotated; retention stated (logs 7 days, R2 lifecycle rules listed, D1 Time Travel 30 days); rollback rehearsed on staging once.

**9.16 Anti-patterns to refuse.** `BEGIN TRANSACTION` in D1; IN lists built from unbounded arrays; `LIKE` patterns from raw user input; large JSON columns projected in list queries; closure mutation inside Workflow steps; `waitUntil` for work over 25 seconds or needing retries; KV for anything just written; the rate-limit binding as a quota; Durable Objects in the API Worker without a real-time requirement; `@cloudflare/vitest-pool-workers` in a new project; quoted secret values; a contract migration in the same release as its code; Workers Builds auto-deploying `main` around the ladder.

**9.17 Owner's production lessons (keep).** Outbound email is the `send_email` binding to verified destinations, not a REST endpoint. A D1→R2 backup does not fit one request's CPU; dispatch it under `waitUntil` and record per-table failures. D1 rejects GLOB character classes in CHECKs; long LIKE terms trip "LIKE too complex"; joining a multi-KB blob column onto thousands of rows throws a memory-limit error. Authenticated Gateway returns 401 without `cf-aig-authorization`; DeepSeek ran BYOK on the provider path, not the unified path; `cf-aig-skip-cache: true` when a stale cached response would be wrong. `rm -rf .wrangler` when a stale esbuild output makes local behaviour lie. `keep_vars: true` if the owner sets vars in the dashboard, or every deploy clobbers them.
