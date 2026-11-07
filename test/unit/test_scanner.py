from __future__ import annotations

from pathlib import Path

import pytest
from test_read_sample import read_sample

from assert_no_comments.scanner import (
    HCL,
    Finding,
    Unreadable,
    c_comments,
    comments_in,
    cpp_comments,
    hcl_comments,
    javascript_comments,
    parsed_comments,
    python_comments,
    reader_for,
    shell_comments,
    systemverilog_comments,
    tsx_comments,
    typescript_comments,
    workflow_comments,
    yaml_comments,
)


CPP_SUFFIXES = (
    ".C",
    ".CPP",
    ".H",
    ".HPP",
    ".c++",
    ".cc",
    ".cp",
    ".cpp",
    ".cxx",
    ".h",
    ".h++",
    ".hh",
    ".hp",
    ".hpp",
    ".hxx",
    ".tcc",
)

SHELL_SUFFIXES = (".bash", ".sh")

SYSTEMVERILOG_SUFFIXES = (".sv", ".svh", ".v", ".vh")

WORKFLOW_PATHS = (
    ".github/workflows/build.yml",
    ".github/workflows/build.yaml",
    "action.yml",
    "action.yaml",
    ".github/actions/setup/action.yml",
)

PLAIN_YAML_PATHS = (
    "etc/config.yml",
    ".github/dependabot.yml",
    ".github/workflows/templates/build.yml",
)

BASH_OR_SH_STEPS = ("step_shell_bash", "step_shell_custom_bash", "step_shell_sh")

UNREAD_SHELL_STEPS = ("step_shell_cmd", "step_shell_pwsh")

WINDOWS_RUNNERS = ("windows_label_list", "windows_runner")

OTHER_RUNNERS = ("expression_runner", "linux_runner")


def sample(name: str) -> str:
    return read_sample(Path(__file__).parent, name)


class TestPythonComments:
    def test_a_comment_on_a_line_of_its_own_is_reported(self) -> None:
        assert python_comments(sample("python/comment_on_line_own_reported")) == [1]

    def test_a_comment_after_code_on_the_same_line_is_reported(self) -> None:
        assert python_comments(sample("python/comment_after_code_on_same_line_reported")) == [2]

    def test_a_hash_inside_a_string_is_not_reported(self) -> None:
        assert python_comments(sample("python/hash_inside_string_reported")) == []

    def test_a_shebang_on_the_first_line_is_not_reported(self) -> None:
        assert python_comments(sample("python/shebang_spared")) == []

    def test_a_shebang_on_the_second_line_is_reported(self) -> None:
        assert python_comments(sample("python/shebang_on_second_line_reported")) == [2]

    def test_a_shebang_after_a_space_is_reported(self) -> None:
        assert python_comments(sample("python/indented_shebang_reported")) == [1]

    def test_a_first_line_with_a_space_before_the_bang_is_reported(self) -> None:
        assert python_comments(sample("python/spaced_bang_reported")) == [1]

    def test_a_comment_after_the_shebang_is_reported(self) -> None:
        assert python_comments(sample("python/comment_after_shebang_reported")) == [2]

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


class TestYamlComments:
    def test_a_comment_is_reported(self) -> None:
        assert yaml_comments(sample("yaml/comment_reported")) == [3]

    def test_a_hash_inside_a_block_scalar_is_not_reported(self) -> None:
        assert yaml_comments(sample("yaml/hash_inside_block_scalar_reported")) == []

    def test_a_hash_inside_a_quoted_string_is_not_reported(self) -> None:
        assert yaml_comments(sample("yaml/hash_inside_quoted_string_reported")) == []

    def test_a_file_with_nothing_in_it_reports_nothing(self) -> None:
        assert yaml_comments("") == []


def _workflow(name: str) -> list[int]:
    return workflow_comments(sample(f"workflow/{name}"))


class TestWorkflowComments:
    def test_a_yaml_comment_is_reported(self) -> None:
        assert _workflow("yaml_comment_reported") == [4]

    def test_a_file_with_nothing_in_it_reports_nothing(self) -> None:
        assert workflow_comments("") == []

    def test_a_comment_line_in_a_literal_run_script_is_reported(self) -> None:
        assert _workflow("literal_run_comment_line") == [7]

    def test_a_comment_after_a_command_in_a_run_script_is_reported(self) -> None:
        assert _workflow("comment_after_command") == [7]

    def test_a_comment_line_in_a_folded_run_script_is_reported(self) -> None:
        assert _workflow("folded_run_comment_line") == [8]

    def test_a_comment_line_in_a_composite_action_step_is_reported(self) -> None:
        assert _workflow("composite_action_step") == [6]

    def test_a_comment_after_an_expression_is_reported(self) -> None:
        assert _workflow("comment_after_expression") == [7]

    def test_a_python_step_is_read_as_python(self) -> None:
        assert _workflow("python_step") == [8]

    def test_an_expression_does_not_stop_a_python_step_from_parsing(self) -> None:
        assert _workflow("python_step_with_expression") == [8]

    def test_markers_the_shell_reads_as_content_are_not_reported(self) -> None:
        assert _workflow("markers_the_shell_reads_as_content") == []

    def test_a_block_scalar_under_another_key_is_not_read(self) -> None:
        assert _workflow("block_scalar_under_another_key") == []

    def test_a_quoted_run_value_is_not_read(self) -> None:
        assert _workflow("quoted_run_value") == []


class TestWorkflowShells:
    @pytest.mark.parametrize("name", BASH_OR_SH_STEPS)
    def test_a_step_whose_shell_is_bash_or_sh_is_read(self, name: str) -> None:
        assert _workflow(name) == [7]

    def test_a_job_default_shell_is_read_on_a_windows_runner(self) -> None:
        assert _workflow("job_default_shell_on_windows") == [10]

    def test_a_workflow_default_shell_is_read_on_a_windows_runner(self) -> None:
        assert _workflow("workflow_default_shell_on_windows") == [10]

    def test_a_job_default_is_taken_before_the_workflow_default(self) -> None:
        assert _workflow("job_default_before_workflow_default") == [13]

    def test_a_step_shell_is_taken_before_the_defaults(self) -> None:
        assert _workflow("step_shell_before_defaults") == [13]

    @pytest.mark.parametrize("name", UNREAD_SHELL_STEPS)
    def test_a_shell_with_no_reader_is_not_read(self, name: str) -> None:
        assert _workflow(name) == []

    @pytest.mark.parametrize("name", WINDOWS_RUNNERS)
    def test_a_script_with_no_shell_on_a_windows_runner_is_not_read(self, name: str) -> None:
        assert _workflow(name) == []

    @pytest.mark.parametrize("name", OTHER_RUNNERS)
    def test_a_script_with_no_shell_on_any_other_runner_is_read(self, name: str) -> None:
        assert _workflow(name) == [7]


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


class TestTypescriptComments:
    def test_a_comment_is_reported(self) -> None:
        assert typescript_comments(sample("typescript/comment_reported")) == [1]

    def test_a_documentation_block_is_reported(self) -> None:
        assert typescript_comments(sample("typescript/documentation_block_reported")) == [2]

    def test_a_type_assertion_does_not_hide_the_comment_after_it(self) -> None:
        assert typescript_comments(sample("typescript/type_assertion_hide_comment_after")) == [2]


class TestTsxComments:
    def test_a_comment_is_reported(self) -> None:
        assert tsx_comments(sample("tsx/comment_reported")) == [2]

    def test_a_comment_after_a_closing_element_is_reported(self) -> None:
        assert tsx_comments(sample("tsx/comment_after_closing_element_reported")) == [4]

    def test_a_comment_braced_inside_an_element_is_reported(self) -> None:
        assert tsx_comments(sample("tsx/comment_braced_inside_element_reported")) == [3]


class TestCppComments:
    def test_a_line_comment_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/line_comment_reported")) == [2]

    def test_a_block_comment_is_reported_at_its_first_line(self) -> None:
        assert cpp_comments(sample("cpp/block_comment_reported_first_line")) == [2]

    def test_a_triple_slash_comment_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/triple_slash_comment_reported")) == [1]

    def test_a_documentation_block_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/documentation_block_reported")) == [2]

    def test_a_comment_after_code_on_the_same_line_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/comment_after_code_reported")) == [2]

    def test_a_comment_continued_over_a_backslash_is_reported_once(self) -> None:
        assert cpp_comments(sample("cpp/comment_continued_over_backslash")) == [1]

    def test_a_comment_in_a_define_body_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/comment_in_define_body_reported")) == [2]

    def test_a_comment_on_the_continued_line_of_a_define_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/comment_continued_define_line")) == [2]

    def test_a_block_comment_in_a_define_body_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/block_comment_in_define_body")) == [2]

    def test_a_double_slash_inside_a_define_string_is_not_reported(self) -> None:
        assert cpp_comments(sample("cpp/double_slash_in_define_string")) == []

    def test_the_grammar_opens_a_block_comment_inside_a_define_string(self) -> None:
        assert cpp_comments(sample("cpp/block_opened_in_define_string")) == [1]

    def test_a_double_slash_inside_a_string_is_not_reported(self) -> None:
        assert cpp_comments(sample("cpp/double_slash_in_string")) == []

    def test_a_double_slash_inside_a_raw_string_is_not_reported(self) -> None:
        assert cpp_comments(sample("cpp/double_slash_in_raw_string")) == []

    def test_a_raw_string_delimiter_keeps_its_body_open_past_a_quote(self) -> None:
        assert cpp_comments(sample("cpp/raw_string_delimiter_keeps_body")) == []

    def test_a_slash_character_literal_is_not_reported(self) -> None:
        assert cpp_comments(sample("cpp/slash_character_literal")) == []

    def test_a_block_opener_inside_a_string_is_not_reported(self) -> None:
        assert cpp_comments(sample("cpp/block_opener_in_string")) == []

    def test_a_file_that_will_not_parse_still_reports_what_it_can(self) -> None:
        assert cpp_comments(sample("cpp/file_will_parse_reports")) == [1, 3]


class TestNamespaceEndComments:
    def test_the_end_of_a_named_namespace_is_spared(self) -> None:
        assert cpp_comments(sample("cpp/ends_named_namespace")) == []

    def test_an_end_naming_another_namespace_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/names_another_namespace")) == [4]

    def test_an_end_leaving_out_the_name_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/leaves_out_name")) == [4]

    def test_a_block_comment_ending_a_namespace_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/block_comment_ends_namespace")) == [4]

    def test_an_end_spaced_otherwise_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/spaced_namespace_end")) == [4]

    def test_an_end_with_more_words_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/namespace_end_more_words")) == [4]

    def test_an_end_on_the_line_after_the_brace_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/namespace_end_next_line")) == [5]

    def test_the_end_of_an_anonymous_namespace_is_spared(self) -> None:
        assert cpp_comments(sample("cpp/ends_anonymous_namespace")) == []

    def test_a_name_on_the_end_of_an_anonymous_namespace_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/names_namespace_anonymous_one_closes")) == [4]

    def test_the_end_of_a_nested_name_namespace_is_spared(self) -> None:
        assert cpp_comments(sample("cpp/ends_nested_name_namespace")) == []

    def test_the_end_of_an_inline_namespace_is_spared(self) -> None:
        assert cpp_comments(sample("cpp/ends_inline_namespace")) == []

    def test_the_end_of_a_namespace_nested_in_another_is_spared(self) -> None:
        assert cpp_comments(sample("cpp/ends_namespace_nested_another")) == []

    def test_the_end_of_a_namespace_with_a_one_line_body_is_spared(self) -> None:
        assert cpp_comments(sample("cpp/ends_namespace_one_line_body")) == []

    def test_a_struct_end_named_like_a_namespace_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/struct_end_named_namespace")) == [4]

    def test_a_function_end_named_like_a_namespace_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/function_end_named_namespace")) == [4]

    def test_an_include_guard_end_is_reported(self) -> None:
        assert cpp_comments(sample("cpp/include_guard_end")) == [7]


class TestCComments:
    def test_a_line_comment_is_reported(self) -> None:
        assert c_comments(sample("c/line_comment_reported")) == [2]

    def test_a_block_comment_is_reported_at_its_first_line(self) -> None:
        assert c_comments(sample("c/block_comment_reported_first_line")) == [2]

    def test_a_comment_after_code_on_the_same_line_is_reported(self) -> None:
        assert c_comments(sample("c/comment_after_code_reported")) == [2]

    def test_a_comment_in_a_define_body_is_reported(self) -> None:
        assert c_comments(sample("c/comment_in_define_body_reported")) == [2]

    def test_a_comment_on_the_continued_line_of_a_define_is_reported(self) -> None:
        assert c_comments(sample("c/comment_continued_define_line")) == [2]

    def test_the_grammar_opens_a_block_comment_inside_a_define_string(self) -> None:
        assert c_comments(sample("c/block_opened_in_define_string")) == [1]

    def test_a_double_slash_inside_a_string_is_not_reported(self) -> None:
        assert c_comments(sample("c/double_slash_in_string")) == []

    def test_a_double_slash_inside_a_define_string_is_not_reported(self) -> None:
        assert c_comments(sample("c/double_slash_in_define_string")) == []

    def test_a_slash_character_literal_is_not_reported(self) -> None:
        assert c_comments(sample("c/slash_character_literal")) == []

    def test_a_block_opener_inside_a_string_is_not_reported(self) -> None:
        assert c_comments(sample("c/block_opener_in_string")) == []

    def test_a_comment_beside_a_name_cpp_reserves_is_reported(self) -> None:
        assert c_comments(sample("c/comment_beside_cpp_keyword_name")) == [1]


class TestShellComments:
    def test_a_line_comment_is_reported(self) -> None:
        assert shell_comments(sample("shell/line_comment_reported")) == [2]

    def test_a_comment_after_a_command_on_the_same_line_is_reported(self) -> None:
        assert shell_comments(sample("shell/comment_after_command_reported")) == [1]

    def test_a_shebang_on_the_first_line_is_not_reported(self) -> None:
        assert shell_comments(sample("shell/shebang_spared")) == []

    def test_a_shebang_on_the_second_line_is_reported(self) -> None:
        assert shell_comments(sample("shell/shebang_on_second_line_reported")) == [2]

    def test_a_shebang_after_a_space_is_reported(self) -> None:
        assert shell_comments(sample("shell/indented_shebang_reported")) == [1]

    def test_a_first_line_with_a_space_before_the_bang_is_reported(self) -> None:
        assert shell_comments(sample("shell/spaced_bang_reported")) == [1]

    def test_a_hash_inside_a_double_quoted_string_is_not_reported(self) -> None:
        assert shell_comments(sample("shell/hash_in_double_quotes")) == []

    def test_a_hash_inside_a_single_quoted_string_is_not_reported(self) -> None:
        assert shell_comments(sample("shell/hash_in_single_quotes")) == []

    def test_a_hash_inside_a_word_is_not_reported(self) -> None:
        assert shell_comments(sample("shell/hash_in_word")) == []

    def test_a_hash_inside_a_here_document_is_not_reported(self) -> None:
        assert shell_comments(sample("shell/hash_in_here_document")) == []

    def test_a_hash_inside_a_parameter_expansion_is_not_reported(self) -> None:
        assert shell_comments(sample("shell/hash_in_parameter_expansion")) == []


def _hdl(name: str) -> list[int]:
    return systemverilog_comments(sample(f"systemverilog/{name}"))


class TestSystemverilogComments:
    def test_a_line_comment_is_reported(self) -> None:
        assert _hdl("line_comment_reported") == [2]

    def test_a_block_comment_is_reported_at_its_first_line(self) -> None:
        assert _hdl("block_comment_reported_first_line") == [2]

    def test_a_comment_after_code_on_the_same_line_is_reported(self) -> None:
        assert _hdl("comment_after_code_reported") == [2]

    def test_a_comment_after_endmodule_is_reported(self) -> None:
        assert _hdl("comment_after_endmodule_reported") == [2]

    def test_a_line_comment_in_a_define_body_is_reported(self) -> None:
        assert _hdl("comment_in_define_body_reported") == [1]

    def test_a_block_comment_in_a_define_body_is_reported(self) -> None:
        assert _hdl("block_comment_in_define_body_reported") == [1]

    def test_a_comment_on_the_continued_line_of_a_define_is_reported(self) -> None:
        assert _hdl("comment_continued_define_line") == [2]

    def test_a_double_slash_inside_a_define_string_is_not_reported(self) -> None:
        assert _hdl("double_slash_in_define_string") == []

    def test_a_line_comment_ends_at_the_backslash_that_continues_a_define(self) -> None:
        assert _hdl("comment_ends_at_the_backslash") == [1, 2]

    def test_the_grammar_ends_a_define_inside_a_block_comment(self) -> None:
        assert _hdl("block_comment_over_lines_in_define") == [2]

    def test_the_grammar_ends_a_define_inside_a_triple_quoted_string(self) -> None:
        assert _hdl("triple_quoted_string_in_define") == [2, 3]

    def test_a_triple_quoted_string_outside_a_macro_is_not_reported(self) -> None:
        assert _hdl("triple_quoted_string_outside_macro") == []

    def test_comment_markers_inside_a_string_literal_are_not_reported(self) -> None:
        assert _hdl("markers_in_string_literal") == []

    def test_an_attribute_instance_is_not_reported(self) -> None:
        assert _hdl("attribute_instance") == []

    def test_a_verilog_2005_file_reports_its_comments(self) -> None:
        assert _hdl("verilog_2005_comments") == [2, 4]


class TestParsedComments:
    def test_a_grammar_named_directly_reads_its_comments(self) -> None:
        assert parsed_comments(sample("parsed/grammar_named_directly_reads_comments"), HCL) == [1]

    def test_two_comments_on_one_line_are_reported_once(self) -> None:
        assert javascript_comments(sample("parsed/two_comments_on_one_line_reported_once")) == [1]


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

    @pytest.mark.parametrize("suffix", CPP_SUFFIXES)
    def test_a_cpp_suffix_gets_the_cpp_reader(self, suffix: str) -> None:
        assert reader_for(f"src/counting{suffix}") is cpp_comments

    def test_a_c_file_gets_the_c_reader(self) -> None:
        assert reader_for("src/counting.c") is c_comments

    def test_a_c_file_does_not_get_the_cpp_reader(self) -> None:
        assert reader_for("src/counting.c") is not cpp_comments

    @pytest.mark.parametrize("suffix", SHELL_SUFFIXES)
    def test_a_shell_suffix_gets_the_shell_reader(self, suffix: str) -> None:
        assert reader_for(f"scripts/release{suffix}") is shell_comments

    @pytest.mark.parametrize("suffix", SYSTEMVERILOG_SUFFIXES)
    def test_a_hardware_description_suffix_gets_the_systemverilog_reader(
        self, suffix: str
    ) -> None:
        assert reader_for(f"rtl/counter{suffix}") is systemverilog_comments

    def test_a_map_file_gets_no_reader(self) -> None:
        assert reader_for("dist/app.js.map") is None

    def test_a_lock_file_gets_no_reader(self) -> None:
        assert reader_for("infra/.terraform.lock.hcl") is None

    def test_a_markdown_file_gets_no_reader(self) -> None:
        assert reader_for("README.md") is None

    def test_a_suffix_nobody_speaks_gets_no_reader(self) -> None:
        assert reader_for("notes.txt") is None


class TestReaderForGithubActions:
    @pytest.mark.parametrize("path", WORKFLOW_PATHS)
    def test_a_workflow_or_an_action_gets_the_workflow_reader(self, path: str) -> None:
        assert reader_for(path) is workflow_comments

    @pytest.mark.parametrize("path", PLAIN_YAML_PATHS)
    def test_any_other_yaml_file_gets_the_yaml_reader(self, path: str) -> None:
        assert reader_for(path) is yaml_comments


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

    def test_a_workflow_whose_python_step_will_not_parse_is_unreadable(self) -> None:
        text = sample("comments_in/workflow_python_step_will_not_parse")
        with pytest.raises(Unreadable):
            comments_in(".github/workflows/build.yml", text)


class TestFinding:
    def test_prints_as_path_and_line(self) -> None:
        assert str(Finding("src/counting.py", 2)) == "src/counting.py:2"

    def test_two_findings_on_the_same_line_are_the_same_finding(self) -> None:
        assert Finding("src/counting.py", 2) == Finding("src/counting.py", 2)
