import { useCallback, useEffect, useState, type ChangeEvent } from 'react';
import axios from 'axios';

import SettingsModal from './components/SettingsModal';
import ColorPicker from './components/ColorPicker';
import GalleryItem from './components/GalleryItem';
import AutofillPanel from './components/right/AutofillPanel';
import type { ImageWithPrompt, PromptDTO } from './types/promptBuilder';

interface Slots {
  subject: string;
  style: string;
  composition: string;
  lighting: string;
  mood: string;
  details: string;
  quality: string;
}

type ApiQuality = 'low' | 'high';
type ApiSize = '1024x1024' | '1024x1792' | '1792x1024' | '1536x1024';

function App() {
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
  const [apiQuality, setApiQuality] = useState<ApiQuality>('low');
  const [apiSize, setApiSize] = useState<ApiSize>('1536x1024');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fetchGalleryImages = useCallback(async () => {
    try {
      const response = await axios.get<ImageWithPrompt[]>('/api/images');
      setGalleryImages(response.data);
    } catch (err) {
      console.error('Failed to fetch images', err);
    }
  }, []);

  const fetchPresets = useCallback(async () => {
    try {
      const response = await fetch(`/presets.json?t=${new Date().getTime()}`);
      if (!response.ok) throw new Error('Network response was not ok');
      const data = await response.json();
      setPresets(data);
    } catch (err) {
      console.error('Failed to load presets', err);
    }
  }, []);

  useEffect(() => {
    fetchGalleryImages();
    fetchPresets();
  }, [fetchGalleryImages, fetchPresets]);

  useEffect(() => {
    if (!toastMessage) return;
    const id = window.setTimeout(() => setToastMessage(null), 3000);
    return () => window.clearTimeout(id);
  }, [toastMessage]);

  const handleAssemble = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.post<PromptDTO>('/api/assemble', slots);
      const promptData = response.data;
      promptData.params = {
        ...promptData.params,
        size: apiSize,
        quality: apiQuality,
      };
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
      await fetchGalleryImages();
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

  return (
    <div className="app-container">
      <aside className="controls">
        <div className="controls-header">
          <h1>Prompt Engineer</h1>
          <button onClick={() => setShowSettings(true)}>⚙️</button>
        </div>

        <div className="form-group">
          <label>Load Preset</label>
          <select onChange={(event) => loadPreset(event.target.value)} defaultValue="">
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
              onChange={(event) => setNewPresetName(event.target.value)}
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
              onChange={(event) => setApiQuality(event.target.value as ApiQuality)}
              disabled={isLoading}
            >
              <option value="low">Low</option>
              <option value="high">High</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="apiSize">Size</label>
            <select
              id="apiSize"
              value={apiSize}
              onChange={(event) => setApiSize(event.target.value as ApiSize)}
              disabled={isLoading}
            >
              <option value="1536x1024">1536x1024</option>
              <option value="1024x1024">1024x1024</option>
              <option value="1024x1792">1024x1792</option>
              <option value="1792x1024">1792x1024</option>
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
            onChange={(event) => setNumImages(Number(event.target.value))}
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

      <aside className="processing traits-sidebar">
        <AutofillPanel onShowToast={setToastMessage} refreshGallery={fetchGalleryImages} />
      </aside>

      {toastMessage && <div className="toast">{toastMessage}</div>}

      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </div>
  );
}

export default App;
