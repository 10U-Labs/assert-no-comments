---
name: solving-an-issue-ends-at-the-push
description: "A request to solve, fix or take an issue is a request to commit and push the fix; never stop at a finished working tree and wait to be told to push"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T03:29:40.359Z
---

# Solving an issue ends at the push

A request to solve, fix or take an issue is a request to commit and push the
fix. Once the change is ready, stage it, commit it and push it without waiting
to be told to push.

**Why:** CI is the only place the fix is tested, so a fix left in the working
tree is untested and unfinished, and waiting for a separate go-ahead stalls the
work.

**How to apply:** stage and commit per
[[the-index-is-read-back-before-committing]], push per
[[push-once-and-let-the-run-finish]], and once the runs are clean read the issue
back per [[a-push-can-leave-its-issues-open]].
