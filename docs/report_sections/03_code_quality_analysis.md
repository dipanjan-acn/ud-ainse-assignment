# Code Quality Analysis

## Metrics

| Measure | Value |
|---------|-------|
| Application Python files | 15 (root modules and `utils/`) |
| Application lines | 1,122 |
| Largest file | `cli.py`, 149 lines (limit 200) |
| Functions in application code | 87 |
| Classes in application code | 12 |
| Longest function body | 7 lines (limit 7) |
| Test cases | 204, in 14 test files |
| Branch coverage | 100% |
| flake8 issues | 0 |
| mypy errors (strict) | 0 |
| bandit issues | 0 (867 lines scanned) |
| Known dependency vulnerabilities | 0 (76 packages) |
| Manual scenarios passed | 17 of 17 |

## Structure

Each module has one job. The quiz logic (`quiz_modes.py`, `quiz_engine.py`) has
no dependency on the terminal or the network. The network code is confined to one
module, `ai_transport.py`. Settings are resolved in `config.py`, separate from the
command-line flags in `arguments.py`.

## Self-assessment

- **Readability: 4.** Modules are short and named for their job. Some helper names
  are long, but they say what the helper does.
- **Maintainability: 4.** A new quiz mode needs one class and one entry in the
  factory. The size rules keep each module easy to review.
- **Test quality: 4.** Tests check exact results and error messages. Ctrl+C is
  checked with an injected exception and with a real interrupt in a pseudo-terminal.
- **Documentation: 4.** The README covers setup, configuration, and architecture.
  The edit log and the analysis record decisions and mistakes.

## Where the code is weaker

- The adaptive queue re-asks a missed card at the back, not sooner.
- Progress is not saved between runs.
- The AI generator has been tested only against a fake transport, not the live service.
