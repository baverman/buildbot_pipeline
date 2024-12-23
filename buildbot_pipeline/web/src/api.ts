import {
    type Worker,
    type Builder,
    type Build,
    type Log,
    type LogChunk,
    type Step,
    type Change,
    type Properties,
    type BuildRequest,
    type BuildSet,
} from './types'

const builderNameCache = new Map<number, string>()

export interface Config {
    backend: string
    log_limit: number
}

export async function fetchData(config: Config, url: string) {
    const resp = await fetch(config.backend + url, {
        headers: { Accept: 'application/json' },
    })
    return await resp.json()
}

export async function sendRPC(config: Config, url: string, action: string, params?: object) {
    const payload = JSON.stringify({
        id: url,
        jsonrpc: '2.0',
        method: action,
        params: params ?? {},
    })
    const resp = await fetch(config.backend + '/api/v2' + url, {
        method: 'POST',
        body: payload,
        headers: { 'Content-Type': 'application/json' },
    })
    return await resp.json()
}

export async function sendBuildAction(config: Config, buildid: number, action: string) {
    return await sendRPC(config, `/builds/${buildid}`, action)
}

export async function getWorkers(config: Config): Promise<Worker[]> {
    const data = await fetchData(config, `/api/v2/workers?order=name`)
    return data.workers
}

export async function getWorker(config: Config, id: number): Promise<Worker | null> {
    return (await fetchData(config, `/api/v2/workers/${id}`))?.workers[0]
}

export async function getAllBuilders(config: Config): Promise<Builder[]> {
    const data = await fetchData(config, '/api/v2/builders?order=name')
    for (const it of data.builders) {
        builderNameCache.set(it.builderid, it.name)
    }
    return data.builders
}

export async function getBuilderBuilds(config: Config, builder_ids: number[]): Promise<Build[]> {
    if (!builder_ids.length) {
        return []
    }
    const data = await fetchData(
        config,
        `/api/v2/builds?builderids=${builder_ids.join(',')}&order=-buildid&limit=300`,
    )
    return data.builds
}

export async function getLogContent(
    config: Config,
    logid: number,
    offset?: number,
    limit?: number,
): Promise<LogChunk[]> {
    const qs = []
    if (offset !== null && offset !== undefined) {
        qs.push(`offset=${offset}`)
    }
    if (limit !== null && limit !== undefined) {
        qs.push(`limit=${limit}`)
    }
    const qsstr = qs.length ? '?' + qs.join('&') : ''
    const url = `/api/v2/logs/${logid}/contents${qsstr}`
    return (await fetchData(config, url)).logchunks
}

export async function getStepLogs(config: Config, id: number): Promise<Log[]> {
    return (await fetchData(config, `/api/v2/steps/${id}/logs`)).logs
}

export async function getBuilderNames(
    config: Config,
    builder_ids: number[],
): Promise<Map<number, string>> {
    const non_existing_ids = builder_ids.filter((it) => !builderNameCache.has(it))
    await getBuilders(config, non_existing_ids)
    const result = new Map()
    for (const it of builder_ids) {
        result.set(it, builderNameCache.get(it) ?? 'unknown')
    }
    return result
}

export async function getBuilderName(config: Config, id: number): Promise<string> {
    return (await getBuilderNames(config, [id])).get(id)!
}

export async function getBuilders(config: Config, builder_ids: number[]): Promise<Builder[]> {
    if (!builder_ids.length) {
        return []
    }
    const data = await fetchData(config, `/api/v2/builders?builderids=${builder_ids.join(',')}`)
    for (const it of data.builders) {
        builderNameCache.set(it.builderid, it.name)
    }
    return data.builders
}

export function urlQuery(data: Record<string, unknown>): string {
    const result = []
    for (const k in data) {
        const val = data[k]
        if (val) {
            if (Array.isArray(val)) {
                for (const it of val) {
                    result.push(`${k}=${it}`)
                }
            } else {
                result.push(`${k}=${val}`)
            }
        }
    }
    return result.join('&')
}

export async function getBuildsByRequest(
    config: Config,
    reqids: number[],
    settings?: { properties: string[] },
): Promise<Build[]> {
    if (!reqids.length) {
        return []
    }
    const props = settings && settings.properties
    const url = '/api/v2/builds?' + urlQuery({ reqids: reqids.join(','), property: props })
    return (await fetchData(config, url)).builds ?? []
}

export async function getBuildSteps(config: Config, id: number): Promise<Step[]> {
    return (await fetchData(config, `/api/v2/builds/${id}/steps`)).steps
}

export async function getBuildProperties(config: Config, id: number): Promise<Properties> {
    return (await fetchData(config, `/api/v2/builds/${id}/properties`)).properties[0] || {}
}

export async function getBuildChanges(config: Config, id: number): Promise<Change[]> {
    return (await fetchData(config, `/api/v2/builds/${id}/changes`)).changes
}

export async function getChangesBySSID(config: Config, id: number): Promise<Change[]> {
    return (await fetchData(config, `/api/v2/sourcestamps/${id}/changes`)).changes
}

export async function getChangeBuilds(config: Config, id: number): Promise<Build[]> {
    return (await fetchData(config, `/api/v2/changes/${id}/builds`)).builds
}

export async function getRelatedBuilds(config: Config, buildid: number): Promise<Build[]> {
    const url = `/api/v2/builds?relatedfor=${buildid}`
    return (await fetchData(config, url)).builds || []
}

export async function getBuildByNumber(
    config: Config,
    builderid: number,
    number: number,
): Promise<Build | null> {
    const url = `/api/v2/builders/${builderid}/builds/${number}`
    return (await fetchData(config, url)).builds[0] || null
}

export async function getRequests(config: Config, reqids: number[]): Promise<BuildRequest[]> {
    if (!reqids.length) {
        return []
    }
    const url = `/api/v2/buildrequests?reqids=${reqids.join(',')}`
    return (await fetchData(config, url))?.buildrequests ?? []
}

export async function getBuildset(config: Config, id: number): Promise<BuildSet | null> {
    const url = `/api/v2/buildsets/${id}`
    return (await fetchData(config, url)).buildsets[0] ?? null
}

export async function getBuild(config: Config, id: number): Promise<Build | null> {
    return (await fetchData(config, `/api/v2/builds/${id}`)).builds[0] || null
}
