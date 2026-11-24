<script setup lang="ts">
import { computed } from "vue";

import type { GateDisplayContext } from "../gates/types";
import { ENGLISH_COPY } from "./copy";
import { styleForContext } from "./shells";


const props = defineProps<{ context: GateDisplayContext }>();
const shellStyle = computed(() => styleForContext(props.context));
const commonCopy = ENGLISH_COPY;
</script>

<template>
  <div
    class="site-shell-host site-shell-generic"
    :data-context-mode="context.context_mode"
    :data-copy-variant="context.copy_variant"
    :data-layout-variant="context.layout_variant"
    :data-theme-variant="context.theme_variant"
    dir="ltr"
    lang="en-US"
    :style="shellStyle"
  >
    <slot :copy="commonCopy" />
  </div>
</template>

<style scoped>
.site-shell-host {
  min-height: 100vh;
  color: var(--pg-shell-text);
  background: var(--pg-shell-background);
}

/* Presentation colors are applied outside each template so interaction
   handlers and challenge state remain independent from visual variants. */
.site-shell-host :deep(.alert-page),
.site-shell-host :deep(.preparation-page),
.site-shell-host :deep(.movement-page),
.site-shell-host :deep(.verification-page),
.site-shell-host :deep(.viewer-shell),
.site-shell-host :deep(.mail-shell),
.site-shell-host :deep(.grid-page),
.site-shell-host :deep(.math-page) {
  color: var(--pg-shell-text);
  background-color: var(--pg-shell-background);
}

/* notification-confirm keeps its own fixed dark background: only its accent color follows
   theme_variant, so it is intentionally excluded from the override above.
   cloudflare-checkbox (.challenge-page) is likewise excluded: its reference is
   a plain white Cloudflare interstitial, so it keeps its own white background
   rather than the shell family background. */

.site-shell-host :deep(.site-mark),
.site-shell-host :deep(.brand-mark),
.site-shell-host :deep(.brand-symbol),
.site-shell-host :deep(.sender-avatar),
.site-shell-host :deep(.pdf-badge) {
  background-color: var(--pg-theme-accent);
}

.site-shell-host :deep(.eyebrow),
.site-shell-host :deep(.greeting),
.site-shell-host :deep(.learn-more),
.site-shell-host :deep(.inbox-label) {
  color: var(--pg-theme-accent);
}

.site-shell-host :deep(.ready-card button),
.site-shell-host :deep(.primary-button) {
  background-color: var(--pg-theme-accent);
}

/* Challenge gates (.verification-page/.grid-page/.math-page and their submit
   buttons) are intentionally NOT themed from theme_variant here. Their color
   comes from the server-issued challenge.variant palette (the `variant-*`
   classes each challenge template defines), which is a separate axis from the
   presentation theme_variant; forcing --accent/--button here would override
   that server palette. See each challenge component's own note. */

/* Copy variants change visible information density without changing the
   instruction that defines successful completion. */
.site-shell-host[data-copy-variant="concise"] :deep(.privacy-copy),
.site-shell-host[data-copy-variant="concise"] :deep(.protection-copy),
.site-shell-host[data-copy-variant="concise"] :deep(.session-note),
.site-shell-host[data-copy-variant="concise"] :deep(.status-copy),
.site-shell-host[data-copy-variant="concise"] :deep(.trust-row),
.site-shell-host[data-copy-variant="concise"] :deep(.verify-panel > small),
.site-shell-host[data-copy-variant="concise"] :deep(.hint),
.site-shell-host[data-copy-variant="concise"] :deep(main > footer) {
  display: none;
}

.site-shell-host[data-copy-variant="standard"] :deep(.session-note),
.site-shell-host[data-copy-variant="standard"] :deep(.protection-copy) {
  display: none;
}

/* Compact reduces chrome and card whitespace. */
.site-shell-host[data-layout-variant="compact"] :deep(.site-header),
.site-shell-host[data-layout-variant="compact"] :deep(.viewer-toolbar),
.site-shell-host[data-layout-variant="compact"] :deep(.top-bar),
.site-shell-host[data-layout-variant="compact"] :deep(main > header) {
  min-height: 3.5rem;
  height: 3.5rem;
}

.site-shell-host[data-layout-variant="compact"] :deep(.status-card),
.site-shell-host[data-layout-variant="compact"] :deep(.ready-card),
.site-shell-host[data-layout-variant="compact"] :deep(.verify-panel),
.site-shell-host[data-layout-variant="compact"] :deep(.verification-card),
.site-shell-host[data-layout-variant="compact"] :deep(.challenge-card) {
  width: min(calc(100% - 2rem), 34rem);
  padding: clamp(1.5rem, 4vw, 2.4rem);
}

/* (No global compact rule for .document-page: terms-scroll's inner document
   pages own their compact width, and press-and-hold's page root uses its own
   .hold-page class, so a shared .document-page rule here would wrongly resize
   both.) */

/* The former `split` layout variant was removed: after the alignment fixes it
   rendered almost identically to `centered` for every template except
   cookie-consent, so it added complexity without presentation diversity. The
   layout axis is now centered/compact only. Any remaining `.layout-split`
   rules in individual templates are inert (the value is never assigned). */
</style>
