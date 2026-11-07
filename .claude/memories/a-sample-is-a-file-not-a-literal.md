---
name: a-sample-is-a-file-not-a-literal
description: Source text handed to a reader is a .txt file under the samples/ directory of its tier, named for its test and loaded with sample()
metadata:
  type: feedback
---

# A sample is a file, not a literal

Source text handed to a reader is a `.txt` file under the `samples/` directory
of the tier that reads it, named for the test that reads it, and loaded with
`sample()`. The eight that make up the project tree live in each CLI tier's
`samples/project/`, because they belong to no single test and both CLI tiers
write them.

**Why:** `.txt` is in no gate's glob and in no entry of `READERS`, so a sample
carrying a comment sits in the tree untouched by the tool that would otherwise
fail the build over it, and needs no `--exclude`.

**How to apply:** never write source text as a string literal in a test.
