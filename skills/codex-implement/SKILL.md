---
name: codex-implement
description: Implement a code task by delegating to codex, then review and verify it. Use when the user wants a feature built or a bug fixed by codex ("have codex implement X", "get codex to build this", "route this ticket to codex").
---

Deliver a code change through codex: codex writes, you own the seams, the review, and the verification before it lands. Invocation mechanics live in `codex` — this skill is the pipeline on top.

## Before delegating: agree the seams

TDD at the wrong seam is expensive to redo. If the public seams the tests will sit at aren't already agreed with the user, propose them and get an OK first. Then write the brief.

## The pipeline

1. **Delegate.** Hand codex the brief with `codex exec` (see `codex`). The brief states the work and instructs codex to: *use `$tdd` at the agreed seams, typecheck as you go, run the relevant tests.* Capture the `-o` result and the git diff.

2. **Review — a second codex agent.** A fresh, read-only codex running `$code-review`, returning a structured verdict:

   ```
   codex exec -s read-only --output-schema <scratch>/verdict.json \
     -o <scratch>/review.md \
     "Run \$code-review of the changes since <base>. Return {verdict:'pass'|'fail', issues:[{file,line,severity,note}]}."
   ```

   Lighter native alternative: `codex review --uncommitted`.

3. **Verify yourself.** Read the diff. Run the full test suite and the typecheck yourself. Codex's word that tests pass is not delivery — you confirm it.

4. **Loop if needed.** On a failing test, a typecheck error, or a `fail` verdict, send codex a follow-up brief to fix (resume the session or a new exec), then re-verify from step 3.

5. **Commit** to the current branch once tests are green, typecheck is clean, and the verdict is pass.

6. **Report.** Summarize what changed, the review verdict, and the test/typecheck status.

Done means: tests green, typecheck clean, verdict pass, committed.

## Model

Defaults to `gpt-6-sol`/high from config, for both the implement and the review runs. Step up to `-m gpt-6-astra` when the brief is design-heavy; step down to `-m gpt-6-luna` for a mechanical fix-up loop. Slugs and effort levels per `codex`.
