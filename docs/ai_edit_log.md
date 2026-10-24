# AI Edit Log

**Purpose:** a record of how AI-generated and AI-assisted code was reviewed,
tested, and corrected while building the Flashcard Quizzer.

**How this build was done:** Claude (Anthropic's coding assistant, in a local
terminal session) wrote the code under direction from the project specification
and from quality rules set by the student: functions of at most 7 lines, files
of at most 200 lines, descriptive PEP 8 names, and tests for edge cases and
errors as well as normal use. Each change below was checked by running the
test suite, coverage, flake8, mypy, black, and isort, and by running the CLI
by hand. Where a check failed, the failing output drove the fix.

Entries are listed in the order they happened. "Prompt" is the rule or
instruction the assistant was working to at that point, not a verbatim chat
message, because the build was done in one continuous session.

---

## 2026-10-24 - Loader error handling broke the function-length rule

**Context:** Reading a deck file can fail in several ways: missing file,
directory, bad encoding, permission denied, and bad JSON. The first version of
`_read_text` handled each one in its own `except` branch.

**AI Tool Used:** Claude

**Prompt/Request:** Functions may have at most 7 lines of logic. Each failure
mode must produce a friendly message, not a traceback.

**AI Response:** One function with four `except` clauses and a directory check.
Functionally correct and every test passed, but the body was about 10 lines.

**Changes Made:**
- Split the error translation into `_read_failure`, which picks the message
  from the exception type.
- `_read_text` now catches `(OSError, UnicodeDecodeError)` in one clause.

**Reasoning:** The size rule is part of the quality bar, so passing tests were
not enough. A dedicated helper also makes each message easy to find and test.

**Outcome:** `_read_text` is 6 lines and `_read_failure` is 5. All 26 loader
tests still pass, and the code-size gate (`tests/test_code_limits.py`) passes.

**Lessons Learned:** A size rule has to be enforced by a test, or it erodes
with every edit. The first version was correct but would have failed review.

---

## 2026-10-24 - Adaptive-mode assertion that could pass for the wrong reason

**Context:** The rubric asks for a test showing that adaptive mode repeats
wrong answers.

**AI Tool Used:** Claude

**Prompt/Request:** Write `test_adaptive_mode_behavior`: a wrong answer must be
asked again.

**AI Response:** The first draft ended with
`assert asked.count(DECK[0]) == 2 or asked[-1] == DECK[0]`.

**Changes Made:** Replaced it with an exact expected order,
`assert asked == [DECK[1], DECK[2], DECK[0]]`, and added a
`remaining() == 3` check directly after the wrong answer.

**Reasoning:** An `or` between two loose conditions can pass for the wrong
reason. The exact order fails if the queue logic is wrong in any way.

**Outcome:** The test now pins the full behaviour: the wrong card goes to the
back of the queue and is asked again.

**Lessons Learned:** Assertions need to be exact. A test that would also pass
on broken code does not protect anything.

---

## 2026-10-24 - Integration test script in the wrong order

**Context:** The adaptive integration test feeds scripted answers in order.

**AI Tool Used:** Claude

**Prompt/Request:** A session where the first card is missed, then answered
correctly on its repeat, should report 4 attempts, 3 correct, and 1 incorrect.

**AI Response:** The script was written as `["x", "Application Programming
Interface", "Central Processing Unit", "Domain Name System"]`.

**Changes Made:** Traced the expected question order by hand (the missed card
returns at the back of the queue) and rewrote the script to
`["x", "Central Processing Unit", "Domain Name System",
"Application Programming Interface"]`.

**Reasoning:** The script ran out of answers and raised `StopIteration`. The
fault was in the test, not in the quiz code.

**Outcome:** The test passes with the expected counts.

**Lessons Learned:** Before writing expected results, trace the sequence the
code will actually produce.

---

## 2026-10-24 - Type checking caught an `Any` return and a value-returning lambda

**Context:** The project runs mypy in strict mode.

**AI Tool Used:** Claude

**Prompt/Request:** Keep `python -m mypy .` clean with strict settings.

**AI Response:** Two errors. In `file_handler.py`, `return data["cards"]` returns
`Any` from a function typed `list[Any]`. In `test_cli.py`, the lambda
`lambda prompt: prompts.append(prompt) or "one"` returns the result of a
method that returns `None`.

**Changes Made:**
- Assigned `data["cards"]` to a typed local before returning it.
- Replaced the lambda with a named `recording_ask` helper that records the
  prompt and then returns the answer.

**Reasoning:** Typed locals make the return type explicit. A named function
makes the recording behaviour obvious to a reader.

**Outcome:** mypy reports no issues in 22 source files.

**Lessons Learned:** Strict type checking finds real mistakes in test code too.

---

## 2026-10-24 - Export failure appeared only after the quiz had run

**Context:** I ran the CLI by hand with `--export` pointed at a folder. The
quiz ran through every card, then printed an error and exited with status 1.

**AI Tool Used:** Claude

**Prompt/Request:** A bad export path should fail before the user spends time on
the quiz.

**AI Response:** The first version wrote the report after the quiz, so the
failure came at the end.

**Changes Made:**
- Added `_check_export_target`, which runs before the quiz and rejects an
  existing folder or a missing parent folder.
- Added two tests, one for each case, asserting the quiz never prompts.

**Reasoning:** Late failures waste the user's session. Checking early costs a
few lines.

**Outcome:** Both bad-path cases exit with status 1 before the first question.
The fix made the CLI's `_play` function longer, so I moved the report and
logging steps into helper functions to keep it within the size rule.

**Lessons Learned:** Manual runs find usability problems that unit tests miss.
The test suite passed before the manual run, but the behaviour was still wrong.

---

## 2026-10-24 - Size gate caught two long functions

**Context:** After the observer and export features were added, the
code-size test failed on two functions.

**AI Tool Used:** Claude

**Prompt/Request:** Keep every function body at 7 lines or fewer.

**AI Response:** `build_report` returned a 9-line dictionary literal.
`AnswerLogger.__call__` was 8 lines because of a multi-line logging call.

**Changes Made:**
- `build_report` now builds the header fields and merges in `_totals`.
- The log format string became a module constant, so the call fits in fewer
  lines.

**Reasoning:** A reader should see the whole logic of a function at once. Both
functions were correct, but the rule exists to keep them readable.

**Outcome:** The size gate passes for every application module.

**Lessons Learned:** A rule with a test behind it is easier to keep than a rule
kept in memory.

---

## Limitations I did not verify

- **Ctrl+C:** The graceful stop is tested by injecting `KeyboardInterrupt`
  into the answer function, not by pressing a real key in a terminal. I did not
  test it interactively.
- **Colors on Windows:** Only macOS terminals were checked. The ANSI codes are
  standard, but I did not confirm that every Windows console renders them.
- **Coverage gate:** The configured minimum is 100%. The measured value on
  the final run is recorded in `docs/coverage_summary.txt`.
