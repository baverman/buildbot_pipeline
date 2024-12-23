export interface Worker {
    graceful: boolean
    name: string
    paused: boolean
    workerid: number
    connected_to: {
        masterid: number,
    }[]
    workerinfo: {
        access_uri: string | null,
        admin: string | null,
        host: string | null,
        version: string,
    }
}

export interface Builder {
    builderid: number
    description: string | null
    description_format: string | null
    description_html: string | null
    masterids: number[]
    name: string
    tags: string[]
}

interface Properties {
    owners?: [string[], string]
    workername?: [string, string]
}

export interface Build {
    builderid: number
    buildid: number
    buildrequestid: number
    complete: boolean
    complete_at: number
    masterid: number
    number: number
    properties: Properties
    results: number
    started_at: number
    state_string: string
    workerid: number
}

export interface Log {
    logid: number
    complete: boolean
    name: string
    num_lines: number
    slug: string
    stepid: number
    type: string
}

export interface LogChunk {
    content: string
    firstline: number
    logid: number
}

export interface StepUrl {
    name: string
    url: string
}

export interface Step {
    buildid: number
    complete: boolean
    complete_at: number
    hidden: boolean
    name: string
    number: number
    results: number
    started_at: number
    state_string: string
    stepid: number
    urls: StepUrl[]
}
