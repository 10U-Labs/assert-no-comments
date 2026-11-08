---
name: memories-live-in-dot-claude-memories
description: This repository's conventions are memories in .claude/memories/, set by an absolute autoMemoryDirectory in the untracked .claude/settings.local.json; there is no CLAUDE.md
metadata:
  type: project
---

# Memories live in .claude/memories

A convention learned in a session is a memory in `.claude/memories/`, one fact
to a file and listed in `MEMORY.md`, and there is no `CLAUDE.md`.
`.claude/settings.json`, which is tracked, sets `autoMemoryEnabled: true`;
`.claude/settings.local.json`, which is gitignored, sets `autoMemoryDirectory`
to the absolute path of this clone's `.claude/memories/`, so that the memory a
session writes lands in the tree.

**Why:** the default store under `~/.claude/projects/` belongs to one machine,
is unversioned, and is invisible to everyone else working here.
`autoMemoryDirectory` takes only an absolute or `~/`-prefixed path; a relative
one is ignored without a warning and the default is used instead, so what a
session writes lands outside the tree and what the tree holds goes unread. An
absolute path is a fact about one machine, so it lives in the untracked file.
10ulabs.com, api.10ulabs.com and wan-synthesizer are laid out the same way.

**How to apply:** a new clone writes its own `.claude/settings.local.json`. The
path is resolved once, when `claude` starts, so a change to it takes effect only
after a restart; a session whose system prompt names a
`~/.claude/projects/.../memory/` path is a process older than the setting, not a
broken setting. Either way, read `.claude/memories/*.md` and write there. What
belongs in a memory at all is [[a-memory-holds-only-what-the-tree-cannot-say]].
