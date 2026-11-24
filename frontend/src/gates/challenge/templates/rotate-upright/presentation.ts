import type { CopyVariant } from "../../../types";


export interface RotateUprightCopy {
  eyebrow: string;
  heading: string;
  instruction: string;
  detail: string;
  sliderLabel: string;
  verifyContinue: string;
  checking: string;
  imageUnavailable: string;
  privacy: string;
  help: string;
  security: string;
}

export const ENGLISH_ROTATE_UPRIGHT_COPY: RotateUprightCopy = {
  eyebrow: "Verification required",
  heading: "Rotate the image upright",
  instruction: "Use the slider to turn the picture the right way up, then continue.",
  detail: "This verification keeps automated clients from reaching the page.",
  sliderLabel: "Rotation",
  verifyContinue: "Verify and continue",
  checking: "Checking…",
  imageUnavailable: "The verification image could not be loaded.",
  privacy: "Privacy",
  help: "Help",
  security: "Security",
};

export function rotateUprightCopy(): RotateUprightCopy {
  return ENGLISH_ROTATE_UPRIGHT_COPY;
}

// Information density follows copy_variant without changing the completion
// condition (submitting the server-validated upright rotation).
export function rotateUprightInstruction(
  copy: RotateUprightCopy,
  variant: CopyVariant,
): string {
  if (variant === "concise") return copy.instruction;
  return `${copy.instruction} ${copy.detail}`;
}
