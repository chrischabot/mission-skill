# Parallel execution

Read this file at the `decompose` phase, before you spawn more than one agent that edits the
project, when a wave's makers have reported, when a package fails, and before you create any git
worktree. It decides how design becomes work packages, which execution mode each wave uses, what
every brief must state (the repository root and commands written as `cd <root> && <command>`), how a
wave lands on the current branch and is verified, when a worktree is allowed and how it ends, and
what you refuse.

## Contents

1. The substrate · 2. Packages · 3. Waves · 4. Execution mode · 5. Maker rules and runtime
isolation · 6. Brief and report · 7. Integration · 8. Verification · 9. Sizing · 10. Package
failure · 11. The worktree lane · 12. Experiments · 13. Review panel template · 14. Refuse these

`DRIVE` below means `python3 <skill dir>/scripts/drive.py`, with the absolute skill directory
SKILL.md names, and `TMP` means `${TMPDIR:-/tmp}`.

## 1. The substrate

Makers work in the one shared checkout on the current branch (main in the owner's repositories),
each owning a disjoint set of paths, and never run git. You integrate, run the gates, and commit per package. At most eight makers edit in one wave.
Worktrees exist only for experiment arms whose losers are discarded, bisects, and hypothesis arms;
they are detached (no branch), live under `$TMP`, start from HEAD, and are landed or removed in the
step that consumed their result. Every wave ends with no worktree, branch, or uncommitted path that
`.drive/local/baseline.json` does not list, and `drive.py lint --stop` refuses to let the run stop
otherwise. The owner's own worktrees, branches, and uncommitted files, recorded at `drive.py init`,
are never the run's to land, commit, or remove.

## 2. Packages

`drive:architect` writes the decomposition and you check the `decompose` gate. The output is
`.drive/packages/index.md` and one `.drive/packages/<id>/brief.md` per package. A package id is a
short slug of what it delivers (`billing-export-api`), never a number.

1. Make each deliverable in DESIGN.md or the change spec (module, screen, endpoint, migration,
   test suite, document) a candidate package.
2. List each package's owned paths as backticked globs under `## Files you own` in its brief. No
   path may fall under two packages.
3. Give every file several packages would want to the integrator (you), listed under
   `## Integrator-owned` in `index.md`: entry points that register routes or modules, manifests and
   lockfiles, generated code, build and project files, shared configuration, the changelog, and
   `.drive/`. Makers request changes to these through `wiring_needed`.
4. Draw dependencies: a package depends on another when it imports its code, consumes its
   contract, or needs its migration. Contracts (types, schemas, generated clients, design tokens)
   are packages of their own.
5. Size each package for one context: about 10 files, about 1,500 changed lines, one STATUS claim,
   120 turns (the implementer's `maxTurns`, which no call can raise), one to two hours. Split larger ones along a seam with a
   contract; fold smaller ones into a neighbour or your own wiring.
6. Mark `hard: yes` for concurrency, a cross-cutting seam, an unfamiliar framework, or the fix of
   a bug. Hard packages launch with `model: "opus"`.
7. Run the disjointness check below; fix every overlap by splitting or merging packages. Run it
   again before each wave, because re-plans move ownership.

Two globs overlap when either literal prefix (the text before the first `*`) starts with the
other. That is conservative on purpose: packages create files that do not exist yet.

```bash
python3 - <<'PY'
import glob, itertools, re
def globs(path, heading):
    out, on = [], False
    for line in open(path):
        if line.startswith('## '): on = line.strip() == heading
        elif on: out += re.findall(r'`([^`]+)`', line)
    return out
owners = {p.split('/')[-2]: globs(p, '## Files you own') for p in glob.glob('.drive/packages/*/brief.md')}
owners['integrator'] = globs('.drive/packages/index.md', '## Integrator-owned')
def overlap(a, b):
    pa, pb = a.split('*')[0], b.split('*')[0]
    return pa.startswith(pb) or pb.startswith(pa)
bad = [(x, ga, y, gb) for (x, gx), (y, gy) in itertools.combinations(owners.items(), 2)
       for ga in gx for gb in gy if overlap(ga, gb)]
print('ownership disjoint' if not bad else '\n'.join(f'OVERLAP {x} {ga} <> {y} {gb}' for x, ga, y, gb in bad))
PY
```

`index.md` holds one table, `| id | wave | claim key | owns | depends on | hard | status |`, with
status `planned`, `running`, `complete`, `partial`, `blocked`, `integrated`, `verified`, or
`failed`. Update a row after every report and verdict so a resumed session continues from the file.

## 3. Waves

Every package in a wave depends only on packages already integrated and committed. Wave 0 holds
what everything depends on (skeleton with gates wired, contracts, design tokens, a test harness
that enforces production constraints, schema, and ignore-file entries for everything the test
runner and the local runtime write, such as coverage data, `test-results/`, junit reports, and
`.wrangler/` state) and runs one package at a time, each committed
before the next. Never put a client and the endpoint it calls in one wave unless their contract
package is already merged. A client that cannot compile in parallel (one project file, one build
cache) is a design defect to raise at the `design` gate: split it into per-feature modules with a
thin app target in wave 0.

When a wave holds four or more packages cut from one pattern, as a `move` across call sites or a
`build` with many similar modules usually does, run one of them alone through integration and its
verifier round first. Wave 0 proves the scaffold, not the brief: a flaw in how the briefs were cut,
what their test commands cover, or how large each package is would otherwise appear in every package
of the wave and cost a fix round for each. Correct the remaining briefs or the package size from what
the pilot shows, record the change in DECISIONS.md, then start the rest.

## 4. Execution mode

Use Workflows only for reading and judging; every edit goes through an Agent call.

| Mode | Use when | How |
|---|---|---|
| Inline | XS work, integrator wiring, fixes to a seam you own | You edit in your own turn; outside XS a verifier still checks it. |
| One Agent call | One package, a bug fix, or packages in a dependent chain | `drive:implementer` with the brief, then one `drive:verifier`. |
| Background Agent fan-out | Two to eight disjoint packages | One call per package, `run_in_background: true`, all in one message. |
| Workflow | Read-only fan-outs: review panels, research sweeps, hypothesis tournaments, screenshot judging, audits over many files | Load `workflow-authoring` before the run's first script; template in section 13. |

A maker call is `subagent_type: "drive:implementer"`, `run_in_background: true`,
`description: "<id>"`, and a prompt that opens with the reason and points at the brief by absolute
path: "I'm working on <goal> for <owner>. They need <what this package enables>. With that in mind,
implement the package in `<root>/.drive/packages/<id>/brief.md`. The repository root is `<root>`;
run every command as `cd <root> && <command>`." Pass `model: "opus"` only
under the conditions in `models.md`. Pass neither `name` nor `isolation`.

Say nothing about a package until its completion notification arrives. While makers run, write
the coming handoffs and prepare wiring you already know about.

Invoking `/drive` is not an opt-in to workflows. A workflow runs when the launch settings allow
`Workflow` (every recipe in `long-running.md` section 2 does) or when the owner's own prompt asked
for one; in an interactive Manual session each launch prompts. When a Workflow call is refused, or
would prompt in a session nobody watches, run the same fan-out as background Agent calls with the
same agent types and questions, at most eight at a time, and write the results to the same review
file. Never put an editing agent in a Workflow: a relaunch after one failed agent reruns every agent
that started after it, re-applying edits to edited files.

## 5. Maker rules

The implementer's agent file, `<skill dir>/agents/implementer.md`, carries the maker
rules and is loaded on every call, so never paste a second copy into a brief, where the two would
drift. In short: edit only owned paths; run no git command that changes anything, except `git restore
<path>` on a file the maker owns, which the guard allows only for literal paths a package brief owns; run only the
brief's commands; install nothing; request wiring as exact patches; write the refuting test first
and see it red; stop at eighty percent of the budget when not converging; report only what a tool
result shows. A path changed by accident is never restored by the maker; it is listed in the
report's `files` marked "accidental", and you revert it at integration (section 7, step 2).

Add to a brief only the lines that belong to this package: the repository root, the exact commands
written as `cd <root> && <command>`, its runtime isolation values (below), the per-package build
directory when the toolchain holds a global build lock, and any path it must not touch beyond other
packages' globs.

**Runtime isolation.** Makers in one wave run their focused tests at the same moment, so two
packages whose tests start a local service would collide on its port, share rows in its database,
or drive the same simulator. Give every such package its own runtime, write the values into its
brief under **Commands you may run**, and record them on its row in `index.md`.

| Resource | Per package | How |
|---|---|---|
| Port | the project's test port plus 10 times the package's position in the wave (1 to 8) | pass it through the variable or config key the project already reads (`PORT`, a test settings file); a hard-coded port is a wave 0 package that makes it configurable |
| Database | its own name, `<app>_test_<package id>` with hyphens as underscores, or a file under `$TMP/drive-<repo>-<package id>/` for a file database | the brief's commands create it from the committed schema or migrations and drop it at the end; never the shared development database |
| Simulator | a clone of the base device: `xcrun simctl clone <base udid> drive-<package id>` | boot, test, and `xcrun simctl delete drive-<package id>` in the same command; the udid goes in the report |
| Build output | `$TMP/drive-<repo>-<package id>/build` | whenever the toolchain holds a global build lock or cache |

At integration, before the full gates, confirm each package's runtime is gone
(`xcrun simctl list devices | grep drive-`, the database list, `lsof -i :<port>`) and remove what is
left. The full gates then run once on the project's default port, database, and device.

## 6. Brief and report

`templates/package-brief.md` and `templates/package-report.schema.json` are authoritative. The
brief carries: **Why** (the larger goal, who it serves, what this package enables); **Repository
root** as an absolute path; **Goal** in user-visible terms; **Claim** (STATUS key and claim words);
**Inputs you rely on** (merged files and design sections, read-only); **Contract** (shapes others
code against; a needed change means `blocked`, because a contract change is its own package);
**Files you own**; **Files you must not touch**; **Tests to make pass** (the TESTPLAN.md rows,
refutation first, and the production constraints the harness must enforce); **Commands you may
run** (the exact focused test command and any build command, each written as
`cd <root> && <command>`, and the per-package build directory); **Lessons that apply to this task**
(at most ten, verbatim); **Done means**; and **Budget**. A subagent's shell may not start in the
repository, which is why the root and the `cd` are never left implicit.

The report carries `package`, `status` (`complete`, `partial`, `blocked`), `files` (with accidental
changes marked), `tests` as `path::name`, `gates_run` (command, exit code, output tail up to 1,000
characters), `wiring_needed` (file and exact patch), `deps_requested` (name, version, reason),
`honest_gaps`, `follow_ups` (tempting improvements), `noticed_not_touched` (file, problem, one-line
reason), `concerns` (what the maker could not resolve and the assumptions it made), `summary` (at
most 1,500 characters), and `model`. Empty `gates_run` counts as `partial`; so does a missing report.
Carry `noticed_not_touched` and `concerns` into STATE.md "Discoveries" and the final report.

## 7. Integration

When the wave's makers have reported or exhausted their budgets, work alone in the tree, in this
order:

1. Save any report the maker did not write to `.drive/packages/<id>/report.json`. Mark `partial`
   and `blocked` packages for section 10.
2. Audit paths: compare `git status --porcelain` with each report's `files` and the ownership
   globs. For every change outside its package's globs, marked "accidental", or claimed by no
   report, save
   `git diff -- <path> > .drive/local/logs/drift-<id>.patch`, revert it, and note the drift on the
   package row.
3. Apply each `complete` package's `wiring_needed`, one package at a time. Install all
   `deps_requested` in one command so the lockfile changes once.
4. Run the full gates (build, type check, lint, whole test suite) plus at least one check against a
   real runtime rather than a shim, and print the `DRIVE · VERIFY` block.
5. Green: commit per package, staging by explicit path only that package's `files`, the wiring you
   applied for it, the frozen tests it turns green, and its `.drive/packages/<id>/report.json`. Never
   run `git add -A`, `git add .`, or `git add .drive` while any agent is running: a directory-wide add
   takes whatever another agent has written and not yet committed, and one run swept a verifier's
   uncommitted verdict rewrite into a package commit that way. Message `<type>(<area>): <claim words> [pkg <id>]`. Record the
   sha in `index.md`.
6. Red: map each failing test to its owning package by path and send that package to a fix round
   with the command and output tail. Commit nothing red. Fix red in a wiring seam yourself.
7. Run the orphan audit, `$DRIVE lint --stop`. It must report no worktree, run branch, or
   uncommitted path created during the run; it compares against `.drive/local/baseline.json`, so the
   owner's pre-existing worktrees, branches, and dirty files are never findings. Remove or commit
   only what it names, and fix any other finding it prints before the verifier round.
8. Only then spawn verifiers. A verdict about an uncommitted tree describes a state that can change
   under it.

A wave running longer than about an hour may commit one `complete` package early, staging only its
reported paths after its own test command passes; the full gates still run before any verifier.

## 8. Verification

**The unit follows size** (`references/verification.md` section 2). At S one verifier covers the run.
At M one handoff covers a wave once its packages are integrated and committed, split into as few
handoffs as the budget line allows, and a package carrying an `auth`, money, or data-loss claim is
verified alone. Per-package handoffs are the default only at L and XL.

**The handoff.** After the packages it covers are committed, build `.drive/handoffs/<unit>.md`, or
`<unit>-r<n>.md` for a later round (the unit is the package id, or `wave-<n>` for a wave handoff), from
the handoff template: the repository root as an absolute path, brief path, claim,
commit range, changed files taken from git, wiring items, validation commands written as
`cd <root> && <command>`, the lessons list, and the verdict schema path. It carries nothing from the
maker's summary, gaps, or reasoning. Spawn `drive:verifier` with the handoff; a wave's verifiers are
read-only and may run as parallel background calls. A package handoff's verifier writes its verdict under the
package's claim key, `.drive/proofs/<claim key>/r<n>/verdict.json`, against
`templates/verdict.schema.json`, so the STATUS row's `verdict:` token and the proof directory share one
key; a wave handoff's verifier writes `.drive/proofs/wave-<n>/r<m>/verdict.json` listing each claim key
in `claims[]`, and every STATUS row it covers names that file. A changed file outside the ownership globs is a `blocking` gap
whatever its quality. Only a passing verdict moves a STATUS row to Local Proof or above, and only one
the verifier wrote itself: drive's hooks record its hash in the provenance ledger when the verifier
stops, and the lint refuses a verdict file you copied, edited, or wrote.

**The seams.** At L and XL one more `drive:verifier` per wave checks the seams: consumers against their contract
package, every wiring line, and, for each shim or fake the wave introduced, where it is kinder
than production. It re-runs the full gates rather than trusting your transcript. At M the wave handoff covers the
seams itself. Then commit the
wave's STATUS rows as `chore(drive): wave <n> status`.

**Rounds.** A failing verdict returns each package whose claims hold a confirmed blocking gap, with the
verdict's `for_maker` text. Limits, as
SKILL.md section 5 sets them: `fix` 2; `feature` and `report` 3; `publish` 3 per phase gate; `build`
3 per milestone plus 2 final; `move` 3 per phase and 4 at cutover; `operate` 2 per observed step. A blocking gap that returns after a fix needs an investigation record before
more code changes. A dispute with a verifier goes once to `drive:auditor` with
`.drive/reviews/<date>-dispute-<key>.md`; it rules `defect`, `not_a_defect`, or `rubric_ambiguous`,
and you write the DECISIONS.md entry from the ruling (`references/verification.md` section 6).

## 9. Sizing

| Size | Packages | Makers per wave | Verification | Read-only fan-outs |
|---|---|---|---|---|
| XS | none | none | commit body records claim and evidence | none |
| S | 1 | 1 | one verifier | up to 3 investigators or researchers |
| M | 2 to 6 | up to 5 | one verifier per wave, covering the seams; a package with an auth, money, or data-loss claim verified alone | one review panel if the shape calls for it |
| L | 6 to 20 | up to 8 | a verifier per package and one per wave on the seams, plus a review panel per milestone | one Workflow per phase |
| XL | more than 20 | up to 8 | as L | one Workflow per phase or subsystem |

Read-only fan-outs may run up to the Workflow cap of 16 concurrent agents. Keep each Workflow under
the default size guideline of 15 agents where the job allows and always under the 25-agent,
1.5-million-token warning; split a larger review by subsystem and read each result before writing
the next. Your context cannot be re-spawned: keep status lines and paths, never contents; never ask
a maker for a diff or a log; after compaction re-read `index.md` and the reports from disk.

## 10. Package failure

| Outcome | Action |
|---|---|
| `partial` (turn limit, budget, missing report) | Continue it once with the exact remaining items: resume the same agent with `SendMessage` when its id is still valid in this session, which keeps its cache; after a resume or compaction, re-dispatch a fresh agent from the brief, which tells it to report work already present. Either way it is one workaround ledger row. Partial again: re-scope. A third attempt with the same brief is forbidden. |
| `blocked` on a dependency | Install it at integration; the package re-runs next wave. |
| `blocked` on contract ambiguity | Decide and record the decision with its undo in DECISIONS.md; have `drive:architect` specify the change in DESIGN.md section 4; run the change as its own `drive:implementer` package that updates `contracts/`, regenerates consumers, and runs both contract suites; commit it as `contract: <change in words>`; re-brief every package that consumes it. |
| `blocked` on the environment | Record the exact command a person would need under Open failures. Never fake it. |
| Verifier failed it twice | Re-run once with `model: "opus"`, a fresh agent, and a brief saying what was tried and what the verdicts found. Failing again, record an open failure and continue. |
| Poisoned (breaks the tree, not fixable in one round) | Save its diff under `.drive/local/logs/`, revert its reported files, mark it `failed`, move dependents to a later wave. Siblings still integrate. |
| The same workaround needed a second time | Stop that line and open an investigation record. |

A package never blocks its wave. A classifier decline is not a package failure; use `safety.md`.

## 11. The worktree lane

Use a worktree for three things only: an experiment arm whose losers are discarded, a bisect, and a
hypothesis probe that needs a code change. Never for an ordinary package, a package that wants a
shared file (give the file to the integrator), or feature work on an existing product, where a
fresh checkout's dependency drift produces phantom failures.

**The harness will not merge for you.** A worktree from `isolation: worktree` is removed
automatically only if the subagent changed nothing. One with changes stays on disk, the periodic
sweep keeps any worktree with changed files or unpushed commits (exactly a finished, unmerged
package), nothing merges it back, and headless runs clean up nothing. Never set
`isolation: worktree` on an agent that edits; create worktrees yourself and own their end.

**Create** from the repository root after committing everything the arm must see, as a detached
worktree, so no branch exists to leave behind. Install dependencies inside it and name its build
directory. The arm's brief states `$WT` as its repository root, owns `$WT/**`, and writes every
command as `cd "$WT" && <command>`. Record the path and base sha under "In flight". The guard holds
you and every agent to this form: it refuses `git worktree add` without `--detach` or outside a
scratch directory (`/private/tmp`, `/tmp`, or `$TMPDIR`) and any `-b`, `-B`, or `--orphan`. In the
shared checkout and in every worktree of this repository, detached ones under a scratch directory
included, it refuses you and every agent any command that creates, renames, or force-moves a branch,
creates or deletes a tag, or moves a branch ref or HEAD; it refuses every `git push` from any
directory; and it refuses the main thread switching branches, `git reset --hard`, a rebase, and, while a run is active, `git stash` other than `list` and `show`, `git clean` other than a dry run, `git commit --amend`, `git reset` to a commit other than `HEAD` (`git reset`, `git reset HEAD`, and `git reset -- <paths>` still unstage), and `git update-ref HEAD`. Inside a detached worktree, commit only on its detached HEAD. The main thread deletes a branch only with
`git branch -d <branch>`, never `-D` or `-f`, and removes a worktree with `git worktree remove <path>`,
each only when `.drive/local/baseline.json` does not list it, so the owner's pre-existing branches
and worktrees are refused.

```bash
SLUG=<arm-slug>; ROOT=$(git rev-parse --show-toplevel); REPO=$(basename "$ROOT")
WT="${TMPDIR:-/tmp}/drive-$REPO-$SLUG"
git -C "$ROOT" worktree add --detach "$WT" HEAD
```

**Commit, then land the winner.** The maker never runs git; you commit its reported paths inside the
worktree, on its detached HEAD. Record `SHA` (the arm's HEAD) and `PRE` (the main checkout's HEAD) in
STATE.md before landing. Run `$DRIVE worktree-land <worktree path> <sha>` from the main checkout; it
takes the worktree's path, never a branch name. It refuses when run inside a worktree, when the path
is not a registered worktree, when the worktree's HEAD moved after the sha you recorded (exit 2), when
either checkout has uncommitted changes (`.drive/local/` aside), when the main checkout is on a
detached HEAD or on a branch other than the one `.drive/local/baseline.json` recorded, when the
worktree lies outside a scratch directory and `.claude/worktrees/` (exit 2), and when the arm holds no
new commits. Otherwise it cherry-picks the arm's commits since its merge base onto the current branch,
removes the worktree with `--force`, prunes, deletes the arm's branch only when it is a `drive/*`
branch, and prints the undo, `git revert --no-edit <PRE>..HEAD`. When the commits do not apply cleanly it aborts the cherry-pick and keeps the worktree:
a conflict deeper than an import block or a registration line is a decomposition error, so re-scope.

```bash
git -C "$WT" add -- <paths from the report> && git -C "$WT" commit -m "experiment($SLUG): <approach>"
SHA=$(git -C "$WT" rev-parse HEAD) && PRE=$(git -C "$ROOT" rev-parse HEAD)
cd "$ROOT" && $DRIVE worktree-land "$WT" "$SHA"
```

Shell variables do not survive between Bash calls, so run each block as one command or re-derive
`ROOT` and `WT` at its start. Run the full gates on the current branch. On red,
`git revert --no-edit "$PRE"..HEAD` and treat the arm as failed.

**Remove losers** in the same step, after recording each loser's sha and why it lost in RESEARCH.md:
`git -C "$ROOT" worktree remove --force "${WT_LOSER:?}" && git -C "$ROOT" worktree prune`.

**Bisect** in a detached worktree, run by `drive:investigator`. The reproduction command exits 0
for good, 1 to 124 for bad, 125 to skip; copy the culprit and its evidence into HUNT.md.

```bash
ROOT=<absolute repository root>; SLUG=<slug>; REPO=$(basename "$ROOT")
WT="${TMPDIR:-/tmp}/drive-$REPO-bisect-$SLUG"; git -C "$ROOT" worktree add --detach "$WT" HEAD
( cd "$WT" && git bisect start <bad-sha> <good-sha> && git bisect run <repro command>; \
  git bisect log > "$ROOT/.drive/local/logs/bisect-$SLUG.log"; git bisect reset )
git -C "$ROOT" worktree remove --force "${WT:?}" && git -C "$ROOT" worktree prune
```

**Hypothesis probes** use the same detached form; the worktree is removed whether or not the
hypothesis survives, and only the confirmed fix is applied in the shared checkout by the `fix` phase.

## 12. Experiments

Run alternatives in parallel only for a design decision reading cannot settle, a performance
approach with a benchmark, or competing hypotheses for a deep bug; otherwise one maker and a
verifier cost less. Give two or three arms the same goal, acceptance tests, and benchmark command,
each with one distinct approach constraint. Run them in worktrees as background calls, commit each,
and record its sha, benchmark output, and a one-paragraph rationale. A fresh judge that authored no
arm receives the rubric, tests, numbers, and worktree paths, and must name the deciding evidence.
Land the winner, remove the losers in the same step, and record the comparison in RESEARCH.md. An
idea worth keeping from a losing arm becomes its own small package, briefed and verified like any
other, never a paste into the winner at landing. When the arms disagree on the shape of the answer
rather than its quality, the goal or the acceptance tests left the shape open: record the
clarification in DECISIONS.md and re-run the arms against it instead of choosing.

| Decided by | Judge |
|---|---|
| Tests and benchmark numbers | `drive:verifier`, re-running the benchmark in each worktree |
| Design trade-offs needing judgment | `drive:auditor`, once |
| Visual direction for `ui` work | `drive:ui-reviewer`, capturing and scoring every arm against the design contract |
| Bug hypotheses | `drive:investigator` arms state predictions; `drive:verifier` runs the discriminating checks |

## 13. Review panel template

Each claim gets three lenses. One `drive:grader` answers a checklist question: is the cited evidence
present and was it run. Two `drive:verifier` agents try to refute the claim through the kindness and
defect lenses, because those are judgment and never go to the grader (`models.md` section 5). A
fresh `drive:verifier` settles every split, unknown, or missing vote. Every lens is read-only and
writes no file; the script cannot touch files either, so pass the repository root and the claims in
`args` and write the returned results to `.drive/reviews/<date>-panel-<slug>.md`. Panel output is
review evidence and a source of fix packages; a STATUS rung still moves only through a verifier round
with its own `verdict.json`.

Each claim costs three lens agents and a settling verifier when the votes split. They are reviewers,
so the lint's subagent count, which counts maker spawns only, never sees them, but the dollar envelope
does (`models.md` section 7). Panel at most about three claims in an M run. With
more claims than that, panel the riskiest ones (live rows, auth rows, rows whose tests use doubles)
and record in the review file which claims were sampled and why. The script needs the Workflow tool
(section 4); without it, run the same lenses as background Agent calls.

```javascript
export const meta = {
  name: 'drive-review-panel',
  description: 'A grader checks the evidence and two verifiers try to refute each claim; a fresh verifier settles splits, unknowns, and gaps',
  phases: [{ title: 'Refute', detail: 'one grader and two verifiers per claim' }, { title: 'Decide', detail: 'fresh verifier on unsettled claims' }],
}
// args: { root: '<absolute repository root>', claims: [{ key, claim, handoff, evidence: ['<path>', ...] }] }
const LENSES = [
  { agentType: 'drive:grader', name: 'evidence', question:
    'Does every evidence path exist, does each cited test:<path>::<name> and severe:<path>::<name> appear in its file, ' +
    'and does commands.log show each cited test command run with exit 0? Answer holds only when every item is present.' },
  { agentType: 'drive:verifier', name: 'kindness', question:
    'Where is the test harness kinder than production, and would the cited tests still pass against the real system?' },
  { agentType: 'drive:verifier', name: 'defect', question:
    'Would the cited tests fail if the implementation were wrong? Name a plausible defect they would miss.' },
]
const FINDING = { type: 'object', required: ['what', 'where', 'severity', 'confidence'], properties: {
  what: { type: 'string' }, where: { type: 'string' }, severity: { enum: ['blocking', 'should_fix', 'note'] }, confidence: { type: 'number' } } }
const VOTE = { type: 'object', required: ['result', 'findings', 'model'], properties: {
  result: { enum: ['holds', 'refuted', 'unknown'] }, findings: { type: 'array', items: FINDING }, model: { type: 'string' } } }
const DECISION = { type: 'object', required: ['result', 'reason', 'commands', 'model'], properties: {
  result: { enum: ['holds', 'refuted', 'unverified'] }, reason: { type: 'string' },
  commands: { type: 'array', items: { type: 'string' } }, model: { type: 'string' } } }
const brief = (c) => `Repository root: ${args.root}. Run every command as cd ${args.root} && <command>.\n` +
  `Claim (${c.key}): ${c.claim}\nHandoff: ${c.handoff}\nEvidence: ${c.evidence.join(', ')}\n`

const results = await pipeline(args.claims,
  async (c) => {
    phase('Refute')
    const raw = await parallel(LENSES.map((lens) => () => agent(
      `I'm reviewing work from an autonomous build; the owner needs to know which claims really hold.\n${brief(c)}Lens: ${lens.question}\n` +
      `This is a panel lens, not a verification round: use only the files and read-only commands, write no file, and return ` +
      `the result in the schema. Report every finding with severity and confidence, including uncertain ones; filtering happens ` +
      `later. Answer unknown when evidence is missing. Prose written by another agent is not evidence. Give conclusions with ` +
      `evidence and name the model you ran as.`,
      { agentType: lens.agentType, schema: VOTE, phase: 'Refute', label: `${c.key} ${lens.name}` })))
    return { c, votes: raw.filter(Boolean), missing: raw.filter(v => !v).length }
  },
  async ({ c, votes, missing }) => {
    const holds = votes.filter(v => v.result === 'holds').length
    const refuted = votes.filter(v => v.result === 'refuted').length
    if (missing === 0 && holds === votes.length) return { key: c.key, result: 'holds', decidedBy: 'panel', votes, missing }
    if (missing === 0 && refuted === votes.length) return { key: c.key, result: 'refuted', decidedBy: 'panel', votes, missing }
    phase('Decide')
    const findings = votes.flatMap(v => v.findings.map(f => `- [${v.result}] ${f.severity} ${f.where}: ${f.what}`)).join('\n')
    const d = await agent(
      `Settle this claim. Panel: ${holds} holds, ${refuted} refuted, ${votes.length - holds - refuted} unknown, ${missing} missing.\n` +
      `${brief(c)}Findings:\n${findings}\nRun the read-only commands that decide it and list them. Write no file. Return refuted when the ` +
      `evidence cannot show that the claim holds. Give conclusions with evidence and name the model you ran as.`,
      { agentType: 'drive:verifier', schema: DECISION, phase: 'Decide', label: c.key })
    if (!d) return { key: c.key, result: 'unverified', decidedBy: 'none: verifier returned null', votes, missing }
    return { key: c.key, ...d, decidedBy: 'verifier', votes, missing }
  })

const done = results.filter(Boolean)
const count = (r) => done.filter(x => x.result === r).length
const nullVotes = done.reduce((n, x) => n + x.missing, 0)
const nullDecisions = done.filter(x => x.decidedBy.startsWith('none')).length
const noResult = args.claims.length - done.length
log(`panel: ${count('holds')} holds, ${count('refuted')} refuted, ${count('unverified') + noResult} unverified; ` +
    `null lens votes ${nullVotes}, null verifier decisions ${nullDecisions}, claims with no result ${noResult}`)
return { results: done, nullVotes, nullDecisions, noResult }
```

An `agent()` call resolves to null when it is stopped, blocked by the permission classifier, or
ends on an unrecoverable API error. A null is never a pass: the script counts every null, and a
claim without a decision is `unverified`. Copy the logged counts into the review file, and classify
more than one null in a panel as a Boundary event with `safety.md`.

## 14. Refuse these

- Two packages owning one path, or a maker editing outside its ownership.
- A swarm for a one-file bug; use one agent and one verifier.
- Makers running whole-workspace builds, lints, or test suites, or concurrent builds against a
  shared toolchain lock.
- An editing agent inside a Workflow, or `isolation: worktree` on an agent that edits.
- Merging without the full gates, or verifying an uncommitted tree.
- `git add -A`, pull requests as integration, agent teams, and `/batch`.
- A `git push` from the run; a push is an owner step named in REPORT.md's "Needed from you".
- Diffs, logs, or screenshots in your own context.
- A worktree, a branch of any name, or a package's database, simulator clone, or service created
  during the wave and still alive at its end.
- Scope items from one package's report flowing into later briefs without your decision.
- Telling a maker to double-check its work or spawn its own reviewer; you schedule verification.
