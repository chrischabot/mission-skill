# CONSTRAINTS · <project>
measured: <short sha> · <YYYY-MM-DD> · by <agent> · rules: references/testing.md section 8
guard: `drive.py guard`, which compares with GOAL.md's baseline_sha, before every integration commit and at the final audit · exit 0 clean, 1 violation, 2 could not run (a failure)
project's own constraints: <path of the repository's existing constraints or quality configuration | none>

<!-- Required at size M and above. Written at archaeology for existing code, and after wave 0 lands for
a greenfield build (nothing exists to measure before); committed before the next integration commit in
every case. With no owner target, measure today and record that value. Never
record a threshold the codebase fails today. Change a row only in a commit of its own, with the
measurement output and the reason; loosening also needs a DECISIONS.md entry in that commit. The guard
compares numbers only in the measured, tolerance, and target columns of the Enforced table and never
compares dates. Delete guidance comments once the rows are filled. -->

## Floor
These hold without a row and are never relaxed:
- No added suppression comments (for example `@ts-ignore`, `eslint-disable`, `# noqa`, `swiftlint:disable`, `#[allow(...)]`, `//nolint`) and no added skips.
- No assertion removed from a test file that still exists.
- No stubs, placeholder throws, unimplemented markers, or empty catch blocks in production code.
- No secrets in any tracked file.
- This file is never loosened to let a change pass.

## Enforced
<!-- One row per rule. The command prints the value the row compares. Direction is "must not fall" or
"must not grow". Tolerance absorbs drift from unrelated files. At least one row's verdict must come from
outside the project's own tests: a vulnerability database, an accessibility engine, or the platform's
limits probe. -->

| rule | command | measured | direction | tolerance | target | reason | measured at |
|---|---|---|---|---|---|---|---|
| Type errors | `<exact command that prints the error count>` | <n> | must not grow | 0 | 0 | <why> | <short sha> · <YYYY-MM-DD> |
| Lint violations | `<exact command that prints the count>` | <n> | must not grow | 0 | <owner target or none> | <why> | <short sha> · <YYYY-MM-DD> |
| Test suite passing | `<exact command that prints passed and total>` | <passed>/<total> | must not fall | 0 | all | <why> | <short sha> · <YYYY-MM-DD> |
| Dependency vulnerabilities at high or above | `<scanner command>` | <n> | must not grow | 0 | 0 | outside check: vulnerability database | <short sha> · <YYYY-MM-DD> |
| <rule in words> | `<exact command>` | <value with unit> | <must not fall or must not grow> | <value with unit> | <owner target or none> | <why, and the target when today's value falls short of it> | <short sha> · <YYYY-MM-DD> |

## Measured only
<!-- Values recorded with a direction but not enforced by the guard, such as a bundle size on a project
with no budget yet. Promote a row to Enforced in its own commit. -->

| metric | command | measured | direction | measured at |
|---|---|---|---|---|
| <metric in words> | `<exact command>` | <value with unit> | <must not fall or must not grow> | <short sha> · <YYYY-MM-DD> |

## Exceptions
<!-- A suppression, skip, or relaxed rule allowed for a named path, including the skip of a quarantined
flaky test (references/testing.md section 10, with the STATE.md ticket as the reason). An exception
without a DECISIONS.md entry is unrecorded, and the guard blocks it. The path cell may name several
paths or globs separated by commas; name the files rather than widening a glob. -->

| rule | path | reason | undo | decision |
|---|---|---|---|---|
| <rule> | `<path or glob>` | <why this path cannot meet the rule now> | <the change that removes the exception> | DECISIONS.md <YYYY-MM-DD>-<slug> |

## Changes
<!-- Append only. One line per row change, matching its own commit. -->

| date | rule | old | new | tighter or looser | evidence | commit | decision |
|---|---|---|---|---|---|---|---|
| <YYYY-MM-DD> | <rule> | <value> | <value> | <tighter or looser> | <path of the measurement output> | <short sha> | <DECISIONS.md slug, required when looser> |
