<script setup>
import { inject, ref } from 'vue'
import ToggleArrow from './ToggleArrow.vue'
import StepContent from './StepContent.vue'
import Activated from './Activated.vue'
import {fmtDuration} from '../utils'
import {resultClass} from '../data'

const config = inject('config')
const props = defineProps(['step'])
const details = ref(false)
</script>

<template>
    <div class="step-row vspacer">
        <div class="pure-g" @click.stop.prevent="details = !details">
            <div class="pure-u-1-3">
                <span :class="`badge ${resultClass(props.step)}`">{{ props.step.number}}</span>&hairsp;
                <ToggleArrow :active="details" />
                {{ props.step.name }}
            </div>
            <div class="pure-u-2-3 right">{{ fmtDuration(props.step) }} {{ props.step.state_string }}</div>
        </div>
        <Activated :active="details">
            <StepContent v-show="details" :step="props.step" />
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
