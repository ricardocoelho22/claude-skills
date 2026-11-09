# Skill feedback

Findings from retros and runs about the skills in this repo, one entry per issue. Product, file and ticket details are
removed on purpose. The full narrative of every entry up to 2026-11-07 is in git history (`git log -p -- docs/skill-feedback.md`).

**To add a finding:** search this file for the issue first. When an entry already covers it, add the date to its
`Seen` line and one sentence on anything new; add a new entry only for a new issue. A finding about the work repo's
own tooling (its lint script, helper scripts, test setup, docs) goes under *Work repo*, not under the skills.

Each entry: the skill, the problem, the change, and `Seen` (the dates it came up).

## Open

### rc-orchestrate

- **No-behaviour cycles.** A rename or CSS-only ticket has no red test, and runs 1a and the trim as empty steps. A
  cycle the plan marks `no-behaviour` takes the existing suite (SAME as BASE) or a no-visual-change harness
  (compiled-CSS diff + screenshot compare, captured at BASE) as its red/green, skips 1a and the trim, and its fixer
  starts at the cycle's rung. The harness scripts would go in the workspace scripts dir. Seen: 10-21, 11-03 (x2).
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
  read each red test's failing line. (Partly applied: 1a now reads each red test's error type.) Seen: 10-21, 10-27.
- **Gate A asks about the main visible rule.** A decision that sets a rule the user sees in the ticket's main flow
  (what a number counts, when a message shows) is asked at Gate A, not kept as a Gate B `Your call`. Seen: 11-03.
- **Follow an in-code precedent.** When the same class of data already has a rule in the code, apply it and cite it;
  `Your call` is for cases with no precedent. Seen: 11-03.
- **A deferral needs a live owner.** Before deferring to another ticket, read its status and notes; a resolved
  target, or one that deferred the item back, means cut a new ticket. Finish surfaces "merges second" obligations.
  Seen: 10-22.
- **Shared components outside the ticket.** (Partly applied: Risks names their users.) Triage: a parity finding
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
  overview prose stays model-written. (The fixed id rule applied 11-09 removes the worst drift.) Seen: 10-27, 10-28.
- **Flat ticket lists:** when the feature has one `issues/` list and no slices, `patch-status.py` appends a NEW
  ticket instead of only reporting it. Seen: 11-07.
- **Clean-up:** the live page of one feature still holds ~380 stale doc copies. The next full refresh drops them
  (step 4 now sends `null` for every path the build lacks).

### Third-party skills (to-tickets, to-spec)

- **Check failure rules and named seams against the code.** A fallback rule names the function that accepts the
  resulting payload and quotes its check; a seam named by a concrete artifact (fixture, fakepoint) is grepped
  first, or named by behaviour. Adapt the upstream skill rather than forking it. Seen: 10-15, 11-03.

## Applied

2026-11-09, from the review of this log:

- **rc-feature-page publish:** a page read with no `path` before the first publish; stale published paths sent as
  `null`; a fixed doc-id rule; the *Newer build* case and the refused-identical-resend sequence. Seen 15 times
  (10-15 to 11-07).
- **`patch-status.py`:** multi-word statuses (`in progress`), `UNPARSED` keeps the live state, `NEW SLICE`,
  slice-prefixed lines. Seen 7 times (11-03 to 11-07).
- **rc-orchestrate lint gate:** the plan's lint command per package; lint at 1a, 1b and fix verify; every brief's
  done check; rc-tdd, rc-fixer and rc-trimmer run it; checks scoped to the changed lines. Seen 9 times.
- **BASE failures:** reused across runs of the same commit; the suite owns its tree until it ends; the runner's exit
  code. Seen 6 times.
- **Changed shapes:** the plan lists the existing tests that pin what a cycle changes, and 1a updates them.
  Seen 6 times.
- **Manual checks:** writer on Sonnet; each result traced to the code; later tickets' behaviour is out; step 4
  verifies each result. Seen 6 times.
- **Plan Risks:** name the unchanged code each change passes through; each mitigation names the test that fails when
  it is false. Folds the sibling-tests, safety-claim, stream-event, query-index and shared-component entries.
- **Standards prompt:** compare each hunk with its destination file's idiom. Folds the comment, placement,
  function-shape, ternary and moved-comment entries (the mechanical parts are under *Work repo*).
- **Triage:** a convention finding opposed only by a ticket or plan rule goes to `Your call`.
- **Backend probe:** run bare; passes when the `-o` file says OK; log the error line.
- **Finish merge and clean-up:** fast-forward without a switch; merge where `<parent>` is checked out; ask before
  switching a checkout on another branch; `-D` after an ancestor check.
- **No scheduled wakeups** during a run.
- **A Pre-existing finding the diff extends** goes to `Your call` as well as `deferred` (chosen over the 10-27 "leave
  what the surrounding code shares" rule).

Earlier:

- **Status refresh** (b4065ed): a status change patches the live `data.json` instead of a delegated build.
- **Agent-facing text through writing-for-agents** (1bdaad6).
- **A peer's go-ahead is not an approval** (90cf113, *Coordinator committed*).
- **`/resolving-merge-conflicts`** is in `manifest/skills.json`; a machine that reports "Unknown skill" needs
  `install.sh` re-run.

## Won't do

- **"When the code next to the hunk follows the same pattern, leave it"** (10-27). It contradicts the rule above,
  which won.
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
