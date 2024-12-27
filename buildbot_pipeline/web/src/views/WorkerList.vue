<script setup lang="ts">
import { ref } from 'vue'
import Loader from '../components/Loader.vue'
import * as api from '../api'
import { type Worker } from '../types'

const workers = ref<Worker[] | null>(null)

async function getData() {
    workers.value = await api.getWorkers()
}

function getState(worker: Worker): string {
    if (worker.connected_to.length) {
        if (worker.paused) {
            return 'paused'
        } else {
            return 'ok'
        }
    } else {
        return 'stopped'
    }
}

const load = getData()
</script>

<template>
    <Loader :wait="load">
        <table>
            <thead>
                <tr>
                    <th>State</th>
                    <th>Name</th>
                    <th>Admin</th>
                    <th>Host</th>
                    <th>Version</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="worker in workers" :key="worker.workerid">
                    <td>{{ getState(worker) }}</td>
                    <td>
                        <router-link :to="{ name: 'worker', params: { id: worker.workerid } }">{{
                            worker.name
                        }}</router-link>
                    </td>
                    <td>{{ worker.workerinfo.admin }}</td>
                    <td>{{ worker.workerinfo.host }}</td>
                    <td>{{ worker.workerinfo.version }}</td>
                </tr>
            </tbody>
        </table>
    </Loader>
</template>
