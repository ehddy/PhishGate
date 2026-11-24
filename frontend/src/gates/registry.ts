import type { GateTemplateDefinition } from "./types";
import { completeChallengeGate } from "./challenge/handler";
import AreaSelectGate from "./challenge/templates/area-select/AreaSelectGate.vue";
import CustomDigitGate from "./challenge/templates/custom-digit/CustomDigitGate.vue";
import ImageGridGate from "./challenge/templates/image-grid/ImageGridGate.vue";
import MathChallengeGate from "./challenge/templates/math-challenge/MathChallengeGate.vue";
import RotateUprightGate from "./challenge/templates/rotate-upright/RotateUprightGate.vue";
import TextCaptchaGate from "./challenge/templates/text-captcha/TextCaptchaGate.vue";
import { completeClickGate } from "./click/handler";
import AlertGate from "./click/templates/alert/AlertGate.vue";
import BlurredPreviewGate from "./click/templates/blurred-preview/BlurredPreviewGate.vue";
import CloudflareCheckboxGate from "./click/templates/cloudflare-checkbox/CloudflareCheckboxGate.vue";
import CookieConsentGate from "./click/templates/cookie-consent/CookieConsentGate.vue";
import DocumentReadyGate from "./click/templates/document-ready/DocumentReadyGate.vue";
import NotificationConfirmGate from "./click/templates/notification-confirm/NotificationConfirmGate.vue";
import SecurityCheckGate from "./click/templates/security-check/SecurityCheckGate.vue";
import { completeInteractionGate } from "./interaction/handler";
import BelowFoldRevealGate from "./interaction/templates/below-fold-reveal/BelowFoldRevealGate.vue";
import MovementVerifyGate from "./interaction/templates/movement-verify/MovementVerifyGate.vue";
import PressAndHoldGate from "./interaction/templates/press-and-hold/PressAndHoldGate.vue";
import SlideToVerifyGate from "./interaction/templates/slide-to-verify/SlideToVerifyGate.vue";
import TermsScrollGate from "./interaction/templates/terms-scroll/TermsScrollGate.vue";


export const templateRegistry: Record<string, GateTemplateDefinition> = {
  "custom-digit": {
    templateId: "custom-digit",
    gateType: "challenge",
    component: CustomDigitGate,
    complete: completeChallengeGate,
  },
  "math-challenge": {
    templateId: "math-challenge",
    gateType: "challenge",
    component: MathChallengeGate,
    complete: completeChallengeGate,
  },
  "image-grid": {
    templateId: "image-grid",
    gateType: "challenge",
    component: ImageGridGate,
    complete: completeChallengeGate,
  },
  "text-captcha": {
    templateId: "text-captcha",
    gateType: "challenge",
    component: TextCaptchaGate,
    complete: completeChallengeGate,
  },
  "area-select": {
    templateId: "area-select",
    gateType: "challenge",
    component: AreaSelectGate,
    complete: completeChallengeGate,
  },
  "rotate-upright": {
    templateId: "rotate-upright",
    gateType: "challenge",
    component: RotateUprightGate,
    complete: completeChallengeGate,
  },
  alert: {
    templateId: "alert",
    gateType: "click",
    component: AlertGate,
    complete: completeClickGate,
  },
  "cloudflare-checkbox": {
    templateId: "cloudflare-checkbox",
    gateType: "click",
    component: CloudflareCheckboxGate,
    complete: completeClickGate,
  },
  "cookie-consent": {
    templateId: "cookie-consent",
    gateType: "click",
    component: CookieConsentGate,
    complete: completeClickGate,
  },
  "document-ready": {
    templateId: "document-ready",
    gateType: "click",
    component: DocumentReadyGate,
    complete: completeClickGate,
  },
  "notification-confirm": {
    templateId: "notification-confirm",
    gateType: "click",
    component: NotificationConfirmGate,
    complete: completeClickGate,
  },
  "security-check": {
    templateId: "security-check",
    gateType: "click",
    component: SecurityCheckGate,
    complete: completeClickGate,
  },
  "blurred-preview": {
    templateId: "blurred-preview",
    gateType: "click",
    component: BlurredPreviewGate,
    complete: completeClickGate,
  },
  "movement-verify": {
    templateId: "movement-verify",
    gateType: "interaction",
    component: MovementVerifyGate,
    complete: completeInteractionGate,
  },
  "press-and-hold": {
    templateId: "press-and-hold",
    gateType: "interaction",
    component: PressAndHoldGate,
    complete: completeInteractionGate,
  },
  "slide-to-verify": {
    templateId: "slide-to-verify",
    gateType: "interaction",
    component: SlideToVerifyGate,
    complete: completeInteractionGate,
  },
  "terms-scroll": {
    templateId: "terms-scroll",
    gateType: "interaction",
    component: TermsScrollGate,
    complete: completeInteractionGate,
  },
  "below-fold-reveal": {
    templateId: "below-fold-reveal",
    gateType: "interaction",
    component: BelowFoldRevealGate,
    complete: completeInteractionGate,
  },
};
