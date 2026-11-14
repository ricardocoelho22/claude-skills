# desk: the remote dev box

My Windows desktop runs WSL2 Ubuntu as a second machine for heavy agent work
(32 GB RAM against the laptop's 16). The laptop reaches it over Tailscale as
`ssh desk`.

**Nothing outside this folder knows the desk exists.** `install.sh`, `skills/`,
`agents/` and `scripts/check.sh` never touch it. Other machines that use this
repo ignore the folder and keep working on their own. Keep it that way: never
make a skill or agent depend on the desk.

| File | What it is |
|------|------------|
| `README.md` | This page: layout, what syncs and how, drift, rebuild. |
| `windows-setup.ps1` | The Windows-side PowerShell blocks, to copy and paste. |
| `drift-check.sh` | Run it on the laptop to compare the laptop with the desk. Read-only. |
| `synced.txt` | The repos and folders the drift check compares. |

## Layout

```
Laptop (macOS)  ──Tailscale──►  Windows desktop  ─►  WSL2 Ubuntu 24.04
ricardos-macbook-pro            desktop-u4bcnmu      desk (user ricardo)
```

| What | Where |
|------|-------|
| Ubuntu's disk | `E:\WSL\Ubuntu\ext4.vhdx` on the NVMe (~140 GB, used only for this). C: is a nearly full SSD and D: is an HDD: never put WSL on either. |
| WSL limits | `%USERPROFILE%\.wslconfig`: 24 GB RAM, 14 threads, swap file on E:. See `windows-setup.ps1`. |
| Keep-alive | Task Scheduler task "WSL keep-alive": starts WSL at Windows logon, with no window. |
| SSH | Laptop `~/.ssh/config` has `Host desk`. Key login only; passwords are off (`/etc/ssh/sshd_config.d/00-no-passwords.conf`). |
| Paths | Same layout as the laptop with `~` swapped: repos in `~/Code/...`. |
| Tools | All installed for the user, no sudo, in `~/.local/bin` (claude, asdf, gh) and asdf (Node 24.21.0, codex, pnpm 9.15.9, yarn 1.22, jq 1.6). jq is set user-wide (`asdf set -u jq 1.6`) because the status line needs it everywhere. The PATH is set at the **top** of `~/.bashrc`, so plain `ssh desk 'cmd'` finds them. |

## Daily use

```bash
ssh desk -t 'tmux new -As main'    # attach, or create the session
```

Work in tmux windows (`Ctrl-b c` new, `Ctrl-b d` detach). Agents keep running
when the laptop sleeps. For an editor, use VS Code **Remote - SSH** to `desk`.

To get the desktop back for something else, run `wsl --shutdown` in PowerShell.
This kills every tmux and agent session. `Start-ScheduledTask -TaskName "WSL keep-alive"`
starts WSL again.

## What syncs, and how

Each machine has its own copy of everything. Nothing syncs on its own: each row
says what keeps the two copies the same.

| What | Source of truth | How the desk gets it | How it drifts | Prevention |
|------|-----------------|----------------------|---------------|------------|
| Work repos (`synced.txt`) | GitHub | `git push` on one, `git pull` on the other | Work on the same branch on both; uncommitted work left on one | **One machine per branch at a time.** Push before you switch machines. |
| Sidedoor loose files (`~/Code/sidedoor/tickets`, `z-features`, `CLAUDE.md`, …) | None: not in git | Copied once on 2026-11-14 | Every edit on either machine | Edit tickets on one machine only, or put the folder under git (best fix) |
| My skills and agents | This repo | `git pull` here; the links already point into the repo | Forgetting to pull | Pull this repo on both after a change |
| Third-party skills (`~/.agents/skills`) | Upstream, via `~/.agents/.skill-lock.json` | Copied once | Running `npx skills update -g` on only one machine | Update on both, or copy the folder and lock file across |
| `~/.claude/CLAUDE.md`, `~/.claude/settings.json` | The laptop | Copied once, with paths rewritten | Any edit on either machine | Edit on the laptop, then copy it over (see Fixing drift) |
| Claude plugins | `manifest/plugins.json` | Installed by hand | Installing on one only | Install on both. On the desk the marketplace is called `anthropic-plugin-directory`. |
| `~/.codex/config.toml` | The laptop | Copied once | codex adds a trusted-project entry for each new repo you open | Expected drift. Only copy it over when the model or settings change. |
| Claude memory (`~/.claude/projects/*/memory`) | Neither: each machine writes its own | Copied once, renamed for Linux paths | Every session that saves a memory | Reconcile now and then (see Fixing drift) |
| Logins (claude, codex, gh) | Each machine | Signed in separately | Expired tokens | Run the login again on the machine that fails |
| `.env` files | The laptop | Copied once | Rotating a secret on one machine | Copy the file again after you rotate a secret |

## Drift check

```bash
desk/drift-check.sh          # on the laptop; host defaults to desk
```

It runs the same read-only collector on both machines and prints:

- **Repos:** branch, commit, uncommitted file count, and ahead/behind against the
  remote-tracking branch (no fetch is done, so this compares against your last fetch).
  It flags the same branch on two different commits, and uncommitted changes on
  both machines on the same branch.
- **Loose folders:** a hash per top-level entry in each `files` line of `synced.txt`.
- **Config, skills, agents, plugins, memory:** only what differs. Paths are
  normalised to `~` first, so `/Users/ricardocoelho` and `/home/ricardo` don't
  count as drift.
- **Tool versions:** for information only. Claude Code updates itself, so a
  version gap is normal.

It exits 1 when something drifted and 2 when it can't reach the desk.

## Fixing drift

Run these on the laptop. They copy **laptop → desk**; swap the order to copy back.

```bash
# Claude global config: rewrite paths on the way over
sed "s#$HOME#/home/ricardo#g" ~/.claude/settings.json | ssh desk 'cat > ~/.claude/settings.json'
scp ~/.claude/CLAUDE.md desk:.claude/

# Third-party skills + lock file
rsync -a --delete ~/.agents/skills/ desk:.agents/skills/ && scp ~/.agents/.skill-lock.json desk:.agents/

# This repo: pull on the desk
ssh desk 'git -C ~/Code/claude-skills pull --ff-only'

# Sidedoor loose files: shows what would change; drop -n to copy
rsync -avn --exclude='sidedoor-*/' --exclude=worktrees --exclude=.pnpm-store --exclude=.DS_Store \
  ~/Code/sidedoor/ desk:Code/sidedoor/

# One project's memory (the folder names differ per machine)
rsync -av ~/.claude/projects/-Users-ricardocoelho-Code-sidedoor/memory/ \
  desk:.claude/projects/-home-ricardo-Code-sidedoor/memory/
```

When both machines changed the same memory or ticket file, merge it by hand. Don't
copy over it.

## Known quirks

- `systemctl` reports `degraded` because of `systemd-binfmt.service`. This is harmless
  on WSL, which handles binfmt itself.
- Sparse VHD (`wsl --manage --set-sparse`) is deliberately **off**: Microsoft marks
  it unsafe because it can corrupt the disk. Compact by hand instead (see `windows-setup.ps1`).
- `sidedoor-docs` installs with **yarn**. Its pnpm lockfile is stale; pnpm 9 rejects
  the workspace file, and `--frozen-lockfile` fails.
- Claude in Chrome does not work from desk sessions, because there is no Chrome next to them.
- After a Windows Update reboot, WSL only comes back once someone logs in to
  Windows (at the desk, or by Remote Desktop over Tailscale).

## Rebuild from scratch

1. Windows: set sleep to never, then run
   `wsl --install -d Ubuntu --location E:\WSL\Ubuntu` (or install it and use
   `wsl --manage … --move`). Create the user `ricardo`. Install Tailscale for Windows.
   Run blocks 1 and 2 of `windows-setup.ps1`.
2. Ubuntu:
   - `sudo apt install -y build-essential git tmux openssh-server curl unzip rsync`
   - `sudo systemctl enable --now ssh`
   - Install Tailscale, then `sudo tailscale up --hostname=desk`. Disable key expiry for `desk` in the admin console.
3. Laptop: `ssh-copy-id desk`. Then in Ubuntu, add the `00-no-passwords.conf` drop-in and restart ssh.
4. Tools, from the laptop over ssh:
   - Put the PATH line at the top of `~/.bashrc`.
   - Install asdf and gh as release binaries into `~/.local/bin`.
   - `asdf install nodejs 24.21.0`, then `npm i -g @openai/codex pnpm@9.15.9 yarn`.
   - Install Claude Code with the native installer.
5. Copy the repos with rsync, leaving out `node_modules`, `.next`, `dist`, `build`,
   `.terraform`, `.terragrunt-cache` and `worktrees`. This keeps unpushed work and
   `.env` files. Then run `git worktree prune` in each repo.
6. Copy the config: `~/.claude` (CLAUDE.md, settings.json, skills and agents
   links, memory), `~/.agents`, `~/.codex/config.toml` and `skills`,
   `~/.config/git/ignore`, `~/.tmux.conf`. Rewrite `/Users/ricardocoelho` to
   `/home/ricardo`, and memory folder names from `-Users-ricardocoelho-…` to `-home-ricardo-…`.
7. Sign in, in an interactive `ssh desk`:
   - `gh auth login -h github.com -p https -w && gh auth setup-git`
   - `codex login --device-auth`
   - run `claude`, then type /login
8. Run `desk/drift-check.sh`.
