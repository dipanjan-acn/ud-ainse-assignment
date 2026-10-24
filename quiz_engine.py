"""Quiz session engine and the factory that builds quiz modes.

Design patterns used here:
- Strategy: `QuizMode` (in quiz_modes.py) is the interchangeable ordering
  algorithm that `QuizSession` delegates to.
- Factory: `create_quiz_mode` turns a mode name into the matching strategy.
"""

import random
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from quiz_modes import AdaptiveMode, QuizMode, RandomMode, SequentialMode
from utils.flashcard import Flashcard

ModeBuilder = Callable[[Sequence[Flashcard], random.Random], QuizMode]


def new_generator() -> random.Random:
    """Return a generator for shuffling card order.

    This is not used for anything security-sensitive, so the non-cryptographic
    generator is acceptable here.
    """
    return random.Random()  # nosec B311


MODE_BUILDERS: dict[str, ModeBuilder] = {
    "sequential": lambda cards, rng: SequentialMode(cards),
    "random": lambda cards, rng: RandomMode(cards, rng),
    "adaptive": lambda cards, rng: AdaptiveMode(cards),
}


def create_quiz_mode(
    name: str,
    cards: Sequence[Flashcard],
    rng: Optional[random.Random] = None,
) -> QuizMode:
    """Factory: build the quiz mode registered under `name`.

    Raises:
        ValueError: If no mode is registered under `name`.
    """
    builder = MODE_BUILDERS.get(name)
    if builder is None:
        choices = ", ".join(MODE_BUILDERS)
        raise ValueError(f"Unknown quiz mode '{name}'. Choose from: {choices}.")
    return builder(cards, rng if rng is not None else new_generator())


def normalize_answer(text: str) -> str:
    """Lower-case text and collapse runs of whitespace for comparison."""
    return " ".join(text.casefold().split())


def is_correct(answer: str, expected: str) -> bool:
    """Return True when the answer matches the expected text after normalizing."""
    return normalize_answer(answer) == normalize_answer(expected)


@dataclass
class SessionStats:
    """Running totals for one quiz session."""

    correct: int = 0
    incorrect: int = 0
    misses: Counter[str] = field(default_factory=Counter)

    @property
    def attempts(self) -> int:
        """Return the total number of answers given."""
        return self.correct + self.incorrect

    @property
    def accuracy(self) -> float:
        """Return the percentage of correct answers, or 0.0 with no attempts."""
        if self.attempts == 0:
            return 0.0
        return self.correct / self.attempts * 100

    def record(self, front: str, correct: bool) -> None:
        """Count one answer, remembering which card was missed."""
        if correct:
            self.correct += 1
            return
        self.incorrect += 1
        self.misses[front] += 1


@dataclass(frozen=True)
class AnswerEvent:
    """What happened on one answer, passed to every observer."""

    front: str
    expected: str
    answer: str
    correct: bool


AnswerObserver = Callable[[AnswerEvent], None]


class QuizSession:
    """Runs a quiz by pairing a quiz mode with running statistics.

    Observers registered with `add_observer` are told about every answer.
    """

    def __init__(self, mode: QuizMode) -> None:
        """Start a session that asks cards in the order chosen by `mode`."""
        self._mode = mode
        self._stats = SessionStats()
        self._observers: list[AnswerObserver] = []

    def add_observer(self, observer: AnswerObserver) -> None:
        """Register a callable that receives an AnswerEvent after each answer."""
        self._observers.append(observer)

    @property
    def stats(self) -> SessionStats:
        """Return the statistics collected so far."""
        return self._stats

    def next_card(self) -> Optional[Flashcard]:
        """Return the next card to ask, or None when the quiz is finished."""
        return self._mode.next_card()

    def submit(self, card: Flashcard, answer: str) -> bool:
        """Check an answer, record it, and return whether it was correct."""
        correct = is_correct(answer, card.back)
        self._stats.record(card.front, correct)
        self._mode.record_answer(card, correct)
        self._notify(AnswerEvent(card.front, card.back, answer, correct))
        return correct

    def _notify(self, event: AnswerEvent) -> None:
        """Pass one answer event to every registered observer."""
        for observer in self._observers:
            observer(event)
