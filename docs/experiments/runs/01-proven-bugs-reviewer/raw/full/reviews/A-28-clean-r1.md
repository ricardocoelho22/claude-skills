**0 Important, 1 Nit, 0 Pre-existing.**

The main path works. This diff can only add new `es` detections, so a reply that should be Spanish still passes. I checked the run #2 reply and the four proper-noun cases in the spec by hand, and they classify the way the tests expect.

**Nit: Spanish content words count even when they are capitalized, so proper nouns can still flag English replies.**

- **Evidence:** In `src/evals/agent/assertions.ts:205-206`, `countWordMatches(words, SPANISH_CONTENT_WORDS)` runs on `normalizeText(text)`, which lowercases everything. The orthography check guards proper nouns with `LOWERCASE_WORD_START` (`:189`), but this one has no such guard. So any capitalized word in an English reply that is also on the content list counts as Spanish.
- **Example:** `'**Seller:** Venta Realty, El Paso'`
  - English stopwords: 0, so the English short-circuit at `:201` doesn't apply.
  - Spanish: `el` (stopword) plus `venta` (content word) gives 2, so `classifyLanguage(0, 2)` returns `es`.
  - Result: a language failure when English is expected.
- **Other names that could do the same:** `Compra`, `Sitio`, `Cierre`, `Propiedad`, `Fecha` in a street, business or listing name, paired with one Spanish stopword (`el`, `de`, `la`, `del`, `no`; `no` is also common English).
- **Why it matters:** The ticket says English replies with Spanish names or addresses must not be flagged. The new tests only cover names that aren't on the content list (`Calle Ocho`, `El Paso`, `José Peña`).
- **Possible fix:** Only count content words that appear lowercase in the raw text, the same way the orthography check works. The run #2 reply still fails with that change, because its matching words are lowercase there.

Not flagged: I didn't check the ticket's claim that re-grading the 60 committed transcripts changed exactly one attempt.