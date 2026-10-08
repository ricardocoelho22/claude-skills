---
name: codex-implement
description: Implement a code task by delegating to codex, then review and verify it. Use when the user wants a feature built or a bug fixed by codex ("have codex implement X", "get codex to build this", "route this ticket to codex").
---

Deliver a code change through codex: codex writes, and you own the seams, the review, and the verification before it lands. Invocation mechanics live in `codex`, including the rule that every run goes in the background. This skill is the pipeline on top.

## Before delegating: agree the seams

TDD at the wrong seam is expensive to redo. Confirm the public seams the tests will sit at with the user; if they aren't agreed yet, propose them and get an OK. Then write the brief.

## The pipeline

1. **Delegate.** Hand codex the brief through the `codex` skill's wrapper (`codex-run.sh`), in the background. The brief states the work and tells codex to *use `$tdd` at the agreed seams, typecheck as you go, and run the relevant tests.* When the run exits, take the `-o` result and the git diff.

2. **Review with a second codex agent.** Start a fresh, read-only codex run of `$code-review`, also in the background, and have it return a structured verdict:

   ```
   ~/.claude/skills/codex/scripts/codex-run.sh -s read-only \
     --output-schema ~/.claude/skills/codex-implement/verdict.schema.json \
     -o <scratch>/review.md \
     "Run \$code-review of the changes since <base>. The spec is <spec path, or the task as briefed>. Return the verdict: fail when any issue must be fixed before commit."
   ```

   Name the spec: `$code-review` otherwise stops to ask for one, and a non-interactive codex cannot answer.

   `review.md` comes back as JSON matching `verdict.schema.json`: a `pass`/`fail` verdict plus located issues.

   Lighter native alternative: `codex review --uncommitted`.

3. **Verify yourself.** Read the diff. Run the full test suite and the typecheck yourself. Codex's report that tests pass is a claim, and your own green run is the delivery.

4. **Loop if needed.** On a failing test, a typecheck error, or a `fail` verdict, send codex a follow-up brief to fix it (resume the session or start a new exec), then re-verify from step 3.

5. **Commit** to the current branch once tests are green, typecheck is clean, and the verdict is pass.

6. **Report.** Summarize what changed, the review verdict, and the test/typecheck status.

Done means: tests green, typecheck clean, verdict pass, committed.

## Model

Both the implement and the review runs default to `gpt-6-sol`/high from config. Step up to `-m gpt-6-astra` when the brief is design-heavy; step down to `-m gpt-6-luna` for a mechanical fix-up loop. Slugs and effort levels are listed in `codex`.
