**2 Important, 0 Nit, 0 Pre-existing.** The ticket says "no behaviour change", but two small logic edits came along with the code that was moved.

**1. Important: the rollover now triggers one token later**
`agent-conversation-chain.service.ts:39`
```ts
return replayTokens > maxReplayTokens
```
The original at `bead2cb:agent.service.ts:326` was `return replayTokens >= maxReplayTokens`. A conversation whose replay estimate lands exactly on `AGENT_ROLLOVER_MAX_REPLAY_TOKENS` used to roll over and now replays in full. The turn-count check on line 34 still uses `>=`, so the two ceilings now disagree about the boundary. None of the specs pin the boundary: they set the limit to 1, 100 or 30_000, far from the estimates. That is why the "existing specs pass" check misses it.
Fix: change it back to `>=`.

**2. Important: page context with no entities is no longer sent to the model**
`agent-turn.service.ts:83` (`withPageContextPart`)
```ts
if (message.role !== 'user' || !message.metadata?.pageContext?.entities.length) {
```
The original at `bead2cb:agent.service.ts:828` was `!message.metadata?.pageContext`. The DTO (`agent.dto.ts:12-15`) requires `route` and accepts an empty `entities` array, since only `.max(20)` applies. So a request like `{ route: '/listings', entities: [] }` used to add a "Page context …" text part carrying the route, and now adds nothing. The model loses the route. This affects replay of messages already stored in Mongo too, not just new turns.
Fix: change the guard back to `!message.metadata?.pageContext`.

**Checked and found equivalent to `bead2cb`:**
- **Turn engine:** `runTurn`, `streamModelTurn`, `meterTurn`, `buildTools`, `applyModelEvent`. The extracted helpers (`isAgentDisabledResult`, `toTurnUsage`, `findToolPart`, `toToolInputSchema`) keep the same logic.
- **Chain:** `walkChain`, `resolveHead`, `rollOverAfterPreflight`, `fallBackToPredecessor`.
- **Queries:** all five methods plus `projectOwnedDetail`.
- **Entry points:** `startConversation` and `continueConversation`. Ownership and actor-type filters are kept on every repository call, so authorization doesn't change.
- **Wiring:** there's no circular injection. Chain depends on Turn, Queries on Chain, and the conversation service on all three. `agent.module.ts` registers all three providers. The controller still sends errors from the queries service through `throwLifecycleError`.