// Runtime single source of truth for the presentation variant value lists.
//
// types.ts derives its unions from these arrays (`typeof X[number]`), and the
// screenshot harness reads these literals out of this file, so the allowed
// values live in exactly one place. The order here is only a listing order;
// the backend derives which value a gate actually gets (presentation.py).
export const CONTEXT_MODES = ["neutral", "brand-label"] as const;
export const LAYOUT_VARIANTS = ["centered", "compact"] as const;
export const COPY_VARIANTS = ["concise", "standard", "detailed"] as const;
export const THEME_VARIANTS = ["blue", "mint", "slate", "violet"] as const;
