# Run — 01 proven-bugs reviewer

- **Ticket:** docs/experiments/01-proven-bugs-reviewer.md
- **Feature folder:** none (outside a features root): no feature page; run dir `docs/experiments/runs/01-proven-bugs-reviewer/`
- **Backend:** codex (probe OK 2026-11-02), used for the grader only; arms are Claude by design.

## Ground

| Repo | Role | Branch | BASE |
|---|---|---|---|
| claude-skills | harness (worktree `experiment/01-proven-bugs-reviewer`) | main | 023b0a1 |
| sidedoor-backend | inputs, read at historical commits (detached worktrees, never a branch) | ai-agent-v0 | 7f287c4 |

claude-skills tree is not clean: README.md, install.sh, confounds.md, rc-retro, scripts/, .githooks/, docs/experiments/ are uncommitted (this session's work). The harness worktree branches from 023b0a1, so none of it reaches the harness; the arms' Bugs brief and `rc-reviewer` at 023b0a1 are the committed ones.

## Inputs (backend only)

| Ticket | BASE..commit | Diff (all / non-test, excl. eval results) | Real seeds |
|---|---|---|---|
| 15 | c1a6367..6945ccf (rebased onto c1a6367; bead2cb..6945ccf also held 25 and 28) | +2968/−296 · +932/−233 | — |
| 16 | e3f49f9..73d14a2 | +642/−42 · +147/−33 | — |
| 25 | bead2cb..3e70bff | +972/−781 · +871/−723 | — |
| 28 | bead2cb..6e0f35e | +127/−5 · +74/−5 | — |
| 29 | 1bd7048..f6d448f (3 commits; rebased onto 1bd7048) | +608/−25 · +421/−16 | contacts.seed.ts:66-70 `deletedAt: null` vs `$exists:false`; pro-microsites.seed.ts:63-89 slug taken aborts the seed run |
| 30 | e3f49f9..50fe387 | +924/−38 · +222/−34 | — |
| 31 | 7a6989a..3ec20e8 | +289/−19 · +28/−10 | — |
| 32 | e3f49f9..17efe12 | +345/−43 · +157/−7 | driver.ts:95 retry re-anchors `textAfterProposal` |

Historical Bugs-axis lines across these 8 runs: 13, of which 3 fixed, 7 deferred (mostly pre-existing), 2 `rejected: intentional`, 1 `rejected: wrong`.

## Design (agreed at Gate A, 2026-11-02)

The user chose (b) for the claim and took the orchestrator's recommendation on every other field ("go with your recommendations for all").

- **Claim:** requiring the Bugs reviewer to prove every finding above Nit with a run cuts its false findings above Nit by at least half, at the cost of at most one more missed seed than the current reviewer.
- **Arms.** The variable is "proof required and permitted"; everything else is held the same.
  - **A (current):** the `rc-reviewer` role at 023b0a1 (read-only; tools Read, Grep, Glob, Bash) + the Bugs brief from `skills/rc-orchestrate/SKILL.md` step 2 at 023b0a1, verbatim.
  - **B (proven):** the same role file with its **Read only** paragraph replaced by: "**Scratch copy.** The working tree is a disposable copy: you may write and run tests and scripts in it. Leave the code under review as you found it." Tools add Write and Edit. The brief is A's plus: "Prove each finding above Nit with a run against the real code: a failing test or a script, in this working tree. Report the command, the output it printed, and the output the ticket requires. A finding you could not run is at most a Nit, with the reason it could not run."
  - Both: the role files are frozen into the harness (passed with `--agents`, never read from `~/.claude/agents/`), opus · medium, the same prompt skeleton (diff command, ticket path, brief), the same settings sources, the same cwd layout.
- **Call:** headless `claude -p` (CLI 2.1.316), `--output-format json`, cwd = the input's scratch worktree. Writes stay inside it; no network beyond the model.
- **Inputs:** the 8 backend diffs in *Inputs* above, each in two conditions:
  - **Seeded:** the ticket's diff plus its seeds. Real seeds: the 3 in the table, re-created from their review-log descriptions. Synthetic seeds: 2 per diff, written by codex (another family than the arms), one-hunk mutations in non-test code the diff touches, in the Bugs brief's classes (empty/null, boundary, unhandled error path, broken caller, missing authorization), each in a different function from the other seeds. Every seed must keep typecheck and the touched spec files green (real bugs passed both), and has a one-line answer key written before any review.
  - **Clean:** the ticket's diff alone (committed, post-fix code).
  - **No leak through git:** each scratch worktree is detached at the ticket's **BASE**, with the ticket diff (+ seeds) applied as uncommitted changes and new files `git add -N`, so `git diff <BASE>`, `git diff` and `git diff HEAD` all show the same thing, as in a real run. The ticket file is copied in from `sidedoor/z-features/ai-agent/issues/` with its status reset to `in-progress` and its boxes unticked. Answer keys and run files stay outside every scratch worktree.
  - **Worktrees:** one per (ticket, condition) at `sidedoor/worktrees/exp01-<ticket>-<seeded|clean>/backend`, prepared by `sidedoor/worktrees/setup.sh`; reset to its pristine state (checkout + clean, keeping `node_modules` and `.env`) before every review. At most 2 reviews run at once, never two in one worktree. Order across arms is randomized per (input, rep).
- **Metric**, per review: seeds hit; findings above Nit that hit no seed, each verdicted real-but-unseeded / false / unsure; wall time; every usage field and `total_cost_usd`. Recall reported for real and synthetic seeds apart. `Pre-existing` findings are counted apart, never as false.
- **Hit rule** (fixed now): a finding hits a seed when it names the seed's file, points within ±10 lines of it or names the enclosing function, and describes the defect's effect.
- **Grading**, by codex (gpt-6.1-sol · medium, read-only), logged apart from the arms:
  1. **Extract:** per review, the findings as JSON {file, line, tag, effect}, proof commands and outputs stripped, so the grader cannot tell the arms apart.
  2. **Grade:** shuffled findings per input, arm names stripped, against that input's answer keys by the hit rule; each non-hit gets a verdict from reading the worktree's code.
  3. **Human check:** the user labels a blind sample of 20 non-hits; agreement with codex is reported.
- **Size:** 8 diffs × 2 conditions × 2 arms × 3 reps = 96 reviews. Smoke: ticket 29 (it holds 2 real seeds), seeded, 1 rep per arm = 2 reviews, plus their grading.
- **Decision rule:** adopt B when, summed over the 3 reps and averaged per rep, B's seeds hit ≥ A's − 1, B's false findings above Nit ≤ ½ of A's, and B's median wall time ≤ 2× A's. When A's false findings above Nit total fewer than 6 across all its reviews, the verdict is **inconclusive** on precision, and the report says so.
- **Budget cap:** $150 in `total_cost_usd` across arms (Claude Code's own price table, CLI 2.1.316, 2026-11-02). Codex grading runs on the codex login and is counted in calls and tokens.
- **Stop rule:** stop at the cap; stop when either arm has more than 25% failed calls after its first 12; no early stop on a decisive result (n is too small to call early).
- **Fallback:** when the smoke shows B cannot run the backend specs in a scratch worktree, B proves with a script against the module, and that change returns to the user before the full run.
- **Paths:**
  - harness: `/Users/ricardocoelho/Code/claude-skills-experiment-01-proven-bugs-reviewer/experiments/01-proven-bugs-reviewer/` (branch `experiment/01-proven-bugs-reviewer` from 023b0a1);
  - raw output: `/Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer/raw/`.

## Log

- 2026-11-02 Phase 0 done; Gate A settled (above).
- Phase 1 harness call: rc-experimenter, Claude rung 3 (sonnet · medium), brief runs/01-proven-bugs-reviewer/harness-brief.md, checkpoint 191d6551a2e05df6a2224e8881f7f9460727c1b7.
- Phase 1 smoke returned (harness untracked under experiments/01-proven-bugs-reviewer/). Smoke: ticket 29 seeded, 1 rep/arm, $1.01 per attempt, ~100 s/review; projected full run ≈ $49, ≈ 80 min at concurrency 2. B ran backend specs in-sandbox (fallback not needed).
- Orchestrator's verification:
  - A's role file is byte-identical to 023b0a1's `rc-reviewer.md`. A and B differ in the role's tools line, its read-only paragraph and B's brief suffix, as designed, **and in permissions beyond the variable**: A uses `autoAllowBashIfSandboxed: false` + a read-only allowlist, which denied a compound `rg` chain; B auto-allows. → fix: same sandbox settings for both arms.
  - Seeds: S1 (real) is reachable. Imported contacts are upserted with filter `deletedAt: null` (`contacts.repo.ts:136`), so Mongo writes an explicit null that `$exists:false` misses; A's "no default, so it works" is a genuine miss. S2 (real) is reachable when another account holds the slug; both arms missed it. **S3 (synthetic) is unreachable**: both callers trim and require `min(1)`, so it is not a defect → fix: synthetic seeds need a caller path that reaches them, named in the answer key. S4 is a real defect at Nit weight.
  - Grading: B's `journey-invitations.seed.ts:415` finding is S4 (same defect A hit), missed by the grader because B's line number is wrong (the file has 137 lines). → fix: the hit rule also accepts a finding that quotes the seeded code.
- Phase 1 verification re-run launched → raw/smoke-check/. Phase 2 design review launched (rc-reviewer, brief runs/01-proven-bugs-reviewer/design-review-brief.md), in parallel.
- Phase 2 design review (rc-reviewer): 0 invalidates, 3 weakens, 2 notes. Triage:
  - fixed: leak via the ticket's `Origin:` line + readable run logs (weakens); leak via shared git refs, `git diff --stat f6d448f -- src` lists exactly the seeds (weakens; orchestrator rates it near-invalidating); no tool trace, so leaks and B's proofs cannot be audited (weakens); wall time counts the last retry only (note).
  - caveat → stop point: precision will likely be inconclusive (A logged 0 above-Nit findings in the smoke). Added to the stop rule: after rep 1, when A's false findings above Nit project below 6 over 3 reps, pause and report to the user before reps 2–3.
  - Orchestrator's own three (equal permissions, reachable synthetic seeds, hit rule accepts a code quote) go into the same fix round. Hit-rule amendment: "A finding hits a seed when it names the seed's file, describes the defect's effect, and locates it by any one of: a line within ±10 of the seed, the enclosing function's name, or a quote of the seeded code." Made before any full-run data.
- Phase 1 verify re-run (raw/smoke-check): exit 0, 2 rows, every usage field, A $0.39 49.7 s, B $0.47 109.3 s; rows record model None (fix 8). Fix round: rc-experimenter rung 3, brief runs/01-proven-bugs-reviewer/fix-brief.md, checkpoint 044a0e1452484438f5b1a0ef11ee199faac76bc5 (harness files intent-added).
- Fix round verified by the orchestrator:
  - The arms' argv differ in the brief suffix and the role JSON only, and the settings are identical.
  - The clone holds history to 1bd7048 only (`git cat-file f6d448f` fails, no remote).
  - The leak probe was refused on every protected read, under both arms.
  - Smoke-2 ($0.68): both arms hit the new S3. A tagged it a Nit at a wrong line (a quote hit), B tagged it Important with a failing spec. leak_suspect none; model claude-opus-5-5 only.
  - Regrade: B's old :415 finding now hits S4.
  - The experimenter also denied reads of `sidedoor-backend` (it holds the post-fix commits); accepted.
  - Projected full run ≈ $33.
- Inputs call: rc-experimenter rung 3, brief runs/01-proven-bugs-reviewer/inputs-brief.md (seeds for the 7 other tickets, 16 isolated copies, leak_suspect on inputs only, jest summary in proof_runs), checkpoint fe32f77ec6afc85eacc714d83c4345955b55a756.
- 2026-11-03 Inputs call stopped partway (ran ~7 h).
  - Done: all 16 isolated copies exist; the 8 clean inputs, seeded 29 and seeded 32 (structural checks) pass.
  - Codex seed calls for 15/16/25/28/30/31 stalled. The likely cause is the experimenter's codex calls: `workspace-write` without the network flag, with a brief that told codex to run pnpm and jest. Every log ends right before that step.
  - Orchestrator's decisions:
    - (1) Codex seed calls rerun by the orchestrator: network flag on, 900 s timeout, and the brief tells codex not to run pnpm/jest/tsc (the checks run afterwards).
    - (2) Ticket 32's real seed also deletes the spec the fix added ("keeps text after the successful proposal when a second edit is rejected"). That spec did not exist when the real reviewer saw the bug, so keeping it would leak the answer (confounds: *Leaked answers*).
- Codex seed calls, orchestrator:
  - The first batch of 6 timed out at 900 s with no edits. The logs open with "failed to refresh available models: request timed out", then a model turn never returns: transient network to OpenAI, not the harness.
  - A retry on 28 at 09:30 finished in about 1 min: `assertions.ts:163 · extractWords · empty assistant replies throw … · reached via runner.ts:71`.
  - Round 1 for 15/16/25/30/31/32 is running. Ticket 32 was missing from the first batch: it needs 2 synthetic seeds besides its real one.
- Codex seed rounds 1–2 done (13 synthetic seeds, all rc=0; codex ran no tests by brief).
- Ticket 15's input range was wrong: `bead2cb..6945ccf` holds 25's and 28's merges. 15's own change is `c1a6367..6945ccf`; Inputs table corrected. 15 syn-2 sits in 25's file (and duplicates 25's seed): retired. The other 7 ranges hold only their ticket's commits.
- Verify call: rc-experimenter rung 3, brief runs/01-proven-bugs-reviewer/verify-brief.md (rebuild 15, new 15 syn-2, 32 real seed drops the fix's spec, verify all seeds, answer keys, 16-input check), checkpoint 98a6ce04ad86681fba838b52462924a0f553dad7.
- Verify call returned:
  - 15 rebuilt at c1a6367, with a new syn-2 (`setStepDueDate`, a boundary bug).
  - 31 syn-1 was replaced: with syn-2 applied it could not be reached. The new one is `runTurn`, an error marker dropped.
  - 32's real seed now also deletes the fix's spec.
  - All 15 synthetic + 3 real seeds: inside the ticket's own diff, typecheck clean, covering specs green, reachability stated.
  - 25 syn-2 is only narrowly reachable (an exact-equality boundary): caveat.
  - Orchestrator spot-check: 15 isolated at c1a6367 (`cat-file 6945ccf` fails); 32's patch deletes exactly that one test; `check_inputs.py` 16/16 pass, re-run by the orchestrator.
- **Frozen:** harness committed on `experiment/01-proven-bugs-reviewer` @ `2baeb02`. The full run uses that commit only.
- Phase 3, rep 1: rc-experimenter rung 3, run mode, brief runs/01-proven-bugs-reviewer/run-brief.md, raw/full/.
- Rep 1 done (raw/full/, $14.22: A $6.18, B $8.04). Recomputed by the orchestrator from the raw rows; it matches the experimenter's numbers.
  - Reviews: 16/16 ok per arm, 0 retries, leak_suspect 0, opus 5.5 only.
  - Seeds: both arms hit 14/16 synthetic and miss the same two (16 S2, 29 S4); both hit 0/3 real.
  - Hits tagged above Nit: A 11, B 13. No hits on clean inputs.
  - Findings above Nit that hit no seed (codex verdicts):
    - A: 1 false (31 clean, the en/es message) and 1 Pre-existing.
    - B: 3 "real-but-unseeded": 15 clean, per-step milestone events (ticket 15's deferred Important); 28 clean, proper nouns; 31 clean, the truncation spec's stream shape.
  - **The grader is wrong on B-31:** the same finding was logged `rejected: wrong` in ticket 31's run after a real-model probe showed the provider emits no tool-call part. Corrected: A 1 false above Nit, B ≥1.
  - Median wall: A 46 s, B 89 s (1.93×).
  - **Pause point hit:** A's false findings above Nit = 1 in rep 1, which projects to ~3 over 3 reps, below the 6 the decision rule needs. Precision is inconclusive, as predicted. Back to the user before reps 2–3.
- The user stopped the run at rep 1 ("yes, stop and write it up").
- Human-check sample: 4 of 18 match past triage in the sidedoor run logs. Codex agrees on 3 (H07, H10, H15) and is wrong on H05 (B-31, `rejected: wrong` by a real-model probe). The other 14 are unlabelled.
- Research file: docs/experiments/01-proven-bugs-reviewer-results.md. Verdict: inconclusive.
- Gate B accepted by the user. Finish: ticket set to done with an ## Answer section; harness worktree removed (branch experiment/01-proven-bugs-reviewer @ 2baeb02 kept); 16 scratch clones under sidedoor/worktrees/exp01-* deleted. No feature page (outside a features root).
