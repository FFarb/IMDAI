import React, { useEffect, useMemo, useState } from 'react';

export interface EtsyListingFormValues {
  title: string;
  description: string;
  price: number;
  quantity: number;
  taxonomyId: number;
}

interface EtsySidebarProps {
  imageToProcess: string | null;
  apiBaseUrl: string;
  onCreateListing: (values: EtsyListingFormValues) => Promise<{ message: string; listing_url?: string } | void>;
  onClearSelection?: () => void;
}

const EtsySidebar: React.FC<EtsySidebarProps> = ({
  imageToProcess,
  apiBaseUrl,
  onCreateListing,
  onClearSelection,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [taxonomyId, setTaxonomyId] = useState('');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setStatusMessage(null);
    setErrorMessage(null);
    setTitle('');
    setDescription('');
    setPrice('');
    setQuantity('1');
    setTaxonomyId('');
  }, [imageToProcess]);

  const previewSrc = useMemo(() => {
    if (!imageToProcess) return '';
    if (imageToProcess.startsWith('http')) return imageToProcess;
    return `${apiBaseUrl}${imageToProcess}`;
  }, [apiBaseUrl, imageToProcess]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!imageToProcess) {
      setErrorMessage('Select an image from the gallery before creating a listing.');
      return;
    }

    const parsedPrice = parseFloat(price);
    const parsedQuantity = parseInt(quantity, 10);
    const parsedTaxonomy = parseInt(taxonomyId, 10);

    if (Number.isNaN(parsedPrice) || parsedPrice <= 0) {
      setErrorMessage('Please enter a valid price greater than zero.');
      return;
    }

    if (Number.isNaN(parsedQuantity) || parsedQuantity <= 0) {
      setErrorMessage('Please enter a valid quantity greater than zero.');
      return;
    }

    if (Number.isNaN(parsedTaxonomy)) {
      setErrorMessage('Please enter a valid taxonomy ID.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setStatusMessage(null);

    try {
      const response = await onCreateListing({
        title,
        description,
        price: parsedPrice,
        quantity: parsedQuantity,
        taxonomyId: parsedTaxonomy,
      });

      if (response && 'message' in response) {
        const link = response.listing_url ? ` View listing: ${response.listing_url}` : '';
        setStatusMessage(`${response.message}${link}`);
      } else {
        setStatusMessage('Listing request submitted.');
      }
    } catch (error: any) {
      const detail = error?.response?.data?.detail ?? error?.message ?? 'Failed to create Etsy listing.';
      setErrorMessage(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <aside className="controls">
      <h2>Etsy</h2>
      <hr />
      {!imageToProcess ? (
        <p>Select an image from the gallery to prepare an Etsy listing.</p>
      ) : (
        <>
          <div className="form-group" style={{ textAlign: 'center' }}>
            <img
              src={previewSrc}
              alt="Preview of selected listing"
              style={{ maxWidth: '100%', borderRadius: '8px', border: '1px solid #444' }}
            />
            {onClearSelection && (
              <button
                type="button"
                onClick={onClearSelection}
                style={{ marginTop: '0.75rem' }}
              >
                Clear Selection
              </button>
            )}
          </div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="etsy-title">Title</label>
              <input
                id="etsy-title"
                type="text"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="etsy-description">Description</label>
              <textarea
                id="etsy-description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={4}
              />
            </div>
            <div className="form-group">
              <label htmlFor="etsy-price">Price (USD)</label>
              <input
                id="etsy-price"
                type="number"
                min="0"
                step="0.01"
                value={price}
                onChange={(event) => setPrice(event.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="etsy-quantity">Quantity</label>
              <input
                id="etsy-quantity"
                type="number"
                min="1"
                value={quantity}
                onChange={(event) => setQuantity(event.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="etsy-taxonomy">Taxonomy ID</label>
              <input
                id="etsy-taxonomy"
                type="number"
                min="0"
                value={taxonomyId}
                onChange={(event) => setTaxonomyId(event.target.value)}
                required
              />
            </div>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating Listing...' : 'Create Etsy Listing'}
            </button>
          </form>
        </>
      )}
      {statusMessage && <p style={{ color: '#4caf50', marginTop: '1rem' }}>{statusMessage}</p>}
      {errorMessage && <p style={{ color: 'salmon', marginTop: '1rem' }}>{errorMessage}</p>}
    </aside>
  );
};

export default EtsySidebar;
