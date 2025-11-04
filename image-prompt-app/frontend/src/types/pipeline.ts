// ----- Common Sub-types --------------------------------------------------------

export type RefItem = {
  url: string;
  title: string;
  type: 'gallery' | 'article' | 'store' | 'blog' | 'community' | 'other';
  summary?: string;
};

export type PaletteItem = {
  hex: string;
  weight: number;
};

export type DesignIdea = {
  motifs: string[];
  composition: string[];
  line: 'ultra-thin' | 'thin' | 'regular' | 'bold';
  outline: 'none' | 'clean' | 'heavy' | 'rough';
  typography: string[];
  palette: PaletteItem[];
  mood: string[];
  hooks: string[];
  notes: string[];
};

// ----- New Distribution Types ------------------------------------------------

export type ColorDistribution = {
  area: 'background' | 'foreground' | 'focal' | 'accent' | 'text' | 'other';
  hex: string;
  weight: number;
};

export type LightZone = {
  area: string;
  intensity: number;
  notes?: string;
};

export type LightDistribution = {
  direction: string;
  key?: number;
  fill?: number;
  rim?: number;
  ambient?: number;
  zones?: LightZone[];
  notes?: string;
};

export type GradientStop = {
  hex: string;
  pos: number;
  weight?: number;
};

export type GradientDef = {
  allow: boolean;
  type: 'linear' | 'radial' | 'conic';
  angle?: number;
  center?: { x: number; y: number };
  stops: GradientStop[];
  areas: string[];
  vector_approximation_steps?: number;
};

export type GradientDistribution = GradientDef[];


// ----- Main Pipeline Step Schemas --------------------------------------------

export type ResearchOutput = {
  references: RefItem[];
  designs: DesignIdea[];
  palette?: PaletteItem[];
  notes?: string;
  color_distribution: ColorDistribution[];
  light_distribution: LightDistribution;
  gradient_distribution: GradientDistribution;
};

export type SynthesisPrompt = {
  title?: string;
  positive: string;
  negative: string[];
  notes?: string;
  palette_distribution: { hex: string; weight: number }[];
  light_distribution: LightDistribution;
  gradient_distribution: GradientDistribution;
  constraints?: {
    transparent_background?: boolean;
    vector_safe?: boolean;
    gradient_mode?: 'stepped-bands' | 'true-gradients';
  };
};

export type SynthesisOutput = {
  prompts: SynthesisPrompt[];
};
