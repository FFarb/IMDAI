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
  revised_prompt?: string | null;
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
