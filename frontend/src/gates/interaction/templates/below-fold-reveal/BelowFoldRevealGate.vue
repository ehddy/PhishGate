<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { GateDisplayContext } from "../../../types";
import { belowFoldAdditionalInfo, belowFoldCopy } from "./presentation";

const props = defineProps<{
  displayContext: GateDisplayContext;
  parameters?: Record<string, unknown>;
}>();
const emit = defineEmits<{ complete: [] }>();

onMounted(() => {
  document.title = "Delivery Status Notification (Failure) - Inbox";
});

const messageViewport = ref<HTMLElement | null>(null);
const completing = ref(false);
const brand = computed(() => props.displayContext.brand?.trim() || "Message Center");
const copy = computed(() => belowFoldCopy());
const additionalInfo = computed(() => belowFoldAdditionalInfo(copy.value, props.displayContext.copy_variant));
const thresholdPercent = computed(() => {
  const configured = props.parameters?.threshold_percent;
  return typeof configured === "number" && configured > 0 && configured <= 100
    ? configured
    : 82;
});

function handleScroll(): void {
  const container = messageViewport.value;
  if (!container || completing.value) return;

  const maxScroll = container.scrollHeight - container.clientHeight;
  const progress = maxScroll > 0 ? (container.scrollTop / maxScroll) * 100 : 0;
  if (progress >= thresholdPercent.value) {
    completing.value = true;
    emit("complete");
  }
}
</script>

<template>
  <main class="mail-shell" :class="`layout-${displayContext.layout_variant}`" :data-variant-id="displayContext.variant_id">
    <header class="top-bar">
      <div class="mail-brand">
        <span class="menu-icon" aria-hidden="true">☰</span>
        <span class="envelope-mark" aria-hidden="true">✉</span>
        <strong>Mail</strong>
      </div>
      <div class="search-box" aria-hidden="true"><span>⌕</span> {{ copy.searchMessages }}</div>
      <div class="top-actions" aria-hidden="true"><span>?</span><span>⚙</span><i>M</i></div>
    </header>

    <div class="workspace">
      <aside class="sidebar" aria-hidden="true">
        <div class="compose-button"><span>＋</span>{{ copy.compose }}</div>
        <nav>
          <span class="active">▣ <b>{{ copy.inbox }}</b><small>12</small></span>
          <span>☆ {{ copy.starred }}</span>
          <span>◷ {{ copy.snoozed }}</span>
          <span>➤ {{ copy.sent }}</span>
          <span>▤ {{ copy.drafts }}</span>
        </nav>
        <div class="storage"><span></span><small>{{ copy.storageNote }}</small></div>
      </aside>

      <section class="message-panel">
        <div class="message-actions" aria-hidden="true">
          <span>←</span><span>▣</span><span>⌫</span><span>✉</span><i></i><span>◀</span><span>▶</span>
        </div>

        <div
          ref="messageViewport"
          class="message-viewport"
          role="region"
          aria-label="Scrollable message"
          tabindex="0"
          @scroll.passive="handleScroll"
        >
          <article class="message">
            <div class="subject-row">
              <h1>{{ copy.deliveryNotification }}</h1>
              <span class="inbox-label">{{ copy.inboxLabel }}</span>
              <span class="subject-tools" aria-hidden="true">☆ ⤴ ⋮</span>
            </div>

            <div class="sender-row">
              <span class="sender-avatar" aria-hidden="true">M</span>
              <div class="sender-copy">
                <strong>{{ copy.mailDeliveryService }}</strong>
                <span>&lt;delivery@message-center.test&gt;</span>
                <small>{{ copy.toMe }}</small>
              </div>
              <time>10:21 AM</time>
            </div>

            <div class="delivery-card">
              <span class="notice-icon" aria-hidden="true">?</span>
              <h2>{{ copy.addressNotFound }}</h2>
              <p>{{ copy.addressNotFoundBody }}</p>
              <span class="learn-more">{{ copy.learnMore }}</span>
            </div>

            <section class="response-copy">
              <h3>{{ copy.responseWas }}</h3>
              <p>{{ copy.responseBody }}</p>
              <p>{{ copy.automatedNotice(brand) }}</p>
            </section>

            <div class="spacer-copy" aria-hidden="true">
              <span></span><span></span><span></span><span></span>
            </div>

            <section class="reveal-card" aria-label="Additional message details">
              <span class="shield" aria-hidden="true">✓</span>
              <div>
                <p class="eyebrow">{{ copy.messageDetails }}</p>
                <h2>{{ copy.additionalInfo }}</h2>
                <p v-if="additionalInfo">{{ additionalInfo }}</p>
              </div>
            </section>

            <div class="reply-actions" aria-hidden="true">
              <button type="button" tabindex="-1">↩ {{ copy.reply }}</button>
              <button type="button" tabindex="-1">→ {{ copy.forward }}</button>
            </div>
          </article>
        </div>
      </section>
    </div>

    <div v-if="!completing" class="scroll-cue" aria-hidden="true">
      <span>↓</span> {{ copy.scrollCue }}
    </div>
    <div v-else class="opening-overlay" role="status" aria-live="assertive">
      <span class="spinner" aria-hidden="true"></span><strong>{{ copy.openingMessage }}</strong>
    </div>
  </main>
</template>

<style scoped>
:global(*) { box-sizing: border-box; }
:global(html), :global(body), :global(#app) { height: 100%; }
:global(body) { margin: 0; overflow: hidden; font-family: Arial, Helvetica, sans-serif; }
.mail-shell { height: 100vh; overflow: hidden; background: #f6f8fc; color: #202124; }
.top-bar { display: grid; height: 64px; grid-template-columns: 238px minmax(280px, 720px) 1fr; align-items: center; gap: 18px; padding: 8px 18px; border-bottom: 1px solid #e7e9ed; background: #f6f8fc; }
.mail-brand { display: flex; align-items: center; gap: 12px; color: #3c4043; font-size: 21px; }
.menu-icon { color: #5f6368; font-size: 20px; }
.envelope-mark { display: grid; width: 34px; height: 28px; place-items: center; border-radius: 6px; color: #fff; background: linear-gradient(135deg, var(--pg-theme-accent, #4285f4), color-mix(in srgb, var(--pg-theme-accent, #4285f4) 75%, #000)); font-size: 17px; }
.search-box { display: flex; height: 46px; align-items: center; gap: 14px; padding: 0 18px; border-radius: 24px; color: #5f6368; background: #eaf1fb; font-size: 14px; }
.search-box span { font-size: 24px; transform: rotate(-20deg); }
.top-actions { display: flex; align-items: center; justify-content: flex-end; gap: 20px; color: #5f6368; font-size: 18px; }
.top-actions i { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 50%; color: white; background: #a142f4; font-size: 14px; font-style: normal; }
.workspace { display: flex; height: calc(100vh - 64px); }
.sidebar { flex: 0 0 238px; padding: 14px 12px; color: #3c4043; }
.compose-button { display: flex; width: 145px; height: 54px; align-items: center; gap: 13px; margin: 0 0 17px 2px; padding: 0 20px; border-radius: 16px; background: #c2e7ff; box-shadow: 0 1px 2px rgba(60, 64, 67, .2); font-size: 14px; }
.compose-button span { font-size: 25px; font-weight: 300; }
.sidebar nav { display: grid; gap: 2px; }
.sidebar nav > span { display: flex; height: 32px; align-items: center; gap: 15px; padding: 0 14px 0 20px; border-radius: 0 17px 17px 0; font-size: 14px; }
.sidebar nav .active { background: color-mix(in srgb, var(--pg-theme-accent, #4285f4) 18%, #fff); color: #1f1f1f; }
.sidebar nav small { margin-left: auto; font-size: 12px; font-weight: 700; }
.storage { margin: 38px 14px 0 20px; }
.storage span { display: block; height: 4px; margin-bottom: 8px; border-radius: 3px; background: linear-gradient(90deg, var(--pg-theme-accent, #4285f4) 0 18%, #dfe3e7 18%); }
.storage small { color: #747775; font-size: 10px; }
.message-panel { display: flex; min-width: 0; flex: 1; flex-direction: column; overflow: hidden; border-radius: 15px 0 0; background: white; box-shadow: 0 1px 2px rgba(60, 64, 67, .12); }
.message-actions { display: flex; height: 49px; flex: 0 0 49px; align-items: center; gap: 25px; padding: 0 22px; border-bottom: 1px solid #eef0f2; color: #5f6368; font-size: 17px; }
.message-actions i { flex: 1; }
.message-viewport { flex: 1; min-height: 0; overflow-y: auto; outline: none; scroll-behavior: smooth; }
.message-viewport:focus-visible { box-shadow: inset 0 0 0 2px #6ea8fe; }
.message { width: min(960px, 100%); margin: 0 auto; padding: 26px 54px 90px; }
.subject-row { display: flex; align-items: center; gap: 12px; padding-left: 54px; }
.subject-row h1 { margin: 0; font-size: 23px; font-weight: 400; }
.inbox-label { padding: 3px 7px; border-radius: 4px; background: #e7e7e7; color: #5f6368; font-size: 11px; }
.subject-tools { margin-left: auto; color: #5f6368; word-spacing: 13px; }
.sender-row { display: flex; align-items: flex-start; gap: 12px; margin: 30px 0; }
.sender-avatar { display: grid; width: 42px; height: 42px; flex: 0 0 42px; place-items: center; border-radius: 50%; color: white; background: #e8710a; font-size: 19px; }
.sender-copy { display: flex; min-width: 0; flex: 1; flex-wrap: wrap; align-items: baseline; gap: 5px; padding-top: 4px; }
.sender-copy strong { font-size: 14px; }
.sender-copy span { overflow: hidden; color: #5f6368; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.sender-copy small { width: 100%; margin-top: 4px; color: #5f6368; font-size: 12px; }
.sender-row time { padding-top: 5px; color: #5f6368; font-size: 12px; }
.delivery-card { margin: 38px 20px 55px 54px; padding: 38px 44px; border: 1px solid #dadce0; border-radius: 2px; }
.notice-icon { display: grid; width: 56px; height: 66px; place-items: center; margin-bottom: 25px; border: 7px solid #f6a623; color: #f6a623; font-size: 34px; font-weight: 700; }
.delivery-card h2 { margin: 0 0 22px; font-size: 26px; }
.delivery-card p { max-width: 660px; margin: 0 0 27px; color: #6f7275; font-size: 20px; line-height: 1.48; }
.learn-more { color: var(--pg-theme-accent, #1a73e8); font-size: 14px; font-weight: 700; }
.response-copy { margin: 0 40px 0 54px; }
.response-copy h3 { margin: 0 0 24px; font-size: 20px; font-weight: 400; }
.response-copy p { max-width: 740px; margin: 0 0 18px; color: #34373a; font-family: "Courier New", monospace; font-size: 15px; line-height: 1.55; }
.spacer-copy { display: grid; gap: 13px; min-height: 48vh; align-content: center; margin: 10px 54px; }
.spacer-copy span { display: block; height: 9px; border-radius: 5px; background: #f1f3f4; }
.spacer-copy span:nth-child(2) { width: 91%; }
.spacer-copy span:nth-child(3) { width: 72%; }
.spacer-copy span:nth-child(4) { width: 84%; }
.reveal-card { display: flex; align-items: flex-start; gap: 20px; margin: 0 40px 36px 54px; padding: 28px; border: 1px solid #c8d8ef; border-radius: 10px; background: color-mix(in srgb, var(--pg-theme-accent, #1a73e8) 6%, #fff); }
.shield { display: grid; width: 44px; height: 44px; flex: 0 0 44px; place-items: center; border-radius: 50%; color: white; background: var(--pg-theme-accent, #1a73e8); font-size: 21px; }
.eyebrow { margin: 1px 0 8px; color: #526a8b; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; }
.reveal-card h2 { margin: 0 0 8px; font-size: 19px; }
.reveal-card p:last-child { margin: 0; color: #5f6368; font-size: 14px; line-height: 1.5; }
.reply-actions { display: flex; gap: 10px; margin-left: 54px; }
.reply-actions button { padding: 10px 20px; border: 1px solid #dadce0; border-radius: 20px; color: #3c4043; background: white; font-size: 13px; }
.scroll-cue { position: fixed; z-index: 5; bottom: 20px; left: calc(50% + 119px); display: flex; align-items: center; gap: 9px; padding: 10px 15px; border-radius: 20px; color: white; background: rgba(32, 33, 36, .9); box-shadow: 0 3px 10px rgba(0, 0, 0, .25); font-size: 12px; transform: translateX(-50%); pointer-events: none; }
.scroll-cue span { font-size: 17px; animation: nudge 1.4s ease-in-out infinite; }
.opening-overlay { position: fixed; z-index: 8; inset: 0; display: flex; align-items: center; justify-content: center; gap: 13px; color: #202124; background: rgba(255, 255, 255, .92); }
.spinner { width: 25px; height: 25px; border: 3px solid #d8e2f1; border-top-color: var(--pg-theme-accent, #1a73e8); border-radius: 50%; animation: spin .75s linear infinite; }
@keyframes nudge { 0%, 100% { transform: translateY(-2px); } 50% { transform: translateY(3px); } }
@keyframes spin { to { transform: rotate(360deg); } }

/* Mimics a real webmail client, so layout_variant maps to settings a real
   client actually offers rather than an arbitrary reflow: compact matches a
   denser row/spacing preset, split matches a "reading pane full width,
   sidebar hidden" focused-reading mode. */
.layout-compact .top-bar { height: 56px; }
.layout-compact .compose-button { height: 44px; }
.layout-compact .sidebar nav > span { height: 27px; }
.layout-compact .message { padding: 18px 44px 70px; }
.layout-compact .sender-row { margin: 18px 0; }
.layout-compact .delivery-card { margin: 24px 20px 34px 54px; padding: 26px 30px; }
.layout-compact .spacer-copy { min-height: 34vh; }

.layout-split .sidebar { display: none; }
.layout-split .message-panel { border-radius: 0; }
.layout-split .message { width: min(1120px, 100%); }
/* The base .scroll-cue uses left: calc(50% + 119px) to centre over the message
   panel, offsetting half the 238px sidebar. Split hides the sidebar, so the
   cue must re-centre on the viewport. */
.layout-split .scroll-cue { left: 50%; }

@media (max-width: 760px) {
  .top-bar { height: 58px; grid-template-columns: 1fr auto; padding: 7px 14px; background: #eef3fb; }
  .mail-brand { font-size: 0; }
  .mail-brand strong, .search-box { display: none; }
  .top-actions span { display: none; }
  .workspace { height: calc(100vh - 58px); }
  .sidebar { display: none; }
  .message-panel { border-radius: 0; }
  .message-actions { height: 50px; flex-basis: 50px; gap: 23px; padding: 0 18px; background: #eef3fb; }
  .message-actions span:nth-of-type(2), .message-actions span:nth-of-type(3) { display: none; }
  .message { padding: 18px 16px 85px; }
  .subject-row { flex-wrap: wrap; padding-left: 0; }
  .subject-row h1 { flex: 1 0 calc(100% - 60px); font-size: 24px; line-height: 1.35; }
  .subject-tools { display: none; }
  .sender-row { margin: 25px 0 34px; }
  .sender-copy span { display: none; }
  .delivery-card { margin: 0 0 50px; padding: 34px 26px; }
  .delivery-card h2 { font-size: 25px; }
  .delivery-card p { font-size: 18px; }
  .response-copy { margin: 0 18px; }
  .response-copy h3 { font-size: 20px; }
  .response-copy p { font-size: 14px; }
  .spacer-copy { min-height: 52vh; margin: 4px 18px; }
  .reveal-card { margin: 0 0 30px; padding: 22px 18px; }
  .reveal-card h2 { font-size: 18px; }
  .reply-actions { margin-left: 0; }
  .scroll-cue { bottom: 16px; left: 50%; }
}
@media (prefers-reduced-motion: reduce) { .scroll-cue span, .spinner { animation: none; } }
</style>
