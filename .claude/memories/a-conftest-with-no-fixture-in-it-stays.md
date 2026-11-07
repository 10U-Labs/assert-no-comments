---
name: a-conftest-with-no-fixture-in-it-stays
description: test/integration/conftest.py and test/e2e/conftest.py are zero bytes and stay, so the next fixture has a place to go
metadata:
  type: feedback
---

# A conftest with no fixture in it stays

`test/integration/conftest.py` and `test/e2e/conftest.py` are zero bytes, and
they stay. Zero bytes is what an empty file is here: a docstring, a `pass` or a
blank line to stand in for content is content, and the file is empty or it is
not.

**Why:** the file is what tells whoever writes the next fixture that this level
exists to hold one; left to itself a session writes setup into the test file
already open in front of it.

**How to apply:** delete neither file, and put nothing in either but a fixture.
Nothing in CI fails when one of them is deleted, so the file is kept for the
reader rather than for a gate.
