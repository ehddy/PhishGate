<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateChallenge, GateDisplayContext, GateSubmission } from "../../../types";
import { rotateUprightCopy, rotateUprightInstruction } from "./presentation";

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

const step = ref(0);
const rotationChallenge = computed(() =>
  props.challenge?.kind === "rotation" ? props.challenge : null,
);
const stepCount = computed(() => rotationChallenge.value?.step_count ?? 8);
const brand = computed(() => props.displayContext.brand?.trim() || "Secure Access");
const visualVariant = computed(() => rotationChallenge.value?.variant ?? "blue");
const copy = computed(() => rotateUprightCopy());
const instruction = computed(() => rotateUprightInstruction(copy.value, props.displayContext.copy_variant));
const previewStyle = computed(() => ({
  transform: `rotate(${(step.value * 360) / stepCount.value}deg)`,
}));

function submitAnswer(): void {
  if (props.completing) return;
  emit("complete", { answer: String(step.value) });
}
</script>

<template>
  <main
    class="rotate-upright-page"
    :class="[`variant-${visualVariant}`, `layout-${displayContext.layout_variant}`]"
    :data-variant-id="displayContext.variant_id"
  >
    <section class="verification-card" aria-labelledby="rotate-title">
      <header class="card-head">
        <span class="badge" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9">
            <path d="M12 2l8 3v6c0 5-3.4 8.3-8 11-4.6-2.7-8-6-8-11V5z" stroke-linejoin="round" />
          </svg>
        </span>
        <span class="brand">{{ brand }}</span>
      </header>

      <p class="eyebrow">{{ copy.eyebrow }}</p>
      <h1 id="rotate-title">{{ copy.heading }}</h1>
      <p class="instruction">{{ instruction }}</p>

      <div class="stage">
        <img
          v-if="rotationChallenge?.image_data_url"
          :src="rotationChallenge.image_data_url"
          :alt="copy.heading"
          :style="previewStyle"
        />
        <div v-else class="stage-missing" role="alert">{{ copy.imageUnavailable }}</div>
      </div>

      <label class="slider">
        <span class="slider-label">{{ copy.sliderLabel }}</span>
        <input
          type="range"
          min="0"
          :max="stepCount - 1"
          step="1"
          :value="step"
          :disabled="completing"
          :aria-label="copy.sliderLabel"
          @input="step = Number(($event.target as HTMLInputElement).value)"
        />
      </label>

      <p v-if="completionError" class="answer-error" role="alert">{{ completionError }}</p>
      <button type="button" :disabled="completing" @click="submitAnswer">
        <span v-if="completing" class="spinner" aria-hidden="true"></span>
        {{ completing ? copy.checking : copy.verifyContinue }}
      </button>
    </section>

    <footer aria-hidden="true"><span>{{ copy.privacy }}</span><i></i><span>{{ copy.help }}</span><i></i><span>{{ copy.security }}</span></footer>
  </main>
</template>

<style scoped>
* { box-sizing: border-box; }
.rotate-upright-page {
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
button, input { font: inherit; }

.verification-card {
  width: min(100%, 24rem);
  padding: 1.8rem 1.9rem 1.6rem;
  border: 1px solid rgba(20, 33, 58, 0.1);
  border-radius: 0.8rem;
  background: #fff;
  box-shadow: 0 1.5rem 3.6rem rgba(20, 33, 58, 0.15);
  text-align: center;
}
.card-head { display: flex; align-items: center; justify-content: center; gap: 0.55rem; margin-bottom: 1rem; }
.badge { display: grid; width: 1.9rem; height: 1.9rem; place-items: center; border-radius: 0.45rem; color: #fff; background: var(--accent); }
.brand { color: #27324a; font-size: 0.92rem; font-weight: 700; }

.eyebrow { margin: 0 0 0.3rem; color: var(--accent); font-size: 0.68rem; font-weight: 800; letter-spacing: 0.13em; text-transform: uppercase; }
h1 { margin: 0; color: #16202e; font-size: 1.25rem; line-height: 1.25; }
.instruction { margin: 0.55rem 0 1.2rem; color: #4a5568; font-size: 0.9rem; line-height: 1.45; }

.stage {
  display: grid;
  width: 11rem;
  height: 11rem;
  margin: 0 auto 1.2rem;
  place-items: center;
  border: 1px solid rgba(20, 33, 58, 0.12);
  border-radius: 0.6rem;
  background: var(--soft);
  overflow: hidden;
}
.stage img { width: 9.5rem; height: 9.5rem; border-radius: 0.3rem; transition: transform 0.08s linear; }
.stage-missing { padding: 1.5rem; color: #a7442f; font-size: 0.85rem; }

.slider { display: block; text-align: left; }
.slider-label { display: block; margin: 0 0 0.4rem 0.1rem; color: #445169; font-size: 0.78rem; font-weight: 700; }
.slider input { width: 100%; accent-color: var(--accent); cursor: pointer; }

.answer-error { margin: 0.6rem 0 0; color: #a72e28; font-size: 0.74rem; }
button {
  display: flex;
  width: 100%;
  height: 3rem;
  margin-top: 1rem;
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

footer { display: flex; justify-content: center; gap: 0.7rem; margin-top: 1.4rem; color: #8a93a3; font-size: 0.72rem; }
footer i { width: 3px; height: 3px; border-radius: 50%; background: #aab1bc; }

.layout-compact .verification-card { width: min(100%, 21rem); padding: 1.5rem 1.6rem 1.3rem; }
</style>
