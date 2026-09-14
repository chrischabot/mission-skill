# Backend design · <system>

<!-- Template: skills/mission/templates/design/BACKEND.md → .mission/design/BACKEND.md (L/XL; M only if the change
     touches data ownership or an external boundary). Record trade-offs, not an implementation manual. If there are no
     genuine alternatives, delete this doc and write a task list in PLAN.md. Keep under ~20 pages; split beyond. -->

Links: CHARTER.md · SPEC.md (domains <API, DATA, SEC, …>) · ADRs: design/adr/ · Contract file: <openapi.yaml |
packages/contracts> · Status: draft | reviewed | approved

## 1. Context & scope (objective facts; not requirements)

<What exists, what this system adds, trust boundaries touched.>

## 2. Goals / non-goals

Charter G*/NG* apply. Design-level non-goals: <e.g. "no offline write queue in v1">

## 3. System context diagram

```text
<clients> ──HTTPS──▶ <this system> ──▶ <third parties>
                   (trust boundary: <…>)
```

## 4. Components and ownership (exactly one owner per record, schedule and side effect)

| Component | Responsibility (one) | Owns (records, schedules, external side effects) | Does NOT own |
|---|---|---|---|
| <photos-api> | <accept, store, delete photos> | <Photo rows, R2 objects, delete side effect> | <outfit composition> |

## 5. Platform limits that bound the design (each with a source URL and access date)

| Limit | Value | Source (URL, accessed) | Design consequence |
|---|---|---|---|
| <limit> | <value> | <URL, YYYY-MM-DD> | <consequence> |

Cloudflare backends MUST include at least these rows (values as verified by the source lane; re-verify before relying):

| Limit | Value | Source | Design consequence |
|---|---|---|---|
| D1 max database size (Paid) | 10 GB, cannot be increased | https://developers.cloudflare.com/d1/platform/limits/ | archive or shard (per tenant/user) before <n> rows |
| D1 concurrency | single-threaded per database (≈1,000 qps at 1 ms queries) | same | keep queries short; batch large UPDATE/DELETE |
| D1 queries per Worker invocation (Paid) | 1,000 | same | no N+1 loops in a request |
| D1 bound parameters per query | 100 | same | chunk bulk inserts |
| Store fit | KV eventually consistent config/sessions · R2 large objects, no egress fees · Durable Objects coordination and strongly consistent per-key state · D1 relational read-heavy · Queues background jobs | https://developers.cloudflare.com/workers/platform/storage-options/ | per-entity store table in §6 |
| <Workers CPU time, request body size, R2 object size, Queue batch size> | <look up> | <URL> | <…> |

## 6. Data model

| Entity | Store | Owner | Key & indexes | Retention | PII? | Why this store |
|---|---|---|---|---|---|---|
| <Photo metadata> | <D1> | <photos-api> | <photo_id; (user_id, created_at)> | <until user deletes> | <yes> | <relational queries by user> |
| <Photo bytes> | <R2> | <photos-api> | <users/<id>/<photo_id>> | <same as metadata> | <yes> | <blobs, no egress fees> |

### State machines (every multi-step lifecycle)

| Entity | States | Legal transitions (event) | Rejected transitions (requirement ID) | Terminal |
|---|---|---|---|---|
| <Photo> | <uploading, stored, deleting, deleted> | <uploading→stored (upload complete); stored→deleting (delete request); deleting→deleted (object + row gone)> | <deleted→stored (DATA-0NN)> | <deleted> |

## 7. API contracts (sketch trade-off-relevant parts only; the contract file is the source of truth)

| Method & path | Auth scope | Request / response schema ref | Idempotency key | Errors (codes) | Rate limit | Pagination / versioning |
|---|---|---|---|---|---|---|
| <POST /v1/photos> | <user> | <contracts#/Photo> | <Idempotency-Key header> | <400, 401, 413, 429, 503> | <n/min> | <n/a; /v1 prefix> |

## 8. Key flows (sequence per P1 journey)

<J1: client → API → D1 → R2 → response; note where each failure in §9 can occur.>

## 9. External calls, failure modes, idempotency and retry

| Boundary | Failure (timeout, 5xx, partial write, duplicate delivery, quota) | Detection | Response (retry policy, backoff, max attempts, fallback) | Idempotent how | Req ID | Fixture |
|---|---|---|---|---|---|---|
| <R2 put> | <timeout> | <exception > 5 s> | <retry 3× exp. backoff, then 503 + orphan sweep> | <object key = photo_id> | <API-0NN> | <r2_timeout_stub> |

## 10. Security & privacy

Threat model (assets, actors, entry points) · authn/authz at the final dispatch boundary · secrets handling · all input
as untrusted data · PII inventory · retention and deletion (personal images: deletion path and deadline) · audit log.

## 11. Observability & operations

Logs / metrics / traces · health checks · alerts with thresholds · runbook stubs · deploy and rollback commands.

## 12. Cost model

| Driver | Unit price (source URL) | Expected volume | Monthly estimate | Ceiling and behaviour at ceiling |
|---|---|---|---|---|
| <R2 storage> | <…> | <…> | <…> | <…> |

## 13. Alternatives considered (≥2, genuine)

| Option | Summary | Decisive trade-off | Verdict |
|---|---|---|---|
| A <chosen> | <…> | <…> | chosen (ADR-NNN) |
| B <…> | <…> | <…> | rejected because <…> |

## 14. Open questions

[NEEDS CLARIFICATION: <question> · owner · default · blocks <ID>]

## 15. Test strategy hooks (for TEST-PLAN.md)

IDs needing fakes: <…> · contract tests: <…> · failure fixtures: <…> · live canaries (PENDING-LIVE): <…>
