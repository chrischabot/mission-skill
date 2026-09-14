# ADR-<NNN>: <decision title>

<!-- Template: skills/mission/templates/design/ADR.md → .mission/design/adr/ADR-<NNN>.md (Nygard format).
     REQUIRED for choices expensive to reverse: datastore, auth model, API style, client platform, sync model, public URL
     structure, token set, legacy-owner cutover. Also log a one-line D-<NNN> entry in DECISIONS.md that points here.
     Never edit an accepted ADR's decision: supersede it with a new ADR and set this one to "superseded by ADR-<NNN>". -->

Status: proposed | accepted | rejected | deprecated | superseded by ADR-<NNN> · Date: <YYYY-MM-DD>
Deciders: <agent roster name + model ID; human if confirmed> · Decision entry: D-<NNN>

## Context

<Forces and constraints; requirement IDs affected (<API-003, PRIV-001>); platform limits with source URLs; evidence
(spike result, measurement, doc quote). "I tried it out and it works" is valid evidence when the spike is linked.>

## Decision

<What we will do, in active voice: "We will store photo bytes in R2 and metadata in D1.">

## Alternatives

| Option | Decisive trade-off | Why not chosen |
|---|---|---|
| <B> | <…> | <…> |
| <C> | <…> | <…> |

## Consequences

- Easier: <…>
- Harder: <…>
- New requirements or limits introduced: <IDs>
- Reversal cost: <L | M | H> — <what reversal would take>
- Revisit trigger: <measurable condition, e.g. "D1 database > 5 GB" or "second client platform added">
