<script setup>
import { inject, ref, } from 'vue'
import {getAllBuilders, getBuilderBuilds, resultClass} from '../data'
import Loader from '../components/Loader.vue'
const config = inject('config')

async function getBuilders() {
   const builders = await getAllBuilders(config)
   return (builders || []).filter(
       it => (!~it.tags.indexOf('hidden')))
}

async function getBuilds(builder_ids) {
   const result = new Map();
   const builds = await getBuilderBuilds(config, builder_ids)
   for (var it of builds) {
       if (result.has(it.builderid)) {
          result.get(it.builderid).push(it)
       } else {
          result.set(it.builderid, [it])
       }
   }
   return result
}

const builders = ref(null)
const builds = ref(null)

async function getData() {
    const lbuilders = await getBuilders()
    builds.value = await getBuilds(lbuilders.map(it => it.builderid))
    builders.value = lbuilders
}

const load = getData()
</script>

<template>
<Loader :wait="load">
    <table role="grid">
        <tr v-for="builder in builders">
            <td><router-link :to="{name: 'builder', params: {id: builder.builderid}}">{{ builder.name }}</router-link></td>
            <td style="line-height: 1.5">
                <template v-for="build in (builds.get(builder.builderid) || []).slice(0, 15)">
                    <router-link
                            :class="`badge ${resultClass(build)}`"
                            :to="{name: 'build', params: {builderid: builder.builderid, number: build.number}}">
                        {{ build.number }}
                    </router-link>&hairsp;
                </template>
            </td>
        </tr>
    </table>
</Loader>
</template>
