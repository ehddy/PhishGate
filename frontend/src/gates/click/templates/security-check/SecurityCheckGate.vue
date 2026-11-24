<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateDisplayContext } from "../../../types";
import { securityCheckCopy, securityCheckDetail } from "./presentation";

const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();

const completing = ref(false);
const brand = computed(() => props.displayContext.brand?.trim() || "This site");
const copy = computed(() => securityCheckCopy());
const detail = computed(() => securityCheckDetail(copy.value, props.displayContext.copy_variant));

onMounted(() => {
  document.title = copy.value.heading;
});

function continueToContent(): void {
  if (completing.value) return;
  completing.value = true;
  emit("complete");
}
</script>

<template>
  <main
    class="interstitial-page"
    :class="`layout-${displayContext.layout_variant}`"
    :data-variant-id="displayContext.variant_id"
  >
    <header class="site-header" aria-hidden="true">
      <div class="site-identity">
        <span class="site-mark">{{ brand.charAt(0).toUpperCase() }}</span>
        <strong>{{ brand }}</strong>
      </div>
      <div class="header-status"><span></span>{{ copy.eyebrow }}</div>
    </header>

    <section class="notice-card" aria-labelledby="interstitial-title" aria-describedby="interstitial-detail">
      <div class="shield-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M12 2l8 3v6c0 5-3.4 8.3-8 11-4.6-2.7-8-6-8-11V5z" stroke-linejoin="round" />
          <path d="M8.5 12l2.4 2.4 4.6-4.8" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>

      <p class="eyebrow">{{ copy.eyebrow }}</p>
      <h1 id="interstitial-title">{{ copy.heading }}</h1>
      <p v-if="detail" id="interstitial-detail" class="detail">{{ detail }}</p>

      <div class="reason-panel">
        <p class="reason-title">{{ copy.reasonTitle }}</p>
        <ul>
          <li><span aria-hidden="true">✓</span>{{ copy.reasonOne }}</li>
          <li><span aria-hidden="true">✓</span>{{ copy.reasonTwo }}</li>
        </ul>
      </div>

      <button type="button" class="primary-button" :disabled="completing" @click="continueToContent">
        <span v-if="completing" class="spinner" aria-hidden="true"></span>
        {{ completing ? copy.verifying : copy.continueLabel }}
      </button>

      <p class="status-copy">{{ copy.statusNote }}</p>
    </section>

    <footer aria-hidden="true">
      <span>{{ copy.privacy }}</span><i></i><span>{{ copy.terms }}</span><i></i><span>{{ copy.help }}</span>
    </footer>
  </main>
</template>

<style scoped>
* { box-sizing: border-box; }
.interstitial-page {
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  color: var(--pg-shell-text, #1f2733);
  background: var(--pg-shell-background, #eef1f6);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button { font: inherit; }

.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 4.25rem;
  padding: 0 2rem;
  border-bottom: 1px solid rgba(23, 34, 54, 0.1);
  background: var(--pg-shell-surface, #fff);
}
.site-identity { display: flex; align-items: center; gap: 0.7rem; font-size: 0.95rem; font-weight: 680; }
.site-mark {
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border-radius: 0.45rem;
  color: #fff;
  background: var(--pg-theme-accent, #2563c9);
  font-size: 1rem;
}
.header-status { display: flex; align-items: center; gap: 0.45rem; color: #6b7482; font-size: 0.8rem; }
.header-status span {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: #22a06b;
}

.notice-card {
  width: min(calc(100% - 2rem), 34rem);
  margin: 9vh auto 3rem;
  padding: 2.6rem 2.4rem 1.6rem;
  border: 1px solid rgba(23, 34, 54, 0.08);
  border-radius: 0.7rem;
  background: var(--pg-shell-surface, #fff);
  box-shadow: 0 1.5rem 3.5rem rgba(28, 39, 58, 0.14);
  text-align: center;
}
.shield-icon {
  display: grid;
  width: 3.4rem;
  height: 3.4rem;
  margin: 0 auto 1.1rem;
  place-items: center;
  border-radius: 0.9rem;
  color: var(--pg-theme-accent, #2563c9);
  background: color-mix(in srgb, var(--pg-theme-accent, #2563c9) 12%, #fff);
}
.eyebrow {
  margin: 0 0 0.45rem;
  color: var(--pg-theme-accent, #2563c9);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
h1 { margin: 0; color: var(--pg-shell-text, #1b2432); font-size: clamp(1.5rem, 4.5vw, 1.95rem); line-height: 1.2; }
.detail { margin: 0.85rem auto 0; max-width: 28rem; color: #5a6472; font-size: 0.93rem; line-height: 1.5; }

.reason-panel {
  margin: 1.5rem 0 1.4rem;
  padding: 1rem 1.1rem;
  border: 1px solid rgba(23, 34, 54, 0.1);
  border-radius: 0.5rem;
  background: color-mix(in srgb, var(--pg-shell-background, #eef1f6) 55%, #fff);
  text-align: left;
}
.reason-title { margin: 0 0 0.6rem; color: #3b4454; font-size: 0.82rem; font-weight: 680; }
.reason-panel ul { margin: 0; padding: 0; list-style: none; display: grid; gap: 0.4rem; }
.reason-panel li { display: flex; align-items: flex-start; gap: 0.5rem; color: #57616f; font-size: 0.82rem; line-height: 1.4; }
.reason-panel li span { color: #22a06b; font-weight: 700; }

.primary-button {
  display: flex;
  width: 100%;
  min-height: 3rem;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  border: 0;
  border-radius: 0.42rem;
  color: #fff;
  background: var(--pg-theme-accent, #2563c9);
  box-shadow: 0 0.35rem 0.9rem rgba(37, 99, 201, 0.24);
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 650;
}
.primary-button:hover:not(:disabled) { filter: brightness(0.94); }
.primary-button:focus-visible { outline: 3px solid color-mix(in srgb, var(--pg-theme-accent, #2563c9) 32%, transparent); outline-offset: 3px; }
.primary-button:disabled { cursor: default; opacity: 0.85; }
.status-copy { margin: 0.9rem 0 0; color: #828b98; font-size: 0.74rem; }

.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

footer {
  display: flex;
  min-height: 3.5rem;
  align-items: center;
  justify-content: center;
  gap: 0.7rem;
  color: #8a929e;
  font-size: 0.74rem;
}
footer i { width: 3px; height: 3px; border-radius: 50%; background: #aab1bc; }

.layout-compact .notice-card { margin-top: 5vh; padding: 2rem 1.8rem 1.3rem; }
.layout-split .notice-card { margin-inline: auto; }

@media (max-width: 40rem) {
  .site-header { height: 3.7rem; padding: 0 1rem; }
  .notice-card { margin-top: 5vh; padding: 1.9rem 1.3rem 1.2rem; }
}
</style>
