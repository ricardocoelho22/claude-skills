---
name: rc-experiment
description: "Run a measurement ticket (a spike, a cost or quality experiment) as an orchestrator: agreed design, harness, smoke run, adversarial review, full run, research file."
disable-model-invocation: true
argument-hint: "path to the experiment ticket"
---

# Orchestrated experiment

A finding the user can trust, backed by raw data and a harness anyone can re-run. The deliverable is a **research file**, not code: the harness is evidence, kept on a throwaway branch, and nothing merges into the working branch.

**You are the orchestrator,** in the sense `~/.claude/skills/rc-orchestrate/SKILL.md` defines: you hold the gates, write the briefs, verify every return, and carry the thread. Read that file first. This skill reuses its *Executors* section (checkpoints, new files, session hygiene, fallback), its *Rungs* (step up on a rejected return), *Refresh the page*, *Track status*, and *Writing a brief*, and names only what differs.

## The cast

| Role | Role file | Route |
|---|---|---|
| Orchestrator + designer | — (you) | session model |
| Explorer (optional) | `rc-explorer` | as in rc-orchestrate's cast |
| Experimenter | `rc-experimenter` | always Claude, rung 3 by default: its runs call paid APIs over the network, which codex's sandbox blocks |
| Reviewer | `rc-reviewer` | always Claude (opus · medium) |

## Phase 0 — Ground and design

Read the ticket yourself, in full. Then, as rc-orchestrate's Phase 0 says: **pin the ground** (BASE and branch per repo; the tree must be clean), **find the feature**, and **open the run file** in `<feature>/runs/<slug>.md`. Run the backend check and **explore** only when the harness must call the repo's own code (a prompt builder, a client); spot-check the report as rc-orchestrate says.

**Branch off.** In each repo the harness touches, create and check out `experiment/<slug>` from BASE. The harness lives there; the working branch never sees it.

**Draft the design** into the run file:

- **Claim**: one sentence the experiment confirms or refutes.
- **Arms**: what each runs, and the one variable that differs between them.
- **Metric**: what is measured per call and how it rolls up per arm (cost per task, not per token, when models differ). A quality check next to cost, or a reason none is needed.
- **Inputs**: their source and how many.
- **Sample size**: per arm, and the smoke size (a few calls per arm).
- **Budget cap**: the most the full run may spend, in currency.
- **Stop rule**: when the run stops early (the cap, an error rate, a result already decisive).
- **Price table**: which one, dated.
- **Paths**: the harness folder, and the raw-output folder `<feature>/scratchpad/<slug>/raw/` (without a feature folder, `<run-dir>/raw/`).

Set the ticket `in-progress` and refresh the page.

## Gate A — The design 🚦 (required)

Every field of the design is a decision the user pays for. Invoke `/grilling`, adapted:

- **Root:** the design above. Grill the claim first: a claim that no number could refute is not ready.
- **Exit:** once the user confirms every field, write the answers into the run file, then proceed.

## Phase 1 — Harness and smoke run

Brief `rc-experimenter` in **harness mode**: the design (by path), the harness path, the raw-output path, the smoke size, and the boundary: **build the harness, run the smoke run only, and return before any full run.**

Verify:

- The call's delta touches the harness folder only.
- Re-run the smoke run yourself with the command it reports, writing to `raw/smoke-check/`. Every call has a raw row with every usage field, cost, and the price table.
- The arms' configs differ only in the variable under test (diff them).
- Smoke spend is under the cap, and the projected full-run cost (smoke cost per call × full size) is under the cap. A projection over the cap goes to the user: the design changes, not the harness.

## Phase 2 — Design review

Brief `rc-reviewer` to attack the measurement. The brief gives: the design (by path), the harness diff (`git diff <BASE>` on `experiment/<slug>`), the smoke raw rows, and [`confounds.md`](confounds.md) as a floor, not the scope. It asks one question: **what makes this measurement not measure the claim?** Each finding names the confound, its evidence in the harness or the rows, and a severity: `invalidates` (the result would be wrong), `weakens` (the result needs a caveat), or `note`.

Triage each finding against your own reading:

- **Fix**: an `invalidates` finding, or a `weakens` finding that is cheap to fix. Brief `rc-experimenter` in harness mode with the findings quoted, then verify and re-run the smoke as in Phase 1.
- **Caveat**: a `weakens` finding you accept. It goes into the research file's limitations.
- **Rejected**: with a reason, in the run file.

Cap at **one fix round**. A finding that needs a design change, or a second `invalidates` round, goes to the user and back to Gate A.

**Freeze.** Commit the harness on `experiment/<slug>` and record the commit hash in the run file. The full run uses that commit and nothing else.

## Phase 3 — Full run

Brief `rc-experimenter` in **run mode**: the frozen commit, the full size, the raw-output path, the cap, and the stop rule.

Verify: the call's delta against its checkpoint is empty; every call has a row, failed calls included; spend is at or under the cap; and recompute the per-arm numbers yourself from the raw rows. Your numbers are the result. The experimenter's are a claim.

## Gate B — Accept the results 🚦 (required)

Accepting means the user trusts the finding; nothing merges into the working branch. Draft the research file (below), then show this report:

```
## Experiment — <title>          <confirmed | refuted | inconclusive>
Claim:      <one sentence>
Result:     <per arm: metric, spread, n>
Spend:      <total> of <cap>
Caveats:    <one line each, or "none">
Review:     <n> fixed · <n> caveats · <n> rejected
Harness:    experiment/<slug> @ <short hash>
Research:   <path>

Accept?
```

On change requests: a new analysis of the same raw rows is yours to do, then re-show the report. More data or a new arm changes the design: back to Gate A, and a new run under its own cap.

On acceptance, run *Finish*.

## The research file

`<feature>/scratchpad/<slug>.md`. Without a feature folder, put it where the repo keeps research notes, and say where. It holds:

- **TL;DR**, first, as the layout's *TL;DR* rule says: the verdict with its headline numbers, what it means for the decision the ticket feeds, and the largest caveat.
- **Question and claim**, and the verdict.
- **Design**: arms, metric, inputs, n, price table with its date.
- **Results**: per-arm numbers with their spread, computed from the raw rows.
- **Limitations**: every accepted caveat.
- **Sources**: the harness branch and commit, the run command, and the raw-output path. Every number traces to them.

## Finish

1. **Record it.** Add an `## Experiments` entry to `overview.md` in the layout's format (`~/.claude/skills/rc-feature-page/feature-layout.md`), with `Source:` pointing at the research file. When the ticket is a wayfinder ticket, resolve it as the tracker doc's *Resolve* says: the answer under `## Answer`, then the gist and link in the map. Otherwise resolve it the way the repo's tracker closes work.
2. **Return.** Check out the working branch again in every repo. `experiment/<slug>` stays, unmerged.
3. **Refresh the page.**
4. **Report**: the verdict, the research file path, the harness branch and commit, spend against the cap, and the page URL.
