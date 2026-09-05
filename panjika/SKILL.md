---
name: panjika
description: >
  Read and write the agent ledger for this repository. Use it before editing a file to see which
  agent sessions have touched it and what became of their changes, and after a turn to check
  whether your own changes landed in git, are still uncommitted, or were written over. Triggers
  on: "did my change land", "who edited this file", "agent history", "what happened to my edit",
  "panjika".
---

# panjika

An append-only JSONL ledger of agent sessions, the files they touched, and where those changes
went in git. Every harness working in this repository writes to the same one.

## Before you edit a file

```sh
panjika trail path/to/file.py
```

Every agent session and every commit that has ever touched that file, newest first, on one
timeline, each session with the branch it ran on. Read it when a file looks like somebody has
been here before, or when a change you are about to make may undo one.

## After you have changed something

```sh
panjika landed            # the newest session in this ledger
panjika landed --json     # the same, as records
```

One verdict per file. Read the state first.

| state | what it means | what to do |
|---|---|---|
| `landed` | every line is in a commit | nothing; it is done |
| `partly_landed` | some lines are committed, some are gone or still uncommitted | read `why`; it counts them |
| `pending` | the lines are in the working tree and nothing is committed | commit, or say why you are not |
| `replaced` | none of the lines survive here; `why` names the commit and author that own them now | do not rewrite it. Read that commit first |
| `gone` | the file is not in the working tree | check whether it moved |
| `untracked` | git is not tracking the file | `git add` it, or it will never land |
| `uncertain` | commits touched the file since, but no line record is here to say whether this change is in them | read those commits, or run where the session ran |
| `unknown` | no line record and no commit since | nothing to go on |

`evidence` says how sure the verdict is. `lines` matched the exact lines you wrote against
`git blame`, which survives the file being reformatted, moved, or committed together with
somebody else's change. `path` only knows that some commit touched the file afterwards, which
is as consistent with a revert as with survival, so on `path` alone the answer is `uncertain`
and never `landed`.

## Branches

A verdict is about one working tree. Three fields say which.

- `branch` is the branch the session ran on.
- `branch_gone` is true when that branch no longer exists.
- `elsewhere` names the branches whose committed copy of the file still holds every line. It is
  filled in for `replaced` and `gone`.
- `anywhere` is true for `landed`, `partly_landed` and `pending`, and for anything `elsewhere`
  found. It is false for `uncertain`, `unknown` and `untracked` too, because none of those knows
  where the lines are.

A change made on a feature branch reads as `replaced` from `main`. Check `elsewhere` before
concluding anything from `replaced`. `replaced` with an empty `elsewhere` and `evidence` of
`lines` means the work is on no branch here. Two branches that wrote the same line
independently both count as holding it, because the match is on content.

## Planning against it

`replaced` with nothing in `elsewhere` is the one worth stopping for. Making the same change
again is almost never the next thing to do. Read the commit named in `why`, then either work
with it or say plainly that the two changes disagree.

`pending` across many files at the end of a turn usually means the work is done and uncommitted.

## From Python

```python
from panjika import landed, trail, log, session

for v in landed():                 # the newest session in this repository
    print(v.state, v.path, v.why, v.branch)

trail('src/app.py')                # sessions and commits on one timeline
log(limit=10, harness='codex')     # what codex has been doing here
session('latest').files            # what the last session changed
```

`landed()` returns `Verdict` objects with `state`, `why`, `kept`, `total`, `survived`,
`evidence`, `commits`, `branch`, `branch_gone`, `elsewhere` and `anywhere`.

## Recording from a harness with no adapter

```sh
panjika record '{"session":"my-run","do":"begin","harness":"my-script","prompt":"regenerate fixtures"}'
panjika record '{"session":"my-run","do":"step","tool":"make","target":"fixtures","ok":true}'
panjika record '{"session":"my-run","do":"end","status":"done"}'
```

## Setting it up

```sh
panjika install        # hooks for Claude Code and Codex, a git post-commit hook, and this skill
panjika init           # the ledger folder alone
panjika backfill       # sessions that ran before the ledger existed, from the transcripts
```

Hooks only see what happens next, so a ledger installed today knows nothing about yesterday.
`panjika backfill` reads the harness's own transcripts, subagents included. Run it before
concluding from an empty trail that nothing ever touched the file.

`.panjika/ledger/` is meant to be committed. `.panjika/detail/` is machine-local and gitignored.
It holds whole tool arguments, whole outputs, and the line hashes that make `landed` exact.
