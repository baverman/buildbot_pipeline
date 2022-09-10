export function divmod(x, y) {
    x = x | 0
    const reminder = x % y
    return [(x - reminder) / y, reminder]
}

export function pad2(num) {
    const s = num.toString()
    if (s.length < 2) {
        return '0' + s
    }
    return s
}

export function fmtDuration(item) {
    var dur
    if (item.complete) {
        dur = item.complete_at - item.started_at
    } else {
        dur = new Date().getTime() / 1000 - item.started_at
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

export function fmtAge(start) {
    const now = new Date().getTime() / 1000 | 0
    const delta = now - start
    if (delta < 5) {
        return 'a moment ago'
    } else if (delta < 300) {
        return `${delta}s ago`
    } else if (delta < 3600) {
        return `${delta / 60 | 0}m ago`
    } else if (delta < 86400) {
        return `${delta / 3600 | 0}h ago`
    }

    const d = new Date(start * 1000)
    if (delta < 86400 * 30) {
        return `${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())} ${pad2(d.getHours())}:${pad2(d.getMinutes())}`
    }
    return `${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}`
}

export function buildLink(build) {
    return {name: 'build', params: {builderid: build.builderid, number: build.number}}
}
