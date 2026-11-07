# Verify brief — experiment 01, proven-bugs reviewer

**Mode: harness.** Finish and verify the inputs. Run no reviews and no grading.

- Harness: `/Users/ricardocoelho/Code/claude-skills-experiment-01-proven-bugs-reviewer/experiments/01-proven-bugs-reviewer/` (H below). Its `check_inputs.py`, `prep.py` and `config.json` are from earlier sessions of your role.
- Design: `/Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer.md` (*Design*, and the *Log* amendments).
- Seed runner the orchestrator used, which works: `/private/tmp/claude-501/-Users-ricardocoelho-Code-claude-skills/612b22c6-555b-4884-a849-34a2e1709e4a/scratchpad/seedrun.sh <ticket> <n> "<existing seeds>" "<class>"`. It writes the brief, snapshots the copy, calls codex with the network flag and a 900 s timeout, and writes `H/seeds/<t>/syn-<n>.patch`. Codex is told not to run pnpm or jest, so every check below is yours. Launch it with Bash in the background and wait for it; an earlier stall was a transient OpenAI network timeout.

## 1. Ticket 15's input is wrong: rebuild it

`bead2cb..6945ccf` also holds tickets 25's and 28's merges: 15 was rebased onto `c1a6367` before its commit. 15's own change is `c1a6367..6945ccf` (15 files, +2968/−296; non-test +932/−233).

- Set 15's BASE to `c1a6367` in `config.json`. Remove both 15 copies (`/Users/ricardocoelho/Code/sidedoor/worktrees/exp01-15-{seeded,clean}`) and rebuild them with `prep`, including setup.
- `seeds/15/syn-2.patch` (`isAtRolloverCeiling` in `agent-conversation-chain.service.ts`) is outside 15's own diff and duplicates 25's seed: move it to `seeds/15/retired/`.
- Re-apply `seeds/15/syn-1.patch` (`updateStep` in `journeys.service.ts`, which is in 15's own diff); regenerate it if its offsets no longer apply.
- Write a new 15 syn-2 with `seedrun.sh 15 2 "updateStep in src/modules/journeys/journeys.service.ts" "boundary (off-by-one, inclusive/exclusive), unhandled error path, or broken caller of changed code"` from a copy reset with syn-1 applied.

## 2. Ticket 32's real seed: remove the fix's spec

The spec "keeps text after the successful proposal when a second edit is rejected" in `src/evals/agent/driver.spec.ts` was added by the fix; the real reviewer never saw it. Extend `seeds/32/real-1-retry-reanchors-textAfterProposal.patch` so it also deletes that one test (and nothing else). The seeded copy's other specs must stay green.

## 3. Verify every seed

Seeds to verify (each codex key as returned; `t` = ticket):

| t | seed | key |
|---|---|---|
| 15 | syn-1 | `src/modules/journeys/journeys.service.ts:619 · updateStep · Explicit null updates silently preserve fields instead of clearing them. · reached via src/modules/journeys/journeys.controller.ts:406` |
| 15 | syn-2 | new, from step 1 |
| 16 | syn-1 | `src/modules/notifications/listeners/milestone-detection.listener.ts:65 · handleTimelineBatchApplied · A batch adding a step dereferences undefined and suppresses section celebrations earned in that batch. · reached via src/modules/journeys/journeys.service.ts:695` |
| 16 | syn-2 | `src/modules/notifications/listeners/timeline-batch-notification.listener.ts:28 · handleTimelineBatchApplied · A transient professional lookup failure silently removes the sender exclusion, notifying the approving professional if delivery succeeds. · reached via src/modules/journeys/journeys.service.ts:693` |
| 25 | syn-1 | `src/modules/agent/agent-turn.service.ts:83 · withPageContextPart · Valid page context with empty entities silently loses its route in model prompts. · reached via src/modules/agent/agent.controller.ts:80` |
| 25 | syn-2 | `src/modules/agent/agent-conversation-chain.service.ts:39 · isAtRolloverCeiling · Rollover is skipped when replay tokens exactly equal the ceiling and turns remain below their limit. · reached via src/modules/agent/agent.service.ts:171` |
| 28 | syn-1 | `src/evals/agent/assertions.ts:163 · extractWords · Empty assistant replies throw, replacing turn diagnostics with driver_error and discarding the transcript. · reached via src/evals/agent/runner.ts:71` |
| 28 | syn-2 | `src/evals/agent/assertions.ts:201 · detectReplyLanguage · Short Spanish replies with one English stopword can bypass Spanish evidence and incorrectly pass the language check. · reached via src/evals/agent/assertions.ts:307` |
| 30 | syn-1 | `src/modules/journeys/journey-edits.planner.ts:152 · reachesStep · An empty precedent list ends traversal early, allowing cycles through pending branches. · reached via src/modules/agent/tools/journey.tools.ts:307` |
| 30 | syn-2 | `src/modules/agent/tools/journey-edit-preview.ts:27 · previewNewStep · New-step previews omit all dependencies when two or more precedents are supplied. · reached via src/modules/agent/tools/journey-edit-preview.ts:77` |
| 31 | syn-1 | `src/modules/agent/agent-conversation.projection.ts:56 · projectMessage · Truncated replies containing partial text lose their truncation flag when retrieved. · reached via src/modules/agent/agent-conversation-queries.service.ts:105` |
| 31 | syn-2 | `src/modules/agent/agent-turn.service.ts:296 · streamModelTurn · Length-truncated responses containing partial text or tool activity lose truncation metadata and the SSE warning flag. · reached via src/modules/agent/agent-model-client.service.ts:280` |
| 32 | real-1 | `src/evals/agent/driver.ts:95 · textAfterProposalOf · the isProposedToolOutput filter is gone, so a rejected edit_journey retry (proposal_already_pending_this_turn) re-anchors textAfterProposal and maxReplyWords passes falsely · reached via src/evals/agent/assertions.ts:251 and driver.ts:319` |
| 32 | syn-1 | `src/evals/agent/driver.ts:325 · buildTurn · Empty post-proposal text is omitted, causing word-limit checks to count pre-proposal prose and falsely fail valid turns. · reached via src/evals/agent/driver.ts:264` |
| 32 | syn-2 | `src/evals/agent/assertions.ts:250 · checkProposalReply · Truncated replies bypass maxReplyWords, allowing overlong mixed-edit replies to pass. · reached via src/evals/agent/runner.ts:71` |

For each ticket's seeded copy with all its seeds applied together, and each seed:

- **In the ticket's own diff:** the mutated lines sit in code that `git diff <BASE> <commit>` adds or changes (not untouched code).
- **Typecheck** passes.
- **Specs green:** every spec file covering a changed file passes (`pnpm exec jest <files> --runInBand`; Mongo-backed suites flake under load, so rerun a timeout before judging).
- **Reachable:** read the caller in `reached via` and confirm real input reaches the defect at the seeded state (what the DTO, schema and callers allow). Say in one line per seed what input reaches it.
- **Line:** correct the key's line number to the mutated line in the seeded copy.

A seed that fails any check is replaced once with `seedrun.sh` (same ticket, existing seeds named, same class list) and verified the same way; one that fails again is dropped and reported. Then write `H/seeds/<t>/answer-keys.txt` for every ticket in ticket 29's format (`real|synthetic · file:line · function · effect · reached via …`).

## 4. Check all 16 inputs

Run `check_inputs.py` over all 16 and save `H/inputs-check.txt`. Every input must pass.

## Boundary

- No reviews, no grader calls, no change to arms, prompts, runner flags or the hit rule.
- Leave no background processes; the stray mongod pid 14780 is not yours.
- No commits or branches in claude-skills. Leave the run file alone.

## Return

Your role file's format, under 500 words, plus: the final answer keys per ticket, quoted; per seed one line: pass/replaced/dropped and the input that reaches it; the 16-input check result; anything that looked off.
