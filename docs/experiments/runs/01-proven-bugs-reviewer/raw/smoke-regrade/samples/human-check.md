# Human check: label each finding real / false / unsure from the code (blind to arm and to codex's verdict)

## H01  (29 seeded)
- where: `src/seeds/journey-invitations.seed.ts:408`
- tag: Nit
- claim: The sender's consumer profile is looked up but only used to skip the invitation when it is missing. This makes the professional invitation depend on Ricardo also having an unrelated consumer profile.
- quote: 
- your label: 

## H02  (29 seeded)
- where: `src/seeds/journey-invitations.seed.ts:81`
- tag: Nit
- claim: The unused consumer-profile check skips the only invitation with just a warning if Ricardo has no consumer profile, even though the invitation is sent by the professional actor.
- quote: if (!consumerProfile) { ... skipped += 1; continue }
- your label: 
