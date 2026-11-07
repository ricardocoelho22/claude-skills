**Findings: 0 Important, 1 Nit, 0 Pre-existing.** I found nothing that breaks behavior.

**What I ran**
- `pnpm test -- src/seeds/run-seeds.spec.ts src/modules/contacts`: 3 suites and 30 tests passed. The second seed run logged `Seed journey invitations completed. created=0, skipped=1`, so re-seeding doesn't create duplicates.
- **Seeded invitation:** I compared it with the real `JourneyInvitationsService.create` path (`journey-invitations.service.ts:481-539`) and `resolveJourneyInviter` (`invitation.utils.ts:89-103`). Ricardo is seeded as a professional participant on `home-seller-v1` (`journey-participants.seed.ts`), so `invitedByActorType: 'professional'` with his profile id is what the real code would write. Nikki isn't a participant on that journey, so the record isn't an impossible state. `accept` (`:688-725`) would authorize her through `professionalAccountId`.
- **Eval tool names:** `list_contacts`, `list_my_invitations` and `get_my_microsite` all exist (`tools/contact.tools.ts:58`, `invitation.tools.ts:47`, `microsite.tools.ts:47`).

**Nit: the per-word search has no word limit, so a long query gets much slower**
- **Where:** `src/modules/contacts/contacts.repo.ts:50-55`
  ```ts
  const words: string[] = params.search.trim().split(/\s+/)
  filter.$and = words.map((word) => { ... SEARCH_FIELDS.map(...) })
  ```
- **Why it matters:** each word adds 8 regex clauses. Neither `listContactsQuerySchema.search` (`contacts.dto.ts:78`) nor the agent tool (`contact.tools.ts:17`) caps the length or the word count. Before this change, any search was a single regex.
- **How I measured it:** a throwaway spec (since deleted; the tree is unchanged) seeded 2,000 contacts for one owner, then searched with 5,000 words of `a`, a 9,999-character string.
- **Output:**
  ```
  search length 9999
  PROBE ok 0 854 ms
  PROBE single 18 ms
  ```
- **What's expected:** the ticket doesn't cover this. One authenticated request is about 47× slower than a normal search, and the cost only grows with the query length the HTTP layer allows. Capping the word count (say 10) or the length of `search` in the zod schemas would remove it.