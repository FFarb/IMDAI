import React, { useState } from 'react';
import axios from 'axios';

interface SettingsModalProps {
  onClose: () => void;
  onApiKeyUpdate: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ onClose, onApiKeyUpdate }) => {
  const [apiKey, setApiKey] = useState('');
  const [etsyApiKey, setEtsyApiKey] = useState('');
  const [message, setMessage] = useState('');

  const handleSave = async () => {
    try {
      const requests: Promise<unknown>[] = [];

      if (apiKey.trim()) {
        requests.push(axios.post('/api/settings/key', { api_key: apiKey.trim() }));
      }

      if (etsyApiKey.trim()) {
        requests.push(axios.post('/api/settings/etsy_key', { api_key: etsyApiKey.trim() }));
      }

      if (requests.length === 0) {
        setMessage('Enter a key before saving.');
        return;
      }

      await Promise.all(requests);
      setMessage('Settings saved successfully!');
      onApiKeyUpdate();
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (error) {
      setMessage('Failed to save API key.');
      console.error(error);
    }
  };

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
          <label htmlFor="etsy-api-key">Etsy API Key</label>
          <input
            id="etsy-api-key"
            type="password"
            value={etsyApiKey}
            onChange={(e) => setEtsyApiKey(e.target.value)}
            placeholder="etsy-..."
          />
        </div>
        {/* Placeholder for model names */}
        <div className="form-group">
          <label>Chat Model</label>
          <input type="text" value="gpt-4-turbo-preview" disabled />
        </div>
        <div className="form-group">
          <label>Image Model</label>
          <input type="text" value="gpt-image-1 (via dall-e-3)" disabled />
        </div>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
          <button onClick={onClose}>Cancel</button>
          <button onClick={handleSave}>Save</button>
        </div>
        {message && <p>{message}</p>}
      </div>
    </div>
  );
};

export default SettingsModal;
