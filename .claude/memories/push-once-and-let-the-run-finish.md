---
name: push-once-and-let-the-run-finish
description: Push once per issue and read that run; a second push on the same ref cancels the first run and costs that commit its release
metadata:
  type: feedback
---

# Push once and let the run finish

Push once per issue and read that run before pushing again.

**Why:** both workflows cancel the run in progress when a second push lands on
the same ref. The tree is still verified, by the later run, but the cancelled
commit loses its own release, because `release` never gets its `needs`.

**How to apply:** find the run per [[find-a-run-by-the-full-hash]] and wait for
every run the push started to finish, per [[ci-is-the-source-of-truth]].
