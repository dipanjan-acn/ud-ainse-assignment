# Submission checklist

Checked against the repository at commit `73f43e7` on `main`. Status key:
**Met** means the item is complete and was verified. **Partial** means part of it
is missing. **Open** means action is needed.

## Submission requirements

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | GitHub repository link | Met | https://github.com/dipanjan-acn/ud-ainse-assignment (public) |
| 2 | Complete codebase: source, tests, documentation | Met | `main.py`, `cli.py`, `arguments.py`, `config.py`, `quiz_engine.py`, `quiz_modes.py`, `quiz_runner.py`, `observers.py`, `export.py`, `display.py`, `ai_generator.py`, `ai_transport.py`, `utils/`, `tests/`, `docs/` |
| 3 | `ai_edit_log.md` with at least 5 detailed AI interactions | Met | 12 entries, each with context, prompt, response, changes, reasoning, outcome, and lessons. No template placeholders remain |
| 4 | Final report from the provided template, 1,000 to 1,500 words | **Partial** | Word count is 1,317, which meets the range. Five template sections are missing (see below) |
| 5 | README with current setup instructions and feature descriptions | Met | Setup, usage, configuration, AI generation, security, architecture diagrams, and testing commands |
| 6 | Test coverage report above 80% | Met | 100% branch coverage. Text report in `docs/coverage_summary.txt`. The HTML report (`htmlcov/`) is generated locally and is git-ignored |
| 7 | Code quality verification: all linting tools pass | Met | flake8 (0 issues), mypy strict (0 errors), black and isort (clean). Results are recorded in `docs/test_execution_report.pdf` |

## Project requirements

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 8 | Loads JSON in array and object formats | Met | `utils/file_handler.py`; tests in `test_flashcard_loader.py` |
| 9 | Friendly messages for malformed JSON or missing fields, no tracebacks | Met | CLI scenarios CLI-02 and CLI-03 |
| 10 | Sequential, random, and adaptive modes | Met | `quiz_modes.py` |
| 11 | Strategy pattern | Met | `QuizMode` and its three subclasses |
| 12 | Factory pattern, selecting the mode from user input | Met | `create_quiz_mode` in `quiz_engine.py` |
| 13 | `argparse` with `-f`, `-m`, and `--stats` | Met | `arguments.py`; CLI-01 lists every flag |
| 14 | Green and red feedback | Met | `display.py`; TTY-01 checks the colored output |
| 15 | `exit` and Ctrl+C quit gracefully | Met | TTY-05 and TTY-06 |
| 16 | `python main.py --help` works | Met | CLI-01 |
| 17 | `python main.py --mode sequential --file data/glossary.json` works | Met | CLI-08 |
| 18 | `python main.py -m adaptive -f data/python_basics.json` plays a full game | Met | CLI-06 and TTY-04 |

## Required test cases

| Required name | Status | Actual name in the repo |
|---------------|--------|--------------------------|
| `test_load_valid_flashcards_array` | Met | Exact match |
| `test_load_invalid_json` | **Open** | `test_load_invalid_json_raises_friendly_error` |
| `test_load_missing_required_field` | **Open** | `test_load_missing_required_field_back_is_rejected` |
| `test_quiz_mode_factory` | Met | Exact match |
| `test_adaptive_mode_behavior` | Met | Exact match |
| `test_full_session` | **Open** | `test_full_session_with_three_answers_reports_correct_stats` |

The three open items are the same tests under longer names. Renaming them to the
exact required names would satisfy a literal check, and would not change behaviour.

## Final report gaps

The template sections below are missing from `docs/final_report.md`:

- Challenges with AI Collaboration
- Code Quality Measures (the content exists under Software Engineering Practices)
- Code Quality Analysis (the content exists under Quality Results)
- Learning Outcomes
- Appendices

The template also says "Aim for 2000-3000 words". That conflicts with the
1,000 to 1,500 word requirement in the assignment. This checklist follows the
assignment.

## Open actions

1. Rename the three tests to the exact required names.
2. Add the five missing template sections to the final report, keeping it within 1,500 words.
3. Decide whether the HTML coverage report should be committed. It is currently git-ignored.
4. Commit this checklist, if you want it in the repository.
