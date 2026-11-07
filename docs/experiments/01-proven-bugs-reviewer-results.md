# 01 — Does a Bugs reviewer that must prove its findings review better?

## TL;DR

**Inconclusive. We keep the current Bugs brief.**
- **Recall:** requiring a run as proof for every finding above Nit did not change it. Both arms found the same 14 of 16 synthetic bugs and none of the 3 real ones.
- **False findings:** the current reviewer made 1 false finding above Nit in 16 reviews. That is too few to show any cut, let alone a halving.
- **Cost:** the proving reviewer took 1.9× the wall time and 1.3× the cost.
- **Where it did differ:** it rated severity more accurately (13 vs 11 of its hits tagged Important) and found more real bugs nobody had planted. But one of its "proved" Important findings is a finding the ticket 31 run had already shown wrong with a real-model probe: it proved against the SDK adapter, not the real provider.
- **Largest caveat:** a single repetition, with planted bugs that were too easy (88%) or too hard (0%) for either arm.

## Question and claim

pstack's `interrogate` keeps only findings a run proves. Would that make our Bugs reviewer (`rc-orchestrate` step 2) better?

- **Claim:** requiring the Bugs reviewer to prove every finding above Nit with a run cuts its false findings above Nit by at least half. The allowed cost is at most one more missed seed than the current reviewer.
- **Decision rule, set before the run:** adopt B when, per repetition:
  - B's seeds hit are at least A's − 1;
  - B's false findings above Nit are at most half of A's;
  - B's median wall time is at most 2× A's.
  - When A has fewer than 6 false findings above Nit, precision is inconclusive.
- **Verdict: inconclusive.** Recall: no loss. Precision: A had 1 false finding above Nit in 16 reviews, against the 6 needed. Wall time: 1.93×.

## Design

- **Arms:** both are `rc-reviewer` (opus 5.5 · medium) with the Bugs brief verbatim from `rc-orchestrate` at 023b0a1, run headless with `claude -p`.
  - **A (current):** the role's read-only paragraph and the brief as written.
  - **B (proven):** a "scratch copy" paragraph, Write and Edit tools, and this sentence added to the brief: "Prove each finding above Nit with a run against the real code: a failing test or a script … A finding you could not run is at most a Nit."
  - **Held the same:** permissions, sandbox and prompt skeleton. The arms' full command lines differ only in the variable (`arms-args.diff`).
- **Inputs:** 8 `sidedoor` ai-agent backend tickets (15, 16, 25, 28, 29, 30, 31, 32), each in two conditions:
  - **Seeded:** 3 real bugs that past reviews had found, re-created, plus 16 synthetic bugs written by codex.
    - Every planted bug sits in code the ticket changed, keeps typecheck and the covering specs green, and has a named caller that reaches it.
    - Ticket 32's real seed also removes the spec the original fix added.
  - **Clean:** the committed, post-fix code.
- **Isolation:** each input is its own clone holding history only up to the ticket's starting commit, so no later commit can give away the answer.
  - The whole diff sits uncommitted, as in a real review.
  - Reads of the run logs, harness and answer keys are denied, and a probe confirmed it.
  - The tool traces show no attempt to read them (`leak_suspect` 0).
- **Metric:** per review:
  - seeds hit, by a hit rule fixed before the run: same file and the defect's effect, located by a line within ±10, the enclosing function, or a quote of the seeded code;
  - findings above Nit that hit no seed, judged by codex (gpt-6.1-sol) as false, real-but-unseeded or unsure, with the findings shuffled and the arms stripped;
  - wall time, tokens and cost.
- **Size:** 1 repetition, so 32 reviews (16 per arm). The design allowed 3 repetitions with a pause after the first. The pause triggered, and the user stopped the run there.
- **Prices:** Claude Code's `total_cost_usd` (CLI 2.1.316, list cost basis, 2026-11-03). Codex grading ran on the codex login and is logged apart.

## Results

From `raw/full/reviews.jsonl` and `raw/full/graded/*.json`, recomputed by the orchestrator.

| Per arm, 16 reviews | A (current) | B (proven) |
|---|---|---|
| Reviews ok / failed | 16 / 0 | 16 / 0 |
| Synthetic seeds hit | 14 / 16 | 14 / 16 (same 2 missed: 16 S2, 29 S4) |
| Real seeds hit | 0 / 3 | 0 / 3 |
| Seed hits tagged above Nit | 11 | 13 |
| Hits on clean inputs | 0 | 0 |
| Findings: Important / Nit / Pre-existing | 12 / 10 / 1 | 16 / 7 / 0 |
| Non-hit findings above Nit, codex verdict | 1 false, 1 Pre-existing | 3 real-but-unseeded |
| … after the run-log correction below | 1 false | ≥ 1 false, 2 real-but-unseeded |
| Median / total wall time | 46 s / 773 s | 89 s / 1,422 s |
| Cost | $6.18 | $8.04 |
| Proof runs (tests or scripts B ran) | — | 34 |

**The grader against past human triage.** 4 of the 18 sampled non-hits match findings already triaged in the sidedoor run logs. Codex agrees on 3:
- per-step milestone events (15, deferred Important): agrees;
- an ad-hoc closing step (15, deferred Pre-existing): agrees;
- an unbounded search word count (29, deferred Nit): agrees.

It disagrees on B's Important about the ticket 31 truncation spec. Codex called it real; ticket 31's run logged it `rejected: wrong` after a real-model probe showed the provider never sends that stream shape. B's proof ran against the SDK adapter, so it proved something about the adapter, not about production. The remaining 14 sampled findings have no human label.

**Spend:** $14.22 for the full run, plus about $4 for the smoke runs, against a $150 cap. There were 0 retries and the stop rule never fired.

## What it means for the Bugs brief

- **Keep the current brief.** Proof requirements cost about 2× the time, and there is no evidence they cut false findings: false findings above Nit are rare for this reviewer in the first place (also 1 `rejected: wrong` in 13 historical Bugs lines).
- **Proof is not truth.** A run against a mock or adapter can prove a wrong finding with confidence. Any future proof rule has to say what counts as real (a real provider, a real database), or it adds false confidence.
- **Worth a separate test: severity.** B tagged its hits Important more often (13 vs 11), and in the smoke run it proved with a failing spec a bug that A had called a Nit. A follow-up should use bugs that escaped review and score severity calibration, not raw recall.

## Limitations

- **One repetition.** The smoke runs showed large run-to-run variance (the same arm hit a seed once and missed it the next time), so per-arm differences of 1–2 are noise.
- **Seed difficulty.** The synthetic seeds sat at a ceiling (88% for both arms) and the real ones at a floor (0 of 3), so recall could not separate the arms. Only 3 real seeds exist.
- **Grader reliability.** Codex was wrong on 1 of the 4 non-hits that can be checked against the run logs, and the one it got wrong is the most consequential. The other 14 sampled non-hits were not labelled by a human.
- **One narrow seed.** Seed 25 syn-2 is reachable only when the replay tokens exactly equal the ceiling.
- **Same model family.** The reviewers ran with project settings only, not the user's settings, and both arms are Claude; codex wrote the synthetic seeds and graded.
- **Clean inputs are post-fix code** that had already been through one review-and-fix round, which lowers the false-finding rate on them.
- **Ticket 15's range.** It was first built from a range that also held tickets 25 and 28. That was caught and rebuilt before the freeze.

## Sources

- **Ticket:** `docs/experiments/01-proven-bugs-reviewer.md`.
- **Run file:** `docs/experiments/runs/01-proven-bugs-reviewer.md` (ground, the design agreed at Gate A, every decision and amendment).
- **Harness:** branch `experiment/01-proven-bugs-reviewer` @ `2baeb02`, folder `experiments/01-proven-bugs-reviewer/`, with the arms' files under `agents/`, seeds and answer keys under `seeds/`, and `arms-args.diff`.
- **Run command, rep 1:** `python3 run_reviews.py --raw <raw> --tickets 15 16 25 28 29 30 31 32 --conditions seeded clean --reps 1 --seed 1`, then `grade.py --raw <raw> --seed 1` and `summary.py --raw <raw>`.
- **Raw output:** `docs/experiments/runs/01-proven-bugs-reviewer/raw/` (per-review rows, extractions and grades are in git; the full review transcripts in `claude-json/` and the codex logs stay on the machine that ran it):
  - `full/`: rep 1, with `summary-rep1.json` and the human-check sheet `samples/human-check.md`;
  - `smoke/`, `smoke-check/`, `smoke-2/` and `smoke-regrade/`: the smoke runs;
  - `smoke-2/leak-probe/`: the leak probe.
