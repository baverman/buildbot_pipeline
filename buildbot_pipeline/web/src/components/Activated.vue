<script setup lang="ts">
import { ref, unref, watch } from 'vue'
const props = defineProps<{ active: boolean }>()
const activated = ref(unref(props.active))

if (!activated.value) {
    const unwatch = watch(
        () => unref(props.active),
        () => {
            unwatch()
            activated.value = true
        },
    )
}
</script>

<template>
    <template v-if="activated">
        <slot />
    </template>
</template>
