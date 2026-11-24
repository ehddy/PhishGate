<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import type { GateDisplayContext } from "../../../types";
import { holdCopy, holdNotice } from "./presentation";


const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();

const holdButton = ref<HTMLButtonElement | null>(null);
const progress = ref(0);
const holding = ref(false);
const releasedEarly = ref(false);
const verified = ref(false);
const copy = computed(() => holdCopy());
const notice = computed(() => holdNotice(copy.value, props.displayContext.copy_variant));
const holdDurationMs = computed(() => {
  const configured = props.parameters?.hold_duration_ms;
  return typeof configured === "number" && configured >= 1000 && configured <= 10000
    ? Math.round(configured)
    : 3000;
});
const holdDurationSeconds = computed(() => holdDurationMs.value / 1000);
const progressStyle = computed(() => ({ width: `${progress.value}%` }));

let activePointerId: number | null = null;
let animationFrame = 0;
let holdStartedAt = 0;

onMounted(() => {
  document.title = "Secure document verification";
  window.addEventListener("blur", cancelHold);
});

onBeforeUnmount(() => {
  window.removeEventListener("blur", cancelHold);
  window.cancelAnimationFrame(animationFrame);
});

function updateProgress(timestamp: number): void {
  if (!holding.value || verified.value) {
    return;
  }

  const elapsed = timestamp - holdStartedAt;
  progress.value = Math.min(100, (elapsed / holdDurationMs.value) * 100);
  if (progress.value >= 100) {
    holding.value = false;
    verified.value = true;
    const pointerId = activePointerId;
    activePointerId = null;
    if (pointerId !== null && holdButton.value?.hasPointerCapture(pointerId)) {
      holdButton.value.releasePointerCapture(pointerId);
    }
    emit("complete");
    return;
  }

  animationFrame = window.requestAnimationFrame(updateProgress);
}

function startHold(event: PointerEvent): void {
  if (verified.value || holding.value || (event.pointerType === "mouse" && event.button !== 0)) {
    return;
  }

  releasedEarly.value = false;
  progress.value = 0;
  holding.value = true;
  activePointerId = event.pointerId;
  holdStartedAt = performance.now();
  holdButton.value?.setPointerCapture(event.pointerId);
  animationFrame = window.requestAnimationFrame(updateProgress);
}

function cancelHold(): void {
  if (!holding.value || verified.value) {
    return;
  }

  window.cancelAnimationFrame(animationFrame);
  holding.value = false;
  releasedEarly.value = true;
  progress.value = 0;
  activePointerId = null;
}
</script>

<template>
  <main
    class="hold-page"
    :class="`layout-${displayContext.layout_variant}`"
    :data-variant-id="displayContext.variant_id"
  >
    <header class="document-header">
      <div class="document-brand">
        <span class="document-mark" aria-hidden="true">▤</span>
        <span>{{ displayContext.brand || copy.secureDocument }}</span>
      </div>
      <span class="secure-label">Secure access</span>
    </header>

    <section class="verification-card" aria-labelledby="hold-title">
      <div class="file-icon" :class="{ verified }" aria-hidden="true">
        {{ verified ? "✓" : "▧" }}
      </div>
      <h1 id="hold-title">{{ verified ? copy.verificationComplete : copy.verifyIdentity }}</h1>
      <p class="document-message">
        {{ verified ? copy.openingDocument : copy.receivedDocument }}
      </p>

      <div v-if="notice && !verified" class="notice">{{ notice }}</div>

      <div class="hold-panel" :class="{ holding, verified, failed: releasedEarly }">
        <p class="hold-heading">
          {{ verified ? copy.verificationComplete : copy.pressAndHold }}
        </p>
        <button
          ref="holdButton"
          type="button"
          class="hold-button"
          :disabled="verified"
          :aria-pressed="holding"
          @pointerdown.prevent="startHold"
          @pointerup.prevent="cancelHold"
          @pointercancel="cancelHold"
          @lostpointercapture="cancelHold"
          @contextmenu.prevent
        >
          <span aria-hidden="true">{{ verified ? "✓" : holding ? "●" : "○" }}</span>
          <span>
            {{ verified ? copy.verificationComplete : copy.holdFor(holdDurationSeconds) }}
          </span>
        </button>

        <div
          class="progress-track"
          role="progressbar"
          :aria-label="copy.pressAndHold"
          :aria-valuenow="Math.round(progress)"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <span class="progress-fill" :style="progressStyle"></span>
        </div>

        <p class="hold-status" aria-live="polite">
          {{ releasedEarly ? copy.releaseRetry : copy.keepHolding }}
        </p>
      </div>

      <footer>{{ copy.footer }}</footer>
    </section>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(body) {
  margin: 0;
  color: #24282f;
  background: #f3f5f8;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button { font: inherit; }
.hold-page { min-height: 100vh; background: linear-gradient(145deg, #f7f8fb, #edf1f6); }
.document-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 4.25rem;
  padding: 0 2rem;
  border-bottom: 1px solid #dfe4eb;
  background: rgba(255, 255, 255, 0.94);
}
.document-brand { display: flex; align-items: center; gap: 0.7rem; color: #343b46; font-size: 0.92rem; font-weight: 680; }
.document-mark {
  display: grid;
  width: 2rem;
  height: 2rem;
  place-items: center;
  border-radius: 0.42rem;
  color: #fff;
  background: var(--pg-theme-accent, #6655c7);
  font-size: 1rem;
}
.secure-label { color: #788290; font-size: 0.75rem; }
.verification-card {
  width: min(calc(100% - 2rem), 28rem);
  margin: 9vh auto 3rem;
  padding: 2.35rem 2.2rem 1.4rem;
  border: 1px solid #dce1e8;
  border-radius: 0.45rem;
  background: #fff;
  box-shadow: 0 1.4rem 3.5rem rgba(45, 55, 72, 0.14);
  text-align: center;
}
.file-icon {
  display: grid;
  width: 3.2rem;
  height: 3.2rem;
  margin: 0 auto 1rem;
  place-items: center;
  border-radius: 0.55rem;
  color: #fff;
  background: var(--pg-theme-accent, #6655c7);
  font-size: 1.45rem;
  transition: background 0.2s ease;
}
.file-icon.verified { background: #238555; }
h1 { margin: 0; color: #20242b; font-size: clamp(1.55rem, 5vw, 1.9rem); line-height: 1.2; }
.document-message { margin: 0.7rem 0 1.35rem; color: #606a77; font-size: 0.92rem; }
.notice { margin-bottom: 1rem; padding: 0.72rem 0.85rem; border-radius: 0.35rem; color: #596371; background: #f5f6f8; font-size: 0.78rem; line-height: 1.45; }
.hold-panel { padding: 1.15rem; border: 1px solid #dce1e7; border-radius: 0.32rem; background: #fbfcfd; }
.hold-panel.holding { border-color: color-mix(in srgb, var(--pg-theme-accent, #1473c9) 55%, #dce1e7); }
.hold-panel.verified { border-color: #9bcbb3; background: #f4fbf7; }
.hold-panel.failed { border-color: #e3b2ad; }
.hold-heading { margin: 0 0 0.85rem; color: #535c68; font-size: 0.9rem; }
.hold-button {
  display: flex;
  width: 100%;
  min-height: 3rem;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  border: 0;
  border-radius: 0.18rem;
  color: #fff;
  background: var(--pg-theme-accent, #1473c9);
  box-shadow: 0 0.2rem 0.55rem rgba(25, 80, 145, 0.18);
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 650;
  touch-action: none;
  user-select: none;
}
.hold-button:active, .hold-panel.holding .hold-button { filter: brightness(0.88); transform: translateY(1px); }
.hold-button:focus-visible { outline: 3px solid color-mix(in srgb, var(--pg-theme-accent, #1473c9) 32%, transparent); outline-offset: 3px; }
.hold-button:disabled { background: #238555; cursor: default; opacity: 1; }
.progress-track { height: 0.32rem; margin-top: 0.8rem; overflow: hidden; border-radius: 999px; background: #e2e6eb; }
.progress-fill { display: block; height: 100%; border-radius: inherit; background: var(--pg-theme-accent, #1473c9); transition: width 0.04s linear; }
.hold-panel.verified .progress-fill { background: #238555; }
.hold-status { min-height: 1.05rem; margin: 0.65rem 0 0; color: #7b8490; font-size: 0.71rem; }
.hold-panel.failed .hold-status { color: #a4473e; }
footer { margin-top: 1.35rem; color: #8a929e; font-size: 0.7rem; }
.layout-compact .verification-card { margin-top: 5vh; padding-block: 1.8rem 1.2rem; }
/* Keep the card centred in split (margin-inline: auto). The earlier
   margin-right-only rule left margin-left:auto, pushing the card to the right
   edge. */
.layout-split .verification-card { margin-inline: auto; }
@media (max-width: 40rem) {
  .document-header { height: 3.7rem; padding: 0 1rem; }
  .verification-card { margin-top: 5vh; padding: 1.8rem 1.2rem 1.2rem; }
}
</style>
