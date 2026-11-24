import type { CopyVariant } from "../../../types";


export interface SecurityCheckCopy {
  eyebrow: string;
  heading: string;
  lead: string;
  detail: string;
  reasonTitle: string;
  reasonOne: string;
  reasonTwo: string;
  continueLabel: string;
  verifying: string;
  statusNote: string;
  privacy: string;
  terms: string;
  help: string;
}

export const ENGLISH_SECURITY_CHECK_COPY: SecurityCheckCopy = {
  eyebrow: "Security checkpoint",
  heading: "Before you continue",
  lead: "We need to confirm this request before taking you to the page you asked for.",
  detail:
    "This extra step protects the destination from automated traffic. It only takes a moment and keeps your session in this window.",
  reasonTitle: "Why am I seeing this?",
  reasonOne: "The connection is being verified for security.",
  reasonTwo: "No account details are requested on this step.",
  continueLabel: "Continue",
  verifying: "Verifying…",
  statusNote: "You will be returned to the requested page automatically.",
  privacy: "Privacy",
  terms: "Terms",
  help: "Help",
};

export function securityCheckCopy(): SecurityCheckCopy {
  return ENGLISH_SECURITY_CHECK_COPY;
}

// Information density follows copy_variant without changing the completion
// condition (a single Continue click).
export function securityCheckDetail(
  copy: SecurityCheckCopy,
  variant: CopyVariant,
): string {
  if (variant === "concise") return "";
  if (variant === "standard") return copy.lead;
  return `${copy.lead} ${copy.detail}`;
}
