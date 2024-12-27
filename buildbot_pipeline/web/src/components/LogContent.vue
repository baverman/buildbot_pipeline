<script setup lang="ts">
import { inject, ref, onMounted, nextTick } from 'vue'
import { getLogContent, type Config } from '../api'
import { type Log } from '../types'

const config = inject('config') as Config
const props = defineProps<{ log: Log }>()
const hcontent = ref('')
const content = ref<[string, string][]>([])
const el = ref<HTMLPreElement | null>(null)

async function getData() {
    const log = props.log
    if (log.type == 'h') {
        const chunks = await getLogContent(log.logid)
        const result = chunks.map((it) => it.content)
        hcontent.value = result.join('')
        return
    }
    const chunks = await getLogContent(
        log.logid,
        Math.max(0, log.num_lines - config.log_limit),
        config.log_limit,
    )
    const result: [string, string][] = []
    const ws = /\r?\n/
    for (const it of chunks) {
        for (const line of it.content.split(ws)) {
            if (log.type == 's') {
                if (line.length) {
                    result.push([line[0], line.slice(1) + '\n'])
                }
            } else {
                result.push(['o', line + '\n'])
            }
        }
    }
    content.value = result

    await nextTick()
    if (el.value) {
        el.value.scrollTop = el.value.scrollHeight
    }
}

onMounted(() => getData())
</script>

<template>
    <div class="log-content" v-if="props.log.type == 'h'" v-html="hcontent" />
    <pre
        v-else
        class="log-content"
        ref="el"
    ><template v-for="(line, index) in content" :key="index"><span :class="`line-${line[0]}`">{{ line[1] }}</span></template></pre>
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
