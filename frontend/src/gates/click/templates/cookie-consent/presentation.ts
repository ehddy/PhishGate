import type { CopyVariant } from "../../../types";


interface CookieCopy {
  title: string;
  website: string;
  policyLink: string;
  accept: string;
  opening: string;
  closeLabel: string;
  baseNotice: (siteName: string) => string;
  standardDetail: string;
  detailedDetail: string;
}

export interface CookieShellCopy {
  eyebrow: string;
  title: string;
  description: string;
  action: string;
}

export const ENGLISH_COOKIE_COPY: CookieCopy = {
  title: "Cookie preferences",
  website: "This website",
  policyLink: "Read our Cookie Policy",
  accept: "Accept all",
  opening: "Opening…",
  closeLabel: "Close cookie notice",
  baseNotice: (siteName) => `${siteName} uses cookies to keep this site working properly.`,
  standardDetail: "We also use analytics to understand how visitors use our services.",
  detailedDetail: "You can review your choices and learn how we protect your information in our Cookie Policy.",
};

export const GENERIC_SHELL_COPY: CookieShellCopy = {
  eyebrow: "Services designed around you",
  title: "Everything you need, in one place.",
  description: "Discover useful information and services for your everyday needs.",
  action: "Explore services",
};

export function cookiePresentationCopy(): CookieCopy {
  return ENGLISH_COOKIE_COPY;
}

export function cookieDescription(copy: CookieCopy, variant: CopyVariant, siteName: string): string {
  const parts = [copy.baseNotice(siteName)];
  if (variant !== "concise") parts.push(copy.standardDetail);
  if (variant === "detailed") parts.push(copy.detailedDetail);
  return parts.join(" ");
}
