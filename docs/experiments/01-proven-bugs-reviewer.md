# 01: Does a Bugs reviewer that must prove its findings review better?

Status: done
Blocked by: none

Run with `/rc-experiment docs/experiments/01-proven-bugs-reviewer.md`. The design below is a proposal; Gate A settles every field.

## Question

`rc-orchestrate` step 2 runs a Bugs reviewer that checks its findings by reading. pstack's `interrogate` keeps only findings a run proves: "Leave out anything you did not run." Requiring proof should cut findings that send the fixer after code that was fine, but it costs time and may lose real bugs that are hard to run. Is the trade worth it?

## Claim

Requiring the Bugs reviewer to prove each `Important` finding with a command and its output halves false positives per review, without losing recall on seeded bugs.

## Arms

The one variable is the proof requirement in the Bugs brief.

- **A (current):** `rc-reviewer` with the Bugs brief from `rc-orchestrate` step 2, verbatim.
- **B (proven):** the same brief, plus: "Prove each Important finding with a run against the real code: a failing test or a script, in the scratch copy named below. Report the command, the output it printed, and the output the ticket requires. A finding you could not run is at most a Nit, with the reason it could not run." B needs a writable scratch copy of the repo at the reviewed state, and Bash beyond reading; A gets the same copy, read-only.

Both arms: same model and effort (`rc-reviewer`'s opus · medium), same diff, same ticket path, same word cap.

## Inputs

The eight `sidedoor` ai-agent tickets with review logs (15, 16, 25, 28, 29, 30, 31, 32), each as BASE..its ticket commit (BASE per repo is in `sidedoor/z-features/ai-agent/runs/<ticket>.md`). Committed code is the post-fix state, so every input is a seeded copy of it:

- **Real seeds**: past Bugs findings logged `fixed`, re-planted at their `file:line` (29: contacts `deletedAt: null` vs `$exists:false`; 29: microsite slug taken aborts the seed run; 32: retry re-anchors `textAfterProposal`). About 3–4 exist, so they show realism, not a rate.
- **Synthetic seeds**: one-hunk mutations in the classes the Bugs brief names (empty/null, boundary, unhandled error path, broken caller, missing authorization), 2–3 per diff, each a patch file with a one-line answer key written before any run.
- **Clean control**: each diff with no seed, to count false positives where the right answer is none.

## Metric

Per review: seeds hit (recall), findings that hit no seed (false positives), wall time, tokens. Report recall for real and synthetic seeds apart (`confounds.md`, *What gets judged*).

- **Hit rule**, fixed before the run: a finding names the seed's file, points within ±10 lines or at the enclosing function, and describes the defect's effect.
- **Grader**: a codex call (another model family than both arms) applies the hit rule to shuffled findings with arm names stripped. You label a blind sample of the non-hits as real-but-unseeded or false, so a real bug found in the committed code is not counted against an arm.

## Size

8 diffs × (seeded + clean) × 2 arms × 3 repetitions = 96 reviews. Smoke: 1 diff × 2 arms × 1 repetition.

## Decision rule

Adopt B when its recall is no more than one seed below A's and its false positives per review are at most half of A's, at a median wall time at most twice A's. When B cuts false positives but loses recall, try the split: proof required only for `Important`, read-only for the rest.

## Open questions for Gate A

- **Budget**: reviews run on the subscription or the API? The cap follows from that.
- **Running sidedoor tests in a scratch copy**: needs the worktree setup script and, for the backend, in-memory Mongo. If the smoke shows B cannot run tests, proof falls back to a script against the module, or the experiment shrinks to the frontend and pure-function diffs.
- **Seeds per diff**: 2–3 in one diff is cheaper; one per diff makes hits unambiguous.
- **n**: 96 reviews may still leave the arms within each other's spread; the smoke's per-arm spread decides.

## Where it leads

A confirmed claim changes the Bugs brief in `rc-orchestrate` step 2 and the tools in `agents/rc-reviewer.md`. A refuted one is still worth a line in `rc-retro`'s notes: the review log's rejected rate is then the noise to accept.

## Answer

Inconclusive; keep the current Bugs brief. Requiring proof did not change recall (both arms found 14 of 16 synthetic bugs and 0 of 3 real ones). The current reviewer made too few false findings (1 in 16 reviews) for a cut to show. The proving reviewer cost 1.9× the wall time and once "proved" a wrong finding against an adapter. Full write-up: [01-proven-bugs-reviewer-results.md](01-proven-bugs-reviewer-results.md).
