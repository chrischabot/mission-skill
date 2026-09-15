# GOAL · <goal slug>
goal: "<verbatim prompt>"
live means: <deployed host, device and backend, clean install, or out of scope: reason>
budget: <turns> turns · <subagents> subagents · <wall clock> · <usd envelope>

<!-- Written at intake and committed as `drive(intake): <slug>` before any other work. The slug names
the deliverable in one to three words (linkkeeper), passed to drive.py init as --slug, never the goal
sentence. The usd envelope comes from references/models.md section 7. After that
the goal line, the restate block, and the intake plan never change: tick plan lines, append to
reclassifications, append under Re-plans. Every restate value is quoted from the goal in double
quotes or begins with "assumption:". A run with sub-goals repeats "Classification · <sub-goal slug>"
and "Plan · <sub-goal slug>" headings, in run order. probe.repos lists, as absolute paths, every
other repository the run writes to (a move's old service, a second surface); the write guard and the
launch settings allow those and nothing else outside probe.repo. A probe command of `none` means the
project has no such command, and `test_command: none` means no suite, so verdicts need no full-suite
run; replacing a `none` with a real command later needs a DECISIONS.md entry naming it. With
sub-goals, every STATUS row carries a `sub:<sub-goal slug>` token. The budget's subagent figure, the
number directly before "subagents", counts maker spawns only (implementer, writer, designer,
architect, researcher); the lint warns past it and fails past twice it until DECISIONS.md records the
overrun with a Narrows line. -->


## Restate
- outcome: <outcome quoted from the goal, or assumption: ...>
- user: <user quoted from the goal, or assumption: ...>
- why now: <why now quoted from the goal, or assumption: ...>
- success: <success quoted from the goal, or assumption: ...>
- constraints: <constraints quoted from the goal, or assumption: ...>
- out of scope: <out of scope quoted from the goal, or assumption: ...>

## Classification
```yaml
shape: <build|feature|fix|move|publish|report|operate>
variant: null
size: <S|M|L|XL>
size_set_by: "<the structural trigger that set the size>"
traits: { confirmed: [], suspected: [] }
suspected_because: {}
probe:
  repo: <absolute repository path>
  stacks: []
  build_command: "<exact build command, or none>"
  focused_test_command: "<exact command that runs one test, or none>"
  test_command: "<exact full-suite command, or none when the project has no suite>"
  baseline_sha: "<short sha>"
  claude_md: <present or absent>
  system_tools: none
assumptions: []
not_asked: []
classified_at: <ISO UTC>
reclassifications: []
```

## Plan
- [ ] intake · artifact: .drive/GOAL.md · exit: committed as drive(intake): <goal slug> · checker: orchestrator
- [ ] report · artifact: .drive/REPORT.md · exit: final audit go; drive.py lint --final passes · checker: verifier

## Re-plans
