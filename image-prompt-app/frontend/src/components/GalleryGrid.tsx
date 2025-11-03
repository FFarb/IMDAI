import type { ImageResult, SynthPrompt } from '../types/pipeline';

interface GalleryGridProps {
  images: ImageResult[][] | null;
  prompts: SynthPrompt[] | null;
  onGenerateImages: (index: number, append?: boolean) => void;
  onCopyPrompt: (index: number) => void;
  onDownloadImage: (promptIndex: number, imageIndex: number) => void;
  isLoading: boolean;
}

export function GalleryGrid({
  images,
  prompts,
  onGenerateImages,
  onCopyPrompt,
  onDownloadImage,
  isLoading,
}: GalleryGridProps) {
  if (!images || !prompts || !prompts.length) {
    return (
      <section className="card">
        <header className="card-header">
          <div>
            <h2>Gallery</h2>
            <p className="card-subtitle">Generate images to see results here.</p>
          </div>
        </header>
        <p className="muted">No images yet.</p>
      </section>
    );
  }

  return (
    <section className="card">
      <header className="card-header">
        <div>
          <h2>Gallery</h2>
          <p className="card-subtitle">Review outputs, request variations, and export assets.</p>
        </div>
      </header>

      <div className="gallery-grid">
        {prompts.map((prompt, promptIndex) => {
          const promptImages = images[promptIndex] ?? [];
          return (
            <div className="gallery-column" key={`prompt-${promptIndex}`}>
              <div className="gallery-header">
                <h3>
                  Prompt {String.fromCharCode(65 + promptIndex)}
                  {prompt.title ? ` · ${prompt.title}` : ''}
                </h3>
                <div className="card-actions">
                  <button type="button" onClick={() => onGenerateImages(promptIndex, true)} disabled={isLoading}>
                    Variations
                  </button>
                  <button type="button" onClick={() => onGenerateImages(promptIndex, false)} disabled={isLoading}>
                    Regenerate
                  </button>
                  <button type="button" onClick={() => onCopyPrompt(promptIndex)} disabled={isLoading}>
                    Copy Prompt
                  </button>
                </div>
              </div>

              <div className="image-stack">
                {promptImages.length ? (
                  promptImages.map((image, imageIndex) => {
                    const src = image.url ?? (image.b64_json ? `data:image/png;base64,${image.b64_json}` : null);
                    if (!src) return null;
                    return (
                      <figure key={`${promptIndex}-${imageIndex}`} className="image-card">
                        <img src={src} alt={`Prompt ${promptIndex + 1} result ${imageIndex + 1}`} />
                        <figcaption>
                          <button
                            type="button"
                            onClick={() => onDownloadImage(promptIndex, imageIndex)}
                            disabled={isLoading}
                          >
                            Download
                          </button>
                        </figcaption>
                      </figure>
                    );
                  })
                ) : (
                  <p className="muted">No images yet for this prompt.</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
