# Performance decisions

This note records what was measured, what was changed, and what was deliberately
left alone.

## Measurements

Median of 5 runs (3 for the CLI), Apple M5 Pro, Python 3.11, macOS. Results are
in `docs/test_execution_report.pdf` and the performance report.

| Operation | Median |
|-----------|--------|
| Load a 1,000-card deck | 1.1 ms |
| Load a 10,000-card deck | 6.0 ms |
| Load a 100,000-card deck | 56.6 ms |
| Random session, 100,000 cards, all answered | 113.8 ms |
| Adaptive session, 10,000 cards, all missed once | 14.1 ms |
| CLI, 10,000 piped answers | 65.9 ms |
| CLI startup (`--help`) | 39.5 ms |

## Decisions

**1. The queue uses `collections.deque`.** Each quiz mode pops the next card from
the front and, in adaptive mode, adds missed cards to the back. `deque` does both
in constant time, where a list would shift every item on each pop. This is the
one data-structure choice made for speed.

**2. No other optimization was made.** Every operation finishes in well under
120 ms even for 100,000 cards. A quiz is driven by a person typing, so the time
spent waiting for input is far longer than the time spent in the app. Caching,
streaming, or lazy loading would add complexity without a measurable benefit.

**3. Deck size is capped rather than optimized.** A 1 MB file limit and a
500-character limit per field keep memory use bounded. The cap is a safety
decision, not a speed one. Decks larger than the cap should be split.

**4. Network latency is bounded, not tuned.** Generating a deck depends on the
AI service, which is much slower than local work. A 30-second timeout stops a
slow request from hanging the command. Retries were not added. A failed request
gives a clear message, and the user can run the command again.

**5. Startup cost was left as it is.** About 40 ms of the CLI's time is Python
starting and importing modules. Lazy imports could cut that, but the saving is
small and would make the code harder to read.

## What would change these decisions

- Decks with several hundred thousand cards, or a session that keeps answers in
  memory across runs: measure again before changing anything.
- A slower target machine: the figures here are from one fast laptop.
