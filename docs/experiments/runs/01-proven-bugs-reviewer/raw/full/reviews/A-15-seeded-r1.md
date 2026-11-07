I found 2 Important issues in the diff and no Nits or Pre-existing problems.

**1. Important: a `null` in the step PATCH no longer clears the field.** `src/modules/journeys/journeys.service.ts:617-621`
```ts
for (const field of nullableFields) {
  const value = input[field]
  if (value === undefined || value === null) continue
  Object.assign(update, { [field]: value })
}
```
The old code put `null` values into `unsetFields`. The new loop skips them, and nothing adds to `unsetFields` any more (it is declared at :587 and passed to `journeysRepository.updateStep` at :637). The DTO still accepts `null` to clear six fields (`journeys.dto.ts:211-220`), and `PATCH` reaches this method through `journeys.controller.ts:406`. Affected fields: `description`, `plannedDurationHours`, `startedAt`, `dueAt`, `completedAt`, `gamify`. A user who clears a due date or description gets a success response, but the old value stays. This sits in the manual step endpoint, outside the ticket's scope, and no spec in the diff tests clearing with `null`.

**2. Important: changing only the time of a due date is rejected as "no change".** `src/modules/journeys/journey-edits.planner.ts:389`
```ts
if (step.dueAt?.toDateString() === dueAt?.toDateString()) return
```
The input schema accepts full datetimes (`journey.tools.ts`, `editDateSchema = z.union([z.iso.date(), z.iso.datetime({ offset: true })])`). The old preview compared `getTime()`. The new check compares calendar days only, so moving a step from 09:00 to 17:00 on the same day is dropped. If it is the only op, the whole batch fails with `no_change`. `toDateString()` also uses the server's local timezone, so whether two instants count as "the same day" depends on where the server runs. Root cause: the comparison should use `getTime()`, or compare in UTC if day-level matching is what's wanted.

Checked and found sound:
- **Batch handling:** batches validate atomically, and an invalid op rejects the whole batch.
- **Write guard and retry:** the single write is guarded on `updatedAt` and retried once, ending in `JourneyEditConflictError`.
- **Error mapping:** the tool handler and the proposal path both map `JourneyEditsInvalidError` to `AgentInvalidOperationsError`, and approval records the `invalid_operations` details.
- **Precedents:** references to removed steps are still cleaned up through the `journey.step_removed` event listener.