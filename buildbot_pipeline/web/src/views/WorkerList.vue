<script setup>
import { inject, ref } from 'vue'
import Loader from '../components/Loader.vue'
import * as data from '../data'
const config = inject('config')

const workers = ref(null)

async function getData() {
    workers.value = await data.getWorkers(config)
}

function getState(worker) {
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
        <tr v-for="worker in workers">
            <td>{{ getState(worker) }}</td>
            <td><router-link :to="{name: 'worker', params: {id: worker.workerid}}">{{ worker.name }}</router-link></td>
            <td>{{ worker.workerinfo.admin }}</td>
            <td>{{ worker.workerinfo.host }}</td>
            <td>{{ worker.workerinfo.version }}</td>
        </tr>
    </tbody>
    </table>
</Loader>
</template>
