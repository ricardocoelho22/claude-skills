# Inputs brief — experiment 01, proven-bugs reviewer

**Mode: harness.** Prepare every input for the full run and verify it. Run no reviews and no grading.

- Harness: `/Users/ricardocoelho/Code/claude-skills-experiment-01-proven-bugs-reviewer/experiments/01-proven-bugs-reviewer/` (you, in an earlier session of your role, built and fixed it; its smoke for ticket 29 seeded passed).
- Design and inputs table: `/Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer.md`, *Inputs* and *Design*, plus the amendments in its *Log* (reachable seeds, amended hit rule).
- Seed rules: `seeds/synthetic-brief.md` in the harness. Ticket 29's four seeds are done; keep them.

## Goal

All 16 inputs (tickets 15, 16, 25, 28, 29, 30, 31, 32 × seeded, clean) prepared exactly as ticket 29 seeded is: an isolated clone at BASE, the ticket diff (+ seeds) uncommitted, new files `git add -N`, `TICKET.md` with origin lines stripped, setup done so specs run.

## Seeds

- **Synthetic:** 2 per ticket for the 7 other tickets, written by codex under `seeds/synthetic-brief.md` (one-hunk, non-test code the diff touches, the Bugs brief's classes, reachable from a named caller, each in a different function). Ticket 31's non-test diff is 28 lines: when 2 reachable seeds in distinct functions cannot fit, use 1 and say so.
- **Real (ticket 32):** `driver.ts:95`: a rejected `edit_journey` retry (`proposal_already_pending_this_turn`) re-anchors `textAfterProposal`, so `maxReplyWords` passes falsely. Re-create it in the committed code from that description (the committed code is the fixed version; find the line by reading `driver.ts` around the retry handling). Do not read the sidedoor run logs for it; the description above is all there is.
- **Each seed, verified by you:** applies cleanly with the ticket's other seeds; typecheck passes; the spec files covering the changed files stay green; you read the caller named in `reached via` and confirm the seeded path reaches the defect. Reject and replace a seed that fails any of these (at most one replacement per seed; report any left unfilled).
- Answer keys in the existing format, one file per ticket, in the harness.

## Two small harness changes

1. `summary.py`'s `leak_suspect` matches `sidedoor-backend` inside text the reviewer read (TICKET.md). Match only tool-call **inputs** (commands and paths), not outputs.
2. `proof_runs` logs a pipeline's exit code (`pnpm test … | tail -40` exited 0 though jest failed). Also record jest's `Tests:` summary line from the tool output when present.

## Checks per input

For each of the 16: `git log --all --oneline | head -1` is the ticket's BASE; `git cat-file -t <ticket commit>` fails; `git diff HEAD --numstat` (with seeds reversed, for seeded inputs) equals `git -C /Users/ricardocoelho/Code/sidedoor/sidedoor-backend diff <BASE> <commit> --numstat -- . ':(exclude)evals/agent/results'`; `TICKET.md` has no origin, run-log or `z-features` line; the input resets to pristine via `prep.reset`. Save the check output to `inputs-check.txt` in the harness.

## Boundary

- No reviews, no grader calls, no changes to the arms, prompts, runner flags or hit rule.
- Leave no background processes; the stray mongod pid 14780 is not yours, leave it.
- No commits or branches in claude-skills. Leave the run file alone.

## Return

Your role file's format, under 500 words, plus: every answer key, quoted, grouped by ticket; any seed you could not fill and why; `inputs-check.txt`'s pass/fail per input; disk used by the 16 copies.
