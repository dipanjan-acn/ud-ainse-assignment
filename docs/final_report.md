# AI-Assisted Development Project Report

**Project Title:** Flashcard Quizzer
**Repository:** https://github.com/dipanjan-acn/ud-ainse-assignment
**Date:** 2026-10-24

## Executive Summary

The Flashcard Quizzer is a command-line app that loads flashcards from a JSON
deck and quizzes the user in one of three modes: sequential, random, or adaptive.
Adaptive mode asks again any card answered wrongly, until it is answered
correctly. The app also prints a session summary, colors each answer green or
red, exports a JSON report, and logs each answer to a file. It exits cleanly on
`exit`, Ctrl+C, or end of input.

I built it with Claude, an AI coding assistant, in a local terminal. I wrote the
specification and the quality rules. The assistant wrote the code, and I checked
each change with the tests, coverage, linters, and by running the CLI by hand.
Several first drafts were correct but broke a rule I had set, or contained a test
that could pass for the wrong reason. These are documented in `ai_edit_log.md`.

The final result has 133 test cases, 100% branch coverage of the application code,
zero flake8 errors, and a clean strict mypy run.

## Project Overview

### Problem Statement

Flashcard revision works best when the user is quizzed on the cards they find
hard. A fixed order does not do that. The app needed to load a deck from a file,
offer several quiz orders, and fail clearly when a deck is bad.

### Solution Approach

The code is split by responsibility:

- `utils/` reads and validates decks.
- `quiz_modes.py` holds the ordering strategies.
- `quiz_engine.py` holds the session, the statistics, and the mode factory.
- `quiz_runner.py` runs the question loop.
- `observers.py`, `export.py`, and `display.py` handle the log file, the JSON
  report, and terminal output.
- `cli.py` parses arguments and wires the parts together.

The code targets Python 3.10 or later, and the runtime uses only the standard
library. The development tools are pytest, coverage, black, isort, flake8, and mypy.

### Final Features

- Decks in array or object format, with one-line error messages
- Sequential, random, and adaptive quiz modes
- A factory that selects a mode by name
- Green and red feedback, with `--no-color` and `NO_COLOR` support
- Session summary with accuracy and most missed cards (`--stats`)
- JSON export (`--export`), checked before the quiz starts
- Per-answer log file (`--log-file`), implemented as an observer
- Graceful stop on `exit`, Ctrl+C, or end of input

## AI Collaboration Experience

### AI Tools Used

- [x] Claude (Anthropic's coding assistant, used through a terminal session)
- [ ] GitHub Copilot, [ ] ChatGPT, [ ] Other

### Collaboration Workflow

1. **Structure the request.** Each request stated the behaviour, the limits
   (7 lines per function body, 200 lines per file), and the tests expected.
2. **Write tests first.** Each test file was run before its module existed, to
   confirm it failed.
3. **Implement the minimum** to make those tests pass.
4. **Run every gate:** pytest, coverage at 100%, flake8, strict mypy, black,
   isort, and a size test that enforces the 7-line and 200-line rules.
5. **Check by hand.** I ran the CLI with good decks, bad decks, bad paths, and
   piped answers, and read the output.

### Most Valuable AI Interactions

#### Example 1: Splitting a function that broke the size rule

**Context:** Reading a deck can fail several ways, each with its own message.
**AI Prompt:** Handle each failure with a friendly message, in 7 lines or fewer.
**AI Response:** One function with four `except` branches. Correct, but about
10 lines long.
**Your Changes:** Moved message selection into `_read_failure`.
**Outcome:** Both functions are within the limit, and all loader tests pass.

#### Example 2: Catching a test that could pass for the wrong reason

**Context:** The rubric requires a test that adaptive mode repeats wrong answers.
**AI Response:** An assertion joined two loose conditions with `or`.
**Your Changes:** Replaced it with the exact expected order.
**Outcome:** The test now fails if the queue logic is wrong in any way.

#### Example 3: Checking a bad export path before the quiz

**Context:** A manual run with an export path that was a folder ran the whole
quiz before reporting the error.
**Your Changes:** Added a check before the quiz, with tests asserting that no
prompt is shown.
**Outcome:** Bad paths fail immediately. The change grew one function past the
size limit, so I split out helpers.

#### Example 4: Strict typing caught real mistakes

**Context:** mypy runs in strict mode.
**AI Response:** One `Any` return, and a lambda that returned the result of a
method returning `None`.
**Your Changes:** Added a typed local and a named helper.
**Outcome:** mypy is clean across 22 source files.

## Software Engineering Practices

### Code Quality Measures

- [x] Formatting (black) and import order (isort)
- [x] Linting (flake8, no errors) and strict type hints (mypy)
- [x] Docstrings on application modules and functions
- [x] Error handling: deck, file, and export errors give one-line messages

### Testing Strategy

- **Types of tests:** unit tests for each module, edge cases for invalid input,
  error tests for file and JSON failures, and integration tests that run whole
  sessions from the command line.
- **Coverage:** 100% branch coverage, enforced in `.coveragerc`.
- **Reliability:** the size test checks every function and file on each run.
- **Test-driven development:** used throughout. Tests were run and seen to fail
  before each implementation existed.

### Design Patterns Used

- **Strategy (`quiz_modes.py`):** `QuizMode` defines how cards are ordered. The
  three modes are interchangeable, so the session does not need to know which
  one it is running.
- **Factory (`quiz_engine.py`):** `create_quiz_mode` maps the `--mode` name to
  its strategy. Adding a mode means adding one entry to `MODE_BUILDERS`.
- **Observer (`quiz_engine.py`, `observers.py`):** `QuizSession` tells registered
  observers about each answer. The log file is one observer, so logging can be
  added or removed without touching quiz logic.

Strategy fits because the mode is chosen at runtime. Observer fits because
logging is an optional side effect.

### Code Structure and Organization

Each module has one job, and `main.py` is a single import and call. The largest
file is about 100 lines, and the size test enforces the 200-line and 7-line limits.

## Technical Challenges and Solutions

### Challenge 1: Keeping the size rule while adding features

**Problem:** Each new feature pushed a function past 7 lines.
**Solution:** Moved logic into descriptively named helpers. The size test caught
every case.
**Lessons Learned:** A rule with a test behind it is kept. A rule kept only in
mind is not.

### Challenge 2: Behaviour that only showed up by hand

**Problem:** All tests passed, but a bad export path failed only after the quiz.
**Solution:** Added a check before the quiz, with a test that no prompt is shown.
**Lessons Learned:** Run the program the way a user would, not only the test suite.

## Code Quality Analysis

### Metrics

- Application modules: 10, about 500 lines in total
- Test functions: 101, giving 133 test cases. Coverage 100% (branch).
- Linting: 0 flake8 errors. Type checking: 0 mypy errors (strict)

### Self-Assessment

- **Code Readability:** 4. Modules are short and named for their job.
- **Code Maintainability:** 4. The strategy and factory make new modes simple to add.
- **Test Quality:** 4. Tests check exact results and error messages. Ctrl+C is
  simulated, not pressed.
- **Documentation:** 4. The README covers setup, usage, and architecture. The AI
  log records real changes, including mistakes.

## Learning Outcomes

### Technical Skills Developed

- Applying Strategy, Factory, and Observer where each has a clear reason
- Writing tests that check exact behaviour, including error paths
- Enforcing code-size rules with a test
- Configuring coverage, flake8, mypy, black, and isort to agree

### AI Collaboration Skills

- Stating limits in the request (function length, file length, message
  wording) produced code that met them more often
- Reviewing each output against the tests and the limits caught problems that
  passed the tests
- First drafts were often correct but needed correction: loose assertions, long
  functions, and typing gaps
- The assistant cannot test the program by hand. A manual run found a usability
  problem the tests did not

## Reflection

### What Worked Well

- Tests first, with every gate run after each change
- The size test, which stopped long functions from accumulating
- Naming each module by its job, which made the design easy to explain

### What Could Be Improved

- Adaptive mode re-queues a wrong card at the back. A smarter scheduler would
  repeat hard cards sooner.
- Progress is not saved between runs.

### Future Enhancements

- Save progress per deck, so adaptive mode learns across sessions
- Add a spaced-repetition mode as another strategy

## Conclusion

The app meets the specification, and every quality gate passes. The most useful
part of the AI collaboration was writing tests and code together, then checking
each change against written rules. A correct first draft is not a finished one.
