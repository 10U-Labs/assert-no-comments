---
name: a-sample-is-a-file-not-a-literal
description: "Source text handed to a reader is a file under its tier's samples/ directory, ending as the file it stands for ends and loaded with sample() by its full name; every checker that reads that ending leaves test/*/samples/ out on its command line"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T03:25:25.536Z
---

# A sample is a file, not a literal

Source text handed to a reader is a file under the `samples/` directory of the
tier that reads it, named for the test that reads it, and loaded with
`sample()` by its full name. The samples that make up a project tree live in
each CLI tier's `samples/project/`, because they belong to no single test.

A sample ends as the file it stands for ends: in the language its folder names,
or else as the path its test writes it to or hands to the reader with it. A
sample standing for a file with no ending, such as a `Makefile`, has none.

Every CI job whose checker reads one of those endings leaves `test/*/samples/`
out with a flag on its command line: the `exclude` input of the
`assert-no-comments` job, `--exclude`, `--ignore`, `--ignore-paths`, or the
`ignore` key in yamllint's `--config-data`.

**Why:** a file's ending says what the file holds, and `.txt` around Python
says something false. The skips keep the samples, which carry comments and in
places do not parse, away from checkers that are not meant to read them. They
sit on the command line because `assert-no-linter-config-files` fails the build
over a checker's config file.

**How to apply:** never write source text as a string literal in a test. When a
job is added whose checker reads a sample's ending, give it the same skip.
