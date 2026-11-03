I found 0 Important, 1 Nit and 0 Pre-existing issues. I found nothing that breaks behavior.

**Nit: any approved batch now notifies, even ones that add or remove nothing**
- `timeline-batch-notification.listener.ts:20-38` sends `JOURNEY_TIMELINE_UPDATED` every time `JOURNEY_TIMELINE_BATCH_APPLIED` fires. It never looks at what changed.
- `journeys.service.ts:691-696` fires that event after every successful `replaceTimeline`.
- Before this diff, a batch notified the homeowner only when it added or removed steps. Those notifications came from `step-progress.listener.ts:20` (step added) and `step-removed.listener.ts`. A batch that only renamed, reordered, rescheduled or changed step statuses sent nothing.
- Now every such batch sends a notification. That may be what "aggregate" was meant to cover. If it wasn't, check `event.before` against `event.after` for step adds and removals before sending.

What I checked and found correct:
- **Who gets a batch id:** only the agent's `edit_journey` tool calls `applyJourneyEdits` (`journey.tools.ts:259`). Manual `updateStep` (`journeys.service.ts:655-658`) emits without a batch id, so editor changes behave as before.
- **Milestones:** the new batch handler starts milestone checks from the same steps the old per-event handler did: existing steps whose status changed to completed or skipped, ignoring added steps. It checks "journey completed" first and returns early, then checks each affected section once. `event.after` is a lean `findOneAndUpdate({new:true})` result (`journeys.repo.ts:196-202`), so `status`, `steps`, `sections` and `purpose` are all there.
- **Listener early-returns:** only `milestone-detection`, `step-progress` (step added) and `step-removed` skip batch-stamped events. The other `journey.step_updated` and `journey.step_removed` listeners (engagements `step-status-changed`, `step-reminder`, journeys `step-removed`) aren't notification senders and still run, which is correct.
- **Excluding the pro:** `findByJourneyAndActor` returns `JourneyParticipant | null`. `professional?.accountId` handles null, and `notifyParticipantsInApp` treats an undefined `excludeAccountId` as an empty set (`participant-notifier.service.ts:167-168`).
- **Errors:** both new handlers catch and log, so a failing listener can't reject `applyJourneyEdits` after the write has been committed.