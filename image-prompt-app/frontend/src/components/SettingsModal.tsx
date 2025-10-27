import React, { useEffect, useState } from 'react';
import axios from 'axios';

import { getOptions } from '../api/meta';
import { AUTOFILL_PREFERENCES_KEY } from '../constants/storage';
import type { MetaOptions } from '../types/meta';
import type { StoredAutofillPreferences } from '../types/preferences';

interface SettingsModalProps {
  onClose: () => void;
  onApiKeyUpdate: () => void;
}

const API_BASE = import.meta.env.VITE_API_BASE || '';

function loadPreferences(): StoredAutofillPreferences | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(AUTOFILL_PREFERENCES_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredAutofillPreferences;
  } catch (error) {
    console.warn('Failed to parse autofill preferences', error);
    return null;
  }
}

function mergePreferences(patch: Partial<StoredAutofillPreferences>): void {
  if (typeof window === 'undefined') return;
  let current: StoredAutofillPreferences = {};
  const raw = window.localStorage.getItem(AUTOFILL_PREFERENCES_KEY);
  if (raw) {
    try {
      current = JSON.parse(raw) as StoredAutofillPreferences;
    } catch (error) {
      console.warn('Failed to parse existing preferences', error);
    }
  }
  const next = { ...current, ...patch };
  window.localStorage.setItem(AUTOFILL_PREFERENCES_KEY, JSON.stringify(next));
}

const SettingsModal: React.FC<SettingsModalProps> = ({ onClose, onApiKeyUpdate }) => {
  const [apiKey, setApiKey] = useState('');
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState<'success' | 'error' | ''>('');
  const [imageModels, setImageModels] = useState<string[]>([]);
  const [selectedImageModel, setSelectedImageModel] = useState('');
  const [loadingOptions, setLoadingOptions] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const fetchOptions = async () => {
      setLoadingOptions(true);
      try {
        const data: MetaOptions = await getOptions();
        if (cancelled) return;
        setImageModels(data.image_models);
        const stored = loadPreferences();
        const preferred = stored?.imageModel && data.image_models.includes(stored.imageModel)
          ? stored.imageModel
          : data.image_models[0] ?? '';
        setSelectedImageModel(preferred);
        if (preferred) {
          mergePreferences({ imageModel: preferred });
        }
      } catch (error) {
        if (cancelled) return;
        console.error('Failed to load image models', error);
        const stored = loadPreferences();
        const fallback = stored?.imageModel ?? 'gpt-image-1';
        setImageModels([fallback]);
        setSelectedImageModel(fallback);
      } finally {
        if (!cancelled) {
          setLoadingOptions(false);
        }
      }
    };

    fetchOptions();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleSave = async () => {
    if (!apiKey.trim()) {
      setMessage('API key cannot be empty.');
      setStatus('error');
      return;
    }

    try {
      await axios.post(`${API_BASE}/api/settings/key`, { api_key: apiKey.trim() });
      setMessage('API Key saved successfully!');
      setStatus('success');
      onApiKeyUpdate();
    } catch (error) {
      console.error(error);
      setMessage('Failed to save API key.');
      setStatus('error');
    }
  };

  const handleImageModelChange = (value: string) => {
    setSelectedImageModel(value);
    mergePreferences({ imageModel: value });
  };

  const messageColor = status === 'success' ? '#3ad17d' : '#ff6b6b';

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2>Settings</h2>
        <div className="form-group">
          <label htmlFor="api-key">OpenAI API Key</label>
          <input
            id="api-key"
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-..."
          />
        </div>
        <div className="form-group">
          <label>Chat Model</label>
          <input type="text" value="gpt-4-turbo-preview" disabled />
        </div>
        <div className="form-group">
          <label htmlFor="image-model">Image Model</label>
          <select
            id="image-model"
            value={selectedImageModel}
            onChange={(event) => handleImageModelChange(event.target.value)}
            disabled={loadingOptions}
          >
            {imageModels.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
          <button onClick={onClose}>Cancel</button>
          <button onClick={handleSave}>Save</button>
        </div>
        {message && (
          <p style={{ color: messageColor, marginTop: '0.75rem' }}>{message}</p>
        )}
      </div>
    </div>
  );
};

export default SettingsModal;
