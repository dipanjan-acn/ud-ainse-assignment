# AI-Assisted Development Project Report

**Project Title:** Flashcard Quizzer
**Repository:** https://github.com/dipanjan-acn/ud-ainse-assignment
**Date:** 2026-10-24
**Version reported:** commit 2e8b2ff, with the latest reports in `docs/`

## Executive Summary

The Flashcard Quizzer is a command-line app that quizzes the user on flashcards
from a JSON deck. It has three modes: sequential, random, and adaptive. Adaptive
mode asks again any card answered wrongly, until it is answered correctly. The
app also shows a session summary, colors each answer, exports a JSON report, logs
each answer, reads settings from a config file or environment variables, and can
generate a deck with an AI service.

I built it with Claude, an AI coding assistant, in a local terminal. I set the
specification and the quality rules. The assistant wrote the code, and I checked
each change with the tests, linters, security scanners, and the CLI itself. Many
first drafts were correct but broke a rule I had set, or contained a test that
could pass for the wrong reason. The edit log records these cases. It has 12
entries. An earlier summary said eight, which was wrong.

The current result: 204 tests pass, with 100% branch coverage. flake8, strict
mypy, black, and isort are clean. bandit reports no issues, pip-audit reports no
known vulnerabilities, and all 17 scripted manual scenarios pass.

## Project Overview

### Problem Statement

Flashcard revision works best when the user is quizzed on the cards they find
hard. The app had to load a deck, offer several quiz orders, fail clearly on bad
input, and make decks easy to create.

### Solution Approach

- `utils/` reads, validates, and saves decks, and defines the card model.
- `quiz_modes.py` holds the ordering strategies. `quiz_engine.py` holds the
  session, the statistics, and the mode factory.
- `config.py` resolves settings. `ai_generator.py` builds and checks AI requests,
  and `ai_transport.py` is the only module that touches the network.
- `cli.py` and `arguments.py` parse the command line and wire the parts together.

The code targets Python 3.10 or later. The runtime uses only the standard library.

### Final Features

- Decks in array or object format, with one-line error messages
- Input limits: deck files up to 1 MB, card text up to 500 characters
- Sequential, random, and adaptive modes, chosen through a factory
- Settings from flags, then environment variables, then a JSON config file
- AI deck generation (`--generate`, `--count`, `--save`) over HTTPS only
- Colored feedback, a session summary, a JSON export, and a per-answer log
- Graceful stop on `exit`, Ctrl+C, or end of input

## AI Collaboration Experience

### AI Tools Used

- [x] Claude (Anthropic's coding assistant, used through a terminal session)
- [ ] GitHub Copilot, [ ] ChatGPT, [ ] Other

### Collaboration Workflow

1. **State the rules.** Each request stated the behaviour and the limits: 7
   lines per function body, 200 lines per file, and 100% coverage.
2. **Write tests first,** and run them to confirm they fail.
3. **Implement the minimum** to make them pass.
4. **Run every gate** after each change: tests with coverage, flake8, strict
   mypy, black, isort, the size test, bandit, and pip-audit.
5. **Check by hand.** I ran the CLI with good and bad decks, bad paths, piped
   answers, and a real Ctrl+C.

### Most Valuable AI Interactions

#### Example 1: A security finding that needed a check, not a suppression

**Context:** Bandit flagged `urlopen` in the AI transport (B310), because it can
open file and other schemes.
**AI Response:** The simplest fix was a `# nosec` comment.
**Your Changes:** Added an HTTPS-only check before the call, with tests showing
that `http`, `file`, and `ftp` URLs never reach `urlopen`.
**Outcome:** bandit reports no issues on 867 lines of app code.

#### Example 2: A test that could pass for the wrong reason

**Context:** The rubric requires a test that adaptive mode repeats wrong answers.
**AI Response:** An assertion joined two loose conditions with `or`.
**Your Changes:** Replaced it with the exact expected order.
**Outcome:** The test now fails if the queue logic is wrong in any way.

#### Example 3: Splitting a function that broke the size rule

**Context:** Reading a deck can fail in several ways, each with its own message.
**AI Response:** One function with four `except` branches, about 10 lines long.
**Your Changes:** Moved the choice of message into a helper.
**Outcome:** Both functions are within the limit, and the loader tests pass.

## Software Engineering Practices

### Code Quality and Security

- Formatting (black), import order (isort), and strict type hints (mypy).
- Docstrings on every module, class, and function. Errors give one-line messages,
  and no traceback reaches the user.
- Deck files are limited to 1 MB and card text to 500 characters, so memory use
  stays bounded.
- Only HTTPS URLs are opened. The API key is sent only in a header and never
  appears in output or errors.

### Testing Strategy

- **Types of tests:** unit tests for each module, edge cases for invalid input,
  error tests for files, JSON, configuration, and HTTP failures, and integration
  tests that run whole sessions from the command line.
- **Coverage:** 100% branch coverage, enforced in `.coveragerc`.
- **Network:** the AI tests use a fake transport and never reach the real service.

### Design Patterns Used

- **Strategy (`quiz_modes.py`):** the three modes are interchangeable, so the
  session never checks which mode it is running.
- **Factory (`quiz_engine.py`):** `create_quiz_mode` maps the mode name to its
  strategy. A new mode needs one entry in `MODE_BUILDERS`.
- **Observer (`quiz_engine.py`, `observers.py`):** `QuizSession` tells registered
  observers about each answer. The log file is one observer.

Strategy fits because the mode is chosen at runtime. Observer fits because
logging is an optional side effect.

## Performance

A 10,000-card deck loads in about 5 ms, and a 10,000-answer CLI session takes
about 110 ms. Profiling found no single hot spot. One candidate, stripping each
field once, showed no real change in an A/B comparison and was reverted, so no
optimization is included. The evidence is in `docs/performance_decisions.md`.
Two limits apply: the 1 MB file limit rejects 100,000-card decks, and run-to-run
variance on the test machine is large.

## Technical Challenges and Solutions

### Challenge 1: Keeping the size rule while adding features

**Problem:** Each feature pushed a function past 7 lines, and the AI generator
reached 204 lines.
**Solution:** Moved the network code into `ai_transport.py`, and split the helpers.
**Lessons Learned:** A rule with a test behind it is kept. A rule kept only in mind
is not.

### Challenge 2: A requirements line that was silently broken

**Problem:** An appended pin was joined to the line above it, which turned a
dependency into a comment.
**Solution:** A dry-run install showed the pin had no effect. The file was rewritten
with one requirement per line, and a fresh install was checked.
**Lessons Learned:** Verify a change by its effect, not only by the exit code.

## Quality Results

- Application code: 15 Python files, about 1,120 lines in total
- Tests: 204 test cases in 14 files, with 100% branch coverage
- Linting: 0 flake8 errors. Type checking: 0 mypy errors (strict)
- Security: 0 bandit issues on 867 lines. 0 known dependency vulnerabilities
- Manual scenarios: 17 of 17 passed

## Known Gaps

- **Windows:** not tested. The terminal scenarios are reported as skipped there,
  and colors have not been checked.
- **Live AI service:** the generator has not been run against the real service.
  Its replies are checked against the documented API format.
- **Progress:** progress is not saved between runs.

## Reflection

- The strongest practice was writing tests and code together, then checking each
  change against written rules.
- First drafts were often correct but needed correction: loose assertions, long
  functions, typing gaps, and one silent dependency error.
- Adaptive mode re-queues a wrong card at the back. A smarter scheduler would
  repeat hard cards sooner, and saving progress would let it learn across sessions.

## Conclusion

The app meets the specification, and every quality gate and security scan passes.
A correct first draft was not a finished one. The rules, the tests, the scanners,
and a manual run each caught problems the others missed.
