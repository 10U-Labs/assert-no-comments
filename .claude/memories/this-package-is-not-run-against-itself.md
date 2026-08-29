# This package is not run against itself

`src/assert_no_comments/` carries a docstring on every module, class and
function, which is exactly what the tool it ships reports as a finding.
That looks like hypocrisy and is worth explaining once, because the
alternative was tried and is worse.

`release.yml` gates on `pylint-src` and `pylint-test` with
`--fail-on=C,R,W`, and pylint's `missing-module-docstring`,
`missing-class-docstring` and `missing-function-docstring` are all C.
So this repository requires the docstrings that `assert-no-comments`
forbids, and the two rules cannot both hold in one tree. Turning the
pylint rules off would mean shipping a linter configuration, which
`no-linter-configs` fails the run for, or an inline directive, which
`no-inline-directives` fails the run for.

The rule the tool enforces is a repository's rule, not a universal one.
wan-synthesizer adopted it and turned the three pylint checks off to
match, in GitHub issue #116. This repository is the sibling of
`assert-python-definition-is-used` and keeps that repository's
conventions, docstrings included, so that a reader moving between the
two finds the same shape. Neither repository runs the other's tool on
itself either.

What this costs is that the package's own source is not a worked example
of what it asks for. `test/samples.py` is where to look for that: it
holds the clean tree and the commented tree the integration and
end-to-end tiers are run against.

This was written on 2026-08-23, when the package was first published.
