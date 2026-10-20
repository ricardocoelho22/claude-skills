# Notes for the multi-ticket skill

On 2026-10-20, `orchestrate` was trimmed to one ticket per run. This file keeps what came out of it, plus the run-wide pieces that `orchestrate` still repeats on every ticket, so the skill that drives several tickets can pick them up.

## Removed from orchestrate

**Ticket order.** The plan ordered tickets by their blocking edges. The new skill owns that order, and with it the decision of which tickets can run in parallel.

**Mixed experiment runs.** When only some tickets were experiments, the plan marked each one `experiment` and gave it no cycles. In its place in the order, the ticket ran through `~/.claude/skills/experiment/SKILL.md` instead of Phase 1. That skill keeps its own run file and gates and ends back on the working branch. The cross-ticket review left experiment tickets out. (`orchestrate` still hands a single experiment ticket to `experiment`.)

**Two bases.** The run pinned `BASE`, the HEAD per repo at the start of the run, and each ticket pinned `TICKET_BASE`, the HEAD per repo when that ticket started (that is, after the earlier tickets' commits). Per-ticket review, fix, trim, manual checks and Gate B used `TICKET_BASE`; the cross-ticket review used `BASE`. Now `orchestrate` has only `BASE`, so when the new skill invokes it per ticket, that ticket's `BASE` is what used to be `TICKET_BASE`. The new skill keeps the run-level base itself.

**Cross-ticket review (old Phase 2), verbatim:**

> Each ticket was reviewed on its own. Once all are committed, invoke `/code-review` with fixed point BASE, reviewers spawned as `impl-reviewer`, and add to the brief: **per-ticket review is done; report only issues that span tickets** (duplicated helpers, inconsistent naming, contracts that drifted between tickets). Triage and fix as in steps 2–3, then run the full test suite once per repo and compare failures against the BASE failures. Show the fixes at a Gate B (the report's title line, the review line, one line per fix, and `Commit?`) and commit on approval.

**The loop at Gate B.** After a commit, the next ticket started at Phase 1. Gate A was re-opened only when a ticket needed seams the plan did not cover, because there was one plan for every ticket and Gate A was held once for all of them.

**Finish report.** It listed the tickets landed, ahead of the commits per repo.

## Run-wide work orchestrate now repeats per ticket

If the new skill invokes `orchestrate` per ticket, each of these runs once per ticket. Decide which of them the new skill does once and passes in, and give `orchestrate` a "skip this if the caller provides it" seam for each:

- **Backend check**, plus the rule "after two codex failures in one run, switch the rest of the run to `claude`". Per ticket, the failure count resets.
- **BASE failures**, a full test-suite run per repo. Done per ticket, it costs one full-suite run per ticket. Done once, a later ticket has to tell its own failures apart from failures an earlier ticket introduced.
- **Explorer recon.** Some of it (commands, test setup, reuse candidates) holds across the whole feature.
- **Feature page create.** Only the first ticket creates the page; later tickets refresh it.
- **Run file.** Currently one per ticket under `<feature>/runs/<slug>.md`. The new skill probably wants its own run file that points at each ticket's run file.

## Constraints for parallel tickets

- **One executor per working tree.** `orchestrate` runs executors one at a time because two in one tree collide. Parallel tickets need one worktree each (see the `implement-spec` idea of worktrees plus an integration branch).
- **Checkpoints are per repo.** The snapshot copies that repo's index, so each worktree needs its own index snapshot. Store each one in that ticket's run dir.
- **Only the main session publishes the feature page.** Sub-agents can build the page but cannot publish it, and refreshes run one at a time. With parallel tickets, status changes arrive from several runs at once, and the main session has to merge them into one refresh at a time.
- **Gate B stays per ticket**, in the main session, because sub-agents cannot talk to the user. Parallel tickets therefore queue their Gate Bs for the user.
