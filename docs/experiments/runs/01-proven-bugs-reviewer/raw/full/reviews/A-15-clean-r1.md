I found nothing that needs fixing: no Important findings, 1 Nit and 1 Pre-existing.

I traced each changed path through to its callers: the planner (`journey-edits.planner.ts`), `applyJourneyEdits` and its single retry, `replaceTimeline` and its `updatedAt` guard, how the event emitter handles removed, added and moved steps, the tool handler mapping `JourneyEditsInvalidError` to `AgentInvalidOperationsError`, and the approval path that records `invalid_operations` against `apply_failed`. Validation runs on the working plan, so any invalid op rejects the whole batch before anything is written. The retry re-plans against a freshly fetched journey and emits events relative to that fetch. The precedent cleanup and engagement cancellation on step removal still run through the `journey.step_removed` listener. No stale references to `applyStepEdits` or the old edit types are left.

**Nit: the preview shows step IDs that never get created**
- `journey.tools.ts` (`proposeEditJourney`) calls `planJourneyEdits`, which generates new ObjectIds through `createStep` (`journey-edits.planner.ts:170`, `id: options.generateStepId!()`). The `add_step` and `add_section.steps[]` previews keep those IDs (`journey-edit-preview.ts:20, 46`).
- On approval, the handler calls `applyJourneyEdits`, which plans again and generates different IDs (`journeys.service.ts:676`).
- So the `stepId` on an added step in the card never exists in the journey. Anything that links to a step from the card, or keys on that ID after approval, will point at nothing. Either leave `stepId` out of new-step previews, or say in a comment that it is provisional.

**Pre-existing, now reachable through the agent: ad-hoc steps in the closing section stop closing steps being generated**
- `accepted-offer.listener.ts` skips generating closing steps when `existingAdHocSteps.length > 0`.
- The planner creates every step as `type: 'ad_hoc'` (`journey-edits.planner.ts:178`). It also allows `add_step` and `move_step` into `acceptedOfferSectionKey`, because the only guard is on `remove_section` (`journey-edits.planner.ts:92`).
- So if the agent is asked to "add a step to Closing" before an offer is accepted, accepting the offer later creates no closing steps. Separately, `backToMarket` (`journeys.service.ts:440`) deletes every step in that section, including ones the user moved there.
- The REST `addStep` already allowed this, so the diff doesn't introduce it, but it is now one agent request away.