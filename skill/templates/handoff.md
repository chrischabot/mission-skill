# Handoff · <unit>

I'm working on <larger task> for <who>. They need <what the verified result enables>. With that in mind: verify every claim below against the scope, run the validation commands yourself, and try to refute each claim.

goal: <the goal line from GOAL.md, quoted>
repository root: <absolute path; run every command as cd <root> && <command>>
skill directory: <absolute path of the drive skill, for references/ and templates/ named below>
mode: `<standard | close check | final-audit checklist | refutation | mechanism confirmation | blind re-grade | instrument audit | claims audit | docs smoke test | telemetry-only diagnosis | operate observation | plan review>`
round: <n>/<K>
pre-fix sha: `<for a fix, the commit before the fix, which you export yourself with git archive; otherwise none>`
frozen: `<yes or no>` · range base `<sha for drive.py freeze check --base and drive.py guard --base>`
rubric: .drive/rubrics/<shape>.md at <commit sha that froze it>
spec: <path and section: SPEC.md, HUNT.md brief, MIGRATION.md invariants, or RESEARCH.md>
previous gaps: <path to the prior round's verdict.json, or none>
output: templates/verdict.schema.json · proof directory .drive/proofs/<key>/r<n>/

<!-- Built by the orchestrator from files only. Never paste a maker's transcript, summary, report
prose, honest_gaps, self-assessment, or any assertion that a claim holds; never add an opinion of
quality, urgency, or remaining budget. One "### <claim key>" block per claim. -->

## Claims
### <claim key>
Claim: <claim words from STATUS.md>
What must be true: <the spec's What would prove this wrong scenario>

## Scope
range: <base sha>..<head sha>
checkout: <absolute checkout path>
owned paths: `<the package's ownership globs, or none>`
changed files:
- <path from git diff --name-only on the range>

## Validation
build: `<exact build command, or none>`
typecheck: `<exact typecheck command, or none>`
lint: `<exact lint command, or none>`
tests: `<exact full-suite command, or none when GOAL.md's probe records no suite>`
live: `<exact live check command, or none>`

## Evidence inputs
- <test path, severe: test, or capture to re-run, as an input and never as proof>

## Lessons that apply to this task
- <rule heading verbatim from the maker's brief, or none>

## What to return
Write the verdict JSON that follows templates/verdict.schema.json to the proof directory above with a Bash heredoc (or to the one .drive/reviews/ path this handoff names for its mode), and save each command's output there with tee. Your final message is the status line, that path, and the counts; it never carries the JSON. Report every finding you observe, each with its confidence and severity, including ones that look minor; filtering happens in a later step. Treat evidence inputs as things to re-run, never as proof. When a claim cannot be settled, mark it unverifiable or refuted, not holds. Give each conclusion with the command output or file line that supports it. Name the surface you verified on (for example xcuitest+simctl or playwright). Label every number with its source.
