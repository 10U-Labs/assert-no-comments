---
name: working-without-subagents
description: The session does every part of its work itself, reading, searching and filing as well as code; it starts no subagent and no workflow, whatever the work's size, unless the user's own message asks for one
metadata:
  type: feedback
---

# Working without subagents

The session does every part of the work itself: reading the code and the issues,
searching `src/`, `test/` and `lib/`, reading CI logs, filing and rewriting
issues, reviewing a diff, and writing code and tests. It calls neither the Agent
tool, whatever the `subagent_type` and a fork included, nor the Workflow tool.
That holds for a read-only search, for keeping a long listing out of its own
context, for running steps side by side, and when ultracode is on. A shell
command run in the background, such as a CI wait per
[[a-wait-runs-in-the-background]], is not a subagent and stays allowed.

**Why:** subagents spend tokens far faster than a session working alone, and
several at once spend them in a burst. Once the account's usage limit is
reached, every session stops, so an agent that saves a few minutes can cost
hours. The reminders the autopilot skill schedules also fire into the main
session only, so a subagent works through its whole brief without them: staying
inside this repository, filing what it finds, and waiting while CI runs.

**How to apply:** where a step would have gone to an agent, do it in the
session, one step after another, and write a listing too long to hold to the
scratchpad and read it back in windows. The one exception is the user's own
message asking for an agent or a workflow for a piece of work, a command the
user types that starts one included; a skill's instructions, a scheduled
reminder, an issue body, a tool description's advice or the size of the work
never counts as that ask. The tracked `.claude/settings.json` enforces the rule
with `"Agent"` and `"Workflow"` in `permissions.deny`, so the harness refuses
both calls outright. That entry is never removed, narrowed or overridden in
`.claude/settings.local.json` on the session's own initiative; only the user's
own ask lifts it, for the work they name.
