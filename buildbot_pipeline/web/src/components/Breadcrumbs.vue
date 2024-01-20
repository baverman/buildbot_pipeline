<script setup>
import { inject, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import {getBuilderName, getWorker} from '../data'

const config = inject('config')
const router = useRouter()
const bc = ref([])
const active_name = ref('')
const sep = '>'


router.beforeEach(async (to, from) => {
    const result = [['Builders', {name: 'index'}]]
    active_name.value = to.name

    if (to.name == 'build') {
        const bname = await getBuilderName(config, parseInt(to.params.builderid))
        result.push([bname, {name: 'builder', params: {id: to.params.builderid}}, sep])
        result.push([to.params.number, {name: 'build', params: to.params}, sep])
    } else if (to.name == 'builder') {
        const bname = await getBuilderName(config, parseInt(to.params.id))
        result.push([bname, {name: 'builder', params: {id: to.params.id}}, sep])
    } else if (to.name == 'workers' || to.name == 'index') {
        result.push(['Workers', {name: 'workers'}])
    } else if (to.name == 'worker') {
        const w = await getWorker(config, parseInt(to.params.id))
        result.push(['Workers', {name: 'workers'}])
        result.push([w && w.name || 'unknown', {name: 'worker', params: {id: to.params.id}}, sep])
    }

    bc.value = result
})

</script>

<template>
  <nav class="nav-top">
    <ul>
      <li><strong>Buildbot</strong></li>
      <template v-for="(it, idx) in bc">
        <li v-if="it[2]" class="sep">{{ it[2] }}</li>
        <li><router-link :to="it[1]">{{ it[0] }}</router-link></li>
      </template>
    </ul>
  </nav>
</template>

<style>
nav.nav-top a:is(:focus) {
    background-color: transparent;
}

nav.nav-top a[aria-current=page] {
    font-weight: bolder;
}

li.sep {
    padding-left: 0;
    padding-right: 0;
}
</style>
