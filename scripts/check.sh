#!/usr/bin/env bash
#
# Check that this repo's skills and agents still hang together:
#   1. every skills/<name>/SKILL.md and agents/<name>.md has frontmatter whose
#      `name` matches its file and a `description`;
#   2. every ~/.claude/skills/... or ~/.claude/agents/... path they mention
#      resolves: ours against this repo, a third-party skill against ~/.claude
#      (warn only), and any other name is an error (a stale name after a rename);
#   3. every relative markdown link resolves;
#   4. every skill or agent they name (rc-<name>, /<skill>, subagent_type) is
#      ours, listed in manifest/skills.json, or built in.
#
# Exit 1 on any error. Run by install.sh and by the pre-commit hook.
set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR" || exit 1
errors=0
err()  { printf '\033[1;31m[error]\033[0m %s\n' "$*"; errors=$((errors + 1)); }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT

third_party=$(grep -oE '"name": *"[^"]+"' manifest/skills.json | sed -E 's/.*"([^"]+)"$/\1/')
builtin="general-purpose Explore Plan effort model clear compact"   # built-in agents and slash commands
known() { # <name>: ours, third-party, or built in
  [ -d "skills/$1" ] || [ -f "agents/$1.md" ] || grep -qx "$1" <<<"$third_party" ||
    [[ " $builtin " == *" $1 "* ]]
}

docs=$(find skills agents docs README.md -name '*.md' -not -path '*/node_modules/*' -not -path 'docs/research/*' 2>/dev/null | sort)

# --- 1. Frontmatter ---
check_frontmatter() { # <file> <expected name>
  local file=$1 want=$2 fm
  if [ "$(head -1 "$file")" != "---" ]; then err "$file: no frontmatter"; return; fi
  fm=$(awk 'NR>1 && /^---$/{exit} NR>1' "$file")
  grep -qE "^name: *\"?$want\"?$" <<<"$fm" || err "$file: frontmatter name is not '$want'"
  grep -qE '^description: *[^ ]' <<<"$fm" || err "$file: frontmatter has no description"
}
for f in skills/*/SKILL.md; do check_frontmatter "$f" "$(basename "$(dirname "$f")")"; done
for f in agents/*.md; do check_frontmatter "$f" "$(basename "$f" .md)"; done

# --- 2. ~/.claude paths ---
grep -ohE '~/\.claude/(skills|agents)/[A-Za-z0-9_.-]+(/[A-Za-z0-9_./-]*[A-Za-z0-9_-])?' $docs | sort -u |
while read -r ref; do
  rest=${ref#\~/.claude/}            # skills/<name>/... or agents/<file>
  kind=${rest%%/*}; item=${rest#*/}; name=${item%%/*}
  [ "$name" = "." ] && continue
  if [ -e "$kind/$name" ]; then
    [ -e "$rest" ] || echo "error $ref"
  elif ! grep -qx "$name" <<<"$third_party"; then
    echo "error $ref"
  elif [ ! -e "$HOME/.claude/$rest" ]; then
    echo "warn $ref"
  fi
done > "$tmp/paths"
while read -r level ref; do
  if [ "$level" = error ]; then err "no such file here or in the manifest: $ref"; else warn "third-party, not installed: $ref"; fi
done < "$tmp/paths"

# --- 3. Relative markdown links ---
for f in $docs; do
  dir=$(dirname "$f")
  grep -oE '\]\([^)#: ]+\.(md|sh|json|tsv)(#[^)]*)?\)' "$f" | sed -E 's/^\]\(//; s/[#)].*$//' |
  while read -r link; do
    [ -e "$dir/$link" ] || echo "$f -> $link"
  done
done > "$tmp/links"
while read -r line; do err "broken link: $line"; done < "$tmp/links"

# --- 4. Named skills and agents ---
{
  grep -ohE '`/?rc-[a-z0-9-]*[a-z0-9]' $docs | grep -oE 'rc-[a-z0-9-]+'
  grep -ohE '`/[a-z][a-z0-9-]*[a-z0-9]`' $docs | tr -d '`/'
  grep -ohE 'subagent_type: *`?[A-Za-z][A-Za-z0-9-]*' $docs | sed -E 's/subagent_type: *`?//'
} | sort -u | while read -r name; do known "$name" || echo "$name"; done > "$tmp/names"
while read -r name; do err "no skill or agent named $name (ours, manifest, or built in)"; done < "$tmp/names"

if [ "$errors" -gt 0 ]; then
  printf '%s error(s)\n' "$errors"
  exit 1
fi
echo "check: ok"
