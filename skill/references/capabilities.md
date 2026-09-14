# Capabilities: which skill, tool, or CLI does each job

Read this file at intake, before planning, and again whenever you are about to delegate a job that
an installed skill, MCP tool, or CLI already does. It decides four things: what is present on this
host (the preflight), how each capability reaches the agent that needs it (the route), what to use
in each phase of each shape (the map), and what to do when something is missing (the fallbacks and
their status ceilings). Drive conducts installed capabilities; it does not paraphrase them into
worker prompts. Write your own procedure only where the map shows a gap or the preflight shows the
skill is missing. Before invoking any skill or tool, read the "Learned constraints" at the end of
this file for entries that name it.

Contents
1. Preflight
2. Invocation routes and the facts that decide them
3. The capability map
4. MCP tools per role
5. Overlapping reviewers and the capability behind each hardening step
6. Fallbacks, status ceilings, and the degradation rules
7. Condensed fallbacks (severe testing, frontend design, prose writing)
8. Delegation templates and the orchestrator's hardening commands
9. What drive never invokes
10. Learned constraints

## 1. Preflight

Run this capability preflight at intake right after `drive.py init` and `drive.py preflight` (the
launch check in `references/long-running.md` section 3), so it never runs at XS (which has no
`.drive/`) and never writes into a paused run that `init` is about to archive. Run it again at every
resume, because the tool surface differs between the Desktop app, the terminal, and a headless run
on the same machine. The orchestrator runs it; subagents never do.

1. Run `drive.py capabilities`, the state tool in the skill directory SKILL.md names. It writes
   `.drive/capabilities.json` with what Bash can see: each skill
   directory under `~/.claude/skills/` as `true`, `false`, or `"dangling"` (a symlink whose target is
   gone), plugin variants of a skill (`<plugin>:<name>`), and the CLIs `gh` (authenticated),
   `tvly`, `imagegen`, `xcodebuild`, `simctl` (a booted device), `wrangler`, `agent-browser`, plus
   `git:origin` and `git:baseline_sha`. A rerun rewrites the file and keeps only the recorded
   `git:baseline_sha`, so on every resume steps 2 and 3 merge the `mcp:` and `resolved:` keys again.
   The baseline is set once, at intake, and GOAL.md's probe block holds the canonical copy.
2. Run one ToolSearch call with exact names, because keyword searches were verified to miss tools
   that are present (a `+Claude_Browser` search found nothing in a session where the Browser pane
   was loaded) while `select:` returns every tool that exists, loaded or deferred, and silently
   omits names that do not:

   `select:mcp__playwright__browser_snapshot,mcp__chrome-devtools__lighthouse_audit,mcp__Claude_Code_iOS_Simulator__control,mcp__tavily-remote-mcp__tavily_extract,mcp__Claude_Browser__preview_start`

| Key to merge | Present when this schema comes back |
|---|---|
| `mcp:playwright` | `mcp__playwright__browser_snapshot` |
| `mcp:chrome-devtools` | `mcp__chrome-devtools__lighthouse_audit` |
| `mcp:ios-simulator` | `mcp__Claude_Code_iOS_Simulator__control` (Desktop app only) |
| `mcp:tavily` | `mcp__tavily-remote-mcp__tavily_extract` |
| `mcp:browser-pane` | `mcp__Claude_Browser__preview_start` (Desktop app only) |

3. Resolve the skills against your own skill listing, which is authoritative for what is invocable;
   the script only catches dangling links. Accept a plugin variant where the plain name is missing
   or dangling (`writing` or any `<plugin>:writing`; `deep-research` or `<plugin>:deep-research`).
   Merge `mcp:*` keys and `resolved:prose`, `resolved:deep-research` (the name that will actually be
   invoked, or `null`) into `.drive/capabilities.json` with a small Python edit, never by hand.
   A server the session reports as failed to connect counts as missing for this run; record its
   reason beside the key.
4. For every capability the map needs for this shape and these traits that is missing, look up
   section 6, apply the fallback and ceiling, and write the substitutions once into STATE.md under
   "Verified facts", one line each:
   `- Capability substitution: <missing> → <fallback>; ceiling <rung or none>. Verified: preflight <ISO date>.`
   Plan only with what the file shows as present. Do not stop to ask for anything to be installed.
   On resume, rewrite those lines only if the set changed, and say in one line what changed.

## 2. Invocation routes and the facts that decide them

| Route | How | Use it for |
|---|---|---|
| Orchestrator Skill tool | You invoke the skill in the main conversation | Skills that launch processes or plan workflows: `/run`, `workflow-authoring` |
| Preload | `skills:` in the agent file; full text is in context from the first turn | Method the role needs every time: `drive:researcher` gets `deep-research`; `drive:designer` gets `frontend-design`; `drive:severe-tester` and `drive:security-reviewer` get `severe-testing` |
| Named in the brief | The brief's first line: "Before you start, invoke the Skill tool with `<skill>`." | Knowledge this project needs and the role does not always need; only for agents whose tools include Skill (architect, implementer, writer, researcher, investigator, ui-reviewer, severe-tester, security-reviewer). Also `/simplify` to `drive:implementer` under a package brief and `/code-review` to `drive:security-reviewer` in its code-review mode, which keeps a tree edit and security findings out of your context |
| File path | An absolute path in the brief | A skill that is really a document, reference files a preload may not locate, and anything a read-only role needs: the reference file an installed skill ships (such as the `audit` skill's subsystem guide or the `google-dev-docs-style` review checklist) at the absolute path the preflight resolved, the cached guidelines at `.drive/local/ui/web-interface-guidelines.md` |

These facts were verified on Claude Code 2.1.263 and decide the routes:

- The Skill tool works inside subagents, and a subagent can invoke skills it was not given, so a
  read-only role must not have the Skill tool at all. `drive:verifier`, `drive:grader`, and
  `drive:auditor` run with Read, Grep, Glob, and Bash only.
- Preloads come from the skills installed on this host, not from drive's plugin: `deep-research`,
  `severe-testing`, and `frontend-design` do not ship with drive. A preload that is missing is
  silently absent from the agent, so the substitution line from section 1 step 4 is what tells the
  agent to follow section 7's fallback; put that sentence in the brief of every agent whose preload
  is missing.
- `skills:` preloads the full text of user, plugin, and bundled skills. A skill with
  `disable-model-invocation: true` (a user-only skill such as `refactor` or `/verify`) is silently
  absent when preloaded and refused when invoked. Never plan a step that needs one.
- A bundled orchestration skill changes behaviour with the tools of the agent that loads it:
  `/simplify` preloaded into an agent without the Agent tool becomes a single-pass inline edit, and
  with the Agent tool it fans out from depth two. Never preload an orchestration skill, and name only
  two, each to one role: `/simplify` to `drive:implementer`, where it runs as a single-pass edit of the
  brief's paths, and `/code-review` to `drive:security-reviewer`, which lacks the Agent tool, so the
  review runs without its finder fleet and is a narrower pass than the same command in the main
  conversation. Record that in the review file.
- A skill runs on the model of the agent that invokes it. From the orchestrator that is Fable, whose
  cyber classifier is most likely to decline a security review. So `/security-review` runs only
  inside `drive:security-reviewer` (Opus), which invokes the Skill tool with `security-review` after
  checking that the diff it will read covers the run (section 8). Never run it in your own context.
- `/code-review` with no level reuses the last level the user typed, even in an earlier session,
  and with no target reviews commits ahead of upstream, which is empty on a main branch that was
  already pushed. Always pass both: `/code-review <level> <baseline_sha>...HEAD`. Commit first; the
  range does not include uncommitted edits.
- `/security-review` reads the diff between the branch and origin's default branch, needs an
  `origin` remote, and takes no documented target. It hard-excludes denial of service, rate
  limiting, and several other categories, so its clean result is weak evidence on those.
- A preloaded skill that refers to `references/*.md` by relative path may not find them. Pass
  absolute reference paths in the brief whenever the skill has reference files.
- In a Workflow script, pass `agentType: 'drive:<name>'` so the agent's preloads come along; do not
  depend on the Skill tool inside `agent()` calls, which is unverified. Invoke
  `workflow-authoring` yourself before writing the run's first script.

## 3. The capability map

Routes: **orch** you invoke it; **pre** preloaded; **named** named in the brief; **path** passed as
a file path. Traits in parentheses narrow a row.

| Phase | Shapes | Skills (route) | MCP and CLI | Agents |
|---|---|---|---|---|
| intake | all | none | `drive.py capabilities`; ToolSearch probes; `git rev-parse HEAD` | orchestrator |
| archaeology | feature, fix, move, operate | `audit` reference (path) for bounded subsystem readers; whole-codebase `audit` (orch) only for move at L or XL | `gh run list`, `gh issue view` (fix, operate); `git log -S` | `drive:researcher` |
| research | build, publish, report; feature and move with `research-needed` | `deep-research` (pre); `tavily-dynamic-search` for large payloads, `tavily-research` for one cited synthesis, `tavily-crawl` for bulk docs (named) | Tavily MCP or `tvly`; WebSearch; `curl` for raw citation text | `drive:researcher`, several via Workflow; `drive:grader` checks citations |
| one-page lookup | any | none | `tvly extract --format text <url>` or `curl -sL`; quotation stored in RESEARCH.md | one researcher |
| spec | build, feature, move | `claude-api` (named, `ai-llm`) | none | `drive:architect` |
| design | build, feature, publish, move | `frontend-design` (pre, designer; `ui`); `dataviz` (named, any chart); `claude-api` (named to architect, `ai-llm`) | none | `drive:designer`, `drive:architect` |
| test-plan | build, feature, move | `severe-testing` (named, for claim, refutation, and oracle vocabulary in TESTPLAN.md) | none | `drive:architect` |
| decompose | build, feature, move | `workflow-authoring` (orch, before the first script) | none | orchestrator, `drive:architect` |
| inventory, characterize | move | `audit` reference (path) | project test runner | `drive:researcher`; `drive:severe-tester` writes characterization and parity tests |
| reproduce, diagnose | fix | `severe-testing` (named, verify rung) | `gh run view <id> --log-failed`; `git bisect` in a detached worktree under `${TMPDIR:-/tmp}` removed in the same step | `drive:investigator` |
| build, fix | build, feature, fix, move, publish | stack playbooks (named): `rust-refinement`, `vercel-react-best-practices`, `react-component-performance`, `claude-api`; `frontend-design` for new UI; `imagegen` for imagery (publish, marketing) | project toolchain, `xcodebuild`, `wrangler`, `imagegen` | `drive:implementer` |
| draft, docs | publish, report; docs phase of build, feature, move | prose skill from `resolved:prose` (named); `google-dev-docs-style` (named) for documentation pages; its review checklist (path) goes to the docs reviewer, never to the writer as a self-check | none | `drive:writer`; story mapping as a `drive:writer` call with `model: "fable"` for a substantial narrative; `drive:grader` checks doc claims and runs the style checklist |
| verify | all code shapes | `/code-review <level> <range>` (named to `drive:security-reviewer`; `existing-code`, and per milestone on build) | deterministic gates by Bash | `drive:verifier`; `drive:grader` for conformance; `drive:severe-tester` |
| harden: security | any with `auth`, or the surface list in `references/security.md` section 1 | `security-review` (invoked by the reviewer); `severe-testing` (pre) | read-only `git` | `drive:security-reviewer` |
| harden: UI, design-qa | `ui` on any shape; publish | `/run` (orch, to launch); `frontend-design` (named, taste lens); guidelines file (path) for web | Playwright MCP; Chrome DevTools MCP; iOS Simulator MCP or `xcodebuild` and `simctl`; Browser pane in Desktop only | `drive:ui-reviewer` |
| harden: simplify | build milestones, feature; move after cutover; never a fix | `/simplify <paths>` (named to `drive:implementer`) | none | `drive:implementer` under a package brief; `drive:grader` checks the test baseline |
| live-proof, deploy, cutover, execute, observe | build, feature, publish, move, operate | domain reference `references/domains/<d>.md` | the system's own MCP verbs or CLI; `gh run`; `Monitor` | `drive:verifier` |
| soak, waiting | move, operate | `loop` (orch) only for a condition with no signal | `Monitor` first | orchestrator |
| retro, final audit, report | all | none | `drive.py lint --final` | `drive:auditor`, or a fresh `drive:verifier` when the auditor is not required; orchestrator for the report |

Leave skills out where they do harm. No design skill on a fix: a visual regression is judged against
the previous screenshot and the existing tokens, never a new direction. `frontend-design` runs in
"distinctive" mode for build and publish, and in "match the existing design system" mode for a
feature on an existing product; the brief says which. No `deep-research` for a question one primary
page answers. No design, research, or simplify skills on operate or `fix/incident`. `imagegen` never
produces app screenshots or anything presented as a real capture.

## 4. MCP tools per role

| Role and job | First choice | Second | Without the Desktop app, or when absent |
|---|---|---|---|
| `drive:ui-reviewer`, web | Playwright MCP: accessibility snapshot, screenshots, scripted flows; isolated browser, headless-capable | Chrome DevTools MCP: `lighthouse_audit`, `performance_start_trace` and `performance_analyze_insight`, console and network detail | `agent-browser` CLI; else an `npx playwright` script whose screenshots the reviewer reads |
| `drive:ui-reviewer`, iOS | iOS Simulator MCP: `build`, then `control` with `launch`, `screenshot`, `inspect`, `tap`, `swipe` | none | `xcodebuild test` with an XCUITest target (queries and taps the accessibility hierarchy) plus `xcrun simctl io <udid> screenshot <file>` |
| `drive:ui-reviewer`, localhost preview | Browser pane (`preview_start`), Desktop only, localhost only | none | Playwright MCP |
| `drive:researcher` | Tavily MCP or `tvly` (search, extract, map, crawl, research) | WebSearch for breadth | `curl -sL` for page text; `tvly research`, `map`, and `crawl` need a login, so an unattended run records the cap and never starts `tvly login` |
| citation checks (`drive:grader`, `drive:verifier`, `drive:auditor`) | `tvly extract --format text <url>` through Bash | `curl -sL <url>` | never WebFetch: it answers through a small model, and a summary is not a quotation |
| `drive:investigator`, fix and operate | `gh run list`, `gh run view <id> --log-failed`, `gh issue view`, `git blame`, `git log -S` | project logs | local reproduction only when `gh` is unauthenticated |
| live proof and operate | the target system's own MCP verbs or CLI, loaded at intake | its API | never its database or storage directly |

The headless reality: the iOS Simulator MCP and the Browser pane are injected by the Desktop app and
do not exist in `claude -p` or the terminal CLI. Playwright MCP and Chrome DevTools MCP do. Every UI
verdict names the surface it used (`playwright-mcp`, `chrome-devtools-mcp`, `ios-simulator-mcp`,
`xcuitest+simctl`, `agent-browser`, `npx-playwright`, `browser-pane`) in its `ran` list, and a
verdict that used `xcuitest+simctl` says the accessibility tree was inspected only through XCUITest
queries.

Never start Playwright MCP from `@latest`, which runs whatever npm serves that day inside the
reviewer. When the reviewer starts the server itself, it uses `@playwright/mcp@0.0.80` (the current
version when this was checked on 2026-09-14), and first compares
`npm view @playwright/mcp@0.0.80 dist.integrity` with
`sha512-FOPXHm2SvFhAQylm10jMZ35B/SR2TaMLVkavAlwoG4N2qCb5RqbvhQYcu3zmXNyxR2DW0Ooxe+9XPVt5UjKRCQ==`.
Merge the pinned version and the observed integrity into `.drive/capabilities.json` as
`pin:playwright-mcp`, and refuse to start the server when the two values differ; that caps web
`[ui]` rows at the fallback in section 6. When the owner's own configured server is already running,
record the version it reports in each UI proof's `proof.json`, and when a later verdict fails on a
different version, re-run the earlier one before blaming the code. Raising the pin is a lesson commit
to this file that carries the new integrity value.

Never use the owner's real, logged-in browser for verification or for anything else in a run:
`claude-in-chrome` tools and the `chrome-cdp` skill act in the owner's real sessions and accounts. The
Chrome DevTools MCP browser uses its own persistent profile; point it only at localhost or the
project's own deployed URLs, and never sign in to, read, or create account state there.
`computer-use` needs the owner to approve each application, which is a queue; do not plan on it, and
verify native macOS UI with XCUITest instead. Domain MCP servers are used only when the goal names
that system, and then through its own verbs.

The ui-reviewer's frontmatter disallows `mcp__playwright__browser_run_code_unsafe`,
`mcp__playwright__browser_file_upload`, `mcp__chrome-devtools__upload_file`, and
`mcp__chrome-devtools__execute_3p_developer_tool`. If a composed tool writes into the project (the
Browser pane writes `.claude/launch.json`), remove the file before the phase ends unless it is a run
recipe you deliberately commit with the change.

## 5. Overlapping reviewers and the capability behind each hardening step

The five review-shaped capabilities look alike and are not substitutes. `/code-review` hunts
correctness bugs and cleanups in a diff with a finder fleet; its output is findings, never proof.
`/simplify` hunts no bugs; it restructures changed code and edits the tree. `severe-testing` is not a
review: it writes and runs tests that try to refute named claims and scores what it demonstrates.
`/security-review` is a narrow, high-precision read of a diff for exploitable vulnerabilities and is
deliberately blind to resource exhaustion and theoretical races, which severe testing covers. `audit`
reads a whole codebase for structural simplification in data and state; it is discovery for
archaeology, never hardening, and it must not run tests.

The order of the hardening steps, when each runs, and how code-review findings are handled are
canonical in `references/verification.md` section 5; follow that file. This table adds only which
capability each step uses and what its output counts as.

| Step in verification.md section 5 | Agent | Capability and route | Its output counts as |
|---|---|---|---|
| Gates | orchestrator | the project toolchain by Bash | the GATES line |
| Correctness | `drive:verifier` | handoff from files; on existing code, `/code-review <level> <range>` run by `drive:security-reviewer` beside it | `verdict:`; code-review findings are a Markdown report the security reviewer writes under `.drive/reviews/` through a quoted heredoc, input for the orchestrator and never a verdict or a STATUS evidence token |
| Conformance | `drive:grader` | the frozen rubric by path | a verdict input |
| Severe testing | `drive:severe-tester` | `severe-testing` (pre) | `severe:` tokens the verifier re-runs |
| Security review | `drive:security-reviewer` | `security-review` invoked by the reviewer when its range checks pass, else its own lenses | `review:.drive/reviews/<date>-security-<slug>.md` on the rows it covered, which never satisfies Done's final-audit `review:` |
| UI review | `drive:ui-reviewer` | the MCP tools or CLIs in section 4; the app launched by the project recipe or `/run` (orch) | `shot:` and `findings.json` |
| Simplify | `drive:implementer` | `/simplify <paths>` named in its package brief, then your gates and the grader's baseline check | its own commit, reverted if the test baseline changed |
| Docs review | `drive:grader` | `google-dev-docs-style` review checklist (path) for docs pages | `doc:` |
| Final audit | `drive:auditor`, or a fresh `drive:verifier` when the auditor is not required | the checklist in `references/definition-of-done.md` section 6; no skill | the `review:` token Done requires |

Security review follows severe testing because the tester's demonstrations are what the reviewer
checks, and the skill's exclusions make a clean reading weak on its own. Simplification comes after
every verdict because it edits the tree and would otherwise invalidate them.

## 6. Fallbacks, status ceilings, and the degradation rules

| Missing | Fallback | Status ceiling |
|---|---|---|
| `severe-testing` | `drive:severe-tester` and `drive:security-reviewer` follow section 7.1 | none; the verdict notes the fallback |
| `deep-research` and its plugin variant | researcher follows `references/research.md` | none |
| Tavily skills, CLI, and MCP all absent | WebSearch for discovery, `curl -sL` for raw citation text | none; slower |
| `frontend-design` | designer follows section 7.2 | none for function; the ui-reviewer's taste notes name the gap |
| `web-design-guidelines` or network | objective checks and the design contract in `references/ui-verification.md` | none |
| Playwright MCP and Chrome DevTools MCP | `agent-browser`, else an `npx playwright` script | none if a scripted browser captures `shot:` evidence; otherwise `[ui]` web rows cap at Partial |
| iOS Simulator MCP (every non-Desktop run) | `xcodebuild test` with XCUITest plus `simctl io screenshot` | none; the verdict states the limited accessibility inspection |
| Xcode or a bootable simulator | none | `[ui]` and `native-platform` rows cap at Partial |
| `/security-review`, no `origin`, or a range it would not cover | `drive:security-reviewer` reviews `<baseline_sha>...HEAD` itself with the severe-testing lenses | none |
| `/code-review` | verifier alone | none; one fewer independent pass, recorded |
| `/simplify` | skip the step and record it | none; simplification is not a completion requirement |
| prose skill (`writing` and every `<plugin>:writing`) | writer follows section 7.3 | none; the auditor reads narrative prose against 7.3's checklist |
| `google-dev-docs-style` | the project's existing docs conventions: second person, present tense, sentence-case headings, numbered steps, every command run before it is printed | none |
| `imagegen` or its API key (`imagegen models` fails) | real screenshots and typographic design | none |
| `gh` unauthenticated | local reproduction of CI failures | none for Local Proof; CI runs cannot supply `ops:` evidence |
| `claude-api` | researcher reads the platform docs as raw text | none |
| Workflow tool absent, not allowed by the launch settings, or a Workflow call refused | background Agent calls from you with the same agent types, at most eight at a time | none; slower |
| a domain MCP server that failed to connect | the system's CLI or API | claims that need the system cap at Local Proof until it answers |

Two rules govern degradation. A missing verification capability lowers the ceiling of the claims it
would have verified; it never lets a layer pass by default, and a skipped layer is written as
skipped with its reason, never as green. A missing capability is reported once, as a substitution
line in STATE.md and a sentence in REPORT.md; the run does not stop, ask, or install anything.

## 7. Condensed fallbacks

These are fallbacks, used only when section 1 found the named skill missing. When the skill is
present, invoke the skill and ignore this section.

### 7.1 Fallback for `severe-testing`

Write tests that try to refute each claim, not tests that merely accompany it. For each claim key: write the claim, its valid input
space, postconditions, invariants, and failure semantics. List observations that would prove it
false (wrong value, silent corruption, leak, unauthorized access, stale state, race, timeout,
resource blowup, missing audit trail, unsafe fallback). Choose an oracle independent of the code: a
spec, a mathematical identity, a reference implementation, a permission matrix, a schema validator,
an accessibility tree. Attack the input space: boundaries and one past them, malformed and empty
data, Unicode normalization and control characters, huge and deeply nested values, duplicates,
reordering, retries, interrupted writes, concurrent operations, restarts. Where the code touches
identity, data, files, network, plugins, or model prompts, fan out by lens and treat each separately:
authorization, authentication and session, injection, file and path handling, outbound requests,
parsing, secrets and privacy, concurrency, resource exhaustion, supply chain, UI abuse, agent and
prompt misuse. Run hostile cases only in disposable fixtures, and write no working exploit into any
file the orchestrator will read.

Head each test file with `CLAIM`, `PRECONDITIONS`, `POSTCONDITIONS`, `ORACLE`, and `SEVERITY` lines.
Severity of a test: weak (no-crash, shape, one happy path), moderate (edge and invalid cases), strong
(property tests, fuzzing, reference oracles, invariants, concurrency), severe (adversarial inputs with
independent oracles, failure injection, limits, restart, authorization boundaries). Important claims
need at least one strong or severe test.

Score every finding: 0 inapplicable; 25 speculative; 50 reproduced under contrived conditions, with
the conditions stated; 75 reliably reproduced under realistic conditions against an independent
oracle; 100 demonstrated in the real runtime with captured evidence. Report every finding with its
score and severity, list 25-level findings under untested risk, and drop only score 0. A regression test for a fixed bug must score 75 or 100,
which means it failed on the broken code. Before scoring, drop false positives: no attack surface,
preconditions the attacker already has, a higher layer that mitigates it unless you show the layer
fails, concurrency speculation without shared mutable state, helpers unreachable from untrusted
input, input sizes with no delivery path, pre-existing issues unrelated to the claim, and generic
warnings with no concrete path. The pass is incomplete without commands run with results, and a
precise note of skipped categories and weakened oracles.

### 7.2 Fallback for `frontend-design`

Pin the subject first: one concrete subject, its audience, and the screen's single job, stated in
DESIGN.md. Then work in two passes. Pass one writes a compact plan: four to six named hex colours,
typefaces for at least two roles (a display face used with restraint, a body face, a utility face
when data needs it), a layout concept in one sentence with an ASCII wireframe, and one signature
element the product will be remembered by. Pass two critiques the plan: for each part, ask whether
you would produce it for any similar brief; if yes, revise it and record the rejected default and why.
The current generic looks and the other templated-default tells are listed in
`references/ui-verification.md` section 7; check the plan against that list, and use one of those
looks only when the brief asks for it.

Put the one bold choice in the signature element and keep everything around it quiet. Structural devices must
encode something true about the content. Motion is either one orchestrated moment or none. Build to a
quality floor without announcing it: responsive to mobile, visible keyboard focus, reduced motion
respected. Copy is design material: name things by what people control, use active verbs that say
what happens ("Save changes", not "Submit"), keep an action's name the same through the flow, make
errors say what went wrong and how to fix it without apology, and make empty states invite the next
action. For a feature on an existing product, extract the existing tokens and type scale into the
design contract first and match them; distinctiveness is not the goal there. For iOS, the platform's
Human Interface Guidelines are the base, and departures are logged in DESIGN.md.

### 7.3 Fallback for the prose `writing` skill

The sources, the author's framing, and approved examples are the authority. Keep six relationships
intact: to the source, the thought, the author, the reader, the structure, and the language. Keep
faith with the record: never invent a motive, reaction, result, or wider implication, and keep
uncertainty, causality, and proportion as the sources give them; keep private material out unless it
is in scope. Write what the evidence means to a person, not the log of actions that produced it, and
put agency where it belongs: the author for aims, judgments, and trade-offs, the system for runtime
behaviour. Write to the actual reader in exact adult words; clarity means the whole thought, not the
smallest vocabulary. Choose the form the material needs, and give titles, headings, and endings
practical jobs rather than a slogan-like summary of the piece. Stop where the thought is complete.

For a substantial narrative built from a rich source bundle, have the orchestrator run story mapping
as a `drive:writer` Agent call with `model: "fable"`: it returns several source-anchored story maps and drafts no
prose, and it never sees a draft. The writer verifies every load-bearing claim in the chosen map
against the sources and uses one primary arc. Also read the voice section of the user's global
`~/.claude/CLAUDE.md` when one exists.

Revise by checking six things and repairing the smallest real failure each time: that invention or
editorial accounting has not displaced the source; that chronology, architecture, or visible actions
have not displaced the thought and its consequence; that a briefing voice or oversimplification has
not displaced the author's relationship to this reader; that the title, headings, and ending do not
read as a slogan-like précis; that cadence, polish, or drama has not supplied importance the meaning
did not earn; and that a diminishing frame or misplaced credit has not displaced the author's
judgment. Ban staccato bursts, one-line dramatic paragraphs, hype, rhetorical questions, and em-dash
strings.

## 8. Delegation templates and the orchestrator's hardening commands

A worker that should load a conditional skill gets this brief. The first paragraph changes per
skill; the rest is the standard brief shape.

```text
Before you start, invoke the Skill tool with `<skill>`. Use its <the part you need, e.g. "operating
contract and its rule that mechanical and behavioural changes land in separate commits">. Do not run
its full workflow; your scope is the package below. <Mode line when relevant, e.g. "Use
frontend-design in match-the-existing-design-system mode.">
Reference files, if the skill has them: <absolute paths>.

Repository root: <absolute path>
Objective: <one sentence>
Claim keys: <slugs from STATUS.md>
You own: <paths>. Do not touch: <paths>. Never run git.
Commands you may run: <exact commands, each written as `cd <root> && <command>`>
Write your full output to: <path under .drive/>
Report: a status line, file paths, at most 1,500 characters, and the model you ran as.
Budget: <turns or tool calls>

Lessons that apply to this task
<at most ten rules quoted verbatim>
```

| Worker | Skill named | Mode or scope line |
|---|---|---|
| `drive:implementer` | `rust-refinement`, `vercel-react-best-practices`, `react-component-performance`, `claude-api`, or `frontend-design` | the package only; for `claude-api`, "take model ids and caching rules from it, not from memory" |
| `drive:architect` | `frontend-design`, `dataviz`, `claude-api`, `severe-testing` | "stop after the plan; write it into DESIGN.md or TESTPLAN.md" |
| `drive:writer` | the value of `resolved:prose`; `google-dev-docs-style` for docs pages | never both on the same page |
| `drive:researcher` | `tavily-dynamic-search`, `tavily-research`, or `tavily-crawl` | the question, the decision it serves, the budget |
| `drive:investigator` | `severe-testing` | "for the verify rung only" |
| `drive:ui-reviewer` | `frontend-design` | "as a taste lens against DESIGN.md; you edit nothing" |

The security reviewer's range checks, and the order it runs them in before invoking the Skill tool
with `security-review`, live in `<skill dir>/agents/security-reviewer.md`; do not repeat
them in its brief. Its brief gives `baseline_sha`, the threat model section, the severe tester's
report path, and the output file `.drive/reviews/<date>-security-<slug>.md` (none at XS, where the
findings return in its final message). When a check fails, it reviews `git diff <baseline_sha>...HEAD`
itself with the severe-testing security lenses and names the path it took. It describes weaknesses
without working attack material and returns counts by severity and the file path.

The orchestrator's own hardening commands, which are instructions to yourself, not a subagent
prompt:

```text
baseline=<baseline_sha from GOAL.md's probe block>     # per milestone on build: the milestone's start sha
git status --porcelain                                   # must be empty; commit the package first
git rev-list --count ${baseline}..HEAD                   # 0: spawn no diff reviewer; record "empty range" (see below)
# code review: spawn drive:security-reviewer in its code-review mode to run /code-review <level> ${baseline}...HEAD
#   level: the one references/verification.md section 5 gives; never omit level or range; never --fix, --comment, --post, or ultra
# security review: spawn drive:security-reviewer with the brief above; never /security-review here
git diff --name-only ${baseline}...HEAD -- . ':!.drive' # the paths for /simplify, minus lockfiles and generated code
# simplify: spawn drive:implementer with a package brief that owns those paths and runs /simplify <those paths>
#   skipped at XS, for every fix, and for move before cutover is proven
# then: gates; drive:grader compares test names and pass counts with the pre-simplify log
# pass: commit as "simplify: <unit>"
# fail: git status --porcelain lists what simplify touched; git restore --staged --worktree -- <those tracked paths>
#       and remove only the untracked files simplify created
```

An empty range means there is nothing for a diff reviewer to read, so spawn none and write
"empty range at <sha>" under "Verified facts". When the plan expected code changes, an empty range is
itself a failure event: the work was never committed, or `baseline_sha` is wrong. A security reviewer
that meets an empty range anyway reports `blocked`, which is the same finding.

When no project run recipe exists (a `.claude/skills/run-*` skill, a run section in CLAUDE.md, or
documented scripts), invoke `/run` to launch the app, record the URL, port, and process ids in
`.drive/local/run.md`, and stop those processes when the phase ends. `/run`'s own screenshots are
never evidence; the ui-reviewer captures its own.

## 9. What drive never invokes

| Capability | Why not |
|---|---|
| `improve` | it writes `plans/` into the repository root and waits for a person to pick which plans to write |
| `/batch` | it waits for plan approval, puts every unit in its own worktree, and opens pull requests |
| `skill-creator` review viewer | it is a human review queue; drive's own evals run through `claude plugin eval` |
| `refactor`, `/verify` | user-only; preloading does nothing and invoking is refused. `/run` plus `drive:verifier` covers `/verify`'s intent |
| `anthropic-skills:simplify` | its pipeline asks which findings to plan and executes in worktrees; drive uses bundled `/simplify` and plans larger moves with `drive:architect` |
| `design` canvas | it publishes an artifact, and drive publishes nothing on the owner's behalf |
| `claude-in-chrome`, `chrome-cdp`, `computer-use` | the owner's real browser and desktop (section 4) |
| `/code-review --fix`, `--comment`, `--post`, `ultra`; `gh pr create`; `gh pr comment` | edits outside checkpoints, or posts and publishes on the owner's behalf |
| `/schedule` for anything but a signal-less soak | never wait on a scheduler; it also fails without a claude.ai login |

Drive may read these skills' reference files for method, such as a finding format or a set of lenses,
but never runs their interactive flows. Never edit another skill's files during a run.

Skill and tool quirks discovered during runs are appended below with the lesson template in `templates/lesson.md`, capped at 40 entries.

## Learned constraints
