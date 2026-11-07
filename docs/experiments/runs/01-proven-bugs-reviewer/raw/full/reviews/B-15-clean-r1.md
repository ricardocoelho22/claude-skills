I found one Important issue and no Nits.

**1. Important: one batch that finishes several steps fires the milestone events once per step instead of once.**

- **Where:** `src/modules/journeys/journeys.service.ts`, in `emitTimelineEditEvents`. After the single timeline write, it loops over the steps and emits one `journey.step_updated` per changed step:
  ```ts
  for (const step of after.steps) {
    const oldStep = oldSteps.get(step.id)
    if (!oldStep || isDeepStrictEqual(oldStep, step)) continue
    await this.eventEmitter.emitAsync('journey.step_updated', ...)
  ```
- **Why it repeats:** `MilestoneDetectionListener.handleStepUpdated` (`src/modules/notifications/listeners/milestone-detection.listener.ts:33`) reloads the journey on every event. Each time, it sees the final state of the whole batch: every step done. So it emits `JOURNEY_COMPLETED`, or `JOURNEY_SECTION_COMPLETED`, once for each completed step in the batch.
- **What's new:** before this diff, `updateStep` wrote one step and emitted one event. The batch path now emits N events against one journey state.
- **Effect:** a request like "mark the last three steps done" sends three "journey completed" milestone events, and so three celebrations or notifications.

**How I ran it:** I added a temporary spec, `src/modules/journeys/zz-review-milestone.spec.ts`. It reuses the in-memory Mongo setup from `journeys.service.spec.ts` and also registers the real `MilestoneDetectionListener`. The test builds a journey with 3 pending steps in one section, then calls `applyJourneyEdits` with three `set_step_status: completed` ops.

```
pnpm test -- src/modules/journeys/zz-review-milestone.spec.ts
    JOURNEY_COMPLETED emitted 3 times
    Expected number of calls: 1
    Received number of calls: 3
Tests:       1 failed, 1 total
```

**What the ticket needs:** the ticket says mixed multi-op proposals go through the ticket-14 apply path "unchanged", and that each proposal is applied as a single batch. So one batch should produce one completion milestone. There are two ways to fix it:
- Check milestones once per batch, for example with a batch-level event the listener handles.
- Or have the listener judge each step against the "before" state. That breaks the current single-step behaviour, so the first option is cleaner.

I deleted the temporary spec and patch script, so the working tree is as I found it.