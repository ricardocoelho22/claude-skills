**0 Important, 1 Nit, 0 Pre-existing.** Nothing in this diff breaks behaviour. The one Nit is a design choice about how search is limited.

**Nit: contact search ignores every word after the second, and nothing tells the caller**
`src/modules/contacts/contacts.repo.ts:51`
```ts
const words: string[] = params.search.trim().split(/\s+/, 2)
```
The `2` limit keeps the first two words and drops the rest. Searching "Maria del Carmen" matches on "Maria" and "del" only, and "Grace Kim Bayview" never checks "Bayview". The results are then wider than what was asked for, and nothing signals it. The agent's `list_contacts` tool feeds into this (`src/modules/agent/tools/contact.tools.ts:17`, through the service). It treats a single match as the intended contact, so a wider set can hand it the wrong person. If the cap exists to bound query cost, a higher limit such as 4–5 would keep it bounded. Otherwise, apply every word.

What I checked and found sound:
- **Contacts seed re-runs.** `deletedAt` is an optional prop with no default (`contact.schema.ts:96-97`), so the `{ deletedAt: { $exists: false } }` lookup finds the live record and the seed doesn't create duplicates. The spec's second-run test covers this.
- **Search filter scoping.** The new `$and` sits alongside the `ownerAccountId` and `deletedAt: null` filters and doesn't replace them, so results stay limited to the owner. Each word goes through `escapeRegExp`, so there's no regex injection. Whitespace-only input is caught by `params.search?.trim()`.
- **Invitation seed re-runs.** `findPendingByJourneyAndProfessional` (`journey-invitations.repo.ts:88-96`) prevents duplicate pending invitations. The sender (ricardo) is also the pro that `journey-participants.seed.ts:33-35` attaches to `home-seller-v1`, so the invitation is consistent with the existing seed data.
- **Microsite seed.** It is skipped when the account already has a microsite. The slug has a sparse unique index (`pro-microsite.schema.ts:146`), and no other seed uses this slug.
- **Seed order in `run-seeds.ts`.** Contacts and microsites run after professional profiles, and invitations after journey participants, so each seeder's dependencies already exist.