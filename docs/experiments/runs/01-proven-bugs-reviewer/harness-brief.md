# Harness brief — experiment 01, proven-bugs reviewer

**Mode: harness.** Build the harness, run the smoke run only, and return before any full run.

## Goal

Measure whether a Bugs code reviewer that must prove its findings by running code (arm B) produces fewer false findings than the current read-only reviewer (arm A) without missing more planted bugs. The design is agreed with the user and lives in the run file: `/Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer.md`, section *Design*, plus the *Inputs* table above it. Read the whole run file first; it is the spec you build against. Where this brief and the run file disagree, stop and report.

## Paths

- Harness folder (yours to create; touch nothing else in this repo): `/Users/ricardocoelho/Code/claude-skills-experiment-01-proven-bugs-reviewer/experiments/01-proven-bugs-reviewer/`. That worktree is at commit 023b0a1; read the arm sources from it: `agents/rc-reviewer.md` and the Bugs brief in `skills/rc-orchestrate/SKILL.md` step 2 (the bullet starting `**Bugs axis:**`, the quoted text only).
- Raw output: `/Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer/raw/smoke/`.
- Inputs repo: `/Users/ricardocoelho/Code/sidedoor/sidedoor-backend` (read its `CLAUDE.md` and `/Users/ricardocoelho/Code/sidedoor/CLAUDE.md`). Never commit, branch, or change its main checkout; add detached worktrees only, under `/Users/ricardocoelho/Code/sidedoor/worktrees/exp01-<ticket>-<seeded|clean>/backend` (absolute path to `git worktree add`), then run `/Users/ricardocoelho/Code/sidedoor/worktrees/setup.sh exp01-<ticket>-<condition>`.
- Ticket files: `/Users/ricardocoelho/Code/sidedoor/z-features/ai-agent/issues/` (find each by its number).
- Real-seed sources: the review-log lines in `/Users/ricardocoelho/Code/sidedoor/z-features/ai-agent/runs/29-seed-coverage.md` (lines starting `bugs · Minor · src/seeds/`) and `32-journey-write-evals.md` (the `Bugs · Minor · driver.ts:95` line), plus the surrounding run notes. Re-create each bug in the committed code so it matches the description; the code as committed is the fixed version.

## What to build

Everything below is in the run file's design; this is the build order.

1. **Input prep script.** For each (ticket, condition): the worktree detached at the ticket's BASE, the ticket diff (BASE..commit, excluding `evals/agent/results/`) applied uncommitted with new files `git add -N`, plus the seed patches for the seeded condition, plus the ticket file copied in (status `in-progress`, boxes unticked). A reset command that returns a worktree to that pristine state before every review, keeping `node_modules` and `.env`. Check: `git diff HEAD` in a prepared worktree shows the ticket diff and seeds together, with nothing committed past BASE.
2. **Seeds.** Each seed is a patch file plus a one-line answer key (`file:line · function · effect`), stored in the harness folder, never inside a sidedoor worktree. Synthetic seeds are written by codex, as the design says; call it through `~/.claude/skills/rc-codex/scripts/codex-run.sh` (read `~/.claude/skills/rc-codex/SKILL.md` for the mechanics), from inside the worktree, which is a git repo. For the smoke you need ticket 29's seeds only: its 2 real seeds + 2 synthetic. Verify each seed: typecheck passes, and the spec files covering the changed file stay green (`pnpm exec jest <file> --runInBand`; see the backend `CLAUDE.md` for the real commands).
3. **Review runner.** One `claude -p` call per review, cwd = the scratch worktree, `--output-format json`, the arm's agent passed with `--agents` from files frozen in the harness folder (A: `rc-reviewer.md` verbatim; B: as the design states), `--model opus --effort medium`. The prompt is the same skeleton for both arms: the diff command `git diff <BASE>`, the ticket file path inside the worktree, the arm's Bugs brief. Pick permission flags so A cannot write and B can write only inside its worktree; say which you chose and why. One raw row per call: arm, ticket, condition, rep, model id, every usage field the JSON returns, `total_cost_usd`, wall time, exit status, retries, and the reviewer's full text saved to its own file. The runner sums cost and refuses a call that would cross the $150 cap. It supports the design's concurrency (at most 2, never two in one worktree) and the randomized arm order.
4. **Grading.** The design's three grading steps with codex: extraction to JSON with proofs stripped, blind shuffled grading against the answer keys by the hit rule (quote the hit rule verbatim into the grader prompt), and a sample file for the human check (20 non-hits, blind; for the smoke, all non-hits). Grader calls get their own raw rows, apart from the arms'.
5. **Summary script.** Computes, from the raw rows only, the per-arm numbers the decision rule needs: seeds hit (real and synthetic apart), false findings above Nit, Pre-existing count, median wall time, cost.

## Smoke run

Ticket 29, seeded, 1 rep per arm: 2 reviews, then their extraction and grading, then the summary. Before the reviews, check the real seeds re-create the bugs the review log describes.

## Boundary

- Build the harness and run the smoke only. Return before any full run, and before preparing inputs other than ticket 29.
- The design is fixed. If it cannot be measured as written (for example, B cannot run the backend specs in a scratch worktree, or `--agents` cannot carry the frozen role files), stop and report with what you would propose. Changing the design is the orchestrator's call.
- Every check runs. A check the sandbox blocks is reported with its output, and the other checks still run.
- Make no commits and create no branches. Leave the run file alone.

## Return

Your role file's format, under 400 words, plus:
- the exact command that re-runs the smoke from scratch, writing to a raw folder given as an argument;
- the two arms' frozen agent files, by path, so the orchestrator can diff them;
- the seeds' answer keys, quoted;
- wall time per review and the projected full-run cost and duration (smoke cost per call × 96, and the same for time at concurrency 2).
