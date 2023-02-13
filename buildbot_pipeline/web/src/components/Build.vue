<script setup>
import { inject, ref, onMounted, computed } from 'vue'
import {getBuilderNames, getBuildSteps, resultClass, resultTitle} from '../data'
import {fmtDuration} from '../utils'
import StepList from './StepList.vue'

const config = inject('config')
const props = defineProps(['build'])

const builder_name = ref(null)
const state = ref(0)  // 0 - folded, 1 - problems, 2 - all
const state_labels = [
    '<i class="fa fa-expand" aria-hidden="true"></i>&nbsp;None',
    '<i class="fa fa-expand" aria-hidden="true"></i>&nbsp;Problems',
    '<i class="fa fa-compress" aria-hidden="true"></i>&nbsp;All'
]

function nextState() {
    state.value = (state.value + 1) % 3
}

async function getData() {
    if (props.build.properties.virtual_builder_title) {
        builder_name.value = props.build.properties.virtual_builder_title[0]
    } else {
        builder_name.value = (await getBuilderNames(config, [props.build.builderid])).get(props.build.builderid)
    }
}

onMounted(() => getData())
</script>

<template>
<div>
    <div class="pure-g nested-build-row">
        <div class="pure-u-2-5">
            <span class="pure-button nested-build-state" @click="nextState" v-html="state_labels[state]" />&nbsp;
            <router-link :to="{name: 'build', params: {builderid: props.build.builderid, number: props.build.number}}">{{ builder_name }}/{{ props.build.number }}</router-link>
        </div>
        <div class="pure-u-3-5 right nested-build-status">
            {{ fmtDuration(props.build) }} {{ props.build.state_string }}
            <span :class="`badge-text ${resultClass(props.build, true)}`">{{ resultTitle(props.build).toUpperCase() }}</span>
        </div>
    </div>
    <StepList v-if="state" :build="props.build" :filter-steps="state" />
</div>
</template>

<style>
.nested-build-state {
    font-size: 80%;
    padding: 0.3em 0.5em;
    border-radius: 2px;
    min-width: 4em;
    background-color: #fff;
    border: 1px solid #ccc;
}

.nested-build-row {
    padding: 0.5em 0.8em;
    background-color: #f5f5f5;
    border-color: #ddd;
    border-radius: 3px;
    border-width: 1px;
    border-style: solid;
}

.nested-build-status {
    font-size: 90%;
}
</style>
