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
