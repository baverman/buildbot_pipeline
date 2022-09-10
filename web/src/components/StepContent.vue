<script setup>
import { inject, ref, onMounted } from 'vue'
import {getStepLogs, parseStepUrls, getBuildsByNumber, getRequests, getBuilderNames, getBuildsByRequest} from '../data'
import Log from './Log.vue'
import Build from './Build.vue'

const config = inject('config')
const props = defineProps(['step'])
const step = props.step
const logs = ref([])

const request_urls = ref([])
const builds = ref([])
const other_urls = ref([])

async function getData() {
    logs.value = await getStepLogs(config, step.stepid)
    const data = parseStepUrls(step.urls)
    other_urls.value = data.other

    await getBuilderNames(config, data.builds.map(it => it.builderid))
    // builds.value = await getBuildsByNumber(config, data.builds.map(it => it.bnum))
    builds.value = await getBuildsByRequest(config, data.requests.map(it => it.reqid))
    const claimed_requests = new Map(builds.value.map(it => [it.buildrequestid, 1]))
    request_urls.value = data.requests.filter(it => !claimed_requests.has(it.reqid))

    const breqs = await getRequests(config, request_urls.value.map(it => it.reqid))
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
