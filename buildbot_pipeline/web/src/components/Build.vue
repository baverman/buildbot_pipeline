<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getBuilderNames } from '../api'
import { resultClass, resultTitle, fmtDuration } from '../utils'
import { type Build } from '../types'
import StepList from './StepList.vue'

const props = defineProps<{ build: Build }>()

const builder_name = ref<string | null>(null)
const state = ref(0) // 0 - folded, 1 - problems, 2 - all
const state_labels = [
    '<i class="fa fa-expand" aria-hidden="true"></i>&nbsp;None',
    '<i class="fa fa-expand" aria-hidden="true"></i>&nbsp;Problems',
    '<i class="fa fa-compress" aria-hidden="true"></i>&nbsp;All',
]

function nextState() {
    state.value = (state.value + 1) % 3
}

async function getData() {
    if (props.build.properties.virtual_builder_title) {
        builder_name.value = props.build.properties.virtual_builder_title[0]
    } else {
        builder_name.value =
            (await getBuilderNames([props.build.builderid])).get(props.build.builderid) ?? 'unknown'
    }
}

onMounted(() => getData())
</script>

<template>
    <div>
        <div class="cbox nested-build-row">
            <div>
                <span
                    class="nested-build-state"
                    @click="nextState"
                    v-html="state_labels[state]"
                />&nbsp;
                <router-link
                    :to="{
                        name: 'build',
                        params: { builderid: props.build.builderid, number: props.build.number },
                    }"
                    >{{ builder_name }}/{{ props.build.number }}</router-link
                >
            </div>
            <div class="cbox-push nested-build-status">
                {{ fmtDuration(props.build) }} {{ props.build.state_string }}
                <span :class="`badge-text ${resultClass(props.build, true)}`">{{
                    resultTitle(props.build).toUpperCase()
                }}</span>
            </div>
        </div>
        <KeepAlive>
            <StepList v-if="state" :build="props.build" :filter-steps="state" />
        </KeepAlive>
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
    cursor: pointer;
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
