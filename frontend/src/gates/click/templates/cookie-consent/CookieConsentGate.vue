<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { ENGLISH_COPY } from "../../../../presentation/copy";
import type { GateDisplayContext } from "../../../types";
import { cookieDescription, cookiePresentationCopy, GENERIC_SHELL_COPY } from "./presentation";


const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();
const completing = ref(false);
const brand = computed(() => props.displayContext.brand?.trim() || null);
const commonCopy = ENGLISH_COPY;
const cookieCopy = computed(() => cookiePresentationCopy());
const siteName = computed(() => brand.value ?? cookieCopy.value.website);
const shellCopy = GENERIC_SHELL_COPY;
const description = computed(() =>
  cookieDescription(cookieCopy.value, props.displayContext.copy_variant, siteName.value),
);

onMounted(() => {
  document.title = brand.value ?? commonCopy.welcome;
});

function dismissConsent(): void {
  if (completing.value) return;
  completing.value = true;
  emit("complete");
}
</script>

<template>
  <main
    class="cookie-page"
    :class="`layout-${displayContext.layout_variant}`"
    :data-variant-id="displayContext.variant_id"
  >
    <header class="site-header" aria-hidden="true">
      <div class="wordmark">
        <span class="brand-mark">{{ brand?.charAt(0).toUpperCase() || "W" }}</span>
        <span>{{ brand || commonCopy.welcome }}</span>
      </div>
      <nav>
        <span>{{ commonCopy.privacy }}</span>
        <span>{{ commonCopy.support }}</span>
      </nav>
    </header>

    <section class="background-content" aria-hidden="true">
      <div class="eyebrow">{{ shellCopy.eyebrow }}</div>
      <h1>{{ shellCopy.title }}</h1>
      <p>{{ shellCopy.description }}</p>
      <div class="content-button">{{ shellCopy.action }}</div>
      <div class="feature-row">
        <div class="feature-card"><span></span><i></i><i></i></div>
        <div class="feature-card"><span></span><i></i><i></i></div>
        <div class="feature-card"><span></span><i></i><i></i></div>
      </div>
    </section>

    <div class="page-shade"></div>

    <section
      class="consent-card"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cookie-title"
      aria-describedby="cookie-description"
    >
      <button
        class="close-button"
        type="button"
        :aria-label="cookieCopy.closeLabel"
        :disabled="completing"
        @click="dismissConsent"
      >×</button>

      <div class="consent-copy">
        <div class="cookie-icon" aria-hidden="true">
          <span></span><span></span><span></span>
        </div>
        <div class="text-content">
          <h2 id="cookie-title">{{ cookieCopy.title }}</h2>
          <p id="cookie-description">{{ description }}</p>
          <a href="#cookie-policy" @click.prevent>{{ cookieCopy.policyLink }}</a>
        </div>
      </div>

      <div class="consent-actions">
        <button class="accept-button" type="button" :disabled="completing" @click="dismissConsent">
          {{ completing ? cookieCopy.opening : cookieCopy.accept }}
        </button>
      </div>
    </section>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(body) {
  margin: 0;
  color: var(--pg-shell-text, #202733);
  background: var(--pg-shell-background, #f5f7fa);
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button, a { font: inherit; }
.cookie-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  color: var(--pg-shell-text, #202733);
  background: radial-gradient(circle at 70% 18%, var(--pg-theme-accent-soft, #e8f0ff), transparent 28rem), var(--pg-shell-background, #f5f7fa);
}
.site-header {
  display: flex;
  height: 4.5rem;
  align-items: center;
  justify-content: space-between;
  padding: 0 6vw;
  border-bottom: 1px solid color-mix(in srgb, var(--pg-shell-text, #202733) 12%, transparent);
  background: color-mix(in srgb, var(--pg-shell-surface, #fff) 92%, transparent);
}
.wordmark { display: flex; min-width: 0; align-items: center; gap: .7rem; font-weight: 720; }
.wordmark > span:last-child { max-width: 45vw; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.brand-mark { display: grid; width: 2rem; height: 2rem; flex: 0 0 auto; place-items: center; border-radius: .55rem; color: #fff; background: var(--pg-theme-accent, #2563c9); font-size: .85rem; }
nav { display: flex; gap: 2rem; color: color-mix(in srgb, var(--pg-shell-text, #202733) 68%, transparent); font-size: .86rem; }
.background-content { width: min(88%, 68rem); margin: 10vh auto 0; text-align: center; }
.eyebrow { color: var(--pg-theme-accent, #2563c9); font-size: .75rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; }
.background-content h1 { max-width: 52rem; margin: 1rem auto; font-size: clamp(2.15rem, 5vw, 4.5rem); letter-spacing: -.045em; line-height: 1.05; }
.background-content p { margin: 0 auto; color: color-mix(in srgb, var(--pg-shell-text, #202733) 68%, transparent); font-size: 1.05rem; }
.content-button { width: max-content; margin: 2rem auto 3.4rem; padding: .82rem 1.3rem; border-radius: .48rem; color: #fff; background: var(--pg-theme-accent, #2563c9); font-size: .9rem; font-weight: 680; }
.feature-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem; }
.feature-card { height: 10rem; padding: 1.3rem; border: 1px solid color-mix(in srgb, var(--pg-shell-text, #202733) 10%, transparent); border-radius: .85rem; background: var(--pg-shell-surface, #fff); text-align: left; }
.feature-card span { display: block; width: 2.2rem; height: 2.2rem; margin-bottom: 1.2rem; border-radius: .55rem; background: var(--pg-theme-accent-soft, #e8f0ff); }
.feature-card i { display: block; width: 76%; height: .55rem; margin-top: .7rem; border-radius: 1rem; background: color-mix(in srgb, var(--pg-shell-text, #202733) 10%, transparent); }
.feature-card i:last-child { width: 54%; }
.page-shade { position: fixed; inset: 0; background: rgba(15, 20, 29, .7); backdrop-filter: blur(2px); }
.consent-card { position: fixed; z-index: 2; color: #20242b; background: #fff; box-shadow: 0 1.5rem 4rem rgba(0, 0, 0, .3); }
.close-button { position: absolute; top: .65rem; inset-inline-end: .65rem; display: grid; width: 2.55rem; height: 2.55rem; place-items: center; border: 0; border-radius: .45rem; color: #7b828d; background: transparent; font-size: 1.55rem; cursor: pointer; }
.close-button:hover, .close-button:focus-visible { color: #272c33; background: #f1f3f5; }
.cookie-icon { position: relative; flex: 0 0 auto; width: 2.5rem; height: 2.5rem; border-radius: 50%; background: #d69a47; box-shadow: inset -.35rem -.25rem 0 #b87831; }
.cookie-icon::after { position: absolute; top: -.1rem; right: -.15rem; width: 1.15rem; height: 1.05rem; border-radius: 0 0 0 100%; background: #fff; content: ""; }
.cookie-icon span { position: absolute; width: .3rem; height: .3rem; border-radius: 50%; background: #70451e; }
.cookie-icon span:nth-child(1) { top: .55rem; left: .6rem; }
.cookie-icon span:nth-child(2) { top: 1.4rem; left: .8rem; }
.cookie-icon span:nth-child(3) { top: 1.05rem; left: 1.5rem; }
h2 { margin: 0 0 .7rem; font-size: 1.55rem; letter-spacing: -.02em; }
.consent-card p { margin: 0; color: #505762; font-size: .94rem; line-height: 1.58; }
.consent-card a { display: inline-block; margin-top: .55rem; color: var(--pg-theme-accent, #2563c9); font-size: .85rem; text-underline-offset: .16rem; }
.accept-button { min-width: 8.5rem; padding: .78rem 1.3rem; border: 0; border-radius: .45rem; color: #fff; background: var(--pg-theme-accent, #2563c9); font-weight: 680; cursor: pointer; }
.accept-button:hover, .accept-button:focus-visible { filter: brightness(.92); box-shadow: 0 0 0 .2rem var(--pg-theme-accent-soft, #e8f0ff); }
button:disabled { cursor: wait; opacity: .72; }

.layout-centered .consent-card { left: 50%; bottom: clamp(2rem, 9vh, 6rem); width: min(calc(100% - 2rem), 34rem); padding: 2.3rem 3rem 2.5rem; border-radius: .9rem; text-align: center; transform: translateX(-50%); }
.layout-centered .consent-copy { display: grid; justify-items: center; }
.layout-centered .cookie-icon { margin-bottom: 1rem; }
.layout-centered .consent-actions { margin-top: 1.6rem; }
.layout-compact .page-shade { background: rgba(15, 20, 29, .38); backdrop-filter: blur(1px); }
.layout-compact .consent-card { right: 1.25rem; bottom: 1.25rem; left: 1.25rem; display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 1.5rem; max-width: 72rem; margin: auto; padding: 1.35rem 4rem 1.35rem 1.5rem; border-radius: .75rem; }
.layout-compact .consent-copy { display: grid; grid-template-columns: auto minmax(0, 1fr); align-items: start; gap: 1rem; }
.layout-compact h2 { font-size: 1.15rem; }
.layout-compact .cookie-icon { margin-top: .15rem; }
.layout-split .page-shade { background: rgba(15, 20, 29, .3); backdrop-filter: blur(1px); }
.layout-split .consent-card { top: 0; bottom: 0; inset-inline-end: 0; display: flex; width: min(42rem, 44vw); flex-direction: column; justify-content: center; padding: clamp(3rem, 7vw, 7rem); }
.layout-split .cookie-icon { width: 3.2rem; height: 3.2rem; margin-bottom: 1.8rem; }
.layout-split h2 { font-size: clamp(1.8rem, 3vw, 2.55rem); }
.layout-split .consent-card p { font-size: 1rem; line-height: 1.7; }
.layout-split .consent-actions { margin-top: 2rem; }
.layout-split .accept-button { width: 100%; min-height: 3rem; }

@media (max-width: 48rem) {
  .site-header { height: 3.8rem; padding: 0 1rem; }
  nav { display: none; }
  .background-content { margin-top: 8vh; }
  .feature-row { grid-template-columns: 1fr; }
  .feature-card:nth-child(n + 2) { display: none; }
  .layout-centered .consent-card, .layout-compact .consent-card, .layout-split .consent-card {
    top: auto;
    right: 1rem;
    bottom: 1rem;
    left: 1rem;
    display: block;
    width: auto;
    max-height: calc(100vh - 2rem);
    margin: 0;
    padding: 2rem 1.35rem 1.5rem;
    overflow: auto;
    border-radius: .85rem;
    text-align: start;
    transform: none;
  }
  .layout-centered .consent-copy, .layout-compact .consent-copy, .layout-split .consent-copy { display: block; }
  .cookie-icon { margin: 0 0 1rem; }
  .consent-actions { margin-top: 1.35rem; }
  .accept-button { width: 100%; }
}
</style>
