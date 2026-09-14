# 28 · Review: paths, tooling names, models, contamination, style, size, frontmatter

Scope: every file under `skill/` except `scripts/` and `evals/` (SKILL.md, 12 agents, 30 references,
24 templates; 11,737 lines). Rules applied: `25-drafting-brief.md` and `24-synthesis.md` sections 1,
2, 4, 6 and the amendment sections 15 to 19. Every file was read in full; the mechanical parts were
also checked with scripts (path extraction, section cross-reference resolution, shingle-based
duplicate detection, YAML parsing, token estimates). Scratch lived under `/private/tmp` and has been
deleted. Line numbers refer to the files as they stood at review time.

A note on severity. Findings marked **defect** contradict the synthesis, the brief, or another skill
file in a way an agent would act on. Findings marked **minor** are wording or tidiness. Findings
marked **decide** need a coordinator ruling before anyone edits.

---

## 1. Paths

### 1.1 Skill files referenced but absent

None beyond the excluded pending set. Every `references/...`, `templates/...` (including
`templates/design/*` and `templates/rubrics/*`) and `agents/...` path that is not on the pending list
exists. Pending files that are referenced: `templates/handoff.md` (7 refs), `templates/investigation.md`
(4), `templates/lesson.md` (10), `templates/REPORT.md` (2), `templates/verdict.schema.json` (5),
`templates/package-brief.md` (2), `templates/package-report.schema.json` (2), `scripts/drive.py`.

Two pending templates are never referenced anywhere: `postmortem.md` and `retro.md`.
`references/lessons.md` section 12 describes the post-mortem as an extension of the investigation
record and the retro as `.drive/reviews/<date>-retro.md` without naming a template. **decide**: either
name them there ("from `templates/postmortem.md`" at lessons.md:305; "from `templates/retro.md`" at
lessons.md:315) or drop them from the template work list. Likewise `GOAL.md`, `STATE.md`,
`STATUS.md`, `DECISIONS.md`, `LESSONS.md`, `proof.json` and `packages-index.md` are never referenced as
`templates/<name>`; that is fine if `drive.py init` copies them, but `drive.py selfcheck` cannot then
verify them by reference.

### 1.2 Relative skill paths inside agent files (defect)

Subagents run with the target repository as their working directory, so a bare `templates/...` or
`references/...` path in an agent file resolves to the project, not the skill. `capabilities.md:98`
already warns about exactly this for preloaded skills. Half the agent files use the absolute
`~/.claude/skills/drive/` prefix on one path and a bare path on the next. Fix every line below by
prefixing `~/.claude/skills/drive/` (or writing "beside it in `~/.claude/skills/drive/references/`"):

| File:line | Bare path |
|---|---|
| agents/architect.md:31 | `templates/capability-map.md` |
| agents/architect.md:33 | `templates/SPEC.md`, `templates/change-spec.md` |
| agents/architect.md:37 | `templates/DESIGN.md` |
| agents/architect.md:45 | `templates/package-brief.md` |
| agents/architect.md:64 | `spec.md` |
| agents/architect.md:65 | `design.md` |
| agents/auditor.md:48 | `references/models.md` |
| agents/auditor.md:72-73 | `references/spec.md`, `references/design.md` |
| agents/designer.md:18 | `templates/design/DESIGN.md`, `tokens.json`, `screens.yaml` |
| agents/grader.md:42 | `references/lessons/`, `references/domains/*.md`, `references/capabilities.md`, `rejected.md` |
| agents/implementer.md:55 | `templates/package-report.schema.json` |
| agents/investigator.md:35 | `templates/investigation.md` |
| agents/investigator.md:56 | `templates/lesson.md` |
| agents/researcher.md:17 | `templates/RESEARCH.md`, `templates/how-it-works.md` |
| agents/security-reviewer.md:67 | `security.md` |
| agents/severe-tester.md:18 | `testing.md` ("beside it" is readable but still bare) |
| agents/ui-reviewer.md:68 | `templates/verdict.schema.json` (line 67 uses the absolute form) |

Tooling note: `drive.py selfcheck` should normalise the `~/.claude/skills/drive/` and
`$HOME/.claude/skills/drive/` prefixes before checking existence, and should skip the project-side
`scripts/ios/*.sh` and `scripts/lint-workflows.mjs` paths listed in 1.4.

### 1.3 `.drive/` names that contradict section 4, its amendments, or each other

| File:line | Finding | Fix |
|---|---|---|
| references/ui-verification.md:168; templates/design/screens.yaml:12 | `.drive/ios/devices.json`, while decision 19.9 and `domains/ios.md:54,143` use `.drive/local/ios/devices.json` (UDIDs are machine-local and gitignored) | replace with `.drive/local/ios/devices.json` in both |
| references/verification.md:378 | final audit written to `.drive/reviews/<date>-final-audit.md` and `.drive/proofs/final-audit/r<n>/verdict.json`; decisions 19.11 and 19.16, `agents/auditor.md:49` and `definition-of-done.md:286` say `.drive/reviews/<date>-final-audit.json` | "Save its verdict, unedited, to `.drive/reviews/<date>-final-audit.json` and cite that file as the `review:` token." |
| agents/verifier.md:13; references/parallel.md:197; references/verification.md:51, state-files.md:55 | the handoff is `.drive/handoffs/<key>.md`, `<id>.md`, and `<unit>.md` in three places; section 4 says `<unit>` | use `.drive/handoffs/<unit>.md` in verifier.md:13 and parallel.md:197 |
| references/parallel.md:201 | per-package verdicts at `.drive/proofs/<id>/r<n>/verdict.json`; section 4 has `proofs/<key>/`, and 4.5 says `unit` is a key or package id | either write `proofs/<unit>/` in section 4 and state-files.md:57, or keep `<key>` and have a package verdict live under its claim key (parallel.md:201) |
| references/shapes/report.md:23 | saved sources at `.drive/local/sources/<slug>-<date>.md`; decision 19.12 and research.md:207 use `.drive/local/research/sources/<source>-<date>.txt` | replace with `.drive/local/research/sources/<source>-<date>.txt` |
| references/shapes/report.md:25 vs references/definition-of-done.md:86 | citation check saved as `citations.json` in one, `citations.txt` in the other (the `test:` token grammar needs one name) | pick `citations.json` and change definition-of-done.md:86 to `test:.drive/proofs/<key>/r<n>/citations.json::every citation resolves` |
| references/shapes/publish.md:31, :42 | positioning, site map and page briefs live in SPEC.md; decision 19.3, `domains/web.md:73` and `intake.md:254` put them in `.drive/content-plan/` | publish.md:31 artifact "`.drive/content-plan/` (positioning.md, sitemap.yaml, briefs/); the claims ledger in the site's content directory"; publish.md:42 "`.drive/content-plan/` holds three parts." |
| references/design.md:225-226 | the grader "writes JSON to `.drive/reviews/<date>-design-consistency-<slug>.md`" | write `.json`, or say "a Markdown file whose first block is JSON" as design.md:255 does for the review verdict, so the lint knows what to parse |
| agents/ui-reviewer.md:14; references/ui-verification.md:47, :319 | `.drive/rubrics/ui.md` is outside section 4's `rubrics/<shape>.md` and has no template | add a row to state-files.md:55 ("`rubrics/ui.md`, frozen from ui-verification.md section 11") or add `templates/rubrics/ui.md` |
| references/shapes/fix.md:30 | `.drive/proofs/<key>/repro.sh` sits above the round directories section 4 defines | move to `.drive/proofs/<key>/r1/repro.sh`, or add it to state-files.md:57 |
| references/shapes/fix.md:47 | `lessons/general.md` (relative, inside the HUNT example) | `references/lessons/general.md` |
| references/capabilities.md:386; domains/cloudflare.md:316; agents/investigator.md:54 | `.drive/local/run.md`, `.drive/local/smoke.env`, `.drive/investigations/<date>-<slug>.patch` are unlisted | minor: add to state-files.md section 2 so the lint and selfcheck know them |

### 1.4 Paths that look like skill paths but are project paths (minor)

`domains/cloudflare.md:182` `scripts/lint-workflows.mjs`, and `scripts/ios/*.sh` in
`domains/ios.md:42,87,137,337` and `ui-verification.md:121`, are project files, and nothing says who
writes `lint-workflows.mjs`. Fix cloudflare.md:182 to "the project's `scripts/lint-workflows.mjs`,
written by `drive:implementer` in wave 0," and add "the project's" before the first `scripts/ios/`
mention in ios.md:42. `domains/web.md:175` `design/images/` is outside section 4's `design/` list;
add it to the synthesis list or to state-files.md section 2.

---

## 2. `drive.py` subcommands named in the docs

Twelve of the expected fourteen are named. `hook-reinject` and `selfcheck` are never named: the
SessionStart re-injection is described without its subcommand at long-running.md:258 and
state-files.md:25, 261-262, and selfcheck appears nowhere. No unexpected subcommand is named.

| Subcommand and arguments as written | Where | Behaviour the docs rely on (for the tooling author to confirm) |
|---|---|---|
| `init --goal "<goal>"` | SKILL.md:135-136; intake.md:35, 96; long-running.md:124; state-files.md:336-338; domains/ios.md:304, 399 (bare `init`) | creates `.drive/` and writes `.drive/local/active`; archives an unfinished run for a different goal to `.drive/runs/<date>-<slug>/` "in one commit" and "clears `.drive/local/`". `--slug` is never used |
| `start` | SKILL.md:21, 57; lessons.md:49; lessons/general.md:39; state-files.md:25, 260; long-running.md:124, 235 | exit 0 always; prints STATE header and Resume here, rung counts, open rows, open failures, ledger rows at count ≥2, lint findings. **decide**: long-running.md:124 says run `$DRIVE start` on resume when `.drive/local/active` is missing, which implies `start` re-creates the marker; the synthesis defines `start` as read-only |
| `lint --gate <phase>`, `--gate spec`, `--gate design`, `--gate research`, `--stop`, `--final`, `--json` | SKILL.md:175, 340; state-files.md:225-237, 245; spec.md:285; design.md:339; research.md:301; long-running.md:160-161, 174, 192, 337; parallel.md:24; lessons/general.md:19, 49, 69; auditor.md:47; definition-of-done.md:284, 289; capabilities.md:129; intake.md:458; every shape file's report row | the check table in state-files.md section 9; `--stop` requires one worktree and no `drive/*` branch; Live Proof needs `proof.json` `environment` live or device with `shim_differences`; `shot:` on `[ui]` rows; `live` flips and Dropped rows need a DECISIONS.md change; with `registry: <command>` in STATE.md the lint runs that command (state-files.md:331) |
| `hook-stop` | SKILL.md:12; long-running.md:153 | decision table at long-running.md:156-166, including stall detection after six unchanged blocks |
| `hook-guard` | verification.md:88 | runs on Bash, Edit, Write, NotebookEdit. verification.md:88-91 names only the UI reviewer's write area; the tool must also apply decisions 19.1 (verifier under `.drive/proofs/` and `/private/tmp`), 19.13 (`.drive/local/ui/`), 19.14 (security-reviewer and auditor under `.drive/reviews/`) |
| `hook-snapshot start\|stop` | verification.md:92 | records HEAD and a tracked-status hash; blocks the stop and logs to `.drive/local/gate.log` |
| `end` | SKILL.md:340; definition-of-done.md:289; long-running.md:174, 337 | removes `.drive/local/active` after `lint --final` |
| `worktree-land <branch> <sha>` | parallel.md:271, 277; lessons/general.md:47 | merge, remove worktree, delete branch, prune; refuse if the branch moved |
| `lesson-check` | lessons.md:247-250, 287; lessons/README.md:26 | template fields, near-duplicate headings, secret-shaped strings and home-directory paths, caps, standing-rules block ≤15 lines, SKILL.md line cap |
| `lesson-commit <file>...` | SKILL.md:298; lessons.md:251-262; lessons/README.md:27 | stages only named files; message `lesson(<scope>): <heading>` with the five-line body at lessons.md:255-262 |
| `capabilities` | SKILL.md:78; intake.md:98; capabilities.md:30-36, 111; long-running.md:129 | creates `.drive/` when absent (capabilities.md:30, not in the synthesis); flat keys; `"dangling"` values; keeps `git:baseline_sha` on re-runs |
| `guard` | SKILL.md:269; testing.md:176-183, 352; verification.md:349; templates/CONSTRAINTS.md:3; shapes build.md:29, feature.md:28, fix.md:32, move.md:32; definition-of-done.md:259; rubrics build, feature, fix, move, operate, publish | staged, unstaged, untracked; exit 0 clean, 1 violation, 2 could not run; ignores date edits |
| `hook-reinject` | not named | fix: name it once, e.g. long-running.md:258 "the SessionStart hook (`drive.py hook-reinject`) prints the start view" |
| `selfcheck` | not named | fix: name it where the loop's constraints are described, e.g. lessons.md:198-201 or a new line in SKILL.md's reference index row for maintainers |

---

## 3. Models and names

**`haiku` as a model value:** none. Every occurrence of Haiku (models.md:6, 120-130;
long-running.md:53, 185-186) explains why it is excluded or names the environment variable.

**Version-numbered model ids other than `claude-opus-4-8`:**

| File:line | Text | Assessment and fix |
|---|---|---|
| references/long-running.md:53 | `ANTHROPIC_DEFAULT_HAIKU_MODEL` = `claude-sonnet-5` | **decide.** Report 01 line 198 records that this variable takes a full model name, so an alias may not work. The brief allows exactly one pinned id. Either record an exception in synthesis section 19 ("`claude-sonnet-5` is allowed only as the value of `ANTHROPIC_DEFAULT_HAIKU_MODEL`"), or switch to `CLAUDE_CODE_GOAL_GRADER_MODEL` if a probe shows it accepts `sonnet` |
| references/long-running.md:186 | `ANTHROPIC_DEFAULT_HAIKU_MODEL=claude-sonnet-5` | same ruling |
| references/models.md:128 | "sets it to `claude-sonnet-5`" | same ruling |

**Version-numbered display names in prose.** These are facts rather than routing values, and most are
load-bearing; listed so the coordinator can confirm they are wanted.

| File:line | Text | Assessment |
|---|---|---|
| SKILL.md:248 | "one retry on Opus 4.8" | the allowed retry; keep |
| references/models.md:20-21, 30-32 | Fable 5.1, Opus 5, Sonnet 5 (alias resolution and price table) | keep; they date the prices |
| references/models.md:122 | Haiku 4.5 | keep; explains the exclusion (synthesis 16.12) |
| references/models.md:169 | "On Fable 5.1 an effort change keeps the cache" | minor: "On Fable an effort change keeps the cache" unless the version matters |
| references/models.md:192 | "Opus 4.8 where Opus 5 was expected" | keep; it is the fallback signature |
| references/safety.md:13, 20, 21, 127, 138, 139, 181 | Fable 5.1 or Fable 5, Opus 4.8, Opus 5 | keep; the fallback table is only true per version |

**Agent names outside the roster of twelve:** none. Every `drive:<name>` is a roster name; the only
other `drive:` token is the `drive:standing-rules` marker. `models.md:94` names Explore and Plan only
to forbid them.

**`drive-` prefixed agent names:** none. The `drive-` strings are session names (`--name drive-<slug>`,
long-running.md:68, 76), a Workflow meta name (`drive-review-panel`, parallel.md:325), a simulator
name (`drive-sample-phone`, ios.md:53, 204), and scratch directories (`drive-prefix-`, `drive-verify-`,
`drive-audit-`).

---

## 4. Example contamination

No fashion, outfit, wardrobe, garment, Garderobe or Arcwell mention; no email address; no hostname
beyond `example.com` placeholders and vendor documentation hosts. The seeded lessons say only "owner's
project" or "owner's projects". Findings:

| File:line | Text | Fix |
|---|---|---|
| SKILL.md:76 | "look under `~/Projects` before assuming greenfield" | owner-specific directory convention in a general skill. "look in the parent directory of the working directory and in the directories named by `DRIVE_PROJECTS_DIR` (default `~/Projects`) before assuming greenfield" or simply "look for a sibling repository that the goal names" |
| references/intake.md:77 | `ls -d ~/Projects/*<name>*` and `~/Projects/*/README.md` | same change; use `"${DRIVE_PROJECTS_DIR:-$(dirname "$PWD")}"` |
| references/intake.md:211 | "sibling repositories under `~/Projects`" | "sibling repositories beside this one" |
| references/shapes/build.md:13 | "look under `~/Projects`" | "look in sibling directories" |
| references/intake.md:427 | `repo: /Users/<owner>/Projects/admin-app` | home-directory path in an example; `repo: /path/to/admin-app` |
| references/lessons.md:10 | "The skill repository is `~/Projects/drive`" | "The skill repository is the git checkout that `~/.claude/skills/drive` links into; resolve it with `git -C ~/.claude/skills/drive rev-parse --show-toplevel`" |
| references/lessons.md:267-268; references/lessons/README.md:33, 39 | `git -C ~/Projects/drive ...` | `git -C "$(git -C ~/.claude/skills/drive rev-parse --show-toplevel)" ...` (also fixes `lesson-commit` for anyone who clones elsewhere) |
| references/domains/ios.md:69-71 | "Verified on the owner's Mac 2026-09-14 ... Xcode 27.0 (27A5209h ...) at `/Applications/Xcode.app` and 26.6 at `/Applications/Xcode-26.app` ... MCP failing as above" | a host inventory that is wrong on every other machine; delete the paragraph (the doctor records these facts per run into STATE.md), or keep only the facts that generalise: "Two runtime builds can share one identifier; record both." |
| references/domains/ios.md:229 | `location "$UDID" set 51.5074,-0.1278` (central London) | minor, a faint personal hint; use a neutral coordinate such as `37.3349,-122.0090` |
| references/lessons/general.md:60 | "A review queue built to hold memory items for approval dead-lettered 2,286 items" | minor; the detail "memory items" narrows the project. "held items for approval and dead-lettered 2,286 of them" |

Generic harness paths (`~/.claude/CLAUDE.md` at writer.md:23, capabilities.md:310, spec.md:68;
`~/.claude/projects/<project>/memory/` at lessons.md:174; `~/Library/Caches/ms-playwright/` at
ui-verification.md:133; the `$HOME/.claude/skills/drive` install path) are standard locations and
acceptable. `domains/cloudflare.md` section 4 and the gateway example at section 15 and intake.md:590
are recognisably derived from owner work but carry no names; acceptable as anonymised platform facts.

---

## 5. Style

**Em dashes:** none (also no en dashes or `--` used as dashes).
**Rule-ID labels in prose (R-01, F-03, L-017, D-02):** none. Numeric section cross-references were all
resolved by script; every "file.md section N" and "SKILL.md section N" points at an existing heading.
**Instructions to show or explain reasoning:** none. Every mention of reasoning forbids asking for it
(SKILL.md:197, 260; models.md:115; safety.md:56-60; spec.md:84, 233; verification.md:79).
**Instructions to makers to double-check their own work:** none direct. SKILL.md:259 and
parallel.md:398 forbid it. Two borderline items follow at the end of this section.
**Hype words:** none of the promotional set. "genuinely" appears three times as a filler intensifier.

The remaining findings are aphorisms, staccato pairs, personification, and one set of rhetorical
questions. Each has a replacement.

### SKILL.md
| Line | Current | Replacement |
|---|---|---|
| 49 | "If a constraint is genuinely wrong," | "If a constraint is wrong," |
| 161 | "Downgrades are welcome." | "Size and traits may also go down." |

### references/capabilities.md
| Line | Current | Replacement |
|---|---|---|
| 239 | "Refute claims; do not decorate them with tests." | "Write tests that try to refute each claim, not tests that merely accompany it." |
| 284 | "Spend boldness in one place and keep everything around the signature quiet." | "Put the one bold choice in the signature element and keep everything around it quiet." |
| 312-318 | six rhetorical questions ("Has invention or editorial accounting displaced the source? ...") | recast as checks: "Revise by checking six things and repairing the smallest real failure each time: that invention or editorial accounting has not displaced the source; that chronology, architecture, or visible actions have not displaced the thought and its consequence; that a briefing voice or oversimplification has not displaced the author's relationship to this reader; that the title, headings, and ending do not read as a slogan-like précis; that cadence, polish, or drama has not supplied importance the meaning did not earn; and that a diminishing frame or misplaced credit has not displaced the author's judgment." |

### references/definition-of-done.md
| Line | Current | Replacement |
|---|---|---|
| 308 | "...is a Scaffold with good prose." | "Documentation of behaviour that no verdict proves supports Scaffold at most." |
| 311 | "...and green is exactly what a mirage looks like." | "The audit is the only independent check on your summary of the run, and a mirage passes every gate you already ran." |

### references/design.md
| Line | Current | Replacement |
|---|---|---|
| 67-68 | "A design that still runs long is telling you the capability map should split." | "If DESIGN.md still runs long, split the capability map." |

### references/intake.md
| Line | Current | Replacement |
|---|---|---|
| 322-324 | "Trait inflation is how ceremony returns: ... Hold these lines." | "Marking too many traits adds gates that find nothing: every run marked `auth` and `data`, three reviews per package, and a budget spent on checks with no findings. Apply these thresholds." |
| 401-402 | "...because silent disagreement about what is not being built is half of all misalignment." | "...because an unstated boundary is where the owner and the run most often disagree." |

### references/lessons.md
| Line | Current | Replacement |
|---|---|---|
| 274 | "deferring it is a queue by another name." | "because a deferred consolidation is an approval queue." |
| 291-292 | "A lesson that was never relevant in five runs is telling you its scope is wrong." | "A lesson that was not relevant in five runs probably has the wrong scope; narrow or retire it." |
| 296 | "Consulting is a mechanism, not a hope." | delete the sentence; the paragraph already states the mechanism |
| 336 | "Flaky is a place to look." | "A flaky result is a symptom, not a cause." |
| 341 | "Later never comes. Consolidate now." | "A deferred consolidation does not get run; consolidate now." |
| 342 | "Written corrections recur." | "A correction recorded only as prose tends to recur;" |

### references/models.md
| Line | Current | Replacement |
|---|---|---|
| 124 | "Sonnet at low effort is a model you can actually tell to think less." | "Sonnet at low effort gives the cheap tier and still honours an effort setting." |

### references/observability.md
| Line | Current | Replacement |
|---|---|---|
| 51 | "Metrics say that something is wrong, traces say where, and logs say why." | "Use metrics to detect a problem, traces to locate it, and logs to explain it." (minor) |
| 243 | "\"The diagnosis test is theatre, I know the cause.\"" | "\"The diagnosis test is unnecessary; I know the cause.\"" |

### references/parallel.md
| Line | Current | Replacement |
|---|---|---|
| 90 | "Workflows read and judge; Agent calls edit." | "Use Workflows only for reading and judging; every edit goes through an Agent call." |

### references/research.md
| Line | Current | Replacement |
|---|---|---|
| 8-9 | "Research is a bounded service to decisions; it has no appetite of its own." | delete; the paragraph already says research serves named decisions |
| 297 | "Research ends by criteria, never by exhaustion." | "Research ends when these criteria hold, not when the budget or the sources run out." |

### references/safety.md
| Line | Current | Replacement |
|---|---|---|
| 26 | "Fallback rescues a request; it does not protect the run." | "Fallback completes the flagged request, but it degrades every later decision in the run." |

### references/security.md
| Line | Current | Replacement |
|---|---|---|
| 364 | "...is the whole attack." | "a two-line change to an ownership check can expose every account." |

### references/spec.md
| Line | Current | Replacement |
|---|---|---|
| 35 | "The longer the run, the more the spec matters." | delete (minor) |
| 114 | "People read the words; only machines read the key." | "Prose uses the words; paths and tools use the key." (minor) |

### references/state-files.md
| Line | Current | Replacement |
|---|---|---|
| 362 | "Two writers clobber each other. Workers report; you write." | "Two writers overwrite each other's edits, so workers report and you write." |
| 365 | "Your memory is what did not survive." | "Your recollection did not survive compaction or resume;" |

### references/testing.md
| Line | Current | Replacement |
|---|---|---|
| 186 | "If a constraint is genuinely wrong," | "If a constraint is wrong," |
| 188 | "Tightening passes silently. Loosening is loud: it needs..." | "Tightening passes silently; loosening needs..." |
| 277-278 | "A rollback that has never been run is a hope." | "A rollback that has never run is not evidence that rollback works." |
| 334 | "Its setup is paid once; a kind double is paid in production." | "Its setup is a one-time cost, while a kinder double lets limit violations reach production." |
| 335 | "...are not evidence. Read the ledger." | "...are not evidence; check the kindness ledger for what the double does not enforce." |

### references/ui-verification.md
| Line | Current | Replacement |
|---|---|---|
| 391 | "Not a verdict. Five observations, ..." | "That is not a verdict: record five observations, the worst element, and three clean checks per cell, or the review is incomplete." |

### references/verification.md
| Line | Current | Replacement |
|---|---|---|
| 336 | "A verifier weaker than its maker is self-review under another name," | "A verifier weaker than its maker is effectively self-review," |
| 390 | "Done never comes from a bound." | "Reaching the bound never makes a row Done." |
| 396 | "Twice in a row is doubt theater and a failure event." | "Two consecutive rounds dismissed as misunderstandings mean you are validating rather than verifying, which is a failure event (section 7)." ("doubt theater" is a report-23 label the reader has to decode) |

### references/domains/cloudflare.md
| Line | Current | Replacement |
|---|---|---|
| 34-35 | "Green runs against a shim are evidence about the shim." | "A green run against a shim shows only that the shim accepted the code." |
| 358 | "A deploy without the smoke is Scaffold with a URL." | "A deploy without the smoke supports Scaffold at most." |

### references/shapes/build.md
| Line | Current | Replacement |
|---|---|---|
| 111-112 | "Parallelism is high. Research lanes run together (three to five). Wave 0 is serial. Later waves run up to eight..." | "Parallelism is high: three to five research lanes run together, wave 0 runs serially, and later waves run up to eight..." |

### references/shapes/feature.md
| Line | Current | Replacement |
|---|---|---|
| 113 | "Parallelism is moderate. Archaeology lanes run together. Once the contract change is fixed, packages..." | "Parallelism is moderate: archaeology lanes run together, and once the contract change is fixed, packages..." |
| 134 | "...because later does not come." | "...because docs deferred to a later change are rarely written." |

### references/shapes/fix.md
| Line | Current | Replacement |
|---|---|---|
| 93 | "No reproducer, no rung above Partial." | "Without a reproducer, no row rises above Partial." |

### references/shapes/operate.md
| Line | Current | Replacement |
|---|---|---|
| 35 | "A backup never restored is a hope." | delete; line 96 already says it plainly |

### references/shapes/publish.md
| Line | Current | Replacement |
|---|---|---|
| 92 | "consent only if cookies are genuinely set" | "consent only if the site sets cookies" |
| 118 | "A scaffold without briefs invites filler, and filler ships." | "Without briefs the scaffold fills with placeholder copy, which then ships." |
| 119 | "...; no claim id, no sentence." | "...; a sentence without a claim id is removed." |
| 120 | "one real person beats a fictional grid." | "a team page with one real person is correct." |

### references/shapes/report.md
| Line | Current | Replacement |
|---|---|---|
| 93 | "What everyone knows is memory;" | "Common knowledge is still memory;" |

### Borderline: maker self-review and recall wording
| File:line | Finding | Fix |
|---|---|---|
| agents/writer.md:19-20; capabilities.md:122; domains/web.md:37, 189 | the writer (a maker) finishes each docs page by running `google-dev-docs-style`'s review checklist on its own output, which is close to the self-verification synthesis 16.2 forbids | **decide**: keep the checklist as a writing method, or move it to the docs-review step (`drive:grader` with the checklist by path, as capabilities.md:195 already schedules) and delete "finish a docs page with that skill's review checklist" from writer.md:19-20 |
| agents/severe-tester.md:59-60; capabilities.md:262 | "Report every finding scored 50 or above"; 25-level items go to untested risk | acceptable because nothing is dropped, but the wording invites filtering inside the review (synthesis 16.4). "Report every finding with its score and severity; list 25-level findings under untested risk; drop only score 0." |

---

## 6. Size and compaction

### SKILL.md

373 lines (cap 450). Token estimates, since no tokenizer is installed here, as a range of chars/4,
chars/3.5, and words × 1.33:

| Span | Estimate |
|---|---|
| Frontmatter | 120 to 210 |
| Whole file | 5,600 to 7,700 |
| Body without frontmatter | 5,500 to 7,500 |
| First 150 lines (ends inside section 3 step 7) | 2,400 to 3,300 |
| Body through the end of section 6 (line 276) | 4,100 to 5,600 |
| Body through the end of section 5 (line 225) | 3,300 to 4,500 |

**Sections 1 to 6 do not reliably fit in the first 5,000 tokens (defect).** The low estimate fits
with 900 tokens to spare; the two higher estimates put the end of section 6 at 4,900 and 5,600. Two
further facts push it over. First, line 21 injects the `drive.py start` view before section 1, and
the skill is re-attached after compaction as rendered content, so the start view (STATE header, Resume
here, rung counts, open rows, open failures, ledger rows, lint findings) consumes the same budget; on
a mid-run M or L project that can be several hundred to over a thousand tokens. Second, section 6
holds the briefs rules and the parallel-work rules, which are exactly what the orchestrator needs
after compaction.

Fix, in order of preference: (1) move the injected start view below section 6, just above
"## 7. Failures and lessons", with the heading "Run state at invocation" (the SessionStart hook reprints
it after compaction anyway); (2) shorten section 3 by replacing the 19-row trait table
(SKILL.md:102-122, about 700 tokens) with the one-line rule already at SKILL.md:98-100 plus "read the
trait's section in `references/intake.md`", which the intake reference already requires; (3) move the
Size table's Ceremony column (SKILL.md:127-133) to intake.md. Options 1 and 2 together bring the end
of section 6 to about 3,400 to 4,600 tokens with no injected text ahead of it. Also correct
synthesis section 1's "first ~150 lines survive compaction", which should read "first 5,000 tokens",
matching state-files.md:25 and long-running.md:258.

### References over 350 lines

All thirteen carry a table of contents: capabilities (408), design (362), intake (635), lessons (358),
parallel (398), security (385), state-files (379), testing (359), ui-verification (411), verification
(411), domains/cloudflare (449), domains/ios (450), domains/web (406). Two tables of contents have
drifted from their headings (minor):

- `domains/cloudflare.md:11-14` abbreviates section 16 ("Operational gates", heading "Operational
  gates before Done") and 17 ("Anti-patterns", heading "Anti-patterns to refuse") and omits "Learned
  constraints". Fix: use the full headings and append "· Learned constraints".
- `domains/ios.md:11-14` omits "Learned constraints". Fix: append "· Learned constraints".

Size targets from the brief are exceeded, which matters for context cost rather than correctness:
topic references over 350 lines are capabilities, design, intake (635, the largest overrun), lessons,
parallel, security, state-files, testing, ui-verification, verification; shape files over 140 are
build (142), feature (145), move (204), fix (220); agent files over 70 are architect (73), ui-reviewer
(75), investigator (76), verifier (77), auditor (80). `domains/ios.md` sits at the 450 cap. The one
worth acting on is intake.md: section 14's worked classifications (lines 553-635, about 80 lines) can
move to a new `references/intake-examples.md` without loss, since nothing else reads them at a gate.

### Duplicated blocks that can drift

Script-detected template repetition (the rubric standing floors, and the Assumptions, Risks, and
Changes blocks shared by SPEC.md, change-spec.md and MIGRATION.md) is intentional; a change to the
standing floor must touch seven rubric files, which `drive.py selfcheck` could compare. The blocks
below are rules repeated in prose, and six have already drifted.

| Block | Copies | Status | Fix |
|---|---|---|---|
| Rung evidence table | definition-of-done.md:49-58; state-files.md:188-197 | identical today | keep it in state-files.md (the grammar the lint enforces) and replace definition-of-done.md:47-58 with one sentence pointing there |
| Transcript block | SKILL.md:209-216; verification.md:139-146 | differs (verification adds "one line each, blocking first" and a `pending` rule) | keep SKILL.md's copy (it survives compaction), move the two extra rules into it, and have verification.md point to it |
| Red check rule | SKILL.md:48-50; testing.md:185-186 | identical | keep both only if testing.md cites SKILL.md; otherwise delete testing.md's first sentence |
| Roster model and effort | SKILL.md:231-244; models.md:43-57; verification.md:323-331; the agent frontmatter | consistent | have `selfcheck` compare the tables with frontmatter |
| Hardening order | SKILL.md:218-224; capabilities.md:184-196; verification.md:154-164 | differs at the docs step (capabilities: writer fixes, grader checks; verification: grader checks only) | keep verification.md section 5 as canonical, reduce capabilities.md section 5's table to the columns that are about capabilities, align the docs step |
| Maker rules | parallel.md:113-142; agents/implementer.md:17-50 | **drifted**: parallel.md:155-159 lists report fields without `noticed_not_touched` and `concerns` (synthesis 18.15), and rule 10 sends extras to `follow_ups` while implementer.md sends them to "the report" | the agent file is always loaded, so shorten parallel.md section 5 to "The implementer's agent file carries the maker rules; add only package-specific lines to the brief", and add `noticed_not_touched` and `concerns` to parallel.md:155-158 |
| Security range checks | agents/security-reviewer.md:26-33; capabilities.md:356-361; security.md:113-115 | **drifted**: security.md:113 says "the four range checks" and lists three; the agent file runs five commands | keep the agent file's block; security.md:113-115 "Run the range checks in the agent's order of work" |
| Templated-default tells | capabilities.md:278-282; ui-verification.md:231-239; domains/web.md:148-155 | **drifted**: web.md adds the Inter, Roboto, Arial, Fraunces display-face tell | keep ui-verification.md section 7 canonical, add the display-face line there, and have the other two point to it |
| Final-audit checklist and output | definition-of-done.md section 6; verification.md section 13; agents/auditor.md:30-50 | **drifted** on the output path (section 1.3 above) | keep definition-of-done.md section 6 canonical; reduce verification.md section 13 to who runs it and a pointer |
| Pre-fix check | verifier.md:36-38, severe-tester.md:49-52, definition-of-done.md:127-129, 258 use a `git archive` copy; fix.md:143-150, testing.md:242-252, security.md:104-107, rubrics/fix.md:40 use a detached worktree | **drifted** against decision 19.16-17, which says always `git archive` | replace the worktree blocks with the `git archive` form from verifier.md:37 (fix.md:143-149, testing.md:242-252, security.md:105-107) and "the pre-fix `git archive` copy" in rubrics/fix.md:40 |
| Screenshot widths | publish.md:74, ui-verification.md:170, web.md:286 (360, 768, 1280, 1600) | **drifted**: rubrics/publish.md:42 and verification.md:316 say 375, 768, 1440; definition-of-done.md:154 says "three widths" | use 360, 768, 1280, 1600 (decision 19.13) in all three |
| `fix/incident` mitigation phase | fix.md:14, 28 (`execute` before archaeology); intake.md:150 (`mitigate` before `reproduce`) | **drifted** against decision 19.17 and the canonical phase list | intake.md:150 "`execute` runs before `archaeology`, with its undo recorded first" |
| SKILL.md trait and size tables | SKILL.md:102-133; intake.md sections 7 and 9; each shape's Size table | consistent today; intake.md:9 acknowledges the summary | covered by the compaction fix above |

---

## 7. Frontmatter

All thirteen frontmatter blocks parse as YAML (checked with PyYAML).

**SKILL.md** fields: `name`, `description`, `argument-hint`, `disable-model-invocation`,
`disallowed-tools`, `effort`, `hooks`. All are documented skill fields (report 01, skills section).
It sets no `model`, as synthesis section 2 requires, and the Stop hook command uses the
`$HOME/.claude/skills/drive` path per 17.4. The description (417 characters) differs from the
synthesis text but is removed from context by `disable-model-invocation`, so its length does not
matter.

**Agents** use `name`, `description`, `model`, `effort`, `tools`, `disallowedTools`, `skills`,
`maxTurns`, `color`. None uses `hooks`, `mcpServers`, `permissionMode`, or `memory`. Models and effort
match synthesis section 6 as amended by section 15 (writer on `opus`; grader, verifier and auditor
without Skill or WebFetch; Skill added to researcher, architect, implementer via inheritance, writer,
severe-tester, security-reviewer, ui-reviewer, investigator; preloads `deep-research`,
`frontend-design`, `severe-testing` ×2).

| Field or issue | Where | Assessment and fix |
|---|---|---|
| `color` | all 12 agents | documented for subagents but absent from report 01's list of fields plugin agents support (01:97-98). Probably ignored harmlessly. **decide**: keep for local-install use, or remove to keep plugin frontmatter to supported fields |
| writer preload claim | domains/web.md:36 | says `drive:writer` has `writing` preloaded; `agents/writer.md` has no `skills:` and synthesis 15.1 says the brief names the prose skill. Fix web.md:36: "`drive:writer`, invoked with the Skill tool under the name resolved at preflight (it may carry a plugin prefix)" |
| designer and imagegen | domains/web.md:40 | names `drive:designer` as the `imagegen` user; the designer has Bash, so the CLI works, but capabilities.md:121 routes imagery to `drive:implementer`. Fix one of the two so the map and the domain file agree |
| auditor `disallowedTools: Edit, Write` | agents/auditor.md:7 | redundant with the explicit `tools` allowlist and omits NotebookEdit and Agent, which verifier.md:7 lists; harmless. Minor: match verifier.md for consistency |
