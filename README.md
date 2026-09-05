# panjika

> the register of deeds

A panji is the genealogical register a panjikar keeps: who descends from whom, appended and
never rewritten. This is the same thing for agent work. Every session, every file it touched,
and where that change ended up in git, in one append-only JSONL ledger that every harness in a
repository writes to.

Agent sessions are logged today. What is missing is the join: **which session changed this
file, in what context, and did the change survive.** That is what this answers.

## The two questions

```
$ panjika trail charges.py
cf02cc5  commit  no rounding: amounts are already in cents
          Sam  2h ago
rb-0c7e  ramabana  total() should round to 2dp
          +1/-1  sonnet  2h ago
8131d52  commit  skip negative amounts in total()
          Sam  1d ago
cc-4f21  claude-code  total() blows up on refunds. Make it skip negative amounts.
          +1/-1  opus-5  1d ago
b5a1608  commit  the billing module
          Sam  3d ago
```

Three harnesses, one file, one timeline. Then the question an agent should ask before it plans
anything:

```
$ panjika landed rb-0c7e
replaced  charges.py  0/1 lines
    none of the 1 lines this session wrote are in the file;
    cf02cc5 'no rounding: amounts are already in cents' by Sam owns it now

1 replaced
```

The rounding change did not survive, and the commit message says why. An agent about to make
that change again now knows not to.

## Install

```sh
pip install panjika
panjika install     # Claude Code and Codex hooks, a git post-commit hook, the skill, the ledger
panjika backfill    # and everything that already happened, out of the transcripts
```

`panjika install` writes `.claude/settings.json`, `.codex/hooks.json` and
`.git/hooks/post-commit`. Codex will not run a hook until you have reviewed it with `/hooks`.

It also writes `SKILL.md` into `.claude/skills/panjika/`, `.agents/skills/panjika/` and
`.codex/skills/panjika/`. One file ships inside the package and every copy comes from it.
`[project.entry-points.pyskills]` publishes the same text to a harness that reads skills from
installed packages rather than from disk.

## What `landed` says

| state | what it means | what to do about it |
|---|---|---|
| `landed` | every line is in a commit | nothing; it is done |
| `partly_landed` | some lines are committed, some are gone or still uncommitted | read `why`; it counts them |
| `pending` | the lines are in the working tree, nothing is committed | commit, or say why not |
| `replaced` | none of the lines survive; `why` names the commit and the author | read that commit before redoing the work |
| `gone` | the file is not in the working tree | check whether it moved |
| `untracked` | git is not tracking the file | `git add` it, or it will never land |
| `uncertain` | commits touched the file since, but no line record is here to say whether this change is in them | read those commits, or run where the session ran |
| `unknown` | nothing to go on | no line record and no commit since |

## Which branch

A verdict is about one working tree. A change made on a feature branch reads as `replaced` from
`main`, and reads correctly from the branch itself.

`branch` is the branch the session ran on. `branch_gone` says that branch is now deleted.
`elsewhere` names the branches that still hold every line, filled in when the state is
`replaced` or `gone`. `anywhere` is false only when the lines are in no branch at all.

```
$ panjika landed rb-0c7e            # standing on main
replaced  charges.py  0/1 lines  on feature
    none of the 1 lines this session wrote are in the file; still on feature

$ git branch -D feature
$ panjika landed rb-0c7e
replaced  charges.py  0/1 lines  on feature
    none of the 1 lines this session wrote are in the file; and on no other branch either;
    the branch feature it ran on is gone
```

`elsewhere` is answered by hashing each branch's copy of the file and matching the recorded
lines, so it needs no checkout and no blame.

`evidence` says how sure the verdict is. `lines` matched the exact lines the session wrote
against `git blame`, which survives the file being reformatted, moved around, or committed
together with somebody else's change. `path` only knows that some commit touched the file
afterwards, which is as consistent with the change being reverted as with it surviving, so on
`path` evidence alone the answer is `uncertain` and never `landed`.

## From Python

```python
from panjika import landed, trail, log, session

for v in landed():                  # the newest session in this repository
    print(v.state, v.path, v.why)

trail('src/charges.py')             # sessions and commits on one timeline
log(limit=10, harness='codex')      # what codex has been doing here
session('latest').files             # what the last session changed
```

`landed()` returns `Verdict` objects carrying `state`, `why`, `kept`, `total`, `survived`,
`evidence`, `commits`, `branch`, `branch_gone`, `elsewhere` and `anywhere`. Every command takes
`--json` for the same answers as records.

## How it is stored

JSONL, read and written with `orjson`, in `.panjika/` at the repository root. Two tiers:

```
.panjika/
  ledger/2026-09.jsonl    committed. sessions, steps, touches, commits
  detail/2026-09.jsonl    gitignored. whole tool arguments, whole outputs, changed-line hashes
  .gitattributes          ledger/*.jsonl merge=union
  .gitignore              detail/
```

The ledger tier is small, carries no source, and is meant to be committed, so a trail travels
with the repository. Three things make that work:

- **One record is one `write` syscall** to a file opened `O_APPEND`, so two harnesses writing at
  the same moment never interleave inside a line.
- **`merge=union`**, so two branches that both appended merge to the union of their lines rather
  than to a conflict. Every record carries an `id` and readers deduplicate, which is what makes
  taking both sides safe. `00_core.ipynb` merges two real branches and checks it.
- **Nothing is ever rewritten.** A session is not one record; it is every record that named it,
  folded in time order. That is why a hook can append the start of a session, a dozen tool calls
  later, and the end, from three processes, with no lock between them.

The detail tier is machine-local. It holds the hashes of the lines each change added, which is
what makes `landed` exact. Without it the answers degrade to path-level evidence and say so.

## Sessions from before there was a ledger

Hooks only see what happens next, so on the day it is installed a ledger knows nothing. The
harness has already written the transcripts, and `panjika backfill` reads them:

```sh
panjika backfill                    # this project
panjika backfill --all              # every project on this machine
panjika backfill path/to/one.jsonl  # one transcript
```

Claude Code keeps one JSONL per session under `~/.claude/projects/<slug>/` and one file per
subagent beside it. Each subagent becomes its own session under its parent, keeping the
description it was spawned with.

An `Edit` reports the file before and after, so a backfilled touch carries the same line
hashes a hook would have written and `landed` is exact for it. A `Bash` command reports
neither, so its write targets are read off the command line and the touch carries a path and
no lines: precise about which file, honest that the body is not known.

Three things a naive reader of those files gets wrong, each found in a real transcript. Claude
Code splits one API response across several records and repeats the identical `usage` in each,
so summing per record roughly doubles the count. A live transcript's last line is regularly
half written. And a tool call before the first prompt belongs to no prompt in the file, so
filing it under a later one blames a request that did not cause it.

## Harnesses

| harness | how | verified |
|---|---|---|
| Claude Code | `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `PostToolUseFailure`, `SessionEnd` hooks | yes, against the documented payloads |
| Ramabana | hand over the turn record `Agent._remember` already builds | yes |
| git | a `post-commit` hook links each commit to the sessions that touched its files | yes |
| Codex | `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `SubagentStart`, `SubagentStop`, `SessionEnd` hooks | yes, against the documented payloads |
| anything else | `panjika record '{"session":"...","do":"step","tool":"make"}'` | yes |

Ramabana assembles the whole of a turn in one record before writing it to its own log: the
prompt, the reply, the model, the usage, and every tool call with its arguments and its result.
The adapter takes that record whole, so wiring it up is three lines at the end of
`Agent._remember`:

```python
from panjika.harness import ingest
try: ingest({'session': self.session_id, 'cwd': str(self.host.roots[0]), **turn}, 'ramabana')
except Exception: pass      # a ledger that fails must never take a turn down with it
```

Codex uses Claude Code's event vocabulary, delivered the same way, so its adapter reads much
the same. Three things differ and each is handled: there is no separate failure event, so an
error is read out of `tool_response`; the editor is `apply_patch`, which names the files it
touches inside the patch envelope rather than in an argument; and a subagent reports its
parent's `session_id` beside its own `agent_id`. `panjika install` writes
`<repo>/.codex/hooks.json`, and Codex will not run a hook until you have reviewed it with
`/hooks`.

A Codex old enough to lack lifecycle hooks has only `notify`, which fires once per completed
turn and never per tool call. Its keys are kebab-case, unlike every other Codex surface, and
Codex passes the payload as a command-line argument with stdin closed, so it is reached
through `record` rather than `hook`:

```toml
# ~/.codex/config.toml
notify = ["panjika", "record", "--adapter", "codex-notify"]
```

That route records turns and no tool calls, so `landed` has nothing to work from. Prefer
hooks wherever they exist.

Adding a harness is a function that turns its payload into a list of calls, and a line in
`ADAPTERS`. Adapters write nothing, so testing one needs no disk.

## Develop

nbdev. The notebooks under `nbs/` are the source and `panjika/*.py` is generated.

```sh
uv sync --group dev
uv run nbdev-export      # notebooks -> panjika/*.py
uv run nbdev-test        # execute every notebook, which is the whole suite
uv run nbdev-clean       # before committing
```

The tests are cells in the notebooks, and they are also the documentation for what they
test. Each drives a real repository rather than a stub. `03_git.ipynb` walks one file
through `pending`, `landed`, `partly_landed`, `replaced`, `untracked` and `gone`, and then
deletes the machine-local tier to ask the same question from the far side of a clone.
`00_core.ipynb` merges two branches that both appended. `06_backfill.ipynb` imports a
transcript and asks `landed` about the session in it. The shell-command table in
`06_backfill.ipynb` and the payload shapes in `04_harness.ipynb` are worth reading as well as
running.

## License

Apache-2.0
