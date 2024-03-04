import os
import itertools
from buildbot.plugins import util as _

from buildbot.process import properties
from buildbot.process.factory import BuildFactory
from buildbot.config.builder import BuilderConfig
from buildbot.schedulers.triggerable import Triggerable
from buildbot.worker.local import LocalWorker

from . import steps, build, file_store as _unused_important
from . import builder as _unused_important, monkey as _unused_important

build_counters = {}


class BuilderCounter:
    def __init__(self, prefix, amount):
        self.prefix = prefix
        self.amount = amount
        self._counters = {}

    def next_builder(self, key):
        try:
            c = self._counters[key]
        except KeyError:
            c = self._counters[key] = itertools.cycle(range(self.amount))
        idx = next(c)
        return f'{self.prefix}{idx}'


@properties.renderer
def builder_names(props):
    prefix = props.getProperty('pipeline_builder_prefix')
    worker = props.getProperty('workername', '-some-')
    name = build_counters[prefix].next_builder(worker)
    return [name]


def init_pipeline(master_config, builders=10, inner_builders=30,
                  stepsdir=steps.DEFAULT_STEPSDIR, vcs_opts=None, workdir_pool_config=None):
    build_counters['~prop-builder'] = BuilderCounter('~prop-builder', builders)
    build_counters['~prop-inner-builder'] = BuilderCounter('~prop-inner-builder', inner_builders)

    if vcs_opts:
        steps._vcs_opts.update(vcs_opts)

    workers = [it.name for it in master_config['workers']]

    factory = BuildFactory()
    factory.buildClass = build.PipelineBuild
    factory.addStep(steps.PropStep())
    build.PipelineBuild.workdir_pool_manager = build.WorkdirPoolManager(workdir_pool_config or {})

    for i in range(builders):
        master_config['builders'].append(
            BuilderConfig(name=f"~prop-builder{i}",
                          workernames=workers,
                          factory=factory,
                          tags=[steps.HIDDEN],
                          locks=build.builder_locks))

    factory = BuildFactory()
    factory.buildClass = build.PipelineBuild
    factory.addStep(steps.PropStep())
    # factory.workdir = util.Interpolate('%(prop:pipeline_workdir)s')
    for i in range(inner_builders):
        master_config['builders'].append(
            BuilderConfig(name=f"~prop-inner-builder{i}",
                          workernames=workers,
                          factory=factory,
                          tags=[steps.HIDDEN],
                          locks=build.inner_builder_locks))

    dist_workers = [LocalWorker(f'distributor{i}') for i in range(3)]
    master_config['workers'].extend(dist_workers)

    factory = BuildFactory()
    factory.addStep(steps.DistributeStep(name='get builders'))
    master_config['builders'].append(BuilderConfig(
        name="~distributor",
        properties={'pipeline_stepsdir': stepsdir},
        workernames=[it.name for it in dist_workers],
        factory=factory))

    master_config['schedulers'].append(Triggerable('trig-prop-builder', builder_names))

    if os.environ.get('MEMMON'):
        from . import memmon
        memmon.monitor(os.environ['MEMMON'], in_thread=True)
