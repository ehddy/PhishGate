<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateDisplayContext } from "../../../types";
import { alertCopy, alertDialogText } from "./presentation";


const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();
const brand = computed(() => props.displayContext.brand?.trim() || null);
const copy = computed(() => alertCopy());
const status = ref("");

onMounted(() => {
  status.value = copy.value.preparing;
  document.title = "Sign in";
  window.setTimeout(() => {
    const { title, message } = alertDialogText(copy.value, brand.value, props.displayContext.copy_variant);
    // window.alert() is drawn entirely by the browser itself (native chrome,
    // fixed OS font/button/layout) -- no CSS in this file can reach it. The
    // only things under this template's control are its text and the page
    // behind it, both handled below.
    window.alert(`${title}\n\n${message}`);
    status.value = copy.value.opening;
    emit("complete");
  }, 150);
});
</script>

<template>
  <main class="alert-page" :class="`layout-${displayContext.layout_variant}`" :data-variant-id="displayContext.variant_id">
    <header class="site-header">
      <div class="site-mark" aria-hidden="true">◇</div>
      <span>{{ brand ? `${brand} ${copy.protectedContent.toLowerCase()}` : copy.protectedContent }}</span>
    </header>

    <section class="status-card" aria-live="polite">
      <div class="spinner" aria-hidden="true"></div>
      <h1>{{ copy.oneMoment }}</h1>
      <p>{{ status }}</p>
      <small>{{ copy.keepWindowOpen }}</small>
    </section>
  </main>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  color: #202124;
  background: #f7f8fa;
  font-family: Arial, Helvetica, sans-serif;
}

.alert-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 50% 25%, color-mix(in srgb, var(--pg-theme-accent, #dbe5f4) 35%, transparent), transparent 36rem),
    #f7f8fa;
}

.site-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  height: 4rem;
  padding: 0 2rem;
  border-bottom: 1px solid #e1e5eb;
  color: #313b4a;
  background: rgba(255, 255, 255, 0.92);
  font-size: 0.95rem;
  font-weight: 600;
}

.site-mark {
  display: grid;
  width: 1.8rem;
  height: 1.8rem;
  place-items: center;
  border-radius: 0.45rem;
  color: white;
  background: var(--pg-theme-accent, #315b9d);
  font-size: 1.15rem;
}

.status-card {
  width: min(90%, 30rem);
  margin: 18vh auto 0;
  padding: 2.5rem 2.25rem;
  border: 1px solid #e2e6eb;
  border-radius: 0.8rem;
  background: white;
  box-shadow: 0 0.8rem 2.5rem rgba(42, 52, 68, 0.08);
  text-align: center;
}

.spinner {
  width: 2.4rem;
  height: 2.4rem;
  margin: 0 auto 1.4rem;
  border: 0.22rem solid #dce4ef;
  border-top-color: var(--pg-theme-accent, #315b9d);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

h1 {
  margin: 0 0 0.7rem;
  font-size: 1.45rem;
  font-weight: 600;
}

p {
  margin: 0 0 1.25rem;
  color: #596579;
  line-height: 1.55;
}

small {
  color: #8a94a3;
  font-size: 0.78rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* This template's own reachable surface is only the loading backdrop behind
   the native alert(), so layout_variant stays a modest width/position
   change rather than a forced structural rework. */
.layout-compact .status-card { width: min(calc(100% - 2rem), 24rem); margin-top: 22vh; padding: 2rem 1.75rem; }
.layout-split .status-card { width: min(85%, 27rem); }

@media (max-width: 40rem) {
  .site-header {
    height: 3.6rem;
    padding: 0 1.1rem;
  }

  .status-card,
  .layout-compact .status-card,
  .layout-split .status-card {
    margin: 14vh auto 0;
    width: min(90%, 30rem);
    padding: 2.15rem 1.4rem;
  }
}
</style>
