# How it works · <repository> · <area of the goal>
checked at: <short sha> on <YYYY-MM-DD> · by: drive:researcher (<model>)
re-check: `git log <short sha>..HEAD -- <paths below>` shows any change

<!-- Stay under 150 lines. Tag every statement with its evidence:
[read <path>:<line>]  the code says so
[ran `<command>`]     a command run in this checkout showed it
[git <sha or command>] history shows it
[docs <path>]         only documentation says so; not yet checked against code
[inferred from <evidence>] reasoned, not observed
Code and command output outrank docs. Written at M and above for a run with existing code; at S the
same findings go to STATE.md Verified facts. Procedure: references/research.md section 13. -->

## Purpose
<Two sentences: what this code does and for whom.> [<tag>]

## Architecture
<At most ten lines: entry points, modules, stores, external systems, and the flow> [<tag>]

## Verified commands
| Job | Exact command | Result when run | Duration |
|---|---|---|---|
| build | `<command>` | <ok, or the error> | <s> |
| focused test | `<command> <one test>` | <ok> | <s> |
| full suite | `<command>` | <passed>/<total>, <failed> failing, flaky: <names or none> | <s> |
| lint | `<command>` | <ok, or counts> | <s> |
| typecheck | `<command>` | <ok, or counts> | <s> |

Baseline: <passed>/<total> at <short sha>; failing before any change: <test names or none>.

## Drive the app
<!-- Delete when the project has no runnable app. A recipe a later session follows instead of
rediscovering it, committed with this note and proved once by running launch, doctor, one feature,
and cleanup (references/research.md section 13). One Feature line per user-facing feature. -->
Launch:  `<command>` · ready when <log line, port answering, or health response> · process ids recorded in `.drive/local/` [ran `<command>`]
Doctor:  `<read-only command>` shows the running instance is the build under test: <build stamp, version, or commit> [ran `<command>`]
Feature: <user-facing feature> · entry point <route, screen, or command> · end state <what an agent observes> [ran `<command>`]
Cleanup: `<command>` stops only the recorded process ids and leaves `.drive/proofs/` intact [ran `<command>`]

## Dialect
<!-- For each kind of thing the goal adds, the three nearest existing examples and the shape they share.
The architect copies this section into the change spec. -->
| Aspect | Pattern | Nearest examples | Evidence |
|---|---|---|---|
| <placement, naming, errors, validation, logging, config access, or tests> | <the shared shape> | `<path>`, `<path>`, `<path>` | [read <path>:<line>] |

## Data and external systems
| Store or system | Used for | Access path in code | How tests reach it (real, emulator, double) | Evidence |
|---|---|---|---|---|

## Hotspots and dead zones
- Hotspot: <path> changed <n> times in 90 days; <why it matters to the goal>. [git `git log --format= --name-only`]
- Dead zone: <path> has no callers found; <searches run>. [ran `<grep>`]

## Drift table
| Claim | Where it is made | What actually happens | Evidence | Action |
|---|---|---|---|---|
| <"run X to test"> | <README.md:12> | <X no longer exists, and tests run with Y> | [ran `X`] exit 127 | fix the doc in its own commit |

## Blast radius
Score: <small | medium | large> (small: one entry point and no external consumer; medium: several entry points or one external consumer; large: many entry points or several external consumers)
| Change point | Depends on it | How found | Covered by real tests | Risk if it breaks |
|---|---|---|---|---|
| <path or symbol> | <callers, consumers, jobs, other repositories, configuration> | [ran `<grep or gh search code>`] | <test path, or none> | <what a user or operator would see> |

## Could not verify
- <statement>: <why not: needs credentials, a device, production access, a dynamic lookup> · consequence: <claims capped, or research question slug>

## Questions raised for research
- <question> · serves: <decision> · slug: <slug>
