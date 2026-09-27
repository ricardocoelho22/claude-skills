---
name: implement-fleet-codex
description: "Implement a spec or set of tickets as an orchestrator, with codex agents as the executors and Claude agents as the fallback. Successor to implement-fleet."
disable-model-invocation: true
argument-hint: "path to the spec or ticket(s)"
---

# Orchestrated implementation, codex-first

Same destination as `/implement-fleet` (working, reviewed, committed code), with codex doing the execution and Claude doing the review. Code written by one model family and reviewed by another is the point: each catches the other's blind spots.

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
| Test trimmer | `impl-trimmer` | `gpt-6-sol` · medium | `impl-trimmer` |
| Fixer | `impl-fixer` | `gpt-6-sol` · high | `impl-fixer` |
| Manual checklist | — (ad hoc) | `gpt-6-luna` · low | general-purpose, `model: haiku` |
| Reviewer | `impl-reviewer` | — (always Claude) | `impl-reviewer` (opus · medium) |

Role files live in `~/.claude/agents/`. Both backends read the same file, so a role has one definition.

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
  -o <run-dir>/<ticket>-<slice>-<role>.md \
  "Your role is defined in ~/.claude/agents/<role>.md: read it and follow it, ignoring its frontmatter. <brief>"
```

Sandbox is `workspace-write` unless the cast says `read-only`. Launch it with Bash `run_in_background: true`. Mechanics (flags, exit codes, background runs, delivery) are in the `codex` skill.

**Claude call.** The Agent tool with `subagent_type: <role>` and the same brief. Sub-agents already run in the background.

**Fallback.** A codex call has failed when the wrapper exits non-zero. Re-run that one step on the Claude agent and note it in the run file. After two codex failures in one run, switch the rest of the run to `claude`.

**Session hygiene.** Start a fresh codex session per role per slice. Re-briefing the same executor on the same slice resumes instead, keeping its context and cache warm:

```
cd <repo> && ~/.claude/skills/codex/scripts/codex-run.sh resume --last -o <run-dir>/<ticket>-<slice>-<role>-2.md "<follow-up brief>"
```

**New files.** After every executor return, run `git add -N` on the files it created, so every `git diff` below shows them.

---

## Phase 0 — Recon and plan

Read the spec or tickets yourself, in full. This reading is your ground: the source of truth you judge every return against.

**Pin the ground.** For each git repo the work touches:

```
git -C <repo> rev-parse --abbrev-ref HEAD    # branch
git -C <repo> rev-parse HEAD                 # BASE — record it
git -C <repo> status --porcelain             # must be clean, or ask the user
```

A workspace can span several independent repos, so check for them and pin a separate BASE per repo.

**Open the run file.** Create `.scratch/implement-fleet/<slug>.md` (the run dir is `.scratch/implement-fleet/<slug>/`). It holds: spec path, backend, each repo's BASE and branch, BASE failures, the plan, and a per-slice landing log. You are the only writer. Confirm `.scratch/` is gitignored first; if not, use the session scratchpad directory and put its path in every brief.

**Run the backend check.**

**Explore.** Brief the explorer with the spec path, the repo roots, and the feature in your own words. Spot-check its report: open every file it names as in scope and every reuse candidate. Its report is a claim.

**Record BASE failures.** Run the full test suite once per repo. Write every failing test into the run file. A later failure on this list is pre-existing; a failure off it belongs to this run.

**Write the plan** into the run file yourself: mistakes here fan out into every later step.

- **Ticket order**, derived from blocking edges.
- **Per ticket:** the vertical slices in sequence; for each slice, the seams it tests (one line on why each earns a test) and its acceptance criteria.
- **Reuse**: helpers and fixtures executors must call instead of reimplementing.
- **Commands**: verified from config: single test file, full suite, typecheck, lint. Name the package manager.
- **Risks**: shared state, generated code, env vars, the BASE failures.

**Track status.** Keep each ticket's status current in its markdown file under `features/`: `in-progress` when its first slice starts, `done` when Gate B's commit lands, `needs-info` when escalated to the user mid-work.

Done when: the run file holds the backend, BASE per repo, BASE failures, and a plan with seams for every slice.

## Gate A — The plan 🚦 (optional)

Stop only when the plan has open questions the user must resolve: seam candidates you cannot choose between, spec ambiguities with real downstream cost, unknowns that force a re-do if wrong. Otherwise state the ticket order and proceed.

When you stop, invoke `/grilling` with two adaptations:

- **Root:** the open questions above, not the whole spec. Grill only what hangs off them; decisions the spec already settles are out of bounds.
- **Exit:** once the user confirms shared understanding, write each answer into the plan in the run file, then proceed.

## Phase 1 — Per ticket

Record `TICKET_BASE` (HEAD per repo) in the run file, then run steps 1–5.

### 1. Slices

Each slice runs two executors in sequence. Complete both before starting the next slice.

**1a — Tests.** Brief `impl-tdd` in test-writer mode: the slice's seams from the plan, the commands, the paths, and the boundary: **write failing tests only; return before writing production code.**

Verify: `git -C <repo> diff --stat`, `git -C <repo> diff`, then the single test file command. Every changed file is a test file. Every test is red for a behavioral reason, not an import error or missing fixture. A test green before any production code means the seam is wrong: take it to the user.

**1b — Implement.** Brief `impl-tdd` in implementer mode: the red test files, the commands, the paths, and the boundary: **make the red tests green; write no new tests and nothing speculative.**

Verify: the diff touches production files only, typecheck is clean, the single test file is green. A blocked implementer gets a tighter brief, resumed on the same session.

Append what landed to the run file.

### 2. Trim

Brief `impl-trimmer` with the ticket's test files (from `git diff --stat <TICKET_BASE>`), the plan's seams for the ticket, and the commands.

Verify: the diff since the trimmer started only removes or merges test code, the tests stay green, and every removal carries a reason in its return. Put the removals in the run file for Gate B.

### 3. Review

Invoke `/code-review` and follow its steps with two adaptations:

- **Diff:** use `git diff <TICKET_BASE>` (working tree against the ticket's base) and the fixed point `TICKET_BASE`. The ticket is uncommitted, so the skill's `...HEAD` form would show nothing.
- **Reviewers:** where it spawns the Standards and Spec sub-agents, spawn each as `subagent_type: impl-reviewer`, with the prompt the skill specifies.

Triage the findings against your own reading of the code: fix now, deferred (logged in the run file with a reason), or rejected.

### 4. Fix

Send the fix-now set to `impl-fixer` as one brief, quoting each finding with your triage decision. Verify with typecheck and the single test file command for every touched test file. Cap at **one fix round**; a second means a structural problem: take it to the user.

### 5. Manual checklist

Brief the checklist executor with the ticket content, its seams, and `git diff <TICKET_BASE>`. Ask for a markdown checklist of at most 10 items: only checks a human does by hand (visual states, UI flows, timing), each one line: what to do, what to see. Save it next to the ticket as `manual-test-<NN>-<slug>.md`.

Verify: the file exists and every item is a hand check.

## Gate B — Ready to commit 🚦 (required)

The user reads the code here to stay grounded and catch quirks. Hand them a report that makes that fast. Use exactly this shape, one line per item, around 20 lines:

```
## Ticket <NN> — <title>        ✅ tests · ✅ typecheck
Read first: <file> (<why>), then <file>
Changed: <n> files, +<a> −<d>

Key changes:
- <up to 3: behavior that changed, where>
Decisions:
- <up to 3: choice made — reason>

Review:     <n> fixed · <n> deferred (<reason>) · <n> rejected
Trimmed:    <test name> — <reason>   (one line each, or "none")
Deviations: <from the plan, or "none">
Manual checks: <path> (<n> items)

Commit?
```

A ❌ replaces a ✅ when a check fails, and the real failing output goes below the report. Everything else stays in the run file.

On approval, commit per repo on the current branch in the project's commit style. Start the next ticket at Phase 1. Re-open Gate A only when a ticket needs seams the plan does not cover.

## Phase 2 — Cross-ticket review (multi-ticket runs only)

Each ticket was reviewed on its own. Once all are committed, invoke `/code-review` with fixed point BASE, reviewers spawned as `impl-reviewer`, and add to the brief: **per-ticket review is done; report only issues that span tickets** (duplicated helpers, inconsistent naming, contracts that drifted between tickets). Triage and fix as in steps 3–4, then commit the fixes.

## Finish

Run the full test suite once per repo, yourself, plus lint and build if the project defines a combined gate. Compare failures against the BASE failures. Report: tickets landed, commits per repo, checklist paths, deferred findings, codex fallbacks taken, anything left unverified.

---

## Writing a brief

An executor has no access to this conversation, the spec, or the user's answers. Every brief is self-contained. Include:

- **The goal**, in your own words.
- **The seams**, verbatim from the plan.
- **Exact commands** and the package manager.
- **Paths**: the run file, the spec, the repo root, the files in scope.
- **The boundary**: what is out of scope, and the instruction to stop and report rather than expand.
- **What to return**, concretely.

Quote decisions and the user's answers directly: "as discussed" and "the usual pattern" do not resolve inside an executor. Point at files and commits by path; the executor reads them itself.

## When not to use this

A one-file change, a bug fix you already understand, or any task where framing costs more than doing. Use `/implement` for those.
