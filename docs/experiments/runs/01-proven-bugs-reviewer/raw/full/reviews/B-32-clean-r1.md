I found no defects in this diff. Findings: 0 Important, 1 Nit, 0 Pre-existing.

**What I ran:**
- `pnpm typecheck`: clean, so no caller that builds an `EvalTranscriptTurn` broke when the new required `truncated` field was added.
- `pnpm test -- src/evals/agent`: 3 suites, 108 tests, all passed. MongoDB was up (the seed logs printed), so the new driver specs actually ran rather than skipping.

**What I checked by reading:**
- **Truncation flag:** `driver.ts` reads `assistantMessage.metadata.truncated`, which is the field `agent-turn.service.ts:261` writes. The flag is only set when the model stops on its output cap (`finishReason === 'length'`, `agent-model-client.service.ts:138`).
- **Text after the proposal:** `textAfterProposalOf` uses the last `edit_journey` part that `isProposedToolOutput` accepts. If a second edit is rejected, the text after the earlier successful proposal is still graded, and the spec covers this.
- **Seed facts the cases rely on:** `journeys.seed.ts:318-320` has the `Prepare to Sell` and `Negotiation` sections. `Stage Your Home` is `in_progress` (line 354), so the mixed-edit case's "mark it completed" is a real change, not a no-op that would leave no proposal. `Prepare to Sell` holds two steps, so the remove case really is a section with steps in it.
- **`delete-step-refusal` now free only:** this is correct. `remove_step` is a supported `edit_journey` operation (`journey.tools.ts:103`), so on the paid tier the agent would rightly propose the deletion and the old paid expectation (`write_yet` with `noProposal`) would fail.
- **Test-only change:** no security, resource or concurrency surface is touched.

**Nit** (a judgement call; nothing to run, it's a design point): when no proposal is recorded, the `maxReplyWords` check falls back to the full `assistantText` (`assertions.ts:251`, `turn.textAfterProposal ?? turn.assistantText`). In the four new cases `proposal: true` sits next to `maxReplyWords`. So if a turn produces no proposal, it also gets a `reply_words` failure that grades a different text, the full reply rather than the text after the card, which adds a misleading second failure. The fallback is deliberate, documented in `eval.types.ts`, and covered by a spec, so this is optional: skipping the word check when `proposal` is expected and missing would keep each failure to its real cause.