I found 1 Important issue, 0 Nits and 0 Pre-existing.

**[Important] Contact search silently ignores every word after the second**
`src/modules/contacts/contacts.repo.ts:51`:
```ts
const words: string[] = params.search.trim().split(/\s+/, 2)
```
`split` with a limit of `2` throws away the third word onward, so a narrowed search comes back unfiltered. Before this diff, `"Maria Alvarez Fresno"` found nothing because it was matched as one phrase. Now it returns every Maria Alvarez, even ones whose fields don't contain "Fresno". This one repository method serves both callers: the agent's `list_contacts` tool (`src/modules/agent/tools/contact.tools.ts:17` passes `search` straight through) and the contacts endpoint. Any 3-word query (a full street address, a 3-word company name, name plus city) is affected in the same way.

**How I proved it:** I added a throwaway spec, `src/modules/contacts/zz-review.spec.ts` (since deleted), which creates two Maria Alvarez contacts, one in Oakland and one in Fresno, then searches for `'Maria Alvarez Fresno'`.
```
pnpm test -- src/modules/contacts/zz-review.spec.ts
    total for search: 2 [ 'Oakland', 'Fresno' ]
    Expected: 1
    Received: 2
Tests:       1 failed, 1 total
```
**Required:** the ticket doesn't specify search behaviour. The new test says a search matches when "every word matches some field" (`contacts.service.spec.ts:150`), and by that rule only the Fresno contact qualifies, so the result should be 1. **Fix:** drop the `, 2` limit, or cap the word count explicitly and say so in the tool description.

**What I checked and found sound:**
- **Seed re-runs don't duplicate data.** `deletedAt` has no default (`contact.schema.ts:97`), so the seeder's `$exists: false` check finds existing contacts. The two invitation and microsite seeders already check for existing records before creating. A second seed run logged `created=0` for invitations.
- **Seed order is right.** Contacts and microsites seed after professional profiles; invitations seed after journeys.
- **The changed test files pass.** `run-seeds.spec.ts` and `contacts.service.spec.ts` ran 25 of 25 green on in-memory Mongo.
- **Cross-pro isolation holds.** Nikki doesn't see Maria and Ricardo doesn't see Owen in the seeded contacts, so each eval case's forbidden fact really does belong to another account.

The working tree is back as I found it: `git status` shows only the original changes.