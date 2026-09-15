# <One sentence: what failed, observed and not interpreted>
Status: open
Trigger: <one trigger name from the list in the comment below>
Detected: <ISO UTC> by <role> via <what surfaced it>
Got past: <the gate that should have caught this, or none existed>
Timebox: <minutes or turns for Investigate, or none for fix and operate>

<!-- Trigger is one of green-check-failed, verifier-rejection, false-assumption,
repeated-workaround, check-relaxed, incident, eval-regression, budget-overrun, or, for a failure of
drive's own process, one of the process-failure classes in references/lessons.md: premature-done,
gamed-test, symptom-patch, lost-context, wrong-assumption, tool-misuse, spec-gap, classifier-block,
missing-environment, flake-misread, thrashing, parallel-misalignment, scope-creep. A process failure
also names the mechanical control that should have stopped it. One file per failure event at .drive/investigations/<YYYY-MM-DD>-<slug>.md. Status moves
open → diagnosed → verified → fixed → distilled, or ends closed-no-lesson; "open (timebox expired)"
and "verified (live check deferred)" are allowed. Each stage closes only with its minimum record, and
each close adds a Gate log line. A mechanism is a line, a limit, an ordering, a race between two
named operations, or an environment difference; "flaky", "tooling", "environment", and "the model
misunderstood" are places to look, not causes. For a live incident or a Live Proof that failed after
Local Proof, append the sections from templates/postmortem.md. -->

## Fail
- Observed: <exact error text, command, exit code, and environment, pasted>
- Expected: <the behaviour that should have happened>
- Reproduction: <command or test path, and deterministic or n of m runs>

## Investigate
- Shared premise: <!-- the one assumption every earlier fix or workaround for this failure made, and the observation that tests it; none when no fix was tried -->
- Candidate causes, each with the observation that separates it from the others:
  1. <candidate cause> · separated by: <observation>
  2. <candidate cause> · separated by: <observation>
  3. <candidate cause> · separated by: <observation>
- Observations and what they eliminated: <what was run and what it ruled out>
- Mechanism: <the named mechanism>

## Verify
- Prediction: <a second instance the mechanism implies that nobody has observed yet>
- Check run: <command or test that exercises the prediction, with its output path>
- Revert check: <reverting the fix restores the failure: yes or no, with output path>

## Fix
- Change: <commit sha>
- Regression test: <test:<path>::<name>, the reproduction kept>
- Harness now enforces: <what the tests or harness now enforce that they did not, or nothing to enforce>

## Distill
- Candidate lesson: <entry heading in templates/lesson.md form, or none: the reason>
- Routing: <project-fact, domain-constraint, procedural-rule, owner-preference, skill-defect>
- Dedupe verdict: <distinct | same-as <heading> | narrower-than <heading> | broader-than <heading> | contradicts <heading>>
- Auditor verdict: <accepted | rejected at question <n>: reason>
- Written to: <path> at <commit>

## Gate log
- fail recorded <ISO UTC> <role>
