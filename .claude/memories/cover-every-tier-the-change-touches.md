---
name: cover-every-tier-the-change-touches
description: unit/ for readers and CLI helpers, integration/ for the CLI over a real tree, e2e/ for the installed console script; unit and integration each gate on full branch coverage
metadata:
  type: feedback
---

# Cover every tier the change touches

`unit/` for the readers and the CLI helpers, `integration/` for the CLI driven
over a real tree, `e2e/` for the installed console script run the way a workflow
step runs it, all three under `test/`. A change is covered in every tier it
touches.

**Why:** unit and integration each gate on full branch coverage on their own
rather than on the two together. `e2e-tests` carries no coverage gate and
cannot, since it runs the command in another process.

**How to apply:** a line reachable only through the console script is reached by
`run_cli`, the in-process fixture in the root `conftest.py`, and asserted again
through the subprocess.
