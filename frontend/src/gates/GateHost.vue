<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { templateRegistry } from "./registry";
import type { GateConfig, GateSubmission } from "./types";
import { ROUTE_PREFIX } from "../routePrefix";
import SiteShellHost from "../presentation/SiteShellHost.vue";


const search = new URLSearchParams(window.location.search);
const token = search.get("t") ?? "";
const config = ref<GateConfig | null>(null);
const definition = computed(() =>
  config.value ? templateRegistry[config.value.template_id] : undefined,
);
const error = ref("");
const loading = ref(true);
const completing = ref(false);
const interactionProps = computed(() => config.value?.gate_type === "challenge" ? {
  challenge: config.value.challenge,
  completing: completing.value,
  completionError: error.value,
} : {});

onMounted(async () => {
  // DEV/PREVIEW-ONLY screenshot seam. `import.meta.env.DEV` is the literal
  // `false` in `vite build`, so Rollup drops this branch and the dynamically
  // imported module from every production bundle; the second flag keeps it
  // dormant during ordinary `vite serve` unless the harness opts in. The
  // production gate therefore has no token-free config path (CI greps dist/
  // for the previewConfig sentinel to enforce this).
  if (import.meta.env.DEV && import.meta.env.VITE_PHISHGATE_PREVIEW === "1") {
    const { buildPreviewConfig } = await import("./preview/previewConfig");
    const preview = buildPreviewConfig(window.location.search);
    if (preview) {
      config.value = preview;
      loading.value = false;
      return;
    }
  }
  try {
    const response = await fetch(
      `${ROUTE_PREFIX}/api/gates/config?t=${encodeURIComponent(token)}`,
    );
    const payload = (await response.json()) as GateConfig & { detail?: string };
    if (!response.ok) {
      throw new Error(payload.detail ?? "The gate configuration is unavailable.");
    }
    config.value = payload;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "The gate configuration is unavailable.";
  } finally {
    loading.value = false;
  }
});

async function handleComplete(submission: GateSubmission = {}): Promise<void> {
  // In the DEV/preview screenshot seam there is no backend to POST to, so
  // completion is a no-op (otherwise auto-completing templates like `alert`
  // would surface a failed-fetch error toast into the capture). Dropped from
  // production builds with the mount guard above.
  if (import.meta.env.DEV && import.meta.env.VITE_PHISHGATE_PREVIEW === "1") {
    return;
  }
  if (!config.value || !definition.value || completing.value) {
    return;
  }

  completing.value = true;
  error.value = "";
  try {
    const nextUrl = await definition.value.complete(token, submission);
    window.location.assign(nextUrl);
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "The gate could not be completed.";
    completing.value = false;
  }
}
</script>

<template>
  <main v-if="loading" class="gate-loading">Preparing the gate…</main>
  <SiteShellHost v-else-if="definition && config" :context="config.display_context">
    <component
      :is="definition.component"
      :display-context="config.display_context"
      :parameters="config.parameters"
      v-bind="interactionProps"
      @complete="handleComplete"
    />
  </SiteShellHost>
  <main v-else-if="!error" class="gate-error">
    <h1>Gate configuration error</h1>
    <p>The requested gate template or target is unavailable.</p>
  </main>
  <p v-if="error && config?.gate_type !== 'challenge'" class="error-message" role="alert">{{ error }}</p>
</template>

<style scoped>
.gate-loading,
.gate-error {
  display: grid;
  min-height: 100vh;
  place-content: center;
  padding: 2rem;
  font-family: system-ui, sans-serif;
  text-align: center;
}

.error-message {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  max-width: 28rem;
  margin: 0;
  padding: 0.9rem 1rem;
  border-radius: 0.5rem;
  color: #8d1f18;
  background: #fff0ef;
  font-family: system-ui, sans-serif;
}
</style>
