import type { ResearchFlags } from './autofill';

export interface MetaOptions {
  audiences: string[];
  ages: string[];
  default_flags: ResearchFlags;
  research_models: string[];
  image_models: string[];
  defaults?: {
    research_provider: string;
    research_model: string;
    research_timeout_s: number;
  };
}
