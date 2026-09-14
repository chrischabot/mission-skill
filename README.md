# mission — a goal-to-verified-outcome execution skill for Claude Code

`mission` turns a high-level direction into a gated, role-routed execution run: intake and classification → research →
spec → design → plan → build in waves → verification → adversarial review → release → retro. It scales from "fix this
typo" (a task card and one verified check) to "build a multi-platform app" (milestones, contracts, swarms, visual and
UX verification, human batch reviews). It records state in `.mission/` in the target repo so work resumes instead of
restarting, and it turns failures into tests, controls and lessons.

## Install

```sh
cp -R skills/mission ~/.claude/skills/mission          # personal skill (this machine)
# or, for cloud / Routine / CI runs, vendor it into the repo:
cp -R skills/mission <repo>/.claude/skills/mission
```

Personal skills do not load in cloud sessions, which is why `init-mission.sh` also copies the scripts into
`<repo>/.mission/bin/`.

## Use

```text
/mission build a fashion outfit iOS app with a Cloudflare backend and native SwiftUI frontend
/mission the checkout e2e test fails ~1 in 50 runs; find the root cause and fix it
/mission add a usage dashboard to our admin app
/mission move our AI gateway from the external project into a core platform service
/mission research our market position and build a site with about, team, blog and docs
/mission autonomous: upgrade Vite 5 → 7 overnight
/mission resume · /mission status · /mission retro
```

For M/L/XL missions, switch the session to the orchestrator model first: `/model claude-fable-5-1` with medium effort.
S missions run on Opus 4.8 at high effort. Say "lean" to keep the orchestrator on Opus 4.8.

## Models

Only `claude-fable-5-1`, `claude-opus-4-8` and `claude-sonnet-4-6`, pinned by full ID. No Haiku: roles that would use it
run on Sonnet 4.6 at low effort. Effort can only be set in agent frontmatter, so the skill ships 12 roster agents
(`agents/`, installed into `<repo>/.claude/agents/`), one per model·effort·permission profile. Opus 5 and Sonnet 5 exist
and the `opus`/`sonnet` aliases resolve to them on the Anthropic API. To change the model set, edit
`references/conventions.md` §6–§7, the agent files, and the tables in `scripts/preflight.sh`.

## Layout

| Path | What |
|---|---|
| `SKILL.md` | Orchestrator instructions: invariants, phases and gates, build wave, stop rules, conditionals index, reference map |
| `references/conventions.md` | Canonical names: roles, `.mission/` layout, IDs, states, class scoring, models, agent roster, profiles, branches |
| `references/shapes-and-scope.md` | 13 shapes, classification procedure, class toggles, trait → obligation tables, per-shape pipelines, worked examples |
| `references/orchestration.md` | Phase gates, loops and stop rules, briefs, long-running and headless runs, guardrails, classifier boundary |
| `references/models-and-cost.md` | Role → agent matrix, escalation ladder, downgrade guards, budgets, caching, preflight, profiles |
| `references/spec-and-design.md` | Intake questions, charter, requirements registry, backend/frontend/migration designs, ADRs, spec review |
| `references/testing.md` | Traceable hard tests, anti-bloat and anti-cheating rules, backend and E2E testing, per-shape gate tables |
| `references/frontend-verification.md` | Deterministic layout/a11y checks, screenshot matrices, vision verifier, design rubric, walkthroughs, human batch |
| `references/review.md` | Maker/checker separation, trigger-selected adversarial lenses, refutation, dispositions, convergence caps |
| `references/debugging.md` | Reproduce → isolate → hypothesis ledger → confirm → prove → sweep → convert; process-failure taxonomy |
| `references/swarms.md` | When to fan out, patterns, worktrees, ownership, integration, lane contracts, headless waves |
| `references/research.md` | Research triggers, question cards, evidence grading, fact-checking, positioning, public-claims standard |
| `references/memory-and-lessons.md` | STATE/STATUS discipline, hooks, curator pass, lesson promotion into this skill |
| `references/lessons.md` | Promoted cross-project lessons (seeded with 7) |
| `templates/` | Files copied into `.mission/` (charter, spec, registry, acceptance.json, STATUS, STATE, briefs, prompts, rubrics …) |
| `agents/` | Roster agent definitions |
| `scripts/` | `init-mission.sh`, `probe-signals.sh`, `preflight.sh`, `check.sh`, `validate-registry.py`, memory hooks and lint, frozen-path hook and manifest, test-diff grep, flake runner, ownership check, headless wave runner, geometry probe |
| `evals/evals.json` | Eval prompts with assertions for the main shapes |

## Provenance

Synthesized from twelve research reports in `research/mission-skill/` (orchestration, model routing and cost, spec and
design, testing, frontend/visual/UX verification, adversarial review, memory, failure investigation, swarms, research,
project shapes, and practice evidence from the arcwell project), read alongside the source post. The reports separate
verified claims from unverified ones. The skill's "Unverified harness details" sections list what still needs checking
in a live Claude Code session: hook exit-code semantics, the permission rule grammar, per-call worktree isolation, and
`--max-budget-usd`.

## Status of verification

The sandbox was unavailable while the scripts were written, so no script has been executed yet. Before relying on
them, run:

```sh
for f in skills/mission/scripts/*.sh; do bash -n "$f"; done
python3 -m py_compile skills/mission/scripts/validate-registry.py
node --check skills/mission/scripts/geometry-probe.js
python3 -m json.tool skills/mission/templates/acceptance.json
python3 -m json.tool skills/mission/templates/settings.hooks.json
python3 -m json.tool skills/mission/templates/settings.guardrails.json
python3 -m json.tool skills/mission/evals/evals.json
bash skills/mission/scripts/protect-frozen.sh --self-test
bash skills/mission/scripts/flake-runs.sh --p 0.02 --dry-run        # expect 149
python3 skills/mission/scripts/validate-registry.py --registry skills/mission/templates/requirements.yaml --no-pyyaml
mkdir -p /tmp/mission-smoke && bash skills/mission/scripts/init-mission.sh --class M --repo /tmp/mission-smoke --dry-run
```
