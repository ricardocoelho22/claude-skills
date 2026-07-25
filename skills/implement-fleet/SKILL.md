---
name: implement-fleet
description: "Implement a spec or set of tickets as an orchestrator: you frame the work and hold the user gates, while pinned sub-agents explore, write code test-first, and review. Use for multi-ticket or multi-file work where one agent's context would overflow."
disable-model-invocation: true
argument-hint: "path to the spec or ticket(s)"
---

# Orchestrated implementation

Same destination as `/implement` — working, reviewed, committed code — but the work is split
across sub-agents so that no single context holds everything, and so each phase runs on a model
sized to it.

**You are the orchestrator. You do not write production code.** If you find yourself editing a
source file, you have taken an executor's job and lost the context budget that makes this skill
worth invoking. Your four jobs, in order of importance:

1. **Hold the gates.** Sub-agents cannot talk to the user. Every decision that needs a human
   belongs to you and only you.
2. **Write the briefs.** A sub-agent knows nothing about this conversation. Output quality is
   capped by brief quality — this is where your model tier actually pays for itself.
3. **Verify the returns.** Never accept a sub-agent's summary as fact. Re-run the checks
   yourself.
4. **Carry the thread.** You are the only participant who sees the whole run.

## The cast

| Role | `subagent_type` | Model | Why |
|---|---|---|---|
| Orchestrator | — (you) | your session model | Judgement, gates, cross-slice coherence |
| Recon | `impl-explorer` | sonnet | Broad reading, mechanical; volume over subtlety |
| Implementer | `impl-tdd` | sonnet | Bounded slice with confirmed seams and named commands |
| Reviewer | `impl-reviewer` | opus | Judgement-heavy; last gate before commit |

Models are pinned in the agent definitions under `~/.claude/agents/`. Do not pass a `model`
override unless the user asks for one — the definitions are the single source of truth, and
overriding them silently is how a run ends up on a model nobody chose.

Always spawn with `run_in_background: false`. Phases are sequential by data dependency, and
implementers touching the same files in parallel will collide.

---

## Phase 0 — Frame the work (you, alone)

Read the spec or tickets yourself, in full. This is the one thing you must not delegate: it is
the source of truth you will judge every sub-agent return against.

**Pin the ground.** For each git repo the work will touch:

```
git -C <repo> rev-parse --abbrev-ref HEAD    # branch
git -C <repo> rev-parse HEAD                 # BASE — record it
git -C <repo> status --porcelain             # must be clean, or ask the user
```

A working tree can span several independent repos with no umbrella repo above them (a monorepo
folder is not necessarily a git repo). Check rather than assume: pin a separate BASE per repo,
and later diff, review, and commit each repo separately.

**Order the work.** If you were given tickets, read their blocking edges and order them. State
the order you derived — if it is wrong, this is the cheapest moment to find out.

**Open the run file.** Sub-agents share no context with each other or with you; the filesystem
is the only channel between them. Create `.scratch/implement-fleet/<slug>.md` holding: the
spec path, each repo's BASE sha and branch, the ticket order, the confirmed seams (once Gate A
passes), the verified commands, and a running log of what each slice landed. **You are the only
writer.** Sub-agents may read it; they never edit it. Check it is gitignored before writing —
if `.scratch/` is not ignored, use the session scratchpad directory instead and put the path in
every brief.

## Phase 1 — Recon (`impl-explorer`, sonnet)

Spawn one explorer per genuinely separate area — per repo, or per unrelated subsystem. Two or
three at once is usually right; more than that and you are paying for overlap. These are
read-only and independent, so send them **in a single message** to run concurrently.

Give each a self-contained brief: the goal in your own words, the spec path, the repo and paths
to focus on, and what you specifically need answered. Never write "explore the codebase" — name
the question.

**Then verify, before anything is built on it.** Open two or three files the report cites and
confirm they say what it claims. Check the commands it reports against the actual
`package.json` / config. If a report is vague, hedged, or contradicts the spec, re-brief with
the specific gap named — do not paper over it yourself, and do not proceed on a map you have
not checked. Everything downstream inherits this.

## Gate A — Seams and slice order (you + user) 🚦

The TDD rule is absolute: **no test is written at an unconfirmed seam.** An `impl-tdd` agent
cannot ask, so the confirmation happens here or not at all.

Using the explorer's seam inventory and your reading of the spec, propose to the user:

- the **seams** to test, each with one line on why it earns a test;
- the **slice order** — the vertical tracer bullets, in sequence;
- anything you have deliberately decided *not* to test, and why.

Use `AskUserQuestion`. Do not proceed until the user answers. Write the confirmed seams into
the run file **verbatim** — that exact wording goes into every implementer brief.

## Phase 2 — Implement, slice by slice (`impl-tdd`, sonnet)

One agent per slice, strictly sequential. After each returns:

**Verify it yourself. Do not skip this.** The single most common failure of this pattern is an
orchestrator that reads "all tests pass" and believes it.

```
git -C <repo> diff --stat                # what actually changed
git -C <repo> diff                       # read it
<typecheck command>                      # from the run file, run by you
<single test file command>               # from the run file, run by you
```

Check, specifically:

- The diff matches what the agent said it did — and nothing more. Unannounced changes are the
  tell that something went sideways.
- Tests sit at confirmed seams only.
- Reuse the explorer found was actually used, not reimplemented.
- Nothing speculative crept in that the spec did not ask for.

If the agent reports it is blocked, or asks to test at a new seam, **that is correct behavior**
— it was told to stop rather than invent. Decide: re-brief with a tighter scope, or go back to
the user if the seam question is genuinely open. Do not fix it by hand.

Append what landed to the run file, then start the next slice.

## Phase 3 — Review (`impl-reviewer`, opus)

Once the ticket's slices are all in, review the accumulated diff. Spawn **two reviewers in one
message**, one per axis — separate contexts so neither axis masks the other:

- **Standards** — does this follow the repo's documented standards? Give it the standards files
  (`CLAUDE.md`, `CONTRIBUTING.md`, `CODING_STANDARDS.md`, and any project-local review command
  under `.claude/commands/`), and paste the Fowler smell baseline from
  `~/.claude/skills/code-review/SKILL.md` §3 **in full** — the sub-agent has no other access to
  it.
- **Spec** — does this faithfully implement the ticket? Give it the ticket contents (paste, or
  a path it can read) and ask for: requirements missing or partial, behavior nobody asked for,
  and requirements implemented wrongly.

Both get the pinned diff command: `git -C <repo> diff <BASE>...HEAD`.

**Triage the findings yourself** — this is judgement, and it is yours. Sort into: fix now, note
in the run file as follow-up, or reject as wrong. Reviewers can be confidently wrong; if a
finding does not survive your reading of the code, drop it and say so.

Send the "fix now" set to a fresh `impl-tdd` agent as one consolidated fix brief — quoting the
findings, with your triage decision on each. Re-verify as in Phase 2. Cap this at **two fix
rounds**; if a third is needed, stop and take it to the user, because something upstream is
wrong and more rounds will not find it.

## Gate B — Ready to commit (you + user) 🚦

Per ticket, report to the user: what landed, the verified test/typecheck results (actual output,
not your paraphrase), findings fixed, findings deferred, and anything you deviated on. Ask
whether to commit and continue.

On approval, commit **per repo** on the current branch, in the project's commit style (short
imperative Conventional Commits subject). Then return to Phase 2 for the next ticket — reusing
the same run file and confirmed seams. Re-open Gate A only if a new ticket needs seams the user
has not agreed.

## Finish

Run the **full test suite once**, per repo, yourself, plus lint and build if the project defines
a combined gate. Report the real result. Then summarize: tickets landed, commits per repo,
deferred findings from the run file, and anything left unverified.

---

## Writing a brief

The failure mode of this whole pattern is an underspecified brief — a sub-agent cannot see this
conversation, the spec, the explorer's report, or the user's answers. Every brief is
self-contained or it is broken. Include:

- **The goal**, in your own words. Not a pasted ticket title.
- **The confirmed seams**, verbatim from the run file.
- **Exact commands** for typecheck and single-file tests, and the package manager. Never let an
  executor guess these — a wrong guess wastes a whole slice.
- **Paths**: the run file, the spec, the repo root, the files in scope.
- **The boundary** — what is explicitly *not* in this slice, and the instruction to stop and
  report rather than expand.
- **What to return**, concretely.

Paste content rather than referencing "as discussed", "the above", or "the usual pattern". None
of those resolve inside a sub-agent.

## What never leaves you

Gates and user questions. Model selection. Commit decisions. Cross-slice architecture. Triage
of review findings. Whether a slice is actually done. Delegating any of these does not save
context — it removes the judgement that is the entire reason for the split.

## When not to use this

A one-file change, a bug fix you already understand, or anything where framing the work costs
more than doing it. Use `/implement` for those — orchestration overhead on small work is pure
loss.
