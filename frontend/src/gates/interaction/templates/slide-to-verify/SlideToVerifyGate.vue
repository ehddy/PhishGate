<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateDisplayContext } from "../../../types";
import { slideCopy, slideNotice } from "./presentation";


const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();

onMounted(() => {
  document.title = "Identity Verification";
});

const track = ref<HTMLElement | null>(null);
const handle = ref<HTMLElement | null>(null);
const progress = ref(0);
const dragging = ref(false);
const verified = ref(false);
const copy = computed(() => slideCopy());
const notice = computed(() => slideNotice(copy.value, props.displayContext.copy_variant));
const completionPercent = computed(() => {
  const configured = props.parameters?.completion_percent;
  return typeof configured === "number" && configured >= 80 && configured <= 100
    ? configured
    : 94;
});
const handleStyle = computed(() => ({
  left: `${progress.value}%`,
  transform: `translateX(-${progress.value}%)`,
}));
const fillStyle = computed(() => ({ width: `${progress.value}%` }));

function updateProgress(clientX: number): void {
  if (!track.value || !handle.value) {
    return;
  }

  const trackRect = track.value.getBoundingClientRect();
  const handleWidth = handle.value.getBoundingClientRect().width;
  const travelWidth = Math.max(trackRect.width - handleWidth, 1);
  const handleCenter = clientX - trackRect.left - handleWidth / 2;
  progress.value = Math.min(100, Math.max(0, (handleCenter / travelWidth) * 100));
}

function startDrag(event: PointerEvent): void {
  if (verified.value || (event.pointerType === "mouse" && event.button !== 0)) {
    return;
  }

  dragging.value = true;
  handle.value?.setPointerCapture(event.pointerId);
  updateProgress(event.clientX);
}

function moveDrag(event: PointerEvent): void {
  if (dragging.value) {
    updateProgress(event.clientX);
  }
}

function finishDrag(): void {
  if (!dragging.value) {
    return;
  }

  dragging.value = false;
  if (progress.value >= completionPercent.value) {
    progress.value = 100;
    verified.value = true;
    emit("complete");
    return;
  }

  progress.value = 0;
}

function cancelDrag(): void {
  if (!verified.value) {
    dragging.value = false;
    progress.value = 0;
  }
}
</script>

<template>
  <main class="verification-page" :class="`layout-${displayContext.layout_variant}`" :data-variant-id="displayContext.variant_id">
    <header class="site-header">
      <div class="site-identity">
        <span class="site-mark" aria-hidden="true">S</span>
        <span>{{ displayContext.brand ? `${displayContext.brand} secure access` : "Secure access" }}</span>
      </div>
      <span class="encrypted-label">{{ copy.encryptedConnection }}</span>
    </header>

    <section class="verification-card" aria-labelledby="verification-title">
      <div class="shield" :class="{ verified }" aria-hidden="true">
        <span>{{ verified ? "✓" : "◇" }}</span>
      </div>
      <p class="eyebrow">{{ copy.eyebrow }}</p>
      <h1 id="verification-title">{{ verified ? copy.verificationComplete : copy.verifyHuman }}</h1>
      <p class="description">{{ verified ? copy.redirecting : copy.slideInstruction }}</p>

      <div v-if="notice" class="notice">{{ notice }}</div>

      <div
        ref="track"
        class="slider-track"
        :class="{ dragging, verified }"
        aria-label="Slide verification control"
      >
        <span class="slider-fill" :style="fillStyle"></span>
        <span class="track-label">{{ verified ? copy.verified : copy.slideToVerify }}</span>
        <button
          ref="handle"
          class="slider-handle"
          type="button"
          :style="handleStyle"
          :disabled="verified"
          :aria-label="verified ? 'Verification complete' : 'Drag right to verify'"
          :aria-valuenow="Math.round(progress)"
          aria-valuemin="0"
          aria-valuemax="100"
          role="slider"
          @pointerdown.prevent="startDrag"
          @pointermove.prevent="moveDrag"
          @pointerup.prevent="finishDrag"
          @pointercancel="cancelDrag"
          @lostpointercapture="cancelDrag"
          @contextmenu.prevent
        >
          <span aria-hidden="true">{{ verified ? "✓" : "→" }}</span>
        </button>
      </div>

      <p class="hint">{{ verified ? copy.hintOpening : copy.hintDrag }}</p>
    </section>

    <footer>{{ copy.footer }}</footer>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(body) {
  margin: 0;
  color: #1d2530;
  background: #0e1220;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button { font: inherit; }
.verification-page {
  min-height: 100vh;
  background: radial-gradient(circle at 50% 42%, color-mix(in srgb, var(--pg-theme-accent, #36537e) 20%, transparent), transparent 35rem), linear-gradient(145deg, #0a0d17 0%, #11172a 52%, #090c14 100%);
}
.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 4.25rem;
  padding: 0 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  color: #dce4ef;
  background: rgba(10, 13, 23, 0.74);
  backdrop-filter: blur(12px);
}
.site-identity { display: flex; align-items: center; gap: 0.7rem; font-size: 0.92rem; font-weight: 650; }
.site-mark {
  display: grid;
  width: 1.9rem;
  height: 1.9rem;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 50%;
  color: #fff;
  background: var(--pg-theme-accent, #256d59);
  font-size: 0.78rem;
  font-weight: 800;
}
.encrypted-label { color: #8f9aad; font-size: 0.76rem; }
.verification-card {
  width: min(calc(100% - 2rem), 31rem);
  padding: 2.5rem 2.4rem 2.2rem;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 1.35rem;
  background: #fff;
  box-shadow: 0 2rem 5rem rgba(0, 0, 0, 0.35);
  text-align: center;
}
.shield {
  display: grid;
  width: 3.25rem;
  height: 3.25rem;
  margin: 0 auto 1rem;
  place-items: center;
  border-radius: 1rem;
  color: var(--pg-theme-accent, #1c6f59);
  background: color-mix(in srgb, var(--pg-theme-accent, #1c6f59) 14%, #fff);
  font-size: 1.7rem;
  font-weight: 800;
  transition: color 0.2s ease, background 0.2s ease;
}
.shield.verified { color: #fff; background: var(--pg-theme-accent, #1c765c); }
.eyebrow { margin: 0 0 0.45rem; color: #667286; font-size: 0.7rem; font-weight: 750; letter-spacing: 0.13em; text-transform: uppercase; }
h1 { margin: 0; color: #16202e; font-size: clamp(1.55rem, 5vw, 2rem); line-height: 1.2; }
.description { max-width: 24rem; margin: 0.8rem auto 1.5rem; color: #626d7b; font-size: 0.93rem; line-height: 1.55; }
.notice { margin-bottom: 1.4rem; padding: 0.8rem 1rem; border-radius: 0.55rem; color: #5b6573; background: #f3f5f7; font-size: 0.8rem; line-height: 1.45; }
.slider-track {
  position: relative;
  height: 3.75rem;
  overflow: hidden;
  border: 1px solid #c9d0d8;
  border-radius: 999px;
  background: #edf0f4;
  box-shadow: inset 0 1px 3px rgba(20, 29, 42, 0.08);
  user-select: none;
}
.slider-fill { position: absolute; inset: 0 auto 0 0; background: linear-gradient(90deg, color-mix(in srgb, var(--pg-theme-accent, #b9e1d4) 55%, #fff), color-mix(in srgb, var(--pg-theme-accent, #b9e1d4) 30%, #fff)); }
.track-label { position: absolute; inset: 0; display: grid; place-items: center; padding-left: 2.5rem; color: #7b8694; font-size: 0.86rem; font-weight: 650; }
.slider-handle {
  position: absolute;
  top: 0.23rem;
  z-index: 2;
  display: grid;
  width: 3.2rem;
  height: 3.2rem;
  padding: 0;
  place-items: center;
  border: 0;
  border-radius: 50%;
  color: #fff;
  background: var(--pg-theme-accent, #1e715b);
  box-shadow: 0 0.3rem 0.8rem color-mix(in srgb, var(--pg-theme-accent, #1e715b) 28%, transparent);
  cursor: grab;
  touch-action: none;
  transition: box-shadow 0.16s ease, transform 0.16s ease, left 0.16s ease;
}
.slider-track.dragging .slider-handle { cursor: grabbing; transition: box-shadow 0.16s ease; box-shadow: 0 0.25rem 1rem color-mix(in srgb, var(--pg-theme-accent, #1e715b) 40%, transparent); }
.slider-track.verified { border-color: color-mix(in srgb, var(--pg-theme-accent, #1e715b) 45%, #c9d0d8); background: color-mix(in srgb, var(--pg-theme-accent, #1e715b) 12%, #edf0f4); }
.slider-track.verified .slider-fill { background: color-mix(in srgb, var(--pg-theme-accent, #1e715b) 18%, #edf0f4); }
.slider-track.verified .slider-handle { background: var(--pg-theme-accent, #17624e); cursor: default; }
.slider-handle:focus-visible { outline: 3px solid color-mix(in srgb, var(--pg-theme-accent, #20775f) 30%, transparent); outline-offset: 3px; }
.hint { margin: 0.85rem 0 0; color: #8a94a1; font-size: 0.74rem; }
footer { padding: 2rem 1rem; color: #768094; font-size: 0.72rem; text-align: center; }

/* Centered: baseline, card in the vertical middle of the page. */
.layout-centered .verification-page,
.verification-page { display: flex; flex-direction: column; }
.layout-centered .verification-card { margin: clamp(4rem, 12vh, 8rem) auto 0; }

/* Compact: a smaller, tighter card — kept as a modest variant rather than a
   dramatic reflow, since the slider needs enough width to stay usable. */
.layout-compact .verification-card { width: min(calc(100% - 1.5rem), 26rem); margin: clamp(3rem, 10vh, 6rem) auto 0; padding: 2rem 1.6rem 1.8rem; }
.layout-compact .shield { width: 2.7rem; height: 2.7rem; font-size: 1.4rem; }
.layout-compact .slider-track { height: 3.25rem; }
.layout-compact .slider-handle { width: 2.75rem; height: 2.75rem; }

/* Split: same centering as the baseline card, only a touch narrower. */
.layout-split .verification-card { margin: clamp(4rem, 12vh, 8rem) auto 0; width: min(calc(100% - 1.5rem), 27rem); }

@media (max-width: 36rem) {
  .site-header { height: 3.75rem; padding: 0 1rem; }
  .encrypted-label { display: none; }
  .verification-card,
  .layout-compact .verification-card,
  .layout-split .verification-card { margin: 8vh auto 0; width: min(calc(100% - 2rem), 31rem); padding: 2rem 1.2rem 1.7rem; border-radius: 1rem; }
}
@media (prefers-reduced-motion: reduce) {
  .slider-handle, .shield { transition: none; }
}
</style>
