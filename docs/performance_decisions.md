# Performance decisions

This note records what was measured, what was tried, what was kept, and what was
rejected, with the evidence for each decision.

## How performance was measured

- **Repeated runs:** each operation runs 5 times (3 for CLI runs). The median,
  minimum, and maximum are reported.
- **Profiling:** `cProfile` on a 100,000-card session and a 100,000-card load,
  to find where the time goes.
- **A/B comparison:** the old and new code are timed in the same process,
  alternating between them, so machine-wide slowdowns affect both equally.

Run-to-run variance on the test machine was large. CLI startup, which the change
did not touch, measured 40 ms in one run and 82 ms in a later run. Absolute
numbers from different runs should not be compared. Decisions here rest on A/B
comparisons, not on comparing two separate benchmark runs.

## What the profile showed

- **Session (100,000 answers):** time is spread across many small Python calls
  per answer: the loop, answer checking, normalization, statistics, feedback,
  and the exit check. No single function dominates.
- **Load (100,000 cards):** time is spread across per-card validation. The
  largest share is the field checks in `_required_text`.

No single hot spot exists, so no single fix will make a large difference.

## Decisions

**1. The queue uses `collections.deque` (kept).** Quiz modes take the next card
from the front and, in adaptive mode, add missed cards to the back. `deque` does
both in constant time, where a list would shift every item on each removal.

**2. Stripping each field once was tried and rejected.** The validation stripped
each text field twice. Changing that to one strip looked faster in separate
benchmark runs (about 20% at 10,000 cards), but the A/B comparison showed no
measurable change: +1.6% at 10,000 cards and −4.1% at 100,000. That difference is
within run-to-run noise. The change was reverted, because it added churn without
benefit.

**3. Caching the normalized expected answer was not implemented.** Each answer
normalizes the expected text again. Caching it would remove about half of the
normalization calls, which is roughly 8% of session time in the profile. The
change would need a cache or an extra field on `Flashcard`, which adds
complexity for that gain. Recorded as a possible future change, not made.

**4. Streaming the deck load was rejected.** Streaming would reduce peak memory,
but the 1 MB file limit already bounds memory. A streaming JSON parser would
also need a new third-party dependency, which the project avoids on purpose. The
benefit does not justify the cost at this file size.

**5. Deck size is capped rather than optimized.** The 1 MB file limit and the
500-character field limit keep memory use bounded. The cap is a safety decision,
not a speed one. Decks larger than the cap should be split.

**6. Network latency is bounded, not tuned.** Generating a deck depends on the AI
service, which is much slower than local work. A 30-second timeout stops a slow
request from hanging the command. Retries were not added. A failed request gives
a clear message, and the user can run the command again.

**7. Startup cost was left as it is.** Startup is mostly Python starting and
importing modules. Lazy imports could reduce it, but the saving is small and
would make the code harder to read.

## Effect of the 1 MB limit on the benchmark

The 1 MB file limit rejects a 100,000-card deck, which is about 5 MB. The earlier
performance report listed that deck as a measured case, so it described something
the app no longer accepts. The benchmark now raises the limit inside the
benchmark process only, so the 100,000-card rows still measure the parser. A
deck that the app accepts holds roughly 20,000 short cards.

## Current results (latest run)

| Operation | Median |
|-----------|--------|
| Load 1,000 cards | 0.7 ms |
| Load 10,000 cards | 4.7 ms |
| Load 100,000 cards (limit lifted for measurement) | 57.4 ms |
| Random session, 10,000 cards | 9.0 ms |
| Random session, 100,000 cards (limit lifted for measurement) | 115.1 ms |
| Adaptive session, 10,000 cards | 13.9 ms |
| CLI, 10,000 piped answers | 112.5 ms |
| CLI startup | 81.6 ms |

## What would change these decisions

- Decks well beyond the current limit, or a session that keeps answers in memory
  across runs: measure again before changing anything.
- A slower target machine: the figures here come from one laptop, on two
  different days.
