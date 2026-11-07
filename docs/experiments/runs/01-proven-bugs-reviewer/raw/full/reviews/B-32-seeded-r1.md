I found 2 issues, both Important. Both were run against the real code using temporary spec files, which I've since deleted, so the working tree is back as I found it.

**1. Important: no text after the card means the word cap counts the whole reply instead**

- **Evidence:** `src/evals/agent/driver.ts:325` has `...(textAfterProposal ? { textAfterProposal } : {})`. When `textAfterProposalOf` returns `''` (the `edit_journey` part is the last part), that value counts as false and the field is dropped. `assertions.ts:251` then falls back with `turn.textAfterProposal ?? turn.assistantText`, so `maxReplyWords` grades the text written *before* the proposal.
- **Exposed by:** the new spec `accepts empty proposal text at a zero word limit` (`assertions.spec.ts`). It covers `textAfterProposal: ''` at assertion level, but the driver never produces that value.
- **Run:** I copied `driver.spec.ts` into a temporary probe spec. The model mock writes a 28-word preamble, then calls `edit_journey`, with no text after it. The case expects `{ proposal: true, maxReplyWords: 20 }`. Command: `pnpm test -- src/evals/agent/probe.spec.ts -t PROBE`.
- **Printed:**
  `PROBE {"has":false,"proposals":1} [{"turnIndex":0,"check":"reply_words","message":"Reply has 28 words, exceeding the limit of 20."}]`
- **Ticket requires:** `maxReplyWords` covers only "the assistant text written after the proposal". Zero words after the card is within the cap, so it should give `[]`.
- **Fix:** use `textAfterProposal !== undefined` in `driver.ts:325`.

**2. Important: a truncated turn skips the word cap without any failure**

- **Evidence:** `assertions.ts:250` has `if (limit !== undefined && !turn.truncated)`. A truncated turn skips `reply_words` completely. That's only safe when `notTruncated` is also set. `mixed-edit-proposal` (`cases/journey-write.ts`) sets `maxReplyWords: 20` and `maxOutputTokens: 1000` but no `notTruncated`.
- **Run:** a temporary spec fed `checkTranscript` the real `mixed-edit-proposal` case with a paid-tier turn: `proposalCount: 1`, `truncated: true`, 60 words after the proposal, and both expected tools called. Command: `pnpm test -- src/evals/agent/probe2.spec.ts`.
- **Printed:** `PROBE2 []`
- **Ticket requires:** "Small mixed edit … → `proposal`, `maxReplyWords: 20`". A 60-word reply should fail with `reply_words`. As written, a reply that runs long enough to hit the output cap passes.
- **Fix:** skip the word cap only when `notTruncated` already reports the failure. Otherwise, either still apply the cap or report truncation.