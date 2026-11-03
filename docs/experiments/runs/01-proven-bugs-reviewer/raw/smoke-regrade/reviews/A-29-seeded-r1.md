**Findings: 0 Important, 2 Nit, 0 Pre-existing.**

I found no breaking defects. The contacts search rewrite can't produce an empty `$and`: every caller goes through zod with `.trim().min(1)` (`contacts.dto.ts:78`, `agent/tools/contact.tools.ts:17`). The `deletedAt: { $exists: false }` dedup in the contacts seed works because `deletedAt` has no default (`contact.schema.ts:96-97`). `mustInclude` matching ignores case (`assertions.ts:243-244`), so `'ricardo'` matches the sender name. `home-seller-v1` is unique in `journeys.seed.ts:316`. The invitation fills every required schema field and passes the `orgId`-absent filter in `listForProfessional`.

**Nit 1: unused consumer-profile check can drop the invitation without an error.** `src/seeds/journey-invitations.seed.ts:81-86`:
```ts
const consumerProfile = await consumerProfilesService.findByAccountId(senderAccountId)
if (!consumerProfile) { ... skipped += 1; continue }
```
- The invitation is sent by the professional actor (`invitedByActorType: 'professional'`, `invitedByActorId: sender.profileId`).
- `consumerProfile` is never read after this check.
- So if Ricardo has no consumer profile, the only invitation is skipped with just a warning, and the `pending-invitations` eval fails with no clear cause.
- Fix: remove the check, or use the profile to scope the journey lookup (see Nit 2).

**Nit 2: journey lookup ignores the owner and only reads the first 100.** `src/seeds/journey-invitations.seed.ts:88-89`:
```ts
const { items: journeys } = await journeysService.listPaginated({ page: 1, limit: 100 })
const journey = journeys.find((item) => item.templateKey === invitation.journeyTemplateKey)
```
- This searches all journeys platform-wide, unscoped, first page only.
- A fresh DB is fine. But `pnpm seed:local` on a local DB with more than 100 journeys can miss `home-seller-v1` and skip the invitation without an error.
- It can also pick another consumer's journey of that template if a user created one.
- Fix: scope the lookup to the sender's consumer profile, as `journey-participants.seed.ts:66-76` already does.