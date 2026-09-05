# Changelog

## Unreleased

Moved into its own repository. The tests came with it, out of a `tests/` pytest suite and into
cells in the notebooks that export the code, where each drives a real repository and doubles as
the documentation for what it tests.

- `requires-python` is `>=3.11`. It said `>=3.10`, which no resolver could satisfy: `gheasy` has
  required 3.11 since the version this depends on.
- A `replaced` verdict carries the commit that owns those lines now as a field. It was named in
  the prose of `why` and nowhere a reader of the record could reach it. Only that one commit:
  the commit that landed the change also touched the file after the session began, and a field
  about who owns the lines now that lists the change's own commit is worse than an empty one.
- `panjika export` writes text when stdout has no byte stream, rather than raising
  `AttributeError` into a caller that redirected it.
- A Ramabana session is stamped when its turn ran. The adapter ignored the `at` the turn record
  carries, so a session was dated when the ledger read it, which is what `log`, `--since` and a
  bare `landed` all resolve through.
- `panjika show` reported a session with no `started` as `56y ago` and its length as the age of
  the epoch. Ramabana never calls `begin`, so it has none; every other reader already fell back
  to the record's own `at`. `started` joins `prompt` as a field folding keeps the earliest value
  of, since a harness that writes one record per turn repeats it on every turn.
- A verdict says which branch. `branch` is the branch the session ran on, `branch_gone` says it
  has since been deleted, `elsewhere` names the branches whose committed copy still holds
  every line, and `anywhere` says whether panjika can point at the lines anywhere. A change made
  on a feature branch read as `replaced` from `main` with nothing to say why.
- `_replaced_by` asks git for `HEAD` rather than every ref. gheasy's `history` defaults to
  `--all`, so the commit named as owning the lines now could be one on another branch that never
  touched this one.
- `ingest` stamps the repository, root and branch onto a session record written without `begin`.
  Ramabana describes a session that way, so its sessions carried no branch at all.
- One `SKILL.md`, shipped inside the package. `panjika install` writes it into
  `.claude/skills/panjika/`, `.agents/skills/panjika/` and `.codex/skills/panjika/`, and
  `[project.entry-points.pyskills]` publishes the same text. There were three copies of it in the
  repository, kept in sync by hand.
- Every code comment is gone from the package and every docstring is one line. The explanations moved into the
  notebook prose, which is where the documentation is built from.

## 0.0.3

Codex, verified. Its lifecycle hooks use Claude Code's event vocabulary and are delivered the
same way, so `panjika install` now writes `.codex/hooks.json` instead of printing a guess.
Three differences are handled: a failed call is a `PostToolUse` whose `tool_response` reports
the error, since Codex has no separate failure event; `apply_patch` names the files it touches
inside the patch envelope rather than in an argument; and a subagent reports its parent's
`session_id` beside its own `agent_id`. The legacy `notify` route is a second adapter,
`codex-notify`: it fires once per turn and never per tool call, its keys are kebab-case, and
Codex passes it as a command-line argument with stdin closed, so it goes through `record`
rather than `hook`.

A session is headlined by the first thing a person asked it, not the last thing said to it.
`fold` takes a `first` argument for fields that keep their earliest value. Every prompt is
still kept, in order, with where it came from, and `panjika show` lists the later ones.

## 0.0.2

Backfill, and a verdict that no longer guesses.

- `panjika backfill` reads sessions that ran before the ledger existed, out of the harness's
  own transcripts. Claude Code keeps one JSONL per session and one per subagent; each subagent
  becomes its own session under its parent. An `Edit` carries the file before and after, so a
  backfilled touch holds the same line hashes a hook would have written and `landed` is exact
  for it.
- Path-only evidence is `uncertain`, not `landed`. A commit touching the file afterwards is as
  consistent with the change being reverted as with it surviving, and on the far side of a
  clone, where the committed ledger travels but the line record does not, the old answer told
  an agent to skip work it still had to do.
- `Scribe.touch` takes `before` and `after_text`, for a change git can no longer be asked about.

## 0.0.1

First release. Append-only JSONL ledger, two tiers, `trail`, `landed`, `log`, the Claude Code,
Codex and Ramabana adapters, and the git post-commit link.
