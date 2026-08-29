"""Unit tests for the per-language comment readers."""

from __future__ import annotations

import pytest

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


@pytest.mark.unit
class TestPythonComments:
    """Reading a Python file."""

    def test_a_comment_on_a_line_of_its_own_is_reported(self) -> None:
        """A whole-line comment is a finding."""
        assert python_comments("# one\nx = 1\n") == [1]

    def test_a_comment_after_code_on_the_same_line_is_reported(self) -> None:
        """A trailing comment is a finding on the line it trails."""
        assert python_comments("x = 1\ny = 2  # two\n") == [2]

    def test_a_hash_inside_a_string_is_not_reported(self) -> None:
        """A hash the tokeniser reads as string content is not a comment."""
        assert python_comments('x = "# not a comment"\n') == []

    def test_a_module_docstring_is_reported(self) -> None:
        """A module docstring is prose beside code."""
        assert python_comments('"""What this module is for."""\nx = 1\n') == [1]

    def test_a_function_docstring_is_reported(self) -> None:
        """A function docstring is prose beside code."""
        assert python_comments('def f():\n    """What f does."""\n    return 1\n') == [2]

    def test_a_class_docstring_is_reported(self) -> None:
        """A class docstring is prose beside code."""
        assert python_comments('class C:\n    """What C holds."""\n\n    x = 1\n') == [2]

    def test_an_async_function_docstring_is_reported(self) -> None:
        """An async function docstring is prose beside code."""
        assert python_comments('async def f():\n    """What f does."""\n    return 1\n') == [2]

    def test_a_file_with_nothing_in_it_reports_nothing(self) -> None:
        """An empty module has no body to read a docstring from."""
        assert python_comments("") == []

    def test_a_statement_that_is_not_a_docstring_is_not_reported(self) -> None:
        """An assignment opening a module is code, not prose."""
        assert python_comments("x = 1\n") == []

    def test_a_number_standing_alone_is_not_read_as_a_docstring(self) -> None:
        """A bare constant that is not a string is not a docstring."""
        assert python_comments("def f():\n    1\n") == []

    def test_a_string_that_is_not_the_first_statement_is_not_reported(self) -> None:
        """A string later in a body is a value, not a docstring."""
        assert python_comments("def f():\n    x = 1\n    'later'\n") == []


@pytest.mark.unit
class TestYamlComments:
    """Reading a YAML file."""

    def test_a_comment_is_reported(self) -> None:
        """Anything the scanner leaves uncovered is a comment."""
        assert yaml_comments("---\njobs:\n  # why\n  a: 1\n") == [3]

    def test_a_hash_inside_a_block_scalar_is_not_reported(self) -> None:
        """A hash inside a block scalar is content."""
        assert yaml_comments('---\nrun: >-\n  echo "# not a comment"\n') == []

    def test_a_hash_inside_a_quoted_string_is_not_reported(self) -> None:
        """A hash inside a quoted scalar is content."""
        assert yaml_comments('---\nname: "a # b"\n') == []

    def test_a_file_with_nothing_in_it_reports_nothing(self) -> None:
        """An empty document carries no comment."""
        assert yaml_comments("") == []


@pytest.mark.unit
class TestHclComments:
    """Reading an OpenTofu or Terraform file."""

    def test_a_hash_comment_is_reported(self) -> None:
        """A hash runs a comment to the end of the line."""
        assert hcl_comments('# why\nresource "a" "b" {}\n') == [1]

    def test_a_double_slash_comment_is_reported(self) -> None:
        """A double slash runs a comment to the end of the line."""
        assert hcl_comments('resource "a" "b" {}\n// why\n') == [2]

    def test_a_block_comment_is_reported(self) -> None:
        """A block comment is a finding on the line it opens."""
        assert hcl_comments("locals {\n  /* why\n     more why */\n}\n") == [2]

    def test_a_hash_inside_a_string_is_not_reported(self) -> None:
        """A hash the grammar reads as string content is not a comment."""
        assert hcl_comments('bucket = "a#b"\n') == []

    def test_an_escaped_quote_does_not_end_a_string(self) -> None:
        """A backslash escapes the quote that would have closed the string."""
        assert hcl_comments('bucket = "a\\"#b"\n') == []

    def test_a_hash_inside_a_heredoc_is_not_reported(self) -> None:
        """A hash inside a heredoc is content."""
        assert hcl_comments("policy = <<EOT\n# not a comment\nEOT\n") == []

    def test_a_file_that_will_not_parse_still_reports_what_it_can(self) -> None:
        """A broken file is read as far as the grammar gets rather than failing."""
        assert hcl_comments('# why\nresource "a" {\n') == [1]


@pytest.mark.unit
class TestJavascriptComments:
    """Reading a JavaScript or JSX file."""

    def test_a_comment_is_reported(self) -> None:
        """A double slash runs a comment to the end of the line."""
        assert javascript_comments("const a = 1;\n// why\n") == [2]

    def test_a_block_comment_is_reported(self) -> None:
        """A block comment is a finding on the line it opens."""
        assert javascript_comments("const a = 1;\n/* why\n   more why */\n") == [2]

    def test_a_double_slash_inside_a_string_is_not_reported(self) -> None:
        """A URL inside a string is content."""
        assert javascript_comments('const a = "https://example.com";\n') == []

    def test_a_double_slash_inside_a_template_literal_is_not_reported(self) -> None:
        """A backtick opens a string the grammar reads to its end."""
        assert javascript_comments("const a = `https://${host}`;\n") == []

    def test_a_double_slash_inside_a_pattern_is_not_reported(self) -> None:
        """An escaped slash inside a regular expression is pattern content."""
        assert javascript_comments("const a = /https:\\/\\/x/;\n") == []

    def test_a_slash_inside_a_character_class_does_not_end_the_pattern(self) -> None:
        """A slash between brackets is pattern content."""
        assert javascript_comments("const a = /[a-z/]+/;\n") == []

    def test_a_comment_after_a_pattern_is_reported(self) -> None:
        """A pattern the grammar closes leaves the comment after it visible."""
        assert javascript_comments("const a = /[a-z/]+/; // why\n") == [1]

    def test_a_comment_after_a_division_is_reported(self) -> None:
        """A slash after a name divides, so the comment after it is a comment."""
        assert javascript_comments("const a = b / c; // why\n") == [1]

    def test_a_comment_after_a_closing_element_is_reported(self) -> None:
        """The slash of a JSX closing tag does not open a pattern."""
        assert javascript_comments("const El = (\n  <div>\n    a\n  </div> // why\n);\n") == [4]

    def test_a_comment_after_a_self_closing_element_is_reported(self) -> None:
        """The slash of a self-closing JSX tag does not open a pattern."""
        assert javascript_comments("const El = <Foo prop={x} />; /* why */\n") == [1]

    def test_a_comment_braced_inside_an_element_is_reported(self) -> None:
        """A braced block comment is how JSX carries a comment among children."""
        assert javascript_comments("const El = (\n  <div>\n    {/* why */}\n  </div>\n);\n") == [3]

    def test_markers_in_the_text_of_an_element_are_not_reported(self) -> None:
        """Text between JSX tags renders, so it is content rather than a comment."""
        assert javascript_comments("const El = <div>a // not a comment</div>;\n") == []

    def test_a_comment_on_the_last_line_with_no_line_break_is_reported(self) -> None:
        """A file ending mid-comment still reports it."""
        assert javascript_comments("// why") == [1]

    def test_a_file_that_will_not_parse_still_reports_what_it_can(self) -> None:
        """A broken file is read as far as the grammar gets rather than failing."""
        assert javascript_comments("const a = (((\n// why\n") == [2]


@pytest.mark.unit
class TestTypescriptComments:
    """Reading a TypeScript file."""

    def test_a_comment_is_reported(self) -> None:
        """A double slash runs a comment to the end of the line."""
        assert typescript_comments("const a: string = 'x'; // why\n") == [1]

    def test_a_documentation_block_is_reported(self) -> None:
        """A doc block is prose beside code like any other block comment."""
        assert typescript_comments("interface A {\n  /** why */\n  b: string;\n}\n") == [2]

    def test_a_type_assertion_does_not_hide_the_comment_after_it(self) -> None:
        """Angle brackets assert a type here rather than opening an element."""
        assert typescript_comments("const a = <string>y;\n// why\n") == [2]


@pytest.mark.unit
class TestTsxComments:
    """Reading a TSX file."""

    def test_a_comment_is_reported(self) -> None:
        """A double slash runs a comment to the end of the line."""
        assert tsx_comments("const a = <div />;\n// why\n") == [2]

    def test_a_comment_after_a_closing_element_is_reported(self) -> None:
        """The slash of a JSX closing tag does not open a pattern."""
        assert tsx_comments("const El = (\n  <div>\n    a\n  </div> // why\n);\n") == [4]

    def test_a_comment_braced_inside_an_element_is_reported(self) -> None:
        """A braced block comment is how TSX carries a comment among children."""
        assert tsx_comments("const El = (\n  <div>\n    {/* why */}\n  </div>\n);\n") == [3]


@pytest.mark.unit
class TestParsedComments:
    """The shared reader every grammar language is built from."""

    def test_a_grammar_named_directly_reads_its_comments(self) -> None:
        """A reader is a grammar and the walk that pulls the comments out of it."""
        assert parsed_comments("# why\nbucket = 1\n", HCL) == [1]

    def test_two_comments_on_one_line_are_reported_once(self) -> None:
        """A line is a finding at most once, however many comments it holds."""
        assert javascript_comments("/* a */ /* b */\n") == [1]


@pytest.mark.unit
class TestReaderFor:
    """Choosing a reader by file suffix."""

    def test_a_python_file_gets_the_python_reader(self) -> None:
        """A .py suffix names Python."""
        assert reader_for("src/counting.py") is python_comments

    def test_a_yaml_file_gets_the_yaml_reader(self) -> None:
        """A .yaml suffix names YAML, as .yml does."""
        assert reader_for("etc/config.yaml") is yaml_comments

    def test_an_opentofu_file_gets_the_hcl_reader(self) -> None:
        """A .tf suffix names HCL."""
        assert reader_for("infra/main.tf") is hcl_comments

    def test_a_module_javascript_file_gets_the_javascript_reader(self) -> None:
        """An .mjs suffix names JavaScript, as .js does."""
        assert reader_for("src/app.mjs") is javascript_comments

    def test_a_jsx_file_gets_the_javascript_reader(self) -> None:
        """The JavaScript grammar covers JSX, so .jsx needs no grammar of its own."""
        assert reader_for("src/App.jsx") is javascript_comments

    def test_a_typescript_file_gets_the_typescript_reader(self) -> None:
        """A .ts suffix names TypeScript."""
        assert reader_for("src/counting.ts") is typescript_comments

    def test_a_declaration_file_gets_the_typescript_reader(self) -> None:
        """A .d.ts name ends in .ts, so it needs no entry of its own."""
        assert reader_for("src/vite-env.d.ts") is typescript_comments

    def test_a_module_typescript_file_gets_the_typescript_reader(self) -> None:
        """An .mts suffix names TypeScript, as .ts does."""
        assert reader_for("src/app.mts") is typescript_comments

    def test_a_commonjs_typescript_file_gets_the_typescript_reader(self) -> None:
        """A .cts suffix names TypeScript, as .ts does."""
        assert reader_for("src/app.cts") is typescript_comments

    def test_a_tsx_file_gets_the_tsx_reader(self) -> None:
        """A .tsx suffix names TSX, which is its own dialect."""
        assert reader_for("src/App.tsx") is tsx_comments

    def test_tsx_and_typescript_are_read_by_different_grammars(self) -> None:
        """The two dialects read the same characters differently."""
        assert reader_for("src/App.tsx") is not reader_for("src/app.ts")

    def test_a_lock_file_gets_no_reader(self) -> None:
        """A file OpenTofu writes is nobody's source."""
        assert reader_for("infra/.terraform.lock.hcl") is None

    def test_a_markdown_file_gets_no_reader(self) -> None:
        """Prose is the content of a .md file rather than a gloss on it."""
        assert reader_for("README.md") is None

    def test_a_suffix_nobody_speaks_gets_no_reader(self) -> None:
        """The table is a decision about the languages in it and nothing else."""
        assert reader_for("notes.txt") is None


@pytest.mark.unit
class TestCommentsIn:
    """Reading one file by path and content."""

    def test_a_finding_names_the_file_and_the_line(self) -> None:
        """A finding carries the path it was found in."""
        assert comments_in("src/counting.py", "x = 1\n# why\n") == [Finding("src/counting.py", 2)]

    def test_a_file_no_reader_speaks_is_left_alone(self) -> None:
        """A suffix naming no language reports nothing."""
        assert comments_in("README.md", "# A heading\n") == []

    def test_a_file_that_will_not_parse_is_unreadable(self) -> None:
        """A broken file raises rather than reporting nothing."""
        with pytest.raises(Unreadable):
            comments_in("src/counting.py", "def f(\n")

    def test_a_yaml_file_that_will_not_parse_is_unreadable(self) -> None:
        """A broken YAML file raises rather than reporting nothing."""
        with pytest.raises(Unreadable):
            comments_in("etc/config.yml", '"unclosed\n')


@pytest.mark.unit
class TestFinding:
    """How a finding prints."""

    def test_prints_as_path_and_line(self) -> None:
        """A finding reads as path:line."""
        assert str(Finding("src/counting.py", 2)) == "src/counting.py:2"

    def test_two_findings_on_the_same_line_are_the_same_finding(self) -> None:
        """A finding is its path and its line and nothing else."""
        assert Finding("src/counting.py", 2) == Finding("src/counting.py", 2)
