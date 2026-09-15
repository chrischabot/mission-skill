# PLAN · <goal slug>
goal: "<verbatim prompt>"

<!-- Written once by drive:planner, before any code. It is implementation-ready: a Sonnet implementer
builds each package from its section literally, and an Opus reviewer checks the change against it,
so every interface, data shape, behaviour, and test is written out. Nobody reviews the plan, and a
lean run writes no SPEC, DESIGN, or TESTPLAN file. Replace every angle-bracket line, and delete a
part that does not apply. -->

## Goal
<What will be true when the run ends, and for whom, in two or three sentences.>

## Rules to follow
<!-- Consulted before planning: .drive/LEARNINGS.md, references/lessons/general.md,
references/lessons/learned.md, and the Learned constraints of any domain file the stack names. Quote
each rule that applies with its source, or write "none apply". -->
- <the rule, verbatim> · from <file>

## Decisions
- <the decision> · because <one-line reason>

## Research
<!-- Only questions the repository cannot settle, each answered underneath with its source by the
one bounded lookup. Write "none" when there are none. -->
none

## Packages

### P1 · <name>
- depends on: none
- parallel with: <package ids, or none>
- files: <every path to create or change>
- acceptance: `<one command that must pass>`

**Interfaces.** <Each function, class, route, or command with its exact signature, argument and
return types, and the errors it raises or returns.>

**Data.** <Schemas, record shapes, and formats: field names, types, units, and which may be missing.>

**Behaviour.** <What each interface does, in order, with its edge cases (empty, missing, duplicate,
too large, malformed, concurrent) and the handling of each error at a boundary.>

**Tests.**
- `<test name>`: input <the input>; expects <the output or error>

## Order
<Which packages run together, and which wait for which.>

## Out of scope
- <what this run will not do>

## Blocked
- none
