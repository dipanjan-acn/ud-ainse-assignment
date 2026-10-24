"""Quiz modes: Strategy classes that decide which card to ask next."""

import random
from abc import ABC, abstractmethod
from collections import deque
from typing import Sequence

from utils.flashcard import Flashcard


class QuizMode(ABC):
    """Strategy interface for ordering the cards in a quiz."""

    def __init__(self, cards: Sequence[Flashcard]) -> None:
        """Queue the cards in the order returned by `arrange`."""
        self._queue: deque[Flashcard] = deque(self.arrange(list(cards)))

    @abstractmethod
    def arrange(self, cards: list[Flashcard]) -> list[Flashcard]:
        """Return the cards in the order they should first be asked."""

    def record_answer(self, card: Flashcard, correct: bool) -> None:
        """React to an answer. The default does nothing."""

    def next_card(self) -> Flashcard | None:
        """Return the next card to ask, or None when the quiz is over."""
        return self._queue.popleft() if self._queue else None

    def remaining(self) -> int:
        """Return how many cards are still queued."""
        return len(self._queue)


class SequentialMode(QuizMode):
    """Ask the cards in the order they appear in the deck."""

    def arrange(self, cards: list[Flashcard]) -> list[Flashcard]:
        """Keep the deck order unchanged."""
        return cards


class RandomMode(QuizMode):
    """Ask every card once, in a shuffled order."""

    def __init__(self, cards: Sequence[Flashcard], rng: random.Random) -> None:
        """Store the generator used for shuffling, then queue the cards."""
        self._rng = rng
        super().__init__(cards)

    def arrange(self, cards: list[Flashcard]) -> list[Flashcard]:
        """Shuffle the cards in place and return them."""
        self._rng.shuffle(cards)
        return cards


class AdaptiveMode(QuizMode):
    """Ask every card once, then repeat each wrong answer until it is right."""

    def arrange(self, cards: list[Flashcard]) -> list[Flashcard]:
        """Keep the deck order for the first pass."""
        return cards

    def record_answer(self, card: Flashcard, correct: bool) -> None:
        """Queue a missed card again at the end of the quiz queue."""
        if not correct:
            self._queue.append(card)
