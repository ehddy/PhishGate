import type { CopyVariant } from "../../../types";


interface SlideCopy {
  encryptedConnection: string;
  eyebrow: string;
  verifyHuman: string;
  verificationComplete: string;
  slideInstruction: string;
  redirecting: string;
  notice: string;
  slideToVerify: string;
  verified: string;
  hintDrag: string;
  hintOpening: string;
  footer: string;
}

export const ENGLISH_SLIDE_COPY: SlideCopy = {
  encryptedConnection: "Encrypted connection",
  eyebrow: "Security verification",
  verifyHuman: "Verify you're human",
  verificationComplete: "Verification complete",
  slideInstruction: "Slide the control to the right to continue to the requested page.",
  redirecting: "Your request was verified. Redirecting securely…",
  notice: "This step helps protect access from automated requests.",
  slideToVerify: "Slide to verify",
  verified: "Verified",
  hintDrag: "Drag the round handle all the way across",
  hintOpening: "Opening the requested content",
  footer: "Privacy · Security · Help",
};

export function slideCopy(): SlideCopy {
  return ENGLISH_SLIDE_COPY;
}

export function slideNotice(copy: SlideCopy, variant: CopyVariant): string {
  return variant === "concise" ? "" : copy.notice;
}
