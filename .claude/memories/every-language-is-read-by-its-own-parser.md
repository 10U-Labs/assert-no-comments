---
name: every-language-is-read-by-its-own-parser
description: A reader in scanner.py is a parser for its language, never a walk over the characters; read before adding a language or reaching for tree-sitter-language-pack
metadata:
  type: project
---

# Every language is read by its own parser

A reader in `src/assert_no_comments/scanner.py` is a parser for the language it
reads, never a walk over the characters. Python goes through `tokenize` and
`ast`, YAML through `yaml.scan`, and JavaScript, TypeScript, TSX, HCL, C, C++,
Bash, SystemVerilog and Rust through their tree-sitter grammars.

A workflow's `run:` script is the one place the text is changed before a grammar
sees it: `workflow_comments` replaces each `${{ }}` expression with underscores
of the same length. That is not a marker table. GitHub performs the same
substitution on the text before any shell parses it, and without it
`tree-sitter-bash` loses a comment that follows an expression on its line and
`ast` rejects a Python step that assigns one.

A walk over the characters has to guess what each one is from the ones beside
it. Whether a `/` opens a regular expression depends on what came before it, and
a table of the characters that may come before a pattern is wrong somewhere:
with `<` in it, the slash of a JSX closing tag opens a pattern that swallows the
rest of the line and any comment on it. Widening or narrowing the table moves
which inputs are wrong; it does not stop there being inputs that are wrong, and
the failure is silent in the direction that matters, because a missed comment
leaves a job green and nobody re-reads a green job.

So a new language does not get a marker table. It gets a grammar, an entry in
`READERS`, and a reader whose whole body is `parsed_comments(text,
THAT_GRAMMAR)`, with at most a `spared` predicate besides. Dialects that read
the same characters differently are separate grammars: `.tsx` is not `.ts` with
elements in it, because `<string>y` asserts a type in one and opens an element
in the other.

A predicate may spare only text that cannot go stale unnoticed, and it picks
that text out by its place in the tree and its own text, never by the
characters around it. There are two kinds. A comment a formatter writes and
keeps true is one: `closes_its_namespace` spares the end comment clang-format
puts on a namespace's brace. A shebang is the other: the Bash grammar calls
`#!/bin/sh` a comment, but the kernel reads it on every `execve`, so a wrong
one fails the next run, and `is_a_shebang` spares it where it opens the file. A
comment that is only conventional does not qualify, however common: a person
wrote it, nothing corrects it, and it drifts like any other, which is why
`#endif  // GUARD_H_` is still reported though Google's style guide shows it.

Three things this costs, all worth knowing before changing it.

A grammar per language is a dependency per language, and
`tree-sitter-language-pack` is the one that looks like it would save that. It
would ship 371 grammars to serve nine, every one of them a version this
package publishes and does not use, and the nine it does use could no longer
move independently.

A grammar's own defect stays. `tree-sitter-c`, which `tree-sitter-cpp` builds
on, ends a `#define` body at the first `/*` even inside a string, and
`tree-sitter-systemverilog` ends a `` `define ``'s text at a newline inside a
block comment or a triple-quoted string. The only workaround is reading
characters. So each defect is written in `README.md` and pinned by a unit test
that turns red when a grammar release fixes it, rather than patched here.

An unterminated block comment is not reported. A grammar sees an unterminated
`/*` as text it cannot place and produces an `ERROR` node rather than a comment.
The never-fail contract still holds — tree-sitter returns a tree instead of
raising, so a broken JavaScript, TypeScript, HCL, C, C++, Bash, SystemVerilog
or Rust file gives findings rather than an exit code of 2 — but what a broken
file yields is whatever the grammar could still recognise.
`test_a_file_that_will_not_parse_still_reports_what_it_can` in both the unit and
integration tiers is where that is written down.
