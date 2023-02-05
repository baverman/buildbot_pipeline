<script setup>
import { inject, ref, onMounted } from 'vue'
import {getStepLogs, parseStepUrls, getBuildsByNumber, getRequests, getBuilderNames, getBuildsByRequest} from '../data'
import Log from './Log.vue'
import Build from './Build.vue'

const config = inject('config')
const props = defineProps(['step'])
const logs = ref([])

const data_builds = ref([])
const data_requests = ref([])
const request_urls = ref([])
const builds = ref([])
const other_urls = ref([])

async function getData() {
    logs.value = await getStepLogs(config, props.step.stepid)
    const data = parseStepUrls(props.step.urls)
    data_builds.value = data.builds
    data_requests.value = data.requests
    other_urls.value = data.other
    await poll()
}

function hasUncompletedBuilds(builds) {
    return builds.length && builds.filter(it => it.results == null).length
}

async function poll() {
    await getBuilderNames(config, data_builds.value.map(it => it.builderid))
    builds.value = await getBuildsByRequest(config, data_requests.value.map(it => it.reqid),
                                            {'properties': ['virtual_builder_title']})
    const claimed_requests = new Map(builds.value.map(it => [it.buildrequestid, 1]))
    request_urls.value = data_requests.value.filter(it => !claimed_requests.has(it.reqid))

    if (request_urls.value.length || hasUncompletedBuilds(builds.value)) {
        setTimeout(poll, 10000)
    }
}

onMounted(() => getData())
</script>

<template>
    <div class="vspacer">
        <ul v-if="other_urls.length">
            <li v-for="url in other_urls"><a :href="url.url">{{ url.name }}</a></li>
        </ul>
        <div v-if="logs.length" class="vspacer">
            <Log v-for="log in logs" :key="log.logid" :log="log" />
        </div>
        <div v-for="url in request_urls">{{ url }}</div>
        <Build v-for="it in builds" :key="it.buildid" :build="it" />
    </div>
</template>
