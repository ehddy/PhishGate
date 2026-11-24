

interface ImageGridCopy {
  protectedSession: string;
  securityCheck: string;
  verifyHuman: string;
  selectSquares: (category: string) => string;
  imageUnavailable: string;
  checking: string;
  verifyContinue: string;
  privacyCopy: string;
  privacy: string;
  help: string;
  security: string;
}

export const ENGLISH_IMAGE_GRID_COPY: ImageGridCopy = {
  protectedSession: "Protected session",
  securityCheck: "SECURITY CHECK",
  verifyHuman: "Verify you're human",
  selectSquares: (category) => `Select every square with a ${category}, then continue.`,
  imageUnavailable: "Verification image unavailable.",
  checking: "Checking…",
  verifyContinue: "Verify & Continue",
  privacyCopy: "The selected squares are checked only for this local browser session.",
  privacy: "Privacy",
  help: "Help",
  security: "Security",
};

export function imageGridCopy(): ImageGridCopy {
  return ENGLISH_IMAGE_GRID_COPY;
}
