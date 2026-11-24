import type { CopyVariant } from "../../../types";


export interface TextCaptchaCopy {
  eyebrow: string;
  heading: string;
  instruction: string;
  detail: string;
  inputLabel: string;
  placeholder: string;
  verifyContinue: string;
  checking: string;
  caseNote: string;
  imageUnavailable: string;
  privacy: string;
  help: string;
  security: string;
}

export const ENGLISH_TEXT_CAPTCHA_COPY: TextCaptchaCopy = {
  eyebrow: "Verification required",
  heading: "Type the characters you see",
  instruction: "Enter the characters shown in the image to continue.",
  detail: "This verification keeps automated clients from reaching the page.",
  inputLabel: "Characters",
  placeholder: "Enter the characters",
  verifyContinue: "Verify and continue",
  checking: "Checking…",
  caseNote: "Not case-sensitive.",
  imageUnavailable: "The verification image could not be loaded.",
  privacy: "Privacy",
  help: "Help",
  security: "Security",
};

export function textCaptchaCopy(): TextCaptchaCopy {
  return ENGLISH_TEXT_CAPTCHA_COPY;
}

// Information density follows copy_variant without changing the completion
// condition (entering the server-validated characters).
export function textCaptchaInstruction(
  copy: TextCaptchaCopy,
  variant: CopyVariant,
): string {
  if (variant === "concise") return copy.instruction;
  return `${copy.instruction} ${copy.detail}`;
}
