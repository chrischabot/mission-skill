# The lessons store

These files are drive's procedural memory across projects: rules learned from verified failures
that apply whatever the stack. The orchestrator reads `general.md` in full at every intake and
resume above XS, and quotes the rules that apply, at most ten, verbatim in every worker brief under
"Lessons that apply to this task". The full procedure that fills, checks, proves, and prunes this
store is in `references/lessons.md`.

| File | Holds | Cap |
|---|---|---|
| `general.md` | rules about how to run projects, one entry per rule in the lesson template | 60 entries or 16,000 characters |
| `learned.md` | rules lean runs verified and promoted with `drive.py promote`, each with Because, Verified by, Source, and Seen, appended and committed alone without the dedupe and audit below | 80 entries |
| `retired.md` | tombstones for rules merged, superseded, retired as unused, or retired because their eval passes without drive | none |
| `rejected.md` | candidate rules the auditor rejected, so a false lesson is not proposed twice | none |

Platform constraints do not live here. They go to the Learned constraints section of
`references/domains/<domain>.md`, and skill or tool quirks to the Learned constraints section of
`references/capabilities.md`, each capped at 40 entries. Project facts stay in the project's own
`.drive/LESSONS.md`. Owner preferences go to the run's report, and to auto memory only in an
interactive session.

Each entry uses the template in `templates/lesson.md`: a one-sentence rule as the heading, then
When, Do, Because, Check, Verified by, Applies to, Not for, and Seen. Nothing refers to a lesson by
number; the heading is its name. Evidence lines carry no project names, hostnames, home-directory
paths, tokens, or personal data.

A lesson arrives only after an investigation verified its mechanism, `drive:grader` classified it
against the existing entries, `drive:auditor` accepted it, and, where the situation can be set up as
an eval case, that case scored below 1.0 without the rule and 1.0 with it (or is committed and marked
not yet run with the reason). `drive.py lesson-check` must pass, and `drive.py lesson-commit` records
it as one commit, `lesson(<scope>): <rule heading>`, whose body carries `Project: <repository
directory name>` and `Run: <goal slug>` so consolidation can count sightings across projects and
runs. A cap blocks new entries until consolidation runs, and consolidation runs immediately.

Work in the skill directory's real path, never through a path under `~/.claude`, which Claude Code
protects. To see what changed and why, from any shell, with `<skill>` the skill directory:

```bash
git -C "$(cd -P <skill> && pwd -P)" log --oneline -- references/lessons references/domains references/capabilities.md evals
```

To undo any lesson, consolidation, or retirement, revert its commit:

```bash
git -C "$(cd -P <skill> && pwd -P)" revert <sha>
```

A retired rule can also be restored by copying its entry back from `retired.md` in a commit that
says why. Removing or weakening a rule needs consolidation evidence; adding a verified rule is an
ordinary commit.
