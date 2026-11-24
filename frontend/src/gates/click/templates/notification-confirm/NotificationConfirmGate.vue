<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateDisplayContext } from "../../../types";
import { notificationCopy, notificationLead } from "./presentation";


const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();
const blocked = ref(false);
const completing = ref(false);
const brand = computed(() => props.displayContext.brand?.trim() || "This site");
const copy = computed(() => notificationCopy());
const lead = computed(() => notificationLead(copy.value, props.displayContext.copy_variant));

onMounted(() => {
  document.title = "Just a moment...";
});

function allowNotifications(): void {
  if (completing.value) return;
  completing.value = true;
  blocked.value = false;
  emit("complete");
}

function blockNotifications(): void {
  if (!completing.value) blocked.value = true;
}
</script>

<template>
  <main class="notification-page" :class="`layout-${displayContext.layout_variant}`" :data-variant-id="displayContext.variant_id">
    <header class="site-header">
      <div class="brand-lockup">
        <span class="brand-mark" aria-hidden="true">{{ brand.charAt(0).toUpperCase() }}</span>
        <span>{{ brand }}</span>
      </div>
      <span class="status"><i aria-hidden="true"></i> {{ copy.secureConnection }}</span>
    </header>

    <section class="content-card" aria-labelledby="notification-heading">
      <div class="security-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" role="img">
          <path d="M12 3 5.5 5.7v5.1c0 4.6 2.8 8.7 6.5 10.2 3.7-1.5 6.5-5.6 6.5-10.2V5.7L12 3Z" />
          <path d="m8.9 12.1 2 2 4.4-4.6" />
        </svg>
      </div>
      <p class="eyebrow">{{ copy.oneMoreStep }}</p>
      <h1 id="notification-heading">{{ copy.heading }}</h1>
      <p v-if="lead" class="lead">{{ lead }}</p>

      <ol class="steps">
        <li><span>1</span> {{ copy.step1 }}</li>
        <li><span>2</span> {{ copy.step2 }}</li>
      </ol>

      <p v-if="blocked" class="blocked-message" role="status">{{ copy.blocked }}</p>

      <div class="trust-row" aria-label="Security status">
        <span><i aria-hidden="true">✓</i> {{ copy.protectedRequest }}</span>
        <span><i aria-hidden="true">✓</i> {{ copy.privateSession }}</span>
      </div>
    </section>

    <section class="permission-card" aria-labelledby="permission-title">
      <div class="permission-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24">
          <path d="M18 16v-5a6 6 0 0 0-12 0v5l-2 2h16l-2-2Z" />
          <path d="M9.5 20h5" />
        </svg>
      </div>
      <div class="permission-copy">
        <h2 id="permission-title">{{ copy.wantsToShow(brand) }}</h2>
        <p>{{ copy.preferenceNote }}</p>
      </div>
      <div class="permission-actions">
        <button class="secondary-button" type="button" :disabled="completing" @click="blockNotifications">
          {{ copy.block }}
        </button>
        <button class="primary-button" type="button" :disabled="completing" @click="allowNotifications">
          <span v-if="completing" class="spinner" aria-hidden="true"></span>
          {{ completing ? copy.continuing : copy.allow }}
        </button>
      </div>
    </section>

    <footer>{{ copy.footer }}</footer>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(body) {
  margin: 0;
  color: #edf2f7;
  background: #171a1f;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button { font: inherit; }

/* The dark "security check" background is a retained pattern from the
   source figures (MalwareTips' dark Cloudflare-themed gate); only the
   accent color follows theme_variant, matching how a real site's brand
   color would appear on top of a generic security-interstitial look. */
.notification-page {
  min-height: 100vh;
  padding-bottom: 3rem;
  background: radial-gradient(circle at 50% 12%, color-mix(in srgb, var(--pg-theme-accent, #327759) 22%, transparent), transparent 30rem), #171a1f;
}
.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 4.1rem;
  padding: 0 2rem;
  border-bottom: 1px solid #2b3038;
  background: rgba(21, 24, 29, 0.9);
}
.brand-lockup { display: flex; align-items: center; gap: 0.65rem; color: #f7f9fb; font-size: 0.9rem; font-weight: 650; }
.brand-mark { display: grid; width: 1.85rem; height: 1.85rem; place-items: center; border-radius: 0.5rem; color: #fff; background: var(--pg-theme-accent, #25815e); font-size: 0.82rem; }
.status { display: flex; align-items: center; gap: 0.45rem; color: #8f9aa8; font-size: 0.74rem; }
.status i { width: 0.45rem; height: 0.45rem; border-radius: 50%; background: var(--pg-theme-accent, #41ba85); box-shadow: 0 0 0 0.2rem color-mix(in srgb, var(--pg-theme-accent, #41ba85) 20%, transparent); }
.content-card { width: min(calc(100% - 2rem), 36rem); text-align: center; }
.security-icon { display: grid; width: 4rem; height: 4rem; margin: 0 auto 1.2rem; place-items: center; border: 1px solid color-mix(in srgb, var(--pg-theme-accent, #345342) 55%, #1d2b25); border-radius: 1.1rem; background: #1d2b25; }
.security-icon svg { width: 2.25rem; fill: none; stroke: var(--pg-theme-accent, #55c590); stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.7; }
.eyebrow { margin: 0 0 0.55rem; color: var(--pg-theme-accent, #54bf8d); font-size: 0.72rem; font-weight: 750; letter-spacing: 0.14em; text-transform: uppercase; }
h1 { margin: 0; color: #f8fafc; font-size: clamp(1.75rem, 5vw, 2.35rem); line-height: 1.18; }
.lead { max-width: 29rem; margin: 1rem auto 1.8rem; color: #a8b0bb; font-size: 0.95rem; line-height: 1.6; }
.steps { display: grid; gap: 0.65rem; max-width: 26rem; margin: 0 auto; padding: 0; list-style: none; text-align: left; }
.steps li { display: flex; align-items: center; gap: 0.8rem; padding: 0.75rem 0.9rem; border: 1px solid #30363e; border-radius: 0.65rem; color: #c7ced7; background: #1d2127; font-size: 0.85rem; }
.steps li span { display: grid; flex: 0 0 1.55rem; height: 1.55rem; place-items: center; border-radius: 50%; color: var(--pg-theme-accent, #74d2a6); background: color-mix(in srgb, var(--pg-theme-accent, #243c31) 30%, #1d2127); font-size: 0.72rem; font-weight: 750; }
.blocked-message { max-width: 26rem; margin: 1rem auto 0; padding: 0.75rem 0.9rem; border: 1px solid #624841; border-radius: 0.6rem; color: #e9b8a8; background: #2b211f; font-size: 0.78rem; line-height: 1.45; }
.trust-row { display: flex; justify-content: center; gap: 1.5rem; margin-top: 1.5rem; color: #7f8996; font-size: 0.72rem; }
.trust-row i { color: var(--pg-theme-accent, #4cb881); font-style: normal; }
.permission-card {
  position: fixed;
  top: 1rem;
  left: 50%;
  z-index: 5;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0.9rem;
  width: min(calc(100% - 2rem), 38rem);
  padding: 0.9rem;
  border: 1px solid #d6dbe2;
  border-radius: 0.75rem;
  color: #202630;
  background: #fff;
  box-shadow: 0 1rem 2.5rem rgba(0, 0, 0, 0.32);
  transform: translateX(-50%);
}
.permission-icon { display: grid; width: 2.35rem; height: 2.35rem; place-items: center; border-radius: 50%; background: #eef3f7; }
.permission-icon svg { width: 1.3rem; fill: none; stroke: #4b5968; stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.8; }
.permission-copy { min-width: 0; }
.permission-copy h2 { overflow: hidden; margin: 0; font-size: 0.86rem; font-weight: 680; text-overflow: ellipsis; white-space: nowrap; }
.permission-copy p { margin: 0.25rem 0 0; color: #707a87; font-size: 0.72rem; }
.permission-actions { display: flex; gap: 0.45rem; }
.permission-actions button { min-width: 4.5rem; min-height: 2.2rem; padding: 0.45rem 0.8rem; border-radius: 0.45rem; cursor: pointer; font-size: 0.78rem; font-weight: 650; }
.secondary-button { border: 1px solid #ccd2da; color: #485462; background: #fff; }
.primary-button { border: 1px solid var(--pg-theme-accent, #277854); color: #fff; background: var(--pg-theme-accent, #277854); }
.permission-actions button:hover:not(:disabled) { filter: brightness(0.94); }
.permission-actions button:focus-visible { outline: 3px solid color-mix(in srgb, var(--pg-theme-accent, #378861) 28%, transparent); outline-offset: 2px; }
.permission-actions button:disabled { cursor: wait; opacity: 0.72; }
.spinner { display: inline-block; width: 0.72rem; height: 0.72rem; margin-right: 0.25rem; border: 2px solid rgba(255, 255, 255, 0.42); border-top-color: #fff; border-radius: 50%; vertical-align: -0.1rem; animation: spin 0.75s linear infinite; }
footer { color: #697381; font-size: 0.7rem; text-align: center; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Centered: baseline top-down page, matching the source figures directly. */
.layout-centered .content-card { margin: clamp(4rem, 12vh, 7.5rem) auto 0; }
.layout-centered footer { margin-top: 3.5rem; }

/* Compact: permission card and content collapse into one narrower column,
   closer to a mobile-first single-card reading order. */
.layout-compact .content-card { width: min(calc(100% - 2rem), 28rem); margin: clamp(6.5rem, 20vh, 9rem) auto 0; }
.layout-compact .permission-card { width: min(calc(100% - 1.5rem), 28rem); grid-template-columns: auto 1fr; row-gap: 0.6rem; }
.layout-compact .permission-actions { grid-column: 1 / -1; justify-content: flex-end; }
.layout-compact footer { margin-top: 2rem; }

/* Split: same centering as the baseline card, only a touch narrower; the
   notification permission surfaces as its own right-aligned panel. */
.layout-split .content-card { width: min(calc(100% - 2rem), 30rem); margin: clamp(4rem, 14vh, 8rem) auto 0; }
.layout-split .permission-card { left: auto; right: 1.25rem; transform: none; }
.layout-split footer { margin-top: 3.5rem; }

@media (max-width: 40rem) {
  .site-header { height: 3.7rem; padding: 0 1rem; }
  .status { display: none; }
  .layout-centered .content-card,
  .layout-split .content-card { margin-top: 8.5rem; width: min(calc(100% - 2rem), 36rem); margin-inline: auto; text-align: center; }
  .layout-split .eyebrow, .layout-split h1, .layout-split .lead { text-align: center; }
  .layout-split .trust-row { justify-content: center; }
  .permission-card { grid-template-columns: auto 1fr; left: 50%; right: auto; transform: translateX(-50%); }
  .permission-actions { grid-column: 1 / -1; justify-content: flex-end; }
  .trust-row { flex-direction: column; gap: 0.4rem; }
}
@media (prefers-reduced-motion: reduce) { .spinner { animation: none; } }
</style>
