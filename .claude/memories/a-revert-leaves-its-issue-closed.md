---
name: a-revert-leaves-its-issue-closed
description: "Reverting the commit that closed an issue leaves the issue closed, so the revert is followed by gh issue reopen and a read of its state"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T01:58:28.512Z
---

# A revert leaves its issue closed

When a revert takes back the commit that closed an issue, reopen the issue by
hand.

**Why:** GitHub closes an issue when its keyword reaches `main`, and nothing
undoes that. `git revert` adds a commit and leaves the original in history, and
no message the revert carries, `Refs #N` included, reopens `#N`. The issue then
reads as finished while the tree holds none of its work, and the list of open
issues the autopilot works from never offers it again.

**How to apply:** push the revert, then `gh issue reopen <N>` with a comment
naming the commit that closed it, the commit that took it back and what the run
said. Read the state back with `gh issue view <N> --json state`, since the
revert's own output says nothing either way.
