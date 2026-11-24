import type { CopyVariant } from "../../../types";


interface MathChallengeCopy {
  secureConnection: string;
  humanVerification: string;
  verificationRequired: string;
  instruction: string;
  detailedNote: string;
  solveEquation: string;
  problemUnavailable: string;
  yourAnswer: string;
  enterAnswer: string;
  checking: string;
  verifyContinue: string;
  protectionCopy: string;
  privacy: string;
  security: string;
  help: string;
}

export const ENGLISH_MATH_COPY: MathChallengeCopy = {
  secureConnection: "Secure connection",
  humanVerification: "HUMAN VERIFICATION",
  verificationRequired: "Verification required",
  instruction: "Solve this quick problem to continue to the requested page.",
  detailedNote: "Only whole-number answers are accepted.",
  solveEquation: "Solve the equation",
  problemUnavailable: "Problem unavailable",
  yourAnswer: "Your answer",
  enterAnswer: "Enter your answer",
  checking: "Checking…",
  verifyContinue: "Verify & Continue",
  protectionCopy: "This check helps protect the requested service from automated access.",
  privacy: "Privacy",
  security: "Security",
  help: "Help",
};

export function mathChallengeCopy(): MathChallengeCopy {
  return ENGLISH_MATH_COPY;
}

export function mathChallengeInstruction(copy: MathChallengeCopy, variant: CopyVariant): string {
  return variant === "detailed" ? `${copy.instruction} ${copy.detailedNote}` : copy.instruction;
}
