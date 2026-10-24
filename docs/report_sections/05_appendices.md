# Appendices

## Appendix A: AI interaction log, entry titles

The full entries, with prompts, responses, changes, and lessons, are in
`docs/ai_edit_log.md`.

1. Loader error handling broke the function-length rule
2. Adaptive-mode assertion that could pass for the wrong reason
3. Integration test script in the wrong order
4. Type checking caught an `Any` return and a value-returning lambda
5. Export failure appeared only after the quiz had run
6. Size gate caught two long functions
7. Choosing urllib over a third-party HTTP client
8. The size rule split the generator into two modules
9. Bandit found a real weakness, and the fix was a check, not a suppression
10. A test helper broke an assertion it did not need to change
11. JSON for the config file, not TOML
12. A requirements line was silently broken by my own edit

## Appendix B: Commands to reproduce the checks

```bash
python -m pytest --cov=. --cov-report=term-missing
python -m black --check .
python -m isort --check-only .
python -m flake8 .
python -m mypy .
python -m bandit -r . -x ./venv,./tests,./scripts,./htmlcov
python -m pip_audit -r requirements.txt
python scripts/manual_tty_checks.py
```

## Appendix C: Supporting documents

| File | Contents |
|------|----------|
| `docs/ai_edit_log.md` | Twelve AI interaction entries |
| `docs/ai_interaction_analysis.md` | Strengths, weaknesses, and human judgment |
| `docs/performance_decisions.md` | Measurements, rejected changes, and evidence |
| `docs/submission_checklist.md` | Requirement-by-requirement status |
| `docs/coverage_summary.txt` | Coverage output for the final run |
| `docs/test_execution_report.pdf` | Every test, gate, and manual scenario |
| `docs/consolidated_scan_report.pdf` | Scan results, before and after, with actions taken |
| `docs/performance_report.pdf` | Latest performance results and limits |

## Appendix D: Performance summary

| Operation | Median |
|-----------|--------|
| Load a 10,000-card deck | 4.7 ms |
| Random session, 10,000 cards | 9.0 ms |
| Adaptive session, 10,000 cards | 13.9 ms |
| CLI, 10,000 piped answers | 112.5 ms |
| CLI startup | 81.6 ms |

Run-to-run variance on the test machine is large, so compare changes with an A/B
test in one process.
