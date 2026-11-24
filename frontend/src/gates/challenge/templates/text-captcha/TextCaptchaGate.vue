<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateChallenge, GateDisplayContext, GateSubmission } from "../../../types";
import { textCaptchaCopy, textCaptchaInstruction } from "./presentation";

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

const answer = ref("");
const textChallenge = computed(() =>
  props.challenge?.kind === "text-image" ? props.challenge : null,
);
const brand = computed(() => props.displayContext.brand?.trim() || "Secure Access");
const length = computed(() => {
  const configured = props.parameters.text_length;
  return typeof configured === "number" && configured >= 4 && configured <= 8 ? configured : 6;
});
const visualVariant = computed(() => textChallenge.value?.variant ?? "blue");
const canSubmit = computed(() => answer.value.length === length.value && !props.completing);
const copy = computed(() => textCaptchaCopy());
const instruction = computed(() => textCaptchaInstruction(copy.value, props.displayContext.copy_variant));

function keepAlnumOnly(event: Event): void {
  const input = event.target as HTMLInputElement;
  answer.value = input.value.replace(/[^A-Za-z0-9]/g, "").toUpperCase().slice(0, length.value);
}

function submitAnswer(): void {
  if (!canSubmit.value) return;
  emit("complete", { answer: answer.value });
}
</script>

<template>
  <main
    class="text-captcha-page"
    :class="[`variant-${visualVariant}`, `layout-${displayContext.layout_variant}`]"
    :data-variant-id="displayContext.variant_id"
  >
    <section class="verification-card" aria-labelledby="text-captcha-title">
      <header class="card-head">
        <span class="badge" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.9">
            <path d="M12 2l8 3v6c0 5-3.4 8.3-8 11-4.6-2.7-8-6-8-11V5z" stroke-linejoin="round" />
          </svg>
        </span>
        <span class="brand">{{ brand }}</span>
      </header>

      <p class="eyebrow">{{ copy.eyebrow }}</p>
      <h1 id="text-captcha-title">{{ copy.heading }}</h1>
      <p class="instruction">{{ instruction }}</p>

      <div class="captcha-frame">
        <img
          v-if="textChallenge?.image_data_url"
          :src="textChallenge.image_data_url"
          :alt="`${length}-character verification image`"
          width="360"
          height="110"
        />
        <div v-else class="captcha-missing" role="alert">{{ copy.imageUnavailable }}</div>
      </div>

      <form @submit.prevent="submitAnswer">
        <label for="text-answer">{{ copy.inputLabel }} <small>· {{ copy.caseNote }}</small></label>
        <input
          id="text-answer"
          :value="answer"
          :maxlength="length"
          autocomplete="off"
          autocapitalize="characters"
          spellcheck="false"
          :placeholder="copy.placeholder"
          :aria-invalid="Boolean(completionError)"
          :disabled="completing"
          @input="keepAlnumOnly"
        />
        <p v-if="completionError" class="answer-error" role="alert">{{ completionError }}</p>
        <button type="submit" :disabled="!canSubmit">
          <span v-if="completing" class="spinner" aria-hidden="true"></span>
          {{ completing ? copy.checking : copy.verifyContinue }}
        </button>
      </form>
    </section>

    <footer aria-hidden="true"><span>{{ copy.privacy }}</span><i></i><span>{{ copy.help }}</span><i></i><span>{{ copy.security }}</span></footer>
  </main>
</template>

<style scoped>
* { box-sizing: border-box; }
.text-captcha-page {
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
  width: min(100%, 25rem);
  padding: 1.8rem 1.9rem 1.6rem;
  border: 1px solid rgba(20, 33, 58, 0.1);
  border-radius: 0.8rem;
  background: #fff;
  box-shadow: 0 1.5rem 3.6rem rgba(20, 33, 58, 0.15);
}
.card-head { display: flex; align-items: center; gap: 0.55rem; margin-bottom: 1.2rem; }
.badge {
  display: grid;
  width: 1.9rem;
  height: 1.9rem;
  place-items: center;
  border-radius: 0.45rem;
  color: #fff;
  background: var(--accent);
}
.brand { color: #27324a; font-size: 0.92rem; font-weight: 700; }

.eyebrow {
  margin: 0 0 0.3rem;
  color: var(--accent);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.13em;
  text-transform: uppercase;
}
h1 { margin: 0; color: #16202e; font-size: 1.3rem; line-height: 1.25; }
.instruction { margin: 0.55rem 0 1.25rem; color: #4a5568; font-size: 0.9rem; line-height: 1.45; }

.captcha-frame {
  display: grid;
  place-items: center;
  padding: 0.7rem;
  border: 1px solid rgba(20, 33, 58, 0.12);
  border-radius: 0.5rem;
  background: var(--soft);
}
.captcha-frame img { width: 100%; max-width: 360px; height: auto; border-radius: 0.3rem; }
.captcha-missing { padding: 2rem 1rem; color: #a7442f; font-size: 0.85rem; text-align: center; }

form { margin-top: 1.2rem; }
label { display: block; margin: 0 0 0.5rem 0.1rem; color: #445169; font-size: 0.78rem; font-weight: 700; }
label small { color: #8a93a3; font-weight: 500; }
input {
  width: 100%;
  height: 3rem;
  padding: 0 0.95rem;
  border: 1px solid #b9c2d0;
  border-radius: 0.5rem;
  color: #1d2a3d;
  background: #fff;
  font-size: 1.1rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  outline: none;
}
input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 16%, transparent); }
input[aria-invalid="true"] { border-color: #c23b33; }
.answer-error { margin: 0.5rem 0.1rem 0; color: #a72e28; font-size: 0.72rem; }

button {
  display: flex;
  width: 100%;
  height: 3rem;
  margin-top: 0.9rem;
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

.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

footer { display: flex; gap: 0.7rem; margin-top: 1.4rem; color: #8a93a3; font-size: 0.72rem; }
footer i { width: 3px; height: 3px; border-radius: 50%; background: #aab1bc; }

.layout-compact .verification-card { width: min(100%, 22rem); padding: 1.5rem 1.6rem 1.3rem; }
.layout-split .verification-card { width: min(100%, 25rem); }
</style>
