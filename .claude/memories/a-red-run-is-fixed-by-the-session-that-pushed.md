---
name: a-red-run-is-fixed-by-the-session-that-pushed
description: "When the run a push starts goes red, the session that pushed fixes it, whether the push broke something or inherited the break"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T01:58:50.436Z
---

# A red run is fixed by the session that pushed

When a run that a push starts goes red, the session that pushed fixes it,
whether the push caused the failure or inherited it from an earlier commit.
What sets the rule off is the push's own run going red, not a red run the
session merely comes across.

**Why:** a change is unverified until every job that checks it has passed, and
a failed job reads the same whether the change broke something or inherited a
break. `release` needs every other job in `release.yml`, so it is skipped
rather than failed, and an inherited failure hides the change's own result and
holds back its release for as long as it stands.

**How to apply:** once the run completes, `gh run view --log-failed` tells a
break the change caused from one it inherited. Fix both kinds, in one commit
per [[a-rejected-push-is-fixed-forward]], pushed on its own before the next
piece of work: pushed together, a second red run could not say whether the
fix or the new work broke it.
