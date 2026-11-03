# Human check: label each finding real / false / unsure from the code (blind to arm and to codex's verdict)

## H01  (29 seeded)
- where: `src/seeds/journey-invitations.seed.ts:111`
- tag: Nit
- claim: The seeder only checks for an existing pending invitation and bypasses the create flow's check that the professional is not already a participant. It can create a fresh pending invitation after nikki accepts or declines the original, including an invitation to a journey she has already joined.
- your label: 
