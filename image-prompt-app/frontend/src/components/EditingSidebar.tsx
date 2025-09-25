import React, { useState, useEffect } from 'react';

/**
 * Props for the EditingSidebar component.
 * @param {string | null} imagePath - The path to the currently selected image. Null if none selected.
 * @param {() => void} onClose - Callback function to close the sidebar.
 * @param {boolean} isVisible - Controls the rendering of the component.
 */
interface EditingSidebarProps {
  imagePath: string | null;
  onClose: () => void;
  isVisible: boolean;
}

const EditingSidebar: React.FC<EditingSidebarProps> = ({ imagePath, onClose, isVisible }) => {
  // Internal state for the Etsy uploader form fields.
  const [etsyTitle, setEtsyTitle] = useState('');
  const [etsyDescription, setEtsyDescription] = useState('');
  const [etsyTags, setEtsyTags] = useState('');
  const [etsyPrice, setEtsyPrice] = useState('');

  // Effect to reset the form fields whenever a new image is selected.
  // This prevents carrying over data from a previously selected image.
  useEffect(() => {
    if (imagePath) {
      setEtsyTitle('');
      setEtsyDescription('');
      setEtsyTags('');
      setEtsyPrice('');
    }
  }, [imagePath]);

  // If the sidebar is not supposed to be visible, render nothing (null).
  if (!isVisible) {
    return null;
  }
  
  // --- Placeholder Handler Functions ---
  // These functions simulate the feature's behavior until backend logic is implemented.
  const handleUpscale = () => {
    console.log(`[SIDEBAR ACTION] Requesting 4x upscale for image: ${imagePath}`);
    alert(`Upscale requested for: ${imagePath}`);
  };

  const handleConvertToSvg = () => {
    console.log(`[SIDEBAR ACTION] Requesting SVG conversion for image: ${imagePath}`);
    alert(`SVG conversion requested for: ${imagePath}`);
  };

  const handleUploadToEtsy = () => {
    if (!etsyTitle.trim() || !etsyPrice.trim()) {
        alert('"Title" and "Price" are required fields for an Etsy listing.');
        return;
    }
    const etsyListingData = {
        imagePath,
        title: etsyTitle,
        description: etsyDescription,
        tags: etsyTags.split(',').map(tag => tag.trim()).filter(Boolean), // Cleans up tags
        price: parseFloat(etsyPrice),
    };
    console.log('[SIDEBAR ACTION] Uploading to Etsy with the following data:', etsyListingData);
    alert('Check the developer console for the Etsy upload data object.');
  };

  return (
    <aside className="editing-sidebar">
      <div className="sidebar-header">
        <h3>Editing Tools</h3>
        <button onClick={onClose} className="close-btn" aria-label="Close editing sidebar">&times;</button>
      </div>

      {/* Conditionally render content based on whether an image is selected */}
      {imagePath ? (
        <>
          <div className="selected-image-preview">
            <img src={`http://localhost:8000${imagePath}`} alt="Selected for editing" />
          </div>

          {/* Section 1: Image Processing Tools */}
          <div className="sidebar-section">
            <h4>Image Tools</h4>
            <div className="button-group-vertical">
              <button onClick={handleUpscale}>Upscale x4</button>
              <button onClick={handleConvertToSvg}>Convert to SVG for Print</button>
            </div>
          </div>

          {/* Section 2: Etsy Uploader Form */}
          <div className="sidebar-section">
            <h4>Etsy Uploader</h4>
            <div className="form-group">
              <label htmlFor="etsyTitle">Title</label>
              <input id="etsyTitle" type="text" value={etsyTitle} onChange={(e) => setEtsyTitle(e.target.value)} placeholder="e.g., 'Cyberpunk Mercenary'"/>
            </div>
            <div className="form-group">
              <label htmlFor="etsyDescription">Description</label>
              <textarea id="etsyDescription" value={etsyDescription} onChange={(e) => setEtsyDescription(e.target.value)} rows={4} placeholder="Detailed description of the artwork..."></textarea>
            </div>
            <div className="form-group">
              <label htmlFor="etsyTags">Tags (comma-separated)</label>
              <input id="etsyTags" type="text" value={etsyTags} onChange={(e) => setEtsyTags(e.target.value)} placeholder="cyberpunk, art, warrior..."/>
            </div>
            <div className="form-group">
              <label htmlFor="etsyPrice">Price ($)</label>
              <input id="etsyPrice" type="number" step="0.01" min="0" value={etsyPrice} onChange={(e) => setEtsyPrice(e.target.value)} placeholder="9.99"/>
            </div>
            <button onClick={handleUploadToEtsy} style={{width: '100%', marginTop: '1rem'}}>Upload to Etsy</button>
          </div>
        </>
      ) : (
        <div className="sidebar-placeholder">
          <p>Select an image from the gallery to begin editing and uploading.</p>
        </div>
      )}
    </aside>
  );
};

export default EditingSidebar;
