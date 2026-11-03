**0 Important, 1 Nit, 0 Pre-existing.** I found no bugs on the correctness axis. The one finding is a type gap.

**Nit: the type for an invalid-operation detail doesn't include the new `precedentId` field**
- The planner now returns issues with `precedentId` (`src/modules/journeys/journeys.types.ts:140`, set in `src/modules/journeys/journey-edits.planner.ts:123,131,138`).
- They reach the model through `AgentInvalidOperationsError(error.issues)` (`src/modules/agent/tools/journey.tools.ts:277,316`). From there `rejectValidation` (`src/modules/agent/agent-action.service.ts:178`) and the proposal rewrite (`src/modules/agent/agent-proposals.service.ts:101`) pass the details on unchanged.
- But that error's details are typed as `AgentInvalidOperationDetail` (`src/modules/agent/agent.types.ts:273-279`), which only has `index`, `op`, `code`, `stepId` and `sectionKey`.
- At runtime the field still gets through, because the issue objects are passed by reference. The type just doesn't describe it: the model's main hint for these three codes isn't in the type, and any later code that builds details from that type will silently drop it.
- Fix: add `precedentId?: string` to `AgentInvalidOperationDetail`.

**Checked and found sound:**
- **Order of checks:** "precedent not found" runs before "precedent is the step itself", and a step's own id always exists, so a self-reference gets the right code.
- **Cycle check:** `reachesStep` uses a visited set, so it ends even on cycles already stored or on ids that point nowhere. It runs against the batch's state at that point, so earlier operations count.
- **New steps:** cycle and self checks are skipped for `add_step` and `add_section`, which is correct. A new step's id is generated inside the planner, so nothing can name it yet.
- **Comparing lists:** `samePrecedents` gets a deduplicated `next`, so comparing the set's size is valid. Old ids that no longer exist are filtered out before comparing and before the "before" preview.
- **Removal in the same batch:** removing a step and then naming it as a precedent is rejected as not found. Naming it first and then removing it gets cleaned up by the existing `$pull` in the step-removed listener (`src/modules/journeys/journeys.repo.ts:217`).
- **Approval:** `applyJourneyEdits` re-plans against the fresh journey, so a precedent deleted between proposal and approval is rejected, not written.
- **Tool schema:** `updateStepSchema` now also accepts `precedents` alone. `newStepSchema` covers both `add_step` and the steps nested in `add_section`.
- **`get_journey` output:** it now filters out precedent ids that point to missing steps, so the model never copies one back into a proposal.