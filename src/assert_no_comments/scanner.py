from __future__ import annotations

import ast
import bisect
import io
import os
import tokenize
from dataclasses import dataclass
from typing import TYPE_CHECKING

import tree_sitter_bash
import tree_sitter_c
import tree_sitter_cpp
import tree_sitter_hcl
import tree_sitter_javascript
import tree_sitter_systemverilog
import tree_sitter_typescript
import yaml
from tree_sitter import Language, Parser

if TYPE_CHECKING:
    from collections.abc import Callable

    from tree_sitter import Node

DEFINITION_NODES = (ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef, ast.Module)

COMMENT_NODES = frozenset({"block_comment", "comment", "one_line_comment"})

MACRO_BODY_NODES = frozenset({"macro_text", "preproc_arg"})

NAMESPACE_NODE = "namespace_definition"

NAMESPACE_END = b"// namespace"

SHEBANG = "#!"

FIRST_COLUMN_OF_FIRST_LINE = (1, 0)

BASH = Language(tree_sitter_bash.language())
C = Language(tree_sitter_c.language())
CPP = Language(tree_sitter_cpp.language())
HCL = Language(tree_sitter_hcl.language())
JAVASCRIPT = Language(tree_sitter_javascript.language())
SYSTEMVERILOG = Language(tree_sitter_systemverilog.language())
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


def _text_of(node: Node, source: bytes) -> bytes:
    return source[node.start_byte : node.end_byte]


def _spares_nothing(_comment: Node, _source: bytes) -> bool:
    return False


def closes_its_namespace(comment: Node, source: bytes) -> bool:
    definition = comment.prev_sibling
    if definition is None or definition.type != NAMESPACE_NODE:
        return False
    name = definition.child_by_field_name("name")
    ending = NAMESPACE_END if name is None else NAMESPACE_END + b" " + _text_of(name, source)
    same_row = definition.end_point[0] == comment.start_point[0]
    return same_row and _text_of(comment, source) == ending


def is_a_shebang(comment: Node, source: bytes) -> bool:
    return comment.start_byte == 0 and _text_of(comment, source).startswith(SHEBANG.encode())


def _is_a_python_shebang(token: tokenize.TokenInfo) -> bool:
    return token.start == FIRST_COLUMN_OF_FIRST_LINE and token.string.startswith(SHEBANG)


def parsed_comments(
    text: str,
    language: Language,
    *,
    spared: Callable[[Node, bytes], bool] = _spares_nothing,
) -> list[int]:
    source = text.encode("utf-8")
    places: list[int] = []
    pending = [Parser(language).parse(source).root_node]
    while pending:
        node = pending.pop()
        if node.type in MACRO_BODY_NODES:
            body = _text_of(node, source).decode("utf-8")
            places.extend(node.start_point[0] + line for line in parsed_comments(body, language))
        elif node.type in COMMENT_NODES and not spared(node, source):
            places.append(node.start_point[0] + 1)
        pending.extend(node.children)
    return sorted(set(places))


def c_comments(text: str) -> list[int]:
    return parsed_comments(text, C)


def cpp_comments(text: str) -> list[int]:
    return parsed_comments(text, CPP, spared=closes_its_namespace)


def hcl_comments(text: str) -> list[int]:
    return parsed_comments(text, HCL)


def javascript_comments(text: str) -> list[int]:
    return parsed_comments(text, JAVASCRIPT)


def typescript_comments(text: str) -> list[int]:
    return parsed_comments(text, TYPESCRIPT)


def tsx_comments(text: str) -> list[int]:
    return parsed_comments(text, TSX)


def shell_comments(text: str) -> list[int]:
    return parsed_comments(text, BASH, spared=is_a_shebang)


def systemverilog_comments(text: str) -> list[int]:
    return parsed_comments(text, SYSTEMVERILOG)


def python_comments(text: str) -> list[int]:
    places = [
        token.start[0]
        for token in tokenize.generate_tokens(io.StringIO(text).readline)
        if token.type == tokenize.COMMENT and not _is_a_python_shebang(token)
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
    ".C": cpp_comments,
    ".CPP": cpp_comments,
    ".H": cpp_comments,
    ".HPP": cpp_comments,
    ".bash": shell_comments,
    ".c": c_comments,
    ".c++": cpp_comments,
    ".cc": cpp_comments,
    ".cjs": javascript_comments,
    ".cp": cpp_comments,
    ".cpp": cpp_comments,
    ".cts": typescript_comments,
    ".cxx": cpp_comments,
    ".h": cpp_comments,
    ".h++": cpp_comments,
    ".hcl": hcl_comments,
    ".hh": cpp_comments,
    ".hp": cpp_comments,
    ".hpp": cpp_comments,
    ".hxx": cpp_comments,
    ".jsx": javascript_comments,
    ".js": javascript_comments,
    ".mjs": javascript_comments,
    ".mts": typescript_comments,
    ".py": python_comments,
    ".sh": shell_comments,
    ".sv": systemverilog_comments,
    ".svh": systemverilog_comments,
    ".tcc": cpp_comments,
    ".tf": hcl_comments,
    ".tfvars": hcl_comments,
    ".ts": typescript_comments,
    ".tsx": tsx_comments,
    ".v": systemverilog_comments,
    ".vh": systemverilog_comments,
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
