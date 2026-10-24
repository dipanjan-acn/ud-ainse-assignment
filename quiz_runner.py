"""The interactive quiz loop: ask, check, give feedback, and stop cleanly."""

from typing import Callable, TextIO

from display import feedback_message
from quiz_engine import QuizSession

EXIT_COMMAND = "exit"

Asker = Callable[[str], str]


def run_quiz(session: QuizSession, ask: Asker, out: TextIO, color: bool) -> bool:
    """Ask cards until the deck is finished or the user quits.

    Ctrl+C and end-of-input both stop the quiz without a traceback.

    Returns:
        True if every card was answered, False if the quiz stopped early.
    """
    try:
        return _ask_all_cards(session, ask, out, color)
    except (KeyboardInterrupt, EOFError):
        out.write("\nQuiz stopped. Goodbye!\n")
        return False


def _ask_all_cards(session: QuizSession, ask: Asker, out: TextIO, color: bool) -> bool:
    """Run the question loop, returning False if the user types 'exit'."""
    while (card := session.next_card()) is not None:
        answer = ask(f"{card.front}\n> ")
        if _is_exit(answer):
            out.write("Leaving the quiz early.\n")
            return False
        _give_feedback(out, session.submit(card, answer), card.back, color)
    return True


def _is_exit(answer: str) -> bool:
    """Return True when the answer is the exit command, ignoring case and spaces."""
    return answer.strip().lower() == EXIT_COMMAND


def _give_feedback(out: TextIO, correct: bool, expected: str, color: bool) -> None:
    """Write the result of one answer on its own line."""
    out.write(feedback_message(correct, expected, color) + "\n")
