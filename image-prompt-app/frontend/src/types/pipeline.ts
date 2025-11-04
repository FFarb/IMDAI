// Shared type definitions for the three-stage pipeline frontend.

export type ReferenceType =
  | 'gallery'
  | 'article'
  | 'store'
  | 'blog'
  | 'community'
  | 'other';

export interface ResearchReference {
  url: string;
  title: string;
  type: ReferenceType;
  summary?: string;
}

export interface PaletteItem {
  hex: string;
  weight: number;
}

export interface DesignIdea {
  motifs: string[];
  composition: string[];
  line: string;
  outline: string;
  typography: string[];
  palette: PaletteItem[];
  mood: string[];
  hooks: string[];
  notes: string[];
}

export interface ColorDistributionItem {
  area: string;
  hex: string;
  weight: number;
}

export interface LightDistribution {
  direction: string;
  key: number;
  fill: number;
  rim: number;
  ambient: number;
  zones: string[];
  notes?: string;
}

export interface GradientStop {
  hex: string;
  pos: number;
}

export interface GradientDistributionItem {
  allow: boolean;
  type: 'linear' | 'radial' | 'conic';
  stops: GradientStop[];
  areas: string[];
  vector_approximation_steps: number;
}

export interface ResearchOutput {
  references: ResearchReference[];
  designs: DesignIdea[];
  color_distribution: ColorDistributionItem[];
  light_distribution: LightDistribution;
  gradient_distribution: GradientDistributionItem[];
  notes?: string;
}

export interface SynthesisPrompt {
  title?: string;
  positive: string;
  negative: string[];
  notes?: string;
  palette_distribution: PaletteItem[];
  light_distribution: LightDistribution;
  gradient_distribution: GradientDistributionItem[];
  constraints?: {
    transparent_background: boolean;
    vector_safe: boolean;
    gradient_mode: 'approximate' | 'true-gradients';
  };
}

export interface SynthesisOutput {
  prompts: SynthesisPrompt[];
  metadata?: Record<string, unknown>;
}

export interface ImageResult {
  url?: string | null;
  b64_json?: string | null;
  error?: string;
}

export interface GenerateRequest {
  topic: string;
  audience: string;
  age?: string | null;
  depth?: number;
  variants?: number;
  images_per_prompt?: number;
  mode?: 'full' | 'prompts-only';
}

export interface GenerateResponse {
  research: ResearchOutput;
  synthesis: SynthesisOutput;
  images: ImageResult[][];
}
