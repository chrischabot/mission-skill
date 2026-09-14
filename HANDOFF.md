# drive: handoff

This repository holds `/drive`, a Claude Code skill that takes a high-level goal and runs the whole
process: intake and classification, research, specification, design, test planning, parallel
implementation, independent adversarial verification, UI verification with vision, state files,
failure investigation distilled into lessons, and compounding those lessons back into the skill. It
scales from a one-line fix to a greenfield product without ceremony that does not pay for itself.

Last updated 2026-09-14 by the coordinating session.

## Where things stand

The skill is complete and committed under `skill/`: SKILL.md (the spine), twelve agent files with
pinned models, the references, shape files, domain packs and templates, `scripts/drive.py` with its
test suite, `hooks/hooks.json` (which registers the Stop gate, the guard and the snapshot hooks), the
plugin manifest, and the eval suite. `install.sh` links it as `~/.claude/skills/drive` and prints the
per-run launch settings.

Drive uses exactly three models, pinned by full ID: `claude-fable-5-1` for the orchestrator and the
final audit, `claude-opus-5` for design, verification, security, UI review and investigation, and
`claude-sonnet-5` for research, implementation and low-effort grading. No other model is selected;
`skill/scripts/tests/test_model_ids.py` fails if any shipped file says otherwise or if the price
table drifts. Prices, effort levels and the cost envelopes in `references/models.md` were checked
against the live documentation and recomputed in `research/33-model-cost-audit.md`, and recomputed
again independently in `research/34-adversarial-review.md`.

The last full review, `research/34-adversarial-review.md`, found one critical defect (the guard
refused the heredoc every reviewer uses to write its verdict), six high and a set of medium and low
findings. All of them were fixed the same day, and a second clean review of those fixes,
`research/37-fix-review.md`, found two high findings the heredoc fix had introduced (a here-string
hid the lines after it, and heredoc bodies fed to a shell or interpreter went unjudged), four medium
and six low. Those were fixed too, along with a real bug the test runs exposed: GOAL.md's reader
turned an all-digit short sha with a leading zero into a number. `research/35-code-fixes-for-docs.md`
lists every behaviour change the fixes made. The suite has 393 tests and passes on Python 3.13 and on
the macOS system Python 3.9; `selfcheck`, `lesson-check` and `claude plugin validate` pass. The eval
suite has 19 cases.

## What is not yet proven

- **No scored eval run exists.** `claude plugin eval` refuses Bash-granting cases on the machine
  where the skill was written because `~/.docker` contains symbolic links (Docker Desktop and
  OrbStack). Run the suite on a machine without that, or after moving the links, before trusting
  the graders; `skill/evals/README.md` lists each case's idle score.
- **No real run exists.** The cost envelopes are modelled. The first runs should replace them with
  recorded `total_cost_usd` figures.
- **Unverified harness facts** are listed at the end of report 34: whether a background session has
  the iOS Simulator and Browser pane tools, whether `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` in the
  `--settings` env block takes effect, and whether a subagent can invoke the bundled
  `security-review` skill.

## Where to read

- `research/00-brief.md`: the original brief, with corrections at the top. The iOS app with a
  Cloudflare backend was only ever an example of the kind of goal drive receives; no code for it
  exists or should be written.
- `research/01` to `23`: component research. `research/23-agent-skills-extraction.md` covers what
  was reused from addyosmani/agent-skills (MIT; see THIRD_PARTY_NOTICES.md).
- `research/24-synthesis.md`: the binding design record, with amendments in sections 15 to 21.
  Section 21 is the threat model: the guard makes honest mistakes fail loudly, and transcript-backed
  provenance makes tampering evident afterwards; deliberate shell obfuscation is out of scope.
- `research/25` to `32`: the drafting brief and successive review rounds.
- `research/30-compare-mission-vs-drive.md`: comparison with the earlier `mission` skill.
- `research/33-model-cost-audit.md`, `34-adversarial-review.md`, `35-code-fixes-for-docs.md`,
  `36-completion-handoff.md`, `37-fix-review.md`: the model and cost audit, the whole-project
  review, the behaviour changes it produced, the completion checklist (now done), and the review of
  the fixes.

## Checks to run after any change

```bash
python3 -m unittest discover -s skill/scripts/tests
```

```bash
python3 skill/scripts/drive.py selfcheck
```

```bash
python3 skill/scripts/drive.py lesson-check
```

```bash
claude plugin validate skill
```

The suite takes about three minutes and must also pass on the macOS system Python (3.9).
