<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateChallenge, GateDisplayContext, GateSubmission } from "../../../types";
import { customDigitCopy, customDigitInstruction } from "./presentation";

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
  document.title = "Security Check";
});

const answer = ref("");
const digitChallenge = computed(() =>
  props.challenge?.kind === "digit-image" ? props.challenge : null,
);
const brand = computed(() => props.displayContext.brand?.trim() || "Secure Access");
const digitCount = computed(() => {
  const configured = props.parameters.digit_count;
  return typeof configured === "number" && configured >= 4 && configured <= 8 ? configured : 5;
});
const visualVariant = computed(() => digitChallenge.value?.variant ?? "blue");
const canSubmit = computed(() => answer.value.length === digitCount.value && !props.completing);
const copy = computed(() => customDigitCopy());
const instruction = computed(() => customDigitInstruction(copy.value, digitCount.value, props.displayContext.copy_variant));

function keepDigitsOnly(event: Event): void {
  const input = event.target as HTMLInputElement;
  answer.value = input.value.replace(/\D/g, "").slice(0, digitCount.value);
}

function submitAnswer(): void {
  if (!canSubmit.value) return;
  emit("complete", { answer: answer.value });
}
</script>

<template>
  <main
    class="verification-page"
    :class="[`variant-${visualVariant}`, `layout-${displayContext.layout_variant}`]"
    :data-variant-id="displayContext.variant_id"
  >
    <header aria-hidden="true">
      <div class="wordmark"><span>◆</span>{{ brand }}</div>
      <div class="secure-label"><i></i>{{ copy.protectedSession }}</div>
    </header>

    <section class="verification-card" aria-labelledby="verification-title">
      <div class="robot-icon" aria-hidden="true">
        <i></i><span>●</span><span>●</span><b></b>
      </div>
      <p class="eyebrow">{{ copy.securityCheck }}</p>
      <h1 id="verification-title">{{ copy.verifyHuman }}</h1>
      <p class="instruction">{{ instruction }}</p>

      <div class="captcha-frame">
        <img
          v-if="digitChallenge?.image_data_url"
          :src="digitChallenge.image_data_url"
          :alt="`${digitCount}-digit verification image`"
          width="320"
          height="100"
        />
        <div v-else class="captcha-missing" role="alert">{{ copy.imageUnavailable }}</div>
      </div>

      <form @submit.prevent="submitAnswer">
        <label for="digit-answer">{{ copy.verificationCode }}</label>
        <input
          id="digit-answer"
          :value="answer"
          :maxlength="digitCount"
          inputmode="numeric"
          pattern="[0-9]*"
          autocomplete="off"
          :placeholder="copy.enterDigits"
          :aria-invalid="Boolean(completionError)"
          :disabled="completing"
          @input="keepDigitsOnly"
        />
        <p v-if="completionError" class="answer-error" role="alert">{{ completionError }}</p>
        <button type="submit" :disabled="!canSubmit">
          <span v-if="completing" class="spinner" aria-hidden="true"></span>
          {{ completing ? copy.checking : copy.verifyContinue }}
        </button>
      </form>

      <p class="privacy-copy">{{ copy.privacyCopy }}</p>
    </section>

    <footer aria-hidden="true"><span>{{ copy.privacy }}</span><i></i><span>{{ copy.help }}</span><i></i><span>{{ copy.security }}</span></footer>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(html), :global(body), :global(#app) { min-height: 100%; }
:global(body) { margin: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
button, input { font: inherit; }
/* Color here comes from the challenge's own server-generated palette
   variant (blue/violet/mint, derived from PHISHGATE_SEED), not from
   displayContext.theme_variant: the two variant systems are deliberately
   kept separate so the actual problem/answer stays independent of the
   presentation seed. layout_variant (below) only affects sizing/position. */
.verification-page { --accent: #174ea6; --accent-dark: #0d3b82; --soft: #edf4ff; --ink: #14213a; display: flex; min-height: 100vh; flex-direction: column; color: var(--ink); background: radial-gradient(circle at 50% 30%, #fff 0, rgba(255,255,255,.72) 25%, transparent 52%), linear-gradient(145deg, var(--soft), #f7f9fc); }
.variant-violet { --accent: #6842a5; --accent-dark: #4c2d7d; --soft: #f0ebfa; }
.variant-mint { --accent: #176f60; --accent-dark: #0e5146; --soft: #e5f5f0; }
header { display: flex; min-height: 68px; align-items: center; justify-content: space-between; padding: 0 clamp(20px, 5vw, 70px); border-bottom: 1px solid rgba(52, 70, 98, .09); background: rgba(255, 255, 255, .7); }
.wordmark { display: flex; max-width: 55vw; align-items: center; gap: 10px; overflow: hidden; font-size: 15px; font-weight: 750; text-overflow: ellipsis; white-space: nowrap; }
.wordmark span { color: var(--accent); }
.secure-label { display: flex; align-items: center; gap: 8px; color: #68758a; font-size: 11px; }
.secure-label i { width: 7px; height: 7px; border-radius: 50%; background: #27916a; box-shadow: 0 0 0 4px rgba(39, 145, 106, .12); }
.verification-card { width: min(calc(100% - 30px), 440px); margin: auto; padding: 36px 39px 30px; border: 1px solid rgba(48, 68, 98, .11); border-radius: 18px; background: rgba(255, 255, 255, .97); box-shadow: 0 28px 65px rgba(37, 58, 91, .17), 0 3px 9px rgba(37, 58, 91, .07); text-align: center; }
.robot-icon { position: relative; width: 48px; height: 42px; margin: 0 auto 15px; border: 3px solid var(--accent); border-radius: 10px; }
.robot-icon i { position: absolute; top: -12px; left: 50%; width: 3px; height: 10px; background: var(--accent); transform: translateX(-50%); }
.robot-icon i::before { position: absolute; top: -4px; left: -3px; width: 9px; height: 9px; border-radius: 50%; background: var(--accent); content: ""; }
.robot-icon span { position: absolute; top: 12px; color: var(--accent); font-size: 9px; }
.robot-icon span:nth-of-type(1) { left: 10px; }
.robot-icon span:nth-of-type(2) { right: 10px; }
.robot-icon b { position: absolute; right: 11px; bottom: 7px; left: 11px; height: 3px; border-radius: 2px; background: var(--accent); }
.eyebrow { margin: 0 0 7px; color: var(--accent); font-size: 10px; font-weight: 800; letter-spacing: .14em; }
h1 { margin: 0; font-size: 27px; letter-spacing: -.035em; }
.instruction { margin: 12px auto 20px; color: #647087; font-size: 13px; line-height: 1.55; }
.captcha-frame { display: grid; min-height: 102px; place-items: center; overflow: hidden; border: 1px solid #d7deea; border-radius: 10px; background: var(--soft); }
.captcha-frame img { display: block; width: 100%; height: auto; object-fit: cover; }
.captcha-missing { color: #a3302c; font-size: 12px; }
form { margin-top: 20px; text-align: left; }
label { display: block; margin: 0 0 7px 2px; color: #445169; font-size: 12px; font-weight: 700; }
input { width: 100%; height: 48px; padding: 0 15px; border: 1px solid #b9c2d0; border-radius: 8px; color: #1d2a3d; background: #fff; font-size: 17px; letter-spacing: .22em; outline: none; text-align: center; }
input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 16%, transparent); }
input[aria-invalid="true"] { border-color: #c23b33; }
.answer-error { margin: 8px 2px 0; color: #a72e28; font-size: 11px; }
button { display: flex; width: 100%; height: 48px; align-items: center; justify-content: center; gap: 9px; margin-top: 14px; border: 0; border-radius: 8px; color: #fff; background: var(--accent); font-size: 13px; font-weight: 750; cursor: pointer; }
button:hover:not(:disabled) { background: var(--accent-dark); }
button:focus-visible { outline: 3px solid color-mix(in srgb, var(--accent) 24%, transparent); outline-offset: 3px; }
button:disabled { cursor: not-allowed; opacity: .48; }
.spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,.35); border-top-color: #fff; border-radius: 50%; animation: spin .7s linear infinite; }
.privacy-copy { margin: 19px 0 0; color: #9099a8; font-size: 10px; line-height: 1.45; }
footer { display: flex; min-height: 60px; align-items: center; justify-content: center; gap: 11px; color: #7e899a; font-size: 10px; }
footer i { width: 3px; height: 3px; border-radius: 50%; background: #9fa8b5; }
@keyframes spin { to { transform: rotate(360deg); } }

.layout-compact .verification-card { width: min(calc(100% - 24px), 380px); padding: 28px 26px 24px; }
.layout-split .verification-card { width: min(calc(100% - 30px), 400px); }

@media (max-width: 520px) {
  .verification-page { min-height: 100svh; }
  header { min-height: 60px; }
  .secure-label { font-size: 0; }
  .verification-card,
  .layout-compact .verification-card,
  .layout-split .verification-card { margin: auto 15px; width: auto; padding: 30px 24px 26px; }
  footer { min-height: 52px; }
}
@media (prefers-reduced-motion: reduce) { .spinner { animation: none; } }
</style>
