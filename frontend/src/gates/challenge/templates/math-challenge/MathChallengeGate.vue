<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateChallenge, GateDisplayContext, GateSubmission } from "../../../types";
import { mathChallengeCopy, mathChallengeInstruction } from "./presentation";

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

const answer = ref("");
const brand = computed(() => props.displayContext.brand?.trim() || "Protected Service");
const mathChallenge = computed(() =>
  props.challenge?.kind === "math-problem" ? props.challenge : null,
);
const visualVariant = computed(() => mathChallenge.value?.variant ?? "blue");
const canSubmit = computed(() => answer.value.length > 0 && !props.completing);
const copy = computed(() => mathChallengeCopy());
const instruction = computed(() => mathChallengeInstruction(copy.value, props.displayContext.copy_variant));

function keepWholeNumber(event: Event): void {
  const input = event.target as HTMLInputElement;
  answer.value = input.value.replace(/\D/g, "").slice(0, 3);
}

function submitAnswer(): void {
  if (!canSubmit.value) return;
  emit("complete", { answer: answer.value });
}
</script>

<template>
  <main
    class="math-page"
    :class="[`variant-${visualVariant}`, `layout-${displayContext.layout_variant}`]"
    :data-variant-id="displayContext.variant_id"
  >
    <div class="background-grid" aria-hidden="true"><i></i><i></i><i></i></div>

    <header aria-hidden="true">
      <div class="wordmark"><span>✓</span>{{ brand }}</div>
      <div class="security-status"><i></i>{{ copy.secureConnection }}</div>
    </header>

    <section class="challenge-card" aria-labelledby="math-title">
      <div class="shield-icon" aria-hidden="true">✓</div>
      <p class="eyebrow">{{ copy.humanVerification }}</p>
      <h1 id="math-title">{{ copy.verificationRequired }}</h1>
      <p class="instruction">{{ instruction }}</p>

      <div class="problem-panel">
        <span class="problem-label">{{ copy.solveEquation }}</span>
        <strong v-if="mathChallenge" aria-live="polite">{{ mathChallenge.prompt }}</strong>
        <strong v-else class="unavailable" role="alert">{{ copy.problemUnavailable }}</strong>

        <form @submit.prevent="submitAnswer">
          <label for="math-answer">{{ copy.yourAnswer }}</label>
          <input
            id="math-answer"
            :value="answer"
            inputmode="numeric"
            pattern="[0-9]*"
            maxlength="3"
            autocomplete="off"
            :placeholder="copy.enterAnswer"
            :aria-invalid="Boolean(completionError)"
            :disabled="completing"
            @input="keepWholeNumber"
          />
          <p v-if="completionError" class="answer-error" role="alert">{{ completionError }}</p>
          <button type="submit" :disabled="!canSubmit">
            <span v-if="completing" class="spinner" aria-hidden="true"></span>
            {{ completing ? copy.checking : copy.verifyContinue }}
          </button>
        </form>
      </div>

      <p class="protection-copy">{{ copy.protectionCopy }}</p>
    </section>

    <footer aria-hidden="true"><span>{{ copy.privacy }}</span><i></i><span>{{ copy.security }}</span><i></i><span>{{ copy.help }}</span></footer>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(html), :global(body), :global(#app) { min-height: 100%; }
:global(body) { margin: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
button, input { font: inherit; }
/* Color comes from the challenge's own server-generated palette variant
   (blue/violet/mint, derived from PHISHGATE_SEED), kept separate
   from displayContext.theme_variant -- see custom-digit for why. */
.math-page { --accent: #111827; --button: #111; --glow: rgba(36, 91, 154, .24); position: relative; display: flex; min-height: 100vh; flex-direction: column; overflow: hidden; color: #192234; background: linear-gradient(135deg, #18304a, #3f6177 46%, #b89e7b); }
.variant-violet { --accent: #4d326e; --button: #432763; --glow: rgba(91, 55, 129, .27); background: linear-gradient(135deg, #2b273d, #665575 48%, #b89a8c); }
.variant-mint { --accent: #174f49; --button: #123f3a; --glow: rgba(27, 106, 93, .25); background: linear-gradient(135deg, #183b3b, #50756d 46%, #b8a47f); }
.background-grid { position: absolute; inset: 0; opacity: .38; background: linear-gradient(90deg, transparent 49.7%, rgba(255,255,255,.08) 50%, transparent 50.3%), linear-gradient(rgba(255,255,255,.06) 1px, transparent 1px); background-size: 100% 100%, 100% 42px; }
.background-grid::before, .background-grid::after { position: absolute; bottom: -12vh; width: 43vw; height: 64vh; border: 1px solid rgba(255,255,255,.18); background: rgba(18, 28, 40, .22); box-shadow: 0 0 60px rgba(0,0,0,.16); content: ""; transform: perspective(700px) rotateX(58deg); }
.background-grid::before { left: 2vw; }
.background-grid::after { right: 2vw; }
.background-grid i { position: absolute; top: 14%; width: 10px; height: 10px; border-radius: 50%; background: rgba(255,255,255,.75); box-shadow: 0 0 18px rgba(255,255,255,.55); }
.background-grid i:nth-child(1) { left: 17%; }
.background-grid i:nth-child(2) { left: 50%; }
.background-grid i:nth-child(3) { right: 17%; }
header { position: relative; z-index: 2; display: flex; min-height: 68px; align-items: center; justify-content: space-between; padding: 0 clamp(20px, 5vw, 70px); color: #fff; background: rgba(14, 25, 38, .32); backdrop-filter: blur(12px); }
.wordmark { display: flex; max-width: 55vw; align-items: center; gap: 10px; overflow: hidden; font-size: 14px; font-weight: 750; text-overflow: ellipsis; white-space: nowrap; }
.wordmark span { display: grid; width: 27px; height: 27px; place-items: center; border: 1px solid rgba(255,255,255,.55); border-radius: 8px; }
.security-status { display: flex; align-items: center; gap: 8px; color: rgba(255,255,255,.78); font-size: 11px; }
.security-status i { width: 7px; height: 7px; border-radius: 50%; background: #65d39c; box-shadow: 0 0 0 4px rgba(101, 211, 156, .16); }
.challenge-card { position: relative; z-index: 2; width: min(calc(100% - 30px), 520px); margin: auto; padding: 39px 47px 32px; border: 1px solid rgba(255,255,255,.55); border-radius: 19px; background: rgba(247, 248, 250, .91); box-shadow: 0 32px 80px rgba(4, 12, 22, .32), 0 0 70px var(--glow); backdrop-filter: blur(17px); text-align: center; }
.shield-icon { display: grid; width: 42px; height: 42px; margin: 0 auto 14px; place-items: center; border-radius: 50% 50% 45% 45%; color: #fff; background: var(--accent); font-size: 18px; font-weight: 800; }
.eyebrow { margin: 0 0 7px; color: #657084; font-size: 9px; font-weight: 800; letter-spacing: .16em; }
h1 { margin: 0; color: #172033; font-size: 28px; letter-spacing: -.035em; text-transform: capitalize; }
.instruction { margin: 11px 0 22px; color: #626c7d; font-size: 13px; line-height: 1.55; }
.problem-panel { padding: 23px 27px 26px; border: 1px solid rgba(88, 101, 122, .14); border-radius: 13px; background: rgba(255,255,255,.8); box-shadow: inset 0 1px 0 #fff, 0 5px 14px rgba(39, 50, 68, .06); }
.problem-label { display: block; margin-bottom: 8px; color: #858d9b; font-size: 10px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.problem-panel > strong { display: block; margin-bottom: 22px; color: var(--accent); font-family: Georgia, "Times New Roman", serif; font-size: 34px; letter-spacing: .025em; }
.problem-panel > .unavailable { color: #a62f2a; font-family: inherit; font-size: 14px; }
form { text-align: left; }
label { display: block; margin: 0 0 7px 2px; color: #4f5a6c; font-size: 11px; font-weight: 700; }
input { width: 100%; height: 47px; padding: 0 14px; border: 1px solid #bbc3cf; border-radius: 7px; background: #fff; color: #172033; font-size: 16px; outline: none; text-align: center; }
input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 16%, transparent); }
input[aria-invalid="true"] { border-color: #bd3932; }
.answer-error { margin: 8px 2px 0; color: #a72e28; font-size: 11px; }
button { display: flex; width: 100%; height: 47px; align-items: center; justify-content: center; gap: 9px; margin-top: 13px; border: 0; border-radius: 7px; color: #fff; background: var(--button); font-size: 13px; font-weight: 750; cursor: pointer; }
button:hover:not(:disabled) { filter: brightness(1.16); }
button:focus-visible { outline: 3px solid color-mix(in srgb, var(--accent) 28%, transparent); outline-offset: 3px; }
button:disabled { cursor: not-allowed; opacity: .48; }
.spinner { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,.35); border-top-color: #fff; border-radius: 50%; animation: spin .7s linear infinite; }
.protection-copy { margin: 24px 12px 0; color: #7d8695; font-size: 10px; line-height: 1.5; }
footer { position: relative; z-index: 2; display: flex; min-height: 58px; align-items: center; justify-content: center; gap: 11px; color: rgba(255,255,255,.7); font-size: 10px; }
footer i { width: 3px; height: 3px; border-radius: 50%; background: rgba(255,255,255,.65); }
@keyframes spin { to { transform: rotate(360deg); } }

.layout-compact .challenge-card { width: min(calc(100% - 24px), 420px); padding: 30px 32px 26px; }
.layout-split .challenge-card { width: min(calc(100% - 30px), 470px); }

@media (max-width: 540px) {
  .math-page { min-height: 100svh; }
  header { min-height: 60px; }
  .security-status { font-size: 0; }
  .challenge-card,
  .layout-compact .challenge-card,
  .layout-split .challenge-card { margin: auto 15px; width: auto; padding: 31px 23px 27px; }
  .problem-panel { padding: 21px 19px 23px; }
  footer { min-height: 50px; }
}
@media (prefers-reduced-motion: reduce) { .spinner { animation: none; } }
</style>
