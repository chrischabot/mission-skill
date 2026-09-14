# Assumptions · <mission name>

<!-- Template: skills/mission/templates/ASSUMPTIONS.md → .mission/ASSUMPTIONS.md (M+).
     Every gap found at intake becomes a row. Never delete a row: refuted assumptions stay with their evidence and the
     D-entry that changed course. A refuted assumption MUST update CHARTER.md/SPEC.md in the same change set. -->

Reversal cost: **L** = change in one task, no data or contract impact · **M** = rework of one component or document ·
**H** = platform, data ownership, money, irreversible external effect, public contract, or taste anchor.

Confirmation states: `CONFIRMED (human, <date>)` · `VERIFIED (F-NNN)` · `ASSUMED (unconfirmed)` · `REFUTED (D-NNN)`.

| ID | Assumption (statement of fact the mission relies on) | Reversal cost | Asked? (round/question) | Confirmation | How it will be verified (command, source, or human) | Affects (IDs / docs) |
|---|---|---|---|---|---|---|
| A-01 | <e.g. "v1 ships on iPhone only; no iPad layout"> | H | <R1 Q1> | <ASSUMED (unconfirmed)> | <human answer, or App Store device list in charter constraints> | <CHARTER §5, FRONTEND §1> |
| A-02 | <e.g. "Photos are ≤10 MB after on-device compression"> | M | no | <ASSUMED (unconfirmed)> | <measure 20 sample photos with `<command>`> | <API-001> |
| A-03 | <…> | L | no | <…> | <…> | <…> |

## Open high-cost assumptions (IDs only)

<A-01>

## Headless defaults applied

<!-- In a non-interactive run, every unanswered question's ★ default is applied, the row says ASSUMED (unconfirmed),
     and the mission continues unless a STOP condition applies. List the IDs here so the human can review them later. -->

<A-01 (default ★ "iPhone only"), …>
