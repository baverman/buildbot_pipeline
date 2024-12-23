import { type StepUrl } from './types'

const BUILDREQUEST_RE = /#\/?buildrequests\/(\d+)$/
const BUILDNUM_RE = /#\/?builders\/(\d+)\/builds\/(\d+)$/
export const RESULTS = [
    'success',
    'warnings',
    'failure',
    'skipped',
    'exception',
    'retry',
    'cancelled',
    'unknown',
]

export function divmod(x: number, y: number): [number, number] {
    x = x | 0
    const reminder = x % y
    return [(x - reminder) / y, reminder]
}

export function pad2(num: number): string {
    const s = num.toString()
    if (s.length < 2) {
        return '0' + s
    }
    return s
}

export function fmtDuration(item: {
    complete: boolean
    complete_at: number
    started_at: number
}): string {
    let dur
    if (item.complete) {
        dur = item.complete_at - item.started_at
    } else {
        dur = Math.round(new Date().getTime() / 1000 - item.started_at)
    }
    if (dur < 60) {
        return `${dur}s`
    }
    const [_m, s] = divmod(dur, 60)
    const [h, m] = divmod(_m, 60)
    if (h > 0) {
        return `${h}:${pad2(m)}:${pad2(s)}`
    }
    return `${m}:${pad2(s)}`
}

export function fmtAge(start: number): string {
    const now = (new Date().getTime() / 1000) | 0
    const delta = Math.round(now - start)
    if (delta < 5) {
        return 'a moment ago'
    } else if (delta < 120) {
        return `${delta}s ago`
    } else if (delta < 3600) {
        return `${(delta / 60) | 0}m ago`
    } else if (delta < 86400) {
        return `${(delta / 3600) | 0}h ago`
    }

    const d = new Date(start * 1000)
    if (delta < 86400 * 30) {
        return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())} ${pad2(d.getHours())}:${pad2(d.getMinutes())}`
    }
    return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

export function buildLink(build: { builderid: number; number: number }): Record<string, unknown> {
    return { name: 'build', params: { builderid: build.builderid, number: build.number } }
}

export function resultClass(obj: { results: number | null }, no_pulse: boolean = false): string {
    let num = obj.results
    let add = ''
    if (num == null) {
        num = 99
        if (!no_pulse) {
            add = ' pulse'
        }
    }
    return `results_${num}${add}`
}

export interface RequestUrl extends StepUrl {
    reqid: number
}

export interface BuildUrl extends StepUrl {
    bnum: string
    builderid: number
    number: number
}

export function parseStepUrls(urls: StepUrl[]) {
    const requests: RequestUrl[] = []
    const builds: BuildUrl[] = []
    const other: StepUrl[] = []
    for (const it of urls) {
        if (it.name == 'Last successful build') {
            other.push(it)
            continue
        }
        if (it.url.includes('buildrequests/')) {
            const m = it.url.match(BUILDREQUEST_RE)
            if (m !== null) {
                const req = it as RequestUrl
                req.reqid = parseInt(m[1])
                requests.push(req)
                continue
            }
        } else if (it.url.includes('builders/')) {
            const m = it.url.match(BUILDNUM_RE)
            if (m !== null) {
                const b = it as BuildUrl
                b.bnum = m[1] + '-' + m[2]
                b.builderid = parseInt(m[1])
                b.number = parseInt(m[2])
                builds.push(b)
                continue
            }
        }
        if (it.url.startsWith('file-store/')) {
            it.url = '/' + it.url
        }
        other.push(it)
    }
    return { requests, builds, other }
}

export function resultTitle(obj: { results: number | null }): string {
    if (obj.results == null) {
        return 'in progress'
    }
    return RESULTS[obj.results] ?? 'unknown'
}
