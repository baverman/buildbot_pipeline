<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { AppError } from '../api'

const props = defineProps<{ wait: Promise<unknown> }>()
const show_fallback = ref(false)
const ready = ref(false)
const error = ref<string>()

async function waitFn() {
    try {
        await props.wait
    } catch (e) {
        if (e instanceof AppError) {
            error.value = e.toString()
        } else {
            throw e
        }
    }
    ready.value = true
}

setTimeout(() => (show_fallback.value = true), 300)
onMounted(waitFn)
</script>

<template>
    <template v-if="!ready && show_fallback"
        ><div><span aria-busy="true">Loading...</span></div></template
    >
    <template v-if="ready && error">{{ error }}</template>
    <slot v-else-if="ready" />
</template>
