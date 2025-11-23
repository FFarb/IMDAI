import { useState } from 'react';
import type { ImageResult, SynthesisPrompt } from '../types/pipeline';

interface GalleryGridProps {
  prompts: SynthesisPrompt[] | null;
  images: ImageResult[][];
  isLoading: boolean;
  generationIds?: number[];
}

async function approveGeneration(generationId: number): Promise<boolean> {
  try {
    const response = await fetch('http://localhost:8000/api/library/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        generation_id: generationId,
        action_type: 'saved',
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save to library');
    }

    return true;
  } catch (error) {
    console.error('Failed to approve generation:', error);
    throw error;
  }
}

export function GalleryGrid({ prompts, images, isLoading, generationIds }: GalleryGridProps) {
  const [savingStates, setSavingStates] = useState<Record<number, boolean>>({});
  const [savedStates, setSavedStates] = useState<Record<number, boolean>>({});

  if (!prompts?.length) {
    return (
      <section className="card">
        <header className="card-header">
          <div>
            <h2>Gallery</h2>
            <p className="card-subtitle">Generate prompts to review image outputs.</p>
          </div>
        </header>
        <p className="muted">No prompts available yet.</p>
      </section>
    );
  }

  const handleSaveToLibrary = async (promptIndex: number, imageIndex: number) => {
    if (!generationIds) return;

    const flatIndex = promptIndex * (images[0]?.length || 1) + imageIndex;
    const generationId = generationIds[flatIndex];

    if (!generationId) {
      console.error('No generation ID found for this image');
      return;
    }

    setSavingStates(prev => ({ ...prev, [generationId]: true }));

    try {
      await approveGeneration(generationId);
      setSavedStates(prev => ({ ...prev, [generationId]: true }));
    } catch (error) {
      alert(`Failed to save to library: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setSavingStates(prev => ({ ...prev, [generationId]: false }));
    }
  };

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h2>Gallery</h2>
          <p className="card-subtitle">Review generated prompts and their image variations.</p>
        </div>
      </header>

      <div className="gallery-grid">
        {prompts.map((prompt, promptIndex) => {
          const promptImages = images[promptIndex] ?? [];
          return (
            <article className="gallery-column" key={`prompt-${promptIndex}`}>
              <header className="gallery-header">
                <h3>Prompt {promptIndex + 1}</h3>
                <button
                  type="button"
                  className="secondary"
                  disabled={isLoading}
                  onClick={() => {
                    void navigator.clipboard?.writeText?.(prompt.positive);
                  }}
                >
                  Copy Prompt
                </button>
              </header>

              <pre className="prompt-text-wrappable">{prompt.positive}</pre>
              {prompt.negative.length ? (
                <p className="muted">Negative: {prompt.negative.join(', ')}</p>
              ) : null}
              {prompt.notes ? <p className="muted">Notes: {prompt.notes}</p> : null}

              <div className="image-stack">
                {promptImages.length ? (
                  promptImages.map((image, imageIndex) => {
                    if (!image) return null;

                    const src = image.url;

                    if (!src) {
                      return (
                        <p className="muted" key={`image-${promptIndex}-${imageIndex}`}>
                          {image.error ? `Error: ${image.error}` : 'Loading preview...'}
                        </p>
                      );
                    }

                    const flatIndex = promptIndex * promptImages.length + imageIndex;
                    const generationId = generationIds?.[flatIndex];
                    const isSaving = generationId ? savingStates[generationId] : false;
                    const isSaved = generationId ? savedStates[generationId] : false;

                    return (
                      <figure className="image-card" key={`image-${promptIndex}-${imageIndex}`}>
                        <img
                          src={src}
                          alt={`Prompt ${promptIndex + 1} result ${imageIndex + 1}`}
                        />
                        {generationId && (
                          <div className="image-actions">
                            <button
                              type="button"
                              className={isSaved ? "success" : "primary"}
                              disabled={isSaving || isSaved}
                              onClick={() => handleSaveToLibrary(promptIndex, imageIndex)}
                            >
                              {isSaving ? '💾 Saving...' : isSaved ? '✅ Saved to Library' : '💾 Save to Library'}
                            </button>
                          </div>
                        )}
                      </figure>
                    );
                  })
                ) : (
                  <p className="muted">Generate images to see results here.</p>
                )}
              </div>
            </article>
          );
        })}
      </div>

      <style>{`
        .image-card {
          position: relative;
          margin: 0;
        }

        .image-actions {
          margin-top: 0.5rem;
          display: flex;
          gap: 0.5rem;
          justify-content: center;
        }

        .image-actions button {
          font-size: 0.9rem;
          padding: 0.5rem 1rem;
        }

        .image-actions button.success {
          background: #10b981;
          color: white;
        }

        .image-actions button.success:hover:not(:disabled) {
          background: #059669;
        }
      `}</style>
    </section>
  );
}
