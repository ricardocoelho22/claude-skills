Found the problems; writing up the review now.

**Findings: 1 Important, 1 Nit, 0 Pre-existing**

**Important: a cut-off turn still shows the pro nothing.** The backend now marks a cut-off turn as `truncated`, but nothing in the diff gives the pro the en/es message the ticket asks for.
- `agent-model-client.service.ts:138` sets `truncated: part.finishReason === 'length'`.
- `agent-turn.service.ts:261` saves `metadata.truncated`, and `:274` adds `truncated: true` to the `done` event.
- No en/es text is created anywhere (`rg truncated` turns up only these flag sites). The empty-turn case is the ticket's turn 2. The new spec (`agent-conversation.service.spec.ts`, "persists and signals an empty truncated turn") checks that the saved assistant message still has `parts: []` and no `error` event.
- So the pro sees a message only if the frontend shows one from the flag, and the frontend isn't in this worktree (`worktrees/exp01-31-clean/` holds only `backend`).
- The root cause of the silent turn isn't fixed in this diff. Either add a localized text part or error message on the backend, or confirm a frontend change that reads both the `done.truncated` flag and the `metadata.truncated` field on reload.

**Nit: the SSE contract comment is out of date.** `agent.types.ts:478` still says `done \`{ turnId, usage }\``, but `done` can now also carry `truncated`.

Checked and fine:
- **Cut-off tool call:**
  - When the tool call's JSON is unfinished, no `tool-call` event comes out (truncation spec 1).
  - When the call is complete but the model stops for length, the tool isn't run. The call is saved as `input-available`, and `finalizeAssistantParts` (`agent-turn.service.ts:133-137`) turns it into `output-error`/`turn_interrupted`. So the next turn's history doesn't send the model a tool call without a result.
  - I didn't run the specs (this review was read-only), so the claim that the tool isn't run rests on what spec 2 asserts.
- **Multi-step turns:** a step that stops for length ends the AI SDK loop, so the turn's final `finish` reason is the cut-off step's. The flag can't be lost to a later step.
- **Spend breakers:** `hasReachedOutputBudget` (`agent-model-client.service.ts:147`) and metering are unchanged. Metering still records usage for an empty cut-off turn, and the spec pins this (`turns: 1`, `meteredMicroUsd: 716`). The worst case per paid turn rises from about 4,000 to about 12,000 output tokens, as the new comment in `agent.constants.ts:42` says.