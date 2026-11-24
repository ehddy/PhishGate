<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateDisplayContext } from "../../../types";
import { documentReadyCopy, documentReadyDescription } from "./presentation";

const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();

const completing = ref(false);
const brand = computed(() => props.displayContext.brand?.trim() || "Document Center");
const copy = computed(() => documentReadyCopy());
const description = computed(() => documentReadyDescription(copy.value, props.displayContext.copy_variant));

onMounted(() => {
  document.title = "Preparing Your Document";
});

function continueToDocument(): void {
  if (completing.value) return;

  completing.value = true;
  emit("complete");
}
</script>

<template>
  <main class="preparation-page" :class="`layout-${displayContext.layout_variant}`" :data-variant-id="displayContext.variant_id">
    <header class="site-header" aria-hidden="true">
      <div class="site-identity">
        <span class="site-mark">{{ brand.charAt(0).toUpperCase() }}</span>
        <strong>{{ brand }}</strong>
      </div>
      <div class="header-status"><span></span>{{ copy.secureDelivery }}</div>
    </header>

    <section class="ready-card" aria-labelledby="ready-title" aria-describedby="ready-description">
      <div class="document-icon" aria-hidden="true">
        <span class="fold"></span>
        <i></i><i></i><i></i><i></i>
      </div>

      <p class="greeting">{{ copy.greeting }}</p>
      <h1 id="ready-title">{{ copy.heading }}</h1>
      <p v-if="description" id="ready-description" class="description">{{ description }}</p>

      <div
        class="progress-track"
        role="progressbar"
        :aria-label="copy.progressLabel"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow="100"
      >
        <span></span>
      </div>
      <div class="ready-status"><span aria-hidden="true">✓</span>{{ copy.readyStatus }}</div>

      <button type="button" :disabled="completing" @click="continueToDocument">
        <span v-if="completing" class="spinner" aria-hidden="true"></span>
        {{ completing ? copy.opening : copy.continueLabel }}
      </button>

      <p class="session-note">{{ copy.sessionNote }}</p>
    </section>

    <footer aria-hidden="true">
      <span>{{ copy.privacy }}</span><i></i><span>{{ copy.helpCenter }}</span><i></i><span>{{ copy.secureAccess }}</span>
    </footer>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(html), :global(body), :global(#app) { min-height: 100%; }
:global(body) { margin: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
button { font: inherit; }
.preparation-page { display: flex; min-height: 100vh; flex-direction: column; color: #15243a; background: radial-gradient(circle at 50% 35%, rgba(255, 255, 255, .92), transparent 32rem), linear-gradient(145deg, #edf6ff 0%, #dcecff 48%, #eef5fc 100%); }
.site-header { display: flex; height: 72px; align-items: center; justify-content: space-between; padding: 0 clamp(22px, 5vw, 72px); border-bottom: 1px solid rgba(68, 100, 140, .12); background: rgba(255, 255, 255, .68); backdrop-filter: blur(12px); }
.site-identity { display: flex; min-width: 0; align-items: center; gap: 11px; }
.site-mark { display: grid; width: 34px; height: 34px; flex: 0 0 34px; place-items: center; border-radius: 9px; color: #fff; background: var(--pg-theme-accent, #2674d9); box-shadow: 0 5px 13px color-mix(in srgb, var(--pg-theme-accent, #2674d9) 20%, transparent); font-size: 15px; font-weight: 800; }
.site-identity strong { max-width: 44vw; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.header-status { display: flex; align-items: center; gap: 8px; color: #627086; font-size: 12px; }
.header-status span { width: 7px; height: 7px; border-radius: 50%; background: #2e9b66; box-shadow: 0 0 0 4px rgba(46, 155, 102, .12); }
.ready-card { width: min(calc(100% - 32px), 540px); margin: auto; padding: clamp(34px, 5vw, 52px) clamp(27px, 6vw, 58px) 33px; border: 1px solid rgba(96, 124, 157, .15); border-radius: 20px; background: rgba(255, 255, 255, .97); box-shadow: 0 30px 70px rgba(48, 83, 124, .19), 0 4px 12px rgba(48, 83, 124, .08); text-align: center; }
.document-icon { position: relative; width: 62px; height: 72px; margin: 0 auto 25px; padding-top: 28px; border: 3px solid #2f425b; border-radius: 5px; background: #f8fbff; box-shadow: 5px 6px 0 #d7e6f8; }
.document-icon .fold { position: absolute; top: -3px; right: -3px; width: 22px; height: 22px; border-bottom: 3px solid #2f425b; border-left: 3px solid #2f425b; background: linear-gradient(45deg, #e1edfa 49%, #fff 51%); }
.document-icon i { display: block; width: 31px; height: 3px; margin: 0 auto 6px; border-radius: 2px; background: #9caabd; }
.document-icon i:nth-of-type(4) { width: 21px; margin-left: 13px; }
.greeting { margin: 0 0 8px; color: var(--pg-theme-accent, #2674d9); font-size: 12px; font-weight: 750; letter-spacing: .08em; text-transform: uppercase; }
.ready-card h1 { margin: 0; color: #142a46; font-size: clamp(25px, 4vw, 33px); letter-spacing: -.035em; line-height: 1.18; }
.description { max-width: 400px; margin: 16px auto 30px; color: #68778a; font-size: 14px; line-height: 1.65; }
.progress-track { height: 9px; overflow: hidden; border-radius: 8px; background: #e4edf7; }
.progress-track span { display: block; width: 100%; height: 100%; border-radius: inherit; background: linear-gradient(90deg, color-mix(in srgb, var(--pg-theme-accent, #2168cf) 70%, #3e92ee), var(--pg-theme-accent, #2168cf)); }
.ready-status { display: flex; align-items: center; justify-content: center; gap: 7px; margin: 14px 0 25px; color: #587089; font-size: 13px; }
.ready-status span { display: grid; width: 18px; height: 18px; place-items: center; border-radius: 50%; color: white; background: #2e9b66; font-size: 11px; font-weight: 800; }
.ready-card button { display: inline-flex; min-width: 150px; height: 46px; align-items: center; justify-content: center; gap: 9px; padding: 0 25px; border: 0; border-radius: 9px; color: #fff; background: var(--pg-theme-accent, #2674d9); box-shadow: 0 8px 18px color-mix(in srgb, var(--pg-theme-accent, #2674d9) 25%, transparent); font-size: 14px; font-weight: 700; cursor: pointer; transition: transform .15s ease, background .15s ease, box-shadow .15s ease; }
.ready-card button:hover:not(:disabled) { filter: brightness(0.92); transform: translateY(-1px); }
.ready-card button:focus-visible { outline: 3px solid color-mix(in srgb, var(--pg-theme-accent, #2674d9) 28%, transparent); outline-offset: 3px; }
.ready-card button:disabled { cursor: wait; opacity: .8; }
.spinner { width: 16px; height: 16px; border: 2px solid rgba(255, 255, 255, .38); border-top-color: #fff; border-radius: 50%; animation: spin .7s linear infinite; }
.session-note { margin: 25px 0 0; color: #929eac; font-size: 11px; }
footer { display: flex; align-items: center; justify-content: center; gap: 12px; min-height: 66px; color: #758399; font-size: 11px; }
footer i { width: 3px; height: 3px; border-radius: 50%; background: #9eabba; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Centered: baseline card in the vertical/horizontal middle of the page. */
.layout-centered .ready-card { margin: auto; }

/* Compact: a smaller, tighter card near the top instead of vertically
   centered, closer to how a document viewer's own inline notice would sit. */
.layout-compact .preparation-page { justify-content: flex-start; }
.layout-compact .ready-card { width: min(calc(100% - 24px), 30rem); margin: clamp(2.5rem, 8vh, 4.5rem) auto 2rem; padding: 28px 26px 26px; }
.layout-compact .document-icon { width: 48px; height: 56px; margin-bottom: 18px; }
.layout-compact footer { min-height: 48px; }

/* Split: a modestly narrower card, still centered on the page. */
.layout-split .ready-card { width: min(calc(100% - 32px), 30rem); }

@media (max-width: 560px) {
  .preparation-page { min-height: 100svh; }
  .site-header { height: 62px; }
  .header-status { font-size: 0; }
  .ready-card,
  .layout-compact .ready-card,
  .layout-split .ready-card { margin: auto 16px; width: auto; padding-top: 38px; border-radius: 16px; }
  .document-icon { width: 54px; height: 64px; margin-bottom: 21px; }
  footer { min-height: 56px; justify-content: center; padding-right: 0; }
}
@media (prefers-reduced-motion: reduce) { .ready-card button, .spinner { animation: none; transition: none; } }
</style>
