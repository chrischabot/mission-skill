# memory_delta (end of every worker return)

<!-- Template: skills/mission/templates/memory-delta.md. Paste the "Instructions for the worker" section and the block
     skeleton into every brief (templates/brief.md → Return format). Workers NEVER edit .mission/STATE.md or STATUS.md;
     the orchestrator merges this block by ID (references/memory-and-lessons.md P5) and runs memory-lint.sh.
     Use temporary ids new-1, new-2 … for new entries; the orchestrator allocates F-/H-/R-/O-/L- ids. -->

## Instructions for the worker

1. End your return with exactly one `<memory_delta>` block. Empty lists are fine; a missing block is not.
2. `facts_add` ONLY for claims backed by a command you ran (quote the salient output line) or an artifact path with a
   commit SHA. Anything you reasoned out but did not check goes under `hypotheses_add` with a discriminating check.
3. Every failure you hit that took more than one retry goes under `failures_add` with a runnable repro.
4. If new evidence conflicts with a fact or rule you were given, say so under `supersede` or `contradictions`; never
   quietly work around it.
5. List every rule or lesson ID from your brief that you actually applied in `rules_cited`.
6. `lesson_candidates` only for a technique that would help in a *different* repository, one line each.
7. `tasks` reports your own view of the task state; only the verifier's verdict flips a task to PASSED.
8. No secrets, tokens or customer data anywhere in the block: name the secret, never its value.

## Block skeleton

```text
<memory_delta>
facts_add:
  - id: new-1
    claim: "<one-sentence claim>"
    evidence: "`<command>` → `<salient output line>`"   # or "<artifact path> @ <sha>"
    level: <local-run|ci|staging|production|doc-source>
    scope: "<where it holds: component, env, version>"
    recheck_by_days: <90 default | 30 toolchain | 14 production/infra>
    supersedes: <H-NNN|F-NNN|none>
hypotheses_add:
  - id: new-2
    claim: "<claim>"
    for_failure: <O-NNN|new-3|none>
    check: "`<command>` ; <this claim predicts X, the alternative predicts Y>"
hypotheses_falsified:
  - id: <H-NNN>
    evidence: "`<command>` → `<output line>`"
failures_add:
  - id: new-3
    symptom: "<verbatim error or observable>"
    repro: "`<command>`"
    observed: "<…>"
    expected: "<…>"
    blast_radius: "<users/data/components affected, or unknown>"
supersede:
  - id: <F-NNN>
    by: <new-1>
    evidence: "<why the old fact no longer holds>"
contradictions:
  - fact: <F-NNN>
    observation: "<what you saw>"
    evidence: "`<command>` → `<output line>`"
rules_cited: [<R-NNN>, <L-NNN>]
lesson_candidates:
  - "<imperative technique> · applies when <…> · origin <O-NNN or task>"
tasks:
  - id: <T-NNN>
    state: <IN-PROGRESS|VERIFYING|FAILED(iter n)|STALLED|BLOCKED(<reason>)>
    evidence: "`<command>` → `<output line>`"   # or a logs/ path
</memory_delta>
```

## Example (filled)

```text
<memory_delta>
facts_add:
  - id: new-1
    claim: "Dashboard widgets register via the default export of src/widgets/registry.ts"
    evidence: "`rg -n 'registerWidget' src` → src/widgets/registry.ts:14"
    level: local-run
    scope: "apps/web dashboard, main @ 3f2c1ab"
    recheck_by_days: 90
    supersedes: none
hypotheses_add:
  - id: new-2
    claim: "Slow dashboard render is an N+1 fetch in useWidgetData"
    for_failure: none
    check: "`pnpm test perf/widgets --reporter=json` ; N+1 predicts fetch count = widget count + 1, batching predicts 1"
hypotheses_falsified: []
failures_add: []
supersede: []
contradictions: []
rules_cited: [R-002]
lesson_candidates: []
tasks:
  - id: T-009
    state: VERIFYING
    evidence: "`pnpm test apps/web/widgets` → 12 passed"
</memory_delta>
```
