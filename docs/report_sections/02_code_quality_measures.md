# Code Quality Measures

- **Formatting:** black, with the default line length, is clean on every file.
- **Import order:** isort is clean. Its profile is set to black, so the two tools agree.
- **Linting:** flake8 reports no issues, with an 88-character line limit set in `.flake8`.
- **Type checking:** mypy runs in strict mode and reports no errors across 32 source files.
- **Docstrings:** every module, class, and function has one. A check run during the
  build found no missing docstrings.
- **Size rules:** `tests/test_code_limits.py` fails the build if any application
  function body exceeds 7 lines, or any application file exceeds 200 lines.
- **Error handling:** every expected failure produces a one-line message. Unexpected
  exceptions are not caught, so a real bug stays visible.
- **Security scanning:** bandit reports no issues on 867 lines of application code.
  pip-audit reports no known vulnerabilities across 76 packages.
- **Coverage:** branch coverage is 100%, enforced by `.coveragerc`, so a drop below
  100% fails the run.
- **Reproducibility:** each check is a single command listed in the README.
