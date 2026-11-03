The empty-reply crash below is confirmed by reading the code; I didn't run anything.

**Findings: 1 Important, 1 Nit.**

**1. Important: the language check crashes when a turn's text has no letters.**
`src/evals/agent/assertions.ts:162-164`:
```ts
function extractWords(text: string): Set<string> {
  return new Set([...text.match(/\p{L}+/gu)!])
}
```
The old code had `?? []`. The diff swapped it for a `!` assertion. When the text has no letters, `match` returns `null`, and `[...null]` throws a `TypeError`. Two paths reach it:
- **Failed turns:** `src/evals/agent/driver.ts:321` (`failedTurn`) returns `assistantText: ''` for timeouts and thrown errors. `checkGlobalRules` (`assertions.ts:307`) then calls `detectReplyLanguage('')`, which throws. Grading crashes instead of reporting `turn_error`, so the failure the harness exists to report becomes an exception.
- **Letterless user messages:** `checkTranscript` (`assertions.ts:329`) calls `detectLanguage(turn.user)`, which uses the same `extractWords`. A user turn like `"123"` or `"?"` crashes it. That path used to be safe.

The `turn_error` specs (`assertions.spec.ts:313`, `:561`) don't catch this because the `turn()` fixture defaults to non-empty text (`spec.ts:15`).

Fix: put back `?? []` and add a spec with an empty `assistantText` plus an `error`.

**2. Nit: any single English stopword turns off all the new Spanish evidence.**
`assertions.ts:201`: `if (english >= 1) return classifyLanguage(english, spanish)`. The English list includes `me`, `in` and `a`-free short words, and `me` is also a common Spanish pronoun. So a short Spanish reply like `"Perfil guardado. Me encargo del resto."` gives en=1 and es=1 (`del`), so the result is `undefined` and the reply passes. The content words and accents never get counted.

This is no worse than before the diff. But it leaves part of the ticket's goal (catching short Spanish replies) unmet for any reply that contains a word spelled the same in both languages. Removing `me` from the English stopwords, or only applying the gate when the English count is 2 or more, would close it. The second option needs a re-check against the "Rio de Janeiro" / "El Paso" tests.

Nothing else turned up: the switch to `detectReplyLanguage` touches only the reply check, and user-turn detection behaves the same apart from the crash in finding 1.