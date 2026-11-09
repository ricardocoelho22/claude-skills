# Skill feedback

A running list of the open findings from retros and runs about the skills in this repo, one entry per issue. Product,
file and ticket details are removed on purpose. Git history holds everything that has left the list
(`git log -p -- docs/skill-feedback.md`).

**To add a finding:** search this file for the issue first. When an entry already covers it, add the date to its
`Seen` line and one sentence on anything new; add a new entry only for a new issue. A finding about the work repo's
own tooling (its lint script, helper scripts, test setup, docs) goes under *Work repo*, not under the skills.

**When a finding is applied,** the commit that applies it deletes its entry (or the applied part of it). A finding
decided against moves to *Won't do* in one line with the reason, so later retros don't propose it again.

Each entry: the skill, the problem, the change, and `Seen` (the dates it came up).

## Open

### rc-orchestrate

- **No-behaviour cycles.** A rename or CSS-only ticket has no red test, and runs 1a and the trim as empty steps. A
  cycle the plan marks `no-behaviour` takes the existing suite (SAME as BASE) or a no-visual-change harness
  (compiled-CSS diff + screenshot compare, captured at BASE) as its red/green, skips 1a and the trim, and its fixer
  starts at the cycle's rung. The harness scripts would go in the workspace scripts dir. A visual harness proves itself
  at BASE: two runs byte-identical (animations off, fixed width), and one sabotage run (the change removed, files
  restored from a checkpoint tree) that differs. Seen: 10-21, 11-03 (x2), 11-09.
- **Test-only tickets.** When the code under test exists, every test is green before any production code, and 1b has
  nothing to do. Prove each test by a red run with the behaviour under test removed (a stub, or the call deleted in a
  throwaway copy, never the worktree), skip 1b, and log the red output. Seen: 11-09.
- **Seams obey the repo's testing rules.** Before a seam goes into the plan, read every rule file whose path scope
  matches the cycle's test files, and quote the rules that limit what a test may assert; neighbouring tests are no
  guide. A requirement no test may check becomes a manual-guide item and a Gate B deviation. Seen: 11-09 (x2).
- **A removed teardown needs a seam per effect.** When a change removes or moves a teardown (unmount hook, dispose,
  finally), Risks lists every effect it ended (timers, in-flight requests, listeners) and gives each a seam. Seen: 11-09.
- **Test setup that writes shared state.** Recon reads the autouse fixtures on each test command's path and lists
  every write outside the test's own data; a write to a shared stack is a Gate A question. Seen: 11-09.
- **A failed backend probe means `claude`, at once.** Record the backend and move on; read the error only to log it.
  Seen: 11-09.
- **A BASE command with no summary line counts as failed** until its exit code says otherwise. Seen: 11-09.
- **Standards: a convention claim cites the same file.** A finding that a hunk breaks a file's or folder's convention
  cites two instances of it in that file or folder. Seen: 11-09.
- **Prompt-wording tickets measure live.** A ticket that changes text a model reads takes its red/green from a live
  repeat measurement: tighten the fixtures (1a), measure BASE with N repeats, measure each candidate, include
  off-target cases, and put the spend envelope to the user at Gate A. Point at `rc-experiment` for the mechanics. A
  regression case for a live-model bug replays the real turns, states each turn's seed preconditions, and gets a
  single-repeat smoke at BASE first. Seen: 10-23, 11-07 (x2).
- **Product facts need a source.** A Gate B `Your call` that rests on a product fact names its source (glossary,
  schema, UI component). For agent-facing text, the Bugs prompt adds "verify every product claim the text makes
  against the code and the glossary". Seen: 11-07.
- **Re-read the ticket before Gate B.** Save a copy in Phase 0 and diff it before the report; parallel sessions append
  requirements mid-run. Seen: 10-21.
- **A red test fails at its behavioural assert.** A test red at its first assert can hide an error on a later line;
  read each red test's failing line. Seen: 10-21, 10-27.
- **Gate A asks about the main visible rule.** A decision that sets a rule the user sees in the ticket's main flow
  (what a number counts, when a message shows) is asked at Gate A, not kept as a Gate B `Your call`. Seen: 11-03.
- **Follow an in-code precedent.** When the same class of data already has a rule in the code, apply it and cite it;
  `Your call` is for cases with no precedent. Seen: 11-03.
- **A deferral needs a live owner.** Before deferring to another ticket, read its status and notes; a resolved
  target, or one that deferred the item back, means cut a new ticket. Finish surfaces "merges second" obligations.
  Seen: 10-22.
- **Shared components outside the ticket.** Triage: a parity finding
  between a changed shared component and an out-of-scope page is fixed by keeping the outside page as it was (a
  variant or prop), never by extending the change. Seen: 11-07.
- **One combined reviewer for small style-only diffs.** Under ~100 lines with no logic: one `rc-reviewer` with all
  three briefs. Seen: 11-03.
- **A pure-move Gate B round skips the reviewer** when every added line equals a removed line; log the check.
  Seen: 10-28.
- **The trim's delta reaches Gate B unreviewed.** Step 5 verify: a line the trim changed (not only deleted) reads as
  intended. Seen: 11-07.
- **New browser tests run three times at 1b verify,** so a flaky new test is a cycle rejection. Seen: 10-21.
- **Short locator wait for red Vitest browser runs.** A red `expect.element` waits its full timeout (~18 min per red
  file). Seen: 10-29.
- **Briefs:** test names describe behaviour, with no ticket numbers (10-21); every choice a brief leaves to the
  executor already meets the repo rules of the files in scope (11-03); a single-file test command handed down by a
  coordinator is run once at BASE, and a count of 0 means it is wrong (11-07).
- **Codex across two repos:** one call with `--add-dir <other worktree>` (exec only; `resume` drops it). Seen: 11-07.
- **Bugs brief for eval fixtures:** check each forbidden phrase against the wording the prompt itself asks for.
  Seen: 11-07.
- **Test-framework update pending on the parent:** put the new test-API rules in every test-writer brief from
  cycle 1. Seen: 11-03.

### Role files (rc-tdd, rc-fixer, rc-trimmer)

- **Work in the worktree's own state.** To compare with the base, use the checkpoint tree or `git show <base>:<path>`;
  to set work aside, a WIP commit (the stash stack is shared by every worktree and session). The report is the last
  action: wait for every check started, and return with no background process. After a lint `--fix`, keep only the
  call's own files. Seen: 10-21, 10-26, 10-27.
- **Test-writer mode leaves production files untouched for the whole call,** even temporarily, and writes the rule
  behind each expected value beside the assertion. Seen: 10-28.

### rc-feature-page

- **One checked-in generator script** for the delegated build, so builds stop drifting in shape; only the
  overview prose stays model-written. Seen: 10-27, 10-28.
- **Flat ticket lists:** when the feature has one `issues/` list and no slices, `patch-status.py` appends a NEW
  ticket instead of only reporting it. Seen: 11-07.
- **Clean-up:** the live page of one feature still holds ~380 stale doc copies. The next full refresh drops them
  (step 4 now sends `null` for every path the build lacks).

### rc-manual-checks

- **Each check names its precondition.** What must be on screen or in the queue first, and the code that sets it up;
  a result without one over-claims. Seen: 11-09 (the fourth over-claim).

### Third-party skills (to-tickets, to-spec)

- **Check failure rules and named seams against the code.** A fallback rule names the function that accepts the
  resulting payload and quotes its check; a seam named by a concrete artifact (fixture, fakepoint) is grepped
  first, or named by behaviour. Adapt the upstream skill rather than forking it. Seen: 10-15, 11-03.

## Won't do

- **"When the code next to the hunk follows the same pattern, leave it"** (10-27). It contradicts the rc-orchestrate
  rule that a Pre-existing finding the diff extends goes to `Your call`, which won.
- **A backend switch (`RC_BACKEND=claude`) to skip the codex probe.** The credentials trap (13 runs, 10-24 to 11-03)
  cleared on 11-07; the probe costs seconds.
- **Domain checklists in the plan or briefs** (index per query, per-item try in loops, pointer reset in screenshot
  harnesses, seeded shuffle replays). Covered by the Risks principle, or by the work repo's own rules.

## Work repo

Findings about the work repo's tooling. They belong in that repo's backlog.

- **Changed-files lint script:** flag a module-level constant after the first `def`/`class` (escaped 3 times); a
  private (underscore) name imported from another module; a `def` added to a file over ~5000 lines; a `for` nested in
  a `for` in one function; print tree-wide checks under their own heading, marking hits outside the change.
- **Worktree helper script:** on pytest exit 137, print `KILLED (137)` and exit 137 under a pipe (seen 7 times in one
  run); `--no-warm` keeps `pnpm install`; build PYTHONPATH from the copied trees; after a non-ff merge, run the
  target's suite. Done: the checkpoint command, the suite command's `TREE CHANGED` guard, the merge command's lock.
- **A move-code recon script:** given the old module and the moved names, grep the four patch shapes (string target,
  `patch.object`, module-prefix f-strings, logger-name filters) on HEAD and the development branch.
- **Frontend test setup:** a stubbed `<Transition>` keeps a closable notification from emitting `close`; fix the stub
  or add a trap.
- **Testing rules:** the two rules files disagree on `test.for` vs `test.each`; make them agree and lint it.
- **Sinks doc:** add the transcript reader, what it drops, and the raw id reader to use instead.
- **Codex wrapper:** export the shared-credentials file when the token refresh loop has written temp credentials
  (only if the 10-24 trap returns).
