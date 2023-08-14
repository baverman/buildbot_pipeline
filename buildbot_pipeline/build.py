from functools import lru_cache

from twisted.internet import defer

from buildbot.process.build import Build
from buildbot.process.properties import renderer
from buildbot.locks import WorkerLock

from buildbot_pipeline import utils

_current_builds = {}


@lru_cache(None)
def get_lock(name, count):
    return WorkerLock(name, maxCount=count)


@renderer
def builder_locks(props):
    buildername = props.getProperty('virtual_builder_name')
    if not buildername:
        return []
    concurency = int(props.getProperty('pipeline_concurrency', 1))
    return [get_lock('pipeline-' + buildername, concurency).access('counting')]


@renderer
def inner_builder_locks(props):
    lock_name = props.getProperty('lock')
    if lock_name:
        concurency = int(props.getProperty('lock_count', 1))
        return [get_lock('lock-' + lock_name, concurency).access('counting')]
    return []


def select_workdir_index(build, key):
    i = 0
    while True:
        k = key + str(i)
        if k in _current_builds:
            if _current_builds[k]['build'].finished:
                _current_builds[k]['build'] = build
                return i
        else:
            _current_builds[k] = {'build': build}
            return i
        i += 1


def builder_name_to_path(name):
    return name.strip('.').replace('/', '-').replace('\\', '-').replace(':', '-')


@defer.inlineCallbacks
def get_bpath(master, buildid):
    data = yield master.db.build_data.getAllBuildDataNoValues(buildid)
    bpath = next((it['name'] for it in data or [] if it['name'].startswith('bpath:')), None)
    if bpath:
        return list(map(int, list(filter(None, bpath.split(':')))[1:]))
    return []


def set_bpath(master, buildid, bpath):
    name = 'bpath:' + ':'.join(map(str, bpath)) + ':'
    return master.data.updates.setBuildData(buildid, name, b'', 'Build')


def get_child_builds(master, bpath, builderid=None, success=None):
    def thd(conn):
        b = master.db.model.builds
        bd = master.db.model.build_data
        name = 'bpath:' + ':'.join(map(str, bpath))
        cond = []

        if builderid is not None:
            cond.append(b.c.builderid == builderid)

        if success:
            cond.append(b.c.results == 0)

        q = (b.select()
             .select_from(bd.join(b))
             .where(bd.c.name.like(name+'%'), *cond)
             .order_by(b.c.number.desc()))

        if success:
            q = q.limit(1)

        return conn.execute(q).fetchall()
    return master.db.pool.do(thd)


class PipelineBuild(Build):
    def setupWorkerBuildirProperty(self, workerforbuilder):
        path_module = workerforbuilder.worker.path_module

        parent_builddir = self.getProperty('pipeline_builddir')
        if parent_builddir:
            self.setProperty('builddir', parent_builddir, 'Worker')
            self.workdir = path_module.join(parent_builddir, 'build')
            return

        if workerforbuilder.worker.worker_basedir:
            buildername = self.getProperty('virtual_builder_name')
            key = f'{buildername}-{workerforbuilder.worker.name}'
            idx = select_workdir_index(self, key)
            if idx:
                suffix = f'@{idx}'
            else:
                suffix = ''
            builddir = path_module.join(
                workerforbuilder.worker.worker_basedir,
                builder_name_to_path(buildername) + suffix,
            )
            self.setProperty("builddir", builddir, 'Worker')
            self.workdir = path_module.join(builddir, 'build')

    @defer.inlineCallbacks
    def startBuild(self, *args, **kwargs):
        yield super().startBuild(*args, **kwargs)
        self.buildbot_pipeline_bpath = None
        parent_buildid = yield utils.get_parent_buildid(self.master, self.requests[0].bsid)
        if parent_buildid:
            bpath = yield get_bpath(self.master, parent_buildid)
            bpath.append(parent_buildid)
            self.buildbot_pipeline_bpath = bpath
            yield set_bpath(self.master, self.buildid, bpath)

    @defer.inlineCallbacks
    def get_last_successful_build(self):
        if not self.buildbot_pipeline_bpath:
            return None

        builderid = yield self.getBuilderId()
        rv = yield get_child_builds(self.master, self.buildbot_pipeline_bpath[:1], builderid=builderid, success=True)
        return rv and rv[0]
