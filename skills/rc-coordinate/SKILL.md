---
name: rc-coordinate
description: "Coordinate several tickets built in parallel, with every user decision batched in one window. Use when the user wants several tickets, a slice, or a feature's open tickets built in parallel."
argument-hint: "feature folder, slice, or ticket paths"
---

# Coordinated tickets

Several tickets built at once, each by its own `rc-orchestrate` worker in its own worktree, landed one at a time, with the user's decisions brought to one window.

**You are the coordinator.** You choose what runs, route the user's decisions, hold the slots, own the shared git state, and land the commits. Workers plan, write code, review it, run the gates, and look after their own PRs. If you find yourself editing a source file, reading CI output, or answering a plan question yourself, you have taken a worker's job or the user's.

**The bottleneck is the user's attention, not the agents.** Tickets waited hours at the gates while the agents worked minutes. Your main job is to **batch and route the user's touches**. Parallelism comes second. Your own context is the second bottleneck: keep heavy work (logs, suites, reviews) in the workers, and keep the run's state in the run file, so a fresh session can rebuild from it.

Your jobs, in priority order:

1. **Keep the digest.** Every item waiting on the user, in one list, riskiest first, and the user told only what changed (see *Talking to the user*).
2. **Keep writes apart.** Two workers never write the same file at once, and each shared file has one writer.
3. **Land in order.** One landing at a time per target branch, through the merge queue.
4. **Account for every worker.** Each one ends `landed`, `replaced`, `absorbed` or `dropped`. A worker that went silent is `not run`, never clean.

## The protocol and the project file

Workers follow `~/.claude/skills/rc-coordinate/protocol.md`. Read it before you launch anyone: it defines the message events, the slots, the git rules and the bans, and both of you hold to it. Message a worker only to answer, grant, or tell: a message wakes an idle worker.

The **project file** is `docs/agents/coordinate.md` in the work repo (template: `~/.claude/skills/rc-coordinate/project-file.md`). It holds the project's answers: landing mode, merge rules, posting rules, preflight checks, worktree warm-up, slots, bans, and CI pointers. It is the source of truth for every rule below marked *(project file)*.

## 0 — Set up

**Read the project file.** When the repo has none, or it lacks a field this run needs, draft the missing fields from the template with your recommended answers, ask the user once, and write the file when they confirm. Every rule is settled here, before the pilot.

**Preflight.** Run every check the project file lists, plus these: `git` and `gh` reach the remote, and each command the landing mode needs (push, and in PR mode, PR create and the posts) runs without a permission prompt. Run them all, then put every failure to the user in one message, each with its fix. Done when every check passes.

**Pick the tickets.** From the argument, list the tickets: every `open` ticket in the feature or slice, or the paths given (ticket format and status words: `~/.claude/skills/rc-feature-page/feature-layout.md`). Read each one in full, with its `Blocked by:` line. Experiment tickets run like the others: `rc-orchestrate` routes them to `rc-experiment` itself.

**Estimate touch-lists.** For each ticket, write down the files it will likely write, per repo, from the ticket and a quick look at the code. These are estimates; the workers' plans replace them.

**Plan the waves.** A ticket is *ready* when every ticket it is blocked by has landed. A **wave** is the ready tickets whose estimated touch-lists do not overlap. Launch every ticket in the wave unless the project file sets a wave size. When two ready tickets overlap, run the one that unblocks more first, and queue the other.

**Ask the user once**, in one message: the waves, plus anything the project file leaves open (target branch, landing mode, push policy in branch mode).

**Open the run file** at `<feature>/runs/coordinate-<YYYY-MM-DD>.md` (no feature folder: next to the first ticket). You are its only writer. It holds the target branch and run BASE per repo, the landing mode, the slots, and per ticket: path, worker name, session id, worktree, branch, touch-list, state, PR URL, and the ledger (*Finish*). It also holds the digest, the merge order, and the event log.

**Open the feature page.** You are its only writer. When the feature has a page, record its URL; when it has none, create it now (`rc-orchestrate`'s *Full build* in Phase 0), so no worker races to create it.

Done when the user has confirmed the waves and the run file holds every field above.

## 1 — Launch

**Fetch once.** Per repo, one `git fetch` before the wave. You are the only one who fetches: parallel fetches from many worktrees corrupt the shared object store.

**Create each worktree yourself,** one at a time: the branch off the target's tip, then the project file's warm-up command, before the next. Record the path and branch.

**Name each worker** after its subject, in kebab-case (`pdf-page-cut`), and put the subject next to the name on every line the user sees.

**Pilot first.** Launch the first ticket of the first wave alone, and wait for its `plan-ready` before launching the rest. A flaw in the launch then costs one worker, not all of them, and the BASE failures are recorded once.

**Launch a worker** with Bash, from the repo root:

```
claude --bg --name <name> "/rc-orchestrate <ticket path>

A coordinator launched this run. Read ~/.claude/skills/rc-coordinate/protocol.md before Phase 0 and follow it: where it differs from rc-orchestrate, it wins. Coordinator address: <your session id or socket>. Worktree: <path>, branch <branch>, per repo. Landing mode: <branch | pr>. Project file: <path>. Slots: suite<, others>. Banned beyond the protocol: <commands, or none>. <Peers: see below.>"
```

Find your own address in `claude agents --json`. Record each worker's session id from the launch output in the run file. Address a worker by session id, not by name: names repeat across days.

**Name the peers.** When a worker's touch-list is next to another running ticket's (the same module, a shared doc), name that peer in its prompt with one action: "ticket NN also edits `<file>`; whichever lands second rebases." When you are unsure of something, say so in the prompt ("check how that branch relates to `<hash>` before you build on it"); a worker settles it in seconds, and a guess costs a rebase.

Done when every ticket in the wave has a worker whose session id is in the run file.

## 2 — Run

Messages, completion notices and your hourly timer are your only wake-ups. On each wake: log the event with its time in the run file (the ledger is built from these lines), handle it, then tell the user if *Talking to the user* says to.

**Liveness sweep.** On the hourly timer, and on any wake after a gap of 30 minutes or more, check every worker: its row in `claude agents --json` and whether it is reachable in `ListAgents`. `state` is a hint, not the truth: it stays `blocked` after a dead session, and reads `done` while a worker waits on an answer. Resume each dead worker with `claude --bg --resume <session-id> "<what it was doing, from the run file>"`, copying the session id from the run file; it comes back on a new socket, so record that. Tell the user once, with the list, not per worker. In PR mode, a dead worker is an unwatched PR, so the sweep comes before anything else.

| Event | You do |
|---|---|
| `plan-ready` | Check its touch-list against every running worker's real touch-list. With no overlap and no open questions, reply `go` at once. With open questions, put them in the digest **word for word**, with the worker's recommended answers. With an overlap, reply `hold` and put the overlap in the digest with your recommendation (run one after the other, or name a peer). |
| `questions` | Into the digest, word for word. |
| `slot-request` | Grant it if the slot is free; otherwise queue the worker and grant it on release. Note in the digest any holder that is waiting on the user: no one holds a slot while the user is away. |
| `status` | Refresh the feature page (`rc-orchestrate`'s *Refresh the page*). Refreshes run one at a time; when statuses arrive during one, run one more after it lands. |
| `waiting` | Into the digest, with the command that reaches it: `claude attach <name>`. |
| `gate-b` | Into the digest (see *Gate B*). |
| `finished` | Into the merge queue (*Land*). |
| `pushed` | Log it. In PR mode, post a re-review request when the posting rules call for one *(project file)*. |
| `rebase-request` | Into the merge queue, ahead of new tickets. |
| `mergeable` | Merge (*Land*, PR mode). |
| `base-red` | Mark the PR `waiting for base` in the run file and the digest. It is not the ticket's failure. |
| `base-fixed` | Into the merge queue as a rebase, so CI runs fresh on the fixed base. |
| `blocked` | Retry by cause, at most twice: a smaller scope after a context limit, the same brief after a dropped connection, another model after a tool error. Then put it in the digest. Waiting on the user is not stuck. |

### Talking to the user

Message the user only when a decision is needed or a result changes (a ticket landed, merged, dropped, or blocked). The digest lives in the run file; show it whole when the user asks. A worker event that changes nothing for the user goes only in the event log.

**Hourly summary.** Keep a background `sleep 3600` running as your timer. When it fires, run the liveness sweep, and if anything changed since the last summary, send one short block: landed or merged, waiting on the user, waiting on CI or review, waiting for base. Then start the timer again.

### The digest

One line per item waiting on the user, self-contained, riskiest first:

```
<name> (<subject>) · <gate or event> · <the question> → <your recommended answer> (risk: <what goes wrong if wrong>)
```

Show each new item as soon as it is ready, batched with whatever else is ready then. Book human-only steps (sign-ins, UI checks) back to back, after checking that the credentials exist.

**Relay answers word for word.** When the user answers, send each worker its answers in a `go` or `answers` message, quoted as the user typed them, without summary. When an answer needs real back-and-forth, tell the user to answer in that worker's window (`claude attach <name>`).

### Gate B

The worker stops with its change uncommitted in its worktree and sends its report. Show the user the report as sent, the command to open the worktree (`code -a <worktree>`), and the commit message per repo. A skipped test or a new BASE-failure entry goes at the top of the item: it loosens a gate, so the user countersigns it. A PR fix round arrives the same way, as a short Gate B.

- **A change request** (any reply other than approval): send it as `change-request`, word for word. The worker sends `gate-b` again.
- **Approval**, typed by the user in this window: commit in the worker's worktree, per repo, with its commit message, then send `committed` with the hashes. You say "approved" only after the user typed it here.

### Guardrails

- Test a hook with the hook runner (`pre-commit run`, or the project's equivalent).
- Every use of a slotted resource takes its slot, however short.
- Before trusting a watcher's events, check its status parsing against one known state.
- Resume only a session id copied from the run file.

## 3 — Land

The merge queue lands one ticket at a time per target branch, in the order tickets send `finished`. When a later ticket is blocked by an earlier one, the earlier one goes first. A `rebase-request` or `base-fixed` jumps ahead of new tickets. For the head of the queue, per repo, in the worker's worktree:

1. `git fetch`, then rebase the ticket's branch onto the target's current tip.
2. Compare `git patch-id` before and after the rebase. When it changed, the user approved a different diff: back to Gate B, with the rebase's effect on the item.
3. When the rebase moved the branch, send `rebased <tip>`: the worker reruns Finish's gate under the `suite` slot and sends `finished` again. A new failure off its BASE list comes to the digest from the worker.
4. Land it by the landing mode.

Rebase only a held worker's branch: send `hold` first and wait for `held`.

### Branch mode

Fast-forward the target onto the branch. Push only as the push policy allows, and only when origin has not moved: never force. Record the hashes and range in the run file. Tell every running worker whose touch-list overlaps the landed one: `landed <target> <tip>`. The ticket is landed when the target's tip contains its branch and the hashes are in the run file.

### PR mode

**Open.** Push the branch (`--force-with-lease` after a rebase, never a plain force), open the PR with its body built from the Gate B report, and post it as the posting rules say *(project file)*. Record the URL and send the worker `pr-open <url>`: from here it watches its own PR (protocol, *PR follow-up*).

**Merge.** On `mergeable`, check the merge rules *(project file)* yourself against the PR's live state. When they are met, merge by the rule's method, record the hashes, tell overlapping workers `landed <target> <tip>`, and send the worker `merged`. Tell the user in one line. When a rule does not settle it, put it in the digest. The ticket is landed when the PR is merged and its hashes are in the run file.

### After landing

Put the retro question in the digest, and relay the answer as `retro` or `no-retro`. Once the worker ends, remove its worktree and delete its branch (`git branch -D` only after `git merge-base --is-ancestor <branch> <target>` passes; for a squash merge, after the PR shows merged).

A landing makes new tickets ready: plan the next wave as in step 0, and launch it with no pilot. Before you launch a wave, run the wave review below for the wave that just landed.

### Wave review

Each ticket was reviewed on its own. Once a wave has landed, invoke `/code-review` with the fixed point the wave's start (the run BASE for the first wave), its reviewers spawned as `rc-reviewer`, and add to the brief: **per-ticket review is done; report only issues that span tickets**: duplicated helpers, inconsistent naming, contracts that drifted between tickets, and evals or tests made stale by another ticket's change. Then compare each slice spec the wave touched against the code.

Triage the findings as `rc-orchestrate`'s step 2 does. Send the fix-now set to `rc-fixer` in a worktree off the target branch, verify as its step 3 does, and run the full gate. Show the fixes in the digest as a Gate B item: the title line, the review line, one line per fix, and `Commit?`. On approval, commit and land it through the merge queue.

## Finish

Done when every ticket is `landed`, `replaced`, `absorbed` or `dropped`, each wave has had its review, and no worker is still running (`claude agents --json`, checked live).

Write the **ledger** into the run file: per ticket, its active time, its time waiting on the user, its time waiting on a slot, its time in PR review or waiting for base, and its cost where the worker's report gives it. Then report: per repo, the target branch and the range landed; per ticket, its outcome, hashes and PR; the feature page URL; deferred findings from the wave reviews; anything not run.

Then offer `rc-retro` on the coordination itself, with the run file as its source.
