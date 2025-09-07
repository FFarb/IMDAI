import React, { useState } from 'react';

interface PromptDTO {
  positive: string;
  negative: string;
  params: Record<string, any>;
}

interface GalleryItemProps {
  imagePath: string;
  prompt: PromptDTO | null;
  apiBaseUrl: string;
}

const GalleryItem: React.FC<GalleryItemProps> = ({ imagePath, prompt, apiBaseUrl }) => {
  const [showPrompt, setShowPrompt] = useState(false);

  const handleDownload = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}${imagePath}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      // Extract filename from path
      const filename = imagePath.split('/').pop();
      a.download = filename || 'generated-image.png';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to download image:', error);
    }
  };

  return (
    <div className="gallery-item">
      <img src={`${apiBaseUrl}${imagePath}`} alt="Generated art" loading="lazy" />
      <div className="button-group">
        <button className="gallery-item-btn" onClick={() => setShowPrompt(!showPrompt)}>
          {showPrompt ? 'Hide' : 'Prompt'}
        </button>
        <button className="gallery-item-btn" onClick={handleDownload}>
          Download
        </button>
      </div>
      {showPrompt && prompt && (
        <div className="prompt-overlay">
          <h5>Positive</h5>
          <p>{prompt.positive}</p>
          <h5>Negative</h5>
          <p>{prompt.negative}</p>
        </div>
      )}
    </div>
  );
};

export default GalleryItem;
