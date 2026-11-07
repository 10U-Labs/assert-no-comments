---
name: a-tier-is-a-directory-not-a-marker
description: A test's tier is the directory it sits in; no pytest.mark marker restates it, and a tier is selected by naming its directory
metadata:
  type: feedback
---

# A tier is a directory, not a marker

A test belongs to the tier whose directory it sits in, and that is the only
thing that says so. Do not mark it.

**Why:** 49710d3 deleted the three `pytest.mark` markers and the
`pytest_configure` that registered them, because no step in `release.yml` passes
`-m` — each names `test/unit/`, `test/integration/` or `test/e2e/` — so the
registration existed only to keep the decorators from failing the jobs under
`--pythonwarnings=error`, and each of the 40 decorators restated by hand the
directory its file was already in, which nothing checked. A marker that has to
agree with a path is a comment that has to agree with its code.

**How to apply:** select a tier by naming its directory, and add a marker only
where the thing being selected is not a directory. `usefixtures` and the rest of
pytest's builtins are unaffected; those it registers itself.
