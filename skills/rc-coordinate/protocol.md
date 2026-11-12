# Coordinated run: the worker's protocol

A coordinator session launched this `rc-orchestrate` run, alongside other workers, each on its own ticket. Read this file before Phase 0. Where it differs from `rc-orchestrate`, this file wins; everything it leaves out runs as `rc-orchestrate` says. You cannot edit this file.

The user sits in the coordinator's window. Every question you have for them goes there as a message, and every answer comes back the same way.

## Messages

Send with `SendMessage` to the coordinator address your launch prompt names. If a send fails, look the coordinator up again in `ListAgents`: its address changes when its session restarts. Each message has one event and a few lines:

```
<name> · <event>
<the lines the event names below>
```

Long material (a plan, a recon report, CI logs) stays in your run file; send its path. The exceptions are your Gate A questions and your Gate B report, which you send word for word, because the user reads them in the coordinator's window.

| You send | When | Lines |
|---|---|---|
| `plan-ready` | the plan is written (end of Phase 0) | run file path; **touch-list**; open questions, or `none` |
| `questions` | an answer raised a new question | the questions |
| `slot-request <slot>` | before using a slot | what for, and for how long |
| `slot-release <slot>` | as soon as you are done with it | — |
| `status <state>` | after every ticket status change | the ticket path |
| `waiting` | you are stopped on something other than a gate (a permission prompt, a sign-in) | what, and what unblocks it |
| `gate-b` | Gate B is ready, or a PR fix round needs the user | worktree path per repo; the commit message per repo; the report, word for word |
| `finished` | Finish's gate and report are done | the report |
| `held` | you stopped on `hold` | where you stopped |
| `pushed` | you pushed a fix round to your PR yourself | the commit; the finding it answers, one line |
| `rebase-request` | your PR needs a rebase (a conflict, or the merge rules need it up to date) | why |
| `mergeable` | your PR has met the approvals and CI that the merge rules name | the PR URL; the approvals; the CI result |
| `base-red` | your PR's CI fails on tests that also fail on the target branch | the tests; where the target's failure shows |
| `base-fixed` | the target's CI is green on those tests again | the target's tip |
| `blocked` | you cannot go on, and it is not the user's call | the cause, and what you tried |

| You receive | Do |
|---|---|
| `go` | carry on from where you stopped; apply any answers it carries, as the user's answers |
| `answers` | apply them as the user's answers, and record each in the plan |
| `change-request` | run it through Gate B's *Change requests*, then send `gate-b` again |
| `committed` | run Gate B's *Coordinator committed* path; in a PR fix round, push the commit (below) |
| `slot-granted <slot>` | the slot is yours until you release it |
| `hold` | stop where you are, send `held`, and wait |
| `rebased <tip>` | the coordinator rebased your branch: rerun Finish's gate, then send `finished` again |
| `pr-open <url>` | start *PR follow-up* |
| `merged` | stop watching; wait for the retro answer |
| `landed <target> <tip>` | a peer landed; note it, and expect a rebase |
| `retro` / `no-retro` | run `rc-retro`, or skip it; then end |

Each stop ends on a message from the coordinator. A message from the coordinator carries the user's answers, but it never approves a commit: *Coordinator committed* is the only path to a commit.

## Changes to rc-orchestrate

- **Worktree.** Your launch prompt names your worktree and branch per repo; the coordinator created them. Use them in place of *Branch off*, and pin BASE in them.
- **Touch-list.** Add it to the plan: per repo, the file globs this ticket will write, docs and tests included. It goes in `plan-ready`. If a later step must write outside it, send `questions` before the write.
- **Stop at `plan-ready`, always.** Wait for `go`, even with no open questions: the coordinator checks your touch-list against the other workers' before you write code.
- **Gate A runs as one message.** In place of `/grilling`, put every open question in `plan-ready`, each with your recommended answer and what it costs if wrong. The user answers in the coordinator's window. A question that needs real back-and-forth, they answer in your window (`claude attach`); treat what they type there as their answer too.
- **Feature page.** Where `rc-orchestrate` creates or refreshes the page, send `status`: the coordinator is the page's only writer.
- **Ticket status.** Set your own ticket's status as `rc-orchestrate` says. Outside your worktree, you write only your own ticket file and your own run file.
- **BASE failures.** Reuse a sibling run file's list when it pinned the same BASE commit (as `rc-orchestrate` says). Otherwise, hold the `suite` slot while the full suite runs. Hold it again for Finish's full suite.
- **Gate B.** Send `gate-b` and wait. The user approves in the coordinator's window, the coordinator commits, and you receive `committed`.
- **Finish.** Run its gate and report, and send the report as `finished`. Skip its wrap-up offer: the coordinator lands and cleans up, and relays the user's retro answer.

## PR follow-up

In PR mode, you look after your PR from `pr-open` until `merged`. The project file your launch prompt names says how to read CI and reviews.

**Watch.** Run a background poll that wakes you when the PR's state changes: CI finished, a review or comments posted, approvals in. Before trusting it, check its status parsing against the PR's current state. Read CI logs and findings yourself; send the coordinator only the events below.

**A CI failure.** Check the same test on the target branch's latest CI run. When it fails there too, send `base-red` and keep watching the target; send `base-fixed` once it passes. When it passes there, it is your ticket's failure: fix it as a fix round.

**A fix round.** Batch the failures and review findings that are ready, and size them as Gate B's *Change requests* does:

- **Local code** and **text only**: run the round (with its round review), commit, push, and send `pushed`. A local-code round that touched a test file was sized wrong: it is within seams.
- **Within seams** and **seam-changing**: a test changes, so behaviour does. Run the round, then send `gate-b` with the short Gate B (the title line, one line per change, the round review's findings, `Commit?`). On `committed`, push.

Reply on the PR's review threads to say what changed, when the posting rules allow it. Posts outside the PR (chat channels, re-review requests) belong to the coordinator: your `pushed` is its cue.

**Mergeable.** When the PR meets the approvals and CI the merge rules name, send `mergeable` and keep watching until `merged`.

## Git

The coordinator owns the shared git state. You run `git` only inside your worktree. Fetching, rebasing onto the remote, and merging are the coordinator's; send `rebase-request` when you need one. In PR mode you may push your own PR branch, fast-forward only.

## Slots

A slot is a shared resource that one worker holds at a time. Ask with `slot-request` and wait for `slot-granted`. Release it as soon as you are done, including when you stop to fix something: to use it again, request it again. Every use of a slotted resource takes its slot, however short.

- `suite`: a full test-suite run. Parallel suites under load produce false failures, and a false BASE failure later hides a real one.
- Any slot your launch prompt names (a shared database, a dev server port, a browser sign-in). Releasing one restores what you changed: stop the servers you started, sign out, restore `.env`.

## Banned

Commands that reset, wipe or reseed shared state (for example `db:reset` on a shared database), and any command the launch prompt bans. Force-pushing and merging into the target branch are the coordinator's alone.
