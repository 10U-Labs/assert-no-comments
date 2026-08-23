"""Unit tests for the command-line interface."""

from __future__ import annotations

import argparse
import importlib
import sys
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
    determine_exit_code,
    main,
    output_findings,
    parse_patterns,
    read_comments,
    should_skip,
)
from assert_no_comments.scanner import Finding

if TYPE_CHECKING:
    from pathlib import Path

TREE = "kept"
CLEAN = "kept/clean.py"
SECOND = "kept/second.py"


def import_main() -> None:
    """Import the package entry point afresh, so that its call runs again."""
    sys.modules.pop("assert_no_comments.__main__", None)
    importlib.import_module("assert_no_comments.__main__")


def _namespace(**overrides: bool) -> argparse.Namespace:
    """Build the namespace _report reads, with the given flags turned on."""
    settings = {"quiet": False, "count": False, "verbose": False, "annotate": False}
    settings.update(overrides)
    return create_parser().parse_args(
        ["src", *[f"--{name}" for name, chosen in settings.items() if chosen]]
    )


@pytest.mark.unit
class TestCreateParser:
    """Building the argument parser."""

    def test_reads_one_tree(self) -> None:
        """A single positional argument is the tree to read."""
        assert create_parser().parse_args(["src"]).trees == ["src"]

    def test_reads_several_trees(self) -> None:
        """Positional arguments accumulate."""
        assert create_parser().parse_args(["src", "test"]).trees == ["src", "test"]

    def test_annotate_is_off_by_default(self) -> None:
        """Annotations are a GitHub Actions format, asked for rather than assumed."""
        assert create_parser().parse_args(["src"]).annotate is False

    def test_quiet_and_verbose_cannot_both_be_asked_for(self) -> None:
        """The output modes are mutually exclusive."""
        with pytest.raises(SystemExit):
            create_parser().parse_args(["src", "--quiet", "--verbose"])

    def test_fail_fast_and_warn_only_cannot_both_be_asked_for(self) -> None:
        """The behaviour modes are mutually exclusive."""
        with pytest.raises(SystemExit):
            create_parser().parse_args(["src", "--fail-fast", "--warn-only"])


@pytest.mark.unit
class TestParsePatterns:
    """Reading the comma-separated exclude list."""

    def test_nothing_given_is_no_patterns(self) -> None:
        """The flag is optional."""
        assert parse_patterns(None) == []

    def test_a_blank_string_is_no_patterns(self) -> None:
        """An empty value asks for nothing."""
        assert parse_patterns("") == []

    def test_one_pattern_is_read(self) -> None:
        """A single pattern needs no comma."""
        assert parse_patterns("vendor/*") == ["vendor/*"]

    def test_surrounding_spaces_are_dropped(self) -> None:
        """A list written with spaces reads the same as one without."""
        assert parse_patterns(" a/* , b/* ") == ["a/*", "b/*"]

    def test_an_empty_entry_is_dropped(self) -> None:
        """A trailing comma asks for nothing extra."""
        assert parse_patterns("a/*,,") == ["a/*"]


@pytest.mark.unit
class TestShouldSkip:
    """Matching a path against the exclude patterns."""

    def test_a_path_pattern_matches(self) -> None:
        """A pattern naming the directory excludes what is under it."""
        assert should_skip("src/vendor/leaflet.js", ["src/vendor/*"])

    def test_a_basename_pattern_matches(self) -> None:
        """A pattern naming the file alone matches wherever it sits."""
        assert should_skip("src/vendor/leaflet.js", ["leaflet.js"])

    def test_an_unrelated_pattern_does_not_match(self) -> None:
        """A pattern naming something else leaves the file in."""
        assert not should_skip("src/counting.py", ["src/vendor/*"])

    def test_no_patterns_skips_nothing(self) -> None:
        """Without the flag every file stays in."""
        assert not should_skip("src/counting.py", [])


@pytest.mark.unit
class TestIsGlobPattern:
    """Telling a glob from a plain path."""

    def test_a_star_makes_it_a_pattern(self) -> None:
        """A star is a wildcard."""
        assert _is_glob_pattern("src/*.py")

    def test_a_plain_path_is_not_a_pattern(self) -> None:
        """A path with no wildcard names one place."""
        assert not _is_glob_pattern("src/counting.py")


@pytest.mark.unit
class TestWalkSourceFiles:
    """Walking a directory for files a reader speaks the language of."""

    def test_finds_a_python_file(self, tmp_path: Path) -> None:
        """A .py file under the directory is found."""
        (tmp_path / "counting.py").write_text("x = 1\n", encoding="utf-8")
        assert _walk_source_files(str(tmp_path)) == [str(tmp_path / "counting.py")]

    def test_leaves_a_markdown_file_alone(self, tmp_path: Path) -> None:
        """A suffix naming no language is not collected."""
        (tmp_path / "notes.md").write_text("A heading\n", encoding="utf-8")
        assert not _walk_source_files(str(tmp_path))

    def test_reads_a_hidden_directory(self, tmp_path: Path) -> None:
        """Workflow files live under .github, so hidden is not skipped."""
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "release.yml").write_text("---\na: 1\n", encoding="utf-8")
        assert _walk_source_files(str(tmp_path)) == [str(workflows / "release.yml")]

    def test_leaves_a_cache_directory_alone(self, tmp_path: Path) -> None:
        """Compiled output is nobody's source."""
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "counting.py").write_text("x = 1\n", encoding="utf-8")
        assert not _walk_source_files(str(tmp_path))


@pytest.mark.unit
class TestExpand:
    """Turning one argument into the files it names."""

    def test_a_file_names_itself(self, tmp_path: Path) -> None:
        """A file path expands to that file."""
        source = tmp_path / "counting.py"
        source.write_text("x = 1\n", encoding="utf-8")
        assert _expand(str(source)) == ([str(source)], True)

    def test_a_directory_names_what_is_under_it(self, tmp_path: Path) -> None:
        """A directory expands to its source files."""
        (tmp_path / "counting.py").write_text("x = 1\n", encoding="utf-8")
        assert _expand(str(tmp_path)) == ([str(tmp_path / "counting.py")], True)

    def test_a_glob_names_the_files_it_matches(self, tmp_path: Path) -> None:
        """A pattern expands to the matching files."""
        (tmp_path / "counting.py").write_text("x = 1\n", encoding="utf-8")
        assert _expand(str(tmp_path / "*.py")) == ([str(tmp_path / "counting.py")], True)

    def test_a_glob_matching_a_directory_names_what_is_under_it(self, tmp_path: Path) -> None:
        """A pattern matching a directory reads into it."""
        package = tmp_path / "pkg"
        package.mkdir()
        (package / "counting.py").write_text("x = 1\n", encoding="utf-8")
        assert _expand(str(tmp_path / "p*")) == ([str(package / "counting.py")], True)

    def test_a_glob_matching_a_dangling_link_names_nothing(self, tmp_path: Path) -> None:
        """A link to nothing is neither a file to read nor a directory to walk."""
        (tmp_path / "counting.py").symlink_to(tmp_path / "absent.py")
        assert _expand(str(tmp_path / "*.py")) == ([], True)

    def test_a_glob_matching_nothing_names_nothing(self, tmp_path: Path) -> None:
        """A pattern nothing matches reports as unmatched."""
        assert _expand(str(tmp_path / "*.js")) == ([], False)

    def test_a_path_that_is_not_there_names_nothing(self, tmp_path: Path) -> None:
        """A missing path reports as unmatched."""
        assert _expand(str(tmp_path / "absent.py")) == ([], False)


@pytest.mark.unit
class TestCollect:
    """Expanding every argument into the files to read."""

    def test_names_the_files_to_read(self, tmp_path: Path) -> None:
        """A directory collects its source files."""
        (tmp_path / "counting.py").write_text("x = 1\n", encoding="utf-8")
        assert collect([str(tmp_path)], []) == ([str(tmp_path / "counting.py")], [])

    def test_names_the_paths_that_matched_nothing(self, tmp_path: Path) -> None:
        """A missing argument is reported back."""
        assert collect([str(tmp_path / "absent")], [])[1] == [str(tmp_path / "absent")]

    def test_an_excluded_file_is_left_out(self, tmp_path: Path) -> None:
        """A file matching an exclude pattern is not read."""
        (tmp_path / "counting.py").write_text("x = 1\n", encoding="utf-8")
        assert collect([str(tmp_path)], ["counting.py"]) == ([], [])

    def test_a_file_named_twice_is_read_once(self, tmp_path: Path) -> None:
        """Overlapping arguments do not duplicate a file."""
        source = tmp_path / "counting.py"
        source.write_text("x = 1\n", encoding="utf-8")
        assert collect([str(tmp_path), str(source)], []) == ([str(source)], [])

    def test_a_named_file_no_reader_speaks_is_left_out(self, tmp_path: Path) -> None:
        """Naming a markdown file directly still reads nothing."""
        notes = tmp_path / "notes.md"
        notes.write_text("A heading\n", encoding="utf-8")
        assert collect([str(notes)], []) == ([], [])


@pytest.mark.unit
class TestRead:
    """Reading one file from disk."""

    def test_returns_the_content(self, tmp_path: Path) -> None:
        """A readable file comes back as text."""
        source = tmp_path / "counting.py"
        source.write_text("x = 1\n", encoding="utf-8")
        assert _read(str(source), ScanResult()) == "x = 1\n"

    def test_a_missing_file_returns_nothing(self, tmp_path: Path) -> None:
        """A file that will not open reads as nothing."""
        assert _read(str(tmp_path / "absent.py"), ScanResult()) is None

    def test_a_missing_file_records_an_error(self, tmp_path: Path) -> None:
        """A file that will not open is an error, not a clean run."""
        result = ScanResult()
        _read(str(tmp_path / "absent.py"), result)
        assert result.had_error

    def test_a_file_that_is_not_utf8_records_an_error(self, tmp_path: Path) -> None:
        """Bytes that are not text are an error, not a clean run."""
        source = tmp_path / "counting.py"
        source.write_bytes(b"\xff\xfe\x00")
        result = ScanResult()
        _read(str(source), result)
        assert result.had_error


@pytest.mark.unit
class TestReadComments:
    """Reading every file and collecting what it carries."""

    def test_collects_the_findings(self, tmp_path: Path) -> None:
        """A commented file yields a finding."""
        source = tmp_path / "counting.py"
        source.write_text("x = 1\n# why\n", encoding="utf-8")
        assert read_comments([str(source)], ScanResult()) == [Finding(str(source), 2)]

    def test_counts_the_files_it_read(self, tmp_path: Path) -> None:
        """Every file parsed counts towards the summary."""
        source = tmp_path / "counting.py"
        source.write_text("x = 1\n", encoding="utf-8")
        result = ScanResult()
        read_comments([str(source)], result)
        assert result.files_scanned == 1

    def test_a_file_that_will_not_open_is_skipped(self, tmp_path: Path) -> None:
        """An unreadable file scans nothing."""
        result = ScanResult()
        read_comments([str(tmp_path / "absent.py")], result)
        assert result.files_scanned == 0

    def test_a_file_that_will_not_parse_records_an_error(self, tmp_path: Path) -> None:
        """A broken file is an error, not a clean run."""
        source = tmp_path / "counting.py"
        source.write_text("def f(\n", encoding="utf-8")
        result = ScanResult()
        read_comments([str(source)], result)
        assert result.had_error

    def test_a_file_that_will_not_parse_is_not_counted(self, tmp_path: Path) -> None:
        """A file nothing could read did not get scanned."""
        source = tmp_path / "counting.py"
        source.write_text("def f(\n", encoding="utf-8")
        result = ScanResult()
        read_comments([str(source)], result)
        assert result.files_scanned == 0

    def test_verbose_names_each_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verbose says what was read."""
        source = tmp_path / "counting.py"
        source.write_text("x = 1\n", encoding="utf-8")
        read_comments([str(source)], ScanResult(), verbose=True)
        assert f"Reading: {source}" in capsys.readouterr().out


@pytest.mark.unit
class TestOutputFindings:
    """Printing findings in each format."""

    def test_prints_the_path_the_line_and_why(self, capsys: pytest.CaptureFixture[str]) -> None:
        """The default format is readable at a terminal."""
        output_findings([Finding("src/counting.py", 2)])
        assert capsys.readouterr().out == f"src/counting.py:2: {MESSAGE}\n"

    def test_count_mode_prints_only_the_number(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Counting says how many, not which."""
        output_findings([Finding("src/counting.py", 2)], count_mode=True)
        assert capsys.readouterr().out == "1\n"

    def test_annotate_prints_a_workflow_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        """An annotation lands on the line it names in the diff."""
        output_findings([Finding("src/counting.py", 2)], annotate=True)
        assert "::error file=src/counting.py,line=2::" in capsys.readouterr().out

    def test_nothing_found_prints_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        """A clean run is silent."""
        output_findings([])
        assert capsys.readouterr().out == ""


@pytest.mark.unit
class TestDetermineExitCode:
    """Choosing the exit code."""

    def test_a_clean_run_succeeds(self) -> None:
        """Nothing found is success."""
        assert determine_exit_code(ScanResult()) == EXIT_SUCCESS

    def test_findings_fail(self) -> None:
        """Something found fails the run."""
        assert determine_exit_code(ScanResult(findings=[Finding("a.py", 1)])) == EXIT_FINDINGS

    def test_an_error_is_its_own_code(self) -> None:
        """A tree that would not read is neither clean nor a finding."""
        assert determine_exit_code(ScanResult(had_error=True)) == EXIT_ERROR

    def test_warn_only_always_succeeds(self) -> None:
        """Warn-only reports without failing."""
        assert determine_exit_code(ScanResult(had_error=True), warn_only=True) == EXIT_SUCCESS


@pytest.mark.unit
class TestReport:
    """Printing whatever the chosen output mode asks for."""

    def test_quiet_prints_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Quiet reports through the exit code alone."""
        _report(ScanResult(findings=[Finding("a.py", 1)]), _namespace(quiet=True))
        assert capsys.readouterr().out == ""

    def test_verbose_counts_the_files(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verbose says how many files were read."""
        _report(ScanResult(files_scanned=3), _namespace(verbose=True))
        assert "Files scanned: 3" in capsys.readouterr().out

    def test_verbose_counts_the_findings(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verbose says how many findings there were."""
        _report(ScanResult(findings=[Finding("a.py", 1)]), _namespace(verbose=True))
        assert "Findings: 1" in capsys.readouterr().out

    def test_verbose_says_when_something_would_not_read(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verbose says the run hit an error."""
        _report(ScanResult(had_error=True), _namespace(verbose=True))
        assert "Errors occurred during scanning." in capsys.readouterr().out

    def test_count_prints_only_the_number(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Counting says how many, not which."""
        _report(ScanResult(findings=[Finding("a.py", 1)]), _namespace(count=True))
        assert capsys.readouterr().out == "1\n"


@pytest.mark.unit
class TestMainModule:
    """Running the package as a module."""

    def test_calls_main(self) -> None:
        """Importing __main__ runs the CLI."""
        with patch("assert_no_comments.cli.main") as entry_point:
            import_main()
            assert entry_point.called

    def test_calls_main_once(self) -> None:
        """Importing __main__ runs the CLI exactly once."""
        with patch("assert_no_comments.cli.main") as entry_point:
            import_main()
            assert entry_point.call_count == 1


def _stopped_at(args: list[str]) -> object:
    """Run the CLI and name the code it stopped with."""
    with pytest.raises(SystemExit) as stopping:
        main(args)
    return stopping.value.code


@pytest.mark.unit
@pytest.mark.usefixtures("tiny_tree")
class TestMainChoosesTheExitCode:
    """What main stops with."""

    def test_a_tree_with_no_comment_in_it_succeeds(self) -> None:
        """Nothing found is success."""
        assert _stopped_at([CLEAN]) == EXIT_SUCCESS

    def test_a_tree_with_a_comment_in_it_fails(self) -> None:
        """Something found fails the run."""
        assert _stopped_at([TREE]) == EXIT_FINDINGS

    def test_warn_only_succeeds_anyway(self) -> None:
        """Warn-only reports without failing."""
        assert _stopped_at([TREE, "--warn-only"]) == EXIT_SUCCESS

    def test_a_path_that_is_not_there_is_an_error(self) -> None:
        """A tree that is not there fails the run."""
        assert _stopped_at(["absent"]) == EXIT_ERROR

    def test_a_path_that_is_not_there_beside_a_clean_tree_is_an_error(self) -> None:
        """One good tree does not excuse one that is not there."""
        assert _stopped_at([CLEAN, "absent"]) == EXIT_ERROR


@pytest.mark.unit
@pytest.mark.usefixtures("tiny_tree")
class TestMainPrintsWhatItFound:
    """What main says."""

    def test_names_the_file_the_comment_sits_in(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The output names the file."""
        _stopped_at([TREE])
        assert SECOND in capsys.readouterr().out

    def test_fail_fast_says_one_thing(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Fail-fast reports one finding however many there are."""
        _stopped_at([TREE, "--fail-fast"])
        assert len(capsys.readouterr().out.splitlines()) == 1

    def test_quiet_says_nothing(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Quiet reports through the exit code alone."""
        _stopped_at([TREE, "--quiet"])
        assert capsys.readouterr().out == ""

    def test_count_says_how_many(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Counting says how many, not which."""
        _stopped_at([TREE, "--count"])
        assert capsys.readouterr().out == "2\n"

    def test_annotate_says_where(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An annotation lands on the line it names in the diff."""
        _stopped_at([TREE, "--annotate"])
        assert f"::error file={SECOND},line=1::" in capsys.readouterr().out

    def test_verbose_opens_with_how_much_there_is_to_do(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verbose says how many files it will read."""
        _stopped_at([TREE, "--verbose"])
        assert "Reading 3 file(s)..." in capsys.readouterr().out

    def test_verbose_names_what_was_excluded(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verbose says what was left out."""
        _stopped_at([TREE, "--verbose", "--exclude", SECOND])
        assert f"Excluding patterns: {SECOND}" in capsys.readouterr().out

    def test_verbose_with_nothing_excluded_says_nothing_about_it(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Nothing excluded means nothing to report about excluding."""
        _stopped_at([TREE, "--verbose"])
        assert "Excluding patterns" not in capsys.readouterr().out

    def test_a_path_that_is_not_there_is_named(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The error says which path was not found."""
        _stopped_at(["absent"])
        assert "Error: Path not found: absent" in capsys.readouterr().err
