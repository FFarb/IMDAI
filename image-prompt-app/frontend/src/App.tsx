import { useState, useEffect } from 'react';
import axios from 'axios';
import SettingsModal from './components/SettingsModal';

// --- Data Types ---
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

const API_BASE_URL = 'http://localhost:8000'; // For direct image URLs

function App() {
  const [slots, setSlots] = useState<Slots>({
    subject: '', style: '', composition: '', lighting: '',
    mood: '', details: '', quality: 'best quality, 4k'
  });
  const [assembledPrompt, setAssembledPrompt] = useState<PromptDTO | null>(null);
  const [galleryImages, setGalleryImages] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [presets, setPresets] = useState<Record<string, Slots>>({});
  const [showSettings, setShowSettings] = useState(false);
  const [apiKeyIsSet, setApiKeyIsSet] = useState(false); // Assume not set initially

  // --- Effects ---
  useEffect(() => {
    fetchGalleryImages();
    fetchPresets();
  }, []);

  // --- API Functions ---
  const fetchGalleryImages = async () => {
    try {
      const response = await axios.get<string[]>('/api/images');
      setGalleryImages(response.data);
    } catch (err) {
      console.error('Failed to fetch images', err);
    }
  };

  const fetchPresets = async () => {
    try {
      const response = await fetch('/presets.json');
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
      setAssembledPrompt(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to assemble prompt.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!assembledPrompt) return;
    setIsLoading(true);
    setError(null);
    try {
      await axios.post('/api/image', { prompt: assembledPrompt });
      fetchGalleryImages(); // Refresh gallery after generation
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate image.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // --- Event Handlers ---
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setSlots(prev => ({ ...prev, [name]: value }));
  };

  const loadPreset = (presetName: string) => {
    if (presets[presetName]) {
      setSlots(presets[presetName]);
    }
  };

  return (
    <div className="app-container">
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} onApiKeyUpdate={() => setApiKeyIsSet(true)} />}

      <aside className="controls">
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <h1>Prompt Engineer</h1>
          <button onClick={() => setShowSettings(true)}>⚙️</button>
        </div>

        <div className="form-group">
          <label>Load Preset</label>
          <select onChange={(e) => loadPreset(e.target.value)} defaultValue="">
            <option value="" disabled>-- Select a Preset --</option>
            {Object.keys(presets).map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
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

        <button onClick={handleAssemble} disabled={isLoading}>
          {isLoading ? 'Assembling...' : 'Assemble Prompt'}
        </button>

        <hr />

        <h3>Assembled Prompt</h3>
        <div className="prompt-display">
          {assembledPrompt ? JSON.stringify(assembledPrompt, null, 2) : 'Click "Assemble" to generate a prompt.'}
        </div>

        <button onClick={handleGenerate} disabled={!assembledPrompt || isLoading}>
          {isLoading ? 'Generating...' : 'Generate Image'}
        </button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </aside>

      <main className="gallery">
        <h2>Gallery</h2>
        <div className="gallery-grid">
          {galleryImages.map((imgPath) => (
            <img key={imgPath} src={`${API_BASE_URL}${imgPath}`} alt="Generated art" />
          ))}
        </div>
      </main>
    </div>
  );
}

export default App;
