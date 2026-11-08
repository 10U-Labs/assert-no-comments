---
name: a-push-can-leave-its-issues-open
description: "GitHub can accept a commit on main and act on none of its Closes #N lines, so once the runs are clean each issue the message closes is read back and closed by hand if still open"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T01:58:31.763Z
---

# A push can leave its issues open

Once a push's runs are clean, check that every issue its message closes is
closed.

**Why:** GitHub can accept a commit on `main` and act on none of its `Closes #N`
lines. A long message naming many issues is where it is most likely; whether
the count or the size sets it off is not known. An issue left open after its
fix landed reads as unsolved, so a later loop takes it up again and works on
code that already satisfies it.

**How to apply:** for each `Closes #N` line, read `gh issue view <N> --json
state`. Close any still open with `gh issue close <N> --reason completed` and a
comment naming the commit that solved it. The lines themselves are written per
[[an-issue-is-closed-by-its-commit]], and fire per
[[issue-closing-keywords-fire-on-push]].
