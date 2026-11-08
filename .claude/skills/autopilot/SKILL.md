---
name: autopilot
description: Start, restart or stop the autopilot reminders. Use when the user says "start autopilot", "go autonomous on the open issues", "restart autopilot", "stop autopilot" or "reminders only", or asks to clear the reminders. Takes "start", "start bylabel <label>", "start reminders-only", the same three after "restart", or "stop"; every form but "reminders-only" and "stop" also takes `--skip-label <label>`, repeatable.
---

# Autopilot

Fetch `CronCreate`, `CronList` and `CronDelete` with `ToolSearch` first.

Each standing rule gets a reminder of its own, so no rule can be quietly dropped
from a merged block of text, and each reminder has its own minute of a
fifteen-minute cycle, so they arrive one at a time. A reminder fires only while
the session is idle, which is why every wait runs in the background, per
`.claude/memories/a-wait-runs-in-the-background.md`.

This is the autopilot of 10ulabs.com, api.10ulabs.com and wan-synthesizer with
the batching taken out. A commit there solves every open issue of one workflow's
stack; a commit here solves one issue, per
`.claude/memories/one-issue-one-commit.md`, so the loop takes one issue at a
time.

## Standing reminders

Every form.

| Cron | Prompt |
| --- | --- |
| `2,17,32,47 * * * *` | `REMINDER: Code is changed, committed and pushed only in the repository this session runs in. A problem whose code another repository owns, such as one of the assert tools a gate installs, is filed as an issue there, or an issue here is transferred there, and the session goes no further with it: that repository is not edited, its workflows and runs are not read, and nothing is waited for there.` |
| `3,18,33,48 * * * *` | `REMINDER: Let every push carry exactly one commit, and let that commit solve exactly one issue, its tests written first and landing with it, closed by a Closes #N line of its own. Two issues share a commit only where the fix for one is contained in the fix for the other; an issue that will not fit one commit is two issues, and the second is filed rather than pushed separately.` |
| `5,20,35,50 * * * *` | `REMINDER: Before working on an issue, ensure the issue is up to date. If it is outdated, rewrite its title and body as necessary and ensure its labels are correct. Ensure too that it documents a single indivisible problem and names one change that solves it; if it documents more than one problem, split it into one issue per problem, reusing the issue itself as one of those splits.` |
| `7,22,37,52 * * * *` | `REMINDER: While any CI run for a commit pushed to this repository is in progress, only wait, in the background: no diagnosis, edits or commits.` |
| `8,23,38,53 * * * *` | `REMINDER: File what you find as issues, each documenting one indivisible problem. Solve one now only if the work in hand cannot move forward without it; otherwise move on.` |
| `12,27,42,57 * * * *` | `REMINDER: An issue you file is placed before you go back to work, and a blocked_by edge is written only where the block is real. Add one when the issue in hand cannot be finished until the new one is, or when some other open issue cannot. Where nothing waits on it, file it with no edge and move on: an ordering is not a dependency, and an edge written to give an issue a place in the queue is a false statement about the work.` |

## Loop reminders

Every form but `reminders-only`.

On `1,16,31,46 * * * *`, for `start`:

```text
REMINDER: Run gh issue list --state open --search '-label:"needs decision"' --limit 1000 --json number,title,labels --jq 'sort_by(.number) | map({number, title, labels: [.labels[].name]})' for the open issues no decision holds back, lowest number first; take the first that no open issue blocks, in this repository or another, solve it alone in one commit and one push, and run the same command again when it closes. An issue labelled 'needs decision' is left to a person.
```

For `start bylabel <label>`:

```text
REMINDER: Run gh issue list --state open --label '{L}' --search '-label:"needs decision"' --limit 1000 --json number,title,labels --jq 'sort_by(.number) | map({number, title, labels: [.labels[].name]})' for the open issues labelled '{L}', lowest number first; take the first that no open issue blocks, in this repository or another, solve it alone in one commit and one push, and run the same command again when it closes. The open issues without the label '{L}' are not this loop's work, and an issue labelled 'needs decision' is left to a person.
```

| Cron | Prompt |
| --- | --- |
| `4,19,34,49 * * * *` | `REMINDER: Continue autonomously, unless you need human feedback about ANYTHING — not just about what to take next. When you do, rewrite the issue's title if necessary, rewrite the issue's body, label the issue 'needs decision', and move on to the next issue.` |
| `11,26,41,56 * * * *` | `REMINDER: Before labeling an issue with 'needs decision', assess the issue against the rulebook in .claude/memories/ and the code to determine whether it truly needs a decision.` |

## Start and restart

Each `--skip-label <label>` adds `-label:"<label>"` to the loop command's
`--search` and appends `An issue labelled '<label>' is left to a person,
whatever else it carries.` to its reminder.

An issue is blocked while `gh api
repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by` lists an open
issue, wherever that issue lives. A blocker in another repository is read, never
worked: the issue here waits for it.

1. Unless `reminders-only`, make sure the label the loop leaves to a person
   exists: when `gh label list --search 'needs decision' --json name --jq
   '.[].name'` does not print `needs decision`, create it with `gh label create
   'needs decision' --description 'Left to a person' --color d876e3`.
2. Unless `reminders-only`, run the loop command once; if it names no issue,
   schedule the standing reminders only.
3. Call `CronList`. On `start`, `CronDelete` each job on one of the form's slots
   whose prompt differs from that slot's. On `restart`, `CronDelete` every job
   that is not one of the form's reminders, keeping one per slot.
4. `CronCreate` with `recurring: true` each of the form's reminders not already
   scheduled, the label substituted for `{L}`.
5. Tell the user how many reminders are running, and the two limits that come
   with them: the jobs live in this session only and are gone when it ends, and
   recurring jobs auto-expire after seven days.
6. Unless `reminders-only`, solve the first issue the command names that no open
   issue blocks, alone, per `.claude/memories/one-issue-one-commit.md`. When no
   issue can be taken, say which label or blocking issue holds back each open
   issue and stop.

## Writing a blocked_by edge

`gh api repos/{owner}/{repo}/issues/{number}/dependencies/blocked_by -F
issue_id=<id>`, where `{number}` is the issue that waits and `<id>` is the
blocker's numeric id from `gh api repos/{owner}/{repo}/issues/{n} --jq .id`, not
the node id `gh issue view --json id` returns. Sent with `-f` instead of `-F`,
it is rejected with HTTP 422.

## Stop

`CronDelete` every job `CronList` returns, then call `CronList` again to confirm
it is empty and report how many jobs were deleted. A `CronList` that returns
nothing is not a failure; say the schedule was already empty.
