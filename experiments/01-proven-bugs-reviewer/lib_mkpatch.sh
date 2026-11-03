#!/usr/bin/env bash
# usage: lib_mkpatch.sh <worktree> <out.patch> <relpath>...
# Writes a patch of the worktree's current content vs. the pristine-prepared content (git
# stash-free): the caller first saved pristine copies at $PRISTINE_DIR/<relpath>.
set -euo pipefail
WT="$1"; OUT="$2"; shift 2
: > "$OUT"
for f in "$@"; do
  diff -u --label "a/$f" --label "b/$f" "$PRISTINE_DIR/$f" "$WT/$f" >> "$OUT" || true
done
