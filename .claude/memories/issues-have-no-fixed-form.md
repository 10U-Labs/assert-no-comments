---
name: issues-have-no-fixed-form
description: An issue follows no house layout; write each in whatever form lets a session that never saw the conversation act on it alone
metadata:
  node_type: memory
  type: feedback
  originSessionId: 480159be-d838-4153-abff-13fe6b4fba0b
  modified: 2026-11-08T00:00:40.724Z
---

# Issues have no fixed form

There is no house layout for an issue's title or body. An issue is written in
the form that lets a session that has never seen this conversation act on it
from the issue alone: what is wrong, the reproduction inline, and the change
that fixes it.

**Why:** the one test of an issue is whether a fresh session can act on it. A
fixed form made an issue about a memory, a workflow or a setting fill sections
that could only say nothing applied.

**How to apply:** do not mirror an earlier issue's layout for its own sake.
Keep the rules that are about substance rather than form: one indivisible
problem per issue ([[one-indivisible-problem-per-issue]]), one change named
([[an-issue-states-one-solution]]), one closing line per issue
([[an-issue-is-closed-by-its-commit]]), and sections opened with headings
([[issue-sections-take-headings]]).
