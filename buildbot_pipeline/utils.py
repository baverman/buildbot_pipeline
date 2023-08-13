import io
import functools

from twisted.internet import defer

from buildbot.process import remotecommand
from buildbot.process.results import SUCCESS
from buildbot.worker.protocols import base
from buildbot.db.base import CachedMethod


ntype = type('')
btype = type(b'')
utype = type(u'')


def bstr(data, encoding='latin1'):
    if type(data) is utype:
        data = data.encode(encoding)
    return data


def ustr(data, encoding='latin1'):
    if type(data) is btype:
        data = data.decode(encoding)
    return data


def nstr(data, encoding='utf-8'):
    if type(data) is ntype:
        return data
    elif type(data) is btype:
        return data.decode(encoding)
    else:
        return data.encode(encoding)


def ensure_list(data):
    if type(data) is not list:
        return [data]
    return data


@defer.inlineCallbacks
def shell(step, command, collectStdout=False):
    workdir = step.workdir
    if not workdir:
        if callable(step.build.workdir):
            workdir = step.build.workdir(step.build.sources)
        else:
            workdir = step.build.workdir

    args = {
        'workdir': workdir,
        'command': command,
        'logEnviron': False,
        'want_stdout': collectStdout,
        'want_stderr': False,
    }
    cmd = remotecommand.RemoteCommand('shell', args, stdioLogName=None, collectStdout=collectStdout)
    cmd.worker = step.worker
    yield cmd.run(None, step.remote, step.build.builder.name)
    return cmd


def get_workdir(step):
    workdir = step.workdir
    if not workdir:
        if callable(step.build.workdir):
            workdir = step.build.workdir(step.build.sources)
        else:
            workdir = step.build.workdir
    return workdir


def silent_remote_command(step, command, collectStdout=False, **kwargs):
    kwargs.setdefault('logEnviron', False)
    cmd = remotecommand.RemoteCommand(command, kwargs, stdioLogName=None, collectStdout=collectStdout)
    cmd.worker = step.worker
    return cmd.run(None, step.remote, step.build.builder.name)


def hide_if_success(result, step):
    return result == SUCCESS


class BufWriter(base.FileWriterImpl):
    def __init__(self):
        self.buf = io.BytesIO()

    def remote_write(self, data):
        self.buf.write(data)

    def remote_close(self):
        pass


def wrapit(obj, attr=None):
    def decorator(fn):
        lattr =  attr or fn.__name__

        orig = getattr(obj, lattr)
        if isinstance(orig, CachedMethod):
            orig = orig.method

        @functools.wraps(fn)
        def inner(*args, **kwargs):
            return fn(orig, *args, **kwargs)

        setattr(obj, lattr, inner)
        return inner
    return decorator


def add_method(obj, attr=None):
    def decorator(fn):
        lattr =  attr or fn.__name__
        setattr(obj, lattr, fn)
        return fn
    return decorator


class adict(dict):
    __getattr__ = dict.__getitem__


def get_parent_buildid(master, bsid):
    def thd(conn):
        bs = master.db.model.buildsets
        q = (bs.select().with_only_columns(bs.c.parent_buildid)
             .where(bs.c.id == bsid))
        rv = conn.execute(q).fetchone()
        return rv and rv.parent_buildid
    return master.db.pool.do(thd)


def to_bool(value):
   return value and value not in ('0', 'false', 'no', 'False')
