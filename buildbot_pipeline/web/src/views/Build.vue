<script setup>
import { inject, ref } from 'vue'
import { useRouter } from 'vue-router'

import StepList from '../components/StepList.vue'
import Properties from '../components/Properties.vue'
import Changes from '../components/Changes.vue'
import RelBuilds from '../components/RelBuilds.vue'
import Loader from '../components/Loader.vue'

import {getBuildByNumber, getRequests, getBuildset, resultClass, resultTitle,
        getBuild, getBuilderName, getWorker, sendBuildAction, getBuildsByRequest} from '../data'
import {fmtDuration, fmtAge, buildLink} from '../utils'

const config = inject('config')
const build = ref(null)
const buildset = ref(null)
const props = defineProps(['builderid', 'number', 'tab'])
const parent_build = ref(null)
const tab = ref(props.tab || 'steps')
const router = useRouter()

async function getData() {
    const b = await getBuildByNumber(config, props.builderid, props.number)

    const [breqs, w] = await Promise.all([
        getRequests(config, [b.buildrequestid]),
        getWorker(config, b.workerid)
    ])
    b.workername = w.name
    const breq = breqs[0]
    const bs = await getBuildset(config, breq.buildsetid)
    if (bs.parent_buildid) {
        const pb = await getBuild(config, bs.parent_buildid)
        pb.builder_name = await getBuilderName(config, pb.builderid)
        parent_build.value = pb
    }
    build.value = b
    buildset.value = bs
    setTimeout(poll, 5000);
}

async function poll() {
    if (build.value && build.value.results != null) {
        return
    }
    const old_worker = build.value.workername
    const b = await getBuildByNumber(config, props.builderid, props.number)
    b.workername = old_worker
    build.value = b
    setTimeout(poll, 5000)
}

function changeTab(newTab) {
    const lnk = buildLink(build.value)
    lnk.query = {'tab': newTab}
    router.replace(lnk)
    tab.value = newTab
}

async function rebuild() {
    const result = await sendBuildAction(config, build.value.buildid, 'rebuild')
    const breq = result.result.length && Object.values(result.result[1])[0]
    if (breq) {
        for(var i=0; i<10; i++) {
            await new Promise(r => setTimeout(r, 300));
            const data = await getBuildsByRequest(config, [breq])
            if (data.length) {
                const build = data[0];
                router.push(buildLink(data[0]))
                return
            }
        }
    }
    const lnk = {name: 'builder', params: {id: build.value.builderid}}
    router.push(lnk)
}

async function stop() {
    await sendBuildAction(config, build.value.buildid, 'stop')
}

const load = getData()
</script>

<template>
    <Loader :wait="load">
        <div class="vspacer">
            <div>
                <span :class="`badge-text ${resultClass(build, true)}`">{{ resultTitle(build).toUpperCase() }}</span>
                in {{ fmtDuration(build) }}. Started {{ fmtAge(build.started_at) }} on {{ build.workername }}.
                <template v-if="parent_build">
                    Parent: <router-link :to="buildLink(parent_build)">{{ parent_build.builder_name }}/{{ parent_build.number }}</router-link>
                </template><!--
                -->&nbsp;&nbsp;<button v-if="build.results != null" class="w-inline" @click="rebuild">Rebuild</button>
                <button v-else class="w-inline" @click="stop">Stop</button>
            </div>
            <div>{{ build.state_string }}</div>
            <nav class="tab">
                <ul>
                    <li :class="{'active': tab == 'steps'}">
                        <a @click="changeTab('steps')" class="contrast">Steps</a>
                    </li>
                    <li :class="{'active': tab == 'props'}">
                        <a @click="changeTab('props')" class="contrast">Properties</a>
                    </li>
                    <li :class="{'active': tab == 'changes'}">
                        <a @click="changeTab('changes')" class="contrast">Changes</a>
                    </li>
                    <li :class="{'active': tab == 'relbuilds'}">
                        <a @click="changeTab('relbuilds')" class="contrast">Related builds</a>
                    </li>
                </ul>
            </nav>
            <div>
            <KeepAlive>
                <StepList v-if="tab == 'steps'" :build="build" :filter-steps="2" />
                <Properties v-else-if="tab == 'props'" :build="build" />
                <Changes v-else-if="tab == 'changes'" :build="build" :buildset="buildset" />
                <RelBuilds v-else-if="tab == 'relbuilds'" :build="build" :buildset="buildset" />
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
