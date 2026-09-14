# <Product name> · specification
Version: <YYYY-MM-DD> · shape: build · size: <S|M|L|XL> · latest review: <.drive/reviews/<file> | none yet> · changes: <count>

<!-- Written by drive:architect for a build. Rules: references/spec.md. Delete every guidance
comment before the spec gate. Requirements are claims; prose names them by their words; no numbered
identifiers anywhere. Budget: 1,500 to 4,000 words, 15 to 40 requirements. At size S, write under 300
words: What this is, the constraints that bite, and Requirements with their refuting scenarios. When
the goal bundles capabilities, `.drive/capability-map.md` is written first from
templates/capability-map.md. -->

## What this is
<!-- Five sentences: who it is for, the job it does, why it is worth building, what it is not. No
adjective a competitor could also claim. -->

## Goals and non-goals
Goals:
- <An outcome, not a feature. Three to six.>

Budget: the envelope in `.drive/GOAL.md`; scope flexes, the budget does not.

Non-goals:
- <Something that could reasonably be a goal> because <reason>.

## Users and jobs
<!-- One line per user type and job, with the situation and what success looks like. No personas. -->
- <User type>: <job in one sentence, with its situation and success condition>.

## Constraints
Given by the owner:
- <What it requires or forbids>.

Given by the platform:
- <Limit with number and unit>; <what it forbids or requires>. <URL> · checked <YYYY-MM-DD> · research: <ledger slug>

Given by policy or law:
- <Rule and what it requires>. <URL> · checked <YYYY-MM-DD> · research: <ledger slug>

<!-- A constraint without a ledger entry is labelled "decision, not fact" and has an assumption. -->

## Where the test environment is kinder than production
<!-- One line per external system or platform limit the code can reach. TESTPLAN.md's kindness
ledger carries the guard for each. -->
- <System or limit>: the local stand-in <permits what production forbids>. Required: a test against <the real runtime or a live check>.

## Requirements

<!-- Copy this block per requirement. Heading: three to eight words, a claim that could be false.
Its slug is the STATUS key. When `.drive/capability-map.md` exists, replace this section with one
"## Requirements · <module>" section per module, in build order, named exactly as in the map; every
`###` heading stays a claim. -->

### <Claim in three to eight words>

<One paragraph of intent: what the user or caller gets and why it matters.>

**<Scenario title, at most ten words>**
Given <state>. When <trigger>. Then <observable outcome>.

**<Scenario title>**
Given <state>. When <trigger>. Then <observable outcome>.

What would prove this wrong

**<Refuting scenario title>**
Given <state>. When <trigger>. Then <the outcome a plausible wrong implementation would not produce>.

Failure behaviour: <offline, denied, over quota, or partial: what the user sees and the system does>.

## Non-functional budgets
<!-- Numbers with units and the environment they are measured in. Delete a line only with a reason
recorded as an assumption. -->
- Performance: <p95 or cold start on the hot paths, with device or environment>.
- Cost: <ceiling per month at a stated usage level>.
- Offline and degraded: <what works, what degrades, what refuses>.
- Privacy and data: <what is collected, where, retention, verified deletion, and export>.
- Security: <authentication posture, with abuse cases next to use cases>.
- Accessibility floor: <targets, text scaling, labels, contrast, motion, with numbers>.
- Internationalisation: <posture from the first commit>.
- Observability: <what must be visible when it breaks, without a person tailing logs>.

## Success criteria
<!-- Three to seven. Each measurable by an agent, with a number or count, naming the requirements it
evidences. -->
- <Measurable outcome with number and environment>. Evidences: <heading words>; <heading words>.

## Threat model
<!-- At size S when `auth` or the security surface list applies; at M and above it lives in DESIGN.md
section 14. Format and rules: references/security.md section 2. Delete otherwise. -->

## Assumptions

### We assume <the decision, as a plain claim>
Because: <the one or two facts or preferences that drove it>.
Instead we could have: <the strongest alternative>.
To overturn: say "<sentence>". Before <milestone> this costs <cost>; after it costs <cost>, because <reason>.
Status: assumed <YYYY-MM-DD>

## Risks
- <Risk>. Trigger: <what would confirm it>. Response: <what the run does>.

## Glossary
<!-- Every noun used in a specific sense, defined once, so makers do not coin synonyms. -->
- **<Term>**: <definition in one sentence>.

## Changes
<!-- Empty until the spec gate has passed. One line per change, appended, never edited. -->
- <YYYY-MM-DD> · <heading words affected> · <what changed and why> · invalidates: <keys demoted, tests to re-run> · decision: <DECISIONS.md entry | none>
