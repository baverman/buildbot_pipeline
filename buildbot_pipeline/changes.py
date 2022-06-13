import re
import shlex
from twisted.internet import defer
from buildbot.changes import gerritchangesource

value_regex = re.compile(r'^(.+)=(.+)$')


def comment_trigger(properties, event):
    props = []
    for line in event.get('comment').splitlines():
        line = line.strip()
        if line.startswith('bb start'):
            parts = line.split(None, 2)
            if len(parts) < 3:
                props.append({})
            else:
                parts = shlex.split(parts[2])
                p = {}
                for it in parts:
                    m = value_regex.match(it)
                    if m:
                        p[m.group(1)] = m.group(2)
                props.append(p)

    if props:
        builder_props = {}
        for p in props:
            p.pop('workername', None)
            builder_props.setdefault(p.pop('builder', '_all'), {}).update(p)

        builders = set(builder_props)
        builders.discard('_all')
        properties['pipeline_build_props'] = {
            'builders': list(builders),
            'common_props': builder_props.pop('_all', {}),
            'builder_props': builder_props,
        }
        return True


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

        start = []
        skip = []

        if event.get('type') == 'comment-added':
            skip.append('comment')
            if comment_trigger(properties, event):
                start.append('comment')

        if self.ignore_wip and event.get('change', {}).get('wip'):
            skip.append('wip')

        if start or not skip:
            return super().addChangeFromEvent(properties, event)

        return defer.succeed(None)
