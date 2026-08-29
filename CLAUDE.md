# Working in assert-no-comments

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
  - [Commits](#commits)
    - [A rejected push is fixed forward](#a-rejected-push-is-fixed-forward)
    - [One closing line per issue](#one-closing-line-per-issue)
    - [One issue, one commit](#one-issue-one-commit)
    - [Push once and let the run finish](#push-once-and-let-the-run-finish)
    - [Straight to main](#straight-to-main)
  - [Issues](#issues)
    - [An issue states one solution](#an-issue-states-one-solution)
    - [The seven sections](#the-seven-sections)
  - [Markdown](#markdown)
    - [A paragraph wraps at eighty columns](#a-paragraph-wraps-at-eighty-columns)
    - [The table of contents stays](#the-table-of-contents-stays)
  - [Readers](#readers)
    - [Every language is read by its own parser](#every-language-is-read-by-its-own-parser)
  - [Tests](#tests)
    - [A conftest with no fixture in it stays](#a-conftest-with-no-fixture-in-it-stays)
    - [A sample is a file, not a literal](#a-sample-is-a-file-not-a-literal)
    - [A tier is a directory, not a marker](#a-tier-is-a-directory-not-a-marker)
    - [Anything importable lives outside conftest](#anything-importable-lives-outside-conftest)
    - [Cover every tier the change touches](#cover-every-tier-the-change-touches)
    - [Test first](#test-first)
  - [Verification](#verification)
    - [CI is the source of truth](#ci-is-the-source-of-truth)
    - [Finding the run](#finding-the-run)
    - [Path filters are not shell globs](#path-filters-are-not-shell-globs)
- [Notes](#notes)
  - [Where a new convention goes](#where-a-new-convention-goes)

## Overview

The standing conventions for working in this repository. A rule is here only if
working from the tree alone would get it wrong: whatever `release.yml`,
`README.md`, the code or `git log` already answers is not repeated here, because
a second copy goes stale with nothing to catch it.

## Conventions

### Commits

#### A rejected push is fixed forward

Answer a red run with a follow-up commit; do not amend and force-push. Every
check is a job of its own running in parallel with the rest, so a red run names
every check that failed rather than the earliest one. Read the whole list and
answer all of it in one commit.

#### One closing line per issue

An issue is closed by the commit that fixes it, through a `Closes #N` line, one
line per issue. GitHub binds the keyword to a single reference, so `Closes #1
and #2` closes #1 and leaves #2 open.

#### One issue, one commit

One issue is solved by one commit and one push. An issue that cannot be done in
one commit is two issues, and filing the second is the answer rather than
spreading one issue across pushes. Two issues share a commit only where the fix
for one is contained in the fix for the other.

#### Push once and let the run finish

Both workflows cancel the run in progress when a second push lands on the same
ref. The tree is still verified, by the later run, but the cancelled commit
loses its own release, because `release` never gets its `needs`. Push once per
issue and read that run.

#### Straight to main

Work goes straight to `main` as direct commits. Do not create a feature branch,
do not open a pull request, and do not structure advice around a review cycle.
CI is the only review there is, and the tests land in the same commit as the
code they cover.

### Issues

#### An issue states one solution

Its `Proposed Solution` names one change — this function, this file, this
dependency — because the issue is the instruction to whoever picks it up and
they were not in the conversation that produced it. Never file "either X or Y",
a menu with a recommendation, or a question left for the reader. Naming the
alternative that lost is still worth writing; leaving the choice open is not.

#### The seven sections

Seven sections in a fixed order: "Problem", "Why Unit Tests Did Not Catch It?",
"Why Integration Tests Did Not Catch It?", "Why E2E Tests Did Not Catch It?",
"Why Static Analysis Jobs Did Not Catch It?", "Which Regression Tests Would
Prevent This from Happening Again?", "Proposed Solution". Every issue has all
seven; where a tier could not have caught the defect, saying so is the finding
rather than a reason to drop the section. The regression section names the
coverage owed, each test by its tier and its assertion, and is separate from the
solution so that a fix cannot ship with the coverage folded into its last
paragraph.

### Markdown

#### A paragraph wraps at eighty columns

A paragraph in a `.md` file is hard-wrapped at eighty columns, and a paragraph
is the only thing that is: a heading, a table row, a fenced block and an entry
in the table of contents keep whatever width they have, and a commit message
body is still written as one line, because none of those is a markdown
paragraph.

Nothing checks it. `documentation.yml` passes `--disable MD013`, and turning
that rule on would cap every line rather than every paragraph — eighty is its
own default, but exempting tables and fenced blocks takes a config file, and
`assert-no-linter-config-files` names markdownlint. So the cap is kept by
whoever writes the paragraph, at the cost hard wrapping always has: a one-word
edit reflows the words after it and the diff marks lines the edit did not mean
to change. Rewrap the whole paragraph when that happens rather than leaving one
line long, because half a wrapped paragraph reads worse than either.

#### The table of contents stays

The list at the top of this file is the exception to the rule above it: it is
navigation for a reader of this file rather than a claim about anything else in
the tree, and it is rewritten in the same edit as the headings it lists, so it
cannot drift from them the way a copied fact drifts from its source. A session
that has just read the rule about second copies will reach for it first. Leave
it, and update it.

### Readers

#### Every language is read by its own parser

A reader in `src/assert_no_comments/scanner.py` is a parser for the language it
reads, never a walk over the characters. A new language gets a grammar, an entry
in `READERS`, and a reader whose whole body is `parsed_comments(text,
THAT_GRAMMAR)` — never a marker table — and a dialect that reads the same
characters differently gets a grammar of its own rather than a further suffix on
the one it resembles. What that bought and what it cost is in
[every-language-is-read-by-its-own-parser](.claude/memories/every-language-is-read-by-its-own-parser.md);
read it before adding a language, and before reaching for
`tree-sitter-language-pack`.

### Tests

#### A conftest with no fixture in it stays

`test/integration/conftest.py` and `test/e2e/conftest.py` are zero bytes, and
they stay. The file is what tells whoever writes the next fixture that this
level exists to hold one; left to itself a session writes setup into the test
file already open in front of it. Zero bytes is what an empty file is here: a
docstring, a `pass` or a blank line to stand in for content is content, and the
file is empty or it is not. Nothing in CI fails when one of them is deleted, so
the file is kept for the reader rather than for a gate.

#### A sample is a file, not a literal

Source text handed to a reader is a `.txt` file under the `samples/` directory
of the tier that reads it, named for the test that reads it, and loaded with
`sample()`. `.txt` is in no gate's glob and in no entry of `READERS`, so a
sample carrying a comment sits in the tree untouched by the tool that would
otherwise fail the build over it, and needs no `--exclude`. The eight that make
up the project tree live in `samples/project/`, because they belong to no single
test and both CLI tiers write them.

#### A tier is a directory, not a marker

A test belongs to the tier whose directory it sits in, and that is the only
thing that says so. Do not mark it: 49710d3 deleted the three `pytest.mark`
markers and the `pytest_configure` that registered them, because no step in
`release.yml` passes `-m` — each names `test/unit/`, `test/integration/` or
`test/e2e/` — so the registration existed only to keep the decorators from
failing the jobs under `--pythonwarnings=error`, and each of the 40 decorators
restated by hand the directory its file was already in, which nothing checked. A
marker that has to agree with a path is a comment that has to agree with its
code. Select a tier by naming its directory, and add a marker only where the
thing being selected is not a directory. `usefixtures` and the rest of pytest's
builtins are unaffected; those it registers itself.

#### Anything importable lives outside conftest

`conftest.py` holds fixtures and hooks, which pytest finds by itself; a test
module never imports from it. What two tiers share by import — `read_sample`,
the project paths, `CLEAN_PROJECT` and `FULL_RUN` — is two packages under
`lib/`, because `lib/` is where code used more than once in this repository
goes: `test_read_sample` reads one, `test_trees` holds the trees the CLI is run
over: the paths of the files in them, the two versions of the tree, and the
`FULL_RUN` that names them the way the `trees` argument does. They are separate
because four of the five importers want one and not the other, and because a
file reader and a fixture tree change for different reasons; `FULL_RUN` stays
with the tree it names rather than becoming a third package. The package is not
named after the tool: what belongs there is whatever more than one caller needs
and no fixture should hold, which is a fact about the code rather than about
`assert_no_comments`. The tests themselves are not: nothing imports a test, so
`test/unit/`, `test/integration/` and `test/e2e/` stay where they are. Every job
reaches the module through `PYTHONPATH=lib`, since `test/` carries no
`__init__.py` and pytest puts only a test's own directory on the path. Importing
a conftest instead works only while a package layout keeps its module name
unique, and binds the suite to that layout for a reason nothing states.

#### Cover every tier the change touches

`unit/` for the readers and the CLI helpers, `integration/` for the CLI driven
over a real tree, `e2e/` for the installed console script run the way a workflow
step runs it, all three under `test/`. Unit and integration each gate on full
branch coverage on their own rather than on the two together. `e2e-tests`
carries no coverage gate and cannot, since it runs the command in another
process, so a line reachable only through the console script is reached by
`run_cli`, the in-process fixture in the root `conftest.py`, and asserted again
through the subprocess.

#### Test first

The test is written first, then the code that makes it pass. Test-first is
authoring order — the red and the green observations belong to CI, since nothing
runs locally.

### Verification

#### CI is the source of truth

Do not run tests, linters or builds locally to verify a change — write the code
and the tests, commit, push to `main`, and read the run with `gh run list`, `gh
run watch` and `gh run view --log-failed`. The jobs between them want Python,
Node, four tree-sitter grammars and eight tools this machine does not otherwise
carry, and CI checks every gate at once. Reading the code locally is still right
and cheap: `grep` and file reads are how the useful findings surface. A green
push publishes to PyPI and force-moves `latest` by itself, so there is no
version to hold back and a commit that should not be published is a commit that
should not be pushed.

#### Finding the run

Find the run by the full forty-character hash from `git rev-parse HEAD`. `gh run
list --commit` returns an empty list for the short hash `git log --oneline`
prints, which is indistinguishable from a run that has not started. A push
starts one workflow or both, depending on what it touched, and the change is
done when each run that started is green rather than when the first one is.

#### Path filters are not shell globs

A path in a workflow's `paths` filter is not a shell glob. GitHub reads `**` as
any run of characters, `/` included, so `**/*.md` needs a slash to match and
reaches no file at the root of the repository. The form that reaches both is
`'**.md'`, quoted because a bare `*` opens a YAML alias. `node` reads those two
patterns the other way, which is why the `markdownlint '**/*.md'` step reads
files that its own trigger would not have started it for.

## Notes

### Where a new convention goes

A convention learned in a session belongs in this file, and in a note under
`.claude/memories/` where it needs more than a paragraph, linked from the
section that summarises it. Nothing is kept in the session tool's own memory
directory under the home directory: those files belong to one machine, are
unversioned, and are invisible to everyone else working here.
