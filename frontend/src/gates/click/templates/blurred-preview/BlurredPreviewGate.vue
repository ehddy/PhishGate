<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateDisplayContext } from "../../../types";
import { blurredPreviewCopy, blurredPreviewDetail } from "./presentation";

const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();

const completing = ref(false);
const brand = computed(() => props.displayContext.brand?.trim() || "Document Portal");
const copy = computed(() => blurredPreviewCopy());
const detail = computed(() => blurredPreviewDetail(copy.value, props.displayContext.copy_variant));

onMounted(() => {
  document.title = copy.value.heading;
});

function viewDocument(): void {
  if (completing.value) return;
  completing.value = true;
  emit("complete");
}
</script>

<template>
  <main
    class="locked-preview-page"
    :class="`layout-${displayContext.layout_variant}`"
    :data-variant-id="displayContext.variant_id"
  >
    <!-- Blurred, non-interactive placeholder document behind the overlay. It
         contains no real content — just shaped blocks — and is aria-hidden. -->
    <div class="doc-backdrop" aria-hidden="true">
      <div class="doc-sheet">
        <div class="doc-row doc-title"></div>
        <div class="doc-row w80"></div>
        <div class="doc-row w95"></div>
        <div class="doc-row w60"></div>
        <div class="doc-grid">
          <span></span><span></span><span></span><span></span>
          <span></span><span></span><span></span><span></span>
        </div>
        <div class="doc-row w90"></div>
        <div class="doc-row w70"></div>
      </div>
    </div>

    <div class="overlay">
      <section class="preview-card" aria-labelledby="preview-title" aria-describedby="preview-detail">
        <div class="doc-icon" aria-hidden="true">
          <span class="fold"></span>
          <i></i><i></i><i></i>
        </div>
        <p class="eyebrow">{{ copy.eyebrow }}</p>
        <h1 id="preview-title">{{ copy.heading }}</h1>
        <p class="doc-name">{{ copy.docLabel }} · {{ brand }}</p>
        <p v-if="detail" id="preview-detail" class="detail">{{ detail }}</p>

        <button type="button" class="primary-button" :disabled="completing" @click="viewDocument">
          <span v-if="completing" class="spinner" aria-hidden="true"></span>
          {{ completing ? copy.opening : copy.viewLabel }}
        </button>

        <p class="status-copy"><span class="lock" aria-hidden="true">🔒</span>{{ copy.statusNote }}</p>
      </section>
    </div>
  </main>
</template>

<style scoped>
* { box-sizing: border-box; }
.locked-preview-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  color: var(--pg-shell-text, #1e2633);
  background: var(--pg-shell-background, #eceff3);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button { font: inherit; }

.doc-backdrop {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: start center;
  padding-top: 3.5rem;
  filter: blur(7px);
  opacity: 0.85;
}
.doc-sheet {
  width: min(44rem, 90%);
  padding: 2.4rem 2.6rem;
  border-radius: 0.4rem;
  background: #fff;
  box-shadow: 0 1rem 3rem rgba(28, 39, 58, 0.18);
}
.doc-row { height: 0.85rem; margin-bottom: 0.9rem; border-radius: 0.2rem; background: #d7dde4; }
.doc-title { width: 55%; height: 1.5rem; background: #c6cdd6; }
.w60 { width: 60%; } .w70 { width: 70%; } .w80 { width: 80%; } .w90 { width: 90%; } .w95 { width: 95%; }
.doc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.6rem; margin: 1.4rem 0; }
.doc-grid span { height: 3.2rem; border-radius: 0.3rem; background: #e3e8ee; }

.overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: color-mix(in srgb, var(--pg-shell-background, #eceff3) 55%, transparent);
}
.preview-card {
  width: min(100%, 27rem);
  padding: 2.3rem 2.2rem 1.5rem;
  border: 1px solid rgba(28, 39, 58, 0.1);
  border-radius: 0.7rem;
  background: var(--pg-shell-surface, #fff);
  box-shadow: 0 1.8rem 4rem rgba(28, 39, 58, 0.26);
  text-align: center;
}
.doc-icon {
  position: relative;
  width: 2.8rem;
  height: 3.4rem;
  margin: 0 auto 1rem;
  border-radius: 0.3rem;
  background: var(--pg-theme-accent, #2563c9);
}
.doc-icon .fold {
  position: absolute;
  top: 0;
  right: 0;
  width: 0.9rem;
  height: 0.9rem;
  background: color-mix(in srgb, var(--pg-theme-accent, #2563c9) 55%, #fff);
  clip-path: polygon(100% 0, 0 0, 100% 100%);
}
.doc-icon i { position: absolute; left: 0.5rem; right: 0.5rem; height: 0.18rem; border-radius: 1px; background: rgba(255, 255, 255, 0.85); }
.doc-icon i:nth-child(2) { bottom: 1.3rem; }
.doc-icon i:nth-child(3) { bottom: 0.95rem; right: 1.1rem; }
.doc-icon i:nth-child(4) { bottom: 0.6rem; }
.eyebrow {
  margin: 0 0 0.4rem;
  color: var(--pg-theme-accent, #2563c9);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
h1 { margin: 0; color: var(--pg-shell-text, #1b2432); font-size: clamp(1.4rem, 4vw, 1.75rem); line-height: 1.2; }
.doc-name { margin: 0.55rem 0 0; color: #6b7482; font-size: 0.86rem; }
.detail { margin: 0.95rem auto 0; max-width: 23rem; color: #5a6472; font-size: 0.9rem; line-height: 1.5; }

.primary-button {
  display: flex;
  width: 100%;
  min-height: 3rem;
  margin-top: 1.5rem;
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
.status-copy { display: flex; align-items: center; justify-content: center; gap: 0.4rem; margin: 0.9rem 0 0; color: #828b98; font-size: 0.74rem; }
.lock { font-size: 0.8rem; }

.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.layout-compact .preview-card { width: min(100%, 24rem); padding: 1.9rem 1.8rem 1.3rem; }
.layout-split .preview-card { width: min(100%, 27rem); }

@media (max-width: 40rem) {
  .doc-backdrop { padding-top: 2rem; }
  .preview-card { padding: 1.9rem 1.4rem 1.2rem; }
}
</style>
