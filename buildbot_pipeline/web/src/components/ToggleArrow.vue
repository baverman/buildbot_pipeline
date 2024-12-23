<script setup lang="ts">
const props = defineProps<{ active: boolean }>()
</script>

<template>
    <i :class="`fa fa-arrow-circle-${props.active ? 'down' : 'right'}`"></i>
</template>
