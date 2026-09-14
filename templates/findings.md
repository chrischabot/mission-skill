# Findings · surface <surface>

<!-- Template: skills/mission/templates/findings.md (references/review.md F1–F2, Procedure B4–B5).
     File: .mission/reviews/<surface>-findings.md — one file per surface, one "## Round <N>" section per round, each
     holding one YAML block per reviewer. Finding IDs FND-<surface>-NN continue across rounds and are never reused or
     renumbered; the orchestrator assigns final NN when appending (reviewers may use temporary ids new-1, new-2).
     Reviewers return the review header, findings and summary; the orchestrator copies each refuter's verdict
     into `refutation` (full notes: .mission/reviews/<surface>-refutations.md). S missions keep the same fields as a
     table in the PR description or TASK-CARD.md. Replace the example entries; keep the field names. -->

## Round <N>

```yaml
review:
  surface: <surface>                  # stable surface id, e.g. checkout-api
  round: <N>                          # 1 = initial; >1 = scoped re-review (C3)
  cap: <1 | 2 | 3 | 4>                # C2 by class; security-sensitive surfaces >= 3
  scope: "<initial | remediation diff <base>..<head> + callers of <symbols> + constructions of <FND-ids>>"
  lens: <SPEC | DESIGN | CORRECTNESS | TEST-QUALITY | SECURITY | PERFORMANCE | UX | FACT-CHECK | RELEASE>
  persona: <none | hostile-input-author | crash-at-worst-time | skeptical-auditor | first-time-user | maintainer-in-a-year | strongest-counter-argument>
  reviewer: <roster agent, e.g. mission-reviewer>
  commit: <sha>
  unit_size: "<changed LOC | one surface: name>"
  evidence_bundle:
    - <.mission/logs/T-NNN/test.txt>
    - <tests/path/to/test_file>
findings:
  - id: FND-<surface>-NN               # e.g. FND-checkout-03
    type: finding                      # finding | question (no reproduction or construction -> question; cannot block)
    severity: blocker                  # blocker | major | minor | nit
    pre_existing: false                # true -> never blocks this change (R6)
    lens: CORRECTNESS
    class: <short-defect-class>        # e.g. zero-row-write-as-success; reused across rounds for the C4 recurrence check
    instrument: false                  # true if about tests, mutation targets or registry claims (C5 share)
    rubric_item: <none | R1..R12>      # spec/design lens only (templates/spec-review-rubric.md)
    requirement: <REQ-ID or none>
    location: "<src/webhooks/settle.ts:88 | SPEC.md#section | URL>"
    quote: "<verbatim line or sentence at the location>"
    claim: "<one sentence: what is wrong>"
    construction:                      # steps precise enough to become a test; each step cites file:line
      - "<Reservation already settled (src/cost/reservations.ts:41 sets state=settled)>"
      - "<Replay webhook -> settle() runs UPDATE ... WHERE state='held' (settle.ts:80), changes=0>"
      - "<settle.ts:88 returns ok:true without reading changes>"
    evidence: "<npx vitest run tests/scratch/replay.test.ts -> exit 1; 1 failed: expected ok:false, got ok:true>"
    expected: "<replay returns ok:false, or idempotent success with the audit row unchanged>"
    observed: "<ok:true and a second audit row>"
    impact: "<double audit record; reconciler counts the settlement twice>"
    fix_class: "<check affected-row count; add replay test>"
    parent: <none | FND-surface-NN>    # set on sub-findings (F4)
    related: [<FND-surface-NN>]        # earlier findings of the same class or construction
    refutation:                        # filled by the orchestrator from the refuter note (R4); blocker/major only
      verdict: <CONFIRMED | REFUTED | UNVERIFIED | none>   # none = not refuted (minor, nit, question)
      by: <mission-verifier | mission-reviewer | mission-critic>
      evidence: "<reproduced with the scratch test above | guard at file:line>"
      severity_check: <keep | raise:<level> | lower:<level>>
  - id: FND-<surface>-NN
    type: question
    severity: minor
    pre_existing: false
    lens: CORRECTNESS
    class: <short-defect-class>
    instrument: false
    location: "<file:line>"
    claim: "<suspected problem>"
    evidence: "<what was looked at; what would settle it>"
    refutation:
      verdict: none
outside_contract:                      # F6: triaged by the orchestrator in the disposition log
  - location: "<file:line>"
    observation: "<what>"
    evidence: "<command + output, or quote>"
summary:
  blocker: <n>
  major: <n>
  minor: <n>
  nit: <n>                             # <= 5
  questions: <n>
  truncated: <true | false>            # true if more than max_findings existed
  clean: <true | false>                # true = no findings; a valid outcome (R3)
```

## Severity (conventions §4; review.md F2)

| Severity | Meaning | Blocks? |
|---|---|---|
| blocker | Violates a MUST, loses or corrupts data, security exposure, artifact fails its purpose, gate evidence false | Only if refutation CONFIRMED |
| major | Wrong behaviour on a supported path, missing required negative case, overstated completion claim | Only if refutation CONFIRMED |
| minor | Low-impact edge case, maintainability risk, weak but not wrong test | Never; never triggers a round |
| nit | Naming, style, comments; at most 5 per review | Never; never triggers a round |
| flag `pre-existing` | Defect in code the change did not touch | Never; DEFERRED with owner |
| type `question` | No reproduction or construction, or refutation UNVERIFIED | Never; orchestrator triage |
