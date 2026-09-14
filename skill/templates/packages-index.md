# Packages · <goal slug>

<!-- Written to .drive/packages/index.md at the decompose gate and updated after every report and
verdict, so a resumed session continues from the file. One row per package. status is planned,
running, complete, partial, blocked, integrated, verified, or failed. owns repeats the globs under
the brief's "Files you own"; no path may fall under two packages or under Integrator-owned (two globs
overlap when either literal prefix before the first * starts with the other). drive.py lint
--gate decompose runs that check. -->

| id | wave | claim key | owns | depends on | hard | status |
|----|------|-----------|------|------------|------|--------|
| <package id> | <wave number> | <claim key> | `<glob>` | <package ids or none> | <yes or no> | planned |

## Integrator-owned
- `.drive/`
- `<entry point, manifest, lockfile, generated code, build file, or shared configuration>`
