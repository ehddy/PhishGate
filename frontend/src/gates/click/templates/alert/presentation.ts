import type { CopyVariant } from "../../../types";


interface AlertCopy {
  protectedContent: string;
  oneMoment: string;
  preparing: string;
  opening: string;
  keepWindowOpen: string;
  securityNotice: string;
  containsProtectedContent: (brand: string | null) => string;
  selectOk: string;
  detailedNote: string;
}

export const ENGLISH_ALERT_COPY: AlertCopy = {
  protectedContent: "Protected content",
  oneMoment: "One moment",
  preparing: "Preparing protected content…",
  opening: "Opening the requested page…",
  keepWindowOpen: "Keep this window open while the page is prepared.",
  securityNotice: "security notice",
  containsProtectedContent: (brand) => brand ? `This page contains protected ${brand} content.` : "This page contains protected content.",
  selectOk: "Select OK to continue.",
  detailedNote: "Keep this window open while the requested page is prepared.",
};

export function alertCopy(): AlertCopy {
  return ENGLISH_ALERT_COPY;
}

export function alertDialogText(copy: AlertCopy, brand: string | null, variant: CopyVariant): { title: string; message: string } {
  const title = brand ? `${brand} ${copy.securityNotice}` : copy.securityNotice;
  const subject = copy.containsProtectedContent(brand);
  const message = variant === "concise"
    ? subject
    : variant === "detailed"
      ? `${subject} ${copy.selectOk} ${copy.detailedNote}`
      : `${subject} ${copy.selectOk}`;
  return { title, message };
}
