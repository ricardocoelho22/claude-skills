**0 Important · 1 Nit · 0 Pre-existing.** Nothing in the diff breaks behaviour. One case could pass for the wrong reason.

I checked these points by reading the code, and each holds:
- **Driver reads proposals the same way the live service does.** `textAfterProposalOf` (`driver.ts:93-102`) uses `isProposedToolOutput` on `part.output`. The turn service stores that field as `toJsonSafe(event.output)` (`agent-turn.service.ts:455`) and runs the same check before it emits `proposal` (`:461`). So `proposalCount` and `textAfterProposal` agree.
- **Truncation reads the right field.** `truncated: assistantMessage?.metadata?.truncated === true` matches the service, which writes the field only when it is true (`agent-turn.service.ts:261`). The error path in `failedTurn` sets `truncated: false`, and every typed fixture was updated for the new required field (`assertions.spec.ts`, `runner.spec.ts`).
- **Making `delete-step-refusal` free-only is correct.** Paid `edit_journey` now supports `remove_step` (`tools/journey.tools.ts:103`), so on paid the old `write_yet` refusal would have been wrong.
- **The seed data backs the case wording.** `Prepare to Sell` and `Negotiation` are at `seeds/journeys.seed.ts:318-320`. `Stage Your Home` is `in_progress` (`:357`), so "mark as completed" is a real change. The `prep` section holds two steps, so the "remove a section that still has steps" case is valid. Junior participates in `empty-homebuyer-v1` (`journey-participants.seed.ts:27`) and Ricardo in `home-seller-v1` (`:35`). The `{{journey:...}}` placeholders resolve through `loadJourneyIds`.
- **Word count fallback.** `maxReplyWords` counts the full reply only when no proposal was recorded. Every case that sets it also requires `proposal: true`, so a turn with no proposal still fails on `proposal`.

**Nit: `remove-populated-section-asks` does not check that the agent asked anything** (`cases/journey-write.ts:84`)
- `expect: { toolsCalled: ['get_journey'], noProposal: true }`
- Any reply that calls `get_journey` and makes no proposal passes. That includes a wrong refusal ("I can't remove sections yet") and a reply that just describes the section.
- So if a prompt change breaks the rule at `agent-prompt.ts:115` (ask before removing a section that still has steps) by making the agent refuse instead of ask, this case won't catch it.
- Fix: add a check on the question itself, such as a `mustInclude` that names the two steps, or a pattern that requires a question mark.