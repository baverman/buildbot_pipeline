<script setup>
import { inject, ref, onMounted, computed } from 'vue'
import {getBuildProperties} from '../data'

const config = inject('config')
const props = defineProps(['build'])
const properties = ref({})

async function getData() {
    properties.value = await getBuildProperties(config, props.build.buildid)
}

function copy(event) {
    const el = event.target.previousElementSibling
    const textArea = document.createElement("textarea")
    textArea.value = el.textContent
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    textArea.remove()
}

onMounted(() => getData())
</script>

<template>
    <table class="pure-table pure-table-horizontal">
        <thead>
            <tr>
                <td>Name</td>
                <td>Value</td>
                <td>Source</td>
            </tr>
        </thead>
        <tbody>
            <tr v-for="(value, name) in properties">
                <td>{{ name }}</td>
                <td><span class="properties-value">{{ value[0] }}</span> <i @click="copy" class="properties-copy fa fa-clone" aria-hidden="true"></i></td>
                <td>{{ value[1]}}</td>
            </tr>
        </tbody>
    </table>
</template>

<style>
.properties-copy {
    cursor: pointer;
}
</style>
