---
name: a-memory-holds-only-what-the-tree-cannot-say
description: A rule is a memory only if working from the tree alone would get it wrong; it adds the reason, never the history, and repeats nothing release.yml, README.md, the code or git log already answers
metadata:
  type: feedback
---

# A memory holds only what the tree cannot say

A rule is a memory only if working from the tree alone would get it wrong:
whatever `release.yml`, `README.md`, the code or `git log` already answers is
not repeated in a memory. What a memory adds to the tree is the reason for its
rule, never the rule's history.

**Why:** a second copy goes stale with nothing to catch it, and `git log`
already keeps the history. A date, a commit hash or an issue number given as
provenance, or the incident that set a rule, tells the next session when the
rule arrived rather than why it holds.

**How to apply:** before writing a memory, look for the fact in the tree; where
the tree states it, the memory is only the part it does not, which is why. The
**Why:** gives the reason for the rule in the present tense, never when, by whom
or after what incident it was set, and a rule that changes is rewritten in place
rather than annotated with what it used to say. An issue number written as an
example of the rule, rather than as its origin, stays, and so do the
`originSessionId` and `modified` lines the memory tool writes into the
frontmatter, which are its bookkeeping rather than part of the memory.

`MEMORY.md` is the one exception: it is navigation for a reader of the memories
rather than a claim about anything else in the tree, and it is rewritten in the
same edit as the memories it lists, so it cannot drift from them the way a
copied fact drifts from its source. A session that has just read this rule will
reach for the index first. Leave it, and update it.
