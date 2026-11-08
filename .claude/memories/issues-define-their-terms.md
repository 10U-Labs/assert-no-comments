---
name: issues-define-their-terms
description: "An issue's title and body say what each thing they name is, a file's path and contents, a grammar's term, what each cited source has to do with the defect, so a reader who has never seen the run can follow it"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T02:14:42.606Z
---

# Issues define their terms

An issue's title and body carry the context they rely on. A file is named by
its path in the repository, and what it holds is shown or said. A term from a
grammar or from the tool's own code, such as the node name `html_comment`, is
explained: which grammar uses it and what source text it covers. What
assert-no-comments does is said as it happens ("exits 1, reporting a comment
where there is none"), never only as a noun the reader must already know ("a
false finding"). Every source cited, a language's specification or a grammar's
rule, is tied to the defect in the same sentence, never listed as if the
connection were obvious.

**Why:** the session that files an issue knows the run it has just read and
writes as if the reader had read it too. A reader who opens the issue from the
list has none of that, and cannot act on a file, a term or a source whose
meaning and tie to the defect are left out.

**How to apply:** before filing or editing an issue, read its title and body as
someone who has opened it from the issue list with nothing else. For each name,
term and source, ask what it is and why it is there, and add the sentence that
answers. The form is free, per [[issues-have-no-fixed-form]]; the context is
not.
