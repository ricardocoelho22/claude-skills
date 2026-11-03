**Findings: 1 Important, 1 Nit, 0 Pre-existing.**

**1. Important: `extractWords` throws a TypeError when a text has no letters, which crashes grading of any failed turn.**

The function is at `src/evals/agent/assertions.ts:162-164`:
```ts
return new Set([...text.match(/\p{L}+/gu)!])
```
`String.match` returns `null` when nothing matches. The old code handled that with `?? []`. The diff swapped it for a `!` assertion, so the spread now throws on `null`. Two callers can hit this:
- The language check calls `detectReplyLanguage(turn.assistantText)` on every turn (line 307). `driver.ts:321` (`failedTurn`) builds turns with `assistantText: ''`, so every timed-out or thrown turn crashes `checkTranscript` instead of being recorded as a `turn_error`.
- Line 329 calls `detectLanguage(turn.user)`, so a user message with only digits or emoji crashes too.

I ran a scratch spec, `src/evals/agent/zz-review.spec.ts` (since deleted), with `pnpm test -- src/evals/agent/zz-review.spec.ts`:
```
✕ failed turn (driver failedTurn shape)
✕ digits-only user message
TypeError: text.match is not a function or its return value is not iterable
  at extractWords (src/evals/agent/assertions.ts:163:27)
```
The correct result is `[turn_error]` for the first case and `[]` for the second, which is what the code before the diff produced. The fix is to put back `?? []`. None of the committed transcripts has an empty `assistantText`, so the re-grade in the ticket was not affected. Live runs with a failed turn will crash.

**2. Nit: a single English stopword switches off all the new Spanish evidence.**

At line 201, `if (english >= 1) return classifyLanguage(english, spanish)` drops the content-word, accent and punctuation evidence as soon as one English stopword appears. The English list also contains words that are common in Spanish, such as `me`.

In the same scratch run, the reply `'**Perfil:** guardado. Me alegra ayudarte.'` with English expected came back `[]` (passed). The ticket wants a short Spanish reply like this to fail with `[language]`.

This is a matter of tuning the heuristic, so I'm not tagging it Important. One option is to remove `me` from the English set; another is to require `english >= 2` before skipping the extra evidence.