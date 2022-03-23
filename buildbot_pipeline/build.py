from functools import lru_cache

from buildbot.process.build import Build
from buildbot.process.properties import renderer
from buildbot.locks import WorkerLock

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
