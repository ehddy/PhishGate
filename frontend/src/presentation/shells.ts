import type { CSSProperties } from "vue";

import type { GateDisplayContext } from "../gates/types";


const GENERIC_SHELL = { background: "#f5f7fa", surface: "#ffffff", text: "#202733" };

const THEME_TOKENS = {
  blue: { accent: "#2563c9", accentSoft: "#e8f0ff" },
  mint: { accent: "#237a63", accentSoft: "#e3f4ee" },
  slate: { accent: "#475569", accentSoft: "#e9edf2" },
  violet: { accent: "#6d4ac7", accentSoft: "#eee9fb" },
} as const;

export function styleForContext(context: GateDisplayContext): CSSProperties {
  const family = GENERIC_SHELL;
  const theme = THEME_TOKENS[context.theme_variant];
  // Tint the shell background (and, more lightly, the card surface) toward the
  // theme accent so theme_variant visibly changes the page's overall hue, not
  // just small accent elements. The tint is subtle enough to keep text contrast.
  return {
    "--pg-shell-background": `color-mix(in srgb, ${family.background} 88%, ${theme.accent})`,
    "--pg-shell-surface": `color-mix(in srgb, ${family.surface} 96%, ${theme.accent})`,
    "--pg-shell-text": family.text,
    "--pg-theme-accent": theme.accent,
    "--pg-theme-accent-soft": theme.accentSoft,
  } as CSSProperties;
}
