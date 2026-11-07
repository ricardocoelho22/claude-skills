#!/usr/bin/env bash
# codex-run.sh — `codex exec` wrapper that makes silent failures loud and keeps
# the transcript out of the caller's context.
# Usage: codex-run.sh [exec options] "<brief>"      (the `exec` is implied)
#        codex-run.sh resume --last -o <file> "<follow-up>"
# Writes the full transcript to a log (CODEX_LOG or a fresh temp file) and prints
# only the log path and a one-line status. Closes stdin unless CODEX_STDIN=1.
# Exit 2: codex reported an error (bad model, usage limit). Exit 3: no -o output.

[ "${1:-}" = "exec" ] && shift

tmp="${TMPDIR:-/tmp}"
log="${CODEX_LOG:-$(mktemp "${tmp%/}/codex-run.XXXXXX")}"
echo "codex-run: log at $log"

# Track the -o/--output-last-message target so we can verify it after, and the
# -C/--cd directory codex works in.
out_file=""
work_dir="$PWD"
prev=""
for arg in "$@"; do
  case "$prev" in
    -o|--output-last-message) out_file="$arg" ;;
    -C|--cd) work_dir="$arg" ;;
  esac
  case "$arg" in
    --output-last-message=*) out_file="${arg#--output-last-message=}" ;;
    --cd=*) work_dir="${arg#--cd=}" ;;
  esac
  prev="$arg"
done

# A leftover file from an earlier run must not pass for this run's output.
[ -n "$out_file" ] && rm -f "$out_file"

# A linked worktree keeps its index under the main checkout's .git, outside the
# workspace-write sandbox, so `git mv` and `git add` fail. Make the worktree's
# git dir and the shared objects writable; refs stay read-only, so commits still
# fail. (Codex keeps a writable root that is itself a .git dir read-only.)
# `-c` rather than `--add-dir`: `resume` takes no `--add-dir` and drops the
# first call's `-c` overrides.
sandbox_args=()
git_dir=$(git -C "$work_dir" rev-parse --path-format=absolute --git-dir 2>/dev/null)
common_dir=$(git -C "$work_dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
if [ -n "$git_dir" ] && [ "$git_dir" != "$common_dir" ]; then
  sandbox_args=(-c "sandbox_workspace_write.writable_roots=[\"$git_dir\",\"$common_dir/objects\"]")
fi

if [ "${1:-}" = "resume" ]; then
  shift
  set -- resume "${sandbox_args[@]}" "$@"
else
  set -- "${sandbox_args[@]}" "$@"
fi

if [ "${CODEX_STDIN:-}" = "1" ]; then
  codex exec "$@" >"$log" 2>&1
else
  codex exec "$@" </dev/null >"$log" 2>&1
fi
status=$?

err_line=$(grep '^ERROR:' "$log" | grep -E -i '"type":"error"|usage limit' | head -n1)
if [ -n "$err_line" ]; then
  echo "codex-run: failed: $err_line" >&2
  exit 2
fi

if [ "$status" -ne 0 ]; then
  echo "codex-run: codex exited $status; last lines of the log:" >&2
  tail -n 15 "$log" >&2
  exit "$status"
fi

if [ -n "$out_file" ] && [ ! -s "$out_file" ]; then
  echo "codex-run: no output file at $out_file; last lines of the log:" >&2
  tail -n 15 "$log" >&2
  exit 3
fi

echo "codex-run: ok${out_file:+, output at $out_file}"
