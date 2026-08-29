from __future__ import annotations

import ast
import bisect
import io
import os
import tokenize
from dataclasses import dataclass
from typing import TYPE_CHECKING

import tree_sitter_hcl
import tree_sitter_javascript
import tree_sitter_typescript
import yaml
from tree_sitter import Language, Parser

if TYPE_CHECKING:
    from collections.abc import Callable

DEFINITION_NODES = (ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Module)

COMMENT_NODE = "comment"

HCL = Language(tree_sitter_hcl.language())
JAVASCRIPT = Language(tree_sitter_javascript.language())
TYPESCRIPT = Language(tree_sitter_typescript.language_typescript())
TSX = Language(tree_sitter_typescript.language_tsx())


class Unreadable(Exception):
    pass


@dataclass(frozen=True)
class Finding:
    path: str
    line_number: int

    def __str__(self) -> str:
        return f"{self.path}:{self.line_number}"


def _lines_of(text: str, places: list[int]) -> list[int]:
    breaks = [place for place, character in enumerate(text) if character == "\n"]
    return sorted({bisect.bisect_right(breaks, place) + 1 for place in places})


def parsed_comments(text: str, language: Language) -> list[int]:
    places: list[int] = []
    pending = [Parser(language).parse(text.encode("utf-8")).root_node]
    while pending:
        node = pending.pop()
        if node.type == COMMENT_NODE:
            places.append(node.start_point[0] + 1)
        pending.extend(node.children)
    return sorted(set(places))


def hcl_comments(text: str) -> list[int]:
    return parsed_comments(text, HCL)


def javascript_comments(text: str) -> list[int]:
    return parsed_comments(text, JAVASCRIPT)


def typescript_comments(text: str) -> list[int]:
    return parsed_comments(text, TYPESCRIPT)


def tsx_comments(text: str) -> list[int]:
    return parsed_comments(text, TSX)


def python_comments(text: str) -> list[int]:
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
    ".cts": typescript_comments,
    ".hcl": hcl_comments,
    ".jsx": javascript_comments,
    ".js": javascript_comments,
    ".mjs": javascript_comments,
    ".mts": typescript_comments,
    ".py": python_comments,
    ".tf": hcl_comments,
    ".tfvars": hcl_comments,
    ".ts": typescript_comments,
    ".tsx": tsx_comments,
    ".yaml": yaml_comments,
    ".yml": yaml_comments,
}


def reader_for(path: str) -> Callable[[str], list[int]] | None:
    if os.path.basename(path) in GENERATED_FILES:
        return None
    return READERS.get(os.path.splitext(path)[1])


def comments_in(path: str, content: str) -> list[Finding]:
    reader = reader_for(path)
    if reader is None:
        return []
    try:
        lines = reader(content)
    except (SyntaxError, ValueError, tokenize.TokenError, yaml.YAMLError) as error:
        raise Unreadable(str(error)) from error
    return [Finding(path, line) for line in lines]
