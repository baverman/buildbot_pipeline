<script setup lang="ts">
import { ref } from 'vue'
const props = defineProps<{active: boolean}>()
</script>

<template>
    <i :class="`fa fa-arrow-circle-${active ? 'down' : 'right'}`"></i>
</template>
