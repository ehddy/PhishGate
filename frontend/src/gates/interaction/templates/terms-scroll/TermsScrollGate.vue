<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateDisplayContext } from "../../../types";
import { termsScrollCopy, termsScrollLead } from "./presentation";

const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();

onMounted(() => {
  document.title = "Shared document.pdf";
});

const scrollContainer = ref<HTMLElement | null>(null);
const currentPage = ref(1);
const completing = ref(false);
const brand = computed(() => props.displayContext.brand?.trim() || "Secure Documents");
const copy = computed(() => termsScrollCopy());
const lead = computed(() => termsScrollLead(copy.value, props.displayContext.copy_variant));
const thresholdPercent = computed(() => {
  const configured = props.parameters?.threshold_percent;
  return typeof configured === "number" && configured > 0 && configured <= 100
    ? configured
    : 90;
});

function handleScroll(): void {
  const container = scrollContainer.value;
  if (!container || completing.value) return;

  const pages = Array.from(container.querySelectorAll<HTMLElement>(".document-page"));
  const readingLine = container.scrollTop + container.clientHeight * 0.42;
  currentPage.value = pages.reduce(
    (visiblePage, page, index) => page.offsetTop <= readingLine ? index + 1 : visiblePage,
    1,
  );

  const maxScroll = container.scrollHeight - container.clientHeight;
  const progress = maxScroll > 0 ? (container.scrollTop / maxScroll) * 100 : 0;
  if (progress >= thresholdPercent.value) {
    completing.value = true;
    emit("complete");
  }
}
</script>

<template>
  <main class="viewer-shell" :class="`layout-${displayContext.layout_variant}`" :data-variant-id="displayContext.variant_id">
    <header class="viewer-toolbar">
      <div class="file-identity">
        <span class="pdf-badge" aria-hidden="true">PDF</span>
        <span class="file-name">Shared document.pdf</span>
      </div>
      <div class="page-control" aria-live="polite">
        <span class="page-number">{{ currentPage }}</span><span class="page-total">/ 3</span>
      </div>
      <div class="viewer-actions" aria-hidden="true">
        <span class="tool-icon">−</span><span class="zoom-value">100%</span>
        <span class="tool-icon">＋</span><span class="divider"></span>
        <span class="tool-icon print-icon">▣</span><span class="tool-icon">⇩</span>
        <span class="tool-icon">⋮</span>
      </div>
    </header>

    <div
      ref="scrollContainer"
      class="document-viewport"
      role="region"
      aria-label="Scrollable document preview"
      tabindex="0"
      @scroll.passive="handleScroll"
    >
      <div class="page-stack">
        <article class="document-page cover-page" aria-label="Document page 1 of 3">
          <div class="document-brand">
            <span class="brand-symbol" aria-hidden="true">S</span>
            <div><strong>{{ brand }}</strong><small>{{ copy.documentServices }}</small></div>
          </div>
          <div class="confidential-label">{{ copy.confidential }}</div>
          <h1>{{ copy.heading }}</h1>
          <p class="lead">{{ lead }}</p>
          <dl class="document-details">
            <div><dt>{{ copy.documentLabel }}</dt><dd>Account Summary</dd></div>
            <div><dt>{{ copy.referenceLabel }}</dt><dd>SD-904-2086</dd></div>
            <div><dt>{{ copy.preparedLabel }}</dt><dd>September 4, 2026</dd></div>
            <div><dt>{{ copy.statusLabel }}</dt><dd><span class="status-dot"></span>{{ copy.statusReady }}</dd></div>
          </dl>
          <p class="privacy-note">{{ copy.privacyNote }}</p>
          <span class="page-footer">1 / 3</span>
        </article>

        <article class="document-page summary-page" aria-label="Document page 2 of 3">
          <div class="document-brand compact">
            <span class="brand-symbol" aria-hidden="true">S</span>
            <div><strong>{{ brand }}</strong><small>{{ copy.secureDelivery }}</small></div>
          </div>
          <div class="rule"></div>
          <p class="eyebrow">{{ copy.documentSummary }}</p>
          <h2>{{ copy.reviewDetails }}</h2>
          <p class="body-copy">{{ copy.summaryBody }}</p>
          <div class="summary-card">
            <div><span>{{ copy.packageType }}</span><strong>{{ copy.packageTypeValue }}</strong></div>
            <div><span>{{ copy.pageCount }}</span><strong>{{ copy.pageCountValue }}</strong></div>
            <div><span>{{ copy.deliveryMethod }}</span><strong>{{ copy.deliveryMethodValue }}</strong></div>
            <div><span>{{ copy.reviewStatus }}</span><strong class="pending">{{ copy.reviewStatusValue }}</strong></div>
          </div>
          <h3>{{ copy.importantInfo }}</h3>
          <p class="body-copy">{{ copy.importantInfoBody }}</p>
          <div class="signature-lines"><span></span><span></span><span></span></div>
          <span class="page-footer">2 / 3</span>
        </article>

        <article class="document-page final-page" aria-label="Document page 3 of 3">
          <div class="document-brand compact">
            <span class="brand-symbol" aria-hidden="true">S</span>
            <div><strong>{{ brand }}</strong><small>{{ copy.secureDelivery }}</small></div>
          </div>
          <div class="rule"></div>
          <p class="eyebrow">{{ copy.finalPage }}</p>
          <h2>{{ copy.documentReview }}</h2>
          <p class="body-copy">{{ copy.finalBody }}</p>
          <div class="review-panel">
            <span class="review-mark" aria-hidden="true">✓</span>
            <div><strong>{{ copy.reviewMarkAvailable }}</strong><p>{{ copy.reviewMarkNote }}</p></div>
          </div>
          <div class="fine-print">
            <h3>{{ copy.confidentialityNotice }}</h3>
            <p>{{ copy.confidentialityBody }}</p>
          </div>
          <span class="page-footer">3 / 3</span>
        </article>
      </div>
    </div>

    <div v-if="!completing" class="scroll-cue" aria-hidden="true">
      <span class="mouse"><i></i></span><span>{{ copy.scrollCue }}</span>
      <span class="chevron">⌄</span>
    </div>
    <div v-else class="opening-overlay" role="status" aria-live="assertive">
      <div class="spinner" aria-hidden="true"></div><strong>{{ copy.openingDocument }}</strong>
    </div>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(html), :global(body), :global(#app) { height: 100%; }
:global(body) { margin: 0; overflow: hidden; font-family: Arial, Helvetica, sans-serif; }
.viewer-shell { position: relative; display: flex; height: 100vh; flex-direction: column; overflow: hidden; background: #525659; color: #202124; }
.viewer-toolbar { z-index: 3; display: grid; flex: 0 0 56px; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: center; min-width: 0; padding: 0 18px; color: #f1f3f4; background: #323639; box-shadow: 0 2px 6px rgba(0, 0, 0, .45); font-size: 13px; }
.file-identity, .viewer-actions, .page-control { display: flex; align-items: center; }
.file-identity { min-width: 0; gap: 12px; }
.pdf-badge { display: grid; width: 30px; height: 34px; place-items: center; border-radius: 2px; color: white; background: #d93025; font-size: 9px; font-weight: 700; }
.file-name { overflow: hidden; font-weight: 500; text-overflow: ellipsis; white-space: nowrap; }
.page-control { gap: 8px; justify-content: center; }
.page-number { display: grid; width: 30px; height: 28px; place-items: center; border-radius: 2px; color: #e8eaed; background: #202124; }
.page-total { color: #bdc1c6; }
.viewer-actions { justify-self: end; gap: 13px; color: #e8eaed; }
.tool-icon { min-width: 20px; font-size: 19px; line-height: 1; text-align: center; }
.zoom-value { font-size: 12px; }
.divider { width: 1px; height: 24px; margin: 0 3px; background: #5f6368; }
.print-icon { font-size: 16px; }
.document-viewport { flex: 1; min-height: 0; overflow: auto; outline: none; scrollbar-color: #8a8d90 #3f4245; }
.document-viewport:focus-visible { box-shadow: inset 0 0 0 2px #8ab4f8; }
.page-stack { display: flex; width: 100%; flex-direction: column; align-items: center; gap: 22px; padding: 28px 28px 110px; }
.document-page { position: relative; width: min(760px, calc(100vw - 72px)); min-height: 980px; padding: 78px 82px 70px; background: #fff; box-shadow: 0 2px 8px rgba(0, 0, 0, .55); color: #202124; }
.document-brand { display: flex; align-items: center; gap: 12px; color: #253044; }
.document-brand strong { display: block; max-width: 440px; overflow: hidden; font-size: 17px; text-overflow: ellipsis; white-space: nowrap; }
.document-brand small { display: block; margin-top: 2px; color: #7a8492; font-size: 8px; font-weight: 700; letter-spacing: 1.55px; }
.brand-symbol { display: grid; width: 42px; height: 42px; place-items: center; border-radius: 4px 12px 4px 12px; color: #fff; background: var(--pg-theme-accent, #1f5c8f); font-family: Georgia, serif; font-size: 24px; font-weight: 700; }
.document-brand.compact .brand-symbol { width: 34px; height: 34px; font-size: 19px; }
.document-brand.compact strong { font-size: 14px; }
.confidential-label { width: fit-content; margin-top: 92px; padding: 7px 11px; border: 1px solid #9ca7b4; color: #52606d; font-size: 9px; font-weight: 700; letter-spacing: 1.3px; }
.cover-page h1 { max-width: 590px; margin: 25px 0 20px; color: #172f47; font-family: Georgia, "Times New Roman", serif; font-size: 50px; font-weight: 400; line-height: 1.08; }
.lead { max-width: 520px; margin: 0; color: #647181; font-family: Georgia, "Times New Roman", serif; font-size: 18px; line-height: 1.65; }
.document-details { margin: 70px 0 0; border-top: 1px solid #d9dee4; }
.document-details div { display: grid; grid-template-columns: 150px 1fr; padding: 15px 0; border-bottom: 1px solid #e5e8eb; }
.document-details dt { color: #7b8490; font-size: 11px; font-weight: 700; letter-spacing: .4px; text-transform: uppercase; }
.document-details dd { margin: 0; color: #2e3946; font-size: 13px; font-weight: 600; }
.status-dot { display: inline-block; width: 7px; height: 7px; margin-right: 7px; border-radius: 50%; background: #2e8b57; }
.privacy-note { position: absolute; right: 82px; bottom: 70px; left: 82px; margin: 0; color: #929aa4; font-size: 10px; line-height: 1.5; }
.page-footer { position: absolute; right: 30px; bottom: 28px; color: #9aa0a6; font-size: 10px; }
.rule { height: 3px; margin: 28px 0 82px; background: linear-gradient(90deg, var(--pg-theme-accent, #1f5c8f) 0 34%, #dbe5ed 34%); }
.eyebrow { margin: 0 0 13px; color: var(--pg-theme-accent, #1f5c8f); font-size: 10px; font-weight: 700; letter-spacing: 1.8px; }
.document-page h2 { margin: 0 0 22px; color: #1d344a; font-family: Georgia, "Times New Roman", serif; font-size: 38px; font-weight: 400; }
.body-copy { color: #5e6976; font-family: Georgia, "Times New Roman", serif; font-size: 15px; line-height: 1.75; }
.summary-card { margin: 45px 0; border: 1px solid #dce1e6; border-radius: 2px; }
.summary-card div { display: flex; justify-content: space-between; gap: 20px; padding: 17px 20px; border-bottom: 1px solid #e6e9ed; font-size: 12px; }
.summary-card div:last-child { border-bottom: 0; }
.summary-card span { color: #7a8490; }
.summary-card strong { color: #293644; }
.summary-card .pending { color: #9a6400; }
.document-page h3 { margin: 44px 0 10px; color: #293b4e; font-size: 14px; }
.signature-lines { display: grid; gap: 11px; margin-top: 50px; }
.signature-lines span { display: block; height: 7px; border-radius: 2px; background: #eef1f4; }
.signature-lines span:nth-child(2) { width: 84%; }
.signature-lines span:nth-child(3) { width: 61%; }
.review-panel { display: flex; align-items: center; gap: 18px; margin: 55px 0; padding: 24px; border: 1px solid #cfdad5; border-left: 4px solid #357a55; background: #f7faf8; }
.review-mark { display: grid; flex: 0 0 42px; height: 42px; place-items: center; border-radius: 50%; color: #fff; background: #357a55; font-size: 22px; }
.review-panel strong { color: #263f32; font-size: 15px; }
.review-panel p { margin: 5px 0 0; color: #718078; font-size: 12px; }
.fine-print { margin-top: 120px; padding-top: 25px; border-top: 1px solid #dfe3e6; }
.fine-print h3 { margin-top: 0; }
.fine-print p { color: #808790; font-size: 11px; line-height: 1.7; }
.scroll-cue { position: absolute; z-index: 4; bottom: 22px; left: 50%; display: flex; align-items: center; gap: 10px; padding: 10px 15px; border: 1px solid rgba(255, 255, 255, .18); border-radius: 22px; color: #f1f3f4; background: rgba(32, 33, 36, .92); box-shadow: 0 3px 12px rgba(0, 0, 0, .35); font-size: 12px; transform: translateX(-50%); pointer-events: none; white-space: nowrap; }
.mouse { position: relative; width: 14px; height: 19px; border: 1.5px solid #d6d9dc; border-radius: 8px; }
.mouse i { position: absolute; top: 3px; left: 5px; width: 2px; height: 4px; border-radius: 2px; background: #d6d9dc; animation: wheel 1.5s ease-in-out infinite; }
.chevron { margin-left: 2px; color: #bdc1c6; font-size: 17px; }
.opening-overlay { position: absolute; z-index: 6; inset: 0; display: flex; align-items: center; justify-content: center; gap: 13px; color: #f1f3f4; background: rgba(32, 33, 36, .88); font-size: 14px; }
.spinner { width: 25px; height: 25px; border: 3px solid rgba(255, 255, 255, .25); border-top-color: #8ab4f8; border-radius: 50%; animation: spin .75s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes wheel { 0%, 100% { transform: translateY(0); opacity: .4; } 50% { transform: translateY(5px); opacity: 1; } }

/* This viewer mimics a real, fixed PDF-reader chrome, so layout_variant
   intentionally stays a modest width/density change rather than a forced
   structural rework -- a real document viewer doesn't have "split" or
   "compact" page-composition modes, only a narrower or wider reading column. */
.layout-compact .document-page { width: min(600px, calc(100vw - 56px)); padding: 56px 56px 56px; }
.layout-compact .cover-page h1 { font-size: 40px; }
.layout-split .document-page { width: min(880px, calc(100vw - 96px)); }

@media (max-width: 640px) {
  .viewer-toolbar { grid-template-columns: minmax(0, 1fr) auto; height: 52px; padding: 0 12px; }
  .pdf-badge { width: 27px; height: 31px; }
  .page-control { grid-column: 2; grid-row: 1; }
  .viewer-actions { display: none; }
  .page-stack { gap: 14px; padding: 16px 10px 90px; }
  .document-page,
  .layout-compact .document-page,
  .layout-split .document-page { width: 100%; min-height: 660px; padding: 42px 34px 50px; }
  .brand-symbol { width: 35px; height: 35px; font-size: 19px; }
  .document-brand strong { max-width: 230px; font-size: 14px; }
  .confidential-label { margin-top: 55px; }
  .cover-page h1 { margin-top: 18px; font-size: 34px; }
  .lead { font-size: 14px; }
  .document-details { margin-top: 42px; }
  .document-details div { grid-template-columns: 105px 1fr; padding: 11px 0; }
  .privacy-note { right: 34px; bottom: 48px; left: 34px; }
  .rule { margin: 20px 0 48px; }
  .document-page h2 { font-size: 29px; }
  .body-copy { font-size: 13px; line-height: 1.65; }
  .summary-card { margin: 30px 0; }
  .summary-card div { padding: 13px 14px; }
  .fine-print { margin-top: 65px; }
  .scroll-cue { bottom: 14px; max-width: calc(100vw - 24px); overflow: hidden; text-overflow: ellipsis; }
}
@media (prefers-reduced-motion: reduce) { .mouse i, .spinner { animation: none; } }
</style>
