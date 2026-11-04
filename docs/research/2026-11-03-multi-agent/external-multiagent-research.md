# External research: orchestrating multiple coding agents (2025–2026)

Gathered 2026-11-03. Sources were fetched directly unless marked otherwise. The WebFetch tool returns a model-summarised view of each page, so "quotes" below are short phrases that the fetch reported as verbatim; spot-check any quote before you rely on its exact wording.

Labels used throughout:
- **[DOC]** documented product behaviour (official docs)
- **[DATA]** measured result reported by the source
- **[OPINION]** practitioner judgement or recommendation
- **[INFERENCE]** my reading of how a fact applies to our setup
- **[UNVERIFIED]** could not confirm against the primary source

---

## Part 1 — Sources

### A. Claude Code official docs (code.claude.com/docs, current as fetched 2026-11-03; pages carry no dates, only version notes)

#### A1. Subagents — https://code.claude.com/docs/en/sub-agents
- [DOC] Frontmatter fields: `name`, `description` (required); `tools`, `disallowedTools`, `model` (`sonnet|opus|haiku|fable|<id>|inherit`), `permissionMode` (`default|acceptEdits|auto|dontAsk|bypassPermissions|plan|manual`), `maxTurns`, `skills` (preload), `mcpServers`, `hooks`, `memory` (`user|project|local`), `background`, `isolation: worktree`, `omitClaudeMd`, `effort`, `autoCompactWindow`, `color`, `initialPrompt`. Unknown fields are silently ignored.
- [DOC] **Concurrency**: "when 20 subagents are running in a session, spawning another … fails with `Concurrent subagent limit reached`". You can change this with `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`. "There's no limit on the total number of subagents Claude can spawn over a session."
- [DOC] **Nesting**: subagents can spawn subagents "up to three layers below the main conversation" (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`). To prevent spawning, remove `Agent` from `tools`.
- [DOC] **Skills**: the `skills` field only preloads skills. "Subagents can still invoke unlisted project, user, and plugin skills through the Skill tool." To block skills, remove `Skill` from the subagent's tools. A skill with `disable-model-invocation: true` can't be preloaded.
- [DOC] **Permissions**: subagents "inherit the parent's permission rules". If the parent is in `bypassPermissions`, `acceptEdits` or auto, the subagent runs in that mode and its own `permissionMode` is ignored. Plugin subagents ignore `hooks`, `mcpServers` and `permissionMode`.
- [DOC] **Background vs foreground**: by default a subagent spawned from the main conversation runs in the background. In interactive sessions fork mode is on by default (from v2.1.302), which means Claude can't wait on a subagent unless `CLAUDE_CODE_FORK_SUBAGENT=0`. When a background subagent hits a permission prompt, Claude Code "surfaces the prompt in your main session and names the subagent that is asking."
- [DOC] Background subagents keep all MCP tools but only these built-ins: `Read, Grep, Glob, LSP, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage, Artifact` (+ `SubagentHandback`). Every subagent loses `AskUserQuestion`, `EnterPlanMode`, `ExitPlanMode` (unless in plan mode), `ScheduleWakeup`, `Workflow`.
- [DOC] **Context**: each subagent "starts with a fresh, isolated context window" and "doesn't see your conversation history". It starts with its system prompt, the delegation message, CLAUDE.md (except Explore/Plan), a git status snapshot, and any preloaded skills.
- [DOC] **Resume**: each invocation is a new instance. Claude resumes an earlier subagent with `SendMessage` to its ID or name, and the resumed agent has its full history. Transcripts live at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`. Subagents auto-compact on their own, and `autoCompactWindow` controls when.
- [DOC] **Worktree base**: `isolation: worktree` gives the subagent "an isolated copy of the repository branched by default from your default branch rather than the parent session's `HEAD`." If the subagent made no changes, the worktree is cleaned up automatically.
- [DOC] **Forks** (`/subtask`, or Agent tool fork) inherit the full conversation and share the parent's prompt cache. A fork's edits can go to a worktree via `isolation: "worktree"`. A fork can't spawn further forks.
- [DOC] Guidance: "Isolate high-volume work"; use the main conversation for "iterative work, shared multi-phase context".

#### A2. Agent teams — https://code.claude.com/docs/en/agent-teams
- [DOC] "experimental and disabled by default". Turn on with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. In `-p` / Agent SDK, "Claude doesn't spawn teammates".
- [DOC] When teams are enabled, an Agent call that passes a `name` launches a teammate, unless the call is a fork or passes `isolation`. The docs warn "teams can form even when you didn't ask for one."
- [DOC] Architecture: a lead, teammates, a shared task list at `~/.claude/tasks/{team}/`, and mailboxes at `~/.claude/teams/{team}/inboxes/{agent}.json`. "Task claiming uses file locking to prevent race conditions." Tasks have pending, in-progress and completed states plus dependencies. "Teammates don't self-claim a blocked task". Dependents unblock automatically.
- [DOC] Communication: messages are delivered automatically and "the lead doesn't need to poll". When a teammate goes idle, it notifies the lead and includes its final answer. There is no broadcast: "send one message per recipient."
- [DOC] **Permissions**: "Teammates start with the lead's permission mode, except `dontAsk`". "Teammate permission prompts appear in the lead session". A teammate can't have its own mode at spawn time, only after.
- [DOC] **Approvals can't be relayed**: "A teammate can't approve a permission prompt or supply consent on your behalf, and a teammate that was denied an action can't relay it to another teammate to bypass the check." In auto mode, the classifier "treats an approval claim relayed from another agent as untrusted input".
- [DOC] **Skills**: teammates load skills from project and user settings. The `skills` field of a subagent definition is NOT applied to teammates. Plain text and skills typed by the user while viewing a teammate go to that teammate.
- [DOC] **Isolation**: "Agent teams don't isolate teammates in worktrees" (from agents.md). The guidance is to "Break the work so each teammate owns a different set of files."
- [DOC] **Hooks**: `TeammateIdle`, `TaskCreated` and `TaskCompleted`. Exit code 2 on each of these keeps the teammate working, blocks the task's creation, or blocks its completion.
- [DOC] Limitations: in-process teammates aren't restored after `/resume`; "Task status can lag"; one team per session; no nested teams; a teammate can't run background subagents; the lead is fixed for its lifetime.
- [OPINION/DOC guidance] "Start with 3-5 teammates"; "5-6 tasks per teammate"; "Three focused teammates often outperform five scattered ones." Start with research and review before parallel implementation. The lead sometimes "starts implementing tasks itself instead of waiting", and it can also "stop early".

#### A3. Cross-session messaging — https://code.claude.com/docs/en/cross-session-messaging
- [DOC] Requires v2.1.224+ (macOS/Linux) and is on by default. Tools: `ListAgents` (discover) and `SendMessage` (send). `/list-agents` (alias `/peers`) shows what this session can reach.
- [DOC] A message is "a piece of text … never the sender's conversation history or files." It is plain text only, with a cap of about 1M characters. Bursts are refused at the sender. On the receiving side the inbox queues at most 50 accepted messages, rate-limits per sender, and drops identical repeats.
- [DOC] Delivery: the receiver reads the message "between tool calls during an active turn". If the receiver is idle, the message starts a new turn, which counts toward usage. `notify_when_idle` (v2.1.236+) asks a session for one notice when it goes idle or exits. Subscriptions expire after 12 hours, and only the main conversation can subscribe, and only to local sessions.
- [DOC] **What a peer message can't do**: "It can't approve anything … can't answer a pending permission prompt on your behalf". "It can't change configuration". "**Commands don't run**: a command in the message's text, such as `/compact`, arrives as plain text. Claude Code never executes it." "Permission prompts still fire".
- [DOC] Claude "is instructed never to ask another session for an action that was denied or blocked in its own session … and to route that work back to you instead."
- [DOC] Inbound control `crossSessionInbound`: `accept|hold|refuse`. The default depends on permission mode. A bypassing receiver holds messages from prompting senders for approval, and a held message expires after `dialogExpiry` (5 minutes by default). A `claude -p` worker does bind an inbox, so "start it with `crossSessionInbound` set to `accept` in its `--settings` value" to let it take messages unattended. `--bare` sessions bind no inbox.
- [DOC] Hooks and scripts can post into their own session via `CLAUDE_CODE_MESSAGING_SOCKET` and `CLAUDE_CODE_MESSAGING_TOKEN`. A message from the session's own child processes is delivered even when no `crossSessionInbound` setting applies.
- [DOC] A session in a container can't reach one on the host.

#### A4. Worktrees — https://code.claude.com/docs/en/worktrees
- [DOC] `claude --worktree <name>` (`-w`) creates `.claude/worktrees/<name>/` on branch `worktree-<name>`. The `EnterWorktree` / `ExitWorktree` tools do the same mid-session. Removing `permissions.blockWritesOutsideWorkingDirectories` brings those tools back if they're missing.
- [DOC] **Base ref** (`worktree.baseRef`): `"fresh"` (the default) means "branch from the repository's default branch on the remote". `"head"` means branch from the current local HEAD. You can't name a branch. For `fresh`, Claude Code fetches only "When the repository hasn't been fetched in the last 24 hours", with a 5-second cap, and otherwise "uses the locally cached ref". **So a new worktree can start from an origin/main that is up to 24 hours stale.**
- [DOC] A reopened worktree resets to the default branch only if it is clean, still on its own branch, and has no commits of its own (or its PR was merged and the remote branch deleted).
- [DOC] **Isolation enforcement**: Claude Code blocks Edit/Write into the main checkout, Bash run from the main checkout's cwd, and git redirects (`-C`, `GIT_DIR`, etc.). It also refuses commands it can't parse. It does **not** track files that a `cp` or a shell redirect writes into the main checkout.
- [DOC] Shared with the main checkout: `.git`, project-scope plugins, and **permission approvals**. "Yes, and don't ask again" in a worktree saves to the main checkout's `.claude/settings.local.json`, so it applies to all worktrees. When the worktree has no `.claude/skills|agents|commands` of its own, the untracked ones are read through from the main checkout.
- [DOC] `.worktreeinclude` (gitignore syntax) copies gitignored files such as `.env` into new worktrees. `worktree.symlinkDirectories` is for large directories (best-practices page).
- [DOC] Hooks: `${CLAUDE_PROJECT_DIR}` stays at the original root, and the hook's `cwd` input field follows the worktree. `WorktreeCreate` / `WorktreeRemove` hooks replace the git logic.
- [DOC] Cleanup: `claude -p --worktree` runs are never cleaned up automatically. "Use `git worktree remove`", and `git worktree unlock` it first if needed. Claude Code holds a `git worktree lock` while an agent is running.

#### A5. Run agents in parallel (overview) — https://code.claude.com/docs/en/agents
- [DOC] There are five approaches: subagents, agent view (background sessions; research preview), agent teams (experimental), dynamic workflows, and Projects (cloud; public beta). `/batch` is "a skill that has Claude split one large change into 5 to 30 worktree-isolated subagents".
- [DOC] Decision axes: who coordinates, whether the workers need to talk, and whether they touch the same files. "Subagents report results back to the conversation that spawned them, and agent view sessions report results only to you."

#### A6. Background sessions / agent view — https://code.claude.com/docs/en/agent-view
- [DOC] `claude --bg "<prompt>"`, `claude agents`, `claude attach|logs|stop|respawn|rm <id>`. `--bg` is rejected together with `-p`.
- [DOC] Before it edits anything, a dispatched background session "moves the session into an isolated git worktree under `.claude/worktrees/`" (`worktree.bgIsolation`). Before it finishes, it is told to "commit and push without asking … Never push to `main` or `master`, force-push, or merge."
- [DOC] Permission prompts put the session in `Needs input`. "Replying in the peek panel does not answer a permission prompt … attach with `→`." A held cross-session message also shows on the row as `approve message from`.
- [DOC] Scripting interface: "poll `claude agents --json --all` and read `state`, `status`, and `waitingFor`." `state` values: `working|blocked|done|failed|stopped`. "The files under `~/.claude/jobs/<id>/` are not a stable interface."
- [DOC] Idle, unattached sessions are stopped after about an hour, and pinning one (`Ctrl+T`) keeps it alive. The `Notification` hook fires `agent_needs_input` and `agent_completed`.
- [DOC] Limits: "running ten agents in parallel uses quota roughly ten times as fast"; sessions are local.

#### A7. Dynamic workflows — https://code.claude.com/docs/en/workflows
- [DOC] A workflow is a JS script with `agent()`, `pipeline()`, `parallel()`, `phase()` and `log()`. In a workflow, "the script" decides what runs next, and intermediate results "live in script variables", so "Claude's context holds only the final answer". A run can be resumed within the same session.
- [DOC] Limits: "Up to 16 concurrent agents by default" (`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` 1–256), 1,000 agents per run, and a `Large workflow` warning above 25 agents or 1.5M tokens.
- [DOC] "**No mid-run user input** … For sign-off between stages, run each stage as its own workflow." In `claude -p` there is no approval prompt, so allow `Workflow` with a rule.
- [DOC] In auto mode, the prompt a script passes to `agent()` "doesn't count as a request from you".

#### A8. Hooks — https://code.claude.com/docs/en/hooks
- [DOC] Coordination-relevant events: `SubagentStart` (adds context only), `SubagentStop` (exit 2 prevents the stop), `Stop` (exit 2 makes Claude keep working; input includes `last_assistant_message`), `TeammateIdle`, `TaskCreated`, `TaskCompleted` (all blockable), `Notification` (side effects only), `PermissionRequest` (allow/deny via `hookSpecificOutput.decision.behavior`; exit 2 not honoured), `WorktreeCreate` / `WorktreeRemove`, `PreCompact` (exit 2 blocks compaction), `SessionStart`, `SessionEnd`, `PostToolBatch`, `FileChanged`.

#### A9. Headless — https://code.claude.com/docs/en/headless
- [DOC] `claude -p`: `--output-format json|stream-json`. JSON output includes `session_id`, `total_cost_usd` and a per-model cost breakdown. `--json-schema` returns `structured_output`. `--resume <id>` and `--continue`.
- [DOC] "User-invoked skills and custom commands work. Include `/skill-name` in the prompt string". `--bare` skips skills, hooks, CLAUDE.md and MCP, and is "recommended … will become the default for `-p`".
- [DOC] Since v2.1.302, `-p` starts in Manual mode. A call that needs approval is denied unless a `PermissionRequest` hook or `--permission-prompt-tool` approves it. `--permission-prompts none` (v2.1.259+) denies without waiting.
- [DOC] Stream subagent messages with `--forward-subagent-text`; `parent_tool_use_id` links each one to its tree.

#### A10. Skills — https://code.claude.com/docs/en/skills
- [DOC] With `disable-model-invocation: true`, Claude can invoke the skill "Not on its own", and "Claude Code blocks the call". Only the user typing `/name` runs it.
- [DOC] With `user-invocable: false`, only Claude can invoke the skill.
- [DOC] `context: fork` plus `agent:` runs the skill in a subagent, and `background` defaults to true. `allowed-tools` grants permission only "during the turn that invokes this skill. The grant clears when you send your next message."

#### A11. Best practices — https://code.claude.com/docs/en/best-practices
- [OPINION/official] Before running unattended, ask: does it know what done is, can it check itself, what can it touch, what stops it (`--max-turns`, `--max-budget-usd`), and "who signs off?"
- [OPINION/official] A fresh reviewer helps "because it hasn't seen your reasoning", but delegating "doesn't make the answer any better". On subagents: "a fresh subagent first has to gather context … so it can end up slower".
- [OPINION/official] Treat context as "Running out of context is rarely the problem anymore" (1M windows), and `/clear` between tasks is still worth doing.

#### A12. Costs — https://code.claude.com/docs/en/costs
- [DOC/DATA] "Agent teams use approximately 7x more tokens than standard sessions when teammates run in plan mode." Advice: use Sonnet for teammates, keep teams small, keep spawn prompts focused, and shut teammates down.
- [DOC] A cross-session message that wakes an idle session sends that session's full context, so use `hold` if this matters. `/usage` attributes usage by subagent and skill.

#### A13. Projects (cloud coordinator) — https://code.claude.com/docs/en/claude-projects
- [DOC] The coordinator conversation "sees what threads report back, not every step they take" and "works from recent messages, recent threads, and project memory rather than its full history".
- [DOC] Thread states: Ready for review, **Waiting on you**, Working, **Landing** (PR approved or queued to merge).
- [DOC] **Approvals are per-thread**: "When a thread needs your approval, the prompt is inside that thread … Telling Claude in the project conversation to go ahead doesn't reach it."
- [DOC/OPINION] Recommended setup: ask Claude to "propose threads before starting them and to run a few at a time", then drop those limits once threads come back the way you want. There is a hard limit of 500 threads/day.

### B. Anthropic engineering posts

#### B1. "How we built our multi-agent research system" — https://www.anthropic.com/engineering/multi-agent-research-system — 2025-06-13
- [DATA] An Opus 4 lead with Sonnet 4 subagents beat single-agent Opus 4 by "90.2%" on their internal research eval. Token usage explains 80% of the variance on BrowseComp. Multi-agent runs use "about 15× more tokens than chats".
- [OPINION] Poor fits: domains needing "all agents to share the same context" and many dependencies, which includes most coding.
- [Practice] Each subagent gets an objective, an output format, tool and source guidance, and clear task boundaries. Effort scales with complexity (1 agent and 3–10 calls for simple work, 10+ subagents for complex work). Failure mode: "50 subagents for simple queries" plus duplicated work.
- [Practice] Subagents write their outputs to external storage and pass "lightweight references back to the coordinator", which avoids a "game of telephone". The lead saves its plan to memory before its context is truncated. Phases are summarised and fresh subagents are spawned.
- [DATA/limit] The lead runs subagents synchronously, so the slowest one blocks.
- [Practice] Start evals with about 20 cases, use an LLM judge with a single-prompt rubric, keep human testing, and add full tracing. Errors compound, so resume from checkpoints. Use rainbow deploys.

#### B2. "Effective context engineering for AI agents" — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — 2025-09-29
- [Practice] A subagent "returns only a condensed, distilled summary", often 1,000–2,000 tokens. Other practices: compaction, structured note-taking outside the context, and just-in-time retrieval by reference. Context rot is real.

#### B3. "Effective harnesses for long-running agents" — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents — 2025-11-26
- [Practice] An initializer agent sets up the environment. The coding agents then keep `claude-progress.txt` and a JSON feature list in which only the `passes` field may change ("It is unacceptable to remove or edit tests"). They work on one feature per session, commit as checkpoints, and leave code "appropriate for merging to a main branch". Each session starts the same way: pwd, git log, progress file, feature list, `init.sh`, and a smoke e2e test.
- [DATA/observed] Failure modes: one-shotting the whole app, declaring victory early, marking features done without e2e tests, and leaving the environment broken for the next session.
- [OPINION] Whether multi-agent beats one general agent is an open question. Specialised QA or cleanup agents are suggested as future work.

#### B4. "Harness design for long-running application development" — https://www.anthropic.com/engineering/harness-design-long-running-apps — 2026-03-24
- [Practice] Roles are planner, generator and evaluator. The evaluator uses Playwright to click through the app. A **sprint contract** is negotiated before coding: "The generator proposed what it would build and how success would be verified". Agents hand off through files.
- [DATA/OPINION] Agents "confidently prais[e] the work". "tuning a standalone evaluator to be skeptical turns out to be far more tractable". "Claude is a poor QA agent" out of the box, so the evaluator had to be tuned by reading its logs.
- [DATA] Solo run: 20 min, $9. Full harness: 6 h, $200 ("over 20x"). Updated harness: 3 h 50 min, $124.70.
- [OPINION] "every component in a harness encodes an assumption about what the model can't do on its own". As models improved, sprints, context resets and per-sprint evaluation were removed; the planner and evaluator were kept.

#### B5. "Building a C compiler with a team of parallel Claudes" — https://www.anthropic.com/engineering/building-c-compiler — 2026-02-05 (Nicholas Carlini)
- [DATA] 16 agents, about 2,000 sessions over about 2 weeks, just under $20k, a ~100k-line Rust C compiler that builds Linux 6.9.
- [Practice] Each agent ran in its own container with a clone of a bare upstream repo. Agents claimed tasks by writing a lock file to `current_tasks/`, and git's push conflicts settled races. The cycle was pull, merge, push, release the lock. "I don't use an orchestration agent." Merge conflicts were frequent and Claude handled them.
- [Practice] Test output was kept short and logs went to files with grep-able tags. A `--fast` random test subset made up for the model's poor sense of time. READMEs and progress files oriented fresh contexts. Some agents were specialists (dedup, perf, docs, Rust-quality reviewer).
- [DATA/lesson] Parallelism collapsed when every agent hit the same bug (the kernel build), and they overwrote each other's fixes. The fix was a GCC oracle that split the failing surface so agents could work on different bugs. CI was added late, after regressions. "tests passing does not guarantee the work is done."

### C. Counterpoints and other practitioners

#### C1. Cognition, "Don't Build Multi-Agents" — https://cognition.com/blog/dont-build-multi-agents — 2025-06-12 (Walden Yan)
- [OPINION] Principles: "Share context" (full traces, not just messages) and "Actions carry implicit decisions". The Flappy Bird example: subagents produced a mismatched background and bird. Recommends a single-threaded linear agent, with a context-compression model for long tasks.
- Note: this predates the current Claude Code. Its claim that Claude Code subagents don't run in parallel and don't write code is out of date ([DOC] A1).

#### C2. Cognition, "Devin can now Manage Devins" — https://cognition.com/blog/devin-can-now-manage-devins — 2026-03-19
- [DOC/product] The coordinator "scopes the work", assigns pieces, monitors, "resolves any conflicts", and compiles the results. Each worker is "running in its own isolated virtual machine" with "a clean slate, a narrow focus, its own shell, and its own test runner". The coordinator can message workers mid-task and read their trajectories. Example prompt: "one session per service or package (10 at a time)". No merge mechanism is described.

#### C3. Cognition, "Multi-Agents: What's Actually Working" — https://cognition.com/blog/multi-agents-working — 2026-04-22 (Walden Yan)
- [OPINION] Multi-agent works when "writes stay single-threaded" and extra agents "contribute intelligence rather than actions". Parallel-writer swarms still don't work, and unstructured swarms are "mostly a distraction".
- [DATA] Devin Review: "an average of 2 bugs per PR", about 58% severe. The reviewer works best with clean context ("only look at the diff"). The coder uses its wider context of the user's instructions to filter the findings, which avoids loops and out-of-scope work.
- [OPINION] Manager/worker problems: managers are "overly prescriptive", and agents "assume they share state with their children when they don't". The open problems are about communication: how children surface discoveries that affect siblings, and how to transfer context without overwhelming the receiver.

#### C4. Cursor, "Scaling long-running autonomous coding" — https://cursor.com/blog/scaling-agents — 2026-01-14 (Wilson Lin)
- [DATA] Flat self-coordination through a locked shared file failed: "Twenty agents would slow down to the effective throughput of two or three." Optimistic concurrency was better but agents became risk-averse and avoided hard tasks.
- [Practice] Planners (recursive) create tasks. Workers "don't coordinate with other workers". A judge decides whether to continue, and every cycle starts fresh. Models are chosen per role.
- [OPINION] An integrator role "created more bottlenecks", because workers could resolve conflicts themselves. "Too little structure and agents conflict, duplicate work, and drift. Too much structure creates fragility." "the prompts matter more."

#### C5. Cursor, "Towards self-driving codebases" — https://cursor.com/blog/self-driving-codebases — 2026-02-05
- [DATA] About 1,000 commits/hour at peak and 10M tool calls in a week.
- [Practice] A single executor that planned, spawned and merged was "given too many roles", so the final design has a root planner that "does no coding itself", subplanners, and workers. Each worker returns one handoff to its planner. `scratchpad.md` is "frequently rewritten versus being appended to".
- [OPINION] Requiring 100% correctness before every commit serialised the system, so they accepted a small error rate and propose a periodic "green" branch with a fixup pass. Constraints ("No TODOs, no partial implementations") work better than reminders, and concrete numbers ("20-100 tasks") help. Disk I/O from parallel compiles became a bottleneck.

#### C6. Simon Willison, "Embracing the parallel coding agent lifestyle" — https://simonwillison.net/2025/Oct/5/parallel-coding-agents/ — 2025-10-05
- [OPINION] "the natural bottleneck on all of this is how fast I can review the results". "I can only focus on reviewing and landing one significant change at a time." Parallelise research, explanations, small maintenance, and work you've specified exactly. Run in containers when using YOLO mode.

#### C7. OpenAI Codex subagents — https://learn.chatgpt.com/docs/agent-configuration/subagents (redirected from developers.openai.com/codex/concepts/subagents; undated)
- [DOC] "use parallel agents for read-heavy tasks such as exploration, tests, triage, and summarization". "Be more careful with parallel write-heavy workflows, because agents editing code at once can create conflicts." Subagents run only when explicitly asked.
- [DOC] "Subagents inherit your current sandbox policy", and custom agents can't override it. In non-interactive runs, an action that needs new approval fails and the error goes back to the parent. Concurrency is capped with `agents.max_concurrent_threads_per_session` (legacy `agents.max_threads`).

#### C8. OpenAI, "Harness engineering: leveraging Codex in an agent-first world" — https://openai.com/index/harness-engineering/ — 2026-02-11 (Ryan Lopopolo)
- [UNVERIFIED] openai.com returned 403. Secondary sources (InfoQ https://www.infoq.com/news/2026/02/openai-harness-engineering-codex) report about 1M lines and about 1,500 PRs over 5 months with no hand-written code. They also report that the repo is the agent's system of record, with the quote "anything it can't access in-context while running effectively doesn't exist", and a short AGENTS.md that points to deeper docs. From memory, the post also argued for minimal blocking merge gates and app instances bootable per worktree; **I could not verify this**.

#### C9. GitHub merge queue docs — https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
- [DOC] Each queued PR is tested on a temporary branch made of the latest base plus the PRs ahead of it (`merge_group`), and CI must trigger on `merge_group`. Authors don't have to rebase. A failing PR is removed and the group is rebuilt without it. Build concurrency can be 1–100. There is an option to merge non-failing PRs only.

#### C10. mergetrain (PyPI) — https://pypi.org/project/mergetrain/
- [OPINION/vendor] A local merge queue for worktree agents. A runner builds an integration worktree, merges queued branches FIFO, runs gates once per train, then pushes. Agents get no push credential. Seen only through search snippets; not otherwise verified.

### D. Research

#### D1. Cemri et al., "Why Do Multi-Agent LLM Systems Fail?" (MAST) — https://arxiv.org/abs/2503.13657 (v3 2025-10-26; NeurIPS 2025)
- [DATA] 14 failure modes in 3 groups, from about 1,600 traces across 7 frameworks. Failure rates were 41–86.7%.
  - System design, about 44%: disobeys task spec 11.8%, step repetition 15.7%, unaware of termination 12.4%, loss of history 2.8%, disobeys role 1.5%.
  - Inter-agent misalignment, about 32%: reasoning-action mismatch 13.2%, task derailment 7.4%, fails to ask for clarification 6.8%, conversation reset 2.2%, ignores other agent's input 1.9%, withholds information 0.85%.
  - Task verification, about 24%: incorrect verification 9.1%, no or incomplete verification 8.2%, premature termination 6.2%.
- [DATA] Interventions: clearer role specs gave +9.4%, and a high-level objective verification step gave +15.6%. Verifiers often check only that the code compiles. The paper recommends multi-level verification.

#### D2. Google Research, "Towards a science of scaling agent systems" — https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/ — 2026-01-28 (arXiv 2512.08296)
- [DATA] 180 configurations. Parallelisable task: centralised coordination +80.9%. Sequential task: "every multi-agent variant … degraded performance by 39-70%". Independent agents "amplified errors by 17.2x", centralised ones 4.4x. The coordination "tax" grows disproportionately with tool count.
- [UNVERIFIED] The "45% capability threshold" is cited only by secondary sources.

---

## Part 2 — Synthesis

### 1. When multi-agent beats single-agent for coding, and when it doesn't
- **Beats it** when the units are genuinely independent and each can be verified on its own: separate tickets touching disjoint files, independent failing tests, or per-file migrations ([DATA] D2 +81% on parallelisable work; B5 independent tests; C4/C5). Multi-agent also helps for **review by a fresh agent**, which is the most consistently positive multi-agent pattern ([DATA] C3; [OPINION] A11, B4).
- **Loses** on sequential or tightly coupled work, where variants were −39% to −70% (D2), and where many workers converge on the same bug (B5 kernel). It also loses when workers make implicit design decisions that must agree (C1, C3) and when tool-heavy agents pay a coordination tax (D2). Cost runs about 4–15× or more (B1 15× vs chat; A12 7× for plan-mode teams; B4 over 20×).
- **Consensus as of 2026** (opinion, but it converges across Anthropic, Cognition, Cursor and OpenAI): use one coordinator with isolated workers that each own a disjoint write scope. Any cross-worker integration goes through a single serialised path. Peer swarms and parallel writers on shared code do not work well (C3, C4, C5, D2 centralised 4.4× vs independent 17.2×).
- **[INFERENCE] For us**: parallelising ticket implementation across worktrees fits these findings, but only if the tickets have disjoint write sets. Two tickets that touch the same module should be run sequentially, not "merged later".

### 2. Decomposition and dependency handling
- Decompose into self-contained units that each produce a clear deliverable and can be verified on their own ([DOC] A2 sizing; B3 one feature per session). Agent teams' docs suggest "5-6 tasks per teammate" with 3–5 teammates ([OPINION/DOC]).
- Model dependencies explicitly. Agent-team tasks support `blocked` dependencies that unblock automatically ([DOC] A2). The rule there is the one to copy: no worker self-claims a blocked task.
- Workers should not coordinate with each other. Planners plan and workers execute (C4, C5). A coordinator that also implements gets overloaded (C5) or stops waiting for its workers ([DOC] A2 "starts implementing tasks itself").
- Agree on a "done" contract before coding: sprint contracts (B4), a JSON feature list whose tests can't be edited (B3), failing tests as the spec. This matches our test-first pipeline.
- When everything fails on one shared blocker, split the failure surface with an oracle rather than throwing more agents at it (B5).
- Concrete numbers and hard constraints in planner prompts work better than vague exhortations (C5).

### 3. Context sharing vs isolation
**What to pass a worker** (the brief is the worker's only context; [DOC] A1, A2, A3): the objective, the output format, the task boundaries (which files it owns and which it must not touch), the tools and commands to use, the verification command, and pointers to the files that define the spec. Use references (paths, ticket file, commit SHA), not pasted content (B1, B2). Include the implicit decisions that siblings depend on, such as interfaces, naming and schema, because "Actions carry implicit decisions" (C1, C3). Keep the brief focused, since everything in it costs tokens from turn one ([DOC] A12).

**Isolation** is useful for reviewers: give them the diff and the spec, not the coder's reasoning (C3, A11, B4).

**Keeping the coordinator small**:
- Workers return condensed summaries of about 1–2k tokens (B2) and write details to files that the coordinator reads only on demand (B1).
- Move orchestration state out of the coordinator's context and into files: a progress file and ticket statuses (B3), or a script (A7 workflows keep intermediate results "in script variables").
- Projects' coordinator "works from recent messages, recent threads, and project memory rather than its full history" ([DOC] A13). That is a model for ours: keep a durable status file as the source of truth and treat the conversation as disposable.
- Rewrite the scratchpad rather than appending to it (C5). Use `PreCompact` or `SessionStart` hooks to re-inject the status file after compaction ([DOC] A8; [INFERENCE]).
- Be aware that each delivered `SendMessage` to an idle coordinator starts a turn and re-sends its full context ([DOC] A12). Batch worker reports instead of sending a stream of pings: the inbox refuses bursts and suggests batching ([DOC] A3).

### 4. Coordinating shared resources
**Merge order, integration branch, stale bases**
- [DOC] Claude-created worktrees branch from the remote default branch, refreshed only if the last fetch is older than 24 hours ([DOC] A4). Subagent worktrees do NOT start from the coordinator's HEAD unless `worktree.baseRef: "head"` is set ([DOC] A1). **[INFERENCE] This is a likely contributor to our stale-base pain.** Run `git fetch` explicitly before creating worktrees, or create them yourself with `git worktree add <path> origin/main` after a fetch, and rebase or merge at land time rather than at start.
- Serialise integration through one path: a merge-queue pattern that tests each candidate on base + everything ahead of it and evicts and rebuilds on failure ([DOC] C9; [OPINION] C10). Don't make each worker rebase repeatedly against a moving main. That is exactly the problem merge queues remove ([DOC] C9).
- Cursor found that a dedicated integrator agent became a bottleneck and let workers resolve their own conflicts (C4, C5). Carlini's agents also merged themselves (B5). **[INFERENCE] With one merge slot and human approval per ticket, a single landing lane is still right.** Keep the lane mechanical: fetch, rebase or merge onto the latest main, rerun the tests, then present the result to the human. Send conflicts back to the owning worker rather than having the coordinator resolve them.
- An optional pattern is to accept a small error rate on the integration branch and keep a periodic "green" snapshot with a fixup pass (C5) [OPINION]. With a per-ticket human approval gate this is probably not appropriate for main, but it can work for an integration branch.

**Locks and slots for local resources (DB, ports, browser, status page)**
- File-lock task claiming is documented in agent teams ([DOC] A2) and was used by Carlini through lock files plus git (B5). Cursor's flat lock coordination degraded to 2–3× effective throughput from 20 agents, mainly because locks were held too long or never released (C4). **[INFERENCE]** Hold locks only around the critical section (a manual browser check, a DB migration, a merge), give each lock a TTL and an owner, and release it in a `Stop` or `SubagentStop` hook.
- Give each worktree its own ports and DB where possible (`.worktreeinclude` env files with per-worktree ports; `WorktreeCreate` hook to provision them) ([DOC] A4) so fewer resources are shared at all. [UNVERIFIED] OpenAI reportedly made the app bootable per worktree (C8).
- Have a single writer for the shared status page: the coordinator, or a script fed by `claude agents --json` ([DOC] A6). Workers send status rather than editing the page.

### 5. Communication protocols and status reporting
- [DOC] Cross-session `SendMessage` is plain text, ≤ about 1M characters, delivered between tool calls or as a new turn. Bursts are refused, and the inbox holds at most 50 queued messages. `notify_when_idle` gives one completion notice (main conversation only, local sessions only, 12-hour expiry). A `-p` worker needs `crossSessionInbound: accept` to receive messages unattended, and `--bare` workers can't receive at all ([DOC] A3).
- [DOC] Agent-team teammates automatically notify the lead with their final answer when they go idle. Subagents return their result to the caller. `TeammateIdle`, `TaskCompleted` and `SubagentStop` hooks can enforce "don't stop until X is true" ([DOC] A2, A8).
- [DOC] For scripted status, poll `claude agents --json --all` (`state`, `status`, `waitingFor`). Don't read `~/.claude/jobs` ([DOC] A6). For `-p` workers, use `--output-format json` (`session_id`, `total_cost_usd`, `structured_output` with `--json-schema`) ([DOC] A9).
- Practices: use a fixed report schema (status, branch, SHA, tests run and result, files touched, open questions, blocked-on) ([INFERENCE] from B1 output-format guidance and A9 json-schema). Reply with a terse `OK/FAIL` plus a pointer to a file (A11). Hand off through files when the payload is large (B4, B1).
- Peer messages can't carry consent or run commands. A `/skill` in a message "arrives as plain text" ([DOC] A3). The receiving Claude can still call the Skill tool itself, unless the skill has `disable-model-invocation: true`, in which case only a human typing `/name` can launch it ([DOC] A10). **[INFERENCE] This likely explains our "skills that couldn't be launched by a peer".** Make the worker-side pipeline skills model-invocable, or launch workers as `claude -p "/skill-name …"` (user-invoked skills expand in `-p`; [DOC] A9), or define the worker as a subagent with preloaded `skills:`. Note that the `skills` field is ignored for teammates ([DOC] A2).

### 6. Failure modes and mitigations
| Failure | Source | Mitigation |
|---|---|---|
| Conflicting implicit decisions between parallel writers | C1, C3 | Disjoint write scopes; pin shared interfaces in the brief; sequence coupled tickets |
| Everyone converges on the same bug and they overwrite each other | B5 | Detect shared blockers; split with an oracle; assign one owner |
| Lock contention / locks never released | C4 | Short-lived, TTL'd locks; optimistic concurrency; release in hooks |
| Risk-averse workers churn on easy tasks | C4 | Planner assigns the work; workers don't self-select |
| Coordinator overloaded / starts implementing / stops early | C5, A2 | Coordinator does no coding; explicit "wait for workers"; `Stop` hook gate |
| Premature "done" / self-praise / superficial verification | B3, B4, D1 (FC3 ~24%) | Independent skeptical reviewer; executable acceptance tests; high-level objective check (+15.6% in D1) |
| Step repetition, unaware of termination | D1 (15.7%, 12.4%) | Explicit termination conditions; `maxTurns` / `--max-budget-usd`; judge that decides whether to continue (C4) |
| Context drift and tunnel vision on long runs | C4, C5, B4 | Fresh workers per ticket; rewrite scratchpads instead of appending; progress files |
| Status lags (task not marked complete) | A2 | `TaskCompleted` / `SubagentStop` hooks; coordinator checks git state, not only the reported state |
| Stale base at integration | A4 (24 h cache) | Explicit fetch; merge-queue style test-on-latest; rebase at land time |
| Errors compound in stateful agents | B1 | Checkpoint commits; resume rather than restart (B3) |
| Agents assume they share state with their children | C3 | State everything explicitly in the brief; nothing is inherited ([DOC] A1, A2) |
| Silent work in the main checkout via `cp` or a shell redirect | A4 | Isolation checks don't track such writes; sandbox or permissions needed |

### 7. Human-in-the-loop at scale
- **Documented facts about approvals**:
  - Approval prompts belong to the session or thread that raised them. A message from another agent or session "never counts as your consent" ([DOC] A2, A3).
  - In Projects, "Telling Claude in the project conversation to go ahead doesn't reach" a thread waiting on approval ([DOC] A13).
  - Background subagents' prompts surface in the main session with the subagent named ([DOC] A1). Teammates' prompts surface in the lead ([DOC] A2). Background sessions need you to attach to answer ([DOC] A6).
  - A skill's `allowed-tools` grant ends when the user's next message arrives ([DOC] A10).
  - "Don't ask again" approvals in a worktree persist to the main checkout's `settings.local.json`, so they are shared across all worktrees ([DOC] A4).
- **[INFERENCE] Implications for our setup**: an approval typed in the coordinator can't be forwarded to a worker as consent. That is by design, so don't build on relaying "approved" text. Choose one of these instead:
  - (a) Pre-approve the routine tool calls through permission rules or auto mode before you dispatch ([DOC] A2 "Pre-approve common operations").
  - (b) Keep the human-gated action (the commit or merge) in the session where the human types. The coordinator, or a landing lane the human attaches to, performs the commit after the human says yes there.
  - (c) Use subagents or teammates, whose prompts already surface in the lead session where the human is.
- **Batching**: the review bottleneck is the human (C6: "how fast I can review"). Queue completed tickets in a "Ready for review" state and present them one at a time with a short diff tour. Use states like Projects' Ready for review / Waiting on you / Landing (A13), or agent view's Needs input / Ready for review groups (A6). A merge queue lets the human approve several tickets that then land serially with retests (C9).
- Start with few concurrent workers and require plans before starting; widen once the results look right ([OPINION/DOC] A13, A2 "Start with research and review"). Before running unattended, apply the five-question checklist ([OPINION/official] A11).

### 8. Observability and cost
- Cost multipliers: about 15× vs chat for multi-agent research (B1); about 7× for plan-mode agent teams (A12); over 20× for the full harness vs a solo run (B4); "roughly ten times" the quota for 10 background sessions (A6). Budget per ticket with `--max-budget-usd` or `--max-turns` (A9, A11).
- [DOC] Measurement: `/usage` attributes usage by subagent and skill (A12). `-p` JSON reports `total_cost_usd` per run (A9). OpenTelemetry export gives per-user, near-real-time metrics (A12). `/workflows` shows per-agent token use (A7). Subagent transcripts are on disk at a known path (A1), and `--forward-subagent-text` plus `parent_tool_use_id` lets you rebuild the agent tree (A9).
- [DOC] Cache: subagent, teammate and workflow-agent caches last 5 minutes unless `subagentPromptCacheTtl: "1h"` is set (A2, A7). Forks share the parent's cache (A1). Workflow fan-outs stagger starts so siblings can read a shared prefix (A7).
- [Practice] Trace decisions, not only outcomes (B1). Read the reviewer or evaluator logs to calibrate them (B4). Start evals small, about 20 cases (B1).
- [DATA] Infrastructure contention (disk I/O from parallel builds) can become the bottleneck before tokens do (C5).

---

## Unverified or caveated items
- OpenAI "Harness engineering" (C8): the primary page returned 403. Every detail beyond the InfoQ and The Neuron summaries is unverified, including per-worktree booting and merge philosophy.
- Google's "45% threshold" (D2): secondary sources only.
- mergetrain (C10): seen only through PyPI search snippets; vendor claims.
- Contrary Research's claim that Devin's manager handles "up to ten workers" with automatic merging: the primary post shows only a user-chosen "10 at a time".
- Anthropic research-system quotes about coding being a poor fit come from a summarising fetch, so the exact wording was not seen.
- Claude Code docs change quickly, and many behaviours are version-gated (v2.1.2xx–2.1.31x). Check `claude --version` against the version notes cited in A1–A13.
