import React, { useState } from 'react';
import axios from 'axios';

interface SettingsModalProps {
  onClose: () => void;
  onApiKeyUpdate?: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ onClose, onApiKeyUpdate }) => {
  const [apiKey, setApiKey] = useState('');
  const [message, setMessage] = useState('');

  const handleSave = async () => {
    try {
      await axios.post('/api/settings/key', { api_key: apiKey });
      setMessage('API Key saved successfully!');
      onApiKeyUpdate?.();
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
