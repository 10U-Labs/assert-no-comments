---
name: commits-go-straight-to-main
description: Work lands as direct commits on main; no feature branch, no pull request, and no advice built around a review cycle
metadata:
  type: feedback
---

# Commits go straight to main

Work goes straight to `main` as direct commits. Do not create a feature branch,
do not open a pull request, and do not structure advice around a review cycle.

**Why:** CI is the only review there is. Both workflows run on a push to `main`
and on nothing else, so a branch would get no run at all, and the tests land in
the same commit as the code they cover.

**How to apply:** commit on `main` and push, one issue to a commit per
[[one-issue-one-commit]], and close the issue from the message per
[[an-issue-is-closed-by-its-commit]].
