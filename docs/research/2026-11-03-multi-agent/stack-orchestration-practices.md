# Multi-agent orchestration practices in pstack and EGM

Catalogue for designing the multi-ticket / multi-session skill that sits above `rc-orchestrate`.

**Source roots.**

- `pstack/` = `scratchpad/cursor-plugins/repo/pstack/` (Cursor plugin by poteto, MIT, `pstack/LICENSE`: "Copyright (c) 2026 Lauren Tan"; no LICENSE at the repo root above it).
- `pm/` = `pstack/skills/poteto-mode/`, `pb/` = `pm/playbooks/`.
- `egm/` = `scratchpad/egm/repo/` (google/elephant-goldfish-model, Apache-2.0, `egm/LICENSE`).
- Ours: `docs/multi-ticket-skill-notes.md` (notes), `skills/rc-orchestrate/SKILL.md` (orch).

**Our constraints used for the verdicts.** Gate B (human approval) per ticket, held in the main session. Codex executes, Claude reviews. Subagents cannot talk to the user. Separate Claude Code sessions can message each other (SendMessage / ListAgents). `rc-orchestrate` merges locally at Finish; pushing is the user's call (orch:265). One executor per working tree (orch:57). Only the main session publishes the feature page (notes:35).

**Verdict key.** As-is: adopt the rule unchanged. Adapt: adopt with the stated change. Conflicts: clashes with our design (reason given). Skip: not relevant.

---

## 1. Topology and decomposition

### T1. The coordinator runs the program, never the code
- **Rule.** The coordinator decides which agent does each piece and checks what it produces. It never authors or edits code. Conflicted merges, rebases, and fixes go to the owners.
- **Source.** `pb/orchestrate.md:3` "You run the program, never the code."; `:9` "You never author or edit code. Conflicted merges, chain rebases, and fixes go to owners."
- **Prevents.** The coordinator's context fills with code. It loses the program view and becomes a second, unreviewed writer.
- **Verdict.** As-is. This is `rc-orchestrate`'s rule one level up (orch:11). The multi-ticket coordinator never runs an executor itself. It does not even run `rc-orchestrate` steps; it delegates them to ticket sessions.

### T2. One owner per unit, the only writer of its branch
- **Rule.** Each PR has one owner that carries it from build to merge. Only the owner pushes, rebases, or retargets the branch. Retargeting a base orphans everything above it, so the owner does that only on the coordinator's call.
- **Source.** `pb/orchestrate.md:9` "The owner is the only writer of its branch and carries the PR from build to merge."
- **Prevents.** Two actors writing one branch. Silent orphaning of dependent work.
- **Verdict.** Adapt. Owner = one Claude Code session running `rc-orchestrate` for one ticket, in its own worktree on its own branch. Landing onto the integration branch is the exception: see S5/S6. Either the coordinator lands, as the single writer of the integration branch, or the owner lands on the coordinator's call. It must not be both.

### T3. Fresh worker per independent task, with upstream reports pasted in full
- **Rule.** A kickoff carries everything the worker needs, including each upstream report it depends on, pasted in full. Workers cannot see their siblings.
- **Source.** `pb/orchestrate.md:10` "Its kickoff carries everything it needs, including each upstream report it depends on, pasted in full. Workers can't see their siblings."
- **Prevents.** A dependent ticket rebuilding or contradicting what its parent decided.
- **Verdict.** Adapt. `rc-orchestrate` briefs point at files instead of pasting (orch:287). For a dependent ticket, the kickoff should name the parent ticket's run file and its approved Gate B report by path, plus any decision quoted from chat. Paste only what lives nowhere on disk.

### T4. Three levels at most; a sub-coordinator sends one rollup; about ten in flight; rolling start
- **Rule.** Add a sub-coordinator only when one area has many parallel workers. It sends the coordinator one rollup, never raw worker reports. Stop at three levels. Keep about ten workers in flight per coordinator. Start the next worker as each finishes, not in batches.
- **Source.** `pb/orchestrate.md:11` "Stop at three levels: you, sub-coordinators, and workers. Keep about ten workers in flight per coordinator, and start the next one as each finishes instead of waiting on a whole batch."
- **Prevents.** Coordinator context flooding. Idle capacity while a batch drains.
- **Verdict.** Adapt. Our tree is already exactly three levels: multi-ticket coordinator, then ticket sessions (each a sub-coordinator running `rc-orchestrate`), then executors and reviewers. Keep the rolling start. Ten is the wrong cap for us. Our bottleneck is the human at Gate B, not the agents. Cap in-flight tickets at what the user can review (likely 2 or 3), and start the next ticket when a Gate B clears, not when an agent finishes.

### T5. Pilot first
- **Rule.** Take one unit through kickoff, owner, verifier, and merge before fanning out. On near-identical cheap units, the first unit is the test.
- **Source.** `pb/orchestrate.md:14` "Start with one unit. … so a flaw in the kickoff costs one agent instead of fifty."
- **Prevents.** A kickoff flaw replicated across every parallel ticket.
- **Verdict.** As-is. Run the first ticket alone, through Gate B and landing, before opening parallel tickets. That run also produces the run-wide facts (backend check, BASE failures, recon) that later tickets reuse (notes:25-29).

### T6. The throughput checkpoint decides independence
- **Rule.** Before fan-out, write four items. *Blocking first steps* run before fan-out. *Independent workstreams*: disjoint files, services, or layers parallelize, and shared writes serialize. *Shared mutable state*: default to splitting it. *Smallest safe decomposition*: if one worker is best, say why. A dimension that does not apply keeps its line as `n/a: <reason>`.
- **Source.** `pb/feature.md:7-11` "Disjoint files, services, or layers parallelize. Shared writes serialize."
- **Prevents.** Parallel tickets that collide on the same files. Parallelism chosen by default rather than by evidence.
- **Verdict.** As-is. This is the independence test our notes leave open (notes:7). Two tickets run in parallel only when their file globs from recon are disjoint and neither has a blocking edge on the other.

### T7. Parallel off trunk; stack only on a real build dependency
- **Rule.** Owners run in parallel off trunk, never stacked, so each lands alone. A PR stacks only on a PR it builds on, and then rebases onto its parent's branch.
- **Source.** `pb/autopilot-full.md:13` "Run owners in parallel off trunk, never stacked, so each PR lands on its own."; `pb/autopilot-stack.md:6` "Stack a PR only when it builds on another PR."
- **Prevents.** False dependencies that serialize landing. A rejection in one ticket blocking unrelated ones.
- **Verdict.** Adapt. Independent tickets branch from the run-level BASE (notes:11). A dependent ticket starts only after its parent's Gate B approval and branches from the parent's approved commit. That is the plan template's rule: "Start dependent work only after its parent merges, or base it on the parent branch" (`pb/multi-phase-plan.md:48`).

### T8. A dependency graph and file boundaries written into the plan
- **Rule.** The plan lists which units are independent and first, which depend on which, and each unit's file glob ("<PR id> touches only `<glob>`").
- **Source.** `pb/multi-phase-plan.md:48-51` "Hold the file boundaries. <PR id or class> touches only `<glob>`."
- **Prevents.** Scope creep into a sibling's files. Dependencies that exist only in the coordinator's head.
- **Verdict.** As-is. Put it in the multi-ticket run file. Each ticket's brief carries its glob as the "boundary" (orch:283).

### T9. Code-coupled work goes to one owner
- **Rule.** One feature or one migration goes to a single owner, who fans out internally after the blocking phase. Parent-level fan-out is for slices that produce independent artifacts.
- **Source.** `pb/feature.md:19` "Code-coupled work (one feature, one migration) goes to a single owner with the checkpoint inline."
- **Prevents.** Splitting tightly coupled code across owners who cannot see each other.
- **Verdict.** As-is. When two tickets share a seam, run them in sequence in one session, or merge them into one ticket, rather than in parallel.

### T10. Not a program if one agent can finish it
- **Rule.** Work one agent could finish within the session's budget is not a program, however program-shaped it sounds.
- **Source.** `pb/orchestrate.md:3`; `pm/SKILL.md:143` "Work one agent could finish inside the session's budget routes there, not here".
- **Prevents.** Paying coordination overhead for small runs.
- **Verdict.** As-is. Two small tickets go through `rc-orchestrate` one after the other in one session. Multi-session only pays off with several independent tickets. EGM uses the same kind of threshold: direct execution at 5 directories or fewer, a swarm above that (`egm/agents/bootstrap_orchestrator.md:27-28`).

### T11. Sequential stages; parallel only within a stage
- **Rule.** Keep review stages sequential. Parallelize only the reviewers within the current stage. Wait for every one, write the report, and finish remediation before the next stage. Uninterrupted mode skips human checkpoints, not stage dependencies.
- **Source.** `egm/docs/claude.md:41-44` "Keep review stages 5, 6, 7, 8, and 9 sequential. Parallelize only reviewers within the current stage. … Uninterrupted mode skips human checkpoints, not these stage dependencies."
- **Prevents.** Later stages running on input that earlier stages would have changed.
- **Verdict.** As-is, as "waves". Tickets in one dependency wave run in parallel. The next wave starts when the current wave's prerequisites are approved and landed. The cross-ticket review (notes:15) is its own final stage.

### T12. Fan-out shape is declared up front
- **Rule.** Partition into slices, race N workers on identical briefs, or mix both. For a race, declare `first pass`, `rank all`, or `best-of` before spawning.
- **Source.** `pstack/skills/swarm/SKILL.md:21`.
- **Prevents.** Picking the selection rule after seeing the results.
- **Verdict.** Adapt, narrowly. Tickets are a partition, not a race. This matters only if we ever race codex against Claude on one ticket.

---

## 2. Ownership and verification

### V1. The verifier is not the author, and comes from a different model family
- **Rule.** Each PR gets a verifier that did not write it, on a different model family. The owner merges only on that verifier's pass at the current head.
- **Source.** `pb/orchestrate.md:13` "Each PR gets a verifier that isn't its author, on a different model family."; `pb/shipping.md:5` "Only a verdict from an agent that did not write the code counts, because an author checks what it meant to build."
- **Prevents.** Self-verification bias. An author checks what it meant to build.
- **Verdict.** As-is. This is our codex-executes, Claude-reviews split (orch:9). Note that pstack in Claude Code loses this: non-Claude slugs collapse to the session model (`pstack/docs/harness/claude-code.md:35`). We keep the split because we route execution through `rc-codex`.

### V2. Read the diff, not the summary; a verdict covers one head
- **Rule.** Read the diff or the artifact, not only the worker's summary. Green CI is an input to a verdict, not a verdict. A verdict covers one head SHA, so a new push needs a new verdict.
- **Source.** `pb/orchestrate.md:19` "A verdict covers one head SHA, so a new push needs a new verdict."
- **Prevents.** Approving code that changed after review.
- **Verdict.** As-is. Gate B approval covers one tree. A rebase onto the integration branch after approval needs either a new check or the patch-id carry in V3.

### V3. The patch-id rule: a verdict survives a rebase only if the patch is unchanged
- **Rule.** A verdict covers a patch. Before trusting an older verdict after a rebase, compare `git patch-id` at the verdict SHA with the current head. If they match, the verdict stands. If they differ, re-verify what drifted.
- **Source.** `pb/shipping.md:7` "Compare `git patch-id` at the verdict SHA with the current head before trusting an older verdict."; `pb/autopilot-stack.md:6` "a PR whose `git patch-id` the restack leaves unchanged keeps its verdict."
- **Prevents.** Re-asking the human about code they already approved. Or the reverse: landing code whose approved form no longer exists.
- **Verdict.** As-is. This is the best answer to "a ticket approved at Gate B must be rebased before landing". Same patch-id: land without a second Gate B. Changed patch-id (a conflict resolution): re-run tests, review the delta, and show a short re-approval.

### V4. Account for every worker
- **Rule.** Account for every worker spawned as done, replaced, or absorbed into another worker's scope.
- **Source.** `pb/orchestrate.md:21` "Account for every worker you spawned as done, replaced, or absorbed into another worker's scope."
- **Prevents.** Orphaned sessions that still hold worktrees, and tickets that silently never ran.
- **Verdict.** As-is. The coordinator's run file keeps one row per ticket session: id/name, worktree, branch, state (running, waiting-gate-B, approved, landed, replaced, absorbed, dropped).

### V5. A worker that did not report did not run
- **Rule.** A reviewer that times out, fails, or returns no report did not review. Retry it once. If it fails again, record it as `not run`. Never count it as zero findings. A summary that omits a reviewer's status means `not run`, and a `not run` reviewer makes the round unclean.
- **Source.** `egm/skills/egm-review-loop/SKILL.md:132-136` "Never count it as a reviewer with zero findings."; `egm/agents/synthesizer.md:40`; pstack's version is `pstack/skills/swarm/SKILL.md:37` "After a second miss, record a gap. A gap does not count as a pass."
- **Prevents.** Silent coverage holes reported as clean results.
- **Verdict.** As-is. Our commit `ea07f35` already counts not-run reviewers. Extend it to ticket sessions: a session that dies or goes silent is `not run`, not "no changes".

### V6. Results must carry their provenance
- **Rule.** Drop a result that does not record the SHAs and method its brief named, and respawn that worker once.
- **Source.** `pstack/skills/swarm/SKILL.md:23,37` "Drop a result that does not record the SHAs and method its brief names".
- **Prevents.** Verdicts that cannot be tied to the code they judged.
- **Verdict.** As-is. A ticket session's Gate B-ready message must name the branch, the head SHA, and the tree it was reviewed at.

### V7. Each kickoff names the evidence that proves done
- **Rule.** Each kickoff names the done-evidence (a command and its expected output, a check, or an artifact). It also names the goal, the paths the worker may and may not write, and the actions it must not take. If you cannot name the evidence, the unit is not scoped yet.
- **Source.** `pb/orchestrate.md:18` "If you can't name the evidence, the unit isn't scoped yet."
- **Prevents.** Unverifiable tickets entering the parallel pool.
- **Verdict.** Adapt. Our brief list (orch:279-285) lacks "may not write" and "must not take". Add both to the ticket-session kickoff: no writes outside the worktree, no merge into the integration branch, no feature-page publish, no push.

### V8. Send back drift; park non-blocking fixes
- **Rule.** Send back work that drifts from scope or grows past what was asked. Keep only fixes that block the program. Park the rest as follow-ups.
- **Source.** `pb/orchestrate.md:20`.
- **Prevents.** Ticket scope creep that breaks file-boundary independence (T8).
- **Verdict.** As-is.

### V9. Block only on a problem you can show
- **Rule.** Block a PR only for a problem you can show, with a failing run at the head or a doc line the PR made wrong. A problem the base already has does not block unless the PR copies it or newly reaches it. Everything else becomes a follow-up.
- **Source.** `pb/autopilot-full.md:16` "A problem the PR's base already has … doesn't block unless the PR copies it or newly reaches it."
- **Prevents.** Cross-ticket review churning on pre-existing debt.
- **Verdict.** As-is for the cross-ticket review triage. It matches our BASE-failures logic (orch:51).

### V10. Loosening a gate needs a countersign
- **Rule.** Anything that loosens a gate (a raised budget, an allowlist entry) needs a verifier's proof and then the coordinator's fresh countersign, because the owner is the one who wants green. A disabled or soft-failed check always comes out.
- **Source.** `pb/autopilot-full.md:20` "because the owner is the one who wants green."
- **Prevents.** An owner relaxing a test, skip-listing a failure, or widening the BASE failures to get approved.
- **Verdict.** Adapt. Make it a Gate B line: any ticket that edits test config, skips tests, or adds to the BASE-failures list shows it as "Your call".

### V11. You own every subagent's work
- **Rule.** Review the diff and write your own summary. Do not pass through what the subagent said. A second opinion is the same prompt on a different model, and agreement is high-signal.
- **Source.** `pm/SKILL.md:100`.
- **Prevents.** Relaying a worker's optimistic summary to the human as fact.
- **Verdict.** As-is. It matches orch:17 ("An executor's summary is a claim").

### V12. Fresh agents by default; resume only for state that is costly to move
- **Rule.** Give new work (a fix round, follow-up, retry, or next queue item) to a fresh agent with consolidated scope: the original brief, every later directive, and the prior report and branch. Resume an existing agent only when the work needs its checkout, uncommitted changes, or a running process. A role (such as PR owner) outlives its agent.
- **Source.** `pm/SKILL.md:102` "Interrupt-chained resumes silently drop directives, so fire a fresh subagent with consolidated scope rather than trusting a 'done' summary."
- **Prevents.** Lost directives in long-lived agents. A stale "done".
- **Verdict.** Adapt. A ticket session is a long-lived role. Keep it alive while its worktree holds uncommitted work awaiting Gate B. That is exactly the "state costly to move" exception. Our codex resume rule (orch:91) also falls under the same exception (warm cache, same cycle). For a stalled or crashed ticket, start a fresh session with the consolidated brief rather than messaging the old one.

---

## 3. Shared state and resources

### S1. Separate before serializing
- **Rule.** When concurrent actors might write the same file, branch, or key, first remove the sharing. Give each actor its own file and merge only at the read or reporting boundary. Two workers writing their own field into one `state.json` is still shared mutation. Serialize structurally (lockfile, sequential phase, single writer) only for a real invariant. Instructions and conventions are not concurrency control.
- **Source.** `pstack/skills/principle-separate-before-serializing-shared-state/SKILL.md:9,15-16` "Instructions and conventions are not concurrency control."
- **Prevents.** Intermittent races on the run file, the ticket file, and the feature-page data.
- **Verdict.** As-is, and central. Each ticket session writes only its own run file and its own status file (`<feature>/runs/<slug>.md`, notes:29). The coordinator is the single reader and the single writer of the multi-ticket run file and the feature page. That resolves notes:35 structurally rather than by instruction.

### S2. Each worker gets its own writable output
- **Rule.** Each writing worker gets its own output location (a git worktree where possible).
- **Source.** `pstack/skills/swarm/SKILL.md:23`; `pstack/skills/arena/SKILL.md:18` "Give each candidate its own output location (a git worktree where possible …)".
- **Prevents.** Executor collisions in one tree.
- **Verdict.** As-is. One worktree per ticket, matching notes:33. Per-repo index snapshots then live in each ticket's run dir (notes:34).

### S3. A single external writer
- **Rule.** The coordinator is the only poster to the external surface. Every child prompt explicitly forbids those writes. Never give a child the credentials. If a child needs write access to run, do not launch it.
- **Source.** `pstack/automations/benny/skills/reproduce-and-fix-issues/SKILL.md:18-23` "The coordinator is the only Slack poster. … If a child needs Slack write access to run, do not launch it."
- **Prevents.** Duplicate or conflicting posts. Workers acting externally without review.
- **Verdict.** Adapt. Our "external surfaces" are the user, the feature page, the integration branch, and ticket resolution. Ticket sessions are told not to publish the page, not to resolve the ticket, and not to merge. They report, and the coordinator does those things. Ticket sessions can talk to the user (they are sessions, not subagents), but only for their own Gate B (H1).

### S4. Keep the base through fix rounds; rebase only for a reason
- **Rule.** Rebase onto current trunk before the code-ready report. Keep that merge base during fix rounds. Rebase again only at merge prep, on a conflict with trunk, on a failure that comes from trunk, or when a known concurrent change to the same files lands.
- **Source.** `pb/multi-phase-plan.md:61`; `pb/autopilot-full.md:10` "Fix rounds stay on that base unless trunk conflicts, breaks CI, or lands a known concurrent change to the same files, because each rebase restarts CI."
- **Prevents.** Endless rebasing. A moving target under review.
- **Verdict.** As-is. A ticket keeps its BASE through Phase 1 and Gate B. It rebases only at landing.

### S5. Rebase at merge prep only when the code that would land was never tested
- **Rule.** Right before merging, fetch trunk and ask whether its changes can affect the patch. Rebase and retest when the landing code was never tested (a conflict, a file both sides changed, a change to which checks run). When trunk changed a caller or a dependency of the patch, run the patch's checks on the merge result. Otherwise merge. If a third rebase looms, hold and report to the root, which sequences the colliding work.
- **Source.** `pb/autopilot-full.md:19` "because rebasing for every trunk move never ends. … If trunk would force a third rebase past merge prep, hold and report to the root, which sequences the colliding work."
- **Prevents.** Untested merge results landing, and also endless rebase loops.
- **Verdict.** As-is for landing approved tickets onto the integration branch. Combine with V3.

### S6. Land the contiguous verified run bottom-up, and leave the stack alone while landing
- **Rule.** Walk up from the lowest unmerged unit and stop at the first one without a pass. Land that run one at a time, lowest first. A verified unit above an unverified one waits. While landing, the only branch change allowed is moving the next unit onto the merge result.
- **Source.** `pb/shipping.md:6` "Land only the contiguous verified run rooted at the bottom."; `:9` "Leave the stack alone while it lands."
- **Prevents.** Landing a child without its parent. Concurrent edits racing the landing.
- **Verdict.** Adapt. For us "verified" means Gate B approved. Independent tickets have no stack, so each lands on approval. Dependent chains land bottom-up. GitHub mechanics (retarget, `--auto`, merge queue) are skipped because we merge locally.

### S7. Work only the merge frontier; one babysitter per stack; never mutate topology from a side role
- **Rule.** The lowest unmerged PR is the only one that matters until it merges. Upstack items are read and batched, not fixed. Before starting, check nobody else is babysitting. A babysitter never rebases, retargets, or force-pushes; it reports rebase-shaped work to the owner.
- **Source.** `pb/babysit.md:8-10` "Work the merge frontier and nothing above it."; "One babysitter per stack."; "Never mutate stack topology."
- **Prevents.** Thrash from fixing upstack while the base is red. Two landers.
- **Verdict.** Adapt. One lander (the coordinator) per integration branch. Note the "check nothing else is already on it" step is a convention, which pstack's own S1 says is not concurrency control. Use ListAgents plus a claim recorded in the coordinator's run file.

### S8. Classify a failure before retrying
- **Rule.** Flake or infrastructure earns one fresh build, never a job retry. An identical second failure means it was never flake. A failure in code the diff never touches means a stale base (check with `git merge-base --is-ancestor`). Only a failure in the diff's own code gets a commit.
- **Source.** `pb/babysit.md:19` "An identical second failure means it was never flake … A failure in code the diff never touches means a stale base".
- **Prevents.** Retry loops, and fixes committed for problems the ticket did not cause.
- **Verdict.** As-is. It extends our BASE-failures and flaky-test rule (orch:51) with the stale-base check, which matters once parallel tickets land at different times (notes:26).

### S9. Make operations idempotent; reconcile from observed state
- **Rule.** Derive each step from the state that exists, not from what the previous run meant to do. Anything a run leaves behind (a lock, temp file, claimed job) must be recognizable as stale by the next run. Test it: what if this runs twice, or crashed at every point?
- **Source.** `pstack/skills/principle-make-operations-idempotent/SKILL.md:13-15` "derive each step from the state that exists, not from what the previous run meant to do."
- **Prevents.** A coordinator restart that double-launches tickets or re-lands commits.
- **Verdict.** As-is. On every start or tick, the coordinator rebuilds ticket state from `git worktree list`, branch heads, each ticket's run file, and ListAgents, and diffs that against its plan. EGM's analogue is re-resolving the target range before every round rather than caching it (`egm/skills/egm-review-loop/SKILL.md:101-107`).

### S10. Record agent ids and a stuck-after runtime where a replacement can find them
- **Rule.** Whoever spawns an agent records its id, state, and a stuck-after runtime (from past runs of its kind) in the root's store, so the root can probe it if the parent dies. Assume the machine dies: push early, and push each finished unit before starting the next.
- **Source.** `pb/autopilot-full.md:12` "Assume the VM dies. … Whoever spawns a subagent records its id, state, and a stuck-after runtime from past runs of its kind in that store".
- **Prevents.** Unrecoverable runs when the coordinator or a ticket session crashes.
- **Verdict.** Adapt. There is no push (local only). Each ticket session's run file is the durable record. The coordinator's run file holds each session's name/id and an expected Gate B-ready time. Our run files' landing logs can supply the "stuck-after" baseline.

### S11. Own-branch-only force pushes; stop on foreign writes
- **Rule.** Force-push only your own branch, with `--force-with-lease` pinned to the SHA you last pushed. On any push you did not make, stop and report to the root.
- **Source.** `pb/autopilot-full.md:12` "on any push you did not make, stop and report to the root."
- **Prevents.** Overwriting someone else's work.
- **Verdict.** Adapt. Locally: a ticket session that finds a commit it did not make on its branch, or changes in its worktree it did not make, stops and reports. The checkpoint tree hash (orch:80) makes that detectable.

### S12. Worktree cleanup by evidence; uncommitted work pauses
- **Rule.** Read paths from `git worktree list`, never hand-typed. Classify each worktree by merge state, uncommitted work, and the chat that touched it. The bucket is advice, not permission. `wip` (tracked uncommitted edits) needs a human decision. Clean, merged, not-in-use proceeds.
- **Source.** `pb/worktree-cleanup.md:3-7` "The bucket is advice, not permission."; `pm/scripts/worktree-audit.sh` (134 lines).
- **Prevents.** Deleting a live ticket's worktree, or its uncommitted Gate B work.
- **Verdict.** As-is for the multi-ticket Finish. It extends orch:267. The audit script could be borrowed with attribution (MIT).

### S13. Durable deliverables live outside the session scratchpad
- **Rule.** Write briefs, drafts, and reports to the working directory, not the per-session scratchpad: "it belongs to one session, and the deliverables must outlive it."
- **Source.** `egm/docs/claude.md:29-31`.
- **Prevents.** Losing run state when a session ends, which is fatal for multi-session pickup.
- **Verdict.** As-is. Our run files already live under `<feature>/runs/`. Keep the coordinator's file there too.

---

## 4. Communication

### C1. No relaying between agents; no status pings
- **Rule.** Never relay messages or status between agents. Message a worker only for a follow-up on the same work. Never message one to check on it, because a message restarts an idle agent. Judge progress by side effects.
- **Source.** `pb/orchestrate.md:5` "never relay messages or status between agents."; `:12` "Never message one to check on it, because a message restarts an idle agent."
- **Prevents.** Token burn from waking idle workers. The coordinator becoming a telephone exchange.
- **Verdict.** Adapt. This matters more for us, because SendMessage between sessions is our main channel. Rule: ticket sessions write status to their own files. The coordinator reads files, git, and ListAgents, never pings. SendMessage is reserved for events: the ticket session sends "Gate B ready" or "blocked". The coordinator sends kickoff, a hold, or the user's Gate B answer if the coordinator holds the gates (H1).

### C2. One rollup, artifact first
- **Rule.** A sub-coordinator sends one rollup, never raw worker reports. EGM's synthesizer writes the full report to disk and returns one message with counts by severity and the path. It never puts the report text in chat.
- **Source.** `pb/orchestrate.md:11`; `egm/docs/designs/synthesizer.md:104-111` "The synthesizer must never output the full report text in chat or via `send_message`."; `egm/docs/designs/architecture.md:168-175` (Chat Dump Prohibition, Turn-Yielding Checkpoints).
- **Prevents.** The coordinator's context filling with per-ticket detail.
- **Verdict.** As-is. A ticket session's message to the coordinator is a few lines: ticket, state, head SHA, tests/typecheck, findings counts, and the path to its Gate B report.

### C3. Kickoff content
- **Rule.** The kickoff restates the user's goal. It uses file pointers, not inlined context. It sets an explicit model per role. It names the evidence, the write boundary, and the forbidden actions (V7). It includes upstream reports (T3).
- **Source.** `pm/SKILL.md:19` "Restate the user's goal in each subagent brief"; `pm/SKILL.md:96` "file pointers not inlined context, explicit model per role"; `pb/orchestrate.md:18`.
- **Prevents.** Cold-start agents optimizing the wrong goal.
- **Verdict.** As-is. It is mostly already in orch:277-287. The additions are the forbidden-actions list and the parent-ticket pointers.

### C4. Structured worker reports
- **Rule.** Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence. A worker that can prove a defect lists every one, not only the first. EGM findings get a stable id `<reviewer>-<round>-<n>`, a severity, and a scope.
- **Source.** `pstack/skills/swarm/SKILL.md:31`; `egm/skills/egm-review-loop/SKILL.md:128-131`.
- **Prevents.** Unparseable prose returns. Losing track of a finding across rounds.
- **Verdict.** As-is. Use a fixed vocabulary for ticket-session states and stable finding ids in the cross-ticket review.

### C5. Status ticks report only new, tracked changes
- **Rule.** Each audit tick posts to the operator only when it found a tracked change no earlier message reported (a PR opened, a verdict, a merge, a stuck agent and the action taken, a blocker, a decision only the operator can make). Otherwise it ends silently. It still logs a trail row either way.
- **Source.** `pb/multi-phase-plan.md:42` (the verbatim tick prompt) "If the audit found none, end the turn with no reply text."; `pb/autopilot-full.md:22` "one that changed nothing stays quiet."
- **Prevents.** Status spam that buries the Gate B queue.
- **Verdict.** As-is.

### C6. Guard the context window
- **Rule.** Route bulk work to subagents and keep summaries in the main thread. Size phases and cap scope. Parse long transcripts in a subagent.
- **Source.** `pstack/skills/principle-guard-the-context-window/SKILL.md:9-12`; `pb/session-pickup.md:5`.
- **Prevents.** Coordinator degradation over a multi-day run.
- **Verdict.** As-is. This is also the reason for multi-session over one session with nested agents: each ticket's detail stays in its own session.

### C7. Isolated reviewers get only the task
- **Rule.** Spawn a new agent per independent review. Do not fork or resume a reviewer. Pass only the task, the target, the persona/standard paths, and explicitly supplied context. Never pass parent deliberation. EGM's Claude adapters set `omitClaudeMd: true` and read-only tools (`Read, Grep, Glob`). If the harness has no fresh-context subagent tool, stop: "a review in the same context is not a Goldfish review."
- **Source.** `egm/docs/claude.md:125-151`; `egm/skills/egm-review-loop/SKILL.md:43-44`.
- **Prevents.** The reviewer inheriting the author's assumptions.
- **Verdict.** Adapt. `rc-reviewer` is already a fresh read-only agent. Worth testing EGM's `omitClaudeMd` adapter flag on `rc-reviewer`, since EGM states it needs Claude Code 2.1.271 or later (`egm/docs/claude.md:8`). Unverified by me.

---

## 5. Failure handling

### F1. Retry by cause, twice at most, then replan
- **Rule.** Retry by cause: a smaller scope after a context or memory limit, the same kickoff after a dropped connection, a different model after a tool error. After two retries, drop the unit and replan around it.
- **Source.** `pb/orchestrate.md:22` "Retry by cause … After two retries, drop the unit and replan around it."
- **Prevents.** Blind retries that hit the same wall.
- **Verdict.** Adapt. Within a ticket, our rungs and the codex-to-Claude fallback already do this (orch:47-52, 89). At the coordinator level, a ticket session that fails twice is dropped from the parallel pool. The coordinator re-plans: it narrows the ticket or hands it to the user.

### F2. Stuck detection by side effects; replace at once
- **Rule.** Judge an agent by its pushes and activity, not its status text. An agent is stuck when it errors, cannot start turns, or shows nothing new past its stuck-after runtime. An owner with no push and no trail row by the first tick is stuck. One waiting on you is not stuck, so answer it. Replace a stuck agent at once, without waiting for its stop to land.
- **Source.** `pb/autopilot-full.md:22` "One waiting on you or the operator is not stuck, so answer it. Replace a stuck agent at once"; `pb/orchestrate.md:22` "Judge it by its pushes and PR activity, not its status text."
- **Prevents.** Silent stalls in long runs.
- **Verdict.** Adapt. Side effects for us are run-file landing-log rows, checkpoint hashes, and executor output files. A wake mechanism is needed. pstack uses Cursor's `/loop 1h` (`pb/multi-phase-plan.md:41`). In Claude Code it would be the Monitor tool, a scheduled wake, or simply the arrival of SendMessage events. Which of those exists in the user's version I did not verify.

### F3. A late returner is reconciled, not trusted
- **Rule.** When a stopped worker returns late, check its result against the current state, and hand any unique findings to a fresh worker.
- **Source.** `pb/orchestrate.md:22`.
- **Prevents.** A replaced session's stale "done" overwriting its replacement's work.
- **Verdict.** As-is.

### F4. Hold means zero writes, everywhere, at once
- **Rule.** On the operator's hold or stop, send every owner a zero-writes order at once. Each reports where it stands and keeps its brief until released.
- **Source.** `pb/autopilot-full.md:23`; `pb/multi-phase-plan.md:43`.
- **Prevents.** Owners continuing to write after the human said stop.
- **Verdict.** As-is, via SendMessage to every ticket session. This is one of the few legitimate coordinator-to-session messages.

### F5. Pause safely: a checkpoint a cold agent can resume from
- **Rule.** Stop at a safe boundary and cancel nested subagents. Take no irreversible action to pause. Commit uncommitted edits as one `wip:` commit. Write a resume note off-context with intent, progress, what is verified, next steps, key files, and gotchas. Point at an existing trail rather than duplicating it. "Keep going" never pauses.
- **Source.** `pb/pause-safely.md:3-8`.
- **Prevents.** Lost in-flight state on restart, compaction, or going offline.
- **Verdict.** Adapt. A `wip:` commit on the ticket branch conflicts with "commit only on Gate B approval" (orch:257). Instead, snapshot the tree with the existing checkpoint mechanism (orch:80-85) and record the tree hash in the run file's resume section, or write a `wip` ref outside the branch.

### F6. Session pickup: the trail is authoritative, but verify claims on the artifact
- **Rule.** Read the prior trail and reconstruct state (branch, worktree, what landed, todos, decisions). Do not redo completed work. Then verify the inherited claims against the goal on the real artifact, because a passing self-report is not proof.
- **Source.** `pb/session-pickup.md:6-9` "The prior trail is authoritative input. Resist the bias to re-derive it."; `:9` "A passing prior self-report is not the proof."
- **Prevents.** Both waste (redoing work) and blind trust.
- **Verdict.** As-is, with a note: steps 3 and 5 pull against each other. Our resolution: trust the decisions in the run file, but re-run the cheap checks (tests, typecheck) on the inherited tree before going on.

### F7. A checkable exit predicate; never relax it
- **Rule.** State the exit condition as a checkable predicate before the first iteration. A plateau is not a stop. Never relax the predicate to declare victory. A duration is not a finish condition.
- **Source.** `pb/autonomous-run.md:5,11`; `pstack/docs/guide/07-overnight.md:120` "a duration is not a finish condition."
- **Prevents.** Hours of motion with no result. Goal reinterpretation.
- **Verdict.** As-is. The coordinator's predicate: every planned ticket is landed, dropped with a reason, or waiting on the user, and the cross-ticket review is clean.

### F8. Convergence, churn, and cap in a review loop
- **Rule.** A finding is *settled* when contested or accepted as risk, and a settled finding is not reopened. A *fixed* finding that reappears at the same scope is reopened. A round is *clean* when there is no unsettled Blocker or Major, and a `not run` reviewer makes it unclean. *Converged* = two consecutive clean rounds. *Cap* = 5 rounds. *Churn* = a new finding at the scope of an applied fix that reverting the fix would resolve. On cap or churn, ask the user one question.
- **Source.** `egm/skills/egm-review-loop/SKILL.md:151-173` "Converged: Two consecutive clean rounds. One clean round is not enough, because the next fresh reviewer can find a different gap in the same text."
- **Prevents.** Infinite fix-review loops. Re-litigating settled findings. Fix ping-pong.
- **Verdict.** Adapt. Use the settled/fixed/churn definitions in the cross-ticket review and in Gate B change-request rounds (orch:255 already asks the user before a fourth round). "Two clean rounds" doubles review cost. Use it only for the final cross-ticket review, if at all.

### F9. Fail closed; don't race an owner
- **Rule.** Fail closed when config, required access, or the adapter is missing. Stop when a person clearly owns the fix. An existing fix artifact switches the run to verify mode, with no authoring over it.
- **Source.** `pstack/automations/benny/skills/reproduce-and-fix-issues/SKILL.md:11,28,103` "If a person owns the work but has not produced an artifact, stop. Do not race them."
- **Prevents.** Two sessions (or a session and a human) building the same ticket.
- **Verdict.** Adapt. Before kicking off a ticket, check its status (already in progress, already resolved, or a branch already exists) and skip it if someone owns it.

### F10. Divergence means the frame was wrong
- **Rule.** If parallel candidates wildly diverge, the frame was under-specified. Reframe and re-run rather than averaging. A problem verification finds that the arena missed means go back to the frame or the graft.
- **Source.** `pstack/skills/arena/SKILL.md:40,44`.
- **Prevents.** Papering over a bad brief.
- **Verdict.** Adapt. When two parallel tickets come back with contradictory contracts, the plan's seams were under-specified. Go back to Gate A rather than reconciling in the cross-ticket review.

---

## 6. Human involvement

### H1. Gates stay with the human; everything else does not reach them
- **Rule.** Ask the user only for a real decision or a blocker: an irreversible action, a product or preference call no experiment settles, or a dead end that survived a replan. Rebase mechanics, retries, CI flakes, review triage, and "should I keep going" never reach the user.
- **Source.** `pb/orchestrate.md:23`.
- **Prevents.** Decision fatigue that turns Gate B into rubber-stamping.
- **Verdict.** As-is, outside Gate B. The open design choice: does each ticket session hold its own Gate B (sessions can talk to the user) or does the coordinator collect them? notes:36 assumes the main session. With multi-session, a ticket session can hold its own Gate B. That keeps the code-review context next to the change-request flow (orch:242-257), but scatters the user across N sessions. Recommendation: the ticket session holds Gate B (it owns the change-request loop and the worktree). The coordinator holds the queue view (H4) and the landing.

### H2. Never block on the human, for reversible work
- **Rule.** The human supervises asynchronously. Proceed on reversible work, present the result, and let the human course-correct. Irreversible actions still need confirmation.
- **Source.** `pstack/skills/principle-never-block-on-the-human/SKILL.md:9-15`.
- **Prevents.** Agents idling on questions they could answer.
- **Verdict.** Conflicts in part. Our Gate B deliberately blocks every commit on the human, because the human reads the code to stay grounded (orch:225). Adapt the spirit: a ticket waiting at Gate B blocks only itself and its dependents. Every independent ticket keeps running. pstack's "waiting on you is not stuck" (F2) is the matching rule.

### H3. Classify a fork before asking
- **Rule.** Before asking "which approach", classify the question. If a run could settle it (behavior, timing, output, perf), prototype it and let the result decide. Ask only about genuine product or preference calls.
- **Source.** `pm/SKILL.md:21`.
- **Prevents.** Burning human attention on empirical questions.
- **Verdict.** As-is for Gate A planning and "Your call" lines.

### H4. Queue decisions in a self-contained digest
- **Rule.** Open with one sentence naming what waits on the user. Then give a short what-happened section (under 100 words). Then each action item, about 30 words each, with its link, what it changes for users, the evidence, the risk (even if low), and your pick. Items that share a call get the call once, then one bullet each, riskiest first. Never cut items to save words. Keep the turn read-only.
- **Source.** `pstack/skills/ketchup/SKILL.md:17-33` "Never cut items or shrink them to stay under a word count"; "When items share a call, write the call and your pick once, then give each item its own bullet, riskiest first".
- **Prevents.** A backlog of Gate Bs the user cannot triage from one message.
- **Verdict.** Adapt. This is the coordinator's "what's waiting on you" message: which ticket sessions are at Gate B, with a one-line risk each and the pick. The Gate B content itself stays in the ticket session (orch:225-240).

### H5. The operator's gates come first; a request to state the plan is not a go
- **Rule.** The autonomy grant covers only the queue's items. Items the operator names as theirs stop at merge-ready. A request to state the plan is not a go. The plan is handed back, and execution starts only on an explicit go.
- **Source.** `pb/autopilot-full.md:7` "A request to state the plan is not a go."; `pb/multi-phase-plan.md:7,34`.
- **Prevents.** Agents starting execution off a planning request.
- **Verdict.** As-is. It matches our optional Gate A (orch:162).

### H6. Stop at verified; hand landing to the operator
- **Rule.** Autopilot-stack stops when each PR is verified and green at its head, then hands the PRs to the operator. After handoff, nobody pushes without the operator's go. Every tick prompt names the no-merge rule, so each tick sees it.
- **Source.** `pb/autopilot-stack.md:5` "After the handoff, nobody pushes without the operator's go. Every loop tick prompt names this file, so each tick sees the no-merge rule."
- **Prevents.** Drift into merging during long autonomous runs.
- **Verdict.** As-is. This is the pstack playbook closest to our design. Our version: every ticket stops at Gate B. Landing is local, and push stays the user's call (orch:265). Autopilot-full (the owner merges) conflicts with Gate B and should not be used.

### H7. Turn-yielding checkpoints
- **Rule.** When feedback is required, point to the artifact in a concise message and yield. Stay idle across human turns, and loop again only when the user explicitly confirms.
- **Source.** `egm/docs/designs/architecture.md:173-175`; `egm/skills/egm-review-loop/SKILL.md:175-179` "The driver must remain idle across human turns".
- **Prevents.** Agents running ahead of an unanswered gate.
- **Verdict.** As-is, per ticket session. The coordinator does not idle, because it keeps other tickets moving (H2).

### H8. Always-pause list
- **Rule.** Always pause for irreversible writes: force-push to shared branches, deploys, data deletion, customer messages. Session overrides ("going to bed") keep reversible work going.
- **Source.** `pm/SKILL.md:84-88`.
- **Verdict.** As-is. Ours adds every commit (Gate B) and the merge into `<parent>` (orch:263).

---

## 7. Audit trail

### A1. One append-only decision log, with evidence pointers
- **Rule.** Use one TSV with one row per decision: `ts, phase, decision, why, evidence, result`. Evidence is a pointer (SHA, `file:line`, a path), never prose. The log is append-only, and a wrong call gets a superseding row. Log decision points, not every action.
- **Source.** `pstack/skills/show-me-your-work/SKILL.md:13-22,40,52` "Append-only. A wrong call gets a new row that supersedes it."; helper `scripts/log.sh` (sanitizes tabs and newlines, and prefixes formula-injection characters).
- **Prevents.** Unreviewable overnight runs.
- **Verdict.** Adapt. Our run files already carry a landing log. The coordinator's run file should keep an append-only decision table in this shape: ticket kicked off, dropped, replanned, landed (with SHA), patch-id carry, replacement session.

### A2. Multiple runs writing one log mark their stretch
- **Rule.** A pickup, replacement agent, or new chat starts a new run. Its first row has phase `start` and names the `ts` range of earlier rows it did not write, plus its own agent id.
- **Source.** `pstack/skills/show-me-your-work/SKILL.md:42`.
- **Prevents.** Confusion over which session made which decision after a handover.
- **Verdict.** Adapt. With S1 (one log per session), interleaving cannot happen. Use the `start` row only when a replacement session takes over a ticket's run file.

### A3. Audit the log against the transcript, then a cross-family review of the trail
- **Rule.** At the end, walk this run's rows against the transcript. Every row must map to a real action, its evidence must resolve, and missing forks get rows added. Then a reviewer from a different model family reads the trail and transcript and flags weak evidence, skipped verification, risky choices, and gaps. The reply ends with an "Attention" section that names the reviewer model.
- **Source.** `pstack/skills/show-me-your-work/SKILL.md:55-74` "Self-review is not a substitute."
- **Prevents.** A trail that tells a nicer story than what happened.
- **Verdict.** Adapt. In Claude Code the other family is codex. Hand the coordinator run file and the ticket run files to codex via `rc-codex`, read-only, for the Attention pass. `rc-retro` (orch:266) is the natural place for this.

### A4. Silent ticks still log
- **Rule.** Every audit tick logs a row naming the items reported, or `none`.
- **Source.** `pb/multi-phase-plan.md:42`.
- **Prevents.** Gaps in the record that hide a stalled supervisor.
- **Verdict.** As-is.

### A5. Reviewer status table in every report
- **Rule.** The report opens with a table giving each requested reviewer's status, `completed` or `not run`.
- **Source.** `egm/agents/synthesizer.md:49-53`.
- **Verdict.** As-is, as a ticket status table in the coordinator's run file and in the cross-ticket review report.

### A6. Plan as an evidence checklist, linted by a script
- **Rule.** The plan is a checklist: one box per unit, each naming its evidence, checked only when the evidence exists. A script lints the plan's structure, which encodes lessons as structure rather than more prose.
- **Source.** `pb/multi-phase-plan.md:3,24` "Check a box only when its evidence exists"; `:10` runs `pm/scripts/check-plan.mjs` (205 lines).
- **Prevents.** Plans that drift from the template. Boxes ticked on claims.
- **Verdict.** Adapt the idea. The script itself hardcodes pstack's PR/live-lane/perf sections (`check-plan.mjs:5-27`, e.g. "Ten lanes on … at the PR head"), so it is not reusable. A small check over our multi-ticket run file (every ticket has a state, every landed ticket has a SHA) would do the same job. This repo already has a check script (`bdbe1cb feat(check)`).

### A7. Re-read the playbook from trunk at every tick
- **Rule.** At program start and every tick, re-read the execution playbook (and the leaf skills it uses) from trunk, audit the operation against it, and fix drift in that tick.
- **Source.** `pb/multi-phase-plan.md:35-42`; `pb/autopilot-full.md:22` "because long runs drift and agents stall silently."
- **Prevents.** Drift from the protocol over a long run, and running stale instructions after a skill fix lands.
- **Verdict.** Adapt. Re-read the multi-ticket skill (and the relevant `rc-orchestrate` sections) at each coordinator wake.

---

## 8. Reuse verdicts

### Reusable nearly verbatim in Claude Code
pstack is MIT, so copying needs the copyright notice. EGM is Apache-2.0, so copying needs the license and a notice of changes.

- **The five principle skills** (`separate-before-serializing-shared-state`, `sequence-verifiable-units`, `never-block-on-the-human`, `guard-the-context-window`, `make-operations-idempotent`). Each is 12-22 lines of plain prose with no tool dependencies. Caveat: `never-block-on-the-human` must be scoped so it does not override Gate B. The best route is to quote the rules into our skill rather than vendoring the files.
- **`pb/orchestrate.md` Topology and Supervision bullets** (lines 9-23). These are almost harness-free. Remove the Cursor pieces: `environment: "cloud"` (maps to `isolation: "worktree"`, `pstack/docs/harness/claude-code.md:23`), the Project tracker, and PR/CI event subscriptions.
- **`pb/pause-safely.md` and `pb/session-pickup.md`.** Short, with only the transcript path to map (claude-code.md:56). Pause needs the wip-commit change (F5).
- **`ketchup`**. Works as a Gate B queue digest. It depends on `/bro` (voice only) and `/visualize` (optional).
- **`show-me-your-work`** with `scripts/log.sh`. It needs the transcript path mapping, plus a cross-family reviewer. In Claude Code the `Agent` tool cannot run a non-Claude family (claude-code.md:35 drops grok/gpt to the session model), so that reviewer must go through `rc-codex`.
- **EGM review-loop convergence rules** (`SKILL.md:151-173`) and **the not-run rule** (`:132-136`). Self-contained. We already took the not-run rule.
- **EGM synthesizer contract** (artifact on disk, one-message summary with counts and path). Reusable as the pattern for the cross-ticket review and for ticket-to-coordinator rollups.

### Reusable with real work
- **`swarm` and `arena`**. The shape rules are sound. They depend on `~/.cursor/rules/pstack-models.mdc` model roles, cloud VMs, and a different-family cross-judge. In Claude Code all of these degrade, and the family diversity disappears unless codex is wired in.
- **`pb/shipping.md` landing logic** (contiguous verified run, patch-id carry, leave the stack alone). Take the rules, not the text. Its `gh`/Origin/merge-queue mechanics do not apply to local merges.
- **`pm/scripts/worktree-audit.sh`**. Probably usable for cleanup after review. I did not read its body.

### Not worth reusing
- **`pb/autopilot-full.md` as a playbook.** The owner self-merges after a swarm verdict, which conflicts with Gate B. Harvest its individual rules (S4, S5, S10, F2, V10) instead.
- **`pb/multi-phase-plan.md` template and `check-plan.mjs`.** Built around PRs, ten live lanes per PR, perf gates, video review, and Cursor control skills (`control-ui`/`control-cli` from `cursor-team-kit`, not shipped in pstack). Far heavier than our ticket model.
- **`pb/babysit.md` and `scripts/watch-pr`.** GitHub/Origin PR babysitting with Bugbot. We have no PRs in the loop.
- **`automations/benny`.** Cursor Automations plus Slack. Claude Code has no equivalent (claude-code.md:60-64 says skip). Only the single-poster rule (S3) and fail-closed / don't-race gates (F9) are worth taking.
- **`poteto-mode` SKILL.md as a whole.** A style mode with Cursor model slugs and its own playbook router. Its Subagents section (92-102) is the valuable part, already catalogued (T*, V11, V12).
- **Most of EGM.** It orchestrates document review, not code execution across sessions. It has no worktrees, branches, landing, or multi-session coordination. The bootstrap orchestrator is a doc-generation partitioner.

---

## 9. Weak spots

### pstack
1. **Convention used as concurrency control, against its own principle.** "One babysitter per stack. Before starting, check nothing else is already on it" (`pb/babysit.md:9`) is a check-then-act convention. The principle it ships says "Instructions and conventions are not concurrency control" (`principle-separate…:9`).
2. **No cost budget.** Ten live lanes plus perf plus two or more audit lanes per PR (`pb/multi-phase-plan.md:13,65`), about ten workers per coordinator, and full swarms. Nothing caps tokens or spend. "Stuck-after runtime from past runs" (`pb/autopilot-full.md:12`) assumes a history store that nothing creates.
3. **Model diversity disappears in Claude Code.** Cross-family verification is a load-bearing rule (V1, A3, the arena judge). Yet the Claude Code harness map drops every non-Claude slug to the session model and only says so (`docs/harness/claude-code.md:35`). The independence property quietly fails.
4. **Heavy dependence on Cursor-only primitives.** Cloud VMs, Projects, `/loop`, PR/CI subscriptions, Automations, Bugbot, and `cursor-team-kit` control skills. The harness doc's answer for many of them is "Skipped in Claude Code" (claude-code.md:60), which removes the wake and supervision mechanism entirely.
5. **Internal tensions.** Session pickup says the trail "is authoritative … Resist the bias to re-derive it" (`:6-7`) and then "A passing prior self-report is not the proof" (`:9`). "Never block on the human" sits against review gates. Orchestrate says "Call no scripts, run no polling loops" (`:5`), while the babysit it delegates to runs `watch-pr` under `/loop`.
6. **Prose density.** The verification rule sentence is repeated in every block of the plan template (`pb/multi-phase-plan.md:13,28,96,100,113`). Playbook paragraphs carry many rules each (e.g. `pb/autopilot-full.md:19`). Reader load is high, and partial compliance is likely.
7. **PR-centric worldview.** Every ownership and landing rule is phrased in PRs, heads, CI, and forge state. There is no local, approval-gated variant, so everything must be translated.

### EGM
1. **Wrong domain for multi-ticket work.** It covers document review only, with no code execution, worktrees, branches, landing, or cross-session coordination.
2. **Expensive convergence.** Two consecutive clean rounds (`SKILL.md:165`), an optional A/B double spawn per reviewer (`synthesizer.md:39`), and up to 5 rounds. Each round also yields to the human (`SKILL.md:175-179`), which makes a run slow.
3. **LLM-only dedup.** The synthesizer normalizes and dedupes with no structural check. The stable ids are assigned by the root (`SKILL.md:129`), not by the synthesizer, so dedup quality across rounds is unverifiable.
4. **Unverified harness claims.** It says Claude Code nests subagents "Up to 3 levels by default" (`docs/harnesses.md:91`) and requires 2.1.271+ for `omitClaudeMd` (`docs/claude.md:8`). Both need checking before we rely on them.
5. **Ceremony.** Role-title enforcement for dashboards (`docs/designs/synthesizer.md:66-68`) and the Antigravity side-panel artifact protocol add little in Claude Code.
