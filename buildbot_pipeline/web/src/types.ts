export interface Worker {
    graceful: boolean
    name: string
    paused: boolean
    workerid: number
    connected_to: {
        masterid: number
    }[]
    workerinfo: {
        access_uri: string | null
        admin: string | null
        host: string | null
        version: string
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

type Property<T> = [T, string]

export interface Properties {
    [key: string]: Property<unknown>
}

export type KnownProperties = {
    owners?: Property<string[]>
    workername?: Property<string>
    virtual_builder_title?: Property<string>
} & Properties

export interface Build {
    builderid: number
    buildid: number
    buildrequestid: number
    complete: boolean
    complete_at: number
    masterid: number
    number: number
    properties: KnownProperties
    results: number | null
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
    results: number | null
    started_at: number
    state_string: string
    stepid: number
    urls: StepUrl[]
}

export interface Change {
    changeid: number
    author: string
    branch: string
    comments: string
    files: string[]
    revlink: string
    revision: string
}

export interface BuildSet {
    bsid: number
    complete: boolean
    complete_at: number
    external_idstring: string | null
    parent_buildid: number
    parent_relationship: string
    reason: string
    results: number
    sourcestamps: {
        branch: string
        codebase: string
        created_at: number
        patch: string | null
        project: string
        repository: string
        revision: string
        ssid: number
    }[]
    submitted_at: number
}

export interface BuildRequest {
    buildsetid: number
}
