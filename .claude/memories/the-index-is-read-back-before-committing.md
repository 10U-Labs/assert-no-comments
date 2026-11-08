---
name: the-index-is-read-back-before-committing
description: Run git status --porcelain between staging and committing and compare it with what the change touched
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T01:58:41.363Z
---

# The index is read back before committing

Run `git status --porcelain` after staging and before committing, and compare
what it lists with what the change touched.

**Why:** a failed staging command exits non-zero, and that decides nothing when
`git add` and `git commit` are separate calls rather than one `&&` chain,
because nothing reads the exit status. Reading the index shows the failure
whatever caused it, for the cost of one command.

**How to apply:** one `git status --porcelain` between staging and committing,
every time. It catches the miss in
[[git-add-stages-nothing-when-one-path-is-missing]] and the sweep in
[[a-path-is-staged-by-name]] alike.
