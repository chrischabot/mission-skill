# Capability map · <project> · <goal slug>
written: <YYYY-MM-DD> at <short sha> · by: drive:architect (<model>)
checked: .drive/reviews/<date>-capability-map-<slug>.json · result: <clean | findings fixed>

<!-- Write this before SPEC.md for a build at M and above, or a feature at L or XL, when the goal
bundles capabilities: they have their own users or data, could ship and be verified separately,
or one could be cut without rewriting the others. Name modules in plain words and keep the names
for the whole run. Procedure: references/design.md section 3. -->

## Why this goal is several capabilities
<The trigger in a sentence: own users or data, separate proof, or cuttable>

## Modules
| Module | Responsibility | Owns (data, secrets, external connections) | Depends on | Provides contract to | SPEC.md section |
|---|---|---|---|---|---|
| <plain words> | <one sentence> | <list> | <modules, or none> | <modules, or none> | <heading> |

## Contracts between modules
| Provider | Consumer | What crosses | Specified in (provider's SPEC.md section) | Contract location |
|---|---|---|---|---|

## Build order
<module> → <module> → <module>

| Wave | Modules | Why this wave |
|---|---|---|
| 0 | shared schema, contracts, <foundation module> | everything else depends on them |
| 1 | <modules with dependencies only in wave 0> | <reason> |

## Checks
| Check | Result | Evidence |
|---|---|---|
| Dependencies point one way (no cycles; two modules needing each other were merged) | <pass or what was merged> | <grader file> |
| Each module can be verified without another module's implementation, contract fixtures aside | <pass or module> | <grader file> |
| Every contract lives in its provider's section | <pass or contract> | <grader file> |
| No data, secret, or external connection is owned by two modules | <pass or resource> | <grader file> |

## Cut line
<Modules that could be dropped without rewriting the rest, and what each removes>. Dropping one later requires a DECISIONS.md entry.
