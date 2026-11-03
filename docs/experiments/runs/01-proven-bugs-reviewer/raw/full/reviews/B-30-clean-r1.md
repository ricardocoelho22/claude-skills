**Findings: 0 Important, 1 Nit, 0 Pre-existing.**

I found no defects that break behaviour. Planner validation for all three codes, dedupe, replace/clear/keep semantics, the preview mapping, the zod schema and the approval replay (`applyJourneyEdits` re-plans from the stored `Mixed` input) all hold up when traced through the code. The planner and agent suites pass (36 suites, 406 tests) and `pnpm typecheck` is clean.

Things I checked and found correct:
- **Cycle check across ops:** `reachesStep` (`journey-edits.planner.ts:144`) walks `plan.steps`, which already holds earlier ops' precedent updates. So B→A followed by A→B in one batch is rejected. The `visited` set stops infinite loops on cycles already stored in the data.
- **Dangling stored ids:** `updateStep` filters stored precedents against the live steps (`livePrecedents`) before comparing. Sending the current visible list counts as `no_change`, not a phantom diff.
- **Removing a step:** when a removed step is still someone's precedent, `emitTimelineEditEvents` fires `journey.step_removed`. `StepRemovedListener.cleanupPrecedents` then `$pull`s the id from every step's precedents, so the database ends clean.

**Nit: the card can show a precedent the same batch deletes**
- **Evidence:** `journey-edits.planner.ts` `validateOperation` checks precedents against `plan.steps` only at that op's position. Nothing re-checks them after a later `remove_step` / `remove_section deleteSteps:true`.
- **Probe:** I ran a throwaway spec in `src/modules/journeys/`, since deleted. It ran `[{op:'update_step', stepId:'b', precedents:['a']}, {op:'remove_step', stepId:'a'}]`, ran with `pnpm test -- src/modules/journeys/zz-probe.spec.ts`, and printed:
  `PROBE [["b",["a"]]] {"precedents":[{"id":"a","title":{"en":"a","es":"a"}}]}`
- **Effect:** the card shows "B waits on a" next to "remove a". After approval the listener strips `a`, so the database is correct and only the preview is misleading.
- **What the ticket says:** "at that point of the batch" allows this, so it's a judgement call. One fix is to drop removed ids from earlier changes' `after.precedents` when building the preview.