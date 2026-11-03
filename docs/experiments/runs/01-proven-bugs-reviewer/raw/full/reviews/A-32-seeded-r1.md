I'm finishing the review of the eval diff. I've checked the driver, the assertions, the cases and the seed and prompt references.

**Findings: 1 Important, 1 Nit, 0 Pre-existing**

**1. Important: a proposal with no text after it is graded on the whole reply**
- `src/evals/agent/driver.ts:325`: `...(textAfterProposal ? { textAfterProposal } : {}),`
- When the turn ends on the card, `textAfterProposalOf` returns `''`. Because `''` is falsy, the field is left off the transcript.
- `assertions.ts` `checkProposalReply` then uses `turn.textAfterProposal ?? turn.assistantText`, so it counts the full reply, including any text before the tool call.
- Effect: a model that writes "I'll add Closing Prep with eight steps, each with a short description and a date in the next 30 days…" and then proposes with no closing line fails `reply_words` in `large-section-proposal-en`, `large-section-proposal-es` and `mixed-edit-proposal`. That is the best possible behaviour, and it gets marked as a failure.
- The new spec "accepts empty proposal text at a zero word limit" only tests the assertion with `textAfterProposal: ''` passed in by hand. The driver never produces that value, so the bug is hidden. The spec "records a plain-text turn … with no proposal text field" depends on this same falsy check.
- Fix: test `textAfterProposal !== undefined`, and add a driver spec for a proposal with no text after it.

**2. Nit: `maxReplyWords` passes silently on a truncated turn**
- `assertions.ts` `checkProposalReply`: `if (limit !== undefined && !turn.truncated)` skips the word check when the turn was truncated.
- `mixed-edit-proposal` sets `maxReplyWords: 20` but not `notTruncated`. If that turn hits the cap, it passes the word check and nothing reports the truncation.
- Fix: add `notTruncated: true` to that case, or make the skip fail the check instead of passing.

**Checked and fine:**
- Making `delete-step-refusal` free only is justified. `agent-prompt.ts:115-117` now allows deletion on paid through `deleteSteps`.
- `emptyPage` and `sellerPage` are used with the accounts that participate in those journeys, as `CASES.md` cites.
- Every `EvalTranscriptTurn` literal now sets the new required `truncated` field: the driver, the error turn, and the fixtures in `assertions.spec.ts` and `runner.spec.ts`.