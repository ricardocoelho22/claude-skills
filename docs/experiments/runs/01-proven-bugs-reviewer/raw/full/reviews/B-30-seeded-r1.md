I found 2 Important issues, 0 Nits and 0 Pre-existing. I ran a throwaway spec in `src/zz-probe/` with `pnpm test -- src/zz-probe/probe.spec.ts`, then deleted it. The code under review is unchanged.

**1. Important: cycle detection gives up early and lets cycles through.**
`src/modules/journeys/journey-edits.planner.ts`, in `reachesStep`:
```ts
const step = steps.find(...)
if (step?.precedents.length === 0) return false
if (step) pending.push(...step.precedents)
```
The search returns `false` as soon as it pops any step that has no precedents, even when other branches are still waiting in `pending`. So a cycle check fails whenever one branch hits such a step before the branch that loops back is explored.
- **Setup:** step P waits on [Q, L], Q waits on [T], and L waits on nothing. Then send `update_step` T with `precedents: ['P']`, which closes T→P→Q→T.
- **Output:** `CYCLE RESULT "accepted"`
- **Ticket requires:** the batch is rejected with `precedent_cycle`.
- **Fix:** replace the early `return false` with `continue`, or drop that line. The loop's final `return false` already covers the case where nothing reaches the target.

**2. Important: the proposal card drops precedents when a new step has more than one.**
`src/modules/agent/tools/journey-edit-preview.ts`, in `previewNewStep`:
```ts
...(precedents?.length === 1 ? { precedents: previewPrecedents(precedents) } : {}),
```
The preview only includes precedents when there is exactly one. With two or more, the card shows nothing, but the planner still saves them because `createStep` stores the full list. The user would approve dependencies they never saw. This affects both `add_step` and the steps nested in `add_section`, which go through the same function.
- **Setup:** `add_step` with `precedents: ['A','B']`.
- **Output:** `PREVIEW {"op":"add_step",...,"step":{"title":{"en":"N","es":"N"}}}`, with no `precedents` key.
- **Ticket requires:** "Proposal card renders precedent changes", so the step should carry `precedents: [{stepId:'A',...},{stepId:'B',...}]`.
- **Fix:** change the condition to `precedents?.length`.

The rest of the diff looked sound: the validation order (step exists, then missing precedent, then self, then cycle), removing duplicate ids, `[]` clearing the list against only the precedents that still exist, the change to the `update_step` refine check, and filtering dangling ids in `projectJourney`.