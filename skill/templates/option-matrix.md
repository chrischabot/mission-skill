# Option matrix · <decision in words>
frozen: <YYYY-MM-DD> · commit <short sha> · by <agent> · rules: references/research.md section 15
decision record: <DESIGN.md decision heading or record path, once written>

<!-- For a choice that is expensive to reverse: a datastore, auth provider, hosting platform, sync
model, public API style, build versus adopt, or a new core dependency. Written to
.drive/research/options-<slug>.md. Fill "Frozen before scoring" and commit it before any scorer
starts; changing it afterwards needs a DECISIONS.md entry and fresh scores from both scorers. The
two scorers, a fresh drive:architect and a fresh drive:investigator spawned in one message, each
write their own scoring table to their own output path and see neither the other's scores nor the
orchestrator's preference. Every score cites evidence (a research slug, a probe output, or a
repository path); a score without evidence counts as 1. At S, replace this file with three lines in
RESEARCH.md: the options, the choice, and why. Delete guidance comments as sections fill. -->

## Frozen before scoring
Problem: <what must be decided, and which claims depend on it>
Constraints: <owner, platform, and policy limits that bind every option>
Options:
- <keep what exists, when something exists>
- <option>
- <option>

### Gates
<!-- Pass or fail. A failed gate removes the option before scoring. -->
| gate | evidence required |
|---|---|
| <runs on the required platform and version> | <research slug or probe output> |
| <licence compatible with the project> | <licence file at the pinned version> |

### Criteria
<!-- Three to six criteria, weights summing to 100, anchors written now and not after scoring. -->
| criterion | weight | how measured | 1 means | 3 means | 5 means |
|---|---|---|---|---|---|
| <criterion in words> | <weight> | <evidence that decides it> | <anchor> | <anchor> | <anchor> |

Benchmark plan: <workload, data, metric, warm-up, five or more runs, versions, deciding threshold>

## Probes
<!-- One per leading option whose riskiest unknown reading could not settle, run by drive:investigator
in a scratch directory within its timebox. Probe code is never merged. -->
| option | riskiest unknown | timebox | result | output path |
|---|---|---|---|---|
| <option> | <question reading could not settle> | <hours> | <what the probe showed> | <probe output path> |

## Scores
<!-- Copied from the two scorers' files after both have written them. One column per criterion. -->
| option | scorer | gates | <criterion> | <criterion> | weighted total | evidence |
|---|---|---|---|---|---|---|
| <option> | drive:architect | <pass, or the failed gate> | <score> | <score> | <total> | <slugs and paths> |
| <option> | drive:investigator | <pass, or the failed gate> | <score> | <score> | <total> | <slugs and paths> |

## Disagreements
<!-- Any gate disagreement, or two scores more than one point apart on a criterion. A fresh
drive:auditor rules from both rationales. Write "none" when the scorers agreed within a point. -->
| option and criterion | first score and reason | second score and reason | ruling | deciding evidence |
|---|---|---|---|---|

## Choice
Chosen: <option>, because <the two strongest reasons, with evidence>
Rejected: <option: the deciding reason>
The result flips if: <the weight or assumption whose change reverses it>
Reverse the decision when: <a measurable trigger>
