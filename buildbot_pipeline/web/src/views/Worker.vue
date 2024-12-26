<script setup lang="ts">
import { inject, ref } from 'vue'
import Loader from '../components/Loader.vue'
import { type Worker } from '../types'
import * as api from '../api'

const config = inject('config') as api.Config
const props = defineProps<{ id: number }>()

const worker = ref<Worker | null>(null)
const reason = ref('')

async function getData() {
    worker.value = await api.getWorker(config, props.id)
    if (!worker.value) {
        throw new api.AppError('Worker not found')
    }
}

async function action(method: string) {
    await api.sendRPC(config, `/workers/${props.id}`, method, { reason: reason.value })
    worker.value = await api.getWorker(config, props.id)
}

const load = getData()
</script>

<template>
    <Loader :wait="load">
        <div v-if="worker" class="content">
            <textarea v-model="reason" placeholder="Reason" rows="10" cols="60" />
            <button
                class="w-inline"
                @click="action('stop')"
                :disabled="!worker.connected_to.length"
            >
                Shutdown</button
            >&nbsp;
            <button
                class="w-inline"
                @click="action('kill')"
                :disabled="!worker.connected_to.length"
            >
                Force shutdown</button
            >&nbsp;
            <button class="w-inline" @click="action('pause')" :disabled="worker.paused">
                Pause</button
            >&nbsp;
            <button class="w-inline" @click="action('unpause')" :disabled="!worker.paused">
                Unpause
            </button>
        </div>
    </Loader>
</template>
