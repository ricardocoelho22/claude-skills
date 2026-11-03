I found 2 findings: 1 Important and 1 Nit. In this working tree the agent specs (409 tests), typecheck and lint all pass.

**1. Important: the spec doesn't cover a real cut-off tool call, and in that case a raw JSON parse error reaches the pro**

- **Evidence:** Anthropic's provider always ends a content block with `tool-input-end` and then a `tool-call` carrying whatever JSON it had so far. It does this even when the model hit `max_tokens` (`node_modules/.pnpm/@ai-sdk+anthropic@2.0.99_zod@4.1.13/.../dist/index.js:3416-3427`, `input: contentBlock.input === "" ? "{}" : contentBlock.input`).
- **The gap:** the first case in `agent-model-client.truncation.spec.ts:47-70` feeds a stream that stops after `tool-input-delta` with no `tool-call` part. It then asserts there are no `tool-error` events. That stream never happens with the real provider, so the spec covers a path production can't reach.
- **Run:** I copied the spec to a temporary file, added the two parts the provider really sends (`tool-input-end`, then `tool-call` with input `{"id":"journey-`), and ran `pnpm test -- src/modules/agent/zz-real.spec.ts -t unclosed`. I deleted the file afterwards. The events it printed:
  ```
  [{"type":"step-start"},{"type":"tool-call",...,"input":"{\"id\":\"journey-"},
   {"type":"tool-error",...,"error":"Invalid input for tool get_journey: JSON parsing failed: Text: {\"id\":\"journey-.\nError message: Unterminated string in JSON ..."},
   {"type":"finish","truncated":true,...}]
  ```
  The test then fails: `expect(...tool-error...).toEqual([])` received 1 item.
- **What happens next:** `agent-turn.service.ts:469-483` sends this to the client as `tool-result` with `status: 'error'` and the raw parser text. It also stores that text as the part's `errorText`, which the model reads on the next turn.
- **What the ticket requires:** a cut-off call is never executed, and that is pinned by a spec. Execution is still skipped, so that part holds. But the spec doesn't pin the shape that actually occurs, and the pro gets a parser error next to the `truncated` flag.
- **Fix:** model the real stream in the spec. Then decide whether a tool error on a turn that finished for `length` should be relabelled (for example `output_truncated`) rather than passing the parse text through.

**2. Nit: the backend has no visible en/es message for a cut-off turn (could not run)**

- **Evidence:** the diff only adds a `truncated` flag: `agent-turn.service.ts:261` (message metadata), `:274` (`done` event) and `agent-conversation.projection.ts:56`. No en or es text exists anywhere in the backend.
- **Why I couldn't check it:** for turn 2 of the ticket (a cut-off `edit_journey` call), the stored message holds only an `output-error` tool part. Whether the pro sees the message depends entirely on the frontend reading `truncated`. This worktree contains only `backend/`, so I couldn't run or read that side.
- **What to do:** confirm the frontend change exists and is reviewed alongside this diff. Otherwise the turn is still silent.