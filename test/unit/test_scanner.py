from __future__ import annotations

from pathlib import Path

import pytest
from test_support import read_sample

from assert_no_comments.scanner import (
    HCL,
    Finding,
    Unreadable,
    comments_in,
    hcl_comments,
    javascript_comments,
    parsed_comments,
    python_comments,
    reader_for,
    tsx_comments,
    typescript_comments,
    yaml_comments,
)


def sample(name: str) -> str:
    return read_sample(Path(__file__).parent, name)


@pytest.mark.unit
class TestPythonComments:
    def test_a_comment_on_a_line_of_its_own_is_reported(self) -> None:
        assert python_comments(sample("python/comment_on_line_own_reported")) == [1]

    def test_a_comment_after_code_on_the_same_line_is_reported(self) -> None:
        assert python_comments(sample("python/comment_after_code_on_same_line_reported")) == [2]

    def test_a_hash_inside_a_string_is_not_reported(self) -> None:
        assert python_comments(sample("python/hash_inside_string_reported")) == []

    def test_a_module_docstring_is_reported(self) -> None:
        assert python_comments(sample("python/module_docstring_reported")) == [1]

    def test_a_function_docstring_is_reported(self) -> None:
        assert python_comments(sample("python/function_docstring_reported")) == [2]

    def test_a_class_docstring_is_reported(self) -> None:
        assert python_comments(sample("python/class_docstring_reported")) == [2]

    def test_an_async_function_docstring_is_reported(self) -> None:
        assert python_comments(sample("python/async_function_docstring_reported")) == [2]

    def test_a_file_with_nothing_in_it_reports_nothing(self) -> None:
        assert python_comments("") == []

    def test_a_statement_that_is_not_a_docstring_is_not_reported(self) -> None:
        assert python_comments(sample("python/statement_docstring_reported")) == []

    def test_a_number_standing_alone_is_not_read_as_a_docstring(self) -> None:
        assert python_comments(sample("python/number_standing_read_as_docstring")) == []

    def test_a_string_that_is_not_the_first_statement_is_not_reported(self) -> None:
        assert python_comments(sample("python/string_first_statement_reported")) == []


@pytest.mark.unit
class TestYamlComments:
    def test_a_comment_is_reported(self) -> None:
        assert yaml_comments(sample("yaml/comment_reported")) == [3]

    def test_a_hash_inside_a_block_scalar_is_not_reported(self) -> None:
        assert yaml_comments(sample("yaml/hash_inside_block_scalar_reported")) == []

    def test_a_hash_inside_a_quoted_string_is_not_reported(self) -> None:
        assert yaml_comments(sample("yaml/hash_inside_quoted_string_reported")) == []

    def test_a_file_with_nothing_in_it_reports_nothing(self) -> None:
        assert yaml_comments("") == []


@pytest.mark.unit
class TestHclComments:
    def test_a_hash_comment_is_reported(self) -> None:
        assert hcl_comments(sample("hcl/hash_comment_reported")) == [1]

    def test_a_double_slash_comment_is_reported(self) -> None:
        assert hcl_comments(sample("hcl/double_slash_comment_reported")) == [2]

    def test_a_block_comment_is_reported(self) -> None:
        assert hcl_comments(sample("hcl/block_comment_reported")) == [2]

    def test_a_hash_inside_a_string_is_not_reported(self) -> None:
        assert hcl_comments(sample("hcl/hash_inside_string_reported")) == []

    def test_an_escaped_quote_does_not_end_a_string(self) -> None:
        assert hcl_comments(sample("hcl/escaped_quote_end_string")) == []

    def test_a_hash_inside_a_heredoc_is_not_reported(self) -> None:
        assert hcl_comments(sample("hcl/hash_inside_heredoc_reported")) == []

    def test_a_file_that_will_not_parse_still_reports_what_it_can(self) -> None:
        assert hcl_comments(sample("hcl/file_will_parse_reports")) == [1]


@pytest.mark.unit
class TestJavascriptComments:
    def test_a_comment_is_reported(self) -> None:
        assert javascript_comments(sample("javascript/comment_reported")) == [2]

    def test_a_block_comment_is_reported(self) -> None:
        assert javascript_comments(sample("javascript/block_comment_reported")) == [2]

    def test_a_double_slash_inside_a_string_is_not_reported(self) -> None:
        assert javascript_comments(sample("javascript/double_slash_inside_string_reported")) == []

    def test_a_double_slash_inside_a_template_literal_is_not_reported(self) -> None:
        assert javascript_comments(sample("javascript/double_slash_inside_template_literal")) == []

    def test_a_double_slash_inside_a_pattern_is_not_reported(self) -> None:
        assert javascript_comments(sample("javascript/double_slash_inside_pattern_reported")) == []

    def test_a_slash_inside_a_character_class_does_not_end_the_pattern(self) -> None:
        assert javascript_comments(sample("javascript/slash_inside_character_class_end")) == []

    def test_a_comment_after_a_pattern_is_reported(self) -> None:
        assert javascript_comments(sample("javascript/comment_after_pattern_reported")) == [1]

    def test_a_comment_after_a_division_is_reported(self) -> None:
        assert javascript_comments(sample("javascript/comment_after_division_reported")) == [1]

    def test_a_comment_after_a_closing_element_is_reported(self) -> None:
        assert javascript_comments(sample("javascript/comment_after_closing_element")) == [4]

    def test_a_comment_after_a_self_closing_element_is_reported(self) -> None:
        assert javascript_comments(sample("javascript/comment_after_self_closing_element")) == [1]

    def test_a_comment_braced_inside_an_element_is_reported(self) -> None:
        assert javascript_comments(sample("javascript/comment_braced_inside_element")) == [3]

    def test_markers_in_the_text_of_an_element_are_not_reported(self) -> None:
        assert javascript_comments(sample("javascript/markers_in_text_element_reported")) == []

    def test_a_comment_on_the_last_line_with_no_line_break_is_reported(self) -> None:
        assert javascript_comments("// why") == [1]

    def test_a_file_that_will_not_parse_still_reports_what_it_can(self) -> None:
        assert javascript_comments(sample("javascript/file_will_parse_reports")) == [2]


@pytest.mark.unit
class TestTypescriptComments:
    def test_a_comment_is_reported(self) -> None:
        assert typescript_comments(sample("typescript/comment_reported")) == [1]

    def test_a_documentation_block_is_reported(self) -> None:
        assert typescript_comments(sample("typescript/documentation_block_reported")) == [2]

    def test_a_type_assertion_does_not_hide_the_comment_after_it(self) -> None:
        assert typescript_comments(sample("typescript/type_assertion_hide_comment_after")) == [2]


@pytest.mark.unit
class TestTsxComments:
    def test_a_comment_is_reported(self) -> None:
        assert tsx_comments(sample("tsx/comment_reported")) == [2]

    def test_a_comment_after_a_closing_element_is_reported(self) -> None:
        assert tsx_comments(sample("tsx/comment_after_closing_element_reported")) == [4]

    def test_a_comment_braced_inside_an_element_is_reported(self) -> None:
        assert tsx_comments(sample("tsx/comment_braced_inside_element_reported")) == [3]


@pytest.mark.unit
class TestParsedComments:
    def test_a_grammar_named_directly_reads_its_comments(self) -> None:
        assert parsed_comments(sample("parsed/grammar_named_directly_reads_comments"), HCL) == [1]

    def test_two_comments_on_one_line_are_reported_once(self) -> None:
        assert javascript_comments(sample("parsed/two_comments_on_one_line_reported_once")) == [1]


@pytest.mark.unit
class TestReaderFor:
    def test_a_python_file_gets_the_python_reader(self) -> None:
        assert reader_for("src/counting.py") is python_comments

    def test_a_yaml_file_gets_the_yaml_reader(self) -> None:
        assert reader_for("etc/config.yaml") is yaml_comments

    def test_an_opentofu_file_gets_the_hcl_reader(self) -> None:
        assert reader_for("infra/main.tf") is hcl_comments

    def test_a_module_javascript_file_gets_the_javascript_reader(self) -> None:
        assert reader_for("src/app.mjs") is javascript_comments

    def test_a_jsx_file_gets_the_javascript_reader(self) -> None:
        assert reader_for("src/App.jsx") is javascript_comments

    def test_a_typescript_file_gets_the_typescript_reader(self) -> None:
        assert reader_for("src/counting.ts") is typescript_comments

    def test_a_declaration_file_gets_the_typescript_reader(self) -> None:
        assert reader_for("src/vite-env.d.ts") is typescript_comments

    def test_a_module_typescript_file_gets_the_typescript_reader(self) -> None:
        assert reader_for("src/app.mts") is typescript_comments

    def test_a_commonjs_typescript_file_gets_the_typescript_reader(self) -> None:
        assert reader_for("src/app.cts") is typescript_comments

    def test_a_tsx_file_gets_the_tsx_reader(self) -> None:
        assert reader_for("src/App.tsx") is tsx_comments

    def test_tsx_and_typescript_are_read_by_different_grammars(self) -> None:
        assert reader_for("src/App.tsx") is not reader_for("src/app.ts")

    def test_a_lock_file_gets_no_reader(self) -> None:
        assert reader_for("infra/.terraform.lock.hcl") is None

    def test_a_markdown_file_gets_no_reader(self) -> None:
        assert reader_for("README.md") is None

    def test_a_suffix_nobody_speaks_gets_no_reader(self) -> None:
        assert reader_for("notes.txt") is None


@pytest.mark.unit
class TestCommentsIn:
    def test_a_finding_names_the_file_and_the_line(self) -> None:
        found = comments_in("src/counting.py", sample("comments_in/finding_names"))
        assert found == [Finding("src/counting.py", 2)]

    def test_a_file_no_reader_speaks_is_left_alone(self) -> None:
        assert comments_in("README.md", sample("comments_in/file_no_reader_speaks_left")) == []

    def test_a_file_that_will_not_parse_is_unreadable(self) -> None:
        with pytest.raises(Unreadable):
            comments_in("src/counting.py", sample("comments_in/file_will_parse_unreadable"))

    def test_a_yaml_file_that_will_not_parse_is_unreadable(self) -> None:
        with pytest.raises(Unreadable):
            comments_in("etc/config.yml", sample("comments_in/yaml_file_will_parse_unreadable"))


@pytest.mark.unit
class TestFinding:
    def test_prints_as_path_and_line(self) -> None:
        assert str(Finding("src/counting.py", 2)) == "src/counting.py:2"

    def test_two_findings_on_the_same_line_are_the_same_finding(self) -> None:
        assert Finding("src/counting.py", 2) == Finding("src/counting.py", 2)
