<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import Breadcrumbs from './components/Breadcrumbs.vue'
const route = useRoute()
</script>

<template>
    <Breadcrumbs />
    <router-view :key="route.path" />
</template>

<style>
body {
    padding: 0 1em 1em 1em;
    /* color: #333; */
}

:root {
    --form-element-spacing-vertical: 0.3rem;
}

.right {
    text-align: right;
}

.results_0 {
    color: #000;
    background-color: #8d4;
    border-color: #4f8530;
}

.results_1 {
    color: #ffffff;
    background-color: #fa3;
    border-color: #c29d46;
}

.results_2 {
    color: #000;
    background-color: #e88;
    border-color: #a77272;
}

.results_3 {
    color: #000;
    background: #aaddee;
    border-color: #aaddee;
}

.results_4 {
    color: #ffffff;
    background-color: #c6c;
    border-color: #aca0b3;
}

.results_5 {
    color: #000;
    background-color: #ecc;
    border-color: #aca0b3;
}

.results_6 {
    color: #000;
    background-color: #ecc;
    border-color: #aca0b3;
}

.results_7 {
    color: #000;
    background-color: #e7d100;
    border-color: #aca0b3;
}

.results_99 {
    color: #000;
    background-color: #e7d100;
    border-color: #aca0b3;
}

.pulse {
    -webkit-animation: pulse_animation 1s linear infinite;
    animation: pulse_animation 1s linear infinite;
    transform-origin: 70% 70%;
    display: inline-block;
}

@keyframes pulse_animation {
    0% {
        transform: scale(0.9);
        -webkit-transform: scale(0.9);
    }
    30% {
        transform: scale(0.9);
        -webkit-transform: scale(0.9);
    }
    40% {
        transform: scale(1.08);
        -webkit-transform: scale(1.08);
    }
    50% {
        transform: scale(0.9);
        -webkit-transform: scale(0.9);
    }
    60% {
        transform: scale(0.9);
        -webkit-transform: scale(0.9);
    }
    70% {
        transform: scale(1.05);
        -webkit-transform: scale(1.05);
    }
    80% {
        transform: scale(0.9);
        -webkit-transform: scale(0.9);
    }
    100% {
        transform: scale(0.9);
        -webkit-transform: scale(0.9);
    }
}

.badge {
    border-radius: 0.8em;
    padding: 0.1em 0.5em;
    text-decoration: none;
    font-size: 90%;
}

.badge-text {
    border-radius: 3px;
    padding: 0.2em 0.5em;
    text-decoration: none;
    font-weight: 700;
    font-size: 80%;
}

.w-100 {
    width: 100%;
}

.w-inline {
    display: inline-block;
    width: auto;
    margin: 0;
}

div.__comment {
    box-sizing: border-box;
    width: 100%;
    max-width: 100%;
}

.vspacer-grid {
    min-width: 0;
    display: grid;
    grid-auto-flow: row;
    grid-row-gap: var(--spacer-gap, 0.6em);
}

.vspacer > *:not(:last-child) {
    margin-bottom: var(--spacer-gap, 0.6em);
}

a.__comment {
    color: #337ab7;
    text-decoration: none;
}

.nowrap {
    white-space: nowrap;
}

.cbox {
    display: flex;
}

.cbox-push {
    margin-left: auto;
}
</style>
