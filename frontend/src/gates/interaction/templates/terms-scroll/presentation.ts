import type { CopyVariant } from "../../../types";


interface TermsScrollCopy {
  documentServices: string;
  secureDelivery: string;
  confidential: string;
  heading: string;
  lead: string;
  detailedLead: string;
  documentLabel: string;
  referenceLabel: string;
  preparedLabel: string;
  statusLabel: string;
  statusReady: string;
  privacyNote: string;
  documentSummary: string;
  reviewDetails: string;
  summaryBody: string;
  packageType: string;
  packageTypeValue: string;
  pageCount: string;
  pageCountValue: string;
  deliveryMethod: string;
  deliveryMethodValue: string;
  reviewStatus: string;
  reviewStatusValue: string;
  importantInfo: string;
  importantInfoBody: string;
  finalPage: string;
  documentReview: string;
  finalBody: string;
  reviewMarkAvailable: string;
  reviewMarkNote: string;
  confidentialityNotice: string;
  confidentialityBody: string;
  scrollCue: string;
  openingDocument: string;
}

export const ENGLISH_TERMS_SCROLL_COPY: TermsScrollCopy = {
  documentServices: "DOCUMENT SERVICES",
  secureDelivery: "SECURE DELIVERY",
  confidential: "PRIVATE & CONFIDENTIAL",
  heading: "Document available for review",
  lead: "A secure document has been shared with you.",
  detailedLead: "Review all pages to continue to the requested destination.",
  documentLabel: "Document",
  referenceLabel: "Reference",
  preparedLabel: "Prepared",
  statusLabel: "Status",
  statusReady: "Ready for review",
  privacyNote: "This document may contain private information intended only for its recipient.",
  documentSummary: "DOCUMENT SUMMARY",
  reviewDetails: "Review details",
  summaryBody: "The following summary confirms the document package prepared for this session. Review the delivery information and continue through each page for the complete notice.",
  packageType: "Package type",
  packageTypeValue: "Electronic document",
  pageCount: "Number of pages",
  pageCountValue: "3 pages",
  deliveryMethod: "Delivery method",
  deliveryMethodValue: "Secure web viewer",
  reviewStatus: "Review status",
  reviewStatusValue: "In progress",
  importantInfo: "Important information",
  importantInfoBody: "Please review the complete document before leaving this viewer. Access is limited to this browser session and the document is not sent to any external service.",
  finalPage: "FINAL PAGE",
  documentReview: "Document review",
  finalBody: "You have reached the final section of the shared document. The viewer will continue automatically when the document has been fully reviewed.",
  reviewMarkAvailable: "Document available",
  reviewMarkNote: "All three pages are ready to view.",
  confidentialityNotice: "Confidentiality notice",
  confidentialityBody: "The contents of this document are intended only for the designated recipient. If you received this notice in error, close the viewer and contact the sender.",
  scrollCue: "Scroll to review the complete document",
  openingDocument: "Opening document…",
};

export function termsScrollCopy(): TermsScrollCopy {
  return ENGLISH_TERMS_SCROLL_COPY;
}

export function termsScrollLead(copy: TermsScrollCopy, variant: CopyVariant): string {
  if (variant === "concise") return copy.lead;
  return `${copy.lead} ${copy.detailedLead}`;
}
