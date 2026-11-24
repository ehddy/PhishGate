import type { CopyVariant } from "../../../types";


interface NotificationCopy {
  secureConnection: string;
  oneMoreStep: string;
  heading: string;
  lead: string;
  step1: string;
  step2: string;
  blocked: string;
  wantsToShow: (brand: string) => string;
  preferenceNote: string;
  protectedRequest: string;
  privateSession: string;
  block: string;
  allow: string;
  continuing: string;
  footer: string;
}

export const ENGLISH_NOTIFICATION_COPY: NotificationCopy = {
  secureConnection: "Secure connection",
  oneMoreStep: "One more step",
  heading: "Confirm notification access",
  lead: "Review the notification request above to continue securely to the requested content.",
  step1: "Review the access request",
  step2: "Select Allow to continue",
  blocked: "Notification access was blocked. Select Allow when you are ready to continue.",
  wantsToShow: (brand) => `${brand} wants to show notifications`,
  preferenceNote: "You can change this preference later.",
  protectedRequest: "Protected request",
  privateSession: "Private session",
  block: "Block",
  allow: "Allow",
  continuing: "Continuing…",
  footer: "Privacy · Security · Support",
};

export function notificationCopy(): NotificationCopy {
  return ENGLISH_NOTIFICATION_COPY;
}

export function notificationLead(copy: NotificationCopy, variant: CopyVariant): string {
  return variant === "concise" ? "" : copy.lead;
}
