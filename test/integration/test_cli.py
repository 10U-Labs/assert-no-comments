from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path
from test.conftest import (
    CLEAN_PROJECT,
    COMPONENT,
    EXCLUDE_VENDORED,
    FULL_RUN,
    NOTES,
    PROJECT,
    SOURCE,
    VENDORED,
    WORKFLOW,
)
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from assert_no_comments.cli import (
    EXIT_ERROR,
    EXIT_FINDINGS,
    EXIT_SUCCESS,
    MESSAGE,
    ScanResult,
    _expand,
    _is_glob_pattern,
    _read,
    _report,
    _walk_source_files,
    collect,
    create_parser,
    output_findings,
    parse_patterns,
    read_comments,
    should_skip,
)
from assert_no_comments.scanner import HCL, Finding, Unreadable, comments_in, parsed_comments

if TYPE_CHECKING:
    from collections.abc import Callable

    RunCli = Callable[[list[str]], tuple[int, str, str]]
    Sample = Callable[[str], str]
    WriteTree = Callable[[dict[str, str]], Path]


def _lines(tmp_path: Path, name: str, content: str) -> list[int]:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return [found.line_number for found in comments_in(str(path), path.read_text(encoding="utf-8"))]


def _settings(**overrides: bool) -> argparse.Namespace:
    chosen = {"quiet": False, "count": False, "verbose": False, "annotate": False}
    chosen.update(overrides)
    return create_parser().parse_args(["src", *[f"--{k}" for k, v in chosen.items() if v]])


@pytest.mark.integration
class TestPythonFilesOnDisk:
    def test_reports_a_comment(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.py", "# why\nx = 1\n") == [1]

    def test_reports_a_trailing_comment(self, tmp_path: Path, sample: Sample) -> None:
        assert _lines(tmp_path, "a.py", sample("commented_python")) == [2]

    def test_reports_a_docstring(self, tmp_path: Path, sample: Sample) -> None:
        assert _lines(tmp_path, "a.py", sample("documented_python")) == [2]

    def test_reports_a_module_docstring(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.py", '"""Why."""\nx = 1\n') == [1]

    def test_reports_a_class_docstring(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.py", 'class C:\n    """Why."""\n\n    x = 1\n') == [2]

    def test_reports_an_async_function_docstring(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.py", 'async def f():\n    """Why."""\n    return 1\n') == [2]

    def test_leaves_a_hash_in_a_string_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.py", 'x = "# not a comment"\n') == []

    def test_leaves_a_bare_number_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.py", "def f():\n    1\n") == []

    def test_leaves_an_assignment_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.py", "x = 1\n") == []

    def test_leaves_an_empty_file_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.py", "") == []

    def test_a_file_that_will_not_parse_is_unreadable(
        self, tmp_path: Path, sample: Sample
    ) -> None:
        with pytest.raises(Unreadable):
            _lines(tmp_path, "a.py", sample("broken_python"))


@pytest.mark.integration
class TestYamlFilesOnDisk:
    def test_reports_a_comment(self, tmp_path: Path, sample: Sample) -> None:
        assert _lines(tmp_path, "a.yml", sample("commented_workflow")) == [3]

    def test_reads_the_yaml_suffix_too(self, tmp_path: Path, sample: Sample) -> None:
        assert _lines(tmp_path, "a.yaml", sample("commented_workflow")) == [3]

    def test_leaves_a_hash_in_a_block_scalar_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.yml", '---\nrun: >-\n  echo "# nope"\n') == []

    def test_leaves_a_hash_in_a_quoted_scalar_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.yml", '---\nname: "a # b"\n') == []

    def test_a_file_that_will_not_parse_is_unreadable(self, tmp_path: Path) -> None:
        with pytest.raises(Unreadable):
            _lines(tmp_path, "a.yml", '"unclosed\n')


@pytest.mark.integration
class TestOpenTofuFilesOnDisk:
    def test_reports_a_hash_comment(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.tf", '# why\nresource "a" "b" {}\n') == [1]

    def test_reports_a_double_slash_comment(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.tf", 'resource "a" "b" {}\n// why\n') == [2]

    def test_reports_a_block_comment(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.tf", "locals {\n  /* why\n     more */\n}\n") == [2]

    def test_reads_the_tfvars_suffix_too(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.tfvars", "# why\nbucket = 1\n") == [1]

    def test_reads_the_hcl_suffix_too(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.hcl", "# why\nbucket = 1\n") == [1]

    def test_leaves_a_hash_in_a_string_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.tf", 'bucket = "a#b"\n') == []

    def test_leaves_a_hash_in_a_heredoc_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.tf", "policy = <<EOT\n# not a comment\nEOT\n") == []

    def test_a_file_that_will_not_parse_still_reports_what_it_can(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.tf", '# why\nresource "a" {\n') == [1]


@pytest.mark.integration
class TestJavascriptFilesOnDisk:
    def test_reports_a_comment(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.js", "const a = 1;\n// why\n") == [2]

    def test_reports_a_block_comment(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.js", "const a = 1;\n/* why\n   more */\n") == [2]

    def test_reads_the_mjs_suffix_too(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.mjs", "// why") == [1]

    def test_reads_the_cjs_suffix_too(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.cjs", "// why") == [1]

    def test_reads_the_jsx_suffix_too(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.jsx", "// why") == [1]

    def test_leaves_a_url_in_a_string_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.js", 'const a = "https://example.com";\n') == []

    def test_leaves_a_url_in_a_template_literal_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.js", "const a = `https://${host}`;\n") == []

    def test_leaves_a_double_slash_in_a_pattern_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.js", "const a = /https:\\/\\/x/;\n") == []

    def test_a_slash_in_a_character_class_does_not_end_a_pattern(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.js", "const a = /[a-z/]+/;\n") == []

    def test_reports_a_comment_after_a_pattern(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.js", "const a = /[a-z/]+/; // why\n") == [1]

    def test_reports_a_comment_after_a_division(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.js", "const a = b / c; // why\n") == [1]

    def test_reports_a_comment_after_a_closing_element(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.jsx", "const El = (\n  <div>a</div> // why\n);\n") == [2]

    def test_reports_a_comment_after_a_self_closing_element(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.jsx", "const El = <Foo prop={x} />; /* why */\n") == [1]

    def test_reports_a_comment_braced_inside_an_element(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.jsx", "const El = <div>\n  {/* why */}\n</div>;\n") == [2]

    def test_leaves_markers_in_the_text_of_an_element_alone(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.jsx", "const El = <div>a // not a comment</div>;\n") == []


@pytest.mark.integration
class TestTypescriptFilesOnDisk:
    def test_reports_a_comment(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.ts", "const a: string = 'x'; // why\n") == [1]

    def test_reports_a_documentation_block(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.ts", "interface A {\n  /** why */\n  b: string;\n}\n") == [2]

    def test_reads_a_declaration_file(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.d.ts", '/// <reference types="vite/client" />\n') == [1]

    def test_reads_the_mts_suffix_too(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.mts", "// why") == [1]

    def test_reads_the_cts_suffix_too(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.cts", "// why") == [1]

    def test_a_type_assertion_does_not_hide_the_comment_after_it(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "a.ts", "const a = <string>y;\n// why\n") == [2]


@pytest.mark.integration
class TestTsxFilesOnDisk:
    def test_reports_every_form_a_comment_takes(
        self, tmp_path: Path, sample: Sample
    ) -> None:
        assert _lines(tmp_path, "App.tsx", sample("commented_tsx")) == [3, 5, 8]

    def test_a_file_with_no_comment_in_it_reports_nothing(
        self, tmp_path: Path, sample: Sample
    ) -> None:
        assert _lines(tmp_path, "App.tsx", sample("clean_tsx")) == []

    def test_an_element_does_not_hide_the_comment_after_it(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "App.tsx", "const a = <div />;\n// why\n") == [2]


@pytest.mark.integration
class TestFilesNoReaderSpeaks:
    def test_a_markdown_file_reports_nothing(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "notes.md", "# A heading\n") == []

    def test_a_lock_file_reports_nothing(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, ".terraform.lock.hcl", "# generated\n") == []

    def test_a_file_with_no_suffix_reports_nothing(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "Makefile", "# why\nall:\n") == []


@pytest.mark.integration
class TestParsedComments:
    def test_reads_a_grammar_named_directly(self, tmp_path: Path) -> None:
        (tmp_path / "a.tf").write_text("# why\nbucket = 1\n", encoding="utf-8")
        content = (tmp_path / "a.tf").read_text(encoding="utf-8")
        assert parsed_comments(content, HCL) == [1]

    def test_reports_one_line_once(self, tmp_path: Path) -> None:
        assert _lines(tmp_path, "b.js", "/* a */ /* b */\n") == [1]


@pytest.mark.integration
class TestCollectingFiles:
    def test_a_directory_names_what_is_under_it(self, write_tree: WriteTree) -> None:
        write_tree(CLEAN_PROJECT)
        assert collect(["src"], [EXCLUDE_VENDORED]) == ([str(Path(SOURCE))], [])

    def test_a_glob_names_the_files_it_matches(self, write_tree: WriteTree) -> None:
        write_tree(CLEAN_PROJECT)
        assert collect(["src/*.py"], [])[0] == [str(Path(SOURCE))]

    def test_a_glob_reads_into_a_directory_it_matches(self, write_tree: WriteTree) -> None:
        write_tree(CLEAN_PROJECT)
        assert str(Path(SOURCE)) in collect(["sr*"], [EXCLUDE_VENDORED])[0]

    def test_a_glob_matching_nothing_is_missing(self, write_tree: WriteTree) -> None:
        write_tree(CLEAN_PROJECT)
        assert collect(["src/*.rs"], [])[1] == ["src/*.rs"]

    def test_a_dangling_link_names_nothing(self, write_tree: WriteTree) -> None:
        root = write_tree(CLEAN_PROJECT)
        (root / "link.py").symlink_to(root / "absent.py")
        assert collect(["*.py"], [])[0] == []

    def test_a_file_named_twice_is_read_once(self, write_tree: WriteTree) -> None:
        write_tree(CLEAN_PROJECT)
        assert collect(["src", SOURCE], [EXCLUDE_VENDORED])[0] == [str(Path(SOURCE))]

    def test_a_markdown_file_named_directly_is_left_out(self, write_tree: WriteTree) -> None:
        write_tree(CLEAN_PROJECT)
        assert collect([NOTES], [])[0] == []

    def test_a_missing_path_is_reported_back(self, write_tree: WriteTree) -> None:
        write_tree(CLEAN_PROJECT)
        assert collect(["absent"], []) == ([], ["absent"])

    def test_a_named_file_expands_to_itself(self, write_tree: WriteTree) -> None:
        write_tree(CLEAN_PROJECT)
        assert _expand(SOURCE) == ([SOURCE], True)

    def test_a_hidden_directory_is_read(self, write_tree: WriteTree) -> None:
        write_tree(CLEAN_PROJECT)
        assert _walk_source_files(".github") == [str(Path(WORKFLOW))]

    def test_a_cache_directory_is_left_alone(self, write_tree: WriteTree) -> None:
        root = write_tree(CLEAN_PROJECT)
        (root / "src" / "__pycache__").mkdir()
        (root / "src" / "__pycache__" / "cached.py").write_text("# why\n", encoding="utf-8")
        assert "cached.py" not in str(_walk_source_files("src"))

    def test_a_glob_is_told_from_a_path(self) -> None:
        assert _is_glob_pattern("src/*.py")

    def test_a_plain_path_is_not_a_glob(self) -> None:
        assert not _is_glob_pattern(SOURCE)

    def test_an_excluded_file_is_left_out(self, write_tree: WriteTree) -> None:
        write_tree(CLEAN_PROJECT)
        assert str(Path(VENDORED)) not in collect(["src"], [EXCLUDE_VENDORED])[0]

    def test_an_exclude_matching_a_basename_is_honoured(self) -> None:
        assert should_skip(VENDORED, ["leaflet.js"])

    def test_an_unrelated_exclude_leaves_the_file_in(self) -> None:
        assert not should_skip(SOURCE, [EXCLUDE_VENDORED])

    def test_no_exclude_leaves_every_file_in(self) -> None:
        assert not should_skip(SOURCE, parse_patterns(None))

    def test_a_blank_exclude_leaves_every_file_in(self) -> None:
        assert parse_patterns("") == []

    def test_a_spaced_exclude_list_reads_the_same(self) -> None:
        assert parse_patterns(" a/* , b/* ") == ["a/*", "b/*"]

    def test_a_trailing_comma_asks_for_nothing_extra(self) -> None:
        assert parse_patterns("a/*,,") == ["a/*"]


@pytest.mark.integration
class TestReadingFiles:
    def test_reads_the_content(self, write_tree: WriteTree, sample: Sample) -> None:
        write_tree(PROJECT)
        assert _read(SOURCE, ScanResult()) == sample("commented_python")

    def test_a_missing_file_reads_as_nothing(self, write_tree: WriteTree) -> None:
        write_tree(PROJECT)
        assert _read("absent.py", ScanResult()) is None

    def test_a_missing_file_records_an_error(self, write_tree: WriteTree) -> None:
        write_tree(PROJECT)
        result = ScanResult()
        _read("absent.py", result)
        assert result.had_error

    def test_a_file_that_is_not_utf8_records_an_error(self, write_tree: WriteTree) -> None:
        root = write_tree(PROJECT)
        (root / "binary.py").write_bytes(b"\xff\xfe\x00")
        result = ScanResult()
        _read("binary.py", result)
        assert result.had_error

    def test_collects_the_findings(self, write_tree: WriteTree) -> None:
        write_tree(PROJECT)
        assert read_comments([SOURCE], ScanResult()) == [Finding(SOURCE, 2)]

    def test_counts_the_files_it_read(self, write_tree: WriteTree) -> None:
        write_tree(PROJECT)
        result = ScanResult()
        read_comments([SOURCE], result)
        assert result.files_scanned == 1

    def test_a_file_that_will_not_open_is_not_counted(self, write_tree: WriteTree) -> None:
        write_tree(PROJECT)
        result = ScanResult()
        read_comments(["absent.py"], result)
        assert result.files_scanned == 0

    def test_a_file_that_will_not_parse_records_an_error(self, write_tree: WriteTree) -> None:
        write_tree({**PROJECT, "src/broken.py": "broken_python"})
        result = ScanResult()
        read_comments(["src/broken.py"], result)
        assert result.had_error

    def test_a_file_that_will_not_parse_is_not_counted(self, write_tree: WriteTree) -> None:
        write_tree({**PROJECT, "src/broken.py": "broken_python"})
        result = ScanResult()
        read_comments(["src/broken.py"], result)
        assert result.files_scanned == 0

    def test_verbose_names_each_file(
        self, write_tree: WriteTree, capsys: pytest.CaptureFixture[str]
    ) -> None:
        write_tree(PROJECT)
        read_comments([SOURCE], ScanResult(), verbose=True)
        assert f"Reading: {SOURCE}" in capsys.readouterr().out


@pytest.mark.integration
class TestReportingFindings:
    def test_prints_the_path_the_line_and_why(self, capsys: pytest.CaptureFixture[str]) -> None:
        output_findings([Finding(SOURCE, 2)])
        assert capsys.readouterr().out == f"{SOURCE}:2: {MESSAGE}\n"

    def test_counting_prints_only_the_number(self, capsys: pytest.CaptureFixture[str]) -> None:
        output_findings([Finding(SOURCE, 2)], count_mode=True)
        assert capsys.readouterr().out == "1\n"

    def test_annotating_prints_a_workflow_command(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output_findings([Finding(SOURCE, 2)], annotate=True)
        assert f"::error file={SOURCE},line=2::" in capsys.readouterr().out

    def test_a_clean_run_prints_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        output_findings([])
        assert capsys.readouterr().out == ""

    def test_quiet_prints_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        _report(ScanResult(findings=[Finding(SOURCE, 2)]), _settings(quiet=True))
        assert capsys.readouterr().out == ""

    def test_verbose_counts_the_files(self, capsys: pytest.CaptureFixture[str]) -> None:
        _report(ScanResult(files_scanned=4), _settings(verbose=True))
        assert "Files scanned: 4" in capsys.readouterr().out

    def test_verbose_counts_the_findings(self, capsys: pytest.CaptureFixture[str]) -> None:
        _report(ScanResult(findings=[Finding(SOURCE, 2)]), _settings(verbose=True))
        assert "Findings: 1" in capsys.readouterr().out

    def test_verbose_says_when_something_would_not_read(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _report(ScanResult(had_error=True), _settings(verbose=True))
        assert "Errors occurred during scanning." in capsys.readouterr().out

    def test_counting_through_report(self, capsys: pytest.CaptureFixture[str]) -> None:
        _report(ScanResult(findings=[Finding(SOURCE, 2)]), _settings(count=True))
        assert capsys.readouterr().out == "1\n"


@pytest.mark.integration
class TestTheCommandOverATree:
    def test_a_clean_tree_succeeds(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CLEAN_PROJECT)
        assert run_cli(FULL_RUN)[0] == EXIT_SUCCESS

    def test_a_commented_tree_fails(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(PROJECT)
        assert run_cli(FULL_RUN)[0] == EXIT_FINDINGS

    def test_names_the_commented_file(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(PROJECT)
        assert SOURCE in run_cli(FULL_RUN)[1]

    def test_reads_a_workflow_file(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree({**CLEAN_PROJECT, WORKFLOW: "commented_workflow"})
        assert WORKFLOW in run_cli(FULL_RUN)[1]

    def test_reads_a_typescript_component(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree({**CLEAN_PROJECT, COMPONENT: "commented_tsx"})
        assert COMPONENT in run_cli(FULL_RUN)[1]

    def test_counts_every_comment_a_component_carries(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree({**CLEAN_PROJECT, COMPONENT: "commented_tsx"})
        assert run_cli([*FULL_RUN, "--count"])[1] == "3\n"

    def test_leaves_the_vendored_javascript_alone(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert "leaflet" not in run_cli(FULL_RUN)[1]

    def test_reports_the_vendored_javascript_when_nothing_is_excluded(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN_PROJECT)
        assert "leaflet" in run_cli(["src"])[1]

    def test_leaves_a_markdown_file_alone(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(PROJECT)
        assert "notes.md" not in run_cli(FULL_RUN)[1]

    def test_fail_fast_stops_at_the_first_finding(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree({**PROJECT, WORKFLOW: "commented_workflow"})
        assert len(run_cli([*FULL_RUN, "--fail-fast"])[1].splitlines()) == 1

    def test_warn_only_succeeds_with_findings(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert run_cli([*FULL_RUN, "--warn-only"])[0] == EXIT_SUCCESS

    def test_quiet_prints_nothing(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(PROJECT)
        assert run_cli([*FULL_RUN, "--quiet"])[1] == ""

    def test_counting_prints_only_the_number(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(PROJECT)
        assert run_cli([*FULL_RUN, "--count"])[1] == "1\n"

    def test_verbose_says_how_many_files_it_will_read(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN_PROJECT)
        assert "file(s)..." in run_cli([*FULL_RUN, "--verbose"])[1]

    def test_verbose_names_the_exclude_patterns(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN_PROJECT)
        assert EXCLUDE_VENDORED in run_cli([*FULL_RUN, "--verbose"])[1]

    def test_verbose_without_an_exclude_says_nothing_about_patterns(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN_PROJECT)
        assert "Excluding patterns" not in run_cli(["src", "--verbose"])[1]

    def test_annotating_prints_a_workflow_command(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert f"::error file={SOURCE}," in run_cli([*FULL_RUN, "--annotate"])[1]


@pytest.mark.integration
class TestTheCommandWhenATreeWillNotRead:
    def test_a_missing_tree_is_an_error(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CLEAN_PROJECT)
        assert run_cli(["absent"])[0] == EXIT_ERROR

    def test_a_missing_tree_is_named(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        write_tree(CLEAN_PROJECT)
        assert "Error: Path not found: absent" in run_cli(["absent"])[2]

    def test_a_missing_tree_beside_a_clean_one_is_still_an_error(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN_PROJECT)
        assert run_cli(["src", "absent", "--exclude", EXCLUDE_VENDORED])[0] == EXIT_ERROR

    def test_a_missing_tree_beside_findings_still_reports_them(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(PROJECT)
        assert SOURCE in run_cli(["src", "absent", "--exclude", EXCLUDE_VENDORED])[1]

    def test_a_broken_file_in_the_tree_is_an_error(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree({**CLEAN_PROJECT, "src/broken.py": "broken_python"})
        assert run_cli(FULL_RUN)[0] == EXIT_ERROR

    def test_the_output_modes_are_mutually_exclusive(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN_PROJECT)
        assert run_cli(["src", "--quiet", "--verbose"])[0] == EXIT_ERROR

    def test_the_behaviour_modes_are_mutually_exclusive(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        write_tree(CLEAN_PROJECT)
        assert run_cli(["src", "--fail-fast", "--warn-only"])[0] == EXIT_ERROR

    def test_annotating_is_off_unless_asked_for(self) -> None:
        assert create_parser().parse_args(["src"]).annotate is False

    def test_several_trees_are_read(self) -> None:
        assert create_parser().parse_args(["src", "test"]).trees == ["src", "test"]


@pytest.mark.integration
class TestRunningAsAModule:
    def test_calls_main(self) -> None:
        with patch("assert_no_comments.cli.main") as entry_point:
            sys.modules.pop("assert_no_comments.__main__", None)
            runpy.run_module("assert_no_comments", run_name="__main__")
            assert entry_point.called

    def test_calls_main_once(self) -> None:
        with patch("assert_no_comments.cli.main") as entry_point:
            sys.modules.pop("assert_no_comments.__main__", None)
            runpy.run_module("assert_no_comments", run_name="__main__")
            assert entry_point.call_count == 1
