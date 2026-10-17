#!/bin/bash
# Status line: messaging name (how peer sessions reach this one) · model · context used
# /usr/bin/jq first: an asdf jq shim with no pinned version fails here
JQ=/usr/bin/jq; [ -x "$JQ" ] || JQ=jq
input=$(cat)

sid=$($JQ -r '.session_id // empty' <<<"$input")
name=$($JQ -r --arg s "$sid" 'select(.sessionId == $s) | .name' ~/.claude/sessions/*.json 2>/dev/null | head -1)
model=$($JQ -r '.model.display_name // .model.id // "?"' <<<"$input")
ctx=$($JQ -r '
  (.context_window.used_percentage
   // (if .context_window.current_usage and .context_window.context_window_size then
         ((.context_window.current_usage | (.input_tokens // 0) + (.cache_creation_input_tokens // 0) + (.cache_read_input_tokens // 0))
          * 100 / .context_window.context_window_size)
       else empty end))
  | floor | tostring + "%"' <<<"$input" 2>/dev/null)

echo "✉ ${name:-?} · ${model} · ctx ${ctx:-–}"
