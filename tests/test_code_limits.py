"""Quality gates: keep functions short and files small.

Rules enforced on application code (not tests):
- A function's logic (its body, excluding the docstring) is at most 7 lines.
- A file, which holds its classes, is at most 200 lines.
"""

import ast
from pathlib import Path
from typing import Iterator, Union

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MAX_FUNCTION_LINES = 7
MAX_FILE_LINES = 200

FunctionNode = Union[ast.FunctionDef, ast.AsyncFunctionDef]


def app_source_files() -> list[Path]:
    """Return every application module, excluding tests and the virtualenv."""
    files = [*PROJECT_ROOT.glob("*.py"), *PROJECT_ROOT.glob("utils/*.py")]
    return sorted(path for path in files if path.name != "conftest.py")


def function_nodes(tree: ast.Module) -> Iterator[FunctionNode]:
    """Yield every function and method defined in a module."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def logic_line_count(node: FunctionNode) -> int:
    """Count the lines of a function body, skipping its docstring."""
    body = node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(getattr(body[0], "value", None), ast.Constant)
    ):
        body = body[1:]
    if not body:
        return 0
    assert node.end_lineno is not None
    return node.end_lineno - body[0].lineno + 1


@pytest.mark.parametrize("path", app_source_files(), ids=lambda p: p.name)
def test_file_is_at_most_200_lines(path: Path) -> None:
    line_count = len(path.read_text(encoding="utf-8").splitlines())

    assert line_count <= MAX_FILE_LINES, f"{path.name} has {line_count} lines"


@pytest.mark.parametrize("path", app_source_files(), ids=lambda p: p.name)
def test_every_function_logic_is_at_most_7_lines(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    too_long = [
        f"{node.name} ({logic_line_count(node)} lines)"
        for node in function_nodes(tree)
        if logic_line_count(node) > MAX_FUNCTION_LINES
    ]

    assert too_long == [], f"{path.name}: {', '.join(too_long)}"


def test_the_source_set_is_not_empty() -> None:
    assert len(app_source_files()) >= 8
