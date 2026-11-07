---
name: test-first
description: The test is written first, then the code that makes it pass; the red and green observations belong to CI
metadata:
  type: feedback
---

# Test first

The test is written first, then the code that makes it pass.

**Why:** test-first is authoring order. The red and the green observations
belong to CI, since nothing runs locally, per [[ci-is-the-source-of-truth]].

**How to apply:** the test and the code land in the same commit, per
[[commits-go-straight-to-main]].
