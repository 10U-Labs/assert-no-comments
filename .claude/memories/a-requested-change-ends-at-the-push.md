---
name: a-requested-change-ends-at-the-push
description: A change the user asks for is finished only once it is committed and pushed; commit and push it without asking whether to and without waiting to be told to push
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T03:35:21.285Z
---

# A requested change ends at the push

A change the user asks for, whether an issue's fix, a memory or any other edit
to the tree, is finished only once it is committed and pushed. When it is
ready, stage it, commit it and push it without asking whether to and without
waiting to be told to push.

**Why:** CI is the only place a change is tested, so a change left in the
working tree is untested and unfinished, and asking or waiting for a go-ahead
only holds back work the user has already asked for.

**How to apply:** stage and commit per
[[the-index-is-read-back-before-committing]], push per
[[push-once-and-let-the-run-finish]], and once the runs are clean read back each
issue the message closes per [[a-push-can-leave-its-issues-open]].
