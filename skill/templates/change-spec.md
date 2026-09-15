# <Change name> · change spec
Version: <YYYY-MM-DD> · shape: <feature | move/refactor | move/upgrade | publish> · size: <S|M|L|XL> · baseline: <baseline_sha> · latest review: <.drive/reviews/<file> | none yet> · changes: <count>

<!-- Written by drive:architect for a feature, a change to an existing library, CLI, or data pipeline,
a refactor, an upgrade, or a site. Rules: references/spec.md. Under 800 words; at S keep only What
changes, Must not change, and Requirements, under 300 words. For move/refactor and move/upgrade the
Requirements section holds no new behaviour: wanted new behaviour is a separate feature sub-goal.
For a site, this file holds only behavioural claims (forms, search, feeds); positioning, site map, and
page briefs live in .drive/content-plan/. Delete every guidance comment before the spec gate. -->

## What changes and why
<!-- Three to five sentences: the outcome a user or caller sees, and why now. -->

## Where it lands
<!-- Read from the code, never guessed. Cite .drive/how-it-works.md where archaeology ran. -->
- Files and modules: <paths>
- Interfaces and contracts touched: <route, schema, event, exported symbol, command, with where each is defined>
- Data touched: <tables, stores, or files, each marked read or write>

## Blast radius
<!-- Copied from .drive/how-it-works.md at the spec phase (at S, from STATE.md Verified facts). The
score chooses the discipline in references/shapes/feature.md: small as written; medium adds goldens on
shared contracts and a flag; large re-classifies to move/migration. drive:architect fills Safe because; the severe tester receives
it as a claim to refute. -->
Score: <small | medium | large>, because <entry points and external consumers counted>

| change point | depends on it | how found | covered by real tests | risk if it breaks |
|---|---|---|---|---|
| <path or symbol> | <callers, consumers, jobs, other repositories, configuration> | `<grep or search command>` | <test path, or none> | <what a user or operator would see> |

Safe because: <the one fact that keeps every dependant above working, in one sentence> · proved by <test:<path>::<name> | `<command>` with its output path | unproven>

## Dialect
<!-- The three nearest existing examples of what this change adds, copied from .drive/how-it-works.md.
New code copies their shape. -->

| aspect | pattern to follow | nearest examples |
|---|---|---|
| file placement and naming | <pattern> | `<path>`, `<path>`, `<path>` |
| error handling and validation | <pattern> | `<path>` |
| logging and configuration access | <pattern> | `<path>` |
| test location and naming | <pattern> | `<path>` |

## Must not change
<!-- The load-bearing section. Behaviours, contracts, performance characteristics, and data that stay
exactly as they are. Each entry is a claim heading with the check that catches a regression. A refactor
or upgrade is mostly this section. Use the existing suite where it already guards the claim; add a
characterization test captured from the current code where it does not. -->

### <Invariant as a claim in three to eight words>
Guarded by: <test:<path>::<name> that exists today | characterization test to add, captured at <baseline_sha>>
Measured baseline: <value with unit and command, for a performance invariant | not applicable>

What would prove this wrong

**<Regression scenario title>**
Given <state>. When <trigger>. Then <the unchanged outcome>.

## Requirements
<!-- New or changed behaviour only. Copy per requirement. The heading slug is the STATUS key. -->

### <Claim in three to eight words>

<One paragraph of intent.>

**<Scenario title, at most ten words>**
Given <state>. When <trigger>. Then <observable outcome>.

**<Scenario title>**
Given <state>. When <trigger>. Then <observable outcome>.

What would prove this wrong

**<Refuting scenario title>**
Given <state>. When <trigger>. Then <the outcome a plausible wrong implementation would not produce>.

Failure behaviour: <what the user sees and what the system does when a dependency fails>.

## Non-functional deltas
<!-- Only what this change affects, as numbers: a new hot path's budget, new data's retention and
deletion, a new permission's purpose, a bundle or binary size ceiling. -->
- <Budget with number, unit, and how it is measured>.

## Constraints
- <Owner, platform, or policy constraint with number>. <URL> · checked <YYYY-MM-DD> · research: <ledger slug>
- Kinder stand-in: <system or limit> is not enforced by <local double>; required: <real-semantics test or live check>.

## Done means
<!-- The end-to-end proof: the command or flow that demonstrates the change against the running
system, and the highest rung reachable here. -->
- Proof: `<exact command or flow>` against <local runtime | deployed environment>.
- Highest rung: <Local Proof | Live Proof | Operational>, because <live means, from GOAL.md>.
- The pre-existing suite at <baseline_sha> still passes with no test deleted, skipped, or loosened.

## Threat model
<!-- At size S when `auth` or the security surface list applies; at M and above it lives in DESIGN.md
section 14. Format and rules: references/security.md section 2. Delete otherwise. -->

## Assumptions

### We assume <the decision, as a plain claim>
Because: <the facts or preferences that drove it>.
Instead we could have: <the strongest alternative>.
To overturn: say "<sentence>". Before <milestone> this costs <cost>; after it costs <cost>, because <reason>.
Status: assumed <YYYY-MM-DD>

## Risks
- <Risk>. Trigger: <what would confirm it>. Response: <what the run does>.

## Changes
- <YYYY-MM-DD> · <heading words affected> · <what changed and why> · invalidates: <keys demoted, tests to re-run> · decision: <DECISIONS.md entry | none>
