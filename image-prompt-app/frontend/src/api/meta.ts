import type { MetaOptions } from '../types/meta';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export async function getOptions(): Promise<MetaOptions> {
  const response = await fetch(`${API_BASE}/api/meta/options`);
  if (!response.ok) {
    throw new Error('Failed to load options');
  }
  return response.json() as Promise<MetaOptions>;
}
