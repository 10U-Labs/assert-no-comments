from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from test_assert_no_comments.support import read_sample

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

TREE = "kept"
CLEAN = "kept/clean.py"
SECOND = "kept/second.py"


def sample(name: str) -> str:
    return read_sample(Path(__file__).parent, name)


def import_main() -> None:
    sys.modules.pop("assert_no_comments.__main__", None)
    importlib.import_module("assert_no_comments.__main__")


def _namespace(**overrides: bool) -> argparse.Namespace:
    settings = {"quiet": False, "count": False, "verbose": False, "annotate": False}
    settings.update(overrides)
    return create_parser().parse_args(
        ["src", *[f"--{name}" for name, chosen in settings.items() if chosen]]
    )


@pytest.mark.unit
class TestCreateParser:
    def test_reads_one_tree(self) -> None:
        assert create_parser().parse_args(["src"]).trees == ["src"]

    def test_reads_several_trees(self) -> None:
        assert create_parser().parse_args(["src", "test"]).trees == ["src", "test"]

    def test_annotate_is_off_by_default(self) -> None:
        assert create_parser().parse_args(["src"]).annotate is False

    def test_quiet_and_verbose_cannot_both_be_asked_for(self) -> None:
        with pytest.raises(SystemExit):
            create_parser().parse_args(["src", "--quiet", "--verbose"])

    def test_fail_fast_and_warn_only_cannot_both_be_asked_for(self) -> None:
        with pytest.raises(SystemExit):
            create_parser().parse_args(["src", "--fail-fast", "--warn-only"])


@pytest.mark.unit
class TestParsePatterns:
    def test_nothing_given_is_no_patterns(self) -> None:
        assert parse_patterns(None) == []

    def test_a_blank_string_is_no_patterns(self) -> None:
        assert parse_patterns("") == []

    def test_one_pattern_is_read(self) -> None:
        assert parse_patterns("vendor/*") == ["vendor/*"]

    def test_surrounding_spaces_are_dropped(self) -> None:
        assert parse_patterns(" a/* , b/* ") == ["a/*", "b/*"]

    def test_an_empty_entry_is_dropped(self) -> None:
        assert parse_patterns("a/*,,") == ["a/*"]


@pytest.mark.unit
class TestShouldSkip:
    def test_a_path_pattern_matches(self) -> None:
        assert should_skip("src/vendor/leaflet.js", ["src/vendor/*"])

    def test_a_basename_pattern_matches(self) -> None:
        assert should_skip("src/vendor/leaflet.js", ["leaflet.js"])

    def test_an_unrelated_pattern_does_not_match(self) -> None:
        assert not should_skip("src/counting.py", ["src/vendor/*"])

    def test_no_patterns_skips_nothing(self) -> None:
        assert not should_skip("src/counting.py", [])


@pytest.mark.unit
class TestIsGlobPattern:
    def test_a_star_makes_it_a_pattern(self) -> None:
        assert _is_glob_pattern("src/*.py")

    def test_a_plain_path_is_not_a_pattern(self) -> None:
        assert not _is_glob_pattern("src/counting.py")


@pytest.mark.unit
class TestWalkSourceFiles:
    def test_finds_a_python_file(self, tmp_path: Path) -> None:
        (tmp_path / "counting.py").write_text(sample("walk/finds_python_file"), encoding="utf-8")
        assert _walk_source_files(str(tmp_path)) == [str(tmp_path / "counting.py")]

    def test_leaves_a_markdown_file_alone(self, tmp_path: Path) -> None:
        (tmp_path / "notes.md").write_text(sample("walk/leaves_markdown_file"), encoding="utf-8")
        assert not _walk_source_files(str(tmp_path))

    def test_reads_a_hidden_directory(self, tmp_path: Path) -> None:
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "release.yml").write_text(sample("walk/reads_hidden"), encoding="utf-8")
        assert _walk_source_files(str(tmp_path)) == [str(workflows / "release.yml")]

    def test_leaves_a_cache_directory_alone(self, tmp_path: Path) -> None:
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "counting.py").write_text(sample("walk/leaves_cache_directory"), encoding="utf-8")
        assert not _walk_source_files(str(tmp_path))


@pytest.mark.unit
class TestExpand:
    def test_a_file_names_itself(self, tmp_path: Path) -> None:
        source = tmp_path / "counting.py"
        source.write_text(sample("expand/file_names_itself"), encoding="utf-8")
        assert _expand(str(source)) == ([str(source)], True)

    def test_a_directory_names_what_is_under_it(self, tmp_path: Path) -> None:
        (tmp_path / "counting.py").write_text(sample("expand/directory_names"), encoding="utf-8")
        assert _expand(str(tmp_path)) == ([str(tmp_path / "counting.py")], True)

    def test_a_glob_names_the_files_it_matches(self, tmp_path: Path) -> None:
        (tmp_path / "counting.py").write_text(sample("expand/glob_names_files"), encoding="utf-8")
        assert _expand(str(tmp_path / "*.py")) == ([str(tmp_path / "counting.py")], True)

    def test_a_glob_matching_a_directory_names_what_is_under_it(self, tmp_path: Path) -> None:
        package = tmp_path / "pkg"
        package.mkdir()
        (package / "counting.py").write_text(sample("expand/glob_matching"), encoding="utf-8")
        assert _expand(str(tmp_path / "p*")) == ([str(package / "counting.py")], True)

    def test_a_glob_matching_a_dangling_link_names_nothing(self, tmp_path: Path) -> None:
        (tmp_path / "counting.py").symlink_to(tmp_path / "absent.py")
        assert _expand(str(tmp_path / "*.py")) == ([], True)

    def test_a_glob_matching_nothing_names_nothing(self, tmp_path: Path) -> None:
        assert _expand(str(tmp_path / "*.js")) == ([], False)

    def test_a_path_that_is_not_there_names_nothing(self, tmp_path: Path) -> None:
        assert _expand(str(tmp_path / "absent.py")) == ([], False)


@pytest.mark.unit
class TestCollect:
    def test_names_the_files_to_read(self, tmp_path: Path) -> None:
        (tmp_path / "counting.py").write_text(sample("collect/names_files_to"), encoding="utf-8")
        assert collect([str(tmp_path)], []) == ([str(tmp_path / "counting.py")], [])

    def test_names_the_paths_that_matched_nothing(self, tmp_path: Path) -> None:
        assert collect([str(tmp_path / "absent")], [])[1] == [str(tmp_path / "absent")]

    def test_an_excluded_file_is_left_out(self, tmp_path: Path) -> None:
        (tmp_path / "counting.py").write_text(sample("collect/excluded_file"), encoding="utf-8")
        assert collect([str(tmp_path)], ["counting.py"]) == ([], [])

    def test_a_file_named_twice_is_read_once(self, tmp_path: Path) -> None:
        source = tmp_path / "counting.py"
        source.write_text(sample("collect/file_named_twice_read_once"), encoding="utf-8")
        assert collect([str(tmp_path), str(source)], []) == ([str(source)], [])

    def test_a_named_file_no_reader_speaks_is_left_out(self, tmp_path: Path) -> None:
        notes = tmp_path / "notes.md"
        notes.write_text(sample("collect/named_file_no_reader_speaks_left_out"), encoding="utf-8")
        assert collect([str(notes)], []) == ([], [])


@pytest.mark.unit
class TestRead:
    def test_returns_the_content(self, tmp_path: Path) -> None:
        source = tmp_path / "counting.py"
        source.write_text(sample("read/returns_content"), encoding="utf-8")
        assert _read(str(source), ScanResult()) == "x = 1\n"

    def test_a_missing_file_returns_nothing(self, tmp_path: Path) -> None:
        assert _read(str(tmp_path / "absent.py"), ScanResult()) is None

    def test_a_missing_file_records_an_error(self, tmp_path: Path) -> None:
        result = ScanResult()
        _read(str(tmp_path / "absent.py"), result)
        assert result.had_error

    def test_a_file_that_is_not_utf8_records_an_error(self, tmp_path: Path) -> None:
        source = tmp_path / "counting.py"
        source.write_bytes(b"\xff\xfe\x00")
        result = ScanResult()
        _read(str(source), result)
        assert result.had_error


@pytest.mark.unit
class TestReadComments:
    def test_collects_the_findings(self, tmp_path: Path) -> None:
        source = tmp_path / "counting.py"
        source.write_text(sample("read_comments/collects_findings"), encoding="utf-8")
        assert read_comments([str(source)], ScanResult()) == [Finding(str(source), 2)]

    def test_counts_the_files_it_read(self, tmp_path: Path) -> None:
        source = tmp_path / "counting.py"
        source.write_text(sample("read_comments/counts_files_read"), encoding="utf-8")
        result = ScanResult()
        read_comments([str(source)], result)
        assert result.files_scanned == 1

    def test_a_file_that_will_not_open_is_skipped(self, tmp_path: Path) -> None:
        result = ScanResult()
        read_comments([str(tmp_path / "absent.py")], result)
        assert result.files_scanned == 0

    def test_a_file_that_will_not_parse_records_an_error(self, tmp_path: Path) -> None:
        source = tmp_path / "counting.py"
        source.write_text(sample("read_comments/file_will_parse_records_error"), encoding="utf-8")
        result = ScanResult()
        read_comments([str(source)], result)
        assert result.had_error

    def test_a_file_that_will_not_parse_is_not_counted(self, tmp_path: Path) -> None:
        source = tmp_path / "counting.py"
        source.write_text(sample("read_comments/file_will_parse_counted"), encoding="utf-8")
        result = ScanResult()
        read_comments([str(source)], result)
        assert result.files_scanned == 0

    def test_verbose_names_each_file(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        source = tmp_path / "counting.py"
        source.write_text(sample("read_comments/verbose_names_each_file"), encoding="utf-8")
        read_comments([str(source)], ScanResult(), verbose=True)
        assert f"Reading: {source}" in capsys.readouterr().out


@pytest.mark.unit
class TestOutputFindings:
    def test_prints_the_path_the_line_and_why(self, capsys: pytest.CaptureFixture[str]) -> None:
        output_findings([Finding("src/counting.py", 2)])
        assert capsys.readouterr().out == f"src/counting.py:2: {MESSAGE}\n"

    def test_count_mode_prints_only_the_number(self, capsys: pytest.CaptureFixture[str]) -> None:
        output_findings([Finding("src/counting.py", 2)], count_mode=True)
        assert capsys.readouterr().out == "1\n"

    def test_annotate_prints_a_workflow_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        output_findings([Finding("src/counting.py", 2)], annotate=True)
        assert "::error file=src/counting.py,line=2::" in capsys.readouterr().out

    def test_nothing_found_prints_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        output_findings([])
        assert capsys.readouterr().out == ""


@pytest.mark.unit
class TestDetermineExitCode:
    def test_a_clean_run_succeeds(self) -> None:
        assert determine_exit_code(ScanResult()) == EXIT_SUCCESS

    def test_findings_fail(self) -> None:
        assert determine_exit_code(ScanResult(findings=[Finding("a.py", 1)])) == EXIT_FINDINGS

    def test_an_error_is_its_own_code(self) -> None:
        assert determine_exit_code(ScanResult(had_error=True)) == EXIT_ERROR

    def test_warn_only_always_succeeds(self) -> None:
        assert determine_exit_code(ScanResult(had_error=True), warn_only=True) == EXIT_SUCCESS


@pytest.mark.unit
class TestReport:
    def test_quiet_prints_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        _report(ScanResult(findings=[Finding("a.py", 1)]), _namespace(quiet=True))
        assert capsys.readouterr().out == ""

    def test_verbose_counts_the_files(self, capsys: pytest.CaptureFixture[str]) -> None:
        _report(ScanResult(files_scanned=3), _namespace(verbose=True))
        assert "Files scanned: 3" in capsys.readouterr().out

    def test_verbose_counts_the_findings(self, capsys: pytest.CaptureFixture[str]) -> None:
        _report(ScanResult(findings=[Finding("a.py", 1)]), _namespace(verbose=True))
        assert "Findings: 1" in capsys.readouterr().out

    def test_verbose_says_when_something_would_not_read(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _report(ScanResult(had_error=True), _namespace(verbose=True))
        assert "Errors occurred during scanning." in capsys.readouterr().out

    def test_count_prints_only_the_number(self, capsys: pytest.CaptureFixture[str]) -> None:
        _report(ScanResult(findings=[Finding("a.py", 1)]), _namespace(count=True))
        assert capsys.readouterr().out == "1\n"


@pytest.mark.unit
class TestMainModule:
    def test_calls_main(self) -> None:
        with patch("assert_no_comments.cli.main") as entry_point:
            import_main()
            assert entry_point.called

    def test_calls_main_once(self) -> None:
        with patch("assert_no_comments.cli.main") as entry_point:
            import_main()
            assert entry_point.call_count == 1


def _stopped_at(args: list[str]) -> object:
    with pytest.raises(SystemExit) as stopping:
        main(args)
    return stopping.value.code


@pytest.mark.unit
@pytest.mark.usefixtures("tiny_tree")
class TestMainChoosesTheExitCode:
    def test_a_tree_with_no_comment_in_it_succeeds(self) -> None:
        assert _stopped_at([CLEAN]) == EXIT_SUCCESS

    def test_a_tree_with_a_comment_in_it_fails(self) -> None:
        assert _stopped_at([TREE]) == EXIT_FINDINGS

    def test_warn_only_succeeds_anyway(self) -> None:
        assert _stopped_at([TREE, "--warn-only"]) == EXIT_SUCCESS

    def test_a_path_that_is_not_there_is_an_error(self) -> None:
        assert _stopped_at(["absent"]) == EXIT_ERROR

    def test_a_path_that_is_not_there_beside_a_clean_tree_is_an_error(self) -> None:
        assert _stopped_at([CLEAN, "absent"]) == EXIT_ERROR


@pytest.mark.unit
@pytest.mark.usefixtures("tiny_tree")
class TestMainPrintsWhatItFound:
    def test_names_the_file_the_comment_sits_in(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stopped_at([TREE])
        assert SECOND in capsys.readouterr().out

    def test_fail_fast_says_one_thing(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stopped_at([TREE, "--fail-fast"])
        assert len(capsys.readouterr().out.splitlines()) == 1

    def test_quiet_says_nothing(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stopped_at([TREE, "--quiet"])
        assert capsys.readouterr().out == ""

    def test_count_says_how_many(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stopped_at([TREE, "--count"])
        assert capsys.readouterr().out == "2\n"

    def test_annotate_says_where(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stopped_at([TREE, "--annotate"])
        assert f"::error file={SECOND},line=1::" in capsys.readouterr().out

    def test_verbose_opens_with_how_much_there_is_to_do(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stopped_at([TREE, "--verbose"])
        assert "Reading 3 file(s)..." in capsys.readouterr().out

    def test_verbose_names_what_was_excluded(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stopped_at([TREE, "--verbose", "--exclude", SECOND])
        assert f"Excluding patterns: {SECOND}" in capsys.readouterr().out

    def test_verbose_with_nothing_excluded_says_nothing_about_it(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stopped_at([TREE, "--verbose"])
        assert "Excluding patterns" not in capsys.readouterr().out

    def test_a_path_that_is_not_there_is_named(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stopped_at(["absent"])
        assert "Error: Path not found: absent" in capsys.readouterr().err
