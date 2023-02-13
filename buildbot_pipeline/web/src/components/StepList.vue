<script setup>
import { inject, ref, onMounted, computed } from 'vue'
import {getBuildSteps} from '../data'
import StepListRow from './StepListRow.vue'

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

onMounted(() => getData())

</script>

<template>
    <template v-for="step in steps" :key="step.stepid">
        <StepListRow v-if="includeStep(step, props.filterSteps)" :step="step" />
    </template>
</template>
