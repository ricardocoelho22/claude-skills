# Human check: label each finding real / false / unsure from the code (blind to arm and to codex's verdict)

## H01  (29 seeded)
- where: `src/seeds/journey-invitations.seed.ts:408`
- tag: Nit
- claim: The sender's consumer profile is looked up but only used to skip the invitation when missing. This makes the professional invitation depend on Ricardo also having an unrelated consumer profile.
- your label: 

## H02  (29 seeded)
- where: `src/seeds/journey-invitations.seed.ts:415`
- tag: Nit
- claim: The journey is picked by template key from only the first page of 100 journeys. If another home-seller-v1 journey is seeded or the list exceeds 100 journeys, the invitation will silently go to the wrong journey or be skipped.
- your label: 

## H03  (29 seeded)
- where: `src/seeds/journey-invitations.seed.ts:81`
- tag: Nit
- claim: An unused consumer-profile check skips the invitation with only a warning if Ricardo has no consumer profile, even though the invitation is sent by the professional actor. This causes the pending-invitations eval to fail with no clear cause.
- your label: 
