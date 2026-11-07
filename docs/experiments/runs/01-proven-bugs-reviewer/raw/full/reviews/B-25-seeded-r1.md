**2 Important, 0 Nit, 0 Pre-existing.**

The ticket requires "no behaviour change", but the diff changes two behaviours. Both are proven by a temporary probe spec, `src/modules/agent/zz-review-probe.spec.ts`, which drives the real new services. I deleted it after the run, so the code under review is as I found it.

Command: `pnpm test -- src/modules/agent/zz-review-probe.spec.ts`

**1. Important: the rollover now waits one token longer, at the exact ceiling**
- **Evidence:** `src/modules/agent/agent-conversation-chain.service.ts:40` reads `return replayTokens > maxReplayTokens`. The original at `bead2cb:src/modules/agent/agent.service.ts:326` read `return replayTokens >= maxReplayTokens`.
- **Effect:** when the replay tokens exactly equal `AGENT_ROLLOVER_MAX_REPLAY_TOKENS`, the conversation used to roll over and now replays in full.
- **Run:** the probe sets the ceiling to exactly the conversation's estimated replay tokens.
  - Printed: `✕ rolls over when replay tokens equal the ceiling … Expected: true  Received: false`
  - Required (the original behaviour): `true`
- **Fix:** restore `>=`.

**2. Important: page context with a route but no entities is no longer sent to the model**
- **Evidence:** `src/modules/agent/agent-turn.service.ts`, `withPageContextPart`, reads `if (message.role !== 'user' || !message.metadata?.pageContext?.entities.length)`. The original `toModelMessages` (old line ~828) read `if (message.role !== 'user' || !message.metadata?.pageContext)`.
- **Effect:** `AgentPageContext` carries a `route` (`agent.dto.ts:12-14`), and an empty `entities: []` passes the schema. Before, the model saw `Page context (ids and labels only): {"route":"/dashboard","entities":[]}`. Now the route is silently dropped from the model's input, for new turns and for replayed history.
- **Run:** the probe calls `toModelMessages` on a user message whose page context is `{ route: '/dashboard', entities: [] }`.
  - Printed: `✕ sends page context with route and no entities … Expected substring: "Page context"  Received string: "[{\"role\":\"user\",\"content\":[{\"type\":\"text\",\"text\":\"hi\"}]}]"`
  - Required: the output contains `Page context`, as the original code produced.
- **Fix:** restore the `!message.metadata?.pageContext` check.

These two are the whole class of logic drift between the old and new code. I compared the moved turn engine against the old one line by line, and the rest are pure extractions with the same behaviour: `isAgentDisabledResult`, `toTurnUsage`, `toModelToolPart`, `toToolInputSchema`, `findToolPart`, the hoisted `AgentExecutionContext`, and `LAST_TOOL_PROVIDER_OPTIONS`. The chain, query and entry-point code otherwise matches the original apart from the switch to the injected services. The controller sends every query route to `AgentConversationQueriesService`, the module registers all three new providers, and the spec changes only switch which service is called.