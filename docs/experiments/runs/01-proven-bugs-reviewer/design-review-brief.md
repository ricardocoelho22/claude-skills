# Design review — experiment 01, proven-bugs reviewer

You are reviewing a **measurement**, not product code. One question: **what makes this measurement not measure the claim?**

## Read

- The design: `/Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer.md` (sections *Inputs* and *Design*). The claim is there, with the decision rule.
- The harness: every file under `/Users/ricardocoelho/Code/claude-skills-experiment-01-proven-bugs-reviewer/experiments/01-proven-bugs-reviewer/` (untracked; `git -C /Users/ricardocoelho/Code/claude-skills-experiment-01-proven-bugs-reviewer status` lists it; it is all new, so read the files directly).
- The smoke raw rows and outputs: `/Users/ricardocoelho/Code/claude-skills/docs/experiments/runs/01-proven-bugs-reviewer/raw/smoke/` (`reviews.jsonl`, `reviews/`, `claude-json/`, `extracted/`, `graded/`, `grader.jsonl`, `summary.json`).
- The prepared input, to check seeds against the real code: `/Users/ricardocoelho/Code/sidedoor/worktrees/exp01-29-seeded/backend` (read only; a smoke re-run may reset it while you read, so prefer `git -C <it> diff` over timing-sensitive reads).
- The floor of confounds to check, not the scope: `/Users/ricardocoelho/Code/claude-skills/skills/rc-experiment/confounds.md`. The *What gets judged* section matters most here.

## Already known — do not re-report

The orchestrator has already found these; extend them only if you find more instances or a consequence it missed:

1. Seed S3 (`contacts.repo.ts:50`, whitespace-only search) is unreachable: both callers trim and require min(1) (`contacts.dto.ts:78`, `agent/tools/contact.tools.ts:17`). Both arms correctly reasoned it away.
2. The grader missed B's finding at `journey-invitations.seed.ts:415`, which is the same defect as S4 and A's hit, because B's line number is wrong (the file has 137 lines) and it does not name the function. The hit rule is too literal for wrong line numbers.
3. The arms' permissions differ beyond the variable: A has `autoAllowBashIfSandboxed: false` plus a read-only Bash allowlist, so compound read commands are denied; B auto-allows Bash in the sandbox.

## Report

Each finding names: the confound, its evidence (file:line in the harness or a quoted raw row), a severity (`invalidates`: the result would be wrong; `weakens`: the result needs a caveat; `note`), and the cheapest fix. Lead with the count by severity. Under 600 words. Verify each finding by reading; a speculative finding costs a fix round.
