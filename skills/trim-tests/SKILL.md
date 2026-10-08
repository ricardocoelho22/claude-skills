---
name: trim-tests
description: Trim freshly written tests down to the ones that earn their place, deleting and merging only. Use when the user wants tests trimmed, pruned, or de-duplicated, or after test-first work (`/tdd`, `codex-implement`) has over-produced tests.
---

Test-first agents over-produce: the same behavior pinned twice, tests that assert on a mock, tests that reach past the seams into internals. This skill cuts them. The trim rule and the removal reasons live in `~/.claude/agents/impl-trimmer.md`; the `impl-trimmer` agent applies them, and you set the scope and verify.

## 1. Scope

Pin the **base**: the commit the user names, else `git merge-base HEAD <default-branch>`. The tests in scope are the test files changed since base, untracked ones included:

```
git diff --name-only <base>
git ls-files --others --exclude-standard
```

Tests that existed before base are out of scope even if they look redundant: someone already agreed to them.

Done when: you hold the base and the list of test files in scope.

## 2. Seams

The seams decide which tests are off-seam, so wrong seams mean wrong cuts. Take them from the user, the spec, or the plan the tests were written against. With none of those, infer them from what the tests call (the public functions, endpoints, components they drive) and confirm the list with the user before going on.

Done when: every test file in scope maps to at least one confirmed seam.

## 3. Snapshot

Copy every in-scope test file into a scratch dir, and save `git diff --stat <base>` there. These are the "before" you verify against.

## 4. Trim

Spawn `subagent_type: impl-trimmer` with a self-contained brief: the test file paths, the seams verbatim, the single-test-file command (verified from the project's config), and the package manager.

## 5. Verify

The trimmer's return is a claim. Check it yourself:

- **Deletes and merges only.** Diff each test file against its snapshot (`git diff --no-index`): every hunk removes tests or folds them together, and every surviving assertion is unchanged.
- **Production untouched.** `git diff --stat <base>` matches the saved one on every non-test file.
- **Green.** Run the single-test-file command for every touched file.
- **Reasoned.** Every removal in the return carries one reason: duplicate, mock-only, or off-seam.

A failed check gets the trim reverted from the snapshot, and the failure goes to the user.

## Report

The removals and merges, one line each with the reason, then the test command output.
