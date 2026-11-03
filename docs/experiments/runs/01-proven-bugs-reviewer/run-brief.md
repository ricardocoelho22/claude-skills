# Run brief — experiment 01, proven-bugs reviewer, rep 1

**Mode: run.** Run the frozen harness, change no code.

- Frozen harness: branch `experiment/01-proven-bugs-reviewer` at commit `2baeb02`, checked out in `/Users/ricardocoelho/Code/claude-skills-experiment-01-proven-bugs-reviewer` (H = `<that>/experiments/01-proven-bugs-reviewer`). Check `git -C <that> rev-parse --short HEAD` is `2baeb02` and `git status --short` is empty before you start, and again before you return.
- Design: `/Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer.md`.
- Raw output: `/Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer/raw/full/` (new; must not hold `reviews.jsonl` yet).

## Run

This call runs **rep 1 only** (the design's pause point), all 16 inputs, both arms: 32 reviews.

```
cd H
python3 run_reviews.py --raw <raw> --tickets 15 16 25 28 29 30 31 32 --conditions seeded clean --reps 1 --seed 1
python3 grade.py --raw <raw> --seed 1
python3 summary.py --raw <raw> > <raw>/summary-rep1.json
```

Run the reviews with Bash in the background and wait for the completion notice; expect 30–60 min. The runner enforces the $150 cap and the failed-call stop rule itself. A bug that blocks the run is a stop-and-report, not a fix. Save everything the commands print to `<raw>/run-rep1.log`.

## Boundary

- No code changes, no commits, no reps 2–3.
- Leave no background processes when you return (claude, codex, mongod); the stray mongod pid 14780 is not yours.
- Leave the run file alone.

## Return

Your role file's format (run mode), under 400 words, plus, from the raw rows only: per arm, reviews ok/failed, seeds hit (real and synthetic apart), findings by tag, false / real-but-unseeded / unsure findings above Nit, `leak_suspect` count, median and total wall time, cost; B's `proof_runs` count; spend against the cap.
