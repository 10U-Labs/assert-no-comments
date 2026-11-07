---
name: anything-importable-lives-outside-conftest
description: conftest.py holds only fixtures and hooks; code two tiers share by import is lib/test_read_sample and lib/test_trees, reached through PYTHONPATH=lib
metadata:
  type: feedback
---

# Anything importable lives outside conftest

`conftest.py` holds fixtures and hooks, which pytest finds by itself; a test
module never imports from it. What two tiers share by import — `read_sample`,
the project paths, `CLEAN_PROJECT` and `FULL_RUN` — is two packages under
`lib/`, because `lib/` is where code used more than once in this repository
goes: `test_read_sample` reads one, `test_trees` holds the trees the CLI is run
over: the paths of the files in them, the two versions of the tree, and the
`FULL_RUN` that names them the way the `trees` argument does.

They are separate because four of the five importers want one and not the other,
and because a file reader and a fixture tree change for different reasons;
`FULL_RUN` stays with the tree it names rather than becoming a third package.
The package is not named after the tool: what belongs there is whatever more
than one caller needs and no fixture should hold, which is a fact about the code
rather than about `assert_no_comments`. The tests themselves do not move there:
nothing imports a test, so `test/unit/`, `test/integration/` and `test/e2e/`
stay where they are.

**Why:** importing a conftest instead works only while a package layout keeps
its module name unique, and binds the suite to that layout for a reason nothing
states.

**How to apply:** every job reaches the module through `PYTHONPATH=lib`, since
`test/` carries no `__init__.py` and pytest puts only a test's own directory on
the path.
