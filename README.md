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

### `scout`

Reads a spec or ticket(s), does light recon (repo count, subsystem spread, seam
clarity, ticket dependencies), and recommends `/implement` or `/implement-fleet`
before either one starts. Confirms with the user, then hands off to whichever is
chosen. Exists so the fleet/plain choice is made from evidence, not a guess.

### `implement-fleet`

Orchestrated version of `/implement`. The session model frames the work, holds the
user gates, writes the briefs and verifies every return; pinned sub-agents do the
execution. Split by phase:

| Phase | Agent | Model |
|-------|-------|-------|
| Recon | `impl-explorer` | sonnet (read-only) |
| Implement | `impl-tdd` | sonnet |
| Review | `impl-reviewer` | opus (read-only, two axes in parallel) |

Two user gates: seams + slice order before any test is written, and per-ticket
before committing.

**Depends on** the third-party `tdd` and `code-review` skills (both in
`manifest/skills.json`) — `impl-tdd` reads `~/.claude/skills/tdd/SKILL.md`, and the
orchestrator pastes the smell baseline out of `~/.claude/skills/code-review/SKILL.md`.
Install those before using it.

### `implement-fleet-codex`

Successor to `implement-fleet`; the old skill stays as a fallback until this one
has proven itself. Codex agents execute, Claude reviews, so every change gets a
cross-model review. Falls back to the Claude agents when codex is unavailable.

| Phase | Role | Codex route | Claude fallback |
|-------|------|-------------|-----------------|
| Recon | `impl-explorer` | `gpt-6-sol` medium, read-only | sonnet medium |
| Tests / implement | `impl-tdd` | `gpt-6-sol` medium | sonnet medium |
| Trim tests | `impl-trimmer` | `gpt-6-sol` medium | sonnet medium |
| Review | `impl-reviewer` via `/code-review` | — | opus medium |
| Fix | `impl-fixer` | `gpt-6-sol` high | sonnet high |
| Manual checklist | ad hoc | `gpt-6-luna` low | haiku |

Per ticket: slices (tests → implement) → trim → review → fix → manual checklist →
Gate B (required, short report). Gate A (the plan) is optional.

**Depends on** the `codex` CLI (optional; triggers the fallback when missing) and
the `tdd` and `code-review` skills.

### `codex`

Routing mechanics for handing a single task to the [codex CLI](https://github.com/openai/codex)
via `codex exec` — sandbox flags, model/effort overrides, and how to take delivery
(the `-o` file plus the git diff). No methodology; just the plumbing.

### `codex-implement`

Implement → review → verify pipeline on top of `codex`. Agrees seams with the user,
has codex implement with `$tdd`, runs a second read-only codex on `$code-review` for
a structured verdict, then verifies tests and typecheck locally before committing.

**Depends on** the `codex` CLI being installed and configured (`~/.codex/config.toml`),
and on `tdd` / `code-review` being available to codex via `~/.agents/skills`.

## Third-party skills (reinstalled, not vendored)

Installed via the Skills CLI: `npx skills add <source> -g -y -s <name>`.

| Skill | Source |
|-------|--------|
| `find-skills` | [`vercel-labs/skills`](https://github.com/vercel-labs/skills) |
| `frontend-design` | [`anthropics/skills`](https://github.com/anthropics/skills) |
| `grill-me` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `grill-with-docs` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `to-prd` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `to-issues` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `tdd` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `handoff` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `teach` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `code-review` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `implement` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `research` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `to-spec` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `to-tickets` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `wayfinder` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |

These are installer-managed (`~/.agents/.skill-lock.json`) — **never edit them in
place**, the installer overwrites on update. Fork or write your own alongside, which
is exactly why `implement-fleet` lives in `skills/` rather than patching `implement`.

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
