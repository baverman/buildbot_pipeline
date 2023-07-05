import operator
import itertools
import jinja2
from functools import lru_cache

from twisted.internet import defer
from buildbot.reporters import gerrit, utils, mail
from buildbot.data import resultspec
from buildbot.process import results
from buildbot.reporters.generators import build as generators_build
from buildbot.reporters.base import ReporterBase


class GerritStatusPush(gerrit.GerritStatusPush):
    def isBuildReported(self, build):
        return build['properties']['buildername'][0].startswith('~prop-builder')

    def send_start_notification(self, build):
        if build['results'] not in (results.SUCCESS, results.WARNINGS):
            return

        url = utils.getURLForBuild(self.master, build['builder']['builderid'], build['number'])

        result = {
            'message': f'Build started {url}',
            'labels': {'Verified': 0},
        }

        self.sendCodeReviews(build, result)

    @defer.inlineCallbacks
    def buildsetComplete(self, key, msg):
        if not self.summaryCB:
            return

        bsid = msg['bsid']
        res = yield utils.getDetailsForBuildset(self.master, bsid, want_properties=True)
        buildset = res['buildset']
        if res['builds'] and res['builds'][0]['builder']['name'] == '~distributor':
            self.send_start_notification(res['builds'][0])

        buildsets = yield self.master.data.get(
            ('buildsets',),
            filters=[resultspec.Filter('parent_buildid', 'eq', [buildset['parent_buildid']])])

        if not buildsets or not all(it['complete'] for it in buildsets):
            return

        bs_ids = [it['bsid'] for it in buildsets][:50]
        breqs = yield self.master.data.get(
            ('buildrequests',),
            filters=[resultspec.Filter('buildsetid', 'in', bs_ids)])

        breqs.sort(key=lambda it: (it['builderid'], it['buildrequestid']))

        final_br_ids = []
        for _, g in itertools.groupby(breqs, operator.itemgetter('builderid')):
            br = list(g)[-1]
            final_br_ids.append(br['buildrequestid'])

        builds = yield self.master.data.get(
            ('builds',),
            filters=[resultspec.Filter('buildrequestid', 'in', final_br_ids)])

        yield utils.getDetailsForBuilds(self.master, buildset, builds, want_properties=True)
        yield self.sendBuildSetSummary(buildset, builds)


class BuildStatusGenerator(generators_build.BuildStatusGenerator):
    def is_message_needed_by_props(self, build):
        result =  super().is_message_needed_by_props(build)
        if result:
            return True

        build_tags = build['properties'].get('build_tags', [None])[0] or []
        if self.tags is not None and not self._matches_any_tag(build_tags):
            return False

        return True


class LogReporter(ReporterBase):
    def sendMessage(self, reports):
        fmt = report_formatter('notify_log_template', '{{ body | pprint }}')
        for it in reports:
            print('@@ REPORT\n', fmt(it), flush=True)


class MailNotifier(mail.MailNotifier):
    @defer.inlineCallbacks
    def getResponsibleUsersForBuild(self, master, buildid):
        props = yield master.data.get(("builds", buildid, 'properties'))
        result = list(filter(None, (it.strip() for it in props.get('email_notification_address', [''])[0].split(','))))
        if 'owner' in result:
            result.remove('owner')
            extra = yield super().getResponsibleUsersForBuild(master, buildid)
            result.extend(extra)
        return result


@lru_cache(100)
def jinja_template(template):
    return jinja2.Template(template)


def report_formatter(template_property, default_template):
    def formatter(report: dict):
        props = {k: v[0] for k, v in report['body']['properties'].items()}
        template = props.get(template_property) or default_template
        report['body']['properties'] = props
        return jinja_template(template.strip()).render(props=props, **report)

    return formatter
