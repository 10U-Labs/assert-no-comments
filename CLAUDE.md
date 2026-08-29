# Working in assert-no-comments

## Overview

These are the standing conventions for working in this repository. A section states a rule, a trap or the reason behind one, and links the longer write-up where there is one — one note per topic under `.claude/memories/`.

A section here does not restate what a file in the tree already says. `README.md` is the argument for the tool and the reference for what it reads; `.github/workflows/release.yml` is the list of jobs a push has to get past. An inventory copied into this file is a second copy that goes stale with nothing to catch it, so where the answer is in a workflow file or in the README, this file points at it rather than paraphrasing it. A table of contents is that same second copy of the headings below it, which is why this file has none.

## Conventions

### Commits

#### A rejected push is fixed forward

A push rejected by CI is answered with a follow-up commit. Do not amend and force-push: `main` is what the run read, and every check here is a job of its own running in parallel with the rest, so a red run names every check that failed rather than the earliest one. Read the run for that whole list and answer all of it in one commit.

#### One closing line per issue

An issue is closed by the commit that fixes it, through a `Closes #N` line in the message, one line per issue. GitHub binds the keyword to a single reference, so `Closes #1 and #2` closes #1 and leaves #2 open; `2e9c821` wrote exactly that, and #2 had to be closed by hand nine seconds later. Closing by hand is the fallback for history already published, not the way it is done.

#### One issue, one commit

One issue is solved by one commit and one push. An issue that cannot be done in one commit is two issues, and filing the second is the answer rather than spreading one issue across pushes. Two issues share a commit only where the fix for one is contained in the fix for the other, which is what `2e9c821` says in its first paragraph: a `.ts` reader added without the parser would have been a fresh instance of the defect the other issue was about, so the suffixes and the grammars landed together.

#### Push once and let the run finish

Both workflows cancel the run in progress when a second push lands on the same ref. The tree is still verified, by the later run, but the cancelled commit loses its own release, because `release` never gets its `needs`. Push once per issue and read that run.

#### Straight to main

Work goes straight to `main` as direct commits. Do not create a feature branch, do not open a pull request, and do not structure advice around a review cycle. There is no pull-request buffer, so CI is the only review there is and the tests land in the same commit as the code they cover.

### Docstrings

#### The package is run against itself

`release.yml` runs the tool this repository publishes over the repository that publishes it, through `./`, and `release` needs that job. It is red, and has been since it was added: `src/` and `test/` carry a docstring on every module, class and function, because `pylint-src` and `pylint-test` gate on `--fail-on=C,R,W` with the three `missing-*-docstring` checks left on. The prose the tool forbids is the prose pylint requires, both rules are in force at once, and nothing has published from either commit.

That is #3, and until it lands — the `--disable=missing-*-docstring` flags onto both pylint steps and every docstring in `src/` and `test/` deleted with them, in one commit — a new module, class or test still carries its docstring, and a red `assert-no-comments` is the known state of the tree rather than something a push introduced. Read a run for what is red beside it.

### Issues

#### An issue states one solution

An issue is definitive. Its `Proposed Solution` names one change — this function, this file, this dependency — because the issue is the instruction to whoever picks it up and they were not in the conversation that produced it. Never file "either X or Y", a menu with a recommendation, or a question left for the reader. Naming the alternative that lost is still worth writing, and #2 does it: widening `OPENS_A_PATTERN` moves which inputs are wrong rather than ending the class. What is not allowed is leaving the choice open.

#### The seven sections

An issue has seven sections in a fixed order: "Problem", "Why Unit Tests Did Not Catch It?", "Why Integration Tests Did Not Catch It?", "Why E2E Tests Did Not Catch It?", "Why Static Analysis Jobs Did Not Catch It?", "Which Regression Tests Would Prevent This from Happening Again?", "Proposed Solution". Issues #1 and #2 are both written that way. Every issue has all seven; where a tier could not have caught the defect, saying so is the finding rather than a reason to drop the section. Static analysis is asked separately because a job reads the text and refuses a shape wherever it appears, where a tier executes the program and can only catch what a caller could observe. The regression section names the coverage owed, each test by its tier and its assertion, and is separate from the solution so that a fix cannot ship with the coverage folded into its last paragraph.

### Markdown

#### A paragraph is one line

`markdownlint` runs with `--disable MD013`, so nothing holds a line to a column count: a paragraph is written as one line and the reader's editor wraps it. Do not put newlines inside prose to make it fit a width, and do not wrap commit message bodies either — nothing checks those, but every commit from this one on is written the same way. Hard wrapping is what makes a one-word edit arrive as a rewritten paragraph, because the words after it move onto the lines below and the diff marks all of them; a paragraph on one line is a diff that names the paragraph that changed and nothing else.

The flag is on the command line rather than in a `.markdownlint.json`, because [configuration goes on the command line](#configuration-goes-on-the-command-line) — `assert-no-linter-config-files` runs with `--linters pylint,mypy,yamllint` and would not have caught the file, so this one is on the convention rather than on a job. `--disable` takes a list, so the `--` before the glob is what ends it; without it `markdownlint` reads `'**/*.md'` as a further rule name and lints no files at all.

`10U-Labs/10ulabs.com` disables the same rule, so prose moves between the two repositories as it is rather than being re-wrapped on the way.

### Readers

#### Every language is read by its own parser

A reader in `src/assert_no_comments/scanner.py` is a parser for the language it reads, never a walk over the characters. A new language gets a grammar, an entry in `READERS`, and a reader whose whole body is `parsed_comments(text, THAT_GRAMMAR)` — never a marker table — and a dialect that reads the same characters differently gets a grammar of its own rather than a further suffix on the one it resembles.

The rule was bought rather than chosen, by issue #2, and what it cost is in [every-language-is-read-by-its-own-parser](.claude/memories/every-language-is-read-by-its-own-parser.md). Read that before adding a language, and before reaching for `tree-sitter-language-pack`.

### Releases

#### Every green push publishes

A green push to `main` touching the paths `release.yml` filters on tags, builds, publishes to PyPI and force-moves `latest`. There is no separate release step to remember and no chance to hold a version back, so a commit that should not be published is a commit that should not be pushed. `latest` is what `10U-Labs/assert-no-comments@latest` resolves to in the composite action, so moving it hands every consumer of the action the new version at once.

#### The tag is made before the build

The version is `setuptools-scm` reading the tag `release` has just made, and the tag is a UTC timestamp, so a build that ran before the tagging step would publish a version derived from the previous tag instead. Keep those steps in the order they are in.

### Tests

#### A conftest with no fixture in it stays

`test/integration/conftest.py` and `test/e2e/conftest.py` hold a docstring and nothing else, and they stay. The file is what tells whoever writes the next fixture that this level exists to hold one; left to itself a session writes setup into the test file already open in front of it, and the same setup is then copied into every other file that needs it. They cannot be emptied to zero bytes, because `pylint-test` gates on `--fail-on=C,R,W` and `missing-module-docstring` is a C.

#### Cover every tier the change touches

A change is covered at every tier it touches: `test/unit/` for the readers and the CLI helpers, `test/integration/` for the CLI driven over a real tree, `test/e2e/` for the installed console script run the way a workflow step runs it. The tree has no deployment split, because this package deploys nothing, and what decides the tier is what the test reads. `2e9c821` is the shape — a `.tsx` sample, one unit test per comment form, and an integration and an end-to-end run over the tree holding it.

#### One assert per pytest

Every test asserts once, and `assert-one-assert-per-pytest` fails the push over a second one rather than leaving it to be noticed in review. A test name is a sentence saying what is true, `test_a_hash_inside_a_string_is_not_reported`, and carries the docstring `pylint-test` requires.

#### Test first

We do TDD: the test is written first, then the code that makes it pass. Test-first is authoring order — the red and the green observations belong to CI, since nothing runs locally. A commit says which test was red before it, the way `2e9c821` does in its last paragraph.

#### The coverage gate is on the in-process tiers

`unit-tests` and `integration-tests` each gate on total branch coverage of the package, so each tier stands on its own rather than on the two together. `e2e-tests` carries no coverage gate and cannot: `run_cli_subprocess` runs the command in another process, which is the point of that tier and also why its lines are invisible to `coverage`. A line reachable only through the console script is therefore reached by `run_cli`, the in-process fixture in `test/conftest.py`, and asserted again through the subprocess.

#### Trees under test go in samples

`test/samples.py` holds the sample trees and all three tiers import from it. A tier that assembles its own tree inline is how two tiers come to disagree about what a clean project looks like. The module is also the worked example this package's own source cannot be, since that source carries the docstrings the tool reports.

### Verification

#### CI is the source of truth

Do not run tests, linters or builds locally to verify a change — write the code and the tests, commit, push to `main`, and read the run with `gh run list`, `gh run watch` and `gh run view --log-failed`. The jobs `release` needs want Python, Node, four tree-sitter grammars and eight tools this machine does not otherwise carry; CI installs all of it per job and checks every gate at once. Reading the code locally is still right and cheap: `grep` and file reads are how the useful findings surface.

#### Configuration goes on the command line

There is no `.pylintrc`, no `mypy.ini`, no `.yamllint` and no inline `pylint: disable` anywhere, and there cannot be: `assert-no-linter-config-files` and `assert-no-inline-directives` fail the run over either. Every option a tool takes is written into the step that runs it. A rule that cannot be turned off is the point: the cost of it lands as a decision made somewhere visible, which is what the docstrings are — [the package is run against itself](#the-package-is-run-against-itself), and the flags that answer for that go on the pylint steps.

#### Finding the run

Find the run by the full forty-character hash from `git rev-parse HEAD`. `gh run list --commit` returns an empty list for the short hash `git log --oneline` prints, which is indistinguishable from a run that has not started. A push starts one workflow or both, depending on what it touched, and the change is done when each run that started is green rather than when the first one is.

#### Keys in a YAML file are alphabetical

`yamllint` runs `--strict` with `key-ordering: enable`, so every mapping in every YAML file here is in alphabetical order — which is why `name` and `on` sit at the bottom of a workflow file, under `jobs`, and why the jobs themselves are alphabetical. A new job goes in its alphabetical place, and in the `needs` list of `release`, which is sorted the same way.

#### Path filters are not shell globs

A path in a workflow's `paths` filter is not a shell glob. GitHub reads `**` as any run of characters, `/` included, so `**/*.md` needs a slash to match and reaches no file at the root of the repository: it covers `.claude/memories/every-language-is-read-by-its-own-parser.md` and misses `README.md` and this file. The form that reaches both is `'**.md'`, quoted because a bare `*` opens a YAML alias. `node` reads those two patterns the other way, `**/` matching zero directories, which is why the `markdownlint '**/*.md'` step reads files that its own trigger would not have started it for.

## Notes

### Where a new convention goes

A convention learned in a session belongs in this repository: a paragraph in this file, and a note under `.claude/memories/` where it needs more than a paragraph, linked from the section that summarises it. Nothing is kept in the session tool's own memory directory under the home directory. Those files belong to one machine, are unversioned, and are invisible to everyone else working here, so a rule kept there is a rule the next reader never sees, and a rule kept in both places drifts with nothing to signal it. That is why the local copy of the closing rule was deleted when this file was written: it had moved to [one closing line per issue](#one-closing-line-per-issue).
