#!/usr/bin/env python3
"""Status refresh: patch a published feature page's data.json from the ticket files on disk.

Usage: patch-status.py <live-data.json> <feature-folder> <out-dir>

Keeps every id, slice, doc and decision of the live page. Changes only:
  - each ticket's status, read from its file's Status: line;
  - a ticket's checklist, when a manual-test-NN-*.md guide exists and the ticket has none
    (the guide is copied to <out-dir>/src/docs/<id>.md and added to docs and published);
  - builtAt.
Ticket files are looked up in <feature>/specs/<slice-id>/issues/ when that folder exists, else in
<feature>/issues/. Tickets on disk that the page does not show are listed as NEW, and slice folders
with tickets that the page does not show as NEW SLICE: placing either needs a full refresh. A status
line that maps to no known state is listed as UNPARSED and the ticket keeps its live state. Also writes <out-dir>/index.html from the skill's page template. Prints the changes and the
`files` list for the Artifact publish (file_path <out-dir>/index.html, root <out-dir>).
"""
import glob
import json
import os
import re
import shutil
import sys
from datetime import datetime

STATES = {
    'done': ['done', 'resolved', 'closed', 'completed', 'shipped', 'merged'],
    'in-progress': ['in-progress', 'claimed', 'in-review'],
    'needs-you': ['needs-info', 'ready-for-human', 'needs-triage'],
    'open': ['open', 'todo', 'ready-for-agent', 'blocked'],
    'deferred': ['deferred', 'on-hold', 'later'],
    'dropped': ['dropped', 'wontfix', "won't-fix", 'archived', 'cancelled', 'duplicate'],
}
WORD_TO_STATE = {word: state for state, words in STATES.items() for word in words}
STATUS_LINE = re.compile(r'^\**Status:?\**:?\s*\**\s*([A-Za-z_\' -]+)', re.MULTILINE)
TICKET_FILE = re.compile(r'^(\d+)-.+\.md$')


def ticket_state(path):
    """(state, phrase) from the ticket's Status: line; state is None when the phrase maps to no known state.

    Multi-word phrases (`in progress`, `ready for agent`) match as their hyphenated form; the longest
    known prefix wins, so trailing words (`in progress resumed`) are ignored.
    """
    match = STATUS_LINE.search(open(path, encoding='utf-8').read())
    if not match:
        return 'open', ''
    phrase = match.group(1).strip()
    words = re.split(r'[\s_-]+', phrase.lower())
    for end in range(len(words), 0, -1):
        state = WORD_TO_STATE.get('-'.join(words[:end]))
        if state:
            return state, phrase
    return None, phrase


def issues_dir(feature, slice_id):
    nested = os.path.join(feature, 'specs', slice_id, 'issues')
    return nested if os.path.isdir(nested) else os.path.join(feature, 'issues')


def is_ticket(path):
    with open(path, encoding='utf-8') as handle:
        return re.match(r'#\s*\d+:', handle.readline()) is not None


def main(live_path, feature, out_dir):
    data = json.load(open(live_path, encoding='utf-8'))
    os.makedirs(os.path.join(out_dir, 'src', 'docs'), exist_ok=True)
    shown, new_docs = set(), []
    for slice_ in data['slices']:
        folder = issues_dir(feature, slice_['id'])
        for ticket in slice_['tickets']:
            num = ticket['num']
            shown.add((folder, num))
            files = [f for f in glob.glob(os.path.join(folder, f'{num}-*.md')) if is_ticket(f)]
            if not files:
                print(f'MISSING  {num} (no ticket file in {folder})')
                continue
            state, phrase = ticket_state(files[0])
            if state is None:
                print(f'UNPARSED {slice_["id"]}/{num}: "{phrase}" (kept {ticket.get("status")})')
            elif state != ticket.get('status'):
                print(f'STATUS   {slice_["id"]}/{num}: {ticket.get("status")} -> {state}')
                ticket['status'] = state
            guides = glob.glob(os.path.join(folder, f'manual-test-{num}-*.md'))
            if guides and not ticket.get('checklist'):
                doc_id = os.path.basename(guides[0])[:-3]
                title = open(guides[0], encoding='utf-8').readline().lstrip('# ').strip()
                src = f'src/docs/{doc_id}.md'
                shutil.copy(guides[0], os.path.join(out_dir, src))
                data['docs'][doc_id] = {'title': title, 'kind': 'Manual checks', 'src': src}
                ticket['checklist'] = doc_id
                new_docs.append(src)
                print(f'GUIDE    {slice_["id"]}/{num}: {src}')
    for folder in {f for f, _ in shown}:
        for path in sorted(glob.glob(os.path.join(folder, '*.md'))):
            match = TICKET_FILE.match(os.path.basename(path))
            if match and (folder, match.group(1)) not in shown and is_ticket(path):
                print(f'NEW      {os.path.relpath(path, feature)} (not on the page: run a full refresh)')
    page_slices = {slice_['id'] for slice_ in data['slices']}
    for folder in sorted(glob.glob(os.path.join(feature, 'specs', '*', 'issues'))):
        slice_id = os.path.basename(os.path.dirname(folder))
        if slice_id not in page_slices and any(is_ticket(p) for p in glob.glob(os.path.join(folder, '*.md'))):
            print(f'NEW SLICE {slice_id} (not on the page: run a full refresh)')
    template = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'page', 'index.html')
    page = open(template, encoding='utf-8').read()
    page = re.sub(r'<title>.*?</title>', f"<title>{data['feature']}</title>", page, count=1, flags=re.S)
    with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as handle:
        handle.write(page)
    data['builtAt'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    data['published'] = sorted(set(data.get('published', [])) | set(new_docs))
    with open(os.path.join(out_dir, 'data.json'), 'w', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    print('FILES    ' + json.dumps([{'path': p} for p in ['data.json', *new_docs]]))


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
