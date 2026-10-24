# Learning Outcomes

## Technical skills

- Applying Strategy, Factory, and Observer where each one solves a real problem.
- Writing tests that check exact behaviour, including error paths and edge cases.
- Enforcing code-size and security rules with tests and scanners, so they cannot
  quietly lapse.
- Configuring coverage, flake8, mypy, black, isort, bandit, and pip-audit to agree.
- Handling untrusted input: size limits, field validation, and an HTTPS-only network path.
- Separating a network boundary from the logic that uses it, so the logic can be
  tested without a network.

## AI collaboration skills

- Stating constraints in the request, such as the minimum Python version, the
  dependency policy, and the size limits, produced code that met them more often.
- Checking each suggestion against those constraints caught wrong assumptions.
- Treating a passing test as one check among several. Tests, scanners, and manual
  runs each found problems the others missed.
- Verifying claims by running commands. A recalled count was wrong, and the file
  gave the correct figure.
- Recognizing which decisions need a person: scope, security posture, public
  visibility of the repository, and what counts as done.

## Software engineering insights

- A pattern should solve a real problem. Strategy fits because the mode is chosen
  at runtime. Observer fits because logging is an optional side effect.
- A proposed optimization needs evidence. One candidate looked faster in separate
  runs and made no difference in an A/B comparison, so it was rejected.
- A dependency should be justified. The standard library covered every need here.
