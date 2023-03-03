<script setup>
import { inject, ref, onMounted, nextTick } from 'vue'
import {getLogContent} from '../data'

const config = inject('config')
const props = defineProps(['log'])
const content = ref([])
const el = ref(null)

async function getData() {
    const log = props.log
    if (log.type == 'h') {
        const chunks = await getLogContent(config, log.logid)
        const result = chunks.map(it => it.content)
        content.value = result.join('')
        return
    }
    const chunks = await getLogContent(config, log.logid, Math.max(0, log.num_lines-config.log_limit), config.log_limit)
    const result = []
    const ws = /\r?\n/
    for (var it of chunks) {
        for (var line of it.content.split(ws)) {
            if (log.type == 's') {
                result.push([line[0], line.slice(1) + '\n'])
            } else {
                result.push(['o', line + '\n'])
            }
        }
    }
    if (result.length) {
        result[result.length-1] = result[result.length-1].slice(0, -1)
    }
    content.value = result

    await nextTick()
    el.value.scrollTop = el.value.scrollHeight
}

onMounted(() => getData())
</script>

<template>
    <div class="log-content" v-if="props.log.type == 'h'" v-html="content" />
    <pre v-else class="log-content" ref="el"><template v-for="line in content"><span :class="`line-${line[0]}`">{{ line[1] }}</span></template></pre>
</template>

<style>
.log-content {
    padding: 0.5em 0.6em;
    max-height: 50vh;
    overflow: auto;
    margin: 0;
    border-color: #ddd;
    border-radius: 0 0 3px 3px;
    border-width: 1px;
    border-style: solid;
    border-top: 0;
}

pre.log-content {
    background-color: #fcfcfc;
    line-height: 1.3;
    font-size: 90%;
    color: #222;
}

.line-e {
    color: #ff4c33;
}

.line-h {
    color: #00aa95;
}
</style>
