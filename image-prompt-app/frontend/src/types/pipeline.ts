// Simplified shared type definitions for the string-based pipeline flow.

export interface ResearchOutput {
  analysis: string;
  highlights: string[];
  segments: string[];
}

export interface SynthesisPrompt {
  positive: string;
  negative: string[];
  notes?: string | null;
}

export interface SynthesisOutput {
  prompts: SynthesisPrompt[];
  raw_text: string;
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
  variants?: number;
  images_per_prompt?: number;
  mode?: 'full' | 'prompts-only';

  // Research parameters
  research_model?: string;
  research_mode?: string;
  reasoning_effort?: string;

  // Synthesis parameters
  synthesis_mode?: string;

  // Image parameters
  image_model?: string;
  image_quality?: string;
  image_size?: string;
}

export type BriefValues = GenerateRequest;

export interface GenerateResponse {
  research: ResearchOutput;
  synthesis: SynthesisOutput;
  images: ImageResult[][];
}
