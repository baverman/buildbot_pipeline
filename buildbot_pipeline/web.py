import os.path
from twisted.web import static, resource

from buildbot.www import service
from buildbot_pipeline import utils


class UI:
    def __init__(self):
        self.description = 'Buildbot pipeline UI'
        self.ui = False
        self.static_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '../web/dist'))
        self.resource = static.File(self.static_dir)

    def setMaster(self, master):
        self.master = master
        # import traceback
        # traceback.print_stack()

    def setConfiguration(self, config):
        self.config = config


ep = UI()


@utils.wrapit(service.WWWService)
def refresh_base_plugin_name(orig, self, new_config):
    self.base_plugin_name = 'bb-pipeline'


# @utils.wrapit(resource.Resource)
# def putChild(orig, self, path, child):
#     if path == b'':
#         path = b'old'
#     elif path == b'bb-pipeline':
#         path = b''
#     return orig(self, path, child)


@utils.wrapit(service.WWWService)
def setupSite(orig, self, *args, **kwargs):
    orig(self, *args, **kwargs)
    print(self.root)
    # self.root.putChild(b'', self.root.children[b'bb-pipeline'])
    # print(self.root.children)
