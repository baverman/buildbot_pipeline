import os

import buildbot.data.properties as data_properties
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
        self.master.data.updates.setBuildProperties = data_properties.Properties(master).setBuildProperties

        # from twisted.internet import defer
        #
        # @defer.inlineCallbacks
        # def async_do():
        #     data = yield self.master.data.get(('builders',))
        #     for it in sorted(data, key=lambda r: r['name']):
        #         parts = it['name'].split('/')
        #         if len(parts) > 2:
        #             print(it['name'])
        #             yield master.data.updates.updateBuilderInfo(it['builderid'], None, ['_virtual_', 'hidden'])
        #
        # async_do()

    def setConfiguration(self, config):
        path = config['path']
        os.makedirs(path, exist_ok=True)
        self.path = path
        self.resource = static.File(path)
        self.resource.contentTypes['.log'] = 'text/plain'


app = PublicApp()


def init():
    apps = get_plugins('www', None, load_now=True)
    entry = _PluginEntry(apps._group,
                         adict(name='file-store',
                               dist=adict(project_name='pipeline', version='0.1')),
                         None)
    entry._value = app
    apps._tree.add('file-store', entry)
