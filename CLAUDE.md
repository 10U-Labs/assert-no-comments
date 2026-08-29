# Working in assert-no-comments

## Overview

The standing conventions for working in this repository. A rule is here only if working from the tree alone would get it wrong: whatever `release.yml`, `README.md`, the code or `git log` already answers is not repeated here, because a second copy goes stale with nothing to catch it.

## Conventions

### Commits

#### A rejected push is fixed forward

Answer a red run with a follow-up commit; do not amend and force-push. Every check is a job of its own running in parallel with the rest, so a red run names every check that failed rather than the earliest one. Read the whole list and answer all of it in one commit.

#### One closing line per issue

An issue is closed by the commit that fixes it, through a `Closes #N` line, one line per issue. GitHub binds the keyword to a single reference, so `Closes #1 and #2` closes #1 and leaves #2 open.

#### One issue, one commit

One issue is solved by one commit and one push. An issue that cannot be done in one commit is two issues, and filing the second is the answer rather than spreading one issue across pushes. Two issues share a commit only where the fix for one is contained in the fix for the other.

#### Push each change as it is finished, once

A finished change is pushed straight away rather than held back to travel with the next one — nothing is verified until it is on `main`. Once, though: both workflows cancel the run in progress when a second push lands on the same ref, and the tree is still verified by the later run but the cancelled commit loses its own release, because `release` never gets its `needs`.

#### Straight to main

Work goes straight to `main` as direct commits. Do not create a feature branch, do not open a pull request, and do not structure advice around a review cycle. CI is the only review there is, and the tests land in the same commit as the code they cover.

### Docstrings

#### Write the docstring, and expect the job to be red

`release.yml` runs this package over its own tree and that job is red, because `pylint-src` and `pylint-test` gate on `--fail-on=C,R,W` with the `missing-*-docstring` checks on: the prose the tool forbids is the prose pylint requires. Write the docstring — pylint is the gate that is actually enforced — and read a red `assert-no-comments` as the standing state of the tree rather than something your push introduced. Which of the two rules wins is the open question in #3, and it is not answered in passing by a commit about something else.

### Issues

#### An issue states one solution

Its `Proposed Solution` names one change — this function, this file, this dependency — because the issue is the instruction to whoever picks it up and they were not in the conversation that produced it. Never file "either X or Y", a menu with a recommendation, or a question left for the reader. Naming the alternative that lost is still worth writing; leaving the choice open is not.

#### The seven sections

Seven sections in a fixed order: "Problem", "Why Unit Tests Did Not Catch It?", "Why Integration Tests Did Not Catch It?", "Why E2E Tests Did Not Catch It?", "Why Static Analysis Jobs Did Not Catch It?", "Which Regression Tests Would Prevent This from Happening Again?", "Proposed Solution". Every issue has all seven; where a tier could not have caught the defect, saying so is the finding rather than a reason to drop the section. The regression section names the coverage owed, each test by its tier and its assertion, and is separate from the solution so that a fix cannot ship with the coverage folded into its last paragraph.

### Markdown

#### A paragraph is one line

Nothing here holds a line to a column count, so a paragraph is written as one line and the reader's editor wraps it — in markdown files and in commit message bodies alike. Hard wrapping is what makes a one-word edit arrive as a rewritten paragraph, because the words after it move onto the lines below and the diff marks all of them.

### Readers

#### Every language is read by its own parser

A reader in `src/assert_no_comments/scanner.py` is a parser for the language it reads, never a walk over the characters. A new language gets a grammar, an entry in `READERS`, and a reader whose whole body is `parsed_comments(text, THAT_GRAMMAR)` — never a marker table — and a dialect that reads the same characters differently gets a grammar of its own rather than a further suffix on the one it resembles. What that bought and what it cost is in [every-language-is-read-by-its-own-parser](.claude/memories/every-language-is-read-by-its-own-parser.md); read it before adding a language, and before reaching for `tree-sitter-language-pack`.

### Tests

#### A conftest with no fixture in it stays

`test/integration/conftest.py` and `test/e2e/conftest.py` hold a docstring and nothing else, and they stay. The file is what tells whoever writes the next fixture that this level exists to hold one; left to itself a session writes setup into the test file already open in front of it. They cannot be emptied to zero bytes, because `missing-module-docstring` is a C and `pylint-test` gates on C.

#### Cover every tier the change touches

`test/unit/` for the readers and the CLI helpers, `test/integration/` for the CLI driven over a real tree, `test/e2e/` for the installed console script run the way a workflow step runs it. Unit and integration each gate on full branch coverage on their own rather than on the two together. `e2e-tests` carries no coverage gate and cannot, since it runs the command in another process, so a line reachable only through the console script is reached by `run_cli`, the in-process fixture in `test/conftest.py`, and asserted again through the subprocess.

#### One assert per pytest

Every test asserts once. A test name is a sentence saying what is true, `test_a_hash_inside_a_string_is_not_reported`, and carries the docstring `pylint-test` requires.

#### Test first

The test is written first, then the code that makes it pass. Test-first is authoring order — the red and the green observations belong to CI, since nothing runs locally.

#### Trees under test go in samples

`test/samples.py` holds the sample trees and all three tiers import from it. A tier that assembles its own tree inline is how two tiers come to disagree about what a clean project looks like.

### Verification

#### CI is the source of truth

Do not run tests, linters or builds locally to verify a change — write the code and the tests, commit, push to `main`, and read the run with `gh run list`, `gh run watch` and `gh run view --log-failed`. The jobs between them want Python, Node, four tree-sitter grammars and eight tools this machine does not otherwise carry, and CI checks every gate at once. Reading the code locally is still right and cheap: `grep` and file reads are how the useful findings surface. A green push publishes to PyPI and force-moves `latest` by itself, so there is no version to hold back and a commit that should not be published is a commit that should not be pushed.

#### Configuration goes on the command line

There is no `.pylintrc`, no `mypy.ini`, no `.yamllint` and no inline `pylint: disable` anywhere, and there cannot be: `assert-no-linter-config-files` and `assert-no-inline-directives` fail the run over either. Every option a tool takes is written into the step that runs it.

#### Finding the run

Find the run by the full forty-character hash from `git rev-parse HEAD`. `gh run list --commit` returns an empty list for the short hash `git log --oneline` prints, which is indistinguishable from a run that has not started. A push starts one workflow or both, depending on what it touched, and the change is done when each run that started is green rather than when the first one is.

#### Keys in a YAML file are alphabetical

`yamllint` runs `--strict` with `key-ordering`, so every mapping in every YAML file here is in alphabetical order — which is why `name` and `on` sit at the bottom of a workflow file, under `jobs`. A new job goes in its alphabetical place, and in the `needs` list of `release`, sorted the same way.

#### Path filters are not shell globs

A path in a workflow's `paths` filter is not a shell glob. GitHub reads `**` as any run of characters, `/` included, so `**/*.md` needs a slash to match and reaches no file at the root of the repository. The form that reaches both is `'**.md'`, quoted because a bare `*` opens a YAML alias. `node` reads those two patterns the other way, which is why the `markdownlint '**/*.md'` step reads files that its own trigger would not have started it for.

## Notes

### Where a new convention goes

A convention learned in a session belongs in this file, and in a note under `.claude/memories/` where it needs more than a paragraph, linked from the section that summarises it. Nothing is kept in the session tool's own memory directory under the home directory: those files belong to one machine, are unversioned, and are invisible to everyone else working here.
