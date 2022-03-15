import os.path
import json
import yaml
import itertools
import re
from pathlib import Path

from buildbot.plugins import util, worker
from buildbot.schedulers.triggerable import Triggerable
from buildbot.schedulers.basic import AnyBranchScheduler
from buildbot.process import buildstep, logobserver
from buildbot.process.factory import BuildFactory
from buildbot.config import BuilderConfig
from buildbot.steps.transfer import MultipleFileUpload
from buildbot.steps.trigger import Trigger
from buildbot.steps.source import git

from twisted.internet import defer
from twisted.python.failure import Failure

from buildbot_pipeline import junit, utils, filters, file_store


def gen_steps(step, data):
    if type(data) is list:
        return [gen_steps(step, it) for it in data]
    elif 'shell' in data:
        copy = data.copy()
        copy['command'] = copy.pop('shell')
        return DynamicStep(**copy)
    elif 'steps' in data:
        return [gen_steps(step, it) for it in data['steps']]
    elif 'parallel' in data:
        return Parallel(data['parallel'])
    elif 'git' in data:
        data.pop('git')
        data.update(_vcs_opts)
        return git.Git(**data)
    elif 'upload' in data:
        bname = step.getProperty('virtual_builder_name') or step.getProperty('buildername')
        bnum = step.getProperty('buildnumber')
        return MultipleFileUpload(
            workersrcs=[data['upload']],
            glob=True,
            url=f'file-store/{bname}/{bnum}/',
            masterdest=os.path.join(file_store.app.path, bname, str(bnum)))

    raise Exception(f'Unknown step {data}')


@util.renderer
def builder_names(props):
    return [props.getProperty('pipeline_builder')]


class Parallel(Trigger):
    waitForFinish = True

    def __init__(self, steps_info, inner=True, **kwargs):
        super().__init__('trig-prop-builder', **kwargs)
        self.steps_info = steps_info
        self.correct_names = [it['name'] for it in steps_info]
        self.inner = inner

    # @defer.inlineCallbacks
    def getSchedulersAndProperties(self):
        if self.inner:
            builder_name = self.getProperty('parent_builder_name') or self.getProperty('virtual_builder_name') or self.getProperty('buildername')
            worker_name = self.getProperty('workername')
            workdir = self.getProperty('pipeline_workdir') or os.path.join(self.getProperty('builddir'), self.workdir)

        # url = yield self.build.getUrl()
        result = []
        for it in self.steps_info:
            s = {
                'sched_name': 'trig-prop-builder',
                'props_to_set': {
                    'steps_info': json.dumps(it),
                    # 'parent_build': url,
                },
                'unimportant': False
            }

            if self.inner:
                s['props_to_set'].update(
                    virtual_builder_name=f"{builder_name}/{it['name']}",
                    workername=worker_name,
                    parent_builder_name=builder_name,
                    pipeline_workdir=workdir,
                    pipeline_builder=inner_build_counter.next_builder(worker_name),
                )
            else:
                s['props_to_set'].update(
                   virtual_builder_name=it['name'],
                   pipeline_builder=build_counter.next_builder('one'),
                   reporters='gerrit',
                )

            result.append(s)
        return result

    def getCurrentSummary(self):
        if self.triggeredNames:
            self.triggeredNames = self.correct_names
        return super().getCurrentSummary()


class PropStep(buildstep.BuildStep):
    hideStepIf = True

    def run(self):
        self.build.addStepsAfterCurrentStep(utils.ensure_list(gen_steps(
            self, json.loads(self.getProperty('steps_info', '{}')))))
        return util.SUCCESS


class GatherBuilders(buildstep.BuildStep):
    haltOnFailure = True
    name = 'parse builders'

    @defer.inlineCallbacks
    def run(self):
        workdir = os.path.join(self.getProperty('builddir'), self.workdir)
        result = util.SUCCESS
        step_info = []
        buildbot_path = Path(workdir) / 'buildbot'
        for it in buildbot_path.glob('**/*.yaml'):
            name, _, _ = str(it.relative_to(buildbot_path)).rpartition('.')
            try:
                with open(it) as f:
                    step = yaml.safe_load(f)
            except Exception as e:
                result = util.WARNINGS
                yield self.addCompleteLog(name, Failure(e).getTraceback())
            else:
                repo = self.getProperty('repository')
                step['name'] = name
                if 'steps' in step:
                    step['steps'].insert(0, {'git': True, 'repourl': repo})

                changes = list(self.build.allChanges())
                if changes:
                    if 'filters' in step:
                        if not filters.make_filters(step['filters'])(changes[0]):
                            yield self.addCompleteLog(name, 'skipped by filters')
                            continue

                    step_info.append(step)

        if step_info:
            self.build.addStepsAfterCurrentStep([Parallel(step_info, inner=False, waitForFinish=False)])

        return result


class DistributeStep(buildstep.BuildStep):
    def run(self):
        repo = self.getProperty('repository')
        _, _, self.build.workdir = repo.rpartition('/')
        self.build.addStepsAfterCurrentStep([git.Git(repourl=repo, **_vcs_opts), GatherBuilders()])
        return util.SUCCESS


class DynamicStep(buildstep.ShellMixin, buildstep.BuildStep):
    logEnviron = False

    def __init__(self, **kwargs):
        self.junit = kwargs.pop('junit', None)
        kwargs = self.setupShellMixin(kwargs)
        super().__init__(**kwargs)
        self.observer = logobserver.BufferLogObserver()
        self.addLogObserver('stdio', self.observer)

    def extract_steps(self, stdout):
        m = re.search('(?s)__PIPELINE_' + 'START__(.*)__PIPELINE_' + 'END__', stdout)
        if not m:
            return []

        data = yaml.safe_load(m[1])
        return utils.ensure_list(gen_steps(self, data))

    @defer.inlineCallbacks
    def run(self):
        cmd = yield self.makeRemoteShellCommand()
        yield self.runCommand(cmd)
        result = cmd.results()
        if result == util.SUCCESS:
            self.build.addStepsAfterCurrentStep(self.extract_steps(self.observer.getStdout()))

        if self.junit:
            wd = utils.get_workdir(self)
            rv = yield utils.silent_remote_command(self, 'glob', path=os.path.join(wd, self.junit))
            for fname in rv.updates['files'][0]:
                writer = utils.BufWriter()

                rv = yield utils.silent_remote_command(
                    self, 'uploadFile', workdir='/', workersrc=fname, writer=writer,
                    blocksize=16384, maxsize=1 << 20, keepstamp=False)

                if rv.rc == util.SUCCESS:
                    writer.buf.seek(0)
                    suites = junit.parse(writer.buf)
                    writer.buf.close()
                    h = junit.gen_html(suites, embed=True)
                    if suites:
                        n = suites[0]['name']
                    else:
                        n = 'tests'
                    self.addHTMLLog(n, h)

        return result


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
        return f'{self.prefix}{next(c)}'


build_counter = None
inner_build_counter = None
_vcs_opts = {'logEnviron': False, 'mode': 'full', 'method': 'fresh'}


def init_pipeline(master_config, builders, inner_builders, change_filter=None, vcs_opts=None):
    global build_counter, inner_build_counter
    build_counter = BuilderCounter('~prop-builder', builders)
    inner_build_counter = BuilderCounter('~prop-inner-builder', inner_builders)

    if vcs_opts:
        _vcs_opts.update(vcs_opts)

    workers = [it.name for it in master_config['workers']]

    factory = BuildFactory()
    factory.addStep(PropStep())
    factory.workdir = util.Interpolate('%(prop:virtual_builder_name)s')
    for i in range(builders):
        master_config['builders'].append(
            BuilderConfig(name=f"~prop-builder{i}",
                          workernames=workers,
                          factory=factory))

    factory = BuildFactory()
    factory.addStep(PropStep())
    factory.workdir = util.Interpolate('%(prop:pipeline_workdir)s')
    for i in range(inner_builders):
        master_config['builders'].append(
            BuilderConfig(name=f"~prop-inner-builder{i}",
                          workernames=workers,
                          factory=factory))

    dist_workers = [worker.LocalWorker(f'distributor{i}') for i in range(3)]
    master_config['workers'].extend(dist_workers)

    factory = BuildFactory()
    factory.addStep(DistributeStep(name='get builders'))
    master_config['builders'].append(BuilderConfig(
        name="~distributor", workernames=[it.name for it in dist_workers], factory=factory))

    master_config['schedulers'].append(AnyBranchScheduler(
        name="~distributor",
        treeStableTimer=None,
        change_filter=change_filter,
        builderNames=["~distributor"]))

    master_config['schedulers'].append(Triggerable('trig-prop-builder', builder_names))

    file_store.init()


# @wrapit(builder.Builder, 'getAvailableWorkers')
# def getAvailableWorkers(orig, self):
#     current_workers = orig(self)
#     if self.name != 'prop-builder0':
#         return current_workers
#
#     result = []
#     for wfb in current_workers:
#         nwfb = workerforbuilder.WorkerForBuilder()
#         nwfb.setBuilder(self)
#         nwfb.builder_name = self.name + str(id(nwfb))
#         nwfb.remoteCommands = wfb.remoteCommands
#         nwfb.worker = wfb.worker
#         nwfb.state = workerforbuilder.States.AVAILABLE
#         result.append(nwfb)
#
#     return result
