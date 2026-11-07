# Multi-session orchestration audit (sidedoor ai-agent, 2026-10-31 → 2026-11-03)

Read-only reconstruction from transcripts in `~/.claude/projects/-Users-ricardocoelho-Code-sidedoor/`, the run files in `sidedoor/z-features/ai-agent/runs/`, `sidedoor/CLAUDE.md`, the progress memory file and `claude-skills/skills/rc-orchestrate/SKILL.md`.
Citation format: `<session prefix> <MM-DDThh:mm>` plus a short quote. **[T]** = the transcript shows it. **[I]** = my inference.

**Date correction.** The "11-02" coordinator `4228230a` started on **10-31 17:56**. The work ran in three bursts: 10-31 18:01–18:40 (assign, build to the gates), 11-01 13:05–16:41 (gates, manual checks, merges), and 11-02 09:46–10:12 (last merge, page refresh, new ticket 31). The file's mtime is 11-02.

## Cast

| Run | Coordinator | Worker session (name) | Ticket |
|---|---|---|---|
| A (10-31 → 11-02) | `4228230a` = sidedoor-39 [625c42], socket 30219 | `f9646d77` sidedoor-f8 | 28 eval language check |
| | | `a09afe80` sidedoor-9a | 29 seed coverage |
| | | `094a6555` sidedoor-23 | 25 split AgentConversationService |
| | | `4d6e48e6` sidedoor-ce | 15 full ops union |
| B (11-03, still in progress) | `60fa5a67` = sidedoor-83 [dbf287], socket 29252 | `5939529b` sidedoor-de | 26 paid-tier language mirroring |
| | | `d8c4a906` sidedoor-73 | 33 silent turn on stop |
| | | `dde7d843` sidedoor-39 [b651d9] (name reused from run A's coordinator) | 24 v0 docs close-out |

`d5cafdf3` (ticket 31, 11-02) is a single-session run with no cross-session traffic, apart from subagent hand-backs. It is out of scope, except that the run-A coordinator wrote its ticket.

Run B transcripts end with every worker at or near Gate B (`dde7d843 11:58`, `5939529b 12:13`, `d8c4a906 12:28`). No worker has reported back to sidedoor-83 yet, and nothing is merged. Everything I say about run B's merge phase is **[I]**.

---

## 1. The protocol that emerged

### Assignment
- **Run A [T].** The human named the tickets and how to split them ("lets go with 28, 29, 25, 15. I think they can be paralelized right?", `4228230a 10-31T18:01`). The coordinator read the 4 tickets, called ListAgents, and sent each newly started idle session one long brief (`4228230a 18:02:02–18:02:16`). Each brief held:
  - the ticket path and "claim it first";
  - the worktree path, the base branch and SHA (`ai-agent-v0` at bead2cb), and the docs base `ai-agent-13-docs-sweep` "NOT docs main";
  - "three other sessions are running … don't touch those";
  - the specific overlap with one named peer and what to do about it (28↔29 on `evals/agent/results/`; 25↔15 on `agent.service.ts`, "flag it at Gate A");
  - "merge only after Ricardo approves at Gate B … Don't push".

  It skipped the older sessions sidedoor-4c and claude-skills-1d on purpose: "they're older sessions that may still hold context you want" (`4228230a 18:02:27`).
- **All four assignments bounced [T].** `rc-orchestrate` still had `disable-model-invocation`, so each worker's Skill call failed ("Skill rc-orchestrate cannot be used with Skill tool due to disable-model-invocation", `f9646d77 18:02:31`). Each worker replied "nothing is locked", then waited. The human typed `/rc-orchestrate <ticket>` in all four windows between 18:07:01 and 18:07:17. The coordinator concluded: "Next time I'll give you these commands to type yourself rather than messaging the sessions" (`4228230a 18:02:44`).
- **Run B [T].** After 6d6f220 (11-02 16:02), the brief was shorter, and every worker invoked the skill itself within 4 seconds of the message (`5939529b 11:38:39 Skill rc-orchestrate`, `d8c4a906 11:38:39`, `dde7d843 11:38:47`). The human typed nothing to start them. Run B's brief dropped most of run A's setup detail. It kept "claim first", the worktree convention, "keep off X's file", "Ricardo answers the gates in your session directly", and "SendMessage sidedoor-83 … when done or blocked".

### Addressing
- **[T]** The coordinator addressed workers by name (`sidedoor-f8`). Every worker replied to the raw socket (`"to": "uds:/tmp/cc-socks/30219.sock"`), which it took from the `from=` attribute.
- **[I]** That was lucky and correct, because names are not stable: "sidedoor-39" is the run-A coordinator and also a run-B worker (`60fa5a67 11:38:21 ListAgents`: "sidedoor-39 [b651d9] … started 46s ago").

### Shared-resource arbitration
All of it was invented on the fly in run A, on 11-01, when the human asked the coordinator to "coordinate them to run their respective manual checks" (`4228230a 11-01T15:43`).

- **Manual-check slot.** One holder at a time of the shared Mongo (27017, same DB), ports 4000/3000, and one Chrome with Clerk cookies shared across localhost ports.
  - The order was 29 → 25 → 15, and 28 ran without the slot because it needed no servers.
  - Rules: wait for "GO"; on release, "stop both dev servers, sign out … close the tab … message me a one-line result".
  - A fix that takes long gives up the slot: "29 releasing to fix", and the worker is re-queued.
  - Ban `pnpm db:reset`: "It wipes the Mongo everyone shares, including Ricardo's local data" (`4228230a 15:44:08`).
  - Workers kept to the rules. For example: "Servers are stopped, Chrome is signed out and the tab is closed, so the slot is yours for 25" (`a09afe80 15:48:01`).
- **Merge slot.** Created at 15:45: "You hold the merge slot now. Nobody else merges into backend `ai-agent-v0` until you're done." The holder's sequence was fixed: commit → fetch → rebase onto the current tip → full checkup / docs build → merge (in the main checkout) → push (added at 15:54) → ticket done → remove worktree and branch. Then it messages the hashes and pushed range, which releases the slot.
  - The slot was granted strictly one at a time: 28 at 15:45, 25 at 16:16, 15 at 16:27, 29 at 16:31 (conditional on its re-check).
- **Push.** Allowed only inside the merge slot, with "Fetch first: if origin has moved, stop and tell me rather than force" (`4228230a 15:54`). Every push was a fast-forward with "Origin hadn't moved" (`f9646d77 15:54`, `094a6555 16:20`, `4d6e48e6 16:31`, `a09afe80 09:50`).
- **Rebase hand-off.** When a ticket landed, the coordinator broadcast the new tips and a "map for your rebase" to the next in line. For example, 25's file split went to 15: "AgentConversationService … now holds only start/continue; turn engine is agent-turn.service.ts …" (`4228230a 16:21:17`).
- **Feature page.** At first every worker refreshed it on its own (see §3). After 29 reported a regressing build, the coordinator banned worker refreshes: "I'll do one consolidated refresh from this session once 25, 29 and 15 have all merged" (`4228230a 16:19:53`). It did that refresh at `11-02T09:52`.
- **API spend.** The coordinator told 28 to skip `pnpm eval:smoke` "since it spends API credits" (`4228230a 15:44:29`). Live `pnpm eval` runs were "orchestrator only, unsandboxed, never an executor".
- **Run B [T].** None of the above was restated. There is no slot rule, no merge order, no push rule, and no feature-page ownership rule. Run B's workers each patched the page themselves (`dde7d843 11:40`, `5939529b 11:45`, `d8c4a906 12:09`).

### Status reporting
- **[T]** Workers sent a short report at each milestone: slot taken, slot released (pass/fail with details), committed, merged plus hashes, and pushed plus range. The coordinator turned each one into a short summary for the human, usually with the next action for the human. One example: "Type a yes in sidedoor-23 when you get a moment" (`4228230a 16:03`).
- **[T]** Run A's coordinator also pulled status itself, by reading ticket `**Status:**` lines and listing `worktrees/` with bash (`4228230a 18:07:24`, `15:43:28`).
- **Gap [T].** Run B's brief asks for a report only "when the ticket is done, or if you hit a blocker". Gate waits are not reported. sidedoor-83's last event is `11:44` ("none has reported back yet"), while 33 sat waiting on the human for 19 minutes (`d8c4a906 11:48:38 → 12:08:06`).

### Handoffs
- **[T]** Worker to coordinator to worker: "28 has landed … rebase onto it before your final full pnpm eval" (`4228230a 15:49:10`).
- **[T]** Taste items were collected for the human. Each final report had to list "UI-facing choice[s] whose look or wording is a matter of taste … with the page and the exact prompt". The coordinator merged these into one list (`4228230a 16:27:39`, `09:52:54`).

---

## 2. Where the human had to act in a specific window, and why

| # | What | Where / when | Why |
|---|---|---|---|
| 1 | Type `/rc-orchestrate <ticket>` | All 4 run-A workers, 10-31 18:07 | `disable-model-invocation` blocked the peer launch [T]. Fixed by 6d6f220; run B needed nothing. |
| 2 | Answer Gate A questions | 25: `18:19 ok`, then Q2 `11-01 13:05 ok to A`, plan `13:07 ok`. 15: `13:07 ok for Q1`, `13:08 ok`, `13:08 ok`. Run B 26: `11:44 yes q1`. 33: `11:45 ok for b`, `11:48 ok`, `12:08 ok` | By design, the gates are in the worker [T]. The grilling rule ("one at a time") means 2–3 separate visits per window. |
| 3 | Re-type commit approval already given to the coordinator | 28 `15:46 yes`, 25 `15:47 yes`, 15 `15:47 "yes its true approve"`, 29 `16:16 yes` (its Gate B) | The coordinator relayed "you have my permission to tell them to commit, merge and cleanup" (`4228230a 15:45:25`). Every worker refused the relay: "Our CLAUDE.md asks for your own approval … a message relayed from another session isn't that" (`f9646d77 15:46:04`). The source is `sidedoor/CLAUDE.md:55` plus the harness's peer-message guard [T]. |
| 4 | Re-type push approval | 28 `15:54 do it`, 25 `16:16 yes both`, 15 `16:15 "yes push approved"`, 29 docs push asked again at `16:17` and `16:28` | Same as #3 [T]. 29 even split it per branch: "your 'yes' covered only the backend push" (`a09afe80 16:17:21`). |
| 5 | Sign in to the app in Chrome | 25 `15:50 done`, 15 `16:15 signed in`. 29: no sign-in at all; the human didn't have nikki's or luis's passwords ("whats her password?", `a09afe80 16:41`) | Agents won't type credentials into Clerk's hosted sign-in [T] (`4d6e48e6 16:08:07`, `094a6555 15:49:02`). |
| 6 | Gate B change requests | 25 "reduce nesting" and 15 "/writing-for-agents on agent-prompt.ts … journeys.service.ts could use some refactor" (`4d6e48e6 15:53:28`) | The human reviews the code in the worker window [T]. The coordinator only learned of it second hand ("i told them some feedbacks", `4228230a 15:54:32`). |
| 7 | Decide whether to merge without the UI re-check | `a09afe80 11-02T09:46` "its ok ill check them myself later", then `09:50 ok` | The sign-in was not possible; see #5 [T]. |
| 8 | Status pings per window | "all good?" (`a09afe80 11-01T13:05`) | The human checked the worker directly, not the coordinator [T]. |

**Count [T].** In run A the human typed 26 messages in worker windows (28: 5, 29: 6, 25: 8, 15: 7) and 9 in the coordinator. About 11 of the 26 existed only because of #1, #3 or #4.

---

## 3. Failures and friction

1. **The skill invocation limit cost a full round trip [T].** Four briefs went out, four workers declined, and the human had to type four commands (see §1). The coordinator had not checked invocability first. Run B shows this is fixed.

2. **Relayed approvals are worthless by construction [T].** The coordinator collected a blanket approval and relayed it four times, and then again for push. Every worker re-asked in its own window. The coordinator predicted this ("Some sessions may still ask you to confirm in their own window", `4228230a 15:45:56`) but still spent eight messages on it.
   **[I]** A skill should not route approvals through the coordinator. It should list which windows need a "yes".

3. **Bursts of messages crossed each other [T].**
   - At 15:44 each of 25 and 15 got three messages in about 30 seconds: the slot order, the fix rules, and "drive Chrome yourself". A fourth followed at 15:45 (authorization) and a fifth at 15:54 (push). Each produced a worker acknowledgement and a re-ask to the human.
   - **Crossed messages.** The coordinator sent 15 "GO" at 15:57:00 while 15 was running the human's Gate B changes. It had to send a follow-up: "our messages crossed … run the manual checks after those changes land" (`4228230a 15:58:39`).
   - 28 got "Skip the optional pnpm eval:smoke unless Ricardo asks" after Ricardo had already asked for it in 28's window ("do it", `f9646d77 15:42:56`). Two principals sent conflicting instructions.

4. **The coordinator's briefs had gaps that caused rework [T].**
   - **Docs base.** 29's brief said "This is backend only". When 29 later needed a docs change, it based the docs worktree on docs `main` ("off docs main 80d78d8", `a09afe80 15:57:09`). The coordinator corrected it (`4228230a 15:57:17`), and 29 had to move it with `reset --keep`.
   - **Prompt-file overlap.** The run-A briefs did not foresee that 29's prompt fix and 15 would both edit `agent-prompt.ts`. The coordinator noticed only at 15:49:31 ("29's 'spouse' fix touches the prompt too"). The worker covered it: 15 limited its rewrite to its own block "because ticket 29 changes other blocks in the same file" (`4d6e48e6 16:04:37`).
   - **Docs overlap in run B [I, from T].** Run B's briefs call 24 "docs only" and 33 and 26 "unrelated areas". But 26 now also edits `sidedoor-docs/docs/backend-api/agent.md` and `ai-voice-guide.md` on a `worktrees/26/docs` branch off `ai-agent-13-docs-sweep` (`5939529b 12:00:50`). 33 edits the same `agent.md` (`d8c4a906 12:18:46`). 24 edits five other docs pages on the same parent branch. Three branches will merge into one docs branch with no merge-slot rule. The `agent.md` hunks are in different sections, so a conflict is unlikely but possible.

5. **Parallel test load produced false BASE failures in every run-A worker and one run-B worker [T].**
   - 28: "223 failing tests across 28 suites" (`f9646d77 18:15`).
   - 25: "581 failures across 20 slow suites … load average around 20–25" (`094a6555 18:18`).
   - 29: 39 suites (`a09afe80 18:23`).
   - 15: 106 failures (`4d6e48e6`, run file line 29).
   - 33: two suites "timed out starting in-memory Mongo, probably load from the parallel sessions" (`d8c4a906 11:43:48`).

   Each worker re-ran the suites serially, at a cost of 3–5 minutes plus diagnosis, and 25 hit a zsh quoting slip along the way. 25's retro traced the cause: `MongoMemoryServer.create` runs with the default 10 s `launchTimeout` (`094a6555 16:42`).

6. **The feature-page artifact was contested.**
   - **Run A [T].**
     - 28 published at 18:14–18:15 after two refusals.
     - 29 tried at 18:15 and was refused: "Another session republished the page after I read it".
     - 15 was refused at 18:23 and skipped.
     - 25's haiku build "came back with no ticket mapping" and was held back (`094a6555 16:19:59`).
     - 29's build "dropped the ticket-to-slice mapping … publishing it would have regressed the page" (`a09afe80 16:19:47`).
     - 28 published a hand-mapped full rebuild by haiku at 15:51 ("tickets were mapped to slices by hand").
     - The coordinator then centralised the refresh, and its own refresh at 09:52 also took three publish calls.
   - **Run B [T].** This was after b4065ed "status refresh patch", which the skill now describes as letting "concurrent sessions … patch the same page instead of rebuilding over each other". Each of the three workers still needed read → refused ("hadn't viewed the live version") → refused ("identical content") → accepted, so every refresh costs three publish calls (`dde7d843 11:40:37–11:40:53`, `d8c4a906 12:08:59–12:09:19`). Nothing was clobbered, so the patch design works. The retries are the friction.

7. **Concurrent writes to the shared memory file [T].** The coordinator (`4228230a 15:49:23`) and worker 28 (`f9646d77 15:49:16`) both appended a "Ticket 28 DONE" line to `memory/project_ai_agent_ticket_progress.md`, 7 seconds apart. The file now has two entries, at lines 38 and 39. 28 later updated only its own line to "PUSHED", so line 39 still says "NOT pushed". The two lines contradict each other.

8. **Side effects on the human's data in the shared Mongo [T].** 15's manual checks edited Ricardo's real local journey: "Your journey ('Journey - May 27, 2026') has been edited by these checks. Removed: …" (`4d6e48e6 16:28:06`). 29's seeds went into the shared DB too. The coordinator prevented a `db:reset`. 29's own guide still told the reader to run `pnpm db:reset`, and 29 flagged that to the human afterwards (`a09afe80 09:47:47`).

9. **A slot held while waiting on a sign-in that never came [T].** 29 took the re-check slot at 16:27 and opened the sign-in page at 16:28. The human had no password (16:41) and returned at 09:46 the next day. The coordinator had scheduled the check around "Ricardo signing in" without knowing the credentials were missing. It had already flagged that the ticket was fine to merge without it (`4228230a 09:47:49`). No one else needed the slot overnight, so the hold cost nothing. **[I]** It would block a longer queue.

10. **Wasted eval spend from ordering [T].** 29 started its "final" full `pnpm eval` before the review of its fix round. The review found a Major issue, so 29 killed the eval part way (`a09afe80 15:58:04` TaskStop on `pnpm eval`), reset the result files, and later ran it again (`16:03`, $0.43).

11. **Context compaction in workers, not in the coordinator [T].** 29 compacted at `11-01T14:00` and 15 at `11-01T14:54`. Their peak contexts were about 238k and 308k tokens; 25 peaked at about 313k without compacting. The run-A coordinator peaked at 156k and never compacted (see §4).

12. **Stale state in coordinator reads [T, minor].** At `18:07:28` the coordinator said "15 hasn't claimed yet". 15 claimed at 18:07:37: a file poll ran 13 seconds before the worker's write.

13. **No lost or held messages [T].** All 231 inbound peer messages arrived with `from-mode="prompting"`. Every SendMessage returned `success:true … not yet read`. No "[Cross-session delivery notice]" hold or refusal appears in any of the nine transcripts.

---

## 4. What the coordinator spent its context and time on, and whether the parallelism decision was right

**Context [T].** Coordinator `4228230a` grew from 40k (frontier question) to 70k (after assignment), 123k (after the last merge), then 140k (page refresh) and 149k (ticket-31 diagnosis). So coordinating four tickets cost about 80k tokens over two days, across 39 sent and 28 received messages. Each received message carries about 120 tokens of anti-laundering boilerplate.

**Time [T].** Most coordinator turns took 3–30 seconds. The longest:
- the 15:44 slot setup, at 90 s;
- the ticket-31 investigation, at 82 s;
- the consolidated page refresh, at 84 s.

It did no polling and no idle loops: between 10-31 18:10 and 11-01 15:43 it had zero events. **[I]** The coordinator was not the bottleneck. It was idle while every worker waited on the human.

**What it actually did, by value [T]:**
- predicted conflicts and set the merge order (28 first, because 26, 27 and 29's final eval depend on it);
- invented and ran the two slots;
- stopped a `db:reset` of the shared database;
- corrected 29's docs base;
- gave 15 the rebase map from 25's split;
- caught a risky approval. It told the human to question 29's `unread-notifications` failure before approving: "nobody has shown this case fails without 29's prompt too" (`4228230a 16:12:19`);
- recommended running 26 and 27 one after the other: "Both edit the same file … second to merge would conflict on the result files" (`4228230a 15:49:31`);
- merged the taste lists, and wrote ticket 31 from the human's feedback.

**Was running 28, 29, 25 and 15 in parallel right? Yes [T].**
- 28's rebase was a no-op.
- 25 rebased onto 28: "dry run of the merge shows no conflicts" (`094a6555 16:16:27`).
- 15 rebased onto 25: "no conflicts, and agent.service.ts was never touched" (`4d6e48e6 16:31:42`).
- 29 fast-forwarded onto 28, had "No file overlap with 25", and on 15 "Git merged the shared prompt file cleanly" (`a09afe80 16:32:27`).

There were zero merge conflicts. The one dependency (29's final eval after 28) cost 29 nothing real: 29 finished its build by 10-31 18:39 and then waited on 28. **[I]** 28 was waiting on the human's Gate B, so the dependency was dominated by human latency, not by the parallelism.

**Run B's split (26, 33 and 24 in parallel, then 27, then 17) [I].** The code split is sound: the backend files don't overlap. The "24 is docs only, stay in sidedoor-docs" framing misses that 26 and 33 also produce docs commits on the same docs branch (§3.4). No merge or push protocol has been given yet.

---

## 5. Costs (wall time per ticket)

Active time is time when the agent worked, not counting waits on the human or a slot. All figures are from transcript timestamps [T]; the splits between categories are approximate.

| Ticket | Launch → done | Active agent time | Waiting on human | Waiting on slot or peer |
|---|---|---|---|---|
| 28 | 10-31 18:07 → 11-01 15:55 (≈21.8 h) | ≈0.5 h (Gate B ready 18:28) | ≈21.2 h (Gate B, overnight) | 0 |
| 25 | 18:07 → 11-01 16:21 (≈22.2 h) | ≈1.3 h | ≈19 h at Gate A Q2 (18:19 → 13:05); ≈2.3 h at Gate B (13:24 → 15:47) | 4 min for the check slot (15:44 → 15:48); 0 for the merge slot |
| 15 | 18:07 → 11-01 16:31 (≈22.4 h) | ≈2.5 h | ≈18.7 h at Gate A (18:21 → 13:07); ≈1.8 h at Gate B (14:00 → 15:47); 7 min for the sign-in | about 0 for the check slot (it was busy with Gate B changes); 0 for the merge slot |
| 29 | 18:07 → 11-02 09:51 (≈39.7 h) | ≈1.5 h | ≈17 h at the sign-in and re-check (16:28 → 09:47) | ≈21 h waiting on 28's merge (18:39 → 15:49), itself waiting on the human; ≈15 min for the re-check slot |
| 24 (B) | 11:38 → Gate B 11:55 | 17 min | open | – |
| 26 (B) | 11:38 → Gate B 12:10 | ≈29 min | 3 min at Gate A | – |
| 33 (B) | 11:38 → ≈12:28, pre-Gate B | ≈27 min | ≈24 min across 3 gate prompts (19.5 min for the final plan "ok") | – |

**[I]** Slot contention was negligible: minutes at most. Almost all elapsed time was human latency at the per-window gates, sign-ins and approvals. Even with the human present (run B), the human's attention switching between three windows added about 20 minutes to 33.

Live model spend on run A was small: 28 smoke $0.04; 29 $0.07 plus $0.43 plus one aborted run; 15 about $0.90 plus $0.75 in prompt checks. Run B 26 was about $2.56 of a $4 cap.

---

## 6. What worked well and should be kept as rules

1. **Brief each worker about one named peer and one action [T].** The useful overlap note names the peer, the file and the action ("Whichever of you merges second rebases… flag it at Gate A"). It worked, and the workers acted on it.
2. **One merge slot per target branch, with a fixed sequence [T].** The sequence is fetch → rebase onto the current tip → full gate → merge → push only if origin hasn't moved, never force → report hashes and range → release. It gave zero conflicts, zero forced pushes and four clean pushes.
3. **One holder at a time for anything stateful and shared [T].** That covers Mongo, ports, Chrome and the Clerk session. Release means stop the servers, sign out, close the tab and restore `.env`. "Releasing to fix" re-queues the worker. Workers kept to it without exception.
4. **Ban destructive shared-state commands up front [T].** The `db:reset` ban prevented the obvious disaster.
5. **On landing, broadcast the new tips and a rebase map to the next in line [T].** The map from 25 to 15 made 15's rebase trivial.
6. **One writer for shared summaries [T, I].** One session owns the feature page and the progress memory, or every writer must patch. Run A's page race and the duplicated memory entry are both multi-writer problems.
7. **Workers report on milestones only, in short structured lines [T].** Slot taken or released, committed, merged with hashes, pushed with range, plus a "UI taste" list. This kept the coordinator at about 80k tokens for four tickets.
8. **Reply to the socket, not the name [T].** Names are reused across days.
9. **The coordinator should flag its own uncertainty instead of guessing [T].** Run B's brief to 24 said "check how that branch relates to … b386359 before you build on it", and the worker resolved it in 6 seconds (`dde7d843 11:39:06`).
10. **Order the queue so the human is needed in one sitting [T].** "Doing them back to back means you only have to be there once" (`4228230a 16:08:13`).

## Implications for a skill [I]

- **Approvals stay in the worker windows.** Have the coordinator output a "windows waiting on you" checklist (window, question, suggested answer), not relay approvals. Or let the human type one scoped standing approval per worker at launch, which the worker records in its run file.
- **Check that the skill is model-invocable before messaging.** Otherwise print the commands for the human to type.
- **Make the protocol part of the first brief, not a later add-on.** That covers the slot rules, merge order, push policy, page and memory ownership, and the shared-DB rules. Run B shows the rules are lost when nobody restates them.
- **Predict overlap per repo, docs included.** Ask each worker at Gate A for its planned touch-list across repos, and re-check overlap when a worker adds a repo mid-run.
- **Report gate waits.** Each worker should ping "waiting on Ricardo at Gate A/B" so the coordinator can tell the human where to go. Alternatively, the coordinator reads `runs/<slug>.md` and the ticket Status lines instead of waiting for messages.
- **Treat sign-ins as a human-scheduled resource.** Check that credentials exist before booking the slot, and don't hold the slot when the human is away.
- **Pre-empt the test load.** Before parallel BASE runs, use a raised Mongo `launchTimeout` or `--maxWorkers=2`, or stagger the runs.
