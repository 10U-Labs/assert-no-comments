---
name: closing-keyword-form
description: Write a close as Closes #N and a mention as Refs #N or See #N, one line per issue; nothing enforces the choice
metadata:
  type: feedback
---

# The form of an issue reference

Write a close as `Closes #N` and a mention as `Refs #N` or `See #N`, one line
per issue.

**Why:** any of the nine closing keywords closes the issue the same way, per
[[issue-closing-keywords-fire-on-push]], so nothing enforces the choice. With
one word for a close, a search of the log for `Closes #` finds every commit that
finished an issue, and with one form for a mention, the word chosen for it
cannot turn out to be one of the nine.

**How to apply:** pick the form by whether the commit finishes the issue, and
give each issue its own line, per [[an-issue-is-closed-by-its-commit]]. A bare
`#N` mentions the issue too, but inside a sentence it can land after a keyword
without meaning to; `Refs #N` on a line of its own cannot.
