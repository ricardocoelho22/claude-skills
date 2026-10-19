#!/bin/bash
# Status line: messaging name (how peer sessions reach this one) · model (effort) · git branch · context used · cost
# /usr/bin/jq first: an asdf jq shim with no pinned version fails here
JQ=/usr/bin/jq; [ -x "$JQ" ] || JQ=jq
input=$(cat)

sid=$($JQ -r '.session_id // empty' <<<"$input")
name=$($JQ -r --arg s "$sid" 'select(.sessionId == $s) | .name' ~/.claude/sessions/*.json 2>/dev/null | head -1)
model=$($JQ -r '.model.display_name // .model.id // "?"' <<<"$input")
effort=$($JQ -r '.effort.level // empty' <<<"$input")
dir=$($JQ -r '.workspace.current_dir // .cwd // empty' <<<"$input")
branch=$(git --no-optional-locks -C "${dir:-.}" branch --show-current 2>/dev/null)
[ -n "$branch" ] || branch=$($JQ -r '.worktree.branch // empty' <<<"$input")
ctx=$($JQ -r '
  (.context_window.used_percentage
   // (if .context_window.current_usage and .context_window.context_window_size then
         ((.context_window.current_usage | (.input_tokens // 0) + (.cache_creation_input_tokens // 0) + (.cache_read_input_tokens // 0))
          * 100 / .context_window.context_window_size)
       else empty end))
  | floor | tostring + "%"' <<<"$input" 2>/dev/null)

# Cost only on API billing: subscribers get rate_limits.five_hour/seven_day after the first
# response, and before it the cost is still 0, so a subscriber never sees it
cost=$($JQ -r '
  if .rate_limits.five_hour or .rate_limits.seven_day then empty
  elif (.cost.total_cost_usd // 0) > 0 then .cost.total_cost_usd
  else empty end' <<<"$input" 2>/dev/null)
[ -n "$cost" ] && cost=$(printf '$%.2f' "$cost")

echo "✉ ${name:-?} · ${model}${effort:+ ($effort)}${branch:+ · ⎇ $branch} · ctx ${ctx:-–}${cost:+ · $cost}"
