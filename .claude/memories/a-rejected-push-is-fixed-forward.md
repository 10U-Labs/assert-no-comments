---
name: a-rejected-push-is-fixed-forward
description: A red run is answered by one follow-up commit that fixes every failed check, never by an amend and force-push
metadata:
  type: feedback
---

# A rejected push is fixed forward

Answer a red run with a follow-up commit; do not amend and force-push.

**Why:** the commit is already on `main`, the only branch there is, per
[[commits-go-straight-to-main]]. Every check is a job of its own running in
parallel with the rest, so a red run names every check that failed rather than
the earliest one.

**How to apply:** read the whole list, with `gh run view --log-failed`, and
answer all of it in one commit, pushed once per
[[push-once-and-let-the-run-finish]].
