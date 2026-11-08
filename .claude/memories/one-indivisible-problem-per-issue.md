---
name: one-indivisible-problem-per-issue
description: "An issue holds one problem: one fault in how a file is read, with every case of it listed, or else one defect with one fix; two problems are split, and issues holding cases of one fault are merged"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T02:11:20.625Z
---

# One indivisible problem per issue

An issue holds one problem and no more.

- **An issue about how a file is read** holds one fault in the reading, such as
  a form of comment a reader misses, and lists every case of it: each language
  whose reader shares the fault and each place in a file where it shows. Two
  faults are two issues, even when they share a language or a first report.
  Two cases of one fault are one issue, even when they were found apart.
- **Any other issue**, about a memory, a workflow, a setting or the tool's own
  behaviour, holds one defect with one fix.

**Why:** an issue holding two problems never closes cleanly: it sits open while
half of it is done, and its title says less than its body. An issue holding one
case of a fault closes too soon: its fix reaches that case, the other cases
surface later as issues of their own, and one fault becomes a chain of issues,
each paying for a run and a release of its own.

**How to apply:** ask of each finding which fault it shows. Where an issue of
that fault is open, add the finding to it as a case; where none is, open one
that lists every case. An open issue found holding two problems is split on the
spot: its number stays with the problem its title leads with, and the other
moves to a new issue. Open issues found holding cases of one fault are merged
into the lowest-numbered of them, and the others are closed as duplicates of
it. A split divides problems, not file lists: two symptoms of one defect stay
together. Issues that stay apart can still be worked on as one piece, per
[[issues-that-share-code-are-one-piece-of-work]], and each names one change,
per [[an-issue-states-one-solution]].
