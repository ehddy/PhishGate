import type { CopyVariant } from "../../../types";


export interface AreaSelectCopy {
  eyebrow: string;
  headingPrefix: string;
  headingSuffix: string;
  instruction: string;
  detail: string;
  verifyContinue: string;
  checking: string;
  imageUnavailable: string;
  selectedNote: string;
  privacy: string;
  help: string;
  security: string;
  categories: Record<string, string>;
}

export const ENGLISH_AREA_SELECT_COPY: AreaSelectCopy = {
  eyebrow: "Verification required",
  headingPrefix: "Select the ",
  headingSuffix: "",
  instruction: "Click the requested item in the image to continue.",
  detail: "This verification keeps automated clients from reaching the page.",
  verifyContinue: "Verify and continue",
  checking: "Checking…",
  imageUnavailable: "The verification image could not be loaded.",
  selectedNote: "Selection marked — verify to continue.",
  privacy: "Privacy",
  help: "Help",
  security: "Security",
  categories: {},
};

export function areaSelectCopy(): AreaSelectCopy {
  return ENGLISH_AREA_SELECT_COPY;
}

export function areaSelectCategoryLabel(copy: AreaSelectCopy, category: string): string {
  return copy.categories[category] ?? category;
}

// Information density follows copy_variant without changing the completion
// condition (clicking the correct region).
export function areaSelectInstruction(
  copy: AreaSelectCopy,
  variant: CopyVariant,
): string {
  if (variant === "concise") return copy.instruction;
  return `${copy.instruction} ${copy.detail}`;
}
