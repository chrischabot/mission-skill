# Rubric · report · <goal slug>
frozen: <ISO UTC> · commit <short sha> · copied from templates/rubrics/report.md by drive:architect
applies to: <report path and claim keys>
questions: <the questions from GOAL.md, by their words>
freshness bound: <how old a source may be before it needs a note>

<!-- Fill every placeholder and commit before research lanes start. Never edit during a verification
loop. Each criterion reads: observation, oracle, refutation, threshold. Citation checks read raw text
(`curl -sL` or `tvly extract`), never a rendered summary. A criterion that cannot apply is reported as
`rubric_gap:`. Rules: references/verification.md and references/research.md. -->

## Standing floor
<!-- Always in scope. Never a rubric gap. For a report the floor applies to probes and to any code the
research wrote. -->

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| No weakened checks | no probe or citation check rewritten to agree with the draft; no source removed from the register after grading contradicted it | RESEARCH.md history over the range | a graded source removed, or a probe edited after its result | blocking |
| Local stand-ins named | every probe run against an emulator or local stand-in states where it is kinder than the real system | the ledger's "Kinder locally" lines | a probe result presented as the real system's behaviour | blocking |
| No data loss | probes ran against scratch resources that were removed afterwards, never against owner data | ledger probe lines with "removed" | a probe against a production resource, or a scratch resource left behind | blocking |
| Security holds | no credential, token, or private identifier appears in the report or the ledger | grep of both files | a match | blocking |

## Process

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Ledger before prose | every entry the draft cites existed in RESEARCH.md before the draft commit | `git log` order | a citation to an entry added afterwards | should_fix |
| Disconfirming search | each load-bearing entry records the search for contrary evidence | ledger "Disconfirming" lines | a load-bearing entry without one | should_fix |
| Grading ran | the citation grading file exists for this draft's commit | `.drive/reviews/<date>-citations-<slug>.json`, cited as `test:.drive/reviews/<date>-citations-<slug>.json::every citation resolves` | no grading file, or one for an older draft | blocking |
| Values have sources | every number names its source, date, and whether it is measured, estimated, or quoted | reading | an unsourced number, or an estimate presented as measured | blocking |

## User outcome

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| The owner can decide | each decision the goal names can be made from the report's recommendations and the evidence they cite | mapping of decisions to recommendation sections | a named decision the report does not equip | blocking |

## Shape criteria

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Every question answered | each question from GOAL.md has a section that answers it, not an adjacent question | question-to-section mapping | an unanswered question | blocking |
| Citations support their sentences | the cited source's raw text says what the sentence says, for every load-bearing citation and one in three of the rest chosen at random | drive:grader fetches raw text and quotes each graded source | a source that does not support its sentence | blocking |
| Kinds of claim labelled | verified fact, source claim, inference, and opinion are distinguishable for every assertion in findings | reading against the ledger classes | an unlabelled assertion, or opinion presented as fact | should_fix |
| Sources fresh | every source is dated; nothing older than the freshness bound is cited without a note; no stale ledger entry is cited as verified | ledger checked and re-verify dates | a stale entry cited as verified | blocking |
| Conflicts shown | every open conflict in RESEARCH.md appears in the report as a conflict | Open conflicts section against the report | a contested figure presented as settled | should_fix |
| Recommendations follow | each recommendation cites the findings that support it | reading | a recommendation with no supporting finding | blocking |
| Nothing material missing | the adversarial reader finds no source class, modality, or question the report should have covered | `.drive/proofs/<key>/r<n>/refutations.md` from the adversarial reader (a fresh drive:verifier), checked against the questions | an omission that changes a recommendation (blocking) or adds context (should_fix) | as stated |
| Prose reads as intended | the report passes the prose skill's checklist named in the writer's brief | grader reading against that checklist | a failed item in the summary or recommendations | should_fix |

## Trait additions

| trait | criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|---|
| `existing-code` | Codebase facts pinned | each fact about code names the commit it was checked at and still holds at HEAD | ledger sha against a re-check by the grader | a fact that no longer holds | blocking |
| `ai-llm` | Model facts from the source | model names, prices, and limits come from the provider's current documentation, not memory | citation check | an uncited or outdated model fact | blocking |

## Amendments
- <ISO UTC> · <criterion added, removed, or reworded> · because <rubric gap or ruling> · DECISIONS.md <date>-<slug> · applies from <unit>
