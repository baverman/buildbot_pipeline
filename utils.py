import io
import functools

from twisted.internet import defer

from buildbot.process import remotecommand
from buildbot.process.results import SUCCESS
from buildbot.worker.protocols import base


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


def wrapit(obj, attr):
    orig = getattr(obj, attr)
    def decorator(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            return fn(orig, *args, **kwargs)
        setattr(obj, attr, inner)
        return inner
    return decorator


class adict(dict):
    __getattr__ = dict.__getitem__
