---
name: git-add-stages-nothing-when-one-path-is-missing
description: "git add stages none of its paths when any one of them matches nothing, so a removed path goes to git rm and never to git add"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T01:58:38.561Z
---

# git add stages nothing when one path is missing

Name a removed path to `git rm` and an added or changed path to `git add`, and
never name both kinds to one command.

**Why:** `git add` stages none of its paths when any one of them matches nothing
on disk. It reports `fatal: pathspec '<path>' did not match any files` and exits
non-zero having staged nothing, not everything but the bad path. A rename is
what produces such a list, since the old path is gone from disk and the new one
is not yet tracked, and a commit made after it carries only what was already
staged: the deletion, without the file that replaces it.

**How to apply:** split the staging into a `git rm` for what is gone and a
`git add` for what is there, then confirm it per
[[the-index-is-read-back-before-committing]].
