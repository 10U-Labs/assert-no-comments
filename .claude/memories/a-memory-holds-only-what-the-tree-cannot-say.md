---
name: a-memory-holds-only-what-the-tree-cannot-say
description: A rule is a memory only if working from the tree alone would get it wrong; nothing release.yml, README.md, the code or git log already answers is repeated
metadata:
  type: feedback
---

# A memory holds only what the tree cannot say

A rule is a memory only if working from the tree alone would get it wrong:
whatever `release.yml`, `README.md`, the code or `git log` already answers is
not repeated in a memory.

**Why:** a second copy goes stale with nothing to catch it.

**How to apply:** before writing a memory, look for the fact in the tree; where
the tree states it, the memory is only the part it does not, such as why, or
what was tried and lost. `MEMORY.md` is the one exception: it is navigation for
a reader of the memories rather than a claim about anything else in the tree,
and it is rewritten in the same edit as the memories it lists, so it cannot
drift from them the way a copied fact drifts from its source. A session that has
just read this rule will reach for the index first. Leave it, and update it.
