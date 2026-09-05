---
name: panjika
description: >
  Read and write the agent ledger for this repository. Use it before you edit a file, to see
  which agent sessions changed it and what happened to their changes. Use it after a turn, to
  see if your own changes went into git, are still uncommitted, or were replaced. Triggers
  on: "did my change land", "who edited this file", "agent history", "what happened to my
  edit", "panjika".
---

# panjika

A JSONL ledger of agent sessions, the files they changed, and the place those changes went to in git. panjika only adds to it. Each harness in this repository writes to the same ledger.

## Before you edit a file

```sh
panjika trail path/to/file.py
```

This gives each agent session and each commit that changed the file, newest first, in one list. Each session shows the branch it ran on.

Read it when a file looks like another agent changed it. Read it when your change can remove an earlier one.

## After you change something

```sh
panjika landed            # the newest session in this ledger
panjika landed --json     # the same answer, as records
```

You get one verdict for each file. Read the state first.

| state | what it means | what to do |
|---|---|---|
| `landed` | each line is in a commit | nothing |
| `partly_landed` | some lines are in a commit, and some are gone or not committed | read `why`. It counts them |
| `pending` | the lines are in the working tree, and nothing is committed | commit them, or give the reason |
| `replaced` | no line is in the file here. `why` gives the commit and the author that own them now | do not write it again. Read that commit first |
| `gone` | the file is not in the working tree | check if a person moved it |
| `untracked` | git does not track the file | run `git add`, or the change cannot go into git |
| `uncertain` | a commit changed the file after the session, but there is no line record | read those commits, or run panjika where the session ran |
| `unknown` | there is no line record and no later commit | nothing to read |

`evidence` says how accurate the answer is.

`lines` means panjika compared your lines with `git blame`. This answer stays correct if a person formats the file again, or moves the lines. It also stays correct if the lines go into git with another change.

`path` means panjika only knows that a commit changed the file. That commit can be a revert, or it can hold your change. panjika cannot know which. Thus `path` gives `uncertain` and never `landed`.

## Branches

A verdict is about one working tree. Four fields say which one.

- `branch` is the branch that the session ran on.
- `branch_gone` is true if a person deleted that branch.
- `elsewhere` gives each branch that has every line of the session in its copy of the file. panjika fills it in for `replaced` and `gone`.
- `anywhere` is true for `landed`, `partly_landed` and `pending`, and for any branch in `elsewhere`. It is false for `uncertain`, `unknown` and `untracked`, because panjika cannot find the lines there.

A change made on a feature branch reads `replaced` from `main`. Read `elsewhere` before you decide anything from `replaced`.

`replaced` with an empty `elsewhere` and `evidence` of `lines` means the change is on no branch here.

panjika compares the text of a line. Two branches that wrote the same line each count as a branch that has it.

## How to plan with it

Stop for `replaced` with an empty `elsewhere`. Do not make the same change again. Read the commit in `why`. Then work with that commit, or say that the two changes do not agree.

Many files with `pending` at the end of a turn usually means the work is done and not committed.

## From Python

```python
from panjika import landed, trail, log, session

for v in landed():                 # the newest session in this repository
    print(v.state, v.path, v.why, v.branch)

trail('src/app.py')                # the sessions and the commits for one file
log(limit=10, harness='codex')     # what codex did here
session('latest').files            # the files that the last session changed
```

`landed()` gives `Verdict` objects. Each one has `state`, `why`, `kept`, `total`, `survived`, `evidence`, `commits`, `branch`, `branch_gone`, `elsewhere` and `anywhere`.

## From a harness with no adapter

```sh
panjika record '{"session":"my-run","do":"begin","harness":"my-script","prompt":"regenerate fixtures"}'
panjika record '{"session":"my-run","do":"step","tool":"make","target":"fixtures","ok":true}'
panjika record '{"session":"my-run","do":"end","status":"done"}'
```

## Setup

```sh
panjika install        # the hooks for Claude Code and Codex, the git hook, and this skill
panjika init           # only the ledger folder
panjika backfill       # the sessions that ran before the ledger existed
```

A hook only sees the next event. A ledger that you install today knows nothing about yesterday. `panjika backfill` reads the transcripts of the harness, and the transcripts of its subagents. Run it before you decide from an empty trail that no session changed the file.

You commit `.panjika/ledger/`. You do not commit `.panjika/detail/`. The `detail` tier holds the full tool arguments, the full outputs, and the line hashes that `landed` needs.
