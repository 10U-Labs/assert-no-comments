---
name: unpushed-commits-go-out-first
description: "A commit sitting on local main unpushed is pushed, one per push, before any new work starts"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T01:58:46.912Z
---

# Unpushed commits go out first

Push any commit that sits on local `main` unpushed before starting new work.

**Why:** an unpushed commit is work CI has not checked. Building more on top of
it lets it go stale against the tree and buries a red run under the work
stacked above it.

**How to apply:** `git log origin/main..main` lists them. Push the oldest alone
with `git push origin <sha>:main` and wait for its runs per
[[push-once-and-let-the-run-finish]] before pushing the next, because a push
carrying several commits runs only the newest and releases none of the others.
