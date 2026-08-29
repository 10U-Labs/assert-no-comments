from __future__ import annotations

import io
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from assert_no_comments.cli import main

if TYPE_CHECKING:
    from collections.abc import Callable


def read_sample(directory: Path, name: str) -> str:
    return (directory / "samples" / f"{name}.txt").read_text(encoding="utf-8")


SOURCE = "src/counting.py"
COMPONENT = "src/App.tsx"
WORKFLOW = ".github/workflows/release.yml"
VENDORED = "src/www/spa/vendor/leaflet.js"
NOTES = "src/notes.md"

CLEAN_PROJECT = {
    SOURCE: "project/clean_python",
    WORKFLOW: "project/clean_workflow",
    VENDORED: "project/vendored_javascript",
    NOTES: "project/prose",
}

PROJECT = {**CLEAN_PROJECT, SOURCE: "project/commented_python"}

EXCLUDE_VENDORED = "src/www/spa/vendor/*"

FULL_RUN = ["src", ".github/workflows", "--exclude", EXCLUDE_VENDORED]


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end tests")


@pytest.fixture
def run_cli() -> Callable[[list[str]], tuple[int, str, str]]:
    def runner(args: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = 0
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                main(args)
            except SystemExit as exit_request:
                exit_code = int(exit_request.code) if exit_request.code is not None else 0
        return exit_code, stdout.getvalue(), stderr.getvalue()

    return runner


@pytest.fixture
def run_cli_subprocess() -> Callable[[list[str]], tuple[int, str, str]]:
    def runner(args: list[str]) -> tuple[int, str, str]:
        result = subprocess.run(
            [sys.executable, "-m", "assert_no_comments", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr

    return runner


@pytest.fixture
def write_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Callable[[dict[str, str]], Path]:
    def builder(files: dict[str, str]) -> Path:
        for relative, name in files.items():
            path = tmp_path / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(read_sample(request.path.parent, name), encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        return tmp_path

    return builder
