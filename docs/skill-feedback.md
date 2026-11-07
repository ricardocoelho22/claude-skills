# Skill feedback

Anonymised notes from retros and runs about the skills in this repo. One entry per finding: the skill, what happened,
the suggested change. Entries are in chronological order. Product, file and ticket details are removed on purpose.

## 2026-10-15 — retro of an orchestrate run (backend + frontend ticket)

### to-tickets (or to-spec): check every failure rule against the code that receives it

- **What happened:** a ticket and its spec said "if one optional step fails, send the payload without that part (the
  rest stays)". The receiving backend validator rejects a payload without that part, so the rule would
  also have dropped the rest of the payload. The orchestrator found it only while spot-checking the recon;
  it cost a Gate A stop and edits to the spec, the ticket and a design record.
- **Suggested change:** when a ticket states a fallback or failure rule, it names the function that accepts the
  resulting payload and quotes that function's check. A failure path is a branch; a branch the receiving code
  rejects is a spec bug, cheaper to find while cutting tickets than at Gate A.

### orchestrate, step 4 (manual checks): pass facts in the brief

- **What happened:** the manual-checks agent (Haiku) wrote two false claims into its guide: "the over-cap path has no
  test" (a test covers it) and "merge tickets X and Y first" (the branch already held them). The orchestrator
  corrected both by hand. A memory note about subagents inventing facts describes the same pattern.
- **Suggested change:** the step-4 brief carries the ticket's test names (from the diff) and the branch's base and
  what it already contains, and tells the agent to state coverage only from that list. Or run the step on Sonnet
  when the guide states what the tests cover.

### feature-artifact, Build and publish steps 4-5: unread `data.json` and the refused-publish rule

- **What happened (step 4):** the first refresh publish of the run was refused although the orchestrator had read
  the page URL: the publish also checks each published file, and `data.json` had not been read
  (`action: "read", path: "data.json"`). One extra read and one extra publish.
- **What happened (step 5):** a later refresh was refused because another ticket's session had published in between.
  The live `data.json` showed one ticket in-progress and another done; the new build showed both done. Step 5 says
  "different states -> rebuild from step 1". The orchestrator did not rebuild: the build was made after the other
  publish and already held every live state, so it published it unchanged (the tool accepts that on the second try).
  This is a deviation from the skill as written.
- **Suggested change:**
  - Step 4: on a refresh, read the page URL and its `data.json` path before the first publish of the run.
  - Step 5: add a third case — the build's states include every live state (the build is newer) -> publish again
    unchanged; rebuild only when the live version shows a state the build lacks.

## 2026-10-20 — retro of an orchestrate run (backend ticket)

### orchestrate, Phase 0 "Open the run file": create the run dir too

- **What happened:** the `mkdir` of the run directory sat in a call the user rejected. The two BASE suites then ran in
  the background with their logs redirected into the missing dir. Both failed to write, yet the job reported exit 0,
  because the command's last step (`grep ... | tail`) succeeded. One full re-run of both suites (~12 min).
- **Suggested change:** "Open the run file" says to create the run dir in the same step as the run file. The
  BASE-failures step says a background suite command ends on the test runner's own exit code (or prints it), never
  on a trailing `grep`/`tail`.

### orchestrate, Phase 0 "Record BASE failures": reuse a BASE run of the same commit

- **What happened:** the backend service's full suite (~12 min) ran at BASE and again at Finish. All tickets of one
  feature are cut from the same parent commit, so each next ticket re-runs the suite for the same known failures.
- **Suggested change:** keep the BASE failure list per repo commit (a cache file named by sha and suite) and reuse it
  when a later run pins the same BASE; run the suite only on a cache miss.

### feature-artifact, Build and publish step 2: one deterministic doc id, and drop stale published docs

- **What happened:** two delegated builds in one session named the same guides differently. A publish keeps every
  published file it does not list, so the artifact now holds both sets, and the stale set grows with each refresh.
- **Suggested change:** step 2 states one id rule the builder follows (one pattern for guides, the source-file stem
  for experiments and related docs). Step 4 lists the artifact's published doc paths (`action: "list", scope:
  "files"`) and passes `null` for each one the new build lacks.

## 2026-10-21 — retro of an orchestrate run (backend ticket)

### feature-artifact, Build and publish steps 2 and 4: the two entries above recur (third run)

- **What happened:** 2 of 3 refresh publishes were refused. The first: the orchestrator read only
  `action: "read", path: "data.json"`, and a read with `path` does not count as reading the page. The second: another
  session's build had switched every doc id to a long form; the run's build used the short ids, so publishing it broke
  the long-id links, and the long-id files stay on the artifact.
- **Suggested change:** apply the two entries above ("unread `data.json`...", "one deterministic doc id..."). Make the
  doc-id rule a script the builder runs, not a choice the Haiku builder makes. Step 4 adds: read the page itself (no
  `path`) AND its `data.json` before the first publish of a run.

### orchestrate, Finish "Merge" and "Clean up": the main checkout may be on another branch

- **What happened:** the main checkout was on an unrelated branch. `git -C <origin> switch <parent>` would have moved
  it away from the user's work, so the run used `git fetch . <slug>:<parent>` (fast-forward only, no switch). Then
  `git branch -d <slug>` refused ("not fully merged"): `-d` compares against HEAD, not the parent. The user had to
  approve `-D`.
- **Suggested change:** Merge: when `<parent>` is an ancestor of `<slug>`, fast-forward with
  `git -C <origin> fetch . <slug>:<parent>`; switch the checkout only for a real merge, and ask first when the
  checkout is on another branch. Clean up: confirm `git merge-base --is-ancestor <slug> <parent>`, then
  `git branch -D <slug>`.

### orchestrate, Phase 0 "Backend check": run the probe from the repo, and name the trap

- **What happened:** the probe command has no `cd <repo>`; run from a non-git workspace dir it failed on "Not inside a
  trusted directory". The second probe failed on "failed to load AWS credentials", which the repo's local-dev traps
  file already documents; the orchestrator did not grep that file, so the run file does not name the trap.
- **Suggested change:** the probe starts with `cd <repo> &&`, like every codex call. A failed probe: grep the traps
  file for the error text and write the trap on the run file's Backend line.

### orchestrate, Phase 0 "Record BASE failures": the BASE suite shared the worktree with the executors

- **What happened:** with no reusable BASE list, the backend suite (21 min, 11 min when alone) ran in the background
  while the first executors edited the same worktree. The result held only because pytest imports app modules at
  collection time; a lazy import would have mixed BASE and new code.
- **Suggested change:** extends "reuse a BASE run of the same commit" above. On a cache miss, run the BASE suite in a
  detached checkout of BASE (`git worktree add --detach <tmp> <BASE>` plus the venv clone), or start the first
  executor only after collection ends.

## 2026-10-21 — retro of an orchestrate run (backend + frontend ticket)

### orchestrate: step 3 (Fix) and Gate B changes verify only the ticket's test files

- **What happened:** review fix F1 changed shared runtime code. The fix was verified with the ticket's test files
  only. It broke an unrelated wiring test (a turn with `message=None` raised AttributeError). Only the Finish full
  suite found it, after the merge into the parent, which cost a post-merge follow-up commit.
- **Suggested change:** in step 3 and after each Gate B change, also run the tests of every module the change touched
  (grep the test tree for imports of each changed production module), not only the ticket's test files. That list is
  cheap (seconds); the full suite is not (15-21 min).

### orchestrate: re-read the ticket file before Gate B

- **What happened:** a parallel session appended a requirement to this ticket mid-run ("the cap must count queued
  items"). The orchestrator had read the ticket only in Phase 0; the Spec reviewer found the note.
- **Suggested change:** before the Gate B report, diff the ticket file against its Phase 0 copy (save one in the run
  dir) and list new comments in the report.

### orchestrate: new browser tests run once at 1a/1b verify

- **What happened:** a test asserted the order of two parallel requests. It passed in its cycle and failed 2 of 3 runs
  later; found only by the orchestrator's triple run after the trim. The cycle was already at the top rung, so no
  step-up existed and the fix went through Gate B.
- **Suggested change:** at 1b verify, run each new frontend browser test file three times (or with a repeat option),
  so a flaky new test is a cycle rejection, not a Gate B item.

### feature-artifact: concurrent sessions refresh the same page

- **What happened:** two of three publishes this run were refused because another session had published in between.
  Each needed a read, a manual `builtAt` comparison and a re-send.
- **Suggested change:** the delegated build returns its `builtAt`; the publish step compares it with the live
  `data.json` `builtAt` and re-sends unchanged when ours is newer, as one documented step.

## 2026-10-21 — retro of an orchestrate run (frontend ticket)

### orchestrate, steps 1a and 1b verify: lint the call's delta, not only at the end

- **What happened:** two executor claims were false, and only lint could have caught them early. (1) A test-writer said
  it imported a constant, but did not. The test was red with a KeyError (an assertion's left side runs first), so the
  red looked like a behaviour failure. The NameError appeared only after the next call, and cost a resume. (2) An
  implementer reported "eslint clean", but a component had two native `<img>` tags that a repo lint rule rejects. The
  fix round found them.
- **Suggested change:** at 1a and 1b verify, run the repo's changed-files lint over the call's delta (the repo's lint
  helper against the checkpoint tree, or pylint/flake8 + eslint on the delta files). An undefined name (F821/E0602)
  or a lint error makes the return a rejection. Read each red test's error type, not only the count.

### impl-tdd (test-writer mode): the orchestrator gives the BASE count; no git stash

- **What happened:** a test-writer ran a bare `git stash` / `git stash pop` in the worktree to count a test file's
  results before its edit. The stash stack is shared by every worktree and session. The tree came back intact this
  time.
- **Suggested change:** the role file says that BASE counts come from the brief or from the checkpoint tree
  (`git restore --source=<tree> -- <file>` into a scratch copy), and that the executor uses only the worktree's own
  state. The orchestrator puts the per-file BASE counts of every test file the cycle edits into the brief.

### orchestrate, Phase 0 "Write the plan" -> Risks: name the sibling tests that pin a contract the ticket changes

- **What happened:** the ticket changed a composer function's output from `{ id }` to `{ id, name }`. A sibling ticket,
  built in parallel on the same base, added a test that pins `[{ id }]`. The break showed only on the merged tree
  (2 red tests). The fix was one line in the merge commit.
- **Suggested change:** when the plan changes a shape that parallel sibling tickets use, Risks names that shape.
  Before the merge, grep the parent branch's diff since BASE for tests that pin the shape. Recurring entries also
  applied to this run: re-read the ticket before Gate B, concurrent page refreshes (2 refusals), and cleanup with the
  main checkout on another branch.

### orchestrate, Finish step 1 (Merge): the parent lives in a worktree that other sessions also merge into

- **What happened:** the parent branch is checked out in its own worktree, and several sessions merge into it. A clean
  `status` check passed. Seconds later, another session started its merge there. Git refused this run's merge only
  because `MERGE_HEAD` existed. The skill says `git -C <origin> switch <parent>`, which names neither case.
- **Suggested change:** Merge: when `<parent>` is checked out in a worktree (`git worktree list`), merge there
  through the worktree helper script's merge command, never by a switch. The script now refuses while a merge, rebase
  or cherry-pick is in progress there, takes a per-worktree lock, and merges with `--no-verify`.
- **Also (Finish, BASE failures):** the helper script has a command that runs the full backend suite, writes
  normalised failure ids and prints SAME or the NEW failures (exit 1). Use it for the BASE run, the Finish run and
  the post-merge run instead of hand-written grep/diff pipelines.

### orchestrate, Finish step 1: `/resolving-merge-conflicts` does not exist

- **What happened:** the merge had a test-file conflict. The Skill tool answered "Unknown skill:
  resolving-merge-conflicts". The orchestrator resolved the conflict by hand (both sides added tests and imports).
- **Suggested change:** point at a skill that exists, or put the rule in the step itself: "resolve; when both sides
  add, keep both; run the touched test files and lint; commit the merge with `--no-verify`".

### feature-artifact step 4: seen again, the other way round

- **What happened:** the orchestrator read the `data.json` path but not the page, and the first publish was refused
  ("You hadn't viewed the live version"). The second publish was refused as "identical content resent". The third
  publish (identical) went through. A refresh must read both the page URL and `data.json` before its first publish.

## 2026-10-21 — retro of an orchestrate run (rename ticket)

### orchestrate, Phase 0 (Record BASE failures): the BASE run shared the tree with the first executor

- **Done 2026-10-21:** the helper script's suite command now has a guard (exit 2, `TREE CHANGED DURING RUN`). The
  skill change is still open.
- **What happened:** the BASE suite ran in the background in the run worktree, and the implementer started in the
  same tree. The suite runs in place, so the BASE list would have mixed old and new code. The orchestrator stopped it
  and re-ran BASE on the clean parent worktree at the same commit (12 min lost).
- **Suggested change:** "Record BASE failures" finishes before the first executor checkpoint, or runs on another
  clean tree at BASE (the parent worktree when it is at BASE). Script guard: the suite command compares the tree
  before and after and exits 2 when they differ.

### feature-artifact step 4: seen again

- **What happened:** read `data.json` only -> refused; identical resend -> refused; third publish -> published. Two
  extra publishes of a ~57-file manifest. The entries above are still unapplied.

### orchestrate, Phase 0 (Backend check): the probe's error is not kept

- **What happened:** the probe ran with output to `/dev/null` and exited 1. Its stderr held the text of a trap the
  repo's traps file already documents ("failed to load AWS credentials"); the run did not see it.
- **Suggested change:** write the probe's stderr to a file in the run dir; on a non-zero exit, grep the traps file
  for its last error line and record the trap with the backend.

### orchestrate, step 1b and *Writing a brief*: the implementer's verify list lacks the lint gate

- **What happened:** the brief named a raw pylint command (wrong rcfile; the package's CLAUDE.md corrected it) and not
  the repo's changed-files lint script. The lint gate then failed on a renamed section divider after the return,
  which cost one fixer round.
- **Suggested change:** the plan's lint command goes into every implementer and fixer verify list.

### orchestrate: no-behaviour tickets (a rename) run the full ceremony

- **What happened:** the ticket was a pure rename. Step 1a (red tests) and step 5 (trim) had nothing to do and were
  logged as deviations; the review fixer ran at rung 4 (Sonnet, high) for three cosmetic edits.
- **Suggested change:** a cycle the plan marks `no-behaviour` skips 1a and 5, uses the existing suite (SAME as BASE)
  as its acceptance, and its fixer starts at the cycle's rung instead of rung 4.

### feature-artifact step 5: two runs refresh in parallel

- **What happened:** two tickets refreshed the page minutes apart. The live version (built 18:03) showed two states
  in-progress; this run's build (18:43) matched the files on disk (resolved / done). Step 5's "a second refusal goes
  to the user" stopped the run for a user round, then an identical resend was refused, then the third publish went
  through.
- **Suggested change:** when the build's `builtAt` is later than the live `builtAt` and every state difference moves
  toward the files on disk, the refusal counts as the read: publish again without asking.

### orchestrate, *Writing a brief*: local ticket numbers leak from the brief into test names

- **What happened:** the briefs said "cycle 1 / ticket N"; the test-writers named 6 describe blocks after the ticket.
  The lint helper flagged them only at review time; the fixer renamed them.
- **Suggested change:** the brief template says "test names describe behaviour, with no ticket numbers", and every
  executor's verify list runs the changed-files lint against BASE.

### orchestrate, *Executors* (Checkpoint): use the script

- **What happened:** the three-command checkpoint snippet plus a run-file heredoc ran 8 times in one run.
- **Suggested change:** where a worktree helper script exists, the checkpoint is one script command (added
  2026-10-22; prints the tree hash).

## 2026-10-22 — retro of two orchestrate runs (frontend tickets)

### orchestrate, *Finish* step 1 (merge): the conflict skill does not exist

- **What happened:** Finish says "On a conflict, invoke `/resolving-merge-conflicts`". No such skill is installed
  ("Unknown skill"). The merge had 4 conflicted files; the orchestrator improvised a fixer brief.
- **Suggested change:** point Finish at the helper script's merge command and state the procedure inline (or create
  the skill): keep both sides of add/add test hunks; drop a test only when a plan decision replaced its behaviour;
  re-apply the plan's type/contract decisions over the parent's newer code; run the full suite on the merged tree;
  commit with `--no-verify`.

### orchestrate, *Write the plan* + step 1b: name the tests a contract change breaks

- **What happened:** two implementers blocked. Plan decisions changed a contract (the send payload gained a field;
  recall returned the whole queued message), which broke existing tests that pinned the old shape. The briefs said
  "do not edit tests", so each block cost a round trip.
- **Suggested change:** when a plan decision changes a contract, the plan lists the existing tests that pin the old
  contract, and the implementer brief allows exactly those assertion edits.

### orchestrate, step 2 (review triage): a deferral needs a live owner

- **What happened:** ticket A deferred an item to ticket B; B's review deferred it back to A (already resolved). A
  third ticket left "whichever of the two merges second wires it". Nobody owned either; they surfaced only from
  memory at merge time, and became a new ticket.
- **Suggested change:** before deferring to another ticket, read that ticket's status and notes. A resolved target,
  or a target that deferred the same item back, means: cut a new ticket instead. In Finish step 1, grep the
  parent's open/resolved ticket notes for merge-time obligations ("merges second") and surface them before the merge.

### feature-artifact, *Build and publish* step 5: say how a refused identical resend ends

- **What happened:** every refresh in these runs took 3 publish calls (~60-file lists each): refused (live version
  newer), resent unchanged -> refused ("identical content"), sent a third time -> published.
- **Suggested change:** step 5 states the sequence: after the `data.json` comparison shows the build covers the live
  version, the next send is refused as identical once; send it once more unchanged and it goes through. That saves
  the guesswork, not the calls.

## 2026-10-23 — retro of an orchestrate run (backend ticket on an LLM gate)

### orchestrate, step 2 (review): the Standards brief names writing-for-agents for model-facing text

- **What happened:** the orchestrator wrote a judge rule line into the implementer brief. It ended on a negation and
  did not reuse the surrounding manifest's words. Both reviewers passed it; the user caught it at Gate B.
- **Suggested change:** when the diff adds text a model reads (prompt constants, rule lines, knowledge-base prose),
  the Standards reviewer brief says: "judge that text against the writing-for-agents skill". The orchestrator drafts
  such text with the skill loaded before it goes into a brief.

### orchestrate, *Write the plan*: a change to what an LLM judge reads gets an off-target A/B before Gate B

- **What happened:** the plan tested only the target case. The user had to ask for the inverse check. It found two
  shifts on requests unrelated to the change, and that the new rule line was not needed. None of it was in the
  Gate B report.
- **Suggested change:** when a ticket changes a judge's or gate's input or wording, the plan adds an A/B step after
  review: the target case plus off-target cases (real referent, unclear target, cut-off qualifier, off-screen how-to,
  other entity), with and without the change, n>=3, using the workspace's A/B script. Its result goes in the Gate B
  report next to the tests.

## 2026-10-24 — retro of an orchestrate run (frontend + backend ticket)

### orchestrate, *Refresh the page*: say which `read` counts before the first publish

- **What happened:** the first publish of the run was refused ("You hadn't viewed the live version"). The
  orchestrator had read the artifact with `path: data.json`; a read of a published file does not count as viewing the
  page.
- **Suggested change:** "On a refresh, your first publish of the run needs a `read` of the page URL with no `path`
  first." (Pairs with the feature-artifact note on the refused identical resend.)

### orchestrate / codex, Phase 0 backend check: codex has no cloud credentials in this workspace

- **What happened:** the probe exited 1 with "failed to load AWS credentials: the credentials provider was not
  properly configured" (codex reaches its model through a cloud provider here). The user said "codex is off, use
  claude" for earlier runs; this run hit the same failure, so every run since mid-October is Claude-only.
- **Suggested change:** either (a) the codex wrapper script exports the shared-credentials-file variable when the
  workspace's token refresh loop has written temp credentials, or (b) orchestrate reads a workspace setting (for
  example `ORCHESTRATE_BACKEND=claude` in the environment) and skips the probe. The user picks which.

## 2026-10-26 — retro of an orchestrate run (backend + frontend ticket)

### feature-artifact, *Delegated build* on a refresh: start from the live `data.json`

- **What happened:** both refreshes in the run rebuilt `data.json` from scratch with Haiku. The build rewrote the
  hand-curated decision lines (24 entries, different wording) and renamed doc ids. Twice, the orchestrator read the
  live `data.json` and patched only the changed ticket status. Also, after an editor crash the build folder landed in
  the previous session's scratchpad, which the publish refused ("outside the working directory or your scratchpad").
- **Suggested change:** on a refresh, the build reads the live `data.json` (`read` with `path: data.json`) and changes
  only what the feature files changed: statuses, checklist links, new docs, waiting lines. A full rebuild runs only
  on a create or when the user asks. The orchestrator gives the build its own session's scratchpad path in the brief.

### impl-* role files: set work aside without `git stash`; the report is the last action

- **What happened:** (1) an implementer ran `git stash` in a worktree to compare with the base. The stash stack is
  shared with the main checkout and other sessions; it failed harmlessly. (2) Two executors (an implementer and a
  Gate B fixer) left a background lint monitor running after their report, and re-sent the same report 2-3 times.
  The orchestrator had to stop one with TaskStop.
- **Suggested change:** in `impl-tdd`, `impl-fixer`, `impl-trimmer`: "To compare with the base, use the checkpoint
  tree or `git show <base>:<path>`; to set work aside, a WIP commit." and "Your report is your last action: wait for
  every check you started before you write it."

### orchestrate step 4 / manual-checklist: expected results must trace to the diff

- **What happened:** the Haiku guide-writer (rung 1) wrote 2 wrong items. One said a file with a wrong extension gives
  a parse error, but a file-type check refuses it earlier. The other said a trace shows the payload, but a masking
  step replaces it. The orchestrator caught both by reading the guide.
- **Suggested change:** run the manual-checks executor at rung 2. manual-checklist adds: "each expected result names
  the test or code line it comes from; drop an item you cannot trace."

### orchestrate / codex backend: third claude-only run

- **What happened:** the probe failed again with "failed to load AWS credentials". See the 2026-10-24 entry; still
  open.

## 2026-10-27 — retro of an orchestrate run (backend + frontend ticket)

### orchestrate: executors and triage run the repo lint gate, not pylint alone

- **What happened:** every implementer and the fixer ran only pylint (10.00). The repo lint gate (the changed-files
  lint script against BASE) ran first after the trim and failed on 3 items: an inline `#` comment (a rule in the
  package's CLAUDE.md), a known import-error trap on framework imports in touched files, and an autopep8 indent that
  the fixer's rename broke. This cost two more fixer rounds. Also, at triage the orchestrator rejected the Standards
  finding on that inline comment as "matches the surrounding code", and the gate then enforced it.
- **Suggested change:** orchestrate *Writing a brief* -> every implementer, fixer and trimmer brief carries the
  plan's lint command as part of its done check ("green tests and a `clean` lint gate"). Step 2 triage: run the lint
  gate before you reject a Standards finding; a finding the gate enforces is fix-now.

### manual-checklist / orchestrate step 4: give the writer the slice's scope boundary

- **What happened:** at rung 2 the guide-writer still wrote 2 items that describe later tickets. The orchestrator
  corrected both.
- **Suggested change:** the step 4 brief names which later tickets own which behaviour (the plan's scope boundary).
  manual-checklist: "write a check only for behaviour this diff adds; behaviour a later ticket owns is out."

### impl-explorer: report the package's lint command from its CLAUDE.md

- **What happened:** the plan's pylint command used one rcfile; the package's CLAUDE.md requires another. The first
  executor found and corrected it.
- **Suggested change:** impl-explorer's Commands section: "read the lint/typecheck command from the nearest
  CLAUDE.md/AGENTS.md of each package in scope and quote it."

### orchestrate / codex backend: fourth claude-only run

- **What happened:** the probe failed again with "failed to load AWS credentials". See the 2026-10-24 entry; still
  open.

## 2026-10-27 — retro of an orchestrate run (frontend + backend ticket, caps and budget)

### rc-orchestrate step 2: a comment pass in the Standards brief

- **What happened:** the user caught two items at Gate B that the Standards reviewer missed with the workspace coding
  standards in hand: `//` comments that restate the code, and logic formatters in a constants file.
- **Suggested change:** Standards brief: "for each comment the diff adds or changes: does it give a why the code
  cannot? If not, flag it." (The constants/utils rule is now a line in the coding standards.)

### rc-orchestrate step 2: suppress findings the surrounding code shares

- **What happened:** across 15 run logs, labelled Standards findings were 19 fixed / 16 rejected / 8 deferred; many
  rejections read "the surrounding code follows the same pattern".
- **Suggested change:** Standards brief: "when the code next to the hunk follows the same pattern, leave it; repo
  convention wins."

### rc-feature-page: merge onto the live data.json at publish

- **What happened:** both publishes of the run were refused because parallel sessions published in between; the
  orchestrator read the live `data.json` and re-applied the run's status and doc changes by hand.
- **Suggested change:** Build and publish: "right before publish, read the live `data.json` and apply only this run's
  status, checklist and doc changes onto it."

### rc-tdd / rc-fixer: return clean

- **What happened:** a test-writer returned with background work still running (a second writer risk in the tree);
  executors ran the lint helper's `--fix`, which reformats every changed file, other cycles' too.
- **Suggested change:** role files: "return with no background process" and "after --fix, check git diff --stat
  against the call's checkpoint and keep only your files."

### worktree helper script, merge: test the target after a non-ff merge

- **What happened:** merging the main development branch into the feature parent broke 24 route tests (another
  change added a database collection that a test harness did not patch); the next run found it only at BASE.
- **Suggested change:** after a merge that is not a fast-forward, the merge command runs the test suite on the target
  and prints new failures (or prints a reminder to run it).

### orchestrate / codex backend: fifth claude-only run

- **What happened:** probe failed again ("failed to load AWS credentials"). Likely the codex credential chain does not
  read the workspace's temp-credentials file; still open, see the 2026-10-24 entry.

## 2026-10-27 — orchestrate run (backend ticket, untrusted-content rows)

### rc-orchestrate: check the live page before a refresh build

- **What happened:** two delegated refresh builds (~340k tokens together) were thrown away; both times another
  session had already published the same ticket states, so the publish was skipped (step 5, same states).
- **Suggested change:** *Refresh the page*: before spawning the build, read the live `data.json` and check the
  changed ticket's state; when the live page already shows it, skip the build and say so in the run file.

### rc-orchestrate: agent-facing text goes through writing-for-agents

- **What happened:** fix briefs dictated text for a rules file and for docstrings that agents read; the user had to
  ask for writing-for-agents, which then found a stale paragraph, a missing rule-table branch and the same limit
  repeated in three rows (one more Gate B round).
- **Suggested change:** *Writing a brief*: when a change edits an agent-facing file (rules files, CLAUDE.md, skills,
  registry or gate docstrings), the brief tells the executor to load writing-for-agents first.

### rc-orchestrate: lint in the fixer's verify, not only at Finish

- **What happened:** the lint helper caught a ticket reference in a comment (the repo allows only the tracker-ID form)
  only while the orchestrator prepared Gate B; the text came from the orchestrator's own fix brief, so one extra fix
  round ran.
- **Suggested change:** step 3 verify (and Gate B change verify): run the lint script over the changed files.

### rc-orchestrate / rc-tdd: a red test must fail at its behavioural assert

- **What happened:** a test failed at its first assert, which hid a KeyError on a later line; the implementer stopped
  on it and the test-writer was resumed for a one-line fix.
- **Suggested change:** step 1a verify: a test with several asserts counts as red only when it fails at the
  behavioural assert; rc-tdd test-writer: "each red test fails on the assertion that names the missing behaviour, and
  the lines after it run against a stub of the expected value" (or: flag multi-assert tests whose later lines never
  ran).

## 2026-10-27 — retro of an orchestrate run (frontend + backend ticket, history reload)

### rc-orchestrate / rc-feature-page: a status-only refresh patches the live data

- **What happened:** the delegated build (Haiku) took ~160k tokens and 4 min and rewrote all 30 decision lines in its
  own words; it was not used. Both refreshes of this run (second run in a row) worked by reading the live
  `data.json`, changing one ticket's status (+ one guide doc entry and its file), and republishing. The publish needs
  a page `file_path` even for a data-only change, and `read path=index.html` returns the page wrapped in the skeleton
  (use the build's source `index.html`, or read the bare url).
- **Suggested change:** *Refresh the page*: when only ticket statuses or guides changed, patch the live `data.json`
  (re-read right before the publish: parallel runs publish too) instead of a delegated build; keep the delegated
  build for slice/spec/overview changes.

### rc-orchestrate: Finish -> Merge names a skill that is not installed

- **What happened:** "On a conflict, invoke `/resolving-merge-conflicts`" -> "Unknown skill". Resolved by hand
  (2 conflicts: an earlier ticket had moved some formatters to another module).
- **Suggested change:** install the skill, or replace the line with the hand procedure (resolve, lint the resolved
  files, run the touched test files, commit `--no-verify`).

### rc-orchestrate: backend check must run from the repo root

- **What happened:** the probe run from the workspace dir (not a git repo) failed on "Not inside a trusted
  directory"; from the worktree it failed on "failed to load AWS credentials" (fourth run in a row).
- **Suggested change:** Phase 0 *Run the backend check*: `cd <repo> &&` before the probe, as the codex call already
  does; separately, the codex credential setup is still broken.

### rc-orchestrate: the test-writer owns the expectations a new field breaks

- **What happened:** two cycles each added an optional field to a shape that existing tests compare exactly (about 23
  tests in three files). The test-writer saw it ("the next cycle must update..."), but the implementer's brief forbids
  test edits, so both implementers blocked and were resumed with a one-off permission.
- **Suggested change:** step 1a brief: "When the cycle adds a field to a shape that existing tests compare exactly,
  update those expectations in this step; they go red with the new tests." Step 1b's "no test edits" then holds.

### rc-feature-page: one generator script, not a fresh one per build

- **What happened:** each delegated build writes its own generator. Between two builds the slice keys changed case and
  every published doc path was renamed; the old paths stay published (files left out are kept), and a conflict with
  another session's publish needed a hand comparison of the two `data.json` files.
- **Suggested change:** keep one checked-in generator script in the skill and have the delegated build run it; only
  the overview-driven prose stays model-written. Pairs with the "status-only refresh patches the live data" entry.

## 2026-10-28 — retro of an orchestrate run (backend job ticket)

### rc-orchestrate: a plan risk that claims safety names the test that holds it

- **What happened:** the plan's Risks said "Edit/Regenerate race: covered by the 24 h file-age grace". No test backed
  it, and it was false (the re-send reuses OLD file ids). The Bugs reviewer caught it after both cycles; the fix
  needed a user decision and a new test in a third file. Logged `escaped · plan`.
- **Suggested change:** Phase 0 *Write the plan* -> Risks: "each mitigation names the test that fails when it is
  false; a mitigation with no test is an open question for Gate A". For a job that deletes data, also brief the
  explorer to list every writer and remover of the state the job reads, and the windows between them (the "unchanged
  code" check of the second-reader review rule, at plan time).

### rc-orchestrate: the plan places new code by the coding standards, and the Standards reviewer checks placement

- **What happened:** the plan put the new job into a 3,000-line module that holds 16 tasks. The coding standards say
  "New feature code goes in its own module". The Standards reviewer did not flag it; the user did at Gate B, which
  cost two extra rounds (refactor + module move + round review + round fix). Logged `escaped · standards`.
- **Suggested change:** (a) Phase 0 plan: name the module for new logic and check it against the placement rule; (b)
  Standards brief in step 2: add "placement: new logic added to a file that already holds several responsibilities".

### rc-orchestrate: briefs for a loop over stored items name the per-item try boundary

- **What happened:** all three reviewers flagged a skip-check outside the per-item `try` (a backend rule: loops over
  stored items catch per item). The Gate B refactor then reintroduced the same class at another read (copied from a
  similar loop), caught only by the round review.
- **Suggested change:** in *Writing a brief*, when the code loops over stored items: "every I/O call inside the loop
  sits inside the per-item try; say which calls". Quote the rule in implementer and fixer briefs.

### a sinks doc for user messages: list the transcript reader's shaping

- **What happened:** the spec said "use the transcript reader the backfill uses" for referenced ids. Recon found that
  the reader is shaped for the UI: it drops some entries, skips internal messages and falls back to older
  checkpoints; each would have deleted live files. The repo's sinks doc does not name this reader.
- **Suggested change:** add a row to the sinks doc naming that reader, saying what it drops, and pointing at the raw
  id reader to use instead.

### rc-feature-page: +1 for "a status-only refresh patches the live data"

- This run published the full 70-file list three times (one refusal from a parallel session, one identical-resend
  refusal). The existing entry above covers the fix.

## 2026-10-28 — retro of an orchestrate run (backend job ticket, second pass)

### rc-feature-page: the renamed doc paths reached the 512-file cap (escalates "one generator script")

- **What happened:** the delegated build named every published doc copy in a new way again. The live page held 448
  files, mostly stale copies of the same ~70 docs under 8 naming schemes. The publish failed with "manifest exceeds
  512 entries". Fixed by hand: listed the files (`scope: "files"`) and sent `null` for 80 stale paths. ~368 stale
  paths are still published.
- **Suggested change:** (a) the "one generator script" entry above, with a fixed doc naming rule; (b) *Build and
  publish* step 4: list the live files first and send `null` for every published path that the build does not have,
  so each refresh leaves exactly the build's files; (c) one clean-up publish to drop the ~368 stale paths.

### rc-feature-page: +1 for "a status-only refresh patches the live data"

- Two refreshes this run. Each delegated build took ~155k tokens and 3.5 min. The first publish was refused because a
  `read` with `path: "data.json"` does not count as viewing the page; then "identical content resent" was refused
  once more. *Build and publish* step 4: say "read the url with no `path`".

### rc-orchestrate: the plan lists the existing tests that a new rule changes (+1 to "the test-writer owns...")

- **What happened:** the second pass changed what two earlier tests at the same seam see. The plan did not name them;
  the implementer found them red and stopped, which cost an extra test-writer call. Logged `escaped · plan`.
- **Suggested change:** Phase 0 *Write the plan* -> per cycle: "Existing tests at this seam whose fixtures the new
  rule now matches (grep the seam's test file for the fixtures the rule reads)"; step 1a updates them with the new
  tests.

### rc-orchestrate: Gate B asked for a refactor two runs in a row -> add function shape to the Standards brief

- **What happened:** two consecutive Gate Bs asked for a refactor, and then for "get rid of all the nested fors in
  same function — I generally hate nested fors". Each request cost a fixer round and a round review. The Standards
  reviewer passed the code both times.
- **Suggested change:** (a) add to the coding standards (judgement call, read at review): "One loop level per
  function: extract the per-item work into its own function, with its per-item try inside"; (b) the Standards brief
  in rc-orchestrate step 2 adds "function shape: nested loops, a public function that holds a whole pass, helpers
  duplicated across passes"; (c) optional mechanical check: an AST check in the changed-files lint script that flags
  a `for` nested in a `for` inside one function on added lines.

### worktree helper script: a trap recurred through a copied tooling directory (fixed in this run)

- **What happened:** the main checkout merged the development branch mid-run; one of its tooling modules imports a
  module the worktree's test tree does not have, and the container's PYTHONPATH reached the main checkout's copy
  before any worktree copy. The fixer was blocked; the orchestrator added the directory to the script's copied trees
  and to the PYTHONPATH.
- **Suggested change:** build the container PYTHONPATH from the list of copied trees, so a newly copied tree is
  always first. The repo's traps file has a note.

### rc-orchestrate / codex: probe failed on cloud credentials again (open since 2026-10-24)

- Same "failed to load AWS credentials"; whole run on Claude. See the 2026-10-24 entry.

## 2026-10-28 — retro of an orchestrate run (backend job ticket, parts and index)

Review outcomes across all run logs: standards 13 fixed / 1 deferred / 1 rejected; spec 4 fixed / 1 deferred; bugs 4
fixed / 3 deferred / 1 rejected. No axis is noisy. Escapes: standards 2 (module layout; feature code in a big module),
plan 2.

### changed-files lint script: module constants after the first def -> deterministic check (escaped twice)

- **What happened:** the Standards reviewer flagged constants added mid-file in the test file, but not the same
  pattern in the new production module. The user caught it at Gate B: one more fixer round. `escaped · standards`.
- **Suggested change:** the rule is mechanical (coding standards: constants at the file top). Add an AST pass to the
  lint script: on added lines of changed `.py` files, fail a module-level `NAME = ...` (UPPER or `_UPPER`) that sits
  after the first module-level `def`/`class`. Keep `logger`/`__all__` exempt.

### rc-orchestrate: plan Risks must pair each new query with the index that serves its filter AND sort

- **What happened:** the plan for the second pass batched by `_id` while the only index was a partial index on
  another field. The spec reviewer found the blocking sort after implementation; it cost a user question, a second
  test-first cycle, and a spec/checklist update (the index became a compound index). A later round review then found
  the seek also needed a top-level bound.
- **Suggested change:** Phase 0 *Write the plan* -> **Risks**: "For each new or changed database query: the index
  that serves its filter and its sort, and the resume/seek shape when it is paginated." Add the same line to the Bugs
  brief's "worth checking" list for diffs that touch `find`/`sort`/`limit`.

### rc-tdd (test-writer mode): no prototype implementation in the tree; derive expectations from the brief

- **What happened:** one test-writer wrote a throwaway implementation in three production files to check its tests
  could pass, then restored them (verified unchanged, but a crash mid-way would have left production edits inside a
  "tests only" delta). Another test-writer pinned a wrong resume point (first file of the NEXT batch, not the last
  file done); the implementer caught it and stopped.
- **Suggested change:** `agents/rc-tdd.md`, test-writer mode: "Production files stay untouched for the whole call,
  even temporarily. Derive each expected value from the brief's stated rule and write the rule beside the assertion
  in a short comment" (the comment makes an off-by-one visible to the implementer and reviewer).

### rc-orchestrate: no ScheduleWakeup in orchestrate runs (a memory rule existed; it fired twice as fake user turns)

- **What happened:** the orchestrator scheduled a 20-min fallback wakeup while recon and the BASE suite ran. Its
  prompt ("continue rc-orchestrate run ...") arrived twice, once while Gate A/B waited on the user — it reads like a
  user turn. Background tasks already notify on completion. The memory note covered only gates.
- **Suggested change:** rc-orchestrate *Executors*: "Background executors and suites notify on completion: schedule
  no wakeup during a run." (Positive form: "wait for the completion notice.")

### rc-orchestrate: backend probe must run from the repo root

- **What happened:** the Phase 0 probe ran from the workspace dir (not a git repo) and failed on "Not inside a
  trusted directory"; the re-run from the worktree failed on cloud credentials as before (open since 2026-10-24).
- **Suggested change:** prefix the probe snippet with `cd <repo> &&`, like the codex call snippet below it.

### rc-feature-page: "read first" means a page read, not a `path` read

- **What happened:** before the first refresh publish the orchestrator read `data.json` with `path`; the publish was
  still refused ("hadn't viewed the live version"), then refused again as "identical content", and went through on
  the third call.
- **Suggested change:** Build and publish step 4: "read it first (`action: "read"` with `url` and no `path`)".

### rc-orchestrate: a pure-move Gate B round needs no rc-reviewer

- **What happened:** Gate B change 1 only moved two constants. The orchestrator checked "every added line equals a
  removed line" (`git diff <tree> | grep '^[+-][^+-]' | sed 's/^[+-]//' | sort | uniq -u` is empty) instead of
  spawning a reviewer, and logged it as a deviation.
- **Suggested change:** Gate B *Round review*: "A local-code round whose delta is a pure move (the check above prints
  nothing) skips the reviewer; log the check."

## 2026-10-29 — retro of two orchestrate runs (frontend tickets)

### rc-feature-page: +1 for "the renamed doc paths reached the 512-file cap" (third time)

- The page held 502 files; the build named the docs again in a new way. The publish failed on the 512 cap; the
  orchestrator sent `null` for 82 stale copies. ~380 stale copies are still published (464 files now), so the next
  1-2 refreshes hit the cap again. The fix in that entry ((a) fixed naming rule, (b) `null` for every published path
  the build lacks) is now blocking. The build also cost ~173k tokens (Haiku).

### rc-orchestrate: +1 for "the plan lists the existing tests that a new rule changes" (a rename is one such rule)

- The plan renamed a private method; one existing test read the old name. The implementer stopped and asked; one
  round trip. Add to that entry: "for each rename, grep the tests for the old name; step 1a or the implementer
  updates those references and reports them."

### rc-orchestrate: +1 for "Gate B asked for a refactor" -> the Standards brief compares a hunk with its file's idiom

- **What happened:** at Gate B the user asked "this store file seems a bit weird?" The new hunk built a temp object, a
  ternary between two objects and a 4-line ad-hoc type, where the same file sets the same field with one conditional
  spread and already has a type for it. Three reviewers passed it (logged `escaped · standards`). Third Gate B
  refactor request in four runs.
- **Suggested change:** add to the Standards brief in step 2: "For each new hunk, find code in the same file that
  does the same job (sets the same field, reads the same response key); flag a hunk that does it a different way."

### rc-orchestrate: +1 for the codex credentials entry (sixth and seventh claude-only runs)

- Probes: "failed to load AWS credentials". No cross-family review in any run since 2026-10-24.

### testing rules: `test.for` vs `test.each` conflict (repo rules, not a skill)

- Two rules files in the repo disagree: one says "Parametrize with `test.for()`", the other says `test.each`. A
  test-writer used `test.each`; a fix round converted it.
- **Suggested change:** make the rules agree, and add an eslint `no-restricted-syntax` for `test.each`/`it.each` in
  frontend test files.

### rc-feature-page / patch-status.py: a slice that is not on the page is silent (2026-11-03)

- **What happened:** a new feature slice with a tickets folder is not on the live page. The status refresh walks only
  the live page's slices, so it printed no `NEW` line, and the ticket's done state never showed. The orchestrator
  read the one `STATUS 01` line as its own ticket; it was another slice's ticket 01.
- **Second cause:** that other ticket says `Status: in progress — resumed ...` (a space, off the tracker
  vocabulary), and the script maps it to `UNKNOWN:in`, so every refresh would publish a wrong state. The
  orchestrator first blamed the hyphen split; the split is fine.
- **Suggested change:** in `patch-status.py`, print `NEW slice <id>` for each slice folder with a tickets folder that
  the page does not show, and prefix each `STATUS` line with the slice id. Accept `in progress` as `in-progress`
  (normalise a space between two vocabulary words), or fix the ticket line.

### rc-orchestrate: red test-writer runs take ~18 min in Vitest browser tests (tool economy)

- **What happened:** each red `expect.element` waits its full 30 s timeout, so the 1a run of one test file (34 red)
  took ~18 min twice (writer + orchestrator verify).
- **Suggested change:** in the 1a verify step and the test-writer brief, run the red file with a short locator wait
  (a Vitest browser timeout option, or an environment variable the config reads; check the Vitest config first). A
  red test needs to be red, not to wait 30 s to prove it.

### rc-orchestrate: verify list missed a test that reads the changed type

- **What happened:** the fixer removed fields from a view type and found a hook test that reads those fields; that
  file was not in the orchestrator's verify list (from the recon). It was green.
- **Suggested change:** Phase 0 *Explore* brief: "for each type or hook the ticket changes, list every test file that
  imports it" (a grep the explorer can do cheaply), and put those files in the plan's Commands.

### rc-orchestrate: +1 for the codex credentials entry (eighth claude-only run)

- Probe, 2026-11-02: "failed to load AWS credentials". Review axes still healthy across the run logs (Standards 12
  fixed / 5 rejected / 4 deferred; Bugs 2 / 0 / 3; 3 escaped total, none this run), so no brief change.

## 2026-11-03 — retro of an orchestrate run (frontend ticket, grey rows)

### rc-feature-page, `scripts/patch-status.py`: a new slice is invisible, and "in progress" parses as UNKNOWN

- **What happened:** the status refresh after a ticket went `in-progress` printed only
  `STATUS 01: in-progress -> UNKNOWN:in` and no `NEW` line, although a whole slice (8 tickets) is not on the page.
  The orchestrator did not publish, so the page still lacks the slice.
- **Cause (verified in the script):** (1) the `NEW` scan walks only the ticket folders of slices already in
  `data['slices']`, so a new slice's folder is never read; (2) `ticket_state` splits the status on whitespace, so a
  line like `**Status:** in progress ...` yields the word `in` -> `UNKNOWN:in`, and a publish would write that state
  to the page.
- **Suggested change:** also glob every slice's ticket folder and print `NEW SLICE <id> (not on the page: run a full
  refresh)` for every folder whose id is not a page slice; normalise `in progress` -> `in-progress` before the split
  (or map multi-word states), and refuse to write a state that starts with `UNKNOWN:` (print it, keep the old state).

### rc-explorer (rc-orchestrate Phase 0): list the tests whose SETUP depends on removed behaviour

- **What happened:** the recon listed every test that asserted the removed UI element, but not two edit-box tests
  whose setup first polled a request counter for the sent message's extra resources. After the implementation they
  failed, and the run needed an extra test-writer round plus a cross-session note to the ticket that owned those
  tests.
- **Suggested change:** in the explorer role, for every behaviour the ticket removes, grep the tests for its
  observable (request counter, test id, role, class) and list EVERY hit, setup lines included, with the ticket or
  area that owns the test. Same rule as the second-reader review rule "find the tests that the change breaks outside
  the diff", applied at plan time.

### rc-tdd, test-writer mode: run the lint gate on the test files before returning

- **What happened:** the test-writer returned tests with a bitwise `&` helper; the lint helper failed on
  `no-bitwise` only after the implementer ran it, which cost one more round. The check exists; the test-writer brief
  and role do not ask for it.
- **Suggested change:** test-writer mode ends with the repo's lint command on the files it changed, and returns its
  result line. A red-for-the-right-reason test that fails lint is not done.

### rc-orchestrate, Writing a brief: offer executors only options that meet the repo rules

- **What happened:** the implementer brief said to put a UI label in a constant "only if that module is where such
  labels live; otherwise inline". The implementer inlined it, and the Standards reviewer flagged it against a repo
  rule (extract string literals to constants). One fix-round item came from the brief, not the executor.
- **Suggested change:** a line under *Writing a brief*: every choice a brief leaves to the executor must already
  comply with the path-scoped rules of the files in scope; when unsure, decide it in the plan.

### rc-orchestrate, backend check: skip the codex probe while the credentials trap holds

- **What happened:** the probe failed again with "failed to load AWS credentials" (codex access lost since mid-October;
  44 mentions across the run files). Each run spends a probe and a log line to learn the same fact.
- **Suggested change:** read a switch first (e.g. `RC_BACKEND=claude` in the environment, or a one-line `BACKEND` file
  in the rc-codex skill that the user sets) and record "backend claude" without probing; the user removes the switch
  when access returns.

## 2026-11-03 — retro of an orchestrate run (frontend layout ticket)

### rc-orchestrate, Finish: a frontend failure off the BASE list gets a seeded shared-context replay before "flaky"

- **What happened:** the finish domain run (parallel, no shuffle, so no seed) failed one test that passed alone 3
  times; it was logged as flaky. A peer orchestrator pointed at a repo rule: "passes alone, fails in the shared run"
  means a leak from another file. The seeded replay (`--no-isolate --no-file-parallelism --sequence.shuffle.files
  --sequence.seed=N`, head and base) took 4 extra runs, found no leak from this change, and found a different
  pre-existing leak that reproduces on the base.
- **Suggested change:** in *Finish*, for a frontend run: run the domain set once with
  `--sequence.shuffle.files --sequence.seed=<fixed>` so any failure can be replayed; a failure off the BASE list is
  replayed with the same seed in shared context on head and BASE before it is called flaky or pre-existing. Point to
  the rules file, do not copy it.

### rc-tdd, implementer + rc-orchestrate plan: a CSS-only acceptance needs a look, not only tests

- **What happened:** the plan said "layout is CSS only: hand check, not a test", and the implementer brief described
  both layouts. The return passed every test but kept `flex-wrap` in one layout and let a chip break the grid in the
  other. The Spec reviewer caught both from the design frames; one fix-round item each.
- **Suggested change:** when the plan marks an acceptance as CSS only, the implementer (and the fixer) render each
  layout in the vitest browser, take `page.screenshot()` to the run dir, read the image against the design frame, and
  return the paths. No assertion, so no brittle test; the orchestrator glances at the images at verify.

### rc-tdd, test-writer mode: run the lint gate before returning (+1)

- **What happened:** again: a test-writer's helper failed prettier; the implementer could not fix it (test file out of
  scope), so it rode to the fix round. Same entry as the previous retro.

### worktree helper script: `add --no-warm` also skips `pnpm install`

- **What happened:** a temp base worktree made with `--no-warm` failed all 118 vitest files (a workspace package
  import could not resolve) until `pnpm install --frozen-lockfile` ran. The usage text says `--no-warm` skips "pnpm
  install + warm Vite's cache", but the name reads as "skip the warm-up only".
- **Suggested change:** `--no-warm` keeps the install and skips only the Vite warm-up (install is ~30 s), or the
  script prints "deps not installed: run pnpm install --frozen-lockfile" at the end.

### changed-files lint script: label tree-wide checks as tree-wide

- **What happened:** after a merge of the development branch, a new tree-wide SCSS ratchet made the lint result
  FAILED, listing two components the change did not touch. It took a manual check against the base to show the
  failure was already there.
- **Suggested change:** the script prints tree-wide checks under their own heading, marks hits in files outside the
  change as "not in this change", and, given a base, says whether the base fails it too.

### rc-orchestrate, peer orchestrators: the commit go-ahead relays the user's review

- **What happened:** a peer orchestrator gave the Gate B go-ahead, the commit was made at once, and the peer withdrew
  the go-ahead a minute later ("the user wants to read the code before each commit"). The commit stood; the user
  accepted it after reading.
- **Suggested change:** in the brief a peer orchestrator sends, and in *Gate B*: when the go-ahead comes from a peer,
  it must say the user read the Gate B report ("the user approved"); a go-ahead without that line is asked back once
  before the commit.

### rc-orchestrate, backend check: +1 (ninth claude-only run)

## 2026-11-03 — retro of an orchestrate run (backend + frontend ticket, live rows)

### rc-orchestrate, plan: a new stream event must name every hold/discard path it crosses (escaped · plan)

- **What happened:** a plan decision sent a new server-sent event outside the answer holdback ("flows like `step`"),
  written without a source. The Bugs and Spec reviewers both found that a discarded draft (answer-check revision,
  plan hold) then leaves a false row. Fixed in the one fix round, with 3 new tests. A second plan slip of the same
  kind: the plan pinned a wire payload as exactly `{id, name}` without reading the shared event constructor, which
  adds a `timestamp`; the implementer then added a speculative flag to the shared class to satisfy the
  exact-equality tests (removed in review).
- **Suggested change:** in *Write the plan* -> **Risks**, add one line: "A new event, message field or payload on a
  shared channel: name the unchanged code it passes through (buffers, holds, discards, retries, the shared
  constructor) and decide each path in the plan." This is the second-reader rule "name the unchanged code" applied at
  plan time, where it is cheapest.

### rc-feature-page, patch-status.py: a slice missing from the page is silent, and "in progress" parses as UNKNOWN

- **What happened:** the live page had no entry for the current slice. The status refresh printed only
  `STATUS 01: in-progress -> UNKNOWN:in` (another slice's ticket, whose line is `Status: in progress — ...`) and
  nothing about this ticket or the missing slice. Publishing would have corrupted the other slice's state; the
  orchestrator skipped it.
- **Suggested change:** (1) normalise a space in the status word (`in progress` -> `in-progress`) before the
  `WORD_TO_STATE` lookup; (2) list every slice folder on disk whose id is not on the page as `NEW SLICE <id> (run a
  full refresh)`; (3) never write an `UNKNOWN:` state into `data.json` — print it and keep the old value.

### Ticket writing (feature-artifact / issue tickets): a named seam must exist

- **What happened:** a ticket and the spec's testing decisions name "the store test through the SSE fakepoint". No SSE
  fakepoint exists (the test fixtures cover only the POST); recon found it and the plan mapped the seam to the
  stream-callback builder plus a fake event-source test.
- **Suggested change:** when a ticket names a test seam by a concrete artifact (a fakepoint, a fixture, a helper), the
  ticket writer greps for it, or writes the seam by behaviour ("the store, driven by the stream callbacks").

### worktree helper script, suite command: BASE run shares the worktree with executors

- **What happened:** the BASE backend suite (20 min) ran in the ticket worktree while executors edited it; the
  script's log listed the changed files afterwards. The run was valid only because pytest had collected and imported
  before the first edit.
- **Suggested change:** rc-orchestrate *Record BASE failures*: start the BASE suite before the first executor and let
  no executor start until collection has finished — or, simpler, run the BASE suite on the shared parent worktree
  when its HEAD equals BASE, never in the run's own worktree.

### rc-orchestrate, backend check: +1 (tenth claude-only run: codex "failed to load AWS credentials")

## 2026-11-03 — retro of an orchestrate run (frontend ticket, banner slot)

### Frontend test setup: a stubbed `<Transition>` makes a design-system notification's `closable` untestable (severity: high)

- **What happened:** `closable` emits `close` only from the collapse transition's `before-collapse` hook. The test
  setup (Vue Test Utils) stubs `<Transition>`, so the hook never fires: the banner hid, but the parent never heard the
  close. The implementer replaced `closable` with its own close button. The user accepted it, but production lost the
  collapse animation, and a design follow-up list got one more item. The same stub problem is already documented for
  modals.
- **Suggested change:** fix it once in the test setup: render `<Transition>` so that its JS hooks still fire (or stub
  the expand/collapse transition with one that calls before/after-collapse synchronously). Until then, add a trap to
  the repo's traps file ("closable notification never emits close in tests -> Transition stub"), so the next
  implementer does not change product markup for a test limit.

### rc-orchestrate Gate A: a [Your call] that defines the ticket's main visible rule belongs at Gate A (severity: medium)

- **What happened:** the orchestrator marked 4 plan decisions [Your call] and kept them for Gate B. The user overturned
  one (what a number in a cap banner counts: a running total vs "the count refused by the last add"). That cost a
  full extra cycle (tests, implementation, round review) plus a batch API change in 3 callers. The other 3 were
  accepted.
- **Suggested change:** in *Gate A*, add: "A decision you make alone that sets a rule the user will see in the
  ticket's main flow (what a number counts, when a message shows or goes) is an open question: ask it at Gate A. Keep
  [Your call] at Gate B for edge cases and copy." One question then saves one cycle.

### rc-orchestrate backend check: +1 (eleventh claude-only run)

### rc-feature-page patch-status.py: +1 (the new slice still not on the page; same `UNKNOWN:in` line)

### rc-orchestrate, peer integration: write tests in the target's test API from the first brief (severity: low)

- **What happened:** a heads-up about a test-framework major update arrived after the first cycle's tests were
  written; it cost one mechanical test pass (22 `await`s). Later briefs carried the rules and needed nothing.
- **Suggested change:** in *Phase 0*, when the parent branch is known to take a test-framework update before this
  ticket merges (ask the orchestrator peer, or check the parent's pending merges), put the new test-API rules in the
  run file's plan and in every test-writer brief from cycle 1.

### Review log counts (all runs of the feature)

- Standards: mostly fixed (36 fixed, 9 rejected, 6 deferred); Bugs: 9 fixed, 9 deferred, 1 rejected; Spec: 13 fixed,
  2 deferred, 1 rejected. No axis is noisy. 3 `escaped` lines exist from earlier runs; none in this run.

## 2026-11-03 — retro of an orchestrate run (backend + frontend ticket, reload)

### rc-orchestrate / rc-reviewer Standards brief: 4 style findings escaped to the user at Gate B (severity: high)

- **What happened:** the user's Gate B round 1 had 5 requests; 4 were Standards findings the reviewer missed: a
  mid-file module constant (the reviewer flagged only the test constants), an inline comment that repeats the helper's
  doc line, a conditional spread with a ternary in a big object literal, and a new helper + constant added to a
  14,000-line module. Cost: one extra fix round + round review.
- **Suggested change:**
  - Mechanical -> checks in the changed-files lint script: (a) an added module-level constant after the first
    `def`/`class` of a Python module; (b) added `def`s in a file over ~5000 lines ("put new helpers in a sibling
    module; the big file gets call sites only").
  - Judgement -> append to the Standards prompt in rc-orchestrate step 2: "Flag a comment that restates a nearby doc
    comment, and a conditional spread / nested ternary inside an object literal where a named helper would read
    plainly."

### rc-orchestrate Gate B "Your call": follow an in-code precedent instead of asking (severity: low)

- **What happened:** the orchestrator kept "copying a conversation keeps the rows" as a Your call. The user chose
  strip, the same as an existing copy filter that strips similar user data. The precedent was in the code.
- **Suggested change:** in step 2 triage: "When the same class of data already has a rule in the code (a filter, a
  sink rule), apply that rule in the plan and cite it; a Your call is for cases with no precedent."

### worktree helper script, backend test commands: exit 137 hidden, reported as success (severity: medium)

- **What happened:** two backend area runs were SIGKILLed (137) mid-suite (a known container-memory trap, probably
  another session's run at the same time). The executor's background task reported exit 0 through a pipe and it
  waited 30 min on a Monitor; the orchestrator's own run printed `exit=137` only because it echoed `$?` before the
  grep.
- **Suggested change:** when pytest exits 137, the script prints "KILLED (137): container memory limit — re-run when
  no other pytest runs in the container" and exits 137 even under a pipe (`set -o pipefail` inside the wrapper);
  optionally refuse to start while another pytest runs in the container.

### rc-orchestrate Phase 0: BASE suite raced with the first executor (severity: low)

- **What happened:** the orchestrator started the 17-min BASE suite and then the first test-writer in the same
  worktree; the suite marked itself invalid (TREE CHANGED). Saved only because a peer had a clean BASE count for the
  same commit.
- **Suggested change:** in *Record BASE failures*: "Let the BASE suite finish before the first executor call, or run
  it in a throwaway worktree at BASE (the helper script's add command with a no-warm option)."

### rc-orchestrate backend check: +1 (twelfth claude-only run)

### rc-feature-page: +1 (page not refreshed; the new slice still missing on the live page)

### Review log counts (this run)

- Standards: 3 fixed, 1 deferred, 4 escaped. Spec: 1 fixed, 1 Your call. Bugs: 0 findings, 1 deferred note. Round
  review: 1 Nit fixed. Standards is the axis to tune (escapes), not noisy.

## 2026-11-03 — retro of an orchestrate run (frontend ticket, style language migration)

### rc-feature-page patch-status.py: "in progress" parses as UNKNOWN:in (severity: medium)

- **What happened:** both status refreshes printed `STATUS 01: in-progress -> UNKNOWN:in` for another slice's ticket
  (`Status: in progress — resumed ...`). The script takes the first word. Publishing as is would have overwritten
  the live "in-progress" state; the orchestrator restored it by hand both times.
- **Suggested change:** in patch-status.py, normalise the status phrase before the lookup (`in progress` ->
  `in-progress`, case-insensitive), and never write an `UNKNOWN:*` over a known live state: keep the live value and
  print `UNPARSED <file>: <raw line>`.

### rc-feature-page Status refresh: a data.json read does not count as the page read (severity: low)

- **What happened:** step 1 reads `data.json` (`path`), then the publish was refused ("You hadn't viewed the live
  version"), and the resend of the same content was refused a second time before a third send went through.
- **Suggested change:** in *Status refresh* step 1: "On the session's first refresh, also read the page itself
  (`action: "read"` without `path`); a `path` read does not count as viewing it."

### rc-orchestrate: a CSS-only ticket has no red test; use a reusable no-visual-change harness (severity: medium)

- **What happened:** the ticket changed only style blocks, so the test-first cycle had no seam. The orchestrator
  replaced it with a harness cycle: compiled-CSS diff (`@vue/compiler-sfc` compileStyle, normalised) + vitest browser
  screenshots with a pngjs pixel compare, captured twice at BASE for stability. It gave hard evidence (CSS diff = one
  line; 14/14 SAME) and cost one Sonnet call. More tickets of this kind will come.
- **Suggested change:** move the two harness scripts (compiled-CSS diff, screenshot compare) to the workspace
  scripts dir (take the component list as arguments), and add to rc-orchestrate *Write the plan*: "A ticket with no
  behaviour change (style, rename) gets a `no-visual-change` cycle: BASE capture with the harness, then the change,
  then the same capture; the compare is the cycle's red/green."

### rc-manual-checks executor (Haiku): one wrong item (severity: low)

- **What happened:** the guide said a sent message shows the same overflow marker as the input area; sent messages render it differently. The
  orchestrator fixed the line. The brief named the sent-message rendering, but Haiku confused the two surfaces.
- **Suggested change:** in rc-orchestrate step 4, brief the guide writer with the component-to-surface map from the
  plan (which component renders where), or run it at Sonnet when the change spans more than one surface.

### rc-orchestrate step 2: three reviewers on a 45-line style-only diff (severity: low)

- **What happened:** Standards, Spec and Bugs each found 0 (about 95k tokens together). The harness evidence had
  already proved the CSS identical.
- **Suggested change:** allow one combined rc-reviewer (all three briefs in one prompt) when the diff is under ~100
  lines and touches no script or logic; keep three for everything else.

### rc-orchestrate backend check: +1 (codex probe exit 1 again; thirteenth claude-only run)

### Review log counts (all runs of the feature)

- Standards: 36 fixed, 6 deferred, 9 rejected (~15% rejected: not noisy). Spec: 13 fixed, 3 deferred, 1 rejected.
  Bugs: 10 fixed, 10 deferred, 1 rejected. Escaped: 3 in total. This run: 0 findings on every axis.

## 2026-11-03 — retro of an orchestrate run (backend ticket, move code between modules)

Gate B took 2 rounds of user changes (comment length; underscore rename).

1. **High · Coding standards (repeat class).** Two user asks at Gate B that review did not settle:
   - Underscore names imported across modules: the Standards reviewer DID report it (Nit); the orchestrator rejected
     it as "intentional" citing the ticket's "no rename". The user overrode it. A ticket rule written by the planner
     is not the user's answer to a convention conflict. Proposal (rc-orchestrate step 2, *Intent needs a source*):
     "When a finding is a repo/user convention and the only source against it is a ticket rule, put it on
     `Your call:`, never `rejected: intentional`." Mechanical part -> a check in the changed-files lint script: an
     added import line that imports a private (underscore) name from another module warns.
   - Moved constant comments 2-5 lines long where the file's other constants have one line or none. Judgement call ->
     rc-reviewer Standards brief: "For moved code, compare its comments with the destination file's norm (length,
     referents like 'the same X'), not with the source file."
   Escaped Standards lines across this feature's runs: 9 (mid-file constants x3, repeat/long comments x3, big-file
   growth x2, ternary x1) — the user-rule block in the brief helps but does not cover "match the destination".
2. **Medium · Navigation / recon for move tickets.** Recon grepped the usual patch targets but missed a log-capture
   filter by the logger NAME string; its logs-nothing test would have passed vacuously. The implementer caught it.
   Proposal: a small workspace script that, given the old module and the moved names, greps the four patch shapes
   (string target, `patch.object(mod, ...)`, `f'{MODULE}.…'` prefixes, logger-name strings / `caplog` filters) on HEAD
   and the development branch; point rc-explorer at it for any ticket that moves code between modules.
3. **Medium · Automated checks (repeat of the previous finding).** The backend test command was SIGKILLed (exit 137,
   container memory) 6 times in this run (implementer x2, fixer x2, orchestrator x2); each cost a re-run and an output
   that ends mid-line. Proposal: the script detects 137, prints `MEMORY KILL — not a test result`, and retries once
   when the container is under its memory limit.
4. **Low · Coding standards (good catch to keep).** The orchestrator found before the rename that the new name would
   shadow a local variable in 9 bodies and asked; the user chose a longer name. Proposal for the rename brief
   template: "grep the new name as a local/parameter before renaming."
5. **Low · Information access.** Codex probe failed again (cloud credentials) — third run in a row on the Claude
   fallback. The feature page was again not refreshed by the run.
