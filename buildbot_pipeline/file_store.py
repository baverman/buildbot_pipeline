import os

import buildbot.data.properties as data_properties
from twisted.web import static


class FileStore:
    def __init__(self):
        self.description = 'File storage'
        self.ui = False
        self.path = None

    def setMaster(self, master):
        self.master = master
        self.master.data.updates.setBuildProperties = data_properties.Properties(master).setBuildProperties

    def setConfiguration(self, config):
        path = config['path']
        os.makedirs(path, exist_ok=True)
        self.path = path
        self.resource = static.File(path)
        self.resource.contentTypes['.log'] = 'text/plain'


ep = FileStore()
