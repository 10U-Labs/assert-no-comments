---
name: ci-shows-all-output
description: "Every CI step shows all the output its tools produce, passing or failing: no quiet or count flags, no /dev/null, no captured output left unprinted"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T02:14:50.772Z
---

# CI shows all output

Every step of this repository's workflows shows everything its tools print, for
passing runs as well as failing ones. That means:

- no `-q`, `--quiet`, `--silent` or `--count` flags, and `--verbose` wherever a
  tool has one;
- no `>/dev/null`;
- output captured into a variable or a file is printed as well;
- `PYTHONUNBUFFERED=1` for a Python script that prints as it goes, so each line
  reaches the log when it is printed rather than all at once at the end.

`action.yml`'s `quiet` and `count` inputs are for the repositories that use the
action. This repository's own `assert-no-comments` job leaves them off and sets
`verbose`. A plain string test, such as `grep -q` on a value already in the
log, hides nothing and can stay.

**Why:** the user wants to read a step's log without guessing what was left
out. A step that prints nothing, or prints only when it fails, reads as hidden
output.

**How to apply:** when writing or reviewing a CI step or a script it runs, show
what it runs, and stream it rather than reporting at the end.
