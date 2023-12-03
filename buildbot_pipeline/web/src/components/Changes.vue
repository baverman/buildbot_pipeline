<script setup>
import { inject, ref } from 'vue'
import Loader from './Loader.vue'
import {getChangesBySSID, getChangeBuilds, getBuilders, resultClass} from '../data'

const config = inject('config')
const props = defineProps(['build', 'buildset'])
const build = props.build
const buildset = props.buildset
const changes = ref({})

async function getData() {
    var plist = buildset.sourcestamps.map(it => getChangesBySSID(config, it.ssid))
    const cl = await Promise.all(plist)
    const result = []
    for (var it of cl) {
        for (var c of it) {
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
            <p style="line-height:130%">
                <a :href="change.revlink">{{ change.author }}</a>
                <pre>{{ change.comments }}</pre>
                Branch: {{ change.branch }}<br>
                Revision: {{ change.revision }}<br>
                Files:
                <ul><li v-for="fname in change.files" :key="fname">{{ fname }}</li></ul>
            </p>
        </div>
    </Loader>
</template>
