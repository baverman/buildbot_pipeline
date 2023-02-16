<script setup>
import { inject, ref, onMounted } from 'vue'
import * as data from '../data'
const config = inject('config')
const props = defineProps(['id'])

const worker = ref(null)
const reason = ref('')

async function getData() {
    worker.value = await data.getWorker(config, props.id)
}

async function action(method) {
    await data.sendRPC(config, `/workers/${props.id}`, method, {'reason': reason.value})
    worker.value = await data.getWorker(config, props.id)
}

onMounted(() => getData())
</script>

<template>
    <template v-if="worker">
        <p>
            <textarea v-model="reason" placeholder="Reason" rows=10 cols=60 />
        </p>
        <button @click="action('stop')" :disabled="!worker.connected_to.length">Shutdown</button>&nbsp;
        <button @click="action('kill')" :disabled="!worker.connected_to.length">Force shutdown</button>&nbsp;
        <button @click="action('pause')" :disabled="worker.paused">Pause</button>&nbsp;
        <button @click="action('unpause')" :disabled="!worker.paused">Unpause</button>
    </template>
</template>
