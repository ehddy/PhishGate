<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateDisplayContext } from "../../../types";
import { cloudflareCopy, cloudflareInstruction } from "./presentation";


const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();
const state = ref<"idle" | "checking" | "verified">("idle");
const brand = computed(() => props.displayContext.brand?.trim() || null);
const copy = computed(() => cloudflareCopy());
const heading = computed(() => `${brand.value ?? "This website"} ${copy.value.headingSuffix}`);
const instruction = computed(() => cloudflareInstruction(copy.value, props.displayContext.copy_variant));
const showFooter = computed(() => props.displayContext.copy_variant !== "concise");

onMounted(() => {
  document.title = "Just a moment...";
});

function verifyHuman(): void {
  if (state.value !== "idle") return;
  state.value = "checking";
  window.setTimeout(() => {
    state.value = "verified";
    emit("complete");
  }, 1400);
}
</script>

<template>
  <main class="challenge-page" :class="`layout-${displayContext.layout_variant}`" :data-variant-id="displayContext.variant_id">
    <section class="verify-shell">
      <div class="message-block">
        <h1>{{ heading }}</h1>
        <p v-if="instruction" class="status-copy">{{ instruction }}</p>
      </div>

      <button
        class="turnstile-widget"
        type="button"
        role="checkbox"
        :aria-checked="state === 'verified'"
        :aria-busy="state === 'checking'"
        :disabled="state !== 'idle'"
        @click="verifyHuman"
      >
        <span class="control" :class="state" aria-hidden="true">
          <span v-if="state === 'checking'" class="spinner"></span>
          <span v-else-if="state === 'verified'" class="checkmark">✓</span>
        </span>
        <span class="control-label">
          {{ state === "checking" ? copy.verifying : state === "verified" ? copy.success : copy.verify }}
        </span>

        <span class="provider" aria-hidden="true">
          <span class="cloud-mark"><i></i><i></i><i></i></span>
          <strong>CLOUDFLARE</strong>
          <small>{{ copy.privacy }} · {{ copy.help }}</small>
        </span>
      </button>

      <p class="live-status" aria-live="polite">
        {{ state === "checking" ? copy.statusChecking : copy.statusIdle }}
      </p>

      <div v-if="showFooter" class="divider"></div>
      <footer v-if="showFooter">
        <span>{{ copy.rayIdLabel }}: <strong>local-research</strong></span>
        <span>{{ copy.performanceBy }} <strong>Cloudflare</strong></span>
      </footer>
    </section>
  </main>
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  color: #313131;
  background: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

button {
  font: inherit;
}

/* This widget stays a fixed, real-world Cloudflare orange regardless of
   theme_variant: the pattern being reproduced is a specific third-party
   provider's own branding, not the protected site's brand color. */
.challenge-page {
  min-height: 100vh;
  background: #ffffff;
}

.message-block h1 {
  margin: 0 0 0.65rem;
  color: #313131;
  font-weight: 500;
  letter-spacing: -0.025em;
  line-height: 1.25;
}

.message-block p {
  margin: 0;
  color: #595959;
  line-height: 1.6;
}

.turnstile-widget {
  display: grid;
  grid-template-columns: 2rem minmax(0, 1fr) 6.7rem;
  align-items: center;
  min-height: 5rem;
  padding: 0.7rem 0.8rem 0.7rem 0.95rem;
  border: 1px solid #d7d7d7;
  border-radius: 0.18rem;
  color: #222;
  background: #fafafa;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  text-align: left;
}

.turnstile-widget:hover:not(:disabled) {
  border-color: #b9b9b9;
  background: #f7f7f7;
}

.turnstile-widget:focus-visible {
  outline: 3px solid rgba(0, 102, 204, 0.25);
  outline-offset: 2px;
}

.turnstile-widget:disabled {
  cursor: wait;
  opacity: 1;
}

.control {
  display: grid;
  width: 1.55rem;
  height: 1.55rem;
  place-items: center;
  border: 2px solid #6f6f6f;
  border-radius: 0.13rem;
  background: #fff;
}

.control.checking {
  border-color: transparent;
  background: transparent;
}

.control.verified {
  border-color: #238636;
  color: #fff;
  background: #238636;
}

.spinner {
  width: 1.45rem;
  height: 1.45rem;
  border: 0.18rem solid #d8d8d8;
  border-top-color: #f48120;
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
}

.checkmark {
  font-size: 1rem;
  font-weight: 700;
  line-height: 1;
}

.control-label {
  padding-left: 0.6rem;
  font-size: 0.94rem;
  font-weight: 400;
  white-space: nowrap;
}

.provider {
  display: flex;
  align-items: center;
  flex-direction: column;
  color: #2c2c2c;
  line-height: 1;
}

.provider strong {
  margin-top: 0.2rem;
  font-size: 0.57rem;
  font-weight: 800;
  letter-spacing: 0.09em;
}

.provider small {
  margin-top: 0.32rem;
  color: #555;
  font-size: 0.52rem;
  white-space: nowrap;
}

.cloud-mark {
  position: relative;
  display: block;
  width: 2.55rem;
  height: 1.25rem;
}

.cloud-mark i {
  position: absolute;
  display: block;
  background: #f48120;
}

.cloud-mark i:nth-child(1) {
  right: 0.15rem;
  bottom: 0.1rem;
  width: 2.15rem;
  height: 0.62rem;
  border-radius: 1rem 1rem 0.2rem 0.2rem;
}

.cloud-mark i:nth-child(2) {
  top: 0.15rem;
  left: 0.65rem;
  width: 1.05rem;
  height: 1.05rem;
  border-radius: 50%;
}

.cloud-mark i:nth-child(3) {
  right: 0;
  bottom: 0.08rem;
  width: 0.65rem;
  height: 0.46rem;
  border-radius: 50% 50% 0.2rem 0.2rem;
  background: #f6a84a;
}

.live-status {
  margin: 0;
  color: #595959;
  font-size: 0.92rem;
  line-height: 1.6;
}

.divider {
  height: 1px;
  background: #dedede;
}

footer {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  color: #777;
  font-size: 0.75rem;
}

footer strong {
  color: #555;
  font-weight: 500;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Centered: baseline full-page interstitial, matching the reference figures
   directly (a real Cloudflare challenge page occupies the whole viewport). */
.layout-centered .verify-shell {
  width: min(100%, 52rem);
  margin: 0 auto;
  padding: clamp(5.5rem, 18vh, 12rem) 1.5rem 3rem;
}
.layout-centered .message-block h1 { font-size: clamp(1.55rem, 3vw, 2rem); max-width: 43rem; }
.layout-centered .turnstile-widget { width: min(100%, 23.5rem); margin: 2.25rem 0 1.5rem; }
.layout-centered .divider { margin: clamp(5rem, 18vh, 9rem) 0 1.35rem; }

/* Compact: the widget becomes a small bordered/shadowed card floating on a
   plain page, matching Sophos X-Ops' minimal-turnstile reference (a
   standalone widget rather than a full utilitarian page). */
.layout-compact .challenge-page { display: grid; place-items: center; padding: 2rem; }
.layout-compact .verify-shell {
  width: min(calc(100% - 2rem), 26rem);
  padding: 1.75rem 1.6rem;
  border: 1px solid #e3e3e3;
  border-radius: 0.6rem;
  background: #fff;
  box-shadow: 0 1rem 2.5rem rgba(20, 20, 20, 0.09);
  text-align: center;
}
.layout-compact .message-block h1 { font-size: 1.05rem; }
.layout-compact .turnstile-widget { width: 100%; margin: 1.25rem 0 1rem; text-align: left; }
.layout-compact .live-status { font-size: 0.82rem; }
.layout-compact .divider { margin: 1.1rem 0 0.9rem; }

/* Split: a modestly narrower shell, still centered on the page. */
.layout-split .verify-shell {
  width: min(30rem, 42vw);
  margin: 0 auto;
  padding: clamp(5.5rem, 18vh, 12rem) 1.5rem 3rem;
}

@media (max-width: 35rem) {
  .layout-centered .verify-shell,
  .layout-split .verify-shell {
    width: 100%;
    padding: 4.5rem 1.25rem 2rem;
    margin: 0;
  }

  .turnstile-widget {
    grid-template-columns: 1.8rem minmax(0, 1fr) 5.75rem;
    padding-left: 0.75rem;
  }

  .control-label {
    padding-left: 0.45rem;
    font-size: 0.84rem;
  }

  .provider {
    transform: scale(0.9);
  }

  footer {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
