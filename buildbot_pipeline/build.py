from functools import lru_cache

from twisted.internet import defer

from buildbot.process.build import Build
from buildbot.process.properties import renderer
from buildbot.locks import WorkerLock

from buildbot_pipeline import utils

_current_builds = {}


class WorkdirPool:
    def __init__(self, size):
        self.size = size
        self.occupied = set()
        self.waiting = []

    def acquire(self, token):
        if self.size is None or len(self.occupied) < self.size:
            idx = 0
            while True:
                if idx not in self.occupied:
                    self.occupied.add(idx)
                    token['idx'] = idx
                    return defer.succeed(token)
                idx += 1
        else:
            d = defer.Deferred(canceller=self.waiting.remove)
            self.waiting.append(d)
            return d

    def release(self, token):
        if self.waiting:
            self.waiting.pop(0).callback(token)
        else:
            self.occupied.discard(token['idx'])


class WorkdirPoolManager:
    def __init__(self, config):
        self.config = config
        self.pools = {}

    def _key_size(self, workername, project, builder):
        if project in self.config:
            pc = self.config[project]
            key = workername, project
            size = pc.get('workers', {}).get(workername, pc.get('size'))
        else:
            key = workername, project, builder
            size = None
        return key, size

    def acquire(self, workername, project, builder):
        key, size = self._key_size(workername, project, builder)
        try:
            p = self.pools[key]
        except KeyError:
            p = self.pools[key] = WorkdirPool(size)

        return p.acquire({'key': key, 'is_shared': project in self.config})

    def release(self, token):
        p = self.pools.get(token['key'])
        p and p.release(token)


@lru_cache(None)
def get_lock(name, count):
    return WorkerLock(name, maxCount=count)


@renderer
def builder_locks(props):
    buildername = props.getProperty('virtual_builder_name')
    if not buildername:
        return []
    concurency = int(props.getProperty('pipeline_concurrency', 1))
    c_lock = get_lock('pipeline-' + buildername, concurency).access('counting')
    return [c_lock]


@renderer
def inner_builder_locks(props):
    lock_name = props.getProperty('lock')
    if lock_name:
        concurency = int(props.getProperty('lock_count', 1))
        return [get_lock('lock-' + lock_name, concurency).access('counting')]
    return []


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


def get_project_from_url(url):
    return (url.rpartition('/')[2] or 'unknown').strip('/')


class PipelineBuild(Build):
    workdir_pool_manager = None

    def setupWorkerBuildirProperty(self, workerforbuilder):
        path_module = workerforbuilder.worker.path_module

        parent_builddir = self.getProperty('pipeline_builddir')
        if parent_builddir:
            self.setProperty('builddir', parent_builddir, 'Worker')
            self.workdir = self.getProperty('pipeline_wc')
            self.setProperty('wc', self.workdir, 'Worker')
            return

        if workerforbuilder.worker.worker_basedir:
            buildername = self.getProperty('virtual_builder_name')
            project = self.getProperty('project') or get_project_from_url(self.getProperty('repository'))
            builddir = path_module.join(
                workerforbuilder.worker.worker_basedir,
                project,
                builder_name_to_path(buildername)
            )
            self.setProperty("builddir", builddir, 'Worker')
            # self.workdir = path_module.join(builddir, 'build')

    @defer.inlineCallbacks
    def acquireLocks(self, res=None):
        yield super().acquireLocks(res=res)
        if self.getProperty('pipeline_builddir'):
            return

        buildername = self.getProperty('virtual_builder_name')
        project = self.getProperty('project') or get_project_from_url(self.getProperty('repository'))
        token = yield self.workdir_pool_manager.acquire(self.workername, project, buildername)
        self._pipeline_acquired_token = token

        if token['is_shared']:
            parts = project, 'wc' + str(token['idx'])
        else:
            suffix = str(token['idx'])
            if suffix == '0':
                suffix = ''
            parts = project, builder_name_to_path(buildername), 'build' + suffix

        self.workdir = self.path_module.join(
            self.workerforbuilder.worker.worker_basedir,
            *parts
        )
        self.setProperty('wc', self.workdir, 'Worker')

    def releaseLocks(self):
        if hasattr(self, '_pipeline_acquired_token'):
            self.workdir_pool_manager.release(self._pipeline_acquired_token)
            del self._pipeline_acquired_token
        super().releaseLocks()

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
