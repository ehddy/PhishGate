import type { CopyVariant } from "../../../types";


interface MovementCopy {
  secureAccess: string;
  connectionCheck: string;
  instruction: (brand: string | null) => string;
  idleLabel: string;
  verifiedLabel: string;
  redirecting: string;
  footnote: string;
}

export const ENGLISH_MOVEMENT_COPY: MovementCopy = {
  secureAccess: "Secure access",
  connectionCheck: "Connection check",
  instruction: (brand) => `Move your mouse inside the box below to verify your connection and continue to the ${brand ? `${brand} page` : "requested page"}.`,
  idleLabel: "Move your mouse here",
  verifiedLabel: "Verified",
  redirecting: "Verified — redirecting…",
  footnote: "This check confirms an active mouse connection before continuing.",
};

export function movementCopy(): MovementCopy {
  return ENGLISH_MOVEMENT_COPY;
}

export function movementFootnote(copy: MovementCopy, variant: CopyVariant): string {
  return variant === "concise" ? "" : copy.footnote;
}
