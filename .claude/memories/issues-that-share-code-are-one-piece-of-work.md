---
name: issues-that-share-code-are-one-piece-of-work
description: Issues whose fixes go through the same code are taken whole as one piece of work, test first, each part committed and pushed once it stands on its own, one Closes line per issue
metadata:
  type: feedback
---

# Issues that share code are one piece of work

Before taking anything, read every open issue the loop lists and sort them into
groups of issues whose fixes go through the same code. Take the group holding
the lowest-numbered issue whole, as one piece of work designed and tested
together, its tests written first. Commit and push each part of it once that
part stands on its own, and give each issue a commit solves a `Closes #N` line
of its own.

**Why:** issues that change the same code, such as readers that each add a
grammar and a row to `READERS`, share one design. Taken one at a time, each is
designed without the others in view, so the shared part is settled by whichever
lands first and reworked by each one after it.

**How to apply:** a part stands on its own when its commit is green by itself
and closes every issue it names. Push it, wait for its runs per
[[push-once-and-let-the-run-finish]], then push the next. An issue whose fix
shares no code with any other is a group of one, and a group that is too big for
one commit is pushed in parts rather than split into new issues. Close each
issue per [[an-issue-is-closed-by-its-commit]].
