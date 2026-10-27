# claude-skills

My portable Claude Code setup. Clone it on a new laptop and run one script to
link my own global skills and sub-agents. Third-party skills and plugins are
listed in `manifest/` but installed by hand.

```bash
git clone <this-repo-url> claude-skills
cd claude-skills
./install.sh
```

`install.sh` is idempotent — safe to re-run. It only adds things.

## What's in here

| Path | What it is |
|------|------------|
| `skills/` | **My own** global skills (real files = source of truth). Symlinked into `~/.claude/skills/`. |
| `agents/` | **My own** sub-agent definitions. Symlinked into `~/.claude/agents/`. |
| `manifest/skills.json` | Third-party global skills I use but didn't write. Not installed by `install.sh`. |
| `manifest/plugins.json` | Claude Code plugins + their marketplace. Not installed by `install.sh`. |
| `statusline/` | My status line script. Symlinked to `~/.claude/statusline.sh`. |
| `install.sh` | Symlinks `skills/`, `agents/` and the status line into `~/.claude/`, and sets `statusLine` in `settings.json` if unset. |

## My own skills

### `rc-orchestrate`

Orchestrated implementation of one ticket, codex-first. The session
model writes the plan and the briefs, holds the user gates, and verifies every
return; codex agents execute and Claude reviews, so every change gets a
cross-model review. When codex is unavailable (or a call fails), each step falls
back to its Claude agent.

| Step | Role | Codex route | Claude fallback |
|------|------|-------------|-----------------|
| Recon | `rc-explorer` | `gpt-6.1-sol` medium, read-only | haiku medium |
| Tests, then implement | `rc-tdd` | `gpt-6.1-sol` medium | sonnet medium |
| Review | `rc-reviewer` via `/code-review` | — | opus medium |
| Fix (one round) | `rc-fixer` | `gpt-6.1-sol` high | sonnet high |
| Manual checks | follows `rc-manual-checks` | — | haiku |
| Trim tests | `rc-trimmer` | `gpt-6.1-sol` medium | haiku medium |

Flow: a branch per ticket (or a worktree, on request) → recon → BASE test
failures recorded → plan → **Gate A** (optional: only when the plan has open
questions) → cycles (tests → implement) → review → fix → manual checks → trim →
**Gate B** (required: a short report to read before committing) → an offer to
merge into the parent branch, run `/rc-retro`, and clean up the branch or worktree.

Review runs `/code-review` with its reviewers spawned as `rc-reviewer`, so the
review method tracks upstream `code-review` while the model stays pinned.

**Depends on** the `rc-codex` skill and CLI (optional: missing codex triggers the
fallback), and the third-party `tdd`, `code-review`, `grilling`, and
`resolving-merge-conflicts` skills.

This is the main driver for all implementation work; it does not hand off to
`/implement` or `/implement-spec`.

### `rc-experiment`

Orchestrated measurement for a ticket whose deliverable is a finding, not code (a
cost or quality experiment, a spike). Reuses rc-orchestrate's executor mechanics.
Flow: design → **Gate A** (required: claim, arms, metric, n, budget cap, stop rule)
→ harness + smoke run (`rc-experimenter`) → adversarial design review
(`rc-reviewer`, asked what makes the measurement not measure the claim, with
`confounds.md` as a floor) → freeze the harness at a commit → full run →
**Gate B** (accept the results). The harness stays on an unmerged
`experiment/<slug>` branch; the output is a research file in the feature's
`scratchpad/` plus an *Experiments* entry in `overview.md`.

### `rc-trim-tests`

Cuts freshly written tests down to the ones that earn their place: deletes and
merges only, each removal tagged duplicate, mock-only, off-seam, or tautological. Scopes to
test files changed since a base, confirms the seams, runs `rc-trimmer`, then
verifies against a snapshot that only tests were removed and everything stays green.

### `rc-manual-checks`

At most 10 one-line hand checks (`do this → see this`) for a diff: only what a
human must verify by looking (visual states, flows, timing, real external
services). The list is a guide in plain bullets: its checks are assumed done and
never wait on anyone. Also the rule set rc-orchestrate's manual-checks executor follows.

### `rc-diff-tour`

A ~15-line reading guide to a diff: read order with reasons, key changes,
decisions (reasons only when recorded), and what to watch for. Orientation, not
judgment. rc-orchestrate's Gate B report is an rc-diff-tour plus the run's lines.

### `rc-feature-page`

A feature's page, published as a claude.ai artifact: destination, architecture,
vertical slices with their ticket status, and what waits on the user. The page is a
view of the feature's files and is never edited by hand. `create` drafts the
feature's `overview.md` for one review, then publishes. `refresh` rebuilds the page
from the files and republishes it to the same URL, flagging drift (for example, a
spec that changed after its summary was written). `rc-orchestrate` runs it: it
opens the page in Phase 0 and refreshes it after every ticket status change and at
Finish. The page is fixed templates in
`page/` that read a generated `data.json`, so it looks the same on every refresh.

`feature-layout.md` is the shared convention for where feature files live: a
features root above the repos, `specs/<slice>/` per vertical slice, and a tracker
doc template that steers `wayfinder`, `to-spec`, and `to-tickets` into that tree.

### `rc-codex`

Routing mechanics for handing a single task to the [codex CLI](https://github.com/openai/codex).
Every call goes through `scripts/codex-run.sh`, a `codex exec` wrapper that closes
stdin (an open stdin hangs backgrounded runs), writes the transcript to a log
instead of the caller's context, and turns codex's silent failures into exit codes:
2 for a codex error (bad model, usage limit), 3 for a missing `-o` output. Also
covers sandbox flags, model/effort overrides, session resume, and taking delivery
(the `-o` file plus the git diff).

## My own sub-agents

Each role file is the single definition of that role: Claude spawns it as a
sub-agent, and `rc-orchestrate` briefs codex to read the same file.

| Agent | Role | Used by |
|-------|------|---------|
| `rc-explorer` | Read-only recon: files in scope, reuse, seams, commands | `rc-orchestrate` |
| `rc-tdd` | One test-first cycle: test-writer or implementer mode | `rc-orchestrate` |
| `rc-trimmer` | Deletes or merges redundant tests, one reason each | `rc-trim-tests`, `rc-orchestrate` |
| `rc-reviewer` | Thin opus shell that follows the review brief it's given | `rc-orchestrate`, `rc-experiment` |
| `rc-fixer` | Applies a triaged set of review findings, one round | `rc-orchestrate` |
| `rc-experimenter` | Builds an experiment harness + smoke run, or runs the frozen harness | `rc-experiment` |

## Status line

`statusline/statusline.sh` prints `✉ <name> · <model> (<effort>) · ⎇ <branch> · ctx <n>% · cache <n>m · $<cost>`:

- **name**: the session's messaging name, the one peer sessions `SendMessage` it
  by. Claude Code doesn't hand it to status lines, so the script looks the
  `session_id` up in `~/.claude/sessions/<pid>.json`. That file is undocumented:
  if its shape changes the name shows as `?`.
- **effort**: `effort.level`, which follows `/effort` changes mid-session. The
  parenthetical is left out when the model has no effort setting.
- **branch**: the git branch of the session's current directory, so parallel
  worktree sessions are told apart. Left out outside a repo.
- **ctx**: `context_window.used_percentage`, else computed from the current
  usage; `–` when neither is there.
- **cache**: minutes until the prompt cache goes cold, from `prompt_cache.expires_at`
  against the clock; `cache cold` once it has, so you know the next prompt
  re-caches the conversation. Hidden until a response reports cache tokens.
  It only ticks while idle because `install.sh` sets `refreshInterval: 30`.
- **cost**: `cost.total_cost_usd`, shown only on API billing. Claude Code has no
  billing field, so the script hides it whenever `rate_limits.five_hour` or
  `seven_day` is present (only subscribers get those) and while it is still 0
  (before the first response, when `rate_limits` hasn't arrived yet).

Needs `jq` (`/usr/bin/jq` on recent macOS, else whatever is on `PATH`).

## Third-party skills (reinstalled, not vendored)

`install.sh` does not install these. Install by hand with the Skills CLI:
`npx skills add <source> -g -y -s <names…>`, one call per source. Update them all with `npx skills update -g`.

Matt also ships these as a self-updating Claude Code plugin (`mattpocock-skills`).
They stay on the Skills CLI here because the plugin would namespace them
(`mattpocock-skills:tdd`) and move them out of `~/.agents/skills`, which breaks the
path references in `rc-tdd` and the `$tdd` / `$code-review` calls codex makes.

| Skill | Source |
|-------|--------|
| `find-skills` | [`vercel-labs/skills`](https://github.com/vercel-labs/skills) |
| `frontend-design` | [`anthropics/skills`](https://github.com/anthropics/skills) |
| `grill-me` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `grill-with-docs` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `tdd` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `handoff` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `teach` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `code-review` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `implement` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `implement-spec` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `research` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `to-spec` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `to-tickets` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `wayfinder` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `grilling` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `domain-modeling` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `wait-what` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `codebase-design` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `ask-matt` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `diagnosing-bugs` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `improve-codebase-architecture` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `prototype` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `setup-matt-pocock-skills` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `to-questionnaire` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `triage` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `wizard` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `writing-for-agents` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `retro` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `pr` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `resolving-merge-conflicts` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |

These are installer-managed (`~/.agents/.skill-lock.json`) — **never edit them in
place**, the installer overwrites on update. Fork or write your own alongside, which
is exactly why `rc-orchestrate` lives in `skills/` rather than patching `implement`.

## Plugins

`install.sh` does not install these. Install by hand with `claude plugin marketplace add`
and `claude plugin install <name> -s user`. Marketplace: [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official).

| Plugin | Marketplace |
|--------|-------------|
| `code-simplifier` | `claude-plugins-official` |
| `vercel` | `claude-plugins-official` |

## Adding a new global skill of my own

1. Create `skills/<name>/SKILL.md` (and any supporting files).
2. Re-run `./install.sh` to symlink it into `~/.claude/skills/`.
3. Commit and push.

Same for a sub-agent: drop `agents/<name>.md` in, re-run `./install.sh`. Agent
definitions are read at session start, so restart Claude Code before they appear.

Keep paths inside these files `~`-relative, never `/Users/<me>/…` — they have to
resolve on a machine with a different username.

## Adding a new third-party skill / plugin

Install it by hand (see above) and add an entry to `manifest/skills.json` or
`manifest/plugins.json` to keep the record. Find the upstream source of an installed skill in
`~/.agents/.skill-lock.json`.

## Note on project-specific skills

Skills scoped to a single project (e.g. `sidedoor-frontend/.claude/skills/*`)
live in *that project's* repo and travel with it on clone — they are **not**
managed here. This repo only handles global (`~/.claude/skills`) skills and
plugins.
