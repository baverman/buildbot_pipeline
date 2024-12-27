<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { getBuilderName, getWorker } from '../api'

type Entry = [string | string[] | number, object, string?]

const router = useRouter()
const bc = ref<Entry[]>([])
const active_name = ref('')
const sep = '>'

router.beforeEach(async (to) => {
    const result: Entry[] = [['Builders', { name: 'index' }]]
    active_name.value = to.name as string

    if (to.name == 'build') {
        const bname = await getBuilderName(parseInt(to.params.builderid as string))
        result.push([bname, { name: 'builder', params: { id: to.params.builderid } }, sep])
        result.push([to.params.number, { name: 'build', params: to.params }, sep])
    } else if (to.name == 'builder') {
        const bname = await getBuilderName(parseInt(to.params.id as string))
        result.push([bname, { name: 'builder', params: { id: to.params.id } }, sep])
    } else if (to.name == 'workers' || to.name == 'index') {
        result.push(['Workers', { name: 'workers' }])
    } else if (to.name == 'worker') {
        const w = await getWorker(parseInt(to.params.id as string))
        result.push(['Workers', { name: 'workers' }])
        result.push([
            (w && w.name) || 'unknown',
            { name: 'worker', params: { id: to.params.id } },
            sep,
        ])
    }

    bc.value = result
})
</script>

<template>
    <nav class="nav-top">
        <ul>
            <li><strong>Buildbot</strong></li>
            <template v-for="(it, index) in bc" :key="index">
                <li v-if="it[2]" class="sep">{{ it[2] }}</li>
                <li>
                    <router-link :to="it[1]">{{ it[0] }}</router-link>
                </li>
            </template>
        </ul>
    </nav>
</template>

<style>
nav.nav-top a:is(:focus) {
    background-color: transparent;
}

nav.nav-top a[aria-current='page'] {
    font-weight: bolder;
}

li.sep {
    padding-left: 0;
    padding-right: 0;
}
</style>
