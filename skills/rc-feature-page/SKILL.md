---
name: rc-feature-page
description: Build or refresh a feature's page, a claude.ai artifact that shows the feature's architecture, slices, ticket status, and what waits on the user. Use when the user wants a feature page created, refreshed, or shared, or when another skill changes a feature's files and the page must follow.
argument-hint: "create | refresh  [feature folder]"
---

The feature page is a **view**. The feature's files are the source of truth: `overview.md` says what the feature is, the ticket files hold status, and the wayfinder map holds decisions. The page never holds anything the files do not, and nobody edits it. A **refresh** rebuilds it from the files and republishes it to the same URL, so any session can run one at any time.

The page answers three questions for a reader who may be tired: where are we, how is the feature built, and what waits on me. It shows the current state only. It is not a log. History stays in the run files and in git.

Read [`feature-layout.md`](feature-layout.md) first. It defines the tree, the ticket states, the `overview.md` format, and the writing rule this skill follows.

**Single writer.** Only a main session publishes. A sub-agent, a codex executor, or a session in a worktree never publishes; it reports to the main session, which runs the refresh. Two main sessions can still refresh one page at the same time; the one that publishes second gets a refusal, which *Build and publish* step 5 handles.

**Delegated build.** The main session can hand everything except the publish to one sub-agent. The sub-agent runs *Create* steps 1 and 2 (with the review waived) or *Refresh* steps 1 and 2, then *Build and publish* steps 1 to 3 in the build folder it is given. It returns the build folder, the list of files in it, and the waiting lines. The main session then runs *Build and publish* steps 4 and 5 (a rebuild in step 5 is a new delegated build) and the rest of *Create* or *Refresh*: the publish, the `Artifact:` line, and the report.

## Locate the feature

Find the features root (see *Features root* in the layout), then the feature folder: the one the user or the calling skill named, or the only feature with open tickets. When more than one fits, ask.

- `overview.md` with a URL on its `Artifact:` line: run **refresh**.
- No `overview.md`, or an empty `Artifact:` line: run **create**.

## Create

1. **Read the feature.** Read `wayfinder/map.md`, every `specs/<slice>/spec.md`, and the title and status of every ticket. In an older tree, read whatever specs, maps, and tickets the folder holds.
2. **Draft `overview.md`** in the layout's format, following its writing rule. Every claim comes from a file you read: the destination from the map or the spec, the architecture and the slice summaries from the specs, the experiments from resolved wayfinder `prototype` and `research` tickets and from experiment files in `scratchpad/`. When the feature has one spec that covers several slices, propose the slices and say which tickets go in each. Set each `Summary checked` to today.
3. **Review with the user.** Show the draft and change it until the user approves it. The user reviews the overview once, here; later refreshes only read it. Write the approved file. When the calling skill says the review is waived (`rc-orchestrate` does), write the draft as it is and say in your report that `overview.md` is new and unreviewed.

   Done when: `overview.md` is on disk, approved by the user or with the review waived.
4. **Build and publish** (below). On this first publish, pass `icon: "map"`. Write the new URL on the `Artifact:` line of `overview.md`.

## Refresh

1. **Gather** from the files:
   - **Slices**: from `## Slices` in `overview.md`, in that order. A slice's tickets are the files in its `issues/` folder that start with `# NN: <title>`; each ticket's state comes from its `Status:` line, mapped as *Ticket status* in the layout says. A `manual-test-NN-*.md` file is that ticket's manual-checks guide: reference the page links from the ticket, with its checks assumed done, so it adds nothing to the ticket's state or to what waits on the user.
   - **Decisions**: each line under *Decisions so far* in `wayfinder/map.md`: the linked ticket title, the gist cut to its first sentence, and the decision. The decision is one line of at most 15 words that states what was decided, not the topic ("Free tier runs on Haiku, paid on Sonnet", not "Model choice per tier"). Write it from the gist and say nothing the gist does not. None when there is no map.
   - **Experiments**: each entry under `## Experiments` in `overview.md`, in that order.
   - **Related**: the links under `## Related` in `overview.md`. When `delivery-tickets/` holds markdown files, add one more line with no link: "Delivery tickets: N drafts in delivery-tickets/".
2. **Find what waits on the user.** Each finding is one line, in the writing rule's style:
   - a ticket in state `needs-you`, named with its slice;
   - a status word the layout does not list;
   - an open, unblocked, unclaimed wayfinder ticket of type `grilling` or `prototype` (a decision that needs the user);
   - a folder under `specs/` that `overview.md` does not list, or a listed `Folder:` that does not exist while the slice has a summary;
   - a `spec.md` changed after its slice's `Summary checked` date (compare the file's modification date);
   - a slice with a `spec.md` but no summary;
   - a resolved wayfinder `prototype` ticket that no *Experiments* entry names as its source.

   Report drift on the page. Never fix `overview.md` during a refresh: the user, or the skill that changed the plan, updates it.
3. **Build and publish** (below).
4. **Report** the URL and the waiting lines to the user.

Done when: the publish succeeded and every finding from step 2 is on the page.

## Build and publish

Build in `<scratchpad>/rc-feature-page/<feature>/`, starting from an empty folder each time.

1. Copy everything in this skill's `page/` folder into the build folder. In `index.html`, replace the text of `<title>` with the feature name.
2. Copy each manual-checks guide, and each markdown file named under *Experiments* or *Related*, to `src/docs/<id>.md`. Copy each HTML prototype named there to `src/proto/<name>.html`. Copy them as they are; never edit a copied file. An experiment whose source is a folder or a branch gets no copy; the page shows its path.
3. Write `data.json` (schema below).
4. Publish with the `Artifact` tool: `file_path` is the build folder's `index.html`, `root` is the build folder, and `files` lists every other file in it. On a refresh, pass `url` from `overview.md`; when this session has not yet read or published that artifact, read it first (`action: "read"`). The page templates already meet the artifact page contract, so a refresh needs no design pass.
5. **Refused publish.** A refusal on an artifact you already read means another session published the page after your read. It hands you the live version. Read that version's `data.json` (`action: "read"`, `path: "data.json"`) and compare its ticket states with your build's:
   - **Same states:** the other session already published what your refresh exists to show. Skip the publish and say so in the report.
   - **Different states:** the files can have changed since your build read them. Rebuild from step 1, then publish with the same `url`; the refusal counts as the read. A second refusal goes to the user.

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
        { "num": "07", "title": "From the # heading, without the number", "status": "open | in-progress | needs-you | done | deferred | dropped", "checklist": "<doc id> or null" }
      ]
    }
  ],
  "waiting": [ { "text": "One line.", "href": "slice.html#<id> or doc.html#<id> or null" } ],
  "decisions": [ { "title": "Ticket title", "decision": "One line that states what was decided.", "gist": "First sentence of the gist." } ],
  "experiments": [ { "title": "From the ### heading", "result": "From Result:", "summary": "Its sentences, copied as they are", "source": "From Source:", "href": "doc.html#<id> or src/proto/<name>.html or null" } ],
  "links": [ { "title": "From Related", "note": "Its one line", "href": "doc.html#<id> or src/proto/<name>.html or null" } ],
  "docs": { "<id>": { "title": "Page title", "kind": "Manual checks | Experiment | Research | Notes", "src": "src/docs/<id>.md" } },
  "published": ["", "./", "index.html", "slice.html", "doc.html", "<every other published path>"]
}
```

A link inside copied markdown that points at a path not in `published` shows as plain text, so list every published path there. One-line fields (titles, purposes, gists, results, waiting lines) take inline markdown. Raw HTML in any markdown shows as text.
