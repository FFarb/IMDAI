export type ReferenceType =
  | 'gallery'
  | 'article'
  | 'store'
  | 'blog'
  | 'community'
  | 'other';

export type RefItem = {
  url: string;
  title: string;
  type: ReferenceType;
  summary?: string;
};

export type PaletteItem = {
  hex: string;
  weight: number;
};

export type ResearchOutput = {
  references: RefItem[];
  motifs: string[];
  composition: string[];
  line: 'ultra-thin' | 'thin' | 'regular' | 'bold';
  outline: 'none' | 'clean' | 'heavy' | 'rough';
  typography: string[];
  palette: PaletteItem[];
  mood?: string[];
  hooks?: string[];
  notes?: string;
};

export type SynthPrompt = {
  title?: string;
  positive: string;
  negative: string[];
  notes?: string;
};

export type SynthesisOutput = {
  prompts: SynthPrompt[];
};

export type ImageResult = { url?: string; b64_json?: string };

export type GenerateResponse = {
  research: ResearchOutput | null;
  synthesis: SynthesisOutput | null;
  images: ImageResult[][] | null;
};

export type GenerateMode = 'full' | 'research_only' | 'synthesis_only' | 'images_only';

export type GenerateRequest = {
  topic: string;
  audience: string;
  age: string;
  depth: number;
  variants: number;
  images_per_prompt: number;
  mode: GenerateMode;
  selected_prompt_index?: number | null;
  research?: ResearchOutput;
  synthesis?: SynthesisOutput;
};
