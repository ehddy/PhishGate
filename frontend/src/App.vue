<script setup lang="ts">
import GateHost from "./gates/GateHost.vue";
import { ROUTE_PREFIX } from "./routePrefix";


const isGateRoute = Boolean(ROUTE_PREFIX) && window.location.pathname === `${ROUTE_PREFIX}/`;
</script>

<template>
  <GateHost v-if="isGateRoute" />
  <main v-else>
    <p>PhishGate frontend is running.</p>
  </main>
</template>

<style scoped>
main {
  display: grid;
  min-height: 100vh;
  place-items: center;
  font-family: system-ui, sans-serif;
}
</style>
