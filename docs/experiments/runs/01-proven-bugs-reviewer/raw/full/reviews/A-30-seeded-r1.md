I found 2 issues: 2 Important, 0 Nit, 0 Pre-existing.

**1. Important: the cycle check can stop before it has checked every path, so it misses real cycles.**
`src/modules/journeys/journey-edits.planner.ts:152`
```ts
const step: JourneyStep | undefined = steps.find((step) => step.id === id)
if (step?.precedents.length === 0) return false
if (step) pending.push(...step.precedents)
```
`reachesStep` walks a stack of steps that still need checking. As soon as it pops one step with no precedents, it returns `false` for the whole search, even when other entries are still on the stack.

Here is a case that gets through. Step B has precedents `[C, D]`, D has none, and C has precedents `[A]`. The op is `update_step` A with `precedents: [B]`.
- The stack becomes `[C, D]`.
- `pop()` takes D first, and D has no precedents, so the function returns `false`.
- The A→B→C→A cycle is never found and gets saved, which breaks the ticket's `precedent_cycle` criterion.

Fix: replace the `return false` with `continue`, or delete the line, since the `visited` set and the final `return false` already cover that case.

**2. Important: the proposal card drops precedents for any new step that has two or more of them.**
`src/modules/agent/tools/journey-edit-preview.ts:27`
```ts
...(precedents?.length === 1 ? { precedents: previewPrecedents(precedents) } : {}),
```
This preview is used for `add_step` (line 77) and for the nested steps in `add_section` (line 48). Both the planner (`addStep` at planner.ts:370 and `addSection` at :287) and the input schema accept a list of any length. So a new step with 2 or more precedents shows no precedents on the card. When the user approves, those dependencies are still saved (`createStep` at :243), which they never saw.

Fix: use `precedents?.length ? …`, or `precedents?.length > 0`. The spec fixtures at `agent-edit-journey.spec.ts:288` and `:298` only use one precedent per step, which is why this passes the tests.

Things I checked that hold up:
- **Dangling ids:** a new step can name a step that a later op in the same batch removes. That id is cleaned up after commit by `step-removed.listener.ts:95` (via `journeys.repo.ts:235` `$pull`).
- **Lock state:** `journey-created-progress.listener.ts:31` ignores dangling ids.
- **`get_journey` output:** `projectJourney` now filters dangling ids.
- **Saving:** `journeys.service.ts:676-681` saves `plan.steps` as-is, so precedents are stored.