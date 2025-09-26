import { useState, useEffect } from 'react';
import axios from 'axios';
import SettingsModal from './components/SettingsModal';
import ColorPicker from './components/ColorPicker';
import GalleryItem from './components/GalleryItem';
import EtsySidebar, { EtsyListingFormValues } from './components/EtsySidebar';

// --- Data Types ---
interface Slots {
  subject: string;
  text: string;
  style: string;
  composition: string;
  lighting: string;
  mood: string;
  details: string;
  quality: string;
}

const DEFAULT_SLOTS: Slots = {
  subject: '',
  text: '',
  style: '',
  composition: '',
  lighting: '',
  mood: '',
  details: '',
  quality: 'masterpiece, high detail, 8k',
};

const SLOT_CATEGORIES: { title: string; fields: (keyof Slots)[] }[] = [
  { title: 'Text', fields: ['text'] },
  { title: 'Subject & Composition', fields: ['subject', 'composition'] },
  { title: 'Style & Mood', fields: ['style', 'lighting', 'mood'] },
  { title: 'Details & Quality', fields: ['details', 'quality'] },
];

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

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [slots, setSlots] = useState<Slots>({ ...DEFAULT_SLOTS });
  const [assembledPrompt, setAssembledPrompt] = useState<PromptDTO | null>(null);
  const [galleryImages, setGalleryImages] = useState<ImageWithPrompt[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [presets, setPresets] = useState<Record<string, Slots>>({});
  const [showSettings, setShowSettings] = useState(false);
  const [newPresetName, setNewPresetName] = useState('');
  const [imageToProcess, setImageToProcess] = useState<string | null>(null);

  // --- User-Controlled API Parameters ---
  const [numImages, setNumImages] = useState(1);
  const [apiQuality, setApiQuality] = useState<ApiQuality>('hd');
  const [apiSize, setApiSize] = useState<ApiSize>('1024x1024');
  const [apiStyle, setApiStyle] = useState<ApiStyle>('vivid');

  // --- Effects ---
  useEffect(() => {
    fetchGalleryImages();
    fetchPresets();
  }, []);

  // --- API Functions ---
  const fetchGalleryImages = async () => {
    try {
      const response = await axios.get<ImageWithPrompt[]>('/api/images');
      setGalleryImages(response.data);
    } catch (err) { console.error('Failed to fetch images', err); }
  };

  const fetchPresets = async () => {
    try {
      const response = await fetch(`/presets.json?t=${new Date().getTime()}`);
      if (!response.ok) throw new Error("Network response was not ok");
      const data: Record<string, Partial<Slots>> = await response.json();
      const normalized: Record<string, Slots> = Object.fromEntries(
        Object.entries(data).map(([name, slotValues]) => [name, { ...DEFAULT_SLOTS, ...slotValues }])
      );
      setPresets(normalized);
    } catch (err) { console.error('Failed to load presets', err); }
  };

  const handleAssemble = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.post<PromptDTO>('/api/assemble', slots);
      const promptData = response.data;

      // *** FINAL FIX: Manually override ALL API params to ensure validity ***
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
    if (!newPresetName.trim()) { setError("Please enter a name for the preset."); return; }
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

  // --- Event Handlers ---
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setSlots(prev => ({ ...prev, [name]: value }));
  };

  const loadPreset = (presetName: string) => {
    if (presets[presetName]) { setSlots({ ...DEFAULT_SLOTS, ...presets[presetName] }); }
  };

  const handleSelectImageForProcessing = (path: string) => {
    setImageToProcess(path);
  };

  const handleCreateEtsyListing = async (values: EtsyListingFormValues) => {
    if (!imageToProcess) {
      throw new Error('No image selected for Etsy listing.');
    }

    const payload = {
      image_path: imageToProcess,
      title: values.title,
      description: values.description,
      price: values.price,
      quantity: values.quantity,
      taxonomy_id: values.taxonomyId,
    };

    const response = await axios.post('/api/etsy/create_listing', payload);
    return response.data;
  };

  return (
    <div className="app-container">
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} onApiKeyUpdate={() => {}} />}

      <aside className="controls">
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <h1>Prompt Engineer</h1>
          <button onClick={() => setShowSettings(true)}>⚙️</button>
        </div>

        <div className="form-group">
          <label>Load Preset</label>
          <select onChange={(e) => loadPreset(e.target.value)} defaultValue="">
            <option value="" disabled>-- Select a Preset --</option>
            {Object.keys(presets).map(name => (<option key={name} value={name}>{name}</option>))}
          </select>
        </div>
        <div className="form-group">
            <label>Save Current as Preset</label>
            <div style={{display: 'flex'}}>
                <input type="text" placeholder="New preset name..." value={newPresetName} onChange={(e) => setNewPresetName(e.target.value)} style={{borderTopRightRadius: 0, borderBottomRightRadius: 0}} />
                <button onClick={handleSavePreset} disabled={isLoading} style={{borderTopLeftRadius: 0, borderBottomLeftRadius: 0}}>Save</button>
            </div>
        </div>

        {SLOT_CATEGORIES.map((category) => (
          <section key={category.title} className="slot-category">
            <h3>{category.title}</h3>
            {category.fields.map((key) => (
              <div className="form-group" key={key}>
                <label htmlFor={key}>{key.charAt(0).toUpperCase() + key.slice(1)}</label>
                <input
                  type="text"
                  id={key}
                  name={key}
                  value={slots[key]}
                  onChange={handleInputChange}
                />
              </div>
            ))}
          </section>
        ))}

        <ColorPicker />

        <button onClick={handleAssemble} disabled={isLoading}>{isLoading ? 'Assembling...' : 'Assemble Prompt'}</button>
        <hr />

        <h3>Assembled Prompt</h3>
        <div className="prompt-display">{assembledPrompt ? JSON.stringify(assembledPrompt, null, 2) : 'Click "Assemble" to generate a prompt.'}</div>

        {/* --- FINAL API CONTROLS --- */}
        <div className="api-controls-grid">
          <div className="form-group">
            <label htmlFor="apiQuality">Quality</label>
            <select id="apiQuality" value={apiQuality} onChange={(e) => setApiQuality(e.target.value as ApiQuality)} disabled={isLoading}>
              <option value="hd">HD</option>
              <option value="standard">Standard</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="apiSize">Size</label>
            <select id="apiSize" value={apiSize} onChange={(e) => setApiSize(e.target.value as ApiSize)} disabled={isLoading}>
              <option value="1024x1024">1024x1024</option>
              <option value="1024x1792">1024x1792</option>
              <option value="1792x1024">1792x1024</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="apiStyle">Style</label>
            <select id="apiStyle" value={apiStyle} onChange={(e) => setApiStyle(e.target.value as ApiStyle)} disabled={isLoading}>
              <option value="vivid">Vivid</option>
              <option value="natural">Natural</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="numImages">Amount</label>
            <select id="numImages" value={numImages} onChange={(e) => setNumImages(parseInt(e.target.value, 10))} disabled={!assembledPrompt || isLoading}>
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
              <option value={4}>4</option>
            </select>
          </div>
        </div>

        <button onClick={handleGenerate} disabled={!assembledPrompt || isLoading}>{isLoading ? `Generating ${numImages}...` : `Generate ${numImages} Image(s)`}</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </aside>

      <main className="gallery">
        <h2>Gallery</h2>
        <div className="gallery-grid">
          {galleryImages.map((item) => (
            <GalleryItem
              key={item.image_path}
              imagePath={item.image_path}
              prompt={item.prompt}
              apiBaseUrl={API_BASE_URL}
              onSelectForEtsy={handleSelectImageForProcessing}
            />
          ))}
        </div>
      </main>

      {/* --- Right-hand Etsy Sidebar --- */}
      <EtsySidebar
        imageToProcess={imageToProcess}
        apiBaseUrl={API_BASE_URL}
        onCreateListing={handleCreateEtsyListing}
        onClearSelection={() => setImageToProcess(null)}
      />
    </div>
  );
}

export default App;
