---
name: gh-search-returns-at-most-1000-issues
description: gh issue list with --search or --label goes through GitHub search, which returns at most 1000 issues; a listing of every open issue uses --limit 10000 and keeps or leaves out labels inside --jq
metadata:
  type: feedback
---

# gh search returns at most 1000 issues

A `gh issue list` that carries `--search` or `--label` is sent through GitHub's
search API, which returns at most 1000 results whatever `--limit` asks for.
Without either, it pages through the repository's issues over GraphQL and
returns as many as `--limit` allows. A listing of every open issue is therefore
`gh issue list --state open --limit 10000`, with labels kept by
`map(select(any(.labels[]; .name == "<label>")))` or left out by
`map(select(all(.labels[]; .name != "<label>")))` inside `--jq`.

**Why:** a search listing past the cap drops the oldest issues without a word,
and a loop that takes the lowest number first never sees them. `GH_DEBUG=api`
shows which way a listing goes: with `--label`, `gh issue list` sends a GraphQL
query named `IssueSearch`; with neither flag, one named `IssueList`.

**How to apply:** write no `--search` or `--label` into a command that has to
see every issue, such as the autopilot's loop commands, and treat a listing
whose length equals its `--limit` as cut short.
