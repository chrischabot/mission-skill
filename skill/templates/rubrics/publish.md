# Rubric · publish · <goal slug>
frozen: <ISO UTC> · commit <short sha> · copied from templates/rubrics/publish.md by drive:architect
applies to: <page, template, and claim keys>
deployed at: <production URL when in scope, otherwise the preview URL> (preview-only rows carry live n, and the report holds the promote command)
derived from: <path or URL of a known-good comparable site | none>

<!-- Fill every placeholder, delete trait rows that do not apply, and commit before the first draft or
build. Never edit during a verification loop. Each criterion reads: observation, oracle, refutation,
threshold. Measured thresholds come from .drive/CONSTRAINTS.md rows where they exist. A criterion that
cannot apply is reported as `rubric_gap:`. Rules: references/verification.md and
references/ui-verification.md. -->

## Standing floor
<!-- Always in scope. Never a rubric gap. -->

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| No weakened checks | no link check, accessibility run, or test skipped or loosened; no suppression added | `drive.py guard` exit 0; diff of check configuration over the range | a check disabled or a threshold lowered without a DECISIONS.md entry | blocking |
| Harness no kinder than production | local previews that differ from the deployed host (headers, redirects, base paths, caching) have kindness-ledger rows and a check on the deployed URL | TESTPLAN.md ledger | a page that works only on the local preview | blocking |
| No data loss | replacing an existing site kept an export of the previous deployment and a recorded rollback command | DECISIONS.md undo and export path | a replaced deployment with no rollback | blocking |
| Security holds | no secret, token, or private path in built assets or source maps; forms validate on the server | grep of the build output; form severe tests | a matched secret; a form accepting a hostile payload | blocking |

## Process

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Research before copy | every RESEARCH.md question the copy depends on was answered before its draft commit | `git log` order | a draft citing an entry answered later | should_fix |
| Captures by the reviewer | every `shot:` was captured by drive:ui-reviewer from the stamped build | findings.json and capture metadata against the build stamp | a capture from another agent or an older build | blocking |
| Values have sources | every score and timing names its tool, URL, and whether lab or field | reading | an unsourced or mislabelled number | blocking |

## User outcome

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| <Visitor's primary job> | a first-time visitor reaches <what the site exists to show or start> within <n> actions from the home page | ui-reviewer walkthrough on the deployed URL | over the action budget, or a dead end | blocking |

## Shape criteria

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Deployed build is this commit | the deployed URL (production when in scope, otherwise the preview) serves the build stamp of HEAD | `curl` of the stamp | a different stamp | blocking |
| Responsive | every template renders at 360, 768, 1280, and 1600 px with no horizontal scroll | captures plus `document.documentElement.scrollWidth <= innerWidth` | overflow at any width | blocking |
| Links intact | zero broken internal links; external links answer below 400 | `<crawl command>` output | an internal 404 (blocking) or a dead external link (should_fix) | as stated |
| No console errors | each route loads with no console error | browser console capture per route | any error | blocking |
| Accessibility | zero critical or serious axe violations on each template; keyboard reaches every control with visible focus | axe run; keyboard traversal test | a violation, or an unreachable control | blocking |
| Performance | Lighthouse performance and accessibility at or above the CONSTRAINTS.md rows on the deployed URL | `lhci` or DevTools audit, three runs, median | below the row (should_fix); below <hard floor> (blocking) | as stated |
| Statements are true | every factual sentence traces to a RESEARCH.md entry or a repository file | grader claim-trace table | an unsupported sentence | blocking |
| No evidence marker ships | no `NEEDS-EVIDENCE` marker remains; each became a verified claim or a removed sentence with a DECISIONS.md narrowing | `grep -rn "NEEDS-EVIDENCE"` over the content directory and the build output | any match, or a removed sentence with no narrowing entry | blocking |
| Product described as it is | every feature the copy describes exists and works as described | repository search and the documented commands | a described feature that is absent | blocking |
| Design contract met | ui-reviewer reports zero blocking and major findings, with the observation counts references/ui-verification.md section 7 sets | findings.json against `design/DESIGN.md` | a blocking or major finding, or a review below those counts | blocking |
| Not a template | no templated-default tell on a primary page, and the page is recognisable as this project without its logo | ui-reviewer penalty list | a tell on a primary page | should_fix |
| Copy works | controls say what happens; errors say what went wrong and how to recover; empty states invite the next step | ui-reviewer copy pass | vague control labels or apologetic, unhelpful errors | should_fix |
| Blog and docs sections work | the blog index lists posts and a post renders; a docs page renders with navigation; feeds and sitemap validate when present | walkthrough and validator output | a dead section or an invalid feed | blocking for a dead section; should_fix for a feed |

## Trait additions

| trait | criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|---|
| `prose-content` | Prose checklist | narrative pages pass the prose skill's checklist named in the writer's brief | grader reading against that checklist | a failed item on a primary page | should_fix |
| `api` | Forms and search behave | each form and search endpoint meets the backend endpoint criteria in references/verification.md | tests and live requests | a 5xx or an accepted malformed payload | blocking |
| `research-needed` | Freshness | no cited RESEARCH.md entry is stale | ledger dates against re-verify dates | a stale entry cited as verified | blocking |

## Amendments
- <ISO UTC> · <criterion added, removed, or reworded> · because <rubric gap or ruling> · DECISIONS.md <date>-<slug> · applies from <unit>
