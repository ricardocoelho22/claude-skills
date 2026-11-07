**2 Important, 0 Nit, 0 Pre-existing.**

I proved both with a throwaway spec, `src/modules/agent/zz-review-probe.spec.ts`, which I ran with `pnpm test -- src/modules/agent/zz-review-probe.spec.ts` and then deleted. Both probes failed.

**1. Important: a cut-off turn is still silent once any earlier part exists.**
`agent-turn.service.ts:296` sets `truncated = event.truncated && assistantParts.length === 0`. A tool call adds a `dynamic-tool` part (`:437-443`), so the flag is dropped whenever the turn already has one. That is the ticket's own pattern: `get_journey` runs first, then `edit_journey` hits the cap.
- **Probe A:** I scripted `tool-call get_journey`, then its `tool-result`, then `step-start`, then `finish {truncated:true}`.
- **Printed:** `A parts ["dynamic-tool","step-start"] metadata.truncated undefined done {"turnId":"…","usage":{…"outputTokens":6000…}}`, and `toMatchObject({ truncated: true })` fails.
- **Ticket requires:** "when a model call stops for length… the pro gets a visible message… instead of an empty turn". Here the pro gets only a read-tool chip, with no message.

The same gate covers two more cases:
- **Prose then a cut-off call:** the ticket's turn-1 shape still produces no flag.
- **Complete tool call with a `length` finish:** the second case in `agent-model-client.truncation.spec.ts` shows the SDK emits the `tool-call` event without running it. `applyModelEvent` pushes that part, so `truncated` is false. `finalizeAssistantParts` (`:133-136`) then saves it as `output-error 'turn_interrupted'`, and the pro sees no length message.

**2. Important: an error with no parts now loses `metadata.error`.**
`agent-turn.service.ts:260` changed the error spread to `...(fatalError && assistantParts.length > 0 ? { error: fatalError } : {})`. An `error` event only emits and never pushes a part (`:486-488`), so a model failure before any output now saves an assistant message with no parts and no error.
- **Probe B:** the model yields only `{ type: 'error', error: 'model stream failed' }`.
- **Printed:** `B parts 0 error undefined`, and `toMatchObject({ error: 'model stream failed' })` fails.
- **Before this diff:** `error` was always set when there was a fatal error. Existing specs pass only because each one streams text before the error.
- **Callers that break:**
  - `agent-title.listener.ts:47` (`if (assistantMessage?.metadata?.error) return`) no longer skips these turns, so a failed turn starts title generation, which is a paid model call.
  - `agent-conversation.projection.ts:55` stops sending `error` to the client, so on reload the failed turn shows as an empty reply with no error.
  - `src/evals/agent/driver.ts:305` loses that error as a fallback.
- **Fix:** restore the error spread with no condition. Nothing in the ticket asks to drop it. The new "empty truncated turn" spec only needs `error` to be absent when there is no `fatalError`, which the old code already did.