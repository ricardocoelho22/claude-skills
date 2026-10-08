---
name: diff-tour
description: Write a short reading guide to a diff, saying which files to read first, what changed, and which decisions were made. Use when the user wants to be walked through a branch, PR, or set of changes before reading or reviewing it.
---

A diff in file order is a bad reading order. The tour gives the human a path through the code, so they read the core of the change first and the ripple last. It orients the reader. Judging the code is `/code-review`'s job.

## Gather

- **Base**: the commit given, else `git merge-base HEAD <default-branch>`.
- **The diff**: `git diff --stat <base>`, then `git diff <base>` in full. Run `git add -N` on untracked files first so they show.
- **The intent**: the ticket or spec when there is one, and `git log <base>..HEAD`.

## Order the reading

Start with the file where the behavior lives, then the files that call into it, then wiring and config, then tests. Generated files, lockfiles, and snapshots go on a skim line.

Done when: every changed file is either in the read order or on the skim line.

## The tour

Around 15 lines, exactly this shape:

```
## <branch or ticket> — <title>
Read first: <file> (<why>), then <file> (<why>), then <file>
Skim: <files, or "none">
Changed: <n> files, +<a> −<d>

Key changes:
- <up to 3: behavior that changed, where>
Decisions:
- <up to 3: choice made — reason>
Watch for: <up to 2: things that deserve a careful eye, or "none">
```

A decision's reason comes from the spec, a commit message, or a code comment. When none records it, write "reason not recorded" rather than supplying one. **Watch for** is the place for behavior outside the stated intent, deleted code paths, migrations, and changes to shared config.
