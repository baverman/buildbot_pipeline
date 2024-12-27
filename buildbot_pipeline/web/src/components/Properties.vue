<script setup lang="ts">
import { ref } from 'vue'
import { getBuildProperties } from '../api'
import { type Build, type Properties } from '../types'
import Loader from './Loader.vue'

const props = defineProps<{ build: Build }>()
const properties = ref<Properties>({})

async function getData() {
    properties.value = await getBuildProperties(props.build.buildid)
}

function copy(event: Event) {
    const el = (event.target as HTMLSpanElement).previousElementSibling!
    const textArea = document.createElement('textarea')
    textArea.value = el.textContent ?? ''
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    textArea.remove()
}

const load = getData()
</script>

<template>
    <Loader :wait="load">
        <table role="grid">
            <thead>
                <tr>
                    <td>Name</td>
                    <td>Value</td>
                    <td>Source</td>
                </tr>
            </thead>
            <tbody>
                <tr v-for="(value, name) in properties" :key="name">
                    <td>{{ name }}</td>
                    <td>
                        <span class="properties-value">{{ value[0] }}</span>
                        <i @click="copy" class="properties-copy fa fa-clone" aria-hidden="true"></i>
                    </td>
                    <td>{{ value[1] }}</td>
                </tr>
            </tbody>
        </table>
    </Loader>
</template>

<style>
.properties-copy {
    cursor: pointer;
}
</style>
