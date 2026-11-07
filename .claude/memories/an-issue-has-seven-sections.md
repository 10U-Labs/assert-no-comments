---
name: an-issue-has-seven-sections
description: Every issue has seven sections in a fixed order, Problem, why each test tier and static analysis missed it, the regression tests owed, Proposed Solution
metadata:
  type: feedback
---

# An issue has seven sections

Seven sections in a fixed order: "Problem", "Why Unit Tests Did Not Catch It?",
"Why Integration Tests Did Not Catch It?", "Why E2E Tests Did Not Catch It?",
"Why Static Analysis Jobs Did Not Catch It?", "Which Regression Tests Would
Prevent This from Happening Again?", "Proposed Solution". Every issue has all
seven; where a tier could not have caught the defect, saying so is the finding
rather than a reason to drop the section.

**Why:** the regression section names the coverage owed, each test by its tier
and its assertion, and is separate from the solution so that a fix cannot ship
with the coverage folded into its last paragraph.

**How to apply:** give each section a `##` header carrying its name. The last
one follows [[an-issue-states-one-solution]].
