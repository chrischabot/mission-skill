# DECISIONS · <project> · mission: <one-line goal>

<!-- Template: skills/mission/templates/DECISIONS.md → .mission/DECISIONS.md (M+). Append-only ADR-lite.
     Owner: orchestrator (after a decision gate, or when logging a default taken on the user's behalf).
     Record EVERY: design choice with real alternatives, waiver (gate PASSED-WITH-WAIVER(D-id)), model downgrade or
     profile change, scope cut or requirement demotion, task cancellation (CANCELLED(D-id)), spec change after freeze,
     class downgrade, autonomous-mode sign-off, deviation from an existing repo convention.
     Irreversible choices also get design/adr/ADR-NNN.md; the D-entry links it.
     To change a decision: add a new entry with "Supersedes: D-NNN" and add "Superseded-by" to the old index line.
     Never edit a past decision's body. Keep the index ≤25 lines; move older index lines to archive/decisions-index.md.
     Mirror each index line into STATE.md "## Decisions index". -->

## Index
<!-- - D-NNN <title> · <accepted|superseded-by D-NNN|rejected> · <YYYY-MM-DD> -->

<!-- Entry format (copy below the last entry, uncommented):

## D-NNN · <title>
- Date: <YYYY-MM-DD> · Status: <proposed|accepted|superseded-by D-NNN|rejected> · Kind: <design|waiver|downgrade|scope-cut|demotion|cancellation|spec-change|convention-deviation|sign-off>
- Decider: <agent · model @ effort> · Approved by: <orchestrator | human (<date>) | autonomous default (notify)>
- Context: <what forced the decision; cite O-/F-/FND-/A- ids>
- Options considered:
  1. <option>: <cost, risk, reversal cost>
  2. <option>: <…> ✅
  3. Deliberately NOT <tempting option>: <why>
- Decision: <option n, one sentence>
- Consequences: <what gets harder or easier; follow-up tasks T-NNN>
- Verification: `<command or check that shows the decision holds>` · Level: <local-run|ci|staging|production|doc-source>
- Revisit when: <measurable trigger>
- Supersedes: <D-NNN | —> · ADR: <design/adr/ADR-NNN.md | —>

-->
