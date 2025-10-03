import { ChangeEvent, FormEvent } from 'react';
import type { DiscoveryFilters } from '../../types/discovery';

const ADAPTER_OPTIONS = [
  { label: 'Openverse', value: 'openverse' },
  { label: 'Unsplash', value: 'unsplash' },
  { label: 'Generic', value: 'generic' },
];

interface ReferenceSearchBarProps {
  query: string;
  adapters: string[];
  filters: DiscoveryFilters;
  loading: boolean;
  error?: string | null;
  onQueryChange: (value: string) => void;
  onAdaptersChange: (value: string[]) => void;
  onFiltersChange: (value: DiscoveryFilters) => void;
  onSearch: () => void;
  onUploadLocal?: (files: FileList) => void;
  onResetSession?: () => void;
}

export default function ReferenceSearchBar({
  query,
  adapters,
  filters,
  loading,
  error,
  onQueryChange,
  onAdaptersChange,
  onFiltersChange,
  onSearch,
  onUploadLocal,
  onResetSession,
}: ReferenceSearchBarProps) {
  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    onSearch();
  };

  const toggleAdapter = (adapter: string) => {
    if (adapters.includes(adapter)) {
      onAdaptersChange(adapters.filter((item) => item !== adapter));
    } else {
      onAdaptersChange([...adapters, adapter]);
    }
  };

  const handleFileUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0 && onUploadLocal) {
      onUploadLocal(files);
      event.target.value = '';
    }
  };

  return (
    <section className="reference-search">
      <form onSubmit={handleSubmit}>
        <label className="reference-label" htmlFor="reference-query">Reference search</label>
        <div className="reference-search-row">
          <input
            id="reference-query"
            type="text"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Describe the vibe (e.g. minimal safari nursery)"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !query.trim()}>
            {loading ? 'Searching…' : 'Discover'}
          </button>
        </div>
      </form>

      <div className="reference-adapters">
        {ADAPTER_OPTIONS.map((adapter) => (
          <label key={adapter.value} className="reference-chip">
            <input
              type="checkbox"
              checked={adapters.includes(adapter.value)}
              onChange={() => toggleAdapter(adapter.value)}
              disabled={loading}
            />
            <span>{adapter.label}</span>
          </label>
        ))}
      </div>

      <div className="reference-filters">
        <div className="reference-filter-row">
          <label className="reference-chip">
            <input
              type="checkbox"
              checked={filters.dedup}
              onChange={(event) => onFiltersChange({ ...filters, dedup: event.target.checked })}
            />
            <span>Dedup</span>
          </label>
          <label className="reference-chip">
            <input
              type="checkbox"
              checked={filters.hideWatermarks}
              onChange={(event) => onFiltersChange({ ...filters, hideWatermarks: event.target.checked })}
            />
            <span>No watermark</span>
          </label>
        </div>
        <div className="reference-filter-row">
          <label className="reference-chip">
            <input
              type="checkbox"
              checked={filters.kidsSafe}
              onChange={(event) => onFiltersChange({ ...filters, kidsSafe: event.target.checked })}
            />
            <span>Kids-safe</span>
          </label>
          <label className="reference-chip">
            <input
              type="checkbox"
              checked={filters.hideBusy}
              onChange={(event) => onFiltersChange({ ...filters, hideBusy: event.target.checked })}
            />
            <span>No busy BG</span>
          </label>
        </div>
        <div className="reference-slider">
          <label htmlFor="quality-slider">Quality ≥ {filters.minQuality.toFixed(1)}</label>
          <input
            id="quality-slider"
            type="range"
            min={0}
            max={1}
            step={0.1}
            value={filters.minQuality}
            onChange={(event) => onFiltersChange({ ...filters, minQuality: parseFloat(event.target.value) })}
          />
        </div>
      </div>

      <div className="reference-actions">
        <label className="reference-upload">
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={handleFileUpload}
            disabled={loading || !onUploadLocal}
          />
          <span>Upload local refs</span>
        </label>
        {onResetSession && (
          <button type="button" className="link-button" onClick={onResetSession} disabled={loading}>
            Reset session
          </button>
        )}
      </div>

      {error && <div className="reference-error">{error}</div>}
    </section>
  );
}
