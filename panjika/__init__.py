"""The names an agent reaches for. Everything else is one module down.

`landed` and `trail` are the two that matter: what became of what I wrote, and who has touched
this file before me. Both work with no arguments beyond a path, because the ledger for the
repository you are standing in is found by walking up from the working directory.
"""

__version__ = "0.0.3"

from panjika.core import Home, Ledger, Scribe, find_home
from panjika.git import Verdict, blend as trail, landed, link_commit, report


def log(limit=20, harness='', since='', path='', repo='', home=None, start='.'):
    "Sessions, newest first. The same rows as `panjika log`."
    return Ledger(home, start).sessions(limit=limit, harness=harness, since=since,
                                        path=path, repo=repo)


def session(sid='latest', home=None, start='.'):
    "One session with all its records. `latest` is the newest session."
    led = Ledger(home, start)
    if sid in ('latest', '', None):
        rows = led.sessions(limit=1)
        if not rows: return None
        sid = rows[0].session
    return led.session(sid)


def record(session='', home=None, start='.', **fields):
    "Record one act for a session, through the generic adapter."
    from panjika.harness import ingest
    return ingest({'session': session, 'cwd': str(start), **fields}, 'generic', home, start)


__all__ = ['Home', 'Ledger', 'Scribe', 'Verdict', 'find_home', 'landed', 'link_commit', 'log',
           'record', 'report', 'session', 'trail']
