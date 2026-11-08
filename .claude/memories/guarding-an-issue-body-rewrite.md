---
name: guarding-an-issue-body-rewrite
description: "Rewriting an issue body by fetching it to a file, editing it and writing it back with gh issue edit --body-file never writes an empty file, since that wipes the body; an earlier version comes back through GraphQL userContentEdits"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T02:14:46.930Z
---

# Guarding an issue body rewrite

When an issue body is rewritten by fetching it to a file, editing the file and
writing it back with `gh issue edit --body-file`, chain each command with `&&`
and check that the file is not empty before the write.

**Why:** GitHub answers a fetch with a server error at times. The shell's
redirect has already created the file, so a failed fetch leaves it empty, and
writing that back replaces the whole body with nothing.

**How to apply:** fetch with
`gh issue view <N> --json body --jq .body > <file> && wc -c < <file>`, so the
size shows in the same call. An edit made by a script joins the same chain.
Write back with `[ -s <file> ] && gh issue edit <N> --body-file <file>`. A
wiped body is recovered from the issue's edit history, whose nodes run newest
first and whose `diff` holds each version's full text:

```sh
gh api graphql -f query='query{repository(owner:"10U-Labs",name:"assert-no-comments"){issue(number:<N>){userContentEdits(first:5){nodes{createdAt diff}}}}}'
```
