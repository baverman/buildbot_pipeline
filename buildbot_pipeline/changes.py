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
        kwargs['handled_events'] = ['patchset-created', 'comment-added', 'change-merged', 'ref-updated']
        return super().reconfigService(**kwargs)

    def eventReceived_ref_updated(self, properties, event):
        project = event.get('refUpdate').get('project')
        if self.projects and project not in self.projects:
            return None

        tag_name = event.get('refUpdate').get('refName')
        if tag_name.startswith('refs/tags/'):
            tag_name = tag_name[len('refs/tags/'):]
        else:
            tag_name = None

        rev = event.get('refUpdate').get('newRev')
        if tag_name and rev and set(rev) != {'0'}:
            properties['event.change.status'] = 'TAGGED'
            properties['event.change.tag'] = tag_name
            return super().eventReceived_ref_updated(properties, event)
        return None

    def addChangeFromEvent(self, properties, event):
        project = event.get('project')
        if self.projects and project not in self.projects:
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
