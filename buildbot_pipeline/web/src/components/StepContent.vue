<script setup lang="ts">
import { ref } from 'vue'
import * as api from '../api'
import Log from './Log.vue'
import Build from './Build.vue'
import Loader from './Loader.vue'
import { parseStepUrls, type RequestUrl, type BuildUrl } from '../utils'
import { type Log as LogT, type StepUrl, type Build as BuildT, type Step } from '../types'

const props = defineProps<{ step: Step }>()
const logs = ref<LogT[]>([])

const data_builds = ref<BuildUrl[]>([])
const data_requests = ref<RequestUrl[]>([])
const request_urls = ref<RequestUrl[]>([])
const builds = ref<BuildT[]>([])
const other_urls = ref<StepUrl[]>([])

async function getData() {
    logs.value = await api.getStepLogs(props.step.stepid)
    const data = parseStepUrls(props.step.urls)
    data_builds.value = data.builds
    data_requests.value = data.requests
    other_urls.value = data.other
    await poll()
}

function hasUncompletedBuilds(builds: BuildT[]) {
    return builds.length && builds.filter((it) => it.results == null).length
}

async function poll() {
    await api.getBuilderNames(data_builds.value.map((it) => it.builderid))
    builds.value = await api.getBuildsByRequest(
        data_requests.value.map((it) => it.reqid),
        { properties: ['virtual_builder_title'] },
    )
    const claimed_requests = new Map(builds.value.map((it) => [it.buildrequestid, 1]))
    request_urls.value = data_requests.value.filter((it) => !claimed_requests.has(it.reqid))

    if (request_urls.value.length || hasUncompletedBuilds(builds.value)) {
        setTimeout(poll, 10000)
    }
}

const load = getData()
</script>

<template>
    <Loader :wait="load">
        <div class="vspacer">
            <ul v-if="other_urls.length">
                <li v-for="(url, index) in other_urls" :key="index">
                    <a :href="url.url">{{ url.name }}</a>
                </li>
            </ul>
            <div v-if="logs.length" class="vspacer">
                <Log v-for="log in logs" :key="log.logid" :log="log" />
            </div>
            <div v-for="(url, index) in request_urls" :key="index">{{ url }}</div>
            <Build v-for="it in builds" :key="it.buildid" :build="it" />
        </div>
    </Loader>
</template>
