---
name: scout
description: "Size a spec or ticket(s) before implementing: reads it, does light recon, and recommends /implement or /implement-fleet with reasoning — then hands off to whichever one the user confirms."
disable-model-invocation: true
argument-hint: "path to the spec or ticket(s)"
---

# Scout: size the work, then route it

`/implement` and `/implement-fleet` reach the same destination — working, reviewed, committed
code — by different means: one you execute yourself, the other you orchestrate across pinned
sub-agents. Picking wrong wastes something either way — orchestration overhead on a one-file fix,
or a context overflow halfway through a five-ticket migration. This skill exists to make that
call before either one starts, from actual evidence instead of a guess.

## What this skill is not

Do not implement anything here. Do not write code, do not open Gate A, do not spawn `impl-tdd` or
`impl-explorer`. This is reconnaissance and a decision, nothing else. If you find yourself outside
"reading and deciding," you've wandered into the skill you were supposed to route to.

## 1. Read the work, in full

Read the spec or every ticket the user pointed at, yourself, before anything else. If it's a set
of tickets, note whether they name blocking edges or an order — that's a fleet signal, below.

## 2. Light recon — enough to size, not enough to design

Using Grep/Glob/Read directly (no sub-agents — this must stay cheap), answer:

- **How many git repos does this plausibly touch?** Check the workspace layout / CLAUDE.md for
  repo boundaries if unclear, and grep for the systems/services the spec names.
- **How many genuinely separate subsystems or files?** A handful of edits in one module reads
  differently than changes spread across unrelated directories.
- **How many seams, and are they obvious or open questions?** Skim the touched code paths — is
  there one clear place to hang a test, or several places where the right seam is a judgment call
  the user hasn't made yet?
- **Is this one ticket or several, and do they have a dependency order?**

Keep this fast — a few targeted greps and a handful of file reads. If the spec references a
subsystem you don't recognize, one Explore agent call is acceptable to orient (not more) — this is
sizing, not the recon phase itself; `implement-fleet`'s own Phase 1 redoes it properly if the
fleet gets picked.

## 3. Decide

Lean **`/implement-fleet`** when two or more of these are true:

- More than one git repo is plausibly touched.
- More than one ticket, with a real dependency order between them.
- The touched area spans unrelated subsystems, not a single cohesive slice.
- There are genuinely open seam questions that need a user decision before any test is written.
- Reading the spec plus the likely-touched files yourself would leave little headroom for the
  implementation and review that follow in the same context.

Lean **`/implement`** otherwise — in particular for a one-file change, a bug fix you already
understand, or anything where framing the work as a fleet costs more than doing it. (This is
`implement-fleet`'s own stated boundary — respect it, don't re-litigate it.)

If the signals split roughly evenly, say so plainly and let the user break the tie — don't force a
confident-sounding recommendation out of a genuinely close call.

## 4. Report and confirm

Tell the user, concretely and briefly:

- What you found — repo count, ticket count/order, subsystem spread, seam clarity — the actual
  evidence, not just the verdict.
- Your recommendation and the one or two signals that drove it.

Ask the user to confirm or override — use `AskUserQuestion` with the recommended option
pre-highlighted and the other as an explicit alternative. Do not invoke either skill until they
answer.

## 5. Hand off

On confirmation, invoke the chosen skill (`/implement` or `/implement-fleet`) yourself, passing
through the same spec/ticket path. Don't re-explain the work to the user first — the chosen skill
reads the spec itself in its own first step.
