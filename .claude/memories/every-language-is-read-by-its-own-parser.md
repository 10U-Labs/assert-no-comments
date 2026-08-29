# Every language is read by its own parser

A reader in `src/assert_no_comments/scanner.py` is a parser for the language it reads, never a walk over the characters. Python goes through `tokenize` and `ast`, YAML through `yaml.scan`, and JavaScript, TypeScript, TSX and HCL through their tree-sitter grammars.

The rule was bought rather than chosen. `marked_comments` walked a file character by character and asked `_opens_a_pattern` whether a `/` began a regular expression, guessing from the last non-space character before it. `<` was in that table, so the slash of a JSX closing tag looked like the start of a pattern and the walk swallowed the rest of the line, taking any comment on it. That is GitHub issue #2. Widening or narrowing the table moves which inputs are wrong; it does not stop there being inputs that are wrong, and the failure is silent in the direction that matters, because a missed comment leaves a job green and nobody re-reads a green job.

So a new language does not get a marker table. It gets a grammar, an entry in `READERS`, and a reader whose whole body is `parsed_comments(text, THAT_GRAMMAR)`. Dialects that read the same characters differently are separate grammars: `.tsx` is not `.ts` with elements in it, because `<string>y` asserts a type in one and opens an element in the other.

Two things this costs, both worth knowing before changing it.

A grammar per language is a dependency per language, and `tree-sitter-language-pack` is the one that looks like it would save that. It would ship 371 grammars to serve four, every one of them a version this package publishes and does not use, and the four it does use could no longer move independently.

An unterminated block comment is no longer reported. `marked_comments` reported it where it opened; a grammar sees an unterminated `/*` as text it cannot place and produces an `ERROR` node rather than a comment. The never-fail contract still holds — tree-sitter returns a tree instead of raising, so a broken JavaScript, TypeScript or HCL file gives findings rather than an exit code of 2 — but what a broken file yields is now whatever the grammar could still recognise. `test_a_file_that_will_not_parse_still_reports_what_it_can` in both the unit and integration tiers is where that is written down.

This was written on 2026-08-29, when issues #1 and #2 were closed.
