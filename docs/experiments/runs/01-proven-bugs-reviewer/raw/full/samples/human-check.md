# Human check: label each finding real / false / unsure from the code (blind to arm and to codex's verdict)

## H01  (15 clean)
- where: `journey.tools.ts:170`
- tag: Nit
- claim: The preview generates new step IDs, but approval plans again and generates different IDs. Links or keys using an added step's preview stepId will point at a step that never exists in the journey.
- quote: id: options.generateStepId!()
- your label: 

## H02  (31 clean)
- where: `agent-model-client.service.ts:138`
- tag: Important
- claim: The backend marks a cut-off turn as truncated but does not provide the requested en/es message. An empty cut-off turn remains silent unless the frontend displays a message from the flag.
- quote: truncated
- your label: 

## H03  (28 clean)
- where: `src/evals/agent/assertions.ts:205`
- tag: Nit
- claim: Spanish content words count even when capitalized because the text is lowercased and the content-word check has no proper-noun guard. English replies containing Spanish names or addresses can therefore be classified as Spanish and fail when English is expected.
- quote: countWordMatches(words, SPANISH_CONTENT_WORDS)
- your label: 

## H04  (31 clean)
- where: `agent-turn.service.ts:261`
- tag: Nit
- claim: The backend adds a truncated flag but no visible English or Spanish message for a cut-off turn. Unless the frontend reads that flag and displays a message, the turn remains silent.
- quote: truncated
- your label: 

## H05  (31 clean)
- where: `agent-model-client.truncation.spec.ts:47`
- tag: Important
- claim: The spec omits the tool-call part that the real provider sends for a cut-off tool call, so it covers a stream shape production cannot reach. With the real stream shape, raw JSON parser text reaches the pro as a tool error and is stored for the model to read on the next turn.
- quote: status: 'error'
- your label: 

## H06  (28 clean)
- where: `assertions.ts:105`
- tag: Nit
- claim: English loanwords with accents count as Spanish orthography. Two lowercase accented loanwords and fewer than two English stopwords are enough to classify a reply as Spanish.
- quote: SPANISH_ACCENTS = /[áéíóúñ]/u
- your label: 

## H07  (15 clean)
- where: `src/modules/journeys/journeys.service.ts:None`
- tag: Important
- claim: A batch that completes several steps emits one journey.step_updated event per changed step against the same final journey state, causing completion milestones to fire once per completed step instead of once per batch. Completing the last three steps therefore sends three journey-completed milestone events and three celebrations or notifications.
- quote: await this.eventEmitter.emitAsync('journey.step_updated', ...)
- your label: 

## H08  (29 clean)
- where: `src/seeds/journey-invitations.seed.ts:111`
- tag: Nit
- claim: The invitation seed checks only for an existing pending invitation, so it can create another pending invitation after the original is accepted or declined. After acceptance, this leaves a journey participant holding a pending invitation to the same journey, a state the service forbids.
- quote: status: 'pending'
- your label: 

## H09  (30 clean)
- where: `src/modules/agent/agent.types.ts:273`
- tag: Nit
- claim: AgentInvalidOperationDetail omits the new precedentId field, so the type does not describe the model's main hint for these three codes. The field passes through at runtime, but later code that builds details from this type will silently drop it.
- quote: op
- your label: 

## H10  (15 clean)
- where: `accepted-offer.listener.ts:178`
- tag: Pre-existing
- claim: The agent can add or move ad-hoc steps into the closing section, causing later offer acceptance to skip generating closing steps. Separately, backToMarket deletes every step in that section, including steps the user moved there.
- quote: type: 'ad_hoc'
- your label: 

## H11  (32 clean)
- where: `cases/journey-write.ts:84`
- tag: Nit
- claim: The expectation does not check that the agent asked a question. A reply that calls get_journey and makes no proposal passes even if it incorrectly refuses removal or merely describes the section.
- quote: expect: { toolsCalled: ['get_journey'], noProposal: true }
- your label: 

## H12  (30 clean)
- where: `journey-edits.planner.ts:None`
- tag: Nit
- claim: Precedents are checked only at that operation's position and are not re-checked after a later step deletion, so the card can show a precedent the same batch deletes. After approval the listener strips the deleted precedent, leaving the database correct but the preview misleading.
- quote: plan.steps
- your label: 

## H13  (28 clean)
- where: `assertions.ts:197`
- tag: Important
- claim: Capitalized proper nouns count as Spanish content words because the text is lowercased before content-word matching, without a capitalization guard. One Spanish stopword plus one capitalized content word reaches the threshold, causing English replies containing Spanish names or addresses to fail.
- quote: countWordMatches(words, SPANISH_CONTENT_WORDS)
- your label: 

## H14  (32 clean)
- where: `assertions.ts:251`
- tag: Nit
- claim: When a proposal is expected but missing, the maxReplyWords check falls back to the full assistantText rather than the text after the card. This adds a misleading second reply_words failure that grades a different text.
- quote: turn.textAfterProposal ?? turn.assistantText
- your label: 

## H15  (29 clean)
- where: `src/modules/contacts/contacts.repo.ts:50`
- tag: Nit
- claim: The per-word search has no word limit, and each word adds 8 regex clauses. Neither the query schema nor the agent tool caps the search length or word count, so long queries get much slower as query length grows.
- quote: const words: string[] = params.search.trim().split(/\s+/)
- your label: 

## H16  (31 clean)
- where: `agent.types.ts:478`
- tag: Nit
- claim: The SSE contract comment still describes done as carrying only turnId and usage, although it can now also carry truncated.
- quote: done `{ turnId, usage }`
- your label: 

## H17  (16 clean)
- where: `timeline-batch-notification.listener.ts:20`
- tag: Nit
- claim: Every approved batch now sends a homeowner notification without checking what changed. Batches that only rename, reorder, reschedule or change step statuses now notify, whereas previously only batches that added or removed steps did.
- quote: replaceTimeline
- your label: 

## H18  (15 seeded)
- where: `journeys.service.ts:672`
- tag: Nit
- claim: Proposal and application each generate new step ids, so stepId values in add_step and add_section previews never match the ids stored. This causes trouble if the frontend or a later turn refers to those preview ids.
- quote: new Types.ObjectId()
- your label: 
