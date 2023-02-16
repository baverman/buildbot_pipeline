const builderNameCache = new Map()

export const RESULTS = ["success", "warnings", "failure", "skipped", "exception", "retry", "cancelled", "unknown"]

export function urlQuery(data) {
    var result = []
    for(var k in data) {
        const val = data[k]
        if (val) {
            if (typeof(val) == typeof([])) {
                for(var it of val) {
                    result.push(`${k}=${it}`)
                }
            } else {
                result.push(`${k}=${val}`)
            }
        }
    }
    return result.join('&')
}


export function resultClass(obj, no_pulse) {
    var num = obj.results;
    var add = '';
    if (num == null) {
        num = 99;
        if (!no_pulse) {
            add = ' pulse';
        }
    }
    return `results_${num}${add}`;
}

export function resultTitle(obj) {
    if (obj.results == null) {
        return 'in progress';
    }
    return RESULTS[obj.results] || 'unknown';
}

export async function fetchData(config, url) {
    const resp = await fetch(config.backend + url)
    return await resp.json()
}

export async function getBuildByNumber(config, builderid, number) {
    const url = `/api/v2/builders/${builderid}/builds/${number}`
    return (await fetchData(config, url)).builds[0] || null
}

export async function sendBuildAction(config, buildid, action) {
    return await sendRPC(`/builds/${buildid}`, action)
}

export async function sendRPC(config, url, action, params) {
    const payload = JSON.stringify({
        'id': url,
        'jsonrpc': '2.0',
        'method': action,
        'params': params || {},
    })
    const resp = await fetch(config.backend + '/api/v2' + url, {
        'method': 'POST',
        'body': payload,
        'headers': {'Content-Type': 'application/json'},
    })
    return await resp.json()
}

export async function getBuildsByNumber(config, bnums) {
    if (!bnums.length) {
        return []
    }
    const url = `/api/v2/builds?bnums=${bnums.join(',')}`
    return (await fetchData(config, url)).builds || null
}

export async function getBuildsByRequest(config, reqids, settings) {
    if (!reqids.length) {
        return []
    }
    const props = settings && settings.properties
    const url = '/api/v2/builds?' + urlQuery({reqids: reqids.join(','), property: props})
    return (await fetchData(config, url)).builds || null
}

export async function getRequests(config, reqids) {
    if (!reqids.length) {
        return []
    }
    const url = `/api/v2/buildrequests?reqids=${reqids.join(',')}`
    return (await fetchData(config, url)).buildrequests || null
}

export async function getBuildset(config, id) {
    const url = `/api/v2/buildsets/${id}`
    return (await fetchData(config, url)).buildsets[0]
}

export async function getAllBuilders(config) {
    const data = await fetchData(config, '/api/v2/builders?order=name')
    for (var it of data.builders) {
        builderNameCache.set(it.builderid, it.name)
    }
    return data.builders
}

export async function getBuilders(config, builder_ids) {
    if (!builder_ids.length) {
        return []
    }
    const data = await fetchData(config, `/api/v2/builders?builderids=${builder_ids.join(',')}`)
    for (var it of data.builders) {
        builderNameCache.set(it.builderid, it.name)
    }
    return data.builders
}

export async function getBuilderBuilds(config, builder_ids) {
    if (!builder_ids.length) {
        return []
    }
    const data = await fetchData(config, `/api/v2/builds?builderids=${builder_ids.join(',')}&order=-buildid&limit=300`)
    return data.builds
}

export async function getBuilderNames(config, builder_ids) {
    const non_existing_ids = builder_ids.filter(it => !builderNameCache.has(it))
    await getBuilders(config, non_existing_ids)
    const result = new Map()
    for (var it of builder_ids) {
        result.set(it, builderNameCache.get(it, 'unknown'))
    }
    return result
}

export async function getBuilderName(config, id) {
    return (await getBuilderNames(config, [id])).get(id)
}

export async function getBuild(config, id) {
    return (await fetchData(config, `/api/v2/builds/${id}`)).builds[0] || null
}

export async function getWorker(config, id) {
    return (await fetchData(config, `/api/v2/workers/${id}`)).workers[0] || null
}

export async function getBuildSteps(config, id) {
    return (await fetchData(config, `/api/v2/builds/${id}/steps`)).steps
}

export async function getBuildProperties(config, id) {
    return (await fetchData(config, `/api/v2/builds/${id}/properties`)).properties[0] || {}
}

export async function getBuildChanges(config, id) {
    return (await fetchData(config, `/api/v2/builds/${id}/changes`)).changes
}

export async function getChangesBySSID(config, id) {
    return (await fetchData(config, `/api/v2/sourcestamps/${id}/changes`)).changes
}

export async function getChangeBuilds(config, id) {
    return (await fetchData(config, `/api/v2/changes/${id}/builds`)).builds
}

export async function getStepLogs(config, id) {
    return (await fetchData(config, `/api/v2/steps/${id}/logs`)).logs
}

const BUILDREQUEST_RE = /#buildrequests\/(\d+)$/
const BUILDNUM_RE = /#builders\/(\d+)\/builds\/(\d+)$/

export function parseStepUrls(urls) {
    const requests = []
    const builds = []
    const other = []
    for (var it of urls) {
        if (it.url.includes('#buildrequests/')) {
            const m = it.url.match(BUILDREQUEST_RE)
            if (m !== null) {
                it.reqid = parseInt(m[1])
                requests.push(it)
                continue
            }
        } else if (it.url.includes('#builders/')) {
            const m = it.url.match(BUILDNUM_RE)
            if (m !== null) {
                it.bnum = m[1] + '-' + m[2]
                it.builderid = parseInt(m[1])
                it.number = parseInt(m[2])
                builds.push(it)
                continue
            }
        }
        if (it.url.startsWith('file-store/')) {
            it.url = '/' + it.url
        }
        other.push(it)
    }
    return {requests, builds, other}
}

export async function getLogContent(config, logid, offset, limit) {
    const qs = []
    if (offset !== null && offset !== undefined) {
        qs.push(`offset=${offset}`)
    }
    if (limit !== null && limit !== undefined) {
        qs.push(`limit=${limit}`)
    }
    const qsstr = qs.length ? ('?' + qs.join('&')) : ''
    const url = `/api/v2/logs/${logid}/contents${qsstr}`
    return (await fetchData(config, url)).logchunks
}

export async function getWorkers(config) {
    const data = await fetchData(config, `/api/v2/workers?order=name`)
    return data.workers
}
