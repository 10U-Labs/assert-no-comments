"""Integration tests driving the CLI and the readers over real source trees."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path
from test.samples import (
    BROKEN_PYTHON,
    CLEAN_PROJECT,
    COMMENTED_PYTHON,
    COMMENTED_WORKFLOW,
    DOCUMENTED_PYTHON,
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
from assert_no_comments.scanner import Finding, Unreadable, comments_in, marked_comments

if TYPE_CHECKING:
    from collections.abc import Callable

    RunCli = Callable[[list[str]], tuple[int, str, str]]
    WriteTree = Callable[[dict[str, str]], Path]


def _lines(tmp_path: Path, name: str, content: str) -> list[int]:
    """Write one file, read it back, and name the lines carrying a comment."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return [found.line_number for found in comments_in(str(path), path.read_text(encoding="utf-8"))]


def _settings(**overrides: bool) -> argparse.Namespace:
    """Build the namespace _report reads, with the given flags turned on."""
    chosen = {"quiet": False, "count": False, "verbose": False, "annotate": False}
    chosen.update(overrides)
    return create_parser().parse_args(["src", *[f"--{k}" for k, v in chosen.items() if v]])


@pytest.mark.integration
class TestPythonFilesOnDisk:
    """Python files read from the file system."""

    def test_reports_a_comment(self, tmp_path: Path) -> None:
        """A comment in a file on disk is a finding."""
        assert _lines(tmp_path, "a.py", "# why\nx = 1\n") == [1]

    def test_reports_a_trailing_comment(self, tmp_path: Path) -> None:
        """A comment after code is a finding on the line it trails."""
        assert _lines(tmp_path, "a.py", COMMENTED_PYTHON) == [2]

    def test_reports_a_docstring(self, tmp_path: Path) -> None:
        """A docstring is prose beside code."""
        assert _lines(tmp_path, "a.py", DOCUMENTED_PYTHON) == [2]

    def test_reports_a_module_docstring(self, tmp_path: Path) -> None:
        """A module docstring is prose beside code."""
        assert _lines(tmp_path, "a.py", '"""Why."""\nx = 1\n') == [1]

    def test_reports_a_class_docstring(self, tmp_path: Path) -> None:
        """A class docstring is prose beside code."""
        assert _lines(tmp_path, "a.py", 'class C:\n    """Why."""\n\n    x = 1\n') == [2]

    def test_reports_an_async_function_docstring(self, tmp_path: Path) -> None:
        """An async function docstring is prose beside code."""
        assert _lines(tmp_path, "a.py", 'async def f():\n    """Why."""\n    return 1\n') == [2]

    def test_leaves_a_hash_in_a_string_alone(self, tmp_path: Path) -> None:
        """A hash the tokeniser reads as string content is not a comment."""
        assert _lines(tmp_path, "a.py", 'x = "# not a comment"\n') == []

    def test_leaves_a_bare_number_alone(self, tmp_path: Path) -> None:
        """A bare constant that is not a string is not a docstring."""
        assert _lines(tmp_path, "a.py", "def f():\n    1\n") == []

    def test_leaves_an_assignment_alone(self, tmp_path: Path) -> None:
        """An assignment opening a module is code, not prose."""
        assert _lines(tmp_path, "a.py", "x = 1\n") == []

    def test_leaves_an_empty_file_alone(self, tmp_path: Path) -> None:
        """An empty module has no body to read a docstring from."""
        assert _lines(tmp_path, "a.py", "") == []

    def test_a_file_that_will_not_parse_is_unreadable(self, tmp_path: Path) -> None:
        """A broken file raises rather than reporting nothing."""
        with pytest.raises(Unreadable):
            _lines(tmp_path, "a.py", BROKEN_PYTHON)


@pytest.mark.integration
class TestYamlFilesOnDisk:
    """YAML files read from the file system."""

    def test_reports_a_comment(self, tmp_path: Path) -> None:
        """Anything the scanner leaves uncovered is a comment."""
        assert _lines(tmp_path, "a.yml", COMMENTED_WORKFLOW) == [3]

    def test_reads_the_yaml_suffix_too(self, tmp_path: Path) -> None:
        """A .yaml file is YAML, as a .yml file is."""
        assert _lines(tmp_path, "a.yaml", COMMENTED_WORKFLOW) == [3]

    def test_leaves_a_hash_in_a_block_scalar_alone(self, tmp_path: Path) -> None:
        """A hash inside a block scalar is content."""
        assert _lines(tmp_path, "a.yml", '---\nrun: >-\n  echo "# nope"\n') == []

    def test_leaves_a_hash_in_a_quoted_scalar_alone(self, tmp_path: Path) -> None:
        """A hash inside a quoted scalar is content."""
        assert _lines(tmp_path, "a.yml", '---\nname: "a # b"\n') == []

    def test_a_file_that_will_not_parse_is_unreadable(self, tmp_path: Path) -> None:
        """A broken file raises rather than reporting nothing."""
        with pytest.raises(Unreadable):
            _lines(tmp_path, "a.yml", '"unclosed\n')


@pytest.mark.integration
class TestOpenTofuFilesOnDisk:
    """OpenTofu files read from the file system."""

    def test_reports_a_hash_comment(self, tmp_path: Path) -> None:
        """A hash runs a comment to the end of the line."""
        assert _lines(tmp_path, "a.tf", '# why\nresource "a" "b" {}\n') == [1]

    def test_reports_a_double_slash_comment(self, tmp_path: Path) -> None:
        """A double slash runs a comment to the end of the line."""
        assert _lines(tmp_path, "a.tf", 'resource "a" "b" {}\n// why\n') == [2]

    def test_reports_a_block_comment(self, tmp_path: Path) -> None:
        """A block comment is a finding on the line it opens."""
        assert _lines(tmp_path, "a.tf", "locals {\n  /* why\n     more */\n}\n") == [2]

    def test_reports_an_unclosed_block_comment(self, tmp_path: Path) -> None:
        """An unclosed block comment is reported where it opened."""
        assert _lines(tmp_path, "a.tf", "locals {\n  /* why\n") == [2]

    def test_reads_the_tfvars_suffix_too(self, tmp_path: Path) -> None:
        """A .tfvars file is HCL, as a .tf file is."""
        assert _lines(tmp_path, "a.tfvars", "# why\nbucket = 1\n") == [1]

    def test_leaves_a_hash_in_a_string_alone(self, tmp_path: Path) -> None:
        """A hash inside a quoted string is content."""
        assert _lines(tmp_path, "a.tf", 'bucket = "a#b"\n') == []

    def test_an_escaped_quote_does_not_end_a_string(self, tmp_path: Path) -> None:
        """A backslash escapes the quote that would have closed the string."""
        assert _lines(tmp_path, "a.tf", 'bucket = "a\\"#b"\n') == []

    def test_an_unclosed_string_swallows_the_rest(self, tmp_path: Path) -> None:
        """An unclosed string runs to the end, so nothing after it is read."""
        assert _lines(tmp_path, "a.tf", 'bucket = "a#b\n') == []


@pytest.mark.integration
class TestJavascriptFilesOnDisk:
    """JavaScript files read from the file system."""

    def test_reports_a_comment(self, tmp_path: Path) -> None:
        """A double slash runs a comment to the end of the line."""
        assert _lines(tmp_path, "a.js", "const a = 1;\n// why\n") == [2]

    def test_reads_the_mjs_suffix_too(self, tmp_path: Path) -> None:
        """An .mjs file is JavaScript, as a .js file is."""
        assert _lines(tmp_path, "a.mjs", "// why") == [1]

    def test_reads_the_cjs_suffix_too(self, tmp_path: Path) -> None:
        """A .cjs file is JavaScript, as a .js file is."""
        assert _lines(tmp_path, "a.cjs", "// why") == [1]

    def test_reads_the_jsx_suffix_too(self, tmp_path: Path) -> None:
        """A .jsx file is JavaScript, as a .js file is."""
        assert _lines(tmp_path, "a.jsx", "// why") == [1]

    def test_leaves_a_url_in_a_string_alone(self, tmp_path: Path) -> None:
        """A URL inside a string is content."""
        assert _lines(tmp_path, "a.js", 'const a = "https://example.com";\n') == []

    def test_leaves_a_url_in_a_template_literal_alone(self, tmp_path: Path) -> None:
        """A backtick opens a string like any other quote."""
        assert _lines(tmp_path, "a.js", "const a = `https://${host}`;\n") == []

    def test_a_slash_in_a_character_class_does_not_end_a_pattern(self, tmp_path: Path) -> None:
        """A slash between brackets is pattern content."""
        assert _lines(tmp_path, "a.js", "const a = /[a-z/]+/;\n") == []

    def test_a_pattern_after_return_is_not_division(self, tmp_path: Path) -> None:
        """A slash after return opens a pattern."""
        assert _lines(tmp_path, "a.js", "function f() {\n  return /a/;\n}\n") == []

    def test_a_pattern_opening_a_file_is_not_division(self, tmp_path: Path) -> None:
        """A slash with nothing before it opens a pattern."""
        assert _lines(tmp_path, "a.js", "/a/.test(b);\n") == []

    def test_an_escaped_slash_does_not_end_a_pattern(self, tmp_path: Path) -> None:
        """A backslash escapes the slash that would have closed the pattern."""
        assert _lines(tmp_path, "a.js", "const a = /a\\/b/;\n") == []

    def test_an_unclosed_pattern_swallows_the_rest(self, tmp_path: Path) -> None:
        """An unclosed pattern with no line break runs to the end."""
        assert _lines(tmp_path, "a.js", "const a = /abc") == []

    def test_a_line_break_ends_a_pattern(self, tmp_path: Path) -> None:
        """A pattern cannot span lines, so the next line is read as code."""
        assert _lines(tmp_path, "a.js", "const a = /abc\n// why\n") == [2]

    def test_a_division_is_not_a_pattern(self, tmp_path: Path) -> None:
        """A slash after a name divides."""
        assert _lines(tmp_path, "a.js", "const a = b / c;\n// why\n") == [2]


@pytest.mark.integration
class TestFilesNoReaderSpeaks:
    """Files whose suffix names no language."""

    def test_a_markdown_file_reports_nothing(self, tmp_path: Path) -> None:
        """Prose is the content of a .md file rather than a gloss on it."""
        assert _lines(tmp_path, "notes.md", "# A heading\n") == []

    def test_a_lock_file_reports_nothing(self, tmp_path: Path) -> None:
        """A file OpenTofu writes is nobody's source."""
        assert _lines(tmp_path, ".terraform.lock.hcl", "# generated\n") == []

    def test_a_file_with_no_suffix_reports_nothing(self, tmp_path: Path) -> None:
        """A name with no suffix names no language."""
        assert _lines(tmp_path, "Makefile", "# why\nall:\n") == []


@pytest.mark.integration
class TestMarkedComments:
    """The shared reader the marker languages are built from."""

    def test_reads_a_language_it_was_told_about(self, tmp_path: Path) -> None:
        """A marker set the readers do not use still works."""
        (tmp_path / "a.sql").write_text("a = 1\n-- why\n", encoding="utf-8")
        content = (tmp_path / "a.sql").read_text(encoding="utf-8")
        assert marked_comments(content, "'", ("--",), ("/*", "*/"), False) == [2]

    def test_reports_one_line_once(self, tmp_path: Path) -> None:
        """A line is a finding at most once, however many markers it holds."""
        (tmp_path / "b.sql").write_text("/* a */ /* b */\n", encoding="utf-8")
        content = (tmp_path / "b.sql").read_text(encoding="utf-8")
        assert marked_comments(content, "'", (), ("/*", "*/"), False) == [1]


@pytest.mark.integration
class TestCollectingFiles:
    """Turning arguments into the files to read."""

    def test_a_directory_names_what_is_under_it(self, write_tree: WriteTree) -> None:
        """A directory expands to its source files."""
        write_tree(CLEAN_PROJECT)
        assert collect(["src"], [EXCLUDE_VENDORED]) == ([str(Path(SOURCE))], [])

    def test_a_glob_names_the_files_it_matches(self, write_tree: WriteTree) -> None:
        """A pattern expands to the matching files."""
        write_tree(CLEAN_PROJECT)
        assert collect(["src/*.py"], [])[0] == [str(Path(SOURCE))]

    def test_a_glob_reads_into_a_directory_it_matches(self, write_tree: WriteTree) -> None:
        """A pattern matching a directory reads into it."""
        write_tree(CLEAN_PROJECT)
        assert str(Path(SOURCE)) in collect(["sr*"], [EXCLUDE_VENDORED])[0]

    def test_a_glob_matching_nothing_is_missing(self, write_tree: WriteTree) -> None:
        """A pattern nothing matches reports as unmatched."""
        write_tree(CLEAN_PROJECT)
        assert collect(["src/*.rs"], [])[1] == ["src/*.rs"]

    def test_a_dangling_link_names_nothing(self, write_tree: WriteTree) -> None:
        """A link to nothing is neither a file to read nor a directory to walk."""
        root = write_tree(CLEAN_PROJECT)
        (root / "link.py").symlink_to(root / "absent.py")
        assert collect(["*.py"], [])[0] == []

    def test_a_file_named_twice_is_read_once(self, write_tree: WriteTree) -> None:
        """Overlapping arguments do not duplicate a file."""
        write_tree(CLEAN_PROJECT)
        assert collect(["src", SOURCE], [EXCLUDE_VENDORED])[0] == [str(Path(SOURCE))]

    def test_a_markdown_file_named_directly_is_left_out(self, write_tree: WriteTree) -> None:
        """Naming a markdown file directly still reads nothing."""
        write_tree(CLEAN_PROJECT)
        assert collect([NOTES], [])[0] == []

    def test_a_missing_path_is_reported_back(self, write_tree: WriteTree) -> None:
        """A path that is not there is named."""
        write_tree(CLEAN_PROJECT)
        assert collect(["absent"], []) == ([], ["absent"])

    def test_a_named_file_expands_to_itself(self, write_tree: WriteTree) -> None:
        """A file path expands to that file."""
        write_tree(CLEAN_PROJECT)
        assert _expand(SOURCE) == ([SOURCE], True)

    def test_a_hidden_directory_is_read(self, write_tree: WriteTree) -> None:
        """Workflow files live under .github, so hidden is not skipped."""
        write_tree(CLEAN_PROJECT)
        assert _walk_source_files(".github") == [str(Path(WORKFLOW))]

    def test_a_cache_directory_is_left_alone(self, write_tree: WriteTree) -> None:
        """Compiled output is nobody's source."""
        root = write_tree(CLEAN_PROJECT)
        (root / "src" / "__pycache__").mkdir()
        (root / "src" / "__pycache__" / "cached.py").write_text("# why\n", encoding="utf-8")
        assert "cached.py" not in str(_walk_source_files("src"))

    def test_a_glob_is_told_from_a_path(self) -> None:
        """A star is a wildcard."""
        assert _is_glob_pattern("src/*.py")

    def test_a_plain_path_is_not_a_glob(self) -> None:
        """A path with no wildcard names one place."""
        assert not _is_glob_pattern(SOURCE)

    def test_an_excluded_file_is_left_out(self, write_tree: WriteTree) -> None:
        """A file matching an exclude pattern is not read."""
        write_tree(CLEAN_PROJECT)
        assert str(Path(VENDORED)) not in collect(["src"], [EXCLUDE_VENDORED])[0]

    def test_an_exclude_matching_a_basename_is_honoured(self) -> None:
        """A pattern naming the file alone matches wherever it sits."""
        assert should_skip(VENDORED, ["leaflet.js"])

    def test_an_unrelated_exclude_leaves_the_file_in(self) -> None:
        """A pattern naming something else leaves the file in."""
        assert not should_skip(SOURCE, [EXCLUDE_VENDORED])

    def test_no_exclude_leaves_every_file_in(self) -> None:
        """Without the flag every file stays in."""
        assert not should_skip(SOURCE, parse_patterns(None))

    def test_a_blank_exclude_leaves_every_file_in(self) -> None:
        """An empty value asks for nothing."""
        assert parse_patterns("") == []

    def test_a_spaced_exclude_list_reads_the_same(self) -> None:
        """A list written with spaces reads the same as one without."""
        assert parse_patterns(" a/* , b/* ") == ["a/*", "b/*"]

    def test_a_trailing_comma_asks_for_nothing_extra(self) -> None:
        """An empty entry is dropped."""
        assert parse_patterns("a/*,,") == ["a/*"]


@pytest.mark.integration
class TestReadingFiles:
    """Reading the collected files from disk."""

    def test_reads_the_content(self, write_tree: WriteTree) -> None:
        """A readable file comes back as text."""
        write_tree(PROJECT)
        assert _read(SOURCE, ScanResult()) == COMMENTED_PYTHON

    def test_a_missing_file_reads_as_nothing(self, write_tree: WriteTree) -> None:
        """A file that will not open reads as nothing."""
        write_tree(PROJECT)
        assert _read("absent.py", ScanResult()) is None

    def test_a_missing_file_records_an_error(self, write_tree: WriteTree) -> None:
        """A file that will not open is an error, not a clean run."""
        write_tree(PROJECT)
        result = ScanResult()
        _read("absent.py", result)
        assert result.had_error

    def test_a_file_that_is_not_utf8_records_an_error(self, write_tree: WriteTree) -> None:
        """Bytes that are not text are an error, not a clean run."""
        root = write_tree(PROJECT)
        (root / "binary.py").write_bytes(b"\xff\xfe\x00")
        result = ScanResult()
        _read("binary.py", result)
        assert result.had_error

    def test_collects_the_findings(self, write_tree: WriteTree) -> None:
        """A commented file yields a finding."""
        write_tree(PROJECT)
        assert read_comments([SOURCE], ScanResult()) == [Finding(SOURCE, 2)]

    def test_counts_the_files_it_read(self, write_tree: WriteTree) -> None:
        """Every file parsed counts towards the summary."""
        write_tree(PROJECT)
        result = ScanResult()
        read_comments([SOURCE], result)
        assert result.files_scanned == 1

    def test_a_file_that_will_not_open_is_not_counted(self, write_tree: WriteTree) -> None:
        """An unreadable file scans nothing."""
        write_tree(PROJECT)
        result = ScanResult()
        read_comments(["absent.py"], result)
        assert result.files_scanned == 0

    def test_a_file_that_will_not_parse_records_an_error(self, write_tree: WriteTree) -> None:
        """A broken file is an error, not a clean run."""
        write_tree({**PROJECT, "src/broken.py": BROKEN_PYTHON})
        result = ScanResult()
        read_comments(["src/broken.py"], result)
        assert result.had_error

    def test_a_file_that_will_not_parse_is_not_counted(self, write_tree: WriteTree) -> None:
        """A file nothing could read did not get scanned."""
        write_tree({**PROJECT, "src/broken.py": BROKEN_PYTHON})
        result = ScanResult()
        read_comments(["src/broken.py"], result)
        assert result.files_scanned == 0

    def test_verbose_names_each_file(
        self, write_tree: WriteTree, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verbose says what was read."""
        write_tree(PROJECT)
        read_comments([SOURCE], ScanResult(), verbose=True)
        assert f"Reading: {SOURCE}" in capsys.readouterr().out


@pytest.mark.integration
class TestReportingFindings:
    """Printing what the run found."""

    def test_prints_the_path_the_line_and_why(self, capsys: pytest.CaptureFixture[str]) -> None:
        """The default format is readable at a terminal."""
        output_findings([Finding(SOURCE, 2)])
        assert capsys.readouterr().out == f"{SOURCE}:2: {MESSAGE}\n"

    def test_counting_prints_only_the_number(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Counting says how many, not which."""
        output_findings([Finding(SOURCE, 2)], count_mode=True)
        assert capsys.readouterr().out == "1\n"

    def test_annotating_prints_a_workflow_command(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An annotation lands on the line it names in the diff."""
        output_findings([Finding(SOURCE, 2)], annotate=True)
        assert f"::error file={SOURCE},line=2::" in capsys.readouterr().out

    def test_a_clean_run_prints_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Nothing found is silent."""
        output_findings([])
        assert capsys.readouterr().out == ""

    def test_quiet_prints_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Quiet reports through the exit code alone."""
        _report(ScanResult(findings=[Finding(SOURCE, 2)]), _settings(quiet=True))
        assert capsys.readouterr().out == ""

    def test_verbose_counts_the_files(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verbose says how many files were read."""
        _report(ScanResult(files_scanned=4), _settings(verbose=True))
        assert "Files scanned: 4" in capsys.readouterr().out

    def test_verbose_counts_the_findings(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verbose says how many findings there were."""
        _report(ScanResult(findings=[Finding(SOURCE, 2)]), _settings(verbose=True))
        assert "Findings: 1" in capsys.readouterr().out

    def test_verbose_says_when_something_would_not_read(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verbose says the run hit an error."""
        _report(ScanResult(had_error=True), _settings(verbose=True))
        assert "Errors occurred during scanning." in capsys.readouterr().out

    def test_counting_through_report(self, capsys: pytest.CaptureFixture[str]) -> None:
        """The count mode reaches the printer."""
        _report(ScanResult(findings=[Finding(SOURCE, 2)]), _settings(count=True))
        assert capsys.readouterr().out == "1\n"


@pytest.mark.integration
class TestTheCommandOverATree:
    """The command run over a whole tree."""

    def test_a_clean_tree_succeeds(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        """Nothing found is success."""
        write_tree(CLEAN_PROJECT)
        assert run_cli(FULL_RUN)[0] == EXIT_SUCCESS

    def test_a_commented_tree_fails(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        """Something found fails the run."""
        write_tree(PROJECT)
        assert run_cli(FULL_RUN)[0] == EXIT_FINDINGS

    def test_names_the_commented_file(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        """The output names the file the comment sits in."""
        write_tree(PROJECT)
        assert SOURCE in run_cli(FULL_RUN)[1]

    def test_reads_a_workflow_file(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        """A comment in a workflow file is a finding too."""
        write_tree({**CLEAN_PROJECT, WORKFLOW: COMMENTED_WORKFLOW})
        assert WORKFLOW in run_cli(FULL_RUN)[1]

    def test_leaves_the_vendored_javascript_alone(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """An excluded tree is code somebody else wrote."""
        write_tree(PROJECT)
        assert "leaflet" not in run_cli(FULL_RUN)[1]

    def test_reports_the_vendored_javascript_when_nothing_is_excluded(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """Without the flag the vendored tree is read like any other."""
        write_tree(CLEAN_PROJECT)
        assert "leaflet" in run_cli(["src"])[1]

    def test_leaves_a_markdown_file_alone(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        """Prose is the content of a .md file rather than a gloss on it."""
        write_tree(PROJECT)
        assert "notes.md" not in run_cli(FULL_RUN)[1]

    def test_fail_fast_stops_at_the_first_finding(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """Fail-fast reports one finding however many there are."""
        write_tree({**PROJECT, WORKFLOW: COMMENTED_WORKFLOW})
        assert len(run_cli([*FULL_RUN, "--fail-fast"])[1].splitlines()) == 1

    def test_warn_only_succeeds_with_findings(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """Warn-only reports without failing."""
        write_tree(PROJECT)
        assert run_cli([*FULL_RUN, "--warn-only"])[0] == EXIT_SUCCESS

    def test_quiet_prints_nothing(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        """Quiet reports through the exit code alone."""
        write_tree(PROJECT)
        assert run_cli([*FULL_RUN, "--quiet"])[1] == ""

    def test_counting_prints_only_the_number(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        """Counting says how many, not which."""
        write_tree(PROJECT)
        assert run_cli([*FULL_RUN, "--count"])[1] == "1\n"

    def test_verbose_says_how_many_files_it_will_read(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """Verbose opens by saying how much there is to do."""
        write_tree(CLEAN_PROJECT)
        assert "file(s)..." in run_cli([*FULL_RUN, "--verbose"])[1]

    def test_verbose_names_the_exclude_patterns(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """Verbose says what was left out."""
        write_tree(CLEAN_PROJECT)
        assert EXCLUDE_VENDORED in run_cli([*FULL_RUN, "--verbose"])[1]

    def test_verbose_without_an_exclude_says_nothing_about_patterns(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """Nothing excluded means nothing to report about excluding."""
        write_tree(CLEAN_PROJECT)
        assert "Excluding patterns" not in run_cli(["src", "--verbose"])[1]

    def test_annotating_prints_a_workflow_command(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """An annotation lands on the line it names in the diff."""
        write_tree(PROJECT)
        assert f"::error file={SOURCE}," in run_cli([*FULL_RUN, "--annotate"])[1]


@pytest.mark.integration
class TestTheCommandWhenATreeWillNotRead:
    """The command run over something it cannot read."""

    def test_a_missing_tree_is_an_error(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        """A tree that is not there fails the run."""
        write_tree(CLEAN_PROJECT)
        assert run_cli(["absent"])[0] == EXIT_ERROR

    def test_a_missing_tree_is_named(self, write_tree: WriteTree, run_cli: RunCli) -> None:
        """The error says which path was not found."""
        write_tree(CLEAN_PROJECT)
        assert "Error: Path not found: absent" in run_cli(["absent"])[2]

    def test_a_missing_tree_beside_a_clean_one_is_still_an_error(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """One good tree does not excuse one that is not there."""
        write_tree(CLEAN_PROJECT)
        assert run_cli(["src", "absent", "--exclude", EXCLUDE_VENDORED])[0] == EXIT_ERROR

    def test_a_missing_tree_beside_findings_still_reports_them(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """The findings are what the run is for."""
        write_tree(PROJECT)
        assert SOURCE in run_cli(["src", "absent", "--exclude", EXCLUDE_VENDORED])[1]

    def test_a_broken_file_in_the_tree_is_an_error(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """A file nothing could parse fails the run."""
        write_tree({**CLEAN_PROJECT, "src/broken.py": BROKEN_PYTHON})
        assert run_cli(FULL_RUN)[0] == EXIT_ERROR

    def test_the_output_modes_are_mutually_exclusive(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """Quiet and verbose cannot both be asked for."""
        write_tree(CLEAN_PROJECT)
        assert run_cli(["src", "--quiet", "--verbose"])[0] == EXIT_ERROR

    def test_the_behaviour_modes_are_mutually_exclusive(
        self, write_tree: WriteTree, run_cli: RunCli
    ) -> None:
        """Fail-fast and warn-only cannot both be asked for."""
        write_tree(CLEAN_PROJECT)
        assert run_cli(["src", "--fail-fast", "--warn-only"])[0] == EXIT_ERROR

    def test_annotating_is_off_unless_asked_for(self) -> None:
        """Annotations are a GitHub Actions format, asked for rather than assumed."""
        assert create_parser().parse_args(["src"]).annotate is False

    def test_several_trees_are_read(self) -> None:
        """Positional arguments accumulate."""
        assert create_parser().parse_args(["src", "test"]).trees == ["src", "test"]


@pytest.mark.integration
class TestRunningAsAModule:
    """Running the package with python -m."""

    def test_calls_main(self) -> None:
        """The module entry point runs the CLI."""
        with patch("assert_no_comments.cli.main") as entry_point:
            sys.modules.pop("assert_no_comments.__main__", None)
            runpy.run_module("assert_no_comments", run_name="__main__")
            assert entry_point.called

    def test_calls_main_once(self) -> None:
        """The module entry point runs the CLI exactly once."""
        with patch("assert_no_comments.cli.main") as entry_point:
            sys.modules.pop("assert_no_comments.__main__", None)
            runpy.run_module("assert_no_comments", run_name="__main__")
            assert entry_point.call_count == 1
