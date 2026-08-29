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
  - [Docstrings](#docstrings)
    - [The package is not run against itself](#the-package-is-not-run-against-itself)
    - [Why the tool refuses prose is in the README](#why-the-tool-refuses-prose-is-in-the-readme)
  - [Issues](#issues)
    - [An issue states one solution](#an-issue-states-one-solution)
    - [The seven sections](#the-seven-sections)
  - [Markdown](#markdown)
    - [Markdown is hard-wrapped](#markdown-is-hard-wrapped)
  - [Readers](#readers)
    - [Every language is read by its own parser](#every-language-is-read-by-its-own-parser)
    - [What a new language costs](#what-a-new-language-costs)
  - [Releases](#releases)
    - [Every green push publishes](#every-green-push-publishes)
    - [The tag is made before the build](#the-tag-is-made-before-the-build)
  - [Tests](#tests)
    - [A conftest with no fixture in it stays](#a-conftest-with-no-fixture-in-it-stays)
    - [Cover every tier the change touches](#cover-every-tier-the-change-touches)
    - [One assert per pytest](#one-assert-per-pytest)
    - [Test first](#test-first)
    - [The coverage gate is on the in-process tiers](#the-coverage-gate-is-on-the-in-process-tiers)
    - [Trees under test go in samples](#trees-under-test-go-in-samples)
  - [Verification](#verification)
    - [CI is the source of truth](#ci-is-the-source-of-truth)
    - [Configuration goes on the command line](#configuration-goes-on-the-command-line)
    - [Finding the run](#finding-the-run)
    - [Keys in a YAML file are alphabetical](#keys-in-a-yaml-file-are-alphabetical)
    - [Path filters are not shell globs](#path-filters-are-not-shell-globs)
- [Notes](#notes)
  - [Where a new convention goes](#where-a-new-convention-goes)

## Overview

These are the standing conventions for working in this repository. A
section states a rule, a trap or the reason behind one, and links the
longer write-up where there is one — one note per topic under
`.claude/memories/`.

A section here does not restate what a file in the tree already says.
`README.md` is the argument for the tool and the reference for what it
reads; `.github/workflows/release.yml` is the list of jobs a push has to
get past. An inventory copied into this file is a second copy that goes
stale with nothing to catch it, so where the answer is in a workflow
file or in the README, this file points at it rather than paraphrasing
it.

## Conventions

### Commits

#### A rejected push is fixed forward

A push rejected by CI is answered with a follow-up commit. Do not amend
and force-push: `main` is what the run read, and every check here is a
job of its own running in parallel with the rest, so a red run names
every check that failed rather than the earliest one. Read the run for
that whole list and answer all of it in one commit.

#### One closing line per issue

An issue is closed by the commit that fixes it, through a `Closes #N`
line in the message, one line per issue. GitHub binds the keyword to a
single reference, so `Closes #1 and #2` closes #1 and leaves #2 open;
`2e9c821` wrote exactly that, and #2 had to be closed by hand nine
seconds later. Closing by hand is the fallback for history already
published, not the way it is done.

#### One issue, one commit

One issue is solved by one commit and one push. An issue that cannot be
done in one commit is two issues, and filing the second is the answer
rather than spreading one issue across pushes. Two issues share a commit
only where the fix for one is contained in the fix for the other, which
is what `2e9c821` says in its first paragraph: a `.ts` reader added
without the parser would have been a fresh instance of the defect the
other issue was about, so the suffixes and the grammars landed together.

#### Push once and let the run finish

Both workflows set `cancel-in-progress` on a group keyed by workflow and
ref, so a second push cancels the run the first one started. The tree is
still verified, by the later run, but the cancelled commit loses its own
release, because `release` never gets its `needs`. Push once per issue
and read that run.

#### Straight to main

Work goes straight to `main` as direct commits. Do not create a feature
branch, do not open a pull request, and do not structure advice around a
review cycle. There is no pull-request buffer, so CI is the only review
there is and the tests land in the same commit as the code they cover.

### Docstrings

#### The package is not run against itself

None of the fourteen jobs in `release.yml` is `assert-no-comments`, and
`src/assert_no_comments/` and `test/` carry a docstring on every module,
class and function — exactly what the tool this repository ships reports
as a finding. `pylint-src` and `pylint-test` gate on `--fail-on=C,R,W`
and the three `missing-*-docstring` checks are C, so the prose the tool
forbids is prose pylint requires.

That conflict has a resolution, which is why #3 and #6 are open. The
sibling `assert-python-definition-is-used` passes
`--disable=missing-*-docstring` to pylint on the command line, which is
neither a configuration file nor an inline directive, and gates its own
tree on `assert-no-comments`. Until #3 is answered, treat the docstrings
here as a standing question rather than a settled rule, and treat the
rule the tool enforces as a repository's rule rather than a universal
one.

#### Why the tool refuses prose is in the README

The case for the rule — what a comment was about to say and where each
of those things goes instead — is the "Why" section of `README.md`, and
what counts as a comment is the table below it. Point a reader there
rather than restating it. This file says how work is done here; the
README says what the tool is for, and the two saying it in different
words is how they come apart.

### Issues

#### An issue states one solution

An issue is definitive. Its `Proposed Solution` names one change — this
function, this file, this dependency — because the issue is the
instruction to whoever picks it up and they were not in the conversation
that produced it. Never file "either X or Y", a menu with a
recommendation, or a question left for the reader. Naming the
alternative that lost is still worth writing, and #2 does it: widening
`OPENS_A_PATTERN` moves which inputs are wrong rather than ending the
class. What is not allowed is leaving the choice open.

#### The seven sections

An issue has seven sections in a fixed order: "Problem", "Why Unit Tests
Did Not Catch It?", "Why Integration Tests Did Not Catch It?", "Why E2E
Tests Did Not Catch It?", "Why Static Analysis Jobs Did Not Catch It?",
"Which Regression Tests Would Prevent This from Happening Again?",
"Proposed Solution". Issues #1 and #2 are both written that way. Every
issue has all seven; where a tier could not have caught the defect,
saying so is the finding rather than a reason to drop the section.
Static analysis is asked separately because a job reads the text and
refuses a shape wherever it appears, where a tier executes the program
and can only catch what a caller could observe. The regression section
names the coverage owed, each test by its tier and its assertion, and is
separate from the solution so that a fix cannot ship with the coverage
folded into its last paragraph.

### Markdown

#### Markdown is hard-wrapped

`markdownlint` runs over the repository with its default rules and no
configuration file, so `MD013` holds every line to eighty columns. Wrap
prose by hand, the way `README.md` and the notes under
`.claude/memories/` already are, and wrap commit message bodies too —
nothing checks those, but every commit here is wrapped. A line past
eighty passes only when it carries no space beyond the limit, which is
what lets a long identifier in backticks overflow: the one such line in
`every-language-is-read-by-its-own-parser.md` is a test name. This is
the opposite of the rule in `10U-Labs/10ulabs.com`, whose markdown
linter runs with the line-length rule disabled, so prose moved between
the two repositories is re-wrapped rather than pasted.

### Readers

Longer: [every-language-is-read-by-its-own-parser](.claude/memories/every-language-is-read-by-its-own-parser.md).

#### Every language is read by its own parser

A reader in `src/assert_no_comments/scanner.py` is a parser for the
language it reads, never a walk over the characters. Python goes through
`tokenize` and `ast`, YAML through `yaml.scan`, and JavaScript,
TypeScript, TSX and OpenTofu through their tree-sitter grammars. The
rule was bought rather than chosen. `marked_comments` guessed whether a
`/` opened a regular expression from the last non-space character before
it, `<` was in that table, so the slash of a JSX closing tag looked like
the start of a pattern and the walk swallowed the rest of the line. That
is issue #2. Widening the table moves which inputs are wrong; it does
not stop there being inputs that are wrong, and the failure is silent in
the direction that matters, because a missed comment leaves a job green
and nobody re-reads a green job.

#### What a new language costs

A new language gets a grammar, an entry in `READERS`, and a reader whose
whole body is `parsed_comments(text, THAT_GRAMMAR)` — never a marker
table. Dialects that read the same characters differently are separate
grammars: `.tsx` is not `.ts` with elements in it, because `<string>y`
asserts a type in one and opens an element in the other. A grammar per
language is a dependency per language, and `tree-sitter-language-pack`
is the one that looks like it would save that; it would ship 371
grammars to serve four, every one of them a version this package
publishes and does not use. The never-fail contract holds either way — a
file the grammar cannot parse gives findings rather than an exit code of
2 — and what a broken file yields is whatever the grammar could still
recognise.

### Releases

#### Every green push publishes

A green push to `main` touching the paths `release.yml` filters on tags,
builds, publishes to PyPI and force-moves `latest`. There is no separate
release step to remember and no chance to hold a version back, so a
commit that should not be published is a commit that should not be
pushed. `latest` is what `10U-Labs/assert-no-comments@latest` resolves
to in the composite action, so moving it hands every consumer of the
action the new version at once.

#### The tag is made before the build

`release` creates the tag, builds, and only then pushes the tag. The
version is `setuptools-scm` reading that tag, and the tag is a UTC
timestamp, so a build that ran before the tagging step would publish a
version derived from the previous tag instead. Keep those steps in that
order.

### Tests

#### A conftest with no fixture in it stays

`test/integration/conftest.py` and `test/e2e/conftest.py` hold a
docstring and nothing else, and they stay. The file is what tells
whoever writes the next fixture that this level exists to hold one; left
to itself a session writes setup into the test file already open in
front of it, and the same setup is then copied into every other file
that needs it. They cannot be emptied to zero bytes, because
`pylint-test` gates on `--fail-on=C,R,W` and `missing-module-docstring`
is a C.

#### Cover every tier the change touches

A change is covered at every tier it touches: `test/unit/` for the
readers and the CLI helpers, `test/integration/` for the CLI driven over
a real tree, `test/e2e/` for the installed console script run the way a
workflow step runs it. The tree has no deployment split, because this
package deploys nothing, and what decides the tier is what the test
reads. `2e9c821` is the shape — a `.tsx` sample, one unit test per
comment form, and an integration and an end-to-end run over the tree
holding it.

#### One assert per pytest

Every test asserts once. `one-assert-per-pytest` is a job in
`release.yml`, so a second assert fails the push rather than being
noticed in review. A test name is a sentence saying what is true,
`test_a_hash_inside_a_string_is_not_reported`, and carries the docstring
`pylint-test` requires.

#### Test first

We do TDD: the test is written first, then the code that makes it pass.
Test-first is authoring order — the red and the green observations
belong to CI, since nothing runs locally. A commit says which test was
red before it, the way `2e9c821` does in its last paragraph.

#### The coverage gate is on the in-process tiers

`unit-tests` and `integration-tests` each run with
`--cov=assert_no_comments --cov-branch --cov-fail-under=100`, so each
tier stands on its own rather than on the two together. `e2e-tests`
carries no coverage gate and cannot: `run_cli_subprocess` runs the
command in another process, which is the point of that tier and also why
its lines are invisible to `coverage`. A line reachable only through the
console script is therefore reached by `run_cli`, the in-process fixture
in `test/conftest.py`, and asserted again through the subprocess.

#### Trees under test go in samples

`test/samples.py` holds the sample trees and all three tiers import from
it. A tier that assembles its own tree inline is how two tiers come to
disagree about what a clean project looks like. The module is also the
worked example this package's own source cannot be, since that source
carries the docstrings the tool reports.

### Verification

#### CI is the source of truth

Do not run tests, linters or builds locally to verify a change — write
the code and the tests, commit, push to `main`, and read the run with
`gh run list`, `gh run watch` and `gh run view --log-failed`. Fourteen
jobs gate a release, and between them they want Python, Node, four
tree-sitter grammars and eight tools this machine does not otherwise
carry; CI installs all of it per job and checks every gate at once.
Reading the code locally is still right and cheap: `grep` and file reads
are how the useful findings surface.

#### Configuration goes on the command line

There is no `.pylintrc`, no `mypy.ini`, no `.yamllint` and no inline
`pylint: disable` anywhere, and there cannot be: `no-linter-configs` and
`no-inline-directives` fail the run over either. Every option a tool
takes is written into the step that runs it — the yamllint rules arrive
as `--config-data`, `pylint` gets `--fail-on=C,R,W --fail-under=10.0`,
`mypy` gets `--strict` over `src/`. A rule that cannot be turned off is
the point: the cost of it lands as a decision made somewhere visible,
which is what [the package is not run against
itself](#the-package-is-not-run-against-itself) is.

#### Finding the run

Find the run by the full forty-character hash from `git rev-parse HEAD`.
`gh run list --commit` returns an empty list for the short hash
`git log --oneline` prints, which is indistinguishable from a run that
has not started. A push starts one workflow or both, depending on what
it touched, and the change is done when each run that started is green
rather than when the first one is.

#### Keys in a YAML file are alphabetical

`yamllint` runs `--strict` with `key-ordering: enable`, so every mapping
in every YAML file here is in alphabetical order — which is why `name`
and `on` sit at the bottom of a workflow file, under `jobs`, and why the
jobs themselves are alphabetical. `truthy` allows `on` so that key needs
no quoting, and `empty-lines` allows none inside a file. A new job goes
in its alphabetical place, and in the `needs` list of `release`, which
is sorted the same way.

#### Path filters are not shell globs

A path in a workflow's `paths` filter is not a shell glob. GitHub reads
`**` as any run of characters, `/` included, so `**/*.md` needs a slash
to match and reaches no file at the root of the repository: it covers
`.claude/memories/every-language-is-read-by-its-own-parser.md` and
misses `README.md` and this file. The form that reaches both is
`'**.md'`, quoted because a bare `*` opens a YAML alias. `node` reads
those two patterns the other way, `**/` matching zero directories, which
is why the `markdownlint '**/*.md'` step reads files that its own
trigger would not have started it for.

## Notes

### Where a new convention goes

A convention learned in a session belongs in this repository: a
paragraph in this file, and a note under `.claude/memories/` where it
needs more than a paragraph, linked from the section that summarises it.
Nothing is kept in the session tool's own memory directory under the
home directory. Those files belong to one machine, are unversioned, and
are invisible to everyone else working here, so a rule kept there is a
rule the next reader never sees, and a rule kept in both places drifts
with nothing to signal it. That is why the local copy of the closing
rule was deleted when this file was written: it had moved to
[one closing line per issue](#one-closing-line-per-issue).
