---
name: only-wait-while-a-run-is-in-progress
description: "While any run of either workflow is in progress for a pushed commit, only wait; no diagnosis, edits or commits until it lands, with or without the autopilot"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T01:58:44.311Z
---

# Only wait while a run is in progress

While any run for a pushed commit is in progress, of `release.yml` or
`markdownlint.yml`, do nothing but wait for it: no probing of the failing
file, no edits, no commits.

**Why:** a run's findings decide the next step, and work done before they land
is done on a guess about them. The rule holds whether or not the autopilot is
running; its wait reminder only repeats it.

**How to apply:** after a push, start the wait in the background per
[[a-wait-runs-in-the-background]] and end the turn. Read the run when it
completes, then act. A run a later push will cancel is no exception: wait for
the new run rather than working under it.
