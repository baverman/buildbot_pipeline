from buildbot.process import builder
from twisted.internet import defer

from . import utils


@utils.wrapit(builder.Builder)
def getAvailableWorkers(orig, self):
    if not self.name.startswith('~prop-builder'):
        return orig(self)

    result = []
    for name, bldr in self.botmaster.builders.items():
        if name.startswith('~prop-builder'):
            result.extend(orig(bldr))

    return result


@utils.wrapit(builder.Builder)
def maybeStartBuild(orig, self, workerforbuilder, breqs):
    if not self.running:
        return defer.succeed(False)

    if not self.name.startswith('~prop-builder'):
        return orig(self, workerforbuilder, breqs)

    return orig(workerforbuilder.builder, workerforbuilder, breqs)
