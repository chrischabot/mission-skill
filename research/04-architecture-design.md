# Architecture and design phase: backend design, frontend design, interface contracts, and design review

Component report for the `/drive` skill. Date: 2026-09-14. Every claim below is marked as a verified fact (with URL), a claim taken from the source post, or my opinion. Where I say "verify before committing" I mean the skill should spend a research step on it, not that I am unsure it exists.

## 1. Executive opinion

The design phase exists to let several agents build in parallel without colliding, and to give the later verification stages something concrete to verify against. Everything else about it is secondary. That framing settles most questions: a design artifact earns its place only if some later agent reads it and acts differently because of it, and the most valuable design artifacts are therefore the machine-checkable ones (an API contract with fixtures, a token file, a per-screen intent record, a table of behavioral claims), with prose reserved for rationale.

The skill should produce, for anything above a small feature, a contract package that neither the backend agent nor the frontend agent owns, generated types on both sides, fixtures that double as mock-server examples, and a contract test on each side that runs inside a production-faithful harness. That is the seam. Backend and frontend agents then work against the seam rather than against each other, and integration becomes a check rather than a negotiation.

Design review must be done by an agent that never saw the designer's reasoning, using a rubric that demands evidence pointers, and it must include a pre-mortem: assume the system failed in six months, write the incident report, and turn each plausible cause into a mitigation, an accepted risk recorded in a decision record, or a test. The reviewer's verdict file is the design gate; the orchestrator may not approve its own design.

Design should be sized to scope. A bug hunt gets a one-paragraph diagnosis note and no design docs at all. A dashboard feature gets a one-page change design plus a contract delta. A greenfield app or a service migration gets the full set, but time-boxed to "enough for parallel implementation to start", with deferred decisions written down as proposed decision records rather than resolved prematurely.

Finally, design docs rot unless something reconciles them with code. Each doc carries a "reconciled at commit" line, a cheap Sonnet checker diffs the doc against the contract and the code at the end of implementation, and status files link every design claim to the test that tries to refute it. Ground truth stays code and tests; design docs are the plan, never the proof.

## 2. What the post says, and a critique

The source post is about self-improving agent systems in general and says almost nothing about design. Three passages touch this component.

Step 13 describes vision self-verification: "Verifier sub-agent reads the screenshot with vision, compares against the goal description, design tokens in the project Skill, and the previous screenshot from STATE.md." This is the one genuinely useful design idea in the post, and it is right in outline but underspecified. "Design tokens in the project Skill" is the wrong home; tokens belong in the repository next to the code that must obey them, where a test can compare the two. A screenshot compared against a "goal description" is too vague to grade; the verifier needs per-screen statements written as observable facts ("exactly one filled accent button is visible"), otherwise it will grade vibes and pass mediocre work, which is exactly the self-critique failure the post warns about elsewhere. The "previous screenshot" idea is good and should be a baseline directory, not a line in STATE.md.

Step 7 lists the tournament pattern, "pairwise comparison for taste-based ranking; useful for design or naming." The Claude Code workflows documentation independently lists "a hard plan worth drafting from several independent angles before you commit to one" as a use case (verified, see section 3). For greenfield and migration shapes this is worth using for the backend design: two or three designs under different constraints, then a comparison. For anything smaller it is waste.

Step 4 routes "architecture decisions" to Opus 4.8. That is the right tier for producing a design document, but the post treats architecture as a subtask the orchestrator delegates and then trusts. The Anthropic harness post it cites elsewhere makes the opposite point: a generator's self-assessment is unreliable and a skeptical standalone evaluator is far more tractable (verified quote in section 3). The post applies that lesson to code and forgets to apply it to designs. The skill should not.

The post's general thesis, that the environment around the model is what compounds, holds for design too, with one addition it misses: decision records are the design-phase version of the lesson file. A team that writes down why it chose D1 over Postgres, and what it would take to reverse that, does not re-derive the choice next quarter, and an agent that reads the record does not silently undo it while "simplifying".

## 3. Verified facts

Checked 2026-09-14 against live documentation unless noted.

Claude Code harness:

- Subagent frontmatter supports `model` (`sonnet|opus|haiku|fable|inherit|<full id>`), `effort` (`low|medium|high|xhigh|max`), `isolation: worktree`, `memory` (`user|project|local`), `tools`, `disallowedTools`, `maxTurns`, `permissionMode`, `skills` (preloaded in full), `mcpServers`, `hooks`, `background`, `color`. Model resolution: per-invocation parameter, then frontmatter, then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main session model. https://code.claude.com/docs/en/sub-agents
- A non-fork subagent starts with fresh context and receives its own system prompt, the task message, every CLAUDE.md level the main conversation loads including project rules, git status, and preloaded skills. It does not receive parent conversation history, the parent's auto memory, or files the parent already read. The built-in Explore and Plan agents skip CLAUDE.md. https://code.claude.com/docs/en/sub-agents
- Subagent `memory: project` lives at `.claude/agent-memory/<agent-name>/`; the first 200 lines or 25 KB of its `MEMORY.md` load into the prompt. https://code.claude.com/docs/en/sub-agents
- `.claude/rules/*.md` files load every session; files with `paths:` frontmatter (glob patterns) load only when Claude reads matching files. CLAUDE.md supports `@path` imports (max depth four). Auto memory lives at `~/.claude/projects/<project>/memory/` and is not shared across machines. https://code.claude.com/docs/en/memory
- Dynamic workflows: a JavaScript script with `agent()`, `parallel()`, `pipeline()`, `phase()`; `agent()` accepts a `schema` and returns validated JSON; up to 16 concurrent agents, 1,000 per run; `Date.now()` and `Math.random()` throw inside the script; default size guideline "medium" aims for fewer than 15 agents; the docs list "a hard plan worth drafting from several independent angles before you commit to one" as a use case. https://code.claude.com/docs/en/workflows
- Documentation index (the brief's `llms.txt` URL under `/docs/en/` returned 404; the working one is https://code.claude.com/docs/llms.txt). Relevant pages: sub-agents, agents, agent-teams, workflows, memory, skills, hooks, headless, goal, permission-modes, prompt-caching, costs, checkpointing.

Anthropic engineering, "Harness design for long-running application development" (Prithvi Rajasekaran, 2026-03-24): planner expands a short prompt into a full product spec including visual design language and feature list; evaluator drives the running app through Playwright and grades on design quality, originality, craft, functionality with hard thresholds; "tuning a standalone evaluator to be skeptical turns out to be far more tractable than making a generator critical of its own work"; "When asked to evaluate work they've produced, agents tend to respond by confidently praising the work"; reported cost of a full harness run $124.70 over 3.85 hours versus a $9, 20-minute solo run that shipped broken core features. https://www.anthropic.com/engineering/harness-design-long-running-apps

Cloudflare platform (limits and pricing as published on 2026-09-14):

- D1: max database size 10 GB (Paid), 500 MB (Free); max bound parameters per query 100; max SQL statement 100 KB; max columns per table 100; max row or blob 2 MB; queries per Worker invocation 1,000 (Paid); Time Travel 30 days (Paid). https://developers.cloudflare.com/d1/platform/limits/
- D1 pricing: 25 billion rows read and 50 million rows written per month included on Paid, then $0.001 per million reads and $1.00 per million writes; 5 GB storage included then $0.75 per GB-month; rows read counts rows scanned, so missing indexes are a billing problem as well as a latency problem. https://developers.cloudflare.com/d1/platform/pricing/
- D1 `batch()` is the only transaction mechanism ("each statement in the list will execute and commit, sequentially, non-concurrently"; a failing statement aborts and rolls back the sequence); D1 runs in auto-commit; no interactive `BEGIN/COMMIT`. Result `meta` carries `rows_read`, `rows_written`, `duration`, `served_by`. https://developers.cloudflare.com/d1/worker-api/d1-database/
- D1 read replication with the Sessions API (`withSession`, bookmarks, `first-primary` / `first-unconstrained`, sequential consistency) was announced as public beta on 2025-04-10; I found no GA announcement. https://developers.cloudflare.com/d1/best-practices/read-replication/ and https://developers.cloudflare.com/changelog/post/2025-04-10-d1-read-replication-beta/
- D1 migrations: `wrangler d1 migrations create|list|apply`, SQL files in `migrations/`, tracked in a `d1_migrations` table; no rollback command documented. https://developers.cloudflare.com/d1/reference/migrations/
- The 100 bound-parameter limit is enforced inside workerd (`sqlite3_limit(db, SQLITE_LIMIT_VARIABLE_NUMBER, 100)`), which Miniflare v3 and `wrangler dev` run, so local development reproduces it; a Node-side sql.js shim does not. https://github.com/cloudflare/workers-sdk/issues/2811
- Workers testing: `@cloudflare/vitest-pool-workers` was renamed `@cloudflare/vitest-plugin` (v1) on 2026-08-19; it runs Vitest inside workerd with real binding semantics and isolated per-test storage; codemod `npx @cloudflare/codemods vitest:pool-workers-to-vitest-plugin`. https://developers.cloudflare.com/changelog/post/2026-08-19-vitest-plugin/ and https://developers.cloudflare.com/workers/testing/vitest-integration/
- R2: storage $0.015 per GB-month, Class A $4.50 per million, Class B $0.36 per million, egress free; free tier 10 GB, 1 M Class A, 10 M Class B; single-part upload up to ~5 GiB. https://developers.cloudflare.com/r2/pricing/ and https://developers.cloudflare.com/r2/platform/limits/
- R2 presigned URLs: GET, HEAD, PUT, DELETE (not POST), expiry 1 second to 7 days, only on the S3 API domain, Content-Type can be pinned so a mismatched upload fails signature validation. https://developers.cloudflare.com/r2/api/s3/presigned-urls/
- R2 event notifications deliver `object-create` and `object-delete` to Queues; 100 rules per bucket. https://developers.cloudflare.com/r2/buckets/event-notifications/
- Durable Objects: SQLite-backed storage is the recommended default for new classes; requests $0.15 per million after 1 M included; duration $12.50 per million GB-s billed at 128 MB; SQLite rows priced like D1. https://developers.cloudflare.com/durable-objects/platform/pricing/
- Workflows: available on Free and Paid (GA); `step.do` returns must be structured-cloneable and ≤ 1 MiB; retries configurable, `NonRetryableError` stops retries; `step.sleep`, `step.sleepUntil`, `step.waitForEvent` (default timeout 24 hours); rollback handlers per step; 10,000 steps per instance on Paid; 30-day state retention. https://developers.cloudflare.com/workflows/ , https://developers.cloudflare.com/workflows/build/workers-api/ , https://developers.cloudflare.com/workflows/reference/limits/
- Queues: 128 KB messages, batches of 100, 5,000 messages per second per queue, retention up to 14 days, consumer wall clock 15 minutes. https://developers.cloudflare.com/queues/platform/limits/
- Workers limits: CPU 30 s default on Paid configurable to 5 minutes; 128 MB memory; 10,000 subrequests (Paid); request body 100 MB on Free/Pro zones; 6 simultaneous outbound connections. https://developers.cloudflare.com/workers/platform/limits/
- Workers Logs: `[observability] enabled = true`, `head_sampling_rate` 0 to 1; retention 3 days Free, 7 days Paid; 20 M events per month included on Paid then $0.60 per million; structured `console.log` objects are indexed by field. https://developers.cloudflare.com/workers/observability/logs/workers-logs/
- Versions and rollback: `wrangler versions list`, `wrangler deployments list`, gradual percentage deployments, `wrangler rollback` to any of the 100 most recent versions; rollback restores code only, never bindings, D1 schema, or secrets, and is blocked across Durable Object class lifecycle changes. https://developers.cloudflare.com/workers/configuration/versions-and-deployments/ and https://developers.cloudflare.com/workers/configuration/versions-and-deployments/rollbacks/
- Environments: `[env.<name>]` deploys as `<name>-<env>`; bindings, vars, and secrets are non-inheritable and must be repeated per environment. https://developers.cloudflare.com/workers/wrangler/environments/
- Workers Builds: connect GitHub/GitLab, build on push, preview URLs per version; `npx wrangler versions upload` as deploy command uploads without promoting. https://developers.cloudflare.com/workers/ci-cd/builds/
- Rate limiting binding: `simple.limit` with `period` of 10 or 60 seconds only; counters are per Cloudflare location, eventually consistent, and "intentionally designed to not be used as an accurate accounting system." https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/
- Cloudflare Images: 5,000 unique transformations per month free then $0.50 per 1,000; transformations work on R2-hosted images; `segment=foreground` removes backgrounds using BiRefNet on Workers AI (open beta per Cloudflare's announcement), combinable with `background=`, `trim`, `fit`; `gravity=face` exists. https://developers.cloudflare.com/images/pricing/ and https://developers.cloudflare.com/images/transform-images/transform-via-url/ and https://blog.cloudflare.com/background-removal/
- Workers AI: $0.011 per 1,000 neurons after 10,000 free per day; vision-capable text models include `@cf/meta/llama-4-scout-17b-16e-instruct` and `@cf/meta/llama-3.2-11b-vision-instruct` ($0.049 in / $0.676 out per M tokens). https://developers.cloudflare.com/workers-ai/platform/pricing/ and https://developers.cloudflare.com/workers-ai/models/
- AI Gateway: Anthropic is a supported provider; BYOK stores provider keys in Secrets Store and requests carry only `cf-aig-authorization`; caching, rate limiting, cost analytics. https://developers.cloudflare.com/ai-gateway/ and https://developers.cloudflare.com/ai-gateway/configuration/bring-your-own-keys/

Claude API (from the bundled `claude-api` reference, cached 2026-06-24, and the live vision page):

- Pricing per million tokens: Fable 5.1 $10 / $50; Opus 5 $5 / $25; Sonnet 5 $2 / $10; Haiku 4.5 $1 / $5. Structured outputs via `output_config.format`; refusal fallbacks exist for Fable-tier models.
- Vision cost is `⌈width/28⌉ × ⌈height/28⌉` tokens; a 1000×1000 image is 1,296 tokens; models from 4.7 onward accept up to 2576 px long edge (4,784 tokens), so pre-resize to control cost; max 10 MB per image; JPEG, PNG, GIF, WebP. https://platform.claude.com/docs/en/build-with-claude/vision

Apple and Swift:

- iOS 27 ships 2026-09-14; Xcode 27 with Swift 6.4 is required to target it. https://9to5mac.com/2026/09/09/apple-confirms-ios-27-release-date-september-14/
- Observation framework (`@Observable`, granular SwiftUI tracking) is iOS 17+; the `Observations` async sequence (Swift 6.2, SE-0475) requires OS 26 and is not back-ported. https://developer.apple.com/documentation/observation and https://useyourloaf.com/blog/swift-observations-asyncsequence-for-state-changes/
- Swift Testing (`@Test`, `#expect`, `#require`, parameterized tests, tags, parallel by default) shipped with Xcode 16 and coexists with XCTest. https://developer.apple.com/xcode/swift-testing/
- Swift OpenAPI Generator: latest release 1.13.1 published 2026-09-01; supports OpenAPI 3.0, 3.1, and preliminary 3.2; generates types, client, and server; URLSession client transport. https://github.com/apple/swift-openapi-generator and https://api.github.com/repos/apple/swift-openapi-generator/releases/latest
- `VNGenerateForegroundInstanceMaskRequest` (iOS 17+) produces foreground instance masks on device and `generateMaskedImage` returns the cut-out; a Swift-native `GenerateForegroundInstanceMaskRequest` exists from iOS 18. https://developer.apple.com/documentation/vision/vngenerateforegroundinstancemaskrequest
- `PhotosPicker` (iOS 16+) needs no photo-library permission and loads items via `loadTransferable`. https://developer.apple.com/documentation/photosui/photospicker
- App Attest (`DCAppAttestService`): generate key, attest with a server challenge, per-request assertions; not available in the Simulator; Apple rate-limits attestation. https://developer.apple.com/documentation/devicecheck/establishing-your-app-s-integrity
- Foundation Models framework (on-device LLM, iOS 26) is text-only in iOS 26; image input arrives with iOS 27 per beta coverage. Verify against the final iOS 27 docs before relying on it. https://www.appcoda.com/foundation-models/ (secondary source; the Apple doc fetch returned an unreliable summary and I am not repeating it)
- GRDB versus SwiftData in 2026 community guidance: SwiftData for simple apps that stay simple; GRDB where migrations, full-text search, or large record counts matter. https://www.pistack.xyz/posts/2026-08-11-grdb-swiftdata-core-data-swift-persistence-comparison/ (secondary source; opinion-grade)
- swift-snapshot-testing 1.12+: `.image` and `.recursiveDescription` strategies per device, works with Swift Testing via `@Suite(.snapshots(record: .failed))`. https://github.com/pointfreeco/swift-snapshot-testing
- PactSwift implements Pact specification v3 with an in-process mock service. https://github.com/surpher/PactSwift

Contract tooling:

- Zod v4 has native `z.toJSONSchema()` with `target: "openapi-3.0" | "draft-2020-12"`, `io: "input" | "output"`, metadata via `.meta()` and registries, `$ref` extraction via `reused: "ref"`. https://zod.dev/json-schema
- chanfana (Cloudflare-maintained) adds OpenAPI 3 / 3.1 generation and Zod v4 request validation to Hono and itty-router; used by Cloudflare's Radar API. https://github.com/cloudflare/chanfana
- `@hono/zod-openapi` is actively released (1.6.x); the official example serves an OpenAPI 3.0.0 document. https://hono.dev/examples/zod-openapi
- openapi-typescript v7 generates zero-runtime TypeScript types from OpenAPI 3.0/3.1. https://openapi-ts.dev/
- Stoplight Prism serves mock responses from an OpenAPI document, validates incoming requests against it, and generates dynamic data with `-d`. https://docs.stoplight.io/docs/prism/674b27b261c3c-overview
- Schemathesis runs property-based tests against OpenAPI 3.x/3.2 schemas, chains operations, and emits a minimal curl reproducer per bug (`uvx schemathesis run <url>`). https://schemathesis.readthedocs.io/en/stable/
- Pact's own docs distinguish consumer-driven contracts (contract by example, only the parts consumers use) from provider contract testing against an OpenAPI document. https://docs.pact.io/

Decision records and pre-mortems:

- MADR 4.0.0 (2024-09-17): title, context and problem statement, considered options, decision outcome, consequences; files `docs/decisions/NNNN-title-with-dashes.md`. https://adr.github.io/madr/
- Nygard's original format (2011): title, context, decision, status (proposed, accepted, deprecated, superseded), consequences; one or two pages; never edit, supersede. https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- Klein, "Performing a Project Premortem", HBR September 2007, citing Mitchell, Russo and Pennington (1989): imagining an event has already occurred improves identification of reasons for outcomes by about 30 percent. https://hbr.org/2007/09/performing-a-project-premortem

## 4. Detailed spec

### 4.1 Where design sits, what it consumes, what it emits

Inputs: the specification from the previous phase (goals, users, scope boundaries, non-goals), the research ledger, the shape classification and size estimate from intake, and for existing codebases a read of the current architecture (the skill should have the `audit` or `Explore` results at hand).

Outputs, all in the project repository (never in the skill directory, which is procedural memory, not project memory):

```
docs/design/README.md              index; sizes; "reconciled at <commit>" line
docs/design/backend.md             (medium and above)
docs/design/frontend.md            (any shape with a UI)
docs/design/intent/tokens.json     design tokens, single source of truth for visuals
docs/design/intent/screens/<screen>.md   per-screen intent, observable statements
docs/design/intent/reference/<screen>-<state>-<scheme>.png   mockups, if produced
docs/design/baselines/             accepted screenshots, written by the vision verifier later
docs/design/claims.md              behavioral claims -> refuting tests -> status rung
docs/design/reviews/<date>-<what>.md   reviewer verdicts and pre-mortems
docs/design/research-to-verify.md  things assumed in the design that a research step must confirm
docs/decisions/README.md           one line per decision record
docs/decisions/NNNN-<title>.md
contract/                          the seam (section 4.5)
.claude/rules/design.md            path-scoped pointers so implementers read the right docs
```

The design gate is the exit of this phase. All of the following must hold, and the orchestrator records which agent produced each piece of evidence:

1. The contract package emits its OpenAPI document without error; the committed document equals the emitted one; every fixture validates against its schema.
2. Every endpoint named in `backend.md` exists in the contract and every contract operation is mentioned in `backend.md` (a Sonnet checker does this; see 4.7).
3. Every screen in `frontend.md` has an intent file, and every intent file lists at least the loading, empty, error, and populated states where they apply.
4. `claims.md` names at least one refutable behavioral claim per component, in plain words.
5. A review verdict file exists with `pass` or `pass-with-changes`, every `block` finding has a recorded resolution, and the pre-mortem section is non-empty.
6. The decision index lists every non-default technology or pattern choice, and every accepted risk from the pre-mortem.
7. STATUS rows exist for every component at the "Missing" or "Scaffold" rung; STATE lists the research-to-verify items with a status each.
8. `.claude/rules/design.md` exists with `paths:` frontmatter so implementer subagents load the right docs when they touch the right directories.

The orchestrator must not write the review verdict itself. If the reviewer blocks and the designer disagrees, the orchestrator (Fable) adjudicates once, records the adjudication in the review file, and moves on. Never loop more than twice; a third disagreement becomes a proposed decision record with both positions and the implementation proceeds with the reviewer's position, because the reviewer is the one who did not write the thing.

### 4.2 How much design is enough

The honest answer is "enough that two agents working in parallel would not make different assumptions about the same thing." That varies by scope, so the skill sizes design at intake:

| Size | Typical shapes | Design artifacts | Review |
|---|---|---|---|
| Trivial | bug fix, copy change, dependency bump | none; a diagnosis note in STATE (hypothesis, evidence, refuting test) | none |
| Small | one screen or one endpoint, no new storage, no new external dependency | change design (one page, in the PR description or `docs/design/changes/<slug>.md`); contract delta with fixtures; screen intent file if UI | Sonnet consistency checker only, unless the change touches auth, deletion, payments, or migrations, in which case the reviewer runs |
| Medium | new storage table or new external dependency, or several surfaces | `backend.md` change sections (data model delta, failure semantics, cost), `frontend.md` for new screens, contract, decision records for each non-default choice | reviewer (Opus) with a short pre-mortem (three causes) |
| Large | greenfield app, service migration, new subsystem | the full set from 4.1 | reviewer (Opus, or Fable for migrations), full pre-mortem, optionally two or three designs in parallel then compared |

Two rules stop the phase from expanding. First, the design phase is time-boxed to what parallel implementation needs to start; a decision whose answer implementation does not need yet is written as a proposed decision record with a "decide by" trigger (a milestone or a measurement), not resolved now. Second, no design doc may exceed the size a reviewer can read in one sitting; if `backend.md` passes roughly 2,500 words, split by component and let the index carry the map.

### 4.3 Backend design document

`docs/design/backend.md` uses this section order. Each section says what it must contain; a section that does not apply says "not applicable because ..." rather than being omitted, so the checker can tell absence from oversight.

1. Context. Three paragraphs at most: what the system does, who calls it, what already exists. Link the spec; do not restate it.
2. Components. One paragraph per component with its single responsibility, what it owns (data, secrets, external connections), and what it must never do. A component diagram is optional; if present, use a Mermaid block so it renders and diffs.
3. Data model. Tables or collections with keys, types, indexes, and the queries each index serves. For every table: expected row count at three scales (launch, one year, "we got lucky"), row size, retention, and whether it holds personal data. Soft-delete policy. Identifier scheme (I default to ULIDs as text: sortable, no coordination). Include the platform limits that bite: for D1, the 100 bound parameters per statement and the 10 GB per database, with the design's headroom against each.
4. API contract. A pointer to `contract/` plus the conventions the contract follows: URL versioning (`/v1`), error format (RFC 9457 problem details: `type`, `title`, `status`, `detail`, `instance`, plus `request_id`), pagination (cursor-based, opaque cursor), timestamps (RFC 3339 UTC), idempotency header name, authentication header. The document never restates schemas; the contract is the source of truth.
5. Auth model. Identities (users, devices, services), how each authenticates, token lifetimes and rotation, and the authorization rule per resource stated as "a caller may X a Y when Z". Where secrets live. What happens on revocation.
6. Failure semantics. A table, one row per write path: what the client observes on success, on timeout, on partial failure; whether retry is safe; what compensation runs; what state is left behind if compensation also fails. This is the section reviewers read first and designers most often skip.
7. Idempotency. Which operations are idempotent by nature, which require a client key, where keys are stored, their TTL, and what a replay returns (the original response, not a new success).
8. Observability. The structured log shape (fields, always including `request_id`, a hashed user reference, component, and outcome), which metrics exist and where to read them, the three questions an operator will ask at 3 a.m. and the query that answers each, and what alerts (if any) fire and to whom.
9. Cost envelope. Assumptions in one table (users, actions per user, object sizes), unit prices with URLs, monthly totals at the three scales, the dominant cost line, and the kill switch for it (a flag or quota that caps spend when a metric crosses a threshold). Rough is fine; absent is a block.
10. Environments. Names, which resources each owns (never shared buckets or databases across environments), how the client selects one, what test data lives where.
11. Deployment. The command or trigger that deploys each environment, what runs before promotion, how a version reaches production (gradual or all at once), and who or what can trigger it. Under the owner's preferences this is automated: main deploys to staging, the skill promotes to production after live proof.
12. Rollback. The command, its limits (on Cloudflare: code only, no schema, no bindings), and therefore the schema compatibility rule (expand-and-contract: every migration must keep the previous code version working).
13. Scaling cliffs. The ordered list of hard limits the design will hit as usage grows, with headroom, and whether the design will notice before hitting each.
14. Security boundaries. A trust-boundary list: what enters from the device, from third parties, from operators; validation at each boundary; what is encrypted where; the personal-data map and the deletion path that satisfies an account-deletion request end to end.
15. Claims. Five to fifteen sentences of the form "when X, the system Y", each refutable by a test, copied into `claims.md`.
16. Research to verify. Every assumption the design rests on that was not verified in the research phase, with the cheapest way to verify it.
17. Open decisions. Pointers to proposed decision records.

Contract-first conventions for the Cloudflare backend the skill should default to unless a decision record says otherwise: TypeScript, a single Worker with Hono, Zod schemas from the contract package for request validation, D1 for relational state, R2 for blobs, Workflows for any multi-step job with retries, Queues only when an external event source demands them, Durable Objects only when per-entity coordination or real-time fan-out is a requirement of the spec, Workers Logs on, `wrangler` environments `dev`, `staging`, `production`.

### 4.4 Frontend design document and the design intent record

`docs/design/frontend.md` covers, in this order: information architecture (the objects users think in, and the hierarchy among them), screen inventory (a table: screen, route, purpose, data dependencies, states), navigation (the graph, deep links, back behavior, modal versus push), state model (what is server truth, what is local truth, what is derived; where each lives; how sync and conflict work), design system (a pointer to `tokens.json` plus the rules that tokens cannot express: when to use the accent color, how many primary actions a screen may have, image treatment), component inventory (reusable components with their variants and states), empty/loading/error/offline states as a policy (skeletons versus spinners, when to show a retry, what an empty state must contain), accessibility requirements (Dynamic Type range, VoiceOver labeling rules, contrast, reduce-motion behavior, hit-target minimum 44 pt, no color-only meaning), responsive and adaptive rules (size classes, iPad, landscape, or explicitly "iPhone portrait only, v1"), and dark mode (both schemes from day one, tokens carry both).

The design intent record is what makes UI verification possible later, and it has three parts.

Tokens, `docs/design/intent/tokens.json`. Keep the format small and own it; the W3C Design Tokens Community Group format is an option if the project already uses tooling that reads it (verify the current spec version before adopting). Minimal shape:

```json
{
  "color": {
    "bg":            { "light": "#FAF8F5", "dark": "#141311" },
    "surface":       { "light": "#FFFFFF", "dark": "#1E1C19" },
    "text.primary":  { "light": "#1A1816", "dark": "#F3EFE9" },
    "text.secondary":{ "light": "#6B655E", "dark": "#A39C93" },
    "accent":        { "light": "#B5482B", "dark": "#E0714F" },
    "danger":        { "light": "#B3261E", "dark": "#F2857D" }
  },
  "type":   { "family": "system", "scale": { "title": 28, "heading": 22, "body": 17, "caption": 13 }, "weights": { "title": "semibold", "body": "regular" } },
  "space":  { "xs": 4, "sm": 8, "md": 16, "lg": 24, "xl": 32 },
  "radius": { "sm": 6, "md": 12, "lg": 20 },
  "motion": { "fast": 150, "base": 250, "easing": "easeOut", "reduceMotion": "respect" },
  "layout": { "gridColumns.compact": 3, "gutter": 8, "hitTarget": 44 }
}
```

The frontend implementer generates or hand-writes the platform token file (`DesignTokens.swift`, `tokens.css`) from this JSON, and a unit test parses the JSON and asserts equality with the platform constants. That test is the seam that stops "the tokens exist but the code hardcodes #333". Add a grep gate in the test plan: no literal color or point-size in view code outside the token file.

Per-screen intent, `docs/design/intent/screens/<screen>.md`:

```markdown
# Screen: Closet
Route: closet (tab 1). Data: list garments. States: loading, empty, populated, error, offline.

## Purpose
One sentence a stranger would understand.

## Layout intent
Grid of garment cut-outs, three columns on compact width, gutter = space.sm, cards use radius.md,
category filter chips above the grid, one floating "Add" action.

## Must be true (each line is something a screenshot or an accessibility tree can confirm)
1. Exactly one filled accent-colored button is visible, labeled "Add garment".
2. Empty state shows one illustration, one heading, one body line, and that button; no grid chrome.
3. Loading shows skeleton cards in the grid shape, not a spinner.
4. All text is at least 4.5:1 against its background in both schemes.
5. At Dynamic Type accessibility XL the grid drops to two columns and no garment name is truncated.
6. Every garment image has an accessibility label built from its category and color.

## Must not be true
- No literal colors outside tokens. No meaning carried by color alone. No text under 13 pt.

## Reference
reference/closet-populated-light.png, reference/closet-populated-dark.png (design canvas, 2026-09-14).
Treat as intent, not as a pixel target.

## Open decisions
Pointers to proposed decision records, if any.
```

The vision verifier (another component) receives the screenshot, this file, `tokens.json`, and the accepted baseline from `docs/design/baselines/` if one exists, and returns a structured diff against the numbered statements. Statements that cannot be checked from a screenshot or an accessibility tree ("feels premium", "delightful") are banned from the "must be true" list; put taste in the layout-intent prose and let the `frontend-design` skill's guidance shape it, but grade only what can be observed.

Reference mockups are optional. For a greenfield consumer app they are worth producing with the installed `design` skill (canvas artboards, exported PNG) because they anchor the vision verifier and the implementer alike; for a dashboard feature inside an existing design system they are usually not worth the time, and the intent file plus existing components suffice.

### 4.5 Interface-first decomposition: the contract package

The principle: the contract is data that neither implementation owns. The design phase writes it; implementation agents consume it; changing it is a contract-change step (fixtures updated, both sides regenerated, both contract test suites green, one commit), never a side effect of implementing a feature.

Layout:

```
contract/
  package.json                # scripts: emit, check, mock, test
  src/schemas.ts              # Zod v4 schemas with .meta({ id, description, examples })
  src/endpoints.ts            # declarative operation table (below)
  src/emit-openapi.ts         # builds openapi.yaml from schemas + table + fixtures
  openapi.yaml                # generated; committed; drift-checked
  fixtures/<operation>/<case>.json   # { request: {...}, response: { status, body } }
  generated/types.ts          # openapi-typescript output for non-Zod consumers (optional)
```

The operation table is plain TypeScript data:

```ts
export const operations = {
  createGarment: {
    method: "POST", path: "/v1/garments",
    auth: "user", idempotency: "required",   // Idempotency-Key header
    request: { body: CreateGarmentRequest },
    responses: { 201: Garment, 400: Problem, 401: Problem, 409: Problem, 422: Problem },
    summary: "Create a garment record before uploading its photo",
  },
  // ...
} as const satisfies Record<string, Operation>;
```

`emit-openapi.ts` walks the table, converts each schema with `z.toJSONSchema(schema, { target: "openapi-3.0", io: "input" })` for requests and `io: "output"` for responses, extracts shared components through a Zod registry (`reused: "ref"`), attaches every fixture as a named example on its operation, and writes `openapi.yaml`. The backend imports the same table and schemas to register Hono routes and validate requests (chanfana or `@hono/zod-openapi` are acceptable adapters, but keep the table as the source and the adapter thin). The iOS package generates its client from `openapi.yaml` with Swift OpenAPI Generator (`generate: [types, client]`), so it never sees Zod.

Fallback when the backend is not TypeScript: hand-write `openapi.yaml` as the source of truth, generate server types and validators from it, and keep the same fixture and drift rules. The seam is the same; only the direction of generation changes.

Commands the skill runs at the design gate and in CI:

```bash
# contract emits and has not drifted
npm --prefix contract run emit && git diff --exit-code contract/openapi.yaml
# fixtures validate against schemas
npm --prefix contract run check
# mock server for the frontend agent, serving the fixtures as named examples
npx @stoplight/prism-cli mock -d contract/openapi.yaml -p 4010   # client sends Prefer: example=<case>
# Swift client
swift run swift-openapi-generator generate contract/openapi.yaml \
  --mode types --mode client --access-modifier package \
  --output-directory ios/Packages/APIClient/Sources/Generated
```

Contract tests are the seam, and each side has two layers.

Backend, in workerd via `@cloudflare/vitest-plugin`: for every operation and fixture, send the fixture request to `SELF.fetch`, assert the status matches and the body parses with the response schema, and for stateful cases assert the D1 rows. Then a property-based sweep: `uvx schemathesis run http://127.0.0.1:8787/openapi.json --checks all` against `wrangler dev`, which catches the schema-versus-implementation mismatches fixtures never think of. Both run in the real runtime; the shim rule in section 7 explains why this is not negotiable.

Frontend, in Swift Testing: a fake `ClientTransport` that returns each fixture response, asserting the generated client decodes every fixture (this catches nullable, `oneOf`, and date-format edge cases in generated code before any network exists); then an integration target against Prism for two or three flows end to end; then a smoke test against staging as part of live proof. Consumer-driven Pact contracts (PactSwift) are an option when a third party owns the provider; for a backend the same skill builds, the fixtures plus Schemathesis give the same assurance with one fewer tool.

Ownership rules for parallel agents, stated in the implementation prompts: the backend agent owns `worker/`, the frontend agent owns `ios/`, nobody edits `contract/` during implementation without a contract-change step, and a contract-change step is executed by the architect agent (or the orchestrator) rather than by whichever implementer hit the gap. Fixtures are the shared vocabulary; when an implementer finds the fixture set insufficient, the request is "add fixture for case X", and it goes through the same path.

### 4.6 Architecture decision records

Use MADR-lite. One file per decision at `docs/decisions/NNNN-title-with-dashes.md`, sequential numbers never reused, plus `docs/decisions/README.md` with one line per record (number, title, status, date). The format:

```markdown
# 0003: Store garment photos in R2 with presigned uploads

Status: accepted (2026-09-14). Supersedes: none. Applies to: worker/src/photos/**, ios/Packages/Upload/**

## Context
Two or three sentences on the forces: photo sizes, Worker request limits, device connectivity, cost.

## Options considered
1. Upload through the Worker, Worker writes to R2.
2. Presigned PUT from the device directly to R2, Worker verifies afterwards.
3. Cloudflare Images direct creator upload.

## Decision
We will use presigned PUT URLs (15-minute expiry, Content-Type pinned) issued by the Worker,
followed by an explicit completion call that verifies the object exists.

## Consequences
Good: no upload bytes through the Worker; free egress. Bad: orphaned objects on abandoned uploads,
handled by a Workflow that waits for the completion event and deletes on timeout. Neutral: URLs
work only on the S3 API domain, so the app never uses custom domains for uploads.

## How we would reverse this
Add a Worker upload route behind the same completion contract; the client change is one adapter.
```

Write a record when any of the following is true: the design chose between two or more viable options with lasting consequences; the design uses a beta or preview feature on the critical path; the design overrides one of the skill's defaults; the reviewer flagged a choice; a pre-mortem risk is accepted rather than mitigated; an implementer proposes a change to the contract. Do not write one for choices that have no reasonable alternative or that a later reader could re-derive in a minute.

Consultation is the part most teams get wrong, and the harness gives three mechanisms. First, `.claude/rules/design.md` with `paths:` frontmatter lists the design docs and decision records relevant to each directory, so any implementer subagent that touches `worker/src/photos/` loads the photo decisions without being told (verified: subagents load project rules). Second, the decision index is imported into the project `CLAUDE.md` with `@docs/decisions/README.md`, so every session sees the one-line list. Third, the design reviewer and the failure-analysis component are instructed to read the index and cite record numbers in their findings, which keeps records alive. Records are never edited after acceptance; a change is a new record that supersedes, and the old one's status line says so.

### 4.7 Independent design review and the pre-mortem

The reviewer is a separate agent with a fresh context, no access to the designer's transcript, and read-only tools plus the ability to write its verdict file. It receives paths, not summaries: the design docs, the contract, `claims.md`, the decision index, the spec, and the research ledger. It is told the project shape and size.

Rubric. Eleven dimensions, each scored 0 (absent or wrong), 1 (present with gaps), 2 (sound), and each score must cite the section or file it judged:

1. Simplicity: could any component, table, or dependency be removed without losing a spec requirement?
2. Boring technology: is every non-default or beta choice justified in a decision record, and is anything in preview on the critical path?
3. Single source of truth: for every important fact (identity, contract, tokens, garment attributes) is there exactly one owner, and are derived copies regenerated rather than edited?
4. Failure handling: does every write path have stated partial-failure behavior, safe retries, timeouts, and compensation?
5. Security boundaries: are trust boundaries drawn, inputs validated at each, authorization stated per resource, secrets placed, personal data mapped with a deletion path?
6. Scaling cliffs: are the hard limits listed with headroom, and will the system notice before hitting the first one?
7. Vendor lock-in: is the cost of leaving each vendor stated, and is the lock-in deliberate and recorded?
8. Testability: does every claim have a refuting test that can run locally in a production-faithful harness, and do the seams (contract, fixtures, mock transport) exist?
9. Cost: is the envelope present with assumptions, a dominant driver, and a kill switch?
10. Operability: can a tired person find what broke from the logs and the three 3 a.m. queries?
11. Data lifecycle and privacy: retention, deletion, backups, restore drill, and what a user can take with them.

Verdict rules: any 0 on failure handling, security boundaries, or testability is `block`; no blocks and no 0 anywhere is `pass` or `pass-with-changes` depending on whether any `major` findings remain. The output is JSON first (so the orchestrator can act on it) and a readable Markdown rendering second:

```json
{
  "verdict": "pass-with-changes",
  "scores": { "simplicity": 2, "boring": 1, "single_source": 2, "failure": 1, "security": 2,
              "scaling": 2, "lockin": 2, "testability": 2, "cost": 1, "operability": 1, "data": 2 },
  "findings": [
    { "severity": "major", "dimension": "failure", "where": "backend.md#6-failure-semantics",
      "claim": "Abandoned uploads leave objects in R2 forever",
      "evidence": "No row in the failure table for 'presign issued, PUT never completes'",
      "fix": "Start a Workflow at presign time; waitForEvent('uploaded', 1h); delete on timeout",
      "needs_decision_record": true }
  ],
  "premortem": [
    { "cause": "Inference bill 10x the envelope because suggestions were re-run on every app open",
      "probability": "medium", "detectable_by": "AI Gateway cost analytics; per-user daily counter",
      "mitigation": "Per-user daily quota in D1 plus 24h cache keyed on wardrobe hash + context",
      "decision": "mitigate" }
  ],
  "unverified_assumptions": [ "Images segment=foreground quality on garments photographed on a bed" ]
}
```

Pre-mortem procedure, run by the same reviewer as the second half of its task, after scoring, so the scoring is not colored by the invented failures:

1. Write one paragraph dated six months from now stating that the project failed, was rolled back, or is quietly unused. Pick the most plausible of the three for this shape.
2. List at least six causes, at least one from each of: data loss or corruption, cost, a platform limit, auth or security, user abandonment, vendor or dependency change, an operational blind spot, integration drift between backend and frontend.
3. For each cause: name the design element that permits it; state how it would be detected (a test, a metric, an alert) and whether the design already contains that detection; propose the mitigation and its cost; recommend mitigate, accept, or "needs a decision record".
4. Rank by probability times damage. The top three must be resolved before the gate: mitigated in the design, or accepted in a decision record titled "Accepted risk: ...".

Klein's HBR article summarizes the research basis: prospective hindsight raises the rate of correctly identifying reasons for outcomes by about 30 percent. The value for agents is structural rather than psychological; a reviewer asked "is this good?" praises, a reviewer asked "why did this fail?" has to name mechanisms, and named mechanisms turn into tests.

The Sonnet consistency checker is a separate, cheap, mechanical pass that runs before the reviewer so the reviewer spends judgment on judgment: it returns JSON listing endpoints in `backend.md` missing from the contract and vice versa, screens in `frontend.md` without intent files, intent files missing a required state, claims without a test path, decision records referenced but absent, and tokens used in reference prose that do not exist in `tokens.json`.

For greenfield and migration shapes the skill may draft the backend design from several angles before review: three architect agents in parallel, each given the same spec and one constraint ("the fewest moving parts", "the cheapest at 100x scale", "the easiest to operate alone"), then the reviewer compares and recommends one or a merge. The workflows documentation names this use; it costs roughly three designs' worth of Opus tokens and is worth it only when the blast radius is the whole system.

### 4.8 Connecting design to STATUS, STATE, and the test plan

The bridge is `docs/design/claims.md`, one row per behavioral claim, written during design and completed during testing:

```markdown
| Claim (plain words) | Component | Refuting test | Rung | Evidence |
|---|---|---|---|---|
| A garment photo upload that is never completed leaves no object in R2 after one hour | photos | worker/test/photos.abandoned.test.ts | Missing | |
| Replaying a create-garment request with the same idempotency key returns the original 201 and creates one row | garments | worker/test/idempotency.test.ts | Missing | |
| Outfit suggestions never reference a garment the user has deleted | suggestions | worker/test/suggest.tombstones.test.ts | Missing | |
```

The test-design component turns each row into a test that tries to make the claim false; the status component moves the rung (Missing, Scaffold, Partial, Local Proof, Live Proof, Operational, Done) and fills Evidence with a path or URL. A claim without a test cannot pass Scaffold. A claim whose test runs only in a harness kinder than production cannot pass Local Proof. Design docs are read as the plan; when code and doc disagree, code wins and the doc is what gets fixed, in the reconcile step at the end of implementation, where the Sonnet checker diffs `backend.md` sections against the contract and the code and the architect updates the doc and its "reconciled at <commit>" line.

STATE gets two design-phase sections: "Design decisions" (one line per accepted record, with number) and "Research to verify" (each assumption with `unverified`, `verified <date> <url>`, or `refuted <date>` and the consequence). STATUS gets the component rows at their starting rung. The decision index and the claims table are what a future session reads first to resume rather than restart.

### 4.9 Worked example: the outfit app

Input, paraphrased from the brief: a fashion and outfit-creating iOS app; users photograph garments, the app builds a closet, suggests outfits for an occasion, and lets users compose and save outfits. Cloudflare backend, native Swift front end. What follows is the design I would commit to, with the reasoning, and the list of things to verify by research before committing.

Backend on Cloudflare.

Runtime and shape: one Worker (TypeScript, Hono) exposing `/v1`; one D1 database; one R2 bucket per environment; one Workflow class for photo ingest; AI Gateway in front of Anthropic with BYOK; Workers Logs on. No Durable Objects, no Queues, no Vectorize in v1. The reasoning for each omission: the spec has no per-entity real-time coordination (Durable Objects earn their place when two clients must agree on one object's state live); Workflows already provide retries, persisted state, sleeps, and event waits, so a Queue would only add a second place to look; similarity search over garments is a v2 feature, and until it exists an embedding index is a cost without a caller.

Data model in D1, ULID text primary keys, all tables with `user_id`, `created_at`, `updated_at`, `deleted_at`:

- `users` (apple_sub unique, email_relay, created_at)
- `sessions` (refresh_token_hash unique, expires_at, revoked_at)
- `garments` (category, subcategory, colors_json, pattern, material, formality 1-5, seasons_json, fit, brand, notes, attributes_source enum manual|model, attributes_confidence)
- `garment_photos` (garment_id, kind original|cutout|thumb, r2_key, width, height, bytes, state pending|ready|failed, workflow_instance_id)
- `outfits` (name, occasion, is_favorite), `outfit_items` (outfit_id, garment_id, slot)
- `suggestions` (context_json, model, input_tokens, output_tokens, cost_micros, wardrobe_hash), `suggestion_outfits` (suggestion_id, garment_ids_json, rationale, rank), `suggestion_feedback` (suggestion_outfit_id, verdict worn|liked|dismissed)
- `wear_log` (garment_id, worn_on date)
- `idempotency_keys` (key, user_id, request_hash, response_status, response_body, expires_at)
- `usage_daily` (user_id, day, suggestions_count, photos_count)

Indexes: `(user_id, updated_at)` on every user-owned table for sync pulls; `(user_id, deleted_at)` where lists exclude deleted rows; `(garment_id, kind)` on photos; `(user_id, day)` unique on `usage_daily`. Row budget at 1,000 users with 50 garments each: 50k garments, 150k photos, a few hundred thousand wear-log rows over a year; far inside the 10 GB and the included read and write allowances. Every multi-row insert is chunked to `floor(100 / columns)` rows per statement because of the bound-parameter limit, and every multi-statement write is a single `batch()` because that is the only transaction D1 has. Read replication stays off (beta, and per-user data does not need it).

Photos: the device pre-resizes to a 2048 px long edge, strips EXIF (location data has no business on the server), and encodes JPEG at quality 0.85. The Worker issues two presigned PUT URLs (original and cut-out, Content-Type pinned, 15-minute expiry) and at the same moment starts a `GarmentIngest` Workflow instance whose first step is `waitForEvent("uploaded", timeout 1h)`. The device uploads with a background `URLSession` so the transfer survives backgrounding, then calls `POST /v1/garments/{id}/photos/{photoId}/complete`, which verifies both objects with `HEAD`, records sizes, and sends the event. If the event never arrives the Workflow deletes the pending objects and marks the photo `failed`; no orphans, no lifecycle-rule guesswork. Subsequent steps: derive a 512 px thumbnail (Images transformation on the R2 object, cached), then call Claude with the cut-out to extract attributes as structured output (category, colors as named swatches with hex, pattern, material guess, formality, seasons, fit) and write them with `attributes_source = model`. Invalid images raise `NonRetryableError`; transient failures retry with backoff; a rollback handler deletes derived objects if a later step fails permanently.

Background removal: on device first, server fallback. `VNGenerateForegroundInstanceMaskRequest` (iOS 17+) produces the cut-out in well under a second on modern hardware, costs nothing, works offline, and keeps the original photo's background (often a bedroom) off the server entirely in the common path; the app uploads original and cut-out together. The Worker falls back to Images `segment=foreground` when the device reports a low-confidence mask or the client is older. This is a real trade: two implementations of one feature. I accept it because the server path is a single transformation parameter, and because the privacy and cost wins of the device path are large. Quality comparison on real garment photos is the first research item below.

Attributes and suggestions with Claude: route through AI Gateway (BYOK, caching, cost analytics, rate limits) to the Anthropic API. Attribute extraction uses Sonnet 5 by default: at a 1000×1000 cut-out (1,296 visual tokens) plus roughly 400 prompt tokens and 200 output tokens, that is about $0.005 per photo; Opus 5 would be about $0.018. Suggestions send a compact wardrobe summary (attributes and ids, never images) plus the context (occasion, weather, date, recent wear) and ask for three outfits as structured output with garment ids and one-line rationales; the Worker validates every id against live rows before storing or returning. Default Sonnet 5 at roughly 3,000 input and 500 output tokens is about $0.011 per suggestion; Opus 5 about $0.028. Caching key: hash of the wardrobe attribute set plus normalized context plus day, so reopening the app does not re-bill. Per-user daily quota lives in `usage_daily` (the rate-limit binding is per-location and eventually consistent, useful against bursts, useless as a quota).

Cost envelope at 1,000 monthly active users, 50 garments each, 12 suggestions per user per month: Workers Paid $5; R2 about 100 GB of originals and cut-outs, about $1.50; D1 inside included allowances; Workflows and Logs inside included allowances; one-time attribute extraction of 50k photos about $250 on Sonnet 5 (about $900 on Opus 5); suggestions about $130 per month on Sonnet 5 (about $330 on Opus 5); Images transformations for thumbnails 50k unique, about $25 one-time. Inference dominates by two orders of magnitude, which is why the design spends its complexity on caching, compact summaries, and quotas, and why the kill switch is a per-environment flag that downgrades suggestions to a rules-based composer when daily spend from AI Gateway analytics crosses a threshold.

Auth: Sign in with Apple only. The app obtains the identity token; the Worker verifies it with `jose` against Apple's JWKS (issuer `https://appleid.apple.com`, audience the bundle id, expiry), creates the user keyed on `sub`, and issues its own access token (1 hour) plus a rotating refresh token stored hashed. No third-party auth vendor: one provider, one JWKS fetch, no monthly bill, no lock-in. App Attest is designed for but not built in v1: the contract reserves an `X-App-Assertion` header on presign and suggestion endpoints so abuse controls can arrive without a contract change.

Observability: structured JSON logs with `request_id`, `user_ref` (hashed), `op`, `outcome`, `duration_ms`, and for inference `model`, `input_tokens`, `output_tokens`, `cache_hit`; head sampling 1.0 in staging, 0.2 in production; the three 3 a.m. queries are "failures by op in the last hour", "Workflow instances stuck in waiting over one hour", and "inference cost by user today". Workflow instance status is inspected with `wrangler workflows instances describe`.

Environments, deployment, rollback: `dev` (local `wrangler dev` with local D1 and R2), `staging`, `production`, each with its own D1, bucket, gateway, and secrets. Main deploys to staging automatically (Workers Builds); the skill promotes to production with `wrangler deploy --env production` after the staging end-to-end run passes, and TestFlight builds point at staging. Rollback is `wrangler rollback`, which restores code only, so every D1 migration is expand-and-contract and the previous version must keep working against the new schema; the contract test suite runs against the previous Worker version in CI for exactly this reason.

Decision records this design would produce: D1 over Postgres via Hyperdrive (reversal cost: a repository layer and a migration script); presigned uploads over Worker-proxied uploads; on-device cut-out first with server fallback; Sign in with Apple only; Sonnet 5 default with Opus 5 behind a flag; no Durable Objects or Queues in v1; Workflows for ingest; accepted risk: read replication off, so a user in Sydney sees roughly 200 ms extra on cold reads.

Swift front end.

Minimum iOS 26, targeting the iOS 27 SDK with Swift 6.4 in strict concurrency. iOS 27 released today, so requiring the previous major excludes only devices that cannot run iOS 26, and it makes the `Observations` async sequence and the iOS 26 system design language available. Whether to adopt the system's materials wholesale or keep a warmer custom look is a decision record, taken with the `frontend-design` skill's guidance and the current Human Interface Guidelines in hand.

Architecture: SwiftUI with the Observation framework. One `AppModel` at the root, one `@Observable` feature model per screen owning that screen's state and intents, a `Dependencies` value injected through the environment holding the API client, the store, the photo pipeline, and a clock, with protocol-typed members so tests inject fakes. No ViewModel ceremony beyond that, and no Composable Architecture: TCA is well built, but its reducer and effect plumbing is a surface that parallel agents keep getting subtly wrong, and Observation plus plain protocols gives the same testability at a fraction of the vocabulary. Navigation uses `NavigationStack` with a typed `Route` enum per tab, a `TabView` of four tabs (Closet, Outfits, Today, Profile), and a deep-link parser that maps URLs to routes so tests and the vision verifier can jump to any screen.

Networking: the generated client from Swift OpenAPI Generator with the URLSession transport; a `ClientMiddleware` injects the access token, refreshes on 401 once, and adds a request id; generated `Problem` errors map to a small domain error enum the UI can render. Uploads bypass the generated client and go straight to the presigned URLs through a background `URLSession` with the pinned Content-Type.

Offline cache and sync: GRDB over SwiftData. The closet must work in a fitting room with no signal, search must be instant, and the sync layer needs explicit cursors, tombstones, and an outbox, all of which are plain SQL in GRDB and fought-for in SwiftData; GRDB's `ValueObservation` also feeds Observation-based models cleanly. Sync is pull by `updated_at` cursor per table with tombstones honored, and push through an outbox table of local mutations (wear log, favorites, manual attribute edits) each carrying an idempotency key; the server is authoritative and conflicts resolve last-writer-wins in v1, recorded as an accepted risk. SwiftData remains acceptable if a decision record argues the app will stay small; the migration story is the risk that decides it.

Photo capture: `PhotosPicker` (no permission prompt, user picks what to share) plus an AVFoundation camera view for in-app capture with a garment-outline overlay; the pipeline downsizes, strips metadata, encodes, runs the Vision foreground mask, previews the cut-out for the user to accept or retake, then uploads. The cut-out is PNG with alpha because outfit composition layers garments.

Design system: the tokens in 4.4 are a plausible starting palette (warm off-white and near-black grounds, one terracotta accent, system type at a 13/17/22/28 scale, 4/8/16/24/32 spacing, 6/12/20 radii). Rules tokens cannot express: one filled accent action per screen; garment imagery is always the cut-out on the surface color, never the original photo, so the closet reads as a catalog; color names appear beside swatches everywhere color carries meaning.

Screens (each with an intent file): Onboarding (sign in, one-paragraph promise, camera intro), Closet (grid, filters, empty and loading states), Garment detail (cut-out, attributes with edit, wear history), Add garment (capture, cut-out preview, attribute review), Outfits (saved list), Outfit composer (drag garments onto a canvas of slots), Today (context input, three suggestions, accept or dismiss), Profile (account, data export, delete account, quotas).

Accessibility: Dynamic Type through the accessibility sizes with grid fallbacks; every garment image labeled from category and color; VoiceOver order defined per screen; reduce-motion swaps the composer's animations for cross-fades; 44 pt targets; contrast checked in both schemes by a test that renders each token pair.

Testing seams the design provides: Swift Testing units with injected fakes; fixture-driven decoding tests through a fake transport; snapshot tests per screen and state in light and dark at two Dynamic Type sizes with swift-snapshot-testing; XCUITest flows on the Simulator; the Simulator MCP for the vision verifier. Camera and App Attest do not exist in the Simulator, so the intent files mark capture screens as "verify on device or with an injected sample image".

Research to verify before committing the design (the skill runs these as research steps, records results in STATE, and reverses the affected decision if refuted):

1. Cut-out quality on real garment photos: Vision foreground mask versus Images `segment=foreground`, on flat-lay and on-hanger photos with cluttered backgrounds; also whether `segment` bills extra as Workers AI usage beyond the transformation count.
2. AI Gateway passthrough of Anthropic structured outputs and of the `fallbacks` parameter, and whether gateway caching keys on the full body.
3. Sign in with Apple server-side edge cases: private relay emails, token revocation via server-to-server notifications, and the user cancelling mid-flow.
4. Workflows `waitForEvent` behavior and cost with tens of thousands of concurrently waiting instances (the concurrency limit counts running, not waiting, per the docs; confirm the queued-instance limits are not hit at launch bursts).
5. GRDB under Swift 6.4 strict concurrency, and its `ValueObservation` with `@Observable` models.
6. Background `URLSession` PUT to a presigned URL with pinned Content-Type from a suspended app, including retry semantics after a network change.
7. Swift OpenAPI Generator output for the contract's `oneOf` and nullable shapes; adjust the contract's shapes to what generates cleanly rather than fighting the generator.
8. Whether the iOS 26 system design language constrains a custom token palette in ways the HIG now discourages.
9. Weather source for the Today screen (a free, keyless API versus WeatherKit, which has its own quota and entitlement).
10. App Store privacy labels and review guidance for apps that send user photos to a third-party model, and the disclosure copy that satisfies them.
11. Foundation Models on iOS 27 as an offline fallback for attribute extraction, only once the final docs confirm image input.

## 5. Conditionals by project shape

Greenfield app (the outfit app): the full set in 4.1; contract package as the seam; reference mockups worth producing; reviewer on Opus with a full pre-mortem; optional three-angle backend design; decision records for every stack choice; cost envelope mandatory; STATUS rows for every component from Missing.

Deep bug hunt: no design documents. STATE gets a diagnosis note (symptom, hypothesis, evidence for and against, the refuting test). The only design output is a mini decision record if the fix changes an interface or a data shape, and a contract-change step if the bug is in the contract. The reviewer does not run; the adversarial verification component reviews the fix. If the same bug has been "fixed" before, that is a design smell, and the skill escalates to a small design review of the surrounding component (the owner's rule: the second time is the bug).

Feature on an existing product (the dashboard): first extract, do not invent. The architect reads the existing design system and writes `tokens.json` from what the codebase already does; the frontend intent files inherit existing components. The change design is one page: which existing endpoints or queries feed the dashboard, any new query with its index and rows-read cost, the contract delta with fixtures, and the screens with their states. Decision records only for a new library or a new pattern. The reviewer runs only if the change touches auth, deletion, money, or migrations; otherwise the Sonnet checker suffices. Vision verification against intent files is the main quality gate, so intent files matter more here than backend docs.

Migration or consolidation (moving the AI gateway into the platform): the design is a parity-and-cutover plan, not a system design. Artifacts: a behavior inventory of the existing service extracted from its tests, its logs, and its live traffic (capturing an OpenAPI document from traffic if none exists); the target placement inside the platform and the contract the platform will expose; a shadow or dual-run plan with a comparison harness; a cutover switch with a kill switch back; data migration and reconciliation; a decommission checklist; decision records for every behavior deliberately dropped. No frontend design beyond any operator surface. The reviewer runs on Fable with the pre-mortem mandatory, because migration failures are subtle (a header the old gateway silently normalized, a timeout the new one does not honor) and the blast radius is every caller.

Research plus website (market position, marketing site with blog and docs): design is mostly frontend. Information architecture, content model (frontmatter schemas for blog and docs pages, sidebar structure), tokens and reference pages, a performance budget (Lighthouse thresholds as claims), accessibility, hosting (Cloudflare Pages or Workers static assets), and a decision record for the site generator. No backend document unless there is a form or newsletter, in which case a one-page change design and a Turnstile-protected endpoint. The intent files are central because vision verification is the main verification; the reviewer runs on Opus at medium effort, since the risks are content and taste rather than data loss.

Other shapes, briefly: pure research report needs no design phase. Refactor or simplification needs no new design but must read the decision index first and add records for anything it reverses. Ops or incident needs a remediation plan with a rollback line, no design docs. Data pipeline needs source and target schema contracts (the same contract package idea, with fixtures as sample records), replay and idempotency semantics, a backfill plan, and lineage; the reviewer runs. CLI tool needs a command grammar contract (help text and exit codes as the contract, with golden-output fixtures) and a config-file schema. Library or SDK needs the public API surface as the contract, a semantic-versioning policy, and decision records for API shape; contract tests are the public examples compiled and run.

Conditionals the skill should encode as plain sentences: if the task adds storage, write the data model and failure-semantics sections and run the reviewer. If the task adds an external dependency or a beta feature, write a decision record and add a research-to-verify item. If the task has a UI, write intent files and tokens. If the task touches auth, deletion, money, or migrations, the reviewer runs regardless of size. If the task is a migration, the reviewer is Fable and the pre-mortem is mandatory. If more than one implementation agent will write code at once, the contract package exists before any of them starts.

## 6. Model and effort assignment

Roles in this component and my assignments:

| Role | Model | Effort | Tools | Isolation | Predefined |
|---|---|---|---|---|---|
| Backend architect (backend.md, contract package, decision records) | opus | xhigh | Read, Grep, Glob, Bash, WebFetch, WebSearch, Write, Edit | none (writes docs and `contract/` on main) | yes |
| Frontend designer (frontend.md, tokens, intent files, reference mockups) | opus | xhigh | Read, Grep, Glob, Bash, WebFetch, WebSearch, Write, Edit, Skill | none | yes; preloads `frontend-design`, and `web-design-guidelines` for web shapes |
| Design reviewer (rubric, pre-mortem, verdict) | opus by default; fable for migrations and for greenfield when the designer was opus and the orchestrator wants a second tier of judgment | xhigh (max for migrations) | Read, Grep, Glob, WebFetch, WebSearch, Write | none | yes |
| Consistency checker (mechanical cross-checks, drift check) | sonnet | low | Read, Grep, Glob, Bash | none | optional; an inline Agent call with a JSON schema is enough |
| Adjudicator and gate-keeper | fable (the orchestrator itself) | inherits | | | the skill |

Why not Fable for the designers: producing a design document is hard-but-bounded work with a clear rubric, which is the owner's definition of Opus territory, and the reviewer plus adjudication catches what a designer misses more cheaply than a Fable designer would. Why Opus at xhigh rather than high: the claude-api reference notes xhigh is the best setting for most agentic work on this generation, and design is where a missed failure mode costs the most later. Why Sonnet at low for the checker: the checks are list comparisons and file existence; a low-effort Sonnet returns tighter JSON with fewer tool calls, and the owner does not want Haiku in a general skill.

Draft agent definitions for `~/.claude/agents/` (the skill ships them separately, since a skill cannot bundle agents outside a plugin).

`drive-architect.md`:

```markdown
---
name: drive-architect
description: Writes the backend design document, the contract package, and decision records for a project the drive skill is executing. Use after the spec is approved and before implementation.
model: opus
effort: xhigh
tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, Write, Edit
memory: project
color: blue
---
You design backends so that several agents can implement them in parallel without colliding, and so
that later verification has something concrete to check. You write docs/design/backend.md in the
section order the drive skill prescribes, the contract package under contract/, docs/design/claims.md,
docs/design/research-to-verify.md, and decision records under docs/decisions/.

Read first: the spec, the research ledger, docs/decisions/README.md if it exists, and the existing code
if there is any. Prefer boring technology; every non-default or beta choice gets a decision record with
the reversal cost stated. State partial-failure behavior for every write path. Put numbers in the cost
envelope even when rough, with assumptions. Respect platform limits you have verified this session and
cite the URL in the doc. Write claims as sentences a test could make false. Do not restate schemas in
prose; the contract is the source of truth and you keep the doc and the contract consistent.

You do not implement. You do not approve your own design. When you cannot decide, write a proposed
decision record with both options and a "decide by" trigger, and move on.
```

`drive-frontend-designer.md`:

```markdown
---
name: drive-frontend-designer
description: Writes the frontend design document, design tokens, per-screen intent files, and reference mockups for a project the drive skill is executing.
model: opus
effort: xhigh
tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, Write, Edit, Skill
skills:
  - frontend-design
memory: project
color: purple
---
You design user interfaces so that an implementer can build them and a vision verifier can later check
them against your intent. You write docs/design/frontend.md, docs/design/intent/tokens.json, one
docs/design/intent/screens/<screen>.md per screen, and, when the skill asks, reference mockups under
docs/design/intent/reference/ using the design skill.

For an existing product, extract the design system from the code before writing anything; never invent
a second one. For a new product, choose a distinctive direction and record it, then express it as
tokens and rules. Every screen lists its loading, empty, error, and populated states, and any offline
state. In "Must be true" write only statements a screenshot or an accessibility tree can confirm; put
taste in the layout intent prose. Both color schemes from day one. Dynamic Type through accessibility
sizes. Nothing means something by color alone.

You do not implement, and you do not approve your own design.
```

`drive-design-reviewer.md`:

```markdown
---
name: drive-design-reviewer
description: Independently reviews design documents and contracts against the drive rubric and runs a pre-mortem. Must run in a fresh context with no access to the designer's reasoning.
model: opus
effort: xhigh
tools: Read, Grep, Glob, WebFetch, WebSearch, Write
memory: project
color: red
---
You are the reviewer who did not write the design. You receive file paths, never summaries. Read the
spec, docs/design/*, contract/, docs/design/claims.md, and docs/decisions/README.md. Score the eleven
rubric dimensions 0 to 2, citing the section or file behind every score. Any 0 on failure handling,
security boundaries, or testability is a block. Then run the pre-mortem: date it six months out, state
that the project failed, list at least six causes across data, cost, platform limits, auth, abandonment,
vendor change, operations, and integration drift; for each name the design element that permits it, how
it would be detected, the mitigation and its cost, and your recommendation. Rank by probability times
damage.

Be skeptical and specific. A finding without a "where" and an "evidence" is not a finding. Praise is not
output. Write the JSON verdict first and a readable rendering second to docs/design/reviews/<date>-<what>.md.
Do not edit the design; do not implement; do not soften a block because the fix looks expensive.
```

Whether the reviewer should be Fable by default is an open question (section 8). The orchestrator passes `model: fable` per invocation for migrations and for greenfield systems whose failure would be expensive to unwind, which the frontmatter default of opus does not prevent, since the per-invocation parameter wins.

## 7. Failure modes and anti-patterns

The design phase can produce mirage completion in several distinct ways, and each has a structural prevention.

The document that nothing reads. A `backend.md` exists, implementers never open it, and the design gate passes because the file is present. Prevention: the gate checks consistency between doc, contract, and later code, not existence; `.claude/rules/design.md` loads the doc for anyone touching the relevant paths; implementer prompts name the sections they must follow; the reconcile step diffs doc against code at the end.

Contract drift. The contract package is edited by an implementer to make a test pass, the iOS client is not regenerated, and integration fails a day later. Prevention: the drift check (`emit` then `git diff --exit-code`) in the gate and in CI; the ownership rule that implementers do not edit `contract/`; regenerated Swift committed alongside every contract change; a fixture decoding test on the iOS side that fails the moment shapes move.

A harness kinder than production. This is the owner's D1 incident generalized: a sql.js shim let unlimited bound parameters through, 24 green runs, a live failure. Design-phase versions of the same mistake: contract tests that run against Prism only (Prism accepts any request the schema allows and returns examples; it proves the client, never the server); Worker tests in Node with a SQLite shim rather than in workerd; iOS tests with `URLProtocol` stubs that return whatever the test author imagined; Simulator-only verification of camera or App Attest paths. Prevention as a standing question written into the test plan: for every fake, where is it kinder than the real thing? Backend contract tests run in `@cloudflare/vitest-plugin` inside workerd, which enforces the 100-parameter limit locally; Schemathesis runs against the real Worker; iOS integration tests hit Prism for shape and staging for truth; camera paths are marked device-only in the intent files.

The self-approving gate. The orchestrator designs, then "reviews", then passes. Prevention: the verdict file must come from the reviewer agent; the skill checks the file's provenance (agent name in the file header) before opening the gate; adjudication is recorded, never silent.

Rubber-stamp review. The reviewer shares context with the designer, or gets a summary instead of the files, and praises. Prevention: fresh context, file paths not summaries, mandatory evidence pointers, the pre-mortem's requirement to name mechanisms, and a hard rule that a review with zero findings on a large design is itself a finding (the orchestrator re-runs the reviewer with the instruction "the previous review found nothing; that is implausible; find the three weakest points").

Generic pre-mortems. "The team lacked focus", "scope crept". Prevention: every cause must point at a design element and a detection mechanism; causes without both are discarded by the orchestrator before adjudication.

Tokens that decorate rather than govern. A beautiful `tokens.json`, and view code full of literal hex. Prevention: the platform token file is generated or asserted equal to the JSON by a test; a grep gate forbids literal colors and point sizes in view code; the vision verifier gets the tokens and checks the accent count and contrast.

Unverifiable intent. Intent files full of "feels premium" and "delightful". Prevention: the "Must be true" list accepts only observable statements; the checker rejects lines without a noun that appears on screen; taste lives in the layout-intent prose where it guides rather than grades.

Decision graveyard. Records written at design time and never read, so a later "simplify" pass reverses a deliberate choice. Prevention: the index imported into CLAUDE.md, path-scoped rules, the reviewer and the failure-analysis component citing record numbers, and the refactor shape's rule to read the index first.

Over-design of small work and under-design of migrations. Prevention: the sizing table at intake, and the conditional that migrations always get the full plan and a Fable reviewer regardless of how small the diff looks.

Design docs frozen at gate time. Code evolves, docs describe the plan from three weeks ago, and the next session trusts the docs. Prevention: the "reconciled at <commit>" line, the reconcile step, and the ground-truth precedence written into the skill: code and tests, then proof artifacts, then STATUS, then docs prose.

Cost envelope omitted "because it is early". Prevention: absence is a block; rough numbers with assumptions are fine, and the outfit example shows how a rough envelope changes the design (inference dominates, so caching and quotas move from nice-to-have to core).

## 8. Open questions and trade-offs

Zod-first versus OpenAPI-first contracts. Zod-first gives runtime validation and TypeScript inference for free on a Cloudflare backend and emits OpenAPI natively in v4; OpenAPI-first is language-neutral and reads better for a human. Recommendation: Zod-first when the backend is TypeScript (the common case for this owner), OpenAPI-first otherwise, and in both cases the same fixture, drift, and ownership rules. Verify that Swift OpenAPI Generator handles the emitted shapes cleanly before the gate; adjust shapes toward what generates well.

Reviewer on Opus or Fable by default. Opus at xhigh is the owner's tier for hard-but-bounded judgment and is likely enough for most designs; Fable costs about twice as much and is the tier for the hardest judgment. Recommendation: Opus by default, Fable for migrations and for greenfield systems with real data-loss or cost exposure, chosen per invocation by the orchestrator. Measure: if Fable reviews find blocks that Opus reviews missed on the same design more than occasionally, flip the default.

How much frontend design before code for a solo owner. Reference mockups through the `design` skill cost time and can anchor too early; going straight to SwiftUI with tokens and intent files is faster and the vision verifier still has something to grade. Recommendation: mockups for greenfield consumer apps and marketing sites, none for dashboards inside an existing system.

On-device versus server-side cut-outs. Two implementations of one feature is a real cost. Recommendation stands (device first, server fallback) pending the quality research item; if device masks are clearly worse on garments, flip to server-only and accept the privacy cost with a decision record.

GRDB versus SwiftData. GRDB wins on migrations and control; SwiftData wins on being Apple's default and on less code. Recommendation: GRDB, reconsidered only if the app is deliberately kept small.

D1 versus Postgres through Hyperdrive for the long term. D1's 10 GB ceiling per database and the absence of interactive transactions are the two cliffs; per-user data at this app's scale is far from both. Recommendation: D1 with a repository layer and the reversal cost recorded.

Where design artifacts live for skill-level learning. Project docs belong in the project repo; lessons about designing (a rubric dimension that keeps catching the same class of problem) belong in the skill's references. Recommendation: the failure-analysis component copies generalized lessons into `references/design-lessons.md`; project docs never leave the project.

How strict to be about implementers not touching the contract. Strict rules slow down small, obviously-correct additions; loose rules produce drift. Recommendation: strict, with a fast path: an implementer may add a fixture or a new optional response field through a contract-change step it runs itself, provided the drift check and both contract suites pass in the same commit; breaking changes go back to the architect.

## 9. Skill text candidates

Design gate, for SKILL.md:

> Design ends when several agents could implement in parallel without making different assumptions about the same thing. Before any implementer starts, the contract package must emit cleanly and match its committed document, every screen must have an intent file, every component must have at least one claim a test could make false, and a reviewer who did not write the design must have written a verdict file with no unresolved blocks. You do not approve your own design; if you and the reviewer disagree twice, record both positions in a proposed decision record and proceed with the reviewer's position.

Sizing, for SKILL.md:

> Size the design to the scope. A bug fix gets a diagnosis note in STATE and no design documents. A small feature gets a one-page change design and a contract delta with fixtures. Anything that adds storage or an external dependency gets the backend design sections that change, a decision record per non-default choice, and a review. A greenfield system or a migration gets the full set. When in doubt, write the proposed decision record and defer; do not resolve decisions implementation does not need yet.

Contract as the seam, for `references/contracts.md`:

> The contract is data that no implementation owns. Write it during design as a package of schemas, an operation table, and fixtures; emit the OpenAPI document from it and commit the emitted file; generate the client on one side and the validators on the other. Implementers consume the contract and never edit it while implementing. A contract change is its own step: update fixtures, regenerate both sides, run both contract suites, commit once. When an implementer finds a gap, the request is "add a fixture for case X", not an edit.

Production-faithful contract tests, for `references/contracts.md`:

> A mock that accepts anything proves the client and nothing else. Run backend contract tests inside the real runtime (for Workers, the Cloudflare Vitest plugin inside workerd, which enforces the same limits production does), and run a schema fuzzer against the running service. On the client, decode every fixture through the generated code before any network exists, then hit the mock server for flows, then hit staging for truth. Of every fake, ask where it is kinder than the real thing, and write the answer into the test plan.

Design intent for vision verification, for `references/frontend-design.md`:

> Record intent so a verifier can grade it. Tokens live in one JSON file and the platform token file is asserted equal to it by a test. Each screen has an intent file whose "Must be true" list contains only statements a screenshot or an accessibility tree can confirm: how many filled accent buttons are visible, what the empty state contains, which text sizes appear, whether the grid changed columns at a Dynamic Type size. Put taste in the layout prose. Keep accepted screenshots as baselines next to the intent files, so the next comparison is against the last accepted state, not against memory.

Backend design order, for `references/backend-design.md`:

> Write the backend design in this order and write "not applicable because" rather than skipping a section: context, components, data model with row budgets and platform limits, contract conventions, auth model, failure semantics per write path, idempotency, observability with the three questions an operator asks at 3 a.m., cost envelope with assumptions and a kill switch, environments, deployment, rollback and the schema compatibility rule it forces, scaling cliffs in the order they will be hit, security boundaries and the personal-data deletion path, claims, research to verify, open decisions.

Failure semantics, for `references/backend-design.md`:

> For every write path, state what the client sees on success, on timeout, and on partial failure; whether a retry is safe and why; what compensation runs; and what is left behind if compensation also fails. This is the section a reviewer reads first. If a path has no row here, it is not designed yet.

Decision records, for `references/decisions.md`:

> Write a decision record when you chose between real options with lasting consequences, used a beta feature on the critical path, overrode a default, accepted a risk the pre-mortem raised, or changed a contract. One file per decision under docs/decisions, numbered, never edited after acceptance; supersede instead. Each record states the reversal cost and the paths it applies to. Import the index into CLAUDE.md and add a path-scoped rule so anyone touching those paths loads the records. Read the index before simplifying anything.

Independent review, for `references/design-review.md`:

> The reviewer is an agent that did not write the design, given file paths and not summaries, with read-only tools and one verdict file to write. It scores simplicity, boring technology, single source of truth, failure handling, security boundaries, scaling cliffs, vendor lock-in, testability, cost, operability, and data lifecycle from 0 to 2, and it cites the section behind every score. A zero on failure handling, security, or testability blocks. A review that finds nothing wrong with a large design is itself a finding; rerun it asking for the three weakest points.

Pre-mortem, for `references/design-review.md`:

> After scoring, date a paragraph six months from now and state that the project failed. List at least six causes spanning data loss, cost, platform limits, auth, abandonment, vendor change, operations, and integration drift. For each, name the design element that permits it, how it would be detected and whether the design already detects it, the mitigation and its cost, and whether to mitigate, accept, or write a decision record. Discard any cause that does not name a mechanism. Resolve the top three by probability times damage before the gate opens.

Claims, for SKILL.md:

> Every component names its behavioral claims during design as plain sentences of the form "when X, the system Y", each one something a test could make false. The claims table links each claim to its refuting test and its status rung. A claim without a test does not pass Scaffold; a claim whose test runs only in a harness kinder than production does not pass Local Proof. Design documents are the plan; code and tests are the truth; when they disagree, fix the document in the reconcile step and update its "reconciled at" commit.

Cost envelope, for `references/backend-design.md`:

> Put numbers in the cost envelope even when they are rough: assumptions in a table, unit prices with URLs, monthly totals at launch scale, one-year scale, and a lucky scale, the line that dominates, and the switch that caps it. An absent envelope blocks review. In systems that call a model, inference usually dominates by an order of magnitude or more, and that fact should move caching, compact prompts, and quotas from nice-to-have into the core design.

Existing products, for SKILL.md:

> For a feature on an existing product, extract before you design. Read the existing design system into tokens, reuse existing components in the intent files, and write a one-page change design that names the existing endpoints and queries the feature uses, any new query with its index and read cost, and the contract delta. Do not write a second architecture; do not write a second design system.

Migrations, for SKILL.md:

> For a migration, the design is a parity-and-cutover plan: inventory the existing behavior from tests, logs, and traffic; define the target's contract; plan a shadow or dual run with a comparison harness; define the cutover switch and the switch back; plan data reconciliation and decommission; record every behavior deliberately dropped. Review on the strongest model with a mandatory pre-mortem, because migration failures hide in headers, timeouts, and defaults the old system normalized silently.

Consulting design later, for SKILL.md:

> Implementers load the design through the repository, not through your prompt alone: a path-scoped rule under .claude/rules names the design documents and decision records for each directory, and the decision index is imported into CLAUDE.md. Still name the sections an implementer must follow in its task prompt, because a rule that loads is not a rule that was read.
