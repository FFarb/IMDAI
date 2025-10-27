import type { ResearchFlags } from './autofill';

export interface StoredAutofillPreferences {
  audience?: string;
  age?: string;
  flags?: ResearchFlags;
  researchModel?: string;
  imageModel?: string;
  customAudiences?: string[];
  customAges?: string[];
}
