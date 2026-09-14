# Task · <name> · Class: S

<!-- Template: skills/mission/templates/TASK-CARD.md. S missions only. Put this card in the PR description, or in
     .mission/TASK-CARD.md only if the work spans sessions. If any field needs more than two lines, reclassify upward
     (conventions §5) and write a CHARTER instead. -->

Profile (5 lines; replaces PROFILE.yaml for S — see references/shapes-and-scope.md):
- Shape: <BUG | FEA | UPG | …> · Scores: Breadth <0> Duration <0> Uncertainty <0–2> Coordination <0> → S
- Justification: <"one behaviour in one file; diff describable in one sentence">
- Traits present (evidence): <touches_auth (src/auth/session.ts:40) | none>
- Gate zero: <REPRODUCED | CONVENTIONS-MAPPED | …>
- Obligations: <AU-2, NT-1 | none>

Direction (verbatim): "<original prompt>"

**Goal:** <one sentence; an outcome, not an activity>

**Acceptance:** <observable result> — proven by `<command>` → <expected exit code / output line>

**Test first:** <test path::name, citing @req:<ID> if the repo has a registry> fails before the change, passes after.

**Must not change:** <files, behaviours, public APIs, tests>

**Assumptions:** <A-01 statement (reversal cost L/M) — or "none">

**Bound:** stop after <n> turns or <t> minutes; escalate if <stop condition>.

---

## Bug fix variant (replace the Acceptance/Test-first lines above)

**Repro:** env <versions, config, data> · steps 1. <…> 2. <…> · frequency <always | k in n runs> · evidence <log or
screenshot path>

**Current (defect):** When <condition>, <system> <incorrect behaviour>.

**Expected:** When <condition>, <system> SHALL <correct behaviour> — oracle `<test path::name>` fails before the fix.

**Unchanged (regression fence):** When <adjacent condition>, <system> SHALL CONTINUE TO <existing behaviour> —
oracle `<existing test>`.

**Root cause (verified, not guessed):** <file:line + evidence; filled after investigation>

**Proof of fix:** <command> exits 0; for flaky defects n ≥ ln(α)/ln(1−p) consecutive clean runs with state reset
(see references/debugging.md).

**Generalisation (for LESSONS-INBOX.md):** <class of bug; rule to consult next time — or "none">
