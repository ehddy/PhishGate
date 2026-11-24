import type { CopyVariant } from "../../../types";


export interface BlurredPreviewCopy {
  docLabel: string;
  eyebrow: string;
  heading: string;
  lead: string;
  detail: string;
  viewLabel: string;
  opening: string;
  statusNote: string;
  secured: string;
}

export const ENGLISH_BLURRED_PREVIEW_COPY: BlurredPreviewCopy = {
  docLabel: "Shared document",
  eyebrow: "Preview locked",
  heading: "View this document",
  lead: "This document is ready. Confirm below to load the full preview in this window.",
  detail: "The preview stays blurred until you continue. No sign-in is required for this step.",
  viewLabel: "View document",
  opening: "Loading…",
  statusNote: "You will be taken to the document automatically.",
  secured: "Secured preview",
};

export function blurredPreviewCopy(): BlurredPreviewCopy {
  return ENGLISH_BLURRED_PREVIEW_COPY;
}

// Information density follows copy_variant without changing the completion
// condition (a single View click).
export function blurredPreviewDetail(
  copy: BlurredPreviewCopy,
  variant: CopyVariant,
): string {
  if (variant === "concise") return "";
  if (variant === "standard") return copy.lead;
  return `${copy.lead} ${copy.detail}`;
}
