<script setup>
import { inject, ref, onMounted, computed } from 'vue'
import {getChangesBySSID, getChangeBuilds, getBuilders, resultClass} from '../data'

const config = inject('config')
const props = defineProps(['build', 'buildset'])
const build = props.build
const buildset = props.buildset
const builders = ref([])
const builds = ref(new Map())

function showBuilder(it) {
    return it.builderid == build.builderid || it.masterids.length || (~it.tags.indexOf('_virtual_') && !~it.tags.indexOf('hidden'))
}

async function getData() {
    var plist = buildset.sourcestamps.map(it => getChangesBySSID(config, it.ssid))
    const cl = await Promise.all(plist)
    const result = []
    for (var it of cl) {
        for (var c of it) {
            result.push(c)
        }
    }

    plist = result.map(it => getChangeBuilds(config, it.changeid))
    const cbuilds = await Promise.all(plist)
    const b2b = new Map()
    for (var blist of cbuilds) {
        for (var b of blist) {
            if (b.buildid == build.buildid) {
                b.current = true
            }
            const k = b.builderid
            if (b2b.has(k)) {
                b2b.get(k).push(b)
            } else {
                b2b.set(k, [b])
            }
        }
    }

    builders.value = (await getBuilders(config, Array.from(b2b.keys()))).filter(showBuilder)
    builds.value = b2b
}

onMounted(() => getData())
</script>

<template>
    <table class="pure-table pure-table-horizntal pure-table-striped changes-history">
        <tr v-for="builder in builders">
            <td><router-link :to="{name: 'builder', params: {id: builder.builderid}}">{{ builder.name }}</router-link></td>
            <td style="line-height: 1.3">
                <template v-for="build in (builds.get(builder.builderid) || [])">
                    <router-link
                            :class="['badge', `${resultClass(build)}`, {'changes-current': build.current}]"
                            :to="{name: 'build', params: {builderid: builder.builderid, number: build.number}}">
                        {{ build.number }}
                    </router-link>&hairsp;
                </template>
            </td>
        </tr>
    </table>
</template>

<style>
.changes-current {
    font-weight: 700;
}

.changes-history td {
    font-size: 90%;
}
</style>
