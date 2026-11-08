---
name: a-paragraph-wraps-at-eighty-columns
description: A paragraph in a .md file, memories and skills included, is hard-wrapped at eighty columns; headings, table rows, fences, frontmatter, index entries and commit bodies are not
metadata:
  type: feedback
---

# A paragraph wraps at eighty columns

A paragraph in a `.md` file — `README.md`, a memory here, a skill — is
hard-wrapped at eighty columns, and a paragraph is the only thing that is: a
heading, a table row, a fenced block, a frontmatter line and an entry in
`MEMORY.md` keep whatever width they have, and a commit message body is still
written as one line, because none of those is a markdown paragraph.

**Why:** nothing checks it. `markdownlint.yml` passes `--disable MD013`, and
turning that rule on would cap every line rather than every paragraph — eighty
is its own default, but exempting tables and fenced blocks takes a config file,
and `assert-no-linter-config-files` names markdownlint. So the cap is kept by
whoever writes the paragraph.

**How to apply:** hard wrapping has the cost it always has: a one-word edit
reflows the words after it and the diff marks lines the edit did not mean to
change. Rewrap the whole paragraph when that happens rather than leaving one
line long, because half a wrapped paragraph reads worse than either.
