import os.path
import json
import yaml
import itertools
import re
from pathlib import Path

from buildbot.plugins import util, worker
from buildbot.schedulers.triggerable import Triggerable
from buildbot.schedulers.basic import AnyBranchScheduler
from buildbot.process import buildstep, logobserver, builder, results
from buildbot.process.factory import BuildFactory
from buildbot.config import BuilderConfig
from buildbot.steps.transfer import MultipleFileUpload
from buildbot.steps.trigger import Trigger
from buildbot.steps.source import git

from twisted.internet import defer
from twisted.python.failure import Failure

from buildbot_pipeline import junit, utils, filters, file_store, build


def gen_steps(step, data):
    if type(data) is list:
        return [gen_steps(step, it) for it in data]

    if 'shell-fail' in data:
        data['shell'] = data.pop('shell-fail')
        data['haltOnFailure'] = True

    if 'shell' in data:
        copy = data.copy()
        copy['command'] = copy.pop('shell')
        env = copy.setdefault('env', {})
        env['BUILD_ID'] = util.Interpolate('%(prop:root_buildnumber:-%(prop:buildnumber)s)s')
        env['WORKSPACE'] = util.Interpolate('%(prop:builddir)s')
        return DynamicStep(**copy)
    elif 'steps' in data:
        return [gen_steps(step, it) for it in data['steps']]
    elif 'parallel' in data:
        return Parallel(data['parallel'])
    elif 'git' in data:
        data.pop('git')
        data.update(_vcs_opts)
        return git.Git(**data)

    raise Exception(f'Unknown step {data}')


@util.renderer
def builder_names(props):
    prefix = props.getProperty('pipeline_builder_prefix')
    worker = props.getProperty('workername', '-some-')
    name = build_counters[prefix].next_builder(worker)
    return [name]


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
            builddir = self.getProperty('builddir')
            root_buildnumber = self.getProperty('pipeline_buildnumber') or self.getProperty('buildnumber')

        result = []
        for it in self.steps_info:
            s = {
                'sched_name': 'trig-prop-builder',
                'props_to_set': {
                    'steps_info': json.dumps(it),
                },
                'unimportant': False
            }

            if self.inner:
                s['props_to_set'].update(
                    virtual_builder_name=f"{builder_name}/{it['name']}",
                    workername=worker_name,
                    parent_builder_name=builder_name,
                    pipeline_builddir=builddir,
                    pipeline_builder_prefix='~prop-inner-builder',
                    pipeline_buildnumber=root_buildnumber,
                )
            else:
                s['props_to_set'].update(
                   virtual_builder_name=it['name'],
                   pipeline_builder_prefix='~prop-builder',
                   reporters='gerrit',
                   pipeline_concurrency=str(it.get('concurrency', 1)),
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
        return results.SUCCESS


class GatherBuilders(buildstep.BuildStep):
    haltOnFailure = True
    name = 'parse builders'

    @defer.inlineCallbacks
    def run(self):
        workdir = os.path.join(self.getProperty('builddir'), self.workdir)
        result = results.SUCCESS
        step_info = []
        repo_path = Path(workdir)
        buildbot_path = repo_path / 'buildbot'
        for it in buildbot_path.glob('**/*.yaml'):
            it_repo_path = str(it.relative_to(repo_path))
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
                    start_build = it_repo_path in changes[0].files
                    if not start_build and 'filters' in step:
                        start_build = filters.make_filters(step['filters'])(changes[0])

                    if start_build:
                        step_info.append(step)
                    else:
                        yield self.addCompleteLog(name, 'skipped by filters')

        if step_info:
            self.build.addStepsAfterCurrentStep([Parallel(step_info, inner=False, waitForFinish=False)])
            return result

        self.descriptionDone = ['There are no suitable jobs']
        return results.CANCELLED


class DistributeStep(buildstep.BuildStep):
    def run(self):
        repo = self.getProperty('repository')
        _, _, self.build.workdir = repo.rpartition('/')
        self.build.addStepsAfterCurrentStep([git.Git(repourl=repo, **_vcs_opts), GatherBuilders()])
        return results.SUCCESS


class DynamicStep(buildstep.ShellMixin, buildstep.BuildStep):
    logEnviron = False

    def __init__(self, **kwargs):
        self.junit = kwargs.pop('junit', None)
        self.upload = kwargs.pop('upload', None)
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
        if result == results.SUCCESS:
            self.build.addStepsAfterCurrentStep(self.extract_steps(self.observer.getStdout()))

        if self.junit:
            yield self.handleJUnit(self.junit)

        if self.upload:
            yield self.handleUpload(self.upload)

        return result

    @defer.inlineCallbacks
    def handleJUnit(self, desc):
        wd = utils.get_workdir(self)
        rv = yield utils.silent_remote_command(self, 'glob', path=os.path.join(wd, desc))
        for fname in rv.updates['files'][0]:
            writer = utils.BufWriter()

            rv = yield utils.silent_remote_command(
                self, 'uploadFile', workdir='/', workersrc=fname, writer=writer,
                blocksize=16384, maxsize=1 << 20, keepstamp=False)

            if rv.rc == results.SUCCESS:
                writer.buf.seek(0)
                suites = junit.parse(writer.buf)
                writer.buf.close()
                h = junit.gen_html(suites, embed=True)
                if suites:
                    n = suites[0]['name']
                else:
                    n = 'tests'
                self.addHTMLLog(n, h)

    @defer.inlineCallbacks
    def handleUpload(self, desc):
        bname = build.builder_name_to_path(self.getProperty('virtual_builder_name') or self.getProperty('buildername'))
        bnum = self.getProperty('pipeline_buildnumber') or self.getProperty('buildnumber')
        cmd = MultipleFileUpload(
            workersrcs=[desc['files']],
            glob=True,
            url=f'file-store/{bname}/{bnum}/' + desc.get('link', ''),
            urlText=desc.get('title'),
            masterdest=os.path.join(file_store.app.path, bname, str(bnum)))

        cmd.setBuild(self.build)
        cmd.setWorker(self.worker)
        cmd.stepid = self.stepid
        cmd._running = True
        cmd.remote = self.remote
        cmd.addLog = self.getLog
        yield cmd.run()


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


build_counters = {}
_vcs_opts = {'logEnviron': False, 'mode': 'full', 'method': 'fresh'}


def init_pipeline(master_config, builders, inner_builders, change_filter=None, vcs_opts=None):
    build_counters['~prop-builder'] = BuilderCounter('~prop-builder', builders)
    build_counters['~prop-inner-builder'] = BuilderCounter('~prop-inner-builder', inner_builders)

    if vcs_opts:
        _vcs_opts.update(vcs_opts)

    workers = [it.name for it in master_config['workers']]

    factory = BuildFactory()
    factory.buildClass = build.PipelineBuild
    factory.addStep(PropStep())
    # factory.workdir = util.Interpolate('%(prop:virtual_builder_name)s')
    for i in range(builders):
        master_config['builders'].append(
            BuilderConfig(name=f"~prop-builder{i}",
                          workernames=workers,
                          factory=factory,
                          locks=build.builder_locks))

    factory = BuildFactory()
    factory.buildClass = build.PipelineBuild
    factory.addStep(PropStep())
    # factory.workdir = util.Interpolate('%(prop:pipeline_workdir)s')
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


@utils.wrapit(builder.Builder, 'getAvailableWorkers')
def getAvailableWorkers(orig, self):
    if not self.name.startswith('~prop-builder'):
        return orig(self)

    result = []
    for name, bldr in self.botmaster.builders.items():
        if name.startswith('~prop-builder'):
            result.extend(orig(bldr))

    return result


@utils.wrapit(builder.Builder, 'maybeStartBuild')
def maybeStartBuild(orig, self, workerforbuilder, breqs):
    if not self.running:
        return defer.succeed(False)

    if not self.name.startswith('~prop-builder'):
        return orig(self, workerforbuilder, breqs)

    return orig(workerforbuilder.builder, workerforbuilder, breqs)
