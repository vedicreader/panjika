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
landed in git. Every harness working in this repository writes to the same one.

## Before you edit a file

```sh
panjika trail path/to/file.py
```

Every agent session and every commit that has ever touched that file, newest first, on one
timeline. Read it when a file looks like somebody has been here before, when a change you are
about to make may undo one, or when you want to know which model last had an opinion about it.

## After you have changed something

```sh
panjika landed            # the newest session in this ledger
panjika landed --json     # the same, as records
```

One verdict per file. The state is the thing to read:

| state | what it means | what to do |
|---|---|---|
| `landed` | every line is in a commit | nothing; it is done |
| `partly_landed` | some lines are committed, some are gone or still uncommitted | read `why`; the missing lines are named |
| `pending` | the lines are in the working tree and nothing is committed | commit, or say why you are not |
| `replaced` | none of the lines survive; `why` names the commit and author that own them now | do not just rewrite it. Find out why it was replaced first |
| `gone` | the file is not in the working tree | the change cannot land; check whether the file moved |
| `untracked` | git is not tracking the file | `git add` it, or accept that it will never land |
| `uncertain` | commits touched the file since, but no line record is here to say whether this change is in them | read those commits, or run where the session ran |
| `unknown` | nothing to go on | the machine-local half of the ledger is missing, usually because this ledger came from somebody else |

`evidence` says how sure the verdict is. `lines` matched the exact lines you wrote against
`git blame`, which survives the file being reformatted, moved, or committed together with
somebody else's change. `path` only knows that some commit touched the file afterwards, which
is as consistent with a revert as with survival, so on `path` alone the answer is `uncertain`
and never `landed`.

## Planning against it

`replaced` is the one worth stopping for. If your last change was replaced, the next thing to do
is almost never to make the same change again. Read the commit named in `why`, and either work
with it or say plainly that the two changes disagree.

`pending` across many files at the end of a turn usually means the work is done and uncommitted,
not that it failed.

## From Python

```python
from panjika import landed, trail, log, session

for v in landed():                 # the newest session in this repository
    print(v.state, v.path, v.why)

trail('src/app.py')                # sessions and commits on one timeline
log(limit=10, harness='codex')     # what codex has been doing here
session('latest').files            # what the last session changed
```

`landed()` returns `Verdict` objects with `state`, `why`, `kept`, `total`, `survived`,
`evidence` and `commits`.

## Recording from a harness with no adapter

```sh
panjika record '{"session":"my-run","do":"begin","harness":"my-script","prompt":"regenerate fixtures"}'
panjika record '{"session":"my-run","do":"step","tool":"make","target":"fixtures","ok":true}'
panjika record '{"session":"my-run","do":"end","status":"done"}'
```

## Setting it up

```sh
panjika install        # Claude Code and Codex hooks, and a git post-commit hook
panjika init           # the ledger folder alone
panjika backfill       # sessions that ran before the ledger existed, from the transcripts
```

Hooks only see what happens next, so a ledger installed today knows nothing about yesterday.
`panjika backfill` reads the harness's own transcripts, subagents included. If a trail looks
empty, run it before concluding that nothing ever touched the file.

`.panjika/ledger/` is meant to be committed. `.panjika/detail/` is machine-local and gitignored:
it holds whole tool arguments, whole outputs, and the line hashes that make `landed` exact.
