from __future__ import annotations

import argparse
import fnmatch
import glob
import os
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .scanner import Finding, Unreadable, comments_in, reader_for

if TYPE_CHECKING:
    from collections.abc import Sequence

EXIT_SUCCESS = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

GLOB_CHARACTERS = ("*", "?", "[")

SKIPPED_DIRECTORIES = (".git", "__pycache__", "node_modules")

MESSAGE = "carries a comment or a docstring; delete it and let the code say what it does"


@dataclass
class ScanResult:
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    had_error: bool = False


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="assert-no-comments",
        description=(
            "Assert that nothing in the given trees carries a comment or a docstring. "
            "Prose beside code is never checked, so it stops being true and nothing says "
            "when, and the reader who believes it works from a program that no longer "
            "exists."
        ),
    )

    parser.add_argument(
        "trees",
        nargs="+",
        metavar="TREE",
        help=(
            "One or more file paths, directory paths, or glob patterns to read. "
            "Directories are read recursively, and a file whose suffix names no "
            "language this understands is left alone."
        ),
    )

    parser.add_argument(
        "--exclude",
        metavar="PATTERNS",
        help=(
            "Comma-separated glob patterns to leave out, such as "
            "'src/www/spa/vendor/*' for code somebody else wrote."
        ),
    )

    parser.add_argument(
        "--annotate",
        action="store_true",
        help=(
            "Print each finding as a GitHub Actions ::error annotation, so it lands on "
            "the line it names in the diff."
        ),
    )

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output. Exit code indicates success (0) or findings (1).",
    )
    output_group.add_argument(
        "--count",
        action="store_true",
        help="Output only the count of findings.",
    )
    output_group.add_argument(
        "--verbose",
        action="store_true",
        help="Show the files read, the findings and a summary.",
    )

    behavior_group = parser.add_mutually_exclusive_group()
    behavior_group.add_argument(
        "--fail-fast",
        action="store_true",
        help="Exit immediately after finding the first comment.",
    )
    behavior_group.add_argument(
        "--warn-only",
        action="store_true",
        help="Always exit with code 0, even if findings exist.",
    )

    return parser


def parse_patterns(patterns_str: str | None) -> list[str]:
    if not patterns_str:
        return []
    return [pattern.strip() for pattern in patterns_str.split(",") if pattern.strip()]


def _is_glob_pattern(path: str) -> bool:
    return any(character in path for character in GLOB_CHARACTERS)


def _walk_source_files(directory: str) -> list[str]:
    found: list[str] = []
    for root, directories, filenames in os.walk(directory):
        directories[:] = [name for name in directories if name not in SKIPPED_DIRECTORIES]
        found.extend(
            os.path.join(root, filename)
            for filename in filenames
            if reader_for(filename) is not None
        )
    return found


def _expand(path: str) -> tuple[list[str], bool]:
    if _is_glob_pattern(path):
        matched = glob.glob(path, recursive=True, include_hidden=True)
        found: list[str] = []
        for entry in matched:
            if os.path.isfile(entry):
                found.append(entry)
            elif os.path.isdir(entry):
                found.extend(_walk_source_files(entry))
        return (found, bool(matched))
    if os.path.isfile(path):
        return ([path], True)
    if os.path.isdir(path):
        return (_walk_source_files(path), True)
    return ([], False)


def should_skip(path: str, exclude_patterns: list[str]) -> bool:
    return any(
        fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern)
        for pattern in exclude_patterns
    )


def collect(paths: Sequence[str], exclude_patterns: list[str]) -> tuple[list[str], list[str]]:
    found: set[str] = set()
    missing: list[str] = []
    for path in paths:
        expanded, matched = _expand(path)
        if not matched:
            missing.append(path)
            continue
        for entry in expanded:
            normalised = os.path.normpath(entry)
            if reader_for(normalised) is not None and not should_skip(
                normalised, exclude_patterns
            ):
                found.add(normalised)
    return (sorted(found), missing)


def _read(path: str, result: ScanResult) -> str | None:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError) as error:
        print(f"Error reading {path}: {error}", file=sys.stderr)
        result.had_error = True
        return None


def read_comments(paths: Sequence[str], result: ScanResult, verbose: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        content = _read(path, result)
        if content is None:
            continue
        if verbose:
            print(f"Reading: {path}")
        try:
            findings.extend(comments_in(path, content))
        except Unreadable as error:
            print(f"Could not parse {path}: {error}", file=sys.stderr)
            result.had_error = True
            continue
        result.files_scanned += 1
    return findings


def output_findings(
    findings: list[Finding], count_mode: bool = False, annotate: bool = False
) -> None:
    if count_mode:
        print(len(findings))
        return
    for finding in findings:
        if annotate:
            print(
                f"::error file={finding.path},line={finding.line_number}::"
                f"{finding} {MESSAGE}"
            )
        else:
            print(f"{finding}: {MESSAGE}")


def determine_exit_code(result: ScanResult, warn_only: bool = False) -> int:
    if warn_only:
        return EXIT_SUCCESS
    if result.findings:
        return EXIT_FINDINGS
    if result.had_error:
        return EXIT_ERROR
    return EXIT_SUCCESS


def _report(result: ScanResult, args: argparse.Namespace) -> None:
    if args.quiet:
        return
    output_findings(result.findings, args.count, args.annotate)
    if args.verbose:
        print()
        print(f"Files scanned: {result.files_scanned}")
        print(f"Findings: {len(result.findings)}")
        if result.had_error:
            print("Errors occurred during scanning.")


def main(argv: Sequence[str] | None = None) -> None:
    args = create_parser().parse_args(argv)
    exclude_patterns = parse_patterns(args.exclude)
    result = ScanResult()

    paths, missing = collect(args.trees, exclude_patterns)
    for path in missing:
        print(f"Error: Path not found: {path}", file=sys.stderr)
    if not paths and missing:
        sys.exit(EXIT_ERROR)
    if missing:
        result.had_error = True

    if args.verbose:
        print(f"Reading {len(paths)} file(s)...")
        if exclude_patterns:
            print(f"Excluding patterns: {', '.join(exclude_patterns)}")
        print()

    findings = read_comments(paths, result, args.verbose)
    result.findings = findings[:1] if (args.fail_fast and findings) else findings

    _report(result, args)
    sys.exit(determine_exit_code(result, args.warn_only))
