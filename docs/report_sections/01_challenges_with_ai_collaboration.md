# Challenges with AI Collaboration

This section records where the AI assistant's output needed correction, what
kind of error each one was, and how it was caught. The full record is in
`docs/ai_edit_log.md`.

## Wrong assumptions about the project

- **Dependency choice:** The assistant proposed a third-party HTTP client. The
  standard library's `urllib` was enough, and it kept the runtime dependency-free.
- **Language version:** The assistant proposed TOML configuration, which needs
  Python 3.11. The project supports 3.10, so the config file is JSON.

These were correct in general and wrong for this project. Each was caught by
checking the suggestion against the project's stated constraints.

## Rule violations in first drafts

First drafts repeatedly broke the 7-line function rule and the 200-line file rule.
The `ai_generator.py` module reached 204 lines. The size test caught each case,
and each was fixed by moving logic into named helpers or a separate module.

## Weak tests

One adaptive-mode assertion accepted two outcomes joined by `or`, so it could pass
for the wrong reason. It was replaced with an exact expected order. A scripted
integration test fed answers in the wrong order, which I found by tracing the
expected sequence by hand.

## Edits that changed behaviour

- A type fix replaced a lambda with a helper that stopped recording prompts. A
  configuration test failed on the missing data, and the helper was restored.
- A requirements pin was appended without a newline, which joined it to the line
  above and silently removed a dependency. A dry-run install and a fresh install
  caught it.

## Inaccurate reporting

A summary said the edit log had eight entries. It had six. The count came from
memory rather than from the file. Later counts were checked by running commands.

## Environment and tooling

Some commands assumed GNU tools that macOS does not provide, such as `timeout`.
Shell globbing in zsh did not expand a variable as expected. Each failure was
visible in the output and was fixed, but each cost time.

## Lessons

Checking every suggestion against the project's constraints caught most of the
problems. The tests, scanners, and manual runs caught the rest, and no single
check was enough on its own.
