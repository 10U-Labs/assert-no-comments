"""End-to-end tests running the installed command the way a workflow step does."""

from __future__ import annotations

from test.samples import (
    BROKEN_PYTHON,
    CLEAN_PROJECT,
    COMMENTED_WORKFLOW,
    EXCLUDE_VENDORED,
    FULL_RUN,
    PROJECT,
    SOURCE,
    WORKFLOW,
)
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    RunCli = Callable[[list[str]], tuple[int, str, str]]
    WriteTree = Callable[[dict[str, str]], Path]


@pytest.mark.e2e
class TestTheCommandAsAStepRunsIt:
    """The command as a workflow step invokes it."""

    def test_a_clean_tree_succeeds(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """Nothing found is success."""
        write_tree(CLEAN_PROJECT)
        assert run_cli_subprocess(FULL_RUN)[0] == 0

    def test_a_commented_tree_fails(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """Something found fails the run."""
        write_tree(PROJECT)
        assert run_cli_subprocess(FULL_RUN)[0] == 1

    def test_names_the_commented_file(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """The output names the file the comment sits in."""
        write_tree(PROJECT)
        assert SOURCE in run_cli_subprocess(FULL_RUN)[1]

    def test_says_why_the_line_is_a_finding(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """The message says what to do about it."""
        write_tree(PROJECT)
        assert "let the code say what it does" in run_cli_subprocess(FULL_RUN)[1]

    def test_annotates_the_line_for_the_diff(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """An annotation lands on the line it names in the diff."""
        write_tree(PROJECT)
        assert f"::error file={SOURCE},line=2::" in run_cli_subprocess([*FULL_RUN, "--annotate"])[1]

    def test_reads_a_workflow_file(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """A comment in a workflow file is a finding too."""
        write_tree({**CLEAN_PROJECT, WORKFLOW: COMMENTED_WORKFLOW})
        assert WORKFLOW in run_cli_subprocess(FULL_RUN)[1]

    def test_leaves_the_vendored_javascript_alone(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """An excluded tree is code somebody else wrote."""
        write_tree(PROJECT)
        assert "leaflet" not in run_cli_subprocess(FULL_RUN)[1]

    def test_leaves_a_markdown_file_alone(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """Prose is the content of a .md file rather than a gloss on it."""
        write_tree(PROJECT)
        assert "notes.md" not in run_cli_subprocess(FULL_RUN)[1]

    def test_warn_only_succeeds_with_findings(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """Warn-only reports without failing."""
        write_tree(PROJECT)
        assert run_cli_subprocess([*FULL_RUN, "--warn-only"])[0] == 0

    def test_quiet_prints_nothing(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """Quiet reports through the exit code alone."""
        write_tree(PROJECT)
        assert run_cli_subprocess([*FULL_RUN, "--quiet"])[1] == ""

    def test_counting_prints_only_the_number(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """Counting says how many, not which."""
        write_tree(PROJECT)
        assert run_cli_subprocess([*FULL_RUN, "--count"])[1] == "1\n"

    def test_a_missing_tree_is_an_error(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """A tree that is not there fails the run."""
        write_tree(CLEAN_PROJECT)
        assert run_cli_subprocess(["absent"])[0] == 2

    def test_a_broken_file_is_an_error(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """A file nothing could parse fails the run."""
        write_tree({**CLEAN_PROJECT, "src/broken.py": BROKEN_PYTHON})
        assert run_cli_subprocess(FULL_RUN)[0] == 2

    def test_a_broken_file_is_named(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """The error says which file would not parse."""
        write_tree({**CLEAN_PROJECT, "src/broken.py": BROKEN_PYTHON})
        assert "Could not parse src/broken.py" in run_cli_subprocess(FULL_RUN)[2]

    def test_verbose_summarises_the_run(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """Verbose closes by saying how much it read."""
        write_tree(CLEAN_PROJECT)
        assert "Files scanned: 2" in run_cli_subprocess([*FULL_RUN, "--verbose"])[1]

    def test_the_exclude_flag_is_honoured(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        """A tree named by --exclude is not read."""
        write_tree(CLEAN_PROJECT)
        assert EXCLUDE_VENDORED in run_cli_subprocess([*FULL_RUN, "--verbose"])[1]
