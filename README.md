# claude-skills

My portable Claude Code setup. Clone it on a new laptop and run one script to
restore all my global skills and plugins.

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
| `manifest/skills.json` | Third-party global skills I use but didn't write. Reinstalled from upstream. |
| `manifest/plugins.json` | Claude Code plugins + their marketplace. |
| `install.sh` | Bootstrap script. |

## My own skills

### `orchestrate`

Orchestrated implementation of a spec or set of tickets, codex-first. The session
model writes the plan and the briefs, holds the user gates, and verifies every
return; codex agents execute and Claude reviews, so every change gets a
cross-model review. When codex is unavailable (or a call fails), each step falls
back to its Claude agent.

| Step | Role | Codex route | Claude fallback |
|------|------|-------------|-----------------|
| Recon | `impl-explorer` | `gpt-6-sol` medium, read-only | haiku medium |
| Tests, then implement | `impl-tdd` | `gpt-6-sol` medium | sonnet medium |
| Review | `impl-reviewer` via `/code-review` | — | opus medium |
| Fix (one round) | `impl-fixer` | `gpt-6-sol` high | sonnet high |
| Manual checklist | follows `manual-checklist` | `gpt-6-luna` low | haiku |
| Trim tests | `impl-trimmer` | `gpt-6-sol` medium | haiku medium |

Flow: recon → BASE test failures recorded → plan → **Gate A** (optional: only
when the plan has open questions) → per ticket: slices (tests → implement) →
review → fix → manual checklist → trim → **Gate B** (required: a short report to
read before committing) → cross-ticket review for multi-ticket runs.

Review runs `/code-review` with its reviewers spawned as `impl-reviewer`, so the
review method tracks upstream `code-review` while the model stays pinned.

**Depends on** the `codex` skill and CLI (optional: missing codex triggers the
fallback), and the third-party `tdd`, `code-review`, and `grilling` skills.

This is the main driver for all implementation work; it does not hand off to
`/implement` or `/implement-spec`.

### `trim-tests`

Cuts freshly written tests down to the ones that earn their place: deletes and
merges only, each removal tagged duplicate, mock-only, off-seam, or tautological. Scopes to
test files changed since a base, confirms the seams, runs `impl-trimmer`, then
verifies against a snapshot that only tests were removed and everything stays green.

### `manual-checklist`

At most 10 one-line hand checks (`do this → see this`) for a diff: only what a
human must verify by looking (visual states, flows, timing, real external
services). Also the rule set orchestrate's checklist executor follows.

### `diff-tour`

A ~15-line reading guide to a diff: read order with reasons, key changes,
decisions (reasons only when recorded), and what to watch for. Orientation, not
judgment. Orchestrate's Gate B report is a diff-tour plus the run's lines.

### `feature-artifact`

A feature's page, published as a claude.ai artifact: destination, architecture,
vertical slices with their ticket status, and what waits on the user. The page is a
view of the feature's files and is never edited by hand. `create` drafts the
feature's `overview.md` for one review, then publishes. `refresh` rebuilds the page
from the files and republishes it to the same URL, flagging drift (for example, a
spec that changed after its summary was written). The page is fixed templates in
`page/` that read a generated `data.json`, so it looks the same on every refresh.

`feature-layout.md` is the shared convention for where feature files live: a
features root above the repos, `specs/<slice>/` per vertical slice, and a tracker
doc template that steers `wayfinder`, `to-spec`, and `to-tickets` into that tree.

### `codex`

Routing mechanics for handing a single task to the [codex CLI](https://github.com/openai/codex).
Every call goes through `scripts/codex-run.sh`, a `codex exec` wrapper that closes
stdin (an open stdin hangs backgrounded runs), writes the transcript to a log
instead of the caller's context, and turns codex's silent failures into exit codes:
2 for a codex error (bad model, usage limit), 3 for a missing `-o` output. Also
covers sandbox flags, model/effort overrides, session resume, and taking delivery
(the `-o` file plus the git diff).

### `codex-implement`

Implement → review → verify pipeline on top of `codex`, for a single task. Agrees
seams with the user, has codex implement with `$tdd`, runs a second read-only
codex on `$code-review` returning a JSON verdict (schema in
`verdict.schema.json`), then verifies tests and typecheck locally before committing.

**Depends on** the `codex` CLI being installed and configured (`~/.codex/config.toml`),
and on `tdd` / `code-review` being available to codex via `~/.agents/skills`.

## My own sub-agents

Each role file is the single definition of that role: Claude spawns it as a
sub-agent, and `orchestrate` briefs codex to read the same file.

| Agent | Role | Used by |
|-------|------|---------|
| `impl-explorer` | Read-only recon: files in scope, reuse, seams, commands | `orchestrate` |
| `impl-tdd` | One slice test-first: test-writer or implementer mode | `orchestrate` |
| `impl-trimmer` | Deletes or merges redundant tests, one reason each | `trim-tests`, `orchestrate` |
| `impl-reviewer` | Thin opus shell that follows the review brief it's given | `orchestrate` |
| `impl-fixer` | Applies a triaged set of review findings, one round | `orchestrate` |

## Third-party skills (reinstalled, not vendored)

Installed via the Skills CLI: `npx skills add <source> -g -y -s <names…>`, one call per
source. Update them all with `npx skills update -g`.

Matt also ships these as a self-updating Claude Code plugin (`mattpocock-skills`).
They stay on the Skills CLI here because the plugin would namespace them
(`mattpocock-skills:tdd`) and move them out of `~/.agents/skills`, which breaks the
path references in `impl-tdd` and the `$tdd` / `$code-review` calls codex makes.

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

These are installer-managed (`~/.agents/.skill-lock.json`) — **never edit them in
place**, the installer overwrites on update. Fork or write your own alongside, which
is exactly why `orchestrate` lives in `skills/` rather than patching `implement`.

## Plugins

Installed via `claude plugin`. Marketplace: [`anthropics/claude-plugins-official`](https://github.com/anthropics/claude-plugins-official).

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

Add an entry to `manifest/skills.json` or `manifest/plugins.json`, then re-run
`./install.sh`. Find the upstream source of an installed skill in
`~/.agents/.skill-lock.json`.

## Note on project-specific skills

Skills scoped to a single project (e.g. `sidedoor-frontend/.claude/skills/*`)
live in *that project's* repo and travel with it on clone — they are **not**
managed here. This repo only handles global (`~/.claude/skills`) skills and
plugins.
