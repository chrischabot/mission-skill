# Third-party notices

The drive skill adapts material from the projects below. Files that lift a substantial passage nearly verbatim name the source file in a one-line header.

## addyosmani/agent-skills

Source: https://github.com/addyosmani/agent-skills (commit be4e44a, 2026-09-11). Adapted: constraint floor and guard, keep-or-revert for performance work, idempotency and expand-and-contract guidance, the derived-path deletion check, measurement honesty, the observability evidence standard, the eval harness shape, the excuses-and-red-flags skill format, and several checklists.

Files adapted in drive's own words (no verbatim lifts): `skills/security-and-hardening/SKILL.md`, `references/security-checklist.md`, `skills/api-and-interface-design/SKILL.md`, `agents/security-auditor.md`, `skills/observability-and-instrumentation/SKILL.md`, `references/observability-checklist.md`, `skills/constraint-driven-development/`, `skills/performance-optimization/`, `skills/deprecation-and-migration/`, `agents/web-performance-auditor.md`, `evals/`.

```
MIT License

Copyright (c) 2025 Addy Osmani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## cursor/plugins: pstack

Source: https://github.com/cursor/plugins, directory `pstack/` (commit c1c0a32, 2026-09-14). Evaluated in `research/38-pstack-evaluation.md`. Adapted in drive's own words (no verbatim lifts): three more shapes of a test that observes nothing, hypothesis families and benchmark sensitivity for performance work, interface-depth red flags, a stale-state bug class, the order of strength for a lesson's check, UI reproduction through the reported path, a pilot package before a wave of similar packages, codemods proved against a hand edit, a recorded recipe for driving the app, the shared premise of failed fixes, the one fact a change is safe because of, whole sentences in run output, a file-size row in the feature and build rubrics, the signs that a design rather than a package is wrong, caller usage before types, retro and lesson-auditor questions on passes for the wrong reason and on durability, comments that give a reason, handling of divergent experiment arms, and history as evidence of when code changed rather than of why. The four design red flags are John Ousterhout's ideas from *A Philosophy of Software Design*.

Which drive files took which pstack material:

- `skill/references/testing.md`, `skill/agents/severe-tester.md`: `skills/principle-test-behavior-not-implementation/SKILL.md`.
- `skill/references/shapes/fix.md`, `skill/templates/HUNT.md`, `skill/references/verification.md` (the same-scenario comparison): `skills/poteto-mode/playbooks/perf-issue.md`, `playbooks/hillclimb.md`, `playbooks/multi-phase-plan.md`, `skills/principle-fix-root-causes/SKILL.md`, `automations/benny/skills/reproduce-and-fix-issues/SKILL.md` and `references/control-adapter.md`, `skills/why/references/epistemics.md`.
- `skill/references/ui-verification.md`, `skill/agents/researcher.md`: `automations/benny/skills/reproduce-and-fix-issues/`, `skills/create-verification-skill/SKILL.md`, `skills/maintain-verification-skill/SKILL.md`, `skills/why/references/epistemics.md` and `investigator-prompt.md`.
- `skill/references/design.md`, `skill/references/verification.md` (the signs of a wrong design): `skills/architect/SKILL.md`, `skills/architect/references/design-red-flags.md` and `rationale-template.md`.
- `skill/references/lessons.md`, `skill/references/lessons/rejected.md`, `skill/agents/auditor.md`, `skill/agents/investigator.md`, `skill/templates/retro.md`, `skill/templates/investigation.md`: `skills/principle-encode-lessons-in-structure/SKILL.md`, `skills/principle-attack-the-premise/SKILL.md`, `skills/reflect/references/divergent-reviewer.md` and `synthesizer.md`.
- `skill/references/parallel.md`: `skills/poteto-mode/playbooks/orchestrate.md`, `skills/arena/SKILL.md`.
- `skill/references/shapes/move.md`, `skill/agents/implementer.md`, `skill/agents/verifier.md`: `skills/principle-build-the-lever/SKILL.md`, `skills/no-comments/SKILL.md`, `agents/comment-sicko.md`, `skills/why/references/epistemics.md`.
- `skill/agents/writer.md`, `skill/references/state-files.md`: `skills/unslop/SKILL.md` (the rule on over-compression).
- `skill/templates/how-it-works.md`, `skill/references/research.md`, `skill/references/safety.md`: `skills/create-verification-skill/SKILL.md`, `skills/maintain-verification-skill/SKILL.md`, `skills/why/references/epistemics.md` and `investigator-prompt.md`.
- `skill/templates/rubrics/feature.md`, `skill/templates/rubrics/build.md`: `skills/interrogate/references/code-quality-review.md`.
- `skill/agents/architect.md`, `skill/templates/change-spec.md`, `skill/references/shapes/feature.md`: `skills/blast-radius/SKILL.md`.

```
MIT License

Copyright (c) 2026 Lauren Tan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
