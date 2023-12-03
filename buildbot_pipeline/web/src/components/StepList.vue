<script setup>
import { inject, ref } from 'vue'
import {getBuildSteps} from '../data'
import StepListRow from './StepListRow.vue'
import Loader from './Loader.vue'

const config = inject('config')
const props = defineProps(['build', 'filter-steps'])
const steps = ref([])

function includeStep(step, fstate) {
    return !step.hidden && (fstate == 2 || (fstate == 1 && step.results > 0))
}

function allStepsDone(steps) {
}

async function getData() {
    steps.value = await getBuildSteps(config, props.build.buildid)
    setTimeout(poll, 5000);
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
