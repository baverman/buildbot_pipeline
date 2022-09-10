<script setup>
import { RouterLink, RouterView, useRoute } from 'vue-router'
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
    color: #333;
}

.right {
    text-align: right;
}

.results_0 {
    color: #000;
    background-color: #8d4;
    border-color: #4F8530;
}

.results_1 {
    color: #FFFFFF;
    background-color: #fa3;
    border-color: #C29D46;
}

.results_2 {
    color: #000;
    background-color: #e88;
    border-color: #A77272;
}

.results_3 {
    color: #000;
    background: #AADDEE;
    border-color: #AADDEE;
}

.results_4 {
    color: #FFFFFF;
    background-color: #c6c;
    border-color: #ACA0B3;
}

.results_5 {
    color: #000;
    background-color: #ecc;
    border-color: #ACA0B3;
}

.results_6 {
    color: #000;
    background-color: #ecc;
    border-color: #ACA0B3;
}

.results_7 {
    color: #000;
    background-color: #E7D100;
    border-color: #ACA0B3;
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

div {
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

a {
    color: #337ab7;
    text-decoration: none;
}

.nowrap {
    white-space: nowrap;
}
</style>
