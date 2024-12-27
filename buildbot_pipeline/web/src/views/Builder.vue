<script setup lang="ts">
import { ref } from 'vue'
import Loader from '../components/Loader.vue'
import { fetchData } from '../api'
import { fmtDuration, fmtAge, resultClass } from '../utils'
import { type Build } from '../types'

const props = defineProps<{ id: number }>()
const builds = ref<Build[]>([])

async function getData() {
    const url = `/api/v2/builders/${props.id}/builds?limit=100&order=-number&property=owners&property=workername`
    const data = await fetchData(url)
    builds.value = data.builds || []
}

async function loadMore() {
    const blist = builds.value
    const last_num = blist[blist.length - 1].number
    const url = `/api/v2/builders/${props.id}/builds?limit=100&order=-number&number__lt=${last_num}&property=owners&property=workername`
    const data = await fetchData(url)
    builds.value = blist.concat(data.builds)
}

const load = getData()
</script>

<template>
    <Loader :wait="load">
        <table role="grid">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Started</th>
                    <th>Duration</th>
                    <th>Owners</th>
                    <th>Worker</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="build in builds" :key="build.buildid">
                    <td>
                        <router-link
                            :to="{
                                name: 'build',
                                params: { builderid: props.id, number: build.number },
                            }"
                            :class="`badge ${resultClass(build)}`"
                        >
                            {{ build.number }}
                        </router-link>
                    </td>
                    <td class="nowrap">{{ fmtAge(build.started_at) }}</td>
                    <td>{{ fmtDuration(build) }}</td>
                    <td>{{ (build.properties.owners?.[0] || []).join(', ') }}</td>
                    <td>{{ build.properties.workername?.[0] }}</td>
                    <td>{{ build.state_string }}</td>
                </tr>
            </tbody>
        </table>
        <span class="secondary" role="button" @click="loadMore">More...</span>
    </Loader>
</template>
