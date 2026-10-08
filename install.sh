#!/usr/bin/env bash
#
# Link this repo's own Claude Code skills and sub-agents on a fresh machine.
# Third-party skills and plugins are not installed; see manifest/ for the list.
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
# Skills that delegate (e.g. orchestrate) are inert without these.
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

log "Done. Restart Claude Code to load newly linked skills/agents."
