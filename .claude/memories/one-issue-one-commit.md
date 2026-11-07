---
name: one-issue-one-commit
description: One issue is solved by one commit and one push; an issue too big for one commit is two issues, and issues are never batched
metadata:
  type: feedback
---

# One issue, one commit

One issue is solved by one commit and one push. An issue that cannot be done in
one commit is two issues, and filing the second is the answer rather than
spreading one issue across pushes. Two issues share a commit only where the fix
for one is contained in the fix for the other.

**Why:** this is where this repository parts from 10ulabs.com, api.10ulabs.com
and wan-synthesizer, whose commits each solve every open issue of one workflow's
stack. A habit or a skill carried over from them would batch here too unless
something said not to.

**How to apply:** when an issue turns out not to fit one commit, file the part
that does not fit as an issue of its own and push the rest alone, closing the
one issue it solves per [[an-issue-is-closed-by-its-commit]].
