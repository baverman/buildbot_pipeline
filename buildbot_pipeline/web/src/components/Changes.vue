<script setup lang="ts">
import { inject, ref } from 'vue'
import Loader from './Loader.vue'
import { getChangesBySSID, type Config } from '../api'
import { type Change, type BuildSet } from '../types'

const config = inject('config') as Config
const props = defineProps<{ buildset: BuildSet }>()
const buildset = props.buildset
const changes = ref<Change[]>([])

async function getData() {
    const plist = buildset.sourcestamps.map((it) => getChangesBySSID(config, it.ssid))
    const cl = await Promise.all(plist)
    const result = []
    for (const it of cl) {
        for (const c of it) {
            result.push(c)
        }
    }

    changes.value = result
}

const load = getData()
</script>

<template>
    <Loader :wait="load">
        <div class="vspacer" v-for="change in changes" :key="change.changeid">
            <div style="line-height: 130%">
                <a :href="change.revlink">{{ change.author }}</a>
                <pre>{{ change.comments }}</pre>
                Branch: {{ change.branch }}<br />
                Revision: {{ change.revision }}<br />
                Files:
                <ul>
                    <li v-for="fname in change.files" :key="fname">{{ fname }}</li>
                </ul>
            </div>
        </div>
    </Loader>
</template>
