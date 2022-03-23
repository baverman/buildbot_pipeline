from twisted.internet import defer
from buildbot.changes import gerritchangesource


class GerritChangeSource(gerritchangesource.GerritChangeSource):
    def checkConfig(self, projects=None, ignore_wip=True, **kwargs):
        super().checkConfig(**kwargs)

    def reconfigService(self, projects=None, ignore_wip=True, **kwargs):
        self.projects = projects
        self.ignore_wip = ignore_wip
        return super().reconfigService(**kwargs)

    def addChangeFromEvent(self, properties, event):
        if self.projects and event.get('project') not in self.projects:
            return defer.succeed(None)

        if self.ignore_wip and event.get('change', {}).get('wip'):
            return defer.succeed(None)

        return super().addChangeFromEvent(properties, event)
