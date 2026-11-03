I found 1 issue: 1 Important, 0 Nit, 0 Pre-existing.

**Important: milestone celebrations get silently dropped whenever an approved batch adds a step**

- **Evidence:** `src/modules/notifications/listeners/milestone-detection.listener.ts`, inside `handleTimelineBatchApplied`:
  ```ts
  const beforeSteps = new Map(event.before.steps.map((step) => [step.id, step]))
  const triggerSteps = event.after.steps.filter((step) => {
    const beforeStep = beforeSteps.get(step.id)
    return beforeStep!.status !== step.status && this.isStepDone(step)
  })
  ```
- **What goes wrong:** `event.after` is the timeline after the batch is applied. In `journeys.service.ts` (`emitTimelineEditEvents`, around lines 718–731), `after` can contain steps that `before` does not; that is exactly the add case, where `journey.step_added` is emitted for steps missing from `oldSteps`. For any such step, `beforeSteps.get(step.id)` is `undefined`, so `beforeStep!.status` throws a TypeError.
  - The listener's `catch` turns that into a log line ("Failed to check milestones…") and stops.
  - So any batch that adds a step and also completes the last open steps of a section or journey sends no `JOURNEY_SECTION_COMPLETED` or `JOURNEY_COMPLETED` at all.
  - Per-step `step_updated` handling now returns early on batch-stamped events (`if (event.batchId) return`), so nothing else sends those notifications either. Before this diff they would have gone out, so this is a regression.
  - The milestone spec never builds a batch containing an added step, which is why the tests don't catch it.
- **Fix:** skip steps with no `before` entry (`if (!beforeStep) return false`). Alternatively, treat an added step that arrives already done as a trigger, if that is the behaviour you want. Add a spec for a batch that adds a step and also completes a section.

Other things I checked that hold up:
- The batch id is stamped on add, remove and update events in the batch path. The manual paths (`updateStep` and the standalone add/remove) carry no id, so they behave as before.
- `TimelineBatchNotificationListener` resolves its dependencies: `JourneyParticipantsModule` is imported in `notifications.module.ts:90`.
- If the professional lookup fails, it falls back to `null`, so the notice goes to every participant, which is acceptable.
- `StepStatusChangedListener` (engagements) and `StepReminderListener` still run per step for batch events. That is correct: they handle engagement status and reminders, not homeowner notifications.