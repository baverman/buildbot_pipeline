<script setup lang="ts">
import { inject, ref } from 'vue'
import { useRouter } from 'vue-router'

import StepList from '../components/StepList.vue'
import Properties from '../components/Properties.vue'
import Changes from '../components/Changes.vue'
import RelBuilds from '../components/RelBuilds.vue'
import Loader from '../components/Loader.vue'

import * as api from '../api'
import { type Build, type BuildSet } from '../types'
import { fmtDuration, fmtAge, buildLink, resultClass, resultTitle } from '../utils'

interface Data {
    build: Build
    parent_build?: Build
    parent_builder_name?: string
    buildset: BuildSet
    workername: string
}

const router = useRouter()
const config = inject('config') as api.Config

const props = defineProps<{ builderid: number; number: number; tab?: string }>()
const tab = ref(props.tab ?? 'steps')

const data = ref<Data | null>(null)

async function getData() {
    const b = await api.getBuildByNumber(config, props.builderid, props.number)
    if (!b) {
        throw new api.AppError('Build not found')
    }

    const [breqs, w] = await Promise.all([
        api.getRequests(config, [b.buildrequestid]),
        api.getWorker(config, b.workerid),
    ])
    const breq = breqs[0]
    const bs = (await api.getBuildset(config, breq.buildsetid))!
    let pb = undefined
    let parent_builder_name = undefined
    if (bs.parent_buildid) {
        pb = (await api.getBuild(config, bs.parent_buildid))!
        parent_builder_name = await api.getBuilderName(config, pb.builderid)
    }
    data.value = {
        build: b,
        buildset: bs,
        parent_build: pb,
        parent_builder_name: parent_builder_name,
        workername: w?.name ?? 'unknown', // TODO workername cache
    }
    setTimeout(poll, 5000)
}

async function poll() {
    if (!data.value || data.value.build.results != null) {
        return
    }
    data.value.build = (await api.getBuildByNumber(config, props.builderid, props.number))!
    setTimeout(poll, 5000)
}

function changeTab(newTab: string) {
    if (data.value) {
        const lnk = buildLink(data.value.build)
        lnk.query = { tab: newTab }
        router.replace(lnk)
        tab.value = newTab
    }
}

async function rebuild() {
    const build = data.value!.build
    const result = await api.sendBuildAction(config, build.buildid, 'rebuild')
    const breq = result.result.length && Object.values(result.result[1])[0]
    if (breq) {
        for (let i = 0; i < 10; i++) {
            await new Promise((r) => setTimeout(r, 300))
            const builds = await api.getBuildsByRequest(config, [breq])
            if (builds.length) {
                router.push(buildLink(builds[0]))
                return
            }
        }
    }
    const lnk = { name: 'builder', params: { id: build.builderid } }
    router.push(lnk)
}

async function stop() {
    await api.sendBuildAction(config, data.value!.build.buildid, 'stop')
}

const load = getData()
</script>

<template>
    <Loader :wait="load">
        <div v-if="data" class="vspacer">
            <div>
                <span :class="`badge-text ${resultClass(data.build, true)}`">{{
                    resultTitle(data.build).toUpperCase()
                }}</span>
                in {{ fmtDuration(data.build) }}. Started {{ fmtAge(data.build.started_at) }} on
                {{ data.workername }}.
                <template v-if="data.parent_build">
                    Parent:
                    <router-link :to="buildLink(data.parent_build)"
                        >{{ data.parent_builder_name }}/{{ data.parent_build.number }}</router-link
                    > </template
                ><!--
                -->&nbsp;&nbsp;<button
                    v-if="data.build.results != null"
                    class="w-inline"
                    @click="rebuild"
                >
                    Rebuild
                </button>
                <button v-else class="w-inline" @click="stop">Stop</button>
            </div>
            <div>{{ data.build.state_string }}</div>
            <nav class="tab">
                <ul>
                    <li :class="{ active: tab == 'steps' }">
                        <a @click="changeTab('steps')" class="contrast">Steps</a>
                    </li>
                    <li :class="{ active: tab == 'props' }">
                        <a @click="changeTab('props')" class="contrast">Properties</a>
                    </li>
                    <li :class="{ active: tab == 'changes' }">
                        <a @click="changeTab('changes')" class="contrast">Changes</a>
                    </li>
                    <li :class="{ active: tab == 'relbuilds' }">
                        <a @click="changeTab('relbuilds')" class="contrast">Related builds</a>
                    </li>
                </ul>
            </nav>
            <div>
                <KeepAlive>
                    <StepList v-if="tab == 'steps'" :build="data.build" :filter-steps="2" />
                    <Properties v-else-if="tab == 'props'" :build="data.build" />
                    <Changes v-else-if="tab == 'changes'" :buildset="data.buildset" />
                    <RelBuilds v-else-if="tab == 'relbuilds'" :build="data.build" />
                </KeepAlive>
            </div>
        </div>
    </Loader>
</template>

<style scoped>
nav.tab a {
    --nav-link-spacing-vertical: 0.2rem;
    border-radius: 0;
    cursor: pointer;
    border-bottom: 3px transparent solid;
}

nav.tab li.active a {
    border-bottom: 3px gray solid;
    font-weight: bolder;
}

nav.tab li {
    --nav-element-spacing-vertical: 0.5rem;
}
</style>
