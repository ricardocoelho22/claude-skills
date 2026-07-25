#!/usr/bin/env bash
#
# Bootstrap your Claude Code skills + plugins on a fresh machine.
#
#   git clone <this-repo> && cd claude-skills && ./install.sh
#
# Idempotent: safe to run repeatedly. It only ADDS things; it never removes
# skills/plugins you already have.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SKILLS_DIR="${HOME}/.claude/skills"
CLAUDE_AGENTS_DIR="${HOME}/.claude/agents"

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }

# --- 1. Personal skills: symlink repo skills/<name> -> ~/.claude/skills/<name> ---
# The repo stays the source of truth; edits here are reflected live.
log "Linking personal skills from skills/ …"
mkdir -p "$CLAUDE_SKILLS_DIR"
shopt -s nullglob
personal=("$REPO_DIR"/skills/*/)
if [ ${#personal[@]} -eq 0 ]; then
  echo "   (none yet — drop a skill folder under skills/ and re-run to link it)"
fi
for dir in "${personal[@]}"; do
  name="$(basename "$dir")"
  target="$CLAUDE_SKILLS_DIR/$name"
  src="${dir%/}"
  if [ -L "$target" ] && [ "$(readlink "$target")" = "$src" ]; then
    echo "   ok   $name (already linked)"
  elif [ -e "$target" ] && [ ! -L "$target" ]; then
    warn "$target exists and is not a symlink — leaving it untouched"
  else
    ln -sfn "$src" "$target"
    echo "   link $name"
  fi
done

# --- 2. Sub-agent definitions: symlink repo agents/<name>.md -> ~/.claude/agents/ ---
# Skills that delegate (e.g. implement-fleet) are inert without these.
log "Linking sub-agents from agents/ …"
mkdir -p "$CLAUDE_AGENTS_DIR"
agents=("$REPO_DIR"/agents/*.md)
if [ ${#agents[@]} -eq 0 ]; then
  echo "   (none yet)"
fi
for src in "${agents[@]}"; do
  name="$(basename "$src")"
  target="$CLAUDE_AGENTS_DIR/$name"
  if [ -L "$target" ] && [ "$(readlink "$target")" = "$src" ]; then
    echo "   ok   $name (already linked)"
  elif [ -e "$target" ] && [ ! -L "$target" ]; then
    warn "$target exists and is not a symlink — leaving it untouched"
  else
    ln -sfn "$src" "$target"
    echo "   link $name"
  fi
done

# --- 3. Third-party skills via the Skills CLI (npx skills) ---
log "Installing third-party skills (npx skills add) …"
if ! command -v npx >/dev/null 2>&1; then
  warn "npx (Node.js) not found — skipping skills. Install Node.js, then re-run."
else
  while IFS=$'\t' read -r source name; do
    [ -z "${name:-}" ] && continue
    echo "   → $source ($name)"
    npx -y skills add "$source" -g -y -s "$name" || warn "skill install failed: $name"
  done < <(node -e '
    const m = require(process.argv[1]);
    for (const s of m.skills) console.log(`${s.source}\t${s.name}`);
  ' "$REPO_DIR/manifest/skills.json")
fi

# --- 4. Plugins via the Claude Code CLI ---
log "Configuring plugins (claude plugin) …"
if ! command -v claude >/dev/null 2>&1; then
  warn "'claude' CLI not found — skipping plugins."
else
  while IFS=$'\t' read -r kind val; do
    case "$kind" in
      MARKET)
        echo "   + marketplace $val"
        claude plugin marketplace add "$val" --scope user || warn "marketplace add: $val (may already exist)"
        ;;
      PLUGIN)
        echo "   + plugin $val"
        claude plugin install "$val" -s user || warn "plugin install: $val (may already be installed)"
        ;;
    esac
  done < <(node -e '
    const m = require(process.argv[1]);
    for (const mp of m.marketplaces) console.log(`MARKET\t${mp.source}`);
    for (const p of m.plugins) console.log(`PLUGIN\t${p}`);
  ' "$REPO_DIR/manifest/plugins.json")
fi

log "Done. Restart Claude Code to load newly installed plugins/skills."
