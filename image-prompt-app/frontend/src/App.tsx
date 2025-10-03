import { useState, useEffect, useMemo, useCallback } from 'react';
import type { ChangeEvent } from 'react';
import axios from 'axios';
import SettingsModal from './components/SettingsModal';
import ColorPicker from './components/ColorPicker';
import GalleryItem from './components/GalleryItem';
import ProcessingSidebar from './components/ProcessingSidebar';
import ReferenceSearchBar from './components/reference/ReferenceSearchBar';
import ReferenceResultsGrid from './components/reference/ReferenceResultsGrid';
import ReferenceSelectedList from './components/reference/ReferenceSelectedList';
import ReferenceStatusBar from './components/reference/ReferenceStatusBar';
import type {
  DiscoveryFilters,
  DiscoverStats,
  Reference,
} from './types/discovery';
import {
  searchDiscovery,
  fetchReferences as fetchDiscoveryReferences,
  fetchStats as fetchDiscoveryStats,
  selectReference,
  hideReference as hideDiscoveryReference,
  deleteReference as deleteDiscoveryReference,
  starReference as starDiscoveryReference,
  uploadLocalReferences,
  persistSessionId,
  loadPersistedSessionId,
} from './api/discover';

// --- Discovery constants ---
const DISCOVERY_PAGE_SIZE = 24;
const DISCOVERY_RPS = Number(import.meta.env.VITE_DISCOVERY_RPS ?? 3);
const DEFAULT_FILTERS: DiscoveryFilters = {
  dedup: true,
  minQuality: 0.5,
  hideWatermarks: true,
  kidsSafe: true,
  hideBusy: true,
};

// --- Prompt builder types ---
interface Slots {
  subject: string;
  style: string;
  composition: string;
  lighting: string;
  mood: string;
  details: string;
  quality: string;
}

interface PromptDTO {
  positive: string;
  negative: string;
  params: Record<string, any>;
}

interface ImageWithPrompt {
  image_path: string;
  prompt: PromptDTO | null;
}

// --- API Parameter Types ---
type ApiQuality = 'standard' | 'hd';
type ApiSize = '1024x1024' | '1024x1792' | '1792x1024';
type ApiStyle = 'vivid' | 'natural';

function App() {
  // --- Prompt builder state ---
  const [slots, setSlots] = useState<Slots>({
    subject: '',
    style: '',
    composition: '',
    lighting: '',
    mood: '',
    details: '',
    quality: 'masterpiece, high detail, 8k',
  });
  const [assembledPrompt, setAssembledPrompt] = useState<PromptDTO | null>(null);
  const [galleryImages, setGalleryImages] = useState<ImageWithPrompt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [presets, setPresets] = useState<Record<string, Slots>>({});
  const [showSettings, setShowSettings] = useState(false);
  const [newPresetName, setNewPresetName] = useState('');
  const [numImages, setNumImages] = useState(1);
  const [apiQuality, setApiQuality] = useState<ApiQuality>('hd');
  const [apiSize, setApiSize] = useState<ApiSize>('1024x1024');
  const [apiStyle, setApiStyle] = useState<ApiStyle>('vivid');

  // --- Discovery state ---
  const [discoverySessionId, setDiscoverySessionId] = useState<string | null>(null);
  const [discoveryQuery, setDiscoveryQuery] = useState('');
  const [selectedAdapters, setSelectedAdapters] = useState<string[]>(['openverse', 'unsplash', 'generic']);
  const [discoveryFilters, setDiscoveryFilters] = useState<DiscoveryFilters>(DEFAULT_FILTERS);
  const [discoveryStats, setDiscoveryStats] = useState<DiscoverStats | null>(null);
  const [resultReferences, setResultReferences] = useState<Reference[]>([]);
  const [selectedReferences, setSelectedReferences] = useState<Reference[]>([]);
  const [resultsOffset, setResultsOffset] = useState(0);
  const [hasMoreResults, setHasMoreResults] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const [discoveryError, setDiscoveryError] = useState<string | null>(null);
  const [resultsFocusedId, setResultsFocusedId] = useState<string | null>(null);
  const [selectedFocusedId, setSelectedFocusedId] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [lastStatsUpdated, setLastStatsUpdated] = useState<Date | null>(null);

  // --- Effects ---
  useEffect(() => {
    fetchGalleryImages();
    fetchPresets();
    const persistedSession = loadPersistedSessionId();
    if (persistedSession) {
      setDiscoverySessionId(persistedSession);
    }
  }, []);

  useEffect(() => {
    if (!discoverySessionId) {
      setResultReferences([]);
      setSelectedReferences([]);
      setDiscoveryStats(null);
      setResultsOffset(0);
      setHasMoreResults(false);
      persistSessionId(null);
      return;
    }

    const initializeSession = async () => {
      try {
        setIsLoadingResults(true);
        const [results, selected, stats] = await Promise.all([
          fetchDiscoveryReferences(discoverySessionId, { status: 'result', offset: 0, limit: DISCOVERY_PAGE_SIZE }),
          fetchDiscoveryReferences(discoverySessionId, { status: 'selected', offset: 0, limit: 200 }),
          fetchDiscoveryStats(discoverySessionId),
        ]);
        setResultReferences(results.items);
        setResultsOffset(results.items.length);
        setHasMoreResults(results.items.length < results.total);
        setSelectedReferences(selected.items);
        setDiscoveryStats(stats);
        setLastStatsUpdated(new Date());
        persistSessionId(discoverySessionId);
      } catch (err: any) {
        setDiscoveryError(err.message ?? 'Failed to load discovery session');
      } finally {
        setIsLoadingResults(false);
      }
    };

    initializeSession();
  }, [discoverySessionId]);

  useEffect(() => {
    if (!toastMessage) return;
    const id = window.setTimeout(() => setToastMessage(null), 3000);
    return () => window.clearTimeout(id);
  }, [toastMessage]);

  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Enter' && document.activeElement instanceof HTMLElement) {
        const tag = document.activeElement.tagName.toLowerCase();
        if (tag !== 'input' && tag !== 'textarea') {
          event.preventDefault();
          if (!isDiscovering) handleDiscoverySearch();
        }
      }
      if (!discoverySessionId) return;
      if (event.key.toLowerCase() === 'a' && resultsFocusedId) {
        const reference = resultReferences.find((item) => item.id === resultsFocusedId);
        if (reference) {
          event.preventDefault();
          handleSelectReference(reference);
        }
      }
      if (event.key.toLowerCase() === 'h' && resultsFocusedId) {
        const reference = resultReferences.find((item) => item.id === resultsFocusedId);
        if (reference) {
          event.preventDefault();
          handleHideReference(reference);
        }
      }
      if (event.key === '*' && resultsFocusedId) {
        const reference = resultReferences.find((item) => item.id === resultsFocusedId);
        if (reference) {
          event.preventDefault();
          handleStarReference(reference);
        }
      }
      if (event.key.toLowerCase() === 'd' && selectedFocusedId) {
        const reference = selectedReferences.find((item) => item.id === selectedFocusedId);
        if (reference) {
          event.preventDefault();
          handleDeleteReference(reference);
        }
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [discoverySessionId, isDiscovering, resultsFocusedId, selectedFocusedId, resultReferences, selectedReferences]);

  // --- Prompt builder API functions ---
  const fetchGalleryImages = async () => {
    try {
      const response = await axios.get<ImageWithPrompt[]>('/api/images');
      setGalleryImages(response.data);
    } catch (err) {
      console.error('Failed to fetch images', err);
    }
  };

  const fetchPresets = async () => {
    try {
      const response = await fetch(`/presets.json?t=${new Date().getTime()}`);
      if (!response.ok) throw new Error('Network response was not ok');
      const data = await response.json();
      setPresets(data);
    } catch (err) {
      console.error('Failed to load presets', err);
    }
  };

  const handleAssemble = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.post<PromptDTO>('/api/assemble', slots);
      const promptData = response.data;
      promptData.params.quality = apiQuality;
      promptData.params.size = apiSize;
      promptData.params.style = apiStyle;
      setAssembledPrompt(promptData);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to assemble prompt.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!assembledPrompt) return;
    setIsLoading(true);
    setError(null);
    try {
      await axios.post('/api/image', { prompt: assembledPrompt, n: numImages });
      fetchGalleryImages();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate image.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSavePreset = async () => {
    if (!newPresetName.trim()) {
      setError('Please enter a name for the preset.');
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      await axios.post('/api/presets', { name: newPresetName, slots });
      setNewPresetName('');
      await fetchPresets();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save preset.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setSlots((prev) => ({ ...prev, [name]: value }));
  };

  const loadPreset = (presetName: string) => {
    if (presets[presetName]) {
      setSlots(presets[presetName]);
    }
  };

  // --- Discovery helpers ---
  const filteredResults = useMemo(() => {
    return resultReferences.filter((reference) => {
      if (discoveryFilters.hideWatermarks && reference.flags.watermark) return false;
      if (discoveryFilters.kidsSafe && reference.flags.nsfw) return false;
      if (discoveryFilters.hideBusy && reference.flags.busy_bg) return false;
      if (reference.scores.quality < discoveryFilters.minQuality) return false;
      return true;
    });
  }, [resultReferences, discoveryFilters]);

  const refreshStats = useCallback(async () => {
    if (!discoverySessionId) return;
    try {
      setDiscoveryError(null);
      const stats = await fetchDiscoveryStats(discoverySessionId);
      setDiscoveryStats(stats);
      setLastStatsUpdated(new Date());
    } catch (err: any) {
      setDiscoveryError(err.message ?? 'Failed to refresh stats');
    }
  }, [discoverySessionId]);

  const handleDiscoverySearch = useCallback(async () => {
    if (!discoveryQuery.trim()) return;
    setIsDiscovering(true);
    setDiscoveryError(null);
    try {
      const sessionId = await searchDiscovery({
        query: discoveryQuery.trim(),
        adapters: selectedAdapters,
        limit: DISCOVERY_PAGE_SIZE,
      });
      setDiscoverySessionId(sessionId);
      setResultReferences([]);
      setSelectedReferences([]);
      setResultsOffset(0);
      setHasMoreResults(false);
      persistSessionId(sessionId);
      setLastStatsUpdated(null);
    } catch (err: any) {
      setDiscoveryError(err.message ?? 'Discovery search failed');
    } finally {
      setIsDiscovering(false);
    }
  }, [discoveryQuery, selectedAdapters]);

  const loadMoreResults = async () => {
    if (!discoverySessionId) return;
    setIsLoadingResults(true);
    try {
      setDiscoveryError(null);
      const response = await fetchDiscoveryReferences(discoverySessionId, {
        status: 'result',
        offset: resultsOffset,
        limit: DISCOVERY_PAGE_SIZE,
      });
      setResultReferences((prev) => [...prev, ...response.items]);
      const nextOffset = resultsOffset + response.items.length;
      setResultsOffset(nextOffset);
      setHasMoreResults(nextOffset < response.total);
    } catch (err: any) {
      setDiscoveryError(err.message ?? 'Failed to load more references');
    } finally {
      setIsLoadingResults(false);
    }
  };

  const handleSelectReference = async (reference: Reference) => {
    if (!discoverySessionId) return;
    try {
      setDiscoveryError(null);
      await selectReference(discoverySessionId, reference.id);
      const updated = { ...reference, status: 'selected' as const };
      setResultReferences((prev) => prev.filter((item) => item.id !== reference.id));
      setSelectedReferences((prev) => [updated, ...prev]);
      setResultsFocusedId(null);
      setSelectedFocusedId(reference.id);
      await refreshStats();
    } catch (err: any) {
      setDiscoveryError(err.message ?? 'Failed to select reference');
    }
  };

  const handleHideReference = async (reference: Reference) => {
    if (!discoverySessionId) return;
    try {
      setDiscoveryError(null);
      await hideDiscoveryReference(discoverySessionId, reference.id);
      setResultReferences((prev) => prev.filter((item) => item.id !== reference.id));
      setSelectedReferences((prev) => prev.filter((item) => item.id !== reference.id));
      await refreshStats();
    } catch (err: any) {
      setDiscoveryError(err.message ?? 'Failed to hide reference');
    }
  };

  const handleDeleteReference = async (reference: Reference) => {
    if (!discoverySessionId) return;
    try {
      setDiscoveryError(null);
      await deleteDiscoveryReference(discoverySessionId, reference.id);
      setResultReferences((prev) => prev.filter((item) => item.id !== reference.id));
      setSelectedReferences((prev) => prev.filter((item) => item.id !== reference.id));
      await refreshStats();
    } catch (err: any) {
      setDiscoveryError(err.message ?? 'Failed to delete reference');
    }
  };

  const handleStarReference = async (reference: Reference) => {
    if (!discoverySessionId) return;
    try {
      setDiscoveryError(null);
      const nextWeight = await starDiscoveryReference(discoverySessionId, reference.id);
      setResultReferences((prev) =>
        prev.map((item) => (item.id === reference.id ? { ...item, weight: nextWeight } : item)),
      );
      setSelectedReferences((prev) =>
        prev.map((item) => (item.id === reference.id ? { ...item, weight: nextWeight } : item)),
      );
    } catch (err: any) {
      setDiscoveryError(err.message ?? 'Failed to star reference');
    }
  };

  const handleMoveReference = (reference: Reference, direction: 'up' | 'down') => {
    setSelectedReferences((prev) => {
      const index = prev.findIndex((item) => item.id === reference.id);
      if (index === -1) return prev;
      const next = [...prev];
      const swapWith = direction === 'up' ? index - 1 : index + 1;
      if (swapWith < 0 || swapWith >= next.length) return prev;
      [next[index], next[swapWith]] = [next[swapWith], next[index]];
      return next;
    });
  };

  const handleUploadLocal = async (files: FileList) => {
    if (!discoverySessionId) return;
    setIsDiscovering(true);
    try {
      setDiscoveryError(null);
      const count = await uploadLocalReferences(discoverySessionId, files);
      setToastMessage(`Uploaded ${count} local reference${count === 1 ? '' : 's'}`);
      const response = await fetchDiscoveryReferences(discoverySessionId, { status: 'result', offset: 0, limit: DISCOVERY_PAGE_SIZE });
      setResultReferences(response.items);
      setResultsOffset(response.items.length);
      setHasMoreResults(response.items.length < response.total);
      await refreshStats();
    } catch (err: any) {
      setDiscoveryError(err.message ?? 'Failed to upload local references');
    } finally {
      setIsDiscovering(false);
    }
  };

  const handleInfoReference = (reference: Reference) => {
    window.open(reference.url, '_blank', 'noopener');
  };

  const handleCopyPalette = async (reference: Reference) => {
    try {
      await navigator.clipboard.writeText(reference.url);
      setToastMessage('Reference link copied to clipboard');
    } catch (err) {
      setToastMessage('Clipboard copy failed');
    }
  };

  const handleResetDiscovery = () => {
    setDiscoverySessionId(null);
    setResultReferences([]);
    setSelectedReferences([]);
    setDiscoveryStats(null);
    setDiscoveryError(null);
    persistSessionId(null);
  };

  // --- Derived values ---
  const selectedCount = selectedReferences.length;

  return (
    <div className="app-container">
      {showSettings && (
        <SettingsModal onClose={() => setShowSettings(false)} onApiKeyUpdate={() => {}} />
      )}

      <aside className="reference-column">
        <ReferenceSearchBar
          query={discoveryQuery}
          adapters={selectedAdapters}
          filters={discoveryFilters}
          loading={isDiscovering || isLoadingResults}
          error={discoveryError}
          onQueryChange={setDiscoveryQuery}
          onAdaptersChange={setSelectedAdapters}
          onFiltersChange={setDiscoveryFilters}
          onSearch={handleDiscoverySearch}
          onUploadLocal={discoverySessionId ? handleUploadLocal : undefined}
          onResetSession={discoverySessionId ? handleResetDiscovery : undefined}
        />
        <ReferenceStatusBar
          stats={discoveryStats}
          selectedCount={selectedCount}
          rps={DISCOVERY_RPS}
          lastUpdated={lastStatsUpdated}
        />
        <div className="reference-scroll">
          <ReferenceResultsGrid
            references={filteredResults}
            loading={isLoadingResults}
            hasMore={hasMoreResults}
            focusedId={resultsFocusedId}
            onAdd={handleSelectReference}
            onHide={handleHideReference}
            onStar={handleStarReference}
            onLoadMore={loadMoreResults}
            onFocusChange={setResultsFocusedId}
          />
          <h3 className="selected-heading">Selected references</h3>
          <ReferenceSelectedList
            references={selectedReferences}
            focusedId={selectedFocusedId}
            onFocusChange={setSelectedFocusedId}
            onHide={handleHideReference}
            onDelete={handleDeleteReference}
            onStar={handleStarReference}
            onMove={handleMoveReference}
            onInfo={handleInfoReference}
            onCopyPalette={handleCopyPalette}
          />
        </div>
      </aside>

      <aside className="controls">
        <div className="controls-header">
          <h1>Prompt Engineer</h1>
          <button onClick={() => setShowSettings(true)}>⚙️</button>
        </div>

        <div className="form-group">
          <label>Load Preset</label>
          <select onChange={(e) => loadPreset(e.target.value)} defaultValue="">
            <option value="" disabled>
              -- Select a Preset --
            </option>
            {Object.keys(presets).map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Save Current as Preset</label>
          <div className="preset-save">
            <input
              type="text"
              placeholder="New preset name..."
              value={newPresetName}
              onChange={(e) => setNewPresetName(e.target.value)}
            />
            <button onClick={handleSavePreset} disabled={isLoading}>
              Save
            </button>
          </div>
        </div>

        {Object.keys(slots).map((key) => (
          <div className="form-group" key={key}>
            <label htmlFor={key}>{key.charAt(0).toUpperCase() + key.slice(1)}</label>
            <input
              type="text"
              id={key}
              name={key}
              value={slots[key as keyof Slots]}
              onChange={handleInputChange}
            />
          </div>
        ))}

        <ColorPicker />

        <button onClick={handleAssemble} disabled={isLoading}>
          {isLoading ? 'Assembling...' : 'Assemble Prompt'}
        </button>

        <hr />

        <h3>Assembled Prompt</h3>
        <div className="prompt-display">
          {assembledPrompt ? JSON.stringify(assembledPrompt, null, 2) : 'Click "Assemble" to generate a prompt.'}
        </div>

        <div className="api-controls-grid">
          <div className="form-group">
            <label htmlFor="apiQuality">Quality</label>
            <select
              id="apiQuality"
              value={apiQuality}
              onChange={(e) => setApiQuality(e.target.value as ApiQuality)}
              disabled={isLoading}
            >
              <option value="hd">HD</option>
              <option value="standard">Standard</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="apiSize">Size</label>
            <select
              id="apiSize"
              value={apiSize}
              onChange={(e) => setApiSize(e.target.value as ApiSize)}
              disabled={isLoading}
            >
              <option value="1024x1024">1024x1024</option>
              <option value="1024x1792">1024x1792</option>
              <option value="1792x1024">1792x1024</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="apiStyle">Style</label>
            <select
              id="apiStyle"
              value={apiStyle}
              onChange={(e) => setApiStyle(e.target.value as ApiStyle)}
              disabled={isLoading}
            >
              <option value="vivid">Vivid</option>
              <option value="natural">Natural</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="numImages">Number of Images</label>
          <input
            type="number"
            id="numImages"
            min={1}
            max={4}
            value={numImages}
            onChange={(e) => setNumImages(Number(e.target.value))}
          />
        </div>

        <button onClick={handleGenerate} disabled={isLoading || !assembledPrompt}>
          {isLoading ? 'Generating...' : 'Generate Images'}
        </button>
        {error && <div className="error-text">{error}</div>}
      </aside>

      <main className="gallery">
        <h2>Gallery</h2>
        <div className="gallery-grid">
          {galleryImages.map((image) => (
            <GalleryItem key={image.image_path} image={image} />
          ))}
        </div>
      </main>

      <aside className="processing">
        <ProcessingSidebar />
      </aside>

      {toastMessage && <div className="toast">{toastMessage}</div>}
    </div>
  );
}

export default App;
