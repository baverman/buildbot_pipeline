<script setup>
import { inject, ref } from 'vue'
import Loader from '../components/Loader.vue'
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

const load = getData()
</script>

<template>
    <Loader :wait="load">
        <div class="content">
            <textarea v-model="reason" placeholder="Reason" rows=10 cols=60 />
            <button class="w-inline" @click="action('stop')" :disabled="!worker.connected_to.length">Shutdown</button>&nbsp;
            <button class="w-inline" @click="action('kill')" :disabled="!worker.connected_to.length">Force shutdown</button>&nbsp;
            <button class="w-inline" @click="action('pause')" :disabled="worker.paused">Pause</button>&nbsp;
            <button class="w-inline" @click="action('unpause')" :disabled="!worker.paused">Unpause</button>
        </div>
    </Loader>
</template>
