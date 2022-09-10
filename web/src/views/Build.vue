<script setup>
import { inject, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import StepList from '../components/StepList.vue'
import Properties from '../components/Properties.vue'
import Changes from '../components/Changes.vue'

import {getBuildByNumber, RESULTS, getRequests, getBuildset,
        getBuild, getBuilderName, getWorker} from '../data'
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
}

function changeTab(newTab) {
    const lnk = buildLink(build.value)
    lnk.query = {'tab': newTab}
    router.replace(lnk)
    tab.value = newTab
}

onMounted(() => getData())
</script>

<template>
    <template v-if="build">
        <div class="vspacer">
            <div>
                <span :class="`badge-text results_${build.results}`">{{ RESULTS[build.results].toUpperCase() }}</span>
                in {{ fmtDuration(build) }}. Started {{ fmtAge(build.started_at) }} on {{ build.workername }}.
                <template v-if="parent_build">
                    Parent: <router-link :to="buildLink(parent_build)">{{ parent_build.builder_name }}/{{ parent_build.number }}</router-link>
                </template>
            </div>
            <div>{{ build.state_string }}</div>
            <div class="pure-menu pure-menu-horizontal">
                <ul class="pure-menu-list">
                    <li :class="{'pure-menu-item': true, 'pure-menu-selected': tab == 'steps'}">
                        <a @click="changeTab('steps')" class="pure-menu-link">Steps</a>
                    </li>
                    <li :class="{'pure-menu-item': true, 'pure-menu-selected': tab == 'props'}">
                        <a @click="changeTab('props')" class="pure-menu-link">Properties</a>
                    </li>
                    <li :class="{'pure-menu-item': true, 'pure-menu-selected': tab == 'changes'}">
                        <a @click="changeTab('changes')" class="pure-menu-link">Changes</a>
                    </li>
                </ul>
            </div>
            <hr>
            <div>
            <KeepAlive>
                <StepList v-if="tab == 'steps'" :build="build" :filter-steps="2" />
                <Properties v-else-if="tab == 'props'" :build="build" />
                <Changes v-else-if="tab == 'changes'" :build="build" :buildset="buildset" />
            </KeepAlive>
            </div>
        </div>
    </template>
</template>

<style scoped>
.pure-menu-selected .pure-menu-link {
    border-bottom: 3px gray solid;
}

.pure-menu-link {
    cursor: pointer;
    border-bottom: 3px transparent solid;
}

</style>
