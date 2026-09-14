# From high-level prompt to an overarching specification

Component report for the `/drive` skill. Date: 2026-09-14. Everything marked "verified" was fetched live today from the URL given; "source claim" is something a page asserts that I did not independently confirm; everything else is my opinion, argued.

## 1. Executive opinion

The specification phase exists to do one thing: turn a few paragraphs into the document that every later agent (architect, test designer, implementer, verifier, status keeper) reads instead of the owner. Once the run is autonomous, the spec *is* the owner. So its quality is measured by two questions: can an agent that has read only this document and the code decide what to do next without asking anyone, and can the owner, returning hours later, see every decision that was made on his behalf and overturn any of them in one sentence?

That framing decides what goes in. The executable core is a set of **named requirements**, each a short plain-language behavioral claim used as a heading, each carrying acceptance scenarios and at least one scenario written to prove the claim wrong. Around that core sit the goals and non-goals, the constraints with verified numbers, an **assumptions log** in which every decision the orchestrator made for the owner is stated with its reversal cost, measurable success criteria, a short risk register, and a glossary. Nothing else is load-bearing: no personas, no estimates, no stack choices beyond the ones the owner gave, no task lists, no mockups. Those belong to later phases or nowhere.

Traceability without identifiers is solved by making the handle the identifier. Prose says "the forecast rule"; the test suite is literally named "Suggestions respect the forecast"; the STATUS row is keyed by the same words turned into a slug. A small lint script enforces the linkage so the linkage does not depend on discipline.

Open questions default to decide-and-log. One batched question is permitted, asked once at the end of drafting, and only for decisions that are expensive to reverse, have no defensible default, and would change a large share of the work. When the run is headless the question tool is simply absent, so the skill must be correct without it.

The spec is then reviewed by a fresh-context Opus subagent against a rubric whose most important item is refutation: for each requirement, try to satisfy the tests while failing the user. The post the coordinator is working from never mentions a specification at all. That is its largest gap, and this component fills it.

## 2. What the post says, and a critique

The post is about loops, dynamic workflows, routines, memory files, and verifier subagents. It is silent on requirements. Its "compound stack" has four layers (primitives, orchestration, memory, self-improvement) and none of them holds a statement of what is being built. Its state-file template has verified facts, general rules, open failures, lessons, and a last-session note, but no goals, no scope, no acceptance criteria. Its `/goal` example ("all tests pass") assumes the tests already encode the intent. For a bug fix in a mature codebase that is often true. For "build me a fashion app from two paragraphs" it is false: the tests do not exist yet, and whoever writes them needs something to write them from.

Where the post is right, and where the live sources back it: an independent verifier beats self-critique (Anthropic's Fable 5 prompting guide says exactly this, verified below), and a premature "done" is the characteristic failure of long runs. But the fix Anthropic actually documented for premature completion in its November 2025 harness post was not a loop primitive; it was a *feature requirements file* written by an initializer agent that expands the user's prompt into a comprehensive list of features with test steps, which later agents may only mark as passing and never edit or delete (verified). That is a specification with a status column. The post skipped it.

Where the post exaggerates: "Self-verification built in. Writes its own tests to check its work." A model writing tests for code it just wrote, from intent it inferred itself, is testing its own reading of the prompt. The Fable guide's recommendation is more precise: verify "with subagents against the specification." The specification is the fixed point the verifier needs; without it there is nothing to verify against except the maker's own summary.

Where the post is wrong for this owner: it routes graders to Haiku (the owner has ruled this out) and it treats memory as the durable state without distinguishing project state (what we are building, what is done) from procedural memory (how we work). The spec and STATUS are project state; lessons are procedural. Conflating them is how a run ends up "remembering" a fact about a feature that was descoped three days ago.

One more thing the post gets backwards by omission: it says "Fable 5 was built to run for days." A run that goes for days on an under-specified goal produces days of confident output in a direction the owner did not intend. Length amplifies specification errors. The longer the autonomous run, the more the spec matters, not less.

## 3. Verified facts

### Harness and model behavior

- **Anthropic, "Effective harnesses for long-running agents" (2025-11-26).** The initializer agent writes "a comprehensive file of feature requirements expanding on the user's initial prompt" as JSON with category, description, test steps, and a `passes` field initially `false`; coding agents "edit this file only by changing the status of a passes field"; "It is unacceptable to remove or edit tests." Documented failure mode: "a later agent instance would look around, see that progress had been made, and declare the job done." https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- **Anthropic, "Prompting Claude Fable 5" (platform docs).** "Separate, fresh-context verifier subagents tend to outperform self-critique." Recommended instruction: "Establish a method for checking your own work at an interval of [X] as you build... verifying your work with subagents against the specification." "Skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality." Effort "is the primary control"; `high` as default, `xhigh` for capability-sensitive work. Supplied autonomous-operation reminder: "You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task..." and checkpoint rule: "Pause for the user only when the work genuinely requires them: a destructive or irreversible action, a real scope change, or input that only they can provide." Also: Fable "performs well when given complex, multithreaded requests and asked to determine next steps" and "Give the reason, not only the request." Warning: instructions to echo internal reasoning can trigger the `reasoning_extraction` refusal. https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- **Claude Code best practices.** Documented spec workflow: "have Claude interview you first... using the AskUserQuestion tool... then write a complete spec to SPEC.md", then "start a fresh session to execute it." "The most useful specs are self-contained: they name the files and interfaces involved, state what is out of scope, and end with an end-to-end verification step that proves the feature works." Reviewer caution: "A reviewer prompted to find gaps will usually report some, even when the work is sound... Tell the reviewer to flag only gaps that affect correctness or the stated requirements." https://code.claude.com/docs/en/best-practices.md
- **AskUserQuestion tool.** Each call supports 1 to 4 questions with 2 to 4 options each; `multiSelect` supported; free-text "Other" is a host convention. "AskUserQuestion is not currently available in subagents spawned via the Agent tool." https://code.claude.com/docs/en/agent-sdk/user-input.md. Interactive behavior: questions "stay open until you answer them" unless `askUserQuestionTimeout` (`60s`, `5m`, `10m`) is set, after which the dialog closes, submits selected options, and tells Claude the user may be away so it "proceeds on its own judgment and can re-ask later." https://code.claude.com/docs/en/tools-reference.md
- **Headless mode.** With `--permission-prompts none`, "Claude Code removes the tools that need an answer from a person, such as AskUserQuestion, so Claude can't call them." In `dontAsk` mode, "AskUserQuestion... [is] denied even when an allow rule matches." User-invoked skills work in `-p`: "include /skill-name in the prompt string." `--bare` skips skills/agents discovery except `--add-dir` skills. https://code.claude.com/docs/en/headless.md. An open GitHub issue (2026-02-28) reports AskUserQuestion returning empty answers immediately in some environments. https://github.com/anthropics/claude-code/issues/29530
- **/goal.** Condition up to 4,000 characters; evaluated after each turn by the small fast model (Haiku by default; `ANTHROPIC_DEFAULT_HAIKU_MODEL` overrides everywhere the small model is used); the evaluator "doesn't run commands or read files independently, so write the condition as something Claude's own output can demonstrate"; verdicts met / not yet met / impossible; works with `-p`; defers while background work runs, check-in after 30 minutes. https://code.claude.com/docs/en/goal.md
- **Skills.** "Keep SKILL.md under 500 lines"; supporting files referenced by relative path; `${CLAUDE_SKILL_DIR}`; after compaction "Keeps the first 5,000 tokens of each", "combined budget of 25,000 tokens"; `description` + `when_to_use` truncated at 1,536 characters; `context: fork` with `agent:` runs a skill in a subagent. https://code.claude.com/docs/en/skills.md
- **Advisor tool (experimental, Anthropic API only).** A Fable 5.1 main model accepts only a Fable 5.1 advisor; an Opus or Sonnet advisor is rejected. Subagents inherit the advisor with the same pairing check. https://code.claude.com/docs/en/advisor.md

### Specification practice (sources for the design)

- **GitHub Spec Kit.** Spec template uses prioritized, independently testable user stories, `FR-###` functional requirements, `SC-###` success criteria that must be "technology-agnostic and measurable", Given/When/Then acceptance scenarios, an Assumptions section. https://raw.githubusercontent.com/github/spec-kit/main/templates/spec-template.md. The specify command: "Maximum 3 [NEEDS CLARIFICATION] markers total", mark only when "no reasonable default exists", prioritize "scope > security/privacy > user experience > technical details", and "Record reasonable defaults in the Assumptions section." https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md. The clarify command: "Maximum 5 clarification questions", ranked by "Impact * Uncertainty", answerable by multiple choice or a ≤5-word answer, recorded under `## Clarifications / ### Session YYYY-MM-DD`. https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/clarify.md
- **Kiro specs (AWS).** Three files: `requirements.md`, `design.md`, `tasks.md`; EARS-style acceptance criteria "WHEN [condition/event] THE SYSTEM SHALL [expected behavior]"; tasks reference requirements as "_Requirements: 1.1, 2.3_". https://kiro.dev/docs/specs/feature-specs/
- **EARS (Mavin).** Six patterns: ubiquitous; state-driven "While"; event-driven "When"; optional "Where"; unwanted behaviour "If ..., then"; complex combinations. https://alistairmavin.com/ears/
- **Gherkin.** `Feature`, `Rule` (one business rule), `Scenario`/`Example` (3 to 5 steps recommended), Given/When/Then/And/But, `Background`, `Scenario Outline` + `Examples`, `@tags`. Then steps "should verify observable output, not internal system state." https://cucumber.io/docs/gherkin/reference/
- **Shape Up pitch.** Problem, appetite ("how much time we want to spend and how that constrains the solution", as opposed to an estimate), solution, rabbit holes, no-gos. https://basecamp.com/shapeup/1.5-chapter-06
- **Google design docs.** Non-goals "aren't negated goals like 'The system shouldn't crash', but rather things that could reasonably be goals, but are explicitly chosen not to be goals." Do not write one that is merely an implementation manual. https://www.industrialempathy.com/posts/design-docs-at-google/
- **Spolsky, functional specs.** Scenarios, nongoals, open issues allowed in a first draft but resolved before coding, "specs need to stay alive." https://www.joelonsoftware.com/2000/10/03/painless-functional-specifications-part-2-whats-a-spec/
- **Nygard, ADRs.** Title, context, decision ("We will..."), status (proposed / accepted / deprecated / superseded), consequences ("not just the positive ones"); never delete, mark superseded. https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- **ISO/IEC 25010 (2011 list as published on Wikipedia).** Functional suitability, performance efficiency, compatibility, usability (incl. accessibility), reliability, security, maintainability, portability, each with sub-characteristics. https://en.wikipedia.org/wiki/ISO/IEC_25010 (The 2023 revision renames and adds a safety characteristic; I did not fetch the standard itself, so treat the 2023 details as my knowledge.)
- **Swift Testing.** `@Test("display name")` gives a human-readable name; tags declared as `extension Tag { @Tag static var name: Self }` and applied with `.tags(.name)` to tests and suites; filterable. https://developer.apple.com/documentation/testing/addingtags
- **Amazon PR/FAQ.** Press release under one page; FAQ two to five pages split into external and internal questions. https://workingbackwards.com/resources/working-backwards-pr-faq/ (source claim; consultancy page)

### Platform constraints relevant to the worked example

- **Cloudflare D1 limits.** Max bound parameters per query 100; max database size 10 GB (Paid) / 500 MB (Free); SQL statement length 100 KB; 100 columns per table; 2 MB max row/string/blob; 30 s max query duration; single-threaded per database. https://developers.cloudflare.com/d1/platform/limits/
- **Cloudflare Workers limits.** CPU 10 ms/request (Free), 30 s default up to 5 min (Paid); 128 MB memory per isolate; 6 simultaneous open connections; 64 MiB script size; 100k requests/day on Free. https://developers.cloudflare.com/workers/platform/limits/
- **Cloudflare R2.** Free tier 10 GB-month storage, 1M Class A and 10M Class B operations per month; $0.015/GB-month Standard; egress free. https://developers.cloudflare.com/r2/pricing/. Max object 5 TiB, single upload 5 GiB. https://developers.cloudflare.com/r2/platform/limits/
- **Cloudflare Images `segment=foreground`.** "Automatically isolates the subject of an image by replacing the background with transparent pixels"; "uses an open-source model called BiRefNet through Workers AI." https://developers.cloudflare.com/images/transform-images/transform-via-url/
- **Cloudflare Vitest integration.** The current recommendation is `@cloudflare/vitest-plugin` (the older `vitest-pool-workers` has a migration page); it "runs your Vitest tests inside the Workers runtime", "runs tests fully-locally using Miniflare", with "isolated per-test-file storage." https://developers.cloudflare.com/workers/testing/vitest-integration/
- **Apple App Review 4.8 (Login Services).** Third-party/social login for the primary account requires an equivalent privacy-preserving option; "Another login service is not required if: Your app exclusively uses your company's own account setup and sign-in systems." **5.1.1(v):** "If your app supports account creation, you must also offer account deletion within the app." **5.1.1(iii):** "Where possible, use the out-of-process picker or a share sheet rather than requesting full access to protected resources like Photos." https://developer.apple.com/app-store/review/guidelines/
- **WeatherKit.** 500,000 API calls/month included with the Apple Developer Program; paid tiers from $49.99 for 1M; Apple Weather attribution and data-source link required; iOS 16+. https://developer.apple.com/weatherkit/get-started/
- **EventKit, iOS 17+.** Two tiers: write-only (`NSCalendarsWriteOnlyAccessUsageDescription`) and full access (`NSCalendarsFullAccessUsageDescription`); `EKEventEditViewController` adds events without a permission prompt. https://developer.apple.com/documentation/eventkit/accessing-calendar-using-eventkit-and-eventkitui
- **PHPickerViewController.** "runs in a separate process from your app"; "doesn't require the app to request photo library access permissions"; iOS 14+. https://developer.apple.com/documentation/photokit/selecting-photos-and-videos-in-ios
- **Vision `VNGenerateForegroundInstanceMaskRequest`.** On-device foreground/subject masks; iOS 17+. https://developer.apple.com/documentation/vision/vngenerateforegroundinstancemaskrequest
- **Privacy manifests** (`PrivacyInfo.xcprivacy`): tracking flag, collected data types, required-reason API declarations; required for submissions since spring 2024. https://developer.apple.com/documentation/bundleresources/privacy-manifest-files
- **HIG accessibility.** 44×44 pt minimum hit target; Dynamic Type; VoiceOver labels; Reduce Motion; color never the sole carrier of meaning; 4.5:1 text contrast. https://developer.apple.com/design/human-interface-guidelines/accessibility
- **WCAG 2.2 AA thresholds.** 1.4.3 contrast 4.5:1 (3:1 large text); 1.4.4 resize to 200%; 1.4.11 non-text contrast 3:1; 2.5.8 target size 24×24 CSS px; 2.5.7 dragging alternative. https://www.w3.org/WAI/WCAG22/quickref/
- **String Catalogs** (`.xcstrings`): Xcode 15+, automatic extraction from `Text(...)` and `String(localized:)`, plural and device variation. https://developer.apple.com/documentation/xcode/localizing-and-varying-text-with-a-string-catalog
- **iOS 27** ships publicly today, 2026-09-14 (announced at WWDC26 on 2026-06-08). https://9to5mac.com/2026/09/09/apple-confirms-ios-27-release-date-september-14/. Xcode 27.0 RC (27A266a) dated 2026-09-09 with the iOS 27.0 SDK; latest stable listed is Xcode 26.6 (2026-06-25). https://en.wikipedia.org/wiki/Xcode
- **Wardrobe-app landscape** (competitor-authored comparison, source claim only): Acloset, Whering, Indyx, Fits, Alta, Clueless, Stylebook, Cladwell, Pureple. Automatic background removal is table stakes; weather-aware suggestions exist in roughly half; calendar-event reading is rare (Alta, GetWardrobe); pricing ranges from free to ~$10/month. https://getwardrobe.com/compare/
- **Not verified, do not cite as fact:** Apple's Foundation Models framework details. The fetched page summary returned internally inconsistent numbers (an iOS 18.2 minimum and a 128K context window, which contradict what I know). The research phase must re-verify before the architecture phase relies on on-device generation.

## 4. Detailed spec: what the skill instructs

### 4.1 Where the phase sits and what it produces

Inputs: the owner's prompt (`$ARGUMENTS`), the shape classification from intake, the owner's standing preferences (his global `CLAUDE.md` and memory files), the repository if one exists, and two research digests (platform constraints and, for products, a competitive scan). Output: one spec document plus a seeded STATUS file. I refer to the state directory as `.drive/`; the coordinator should align the path with the state-tracking report.

```
.drive/
  SPEC.md            # the document this report designs (template varies by shape)
  STATUS.md          # one row per requirement handle, seeded from SPEC.md
  RESEARCH.md        # ledger; entries name the spec section they fed
  spec-review/
    2026-09-14-round-1.md   # reviewer findings, verbatim
scripts/ (inside the skill dir, not the project)
  drive-spec-lint     # mechanical checks, exit 0/1
  drive-spec-slice    # print one requirement's section for a worker prompt
  drive-spec-hash     # per-handle content hashes for STATUS drift detection
```

### 4.2 The steps, in order

**Step 0. Read what already answers the questions.** Before drafting, the orchestrator reads the owner's preference files and, when a repo exists, its `CLAUDE.md`, README, existing specs, and test layout. Half of the "open questions" an author would otherwise raise are answered here (commit straight to main, no approval queues, plain language, which test runner). A question whose answer is already on disk is a defect in the spec phase, not an open question.

**Step 1. Pick the template by shape.** Greenfield product → `SPEC.md`. Feature on an existing product, refactor, data pipeline, CLI, library → change spec. Bug hunt or incident → bug brief. Migration or consolidation → migration charter. Pure research, or the research half of research-plus-website → research brief, followed by a change spec for the website. Templates are in 4.7.

**Step 2. Run the research feeders that the spec needs, before drafting where cheap, in parallel where slow.** Platform constraints are cheap and must land first: they become the Constraints section with numbers and URLs (the D1 100-parameter limit is the canonical example of a fact that must be in the spec, because a test environment that does not enforce it certified broken code). The competitive scan is slower and only affects non-goals and table stakes, so the author drafts with a placeholder and merges it on arrival. Every research entry records which spec section it fed.

**Step 3. Draft in a fresh Fable subagent.** The author receives: the prompt verbatim, the shape, the owner's preferences, the constraint digest, the template, and the rules in 4.3 to 4.5. It writes `.drive/SPEC.md` and returns three things: the list of requirement handles, the assumptions it made, and zero or more candidate questions with a recommended default for each. Drafting happens in a subagent so the orchestrator's context stays clean for the long run that follows, and because the Fable guide says Fable is the model that "performs well when given complex, multithreaded requests and asked to determine next steps", which is exactly what turning two paragraphs into forty decisions is.

**Step 4. Lint.** `drive-spec-lint .drive/SPEC.md` (checks in 4.6). Fix mechanically until it passes; this needs no model.

**Step 5. Independent review.** A fresh-context Opus subagent sees the spec, the prompt, the owner's preferences, and the constraints digest, but not the author's transcript. It returns findings against the rubric in 4.8, each tied to a handle, and a verdict of ready or not ready. The orchestrator fixes and re-reviews the diff. Two rounds maximum; remaining findings that are not blocking move into the risk register with the reviewer's wording. A third round is a sign the prompt was genuinely ambiguous and belongs in the single question, not in more review.

**Step 6. Ask the one question, if there is one.** After review, not before: an informed question is worth asking, an early one just relocates the drafting work onto the owner. Criteria and phrasing in 4.4. Batch every qualifying question into a single `AskUserQuestion` call (1 to 4 questions, 2 to 4 options each, recommended default first). If the tool is unavailable (headless with `--permission-prompts none`, `dontAsk`, or inside a subagent), or it returns empty, proceed with the defaults, mark the assumptions "asked, unanswered", and put them at the top of the final report.

**Step 7. Version and seed.** Write a `Spec version` line (date plus the lint's overall content hash) at the top of `SPEC.md`. Seed `STATUS.md` with one row per handle at "Missing", with the handle's content hash. Hand off to architecture and test design. "Version" does not mean frozen; it means every later change is visible.

**Step 8. The change protocol, for the rest of the project.** Any agent that discovers the spec is wrong, incomplete, or contradicted by reality does not code around it. It edits the requirement, appends an entry to the `Changes` section (date, which handles, what changed, why, what it invalidates), and re-runs the lint. The lint recomputes hashes; STATUS rows whose hash changed drop to "Partial (spec changed)" regardless of what they said before, and their tests must re-run and their verifier must re-verify before the row climbs again. The reviewer re-reviews only the diff, at high effort. Renamed handles keep the old wording as a `Formerly:` alias line so tests and STATUS keep resolving.

### 4.3 What the spec contains, and what it leaves out

**Contents, in reading order, for a greenfield product.** The order is chosen so that the parts agents slice out most often come first and the narrative comes last.

1. **One paragraph: what this is and for whom.** The Amazon press-release discipline compressed to five sentences. No adjectives that a competitor could not also claim.
2. **Goals and non-goals.** Goals as outcomes, three to six. Non-goals in the Google sense: things that could reasonably be goals and are deliberately not, each with a one-clause reason. This section does more to prevent scope creep by later agents than anything else in the document, because a worker that wants to "also add" something checks here first.
3. **Users and jobs.** One line per user type, one line per job ("get dressed in under two minutes on a weekday morning without thinking about the weather"). Not personas. A persona with a name and a coffee order is theater; the job is what tests are written against.
4. **Constraints.** Given by the owner (Cloudflare backend, native Swift) or by the platform (verified limits with URLs) or by law and policy (App Review, privacy). Each constraint states what it forbids or requires, never how to comply; compliance is the architect's problem.
5. **Requirements**, each as a named heading (the handle), with: one paragraph of intent; two to five acceptance scenarios in Given/When/Then, each with its own short title; a sub-heading **What would prove this wrong** holding at least one refuting scenario; and, where relevant, a **Failure behavior** line (what happens offline, on denial, on quota, on partial failure). This is the section the test designer and every implementer reads. It must be sliceable: each requirement stands alone given the glossary and constraints.
6. **Non-functional requirements** stated as budgets with numbers: cold start, p95 latency for the two or three hot paths, monthly cost ceiling at a stated user count, offline behavior, data retention and deletion, accessibility floor (HIG 44 pt targets, Dynamic Type, VoiceOver labels, 4.5:1 contrast), internationalization posture (String Catalog from day one even if English-only), observability minimum (what must be visible when it breaks).
7. **Success criteria.** Three to seven, each measurable by an agent without a human, each traceable to at least one requirement. "The app is delightful" is not a criterion. "A new user with twelve photographed items receives a first outfit suggestion within ninety seconds of finishing onboarding, measured on an iPhone 15 in the simulator" is.
8. **Assumptions log.** Every decision the orchestrator made on the owner's behalf, in the format in 4.4. A greenfield spec with fewer than eight entries is hiding decisions inside requirements.
9. **Risks.** Five to ten, each with the trigger that would confirm it and the response. Not a probability-times-impact matrix; two columns of prose.
10. **Glossary.** Every noun the spec uses in a specific sense ("item", "outfit", "look", "occasion") defined once. Workers on Sonnet will otherwise coin synonyms and the data model will end up with both.
11. **Changes.** Empty at version one. Dated entries thereafter.

**What to leave out, and why.**

- *Technology choices beyond the owner's constraints.* The spec says "photos must survive the app being deleted and reinstalled"; the architecture phase says R2. Putting the stack in the spec means every architectural improvement becomes a spec change, and the reviewer ends up reviewing architecture with a requirements rubric.
- *Task breakdowns and estimates.* Agents do not need estimates; they need budgets. Shape Up's appetite is the right concept: a fixed spend (turns, hours, dollars) that constrains the solution. It goes in the goals section as one line. Task lists belong to planning, and they change hourly.
- *Personas, stakeholder maps, background and history.* None of it is executed by anyone.
- *UI mockups and copy.* The design phase owns them; the spec owns the behaviors and the accessibility floor they must meet.
- *Competitive narrative.* The scan's conclusions enter as non-goals ("no social feed in the first version; every competitor has one and none is differentiated by it") and as table stakes in requirements. The narrative stays in the research ledger.
- *Future work.* Either it is a non-goal now or it is nothing. A wishlist section is where scope creeps in through the back door.
- *"Shall" and EARS capitalization.* EARS is a fine discipline for the shape of a requirement (state, trigger, response) and a poor voice for this owner. Write "When the forecast shows rain during a planned outdoor event, the suggestion includes a waterproof outer layer" rather than "WHEN ... THE SYSTEM SHALL ...". The structure survives; the jargon does not.

**Length budgets.** Greenfield: 1,500 to 4,000 words of prose plus scenarios, roughly 15 to 40 requirements. Change spec: under 800 words. Bug brief: under 400. Migration charter: 1,000 to 2,500. Research brief: under 300. These are readable in one sitting by the owner and cheap to re-attach to every worker. If a greenfield spec wants to exceed 40 requirements, the goals are too broad for one appetite; split into a first version and a named non-goal set.

### 4.4 Open questions: decide-and-log, and the single question

**Default: decide and log.** The author decides, using this preference order (Spec Kit's, which matches the owner's instincts): scope, then security and privacy, then user experience, then technical detail. Every decision becomes an assumptions-log entry in this exact shape, written so the owner can overturn it in one sentence and knows what that costs:

```
### We assume <the decision, as a plain claim>
Because: <the one or two facts or preferences that drove it>.
Instead we could have: <the strongest alternative>.
To overturn: say "<the sentence the owner would type>". Before implementation
starts this costs <small>; after <milestone> it costs <larger>, because <reason>.
Status: assumed 2026-09-14
```

Status values: `assumed <date>`, `asked, unanswered <date>`, `confirmed <date>`, `overturned <date>, see Changes`. Entries are never deleted (Nygard's rule); an overturned one stays with its status changed, because knowing it *was* the assumption explains code that predates the change.

The phrasing matters. "We assume" rather than "the system will", because the owner should be able to skim the headings alone and see every place his judgment was substituted. The reversal-cost line is what makes the log cheap to act on: the owner can decide in ten seconds whether a disagreement is worth raising now.

**The single question.** A question is permitted only when all three hold: the decision is irreversible or expensive to reverse (data model that will hold user data, public API shape, money, legal or privacy posture, product identity such as name or single-user versus multi-user); no default is defensible from the prompt, the owner's preferences, and the research; and the answer changes a large share of the work (a third or more of the requirements, or the architecture's spine). If more than one qualifies, they are batched into one `AskUserQuestion` call (up to four questions, up to four options each, verified). Each question states the recommended default as its first option and says what the orchestrator will do if unanswered. It is asked once, after review, and never repeated.

**When the question cannot be asked.** Headless runs with `--permission-prompts none` remove the tool; `dontAsk` denies it; subagents never have it (all verified). The skill therefore instructs: attempt the question only from the orchestrator's own context; if the tool is absent or the answer comes back empty, proceed with the recommended defaults, mark each as "asked, unanswered", and lead the final report with them. This is the Fable guide's autonomous-operation rule applied to specification: the owner is not watching, so a blocked question is a blocked project.

**What is never asked.** Anything in the preference files. Anything with an industry default (retention, error message tone, session length). Anything the research settled. Anything the architecture phase owns.

### 4.5 Traceability without identifiers

The owner will not read "REQ-014" in prose and tests still need to point at requirements unambiguously. The scheme:

**The handle is the identifier.** Each requirement heading is a short behavioral claim, three to eight words, unique in the document, written as something that could be false: "Suggestions respect the forecast", "Deleting the account removes every photo", "Wardrobe browsing works offline". The claim form is deliberate: it is already the statement a test tries to refute, which is the owner's rule that every feature names its behavioral claim before coding.

**Prose refers to handles in words.** "The forecast rule", or the handle itself in italics. Never a number. The lint fails the document on `FR-`, `REQ-`, `SC-`, `R\d+`, `#\d+` patterns outside code blocks and the Changes section.

**Scenarios have titles too.** Under each handle, each Given/When/Then has a title of up to ten words: "Afternoon rain adds a shell layer", "A sundress is never suggested at four degrees". Two levels, both in plain words, both unique.

**Tests use the same words.** Suite or `describe` name is the handle verbatim; test or `it` name is the scenario title verbatim. In Swift Testing: `@Suite("Suggestions respect the forecast")` containing `@Test("Afternoon rain adds a shell layer")`, and the refuting test additionally tagged `.tags(.refutes)`. In Vitest: `describe("Suggestions respect the forecast", () => { it("Afternoon rain adds a shell layer", ...) })`. Gherkin users already do this: `Rule:` is the handle and `Scenario:` is the title. Cucumber's own guidance that Then steps check observable output rather than internal state applies to every scenario in the spec.

**Slugs for machines only.** `slug = lowercase, non-alphanumerics to hyphens, collapsed`: `suggestions-respect-the-forecast`. STATUS rows, proof directories, and the hash table use the slug. The slug never appears in prose or in test names; it is derived, not authored.

**Renames keep aliases.** When a handle is reworded, the old wording goes on a `Formerly: "..."` line directly under the heading. The lint and the trace resolve either. Aliases are removed only when no test or STATUS row still uses the old form, which the trace can check.

**The trace check.** `drive-spec-lint --trace <test roots>` greps suite and test names from the test tree and reports: requirements with no suite; requirements whose suite has no test marked as refuting; test suites whose name matches no handle or alias (allowed only under a `supporting/` directory). Its report is written into STATUS as a small table, so the trace is ground truth rather than a promise.

Why this beats numbered IDs for this owner and this harness: prose stays readable and the owner can skim headings as a table of contents of claims; tests read like documentation; Sonnet workers receive a section whose heading is literally the name of the suite they must write, so drift between spec and tests requires actively choosing different words. Why it beats no scheme: without something enforced, the reviewer is the only link between spec and tests, and reviewers do not scale to forty requirements.

### 4.6 The lint (mechanical, no model)

Checks, all exit-code enforced:

1. Every `###`-level requirement heading is unique after normalization; aliases counted.
2. Every requirement has at least two scenarios with `Given`/`When`/`Then` lines (a `Given` may be omitted when trivial) and a **What would prove this wrong** sub-heading with at least one scenario.
3. Every scenario title is unique within the document.
4. No identifier-like tokens (`FR-\d`, `REQ-\d`, `SC-\d`, `\bR\d+\b`, `#\d+\b`) outside fenced code and the Changes section.
5. Every success criterion contains a number with a unit or a countable noun.
6. Every assumptions entry has all five lines (`Because`, `Instead we could have`, `To overturn`, cost clause, `Status`).
7. Every non-goal has a reason clause.
8. Every constraint that cites a platform limit carries a URL.
9. Every glossary term appears at least once outside the glossary; every capitalized domain noun used three or more times appears in the glossary.
10. Word-count budget for the shape not exceeded (warning, not failure).
11. `--trace`: as in 4.5.
12. `--hash`: emit `slug<TAB>sha256(section text)` for STATUS.

Sketch, so the coordinator can see the size (a few dozen lines of Python; the real one ships in `${CLAUDE_SKILL_DIR}/scripts/`):

```python
#!/usr/bin/env python3
# drive-spec-lint SPEC.md [--trace test_root ...] [--hash]
import re, sys, hashlib, pathlib
text = pathlib.Path(sys.argv[1]).read_text()
body = re.sub(r"```.*?```", "", text, flags=re.S)
reqs = re.split(r"^### ", body, flags=re.M)[1:]
errors = []
seen = set()
for r in reqs:
    title, _, rest = r.partition("\n")
    if title.startswith("We assume"):        # assumptions live under the same heading level
        for line in ("Because:", "Instead we could have:", "To overturn:", "Status:"):
            if line not in rest: errors.append(f"assumption '{title}': missing '{line}'")
        continue
    if title in seen: errors.append(f"duplicate handle '{title}'")
    seen.add(title)
    if len(re.findall(r"^\s*When ", rest, flags=re.M)) < 2:
        errors.append(f"'{title}': fewer than two scenarios")
    if "What would prove this wrong" not in rest:
        errors.append(f"'{title}': no refuting scenario")
ids = re.findall(r"\b(?:FR|REQ|SC)-\d+|\bR\d+\b", body.split("## Changes")[0])
if ids: errors.append(f"identifier-like tokens in prose: {sorted(set(ids))}")
for e in errors: print("lint:", e)
sys.exit(1 if errors else 0)
```

### 4.7 Templates

Bracketed text is guidance to delete. Every template starts with the same two lines so any agent knows what it is reading.

#### SPEC.md (greenfield product)

```markdown
# <Product name>: specification
Spec version: <date> · <hash from drive-spec-lint --hash> · Shape: greenfield product

## What this is
[Five sentences. Who it is for, what job it does, what makes it worth building, what
it is not. No adjectives a competitor could also use.]

## Goals and non-goals
Goals:
- [Outcome, not feature. Three to six.]
Appetite: [Fixed spend for the first version: e.g. "one autonomous run of at most
N turns and $X; scope flexes, the budget does not."]
Non-goals (deliberate, each with a reason):
- [Thing that could reasonably be a goal] because [reason].

## Users and jobs
- [User type]: [job in one sentence, with the situation and the success condition.]

## Constraints
Given by the owner:
- [e.g. Backend on Cloudflare (Workers, D1, R2). Native Swift iOS client.]
Given by the platform (verified, with URLs):
- [Limit, what it forbids or requires, URL.]
Given by policy or law:
- [App Review clause, privacy rule, what it requires, URL.]

## Requirements
[Each requirement: a handle as heading, one paragraph of intent, scenarios, a refuting
sub-section, failure behavior where relevant. Keep each self-contained.]

### <Handle: three to eight words, a claim that could be false>
[Intent, one paragraph.]

**<Scenario title>**
Given [state]. When [trigger]. Then [observable outcome].

**<Scenario title>**
When [trigger]. Then [observable outcome].

What would prove this wrong
**<Refuting scenario title>**
Given [state]. When [trigger]. Then [the thing that must not happen does not happen].

Failure behavior: [offline / permission denied / quota / partial failure: what the user sees
and what the system does.]

## Non-functional requirements
- Performance: [budgets with numbers and the device or environment they are measured on.]
- Cost: [ceiling per month at a stated usage level.]
- Offline: [what works, what degrades, what refuses.]
- Privacy and data: [what is collected, where it lives, retention, deletion, no-tracking stance.]
- Security: [auth posture, abuse cases considered.]
- Accessibility floor: [e.g. HIG 44 pt targets, Dynamic Type through the largest accessibility
  size, VoiceOver labels on every control, 4.5:1 contrast, Reduce Motion honored.]
- Internationalization: [String Catalog from the first commit; locale-aware units and dates.]
- Observability: [what must be visible when it breaks, without a human tailing logs.]

## Success criteria
- [Measurable by an agent. Each names the requirement(s) it evidences.]

## Assumptions
[One entry per decision made on the owner's behalf. Format in the skill's reference.]

### We assume <claim>
Because: ...
Instead we could have: ...
To overturn: say "...". Before ... this costs ...; after ... it costs ..., because ...
Status: assumed <date>

## Risks
- [Risk]. Trigger: [what would confirm it]. Response: [what we do].

## Glossary
- **Term**: definition, one sentence.

## Changes
[Empty at version one.]
- <date>: <handles affected>. <What changed and why>. Invalidates: <tests / STATUS rows>.
```

#### CHANGE.md (feature on an existing product; also refactor, pipeline, CLI, library)

```markdown
# <Change name>: change spec
Spec version: <date> · <hash> · Shape: feature | refactor | pipeline | cli | library

## What changes and why
[Three to five sentences. The user-visible outcome and the reason now.]

## Where it lands
[Files, modules, interfaces, and data that will change; read from the code, not guessed.
Name the existing patterns the change must follow, with a path to an example of each.]

## Must not change
[Invariants: behaviors, contracts, performance characteristics, and data that stay exactly
as they are. Each gets a scenario below that would catch a regression.]

## Requirements
### <Handle>
[Intent.] Scenarios. What would prove this wrong. Failure behavior.

## Non-functional deltas
[Only what this change affects: a new hot path's budget, new data's retention, new
permission's purpose string.]

## Done means
[End-to-end proof: the command or flow that demonstrates the change against the running
system, and which STATUS rung it can reach here (Local Proof vs Live Proof).]

## Assumptions
### We assume <claim> ... (same format)

## Changes
```

#### BUG.md (bug brief; also incident)

```markdown
# <Short description of the wrong behavior>: bug brief
Spec version: <date> · Shape: bug | incident

## Symptom
[What is observed, verbatim where possible: error text, wrong value, screenshot path.
When it started, how often, which environments.]

## Impact
[Who is affected and how badly. For incidents: blast radius and whether it is ongoing.]

## Reproduction
[Exact steps or command. If not yet reproducible, the closest attempt and what differed.
A bug that cannot be reproduced is not yet ready to fix; the first task is reproduction.]

## Hypotheses
[Ranked. Each with the observation that would confirm or kill it. Prior workarounds count
as evidence that the earlier diagnosis was wrong.]

## Done means
- A test exists that fails before the fix and passes after, named for the claim it refutes
  ("<handle>").
- The root cause is stated in one sentence and matches the fix; no symptom suppression.
- [For incidents: the system is back to its steady state, verified by <check>.]
- One general lesson is written to the lessons file if the cause was a class, not an instance.

## Must not change
[Adjacent behavior the fix could disturb, each with the existing test that guards it.]

## Assumptions
### We assume <claim> ... (same format)
```

#### MIGRATION.md (migration or consolidation charter)

```markdown
# <From> to <To>: migration charter
Spec version: <date> · <hash> · Shape: migration

## Current state
[What exists, where, who calls it, what it stores, measured traffic and data volumes.
Read from the systems, not from memory.]

## Target state
[What exists afterwards. What is deleted. What callers see that is different, if anything.]

## Invariants
[Behaviors and data that must be identical before, during, and after. Each becomes a
parity scenario below. Include the ones that are easy to break silently: ordering,
timezones, rounding, idempotency, auth semantics, limits (e.g. D1's 100 bound
parameters), error shapes.]

## Requirements
### <Handle> (parity and new-behavior claims; same scenario format)
What would prove this wrong.

## Cutover
[Sequence, each step reversible until the point of no return, which is named. Dual-write
or shadow-read period and its exit criterion. Who or what flips the switch; never a
scheduler when a trigger exists.]

## Rollback
[For every step before the point of no return: the exact command or action that undoes
it, and how we would know rollback succeeded. After the point of no return: the recovery
path and its cost.]

## Where the test environment is kinder than production
[For each external system in play: what the local or test stand-in permits that production
forbids, and the test that runs against real semantics to close the gap.]

## Done means
[Live Proof: the production check that shows the target serving real traffic with parity
scenarios green, and the old path removed or dark.]

## Assumptions / Risks / Changes (same formats)
```

#### RESEARCH.md (research brief)

```markdown
# <Question>: research brief
Spec version: <date> · Shape: research

## The question
[One sentence, answerable.]

## The decision it serves
[What will be decided differently depending on the answer, and by which phase. Research
that serves no decision is not commissioned.]

## Lanes
- [Lane]: [what it covers, sources to prefer, what "enough" looks like, budget.]

## Standards of evidence
[Verified fact with URL > source claim > opinion. Freshness requirement. Contradictions
reported, not smoothed.]

## Output
[Where the report goes; which spec sections it feeds; the ledger entry format.]

## Done means
[Every lane has a conclusion or an explicit "could not determine" with what was tried.]
```

### 4.8 The independent spec review

**Who reviews.** A fresh-context subagent on Opus, high effort (xhigh for greenfield and migration), read-only tools. It receives the spec, the prompt, the owner's preferences, and the constraints digest, and nothing from the author's transcript. It is told to report only findings that affect correctness, scope, or the owner's stated preferences, per the best-practices caution about reviewers who find gaps because they were asked to.

**Rubric.** Each item is a question the reviewer answers per requirement or per section, producing a finding only on a "no".

1. *Completeness.* Does every noun and verb in the owner's prompt map to a requirement or a non-goal? Does every job in Users and jobs have at least one requirement? Does every external dependency (network, permission, quota, third-party API) have a stated failure behavior?
2. *Testability.* Can each scenario's Then be observed by an agent without a human? Does each success criterion have a number or a count? Is there a refuting scenario that could actually fail against a plausible wrong implementation, rather than one that restates the happy path negatively?
3. *Contradictions.* Requirements versus non-goals; constraints versus requirements; assumptions versus requirements; success criteria versus appetite.
4. *Hidden scope.* "Also", "etc.", "any", "all", "and more". Requirements that imply unstated systems (sharing implies identity and abuse handling; reminders imply push infrastructure and permission prompts).
5. *Failure semantics.* Offline, partial failure, retry and idempotency, data loss, permission denial, quota exhaustion, first-run empty states.
6. *Non-functional coverage.* Performance budgets, cost ceiling, privacy (collection, storage location, retention, deletion), security, offline, accessibility floor, internationalization posture, observability. Use the ISO 25010 list as the checklist of things to have considered, not as section headings.
7. *Goodhart check.* For each success criterion and each requirement's scenarios: describe an implementation that passes them and still fails the user. If one exists in under a minute of thought, the criterion needs tightening.
8. *Owner-preference conformance.* No approval queues or human review gates in any flow; no scheduler where a trigger exists; no rule IDs or codenames in prose; language a careful colleague would write.
9. *Shim audit.* Does the spec name, per external system, where the test stand-in is kinder than production, and require at least one test against real semantics?
10. *Assumption honesty.* Is anything stated as a requirement that is really an assumption? Is the log's reversal cost plausible?

**Output format.** A findings list, each: severity (`blocks`, `fix before build`, `note`), the handle or section, what is wrong in one or two sentences, a proposed fix. Then a verdict: `ready` or `not ready`, with the single most important reason. No praise, no summary of what is good; the orchestrator does not need to be told the spec is thorough.

**Loop.** Orchestrator applies fixes, re-lints, sends the diff and the previous findings back for a second look. After two rounds, `note`-level findings go to the risk register verbatim and the phase closes. Anything still `blocks` after round two becomes a candidate for the single question.

### 4.9 Research feeding the spec, and spec changes mid-project

**Feeding.** The platform digest produces Constraints (with URLs), non-functional budgets (what the platform makes cheap or expensive), risks (limits close to expected load), and the shim audit entries (which local stand-in ignores which limit). The competitive scan produces non-goals (what not to build), table-stakes requirements (what users will assume exists), and glossary terms (what the market calls things). Existing owner assets found in Step 0 produce constraints or reuse requirements; in this owner's environment, for instance, the visible tool list already includes a set of `garderobe_*` wardrobe tools on his own hub, which the research phase must notice before a fashion app spec is drafted, because "integrate with what he already has" versus "build fresh" is a top-level assumption. Every ledger entry names the section it fed, so a later reader can see why a constraint exists.

**Propagation.** The change protocol in Step 8: edit the requirement, append to Changes, re-lint, hashes shift, STATUS rows demote to "Partial (spec changed)", tests re-run, reviewer checks the diff. The rule that makes this work is that nobody may raise a STATUS row while its hash differs from the one recorded at the row's last verification. That is a two-line check in the status tooling and it closes the most common drift: code moves on, spec is edited later to match, STATUS never noticed.

**The /goal condition for this phase**, for reference: `.drive/SPEC.md passes drive-spec-lint, the latest file in .drive/spec-review/ ends with verdict "ready", and .drive/STATUS.md has one row per requirement handle; or stop after 40 turns`. The evaluator reads only the transcript, so the orchestrator prints the lint result, the verdict line, and the STATUS row count at the end of the turn.

## 5. Conditionals by project shape

| Shape | Template | Research before drafting | Author effort | Reviewer | Single question likely? | Notes |
|---|---|---|---|---|---|---|
| Greenfield app | SPEC.md | Platform constraints (blocking), competitive scan (parallel), owner assets | fable, xhigh | opus, xhigh | Sometimes (identity-level decisions) | Full rubric; accessibility and i18n mandatory; cost ceiling mandatory. |
| Deep bug hunt | BUG.md | None beyond reading the code and history | fable, high (in main context; no subagent) | Skip unless the fix will touch more than a handful of files, then opus high on the brief | Almost never | Reproduction first. A repeated workaround in history is evidence the prior diagnosis was wrong. |
| Feature on existing product | CHANGE.md | Read the code; platform digest only for new dependencies | fable, high | opus, high | Rarely | "Must not change" is the load-bearing section; each invariant gets a guarding test. |
| Migration / consolidation | MIGRATION.md | Measure current state from the systems; platform limits for the target | fable, xhigh | opus, xhigh | Sometimes (point of no return, data ownership) | Shim audit mandatory; rollback per step; cutover driven by a trigger, never a cron. |
| Research + website | RESEARCH.md then CHANGE.md for the site | The research is the first deliverable | fable, high | opus, high on the site spec | Rarely (audience or positioning) | Site spec needs content inventory, WCAG 2.2 AA floor, and design-quality criteria the vision verifier can check. |
| Pure research | RESEARCH.md | n/a | fable, high | none; the report's own review is another component | No | Decision it serves must be named or the brief is rejected. |
| Refactor / simplification | CHANGE.md with one requirement: behavior preserved | Read code and tests | fable, high | sonnet, low, mechanical (does every public behavior have a guard?) | No | The spec is mostly the "Must not change" list. |
| Ops / incident | BUG.md (incident variant) | Live system state | fable, high | none during the incident; opus high on the post-incident lesson | No | Steady-state check is the done criterion. |
| Data pipeline | CHANGE.md plus data contracts | Source and sink schemas measured | fable, high | opus, high | Rarely | Idempotency, late data, and schema drift are required failure behaviors. |
| CLI tool | SPEC.md, reduced | Conventions of the host ecosystem | fable, high | opus, high | Rarely | Command grammar, exit codes, and machine-readable output are requirements. |
| Library / SDK | SPEC.md, reduced | Consumers and their idioms | fable, high | opus, xhigh | Sometimes (public API is expensive to reverse) | The public surface is the spec; every exported symbol has a scenario. |

Conditionals the skill text needs: *if the task mentions a UI, add the accessibility floor and a vision-verifiable success criterion*; *if the task stores anything a user made, add retention, deletion, and export*; *if the task touches money, sign-in, or health, the single question is more likely and the reviewer runs at xhigh*; *if the task names an external platform, the platform digest is blocking and the shim audit is mandatory*; *if the repo already has a spec or design doc, the change spec references it and the lint's trace runs against existing tests too*.

## 6. Model and effort assignment

**Spec author** (`drive-spec-author`): Fable, effort high; xhigh for greenfield and migration. Fresh context via the Agent tool, not `isolation: worktree` (it writes one file under `.drive/`). Tools: Read, Glob, Grep, Bash for read-only inspection, WebFetch and WebSearch for verifying a constraint on the spot, Write and Edit restricted by instruction to `.drive/`. Rationale: the Fable guide singles out ambiguity navigation and "determine next steps" as this model's improvements; the spec is where that is spent. Delegating the draft to Opus and reviewing with Fable inverts the value, because review can only find what the draft contains.

**Spec reviewer** (`drive-spec-reviewer`): Opus, effort high; xhigh for greenfield and migration. Read-only tools. Receives no author transcript. Rationale: hard-but-bounded judgment against a fixed rubric is the owner's definition of Opus work. For a second opinion on a `blocks` finding the orchestrator (Fable) adjudicates; the advisor tool does not help here because a Fable 5.1 main model accepts only a Fable 5.1 advisor (verified).

**Lint and trace**: scripts. No model.

**Question composer**: the orchestrator itself, because the question tool is unavailable in subagents (verified) and because judging what the owner would want asked is orchestration.

**Research feeders**: the deep-research component's assignment applies; from this side, the only requirement is that the constraints digest arrives with URLs and numbers, and that the competitive scan arrives as conclusions (table stakes, non-goals), not as narrative.

Draft agent files for `~/.claude/agents/`:

```markdown
---
name: drive-spec-author
description: Turns a high-level prompt plus research digests into a specification that agents can execute without a human. Used by /drive in its specification phase.
model: fable
effort: high
tools: Read, Glob, Grep, Bash, WebFetch, WebSearch, Write, Edit
maxTurns: 60
---
You write the specification for an autonomous run. The owner will not be available while
the work proceeds; the document you write stands in for him. Write it so that an agent
that has read only this document and the code can decide what to do next, and so that the
owner, returning later, can see every decision made on his behalf and overturn any of them
in one sentence.

Read first: the prompt verbatim, the owner's preference files, the repository if present,
the constraints digest, and the template for this shape. Anything those already answer is
not an open question.

Then write .drive/SPEC.md (or the shape's template) and nothing else. Requirements are
headings phrased as short claims that could be false. Each has two to five scenarios in
Given/When/Then with their own short titles, a "What would prove this wrong" scenario, and
failure behavior where an external dependency is involved. Success criteria carry numbers.
Constraints from the platform carry URLs.

Decide rather than ask. Every decision you make for the owner goes in the Assumptions
section in the standard five-line format with an honest reversal cost. Reserve at most
four candidate questions for decisions that are expensive to reverse, have no defensible
default, and change a large share of the work; state a recommended default for each.

Write in full sentences a careful colleague would use. No rule identifiers, codenames,
"shall", or hype. Do not choose technology beyond the constraints the owner gave. Do not
add task lists, estimates, personas, or mockups.

Return: the file path, the list of requirement handles, the assumptions made, and the
candidate questions with defaults.
```

```markdown
---
name: drive-spec-reviewer
description: Independent review of a /drive specification against a fixed rubric. Fresh context, read-only. Reports only findings that affect correctness, scope, or the owner's stated preferences.
model: opus
effort: high
tools: Read, Glob, Grep
maxTurns: 30
---
You are reviewing a specification that will drive an autonomous build with no human in the
loop. You have the spec, the original prompt, the owner's preferences, and a digest of
platform constraints. You do not have the author's reasoning, and you should not try to
reconstruct it; judge the document.

For each requirement and each section, work through the rubric in
${CLAUDE_SKILL_DIR}/references/spec-review-rubric.md: completeness against the prompt,
testability of every scenario and criterion, contradictions, hidden scope, failure
semantics, non-functional coverage, the Goodhart check (an implementation that passes the
tests yet fails the user), owner-preference conformance, the shim audit, and assumption
honesty.

Report only findings that would change what gets built or how it is verified. Each finding:
severity (blocks / fix before build / note), the handle or section, what is wrong in one or
two sentences, a proposed fix. End with one line: verdict ready or not ready, and the single
most important reason. Do not summarize strengths.
```

## 7. Failure modes and anti-patterns

**Spec theater.** A long, well-formatted document nobody downstream reads, because the executable parts are buried under narrative. Prevention: requirements and assumptions come first in the file; the lint enforces structure; workers receive `drive-spec-slice` output, which only works if sections are self-contained, so the pressure to keep them so is structural.

**Mirage completion of the spec phase itself.** The reviewer returns "looks good" and the phase closes. Prevention: the reviewer is instructed to produce findings or an explicit refutation attempt per requirement, never a summary of strengths; the phase's done condition is lint pass plus verdict line plus seeded STATUS, all printed to the transcript for the goal evaluator; a greenfield spec with fewer than eight assumptions fails the lint as a warning and the reviewer is told to treat it as concealment.

**Assumptions stated as facts.** "The app supports one user" as a requirement rather than "We assume one user" in the log. Prevention: rubric item 10; the lint counts assumptions; the reviewer is told that any requirement not derivable from the prompt or preferences is an assumption in disguise.

**Over-asking.** The author raises six questions because asking feels safer than deciding. Prevention: the three-part criterion, the batch limit of one call, the requirement that every question carry a recommended default, and the fact that headless runs cannot ask at all, so a spec that depends on answers is a spec that cannot run.

**Under-asking on the one thing that mattered.** Deciding single-user versus multi-user silently and building the wrong data model. Prevention: the criterion names identity-level decisions explicitly; the reviewer's rubric asks whether any assumption's reversal cost is so high it should have been the question.

**Refuting scenarios that cannot fail.** "When the forecast is not rain, no shell layer is added" restates the happy path. Prevention: rubric item 2 asks whether a plausible wrong implementation would fail it; the reviewer is asked to name that implementation.

**Tests that certify the shim.** The spec requires behavior that a test stand-in cannot exercise (D1 parameter limits, App Store permission dialogs, WeatherKit quotas) and the tests pass against the stand-in. Prevention: the shim audit is a required section for migrations and a required rubric item for everything; the spec must require at least one test against real semantics per external system, and the STATUS ladder forbids "Live Proof" for anything only proven locally.

**Identifier creep.** A worker adds `REQ-7` to a comment, a later agent copies the convention into prose. Prevention: lint pattern check on the spec; the trace check flags test names that match no handle.

**Drift after the first version.** Code changes, spec unchanged, STATUS says Done. Prevention: content hashes per handle; STATUS rows cannot rise while hash differs from the one at last verification; the Changes section is the only sanctioned way to alter a requirement.

**Feature-list inflation from research.** The competitive scan becomes a list of everything competitors have. Prevention: research enters the spec only as non-goals, table stakes, or glossary; appetite is fixed, so every added requirement must displace one.

**Reasoning echo.** A template that asks the author to "explain your thinking" in the document. Prevention: the assumptions format asks for the decision, the driver, the alternative, and the cost, which is a record of the decision rather than a transcript of reasoning; the Fable guide warns that show-your-reasoning instructions can trigger refusals.

## 8. Open questions and trade-offs

**Author in a subagent versus in the orchestrator's context.** A subagent keeps the long run's context clean and gives the author a fresh window, at the cost of a second pass by the orchestrator to absorb the handles and assumptions. Recommendation: subagent for greenfield, migration, and research-plus-website; main context for bug briefs and small change specs where the spec is a page and the orchestrator has already read the code.

**How many scenarios per requirement.** Two to five with one refuting. Fewer than two invites under-specification; more than five means the requirement is two requirements. Recommendation as stated; the lint enforces the floor and warns on the ceiling.

**Whether to hash.** Content hashes per handle add tooling and a rule to the status keeper. The alternative is dated Changes entries and reviewer discipline. Recommendation: hash. It is twenty lines of script, and the drift it prevents is the most common way an autonomous run lies about itself.

**Handles as headings versus handles as tags.** Headings make slicing trivial and keep prose clean; tags (`@forecast`) are shorter in test code. Recommendation: headings, with the derived slug for machines only. Test names are long but they read as documentation, which is the point.

**Reviewer model.** Opus is the owner's stated choice for hard-but-bounded judgment. For greenfield, the spec is the highest-leverage artifact in the run and a case can be made for a Fable reviewer. Recommendation: Opus at xhigh, with the orchestrator (Fable) adjudicating any `blocks` finding the author disputes. Two Fable passes on the same document mostly agree with each other, which is what adversarial verification is trying to avoid.

**When the question is asked.** After review means the owner's one interruption is informed; before drafting means a wrong assumption never propagates. Recommendation: after review, because a spec drafted around a placeholder ("single-user or multi-user") is cheap to adjust before implementation, and because the owner's habit is to leave the run alone.

**Interaction with plan mode.** Claude Code's own spec workflow uses plan mode and an interview. `/drive` is the opposite posture: no interview, decide-and-log. Recommendation: do not use plan mode inside the skill; the spec phase is its own gate with its own reviewer.

## 9. Skill text candidates

Passages ready to lift into `SKILL.md` or `references/spec.md`. Imperative, plain.

1. **Purpose of the spec.** Write the specification as the document that stands in for the owner while he is away. An agent that has read only this document and the code must be able to decide what to do next; the owner, returning later, must be able to see every decision made on his behalf and overturn any of them in one sentence.

2. **Read before you decide.** Before drafting, read the owner's preference files, the repository's own guidance, and any existing spec or design document. A question those already answer is not an open question; treat raising it as a defect.

3. **Requirements are claims.** Phrase every requirement heading as a short claim that could be false, in three to eight words: "Suggestions respect the forecast", "Deleting the account removes every photo". Under each, write two to five scenarios in Given/When/Then with their own short titles, and a sub-section called "What would prove this wrong" holding at least one scenario a plausible wrong implementation would fail.

4. **No identifiers in prose.** Refer to requirements by their words, never by numbers or codes. Test suites are named with the requirement's exact words; tests are named with the scenario's exact words. Machines use a slug derived from the handle; people never see it.

5. **Decide and log.** When the prompt leaves something open, decide it, using this order of care: scope, then privacy and security, then user experience, then technical detail. Record every such decision in the Assumptions section as "We assume ...", with why, the strongest alternative, the sentence the owner would say to overturn it, and what overturning costs before and after implementation begins. Never delete an assumption; change its status.

6. **The one question.** Ask the owner only when a decision is expensive to reverse, has no defensible default, and would change a large share of the work. Batch every such decision into a single question call, at most four questions, each with a recommended default listed first. Ask once, after review. If the question tool is unavailable or the answer comes back empty, proceed on the defaults, mark them "asked, unanswered", and lead the final report with them.

7. **Constraints carry evidence.** Every platform limit in the Constraints section carries the number and the URL it was read from today. Where the local or test environment does not enforce a production limit, say so, and require a test that exercises the real semantics.

8. **Leave these out.** Do not choose technology beyond what the owner specified. Do not add task lists, estimates, personas, stakeholder lists, mockups, competitive narrative, or a future-work section. If something is worth mentioning and not worth building now, it is a non-goal with a reason.

9. **Non-goals have reasons.** List things that could reasonably be goals and are deliberately not, each with a one-clause reason. Later agents check this section before adding anything.

10. **Budgets, not adjectives.** State non-functional requirements as numbers with the device or environment they are measured on: cold start, hot-path latency, monthly cost at a stated usage level, offline behavior, retention and deletion, an accessibility floor, and an internationalization posture. "Fast" and "intuitive" are not requirements.

11. **Review from a clean seat.** Have a fresh-context reviewer read the spec, the prompt, and the owner's preferences, with none of the author's reasoning. It reports only findings that change what gets built or how it is verified, each tied to a requirement, with a verdict of ready or not ready. Two rounds at most; leftover notes go to the risk register in the reviewer's words.

12. **Try to cheat the criteria.** For each success criterion and each requirement, describe an implementation that would pass the tests yet fail the user. If you can in under a minute, tighten the criterion.

13. **Changing the spec mid-run.** When reality contradicts the spec, do not code around it. Edit the requirement, add a dated entry to Changes naming the affected requirements and what it invalidates, and re-run the lint. Any STATUS row whose requirement text changed drops to "Partial (spec changed)" until its tests re-run and its verifier re-confirms. A renamed requirement keeps its old wording as a "Formerly" line so tests still resolve.

14. **Shape decides the template.** Greenfield product: the full spec. Feature, refactor, pipeline, CLI, library: the change spec, whose load-bearing section is "Must not change". Bug or incident: the brief, which begins with reproduction and ends with a test that fails before the fix. Migration: the charter, with invariants, a cutover whose point of no return is named, and a rollback per step. Research: the brief, which must name the decision it serves.

15. **Done for this phase.** The spec passes the lint, the latest review ends with "ready", STATUS has one row per requirement, and all three are printed to the transcript. Nothing else counts, including a long and careful document.

---

## Appendix: worked example, the fashion and outfit iOS app

**The prompt as the owner might type it** (two paragraphs, invented for the exercise):

> I want an iOS app that knows my wardrobe and tells me what to wear. I photograph my clothes, it catalogs them, and each morning it proposes an outfit that suits the weather and what's on my calendar. I should be able to browse and edit the wardrobe, mark what I actually wore, and put together outfits by hand when I feel like it. Photos should look clean, like a catalog, not like my bedroom floor.
>
> Backend on Cloudflare, native Swift on the phone. I'd like to share an outfit with someone occasionally. Keep it simple and fast; I'll use it every day.

**What the orchestrator finds in Step 0** (from this environment, without reading the owner's private repo): his preferences forbid approval queues and schedulers, require plain language, and commit to main. His tool list includes wardrobe tools on his own hub (`garderobe_inventory_read`, `garderobe_plan_suggest`, `garderobe_wear_log`, and others). That single observation creates the largest assumption in the spec and is the strongest candidate for the one question: build fresh, or build a client for what he already has?

**The spec skeleton the author would produce** (abridged; handles complete, scenarios shown for three requirements, assumptions complete):

```markdown
# Wardrobe: specification
Spec version: 2026-09-14 · <hash> · Shape: greenfield product

## What this is
A personal iOS app that catalogs the owner's clothes from photographs and proposes a daily
outfit that fits the forecast and the day's calendar. It is built for one person who will
open it every morning for under a minute. It stores its data on the owner's own Cloudflare
account. It is not a social network, a shop, or a stylist marketplace.

## Goals and non-goals
Goals:
- Getting dressed on a weekday takes under a minute of attention, weather and calendar included.
- Every item in the wardrobe is findable in under ten seconds by type, color, or warmth.
- Photographs look like a catalog: subject isolated, consistent framing.
- What was actually worn is recorded with one tap, so suggestions improve.
Appetite: one autonomous run; first version proven live on the owner's phone via TestFlight.
Non-goals:
- A social feed or public profiles, because every competitor has one and none is chosen for it.
- Buying or selling clothes, because it changes the app's privacy and payments posture entirely.
- Virtual try-on or body imagery, because it adds sensitive data with no bearing on the morning job.
- Android or web clients, because the owner named native Swift and the appetite is one run.
- Multi-user households, because sharing one wardrobe across accounts changes the data model;
  see the assumption "one user, one wardrobe".

## Users and jobs
- The owner, on a weekday morning: open the app, see one outfit that fits today, accept or
  swap one piece, leave.
- The owner, on a Sunday: photograph new items, retire old ones, browse.
- The owner, occasionally: send an outfit to a friend as an image or link.

## Constraints
Given by the owner: Cloudflare backend; native Swift iOS client; committed to main; no
approval steps in any flow.
Given by the platform (verified 2026-09-14):
- D1 allows at most 100 bound parameters per query and 10 GB per database; single-threaded
  per database. https://developers.cloudflare.com/d1/platform/limits/
- Workers CPU time is 10 ms per request on Free and 30 s by default on Paid; 6 simultaneous
  open connections. https://developers.cloudflare.com/workers/platform/limits/
- R2 includes 10 GB-month, 1M writes, 10M reads free; egress is free.
  https://developers.cloudflare.com/r2/pricing/
- Cloudflare Images can isolate a subject with `segment=foreground` (BiRefNet via Workers AI).
  https://developers.cloudflare.com/images/transform-images/transform-via-url/
- WeatherKit includes 500,000 calls per month with the developer program and requires
  Apple Weather attribution. https://developer.apple.com/weatherkit/get-started/
- Calendar access on iOS 17+ is write-only or full; reading events requires full access
  and its purpose string. https://developer.apple.com/documentation/eventkit/accessing-calendar-using-eventkit-and-eventkitui
- The photo picker runs out of process and needs no library permission.
  https://developer.apple.com/documentation/photokit/selecting-photos-and-videos-in-ios
- Vision can produce foreground masks on device on iOS 17+.
  https://developer.apple.com/documentation/vision/vngenerateforegroundinstancemaskrequest
Given by policy:
- If the app supports account creation it must offer in-app account deletion (App Review
  5.1.1(v)); prefer the out-of-process picker over full Photos access (5.1.1(iii)); an app
  using only its own sign-in is exempt from the alternative-login rule (4.8).
  https://developer.apple.com/app-store/review/guidelines/
- A privacy manifest is required; tracking is declared false.
  https://developer.apple.com/documentation/bundleresources/privacy-manifest-files

## Requirements

### Adding an item takes one photo and two taps
Intent: the wardrobe grows only if adding is nearly free. One photo from camera or picker,
the app proposes type and color, the owner confirms or corrects, done.

**A photographed shirt is cataloged with a proposed type and color**
Given the wardrobe is open. When the owner photographs a shirt. Then within five seconds an
item appears with a proposed type "shirt", a dominant color, and a cleaned image, awaiting
one confirmation tap.

**Correcting the proposal takes one tap per field**
Given a proposed item. When the owner changes the type. Then the item saves with the new
type and no other field changes.

What would prove this wrong
**Adding never blocks on the network**
Given the phone is offline. When the owner photographs an item. Then the item is saved
locally with the raw photo and a "cleaning later" marker, and no error dialog appears.

Failure behavior: no camera permission shows the picker instead; picker cancelled shows
nothing; image cleaning failure keeps the raw photo and marks the item for retry.

### Photos look like a catalog
### Every item is findable in ten seconds
### Suggestions respect the forecast
Intent: the morning outfit fits the day's weather at the owner's location, including changes
during the day.

**Afternoon rain adds a shell layer**
Given a forecast of dry morning and rain from 14:00, and a calendar with an outdoor event at
15:00. When the morning suggestion is generated. Then it includes a waterproof outer layer.

**A cold morning raises warmth**
Given a forecast high of 6 °C. When the suggestion is generated. Then every proposed item's
warmth rating is at or above the "cold" band, and at least one layer is a coat or heavy knit.

What would prove this wrong
**A sundress is never suggested at four degrees**
Given items tagged "summer" and a forecast high of 4 °C. When ten suggestions are generated.
Then none contains a summer-only item.

Failure behavior: no forecast (quota, offline) produces a suggestion from the last cached
forecast with a visible "forecast from <time>" note; no cache produces a season-based
suggestion with a visible note; never an empty screen.

### Suggestions respect the calendar
### Suggestions avoid what was just worn
### Swapping one piece keeps the rest
### Marking an outfit as worn takes one tap
### Wardrobe browsing works offline
### Building an outfit by hand is a drag-and-drop
### Sharing an outfit produces an image and a link
### Shared links expire and reveal nothing else
### Deleting the account removes every photo
### Signing in uses the owner's Apple ID only
### The morning outfit is ready before the owner opens the app
### Every screen is usable with VoiceOver and the largest text size
### The app never asks for more permission than the current action needs

## Non-functional requirements
- Performance: cold start to the morning outfit under 1.5 s on an iPhone 15 (simulator
  measurement accepted for Local Proof; device measurement required for Live Proof); item
  search results under 200 ms for a 500-item wardrobe.
- Cost: under $5 per month on Cloudflare at one user with 1,000 items and 50 suggestions
  per month; under $50 per month at 100 users. WeatherKit within the included quota.
- Offline: browsing, wear logging, and hand-built outfits work offline and sync later;
  suggestions degrade as described under the forecast rule.
- Privacy and data: photos and item metadata live in the owner's Cloudflare account only;
  no analytics SDK; privacy manifest declares no tracking; deletion removes objects and rows
  within 24 hours and is verifiable by a listing that returns nothing.
- Security: Sign in with Apple; per-user tokens; shared links are unguessable and expire.
- Accessibility floor: 44 pt targets, Dynamic Type through the largest accessibility size,
  VoiceOver labels on every control, 4.5:1 contrast, Reduce Motion honored.
- Internationalization: String Catalog from the first commit; Celsius/Fahrenheit and date
  formats follow the device locale; English strings only in the first version.
- Observability: every failed suggestion, failed sync, and failed cleaning is counted and
  visible in a Worker endpoint the owner can hit; no log tailing required.

## Success criteria
- From a fresh install, photographing twelve items and receiving a first suggestion takes
  under four minutes of owner attention, measured in the simulator by the vision verifier.
- Ten consecutive morning suggestions across a synthetic week of forecasts contain zero
  summer-only items on days under 8 °C and a waterproof layer on every rainy-outdoor day.
- Account deletion leaves zero R2 objects and zero D1 rows for the account, verified by
  listing.
- Every screen passes the accessibility audit (labels present, targets at or above 44 pt,
  contrast at or above 4.5:1) as reported by the iOS accessibility inspector.
- Monthly cost projection from measured request counts is under the stated ceiling.

## Assumptions

### We assume one user, one wardrobe
Because: the prompt is written in the first person and describes a daily personal routine;
multi-user changes auth, privacy posture, and the data model.
Instead we could have: a multi-user App Store product from day one.
To overturn: say "make it multi-user". Before implementation this costs about a day of
data-model and auth work; after photos are stored it costs a migration of every object key
and row.
Status: assumed 2026-09-14

### We assume the app is built fresh rather than as a client for the owner's existing wardrobe tools
Because: the prompt does not mention them, and a fresh app keeps the backend under this
project's control. But the owner's hub visibly exposes wardrobe inventory, plan, and wear
tools, so reuse is plausible.
Instead we could have: an iOS client over the existing hub with a thin Cloudflare layer.
To overturn: say "use my existing wardrobe backend". Before implementation this replaces
the backend design entirely but costs little; after the backend is built it discards it.
Status: asked, unanswered 2026-09-14   [this is the single question]

### We assume Sign in with Apple is the only sign-in
Because: it exempts the app from the alternative-login rule, gives a private relay email,
and matches a single-user product.
Instead we could have: email and password, or no account at all with iCloud sync.
To overturn: say "no accounts, use iCloud" or "add email sign-in". Cheap before the
backend's auth exists; moderate after.
Status: assumed 2026-09-14

### We assume iOS 26 is the minimum version
Because: iOS 27 ships today; one version back covers the owner's devices and keeps the
newest frameworks available; Vision's foreground masks need only iOS 17.
Instead we could have: iOS 17 for wider reach.
To overturn: say "support iOS 17". Cheap at any time unless a feature depends on a newer API.
Status: assumed 2026-09-14

### We assume photo cleaning happens on the phone first, with the server as fallback
Because: on-device masks are free, private, and offline-capable; the server path exists for
items that on-device masking handles poorly.
Instead we could have: server-only cleaning.
To overturn: say "clean on the server". Cheap before implementation; moderate after.
Status: assumed 2026-09-14

### We assume outfit suggestions are generated on the server with a model, constrained by rules
Because: rules alone produce dull outfits; a model alone produces sundresses in January.
The forecast and calendar rules are hard constraints; the model chooses within them.
Instead we could have: rules only, or on-device generation.
To overturn: say "rules only". Cheap before implementation.
Status: assumed 2026-09-14

### We assume calendar awareness needs full calendar access, read-only
Because: knowing about an outdoor event requires reading events; write-only access cannot.
Instead we could have: manual "what's today like" prompts.
To overturn: say "don't read my calendar". Cheap at any time.
Status: assumed 2026-09-14

### We assume the morning outfit is prepared by a trigger, not a schedule
Because: the owner's rule is never to wait on a scheduler where a signal exists; the
forecast update and the first app open are signals.
Instead we could have: a fixed 06:00 cron.
To overturn: say "just run it at six". Cheap.
Status: assumed 2026-09-14

### We assume sharing is an image plus an expiring link, with no recipient account
Because: "occasionally share with someone" does not justify identity for recipients.
Instead we could have: in-app friends.
To overturn: say "add friends". Expensive after launch: it reopens privacy and abuse.
Status: assumed 2026-09-14

### We assume no monetization and TestFlight distribution first
Because: one user; App Store listing adds review cycles with no benefit yet.
Instead we could have: an App Store listing from the start.
To overturn: say "ship to the App Store". Moderate: adds review-guideline compliance work.
Status: assumed 2026-09-14

### We assume English only, with a String Catalog from the first commit
Because: one user; the catalog costs nothing now and everything later.
To overturn: say "add Dutch". Cheap.
Status: assumed 2026-09-14

### We assume wear history is kept indefinitely and photos until deleted
Because: suggestions improve with history; storage is cheap at this scale.
To overturn: say "keep 12 months". Cheap.
Status: assumed 2026-09-14

## Risks
- On-device masking produces poor cutouts for dark clothes on dark backgrounds. Trigger:
  more than one in five items needs the server path in the first fifty. Response: default to
  the server path and keep the on-device path for offline.
- D1's 100-parameter limit is hit by bulk item sync. Trigger: any query built from a list.
  Response: chunk at 50 and test against the real limit in the Workers runtime, not a shim.
- WeatherKit attribution is missed and blocks TestFlight review. Trigger: review note.
  Response: attribution view is a requirement scenario, not a design afterthought.
- Calendar full-access prompt is refused. Trigger: denial. Response: suggestions run without
  calendar and say so; the app never re-prompts on its own.

## Glossary
- **Item**: one garment or accessory with a cleaned photo, type, colors, warmth band, and
  tags.
- **Outfit**: a set of items proposed or built for one day; may be saved as a look.
- **Look**: a saved outfit the owner can re-wear.
- **Warmth band**: one of cold, cool, mild, warm, hot, derived from item type and material.
- **Wear**: a dated record that an outfit or item was worn.

## Changes
```

**How much the orchestrator decided itself versus left as assumptions.** It decided everything the platform or policy decides for it (Sign in with Apple's exemption, account deletion, the out-of-process picker, WeatherKit attribution, full calendar access for reading, privacy manifest) and everything with an industry default (retention, offline posture, sharing as a link). It logged twelve assumptions where the prompt was silent and a defensible default existed. It asked one question, because "build fresh versus build on the owner's existing wardrobe tools" fails all three tests for a safe default: it is expensive to reverse after the backend exists, nothing in the prompt settles it, and it changes the entire backend half of the work. The spec is drafted around the "build fresh" default so that the run proceeds either way; if the answer arrives as "use my existing backend", the change protocol swaps the Constraints and roughly a third of the assumptions and the architecture phase starts from the new position.

**Where research fed this spec.** Every URL in Constraints came from the platform digest. The competitive scan (competitor-authored, treated as a source claim) produced two non-goals (social feed, marketplace), one table-stakes requirement (automatic background removal), and one differentiator worth keeping (calendar-event reading, which few competitors do). The observation about the owner's own hub came from Step 0 and produced the single question.
