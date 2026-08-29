from __future__ import annotations

from test.conftest import (
    CLEAN_PROJECT,
    COMPONENT,
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
    def test_a_clean_tree_succeeds(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(CLEAN_PROJECT)
        assert run_cli_subprocess(FULL_RUN)[0] == 0

    def test_a_commented_tree_fails(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert run_cli_subprocess(FULL_RUN)[0] == 1

    def test_names_the_commented_file(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert SOURCE in run_cli_subprocess(FULL_RUN)[1]

    def test_says_why_the_line_is_a_finding(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert "let the code say what it does" in run_cli_subprocess(FULL_RUN)[1]

    def test_annotates_the_line_for_the_diff(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert f"::error file={SOURCE},line=2::" in run_cli_subprocess([*FULL_RUN, "--annotate"])[1]

    def test_reads_a_workflow_file(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree({**CLEAN_PROJECT, WORKFLOW: "commented_workflow"})
        assert WORKFLOW in run_cli_subprocess(FULL_RUN)[1]

    def test_reads_a_typescript_component(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree({**CLEAN_PROJECT, COMPONENT: "commented_tsx"})
        assert COMPONENT in run_cli_subprocess(FULL_RUN)[1]

    def test_counts_every_comment_a_component_carries(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree({**CLEAN_PROJECT, COMPONENT: "commented_tsx"})
        assert run_cli_subprocess([*FULL_RUN, "--count"])[1] == "3\n"

    def test_leaves_the_vendored_javascript_alone(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert "leaflet" not in run_cli_subprocess(FULL_RUN)[1]

    def test_leaves_a_markdown_file_alone(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert "notes.md" not in run_cli_subprocess(FULL_RUN)[1]

    def test_warn_only_succeeds_with_findings(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert run_cli_subprocess([*FULL_RUN, "--warn-only"])[0] == 0

    def test_quiet_prints_nothing(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert run_cli_subprocess([*FULL_RUN, "--quiet"])[1] == ""

    def test_counting_prints_only_the_number(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert run_cli_subprocess([*FULL_RUN, "--count"])[1] == "1\n"

    def test_a_missing_tree_is_an_error(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(CLEAN_PROJECT)
        assert run_cli_subprocess(["absent"])[0] == 2

    def test_a_broken_file_is_an_error(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree({**CLEAN_PROJECT, "src/broken.py": "broken_python"})
        assert run_cli_subprocess(FULL_RUN)[0] == 2

    def test_a_broken_file_is_named(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree({**CLEAN_PROJECT, "src/broken.py": "broken_python"})
        assert "Could not parse src/broken.py" in run_cli_subprocess(FULL_RUN)[2]

    def test_verbose_summarises_the_run(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(CLEAN_PROJECT)
        assert "Files scanned: 2" in run_cli_subprocess([*FULL_RUN, "--verbose"])[1]

    def test_the_exclude_flag_is_honoured(
        self, write_tree: WriteTree, run_cli_subprocess: RunCli
    ) -> None:
        write_tree(CLEAN_PROJECT)
        assert EXCLUDE_VENDORED in run_cli_subprocess([*FULL_RUN, "--verbose"])[1]
