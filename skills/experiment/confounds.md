# Confounds in LLM cost experiments

A confound makes the numbers move for a reason other than the variable under test. This list is a floor for the design review, not its scope: each line names the confound, then how to check for it in the harness or the raw rows.

## What gets counted

- **Cache writes vs warm reads.** The first call writes the cache at a premium; later calls read it cheaply. Check the raw rows for cache-write and cache-read tokens per arm, and whether one arm ran warm while the other ran cold.
- **Cache that never hits.** A prefix that changes per call (a timestamp, an id, a shuffled tool list) defeats caching. Check that cache-read tokens are above zero where the design expects a hit.
- **Uncounted tokens.** Thinking tokens, tool-call tokens, and system-prompt tokens all bill. Check that the cost formula reads every usage field the API returns, not only input and output.
- **Retries and backoff.** A retried call bills twice; a rate-limited arm may pay more for the same work. Check that retries are logged, and that the report counts them or justifies leaving them out.
- **Failed calls dropped.** An arm that errors more looks cheaper when its failures leave the dataset. Check that failed calls have rows and appear in the per-arm counts.
- **Price table.** Prices change and differ between batch and on-demand, and by region or tier. Check that the harness names the price table and its date, and that both arms use the same one.

## What gets compared

- **Arms differ beyond the variable.** A different prompt, temperature, max tokens, tool set, or input set across arms. Diff the arm configs; only the variable under test may differ.
- **Tokenizer differences.** The same text is a different token count on different models. Compare cost per task, not cost per token, when the arms use different models.
- **Output length drift.** One model writes longer answers, so the cost gap is a verbosity gap. Check output tokens per arm, and whether the claim is about cost per task or cost per token.
- **Quality held constant.** A cheaper arm that fails the task did not save money. Check that the design measures task success next to cost, or states why it need not.
- **Order effects.** Running arm A then arm B mixes in warm caches, rate limits, and time-of-day load. Check that calls are interleaved or randomized across arms.
- **Inputs not representative.** A handful of short inputs says little about the real distribution. Check the inputs' source and length spread against production traffic.

## What the numbers can carry

- **n too small for the variance.** LLM outputs vary run to run. Check the per-arm spread in the smoke rows, and that the full-run n can separate the arms by more than that spread.
- **Nondeterminism unpinned.** Temperature, seed, and model version change results between runs. Check that the harness records the exact model id and sampling settings for every call.
- **Harness overhead measured.** Latency or token counts that include the harness's own calls (judges, graders, retries of the grader). Check that grader calls are logged apart from the calls under test.
