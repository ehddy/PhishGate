import type { Component } from "vue";

import type {
  CONTEXT_MODES,
  COPY_VARIANTS,
  LAYOUT_VARIANTS,
  THEME_VARIANTS,
} from "./variants";


export type GateType = "challenge" | "click" | "interaction";

export type ContextMode = (typeof CONTEXT_MODES)[number];
export type LayoutVariant = (typeof LAYOUT_VARIANTS)[number];
export type CopyVariant = (typeof COPY_VARIANTS)[number];
export type ThemeVariant = (typeof THEME_VARIANTS)[number];

export interface DigitImageChallenge {
  kind: "digit-image";
  image_data_url: string;
  variant: "blue" | "violet" | "mint";
}

export interface TextImageChallenge {
  kind: "text-image";
  image_data_url: string;
  variant: "blue" | "violet" | "mint";
}

export interface MathProblemChallenge {
  kind: "math-problem";
  prompt: string;
  operator: "addition" | "subtraction" | "multiplication";
  variant: "blue" | "violet" | "mint";
}

export interface ImageGridChallenge {
  kind: "image-grid";
  category_label: string;
  cells: string[];
  variant: "blue" | "violet" | "mint";
}

export interface AreaSelectChallenge {
  kind: "area-select";
  category_label: string;
  image_data_url: string;
  columns: number;
  rows: number;
  variant: "blue" | "violet" | "mint";
}

export interface RotationChallenge {
  kind: "rotation";
  image_data_url: string;
  step_count: number;
  variant: "blue" | "violet" | "mint";
}

export type GateChallenge =
  | DigitImageChallenge
  | TextImageChallenge
  | MathProblemChallenge
  | ImageGridChallenge
  | AreaSelectChallenge
  | RotationChallenge;

export interface GateSubmission {
  answer?: string;
}

export interface GateDisplayContext {
  brand: string | null;
  context_mode: ContextMode;
  layout_variant: LayoutVariant;
  copy_variant: CopyVariant;
  theme_variant: ThemeVariant;
  variant_id: string;
}

export interface GateConfig {
  gate_type: GateType;
  template_id: string;
  parameters: Record<string, unknown>;
  display_context: GateDisplayContext;
  challenge?: GateChallenge;
}

export interface GateTemplateDefinition {
  templateId: string;
  gateType: GateType;
  component: Component;
  complete: (token: string, submission?: GateSubmission) => Promise<string>;
}
