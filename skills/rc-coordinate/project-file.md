# Project file template

The coordinator reads `docs/agents/coordinate.md` in the work repo at setup. Copy the block below there and fill it in. Point at the repo's own docs rather than copying them: the file holds only what the coordinator and its workers need to find. A field left empty is asked at setup.

```markdown
# Coordinated runs

Read by the rc-coordinate skill at setup. Rules here are settled before a run starts.

## Landing

- Mode: <branch | pr>
- Target branch: <e.g. develop>
- Push policy (branch mode): <no push | push after each landing>
- Wave size: <none, or a number>

## Merge rules (PR mode)

Per area when the rules differ (by path glob):
- Who may merge: <the coordinator, when the rules below are met>
- Approvals needed: <which reviewers or teams, and what counts as an approval>
- CI needed: <which checks must be green>
- Method: <squash | merge | rebase>

## Posting rules (PR mode)

- PR body: <template or doc pointer>
- Where to ask for review, and in what order: <channels, or a doc pointer>
- Re-review requests: <when, and where>
- Who may post: the coordinator posts outside the PR; workers reply only on their PR's review threads.

## CI

- Read a PR's checks: <command>
- Rerun or retrigger: <command, and what it does and does not rerun>
- Read the target branch's latest result for a test: <command or doc pointer>

## Preflight

One line each: what to check, the command, and the fix when it fails.
- <container runtime>: `<command>` → <fix>
- <cloud login>: `<command>` → <fix>
- <tokens, package registries, tools the hooks need>: `<command>` → <fix>

## Worktrees

- Create: <command, e.g. the repo's worktree script>
- Warm-up after create: <commands, e.g. install, build the local packages>
- Remove: <command>

## Slots

Beyond `suite`: <name — what it guards — how a holder restores it on release>

## Banned

<commands, beyond the protocol's>

## Pointers

<the repo's docs on CI, review routing, environment traps>
```
