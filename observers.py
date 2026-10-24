"""Observers that react to each answer, such as writing a log file.

Observer pattern: `QuizSession` notifies registered observers after every
answer, so logging can be added or removed without touching the quiz logic.
"""

import logging
from pathlib import Path
from types import TracebackType
from typing import Optional, Type

from quiz_engine import AnswerEvent

LOG_FORMAT = "%(asctime)s %(message)s"
LINE_FORMAT = "%s answer=%r expected=%r %s"


class AnswerLogger:
    """Observer that appends one line per answer to a log file.

    Use it as a context manager, or call `close` when the quiz is over.
    """

    def __init__(self, path: Path) -> None:
        """Open (or create) the log file in append mode.

        Raises:
            OSError: If the file cannot be opened for writing.
        """
        self._logger = logging.Logger(f"flashcard.{path.name}", logging.INFO)
        self._handler = logging.FileHandler(path, encoding="utf-8")
        self._handler.setFormatter(logging.Formatter(LOG_FORMAT))
        self._logger.addHandler(self._handler)

    def __call__(self, event: AnswerEvent) -> None:
        """Write a single line describing the answer."""
        verdict = "correct" if event.correct else "incorrect"
        self._logger.info(
            LINE_FORMAT, event.front, event.answer, event.expected, verdict
        )

    def close(self) -> None:
        """Flush and release the log file."""
        self._logger.removeHandler(self._handler)
        self._handler.close()

    def __enter__(self) -> "AnswerLogger":
        """Return this logger for use in a `with` block."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Close the log file when the `with` block ends."""
        self.close()
