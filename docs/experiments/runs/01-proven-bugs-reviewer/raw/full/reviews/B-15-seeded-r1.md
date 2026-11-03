I found 2 Important issues and 1 Nit.

**1. Important: the PATCH step endpoint no longer clears a field when it is sent as `null`.**
- Evidence: `src/modules/journeys/journeys.service.ts:617-621`:
  ```ts
  for (const field of nullableFields) {
    const value = input[field]
    if (value === undefined || value === null) continue
  ```
  `unsetFields` (`:587`) is still declared and passed to the repo at `:637`, but nothing ever adds to it now. Before this change, `null` for `description`, `plannedDurationHours`, `startedAt`, `dueAt`, `completedAt` and `gamify` added the field to `unsetFields`. Now a `null` value is silently ignored, so all six fields are affected.
- How I proved it: a scratch spec using the real Mongo setup from `journeys.service.spec.ts`, run with `pnpm test -- src/modules/journeys/zz-review.spec.ts`. It called `updateStep(id, step, { description: null, dueAt: null })`.
- Printed: `after null update: description= {"en":"d","es":"d"} dueAt= 2026-12-01T09:00:00.000Z`, then `Received: {"en": "d", "es": "d"}`.
- Expected: `description` and `dueAt` removed. Sending `null` to clear a field is the existing contract this diff broke.
- Fix: in the `null` branch, push the field into `unsetFields`.

**2. Important: `set_step_due_date` treats any due date on the same calendar day as "no change".**
- Evidence: `src/modules/journeys/journey-edits.planner.ts:389`:
  ```ts
  if (step.dueAt?.toDateString() === dueAt?.toDateString()) return
  ```
  This compares only the day, in the server's local timezone. The code it replaced in `journey.tools.ts` compared `getTime()`.
- How I proved it: same scratch spec. On a step due `2026-12-01T09:00:00Z`, it called `applyJourneyEdits` with `{ op: 'set_step_due_date', dueAt: '2026-12-01T17:00:00Z' }`.
- Printed: `Rejected to value: [JourneyEditsInvalidError: Invalid journey edits]` (code `no_change`).
- Expected: the time change gets applied. The schema accepts full datetimes (`z.iso.datetime({ offset: true })`), so the agent gets a `no_change` it can't do anything about. Whether two instants count as the same day also depends on the server's timezone.
- Fix: compare `getTime()`.

**Nit: the step ids shown on the card for new steps are never the ids actually saved.**
- Evidence: `proposeEditJourney` (`journey.tools.ts`) and `applyJourneyEdits` (`journeys.service.ts:672`) each call `planJourneyEdits`. Each call generates new ids with `new Types.ObjectId()` (`journey-edits.planner.ts:40`).
- So `stepId` in the `add_step` and `add_section` previews (`journey-edit-preview.ts:20,46`) never matches what gets stored. That only causes trouble if the frontend or a later turn refers to those ids.
- Not run: it would need the proposal-decision flow run from start to finish.

I also checked whether renaming a section sends `journey.step_updated` events for steps it didn't touch. It doesn't: no events were emitted. I deleted the scratch spec afterwards, so the working tree is as I found it.