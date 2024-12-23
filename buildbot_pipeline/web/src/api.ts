import { type Worker, type Builder, type Build, type Log, type LogChunk } from './types'

const builderNameCache = new Map<number, string>()

export interface Config {
    backend: string
    log_limit: number
}

export async function fetchData(config: Config, url: string) {
    const resp = await fetch(config.backend + url, {
        'headers': {'Accept': 'application/json'},
    })
    return await resp.json()
}

export async function sendRPC(config: Config, url: string, action: string, params: any) {
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

export async function getWorkers(config: Config): Promise<Worker[]> {
    const data = await fetchData(config, `/api/v2/workers?order=name`)
    return data.workers
}

export async function getWorker(config: Config, id: number | string): Promise<Worker | null> {
    return (await fetchData(config, `/api/v2/workers/${id}`))?.workers[0]
}

export async function getAllBuilders(config: Config): Promise<Builder[]> {
    const data = await fetchData(config, '/api/v2/builders?order=name')
    for (var it of data.builders) {
        builderNameCache.set(it.builderid, it.name)
    }
    return data.builders
}

export async function getBuilderBuilds(config: Config, builder_ids: number[]): Promise<Build[]> {
    if (!builder_ids.length) {
        return []
    }
    const data = await fetchData(config, `/api/v2/builds?builderids=${builder_ids.join(',')}&order=-buildid&limit=300`)
    return data.builds
}

export async function getLogContent(config: Config, logid: number, offset?: number, limit?: number): Promise<LogChunk[]> {
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

export async function getStepLogs(config: Config, id: number): Promise<Log[]> {
    return (await fetchData(config, `/api/v2/steps/${id}/logs`)).logs
}

export async function getBuilderNames(config: Config, builder_ids: number[]): Promise<Map<number, string>> {
    const non_existing_ids = builder_ids.filter(it => !builderNameCache.has(it))
    await getBuilders(config, non_existing_ids)
    const result = new Map()
    for (var it of builder_ids) {
        result.set(it, builderNameCache.get(it) ?? 'unknown')
    }
    return result
}

export async function getBuilders(config: Config, builder_ids: number[]): Promise<Builder[]> {
    if (!builder_ids.length) {
        return []
    }
    const data = await fetchData(config, `/api/v2/builders?builderids=${builder_ids.join(',')}`)
    for (var it of data.builders) {
        builderNameCache.set(it.builderid, it.name)
    }
    return data.builders
}

export function urlQuery(data: Record<string, any>): string {
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

export async function getBuildsByRequest(config: Config, reqids: number[], settings?: {properties: string[]}): Promise<Build[]> {
    if (!reqids.length) {
        return []
    }
    const props = settings && settings.properties
    const url = '/api/v2/builds?' + urlQuery({reqids: reqids.join(','), property: props})
    return (await fetchData(config, url)).builds ?? []
}
