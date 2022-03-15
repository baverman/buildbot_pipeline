import os

from buildbot.plugins.db import get_plugins, _PluginEntry
from twisted.web import static

from .utils import adict


class PublicApp:
    def __init__(self):
        self.description = 'File storage'
        self.ui = False
        self.path = None

    def setMaster(self, master):
        self.master = master

    def setConfiguration(self, config):
        path = config['path']
        os.makedirs(path, exist_ok=True)
        self.path = path
        self.resource = static.File(path)


app = PublicApp()


def init():
    apps = get_plugins('www', None, load_now=True)
    entry = _PluginEntry(apps._group,
                         adict(name='file-store',
                               dist=adict(project_name='pipeline', version='0.1')),
                         None)
    entry._value = app
    apps._tree.add('file-store', entry)
