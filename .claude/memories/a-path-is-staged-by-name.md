---
name: a-path-is-staged-by-name
description: Stage each file by its own path; never git add -A or git add . in this repository
metadata:
  node_type: memory
  type: feedback
  originSessionId: 522cfb64-59f2-4927-8369-5ddee3a12124
  modified: 2026-11-08T01:58:35.362Z
---

# A path is staged by name

Never use `git add -A` or `git add .`. Stage each file by its path.

**Why:** `.claude/` is tracked, since it holds the memories, `settings.json` and
the autopilot skill, but `.gitignore` excludes only `settings.local.json` from
it. The `scheduled_tasks.lock` the cron reminders write beside them is kept out
only by this clone's `.git/info/exclude`, which a fresh clone does not have, so
a sweep there stages the lock with the memories. Other untracked scratch turns
up from time to time as well, so naming each path is the rule regardless.

**How to apply:** name every path, keep removals off the `git add` line per
[[git-add-stages-nothing-when-one-path-is-missing]], and read the index back per
[[the-index-is-read-back-before-committing]].
