---
name: orchestrate
description: "Implement a spec or set of tickets as an orchestrator, with codex agents as the executors and Claude agents as the fallback."
disable-model-invocation: true
argument-hint: "path to the spec or ticket(s)"
---

# Orchestrated implementation, codex-first

Working, reviewed, committed code, with codex doing the execution and Claude doing the review. Code written by one model family and reviewed by another is the point: each catches the other's blind spots.

**You are the orchestrator.** You write the plan and the briefs, hold the gates, and verify every return. Executors write code. Finding yourself editing a source file means you have taken an executor's job.

Your four jobs, in priority order:

1. **Hold the gates.** Sub-agents cannot talk to the user. Every human decision happens here, or it does not happen.
2. **Write the briefs.** Brief quality caps output quality (see *Writing a brief*).
3. **Verify the returns.** An executor's summary is a claim. Re-run the checks yourself.
4. **Carry the thread.** You are the only participant who sees the whole run.

## The cast

| Role | Role file | Codex route | Claude fallback |
|---|---|---|---|
| Orchestrator + planner | — (you) | — | session model |
| Explorer | `impl-explorer` | `gpt-6-sol` · medium · `read-only` | `impl-explorer` |
| Test-writer / Implementer | `impl-tdd` | `gpt-6-sol` · medium | `impl-tdd` |
| Fixer | `impl-fixer` | `gpt-6-sol` · high | `impl-fixer` |
| Manual checklist | — (ad hoc) | `gpt-6-luna` · low | general-purpose, `model: haiku` |
| Test trimmer | `impl-trimmer` | `gpt-6-sol` · medium | `impl-trimmer` |
| Reviewer | `impl-reviewer` | — (always Claude) | `impl-reviewer` (opus · medium) |

Role files live in `~/.claude/agents/`. Both backends read the same file, so a role has one definition.

## Rungs

The cast sets each executor's default; the reviewer stays pinned to its cast entry. Three cases move an executor call up or down this ladder:

| Rung | Claude (`model` · `effort`) | Codex (`-m` · effort) |
|---|---|---|
| 1 | `haiku` · low | `gpt-6-luna` · low |
| 2 | `haiku` · medium | `gpt-6-luna` · medium |
| 3 | `sonnet` · medium | `gpt-6-sol` · medium |
| 4 | `sonnet` · high | `gpt-6-sol` · high |

On a Claude call, set the Agent tool's `model` and `effort`; on a codex call, `-m` and `-c model_reasoning_effort=`. Rung 4 is the ceiling: moves never go past it. Log each call's rung, and every step-up, in the run file's landing log.

- **Cycle marks.** Executors on a cycle the plan marks `mechanical` run one rung down from their default; `design-heavy`, one rung up.
- **Step up.** When verification rejects a return because the executor fell short (tests red for the wrong reason, typecheck failing, files touched outside its scope, checks left failing), re-run that step one rung up. A rejection that points at the plan (a test green before any production code, a seam that cannot hold) goes to the user instead: a stronger model cannot fix a wrong plan.
  - The re-run is a fresh call with the new rung's flags. Before it, restore every file the rejected return touched outside its scope from the call's checkpoint (see *Executors*), keep its in-scope work, and put the failing check output in the brief.
  - Each step steps up at most once. A second rejection, or a rejection at rung 4, goes to the user. The fixer's review round starts at rung 4, so its rejection goes straight to the user; Gate B change requests start lower and can step up.
  - A failure counts against the executor unless it is on the BASE failures list, or three re-runs on unchanged code both pass and fail; log a flaky test next to the BASE failures.
  - A blocked executor has not been rejected: it gets a tighter brief (step 1b).
- **Gate B changes.** Sized by the request; see *Gate B*.

## Executors

Executors run one at a time, since two executors touching one working tree collide. While one runs in the background, the working tree is its alone. Spend the wait on the user and the run file, and verify once its completion notice arrives.

**Backend check** (once, in Phase 0):

```
~/.claude/skills/codex/scripts/codex-run.sh -m gpt-6-luna -c model_reasoning_effort=low -s read-only \
  -o <run-dir>/probe.md "Reply with OK."
```

It runs in the foreground, since it takes seconds. Exit 0 → backend `codex`. Anything else → backend `claude` for the whole run. Record the backend in the run file.

**Codex call.** Through the `codex` skill's wrapper, from the repo root so session lookup by cwd works:

```
cd <repo> && ~/.claude/skills/codex/scripts/codex-run.sh -s <sandbox> -m <model> -c model_reasoning_effort=<effort> \
  -o <run-dir>/<ticket>-<cycle>-<role>.md \
  "Your role is defined in ~/.claude/agents/<role>.md: read it and follow it, ignoring its frontmatter. <brief>"
```

Sandbox is `workspace-write` unless the cast says `read-only`. Launch it with Bash `run_in_background: true`. Mechanics (flags, exit codes, background runs, delivery) are in the `codex` skill.

**Claude call.** The Agent tool with `subagent_type: <role>` and the same brief. Sub-agents already run in the background.

**Checkpoint.** Before every executor call, snapshot each repo's working tree without touching it (`<run-dir>` as an absolute path), and record the tree hash with the call in the run file:

```
cp "$(git -C <repo> rev-parse --path-format=absolute --git-path index)" <run-dir>/snap.idx
GIT_INDEX_FILE=<run-dir>/snap.idx git -C <repo> add -A && GIT_INDEX_FILE=<run-dir>/snap.idx git -C <repo> write-tree
```

`git -C <repo> diff <tree>` is then that call's delta, and `git -C <repo> restore --source=<tree> --worktree -- <file>` puts one file back as it was before the call (delete a file the call created).

**Fallback.** A codex call has failed when the wrapper exits non-zero. Check its delta against the checkpoint and restore what it touched, then re-run that one step on the Claude agent at the same rung and note it in the run file. After two codex failures in one run, switch the rest of the run to `claude`.

**Session hygiene.** Start a fresh codex session per role per cycle. Re-briefing the same executor on the same cycle at the same rung resumes instead, keeping its context and cache warm; a step-up is always a fresh call:

```
cd <repo> && ~/.claude/skills/codex/scripts/codex-run.sh resume --last -o <run-dir>/<ticket>-<cycle>-<role>-2.md "<follow-up brief>"
```

**New files.** After every executor return, run `git add -N` on the files it created, so every `git diff` below shows them.

---

## Phase 0 — Recon and plan

Read the spec or tickets yourself, in full, fetching ticket references through the repo's issue tracker (`docs/agents/issue-tracker.md`). This reading is your ground: the source of truth you judge every return against.

**Pin the ground.** For each git repo the work touches:

```
git -C <repo> rev-parse --abbrev-ref HEAD    # branch
git -C <repo> rev-parse HEAD                 # BASE — record it
git -C <repo> status --porcelain             # must be clean, or ask the user
```

A workspace can span several independent repos, so check for them and pin a separate BASE per repo.

**Open the run file.** Create `.scratch/orchestrate/<slug>.md` (the run dir is `.scratch/orchestrate/<slug>/`). It holds: spec path, backend, each repo's BASE and branch, BASE failures, the plan, and a per-cycle landing log. You are the only writer. Confirm `.scratch/` is gitignored first; if not, use the session scratchpad directory and put its path in every brief.

**Run the backend check.**

**Explore.** Brief the explorer with the spec path, the repo roots, and the feature in your own words. Save its report as `<run-dir>/recon.md` (a codex explorer's `-o` file already is). Spot-check it: open every file it names as in scope and every reuse candidate. Its report is a claim.

**Record BASE failures.** Run the full test suite once per repo. Write every failing test into the run file. A later failure on this list is pre-existing; a failure off it belongs to this run.

**Write the plan** into the run file yourself: mistakes here fan out into every later step.

- **Ticket order**, derived from blocking edges.
- **Per ticket:** its test-first cycles in sequence; for each cycle, the seams it tests (one line on why each earns a test), its acceptance criteria, and a `mechanical` or `design-heavy` mark when it sits off the norm (see *Rungs*).
- **Reuse**: helpers and fixtures executors must call instead of reimplementing.
- **Commands**: verified from config: single test file, full suite, typecheck, lint. Name the package manager.
- **Risks**: shared state, generated code, env vars, the BASE failures.

**Track status** the way the repo's issue tracker records it: `in-progress` when a ticket's first cycle starts, resolved the way the tracker closes work when Gate B's commit lands, `needs-info` when escalated to the user mid-work.

Done when: the run file holds the backend, BASE per repo, BASE failures, and a plan with seams for every cycle.

## Gate A — The plan 🚦 (optional)

Stop only when the plan has open questions the user must resolve: seam candidates you cannot choose between, spec ambiguities with real downstream cost, unknowns that force a re-do if wrong. Otherwise state the ticket order and proceed.

When you stop, invoke `/grilling` with two adaptations:

- **Root:** the open questions above, not the whole spec. Grill only what hangs off them; decisions the spec already settles are out of bounds.
- **Exit:** once the user confirms shared understanding, write each answer into the plan in the run file, then proceed.

## Phase 1 — Per ticket

Record `TICKET_BASE` (HEAD per repo) in the run file, then run steps 1–5.

### 1. Cycles

Each cycle runs two executors in sequence. Complete both before starting the next cycle.

**1a — Tests.** Brief `impl-tdd` in test-writer mode: the cycle's seams from the plan, the commands, the paths, and the boundary: **write failing tests only; return before writing production code.**

Verify: the call's delta (`git -C <repo> diff --stat <tree>`, then `git -C <repo> diff <tree>`), then the single test file command. Every changed file is a test file. Every test is red for a behavioral reason, not an import error or missing fixture. Typecheck errors are expected only where a test calls API the cycle has not built yet. A test green before any production code means the seam is wrong: take it to the user.

**1b — Implement.** Brief `impl-tdd` in implementer mode: the red test files, the commands, the paths, and the boundary: **make the red tests green; write no new tests and nothing speculative.**

Verify: the call's delta (against its checkpoint) touches production files only, typecheck is clean, the single test file is green. A blocked implementer gets a tighter brief, resumed on the same session.

Append what landed to the run file.

### 2. Review

Invoke `/code-review` and follow its steps with two adaptations:

- **Diff:** use `git diff <TICKET_BASE>` (working tree against the ticket's base) and the fixed point `TICKET_BASE`. The ticket is uncommitted, so the skill's `...HEAD` form would show nothing.
- **Reviewers:** where it spawns the Standards and Spec sub-agents, spawn each as `subagent_type: impl-reviewer`, with the prompt the skill specifies.

Triage the findings against your own reading of the code: fix now, deferred (logged in the run file with a reason), or rejected. A finding that a test is redundant, mock-only, off-seam, or tautological goes to the trim in step 5, not the fixer.

### 3. Fix

Send the fix-now set to `impl-fixer` as one brief, quoting each finding with your triage decision and listing every test file in `git diff --stat <TICKET_BASE>`. Verify with typecheck and the single test file command for every one of those test files, not only the ones the fixer touched. Cap at **one fix round**; a second means a structural problem: take it to the user.

### 4. Manual checklist

Brief the checklist executor to read `~/.claude/skills/manual-checklist/SKILL.md` and follow it, with the ticket path, base `TICKET_BASE`, and the output path `manual-test-<NN>-<slug>.md` next to the ticket.

Verify: the file exists and every item is a hand check.

### 5. Trim

Trim runs last, once the ticket's tests are final, so no fixer time goes into tests that are about to be cut. Brief `impl-trimmer` with the ticket's test files (from `git diff --stat <TICKET_BASE>`), the plan's seams for the ticket, the commands, and the test findings routed here in step 2.

Verify: the diff since the trimmer started only removes or merges test code, the tests stay green, and every removal carries a reason in its return. Put the removals in the run file for Gate B.

## Gate B — Ready to commit 🚦 (required)

The user reads the code here to stay grounded and catch quirks. Hand them a report that makes that fast: the `/diff-tour` of the ticket against `TICKET_BASE`, with the test and typecheck status on its title line and the run's lines appended, around 25 lines in all:

```
## Ticket <NN> — <title>        ✅ tests · ✅ typecheck
<the diff-tour body: Read first … Watch for>

Review:     <n> fixed · <n> deferred (<reason>) · <n> rejected
Trimmed:    <test name> — <reason>   (one line each, or "none")
Deviations: <from the plan, or "none">
Manual checks: <path> (<n> items)

Commit?
```

A ❌ replaces a ✅ when a check fails, and the real failing output goes below the report. Everything else stays in the run file.

**Change requests.** When the user asks for changes instead of approving, size each one by the first size that fits, in this order, and brief `impl-fixer` at its rung with the ticket's test files listed as in step 3. Each brief is its own round.

1. **Seam-changing**: a new seam or a changed contract. Add it to the plan as a new cycle and run steps 1–5 for it, then return here. Take it to the user first when it conflicts with a decision recorded in the plan.
2. **Within seams**: a test is added or edited, but only at seams the plan already names: rung 3.
3. **Local code** (a refactor, a symbol rename): the ticket's existing tests still describe the result, so no test is added or edited: rung 2.
4. **Text only** (docs, comments, a diagram): rung 1.

Batch same-rung requests into one brief. Verify as in step 3; a local-code return that touched a test file was sized wrong, so restore that test file from the checkpoint and re-run the request as within-seams. A request rejected at rung 4 is too big for a Gate B change: take it to the user as a new cycle or ticket. When behavior changed, update the manual checklist. Then re-show Gate B: after a within-seams change, the full report with a fresh `/diff-tour`; otherwise, the title line, one line per change, and `Commit?`.

On approval, commit per repo on the current branch in the project's commit style. Start the next ticket at Phase 1. Re-open Gate A only when a ticket needs seams the plan does not cover.

## Phase 2 — Cross-ticket review (multi-ticket runs only)

Each ticket was reviewed on its own. Once all are committed, invoke `/code-review` with fixed point BASE, reviewers spawned as `impl-reviewer`, and add to the brief: **per-ticket review is done; report only issues that span tickets** (duplicated helpers, inconsistent naming, contracts that drifted between tickets). Triage and fix as in steps 2–3, then run the full test suite once per repo and compare failures against the BASE failures. Show the fixes at a Gate B (the report's title line, the review line, one line per fix, and `Commit?`) and commit on approval.

## Finish

Run the full test suite once per repo, yourself, plus lint and build if the project defines a combined gate. Compare failures against the BASE failures; a new failure goes to the user before you report. Report: tickets landed, commits per repo, checklist paths, deferred findings, codex fallbacks taken, step-ups (role, cycle, from and to rung), anything left unverified.

Then offer `/retro` while this session is still in context. The run file is its primary source: fallbacks, blocked executors, fix rounds, and deferred findings are where the environment cost the run.

---

## Writing a brief

An executor has no access to this conversation, the spec, or the user's answers. Every brief is self-contained. Include:

- **The goal**, in your own words.
- **The seams**, verbatim from the plan.
- **Exact commands** and the package manager.
- **Paths**: the run file, the spec, the repo root, the files in scope.
- **The boundary**: what is out of scope, and the instruction to stop and report rather than expand.
- **What to return**, concretely.

Quote what lives only in this conversation (decisions, the user's answers): "as discussed" and "the usual pattern" do not resolve inside an executor. Point at what lives in a file (the spec, `recon.md`, the plan in the run file, commits) by path instead of pasting it; the executor reads it itself.
