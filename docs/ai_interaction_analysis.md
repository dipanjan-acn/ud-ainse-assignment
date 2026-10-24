# AI interaction analysis

This analysis covers how an AI coding assistant (Claude) was used to build the
Flashcard Quizzer, where it helped, where it failed, and where human judgment
was needed. The evidence comes from the edit log
([`ai_edit_log.md`](ai_edit_log.md)), the quality-gate results, and the
corrections made during the work. The counts are approximate, since the work ran
across many sessions and not every intermediate attempt was recorded.

## How the assistant was used

- **Design and scaffolding:** module layout, the three patterns (Strategy,
  Factory, Observer), and the first implementation of each module.
- **Tests:** written before each implementation, then run to see them fail.
- **Quality checks:** running flake8, mypy, black, isort, coverage, bandit, and
  pip-audit, then fixing what they reported.
- **Documentation:** the README, the edit log, the reports, and this analysis.

## Where the assistant was strong

**Known patterns and conventional structure.** The Strategy, Factory, and
Observer patterns were implemented correctly on the first attempt, with clear
names and docstrings. Standard tasks like argument parsing, JSON validation, and
ANSI color codes needed little correction.

**Breadth of error handling.** First drafts already covered missing files,
bad encodings, HTTP errors, timeouts, and malformed replies, with messages that
name the problem. The edge cases were usually the right ones.

**Test ideas.** It proposed the edge cases to test (zero and negative amounts,
bool masquerading as an integer, a card with only whitespace) and most of the
fakes needed to test the network code without a network.

**Fast iteration on feedback.** When a gate failed, the fix was usually correct
on the first try, such as splitting a function or moving a constant.

## Where the assistant was weak

**Quality rules were not met by default.** Across the build, the first drafts
broke the 7-line function rule or the 200-line file rule more than a dozen times,
and mypy strict reported type errors several times. None of this was hidden by
passing tests. The rules only held because a test enforced them. Without
`tests/test_code_limits.py`, these would have shipped.

**Assertions that were too loose.** One adaptive-mode test accepted two outcomes
joined by `or`, which could pass for the wrong reason. The exact order is now
asserted. One integration script fed answers in the wrong order. The assistant
wrote it, and I traced the expected order by hand to fix it.

**Convenience over fit.** It suggested `requests`, which would have added a
dependency for a small need. It also suggested `tomllib` for configuration, which
needs Python 3.11 when the project supports 3.10. Both suggestions were correct in
general, and both were wrong for this project. Checking the project's constraints
caught them.

**Edits that changed behaviour without notice.** A type fix replaced a lambda
with a helper that no longer recorded prompts, which broke a test. Another
edit joined a requirements line onto the line before it, which silently removed a
dependency. A dry-run install caught it. Both were my own edits, and both would
have been hard to spot in review.

**Its own reporting was not reliable.** A summary said the edit log had eight
entries. It had six. The count came from memory, not from the file. Claims about
results now come from running a command, not from recall.

**Shell and environment assumptions.** Several commands assumed GNU tools (for
example, `timeout`, which macOS does not provide), or used zsh globbing in a way
that did not expand. Each failure was visible in the output, and each was fixed,
but they cost time.

## Where human judgment was required

- **Scope and acceptance:** deciding that the status list was seven values, that
  the repo should be public, and that 100% branch coverage was the bar. The
  assistant could propose these, but it could not decide them.
- **Security posture:** the decision to drop `safety`, which needed an account,
  and to fix the bandit B310 finding with a check rather than a suppression.
- **Visual review:** the assistant cannot look at a PDF without help. Screenshots
  of the rendered pages were used to check diagrams and colors, and a human
  reviewed the final reports.
- **Deciding when a fix was complete.** A passing test was not enough on its own.
  The manual checks and the real Ctrl+C test found a usability problem the unit
  tests had missed.

## What worked in prompting

- Stating numeric limits (7 lines, 200 lines, 100% coverage). These became tests,
  so they could not drift.
- Asking for tests before implementation, and for the test run to show the
  failure first.
- Asking for an exact output contract, such as the precise error-message text
  that tests should match.
- Requiring the gates to pass after every change, not only at the end.

## What did not work

- Vague requests such as "make it stand out". These produced generic features. A
  checklist with a rating for each item, and a specific gap for each one, gave a
  useful answer.
- Accepting a suggestion without checking it against the project's stated
  constraints, such as the minimum Python version or the dependency policy.

## Recommendations for future collaboration

1. Put the project's constraints in the first prompt: minimum Python version,
   dependency policy, size limits, and the required gates.
2. Make every rule a test. A rule that is only remembered will be broken.
3. Verify any count, result, or claim by running a command. Do not trust recall.
4. After every edit, run the tests. Fixing a type error or a formatting problem
   can change behaviour.
5. Check any new dependency against the standard library first.
6. Keep a human decision record for scope, security, and acceptance, separate from
   the code.
