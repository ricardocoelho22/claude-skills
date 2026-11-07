**0 Important, 1 Nit, 0 Pre-existing.**

I found nothing that breaks behaviour. These all hold up:
- **Contact search:** the rewritten search in `contacts.repo.ts:50-56` only runs when the trimmed search has text, so an empty or whitespace-only search no longer builds a filter. Every regex is escaped, and both callers (`contacts.controller.ts:27`, `contact.tools.ts:66`) still pass the same parameters.
- **Seed ordering and owners:** each seed runs after the data it reads. The invitation's sender, Ricardo, is a professional on the `home-seller-v1` journey (`journey-participants.seed.ts`), so `invitedByActorType: 'professional'` matches what the service's inviter lookup would produce. Nikki is not already a participant on that journey.
- **Eval strings:** `mustInclude` matching is case-insensitive (`assertions.ts:243-247`), so `'ricardo'` matches "Ricardo".
- **Tools read the seeded records:** the microsite and invitation tools look up records by `context.userId`, and the seeds write the user id into those fields.

**Nit: re-running the invitation seed after the invitation is accepted creates a state the service forbids**
- Evidence: `src/seeds/journey-invitations.seed.ts:111-118` checks only for an existing *pending* invitation:
  ```ts
  const existing = await journeyInvitationsRepository.findPendingByJourneyAndProfessional(journeyId, professionalId)
  if (existing) { skipped += 1; continue }
  ```
  The repo query filters on `status: 'pending'` (`journey-invitations.repo.ts:92-95`).
- Problem: suppose that in local dev Nikki accepts or declines the seeded invitation, and then someone runs `pnpm seed:local` again without resetting the database. The seed inserts a new pending invitation. If she had accepted, she is now a journey participant holding a pending invitation to the same journey. The real create path rules this out with `validateNotAlreadyParticipant` (`journey-invitations.service.ts:496-501`). Since the seed writes straight to the repo, it skips that check.
- Fix: make the seed skip when any invitation exists for this journey and professional, whatever its status. Or also skip when Nikki is already a participant, which matches the check the participants seed does with `findByJourneyAndActor`.