<script setup>
import { inject, ref, onMounted } from 'vue'
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

onMounted(() => getData())
</script>

<template>
<table class="pure-table pure-table-horizntal pure-table-striped">
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
</template>
