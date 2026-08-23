"""Readers that find every comment and docstring a source file carries."""

from __future__ import annotations

import ast
import bisect
import io
import os
import tokenize
from dataclasses import dataclass
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from collections.abc import Callable

DEFINITION_NODES = (ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Module)

OPENS_A_PATTERN = "(,=:[!&|?{};+-*%~^<>"


class Unreadable(Exception):
    """A file no reader could parse."""


@dataclass(frozen=True)
class Finding:
    """A line carrying a comment or a docstring."""

    path: str
    line_number: int

    def __str__(self) -> str:
        """Format as path:line."""
        return f"{self.path}:{self.line_number}"


def _lines_of(text: str, places: list[int]) -> list[int]:
    """Turn character offsets into the one-based lines holding them."""
    breaks = [place for place, character in enumerate(text) if character == "\n"]
    return sorted({bisect.bisect_right(breaks, place) + 1 for place in places})


def _past_quoted(text: str, place: int) -> int:
    """Step over a quoted string, honouring backslash escapes."""
    quote = text[place]
    place += 1
    while place < len(text):
        if text[place] == "\\":
            place += 2
        elif text[place] == quote:
            return place + 1
        else:
            place += 1
    return place


def _past_line(text: str, place: int) -> int:
    """Step to the end of the line an offset sits on."""
    end = text.find("\n", place)
    return len(text) if end < 0 else end


def _past_block(text: str, place: int, closing: str) -> int:
    """Step over a block comment, to the end of the file when nobody closed it."""
    end = text.find(closing, place + len(closing))
    return len(text) if end < 0 else end + len(closing)


def _opens_a_pattern(text: str, place: int) -> bool:
    """Decide whether a slash starts a regular expression rather than a division."""
    before = text[:place].rstrip()
    return not before or before[-1] in OPENS_A_PATTERN or before.endswith("return")


def _past_pattern(text: str, place: int) -> int:
    """Step over a regular expression literal, ending it at a line break."""
    place += 1
    inside_a_class = False
    while place < len(text):
        character = text[place]
        if character == "\\":
            place += 2
        elif character == "\n":
            return place
        elif character == "[":
            inside_a_class = True
            place += 1
        elif character == "]":
            inside_a_class = False
            place += 1
        elif character == "/" and not inside_a_class:
            return place + 1
        else:
            place += 1
    return place


def marked_comments(
    text: str,
    quotes: str,
    line_markers: tuple[str, ...],
    block: tuple[str, str],
    patterns: bool,
) -> list[int]:
    """Find the comments in a language that marks them with fixed characters.

    Args:
        text: The file content.
        quotes: Every character that opens a string.
        line_markers: Every marker running a comment to the end of the line.
        block: The opening and closing markers of a block comment.
        patterns: Whether a slash can open a regular expression literal.

    Returns:
        The lines a comment starts on, sorted and without repeats.
    """
    places: list[int] = []
    place = 0
    while place < len(text):
        character = text[place]
        if character in quotes:
            place = _past_quoted(text, place)
        elif any(text.startswith(marker, place) for marker in line_markers):
            places.append(place)
            place = _past_line(text, place)
        elif text.startswith(block[0], place):
            places.append(place)
            place = _past_block(text, place, block[1])
        elif patterns and character == "/" and _opens_a_pattern(text, place):
            place = _past_pattern(text, place)
        else:
            place += 1
    return _lines_of(text, places)


def hcl_comments(text: str) -> list[int]:
    """Find the comments in an OpenTofu or Terraform file.

    Args:
        text: The file content.

    Returns:
        The lines a comment starts on.
    """
    return marked_comments(text, '"', ("#", "//"), ("/*", "*/"), False)


def javascript_comments(text: str) -> list[int]:
    """Find the comments in a JavaScript file.

    Args:
        text: The file content.

    Returns:
        The lines a comment starts on.
    """
    return marked_comments(text, "\"'`", ("//",), ("/*", "*/"), True)


def python_comments(text: str) -> list[int]:
    """Find the comments and docstrings in a Python file.

    A docstring is the first statement of a module, class or function when it
    is a bare string constant, which is prose beside code exactly as a comment
    is.

    Args:
        text: The file content.

    Returns:
        The lines a comment or docstring starts on.
    """
    places = [
        token.start[0]
        for token in tokenize.generate_tokens(io.StringIO(text).readline)
        if token.type == tokenize.COMMENT
    ]
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, DEFINITION_NODES) or not node.body:
            continue
        opening = node.body[0]
        if isinstance(opening, ast.Expr) and isinstance(opening.value, ast.Constant):
            if isinstance(opening.value.value, str):
                places.append(opening.lineno)
    return sorted(set(places))


def yaml_comments(text: str) -> list[int]:
    """Find the comments in a YAML file.

    The scanner reports the span of every token, so anything left over that is
    not whitespace is a comment.

    Args:
        text: The file content.

    Returns:
        The lines a comment starts on.
    """
    covered = bytearray(len(text))
    for token in yaml.scan(text):
        for place in range(token.start_mark.index, token.end_mark.index):
            covered[place] = 1
    return _lines_of(
        text,
        [place for place, seen in enumerate(covered) if not seen and not text[place].isspace()],
    )


GENERATED_FILES = (".terraform.lock.hcl",)

READERS: dict[str, Callable[[str], list[int]]] = {
    ".cjs": javascript_comments,
    ".hcl": hcl_comments,
    ".jsx": javascript_comments,
    ".js": javascript_comments,
    ".mjs": javascript_comments,
    ".py": python_comments,
    ".tf": hcl_comments,
    ".tfvars": hcl_comments,
    ".yaml": yaml_comments,
    ".yml": yaml_comments,
}


def reader_for(path: str) -> Callable[[str], list[int]] | None:
    """Choose the reader for a file, by its suffix.

    A generated file is nobody's source, so no reader speaks for it either:
    a finding against a lock file is answerable by nobody.

    Args:
        path: The file path.

    Returns:
        The reader, or None when no reader speaks for that file.
    """
    if os.path.basename(path) in GENERATED_FILES:
        return None
    return READERS.get(os.path.splitext(path)[1])


def comments_in(path: str, content: str) -> list[Finding]:
    """Find every comment and docstring in one file.

    Args:
        path: The file path, which chooses the reader.
        content: The file content.

    Returns:
        A finding for each line carrying a comment, empty when no reader
        speaks the language.

    Raises:
        Unreadable: The reader could not parse the file.
    """
    reader = reader_for(path)
    if reader is None:
        return []
    try:
        lines = reader(content)
    except (SyntaxError, ValueError, tokenize.TokenError, yaml.YAMLError) as error:
        raise Unreadable(str(error)) from error
    return [Finding(path, line) for line in lines]
