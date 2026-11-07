# Multi-agent orchestration: practices for the multi-ticket skill

Gathered on 2026-11-03 from three sources:
- our own hand-run multi-session orchestration: run A, 10-31 to 11-02, tickets 28, 29, 25 and 15; run B, 11-03, tickets 26, 33 and 24;
- pstack and Google's EGM;
- external sources: Claude Code docs, Anthropic, Cognition, Cursor, Google Research, MAST.

The evidence sits in [`research/2026-11-03-multi-agent/`](research/2026-11-03-multi-agent/). Each practice below names where it comes from. Design constraints already recorded are in [`multi-ticket-skill-notes.md`](multi-ticket-skill-notes.md).

## TL;DR

- **The bottleneck is your attention, not the agents and not shared resources.**
  - In run A, tickets took 22–40 hours from launch to merge, but the agents worked only 0.5–2.5 hours of that.
  - Waits for a shared resource (a slot) lasted minutes.
  - The rest was waits at Gate A, Gate B and sign-ins. Even with you at the keyboard in run B, switching between three windows added about 20 minutes to one ticket.

  So the skill's main job is to **batch and route your touches**, not to maximise parallelism.
- **Parallel work held up well when each ticket's writes were its own.** Four tickets ran in parallel with zero merge conflicts. The literature agrees: parallelism helps when writes stay single-threaded per unit, and hurts on sequential work.
- **Approvals cannot travel between sessions.** This is documented behaviour, not a bug: a message from another session "can't approve anything". Every approval happens in the worker's own window, so the skill has to bring you to the right window at the right time.
- **Rules agreed in conversation got lost.** Run B restated none of run A's protocol: no slots, no merge order, no single page writer. The protocol has to live in a file the skill hands every worker.

## Practices

### Dispatch and topology

1. **The coordinator plans and lands; it never writes code. Each worker owns one ticket, its worktree, and its branch.**
   - Sources: pstack `orchestrate.md:9` ("one owner per PR… you never author or edit code"); Cursor's planners and workers.
   - A dedicated integrator *agent* became a bottleneck at Cursor. Landing stays mechanical: a slot plus fixed steps.
2. **Run tickets in parallel only when their write sets are disjoint.** Each ticket's plan lists a **touch-list** (file globs per repo, docs included). The coordinator checks the touch-lists for overlap before launch, and again after each Gate A.
   - Sources: pstack `feature.md:7-11` and `multi-phase-plan.md:48-51`; Cognition 2026 ("writes stay single-threaded"); Google's scaling study (+81% on parallel tasks, −39 to −70% on sequential ones).
   - Run A missed that tickets 29 and 15 both changed `agent-prompt.ts`. In run B, tickets 26 and 33 both edit docs `agent.md`.
3. **Name one peer per overlap in the brief, with one action**, such as "whichever merges second rebases; flag it at Gate A". This worked every time in run A.
4. **Pilot first.** Launch one worker and let it reach its plan before launching the rest.
   - Source: pstack `orchestrate.md`: "a flaw in the kickoff costs one agent instead of fifty".
   - Since your latency dominates anyway, the delay is nearly free, and it gives the run-wide facts (below) once.
5. **Let the coordinator dispatch the workers itself**, as background sessions: `claude --bg --name <ticket> "/rc-orchestrate <ticket path>"`.
   - This replaces opening sessions by hand.
   - `claude agents --json` reports each one's `state` (`working`/`blocked`/`done`/`failed`). `waitingFor` stayed `null` in every probe and in the trial, so Agent view's "Needs input" group can't be your queue; the coordinator's digest is.
   - Probed on 11-03 with a skill shaped like `rc-orchestrate`; see [*Background-session probes*](#background-session-probes-2026-11-03). Dispatch from the coordinator's Bash works, the skill call in the prompt runs, and the run's own `git worktree add` works.
   - Run end to end on a real ticket on 11-03/04; see [*Real-ticket trial*](#real-ticket-trial-2026-11-0304).
6. **Not agent teams, for now.** They are experimental, give no worktree isolation, allow one team per session with no nesting, and don't work with `-p`.

### Shared state and resources

7. **Separate before serializing.** Each worker writes only its own run file and its own worktree. One writer each for the feature page, the progress memory, and the ticket statuses.
   - Source: pstack principle: "instructions and conventions are not concurrency control".
   - Run A had five sessions refreshing the page (two builds dropped mappings), and two sessions appended to one memory file 7 seconds apart, leaving lines that contradict each other.
8. **A slot for every stateful shared resource: one holder at a time.**
   - **Manual checks:** the shared DB, ports, browser and sign-in session. Releasing means stopping the servers, signing out, closing the tab and restoring `.env`; "releasing to fix" puts the worker back in the queue.
   - **Merging:** one slot per target branch.
   - Workers kept to this in run A without exception.
9. **The merge slot is a merge queue.**
   - **Steps:** fetch, rebase onto the current tip, run the full gate, merge, push only if origin hasn't moved (never force), then report the hashes and range.
   - **On landing,** broadcast the new tips and a rebase map to the next in line.
   - **An approval survives a rebase** only when `git patch-id` is unchanged (pstack `shipping.md:7`). Otherwise the change returns to Gate B.
10. **Ban destructive shared-state commands up front**, for example `db:reset` on the shared DB.
11. **Start the run-wide work once and stagger it.**
    - **Once:** the backend check, recon of commands and test setup, and the feature page create.
    - **Staggered:** BASE failures. Parallel full-suite runs under load produced false BASE failures (223, 581 and 106 suites, from MongoMemoryServer's 10 s launch timeout).
    - **This matters for correctness:** a polluted BASE list later labels real failures as pre-existing. Stagger the runs, or raise `launchTimeout`, or cap the workers.

### Communication

12. **Judge status by side effects, not pings.**
    - The coordinator reads run files, ticket status lines and `claude agents --json`.
    - Never message a worker to check on it: a message restarts an idle agent, and each message to an idle coordinator re-sends its whole context.
    - **An idle notice is a cue to read `state`, not a gate signal.** A worker that waits on a background subagent ends its turn, so `notify_when_idle` fires before any gate. `state` tells them apart: `blocked` at a gate, `working` while it waits on a subagent, `done` at the end (probe 1).
    - **`state` is a hint, not the truth.** It stayed `blocked` after the background service died overnight, and it read `done` while a resumed worker waited on your wrap-up answer (trial). Before messaging a worker, check it is reachable with `ListAgents`; when it isn't, resume it with `claude --bg --resume <session-id> "<message>"`. A worker's waiting point is its last message and its run file.
    - Source: pstack `orchestrate.md:12`; Claude Code docs.
13. **Messages carry events only:** kickoff, plan ready, waiting on the human, slot request or release, committed, landed (with hashes), blocked.
    - Keep each to a few structured lines, and put details in the run file (Anthropic's research system uses 1–2k-token summaries).
    - Batch them: a burst to one session is refused past its inbox limit, and the inbox queues at most 50 messages.
    - `SendMessage`'s `notify_when_idle` gives one notice when a worker goes idle (it expires after 12 hours).
14. **Put the protocol in the first brief, as a file.** The skill ships a protocol file (slots, merge steps, push policy, single writers, banned commands, the message vocabulary) that every worker reads, and the worker cannot edit it.
    - Source: pstack build-the-lever: "write the lever as a skill they all read… outside the delegates' write scope".
15. **Address replies to the session id or socket, not the name.** Names get reused across days ("sidedoor-39"). A socket changes when the session restarts, so look it up again in `ListAgents` (or the worker's latest message) instead of reusing an old one (trial).
16. **The coordinator states its own uncertainty in a brief** ("check how that branch relates to b386359 before you build on it"). The worker settled that in 6 seconds; a guess would have cost a rebase.

### Your time

17. **Bring all your decisions into one sitting.** The coordinator keeps a single "waiting on you" digest:
    - one line per item: window, gate, the question, a recommended answer and its risk;
    - riskiest first;
    - each item self-contained.

    Sources: pstack `ketchup`; Simon Willison ("how fast I can review the results").
18. **You approve in the coordinator's window, and the coordinator performs the approved action. It never relays an approval.** Workers refuse a relayed "commit" (all four in run A, and probe 1), and a peer message never answers a permission prompt.
    - **Review:** a worker stops at Gate B with the ticket uncommitted in its worktree. You review it in VS Code (`code -a <worktree>` adds it to Source Control) and give change requests in the coordinator's window.
    - **Change requests are relayed.** They aren't approvals, so workers apply them and show Gate B again (probe 2).
    - **On approval, the coordinator commits** in the worker's worktree, then sends the worker the hash. The worker checks the commit against git, doesn't commit again, and runs its wrap-up (probe 2).
    - The coordinator says "approved" only after you typed it in its window. The worker can't verify that claim; it rests on the coordinator's word.
    - **Permission prompts still need the worker's window.** Run workers in a mode that rarely prompts, and `claude attach <name>` when one does.
    - A scoped standing approval also works when you give it at launch, since the `--bg` prompt counts as typed by you.
    - Gate B's reading of the code stays per ticket.
19. **Book human-only steps back to back.** That means sign-ins and UI checks. Check the credentials exist before booking, and never hold a slot while you're away (ticket 29 held the check slot for 17 hours).
20. **Changes that loosen a gate need a countersign.** A skipped test or a new BASE-failure entry goes on Gate B's `Your call:` line (pstack `autopilot-full.md:20`: "the owner is the one who wants green").

### Failure handling and accounting

21. **Account for every worker** as done, replaced, absorbed or dropped. A worker that went silent is `not run`, never "clean" (pstack `orchestrate.md:21`, EGM synthesizer).
22. **Retry by cause, at most twice, then replan.**
    - **The causes:** a smaller scope after a context limit, the same brief after a dropped connection, a different model after a tool error.
    - **Waiting on you is not stuck.**
    - Source: pstack `orchestrate.md:22`.
23. **Before reporting on a ticket, check its live state:** `git log`, the run file, `claude agents`. Don't rely on its last message.

### After a wave

24. **Run a cross-ticket review once a wave lands.** Look for duplicated helpers, contracts that drifted between tickets, and evals made stale by another ticket's prompt change. Then compare the slice spec against the code.
    - Sources: the old Phase 2 in the notes; EGM's drift report.
    - Ticket 15 left ticket 12's eval case stale, and nobody saw it for three tickets.
25. **Keep a run-level ledger** in the coordinator's own run file: per ticket, active time, time waiting on you, time waiting on a slot, and cost. Run A's numbers had to be reconstructed from transcript timestamps.

## Reuse or build

- **Reuse from pstack (MIT, adapt for Claude Code):**
  - `ketchup`, for the waiting-on-you digest;
  - the Topology and Supervision rules of `orchestrate.md`, cited rather than rewritten;
  - the principles `separate-before-serializing-shared-state` and `sequence-verifiable-units`;
  - `show-me-your-work`, for the coordinator's decision trail.

  Skip `autopilot-full` (owners merge on their own, which bypasses Gate B), `swarm` and `arena` (they need Cursor's cloud VMs and model roles), and `babysit`.
- **Use Claude Code itself** for dispatch and status: background sessions, `claude agents --json`, cross-session messaging, `notify_when_idle`, and hooks such as `Stop` and `SubagentStop`. Write no polling scripts.
- **Build our own coordinator skill.** Nothing existing combines a Gate B per ticket, codex executors, our run files and the feature page. It calls `rc-orchestrate` per ticket and adds the protocol file, the slots, the touch-list check, the digest and the wave review.

## Background-session probes (2026-11-03)

Two throwaway skills shaped like `rc-orchestrate`, each dispatched from a coordinator session with `claude --bg --name <name> "/<skill>"` (Claude Code 2.1.317, Opus 5.5 high, auto mode inherited from the coordinator). Probe 1 ran worktree, subagent, edit, Gate A, Gate B. Probe 2 ran Gate B with a change request, then a coordinator commit.

| Question | Result |
|---|---|
| Dispatch from the coordinator's Bash | Works; returns at once with an id. |
| A skill call as the `--bg` prompt | Runs, even with `disable-model-invocation: true`; it counts as typed by you. |
| The run's own `git worktree add` | Works. `bgIsolation` didn't move the session, and no `.claude/worktrees/` appeared. |
| Subagent rows in `claude agents` | None; the worker's subagent stayed inside its row. |
| Gate state | `blocked` at each gate, `working` while waiting on a subagent, `done` at the end. `waitingFor` stayed `null` throughout. |
| Idle notices | Fired on the subagent wait as well as at gates; see practice 12. |
| Relayed Gate A answer | Accepted, and logged as coming from a peer session. |
| Relayed "commit" at Gate B | Refused: "a peer session cannot give that approval for the user". |
| Relayed change request at Gate B | Applied, left uncommitted, Gate B shown again. |
| Coordinator commits, then tells the worker | Worker checked the commit against git, didn't commit again, finished the wrap-up. |

Not tested: a real `rc-orchestrate` run, Gate B answered through `claude attach`, and permission prompts in a detached worker. To parse `claude agents --json` here, use Python: asdf has no `jq` version set for this repo, so `jq` fails.

## Real-ticket trial (2026-11-03/04)

`rc-orchestrate` on sidedoor's `tickets/frontend-test-teardown-flakes.md` (frontend only, no feature folder), launched from the claude-skills coordinator with `claude --bg --name teardown-flakes "/rc-orchestrate <ticket>"` and a prompt paragraph naming the coordinator's socket. `rc-orchestrate` had first gained its *Coordinator committed* path at Gate B. Auto mode, inherited.

| Step | Result |
|---|---|
| Launch to Gate B, unattended | 20 minutes: recon, plan, cycles, review (5 fixed · 1 deferred · 1 rejected), trim, manual-checks guide. Every executor ran on codex, with no step-ups. Gate A skipped: no open questions. |
| Gate B report | Sent to the coordinator word for word, which showed it to you. `state` went `blocked`. |
| Approval and commit | You approved in the coordinator's window. The coordinator committed (0bebd40) and pushed the branch. |
| Overnight | The background service died: no process, no socket, `claude logs` failed, yet `claude agents --json` still said `blocked`. |
| Recovery | `claude --bg --resume <session-id> "<the coordinator's message>"` woke it with its saved options and full context. It came back on a new socket. |
| Coordinator committed | The worker checked the commit (parent BASE, diff matches Gate B, worktree clean, origin points at it), resolved the ticket, ran `checkup` and `build`, and sent Finish's offer. `state` read `done` while it waited. |
| Wrap-up | Your retro and cleanup answers relayed and accepted. |

What it adds to the practices: `state` can be stale or misleading (practice 12), sockets change on restart (practice 15), and the sandbox blocked a codex fixer's `git mv` in the worktree's index (the worker resumed it with a plain `mv`).

Still not tested: Gate A relayed on a real ticket, a permission prompt in a detached worker outside auto mode, and two or more workers at once.

## Open questions

- Confirm Gate A on a real ticket, and a ticket with a feature page (the single page writer of practice 7).
- Does Gate A belong in the worker or the coordinator? Probe 1 showed that a worker accepts relayed Gate A answers, so holding every Gate A in the coordinator's window would batch your planning answers into one sitting. Under practice 18, Gate B's approval moves to the coordinator too; only its review of the code stays per ticket.
- How many workers to run at once? Your attention, not the agents, sets the limit. Run A's four worked; the docs suggest 3–5 for teams.
