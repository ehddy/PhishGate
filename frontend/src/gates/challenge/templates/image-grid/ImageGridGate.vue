<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateChallenge, GateDisplayContext, GateSubmission } from "../../../types";
import { imageGridCopy } from "./presentation";

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
  document.title = "Verify you're human";
});

const selected = ref<Set<number>>(new Set());
const brand = computed(() => props.displayContext.brand?.trim() || "Protected Service");
const gridChallenge = computed(() =>
  props.challenge?.kind === "image-grid" ? props.challenge : null,
);
const visualVariant = computed(() => gridChallenge.value?.variant ?? "blue");
const columns = computed(() => Math.round(Math.sqrt(gridChallenge.value?.cells.length ?? 9)));
const canSubmit = computed(() => selected.value.size > 0 && !props.completing);
const copy = computed(() => imageGridCopy());

function toggleCell(index: number): void {
  if (props.completing) return;
  if (selected.value.has(index)) {
    selected.value.delete(index);
  } else {
    selected.value.add(index);
  }
  // Reassign so the computed/reactive dependents pick up the mutation.
  selected.value = new Set(selected.value);
}

function submitSelection(): void {
  if (!canSubmit.value) return;
  const answer = Array.from(selected.value).sort((a, b) => a - b).join(",");
  emit("complete", { answer });
}
</script>

<template>
  <main
    class="grid-page"
    :class="[`variant-${visualVariant}`, `layout-${displayContext.layout_variant}`]"
    :data-variant-id="displayContext.variant_id"
  >
    <header aria-hidden="true">
      <div class="wordmark"><span>◆</span>{{ brand }}</div>
      <div class="secure-label"><i></i>{{ copy.protectedSession }}</div>
    </header>

    <section class="verification-card" aria-labelledby="grid-title">
      <p class="eyebrow">{{ copy.securityCheck }}</p>
      <h1 id="grid-title">{{ copy.verifyHuman }}</h1>
      <p class="instruction" aria-live="polite">
        {{ gridChallenge ? copy.selectSquares(gridChallenge.category_label) : copy.imageUnavailable }}
      </p>

      <div
        v-if="gridChallenge"
        class="cell-grid"
        :style="{ gridTemplateColumns: `repeat(${columns}, 1fr)` }"
        role="group"
        aria-label="Verification image squares"
      >
        <button
          v-for="(cell, index) in gridChallenge.cells"
          :key="index"
          type="button"
          class="cell"
          :class="{ selected: selected.has(index) }"
          :aria-pressed="selected.has(index)"
          :disabled="completing"
          @click="toggleCell(index)"
        >
          <img :src="cell" :alt="`Square ${index + 1}`" />
          <span class="check-mark" aria-hidden="true">✓</span>
        </button>
      </div>

      <p v-if="completionError" class="answer-error" role="alert">{{ completionError }}</p>
      <button type="button" class="submit-button" :disabled="!canSubmit" @click="submitSelection">
        <span v-if="completing" class="spinner" aria-hidden="true"></span>
        {{ completing ? copy.checking : copy.verifyContinue }}
      </button>

      <p class="privacy-copy">{{ copy.privacyCopy }}</p>
    </section>

    <footer aria-hidden="true"><span>{{ copy.privacy }}</span><i></i><span>{{ copy.help }}</span><i></i><span>{{ copy.security }}</span></footer>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(html), :global(body), :global(#app) { min-height: 100%; }
:global(body) { margin: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
button { font: inherit; }
/* Color comes from the challenge's own server-generated palette variant
   (blue/violet/mint, derived from PHISHGATE_SEED), kept separate
   from displayContext.theme_variant -- see custom-digit for why. */
.grid-page { --accent: #174ea6; --accent-dark: #0d3b82; --soft: #edf4ff; --ink: #14213a; display: flex; min-height: 100vh; flex-direction: column; color: var(--ink); background: radial-gradient(circle at 50% 30%, #fff 0, rgba(255,255,255,.72) 25%, transparent 52%), linear-gradient(145deg, var(--soft), #f7f9fc); }
.variant-violet { --accent: #6842a5; --accent-dark: #4c2d7d; --soft: #f0ebfa; }
.variant-mint { --accent: #176f60; --accent-dark: #0e5146; --soft: #e5f5f0; }
header { display: flex; min-height: 68px; align-items: center; justify-content: space-between; padding: 0 clamp(20px, 5vw, 70px); border-bottom: 1px solid rgba(52, 70, 98, .09); background: rgba(255, 255, 255, .7); }
.wordmark { display: flex; max-width: 55vw; align-items: center; gap: 10px; overflow: hidden; font-size: 15px; font-weight: 750; text-overflow: ellipsis; white-space: nowrap; }
.wordmark span { color: var(--accent); }
.secure-label { display: flex; align-items: center; gap: 8px; color: #68758a; font-size: 11px; }
.secure-label i { width: 7px; height: 7px; border-radius: 50%; background: #27916a; box-shadow: 0 0 0 4px rgba(39, 145, 106, .12); }
.verification-card { width: min(calc(100% - 30px), 420px); margin: auto; padding: 34px 34px 28px; border: 1px solid rgba(48, 68, 98, .11); border-radius: 18px; background: rgba(255, 255, 255, .97); box-shadow: 0 28px 65px rgba(37, 58, 91, .17), 0 3px 9px rgba(37, 58, 91, .07); text-align: center; }
.eyebrow { margin: 0 0 7px; color: var(--accent); font-size: 10px; font-weight: 800; letter-spacing: .14em; }
h1 { margin: 0; font-size: 25px; letter-spacing: -.035em; }
.instruction { margin: 12px auto 18px; color: #647087; font-size: 13px; line-height: 1.55; }
.instruction strong { color: var(--ink); text-transform: capitalize; }
.cell-grid { display: grid; gap: 6px; margin: 0 auto 16px; }
.cell { position: relative; padding: 0; overflow: hidden; border: 2px solid #d7deea; border-radius: 8px; background: var(--soft); cursor: pointer; aspect-ratio: 1; }
.cell img { display: block; width: 100%; height: 100%; }
.cell:hover:not(:disabled) { border-color: var(--accent); }
.cell:focus-visible { outline: 3px solid color-mix(in srgb, var(--accent) 24%, transparent); outline-offset: 2px; }
.cell.selected { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, var(--soft)); }
.cell .check-mark { position: absolute; top: 4px; right: 4px; display: grid; width: 20px; height: 20px; place-items: center; border-radius: 50%; color: #fff; background: var(--accent); font-size: 12px; font-weight: 700; opacity: 0; transform: scale(.6); transition: opacity .12s ease, transform .12s ease; }
.cell.selected .check-mark { opacity: 1; transform: scale(1); }
.cell:disabled { cursor: not-allowed; }
.answer-error { margin: 0 0 12px; color: #a72e28; font-size: 11px; }
.submit-button { display: flex; width: 100%; height: 48px; align-items: center; justify-content: center; gap: 9px; border: 0; border-radius: 8px; color: #fff; background: var(--accent); font-size: 13px; font-weight: 750; cursor: pointer; }
.submit-button:hover:not(:disabled) { background: var(--accent-dark); }
.submit-button:focus-visible { outline: 3px solid color-mix(in srgb, var(--accent) 24%, transparent); outline-offset: 3px; }
.submit-button:disabled { cursor: not-allowed; opacity: .48; }
.spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,.35); border-top-color: #fff; border-radius: 50%; animation: spin .7s linear infinite; }
.privacy-copy { margin: 16px 0 0; color: #9099a8; font-size: 10px; line-height: 1.45; }
footer { display: flex; min-height: 60px; align-items: center; justify-content: center; gap: 11px; color: #7e899a; font-size: 10px; }
footer i { width: 3px; height: 3px; border-radius: 50%; background: #9fa8b5; }
@keyframes spin { to { transform: rotate(360deg); } }

.layout-compact .verification-card { width: min(calc(100% - 24px), 360px); padding: 26px 24px 22px; }
.layout-split .verification-card { width: min(calc(100% - 30px), 380px); }

@media (max-width: 480px) {
  .grid-page { min-height: 100svh; }
  header { min-height: 60px; }
  .secure-label { font-size: 0; }
  .verification-card,
  .layout-compact .verification-card,
  .layout-split .verification-card { margin: auto 15px; width: auto; padding: 28px 22px 24px; }
  footer { min-height: 52px; }
}
@media (prefers-reduced-motion: reduce) { .spinner { animation: none; } .cell .check-mark { transition: none; } }
</style>
