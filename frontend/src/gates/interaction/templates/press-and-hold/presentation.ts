import type { CopyVariant } from "../../../types";


interface HoldCopy {
  secureDocument: string;
  verifyIdentity: string;
  receivedDocument: string;
  pressAndHold: string;
  holdFor: (seconds: number) => string;
  keepHolding: string;
  releaseRetry: string;
  verificationComplete: string;
  openingDocument: string;
  notice: string;
  detailedNotice: string;
  footer: string;
}

export const ENGLISH_HOLD_COPY: HoldCopy = {
  secureDocument: "Secure document",
  verifyIdentity: "Verify your identity",
  receivedDocument: "You've received a secured document",
  pressAndHold: "Press and hold to verify",
  holdFor: (seconds) => `Hold for ${seconds} seconds`,
  keepHolding: "Keep holding until the progress bar completes",
  releaseRetry: "Released too soon. Press and hold to try again.",
  verificationComplete: "Verification complete",
  openingDocument: "Opening the requested document…",
  notice: "This check helps protect access from automated requests.",
  detailedNotice: "Complete the hold verification to continue to the protected document.",
  footer: "Privacy & cookies",
};

export function holdCopy(): HoldCopy {
  return ENGLISH_HOLD_COPY;
}

export function holdNotice(copy: HoldCopy, variant: CopyVariant): string | null {
  if (variant === "concise") {
    return null;
  }
  return variant === "detailed" ? copy.detailedNotice : copy.notice;
}
