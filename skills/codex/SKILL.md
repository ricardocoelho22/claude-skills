---
name: codex
description: Route a single task to the codex CLI and capture the result. Use when the user wants work handed to codex ("have codex do X", "run codex on this", "delegate this to codex"), or when another skill needs the mechanics of invoking codex.
---

Codex is a peer agent you drive non-interactively with `codex exec`. This skill is the routing mechanics — hand it one task, get the result back. It carries no methodology; for the code implement → review → verify pipeline, see `codex-implement`.

Codex shares this machine's skill library (`.agents/skills`), so a brief can name `$tdd`, `$code-review`, `$research` and codex loads that skill itself. There is no `$implement` on the codex side.

## Invoke

```
~/.claude/skills/codex/scripts/codex-run.sh -C <dir> -s workspace-write \
  -o <scratch>/codex-<label>.md \
  "<brief>"
```

- `-o <file>` — codex writes its final message here; this plus the git diff is how you take delivery.
- `-s workspace-write` — codex edits the working tree and runs commands non-interactively; escalations outside the sandbox simply aren't available, which is what you want. (`--approve-for-me` conflicts with `-s` in current codex, and used alone it trips Claude Code's permission classifier — the sandbox flag alone is the working form.)
- `-C <dir>` — working root (defaults to cwd).

The wrapper runs `codex exec` (the `exec` is implied) and:

- **Closes stdin.** Codex appends stdin to the prompt and blocks until EOF, so an open stdin hangs a backgrounded run forever at 0% CPU. Set `CODEX_STDIN=1` to pipe stdin in on purpose.
- **Keeps the transcript out of your context.** The full run goes to a log (`CODEX_LOG`, or a temp file); stdout carries only the log path and a one-line status. Read the log only to diagnose a failure.
- **Makes failures loud.** Exit 2: codex reported an error (bad model, usage limit). Exit 3: no `-o` output. A non-zero codex exit passes through. Every failure prints the log's last lines. A stale `-o` file from an earlier run is deleted first, so it can't pass as this run's output.

Long runs: launch with Bash `run_in_background` and read the `-o` file once it exits.

**Follow-up on the same session** (keeps codex's context and cache warm), run from the same directory:

```
~/.claude/skills/codex/scripts/codex-run.sh resume --last -o <scratch>/codex-<label>-2.md "<follow-up>"
```

## Model and effort

Inherited from `~/.codex/config.toml` (`gpt-6-sol`, high). Override per call:

- `-m <model>` — a slug from `codex debug models`. GPT-6 tiers:
  - `gpt-6-astra` — frontier; design-heavy or judgement-heavy work.
  - `gpt-6-sol` — workhorse; the default for implementation and review.
  - `gpt-6-luna` — fast and cheap; mechanical passes, triage, quick lookups.
- `-c model_reasoning_effort=low|medium|high|xhigh|max` (`ultra` on astra and sol).

A model the account cannot use fails 400, which the wrapper turns into exit 2: check `codex debug models` before overriding.

## Sandbox

- `workspace-write` (default) — codex may edit the working tree.
- `read-only` — plan-only, no writes; use when the user wants a proposal first.
- `danger-full-access` — only when the user explicitly asks.

## Take delivery

Codex edits files in place. To receive the result:

1. Read the `-o` file — codex's own account of what it did.
2. Run `git diff` / `git status` — the actual changes.

When you need a parseable answer (a verdict, a list), add `--output-schema <file.json>` and codex returns JSON matching that schema.

Codex's output is for you, the orchestrator. Act on it and relay what matters — don't paste raw codex transcripts at the user unless they help.
