# Fix brief — experiment 01, proven-bugs reviewer

**Mode: harness.** Apply the fixes below to the harness you (an earlier session of your role) built, re-run the smoke into a fresh folder, and return before any full run.

- Harness: `/Users/ricardocoelho/Code/claude-skills-experiment-01-proven-bugs-reviewer/experiments/01-proven-bugs-reviewer/` (untracked; touch nothing else in that repo).
- Design: `/Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer.md`, *Design*. The fixes below amend it; the orchestrator writes them into the run file.
- New smoke raw folder: `/Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer/raw/smoke-2/`. Leave `raw/smoke/` and `raw/smoke-check/` as they are.

## Fixes

1. **Leak: the ticket points at the answers.** `TICKET.md` keeps an `**Origin:**` line naming `z-features/ai-agent/runs/12-eval-suite.md`, and every run log in `/Users/ricardocoelho/Code/sidedoor/z-features/ai-agent/runs/` holds the review log with the real seeds' descriptions. In `prep.py`'s ticket text, drop the `**Origin:**` line and any other line naming a run log or `z-features`. In both arms' settings, deny reads of `/Users/ricardocoelho/Code/sidedoor/z-features/**`, of the harness folder, and of `/Users/ricardocoelho/Code/claude-skills/docs/experiments/**`: a `permissions.deny` `Read(...)` rule and a sandbox `filesystem.denyRead` for each path. Prove it: from a prepared worktree, under each arm's exact settings, a `claude -p` call asked to `cat` a run log and `Read` the answer-keys file is refused (cheapest model is fine for this probe; log it apart from the arms).
2. **Leak: git refs reach the post-fix commits.** The worktree shares the backend repo's refs, so `git diff --stat f6d448f -- src` prints exactly the seeded files. Build each scratch copy as its own clone that holds only history up to BASE (for example `git clone --no-local --single-branch --branch <tmp-branch-at-BASE>`, or clone then delete every ref but a local branch at BASE and expire the reflog and gc, or `git init` + fetch of BASE only). Keep the rest of the design: ticket diff and seeds uncommitted, new files `git add -N`, `.env` and `node_modules` via the setup script's logic, located at `/Users/ricardocoelho/Code/sidedoor/worktrees/exp01-<ticket>-<condition>/backend` (remove the existing `exp01-29-seeded` git worktree first with `git -C /Users/ricardocoelho/Code/sidedoor/sidedoor-backend worktree remove --force <path>`; it is ours). Prove it: in the prepared copy, `git log --all --oneline | head -1` is BASE, `git cat-file -t f6d448f` fails, and `git diff HEAD` still matches `git diff 1bd7048` of the old worktree (same file list and +/− counts).
3. **Arms' permissions differ beyond the variable.** A uses `autoAllowBashIfSandboxed: false` with a read-only allowlist, which denied a compound `rg` chain; B auto-allows. Give both arms the same permission mode and the same sandbox settings (B's, plus fix 1's denies). The arms then differ only in the role file's tools line and its read-only/scratch-copy paragraph, and B's brief suffix, which is the design's variable. Prove it with a diff of the two arms' full `claude` argument lists, saved in the harness folder.
4. **Tool trace.** Record every tool call: switch to `--output-format stream-json --verbose` (or an equivalent that keeps the full transcript) and save it per review next to the JSON; the raw row still gets every usage field and `total_cost_usd` from the final result event. Add to `summary.py`, per review: whether any tool call touched `z-features`, the harness folder, `docs/experiments`, or ran `git log --all`/`git diff <hash other than BASE>` (`leak_suspect`), and for B, the test or script commands it actually ran with their exit codes (`proof_runs`). The grade must not see the trace.
5. **Wall time on retries.** `run_reviews.py` resets `t0` per attempt, so `wall_s` is the last attempt only while cost sums all attempts. Sum wall time across attempts into `wall_s`, and keep a per-attempt list.
6. **Synthetic seeds must be reachable.** S3 (`contacts.repo.ts:50`, whitespace-only search) is unreachable: both callers trim and require `min(1)` (`contacts.dto.ts:78`, `agent/tools/contact.tools.ts:17`). Add to `seeds/synthetic-brief.md`: a seed must be reachable from a real caller or entry point at the seeded state, and its answer key names that path (`… · reached via <caller file:line>`). Replace S3 with a new codex-written seed under that rule, in a different function from S1, S2, S4. Verify every seed for ticket 29 again (typecheck; spec files covering the changed files green), and check the reachability claim yourself by reading the caller.
7. **Hit rule: quoted code.** B cited `journey-invitations.seed.ts:415` (the file has 137 lines) for the same defect A hit at :88, and the grader marked it a miss. Amend the hit rule, verbatim in the grader prompt: "A finding hits a seed when it names the seed's file, describes the defect's effect, and locates it by any one of: a line within ±10 of the seed, the enclosing function's name, or a quote of the seeded code." Extraction keeps a `quote` field (the shortest code quote the finding gives, or empty); it still strips proof commands and outputs.
8. **Model id unrecorded.** Raw rows carry `model: None`, though the CLI's result JSON names each model it used under `modelUsage` (e.g. `claude-opus-5-5`, with per-model tokens and `costBasis`). Record every `modelUsage` key with its per-model usage in the row, and set `model` to the main one. `summary.py` flags any review that used a model other than the arm's.

## Smoke

Re-run the smoke with the fixed harness into `raw/smoke-2/`: ticket 29, seeded, 1 rep per arm, grading, summary. Then re-grade the saved `raw/smoke/` extractions under the amended hit rule into `raw/smoke-regrade/` (grading only, no new reviews), so the orchestrator can see whether B's :415 finding now hits S4.

## Boundary

- Fix only what is listed. A fix that needs a design change beyond these: stop and report.
- Every check runs; a check the sandbox blocks is reported with its output.
- Leave no background processes when you return (mongod, claude, codex); list any you could not stop.
- No commits, no branches in claude-skills. Leave the run file alone.

## Return

Your role file's format, under 400 words, plus: the proof output for fixes 1–3 (quoted), the new seed's answer key, the smoke-2 per-arm numbers with `leak_suspect` and `proof_runs`, the regrade verdict for B's :415 finding, and the re-run command.
