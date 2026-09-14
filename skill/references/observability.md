# Observability and the Operational rung

Read this file at intake when a deliverable will run without a person watching, at design before
any telemetry is written, before you claim Operational on any STATUS row, and when a soak begins. It
decides when Operational is in scope, what telemetry a run must build (on-call questions, structured
events, trigger stamps, metrics, alerts, a health endpoint, runbooks), how that telemetry is proven
by forcing failures rather than by reading code, where the evidence is saved, and what to refuse.
Domain files add platform gates, such as the Cloudflare file's operational gates; a domain gate adds
to this standard and never replaces a part of it.

## 1. When Operational is in scope

Operational means Live Proof plus evidence that something will notice a break and that the break
can be diagnosed. On STATUS.md it needs the Live Proof evidence set plus an `ops:` token, and only a
verifier's verdict moves a row there.

The per-shape targets in `references/definition-of-done.md` section 3 decide scope; this table
applies them.

| Situation | Operational target |
|---|---|
| `build` whose goal says it must run in production: a service, a scheduled job, a queue consumer, a webhook receiver, a pipeline | one row per service or job, such as `failures-in-the-export-job-are-noticed-and-diagnosable` |
| `fix/incident` | a row claiming a recurrence of the symptom alerts and can be diagnosed |
| `move/migration` | the new path reaches Operational before decommission; the soak rule applies |
| `operate` whose goal includes staying healthy | the observe phase proves the changed state with this standard |
| A domain file adds rows | as that file says |
| `feature`, `publish`, `report`, refactor, upgrade, a library, a CLI run by a person | not a target unless the goal says the result must stay healthy in production; the report says so in one line |

Create the Operational rows at intake with `live: y`, because targets are fixed then. A target found
later is added as a reclassification. Removing one, or accepting Live Proof in its place, needs a
DECISIONS.md entry in the same commit. A run with Operational rows is not Done until they are
Operational or the decision is recorded.

## 2. On-call questions first

Before writing any telemetry, write the two to four questions someone will ask when this breaks.
Every log event, metric, trace, and alert must answer one of them; a signal that answers none is
removed. Write them in DESIGN.md's `## 8. Operations` section; for a shape without DESIGN.md, write
them under an `## Operations` heading in HUNT.md, MIGRATION.md, or the operate plan named in GOAL.md.

```markdown
## Operations
service: export job · Operational row: failures-in-the-export-job-are-noticed-and-diagnosable
| question | signal | query that answers it | alert |
|---|---|---|---|
| Did last night's export run, and for which trigger? | `export_run_finished` event | <exact log query by event and time window> | none |
| When an export fails, which dependency failed and why? | `export_run_failed` with `dependency` and `error_code` | <exact query by correlation id> | page: failures > 0 in 30 min |
| Is the storage dependency slower than its baseline? | latency histogram `dependency="storage"` | <exact p95 query> | ticket: p95 > recorded baseline x 2 for 15 min |
```

Use metrics to detect a problem, traces to locate it, and logs to explain it.

## 3. Structured events and the correlation id

- Emit one structured object per event, never interpolated prose. Every event carries a stable
  snake_case `event` name that describes what happened (`export_run_failed`), `level`, a UTC
  timestamp, the correlation id, `trigger` (section 4), the deployed version, and for outcomes
  `outcome`, `duration_ms`, and an `error_code` from a fixed set.
- Levels mean one thing each: `error` an invariant broke and someone may need to act; `warn` degraded
  but handled (a retry succeeded, a fallback served); `info` a significant business event; `debug`
  off in production.
- Create the correlation id at the boundary where work enters: the request, the scheduled tick, the
  queue message, the CLI invocation. Accept an inbound id only from a trusted upstream, and only after
  checking its format and length, since it is input. Propagate it through outbound headers, queue
  metadata, workflow parameters, and child process environments, and return it in a response header
  so a smoke test can capture it.
- For external calls, log metadata only: the endpoint template, status, latency, attempt number, and
  opaque identifiers.
- Allowlist fields. Never log whole request or response bodies, authorization headers, cookies,
  secrets, tokens, or personal data beyond an opaque user id (`references/security.md` section 8).
- Mark synthetic traffic from smoke tests and proofs with `synthetic: true` so it can be filtered out
  of product numbers and found quickly by the verifier.

## 4. Stamp which trigger started the run

When more than one entry point can start the same work (a scheduler, a replay endpoint, a webhook, a
manual command, a test harness), their log lines are otherwise interchangeable, and attributing one
depends on outside records that may be gone. Set `trigger` where the run starts, from a fixed set
such as `schedule`, `http`, `queue`, `webhook`, `replay`, `manual`, `smoke`, and propagate it with the
correlation id across every boundary. A worker never infers it. Do not call the field `source`, which
collides with the common log schema's network fields. When drive triggers a job now through the
system's own tools, the run carries `trigger: manual` or `smoke`, so the proof shows which run it was.

## 5. Metrics with bounded labels

- For every endpoint and every external dependency, record rate, errors, and duration. For queues,
  pools, and workers, record utilization, saturation (queue depth and age), and errors.
- Record latency as a histogram and read p50, p95, and p99. Never track an average alone.
- Take labels only from small fixed sets: route template, method, status class (`5xx`, not `503`),
  dependency name, trigger. Never use user or tenant ids, emails, raw URLs, request ids, or error text
  as labels; those belong in events.
- When the platform has no metrics product, the counting query over structured events is the metric.
  Save that query with its output as the evidence.

## 6. Symptom alerts that someone receives

- Alert on symptoms users or the owner feel: error rate, p95 or p99 latency, queue age, a scheduled
  run that did not finish, a health check failing from outside. Causes (CPU, memory, one restart) go
  on dashboards, not in alerts.
- Use two severities: `page` for user-facing harm now, `ticket` for degradation to handle this week.
- Take every threshold and duration from a stated objective or a measured baseline recorded with its
  command and date. With no objective, measure today and record it; never guess a number.
- Every alert has a destination the owner already receives, found in the project's configuration or
  its existing alerting. If no such destination exists, name setting one up as an owner step; the
  row stays at Live Proof with that exact step, because an alert whose delivery was never seen proves
  nothing.
- Every alert links to its runbook (section 8). An alert whose response is "ignore it" is deleted.
- If the platform has no native alert for a symptom, use an external prober of the health endpoint
  and say so in the evidence.

## 7. The health endpoint

Every deployed service exposes `GET /health`. It returns the deployed version (commit sha or the
platform's version id), the build time, an overall status, and one entry per critical dependency
with its status and check latency, each check under a short timeout. It answers 200 only when every
critical dependency passes and 503 otherwise. It performs no writes, needs no secret in the request,
and exposes no hostnames, configuration values, stack traces, or credentials. A health endpoint that
always answers 200 is a finding.

Work with no HTTP surface emits a heartbeat instead: one `<job>_run_finished` event per run with the
version, trigger, and outcome, and a saved query that returns the time of the last successful run.
Native apps follow their domain file.

## 8. The runbook minimum

Store runbooks where the project keeps them, or `docs/runbooks/<alert-name>.md`. Each is at least four
lines, and a step is added only when the first check alone cannot decide:

```markdown
# Runbook: <alert name>
Means: <what the symptom is and its two most likely causes>
First check: <the exact query or command, and how to read its result>
First action: <the rollback or mitigation, quoted from the undo recorded in DECISIONS.md>
Who: <the owner, or the channel the alert reaches>
```

A runbook used during an incident is corrected before the incident is closed.

## 9. Prove the telemetry

Telemetry is code and can be wrong. Reading the instrumentation proves nothing; each item below is
performed and captured. Run it against the environment GOAL.md's `live means:` names. Induce failures
in production only through paths confined to the synthetic smoke identity, with no user impact;
where that is impossible, use a staging environment that shares the production log sink, metric
pipeline, and alert routes, and record every difference under "environment differences".

1. **Find a forced failure by correlation id.** Cause one failure through the system's own tools:
   point a staging dependency at a closed port, revoke the smoke identity's access to a test resource,
   or send a request the code must reject. Capture the correlation id from the response or the run
   output, query the log sink by that id, and save the result. Confirm the events are structured, carry
   `trigger` and version, and contain no secret.
2. **See the series.** Send synthetic traffic and confirm each metric series appears with the expected
   labels and plausible values. Where tracing exists, follow one request across every service with no
   broken span.
3. **Fire a copy of each alert once.** Never edit a production alert rule: a lowered threshold pages
   whoever is on call, and a crash before the restore leaves it lowered. Record the undo (deleting
   the copy) first. Create a copy of the alert with the same query and condition, a threshold the
   synthetic traffic crosses, a filter to the synthetic identity, and a test destination instead of
   the real one: a test channel the project's alerting configuration already has, or a webhook
   receiver the run deploys under the synthetic identity and reads back. Capture delivery from the
   alerting system's notification log or the test destination (never the owner's personal inbox
   through a browser), check the runbook link resolves, delete the copy, and read the configuration
   back to prove the copy is gone and the real rule is unchanged. Prove the real rule's route
   separately by reading its configuration: it must name the destination the owner receives. When
   no test destination can exist, record under "Not proven" that delivery was not exercised; the row
   stays at Live Proof with that gap named.
4. **Diagnose an induced failure from telemetry alone.** You inject a fault the diagnoser is not told
   about and write it to `.drive/local/ops-<key>-fault.md`, which no brief quotes. Spawn a fresh
   `drive:verifier` in its telemetry-only diagnosis mode. Its handoff gives the repository root as an
   absolute path, only the symptom as a user would report it, the on-call questions, the telemetry
   query commands written as `cd <root> && <command>`, and the output path
   `.drive/proofs/<key>/r<n>/diagnosis.md`, and it forbids reading source files. The verifier writes
   the failing component, the cause, and the queries it ran to that file. Compare its answer to the
   sealed record; a
   match passes, a miss is a failure event that improves the telemetry. Undo the fault and confirm
   `/health` is green.

A fault injection switch that untrusted callers can reach in production is a security finding. Keep
injection to configuration you control, synthetic identities, or staging.

## 10. Save the evidence

Save each round under `.drive/proofs/<key>/r<n>/`: `ops.md`, the captured query outputs as `*.txt`,
and every command in `commands.log`. `proof.json` records the environment. The STATUS token is
`ops:.drive/proofs/<key>/r<n>/ops.md`. A dashboard or console URL is evidence only beside a saved
capture, because what a URL shows changes.

```markdown
# ops · <key> · round <n>
environment: <live | staging> · target: <route or job> · version: <id served by /health> · commit: <sha>
environment differences: none | <each way this environment differs from production>

## On-call questions → captured answers
| question | query (commands.log line) | capture |

## Forced failure found by correlation id
fault: <what, how> · correlation id: <id> · capture: <file> · fields structured: yes/no · secrets present: no

## Series
| metric | labels seen | capture |

## Alerts fired
| alert | copy threshold and test destination | fired at | delivered at, via | runbook link ok | copy deleted at | read-back capture, real rule unchanged |

## Diagnosis from telemetry alone
symptom given: <text> · diagnosis: .drive/proofs/<key>/r<n>/diagnosis.md · injected fault: <copied from the sealed record after the verdict> · match: yes/no

## Health
capture: <file> · version matches: yes/no · dependency checks: <names>

## Not proven
- <item> · why · the step that would prove it
```

The verifier reviews `ops.md`, re-runs at least the correlation-id query, and supports Operational in
its verdict only when every section is captured or its gap is named under "Not proven" with a
decision.

## 11. Soak checks decide and act

A soak exists only for a property with no signal to trigger now; anything synthetic traffic, a forced
failure, or a fired alert can show is proven now instead. The rules for scheduling are in
`references/long-running.md` section 11. Before the soak starts, write its decision rule into
DECISIONS.md: the checks and their queries, the thresholds taken from recorded baselines, what holds
the stage and for how many checks, and what rolls back through which recorded undo. Each check runs
the queries, writes its captures under `.drive/proofs/<key>/`, and then advances, holds, or rolls back
on its own. A check that only reports is a queue for the owner and is a defect. While a soak is open
its row stays below Operational and the run is not Done.

## 12. What not to do

| Refuse | Do instead |
|---|---|
| Logging secrets, tokens, cookies, whole bodies, or personal data | allowlisted fields and opaque ids |
| User ids, request ids, raw URLs, or error text as metric labels | fixed label sets; the detail goes in events |
| Alerts with no destination anyone receives, or never fired | a known destination and one test-fire with delivery captured |
| Cause alerts paging while the error rate is unwatched | symptom alerts; causes on dashboards |
| Thresholds picked by feel | a recorded objective or a measured baseline |
| Operational claimed from reading instrumentation code | the four proofs in section 9 |
| A production alert rule edited to prove it fires, or an alert copy left in place | fire a copy routed to a test destination, delete it, then read the configuration back |
| A health endpoint that always returns 200 or exposes configuration | dependency checks, 503 on failure, no internals |
| A soak or a schedule standing in for a check you can run now | force the failure and fire the alert today |

## 13. Excuses and rebuttals

| Excuse | Why it fails |
|---|---|
| "Logging can come after it works." | After means the first incident, which is the most expensive moment to find out you cannot see. |
| "More logs give more visibility." | Unstructured volume slows diagnosis; a few named events that answer the questions beat thousands of lines. |
| "The alert is configured, so it works." | Configuration is not delivery; until it fires once and arrives, nobody knows it reaches anyone. |
| "I read the code; the error is logged." | Instrumentation is code with bugs; only the forced failure found by its id shows the line exists. |
| "A user id label makes debugging easier." | It makes the metrics store fail; per-user detail belongs in events. |
| "The diagnosis test is unnecessary; I know the cause." | Knowing the cause is exactly why you cannot run it; a fresh agent with only telemetry shows whether an on-call person could. |
| "We will watch it for a few days." | Watching is waiting on a schedule; synthetic traffic, a forced failure, and a fired alert prove it today. |

## 14. Red flags

- A shape whose target is Operational (section 1) with no Operational row and no decision explaining why.
- Telemetry written before any on-call question, or a signal that answers none.
- Log lines built by string interpolation, or events without a correlation id.
- One log fed by a scheduler, a webhook, and manual runs with no `trigger` field.
- A metric labelled by user, request, URL, or error text; latency tracked only as an average.
- An alert with no runbook, no destination, or no captured delivery.
- An `ops:` token that points at a URL with no saved capture.
- A diagnosis whose handoff named the injected fault, or whose diagnoser read source files.
- A production alert rule edited during a proof, or an alert copy still configured after the round.
- A soak check that reports but never advances, holds, or rolls back.
- A secret, token, or personal detail in a captured log line.
