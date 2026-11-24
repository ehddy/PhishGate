<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateDisplayContext } from "../../../types";


const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();
const verified = ref(false);
const completing = ref(false);
const brand = computed(() => props.displayContext.brand?.trim() || null);
const destination = computed(() => (brand.value ? `${brand.value} page` : "requested page"));

onMounted(() => {
  document.title = "Verifying connection…";
});

function handlePointerMove(): void {
  if (verified.value) {
    return;
  }

  verified.value = true;
  completing.value = true;
  emit("complete");
}
</script>

<template>
  <main class="movement-page">
    <header class="site-header" aria-hidden="true">
      <div class="site-mark">{{ brand?.charAt(0).toUpperCase() || "◇" }}</div>
      <span>{{ brand ? `${brand} secure access` : "Secure access" }}</span>
    </header>

    <section class="verify-panel">
      <h1>{{ brand ? `${brand} connection check` : "Connection check" }}</h1>
      <p>
        Move your mouse inside the box below to verify your connection and
        continue to the {{ destination }}.
      </p>

      <div
        class="target-area"
        :class="{ verified }"
        role="presentation"
        @pointermove="handlePointerMove"
      >
        <template v-if="!verified">
          <span class="pulse-ring" aria-hidden="true"></span>
          <span class="target-label">Move your mouse here</span>
        </template>
        <template v-else>
          <span class="check-mark" aria-hidden="true">✓</span>
          <span class="target-label">{{ completing ? "Verified — redirecting…" : "Verified" }}</span>
        </template>
      </div>

      <small>This check confirms an active mouse connection before continuing.</small>
    </section>
  </main>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  color: #23262b;
  background: #eef0f3;
  font-family: Arial, Helvetica, sans-serif;
}

.movement-page {
  min-height: 100vh;
  background: #eef0f3;
}

.site-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  height: 4rem;
  padding: 0 2rem;
  border-bottom: 1px solid #dadfe5;
  color: #363c45;
  background: #ffffff;
  font-size: 0.95rem;
  font-weight: 600;
}

.site-mark {
  display: grid;
  width: 1.8rem;
  height: 1.8rem;
  place-items: center;
  border-radius: 0.4rem;
  color: white;
  background: #4a5568;
  font-size: 1rem;
  font-weight: 700;
}

.verify-panel {
  width: min(90%, 28rem);
  margin: 14vh auto 0;
  text-align: center;
}

h1 {
  margin: 0 0 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
}

.verify-panel p {
  margin: 0 auto 2rem;
  color: #565d68;
  line-height: 1.55;
}

.target-area {
  position: relative;
  display: grid;
  place-items: center;
  gap: 0.6rem;
  width: 100%;
  height: 12rem;
  margin: 0 auto;
  border: 0.14rem dashed #7c8798;
  border-radius: 0.6rem;
  background: rgba(255, 255, 255, 0.55);
  cursor: crosshair;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.target-area.verified {
  border-style: solid;
  border-color: #2f9e5c;
  background: rgba(217, 245, 227, 0.75);
  cursor: default;
}

.pulse-ring {
  position: absolute;
  width: 3.4rem;
  height: 3.4rem;
  border: 0.14rem solid #7c8798;
  border-radius: 50%;
  opacity: 0.55;
  animation: pulse 1.8s ease-out infinite;
}

.check-mark {
  display: grid;
  width: 2.6rem;
  height: 2.6rem;
  place-items: center;
  border-radius: 50%;
  color: white;
  background: #2f9e5c;
  font-size: 1.4rem;
  font-weight: 700;
}

.target-label {
  color: #4a5568;
  font-size: 0.9rem;
  font-weight: 600;
}

.target-area.verified .target-label {
  color: #1f6f3f;
}

small {
  display: block;
  margin-top: 1.25rem;
  color: #8a92a0;
  font-size: 0.78rem;
}

@keyframes pulse {
  0% {
    transform: scale(0.6);
    opacity: 0.55;
  }

  100% {
    transform: scale(1.6);
    opacity: 0;
  }
}

@media (max-width: 40rem) {
  .site-header {
    height: 3.6rem;
    padding: 0 1.1rem;
  }

  .verify-panel {
    margin-top: 10vh;
  }

  .target-area {
    height: 10rem;
  }
}
</style>
