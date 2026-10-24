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

## Correction to the entry count

An earlier summary of this project said the log had eight entries. It had six.
This file is the source of truth, and the count is now correct. Entries 7 to 12
below cover the second round of changes: size limits, configuration, AI
generation, and the security fix.

---

## 2026-10-24 - Choosing urllib over a third-party HTTP client

**Context:** AI-assisted generation needs an HTTP POST with a JSON body.

**AI Tool Used:** Claude

**Prompt/Request:** Add an integration with an external API without adding
runtime dependencies that the project does not already need.

**AI Response:** The assistant proposed `requests`, which is the common choice,
and noted that the standard library's `urllib` could do the same job.

**Changes Made:** Used `urllib.request` from the standard library. The project
already has no runtime dependencies, and `pip-audit` would have had to cover one
more package.

**Reasoning:** A small, fixed request does not need a client library. Keeping the
runtime dependency-free also keeps the security scans simpler.

**Outcome:** The generator adds no runtime dependency. Tests replace the network
call with a fake transport, so they run without network access.

**Lessons Learned:** When a suggestion adds a dependency, check whether the
standard library covers the need before accepting it.

---

## 2026-10-24 - The size rule split the generator into two modules

**Context:** The first version of `ai_generator.py` contained the request
building, the reply parsing, and the HTTP transport. It was 204 lines long.

**AI Tool Used:** Claude

**Prompt/Request:** Files may have at most 200 lines, and functions at most 7
lines of logic.

**AI Response:** The file broke the 200-line rule, and two helpers were too long.

**Changes Made:** Moved the HTTP transport, the error type, and the header helper
into `ai_transport.py`. The generator keeps the request and reply logic, and it
imports the transport. The two long helpers were split.

**Reasoning:** The split also matches the design: the transport is the only part
that touches the network, so it is the only part that needs a security review.

**Outcome:** Both files are under 200 lines. The module boundary is now the
network boundary.

**Lessons Learned:** A size rule can improve the design, not only the layout.

---

## 2026-10-24 - Bandit found a real weakness, and the fix was a check, not a suppression

**Context:** Bandit flagged the `urlopen` call (B310). It can open `file:` and
other schemes if the URL is not fixed.

**AI Tool Used:** Claude

**Prompt/Request:** Resolve the bandit finding.

**AI Response:** The simplest response would have been a `# nosec` comment.

**Changes Made:** Added a check that only `https` URLs are accepted, before
`urlopen` is called. Added tests that `http://`, `file://`, and `ftp://` URLs
are refused and that `urlopen` is never reached. Added the `# nosec B310`
comment only after the check, with the reason in the docstring.

**Reasoning:** A suppression hides the warning. The check removes the cause, and
a test proves it.

**Outcome:** Bandit reports no issues in the app code. The tests fail if the
check is removed.

**Lessons Learned:** When a scanner flags real behaviour, fix the behaviour first
and suppress only what remains.

---

## 2026-10-24 - A test helper broke an assertion it did not need to change

**Context:** A configuration test checked the prompt text. To fix a `lambda`
that mypy rejected, I replaced it with a helper that answered "yes" but did not
record the prompt.

**AI Tool Used:** Claude

**Prompt/Request:** Fix the mypy error in the test without changing what it
checks.

**AI Response:** My own edit. The replacement removed the recording, so the test
could not read the prompt.

**Changes Made:** Restored a local function that records each prompt and then
answers "yes". Removed the helper that had no remaining use.

**Reasoning:** The fix changed the test's behaviour, not only its typing. Running
the suite caught it straight away.

**Outcome:** The test passes and checks the prompt again.

**Lessons Learned:** Fixing a type error can change behaviour. Run the tests
after every edit, not only at the end.

---

## 2026-10-24 - JSON for the config file, not TOML

**Context:** A configuration file is needed. TOML is a common choice.

**AI Tool Used:** Claude

**Prompt/Request:** Add a config file that works with the project's Python
version.

**AI Response:** TOML support in the standard library (`tomllib`) arrived in Python
3.11. The project targets 3.10.

**Changes Made:** The config file is JSON, read with the standard `json` module.

**Reasoning:** Using `tomllib` would have broken the project on Python 3.10.
JSON needs no new code and works on every supported version.

**Outcome:** The config file works on 3.10 and later, and the tests cover
precedence, errors, and unknown keys.

**Lessons Learned:** Check the minimum supported version before choosing a
library feature, not after.

---

## 2026-10-24 - A requirements line was silently broken by my own edit

**Context:** A pin was appended to `requirements.txt` with a shell heredoc.

**AI Tool Used:** Claude

**Prompt/Request:** Pin `filelock` to a patched version.

**AI Response:** The file had no trailing newline, so the new line was joined to
the `pydantic` line, which turned `pydantic` into a comment. The pin was ignored.

**Changes Made:** Found in a dry-run install, where the old `filelock` still
resolved. Rewrote the file with each requirement on its own line, and checked
the result with a fresh install and `pip-audit`.

**Reasoning:** The dry run showed the pin had no effect. Checking the file
directly showed why.

**Outcome:** Every requirement is on its own line, the fresh install succeeds,
and `pip-audit` reports no advisories.

**Lessons Learned:** Verify a change by its effect, not only by the command
exiting with status 0.

---

## Limitations I did not verify

- **Ctrl+C:** The graceful stop is tested by injecting `KeyboardInterrupt`
  into the answer function. A real interrupt has also been sent to a running
  process, through a pseudo-terminal, in the scripted manual checks.
- **Colors on Windows:** Only macOS terminals were checked. The ANSI codes are
  standard, but I did not confirm that every Windows console renders them.
- **AI generation:** Tests use a fake transport. The real service was not called
  during development, so the reply format is checked against the documented
  Messages API shape, not against live output.
- **Coverage gate:** The configured minimum is 100%. The measured value on
  the final run is recorded in `docs/coverage_summary.txt`.
