<script setup>
import { ref, unref, watch } from 'vue'
const props = defineProps(['active'])
const activated = ref(unref(props.active))

if (!activated.value) {
    const unwatch = watch(() => unref(props.active), () => {
        unwatch()
        activated.value = true
    })
}

</script>

<template>
    <template v-if="activated">
        <slot />
    </template>
</template>
