<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateChallenge, GateDisplayContext, GateSubmission } from "../../../types";
import { areaSelectCategoryLabel, areaSelectCopy, areaSelectInstruction } from "./presentation";

const props = withDefaults(defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
  challenge?: GateChallenge;
  completing?: boolean;
  completionError?: string;
}>(), {
  parameters: () => ({}),
  challenge: undefined,
  completing: false,
  completionError: "",
});
const emit = defineEmits<{ complete: [submission: GateSubmission] }>();

onMounted(() => {
  document.title = "Verification";
});

const selectedIndex = ref<number | null>(null);
const areaChallenge = computed(() =>
  props.challenge?.kind === "area-select" ? props.challenge : null,
);
const columns = computed(() => areaChallenge.value?.columns ?? 3);
const rows = computed(() => areaChallenge.value?.rows ?? 2);
const brand = computed(() => props.displayContext.brand?.trim() || "Secure Access");
const visualVariant = computed(() => areaChallenge.value?.variant ?? "blue");
const copy = computed(() => areaSelectCopy());
const instruction = computed(() => areaSelectInstruction(copy.value, props.displayContext.copy_variant));
const categoryLabel = computed(() =>
  areaChallenge.value ? areaSelectCategoryLabel(copy.value, areaChallenge.value.category_label) : "",
);
const canSubmit = computed(() => selectedIndex.value !== null && !props.completing);
const highlightStyle = computed(() => {
  if (selectedIndex.value === null) return { display: "none" };
  const col = selectedIndex.value % columns.value;
  const row = Math.floor(selectedIndex.value / columns.value);
  return {
    left: `${(col / columns.value) * 100}%`,
    top: `${(row / rows.value) * 100}%`,
    width: `${100 / columns.value}%`,
    height: `${100 / rows.value}%`,
  };
});

function selectRegion(event: MouseEvent): void {
  if (props.completing) return;
  const target = event.currentTarget as HTMLElement;
  const rect = target.getBoundingClientRect();
  const relX = (event.clientX - rect.left) / rect.width;
  const relY = (event.clientY - rect.top) / rect.height;
  const col = Math.min(columns.value - 1, Math.max(0, Math.floor(relX * columns.value)));
  const row = Math.min(rows.value - 1, Math.max(0, Math.floor(relY * rows.value)));
  selectedIndex.value = row * columns.value + col;
}

function submitAnswer(): void {
  if (!canSubmit.value || selectedIndex.value === null) return;
  emit("complete", { answer: String(selectedIndex.value) });
}
</script>

<template>
  <main
    class="area-select-page"
    :class="[`variant-${visualVariant}`, `layout-${displayContext.layout_variant}`]"
    :data-variant-id="displayContext.variant_id"
  >
    <section class="verification-card" aria-labelledby="area-select-title">
      <header class="card-head">
        <span class="badge" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9">
            <path d="M12 2l8 3v6c0 5-3.4 8.3-8 11-4.6-2.7-8-6-8-11V5z" stroke-linejoin="round" />
          </svg>
        </span>
        <span class="brand">{{ brand }}</span>
      </header>

      <p class="eyebrow">{{ copy.eyebrow }}</p>
      <h1 id="area-select-title">{{ copy.headingPrefix }}<b>{{ categoryLabel }}</b>{{ copy.headingSuffix }}</h1>
      <p class="instruction">{{ instruction }}</p>

      <div class="scene-frame">
        <div
          v-if="areaChallenge?.image_data_url"
          class="scene"
          role="button"
          tabindex="0"
          :aria-label="instruction"
          @click="selectRegion"
        >
          <img :src="areaChallenge.image_data_url" :alt="instruction" />
          <span class="highlight" :style="highlightStyle" aria-hidden="true"></span>
        </div>
        <div v-else class="scene-missing" role="alert">{{ copy.imageUnavailable }}</div>
      </div>

      <p class="selected-note" aria-live="polite">{{ selectedIndex !== null ? copy.selectedNote : "" }}</p>
      <p v-if="completionError" class="answer-error" role="alert">{{ completionError }}</p>

      <button type="button" :disabled="!canSubmit" @click="submitAnswer">
        <span v-if="completing" class="spinner" aria-hidden="true"></span>
        {{ completing ? copy.checking : copy.verifyContinue }}
      </button>
    </section>

    <footer aria-hidden="true"><span>{{ copy.privacy }}</span><i></i><span>{{ copy.help }}</span><i></i><span>{{ copy.security }}</span></footer>
  </main>
</template>

<style scoped>
* { box-sizing: border-box; }
.area-select-page {
  --accent: #174ea6;
  --accent-dark: #0d3b82;
  --soft: #edf4ff;
  display: flex;
  min-height: 100vh;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  color: #14213a;
  background: linear-gradient(160deg, var(--soft), #fbfcfe 60%);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.variant-violet { --accent: #6842a5; --accent-dark: #4c2d7d; --soft: #f0ebfa; }
.variant-mint { --accent: #176f60; --accent-dark: #0e5146; --soft: #e5f5f0; }
button { font: inherit; }

.verification-card {
  width: min(100%, 25rem);
  padding: 1.8rem 1.9rem 1.6rem;
  border: 1px solid rgba(20, 33, 58, 0.1);
  border-radius: 0.8rem;
  background: #fff;
  box-shadow: 0 1.5rem 3.6rem rgba(20, 33, 58, 0.15);
}
.card-head { display: flex; align-items: center; gap: 0.55rem; margin-bottom: 1.1rem; }
.badge { display: grid; width: 1.9rem; height: 1.9rem; place-items: center; border-radius: 0.45rem; color: #fff; background: var(--accent); }
.brand { color: #27324a; font-size: 0.92rem; font-weight: 700; }

.eyebrow { margin: 0 0 0.3rem; color: var(--accent); font-size: 0.68rem; font-weight: 800; letter-spacing: 0.13em; text-transform: uppercase; }
h1 { margin: 0; color: #16202e; font-size: 1.25rem; line-height: 1.25; }
h1 b { color: var(--accent); }
.instruction { margin: 0.55rem 0 1.1rem; color: #4a5568; font-size: 0.9rem; line-height: 1.45; }

.scene-frame { border: 1px solid rgba(20, 33, 58, 0.12); border-radius: 0.5rem; overflow: hidden; background: var(--soft); }
.scene { position: relative; display: block; width: 100%; cursor: pointer; line-height: 0; }
.scene img { width: 100%; height: auto; display: block; }
.highlight {
  position: absolute;
  border: 3px solid var(--accent);
  background: color-mix(in srgb, var(--accent) 16%, transparent);
  border-radius: 0.25rem;
  pointer-events: none;
}
.scene-missing { padding: 2.5rem 1rem; color: #a7442f; font-size: 0.85rem; text-align: center; }

.selected-note { min-height: 1rem; margin: 0.7rem 0 0; color: #5a6472; font-size: 0.76rem; }
.answer-error { margin: 0.3rem 0 0; color: #a72e28; font-size: 0.74rem; }

button {
  display: flex;
  width: 100%;
  height: 3rem;
  margin-top: 0.8rem;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  border: 0;
  border-radius: 0.5rem;
  color: #fff;
  background: var(--accent);
  cursor: pointer;
  font-size: 0.92rem;
  font-weight: 700;
}
button:hover:not(:disabled) { background: var(--accent-dark); }
button:focus-visible { outline: 3px solid color-mix(in srgb, var(--accent) 28%, transparent); outline-offset: 3px; }
button:disabled { cursor: not-allowed; opacity: 0.5; }

.spinner { width: 1rem; height: 1rem; border: 2px solid rgba(255, 255, 255, 0.4); border-top-color: #fff; border-radius: 50%; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

footer { display: flex; gap: 0.7rem; margin-top: 1.4rem; color: #8a93a3; font-size: 0.72rem; }
footer i { width: 3px; height: 3px; border-radius: 50%; background: #aab1bc; }

.layout-compact .verification-card { width: min(100%, 22rem); padding: 1.5rem 1.6rem 1.3rem; }
.layout-split .verification-card { width: min(100%, 25rem); }
</style>
