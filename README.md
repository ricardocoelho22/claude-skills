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
| `skills/` | **My own** global skills (real files = source of truth). Symlinked into `~/.claude/skills/`. Empty for now. |
| `manifest/skills.json` | Third-party global skills I use but didn't write. Reinstalled from upstream. |
| `manifest/plugins.json` | Claude Code plugins + their marketplace. |
| `install.sh` | Bootstrap script. |

## Third-party skills (reinstalled, not vendored)

Installed via the Skills CLI: `npx skills add <source> -g -y -s <name>`.

| Skill | Source |
|-------|--------|
| `find-skills` | [`vercel-labs/skills`](https://github.com/vercel-labs/skills) |
| `frontend-design` | [`anthropics/skills`](https://github.com/anthropics/skills) |
| `excalidraw-diagram-generator` | [`github/awesome-copilot`](https://github.com/github/awesome-copilot) |
| `grill-me` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `grill-with-docs` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `to-prd` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `to-issues` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `tdd` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `handoff` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |
| `teach` | [`mattpocock/skills`](https://github.com/mattpocock/skills) |

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

## Adding a new third-party skill / plugin

Add an entry to `manifest/skills.json` or `manifest/plugins.json`, then re-run
`./install.sh`. Find the upstream source of an installed skill in
`~/.agents/.skill-lock.json`.

## Note on project-specific skills

Skills scoped to a single project (e.g. `sidedoor-frontend/.claude/skills/*`)
live in *that project's* repo and travel with it on clone — they are **not**
managed here. This repo only handles global (`~/.claude/skills`) skills and
plugins.
