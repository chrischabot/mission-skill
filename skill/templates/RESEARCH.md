# RESEARCH · <project> · <goal slug>

Read the status block before any phase that depends on an external fact or an unfamiliar part of
the code. Cite entries by slug and say what the entry means beside the slug. Procedure:
references/research.md.

## Status
updated: <ISO UTC>
blocking open questions: <n> (<slugs>)
answered: <n> · assumed pending refutation: <n> · stale: <n> · open conflicts: <n>
load-bearing verified facts graded: <n of m> · last grading: .drive/reviews/<date>-citations-<slug>.json
tools live this run: <tavily mcp | tvly | websearch | curl | playwright>; substitutions: <none | list>
spend: <agents> agents · <tool calls> calls · <credits> Tavily credits · about $<usd> of $<budget>

## Open conflicts
### <slug>: <the disagreement in words>
Side A: <claim> · source: <url with anchor> · read: <raw text via curl | tvly extract | rendered> · checked: <YYYY-MM-DD>
Side B: <claim> · source: <url with anchor> · read: <how> · checked: <YYYY-MM-DD>
Kind: factual | methodological | definitional
Blocks: <decision and file section> · Everything else proceeds.
Next check: <probe or source that would settle it> · by: <agent>

## Questions
### <slug>: <question in words>
Serves: <decision, and the file and section it lands in>
Tier: <S | M | L | XL> · Budget: <lanes, tool calls> · Spent: <tool calls>
Status: open | answered | assumed | stale | conflict
Class: verified fact | source claim | inference | unresolved conflict
Confidence: high | medium | low
Checked: <YYYY-MM-DD> (at <short sha> for codebase facts)
Re-verify by: <YYYY-MM-DD> · Re-verify when: <trigger>
Answer: <plain sentences>
Evidence:
- Primary: <url with anchor> · version: <from the lockfile> · read: <raw text via curl | tvly extract | rendered via Playwright> · quote: "<the supporting sentence>"
- Probe: .drive/research/probes/<slug>.<ext> → .drive/research/probes/<slug>.out · ran: <YYYY-MM-DD> against <scratch resource> · removed: <yes, how>
- Independent: <url> · independent of the primary because: <different origin>
Disconfirming: <terms searched and what was found, or "none found after <n> searches for <terms>">. Kinder locally: <where a local stand-in is kinder than the real system, or none>.
Would change the answer: <event or evidence>
Consumed by: <SPEC.md heading | DESIGN.md section | TESTPLAN.md test | STATE.md fact | page>
Grade: supports | contradicts | not found | not graded · <review path>

## Assumed pending refutation
- <slug>: <assumption>. Conservative branch: <what the design does meanwhile>. Refuting test: planned:<path>::<name>. Would change: <evidence>.

## Stale watch
- <slug>: checked <YYYY-MM-DD>; re-verify was due <YYYY-MM-DD> (or trigger "<trigger>" fired). Not citable as verified until re-checked.

## Source register
| Source | URL | Lane | Fetched | How read | Version or page date | Validator (ETag, Last-Modified, sha256) | Local copy |
|---|---|---|---|---|---|---|---|

## Evidence table (publish and report runs)
| Claim to publish | Slug | Class | Checked | Appears on |
|---|---|---|---|---|

## Attempt ledger
| Date | Change tried | Command | Baseline | Result | Run-to-run variance | Kept or reverted | Reason |
|---|---|---|---|---|---|---|---|

## Research log
- <YYYY-MM-DD> · <phase> · questions: <slugs> · lanes: <n> (<tool calls each>) · reconciled by: <agent, model> · grading: <n of m supported, downgraded slugs> · decisions unblocked: <list> · still blocked: <list> · empty lanes: <lane: terms searched> · freshness: <entries re-checked, moved to stale> · spend: <calls, credits, usd>
