# assert-no-comments

Assert that nothing in a tree carries a comment or a docstring.

## Why

Prose beside code is never checked. The compiler does not read it, the tests do
not run it, and no linter asks whether it is still true, so it stops being true
and nothing says when. The reader who believes it then works from a program that
no longer exists, which is worse than having read nothing at all.

A rename is where the cost shows up first. Change one identifier and every
sentence naming it is now wrong, in files the change never touched, and the diff
gives no way to find them.

So this tool takes the other position: a name, a signature and the shape of a
function are the whole of what a reader gets. When that is not enough to say
what a thing holds or does, the thing is named or shaped wrong rather than
under-explained. The reasoning still gets written down, in the commit message
and the issue, each of which is dated and attached to a change instead of
sitting beside a line claiming to describe it forever.

## Installation

```bash
pip install assert-no-comments
```

## Usage

```bash
# Every tree this repository publishes
assert-no-comments .github/workflows etc lib scripts src test

# The same, leaving out code somebody else wrote
assert-no-comments .github/workflows etc lib scripts src test \
  --exclude 'src/www/spa/vendor/*'
```

### Options

| Option | Effect |
| --- | --- |
| `--exclude PATTERNS` | Comma-separated globs to leave out. |
| `--annotate` | Print each finding as a GitHub Actions `::error` annotation. |
| `--quiet` | Print nothing; report through the exit code. |
| `--count` | Print only how many findings there were. |
| `--verbose` | Print the files read, the findings and a summary. |
| `--fail-fast` | Stop at the first finding. |
| `--warn-only` | Always exit 0. |

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Nothing carries a comment |
| 1 | Something carries a comment |
| 2 | A tree was missing, unreadable, or would not parse |

## What counts as a comment

| Read as | Suffixes | Reported |
| --- | --- | --- |
| Python | `.py` | `#`, except a `#!` first line, and any module, class or function docstring |
| YAML | `.yml`, `.yaml` | `#` |
| GitHub Actions | `.yml` and `.yaml` in `.github/workflows`, `action.yml`, `action.yaml` | `#`, and each `run:` script's comments in its shell's language |
| OpenTofu | `.tf`, `.tfvars`, `.hcl` | `#`, `//`, and `/* */` |
| JavaScript | `.js`, `.mjs`, `.cjs`, `.jsx` | `//`, `/* */`, `{/* */}`, `<!--`, `-->` |
| TypeScript | `.ts`, `.mts`, `.cts` | `//`, `/* */`, `<!--`, and `-->` |
| TSX | `.tsx` | `//`, `/* */`, `{/* */}`, `<!--`, `-->` |
| C | `.c` | `//`, and `/* */` |
| C++ | `.cpp`, `.cc`, `.cxx`, `.c++`, `.cp`, `.C`, `.CPP`, `.tcc`, `.h`, `.hh`, `.hpp`, `.hxx`, `.h++`, `.hp`, `.H`, `.HPP` | `//`, and `/* */` |
| Shell | `.sh`, `.bash` | `#`, except a `#!` first line |
| SystemVerilog | `.sv`, `.svh`, `.v`, `.vh` | `//`, and `/* */` |
| Rust | `.rs` | `//`, `/* */`, and the doc comments `///`, `//!`, `/** */` and `/*! */` |

`{/* */}` is the third form because it is the only one JSX has among the
children of an element: a bare `/* */` there is text that renders.

`<!--` and `-->` are JavaScript's HTML-like comments, each running to the end of
its line like `//`. The JavaScript, TypeScript and TSX grammars all parse them,
though neither a module nor TypeScript accepts one, and either way the line is
reported: it is a comment, or it is not code that should be there. Inside a
string the marker is text, and `a --> b` is a decrement followed by a
comparison, so neither is reported.

`.tsx` is its own row rather than a fourth suffix on the TypeScript one because
the two are different dialects: `<string>y` asserts a type in one and opens an
element in the other, and a reader that guessed wrong would read past the rest
of the line.

`.c` is read by the C grammar, which parses a C++ keyword used as a name, such
as `int new`, where the C++ grammar can only recover from it. `.h` is read as
C++ because its suffix cannot say which of the two languages a header is
written in. The C++ grammar extends the C one and both write comments the same
way, so a C header parses as C++ unless it uses a C++ keyword as a name, and
even then the comments the grammar still recognises are reported.

Verilog is read by the SystemVerilog grammar, because IEEE 1800 took IEEE 1364
into itself in 2009. A Verilog file that uses a later SystemVerilog keyword such
as `logic` as a name will not parse, and the comments the grammar still
recognises are reported. `.map` stays out, though the grammar reads a library
map file, because `.map` is also the suffix of a JavaScript source map.

A workflow is a `.yml` or `.yaml` file directly inside a `.github/workflows`
directory, and an action is a file named `action.yml` or `action.yaml`. Both are
read as YAML, and each step's `run:` script is read again in the language of the
shell GitHub hands it to. A script whose shell's first word is `bash` or `sh` is
read as shell, one whose first word is `python` is read as Python, and one under
any other shell is left alone.

That shell is the one GitHub picks: the step's `shell`, else the job's
`defaults.run.shell`, else the workflow's, else the runner's default. The
default is `pwsh` when a label in the job's `runs-on` starts with `windows`, and
`bash` on any other runner, including one that `runs-on` names by an expression.

GitHub substitutes each `${{ }}` expression into the script's text before the
shell runs it, so each is read as a run of underscores of the same length, and a
comment after one on the same line is still found.

A `run:` written as a block scalar, `|` or `>`, is read from the file's own
lines, so each comment in it is reported at its own line. One written as a
quoted scalar, `'` or `"`, is read from the value YAML gives it, which is the
text GitHub hands the shell, and each comment in it is reported at the line
where the value starts: a quoted value that runs over several lines folds each
line break into a space, and a `\n` escape adds a row the file does not have, so
its rows cannot be mapped back to the file's lines. A plain one is not read
again, since YAML ends it at a `#` after a space and reports that `#` itself.

A file whose suffix names none of those is left alone, so a `.md` file is never
read: prose is the content of a markdown file rather than a gloss on a line of
code. `.terraform.lock.hcl` is left alone too, because OpenTofu writes its
header and nobody can delete it.

The end comment clang-format writes on the brace that closes a C++ namespace,
`// namespace a` after `namespace a` and `// namespace` after an anonymous one,
is not reported either. clang-format writes it, writes it again when it is
deleted from any namespace longer than one line, and corrects it when the
namespace is renamed, so it cannot become untrue, and a tree formatted by
clang-format could not otherwise pass both checks. Only that exact text on the
brace's own line is spared. Every other form is reported, `/* namespace a */`
and `//   namespace   a` included, and so is an end comment on the line below
the brace or one that names a different namespace.

A `#!` line opening a Python, JavaScript, TypeScript, shell or Rust file is not
reported either. It names the interpreter the kernel runs the file with, so a
wrong one fails the next run rather than going stale. The JavaScript and
TypeScript grammars parse it as a line of its own, and the Rust grammar parses
it as a `shebang` node rather than as a comment, while `tokenize` and the shell
grammar parse it as a comment, so the Python and shell readers spare it only
where the kernel reads it, as the first two characters of the file. Anywhere
else, even one space in, it is reported.

A docstring counts as a comment. It is the same prose in the same place, and the
fact that a language keeps it in `__doc__` does not make it any more likely to
still be true. A Rust doc comment is reported for the same reason: rustdoc
compiles the fenced code in one as a doctest, but nothing checks the prose
around it.

Every language is read by its own grammar, so nothing here decides what a
character is by looking at the characters beside it: Python through `tokenize`
and `ast`, YAML through the `yaml` scanner, and JavaScript, TypeScript, TSX,
OpenTofu, C, C++, shell, SystemVerilog and Rust through their tree-sitter
grammars. A `#` inside a Python string, a YAML quoted scalar or block scalar, an
HCL heredoc, or a shell quoted string, word, here-document or parameter
expansion is content. A `//` inside a JavaScript string, template literal or
regular expression is content, a `/` after a name is division, the `/` closing a
JSX tag is neither, and text between JSX tags renders on the page rather than
commenting on it. A `//` inside a C, C++, SystemVerilog or Rust string, or a C++
or Rust raw string, is content, and `(*` opens a SystemVerilog attribute rather
than a comment. A Rust block comment nests, so `/* a /* b */ c */` is one
comment, reported at the line it starts on. A comment in the body of a C or C++
`#define`, or in the text of a SystemVerilog `` `define ``, is still a comment:
the grammar reads it as part of the body, and this tool finds it by parsing the
body again. One in a Rust `macro_rules!` body needs no second parse, since the
grammar reads it as a comment in the macro's tokens. Each of those is a question
about where in the file the character sits, which is what a parser knows and a
marker table does not.

A Python or YAML file that will not parse is an error rather than a file with
nothing in it, and so is a workflow or an action whose `python` step will not
parse. A JavaScript, TypeScript, TSX, OpenTofu, C, C++, shell, SystemVerilog or
Rust file that will not parse is read as far as its grammar gets: the comments
it can still recognise are reported, so a broken file gives findings rather than
an exit code of 2.

One limit belongs to the C and C++ grammars rather than to this tool. They end
the body of a `#define` at the first `/*`, even one inside a string literal, so
in `#define H "a /* b"` they open a block comment that runs to the next `*/`
anywhere in the file. That `#define` line is reported whether it carries a
comment or not, and every comment between it and that `*/` is lost inside the
false one. The rule comes from `tree-sitter-c`, which `tree-sitter-cpp` builds
on, and is reported there as [tree-sitter/tree-sitter-c#335][preproc-arg].

[preproc-arg]: https://github.com/tree-sitter/tree-sitter-c/issues/335

Two limits belong to the SystemVerilog grammar. It ends the text of a
`` `define `` at the first newline with no backslash before it, even inside a
block comment or a triple-quoted string, and reads the rest of that comment or
string as code. In `` `define H(x) or /* a `` followed by `b */ #x`, the block
comment opening on the first line is lost, and in `` `define T """ `` followed
by `x // y`, the `// y` inside the string is reported. Both are reported
upstream, as [gmlarumbe/tree-sitter-systemverilog#87][macro-block] and
[gmlarumbe/tree-sitter-systemverilog#88][macro-string].

[macro-block]: https://github.com/gmlarumbe/tree-sitter-systemverilog/issues/87
[macro-string]: https://github.com/gmlarumbe/tree-sitter-systemverilog/issues/88

## What is walked

A directory argument is read recursively. Hidden directories are read, because
`.github/workflows` is one of the trees most worth checking. `.git`,
`__pycache__` and `node_modules` are skipped, and everything else you want left
out goes in `--exclude`.

The usual thing to exclude is code somebody else wrote:

```bash
assert-no-comments src --exclude 'src/www/spa/vendor/*'
```

Nobody here can answer for a vendored library, and a finding against one is
answerable by nobody, so it is not worth reporting.

## GitHub Actions

```yaml
- name: Assert nothing this repository publishes carries a comment
  uses: 10U-Labs/assert-no-comments@latest
  with:
    exclude: src/www/spa/vendor/*
    trees: .github/workflows etc lib scripts src test
```

`annotate` defaults to true there, so each finding lands on the line it names in
the diff.

## License

Apache-2.0
