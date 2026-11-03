No findings: 0 Important, 0 Nit, 0 Pre-existing. The diff introduces no defects.

What I checked:
- **Moved code:** I compared the original file (`git show bead2cb:src/modules/agent/agent.service.ts`) with the new code, method by method.
  - These moved over word for word: `isAtRolloverCeiling`, `rollOverAfterPreflight`, `fallBackToPredecessor`, `resolveHead`, `walkChain`, `listRecents`, `getCurrent`, `setCurrent`, `getOwned`, `projectOwnedDetail`, `deleteOwned` and `resolveCallerActor`.
  - `startConversation` and `continueConversation` keep the same order of steps and the same `try/finally` that frees the concurrency slot. Only the targets changed (`this.turn.*`, `this.chain.*`, `this.queries.*`).
- **Helpers pulled out of `agent-turn.service.ts`:** `isAgentDisabledResult`, `toTurnUsage`, `toModelToolPart`, `withPageContextPart`, `toToolInputSchema`, `findToolPart` and `LAST_TOOL_PROVIDER_OPTIONS` all compute what the old inline code computed.
  - One real change: `buildTools` now builds one `AgentExecutionContext` per turn and shares it across every tool's `execute`. Before, each call got a fresh object. That only matters if something changes the context during a call. A search of `src/modules` for assignments to `context.` or `ctx.` outside specs found none, so behavior is the same.
- **Dependency injection:** the services depend on each other in one direction only: chain → turn, queries → chain, conversation → turn, chain and queries. There is no cycle, and all three are registered in `agent.module.ts:64-66`.
- **Callers:**
  - The controller (`agent.controller.ts:92-134`) now sends the five query routes to `queriesService`. Each one is still wrapped in `throwLifecycleError`.
  - The eval driver (`src/evals/agent/driver.ts:6,382`) still gets `AgentConversationService` from the app, which still exports it (`agent.module.ts:70`). The driver doesn't call any of the moved query methods.
- **Runs:**
  - `pnpm typecheck` printed only the `tsc --noEmit` header, with no errors.
  - `pnpm test -- src/modules/agent` printed `Test Suites: 34 passed, 34 total`, `Tests: 293 passed, 293 total`.

Because nothing was found, there was nothing to prove with a failing test.