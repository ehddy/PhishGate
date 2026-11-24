import type { CopyVariant } from "../../../types";


interface DocumentReadyCopy {
  secureDelivery: string;
  greeting: string;
  heading: string;
  description: string;
  progressLabel: string;
  readyStatus: string;
  continueLabel: string;
  opening: string;
  sessionNote: string;
  privacy: string;
  helpCenter: string;
  secureAccess: string;
}

export const ENGLISH_DOCUMENT_READY_COPY: DocumentReadyCopy = {
  secureDelivery: "Secure document delivery",
  greeting: "Your requested file is available",
  heading: "Preparing Your Document",
  description: "Your secure document has been prepared and is ready to open in this browser.",
  progressLabel: "Document preparation",
  readyStatus: "Your document is ready",
  continueLabel: "Continue",
  opening: "Opening…",
  sessionNote: "This secure session will continue in the current window.",
  privacy: "Privacy",
  helpCenter: "Help Center",
  secureAccess: "Secure access",
};

export function documentReadyCopy(): DocumentReadyCopy {
  return ENGLISH_DOCUMENT_READY_COPY;
}

export function documentReadyDescription(copy: DocumentReadyCopy, variant: CopyVariant): string {
  return variant === "concise" ? "" : copy.description;
}
