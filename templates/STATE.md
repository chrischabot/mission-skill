# STATE · <project> · mission: <one-line goal>

<!-- Template: skills/mission/templates/STATE.md → .mission/STATE.md (M+). WHAT IS TRUE.
     Owner: orchestrator only. Workers return memory_delta blocks (templates/memory-delta.md); merge them by ID.
     Edit by ID (add / modify / supersede). Never rewrite or "condense" this file wholesale (curator pass instead).
     Budget: ≤150 lines. Any entry body >4 lines → investigations/<id>.md. Lint: .mission/bin/memory-lint.sh
     Task progress, gates and board live in STATUS.md, decisions in DECISIONS.md. A fact in two files is a bug. -->

## Resume
<!-- Stage 5. Overwrite every session and before compaction/reset. A fresh agent with no chat history must be able to
     act on it. The SessionStart hook prints this section. -->
- Updated: <YYYY-MM-DDTHH:MMZ> by <orchestrator model id @ effort> (session s<N>)
- Branch/worktree: <branch> @ <worktree path> (HEAD <short sha>)
- Next action: `<runnable command>` ; expect <result>
- Re-verify last change: `<command>` (was green at <sha>)
- Blocked on: <O-NNN | human queue item in STATUS.md | nothing>
- Read first: <R-NNN, L-NNN, investigations/O-NNN.md, other paths>

## Rules index
<!-- Stage 4 index, printed by the hook. One line per rule, full entry under General rules. Multi-surface missions tag
     the surface. Format:
- R-NNN [<surface>] <imperative rule in ≤15 words> · conf: <low|medium|high>
-->

## Verified facts
<!-- Stage 3. No entry without Evidence + Level + verified date (lint). Unverified → Hypotheses.
     recheck-by: 90 days default, 30 days toolchain facts, 14 days production/infra state, decommission date for
     facts about a system being migrated away. Expired → treat as hypothesis until re-verified. Format:
- F-NNN · <claim> · conf: <low|medium|high> · verified <YYYY-MM-DD> · recheck-by <YYYY-MM-DD>
  Evidence: `<command>` → `<salient output line>` (or <artifact path> @ <commit sha>)
  Level: <local-run|ci|staging|production|doc-source> · Scope: <where it holds> · Supersedes: <H-NNN|F-NNN|—>
     ≥2 surfaces: add ### backend / ### ios / ### contracts subsections here.
     Migration: add ### invariants with parity evidence on BOTH old and new paths.
     Contract: one fact "Contract source of truth: <path> @ <sha>"; never copy the schema. -->

## Hypotheses
<!-- Stage 2. Each needs a discriminating Check (a command whose output would falsify it). FALSIFIED entries stay until
     the parent failure closes, so no session retries them. Format:
- H-NNN · <claim> · opened <YYYY-MM-DD> · for O-NNN
  Check: `<command>` ; <claim predicts X, alternative predicts Y>
- H-NNN · FALSIFIED <YYYY-MM-DD> · <claim>
  Evidence: `<command>` → `<output line that falsified it>`
-->

## General rules
<!-- Stage 4. Imperative + scope + ≥1 verified instance. conf: low = 1 instance, medium = 2, high = ≥3 or reproduced by
     a verifier. Project-only rules live here; cross-project candidates go to LESSONS-INBOX.md. Format:
- R-NNN · <imperative rule> · conf: <low|medium|high> · since <YYYY-MM-DD>
  Applies when: <scope conditions> · Instances: F-NNN[, F-NNN] · Counter-cases: <known exceptions | none known>
  Merged: <R-ids, if any> · Candidate: <L-NNN in LESSONS-INBOX.md, if any>
-->

## Open failures
<!-- Stage 1→2. Open an entry BEFORE trying fixes. Long investigations → investigations/O-NNN.md (2-line entry here).
     CONTRADICTION entries also go here and are resolved by re-running both evidence commands. Format:
- O-NNN · <YYYY-MM-DD> · <symptom> · severity: <blocks merge|blocks milestone|degraded|cosmetic>
  Repro: `<command>` · Observed: <…> · Expected: <…> · Blast radius: <…>
  Hypotheses: <H-ids with status> · Detail: investigations/O-NNN.md
- O-NNN · CONTRADICTION · <YYYY-MM-DD> · F-NNN says <…>; <new observation>
  Resolve by: `<evidence command of F-NNN>` and `<command behind the new observation>`
-->

## Decisions index
<!-- One line per decision; the full entry is in DECISIONS.md. Format:
- D-NNN <title> · <accepted|superseded-by D-NNN> (DECISIONS.md#d-nnn)
-->

## Last session
<!-- One line per session, newest first, keep 5; older lines move to archive/state-YYYY-MM.md. The Stop hook and the
     final verifier check freshness. Format:
- <YYYY-MM-DDTHH:MMZ> · s<N> · <what moved, ≤20 words> · +F-… ~H-… +R-… +O-… −O-… · rules cited: <R-ids>
-->
