<script setup lang="ts">
import { ref } from 'vue'
import ToggleArrow from './ToggleArrow.vue'
import StepContent from './StepContent.vue'
import Activated from './Activated.vue'
import { fmtDuration, resultClass } from '../utils'
import { type Step } from '../types'

const props = defineProps<{ step: Step }>()
const details = ref(false)
</script>

<template>
    <div class="step-row vspacer">
        <div class="cbox" @click.stop.prevent="details = !details">
            <div>
                <span :class="`badge ${resultClass(props.step)}`">{{ props.step.number }}</span
                >&hairsp;
                <ToggleArrow :active="details" />
                {{ props.step.name }}
            </div>
            <div class="cbox-push">{{ fmtDuration(props.step) }} {{ props.step.state_string }}</div>
        </div>
        <Activated :active="details">
            <KeepAlive>
                <StepContent v-if="details" :step="props.step" />
            </KeepAlive>
        </Activated>
    </div>
</template>

<style>
.step-row {
    padding: 0.8em 0.5em;
    border: 1px solid lightgrey;
    border-bottom: 0;
}

.step-row:last-child {
    border: 1px solid lightgrey;
}
</style>
