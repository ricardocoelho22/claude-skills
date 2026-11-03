I found one Important issue and no Nits or Pre-existing ones.

**Important: one batch can lose all of its milestone celebrations when it adds a step**

- **Evidence:** In `src/modules/notifications/listeners/milestone-detection.listener.ts`, `handleTimelineBatchApplied` looks up each step from `after` in the old timeline:
  ```ts
  const beforeStep = beforeSteps.get(step.id)
  return beforeStep!.status !== step.status && this.isStepDone(step)
  ```
  A step the batch adds has no entry in `before`, so `beforeStep` is `undefined` and `.status` throws a `TypeError`. The method's `try/catch` swallows the error. As a result, a batch that adds even one step sends no section or journey celebrations at all, even when the same batch completed a section.
- **Why it matters:** `applyJourneyEdits` in `journeys.service.ts` sends batches with add operations through this path, and the new `if (event.batchId) return` in `handleStepUpdated` turns off the old per-step fallback. So these milestones are now lost, not just sent twice. The ticket requires milestones to "fire once per approved batch". The existing tests only cover batches that complete, edit or remove steps, so none of them hit this case.
- **Command:** I added a temporary test file, `src/modules/notifications/listeners/zz-review-probe.spec.ts`, then deleted it. Its test runs a batch that changes section `a` from `s1 pending` to `s1 completed` and adds a pending step `new` to section `b`. It then expects `journey.section_completed` to be emitted.
  ```
  pnpm test -- src/modules/notifications/listeners/zz-review-probe.spec.ts
  ```
- **Output:**
  ```
  ERROR [MilestoneDetectionListener] Failed to check milestones for journey j1
  ERROR [MilestoneDetectionListener] TypeError: Cannot read properties of undefined (reading 'status')
  ✕ batch that completes section a and adds a step in section b still celebrates section a
    Expected: "journey.section_completed", Anything
    Number of calls: 0
  ```
- **What the ticket requires:** one `JOURNEY_SECTION_COMPLETED` for section `a` (1 call).
- **Fix:** treat a missing `beforeStep` as a status change, e.g. `beforeStep?.status !== step.status`. A step that is added already completed then counts as a trigger, the same way a manual edit is handled today.

**Checked and found sound:**
- The `batchId` early-returns in both notification listeners.
- Manual `updateStep` events carry no `batchId`, so manual edits behave as before.
- The new `TimelineBatchNotificationListener` handles errors (`.catch` on the professional lookup, plus an outer `try/catch`) and leaves out the pro who approved the batch.
- `applyJourneyEdits` is the only caller of `emitTimelineEditEvents`.

I couldn't check the en/es text for the new notification: it isn't in this backend tree and the frontend isn't in this worktree.

The working tree is back to how I found it.