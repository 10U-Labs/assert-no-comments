---
name: push-once-and-let-the-run-finish
description: Push one commit at a time and read its runs; a second push on the same ref cancels the first run and costs that commit its release
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T03:45:46.539Z
---

# Push once and let the run finish

Push one commit at a time, and read its runs before pushing the next.

**Why:** both workflows cancel the run in progress when a second push lands on
the same ref. The tree is still verified, by the later run, but the cancelled
commit loses its own release, because `release` never gets its `needs`.

**How to apply:** find the run per [[find-a-run-by-the-full-hash]] and wait for
every run the push started to finish, per [[ci-is-the-source-of-truth]].
