<script setup>
import { ref } from 'vue'
const props = defineProps(['active'])
</script>

<template>
    <i :class="`fa fa-arrow-circle-${active ? 'down' : 'right'}`"></i>
</template>
