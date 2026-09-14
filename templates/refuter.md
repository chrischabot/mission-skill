# Refuter brief · <FND-surface-NN> · surface <surface> · round <N>

<!-- Template: skills/mission/templates/refuter.md (references/review.md R4, Procedure B5).
     Used for every candidate blocker/major before it reaches the maker. The refuter MUST NOT be the reviewer that raised
     the finding. Default agent `mission-verifier`; concurrency, data integrity or auth → `mission-reviewer`;
     UNVERIFIED on a blocker → re-run on `mission-critic`. The brief contains the finding and the artifact, never the
     reviewer's transcript or the maker's reasoning. Output is appended to .mission/reviews/<surface>-refutations.md and
     the verdict is copied into the finding's `refutation` block. Delete this comment before sending. -->

## Prompt

```text
ROLE: Refuter. A reviewer claims the defect below. Try to DISPROVE it using the actual code, tests and executable
checks. You succeed equally by confirming or by refuting. Agreeing without reproduction is failure; dismissing without
a cited guard is failure.

CLAIMED FINDING (verbatim from .mission/reviews/<surface>-findings.md)
<finding YAML: id, severity, class, location, claim, construction, evidence, expected, observed>

ARTIFACT: <path>@<sha> (read-only). Scratch tests are allowed only in the throwaway worktree <.mission/tmp/refute/<FND-surface-NN>/>
that this brief provides, never in the reviewed checkout; remove it before returning.
EVIDENCE BUNDLE: <test files, gate outputs, schema/migration files, config relevant to the location>

PROCEDURE
1. Restate the claim as a testable proposition: "If <precondition>, then <observable wrong outcome>."
2. Try to reproduce it: run the smallest check that would show the outcome. Prefer executing over reading.
3. Look for guards the reviewer may have missed: upstream validation, schema constraints, unique indexes, triggers,
   types, config, middleware, retries with idempotency keys.
4. Decide:
   CONFIRMED  - you reproduced it, or the construction holds with a cited file:line for every step
   REFUTED    - you found the guard, or the reproduction shows correct behaviour (cite it)
   UNVERIFIED - you could neither reproduce nor refute within budget; say exactly what would settle it
5. If CONFIRMED, check the severity against the taxonomy (blocker: violates a MUST, loses or corrupts data, security
   exposure, artifact fails its purpose, gate evidence false · major: wrong behaviour on a supported path, overstated
   completion claim · minor · nit) and say whether it should be kept, raised or lowered, with the reason.
6. If the finding concerns code the current change did not touch, say so (pre-existing: true).
7. If you hit a safety refusal, stop: status BLOCKED-SAFETY, verdict UNVERIFIED, reason "refusal". Do not rephrase.

OUTPUT: YAML only, no preamble, as your whole reply (this format takes precedence over your agent file's return
format). The orchestrator appends it to .mission/reviews/<surface>-refutations.md.
```

## Output schema

```yaml
finding_id: <FND-surface-NN>
round: <N>
refuter: <mission-verifier | mission-reviewer | mission-critic>
status: <DONE | BLOCKED(<reason>) | BLOCKED-SAFETY>
commit: <sha>
proposition: "If <precondition>, then <observable wrong outcome>."
verdict: <CONFIRMED | REFUTED | UNVERIFIED>
evidence: "<commands + observed output, or file:line quotes for each step / the guard>"
guards_checked:
  - "<file:line> <what it guards, and whether it applies>"
severity_check: <keep | raise:<blocker|major> | lower:<major|minor|nit>>
severity_reason: "<one sentence; required unless keep>"
pre_existing: <true | false>
settle_by: "<UNVERIFIED only: the check that would decide it>"
scratch_cleaned: <true | false>
```

## Orchestrator rules for the result

- CONFIRMED → the finding blocks (if blocker/major after `severity_check`) and goes to the maker.
- REFUTED → disposition `REFUTED` citing this evidence; the maker never sees it as work.
- UNVERIFIED → `type: question` for the orchestrator; cannot block. On a blocker, re-run once on `mission-critic`.
- `severity_check` changes apply only with `severity_reason`. Reviewer and refuter disagree on facts → `CONTESTED`
  (review.md Procedure C).
- Sample 1 in 3 blocker refutations for a blind re-refutation by `mission-reviewer`; one false refutation → all blocker
  refutations on `mission-reviewer` for the rest of the mission.
