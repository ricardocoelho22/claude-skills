**Findings: 1 Important, 1 Nit.**

I ran a re-grade script against the code at bead2cb and the new code. It covered all 60 committed attempts (the `smoke/paid` results directory doesn't exist). Only one result changed, `full/paid/english-overrides-spanish-locale #2: [] -> ["language"]`, which is what the ticket says. `pnpm test -- src/evals` passes (100/100).

**Important: capitalized proper nouns count as Spanish content words, so English replies that mention a Spanish address fail.**
- **Evidence:** at `assertions.ts:197-205`, `detectReplyLanguage` runs `countWordMatches(words, SPANISH_CONTENT_WORDS)` on `extractWords(normalizeText(text))`. That text has already been lowercased, so "Sitio", "Venta", "Compra", "Fecha" and "Proceso" in a street or place name count as Spanish. The orthography counter skips capitalized words through `LOWERCASE_WORD_START`, but the content-word counter has no such guard. One stopword such as `del`/`de`/`la`/`el` plus one capitalized content word reaches the threshold of 2.
- **Command:** a temporary jest probe (since deleted) called `checkTranscript` with `profileLanguage: 'en'` on `'Listing: Paseo del Sitio, Bogotá'`.
- **Output:** `"Listing: Paseo del Sitio, Bogotá" old [] new ["language"]`
- **Ticket requires:** `[]`, because English replies that contain Spanish names or addresses must still pass.
- **Fix direction:** match content words against the raw words, only when they start lowercase (the same guard the orthography counter uses).

**Nit: English loanwords with accents count as Spanish orthography.**
- **Evidence:** at `assertions.ts:105`, `SPANISH_ACCENTS = /[áéíóúñ]/u`. The é also appears in common English loanwords (café, décor, résumé, fiancé).
- **Probe output:** `"Saved. Notes: café, décor." old [] new ["language"]`. Two lowercase accented loanwords and fewer than two English stopwords are enough to classify a reply as Spanish.
- **Why only a Nit:** the reply is contrived, and none of the committed transcripts trigger it (the re-grade above showed no other changes). A short allowlist of loanwords, or counting only ñ, á, í, ó, ú and Spanish punctuation, would close it.

I removed the scratch files. The working tree is back to the diff under review.