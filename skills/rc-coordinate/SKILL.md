---
name: rc-coordinate
description: "Coordinate several tickets built in parallel, with every user decision batched in one window. Use when the user wants several tickets, a slice, or a feature's open tickets built in parallel."
argument-hint: "feature folder, slice, or ticket paths"
---

# Coordinated tickets

Several tickets built at once, each by its own `rc-orchestrate` worker in its own worktree, landed one at a time, with the user's decisions brought to one window.

**You are the coordinator.** You choose what runs, route the user's decisions, hold the slots, and land the commits. Workers plan, write code, and review it. If you find yourself editing a source file or answering a plan question yourself, you have taken a worker's job or the user's.

**The bottleneck is the user's attention, not the agents.** Tickets waited hours at the gates while the agents worked minutes. Your main job is to **batch and route the user's touches**. Parallelism comes second.

Your jobs, in priority order:

1. **Keep the digest.** Every item waiting on the user, in one list, riskiest first (see *The digest*).
2. **Keep writes apart.** Two workers never write the same file at once, and each shared file has one writer.
3. **Land in order.** One merge at a time, through the merge queue.
4. **Account for every worker.** Each one ends `landed`, `replaced`, `absorbed` or `dropped`. A worker that went silent is `not run`, never clean.

## The protocol

Workers follow `~/.claude/skills/rc-coordinate/protocol.md`. Read it before you launch anyone: it defines the message events, the slots and the bans, and both of you hold to it. Message a worker only to answer, grant, or tell: a message wakes an idle worker.

## 0 — Set up

**Pick the tickets.** From the argument, list the tickets: every `open` ticket in the feature or slice, or the paths given (ticket format and status words: `~/.claude/skills/rc-feature-page/feature-layout.md`). Read each one in full, with its `Blocked by:` line. Experiment tickets run like the others: `rc-orchestrate` routes them to `rc-experiment` itself.

**Estimate touch-lists.** For each ticket, write down the files it will likely write, per repo, from the ticket and a quick look at the code. These are estimates; the workers' plans replace them.

**Plan the waves.** A ticket is *ready* when every ticket it is blocked by has landed. A **wave** is the ready tickets whose estimated touch-lists do not overlap. Launch every ticket in the wave; there is no cap. When two ready tickets overlap, run the one that unblocks more first, and queue the other.

**Ask the user once**, in one message: the waves; the target branch (default: the current branch of each repo); the push policy (default: no push); any shared resources the workers need as slots (a database, a dev server port, a browser sign-in), and the commands to ban beyond the protocol's.

**Open the run file** at `<feature>/runs/coordinate-<YYYY-MM-DD>.md` (no feature folder: next to the first ticket). You are its only writer. It holds the target branch and run BASE per repo, the push policy, the slots, and per ticket: path, worker name, session id, worktree, touch-list, state, and the ledger (*Finish*). It also holds the digest and the merge order.

**Open the feature page.** You are its only writer. When the feature has a page, record its URL; when it has none, create it now (`rc-orchestrate`'s *Full build* in Phase 0), so no worker races to create it.

Done when the user has confirmed the waves and the run file holds every field above.

## 1 — Launch

**Pilot first.** Launch the first ticket of the first wave alone, and wait for its `plan-ready` before launching the rest. A flaw in the launch then costs one worker, not all of them, and the BASE failures are recorded once.

**Launch a worker** with Bash, from the repo root:

```
claude --bg --name <slug> "/rc-orchestrate <ticket path>

A coordinator launched this run. Read ~/.claude/skills/rc-coordinate/protocol.md before Phase 0 and follow it: where it differs from rc-orchestrate, it wins. Coordinator address: <your session id or socket>. Slots: suite<, others>. Banned beyond the protocol: <commands, or none>. <Peers: see below.>"
```

Find your own address in `claude agents --json`. Record each worker's session id from the launch output in the run file. Address a worker by session id, not by name: names repeat across days.

**Name the peers.** When a worker's touch-list is next to another running ticket's (the same module, a shared doc), name that peer in its prompt with one action: "ticket NN also edits `<file>`; whichever lands second rebases." When you are unsure of something, say so in the prompt ("check how that branch relates to `<hash>` before you build on it"); a worker settles it in seconds, and a guess costs a rebase.

Done when every ticket in the wave has a worker whose session id is in the run file.

## 2 — Run

Messages and completion notices are your only wake-ups. On each wake: log the event with its time in the run file (the ledger is built from these lines), handle it, then show the digest if it changed.

**Before you report on a worker**, check its live state: the run file, `git log` in its worktree, and its row in `claude agents --json`. `state` is a hint, not the truth: it stays `blocked` after a dead session, and reads `done` while a worker waits on an answer. Before messaging a worker, check it is reachable in `ListAgents`. When it is not, resume it with `claude --bg --resume <session-id> "<your message>"`; it comes back on a new socket, so record that.

| Event | You do |
|---|---|
| `plan-ready` | Check its touch-list against every running worker's real touch-list. With no overlap and no open questions, reply `go` at once. With open questions, put them in the digest **word for word**, with the worker's recommended answers. With an overlap, reply `hold` and put the overlap in the digest with your recommendation (run one after the other, or name a peer). |
| `questions` | Into the digest, word for word. |
| `slot-request` | Grant it if the slot is free; otherwise queue the worker and grant it on release. Note in the digest any holder that is waiting on the user: no one holds a slot while the user is away. |
| `status` | Refresh the feature page (`rc-orchestrate`'s *Refresh the page*). Refreshes run one at a time; when statuses arrive during one, run one more after it lands. |
| `waiting` | Into the digest, with the command that reaches it: `claude attach <name>`. |
| `gate-b` | Into the digest (see *Gate B*). |
| `finished` | Into the merge queue (*Land*). |
| `blocked` | Retry by cause, at most twice: a smaller scope after a context limit, the same brief after a dropped connection, another model after a tool error. Then put it in the digest. Waiting on the user is not stuck. |

### The digest

One list of everything waiting on the user, kept in the run file and shown whenever it changes. One line per item, self-contained, riskiest first:

```
<ticket> · <gate or event> · <the question> → <your recommended answer> (risk: <what goes wrong if wrong>)
```

Show each item as soon as it is ready, batched with whatever else is ready then. Book human-only steps (sign-ins, UI checks) back to back, after checking that the credentials exist.

**Relay answers word for word.** When the user answers, send each worker its answers in a `go` or `answers` message, quoted as the user typed them, without summary. When an answer needs real back-and-forth, tell the user to answer in that worker's window (`claude attach <name>`).

### Gate B

The worker stops with its ticket uncommitted in its worktree and sends its report. Show the user the report as sent, the command to open the worktree (`code -a <worktree>`), and the commit message per repo. A skipped test or a new BASE-failure entry goes at the top of the item: it loosens a gate, so the user countersigns it.

- **A change request** (any reply other than approval): send it as `change-request`, word for word. The worker sends `gate-b` again.
- **Approval**, typed by the user in this window: commit in the worker's worktree, per repo, with its commit message, then send `committed` with the hashes. You say "approved" only after the user typed it here.

## 3 — Land

The merge queue lands one ticket at a time per target branch, in the order tickets send `finished`. When a later ticket is blocked by an earlier one, the earlier one goes first. For the head of the queue, per repo, in the worker's worktree:

1. `git fetch`, then rebase the ticket's branch onto the target's current tip.
2. Compare `git patch-id` before and after the rebase. When it changed, the user approved a different diff: back to Gate B, with the rebase's effect on the item.
3. Run the full gate, holding the `suite` slot. Compare failures against the worker's BASE failures; a new one goes to the digest.
4. Fast-forward the target onto the branch. Push only as the push policy allows, and only when origin has not moved: never force.
5. Record the hashes and range in the run file. Tell every running worker whose touch-list overlaps the landed one: `landed <target> <tip>`.

A ticket is landed when the target's tip contains its branch and the hashes are in the run file.

Then put the user's wrap-up for that ticket in the digest: retro or not. Relay the answer as `retro` or `no-retro`. Once the worker ends, remove its worktree and delete its branch (`git branch -D` only after `git merge-base --is-ancestor <branch> <target>` passes).

A landing makes new tickets ready: plan the next wave as in step 0, and launch it with no pilot. Before you launch a wave, run the wave review below for the wave that just landed.

### Wave review

Each ticket was reviewed on its own. Once a wave has landed, invoke `/code-review` with the fixed point the wave's start (the run BASE for the first wave), its reviewers spawned as `rc-reviewer`, and add to the brief: **per-ticket review is done; report only issues that span tickets**: duplicated helpers, inconsistent naming, contracts that drifted between tickets, and evals or tests made stale by another ticket's change. Then compare each slice spec the wave touched against the code.

Triage the findings as `rc-orchestrate`'s step 2 does. Send the fix-now set to `rc-fixer` in a worktree off the target branch, verify as its step 3 does, and run the full gate. Show the fixes in the digest as a Gate B item: the title line, the review line, one line per fix, and `Commit?`. On approval, commit and land it through the merge queue.

## Finish

Done when every ticket is `landed`, `replaced`, `absorbed` or `dropped`, each wave has had its review, and no worker is still running (`claude agents --json`, checked live).

Write the **ledger** into the run file: per ticket, its active time, its time waiting on the user, its time waiting on a slot, and its cost where the worker's report gives it. Then report: per repo, the target branch and the range landed; per ticket, its outcome and hashes; the feature page URL; deferred findings from the wave reviews; anything not run.

Then offer `rc-retro` on the coordination itself, with the run file as its source.
