import type { ImageWithPrompt } from './promptBuilder';

export interface ResearchFlags {
  use_web: boolean;
  avoid_brands: boolean;
  kids_safe: boolean;
}

export interface ResearchPayload {
  topic: string;
  audience: string;
  age: string;
  flags: ResearchFlags;
  images_n?: number;
}

export interface PaletteColor {
  hex: string;
  weight: number;
}

export interface SourceLink {
  title: string;
  url: string;
}

export interface DatasetTraits {
  palette: PaletteColor[];
  motifs: string[];
  line_weight: 'thin' | 'regular' | 'bold';
  outline: 'clean' | 'rough';
  typography: string[];
  composition: Array<'centered' | 'single character' | 'subtle lattice' | 'grid' | 'minimal frame'>;
  audience: string;
  age: string;
  mood: string[];
  negative: string[];
  seed_examples: string[];
  sources: SourceLink[] | null;
}

export interface AutofillResponse {
  traits: DatasetTraits;
  master_prompt_text: string;
  master_prompt_json: Record<string, unknown>;
}

export interface ResearchResult {
  data: AutofillResponse;
  warning: string | null;
}

export interface OneClickResponse {
  autofill: AutofillResponse;
  images: ImageWithPrompt[];
}

export interface OneClickResult {
  data: OneClickResponse;
  warning: string | null;
}
