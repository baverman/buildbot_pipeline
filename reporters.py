import operator
import itertools

from twisted.internet import defer
from buildbot.reporters import gerrit, utils
from buildbot.data import resultspec


class GerritStatusPush(gerrit.GerritStatusPush):
    def isBuildReported(self, build):
        return build['properties']['buildername'][0].startswith('~prop-builder')

    @defer.inlineCallbacks
    def buildsetComplete(self, key, msg):
        if not self.summaryCB:
            return

        bsid = msg['bsid']
        res = yield utils.getDetailsForBuildset(self.master, bsid, want_properties=False,
                                                want_steps=self.wantSteps, want_logs=self.wantLogs,
                                                want_logs_content=self.wantLogs)
        buildset = res['buildset']

        buildsets = yield self.master.data.get(
            ('buildsets',),
            filters=[resultspec.Filter('parent_buildid', 'eq', [buildset['parent_buildid']])])

        if not buildsets or not all(it['complete'] for it in buildsets):
            return

        bs_ids = [it['bsid'] for it in buildsets]
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
