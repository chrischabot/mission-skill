# Rubric · operate · <goal slug>
frozen: <ISO UTC> · commit <short sha> · copied from templates/rubrics/operate.md by drive:architect
applies to: <step names and claim keys>
target system: <service, account, environment, and region as how-it-works.md names them>
read verbs: <the system's own commands or API calls that show its state>

<!-- Fill every placeholder, delete trait rows that do not apply, and commit before the first step
runs. Never edit during a verification loop. Each criterion reads: observation, oracle, refutation,
threshold. A command's exit code is never the oracle for a change to a live system; a different agent
reads the state afterwards. A criterion that cannot apply is reported as `rubric_gap:`. Rules:
references/verification.md and references/long-running.md for any soak. -->

## Standing floor
<!-- Always in scope. Never a rubric gap. -->

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| No weakened checks | no alert, health check, validation, or test disabled or loosened to let a step proceed | configuration read before and after; `drive.py guard` for tracked files | a check off or loosened without a DECISIONS.md entry | blocking |
| Rehearsal no kinder than production | any dry run or staging rehearsal lists where it differs from production (data size, limits, permissions) | kindness-ledger rows in TESTPLAN.md or STATE.md | a step that passed rehearsal only because of a named difference, with no live check | blocking |
| No data loss | each destructive step had a backup whose restore was tested on a copy, and a written undo, before it ran | undo records and backup lines against the command log | a destructive command logged before its tested backup or undo | blocking |
| Security holds | no secret value entered by the run or written to any file or command line; secrets the owner must set are named | STATE.md, command log, and shell history grep | a secret value anywhere in the run's records | blocking |

## Process

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Runbook and state read first | the runbook and the system's current state were read before the plan was written | read-verb output timestamps before the plan commit | a plan written before any state read | should_fix |
| Undo before each step | every step's undo was recorded before the step ran | DECISIONS.md or STATE.md timestamps against the command log | an undo written after its step | blocking |
| Observed by another agent | each step's effect was read by drive:verifier through the read verbs, not reported by the agent that ran it | `live.md` per step and its verdict | effect evidence that is only the executing command's output | blocking |
| Values have sources | every count, rate, and timing names the command or dashboard query that produced it | reading | an unsourced number | blocking |

## User outcome

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| <The state the goal asked for> | <the system shows the intended end state, in the owner's words> | read verbs run by drive:verifier after the last step | the end state differs from the plan | blocking |

## Shape criteria

| criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|
| Right target | account, environment, service name, and version matched the plan before the first mutating command | read-verb output logged before that command | a mismatch, or no check before the first mutation | blocking |
| Each step's effect present | after every step, the read verbs show that step's intended state | `live.md` for the step | a missing or different state | blocking |
| No collateral change | adjacent state (other services, configuration keys, schedules, permissions) matches its reading from before the run, apart from planned changes | before and after read-verb diff | an unplanned difference | blocking |
| Triggered now | every scheduled or asynchronous effect was triggered through the system's own verb and its result observed | trigger output and a state read | a status that waits for a scheduled run | blocking |
| Soak only without a signal | a soak window exists only for a condition no trigger can force, and its check decides and acts | soak record and the scheduled check's definition | a schedule where a trigger existed, or an open soak at Done | blocking |
| Scripts tested | any script written for the operation has tests and ran in its dry-run mode before the live run | `test:` tokens and the dry-run log | an untested script run live | should_fix |
| Runbook updated | the runbook that was followed now matches what was actually run | `doc:` token and a diff against the command log | a runbook step that contradicts the run | should_fix |

## Trait additions

| trait | criterion | observation | oracle | refutation | threshold |
|---|---|---|---|---|---|
| `deploy-infra` | Config diff before apply | the configuration diff was captured before apply and matches the applied change | saved diff against post-apply read | an applied change absent from the diff | blocking |
| `data` | Import or rewrite counted | row counts and a checksum over sorted keys match the source after the step | verification query output | a mismatch | blocking |
| `auth` | Rotation complete | the old credential is rejected and every consumer authenticates with the new one | a request with each credential; consumer health reads | the old credential accepted, or a consumer failing | blocking |
| `external-systems` | Egress from where it runs | the system reaches each external dependency from its own runtime, not from the operator's machine | a request made from inside the runtime | reachability shown only from the operator's machine | blocking |

## Amendments
- <ISO UTC> · <criterion added, removed, or reworded> · because <rubric gap or ruling> · DECISIONS.md <date>-<slug> · applies from <unit>
