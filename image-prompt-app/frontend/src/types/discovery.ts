export type DiscoveryStatus = 'idle' | 'fetching' | 'ready' | 'error';

export type ReferenceStatus = 'result' | 'selected' | 'hidden' | 'deleted';

export interface DiscoverStats {
  found: number;
  unique: number;
  selected: number;
  dup_rate: number;
}

export interface DiscoverSession {
  id: string;
  query: string;
  adapters: string[];
  created_at: string;
  status: DiscoveryStatus;
  stats: DiscoverStats;
}

export interface ReferenceFlags {
  watermark: boolean;
  nsfw: boolean;
  brand_risk: boolean;
  busy_bg: boolean;
}

export interface ReferenceScores {
  quality: number;
  risk: number;
  outline: number;
  flatness: number;
}

export interface Reference {
  id: string;
  session_id: string;
  site: 'openverse' | 'unsplash' | 'generic' | 'local';
  url: string;
  thumb_url: string;
  title?: string | null;
  license?: string | null;
  author?: string | null;
  width?: number | null;
  height?: number | null;
  p_hash?: string | null;
  flags: ReferenceFlags;
  scores: ReferenceScores;
  status: ReferenceStatus;
  weight: number;
}

export interface ReferenceListResponse {
  items: Reference[];
  total: number;
}

export interface DiscoveryFilters {
  dedup: boolean;
  minQuality: number;
  hideWatermarks: boolean;
  kidsSafe: boolean;
  hideBusy: boolean;
}

export interface DiscoverySearchPayload {
  query: string;
  adapters?: string[];
  limit?: number;
}

export interface PaletteColor {
  hex: string;
  weight: number;
}

export type TypographyStyle = 'rounded' | 'block' | 'script' | 'outline' | 'mixed';

export interface TypographyFeature {
  present: boolean;
  style?: TypographyStyle | null;
}

export interface CompositionFeature {
  centered: boolean;
  symmetry: number;
  grid: boolean;
}

export interface FeatureDescriptor {
  reference_id: string;
  palette: PaletteColor[];
  line_weight: number;
  outline_clarity: number;
  fill_ratio: number;
  typography: TypographyFeature;
  motifs: string[];
  composition: CompositionFeature;
  brand_risk: number;
}

export type LineWeightLabel = 'thin' | 'regular' | 'bold';
export type OutlineLabel = 'clean' | 'rough';

export interface DatasetTraits {
  session_id: string;
  palette: PaletteColor[];
  motifs: string[];
  line_weight: LineWeightLabel;
  outline: OutlineLabel;
  typography: string[];
  composition: string[];
  audience_modes: string[];
}

export interface AnalyzeResponse {
  started: boolean;
  total: number;
}

export interface MasterPromptPayload {
  prompt_text: string;
  prompt_json: Record<string, unknown>;
}

export interface TraitWeights {
  palette: number;
  motifs: number;
  line: number;
  type: number;
  comp: number;
}
