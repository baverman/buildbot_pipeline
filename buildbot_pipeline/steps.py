import os.path
import itertools
import json
import yaml
import shlex
import re
from pathlib import Path

from buildbot.process import buildstep, logobserver, results, properties
from buildbot.steps.transfer import MultipleFileUpload
from buildbot.steps.trigger import Trigger
from buildbot.steps.source import git

from twisted.internet import defer
from twisted.python.failure import Failure

from buildbot_pipeline import junit, utils, filters, file_store, build, schedulers as bbp_schedulers

DEFAULT_STEPSDIR = 'buildbot'
HIDDEN = 'hidden'


def process_interpolate(value):
    if type(value) is str:
        if value.startswith('!'):
            return properties.Interpolate(value[1:])
        elif value.startswith(r'@'):
            return value[1:]
        elif '%(' in value:
            return properties.Interpolate(value)
        else:
            return value
    elif type(value) is list:
        return [process_interpolate(v) for v in value]
    elif type(value) is dict:
        return {k: process_interpolate(v) for k, v in value.items()}
    else:
        return value


def normalize_pipeline(pipeline):
    if 'filters' in pipeline:
        pipeline['filter'] = pipeline.pop('filters')

    if 'scheduler' in pipeline:
        pipeline['schedulers'] = pipeline.pop('scheduler')

    if 'schedulers' in pipeline:
        pipeline['schedulers'] = utils.ensure_list(pipeline['schedulers'])

    pipeline['steps'] = utils.ensure_list(pipeline.get('steps', []))
    if 'parallel' in pipeline:
        pipeline['steps'].append({'parallel': pipeline.pop('parallel')})

    if 'matrix' in pipeline:
        pipeline['steps'].append({'matrix': pipeline.pop('matrix')})

    if 'pmatrix' in pipeline:
        pipeline['steps'].append({'parallel': {'matrix': pipeline.pop('matrix')}})

    return pipeline


def gen_steps(step, data):
    if type(data) is list:
        return [gen_steps(step, it) for it in data]

    if 'shell-fail' in data:
        data['shell'] = data.pop('shell-fail')
        data['haltOnFailure'] = True

    if 'pmatrix' in data:
        data = {'parallel': {'matrix': data.pop('pmatrix')}}

    if 'decodeRC' in data:
        # keys are implicitly converted to str during json dumping
        # fix type back to int
        data['decodeRC'] = {int(i): k for i, k in data['decodeRC'].items()}

    if 'shell' in data:
        data['command'] = data.pop('shell')
        data['doStepIf'] = do_step_if(data)
        step_env = data.get('env', {})
        data['env'] = step.build.pipeline_env.copy()
        data['env'].update(step_env)
        data = process_interpolate(data)
        data['env']['BUILD_ID'] = properties.Interpolate('%(prop:pipeline_buildnumber:-%(prop:buildnumber)s)s')
        data['env']['WORKSPACE'] = properties.Interpolate('%(prop:builddir)s')
        data['env']['BUILD_STATUS'] = build_results
        return DynamicStep(**data)
    elif 'trigger' in data:
        # trigger:
        #   - builder1
        #   - name: builder2
        #     properties:
        #       prop1: value
        #
        # trigger:
        #   properties:
        #     prop: value
        #   builders:
        #     - builder1
        #     - name: builder2
        #       properties:
        #         prop1: value
        info = data['trigger']
        if type(info) is list:
            info = {'builders': info}

        builders = []
        common_props = info.get('properties', {})
        builder_props = {}
        build_props = {'builders': builders, 'common_props': common_props, 'builder_props': builder_props}
        for it in info.get('builders', []):
            if isinstance(it, str):
                builders.append(it)
            else:
                builders.append(it['name'])
                builder_props[it['name']] = it.get('properties', {})
        return GatherBuilders(
            local=False,
            wait_for_finish=info.get('waitForFinish', True),
            build_props=build_props)
    elif 'steps' in data:
        return [gen_steps(step, it) for it in data['steps']]
    elif 'parallel' in data:
        info = data['parallel']
        if type(info) is list:
            info = {'steps': info}

        matrix = info.pop('matrix', None)
        steps = info.pop('steps', [])
        if matrix:
            steps.insert(0, {'matrix': matrix})

        info['doStepIf'] = do_step_if(info)
        info.pop('inner', None)
        return Parallel(list(matrix_steps(steps)), **info)
    elif 'git' in data:
        data = process_interpolate(data)
        data.pop('git')
        data.update(_vcs_opts)
        return git.Git(**data)

    raise Exception(f'Unknown step {data}')


def matrix_steps(steps):
    for info in steps:
        if 'matrix' in info:
            step_desc = info['matrix']
            name = step_desc.pop('name', None)
            skip_passed = step_desc.pop('skip_passed', None)
            all_params = step_desc.pop('params', [])
            for params in utils.ensure_list(all_params):
                params.pop('workername', None)
                params = list(params.items())
                params_keys = [it[0] for it in params]
                params_values = [utils.ensure_list(it[1]) for it in params]
                for pvals in itertools.product(*params_values):
                    props = dict(zip(params_keys, pvals))
                    s = step_desc.copy()
                    s['properties'] = s.get('properties', {}).copy()
                    s['properties'].update(props)
                    if skip_passed is not None:
                        s['properties']['skip_passed'] = skip_passed
                    s['name'] = name.format(**props) if name else '-'.join(map(str, pvals))
                    yield s
        else:
            yield info


@properties.renderer
def build_results(props):
    build = props.getBuild()
    if build.results is not None:
        return str(build.results)
    return ''


class Parallel(Trigger):
    def __init__(self, steps_info, inner=True, **kwargs):
        kwargs.setdefault('waitForFinish', True)
        super().__init__('trig-prop-builder', **kwargs)
        self.steps_info = steps_info
        self.correct_names = [it['name'] for it in steps_info]
        self.inner = inner

    def getAllGotRevisions(self):
        # annotated tags can skew revision so we need to get original revision
        # instead of got_revision property
        revisions = self.getProperty('revision', {})
        if not isinstance(revisions, dict):
            revisions = {'': revisions}
        return revisions

    @defer.inlineCallbacks
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

            passthrough_propnames = (self.getProperty('pipeline_passthrough_props') or []) + ['pipeline_passthrough_props']
            props = {k: self.getProperty(k) for k in passthrough_propnames}
            props.update(it.get('properties', {}))
            props = yield self.render(process_interpolate(props))
            s['props_to_set'].update(props)

            if self.inner:
                s['props_to_set'].update(
                    virtual_builder_name=f"{builder_name}/{it['name']}",
                    virtual_builder_title=it['name'],
                    virtual_builder_tags=[HIDDEN],
                    workername=worker_name,
                    parent_builder_name=builder_name,
                    pipeline_builddir=builddir,
                    pipeline_builder_prefix='~prop-inner-builder',
                    pipeline_buildnumber=root_buildnumber,
                )
            else:
                s['props_to_set'].update(
                   virtual_builder_name=it['name'],
                   virtual_builder_tags=utils.ensure_list(it.get('tags', [])),
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
    hideStepIf = staticmethod(utils.hide_if_success)
    name = 'init'

    @defer.inlineCallbacks
    def checkAlreadyPassed(self):
        build = yield utils.get_last_successful_build(self.master, self.build.buildid)
        if build:
            self.addURL('Last successful build', f'#/builders/{build.builderid}/builds/{build.number}')
            self.descriptionDone = ['Already passed']
            self.build.results = results.SKIPPED
            return True

    @defer.inlineCallbacks
    def run(self):
        steps_info = json.loads(self.getProperty('steps_info', '{}'))

        if utils.to_bool(self.getProperty('skip_passed')):
            already_passed = yield self.checkAlreadyPassed()
            if already_passed:
                return results.SKIPPED

        # TODO: move env handling to gen_steps
        self.build.pipeline_env = {}
        if type(steps_info) is dict:
            self.build.pipeline_env = steps_info.get('env', {})

        self.build.addStepsAfterCurrentStep(utils.ensure_list(gen_steps(self, steps_info)))
        return results.SUCCESS


class GatherBuilders(buildstep.BuildStep):
    haltOnFailure = True
    name = 'parse builders'

    def __init__(self, **kwargs):
        self.pipeline_build_props = kwargs.pop('build_props', None)
        self.wait_for_finish = kwargs.pop('wait_for_finish', False)
        self.is_local = kwargs.pop('local', True)
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def list_pipeline_files(self):
        workdir = os.path.join(self.getProperty('builddir'), self.workdir)
        wc_path = Path(workdir)
        buildbot_path = wc_path / self.getProperty('pipeline_stepsdir', DEFAULT_STEPSDIR)
        result = []

        def extract_parts(fullpath):
            repopath = str(fullpath.relative_to(wc_path))
            name, _, _ = str(fullpath.relative_to(buildbot_path)).rpartition('.')
            return name, str(fullpath), repopath

        if self.is_local:
            for it in buildbot_path.glob('**/*.yaml'):
                result.append(extract_parts(it))
        else:
            rv = yield utils.silent_remote_command(self, 'glob', path=str(buildbot_path / '**/*.yaml'))
            for it in rv.updates['files'][0]:
                result.append(extract_parts(Path(it)))
        return result

    @defer.inlineCallbacks
    def get_pipeline_content(self, fullpath):
        if self.is_local:
            with open(fullpath) as f:
                return yaml.safe_load(f)
        else:
            writer = utils.BufWriter()
            try:
                rv = yield utils.silent_remote_command(
                    self, 'uploadFile', workdir='/', workersrc=fullpath, writer=writer,
                    blocksize=16384, maxsize=1 << 20, keepstamp=False)
                if rv.rc == results.SUCCESS:
                    writer.buf.seek(0)
                    return yaml.safe_load(writer.buf)
                return None
            finally:
                writer.buf.close()

    @defer.inlineCallbacks
    def run(self):
        build_props = self.pipeline_build_props or self.getProperty('pipeline_build_props', {})
        forced_builders = build_props.get('builders')
        common_props = build_props.get('common_props', {})
        builder_props = build_props.get('builder_props', {})

        if not self.getProperty('revision') and self.getProperty('got_revision'):
            self.setProperty('revision', self.getProperty('got_revision'), 'Build')

        schedulers = []

        branch = self.getProperty('branch')
        repo = self.getProperty('repository')
        result = results.SUCCESS
        step_info = []
        changes = list(self.build.allChanges())
        pipelines = yield self.list_pipeline_files()
        for name, fullpath, repopath in pipelines:
            skip_reason = 'unknown'
            start_build = None

            if forced_builders:
                start_build = name in forced_builders
                if not start_build:
                    continue

            try:
                step = yield self.get_pipeline_content(fullpath)
                step = normalize_pipeline(step)
            except Exception as e:
                result = results.WARNINGS
                yield self.addCompleteLog(name, Failure(e).getTraceback())
                continue

            if not step:
                continue

            if self.is_local and not self.pipeline_build_props:
                for it in step.get('schedulers', []):
                    try:
                        it['builder'] = name
                        it['name'] = f'{name}/{it["name"]}'
                        it['repo'] = repo
                        schedulers.append(it)
                    except Exception as e:
                        yield self.addCompleteLog(name + '/scheduler', Failure(e).getTraceback())
                        break

            step['name'] = name
            step['steps'].insert(0, {'git': True, 'repourl': repo})

            if step.get('disabled'):
                start_build = False
                skip_reason = 'disabled'

            if changes:
                if start_build is None and repopath in changes[0].files:
                    start_build = True

                if start_build is None and 'filter' in step:
                    if 'status' not in step['filter']:
                        step['filter']['status'] = 'new'

                    try:
                        flt = filters.make_filters(step['filter'])
                    except Exception as e:
                        result = results.WARNINGS
                        skip_reason = str(e)
                        yield self.addCompleteLog(name, str(e))
                    else:
                        changes[0].props = self.getProperties()
                        if flt and flt(changes[0]):
                            start_build = True
                        else:
                            skip_reason = 'filter'

            if start_build:
                props = step.get('properties', {}).copy()
                props.update(common_props)
                props.update(builder_props.get(name, {}))
                if props:
                    props['pipeline_passthrough_props'] = list(props)

                props.update(step.get('local_properties', {}))
                step['properties'] = props
                step_info.append(step)
            else:
                yield self.addCompleteLog(name, f'skipped by: {skip_reason}')

        if schedulers:
            yield bbp_schedulers.update_schedulers(self.master, branch, schedulers)

        if step_info:
            self.build.addStepsAfterCurrentStep([Parallel(step_info, inner=False, waitForFinish=self.wait_for_finish)])
            return result

        self.descriptionDone = ['There are no suitable jobs']
        self.build.results = results.SKIPPED
        return results.SKIPPED


def do_step_if(step_data):
    when = step_data.pop('when', None)
    skip_when = step_data.pop('skip_when', None)
    if when is None and skip_when is None:
        return step_data.get('doStepIf', True)

    @defer.inlineCallbacks
    def inner(build):
        if when is not None:
            value = yield build.render(properties.Interpolate(when))
            return utils.to_bool(value)

        if skip_when is not None:
            value = yield build.render(properties.Interpolate(skip_when))
            return not utils.to_bool(value)

        return True

    return inner


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

    def extract_props(self, stdout):
        r = '(?m)__PIPELINE_' + r'PROP__\s+(.+)$'
        for data in re.findall(r, stdout):
            name, value = data.split(None, 1)
            yield name, value

    def extract_links(self, stdout):
        r = '(?m)__PIPELINE_' + r'LINK__\s+(.+)$'
        for data in re.findall(r, stdout):
            parts = shlex.split(data)
            if len(parts) >= 2:
                yield parts[:2]

    @defer.inlineCallbacks
    def run(self):
        cmd = yield self.makeRemoteShellCommand()
        yield self.runCommand(cmd)
        result = cmd.results()
        stdout = self.observer.getStdout()
        if result == results.SUCCESS:
            self.build.addStepsAfterCurrentStep(self.extract_steps(stdout))

        for name, url in self.extract_links(stdout):
            yield self.addURL(name, url)

        for name, value in self.extract_props(stdout):
            yield self.setProperty(name, value, 'Step')

        if self.junit:
            for desc in utils.ensure_list(self.junit):
                yield self.handleJUnit(desc)

        if self.upload:
            for desc in utils.ensure_list(self.upload):
                yield self.handleUpload(desc)

        return result

    @defer.inlineCallbacks
    def handleJUnit(self, desc):
        desc = yield self.render(desc)
        if type(desc) is dict:
            label = desc.get('label')
            src = desc.get('src')
        else:
            label = None
            src = desc

        if not src:
            return

        wd = utils.get_workdir(self)
        rv = yield utils.silent_remote_command(self, 'glob', path=os.path.join(wd, src))
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
                n = label or (suites and suites[0]['name'] or 'tests')
                yield self.addHTMLLog(n, h)

    @defer.inlineCallbacks
    def handleUpload(self, desc):
        desc = yield self.render(desc)
        bname = build.builder_name_to_path(self.getProperty('virtual_builder_name') or self.getProperty('buildername'))
        bnum = self.getProperty('pipeline_buildnumber') or self.getProperty('buildnumber')

        build_storage_path = os.path.realpath(os.path.join(file_store.ep.path, bname, str(bnum)))
        if desc.get('dest'):
            dest = os.path.realpath(os.path.join(build_storage_path, desc['dest']))
            if len(os.path.commonpath([dest, build_storage_path])) < len(build_storage_path):
                raise Exception('Upload destination path should be relative to build storage path')
        else:
            dest = build_storage_path

        cmd = MultipleFileUpload(
            workersrcs=utils.ensure_list(desc['src']),
            glob=True,
            url=f'/file-store/{bname}/{bnum}/' + desc.get('link', ''),
            urlText=desc.get('label'),
            masterdest=dest)

        cmd.setBuild(self.build)
        cmd.setWorker(self.worker)
        cmd.stepid = self.stepid
        cmd._running = True
        cmd.remote = self.remote
        cmd.addLog = lambda name: defer.succeed(self.getLog(name))
        yield cmd.run()


_vcs_opts = {'logEnviron': False, 'mode': 'full', 'method': 'fresh'}
