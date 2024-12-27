<script setup lang="ts">
import { ref } from 'vue'
import { getRelatedBuilds, getBuilders } from '../api'
import { resultClass } from '../utils'
import { type Build, type Builder } from '../types'
import Loader from './Loader.vue'

const props = defineProps<{ build: Build }>()
const build = props.build
const builders = ref<Builder[]>([])
const builds = ref(new Map<number, Build[]>())

function showBuilder(it: Builder) {
    return (
        it.builderid == build.builderid ||
        it.masterids.length ||
        (~it.tags.indexOf('_virtual_') && !~it.tags.indexOf('hidden'))
    )
}

async function getData() {
    const cbuilds = await getRelatedBuilds(build.buildid)
    const b2b = new Map()
    for (const b of cbuilds) {
        const k = b.builderid
        if (b2b.has(k)) {
            b2b.get(k).push(b)
        } else {
            b2b.set(k, [b])
        }
    }

    builders.value = (await getBuilders(Array.from(b2b.keys()))).filter(showBuilder)
    builds.value = b2b
}

const load = getData()
</script>

<template>
    <Loader :wait="load">
        <table class="changes-history">
            <tr v-for="builder in builders" :key="builder.builderid">
                <td>
                    <router-link :to="{ name: 'builder', params: { id: builder.builderid } }">{{
                        builder.name
                    }}</router-link>
                </td>
                <td style="line-height: 1.3">
                    <template v-for="it in builds.get(builder.builderid) || []" :key="it.buildid">
                        <router-link
                            :class="[
                                'badge',
                                `${resultClass(it)}`,
                                { 'changes-current': it.buildid == build.buildid },
                            ]"
                            :to="{
                                name: 'build',
                                params: { builderid: builder.builderid, number: it.number },
                            }"
                        >
                            {{ it.number }} </router-link
                        >&hairsp;
                    </template>
                </td>
            </tr>
        </table>
    </Loader>
</template>

<style>
.changes-current {
    font-weight: 700;
}

.changes-history td {
    font-size: 90%;
}

.changes-history {
    width: auto;
}
</style>
