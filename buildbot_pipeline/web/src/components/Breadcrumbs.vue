<script setup>
import { inject, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import {getBuilderName, getWorker} from '../data'

const config = inject('config')
const router = useRouter()
const bc = ref([])

router.beforeEach(async (to, from) => {
    const result = [['Home', {name: 'index'}]]
    if (to.name == 'build') {
        const bname = await getBuilderName(config, parseInt(to.params.builderid))
        result.push([bname, {name: 'builder', params: {id: to.params.builderid}}])
        result.push([to.params.number, {name: 'build', params: to.params}])
    } else if (to.name == 'builder') {
        const bname = await getBuilderName(config, parseInt(to.params.id))
        result.push([bname, {name: 'builder', params: {id: to.params.id}}])
    } else if (to.name == 'workers' || to.name == 'index') {
        result.push(['Workers', {name: 'workers'}])
    } else if (to.name == 'worker') {
        const w = await getWorker(config, parseInt(to.params.id))
        result.push(['Workers', {name: 'workers'}])
        result.push([w && w.name || 'unknown', {name: 'worker', params: {id: to.params.id}}])
    }
    bc.value = result
})

</script>

<template>
  <div class="breadcrumbs">
    <template v-for="(it, idx) in bc">
        <span v-if="idx !== 0">/</span>
        <router-link :to="it[1]">{{ it[0] }}</router-link>
    </template>
  </div>
</template>

<style>
.breadcrumbs {
    padding: 1em 0;
    font-size: 110%;
}

.breadcrumbs span, .breadcrumbs a {
    padding-right: 0.4em;
}

.breadcrumbs span {
    color: grey;
}
</style>
