import React, { useState, ChangeEvent } from 'react';

const ProcessingSidebar: React.FC = () => {
  // State to hold the selected image file
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  // State to hold the URL for the image preview
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  /**
   * Handles the file selection event from the input.
   * @param event The file input change event.
   */
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setSelectedFile(file);

      // Create a temporary URL for previewing the image
      const newPreviewUrl = URL.createObjectURL(file);
      setPreviewUrl(newPreviewUrl);
    }
  };

  /**
   * Handles the image processing submission.
   */
  const handleProcessImage = () => {
    if (!selectedFile) {
      alert('Please select an image file first.');
      return;
    }
    // Placeholder for future API call to the backend
    console.log('Processing image:', selectedFile.name);
    alert(`File "${selectedFile.name}" is ready to be sent for processing.`);
    // TODO: Implement the API call to the backend here.
  };

  return (
    <aside className="controls">
      <h2>Tools</h2>
      <hr />

      {/* Section 1: Etsy Placeholder */}
      <div className="form-group">
        <h3>Etsy Section</h3>
        <p>Etsy-related controls and information will go here.</p>
        {/* Example of a placeholder input */}
        <label htmlFor="etsy-listing-id">Etsy Listing ID</label>
        <input type="text" id="etsy-listing-id" placeholder="e.g., 123456789" />
      </div>

      <hr style={{margin: '2rem 0'}}/>

      {/* Section 2: Image Processing */}
      <div className="form-group">
        <h3>Image Processing</h3>
        <label htmlFor="image-upload">Upload Image for Processing</label>
        <input
          type="file"
          id="image-upload"
          accept="image/png, image/jpeg"
          onChange={handleFileChange}
          style={{
            boxSizing: 'border-box',
            border: '1px solid #555',
            padding: '0.5rem',
            borderRadius: '4px',
            width: '100%'
          }}
        />

        {/* Image Preview Section */}
        {previewUrl && (
          <div style={{ marginTop: '1rem', textAlign: 'center' }}>
            <p>Preview:</p>
            <img
              src={previewUrl}
              alt="Selected file preview"
              style={{ maxWidth: '100%', borderRadius: '8px', border: '1px solid #444' }}
            />
          </div>
        )}

        <button
          onClick={handleProcessImage}
          disabled={!selectedFile}
          style={{ marginTop: '1rem' }}
        >
          Process Image
        </button>
      </div>
    </aside>
  );
};

export default ProcessingSidebar;
