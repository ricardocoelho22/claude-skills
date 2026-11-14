#!/usr/bin/env bash
#
# Compare this machine's Claude/codex setup and work repos with the desk box,
# and report what has drifted. Run it on the laptop:
#
#   desk/drift-check.sh [ssh-host]     # host defaults to desk
#
# Read-only on both machines: no fetch, no writes. See desk/README.md.
# Exit 0 = in sync, 1 = drift found, 2 = desk unreachable.
set -uo pipefail

HOST=${1:-desk}
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNCED=$(grep -vE '^\s*(#|$)' "$DIR/synced.txt")

# Runs on each machine. Prints "key<TAB>value" lines, with $HOME written as ~.
read -r -d '' COLLECTOR <<'EOF'
export PATH="$HOME/.local/bin:$HOME/.asdf/shims:/opt/homebrew/bin:$PATH"
H=$HOME; HKEY=$(printf %s "$HOME" | tr / -)
sha() { if command -v sha256sum >/dev/null; then sha256sum; else shasum -a 256; fi | cut -c1-12; }
# Any home path counts as ~, so a laptop path copied into a desk file isn't drift.
norm() { LC_ALL=C perl -pe 's#/(Users|home)/[A-Za-z0-9._-]+#~#g' "$@"; }
hashtree() { # hash every file under $1 (following links), skipping nested repos and build dirs
  (cd "$1" && find -L . \( -name node_modules -o -name worktrees -o -name .pnpm-store -o -name .git \) -prune \
      -o -type d -exec test -e '{}/.git' ';' -prune -o -type f ! -name .DS_Store -print 2>/dev/null |
    LC_ALL=C sort | while IFS= read -r f; do printf '%s\n' "$f"; norm "$f"; done | sha)
}
emit() { printf '%s\t%s\n' "$1" "${2:-missing}"; }

emit tool.claude "$(claude --version 2>/dev/null | awk '{print $1}')"
emit tool.codex  "$(codex --version 2>/dev/null | awk '{print $2}')"
emit tool.node   "$(node --version 2>/dev/null)"
emit tool.gh     "$(gh --version 2>/dev/null | awk 'NR==1{print $3}')"

for f in .claude/CLAUDE.md .codex/config.toml .config/git/ignore .tmux.conf .agents/.skill-lock.json; do
  [ -f "$H/$f" ] && emit "config.~/$f" "$(norm "$H/$f" | sha)" || emit "config.~/$f"
done
# settings.json without the keys each machine sets for itself (plugins are compared below)
s="$H/.claude/settings.json"; JQ=/usr/bin/jq; [ -x "$JQ" ] || JQ=jq
[ -f "$s" ] && emit "config.~/.claude/settings.json" "$("$JQ" -S 'del(.enabledPlugins, .theme)' "$s" | norm | sha)" \
  || emit "config.~/.claude/settings.json"
for d in "$H"/.claude/skills/*/ "$H"/.agents/skills/*/; do
  d=${d%/}; [ "$d" = "$H/.claude/skills/synced" ] && continue   # claude.ai-synced, managed by Claude per machine
  [ -d "$d" ] && emit "skill.~/${d#$H/}" "$(hashtree "$d")"
done
for f in "$H"/.claude/agents/*.md; do [ -e "$f" ] && emit "agent.$(basename "$f")" "$(norm "$f" | sha)"; done
claude plugin list 2>/dev/null | sed -n 's/^[^A-Za-z0-9]*\([A-Za-z0-9_-]*\)@.*/\1/p' |
  while read -r p; do emit "plugin.$p" installed; done
for m in "$H"/.claude/projects/*/memory; do
  [ -d "$m" ] || continue
  p=$(basename "$(dirname "$m")"); p=${p#"$HKEY"}; p="~${p}"
  for f in "$m"/*.md; do [ -e "$f" ] && emit "memory.$p/$(basename "$f")" "$(norm "$f" | sha)"; done
done

while read -r kind path; do
  g="$H/$path"
  case $kind in
    git)
      if ! git -C "$g" rev-parse --git-dir >/dev/null 2>&1; then emit "repo.$path"; continue; fi
      b=$(git -C "$g" branch --show-current); b=${b:-detached}
      head=$(git -C "$g" rev-parse --short HEAD)
      dirty=$(git -C "$g" status --porcelain | wc -l | tr -d ' ')
      ab=$(git -C "$g" rev-list --left-right --count '@{u}...HEAD' 2>/dev/null | awk '{print "-"$1"/+"$2}')
      emit "repo.$path" "$b $head $dirty ${ab:-none}" ;;
    files)
      [ -d "$g" ] || { emit "files.$path"; continue; }
      for e in "$g"/* "$g"/.[!.]*; do
        [ -e "$e" ] || continue; n=$(basename "$e")
        case $n in node_modules|worktrees|.pnpm-store|.DS_Store) continue ;; esac
        [ -e "$e/.git" ] && continue
        if [ -d "$e" ]; then emit "files.$path/$n" "$(hashtree "$e")"; else emit "files.$path/$n" "$(norm "$e" | sha)"; fi
      done ;;
  esac
done <<< "$SYNCED"
EOF

tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
run() { printf 'SYNCED=%q\n%s\n' "$SYNCED" "$COLLECTOR"; }
run | bash -s 2>/dev/null | LC_ALL=C sort > "$tmp/laptop" &
if ! run | ssh -o ConnectTimeout=10 -o BatchMode=yes "$HOST" bash -s 2>/dev/null | LC_ALL=C sort > "$tmp/desk" \
   || [ ! -s "$tmp/desk" ]; then
  wait; echo "Cannot reach $HOST over ssh (is the desktop on, and WSL running?)"; exit 2
fi
wait

LC_ALL=C join -t $'\t' -a1 -a2 -e missing -o 0,1.2,2.2 "$tmp/laptop" "$tmp/desk" > "$tmp/joined"
drift=0
bold() { printf '\n\033[1m%s\033[0m\n' "$*"; }
flag() { printf '  \033[1;33m⚠\033[0m %s\n' "$*"; drift=$((drift + 1)); }

bold "Repos (branch commit uncommitted ahead/behind; no fetch)"
printf '  %-30s %-38s %s\n' "" laptop "$HOST"
grep '^repo\.' "$tmp/joined" | while IFS=$'\t' read -r key l d; do
  printf '  %-30s %-38s %s\n' "${key#repo.}" "$l" "$d"
done
while IFS=$'\t' read -r key l d; do
  r=${key#repo.}
  [ "$l" = missing ] || [ "$d" = missing ] && { flag "$r: missing on one machine"; continue; }
  read -r lb lh ld _ <<< "$l"; read -r db dh dd _ <<< "$d"
  [ "$lb" != "$db" ] && continue   # different branches: fine, as long as each is pushed
  [ "$lh" != "$dh" ] && flag "$r: $lb is on different commits; push on one, pull on the other"
  [ "$ld" != 0 ] && [ "$dd" != 0 ] && flag "$r: uncommitted changes on both machines on $lb; keep them on one"
done < <(grep '^repo\.' "$tmp/joined")

section() { # <prefix> <title> <hint>
  local rows; rows=$(grep "^$1\." "$tmp/joined" | awk -F'\t' '$2 != $3')
  bold "$2"
  if [ -z "$rows" ]; then echo "  in sync"; return; fi
  while IFS=$'\t' read -r key l d; do
    case "$l|$d" in
      missing\|*) flag "${key#$1.}: only on $HOST" ;;
      *\|missing) flag "${key#$1.}: only on laptop" ;;
      *) flag "${key#$1.}: differs" ;;
    esac
  done <<< "$rows"
  echo "  → $3"
}
section files  "Loose folders (synced.txt)" "edit on one machine only; copy with the rsync in desk/README.md"
section config "Global config"              "copy the laptop's version over (desk/README.md, Fixing drift)"
section skill  "Skills"                      "git pull this repo on both; npx skills update -g on both"
section agent  "Agents"                      "git pull this repo on both"
section plugin "Plugins"                     "claude plugin install on the machine that lacks it"
section memory "Claude memory"               "merge the differing notes, then copy them across"

bold "Tool versions (info only)"
grep '^tool\.' "$tmp/joined" | while IFS=$'\t' read -r key l d; do
  printf '  %-8s laptop %-12s %s %s%s\n' "${key#tool.}" "$l" "$HOST" "$d" "$([ "$l" != "$d" ] && echo '  (differs)')"
done

echo
if [ "$drift" -eq 0 ]; then echo "In sync."; exit 0; fi
echo "$drift item(s) drifted."; exit 1
