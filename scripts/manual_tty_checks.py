"""Run the manual CLI checks as scripted scenarios and report pass or fail.

Terminal scenarios run the app inside a pseudo-terminal, so colors and Ctrl+C
behave as they do for a real user. They need macOS or Linux and are reported
as SKIPPED on Windows. Other scenarios pipe input and check the output.

Run from the project root, using the project's virtual environment:

    python scripts/manual_tty_checks.py [--json results.json]

The exit code is 0 when every scenario passes or is skipped, and 1 otherwise.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CTRL_C = "<ctrl-c>"
BACKS = [
    "Application Programming Interface",
    "Content Delivery Network",
    "Central Processing Unit",
    "Domain Name System",
    "Hypertext Transfer Protocol",
    "Internet Protocol",
    "Random Access Memory",
    "Secure Shell",
    "Transport Layer Security",
    "Virtual Private Network",
]
PYTHON_CARDS = ["def", "len", "for", "bool", "except", "int", "dict", "import"]
WAIT_SECONDS = 15.0


@dataclass
class Outcome:
    """What one run of the app produced."""

    code: Optional[int]
    stdout: str
    stderr: str = ""

    @property
    def text(self) -> str:
        """Return standard output followed by standard error."""
        return self.stdout + self.stderr


@dataclass
class Scenario:
    """One manual check: how to run the app, and what must be true afterwards."""

    id: str
    name: str
    command: list[str]
    expected: str
    checks: list[tuple[str, Callable[[Outcome], bool]]]
    answers: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    terminal: bool = False


@dataclass
class Result:
    """The recorded outcome of one scenario."""

    id: str
    name: str
    command: str
    expected: str
    status: str
    details: list[str]
    exit_code: Optional[int]


def _read_idle(fd: int, quiet: float = 0.5) -> str:
    """Read from the terminal until it has been quiet for `quiet` seconds."""
    import select

    data = b""
    while select.select([fd], [], [], quiet)[0]:
        try:
            chunk = os.read(fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        data += chunk
    return data.decode(errors="replace").replace("\r", "")


def _wait_for_exit(pid: int) -> Optional[int]:
    """Wait for the child process; return its exit code, or None if it hangs."""
    deadline = time.monotonic() + WAIT_SECONDS
    while time.monotonic() < deadline:
        done, status = os.waitpid(pid, os.WNOHANG)
        if done:
            return os.waitstatus_to_exitcode(status)
        time.sleep(0.05)
    os.kill(pid, signal.SIGKILL)
    os.waitpid(pid, 0)
    return None


def run_piped(command: list[str], answers: list[str], env: dict[str, str]) -> Outcome:
    """Run the app with its input piped in, as a script or a non-terminal would."""
    completed = subprocess.run(
        [sys.executable, "main.py", *command],
        input="".join(answer + "\n" for answer in answers),
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env={**os.environ, **env},
        timeout=WAIT_SECONDS,
        check=False,
    )
    return Outcome(completed.returncode, completed.stdout, completed.stderr)


def run_in_terminal(
    command: list[str], answers: list[str], env: dict[str, str]
) -> Outcome:
    """Run the app in a pseudo-terminal, typing each answer in turn."""
    pid, fd = _spawn_in_terminal(command, env)
    chunks = [_read_idle(fd)]
    for answer in answers:
        keys = b"\x03" if answer == CTRL_C else (answer + "\n").encode()
        os.write(fd, keys)
        chunks.append(_read_idle(fd))
    code = _wait_for_exit(pid)
    chunks.append(_read_idle(fd))
    os.close(fd)
    return Outcome(code, "".join(chunks))


def _spawn_in_terminal(command: list[str], env: dict[str, str]) -> tuple[int, int]:
    """Fork a child attached to a new pseudo-terminal running the app."""
    import pty

    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(PROJECT_ROOT)
        os.environ.update(env)
        os.execv(sys.executable, [sys.executable, "main.py", *command])
    return pid, fd


def _make_deck(folder: Path, name: str, text: str) -> Path:
    """Write a deck file into a temporary folder and return its path."""
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


def _ten_card_answers() -> list[str]:
    """Return the correct backs for the glossary, with one deliberate miss."""
    answers = list(BACKS)
    answers[1] = "wrong"
    return answers


def build_scenarios(folder: Path) -> list[Scenario]:
    """Define every scenario; temporary decks and reports go in `folder`."""
    report = folder / "report.json"
    log = folder / "answers.log"
    adaptive = ["-m", "adaptive", "-f", "data/python_basics.json", "--no-color"]
    return [
        *terminal_scenarios(),
        *cli_scenarios(folder, report, log, adaptive),
    ]


def terminal_scenarios() -> list[Scenario]:
    """Scenarios that need a real terminal: colors, exit words, and Ctrl+C."""
    glossary = ["-f", "data/glossary.json"]
    return [
        Scenario(
            "TTY-01",
            "Sequential session, one miss, colors on",
            ["--mode", "sequential", "--file", "data/glossary.json", "--stats"],
            "Exit 0; 9 green and 1 red feedback line; summary of 10 attempts at 90.0%",
            [
                ("exit code is 0", lambda o: o.code == 0),
                ("9 green feedback lines", lambda o: o.text.count("\x1b[32m") == 9),
                ("1 red feedback line", lambda o: o.text.count("\x1b[31m") == 1),
                ("summary shows 10 attempts", lambda o: "Attempts: 10" in o.text),
                ("accuracy is 90.0%", lambda o: "Accuracy: 90.0%" in o.text),
            ],
            answers=_ten_card_answers(),
            terminal=True,
        ),
        Scenario(
            "TTY-02",
            "NO_COLOR environment variable disables colors",
            glossary,
            "Exit 0; no escape codes in the output",
            [
                ("exit code is 0", lambda o: o.code == 0),
                ("no escape codes", lambda o: "\x1b[" not in o.text),
            ],
            answers=["API", "exit"],
            env={"NO_COLOR": "1"},
            terminal=True,
        ),
        Scenario(
            "TTY-03",
            "--no-color flag disables colors",
            [*glossary, "--no-color"],
            "Exit 0; no escape codes in the output",
            [
                ("exit code is 0", lambda o: o.code == 0),
                ("no escape codes", lambda o: "\x1b[" not in o.text),
            ],
            answers=["API", "exit"],
            terminal=True,
        ),
        Scenario(
            "TTY-04",
            "Adaptive session repeats a missed card",
            [
                "-m",
                "adaptive",
                "-f",
                "data/python_basics.json",
                "--stats",
                "--no-color",
            ],
            "Exit 0; 9 attempts for 8 cards, 8 correct",
            [
                ("exit code is 0", lambda o: o.code == 0),
                ("9 attempts", lambda o: "Attempts: 9" in o.text),
                ("8 correct", lambda o: "Correct: 8" in o.text),
            ],
            answers=["wrong", *PYTHON_CARDS[1:], "def"],
            terminal=True,
        ),
        Scenario(
            "TTY-05",
            "Typing 'exit' stops the quiz early",
            [*glossary, "--no-color"],
            "Exit 0; 'Leaving the quiz early.' is printed",
            [
                ("exit code is 0", lambda o: o.code == 0),
                ("early-exit message", lambda o: "Leaving the quiz early." in o.text),
            ],
            answers=["exit"],
            terminal=True,
        ),
        Scenario(
            "TTY-06",
            "Real Ctrl+C stops gracefully",
            glossary,
            "Exit 0; 'Quiz stopped. Goodbye!' printed; no traceback",
            [
                ("exit code is 0", lambda o: o.code == 0),
                ("goodbye message", lambda o: "Quiz stopped. Goodbye!" in o.text),
                ("no traceback", lambda o: "Traceback" not in o.text),
            ],
            answers=[CTRL_C],
            terminal=True,
        ),
    ]


def cli_scenarios(
    folder: Path, report: Path, log: Path, adaptive: list[str]
) -> list[Scenario]:
    """Scenarios that check flags, error messages, and file outputs."""
    bad_card = _make_deck(folder, "missing_back.json", '[{"front": "A"}]')
    bad_json = _make_deck(folder, "broken.json", '[{"front": ')
    return [
        Scenario(
            "CLI-01",
            "--help lists every flag",
            ["--help"],
            "Exit 0; help text names all six flags",
            [
                ("exit code is 0", lambda o: o.code == 0),
                *[
                    (f"lists {flag}", lambda o, f=flag: f in o.stdout)
                    for flag in (
                        "--file",
                        "--mode",
                        "--stats",
                        "--export",
                        "--log-file",
                        "--no-color",
                    )
                ],
            ],
        ),
        Scenario(
            "CLI-02",
            "Card without 'back' gives a one-line error",
            ["-f", str(bad_card)],
            "Exit 1; 'Error:' names the field; no traceback",
            [
                ("exit code is 1", lambda o: o.code == 1),
                ("names 'back'", lambda o: "'back'" in o.stderr),
                ("no traceback", lambda o: "Traceback" not in o.text),
            ],
        ),
        Scenario(
            "CLI-03",
            "Malformed JSON gives a friendly error",
            ["-f", str(bad_json)],
            "Exit 1; 'Invalid JSON' with a line number",
            [
                ("exit code is 1", lambda o: o.code == 1),
                ("invalid JSON message", lambda o: "Invalid JSON" in o.stderr),
                ("no traceback", lambda o: "Traceback" not in o.text),
            ],
        ),
        Scenario(
            "CLI-04",
            "Missing deck file gives a friendly error",
            ["-f", str(folder / "no_such_deck.json")],
            "Exit 1; 'File not found' message",
            [
                ("exit code is 1", lambda o: o.code == 1),
                ("file-not-found message", lambda o: "File not found" in o.stderr),
            ],
        ),
        Scenario(
            "CLI-05",
            "Export to a folder fails before the quiz starts",
            ["-f", "data/glossary.json", "--export", str(folder)],
            "Exit 1; error printed; no question is asked",
            [
                ("exit code is 1", lambda o: o.code == 1),
                ("error message", lambda o: "is a folder" in o.stderr),
                ("no question asked", lambda o: "> " not in o.stdout),
            ],
        ),
        Scenario(
            "CLI-06",
            "Adaptive session, all cards correct (piped input)",
            [*adaptive, "--stats"],
            "Exit 0; 100.0% accuracy",
            [
                ("exit code is 0", lambda o: o.code == 0),
                ("accuracy is 100.0%", lambda o: "Accuracy: 100.0%" in o.stdout),
            ],
            answers=PYTHON_CARDS,
        ),
        Scenario(
            "CLI-07",
            "Export and log file written during a session",
            [*adaptive, "--export", str(report), "--log-file", str(log)],
            "Exit 0; report has 2 attempts; log has 2 lines",
            [
                ("exit code is 0", lambda o: o.code == 0),
                ("report has 2 attempts", lambda o: _report_attempts(report) == 2),
                ("log has 2 lines", lambda o: _line_count(log) == 2),
            ],
            answers=["def", "wrong", "exit"],
        ),
        Scenario(
            "CLI-08",
            "Success-criteria command: sequential mode, glossary deck",
            ["--mode", "sequential", "--file", "data/glossary.json"],
            "Exit 0; quiz starts and exits cleanly",
            [
                ("exit code is 0", lambda o: o.code == 0),
                ("first card shown", lambda o: "API" in o.stdout),
            ],
            answers=["exit"],
        ),
    ]


def _report_attempts(path: Path) -> Optional[int]:
    """Return the attempt count stored in a JSON report, if the file exists."""
    if not path.exists():
        return None
    return int(json.loads(path.read_text(encoding="utf-8"))["attempts"])


def _line_count(path: Path) -> int:
    """Return how many lines a file has, or 0 if it does not exist."""
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8").splitlines())


def run_scenario(scenario: Scenario) -> Result:
    """Run one scenario and compare its outcome with every check."""
    command = " ".join(["python", "main.py", *scenario.command])
    if scenario.terminal and os.name == "nt":
        return Result(
            scenario.id,
            scenario.name,
            command,
            scenario.expected,
            "SKIPPED",
            ["pseudo-terminal checks need macOS or Linux"],
            None,
        )
    runner = run_in_terminal if scenario.terminal else run_piped
    outcome = runner(scenario.command, scenario.answers, scenario.env)
    verdicts = [(label, check(outcome)) for label, check in scenario.checks]
    details = [f"{'PASS' if ok else 'FAIL'}: {label}" for label, ok in verdicts]
    status = "PASS" if all(ok for _, ok in verdicts) else "FAIL"
    return Result(
        scenario.id,
        scenario.name,
        command,
        scenario.expected,
        status,
        details,
        outcome.code,
    )


def main(argv: Optional[list[str]] = None) -> int:
    """Run every scenario, print a summary, and return the exit status."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=Path, help="also write results as JSON")
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory() as temp:
        results = [run_scenario(s) for s in build_scenarios(Path(temp))]
    for result in results:
        print(f"[{result.status}] {result.id} {result.name}")
        for detail in result.details:
            print(f"        {detail}")
    if args.json:
        args.json.write_text(
            json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8"
        )
    failed = [r for r in results if r.status == "FAIL"]
    print(
        f"\n{len(results) - len(failed)} of {len(results)} scenarios passed or skipped"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
