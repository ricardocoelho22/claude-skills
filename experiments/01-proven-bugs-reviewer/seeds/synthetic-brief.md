You are planting a bug for a code-review experiment. Work in the current directory (a git worktree of a NestJS backend with uncommitted changes under review). `git diff HEAD` shows the change set; it already contains three planted bugs in src/seeds/contacts.seed.ts, src/seeds/pro-microsites.seed.ts and src/seeds/journey-invitations.seed.ts. Leave those alone.

Plant exactly ONE NEW bug. Rules:
- It is a one-hunk mutation (a few lines) in NON-TEST source code in a file the diff touches (see `git diff HEAD --stat`; never *.spec.ts, never evals/agent/CASES.md or README.md, never evals results).
- It sits in a DIFFERENT function from the three existing planted bugs (seedContacts, seedProMicrosites, seedJourneyInvitations).
- Its class is one of: empty/null handling, boundary (off-by-one, inclusive/exclusive), unhandled error path, broken caller of changed code. (Not missing authorization: another seed already is.)
- REACHABLE: a real caller or entry point (controller, service, agent tool, seed runner, scheduled job) must be able to reach the broken behaviour at the seeded state, with input that caller really passes. Read every caller before you settle on the mutation: check what each one validates, trims, defaults or guards, and what the DTO and schema constrain. A mutation whose bad input no caller can produce is NOT a defect; do not plant it.
- A realistic mistake a developer could make: no comments, no renames, no dead code, nothing that signals the edit. The code must still typecheck and the existing tests covering the file must still pass (run `pnpm typecheck` and `pnpm exec jest <spec files for the changed files> --runInBand`; if the sandbox blocks jest, say so and run typecheck at least).
- The bug must be a real behavioural defect in code the diff added or changed, not in untouched code.
- Do not touch git state (no commit, no stash, no checkout).

Final message: one line exactly in the form
`<file>:<line> · <function> · <effect> · reached via <caller file:line>`
where line is the line of the mutated code after your edit, function is the enclosing function, effect is one sentence on what goes wrong, and the caller is the file:line where the bad input arrives from a real caller. Then one line stating the class, and the commands you ran with pass/fail.
