---
name: manual-checklist
description: Write the short list of checks a human does by hand to accept a change. Use when the user wants a manual test checklist, QA steps, or "what should I click through" for a branch, PR, or ticket.
---

Automated tests pin behavior at the seams. What they leave is the part a human verifies by looking: visual states, UI flows, timing, copy, real external services. This skill writes that part down, so a tester gets from the diff to the hand checks without reading code.

## Inputs

- **The change**: `git diff <base>`, where base is the commit given, else `git merge-base HEAD <default-branch>`.
- **The intent**: the ticket or spec when there is one. Without it, the commit messages.

Read both in full.

## The checklist

At most 10 items, ordered as a tester walks them. Each item is one line, an action and its observable result:

```
- [ ] <do this> → <see this>
```

An item earns its place when a human must perform it: the result is something seen, felt, or timed, or it crosses a boundary the tests mock (a real email arrives, a real payment clears). Behavior a test already pins is covered; leave it to the tests.

Cover every user-visible surface the diff touches, and each one's empty, error, and loading states where the diff changes them. A change with no human-observable surface gets no checklist: say so in one line instead.

Done when: every user-visible surface in the diff has an item or is named as test-covered, and the list is 10 items or fewer.

## Output

Save as `manual-test-<slug>.md` next to the ticket when there is one, or where the caller names; otherwise return the checklist in chat. Head the file with one line naming the ticket or branch and the base.
