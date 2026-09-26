---
name: implement-fleet
description: "Implement a spec or set of tickets as an orchestrator: you frame the work and hold the user gates, while pinned sub-agents explore, write code test-first, and review. Use for multi-ticket or multi-file work where one agent's context would overflow."
disable-model-invocation: true
argument-hint: "path to the spec or ticket(s)"
---

# Orchestrated implementation

Same destination as `/implement` — working, reviewed, committed code — but split across sub-agents so no single context holds everything, and each phase runs on the model sized to it.

**You are the orchestrator.** You write briefs and hold gates; executors write code. Finding yourself editing a source file means you have taken an executor's job and spent the context budget that makes this skill worth running.

Your four jobs, in priority order:

1. **Hold the gates.** Sub-agents cannot talk to the user. Every human decision happens here, or it does not happen.
2. **Write the briefs.** A sub-agent knows nothing about this conversation. Brief quality caps output quality.
3. **Verify the returns.** A sub-agent's summary is a claim. Re-run the checks yourself.
4. **Carry the thread.** You are the only participant who sees the whole run.

## The cast

| Role | Agent | Model | Effort | Why |
|---|---|---|---|---|
| Orchestrator | — (you) | your session model | session | Judgment, gates, cross-slice coherence |
| Explorer | `impl-explorer` | sonnet | medium | Recon is structured output, not synthesis |
| Test-writer / Implementer | `impl-tdd` | sonnet | medium | Mechanical output from a confirmed spec and seams |
| Fixer | `impl-fixer` | sonnet | high | Debugging across a full diff; reasoning depth earns its keep |
| Reviewer | `impl-reviewer` | opus | medium | Judgment quality is the constraint, not reasoning depth; model over effort |
| Doc-writer | ad hoc, haiku | haiku | low | Pure output, no judgment — the manual testing guide |

Model and effort are pinned in `~/.claude/agents/`. Override only on explicit user request. Spawn all agents with `run_in_background: false`. Agents touching the same files in parallel will collide — keep them sequential.

---

## Phase 0 — Frame and recon

Read the spec or tickets yourself, in full. This reading is your ground: the source of truth you will judge every sub-agent return against.

**Pin the ground.** For each git repo the work touches:

```
git -C <repo> rev-parse --abbrev-ref HEAD    # branch
git -C <repo> rev-parse HEAD                 # BASE — record it
git -C <repo> status --porcelain             # must be clean, or ask the user
```

A workspace can span several independent repos. Check; do not assume. Pin a separate BASE per repo.

**Explore the codebase yourself.** Read the relevant files, grep for existing patterns and utilities, check the test structure, and verify the exact commands from `package.json` or the project config. Your recon must produce — before you move on:

- **Files in scope**: each file that must change and what kind of change (new / extend / wire-up).
- **Reuse**: existing utilities, helpers, fixtures, or types this work should call instead of reimplementing. An executor who misses one reimplements it.
- **Seams**: public boundaries where behavior is observable without reaching inside — HTTP routes, exported methods, component props, module exports. For each: current signature, and whether a test already exists there.
- **Commands**: exact, verified-from-config commands for single test file, full suite, typecheck, and lint. Name the package manager.
- **Risks**: shared state, generated code, env vars, tests already failing on BASE.

Note: the driver doing its own recon fills your context window with raw file content. On large codebases, if context is a concern, consider restoring the `impl-explorer` delegation for this phase.

**Order the tickets.** Read their blocking edges and state the order you derived.

**Track status.** As work moves through the run, keep each ticket's status current in its markdown file under `features/`:

- Starting a ticket's slices → `in-progress`
- Gate B commit approved → `done`
- Escalated to user mid-work (blocked, ambiguous seam) → `needs-info`

**Open the run file.** Create `.scratch/implement-fleet/<slug>.md`. It holds: spec path, each repo's BASE sha and branch, ticket order, confirmed seams, verified commands, and a per-slice landing log. You are the only writer; sub-agents may read it. Confirm `.scratch/` is gitignored first; if not, use the session scratchpad directory and put its path in every brief.

Done when: you have a clear map of the work, verified commands, a seam inventory, and a clean working tree.

## Gate A — Seams and slice order 🚦

Stop here only when the plan has open questions the user must resolve: seam candidates you cannot choose between, spec ambiguities with significant downstream cost, or unknowns that would force a re-do if wrong. If the plan is clear, state the seams and slice order you derived, write them into the run file verbatim, and proceed.

When you do stop:

- the **seams** to test, each with one line on why it earns a test;
- the **slice order** — the vertical slices, in sequence;
- the specific questions blocking you — one per message.

Wait for the answer before proceeding. The confirmed seams go into the run file verbatim — that exact wording goes into every test-writer and implementer brief.

## Phase 1 — Implement, slice by slice

Each slice runs two agents in sequence. Complete both before starting the next slice.

### 1a — Write tests (`impl-tdd`, sonnet)

Brief the test writer with the confirmed seams for this slice, the exact commands, all relevant paths, and this explicit boundary: **write failing tests only — return before writing any production code.**

Verify the return:

```
git -C <repo> diff --stat
git -C <repo> diff
<single test file command>    # from the run file — all tests must fail
```

Every modified file must be a test file. Every test must fail for the right reason — not an import error or missing fixture, but a genuine behavioral gap. When a test passes before any production code is written, the seam is wrong; return the question to the user.

### 1b — Implement (`impl-tdd`, sonnet)

Brief the implementer with the failing test file(s), the exact commands, all relevant paths, and this explicit boundary: **make the red tests green — write no new tests, no speculative additions.**

Verify the return:

```
git -C <repo> diff --stat
git -C <repo> diff
<typecheck command>           # from the run file
<single test file command>    # from the run file — all tests must pass
```

The diff must touch production files only. All tests must pass. When an implementer reports it is blocked: re-brief with a tighter scope. The fix is a new brief.

Append what landed to the run file, then start the next slice.

## Gate B — Ready to commit 🚦

After all slices for a ticket are verified, report: what landed, verified test and typecheck output (actual output, not a paraphrase), and any deviations. Ask whether to commit and continue.

On approval, commit per repo on the current branch in the project's commit style. Return to Phase 1 for the next ticket, reusing the run file and confirmed seams. Re-open Gate A only when a new ticket needs seams the user has not yet confirmed, or introduces an ambiguity the current seam set does not resolve.

## Phase 2 — Final review

Once all tickets are committed, invoke `/code-review` on the full diff since BASE. This runs its own sub-agents and returns consolidated Standards and Spec findings.

Triage the findings yourself against your reading of the code. Sort into: fix now, deferred (logged in the run file), or rejected.

Send the fix-now set to `impl-fixer` as one consolidated brief — quoting each finding with your triage decision. The fixer works across the full diff, not a single slice. Re-verify with the full typecheck and the single-file commands for every touched test file. Cap at **one fix round**; a second means a structural problem — stop and take it to the user.

Commit the fixes per repo before moving to Finish.

## Manual testing guide

For each ticket landed in this run, write a short guide to the checks a human runs by hand — the ones the test suite doesn't touch: visual states, UI flows, timing, anything that needs a human eye. Delegate the writing to an ad hoc agent on haiku, low effort — this is pure output, no judgment.

Brief it with: the ticket or spec content, the confirmed seams for that ticket, and `git diff` against BASE for that ticket's commits. Ask for a short markdown file: what to set up, the steps to run through, what a human should see at each step. No restatement of code, no automated-test coverage, no filler — a human should be able to follow it cold.

Save it next to the ticket or spec it covers, as `manual-test-<NN>-<slug>.md` in the same directory. Verify the return: the file exists at that path and every step is something a human actually does by hand.

## Finish

Run the **full test suite once**, per repo, yourself, plus lint and build if the project defines a combined gate. Report the real output. Then summarize: tickets landed, commits per repo, manual testing guides written and where, deferred findings from the run file, anything left unverified.

---

## Writing a brief

A sub-agent has no access to this conversation, the spec, or the user's answers. Every brief is self-contained or it is broken. Include:

- **The goal**, in your own words — not a pasted ticket title.
- **The confirmed seams**, verbatim from the run file.
- **Exact commands** for typecheck and single-file tests, and the package manager.
- **Paths**: the run file, the spec, the repo root, the files in scope.
- **The boundary** — what is explicitly out of scope for this agent, and the instruction to stop and report rather than expand.
- **What to return**, concretely.

Quote content directly — "as discussed", "the above", and "the usual pattern" do not resolve inside a sub-agent.

## When not to use this

A one-file change, a bug fix you already understand, or any task where framing costs more than doing. Use `/implement` for those — orchestration overhead on small work is pure loss.
