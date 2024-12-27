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

export class AppError extends Error {}

export interface Config {
    log_limit: number
}

export async function fetchData(url: string) {
    const resp = await fetch(url, {
        headers: { Accept: 'application/json' },
    })
    return await resp.json()
}

export async function sendRPC(url: string, action: string, params?: object) {
    const payload = JSON.stringify({
        id: url,
        jsonrpc: '2.0',
        method: action,
        params: params ?? {},
    })
    const resp = await fetch('/api/v2' + url, {
        method: 'POST',
        body: payload,
        headers: { 'Content-Type': 'application/json' },
    })
    return await resp.json()
}

export async function sendBuildAction(buildid: number, action: string) {
    return await sendRPC(`/builds/${buildid}`, action)
}

export async function getWorkers(): Promise<Worker[]> {
    const data = await fetchData('/api/v2/workers?order=name')
    return data.workers
}

export async function getWorker(id: number): Promise<Worker | null> {
    return (await fetchData(`/api/v2/workers/${id}`))?.workers?.[0] ?? null
}

export async function getAllBuilders(): Promise<Builder[]> {
    const data = await fetchData('/api/v2/builders?order=name')
    for (const it of data.builders) {
        builderNameCache.set(it.builderid, it.name)
    }
    return data.builders
}

export async function getBuilderBuilds(builder_ids: number[]): Promise<Build[]> {
    if (!builder_ids.length) {
        return []
    }
    const data = await fetchData(
        `/api/v2/builds?builderids=${builder_ids.join(',')}&order=-buildid&limit=300`,
    )
    return data.builds
}

export async function getLogContent(
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
    return (await fetchData(url)).logchunks
}

export async function getStepLogs(id: number): Promise<Log[]> {
    return (await fetchData(`/api/v2/steps/${id}/logs`)).logs
}

export async function getBuilderNames(builder_ids: number[]): Promise<Map<number, string>> {
    const non_existing_ids = builder_ids.filter((it) => !builderNameCache.has(it))
    await getBuilders(non_existing_ids)
    const result = new Map()
    for (const it of builder_ids) {
        result.set(it, builderNameCache.get(it) ?? 'unknown')
    }
    return result
}

export async function getBuilderName(id: number): Promise<string> {
    return (await getBuilderNames([id])).get(id)!
}

export async function getBuilders(builder_ids: number[]): Promise<Builder[]> {
    if (!builder_ids.length) {
        return []
    }
    const data = await fetchData(`/api/v2/builders?builderids=${builder_ids.join(',')}`)
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
    reqids: number[],
    settings?: { properties: string[] },
): Promise<Build[]> {
    if (!reqids.length) {
        return []
    }
    const props = settings && settings.properties
    const url = '/api/v2/builds?' + urlQuery({ reqids: reqids.join(','), property: props })
    return (await fetchData(url)).builds ?? []
}

export async function getBuildSteps(id: number): Promise<Step[]> {
    return (await fetchData(`/api/v2/builds/${id}/steps`)).steps
}

export async function getBuildProperties(id: number): Promise<Properties> {
    return (await fetchData(`/api/v2/builds/${id}/properties`)).properties[0] || {}
}

export async function getBuildChanges(id: number): Promise<Change[]> {
    return (await fetchData(`/api/v2/builds/${id}/changes`)).changes
}

export async function getChangesBySSID(id: number): Promise<Change[]> {
    return (await fetchData(`/api/v2/sourcestamps/${id}/changes`)).changes
}

export async function getChangeBuilds(id: number): Promise<Build[]> {
    return (await fetchData(`/api/v2/changes/${id}/builds`)).builds
}

export async function getRelatedBuilds(buildid: number): Promise<Build[]> {
    const url = `/api/v2/builds?relatedfor=${buildid}`
    return (await fetchData(url)).builds || []
}

export async function getBuild(id: number): Promise<Build | null> {
    return (await fetchData(`/api/v2/builds/${id}`)).builds[0] || null
}

export async function getBuildByNumber(builderid: number, number: number): Promise<Build | null> {
    const url = `/api/v2/builders/${builderid}/builds/${number}`
    return (await fetchData(url)).builds?.[0] ?? null
}

export async function getRequests(reqids: number[]): Promise<BuildRequest[]> {
    if (!reqids.length) {
        return []
    }
    const url = `/api/v2/buildrequests?reqids=${reqids.join(',')}`
    return (await fetchData(url))?.buildrequests ?? []
}

export async function getBuildset(id: number): Promise<BuildSet | null> {
    const url = `/api/v2/buildsets/${id}`
    return (await fetchData(url)).buildsets[0] ?? null
}
