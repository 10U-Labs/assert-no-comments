---
name: a-wait-runs-in-the-background
description: A wait for CI is a Bash run_in_background or a Monitor, never a foreground sleep or gh run watch, so the session stays idle and the autopilot reminders can fire
metadata:
  type: feedback
---

# A wait runs in the background

Waiting for a workflow run, or for anything else that takes minutes, is done
with `Bash` and `run_in_background: true`, which notifies once when the command
exits, or with `Monitor`, which notifies once per event; never with a foreground
`sleep`, `gh run watch` or polling loop in the session's own shell.

**Why:** a cron reminder fires only while the session is idle. A foreground wait
holds the session busy for the whole run, so the autopilot's standing rules stop
arriving exactly while a push is in flight, and the user cannot type either.
10ulabs.com, api.10ulabs.com and wan-synthesizer hold the same rule for the same
reason.

**How to apply:** start the wait in the background, end the turn, and act on the
notification. `gh run watch --exit-status` is fine inside the background
command; it is the foreground that is the problem. Idle still means idle: the
autopilot's wait reminder forbids diagnosis, edits and commits while the run is
in progress. Find the run per [[find-a-run-by-the-full-hash]].
