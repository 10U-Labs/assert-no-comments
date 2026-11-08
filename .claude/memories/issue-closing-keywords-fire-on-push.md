---
name: issue-closing-keywords-fire-on-push
description: Nine keywords close an issue from anywhere in a commit message pushed to main, brackets included, whatever the run then says; keep them for the commit that finishes the issue
metadata:
  type: feedback
---

# Issue-closing keywords fire on push

GitHub closes an issue for any of nine keywords followed by `#N`: `close`,
`closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves` and
`resolved`. The keyword can stand anywhere in a commit message pushed to the
default branch, subject or body, and it closes the issue on push, whatever the
run then says. Brackets do not stop it: a subject such as `Fix the reader (#12)`
is read as a keyword followed by `#12` and closes that issue.

**Why:** work here goes straight to `main` per [[commits-go-straight-to-main]],
so no pull request stands between a premature keyword and the close, and an
issue closed by a commit whose run then fails stays closed.

**How to apply:** keep a closing keyword for the commit that finishes its issue,
and word a commit that only refers to an issue with none of the nine before its
`#N`, in the subject and the body alike. Before pushing, read the whole message
for a keyword followed by an issue the commit does not finish.
