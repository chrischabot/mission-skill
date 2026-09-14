# TEST-DISPUTE <n> · <YYYY-MM-DD> · task <T-NNN> · raised by <agent file, e.g. mission-worker>

<!-- Template: skills/mission/templates/TEST-DISPUTE.md (references/testing.md W-5, G-3). The maker fills sections 1–4
     and returns STATUS: TEST-DISPUTE instead of touching the test. The orchestrator appends the record to
     .mission/reviews/test-disputes.md, sets the task BLOCKED(test-dispute), and routes it to the original test author
     plus a reviewer who wrote neither the test nor the code. Only they fill section 5. Delete this comment. -->

## 1. Disputed test

- Test: `<path>::<test name>` (`<path>:<line>`)
- Cites: `@req:<ID>` · acceptance check `<AC-NNN>` · spec text: `<.mission/SPEC.md#<section>>` "<quoted requirement>"
- Frozen since: <commit sha of the freeze> · manifest entry present: <yes>

## 2. Claim (pick one)

- [ ] Contradicts the spec — the assertion demands behaviour the requirement does not state or forbids
- [ ] Impossible — no implementation can satisfy it together with <other test / requirement ID>
- [ ] Environment — depends on something unavailable here (<secret, device, network, service>)
- [ ] Implementation detail — asserts internals the spec leaves open (<which>)
- [ ] Flawed oracle — passes or fails for a reason unrelated to the requirement (<how shown>)

## 3. Evidence

- Assertion: `<path>:<line>` "<quoted assertion>"
- Conflict with: "<quoted spec line or other test>" (`<path>:<line>`)
- Command and output: `<command>` → exit <n> → "<salient line>" · log `<.mission/logs/<T-NNN>/<file>>`
- Minimal demonstration (if impossible/flawed): <input, expected per spec, what the test requires>

## 4. What I did and did not do

- Did NOT modify, skip, delete, rename, special-case or weaken the test, its fixtures or configs.
- Did NOT add test-only branches or fixture literals to production code.
- Work state: <branch/commit of partial work, what passes, what is blocked>
- Proposed resolution: <amend criterion in SPEC + registry | amend test | mark criterion UNVERIFIED(<reason>) until
  <env> exists | withdraw requirement>

## 5. Decision (test author + non-author reviewer only)

- Test author: <agent file> · reviewer: <agent file> · date: <YYYY-MM-DD>
- Verdict: <ACCEPTED | REJECTED | CONTESTED → orchestrator adjudication (high effort) or human>
- Reason with evidence: <spec quote, command output, file:line>
- If ACCEPTED: spec/registry change <commit> · D-entry <D-NNN> · test amended <commit> in a session with
  `MISSION_FROZEN_BYPASS=1` · manifest regenerated `frozen-manifest.sh write --force` <commit> · re-proven RED on base:
  <command → failing message>
- If REJECTED: evidence returned to the maker; task resumes at rung <mission-worker | mission-worker-high | …>
- Lesson candidate (spec gap, flawed oracle pattern): <L-NNN | none>
