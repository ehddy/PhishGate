import type { CopyVariant } from "../../../types";


interface CloudflareCopy {
  headingSuffix: string;
  instruction: string;
  detailedInstruction: string;
  verify: string;
  verifying: string;
  success: string;
  statusIdle: string;
  statusChecking: string;
  privacy: string;
  help: string;
  performanceBy: string;
  rayIdLabel: string;
}

export const ENGLISH_CLOUDFLARE_COPY: CloudflareCopy = {
  headingSuffix: "needs to review the security of your connection",
  instruction: "Before proceeding, please verify that you are human.",
  detailedInstruction: "This additional step helps protect the site's owners from bots and automated traffic.",
  verify: "Verify you are human",
  verifying: "Verifying…",
  success: "Success!",
  statusIdle: "This process is automatic. Your browser will redirect shortly.",
  statusChecking: "Checking your browser before accessing the site…",
  privacy: "Privacy",
  help: "Help",
  performanceBy: "Performance & security by",
  rayIdLabel: "Ray ID",
};

export function cloudflareCopy(): CloudflareCopy {
  return ENGLISH_CLOUDFLARE_COPY;
}

export function cloudflareInstruction(copy: CloudflareCopy, variant: CopyVariant): string {
  if (variant === "concise") return "";
  return variant === "detailed" ? `${copy.instruction} ${copy.detailedInstruction}` : copy.instruction;
}
