---
name: orchestrate
description: "Implement one ticket as an orchestrator, with codex agents as the executors and Claude agents as the fallback."
disable-model-invocation: true
argument-hint: "path to the ticket"
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
| Explorer | `impl-explorer` | `gpt-6.1-sol` · medium · `read-only` | `impl-explorer` |
| Test-writer / Implementer | `impl-tdd` | `gpt-6.1-sol` · medium | `impl-tdd` |
| Fixer | `impl-fixer` | `gpt-6.1-sol` · high | `impl-fixer` |
| Manual checks | — (ad hoc) | `gpt-6-luna` · low | general-purpose, `model: haiku` |
| Test trimmer | `impl-trimmer` | `gpt-6.1-sol` · medium | `impl-trimmer` |
| Reviewer | `impl-reviewer` | — (always Claude) | `impl-reviewer` (opus · medium) |

Role files live in `~/.claude/agents/`. Both backends read the same file, so a role has one definition.

## Rungs

The cast sets each executor's default; the reviewer stays pinned to its cast entry. Three cases move an executor call up or down this ladder:

| Rung | Claude (`model` · `effort`) | Codex (`-m` · effort) |
|---|---|---|
| 1 | `haiku` · low | `gpt-6-luna` · low |
| 2 | `haiku` · medium | `gpt-6-luna` · medium |
| 3 | `sonnet` · medium | `gpt-6.1-sol` · medium |
| 4 | `sonnet` · high | `gpt-6.1-sol` · high |

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
  -o <run-dir>/<cycle>-<role>.md \
  "Your role is defined in ~/.claude/agents/<role>.md: read it and follow it, ignoring its frontmatter. <brief>"
```

Sandbox is `workspace-write` unless the cast says `read-only`. Launch it with Bash `run_in_background: true`. Mechanics (flags, exit codes, background runs, delivery) are in the `codex` skill.

**Claude call.** The Agent tool with `subagent_type: <role>` and the same brief. Sub-agents already run in the background.

**Checkpoint.** Before every executor call, snapshot each repo's working tree without touching it (`<run-dir>` as an absolute path), and record the tree hash with the call in the run file. The snapshot holds tracked files plus the untracked files earlier executors created (already intent-to-add, see *New files*); other untracked files stay out of it:

```
cp "$(git -C <repo> rev-parse --path-format=absolute --git-path index)" <run-dir>/snap.idx
GIT_INDEX_FILE=<run-dir>/snap.idx git -C <repo> add -u && GIT_INDEX_FILE=<run-dir>/snap.idx git -C <repo> write-tree
```

`git -C <repo> diff <tree>` is then that call's delta, and `git -C <repo> restore --source=<tree> --worktree -- <file>` puts one file back as it was before the call (delete a file the call created).

**Fallback.** A codex call has failed when the wrapper exits non-zero. Check its delta against the checkpoint and restore what it touched, then re-run that one step on the Claude agent at the same rung and note it in the run file. After two codex failures in one run, switch the rest of the run to `claude`.

**Session hygiene.** Start a fresh codex session per role per cycle. Re-briefing the same executor on the same cycle at the same rung resumes instead, keeping its context and cache warm; a step-up is always a fresh call:

```
cd <repo> && ~/.claude/skills/codex/scripts/codex-run.sh resume --last -o <run-dir>/<cycle>-<role>-2.md "<follow-up brief>"
```

**New files.** After every executor return, run `git add -N` on the files it created, so every `git diff` below shows them.

---

## Phase 0 — Recon and plan

Read the ticket and the spec it belongs to yourself, in full, fetching ticket references through the repo's issue tracker (`docs/agents/issue-tracker.md`). This reading is your ground: the source of truth you judge every return against.

**Route experiments.** An **experiment ticket** is one whose deliverable is a finding, not code: it asks for a measurement (cost, quality, latency) or a spike, and is done when a number or verdict exists. A wayfinder `prototype` or `research` ticket that needs a harness and a measured run is one. When the ticket is an experiment, hand the run to `~/.claude/skills/experiment/SKILL.md` now and follow it instead of this skill.

**Pin the ground.** For each git repo the work touches:

```
git -C <repo> rev-parse --abbrev-ref HEAD    # parent branch — record it
git -C <repo> rev-parse HEAD                 # BASE — record it
git -C <repo> status --porcelain             # must be clean, or ask the user
```

A workspace can span several independent repos, so check for them and pin a separate BASE per repo.

**Branch off.** `<slug>` is the ticket's name in kebab-case; the run file uses it too. In each repo, create the run's branch from BASE:

```
git -C <repo> switch -c <slug>                                # default
git -C <repo> worktree add -b <slug> ../<repo-name>-<slug>    # when the user asks for a worktree
```

Stay on the current branch only when the user says so. When `<slug>` already exists, ask the user. After a worktree add, every `<repo>` below means the worktree, and so does the feature folder when it sits inside the repo; only the wrap-up in *Finish* goes back to the original checkout.

**Find the feature.** The feature folder is the folder in the features root that holds the ticket (tree and features root: `~/.claude/skills/feature-artifact/feature-layout.md`). Work that sits outside a features root has no feature folder: the run then has no feature page, and every *refresh the page* below is skipped.

**Open the run file.** Create `<feature>/runs/<slug>.md` (the run dir is `<feature>/runs/<slug>/`). It holds: ticket path, spec path, feature folder, backend, each repo's BASE, parent branch, run branch, and worktree path if any, BASE failures, the plan, and a per-cycle landing log. You are the only writer. Without a feature folder, use `.scratch/orchestrate/<slug>.md` in the repo: confirm `.scratch/` is gitignored first; if not, use the session scratchpad directory and put its path in every brief.

**Run the backend check.**

**Explore.** Brief the explorer with the ticket and spec paths, the repo roots, and the ticket in your own words. Save its report as `<run-dir>/recon.md` (a codex explorer's `-o` file already is). Spot-check it: open every file it names as in scope and every reuse candidate. Its report is a claim.

**Record BASE failures.** Run the full test suite once per repo. Write every failing test into the run file. A later failure on this list is pre-existing; a failure off it belongs to this run.

**Write the plan** into the run file yourself: mistakes here fan out into every later step.

- **Cycles**: the ticket's test-first cycles in sequence; for each cycle, the seams it tests (one line on why each earns a test), its acceptance criteria, and a `mechanical` or `design-heavy` mark when it sits off the norm (see *Rungs*).
- **Reuse**: helpers and fixtures executors must call instead of reimplementing.
- **Commands**: verified from config: single test file, full suite, typecheck, lint. Name the package manager.
- **Risks**: shared state, generated code, env vars, the BASE failures.

**Open the feature page.** Refresh the page (below); when the feature has no page yet, the refresh creates it. Record the page URL in the run file.

**Refresh the page** means a delegated build (`~/.claude/skills/feature-artifact/SKILL.md`, *Delegated build*), then the publish yourself:

- **Build.** Spawn a general-purpose sub-agent in the background: `model: haiku` for a refresh, `model: sonnet` for a create, since it drafts `overview.md` that nobody reviews. Brief it to read that skill and run a delegated build for the feature folder, with the review waived, in the build folder `<session scratchpad>/feature-artifact/<feature>/` (an absolute path: the publish takes files only from the scratchpad or the working directory). It returns the build folder, every file in it, and the waiting lines; the publish's `files` comes from that list.
- **Publish.** When it returns, run *Build and publish* steps 4 and 5 with the Artifact tool. On a refresh, your first publish of the run needs a `read` of the page URL first. On a create, pass `icon: "map"` and write the new URL on the `Artifact:` line of `overview.md`.
- **One at a time.** The page is a view of the feature's files, so a refresh starts after the file change it must show. When a status changes while a refresh runs, start one more refresh after it lands; it reads the latest files, so it covers every change since.

**Track status** the way the repo's issue tracker records it: `in-progress` when Phase 1 starts, resolved the way the tracker closes work when Gate B's commit lands, `needs-info` when escalated to the user mid-work. After every status change, refresh the page.

**Keep `overview.md` true.** When the run changes a `spec.md` or adds a slice, update that slice's entry in the feature's `overview.md` in the layout's format, and set its `Summary checked` to today, before the next refresh. A refresh reports drift; it never repairs it.

Done when: the run file holds the backend, BASE and the run's branch per repo, BASE failures, and a plan with seams for every cycle, and the feature page URL when the run has a feature folder.

## Gate A — The plan 🚦 (optional)

Stop only when the plan has open questions the user must resolve: seam candidates you cannot choose between, spec ambiguities with real downstream cost, unknowns that force a re-do if wrong. Otherwise state the cycles and proceed.

When you stop, invoke `/grilling` with two adaptations:

- **Root:** the open questions above, not the whole spec. Grill only what hangs off them; decisions the spec already settles are out of bounds.
- **Exit:** once the user confirms shared understanding, write each answer into the plan in the run file, then proceed.

## Phase 1 — Build

Set the ticket `in-progress`, refresh the page, then run steps 1–5.

### 1. Cycles

Each cycle runs two executors in sequence. Complete both before starting the next cycle.

**1a — Tests.** Brief `impl-tdd` in test-writer mode: the cycle's seams from the plan, the commands, the paths, and the boundary: **write failing tests only; return before writing production code.**

Verify: the call's delta (`git -C <repo> diff --stat <tree>`, then `git -C <repo> diff <tree>`), then the single test file command. Every changed file is a test file. Every test is red for a behavioral reason, not an import error or missing fixture. Typecheck errors are expected only where a test calls API the cycle has not built yet. A test green before any production code means the seam is wrong: take it to the user.

**1b — Implement.** Brief `impl-tdd` in implementer mode: the red test files, the commands, the paths, and the boundary: **make the red tests green; write no new tests and nothing speculative.**

Verify: the call's delta (against its checkpoint) touches production files only, typecheck is clean, the single test file is green. A blocked implementer gets a tighter brief, resumed on the same session.

Append what landed to the run file.

### 2. Review

Invoke `/code-review` and follow its steps with two adaptations:

- **Diff:** use `git diff <BASE>` (working tree against BASE) and the fixed point BASE. The ticket is uncommitted, so the skill's `...HEAD` form would show nothing.
- **Reviewers:** where it spawns the Standards and Spec sub-agents, spawn each as `subagent_type: impl-reviewer`, with the prompt the skill specifies.

Triage the findings against your own reading of the code: fix now, deferred (logged in the run file with a reason), or rejected. A finding that a test is redundant, mock-only, off-seam, or tautological goes to the trim in step 5, not the fixer.

### 3. Fix

Send the fix-now set to `impl-fixer` as one brief, quoting each finding with your triage decision and listing every test file in `git diff --stat <BASE>`. Verify with typecheck and the single test file command for every one of those test files, not only the ones the fixer touched. Cap at **one fix round**; a second means a structural problem: take it to the user.

### 4. Manual checks

Brief the manual-checks executor to read `~/.claude/skills/manual-checklist/SKILL.md` and follow it, with the ticket path, BASE as the base, and the output path `manual-test-<NN>-<slug>.md` next to the ticket.

Verify: the file exists and every item is a plain-bullet hand check.

The file is a **guide** for the user, reference like the diff-tour. Assume its checks done: the ticket's status, Gate B's approval, and every report treat the ticket as verified by the tests and typecheck alone.

### 5. Trim

Trim runs last, once the ticket's tests are final, so no fixer time goes into tests that are about to be cut. Brief `impl-trimmer` with the ticket's test files (from `git diff --stat <BASE>`), the plan's seams for the ticket, the commands, and the test findings routed here in step 2.

Verify: the diff since the trimmer started only removes or merges test code, the tests stay green, and every removal carries a reason in its return. Put the removals in the run file for Gate B.

## Gate B — Ready to commit 🚦 (required)

The user reads the code here to stay grounded and catch quirks. Hand them a report that makes that fast: the `/diff-tour` of the ticket against BASE, with the test and typecheck status on its title line and the run's lines appended, around 25 lines in all:

```
## Ticket <NN> — <title>        ✅ tests · ✅ typecheck
<the diff-tour body: Read first … Watch for>

Review:     <n> fixed · <n> deferred (<reason>) · <n> rejected
Trimmed:    <test name> — <reason>   (one line each, or "none")
Deviations: <from the plan, or "none">
Guide:      <path> (manual checks, for reference)

Commit?
```

A ❌ replaces a ✅ when a check fails, and the real failing output goes below the report. Everything else stays in the run file.

**Change requests.** When the user asks for changes instead of approving, size each one by the first size that fits, in this order, and brief `impl-fixer` at its rung with the ticket's test files listed as in step 3. Each brief is its own round.

1. **Seam-changing**: a new seam or a changed contract. Add it to the plan as a new cycle and run steps 1–5 for it, then return here. Take it to the user first when it conflicts with a decision recorded in the plan.
2. **Within seams**: a test is added or edited, but only at seams the plan already names: rung 3.
3. **Local code** (a refactor, a symbol rename): the ticket's existing tests still describe the result, so no test is added or edited: rung 2.
4. **Text only** (docs, comments, a diagram): rung 1.

Batch same-rung requests into one brief. Verify as in step 3; a local-code return that touched a test file was sized wrong, so restore that test file from the checkpoint and re-run the request as within-seams. A request rejected at rung 4 is too big for a Gate B change: take it to the user as a new cycle or ticket. When behavior changed, update the manual-checks guide. Then re-show Gate B: after a within-seams change, the full report with a fresh `/diff-tour`; otherwise, the title line, one line per change, and `Commit?`.

On approval, commit per repo on the run's branch in the project's commit style, resolve the ticket, and refresh the page.

## Finish

Run the full test suite once per repo, yourself, plus lint and build if the project defines a combined gate. Compare failures against the BASE failures; a new failure goes to the user before you report. Refresh the page. Report: the branch (and worktree path) and commits per repo, the feature page URL, guide paths, deferred findings, codex fallbacks taken, step-ups (role, cycle, from and to rung), any test, typecheck, lint, or build you could not run.

Then offer to wrap up: **Merge into `<parent>`, retro, and clean up?** The user may take all three or name a subset; run what they take, in this order. Merge and cleanup run from each repo's original checkout, `<origin>` below (the repo itself when the run made no worktree).

1. **Merge.** Per repo: `git -C <origin> switch <parent>`, then `git -C <origin> merge <slug>`. On a conflict, invoke `/resolving-merge-conflicts`. When the merge was not a fast-forward, run the full test suite again and compare against the BASE failures; a new failure goes to the user. The merge stays local: pushing is the user's call.
2. **Retro.** Invoke `/retro` while this session is still in context. The run file is its primary source: fallbacks, blocked executors, fix rounds, and deferred findings are where the environment cost the run. It runs before cleanup because a worktree removal can take the run file with it.
3. **Clean up.** Per repo: `git -C <origin> worktree remove <worktree-path>` when the run made one, then `git -C <origin> branch -d <slug>`. When either refuses (untracked files, unmerged commits), show the user why and leave the rest to them.

Done when every step the user took has run, or has been handed back to them with the reason it stopped.

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
