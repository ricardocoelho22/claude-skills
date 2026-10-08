# Feature layout

Where a feature's planning and tracking files live. `feature-artifact` reads this tree to build the feature page, and `orchestrate` writes its run files into it. Third-party skills (`wayfinder`, `to-spec`, `to-tickets`) reach it through each repo's tracker doc (see *Tracker doc*).

## Features root

The features root is a folder in the workspace folder, above the repos, never inside a repo. A feature can span several repos, and these files are notes for developers, not product code.

The workspace `CLAUDE.md` names it with one line:

```
Features root: <path>
```

Without that line, look for a `features/` folder next to the repo root. When neither exists, ask the user.

The root is untracked by default. To keep history, the user can make it a private git repo of its own.

## The tree

```
<features-root>/
  <feature>/
    overview.md          the feature in one file: destination, intro, architecture, slices, links
    wayfinder/
      map.md             the wayfinder map
      issues/NN-<slug>.md   decision tickets
    specs/
      <slice>/
        spec.md
        issues/
          NN-<slug>.md               implementation tickets
          manual-test-NN-<slug>.md   manual checklists
    runs/                orchestrate run files
    scratchpad/          experiments, assets, prototypes
    archive/             old material kept for reference
```

- A **slice** is a vertical slice of the feature: a piece that delivers something on its own, such as "users CRUD" or "connect the page to the API". Each slice has its own spec and tickets. (`orchestrate` splits one ticket into test-first **cycles**; a cycle is not a slice.)
- Every slice has a folder under `specs/`, also when the feature has only one slice. The tree has one shape, so no skill has to guess.
- Ticket numbers are unique across the feature. A new ticket takes the next number after the highest one in any slice.
- A ticket file starts with `# NN: <title>` and has a `Status:` line (bold markers allowed) and a `Blocked by:` line.
- `scratchpad/` and `archive/` are not part of the feature page. A file there appears on the page only when `overview.md` links it under *Related*.

## Ticket status

The repo's `triage-labels.md` gives the status strings. The feature page uses four states:

| State | Status strings |
|---|---|
| `done` | done, resolved, closed |
| `in-progress` | in-progress, claimed |
| `needs-info` | needs-info |
| `open` | any other string, or no `Status:` line |

## overview.md

The one file that says what the feature is. People and skills write it; `feature-artifact refresh` only reads it.

```markdown
Artifact: <the feature page URL; empty until the first publish>

# <Feature name>

## Destination

<One or two lines: what is true when the feature is done.>

## About

<One or two short paragraphs for a reader who knows the product but not this feature.>

## Architecture

<A few sentences on the main parts and how they connect. Optional: one mermaid `flowchart TD` of up to about 10 nodes.>

## Slices

### <Slice title>

Folder: specs/<slice>/
Purpose: <one line>
Summary checked: <YYYY-MM-DD>

**What it does.** <Two or three sentences on what the user gets.>

**How it works.**
- <three to five bullets, one for each main part>

**Key choices.**
- <up to three choices> *Reason: <why>*

### <next slice> ...

## Related

- [<title>](<path relative to the feature folder>) — <one line>
```

- The slices are in build order.
- A slice without a folder is **planned**. It has a title and a purpose, and no summary yet.
- `Summary checked` is the date someone last compared the summary with `spec.md`. When the spec changes, update the summary and the date.

## Writing

Write all text in `overview.md`, and any other text a skill writes for the feature page, in ASD-STE100 Simplified Technical English: short sentences, one instruction or fact per sentence, active voice, and common words. Use the terms from the repo's `GLOSSARY.md` (follow `GLOSSARY-MAP.md` when a repo has more than one). Give a little context before the detail. A tired reader must understand each line on the first read.

## Tracker doc

Each repo that uses this layout has a `docs/agents/issue-tracker.md` like this one. It steers every skill that publishes to the issue tracker into the feature tree.

```markdown
# Issue tracker: Local Markdown

Issues and specs live as markdown files in the features root, outside this repo. The layout is in `~/.claude/skills/feature-artifact/feature-layout.md`.

## Conventions

- Features root: `<path>`. One feature per folder: `<features-root>/<feature>/`.
- A spec is `<feature>/specs/<slice>/spec.md`. A slice is a vertical slice of the feature; when the user has not named one, ask which slice the spec is for.
- Implementation tickets are one file each at `<feature>/specs/<slice>/issues/NN-<slug>.md`. Numbers are unique across the feature: take the next number after the highest one in any slice.
- Triage state is a `Status:` line near the top of each ticket (see `triage-labels.md`).
- Comments append to the bottom of the file under a `## Comments` heading.

## When a skill says "publish to the issue tracker"

Create the file in the folders above, creating folders as needed.

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user normally passes the path or the ticket number.

## Wayfinding operations

Used by `/wayfinder`. The map is a file with one child file per ticket.

- **Map**: `<feature>/wayfinder/map.md`.
- **Child ticket**: `<feature>/wayfinder/issues/NN-<slug>.md`, numbered from `01`. A `Type:` line records the ticket type (`research`/`prototype`/`grilling`/`task`); a `Status:` line records `claimed`/`resolved`.
- **Blocking**: a `Blocked by: NN, NN` line near the top. A ticket is unblocked when every ticket it lists is `resolved`.
- **Frontier**: the open, unblocked, unclaimed files in `wayfinder/issues/`; the lowest number wins.
- **Claim**: set `Status: claimed` and save before any work.
- **Resolve**: append the answer under an `## Answer` heading, set `Status: resolved`, then append a gist and link to the map's Decisions so far.
```
