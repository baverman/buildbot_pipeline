from buildbot.schedulers.timed import Periodic, Nightly
from twisted.internet import defer
from twisted.python import log


def make_scheduler(sdata):
    skwargs = dict(
        name=sdata['name'],
        builderNames=["~distributor"],
        codebases={'': {'branch': sdata['branch'], 'repository': sdata['repo']}},
        properties={
            'pipeline_build_props': {
                'builders': [sdata['builder']],
                'common_props': sdata.get('properties', {})
            },
        },
    )

    if sdata['type'] == 'periodic':
        skwargs['periodicBuildTimer'] = sdata.get('period', sdata.get('periodicBuildTimer', 3600))
        s = Periodic(**skwargs)
    elif sdata['type'] == 'nightly':
        for f in ['minute', 'hour', 'dayOfMonth', 'month', 'dayOfWeek']:
            if f in sdata:
                skwargs[f] = sdata[f]
        s = Nightly(**skwargs)
    else:
        raise Exception(f'Unknown type {sdata["type"]}')

    s.pipeline_config_branch = config_branch(sdata)
    s.pipeline_state = sdata
    return s


def config_branch(sdata):
    return sdata.get('config-branch') or sdata['branch']


@defer.inlineCallbacks
def update_schedulers(master, branch, schedulers):
    if not branch:
        return

    removed_schedulers = set()
    for k, v in list(master.config.schedulers.items()):
        if branch == getattr(v, 'pipeline_config_branch', None):
            removed_schedulers.add(v.name)
            master.config.schedulers.pop(k, None)

    added_schedulers = set()
    for it in schedulers:
        try:
            if config_branch(it) != branch:
                continue

            master.config.schedulers[it['name']] = s = make_scheduler(it)
            added_schedulers.add(s.name)
        except Exception as e:
            # TODO: add error information into step
            log.err(e, 'error adding scheduler')
            continue

    if added_schedulers or removed_schedulers:
        if removed_schedulers - added_schedulers:
            log.msg(f'removed schedulers on branch {branch}: {removed_schedulers - added_schedulers}')
        if added_schedulers & removed_schedulers:
            log.msg(f'changed schedulers on branch {branch}: {added_schedulers & removed_schedulers}')
        if added_schedulers - removed_schedulers:
            log.msg(f'added schedulers on branch {branch}: {added_schedulers - removed_schedulers}')

        yield master.scheduler_manager.reconfigServiceWithBuildbotConfig(master.config)
