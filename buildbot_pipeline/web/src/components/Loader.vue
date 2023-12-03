<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps(['wait'])
const show_fallback = ref(false)
const ready = ref(false)

async function wait() {
    await props.wait
    ready.value = true
}

setTimeout(() => show_fallback.value = true, 300)
onMounted(wait)
</script>

<template>
    <template v-if="!ready && show_fallback"><div>Loading...</div></template>
    <slot v-else-if="ready" />
</template>
