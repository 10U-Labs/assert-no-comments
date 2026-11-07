---
name: an-issue-is-closed-by-its-commit
description: An issue is closed by a Closes #N line in the commit that fixes it, one line per issue
metadata:
  type: feedback
---

# An issue is closed by its commit

An issue is closed by the commit that fixes it, through a `Closes #N` line, one
line per issue.

**Why:** GitHub binds the keyword to a single reference, so `Closes #1 and #2`
closes #1 and leaves #2 open. There is no pull request to close it instead, per
[[commits-go-straight-to-main]].

**How to apply:** give each issue its own `Closes #N` line in the message, ahead
of the attribution lines.
