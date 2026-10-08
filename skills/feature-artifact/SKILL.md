---
name: feature-artifact
description: Build or refresh a feature's page, a claude.ai artifact that shows the feature's architecture, slices, ticket status, and what waits on the user. Use when the user wants a feature page created, refreshed, or shared, or when another skill changes a feature's files and the page must follow.
argument-hint: "create | refresh  [feature folder]"
---

The feature page is a **view**. The feature's files are the source of truth: `overview.md` says what the feature is, the ticket files hold status, and the wayfinder map holds decisions. The page never holds anything the files do not, and nobody edits it. A **refresh** rebuilds it from the files and republishes it to the same URL, so any session can run one at any time.

The page answers three questions for a reader who may be tired: where are we, how is the feature built, and what waits on me. It shows the current state only. It is not a log. History stays in the run files and in git.

Read [`feature-layout.md`](feature-layout.md) first. It defines the tree, the ticket states, the `overview.md` format, and the writing rule this skill follows.

**Single writer.** Only the main session publishes. A sub-agent, a codex executor, or a session in a worktree never publishes; it reports to the main session, which runs the refresh.

## Locate the feature

Find the features root (see *Features root* in the layout), then the feature folder: the one the user or the calling skill named, or the only feature with open tickets. When more than one fits, ask.

- `overview.md` with a URL on its `Artifact:` line: run **refresh**.
- No `overview.md`, or an empty `Artifact:` line: run **create**.

## Create

1. **Read the feature.** Read `wayfinder/map.md`, every `specs/<slice>/spec.md`, and the title and status of every ticket. In an older tree, read whatever specs, maps, and tickets the folder holds.
2. **Draft `overview.md`** in the layout's format, following its writing rule. Every claim comes from a file you read: the destination from the map or the spec, the architecture and the slice summaries from the specs. When the feature has one spec that covers several slices, propose the slices and say which tickets go in each. Set each `Summary checked` to today.
3. **Review with the user.** Show the draft and change it until the user approves it. The user reviews the overview once, here; later refreshes only read it. Write the approved file.

   Done when: the user has approved `overview.md` and it is on disk.
4. **Build and publish** (below). On this first publish, pass `icon: "map"`. Write the new URL on the `Artifact:` line of `overview.md`.

## Refresh

1. **Gather** from the files:
   - **Slices**: from `## Slices` in `overview.md`, in that order. A slice's tickets are the `NN-*.md` files in its `issues/` folder; each ticket's state comes from its `Status:` line, mapped to the four states in the layout. A `manual-test-NN-*.md` file is that ticket's checklist.
   - **Decisions**: each line under *Decisions so far* in `wayfinder/map.md`: the linked ticket title, and the gist cut to its first sentence. None when there is no map.
   - **Related**: the links under `## Related` in `overview.md`.
2. **Find what waits on the user.** Each finding is one line, in the writing rule's style:
   - a ticket in state `needs-info`;
   - an open, unblocked, unclaimed wayfinder ticket of type `grilling` or `prototype` (a decision that needs the user);
   - a folder under `specs/` that `overview.md` does not list, or a listed `Folder:` that does not exist while the slice has a summary;
   - a `spec.md` changed after its slice's `Summary checked` date (compare the file's modification date);
   - a slice with a `spec.md` but no summary.

   Report drift on the page. Never fix `overview.md` during a refresh: the user, or the skill that changed the plan, updates it.
3. **Build and publish** (below).
4. **Report** the URL and the waiting lines to the user.

Done when: the publish succeeded and every finding from step 2 is on the page.

## Build and publish

Build in `<scratchpad>/feature-artifact/<feature>/`, starting from an empty folder each time.

1. Copy everything in this skill's `page/` folder into the build folder. In `index.html`, replace the text of `<title>` with the feature name.
2. Copy each checklist and each *Related* markdown file to `src/docs/<id>.md`, and each *Related* HTML prototype to `src/proto/<name>.html`. Copy them as they are; never edit a copied file.
3. Write `data.json` (schema below).
4. Publish with the `Artifact` tool: `file_path` is the build folder's `index.html`, `root` is the build folder, and `files` lists every other file in it. On a refresh, pass `url` from `overview.md`; when this session has not yet read or published that artifact, read it first (`action: "read"`). The page templates already meet the artifact page contract, so a refresh needs no design pass.

### data.json

```json
{
  "feature": "Feature name",
  "destination": "From ## Destination.",
  "builtAt": "YYYY-MM-DD HH:MM",
  "source": "<features-root>/<feature>",
  "intro": "Markdown from ## About, copied as it is.",
  "architecture": "Markdown from ## Architecture, copied as it is.",
  "slices": [
    {
      "id": "<slice folder name>",
      "title": "From the ### heading",
      "purpose": "From Purpose:",
      "specPath": "specs/<slice>/spec.md, or null when the slice is planned",
      "summary": "Markdown of the slice's summary, copied as it is, or null",
      "tickets": [
        { "num": "07", "title": "From the # heading, without the number", "status": "open | in-progress | needs-info | done", "checklist": "<doc id> or null" }
      ]
    }
  ],
  "waiting": [ { "text": "One line.", "href": "slice.html#<id> or doc.html#<id> or null" } ],
  "decisions": [ { "title": "Ticket title", "gist": "First sentence of the gist." } ],
  "links": [ { "title": "From Related", "note": "Its one line", "href": "doc.html#<id> or src/proto/<name>.html" } ],
  "docs": { "<id>": { "title": "Page title", "kind": "Manual checks | Research | Notes", "src": "src/docs/<id>.md" } },
  "published": ["", "./", "index.html", "slice.html", "doc.html", "<every other published path>"]
}
```

A link inside copied markdown that points at a path not in `published` shows as plain text, so list every published path there.
