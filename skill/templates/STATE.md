# STATE · <project> · <goal slug>
status: running
phase: intake
next: <one imperative sentence naming the real next action>
updated: <ISO UTC>
commit: <short sha>
session: <session id>
model: <model · effort actually running>

<!-- Volatile working memory, rewritten (not appended) at every phase gate and before every stop;
150 lines at most. updated comes from `date -u +%Y-%m-%dT%H:%M:%SZ` run at the rewrite, never from
memory. phase names the earliest plan line in GOAL.md not yet ticked, even when later work has
started; the rest of what is under way goes in next and In flight. A spend figure anywhere in this
file comes from a recorded total with its source (a headless result's total_cost_usd, /usage, or the
harness budget line), or says "not measured". status is running, verifying, blocked, stalled, done, stopped, or aborted. The
Stop gate lets a turn end only when: status is done or stopped and lint --final passes; status is
blocked, Blocked on begins with one of budget:, impossible:, destructive:, credentials:, payment:,
legal:, account:, two-diagnoses:, or soak: followed by the condition in words, and REPORT.md says
"Stopped because" (budget: counts only once the maker spawns reach GOAL.md's subagent budget or a
DECISIONS.md entry added since intake has a Decision: line that begins with Stop or Narrow and names
the budget, as in "Decision: Stop; the budget no longer covers the admin screen"; credentials: names
the secret, as in "credentials: CLOUDFLARE_API_TOKEN for the staging deploy", an uppercase name with
an underscore or ending in TOKEN, KEY, SECRET, PASSWORD, PAT, CREDENTIALS, or CERT, or a name in
backquotes or double quotes, never NONE or TBD); status is blocked on "launch preflight: <reason>;
relaunched as `<claude command>`" after drive.py preflight itself recorded a failure; status is
aborted with REPORT.md and a DECISIONS.md entry whose Decision: line begins "Abort;" or "Aborted;"
(the word, then punctuation or the end of the line, for example "Decision: Abort; the owner ended
the run"); status is stalled and the gate itself set it; or a
drive: agent, or a task whose id or whole command is written under In flight, is still running. On
resume, a stalled run writes REPORT.md and runs drive.py end; a blocked run whose condition cleared
appends one DECISIONS.md entry naming the evidence, then sets running. session is the session id,
never its name. Add "registry: <command>" to the header when the project already has
a requirements registry. Line shapes, one per section below:
  Verified facts:   - <fact>. Verified: <command or source and date>.
  Rules in force:   - <project rule>. Because: <reason>. From: <investigation or decision slug>.
  Open failures:    - <YYYY-MM-DD> <slug>: <symptom>. Repro: <path or command> | Observed: <n of m runs>. Next: <step>.
  Discoveries:      - <YYYY-MM-DD> · <file or area> · <problem noticed and not touched, or a premise that changed> · <reason>
  Workaround ledger: one table row per obstacle; at count 2 open an investigation and apply nothing.
  Boundary events:  - <ISO UTC> · <step> · <classifier category or tool refusal> · <action taken> · <result>
In flight names each running agent or background command with its report path, for example
"drive:verifier → export-keeps-totals (report at .drive/local/workers/verifier-1/report.md)". -->

## Resume here
Why: <one sentence>
Blocked on: none
In flight: none

## Verified facts

## Rules in force

## Open failures

## Discoveries

## Workaround ledger
| obstacle | workaround | by | when | count |
|---|---|---|---|---|

## Boundary events
