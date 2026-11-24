import type { CopyVariant } from "../../../types";


interface CustomDigitCopy {
  protectedSession: string;
  securityCheck: string;
  verifyHuman: string;
  instruction: (digitCount: number) => string;
  detailedNote: string;
  verificationCode: string;
  enterDigits: string;
  imageUnavailable: string;
  checking: string;
  verifyContinue: string;
  privacyCopy: string;
  privacy: string;
  help: string;
  security: string;
}

export const ENGLISH_CUSTOM_DIGIT_COPY: CustomDigitCopy = {
  protectedSession: "Protected session",
  securityCheck: "SECURITY CHECK",
  verifyHuman: "Verify you're human",
  instruction: (digitCount) => `Enter the ${digitCount} digits shown below to continue to the requested page.`,
  detailedNote: "The image refreshes only if you leave and return to this page.",
  verificationCode: "Verification code",
  enterDigits: "Enter digits",
  imageUnavailable: "Verification image unavailable",
  checking: "Checking…",
  verifyContinue: "Verify & Continue",
  privacyCopy: "The entered code is checked only for this local browser session.",
  privacy: "Privacy",
  help: "Help",
  security: "Security",
};

export function customDigitCopy(): CustomDigitCopy {
  return ENGLISH_CUSTOM_DIGIT_COPY;
}

export function customDigitInstruction(copy: CustomDigitCopy, digitCount: number, variant: CopyVariant): string {
  const base = copy.instruction(digitCount);
  return variant === "detailed" ? `${base} ${copy.detailedNote}` : base;
}
