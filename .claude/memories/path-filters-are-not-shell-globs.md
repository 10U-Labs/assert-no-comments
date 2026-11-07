---
name: path-filters-are-not-shell-globs
description: GitHub reads ** in a workflow paths filter as any run of characters, so '**.md' reaches files at the root where **/*.md does not
metadata:
  type: feedback
---

# Path filters are not shell globs

A path in a workflow's `paths` filter is not a shell glob. GitHub reads `**` as
any run of characters, `/` included, so `**/*.md` needs a slash to match and
reaches no file at the root of the repository. The form that reaches both is
`'**.md'`, quoted because a bare `*` opens a YAML alias.

`node` reads those two patterns the other way, which is why the `markdownlint
'**/*.md'` step reads files that its own trigger would not have started it for.

**How to apply:** write a filter that has to reach the root as `'**.md'`, and
never copy a pattern from a `run:` step into `paths` on the assumption that both
read it alike.
