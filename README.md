# panjika

> the register of deeds

A panjikar keeps a panji: a register of who descends from whom. A panjikar adds to it and never changes it. panjika is the same thing for agent work.

Each repository has one ledger. It is a JSONL file. It holds each session, each file that the session changed, and the place that the change went to in git. Each harness in the repository writes to the same ledger.

Your harness already logs its sessions. It does not tell you which session changed a file, or if the change is still there. panjika answers those two questions.

## The two questions

```
$ panjika trail charges.py
cf02cc5  commit  no rounding: amounts are already in cents
          Sam  2h ago
rb-0c7e  ramabana  total() should round to 2dp
          +1/-1  sonnet  main  2h ago
8131d52  commit  skip negative amounts in total()
          Sam  1d ago
cc-4f21  claude-code  total() blows up on refunds. Make it skip negative amounts.
          +1/-1  opus-5  main  1d ago
b5a1608  commit  the billing module
          Sam  3d ago
```

Three harnesses, one file, one list. Now ask what happened to one session:

```
$ panjika landed rb-0c7e
replaced  charges.py  0/1 lines  on main
    none of the 1 lines this session wrote are in the file;
    cf02cc5 'no rounding: amounts are already in cents' by Sam owns it now

1 replaced
```

The rounding change is gone. The commit message gives the reason. An agent that wants to make the same change reads this and stops.

## Install

```sh
pip install panjika
panjika install     # the hooks, the git hook, the skill, and the ledger
panjika backfill    # the sessions that ran before you installed panjika
```

`panjika install` writes three files: `.claude/settings.json`, `.codex/hooks.json` and `.git/hooks/post-commit`. Codex does not run a hook until you review it with `/hooks`.

It also writes `SKILL.md` into `.claude/skills/panjika/`, `.agents/skills/panjika/` and `.codex/skills/panjika/`. Use `--no-skill` to stop this. There is one `SKILL.md` in the package, and each copy comes from it. `[project.entry-points.pyskills]` publishes the same text, for a harness that reads skills from packages.

## What `landed` says

| state | what it means | what to do |
|---|---|---|
| `landed` | each line is in a commit | nothing |
| `partly_landed` | some lines are in a commit, and some are gone or not committed | read `why`. It counts them |
| `pending` | the lines are in the working tree, and nothing is committed | commit them, or give the reason |
| `replaced` | no line is in the file. `why` gives the commit and the author | read that commit before you do the work again |
| `gone` | the file is not in the working tree | check if a person moved it |
| `untracked` | git does not track the file | run `git add`, or the change cannot go into git |
| `uncertain` | a commit changed the file after the session, but there is no line record | read those commits, or run panjika where the session ran |
| `unknown` | there is no line record and no later commit | nothing to read |

`evidence` says how accurate the answer is.

`lines` means panjika compared the lines of the session with `git blame`. This answer stays correct if a person formats the file again, or moves the lines. It also stays correct if the lines go into git with another change.

`path` means panjika only knows that a commit changed the file. That commit can be a revert, or it can hold the change. panjika cannot know which. Thus `path` gives `uncertain` and never `landed`.

## Which branch

A verdict is about one working tree. A change made on a feature branch reads `replaced` from `main`. It reads correctly from the feature branch.

- `branch` is the branch that the session ran on.
- `branch_gone` says that a person deleted that branch.
- `elsewhere` gives each branch that has every line of the session in its copy of the file. panjika fills it in for a `replaced` or `gone` verdict.
- `anywhere` is true for `landed`, `partly_landed` and `pending`, and for any branch in `elsewhere`. It is false for `uncertain`, `unknown` and `untracked`, because panjika cannot find the lines. Read it as "panjika can point to these lines". It is not proof that the lines are gone.

The verdict reads the working tree. `elsewhere` reads what each branch has in git, and it includes the current branch. Thus a change can be in git on `main`, and a person can revert it in the working tree. Then the state is `replaced` and `elsewhere` gives `main`.

```
$ panjika landed rb-0c7e            # on main
replaced  charges.py  0/1 lines  on feature
    none of the 1 lines this session wrote are in the file; still on feature

$ git branch -D feature
$ panjika landed rb-0c7e
replaced  charges.py  0/1 lines  on feature
    none of the 1 lines this session wrote are in the file; on no branch in this
    repository; the branch feature it ran on is gone
```

panjika hashes the copy of the file on each branch and compares the recorded lines. It does not change the working tree and it does not use `git blame`.

## From Python

```python
from panjika import landed, trail, log, session

for v in landed():                  # the newest session in this repository
    print(v.state, v.path, v.why)

trail('src/charges.py')             # the sessions and the commits for one file
log(limit=10, harness='codex')      # what codex did here
session('latest').files             # the files that the last session changed
```

`landed()` gives `Verdict` objects. Each one has `state`, `why`, `kept`, `total`, `survived`, `evidence`, `commits`, `branch`, `branch_gone`, `elsewhere` and `anywhere`. Each command has a `--json` option that gives the same answers as records.

## How it is stored

panjika reads and writes JSONL with `orjson`, in `.panjika/` at the repository root. There are two tiers:

```
.panjika/
  ledger/2026-09.jsonl    committed. sessions, steps, touches, commits
  detail/2026-09.jsonl    gitignored. full tool arguments, full outputs, line hashes
  .gitattributes          ledger/*.jsonl merge=union
  .gitignore              detail/
```

The `ledger` tier is small and it holds no source code. You commit it, so the trail goes with the repository. Three things make this work.

- **One record is one `write`** to a file that is open with `O_APPEND`. Thus two harnesses cannot mix their records in one line.
- **`merge=union`.** Two branches can both add records to the same file. The merge keeps the records from both branches. Each record has an `id`, and a reader removes a duplicate. `00_core.ipynb` merges two real branches and tests this.
- **panjika never changes a record.** A session is not one record. It is each record with the same session id, in time order. Thus a hook can add the start of a session, then a dozen tool calls, then the end, from three processes, with no lock.

The `detail` tier stays on your machine. It holds the hashes of the lines that each change added, and `landed` needs them. Without them, the answers use path evidence and say so.

## Sessions from before the ledger

A hook only sees the next event. On the day you install panjika, the ledger is empty. Your harness has already written its transcripts, and `panjika backfill` reads them:

```sh
panjika backfill                    # this project
panjika backfill --all              # each project on this machine
panjika backfill path/to/one.jsonl  # one transcript
```

Claude Code writes one JSONL for each session under `~/.claude/projects/<slug>/`, and one file for each subagent next to it. Each subagent becomes its own session under its parent. It keeps the description that started it.

An `Edit` gives the file before and after. Thus a backfilled touch has the same line hashes as a hook, and `landed` is accurate for it. A `Bash` command gives neither. panjika reads its write targets from the command line, so the touch has a path and no lines. panjika knows the file, and it does not know the content.

Three things in these files are easy to read wrong. panjika handles each one.

- Claude Code writes one API response as several records, and it repeats the same `usage` in each. If you add them, the total is about two times too large.
- The last line of a live transcript is often incomplete.
- A tool call before the first prompt has no prompt. If you file it under a later prompt, you name a request that did not cause it.

## Harnesses

| harness | how | verified |
|---|---|---|
| Claude Code | `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `PostToolUseFailure`, `SessionEnd` hooks | yes, against the documented payloads |
| Ramabana | give the turn record that `Agent._remember` makes | yes |
| git | a `post-commit` hook links each commit to the sessions that changed its files | yes |
| Codex | `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `SubagentStart`, `SubagentStop`, `SessionEnd` hooks | yes, against the documented payloads |
| any other | `panjika record '{"session":"...","do":"step","tool":"make"}'` | yes |

### Ramabana

Ramabana makes one record for a full turn before it writes to its own log. The record has the prompt, the reply, the model and the usage. It also has each tool call, with its arguments and its result. The adapter takes that record, so you need three lines at the end of `Agent._remember`:

```python
from panjika.harness import ingest
try: ingest({'session': self.session_id, 'cwd': str(self.host.roots[0]), **turn}, 'ramabana')
except Exception: pass      # a ledger must never stop a turn
```

### Codex

Codex uses the event names of Claude Code and the same delivery. Three things are different, and panjika handles each one.

- Codex has no failure event. panjika reads the error from `tool_response`.
- The editor is `apply_patch`. It gives the file names inside the patch.
- A subagent sends the `session_id` of its parent and its own `agent_id`.

`panjika install` writes `<repo>/.codex/hooks.json`. Codex does not run a hook until you review it with `/hooks`.

An old Codex has no lifecycle hooks. It has only `notify`, which runs one time for each turn and never for a tool call. Its keys use kebab-case. Codex sends the payload as an argument and closes stdin. Thus you use `record`, not `hook`:

```toml
# ~/.codex/config.toml
notify = ["panjika", "record", "--adapter", "codex-notify"]
```

This route records turns and no tool calls, so `landed` has nothing to compare. Use hooks if your Codex has them.

### Any other harness

Write a function that changes the payload into a list of calls, and add a line to `ADAPTERS`. An adapter writes nothing to the disk, so you can test it without a disk.

## Develop

nbdev. The notebooks in `nbs/` are the source. panjika generates `panjika/*.py`.

```sh
uv sync --group dev
uv run nbdev-export      # notebooks -> panjika/*.py
uv run nbdev-test        # run each notebook. This is the whole test suite
uv run nbdev-clean       # before you commit
```

The tests are cells in the notebooks, and they are also the documentation. Each one uses a real repository. `03_git.ipynb` takes one file through each verdict state and each branch case. `00_core.ipynb` holds the record, the writer and the reader, and merges two branches. `06_backfill.ipynb` imports a transcript and asks `landed` about it.

## License

Apache-2.0
