---
name: issue-sections-take-headings
description: "Each section of an issue body opens with a ## heading on its own line, never with a bolded lead sentence"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 480159be-d838-4153-abff-13fe6b4fba0b
  modified: 2026-11-08T00:00:43.624Z
---

# Issue sections take headings

When an issue body falls into sections, open each with a Markdown heading on
its own line, such as `## The defect` or `## The fix`, with the section's prose
starting below it. Never mark a section by bolding its opening words inline, as
in `**The defect.** The reader misses…`.

**Why:** headings render as real structure on GitHub, show in the outline and
can be linked to, where a bolded lead sentence is only emphasis run into the
paragraph.

**How to apply:** use `##`, since the issue title stands above the sections,
and a short noun phrase with no trailing period for the heading. When editing
an issue written with bolded leads, convert them to headings. This is the one
formatting rule for issues; otherwise [[issues-have-no-fixed-form]] holds.
