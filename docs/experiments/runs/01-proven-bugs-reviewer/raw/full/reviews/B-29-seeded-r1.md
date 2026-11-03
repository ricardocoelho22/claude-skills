**1 Important, 0 Nit, 0 Pre-existing.** The other changes look sound, and the 30 tests in `run-seeds.spec.ts` and the contacts specs pass.

**[Important] Contact search drops every word after the second, so it returns contacts the user ruled out**

- **Evidence:** `src/modules/contacts/contacts.repo.ts:51`
  ```ts
  const words: string[] = params.search.trim().split(/\s+/, 2)
  ```
  The `, 2` limit discards everything after the second word. The old code matched the whole phrase, so a search for "Mary Ann Jones" found nothing. It now matches every contact who has both "Mary" and "Ann", whatever the last name. Two callers get this: the `list_contacts` agent tool (`src/modules/agent/tools/contact.tools.ts:17`) and the contacts controller. The agent then has to ask a disambiguating question about matches the user's third word had already excluded. Three-word searches are common: full names with a middle or compound part, street addresses ("42 Maple Avenue") and company names ("Bayview Home Lending").
- **Run:** I added a temporary spec, `src/zz-review/search3.spec.ts`, and deleted it afterwards. It seeds contacts "Mary Ann Smith" and "Mary Ann Jones" (firstName "Mary Ann"), then searches "Mary Ann Jones".
  ```
  pnpm test -- src/zz-review/search3.spec.ts
  RESULT 2 [ 'Mary Ann Jones', 'Mary Ann Smith' ]
  Expected: 1
  Received: 2
  ```
- **Required:** Every word of the search must match some field, as stated by the new test's own title at `contacts.service.spec.ts:150` ("matches a multi-word search when every word matches some field"). The result should be 1 contact, Mary Ann Jones.
- **Fix:** Drop the `, 2` limit. If the cap is there to bound query cost, use a higher one, or reject searches over the cap instead of truncating them silently.

I also checked these and found no defect:
- **Invitation seed's journey lookup:** it takes the first journey matching `home-seller-v1` without filtering by consumer. Only one seeded journey uses that key (`journeys.seed.ts:316`, ricardo's), so it picks the right one.
- **Contacts seed idempotency:** the seed's existence check uses `deletedAt: { $exists: false }` while the repo uses `deletedAt: null`. That's safe: the schema has no default for `deletedAt`, and the second-run spec confirms nothing is duplicated.
- **Whitespace-only search:** the new `search?.trim()` guard now skips it, where the old code ran a regex on a single space. That's an improvement.