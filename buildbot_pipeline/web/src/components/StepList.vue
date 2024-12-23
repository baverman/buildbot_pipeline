<script setup lang="ts">
import { inject, ref } from 'vue'
import { getBuildSteps, type Config } from '../api'
import StepListRow from './StepListRow.vue'
import Loader from './Loader.vue'
import { type Build, type Step } from '../types'

const config = inject('config') as Config
const props = defineProps<{ build: Build; filterSteps: number }>()
const steps = ref<Step[]>([])

function includeStep(step: Step, fstate: number) {
    return !step.hidden && (fstate == 2 || (fstate == 1 && step.results! > 0))
}

async function getData() {
    steps.value = await getBuildSteps(config, props.build.buildid)
    setTimeout(poll, 5000)
}

async function poll() {
    if (props.build.results != null) {
        return
    }
    await getData()
}

const load = getData()
</script>

<template>
    <Loader :wait="load">
        <template v-for="step in steps" :key="step.stepid">
            <StepListRow v-if="includeStep(step, props.filterSteps)" :step="step" />
        </template>
    </Loader>
</template>
